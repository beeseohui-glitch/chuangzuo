"""
Agent 统一调用层

让每个 Agent 可以脱离 Flow 被独立调用。
- AgentRequest: 标准化请求
- AgentResponse: 标准化响应
- BaseAgentRunner: 统一执行器，管理 Agent 注册和懒加载
"""

import time
import logging
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentRequest(BaseModel):
    """Agent 统一请求"""
    agent_name: str = Field(description="Agent 名称: title/article/tag/compliance/material/topic/kb/analytics/operation/wechat/douyin/orchestrator")
    method: str = Field(description="调用方法名: generate/check/search/generate_topics/generate_report/generate_schedule/generate_article/generate_script/route")
    params: dict[str, Any] = Field(default_factory=dict, description="方法参数，直接对应各 Agent 业务方法的 kwargs")
    enterprise_id: Optional[str] = Field(default=None, description="企业 ID")
    request_id: Optional[str] = Field(default=None, description="请求追踪 ID")


class AgentResponse(BaseModel):
    """Agent 统一响应"""
    success: bool
    data: Optional[Any] = Field(default=None, description="返回数据（Pydantic model 或原生类型）")
    error: Optional[str] = Field(default=None, description="错误信息")
    warnings: list[str] = Field(default_factory=list, description="警告列表")
    duration_ms: float = Field(default=0.0, description="执行耗时(ms)")
    agent_name: str = Field(default="", description="Agent 名称")
    method: str = Field(default="", description="调用方法名")


# Agent 注册表：名称 -> 类引用（延迟构建，避免循环依赖）
_AGENT_REGISTRY: Optional[dict[str, type]] = None


def _build_registry() -> dict[str, type]:
    """构建 Agent 注册表（延迟 import 避免循环依赖）"""
    from agents.title_agent import TitleAgent
    from agents.article_agent import ArticleAgent
    from agents.tag_agent import TagAgent
    from agents.compliance_agent import ComplianceAgent
    from agents.material_agent import MaterialAgent
    from agents.topic_agent import TopicAgent
    from agents.kb_agent import KnowledgeBaseAgent
    from agents.analytics_agent import AnalyticsAgent
    from agents.operation_agent import OperationAgent
    from agents.wechat_article_agent import WechatArticleAgent
    from agents.douyin_script_agent import DouyinScriptAgent
    from agents.orchestrator_agent import OrchestratorAgent

    return {
        "title": TitleAgent,
        "article": ArticleAgent,
        "tag": TagAgent,
        "compliance": ComplianceAgent,
        "material": MaterialAgent,
        "topic": TopicAgent,
        "kb": KnowledgeBaseAgent,
        "analytics": AnalyticsAgent,
        "operation": OperationAgent,
        "wechat": WechatArticleAgent,
        "douyin": DouyinScriptAgent,
        "orchestrator": OrchestratorAgent,
    }


def get_agent_registry() -> dict[str, type]:
    """获取 Agent 注册表（单例）"""
    global _AGENT_REGISTRY
    if _AGENT_REGISTRY is None:
        _AGENT_REGISTRY = _build_registry()
    return _AGENT_REGISTRY


class BaseAgentRunner:
    """Agent 独立执行器 - 包装任意 Agent 的调用"""

    def __init__(self):
        self._agents: dict[str, Any] = {}

    def get_agent(self, agent_name: str) -> Any:
        """
        懒加载 Agent 实例

        Args:
            agent_name: Agent 名称

        Returns:
            Agent 实例

        Raises:
            ValueError: 未知的 Agent 名称
        """
        if agent_name not in self._agents:
            registry = get_agent_registry()
            cls = registry.get(agent_name)
            if not cls:
                raise ValueError(
                    f"Unknown agent: '{agent_name}'. "
                    f"Available: {list(registry.keys())}"
                )
            self._agents[agent_name] = cls()
        return self._agents[agent_name]

    def run(self, request: AgentRequest) -> AgentResponse:
        """
        执行 Agent 调用

        Args:
            request: 标准化请求

        Returns:
            AgentResponse: 标准化响应
        """
        start_time = time.time()

        try:
            agent = self.get_agent(request.agent_name)
            method = getattr(agent, request.method, None)

            if method is None:
                available = [m for m in dir(agent) if not m.startswith("_") and callable(getattr(agent, m))]
                return AgentResponse(
                    success=False,
                    error=f"Method '{request.method}' not found on {request.agent_name}Agent. "
                          f"Available: {available}",
                    agent_name=request.agent_name,
                    method=request.method,
                    duration_ms=(time.time() - start_time) * 1000,
                )

            result = method(**request.params)

            return AgentResponse(
                success=True,
                data=result,
                agent_name=request.agent_name,
                method=request.method,
                duration_ms=(time.time() - start_time) * 1000,
            )

        except TypeError as e:
            logger.error(f"Agent call parameter error: {e}")
            return AgentResponse(
                success=False,
                error=f"Parameter error: {e}",
                agent_name=request.agent_name,
                method=request.method,
                duration_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.error(f"Agent call failed: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e),
                agent_name=request.agent_name,
                method=request.method,
                duration_ms=(time.time() - start_time) * 1000,
            )

    def list_agents(self) -> list[str]:
        """列出所有可用的 Agent 名称"""
        return list(get_agent_registry().keys())

    def clear_cache(self):
        """清除缓存的 Agent 实例"""
        self._agents.clear()
