"""
统一调度 Agent - 意图识别 + 平台路由

职责：
  1. 意图识别：判断用户要发到哪个平台、品牌产品、场景
  2. 平台路由：路由到对应平台工作流
  3. 租户身份校验：enterprise_id 有效性、套餐、额度
  4. 限流：Redis 计数器（每用户每分钟 10 次）
  5. Prompt 注入检测
  6. 追问：未指定平台时追问，最多 3 轮
"""

import os
import re
import json
import time
import logging
from typing import Optional
from pathlib import Path

from crewai import Agent
from crewai.llm import LLM
from pydantic import BaseModel, Field

from config import ORCHESTRATOR_AGENT, LLMManagerConfig
from config.llm_config import get_llm_for_agent
from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm
from tools.llm_tools import LLMCallTool, LLMResponseParser

logger = logging.getLogger(__name__)

# 平台路由映射
PLATFORM_ROUTE_MAP = {
    "xiaohongshu": "xiaohongshu_flow",
    "xhs": "xiaohongshu_flow",
    "小红书": "xiaohongshu_flow",
    "wechat_public": "wechat_public_flow",
    "公众号": "wechat_public_flow",
    "微信公众号": "wechat_public_flow",
    "douyin": "douyin_flow",
    "抖音": "douyin_flow",
}

# Prompt 注入关键词
INJECTION_PATTERNS = [
    r"忽略.{0,10}(之前|上面|上面的|之前的)",
    r"ignore.{0,10}(previous|above|instructions)",
    r"system\s*prompt",
    r"你的(指令|prompt|system)",
    r"reveal.{0,10}(prompt|instructions)",
    r"扮演.{0,5}(其他|另一个)",
    r"pretend.{0,5}(you are|you're)",
    r"jailbreak",
    r"dan\s*mode",
]


class OrchestratorOutput(BaseModel):
    """调度 Agent 输出"""
    platform: Optional[str] = Field(default=None, description="目标平台")
    product: Optional[str] = Field(default=None, description="品牌和产品")
    scene: Optional[str] = Field(default=None, description="场景/需求")
    style: Optional[str] = Field(default=None, description="风格要求")
    route_to: Optional[str] = Field(default=None, description="路由目标工作流名称")
    confidence: float = Field(default=0.0, description="置信度 0-1")
    needs_clarification: bool = Field(default=False, description="是否需要追问")
    clarification_question: Optional[str] = Field(default=None, description="追问问题")


