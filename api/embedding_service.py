"""
异步 Embedding 服务

在 FastAPI 路由中调用，使用 asyncio.to_thread 在后台线程运行本地 embedding 模型。
入库时立即返回，向量化异步执行，失败不阻塞主流程。
"""

import asyncio
import logging
from typing import Optional

from tools.embedding_tools import LocalEmbeddingTool

logger = logging.getLogger(__name__)

# 单例 embedding 工具（懒加载模型，进程内共享）
_embedding_tool: Optional[LocalEmbeddingTool] = None


def _get_embedding_tool() -> LocalEmbeddingTool:
    global _embedding_tool
    if _embedding_tool is None:
        _embedding_tool = LocalEmbeddingTool()
    return _embedding_tool


async def generate_embedding(text: str) -> list[float]:
    """
    异步生成单条 embedding

    Args:
        text: 待向量化的文本

    Returns:
        list[float]: 1024 维归一化向量
    """
    tool = _get_embedding_tool()
    embedding = await asyncio.to_thread(tool.encode, text)
    return embedding[0].tolist()


async def update_embedding_for_record(
    record_id: int,
    title: str,
    content: str,
    db_pool=None,
):
    """
    后台任务：生成 embedding 并写入数据库

    Args:
        record_id: knowledge_base 记录 ID
        title: 标题
        content: 内容
        db_pool: asyncpg 连接池（为 None 时自行获取）
    """
    from api.db import get_pool

    text = f"{title or ''} {content or ''}".strip()
    if not text:
        logger.warning(f"Record {record_id}: empty text, skipping embedding")
        return

    try:
        embedding = await generate_embedding(text)

        pool = db_pool or await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                "UPDATE knowledge_base SET embedding = $1::vector, sync_status = 'synced' WHERE id = $2",
                str(embedding), record_id,
            )
        logger.info(f"Record {record_id}: embedding synced")

    except Exception as e:
        logger.error(f"Record {record_id}: embedding failed — {e}")
        try:
            pool = db_pool or await get_pool()
            async with pool.acquire() as conn:
                await conn.execute(
                    "UPDATE knowledge_base SET sync_status = 'failed' WHERE id = $1",
                    record_id,
                )
        except Exception:
            logger.error(f"Record {record_id}: failed to update sync_status")


def schedule_embedding_update(
    record_id: int,
    title: str,
    content: str,
):
    """
    调度后台 embedding 任务（非阻塞）

    在 FastAPI 路由中调用此函数，向量化会在后台执行。
    """
    asyncio.create_task(update_embedding_for_record(record_id, title, content))
