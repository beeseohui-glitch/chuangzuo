# Content Agent - 项目上下文

## 项目概述
多平台 AI 内容创作 Agent 系统，基于 CrewAI 三层架构（调度层→执行层→能力层）。
支持小红书、公众号、抖音等平台的内容创作、合规审核和一键分发。

## 关键文档
- PRD文档：docs/PRD-v2.1.md
- 多租户数据模型：docs/multi-tenant-data-model.md
- Agent权限补充：docs/prd-supplement-agent-permissions.md
- 知识库权限补充：docs/prd-supplement-knowledge-permissions.md
- 前端API权限补充：docs/prd-supplement-frontend-api-permissions.md

## 技术栈

### 后端
- Agent框架：CrewAI + CrewAI Flows
- LLM：MiniMax-M2.7（OpenAI兼容接口）+ Mimo/DeepSeek/Qwen 四级降级
- Embedding：bge-large-zh-v1.5（本地部署，1024维，sentence-transformers）
- 知识库：Obsidian + pgvector
- 数据库：PostgreSQL 16 + pgvector 扩展（v0.8.2）
- 缓存：Redis 7
- 对象存储：腾讯云 COS
- API：FastAPI

### 前端
- 框架：Next.js 14（App Router + TypeScript）
- UI：shadcn/ui（base-ui 风格）+ Tailwind CSS（深色主题）
- 状态管理：Zustand（auth-store / create-store / user-store / sidebar-store）
- 数据获取：@tanstack/react-query（hooks 层封装，dev mode mock fallback）
- 图表：recharts（动态导入）

### 部署
- Docker + Docker Compose（app / postgres / redis / frontend / prometheus / grafana）

## 架构原则
1. 三层Agent架构：调度层→执行层→能力层
2. 每个Agent必须有独立的Prompt文件（prompts/目录下.md文件）
3. 每个Agent的输出必须用Pydantic模型定义
4. 多租户数据通过 PostgreSQL RLS + enterprise_id 强制隔离
5. 敏感信息通过.env管理，不硬编码

## 目录结构

### 后端（项目根目录）
```
agents/       → Agent定义
tasks/        → Task定义
crews/        → Crew定义
flows/        → Flow工作流
tools/        → 自定义工具
models/       → Pydantic数据模型 + LocalEmbedding
prompts/      → Prompt文件（.md格式）
config/       → 配置文件（LLM / Agent / Platform / Vector）
validators/   → 校验层（ResultValidator / AIFlavorScorer）
orchestrator/ → 统一调度（OrchestratorAgent / Router）
api/          → FastAPI接口
sync/         → Obsidian同步服务
monitoring/   → 监控（Prometheus指标 / 告警）
db/           → 数据库初始化脚本（init.sql / rls.sql / seed.sql）
tests/        → 测试文件
kb/           → 行业知识库数据
scripts/      → 工具脚本
```

### 数据库脚本（db/）
| 文件 | 用途 |
|------|------|
| `db/init.sql` | 完整表结构DDL + pgvector扩展 + 索引（IVFFlat vector_cosine_ops） |
| `db/rls.sql` | RLS策略（5条核心策略）+ 数据库用户（app_tenant/app_platform/app_agent）+ current_user_context() 函数 |
| `db/seed.sql` | 测试数据（2企业 + 2用户 + 18条知识库 + 20条合规规则） |

