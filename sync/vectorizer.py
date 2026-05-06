"""
向量化和向量存储工具
"""

import os
from typing import Optional
from datetime import datetime

from tools.embedding_tools import LocalEmbeddingTool


class Vectorizer:
    """文本向量化工具"""

    def __init__(self, embedding_tool: Optional[LocalEmbeddingTool] = None):
        """
        初始化向量化工具

        Args:
            embedding_tool: Embedding工具，默认创建LocalEmbeddingTool
        """
        self.embedding_tool = embedding_tool or LocalEmbeddingTool()

    def vectorize_text(self, text: str) -> list[float]:
        """
        将文本向量化

        Args:
            text: 输入文本

        Returns:
            向量列表
        """
        return self.embedding_tool.embed(text)

    def vectorize_batch(self, texts: list[str]) -> list[list[float]]:
        """
        批量向量化

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        return [self.embedding_tool.embed(text) for text in texts]

    def compute_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """
        计算两个向量的余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            相似度分数
        """
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def search_similar(
        self,
        query: str,
        vectors: list[list[float]],
        texts: list[str],
        top_k: int = 5,
    ) -> list[dict]:
        """
        在向量库中搜索相似内容

        Args:
            query: 查询文本
            vectors: 向量列表
            texts: 原始文本列表
            top_k: 返回数量

        Returns:
            相似结果列表
        """
        query_vec = self.vectorize_text(query)
        similarities = []

        for i, vec in enumerate(vectors):
            sim = self.compute_similarity(query_vec, vec)
            similarities.append((i, sim))

        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, sim in similarities[:top_k]:
            results.append({
                "index": idx,
                "text": texts[idx],
                "similarity": sim,
            })

        return results