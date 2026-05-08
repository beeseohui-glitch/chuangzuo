"""
创作接口

- POST /api/v1/create/start          提交创作需求，触发 Flow
- GET  /api/v1/create/{task_id}/status 查询任务状态
- WS   /ws/create/{task_id}           实时状态推送
- POST /api/v1/create/{task_id}/select-title  用户选择标题
- POST /api/v1/create/{task_id}/p2-decision   P2 问题处理
- GET  /api/v1/create/{task_id}/result        获取最终笔记包
"""

import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from api.db import get_db_conn
from api.deps import require_tenant, UserInfo
from fastapi import Depends

router = APIRouter(prefix="/api/v1/create", tags=["创作"])


# ── 任务状态 ──────────────────────────────────────────────


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_TITLE_SELECTION = "awaiting_title_selection"
    AWAITING_P2_DECISION = "awaiting_p2_decision"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskRecord(BaseModel):
    task_id: str
    user_id: str
    enterprise_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    current_step: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None
    title_options: Optional[list[dict]] = None
    p2_issues: Optional[list[dict]] = None
    created_at: str = ""
    updated_at: str = ""


# ── 内存任务存储（开发模式）─────────────────────────────────

_tasks: dict[str, TaskRecord] = {}
_ws_connections: dict[str, list[WebSocket]] = {}

# 内存笔记存储（开发模式 fallback，当数据库写入失败时使用）
_memory_notes: list[dict] = []
_memory_note_id_counter = 1000


def get_memory_notes(enterprise_id: str) -> list[dict]:
    """获取指定企业的内存笔记"""
    return [n for n in _memory_notes if n.get("enterprise_id") == enterprise_id]


async def _broadcast(task_id: str, data: dict):
    """向所有监听该 task_id 的 WebSocket 连接广播"""
    connections = _ws_connections.get(task_id, [])
    dead = []
    for ws in connections:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.remove(ws)


def _update_task(task_id: str, **kwargs):
    """更新任务状态并记录时间"""
    task = _tasks.get(task_id)
    if not task:
        return
    for k, v in kwargs.items():
        setattr(task, k, v)
    task.updated_at = datetime.now().isoformat()


async def _run_creation_flow(task_id: str, input_data: dict):
    """后台执行真实创作 Flow"""
    from api.flow_runner import run_creation_flow
    await run_creation_flow(task_id, input_data, _update_task, _broadcast)


# ── 请求/响应模型 ─────────────────────────────────────────


class CreateStartRequest(BaseModel):
    product: str
    scene: Optional[str] = None
    persona: Optional[str] = None
    platform: str = "xiaohongshu"
    mode: str = "quick"  # "quick" 或 "full"


class SelectTitleRequest(BaseModel):
    title_index: int


class P2DecisionRequest(BaseModel):
    accept: bool
    custom_text: Optional[str] = None


# ── 接口 ──────────────────────────────────────────────────


