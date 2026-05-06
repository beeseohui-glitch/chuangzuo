"""
标签 Agent - 小红书标签策略专家
"""

import json
import os
from pathlib import Path
from typing import Optional

from crewai import Agent
from crewai.llm import LLM
from crewai.tools import BaseTool

from config import TAG_AGENT, LLMConfig


class TagAgent:
    """小红书标签创作Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = TAG_AGENT
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
                role="小红书标签策略专家",
                goal="生成8-10个高质量标签",
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
        article: str,
        title: str,
        material_pack: dict,
    ) -> list[str]:
        """
        生成标签

        Args:
            article: 正文内容
            title: 标题
            material_pack: 素材包

        Returns:
            list[str]: 标签列表
        """
        prompt = self._build_prompt(article, title, material_pack)

        response = self.agent.kickoff(prompt)

        try:
            content = response.content if hasattr(response, "content") else str(response)
            return self._parse_response(content)
        except Exception as e:
            return []

    def _build_prompt(
        self,
        article: str,
        title: str,
        material_pack: dict,
    ) -> str:
        """构建提示词"""
        prompt = f"""
请根据以下内容生成小红书标签：

标题：{title}

正文摘要：{article[:200]}...

产品信息：
- 品牌：{material_pack.get('brand', {}).get('name', '未知')}
- 产品：{material_pack.get('product', {}).get('name', '未知')}
- 品类：{', '.join(material_pack.get('product', {}).get('selling_points', [])[:2])}
- 人群：{material_pack.get('persona', {}).get('profile', '未知')}

标签分层策略：
1. 品类大词（必选1-2个）：#护肤 #保健品
2. 功效长尾词（2-3个）：#护肝 #抗老精华
3. 场景词（2-3个）：#酒局必备 #熬夜急救
4. 热度词（1-2个）：根据当前趋势
5. 品牌词（1个）：#品牌名

要求：
- 总数8-10个
- 不得使用与内容无关的热门标签
- 标签必须与内容强关联

输出格式为JSON：
{{"tags": ["#标签1", "#标签2", ...]}}
"""

        return prompt

    def _parse_response(self, content: str) -> list[str]:
        """解析响应"""
        start = content.find("[")
        end = content.rfind("]") + 1

        if start != -1 and end != 0:
            json_str = content[start:end]
            return json.loads(json_str)

        # 尝试找JSON对象
        start = content.find("{")
        end = content.rfind("}") + 1

        if start != -1 and end != 0:
            json_str = content[start:end]
            data = json.loads(json_str)
            if "tags" in data:
                return data["tags"]

        raise ValueError(f"Cannot parse tags from response: {content[:200]}")

    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """你是小红书标签策略专家，擅长生成精准的标签组合。
标签分层策略：
1. 品类大词（必选1-2个）
2. 功效长尾词（2-3个）
3. 场景词（2-3个）
4. 热度词（1-2个）
5. 品牌词（1个）
总数8-10个"""
