"""
Vector 工具 - pgvector 写入和检索
"""

from typing import Optional
import uuid
import psycopg2
from psycopg2.extras import execute_values
from crewai.tools import BaseTool
from pydantic import Field

from config import VectorStoreConfig, VectorIndexConfig, IndexType


class VectorStoreTool(BaseTool):
    """向量存储工具 - pgvector 操作"""

    name: str = "vector_store"
    description: str = "存储和检索知识库向量数据"

    def __init__(self, config: Optional[VectorStoreConfig] = None):
        super().__init__()
        self.config = config or VectorStoreConfig()
        self._conn = None

    @property
    def conn(self):
        """数据库连接"""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
            )
        return self._conn

    def _run(
        self,
        text: str,
        embedding: list[float],
        enterprise_id: str,
        category: str = "default",
        metadata: Optional[dict] = None,
    ) -> str:
        """
        BaseTool 接口 - 存储单个向量

        Args:
            text: 文本内容
            embedding: 向量
            enterprise_id: 企业ID
            category: 分类
            metadata: 额外元数据

        Returns:
            str: 插入记录的ID
        """
        record_id = str(uuid.uuid4())
        metadata_json = psycopg2.extras.Json(metadata or {})

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {self.config.knowledge_table}
                (id, enterprise_id, category, title, content, metadata, embedding)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record_id,
                    uuid.UUID(enterprise_id),
                    category,
                    text[:500],
                    text,
                    metadata_json,
                    embedding,
                ),
            )
            self.conn.commit()

        return record_id

    def batch_insert(
        self,
        records: list[dict],
        enterprise_id: str,
    ) -> list[str]:
        """
        批量插入向量

        Args:
            records: 记录列表，每条记录包含 text, embedding, category, metadata
            enterprise_id: 企业ID

        Returns:
            list[str]: 插入记录的ID列表
        """
        ids = []
        values = []

        for record in records:
            record_id = str(uuid.uuid4())
            ids.append(record_id)
            values.append(
                (
                    record_id,
                    uuid.UUID(enterprise_id),
                    record.get("category", "default"),
                    record["text"][:500],
                    record["text"],
                    psycopg2.extras.Json(record.get("metadata", {})),
                    record["embedding"],
                )
            )

        with self.conn.cursor() as cur:
            execute_values(
                cur,
                f"""
                INSERT INTO {self.config.knowledge_table}
                (id, enterprise_id, category, title, content, metadata, embedding)
                VALUES %s
                """,
                values,
            )
            self.conn.commit()

        return ids

    def search(
        self,
        embedding: list[float],
        enterprise_id: str,
        limit: int = 10,
        category: Optional[str] = None,
        min_similarity: float = 0.5,
    ) -> list[dict]:
        """
        向量检索

        Args:
            embedding: 查询向量
            enterprise_id: 企业ID
            limit: 返回数量
            category: 可选，限定分类
            min_similarity: 最小相似度

        Returns:
            list[dict]: 检索结果列表
        """
        if limit > self.config.search_config.max_limit:
            limit = self.config.search_config.max_limit

        category_filter = ""
        params = [embedding, uuid.UUID(enterprise_id)]

        if category:
            category_filter = "AND category = %s"
            params.append(category)

        # 使用内积操作符（向量已归一化）
        sql = f"""
            SELECT id, category, title, content, metadata,
                   (embedding <=> %s::vector) as similarity
            FROM {self.config.knowledge_table}
            WHERE enterprise_id = %s {category_filter}
              AND (embedding <=> %s::vector) < %s
            ORDER BY embedding <#> %s::vector
            LIMIT %s
        """
        params.extend([1 - min_similarity, embedding, limit])

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "id": str(row[0]),
                    "category": row[1],
                    "title": row[2],
                    "content": row[3],
                    "metadata": row[4],
                    "similarity": 1 - row[5],  # 转换为相似度
                }
            )

        return results

    def delete(self, record_id: str, enterprise_id: str) -> bool:
        """删除记录"""
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                DELETE FROM {self.config.knowledge_table}
                WHERE id = %s AND enterprise_id = %s
                """,
                (uuid.UUID(record_id), uuid.UUID(enterprise_id)),
            )
            self.conn.commit()
            return cur.rowcount > 0

    def create_index(self, index_type: IndexType = IndexType.IVFFLAT) -> str:
        """
        创建向量索引

        Args:
            index_type: 索引类型

        Returns:
            str: 执行结果
        """
        with self.conn.cursor() as cur:
            if index_type == IndexType.IVFFLAT:
                cur.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_knowledge_base_embedding
                    ON {self.config.knowledge_table}
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = {self.config.index_config.lists})
                    """
                )
            elif index_type == IndexType.HNSW:
                cur.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_knowledge_base_embedding
                    ON {self.config.knowledge_table}
                    USING hnsw (embedding vector_cosine_ops)
                    WITH (m = {self.config.index_config.m}, ef_construction = {self.config.index_config.ef_construction})
                    """
                )
            self.conn.commit()

        return f"Index {index_type.value} created"

    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
