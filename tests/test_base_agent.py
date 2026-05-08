"""
测试 BaseAgentRunner — Agent 独立调用层
"""

import pytest
from unittest.mock import patch, MagicMock


class TestBaseAgentRunner:
    """BaseAgentRunner 测试"""

    def test_import(self):
        """测试能否正常导入"""
        from agents.base_agent import BaseAgentRunner, AgentRequest, AgentResponse
        assert BaseAgentRunner is not None
        assert AgentRequest is not None
        assert AgentResponse is not None

    def test_runner_init(self):
        """测试 Runner 初始化"""
        from agents.base_agent import BaseAgentRunner
        runner = BaseAgentRunner()
        assert runner is not None

    def test_list_agents(self):
        """测试列出所有注册 Agent"""
        from agents.base_agent import BaseAgentRunner
        runner = BaseAgentRunner()
        agents = runner.list_agents()
        assert isinstance(agents, list)
        assert len(agents) >= 12
        assert "title" in agents
        assert "article" in agents
        assert "compliance" in agents
        assert "orchestrator" in agents

    def test_get_agent_invalid(self):
        """测试获取不存在的 Agent"""
        from agents.base_agent import BaseAgentRunner
        runner = BaseAgentRunner()
        with pytest.raises((ValueError, KeyError)):
            runner.get_agent("nonexistent_agent")

    def test_agent_request_model(self):
        """测试 AgentRequest 模型"""
        from agents.base_agent import AgentRequest
        req = AgentRequest(
            agent_name="title",
            method="generate",
            params={"topic": "test"},
        )
        assert req.agent_name == "title"
        assert req.method == "generate"
        assert req.params == {"topic": "test"}

    def test_agent_response_model(self):
        """测试 AgentResponse 模型"""
        from agents.base_agent import AgentResponse
        resp = AgentResponse(
            success=True,
            data={"title": "test"},
            duration_ms=100.0,
        )
        assert resp.success is True
        assert resp.data == {"title": "test"}
        assert resp.duration_ms == 100.0

    def test_agent_response_failure(self):
        """测试 AgentResponse 失败场景"""
        from agents.base_agent import AgentResponse
        resp = AgentResponse(
            success=False,
            error="Agent not found",
        )
        assert resp.success is False
        assert resp.error == "Agent not found"

    def test_clear_cache(self):
        """测试清除缓存"""
        from agents.base_agent import BaseAgentRunner
        runner = BaseAgentRunner()
        runner.clear_cache()
        # 不应抛出异常


class TestAgentRunStandalone:
    """各 Agent 的 run_standalone 方法测试"""

    def test_title_agent_has_run_standalone(self):
        """测试 TitleAgent 有 run_standalone 方法"""
        from agents.title_agent import TitleAgent
        assert hasattr(TitleAgent, 'run_standalone')

    def test_article_agent_has_run_standalone(self):
        """测试 ArticleAgent 有 run_standalone 方法"""
        from agents.article_agent import ArticleAgent
        assert hasattr(ArticleAgent, 'run_standalone')

    def test_tag_agent_has_run_standalone(self):
        """测试 TagAgent 有 run_standalone 方法"""
        from agents.tag_agent import TagAgent
        assert hasattr(TagAgent, 'run_standalone')

    def test_compliance_agent_has_run_standalone(self):
        """测试 ComplianceAgent 有 run_standalone 方法"""
        from agents.compliance_agent import ComplianceAgent
        assert hasattr(ComplianceAgent, 'run_standalone')

    def test_material_agent_has_run_standalone(self):
        """测试 MaterialAgent 有 run_standalone 方法"""
        from agents.material_agent import MaterialAgent
        assert hasattr(MaterialAgent, 'run_standalone')

    def test_topic_agent_has_run_standalone(self):
        """测试 TopicAgent 有 run_standalone 方法"""
        from agents.topic_agent import TopicAgent
        assert hasattr(TopicAgent, 'run_standalone')

    def test_orchestrator_agent_has_run_standalone(self):
        """测试 OrchestratorAgent 有 run_standalone 方法"""
        from agents.orchestrator_agent import OrchestratorAgent
        assert hasattr(OrchestratorAgent, 'run_standalone')


class TestAgentRequestModels:
    """各 Agent 的 Request 模型测试"""

    def test_title_agent_request(self):
        """测试 TitleAgentRequest 模型"""
        from agents.title_agent import TitleAgentRequest
        req = TitleAgentRequest(topic="test", material_pack={})
        assert req.topic == "test"
        assert req.material_pack == {}

    def test_article_agent_request(self):
        """测试 ArticleAgentRequest 模型"""
        from agents.article_agent import ArticleAgentRequest
        req = ArticleAgentRequest(title="test", material_pack={})
        assert req.title == "test"

    def test_compliance_agent_request(self):
        """测试 ComplianceAgentRequest 模型"""
        from agents.compliance_agent import ComplianceAgentRequest
        req = ComplianceAgentRequest(title="test", article="content")
        assert req.title == "test"
        assert req.article == "content"

    def test_orchestrator_agent_request(self):
        """测试 OrchestratorAgent 使用 str 参数"""
        from agents.orchestrator_agent import OrchestratorAgent
        agent = OrchestratorAgent()
        # run_standalone 接受 str 参数
        assert hasattr(agent, 'run_standalone')
