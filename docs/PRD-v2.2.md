# 智创笔记 — 多平台 AI 内容创作 Agent 系统

# 产品需求文档（PRD）V2.2

***

## 文档信息

| 项目 | 内容 |
| --- | --- |
| 产品名称 | 智创笔记 |
| 产品定位 | 基于多 Agent 架构的企业级多平台 AI 内容创作系统 |
| 文档版本 | V2.2（代码对齐版） |
| 技术框架 | CrewAI + CrewAI Flows |
| 知识库方案 | pgvector + bge-large-zh-v1.5 本地 Embedding + Web端管理 |
| 目标平台 | 小红书（一期）、公众号/抖音（一期已实现Agent） |
| 总工期 | 18周（含技术预研） |

### 变更说明（V2.1 → V2.2）

| 章节 | 变更类型 | 说明 |
| --- | --- | --- |
| 1.2 核心架构 | 更新 | 前端入口从 Streamlit 更新为 Next.js |
| 1.3 Crew与Flow分工 | 更新 | 小红书工作流实际为 Flow 实现（非 Crew），Crew 仅作辅助 |
| 1.5 技术栈 | 更新 | LLM 主力从 MiniMax-M2.7 更正为 MiMo（mimo-v2.5-pro/mimo-v2.5）；前端从 Streamlit 更新为 Next.js 14 + shadcn/ui + Zustand + React Query |
| 1.6 LLM 降级方案 | 更新 | 主力LLM更正为MiMo；补充Agent分级用模型配置；补充Qwen具体型号(qwen-turbo) |
| 2.3 Agent设计 | 更新 | 12个Agent全部已有实现（含公众号/抖音/运营/选题/数据分析/知识库），补充每个Agent的LLM分配和Prompt文件映射 |
| 2.4 MVP精简方案 | 更新 | 实际已实现12个Agent，非原计划的6/8/10个分阶段 |
| 3.5 pgvector索引 | 更新 | 实际使用向量内积操作符 `<#>`（非余弦距离 `<->`），向量已归一化 |
| 4.1 小红书工作流 | 更新 | 实际为8步Flow（非原描述的多步骤含选题Agent），补充耗时监控 |
| 5.1 选题系统 | 更新 | TopicAgent 已实现（一期），非"二期上线" |
| 七、去AI味策略 | 更新 | AI味评分器已适配中文（短句合并+中文阈值），补充PromptOptimizer工具 |
| 八、合规与风控 | 更新 | 补充SessionManager角色上下文映射（6角色），补充实际RLS实现 |
| 9.2 成本测算 | 更新 | LLM调用更正为MiMo API计费 |
| 十、项目里程碑 | 更新 | Phase 0-5 实际进度更正（多Phase已提前完成） |
| 附录A 目录结构 | 重写 | 完全按实际代码目录重写 |
| 附录B 数据模型 | 更新 | 补充完整8张表定义（原仅knowledge_base），补充compliance_rules/notes/material_packs/title_history/audit_logs |
| 附录C API层 | 更新 | 补充完整33个API端点（原仅3个前缀），补充WebSocket端点 |
| 附录D Agent-LLM映射表 | 新增 | 12个Agent各自的LLM分配、Prompt文件、超时配置 |
| 附录E 前端页面路由 | 新增 | 16个页面路由 + 响应式断点 + 双角色路由守卫 |
| 附录F 测试覆盖 | 新增 | 254个测试函数 + 6个E2E测试 |
| 附录G 性能基准 | 新增 | 全流程耗时监控数据（素材检索17s、标题13s、正文55s、合规196s、标签15s、总计297s） |

***

## 一、产品概述

### 1.1 产品定义

智创笔记是一款基于 **CrewAI 多 Agent 架构** 的企业级内容创作平台，通过"三层 Agent 分层调度 + pgvector 知识库 + 平台化知识管理"的架构，为企业提供从选题推荐到内容创作到数据分析的全链路服务。

### 1.2 核心架构：三层 Agent 分层调度



```
第一层：调度层（1个统一调度Agent，Flow实现）
  → 职责：理解意图，选择平台，路由任务
  → 实现方式：CrewAI Flow（事件驱动，确定性路由）
  → 文件：orchestrator_agent.py + main_flow.py

第二层：执行层（N个平台工作流，Flow实现）
  → 职责：按平台特性完成创作
  → 实现方式：CrewAI Flow（@start/@listen 事件链）
  → 小红书：xiaohongshu_flow.py（8步，已实现）
  → 公众号：WechatArticleAgent（Agent已实现，Flow待封装）
  → 抖音：DouyinScriptAgent（Agent已实现，Flow待封装）

第三层：能力层（M个共享Agent/Tool）
  → 职责：提供跨平台通用专业能力
  → 实现方式：确定性操作用Tool，需推理的用Agent
  → 素材检索（MaterialAgent + MaterialSearchTool）
  → 合规校验（ComplianceAgent + ComplianceCheckTool）
  → 选题推荐（TopicAgent）
  → 数据分析（AnalyticsAgent）
  → 知识库管理（KnowledgeBaseAgent）
```

### 1.3 Crew与Flow的分工边界

| PRD层级 | 推荐实现 | 实际实现 | 说明 |
| --- | --- | --- | --- |
| 统一调度Agent | Flow（事件驱动） | Flow（MainFlow） | 2步：route → dispatch |
| 小红书工作流 | Crew（自主协作） | **Flow（XiaohongshuFlow）** | 8步事件链，Crew仅作Agent容器辅助 |
| 素材检索 | Tool | Tool（MaterialSearchTool） | 三层知识库语义检索 |
| 合规校验 | Tool + Agent混合 | Agent（ComplianceAgent） | LLM推理 + 规则检测 |
| 数据分析 | Agent | Agent（AnalyticsAgent） | 已实现 |

> **V2.2 修正**：小红书工作流实际使用 CrewAI Flow 而非 Crew。Flow 通过 `@start()` 和 `@listen()` 装饰器实现确定性事件链，每个步骤调用独立 Agent。Crew（XiaohongshuCrew）仅作为 Agent 实例的容器，辅助 Flow 获取 Agent 引用。

### 1.4 符合 Prompt / Context / Harness 标准

每个 Agent 均按以下三维标准设计：

| 维度 | 定义 | 实现方式 |
| --- | --- | --- |
| **Prompt** | 角色定义 + 行为指令 + 思考链路 + Few-shot 示例 + 输出格式 | 独立 Prompt 文件（prompts/ 目录下 12 个 .md 文件）+ Pydantic 输出模型 |
| **Context** | 知识库内容 + 对话历史 + 用户偏好 + 检索结果 | pgvector 语义检索 + TTLCache 缓存 |
| **Harness** | 安全护栏 + 质量门禁 + 错误处理 + 重试策略 + 降级方案 + 限流 + 审计 | Tools 约束 + Flow 条件路由 + ResultValidator |

### 1.5 技术栈

