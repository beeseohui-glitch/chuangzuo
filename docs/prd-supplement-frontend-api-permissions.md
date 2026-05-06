# PRD 补充章节：前端和 API 层的多租户权限隔离

> 本章节为 PRD V2.0 的补充内容，补充前端界面和 API 层面的多租户权限隔离设计。

---

## 一、前端知识管理页面权限边界

### 1.1 页面架构概览

| 入口路径 | 适用角色 | 可视范围 | 操作权限 |
| -------- | -------- | -------- | -------- |
| `/knowledge` | 租户用户 | 仅企业私有库 | CRUD（仅本企业） |
| `/admin/knowledge` | 平台管理员 | 公共/行业/模板 | CRUD（全部平台级） |

### 1.2 租户知识管理页面（`/knowledge`）

#### 页面结构

```
知识管理
├── 概览
│   ├── 知识条目统计（本企业）
│   ├── 分类分布
│   └── 最近更新
├── 知识列表
│   ├── 筛选：分类/标签/来源
│   ├── 搜索：（语义搜索，仅本企业）
│   └── 批量操作
├── 上传知识
│   ├── 文档上传（PDF/Word/Markdown）
│   ├── 表单录入
│   └── 批量导入
└── 设置
    ├── 导入/导出
    └── 同步配置
```

#### 功能约束

| 功能 | 约束说明 |
| ---- | -------- |
| 知识列表 | 仅展示 `data_level='tenant'` AND `enterprise_id=当前企业` 的数据 |
| 语义搜索 | 仅搜索本企业私有库（系统底层自动补充平台库，但对页面透明） |
| 上传文档 | 强制设置 `data_level='tenant'`，`enterprise_id=当前企业` |
| 编辑/删除 | 仅限本企业知识条目，其他条目灰度禁用 |
| 不展示平台库 | 页面不渲染任何公共/行业/模板相关内容 |

#### 语义搜索实现（对租户透明）

```javascript
// 租户前端搜索 - 仅调用企业私有库搜索
async function tenantSearch(query, filters) {
  // 前端只传 query，enterprise_id 从 session 获取
  const response = await api.post('/api/v1/knowledge/search', {
    query: query,
    enterprise_id: session.enterprise_id  // 前端不感知平台库
  });

  // 返回结果不包含 platform_category、data_level 等内部字段
  return response.data;  // { results: [...], total: 10 }
}

// 【内部】API 响应会自动补充平台库，但前端无感知
// 响应结构示例：
// {
//   "results": [
//     { "title": "...", "content": "...", "category": "brand" },
//     ...
//   ],
//   "sources": ["private", "industry", "public"]  // 仅内部日志，不返回前端
// }
```

### 1.3 租户上传文档流程

```
用户上传文档
        ↓
[前端校验]
        ↓
  enterprise_id = session.enterprise_id
  data_level = 'tenant'  // 前端显式设置
  platform_category = null
        ↓
[调用 API]
  POST /api/v1/tenant/knowledge/upload
  Body: { file, enterprise_id, data_level: 'tenant' }
        ↓
[API 校验]
        ↓
  校验 enterprise_id 与 token 中一致
  校验 data_level = 'tenant'
  校验 platform_category = null
        ↓
[写入数据库]
  data_level = 'tenant'
  enterprise_id = session.enterprise_id
  platform_category = NULL
```

### 1.4 前端页面路由守卫

```javascript
// 租户页面路由守卫
const tenantRoutes = [
  '/knowledge',
  '/knowledge/list',
  '/knowledge/upload',
  '/knowledge/search',
  '/analytics',
  '/creation'
];

router.beforeEach((to, from, next) => {
  const user = auth.getUser();

  // 租户用户不得访问平台管理后台
  if (to.path.startsWith('/admin/')) {
    if (user.role !== 'platform_admin') {
      return next('/403');  // 拒绝访问
    }
  }

  // 平台管理员不得访问租户创作界面（可选，视业务需求）
  if (tenantRoutes.includes(to.path) && user.role === 'platform_admin') {
    return next('/admin');  // 重定向到平台后台
  }

  next();
});
```

---

## 二、API 层权限隔离

### 2.1 API 路由架构

| 前缀 | 适用角色 | 说明 |
| ---- | -------- | ---- |
| `/api/v1/tenant/knowledge/*` | 租户用户 | 企业私有库 CRUD |
| `/api/v1/platform/knowledge/*` | 平台管理员 | 公共/行业/模板 CRUD |
| `/api/v1/public/*` | 公开接口 | 健康检查等无需鉴权 |

### 2.2 租户知识库 API

#### 路由清单

