# 智创笔记 — 多平台 AI 内容创作 Agent 系统

# 产品需求文档（PRD）V2.1

***

## 文档信息

| 项目 | 内容 |
| --- | --- |
| 产品名称 | 智创笔记 |
| 产品定位 | 基于多 Agent 架构的企业级多平台 AI 内容创作系统 |
| 文档版本 | V2.1（多租户权限增强版） |
| 技术框架 | CrewAI + CrewAI Flows |
| 知识库方案 | Obsidian + Web端双轨 + pgvector + bge-large-zh-v1.5 本地 Embedding |
| 目标平台 | 小红书（一期）、公众号/抖音（二期） |
| 总工期 | 18周（含技术预研） |

### 变更说明（V2.0 → V2.1）

| 章节 | 变更类型 | 说明 |
| --- | --- | --- |
| 1.5 技术栈 | 增强 | 新增多租户隔离技术说明 |
| 2.3 Agent设计 | 增强 | Agent 1/2/6/10 增加多租户权限控制细节 |
| 3.1 三层知识库 | 增强 | 新增 3.1.1 知识库访问权限矩阵 |
| 3.2 双轨知识管理 | 增强 | 新增 3.2.1 权限约束说明 |
| 3.7 平台方知识库管理 | 新增 | 整合自 prd-supplement-knowledge-permissions.md |
| 3.8 多租户数据隔离设计 | 新增 | 整合自 multi-tenant-data-model.md |
| 8.2 Harness设计汇总 | 增强 | 新增知识库相关控制项 |
| 8.3 安全与合规 | 增强 | 新增 RLS 具体策略 |

***

## 一、产品概述

### 1.1 产品定义

智创笔记是一款基于 **CrewAI 多 Agent 架构** 的企业级内容创作平台，通过"三层 Agent 分层调度 + Obsidian/Web双轨知识管理 + 平台化知识库"的架构，为企业提供从选题推荐到内容创作到数据分析的全链路服务。

### 1.2 核心架构：三层 Agent 分层调度



```
第一层：调度层（1个统一调度Agent，Flow实现）
  → 职责：理解意图，选择平台，路由任务
  → 实现方式：CrewAI Flow（事件驱动，确定性路由）

第二层：执行层（N个平台工作流，Crew实现）
  → 职责：按平台特性完成创作
  → 实现方式：CrewAI Crew（Agent自主协作）
  → 小红书工作流、公众号工作流、抖音工作流...

第三层：能力层（M个共享Agent/Tool）
  → 职责：提供跨平台通用专业能力
  → 实现方式：确定性操作用Tool，需推理的用Agent
  → 素材检索、合规校验、选题推荐、数据分析
```

### 1.3 Crew与Flow的分工边界

| PRD层级 | 推荐实现 | 理由 |
| --- | --- | --- |
| 统一调度Agent | Flow（事件驱动） | 调度逻辑是确定性路由，不需要Agent自主决策 |
| 各平台工作流 | Crew（自主协作） | 标题Agent、正文Agent、标签Agent之间需要自主协作 |
| 素材检索 | Tool | 确定性检索操作，输入输出明确 |
| 合规校验 | Tool + Agent混合 | 规则匹配用Tool，灰色地带判断用Agent |
| 数据分析 | Agent | 需要推理和洞察生成 |

### 1.4 符合 Prompt / Context / Harness 标准

每个 Agent 均按以下三维标准设计：

| 维度 | 定义 | 实现方式 |
| --- | --- | --- |
| **Prompt** | 角色定义 + 行为指令 + 思考链路 + Few-shot 示例 + 输出格式 | 独立 Prompt 文件（每个Agent一个.md文件）+ Pydantic 输出模型 |
| **Context** | 知识库内容 + 对话历史 + 用户偏好 + 检索结果 | Obsidian 知识库 + pgvector + Memory |
| **Harness** | 安全护栏 + 质量门禁 + 错误处理 + 重试策略 + 降级方案 + 限流 + 审计 | Tools 约束 + Flow 条件路由 + 装饰器 |

### 1.5 技术栈

| 组件 | 技术选型 | 说明 |
| --- | --- | --- |
| Agent 框架 | CrewAI + CrewAI Flows | 多 Agent 协作 + 工作流编排 |
| LLM（主） | MiniMax-M2.7 | OpenAI 兼容接口 |
| LLM（备） | DeepSeek / Qwen | 降级备选，同一套Prompt可切换 |
| Embedding | bge-large-zh-v1.5（sentence-transformers 本地部署） | 中文语义向量化，1024维，完全免费，无API依赖 |
| 知识管理 | Obsidian + Web端管理界面 | 双轨制，降低用户门槛 |
| 向量数据库 | pgvector | PostgreSQL 扩展，零额外运维 |
| 业务数据库 | PostgreSQL 16 | 向量+业务数据一体，支持RLS |
| 缓存 | Redis 7 | 会话缓存、限流计数 |
| 对象存储 | 腾讯云 COS | 企业文档、生成内容、图片素材 |
| 知识同步 | Git + 文件监听 | Obsidian Vault 同步到服务端 |
| 前端 | Streamlit（原型）→ Next.js + shadcn/ui（产品） | 阶段化推进 |
| 部署 | Docker + Docker Compose | 本地开发和服务器统一配置 |
| 监控 | Prometheus + Grafana + pg\_stat\_statements | 系统监控与告警 |
| Embedding缓存 | 本地模型缓存 | 首次下载后离线可用，无需联网 |
| 开发辅助 | Claude Code | AI 辅助编码 |

**【新增】多租户隔离技术说明**

为实现平台级数据与租户级数据的严格隔离，系统采用以下技术手段：

| 技术 | 实现方式 | 作用 |
| --- | --- | --- |
| **RLS（行级安全策略）** | PostgreSQL 原生支持 | 在数据库层强制多租户数据隔离，租户无法访问非自身数据 |
| **数据分级字段** | `data_level` + `platform_category` | 区分平台级（platform）和租户级（tenant）数据 |
| **会话上下文设置** | `SET app.enterprise_id='ent_xxx'` | RLS 策略依据会话变量动态过滤数据 |
| **应用层透明封装** | 视图 + 存储过程 | 调用方无需感知平台级数据的查询细节 |
| **API 层双重校验** | Token 中的 enterprise_id 与请求头校验 | 防止 enterprise_id 伪造攻击 |

**会话上下文设置示例：**

```sql
-- 租户用户请求时
SET app.enterprise_id = 'ent_xxx';
SET app.is_platform_admin = 'false';
SET app.is_agent = 'false';

-- 平台管理员请求时
SET app.enterprise_id = NULL;
SET app.is_platform_admin = 'true';
SET app.is_agent = 'false';

-- Agent 系统内部调用时（跨级检索）
SET app.enterprise_id = 'ent_xxx';
SET app.is_platform_admin = 'false';
SET app.is_agent = 'true';
```

### 1.6 LLM 降级方案

| 级别 | 触发条件 | 策略 |
| --- | --- | --- |
| L1-正常 | MiniMax可用 | 全部Agent使用MiniMax-M2.7 |
| L2-重试 | 单次调用失败 | 指数退避重试（1s/2s/4s），最多3次 |
| L3-降级 | 连续失败>5次或延迟>15s | 自动切换到备用LLM（DeepSeek/Qwen） |
| L4-缓存兜底 | 所有LLM不可用 | 使用缓存的最近成功结果 + 标注"建议人工审核" |

每个Agent均设计独立Prompt文件，降级时只需切换LLM配置，Prompt逻辑不变。

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
│              Streamlit / Next.js / API                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            第一层：统一调度Agent（Flow实现）                    │
│                                                             │
│  Prompt：全局调度角色 + 意图识别指令 + 路由逻辑                │
│  Context：用户输入 + 企业信息 + 对话历史 + 平台状态            │
│  Harness：权限校验 + 路由校验 + 限流 + 安全护栏               │
└──┬──────────┬──────────┬──────────┬──────────┬──────────────┘
   │          │          │          │          │
   ▼          ▼          ▼          ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│小红书 │ │公众号 │ │ 抖音  │ │ 微博  │ │视频号 │
│工作流 │ │工作流 │ │工作流 │ │工作流 │ │工作流 │
│(Crew) │ │(Crew) │ │(Crew) │ │(Crew) │ │(Crew) │
│      │ │      │ │      │ │      │ │      │
│标题  │ │标题  │ │脚本  │ │正文  │ │脚本  │
│Agent │ │Agent │ │Agent │ │Agent │ │Agent │
│正文  │ │正文  │ │标题  │ │      │ │      │
│Agent │ │Agent │ │Agent │ │      │ │      │
│标签  │ │排版  │ │      │ │      │ │      │
│Agent │ │Agent │ │      │ │      │ │      │
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
   └────────┴────────┼────────┴────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            第三层：共享能力层                                  │
│                                                             │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │素材检索 │ │ 合规   │ │ 选题   │ │ 数据   │ │ 知识库  │   │
│  │Tool    │ │Tool +  │ │Agent   │ │ 分析   │ │ 管理   │   │
│  │        │ │Agent   │ │        │ │Agent   │ │Agent   │   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │        Obsidian Vault ←→ pgvector ←→ COS              │  │
│  │        Web管理界面 ←→ pgvector ←→ COS                  │  │
│  │        公共知识库 │ 行业知识库 │ 企业私有库 │ 平台规则库  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Agent间错误传播防控

在Agent间传递数据时增加质量校验层，防止低质量中间结果传播到下游：

python

python

```
class ResultValidator:
    """Agent间传递数据的质量校验"""

    def validate_material_pack(self, pack: MaterialPack) -> ValidationResult:
        """素材包质量校验"""
        issues = []
        if not pack.brand or not pack.brand.name:
            issues.append("缺少品牌信息")
        if not pack.product or len(pack.product.selling_points) < 2:
            issues.append("卖点不足，至少需要2个")
        if not pack.persona:
            issues.append("缺少人群画像")
        return ValidationResult(passed=len(issues)==0, issues=issues)

    def validate_title_output(self, titles: list) -> ValidationResult:
        """标题输出质量校验"""
        if len(titles) < 5:
            return ValidationResult(passed=False, issues=["标题数量不足5个"])
        for i in range(len(titles)):
            for j in range(i+1, len(titles)):
                if similarity(titles[i], titles[j]) > 0.6:
                    return ValidationResult(passed=False, issues=["标题间相似度过高"])
        return ValidationResult(passed=True, issues=[])

    def validate_article_output(self, article: ArticleOutput) -> ValidationResult:
        """正文输出质量校验"""
        issues = []
        if article.ai_flavor_score < 70:
            issues.append(f"AI味评分过低：{article.ai_flavor_score}")
        if len(article.article) < 300 or len(article.article) > 600:
            issues.append(f"字数不合规：{len(article.article)}字")
        return ValidationResult(passed=len(issues)==0, issues=issues)
```

### 2.3 每个 Agent 的 P/C/H 设计