| 组件 | 技术选型 | 说明 |
| --- | --- | --- |
| Agent 框架 | CrewAI + CrewAI Flows | 多 Agent 协作 + 工作流编排 |
| LLM（主力） | **MiMo**（mimo-v2.5-pro / mimo-v2.5） | 按 Agent 分级使用，OpenAI 兼容接口 |
| LLM（备用） | DeepSeek（deepseek-chat）/ Qwen（qwen-turbo） | 降级备选，同一套Prompt可切换 |
| Embedding | bge-large-zh-v1.5（sentence-transformers 本地部署） | 中文语义向量化，1024维，完全免费，无API依赖 |
| 知识管理 | Web端管理界面 + pgvector | 企业私有库/行业知识库/公共知识库三层 |
| 向量数据库 | pgvector（IVFFlat 索引，lists=100） | PostgreSQL 扩展，零额外运维 |
| 业务数据库 | PostgreSQL 16 | 向量+业务数据一体，支持RLS |
| 缓存 | Redis 7 | 会话缓存、限流计数 |
| 对象存储 | 腾讯云 COS | 企业文档、生成内容、图片素材 |
| 前端 | **Next.js 14**（App Router + TypeScript） | shadcn/ui + Tailwind CSS + 深色主题 |
| 前端状态管理 | Zustand（auth/create/user/sidebar store） | 4个独立 store |
| 前端数据获取 | @tanstack/react-query | hooks 层封装，dev mode mock fallback |
| 前端图表 | recharts（动态导入） | 数据看板可视化 |
| 部署 | Docker + Docker Compose | 4个服务：postgres / redis / app / frontend |
| 监控 | Prometheus + Grafana + pg\_stat\_statements | 系统监控与告警 |
| 认证 | JWT（HS256，24h过期）+ bcrypt | 4种角色：tenant / tenant_admin / platform_admin / platform_operator |
| 开发辅助 | Claude Code | AI 辅助编码 |

**多租户隔离技术说明**

| 技术 | 实现方式 | 作用 |
| --- | --- | --- |
| **RLS（行级安全策略）** | PostgreSQL 原生支持 | 在数据库层强制多租户数据隔离 |
| **数据分级字段** | `data_level` + `platform_category` | 区分平台级（platform）和租户级（tenant）数据 |
| **会话上下文设置** | `SET app.enterprise_id='ent_xxx'` | RLS 策略依据会话变量动态过滤数据 |
| **SessionManager** | 6种角色上下文映射 | platform_admin / platform_operator / tenant_admin / tenant / tenant_user / agent |
| **API 层双重校验** | JWT Token 中的 enterprise_id 与请求头校验 | 防止 enterprise_id 伪造攻击 |

### 1.6 LLM 降级方案

| 级别 | 触发条件 | 策略 |
| --- | --- | --- |
| L1-正常 | MiMo可用 | 全部Agent使用MiMo（按Agent分级：Pro/Simple） |
| L2-重试 | 单次调用失败 | 指数退避重试（1s/2s/4s），最多3次 |
| L3-降级 | 连续失败>5次或延迟>15s | 自动切换到备用LLM（DeepSeek/Qwen） |
| L4-缓存兜底 | 所有LLM不可用 | 使用缓存的最近成功结果 + 标注"建议人工审核" |

**Agent 分级模型配置（AGENT_MODEL_MAP）：**

| Agent | 模型 | 说明 |
| --- | --- | --- |
| orchestrator | mimo-v2.5-pro | 调度需要强推理 |
| article | mimo-v2.5-pro | 正文创作需要高质量 |
| compliance | mimo-v2.5-pro | 合规判断需要强推理 |
| analytics | mimo-v2.5-pro | 数据分析需要强推理 |
| wechat | mimo-v2.5-pro | 公众号长文需要高质量 |
| douyin | mimo-v2.5-pro | 抖音脚本需要高质量 |
| title | mimo-v2.5 | 标题生成，Simple足够 |
| tag | mimo-v2.5 | 标签生成，Simple足够 |
| topic | mimo-v2.5 | 选题推荐，Simple足够 |
| kb | mimo-v2.5 | 知识库管理，Simple足够 |
| operation | mimo-v2.5 | 运营建议，Simple足够 |

**Per-Agent 降级链**：Pro → Simple（同 base_url）→ DeepSeek → Qwen

每个Agent均设计独立Prompt文件（prompts/ 目录下），降级时只需切换LLM配置，Prompt逻辑不变。

### 1.7 服务器配置

| 资源 | 配置 | 说明 |
| --- | --- | --- |
| 服务器 | 腾讯云轻量 4核4G + 4GB Swap | Swap从2GB提升到4GB，为HNSW索引构建预留空间 |
| 系统盘 | SSD 40GB | 够用 |
| 带宽 | 3Mbps | COS 走内网，API 走外网 |
| 流量 | 300GB/月 | 够用 |
| COS | 50G 资源包 | 已有 |

***

## 二、Agent 详细设计

### 2.1 Agent 全景图



```
┌─────────────────────────────────────────────────────────────┐
│                      用户入口                                 │
│              Next.js 14 (App Router) / API                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            第一层：统一调度Agent（Flow实现）                    │
│                                                             │
│  OrchestratorAgent → MainFlow（route → dispatch）            │
│  Prompt：prompts/orchestrator.md                             │
│  LLM：mimo-v2.5-pro                                         │
│  Harness：权限校验 + 路由校验 + 限流(10/min) + Prompt注入检测  │
└──┬──────────┬──────────┬──────────┬──────────┬──────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│小红书 │ │公众号 │ │ 抖音  │ │ 微博  │ │视频号 │
│Flow  │ │Agent │ │Agent │ │(规划) │ │(规划) │
│(已实现)│ │(已实现)│ │(已实现)│ │      │ │      │
│8步   │ │      │ │      │ │      │ │      │
│事件链 │ │      │ │      │ │      │ │      │
└──┬───┘ └──────┘ └──────┘ └──────┘ └──────┘
   │
   ▼
┌─────────────────────────────────────────────────────────────┐
│            第三层：共享能力层（12个Agent + 14个Tool）          │
│                                                             │
│  Agent：                                                    │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │素材检索 │ │ 合规   │ │ 选题   │ │ 数据   │ │ 知识库  │   │
│  │Material│ │Compli- │ │Topic   │ │Analy-  │ │KB      │   │
│  │Agent   │ │ance    │ │Agent   │ │tics    │ │Agent   │   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│  ┌────────┐ ┌────────┐                                     │
│  │ 运营   │ │ 内容   │                                     │
│  │Opera-  │ │Adapter │                                     │
│  │tion    │ │        │                                     │
│  └────────┘ └────────┘                                     │
│                                                             │
│  Tool：                                                     │
│  MaterialSearchTool / ComplianceCheckTool / VectorStoreTool │
│  LLMCallTool / LocalEmbeddingTool / PromptManager           │
│  COSUploadTool / SessionManager / TTLCache / PromptOptimizer│
│  ContentAdapter / MultiPlatformPublisher / ObsidianReader    │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Agent间错误传播防控

在Agent间传递数据时增加质量校验层，防止低质量中间结果传播到下游：

```python
class ResultValidator:
    """Agent间传递数据的质量校验"""

    def validate_material_pack(self, pack: MaterialPack) -> MaterialPackValidation:
        """素材包质量校验 - 检查brand/product/persona/selling_points"""
        # 检查品牌信息、产品信息、人群画像、卖点数量(>=2)

    def validate_title_output(self, titles: list, historical_titles: list = None) -> TitleValidation:
        """标题输出质量校验 - 标题数量>=5、相似度(Jaccard>0.6)、违禁词"""
        # 标题去重 + 违禁词检测 + 历史标题对比

    def validate_article_output(self, article: NoteOutput, min_words=300, max_words=600) -> ArticleValidation:
        """正文输出质量校验 - AI味>=70、字数300-600、违禁词、段落>=3"""
