"""
素材检索 Task
"""

from crewai import Task
from typing import Optional


def create_material_search_task(
    agent,
    product: str,
    scene: Optional[str] = None,
    persona: Optional[str] = None,
    description: Optional[str] = None,
    expected_output: str = "MaterialPack",
) -> Task:
    """
    创建素材检索任务

    Args:
        agent: 执行任务的Agent
        product: 产品名称
        scene: 使用场景
        persona: 人群画像
        description: 任务描述
        expected_output: 期望输出

    Returns:
        Task: CrewAI Task对象
    """
    task_description = description or f"""
从知识库检索素材并组装素材包：

产品：{product}
场景：{scene or '通用'}
人群：{persona or '通用'}

检索优先级：
1. 企业私有库 - 品牌资料、产品资料、历史爆款
2. 行业知识库 - 选题库、用户画像、痛点库
3. 公共知识库 - 平台规则、创作方法论

输出JSON格式：
{{
  "brand": {{...}},
  "product": {{...}},
  "persona": {{...}},
  "scene": [...],
  "compliance": {{...}},
  "missing_fields": [...]
}}
"""

    return Task(
        description=task_description,
        agent=agent,
        expected_output=expected_output,
    )


def create_material_validation_task(
    validator,
    description: Optional[str] = None,
    expected_output: str = "MaterialPackValidation",
) -> Task:
    """
    创建素材包校验任务

    Args:
        validator: 校验器
        description: 任务描述
        expected_output: 期望输出

    Returns:
        Task: CrewAI Task对象
    """
    task_description = description or """
校验素材包完整性：
- 品牌信息是否完整
- 产品卖点是否充足（≥2个）
- 人群画像是否明确
- 使用场景是否相关
"""

    return Task(
        description=task_description,
        agent=validator,
        expected_output=expected_output,
    )
