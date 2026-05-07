-- V2.2 迁移：enterprises 表补充租户管理所需字段
-- 执行方式：psql -U agent -d content_agent -f db/migrate_v2.2.sql

ALTER TABLE enterprises ADD COLUMN IF NOT EXISTS expire_at TIMESTAMP DEFAULT NULL;
ALTER TABLE enterprises ADD COLUMN IF NOT EXISTS contact_name VARCHAR(100) DEFAULT NULL;
ALTER TABLE enterprises ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255) DEFAULT NULL;
ALTER TABLE enterprises ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(50) DEFAULT NULL;

-- 为 status 和 plan_type 添加索引（租户管理筛选用）
CREATE INDEX IF NOT EXISTS idx_enterprises_status ON enterprises(status);
CREATE INDEX IF NOT EXISTS idx_enterprises_plan ON enterprises(plan_type);
