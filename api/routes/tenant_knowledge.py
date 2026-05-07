"""
租户知识库接口

所有接口使用 tenant 角色校验，enterprise_id 从 token 自动注入。
数据存储：PostgreSQL knowledge_base 表 + COS 文件存储。

- GET    /api/v1/tenant/knowledge/tree    分类树
- GET    /api/v1/tenant/knowledge/items   列表+分页+搜索
- POST   /api/v1/tenant/knowledge/items   新增
- PUT    /api/v1/tenant/knowledge/items/{id}  编辑
- DELETE /api/v1/tenant/knowledge/items/{id}  删除
- POST   /api/v1/tenant/knowledge/upload  文件上传（COS）
- POST   /api/v1/tenant/knowledge/search  语义搜索
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel

from api.db import get_db_conn
from api.deps import require_tenant, UserInfo
from api.utils import row_to_dict

router = APIRouter(prefix="/api/v1/tenant/knowledge", tags=["租户知识库"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# ── 请求/响应模型 ─────────────────────────────────────────


class KnowledgeItemCreate(BaseModel):
    title: str
    content: str
    category: str
    tags: list[str] = []


class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[list[str]] = None


class SemanticSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 10


# ── 接口 ──────────────────────────────────────────────────


@router.get("/tree")
async def get_knowledge_tree(
    user: UserInfo = Depends(require_tenant),
):
    """获取知识库分类树"""
    async with get_db_conn(enterprise_id=user.enterprise_id, user_role=user.role) as conn:
        rows = await conn.fetch(
            "SELECT category, COUNT(*) as cnt FROM knowledge_base "
            "WHERE data_level = 'tenant' AND enterprise_id = $1 "
            "GROUP BY category ORDER BY category",
            user.enterprise_id,
        )
        items_by_cat = await conn.fetch(
            "SELECT id, title, category FROM knowledge_base "
            "WHERE data_level = 'tenant' AND enterprise_id = $1 ORDER BY created_at DESC",
            user.enterprise_id,
        )

    categories: dict[str, list] = {}
    for item in items_by_cat:
        cat = item["category"] or "未分类"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({"id": str(item["id"]), "title": item["title"]})

    total = sum(r["cnt"] for r in rows)
    tree = [
        {"category": cat, "count": len(children), "items": children}
        for cat, children in categories.items()
    ]
    return {"tree": tree, "total_items": total}


@router.get("/items")
async def list_items(
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    user: UserInfo = Depends(require_tenant),
):
    """知识条目列表（分页+搜索）"""
    conditions = ["data_level = 'tenant'", "enterprise_id = $1"]
    params: list = [user.enterprise_id]
    idx = 2

    if category:
        conditions.append(f"category = ${idx}")
        params.append(category)
        idx += 1
    if keyword:
        conditions.append(f"(title ILIKE ${idx} OR content ILIKE ${idx})")
        params.append(f"%{keyword}%")
        idx += 1

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    async with get_db_conn(enterprise_id=user.enterprise_id, user_role=user.role) as conn:
        count_row = await conn.fetchrow(f"SELECT COUNT(*) as cnt FROM knowledge_base WHERE {where}", *params)
        total = count_row["cnt"]
        rows = await conn.fetch(
            f"SELECT * FROM knowledge_base WHERE {where} ORDER BY created_at DESC LIMIT ${idx} OFFSET ${idx + 1}",
            *params, page_size, offset,
        )

    return {
        "items": [row_to_dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


@router.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item(
    req: KnowledgeItemCreate,
    user: UserInfo = Depends(require_tenant),
):
    """新增知识条目"""
    async with get_db_conn(enterprise_id=user.enterprise_id, user_role=user.role) as conn:
        row = await conn.fetchrow(
            "INSERT INTO knowledge_base (data_level, enterprise_id, category, title, content, tags, source, created_by) "
            "VALUES ('tenant', $1, $2, $3, $4, $5, 'manual', $6) RETURNING *",
            user.enterprise_id, req.category, req.title, req.content,
            json.dumps(req.tags, ensure_ascii=False), user.user_id,
        )
    return row_to_dict(row)


@router.put("/items/{item_id}")
async def update_item(
    item_id: str,
    req: KnowledgeItemUpdate,
    user: UserInfo = Depends(require_tenant),
):
    """编辑知识条目"""
    async with get_db_conn(enterprise_id=user.enterprise_id, user_role=user.role) as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM knowledge_base WHERE id = $1 AND data_level = 'tenant' AND enterprise_id = $2",
            int(item_id), user.enterprise_id,
        )
        if not existing:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "知识条目不存在"})

        row = await conn.fetchrow(
            "UPDATE knowledge_base SET "
            "title = COALESCE($1, title), "
            "content = COALESCE($2, content), "
            "category = COALESCE($3, category), "
            "tags = COALESCE($4, tags), "
            "updated_at = NOW() "
            "WHERE id = $5 RETURNING *",
            req.title, req.content, req.category,
            json.dumps(req.tags, ensure_ascii=False) if req.tags is not None else None,
            int(item_id),
        )
    return row_to_dict(row)


@router.delete("/items/{item_id}")
async def delete_item(
    item_id: str,
    user: UserInfo = Depends(require_tenant),
):
    """删除知识条目"""
    async with get_db_conn(enterprise_id=user.enterprise_id, user_role=user.role) as conn:
        row = await conn.fetchrow(
            "DELETE FROM knowledge_base WHERE id = $1 AND data_level = 'tenant' AND enterprise_id = $2 RETURNING id",
            int(item_id), user.enterprise_id,
        )
    if not row:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "知识条目不存在"})
    return {"deleted": True, "id": str(row["id"])}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = "manual",
    user: UserInfo = Depends(require_tenant),
):
    """文件上传 → COS + knowledge_base"""
    content = await file.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail={"error": "FILE_TOO_LARGE", "message": "文件大小超过10MB限制"})

    # 上传到 COS
    cos_url = None
    try:
        from tools.cos_tools import COSUploadTool
        cos_tool = COSUploadTool()
        safe_filename = file.filename or "unnamed"
        cos_key = f"{user.enterprise_id}/{uuid.uuid4().hex}/{safe_filename}"
        cos_url = await asyncio.to_thread(cos_tool.upload_bytes, content, cos_key)
    except Exception:
        # COS 上传失败不阻塞，文件内容仍存入数据库
        pass

    text = content.decode("utf-8", errors="replace")[:5000]
    metadata = {}
    if cos_url:
        metadata["cos_url"] = cos_url

    async with get_db_conn(enterprise_id=user.enterprise_id, user_role=user.role) as conn:
        row = await conn.fetchrow(
            "INSERT INTO knowledge_base (data_level, enterprise_id, category, title, content, source, metadata, created_by) "
            "VALUES ('tenant', $1, $2, $3, $4, 'upload', $5, $6) RETURNING *",
            user.enterprise_id, category, file.filename or "未命名文件",
            text, json.dumps(metadata, ensure_ascii=False), user.user_id,
        )
    return row_to_dict(row)


@router.post("/search")
async def semantic_search(
    req: SemanticSearchRequest,
    user: UserInfo = Depends(require_tenant),
):
    """语义搜索（ILIKE 关键词匹配，向量搜索后续集成）"""
    conditions = ["data_level = 'tenant'", "enterprise_id = $1", "(title ILIKE $2 OR content ILIKE $2)"]
    params: list = [user.enterprise_id, f"%{req.query}%"]

    if req.category:
        conditions.append("category = $3")
        params.append(req.category)

    where = " AND ".join(conditions)

    async with get_db_conn(enterprise_id=user.enterprise_id, user_role=user.role) as conn:
        rows = await conn.fetch(
            f"SELECT * FROM knowledge_base WHERE {where} ORDER BY created_at DESC LIMIT ${len(params) + 1}",
            *params, req.limit,
        )

    entries = [row_to_dict(r) for r in rows]
    for e in entries:
        e["score"] = 1.0  # ILIKE 匹配统一给 1.0 分

    return {"entries": entries, "total": len(entries), "query": req.query}
