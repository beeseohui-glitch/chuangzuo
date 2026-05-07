"""
向量工具 - pgvector 写入和语义检索
匹配 knowledge_base 表结构（data_level / platform_category / enterprise_id）
"""

import json
import logging
from typing import Optional

import psycopg2
import psycopg2.extensions
import psycopg2.extras

from config.vector_config import VectorStoreConfig

logger = logging.getLogger(__name__)


class VectorStoreTool:
    """向量存储工具 - pgvector 操作（兼容新表结构）"""

    def __init__(self, config: Optional[VectorStoreConfig] = None):
        self.config = config or VectorStoreConfig()
        self._conn = None

    @property
    def conn(self) -> psycopg2.extensions.connection:
        """数据库连接（自动重连）"""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
            )
            self._conn.autocommit = False
        return self._conn

    def set_session_context(
        self,
        enterprise_id: Optional[str] = None,
        is_platform_admin: bool = False,
        is_agent: bool = False,
        user_role: Optional[str] = None,
    ):
        """
        设置 PostgreSQL 会话变量（RLS 上下文）

        Args:
            enterprise_id: 企业ID
            is_platform_admin: 是否平台管理员
            is_agent: 是否 Agent 系统
            user_role: 用户角色
        """
        # Rollback any failed transaction first
        if self.conn.status != psycopg2.extensions.STATUS_READY:
            self.conn.rollback()

        with self.conn.cursor() as cur:
            if enterprise_id:
                cur.execute("SET app.enterprise_id = %s", (enterprise_id,))
            else:
                cur.execute("SET app.enterprise_id = ''")
            cur.execute("SET app.is_platform_admin = %s", (str(is_platform_admin).lower(),))
            cur.execute("SET app.is_agent = %s", (str(is_agent).lower(),))
            cur.execute("SET app.user_role = %s", (user_role or "",))
            self.conn.commit()

    def clear_session_context(self):
        """清除会话上下文"""
        with self.conn.cursor() as cur:
            cur.execute("RESET app.enterprise_id")
            cur.execute("RESET app.is_platform_admin")
            cur.execute("RESET app.is_agent")
            cur.execute("RESET app.user_role")
            self.conn.commit()

    def insert(
        self,
        title: str,
        content: str,
        embedding: list[float],
        data_level: str = "tenant",
        platform_category: Optional[str] = None,
        enterprise_id: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict] = None,
        created_by: Optional[str] = None,
    ) -> int:
        """
        写入单条知识到 pgvector

        Args:
            title: 标题
            content: 内容
            embedding: 1024 维向量
            data_level: 'platform' 或 'tenant'
            platform_category: 平台级分类 ('public'/'industry'/'template')
            enterprise_id: 租户企业ID
            category: 业务分类
            tags: 标签列表
            metadata: 元数据
            created_by: 创建者

        Returns:
            int: 插入记录的 ID
        """
        sql = """
            INSERT INTO knowledge_base
                (data_level, platform_category, enterprise_id, category,
                 title, content, tags, metadata, embedding, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector, %s)
            RETURNING id
        """
        with self.conn.cursor() as cur:
            cur.execute(sql, (
                data_level,
                platform_category,
                enterprise_id,
                category,
                title,
                content,
                json.dumps(tags or []),
                json.dumps(metadata or {}),
                str(embedding),
                created_by,
            ))
            record_id = cur.fetchone()[0]
            self.conn.commit()
        return record_id

    def batch_insert(
        self,
        records: list[dict],
    ) -> list[int]:
        """
        批量写入知识

        Args:
            records: 记录列表，每条包含 title, content, embedding 等字段

        Returns:
            list[int]: 插入记录的 ID 列表
        """
        if not records:
            return []

        ids = []
        sql = """
            INSERT INTO knowledge_base
                (data_level, platform_category, enterprise_id, category,
                 title, content, tags, metadata, embedding, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector, %s)
            RETURNING id
        """
        with self.conn.cursor() as cur:
            for r in records:
                cur.execute(sql, (
                    r.get("data_level", "tenant"),
                    r.get("platform_category"),
                    r.get("enterprise_id"),
                    r.get("category"),
                    r["title"],
                    r["content"],
                    json.dumps(r.get("tags", [])),
                    json.dumps(r.get("metadata", {})),
                    str(r["embedding"]),
                    r.get("created_by"),
                ))
                ids.append(cur.fetchone()[0])
            self.conn.commit()
        return ids

    def search(
        self,
        embedding: list[float],
        top_k: int = 10,
        data_level: Optional[str] = None,
        enterprise_id: Optional[str] = None,
        platform_category: Optional[str] = None,
        category: Optional[str] = None,
        min_similarity: float = 0.0,
    ) -> list[dict]:
        """
        语义搜索（使用内积操作符 <#>，向量已归一化）

        Args:
            embedding: 查询向量
            top_k: 返回数量
            data_level: 过滤数据级别
            enterprise_id: 过滤企业ID
            platform_category: 过滤平台分类
            category: 过滤业务分类
            min_similarity: 最小相似度阈值

        Returns:
            list[dict]: 检索结果，包含 id, title, content, similarity 等
        """
        if top_k > self.config.search_config.max_limit:
            top_k = self.config.search_config.max_limit

        conditions = []
        condition_params = []

        if data_level:
            conditions.append("data_level = %s")
            condition_params.append(data_level)

        if enterprise_id:
            conditions.append("enterprise_id = %s")
            condition_params.append(enterprise_id)

        if platform_category:
            conditions.append("platform_category = %s")
            condition_params.append(platform_category)

        if category:
            conditions.append("category = %s")
            condition_params.append(category)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        # 内积操作符 <#>：向量已归一化时，内积 = 余弦相似度
        # <#> 返回的是负内积（越小越相似），所以用 -(<#>) 作为相似度分数
        vec_str = str(embedding)
        sql = f"""
            SELECT id, data_level, platform_category, enterprise_id,
                   category, title, content, tags, metadata, created_by,
                   created_at, updated_at,
                   -1 * (embedding <#> %s::vector) AS similarity
            FROM knowledge_base
            WHERE {where_clause}
              AND -1 * (embedding <#> %s::vector) >= %s
            ORDER BY embedding <#> %s::vector
            LIMIT %s
        """
        # 参数顺序：SELECT中的向量、WHERE条件参数、WHERE中的向量、min_similarity、ORDER BY中的向量、top_k
        params = [vec_str] + condition_params + [vec_str, min_similarity, vec_str, top_k]

        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        results = []
        for row in rows:
            r = dict(row)
            r["id"] = r["id"]
            r["similarity"] = float(r["similarity"])
            # 解析 JSON 字段
            if isinstance(r.get("tags"), str):
                r["tags"] = json.loads(r["tags"])
            if isinstance(r.get("metadata"), str):
                r["metadata"] = json.loads(r["metadata"])
            results.append(r)

        return results

    def count(
        self,
        data_level: Optional[str] = None,
        enterprise_id: Optional[str] = None,
        platform_category: Optional[str] = None,
    ) -> int:
        """统计记录数"""
        conditions = []
        params = []

        if data_level:
            conditions.append("data_level = %s")
            params.append(data_level)
        if enterprise_id:
            conditions.append("enterprise_id = %s")
            params.append(enterprise_id)
        if platform_category:
            conditions.append("platform_category = %s")
            params.append(platform_category)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        with self.conn.cursor() as cur:
            cur.execute(f"SELECT count(*) FROM knowledge_base WHERE {where_clause}", params)
            return cur.fetchone()[0]

    def close(self):
        """关闭连接"""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None
