"""
Tool测试
"""

import pytest
from unittest.mock import MagicMock, patch


class TestLLMCallTool:
    """LLM调用工具测试"""

    def test_initialization(self):
        """测试初始化"""
        from tools.llm_tools import LLMCallTool

        with patch("tools.llm_tools.OpenAI"):
            tool = LLMCallTool()
            assert tool is not None

    def test_run_with_mock(self):
        """测试运行"""
        from tools.llm_tools import LLMCallTool

        with patch("tools.llm_tools.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "测试回复"
            mock_client.chat.completions.create.return_value = mock_response
            mock_openai.return_value = mock_client

            tool = LLMCallTool()
            result = tool._run("测试提示")
            assert "测试回复" in result


class TestComplianceCheckTool:
    """合规检查工具测试"""

    def test_initialization(self):
        """测试初始化"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        assert tool is not None

    def test_check_content(self):
        """测试内容检查"""
        from tools.compliance_tools import ComplianceCheckTool

        tool = ComplianceCheckTool()
        result = tool._run("这是一个正常内容", "xiaohongshu", "health")
        assert isinstance(result, list)


class TestEmbeddingTool:
    """Embedding工具测试"""

    def test_initialization(self):
        """测试初始化"""
        from tools.embedding_tools import LocalEmbeddingTool

        with patch("tools.embedding_tools.LocalEmbedding"):
            tool = LocalEmbeddingTool()
            assert tool is not None


class TestVectorStoreTool:
    """向量存储工具测试"""

    def test_initialization(self):
        """测试初始化"""
        from tools.vector_tools import VectorStoreTool

        tool = VectorStoreTool()
        assert tool is not None


class TestObsidianTools:
    """Obsidian工具测试"""

    def test_initialization(self):
        """测试初始化"""
        from tools.obsidian_tools import ObsidianReaderTool

        tool = ObsidianReaderTool()
        assert tool is not None


class TestCOSTools:
    """COS工具测试"""

    def test_initialization(self):
        """测试初始化"""
        from tools.cos_tools import COSUploadTool

        with patch("tools.cos_tools.COSClient"):
            tool = COSUploadTool()
            assert tool is not None
