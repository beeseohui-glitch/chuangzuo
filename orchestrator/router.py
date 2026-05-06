"""
路由器 - 根据平台路由到对应工作流
"""

from typing import Optional
from enum import Enum


class Platform(str, Enum):
    """支持的平台"""
    XIAOHONGSHU = "xiaohongshu"
    OFFICIAL_ACCOUNT = "official_account"
    DOUYIN = "douyin"
    WEIBO = "weibo"
    VIDEO = "video"
    UNSPECIFIED = "unspecified"


class Router:
    """路由器"""

    PLATFORM_FLOW_MAP = {
        Platform.XIAOHONGSHU: "xiaohongshu_flow",
        Platform.OFFICIAL_ACCOUNT: "official_account_flow",
        Platform.DOUYIN: "douyin_flow",
        Platform.WEIBO: "weibo_flow",
        Platform.VIDEO: "video_flow",
    }

    @classmethod
    def route(cls, platform: str) -> str:
        """
        根据平台名称路由到对应Flow

        Args:
            platform: 平台名称

        Returns:
            str: Flow名称，未知平台返回空字符串
        """
        platform_lower = platform.lower().strip()

        for p in Platform:
            if p.value in platform_lower or platform_lower in p.value:
                return cls.PLATFORM_FLOW_MAP.get(p, "")

        return ""

    @classmethod
    def get_platforms(cls) -> list[str]:
        """获取所有支持的平台"""
        return [p.value for p in Platform if p != Platform.UNSPECIFIED]
