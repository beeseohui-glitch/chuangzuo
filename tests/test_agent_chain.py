"""
测试 AgentChain — Agent 链式执行
"""

import pytest
from unittest.mock import patch, MagicMock


class TestAgentChain:
    """AgentChain 测试"""

    def test_import(self):
        """测试能否正常导入"""
        from agents.agent_chain import AgentChain
        assert AgentChain is not None

    def test_chain_init(self):
        """测试链初始化"""
        from agents.agent_chain import AgentChain
        chain = AgentChain()
        assert chain is not None

    def test_add_step(self):
        """测试添加步骤"""
        from agents.agent_chain import AgentChain
        chain = AgentChain()
        result = chain.add_step(
            agent_name="title",
            method="generate",
            params_fn=lambda ctx: {"topic": ctx.get("topic", "")},
        )
        # add_step 返回 self 支持链式调用
        assert result is chain

    def test_chain_fluent_api(self):
        """测试链式 API"""
        from agents.agent_chain import AgentChain
        chain = (AgentChain()
            .add_step("material", "search", lambda ctx: {"product": "test"})
            .add_step("title", "generate", lambda ctx: {"topic": "test"})
            .add_step("article", "generate", lambda ctx: {"title": "test"})
        )
        assert chain is not None


class TestAgentChainResult:
    """AgentChainResult 测试"""

    def test_import(self):
        """测试能否正常导入"""
        from models.agent_message import AgentChainResult
        assert AgentChainResult is not None

    def test_model_creation(self):
        """测试模型创建"""
        from models.agent_message import AgentChainResult
        result = AgentChainResult(
            chain_id="chain_001",
            steps=[{"agent": "title", "duration_ms": 100}],
            final_result={"title": "test"},
            success=True,
            total_duration_ms=100.0,
        )
        assert result.chain_id == "chain_001"
        assert result.success is True
        assert len(result.steps) == 1

    def test_model_with_warnings(self):
        """测试带警告的模型"""
        from models.agent_message import AgentChainResult
        result = AgentChainResult(
            chain_id="chain_002",
            steps=[],
            final_result=None,
            success=False,
            total_duration_ms=0.0,
            warnings=["Step 1 failed"],
        )
        assert result.success is False
        assert len(result.warnings) == 1


class TestAgentMessage:
    """AgentMessage 测试"""

    def test_import(self):
        """测试能否正常导入"""
        from models.agent_message import AgentMessage
        assert AgentMessage is not None

    def test_message_creation(self):
        """测试消息创建"""
        from models.agent_message import AgentMessage
        msg = AgentMessage(
            message_type="task",
            source_agent="orchestrator",
            target_agent="title",
            payload={"topic": "test"},
        )
        assert msg.message_type == "task"
        assert msg.source_agent == "orchestrator"
        assert msg.target_agent == "title"


class TestComplianceFeedback:
    """ComplianceFeedback 测试"""

    def test_import(self):
        """测试能否正常导入"""
        from models.agent_message import ComplianceFeedback, CorrectionRequest
        assert ComplianceFeedback is not None
        assert CorrectionRequest is not None

    def test_feedback_creation(self):
        """测试反馈创建"""
        from models.agent_message import ComplianceFeedback
        feedback = ComplianceFeedback(
            issue_content="绝对化用语",
            issue_location="标题",
            severity="p0",
            suggestion="将'最好'改为'推荐'",
            original_text="这是最好的护肝片",
        )
        assert feedback.severity == "p0"
        assert feedback.original_text == "这是最好的护肝片"

    def test_correction_request(self):
        """测试修正请求"""
        from models.agent_message import ComplianceFeedback, CorrectionRequest
        feedbacks = [
            ComplianceFeedback(
                issue_content="测试",
                issue_location="正文",
                severity="p0",
                suggestion="修改",
                original_text="原文",
            ),
        ]
        req = CorrectionRequest(feedbacks=feedbacks)
        assert len(req.feedbacks) == 1
        assert req.target_field == "article"
        assert req.max_changes == 5
