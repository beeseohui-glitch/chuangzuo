"""
内容适配器 - 将内容适配到不同平台
"""

from typing import Optional
from models import NoteOutput, WechatArticle, PublicAccountContent, DouyinScript, DouyinVideo, DouyinContent, MultiPlatformContent


class ContentAdapter:
    """内容适配器 - 将内容适配到不同平台"""

    def adapt_for_xiaohongshu(self, source: NoteOutput) -> dict:
        """
        将内容适配为小红书格式

        Args:
            source: 源内容（NoteOutput）

        Returns:
            小红书适配后的内容字典
        """
        return {
            "title": source.title[:20] if len(source.title) > 20 else source.title,
            "content": source.article,
            "tags": source.tags[:10],
            "platform": "xiaohongshu",
            "ai_flavor_score": source.ai_flavor_score,
        }

    def adapt_for_wechat_public(self, source: NoteOutput, target_length: str = "medium") -> PublicAccountContent:
        """
        将内容适配为公众号格式

        Args:
            source: 源内容（NoteOutput）
            target_length: 目标长度 short/medium/long

        Returns:
            PublicAccountContent: 公众号内容
        """
        # 转换标签为公众号标签
        tags = source.tags[:5] if source.tags else []

        wechat_article = WechatArticle(
            title=source.title,
            subtitle=None,
            content=self._convert_to_html(source.article),
            summary=source.article[:200] + "..." if len(source.article) > 200 else source.article,
            tags=tags,
        )

        return PublicAccountContent(
            article=wechat_article,
            platform="wechat_public",
            ai_flavor_score=source.ai_flavor_score,
            compliance_status="passed",
        )

    def adapt_for_douyin(self, source: NoteOutput, duration_seconds: int = 60) -> DouyinScript:
        """
        将内容适配为抖音脚本格式

        Args:
            source: 源内容（NoteOutput）
            duration_seconds: 目标时长

        Returns:
            DouyinScript: 抖音脚本
        """
        # 提取前3秒钩子
        hooks = self._extract_hooks(source.article)

        # 转换为主体脚本
        script_content = self._convert_to_timestamps(source.article, duration_seconds)

        return DouyinScript(
            title=source.title[:30] if len(source.title) > 30 else source.title,
            hooks=hooks,
            script_content=script_content,
            cta="关注我获取更多干货",
            duration_seconds=duration_seconds,
            visual_suggestions=self._generate_visual_suggestions(source),
        )

    def _convert_to_html(self, text: str) -> str:
        """将文本转换为HTML格式"""
        paragraphs = text.split("\n\n")
        html_parts = []

        for p in paragraphs:
            if p.strip():
                html_parts.append(f"<p>{p.strip()}</p>")

        return "".join(html_parts)

    def _extract_hooks(self, article: str) -> str:
        """从文章中提取开头钩子"""
        first_para = article.split("\n\n")[0] if article else ""

        if len(first_para) > 50:
            return first_para[:50] + "..."
        return first_para

    def _convert_to_timestamps(self, article: str, total_seconds: int) -> str:
        """将文章转换为带时间戳的脚本"""
        sentences = article.split("。")
        total_sentences = len(sentences)

        if total_sentences == 0:
            return "0s - 内容为空"

        seconds_per_sentence = total_seconds / max(total_sentences, 1)
        script_parts = []

        for i, sentence in enumerate(sentences[:10]):  # 限制10个时间戳
            timestamp = int(i * seconds_per_sentence)
            script_parts.append(f"[{timestamp}s] {sentence.strip()}")

        return "\n".join(script_parts)

    def _generate_visual_suggestions(self, source: NoteOutput) -> list[str]:
        """生成画面建议"""
        suggestions = []

        # 基于内容生成建议
        if "护肝" in source.title or "护肝" in source.article:
            suggestions.append("产品特写镜头")
            suggestions.append("熬夜场景再现")

        if "健康" in source.title or "健康" in source.article:
            suggestions.append("生活场景切换")
            suggestions.append("健康元素图标")

        # 默认建议
        if not suggestions:
            suggestions = [
                "开场悬念画面",
                "产品展示",
                "使用场景",
                "结尾行动号召",
            ]

        return suggestions

    def create_multi_platform_content(self, source: NoteOutput) -> MultiPlatformContent:
        """
        创建跨平台内容

        Args:
            source: 源内容（NoteOutput）

        Returns:
            MultiPlatformContent: 跨平台内容
        """
        return MultiPlatformContent(
            xiaohongshu_content=self.adapt_for_xiaohongshu(source),
            wechat_public_content=self.adapt_for_wechat_public(source),
            douyin_content=None,  # 抖音需要单独处理
            source_material_id=source.metadata.get("material_id", ""),
        )