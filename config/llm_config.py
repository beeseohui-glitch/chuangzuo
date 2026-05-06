from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    """LLM 提供商"""
    MINIMAX = "minimax"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"


class LLMFallbackLevel(str, Enum):
    """LLM 降级级别"""
    L1_NORMAL = "l1_normal"  # 正常
    L2_RETRY = "l2_retry"   # 重试
    L3_FALLBACK = "l3_fallback"  # 降级
    L4_CACHE = "l4_cache"    # 缓存兜底


class LLMConfig(BaseModel):
    """LLM 配置"""
    provider: LLMProvider = Field(default=LLMProvider.MINIMAX, description="LLM 提供商")
    model: str = Field(default="MiniMax-M2.7", description="模型名称")
    api_key: Optional[str] = Field(default=None, description="API Key")
    base_url: str = Field(default="https://api.minimax.chat/v1", description="API 地址")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="温度参数")
    max_tokens: int = Field(default=2048, description="最大 token 数")
    timeout: int = Field(default=30, description="超时秒数")


class LLMFallbackConfig(BaseModel):
    """LLM 降级配置"""
    enabled: bool = Field(default=True, description="是否启用降级")
    max_retries: int = Field(default=3, description="最大重试次数")
    retry_delays: list[int] = Field(default=[1, 2, 4], description="重试延迟秒数")
    fallback_threshold_failures: int = Field(default=5, description="连续失败触发降级的次数")
    fallback_threshold_latency: int = Field(default=15, description="延迟超过 N 秒触发降级")
    cache_ttl_seconds: int = Field(default=3600, description="缓存 TTL 秒数")


class MiniMaxConfig(LLMConfig):
    """MiniMax 专用配置"""
    provider: LLMProvider = Field(default=LLMProvider.MINIMAX)
    model: str = Field(default="MiniMax-M2.7")
    base_url: str = Field(default="https://api.minimax.chat/v1")
    timeout: int = Field(default=120, description="超时秒数")


class DeepSeekConfig(LLMConfig):
    """DeepSeek 备用配置"""
    provider: LLMProvider = Field(default=LLMProvider.DEEPSEEK)
    model: str = Field(default="deepseek-chat")
    base_url: str = Field(default="https://api.deepseek.com/v1")


class QwenConfig(LLMConfig):
    """Qwen 备用配置"""
    provider: LLMProvider = Field(default=LLMProvider.QWEN)
    model: str = Field(default="qwen-turbo")
    base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")


class LLMManagerConfig(BaseModel):
    """LLM 管理器配置"""
    primary: LLMConfig = Field(default_factory=MiniMaxConfig)
    fallbacks: list[LLMConfig] = Field(default_factory=lambda: [DeepSeekConfig(), QwenConfig()])
    fallback_settings: LLMFallbackConfig = Field(default_factory=LLMFallbackConfig)
    current_level: LLMFallbackLevel = Field(default=LLMFallbackLevel.L1_NORMAL)

    def get_current_provider(self) -> LLMConfig:
        """获取当前使用的 LLM 配置"""
        if self.current_level == LLMFallbackLevel.L1_NORMAL:
            return self.primary
        elif self.current_level == LLMFallbackLevel.L3_FALLBACK:
            return self.fallbacks[0] if self.fallbacks else self.primary
        return self.primary
