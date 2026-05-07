-- ============================================
-- 智创笔记 - 完整数据库初始化脚本
-- 包含：pgvector扩展 + 全部表结构 + 索引
-- ============================================

-- 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================
-- 1. 企业表
-- ============================================
CREATE TABLE IF NOT EXISTS enterprises (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100) DEFAULT NULL,
    plan_type VARCHAR(50) DEFAULT 'basic',
    quota_monthly INTEGER DEFAULT 100,
    quota_used INTEGER DEFAULT 0,
    settings JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'active',
    expire_at TIMESTAMP DEFAULT NULL,
    contact_name VARCHAR(100) DEFAULT NULL,
    contact_email VARCHAR(255) DEFAULT NULL,
    contact_phone VARCHAR(50) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 2. 用户表
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'tenant',
    -- role: 'tenant' | 'tenant_admin' | 'tenant_user' | 'platform_admin' | 'platform_operator'
    enterprise_id VARCHAR(255) REFERENCES enterprises(id),
    avatar_url VARCHAR(1000) DEFAULT NULL,
    status VARCHAR(20) DEFAULT 'active',
    last_login_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_enterprise ON users(enterprise_id);

-- ============================================
-- 3. 统一知识库表（平台级 + 租户级）
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    data_level VARCHAR(20) NOT NULL DEFAULT 'tenant',
    -- 'platform' = 平台级, 'tenant' = 租户级

    platform_category VARCHAR(50) DEFAULT NULL,
    -- data_level='platform' 时: 'public'/'industry'/'template'
    -- data_level='tenant' 时: NULL

    enterprise_id VARCHAR(255) DEFAULT NULL,
    -- data_level='tenant' 时必填
    -- data_level='platform' 时为 NULL

    category VARCHAR(100) DEFAULT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(255) DEFAULT NULL,
    source_url VARCHAR(1000) DEFAULT NULL,

    embedding VECTOR(1024),

    sync_status VARCHAR(20) DEFAULT 'pending',
    -- 'pending' = 待向量化 | 'synced' = 已同步 | 'failed' = 向量化失败

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

-- 知识库索引
CREATE INDEX IF NOT EXISTS idx_kb_data_level ON knowledge_base(data_level);
CREATE INDEX IF NOT EXISTS idx_kb_platform_category ON knowledge_base(platform_category);
CREATE INDEX IF NOT EXISTS idx_kb_enterprise ON knowledge_base(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_kb_category ON knowledge_base(category);
-- IVFFlat 向量索引（vector_cosine_ops，lists=100）
CREATE INDEX IF NOT EXISTS idx_kb_sync_status ON knowledge_base(sync_status);
CREATE INDEX IF NOT EXISTS idx_kb_embedding ON knowledge_base
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ============================================
-- 4. 合规规则表
-- ============================================
CREATE TABLE IF NOT EXISTS compliance_rules (
    id SERIAL PRIMARY KEY,
    word VARCHAR(255) NOT NULL,
    level VARCHAR(10) NOT NULL DEFAULT 'P1',
    -- 'P0' = 违禁词, 'P1' = 敏感词
    category VARCHAR(100) DEFAULT NULL,
    description TEXT DEFAULT NULL,
    industry VARCHAR(100) DEFAULT NULL,
    -- NULL = 通用规则, 非NULL = 行业特殊规则
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cr_level ON compliance_rules(level);
CREATE INDEX IF NOT EXISTS idx_cr_industry ON compliance_rules(industry);

-- ============================================
-- 5. 笔记表
-- ============================================
CREATE TABLE IF NOT EXISTS notes (
    id SERIAL PRIMARY KEY,
    enterprise_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    topic VARCHAR(500),
    title VARCHAR(500),
    article TEXT,
    tags JSONB,
    ai_flavor_score INTEGER,
    compliance_status VARCHAR(50),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    published_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notes_enterprise ON notes(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_notes_platform ON notes(platform);
CREATE INDEX IF NOT EXISTS idx_notes_created ON notes(created_at DESC);

-- ============================================
-- 6. 素材包表
-- ============================================
CREATE TABLE IF NOT EXISTS material_packs (
    id SERIAL PRIMARY KEY,
    enterprise_id VARCHAR(255) NOT NULL,
    brand_name VARCHAR(255),
    product_name VARCHAR(255),
    persona_profile TEXT,
    scene_description TEXT,
    compliance_rules JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 7. 历史标题表（去重用）
-- ============================================
CREATE TABLE IF NOT EXISTS title_history (
    id SERIAL PRIMARY KEY,
    enterprise_id VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,
    title VARCHAR(500) NOT NULL,
    title_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_th_enterprise ON title_history(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_th_hash ON title_history(title_hash);

-- ============================================
-- 8. 审计日志表
-- ============================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) DEFAULT NULL,
    enterprise_id VARCHAR(255) DEFAULT NULL,
    action VARCHAR(50) NOT NULL,
    -- 'create'/'update'/'delete'/'login'/'export'
    resource_type VARCHAR(50) NOT NULL,
    -- 'knowledge_base'/'note'/'template'/'user'
    resource_id VARCHAR(255) DEFAULT NULL,
    details JSONB DEFAULT '{}',
    ip_address VARCHAR(45) DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_al_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_al_enterprise ON audit_logs(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_al_created ON audit_logs(created_at DESC);
