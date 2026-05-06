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
- LLM：MiniMax-M2.7（OpenAI兼容接口，DeepSeek/Qwen降级）
- Embedding：bge-large-zh-v1.5（本地部署，1024维）
- 知识库：Obsidian + pgvector
- 数据库：PostgreSQL 16 + pgvector 扩展
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
models/       → Pydantic数据模型
prompts/      → Prompt文件（.md格式）
config/       → 配置文件
validators/   → 校验层（ResultValidator / AIFlavorScorer）
orchestrator/ → 统一调度（OrchestratorAgent / Router）
api/          → FastAPI接口
sync/         → Obsidian同步服务
monitoring/   → 监控（Prometheus指标 / 告警）
tests/        → 测试文件
kb/           → 行业知识库数据
scripts/      → 工具脚本
```

### 前端（frontend/）
```
src/
├── app/                    # 页面
│   ├── login/              # 登录页
│   ├── dashboard/          # 工作台
│   ├── create/             # 创作中心（6步流程）
│   ├── knowledge/          # 知识库管理
│   ├── analytics/          # 数据看板
│   └── settings/           # 设置（含LLM配置）
├── components/
│   ├── ui/                 # shadcn/ui 基础组件
│   ├── layout/             # 布局（app-layout / sidebar / header / bottom-nav）
│   ├── create/             # 创作流程组件（step-input/material/title/article/tags/output / preview-panel）
│   └── shared/             # 通用业务组件（step-indicator / usage-quota / agent-status / ai-score-ring / compliance-badge）
├── hooks/                  # React Query hooks（use-knowledge / use-analytics / use-user / use-media-query）
├── lib/                    # 工具（api.ts / auth.ts / utils.ts）
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
- 每个Tool继承crewai.tools.BaseTool
- 前端：不使用LangChain，只用CrewAI
- 前端：base-ui 使用 `render` 而非 `asChild`，无 `forceMount`，tooltip 用 `delay` 而非 `delayDuration`
- 不跳过测试，按文件逐个开发

## 前端响应式断点
- `>=1280px`（xl）：完整侧边栏 + 宽内容区
- `1024-1279px`（lg）：可折叠侧边栏
- `768-1023px`（md）：侧边栏隐藏，汉堡按钮弹出 overlay
- `<768px`：底部导航栏 + 紧凑布局

## 当前进度

### 后端开发（Phase 0-5 已完成）

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 0 | 技术预研（MiniMax API / CrewAI / 项目结构） | 已完成 |
| Phase 1 | 基础设施 + 单Agent验证（Docker / pgvector / Redis / Embedding / COS） | 已完成 |
| Phase 2 | 核心创作流程（素材→标题→正文→标签→合规→输出） | 已完成 |
| Phase 3 | 知识库 + 选题Agent + Obsidian同步 + Streamlit前端 | 已完成 |
| Phase 4 | 数据分析 + 运营Agent + 数据看板 + Prompt优化 | 已完成 |
| Phase 5 | 多平台扩展（公众号 / 抖音 / 跨平台分发） | 已完成 |

**关键后端文件：**
- 7个Agent：title / article / tag / compliance / material / topic / kb / analytics / operation / wechat / douyin
- 5个Task：title / article / compliance / material / tag
- 2个Crew：xiaohongshu_crew / shared_crew
- 3个Flow：xiaohongshu_flow / main_flow + 各平台Flow
- 7个Tool：embedding / vector / llm / compliance / cos / obsidian / prompt_optimizer
- 6套测试：agents / tools / flows / validators / models / sync / monitoring / api

### 前端开发（已完成）

| 模块 | 内容 | 状态 |
|------|------|------|
| 初始化 | Next.js 14 + shadcn/ui + Tailwind + Zustand + React Query | 已完成 |
| 布局 | AppLayout + Sidebar（响应式overlay）+ Header + BottomNav | 已完成 |
| 登录页 | 邮箱/密码 + 开发模式自动填充 + 分栏品牌展示 | 已完成 |
| 工作台 | 统计卡片 + 快速开始 + 最近创作 + 趋势图 + 额度 | 已完成 |
| 创作中心 | 6步流程（输入→素材→标题→正文→标签→输出）+ 实时预览 | 已完成 |
| 知识库 | 分类树 + 搜索 + CRUD + 上传区域 + 语义搜索按钮 | 已完成 |
| 数据看板 | recharts图表 + 选题排名 + 策略对比 + 优化建议 | 已完成 |
| 设置 | 个人资料 + 企业信息 + LLM模型配置 | 已完成 |
| API联调 | React Query hooks层（mock fallback，后端就绪后移除mock即可） | 已完成 |
| 性能 | 代码分割（dynamic import）+ standalone Docker | 已完成 |
| Docker | 前端Dockerfile（多阶段构建）+ docker-compose frontend服务 | 已完成 |

### 后端API现状
当前后端仅有 2 个端点：
- `POST /api/notes` — 创建笔记
- `GET /api/health` — 健康检查

前端已预置 ~15 个API调用（knowledge / create / analytics / user / enterprise），均通过 React Query hooks 封装，dev mode 下使用 mock 数据。后端接口就绪后只需移除 mock 层。

### 启动方式

```bash
# 后端
cd D:\chuangzuo
docker-compose up -d

# 前端
cd D:\chuangzuo\frontend
npm run dev          # 开发模式（端口3000/3002）
npm run build        # 生产构建
```

### 环境变量（.env.example）
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_APP_NAME=智创笔记
```
