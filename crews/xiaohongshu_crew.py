"""
小红书创作 Crew
"""

from typing import Optional
from crewai import Crew, Agent
from crewai.tools import BaseTool

from agents import TitleAgent, ArticleAgent, TagAgent, ComplianceAgent, MaterialAgent
from config import XIAOHONGSHU_CREW
from models import MaterialPack, NoteOutput, ComplianceReport


class XiaohongshuCrew:
    """小红书创作 Crew"""

    def __init__(
        self,
        agents: Optional[dict[str, Agent]] = None,
        tools: Optional[dict[str, list[BaseTool]]] = None,
        verbose: bool = True,
    ):
        """
        初始化小红书创作 Crew

        Args:
            agents: Agent 实例字典
            tools: 工具字典
            verbose: 是否输出详细日志
        """
        self.config = XIAOHONGSHU_CREW
        self.verbose = verbose

        # 初始化 Agents
        self._title_agent = agents.get("title") if agents else None
        self._article_agent = agents.get("article") if agents else None
        self._tag_agent = agents.get("tag") if agents else None
        self._compliance_agent = agents.get("compliance") if agents else None
        self._material_agent = agents.get("material") if agents else None

        # 初始化 Tools
        self._tools = tools or {}

        self._crew: Optional[Crew] = None

    @property
    def title_agent(self) -> TitleAgent:
        if self._title_agent is None:
            self._title_agent = TitleAgent(tools=self._tools.get("title", []))
        return self._title_agent

    @property
    def article_agent(self) -> ArticleAgent:
        if self._article_agent is None:
            self._article_agent = ArticleAgent(tools=self._tools.get("article", []))
        return self._article_agent

    @property
    def tag_agent(self) -> TagAgent:
        if self._tag_agent is None:
            self._tag_agent = TagAgent(tools=self._tools.get("tag", []))
        return self._tag_agent

    @property
    def compliance_agent(self) -> ComplianceAgent:
        if self._compliance_agent is None:
            self._compliance_agent = ComplianceAgent(tools=self._tools.get("compliance", []))
        return self._compliance_agent

    @property
    def material_agent(self) -> MaterialAgent:
        if self._material_agent is None:
            self._material_agent = MaterialAgent(tools=self._tools.get("material", []))
        return self._material_agent

    def compose(self) -> Crew:
        """
        组合 Crew

        Returns:
            Crew: 组合好的 Crew
        """
        if self._crew is None:
            self._crew = Crew(
                agents=[
                    self.title_agent.agent,
                    self.article_agent.agent,
                    self.tag_agent.agent,
                    self.compliance_agent.agent,
                ],
                tasks=[],
                verbose=self.verbose,
            )
        return self._crew

    def run(
        self,
        topic: str,
        material_pack: dict,
        historical_titles: Optional[list[str]] = None,
    ) -> dict:
        """
        运行小红书创作流程

        Args:
            topic: 选题方向
            material_pack: 素材包
            historical_titles: 历史标题列表

        Returns:
            dict: 包含 title_output, note_output, tags, compliance_report
        """
        crew = self.compose()

        # Step 1: 生成标题
        title_output = self.title_agent.generate(
            topic=topic,
            material_pack=material_pack,
            historical_titles=historical_titles,
        )

        if not title_output.titles:
            return {
                "title_output": title_output,
                "note_output": None,
                "tags": [],
                "compliance_report": None,
                "error": "标题生成失败",
            }

        # Step 2: 选择标题（使用评分最高的）
        selected_title = title_output.titles[0].title

        # Step 3: 生成正文
        note_output = self.article_agent.generate(
            title=selected_title,
            material_pack=material_pack,
        )

        if not note_output.article:
            return {
                "title_output": title_output,
                "note_output": note_output,
                "tags": [],
                "compliance_report": None,
                "error": "正文生成失败",
            }

        # Step 4: 生成标签
        tags = self.tag_agent.generate(
            article=note_output.article,
            title=selected_title,
            material_pack=material_pack,
        )

        # Step 5: 合规检查
        brand_taboos = material_pack.get("brand", {}).get("taboos", [])
        compliance_report = self.compliance_agent.check(
            title=selected_title,
            article=note_output.article,
            tags=tags,
            brand_taboos=brand_taboos,
        )

        return {
            "title_output": title_output,
            "selected_title": selected_title,
            "note_output": note_output,
            "tags": tags,
            "compliance_report": compliance_report,
        }

    def run_with_retry(
        self,
        topic: str,
        material_pack: dict,
        historical_titles: Optional[list[str]] = None,
        max_retries: int = 2,
    ) -> dict:
        """
        带重试的小红书创作流程

        Args:
            topic: 选题方向
            material_pack: 素材包
            historical_titles: 历史标题列表
            max_retries: 最大重试次数

        Returns:
            dict: 创作结果
        """
        result = self.run(topic, material_pack, historical_titles)

        for attempt in range(max_retries):
            if self._is_acceptable(result):
                return result

            # 如果合规不通过，尝试修改
            if result.get("compliance_report") and result["compliance_report"].has_p0_issues:
                # 使用 article_agent 修改内容
                new_note = self.article_agent.generate(
                    title=result["selected_title"],
                    material_pack=material_pack,
                )
                result["note_output"] = new_note

                # 重新检查合规
                result["compliance_report"] = self.compliance_agent.check(
                    title=result["selected_title"],
                    article=new_note.article,
                    tags=result["tags"],
                    brand_taboos=material_pack.get("brand", {}).get("taboos", []),
                )

        return result

    def _is_acceptable(self, result: dict) -> bool:
        """检查结果是否可接受"""
        if result.get("error"):
            return False

        note_output = result.get("note_output")
        if not note_output:
            return False

        # 检查 AI 味评分
        if note_output.ai_flavor_score < 70:
            return False

        # 检查合规
        compliance_report = result.get("compliance_report")
        if compliance_report and compliance_report.has_p0_issues:
            return False

        return True
