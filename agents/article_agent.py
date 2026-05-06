"""
正文 Agent - 小红书正文创作专家
"""

import json
import os
from pathlib import Path
from typing import Optional

from crewai import Agent
from crewai.llm import LLM
from crewai.tools import BaseTool

from config import ARTICLE_AGENT, LLMConfig
from models import NoteOutput, Paragraph
from validators import AIFlavorScorer


class ArticleAgent:
    """小红书正文创作Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = ARTICLE_AGENT
        self.llm_config = llm_config
        self.tools = tools or []
        self._agent: Optional[Agent] = None
        self._scorer = AIFlavorScorer()

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
                role="小红书正文创作专家",
                goal="创作符合小红书风格的高质量正文",
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
        title: str,
        material_pack: dict,
        max_retries: int = 2,
    ) -> NoteOutput:
        """
        生成正文

        Args:
            title: 选定的标题
            material_pack: 素材包
            max_retries: 最大重试次数

        Returns:
            NoteOutput: 笔记输出
        """
        for attempt in range(max_retries + 1):
            prompt = self._build_prompt(title, material_pack, attempt)

            response = self.agent.kickoff(prompt)

            try:
                content = response.content if hasattr(response, "content") else str(response)
                data = self._parse_response(content)

                # Ensure title is set
                if 'title' not in data:
                    data['title'] = title

                note = NoteOutput(**data)

                # 自评AI味评分
                ai_score = self._scorer.score(note.article)
                note.ai_flavor_score = ai_score

                # 段落结构检查
                if not note.paragraphs:
                    note.paragraphs = self._build_paragraphs(note.article)

                # 检查是否需要重试
                if ai_score >= 70 or attempt >= max_retries:
                    if ai_score < 70:
                        note.metadata["warning"] = f"AI味评分{ai_score}分，建议人工润色"
                    return note

            except Exception as e:
                if attempt >= max_retries:
                    return NoteOutput(
                        title=title,
                        article="",
                        tags=[],
                        ai_flavor_score=0,
                        metadata={"error": str(e)},
                    )

        return NoteOutput(
            title=title,
            article="",
            tags=[],
            ai_flavor_score=0,
        )

    def _build_prompt(
        self,
        title: str,
        material_pack: dict,
        attempt: int = 0,
    ) -> str:
        """构建提示词"""
        retry_instruction = ""
        if attempt > 0:
            retry_instruction = f"""
【重试提示】上次生成的文本AI味太重，请更加注重：
- 使用更多口语化表达
- 加入更多生活细节和个人感受
- 避免工整的排比结构
- 使用感叹句和反问句增加情感
"""

        prompt = f"""
请根据以下信息创作小红书正文：

选定标题：{title}

素材包信息：
- 品牌：{material_pack.get('brand', {}).get('name', '未知')}
- 产品：{material_pack.get('product', {}).get('name', '未知')}
- 核心卖点：{', '.join(material_pack.get('product', {}).get('selling_points', [])[:3])}
- 成分：{', '.join(material_pack.get('product', {}).get('ingredients', [])[:3])}
- 人群：{material_pack.get('persona', {}).get('profile', '未知')}
- 使用场景：{material_pack.get('scene', [{}])[0].get('description', '未知') if material_pack.get('scene') else '未知'}
- 品牌禁忌：{', '.join(material_pack.get('brand', {}).get('taboos', []))}

{retry_instruction}

要求：
- 字数300-600字
- 口语化，像朋友聊天
- 善用感叹句、反问句
- emoji 作为节奏标记，不堆砌
- 加入生活细节增加真实感
- 结构：痛点引入→产品发现→卖点展开→真实体验→互动引导
- 避免"首先、其次、最后"的工整结构
- 必须包含安全声明

输出格式为JSON：
{{
  "article": "完整正文",
  "paragraphs": [
    {{"content": "段落内容", "function": "功能标注"}}
  ],
  "ai_flavor_score": 评分
}}
"""

        return prompt

    def _parse_response(self, content: str) -> dict:
        """解析响应"""
        start = content.find("{")
        end = content.rfind("}") + 1

        if start != -1 and end != 0:
            json_str = content[start:end]
            return json.loads(json_str)

        raise ValueError(f"Cannot parse JSON from response: {content[:200]}")

    def _build_paragraphs(self, article: str) -> list[Paragraph]:
        """根据正文内容构建段落结构"""
        paragraphs = article.split("\n\n")
        functions = ["痛点引入", "产品发现", "卖点展开", "真实体验", "互动引导"]

        result = []
        for i, p in enumerate(paragraphs):
            if p.strip():
                func = functions[min(i, len(functions) - 1)]
                result.append(Paragraph(content=p.strip(), function=func))

        return result

    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """你是小红书正文创作专家，擅长创作口语化、真实感强的内容。
结构模板：痛点引入→产品发现→卖点展开→真实体验→互动引导
去AI味策略：口语化语气词、避免工整排比、句式长短不一、加入生活细节"""