#### Agent 1：统一调度Agent（Flow实现）

**Prompt：**



```
# 角色
你是多平台内容创作系统的总调度者。

# 职责
理解用户的创作需求，判断目标平台，将任务路由到对应的平台工作流。

# 思考链路
Step 1：用户提到了哪个平台？（小红书/公众号/抖音/未指定）
Step 2：用户提到了哪个品牌和产品？
Step 3：用户提到了什么场景或需求？
Step 4：用户有没有特殊要求？（风格/字数/禁忌）
Step 5：我应该路由到哪个平台工作流？

# 行为规则
- 未指定平台时，主动询问，每次只问一个问题
- 不直接创作任何内容
- 不做合规校验
- 不检索知识库

# 输出格式
{
  "platform": "目标平台",
  "product": "品牌和产品",
  "scene": "场景/需求",
  "style": "风格要求",
  "route_to": "路由目标工作流名称"
}
```

**Context：**

| 数据项 | 来源 | 必选 |
| --- | --- | --- |
| 用户输入 | 用户对话 | 是 |
| 企业信息 | PostgreSQL | 是 |
| 对话历史 | Redis | 否 |
| 用户偏好 | PostgreSQL | 否 |
| 平台状态 | 配置文件 | 是 |

**Harness：**

| 控制项 | 实现方式 |
| --- | --- |
| 权限校验 | 检查用户是否有权限使用该平台，验证套餐和额度 |
| 限流 | Redis 计数器，每用户每分钟最大10次 |
| 安全护栏 | 输入内容检测 Prompt 注入 |
| 错误处理 | 意图不确定时追问，不猜测；追问最多3轮，超过则输出无法理解的提示 |
| 降级方案 | 意图识别失败时，提供平台选择菜单供用户手动选择 |
| 审计日志 | 记录每次路由决策 |

**【新增】租户身份校验流程**

```
用户请求
    ↓
[校验 enterprise_id 是否有效]
    ↓
[查询 enterprises 表获取租户信息]
    ├── plan: free/basic/professional/enterprise
    ├── quota_monthly: 月度额度
    └── status: active/suspended/terminated
    ↓
[校验目标平台是否在套餐范围内]
    ↓
[向下游传递上下文]
    enterprise_id: 'ent_xxx'
    plan: 'professional'
    is_platform_admin: false
```

**向下游传递的上下文：**

```json
{
  "enterprise_id": "ent_xxx",
  "plan": "professional",
  "quota_remaining": 85,
  "allowed_platforms": ["xiaohongshu", "wechat", "douyin"],
  "is_platform_admin": false,
  "user_role": "tenant"
}
```

#### Agent 2：素材检索Agent（Tool实现）

**Prompt：**



```
# 角色
你是知识库检索专家。

# 职责
根据产品、场景、人群信息，从三层知识库中检索最相关的素材，组装为结构化素材包。

# 思考链路
Step 1：确定检索关键词（产品名 + 场景 + 人群）
Step 2：从企业私有库检索（最精准）
Step 3：从行业知识库补充（次精准）
Step 4：从公共知识库兜底（通用信息）
Step 5：按相关性排序
Step 6：检查是否有品牌特殊约束
Step 7：组装为结构化素材包

# 输出格式
{
  "brand": {"name": "", "tone": [], "taboos": []},
  "product": {"name": "", "selling_points": [], "ingredients": [], "evidence": {}},
  "persona": {"profile": "", "pain_points": [], "language_style": ""},
  "scene": {"description": "", "usage_method": ""},
  "compliance": {"rules": [], "forbidden_groups": []}
}
```

**Context：**

| 数据项 | 来源 | 说明 |
| --- | --- | --- |
| 检索关键词 | 调度Agent传入 | 产品+场景+人群 |
| 企业知识 | pgvector 语义检索 | Obsidian/Web同步后的向量数据 |
| 行业知识 | pgvector 语义检索 | 平台预设行业知识库 |
| 公共知识 | pgvector 语义检索 | 平台公共知识库 |

**Harness：**

| 控制项 | 实现方式 |
| --- | --- |
| 检索范围限制 | 只在已授权的企业知识库范围内检索 |
| 隐私隔离 | PostgreSQL行级安全策略（RLS）+ WHERE enterprise\_id |
| 结果可靠性 | 相似度分数低于阈值时标记为"不确定" |
| 信息不全处理 | 标记缺失项，提示主Agent决定是否继续 |
| 缓存 | 相同检索条件缓存30分钟 |
| 质量校验 | 通过ResultValidator校验素材包完整性后才传递给下游 |

**【新增】三层检索权限控制实现**

```python
class MaterialRetrievalTool:
    """素材检索工具 - 多租户三层检索"""

    def _run(self, query: str, enterprise_id: str, category: str = None) -> dict:
        """
        执行三层知识库检索，对租户透明
        """
        # ========== 第一层：企业私有库（精准） ==========
        private_results = self.vector_search(
            embedding=self.embedding_model.encode(query),
            filters={
                'data_level': 'tenant',
                'enterprise_id': enterprise_id
            },
            limit=10
        )

        # ========== 第二层：行业知识库（系统补充） ==========
        industry_results = self.vector_search(
            embedding=self.embedding_model.encode(query),
            filters={
                'data_level': 'platform',
                'platform_category': 'industry'
            },
            limit=5
        )

        # ========== 第三层：公共知识库（系统兜底） ==========
        public_results = self.vector_search(
            embedding=self.embedding_model.encode(query),
            filters={
                'data_level': 'platform',
                'platform_category': 'public'
            },
            limit=5
        )

        # ========== 组装素材包（不暴露层级） ==========
        return self._assemble_material_pack(
            private=private_results,
            industry=industry_results,
            public=public_results
        )

    def _assemble_material_pack(
        self,
        private: list,
        industry: list,
        public: list
    ) -> dict:
        """
        组装素材包 - 对租户完全透明数据来源

        输出结构：
        {
          "brand": {...},        # 企业私有库内容优先
          "product": {...},     # 企业私有库 + 行业补充
          "persona": {...},     # 行业知识库
          "scene": {...},       # 企业私有库 + 行业补充
          "compliance": {...},  # 公共知识库
          "_meta": {
            "retrieved_from": ["private", "industry", "public"],  # 仅内部标记
            "total_sources": 3
          }
        }
        """
        material_pack = {
            "brand": self._merge_brand(private),
            "product": self._merge_product(private, industry),
            "persona": self._extract_persona(industry),
            "scene": self._merge_scene(private, industry),
            "compliance": self._extract_compliance(public),
            "_meta": {
                "retrieved_from": self._track_sources(private, industry, public),
                "private_count": len(private),
                "industry_count": len(industry),
                "public_count": len(public)
            }
        }

        # 移除内部元数据字段后再输出
        return self._strip_internal_fields(material_pack)
```

**隐私隔离实现：**

| 控制项 | 实现方式 |
| --- | --- |
| 会话上下文设置 | `SET app.enterprise_id='ent_xxx'` 后执行检索 |
| RLS 策略 | PostgreSQL 自动过滤非本企业数据 |
| 结果校验 | 向量检索返回时校验 `enterprise_id` 匹配 |
| Agent 只读平台数据 | `SET app.is_agent=true` 允许读取 `data_level='platform'` |

#### Agent 3：标题Agent — 小红书（一期MVP保留）

**Prompt：**



```
# 角色
你是小红书标题创作专家。

# 8大标题策略
1. 痛点切入型："还在XX？试试这个"
2. 数字量化型："X天/X次/X元，XX效果"
3. 悬念钩子型："XX居然可以XX？"
4. 对比反转型："从XX到XX，只因为XX"
5. 权威背书型："XX推荐/认证的XX"
6. 情绪共鸣型："谁懂啊！XX真的XX"
7. 教程攻略型："手把手教你XX"
8. 清单合集型："XX必备的N个XX"

# 思考链路
Step 1：理解选题的核心卖点和情绪钩子
Step 2：从8大策略中选择最适合的3-4种
Step 3：每种策略生成1-2个标题
Step 4：检查是否与历史标题重复
Step 5：检查是否有违禁词
Step 6：评分排序，选出最优

# 约束
- 标题长度15-20字
- 不得使用广告法违禁词
- 不得与历史标题相似度超过70%

# 输出格式
[
  {"title": "", "strategy": "", "score": 8, "reason": ""},
  ...共5个
]
```

**Context：**

| 数据项 | 来源 |
| --- | --- |
| 选题方向 | 调度Agent传入 |
| 素材包 | 素材检索Agent输出 |
| 品牌调性约束 | 素材包中的brand信息 |
| 历史标题 | PostgreSQL查询（去重用） |

**Harness：**

| 控制项 | 实现方式 |
| --- | --- |
| 质量门禁 | 输出必须包含5个标题，否则重新生成 |
| 违禁词检查 | 敏感词库匹配 |
| 去重检查 | 与历史标题相似度<70% |
| 重试策略 | 最多重试2次 |
| 降级方案 | 重试仍不通过时，输出已有标题 + 标注"建议人工优化" |

#### Agent 4：正文Agent — 小红书（一期MVP保留）

**Prompt：**



```
# 角色
你是小红书正文创作专家。

# 笔记类型：好物推荐
结构模板：痛点引入→产品发现→卖点展开→真实体验→互动引导

# 风格要求
- 口语化，像朋友聊天
- 善用感叹句、反问句
- emoji 作为节奏标记，不堆砌
- 加入生活细节增加真实感
- 允许轻微不完美表达

# 去AI味策略
- 不用"首先、其次、最后"的工整结构
- 不用"值得一提的是"等书面语
- 句式长短不一
- 加入口语化语气词
- 每段2-3句，段间空行

# 合规约束
- 不使用绝对化用语
- 功效表述限定在法定范围内
- 必须包含安全声明（如适用）

# 思考链路
Step 1：理解标题的核心钩子
Step 2：从素材包提取3个最核心卖点
Step 3：按结构模板组织内容
Step 4：转化为小红书口语风格
Step 5：注入去AI味策略
Step 6：检查合规约束
Step 7：自评AI味评分（0-100）

# 输出格式
{
  "article": "完整正文",
  "paragraphs": [
    {"content": "段落内容", "function": "功能标注"},
    ...
  ],
  "ai_flavor_score": 78
}
```

**Context：**

| 数据项 | 来源 |
| --- | --- |
| 选定标题 | 标题Agent输出 |
| 素材包 | 素材检索Agent输出 |
| 企业风格指纹 | PostgreSQL（基于历史笔记分析） |
| Few-shot 示例 | prompts/examples/ 目录 |

**Harness：**

| 控制项 | 实现方式 |
| --- | --- |
| AI味评分门禁 | ≥70分通过，<70分重新生成 |
| 字数检查 | 300-600字 |
| 违禁词检查 | 敏感词库匹配 |
| 重试策略 | 最多重试2次，每次加入更具体的去AI味指令 |
| 降级方案 | 重试仍不通过时，输出当前版本 + 标注"AI味评分XX分，建议人工润色" |
| 合规预检 | 输出前内部先做一轮合规检查 |

