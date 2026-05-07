import os
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class IndexType(str, Enum):
    """向量索引类型"""
    IVFFLAT = "ivfflat"  # MVP阶段，数据量<10万
    HNSW = "hnsw"       # 生产阶段，数据量>10万


class VectorIndexConfig(BaseModel):
    """向量索引配置"""
    index_type: IndexType = Field(default=IndexType.IVFFLAT, description="索引类型")
    dimension: int = Field(default=1024, description="向量维度 bge-large-zh-v1.5")
    metric: str = Field(default="cosine", description="距离度量方式")
    # IVFFlat 参数
    lists: int = Field(default=100, description="IVFFlat lists 参数")
    probes: int = Field(default=10, description="IVFFlat probes 参数")
    # HNSW 参数
    m: int = Field(default=16, description="HNSW m 参数")
    ef_construction: int = Field(default=64, description="HNSW ef_construction 参数")


class VectorSearchConfig(BaseModel):
    """向量检索配置"""
    default_limit: int = Field(default=10, description="默认返回数量")
    max_limit: int = Field(default=100, description="最大返回数量")
    min_similarity_score: float = Field(default=0.5, description="最小相似度阈值")
    enable_cache: bool = Field(default=True, description="是否启用缓存")
    cache_ttl_seconds: int = Field(default=1800, description="缓存 TTL")


class VectorStoreConfig(BaseModel):
    """向量存储配置"""
    host: str = Field(default="localhost", description="数据库主机")
    port: int = Field(default=5432, description="数据库端口")
    database: str = Field(default="content_agent", description="数据库名")
    user: str = Field(default="agent", description="用户名")
    password: str = Field(default="your_password_here", description="密码")
    index_config: VectorIndexConfig = Field(default_factory=VectorIndexConfig)
    search_config: VectorSearchConfig = Field(default_factory=VectorSearchConfig)

    # 知识库表配置
    knowledge_table: str = Field(default="knowledge_base", description="知识库表名")
    embedding_column: str = Field(default="embedding", description="向量列名")

    # RLS 配置
    enable_rls: bool = Field(default=True, description="是否启用行级安全策略")
    enterprise_id_column: str = Field(default="enterprise_id", description="企业ID列名")

    @classmethod
    def from_env(cls) -> "VectorStoreConfig":
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "content_agent"),
            user=os.getenv("DB_USER", "agent"),
            password=os.getenv("DB_PASSWORD", "your_password_here"),
        )


class EmbeddingConfig(BaseModel):
    """Embedding 模型配置"""
    model_name: str = Field(default="BAAI/bge-large-zh-v1.5", description="模型名称")
    device: str = Field(default="cpu", description="运行设备 cpu/cuda")
    cache_folder: Optional[str] = Field(default=None, description="模型缓存目录")
    normalize_embeddings: bool = Field(default=True, description="是否归一化向量")
    encode_kwargs: dict = Field(default_factory=lambda: {"batch_size": 32}, description="编码参数")
    infer_batch_size: int = Field(default=32, description="推理批量大小")


# 默认配置实例
DEFAULT_VECTOR_CONFIG = VectorStoreConfig()
DEFAULT_EMBEDDING_CONFIG = EmbeddingConfig()
