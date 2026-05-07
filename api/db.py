"""
异步数据库连接池 (asyncpg) + RLS 上下文管理

FastAPI 路由使用此模块获取带 RLS 会话变量的数据库连接。
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """获取或创建连接池单例"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "content_agent"),
            user=os.getenv("DB_USER", "agent"),
            password=os.getenv("DB_PASSWORD", "your_password_here"),
            min_size=2,
            max_size=10,
        )
    return _pool


@asynccontextmanager
async def get_db_conn(
    enterprise_id: Optional[str] = None,
    is_platform_admin: bool = False,
    user_role: Optional[str] = None,
):
    """
    获取带 RLS 上下文的数据库连接。

    用法:
        async with get_db_conn(enterprise_id="ent_001", user_role="tenant_admin") as conn:
            rows = await conn.fetch("SELECT * FROM knowledge_base")
    """
    pool = await get_pool()
    conn = await pool.acquire()
    try:
        eid = (enterprise_id or "").replace("'", "''")
        role = (user_role or "").replace("'", "''")
        admin = str(is_platform_admin).lower()
        await conn.execute(f"SET app.enterprise_id = '{eid}'")
        await conn.execute(f"SET app.is_platform_admin = '{admin}'")
        await conn.execute("SET app.is_agent = 'false'")
        await conn.execute(f"SET app.user_role = '{role}'")
        yield conn
    finally:
        await conn.execute("RESET ALL")
        await pool.release(conn)


async def close_pool():
    """关闭连接池（应用关闭时调用）"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