### 关键后端文件
| 文件 | 说明 |
|------|------|
| `config/llm_config.py` | LLM配置 — MiniMax/Mimo/DeepSeek/Qwen + LLMManagerConfig 四级降级管理 |
| `tools/llm_tools.py` | LLMCallTool — L1-L4 降级（重试→降级→缓存），LLMResponseParser JSON解析 |
| `tools/prompt_tools.py` | PromptManager — `{{variable}}` 替换 + 文件缓存，全局单例 `prompt_manager` |
| `tools/crewai_llm.py` | create_llm() — CrewAI 兼容 LLM 构造（LiteLLM 格式 `openai/{model}`） |
| `tools/material_tools.py` | MaterialSearchTool — 三层知识库检索 + 素材包组装，30分钟缓存 |
| `tools/compliance_tools.py` | ComplianceCheckTool — 绝对化/医疗/违禁词检测，ProhibitedWordDetector |
| `validators/ai_flavor_scorer.py` | AIFlavorScorer — 5维度（句式/口语化/结构/细节/不完美）× 20分 = 0-100 |
| `models/local_embedding.py` | LocalEmbedding 类 — bge-large-zh-v1.5 本地编码，1024维归一化向量 |
| `tools/vector_tools.py` | VectorStoreTool — pgvector 写入/检索，RLS 会话上下文，内积操作符 `<#>` |
| `tools/session_tools.py` | SessionManager — 连接池 + PostgreSQL 会话变量管理，角色→上下文映射 |
| `config/vector_config.py` | 向量配置（VectorStoreConfig / EmbeddingConfig / VectorIndexConfig） |
| `flows/xiaohongshu_flow.py` | 小红书创作 Flow — 8步工作流 + 重试/降级 + NotePack输出 |
| `flows/main_flow.py` | 主 Flow — 统一调度 + 平台路由 |
| `api/main.py` | FastAPI 入口 — CORS + 日志 + 异常处理 + 路由注册 |
| `api/auth.py` | JWT 认证 — token 生成/解析 + 测试账号 |
| `api/deps.py` | 依赖注入 — get_current_user / require_tenant / require_platform_admin |
| `api/flow_runner.py` | 异步创作编排器 — asyncio.to_thread 调用 Agent + Event 用户交互 + WebSocket 进度广播 |
| `api/routes/create.py` | 创作接口 — Flow 触发 + 任务状态 + WebSocket |
| `api/routes/tenant_knowledge.py` | 租户知识库 — CRUD + 上传 + 语义搜索 |
| `api/routes/platform_knowledge.py` | 平台管理 — 公共/行业/模板/合规 CRUD |
| `api/routes/analytics.py` | 数据看板 — 摘要 + 趋势 + 选题 + 笔记列表 |

### 前端（frontend/）
```
src/
├── app/
│   ├── login/              # 登录页（双账号：租户+平台管理员）
│   ├── 403/                # 禁止访问页
│   ├── dashboard/          # 租户工作台
│   ├── create/             # 创作中心（6步流程）
│   ├── knowledge/          # 租户知识库管理
│   ├── analytics/          # 数据看板
│   ├── settings/           # 设置（含LLM配置）
│   └── admin/              # 平台管理后台（独立布局+路由守卫）
│       ├── knowledge/
│       │   ├── public/     # 公共知识库 CRUD
│       │   └── industry/   # 行业知识库 CRUD
│       ├── templates/      # 内置模板管理
│       ├── compliance/     # 合规词库管理
│       └── stats/          # 数据统计（recharts图表）
├── components/
│   ├── ui/                 # shadcn/ui 基础组件（含 toast.tsx）
│   ├── layout/
│   │   ├── app-layout.tsx       # 租户布局（响应式 sidebar + bottom-nav）
│   │   ├── sidebar.tsx          # 租户侧边栏
│   │   ├── header.tsx           # 租户头部
│   │   ├── bottom-nav.tsx       # 移动端底部导航
│   │   ├── admin-sidebar.tsx    # 平台管理侧边栏（amber主题）
│   │   └── admin-header.tsx     # 平台管理头部
│   ├── create/             # 创作流程组件
│   └── shared/             # 通用业务组件
├── hooks/
│   ├── use-knowledge.ts    # 租户知识库 hooks
│   ├── use-analytics.ts    # 数据分析 hooks
│   ├── use-user.ts         # 用户/企业 hooks
│   ├── use-admin.ts        # 平台管理 hooks（知识/模板/合规/统计 + dev mode 可变 mock 数据）
│   └── use-media-query.ts  # 响应式断点 hooks
├── lib/
│   ├── api.ts              # API 客户端 + 各域 API 对象（含 adminApi）
│   ├── auth.ts             # 认证工具（双账号登录 + role 存储）
│   └── utils.ts            # 工具函数（cn 等）
├── stores/                 # Zustand stores
└── types/                  # TypeScript 类型定义
```

