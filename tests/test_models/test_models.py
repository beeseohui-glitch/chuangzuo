"""
Model测试

Step 15: 测试模块开发
"""

import pytest
from datetime import datetime


class TestMaterialPack:
    """素材包模型测试"""

    def test_material_pack_creation(self):
        """测试素材包创建"""
        from models.material_pack import (
            MaterialPack,
            BrandInfo,
            ProductInfo,
            PersonaInfo,
            SceneInfo,
            ComplianceRules,
        )

        pack = MaterialPack(
            brand=BrandInfo(
                name="护肝宝",
                tone=["健康", "天然"],
                taboos=["最便宜", "第一"],
            ),
            product=ProductInfo(
                name="护肝片",
                selling_points=["保护肝脏", "天然成分"],
                ingredients=["水飞蓟", "B族维生素"],
            ),
            persona=PersonaInfo(
                profile="30-50岁白领",
                pain_points=["熬夜伤肝"],
            ),
            scene=[
                SceneInfo(
                    description="加班熬夜场景",
                    usage_method="每日一粒",
                )
            ],
            compliance=ComplianceRules(
                rules=["不允许绝对化用语"],
                forbidden_groups=["孕妇"],
            ),
        )

        assert pack.brand.name == "护肝宝"
        assert pack.product.name == "护肝片"
        assert len(pack.product.ingredients) == 2


class TestNoteOutput:
    """笔记输出模型测试"""

    def test_note_output_creation(self):
        """测试笔记输出创建"""
        from models.note_output import NoteOutput, TitleOption, Paragraph

        note = NoteOutput(
            title="测试标题",
            article="测试正文内容",
            tags=["标签1", "标签2"],
            ai_flavor_score=75,
            metadata={"topic": "测试"},
        )

        assert note.title == "测试标题"
        assert note.ai_flavor_score == 75

    def test_title_option(self):
        """测试标题选项"""
        from models.note_output import TitleOption

        title = TitleOption(
            title="测试标题",
            strategy="痛点切入",
            score=8,
            reason="理由清晰",
        )

        assert title.score == 8


class TestComplianceReport:
    """合规报告模型测试"""

    def test_compliance_report_creation(self):
        """测试合规报告创建"""
        from models.compliance_report import (
            ComplianceReport,
            ComplianceIssue,
            ComplianceStatus,
            ComplianceSeverity,
        )

        report = ComplianceReport(
            status=ComplianceStatus.PASSED,
            issues=[],
            suggestions=["建议1"],
        )

        assert report.status == ComplianceStatus.PASSED

    def test_compliance_issue(self):
        """测试合规问题"""
        from models.compliance_report import ComplianceIssue, ComplianceSeverity

        issue = ComplianceIssue(
            type="绝对化用语",
            severity=ComplianceSeverity.P0,
            description="使用了绝对化表述",
            position="标题",
            suggestion="修改为相对化表述",
        )

        assert issue.severity == ComplianceSeverity.P0