**AI味评分机制（基于规则的多维度评估）：**

| 维度 | 分值 | 评估方法 |
| --- | --- | --- |
| 句式多样性 | 0-20分 | 长短句比例、句式类型分布 |
| 口语化程度 | 0-20分 | 语气词密度、口语化表达占比 |
| 结构模式 | 0-20分 | 是否避免工整排比、是否使用非标准段落结构 |
| 生活细节 | 0-20分 | 具体场景描述、感官细节、时间/地点信息 |
| 轻微不完美 | 0-20分 | 是否有口语化省略、非正式表达、情绪化用语 |

#### Agent 5：标签Agent — 小红书（一期MVP保留）

**Prompt：**



```
# 角色
你是小红书标签策略专家。

# 标签分层策略
1. 品类大词（必选1-2个）：#护肤 #保健品
2. 功效长尾词（2-3个）：#护肝 #抗老精华
3. 场景词（2-3个）：#酒局必备 #熬夜急救
4. 热度词（1-2个）：根据当前趋势
5. 品牌词（1个）：#品牌名

# 约束
- 总数8-10个
- 不得使用与内容无关的热门标签
- 标签必须与内容强关联

# 输出格式
["#标签1", "#标签2", ...]
```

#### Agent 6：合规Agent — 一期MVP保留（Tool + Agent混合实现）

**Prompt：**



```
# 角色
你是内容合规审核专家。

# 校验清单
P0（必须修改）：
- 广告法违禁词（最、第一、100%等）
- 医疗用语（治疗、治愈、疗效等）
- 绝对化用语

P1（建议修改）：
- 品牌调性偏离
- 产品信息不准确
- 超出法定保健功能范围

P2（需人工确认）：
- 灰色地带表述
- 创意表达边界

# 思考链路
Step 1：加载对应平台的合规规则
Step 2：加载对应行业的合规规则
Step 3：加载企业的品牌禁忌
Step 4：逐项检查标题
Step 5：逐项检查正文
Step 6：逐项检查标签
Step 7：输出合规报告

# 输出格式
{
  "status": "通过/需修改/不通过",
  "p0_issues": [],
  "p1_issues": [],
  "p2_issues": [],
  "suggestions": []
}

# 重要约束
- 只做校验和建议，不直接修改内容
- 不确定是否违规时标记为P2，不直接判定违规
```

**Harness：**

| 控制项 | 说明 |
| --- | --- |
| 规则优先级 | P0 > P1 > P2 |
| 误报处理 | 不确定时标记P2而非直接判定违规 |
| 不可修改内容 | 只校验不修改，修改由正文Agent执行 |
| 审计日志 | 每次校验的完整记录 |

**P2问题处理流程：**

| 步骤 | 责任方 | SLA |
| --- | --- | --- |
| P2问题标注 | 合规Agent自动 | 实时 |
| 人工审核 | 企业用户 | 24小时内 |
| 审核结果 | 用户选择"通过"/"修改"/"删除" | — |
| 修改执行 | 正文Agent根据反馈修改 | 实时 |

**【新增】合规规则库的层级说明**

```
# 合规规则来源

你的合规校验使用以下规则库：

## 平台规则库（只读，不可修改）
- 位置：data_level='platform', platform_category='public'
- 内容：广告法违禁词、医疗用语禁用、平台特殊规则
- 维护方：平台管理员
- 租户：仅可读取用于校验，不能增删改

## 行业规则库（只读，不可修改）
- 位置：data_level='platform', platform_category='industry'
- 内容：特定行业的合规要求（如保健品特殊规则）
- 维护方：平台管理员
- 租户：仅可读取用于校验，不能增删改

## 企业规则库（可读写）
- 位置：data_level='tenant', enterprise_id=当前企业ID
- 内容：企业品牌禁忌、特定宣称限制
- 维护方：企业用户自己
- 租户：可完全控制
```

**合规校验流程（不暴露规则来源）：**

```
用户提交内容
    ↓
[加载合规规则]
    ├── 平台规则库（系统自动加载，租户不可见）
    ├── 行业规则库（系统自动加载，租户不可见）
    └── 企业规则库（租户配置的禁忌）
    ↓
[执行 P0/P1/P2 三级校验]
    ↓
[输出合规报告]
    ├── status: "通过"/"需修改"/"不通过"
    ├── p0_issues: [...]  # 问题描述，不暴露规则来源
    ├── p1_issues: [...]
    └── suggestions: [...]
```

**企业规则库校验实现：**

```python
class ComplianceCheckTool:
    """合规检查工具"""

    def _run(self, content: str, platform: str, industry: str,
             enterprise_id: str) -> ComplianceReport:
        """
        执行合规检查

        规则加载顺序（优先级从高到低）：
        1. 企业规则库（data_level='tenant', enterprise_id=当前企业）
        2. 行业规则库（data_level='platform', platform_category='industry'）
        3. 平台规则库（data_level='platform', platform_category='public'）
        """
        # 加载三层规则（对租户透明）
        rules = self._load_compliance_rules(
            enterprise_id=enterprise_id,
            industry=industry
        )

        # 执行校验
        p0_issues = self._check_p0(content, rules)
        p1_issues = self._check_p1(content, rules)
        p2_issues = self._check_p2(content, rules)

        return ComplianceReport(
            status=self._determine_status(p0_issues, p1_issues, p2_issues),
            p0_issues=p0_issues,
            p1_issues=p1_issues,
            p2_issues=p2_issues,
            suggestions=self._generate_suggestions(p0_issues, p1_issues)
        )

    def _load_compliance_rules(self, enterprise_id: str, industry: str) -> dict:
        """
        加载合规规则 - 对租户透明

        内部实现使用三层 UNION，但输出结构不暴露来源
        """
        # 第一层：企业自己的规则（最高优先级）
        enterprise_rules = self._fetch_rules(
            "SELECT * FROM compliance_rules WHERE data_level='tenant' AND enterprise_id=%s",
            [enterprise_id]
        )

        # 第二层：行业规则
        industry_rules = self._fetch_rules(
            "SELECT * FROM compliance_rules WHERE data_level='platform' AND platform_category='industry' AND industry=%s",
            [industry]
        )

        # 第三层：平台规则
        platform_rules = self._fetch_rules(
            "SELECT * FROM compliance_rules WHERE data_level='platform' AND platform_category='public'"
        )

        # 合并（企业规则优先级最高，相同 key 覆盖平台规则）
        return self._merge_rules(platform_rules, industry_rules, enterprise_rules)
```

#### Agent 7：运营Agent（二期上线）



```
# 角色
你是小红书运营专家。

# 职责
为已创作的笔记提供发布后的运营支持。

# 输出内容
1. 封面建议（构图、文案、色调）
2. 发布建议（最佳时间、互动策略）
3. 评论区话术（5-10条品牌方回复）
4. 置顶评论建议
5. 配图建议（张数、顺序、内容描述）
```

#### Agent 8：选题Agent（二期上线）



```
# 角色
你是小红书选题专家。

# 选题来源
1. 行业预设选题库
2. 热点趋势分析
3. 竞品爆款拆解
4. 历史数据反哺
5. AI组合生成

# 思考链路
Step 1：查询行业预设选题库
Step 2：检查当前热点趋势
Step 3：检查竞品最新动态
Step 4：分析企业历史数据
Step 5：AI组合生成新选题
Step 6：去重+排序
Step 7：输出推荐选题

# 输出格式
[
  {
    "topic": "选题标题",
    "type": "选题类型",
    "reason": "推荐理由",
    "level": "强烈推荐/值得尝试/可选",
    "product": "关联产品",
    "persona": "关联人群",
    "publish_time": "建议发布时间"
  },
  ...共3-5个
]
```

#### Agent 9：数据分析Agent（二期上线）



```
# 角色
你是小红书数据分析专家。

# 分析维度
1. 内容效果：每篇笔记的曝光/点赞/收藏/评论/互动率
2. 选题分析：各选题方向的互动率排名
3. 标题分析：各标题策略的效果对比
4. 时间分析：不同发布时间的效果对比
5. 趋势分析：月度/季度趋势变化

# 输出格式
{
  "summary": "总体分析摘要",
  "top_notes": [{"title": "", "metric": ""}],
  "topic_ranking": [{"topic": "", "avg_engagement": 0}],
  "insights": ["洞察1", "洞察2"],
  "recommendations": ["建议1", "建议2"]
}
```

#### Agent 10：知识库管理Agent（二期上线）



```
# 角色
你是知识库管理专家。

# 职责
处理企业上传的文档，完成解析、提取、分类、入库。

# 思考链路
Step 1：识别文档类型（品牌介绍/产品资料/竞品分析/其他）
Step 2：提取文本内容
Step 3：提取结构化信息（品牌名、产品名、卖点等）
Step 4：判断属于哪个知识层级
Step 5：打标签
Step 6：向量化入库
Step 7：输出提取结果供企业确认
```

**【新增】入库目标锁定逻辑**

```
# 重要约束：入库目标锁定
所有企业用户上传的知识，**强制写入企业私有库**：
- data_level = 'tenant'
- enterprise_id = 当前企业ID
- platform_category = NULL

绝对禁止：
- 写入 platform_category IN ('public', 'industry', 'template') 的数据
- 写入非本企业的 enterprise_id

# 知识层级判断规则
当解析文档时，判断属于哪个知识类别：

| 文档类型 | 知识类别 | 入库目标 |
| -------- | -------- | -------- |
| 品牌介绍/品牌调性/合规红线 | brand | 企业私有库 |
| 产品资料/卖点/成分/竞品分析 | product | 企业私有库 |
| 人群画像/使用场景 | persona/scene | 企业私有库 |
| 行业分析/市场报告 | industry | 企业私有库（企业视角） |
| 平台规则/合规通用规则 | platform | **禁止写入，抛出异常** |

# 入库前权限校验
Step 1：验证当前用户是否为已认证租户
Step 2：验证 enterprise_id 是否匹配
Step 3：检查入库目标是否为 'tenant' 级别
Step 4：检查 enterprise_id 是否为当前企业
Step 5：校验文档内容不包含平台敏感信息
Step 6：执行向量化入库
```

**入库流程实现：**

