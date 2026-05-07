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
- LLM：MiMo（mimo-v2.5-pro / mimo-v2.5，按Agent分级使用）+ DeepSeek/Qwen 降级
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

### 前端（frontend/）
```
src/
├── app/                    # Next.js App Router 页面
├── components/
│   ├── ui/                 # shadcn/ui 基础组件
│   ├── layout/             # 布局组件（sidebar/header/bottom-nav）
│   ├── create/             # 创作流程组件（6步）
│   └── shared/             # 通用业务组件（agent-status/ai-score-ring/compliance-badge）
├── hooks/                  # React Query hooks
├── lib/
│   ├── api.ts              # API 客户端 + 各域 API 对象
│   ├── api-helpers.ts      # 响应提取工具（extractItems/extractSingle）
│   ├── auth.ts             # 认证工具
│   ├── nav-items.ts        # 共享导航常量
│   ├── score-utils.ts      # 评分颜色/标签工具
│   └── utils.ts            # 通用工具函数
├── stores/                 # Zustand stores
└── types/                  # TypeScript 类型定义
```

## 关键后端文件

| 文件 | 说明 |
|------|------|
| `config/llm_config.py` | LLM配置 — MiMo Pro/Simple 按Agent分级 + get_llm_for_agent() |
| `tools/llm_tools.py` | LLMCallTool — L1-L4 降级，LLMResponseParser JSON解析 |
| `tools/prompt_tools.py` | PromptManager — `{{variable}}` 替换 + 文件缓存 |
| `tools/crewai_llm.py` | create_llm() — CrewAI 兼容 LLM 构造 |
| `tools/cache_tools.py` | TTLCache — 泛型 TTL 缓存（LLM/Embedding/Material 共用） |
| `tools/material_tools.py` | MaterialSearchTool — 三层知识库检索 + 素材包组装 |
| `tools/compliance_tools.py` | ComplianceCheckTool — 绝对化/医疗/违禁词检测 |
| `tools/cos_tools.py` | COSBaseTool 基类 + Upload/Download/Delete |
| `tools/vector_tools.py` | VectorStoreTool — pgvector 写入/检索 |
| `tools/session_tools.py` | SessionManager — 连接池 + RLS 会话上下文 |
| `validators/ai_flavor_scorer.py` | AIFlavorScorer — 5维度×20分 = 0-100 |
| `flows/xiaohongshu_flow.py` | 小红书创作 Flow — 8步工作流 + 重试/降级 |
| `api/utils.py` | 共享工具（row_to_dict 等） |
| `api/flow_runner.py` | 异步创作编排器 — Agent + Event + WebSocket |

## 代码规范

### Agent 统一模式
所有 Agent 使用相同模式构造：
```python
from tools.prompt_tools import prompt_manager
from tools.crewai_llm import create_llm
from tools.llm_tools import LLMResponseParser

class XxxAgent:
    def __init__(self, llm_config: Optional[LLMManagerConfig] = None, ...):
        self._llm_config = llm_config
        self._agent: Optional[Agent] = None

    @property
    def agent(self) -> Agent:
        if self._agent is None:
            prompt = prompt_manager.load_prompt("xxx_agent")
            self._agent = Agent(
                role="...", goal="...", backstory=prompt,
                tools=self.tools, llm=create_llm(self._llm_config),
            )
        return self._agent

    # 解析 LLM 响应
    data = LLMResponseParser.parse_json(content)
```

### Tool 统一模式
- 继承 `crewai.tools.BaseTool`
- Pydantic v2 字段用 `Field()` 类级声明
- 私有属性用 `PrivateAttr`
- 共享初始化逻辑提取到基类（如 COSBaseTool）

### 前端 hooks 模式
```typescript
import { extractItems, extractSingle } from '@/lib/api-helpers';

// 列表提取
const items = extractItems<KnowledgeEntry>(res);

// 单条提取
const data = extractSingle<Enterprise>(res);
```

### 前端评分展示
```typescript
import { getScoreColor, getScoreBadgeColor, getScoreLabel } from '@/lib/score-utils';
```

### 前端导航
```typescript
import { NAV_ITEMS } from '@/lib/nav-items';
// sidebar 用 item.title，bottom-nav 用 item.compactTitle || item.title
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

## Docker 环境

### 容器
| 容器 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| content-agent-db | pgvector/pgvector:pg16 | 5432 | PostgreSQL + pgvector |
| content-agent-redis | redis:7-alpine | 6379 | Redis 缓存 |
| app | 自建 | 8000 | FastAPI |
| frontend | 自建 | 3000 | Next.js |

### 数据库用户
| 用户 | 用途 | RLS |
|------|------|------|
| `agent` | 超级用户（Docker默认） | 绕过 RLS |
| `app_tenant` | 租户应用连接 | RLS 生效 |
| `app_platform` | 平台管理连接 | 绕过 RLS |
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

### 后端（Phase 0-8 全部完成）
- 11个Agent：title / article / tag / compliance / material / topic / kb / analytics / operation / wechat / douyin + orchestrator
- 5个Task + 2个Crew + 3个Flow
- 33个API端点（认证3 + 创作6 + 租户知识库7 + 平台管理16 + 看板4 + 公开1）
- 8张表 + 16条RLS策略 + pgvector 向量索引
- 测试：176项（155 Agent/工具 + 21 Flow端到端）

### 前端（全部完成）
- 7个页面：登录 / 工作台 / 创作中心 / 知识库 / 数据看板 / 设置 / 管理后台
- 6步创作流程 + WebSocket 实时交互 + 合规决策 UI
- 响应式布局（xl/lg/md/sm 四档断点）
- 双角色路由守卫（租户 + 平台管理员）

### 代码质量（2026-05-07 重构）
- 删除死代码：备份文件、未使用的枚举/hook/属性
- 统一Agent模式：7个Agent全部使用 create_llm + prompt_manager
- 提取共享工具：TTLCache、COSBaseTool、row_to_dict、extractItems
- 统一配置：违禁词常量、AI模式列表、导航常量、评分工具
- 测试：154 passed + 21 flow passed，1 pre-existing failure

## 启动方式

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

# 运行测试
cd D:\chuangzuo
python -m pytest tests/test_llm.py tests/test_orchestrator_material_title.py tests/test_article_tag_compliance.py -v
python -m pytest tests/test_xiaohongshu_flow.py -v

# Swagger 文档
# 启动后访问 http://localhost:8000/docs
```

## 环境变量
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=content_agent
DB_USER=agent
DB_PASSWORD=your_password_here
REDIS_HOST=localhost
REDIS_PORT=6379
MIMO_API_KEY=your_key_here
MIMO_BASE_URL=https://token-plan-cn.xiaomimimo.com/v1
MIMO_MODEL=mimo-v2.5-pro
MIMO_SIMPLE_MODEL=mimo-v2.5
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
