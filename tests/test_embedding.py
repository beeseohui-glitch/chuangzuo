"""
Embedding 测试 - bge-large-zh-v1.5 本地编码
验证：单条编码维度、批量编码延迟、归一化确认
"""

import time
import pytest
import numpy as np

from models.local_embedding import LocalEmbedding, BGE_DIMENSION


@pytest.fixture(scope="module")
def embedding():
    """模块级 fixture：加载一次模型"""
    return LocalEmbedding()


class TestLocalEmbedding:
    """LocalEmbedding 类测试"""

    def test_single_encode_dimension(self, embedding: LocalEmbedding):
        """单条文本编码，确认输出维度 1024"""
        text = "这是一段测试文本，用于验证embedding输出维度"
        vector = embedding.encode(text)

        assert isinstance(vector, list), "返回类型应为 list"
        assert len(vector) == BGE_DIMENSION, f"维度应为 {BGE_DIMENSION}，实际为 {len(vector)}"
        assert all(isinstance(v, float) for v in vector), "元素类型应为 float"

    def test_single_encode_normalized(self, embedding: LocalEmbedding):
        """确认向量已归一化（L2 范数 ≈ 1.0）"""
        text = "归一化验证测试"
        vector = embedding.encode(text)
        norm = np.linalg.norm(vector)

        assert abs(norm - 1.0) < 1e-5, f"向量应已归一化，实际 L2 范数: {norm}"

    def test_batch_encode(self, embedding: LocalEmbedding):
        """批量编码 10 条，确认延迟 < 3s"""
        texts = [
            "护肝片适合经常熬夜的人群",
            "益生菌可以改善肠道健康",
            "ChatGPT是目前最流行的AI工具",
            "小红书种草笔记怎么写",
            "广告法禁止使用绝对化用语",
            "褪黑素帮助改善睡眠质量",
            "AI绘画工具推荐Midjourney",
            "品牌故事模板怎么用",
            "维生素C增强免疫力",
            "合规审核需要注意哪些问题",
        ]

        start = time.time()
        vectors = embedding.batch_encode(texts)
        elapsed = time.time() - start

        assert len(vectors) == 10, f"应返回 10 条，实际返回 {len(vectors)}"
        for i, v in enumerate(vectors):
            assert len(v) == BGE_DIMENSION, f"第 {i} 条维度应为 {BGE_DIMENSION}"
        assert elapsed < 3.0, f"批量编码 10 条应 < 3s，实际耗时 {elapsed:.2f}s"

    def test_batch_encode_empty(self, embedding: LocalEmbedding):
        """空列表批量编码"""
        vectors = embedding.batch_encode([])
        assert vectors == [], "空列表应返回空列表"

    def test_encode_consistency(self, embedding: LocalEmbedding):
        """相同文本编码结果一致"""
        text = "一致性测试文本"
        v1 = embedding.encode(text)
        v2 = embedding.encode(text)

        assert v1 == v2, "相同文本的编码结果应完全一致"

    def test_different_texts_different_vectors(self, embedding: LocalEmbedding):
        """不同文本应产生不同向量"""
        v1 = embedding.encode("护肝片的功效")
        v2 = embedding.encode("AI绘画工具推荐")

        cosine_sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        assert cosine_sim < 0.95, f"不同语义文本的相似度应较低，实际: {cosine_sim}"

    def test_dimension_constant(self, embedding: LocalEmbedding):
        """确认维度常量与模型一致"""
        assert embedding.dimension == BGE_DIMENSION
        assert BGE_DIMENSION == 1024
