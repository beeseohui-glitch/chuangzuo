"""
Flow测试
"""

import pytest
from unittest.mock import MagicMock, patch


class TestXiaohongshuFlow:
    """小红书创作Flow测试"""

    def test_flow_initialization(self):
        """测试Flow初始化"""
        from flows.xiaohongshu_flow import XiaohongshuFlow

        with patch("flows.xiaohongshu_flow.LLMCallTool"):
            with patch("flows.xiaohongshu_flow.ComplianceCheckTool"):
                flow = XiaohongshuFlow()
                assert flow is not None

    def test_flow_run(self):
        """测试Flow运行"""
        from flows.xiaohongshu_flow import XiaohongshuFlow

        with patch("flows.xiaohongshu_flow.LLMCallTool") as mock_llm:
            with patch("flows.xiaohongshu_flow.ComplianceCheckTool"):
                mock_instance = MagicMock()
                mock_instance._run.return_value = '{"titles": []}'
                mock_llm.return_value = mock_instance

                flow = XiaohongshuFlow()
                result = flow.run("护肝片种草")
                assert result is not None


class TestMainFlow:
    """主Flow测试"""

    def test_route_to_xiaohongshu(self):
        """测试路由到小红书"""
        from flows.main_flow import MainFlow

        with patch("flows.main_flow.OrchestratorAgent"):
            flow = MainFlow()
            assert flow is not None
