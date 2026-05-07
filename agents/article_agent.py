"""
正文 Agent - 小红书正文创作专家

Prompt：从 prompts/article_agent.md 加载
输出：NoteOutput（article + paragraphs + ai_flavor_score）
Harness：AI味评分 + 段落结构检查 + 最多重试2次
"""

import json
import logging
from typing import Optional

from crewai import Agent
from crewai.tools import BaseTool

from config import ARTICLE_AGENT, LLMManagerConfig
from models import NoteOutput, Paragraph
from validators import AIFlavorScorer
from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm
from tools.llm_tools import LLMCallTool, LLMResponseParser

logger = logging.getLogger(__name__)


class ArticleAgent:
    """小红书正文创作Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMManagerConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = ARTICLE_AGENT
        self._llm_config = llm_config
        self._tools = tools or []
        self._agent: Optional[Agent] = None
        self._llm_tool: Optional[LLMCallTool] = None
        self._scorer = AIFlavorScorer()

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
            prompt = prompt_manager.load_prompt("article_agent")

            self._agent = Agent(
                role="小红书正文创作专家",
                goal="创作符合小红书风格的高质量正文",
                backstory=prompt,
                tools=self._tools,
                verbose=True,
                llm=create_llm(self._llm_config),
            )
        return self._agent

    def generate(
        self,
        title: str,
        material_pack: dict,
    ) -> NoteOutput:
        """
        生成正文

        Args:
            title: 选定的标题
            material_pack: 素材包

        Returns:
            NoteOutput: 笔记输出
        """
        max_retries = self.config.max_retries
        last_error = None

        for attempt in range(max_retries + 1):
            prompt = self._build_prompt(title, material_pack, attempt)

            try:
                response = self.agent.kickoff(prompt)
                content = response.content if hasattr(response, "content") else str(response)
                data = LLMResponseParser.parse_json(content)

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

                logger.warning(f"AI flavor score {ai_score} < 70, retrying ({attempt+1}/{max_retries})")

            except Exception as e:
                last_error = e
                logger.error(f"Article generation failed (attempt {attempt+1}): {e}")

        # 所有重试失败，返回降级结果
        return NoteOutput(
            title=title,
            article="",
            tags=[],
            ai_flavor_score=0,
            metadata={"error": f"正文生成失败（已重试{max_retries}次）: {last_error}"},
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

        brand = material_pack.get('brand') or {}
        product = material_pack.get('product') or {}
        persona = material_pack.get('persona') or {}
        scenes = material_pack.get('scene') or []
        scene_desc = scenes[0].get('description', '未知') if scenes else '未知'

        prompt = f"""
请根据以下信息创作小红书正文：

选定标题：{title}

素材包信息：
- 品牌：{brand.get('name', '未知')}
- 产品：{product.get('name', '未知')}
- 核心卖点：{', '.join((product.get('selling_points') or [])[:3])}
- 成分：{', '.join((product.get('ingredients') or [])[:3])}
- 人群：{persona.get('profile', '未知')}
- 使用场景：{scene_desc}
- 品牌禁忌：{', '.join(brand.get('taboos') or [])}

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

