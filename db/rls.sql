-- ============================================
-- 智创笔记 - RLS 策略 + 数据库用户
-- 前置条件：init.sql 已执行
-- ============================================

-- ============================================
-- 辅助函数：获取当前会话上下文
-- ============================================
CREATE OR REPLACE FUNCTION current_user_context()
RETURNS JSONB AS $$
BEGIN
    RETURN JSONB_BUILD_OBJECT(
        'enterprise_id', current_setting('app.enterprise_id', true),
        'is_platform_admin', COALESCE(current_setting('app.is_platform_admin', true), 'false')::boolean,
        'is_agent', COALESCE(current_setting('app.is_agent', true), 'false')::boolean,
        'user_role', current_setting('app.user_role', true)
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 启用 RLS
-- ============================================
ALTER TABLE knowledge_base ENABLE ROW LEVEL SECURITY;
ALTER TABLE enterprises ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE material_packs ENABLE ROW LEVEL SECURITY;
ALTER TABLE title_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 知识库表 RLS 策略（5条核心策略）
-- ============================================

-- 策略1：平台管理员可读写平台级数据
CREATE POLICY kb_platform_admin_all ON knowledge_base
    FOR ALL
    USING (
        data_level = 'platform'
        AND COALESCE(current_setting('app.is_platform_admin', true), 'false')::boolean = true
    );

-- 策略2：租户可读写自己的租户级数据
CREATE POLICY kb_tenant_crud ON knowledge_base
    FOR ALL
    USING (
        data_level = 'tenant'
        AND enterprise_id = current_setting('app.enterprise_id', true)
    );

-- 策略3：租户可读取平台级数据（Agent检索时对租户透明）
CREATE POLICY kb_tenant_read_platform ON knowledge_base
    FOR SELECT
    USING (
        data_level = 'platform'
        AND current_setting('app.enterprise_id', true) IS NOT NULL
        AND COALESCE(current_setting('app.is_platform_admin', true), 'false')::boolean = false
    );

-- 策略4：Agent可写入租户级数据（系统自动检索结果入库）
CREATE POLICY kb_agent_insert ON knowledge_base
    FOR INSERT
    WITH CHECK (
        data_level = 'tenant'
        AND enterprise_id = current_setting('app.enterprise_id', true)
        AND COALESCE(current_setting('app.is_agent', true), 'false')::boolean = true
    );

-- 策略5：Agent可读取平台级数据（用于跨级检索）
CREATE POLICY kb_agent_read_platform ON knowledge_base
    FOR SELECT
    USING (
        data_level = 'platform'
        AND COALESCE(current_setting('app.is_agent', true), 'false')::boolean = true
    );

-- ============================================
-- 企业表 RLS 策略
-- ============================================
CREATE POLICY ent_platform_admin_all ON enterprises
    FOR ALL
    USING (COALESCE(current_setting('app.is_platform_admin', true), 'false')::boolean = true);

CREATE POLICY ent_tenant_read_own ON enterprises
    FOR SELECT
    USING (id = current_setting('app.enterprise_id', true));

-- ============================================
-- 用户表 RLS 策略
-- ============================================
CREATE POLICY usr_platform_admin_all ON users
    FOR ALL
    USING (COALESCE(current_setting('app.is_platform_admin', true), 'false')::boolean = true);

CREATE POLICY usr_tenant_read_own ON users
    FOR SELECT
    USING (enterprise_id = current_setting('app.enterprise_id', true));

-- ============================================
-- 合规规则表 RLS 策略
-- ============================================
CREATE POLICY cr_platform_admin_all ON compliance_rules
    FOR ALL
    USING (COALESCE(current_setting('app.is_platform_admin', true), 'false')::boolean = true);

CREATE POLICY cr_tenant_read ON compliance_rules
    FOR SELECT
    USING (current_setting('app.enterprise_id', true) IS NOT NULL);

-- ============================================
-- 笔记表 RLS 策略
-- ============================================
CREATE POLICY notes_tenant_isolation ON notes
    FOR ALL
    USING (enterprise_id = current_setting('app.enterprise_id', true));

CREATE POLICY notes_platform_admin_all ON notes
    FOR ALL
    USING (COALESCE(current_setting('app.is_platform_admin', true), 'false')::boolean = true);

-- ============================================
-- 素材包表 RLS 策略
-- ============================================
CREATE POLICY mp_tenant_isolation ON material_packs
    FOR ALL
    USING (enterprise_id = current_setting('app.enterprise_id', true));

-- ============================================
-- 历史标题表 RLS 策略
-- ============================================
CREATE POLICY th_tenant_isolation ON title_history
    FOR ALL
    USING (enterprise_id = current_setting('app.enterprise_id', true));

-- ============================================
-- 审计日志表 RLS 策略
-- ============================================
CREATE POLICY al_platform_admin_all ON audit_logs
    FOR ALL
    USING (COALESCE(current_setting('app.is_platform_admin', true), 'false')::boolean = true);

CREATE POLICY al_tenant_read_own ON audit_logs
    FOR SELECT
    USING (enterprise_id = current_setting('app.enterprise_id', true));

-- ============================================
-- 创建数据库用户
-- ============================================

-- 租户用户：通过RLS策略访问
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_tenant') THEN
        CREATE USER app_tenant WITH PASSWORD 'tenant_secure_pass';
    END IF;
END
$$;
GRANT CONNECT ON DATABASE content_agent TO app_tenant;
GRANT USAGE ON SCHEMA public TO app_tenant;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_tenant;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_tenant;

-- 平台管理员用户：绕过RLS（用于管理后台）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_platform') THEN
        CREATE USER app_platform WITH PASSWORD 'platform_secure_pass';
    END IF;
END
$$;
GRANT CONNECT ON DATABASE content_agent TO app_platform;
GRANT USAGE ON SCHEMA public TO app_platform;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_platform;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO app_platform;

-- Agent系统用户：受限操作
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_agent') THEN
        CREATE USER app_agent WITH PASSWORD 'agent_secure_pass';
    END IF;
END
$$;
GRANT CONNECT ON DATABASE content_agent TO app_agent;
GRANT USAGE ON SCHEMA public TO app_agent;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_agent;
GRANT INSERT ON knowledge_base TO app_agent;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_agent;
