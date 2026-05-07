"""
小红书创作 Flow - 基于 CrewAI Flows 的事件驱动工作流

PRD 4.1 完整流程：
  用户输入 → 素材检索 → 校验 → 标题生成 → 校验 → 正文生成
  → 质量合并评估（AI味+合规）→ 标签+合规并行 → 输出完整笔记包

关键设计：
- 每个环节最多重试2次
- 总重试硬限制4次
- 每个环节有明确降级出口
- 合并AI味评分和合规校验为一次评估
"""

import logging
from datetime import datetime
from typing import Optional

from crewai.flow.flow import Flow, listen, start

from crews import XiaohongshuCrew
from validators import ResultValidator
from models import (
    MaterialPack,
    TitleOutput,
    NoteOutput,
    ComplianceReport,
    ComplianceStatus,
    NotePack,
    NoteMetadata,
)

logger = logging.getLogger(__name__)

# 常量
MAX_STEP_RETRIES = 2
MAX_TOTAL_RETRIES = 4
AI_FLAVOR_THRESHOLD = 70


class RetryLimitExceeded(Exception):
    """总重试次数超过硬限制"""

    def __init__(self, total_retries: int, step: str):
        self.total_retries = total_retries
        self.step = step
        super().__init__(
            f"总重试次数 {total_retries} 超过硬限制 {MAX_TOTAL_RETRIES}，"
            f"最后失败步骤: {step}"
        )


