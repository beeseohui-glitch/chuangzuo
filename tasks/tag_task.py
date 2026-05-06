"""
标签生成 Task
"""

from crewai import Task
from typing import Optional


def create_tag_generation_task(
    agent,
    article: str,
    title: str,
    material_pack: dict,
    description: Optional[str] = None,
    expected_output: str = "标签列表，JSON格式",
) -> Task:
    """
    创建标签生成任务

    Args:
        agent: 执行任务的Agent
        article: 正文内容
        title: 标题
        material_pack: 素材包
        description: 任务描述
        expected_output: 期望输出

    Returns:
        Task: CrewAI Task对象
    """
    product_name = material_pack.get("product", {}).get("name", "未知")
    brand_name = material_pack.get("brand", {}).get("name", "未知")

    task_description = description or f"""
根据内容生成小红书标签：

标题：{title}
正文摘要：{article[:200]}...

产品：{product_name}
品牌：{brand_name}

标签分层策略：
1. 品类大词（必选1-2个）：#护肤 #保健品
2. 功效长尾词（2-3个）：#护肝 #抗老精华
3. 场景词（2-3个）：#酒局必备 #熬夜急救
4. 热度词（1-2个）：根据当前趋势
5. 品牌词（1个）：#{brand_name}

要求：
- 总数8-10个
- 不得使用与内容无关的热门标签
- 标签必须与内容强关联

输出JSON格式：
{{"tags": ["#标签1", "#标签2", ...]}}
"""

    return Task(
        description=task_description,
        agent=agent,
        expected_output=expected_output,
    )
