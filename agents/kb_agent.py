"""
知识库 Agent - 知识检索与管理专家
"""

from typing import Optional

from crewai import Agent
from crewai.tools import BaseTool
from pydantic import BaseModel

from config import LLMManagerConfig
from config.llm_config import get_llm_for_agent
from models import KnowledgeEntry, SearchResult
from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm


class KnowledgeBaseAgent:
    """知识库管理Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMManagerConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self._llm_config = llm_config or get_llm_for_agent("kb")
        self.tools = tools or []
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        """获取 CrewAI Agent 实例"""
        if self._agent is None:
            prompt = prompt_manager.load_prompt("kb_agent")
            self._agent = Agent(
                role="知识库管理专家",
                goal="从知识库中检索相关信息并提供知识问答",
                backstory=prompt,
                tools=self.tools,
                verbose=True,
                llm=create_llm(self._llm_config),
            )
        return self._agent

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
        limit: int = 10,
    ) -> SearchResult:
        """
        搜索知识库

        Args:
            query: 搜索查询
            category: 分类过滤
            tags: 标签过滤
            limit: 返回数量

        Returns:
            SearchResult: 搜索结果
        """
        from sync.obsidian_client import ObsidianClient
        from sync.knowledge_loader import KnowledgeLoader

        obsidian = ObsidianClient()
        loader = KnowledgeLoader(obsidian_client=obsidian)

        # 从Obsidian加载知识
        entries = loader.load_from_obsidian_vault()

        # 简单的关键词过滤
        filtered = []
        for entry in entries:
            if query.lower() in entry.content.lower() or query.lower() in entry.title.lower():
                if category and entry.category != category:
                    continue
                if tags and not any(tag in entry.tags for tag in tags):
                    continue
                filtered.append(entry)

        # 限制返回数量
        limited_entries = filtered[:limit]

        return SearchResult(
            entries=limited_entries,
            total=len(filtered),
            query=query,
        )

    def retrieve_context(
        self,
        query: str,
        max_entries: int = 5,
    ) -> str:
        """
        检索上下文用于增强LLM

        Args:
            query: 查询
            max_entries: 最大条目数

        Returns:
            上下文字符串
        """
        result = self.search(query, limit=max_entries)

        if not result.entries:
            return ""

        context_parts = []
        for entry in result.entries:
            context_parts.append(f"## {entry.title}\n{entry.content[:500]}...")

        return "\n\n".join(context_parts)


class KBAgentRequest(BaseModel):
    """KnowledgeBaseAgent 独立调用请求"""
    query: str
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    limit: int = 10


def _kb_run_standalone(self, req: KBAgentRequest) -> SearchResult:
    return self.search(query=req.query, category=req.category, tags=req.tags, limit=req.limit)


KnowledgeBaseAgent.run_standalone = _kb_run_standalone
