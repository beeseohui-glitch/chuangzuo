"""
向量工具测试 - pgvector 写入、检索、RLS 验证
依赖：数据库已初始化（db/init.sql + db/rls.sql + db/seed.sql）
"""

import time
import pytest

from models.local_embedding import LocalEmbedding
from tools.vector_tools import VectorStoreTool
from config.vector_config import VectorStoreConfig


@pytest.fixture(scope="module")
def embedding():
    """Embedding 模型 fixture"""
    return LocalEmbedding()


@pytest.fixture(scope="module")
def vector_config():
    """数据库配置 fixture（超级用户，用于写入）"""
    return VectorStoreConfig(
        host="localhost",
        port=5432,
        database="content_agent",
        user="agent",
        password="your_password_here",
    )


@pytest.fixture(scope="module")
def rls_config():
    """RLS 测试配置（非超级用户，RLS 生效）"""
    return VectorStoreConfig(
        host="localhost",
        port=5432,
        database="content_agent",
        user="app_tenant",
        password="tenant_secure_pass",
    )


@pytest.fixture(scope="module")
def vector_tool(vector_config):
    """VectorStoreTool fixture（超级用户，用于写入和管理）"""
    tool = VectorStoreTool(config=vector_config)
    yield tool
    tool.close()


@pytest.fixture(scope="module")
def rls_tool(rls_config):
    """RLS 测试工具（非超级用户，RLS 生效）"""
    tool = VectorStoreTool(config=rls_config)
    yield tool
    tool.close()


class TestVectorInsert:
    """向量写入测试"""

    def test_insert_tenant_knowledge(self, vector_tool: VectorStoreTool, embedding: LocalEmbedding):
        """写入一条租户级知识到 pgvector"""
        text = "护肝片的主要成分是水飞蓟素，适合经常熬夜的人群"
        vec = embedding.encode(text)

        record_id = vector_tool.insert(
            title="护肝片成分科普",
            content=text,
            embedding=vec,
            data_level="tenant",
            enterprise_id="ent_demo",
            category="product_knowledge",
            tags=["护肝片", "成分", "科普"],
            created_by="test",
        )

        assert record_id is not None
        assert isinstance(record_id, int)

    def test_insert_platform_knowledge(self, vector_tool: VectorStoreTool, embedding: LocalEmbedding):
        """写入一条平台级知识"""
        text = "广告法规定禁止使用绝对化用语，如最好、第一、唯一等"
        vec = embedding.encode(text)

        record_id = vector_tool.insert(
            title="广告法绝对化用语规范",
            content=text,
            embedding=vec,
            data_level="platform",
            platform_category="public",
            category="compliance",
            tags=["广告法", "合规"],
            created_by="test",
        )

        assert record_id is not None


class TestVectorSearch:
    """向量检索测试"""

    def test_search_returns_results(self, vector_tool: VectorStoreTool, embedding: LocalEmbedding):
        """检索验证能返回结果"""
        query = "护肝片的功效和成分"
        query_vec = embedding.encode(query)

        # 平台管理员身份检索（可看全部平台级数据）
        vector_tool.set_session_context(is_platform_admin=True)

        start = time.time()
        results = vector_tool.search(
            embedding=query_vec,
            top_k=5,
            data_level="platform",
        )
        elapsed = time.time() - start

        assert len(results) > 0, "应返回检索结果"
        assert elapsed < 2.0, f"检索延迟应 < 2s，实际 {elapsed:.2f}s"

        # 验证返回字段
        r = results[0]
        assert "id" in r
        assert "title" in r
        assert "content" in r
        assert "similarity" in r
        assert isinstance(r["similarity"], float)
        assert r["similarity"] > 0

    def test_search_with_filters(self, vector_tool: VectorStoreTool, embedding: LocalEmbedding):
        """带过滤条件的检索"""
        query = "保健品选题"
        query_vec = embedding.encode(query)

        vector_tool.set_session_context(is_platform_admin=True)

        results = vector_tool.search(
            embedding=query_vec,
            top_k=10,
            data_level="platform",
            platform_category="industry",
        )

        for r in results:
            assert r["data_level"] == "platform"
            assert r["platform_category"] == "industry"

    def test_search_similarity_order(self, vector_tool: VectorStoreTool, embedding: LocalEmbedding):
        """结果按相似度降序排列"""
        query = "AI工具推荐"
        query_vec = embedding.encode(query)

        vector_tool.set_session_context(is_platform_admin=True)

        results = vector_tool.search(
            embedding=query_vec,
            top_k=10,
            data_level="platform",
        )

        if len(results) >= 2:
            for i in range(len(results) - 1):
                assert results[i]["similarity"] >= results[i + 1]["similarity"], \
                    "结果应按相似度降序排列"


