"""
FastAPI 应用入口

- CORS 配置（允许 localhost:3002）
- 全局异常处理
- 请求日志中间件
- 路由注册
"""

import logging
import time
from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.auth import LoginRequest, LoginResponse, UserInfo, authenticate, create_access_token
from api.db import close_pool
from api.deps import get_current_user
from api.routes import create, tenant_knowledge, platform_knowledge, analytics

logger = logging.getLogger("api")


# ── 生命周期 ──────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_pool()


# ── 创建应用 ──────────────────────────────────────────────

app = FastAPI(
    title="智创笔记 API",
    description="多平台 AI 内容创作 Agent 系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 请求日志中间件 ────────────────────────────────────────


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000

    logger.info(
        "%s %s %d %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.1f}"
    return response


# ── 全局异常处理 ──────────────────────────────────────────


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "BAD_REQUEST",
            "message": "请求参数错误",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_ERROR",
            "message": "服务器内部错误",
        },
    )


# ── 认证接口 ──────────────────────────────────────────────


@app.post("/api/v1/auth/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """邮箱+密码登录，返回 JWT token"""
    user = await authenticate(req.email, req.password)
    if not user:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "UNAUTHORIZED", "message": "邮箱或密码错误"},
        )

    token = create_access_token(user)
    return LoginResponse(access_token=token, user=user)


@app.get("/api/v1/auth/me", response_model=UserInfo)
async def get_me(user: UserInfo = Depends(get_current_user)):
    """返回当前用户信息"""
    return user


# ── 公开接口 ──────────────────────────────────────────────


@app.get("/api/v1/public/health")
async def health():
    """健康检查（无需鉴权）"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ── 用户/企业接口 ─────────────────────────────────────────


@app.get("/api/v1/user/profile")
async def get_profile(user: UserInfo = Depends(get_current_user)):
    """当前用户资料"""
    from api.db import get_db_conn

    async with get_db_conn(enterprise_id=user.enterprise_id, is_platform_admin=True) as conn:
        row = await conn.fetchrow(
            "SELECT id, email, name, role, enterprise_id, avatar_url, created_at, updated_at "
            "FROM users WHERE id = $1",
            user.user_id,
        )
    if not row:
        return JSONResponse(status_code=404, content={"error": "NOT_FOUND", "message": "用户不存在"})
    return dict(row)


@app.get("/api/v1/enterprise/info")
async def get_enterprise_info(user: UserInfo = Depends(get_current_user)):
    """企业信息"""
    from api.db import get_db_conn

    if not user.enterprise_id:
        return {"id": None, "name": "个人用户", "plan_type": "free", "status": "active"}

    async with get_db_conn(enterprise_id=user.enterprise_id, user_role=user.role) as conn:
        row = await conn.fetchrow("SELECT * FROM enterprises WHERE id = $1", user.enterprise_id)
    if not row:
        return {"id": user.enterprise_id, "name": "未知企业", "plan_type": "free", "status": "active"}
    return dict(row)


@app.get("/api/v1/enterprise/quota")
async def get_enterprise_quota(user: UserInfo = Depends(get_current_user)):
    """企业额度"""
    from api.db import get_db_conn

    if not user.enterprise_id:
        return {"monthly_limit": 5, "used": 0, "reset_date": "2026-06-01"}

    async with get_db_conn(enterprise_id=user.enterprise_id, user_role=user.role) as conn:
        row = await conn.fetchrow(
            "SELECT quota_monthly, quota_used FROM enterprises WHERE id = $1",
            user.enterprise_id,
        )
    return {
        "monthly_limit": row["quota_monthly"] if row else 100,
        "used": row["quota_used"] if row else 0,
        "reset_date": "2026-06-01",
    }


# ── 注册路由 ──────────────────────────────────────────────

app.include_router(create.router)
app.include_router(tenant_knowledge.router)
app.include_router(platform_knowledge.router)
app.include_router(analytics.router)

# ── 启动 ──────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