## 核心业务规则
1. 平台方是总控方，管理公共知识库、行业知识库、内置模板
2. 租户（企业用户）不可见、不可修改平台方的知识库内容
3. 租户只能管理自己的企业私有库
4. 系统在底层（Agent层面）自动调用三层知识库，对租户透明

## 开发规范
- Python 3.11+，类型注解必须
- 每个Tool继承crewai.tools.BaseTool，Pydantic v2 字段必须用 `Field()` 类级声明，私有属性用 `PrivateAttr`，`__init__` 中禁止设置未声明字段
- 前端：不使用LangChain，只用CrewAI
- 前端：base-ui 使用 `render` 而非 `asChild`，无 `forceMount`，tooltip 用 `delay` 而非 `delayDuration`
- 不跳过测试，按文件逐个开发
- HuggingFace 模型下载需设置镜像：`HF_ENDPOINT=https://hf-mirror.com`

## 前端响应式断点
- `>=1280px`（xl）：完整侧边栏 + 宽内容区
- `1024-1279px`（lg）：可折叠侧边栏
- `768-1023px`（md）：侧边栏隐藏，汉堡按钮弹出 overlay
- `<768px`：底部导航栏 + 紧凑布局

## 登录与路由守卫

### 测试账号
| 角色 | 邮箱 | 密码 | 跳转 |
|------|------|------|------|
| 租户管理员 | admin@demo.com | 123456 | /dashboard |
| 平台管理员 | admin@admin.com | admin123 | /admin |

### 路由守卫
- `localStorage.role` 存储角色标识（`"tenant"` 或 `"platform_admin"`）
- `/admin/*` 需要 `platform_admin` 角色，否则跳转 `/403`
- 登录后按 role 自动跳转对应后台
- 根路由 `/` 已登录用户按 role 分发

## Docker 环境

### 容器
| 容器 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| content-agent-db | pgvector/pgvector:pg16 | 5432 | PostgreSQL + pgvector，用户=`agent`，密码=`your_password_here` |
| content-agent-redis | redis:7-alpine | 6379 | Redis 缓存 |
| app | 自建 | 8000/8501 | FastAPI + Streamlit |
| frontend | 自建 | 3000 | Next.js |

### 数据库用户
| 用户 | 用途 | RLS |
|------|------|------|
| `agent` | 超级用户（Docker默认） | 绕过 RLS |
| `app_tenant` | 租户应用连接 | RLS 生效 |
| `app_platform` | 平台管理连接 | 绕过 RLS（ALL PRIVILEGES） |
| `app_agent` | Agent 系统连接 | RLS 生效 |

### RLS 策略（knowledge_base 表，5条）
1. `kb_platform_admin_all` — 平台管理员可读写平台级数据
2. `kb_tenant_crud` — 租户可读写自己的租户级数据
3. `kb_tenant_read_platform` — 租户可读取平台级数据
4. `kb_agent_insert` — Agent 可写入租户级数据
5. `kb_agent_read_platform` — Agent 可读取平台级数据

### 向量索引
- 索引类型：IVFFlat（MVP阶段，< 10万条）
- 操作符：vector_cosine_ops（内积 `<#>`，向量已归一化）
- lists=100
- 生产阶段切换 HNSW（m=16, ef_construction=64）

## 当前进度

