"""
数据看板 + 笔记列表接口

- GET /api/v1/dashboard/summary   工作台摘要
- GET /api/v1/dashboard/trends    趋势数据
- GET /api/v1/dashboard/topics    选题排名
- GET /api/v1/notes               笔记列表
"""

import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.db import get_db_conn
from api.deps import require_tenant, UserInfo
from api.routes.create import get_memory_notes, _memory_notes
from api.utils import row_to_dict

router = APIRouter(tags=["数据看板"])


# ── 接口 ──────────────────────────────────────────────────


@router.get("/api/v1/dashboard/summary")
async def dashboard_summary(
    user: UserInfo = Depends(require_tenant),
):
    """工作台摘要"""
    eid = user.enterprise_id or ""

    # 查询数据库
    db_notes = []
    total_content = 0
    published = 0
    draft = 0
    avg_ai_score = 0.0
    quota_used = 0
    quota_monthly = 100

    try:
        async with get_db_conn(enterprise_id=eid, user_role=user.role) as conn:
            stats_row = await conn.fetchrow(
                "SELECT "
                "  COUNT(*) as total_content, "
                "  COUNT(*) FILTER (WHERE published_at IS NOT NULL) as published, "
                "  COUNT(*) FILTER (WHERE published_at IS NULL) as draft, "
                "  COALESCE(AVG(ai_flavor_score), 0) as avg_ai_score "
                "FROM notes WHERE enterprise_id = $1",
                eid,
            )
            recent_rows = await conn.fetch(
                "SELECT id, title, platform, published_at, ai_flavor_score, created_at "
                "FROM notes WHERE enterprise_id = $1 ORDER BY created_at DESC LIMIT 5",
                eid,
            )
            quota_row = await conn.fetchrow(
                "SELECT quota_monthly, quota_used FROM enterprises WHERE id = $1",
                eid,
            )

        total_content = stats_row["total_content"] or 0
        published = stats_row["published"] or 0
        draft = stats_row["draft"] or 0
        avg_ai_score = round(float(stats_row["avg_ai_score"] or 0), 1)
        if quota_row:
            quota_used = quota_row["quota_used"]
            quota_monthly = quota_row["quota_monthly"]

        for r in recent_rows:
            db_notes.append({
                "id": str(r["id"]),
                "title": r["title"] or "",
                "platform": r["platform"] or "",
                "status": "published" if r["published_at"] else "draft",
                "ai_score": r["ai_flavor_score"] or 0,
                "created_at": r["created_at"].isoformat() if r["created_at"] else "",
            })
    except Exception:
        pass

    # 合并内存笔记
    mem_notes = get_memory_notes(eid)
    mem_creations = []
    for n in mem_notes:
        mem_creations.append({
            "id": n["id"],
            "title": n["title"] or "",
            "platform": n["platform"] or "",
            "status": n.get("status", "draft"),
            "ai_score": n.get("ai_flavor_score", 0),
            "created_at": n.get("created_at", ""),
        })

    # 合并去重（内存笔记在前，数据库在后，按 created_at 倒序）
    all_notes = mem_creations + db_notes
    seen_ids = set()
    unique_notes = []
    for n in all_notes:
        if n["id"] not in seen_ids:
            seen_ids.add(n["id"])
            unique_notes.append(n)
    unique_notes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    recent_creations = unique_notes[:5]

    # 合并统计
    total_mem = len(mem_notes)
    total_all = total_content + total_mem
    mem_scores = [n.get("ai_flavor_score", 0) for n in mem_notes]
    if mem_scores and avg_ai_score > 0:
        all_scores_avg = (avg_ai_score * total_content + sum(mem_scores)) / total_all
        avg_ai_score = round(all_scores_avg, 1)
    elif mem_scores:
        avg_ai_score = round(sum(mem_scores) / len(mem_scores), 1)

    return {
        "content_stats": {
            "total_content": total_all,
            "published": published,
            "draft": draft + total_mem,
            "archived": 0,
            "total_views": 0,
            "total_likes": 0,
            "total_comments": 0,
            "total_shares": 0,
            "avg_ai_score": avg_ai_score,
        },
        "recent_creations": recent_creations,
        "quota": {
            "used": quota_used,
            "total": quota_monthly,
            "reset_date": "2026-06-01",
        },
    }


