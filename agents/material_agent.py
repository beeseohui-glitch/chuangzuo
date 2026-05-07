"""
素材检索 Agent - 知识库检索专家
"""

import json
import logging
from typing import Optional

from crewai import Agent
from crewai.tools import BaseTool

from config import MATERIAL_SEARCH_AGENT, LLMManagerConfig
from models import MaterialPack, BrandInfo, ProductInfo, PersonaInfo, SceneInfo, ComplianceRules
from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm
from tools.llm_tools import LLMResponseParser

logger = logging.getLogger(__name__)


class MaterialAgent:
    """素材检索Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMManagerConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = MATERIAL_SEARCH_AGENT
        self._llm_config = llm_config
        self.tools = tools or []
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        """获取 CrewAI Agent 实例"""
        if self._agent is None:
            prompt = prompt_manager.load_prompt("material_search")
            self._agent = Agent(
                role="知识库检索专家",
                goal="从知识库检索相关素材并组装素材包",
                backstory=prompt,
                tools=self.tools,
                verbose=True,
                llm=create_llm(self._llm_config),
            )
        return self._agent

    def search(
        self,
        product: str,
        scene: Optional[str] = None,
        persona: Optional[str] = None,
        enterprise_id: Optional[str] = None,
    ) -> MaterialPack:
        """
        检索素材

        Args:
            product: 产品名称
            scene: 场景（可选）
            persona: 人群（可选）
            enterprise_id: 企业ID（可选）

        Returns:
            MaterialPack: 素材包
        """
        prompt = self._build_prompt(product, scene, persona)

        response = self.agent.kickoff(prompt)

        try:
            content = response.content if hasattr(response, "content") else str(response)
            data = LLMResponseParser.parse_json(content)

            brand = BrandInfo(**data["brand"]) if data.get("brand") else None
            product = ProductInfo(**data["product"]) if data.get("product") else None
            persona = PersonaInfo(**data["persona"]) if data.get("persona") else None
            scenes = [SceneInfo(**s) for s in data.get("scene", [])]
            compliance = ComplianceRules(**data["compliance"]) if data.get("compliance") else None

            return MaterialPack(
                brand=brand, product=product, persona=persona,
                scene=scenes, compliance=compliance,
                missing_fields=data.get("missing_fields", []),
            )
        except Exception as e:
            logger.error(f"Material search failed: {e}")
            return MaterialPack(missing_fields=["检索失败"])

    def _build_prompt(
        self,
        product: str,
        scene: Optional[str] = None,
        persona: Optional[str] = None,
    ) -> str:
        """构建提示词"""
        prompt = f"""
请根据以下信息从知识库检索素材并组装素材包：

产品：{product}
场景：{scene or '通用'}
人群：{persona or '通用'}

检索优先级：
1. 企业私有库 - 品牌资料、产品资料
2. 行业知识库 - 选题库、用户画像
3. 公共知识库 - 平台规则、创作方法论

输出格式为JSON：
{{
  "brand": {{
    "name": "品牌名称",
    "tone": ["调性词1", "调性词2"],
    "taboos": ["禁忌词1"]
  }},
  "product": {{
    "name": "产品名称",
    "selling_points": ["卖点1", "卖点2", "卖点3"],
    "ingredients": ["成分1", "成分2"],
    "evidence": {{"来源": "内容"}}
  }},
  "persona": {{
    "profile": "人群描述",
    "pain_points": ["痛点1", "痛点2"],
    "language_style": "语言风格"
  }},
  "scene": [
    {{"description": "场景描述", "usage_method": "使用方法"}}
  ],
  "compliance": {{
    "rules": ["规则1"],
    "forbidden_groups": ["禁忌人群"]
  }},
  "missing_fields": []
}}
"""

        return prompt
