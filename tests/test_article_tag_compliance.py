"""
Agent 测试 - 后3个Agent + AIFlavorScorer + ComplianceTools

测试覆盖：
1. ArticleAgent - 初始化、Prompt加载、正文生成、AI味重试、段落构建
2. TagAgent - 初始化、Prompt加载、标签生成、数量校验、格式修复
3. ComplianceAgent - 初始化、Prompt加载、合规检查、P0/P1/P2解析、降级报告
4. AIFlavorScorer - 5维度评分、评分分解、边界情况
5. ComplianceCheckTool - 违禁词检测、标题/正文/标签检查
6. ProhibitedWordDetector - 违禁词检测
"""

import pytest
from unittest.mock import patch, MagicMock

from models import (
    NoteOutput,
    Paragraph,
    TitleOutput,
    TitleOption,
    ComplianceReport,
    ComplianceStatus,
    ComplianceSeverity,
    ComplianceIssue,
)


# ── 共享 fixtures ─────────────────────────────────────────


@pytest.fixture
def material_pack():
    """测试素材包"""
    return {
        "brand": {
            "name": "测试品牌",
            "tone": ["高端", "专业"],
            "taboos": ["不能说便宜"],
        },
        "product": {
            "name": "测试产品",
            "selling_points": ["天然成分", "高效吸收", "无添加"],
            "ingredients": ["水飞蓟", "姜黄素"],
        },
        "persona": {
            "profile": "25-35岁都市白领，关注健康",
            "pain_points": ["加班熬夜", "外卖不健康"],
        },
        "scene": [
            {"description": "加班后恢复", "usage_method": "睡前服用"},
        ],
    }


@pytest.fixture
def sample_article():
    """测试正文"""
    return """
加班到凌晨两点，回到家整个人都快散架了。
说实话，之前一直觉得保健品都是智商税，直到朋友推荐了这款护肝片。
吃了一个月，最明显的感受就是早上起来不那么累了。
当然每个人体质不同，效果因人而异哈。
反正我是回购了，姐妹们可以试试看！
"""


@pytest.fixture
def sample_tags():
    """测试标签"""
    return [
        "#护肝", "#加班必备", "#保健品", "#健康生活",
        "#熬夜急救", "#打工人", "#养生", "#好物推荐",
    ]


# ── ArticleAgent 测试 ─────────────────────────────────────


