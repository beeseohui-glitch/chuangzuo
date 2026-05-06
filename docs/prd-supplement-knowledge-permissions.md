# PRD 补充章节：知识库权限体系

> 本章节为 PRD V2.0 第三章"知识库体系"的补充内容，补充多租户场景下的知识库权限约束。

---

## 3.7 知识库访问权限矩阵

### 3.7.1 权限层级定义

| 权限级别 | 说明 |
| -------- | ---- |
| **完全控制** | 可读、可写、可删 |
| **可读可写** | 可读、可写，不可删 |
| **只读** | 仅可读，不可写、不可删 |
| **不可见** | 对该层级数据不可见 |

### 3.7.2 三层知识库的权限矩阵

| 知识库层级 | 数据级别 | 平台方（运营） | 平台方（管理员） | 租户（企业） | Agent系统 |
| ---------- | -------- | -------------- | --------------- | ------------ | --------- |
| **公共知识库** | platform / public | 只读 | 完全控制 | **不可见** | 只读（检索用） |
| **行业知识库** | platform / industry | 只读 | 完全控制 | **不可见** | 只读（检索用） |
| **内置模板** | platform / template | 只读 | 完全控制 | **不可见** | 只读（检索用） |
| **企业私有库** | tenant | 不可见 | 不可见 | 完全控制 | 可读写（写入检索结果） |

### 3.7.3 权限规则说明

#### 平台方权限规则

| 角色 | 可操作范围 | 说明 |
| ---- | ---------- | ---- |
| 平台运营 | 公共知识库、模板（只读） | 可浏览参考，不能修改 |
| 平台管理员 | 公共知识库、行业知识库、内置模板（完全控制） | 可增删改查所有平台级数据 |

#### 租户权限规则

| 权限项 | 企业私有库 | 公共/行业/模板 |
| ------ | ---------- | -------------- |
| 浏览 | ✅ 本企业数据 | ❌ 完全不可见 |
| 检索 | ✅ 本企业数据 | ❌ 完全不可见 |
| 新增 | ✅ 仅本企业 | ❌ 无权限 |
| 修改 | ✅ 仅本企业 | ❌ 无权限 |
| 删除 | ✅ 仅本企业 | ❌ 无权限 |

**重要约束**：租户在知识管理界面中**完全感知不到**公共知识库、行业知识库、内置模板的存在。所有平台级数据的调用由系统在 Agent 层面自动完成。

---

## 3.8 知识入库权限规则

### 3.8.1 数据写入目标锁定

| 数据来源 | 写入目标 | 归属字段 | 允许条件 |
| -------- | -------- | -------- | -------- |
| 企业上传（Web界面） | 企业私有库 | `data_level='tenant'`, `enterprise_id=企业ID` | 已认证的租户用户 |
| 企业上传（Obsidian同步） | 企业私有库 | `data_level='tenant'`, `enterprise_id=企业ID` | 已配置的 Obsidian Vault |
| 平台方导入（行业知识） | 行业知识库 | `data_level='platform'`, `platform_category='industry'` | 仅平台管理员 |
| 平台方导入（公共规则） | 公共知识库 | `data_level='platform'`, `platform_category='public'` | 仅平台管理员 |
| 平台方配置（模板） | 内置模板 | `data_level='platform'`, `platform_category='template'` | 仅平台管理员 |

### 3.8.2 写入校验流程

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

### 3.8.3 平台级数据写入约束

| 写入来源 | 目标 | 校验机制 |
| -------- | ---- | -------- |
| 平台管理员 | platform_category IN ('public', 'industry', 'template') | RLS策略校验 `is_platform_admin=true` |
| 租户用户 | 任何 platform 数据 | RLS策略直接拒绝 |

---

## 3.9 素材检索 Agent 的三层检索权限控制

### 3.9.1 三层检索逻辑

素材检索 Agent 在执行检索时，按以下顺序依次检索：

| 层级 | 检索优先级 | 读写权限 | 检索范围 | 数据归属 |
| ---- | ---------- | -------- | -------- | -------- |
| **第一层：企业私有库** | 最高（精准匹配） | 读写 | 本企业全部数据 | `data_level='tenant'`, `enterprise_id=当前企业` |
| **第二层：行业知识库** | 中（系统补充） | 只读 | 全量行业知识 | `data_level='platform'`, `platform_category='industry'` |
| **第三层：公共知识库** | 低（兜底） | 只读 | 全量公共知识 | `data_level='platform'`, `platform_category='public'` |

### 3.9.2 检索流程（对租户透明）

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

### 3.9.3 租户感知模型

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

### 3.9.4 Agent 系统用户的会话上下文

```sql
-- Agent 执行检索前设置会话上下文
SET app.enterprise_id = 'ent_xxx';      -- 当前企业ID（用于写入租户级数据）
SET app.is_platform_admin = 'false';
SET app.is_agent = 'true';              -- 标记为Agent系统用户
```