```

### 2.3 每个 Agent 的 P/C/H 设计

#### Agent 1：统一调度Agent（Flow实现）

**Prompt：** `prompts/orchestrator.md`

**Context：**

| 数据项 | 来源 | 必选 |
| --- | --- | --- |
| 用户输入 | 用户对话 | 是 |
| 企业信息 | PostgreSQL（enterprises表） | 是 |
| 用户角色 | JWT Token | 是 |

**Harness：**

| 控制项 | 实现方式 |
| --- | --- |
| 权限校验 | 检查用户角色 + 企业状态 + 套餐额度 |
| 限流 | Redis 计数器，每用户每分钟最大10次 |
| 安全护栏 | 9个正则模式的Prompt注入检测 |
| 错误处理 | 意图不确定时追问，最多3轮 |
| 降级方案 | 意图识别失败时，提供平台选择菜单 |

#### Agent 2：素材检索Agent（Tool实现）

**Prompt：** `prompts/material_search.md`

**实现方式：** MaterialAgent 调用 MaterialSearchTool 执行实际检索

**Harness：**

| 控制项 | 实现方式 |
| --- | --- |
| 检索范围限制 | 三层知识库按优先级检索 |
| 隐私隔离 | PostgreSQL RLS + SessionManager 会话上下文 |
| 结果可靠性 | min_similarity=0.3 阈值过滤 |
| 缓存 | TTLCache 相同检索条件缓存30分钟 |
| 质量校验 | MaterialPackValidation 校验素材包完整性 |

#### Agent 3：标题Agent

**Prompt：** `prompts/title_agent.md`

**LLM：** mimo-v2.5（Simple）

**Harness：**

| 控制项 | 实现方式 |
| --- | --- |
| 质量门禁 | 输出必须包含>=5个标题，否则重新生成 |
| 违禁词检查 | ProhibitedWordDetector 敏感词库匹配 |
| 去重检查 | Jaccard相似度 < 0.6 |
| 重试策略 | 最多重试2次 |
| 降级方案 | 重试仍不通过时，输出已有标题 + 标注"建议人工优化" |

#### Agent 4：正文Agent

**Prompt：** `prompts/article_agent.md`

**LLM：** mimo-v2.5-pro

**Harness：**

| 控制项 | 实现方式 |
| --- | --- |
| AI味评分门禁 | AIFlavorScorer >= 70分通过，< 70分重新生成 |
| 字数检查 | 300-600字 |
| 违禁词检查 | ProhibitedWordDetector 敏感词库匹配 |
| 重试策略 | 最多重试2次，每次加入更具体的去AI味指令 |
| 降级方案 | 重试仍不通过时，输出当前版本 + 标注"建议人工润色" |

**AI味评分机制（AIFlavorScorer，已适配中文）：**

| 维度 | 分值 | 评估方法 |
| --- | --- | --- |
| 句式多样性 | 0-20分 | 长短句标准差（中文适配：短句<8字合并，阈值8-30） |
| 口语化程度 | 0-20分 | 24个语气词密度 |
| 结构模式 | 0-20分 | 14个AI工整结构正则检测（首先/其次/最后等） |
| 生活细节 | 0-20分 | 时间/地点/感官/场景/情绪 5类模式匹配 |
| 轻微不完美 | 0-20分 | 10个非正式表达模式 + 感叹句 + 口语化省略 |

> **V2.2 修正**：句式多样性评分已适配中文文本。中文句子平均16字，标准差约8，原英文阈值（30-80）导致此维度永久低分。修正后：(1) 极短片段(<8字)合并到相邻句子；(2) 阈值调整为8-30对应满分。

#### Agent 5：标签Agent

**Prompt：** `prompts/tag_agent.md`

**LLM：** mimo-v2.5（Simple）

**Harness：**

| 控制项 | 实现方式 |
| --- | --- |
| 标签数量 | >= 8个 |
| 格式检查 | 必须以 `#` 开头 |
| 重试策略 | 最多重试2次 |

#### Agent 6：合规Agent

**Prompt：** `prompts/compliance_agent.md`

**LLM：** mimo-v2.5-pro

**Harness：**

| 控制项 | 说明 |
| --- | --- |
| 规则优先级 | P0 > P1 > P2 |
| 误报处理 | 不确定时标记P2而非直接判定违规 |
| 不可修改内容 | 只校验不修改，修改由正文Agent执行 |
| 降级方案 | 解析失败时返回"需人工审核"降级报告 |

**P0 违禁词常量（ComplianceCheckTool）：**

| 类别 | 词数 | 示例 |
| --- | --- | --- |
| 绝对化用语（ABSOLUTE_WORDS） | 15 | 最、第一、顶级、绝对、100%、全网、独家、首发 |
| 医疗用语（MEDICAL_WORDS） | 16 | 治疗、治愈、疗效、药到病除、根治 |
| 保健品违禁（HEALTHCARE_PROHIBITED） | 12 | 疗效最好、包治、万能 |
| 通用违禁（GENERAL_PROHIBITED） | 8 | 最好、最强、无敌、完美 |

#### Agent 7：运营Agent

**Prompt：** `prompts/operation_agent.md`

**LLM：** mimo-v2.5（Simple）

**状态：** 已实现（`OperationAgent.generate_schedule()`）

#### Agent 8：选题Agent

**Prompt：** `prompts/topic_agent.md`

**LLM：** mimo-v2.5（Simple）

**状态：** 已实现（`TopicAgent.generate_topics()`）

> **V2.2 修正**：PRD V2.1 标记为"二期上线"，实际已在一期实现。

#### Agent 9：数据分析Agent

**Prompt：** `prompts/analytics_agent.md`

**LLM：** mimo-v2.5-pro

**状态：** 已实现（`AnalyticsAgent.generate_report()`）

#### Agent 10：知识库管理Agent

**Prompt：** `prompts/kb_agent.md`

**LLM：** mimo-v2.5（Simple）

**状态：** 已实现（`KnowledgeBaseAgent.search()` + `retrieve_context()`）

#### Agent 11：公众号Agent

**Prompt：** `prompts/wechat_article_agent.md`

**LLM：** mimo-v2.5-pro

**状态：** 已实现（`WechatArticleAgent.generate_article()`）

> **V2.2 新增**：PRD V2.1 未列出此Agent。

#### Agent 12：抖音Agent

**Prompt：** `prompts/douyin_script_agent.md`

**LLM：** mimo-v2.5-pro

**状态：** 已实现（`DouyinScriptAgent.generate_script()`）

> **V2.2 新增**：PRD V2.1 未列出此Agent。

### 2.4 MVP阶段Agent精简方案

> **V2.2 修正**：实际开发进度已超出原计划。以下为实际状态。

| 阶段 | 原计划Agent | 实际状态 |
| --- | --- | --- |
| Phase 1-2（MVP） | 统一调度、素材检索、标题、正文、标签、合规 | **已完成** + 选题、知识库、运营、数据分析、公众号、抖音 |
| Phase 3 | + 选题、知识库管理 | **已提前完成**（Phase 1-2 期间已实现） |
| Phase 4 | + 数据分析、运营 | **已提前完成** |
| Phase 5 | 全部上线 | **12个Agent全部已实现** |

***

## 三、知识库体系

### 3.1 三层知识库