```
# 租户知识库 CRUD
GET    /api/v1/tenant/knowledge/list          # 列出本企业知识
GET    /api/v1/tenant/knowledge/:id          # 获取单条知识详情
POST   /api/v1/tenant/knowledge             # 新增知识（表单录入）
POST   /api/v1/tenant/knowledge/upload      # 上传文档
PUT    /api/v1/tenant/knowledge/:id         # 更新知识
DELETE /api/v1/tenant/knowledge/:id         # 删除知识

# 租户知识检索
POST   /api/v1/tenant/knowledge/search      # 语义搜索（本企业库）
GET    /api/v1/tenant/knowledge/stats       # 知识统计

# 租户模板
GET    /api/v1/tenant/templates             # 获取可用模板（从平台库读取，只读）
```

#### 请求头要求

```
Authorization: Bearer <JWT_TOKEN>
X-Enterprise-Id: ent_xxx    # 显式传递 enterprise_id
Content-Type: application/json
```

#### API 校验流程

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

#### 入库目标锁定校验

```python
@tenant_knowledge_api
def create_knowledge(request):
    body = json.loads(request.body)

    # 强制锁定为租户级
    if body.get('data_level') != 'tenant':
        return JsonResponse({
            'error': 'Bad Request',
            'message': '企业用户只能创建租户级知识'
        }, status=400)

    # 强制 enterprise_id 为当前用户所属企业
    if body.get('enterprise_id') != request.enterprise_id:
        return JsonResponse({
            'error': 'Forbidden',
            'message': 'enterprise_id 必须与当前登录企业一致'
        }, status=403)

    # 强制 platform_category 为 null
    if body.get('platform_category') is not None:
        return JsonResponse({
            'error': 'Bad Request',
            'message': '企业用户不得设置 platform_category'
        }, status=400)

    # 写入数据库（RLS 会自动过滤）
    knowledge = KnowledgeBase.objects.create(
        data_level='tenant',
        enterprise_id=request.enterprise_id,
        platform_category=None,
        category=body['category'],
        title=body['title'],
        content=body['content'],
        created_by=request.enterprise_id
    )

    return JsonResponse({'id': knowledge.id, 'status': 'created'})
```

### 2.3 平台管理员 API

#### 路由清单

```
# 平台公共知识库
GET    /api/v1/platform/knowledge/public/list     # 列出公共知识
POST   /api/v1/platform/knowledge/public          # 创建公共知识
PUT    /api/v1/platform/knowledge/public/:id     # 更新公共知识
DELETE /api/v1/platform/knowledge/public/:id     # 删除公共知识

# 平台行业知识库
GET    /api/v1/platform/knowledge/industry/list      # 列出行业
GET    /api/v1/platform/knowledge/industry/:code/knowledge  # 列出某行业知识
POST   /api/v1/platform/knowledge/industry/:code/knowledge  # 创建行业知识
PUT    /api/v1/platform/knowledge/industry/:code/knowledge/:id  # 更新
DELETE /api/v1/platform/knowledge/industry/:code/knowledge/:id  # 删除

# 平台模板管理
GET    /api/v1/platform/templates                    # 列出模板
POST   /api/v1/platform/templates                  # 创建模板
PUT    /api/v1/platform/templates/:id               # 更新模板
DELETE /api/v1/platform/templates/:id               # 删除模板

# 平台行业分类管理
GET    /api/v1/platform/industries                  # 列出所有行业
POST   /api/v1/platform/industries                  # 创建行业
PUT    /api/v1/platform/industries/:code           # 更新行业
DELETE /api/v1/platform/industries/:code           # 删除行业

# 平台数据统计
GET    /api/v1/platform/stats                       # 平台知识库统计
```

#### 平台管理员校验

```python
# 平台管理员 API 装饰器
def platform_admin_api(f):
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        # 1. JWT token 校验
        token = extract_token(request.headers.get('Authorization'))
        user = validate_token(token)

        # 2. 校验平台管理员角色
        if not user.is_platform_admin:
            return JsonResponse({
                'error': 'Forbidden',
                'message': '仅平台管理员可访问此接口'
            }, status=403)

        # 3. 设置会话上下文
        request.is_platform_admin = True
        request.enterprise_id = None  # 平台管理员无 enterprise_id

        return f(request, *args, **kwargs)
    return decorated_function

@platform_admin_api
def create_public_knowledge(request):
    body = json.loads(request.body)

    # 创建平台级数据
    knowledge = KnowledgeBase.objects.create(
        data_level='platform',
        platform_category='public',
        enterprise_id=None,  # 平台级数据无 enterprise_id
        category=body['category'],
        title=body['title'],
        content=body['content'],
        created_by='platform_admin'
    )

    return JsonResponse({'id': knowledge.id, 'status': 'created'})
```

