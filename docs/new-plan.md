
# 智创笔记架构重构规划 — Agent 独立化 + 灵活编排

> **状态：已完成** — Phase 1 ~ Phase 7 全部执行完毕（2026-05-08）
>
> 执行结果：54 个新增测试全部通过，已有测试无回归。
> 实际实现与计划的偏差：full 模式创作流程改为逐步执行 + WebSocket 中间推送（原计划使用 CreationChain 一次性执行）。

> 给 Claude Code 的执行手册，每一步都有明确输入、输出、验收标准，确保不跑偏。

***

## 总体原则（Claude Code 必须遵守）



```
1. 不删除任何已有的 Agent、Tool、Model 文件
2. 每个 Phase 独立可测试，完成后才能进入下一 Phase
3. 每个 Phase 完成后必须运行已有测试（254个），确保不回归
4. 新增代码必须有对应测试
5. Flow 主干保持可运行，重构是"增强"不是"替换"
6. 每次改动不超过 3 个文件，避免大规模重构失控
```

***

## Phase 1：Agent 独立调用层（P0，预计 2-3 天）

### 目标

让每个 Agent 可以脱离 Flow 被独立调用，这是所有后续工作的基础。

### Step 1.1：定义 Agent 统一调用接口

**文件：**`agents/base_agent.py`（新建）

**要求：**

*   创建 `BaseAgentRunner` 类，提供统一的 `run()` 方法
*   每个 Agent 的 `run()` 接收标准化的 `AgentRequest`，返回标准化的 `AgentResponse`
*   `AgentRequest` 包含：`agent_name`, `input_data`（dict）, `enterprise_id`, `user_id`, `context`（可选的上下游结果）
*   `AgentResponse` 包含：`success`（bool）, `data`（dict/Pydantic model）, `errors`（list）, `warnings`（list）, `metadata`（耗时、token用量、模型信息）
*   内部处理 LLM 降级逻辑（复用已有 `LLMCallTool`）
*   内部处理重试逻辑（复用已有 `agent_config.py` 中的 max\_retries）
*   内部处理超时（复用已有 timeout 配置）

**验收标准：**



```
# 可以这样调用任意 Agent
runner = BaseAgentRunner()
result = runner.run(AgentRequest(
    agent_name="title",
    input_data={"product": "防晒霜", "persona": "25岁女生", "scene": "夏天户外"},
    enterprise_id="ent_001"
))
assert result.success == True
assert len(result.data["titles"]) >= 5
```

### Step 1.2：为每个 Agent 实现独立调用适配

**文件：** 每个 `agents/*.py` 新增 `run_standalone()` 方法

**要求：**

*   在已有的 12 个 Agent 文件中，各自新增一个 `run_standalone(input_data, context=None)` 方法
*   该方法封装该 Agent 独立运行所需的最小输入
*   定义每个 Agent 的输入 schema（Pydantic model，在 `models/` 下新增）

**每个 Agent 的独立输入定义：**

| Agent | 必需输入 | 可选输入（来自上游 Agent） |
| --- | --- | --- |
| TopicAgent | `enterprise_id`, `industry` | `historical_titles`, `hot_topics` |
| MaterialAgent | `enterprise_id`, `query_text` | `topic`（来自选题结果） |
| TitleAgent | `product`, `persona`, `scene` | `material_pack`, `topic` |
| ArticleAgent | `title`, `material_pack`, `persona` | `topic`, `compliance_rules` |
| TagAgent | `title`, `article` | `platform` |
| ComplianceAgent | `title`, `article` | `compliance_rules` |
| OperationAgent | `enterprise_id`, `platform` | `note_pack` |
| AnalyticsAgent | `enterprise_id` | `date_range`, `platform` |
| KnowledgeBaseAgent | `enterprise_id`, `query` | `data_level` |
| WechatArticleAgent | `topic`, `material_pack` | `style`, `length` |
| DouyinScriptAgent | `topic`, `material_pack` | `duration`, `style` |

**验收标准：**

*   每个 Agent 可以通过 `run_standalone()` 独立运行并返回结果
*   编写测试：`tests/test_standalone_agents.py`，覆盖全部 12 个 Agent 的独立调用

### Step 1.3：新增单 Agent API 端点

