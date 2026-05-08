# 智创笔记 — 多平台 AI 内容创作 Agent 系统

# 产品需求文档（PRD）V2.3

***

## 文档信息

| 项目 | 内容 |
| --- | --- |
| 产品名称 | 智创笔记 |
| 产品定位 | 基于多 Agent 架构的企业级多平台 AI 内容创作系统 |
| 文档版本 | V2.3（架构重构版） |
| 技术框架 | CrewAI + CrewAI Flows |
| 知识库方案 | pgvector + bge-large-zh-v1.5 本地 Embedding + Web端管理 |
| 目标平台 | 小红书（一期）、公众号/抖音（一期已实现Agent） |

### 变更说明（V2.2 → V2.3）

| 章节 | 变更类型 | 说明 |
| --- | --- | --- |
| 1.2 核心架构 | 更新 | 新增 Agent 独立调用层（BaseAgentRunner）和 Agent 间通信协议 |
| 2.3 Agent设计 | 更新 | 所有 Agent 新增 `run_standalone()` 方法，支持脱离 Flow 独立调用 |
| 2.5 Agent通信协议 | 新增 | AgentMessage / CorrectionRequest / AgentChainResult 数据结构 |
| 2.6 Agent链式执行 | 新增 | AgentChain 支持顺序执行和合规修正闭环 |
| 3.1 选题系统 | 更新 | 选题接入主流程，支持"数据驱动"模式（full）和"快速创作"模式（quick） |
| 3.2 合规闭环 | 新增 | ComplianceChain 实现 检查→修正→复检 自动闭环 |
| 4.1 Orchestrator | 更新 | 新增 AgentTool，支持 Orchestrator 直接调用任意 Agent |
| 5.1 API层 | 更新 | 新增 13 个 Agent 独立调用端点（/api/v1/agents/*） |
| 6.1 前端 | 更新 | 创作中心支持双模式、新增 AI 工具箱页面、实时 Agent 状态展示 |
| 附录A 目录结构 | 更新 | 新增 agents/chains/、models/agent_message.py |
| 附录B API端点 | 更新 | 新增 /api/v1/agents/* 系列端点 |
| 附录C 前端路由 | 更新 | 新增 /tools 页面 |

***

## 一、产品概述

### 1.1 产品定义

智创笔记是一款基于 **CrewAI 多 Agent 架构** 的企业级内容创作平台，通过"三层 Agent 分层调度 + pgvector 知识库 + 平台化知识管理"的架构，为企业提供从选题推荐到内容创作到数据分析的全链路服务。

### 1.2 核心架构：三层 Agent 分层调度

```
第一层：调度层（OrchestratorAgent + MainFlow）
  → 职责：理解意图，选择平台，路由任务
  → 实现方式：OrchestratorAgent（LLM意图识别） + MainFlow（事件驱动路由）
  → 新增：AgentTool 支持直接调用任意 Agent
  → 文件：orchestrator_agent.py + main_flow.py

第二层：执行层（平台工作流 + AgentChain）
  → 职责：按平台特性完成创作
  → 实现方式：CrewAI Flow + AgentChain（链式执行）
  → 小红书：xiaohongshu_flow.py（8步，已实现）
  → 创作链：CreationChain（quick/full 双模式）
  → 合规链：ComplianceChain（检查→修正→复检闭环）
  → 公众号：WechatArticleAgent（Agent已实现，Flow待封装）
  → 抖音：DouyinScriptAgent（Agent已实现，Flow待封装）

第三层：能力层（12个独立Agent + BaseAgentRunner）
  → 职责：提供跨平台通用专业能力
  → 实现方式：每个 Agent 均可独立调用（run_standalone）
  → 统一入口：BaseAgentRunner（Agent注册表 + 统一调用接口）
  → Agent 列表：title / article / tag / compliance / material / topic / kb / analytics / operation / wechat / douyin / orchestrator
```

### 1.3 Agent 独立调用机制

所有 Agent 均支持脱离 Flow 独立调用，通过 `BaseAgentRunner` 统一管理：

```python
# 统一调用方式
from agents.base_agent import BaseAgentRunner, AgentRequest

runner = BaseAgentRunner()
result = runner.run(AgentRequest(
    agent_name="title",
    method="generate",
    params={"topic": "护肝片", "material_pack": {}},
))
# result: AgentResponse(success=True, data=TitleOutput, duration_ms=1234)
```

**注册表**（12个Agent）：

| Agent名称 | 类 | 主要方法 |
|-----------|---|---------|
| title | TitleAgent | generate |
| article | ArticleAgent | generate |
| tag | TagAgent | generate |
| compliance | ComplianceAgent | check |
| material | MaterialAgent | search |
| topic | TopicAgent | generate_topics |
| kb | KnowledgeBaseAgent | search |
| analytics | AnalyticsAgent | generate_report |
| operation | OperationAgent | generate_plan |
| wechat | WechatArticleAgent | generate |
| douyin | DouyinScriptAgent | generate |
| orchestrator | OrchestratorAgent | route |

### 1.4 Agent 间通信协议

Agent 之间通过结构化消息传递反馈，支持合规修正闭环：

```python
# 合规反馈 → 正文修正
class ComplianceFeedback(BaseModel):
    issue_content: str          # 问题内容
    issue_location: str         # 位置（标题/正文/标签）
    severity: str               # "p0" / "p1" / "p2"
    suggestion: str             # 修改建议
    original_text: str          # 原始文本片段（精准定位）

class CorrectionRequest(BaseModel):
    feedbacks: list[ComplianceFeedback]
    target_field: str = "article"
    max_changes: int = 5
```

**合规修正流程**：
1. ComplianceAgent.check() → ComplianceReport
2. ComplianceAgent.generate_correction_request() → CorrectionRequest
3. ArticleAgent.generate_with_correction() → NoteOutput（精准修改）
4. ComplianceAgent.check() → 复检（最多2轮）

### 1.5 双模式创作流程

支持两种创作模式，均通过 WebSocket 逐步推送中间结果：

| 模式 | 步骤 | 适用场景 | 入口 |
|------|------|---------|------|
| quick | 素材→标题→正文→标签→合规 | 快速创作，已有明确方向 | `/api/v1/create/start` |
| full | 选题→素材→标题→正文→标签→合规 | 数据驱动，需要选题推荐 | `/api/v1/create/start-full` |

**WebSocket 消息协议**（两种模式共用）：

| 消息类型 | 方向 | 说明 |
|---------|------|------|
| `progress` | S→C | 进度更新（step + progress） |
| `topic_options` | S→C | 选题推荐结果（仅 full 模式） |
| `material_ready` | S→C | 素材检索完成 |
| `awaiting_title_selection` | S→C | 等待用户选择标题 |
| `title_selected` | S→C | 用户已选择标题 |
| `article_ready` | S→C | 正文生成完成 |
| `compliance_issues` | S→C | 合规检查发现 P0 问题，等待决策 |
| `completed` | S→C | 流程完成，包含完整结果 |
| `failed` | S→C | 流程失败 |

**quick 模式流程**（`api/flow_runner.py`）：
```
素材检索 → material_ready
标题生成 → awaiting_title_selection → 等待用户选择
正文生成 → article_ready
标签生成 + 合规检查 → compliance_issues（如有P0）→ completed
```

**full 模式流程**（`api/routes/create.py` `_run_full_creation_flow`）：
```
选题推荐 → topic_options
素材检索 → material_ready
标题生成 → awaiting_title_selection → 等待用户选择
正文生成 → article_ready
标签生成 + 合规检查 → compliance_issues（如有P0）→ completed
```

### 1.6 Orchestrator 智能化

OrchestratorAgent 新增 AgentTool，支持直接调用任意 Agent：

```python
# Orchestrator 可以直接调用 Agent
class AgentTool(BaseTool):
    name = "call_agent"
    description = "调用指定 Agent 执行任务"

    def _run(self, agent_name: str, method: str, params: dict) -> str:
        runner = BaseAgentRunner()
        result = runner.run(AgentRequest(
            agent_name=agent_name, method=method, params=params
        ))
        return result.model_dump_json()
```

**意图路由策略**：

| 用户意图 | 策略 | 调用的 Agent |
|---------|------|-------------|
| "帮我写一篇小红书" | 完整创作链 | 选题→素材→标题→正文→合规→标签 |
| "帮我想选题" | 仅选题 | topic.generate_topics |
| "检查一下这篇文案" | 仅合规 | compliance.check |
| "帮我改写为公众号" | 平台适配 | wechat.generate_article |
| "分析一下最近的数据" | 仅分析 | analytics.generate_report |
| "帮我搜一下相关素材" | 仅检索 | material.search |
| "把这个笔记发到多个平台" | 多平台分发 | 依次调用各平台 Agent |

***

## 二、API 层

### 2.1 Agent 独立调用端点

新增 13 个 API 端点，支持前端直接调用各 Agent：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/agents/run` | POST | 统一入口（agent_name + method + params） |
| `/api/v1/agents/title/generate` | POST | 标题生成 |
| `/api/v1/agents/article/generate` | POST | 正文生成 |
| `/api/v1/agents/tag/generate` | POST | 标签生成 |
| `/api/v1/agents/compliance/check` | POST | 合规检查 |
| `/api/v1/agents/topic/generate` | POST | 选题推荐 |
| `/api/v1/agents/material/search` | POST | 素材检索 |
| `/api/v1/agents/kb/search` | POST | 知识库搜索 |
| `/api/v1/agents/analytics/report` | POST | 数据分析 |
| `/api/v1/agents/operation/plan` | POST | 运营计划 |
| `/api/v1/agents/wechat/generate` | POST | 公众号文章 |
| `/api/v1/agents/douyin/generate` | POST | 抖音脚本 |
| `/api/v1/agents/orchestrator/route` | POST | 智能路由 |

### 2.2 创作端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/create/start` | POST | 快速创作（quick模式） |
| `/api/v1/create/start-full` | POST | 数据驱动创作（full模式，含选题推荐） |
| `/api/v1/create/{task_id}/status` | GET | 查询任务状态 |
| `/api/v1/create/{task_id}/select-title` | POST | 用户选择标题 |
| `/api/v1/create/{task_id}/p2-decision` | POST | P2问题决策 |
| `/api/v1/create/{task_id}/result` | GET | 获取最终结果 |
| `/api/v1/create/ws/{task_id}` | WS | WebSocket实时推送（两种模式共用） |

**创作流程实现**：
- quick 模式：`api/flow_runner.py` — `run_creation_flow()`，使用 XiaohongshuCrew 的各 Agent 逐步执行
- full 模式：`api/routes/create.py` — `_run_full_creation_flow()`，使用各独立 Agent 逐步执行（TopicAgent → MaterialSearchTool → TitleAgent → ArticleAgent → TagAgent → ComplianceAgent）
- 两种模式共用同一套 WebSocket 消息协议和用户交互端点（select-title、p2-decision）

***

## 三、前端

### 3.1 页面路由

| 路径 | 页面 | 说明 |
|------|------|------|
| `/dashboard` | 工作台 | 数据概览 |
| `/create` | 创作中心 | 双模式创作（quick/full） |
| `/tools` | AI工具箱 | **新增** — 独立调用12个Agent |
| `/knowledge` | 知识库 | 企业知识管理 |
| `/analytics` | 数据看板 | 内容数据分析 |
| `/settings` | 设置 | 企业/用户设置 |
| `/admin/*` | 管理后台 | 平台管理员专用 |

### 3.2 创作中心双模式

创作中心支持两种模式，通过 StepInput 组件中的模式选择器切换：

- **快速创作**（quick）：输入需求 → 素材确认 → 标题选择 → 正文创作 → 标签与合规 → 完成交付
- **数据驱动**（full）：输入需求 → 选题推荐 → 素材确认 → 标题选择 → 正文创作 → 标签与合规 → 完成交付

**关键组件**：
- `step-input.tsx`：模式选择（quick/full）+ 平台选择 + 产品/场景/风格输入
- `step-topic.tsx`：选题推荐步骤（仅 full 模式），展示 TopicAgent 返回的候选选题列表
- `create-store.ts`：Zustand 状态管理，`setMode` 切换步骤列表，WebSocket 消息处理

**状态流转**：
1. StepInput → `nextStep()` + `startCreation()` → 根据 mode 调用不同 API
2. 后端返回 `task_id`，前端连接 WebSocket 监听进度
3. WebSocket 消息驱动步骤推进和数据填充

### 3.3 AI 工具箱

新增 `/tools` 页面，提供 12 个 Agent 的独立调用界面：

- 分类筛选：创作 / 审核 / 数据 / 运营
- 参数表单：每个工具有独立的输入字段
- 实时执行：调用 `/api/v1/agents/run` 统一入口
- 结果展示：JSON 格式展示执行结果

### 3.4 实时反馈

PreviewPanel 增强：
- Agent 状态指示器：显示各 Agent 的运行状态（idle/running/completed/failed）
- 合规状态展示：实时显示合规检查结果
- 处理中指示：AI 创作进行中的 loading 状态

***

## 四、目录结构变更

```
agents/
├── base_agent.py          # 新增 — Agent 独立调用层（BaseAgentRunner）
├── agent_chain.py         # 新增 — Agent 链式执行
├── chains/                # 新增 — 创作链
│   ├── __init__.py
│   ├── creation_chain.py  # 创作链（quick/full 双模式）
│   └── compliance_chain.py # 合规修正闭环
├── orchestrator_agent.py  # 修改 — 新增 AgentTool
└── ...                    # 修改 — 所有 Agent 新增 run_standalone()

models/
├── agent_message.py       # 新增 — Agent 间通信协议
└── compliance_report.py   # 修改 — ComplianceIssue 新增 original_text

api/routes/
├── agents.py              # 新增 — 13个 Agent 独立调用端点
└── create.py              # 修改 — 新增 /start-full 端点 + _run_full_creation_flow 逐步执行

flows/
└── main_flow.py           # 修改 — 使用 OrchestratorAgent 替代关键词匹配

prompts/
├── orchestrator.md        # 修改 — 新增意图路由策略和 AgentTool 说明
└── compliance_agent.md    # 修改 — 新增 original_text 字段要求

frontend/src/
├── app/tools/             # 新增 — AI 工具箱页面
│   ├── page.tsx
│   └── tools-content.tsx
├── components/create/
│   ├── step-topic.tsx     # 新增 — 选题推荐步骤
│   └── preview-panel.tsx  # 修改 — Agent 状态展示
├── lib/
│   ├── api.ts             # 修改 — 新增 agentsApi + startFullCreation
│   └── nav-items.ts       # 修改 — 新增"工具箱"导航
└── stores/
    └── create-store.ts    # 修改 — 支持 mode 和 topic 步骤
```

***

## 五、测试覆盖

### 5.1 新增测试文件

| 测试文件 | 测试数 | 覆盖内容 |
|---------|--------|---------|
| tests/test_base_agent.py | 18 | BaseAgentRunner 初始化、Agent 注册表、run_standalone 方法、Request/Response 模型 |
| tests/test_agent_chain.py | 11 | AgentChain 顺序执行、链式 API、AgentChainResult、AgentMessage、ComplianceFeedback |
| tests/test_creation_chain.py | 8 | CreationChain quick/full 模式初始化、ComplianceChain 初始化 |
| tests/test_agent_endpoints.py | 13 | 13个 API 端点的路由存在性、前缀、标签、总数验证 |
| **合计** | **54** | |

### 5.2 测试命令

```bash
# 运行全部新增测试（54个）
pytest tests/test_base_agent.py tests/test_agent_chain.py tests/test_creation_chain.py tests/test_agent_endpoints.py -v

# 验证 Agent 注册表
python -c "from agents.base_agent import BaseAgentRunner; r = BaseAgentRunner(); print(r.list_agents())"

# 验证 Agent 独立调用
python -c "from agents.base_agent import BaseAgentRunner, AgentRequest; r = BaseAgentRunner(); print(r.list_agents())"

# 验证通信协议
python -c "from models.agent_message import AgentMessage, ComplianceFeedback, CorrectionRequest; print('OK')"
```