### 2.4 语义搜索 API（跨级透明）

```python
@tenant_knowledge_api
def search_knowledge(request):
    """
    语义搜索 - 对租户透明，自动补充平台库

    内部执行三层检索，但 API 响应不暴露数据来源
    """
    body = json.loads(request.body)
    query = body['query']
    enterprise_id = request.enterprise_id

    # ========== 第一层：本企业私有库 ==========
    private_results = vector_search(
        embedding=encode(query),
        filters={
            'data_level': 'tenant',
            'enterprise_id': enterprise_id
        },
        limit=10
    )

    # ========== 第二层：行业知识库 ==========
    industry_results = vector_search(
        embedding=encode(query),
        filters={
            'data_level': 'platform',
            'platform_category': 'industry'
        },
        limit=5
    )

    # ========== 第三层：公共知识库 ==========
    public_results = vector_search(
        embedding=encode(query),
        filters={
            'data_level': 'platform',
            'platform_category': 'public'
        },
        limit=5
    )

    # ========== 组装结果（不暴露来源层级）==========
    merged = merge_results(private_results, industry_results, public_results)

    # 【关键】移除内部字段
    for item in merged:
        item.pop('data_level', None)
        item.pop('platform_category', None)
        item.pop('enterprise_id', None)

    return JsonResponse({
        'results': merged,
        'total': len(merged),
        # 'sources' 字段不返回前端，仅内部日志
    })
```

### 2.5 API 响应格式

#### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功"
}
```

#### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "enterprise_id 不匹配"
  }
}
```

#### 错误码对照

| 错误码 | HTTP 状态码 | 说明 |
| ------ | ------------ | ---- |
| UNAUTHORIZED | 401 | 未登录或 token 无效 |
| FORBIDDEN | 403 | enterprise_id 不匹配或角色无权限 |
| NOT_FOUND | 404 | 资源不存在（本企业范围内） |
| BAD_REQUEST | 400 | 请求参数错误（如尝试设置平台级字段） |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

---

## 三、平台方管理后台页面设计

### 3.1 页面结构概览

```
平台管理后台 (/admin)
├── 知识库管理
│   ├── 公共知识库 (/admin/knowledge/public)
│   ├── 行业知识库 (/admin/knowledge/industry)
│   │   ├── 保健品
│   │   ├── AI行业
│   │   └── 更多...
│   └── 内置模板 (/admin/knowledge/templates)
├── 行业分类管理 (/admin/industries)
├── 模板管理 (/admin/templates)
├── 合规词库管理 (/admin/compliance)
├── 企业管理 (/admin/enterprises)
├── 数据统计 (/admin/stats)
└── 系统设置 (/admin/settings)
```

### 3.2 公共知识库管理页面

#### 页面路径

`/admin/knowledge/public`

#### 功能列表

| 功能 | 说明 |
| ---- | ---- |
| 列表浏览 | 按分类、标签筛选公共知识 |
| 搜索 | 语义搜索公共知识库 |
| 新增 | 创建公共知识（标题、内容、分类、标签） |
| 编辑 | 修改公共知识 |
| 删除 | 删除公共知识（需二次确认） |
| 批量导入 | Markdown 批量导入 |
| 批量导出 | 导出为 Markdown 文件 |

#### 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│ 公共知识库管理                                              │
├─────────────────────────────────────────────────────────────┤
│ 分类： [平台规则 ▼] [创作方法论 ▼] [合规规则 ▼] [全部 ▼]   │
│ 搜索： [________________________] [搜索]                    │
├─────────────────────────────────────────────────────────────┤
│ + 新增公共知识                                              │
├─────────────────────────────────────────────────────────────┤
│ ☑ 标题               │ 分类       │ 标签       │ 操作    │
│─────────────────────────────────────────────────────────────│
│ ☐ 平台审核规则       │ 平台规则   │ #审核 #规则 │ 编辑 删除 │
│ ☐ 小红书内容规范     │ 平台规则   │ #小红书    │ 编辑 删除 │
│ ☐ 公众号发文规范     │ 平台规则   │ #公众号    │ 编辑 删除 │
│ ☐ 广告法禁用词       │ 合规规则   │ #广告法    │ 编辑 删除 │
│ ☐ 创作方法论         │ 创作方法论 │ #方法论    │ 编辑 删除 │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 行业知识库管理页面

#### 页面路径

`/admin/knowledge/industry`

#### 功能列表