**文件：**`api/routes/agents.py`（新建）

**要求：**

*   新增 12 个端点，每个 Agent 一个：



```
POST /api/v1/agents/topic/recommend
POST /api/v1/agents/material/search
POST /api/v1/agents/title/generate
POST /api/v1/agents/article/generate
POST /api/v1/agents/tag/generate
POST /api/v1/agents/compliance/check
POST /api/v1/agents/operation/suggest
POST /api/v1/agents/analytics/report
POST /api/v1/agents/kb/search
POST /api/v1/agents/wechat/generate
POST /api/v1/agents/douyin/generate
POST /api/v1/agents/orchestrator/route
```

*   所有端点需要 JWT 鉴权
*   复用已有的限流机制（Redis 计数器）
*   返回统一的 `AgentResponse` 格式
*   在 `api/main.py` 中注册新路由

**验收标准：**

*   `curl` 可以单独调用任意 Agent 端点并获得结果
*   编写测试：`tests/test_api/test_agent_endpoints.py`

***

## Phase 2：Agent 间通信协议（P0，预计 2 天）

### 目标

让 Agent 之间可以传递结构化上下文，解决"合规 Agent 发现问题但正文 Agent 不知道"的核心痛点。

### Step 2.1：定义 Agent 间通信数据结构

**文件：**`models/agent_message.py`（新建）

**要求：**



```
class AgentMessage:
    """Agent 间传递的消息"""
    from_agent: str          # 发送方 Agent 名
    to_agent: str            # 接收方 Agent 名
    message_type: str        # "result" / "feedback" / "request" / "correction"
    payload: dict            # 具体数据
    priority: str            # "normal" / "urgent"（P0 问题标记为 urgent）
    trace_id: str            # 用于追踪完整链路

class ComplianceFeedback:
    """合规 Agent 的具体修改建议"""
    issue_type: str          # "prohibited_word" / "absolute_claim" / "medical_claim"
    severity: str            # "P0" / "P1" / "P2"
    original_text: str       # 原文
    suggestion: str          # 建议修改
    location: str            # "paragraph_3_sentence_2"

class CorrectionRequest:
    """要求其他 Agent 修正的请求"""
    target_agent: str
    corrections: list[ComplianceFeedback]
    context: dict            # 原始输入上下文，方便 Agent 重新生成
```

**验收标准：** 数据结构可序列化/反序列化，有完整的类型提示

### Step 2.2：改造 ComplianceAgent 输出结构化反馈

**文件：**`agents/compliance_agent.py`（修改）

**要求：**

*   ComplianceAgent 的输出从简单的 `ComplianceReport` 扩展为包含 `ComplianceFeedback` 列表
*   每个 issue 必须包含：原文、位置（段落+句子级别）、具体修改建议、严重级别
*   Prompt 文件 `prompts/compliance_agent.md` 同步修改，要求 LLM 输出结构化的修改建议

**验收标准：**



```
report = compliance_agent.run_standalone({"title": "...", "article": "..."})
assert report.issues[0].original_text is not None
assert report.issues[0].suggestion is not None
assert report.issues[0].location is not None
```

### Step 2.3：改造 ArticleAgent 接收结构化反馈并精准修改

**文件：**`agents/article_agent.py`（修改）

**要求：**

*   ArticleAgent 的 `run_standalone()` 新增可选参数 `corrections: list[ComplianceFeedback]`
*   当 `corrections` 不为空时，进入"修改模式"而非"重新生成模式"
*   Prompt 文件 `prompts/article_agent.md` 新增修改模式的指令模板
*   修改模式下只改动有问题的段落，保留其余内容不变

**验收标准：**



```
# 模拟：合规发现问题 → 传给正文Agent精准修改
corrections = [ComplianceFeedback(
    issue_type="prohibited_word",
    severity="P0",
    original_text="效果最好",
    suggestion="用户反馈效果很好",
    location="paragraph_2_sentence_1"
)]
result = article_agent.run_standalone(
    {"title": "...", "material_pack": ..., "persona": "..."},
    context={"corrections": corrections}
)
assert "效果最好" not in result.data["article"]
```

### Step 2.4：构建 AgentChain 执行器

**文件：**`agents/agent_chain.py`（新建）

