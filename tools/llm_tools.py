"""
LLM 服务封装 - 四级降级 + 缓存兜底 + 调用记录

降级级别：
  L1-正常：主LLM（MiniMax-M2.7）可用
  L2-重试：单次失败，指数退避（1s/2s/4s），最多3次
  L3-降级：连续失败>5次或延迟>15s，自动切换备用LLM（mimo → DeepSeek → Qwen）
  L4-缓存兜底：所有LLM不可用时，返回缓存结果 + 标注"建议人工审核"
"""

import os
import re
import time
import json
import hashlib
import logging
from dataclasses import dataclass, field
from typing import Optional, Any
from openai import OpenAI
from crewai.tools import BaseTool
from pydantic import Field

from config import (
    LLMConfig,
    LLMFallbackLevel,
    LLMManagerConfig,
    LLMProvider,
    load_llm_config_from_env,
)

logger = logging.getLogger(__name__)


# ── 调用记录 ──────────────────────────────────────────────


@dataclass
class LLMCallRecord:
    """单次 LLM 调用记录"""
    provider: str
    model: str
    latency_ms: float
    success: bool
    error: Optional[str] = None
    fallback_level: str = "L1_NORMAL"
    timestamp: float = field(default_factory=time.time)


class LLMCallLog:
    """LLM 调用日志管理器"""

    def __init__(self, max_records: int = 1000):
        self._records: list[LLMCallRecord] = []
        self._max_records = max_records
        self._consecutive_failures = 0

    def record(self, record: LLMCallRecord):
        """记录一次调用"""
        self._records.append(record)
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]

        if record.success:
            self._consecutive_failures = 0
        else:
            self._consecutive_failures += 1

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    def reset_failures(self):
        self._consecutive_failures = 0

    def get_records(self, limit: int = 50) -> list[LLMCallRecord]:
        return self._records[-limit:]

    def get_stats(self) -> dict:
        if not self._records:
            return {"total": 0, "success": 0, "failure": 0, "avg_latency_ms": 0}
        success = sum(1 for r in self._records if r.success)
        return {
            "total": len(self._records),
            "success": success,
            "failure": len(self._records) - success,
            "avg_latency_ms": sum(r.latency_ms for r in self._records) / len(self._records),
            "consecutive_failures": self._consecutive_failures,
        }


# ── L4 缓存 ──────────────────────────────────────────────


class LLMResponseCache:
    """LLM 响应缓存（L4 兜底用）"""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: dict[str, tuple[str, float]] = {}
        self._ttl = ttl_seconds

    def _cache_key(self, messages: list[dict], model: str) -> str:
        content = json.dumps({"messages": messages, "model": model}, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, messages: list[dict], model: str) -> Optional[str]:
        key = self._cache_key(messages, model)
        if key in self._cache:
            value, ts = self._cache[key]
            if time.time() - ts < self._ttl:
                return value
            del self._cache[key]
        return None

    def put(self, messages: list[dict], model: str, response: str):
        key = self._cache_key(messages, model)
        self._cache[key] = (response, time.time())

    def clear(self):
        self._cache.clear()


# ── 工具函数 ──────────────────────────────────────────────


def strip_think_tags(content: str) -> str:
    """去除MiniMax思考标签及其内容,只返回正文"""
    pattern = r'<think>.*?</think>'
    cleaned = re.sub(pattern, '', content, flags=re.DOTALL)
    cleaned = cleaned.strip()
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    elif cleaned.startswith('```'):
        cleaned = cleaned[3:]
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    return cleaned.strip()


# ── 主工具类 ──────────────────────────────────────────────