| 功能 | 说明 |
| ---- | ---- |
| 行业切换 | 左侧导航切换不同行业 |
| 分类管理 | 选题库/用户画像/痛点库/爆款拆解 |
| 知识 CRUD | 新增/编辑/删除/批量导入 |
| 预览 | 查看知识详情和向量化预览 |

#### 页面布局

```
┌────────────────┬─────────────────────────────────────────────┐
│ 行业知识库      │ 公共知识库 > 保健品                        │
├────────────────┼─────────────────────────────────────────────┤
│ ▼ 保健品       │ 分类：[选题库 ▼] [全部 ▼] [+新增]          │
│   选题库       ├─────────────────────────────────────────────┤
│   用户画像     │ ☑ 标题              │ 分类    │ 操作        │
│   痛点库       │─────────────────────────────────────────────│
│   爆款拆解     │ ☐ 熬夜场景选题     │ 选题库  │ 编辑 删除    │
│                │ ☐ 护肝成分选题     │ 选题库  │ 编辑 删除    │
│ ▼ AI行业       │ ☐ 职场人群选题     │ 选题库  │ 编辑 删除    │
│   选题库       │ ☐ 应酬场景选题     │ 选题库  │ 编辑 删除    │
│   用户画像     │─────────────────────────────────────────────│
│                │                    [批量导入] [导出]        │
└────────────────┴─────────────────────────────────────────────┘
```

### 3.4 内置模板管理页面

#### 页面路径

`/admin/templates`

#### 功能列表

| 功能 | 说明 |
| ---- | ---- |
| 模板列表 | 按类型筛选（品牌/产品/人群/场景/合规） |
| 模板预览 | 查看模板内容和变量定义 |
| 创建模板 | 设置模板类型、名称、内容、变量 |
| 编辑模板 | 修改模板内容和版本升级 |
| 禁用/启用 | 软删除，保留历史数据 |
| 模板版本 | 版本历史记录和回滚 |

#### 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│ 内置模板管理                                                │
├─────────────────────────────────────────────────────────────┤
│ 类型： [全部 ▼] [品牌模板 ▼] [产品模板 ▼] [人群 ▼] [场景 ▼]│
├─────────────────────────────────────────────────────────────┤
│ + 创建模板                                                  │
├─────────────────────────────────────────────────────────────┤
│ 模板名称       │ 类型      │ 版本  │ 状态    │ 操作        │
│─────────────────────────────────────────────────────────────│
│ 品牌介绍模板   │ 品牌模板  │ v3    │ 启用中  │ 编辑 版本 禁用│
│ 产品概览模板   │ 产品模板  │ v2    │ 启用中  │ 编辑 版本 禁用│
│ 人群画像模板   │ 人群模板  │ v1    │ 启用中  │ 编辑 版本 禁用│
│ 场景使用模板   │ 场景模板  │ v1    │ 禁用    │ 编辑 版本 启用│
│ 合规红线模板   │ 合规模板  │ v2    │ 启用中  │ 编辑 版本 禁用│
└─────────────────────────────────────────────────────────────┘
```

### 3.5 合规词库管理页面

#### 页面路径

`/admin/compliance`

#### 功能列表

| 功能 | 说明 |
| ---- | ----|
| 词库分类 | P0禁用词/P1警告词/P2关注词 |
| 平台规则词库 | 广告法禁用词、医疗用语等 |
| 行业规则词库 | 按行业区分的合规要求 |
| 企业规则 | 查看各企业自定义规则（只读） |
| 词库导入/导出 | 批量管理 |

#### 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│ 合规词库管理                                                │
├─────────────────────────────────────────────────────────────┤
│ 分类： [P0禁用词 ▼] [P1警告词 ▼] [P2关注词 ▼]              │
│ 行业： [全部 ▼] [保健品 ▼] [AI行业 ▼]                       │
├─────────────────────────────────────────────────────────────┤
│ + 新增词条                     [批量导入] [导出]            │
├─────────────────────────────────────────────────────────────┤
│ 词条内容             │ 级别 │ 适用行业  │ 说明       │ 操作 │
│─────────────────────────────────────────────────────────────│
│ 最棒                  │ P0   │ 全部      │ 绝对化用语 │ 编辑 │
│ 第一                  │ P0   │ 全部      │ 绝对化用语 │ 编辑 │
│ 治疗                  │ P0   │ 保健品    │ 医疗用语  │ 编辑 │
│ 治愈                  │ P0   │ 保健品    │ 医疗用语  │ 编辑 │
│ 彻底                  │ P1   │ 全部      │ 绝对化用语 │ 编辑 │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、前端组件权限控制

### 4.1 权限组件

```javascript
// 租户权限检查
const TenantGate = {
  // 检查是否为租户用户
  isTenant: () => auth.getUser()?.role === 'tenant',

  // 检查是否可以访问知识管理
  canAccessKnowledge: () => true,  // 租户默认可访问

  // 检查是否可以编辑知识条目
  canEditEntry: (entry) => {
    if (!TenantGate.isTenant()) return false;
    return entry.enterprise_id === auth.getUser().enterprise_id;
  },

  // 检查是否可以删除知识条目
  canDeleteEntry: (entry) => TenantGate.canEditEntry(entry)
};