RLS 策略根据 `is_agent=true` 允许读取平台级数据，但写入时只允许写入 `data_level='tenant'` 的数据。

---

## 3.10 平台方知识库管理后台

### 3.10.1 功能定位

平台方知识库管理后台是**平台管理员**维护公共知识库、行业知识库、内置模板的专用入口。租户无法访问此后台。

### 3.10.2 可管理的数据范围

| 类别 | platform_category | 可管理内容 |
| ---- | ---------------- | ---------- |
| 公共知识库 | `public` | 平台规则、创作方法论、合规通用规则 |
| 行业知识库 | `industry` | 选题库、用户画像、痛点库、爆款拆解 |
| 内置模板 | `template` | 品牌模板、产品模板、人群模板、场景模板 |

### 3.10.3 平台后台功能列表

| 功能 | 说明 |
| ---- | ---- |
| **行业知识管理** | 新增/编辑/删除行业知识，支持批量导入 Markdown |
| **公共知识管理** | 新增/编辑/删除公共知识（平台规则/合规规则） |
| **模板管理** | 创建/编辑/版本控制内置模板 |
| **行业分类配置** | 新增行业、维护行业编码和描述 |
| **数据统计** | 各行业知识库条目数量、检索热度统计 |
| **批量操作** | Markdown 文件批量上传、批量向量化 |

### 3.10.4 平台后台与租户后台的隔离

| 对比维度 | 平台方管理后台 | 租户知识管理界面 |
| -------- | -------------- | ---------------- |
| 访问入口 | `/admin/kb` | `/kb` |
| 可视数据 | 公共/行业/模板 | 仅本企业私有库 |
| 写入目标 | `data_level='platform'` | `data_level='tenant'` |
| 认证方式 | 平台管理员账号 | 企业租户账号 |
| RLS策略 | `is_platform_admin=true` | `enterprise_id=当前企业` |

### 3.10.5 平台后台界面结构

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

---

## 3.11 审计与日志

### 3.11.1 知识库操作审计字段

| 字段 | 说明 |
| ---- | ---- |
| `created_by` | 创建者 ID |
| `updated_by` | 更新者 ID |
| `created_at` | 创建时间 |
| `updated_at` | 更新时间 |

### 3.11.2 审计日志记录

| 操作类型 | 记录内容 | 保留期限 |
| -------- | -------- | -------- |
| 知识入库 | enterprise_id, data_level, category, created_by | 1年 |
| 知识检索 | enterprise_id, query, results_count, source_levels | 6个月 |
| 知识删除 | enterprise_id, deleted_id, deleted_by | 1年 |
| 平台数据变更 | admin_id, table_name, record_id, action | 永久 |

### 3.11.3 异常行为检测

| 异常场景 | 检测逻辑 | 处理方式 |
| -------- | -------- | -------- |
| 租户尝试写入平台数据 | RLS 策略拒绝 + 日志记录 | 触发安全告警 |
| 租户尝试读取平台数据 | 前端不渲染 + API 校验 | 记录访问尝试 |
| 大批量检索平台数据 | Agent 只读频率监控 | 限制单次检索条数 |
| 异常删除企业数据 | 删除前备份 + 需二次确认 | 操作延迟生效 |

---

## 3.12 技术实现要点

### 3.12.1 RLS 策略核心

```sql
-- 租户只能访问自己企业私有库 + 平台级只读
CREATE POLICY kb_tenant_crud ON knowledge_base FOR ALL
    USING (data_level = 'tenant' AND enterprise_id = current_setting('app.enterprise_id', true));

CREATE POLICY kb_tenant_read_platform ON knowledge_base FOR SELECT
    USING (data_level = 'platform');

-- 平台管理员可读写所有平台级数据
CREATE POLICY kb_platform_admin_all ON knowledge_base FOR ALL
    USING (data_level = 'platform' AND current_setting('app.is_platform_admin', true)::boolean = true);
```

### 3.12.2 应用层会话上下文

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

### 3.12.3 检索结果组装

```python
# 素材检索 Agent 检索逻辑（对租户透明）
def retrieve_material_pack(query, enterprise_id):
    # 第一层：本企业私有库
    private_results = vector_search(
        embedding=query,
        data_level='tenant',
        enterprise_id=enterprise_id
    )

    # 第二层：行业知识库（系统自动补充）
    industry_results = vector_search(
        embedding=query,
        data_level='platform',
        platform_category='industry'
    )

    # 第三层：公共知识库（系统自动兜底）
    public_results = vector_search(
        embedding=query,
        data_level='platform',
        platform_category='public'
    )

    # 组装（不暴露来源层级）
    return assemble_material_pack(
        private=private_results,      # 精准，采用
        industry=industry_results,    # 补充，采用
        public=public_results         # 兜底，采用
    )
```

---

## 附录：权限术语对照表

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
