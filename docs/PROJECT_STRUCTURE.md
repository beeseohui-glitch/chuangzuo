# 智创笔记 - 项目目录架构说明

> 基于 CrewAI + CrewAI Flows 的多平台 AI 内容创作 Agent 系统，支持小红书、公众号、抖音等平台的内容创作、合规审核和一键分发。

## 技术栈

| 层 | 技术 |
|---|---|
| Agent 框架 | CrewAI + CrewAI Flows |
| LLM | MiMo (mimo-v2.5-pro / mimo-v2.5) + DeepSeek/Qwen 降级 |
| Embedding | bge-large-zh-v1.5 (本地部署, 1024维) |
| 后端 API | FastAPI |
| 数据库 | PostgreSQL 16 + pgvector |
| 缓存 | Redis 7 |
| 对象存储 | 腾讯云 COS |
| 前端 | Next.js 14 + TypeScript + shadcn/ui + Tailwind CSS |
| 状态管理 | Zustand |
| 部署 | Docker + Docker Compose |

---

## 一级目录总览

```
D:\chuangzuo\
├── agents/          # Agent 定义层（14个Agent + 链式执行器）
├── api/             # FastAPI 后端接口
├── config/          # 配置模块（LLM/Agent/平台/向量）
├── crews/           # CrewAI Crew 定义
├── db/              # 数据库 SQL 脚本
├── docs/            # 产品需求文档（PRD）
├── flows/           # 流程编排（CrewAI Flows）
├── frontend/        # Next.js 前端项目
├── kb/              # 知识库行业数据
├── models/          # Pydantic 数据模型
├── monitoring/      # 监控（Prometheus 指标/告警）
├── prompts/         # Agent Prompt 模板（.md）
├── scripts/         # 运维/开发辅助脚本
├── sync/            # Obsidian 同步模块
├── tasks/           # CrewAI Task 定义
├── tests/           # 测试代码
├── tools/           # Agent 工具模块
├── validators/      # 校验器（AI味评分/结果校验）
└── vault/           # Obsidian Vault 数据目录（Docker 挂载用）
```

---

## 各目录详细说明

### agents/ — Agent 定义层

每个 Agent 对应一个内容创作或运营职能，所有 Agent 继承统一模式（`create_llm` + `prompt_manager`）。

| 文件 | 说明 |
|------|------|
| `base_agent.py` | 统一调用层（AgentRequest/Response/Runner），所有 Agent 注册到统一 registry |
| `agent_chain.py` | Agent 链式执行器（顺序执行 + 反馈循环） |
| `orchestrator_agent.py` | 统一调度 Agent（意图识别 + 平台路由 + 租户校验 + 限流） |
| `topic_agent.py` | 内容选题推荐 |
| `title_agent.py` | 小红书标题创作（8大策略） |
| `article_agent.py` | 小红书正文创作（AI味评分 + 段落结构检查） |
| `tag_agent.py` | 小红书标签策略（5层标签策略） |
| `compliance_agent.py` | 合规审核（P0/P1/P2 三级） |
| `material_agent.py` | 素材检索（pgvector 向量检索） |
| `kb_agent.py` | 知识库检索与管理 |
| `analytics_agent.py` | 数据分析报告 |
| `operation_agent.py` | 内容运营（发布计划） |
| `wechat_article_agent.py` | 公众号文章创作 |
| `douyin_script_agent.py` | 抖音短视频脚本创作 |
| `chains/creation_chain.py` | 创作链（full: 选题→素材→标题→正文→标签→合规；quick: 跳过选题） |
| `chains/compliance_chain.py` | 合规闭环链（检查→修正→重新检查，最多2轮） |

---

### api/ — FastAPI 后端接口