@router.get("/api/v1/dashboard/trends")
async def dashboard_trends(
    days: int = Query(default=14, ge=7, le=90),
    user: UserInfo = Depends(require_tenant),
):
    """趋势数据"""
    eid = user.enterprise_id or ""
    today = datetime.now().date()
    start_date = today - timedelta(days=days - 1)

    async with get_db_conn(enterprise_id=eid, user_role=user.role) as conn:
        rows = await conn.fetch(
            "SELECT DATE(created_at) as d, COUNT(*) as cnt, COALESCE(AVG(ai_flavor_score), 0) as avg_score "
            "FROM notes WHERE enterprise_id = $1 AND DATE(created_at) >= $2 "
            "GROUP BY DATE(created_at) ORDER BY d",
            eid, start_date,
        )

    # 构建日期→数据映射
    data_map = {}
    for r in rows:
        data_map[r["d"].isoformat()] = {
            "count": r["cnt"],
            "avg_score": round(float(r["avg_score"]), 1),
        }

    dates = [(start_date + timedelta(days=i)).isoformat() for i in range(days)]
    counts = [data_map.get(d, {}).get("count", 0) for d in dates]
    scores = [data_map.get(d, {}).get("avg_score", 0) for d in dates]

    # 计算变化率（最近7天 vs 前7天）
    recent_sum = sum(counts[-7:]) if len(counts) >= 7 else sum(counts)
    prev_sum = sum(counts[-14:-7]) if len(counts) >= 14 else 0
    change_rate = ((recent_sum - prev_sum) / prev_sum * 100) if prev_sum > 0 else 0

    return {
        "period_start": dates[0],
        "period_end": dates[-1],
        "metrics": {
            "content_count": {
                "values": counts,
                "change_rate": round(change_rate, 1),
                "trend": "up" if change_rate > 0 else ("down" if change_rate < 0 else "stable"),
            },
            "ai_score": {
                "values": scores,
                "change_rate": 0,
                "trend": "stable",
            },
        },
        "dates": dates,
    }


@router.get("/api/v1/dashboard/topics")
async def dashboard_topics(
    user: UserInfo = Depends(require_tenant),
):
    """选题排名"""
    eid = user.enterprise_id or ""

    async with get_db_conn(enterprise_id=eid, user_role=user.role) as conn:
        rows = await conn.fetch(
            "SELECT topic, COUNT(*) as cnt "
            "FROM notes WHERE enterprise_id = $1 AND topic IS NOT NULL AND topic != '' "
            "GROUP BY topic ORDER BY cnt DESC LIMIT 10",
            eid,
        )

    topics = []
    for i, r in enumerate(rows, 1):
        topics.append({
            "rank": i,
            "title": r["topic"],
            "count": r["cnt"],
        })

    return {"topics": topics}


@router.get("/api/v1/notes")
async def list_notes(
    page: int = 1,
    page_size: int = 20,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    user: UserInfo = Depends(require_tenant),
):
    """笔记列表"""
    eid = user.enterprise_id or ""

    # 查询数据库
    db_items = []
    db_total = 0
    try:
        conditions = ["enterprise_id = $1"]
        params: list = [eid]
        idx = 2

        if platform:
            conditions.append(f"platform = ${idx}")
            params.append(platform)
            idx += 1
        if status == "published":
            conditions.append("published_at IS NOT NULL")
        elif status == "draft":
            conditions.append("published_at IS NULL")

        where = " AND ".join(conditions)
        offset = (page - 1) * page_size

        async with get_db_conn(enterprise_id=eid, user_role=user.role) as conn:
            count_row = await conn.fetchrow(
                f"SELECT COUNT(*) as cnt FROM notes WHERE {where}", *params,
            )
            rows = await conn.fetch(
                f"SELECT * FROM notes WHERE {where} ORDER BY created_at DESC LIMIT ${idx} OFFSET ${idx + 1}",
                *params, page_size, offset,
            )

        db_total = count_row["cnt"]
        for r in rows:
            d = row_to_dict(r, extra_datetime_keys=("published_at",))
            d["status"] = "published" if d.get("published_at") else "draft"
            db_items.append(d)
    except Exception:
        pass

    # 合并内存笔记
    mem_notes = get_memory_notes(eid)
    mem_items = []
    for n in mem_notes:
        if platform and n.get("platform") != platform:
            continue
        if status == "published" and not n.get("published_at"):
            continue
        if status == "draft" and n.get("published_at"):
            continue
        mem_items.append(n)

    # 合并去重
    all_items = mem_items + db_items
    seen_ids = set()
    unique_items = []
    for item in all_items:
        if item["id"] not in seen_ids:
            seen_ids.add(item["id"])
            unique_items.append(item)
    unique_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    total = db_total + len(mem_items)
    start = (page - 1) * page_size
    items = unique_items[start:start + page_size]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


