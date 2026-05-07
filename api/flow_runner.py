"""
异步创作流程编排器

将同步的 CrewAI Agent 调用包装为异步，支持用户交互（标题选择、P2 决策）。
通过 WebSocket 广播进度。
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from crews import XiaohongshuCrew
from models import MaterialPack, NotePack, NoteMetadata, ComplianceStatus

logger = logging.getLogger(__name__)

# 全局任务交互事件存储
_task_events: dict[str, dict] = {}


def get_task_events(task_id: str) -> dict:
    """获取任务的交互事件"""
    if task_id not in _task_events:
        _task_events[task_id] = {
            "title_event": asyncio.Event(),
            "title_selection": None,
            "p2_event": asyncio.Event(),
            "p2_decision": None,
        }
    return _task_events[task_id]


def signal_title_selection(task_id: str, title_index: int):
    """用户选择标题后调用"""
    events = get_task_events(task_id)
    events["title_selection"] = title_index
    events["title_event"].set()


def signal_p2_decision(task_id: str, accept: bool):
    """用户 P2 决策后调用"""
    events = get_task_events(task_id)
    events["p2_decision"] = accept
    events["p2_event"].set()


async def run_creation_flow(
    task_id: str,
    input_data: dict,
    update_task_fn,
    broadcast_fn,
) -> dict:
    """
    异步执行创作流程

    Args:
        task_id: 任务 ID
        input_data: 创作输入（product, scene, persona, enterprise_id）
        update_task_fn: 更新任务状态的回调
        broadcast_fn: WebSocket 广播回调

    Returns:
        dict: 最终结果
    """
    events = get_task_events(task_id)
    crew = XiaohongshuCrew(verbose=False)
    enterprise_id = input_data.get("enterprise_id", "")

    try:
        # ── Step 1: 素材检索（使用真实向量搜索） ──
        update_task_fn(task_id, status="running", current_step="素材检索", progress=10)
        await broadcast_fn(task_id, {"type": "progress", "step": "素材检索", "progress": 10})

        from tools.material_tools import MaterialSearchTool
        material_tool = MaterialSearchTool()
        material_pack = await asyncio.to_thread(
            material_tool.search,
            product=input_data.get("product", ""),
            scene=input_data.get("scene", ""),
            persona=input_data.get("persona", ""),
            enterprise_id=enterprise_id,
        )
        material_dict = material_pack.model_dump(exclude_none=True)

        update_task_fn(task_id, progress=20)
        await broadcast_fn(task_id, {
            "type": "material_ready",
            "material_pack": material_dict,
            "missing_fields": material_pack.missing_fields or [],
        })

        # ── Step 2: 标题生成 ──
        update_task_fn(task_id, current_step="标题生成", progress=25)
        await broadcast_fn(task_id, {"type": "progress", "step": "标题生成", "progress": 25})

        topic = input_data.get("product", "产品推荐")
        if material_pack.product and material_pack.product.name:
            topic = material_pack.product.name

        title_output = await asyncio.to_thread(
            crew.title_agent.generate,
            topic=topic,
            material_pack=material_dict,
            historical_titles=None,
        )

        if not title_output.titles:
            raise Exception("标题生成失败，未返回任何标题")

        title_options = [
            {"title": t.title, "strategy": t.strategy, "score": t.score, "reason": t.reason}
            for t in title_output.titles
        ]

        # 等待用户选择标题
        update_task_fn(
            task_id,
            status="awaiting_title_selection",
            current_step="等待选择标题",
            progress=40,
            title_options=title_options,
        )
        await broadcast_fn(task_id, {
            "type": "awaiting_title_selection",
            "title_options": title_options,
        })

        # 等待用户选择（超时 5 分钟）
        try:
            await asyncio.wait_for(events["title_event"].wait(), timeout=300)
        except asyncio.TimeoutError:
            # 超时自动选择第一个
            events["title_selection"] = 0

        selected_index = events["title_selection"] or 0
        selected_title = title_output.titles[selected_index].title

        update_task_fn(task_id, status="running", current_step="标题已选择", progress=45)
        await broadcast_fn(task_id, {"type": "title_selected", "title": selected_title})

        # ── Step 3: 正文生成 ──
        update_task_fn(task_id, current_step="正文创作", progress=50)
        await broadcast_fn(task_id, {"type": "progress", "step": "正文创作", "progress": 50})

        note_output = await asyncio.to_thread(
            crew.article_agent.generate,
            title=selected_title,
            material_pack=material_dict,
        )

        update_task_fn(task_id, progress=65)
        await broadcast_fn(task_id, {
            "type": "article_ready",
            "article": note_output.article,
            "ai_flavor_score": note_output.ai_flavor_score,
        })

        # ── Step 4: 标签生成 ──
        update_task_fn(task_id, current_step="标签生成", progress=70)
        await broadcast_fn(task_id, {"type": "progress", "step": "标签生成", "progress": 70})

        tags = await asyncio.to_thread(
            crew.tag_agent.generate,
            article=note_output.article,
            title=selected_title,
            material_pack=material_dict,
        )

        update_task_fn(task_id, progress=80)

        # ── Step 5: 合规检查 ──
        update_task_fn(task_id, current_step="合规检查", progress=85)
        await broadcast_fn(task_id, {"type": "progress", "step": "合规检查", "progress": 85})

        brand_taboos = material_pack.brand.taboos if material_pack.brand else []
        compliance_report = await asyncio.to_thread(
            crew.compliance_agent.check,
            title=selected_title,
            article=note_output.article,
            tags=tags,
            brand_taboos=brand_taboos,
        )

        # 如果有 P0 问题，等待用户决策
        if compliance_report.has_p0_issues:
            p0_issues = [
                {"severity": "p0", "content": issue.content, "location": issue.location, "suggestion": issue.suggestion}
                for issue in compliance_report.p0_issues
            ]
            update_task_fn(
                task_id,
                status="awaiting_p2_decision",
                current_step="等待合规决策",
                progress=90,
                p2_issues=p0_issues,
            )
            await broadcast_fn(task_id, {
                "type": "compliance_issues",
                "p0_issues": p0_issues,
            })

            try:
                await asyncio.wait_for(events["p2_event"].wait(), timeout=300)
            except asyncio.TimeoutError:
                events["p2_decision"] = True  # 超时默认接受

        update_task_fn(task_id, progress=95)

        # ── Step 6: 组装最终结果 ──
        compliance_status = compliance_report.status.value if hasattr(compliance_report.status, 'value') else str(compliance_report.status)

        result = {
            "material_pack": material_dict,
            "title_options": title_options,
            "title": selected_title,
            "article": note_output.article,
            "paragraphs": [p.model_dump() for p in note_output.paragraphs] if note_output.paragraphs else [],
            "tags": tags,
            "ai_flavor_score": note_output.ai_flavor_score,
            "compliance_report": {
                "status": compliance_status,
                "p0_issues": [{"severity": "p0", "content": i.content, "location": i.location, "suggestion": i.suggestion} for i in compliance_report.p0_issues] if compliance_report.p0_issues else [],
                "p1_issues": [{"severity": "p1", "content": i.content, "location": i.location, "suggestion": i.suggestion} for i in compliance_report.p1_issues] if compliance_report.p1_issues else [],
                "p2_issues": [{"severity": "p2", "content": i.content, "location": i.location, "suggestion": i.suggestion} for i in compliance_report.p2_issues] if compliance_report.p2_issues else [],
                "suggestions": compliance_report.suggestions or [],
            },
            "metadata": {
                "platform": "xiaohongshu",
                "enterprise_id": enterprise_id,
                "retry_count": 0,
                "degraded": False,
                "llm_used": "mimo-v2.5-pro",
            },
        }

        update_task_fn(
            task_id,
            status="completed",
            current_step="完成",
            progress=100,
            result=result,
        )

        # 持久化到数据库
        await _persist_note(task_id, enterprise_id, input_data, result)

        await broadcast_fn(task_id, {"type": "completed", "result": result})

        # 清理事件
        _task_events.pop(task_id, None)

        return result

    except Exception as e:
        logger.error(f"Flow 执行失败: {e}", exc_info=True)
        update_task_fn(task_id, status="failed", error=str(e))
        await broadcast_fn(task_id, {"type": "failed", "error": str(e)})
        _task_events.pop(task_id, None)
        raise


async def _persist_note(task_id: str, enterprise_id: str, input_data: dict, result: dict):
    """将结果持久化到 notes 表"""
    import json
    import api.routes.create as create_module
    from api.db import get_db_conn

    try:
        async with get_db_conn(enterprise_id=enterprise_id, user_role="tenant_admin") as conn:
            await conn.execute(
                "INSERT INTO notes (enterprise_id, platform, topic, title, article, tags, ai_flavor_score, compliance_status, metadata) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)",
                enterprise_id,
                result["metadata"]["platform"],
                input_data.get("product", ""),
                result["title"],
                result["article"],
                json.dumps(result["tags"], ensure_ascii=False),
                result["ai_flavor_score"],
                result["compliance_report"]["status"],
                json.dumps(result["metadata"], ensure_ascii=False),
            )
    except Exception as db_err:
        logger.error(f"笔记入库失败: {db_err}")

    # 内存 fallback
    create_module._memory_note_id_counter += 1
    create_module._memory_notes.append({
        "id": str(create_module._memory_note_id_counter),
        "enterprise_id": enterprise_id,
        "platform": result["metadata"]["platform"],
        "topic": input_data.get("product", ""),
        "title": result["title"],
        "article": result["article"],
        "tags": result["tags"],
        "ai_flavor_score": result["ai_flavor_score"],
        "compliance_status": result["compliance_report"]["status"],
        "created_at": datetime.now().isoformat(),
        "published_at": None,
        "status": "draft",
    })
