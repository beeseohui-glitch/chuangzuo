"""
统一调度Agent - 理解意图，路由任务
"""

from typing import Optional
from crewai import Agent
from pydantic import BaseModel

from config.agent_config import AgentConfig
from tools.llm_tools import LLMCallTool


class RouterOutput(BaseModel):
    """路由输出"""
    platform: str
    product: str
    scene: str
    style: str
    route_to: str


class OrchestratorAgent:
    """统一调度Agent"""

    def __init__(self, llm: LLMCallTool, config: Optional[AgentConfig] = None):
        self.llm = llm
        self.config = config or AgentConfig()
        self._agent = self._create_agent()

    def _create_agent(self) -> Agent:
        """创建Agent"""
        return Agent(
            role="统一调度者",
            goal="理解用户意图，选择平台，路由任务",
            backstory="你是多平台内容创作系统的总调度者。理解用户需求后，路由到对应平台工作流。",
            tools=[],
            verbose=True,
        )

    def route(self, user_input: str) -> RouterOutput:
        """
        路由用户输入到对应平台

        Args:
            user_input: 用户输入

        Returns:
            RouterOutput: 路由结果
        """
        prompt = f"""请分析以下用户输入，判断目标平台和路由目标：

用户输入：{user_input}

请输出JSON格式：
{{
    "platform": "目标平台：小红书/公众号/抖音/未指定",
    "product": "品牌和产品",
    "scene": "场景/需求",
    "style": "风格要求",
    "route_to": "路由目标工作流名称"
}}

注意：
- 未指定平台时，platform设为"未指定"
- 只做路由，不创作内容
"""
        result = self.llm._run(prompt=prompt, max_tokens=1000, json_mode=True)

        try:
            import json
            data = json.loads(result)
            return RouterOutput(**data)
        except json.JSONDecodeError:
            return RouterOutput(
                platform="未指定",
                product="",
                scene=user_input,
                style="",
                route_to=""
            )

    def clarify(self, question: str) -> str:
        """追问用户以明确意图"""
        prompt = f"""你正在追问用户以明确创作需求。

问题：{question}

请生成一个友好的追问问题，不要暗示任何答案。
"""
        return self.llm._run(prompt=prompt, max_tokens=500)