### 后端开发

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 0 | 技术预研（MiniMax API / CrewAI / 项目结构） | 已完成 |
| Phase 1 | 基础设施 + 单Agent验证（Docker / pgvector / Redis / Embedding / COS） | 已完成 |
| Phase 2 | 核心创作流程（素材→标题→正文→标签→合规→输出） | 已完成 |
| Phase 3 | 知识库 + 选题Agent + Obsidian同步 + Streamlit前端 | 已完成 |
| Phase 4 | 数据分析 + 运营Agent + 数据看板 + Prompt优化 | 已完成 |
| Phase 5 | 多平台扩展（公众号 / 抖音 / 跨平台分发） | 已完成 |
| Phase 6 | FastAPI 后端接口（认证 / 创作 / 知识库 / 看板 / 权限隔离） | 已完成 |
| Phase 7 | 前后端联调（API路径对齐 / 类型对齐 / 认证流程 / 响应格式适配） | 已完成 |
| Phase 8 | API层连接真实创作Flow（flow_runner异步编排 / COS Pydantic修复 / Embedding修复 / 环境变量） | 已完成 |

**关键后端文件：**
- 7个Agent：title / article / tag / compliance / material / topic / kb / analytics / operation / wechat / douyin
- 5个Task：title / article / compliance / material / tag
- 2个Crew：xiaohongshu_crew / shared_crew
- 3个Flow：xiaohongshu_flow / main_flow + 各平台Flow
- 7个Tool：embedding / vector / llm / compliance / cos / obsidian / prompt_optimizer
- 6套测试：agents / tools / flows / validators / models / sync / monitoring / api
- 测试总数：176项（155已有 + 21 Flow端到端）

### LLM 服务封装

| 内容 | 状态 |
|------|------|
| LLM配置 | 已完成（config/llm_config.py）— MiniMax 主力 + Mimo/DeepSeek/Qwen 降级 |
| 四级降级 | 已完成（tools/llm_tools.py）— L1重试→L2指数退避→L3切换Provider→L4缓存 |
| Prompt管理 | 已完成（tools/prompt_tools.py）— `{{variable}}` 替换 + 文件缓存 |
| CrewAI集成 | 已完成（tools/crewai_llm.py）— create_llm() + LiteLLM 格式 |
| 测试 | 40项全部通过（test_llm.py） |

### Agent 更新（prompt_manager + LLM 降级）

| Agent | 文件 | 状态 |
|-------|------|------|
| 统一调度 Agent | agents/orchestrator_agent.py | 已完成 — 意图识别 + 平台路由 + 注入检测 + 限流 |
| 素材检索 Tool | tools/material_tools.py | 已完成 — 三层检索 + 灵活提取（关键词匹配）+ 30min缓存 |
| 标题 Agent | agents/title_agent.py | 已完成 — 8大策略 + 标题数量校验 + 相似度去重 |
| 正文 Agent | agents/article_agent.py | 已完成 — AI味评分重试 + 段落结构检查 |
| 标签 Agent | agents/tag_agent.py | 已完成 — 5层策略 + 数量校验 + #前缀自动修复 |
| 合规 Agent | agents/compliance_agent.py | 已完成 — P0/P1/P2 三级检查 + 降级报告 |
| AI味评分器 | validators/ai_flavor_scorer.py | 已完成 — 5维度×20分 = 0-100 |
| 合规工具 | tools/compliance_tools.py | 已完成 — 绝对化/医疗/违禁词检测 |
| ResultValidator | validators/result_validator.py | 已完成 — 素材包/标题/正文校验 |
| 测试 | tests/test_llm.py + test_orchestrator_material_title.py + test_article_tag_compliance.py | 155项全部通过 |

### 小红书创作 Flow（PRD 4.1 完整工作流）

| 内容 | 状态 |
|------|------|
| NotePack 模型 | 已完成（models/note_output.py）— NotePack + NoteMetadata 完整笔记包输出 |
| XiaohongshuFlow | 已完成（flows/xiaohongshu_flow.py）— 8步@listen链式工作流 |
| 重试机制 | 已完成 — 每步最多2次重试，总重试硬限制4次 |
| 降级路径 | 已完成 — 标题/正文/合规各有明确降级出口 |
| 质量合并评估 | 已完成 — AI味+合规合并为一步评估，避免嵌套重试 |
| 标签+合规 | 已完成 — 同一步骤中顺序执行 |
| 端到端测试 | 已完成（tests/test_xiaohongshu_flow.py）— 21项全部通过 |

