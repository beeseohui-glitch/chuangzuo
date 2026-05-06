from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class AgentType(str, Enum):
    """Agent 类型"""
    ORCHESTRATOR = "orchestrator"
    MATERIAL_SEARCH = "material_search"
    TITLE = "title"
    ARTICLE = "article"
    TAG = "tag"
    COMPLIANCE = "compliance"
    TOPIC = "topic"
    KNOWLEDGE = "knowledge"
    DATA_ANALYSIS = "data_analysis"
    OPERATION = "operation"


class Platform(str, Enum):
    """目标平台"""
    XIAOHONGSHU = "xiaohongshu"
    WECHAT_PUBLIC = "wechat_public"
    DOUYIN = "douyin"
    WEIBO = "weibo"
    VIDEO号 = "video_number"


class AgentSettings(BaseModel):
    """单个 Agent 设置"""
    name: str = Field(description="Agent 名称")
    agent_type: AgentType = Field(description="Agent 类型")
    prompt_file: str = Field(description="Prompt 文件路径")
    max_retries: int = Field(default=2, description="最大重试次数")
    timeout: int = Field(default=60, description="超时秒数")
    temperature: float = Field(default=0.7, description="温度参数")
    output_model: Optional[str] = Field(default=None, description="输出 Pydantic 模型类名")


class CrewSettings(BaseModel):
    """Crew 设置"""
    name: str = Field(description="Crew 名称")
    agents: list[str] = Field(description="包含的 Agent 名称列表")
    verbose: bool = Field(default=False, description="是否输出详细日志")
    max_iterations: int = Field(default=10, description="最大迭代次数")


class FlowSettings(BaseModel):
    """Flow 设置"""
    name: str = Field(description="Flow 名称")
    steps: list[str] = Field(description="执行步骤列表")
    retry_limit: int = Field(default=4, description="总重试次数限制")
    enable_parallel: bool = Field(default=True, description="是否启用并行执行")


# Agent 级别配置
TITLE_AGENT = AgentSettings(
    name="TitleAgent",
    agent_type=AgentType.TITLE,
    prompt_file="prompts/title_agent.md",
    max_retries=2,
    timeout=60,
    output_model="TitleOutput"
)

ARTICLE_AGENT = AgentSettings(
    name="ArticleAgent",
    agent_type=AgentType.ARTICLE,
    prompt_file="prompts/article_agent.md",
    max_retries=2,
    timeout=120,
    output_model="NoteOutput"
)

TAG_AGENT = AgentSettings(
    name="TagAgent",
    agent_type=AgentType.TAG,
    prompt_file="prompts/tag_agent.md",
    max_retries=2,
    timeout=30,
    output_model="list[str]"
)

COMPLIANCE_AGENT = AgentSettings(
    name="ComplianceAgent",
    agent_type=AgentType.COMPLIANCE,
    prompt_file="prompts/compliance_agent.md",
    max_retries=2,
    timeout=60,
    output_model="ComplianceReport"
)

MATERIAL_SEARCH_AGENT = AgentSettings(
    name="MaterialSearchAgent",
    agent_type=AgentType.MATERIAL_SEARCH,
    prompt_file="prompts/material_search.md",
    max_retries=2,
    timeout=60,
    output_model="MaterialPack"
)

ORCHESTRATOR_AGENT = AgentSettings(
    name="OrchestratorAgent",
    agent_type=AgentType.ORCHESTRATOR,
    prompt_file="prompts/orchestrator.md",
    max_retries=3,
    timeout=30,
    output_model="OrchestratorOutput"
)

TOPIC_AGENT = AgentSettings(
    name="TopicAgent",
    agent_type=AgentType.TOPIC,
    prompt_file="prompts/topic_agent.md",
    max_retries=2,
    timeout=60,
    output_model="TopicListOutput"
)

# Crew 配置
XIAOHONGSHU_CREW = CrewSettings(
    name="XiaohongshuCrew",
    agents=["TitleAgent", "ArticleAgent", "TagAgent", "ComplianceAgent"],
    verbose=True,
    max_iterations=15
)

# Flow 配置
XIAOHONGSHU_FLOW = FlowSettings(
    name="XiaohongshuFlow",
    steps=[
        "orchestrator",
        "material_search",
        "validate_material",
        "title_generation",
        "validate_titles",
        "article_generation",
        "validate_article",
        "tag_generation",
        "compliance_check",
        "final_output"
    ],
    retry_limit=4
)