// 平台管理员权限检查
const PlatformAdminGate = {
  isPlatformAdmin: () => auth.getUser()?.role === 'platform_admin',

  // 检查是否可以管理公共知识库
  canManagePublic: () => PlatformAdminGate.isPlatformAdmin(),

  // 检查是否可以管理行业知识库
  canManageIndustry: () => PlatformAdminGate.isPlatformAdmin(),

  // 检查是否可以管理模板
  canManageTemplates: () => PlatformAdminGate.isPlatformAdmin()
};
```

### 4.2 知识列表组件

```javascript
// 租户知识列表组件
const TenantKnowledgeList = {
  // 获取数据（仅本企业）
  async fetchList(filters) {
    const response = await api.get('/api/v1/tenant/knowledge/list', {
      params: {
        enterprise_id: auth.getUser().enterprise_id,
        ...filters
      }
    });
    return response.data;
  },

  // 删除确认
  async confirmDelete(entry) {
    if (!TenantGate.canDeleteEntry(entry)) {
      toast.error('无权删除此条目');
      return;
    }
    // 确认后调用 DELETE /api/v1/tenant/knowledge/:id
  }
};
```

### 4.3 平台管理员知识列表组件

```javascript
// 平台管理员知识列表组件
const PlatformKnowledgeList = {
  // 获取公共知识库
  async fetchPublicList(filters) {
    const response = await api.get('/api/v1/platform/knowledge/public/list', {
      params: filters
    });
    return response.data;
  },

  // 获取行业知识库
  async fetchIndustryList(industryCode, filters) {
    const response = await api.get(
      `/api/v1/platform/knowledge/industry/${industryCode}/knowledge`,
      { params: filters }
    );
    return response.data;
  }
};
```

---

## 五、部署架构

### 5.1 前端路由结构

```
Next.js /app 目录结构
├── (tenant)/                    # 租户布局
│   ├── layout.tsx              # 租户通用布局
│   ├── knowledge/
│   │   ├── page.tsx           # 知识管理首页
│   │   ├── list/page.tsx       # 知识列表
│   │   ├── upload/page.tsx     # 上传页面
│   │   └── search/page.tsx     # 搜索页面
│   └── ...
│
├── (platform)/                  # 平台管理员布局
│   ├── layout.tsx              # 平台管理通用布局
│   ├── admin/
│   │   ├── knowledge/
│   │   │   ├── public/page.tsx
│   │   │   ├── industry/page.tsx
│   │   │   └── templates/page.tsx
│   │   ├── compliance/page.tsx
│   │   ├── industries/page.tsx
│   │   └── ...
│   └── ...
│
└── (public)/                   # 公开页面
    ├── page.tsx
    └── login/page.tsx
```

### 5.2 API 服务结构

```
FastAPI /app 目录结构
├── api/
│   ├── v1/
│   │   ├── tenant/
│   │   │   ├── knowledge/
│   │   │   │   ├── list.py
│   │   │   │   ├── detail.py
│   │   │   │   ├── create.py
│   │   │   │   ├── update.py
│   │   │   │   ├── delete.py
│   │   │   │   ├── search.py
│   │   │   │   └── upload.py
│   │   │   └── __init__.py
│   │   │   └── templates.py
│   │   │
│   │   ├── platform/
│   │   │   ├── knowledge/
│   │   │   │   ├── public/
│   │   │   │   │   ├── list.py
│   │   │   │   │   ├── create.py
│   │   │   │   │   ├── update.py
│   │   │   │   │   └── delete.py
│   │   │   │   └── industry/
│   │   │   │       ├── list.py
│   │   │   │       ├── create.py
│   │   │   │       ├── update.py
│   │   │   │       └── delete.py
│   │   │   ├── templates/
│   │   │   │   └── ...
│   │   │   ├── compliance/
│   │   │   │   └── ...
│   │   │   └── industries/
│   │   │       └── ...
│   │   │
│   │   └── public/
│   │       └── health.py
│   │
│   └── dependencies/
│       ├── auth.py
│       ├── tenant_context.py
│       └── platform_context.py
```