**Flow 流程（8步）：**
1. `material_search`（@start）→ 2. `validate_material` → 3. `title_generation`（重试+降级）
→ 4. `validate_titles` → 5. `article_generation`（AI味重试+降级）→ 6. `quality_evaluation`（合并AI味+合规，P0重试+降级）
→ 7. `tag_and_compliance`（标签+最终合规）→ 8. `final_output`（组装NotePack）

### FastAPI 后端接口

| 内容 | 状态 |
|------|------|
| 应用骨架 | 已完成（api/main.py）— CORS + 请求日志 + 全局异常处理 |
| JWT 认证 | 已完成（api/auth.py）— token 生成/解析 + 双账号测试数据 |
| 依赖注入 | 已完成（api/deps.py）— get_current_user / require_tenant / require_platform_admin |
| 创作接口 | 已完成（api/routes/create.py + api/flow_runner.py）— 6端点 + WebSocket + 真实 Agent 异步编排 |
| 租户知识库 | 已完成（api/routes/tenant_knowledge.py）— 7端点（分类树/CRUD/上传/语义搜索） |
| 平台管理 | 已完成（api/routes/platform_knowledge.py）— 16端点（公共/行业/模板/合规 CRUD） |
| 数据看板 | 已完成（api/routes/analytics.py）— 4端点（摘要/趋势/选题/笔记列表） |
| 权限隔离 | 已完成 — tenant→platform 403，platform→tenant 403，无token 401 |
| Swagger | 已完成 — /docs 自动生成文档 |

**API 端点总计：** 33个（认证3 + 创作6 + 租户知识库7 + 平台管理16 + 看板4 + 公开1）
**后端使用内存 mock 数据，前端已对接真实 API 路径，dev mode 下自动 fallback 到 mock**

### 数据库基础设施

| 内容 | 状态 |
|------|------|
| pgvector 扩展 | 已安装（v0.8.2） |
| 8张表 | enterprises / users / knowledge_base / compliance_rules / notes / material_packs / title_history / audit_logs |
| RLS 策略 | 16条（覆盖全部8张表） |
| 3个应用用户 | app_tenant / app_platform / app_agent |
| 测试数据 | 2企业 + 2用户 + 18条知识库 + 20条合规规则 |
| 向量索引 | IVFFlat (vector_cosine_ops, lists=100) |

### Embedding 服务

| 内容 | 状态 |
|------|------|
| LocalEmbedding 类 | 已完成（models/local_embedding.py） |
| 模型 | bge-large-zh-v1.5，1024维，向量已归一化 |
| 单条编码 | encode(text) → list[float] |
| 批量编码 | batch_encode(texts) → list[list[float]] |
| 模型缓存 | HuggingFace 默认缓存（~2.4GB），离线可用 |
| 测试 | 7项全部通过（test_embedding.py） |

### 向量工具

| 内容 | 状态 |
|------|------|
| VectorStoreTool | 已完成（tools/vector_tools.py） |
| 写入 | insert() / batch_insert() |
| 检索 | search() — 内积操作符 `<#>`，支持 data_level/enterprise_id/platform_category 过滤 |
| 会话上下文 | set_session_context() — 设置 RLS 变量 |
| SessionManager | 已完成（tools/session_tools.py）— 连接池 + 角色→上下文映射 |
| 测试 | 10项全部通过（test_vector.py），含 RLS 隔离验证 |

### 前端开发

