"""
智创笔记 - 知识库管理界面
Streamlit 知识管理页面

Step 24: Streamlit知识管理界面
"""

import os
import sys
import streamlit as st
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from sync import ObsidianClient, KnowledgeLoader
from models import KnowledgeEntry, KBMetadata, SearchResult


st.set_page_config(
    page_title="知识库管理",
    page_icon="📚",
    layout="wide"
)


def init_session_state():
    """初始化会话状态"""
    if "obsidian_client" not in st.session_state:
        st.session_state.obsidian_client = ObsidianClient(
            vault_path=os.getenv("OBSIDIAN_VAULT_PATH", "")
        )

    if "knowledge_loader" not in st.session_state:
        st.session_state.knowledge_loader = KnowledgeLoader(
            obsidian_client=st.session_state.obsidian_client
        )

    if "entries" not in st.session_state:
        st.session_state.entries = []

    if "current_view" not in st.session_state:
        st.session_state.current_view = "home"


def load_knowledge_base():
    """加载知识库"""
    loader = st.session_state.knowledge_loader

    # 从Markdown目录加载
    health_entries = loader.load_from_markdown_dir("health_product")
    ai_entries = loader.load_from_markdown_dir("ai_industry")

    st.session_state.entries = health_entries + ai_entries


def render_home():
    """渲染首页"""
    st.title("📚 知识库管理")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("总条目数", len(st.session_state.entries))

    with col2:
        categories = set(e.category for e in st.session_state.entries)
        st.metric("分类数", len(categories))

    with col3:
        tags = set()
        for e in st.session_state.entries:
            tags.update(e.tags)
        st.metric("标签数", len(tags))

    st.divider()

    # 搜索框
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input("搜索知识库", placeholder="输入关键词搜索...")
    with search_col2:
        st.write("")
        search_button = st.button("🔍 搜索", use_container_width=True)

    if search_query or search_button:
        filtered_entries = [
            e for e in st.session_state.entries
            if search_query.lower() in e.title.lower() or search_query.lower() in e.content.lower()
        ]
        st.write(f"找到 {len(filtered_entries)} 条结果")

        for entry in filtered_entries:
            with st.expander(f"📄 {entry.title}"):
                st.write(f"**分类**: {entry.category}")
                st.write(f"**标签**: {', '.join(entry.tags) if entry.tags else '无'}")
                st.write(f"**来源**: {entry.source}")
                st.text_area("内容", entry.content[:500] + "..." if len(entry.content) > 500 else entry.content, height=200, disabled=True, key=f"content_{entry.id}")

    st.divider()

    # 知识库统计
    st.subheader("📊 知识库统计")

    kb_stats = st.session_state.knowledge_loader.get_kb_stats()
    st.write(f"健康产品知识库文件数: {kb_stats.get('total_files', 0)}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🧪 健康产品")
        health_entries = [e for e in st.session_state.entries if e.category == "health_product"]
        for e in health_entries:
            st.write(f"- {e.title}")

    with col2:
        st.subheader("🤖 AI行业")
        ai_entries = [e for e in st.session_state.entries if e.category == "ai_industry"]
        for e in ai_entries:
            st.write(f"- {e.title}")


def render_import():
    """渲染导入页面"""
    st.title("📥 导入知识")

    upload_col1, upload_col2 = st.columns([2, 1])

    with upload_col1:
        uploaded_file = st.file_uploader("上传Markdown文件", type=["md", "txt"])

    with upload_col2:
        category = st.selectbox("选择分类", ["health_product", "ai_industry", "other"])

    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        st.text_area("文件预览", content[:500] + "..." if len(content) > 500 else content, height=200, disabled=True)

        if st.button("导入到知识库", use_container_width=True):
            st.success(f"文件 {uploaded_file.name} 已导入到 {category}")


def render_settings():
    """渲染设置页面"""
    st.title("⚙️ 设置")

    st.subheader("Obsidian 连接")
    vault_path = st.text_input("笔记库路径", value=os.getenv("OBSIDIAN_VAULT_PATH", ""))
    api_key = st.text_input("API Key", value=os.getenv("OBSIDIAN_API_KEY", ""), type="password")

    if st.button("保存设置"):
        st.success("设置已保存")


def main():
    init_session_state()
    load_knowledge_base()

    # 侧边栏导航
    st.sidebar.title("导航")
    page = st.sidebar.radio("选择页面", ["🏠 首页", "📥 导入", "⚙️ 设置"])

    if page == "🏠 首页":
        render_home()
    elif page == "📥 导入":
        render_import()
    elif page == "⚙️ 设置":
        render_settings()


if __name__ == "__main__":
    main()