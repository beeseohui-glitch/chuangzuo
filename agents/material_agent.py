"""
素材检索 Agent - 知识库检索专家

使用 MaterialSearchTool 做真实向量检索（pgvector），
不再通过 LLM kickoff 编造数据。
"""

import logging
from typing import Optional

from crewai import Agent
from crewai.tools import BaseTool
from pydantic import BaseModel

from config import MATERIAL_SEARCH_AGENT, LLMManagerConfig
from models import MaterialPack
from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm

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
        调用 MaterialSearchTool 做真实向量检索

        Args:
            product: 产品名称
            scene: 场景（可选）
            persona: 人群（可选）
            enterprise_id: 企业ID（可选）

        Returns:
            MaterialPack: 素材包
        """
        from tools.material_tools import MaterialSearchTool

        tool = MaterialSearchTool()
        return tool.search(
            product=product,
            scene=scene or "",
            persona=persona or "",
            enterprise_id=enterprise_id or "",
        )


class MaterialAgentRequest(BaseModel):
    """MaterialAgent 独立调用请求"""
    product: str
    scene: Optional[str] = None
    persona: Optional[str] = None
    enterprise_id: Optional[str] = None


def _material_run_standalone(self, req: MaterialAgentRequest) -> MaterialPack:
    return self.search(
        product=req.product,
        scene=req.scene,
        persona=req.persona,
        enterprise_id=req.enterprise_id,
    )


MaterialAgent.run_standalone = _material_run_standalone