| 层级 | 内容 | 维护方 | 存储方式 |
| --- | --- | --- | --- |
| 公共知识库 | 平台规则、创作方法论、合规通用规则 | 平台方 | pgvector（data_level='platform', platform_category='public'） |
| 行业知识库 | 各行业选题库、用户画像、痛点库、爆款拆解 | 平台方预设 | pgvector（data_level='platform', platform_category='industry'） |
| 企业私有库 | 品牌资料、产品资料、历史笔记、竞品信息 | 企业自维护 | pgvector + COS（data_level='tenant'） |

**3.1.1 知识库访问权限矩阵**（与 V2.1 相同，此处不再重复）

### 3.2 双轨知识管理方案

> **V2.2 修正**：原"Obsidian同步"路径已弱化，Web端管理界面为主要路径。

**路径A：Web端管理界面（主要）**

前端 Next.js 提供完整的知识管理界面：
- 租户端：`/knowledge` — 企业私有库 CRUD + 语义搜索
- 平台端：`/admin/knowledge/*` — 公共/行业/模板 CRUD

**路径B：API直接调用**

通过 REST API 进行知识管理：
- `POST /api/v1/tenant/knowledge/items` — 创建知识条目
- `POST /api/v1/tenant/knowledge/search` — 语义搜索
- `POST /api/v1/tenant/knowledge/upload` — 文件上传（COS + 入库）

### 3.5 pgvector 索引策略

| 阶段 | 数据规模 | 索引类型 | 参数配置 | 说明 |
| --- | --- | --- | --- | --- |
| MVP阶段 | < 10万条 | IVFFlat | lists=100, vector_cosine_ops | 当前使用 |
| 生产阶段 | > 10万条 | HNSW | m=16, ef_construction=64 | 待切换 |

**实际使用的向量操作：**

```sql
-- 使用内积操作符（向量已归一化）
ORDER BY embedding <#> '[...]'::vector

-- 索引定义
CREATE INDEX idx_knowledge_embedding
ON knowledge_base USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

> **V2.2 修正**：实际使用内积操作符 `<#>`（与余弦距离 `<->` 在归一化向量上等价，但性能更好）。

### 3.7 素材检索 Agent 的三层检索权限控制

**实际实现（MaterialSearchTool.search()）：**

```python
# 第一层：企业私有库（top_k=10, min_similarity=0.3）
private_results = vector_store.search(
    embedding=query_embedding, top_k=10,
    data_level="tenant", enterprise_id=enterprise_id, min_similarity=0.3
)

# 第二层：行业知识库（top_k=5, min_similarity=0.3）
industry_results = vector_store.search(
    embedding=query_embedding, top_k=5,
    data_level="platform", platform_category="industry", min_similarity=0.3
)

# 第三层：公共知识库（top_k=5, min_similarity=0.3）
public_results = vector_store.search(
    embedding=query_embedding, top_k=5,
    data_level="platform", platform_category="public", min_similarity=0.3
)
```

### 3.8 平台方知识库管理

**平台后台页面路由（已实现）：**

| 路由 | 页面 | 说明 |
| --- | --- | --- |
| `/admin` | 管理后台首页 | 平台管理员入口 |
| `/admin/knowledge/public` | 公共知识管理 | 平台规则/合规规则 CRUD |
| `/admin/knowledge/industry` | 行业知识管理 | 选题库/用户画像 CRUD |
| `/admin/templates` | 模板管理 | 内置模板 CRUD |
| `/admin/compliance` | 合规规则管理 | 违禁词/合规规则 CRUD |
| `/admin/stats` | 数据统计 | 知识条目统计 |

***

## 四、工作流设计

### 4.1 小红书创作工作流

**实际实现（XiaohongshuFlow，8步事件链）：**

```
用户输入（product, scene, persona, enterprise_id）
    ↓
[Step 1: material_search] @start()
    → MaterialAgent.search() → 三层知识库检索 → MaterialPack
    ↓
[Step 2: validate_material] @listen(material_search)
    → ResultValidator.validate_material_pack() → 非关键失败继续
    ↓
[Step 3: title_generation] @listen(validate_material)
    → TitleAgent.generate() → 5个标题 → TitleOutput
    → 校验失败重试1次，仍失败则降级
    ↓
[Step 4: validate_titles] @listen(title_generation)
    → 记录警告，不阻断流程
    ↓
[Step 5: article_generation] @listen(validate_titles)
    → ArticleAgent.generate() → 正文 + AI味评分 → NoteOutput
    → AI味 < 70 重试，最多2次
    ↓
[Step 6: quality_evaluation] @listen(article_generation)
    → ComplianceAgent.check() → 合规报告
    → P0问题重试正文生成，最多2次
    → 合并评估：AI味 + 合规
    ↓
[Step 7: tag_and_compliance] @listen(quality_evaluation)
    → TagAgent.generate() → 标签列表
    → ComplianceAgent.check() → 最终合规检查
    ↓
[Step 8: final_output] @listen(tag_and_compliance)
    → 组装 NotePack（title + article + paragraphs + tags + compliance_report + metadata）
```

**关键设计：**

*   每个环节最多重试2次（`MAX_STEP_RETRIES = 2`）
*   总重试硬限制4次（`MAX_TOTAL_RETRIES = 4`）
*   每个环节有明确降级出口
*   每个步骤均有耗时监控（`[耗时]` 前缀日志）

**关键常量：**

```python
MAX_STEP_RETRIES = 2       # 单步最大重试
MAX_TOTAL_RETRIES = 4      # 全流程总重试硬限制
AI_FLAVOR_THRESHOLD = 70   # AI味评分阈值
```

### 4.2 跨平台一键分发工作流（二期）



> 与 V2.1 相同。MultiPlatformPublisher 已实现 mock 模式。

***

## 五、选题系统

### 5.1 五条选题来源线

| 来源 | 实现方式 | 优先级 | 状态 |
| --- | --- | --- | --- |
| 行业预设选题库 | pgvector 语义检索 | P0 | **已实现**（TopicAgent） |
| 实时热点与节点日历 | 预设全年节点 + 热点API | P0 | 待实现 |
| 竞品爆款追踪 | 竞品笔记监测 + 自动拆解 | P1 | 待实现 |
| 历史数据反哺 | 企业笔记数据分析 | P1 | **已实现**（AnalyticsAgent） |
| AI组合生成 | 产品×人群×场景×热点 | P2 | **已实现**（TopicAgent.generate_topics()） |

> **V2.2 修正**：TopicAgent 和 AnalyticsAgent 均已在一期实现，非"Phase 3/4"。

***

## 六、防同质化策略

与 V2.1 相同。

***

## 七、去AI味策略

| 维度 | 具体措施 |
| --- | --- |
| 语言 | 口语化语气词（24个）、避免工整排比（14个正则模式）、句式长短不一 |
| 内容 | 加入生活细节、允许轻微不完美表达（10个非正式模式） |
| 结构 | 不同笔记使用不同段落结构 |
| 检测 | AIFlavorScorer 5维度×20分 = 0-100，< 70分自动重新生成 |
| 优化工具 | PromptOptimizer（remove_ai_flavor / make_more_conversational / add_emoji_as_rhythm） |
| 中文适配 | 短句合并(<8字) + 句式多样性阈值调整(8-30) |

> **V2.2 修正**：补充 PromptOptimizer 工具和中文适配说明。

***

## 八、合规与风控

### 8.1 多层合规防护

