"""
智创笔记 - 数据看板
Streamlit 数据分析页面

Step 29: 数据看板界面
"""

import os
import sys
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from agents import AnalyticsAgent, OperationAgent
from models import AnalyticsData, ContentStats, PerformanceMetrics


st.set_page_config(
    page_title="数据看板",
    page_icon="📊",
    layout="wide"
)


def init_session_state():
    """初始化会话状态"""
    if "analytics_agent" not in st.session_state:
        st.session_state.analytics_agent = AnalyticsAgent()

    if "operation_agent" not in st.session_state:
        st.session_state.operation_agent = OperationAgent()

    if "mock_data" not in st.session_state:
        st.session_state.mock_data = generate_mock_data()


def generate_mock_data():
    """生成模拟数据用于展示"""
    return [
        {
            "id": "c001",
            "title": "护肝片种草指南",
            "platform": "xiaohongshu",
            "status": "published",
            "published_at": "2026-05-01 20:00",
            "views": 12500,
            "likes": 890,
            "comments": 156,
            "shares": 67,
            "ai_score": 78,
            "compliance_status": "passed",
        },
        {
            "id": "c002",
            "title": "睡眠健康指南",
            "platform": "xiaohongshu",
            "status": "published",
            "published_at": "2026-05-02 20:00",
            "views": 9800,
            "likes": 720,
            "comments": 98,
            "shares": 45,
            "ai_score": 82,
            "compliance_status": "passed",
        },
        {
            "id": "c003",
            "title": "职场人群护肝指南",
            "platform": "wechat_public",
            "status": "published",
            "published_at": "2026-05-03 08:00",
            "views": 5600,
            "likes": 340,
            "comments": 45,
            "shares": 28,
            "ai_score": 75,
            "compliance_status": "passed",
        },
        {
            "id": "c004",
            "title": "护肝片实测",
            "platform": "xiaohongshu",
            "status": "draft",
            "views": 0,
            "likes": 0,
            "comments": 0,
            "shares": 0,
            "ai_score": 65,
            "compliance_status": "pending",
        },
    ]


def render_overview_tab():
    """渲染概览标签页"""
    st.subheader("📈 内容概况")

    col1, col2, col3, col4 = st.columns(4)

    mock_data = st.session_state.mock_data
    total_content = len(mock_data)
    published = sum(1 for c in mock_data if c.get("status") == "published")
    total_views = sum(c.get("views", 0) for c in mock_data)
    avg_ai_score = sum(c.get("ai_score", 0) for c in mock_data) / len(mock_data) if mock_data else 0

    with col1:
        st.metric("总内容数", total_content)

    with col2:
        st.metric("已发布", published)

    with col3:
        st.metric("总浏览量", f"{total_views:,}")

    with col4:
        st.metric("平均AI评分", f"{avg_ai_score:.1f}")

    st.divider()

    # 平台分布
    st.subheader("📱 平台分布")
    platform_counts = {}
    for c in mock_data:
        platform = c.get("platform", "unknown")
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

    col1, col2 = st.columns(2)
    with col1:
        st.write("**内容数量**")
        for platform, count in platform_counts.items():
            st.write(f"- {platform}: {count}")

    with col2:
        # 简单柱状图
        chart_data = {"平台": list(platform_counts.keys()), "数量": list(platform_counts.values())}
        st.bar_chart(chart_data, x="平台", y="数量")


