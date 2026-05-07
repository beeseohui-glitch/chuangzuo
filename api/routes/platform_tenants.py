"""
平台管理 - 租户管理接口

所有接口使用 platform_admin 角色校验。
数据存储：PostgreSQL enterprises + users 表。

功能：
- 企业 CRUD（列表/详情/新增/编辑/软删除）
- 企业状态管理（active/suspended/terminated）
- 企业额度管理
- 企业用户管理（列表/新增/编辑/重置密码/禁用启用）
- 企业使用统计
- 企业操作日志
"""

import uuid
from datetime import datetime
from typing import Optional

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from api.db import get_db_conn
from api.deps import require_platform_admin, UserInfo
from api.utils import row_to_dict

router = APIRouter(prefix="/api/v1/platform", tags=["平台管理-租户"])


# ── 请求模型 ──────────────────────────────────────────────


class TenantCreate(BaseModel):
    name: str
    industry: Optional[str] = None
    plan_type: str = "free"
    quota_monthly: int = 100
    admin_email: str
    admin_password: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    plan_type: Optional[str] = None
    quota_monthly: Optional[int] = None
    status: Optional[str] = None
    expire_at: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None


class TenantStatusUpdate(BaseModel):
    status: str  # active / suspended / terminated


class TenantQuotaUpdate(BaseModel):
    quota_monthly: int
    reason: Optional[str] = None


class UserCreate(BaseModel):
    email: str
    name: str
    password: Optional[str] = None
    role: str = "tenant"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class UserPasswordReset(BaseModel):
    new_password: Optional[str] = None


class UserStatusUpdate(BaseModel):
    status: str  # active / disabled


# ── 辅助函数 ──────────────────────────────────────────────


