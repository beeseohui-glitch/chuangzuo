"""
会话上下文管理 - PostgreSQL 会话变量 + 连接池
用于 RLS 策略的会话上下文设置
"""

import logging
from typing import Optional
from contextlib import contextmanager

import psycopg2
import psycopg2.pool
import psycopg2.extensions

from config.vector_config import VectorStoreConfig

logger = logging.getLogger(__name__)

# 角色到会话上下文的映射
ROLE_CONTEXT_MAP = {
    "platform_admin": {
        "is_platform_admin": True,
        "is_agent": False,
        "user_role": "platform_admin",
    },
    "platform_operator": {
        "is_platform_admin": True,
        "is_agent": False,
        "user_role": "platform_operator",
    },
    "tenant_admin": {
        "is_platform_admin": False,
        "is_agent": False,
        "user_role": "tenant_admin",
    },
    "tenant": {
        "is_platform_admin": False,
        "is_agent": False,
        "user_role": "tenant",
    },
    "tenant_user": {
        "is_platform_admin": False,
        "is_agent": False,
        "user_role": "tenant_user",
    },
    "agent": {
        "is_platform_admin": False,
        "is_agent": True,
        "user_role": "agent",
    },
}


class SessionManager:
    """
    PostgreSQL 会话管理器

    - 连接池管理
    - 自动设置 RLS 会话变量
    - 根据用户角色设置正确上下文
    """

    def __init__(
        self,
        config: Optional[VectorStoreConfig] = None,
        min_conn: int = 2,
        max_conn: int = 10,
    ):
        self.config = config or VectorStoreConfig()
        self._pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self._min_conn = min_conn
        self._max_conn = max_conn

    def _ensure_pool(self):
        """确保连接池已创建"""
        if self._pool is None:
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                self._min_conn,
                self._max_conn,
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
            )
            logger.info(f"Connection pool created: min={self._min_conn}, max={self._max_conn}")

    @contextmanager
    def get_connection(self):
        """获取连接（上下文管理器，自动归还）"""
        self._ensure_pool()
        conn = self._pool.getconn()
        try:
            yield conn
        finally:
            self._pool.putconn(conn)

    def set_context(
        self,
        conn: psycopg2.extensions.connection,
        enterprise_id: Optional[str] = None,
        is_platform_admin: bool = False,
        is_agent: bool = False,
        user_role: Optional[str] = None,
    ):
        """
        在连接上设置会话变量

        Args:
            conn: 数据库连接
            enterprise_id: 企业ID
            is_platform_admin: 是否平台管理员
            is_agent: 是否 Agent
            user_role: 用户角色
        """
        with conn.cursor() as cur:
            if enterprise_id:
                cur.execute("SET app.enterprise_id = %s", (enterprise_id,))
            else:
                cur.execute("SET app.enterprise_id = ''")
            cur.execute("SET app.is_platform_admin = %s", (str(is_platform_admin).lower(),))
            cur.execute("SET app.is_agent = %s", (str(is_agent).lower(),))
            cur.execute("SET app.user_role = %s", (user_role or "",))
        conn.commit()

    def set_context_by_role(
        self,
        conn: psycopg2.extensions.connection,
        role: str,
        enterprise_id: Optional[str] = None,
    ):
        """
        根据角色自动设置会话上下文

        Args:
            conn: 数据库连接
            role: 用户角色（platform_admin / tenant_admin / agent 等）
            enterprise_id: 企业ID（租户角色必填）
        """
        ctx = ROLE_CONTEXT_MAP.get(role)
        if not ctx:
            raise ValueError(f"Unknown role: {role}. Valid: {list(ROLE_CONTEXT_MAP.keys())}")

        self.set_context(
            conn=conn,
            enterprise_id=enterprise_id if not ctx["is_platform_admin"] else None,
            is_platform_admin=ctx["is_platform_admin"],
            is_agent=ctx["is_agent"],
            user_role=ctx["user_role"],
        )

    def clear_context(self, conn: psycopg2.extensions.connection):
        """清除会话上下文"""
        with conn.cursor() as cur:
            cur.execute("RESET app.enterprise_id")
            cur.execute("RESET app.is_platform_admin")
            cur.execute("RESET app.is_agent")
            cur.execute("RESET app.user_role")
        conn.commit()

    def close(self):
        """关闭连接池"""
        if self._pool:
            self._pool.closeall()
            self._pool = None
            logger.info("Connection pool closed")
