# PRD 补充章节：Agent 层面的多租户权限控制

> 本章节为 PRD V2.0 第二章"Agent 详细设计"的补充内容，补充各 Agent 的多租户权限控制实现细节。

---

## Agent 1：统一调度Agent（Harness 补充）

### 权限校验增强

| 控制项 | 实现方式 | 说明 |
| ------ | -------- | ---- |
| 租户身份校验 | `enterprise_id` + `user_role` | 校验用户是否属于有效租户 |
| 知识库访问范围约束 | 仅传递 `enterprise_id` 给下游 Agent | 下游 Agent 凭此 ID 过滤企业私有库 |
| 套餐额度校验 | 查询 `enterprises` 表的 `quota_monthly` | 校验剩余额度是否充足 |
| 平台访问权限校验 | 根据 `plan` 字段校验可用的目标平台 | free 版仅小红书，基础版及以上多平台 |

### 租户身份校验流程

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

### 向下游传递的上下文

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

---

## Agent 2：素材检索Agent（Harness 补充）

### Prompt 补充（知识库检索说明）

```
# 知识库检索范围
你检索的范围包括三层知识库，按优先级排序：

1. 企业私有库（最高优先级）
   - 检索条件：data_level='tenant' AND enterprise_id=当前企业ID
   - 租户自己的品牌、产品、历史笔记等精准数据
   - 完全匹配，直接采用

2. 行业知识库（次优先级）
   - 检索条件：data_level='platform' AND platform_category='industry'
   - 平台预设的选题库、用户画像、痛点库
   - 补充到素材包，不覆盖企业私有库内容

3. 公共知识库（最低优先级）
   - 检索条件：data_level='platform' AND platform_category='public'
   - 平台规则、创作方法论、合规通用规则
   - 作为兜底补充

# 重要约束
- 企业私有库检索结果：直接采用
- 行业知识库和公共知识库检索结果：仅作为补充，自动标记来源层级为"平台补充"
- 组装素材包时：不得暴露具体的数据来源层级
- 素材包输出结构不得包含 platform_category、data_level 等内部字段
```

### 三层检索权限控制实现

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

### 隐私隔离实现

| 控制项 | 实现方式 |
| ------ | -------- |
| 会话上下文设置 | `SET app.enterprise_id='ent_xxx'` 后执行检索 |
| RLS 策略 | PostgreSQL 自动过滤非本企业数据 |
| 结果校验 | 向量检索返回时校验 `enterprise_id` 匹配 |
| Agent 只读平台数据 | `SET app.is_agent=true` 允许读取 `data_level='platform'` |

### 返回给租户的素材包示例

```json
{
  "brand": {
    "name": "某护肝品牌",
    "tone": ["专业", "亲和"],
    "taboos": ["最高", "第一"]
  },
  "product": {
    "name": "护肝片",
    "selling_points": ["水飞蓟素", "三重护肝"],
    "ingredients": ["水飞蓟素", "葛根", "五味子"],
    "evidence": ["临床验证", "专利成分"]
  },
  "persona": {
    "profile": "长期熬夜、饮酒应酬、高强度工作的职场人群",
    "pain_points": ["熬夜伤肝", "酒精代谢负担", "精力不济"],
    "language_style": "口语化、专业但不晦涩"
  },
  "scene": {
    "description": "熬夜后第二天精力恢复",
    "usage_method": "每日一粒，睡前服用"
  },
  "compliance": {
    "rules": ["保健食品不能宣传治疗作用", "不得使用医疗用语"],
    "forbidden_groups": ["孕妇", "儿童", "肝功能异常者"]
  }
}
```

---

## Agent 6：合规Agent（Harness 补充）

### 合规规则库的层级说明

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

### 合规校验流程（不暴露规则来源）

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

### 企业规则库校验

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

---

## Agent 10：知识库管理Agent（Harness 补充）

### Prompt 补充（入库目标锁定）

```
# 职责
处理企业上传的文档，完成解析、提取、分类、入库。

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

### 入库流程实现

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

### 入库权限校验流程

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

---

## 附录：Agent 权限术语对照

| 术语 | 说明 |
| ---- | ---- |
| `enterprise_id` | 租户唯一标识，每个请求必须携带 |
| `data_level` | `'tenant'`=租户级，`'platform'`=平台级 |
| `platform_category` | 平台级分类：`'public'`/`'industry'`/`'template'` |
| `is_platform_admin` | 会话上下文：是否为平台管理员 |
| `is_agent` | 会话上下文：是否为 Agent 系统调用 |
| 素材检索 Agent 三层检索 | 企业私有库 → 行业知识库 → 公共知识库（对租户透明） |
| 知识入库目标锁定 | 企业上传 → 强制写入 `data_level='tenant'` |
| 合规规则库只读 | 平台规则库和行业规则库对租户只读 |
