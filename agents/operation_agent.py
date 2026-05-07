"""
运营 Agent - 内容运营专家
"""

from typing import Optional
from datetime import datetime, timedelta

from crewai import Agent
from crewai.tools import BaseTool
from pydantic import BaseModel

from config import LLMManagerConfig


class PublishScheduleItem(BaseModel):
    """发布计划项"""
    content_id: str
    title: str
    platform: str
    scheduled_time: str
    priority: str  # high/medium/low


class OperationOutput(BaseModel):
    """运营输出"""
    publish_schedule: list[PublishScheduleItem]
    strategy_recommendations: list[str]
    content_matrix: dict[str, int]


from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm


class OperationAgent:
    """内容运营Agent"""

    def __init__(
        self,
        llm_config: Optional[LLMManagerConfig] = None,
        tools: Optional[list[BaseTool]] = None,
    ):
        self._llm_config = llm_config
        self.tools = tools or []
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        """获取 CrewAI Agent 实例"""
        if self._agent is None:
            prompt = prompt_manager.load_prompt("operation_agent")
            self._agent = Agent(
                role="内容运营专家",
                goal="制定发布计划、优化运营策略、提升内容表现",
                backstory=prompt,
                tools=self.tools,
                verbose=True,
                llm=create_llm(self._llm_config),
            )
        return self._agent

    def generate_schedule(
        self,
        pending_content: list[dict],
        target_platforms: list[str],
        start_date: Optional[str] = None,
    ) -> OperationOutput:
        """
        生成发布计划

        Args:
            pending_content: 待发布内容列表
            target_platforms: 目标平台列表
            start_date: 开始日期

        Returns:
            OperationOutput: 运营输出
        """
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")

        # 生成发布时间表
        publish_schedule = self._create_schedule(pending_content, target_platforms, start_date)

        # 生成策略建议
        strategy_recommendations = self._generate_strategy(pending_content, target_platforms)

        # 生成内容矩阵
        content_matrix = self._calculate_content_matrix(pending_content, target_platforms)

        return OperationOutput(
            publish_schedule=publish_schedule,
            strategy_recommendations=strategy_recommendations,
            content_matrix=content_matrix,
        )

    def _create_schedule(
        self,
        pending_content: list[dict],
        target_platforms: list[str],
        start_date: str,
    ) -> list[PublishScheduleItem]:
        """创建发布计划"""
        schedule = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")

        # 平台黄金时段
        golden_hours = {
            "xiaohongshu": [(12, 0), (20, 0), (21, 0)],
            "wechat_public": [(8, 0), (12, 0)],
            "douyin": [(12, 0), (18, 0), (19, 0)],
        }

        for i, content in enumerate(pending_content):
            platform = content.get("platform", target_platforms[0] if target_platforms else "xiaohongshu")

            # 轮转黄金时段
            hours = golden_hours.get(platform, [(20, 0)])
            hour_idx = i % len(hours)
            hour, minute = hours[hour_idx]

            # 计算日期（每天最多发布2篇）
            day_offset = i // 2
            scheduled = current_date + timedelta(days=day_offset)
            scheduled_time = scheduled.replace(hour=hour, minute=minute).strftime("%Y-%m-%d %H:%M")

            priority = content.get("priority", "medium")

            schedule.append(PublishScheduleItem(
                content_id=content.get("id", f"content_{i}"),
                title=content.get("title", f"内容{i+1}"),
                platform=platform,
                scheduled_time=scheduled_time,
                priority=priority,
            ))

        return schedule

    def _generate_strategy(
        self,
        pending_content: list[dict],
        target_platforms: list[str],
    ) -> list[str]:
        """生成策略建议"""
        recommendations = []

        # 频率建议
        weekly_count = len(pending_content)
        if weekly_count < 3:
            recommendations.append("建议每周发布至少3篇内容以保持活跃度")
        elif weekly_count > 7:
            recommendations.append("发布频率较高，注意内容质量和用户互动")

        # 平台建议
        if "xiaohongshu" in target_platforms:
            recommendations.append("小红书重点投入晚间时段（20:00-22:00）")

        if "douyin" in target_platforms:
            recommendations.append("抖音建议在12:00-14:00、18:00-20:00发布")

        # 内容类型建议
        recommendations.append("保持种草类60%、知识类25%、互动类15%的内容配比")

        return recommendations

    def _calculate_content_matrix(
        self,
        pending_content: list[dict],
        target_platforms: list[str],
    ) -> dict[str, int]:
        """计算内容矩阵"""
        total = len(pending_content)

        matrix = {"total_weekly": total}

        # 按平台统计
        platform_counts = {}
        for content in pending_content:
            platform = content.get("platform", "xiaohongshu")
            platform_counts[platform] = platform_counts.get(platform, 0) + 1

        for platform in target_platforms:
            matrix[f"{platform}_count"] = platform_counts.get(platform, 0)

        return matrix
