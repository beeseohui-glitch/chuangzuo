import os
from pydantic import BaseModel, Field, PrivateAttr
from typing import Optional
from enum import Enum


class LLMProvider(str, Enum):
    """LLM 提供商"""
    MINIMAX = "minimax"
    MIMO = "mimo"
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


class MimoConfig(LLMConfig):
    """Mimo 备用配置（备LLM1）"""
    provider: LLMProvider = Field(default=LLMProvider.MIMO)
    model: str = Field(default="mimo-v2.5-pro")
    base_url: str = Field(default="https://api.mimo.ai/v1")


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
    fallbacks: list[LLMConfig] = Field(default_factory=lambda: [MimoConfig(), DeepSeekConfig(), QwenConfig()])
    fallback_settings: LLMFallbackConfig = Field(default_factory=LLMFallbackConfig)
    current_level: LLMFallbackLevel = Field(default=LLMFallbackLevel.L1_NORMAL)
    _fallback_index: int = PrivateAttr(default=-1)  # 当前降级到第几个fallback，-1表示未降级

    def get_current_provider(self) -> LLMConfig:
        """获取当前使用的 LLM 配置"""
        if self.current_level in (LLMFallbackLevel.L1_NORMAL, LLMFallbackLevel.L2_RETRY):
            return self.primary
        elif self.current_level == LLMFallbackLevel.L3_FALLBACK:
            if 0 <= self._fallback_index < len(self.fallbacks):
                return self.fallbacks[self._fallback_index]
            return self.fallbacks[0] if self.fallbacks else self.primary
        return self.primary

    def get_next_fallback(self) -> Optional[LLMConfig]:
        """获取下一个降级配置"""
        next_index = self._fallback_index + 1
        if next_index < len(self.fallbacks):
            return self.fallbacks[next_index]
        return None

    def advance_fallback(self):
        """切换到下一个降级（从 primary → fallback[0] → fallback[1] → ...）"""
        if self._fallback_index < len(self.fallbacks) - 1:
            self._fallback_index += 1
        self.current_level = LLMFallbackLevel.L3_FALLBACK

    def set_fallback_level(self, level: LLMFallbackLevel):
        """直接设置降级级别"""
        self.current_level = level

    def reset(self):
        """重置到正常状态"""
        self._fallback_index = -1
        self.current_level = LLMFallbackLevel.L1_NORMAL

    @property
    def is_all_fallbacks_exhausted(self) -> bool:
        """是否所有降级都已用尽"""
        return self._fallback_index >= len(self.fallbacks) - 1


def load_llm_config_from_env() -> LLMManagerConfig:
    """从环境变量加载 LLM 配置"""
    # 主LLM: MiniMax
    primary = MiniMaxConfig(
        api_key=os.getenv("MINIMAX_API_KEY", ""),
        base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1"),
        model=os.getenv("MINIMAX_MODEL", "MiniMax-M2.7"),
    )

    # 备LLM1: Mimo
    mimo_key = os.getenv("MIMO_API_KEY", "")
    mimo = MimoConfig(
        api_key=mimo_key,
        base_url=os.getenv("MIMO_BASE_URL", "https://api.mimo.ai/v1"),
        model=os.getenv("MIMO_MODEL", "mimo-v2.5-pro"),
    )

    # 备LLM2: DeepSeek
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek = DeepSeekConfig(
        api_key=deepseek_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    )

    # 备LLM3: Qwen
    qwen_key = os.getenv("QWEN_API_KEY", "")
    qwen = QwenConfig(
        api_key=qwen_key,
        base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        model=os.getenv("QWEN_MODEL", "qwen-turbo"),
    )

    fallbacks = [fb for fb in [mimo, deepseek, qwen] if fb.api_key]

    return LLMManagerConfig(
        primary=primary,
        fallbacks=fallbacks if fallbacks else [mimo],
        fallback_settings=LLMFallbackConfig(
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            fallback_threshold_failures=int(os.getenv("LLM_FALLBACK_THRESHOLD", "5")),
            fallback_threshold_latency=int(os.getenv("LLM_LATENCY_THRESHOLD", "15")),
            cache_ttl_seconds=int(os.getenv("LLM_CACHE_TTL", "3600")),
        ),
    )
