"""
平台管理接口

所有接口使用 platform_admin 角色校验。
数据存储：PostgreSQL knowledge_base + compliance_rules 表。

- 公共/行业/模板知识 → knowledge_base（data_level='platform', platform_category 区分）
- 合规词库 → compliance_rules 表
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.db import get_db_conn
from api.deps import require_platform_admin, UserInfo
from api.utils import row_to_dict

router = APIRouter(prefix="/api/v1/platform", tags=["平台管理"])


# ── 请求模型 ──────────────────────────────────────────────


class PublicKnowledgeCreate(BaseModel):
    title: str
    content: str
    category: str
    tags: list[str] = []


class IndustryKnowledgeCreate(BaseModel):
    title: str
    content: str
    category: str
    industry: str
    tags: list[str] = []


class TemplateCreate(BaseModel):
    name: str
    platform: str
    content: str
    category: str


class ComplianceWordCreate(BaseModel):
    word: str
    category: str
    severity: str = "P1"
    suggestion: str = ""


def _compliancerow_to_dict(row) -> dict:
    """compliance_rules 行转为前端格式（level→severity, description→suggestion）"""
    d = dict(row)
    for key in ("created_at", "updated_at"):
        if key in d and d[key] is not None and not isinstance(d[key], str):
            d[key] = d[key].isoformat()
    if "id" in d:
        d["id"] = str(d["id"])
    return {
        "id": d["id"],
        "word": d.get("word", ""),
        "category": d.get("category", ""),
        "severity": (d.get("level") or "P1").lower(),
        "suggestion": d.get("description") or "",
        "created_at": d.get("created_at", ""),
    }


# ── 公共知识库 ────────────────────────────────────────────


@router.get("/knowledge/public")
async def list_public(
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    user: UserInfo = Depends(require_platform_admin),
):
    conditions = ["data_level = 'platform'", "platform_category = 'public'"]
    params: list = []
    idx = 1

    if category:
        conditions.append(f"category = ${idx}")
        params.append(category)
        idx += 1

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        count_row = await conn.fetchrow(f"SELECT COUNT(*) as cnt FROM knowledge_base WHERE {where}", *params)
        rows = await conn.fetch(
            f"SELECT * FROM knowledge_base WHERE {where} ORDER BY created_at DESC LIMIT ${idx} OFFSET ${idx + 1}",
            *params, page_size, offset,
        )

    return {"items": [row_to_dict(r) for r in rows], "total": count_row["cnt"], "page": page}


@router.post("/knowledge/public", status_code=201)
async def create_public(
    req: PublicKnowledgeCreate,
    user: UserInfo = Depends(require_platform_admin),
):
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "INSERT INTO knowledge_base (data_level, platform_category, category, title, content, tags, created_by) "
            "VALUES ('platform', 'public', $1, $2, $3, $4, $5) RETURNING *",
            req.category, req.title, req.content,
            json.dumps(req.tags, ensure_ascii=False), user.user_id,
        )
    return row_to_dict(row)


@router.put("/knowledge/public/{item_id}")
async def update_public(
    item_id: str,
    req: PublicKnowledgeCreate,
    user: UserInfo = Depends(require_platform_admin),
):
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "UPDATE knowledge_base SET title=$1, content=$2, category=$3, tags=$4, updated_at=NOW() "
            "WHERE id=$5 AND data_level='platform' AND platform_category='public' RETURNING *",
            req.title, req.content, req.category,
            json.dumps(req.tags, ensure_ascii=False), int(item_id),
        )
    if not row:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "条目不存在"})
    return row_to_dict(row)


@router.delete("/knowledge/public/{item_id}")
async def delete_public(
    item_id: str,
    user: UserInfo = Depends(require_platform_admin),
):
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "DELETE FROM knowledge_base WHERE id=$1 AND data_level='platform' AND platform_category='public' RETURNING id",
            int(item_id),
        )
    if not row:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "条目不存在"})
    return {"deleted": True}


# ── 行业知识库 ────────────────────────────────────────────


@router.get("/knowledge/industry")
async def list_industry(
    industry: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    user: UserInfo = Depends(require_platform_admin),
):
    conditions = ["data_level = 'platform'", "platform_category = 'industry'"]
    params: list = []
    idx = 1

    if industry:
        conditions.append(f"metadata->>'industry' = ${idx}")
        params.append(industry)
        idx += 1

    where = " AND ".join(conditions)
    offset = (page - 1) * page_size

    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        count_row = await conn.fetchrow(f"SELECT COUNT(*) as cnt FROM knowledge_base WHERE {where}", *params)
        rows = await conn.fetch(
            f"SELECT * FROM knowledge_base WHERE {where} ORDER BY created_at DESC LIMIT ${idx} OFFSET ${idx + 1}",
            *params, page_size, offset,
        )

    items = []
    for r in rows:
        d = row_to_dict(r)
        # 从 metadata 中提取 industry 字段到顶层
        meta = d.get("metadata") or {}
        d["industry"] = meta.get("industry", "")
        items.append(d)

    return {"items": items, "total": count_row["cnt"], "page": page}


@router.post("/knowledge/industry", status_code=201)
async def create_industry(
    req: IndustryKnowledgeCreate,
    user: UserInfo = Depends(require_platform_admin),
):
    metadata = json.dumps({"industry": req.industry}, ensure_ascii=False)
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "INSERT INTO knowledge_base (data_level, platform_category, category, title, content, tags, metadata, created_by) "
            "VALUES ('platform', 'industry', $1, $2, $3, $4, $5, $6) RETURNING *",
            req.category, req.title, req.content,
            json.dumps(req.tags, ensure_ascii=False), metadata, user.user_id,
        )
    d = row_to_dict(row)
    d["industry"] = req.industry
    return d


@router.put("/knowledge/industry/{item_id}")
async def update_industry(
    item_id: str,
    req: IndustryKnowledgeCreate,
    user: UserInfo = Depends(require_platform_admin),
):
    metadata = json.dumps({"industry": req.industry}, ensure_ascii=False)
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "UPDATE knowledge_base SET title=$1, content=$2, category=$3, tags=$4, metadata=$5, updated_at=NOW() "
            "WHERE id=$6 AND data_level='platform' AND platform_category='industry' RETURNING *",
            req.title, req.content, req.category,
            json.dumps(req.tags, ensure_ascii=False), metadata, int(item_id),
        )
    if not row:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "条目不存在"})
    d = row_to_dict(row)
    d["industry"] = req.industry
    return d


@router.delete("/knowledge/industry/{item_id}")
async def delete_industry(
    item_id: str,
    user: UserInfo = Depends(require_platform_admin),
):
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "DELETE FROM knowledge_base WHERE id=$1 AND data_level='platform' AND platform_category='industry' RETURNING id",
            int(item_id),
        )
    if not row:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "条目不存在"})
    return {"deleted": True}


# ── 模板 ──────────────────────────────────────────────────


@router.get("/templates")
async def list_templates(
    platform: Optional[str] = None,
    user: UserInfo = Depends(require_platform_admin),
):
    conditions = ["data_level = 'platform'", "platform_category = 'template'"]
    params: list = []
    idx = 1

    if platform:
        conditions.append(f"category = ${idx}")
        params.append(platform)
        idx += 1

    where = " AND ".join(conditions)

    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        rows = await conn.fetch(f"SELECT * FROM knowledge_base WHERE {where} ORDER BY created_at DESC", *params)

    items = []
    for r in rows:
        d = row_to_dict(r)
        # 前端模板用 name 字段，DB 用 title
        d["name"] = d.get("title", "")
        d["platform"] = d.get("category", "")
        items.append(d)

    return {"items": items, "total": len(items)}


@router.post("/templates", status_code=201)
async def create_template(
    req: TemplateCreate,
    user: UserInfo = Depends(require_platform_admin),
):
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "INSERT INTO knowledge_base (data_level, platform_category, category, title, content, created_by) "
            "VALUES ('platform', 'template', $1, $2, $3, $4) RETURNING *",
            req.platform, req.name, req.content, user.user_id,
        )
    d = row_to_dict(row)
    d["name"] = d.get("title", "")
    d["platform"] = d.get("category", "")
    return d


@router.put("/templates/{item_id}")
async def update_template(
    item_id: str,
    req: TemplateCreate,
    user: UserInfo = Depends(require_platform_admin),
):
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "UPDATE knowledge_base SET category=$1, title=$2, content=$3, updated_at=NOW() "
            "WHERE id=$4 AND data_level='platform' AND platform_category='template' RETURNING *",
            req.platform, req.name, req.content, int(item_id),
        )
    if not row:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "模板不存在"})
    d = row_to_dict(row)
    d["name"] = d.get("title", "")
    d["platform"] = d.get("category", "")
    return d


@router.delete("/templates/{item_id}")
async def delete_template(
    item_id: str,
    user: UserInfo = Depends(require_platform_admin),
):
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "DELETE FROM knowledge_base WHERE id=$1 AND data_level='platform' AND platform_category='template' RETURNING id",
            int(item_id),
        )
    if not row:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "模板不存在"})
    return {"deleted": True}


# ── 合规词库 ──────────────────────────────────────────────


@router.get("/compliance")
async def list_compliance(
    category: Optional[str] = None,
    user: UserInfo = Depends(require_platform_admin),
):
    conditions = ["is_active = true"]
    params: list = []
    idx = 1

    if category:
        conditions.append(f"category = ${idx}")
        params.append(category)
        idx += 1

    where = " AND ".join(conditions)

    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        rows = await conn.fetch(f"SELECT * FROM compliance_rules WHERE {where} ORDER BY id", *params)

    return {"items": [_compliancerow_to_dict(r) for r in rows], "total": len(rows)}


@router.post("/compliance", status_code=201)
async def create_compliance(
    req: ComplianceWordCreate,
    user: UserInfo = Depends(require_platform_admin),
):
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "INSERT INTO compliance_rules (word, level, category, description) VALUES ($1, $2, $3, $4) RETURNING *",
            req.word, req.severity.upper(), req.category, req.suggestion,
        )
    return _compliancerow_to_dict(row)


@router.put("/compliance/{item_id}")
async def update_compliance(
    item_id: str,
    req: ComplianceWordCreate,
    user: UserInfo = Depends(require_platform_admin),
):
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "UPDATE compliance_rules SET word=$1, level=$2, category=$3, description=$4, updated_at=NOW() "
            "WHERE id=$5 RETURNING *",
            req.word, req.severity.upper(), req.category, req.suggestion, int(item_id),
        )
    if not row:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "合规词不存在"})
    return _compliancerow_to_dict(row)


@router.delete("/compliance/{item_id}")
async def delete_compliance(
    item_id: str,
    user: UserInfo = Depends(require_platform_admin),
):
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "DELETE FROM compliance_rules WHERE id=$1 RETURNING id", int(item_id),
        )
    if not row:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "合规词不存在"})
    return {"deleted": True}
