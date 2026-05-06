"""
标题生成 Task
"""

from crewai import Task
from typing import Optional


def create_title_task(
    agent,
    description: str = "生成小红书标题",
    expected_output: str = "5个不同策略的标题，JSON格式",
) -> Task:
    """
    创建标题生成任务

    Args:
        agent: 执行任务的Agent
        description: 任务描述
        expected_output: 期望输出

    Returns:
        Task: CrewAI Task对象
    """
    return Task(
        description=description,
        agent=agent,
        expected_output=expected_output,
    )


def create_title_validation_task(
    validator,
    description: str = "校验标题质量",
    expected_output: str = "ValidationResult",
) -> Task:
    """
    创建标题校验任务

    Args:
        validator: 校验器
        description: 任务描述
        expected_output: 期望输出

    Returns:
        Task: CrewAI Task对象
    """
    return Task(
        description=description,
        agent=validator,
        expected_output=expected_output,
    )
