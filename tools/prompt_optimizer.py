"""
Prompt优化工具 - 去AI味/Prompt迭代
"""

from typing import Optional
import re

from validators.ai_flavor_scorer import AIFlavorScorer


class PromptOptimizer:
    """Prompt优化器"""

    def __init__(self):
        # 复用 AIFlavorScorer 的 AI 结构模式列表作为权威来源
        self._ai_patterns = AIFlavorScorer.AI_STRUCTURES

        self._formal_patterns = [
            r"具有",
            r"进行",
            r"关于",
            r"对于",
            r"通过",
            r"因此",
            r"然而",
            r"但是",
        ]

    def remove_ai_flavor(self, text: str) -> str:
        """
        去除AI味

        Args:
            text: 输入文本

        Returns:
            去除AI味后的文本
        """
        result = text

        # 替换AI开头模式
        for pattern in self._ai_patterns:
            result = re.sub(pattern, "", result)

        # 替换正式书面语
        for pattern in self._formal_patterns:
            result = re.sub(pattern, "", result)

        # 清理多余空格
        result = re.sub(r"\s+", " ", result).strip()

        return result

    def make_more_conversational(self, text: str) -> str:
        """
        使文本更口语化

        Args:
            text: 输入文本

        Returns:
            口语化后的文本
        """
        result = text

        # 添加语气词
        conversational_phrases = [
            (r"需要注意的是", "对了，提醒一下"),
            (r"实际上", "说实话"),
            (r"可能", "说不定"),
            (r"非常", "特别"),
            (r"比较", "有点"),
            (r"帮助", "帮"),
        ]

        for pattern, replacement in conversational_phrases:
            result = re.sub(pattern, replacement, result)

        return result

    def add_emoji_as节奏(self, text: str, max_emoji: int = 5) -> str:
        """
        添加emoji作为节奏标记（不堆砌）

        Args:
            text: 输入文本
            max_emoji: 最大emoji数量

        Returns:
            添加emoji后的文本
        """
        # 只在关键位置添加emoji
        emoji_map = {
            "痛点": "😣",
            "发现": "👀",
            "体验": "✨",
            "推荐": "👍",
            "重要": "❗",
        }

        result = text
        emoji_count = 0

        for keyword, emoji in emoji_map.items():
            if emoji_count >= max_emoji:
                break
            if keyword in result:
                # 只在第一次出现时添加
                result = result.replace(keyword, f"{emoji}{keyword}", 1)
                emoji_count += 1

        return result

    def optimize_for_platform(self, text: str, platform: str) -> str:
        """
        针对平台优化文本

        Args:
            text: 输入文本
            platform: 平台 xiaohongshu/wechat_public/douyin

        Returns:
            优化后的文本
        """
        result = text

        if platform == "xiaohongshu":
            # 小红书风格：口语化、emoji、简短
            result = self.make_more_conversational(result)
            result = self.remove_ai_flavor(result)
            # 限制长度
            if len(result) > 500:
                result = result[:500] + "..."

        elif platform == "wechat_public":
            # 公众号风格：正式但不失亲和
            result = self.remove_ai_flavor(result)
            # 保持一定结构

        elif platform == "douyin":
            # 抖音风格：短平快、吸引眼球
            result = self.remove_ai_flavor(result)
            if len(result) > 200:
                result = result[:200] + "..."

        return result

    def analyze_ai_score(self, text: str) -> dict:
        """
        分析文本的AI味程度

        Args:
            text: 输入文本

        Returns:
            分析结果字典
        """
        score = 100
        reasons = []

        # 检查AI开头模式
        for pattern in self._ai_patterns:
            if re.search(pattern, text):
                score -= 10
                reasons.append(f"包含AI模式: {pattern}")

        # 检查正式书面语
        formal_count = 0
        for pattern in self._formal_patterns:
            formal_count += len(re.findall(pattern, text))

        if formal_count > 5:
            score -= formal_count * 2
            reasons.append(f"书面语过多: {formal_count}处")

        # 检查句式复杂度
        if len(text) > 300:
            sentences = text.split("。")
            avg_length = sum(len(s) for s in sentences) / len(sentences) if sentences else 0
            if avg_length > 50:
                score -= 10
                reasons.append("句子过长")

        score = max(0, min(100, score))

        return {
            "score": score,
            "reasons": reasons,
            "length": len(text),
            "is_acceptable": score >= 70,
        }

    def suggest_improvements(self, text: str) -> list[str]:
        """
        建议改进点

        Args:
            text: 输入文本

        Returns:
            改进建议列表
        """
        suggestions = []

        # AI模式检测
        for pattern in self._ai_patterns:
            if re.search(pattern, text):
                suggestions.append(f"移除AI开头模式: '{pattern}'")
                break

        # 句子长度检查
        sentences = text.split("。")
        long_sentences = [s for s in sentences if len(s) > 50]
        if long_sentences:
            suggestions.append("拆分过长句子，每句控制在50字以内")

        # 口语化建议
        has_formal = any(re.search(p, text) for p in self._formal_patterns)
        if has_formal:
            suggestions.append("使用更口语化的表达替代书面语")

        # Emoji建议
        if "emoji" not in text.lower() and len(text) > 200:
            suggestions.append("适量添加emoji作为节奏标记")

        if not suggestions:
            suggestions.append("文本质量良好，保持当前风格")

        return suggestions