与 V2.1 相同。

### 8.2 Harness 设计汇总

与 V2.1 相同，补充：

| 控制项 | 实现位置 | 说明 |
| --- | --- | --- |
| SessionManager | tools/session_tools.py | 6种角色上下文映射（platform_admin/platform_operator/tenant_admin/tenant/tenant_user/agent） |
| PromptOptimizer | tools/prompt_optimizer.py | AI味去除 + 语气口语化 + emoji节奏标记 |

### 8.3 安全与合规深层保障

**RLS 策略**（与 V2.1 相同）

**SessionManager 角色上下文映射（ROLE_CONTEXT_MAP）：**

| 角色 | enterprise_id | is_platform_admin | is_agent |
| --- | --- | --- | --- |
| platform_admin | NULL | true | false |
| platform_operator | NULL | true | false |
| tenant_admin | 当前企业 | false | false |
| tenant | 当前企业 | false | false |
| tenant_user | 当前企业 | false | false |
| agent | 目标企业 | false | true |

***

## 九、商业模式

### 9.1 版本与定价

与 V2.1 相同。

### 9.2 成本测算

| 成本项 | 估算方式 | 预估范围 |
| --- | --- | --- |
| **MiMo API调用** | 每篇笔记约8-10次LLM调用 | 按Token计费 |
| Embedding（bge-large-zh-v1.5） | 本地运行，无API调用 | 免费 |
| 服务器 | 腾讯云轻量4核4G | 固定月费 |
| COS存储 | 50G资源包 | 固定月费 |
| 备用LLM | DeepSeek/Qwen降级调用 | 按Token计费（仅降级时产生） |

> **V2.2 修正**：LLM从 MiniMax 更正为 MiMo。

***

## 十、项目里程碑

### Phase 0：技术预研（第1-2周）— **已完成**

### Phase 1：基础设施 + 单Agent验证（第3-4周）— **已完成**

### Phase 2：核心创作流程（第5-7周）— **已完成**

### Phase 3：知识库 + 前端 + 选题（第8-10周）— **已完成**

### Phase 4：数据 + 优化（第11-13周）— **已完成**

### Phase 5：多平台扩展（第14-18周）— **部分完成**

**实际完成情况汇总：**

| 交付项 | 状态 | 说明 |
| --- | --- | --- |
| 12个Agent全部实现 | 已完成 | 含公众号/抖音/运营/选题/数据分析/知识库 |
| 5个Task + 2个Crew + 3个Flow | 已完成 | XiaohongshuFlow(8步) + MainFlow(2步) |
| 33个API端点 | 已完成 | 认证6 + 创作6 + 租户知识库8 + 平台管理16 + 看板4 + 公开1 |
| 8张数据库表 + RLS策略 | 已完成 | 含审计日志 |
| Next.js 前端（16个页面） | 已完成 | 含响应式布局 + 双角色路由守卫 |
| 测试：254个 + 6个E2E | 已完成 | 17个测试文件 |
| 耗时监控 | 已完成 | 全流程8步耗时追踪 |
| AI味评分中文适配 | 已完成 | 短句合并 + 阈值调整 |
| 公众号/抖音创作Flow | 待完成 | Agent已实现，Flow封装待做 |
| 跨平台一键分发 | 待完成 | MultiPlatformPublisher mock模式 |

***

## 十一、开发指南

与 V2.1 相同，补充：

### 11.2 实际开发顺序

```
Step 1-4：项目结构 + 模型 + 配置 + Prompt → 已完成
Step 5：工具开发（14个Tool）→ 已完成
Step 6：校验层（2个Validator）→ 已完成
Step 7：Agent定义（12个Agent）→ 已完成
Step 8-9：Task + Crew → 已完成
Step 10：Flow工作流（3个Flow）→ 已完成
Step 11：统一调度（OrchestratorAgent + MainFlow）→ 已完成
Step 12：前端（Next.js 16个页面）→ 已完成
Step 13-14：同步服务 + 监控 → 已完成
Step 15：API接口（33个端点）→ 已完成
Step 16：Docker配置 → 已完成
Step 17：测试（254个 + 6个E2E）→ 已完成
```

***

## 十二、监控与运维

与 V2.1 相同。

***

## 十三、成功指标

与 V2.1 相同。

***

## 十四、风险与应对

与 V2.1 相同。

***

## 十五、产品研究计划

与 V2.1 相同。

***

## 附录A：项目目录结构（实际代码）