def _get_owned_task(task_id: str, user: UserInfo) -> TaskRecord:
    """获取任务并校验所有权"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "任务不存在"})
    if task.user_id != user.user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN", "message": "无权访问该任务"})
    return task


@router.post("/start")
async def start_creation(
    req: CreateStartRequest,
    background_tasks: BackgroundTasks,
    user: UserInfo = Depends(require_tenant),
):
    """提交创作需求，触发 Flow"""
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()

    task = TaskRecord(
        task_id=task_id,
        user_id=user.user_id,
        enterprise_id=user.enterprise_id or "",
        status=TaskStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    _tasks[task_id] = task

    input_data = {
        "product": req.product,
        "scene": req.scene,
        "persona": req.persona,
        "platform": req.platform,
        "enterprise_id": user.enterprise_id,
    }

    background_tasks.add_task(_run_creation_flow, task_id, input_data)

    return {"task_id": task_id, "status": TaskStatus.PENDING}


@router.post("/start-full")
async def start_full_creation(
    req: CreateStartRequest,
    background_tasks: BackgroundTasks,
    user: UserInfo = Depends(require_tenant),
):
    """提交创作需求（数据驱动模式，含选题推荐）"""
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()

    task = TaskRecord(
        task_id=task_id,
        user_id=user.user_id,
        enterprise_id=user.enterprise_id or "",
        status=TaskStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    _tasks[task_id] = task

    input_data = {
        "product": req.product,
        "scene": req.scene,
        "persona": req.persona,
        "platform": req.platform,
        "enterprise_id": user.enterprise_id,
        "mode": "full",
        "category": req.scene or "health_product",
    }

    background_tasks.add_task(_run_full_creation_flow, task_id, input_data)

    return {"task_id": task_id, "status": TaskStatus.PENDING, "mode": "full"}


async def _run_full_creation_flow(task_id: str, input_data: dict):
    """后台执行完整创作 Flow（含选题），逐步推送 WebSocket 消息"""
    import logging
    from api.flow_runner import get_task_events, _task_events
    logger = logging.getLogger(__name__)
    enterprise_id = input_data.get("enterprise_id", "")

    try:
        # ── Step 1: 选题推荐 ──
        _update_task(task_id, status="running", current_step="选题推荐", progress=5)
        await _broadcast(task_id, {"type": "progress", "step": "选题推荐", "progress": 5})

        from agents.topic_agent import TopicAgent
        topic_agent = TopicAgent()
        topic_output = await asyncio.to_thread(
            topic_agent.generate_topics,
            category=input_data.get("category", "health_product"),
            product=input_data.get("product", ""),
            brand_name=input_data.get("brand_name", ""),
            target_persona=input_data.get("persona", ""),
            num_topics=5,
        )

        topic_options = []
        if topic_output and hasattr(topic_output, 'topics') and topic_output.topics:
            topic_options = [
                {
                    "title": t.title,
                    "angle": getattr(t, 'angle', ''),
                    "keywords": getattr(t, 'keywords', []),
                    "score": getattr(t, 'score', 0),
                }
                for t in topic_output.topics
            ]

        if not topic_options:
            _update_task(task_id, status=TaskStatus.FAILED, error="选题推荐未返回结果")
            await _broadcast(task_id, {"type": "failed", "error": "选题推荐未返回结果，请调整需求后重试"})
            return

        _update_task(task_id, progress=15)
        await _broadcast(task_id, {
            "type": "topic_options",
            "topic_options": topic_options,
        })

        # ── Step 2: 素材检索 ──
        _update_task(task_id, current_step="素材检索", progress=20)
        await _broadcast(task_id, {"type": "progress", "step": "素材检索", "progress": 20})

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

        _update_task(task_id, progress=30)
        await _broadcast(task_id, {
            "type": "material_ready",
            "material_pack": material_dict,
            "missing_fields": material_pack.missing_fields or [],
        })

        # ── Step 3: 标题生成 ──
        _update_task(task_id, current_step="标题生成", progress=35)
        await _broadcast(task_id, {"type": "progress", "step": "标题生成", "progress": 35})

        from agents.title_agent import TitleAgent
        title_agent = TitleAgent()
        # 使用第一个选题的标题作为 topic
        topic_text = topic_options[0]["title"] if topic_options else input_data.get("product", "")
        title_output = await asyncio.to_thread(
            title_agent.generate,
            topic=topic_text,
            material_pack=material_dict,
            historical_titles=None,
        )

        if not title_output.titles:
            _update_task(task_id, status=TaskStatus.FAILED, error="标题生成失败")
            await _broadcast(task_id, {"type": "failed", "error": "标题生成失败"})
            return

        title_options = [
            {"title": t.title, "strategy": t.strategy, "score": t.score, "reason": t.reason}
            for t in title_output.titles
        ]

        # 等待用户选择标题
        _update_task(
            task_id,
            status="awaiting_title_selection",
            current_step="等待选择标题",
            progress=45,
            title_options=title_options,
        )
        await _broadcast(task_id, {
            "type": "awaiting_title_selection",
            "title_options": title_options,
        })

        # 等待用户选择（超时 5 分钟）
        events = get_task_events(task_id)
        try:
            await asyncio.wait_for(events["title_event"].wait(), timeout=300)
        except asyncio.TimeoutError:
            events["title_selection"] = 0

        selected_index = events["title_selection"] or 0
        selected_title = title_output.titles[selected_index].title

        _update_task(task_id, status="running", current_step="标题已选择", progress=50)
        await _broadcast(task_id, {"type": "title_selected", "title": selected_title})

        # ── Step 4: 正文生成 ──
        _update_task(task_id, current_step="正文创作", progress=55)
        await _broadcast(task_id, {"type": "progress", "step": "正文创作", "progress": 55})

        from agents.article_agent import ArticleAgent
        article_agent = ArticleAgent()
        note_output = await asyncio.to_thread(
            article_agent.generate,
            title=selected_title,
            material_pack=material_dict,
        )

        _update_task(task_id, progress=70)
        await _broadcast(task_id, {
            "type": "article_ready",
            "article": note_output.article,
            "ai_flavor_score": note_output.ai_flavor_score,
        })

        # ── Step 5: 标签生成 ──
        _update_task(task_id, current_step="标签生成", progress=75)
        await _broadcast(task_id, {"type": "progress", "step": "标签生成", "progress": 75})

        from agents.tag_agent import TagAgent
        tag_agent = TagAgent()
        tags = await asyncio.to_thread(
            tag_agent.generate,
            article=note_output.article,
            title=selected_title,
            material_pack=material_dict,
        )

        _update_task(task_id, progress=80)

        # ── Step 6: 合规检查 ──
        _update_task(task_id, current_step="合规检查", progress=85)
        await _broadcast(task_id, {"type": "progress", "step": "合规检查", "progress": 85})

        from agents.compliance_agent import ComplianceAgent
        compliance_agent = ComplianceAgent()
        brand_taboos = material_pack.brand.taboos if material_pack.brand else []
        compliance_report = await asyncio.to_thread(
            compliance_agent.check,
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
            _update_task(
                task_id,
                status="awaiting_p2_decision",
                current_step="等待合规决策",
                progress=90,
                p2_issues=p0_issues,
            )
            await _broadcast(task_id, {
                "type": "compliance_issues",
                "p0_issues": p0_issues,
            })

            try:
                await asyncio.wait_for(events["p2_event"].wait(), timeout=300)
            except asyncio.TimeoutError:
                events["p2_decision"] = True

        _update_task(task_id, progress=95)

        # ── Step 7: 组装最终结果 ──
        compliance_status = compliance_report.status.value if hasattr(compliance_report.status, 'value') else str(compliance_report.status)

        result = {
            "material_pack": material_dict,
            "topic_options": topic_options,
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
                "mode": "full",
                "retry_count": 0,
                "degraded": False,
                "llm_used": "mimo-v2.5-pro",
            },
        }

        _update_task(
            task_id,
            status=TaskStatus.COMPLETED,
            current_step="完成",
            progress=100,
            result=result,
        )

        # 持久化到数据库
        await _persist_note_full(task_id, enterprise_id, input_data, result)

        await _broadcast(task_id, {"type": "completed", "result": result})

        # 清理事件
        _task_events.pop(task_id, None)

    except Exception as e:
        logger.error(f"Full Flow 执行失败: {e}", exc_info=True)
        _update_task(task_id, status=TaskStatus.FAILED, error=str(e))
        await _broadcast(task_id, {"type": "failed", "error": str(e)})
        _task_events.pop(task_id, None)


async def _persist_note_full(task_id: str, enterprise_id: str, input_data: dict, result: dict):
    """将 full 模式结果持久化到 notes 表"""
    import json
    from datetime import datetime
    import api.routes.create as create_module

    try:
        from api.db import get_db_conn
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
        import logging
        logging.getLogger(__name__).error(f"笔记入库失败: {db_err}")

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


@router.get("/{task_id}/status")
async def get_task_status(
    task_id: str,
    user: UserInfo = Depends(require_tenant),
):
    """查询任务状态"""
    task = _get_owned_task(task_id, user)

    return {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "current_step": task.current_step,
        "error": task.error,
    }


@router.post("/{task_id}/select-title")
async def select_title(
    task_id: str,
    req: SelectTitleRequest,
    user: UserInfo = Depends(require_tenant),
):
    """用户选择标题"""
    task = _get_owned_task(task_id, user)
    if task.status != TaskStatus.AWAITING_TITLE_SELECTION:
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "当前不在标题选择阶段"})

    if task.title_options and 0 <= req.title_index < len(task.title_options):
        selected = task.title_options[req.title_index]
        _update_task(task_id, status=TaskStatus.RUNNING)
        await _broadcast(task_id, {"type": "title_selected", "title": selected})
        # 通知 flow_runner 用户已选择标题
        from api.flow_runner import signal_title_selection
        signal_title_selection(task_id, req.title_index)
        return {"selected": selected}

    raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "无效的标题索引"})


@router.post("/{task_id}/p2-decision")
async def p2_decision(
    task_id: str,
    req: P2DecisionRequest,
    user: UserInfo = Depends(require_tenant),
):
    """P2 问题处理"""
    task = _get_owned_task(task_id, user)
    if task.status != TaskStatus.AWAITING_P2_DECISION:
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "当前不在 P2 决策阶段"})

    _update_task(task_id, status=TaskStatus.RUNNING)
    await _broadcast(task_id, {"type": "p2_decided", "accept": req.accept})
    # 通知 flow_runner 用户已做决策
    from api.flow_runner import signal_p2_decision
    signal_p2_decision(task_id, req.accept)

    return {"accepted": req.accept}


@router.get("/{task_id}/result")
async def get_result(
    task_id: str,
    user: UserInfo = Depends(require_tenant),
):
    """获取最终笔记包"""
    task = _get_owned_task(task_id, user)
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "任务尚未完成"})

    return {"task_id": task.task_id, "result": task.result}


# ── WebSocket ─────────────────────────────────────────────


@router.websocket("/ws/{task_id}")
async def websocket_create(websocket: WebSocket, task_id: str):
    """WebSocket 实时状态推送"""
    await websocket.accept()

    if task_id not in _ws_connections:
        _ws_connections[task_id] = []
    _ws_connections[task_id].append(websocket)

    # 如果任务已完成，立即推送结果
    task = _tasks.get(task_id)
    if task and task.status == TaskStatus.COMPLETED:
        await websocket.send_json({"type": "completed", "result": task.result})
    elif task and task.status == TaskStatus.FAILED:
        await websocket.send_json({"type": "failed", "error": task.error})

    try:
        while True:
            # 保持连接，等待客户端消息或断开
            await websocket.receive_text()
    except WebSocketDisconnect:
        if task_id in _ws_connections:
            _ws_connections[task_id] = [
                ws for ws in _ws_connections[task_id] if ws != websocket
            ]
