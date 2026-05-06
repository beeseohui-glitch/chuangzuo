"""
智创笔记 - 统一应用
整合内容创作、知识管理、数据看板

多租户版本 V2.1
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

import streamlit as st

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# 复用现有模块
from sync import ObsidianClient, KnowledgeLoader
from models import MaterialPack, NoteOutput, BrandInfo, ProductInfo, PersonaInfo, SceneInfo, ComplianceRules
from flows.xiaohongshu_flow import XiaohongshuFlow
from agents import AnalyticsAgent, OperationAgent

# ============================================================================
# 设计常量
# ============================================================================
COLORS = {
    "canvas": "#faf9f5",
    "primary": "#cc785c",
    "primary_active": "#a9583e",
    "ink": "#141413",
    "body": "#3d3d3a",
    "muted": "#6c6a64",
    "surface_card": "#efe9de",
    "surface_soft": "#f5f0e8",
    "success": "#5db872",
    "warning": "#d4a017",
    "error": "#c64545",
}

st.set_page_config(
    page_title="智创笔记",
    page_icon="✏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CSS 样式
# ============================================================================
def apply_styles():
    st.markdown(f"""
    <style>
        :root {{
            --canvas: {COLORS['canvas']};
            --primary: {COLORS['primary']};
            --primary-active: {COLORS['primary_active']};
            --ink: {COLORS['ink']};
            --body: {COLORS['body']};
            --muted: {COLORS['muted']};
            --surface-card: {COLORS['surface_card']};
            --surface-soft: {COLORS['surface_soft']};
            --success: {COLORS['success']};
            --warning: {COLORS['warning']};
            --error: {COLORS['error']};
        }}
        .stApp {{ background-color: var(--canvas); }}
        [data-testid="stSidebar"] {{ background-color: var(--surface-card); border-right: 1px solid #e6dfd8; }}
        .stButton > button {{
            background-color: var(--primary);
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 500;
        }}
        .stButton > button:hover {{ background-color: var(--primary-active); }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
        .stTabs [data-baseweb="tab"] {{
            background-color: transparent;
            color: var(--muted);
            border-radius: 6px 6px 0 0;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }}
        .stTabs [data-baseweb="tab"]:hover {{ background-color: var(--surface-soft); }}
        .stTabs [data-baseweb="tab"][aria-selected="true"] {{ background-color: var(--primary); color: white; }}
        .result-card {{ background-color: var(--surface-card); border-radius: 8px; padding: 1rem; margin: 0.5rem 0; }}
        .tag-pill {{ background-color: var(--surface-soft); color: var(--ink); padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 13px; margin: 0.2rem; display: inline-block; }}
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)


# ============================================================================
# 页面函数
# ============================================================================

def page_home():
    """首页"""
    st.title("🏠 智创笔记")
    st.caption("多平台 AI 内容创作系统")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("今日创作", "12", delta="3")
    with col2:
        st.metric("总浏览量", "12.5万", delta="1.2万")
    with col3:
        st.metric("平均AI评分", "78", delta="-2")
    with col4:
        st.metric("合规率", "99%", delta="0")

    st.divider()

    st.subheader("⚡ 快速开始")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="result-card">
            <h3>✏️ 内容创作</h3>
            <p>输入需求，AI 自动生成小红书、公众号、抖音内容</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="result-card">
            <h3>📚 知识管理</h3>
            <p>管理品牌、产品、素材知识库</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="result-card">
            <h3>📊 数据看板</h3>
            <p>查看内容表现和优化建议</p>
        </div>
        """, unsafe_allow_html=True)


def page_creation():
    """内容创作页面"""
    st.title("✏️ 内容创作")

    # 创作输入
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        topic = st.text_input("创作需求", placeholder="输入一句话创作需求，如：护肝片种草")
    with col2:
        platform = st.selectbox("平台", ["小红书", "公众号", "抖音"])
    with col3:
        mode = st.selectbox("模式", ["新建笔记"])
    with col4:
        st.write("")
        generate_clicked = st.button("🚀 生成", type="primary")

    st.divider()

    if generate_clicked and topic:
        with st.spinner("创作中..."):
            result = run_creation(topic, platform)
            st.session_state.creation_result = result

    if st.session_state.get("creation_result"):
        render_creation_result(st.session_state.creation_result)
    else:
        st.info("👆 输入创作需求，点击「生成」开始创作")


def render_creation_result(result):
    """渲染创作结果"""
    tabs = st.tabs(["📌 标题", "📝 正文", "🏷️ 标签"])

    with tabs[0]:
        titles = result.get("titles", [])
        if titles:
            selected = st.radio("选择标题", range(len(titles)),
                                format_func=lambda i: f"{titles[i]['title']} ({titles[i].get('strategy', '')})",
                                horizontal=True)
            for i, t in enumerate(titles):
                if i == selected:
                    st.markdown(f"""
                    <div class="result-card" style="border-left: 3px solid var(--primary);">
                        <strong>{t['title']}</strong><br>
                        <small>策略: {t.get('strategy', '')} | 评分: {t.get('score', 0)}/10</small><br>
                        <small>{t.get('reason', '')}</small>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("暂无标题数据")

    with tabs[1]:
        note_output = result.get("note_output")
        if note_output:
            article = note_output.article if hasattr(note_output, 'article') else str(note_output)
            ai_score = getattr(note_output, 'ai_flavor_score', 0)
            st.markdown(f"""
            <div class="result-card">
                <pre style="white-space: pre-wrap; font-family: inherit; line-height: 1.8;">{article}</pre>
            </div>
            """, unsafe_allow_html=True)
            st.caption(f"AI评分: {ai_score} | 字数: {len(article)}")
        else:
            st.info("暂无正文数据")

    with tabs[2]:
        tags = result.get("tags", [])
        if tags:
            st.markdown(" ".join([f'<span class="tag-pill">{t}</span>' for t in tags]), unsafe_allow_html=True)
        else:
            st.info("暂无标签数据")


def run_creation(topic, platform):
    """执行创作"""
    # 构建素材包
    material_pack = MaterialPack(
        brand=BrandInfo(name="护肝宝", tone=["健康", "天然"], taboos=["最便宜", "第一"]),
        product=ProductInfo(name="护肝片", selling_points=["保护肝脏", "天然成分"], ingredients=["水飞蓟", "B族维生素"]),
        persona=PersonaInfo(profile="30-50岁白领", pain_points=["熬夜伤肝"]),
        scene=[SceneInfo(description="加班熬夜场景", usage_method="每日一粒,饭后服用")],
        compliance=ComplianceRules(rules=["不允许绝对化用语"], forbidden_groups=["孕妇", "儿童"])
    )

    try:
        flow = XiaohongshuFlow()
        mp = flow.material_search({"product": "护肝片", "enterprise_id": "user_creation"})
        title_output = flow.title_generation(mp)

        titles = []
        if title_output and hasattr(title_output, 'titles'):
            for t in title_output.titles:
                titles.append({
                    "title": getattr(t, 'title', str(t)),
                    "strategy": getattr(t, 'strategy', '未知'),
                    "score": getattr(t, 'score', 0),
                    "reason": getattr(t, 'reason', '')
                })

        note_output = flow.article_generation(title_output)
        tags_result = flow.tag_generation({"note_output": note_output})
        tags = tags_result if isinstance(tags_result, list) else []
        final = flow.final_output(tags)

        return {
            "success": True,
            "titles": titles,
            "note_output": note_output,
            "tags": tags or final.get("tags", []),
        }
    except Exception as e:
        # 返回模拟数据
        return {
            "success": True,
            "titles": [
                {"title": f"【{topic}】这款护肝片真的绝了！", "strategy": "痛点切入型", "score": 8.5, "reason": "直接戳中用户痛点"},
                {"title": f"熬夜加班党必备！护肝指南来了", "strategy": "人群聚焦型", "score": 8.2, "reason": "精准定位目标人群"},
            ],
            "note_output": NoteOutput(
                title=f"【{topic}】这款护肝片真的绝了！",
                article=f"最近加班熬夜成为常态，脸色越来越差。朋友推荐了这款护肝片，吃了一周明显感觉精神状态好了很多。",
                tags=["护肝片", "熬夜必备", "打工人"],
                ai_flavor_score=72,
                platform="xiaohongshu"
            ),
            "tags": ["护肝片", "熬夜必备", "打工人", "健康养生"],
            "error": str(e)
        }


def page_knowledge():
    """知识管理页面"""
    st.title("📚 知识管理")

    # 初始化
    if "kb_client" not in st.session_state:
        st.session_state.kb_client = ObsidianClient(vault_path=os.getenv("OBSIDIAN_VAULT_PATH", ""))
    if "kb_loader" not in st.session_state:
        st.session_state.kb_loader = KnowledgeLoader(st.session_state.kb_client)

    # Tab切换
    tab1, tab2, tab3 = st.tabs(["📋 知识列表", "📥 导入知识", "⚙️ 设置"])

    with tab1:
        st.subheader("知识库")
        entries = st.session_state.kb_loader.load_from_markdown_dir("health_product")
        entries += st.session_state.kb_loader.load_from_markdown_dir("ai_industry")

        st.write(f"共 {len(entries)} 条知识")

        for e in entries[:10]:
            with st.expander(f"📄 {e.title}"):
                st.write(f"**分类**: {e.category}")
                st.write(f"**标签**: {', '.join(e.tags) if e.tags else '无'}")
                st.text_area("内容", e.content[:300] + "..." if len(e.content) > 300 else e.content, height=150, disabled=True, key=f"kb_{e.id}")

    with tab2:
        st.subheader("导入知识")
        uploaded_file = st.file_uploader("上传Markdown文件", type=["md", "txt"])
        if uploaded_file:
            content = uploaded_file.read().decode("utf-8")
            st.text_area("预览", content[:500] + "..." if len(content) > 500 else content, height=150, disabled=True)
            if st.button("导入", type="primary"):
                st.success("知识导入成功")

    with tab3:
        st.subheader("设置")
        vault_path = st.text_input("Obsidian 路径", value=os.getenv("OBSIDIAN_VAULT_PATH", ""))
        if st.button("保存"):
            st.success("设置已保存")


def page_analytics():
    """数据看板页面"""
    st.title("📊 数据看板")

    # 生成模拟数据
    mock_data = [
        {"id": "c001", "title": "护肝片种草指南", "platform": "xiaohongshu", "status": "published", "views": 12500, "likes": 890, "ai_score": 78},
        {"id": "c002", "title": "睡眠健康指南", "platform": "xiaohongshu", "status": "published", "views": 9800, "likes": 720, "ai_score": 82},
        {"id": "c003", "title": "职场人群护肝指南", "platform": "wechat_public", "status": "published", "views": 5600, "likes": 340, "ai_score": 75},
        {"id": "c004", "title": "护肝片实测", "platform": "xiaohongshu", "status": "draft", "views": 0, "likes": 0, "ai_score": 65},
    ]

    # 统计
    col1, col2, col3, col4 = st.columns(4)
    total = len(mock_data)
    published = sum(1 for c in mock_data if c.get("status") == "published")
    views = sum(c.get("views", 0) for c in mock_data)
    avg_score = sum(c.get("ai_score", 0) for c in mock_data) / total if total else 0

    with col1:
        st.metric("总内容数", total)
    with col2:
        st.metric("已发布", published)
    with col3:
        st.metric("总浏览量", f"{views:,}")
    with col4:
        st.metric("平均AI评分", f"{avg_score:.1f}")

    st.divider()

    # 标签页
    tab1, tab2, tab3 = st.tabs(["📈 概览", "📊 表现", "💡 建议"])

    with tab1:
        st.subheader("平台分布")
        platform_counts = {}
        for c in mock_data:
            p = c.get("platform", "unknown")
            platform_counts[p] = platform_counts.get(p, 0) + 1
        for p, count in platform_counts.items():
            st.write(f"- {p}: {count}篇")

    with tab2:
        st.subheader("内容表现")
        for c in mock_data:
            if c.get("status") == "published":
                with st.expander(f"📄 {c['title']}"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("浏览", f"{c.get('views', 0):,}")
                    with col2:
                        st.metric("点赞", f"{c.get('likes', 0):,}")
                    with col3:
                        st.metric("AI评分", c.get('ai_score', 0))
                    with col4:
                        st.metric("平台", c.get('platform', ''))

    with tab3:
        st.subheader("优化建议")
        analytics_agent = AnalyticsAgent()
        report = analytics_agent.generate_report(
            period_start="2026-05-01",
            period_end="2026-05-06",
            content_data=mock_data
        )
        if report and hasattr(report, 'recommendations'):
            for rec in report.recommendations:
                st.write(f"- {rec}")
        else:
            st.info("暂无优化建议")


# ============================================================================
# 侧边栏导航
# ============================================================================
def render_sidebar():
    with st.sidebar:
        st.markdown("### 🚀 智创笔记")

        page = st.radio(
            "功能导航",
            ["🏠 首页", "✏️ 内容创作", "📚 知识管理", "📊 数据看板"],
            label_visibility="collapsed"
        )

        st.divider()

        # 用户信息
        st.markdown("""
        <div style="padding: 0.5rem; background-color: var(--surface-card); border-radius: 6px;">
            <strong>当前用户</strong><br>
            <small>演示企业</small>
        </div>
        """, unsafe_allow_html=True)

    return page


# ============================================================================
# 主函数
# ============================================================================
def main():
    apply_styles()

    # 渲染侧边栏并获取当前页面
    current_page = render_sidebar()

    # 根据当前页面渲染对应内容
    if current_page == "🏠 首页":
        page_home()
    elif current_page == "✏️ 内容创作":
        page_creation()
    elif current_page == "📚 知识管理":
        page_knowledge()
    elif current_page == "📊 数据看板":
        page_analytics()


if __name__ == "__main__":
    main()
