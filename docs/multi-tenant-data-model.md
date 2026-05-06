# 多租户知识库数据模型隔离方案

## 一、设计目标

| 目标 | 说明 |
|------|------|
| 平台数据隔离 | 公共知识库、行业知识库、内置模板 仅平台方可见可改 |
| 租户数据隔离 | 企业私有库 仅本企业可见可改 |
| 跨级检索透明 | 租户检索时自动补充平台数据，对租户透明 |
| 强制隔离 | PostgreSQL RLS 从数据库层强制执行 |

## 二、数据分级定义

| 级别 | data_level 值 | 说明 | 可读 | 可写 | 可删 |
|------|---------------|------|------|------|------|
| 平台级 | `platform` | 公共知识库、行业知识库、内置模板 | 平台方 + 租户(Agent检索时) | 仅平台方 | 仅平台方 |
| 租户级 | `tenant` | 企业私有库 | 仅本租户 | 仅本租户 | 仅本租户 |

## 三、表结构设计

### 3.1 统一知识库表（同一套表，通过字段区分）

```sql
-- 启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 知识库表（统一表结构，支持平台级和租户级数据）
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    data_level VARCHAR(20) NOT NULL DEFAULT 'tenant',
    -- data_level: 'platform' = 平台级, 'tenant' = 租户级

    -- 平台级数据的归属
    platform_category VARCHAR(50) DEFAULT NULL,
    -- 当 data_level='platform' 时:
    --   'public'        = 公共知识库
    --   'industry'      = 行业知识库
    --   'template'      = 内置模板
    -- 当 data_level='tenant' 时，此字段为 NULL

    -- 租户级数据的归属
    enterprise_id VARCHAR(255) DEFAULT NULL,
    -- 当 data_level='tenant' 时必填
    -- 当 data_level='platform' 时为 NULL

    -- 知识内容
    category VARCHAR(100) DEFAULT NULL,     -- 知识分类：品牌/产品/人群/场景/行业等
    title VARCHAR(500) NOT NULL,           -- 知识标题
    content TEXT NOT NULL,                  -- 知识正文
    source VARCHAR(255) DEFAULT NULL,       -- 来源：obsidian/web/import
    source_url VARCHAR(1000) DEFAULT NULL, -- 原文URL或文件路径

    -- 向量数据
    embedding VECTOR(1024),                 -- bge-large-zh-v1.5 生成，1024维

    -- 元数据
    tags JSONB DEFAULT '[]',               -- 标签数组
    metadata JSONB DEFAULT '{}',            -- 扩展元数据（行业/品牌等）

    -- 审计字段
    created_by VARCHAR(255) DEFAULT NULL,   -- 创建者
    updated_by VARCHAR(255) DEFAULT NULL,   -- 更新者
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束：platform 数据 enterprise_id 必须为 NULL
    -- 约束：tenant 数据 enterprise_id 必须有值
    CONSTRAINT chk_platform_needs_null_enterprise
        CHECK (data_level = 'platform' AND enterprise_id IS NULL OR data_level = 'tenant'),
    CONSTRAINT chk_tenant_needs_enterprise
        CHECK (data_level = 'tenant' AND enterprise_id IS NOT NULL OR data_level = 'platform')
);

-- 向量索引 (IVFFlat for MVP, HNSW for production)
CREATE INDEX idx_kb_data_level ON knowledge_base(data_level);
CREATE INDEX idx_kb_enterprise ON knowledge_base(enterprise_id) WHERE enterprise_id IS NOT NULL;
CREATE INDEX idx_kb_platform_category ON knowledge_base(platform_category) WHERE platform_category IS NOT NULL;
CREATE INDEX idx_kb_embedding ON knowledge_base USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_kb_category ON knowledge_base(category);
```

### 3.2 行业分类表（平台级数据）

```sql
-- 行业分类表（平台级数据）
CREATE TABLE IF NOT EXISTS industry_categories (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,      -- 行业编码：health_product/ai_industry
    name VARCHAR(100) NOT NULL,            -- 行业名称
    description TEXT,                       -- 行业描述
    metadata JSONB DEFAULT '{}',            -- 扩展信息

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 行业知识库表（平台级数据，结构化行业知识）
CREATE TABLE IF NOT EXISTS industry_knowledge (
    id SERIAL PRIMARY KEY,
    industry_code VARCHAR(50) NOT NULL,    -- 关联 industry_categories.code
    category VARCHAR(100) NOT NULL,         -- 子分类：选题库/用户画像/痛点库/爆款拆解
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1024),

    metadata JSONB DEFAULT '{}',
    created_by VARCHAR(255) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ik_industry ON industry_knowledge(industry_code);
CREATE INDEX idx_ik_category ON industry_knowledge(category);
CREATE INDEX idx_ik_embedding ON industry_knowledge USING ivfflat(embedding vector_cosine_ops) WITH (lists = 50);
```