| 模块 | 内容 | 状态 |
|------|------|------|
| 初始化 | Next.js 14 + shadcn/ui + Tailwind + Zustand + React Query | 已完成 |
| 布局 | AppLayout + Sidebar（响应式overlay）+ Header + BottomNav | 已完成 |
| 登录页 | 双账号登录（租户/管理员）+ 角色路由 + 分栏品牌展示 | 已完成 |
| 工作台 | 统计卡片 + 快速开始 + 最近创作 + 趋势图 + 额度 | 已完成 |
| 创作中心 | 6步流程（输入→素材→标题→正文→标签→输出）+ WebSocket 实时交互 + 合规决策 UI | 已完成 |
| 知识库 | 分类树 + 搜索 + CRUD + 上传区域 + 语义搜索按钮 | 已完成 |
| 数据看板 | recharts图表 + 选题排名 + 策略对比 + 优化建议 | 已完成 |
| 设置 | 个人资料 + 企业信息 + LLM模型配置 | 已完成 |
| 性能 | 代码分割（dynamic import）+ standalone Docker | 已完成 |
| Docker | 前端Dockerfile（多阶段构建）+ docker-compose frontend服务 | 已完成 |
| 路由守卫 | 403页面 + admin layout角色检查 + 登录角色路由 | 已完成 |
| 平台管理后台 | 独立布局（amber主题）+ 6个管理页面 + use-admin hooks + dev mode 可变 mock 数据 | 已完成 |
| Toast 通知 | 轻量 toast 系统（components/ui/toast.tsx）+ ToastProvider | 已完成 |
| 前后端联调 | API路径对齐 + 类型对齐 + 认证流程修复 + 响应格式适配 | 已完成 |

### 前后端联调详情

**API 路径对齐（frontend/src/lib/api.ts）：**
| 模块 | 前端路径 | 后端路径 | 修复内容 |
|------|----------|----------|----------|
| 租户知识库 | `/tenant/knowledge` | `/tenant/knowledge/items` | 补充 `/items` 后缀 |
| 知识库搜索 | `GET ?q=` | `POST body:{query}` | GET→POST，query param→body |
| 创作接口 | `/tenant/create` | `/create/start` | 修正前缀 |
| 创作状态 | `/tenant/create/{id}` | `/create/{id}/status` | 修正前缀+补 `/status` |
| 数据看板 | `/tenant/analytics/*` | `/dashboard/*` | 完全重写 |
| 平台知识库 | `/platform/knowledge` | `/platform/knowledge/public` + `/industry` | 拆分为独立端点 |

**类型对齐（frontend/src/types/index.ts）：**
- `KnowledgeEntry.id`：`number` → `string`（后端返回字符串 ID）
- 所有可选字段标记为 `?`（后端不一定返回全部字段）

**认证流程修复（frontend/src/lib/auth.ts）：**
- 移除 `isDevMode()` 绕过，始终调用真实后端 `POST /api/v1/auth/login`
- 后端 `user_id` → 前端 `id` 字段映射
- 网络失败时 fallback 到 dev mode mock

**响应格式适配：**
- 知识库列表：后端返回 `{items, total, page, page_size, total_pages}`，前端提取 `items`
- 模板：后端字段 `name` → 前端 `title`
- 合规词：后端字段 `severity` → 前端 `level`，`suggestion` → `description`
- 统计数据：后端 `{content_stats, recent_creations, quota}` → 前端 `AnalyticsOverview` 映射

**Hooks 层修改：**
- `use-knowledge.ts`：分页响应提取、POST 搜索、string ID
- `use-analytics.ts`：后端响应映射、移除不存在的 `useRecommendations`
- `use-admin.ts`：拆分 public/industry 端点、字段名映射、string ID

### 创作流程交互逻辑（2026-05-07 修复）

**问题**：前端只处理 `completed`/`failed` 消息，忽略后端发送的所有中间消息，导致流程卡在素材确认环节。

**修复方案**：前端适配后端的交互式流程。