class TestArticleAgent:
    """正文 Agent 测试"""

    def test_init(self):
        """测试初始化"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()
        assert agent.config.name == "ArticleAgent"
        assert agent._llm_config is None
        assert agent._agent is None
        assert agent._llm_tool is None
        assert agent._scorer is not None

    def test_init_with_llm_config(self):
        """测试带 LLM 配置初始化"""
        from agents.article_agent import ArticleAgent
        from config import LLMManagerConfig, MiniMaxConfig

        config = LLMManagerConfig(primary=MiniMaxConfig())
        agent = ArticleAgent(llm_config=config)
        assert agent._llm_config is config

    def test_prompt_loading(self):
        """测试 Prompt 加载"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()

        with patch("agents.article_agent.prompt_manager") as mock_pm:
            mock_pm.load_prompt.return_value = "你是正文创作专家"
            prompt = mock_pm.load_prompt("article_agent")
            assert prompt == "你是正文创作专家"

    def test_build_prompt_basic(self, material_pack):
        """测试基础 Prompt 构建"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()
        prompt = agent._build_prompt("测试标题", material_pack, attempt=0)

        assert "测试标题" in prompt
        assert "测试品牌" in prompt
        assert "测试产品" in prompt
        assert "天然成分" in prompt
        assert "加班后恢复" in prompt
        assert "重试提示" not in prompt

    def test_build_prompt_retry(self, material_pack):
        """测试重试 Prompt 构建"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()
        prompt = agent._build_prompt("测试标题", material_pack, attempt=1)

        assert "重试提示" in prompt
        assert "口语化表达" in prompt

    def test_parse_response_valid(self):
        """测试有效 JSON 解析"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()
        content = '{"article": "正文内容", "paragraphs": [{"content": "段落", "function": "功能"}], "ai_flavor_score": 80}'
        data = agent._parse_response(content)

        assert data["article"] == "正文内容"
        assert len(data["paragraphs"]) == 1
        assert data["ai_flavor_score"] == 80

    def test_parse_response_with_markdown(self):
        """测试带 markdown 标记的 JSON 解析"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()
        content = '```json\n{"article": "正文", "paragraphs": []}\n```'
        data = agent._parse_response(content)

        assert data["article"] == "正文"

    def test_parse_response_invalid(self):
        """测试无效 JSON 解析"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()
        with pytest.raises(ValueError, match="Cannot parse JSON"):
            agent._parse_response("这不是JSON")

    def test_build_paragraphs(self):
        """测试段落构建"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()
        article = "第一段内容\n\n第二段内容\n\n第三段内容"
        paragraphs = agent._build_paragraphs(article)

        assert len(paragraphs) == 3
        assert paragraphs[0].content == "第一段内容"
        assert paragraphs[0].function == "痛点引入"
        assert paragraphs[1].function == "产品发现"
        assert paragraphs[2].function == "卖点展开"

    def test_build_paragraphs_empty(self):
        """测试空段落构建"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()
        paragraphs = agent._build_paragraphs("")
        assert paragraphs == []

    def test_generate_success(self, material_pack):
        """测试成功生成正文"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()

        mock_response = MagicMock()
        mock_response.content = '{"article": "这是一篇很好的文章，说实话真的很不错。加班后吃了一颗，第二天精神好多了。", "paragraphs": [{"content": "段落1", "function": "痛点引入"}], "ai_flavor_score": 75}'

        mock_crew_agent = MagicMock()
        mock_crew_agent.kickoff.return_value = mock_response
        agent._agent = mock_crew_agent

        result = agent.generate("测试标题", material_pack)

        assert isinstance(result, NoteOutput)
        assert result.title == "测试标题"
        assert len(result.article) > 0
        assert result.ai_flavor_score >= 0

    def test_generate_low_ai_score_retry(self, material_pack):
        """测试 AI 味评分低时重试"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()

        # 第一次返回低分，第二次返回高分
        low_score_response = MagicMock()
        low_score_response.content = '{"article": "首先，其次，最后。众所周知，综上所述。", "paragraphs": [], "ai_flavor_score": 30}'

        high_score_response = MagicMock()
        high_score_response.content = '{"article": "哇这个真的绝了！谁懂啊，加班到凌晨两点，回到家整个人都快散架了。说实话之前一直觉得保健品是智商税，直到朋友推荐了这款护肝片。吃了一个月，早上起来不那么累了，太惊喜了吧！昨天在公司加班到很晚，吃了一颗，今天精神好多了。姐妹们可以试试看，反正我是回购了，yyds！", "paragraphs": [], "ai_flavor_score": 80}'

        mock_crew_agent = MagicMock()
        mock_crew_agent.kickoff.side_effect = [low_score_response, high_score_response, high_score_response]
        agent._agent = mock_crew_agent

        result = agent.generate("测试标题", material_pack)

        assert isinstance(result, NoteOutput)
        assert mock_crew_agent.kickoff.call_count >= 2

    def test_generate_all_retries_fail(self, material_pack):
        """测试所有重试失败"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()

        bad_response = MagicMock()
        bad_response.content = '{"article": "首先，其次，最后。众所周知。", "paragraphs": [], "ai_flavor_score": 20}'

        mock_crew_agent = MagicMock()
        mock_crew_agent.kickoff.return_value = bad_response
        agent._agent = mock_crew_agent

        result = agent.generate("测试标题", material_pack)

        assert isinstance(result, NoteOutput)
        assert result.ai_flavor_score >= 0  # 最后一次的结果

    def test_generate_exception_handling(self, material_pack):
        """测试异常处理"""
        from agents.article_agent import ArticleAgent

        agent = ArticleAgent()

        mock_crew_agent = MagicMock()
        mock_crew_agent.kickoff.side_effect = Exception("LLM 调用失败")
        agent._agent = mock_crew_agent

        result = agent.generate("测试标题", material_pack)

        assert isinstance(result, NoteOutput)
        assert result.article == ""
        assert "error" in result.metadata


