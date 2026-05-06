"""
选题 Agent - 内容选题专家
"""

import json
import os
from pathlib import Path
from typing import Optional

from crewai import Agent
from crewai.llm import LLM
from crewai.tools import BaseTool

from config import TOPIC_AGENT, LLMConfig
from models import TopicIdea, TopicCategory, TopicSource, TopicListOutput


class TopicAgent:
    """内容选题Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = TOPIC_AGENT
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
                role="内容选题专家",
                goal="发现热门选题并生成有吸引力的选题标题",
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
        return OpenAI(
            api_key=os.getenv("MINIMAX_API_KEY", ""),
            api_base=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1"),
        )

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
            return self._parse_response(content)
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

    def _parse_response(self, content: str) -> TopicListOutput:
        """解析响应"""
        start = content.find("{")
        end = content.rfind("}") + 1

        if start != -1 and end != 0:
            json_str = content[start:end]
            data = json.loads(json_str)

            # 转换 topics
            topics = []
            for t in data.get("topics", []):
                # 确保category是有效的枚举值
                cat_str = t.get("category", "health_product")
                try:
                    cat = TopicCategory(cat_str)
                except ValueError:
                    cat = TopicCategory.HEALTH_PRODUCT

                # 确保source是有效的枚举值
                src_str = t.get("source", "trending")
                try:
                    src = TopicSource(src_str)
                except ValueError:
                    src = TopicSource.TRENDING

                topics.append(TopicIdea(
                    id=t.get("id", f"topic_unknown"),
                    title=t.get("title", ""),
                    description=t.get("description", ""),
                    category=cat,
                    source=src,
                    keywords=t.get("keywords", []),
                    target_persona=t.get("target_persona", ""),
                    estimated_views=t.get("estimated_views"),
                    competition_level=t.get("competition_level", "medium"),
                    recommended_platforms=t.get("recommended_platforms", ["xiaohongshu"]),
                    content_angle=t.get("content_angle", ""),
                ))

            return TopicListOutput(
                topics=topics,
                total=len(topics),
                page=1,
                page_size=len(topics),
            )

        raise ValueError(f"Cannot parse TopicListOutput from response: {content[:200]}")

    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """你是内容选题专家，擅长发现热门选题并生成有吸引力的标题。
选题来源：热门趋势、季节性、新品发布、竞品分析、用户反馈、知识库
策略：人群痛点挖掘、差异化角度、热门趋势捕捉"""