**WebSocket 消息类型：**
| 消息类型 | 含义 | 前端处理 |
|----------|------|----------|
| `progress` | 进度更新 | 保持 loading 状态 |
| `material_ready` | 素材已检索 | 更新 materialPack，停止 loading |
| `awaiting_title_selection` | 等待选择标题 | 更新 titleOptions，显示标题选择 UI |
| `title_selected` | 标题已选择 | 显示 loading，等待正文生成 |
| `article_ready` | 正文已生成 | 更新 article 和 aiScore |
| `compliance_issues` | 有合规问题 | 显示决策 UI（接受/拒绝） |
| `completed` | 流程完成 | 显示最终结果 |
| `failed` | 流程失败 | 显示错误信息 |

**前端关键修改（create-store.ts）：**
- WebSocket handler 添加对所有中间消息的处理
- 新增 `selectTitle(titleIndex)` 方法：调用后端 `/select-title` 接口
- 新增 `confirmP2Decision(accept)` 方法：调用后端 `/p2-decision` 接口

**前端组件修改：**
- `step-material.tsx`：添加对 Optional 字段的防护检查（brand/product/persona/scene/compliance 可能为 null）
- `step-title.tsx`：选择标题后调用 `selectTitle()` 通知后端继续
- `step-tags.tsx`：P0 问题时显示决策 UI，调用 `confirmP2Decision()`

**后端交互点（flow_runner.py）：**
1. 标题选择：发送 `awaiting_title_selection` → 等待 `title_event`（5分钟超时，自动选第一个）
2. P2 决策：发送 `compliance_issues` → 等待 `p2_event`（5分钟超时，自动接受）

### 素材检索优化（2026-05-07）

**问题**：知识库数据分类与代码期望不匹配（无 brand/product/scene 分类），导致素材缺失。

**修复方案**：两步提取策略。

```python
# 1. 优先从对应 category 提取
brand_entries = by_category.get("brand", [])

# 2. 如果没有，从所有结果中按关键词匹配
if not brand_entries:
    all_entries = [e for entries in by_category.values() for e in entries]
    brand_entries = [
        e for e in all_entries
        if any(kw in e.get("title", "") + e.get("content", "")
               for kw in ["品牌", "公司", "企业", "调性"])
    ]

# 3. 兜底处理（返回默认值而非 None）
if not brand_entries:
    return BrandInfo(name=product_name, tone=[], taboos=[])
```

**关键词映射：**
| 提取方法 | 匹配关键词 |
|----------|-----------|
| `_extract_brand` | 品牌、公司、企业、调性 |
| `_extract_product` | 产品、卖点、成分、功效、特点 |
| `_extract_persona` | 人群、画像、用户、目标、痛点、需求 |
| `_extract_scenes` | 场景、使用、用法、时机 |
| `_extract_compliance` | 合规、规则、禁忌、禁止、注意 |

**修改文件：**
- `tools/material_tools.py`：所有 `_extract_*` 方法添加两步提取 + 兜底处理
- `frontend/src/stores/create-store.ts`：WebSocket handler + 交互方法
- `frontend/src/components/create/step-material.tsx`：Optional 字段防护
- `frontend/src/components/create/step-title.tsx`：标题选择通知后端
- `frontend/src/components/create/step-tags.tsx`：P0 决策 UI

### 后端API现状

FastAPI 应用入口：`api/main.py`（CORS + 日志中间件 + 全局异常处理）

**认证接口：**
- `POST /api/v1/auth/login` — 邮箱+密码 → JWT token（含 user_id/enterprise_id/role/plan）
- `GET /api/v1/auth/me` — 返回当前用户信息
- `GET /api/v1/public/health` — 健康检查（无需鉴权）

**创作接口（api/routes/create.py）：**
- `POST /api/v1/create/start` — 提交创作需求，后台触发 Flow
- `GET /api/v1/create/{task_id}/status` — 查询任务状态
- `WebSocket /api/v1/create/ws/{task_id}` — 实时状态推送
- `POST /api/v1/create/{task_id}/select-title` — 用户选择标题
- `POST /api/v1/create/{task_id}/p2-decision` — P2 问题处理
- `GET /api/v1/create/{task_id}/result` — 获取最终笔记包