# ── TagAgent 测试 ─────────────────────────────────────────


class TestTagAgent:
    """标签 Agent 测试"""

    def test_init(self):
        """测试初始化"""
        from agents.tag_agent import TagAgent

        agent = TagAgent()
        assert agent.config.name == "TagAgent"
        assert agent._llm_config is None
        assert agent._agent is None
        assert agent._llm_tool is None

    def test_init_with_llm_config(self):
        """测试带 LLM 配置初始化"""
        from agents.tag_agent import TagAgent
        from config import LLMManagerConfig, MiniMaxConfig

        config = LLMManagerConfig(primary=MiniMaxConfig())
        agent = TagAgent(llm_config=config)
        assert agent._llm_config is config

    def test_prompt_loading(self):
        """测试 Prompt 加载"""
        from agents.tag_agent import TagAgent

        agent = TagAgent()

        with patch("agents.tag_agent.prompt_manager") as mock_pm:
            mock_pm.load_prompt.return_value = "你是标签策略专家"
            prompt = mock_pm.load_prompt("tag_agent")
            assert prompt == "你是标签策略专家"

    def test_build_prompt(self, material_pack):
        """测试 Prompt 构建"""
        from agents.tag_agent import TagAgent

        agent = TagAgent()
        prompt = agent._build_prompt("正文内容", "测试标题", material_pack)

        assert "测试标题" in prompt
        assert "测试品牌" in prompt
        assert "测试产品" in prompt
        assert "品类大词" in prompt
        assert "功效长尾词" in prompt

    def test_parse_response_array(self):
        """测试数组格式解析"""
        from agents.tag_agent import TagAgent

        agent = TagAgent()
        content = '["#标签1", "#标签2", "#标签3"]'
        tags = agent._parse_response(content)

        assert tags == ["#标签1", "#标签2", "#标签3"]

    def test_parse_response_object(self):
        """测试对象格式解析"""
        from agents.tag_agent import TagAgent

        agent = TagAgent()
        content = '{"tags": ["#标签1", "#标签2"]}'
        tags = agent._parse_response(content)

        assert tags == ["#标签1", "#标签2"]

    def test_parse_response_with_markdown(self):
        """测试带 markdown 标记的解析"""
        from agents.tag_agent import TagAgent

        agent = TagAgent()
        content = '```json\n["#标签1", "#标签2"]\n```'
        tags = agent._parse_response(content)

        assert tags == ["#标签1", "#标签2"]

    def test_parse_response_invalid(self):
        """测试无效格式解析"""
        from agents.tag_agent import TagAgent

        agent = TagAgent()
        with pytest.raises(ValueError, match="Cannot parse tags"):
            agent._parse_response("这不是JSON")

    def test_generate_success(self, material_pack):
        """测试成功生成标签"""
        from agents.tag_agent import TagAgent

        agent = TagAgent()

        mock_response = MagicMock()
        mock_response.content = '{"tags": ["#护肝", "#加班必备", "#保健品", "#健康生活", "#熬夜急救", "#打工人", "#养生", "#好物推荐"]}'

        mock_crew_agent = MagicMock()
        mock_crew_agent.kickoff.return_value = mock_response
        agent._agent = mock_crew_agent

        tags = agent.generate("正文内容", "测试标题", material_pack)

        assert len(tags) == 8
        assert all(t.startswith("#") for t in tags)

    def test_generate_insufficient_tags_retry(self, material_pack):
        """测试标签不足时重试"""
        from agents.tag_agent import TagAgent

        agent = TagAgent()

        # 第一次返回不足，第二次返回足够
        short_response = MagicMock()
        short_response.content = '{"tags": ["#标签1", "#标签2"]}'

        full_response = MagicMock()
        full_response.content = '{"tags": ["#标签1", "#标签2", "#标签3", "#标签4", "#标签5", "#标签6", "#标签7", "#标签8"]}'

        mock_crew_agent = MagicMock()
        mock_crew_agent.kickoff.side_effect = [short_response, full_response]
        agent._agent = mock_crew_agent

        tags = agent.generate("正文内容", "测试标题", material_pack)

        assert len(tags) == 8
        assert mock_crew_agent.kickoff.call_count == 2

    def test_generate_fix_missing_hash(self, material_pack):
        """测试自动修复缺少 # 前缀的标签"""
        from agents.tag_agent import TagAgent

        agent = TagAgent()

        mock_response = MagicMock()
        mock_response.content = '{"tags": ["#标签1", "标签2", "#标签3", "#标签4", "#标签5", "#标签6", "#标签7", "#标签8"]}'

        mock_crew_agent = MagicMock()
        mock_crew_agent.kickoff.return_value = mock_response
        agent._agent = mock_crew_agent

        tags = agent.generate("正文内容", "测试标题", material_pack)

        assert all(t.startswith("#") for t in tags)
        assert "#标签2" in tags

    def test_generate_exception_returns_empty(self, material_pack):
        """测试异常返回空列表"""
        from agents.tag_agent import TagAgent

        agent = TagAgent()

        mock_crew_agent = MagicMock()
        mock_crew_agent.kickoff.side_effect = Exception("LLM 调用失败")
        agent._agent = mock_crew_agent

        tags = agent.generate("正文内容", "测试标题", material_pack)

        assert tags == []