### 3.3 模板表（平台级数据）

```sql
-- 内置模板表（平台级数据）
CREATE TABLE IF NOT EXISTS templates (
    id SERIAL PRIMARY KEY,
    template_type VARCHAR(50) NOT NULL,    -- 类型：brand/product/persona/scene/compliance
    name VARCHAR(100) NOT NULL,            -- 模板名称
    content TEXT NOT NULL,                  -- 模板内容
    variables JSONB DEFAULT '[]',          -- 模板变量定义

    platform_category VARCHAR(50) DEFAULT 'template',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    version INTEGER DEFAULT 1,

    created_by VARCHAR(255) DEFAULT 'system',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tmpl_type ON templates(template_type);
CREATE INDEX idx_tmpl_active ON templates(is_active) WHERE is_active = true;
```

### 3.4 租户表（核心用户表）

```sql
-- 租户（企业）表
CREATE TABLE IF NOT EXISTS enterprises (
    id SERIAL PRIMARY KEY,
    enterprise_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,             -- 企业名称
    industry_code VARCHAR(50),             -- 所属行业
    plan VARCHAR(50) DEFAULT 'free',        -- 套餐：free/basic/professional/enterprise
    quota_monthly INTEGER DEFAULT 5,        -- 月度额度

    -- 状态
    status VARCHAR(20) DEFAULT 'active',    -- active/suspended/terminated
    activated_at TIMESTAMP,
    expires_at TIMESTAMP,

    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ent_status ON enterprises(status);
CREATE INDEX idx_ent_industry ON enterprises(industry_code);
```

## 四、RLS 策略设计

### 4.1 核心策略原则

| 角色 | 可读 | 可写 | 可删 |
|------|------|------|------|
| 平台管理员 (is_platform_admin = true) | 全部数据 | 仅平台级 | 仅平台级 |
| 租户用户 (enterprise_id = 'xxx') | 仅自己租户级 + 平台级(只读) | 仅自己租户级 | 仅自己租户级 |
| Agent系统用户 (is_agent = true) | 全部数据(检索用) | 仅租户级(写入检索结果) | 无 |

### 4.2 完整 RLS 策略

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

### 4.3 会话上下文设置

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

## 五、向量化与检索设计

### 5.1 统一检索查询（对租户透明）

```sql
-- 租户检索时，自动补充平台级数据
-- 应用层自动拼接 UNION，不需要租户感知

-- 租户可读的完整数据集（平台级 + 本租户级）
CREATE VIEW kb_tenant_readable AS
SELECT id, data_level, enterprise_id, platform_category,
       category, title, content, source, tags, metadata,
       created_at, updated_at
FROM knowledge_base
WHERE (
    -- 平台级数据
    (data_level = 'platform')
    -- 或本租户级数据
    OR (data_level = 'tenant' AND enterprise_id = current_setting('app.enterprise_id', true))
);

-- 语义检索时自动包含两级数据
CREATE OR REPLACE FUNCTION kb_semantic_search(
    p_query_embedding VECTOR(1024),
    p_enterprise_id VARCHAR(255),
    p_limit INTEGER DEFAULT 10,
    p_category VARCHAR(100) DEFAULT NULL
)
RETURNS TABLE (
    id SERIAL,
    data_level VARCHAR(20),
    enterprise_id VARCHAR(255),
    platform_category VARCHAR(50),
    category VARCHAR(100),
    title VARCHAR(500),
    content TEXT,
    source VARCHAR(255),
    tags JSONB,
    metadata JSONB,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    -- 平台级数据（统一检索）
    SELECT
        kb.id, kb.data_level, kb.enterprise_id, kb.platform_category,
        kb.category, kb.title, kb.content, kb.source, kb.tags, kb.metadata,
        1 - (kb.embedding <=> p_query_embedding) AS similarity
    FROM knowledge_base kb
    WHERE kb.data_level = 'platform'
      AND (p_category IS NULL OR kb.category = p_category)
    ORDER BY kb.embedding <=> p_query_embedding
    LIMIT p_limit

    UNION ALL

    -- 租户级数据（仅本租户）
    SELECT
        kb.id, kb.data_level, kb.enterprise_id, kb.platform_category,
        kb.category, kb.title, kb.content, kb.source, kb.tags, kb.metadata,
        1 - (kb.embedding <=> p_query_embedding) AS similarity
    FROM knowledge_base kb
    WHERE kb.data_level = 'tenant'
      AND kb.enterprise_id = p_enterprise_id
      AND (p_category IS NULL OR kb.category = p_category)
    ORDER BY kb.embedding <=> p_query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;
```