**要求：**

*   创建 `AgentChain` 类，支持按顺序执行多个 Agent
*   每个 Agent 的输出自动注入到下一个 Agent 的 context 中
*   支持"反馈循环"：当某个 Agent 返回 `urgent` 级别的 message 时，可以回退到上游 Agent 重新处理
*   循环有最大次数限制（复用 `MAX_TOTAL_RETRIES = 4`）
*   每步记录耗时（复用已有的耗时监控模式）



```
chain = AgentChain()
chain.add_step("material", MaterialAgent())
chain.add_step("title", TitleAgent())
chain.add_step("article", ArticleAgent())
chain.add_step("compliance", ComplianceAgent())
chain.add_correction_loop("compliance", "article", max_retries=2)

result = chain.execute(initial_input)
```

**验收标准：**

*   可以执行完整的 Agent 链
*   合规问题可以触发正文 Agent 的精准修改（而非盲重试）
*   循环次数被正确限制
*   编写测试：`tests/test_agent_chain.py`

***

## Phase 3：选题接入主流程（P0，预计 1-2 天）

### 目标

把已实现但游离的 TopicAgent 接入创作流程，补齐"全链路"缺口。

### Step 3.1：改造 TopicAgent 输出结构化选题

**文件：**`agents/topic_agent.py`（修改）、`models/topic.py`（修改）

**要求：**

*   TopicAgent 输出的每个选题包含：`title`（选题标题）、`angle`（切入角度）、`keywords`（关键词列表）、`target_persona`（目标人群）、`confidence`（推荐置信度）
*   关键词列表用于下游素材检索的语义锚点

**验收标准：**



```
topics = topic_agent.run_standalone({"enterprise_id": "ent_001", "industry": "美妆"})
assert topics.data[0].keywords is not None
assert len(topics.data[0].keywords) >= 3
```

### Step 3.2：创建带选题的创作 Chain

**文件：**`agents/chains/creation_chain.py`（新建）

**要求：**

*   创建 `CreationChain` 类，基于 `AgentChain` 构建
*   支持两种模式：
    *   **数据驱动模式**：选题 → 素材检索（基于选题关键词）→ 标题 → 正文 → 合规 → 标签
    *   **用户驱动模式**：直接从素材检索开始（跳过选题），与当前流程一致
*   选题步骤返回候选列表，支持两种选择方式：
    *   用户手动选择（API 返回候选，等用户确认后再继续）
    *   系统自动选择（取置信度最高的）



```
# 数据驱动模式
chain = CreationChain(mode="data_driven", enterprise_id="ent_001")
result = chain.execute()  # 自动走完选题→素材→标题→正文→合规→标签

# 用户驱动模式（兼容现有流程）
chain = CreationChain(mode="user_driven", enterprise_id="ent_001")
result = chain.execute(input_data={"product": "防晒霜", "persona": "25岁女生"})
```

**验收标准：**

*   两种模式都能完整执行
*   数据驱动模式中，素材检索的 query 来自选题的 keywords
*   编写测试：`tests/test_creation_chain.py`

### Step 3.3：改造创作 API 支持两种模式

**文件：**`api/routes/create.py`（修改）

**要求：**

*   `POST /api/v1/create/start` 新增参数 `mode: "data_driven" | "user_driven"`
*   `data_driven` 模式下：
    *   第一步返回选题候选列表 + `task_id`
    *   新增 `POST /api/v1/create/{task_id}/select-topic` 端点
    *   用户确认选题后自动继续后续流程
*   `user_driven` 模式下保持现有行为不变

**验收标准：**

*   现有的 `user_driven` 调用方式不受影响（回归测试通过）
*   `data_driven` 模式可以完成完整的选题→创作流程

***

## Phase 4：合规闭环优化（P1，预计 2 天）

### 目标

彻底解决"合规检查 196s 占 66%、盲改 2 次后放弃"的问题。

### Step 4.1：合规检查结果驱动精准修改

**文件：**`agents/chains/creation_chain.py`（修改）

**要求：**

*   利用 Phase 2 构建的 `ComplianceFeedback` 和正文 Agent 的修改模式
*   合规检查发现问题时，将结构化反馈传回正文 Agent
*   正文 Agent 只修改有问题的部分，而非全文重写
*   每次修改后只做增量合规检查（只检查修改过的段落），而非全文重新检查