```
chuangzuo/
├── .claude/
│   ├── CLAUDE.md                    # 项目上下文
│   ├── rules/                       # 开发规则（iterative-development.md, tdd.md）
│   └── plans/                       # 开发计划
├── agents/                          # 12个Agent定义
│   ├── orchestrator_agent.py        # 统一调度Agent
│   ├── material_agent.py            # 素材检索Agent
│   ├── title_agent.py               # 标题Agent
│   ├── article_agent.py             # 正文Agent
│   ├── tag_agent.py                 # 标签Agent
│   ├── compliance_agent.py          # 合规Agent
│   ├── topic_agent.py               # 选题Agent
│   ├── kb_agent.py                  # 知识库Agent
│   ├── analytics_agent.py           # 数据分析Agent
│   ├── operation_agent.py           # 运营Agent
│   ├── wechat_article_agent.py      # 公众号Agent
│   └── douyin_script_agent.py       # 抖音Agent
├── tools/                           # 14个工具
│   ├── material_tools.py            # MaterialSearchTool — 三层知识库检索
│   ├── llm_tools.py                 # LLMCallTool — L1-L4降级
│   ├── crewai_llm.py                # create_llm() — CrewAI兼容LLM构造
│   ├── vector_tools.py              # VectorStoreTool — pgvector写入/检索
│   ├── embedding_tools.py           # LocalEmbeddingTool — bge-large-zh-v1.5
│   ├── compliance_tools.py          # ComplianceCheckTool — 违禁词检测
│   ├── prompt_tools.py              # PromptManager — Prompt加载+变量替换
│   ├── cache_tools.py               # TTLCache — 泛型TTL缓存
│   ├── session_tools.py             # SessionManager — RLS会话上下文
│   ├── cos_tools.py                 # COSBaseTool — 腾讯云COS操作
│   ├── obsidian_tools.py            # Obsidian读取/搜索/链接追踪
│   ├── content_adapter.py           # ContentAdapter — 多平台内容适配
│   ├── multi_platform_publisher.py  # MultiPlatformPublisher — 一键分发(mock)
│   └── prompt_optimizer.py          # PromptOptimizer — AI味去除
├── models/                          # 9个Pydantic数据模型
│   ├── material_pack.py             # MaterialPack, BrandInfo, ProductInfo, PersonaInfo, SceneInfo
│   ├── note_output.py               # NoteOutput, TitleOutput, NotePack, NoteMetadata, TitleOption, Paragraph
│   ├── compliance_report.py         # ComplianceReport, ComplianceStatus, ComplianceIssue
│   ├── validation_result.py         # ValidationResult, MaterialPackValidation, TitleValidation, ArticleValidation
│   ├── topic.py                     # TopicIdea, TopicListOutput, TopicCategory, TopicSource
│   ├── knowledge_base.py            # KnowledgeEntry, SearchResult, KBMetadata, KnowledgeBaseStats
│   ├── analytics.py                 # AnalyticsData, ContentStats, PerformanceMetrics, TrendData
│   ├── platform_content.py          # PublicAccountContent, DouyinContent, MultiPlatformContent
│   └── local_embedding.py           # LocalEmbedding — 本地Embedding封装
├── validators/                      # 2个校验器
│   ├── result_validator.py          # ResultValidator — Agent间质量校验
│   └── ai_flavor_scorer.py          # AIFlavorScorer — AI味5维度评分(中文适配)
├── config/                          # 5个配置文件
│   ├── llm_config.py                # LLM配置 — MiMo/Simple/DeepSeek/Qwen + AGENT_MODEL_MAP
│   ├── agent_config.py              # Agent配置 — max_retries/timeout/output_model
│   ├── platform_config.py           # 平台配置 — 字数/标签/违禁词
│   ├── vector_config.py             # 向量配置 — IVFFlat/HNSW/Embedding参数
│   └── __init__.py                  # 统一导出（37个名称）
├── prompts/                         # 12个Prompt文件
│   ├── orchestrator.md              # 统一调度
│   ├── material_search.md           # 素材检索
│   ├── title_agent.md               # 标题创作
│   ├── article_agent.md             # 正文创作
│   ├── tag_agent.md                 # 标签策略
│   ├── compliance_agent.md          # 合规审核
│   ├── topic_agent.md               # 选题推荐
│   ├── kb_agent.md                  # 知识库管理
│   ├── analytics_agent.md           # 数据分析
│   ├── operation_agent.md           # 内容运营
│   ├── wechat_article_agent.md      # 公众号创作
│   └── douyin_script_agent.md       # 抖音脚本
├── flows/                           # 3个Flow工作流
│   ├── main_flow.py                 # MainFlow — route → dispatch（2步）
│   └── xiaohongshu_flow.py          # XiaohongshuFlow — 8步事件链（含重试/降级/耗时监控）
├── crews/                           # 2个Crew
│   ├── xiaohongshu_crew.py          # XiaohongshuCrew — Agent容器
│   └── shared_crew.py               # SharedCrew — 跨平台共享能力
├── api/                             # FastAPI后端
│   ├── main.py                      # 应用入口 + 路由注册
│   ├── auth.py                      # JWT认证 + bcrypt密码
│   ├── db.py                        # asyncpg连接池 + RLS上下文
│   ├── utils.py                     # 共享工具
│   ├── flow_runner.py               # 异步创作编排器
│   ├── embedding_service.py         # 异步Embedding服务
│   └── routes/
│       ├── create.py                # 创作流程API（6个端点 + WebSocket）
│       ├── analytics.py             # 数据看板API（8个端点）
│       ├── tenant_knowledge.py      # 租户知识库API（8个端点）
│       └── platform_knowledge.py    # 平台管理API（16个端点）
├── db/                              # 数据库脚本
│   ├── init.sql                     # 建表（8张表）
│   ├── rls.sql                      # RLS策略
│   └── seed.sql                     # 种子数据
├── frontend/                        # Next.js前端
│   └── src/
│       ├── app/                     # 16个页面路由（App Router）
│       ├── components/
│       │   ├── ui/                  # shadcn/ui基础组件（20+）
│       │   ├── layout/              # 布局组件（sidebar/header/bottom-nav）
│       │   ├── create/              # 创作流程组件（6步）
│       │   └── shared/              # 通用业务组件
│       ├── hooks/                   # React Query hooks（5个）
│       ├── stores/                  # Zustand stores（4个）
│       ├── lib/                     # API客户端/认证/工具函数
│       └── types/                   # TypeScript类型定义
├── tests/                           # 测试文件（17个 + 6个E2E）
├── monitoring/                      # Prometheus指标 + 告警
├── sync/                            # Obsidian同步服务
├── orchestrator/                    # 调度模块
├── scripts/                         # 工具脚本
├── docker-compose.yml               # Docker编排（4个服务）
├── docker-compose.prod.yml          # 生产环境编排
├── Dockerfile                       # 主应用镜像
└── requirements.txt                 # Python依赖
```

***

## 附录B：数据库表结构

### B.1 完整表定义（8张表）

#### 1. enterprises（企业表）

```sql
CREATE TABLE IF NOT EXISTS enterprises (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    industry VARCHAR(100),
    plan_type VARCHAR(50) DEFAULT 'free',
    quota_monthly INTEGER DEFAULT 100,
    quota_used INTEGER DEFAULT 0,
    settings JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active'
);
```

#### 2. users（用户表）

```sql
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'tenant',
    -- 角色：tenant / tenant_admin / tenant_user / platform_admin / platform_operator
    enterprise_id VARCHAR(255) REFERENCES enterprises(id),
    avatar_url VARCHAR(1000),
    status VARCHAR(20) DEFAULT 'active',
    last_login_at TIMESTAMP
);
```

#### 3. knowledge_base（统一知识库表）

```sql
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    data_level VARCHAR(20) NOT NULL DEFAULT 'tenant',
    platform_category VARCHAR(50) DEFAULT NULL,
    enterprise_id VARCHAR(255) DEFAULT NULL,
    category VARCHAR(100) DEFAULT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(255) DEFAULT NULL,
    source_url VARCHAR(1000) DEFAULT NULL,
    embedding VECTOR(1024),
    sync_status VARCHAR(20) DEFAULT 'pending',
    -- sync_status: pending / synced / failed
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    created_by VARCHAR(255) DEFAULT NULL,
    updated_by VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_platform_needs_null_enterprise
        CHECK (data_level = 'platform' AND enterprise_id IS NULL OR data_level = 'tenant'),
    CONSTRAINT chk_tenant_needs_enterprise
        CHECK (data_level = 'tenant' AND enterprise_id IS NOT NULL OR data_level = 'platform')
);

CREATE INDEX idx_knowledge_embedding
ON knowledge_base USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

#### 4. compliance_rules（合规规则表）

```sql
CREATE TABLE IF NOT EXISTS compliance_rules (
    id SERIAL PRIMARY KEY,
    word VARCHAR(255) NOT NULL,
    level VARCHAR(10) DEFAULT 'P0',
    -- level: P0 / P1
    category VARCHAR(100),
    description TEXT,
    industry VARCHAR(100),
    is_active BOOLEAN DEFAULT true
);
```

#### 5. notes（笔记表）

```sql
CREATE TABLE IF NOT EXISTS notes (
    id SERIAL PRIMARY KEY,
    enterprise_id VARCHAR(255) REFERENCES enterprises(id),
    platform VARCHAR(50),
    topic VARCHAR(500),
    title VARCHAR(500),
    article TEXT,
    tags JSONB DEFAULT '[]',
    ai_flavor_score INTEGER,
    compliance_status VARCHAR(20),
    metadata JSONB DEFAULT '{}',
    published_at TIMESTAMP
);
```

#### 6. material_packs（素材包表）

```sql
CREATE TABLE IF NOT EXISTS material_packs (
    id SERIAL PRIMARY KEY,
    enterprise_id VARCHAR(255) REFERENCES enterprises(id),
    brand_name VARCHAR(255),
    product_name VARCHAR(255),
    persona_profile TEXT,
    scene_description TEXT,
    compliance_rules JSONB DEFAULT '{}'
);
```

#### 7. title_history（标题历史表）

```sql
CREATE TABLE IF NOT EXISTS title_history (
    id SERIAL PRIMARY KEY,
    enterprise_id VARCHAR(255) REFERENCES enterprises(id),
    platform VARCHAR(50),
    title VARCHAR(500),
    title_hash VARCHAR(64)
);
```

#### 8. audit_logs（审计日志表）

```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255),
    enterprise_id VARCHAR(255),
    action VARCHAR(50),
    -- action: create / update / delete / login / export
    resource_type VARCHAR(50),
    -- resource_type: knowledge_base / note / template / user
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### B.2 数据库用户权限设计

