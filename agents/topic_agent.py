"""
选题 Agent - 内容选题专家
"""

import json
import logging
from typing import Optional

from crewai import Agent
from crewai.tools import BaseTool

from config import TOPIC_AGENT, LLMManagerConfig
from config.llm_config import get_llm_for_agent
from models import TopicIdea, TopicCategory, TopicSource, TopicListOutput
from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm
from tools.llm_tools import LLMResponseParser

logger = logging.getLogger(__name__)


class TopicAgent:
    """内容选题Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMManagerConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = TOPIC_AGENT
        self._llm_config = llm_config or get_llm_for_agent("topic")
        self.tools = tools or []
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        """获取 CrewAI Agent 实例"""
        if self._agent is None:
            prompt = prompt_manager.load_prompt("topic_agent")
            self._agent = Agent(
                role="内容选题专家",
                goal="发现热门选题并生成有吸引力的选题标题",
                backstory=prompt,
                tools=self.tools,
                verbose=True,
                llm=create_llm(self._llm_config),
            )
        return self._agent

    def generate_topics(
        self,
        category: str,
        product: str,
        brand_name: str,
        target_persona: str,
        num_topics: int = 5,
    ) -> TopicListOutput:
        """
        生成选题列表

        Args:
            category: 行业分类
            product: 产品名称
            brand_name: 品牌名称
            target_persona: 目标人群
            num_topics: 生成数量

        Returns:
            TopicListOutput: 选题列表输出
        """
        prompt = self._build_prompt(category, product, brand_name, target_persona, num_topics)

        response = self.agent.kickoff(prompt)

        try:
            content = response.content if hasattr(response, "content") else str(response)
            data = LLMResponseParser.parse_json(content)

            topics = []
            for t in data.get("topics", []):
                try:
                    cat = TopicCategory(t.get("category", "health_product"))
                except ValueError:
                    cat = TopicCategory.HEALTH_PRODUCT
                try:
                    src = TopicSource(t.get("source", "trending"))
                except ValueError:
                    src = TopicSource.TRENDING
                topics.append(TopicIdea(
                    id=t.get("id", "topic_unknown"), title=t.get("title", ""),
                    description=t.get("description", ""), category=cat, source=src,
                    keywords=t.get("keywords", []), target_persona=t.get("target_persona", ""),
                    estimated_views=t.get("estimated_views"), competition_level=t.get("competition_level", "medium"),
                    recommended_platforms=t.get("recommended_platforms", ["xiaohongshu"]),
                    content_angle=t.get("content_angle", ""),
                ))
            return TopicListOutput(topics=topics, total=len(topics), page=1, page_size=len(topics))
        except Exception as e:
            return TopicListOutput(
                topics=[],
                total=0,
                warnings=[f"选题生成失败: {str(e)[:100]}"]
            )

    def _build_prompt(
        self,
        category: str,
        product: str,
        brand_name: str,
        target_persona: str,
        num_topics: int,
    ) -> str:
        """构建提示词"""
        return f"""
请为以下产品生成{num_topics}个热门选题：

行业分类：{category}
产品名称：{product}
品牌名称：{brand_name}
目标人群：{target_persona}

要求：
1. 结合当前热门趋势和目标人群痛点
2. 每个选题包含：标题、描述、关键词、预估浏览量、竞争程度
3. 标题15-30字，描述50-100字
4. 覆盖不同角度：产品功效、使用场景、真实体验、对比评测等
5. 差异化避免同质化

输出格式：
{{"topics": [{{"id": "topic_{{timestamp}}_{{random}}", "title": "标题", "description": "描述", "category": "{category}", "source": "trending", "keywords": ["关键词1", "关键词2"], "target_persona": "{target_persona}", "estimated_views": 10000, "competition_level": "medium", "recommended_platforms": ["xiaohongshu"], "content_angle": "角度"}}]}}
"""