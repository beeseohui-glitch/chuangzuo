"""
合规 Agent - 内容合规审核专家

Prompt：从 prompts/compliance_agent.md 加载
P0/P1/P2 三级合规检查
输出：ComplianceReport
Harness：JSON解析 + status映射 + 降级报告
"""

import json
import logging
from datetime import datetime
from typing import Optional

from crewai import Agent
from crewai.tools import BaseTool

from config import COMPLIANCE_AGENT, LLMManagerConfig, XiaohongshuConfig
from config.llm_config import get_llm_for_agent
from models import (
    ComplianceReport,
    ComplianceStatus,
    ComplianceSeverity,
    ComplianceIssue,
)
from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm
from tools.llm_tools import LLMCallTool, LLMResponseParser

logger = logging.getLogger(__name__)


class ComplianceAgent:
    """内容合规审核Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMManagerConfig] = None,
        platform_config: Optional[XiaohongshuConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.config = COMPLIANCE_AGENT
        self.platform_config = platform_config or XiaohongshuConfig()
        self._llm_config = llm_config or get_llm_for_agent("compliance")
        self._tools = tools or []
        self._agent: Optional[Agent] = None
        self._llm_tool: Optional[LLMCallTool] = None

    @property
    def llm_tool(self) -> LLMCallTool:
        """获取 LLM 调用工具（带降级）"""
        if self._llm_tool is None:
            self._llm_tool = LLMCallTool(self._llm_config)
        return self._llm_tool

    @property
    def agent(self) -> Agent:
        """获取 CrewAI Agent 实例"""
        if self._agent is None:
            prompt = prompt_manager.load_prompt("compliance_agent")

            self._agent = Agent(
                role="内容合规审核专家",
                goal="检查内容合规性并生成报告",
                backstory=prompt,
                tools=self._tools,
                verbose=True,
                llm=create_llm(self._llm_config),
            )
        return self._agent

    def check(
        self,
        title: str,
        article: str,
        tags: list[str],
        brand_taboos: Optional[list[str]] = None,
    ) -> ComplianceReport:
        """
        检查内容合规性

        Args:
            title: 标题
            article: 正文
            tags: 标签列表
            brand_taboos: 品牌禁忌词

        Returns:
            ComplianceReport: 合规报告
        """
        max_retries = self.config.max_retries
        last_error = None

        for attempt in range(max_retries + 1):
            prompt = self._build_prompt(title, article, tags, brand_taboos)

            try:
                response = self.agent.kickoff(prompt)
                content = response.content if hasattr(response, "content") else str(response)
                return self._parse_response(content)

            except Exception as e:
                last_error = e
                logger.error(f"Compliance check failed (attempt {attempt+1}): {e}")

        # 所有重试失败，返回降级报告
        return ComplianceReport(
            status=ComplianceStatus.NEEDS_REVISION,
            checked_at=datetime.now().isoformat(),
            suggestions=[f"合规检查失败（已重试{max_retries}次）: {last_error}"],
        )

    def _build_prompt(
        self,
        title: str,
        article: str,
        tags: list[str],
        brand_taboos: Optional[list[str]] = None,
    ) -> str:
        """构建提示词"""
        taboos_str = ", ".join(brand_taboos or [])

        prompt = f"""
请检查以下小红书内容的合规性：

标题：{title}

正文：{article[:500]}...

标签：{', '.join(tags)}

品牌禁忌词：{taboos_str if taboos_str else '无'}

平台违禁词（绝对化用语、医疗用语）：
- 最、第一、100%、顶级、绝对、全网、独家、首发
- 治疗、治愈、疗效、药到病除
- 特效、神效、灵丹、妙药

校验清单：
P0（必须修改）：广告法违禁词、医疗用语
P1（建议修改）：品牌调性偏离、产品信息不准确
P2（需人工确认）：灰色地带表述、创意表达边界

输出格式为JSON：
{{
  "status": "通过/需修改/不通过",
  "p0_issues": [
    {{"severity": "p0", "content": "问题内容", "location": "位置", "suggestion": "建议"}}
  ],
  "p1_issues": [],
  "p2_issues": [],
  "suggestions": ["总体建议"]
}}
"""

        return prompt

    def _parse_response(self, content: str) -> ComplianceReport:
        """解析响应"""
        start = content.find("{")
        end = content.rfind("}") + 1

        if start != -1 and end != 0:
            json_str = content[start:end]
            data = json.loads(json_str)

            # 转换 issues
            for level in ["p0_issues", "p1_issues", "p2_issues"]:
                if level in data:
                    data[level] = [
                        ComplianceIssue(
                            severity=ComplianceSeverity(issue.get("severity", "p1")),
                            content=issue.get("content", ""),
                            location=issue.get("location", ""),
                            suggestion=issue.get("suggestion", ""),
                        )
                        for issue in data[level]
                    ]

            # 转换 status
            status_map = {
                "通过": ComplianceStatus.PASSED,
                "需修改": ComplianceStatus.NEEDS_REVISION,
                "不通过": ComplianceStatus.FAILED,
            }
            data["status"] = status_map.get(data.get("status", ""), ComplianceStatus.NEEDS_REVISION)

            data["checked_at"] = datetime.now().isoformat()

            return ComplianceReport(**data)

        raise ValueError(f"Cannot parse ComplianceReport from response: {content[:200]}")

