"""
数据分析 Agent - 数据分析专家
"""

import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

from crewai import Agent
from crewai.llm import LLM
from crewai.tools import BaseTool

from config import LLMConfig
from models import (
    AnalyticsData,
    ContentStats,
    PerformanceMetrics,
    ContentPerformance,
    TrendData,
)


class AnalyticsAgent:
    """数据分析Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self.llm_config = llm_config
        self.tools = tools or []
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        """获取 CrewAI Agent 实例"""
        if self._agent is None:
            prompt_path = Path("prompts/analytics_agent.md")
            if prompt_path.exists():
                with open(prompt_path, "r", encoding="utf-8") as f:
                    self._prompt_template = f.read()
            else:
                self._prompt_template = self._get_default_prompt()

            self._agent = Agent(
                role="数据分析专家",
                goal="从数据中提取洞察并生成可操作的建议",
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

    def generate_report(
        self,
        period_start: str,
        period_end: str,
        content_data: list[dict],
    ) -> AnalyticsData:
        """
        生成数据分析报告

        Args:
            period_start: 统计周期开始
            period_end: 统计周期结束
            content_data: 内容数据列表

        Returns:
            AnalyticsData: 分析数据
        """
        # 计算内容统计
        content_stats = self._calculate_content_stats(content_data)

        # 计算平台性能
        performance_by_platform = self._calculate_platform_performance(content_data)

        # 获取Top内容
        top_content = self._get_top_content(content_data, limit=5)

        # 生成建议
        recommendations = self._generate_recommendations(content_stats, performance_by_platform)

        return AnalyticsData(
            period_start=period_start,
            period_end=period_end,
            content_stats=content_stats,
            performance_by_platform=performance_by_platform,
            top_performing_content=top_content,
            trends={},
            recommendations=recommendations,
        )

    def _calculate_content_stats(self, content_data: list[dict]) -> ContentStats:
        """计算内容统计"""
        total = len(content_data)
        published = sum(1 for c in content_data if c.get("status") == "published")
        draft = sum(1 for c in content_data if c.get("status") == "draft")

        total_views = sum(c.get("views", 0) for c in content_data)
        total_likes = sum(c.get("likes", 0) for c in content_data)
        total_comments = sum(c.get("comments", 0) for c in content_data)
        total_shares = sum(c.get("shares", 0) for c in content_data)

        ai_scores = [c.get("ai_score", 0) for c in content_data if "ai_score" in c]
        avg_ai = sum(ai_scores) / len(ai_scores) if ai_scores else 0.0

        return ContentStats(
            total_content=total,
            published=published,
            draft=draft,
            total_views=total_views,
            total_likes=total_likes,
            total_comments=total_comments,
            total_shares=total_shares,
            avg_ai_score=avg_ai,
        )

    def _calculate_platform_performance(self, content_data: list[dict]) -> dict[str, PerformanceMetrics]:
        """计算平台性能"""
        platform_data: dict[str, list[dict]] = {}

        for c in content_data:
            platform = c.get("platform", "unknown")
            if platform not in platform_data:
                platform_data[platform] = []
            platform_data[platform].append(c)

        result = {}
        for platform, data in platform_data.items():
            impressions = sum(c.get("views", 0) for c in data)
            clicks = sum(c.get("clicks", 0) for c in data)
            ctr = clicks / impressions if impressions > 0 else 0.0

            total_engagement = sum(
                c.get("likes", 0) + c.get("comments", 0) + c.get("shares", 0)
                for c in data
            )
            engagement_rate = total_engagement / impressions if impressions > 0 else 0.0

            result[platform] = PerformanceMetrics(
                date=datetime.now().strftime("%Y-%m-%d"),
                platform=platform,
                content_count=len(data),
                impressions=impressions,
                clicks=clicks,
                ctr=ctr,
                engagement_rate=engagement_rate,
            )

        return result

    def _get_top_content(self, content_data: list[dict], limit: int = 5) -> list[ContentPerformance]:
        """获取Top内容"""
        sorted_data = sorted(
            content_data,
            key=lambda x: x.get("views", 0) + x.get("likes", 0) * 2,
            reverse=True
        )

        top = []
        for c in sorted_data[:limit]:
            top.append(ContentPerformance(
                content_id=c.get("id", ""),
                title=c.get("title", ""),
                platform=c.get("platform", "unknown"),
                published_at=c.get("published_at", ""),
                views=c.get("views", 0),
                likes=c.get("likes", 0),
                comments=c.get("comments", 0),
                shares=c.get("shares", 0),
                ai_score=c.get("ai_score", 0),
                compliance_status=c.get("compliance_status", "unknown"),
            ))

        return top

    def _generate_recommendations(
        self,
        content_stats: ContentStats,
        performance: dict[str, PerformanceMetrics],
    ) -> list[str]:
        """生成优化建议"""
        recommendations = []

        # AI味评分建议
        if content_stats.avg_ai_score < 70:
            recommendations.append("提升AI味评分低于70的内容，建议增加口语化表达和生活细节")

        # 互动率建议
        for platform, metrics in performance.items():
            if metrics.engagement_rate < 0.05:
                recommendations.append(f"{platform}平台互动率偏低，建议优化标题和开头内容")

        # 发布频率建议
        if content_stats.draft > content_stats.published:
            recommendations.append(f"草稿数量({content_stats.draft})过多，建议加快发布节奏")

        if not recommendations:
            recommendations.append("数据表现良好，继续保持当前创作策略")

        return recommendations

    def _get_default_prompt(self) -> str:
        """获取默认提示词"""
        return """你是数据分析专家，擅长从数据中提取洞察并生成可操作的建议。
核心能力：数据统计分析、内容表现分析、趋势识别、优化建议生成"""