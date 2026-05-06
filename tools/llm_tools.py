"""
LLM 工具 - LLM 调用及降级逻辑
"""

import os
import re
import time
import json
from typing import Optional, Any
from openai import OpenAI
from crewai.tools import BaseTool
from pydantic import Field

from config import (
    LLMConfig,
    LLMFallbackLevel,
    LLMManagerConfig,
    LLMProvider,
)


def strip_think_tags(content: str) -> str:
    """去除MiniMax思考标签及其内容,只返回正文"""
    # 匹配 <think>...</think> 模式(包括换行)
    # re.DOTALL 让 . 匹配换行符
    pattern = r'<think>.*?</think>'
    cleaned = re.sub(pattern, '', content, flags=re.DOTALL)
    # 清理可能残留的多余空白
    cleaned = cleaned.strip()
    # 去除 markdown 代码块标记
    if cleaned.startswith('```json'):
        cleaned = cleaned[7:]
    elif cleaned.startswith('```'):
        cleaned = cleaned[3:]
    if cleaned.endswith('```'):
        cleaned = cleaned[:-3]
    return cleaned.strip()




class LLMCallTool(BaseTool):
    """LLM 调用工具"""

    name: str = "llm_call"
    description: str = "调用 LLM 生成内容"

    def __init__(self, config: Optional[LLMManagerConfig] = None):
        super().__init__()
        self._llm_config = config or self._load_default_config()
        self._clients: dict[LLMProvider, OpenAI] = {}
        self._failure_count = 0
        self._current_provider = self._llm_config.primary.provider

    def _load_default_config(self) -> LLMManagerConfig:
        """从环境变量加载默认配置"""
        api_key = os.getenv("MINIMAX_API_KEY", "")
        return LLMManagerConfig(
            primary=LLMConfig(
                provider=LLMProvider.MINIMAX,
                api_key=api_key,
                base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1"),
                timeout=120,
            )
        )

    @property
    def current_client(self) -> OpenAI:
        """获取当前 LLM 客户端"""
        provider = self._get_current_provider()

        if provider not in self._clients:
            config = self._get_provider_config(provider)
            self._clients[provider] = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=config.timeout,
            )

        return self._clients[provider]

    def _get_current_provider(self) -> LLMProvider:
        """获取当前 provider"""
        if self._llm_config.current_level == LLMFallbackLevel.L3_FALLBACK:
            if self._llm_config.fallbacks:
                return self._llm_config.fallbacks[0].provider
        return self._llm_config.primary.provider

    def _get_provider_config(self, provider: LLMProvider) -> LLMConfig:
        """获取指定 provider 的配置"""
        if provider == self._llm_config.primary.provider:
            return self._llm_config.primary

        for fallback in self._llm_config.fallbacks:
            if fallback.provider == provider:
                return fallback

        return self._llm_config.primary

    def _run(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """
        BaseTool 接口 - 调用 LLM

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

        model = self._get_provider_config(self._get_current_provider()).model

        return self._call_with_retry(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )

    def _call_with_retry(
        self,
        messages: list[dict],
        model: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """带重试的 LLM 调用"""
        fallback_settings = self._llm_config.fallback_settings
        max_retries = fallback_settings.max_retries

        for attempt in range(max_retries):
            try:
                result = self._do_call(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    json_mode=json_mode,
                )

                # 如果结果为空，增加失败计数并重试
                if not result or len(result.strip()) == 0:
                    self._failure_count += 1
                    delay = fallback_settings.retry_delays[
                        min(attempt, len(fallback_settings.retry_delays) - 1)
                    ]
                    if self._should_fallback():
                        self._do_fallback()
                    if attempt == max_retries - 1:
                        raise RuntimeError(f"LLM call returned empty result after {max_retries} attempts")
                    time.sleep(delay)
                    continue

                self._failure_count = 0
                return result

            except Exception as e:
                self._failure_count += 1
                delay = fallback_settings.retry_delays[
                    min(attempt, len(fallback_settings.retry_delays) - 1)
                ]

                if self._should_fallback():
                    self._do_fallback()

                if attempt == max_retries - 1:
                    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {e}")

                time.sleep(delay)

        raise RuntimeError("Unexpected error in LLM retry loop")

    def _do_call(
        self,
        messages: list[dict],
        model: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
    ) -> str:
        """执行 LLM 调用"""
        config = self._get_provider_config(self._get_current_provider())

        kwargs = {
            "model": model,
            "messages": messages,
        }

        # MiniMax-M2.7 with temperature=0 produces extremely long thinking that
        # consumes all tokens, leaving no actual content. Use 0.5 to balance
        # thinking length and output quality.
        if temperature is not None:
            kwargs["temperature"] = temperature
        elif self._get_current_provider() == LLMProvider.MINIMAX:
            kwargs["temperature"] = 0.5
        else:
            kwargs["temperature"] = config.temperature

        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = config.max_tokens

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = self.current_client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content

        # MiniMax-M2.7 returns content wrapped in <think>...</think> tags
        # Strip think tags and return only the actual response content
        content = strip_think_tags(content)

        return content

    def _should_fallback(self) -> bool:
        """判断是否应该降级"""
        fallback_settings = self._llm_config.fallback_settings

        if self._failure_count >= fallback_settings.fallback_threshold_failures:
            return True

        return False

    def _do_fallback(self):
        """执行降级"""
        self._llm_config.current_level = LLMFallbackLevel.L3_FALLBACK
        self._failure_count = 0

        if self._clients:
            self._clients.clear()

    def reset_level(self):
        """重置到正常级别"""
        self._llm_config.current_level = LLMFallbackLevel.L1_NORMAL
        self._failure_count = 0

    def set_level(self, level: LLMFallbackLevel):
        """设置降级级别"""
        self._llm_config.current_level = level
        if level == LLMFallbackLevel.L1_NORMAL:
            self._failure_count = 0


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