| 文件 | 说明 |
|------|------|
| `main.py` | FastAPI 应用入口，注册路由和中间件 |
| `auth.py` | JWT 认证逻辑 |
| `db.py` | PostgreSQL 数据库连接池 |
| `deps.py` | FastAPI 依赖注入 |
| `embedding_service.py` | Embedding 向量化服务 |
| `flow_runner.py` | 异步创作编排器（Agent + Event + WebSocket） |
| `utils.py` | 共享工具（row_to_dict 等） |
| `routes/agents.py` | 13个 Agent 独立调用端点（/api/v1/agents/*） |
| `routes/create.py` | 创作流程端点 |
| `routes/analytics.py` | 数据看板端点 |
| `routes/platform_knowledge.py` | 平台级知识库管理 |
| `routes/platform_tenants.py` | 平台级租户管理 |
| `routes/tenant_knowledge.py` | 租户级知识库管理 |

---

### config/ — 配置模块

| 文件 | 说明 |
|------|------|
| `llm_config.py` | LLM 配置 — MiPro Pro/Simple 按 Agent 分级 + get_llm_for_agent() |
| `agent_config.py` | Agent 参数配置 |
| `platform_config.py` | 平台配置（支持的平台列表、特性开关） |
| `vector_config.py` | pgvector 连接和索引配置 |

---

### crews/ — CrewAI Crew 定义

| 文件 | 说明 |
|------|------|
| `shared_crew.py` | 共享能力 Crew（跨平台通用，组装 MaterialAgent + ComplianceAgent） |
| `xiaohongshu_crew.py` | 小红书创作 Crew（组装 TitleAgent + ArticleAgent + TagAgent + ComplianceAgent + MaterialAgent） |

---

### db/ — 数据库脚本

| 文件 | 说明 |
|------|------|
| `init.sql` | 主初始化脚本（pgvector 扩展 + 8张表 + 向量索引） |
| `rls.sql` | Row Level Security 策略（多租户隔离） |
| `seed.sql` | 种子数据（测试租户、管理员账号） |
| `migrate_v2.2.sql` | v2.2 迁移脚本 |

---

### docs/ — 产品需求文档

| 文件 | 说明 |
|------|------|
| `PRD-v2.3.md` | **当前版本** — 架构重构版（Agent独立调用 + 链式编排 + 智能路由） |
| `PRD-v2.2.md` | 中间版本（代码对齐版） |
| `PRD-v2.1.md` | 早期版本（多租户权限增强） |
| `multi-tenant-data-model.md` | 多租户知识库数据模型隔离方案 |
| `new-plan.md` | 架构重构执行计划（Phase 1~7，已全部完成） |
| `prd-supplement-agent-permissions.md` | 补充：Agent 层面多租户权限控制 |
| `prd-supplement-frontend-api-permissions.md` | 补充：前端和 API 层多租户权限隔离 |
| `prd-supplement-knowledge-permissions.md` | 补充：知识库权限体系 |

---

### flows/ — 流程编排（CrewAI Flows）

| 文件 | 说明 |
|------|------|
| `main_flow.py` | 主工作流入口，使用 OrchestratorAgent 做意图识别和平台路由 |
| `xiaohongshu_flow.py` | 小红书创作 Flow（8步工作流 + 重试/降级） |

---

### frontend/ — Next.js 前端

详见 [前端目录结构](#前端目录结构frontendsrc) 章节。

---

### kb/ — 知识库行业数据

| 目录 | 说明 |
|------|------|
| `ai_industry/` | AI 行业知识（CrewAI 框架文档） |
| `health_product/` | 健康产品知识（护肝、睡眠健康） |

---

### models/ — Pydantic 数据模型

| 文件 | 说明 |
|------|------|
| `note_output.py` | 笔记输出（NoteOutput, TitleOutput, Paragraph） |
| `material_pack.py` | 素材包（BrandInfo, ProductInfo, PersonaInfo, SceneInfo, ComplianceRules） |
| `compliance_report.py` | 合规报告 |
| `knowledge_base.py` | 知识库条目 |
| `local_embedding.py` | 本地 Embedding 模型 |
| `analytics.py` | 数据分析模型 |
| `platform_content.py` | 平台内容格式 |
| `topic.py` | 选题模型 |
| `agent_message.py` | Agent 间通信（ComplianceFeedback, CorrectionRequest, AgentChainResult） |
| `validation_result.py` | 校验结果 |

---

### monitoring/ — 监控

| 文件 | 说明 |
|------|------|
| `metrics.py` | Prometheus 指标采集（LLM调用延迟、Agent执行成功率等） |
| `alerts.py` | 告警逻辑 |

---

### prompts/ — Agent Prompt 模板

每个 Agent 对应一个 `.md` 文件，使用 `{{variable}}` 模板语法。

| 文件 | 对应 Agent |
|------|-----------|
| `orchestrator.md` | OrchestratorAgent |
| `topic_agent.md` | TopicAgent |
| `title_agent.md` | TitleAgent |
| `article_agent.md` | ArticleAgent |
| `tag_agent.md` | TagAgent |
| `compliance_agent.md` | ComplianceAgent |
| `material_search.md` | MaterialAgent |
| `kb_agent.md` | KnowledgeBaseAgent |
| `analytics_agent.md` | AnalyticsAgent |
| `operation_agent.md` | OperationAgent |
| `wechat_article_agent.md` | WechatArticleAgent |
| `douyin_script_agent.md` | DouyinScriptAgent |

---

### scripts/ — 运维/开发脚本

| 文件 | 说明 |
|------|------|
| `check_env.py` | 环境检查（数据库、Redis、LLM 连通性） |
| `generate_embeddings.py` | 批量生成知识库 Embedding |
| `import_kb.py` | 导入知识库数据到 pgvector |
| `test_minimax.py` | MiniMax API 连通性测试 |
| `test_knowledge_flow.sh` | 知识库流程端到端测试 |
| `小红书项目.bat` | Windows 一键启动脚本 |

---

### sync/ — Obsidian 同步模块

| 文件 | 说明 |
|------|------|
| `obsidian_client.py` | Obsidian Vault 文件读取客户端 |
| `file_watcher.py` | 文件变更监控 |
| `knowledge_loader.py` | 知识库内容加载器 |
| `vectorizer.py` | 内容向量化并写入 pgvector |

---

### tasks/ — CrewAI Task 定义

| 文件 | 说明 |
|------|------|
| `title_task.py` | 标题生成 Task 工厂函数 |
| `article_task.py` | 正文生成 Task 工厂函数 |
| `tag_task.py` | 标签生成 Task 工厂函数 |
| `compliance_task.py` | 合规检查 Task 工厂函数 |
| `material_task.py` | 素材检索 Task 工厂函数 |

---

### tests/ — 测试代码

**顶层测试文件：**

| 文件 | 测试内容 |
|------|---------|
| `test_base_agent.py` | BaseAgentRunner 初始化、Agent 注册表、run_standalone |
| `test_agent_chain.py` | AgentChain 顺序执行、AgentMessage、ComplianceFeedback |
| `test_creation_chain.py` | CreationChain quick/full 模式、ComplianceChain |
| `test_agent_endpoints.py` | 13个 Agent API 端点路由存在性验证 |
| `test_article_tag_compliance.py` | 文章、标签、合规 Agent 功能 |
| `test_orchestrator_material_title.py` | Orchestrator 与素材/标题 Agent 联动 |
| `test_llm.py` | LLM 调用基础功能 |
| `test_xiaohongshu_flow.py` | 小红书创作流程端到端 |
| `test_embedding.py` | Embedding 向量化 |
| `test_vector.py` | pgvector 向量检索 |

**E2E 测试：** `phase0_e2e_test.py` ~ `phase5_e2e_test.py`、`full_platform_e2e_test.py`

**子目录测试：** `test_agents/`、`test_api/`、`test_flows/`、`test_models/`、`test_monitoring/`、`test_sync/`、`test_tools/`、`test_validators/`

---

### tools/ — Agent 工具模块

| 文件 | 说明 |
|------|------|
| `llm_tools.py` | LLM 四级降级服务（主LLM→重试→降级→缓存兜底） |
| `crewai_llm.py` | CrewAI LLM 集成，将降级对 Agent 透明化 |
| `prompt_tools.py` | Prompt 管理器（统一加载 + `{{variable}}` 替换 + 文件缓存） |
| `material_tools.py` | 素材检索 Tool（三层知识库检索 + 素材包组装） |
| `embedding_tools.py` | 本地 bge-large-zh-v1.5 Embedding 封装 |
| `vector_tools.py` | pgvector 向量写入和语义检索 |
| `compliance_tools.py` | 敏感词检测（绝对化用语/医疗/违禁词） |
| `cos_tools.py` | 腾讯云对象存储（Upload/Download/Delete） |
| `obsidian_tools.py` | Obsidian Markdown 读取、搜索、链接追踪 |
| `cache_tools.py` | TTL 内存缓存（泛型，LLM/Embedding/Material 共用） |
| `multi_platform_publisher.py` | 多平台一键发布分发 |
| `content_adapter.py` | 内容适配器（跨平台格式转换，预留） |
| `prompt_optimizer.py` | Prompt 优化器（去 AI 味，预留） |

---

### validators/ — 校验器

| 文件 | 说明 |
|------|------|
| `ai_flavor_scorer.py` | AI 味评分（5维度×20分 = 0-100） |
| `result_validator.py` | 通用结果校验（字数/相似度/格式） |

---

## 根目录配置文件

| 文件 | 说明 |
|------|------|
| `requirements.txt` | Python 依赖清单 |
| `Dockerfile` | 主应用镜像（python:3.11-slim + uvicorn） |
| `Dockerfile.embedding` | 独立 Embedding 服务镜像 |
| `Dockerfile.prod` | 生产环境镜像（uvicorn 2 workers） |
| `docker-compose.yml` | 开发环境编排：pgvector(Pg16) + Redis 7 + App(FastAPI:8000) + Frontend(Next.js:3000) |
| `docker-compose.prod.yml` | 生产环境编排：同上 + Prometheus(9090) + Grafana(3000) |
| `prometheus.yml` | Prometheus 抓取配置 |
| `alert_rules.yml` | 告警规则（CPU/内存/LLM延迟/Agent失败率/向量检索） |
| `init.sql` | PostgreSQL 初始化脚本（根目录副本） |
| `1.bat` / `2.bat` / `3.bat` | 代码审查导出脚本（合并关键文件到 txt） |

---

## 前端目录结构（frontend/src/）

```
src/
├── app/                          # Next.js App Router 页面
│   ├── page.tsx                  # 首页/Dashboard
│   ├── login/page.tsx            # 登录页
│   ├── dashboard/page.tsx        # 工作台/数据概览
│   ├── create/page.tsx           # 创作中心（quick/full 双模式）
│   ├── tools/page.tsx            # AI 工具箱（12个独立Agent工具）
│   ├── knowledge/page.tsx        # 知识库管理
│   ├── analytics/page.tsx        # 数据看板
│   ├── settings/page.tsx         # 设置
│   ├── notes/[id]/page.tsx       # 笔记详情
│   ├── admin/                    # 管理后台
│   │   ├── tenants/              #   租户管理
│   │   ├── templates/            #   模板管理
│   │   ├── compliance/           #   合规词库
│   │   ├── knowledge/            #   知识库管理
│   │   └── stats/                #   统计分析
│   └── 403/page.tsx              # 无权限页
│
├── components/
│   ├── ui/                       # shadcn/ui 基础组件
│   ├── layout/                   # 布局组件
│   │   ├── app-layout.tsx        #   主布局
│   │   ├── header.tsx            #   顶部导航
│   │   ├── sidebar.tsx           #   侧边栏
│   │   └── bottom-nav.tsx        #   底部导航（移动端）
│   ├── create/                   # 创作流程组件
│   │   ├── step-input.tsx        #   步骤1：创作输入
│   │   ├── step-topic.tsx        #   步骤2：选题推荐（full模式）
│   │   ├── step-material.tsx     #   步骤3：素材检索
│   │   ├── step-title.tsx        #   步骤4：标题选择
│   │   ├── step-article.tsx      #   步骤5：正文生成
│   │   ├── step-tags.tsx         #   步骤6：标签生成
│   │   ├── step-output.tsx       #   步骤7：最终输出
│   │   └── preview-panel.tsx     #   预览面板（含Agent状态）
│   └── shared/                   # 通用业务组件
│       ├── agent-status.tsx      #   Agent 执行状态展示
│       ├── ai-score-ring.tsx     #   AI 味评分环形图
│       ├── compliance-badge.tsx  #   合规状态徽章
│       └── step-indicator.tsx    #   步骤进度指示器
│
├── hooks/                        # React Query hooks（API 调用封装）
├── lib/
│   ├── api.ts                    # API 客户端 + 各域 API 对象
│   ├── api-helpers.ts            # 响应提取工具（extractItems/extractSingle）
│   ├── auth.ts                   # 认证工具
│   ├── nav-items.ts              # 共享导航常量
│   ├── score-utils.ts            # 评分颜色/标签工具
│   └── utils.ts                  # 通用工具函数（cn 等）
├── stores/                       # Zustand 状态管理
│   ├── auth-store.ts             #   认证状态
│   ├── create-store.ts           #   创作流程状态
│   └── sidebar-store.ts          #   侧边栏状态
└── types/                        # TypeScript 类型定义
```

---

## 启动方式

```bash
# 1. 启动 Docker 基础设施（仅 DB + Redis）
docker start content-agent-db content-agent-redis

# 2. 后端 API（本地开发）
cd D:\chuangzuo
PYTHONIOENCODING=utf-8 HF_ENDPOINT=https://hf-mirror.com python -m uvicorn api.main:app --port 8000 --reload

# 3. 前端（另一个终端）
cd D:\chuangzuo\frontend
npm run dev          # 开发模式（端口3000）

# 完整 Docker 部署（所有服务）
docker compose up -d

# 运行测试
python -m pytest tests/ -v

# Swagger 文档
# 启动后访问 http://localhost:8000/docs
```