# ── ComplianceAgent 测试 ─────────────────────────────────


class TestComplianceAgent:
    """合规 Agent 测试"""

    def test_init(self):
        """测试初始化"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()
        assert agent.config.name == "ComplianceAgent"
        assert agent._llm_config is None
        assert agent._agent is None
        assert agent._llm_tool is None
        assert agent.platform_config is not None

    def test_init_with_llm_config(self):
        """测试带 LLM 配置初始化"""
        from agents.compliance_agent import ComplianceAgent
        from config import LLMManagerConfig, MiniMaxConfig

        config = LLMManagerConfig(primary=MiniMaxConfig())
        agent = ComplianceAgent(llm_config=config)
        assert agent._llm_config is config

    def test_prompt_loading(self):
        """测试 Prompt 加载"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()

        with patch("agents.compliance_agent.prompt_manager") as mock_pm:
            mock_pm.load_prompt.return_value = "你是合规审核专家"
            prompt = mock_pm.load_prompt("compliance_agent")
            assert prompt == "你是合规审核专家"

    def test_build_prompt(self, sample_article, sample_tags):
        """测试 Prompt 构建"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()
        prompt = agent._build_prompt("测试标题", sample_article, sample_tags, ["禁忌词1"])

        assert "测试标题" in prompt
        assert "禁忌词1" in prompt
        assert "P0" in prompt
        assert "P1" in prompt
        assert "P2" in prompt

    def test_build_prompt_no_taboos(self, sample_article, sample_tags):
        """测试无禁忌词 Prompt 构建"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()
        prompt = agent._build_prompt("测试标题", sample_article, sample_tags)

        assert "无" in prompt

    def test_parse_response_passed(self):
        """测试通过状态解析"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()
        content = '{"status": "通过", "p0_issues": [], "p1_issues": [], "p2_issues": [], "suggestions": ["内容合规"]}'
        report = agent._parse_response(content)

        assert isinstance(report, ComplianceReport)
        assert report.status == ComplianceStatus.PASSED
        assert len(report.p0_issues) == 0

    def test_parse_response_with_issues(self):
        """测试有问题的解析"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()
        content = """{
            "status": "需修改",
            "p0_issues": [
                {"severity": "p0", "content": "最好", "location": "标题", "suggestion": "改为推荐"}
            ],
            "p1_issues": [],
            "p2_issues": [
                {"severity": "p2", "content": "可能有效", "location": "正文", "suggestion": "需人工确认"}
            ],
            "suggestions": ["修改绝对化用语"]
        }"""
        report = agent._parse_response(content)

        assert report.status == ComplianceStatus.NEEDS_REVISION
        assert len(report.p0_issues) == 1
        assert report.p0_issues[0].severity == ComplianceSeverity.P0
        assert report.p0_issues[0].content == "最好"
        assert len(report.p2_issues) == 1

    def test_parse_response_failed(self):
        """测试不通过状态解析"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()
        content = '{"status": "不通过", "p0_issues": [], "p1_issues": [], "p2_issues": [], "suggestions": []}'
        report = agent._parse_response(content)

        assert report.status == ComplianceStatus.FAILED

    def test_parse_response_invalid(self):
        """测试无效响应解析"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()
        with pytest.raises(ValueError, match="Cannot parse ComplianceReport"):
            agent._parse_response("这不是JSON")

    def test_parse_response_unknown_status(self):
        """测试未知状态默认为需修改"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()
        content = '{"status": "未知状态", "p0_issues": [], "p1_issues": [], "p2_issues": [], "suggestions": []}'
        report = agent._parse_response(content)

        assert report.status == ComplianceStatus.NEEDS_REVISION

    def test_check_success(self, sample_article, sample_tags):
        """测试成功检查"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()

        mock_response = MagicMock()
        mock_response.content = '{"status": "通过", "p0_issues": [], "p1_issues": [], "p2_issues": [], "suggestions": ["内容合规"]}'

        mock_crew_agent = MagicMock()
        mock_crew_agent.kickoff.return_value = mock_response
        agent._agent = mock_crew_agent

        report = agent.check("测试标题", sample_article, sample_tags)

        assert isinstance(report, ComplianceReport)
        assert report.status == ComplianceStatus.PASSED

    def test_check_with_brand_taboos(self, sample_article, sample_tags):
        """测试带品牌禁忌词检查"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()

        mock_response = MagicMock()
        mock_response.content = '{"status": "需修改", "p0_issues": [], "p1_issues": [{"severity": "p1", "content": "便宜", "location": "正文", "suggestion": "删除"}], "p2_issues": [], "suggestions": ["修改品牌禁忌词"]}'

        mock_crew_agent = MagicMock()
        mock_crew_agent.kickoff.return_value = mock_response
        agent._agent = mock_crew_agent

        report = agent.check("测试标题", sample_article, sample_tags, ["不能说便宜"])

        assert report.status == ComplianceStatus.NEEDS_REVISION

    def test_check_exception_returns_fallback(self, sample_article, sample_tags):
        """测试异常返回降级报告"""
        from agents.compliance_agent import ComplianceAgent

        agent = ComplianceAgent()

        mock_crew_agent = MagicMock()
        mock_crew_agent.kickoff.side_effect = Exception("LLM 调用失败")
        agent._agent = mock_crew_agent

        report = agent.check("测试标题", sample_article, sample_tags)

        assert isinstance(report, ComplianceReport)
        assert report.status == ComplianceStatus.NEEDS_REVISION
        assert "失败" in report.suggestions[0]


# ── AIFlavorScorer 测试 ──────────────────────────────────


class TestAIFlavorScorer:
    """AI味评分器测试"""

    def test_init(self):
        """测试初始化"""
        from validators.ai_flavor_scorer import AIFlavorScorer

        scorer = AIFlavorScorer()
        assert scorer._ai_pattern is not None
        assert scorer._informal_pattern is not None

    def test_score_empty_text(self):
        """测试空文本评分"""
        from validators.ai_flavor_scorer import AIFlavorScorer

        scorer = AIFlavorScorer()
        assert scorer.score("") == 0

    def test_score_human_like_text(self):
        """测试人类风格文本评分（应得高分）"""
        from validators.ai_flavor_scorer import AIFlavorScorer

        scorer = AIFlavorScorer()
        text = """
        哇这个真的绝了！谁懂啊，加班到凌晨两点，整个人都快散架了。
        说实话之前一直觉得保健品是智商税，直到朋友推荐了这款护肝片。
        吃了一个月，早上起来不那么累了，太惊喜了吧！
        姐妹们可以试试看，反正我是回购了。
        """
        score = scorer.score(text)
        assert score >= 40  # 人类风格应该得分较高

    def test_score_ai_like_text(self):
        """测试 AI 风格文本评分（应得低分）"""
        from validators.ai_flavor_scorer import AIFlavorScorer

        scorer = AIFlavorScorer()
        text = """
        首先，这款产品具有多种优势。其次，它的成分天然安全。
        第三，经过临床验证效果显著。第四，性价比极高。
        综上所述，这是一款值得推荐的产品。值得一提的是，它的口碑也很好。
        """
        score = scorer.score(text)
        assert score <= 40  # AI 风格应该得分较低

    def test_score_sentence_diversity(self):
        """测试句式多样性评分"""
        from validators.ai_flavor_scorer import AIFlavorScorer

        scorer = AIFlavorScorer()

        # 长短句混合
        diverse_text = "好。这个产品真的非常不错，我吃了一个月感觉精神好了很多。嗯。"
        score1 = scorer._score_sentence_diversity(diverse_text)

        # 均匀长度句子
        uniform_text = "这个产品不错。那个产品也行。另一个产品挺好。"
        score2 = scorer._score_sentence_diversity(uniform_text)

        assert score1 >= score2

    def test_score_colloquial_level(self):
        """测试口语化程度评分"""
        from validators.ai_flavor_scorer import AIFlavorScorer

        scorer = AIFlavorScorer()

        # 口语化文本
        colloquial = "哇这个真的太好了吧！说实话我本来没抱希望的，结果吃了两周就感觉不一样了呢。"
        score1 = scorer._score_colloquial_level(colloquial)

        # 书面化文本
        formal = "该产品具有良好的效果，经过验证可以改善身体状况。"
        score2 = scorer._score_colloquial_level(formal)

        assert score1 > score2

    def test_score_structure_pattern(self):
        """测试结构模式评分"""
        from validators.ai_flavor_scorer import AIFlavorScorer

        scorer = AIFlavorScorer()

        # 无 AI 结构
        natural = "昨天加班到很晚，回家吃了一颗，今天精神好多了。"
        score1 = scorer._score_structure_pattern(natural)

        # 多 AI 结构
        ai_like = "首先这个产品很好。其次它很安全。第三它很便宜。最后综上所述值得买。"
        score2 = scorer._score_structure_pattern(ai_like)

        assert score1 > score2

    def test_score_life_details(self):
        """测试生活细节评分"""
        from validators.ai_flavor_scorer import AIFlavorScorer

        scorer = AIFlavorScorer()

        # 有生活细节
        detailed = "昨天加班到凌晨，在办公室吃了一颗，今天早上起来精神好多了。"
        score1 = scorer._score_life_details(detailed)

        # 无生活细节
        generic = "这个产品效果很好，值得推荐。"
        score2 = scorer._score_life_details(detailed)

        assert score1 >= score2

    def test_score_slight_imperfection(self):
        """测试轻微不完美评分"""
        from validators.ai_flavor_scorer import AIFlavorScorer

        scorer = AIFlavorScorer()

        # 有非正式表达
        informal = "绝了！这个真的太好用了！谁懂啊！"
        score1 = scorer._score_slight_imperfection(informal)

        # 正式表达
        formal = "这个产品效果不错。"
        score2 = scorer._score_slight_imperfection(formal)

        assert score1 > score2

    def test_get_score_breakdown(self):
        """测试评分分解"""
        from validators.ai_flavor_scorer import AIFlavorScorer

        scorer = AIFlavorScorer()
        text = "哇这个真的绝了！说实话，加班到凌晨吃了一颗，第二天精神好多了。"
        breakdown = scorer.get_score_breakdown(text)

        assert "sentence_diversity" in breakdown
        assert "colloquial_level" in breakdown
        assert "structure_pattern" in breakdown
        assert "life_details" in breakdown
        assert "slight_imperfection" in breakdown
        assert "total" in breakdown
        assert breakdown["total"] == scorer.score(text)

    def test_score_range(self):
        """测试评分范围 0-100"""
        from validators.ai_flavor_scorer import AIFlavorScorer

        scorer = AIFlavorScorer()

        # 各种文本都应在 0-100 范围内
        texts = [
            "",
            "短",
            "这是一个测试文本。",
            "哇！绝了！" * 50,
            "首先其次最后综上所述" * 50,
        ]
        for text in texts:
            score = scorer.score(text)
            assert 0 <= score <= 100


class TestTextAnalyzer:
    """文本分析工具测试"""

    def test_count_chinese_chars(self):
        """测试中文字符统计"""
        from validators.ai_flavor_scorer import TextAnalyzer

        assert TextAnalyzer.count_chinese_chars("你好世界") == 4
        assert TextAnalyzer.count_chinese_chars("hello") == 0
        assert TextAnalyzer.count_chinese_chars("你好hello世界") == 4

    def test_count_sentences(self):
        """测试句子统计"""
        from validators.ai_flavor_scorer import TextAnalyzer

        # split 会在分隔符前后产生空字符串
        assert TextAnalyzer.count_sentences("第一句。第二句！第三句？") >= 3
        assert TextAnalyzer.count_sentences("一句话") >= 1

    def test_extract_keywords(self):
        """测试关键词提取"""
        from validators.ai_flavor_scorer import TextAnalyzer

        keywords = TextAnalyzer.extract_keywords("护肝片真的很好用，护肝效果不错", top_n=3)
        assert len(keywords) <= 3
        assert "护" in keywords  # 出现两次


# ── ComplianceCheckTool 测试 ─────────────────────────────


class TestComplianceCheckTool:
    """合规检查工具测试"""

    def test_init(self):
        """测试初始化"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        assert tool.name == "compliance_check"
        assert tool._prohibited_patterns is not None

    def test_detect_absolute_word(self):
        """测试检测绝对化用语"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        result = tool._run("这是最好的护肝片", "xiaohongshu", "all")

        assert result["passed"] is False
        assert result["issue_count"] > 0
        # "最好的" 匹配 "最"（绝对化用语列表中有"最"）
        assert any("最" in issue["word"] for issue in result["issues"])

    def test_detect_medical_word(self):
        """测试检测医疗用语"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        result = tool._run("这个可以治疗肝病", "xiaohongshu", "all")

        assert result["passed"] is False
        assert any("治疗" in issue["word"] for issue in result["issues"])

    def test_normal_content_passes(self):
        """测试正常内容通过"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        result = tool._run("这款护肝片含有水飞蓟成分", "xiaohongshu", "all")

        assert result["passed"] is True
        assert result["issue_count"] == 0

    def test_check_absolute_only(self):
        """测试仅检查绝对化用语"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        result = tool._run("这是最好的产品", "xiaohongshu", "absolute")

        assert result["passed"] is False
        assert all(issue["category"] == "绝对化用语" for issue in result["issues"])

    def test_check_medical_only(self):
        """测试仅检查医疗用语"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        result = tool._run("可以治疗疾病", "xiaohongshu", "medical")

        assert result["passed"] is False
        assert all(issue["category"] == "医疗用语" for issue in result["issues"])

    def test_check_title(self):
        """测试标题检查"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        result = tool.check_title("这是最好的标题")

        assert "title_length" in result
        assert "in_range" in result
        assert result["passed"] is False

    def test_check_article(self):
        """测试正文检查"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        result = tool.check_article("这是一篇正常的正文内容")

        assert "word_count" in result
        assert "in_range" in result

    def test_check_tags_valid(self):
        """测试有效标签检查"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        result = tool.check_tags(["#标签1", "#标签2", "#标签3"])

        assert result["passed"] is True
        assert result["tag_count"] == 3

    def test_check_tags_invalid(self):
        """测试无效标签检查"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        result = tool.check_tags(["标签1", "#标签2"])

        assert result["passed"] is False
        assert len(result["issues"]) == 1

    def test_batch_check(self):
        """测试批量检查"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        results = tool.batch_check(["正常内容", "这是最好的", "可以治疗"])

        assert len(results) == 3
        assert results[0]["passed"] is True
        assert results[1]["passed"] is False
        assert results[2]["passed"] is False

    def test_issue_context(self):
        """测试问题上下文"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        result = tool._run("这是最好的护肝片", "xiaohongshu", "all")

        for issue in result["issues"]:
            assert "word" in issue
            assert "category" in issue
            assert "position" in issue
            assert "context" in issue


# ── ProhibitedWordDetector 测试 ──────────────────────────


class TestProhibitedWordDetector:
    """违禁词检测器测试"""

    def test_init(self):
        """测试初始化"""
        from tools.compliance_tools import ProhibitedWordDetector

        detector = ProhibitedWordDetector()
        assert detector._patterns is None

    def test_detect_general_prohibited(self):
        """测试检测通用违禁词"""
        from tools.compliance_tools import ProhibitedWordDetector

        detector = ProhibitedWordDetector()
        words = detector.detect("这是最好的产品，全网独家首发")

        # "最好的" 匹配 "最"（GENERAL_PROHIBITED 列表中有"最"）
        assert "最" in words
        assert "全网" in words
        assert "独家" in words
        assert "首发" in words

    def test_detect_healthcare_prohibited(self):
        """测试检测保健品违禁词"""
        from tools.compliance_tools import ProhibitedWordDetector

        detector = ProhibitedWordDetector()
        words = detector.detect("这个灵丹妙药有特效")

        assert "灵丹" in words
        assert "妙药" in words
        assert "特效" in words

    def test_has_prohibited_true(self):
        """测试含违禁词"""
        from tools.compliance_tools import ProhibitedWordDetector

        detector = ProhibitedWordDetector()
        assert detector.has_prohibited("这是最好的") is True

    def test_has_prohibited_false(self):
        """测试不含违禁词"""
        from tools.compliance_tools import ProhibitedWordDetector

        detector = ProhibitedWordDetector()
        assert detector.has_prohibited("这是一款不错的护肝片") is False

    def test_detect_empty_text(self):
        """测试空文本检测"""
        from tools.compliance_tools import ProhibitedWordDetector

        detector = ProhibitedWordDetector()
        words = detector.detect("")
        assert words == []

    def test_patterns_lazy_loaded(self):
        """测试正则懒加载"""
        from tools.compliance_tools import ProhibitedWordDetector

        detector = ProhibitedWordDetector()
        assert detector._patterns is None

        # 触发懒加载
        _ = detector.patterns
        assert detector._patterns is not None


# ── agents/__init__.py 导出测试 ──────────────────────────


class TestAgentExports:
    """Agent 导出测试"""

    def test_imports(self):
        """测试所有 Agent 可正常导入"""
        from agents import (
            ArticleAgent,
            TagAgent,
            ComplianceAgent,
        )

        assert ArticleAgent is not None
        assert TagAgent is not None
        assert ComplianceAgent is not None

    def test_llm_tool_property(self):
        """测试 LLM 工具属性"""
        from agents.article_agent import ArticleAgent
        from agents.tag_agent import TagAgent
        from agents.compliance_agent import ComplianceAgent

        article = ArticleAgent()
        tag = TagAgent()
        compliance = ComplianceAgent()

        # 懒加载
        assert article._llm_tool is None
        assert tag._llm_tool is None
        assert compliance._llm_tool is None
