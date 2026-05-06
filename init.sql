-- PostgreSQL + pgvector 初始化脚本
-- Phase 1: 基础表结构

-- 启用pgvector扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 企业知识库表
CREATE TABLE IF NOT EXISTS knowledge_base (
    id SERIAL PRIMARY KEY,
    enterprise_id VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1024),
    file_path VARCHAR(500),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 向量索引 (IVFFlat for MVP, HNSW for production)
CREATE INDEX IF NOT EXISTS idx_kb_enterprise ON knowledge_base(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_kb_embedding ON knowledge_base USING ivfflat(embedding vector_cosine_ops) WITH (lists = 100);

-- 历史标题表 (去重用)
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

-- 笔记表
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

-- 素材包表
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

-- Row Level Security (RLS) 配置
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE title_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE material_packs ENABLE ROW LEVEL SECURITY;

-- RLS策略
CREATE POLICY tenant_isolation ON knowledge_base USING (enterprise_id = current_setting('app.enterprise_id', true));
CREATE POLICY tenant_isolation ON title_history USING (enterprise_id = current_setting('app.enterprise_id', true));
CREATE POLICY tenant_isolation ON notes USING (enterprise_id = current_setting('app.enterprise_id', true));
CREATE POLICY tenant_isolation ON material_packs USING (enterprise_id = current_setting('app.enterprise_id', true));

-- 性能监控视图
CREATE OR REPLACE VIEW vector_search_stats AS
SELECT
    schemaname,
    tablename,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size
FROM pg_stat_user_indexes
WHERE tablename IN ('knowledge_base', 'title_history', 'notes');

-- 备份视图
CREATE OR REPLACE VIEW notes_backup_view AS
SELECT
    id,
    enterprise_id,
    platform,
    title,
    created_at,
    published_at,
    ai_flavor_score
FROM notes
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '7 days';