**验收标准：**

*   P0 问题修改后，不再触发全文重写
*   合规检查次数从 3 次（首次 + 2次重试）降低到 1-2 次
*   总耗时显著下降

### Step 4.2：标签生成与合规检查并行执行

**文件：**`agents/chains/creation_chain.py`（修改）

**要求：**

*   标签生成不依赖合规结果，可以在合规检查的同时并行执行
*   使用 `asyncio.gather()` 或线程池实现并行
*   两者都完成后才进入最终输出



```
# 伪代码
tag_result, compliance_result = await asyncio.gather(
    tag_agent.run(article),
    compliance_agent.run(title, article)
)
```

**验收标准：**

*   标签生成和合规检查的耗时取两者中较长的一个，而非相加
*   预期节省约 60s（附录 G 中标注的优化收益）

### Step 4.3：优化合规检查 Prompt

**文件：**`prompts/compliance_agent.md`（修改）

**要求：**

*   精简 Prompt，减少 LLM 推理时间
*   合并"首次检查"和"最终检查"为同一个 Prompt（当前流程中合规检查被调用了 3 次，每次都走完整 Prompt）
*   只在首次检查时做全面扫描，修改后做定向复查

**验收标准：**

*   单次合规检查耗时下降 30-40s（文档中预期的优化收益）
*   检查准确率不下降

***

## Phase 5：Orchestrator 智能化（P2，预计 3-4 天）

### 目标

让 OrchestratorAgent 真正具备"理解意图 → 选择策略 → 动态调度"的能力。

### Step 5.1：OrchestratorAgent 接入 Agent 独立调用

**文件：**`agents/orchestrator_agent.py`（修改）

**要求：**

*   OrchestratorAgent 可以将其他 Agent 作为 Tool 来调用
*   创建 `AgentTool` 包装器，将任意 Agent 的 `run_standalone()` 包装为 CrewAI Tool



```
class AgentTool(BaseTool):
    """将 Agent 包装为 Tool，供 Orchestrator 调用"""
    agent_name: str
    runner: BaseAgentRunner

    def _run(self, **kwargs) -> str:
        result = self.runner.run(AgentRequest(
            agent_name=self.agent_name,
            input_data=kwargs
        ))
        return result.data
```

**验收标准：**

*   OrchestratorAgent 可以通过 Tool 方式调用任意下游 Agent

### Step 5.2：定义 Orchestrator 的调度策略

**文件：**`prompts/orchestrator.md`（修改）

**要求：**

*   Prompt 中定义明确的调度策略表：

| 意图 | 策略 | 调用的 Agent |
| --- | --- | --- |
| "帮我写一篇小红书" | 完整创作链 | 选题 → 素材 → 标题 → 正文 → 合规 → 标签 |
| "帮我想选题" | 仅选题 | TopicAgent |
| "检查一下这篇文案" | 仅合规 | ComplianceAgent |
| "帮我改写为公众号" | 平台适配 | ContentAdapter → WechatArticleAgent |
| "分析一下最近的数据" | 仅分析 | AnalyticsAgent |
| "帮我搜一下相关素材" | 仅检索 | MaterialAgent |
| "把这个笔记发到多个平台" | 多平台分发 | MultiPlatformPublisher |

*   Orchestrator 根据用户输入匹配意图，选择策略，调用对应的 Agent
*   当意图不明确时，主动追问而非猜测

**验收标准：**

*   7 种意图都能被正确识别和路由
*   每种路由都能返回正确结果
*   编写测试：`tests/test_orchestrator_routing.py`

### Step 5.3：改造 MainFlow 使用 Orchestrator 调度

**文件：**`flows/main_flow.py`（修改）

**要求：**

*   MainFlow 不再硬编码路由逻辑
*   将路由决策委托给 OrchestratorAgent
*   OrchestratorAgent 的输出是"调用计划"（哪些 Agent、什么顺序、什么参数）
*   MainFlow 按调用计划执行

**验收标准：**

*   现有的完整创作流程仍然可用
*   新增的单 Agent 调用场景也能被正确路由

***

## Phase 6：前端适配（P2，预计 2-3 天）