def _hash_password(password: str) -> str:
    """bcrypt 哈希密码"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _generate_password() -> str:
    """生成随机密码"""
    return uuid.uuid4().hex[:12]


def _enterprise_to_dict(row) -> dict:
    """enterprises 行转为前端格式"""
    d = dict(row)
    for key in ("created_at", "updated_at", "expire_at", "last_active"):
        if key in d and d[key] is not None and not isinstance(d[key], str):
            d[key] = d[key].isoformat()
    if "id" in d:
        d["id"] = str(d["id"])
    # settings 字段可能是 JSONB
    if "settings" in d and isinstance(d["settings"], str):
        import json
        try:
            d["settings"] = json.loads(d["settings"])
        except Exception:
            d["settings"] = {}
    return d


def _user_to_dict(row) -> dict:
    """users 行转为前端格式（隐藏密码哈希）"""
    d = dict(row)
    for key in ("created_at", "updated_at", "last_login_at"):
        if key in d and d[key] is not None and not isinstance(d[key], str):
            d[key] = d[key].isoformat()
    if "id" in d:
        d["id"] = str(d["id"])
    d.pop("password_hash", None)
    return d


# ── 企业列表 ──────────────────────────────────────────────


@router.get("/tenants")
async def list_tenants(
    plan: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    user: UserInfo = Depends(require_platform_admin),
):
    """企业列表（分页+筛选）"""
    conditions: list[str] = []
    params: list = []
    idx = 1

    if plan:
        conditions.append(f"plan_type = ${idx}")
        params.append(plan)
        idx += 1

    if status_filter:
        conditions.append(f"status = ${idx}")
        params.append(status_filter)
        idx += 1

    if search:
        conditions.append(f"(name ILIKE ${idx} OR industry ILIKE ${idx})")
        params.append(f"%{search}%")
        idx += 1

    where = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (page - 1) * page_size

    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        count_row = await conn.fetchrow(
            f"SELECT COUNT(*) as cnt FROM enterprises {where}", *params
        )
        rows = await conn.fetch(
            f"SELECT * FROM enterprises {where} ORDER BY created_at DESC "
            f"LIMIT ${idx} OFFSET ${idx + 1}",
            *params, page_size, offset,
        )

        # 获取每个企业的用户数
        items = []
        for r in rows:
            d = _enterprise_to_dict(r)
            user_count = await conn.fetchrow(
                "SELECT COUNT(*) as cnt FROM users WHERE enterprise_id = $1",
                d["id"],
            )
            d["user_count"] = user_count["cnt"] if user_count else 0
            items.append(d)

    return {"items": items, "total": count_row["cnt"], "page": page, "page_size": page_size}


# ── 企业详情 ──────────────────────────────────────────────


@router.get("/tenants/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    user: UserInfo = Depends(require_platform_admin),
):
    """企业详情"""
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "SELECT * FROM enterprises WHERE id = $1", tenant_id
        )
    if not row:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "企业不存在"})

    d = _enterprise_to_dict(row)

    # 获取用户数
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        user_count = await conn.fetchrow(
            "SELECT COUNT(*) as cnt FROM users WHERE enterprise_id = $1", tenant_id
        )
        d["user_count"] = user_count["cnt"] if user_count else 0

    return d


# ── 新增企业 ──────────────────────────────────────────────


@router.post("/tenants", status_code=201)
async def create_tenant(
    req: TenantCreate,
    user: UserInfo = Depends(require_platform_admin),
):
    """新增企业（自动创建管理员账号）"""
    tenant_id = f"ent_{uuid.uuid4().hex[:8]}"
    admin_id = f"usr_{uuid.uuid4().hex[:8]}"
    admin_password = req.admin_password or _generate_password()
    password_hash = _hash_password(admin_password)

    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        # 检查邮箱是否已存在
        existing = await conn.fetchrow(
            "SELECT id FROM users WHERE email = $1", req.admin_email
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail={"error": "CONFLICT", "message": f"邮箱 {req.admin_email} 已被使用"},
            )

        # 创建企业
        await conn.execute(
            "INSERT INTO enterprises (id, name, industry, plan_type, quota_monthly, "
            "contact_name, contact_email, contact_phone, status) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'active')",
            tenant_id, req.name, req.industry, req.plan_type,
            req.quota_monthly, req.contact_name, req.contact_email, req.contact_phone,
        )

        # 创建管理员用户
        await conn.execute(
            "INSERT INTO users (id, email, name, password_hash, role, enterprise_id, status) "
            "VALUES ($1, $2, $3, $4, 'tenant_admin', $5, 'active')",
            admin_id, req.admin_email, f"{req.name}管理员", password_hash, tenant_id,
        )

        # 写审计日志
        await conn.execute(
            "INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details) "
            "VALUES ($1, 'create', 'enterprise', $2, $3)",
            user.user_id, tenant_id,
            f'{{"name": "{req.name}", "admin_email": "{req.admin_email}"}}',
        )

        row = await conn.fetchrow("SELECT * FROM enterprises WHERE id = $1", tenant_id)

    result = _enterprise_to_dict(row)
    result["admin_email"] = req.admin_email
    result["admin_password"] = admin_password
    result["user_count"] = 1
    return result


# ── 编辑企业 ──────────────────────────────────────────────


@router.put("/tenants/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    req: TenantUpdate,
    user: UserInfo = Depends(require_platform_admin),
):
    """编辑企业信息"""
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        existing = await conn.fetchrow(
            "SELECT id FROM enterprises WHERE id = $1", tenant_id
        )
        if not existing:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "企业不存在"})

        # 动态构建 UPDATE 语句
        updates: list[str] = []
        params: list = []
        idx = 1

        field_map = {
            "name": req.name,
            "industry": req.industry,
            "plan_type": req.plan_type,
            "quota_monthly": req.quota_monthly,
            "status": req.status,
            "contact_name": req.contact_name,
            "contact_email": req.contact_email,
            "contact_phone": req.contact_phone,
        }

        for field, value in field_map.items():
            if value is not None:
                updates.append(f"{field} = ${idx}")
                params.append(value)
                idx += 1

        if req.expire_at is not None:
            updates.append(f"expire_at = ${idx}")
            if req.expire_at:
                try:
                    params.append(datetime.fromisoformat(req.expire_at))
                except ValueError:
                    params.append(None)
            else:
                params.append(None)
            idx += 1

        if not updates:
            raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "无更新字段"})

        updates.append("updated_at = NOW()")
        params.append(tenant_id)

        row = await conn.fetchrow(
            f"UPDATE enterprises SET {', '.join(updates)} WHERE id = ${idx} RETURNING *",
            *params,
        )

        # 审计日志
        await conn.execute(
            "INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details) "
            "VALUES ($1, 'update', 'enterprise', $2, $3)",
            user.user_id, tenant_id, '{"fields_updated": true}',
        )

    return _enterprise_to_dict(row)


# ── 删除企业（软删除 → terminated）────────────────────────


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    user: UserInfo = Depends(require_platform_admin),
):
    """删除企业（软删除：状态设为 terminated）"""
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "UPDATE enterprises SET status = 'terminated', updated_at = NOW() "
            "WHERE id = $1 RETURNING id",
            tenant_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "企业不存在"})

        # 同时禁用该企业所有用户
        await conn.execute(
            "UPDATE users SET status = 'disabled', updated_at = NOW() WHERE enterprise_id = $1",
            tenant_id,
        )

        await conn.execute(
            "INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details) "
            "VALUES ($1, 'delete', 'enterprise', $2, '{}')",
            user.user_id, tenant_id,
        )

    return {"deleted": True}


# ── 修改企业状态 ──────────────────────────────────────────


@router.put("/tenants/{tenant_id}/status")
async def update_tenant_status(
    tenant_id: str,
    req: TenantStatusUpdate,
    user: UserInfo = Depends(require_platform_admin),
):
    """修改企业状态（active/suspended/terminated）"""
    if req.status not in ("active", "suspended", "terminated"):
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "无效状态"})

    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "UPDATE enterprises SET status = $1, updated_at = NOW() WHERE id = $2 RETURNING *",
            req.status, tenant_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "企业不存在"})

        # 如果停用/终止，同步禁用/启用用户
        if req.status == "suspended":
            await conn.execute(
                "UPDATE users SET status = 'disabled', updated_at = NOW() WHERE enterprise_id = $1 AND status = 'active'",
                tenant_id,
            )
        elif req.status == "active":
            await conn.execute(
                "UPDATE users SET status = 'active', updated_at = NOW() WHERE enterprise_id = $1 AND status = 'disabled'",
                tenant_id,
            )

        await conn.execute(
            "INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details) "
            "VALUES ($1, 'update', 'enterprise', $2, $3)",
            user.user_id, tenant_id, f'{{"status": "{req.status}"}}',
        )

    return _enterprise_to_dict(row)


# ── 调整额度 ──────────────────────────────────────────────


@router.put("/tenants/{tenant_id}/quota")
async def update_tenant_quota(
    tenant_id: str,
    req: TenantQuotaUpdate,
    user: UserInfo = Depends(require_platform_admin),
):
    """调整企业月度额度"""
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "UPDATE enterprises SET quota_monthly = $1, updated_at = NOW() WHERE id = $2 RETURNING *",
            req.quota_monthly, tenant_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "企业不存在"})

        await conn.execute(
            "INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details) "
            "VALUES ($1, 'update', 'enterprise', $2, $3)",
            user.user_id, tenant_id,
            f'{{"quota_monthly": {req.quota_monthly}, "reason": "{req.reason or ""}"}}',
        )

    return _enterprise_to_dict(row)


# ── 企业用户列表 ──────────────────────────────────────────


@router.get("/tenants/{tenant_id}/users")
async def list_tenant_users(
    tenant_id: str,
    user: UserInfo = Depends(require_platform_admin),
):
    """获取企业下的用户列表"""
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        # 确认企业存在
        ent = await conn.fetchrow("SELECT id FROM enterprises WHERE id = $1", tenant_id)
        if not ent:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "企业不存在"})

        rows = await conn.fetch(
            "SELECT * FROM users WHERE enterprise_id = $1 ORDER BY created_at DESC",
            tenant_id,
        )

    return {"items": [_user_to_dict(r) for r in rows], "total": len(rows)}


# ── 新增用户 ──────────────────────────────────────────────


@router.post("/tenants/{tenant_id}/users", status_code=201)
async def create_tenant_user(
    tenant_id: str,
    req: UserCreate,
    user: UserInfo = Depends(require_platform_admin),
):
    """在企业下新增用户"""
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        # 确认企业存在
        ent = await conn.fetchrow("SELECT id FROM enterprises WHERE id = $1", tenant_id)
        if not ent:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "企业不存在"})

        # 检查邮箱唯一
        existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", req.email)
        if existing:
            raise HTTPException(status_code=409, detail={"error": "CONFLICT", "message": f"邮箱 {req.email} 已被使用"})

        user_id = f"usr_{uuid.uuid4().hex[:8]}"
        password = req.password or _generate_password()
        password_hash = _hash_password(password)

        row = await conn.fetchrow(
            "INSERT INTO users (id, email, name, password_hash, role, enterprise_id, status) "
            "VALUES ($1, $2, $3, $4, $5, $6, 'active') RETURNING *",
            user_id, req.email, req.name, password_hash, req.role, tenant_id,
        )

    result = _user_to_dict(row)
    result["password"] = password
    return result


# ── 编辑用户 ──────────────────────────────────────────────


@router.put("/platform/users/{user_id}")
async def update_user(
    user_id: str,
    req: UserUpdate,
    user: UserInfo = Depends(require_platform_admin),
):
    """编辑用户信息"""
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        updates: list[str] = []
        params: list = []
        idx = 1

        if req.name is not None:
            updates.append(f"name = ${idx}")
            params.append(req.name)
            idx += 1
        if req.role is not None:
            updates.append(f"role = ${idx}")
            params.append(req.role)
            idx += 1
        if req.status is not None:
            updates.append(f"status = ${idx}")
            params.append(req.status)
            idx += 1

        if not updates:
            raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "无更新字段"})

        updates.append("updated_at = NOW()")
        params.append(user_id)

        row = await conn.fetchrow(
            f"UPDATE users SET {', '.join(updates)} WHERE id = ${idx} RETURNING *",
            *params,
        )
        if not row:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "用户不存在"})

    return _user_to_dict(row)


# ── 重置密码 ──────────────────────────────────────────────


@router.put("/platform/users/{user_id}/reset-pwd")
async def reset_user_password(
    user_id: str,
    req: UserPasswordReset,
    user: UserInfo = Depends(require_platform_admin),
):
    """重置用户密码"""
    new_password = req.new_password or _generate_password()
    password_hash = _hash_password(new_password)

    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "UPDATE users SET password_hash = $1, updated_at = NOW() WHERE id = $2 RETURNING id",
            password_hash, user_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "用户不存在"})

    return {"success": True, "new_password": new_password}


# ── 用户状态（禁用/启用）──────────────────────────────────


@router.put("/platform/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    req: UserStatusUpdate,
    user: UserInfo = Depends(require_platform_admin),
):
    """禁用/启用用户"""
    if req.status not in ("active", "disabled"):
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "无效状态"})

    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        row = await conn.fetchrow(
            "UPDATE users SET status = $1, updated_at = NOW() WHERE id = $2 RETURNING *",
            req.status, user_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "用户不存在"})

    return _user_to_dict(row)


# ── 企业使用统计 ──────────────────────────────────────────


@router.get("/tenants/{tenant_id}/stats")
async def get_tenant_stats(
    tenant_id: str,
    user: UserInfo = Depends(require_platform_admin),
):
    """企业使用统计"""
    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        ent = await conn.fetchrow("SELECT id FROM enterprises WHERE id = $1", tenant_id)
        if not ent:
            raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "企业不存在"})

        # 本月创作篇数
        notes_count = await conn.fetchrow(
            "SELECT COUNT(*) as cnt FROM notes WHERE enterprise_id = $1 "
            "AND created_at >= date_trunc('month', CURRENT_DATE)",
            tenant_id,
        )

        # AI味评分均值
        avg_score = await conn.fetchrow(
            "SELECT AVG(ai_flavor_score) as avg_score FROM notes WHERE enterprise_id = $1 "
            "AND ai_flavor_score IS NOT NULL AND created_at >= date_trunc('month', CURRENT_DATE)",
            tenant_id,
        )

        # 合规率（compliance_status = 'passed' 的比例）
        compliance_stats = await conn.fetchrow(
            "SELECT "
            "COUNT(*) as total, "
            "COUNT(*) FILTER (WHERE compliance_status = 'passed') as passed "
            "FROM notes WHERE enterprise_id = $1 "
            "AND created_at >= date_trunc('month', CURRENT_DATE)",
            tenant_id,
        )

        total_notes = compliance_stats["total"] if compliance_stats else 0
        passed_notes = compliance_stats["passed"] if compliance_stats else 0
        compliance_rate = (passed_notes / total_notes * 100) if total_notes > 0 else 0

        # 总创作篇数
        total_notes_all = await conn.fetchrow(
            "SELECT COUNT(*) as cnt FROM notes WHERE enterprise_id = $1",
            tenant_id,
        )

    return {
        "monthly_notes": notes_count["cnt"] if notes_count else 0,
        "monthly_avg_ai_score": round(float(avg_score["avg_score"] or 0), 1),
        "monthly_compliance_rate": round(compliance_rate, 1),
        "total_notes": total_notes_all["cnt"] if total_notes_all else 0,
    }


# ── 企业操作日志 ──────────────────────────────────────────


@router.get("/tenants/{tenant_id}/logs")
async def get_tenant_logs(
    tenant_id: str,
    page: int = 1,
    page_size: int = 20,
    user: UserInfo = Depends(require_platform_admin),
):
    """企业操作日志"""
    offset = (page - 1) * page_size

    async with get_db_conn(is_platform_admin=True, user_role="platform_admin") as conn:
        count_row = await conn.fetchrow(
            "SELECT COUNT(*) as cnt FROM audit_logs WHERE enterprise_id = $1",
            tenant_id,
        )
        rows = await conn.fetch(
            "SELECT al.*, u.name as user_name, u.email as user_email "
            "FROM audit_logs al LEFT JOIN users u ON al.user_id = u.id "
            "WHERE al.enterprise_id = $1 ORDER BY al.created_at DESC "
            "LIMIT $2 OFFSET $3",
            tenant_id, page_size, offset,
        )

    items = []
    for r in rows:
        d = row_to_dict(r, extra_datetime_keys=())
        items.append(d)

    return {"items": items, "total": count_row["cnt"], "page": page}