class OrchestratorAgent:
    """统一调度 Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMManagerConfig] = None,
        enterprise_id: Optional[str] = None,
        allowed_platforms: Optional[list[str]] = None,
        plan: Optional[str] = None,
    ):
        self.config = ORCHESTRATOR_AGENT
        self._llm_config = llm_config or get_llm_for_agent("orchestrator")
        self._llm_tool: Optional[LLMCallTool] = None
        self._enterprise_id = enterprise_id
        self._allowed_platforms = allowed_platforms or [
            "xiaohongshu", "wechat_public", "douyin"
        ]
        self._plan = plan or "professional"
        self._clarification_rounds = 0
        self._max_clarification_rounds = 3
        self._conversation_history: list[dict] = []

        # 限流（内存实现，可替换为 Redis）
        self._rate_limit_cache: dict[str, list[float]] = {}
        self._rate_limit_max = 10  # 每分钟最大次数

    @property
    def llm_tool(self) -> LLMCallTool:
        if self._llm_tool is None:
            self._llm_tool = LLMCallTool(self._llm_config)
        return self._llm_tool

    def route(self, user_input: str) -> OrchestratorOutput:
        """
        路由用户请求

        Args:
            user_input: 用户输入

        Returns:
            OrchestratorOutput: 路由结果
        """
        # 1. Prompt 注入检测
        if self._detect_injection(user_input):
            logger.warning(f"Prompt injection detected: {user_input[:50]}")
            return OrchestratorOutput(
                confidence=0.0,
                needs_clarification=True,
                clarification_question="抱歉，我无法处理这个请求。请用正常的语言描述您的创作需求。",
            )

        # 2. 限流检查
        if self._enterprise_id and not self._check_rate_limit(self._enterprise_id):
            logger.warning(f"Rate limit exceeded for: {self._enterprise_id}")
            return OrchestratorOutput(
                confidence=0.0,
                needs_clarification=True,
                clarification_question="请求过于频繁，请稍后再试。",
            )

        # 3. 意图识别
        result = self._recognize_intent(user_input)

        # 4. 平台路由校验
        if result.route_to and not result.needs_clarification:
            # 检查平台是否在允许列表中
            platform = result.platform
            if platform and platform not in self._allowed_platforms:
                return OrchestratorOutput(
                    platform=platform,
                    product=result.product,
                    scene=result.scene,
                    style=result.style,
                    route_to=None,
                    confidence=0.5,
                    needs_clarification=True,
                    clarification_question=f"您的套餐不支持{platform}平台。当前支持的平台：{', '.join(self._allowed_platforms)}",
                )

        # 5. 追问逻辑
        if result.needs_clarification:
            self._clarification_rounds += 1
            if self._clarification_rounds > self._max_clarification_rounds:
                return OrchestratorOutput(
                    confidence=0.0,
                    needs_clarification=False,
                    clarification_question=None,
                    route_to=None,
                )

        return result

    def _recognize_intent(self, user_input: str) -> OrchestratorOutput:
        """
        意图识别 - 调用 LLM

        Args:
            user_input: 用户输入

        Returns:
            OrchestratorOutput: 识别结果
        """
        # 加载 Prompt
        system_prompt = prompt_manager.load_prompt("orchestrator")

        # 构建用户消息
        user_message = f"用户输入：{user_input}"

        # 添加对话历史
        if self._conversation_history:
            history_text = "\n".join([
                f"用户：{h['user']}\n系统：{h['system']}"
                for h in self._conversation_history[-3:]
            ])
            user_message = f"对话历史：\n{history_text}\n\n{user_message}"

        # 调用 LLM
        response = self.llm_tool.call(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=500,
            json_mode=True,
        )

        # 解析响应
        try:
            data = LLMResponseParser.parse_json(response)

            # 标准化 platform
            platform = data.get("platform", "")
            route_to = data.get("route_to")
            if not route_to and platform:
                route_to = PLATFORM_ROUTE_MAP.get(platform.lower())

            return OrchestratorOutput(
                platform=platform,
                product=data.get("product"),
                scene=data.get("scene"),
                style=data.get("style"),
                route_to=route_to,
                confidence=data.get("confidence", 0.8),
                needs_clarification=data.get("needs_clarification", False),
                clarification_question=data.get("clarification_question"),
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse orchestrator response: {e}")
            return OrchestratorOutput(
                confidence=0.0,
                needs_clarification=True,
                clarification_question="我没有完全理解您的需求。请问您想在哪个平台发布内容？（小红书/公众号/抖音）",
            )

    def _detect_injection(self, text: str) -> bool:
        """
        检测 Prompt 注入

        Args:
            text: 用户输入

        Returns:
            bool: 是否检测到注入
        """
        text_lower = text.lower()
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    def _check_rate_limit(self, user_id: str) -> bool:
        """
        限流检查（内存实现）

        Args:
            user_id: 用户ID

        Returns:
            bool: 是否允许通过
        """
        now = time.time()
        window = 60  # 1 分钟窗口

        if user_id not in self._rate_limit_cache:
            self._rate_limit_cache[user_id] = []

        # 清理过期记录
        self._rate_limit_cache[user_id] = [
            ts for ts in self._rate_limit_cache[user_id]
            if now - ts < window
        ]

        # 检查是否超限
        if len(self._rate_limit_cache[user_id]) >= self._rate_limit_max:
            return False

        # 记录本次请求
        self._rate_limit_cache[user_id].append(now)
        return True

    def validate_tenant(
        self,
        enterprise_id: str,
        target_platform: str,
    ) -> tuple[bool, Optional[str]]:
        """
        租户身份校验

        Args:
            enterprise_id: 企业ID
            target_platform: 目标平台

        Returns:
            (是否通过, 错误信息)
        """
        if not enterprise_id:
            return False, "缺少企业身份信息"

        # 校验平台是否在套餐范围内
        if target_platform and target_platform not in self._allowed_platforms:
            return False, f"您的套餐不支持{target_platform}平台"

        return True, None

    def reset(self):
        """重置状态"""
        self._clarification_rounds = 0
        self._conversation_history.clear()

    def get_status(self) -> dict:
        """获取状态"""
        return {
            "enterprise_id": self._enterprise_id,
            "plan": self._plan,
            "allowed_platforms": self._allowed_platforms,
            "clarification_rounds": self._clarification_rounds,
            "llm_status": self.llm_tool.get_status() if self._llm_tool else None,
        }


def _orchestrator_run_standalone(self, user_input: str) -> OrchestratorOutput:
    return self.route(user_input=user_input)


OrchestratorAgent.run_standalone = _orchestrator_run_standalone


# ── AgentTool：将任意 Agent 包装为 Orchestrator 可调用的 Tool ──

from crewai.tools import BaseTool as CrewAIBaseTool


class AgentTool(CrewAIBaseTool):
    """将 Agent 包装为 Tool，供 Orchestrator 调用"""
    name: str = "call_agent"
    description: str = (
        "调用指定 Agent 执行任务。"
        "输入参数: agent_name (Agent名称), method (方法名), params (参数dict)。"
        "可用 agent: title, article, tag, compliance, material, topic, kb, analytics, operation, wechat, douyin"
    )

    def _run(self, agent_name: str, method: str, params: dict = {}) -> str:
        """
        调用指定 Agent

        Args:
            agent_name: Agent 名称
            method: 方法名
            params: 参数字典

        Returns:
            JSON 格式的执行结果
        """
        from agents.base_agent import BaseAgentRunner, AgentRequest

        runner = BaseAgentRunner()
        result = runner.run(AgentRequest(
            agent_name=agent_name,
            method=method,
            params=params,
        ))

        if result.success:
            data = result.data
            # 将 Pydantic model 转为 dict
            if hasattr(data, 'model_dump'):
                return json.dumps(data.model_dump(exclude_none=True), ensure_ascii=False)
            return json.dumps({"result": str(data)}, ensure_ascii=False)
        else:
            return json.dumps({"error": result.error}, ensure_ascii=False)
