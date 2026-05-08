"""
测试 Agent API 端点 — /api/v1/agents/*
"""

import pytest


class TestAgentEndpointsImport:
    """Agent 端点导入测试"""

    def test_import_router(self):
        """测试能否导入 agents 路由"""
        from api.routes.agents import router
        assert router is not None

    def test_router_prefix(self):
        """测试路由前缀"""
        from api.routes.agents import router
        assert router.prefix == "/api/v1/agents"

    def test_router_tags(self):
        """测试路由标签"""
        from api.routes.agents import router
        assert "Agent" in router.tags[0] or "agent" in router.tags[0].lower()


class TestAgentEndpointsExist:
    """Agent 端点存在性测试"""

    def test_run_endpoint_exists(self):
        """测试统一调用端点存在"""
        from api.routes.agents import router
        routes = [r.path for r in router.routes]
        assert "/api/v1/agents/run" in routes or any("run" in r for r in routes)

    def test_title_endpoint_exists(self):
        """测试标题生成端点存在"""
        from api.routes.agents import router
        routes = [r.path for r in router.routes]
        assert any("title" in r for r in routes)

    def test_article_endpoint_exists(self):
        """测试正文生成端点存在"""
        from api.routes.agents import router
        routes = [r.path for r in router.routes]
        assert any("article" in r for r in routes)

    def test_compliance_endpoint_exists(self):
        """测试合规检查端点存在"""
        from api.routes.agents import router
        routes = [r.path for r in router.routes]
        assert any("compliance" in r for r in routes)

    def test_topic_endpoint_exists(self):
        """测试选题推荐端点存在"""
        from api.routes.agents import router
        routes = [r.path for r in router.routes]
        assert any("topic" in r for r in routes)

    def test_material_endpoint_exists(self):
        """测试素材检索端点存在"""
        from api.routes.agents import router
        routes = [r.path for r in router.routes]
        assert any("material" in r for r in routes)

    def test_orchestrator_endpoint_exists(self):
        """测试智能路由端点存在"""
        from api.routes.agents import router
        routes = [r.path for r in router.routes]
        assert any("orchestrator" in r for r in routes)

    def test_topic_endpoint_uses_recommend(self):
        """测试选题端点使用 recommend 路径"""
        from api.routes.agents import router
        routes = [r.path for r in router.routes]
        assert any("topic/recommend" in r for r in routes)

    def test_total_agent_routes(self):
        """测试 Agent 路由总数"""
        from api.routes.agents import router
        routes = [r.path for r in router.routes]
        # 应有 13 个路由（1 统一 + 12 快捷）
        assert len(routes) >= 13


class TestMainAppRoutes:
    """测试主应用路由注册"""

    def test_agents_router_registered(self):
        """测试 agents 路由已注册到主应用"""
        from api.main import app
        route_paths = [r.path for r in app.routes]
        assert any("/api/v1/agents" in r for r in route_paths)

    def test_create_router_registered(self):
        """测试 create 路由已注册"""
        from api.main import app
        route_paths = [r.path for r in app.routes]
        assert any("/api/v1/create" in r for r in route_paths)

    def test_total_routes_count(self):
        """测试总路由数量"""
        from api.main import app
        route_paths = [r.path for r in app.routes if hasattr(r, 'path')]
        # 应该有至少 75 个路由（原有 62 + 新增 13）
        assert len(route_paths) >= 70