class LLMCallTool(BaseTool):
    """LLM 调用工具（四级降级）"""

    name: str = "llm_call"
    description: str = "调用 LLM 生成内容，支持四级降级"

    def __init__(self, config: Optional[LLMManagerConfig] = None):
        super().__init__()
        self._llm_config = config or load_llm_config_from_env()
        self._clients: dict[str, OpenAI] = {}
        self._call_log = LLMCallLog()
        self._cache = LLMResponseCache(
            ttl_seconds=self._llm_config.fallback_settings.cache_ttl_seconds
        )

    @property
    def call_log(self) -> LLMCallLog:
        return self._call_log

    @property
    def current_level(self) -> LLMFallbackLevel:
        return self._llm_config.current_level

    def _get_client(self, config: LLMConfig) -> OpenAI:
        """获取或创建 OpenAI 客户端（按 provider+base_url 缓存）"""
        key = f"{config.provider}:{config.base_url}"
        if key not in self._clients:
            api_key = config.api_key or "dummy"
            self._clients[key] = OpenAI(
                api_key=api_key,
                base_url=config.base_url,
                timeout=config.timeout,
            )
        return self._clients[key]

    def _run(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """
        BaseTool 接口 - 调用 LLM（四级降级）

        Args:
            prompt: 用户提示
            system: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数
            json_mode: 是否返回 JSON

        Returns:
            str: LLM 输出
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        return self.call(messages, temperature, max_tokens, json_mode)

    def call(
        self,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """
        调用 LLM（四级降级）

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            json_mode: 是否返回 JSON

        Returns:
            str: LLM 输出
        """
        settings = self._llm_config.fallback_settings
        max_retries = settings.max_retries
        delays = settings.retry_delays

        # ── L1 正常 + L2 重试 ──
        for attempt in range(max_retries):
            provider_config = self._llm_config.get_current_provider()
            start_time = time.time()

            try:
                result = self._do_call(
                    provider_config=provider_config,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )
                latency_ms = (time.time() - start_time) * 1000

                # 成功：记录 + 缓存 + 重置
                self._call_log.record(LLMCallRecord(
                    provider=provider_config.provider,
                    model=provider_config.model,
                    latency_ms=latency_ms,
                    success=True,
                    fallback_level=self._llm_config.current_level,
                ))
                self._cache.put(messages, provider_config.model, result)
                self._call_log.reset_failures()

                # 如果之前在降级，成功后恢复
                if self._llm_config.current_level != LLMFallbackLevel.L1_NORMAL:
                    logger.info(f"LLM {provider_config.provider} recovered, resetting to L1")
                    self._llm_config.reset()
                    self._clients.clear()

                return result

            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                self._call_log.record(LLMCallRecord(
                    provider=provider_config.provider,
                    model=provider_config.model,
                    latency_ms=latency_ms,
                    success=False,
                    error=str(e),
                    fallback_level=self._llm_config.current_level,
                ))
                logger.warning(
                    f"LLM call failed (attempt {attempt+1}/{max_retries}): "
                    f"{provider_config.provider} - {e}"
                )

                # L2 重试：指数退避
                delay = delays[min(attempt, len(delays) - 1)]
                if attempt < max_retries - 1:
                    self._llm_config.set_fallback_level(LLMFallbackLevel.L2_RETRY)
                    time.sleep(delay)

        # ── L3 降级 ──
        if self._call_log.consecutive_failures >= settings.fallback_threshold_failures:
            logger.warning(
                f"Consecutive failures ({self._call_log.consecutive_failures}) >= "
                f"threshold ({settings.fallback_threshold_failures}), trying fallback"
            )

            if not self._llm_config.is_all_fallbacks_exhausted:
                self._llm_config.advance_fallback()
                self._clients.clear()  # 切换 provider 需要新 client
                next_provider = self._llm_config.get_current_provider()
                logger.info(f"Switching to fallback: {next_provider.provider} ({next_provider.model})")

                try:
                    start_time = time.time()
                    result = self._do_call(
                        provider_config=next_provider,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        json_mode=json_mode,
                    )
                    latency_ms = (time.time() - start_time) * 1000

                    self._call_log.record(LLMCallRecord(
                        provider=next_provider.provider,
                        model=next_provider.model,
                        latency_ms=latency_ms,
                        success=True,
                        fallback_level=self._llm_config.current_level,
                    ))
                    self._cache.put(messages, next_provider.model, result)
                    self._call_log.reset_failures()
                    return result

                except Exception as e:
                    self._call_log.record(LLMCallRecord(
                        provider=next_provider.provider,
                        model=next_provider.model,
                        latency_ms=(time.time() - start_time) * 1000,
                        success=False,
                        error=str(e),
                        fallback_level=self._llm_config.current_level,
                    ))
                    logger.error(f"Fallback {next_provider.provider} also failed: {e}")

        # ── L4 缓存兜底 ──
        # 尝试所有可用的 fallback
        while not self._llm_config.is_all_fallbacks_exhausted:
            self._llm_config.advance_fallback()
            self._clients.clear()
            fb_config = self._llm_config.get_current_provider()
            try:
                start_time = time.time()
                result = self._do_call(
                    provider_config=fb_config,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )
                latency_ms = (time.time() - start_time) * 1000
                self._call_log.record(LLMCallRecord(
                    provider=fb_config.provider,
                    model=fb_config.model,
                    latency_ms=latency_ms,
                    success=True,
                    fallback_level=self._llm_config.current_level,
                ))
                self._cache.put(messages, fb_config.model, result)
                self._call_log.reset_failures()
                return result
            except Exception as e:
                logger.warning(f"Fallback {fb_config.provider} failed: {e}")

        # 所有 LLM 不可用，使用缓存
        self._llm_config.set_fallback_level(LLMFallbackLevel.L4_CACHE)
        # 用所有已知 model 尝试缓存
        all_models = [self._llm_config.primary.model] + [fb.model for fb in self._llm_config.fallbacks]
        for model in all_models:
            cached = self._cache.get(messages, model)
            if cached:
                logger.warning("All LLMs failed, returning cached result with audit warning")
                return cached + "\n\n[注：此结果来自缓存，建议人工审核]"

        raise RuntimeError(
            "所有 LLM 均不可用且无缓存结果。请检查网络连接和 API Key 配置。"
        )

    def _do_call(
        self,
        provider_config: LLMConfig,
        messages: list[dict],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """执行单次 LLM 调用"""
        client = self._get_client(provider_config)

        kwargs = {
            "model": provider_config.model,
            "messages": messages,
        }

        if temperature is not None:
            kwargs["temperature"] = temperature
        elif provider_config.provider == LLMProvider.MINIMAX:
            # MiniMax-M2.7 temperature=0 produces extremely long thinking
            kwargs["temperature"] = 0.5
        else:
            kwargs["temperature"] = provider_config.temperature

        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = provider_config.max_tokens

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content

        if not content or len(content.strip()) == 0:
            raise RuntimeError("LLM returned empty content")

        content = strip_think_tags(content)
        return content

    def reset(self):
        """重置到正常状态"""
        self._llm_config.reset()
        self._call_log.reset_failures()
        self._clients.clear()

    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            "current_level": self._llm_config.current_level,
            "current_provider": self._llm_config.get_current_provider().provider,
            "current_model": self._llm_config.get_current_provider().model,
            "call_stats": self._call_log.get_stats(),
            "fallback_index": self._llm_config._fallback_index,
            "is_all_exhausted": self._llm_config.is_all_fallbacks_exhausted,
        }


class LLMResponseParser:
    """LLM 响应解析器"""

    @staticmethod
    def parse_json(response: str) -> dict:
        """解析 JSON 响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
            raise ValueError(f"Cannot parse JSON from: {response}")

    @staticmethod
    def parse_list(response: str) -> list:
        """解析列表响应"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            start = response.find("[")
            end = response.rfind("]") + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
            raise ValueError(f"Cannot parse list from: {response}")
