"""
Agent 独立调用 API

- POST /api/v1/agents/run              统一调用入口
- POST /api/v1/agents/title/generate   标题生成
- POST /api/v1/agents/article/generate 正文生成
- POST /api/v1/agents/tag/generate     标签生成
- POST /api/v1/agents/compliance/check 合规检查
- POST /api/v1/agents/material/search  素材检索
- POST /api/v1/agents/topic/recommend  选题推荐
- POST /api/v1/agents/kb/search        知识库搜索
- POST /api/v1/agents/analytics/report 数据分析
- POST /api/v1/agents/operation/suggest 运营建议
- POST /api/v1/agents/wechat/generate  公众号文章
- POST /api/v1/agents/douyin/generate  抖音脚本
- POST /api/v1/agents/orchestrator/route 意图路由
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Optional

from api.deps import require_tenant, UserInfo
from agents.base_agent import BaseAgentRunner, AgentRequest, AgentResponse

router = APIRouter(prefix="/api/v1/agents", tags=["Agent 独立调用"])

# 全局 Runner 实例（懒加载 Agent）
_runner = BaseAgentRunner()


# ── 统一调用入口 ──────────────────────────────────────────


@router.post("/run", response_model=AgentResponse)
async def run_agent(
    request: AgentRequest,
    user: UserInfo = Depends(require_tenant),
):
    """统一 Agent 调用入口 - 可调用任意 Agent 的任意方法"""
    request.enterprise_id = user.enterprise_id
    return _runner.run(request)


# ── 快捷端点 ──────────────────────────────────────────────


class TitleGenerateRequest(BaseModel):
    topic: str
    material_pack: dict
    historical_titles: Optional[list[str]] = None


@router.post("/title/generate", response_model=AgentResponse)
async def title_generate(
    req: TitleGenerateRequest,
    user: UserInfo = Depends(require_tenant),
):
    """标题生成"""
    return _runner.run(AgentRequest(
        agent_name="title",
        method="generate",
        params=req.model_dump(),
        enterprise_id=user.enterprise_id,
    ))


class ArticleGenerateRequest(BaseModel):
    title: str
    material_pack: dict


@router.post("/article/generate", response_model=AgentResponse)
async def article_generate(
    req: ArticleGenerateRequest,
    user: UserInfo = Depends(require_tenant),
):
    """正文生成"""
    return _runner.run(AgentRequest(
        agent_name="article",
        method="generate",
        params=req.model_dump(),
        enterprise_id=user.enterprise_id,
    ))


class TagGenerateRequest(BaseModel):
    article: str
    title: str
    material_pack: dict


@router.post("/tag/generate", response_model=AgentResponse)
async def tag_generate(
    req: TagGenerateRequest,
    user: UserInfo = Depends(require_tenant),
):
    """标签生成"""
    return _runner.run(AgentRequest(
        agent_name="tag",
        method="generate",
        params=req.model_dump(),
        enterprise_id=user.enterprise_id,
    ))


class ComplianceCheckRequest(BaseModel):
    title: str
    article: str
    tags: list[str] = []
    brand_taboos: Optional[list[str]] = None


@router.post("/compliance/check", response_model=AgentResponse)
async def compliance_check(
    req: ComplianceCheckRequest,
    user: UserInfo = Depends(require_tenant),
):
    """合规检查"""
    return _runner.run(AgentRequest(
        agent_name="compliance",
        method="check",
        params=req.model_dump(),
        enterprise_id=user.enterprise_id,
    ))


class MaterialSearchRequest(BaseModel):
    product: str
    scene: Optional[str] = None
    persona: Optional[str] = None


@router.post("/material/search", response_model=AgentResponse)
async def material_search(
    req: MaterialSearchRequest,
    user: UserInfo = Depends(require_tenant),
):
    """素材检索"""
    return _runner.run(AgentRequest(
        agent_name="material",
        method="search",
        params={**req.model_dump(), "enterprise_id": user.enterprise_id},
        enterprise_id=user.enterprise_id,
    ))


class TopicRecommendRequest(BaseModel):
    category: str
    product: str
    brand_name: str = ""
    target_persona: str = ""
    num_topics: int = 5


@router.post("/topic/recommend", response_model=AgentResponse)
async def topic_recommend(
    req: TopicRecommendRequest,
    user: UserInfo = Depends(require_tenant),
):
    """选题推荐"""
    return _runner.run(AgentRequest(
        agent_name="topic",
        method="generate_topics",
        params=req.model_dump(),
        enterprise_id=user.enterprise_id,
    ))


class KBSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    tags: Optional[list[str]] = None
    limit: int = 10


@router.post("/kb/search", response_model=AgentResponse)
async def kb_search(
    req: KBSearchRequest,
    user: UserInfo = Depends(require_tenant),
):
    """知识库搜索"""
    return _runner.run(AgentRequest(
        agent_name="kb",
        method="search",
        params=req.model_dump(),
        enterprise_id=user.enterprise_id,
    ))


class AnalyticsReportRequest(BaseModel):
    period_start: str
    period_end: str
    content_data: list[dict] = []


@router.post("/analytics/report", response_model=AgentResponse)
async def analytics_report(
    req: AnalyticsReportRequest,
    user: UserInfo = Depends(require_tenant),
):
    """数据分析"""
    return _runner.run(AgentRequest(
        agent_name="analytics",
        method="generate_report",
        params=req.model_dump(),
        enterprise_id=user.enterprise_id,
    ))


class OperationSuggestRequest(BaseModel):
    pending_content: list[dict]
    target_platforms: list[str]
    start_date: Optional[str] = None


@router.post("/operation/suggest", response_model=AgentResponse)
async def operation_suggest(
    req: OperationSuggestRequest,
    user: UserInfo = Depends(require_tenant),
):
    """运营建议"""
    return _runner.run(AgentRequest(
        agent_name="operation",
        method="generate_schedule",
        params=req.model_dump(),
        enterprise_id=user.enterprise_id,
    ))


class WechatGenerateRequest(BaseModel):
    title: str
    material_pack: dict
    target_length: str = "medium"


@router.post("/wechat/generate", response_model=AgentResponse)
async def wechat_generate(
    req: WechatGenerateRequest,
    user: UserInfo = Depends(require_tenant),
):
    """公众号文章生成"""
    return _runner.run(AgentRequest(
        agent_name="wechat",
        method="generate_article",
        params=req.model_dump(),
        enterprise_id=user.enterprise_id,
    ))


class DouyinGenerateRequest(BaseModel):
    topic: str
    material_pack: dict
    duration_seconds: int = 60


@router.post("/douyin/generate", response_model=AgentResponse)
async def douyin_generate(
    req: DouyinGenerateRequest,
    user: UserInfo = Depends(require_tenant),
):
    """抖音脚本生成"""
    return _runner.run(AgentRequest(
        agent_name="douyin",
        method="generate_script",
        params=req.model_dump(),
        enterprise_id=user.enterprise_id,
    ))


class OrchestratorRouteRequest(BaseModel):
    user_input: str


@router.post("/orchestrator/route", response_model=AgentResponse)
async def orchestrator_route(
    req: OrchestratorRouteRequest,
    user: UserInfo = Depends(require_tenant),
):
    """意图路由"""
    return _runner.run(AgentRequest(
        agent_name="orchestrator",
        method="route",
        params={"user_input": req.user_input},
        enterprise_id=user.enterprise_id,
    ))
