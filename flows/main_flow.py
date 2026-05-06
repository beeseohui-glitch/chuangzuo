"""
主 Flow - 统一调度和路由
"""

from typing import Optional, Literal
from crewai.flow.flow import Flow, listen, start

from config import PlatformType
from models import MaterialPack


class MainFlow(Flow):
    """
    主工作流 - 统一调度

    流程：
    1. route - 意图识别和路由
    2. dispatch - 分发到对应平台工作流
    """

    def __init__(self):
        super().__init__()
        self._platform: Optional[PlatformType] = None
        self._route_result: Optional[dict] = None

    @start()
    def route(self, user_input: dict) -> dict:
        """
        意图识别和路由

        Args:
            user_input: 包含 text, enterprise_id, history

        Returns:
            dict: 路由结果
        """
        text = user_input.get("text", "")
        enterprise_id = user_input.get("enterprise_id")

        # 简单的平台识别
        platform = self._detect_platform(text)

        if platform is None:
            return {
                "needs_clarification": True,
                "question": "请问您想创作哪个平台的内容？小红书/公众号/抖音？",
                "platform": None,
            }

        # 提取关键信息
        product = self._extract_product(text)
        scene = self._extract_scene(text)
        style = self._extract_style(text)

        self._platform = platform
        self._route_result = {
            "platform": platform,
            "product": product,
            "scene": scene,
            "style": style,
            "enterprise_id": enterprise_id,
            "needs_clarification": False,
        }

        return self._route_result

    @listen(route)
    def dispatch(self, route_result: dict) -> dict:
        """
        分发到对应平台工作流

        Args:
            route_result: 路由结果

        Returns:
            dict: 执行结果
        """
        if route_result.get("needs_clarification"):
            return {
                "status": "awaiting_clarification",
                "message": route_result.get("question"),
            }

        platform = route_result.get("platform")

        if platform == PlatformType.XIAOHONGSHU:
            return self._run_xiaohongshu(route_result)
        elif platform == PlatformType.WECHAT_PUBLIC:
            return self._run_wechat_public(route_result)
        elif platform == PlatformType.DOUYIN:
            return self._run_douyin(route_result)
        else:
            return {
                "status": "error",
                "message": f"不支持的平台: {platform}",
            }

    def _run_xiaohongshu(self, route_result: dict) -> dict:
        """运行小红书工作流"""
        from flows.xiaohongshu_flow import XiaohongshuFlow

        flow = XiaohongshuFlow()

        return flow.run({
            "product": route_result.get("product", ""),
            "scene": route_result.get("scene"),
            "persona": None,
            "enterprise_id": route_result.get("enterprise_id"),
        })

    def _run_wechat_public(self, route_result: dict) -> dict:
        """运行公众号工作流（待实现）"""
        return {
            "status": "not_implemented",
            "message": "公众号工作流开发中",
            "platform": "wechat_public",
        }

    def _run_douyin(self, route_result: dict) -> dict:
        """运行抖音工作流（待实现）"""
        return {
            "status": "not_implemented",
            "message": "抖音工作流开发中",
            "platform": "douyin",
        }

    def _detect_platform(self, text: str) -> Optional[PlatformType]:
        """检测目标平台"""
        text_lower = text.lower()

        if any(kw in text_lower for kw in ["小红书", "xhs", "小红"]):
            return PlatformType.XIAOHONGSHU
        elif any(kw in text_lower for kw in ["公众号", "微信", "wechat"]):
            return PlatformType.WECHAT_PUBLIC
        elif any(kw in text_lower for kw in ["抖音", "douyin"]):
            return PlatformType.DOUYIN

        return None

    def _extract_product(self, text: str) -> str:
        """提取产品信息"""
        # 简单实现，后续可接入 NER
        return text.split()[0] if text.split() else ""

    def _extract_scene(self, text: str) -> Optional[str]:
        """提取场景信息"""
        scenes = ["熬夜", "加班", "酒局", "送礼", "日常"]
        for scene in scenes:
            if scene in text:
                return scene
        return None

    def _extract_style(self, text: str) -> Optional[str]:
        """提取风格要求"""
        styles = ["专业", "轻松", "幽默", "严谨"]
        for style in styles:
            if style in text:
                return style
        return None
