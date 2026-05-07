"""
小红书创作 Flow 端到端测试

测试覆盖：
1. 完整流程 - 全链路 Happy Path
2. 素材校验失败 - 非关键失败继续流程
3. 标题重试 - 校验失败后重试
4. 正文重试 - AI味评分不达标重试
5. 正文降级 - AI味重试耗尽后降级
6. 合规重试 - P0问题重试正文
7. 合规降级 - P0重试耗尽后降级
8. 总重试硬限制 - 超过4次总重试
9. NotePack输出 - 结构完整性
10. 空标题降级 - 无标题时降级
11. 标签+合规 - 最终步骤两者都有
12. 元数据填充 - 所有metadata字段正确
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from models import (
    MaterialPack,
    BrandInfo,
    ProductInfo,
    PersonaInfo,
    SceneInfo,
    TitleOutput,
    TitleOption,
    NoteOutput,
    Paragraph,
    ComplianceReport,
    ComplianceStatus,
    ComplianceSeverity,
    ComplianceIssue,
    NotePack,
)

from flows.xiaohongshu_flow import (
    XiaohongshuFlow,
    RetryLimitExceeded,
    MAX_STEP_RETRIES,
    MAX_TOTAL_RETRIES,
    AI_FLAVOR_THRESHOLD,
)


# ── 共享 fixtures ─────────────────────────────────────────


@pytest.fixture
def material_pack():
    """完整素材包"""
    return MaterialPack(
        brand=BrandInfo(name="测试品牌", tone=["高端"], taboos=["便宜"]),
        product=ProductInfo(
            name="护肝片",
            selling_points=["天然成分", "高效吸收", "无添加"],
            ingredients=["水飞蓟", "姜黄素"],
        ),
        persona=PersonaInfo(
            profile="25-35岁都市白领",
            pain_points=["加班熬夜", "外卖不健康"],
        ),
        scene=[SceneInfo(description="加班后恢复", usage_method="睡前服用")],
    )


@pytest.fixture
def title_output():
    """合格标题输出（5个标题）"""
    return TitleOutput(
        titles=[
            TitleOption(title="加班党必看！这款护肝片救了我的肝", strategy="痛点", score=9, reason="精准痛点"),
            TitleOption(title="熬夜后的秘密武器，护肝片实测", strategy="悬念", score=8, reason="好奇心"),
            TitleOption(title="打工人护肝指南｜亲测一个月", strategy="攻略", score=8, reason="实用"),
            TitleOption(title="别再忽视你的肝！真实体验分享", strategy="警告", score=7, reason="紧迫感"),
            TitleOption(title="从熬夜到元气满满，我的护肝之路", strategy="故事", score=7, reason="共鸣"),
        ],
    )


@pytest.fixture
def good_note_output():
    """合格正文输出（AI味 >= 70）"""
    return NoteOutput(
        title="加班党必看！这款护肝片救了我的肝",
        article="加班到凌晨两点，回到家整个人都快散架了。说实话之前一直觉得保健品都是智商税，"
                "直到朋友推荐了这款护肝片。吃了一个月，最明显的感受就是早上起来不那么累了。"
                "当然每个人体质不同效果因人而异。反正我是回购了，姐妹们可以试试看！"
                "主要成分是水飞蓟和姜黄素，都是护肝的好东西。",
        paragraphs=[
            Paragraph(content="加班到凌晨两点", function="痛点引入"),
            Paragraph(content="朋友推荐了这款护肝片", function="产品发现"),
            Paragraph(content="吃了一个月最明显的感受", function="真实体验"),
            Paragraph(content="主要成分是水飞蓟", function="卖点展开"),
            Paragraph(content="姐妹们可以试试看", function="互动引导"),
        ],
        ai_flavor_score=75,
        platform="xiaohongshu",
    )


@pytest.fixture
def bad_note_output():
    """不合格正文输出（AI味 < 70）"""
    return NoteOutput(
        title="加班党必看！这款护肝片救了我的肝",
        article="本产品采用先进技术，有效护肝。经临床验证，效果显著。推荐使用。",
        paragraphs=[
            Paragraph(content="本产品采用先进技术", function="卖点展开"),
        ],
        ai_flavor_score=45,
        platform="xiaohongshu",
    )


@pytest.fixture
def passed_compliance():
    """通过的合规报告"""
    return ComplianceReport(
        status=ComplianceStatus.PASSED,
        checked_at=datetime.now().isoformat(),
        suggestions=["内容合规"],
    )


@pytest.fixture
def p0_compliance():
    """有P0问题的合规报告"""
    return ComplianceReport(
        status=ComplianceStatus.FAILED,
        p0_issues=[
            ComplianceIssue(
                severity=ComplianceSeverity.P0,
                content="最好",
                location="正文",
                suggestion="删除绝对化用语",
            ),
        ],
        checked_at=datetime.now().isoformat(),
    )


@pytest.fixture
def failed_compliance():
    """不通过的合规报告（无P0但状态为需修改）"""
    return ComplianceReport(
        status=ComplianceStatus.NEEDS_REVISION,
        p1_issues=[
            ComplianceIssue(
                severity=ComplianceSeverity.P1,
                content="某表述",
                location="正文",
                suggestion="建议修改",
            ),
        ],
        checked_at=datetime.now().isoformat(),
        suggestions=["建议优化措辞"],
    )


def _make_flow(
    material_pack=None,
    title_output=None,
    article_output=None,
    compliance_report=None,
    tags=None,
):
    """创建配置好mock的flow"""
    crew = MagicMock()

    # material_agent
    crew.material_agent.search.return_value = material_pack or MaterialPack(
        brand=BrandInfo(name="品牌", tone=[], taboos=[]),
        product=ProductInfo(name="产品", selling_points=["卖点1", "卖点2"]),
        persona=PersonaInfo(profile="人群"),
    )

    # title_agent
    crew.title_agent.generate.return_value = title_output or TitleOutput(
        titles=[
            TitleOption(title=f"标题{i}", strategy="策略", score=8, reason="理由")
            for i in range(5)
        ],
    )

    # article_agent
    crew.article_agent.generate.return_value = article_output or NoteOutput(
        title="标题0",
        article="这是一篇足够长的测试正文，" * 20,
        paragraphs=[
            Paragraph(content="段落1", function="痛点引入"),
            Paragraph(content="段落2", function="产品发现"),
            Paragraph(content="段落3", function="真实体验"),
        ],
        ai_flavor_score=75,
        platform="xiaohongshu",
    )

    # compliance_agent
    crew.compliance_agent.check.return_value = compliance_report or ComplianceReport(
        status=ComplianceStatus.PASSED,
        checked_at=datetime.now().isoformat(),
        suggestions=["合规"],
    )

    # tag_agent
    crew.tag_agent.generate.return_value = tags or [
        "#护肝", "#加班必备", "#保健品", "#健康生活",
        "#熬夜急救", "#打工人", "#养生", "#好物推荐",
    ]

    flow = XiaohongshuFlow(crew=crew)
    return flow


# ── 测试 ─────────────────────────────────────────────────


class TestXiaohongshuFlow:
    """小红书创作 Flow 测试"""

    def test_constants(self):
        """测试常量定义正确"""
        assert MAX_STEP_RETRIES == 2
        assert MAX_TOTAL_RETRIES == 4
        assert AI_FLAVOR_THRESHOLD == 70

    def test_full_flow_step_by_step(
        self, material_pack, title_output, good_note_output, passed_compliance
    ):
        """测试完整流程 - 逐步调用 Happy Path"""
        flow = _make_flow(
            material_pack=material_pack,
            title_output=title_output,
            article_output=good_note_output,
            compliance_report=passed_compliance,
        )

        # Step 1: 素材检索
        mp = flow.material_search({"product": "护肝片"})
        assert isinstance(mp, MaterialPack)
        assert mp.product.name == "护肝片"

        # Step 2: 校验素材包
        mp = flow.validate_material(mp)
        assert isinstance(mp, MaterialPack)

        # Step 3: 标题生成
        to = flow.title_generation(mp)
        assert isinstance(to, TitleOutput)
        assert len(to.titles) == 5

        # Step 4: 校验标题
        to = flow.validate_titles(to)
        assert isinstance(to, TitleOutput)

        # Step 5: 正文生成
        no = flow.article_generation(to)
        assert isinstance(no, NoteOutput)
        assert no.ai_flavor_score >= AI_FLAVOR_THRESHOLD

        # Step 6: 质量评估
        qr = flow.quality_evaluation(no)
        assert isinstance(qr, dict)
        assert qr["note_output"] is not None
        assert qr["compliance_report"] is not None
        assert qr["degraded"] is False

        # Step 7: 标签+合规
        result = flow.tag_and_compliance(qr)
        assert isinstance(result, dict)
        assert len(result["tags"]) == 8

        # Step 8: 最终输出
        pack = flow.final_output(result)
        assert isinstance(pack, NotePack)
        assert pack.title != ""
        assert pack.article != ""
        assert len(pack.tags) == 8
        assert pack.ai_flavor_score >= AI_FLAVOR_THRESHOLD
        assert pack.compliance_report is not None
        assert pack.metadata.platform == "xiaohongshu"

    def test_material_validation_failure_continues(self, material_pack):
        """素材校验失败时继续流程（非关键失败不阻断）"""
        # 缺少品牌和产品
        incomplete_pack = MaterialPack(
            brand=None,
            product=None,
            persona=PersonaInfo(profile="人群"),
        )
        flow = _make_flow(material_pack=incomplete_pack)

        mp = flow.material_search({"product": "护肝片"})
        mp = flow.validate_material(mp)

        # 应该有警告但流程继续
        assert len(flow._warnings) > 0
        assert isinstance(mp, MaterialPack)

    def test_title_retry_on_validation_failure(self, material_pack):
        """标题校验失败时重试"""
        # 第一次返回不足5个标题，第二次返回5个
        bad_titles = TitleOutput(
            titles=[
                TitleOption(title="标题1", strategy="策略", score=8, reason="理由"),
            ],
        )
        good_titles = TitleOutput(
            titles=[
                TitleOption(title=f"标题{i}", strategy="策略", score=8, reason="理由")
                for i in range(5)
            ],
        )

        flow = _make_flow(material_pack=material_pack)
        flow.crew.title_agent.generate.side_effect = [bad_titles, good_titles]

        mp = flow.material_search({"product": "护肝片"})
        mp = flow.validate_material(mp)
        to = flow.title_generation(mp)

        assert len(to.titles) == 5
        assert flow._total_retries == 1  # 重试了1次

    def test_title_degrade_after_max_retries(self, material_pack):
        """标题重试耗尽后降级"""
        # 始终返回不足5个标题
        bad_titles = TitleOutput(
            titles=[
                TitleOption(title="标题1", strategy="策略", score=8, reason="理由"),
            ],
        )

        flow = _make_flow(material_pack=material_pack)
        flow.crew.title_agent.generate.return_value = bad_titles

        mp = flow.material_search({"product": "护肝片"})
        mp = flow.validate_material(mp)
        to = flow.title_generation(mp)

        # 降级：接受当前标题 + 警告
        assert flow._degraded is True
        assert any("建议人工优化" in w for w in flow._warnings)
        assert len(to.titles) == 1  # 仍然返回了标题

    def test_article_retry_on_low_ai_score(
        self, material_pack, title_output, good_note_output, bad_note_output
    ):
        """正文AI味不达标时重试"""
        flow = _make_flow(material_pack=material_pack, title_output=title_output)
        flow.crew.article_agent.generate.side_effect = [
            bad_note_output,   # AI味 45
            good_note_output,  # AI味 75
        ]

        mp = flow.material_search({"product": "护肝片"})
        flow._material_pack = mp
        to = flow.title_generation(mp)
        no = flow.article_generation(to)

        assert no.ai_flavor_score >= AI_FLAVOR_THRESHOLD
        assert flow._total_retries == 1

    def test_article_degrade_after_max_retries(
        self, material_pack, title_output, bad_note_output
    ):
        """正文AI味重试耗尽后降级"""
        flow = _make_flow(material_pack=material_pack, title_output=title_output)
        # 始终返回低分
        flow.crew.article_agent.generate.return_value = bad_note_output

        mp = flow.material_search({"product": "护肝片"})
        flow._material_pack = mp
        to = flow.title_generation(mp)
        no = flow.article_generation(to)

        assert flow._degraded is True
        assert any("建议人工润色" in w for w in flow._warnings)
        assert no.ai_flavor_score < AI_FLAVOR_THRESHOLD  # 接受了低分版本

    def test_compliance_p0_retry(
        self, material_pack, title_output, good_note_output,
        p0_compliance, passed_compliance
    ):
        """合规P0问题时重试正文生成"""
        flow = _make_flow(
            material_pack=material_pack,
            title_output=title_output,
            compliance_report=p0_compliance,
        )
        # 第二次合规检查通过
        flow.crew.compliance_agent.check.side_effect = [
            p0_compliance,
            passed_compliance,
        ]

        mp = flow.material_search({"product": "护肝片"})
        flow._material_pack = mp
        to = flow.title_generation(mp)
        no = flow.article_generation(to)
        qr = flow.quality_evaluation(no)

        assert qr["compliance_report"].status == ComplianceStatus.PASSED
        assert not qr["compliance_report"].has_p0_issues
        assert flow._total_retries == 1

    def test_compliance_degrade_after_max_retries(
        self, material_pack, title_output, good_note_output, p0_compliance
    ):
        """合规P0重试耗尽后降级"""
        flow = _make_flow(
            material_pack=material_pack,
            title_output=title_output,
            compliance_report=p0_compliance,
        )
        # 始终返回P0问题
        flow.crew.compliance_agent.check.return_value = p0_compliance

        mp = flow.material_search({"product": "护肝片"})
        flow._material_pack = mp
        to = flow.title_generation(mp)
        no = flow.article_generation(to)
        qr = flow.quality_evaluation(no)

        assert flow._degraded is True
        assert any("需人工修改" in w for w in flow._warnings)
        assert qr["degraded"] is True

    def test_total_retry_hard_limit(
        self, material_pack, title_output, bad_note_output, p0_compliance
    ):
        """总重试次数达到硬限制4次后降级"""
        flow = _make_flow(
            material_pack=material_pack,
            title_output=title_output,
            compliance_report=p0_compliance,
        )
        flow.crew.article_agent.generate.return_value = bad_note_output
        flow.crew.compliance_agent.check.return_value = p0_compliance

        mp = flow.material_search({"product": "护肝片"})
        flow._material_pack = mp
        to = flow.title_generation(mp)

        # 正文生成会重试2次（AI味不够），消耗2次总重试
        no = flow.article_generation(to)
        assert flow._total_retries == 2

        # 质量评估会重试2次（P0问题），消耗另外2次总重试
        # 总计4次，恰好等于硬限制，循环结束后正常降级
        qr = flow.quality_evaluation(no)
        assert flow._total_retries == MAX_TOTAL_RETRIES
        assert qr["degraded"] is True
        assert flow._degraded is True

    def test_final_output_is_note_pack(
        self, material_pack, title_output, good_note_output, passed_compliance
    ):
        """最终输出是 NotePack 类型"""
        flow = _make_flow(
            material_pack=material_pack,
            title_output=title_output,
            article_output=good_note_output,
            compliance_report=passed_compliance,
        )

        mp = flow.material_search({"product": "护肝片"})
        flow._material_pack = mp
        to = flow.title_generation(mp)
        no = flow.article_generation(to)
        qr = flow.quality_evaluation(no)
        result = flow.tag_and_compliance(qr)
        pack = flow.final_output(result)

        assert isinstance(pack, NotePack)
        assert pack.title != ""
        assert pack.article != ""
        assert len(pack.tags) >= 0
        assert 0 <= pack.ai_flavor_score <= 100
        assert pack.compliance_report is not None
        assert pack.material_pack is not None
        assert isinstance(pack.metadata.created_at, str)

    def test_empty_title_degradation(self, material_pack):
        """无标题时降级"""
        empty_titles = TitleOutput(titles=[])
        flow = _make_flow(material_pack=material_pack, title_output=empty_titles)

        mp = flow.material_search({"product": "护肝片"})
        flow._material_pack = mp
        to = flow.title_generation(mp)
        to = flow.validate_titles(to)

        assert flow._degraded is True
        # title_generation adds "建议人工优化", validate_titles adds "未生成任何标题"
        assert any("建议人工优化" in w for w in flow._warnings)
        assert any("未生成任何标题" in w for w in flow._warnings)

    def test_tag_and_compliance_both_present(
        self, material_pack, title_output, good_note_output, passed_compliance
    ):
        """标签和合规报告都在最终步骤中"""
        flow = _make_flow(
            material_pack=material_pack,
            title_output=title_output,
            article_output=good_note_output,
            compliance_report=passed_compliance,
        )

        mp = flow.material_search({"product": "护肝片"})
        flow._material_pack = mp
        to = flow.title_generation(mp)
        no = flow.article_generation(to)
        qr = flow.quality_evaluation(no)
        result = flow.tag_and_compliance(qr)

        assert "tags" in result
        assert "compliance_report" in result
        assert len(result["tags"]) == 8
        assert result["compliance_report"].status == ComplianceStatus.PASSED

    def test_metadata_populated(
        self, material_pack, title_output, good_note_output, passed_compliance
    ):
        """元数据字段正确填充"""
        flow = _make_flow(
            material_pack=material_pack,
            title_output=title_output,
            article_output=good_note_output,
            compliance_report=passed_compliance,
        )

        mp = flow.material_search({"product": "护肝片"})
        flow._material_pack = mp
        to = flow.title_generation(mp)
        no = flow.article_generation(to)
        qr = flow.quality_evaluation(no)
        result = flow.tag_and_compliance(qr)
        pack = flow.final_output(result)

        assert pack.metadata.platform == "xiaohongshu"
        assert pack.metadata.retry_count >= 0
        assert pack.metadata.llm_used == "mimo-v2.5-pro"
        assert isinstance(pack.metadata.warnings, list)
        assert isinstance(pack.metadata.degraded, bool)
        assert isinstance(pack.metadata.created_at, str)

    def test_retry_limit_exceeded_exception(self):
        """RetryLimitExceeded 异常属性"""
        exc = RetryLimitExceeded(5, "test_step")
        assert exc.total_retries == 5
        assert exc.step == "test_step"
        assert "5" in str(exc)
        assert "test_step" in str(exc)

    def test_increment_retries_normal(self):
        """正常重试计数递增"""
        flow = _make_flow()
        assert flow._total_retries == 0
        flow._increment_retries("step1")
        assert flow._total_retries == 1
        flow._increment_retries("step2")
        assert flow._total_retries == 2

    def test_increment_retries_exceeds_limit(self):
        """重试计数超过限制时抛异常"""
        flow = _make_flow()
        for i in range(MAX_TOTAL_RETRIES):
            flow._increment_retries(f"step{i}")

        with pytest.raises(RetryLimitExceeded):
            flow._increment_retries("step_over")

    def test_empty_note_output_degradation(self, title_output):
        """无正文时降级"""
        flow = _make_flow()
        no = flow._empty_note_output("测试降级")

        assert no.article == ""
        assert no.ai_flavor_score == 0
        assert flow._degraded is True
        assert any("测试降级" in w for w in flow._warnings)

    def test_p1_p2_issues_do_not_block(
        self, material_pack, title_output, good_note_output, failed_compliance
    ):
        """P1/P2问题不阻断流程"""
        flow = _make_flow(
            material_pack=material_pack,
            title_output=title_output,
            article_output=good_note_output,
            compliance_report=failed_compliance,
        )

        mp = flow.material_search({"product": "护肝片"})
        flow._material_pack = mp
        to = flow.title_generation(mp)
        no = flow.article_generation(to)
        qr = flow.quality_evaluation(no)

        # P1问题不应触发重试
        assert qr["degraded"] is False
        assert qr["compliance_report"].status == ComplianceStatus.NEEDS_REVISION

    def test_reset_state(self, material_pack, title_output):
        """状态重置"""
        flow = _make_flow(material_pack=material_pack, title_output=title_output)

        # 修改状态
        flow._total_retries = 3
        flow._warnings = ["warning1"]
        flow._degraded = True

        # 重置
        flow._reset_state()

        assert flow._total_retries == 0
        assert flow._warnings == []
        assert flow._degraded is False
        assert flow._material_pack is None
        assert flow._title_output is None
        assert flow._note_output is None
        assert flow._tags == []
        assert flow._compliance_report is None
        assert flow._selected_title is None

    def test_best_article_selected_on_degradation(
        self, material_pack, title_output
    ):
        """降级时选择AI味评分最高的版本"""
        low_score = NoteOutput(
            title="标题0",
            article="低分文章",
            paragraphs=[Paragraph(content="段", function="痛点引入")],
            ai_flavor_score=40,
            platform="xiaohongshu",
        )
        mid_score = NoteOutput(
            title="标题0",
            article="中分文章" * 10,
            paragraphs=[
                Paragraph(content="段1", function="痛点引入"),
                Paragraph(content="段2", function="产品发现"),
                Paragraph(content="段3", function="真实体验"),
            ],
            ai_flavor_score=60,
            platform="xiaohongshu",
        )

        flow = _make_flow(
            material_pack=material_pack,
            title_output=title_output,
        )
        flow.crew.article_agent.generate.side_effect = [
            low_score, mid_score, low_score
        ]

        mp = flow.material_search({"product": "护肝片"})
        flow._material_pack = mp
        to = flow.title_generation(mp)
        no = flow.article_generation(to)

        # 应该选择60分的版本（最佳）
        assert no.ai_flavor_score == 60
        assert no.article == "中分文章" * 10
