"""
Validator测试

Step 15: 测试模块开发
"""

import pytest


class TestAIFlavorScorer:
    """AI味评分器测试"""

    def setup_method(self):
        """测试前准备"""
        from validators.ai_flavor_scorer import AIFlavorScorer
        self.scorer = AIFlavorScorer()

    def test_score_article(self):
        """测试文章评分"""
        article = """
        打工人真的太难了，每天加班到十一二点。
        后来被同事种草了护肝片，不得不说真的太香了！
        主要成分是水飞蓟，再加上B族维生素。
        我大概吃了两个月，最明显的感觉就是早上起来不那么累了。
        每天就吃两粒，完全不占时间。
        """
        score = self.scorer.score(article)
        assert 0 <= score <= 100

    def test_score_empty_content(self):
        """测试空内容评分"""
        score = self.scorer.score("")
        assert score == 0

    def test_high_ai_flavour(self):
        """测试高AI味内容"""
        article = """
        首先，水飞蓟是一种非常有效的护肝成分。
        其次，B族维生素对于肝脏代谢具有重要作用。
        最后，每日服用两粒可以有效保护肝脏。
        综上所述，这款护肝片是一款值得推荐的产品。
        """
        score = self.scorer.score(article)
        assert score < 70  # AI味重的内容应该得分较低


class TestResultValidator:
    """结果校验器测试"""

    def setup_method(self):
        """测试前准备"""
        from validators.result_validator import ResultValidator
        self.validator = ResultValidator()

    def test_validate_title_output(self):
        """测试标题输出校验"""
        from models.note_output import TitleOption

        titles = [
            TitleOption(title=f"标题{i}", strategy="策略", score=8, reason="理由")
            for i in range(5)
        ]
        result = self.validator.validate_title_output(titles)
        assert result.passed is True

    def test_validate_title_output_insufficient(self):
        """测试标题数量不足"""
        from models.note_output import TitleOption

        titles = [
            TitleOption(title="标题1", strategy="策略", score=8, reason="理由")
        ]
        result = self.validator.validate_title_output(titles)
        assert result.passed is False
