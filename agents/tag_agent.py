"""
标签 Agent - 小红书标签策略专家

Prompt：从 prompts/tag_agent.md 加载
5层标签策略：品类大词→功效长尾→场景词→热度词→品牌词
输出：8-10个标签
Harness：标签数量校验 + 格式校验（#开头）+ 最多重试2次
"""

import json
import logging
from typing import Optional

from crewai import Agent
from crewai.tools import BaseTool
from pydantic import BaseModel

from config import TAG_AGENT, LLMManagerConfig
from config.llm_config import get_llm_for_agent
from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm
from tools.llm_tools import LLMCallTool, LLMResponseParser

logger = logging.getLogger(__name__)


class TagAgent:
    """小红书标签创作Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMManagerConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = TAG_AGENT
        self._llm_config = llm_config or get_llm_for_agent("tag")
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
            prompt = prompt_manager.load_prompt("tag_agent")

            self._agent = Agent(
                role="小红书标签策略专家",
                goal="生成8-10个高质量标签",
                backstory=prompt,
                tools=self._tools,
                verbose=True,
                llm=create_llm(self._llm_config),
            )
        return self._agent

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
        max_retries = self.config.max_retries
        last_error = None

        for attempt in range(max_retries + 1):
            prompt = self._build_prompt(article, title, material_pack)

            try:
                response = self.agent.kickoff(prompt)
                content = response.content if hasattr(response, "content") else str(response)
                tags = self._parse_response(content)

                # 校验标签数量
                if len(tags) < 8:
                    logger.warning(f"Tag count {len(tags)} < 8, retrying ({attempt+1}/{max_retries})")
                    prompt += f"\n\n[系统提示] 上次只生成了{len(tags)}个标签，请确保生成8-10个标签。"
                    continue

                # 校验标签格式
                valid_tags = [t for t in tags if t.startswith("#")]
                if len(valid_tags) < len(tags):
                    logger.warning(f"Some tags missing # prefix, fixing")
                    tags = [t if t.startswith("#") else f"#{t}" for t in tags]

                return tags

            except Exception as e:
                last_error = e
                logger.error(f"Tag generation failed (attempt {attempt+1}): {e}")

        # 所有重试失败
        logger.error(f"Tag generation failed after {max_retries} retries: {last_error}")
        return []

    def _build_prompt(
        self,
        article: str,
        title: str,
        material_pack: dict,
    ) -> str:
        """构建提示词"""
        brand = material_pack.get('brand') or {}
        product = material_pack.get('product') or {}
        persona = material_pack.get('persona') or {}

        prompt = f"""
请根据以下内容生成小红书标签：

标题：{title}

正文摘要：{article[:200]}...

产品信息：
- 品牌：{brand.get('name', '未知')}
- 产品：{product.get('name', '未知')}
- 品类：{', '.join((product.get('selling_points') or [])[:2])}
- 人群：{persona.get('profile', '未知')}

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


class TagAgentRequest(BaseModel):
    """TagAgent 独立调用请求"""
    article: str
    title: str
    material_pack: dict


def _tag_run_standalone(self, req: TagAgentRequest) -> list[str]:
    return self.generate(article=req.article, title=req.title, material_pack=req.material_pack)


TagAgent.run_standalone = _tag_run_standalone