class TestRLS:
    """RLS 策略验证（使用 app_tenant 用户，RLS 生效）"""

    def test_tenant_sees_own_and_platform(self, rls_tool: VectorStoreTool, embedding: LocalEmbedding):
        """租户身份检索：只能看到自己企业 + 平台级数据"""
        query = "护肝片"
        query_vec = embedding.encode(query)

        # 租户身份：ent_demo
        rls_tool.set_session_context(
            enterprise_id="ent_demo",
            is_platform_admin=False,
            is_agent=False,
            user_role="tenant_admin",
        )

        results = rls_tool.search(embedding=query_vec, top_k=50)

        for r in results:
            if r["data_level"] == "tenant":
                assert r["enterprise_id"] == "ent_demo", \
                    f"租户不应看到其他企业的数据，enterprise_id={r['enterprise_id']}"
            elif r["data_level"] == "platform":
                pass  # 平台级数据租户可读
            else:
                pytest.fail(f"Unexpected data_level: {r['data_level']}")

    def test_tenant_cannot_see_other_tenant(self, rls_tool: VectorStoreTool, embedding: LocalEmbedding):
        """租户不能看到其他租户的数据"""
        query = "护肝片"
        query_vec = embedding.encode(query)

        # 用 ent_test 身份检索
        rls_tool.set_session_context(
            enterprise_id="ent_test",
            is_platform_admin=False,
            user_role="tenant_admin",
        )

        results = rls_tool.search(embedding=query_vec, top_k=50)

        for r in results:
            if r["data_level"] == "tenant":
                assert r["enterprise_id"] == "ent_test", \
                    "租户不应看到 ent_demo 的数据"

    def test_platform_admin_sees_all_platform(self, rls_tool: VectorStoreTool, embedding: LocalEmbedding):
        """平台管理员可看到全部平台级数据（通过 app_tenant 设置上下文）"""
        query = "合规"
        query_vec = embedding.encode(query)

        rls_tool.set_session_context(is_platform_admin=True)

        results = rls_tool.search(
            embedding=query_vec,
            top_k=50,
            data_level="platform",
        )

        assert len(results) > 0, "平台管理员应能看到平台级数据"

    def test_agent_cross_level_search(self, rls_tool: VectorStoreTool, embedding: LocalEmbedding):
        """Agent 跨级检索：可读取平台级数据"""
        query = "选题推荐"
        query_vec = embedding.encode(query)

        rls_tool.set_session_context(
            enterprise_id="ent_demo",
            is_agent=True,
        )

        results = rls_tool.search(
            embedding=query_vec,
            top_k=10,
            data_level="platform",
        )

        assert len(results) > 0, "Agent 应能检索平台级数据"

    def test_count_by_level(self, rls_tool: VectorStoreTool):
        """统计各级别数据量"""
        rls_tool.set_session_context(is_platform_admin=True)

        platform_count = rls_tool.count(data_level="platform")
        assert platform_count > 0, "应有平台级数据"

        tenant_count = rls_tool.count(data_level="tenant")
        assert tenant_count >= 0
