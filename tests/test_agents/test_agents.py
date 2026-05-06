"""
Agent测试
"""

import pytest
from unittest.mock import MagicMock, patch


class TestTitleAgent:
    """标题Agent测试"""

    def setup_method(self):
        """测试前准备"""
        pass

    def test_generate_titles(self):
        """测试生成标题"""
        from agents.title_agent import TitleAgent

        mock_llm = MagicMock()
        mock_llm._run.return_value = '{"titles": [{"title": "测试标题", "strategy": "痛点", "score": 8, "reason": "理由"}]}'

        agent = TitleAgent(mock_llm)
        result = agent.run("护肝片")
        assert result is not None


class TestArticleAgent:
    """正文Agent测试"""

    def test_generate_article(self):
        """测试生成正文"""
        from agents.article_agent import ArticleAgent

        mock_llm = MagicMock()
        mock_llm._run.return_value = "这是一篇测试正文"

        agent = ArticleAgent(mock_llm)
        result = agent.run("护肝片", "测试标题")
        assert result is not None


class TestTagAgent:
    """标签Agent测试"""

    def test_generate_tags(self):
        """测试生成标签"""
        from agents.tag_agent import TagAgent

        mock_llm = MagicMock()
        mock_llm._run.return_value = '{"tags": ["护肝", "养生"]}'

        agent = TagAgent(mock_llm)
        result = agent.run("测试正文", "测试标题")
        assert result is not None


class TestComplianceAgent:
    """合规Agent测试"""

    def test_check_compliance(self):
        """测试合规检查"""
        from agents.compliance_agent import ComplianceAgent

        mock_llm = MagicMock()
        mock_llm._run.return_value = '{"status": "passed", "issues": []}'

        agent = ComplianceAgent(mock_llm)
        result = agent.run("测试内容", "xiaohongshu")
        assert result is not None


class TestMaterialAgent:
    """素材检索Agent测试"""

    def test_search_material(self):
        """测试素材检索"""
        from agents.material_agent import MaterialAgent

        mock_llm = MagicMock()
        mock_llm._run.return_value = '{"brand": {"name": "护肝宝"}, "product": {"name": "护肝片"}}'

        agent = MaterialAgent(mock_llm)
        result = agent.run("护肝片", "加班人群")
        assert result is not None
