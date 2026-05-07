"""
Embedding 工具 - 本地 bge-large-zh-v1.5 模型封装
"""

from typing import Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from crewai.tools import BaseTool
from pydantic import Field, PrivateAttr

from config import EmbeddingConfig


class LocalEmbeddingTool(BaseTool):
    """本地 Embedding 工具 - 使用 bge-large-zh-v1.5"""

    name: str = "local_embedding"
    description: str = "将文本转换为1024维向量向量，用于语义检索"
    config: EmbeddingConfig = Field(default_factory=EmbeddingConfig)

    _model: Optional[SentenceTransformer] = PrivateAttr(default=None)

    @property
    def model(self) -> SentenceTransformer:
        """懒加载模型"""
        if self._model is None:
            self._model = SentenceTransformer(
                self.config.model_name,
                device=self.config.device,
                cache_folder=self.config.cache_folder,
            )
        return self._model

    def encode(self, texts: str | list[str], **kwargs) -> np.ndarray:
        """
        将文本转换为向量

        Args:
            texts: 单个文本或文本列表
            **kwargs: 额外参数

        Returns:
            numpy.ndarray: 归一化后的向量
        """
        if isinstance(texts, str):
            texts = [texts]

        encode_kwargs = {**self.config.encode_kwargs, **kwargs}
        embeddings = self.model.encode(
            texts,
            normalize_embeddings=self.config.normalize_embeddings,
            **encode_kwargs,
        )
        return embeddings

    def _run(self, text: str) -> list[float]:
        """BaseTool 接口 - 单文本嵌入"""
        embedding = self.encode(text)
        return embedding[0].tolist()

    def batch_encode(self, texts: list[str], batch_size: Optional[int] = None) -> np.ndarray:
        """
        批量嵌入

        Args:
            texts: 文本列表
            batch_size: 批量大小，默认使用配置中的值

        Returns:
            numpy.ndarray: 归一化后的向量矩阵
        """
        if batch_size is None:
            batch_size = self.config.infer_batch_size

        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            embeddings = self.encode(batch)
            all_embeddings.append(embeddings)

        return np.vstack(all_embeddings)

    def similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            float: 余弦相似度
        """
        embeddings = self.encode([text1, text2])
        cos_sim = np.dot(embeddings[0], embeddings[1])
        return float(cos_sim)

    def destroy(self):
        """释放模型内存"""
        if self._model is not None:
            del self._model
            self._model = None
            if self.config.device == "cuda":
                import torch
                torch.cuda.empty_cache()


class EmbeddingCache:
    """Embedding 结果缓存"""

    def __init__(self, ttl_seconds: int = 1800):
        self._cache: dict[str, tuple[list[float], float]] = {}
        self._ttl = ttl_seconds

    def get(self, text: str) -> Optional[list[float]]:
        """获取缓存的 embedding"""
        import time

        if text not in self._cache:
            return None

        embedding, timestamp = self._cache[text]
        if time.time() - timestamp > self._ttl:
            del self._cache[text]
            return None

        return embedding

    def set(self, text: str, embedding: list[float]):
        """设置缓存"""
        import time

        self._cache[text] = (embedding, time.time())

    def clear(self):
        """清空缓存"""
        self._cache.clear()