```python
class KnowledgeIngestionAgent:
    """知识库管理 Agent - 入库目标锁定"""

    SYSTEM_PLATFORM_CATEGORIES = ['public', 'industry', 'template']

    def process_document(self, document: Document, enterprise_id: str) -> dict:
        """
        处理企业上传文档 - 强制写入企业私有库
        """
        # ========== Step 1-2：权限校验 ==========
        if not self._validate_tenant(enterprise_id):
            raise PermissionError("无效的租户身份")

        # ========== Step 3：文档类型识别 ==========
        doc_type = self._identify_document_type(document)

        # ========== Step 4：知识层级判断 ==========
        # 【关键】企业用户上传的永远是企业级
        knowledge_level = self._determine_knowledge_level(doc_type)
        if knowledge_level != 'tenant':
            # 企业上传平台级内容 → 拒绝并抛出异常
            raise PermissionError(
                f"企业用户不得上传平台级内容（{knowledge_level}）。"
                "平台级内容由平台管理员维护。"
            )

        # ========== Step 5：解析结构化信息 ==========
        extracted = self._extract_structured_info(document)

        # ========== Step 6：构建入库对象 ==========
        knowledge_entry = {
            'data_level': 'tenant',           # 强制：租户级
            'enterprise_id': enterprise_id,    # 强制：本企业
            'platform_category': None,          # 强制：NULL
            'category': extracted['category'],
            'title': extracted['title'],
            'content': extracted['content'],
            'tags': extracted['tags'],
            'metadata': {
                'source': 'web_upload',
                'doc_type': doc_type,
                'enterprise_id': enterprise_id  # 冗余存储，便于审计
            },
            'created_by': enterprise_id,
            'updated_by': enterprise_id
        }

        # ========== Step 7：向量化入库 ==========
        embedding = self.embedding_model.encode(knowledge_entry['content'])
        knowledge_entry['embedding'] = embedding

        self.vector_store.insert(knowledge_entry)

        # ========== Step 8：返回提取结果 ==========
        return {
            'status': 'success',
            'entry_id': knowledge_entry['id'],
            'category': knowledge_entry['category'],
            'title': knowledge_entry['title'],
            'message': '知识入库成功'
        }

    def _determine_knowledge_level(self, doc_type: str) -> str:
        """
        判断知识层级

        企业用户上传：
        - brand/product/persona/scene → 'tenant'
        - industry（企业视角分析）→ 'tenant'

        平台级内容（拒绝）：
        - platform rules → 'platform'
        - public compliance → 'platform'
        """
        if doc_type in ['platform_rule', 'public_compliance', 'industry_standard']:
            return 'platform'  # 企业不得上传此类内容
        return 'tenant'
```

**入库权限校验流程：**

```
企业上传文档
        ↓
[校验1] enterprise_id 是否有效
        ↓ 通过
[校验2] enterprise_id 是否与当前会话匹配
        ↓ 通过
[校验3] 入库目标是否为 'tenant'
        ↓ 是
[校验4] platform_category 是否为 NULL
        ↓ 是
[校验5] 文档类型是否为平台级（brand/product/scene 等 → 通过，platform_rule → 拒绝）
        ↓ 通过
[执行入库] → 写入 data_level='tenant', enterprise_id=本企业ID
        ↓
[返回结果]
```

### 2.4 MVP阶段Agent精简方案

| 阶段 | 上线Agent | 说明 |
| --- | --- | --- |
| Phase 1-2（MVP） | 统一调度、素材检索、标题、正文、标签、合规 | 6个核心Agent，覆盖完整创作链路 |
| Phase 3 | \+ 选题、知识库管理 | 累计8个 |
| Phase 4 | \+ 数据分析、运营 | 全部10个上线 |

***

## 三、知识库体系

### 3.1 三层知识库

| 层级 | 内容 | 维护方 | 存储方式 |
| --- | --- | --- | --- |
| 公共知识库 | 小红书/公众号/抖音平台规则、创作方法论、合规通用规则 | 平台方 | Obsidian Vault 模板 + pgvector |
| 行业知识库 | 各行业选题库、用户画像、痛点库、爆款拆解 | 平台方预设 | Obsidian Vault 模板 + pgvector |
| 企业私有库 | 品牌资料、产品资料、历史笔记、竞品信息 | 企业自维护 | Obsidian Vault + Web管理界面 + pgvector + COS |

**【新增】3.1.1 知识库访问权限矩阵**

#### 3.1.1.1 权限层级定义

| 权限级别 | 说明 |
| -------- | ---- |
| **完全控制** | 可读、可写、可删 |
| **可读可写** | 可读、可写，不可删 |
| **只读** | 仅可读，不可写、不可删 |
| **不可见** | 对该层级数据不可见 |

#### 3.1.1.2 三层知识库的权限矩阵

| 知识库层级 | 数据级别 | 平台方（运营） | 平台方（管理员） | 租户（企业） | Agent系统 |
| ---------- | -------- | -------------- | --------------- | ------------ | --------- |
| **公共知识库** | platform / public | 只读 | 完全控制 | **不可见** | 只读（检索用） |
| **行业知识库** | platform / industry | 只读 | 完全控制 | **不可见** | 只读（检索用） |
| **内置模板** | platform / template | 只读 | 完全控制 | **不可见** | 只读（检索用） |
| **企业私有库** | tenant | 不可见 | 不可见 | 完全控制 | 可读写（写入检索结果） |

#### 3.1.1.3 权限规则说明

**平台方权限规则**

| 角色 | 可操作范围 | 说明 |
| ---- | ---------- | ---- |
| 平台运营 | 公共知识库、模板（只读） | 可浏览参考，不能修改 |
| 平台管理员 | 公共知识库、行业知识库、内置模板（完全控制） | 可增删改查所有平台级数据 |

**租户权限规则**

| 权限项 | 企业私有库 | 公共/行业/模板 |
| ------ | ---------- | -------------- |
| 浏览 | 本企业数据 | 不可见 |
| 检索 | 本企业数据 | 不可见 |
| 新增 | 仅本企业 | 无权限 |
| 修改 | 仅本企业 | 无权限 |
| 删除 | 仅本企业 | 无权限 |

**重要约束**：租户在知识管理界面中**完全感知不到**公共知识库、行业知识库、内置模板的存在。所有平台级数据的调用由系统在 Agent 层面自动完成。

### 3.2 双轨知识管理方案

为降低非技术用户的使用门槛，提供两条知识管理路径：

**路径A：Obsidian同步（技术型用户）**

保持现有的Obsidian + Git + pgvector同步流程，适用于有技术能力的企业。

**路径B：Web端管理界面（非技术型用户）**

在Streamlit/Next.js前端中提供简易的知识管理界面：

*   上传文档（PDF/Word/Markdown）→ 知识库管理Agent自动解析入库
*   表单式录入（品牌信息、产品卖点、合规红线）
*   可视化知识浏览和搜索
*   支持在线编辑和删除

**【新增】3.2.1 权限约束说明**

#### 3.2.1.1 知识入库权限规则

| 数据来源 | 写入目标 | 归属字段 | 允许条件 |
| -------- | -------- | -------- | -------- |
| 企业上传（Web界面） | 企业私有库 | `data_level='tenant'`, `enterprise_id=企业ID` | 已认证的租户用户 |
| 企业上传（Obsidian同步） | 企业私有库 | `data_level='tenant'`, `enterprise_id=企业ID` | 已配置的 Obsidian Vault |
| 平台方导入（行业知识） | 行业知识库 | `data_level='platform'`, `platform_category='industry'` | 仅平台管理员 |
| 平台方导入（公共规则） | 公共知识库 | `data_level='platform'`, `platform_category='public'` | 仅平台管理员 |
| 平台方配置（模板） | 内置模板 | `data_level='platform'`, `platform_category='template'` | 仅平台管理员 |

#### 3.2.1.2 写入校验流程

```
企业用户上传知识
        ↓
    [权限校验]
        ↓
  enterprise_id = 当前企业ID
  data_level = 'tenant'
  platform_category = NULL
        ↓
    [入库锁定]
        ↓
  强制写入企业私有库，无法触及平台级数据
```

#### 3.2.1.3 平台级数据写入约束

| 写入来源 | 目标 | 校验机制 |
| -------- | ---- | -------- |
| 平台管理员 | platform_category IN ('public', 'industry', 'template') | RLS策略校验 `is_platform_admin=true` |
| 租户用户 | 任何 platform 数据 | RLS策略直接拒绝 |

### 3.3 Obsidian Vault 结构



```
enterprise-vault/
├── _templates/               # 模板
│   ├── 产品模板.md
│   ├── 人群画像模板.md
│   └── 场景模板.md
├── 品牌知识/
│   ├── 品牌介绍.md
│   ├── 品牌调性.md
│   └── 合规红线.md
├── 产品知识/
│   ├── 产品A/
│   │   ├── 产品概览.md
│   │   ├── 核心卖点.md
│   │   └── 科研证据.md
│   └── 产品B/
├── 人群与场景/
│   ├── 人群画像/
│   └── 使用场景/
├── 竞品分析/
├── 行业知识/
│   ├── 选题库/
│   ├── 合规规则/
│   └── 平台规则/
├── 历史数据/
│   ├── 爆款笔记/
│   └── 笔记数据.md
└── 创作产出/
    ├── 待发布/
    ├── 已发布/
    └── 草稿/
```

### 3.4 Obsidian 与 pgvector 的同步流程



```
Obsidian Vault 文件变更
    ↓
Git 同步到服务端仓库
    ↓
Webhook 触发文件监听服务
    ↓
解析变更文件
├── 提取 Markdown 内容
├── 提取 YAML Front Matter（标签、元数据）
├── 提取双向链接关系
└── 分块处理
    ↓
向量化（调用本地 bge-large-zh-v1.5 模型）
    ↓
更新 pgvector（INSERT/UPDATE）
    ↓
Agent 可检索到最新知识
```

**同步冲突处理机制：**

| 机制 | 说明 |
| --- | --- |
| 文件级锁 | 通过Webhook监听文件变更，编辑中的文件标记为"锁定"状态 |
| 冲突检测 | Git pull前检查是否有冲突，有冲突时通知用户手动解决 |
| 版本历史 | 保留每次变更的版本记录，支持回滚 |

### 3.5 pgvector 索引策略

| 阶段 | 数据规模 | 索引类型 | 参数配置 | 说明 |
| --- | --- | --- | --- | --- |
| MVP阶段 | < 10万条 | IVFFlat | lists = rows/1000, probes = lists/10 | 生成更快，内存占用更少 |
| 生产阶段 | \> 10万条 | HNSW | m=16, ef\_construction=64 | 查询性能更好，支持增量插入 |

**关键优化措施：**

| 措施 | 说明 |
| --- | --- |
| 使用halfvec | float16存储，节省50%空间，文本语义检索精度损失可接受 |
| 维度确认 | bge-large-zh-v1.5 输出固定1024维，无需降维 |
| 查询优化 | 使用`EXPLAIN (ANALYZE, VERBOSE, BUFFERS)`验证每次新增检索逻辑 |
| 归一化向量 | bge-large-zh-v1.5 输出的向量已归一化，建议使用内积操作符
ORDER BY embedding <#> '[...]'::vector |

### 3.6 一期行业知识库

| 行业 | 状态 | 选题库 | 用户画像 | 合规规则 |
| --- | --- | --- | --- | --- |
| 保健品 | 一期 | 50+选题方向 | 6类人群画像 | 保健品特殊合规 |
| AI行业 | 一期 | 50+选题方向 | 5类人群画像 | 科技内容合规 |