### 目标

前端支持新的灵活调用模式。

### Step 6.1：创作中心支持双模式

**文件：**`frontend/src/app/create/page.tsx`（修改）

**要求：**

*   创作中心新增模式选择：数据驱动 / 用户驱动
*   数据驱动模式下：
    *   新增"选题推荐"步骤（在素材检索之前）
    *   展示候选选题列表，用户可选择或刷新
    *   选题确认后自动进入素材检索
*   用户驱动模式下保持现有 6 步流程不变

### Step 6.2：新增单 Agent 调用页面

**文件：**`frontend/src/app/tools/page.tsx`（新建）

**要求：**

*   新增"AI 工具箱"页面，列出可独立使用的 Agent
*   每个工具有独立的输入表单和输出展示
*   包含：选题推荐、合规检查、素材检索、标签生成、数据分析
*   路由：`/tools`，角色权限：租户

### Step 6.3：创作流程支持实时反馈

**文件：**`frontend/src/components/create/`（修改）

**要求：**

*   合规检查发现问题时，展示具体的问题和修改建议（而非只显示"不通过"）
*   用户可以看到合规 Agent 的具体反馈内容
*   支持用户手动编辑后再提交校验

***

## Phase 7：清理与文档对齐（P1，预计 1 天）

### Step 7.1：更新 PRD 文档

**文件：**`PRD V2.3`

**要求：**

*   更新架构图，体现 Agent 独立调用 + Chain 编排 + Orchestrator 智能调度
*   更新 Flow 分工说明
*   更新 API 端点列表（新增 12 个 Agent 端点）
*   更新前端页面路由（新增 /tools 页面）
*   移除所有"与 V2.1 相同"的引用，补充实际内容

### Step 7.2：补充测试

**文件：**`tests/` 目录

**要求：**

*   确保新增代码的测试覆盖率 > 80%
*   补充 E2E 测试：数据驱动创作链、用户驱动创作链、单 Agent 调用、Orchestrator 路由
*   运行全部测试，确保无回归

***

## 执行检查清单

每个 Phase 完成后，Claude Code 必须执行：



```
□ 运行全部已有测试（254个）→ 无回归
□ 运行新增测试 → 全部通过
□ 手动验证核心流程（用户驱动模式完整创作）→ 可用
□ 检查是否有文件被意外删除或重命名
□ 检查新增 API 端点的鉴权是否正确
□ 检查 Prompt 文件修改后 LLM 输出格式是否符合 Pydantic model
□ 更新进度记录（哪个 Phase、哪些 Step、完成状态）
```

***

## 预期收益

| 指标 | 当前 | 重构后 |
| --- | --- | --- |
| 单 Agent 可独立调用 | 不可以 | 12 个 Agent 全部可独立调用 |
| 合规反馈 | 盲改，最多 2 次后放弃 | 结构化反馈，精准修改 |
| 合规检查耗时 | 196s（3次全文检查） | ~80s（1次全面+1次定向复查） |
| 全流程耗时 | 297s | ~150s（并行+精准修改） |
| 选题能力 | 游离在流程外 | 集成到创作流程，支持数据驱动模式 |
| Orchestrator | 硬编码 2 步路由 | 7 种意图智能调度 |
| 前端灵活性 | 只能跑完整流程 | 工具箱 + 双模式创作 |

***

## 执行顺序与依赖关系



```
Phase 1（Agent独立调用）
  ↓
Phase 2（Agent间通信）  ← 依赖 Phase 1 的 BaseAgentRunner
  ↓
Phase 3（选题接入）     ← 依赖 Phase 1 的独立调用 + Phase 2 的 Chain
  ↓
Phase 4（合规闭环）     ← 依赖 Phase 2 的 ComplianceFeedback
  ↓
Phase 5（Orchestrator） ← 依赖 Phase 1 的 AgentTool
  ↓
Phase 6（前端适配）     ← 依赖 Phase 3 的双模式 API
  ↓
Phase 7（清理文档）     ← 最后执行
```

Phase 1 和 Phase 2 是基础，必须严格按顺序完成。Phase 3 和 Phase 4 可以并行。Phase 5 依赖 Phase 1。Phase 6 依赖 Phase 3。Phase 7 最后。