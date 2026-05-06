"""
标题 Agent - 小红书标题创作专家
"""

import json
import os
from pathlib import Path
from typing import Optional

from crewai import Agent
from crewai.llm import LLM
from crewai.tools import BaseTool

from config import TITLE_AGENT, LLMConfig
from models import TitleOutput, TitleOption


class TitleAgent:
    """小红书标题创作Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = TITLE_AGENT
        self.llm_config = llm_config
        self.tools = tools or []
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        """获取 CrewAI Agent 实例"""
        if self._agent is None:
            prompt_path = Path(self.config.prompt_file)
            if prompt_path.exists():
                with open(prompt_path, "r", encoding="utf-8") as f:
                    self._prompt_template = f.read()
            else:
                self._prompt_template = self._get_default_prompt()

            self._agent = Agent(
                role="小红书标题创作专家",
                goal="生成5个高质量的小红书标题",
                backstory=self._prompt_template,
                tools=self.tools,
                verbose=True,
                llm=LLM(
                    model="openai/MiniMax-M2.7",
                    api_key=os.getenv("MINIMAX_API_KEY", ""),
                    api_base=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1"),
                    llm_type="litellm",
                ),
            )
        return self._agent

    @property
    def _llm(self):
        """获取 LLM 配置"""
        if self.llm_config:
            return self.llm_config
        from openai import OpenAI
        import os
        return OpenAI(
            api_key=os.getenv("MINIMAX_API_KEY", ""),
            api_base=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1"),
        )

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
            material_pack: 素材包
            historical_titles: 历史标题列表

        Returns:
            TitleOutput: 标题输出
        """
        prompt = self._build_prompt(topic, material_pack, historical_titles)

        response = self.agent.kickoff(prompt)

        try:
            content = response.content if hasattr(response, "content") else str(response)
            data = self._parse_response(content)
            return TitleOutput(**data)
        except Exception as e:
            return TitleOutput(
                titles=[],
                warnings=[f"生成失败: {str(e)}"],
            )

    def _build_prompt(
        self,
        topic: str,
        material_pack: dict,
        historical_titles: Optional[list[str]] = None,
    ) -> str:
        """构建提示词"""
        prompt = f"""
请根据以下信息生成小红书标题：

选题方向：{topic}

素材包信息：
- 品牌：{material_pack.get('brand', {}).get('name', '未知')}
- 产品：{material_pack.get('product', {}).get('name', '未知')}
- 卖点：{', '.join(material_pack.get('product', {}).get('selling_points', [])[:3])}
- 人群：{material_pack.get('persona', {}).get('profile', '未知')}
- 品牌禁忌：{', '.join(material_pack.get('brand', {}).get('taboos', []))}

"""

        if historical_titles:
            prompt += f"历史标题（需避免重复）：\n"
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

    def _parse_response(self, content: str) -> dict:
        """解析响应"""
        # 尝试提取JSON
        start = content.find("{")
        end = content.rfind("}") + 1

        if start != -1 and end != 0:
            json_str = content[start:end]
            return json.loads(json_str)

        raise ValueError(f"Cannot parse JSON from response: {content[:200]}")

    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """你是小红书标题创作专家，擅长使用8大标题策略生成吸引人的标题：
1. 痛点切入型
2. 数字量化型
3. 悬念钩子型
4. 对比反转型
5. 权威背书型
6. 情绪共鸣型
7. 教程攻略型
8. 清单合集型

请生成符合要求的标题。"""
