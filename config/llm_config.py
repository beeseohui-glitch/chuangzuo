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
    """MiMo Pro 配置"""
    provider: LLMProvider = Field(default=LLMProvider.MIMO)
    model: str = Field(default="mimo-v2.5-pro")
    base_url: str = Field(default="https://token-plan-cn.xiaomimimo.com/v1")


class MimoSimpleConfig(LLMConfig):
    """MiMo Simple 配置"""
    provider: LLMProvider = Field(default=LLMProvider.MIMO)
    model: str = Field(default="mimo-v2.5")
    base_url: str = Field(default="https://token-plan-cn.xiaomimimo.com/v1")


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
    primary: LLMConfig = Field(default_factory=MimoConfig)
    fallbacks: list[LLMConfig] = Field(default_factory=lambda: [DeepSeekConfig(), QwenConfig()])
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
    # 主LLM: MiMo
    primary = MimoConfig(
        api_key=os.getenv("MIMO_API_KEY", ""),
        base_url=os.getenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1"),
        model=os.getenv("MIMO_MODEL", "mimo-v2.5-pro"),
    )

    # 备LLM: DeepSeek
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek = DeepSeekConfig(
        api_key=deepseek_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    )

    # 备LLM: Qwen
    qwen_key = os.getenv("QWEN_API_KEY", "")
    qwen = QwenConfig(
        api_key=qwen_key,
        base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        model=os.getenv("QWEN_MODEL", "qwen-turbo"),
    )

    fallbacks = [fb for fb in [deepseek, qwen] if fb.api_key]

    return LLMManagerConfig(
        primary=primary,
        fallbacks=fallbacks if fallbacks else [primary],
        fallback_settings=LLMFallbackConfig(
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            fallback_threshold_failures=int(os.getenv("LLM_FALLBACK_THRESHOLD", "5")),
            fallback_threshold_latency=int(os.getenv("LLM_LATENCY_THRESHOLD", "15")),
            cache_ttl_seconds=int(os.getenv("LLM_CACHE_TTL", "3600")),
        ),
    )


# ── Agent 级别模型映射 ──────────────────────────────────────

# 每个 Agent 使用的模型（pro = mimo-v2.5-pro, simple = mimo-v2.5）
AGENT_MODEL_MAP: dict[str, str] = {
    "orchestrator": "mimo-v2.5-pro",   # 意图识别需要推理
    "title": "mimo-v2.5",              # 创意生成
    "article": "mimo-v2.5-pro",        # 长文本+去AI味
    "compliance": "mimo-v2.5-pro",     # 灰色地带判断
    "analytics": "mimo-v2.5-pro",      # 需要推理
    "tag": "mimo-v2.5",                # 简单分类提取
    "topic": "mimo-v2.5",              # 选题生成
    "kb": "mimo-v2.5",                 # 知识问答
    "operation": "mimo-v2.5",          # 运营建议
    "wechat": "mimo-v2.5-pro",         # 长文本创作
    "douyin": "mimo-v2.5-pro",         # 脚本创作
}


def get_llm_for_agent(agent_name: str) -> LLMManagerConfig:
    """
    根据 Agent 名称获取对应的 LLM 配置

    降级链：Pro → Simple（同 base_url，只是 model 不同）

    Args:
        agent_name: Agent 名称（如 "title", "article" 等）

    Returns:
        LLMManagerConfig: 该 Agent 专属的 LLM 配置
    """
    model = AGENT_MODEL_MAP.get(agent_name, "mimo-v2.5")
    api_key = os.getenv("MIMO_API_KEY", "")
    base_url = os.getenv("MIMO_BASE_URL", "https://token-plan-cn.xiaomimimo.com/v1")

    primary = MimoConfig(api_key=api_key, base_url=base_url, model=model)

    # Fallback：Pro 降级到 Simple，Simple 无更小模型可降
    fallback_model = "mimo-v2.5" if model == "mimo-v2.5-pro" else None
    fallbacks = []
    if fallback_model:
        fallbacks.append(MimoConfig(api_key=api_key, base_url=base_url, model=fallback_model))

    # 额外 fallback：DeepSeek / Qwen（如果有 key）
    deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
    if deepseek_key:
        fallbacks.append(DeepSeekConfig(
            api_key=deepseek_key,
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        ))
    qwen_key = os.getenv("QWEN_API_KEY", "")
    if qwen_key:
        fallbacks.append(QwenConfig(
            api_key=qwen_key,
            base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            model=os.getenv("QWEN_MODEL", "qwen-turbo"),
        ))

    return LLMManagerConfig(
        primary=primary,
        fallbacks=fallbacks,
        fallback_settings=LLMFallbackConfig(
            max_retries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            fallback_threshold_failures=int(os.getenv("LLM_FALLBACK_THRESHOLD", "5")),
            fallback_threshold_latency=int(os.getenv("LLM_LATENCY_THRESHOLD", "15")),
            cache_ttl_seconds=int(os.getenv("LLM_CACHE_TTL", "3600")),
        ),
    )