### 3.7 素材检索 Agent 的三层检索权限控制

**【新增】3.7.1 三层检索逻辑**

素材检索 Agent 在执行检索时，按以下顺序依次检索：

| 层级 | 检索优先级 | 读写权限 | 检索范围 | 数据归属 |
| ---- | ---------- | -------- | -------- | -------- |
| **第一层：企业私有库** | 最高（精准匹配） | 读写 | 本企业全部数据 | `data_level='tenant'`, `enterprise_id=当前企业` |
| **第二层：行业知识库** | 中（系统补充） | 只读 | 全量行业知识 | `data_level='platform'`, `platform_category='industry'` |
| **第三层：公共知识库** | 低（兜底） | 只读 | 全量公共知识 | `data_level='platform'`, `platform_category='public'` |

**【新增】3.7.2 检索流程（对租户透明）**

```
用户输入创作需求
        ↓
[素材检索Agent]
        ↓
┌─────────────────────────────────────────────────────────┐
│ Step 1：检索企业私有库（精准）                            │
│   SQL: WHERE data_level='tenant' AND enterprise_id='xxx' │
│   结果：本企业品牌/产品/卖点 → 直接采用                    │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│ Step 2：补充行业知识库（系统自动）                        │
│   SQL: WHERE data_level='platform' AND platform_category='industry' │
│   结果：行业选题/人群画像/痛点 → 补充到素材包              │
└─────────────────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────┐
│ Step 3：兜底公共知识库（系统自动）                        │
│   SQL: WHERE data_level='platform' AND platform_category='public' │
│   结果：平台规则/合规要求/通用方法论 → 补充到素材包        │
└─────────────────────────────────────────────────────────┘
        ↓
[组装素材包] → 仅输出给租户，不暴露数据来源层级
```

**【新增】3.7.3 租户感知模型**

**租户在创作界面看到的只有**：
- 素材包内容（品牌/产品/卖点/人群/场景）
- **看不到**三层数据分别检索了什么
- **看不到**行业知识库、公共知识库的内容

**素材包输出结构**（对租户透明）：

```json
{
  "brand": {...},
  "product": {...},
  "persona": {...},
  "scene": {...},
  "compliance": {...}
}
```

**【新增】3.7.4 Agent 系统用户的会话上下文**

```sql
-- Agent 执行检索前设置会话上下文
SET app.enterprise_id = 'ent_xxx';      -- 当前企业ID（用于写入租户级数据）
SET app.is_platform_admin = 'false';
SET app.is_agent = 'true';              -- 标记为Agent系统用户
```

RLS 策略根据 `is_agent=true` 允许读取平台级数据，但写入时只允许写入 `data_level='tenant'` 的数据。

### 3.8 平台方知识库管理

**【新增】3.8.1 功能定位**

平台方知识库管理后台是**平台管理员**维护公共知识库、行业知识库、内置模板的专用入口。租户无法访问此后台。

**【新增】3.8.2 可管理的数据范围**

| 类别 | platform_category | 可管理内容 |
| ---- | ---------------- | ---------- |
| 公共知识库 | `public` | 平台规则、创作方法论、合规通用规则 |
| 行业知识库 | `industry` | 选题库、用户画像、痛点库、爆款拆解 |
| 内置模板 | `template` | 品牌模板、产品模板、人群模板、场景模板 |

**【新增】3.8.3 平台后台功能列表**

| 功能 | 说明 |
| ---- | ---- |
| **行业知识管理** | 新增/编辑/删除行业知识，支持批量导入 Markdown |
| **公共知识管理** | 新增/编辑/删除公共知识（平台规则/合规规则） |
| **模板管理** | 创建/编辑/版本控制内置模板 |
| **行业分类配置** | 新增行业、维护行业编码和描述 |
| **数据统计** | 各行业知识库条目数量、检索热度统计 |
| **批量操作** | Markdown 文件批量上传、批量向量化 |

**【新增】3.8.4 平台后台与租户后台的隔离**

| 对比维度 | 平台方管理后台 | 租户知识管理界面 |
| -------- | -------------- | ---------------- |
| 访问入口 | `/admin/kb` | `/kb` |
| 可视数据 | 公共/行业/模板 | 仅本企业私有库 |
| 写入目标 | `data_level='platform'` | `data_level='tenant'` |
| 认证方式 | 平台管理员账号 | 企业租户账号 |
| RLS策略 | `is_platform_admin=true` | `enterprise_id=当前企业` |

**【新增】3.8.5 平台后台界面结构**

```
平台方知识库管理
├── 公共知识库
│   ├── 平台规则
│   ├── 创作方法论
│   └── 合规通用规则
├── 行业知识库
│   ├── 保健品
│   │   ├── 选题库
│   │   ├── 用户画像
│   │   ├── 痛点库
│   │   └── 爆款拆解
│   └── AI行业
│       └── ...
├── 内置模板
│   ├── 品牌模板
│   ├── 产品模板
│   ├── 人群模板
│   └── 场景模板
└── 数据统计
    ├── 知识条目统计
    └── 检索热度分析
```

**【新增】3.8.6 租户前端知识管理页面设计**

#### 3.8.6.1 页面访问约束

| 约束项 | 说明 |
| ------ | ---- |
| 访问路径 | `/knowledge` |
| 可视数据 | 仅 `data_level='tenant'` 且 `enterprise_id=当前企业` 的数据 |
| 不可见数据 | 公共知识库、行业知识库、内置模板（对租户完全透明） |
| 可执行操作 | 新增/编辑/删除本企业知识 |

#### 3.8.6.2 页面结构

```
知识管理 (/knowledge)
├── 概览
│   ├── 知识条目统计（本企业）
│   ├── 分类分布
│   └── 最近更新
├── 知识列表
│   ├── 筛选：分类/标签/来源
│   ├── 搜索：（仅语义搜索本企业库）
│   └── 批量操作
├── 上传知识
│   ├── 文档上传（PDF/Word/Markdown）
│   ├── 表单录入
│   └── 批量导入
└── 设置
    ├── 导入/导出
    └── 同步配置
```

#### 3.8.6.3 功能约束

| 功能 | 约束 |
| ---- | ---- |
| 知识列表 | 仅展示 `data_level='tenant'` AND `enterprise_id=当前企业` 的数据 |
| 语义搜索 | 仅搜索本企业私有库（系统底层自动补充平台库，页面无感知） |
| 上传文档 | 强制设置 `data_level='tenant'`，`enterprise_id=当前企业` |
| 编辑/删除 | 仅限本企业知识条目 |
| 不展示平台库 | 页面不渲染任何公共/行业/模板内容 |

#### 3.8.6.4 前端路由守卫

```javascript
// 租户页面路由守卫
const tenantKnowledgeRoutes = ['/knowledge', '/knowledge/list', '/knowledge/upload'];

router.beforeEach((to, from, next) => {
  const user = auth.getUser();

  // 租户用户不得访问平台管理后台
  if (to.path.startsWith('/admin/')) {
    if (user.role !== 'platform_admin') {
      return next('/403');  // 拒绝访问
    }
  }

  // 平台管理员不得访问租户知识管理（需单独授权）
  if (tenantKnowledgeRoutes.includes(to.path) && user.role === 'platform_admin') {
    return next('/admin');  // 重定向到平台后台
  }

  next();
});
```

### 3.9 审计与日志

**【新增】3.9.1 知识库操作审计字段**

| 字段 | 说明 |
| ---- | ---- |
| `created_by` | 创建者 ID |
| `updated_by` | 更新者 ID |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

**【新增】3.9.2 审计日志记录**

| 操作类型 | 记录内容 | 保留期限 |
| -------- | -------- | -------- |
| 知识入库 | enterprise_id, data_level, category, created_by | 1年 |
| 知识检索 | enterprise_id, query, results_count, source_levels | 6个月 |
| 知识删除 | enterprise_id, deleted_id, deleted_by | 1年 |
| 平台数据变更 | admin_id, table_name, record_id, action | 永久 |

**【新增】3.9.3 异常行为检测**

| 异常场景 | 检测逻辑 | 处理方式 |
| -------- | -------- | -------- |
| 租户尝试写入平台数据 | RLS 策略拒绝 + 日志记录 | 触发安全告警 |
| 租户尝试读取平台数据 | 前端不渲染 + API 校验 | 记录访问尝试 |
| 大批量检索平台数据 | Agent 只读频率监控 | 限制单次检索条数 |
| 异常删除企业数据 | 删除前备份 + 需二次确认 | 操作延迟生效 |

***

## 四、工作流设计

### 4.1 小红书创作工作流



```
用户输入
    ↓
[统一调度Agent] → 意图识别 → 路由到小红书工作流
    ↓
[素材检索Agent] → 从知识库检索素材 → 输出素材包
    ↓
[ResultValidator] → 校验素材包完整性
    ↓
  ┌─ 校验通过 → 继续
  └─ 校验不通过 → 提示用户补充信息 / 使用可用素材继续（标注缺失项）
    ↓
[选题Agent]（可选，用户已选题则跳过）→ 推荐选题
    ↓
[标题Agent] → 生成5个标题
    ↓
[ResultValidator] → 校验标题输出
    ↓
  ┌─ 校验通过 → 用户选择/系统推荐
  └─ 校验不通过 → 重新生成（最多2次）→ 仍不通过则标注"建议人工优化"
    ↓
[正文Agent] → 创作正文 → 输出文章 + AI味评分
    ↓
[质量合并评估] → AI味评分 + 合规校验一次性完成
    ↓
  ┌─ 全部通过 → 进入下一步
  │
  ├─ AI味不通过（<70分）→ 重新生成（最多2次）
  │     ↓ 仍不通过 → 降级：接受当前版本 + 标注"建议人工润色"
  │
  ├─ 合规不通过（P0问题）→ 指定修改（最多2次）
  │     ↓ 仍不通过 → 降级：输出当前版本 + 合规问题清单 + 标记"需人工修改"
  │
  └─ P1/P2问题 → 标注提示，不阻断流程
    ↓
[标签Agent] ─────┐
                  ├── 并行执行
[合规Agent]（最终校验）─────┘
    ↓
[运营Agent]（二期）→ 生成发布建议 + 评论区话术
    ↓
[主Agent汇总] → 输出完整笔记包
```

**关键设计改进：**

*   合并AI味评分和合规校验为一次评估，避免嵌套重试循环
*   每个环节都有明确的降级出口，永远不进入无限循环
*   最大总重试次数硬限制为4次（AI味2次 + 合规2次）

### 4.2 跨平台一键分发工作流（二期）



```
用户输入："帮我把这个内容发到所有平台"
    ↓
[统一调度Agent] → 识别多平台分发意图
    ↓
[素材检索Agent] → 只检索一次 → 输出素材包
    ↓
并行启动：
  ├── 小红书工作流 → 输出图文笔记
  ├── 公众号工作流 → 输出长文
  └── 抖音工作流 → 输出短视频脚本
    ↓
[统一调度Agent] → 汇总所有平台输出 → 交付
```

