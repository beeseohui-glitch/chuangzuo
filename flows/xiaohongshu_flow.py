"""
小红书创作 Flow - 基于 CrewAI Flows 的事件驱动工作流
"""

from typing import Optional, Literal
from crewai.flow.flow import Flow, listen, start

from crews import XiaohongshuCrew
from validators import ResultValidator
from models import MaterialPack, TitleOutput, NoteOutput, ComplianceReport


class XiaohongshuFlow(Flow):
    """
    小红书创作工作流

    流程：
    1. material_search - 素材检索
    2. validate_material - 校验素材包
    3. title_generation - 生成标题
    4. validate_titles - 校验标题
    5. article_generation - 生成正文
    6. validate_article - 校验正文 + 合规检查
    7. tag_generation - 生成标签
    8. final_output - 最终输出
    """

    def __init__(self, crew: Optional[XiaohongshuCrew] = None):
        super().__init__()
        self.crew = crew or XiaohongshuCrew(verbose=False)
        self.validator = ResultValidator()

        # 流程状态
        self._material_pack: Optional[MaterialPack] = None
        self._title_output: Optional[TitleOutput] = None
        self._note_output: Optional[NoteOutput] = None
        self._tags: list[str] = []
        self._compliance_report: Optional[ComplianceReport] = None
        self._selected_title: Optional[str] = None
        self._errors: list[str] = []

    @start()
    def material_search(self, input_data: dict) -> MaterialPack:
        """
        素材检索

        Args:
            input_data: 包含 product, scene, persona, enterprise_id

        Returns:
            MaterialPack: 素材包
        """
        result = self.crew.material_agent.search(
            product=input_data.get("product", ""),
            scene=input_data.get("scene"),
            persona=input_data.get("persona"),
            enterprise_id=input_data.get("enterprise_id"),
        )

        self._material_pack = result
        return result

    @listen(material_search)
    def validate_material(self, material_pack: MaterialPack) -> MaterialPack:
        """
        校验素材包

        Args:
            material_pack: 素材包

        Returns:
            MaterialPack: 校验后的素材包
        """
        validation = self.validator.validate_material_pack(material_pack)

        if not validation.passed:
            self._errors.append(f"素材包校验失败: {', '.join(validation.issues)}")

            # 如果缺少非关键信息，继续流程但记录警告
            if validation.missing_fields:
                material_pack.missing_fields = validation.missing_fields

        return material_pack

    @listen(validate_material)
    def title_generation(self, material_pack: MaterialPack) -> TitleOutput:
        """
        生成标题

        Args:
            material_pack: 素材包

        Returns:
            TitleOutput: 标题输出
        """
        topic = material_pack.product.name if material_pack.product else "产品推荐"

        result = self.crew.title_agent.generate(
            topic=topic,
            material_pack=material_pack.model_dump(),
            historical_titles=None,
        )

        self._title_output = result
        return result

    @listen(title_generation)
    def validate_titles(self, title_output: TitleOutput) -> TitleOutput:
        """
        校验标题

        Args:
            title_output: 标题输出

        Returns:
            TitleOutput: 校验后的标题输出
        """
        validation = self.validator.validate_title_output(title_output)

        if not validation.passed:
            self._errors.append(f"标题校验失败: {', '.join(validation.issues)}")

        return title_output

    @listen(validate_titles)
    def article_generation(self, title_output: TitleOutput) -> NoteOutput:
        """
        生成正文

        Args:
            title_output: 标题输出

        Returns:
            NoteOutput: 笔记输出
        """
        if not title_output.titles:
            return NoteOutput(
                title="",
                article="",
                tags=[],
                ai_flavor_score=0,
                metadata={"error": "没有可用标题"},
            )

        # 选择评分最高的标题
        self._selected_title = title_output.titles[0].title

        result = self.crew.article_agent.generate(
            title=self._selected_title,
            material_pack=self._material_pack.model_dump() if self._material_pack else {},
        )

        self._note_output = result
        return result

    @listen(article_generation)
    def validate_and_compliance(self, note_output: NoteOutput) -> dict:
        """
        校验正文 + 合规检查

        Args:
            note_output: 笔记输出

        Returns:
            dict: 包含 note_output 和 compliance_report
        """
        # 校验正文
        article_validation = self.validator.validate_article_output(note_output)

        if not article_validation.passed:
            self._errors.append(f"正文校验失败: {', '.join(article_validation.issues)}")

        # 合规检查
        if self._selected_title and note_output.article:
            self._compliance_report = self.crew.compliance_agent.check(
                title=self._selected_title,
                article=note_output.article,
                tags=note_output.tags or [],
                brand_taboos=self._material_pack.brand.taboos if self._material_pack and self._material_pack.brand else [],
            )

        return {
            "note_output": note_output,
            "compliance_report": self._compliance_report,
            "article_validation": article_validation,
        }

    @listen(validate_and_compliance)
    def tag_generation(self, result: dict) -> list[str]:
        """
        生成标签

        Args:
            result: validate_and_compliance 返回的结果

        Returns:
            list[str]: 标签列表
        """
        note_output = result.get("note_output")

        if not note_output or not note_output.article:
            return []

        tags = self.crew.tag_agent.generate(
            article=note_output.article,
            title=self._selected_title or "",
            material_pack=self._material_pack.model_dump() if self._material_pack else {},
        )

        self._tags = tags
        return tags

    @listen(tag_generation)
    def final_output(self, tags: list[str]) -> dict:
        """
        最终输出

        Args:
            tags: 标签列表

        Returns:
            dict: 完整结果
        """
        return {
            "success": len(self._errors) == 0,
            "errors": self._errors,
            "selected_title": self._selected_title,
            "note_output": self._note_output,
            "tags": tags or self._tags,
            "compliance_report": self._compliance_report,
            "material_pack": self._material_pack,
        }

    def run(self, input_data: dict) -> dict:
        """
        运行完整流程

        Args:
            input_data: 包含 product, scene, persona, enterprise_id

        Returns:
            dict: 完整结果
        """
        # 重置状态
        self._material_pack = None
        self._title_output = None
        self._note_output = None
        self._tags = []
        self._compliance_report = None
        self._selected_title = None
        self._errors = []

        # 执行父类 run 方法
        return super().run(input_data)
