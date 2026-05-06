"""
素材检索 Agent - 知识库检索专家
"""

import json
import os
from pathlib import Path
from typing import Optional

from crewai import Agent
from crewai.llm import LLM
from crewai.tools import BaseTool

from config import MATERIAL_SEARCH_AGENT, LLMConfig
from models import MaterialPack, BrandInfo, ProductInfo, PersonaInfo, SceneInfo, ComplianceRules


class MaterialAgent:
    """素材检索Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = MATERIAL_SEARCH_AGENT
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
                role="知识库检索专家",
                goal="从知识库检索相关素材并组装素材包",
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
            return self._parse_response(content)
        except Exception as e:
            return MaterialPack(
                missing_fields=["检索失败"],
            )

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

    def _parse_response(self, content: str) -> MaterialPack:
        """解析响应"""
        start = content.find("{")
        end = content.rfind("}") + 1

        if start != -1 and end != 0:
            json_str = content[start:end]
            data = json.loads(json_str)

            # 构建 MaterialPack
            brand = None
            if data.get("brand"):
                brand = BrandInfo(**data["brand"])

            product = None
            if data.get("product"):
                product = ProductInfo(**data["product"])

            persona = None
            if data.get("persona"):
                persona = PersonaInfo(**data["persona"])

            scenes = [SceneInfo(**s) for s in data.get("scene", [])]

            compliance = None
            if data.get("compliance"):
                compliance = ComplianceRules(**data["compliance"])

            return MaterialPack(
                brand=brand,
                product=product,
                persona=persona,
                scene=scenes,
                compliance=compliance,
                missing_fields=data.get("missing_fields", []),
            )

        raise ValueError(f"Cannot parse MaterialPack from response: {content[:200]}")

    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """你是知识库检索专家，擅长从三层知识库中检索最相关的素材。
检索优先级：企业私有库 > 行业知识库 > 公共知识库"""