**租户知识库接口（api/routes/tenant_knowledge.py）：**
- `GET /api/v1/tenant/knowledge/tree` — 分类树
- `GET /api/v1/tenant/knowledge/items` — 列表+分页+搜索
- `POST /api/v1/tenant/knowledge/items` — 新增
- `PUT /api/v1/tenant/knowledge/items/{id}` — 编辑
- `DELETE /api/v1/tenant/knowledge/items/{id}` — 删除
- `POST /api/v1/tenant/knowledge/upload` — 文件上传
- `POST /api/v1/tenant/knowledge/search` — 语义搜索

**平台管理接口（api/routes/platform_knowledge.py）：**
- 公共知识库 CRUD：`/api/v1/platform/knowledge/public`
- 行业知识库 CRUD：`/api/v1/platform/knowledge/industry`
- 模板 CRUD：`/api/v1/platform/templates`
- 合规词库 CRUD：`/api/v1/platform/compliance`

**数据看板接口（api/routes/analytics.py）：**
- `GET /api/v1/dashboard/summary` — 工作台摘要
- `GET /api/v1/dashboard/trends` — 趋势数据
- `GET /api/v1/dashboard/topics` — 选题排名
- `GET /api/v1/notes` — 笔记列表

**权限隔离（已验证）：**
- `/api/v1/tenant/*` 需要 tenant 角色，平台管理员 403 ✓
- `/api/v1/platform/*` 需要 platform_admin 角色，租户 403 ✓
- 无 token 返回 401 ✓
- Swagger 文档 /docs 可访问 ✓

前端已对接真实 API 路径。创作流程已连接真实 Agent（LLM 调用 + 向量检索），知识库/看板接口仍使用内存 mock 数据，前端 dev mode 下自动 fallback 到 mock（后端不可达时）。

### 启动方式

```bash
# 1. 启动 Docker 基础设施（仅 DB + Redis）
docker start content-agent-db content-agent-redis

# 2. 后端 API（本地开发）
cd D:\chuangzuo
PYTHONIOENCODING=utf-8 HF_ENDPOINT=https://hf-mirror.com python -m uvicorn api.main:app --port 8000 --reload

# 3. 前端（另一个终端）
cd D:\chuangzuo\frontend
npm run dev          # 开发模式（端口3000/3002）
npm run build        # 生产构建

# 完整 Docker 部署（所有服务）
docker compose up -d

# 运行测试（需设置 HuggingFace 镜像）
cd D:\chuangzuo
HF_ENDPOINT=https://hf-mirror.com python -m pytest tests/test_embedding.py tests/test_vector.py -v

# 运行 Agent/LLM 测试（无需 HuggingFace）
python -m pytest tests/test_llm.py tests/test_orchestrator_material_title.py tests/test_article_tag_compliance.py -v

# 运行 Flow 端到端测试
python -m pytest tests/test_xiaohongshu_flow.py -v

# Swagger 文档
# 启动后访问 http://localhost:8000/docs
```

### 环境变量
```
# .env（完整版见 .env.example）
# 本地开发用 localhost，Docker 部署用容器名（postgres/redis）
DB_HOST=localhost
DB_PORT=5432
DB_NAME=content_agent
DB_USER=agent
DB_PASSWORD=your_password_here
REDIS_HOST=localhost
REDIS_PORT=6379
MINIMAX_API_KEY=your_key_here
MINIMAX_BASE_URL=https://api.minimax.chat/v1
MINIMAX_MODEL=MiniMax-M2.7
# LLM 降级（可选，有 API key 则启用）
MIMO_API_KEY=your_key_here
MIMO_MODEL=mimo-v2.5-pro
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_MODEL=deepseek-chat
QWEN_API_KEY=your_key_here
QWEN_MODEL=qwen-plus
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_DIM=1024
HF_ENDPOINT=https://hf-mirror.com
JWT_SECRET=your_jwt_secret_here
APP_ENV=development
APP_PORT=8000
PYTHONIOENCODING=utf-8
```