## 六、数据流转规则

### 6.1 写入规则

| 操作 | 目标 | 允许条件 |
|------|------|----------|
| 上传知识 | 企业私有库 (tenant) | 任何已认证租户用户 |
| 导入行业知识 | 行业知识库 (platform) | 仅平台管理员 |
| 创建模板 | 内置模板 (platform) | 仅平台管理员 |
| Agent自动入库 | 企业私有库 (tenant) | Agent系统，自动设置enterprise_id |

### 6.2 读取规则

| 操作 | 数据源 | 说明 |
|------|--------|------|
| 租户知识检索 | 企业私有库 + 平台级（自动UNION） | 对租户透明 |
| 平台方知识管理 | 平台级数据 | 仅平台级 |
| 租户知识管理 | 企业私有库 | 仅本租户 |
| Agent检索 | 全部（平台级 + 租户级） | 写入时只写租户级 |

## 七、数据库用户权限设计

```sql
-- 创建应用数据库用户（最小权限原则）
CREATE USER app_tenant WITH PASSWORD 'xxx';  -- 租户应用用户
CREATE USER app_platform WITH PASSWORD 'xxx'; -- 平台管理员用户
CREATE USER app_agent WITH PASSWORD 'xxx';    -- Agent系统用户

-- 租户用户：只能通过RLS策略访问（不能直接BYPASS）
GRANT CONNECT ON DATABASE content_agent TO app_tenant;
GRANT USAGE ON SCHEMA public TO app_tenant;
GRANT SELECT, INSERT, UPDATE, DELETE ON knowledge_base TO app_tenant;
GRANT USAGE, SELECT ON SEQUENCE knowledge_base_id_seq TO app_tenant;

-- 平台管理员用户：绕过RLS（用于管理后台）
GRANT CONNECT ON DATABASE content_agent TO app_platform;
GRANT USAGE ON SCHEMA public TO app_platform;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_platform;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_platform;

-- Agent系统用户：受限操作（只能SELECT平台级，INSERT租户级）
GRANT CONNECT ON DATABASE content_agent TO app_agent;
GRANT USAGE ON SCHEMA public TO app_agent;
GRANT SELECT ON knowledge_base TO app_agent;
GRANT INSERT ON knowledge_base TO app_agent;  -- 仅用于写入检索结果
GRANT USAGE, SELECT ON SEQUENCE knowledge_base_id_seq TO app_agent;
```

## 八、设计说明

### 8.1 核心设计决策

1. **统一表结构**：平台级和租户级使用同一张 `knowledge_base` 表，通过 `data_level` 字段区分，避免复杂的多表联合查询。

2. **RLS 策略叠加**：通过多个 POLICY 叠加实现复杂的权限控制，确保：
   - 平台管理员无法访问租户数据
   - 租户无法修改平台数据
   - Agent 可以跨级读取但只能写入租户数据

3. **应用层透明**：通过视图和存储过程封装两级数据的 UNION，调用方不需要感知平台级数据的查询。

4. **审计字段**：所有表包含 `created_by`/`updated_by` 字段，便于追踪数据操作责任人。

### 8.2 与现有 init.sql 的兼容

本方案**不兼容**现有 `init.sql` 的简化结构（仅 `enterprise_id`）。建议：

1. **新建库并行开发**：在测试环境验证新结构
2. **数据迁移脚本**：提供从旧结构到新结构的迁移脚本
3. **灰度发布**：先在 Agent 层支持新结构，逐步迁移

### 8.3 后续工作

| 优先级 | 任务 | 说明 |
|--------|------|------|
| P0 | 更新 `models/knowledge_base.py` 添加 data_level 字段 | 匹配新表结构 |
| P0 | 更新 `agents/kb_agent.py` 支持跨级检索 | 实现透明检索 |
| P0 | 更新 `sync/knowledge_loader.py` 设置 data_level | 导入时区分来源 |
| P1 | 更新 `tools/vector_tools.py` 支持 data_level 过滤 | 向量检索支持分级 |
| P1 | 编写数据迁移脚本 | 从旧结构迁移到新结构 |
| P2 | 更新前端 `app_kb.py` 权限控制 | 区分平台/租户界面 |
