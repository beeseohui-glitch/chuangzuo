"""
合规检查 Task
"""

from crewai import Task
from typing import Optional


def create_compliance_check_task(
    agent,
    title: str,
    article: str,
    tags: list[str],
    brand_taboos: Optional[list[str]] = None,
    description: Optional[str] = None,
    expected_output: str = "ComplianceReport",
) -> Task:
    """
    创建合规检查任务

    Args:
        agent: 执行任务的Agent
        title: 标题
        article: 正文
        tags: 标签列表
        brand_taboos: 品牌禁忌词
        description: 任务描述
        expected_output: 期望输出

    Returns:
        Task: CrewAI Task对象
    """
    taboos_str = ", ".join(brand_taboos or [])
    tags_str = ", ".join(tags)

    task_description = description or f"""
检查以下小红书内容的合规性：

标题：{title}

正文：{article[:500]}...

标签：{tags_str}

品牌禁忌词：{taboos_str if taboos_str else '无'}

校验清单：
P0（必须修改）：广告法违禁词、医疗用语
P1（建议修改）：品牌调性偏离、产品信息不准确
P2（需人工确认）：灰色地带表述

输出JSON格式：
{{
  "status": "通过/需修改/不通过",
  "p0_issues": [...],
  "p1_issues": [...],
  "p2_issues": [...],
  "suggestions": [...]
}}
"""

    return Task(
        description=task_description,
        agent=agent,
        expected_output=expected_output,
    )


def create_compliance_fix_task(
    agent,
    compliance_report: dict,
    title: str,
    article: str,
    description: Optional[str] = None,
    expected_output: str = "修改后的内容",
) -> Task:
    """
    创建合规修复任务

    Args:
        agent: 执行任务的Agent
        compliance_report: 合规报告
        title: 原标题
        article: 原正文
        description: 任务描述
        expected_output: 期望输出

    Returns:
        Task: CrewAI Task对象
    """
    p0_issues = compliance_report.get("p0_issues", [])
    issues_str = "\n".join([f"- {issue['content']}" for issue in p0_issues])

    task_description = description or f"""
根据以下合规问题修改内容：

P0问题（必须修改）：
{issues_str}

原标题：{title}
原正文：{article[:500]}...

请修改内容以解决上述合规问题，保持内容质量。
"""

    return Task(
        description=task_description,
        agent=agent,
        expected_output=expected_output,
    )
