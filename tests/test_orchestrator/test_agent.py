"""
Agent测试

Step 15: 测试模块开发
"""

import pytest
from unittest.mock import MagicMock


class TestOrchestratorAgent:
    """统一调度Agent测试"""

    def setup_method(self):
        """测试前准备"""
        self.mock_llm = MagicMock()

    def test_orchestrator_route(self):
        """测试路由功能"""
        from orchestrator.agent import OrchestratorAgent, RouterOutput

        self.mock_llm._run.return_value = '{"platform": "xiaohongshu", "product": "护肝片", "scene": "加班", "style": "口语化", "route_to": "xiaohongshu_flow"}'

        agent = OrchestratorAgent(self.mock_llm)
        result = agent.route("帮我写一个护肝片的小红书笔记")

        assert isinstance(result, RouterOutput)
        assert result.platform == "xiaohongshu"
        assert result.route_to == "xiaohongshu_flow"


class TestRouter:
    """路由器测试"""

    def test_route_xiaohongshu(self):
        """测试小红书路由"""
        from orchestrator.router import Router

        assert Router.route("小红书") == "xiaohongshu_flow"
        assert Router.route("xiaohongshu") == "xiaohongshu_flow"

    def test_route_douyin(self):
        """测试抖音路由"""
        from orchestrator.router import Router

        assert Router.route("抖音") == "douyin_flow"
        assert Router.route("douyin") == "douyin_flow"

    def test_route_unknown(self):
        """测试未知平台路由"""
        from orchestrator.router import Router

        assert Router.route("unknown_platform") == ""

    def test_get_platforms(self):
        """测试获取平台列表"""
        from orchestrator.router import Router

        platforms = Router.get_platforms()
        assert "xiaohongshu" in platforms
        assert "douyin" in platforms