class NoteUpdateRequest(BaseModel):
    title: Optional[str] = None
    article: Optional[str] = None
    tags: Optional[list[str]] = None


@router.get("/api/v1/notes/{note_id}")
async def get_note(
    note_id: str,
    user: UserInfo = Depends(require_tenant),
):
    """获取单条笔记详情"""
    eid = user.enterprise_id or ""

    # 先查内存
    for n in get_memory_notes(eid):
        if n["id"] == note_id:
            return n

    # 再查数据库
    try:
        nid = int(note_id)
    except ValueError:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "笔记不存在"})

    try:
        async with get_db_conn(enterprise_id=eid, user_role=user.role) as conn:
            row = await conn.fetchrow(
                "SELECT * FROM notes WHERE id = $1 AND enterprise_id = $2",
                nid, eid,
            )
        if row:
            d = row_to_dict(row, extra_datetime_keys=("published_at",))
            d["status"] = "published" if d.get("published_at") else "draft"
            return d
    except Exception:
        pass

    raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "笔记不存在"})


@router.put("/api/v1/notes/{note_id}")
async def update_note(
    note_id: str,
    req: NoteUpdateRequest,
    user: UserInfo = Depends(require_tenant),
):
    """编辑笔记"""
    eid = user.enterprise_id or ""

    # 更新内存笔记
    for n in _memory_notes:
        if n["id"] == note_id and n.get("enterprise_id") == eid:
            if req.title is not None:
                n["title"] = req.title
            if req.article is not None:
                n["article"] = req.article
            if req.tags is not None:
                n["tags"] = req.tags
            return {"message": "更新成功"}

    # 更新数据库
    try:
        nid = int(note_id)
    except ValueError:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "笔记不存在"})

    try:
        async with get_db_conn(enterprise_id=eid, user_role=user.role) as conn:
            row = await conn.fetchrow(
                "SELECT id FROM notes WHERE id = $1 AND enterprise_id = $2",
                nid, eid,
            )
            if row:
                updates = []
                params = []
                idx = 1
                if req.title is not None:
                    updates.append(f"title = ${idx}")
                    params.append(req.title)
                    idx += 1
                if req.article is not None:
                    updates.append(f"article = ${idx}")
                    params.append(req.article)
                    idx += 1
                if req.tags is not None:
                    updates.append(f"tags = ${idx}")
                    params.append(json.dumps(req.tags, ensure_ascii=False))
                    idx += 1

                if not updates:
                    raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "没有要更新的字段"})

                params.extend([nid, eid])
                await conn.execute(
                    f"UPDATE notes SET {', '.join(updates)} WHERE id = ${idx} AND enterprise_id = ${idx + 1}",
                    *params,
                )
                return {"message": "更新成功"}
    except HTTPException:
        raise
    except Exception:
        pass

    raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "笔记不存在"})


@router.delete("/api/v1/notes/{note_id}")
async def delete_note(
    note_id: str,
    user: UserInfo = Depends(require_tenant),
):
    """删除笔记"""
    eid = user.enterprise_id or ""

    # 删除内存笔记
    for i, n in enumerate(_memory_notes):
        if n["id"] == note_id and n.get("enterprise_id") == eid:
            _memory_notes.pop(i)
            return {"message": "删除成功"}

    # 删除数据库笔记
    try:
        nid = int(note_id)
    except ValueError:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "笔记不存在"})

    try:
        async with get_db_conn(enterprise_id=eid, user_role=user.role) as conn:
            result = await conn.execute(
                "DELETE FROM notes WHERE id = $1 AND enterprise_id = $2",
                nid, eid,
            )
        if result != "DELETE 0":
            return {"message": "删除成功"}
    except Exception:
        pass

    raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "笔记不存在"})