def render_performance_tab():
    """渲染性能标签页"""
    st.subheader("📊 内容表现")

    mock_data = st.session_state.mock_data
    published_content = [c for c in mock_data if c.get("status") == "published"]

    if not published_content:
        st.info("暂无已发布内容")
        return

    # 内容列表
    for content in published_content:
        with st.expander(f"📄 {content['title']}"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("浏览量", f"{content.get('views', 0):,}")
            with col2:
                st.metric("点赞", f"{content.get('likes', 0):,}")
            with col3:
                st.metric("评论", f"{content.get('comments', 0):,}")
            with col4:
                st.metric("分享", f"{content.get('shares', 0):,}")

            st.write(f"**平台**: {content.get('platform', 'unknown')}")
            st.write(f"**发布时间**: {content.get('published_at', 'unknown')}")
            st.write(f"**AI评分**: {content.get('ai_score', 0)}")
            st.write(f"**合规状态**: {content.get('compliance_status', 'unknown')}")


def render_schedule_tab():
    """渲染发布计划标签页"""
    st.subheader("📅 发布计划")

    # 生成模拟待发布内容
    pending_content = [
        {"id": "p001", "title": "护肝片新品体验", "platform": "xiaohongshu", "priority": "high"},
        {"id": "p002", "title": "熬夜急救指南", "platform": "xiaohongshu", "priority": "medium"},
        {"id": "p003", "title": "职场健康白皮书", "platform": "wechat_public", "priority": "medium"},
    ]

    operation_output = st.session_state.operation_agent.generate_schedule(
        pending_content=pending_content,
        target_platforms=["xiaohongshu", "wechat_public"],
    )

    # 发布计划
    st.write("**即将发布**")
    for item in operation_output.publish_schedule:
        priority_emoji = "🔴" if item.priority == "high" else ("🟡" if item.priority == "medium" else "🟢")
        st.write(f"{priority_emoji} [{item.platform}] {item.title} - {item.scheduled_time}")

    st.divider()

    # 策略建议
    st.write("**策略建议**")
    for rec in operation_output.strategy_recommendations:
        st.write(f"- {rec}")

    st.divider()

    # 内容矩阵
    st.write("**内容矩阵**")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("周发布总量", operation_output.content_matrix.get("total_weekly", 0))
    with col2:
        st.metric("小红书", operation_output.content_matrix.get("xiaohongshu_count", 0))
    with col3:
        st.metric("公众号", operation_output.content_matrix.get("wechat_public_count", 0))


def render_recommendations_tab():
    """渲染优化建议标签页"""
    st.subheader("💡 优化建议")

    mock_data = st.session_state.mock_data

    # 生成分析报告
    analytics_output = st.session_state.analytics_agent.generate_report(
        period_start="2026-05-01",
        period_end="2026-05-04",
        content_data=mock_data,
    )

    if analytics_output.recommendations:
        for rec in analytics_output.recommendations:
            st.write(f"- {rec}")
    else:
        st.info("暂无优化建议，数据表现良好")

    st.divider()

    # AI评分分布
    st.write("**AI评分分布**")
    ai_scores = [c.get("ai_score", 0) for c in mock_data]
    if ai_scores:
        avg_score = sum(ai_scores) / len(ai_scores)
        below_70 = sum(1 for s in ai_scores if s < 70)
        above_80 = sum(1 for s in ai_scores if s >= 80)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("平均AI评分", f"{avg_score:.1f}")
        with col2:
            st.metric("低于70分", below_70)
        with col3:
            st.metric("80分以上", above_80)


def render_analytics_tab():
    """渲染分析标签页"""
    st.subheader("📈 运营分析")

    mock_data = st.session_state.mock_data

    # 计算统计数据
    total_views = sum(c.get("views", 0) for c in mock_data)
    total_engagement = sum(
        c.get("likes", 0) + c.get("comments", 0) + c.get("shares", 0)
        for c in mock_data
    )
    engagement_rate = total_engagement / total_views if total_views > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("总曝光", f"{total_views:,}")
    with col2:
        st.metric("总互动", f"{total_engagement:,}")
    with col3:
        st.metric("互动率", f"{engagement_rate * 100:.2f}%")

    st.divider()

    # 趋势图（模拟数据）
    st.write("**周趋势**")
    trend_data = {
        "日期": ["05-01", "05-02", "05-03", "05-04"],
        "浏览量": [12500, 9800, 5600, 8200],
    }
    st.line_chart(trend_data, x="日期", y="浏览量")


def main():
    init_session_state()

    st.title("📊 智创笔记数据看板")

    # 侧边栏
    st.sidebar.title("导航")
    page = st.sidebar.radio(
        "选择页面",
        ["📈 概览", "📊 表现", "📅 计划", "💡 建议", "📈 分析"]
    )

    if page == "📈 概览":
        render_overview_tab()
    elif page == "📊 表现":
        render_performance_tab()
    elif page == "📅 计划":
        render_schedule_tab()
    elif page == "💡 建议":
        render_recommendations_tab()
    elif page == "📈 分析":
        render_analytics_tab()


if __name__ == "__main__":
    main()