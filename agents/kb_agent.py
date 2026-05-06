"""
知识库 Agent - 知识检索与管理专家
"""

import json
import os
from pathlib import Path
from typing import Optional

from crewai import Agent
from crewai.llm import LLM
from crewai.tools import BaseTool

from config import LLMConfig
from models import KnowledgeEntry, SearchResult


class KnowledgeBaseAgent:
    """知识库管理Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = None  # KB Agent不使用预定义配置
        self.llm_config = llm_config
        self.tools = tools or []
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        """获取 CrewAI Agent 实例"""
        if self._agent is None:
            prompt_path = Path("prompts/kb_agent.md")
            if prompt_path.exists():
                with open(prompt_path, "r", encoding="utf-8") as f:
                    self._prompt_template = f.read()
            else:
                self._prompt_template = self._get_default_prompt()

            self._agent = Agent(
                role="知识库管理专家",
                goal="从知识库中检索相关信息并提供知识问答",
                backstory=self._prompt_template,
                tools=self.tools,
                verbose=True,
                llm=LLM(
                    model="openai/MiniMax-M2.7",
                    api_key=os.getenv("MINIMAX_API_KEY", ""),
                    api_base=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1"),
                    llm_type="litellm",
                ),
            )
        return self._agent

    @property
    def _llm(self):
        """获取 LLM 配置"""
        if self.llm_config:
            return self.llm_config
        from openai import OpenAI
        return OpenAI(
            api_key=os.getenv("MINIMAX_API_KEY", ""),
            api_base=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1"),
        )

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

    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """你是知识库管理专家，擅长知识检索、知识整理和知识问答。
核心能力：知识检索、知识整理、知识问答、知识推荐"""