***

## 五、选题系统

### 5.1 五条选题来源线

| 来源 | 实现方式 | 优先级 | 上线阶段 |
| --- | --- | --- | --- |
| 行业预设选题库 | Obsidian Vault 中的选题库文件 | P0 | Phase 3 |
| 实时热点与节点日历 | 预设全年节点 + 热点API | P0 | Phase 3 |
| 竞品爆款追踪 | 竞品笔记监测 + 自动拆解 | P1 | Phase 4 |
| 历史数据反哺 | 企业笔记数据分析 | P1 | Phase 4 |
| AI组合生成 | 产品×人群×场景×热点 | P2 | Phase 4 |

***

## 六、防同质化策略

| 策略 | 说明 |
| --- | --- |
| 跨企业去重 | 同行业不同企业使用相同选题时，自动调整角度 |
| 企业自身去重 | 追踪历史笔记，避免重复 |
| 风格指纹 | 基于历史笔记生成企业独特的内容风格 |
| 选题空白区推荐 | 主动推荐竞品未覆盖的选题 |

***

## 七、去AI味策略

| 维度 | 具体措施 |
| --- | --- |
| 语言 | 口语化语气词、避免工整排比、句式长短不一 |
| 内容 | 加入生活细节、允许轻微不完美表达 |
| 结构 | 不同笔记使用不同段落结构 |
| 检测 | 基于规则的多维度AI味评分，<70分自动重新生成 |
| 评分机制 | 句式多样性(0-20) + 口语化程度(0-20) + 结构模式(0-20) + 生活细节(0-20) + 轻微不完美(0-20) |

***

## 八、合规与风控

### 8.1 多层合规防护

| 阶段 | 校验内容 |
| --- | --- |
| 资料入库时 | 企业上传资料的合规性扫描 |
| 创作过程中 | 合规Agent实时校验 |
| 输出交付时 | 合规报告 + 需人工确认标注 |
| 持续运营中 | 合规词库定期更新 |

### 8.2 Harness 设计汇总

| 控制项 | 实现位置 | 说明 |
| --- | --- | --- |
| 权限校验 | 统一调度Agent | 用户权限+套餐+额度 |
| 限流 | 统一调度Agent | Redis计数器 |
| 安全护栏 | 统一调度Agent | Prompt注入检测 |
| 质量门禁 | 各Agent输出后 | AI味评分、格式校验 |
| 中间结果校验 | ResultValidator | Agent间传递数据的质量校验 |
| 重试策略 | Flow条件路由 | 每个环节最多重试2次，总重试硬限制4次 |
| 降级方案 | 每个Agent | 重试失败后输出当前版本 + 标注人工建议 |
| 错误处理 | 每个节点 | 超时、异常、降级 |
| 审计日志 | 全链路 | 每次Agent调用记录 |
| 数据隔离 | pgvector查询 | RLS行级安全策略 + WHERE enterprise\_id |
| 输出校验 | 最终输出 | Pydantic Schema校验 |

**【新增】知识库相关控制项**

| 控制项 | 实现位置 | 说明 |
| --- | --- | --- |
| 三层检索权限控制 | 素材检索Agent | 企业私有库→行业知识库→公共知识库，按优先级检索 |
| 入库目标锁定 | 知识库管理Agent | 企业上传强制写入 `data_level='tenant'` |
| 租户身份传递 | 统一调度Agent | `enterprise_id` 传递给下游Agent，用于数据过滤 |
| 平台数据只读 | 合规Agent | 平台规则库和行业规则库对租户只读 |
| 跨级检索透明 | 素材检索Agent | 三层检索结果合并后输出，不暴露数据来源层级 |
| Agent会话上下文 | 所有Agent/Tool | `SET app.is_agent=true` 允许读取平台级数据 |

### 8.3 安全与合规深层保障

| 保障措施 | 说明 |
| --- | --- |
| 行级安全策略（RLS） | PostgreSQL原生支持，在数据库层面强制多租户数据隔离 |
| API层双重鉴权 | 每次请求验证token中的enterprise\_id，与查询条件双重校验 |
| 连接池隔离 | 不同企业使用不同的数据库连接池配置（企业版） |
| 法律责任框架 | 企业用户对发布内容承担最终责任，平台提供合规工具但不替代法律合规义务 |

**【新增】RLS 具体策略**

#### 8.3.1 核心策略原则

| 角色 | 可读 | 可写 | 可删 |
|------|------|------|------|
| 平台管理员 (is_platform_admin = true) | 全部数据 | 仅平台级 | 仅平台级 |
| 租户用户 (enterprise_id = 'xxx') | 仅自己租户级 + 平台级(只读) | 仅自己租户级 | 仅自己租户级 |
| Agent系统用户 (is_agent = true) | 全部数据(检索用) | 仅租户级(写入检索结果) | 无 |

#### 8.3.2 完整 RLS 策略

```sql
-- ============================================
-- 启用 RLS
-- ============================================
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE industry_knowledge ENABLE ROW LEVEL SECURITY;
ALTER TABLE templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE enterprises ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 辅助函数：获取当前会话上下文
-- ============================================
CREATE OR REPLACE FUNCTION current_user_context()
RETURNS JSONB AS $$
BEGIN
    RETURN JSONB_BUILD_OBJECT(
        'enterprise_id', current_setting('app.enterprise_id', true),
        'is_platform_admin', current_setting('app.is_platform_admin', true)::boolean,
        'is_agent', current_setting('app.is_agent', true)::boolean,
        'user_role', current_setting('app.user_role', true)
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 知识库表 RLS 策略
-- ============================================

-- 策略1：平台管理员可读写平台级数据
CREATE POLICY kb_platform_admin_all ON knowledge_base
    FOR ALL
    USING (
        data_level = 'platform'
        AND current_setting('app.is_platform_admin', true)::boolean = true
    );

-- 策略2：租户可读写自己的租户级数据
CREATE POLICY kb_tenant_crud ON knowledge_base
    FOR ALL
    USING (
        data_level = 'tenant'
        AND enterprise_id = current_setting('app.enterprise_id', true)
    );

-- 策略3：租户可读取平台级数据（用于Agent检索，对租户透明）
CREATE POLICY kb_tenant_read_platform ON knowledge_base
    FOR SELECT
    USING (
        data_level = 'platform'
        AND current_setting('app.enterprise_id', true) IS NOT NULL
        AND current_setting('app.is_platform_admin', true)::boolean = false
    );

-- 策略4：Agent可写入租户级数据（系统自动检索结果入库）
CREATE POLICY kb_agent_insert ON knowledge_base
    FOR INSERT
    WITH CHECK (
        data_level = 'tenant'
        AND enterprise_id = current_setting('app.enterprise_id', true)
        AND current_setting('app.is_agent', true)::boolean = true
    );

-- 策略5：Agent可读取平台级数据（用于跨级检索）
CREATE POLICY kb_agent_read_platform ON knowledge_base
    FOR SELECT
    USING (
        data_level = 'platform'
        AND current_setting('app.is_agent', true)::boolean = true
    );

-- ============================================
-- 行业知识库表 RLS 策略（仅平台级）
-- ============================================

CREATE POLICY ik_platform_admin_all ON industry_knowledge
    FOR ALL
    USING (
        current_setting('app.is_platform_admin', true)::boolean = true
    );

CREATE POLICY ik_tenant_read ON industry_knowledge
    FOR SELECT
    USING (
        current_setting('app.is_platform_admin', true)::boolean = false
        AND current_setting('app.enterprise_id', true) IS NOT NULL
    );

-- ============================================
-- 模板表 RLS 策略
-- ============================================

CREATE POLICY tmpl_platform_admin_all ON templates
    FOR ALL
    USING (
        current_setting('app.is_platform_admin', true)::boolean = true
    );

CREATE POLICY tmpl_tenant_read ON templates
    FOR SELECT
    USING (
        is_active = true
        AND current_setting('app.is_platform_admin', true)::boolean = false
        AND current_setting('app.enterprise_id', true) IS NOT NULL
    );

-- ============================================
-- 企业表 RLS 策略
-- ============================================

CREATE POLICY ent_self_read ON enterprises
    FOR SELECT
    USING (
        enterprise_id = current_setting('app.enterprise_id', true)
        OR current_setting('app.is_platform_admin', true)::boolean = true
    );

CREATE POLICY ent_platform_admin_all ON enterprises
    FOR ALL
    USING (
        current_setting('app.is_platform_admin', true)::boolean = true
    );
```

#### 8.3.3 会话上下文设置

```sql
-- ============================================
-- 应用层调用前设置会话上下文
-- ============================================

-- 租户用户请求时：
SET app.enterprise_id = 'ent_xxx';
SET app.is_platform_admin = 'false';
SET app.is_agent = 'false';
SET app.user_role = 'tenant';

-- 平台管理员请求时：
SET app.enterprise_id = NULL;
SET app.is_platform_admin = 'true';
SET app.is_agent = 'false';
SET app.user_role = 'platform_admin';

-- Agent系统内部调用时（跨级检索）：
SET app.enterprise_id = 'ent_xxx';  -- 仍需设置，因为租户级数据写入需要
SET app.is_platform_admin = 'false';
SET app.is_agent = 'true';
SET app.user_role = 'agent';
```

#### 8.3.4 技术实现要点

```python
# 租户请求
SET app.enterprise_id = current_user.enterprise_id
SET app.is_platform_admin = false
SET app.is_agent = false

# Agent系统请求
SET app.enterprise_id = target_enterprise.enterprise_id  # 写入目标租户
SET app.is_platform_admin = false
SET app.is_agent = true
```

***

## 九、商业模式

### 9.1 版本与定价

| 版本 | 目标用户 | 定价策略 | 额度 |
| --- | --- | --- | --- |
| 免费版 | 个人/试用用户 | 免费 | 5篇/月，仅小红书 |
| 基础版 | 中小企业 | 月订阅 | 30篇/月 |
| 专业版 | 中型企业 | 月订阅 | 100篇/月+多账号+竞品监测 |
| 企业版 | 大型企业 | 年订阅 | 不限量+团队协作+审批流程 |

### 9.2 成本测算

| 成本项 | 估算方式 | 预估范围 |
| --- | --- | --- |
| MiniMax API调用 | 每篇笔记约8-10次LLM调用（标题5次+正文2次+标签1次+合规1次+调度1次） | 按Token计费 |
| Embedding（bge-large-zh-v1.5） | 本地运行，无API调用 | 免费（仅消耗本地CPU/GPU资源） |
| 服务器 | 腾讯云轻量4核4G | 固定月费 |
| COS存储 | 50G资源包 | 固定月费 |
| 备用LLM | DeepSeek/Qwen降级调用 | 按Token计费（仅降级时产生） |

### 9.3 价值证明路径