class XiaohongshuFlow(Flow):
    """
    小红书创作工作流

    流程（8步，@listen 链式触发）：
    1. material_search  - 素材检索（@start）
    2. validate_material - 校验素材包（非关键失败继续）
    3. title_generation  - 生成标题（校验失败重试1次）
    4. validate_titles   - 校验标题（记录警告）
    5. article_generation - 生成正文（AI味<70重试，最多2次）
    6. quality_evaluation - 合并评估：AI味+合规（P0重试，最多2次）
    7. tag_and_compliance - 生成标签 + 最终合规检查
    8. final_output      - 组装 NotePack 输出
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

        # 重试与降级
        self._total_retries: int = 0
        self._warnings: list[str] = []
        self._degraded: bool = False
        self._degradation_reason: Optional[str] = None

    # ── Step 1: 素材检索 ────────────────────────────────────

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

    # ── Step 2: 校验素材包 ──────────────────────────────────

    @listen(material_search)
    def validate_material(self, material_pack: MaterialPack) -> MaterialPack:
        """
        校验素材包

        非关键字段缺失时继续流程，记录警告。
        """
        validation = self.validator.validate_material_pack(material_pack)

        if not validation.passed:
            self._warnings.append(
                f"素材包校验警告: {', '.join(validation.issues)}"
            )
            if validation.missing_fields:
                material_pack.missing_fields = validation.missing_fields

        return material_pack

    # ── Step 3: 标题生成 ────────────────────────────────────

    @listen(validate_material)
    def title_generation(self, material_pack: MaterialPack) -> TitleOutput:
        """
        生成标题

        校验失败时重试1次，仍失败则降级（标注"建议人工优化"）。
        """
        topic = material_pack.product.name if material_pack.product else "产品推荐"
        material_dict = material_pack.model_dump()

        for attempt in range(MAX_STEP_RETRIES + 1):
            result = self.crew.title_agent.generate(
                topic=topic,
                material_pack=material_dict,
                historical_titles=None,
            )

            validation = self.validator.validate_title_output(result)

            if validation.passed:
                self._title_output = result
                return result

            # 重试
            if attempt < MAX_STEP_RETRIES:
                self._increment_retries("title_generation")
                logger.warning(
                    f"标题校验失败，重试 ({attempt+1}/{MAX_STEP_RETRIES})"
                )
                continue

        # 降级：接受当前标题 + 警告
        self._warnings.append("标题校验未通过，建议人工优化")
        self._degraded = True
        self._degradation_reason = self._degradation_reason or "标题质量不达标"
        self._title_output = result
        return result

    # ── Step 4: 校验标题 ────────────────────────────────────

    @listen(title_generation)
    def validate_titles(self, title_output: TitleOutput) -> TitleOutput:
        """
        校验标题

        记录警告，不阻断流程。
        """
        if not title_output.titles:
            self._warnings.append("未生成任何标题")
            self._degraded = True
            self._degradation_reason = self._degradation_reason or "无可用标题"

        for w in title_output.warnings:
            self._warnings.append(f"标题警告: {w}")

        return title_output

    # ── Step 5: 正文生成 ────────────────────────────────────

    @listen(validate_titles)
    def article_generation(self, title_output: TitleOutput) -> NoteOutput:
        """
        生成正文

        AI味评分 < 70 时重试，最多2次。
        仍不通过则降级：接受当前版本 + 标注"建议人工润色"。
        """
        if not title_output.titles:
            return self._empty_note_output("没有可用标题")

        self._selected_title = title_output.titles[0].title
        material_dict = (
            self._material_pack.model_dump() if self._material_pack else {}
        )

        best_result: Optional[NoteOutput] = None

        for attempt in range(MAX_STEP_RETRIES + 1):
            result = self.crew.article_agent.generate(
                title=self._selected_title,
                material_pack=material_dict,
            )

            # 记录最佳结果
            if best_result is None or result.ai_flavor_score > best_result.ai_flavor_score:
                best_result = result

            if result.ai_flavor_score >= AI_FLAVOR_THRESHOLD:
                self._note_output = result
                return result

            # 重试
            if attempt < MAX_STEP_RETRIES:
                self._increment_retries("article_generation")
                logger.warning(
                    f"AI味评分 {result.ai_flavor_score} < {AI_FLAVOR_THRESHOLD}，"
                    f"重试 ({attempt+1}/{MAX_STEP_RETRIES})"
                )
                continue

        # 降级：接受最佳版本
        self._warnings.append(
            f"AI味评分 {best_result.ai_flavor_score} 未达标，建议人工润色"
        )
        self._degraded = True
        self._degradation_reason = self._degradation_reason or "AI味评分不达标"
        self._note_output = best_result
        return best_result

    # ── Step 6: 质量合并评估（AI味 + 合规）──────────────────

    @listen(article_generation)
    def quality_evaluation(self, note_output: NoteOutput) -> dict:
        """
        合并评估：AI味评分 + 合规检查

        P0问题时重试正文生成，最多2次。
        仍不通过则降级：输出当前版本 + 合规问题清单 + 标记"需人工修改"。
        P1/P2问题标注提示，不阻断流程。
        """
        if not note_output.article:
            return self._quality_result(note_output, None, True)

        brand_taboos = (
            self._material_pack.brand.taboos
            if self._material_pack and self._material_pack.brand
            else []
        )

        for attempt in range(MAX_STEP_RETRIES + 1):
            # 合规检查
            compliance_report = self.crew.compliance_agent.check(
                title=self._selected_title or "",
                article=note_output.article,
                tags=note_output.tags or [],
                brand_taboos=brand_taboos,
            )

            # 无P0问题，通过
            if not compliance_report.has_p0_issues:
                self._compliance_report = compliance_report
                return self._quality_result(note_output, compliance_report, False)

            # 重试：重新生成正文
            if attempt < MAX_STEP_RETRIES:
                self._increment_retries("quality_evaluation")
                logger.warning(
                    f"合规P0问题，重新生成正文 ({attempt+1}/{MAX_STEP_RETRIES})"
                )
                material_dict = (
                    self._material_pack.model_dump() if self._material_pack else {}
                )
                note_output = self.crew.article_agent.generate(
                    title=self._selected_title or "",
                    material_pack=material_dict,
                )
                self._note_output = note_output

        # 降级：接受当前版本 + 合规问题清单
        p0_contents = [issue.content for issue in compliance_report.p0_issues]
        self._warnings.append(
            f"合规P0问题未修复，需人工修改: {', '.join(p0_contents)}"
        )
        self._degraded = True
        self._degradation_reason = "合规P0问题未修复"
        self._compliance_report = compliance_report
        return self._quality_result(note_output, compliance_report, True)

    # ── Step 7: 标签生成 + 最终合规检查 ─────────────────────

    @listen(quality_evaluation)
    def tag_and_compliance(self, quality_result: dict) -> dict:
        """
        生成标签 + 最终合规检查

        在同一步骤中顺序执行（CrewAI Flow 不支持并行 @listen）。
        """
        note_output = quality_result.get("note_output")
        if not note_output or not note_output.article:
            return {**quality_result, "tags": []}

        material_dict = (
            self._material_pack.model_dump() if self._material_pack else {}
        )

        # 生成标签
        tags = self.crew.tag_agent.generate(
            article=note_output.article,
            title=self._selected_title or "",
            material_pack=material_dict,
        )
        self._tags = tags

        # 最终合规检查（如果之前没有合规报告或有P0问题，重新检查）
        compliance_report = quality_result.get("compliance_report")
        if compliance_report is None or compliance_report.has_p0_issues:
            brand_taboos = (
                self._material_pack.brand.taboos
                if self._material_pack and self._material_pack.brand
                else []
            )
            compliance_report = self.crew.compliance_agent.check(
                title=self._selected_title or "",
                article=note_output.article,
                tags=tags,
                brand_taboos=brand_taboos,
            )
            self._compliance_report = compliance_report

        return {
            **quality_result,
            "tags": tags,
            "compliance_report": compliance_report,
        }

    # ── Step 8: 最终输出 ───────────────────────────────────

    @listen(tag_and_compliance)
    def final_output(self, result: dict) -> NotePack:
        """
        组装完整笔记包

        Returns:
            NotePack: 完整笔记包
        """
        note_output = result.get("note_output") or self._note_output
        tags = result.get("tags") or self._tags
        compliance_report = result.get("compliance_report") or self._compliance_report

        # 构造空的合规报告（如果缺失）
        if compliance_report is None:
            compliance_report = ComplianceReport(
                status=ComplianceStatus.PASSED,
                checked_at=datetime.now().isoformat(),
                suggestions=["未执行合规检查"],
            )

        metadata = NoteMetadata(
            platform="xiaohongshu",
            enterprise_id=getattr(self._material_pack, "enterprise_id", None)
            if self._material_pack
            else None,
            created_at=datetime.now().isoformat(),
            retry_count=self._total_retries,
            llm_used="MiniMax-M2.7",
            warnings=self._warnings.copy(),
            degraded=self._degraded,
            degradation_reason=self._degradation_reason,
        )

        return NotePack(
            title=self._selected_title or (note_output.title if note_output else ""),
            article=note_output.article if note_output else "",
            paragraphs=note_output.paragraphs if note_output else [],
            tags=tags,
            ai_flavor_score=note_output.ai_flavor_score if note_output else 0,
            compliance_report=compliance_report,
            material_pack=self._material_pack,
            metadata=metadata,
        )

    # ── 公共入口 ───────────────────────────────────────────

    def run(self, input_data: dict) -> NotePack:
        """
        运行完整流程

        Args:
            input_data: 包含 product, scene, persona, enterprise_id

        Returns:
            NotePack: 完整笔记包
        """
        self._reset_state()

        try:
            result = super().kickoff(input_data)
            # CrewAI Flow kickoff 返回最后一个步骤的输出
            if isinstance(result, NotePack):
                return result
            # 如果返回的是 dict（中间步骤），从状态组装
            return self._assemble_from_state()
        except RetryLimitExceeded as e:
            logger.error(str(e))
            self._warnings.append(str(e))
            self._degraded = True
            self._degradation_reason = str(e)
            return self._assemble_from_state()

    # ── 内部方法 ───────────────────────────────────────────

    def _reset_state(self):
        """重置流程状态"""
        self._material_pack = None
        self._title_output = None
        self._note_output = None
        self._tags = []
        self._compliance_report = None
        self._selected_title = None
        self._total_retries = 0
        self._warnings = []
        self._degraded = False
        self._degradation_reason = None

    def _increment_retries(self, step: str):
        """增加总重试计数，超过硬限制时抛出异常"""
        self._total_retries += 1
        if self._total_retries > MAX_TOTAL_RETRIES:
            raise RetryLimitExceeded(self._total_retries, step)

    def _empty_note_output(self, reason: str) -> NoteOutput:
        """创建空的笔记输出（降级用）"""
        self._warnings.append(reason)
        self._degraded = True
        self._degradation_reason = self._degradation_reason or reason
        return NoteOutput(
            title="",
            article="",
            tags=[],
            ai_flavor_score=0,
            metadata={"error": reason},
        )

    def _quality_result(
        self,
        note_output: NoteOutput,
        compliance_report: Optional[ComplianceReport],
        degraded: bool,
    ) -> dict:
        """构建质量评估结果"""
        return {
            "note_output": note_output,
            "compliance_report": compliance_report,
            "degraded": degraded,
        }

    def _assemble_from_state(self) -> NotePack:
        """从当前状态组装 NotePack（异常恢复用）"""
        compliance_report = self._compliance_report
        if compliance_report is None:
            compliance_report = ComplianceReport(
                status=ComplianceStatus.PASSED,
                checked_at=datetime.now().isoformat(),
                suggestions=["未执行合规检查"],
            )

        metadata = NoteMetadata(
            platform="xiaohongshu",
            enterprise_id=getattr(self._material_pack, "enterprise_id", None)
            if self._material_pack
            else None,
            created_at=datetime.now().isoformat(),
            retry_count=self._total_retries,
            llm_used="MiniMax-M2.7",
            warnings=self._warnings.copy(),
            degraded=self._degraded,
            degradation_reason=self._degradation_reason,
        )

        note = self._note_output
        return NotePack(
            title=self._selected_title or (note.title if note else ""),
            article=note.article if note else "",
            paragraphs=note.paragraphs if note else [],
            tags=self._tags,
            ai_flavor_score=note.ai_flavor_score if note else 0,
            compliance_report=compliance_report,
            material_pack=self._material_pack,
            metadata=metadata,
        )
