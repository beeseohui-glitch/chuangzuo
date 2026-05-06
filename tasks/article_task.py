"""
正文生成 Task
"""

from typing import Optional
from crewai import Task


def create_article_task(
    agent,
    title: str,
    material_pack: dict,
    description: Optional[str] = None,
    expected_output: str = "小红书正文，JSON格式包含article、paragraphs、ai_flavor_score",
) -> Task:
    """
    创建正文生成任务

    Args:
        agent: 执行任务的Agent
        title: 选定的标题
        material_pack: 素材包
        description: 任务描述
        expected_output: 期望输出

    Returns:
        Task: CrewAI Task对象
    """
    task_description = description or f"""
根据选定标题 '{title}' 和素材包创作小红书正文。

要求：
- 字数300-600字
- 口语化，像朋友聊天
- 善用感叹句、反问句
- emoji 作为节奏标记，不堆砌
- 加入生活细节增加真实感
- 结构：痛点引入→产品发现→卖点展开→真实体验→互动引导
- 避免"首先、其次、最后"的工整结构
- 必须包含安全声明

输出JSON格式：
{{
  "article": "完整正文",
  "paragraphs": [
    {{"content": "段落内容", "function": "功能标注"}}
  ],
  "ai_flavor_score": 评分
}}
"""

    return Task(
        description=task_description,
        agent=agent,
        expected_output=expected_output,
    )


def create_article_validation_task(
    validator,
    min_words: int = 300,
    max_words: int = 600,
    description: Optional[str] = None,
    expected_output: str = "ArticleValidation",
) -> Task:
    """
    创建正文校验任务

    Args:
        validator: 校验器
        min_words: 最小字数
        max_words: 最大字数
        description: 任务描述
        expected_output: 期望输出

    Returns:
        Task: CrewAI Task对象
    """
    task_description = description or f"""
校验正文质量：
- 字数要求：{min_words}-{max_words}字
- AI味评分要求：≥70分
- 违禁词检查
- 段落结构检查
"""

    return Task(
        description=task_description,
        agent=validator,
        expected_output=expected_output,
    )