| 措施 | 说明 |
| --- | --- |
| 免费试用 | 5篇/月免费额度，降低体验门槛 |
| 合规报告 | 每篇笔记附带合规校验报告，展示专业价值 |
| 数据看板 | 展示创作效率提升和内容质量趋势 |
| 案例库 | 积累种子用户的成功案例用于营销 |

***

## 十、项目里程碑

### Phase 0：技术预研（第1-2周）



```
交付项：
  ├── MiniMax-M2.7 生成质量评估（对比DeepSeek/Qwen）
  ├── bge-large-zh-v1.5 本地部署验证 + 1024维向量与pgvector索引兼容性测试
  ├── pgvector在4G内存机器上的性能基准测试
  │   ├── IVFFlat索引构建时间与查询延迟
  │   ├── HNSW索引构建时间与内存占用
  │   └── halfvec精度损失评估
  ├── CrewAI框架原型验证（单Agent跑通）
  ├── Obsidian同步流程端到端验证
  ├── 备用LLM（DeepSeek/Qwen）接口验证
  └── 技术可行性报告

验证标准：
  ✓ MiniMax生成质量满足小红书内容创作需求
  ✓ pgvector在4G内存下可正常工作，检索延迟<2s
  ✓ bge-large-zh-v1.5 本地推理延迟可接受（单条<1s，批量10条<3s）
  ✓ bge-large-zh-v1.5 模型加载后内存占用在可控范围内（约1.5GB）
  ✓ CrewAI单Agent原型跑通输入→输出链路
  ✓ Obsidian文件变更能在30秒内同步到pgvector
  ✓ 备用LLM接口可用，Prompt兼容性良好
```

### Phase 1：基础设施 + 单Agent验证（第3-4周）



```
交付项：
  ├── Docker Compose 环境搭建
  ├── PostgreSQL + pgvector 初始化（含RLS配置）
  ├── Redis 启动
  ├── Prometheus + Grafana 基础监控
  ├── MiniMax-M2.7 API 对接验证 + LLM降级模块
  ├── 单个标题Agent跑通
  ├── 单个正文Agent跑通
  ├── Obsidian Vault 模板创建
  ├── Markdown 文件读取工具
  ├── pgvector 写入和检索工具（含索引策略，维度1024）
  ├── 本地Embedding服务封装（LocalEmbedding类）
  ├── COS 读写验证
  └── ResultValidator 中间结果校验模块

验证标准：
  ✓ 输入选题 → 标题Agent输出5个标题
  ✓ 输入标题+素材 → 正文Agent输出一篇笔记
  ✓ Obsidian 文件能被正确读取
  ✓ 向量检索能返回相关结果，延迟<2s
  ✓ LLM降级切换正常工作
  ✓ 中间结果校验正确拦截低质量数据
```

### Phase 2：核心创作流程（第5-7周）



```
交付项：
  ├── 素材检索Agent + Tool
  ├── 标题Agent + Tool
  ├── 正文Agent + Tool
  ├── 标签Agent
  ├── 合规Agent + Tool
  ├── 小红书创作Flow（完整串联）
  ├── 质量门禁（AI味评分+重试+降级）
  ├── 合规校验循环（不通过→修改→重新校验，最多2次）
  ├── ResultValidator 全链路集成
  ├── 前置Prompt文件（每个Agent独立.md文件）
  ├── 数据备份策略（pg_dump每日+WAL增量）
  └── 监控告警规则配置

验证标准：
  ✓ 输入一句话需求 → 输出完整笔记包
  ✓ 合规不通过时自动修改并重新校验
  ✓ AI味评分低于70时自动重新生成
  ✓ 重试失败时正确降级，不进入死循环
  ✓ 中间结果校验正确工作
  ✓ 监控告警正常触发
```

### Phase 3：知识库 + 前端 + 选题（第8-10周）



```
交付项：
  ├── 选题Agent
  ├── 知识库管理Agent
  ├── Obsidian 同步服务（含冲突处理 + 本地Embedding向量化）
  ├── Web端知识管理界面（上传/录入/浏览）
  ├── 行业知识库灌入（保健品 + AI行业）
  ├── Streamlit 前端
  ├── 统一调度Agent
  ├── 完整流程端到端跑通
  ├── 种子用户测试（3-5人）
  └── 用户反馈收集机制

验证标准：
  ✓ 企业通过Obsidian或Web端上传知识 → 自动入库
  ✓ 用户输入需求 → 全流程自动完成
  ✓ Streamlit 界面可用
  ✓ 种子用户能独立完成一次完整创作
  ✓ 用户反馈收集正常工作
```

### Phase 4：数据 + 优化（第11-13周）



```
交付项：
  ├── 数据分析Agent
  ├── 运营Agent
  ├── 笔记数据导入
  ├── 数据看板
  ├── Prompt 优化迭代（基于种子用户反馈）
  ├── 去AI味优化（AI味评分均值≥80）
  ├── 防同质化机制
  ├── 竞品分析报告
  └── 正式上线准备

验证标准：
  ✓ 数据看板能展示核心指标
  ✓ AI味评分均值≥80
  ✓ 一次生成满意率≥60%
  ✓ 合规率≥99%
```

### Phase 5：多平台扩展（第14-18周）



```
交付项：
  ├── 公众号创作工作流
  ├── 抖音创作工作流
  ├── 跨平台一键分发
  ├── Next.js 产品前端
  ├── 更多行业知识库
  ├── 更多行业知识库
  └── 商业化推广启动
```

***

## 十一、开发指南：通过 Claude Code 开发

### 11.1 项目初始化

bash

bash

```
# 1. 创建项目
mkdir content-agent && cd content-agent
git init

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install crewai crewai-tools psycopg2-binary redis python-frontmatter qcloud-cos streamlit pydantic prometheus-client sentence-transformers


# 4. 生成 requirements.txt
pip freeze > requirements.txt

# 5. 启动基础设施
docker-compose up -d
```

### 11.2 Claude Code 开发顺序



```
严格按以下顺序，每个步骤让 Claude Code 完成一个文件或模块：

Step 1：项目结构
  → 让 Claude 生成完整目录结构和空文件

Step 2：数据模型（models/）
  → MaterialPack、NoteOutput、ComplianceReport、ValidationResult 等 Pydantic 模型

Step 3：配置文件（config/）
  → LLM配置（含降级配置）、Agent配置、平台配置、pgvector索引配置

Step 4：Prompt 文件（prompts/）
  → 每个Agent的System Prompt独立.md文件

Step 5：工具开发（tools/）
  → obsidian_tools.py（Markdown读取、搜索、链接追踪）
  → vector_tools.py（pgvector写入、检索，含索引策略，维度1024）
  → embedding_tools.py（本地bge-large-zh-v1.5封装，含批量向量化）
  → compliance_tools.py（敏感词检测）
  → cos_tools.py（COS读写）
  → llm_tools.py（LLM调用+降级逻辑）

Step 6：校验层（validators/）
  → result_validator.py（Agent间中间结果质量校验）
  → ai_flavor_scorer.py（AI味多维度评分器）

Step 7：Agent定义（agents/）
  → 每个Agent一个文件，引用Prompt和Tools

Step 8：Task定义（tasks/）
  → 每类Task一个文件

Step 9：Crew定义（crews/）
  → 小红书Crew、共享Crew

Step 10：Flow工作流（flows/）
  → 主Flow、小红书创作Flow（含重试+降级逻辑）

Step 11：统一调度（orchestrator/）
  → 调度Agent + 路由逻辑

Step 12：前端（app.py）
  → Streamlit 界面（含知识管理界面）

Step 13：同步服务（sync/）
  → Obsidian 文件监听 + 向量化 + 冲突处理

Step 14：监控（monitoring/）
  → Prometheus指标采集 + Grafana看板 + 告警规则

Step 15：API接口（api/）
  → FastAPI 接口（供前端调用）

Step 16：Docker配置
  → Dockerfile + docker-compose.prod.yml

Step 17：测试（tests/）
  → 每个模块的单元测试
```

### 11.3 与 Claude Code 协作的最佳实践



```
每个会话的结构：

  1. 上下文加载
     "请先阅读 .claude/CLAUDE.md 了解项目全貌，
      以及 .claude/plans/phase-1-plan.md 了解当前阶段任务"

  2. 明确任务
     "今天开发 compliance_agent.py，具体要求：
      - [具体要求列表]"

  3. 先规划后编码
     "先列出你要创建/修改的文件和每个文件的核心逻辑，
      我确认后再开始写代码"

  4. 逐文件实现
     每个文件写完后跑测试，通过后再继续下一个

  5. 更新进度
     "更新 CLAUDE.md 中的进度 checklist"
```

### 11.4 推荐的 Claude Code 技能配置



```
核心技能：
  1. planning-with-files    → 每次开发前先出文件化计划
  2. claude-mem             → 跨会话记住项目进度和决策
  3. iterative-development  → 小步快跑，每步验证

开发规范：
  4. 项目 CLAUDE.md         → 项目级持久上下文
  5. Agent开发规范           → .claude/skills/agent-development.md
  6. Prompt编写规范          → .claude/skills/prompt-engineering.md

质量保障：
  7. tdd                    → 测试驱动，每个Agent必须有测试
  8. code-review            → 每个Phase结束做一次代码审查
```

***

## 十二、监控与运维

### 12.1 监控告警体系

| 监控维度 | 工具 | 告警阈值 |
| --- | --- | --- |
| 系统资源 | Prometheus + Grafana | CPU>80%、内存>90%、磁盘>85% |
| API延迟 | 自定义指标 | P95延迟>5s |
| Agent成功率 | 自定义指标 | 成功率<90% |
| pgvector查询性能 | pg\_stat\_statements | 查询P95>2s |
| LLM调用 | 自定义指标 | 失败率>10%、延迟P95>15s |
| Redis连接 | Prometheus exporter | 连接数>80%上限 |

### 12.2 数据备份策略

| 备份类型 | 频率 | 保留期 | 方式 |
| --- | --- | --- | --- |
| PostgreSQL全量备份 | 每日 | 7天 | pg\_dump |
| WAL增量备份 | 持续 | 3天 | 归档到COS |
| Obsidian Vault | 每次Git push | 永久 | Git历史 |
| COS对象存储 | 腾讯云自动备份 | 按配置 | 腾讯云COS版本控制 |

### 12.3 性能基准与调优

sql

sql

```
-- 每次新增检索逻辑后必须执行性能验证
EXPLAIN (ANALYZE, VERBOSE, BUFFERS)
SELECT * FROM knowledge_base
WHERE enterprise_id = 'xxx'
ORDER BY embedding <-> '[...]'::vector
LIMIT 10;

-- 如果向量已归一化，使用内积操作符获得最佳性能
ORDER BY embedding <#> '[...]'::vector

-- 并行查询优化（4G内存机器建议设为1-2）
SET max_parallel_workers_per_gather = 2;
```

***

## 十三、成功指标

