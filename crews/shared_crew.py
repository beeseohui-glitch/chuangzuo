"""
共享能力 Crew - 跨平台通用能力
"""

from typing import Optional
from crewai import Crew, Agent
from crewai.tools import BaseTool

from agents import MaterialAgent, ComplianceAgent


class SharedCrew:
    """共享能力 Crew"""

    def __init__(
        self,
        agents: Optional[dict[str, Agent]] = None,
        tools: Optional[dict[str, list[BaseTool]]] = None,
        verbose: bool = True,
    ):
        """
        初始化共享能力 Crew

        Args:
            agents: Agent 实例字典
            tools: 工具字典
            verbose: 是否输出详细日志
        """
        self.verbose = verbose

        # 初始化 Agents
        self._material_agent = agents.get("material") if agents else None
        self._compliance_agent = agents.get("compliance") if agents else None

        # 初始化 Tools
        self._tools = tools or {}

        self._crew: Optional[Crew] = None

    @property
    def material_agent(self) -> MaterialAgent:
        if self._material_agent is None:
            self._material_agent = MaterialAgent(tools=self._tools.get("material", []))
        return self._material_agent

    @property
    def compliance_agent(self) -> ComplianceAgent:
        if self._compliance_agent is None:
            self._compliance_agent = ComplianceAgent(tools=self._tools.get("compliance", []))
        return self._compliance_agent

    def compose(self) -> Crew:
        """
        组合 Crew

        Returns:
            Crew: 组合好的 Crew
        """
        if self._crew is None:
            self._crew = Crew(
                agents=[
                    self.material_agent.agent,
                    self.compliance_agent.agent,
                ],
                tasks=[],
                verbose=self.verbose,
            )
        return self._crew

    def search_materials(
        self,
        product: str,
        scene: Optional[str] = None,
        persona: Optional[str] = None,
        enterprise_id: Optional[str] = None,
    ):
        """
        检索素材

        Args:
            product: 产品名称
            scene: 使用场景
            persona: 人群画像
            enterprise_id: 企业ID

        Returns:
            MaterialPack: 素材包
        """
        return self.material_agent.search(
            product=product,
            scene=scene,
            persona=persona,
            enterprise_id=enterprise_id,
        )

    def check_compliance(
        self,
        title: str,
        article: str,
        tags: list[str],
        brand_taboos: Optional[list[str]] = None,
    ):
        """
        检查合规性

        Args:
            title: 标题
            article: 正文
            tags: 标签
            brand_taboos: 品牌禁忌词

        Returns:
            ComplianceReport: 合规报告
        """
        return self.compliance_agent.check(
            title=title,
            article=article,
            tags=tags,
            brand_taboos=brand_taboos,
        )
