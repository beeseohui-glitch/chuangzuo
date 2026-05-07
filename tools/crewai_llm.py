"""
CrewAI LLM 集成 - 将 LLM 降级对 Agent 透明化

用法：
    from tools.crewai_llm import create_llm, create_agent_with_fallback

    # 方式1：直接创建 CrewAI LLM（带降级）
    llm = create_llm()

    # 方式2：创建带降级的 Agent
    agent = create_agent_with_fallback(
        role="标题创作专家",
        goal="生成高质量标题",
        backstory=prompt_content,
        tools=[...],
    )
"""

import os
import logging
from typing import Optional, Any

from crewai import Agent
from crewai.llm import LLM
from crewai.tools import BaseTool

from config import LLMManagerConfig, LLMFallbackLevel, load_llm_config_from_env
from tools.llm_tools import LLMCallTool

logger = logging.getLogger(__name__)


def create_llm(config: Optional[LLMManagerConfig] = None) -> LLM:
    """
    创建 CrewAI 兼容的 LLM（带降级支持）

    CrewAI 使用 LiteLLM 作为底层，格式为 "openai/{model_name}"。
    此函数从 LLMManagerConfig 读取当前 provider 配置，创建对应的 CrewAI LLM。

    当需要切换降级时，调用 switch_llm_provider() 即可，Agent 无需感知。

    Args:
        config: LLM 管理器配置，默认从环境变量加载

    Returns:
        LLM: CrewAI 兼容的 LLM 实例
    """
    if config is None:
        config = load_llm_config_from_env()

    provider_config = config.get_current_provider()

    # CrewAI LiteLLM 格式：openai/{model_name}
    model_name = f"openai/{provider_config.model}"

    return LLM(
        model=model_name,
        api_key=provider_config.api_key or os.getenv("MINIMAX_API_KEY", ""),
        base_url=provider_config.base_url,
        temperature=provider_config.temperature,
        max_tokens=provider_config.max_tokens,
        timeout=provider_config.timeout,
    )


def switch_llm_provider(config: LLMManagerConfig, llm: LLM) -> LLM:
    """
    切换 LLM provider（降级时调用）

    Args:
        config: LLM 管理器配置（已 advance_fallback）
        llm: 当前 CrewAI LLM 实例

    Returns:
        LLM: 更新后的 LLM 实例
    """
    provider_config = config.get_current_provider()
    model_name = f"openai/{provider_config.model}"

    llm.model = model_name
    llm.api_key = provider_config.api_key or ""
    llm.base_url = provider_config.base_url
    llm.temperature = provider_config.temperature
    llm.max_tokens = provider_config.max_tokens

    logger.info(f"Switched LLM to {provider_config.provider} ({provider_config.model})")
    return llm


def create_agent_with_fallback(
    role: str,
    goal: str,
    backstory: str,
    tools: Optional[list[BaseTool]] = None,
    config: Optional[LLMManagerConfig] = None,
    verbose: bool = True,
    **kwargs,
) -> tuple[Agent, LLMCallTool]:
    """
    创建带降级支持的 CrewAI Agent

    返回 (agent, llm_tool) 元组。llm_tool 用于在 Agent 外部调用 LLM（如 Flow 中）。
    Agent 内部直接使用 CrewAI 的 LLM，降级逻辑在 Flow 层面处理。

    Args:
        role: Agent 角色
        goal: Agent 目标
        backstory: Agent 背景（Prompt）
        tools: 工具列表
        config: LLM 配置
        verbose: 是否详细输出
        **kwargs: 传递给 Agent 的其他参数

    Returns:
        (Agent, LLMCallTool) 元组
    """
    llm = create_llm(config)
    llm_tool = LLMCallTool(config)

    agent = Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools or [],
        llm=llm,
        verbose=verbose,
        **kwargs,
    )

    return agent, llm_tool


def create_default_llm_tool(config: Optional[LLMManagerConfig] = None) -> LLMCallTool:
    """
    创建默认的 LLMCallTool（用于在 Agent/Flow 外部直接调用 LLM）

    Args:
        config: LLM 配置

    Returns:
        LLMCallTool 实例
    """
    return LLMCallTool(config)