| 指标 | MVP目标 | 半年目标 |
| --- | --- | --- |
| 生成内容合规率 | ≥99% | ≥99.5% |
| 一次生成满意率 | ≥60% | ≥80% |
| AI味评分均值 | ≥70 | ≥80 |
| 免费版注册用户 | 50 | 500 |
| 付费企业注册数 | 10 | 100 |
| 月活跃企业 | 5 | 50 |
| 端到端创作耗时 | <3分钟 | <2分钟 |

***

## 十四、风险与应对

| 风险 | 影响 | 概率 | 应对 |
| --- | --- | --- | --- |
| 4GB内存不够 | 高 | 高 | 优化配置+4GB Swap+HNSW索引内存优化+halfvec+正式上线后升级服务器 |
| MiniMax API限流/不稳定 | 高 | 中 | LLM降级方案（L1-L4四级）+重试机制+备用LLM自动切换 |
| 本地Embedding模型内存占用 | 中 | 低 | 模型约1.5GB内存，4G服务器需确保Swap充足；可选用更轻量的bge-small-zh-v1.5作为降级方案 |
| pgvector检索性能不足 | 高 | 中 | Phase 0性能基准测试+索引策略优化+查询优化+必要时升级服务器 |
| Obsidian企业不会用 | 中 | 高 | Web端管理界面双轨制+预设模板+视频教程+10分钟上手指南 |
| AI生成内容被平台限流 | 高 | 中 | 持续优化去AI味策略+AI味评分机制+人机协作模式 |
| 内容同质化 | 中 | 中 | 防同质化引擎+风格指纹+选题空白区推荐 |
| Agent循环重试死循环 | 高 | 低 | 合并评估环节+每个环节最多重试2次+总重试硬限制4次+明确降级出口 |
| Agent间错误传播 | 中 | 中 | ResultValidator中间结果校验+缺失项标注+fallback逻辑 |
| 多租户数据泄露 | 高 | 低 | RLS行级安全策略+API双重鉴权+连接池隔离 |
| 竞品快速迭代 | 中 | 高 | 持续竞品监测+差异化定位+快速迭代能力 |
| 人力不足导致延期 | 高 | 中 | 延长工期至18周+MVP阶段精简到6个Agent+Phase 0技术预研降低后期返工 |

***

## 十五、产品研究计划

### 15.1 用户调研

| 调研阶段 | 方法 | 目标 | 样本量 | 时间 |
| --- | --- | --- | --- | --- |
| 需求验证 | 深度访谈 | 了解目标用户的创作痛点和现有工作流 | 15-20人 | Phase 0 |
| 原型测试 | 可用性测试 | 验证核心流程的易用性 | 8-10人 | Phase 3 |
| MVP验证 | 问卷+数据分析 | 验证生成内容的质量和用户满意度 | 30-50人 | Phase 4 |

### 15.2 竞品分析

| 维度 | 分析内容 |
| --- | --- |
| 功能覆盖 | 支持哪些平台、哪些创作环节 |
| 定价模型 | 免费版限制、付费版价格、企业版方案 |
| 技术架构 | 是否使用多Agent、知识库方案、LLM选择 |
| 用户口碑 | 各渠道评价、核心优缺点 |
| 差异化定位 | 各竞品的核心卖点是什么 |

***

## 附录A：项目目录结构



```
chuangzuo（本项目根目录）/
├── .claude/
│   ├── CLAUDE.md
│   ├── plans/
│   └── skills/
├── agents/
│   ├── orchestrator_agent.py
│   ├── material_agent.py
│   ├── title_agent.py
│   ├── article_agent.py
│   ├── tag_agent.py
│   └── compliance_agent.py
├── tasks/
│   ├── title_task.py
│   ├── article_task.py
│   └── compliance_task.py
├── crews/
│   ├── xiaohongshu_crew.py
│   └── shared_crew.py
├── flows/
│   ├── main_flow.py
│   └── xiaohongshu_flow.py
├── tools/
│   ├── obsidian_tools.py
│   ├── vector_tools.py
│   ├── embedding_tools.py
│   ├── compliance_tools.py
│   ├── cos_tools.py
│   └── llm_tools.py
├── validators/
│   ├── result_validator.py
│   └── ai_flavor_scorer.py
├── models/
│   ├── local_embedding.py
│   ├── material_pack.py
│   ├── note_output.py
│   └── compliance_report.py
├── config/
│   ├── llm_config.py
│   ├── agent_config.py
│   ├── platform_config.py
│   └── vector_config.py
├── prompts/
│   ├── orchestrator.md
│   ├── material_search.md
│   ├── title_agent.md
│   ├── article_agent.md
│   ├── tag_agent.md
│   ├── compliance_agent.md
│   └── examples/
├── sync/
│   ├── file_watcher.py
│   └── vectorizer.py
├── monitoring/
│   ├── metrics.py
│   └── alerts.py
├── api/
│   └── main.py
├── app.py
├── docker-compose.yml
├── docker-compose.prod.yml
├── Dockerfile
├── requirements.txt
└── tests/
    ├── test_agents/
    ├── test_tools/
    ├── test_flows/
    └── test_validators/
```

***

## 附录B：多租户数据模型设计

**【新增】B.1 数据分级定义**

| 级别 | data_level 值 | 说明 | 可读 | 可写 | 可删 |
|------|---------------|------|------|------|------|
| 平台级 | `platform` | 公共知识库、行业知识库、内置模板 | 平台方 + 租户(Agent检索时) | 仅平台方 | 仅平台方 |
| 租户级 | `tenant` | 企业私有库 | 仅本租户 | 仅本租户 | 仅本租户 |

**【新增】B.2 统一知识库表结构**

```sql
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    data_level VARCHAR(20) NOT NULL DEFAULT 'tenant',

    platform_category VARCHAR(50) DEFAULT NULL,
    -- 当 data_level='platform' 时: 'public'/'industry'/'template'
    -- 当 data_level='tenant' 时，此字段为 NULL

    enterprise_id VARCHAR(255) DEFAULT NULL,
    -- 当 data_level='tenant' 时必填
    -- 当 data_level='platform' 时为 NULL

    category VARCHAR(100) DEFAULT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(255) DEFAULT NULL,
    source_url VARCHAR(1000) DEFAULT NULL,

    embedding VECTOR(1024),

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
```

**【新增】B.3 数据库用户权限设计**

```sql
-- 租户用户：只能通过RLS策略访问（不能直接BYPASS）
CREATE USER app_tenant WITH PASSWORD 'xxx';
GRANT CONNECT ON DATABASE content_agent TO app_tenant;
GRANT USAGE ON SCHEMA public TO app_tenant;
GRANT SELECT, INSERT, UPDATE, DELETE ON knowledge_base TO app_tenant;
GRANT USAGE, SELECT ON SEQUENCE knowledge_base_id_seq TO app_tenant;

-- 平台管理员用户：绕过RLS（用于管理后台）
CREATE USER app_platform WITH PASSWORD 'xxx';
GRANT CONNECT ON DATABASE content_agent TO app_platform;
GRANT USAGE ON SCHEMA public TO app_platform;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_platform;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_platform;

-- Agent系统用户：受限操作（只能SELECT平台级，INSERT租户级）
CREATE USER app_agent WITH PASSWORD 'xxx';
GRANT CONNECT ON DATABASE content_agent TO app_agent;
GRANT USAGE ON SCHEMA public TO app_agent;
GRANT SELECT ON knowledge_base TO app_agent;
GRANT INSERT ON knowledge_base TO app_agent;
GRANT USAGE, SELECT ON SEQUENCE knowledge_base_id_seq TO app_agent;
```

**【新增】B.4 核心设计决策**

1. **统一表结构**：平台级和租户级使用同一张 `knowledge_base` 表，通过 `data_level` 字段区分，避免复杂的多表联合查询。

2. **RLS 策略叠加**：通过多个 POLICY 叠加实现复杂的权限控制，确保：
   - 平台管理员无法访问租户数据
   - 租户无法修改平台数据
   - Agent 可以跨级读取但只能写入租户数据

3. **应用层透明**：通过视图和存储过程封装两级数据的 UNION，调用方不需要感知平台级数据的查询。

4. **审计字段**：所有表包含 `created_by`/`updated_by` 字段，便于追踪数据操作责任人。

**【新增】B.5 权限术语对照表**

| 术语 | 说明 |
| ---- | ---- |
| `data_level` | 数据级别字段：`'platform'`=平台级，`'tenant'`=租户级 |
| `platform_category` | 平台级数据分类：`'public'`/`'industry'`/`'template'` |
| `enterprise_id` | 租户唯一标识，平台级数据此字段为 NULL |
| `is_platform_admin` | 会话上下文：当前用户是否为平台管理员 |
| `is_agent` | 会话上下文：当前请求是否为 Agent 系统触发 |
| RLS | Row-Level Security，PostgreSQL 行级安全策略 |
| 公共知识库 | 平台级数据，存放平台规则/方法论/合规通用规则 |
| 行业知识库 | 平台级数据，存放选题库/用户画像/痛点库 |
| 企业私有库 | 租户级数据，存放各企业自己的品牌/产品/历史笔记 |

***

## 附录C：API 层权限隔离

**【新增】C.1 API 路由架构**

| 前缀 | 适用角色 | 说明 |
| ---- | -------- | ---- |
| `/api/v1/tenant/knowledge/*` | 租户用户 | 企业私有库 CRUD |
| `/api/v1/platform/knowledge/*` | 平台管理员 | 公共/行业/模板 CRUD |
| `/api/v1/public/*` | 公开接口 | 健康检查等无需鉴权 |

**【新增】C.2 租户知识库 API 校验流程**

```python
# 租户 API 装饰器
def tenant_knowledge_api(f):
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        # 1. 从 JWT token 获取用户信息
        token = extract_token(request.headers.get('Authorization'))
        user = validate_token(token)

        # 2. 从请求头获取 enterprise_id
        request_enterprise_id = request.headers.get('X-Enterprise-Id')

        # 3. 校验 enterprise_id 与 token 中的一致性
        if request_enterprise_id != user.enterprise_id:
            return JsonResponse({
                'error': 'Forbidden',
                'message': 'enterprise_id 不匹配'
            }, status=403)

        # 4. 校验用户角色（非平台管理员）
        if user.is_platform_admin:
            return JsonResponse({
                'error': 'Forbidden',
                'message': '平台管理员不得使用租户 API'
            }, status=403)

        # 5. 注入 enterprise_id 到请求上下文
        request.enterprise_id = user.enterprise_id

        return f(request, *args, **kwargs)
    return decorated_function
```

**【新增】C.3 错误码对照**

| 错误码 | HTTP 状态码 | 说明 |
| ------ | ------------ | ---- |
| UNAUTHORIZED | 401 | 未登录或 token 无效 |
| FORBIDDEN | 403 | enterprise_id 不匹配或角色无权限 |
| NOT_FOUND | 404 | 资源不存在（本企业范围内） |
| BAD_REQUEST | 400 | 请求参数错误（如尝试设置平台级字段） |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
