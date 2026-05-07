"""
JWT 认证模块

- token 生成/验证
- 用户信息模型
- 数据库认证（bcrypt）
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
import jwt
from pydantic import BaseModel

from api.db import get_db_conn


# ── 配置 ──────────────────────────────────────────────────

JWT_SECRET = os.getenv("JWT_SECRET", "dev_jwt_secret_change_in_production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


# ── 模型 ──────────────────────────────────────────────────


class UserRole:
    TENANT = "tenant"
    TENANT_ADMIN = "tenant_admin"
    PLATFORM_ADMIN = "platform_admin"


class UserInfo(BaseModel):
    """JWT 中携带的用户信息"""
    user_id: str
    email: str
    role: str  # tenant | tenant_admin | platform_admin
    enterprise_id: Optional[str] = None
    plan: str = "free"
    name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class TokenPayload(BaseModel):
    sub: str
    user_id: str
    email: str
    role: str
    enterprise_id: Optional[str] = None
    plan: str = "free"
    name: str = ""
    exp: int
    iat: int


# ── Token 操作 ─────────────────────────────────────────────


def create_access_token(user: UserInfo) -> str:
    """生成 JWT access token"""
    now = datetime.utcnow()
    payload = {
        "sub": user.user_id,
        "user_id": user.user_id,
        "email": user.email,
        "role": user.role,
        "enterprise_id": user.enterprise_id,
        "plan": user.plan,
        "name": user.name,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=JWT_EXPIRE_HOURS)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """
    解析 JWT token

    Raises:
        jwt.InvalidTokenError: token 无效或过期
    """
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    return TokenPayload(**payload)


async def authenticate(email: str, password: str) -> Optional[UserInfo]:
    """
    验证邮箱密码，查询 users 表 + bcrypt 校验

    Returns:
        UserInfo 或 None（验证失败）
    """
    async with get_db_conn(is_platform_admin=True) as conn:
        row = await conn.fetchrow(
            "SELECT id, email, name, password_hash, role, enterprise_id "
            "FROM users WHERE email = $1 AND status = 'active'",
            email,
        )

    if not row:
        return None

    stored_hash = row["password_hash"]
    if not bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        return None

    # 查询企业 plan
    plan = "free"
    if row["enterprise_id"]:
        async with get_db_conn(is_platform_admin=True) as conn:
            ent = await conn.fetchrow(
                "SELECT plan_type FROM enterprises WHERE id = $1",
                row["enterprise_id"],
            )
            if ent:
                plan = ent["plan_type"]

    return UserInfo(
        user_id=row["id"],
        email=row["email"],
        role=row["role"],
        enterprise_id=row["enterprise_id"],
        plan=plan,
        name=row["name"],
    )
