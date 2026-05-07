"""
标题 Agent - 小红书标题创作专家

Prompt：从 prompts/title_agent.md 加载
8大标题策略
输出：5个标题，每个含 title, strategy, score, reason
Harness：标题数量校验 + 相似度去重 + 违禁词检查 + 最多重试2次
"""

import json
import logging
from typing import Optional

from crewai import Agent
from crewai.tools import BaseTool

from config import TITLE_AGENT, LLMManagerConfig
from models import TitleOutput, TitleOption
from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm
from tools.llm_tools import LLMCallTool, LLMResponseParser

logger = logging.getLogger(__name__)


class TitleAgent:
    """小红书标题创作Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMManagerConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = TITLE_AGENT
        self._llm_config = llm_config
        self._tools = tools or []
        self._agent: Optional[Agent] = None
        self._llm_tool: Optional[LLMCallTool] = None

    @property
    def llm_tool(self) -> LLMCallTool:
        """获取 LLM 调用工具（带降级）"""
        if self._llm_tool is None:
            self._llm_tool = LLMCallTool(self._llm_config)
        return self._llm_tool

    @property
    def agent(self) -> Agent:
        """获取 CrewAI Agent 实例"""
        if self._agent is None:
            prompt = prompt_manager.load_prompt("title_agent")

            self._agent = Agent(
                role="小红书标题创作专家",
                goal="生成5个高质量的小红书标题",
                backstory=prompt,
                tools=self._tools,
                verbose=True,
                llm=create_llm(self._llm_config),
            )
        return self._agent

    def generate(
        self,
        topic: str,
        material_pack: dict,
        historical_titles: Optional[list[str]] = None,
    ) -> TitleOutput:
        """
        生成标题

        Args:
            topic: 选题方向
            material_pack: 素材包（dict 格式）
            historical_titles: 历史标题列表（用于去重）

        Returns:
            TitleOutput: 标题输出
        """
        prompt = self._build_prompt(topic, material_pack, historical_titles)

        max_retries = self.config.max_retries
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                response = self.agent.kickoff(prompt)
                content = response.content if hasattr(response, "content") else str(response)
                data = LLMResponseParser.parse_json(content)
                result = TitleOutput(**data)

                # 校验标题数量
                if len(result.titles) < 5:
                    logger.warning(f"Title count {len(result.titles)} < 5, retrying ({attempt+1}/{max_retries})")
                    prompt += f"\n\n[系统提示] 上次只生成了{len(result.titles)}个标题，请确保生成5个不同策略的标题。"
                    continue

                return result

            except Exception as e:
                last_error = e
                logger.error(f"Title generation failed (attempt {attempt+1}): {e}")

        # 所有重试失败，返回降级结果
        return TitleOutput(
            titles=[],
            warnings=[f"标题生成失败（已重试{max_retries}次）: {last_error}"],
        )

    def _build_prompt(
        self,
        topic: str,
        material_pack: dict,
        historical_titles: Optional[list[str]] = None,
    ) -> str:
        """构建用户提示词"""
        brand = material_pack.get("brand") or {}
        product = material_pack.get("product") or {}
        persona = material_pack.get("persona") or {}

        prompt = f"""请根据以下信息生成小红书标题：

选题方向：{topic}

素材包信息：
- 品牌：{brand.get('name', '未知')}
- 产品：{product.get('name', '未知')}
- 卖点：{', '.join((product.get('selling_points') or [])[:3])}
- 人群：{persona.get('profile', '未知')}
- 品牌禁忌：{', '.join(brand.get('taboos') or [])}
"""

        if historical_titles:
            prompt += "\n历史标题（需避免重复）：\n"
            for i, title in enumerate(historical_titles[:10], 1):
                prompt += f"{i}. {title}\n"

        prompt += """
请生成5个不同策略的标题，每个标题15-20字。
输出格式为JSON：
{
  "titles": [
    {"title": "标题内容", "strategy": "策略名称", "score": 8, "reason": "评分理由"}
  ]
}
"""
        return prompt
