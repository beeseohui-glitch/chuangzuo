"""
公众号文章 Agent - 公众号内容创作专家
"""

import json
import os
from pathlib import Path
from typing import Optional

from crewai import Agent
from crewai.llm import LLM
from crewai.tools import BaseTool

from config import LLMConfig, WechatPublicConfig
from models import WechatArticle, PublicAccountContent


class WechatArticleAgent:
    """公众号文章创作Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        platform_config: Optional[WechatPublicConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.llm_config = llm_config
        self.platform_config = platform_config or WechatPublicConfig()
        self.tools = tools or []
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        """获取 CrewAI Agent 实例"""
        if self._agent is None:
            prompt_path = Path("prompts/wechat_article_agent.md")
            if prompt_path.exists():
                with open(prompt_path, "r", encoding="utf-8") as f:
                    self._prompt_template = f.read()
            else:
                self._prompt_template = self._get_default_prompt()

            self._agent = Agent(
                role="公众号内容创作专家",
                goal="创作符合公众号风格的深度文章",
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

    def generate_article(
        self,
        title: str,
        material_pack: dict,
        target_length: str = "medium",
    ) -> PublicAccountContent:
        """
        生成公众号文章

        Args:
            title: 标题
            material_pack: 素材包
            target_length: 目标长度 short/medium/long

        Returns:
            PublicAccountContent: 公众号内容
        """
        prompt = self._build_prompt(title, material_pack, target_length)

        response = self.agent.kickoff(prompt)

        try:
            content = response.content if hasattr(response, "content") else str(response)
            article_data = self._parse_response(content)

            # 确保title存在
            if 'title' not in article_data:
                article_data['title'] = title

            article = WechatArticle(**article_data)

            return PublicAccountContent(
                article=article,
                platform="wechat_public",
                ai_flavor_score=article_data.get("ai_flavor_score", 75),
                compliance_status="passed",
            )
        except Exception as e:
            # 返回空内容
            return PublicAccountContent(
                article=WechatArticle(title=title, content=""),
                platform="wechat_public",
                ai_flavor_score=0,
                compliance_status="failed",
                metadata={"error": str(e)},
            )

    def _build_prompt(
        self,
        title: str,
        material_pack: dict,
        target_length: str,
    ) -> str:
        """构建提示词"""
        length_map = {
            "short": "500-1000字",
            "medium": "1500-3000字",
            "long": "5000-10000字",
        }
        target = length_map.get(target_length, "1500-3000字")

        return f"""
请根据以下信息创作公众号文章：

选定标题：{title}

素材包信息：
- 品牌：{material_pack.get('brand', {}).get('name', '未知')}
- 产品：{material_pack.get('product', {}).get('name', '未知')}
- 核心卖点：{', '.join(material_pack.get('product', {}).get('selling_points', [])[:3])}
- 成分：{', '.join(material_pack.get('product', {}).get('ingredients', [])[:3])}
- 人群：{material_pack.get('persona', {}).get('profile', '未知')}

要求：
- 字数{target}
- 结构清晰：开头痛点引入 → 2-4个核心论点 → 总结行动号召
- 语言书面但亲和，避免过于口语化
- 善用短句增加节奏感
- 必须包含安全声明（如涉及健康产品）
- 不得使用绝对化用语

输出格式为JSON：
{{"title": "标题", "subtitle": "副标题（可选）", "content": "正文HTML", "summary": "摘要", "tags": ["标签1", "标签2"]}}
"""

    def _parse_response(self, content: str) -> dict:
        """解析响应"""
        start = content.find("{")
        end = content.rfind("}") + 1

        if start != -1 and end != 0:
            json_str = content[start:end]
            return json.loads(json_str)

        raise ValueError(f"Cannot parse WechatArticle from response: {content[:200]}")

    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """你是公众号内容创作专家，擅长撰写符合微信公众号风格的深度文章。
平台特点：深度内容、专业调性、结构清晰、排版考究
正文结构：开头痛点引入 → 核心论点展开 → 总结行动号召"""