与 V2.1 相同（app_tenant / app_platform / app_agent 三个用户）。

***

## 附录C：API 端点完整列表

### C.1 认证与用户（6个端点）

| 方法 | 路径 | 说明 | 鉴权 |
| --- | --- | --- | --- |
| POST | `/api/v1/auth/login` | 邮箱+密码登录，返回JWT | 无 |
| GET | `/api/v1/auth/me` | 当前用户信息 | JWT |
| GET | `/api/v1/public/health` | 健康检查 | 无 |
| GET | `/api/v1/user/profile` | 用户资料（从DB） | JWT |
| GET | `/api/v1/enterprise/info` | 企业信息 | JWT |
| GET | `/api/v1/enterprise/quota` | 企业额度 | JWT |

### C.2 创作流程（6个端点 + 1个WebSocket）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/v1/create/start` | 提交创作请求，触发Flow |
| GET | `/api/v1/create/{task_id}/status` | 查询任务状态 |
| POST | `/api/v1/create/{task_id}/select-title` | 用户选择标题 |
| POST | `/api/v1/create/{task_id}/p2-decision` | P2合规决策 |
| GET | `/api/v1/create/{task_id}/result` | 获取最终笔记包 |
| WS | `/api/v1/create/ws/{task_id}` | WebSocket实时状态推送 |

### C.3 数据看板（8个端点）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/dashboard/summary` | 看板概览 |
| GET | `/api/v1/dashboard/trends` | 趋势数据（7-90天） |
| GET | `/api/v1/dashboard/vector-stats` | 向量同步状态 |
| GET | `/api/v1/dashboard/topics` | 选题排名 |
| GET | `/api/v1/notes` | 笔记列表（分页+筛选） |
| GET | `/api/v1/notes/{note_id}` | 笔记详情 |
| PUT | `/api/v1/notes/{note_id}` | 编辑笔记 |
| DELETE | `/api/v1/notes/{note_id}` | 删除笔记 |

### C.4 租户知识库（8个端点）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/tenant/knowledge/tree` | 分类树 |
| GET | `/api/v1/tenant/knowledge/items` | 知识列表（分页+搜索） |
| POST | `/api/v1/tenant/knowledge/items` | 创建知识条目 |
| PUT | `/api/v1/tenant/knowledge/items/{item_id}` | 编辑知识条目 |
| DELETE | `/api/v1/tenant/knowledge/items/{item_id}` | 删除知识条目 |
| POST | `/api/v1/tenant/knowledge/upload` | 文件上传（COS + 入库） |
| POST | `/api/v1/tenant/knowledge/search` | 语义搜索（pgvector） |
| POST | `/api/v1/tenant/knowledge/items/{item_id}/resync` | 重新向量化 |

### C.5 平台管理（16个端点）

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/platform/knowledge/public` | 公共知识列表 |
| POST | `/api/v1/platform/knowledge/public` | 创建公共知识 |
| PUT | `/api/v1/platform/knowledge/public/{item_id}` | 编辑公共知识 |
| DELETE | `/api/v1/platform/knowledge/public/{item_id}` | 删除公共知识 |
| GET | `/api/v1/platform/knowledge/industry` | 行业知识列表 |
| POST | `/api/v1/platform/knowledge/industry` | 创建行业知识 |
| PUT | `/api/v1/platform/knowledge/industry/{item_id}` | 编辑行业知识 |
| DELETE | `/api/v1/platform/knowledge/industry/{item_id}` | 删除行业知识 |
| GET | `/api/v1/platform/templates` | 模板列表 |
| POST | `/api/v1/platform/templates` | 创建模板 |
| PUT | `/api/v1/platform/templates/{item_id}` | 编辑模板 |
| DELETE | `/api/v1/platform/templates/{item_id}` | 删除模板 |
| GET | `/api/v1/platform/compliance` | 合规规则列表 |
| POST | `/api/v1/platform/compliance` | 创建合规规则 |
| PUT | `/api/v1/platform/compliance/{item_id}` | 编辑合规规则 |
| DELETE | `/api/v1/platform/compliance/{item_id}` | 删除合规规则 |

**总计：33个REST端点 + 1个WebSocket端点**

***

## 附录D：Agent-LLM-Prompt 映射表

| Agent | 文件 | LLM模型 | Prompt文件 | max_retries | timeout | 输出模型 |
| --- | --- | --- | --- | --- | --- | --- |
| OrchestratorAgent | orchestrator_agent.py | mimo-v2.5-pro | orchestrator.md | 3 | 30s | OrchestratorOutput |
| MaterialAgent | material_agent.py | mimo-v2.5-pro | material_search.md | 2 | 60s | MaterialPack |
| TitleAgent | title_agent.py | mimo-v2.5 | title_agent.md | 2 | 60s | TitleOutput |
| ArticleAgent | article_agent.py | mimo-v2.5-pro | article_agent.md | 2 | 120s | NoteOutput |
| TagAgent | tag_agent.py | mimo-v2.5 | tag_agent.md | 2 | 30s | list[str] |
| ComplianceAgent | compliance_agent.py | mimo-v2.5-pro | compliance_agent.md | 2 | 60s | ComplianceReport |
| TopicAgent | topic_agent.py | mimo-v2.5 | topic_agent.md | 2 | 60s | TopicListOutput |
| KnowledgeBaseAgent | kb_agent.py | mimo-v2.5 | kb_agent.md | 2 | 60s | SearchResult |
| AnalyticsAgent | analytics_agent.py | mimo-v2.5-pro | analytics_agent.md | 2 | 60s | AnalyticsData |
| OperationAgent | operation_agent.py | mimo-v2.5 | operation_agent.md | 2 | 60s | OperationOutput |
| WechatArticleAgent | wechat_article_agent.py | mimo-v2.5-pro | wechat_article_agent.md | 2 | 120s | PublicAccountContent |
| DouyinScriptAgent | douyin_script_agent.py | mimo-v2.5-pro | douyin_script_agent.md | 2 | 120s | DouyinContent |

***

## 附录E：前端页面路由

| 路由 | 页面文件 | 说明 | 角色 |
| --- | --- | --- | --- |
| `/` | page.tsx | 首页（重定向） | 公开 |
| `/login` | login/page.tsx | 登录页 | 公开 |
| `/dashboard` | dashboard/page.tsx | 工作台 | 租户 |
| `/create` | create/page.tsx | 创作中心（6步流程） | 租户 |
| `/analytics` | analytics/page.tsx | 数据看板 | 租户 |
| `/knowledge` | knowledge/page.tsx | 知识库管理 | 租户 |
| `/settings` | settings/page.tsx | 设置 | 租户 |
| `/notes/[id]` | notes/[id]/page.tsx | 笔记详情 | 租户 |
| `/admin` | admin/page.tsx | 管理后台首页 | 平台管理员 |
| `/admin/knowledge/public` | admin/knowledge/public/page.tsx | 公共知识管理 | 平台管理员 |
| `/admin/knowledge/industry` | admin/knowledge/industry/page.tsx | 行业知识管理 | 平台管理员 |
| `/admin/templates` | admin/templates/page.tsx | 模板管理 | 平台管理员 |
| `/admin/compliance` | admin/compliance/page.tsx | 合规规则管理 | 平台管理员 |
| `/admin/stats` | admin/stats/page.tsx | 数据统计 | 平台管理员 |
| `/403` | 403/page.tsx | 无权限页 | 公开 |

**响应式断点：**

| 断点 | 宽度 | 布局 |
| --- | --- | --- |
| xl | >= 1280px | 完整侧边栏 + 宽内容区 |
| lg | 1024-1279px | 可折叠侧边栏 |
| md | 768-1023px | 侧边栏隐藏，汉堡按钮弹出 overlay |
| sm | < 768px | 底部导航栏 + 紧凑布局 |

**前端技术栈：**

| 组件 | 技术 |
| --- | --- |
| 框架 | Next.js 14（App Router + TypeScript） |
| UI库 | shadcn/ui（base-ui 风格）+ Tailwind CSS |
| 主题 | 深色主题 |
| 状态管理 | Zustand（auth-store / create-store / user-store / sidebar-store） |
| 数据获取 | @tanstack/react-query（hooks 层封装） |
| 图表 | recharts（动态导入） |

***

## 附录F：测试覆盖

| 测试文件 | 测试数 | 覆盖范围 |
| --- | --- | --- |
| test_article_tag_compliance.py | 74 | 正文Agent + 标签Agent + 合规Agent |
| test_llm.py | 42 | LLM调用 + 降级 + 解析 |
| test_orchestrator_material_title.py | 41 | 调度Agent + 素材检索 + 标题Agent |
| test_xiaohongshu_flow.py | 21 | 小红书Flow端到端 |
| test_vector.py | 10 | pgvector写入/检索 |
| test_sync/test_obsidian_client.py | 9 | Obsidian同步 |
| test_sync/test_knowledge_loader.py | 9 | 知识加载 |
| test_tools/test_tools.py | 8 | 工具层 |
| test_embedding.py | 7 | Embedding模型 |
| test_monitoring/test_monitoring.py | 6 | 监控指标 |
| test_agents/test_agents.py | 5 | Agent初始化 |
| test_models/test_models.py | 5 | 数据模型序列化 |
| test_orchestrator/test_agent.py | 5 | 调度Agent |
| test_validators/test_validators.py | 5 | 校验器 |
| test_flows/test_flows.py | 3 | Flow工作流 |
| test_api/test_api.py | 2 | API端点 |
| test_sync/test_sync.py | 2 | 同步服务 |
| **总计** | **254** | |

**E2E 测试（6个）：**

| 文件 | 覆盖阶段 |
| --- | --- |
| phase0_e2e_test.py | 技术预研验证 |
| phase2_e2e_test.py | 核心创作流程 |
| phase3_e2e_test.py | 知识库 + 前端 |
| phase4_e2e_test.py | 数据 + 优化 |
| phase5_e2e_test.py | 多平台扩展 |
| full_platform_e2e_test.py | 全平台端到端 |

***

## 附录G：性能基准（全流程耗时监控）

基于实际运行数据（2026-05-08）：

| 步骤 | 耗时 | 占比 | 说明 |
| --- | --- | --- | --- |
| 素材检索 - 向量化 | 17s | 6% | 首次加载bge-large-zh-v1.5模型 |
| 素材检索 - 企业私有库 | 0.3s | <1% | pgvector IVFFlat 索引 |
| 素材检索 - 行业知识库 | 0.2s | <1% | pgvector IVFFlat 索引 |
| 素材检索 - 公共知识库 | 0.2s | <1% | pgvector IVFFlat 索引 |
| 标题Agent | 13s | 4% | mimo-v2.5，1次LLM调用 |
| 正文Agent（第1次） | 55s | 19% | mimo-v2.5-pro，1次LLM调用 + AI味评分 |
| 合规校验（第1次） | 60s | 20% | mimo-v2.5-pro，1次LLM调用 |
| 正文Agent（重生成） | 55s | 19% | P0问题触发重新生成 |
| 合规校验（第2次） | 60s | 20% | 重新校验 |
| 标签Agent | 15s | 5% | mimo-v2.5，1次LLM调用 |
| 最终合规检查 | 60s | 20% | 最终校验（与标签并行可优化） |
| **全流程总计** | **~297s** | **100%** | **约5分钟** |

**已识别瓶颈与优化建议：**

| 优先级 | 瓶颈 | 优化方案 | 预期收益 |
| --- | --- | --- | --- |
| P0 | 合规检查196s（66%） | 标签生成与合规检查并行执行 | 节省60s |
| P0 | 合规检查Prompt优化 | 精简Prompt，减少LLM推理时间 | 节省30-40s |
| P1 | Embedding首次加载17s | 服务启动时预加载模型 | 首次请求零延迟 |
| P1 | AI味评分阈值联动 | 评分与正文Agent内部联动，减少Flow层重试 | 减少1次完整LLM调用 |
| P2 | 知识库数据不足 | 补充行业知识库数据 | 提高素材检索命中率 |

***

## 附录H：Docker 服务配置

| 服务 | 镜像 | 端口 | 说明 |
| --- | --- | --- | --- |
| postgres | pgvector/pgvector:pg16 | 5432 | PostgreSQL 16 + pgvector扩展 |
| redis | redis:7-alpine | 6379 | Redis缓存 |
| app | 自建（./Dockerfile） | 8000 + 8501 | FastAPI + Streamlit(兼容) |
| frontend | 自建（./frontend/Dockerfile） | 3000 | Next.js前端 |

**网络：** content-agent-network（bridge）

**数据卷：** pgdata（PostgreSQL）、redisdata（Redis）、./vault（Obsidian Vault）

***

## 附录I：工具清单（14个）

| 工具文件 | 类名 | 说明 |
| --- | --- | --- |
| material_tools.py | MaterialSearchTool | 三层知识库语义检索 + 素材包组装 |
| llm_tools.py | LLMCallTool, LLMResponseParser | LLM调用 + L1-L4降级 + JSON解析 |
| crewai_llm.py | create_llm() | CrewAI兼容LLM构造（LiteLLM格式） |
| vector_tools.py | VectorStoreTool | pgvector写入/检索（内积操作符） |
| embedding_tools.py | LocalEmbeddingTool | bge-large-zh-v1.5 本地Embedding |
| compliance_tools.py | ComplianceCheckTool, ProhibitedWordDetector | 违禁词检测（4类51个词） |
| prompt_tools.py | PromptManager | Prompt加载 + `{{variable}}` 替换 |
| cache_tools.py | TTLCache | 泛型TTL内存缓存 |
| session_tools.py | SessionManager | PostgreSQL RLS会话上下文（6角色） |
| cos_tools.py | COSUploadTool, COSDownloadTool, COSDeleteTool | 腾讯云COS操作 |
| obsidian_tools.py | ObsidianReaderTool, ObsidianSearchTool, ObsidianLinkTrackerTool | Obsidian文件操作 |
| content_adapter.py | ContentAdapter | 多平台内容适配 |
| multi_platform_publisher.py | MultiPlatformPublisher | 一键分发（mock模式） |
| prompt_optimizer.py | PromptOptimizer | AI味去除 + 口语化 + emoji优化 |
