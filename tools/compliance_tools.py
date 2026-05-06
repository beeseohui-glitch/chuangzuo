"""
Compliance 工具 - 敏感词检测和合规检查
"""

import re
from typing import Optional
from crewai.tools import BaseTool
from pydantic import Field

from config import XiaohongshuConfig, PlatformType


class ComplianceCheckTool(BaseTool):
    """合规检查工具 - 检测敏感词和违禁内容"""

    name: str = "compliance_check"
    description: str = "检查内容是否包含违禁词和合规问题"

    def __init__(self, config: Optional[XiaohongshuConfig] = None):
        super().__init__()
        self._compliance_config = config or XiaohongshuConfig()
        self._prohibited_patterns = self._compile_patterns()

    def _compile_patterns(self):
        """编译违禁词正则表达式"""
        patterns = {}

        # 广告法违禁词
        absolute_words = [
            "最", "第一", "顶级", "绝对", "100%", "全网", "独家", "首发",
            "最好", "最强", "无敌", "完美", "极致", "绝无仅有", "独一无二",
            "nex", "首", "之最", "极致",
        ]

        # 医疗用语
        medical_words = [
            "治疗", "治愈", "疗效", "疗效最好", "药到病除", "根治",
            "预防疾病", "治疗疾病", "消炎", "止痛", "退烧", "降压",
            "减肥", "增肥", "美白", "祛斑", "祛痘", "生发",
        ]

        patterns["absolute"] = self._build_pattern(absolute_words)
        patterns["medical"] = self._build_pattern(medical_words)
        patterns["prohibited"] = self._build_pattern(self._compliance_config.prohibited_words)

        return patterns

    def _build_pattern(self, words: list[str]) -> re.Pattern:
        """构建词组正则"""
        escaped = [re.escape(w) for w in words]
        return re.compile("|".join(escaped))

    def _run(
        self,
        text: str,
        platform: str = "xiaohongshu",
        check_type: str = "all",
    ) -> dict:
        """
        BaseTool 接口 - 检查文本合规性

        Args:
            text: 待检查文本
            platform: 平台类型
            check_type: 检查类型 all/absolute/medical/prohibited

        Returns:
            dict: 检查结果
        """
        issues = []

        if check_type in ("all", "absolute"):
            issues.extend(self._check_pattern(text, "absolute", "绝对化用语"))

        if check_type in ("all", "medical"):
            issues.extend(self._check_pattern(text, "medical", "医疗用语"))

        if check_type in ("all", "prohibited"):
            issues.extend(self._check_pattern(text, "prohibited", "违禁词"))

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "issue_count": len(issues),
        }

    def _check_pattern(self, text: str, pattern_type: str, category: str) -> list[dict]:
        """检查指定类型的违禁词"""
        issues = []
        matches = self._prohibited_patterns[pattern_type].finditer(text)

        for match in matches:
            issues.append({
                "word": match.group(),
                "category": category,
                "position": match.start(),
                "context": text[max(0, match.start()-10):match.end()+10],
            })

        return issues

    def check_title(self, title: str) -> dict:
        """检查标题"""
        result = self._run(title)
        result["title_length"] = len(title)
        result["in_range"] = (
            self.config.min_title_length <= len(title) <= self.config.max_title_length
        )
        return result

    def check_article(self, article: str) -> dict:
        """检查正文"""
        result = self._run(article)
        result["word_count"] = len(article)
        result["in_range"] = (
            self.config.min_article_length <= len(article) <= self.config.max_article_length
        )
        return result

    def check_tags(self, tags: list[str]) -> dict:
        """检查标签"""
        issues = []

        for tag in tags:
            if not tag.startswith("#"):
                issues.append({
                    "tag": tag,
                    "issue": "标签必须以 # 开头",
                })

        result = {
            "passed": len(issues) == 0,
            "issues": issues,
            "tag_count": len(tags),
            "in_range": len(tags) <= self.config.max_tags,
        }

        return result

    def batch_check(self, texts: list[str]) -> list[dict]:
        """批量检查"""
        return [self._run(text) for text in texts]


class ProhibitedWordDetector:
    """违禁词检测器 - 基于规则的简单实现"""

    # 保健品行业特殊违禁词
    HEALTHCARE_PROHIBITED = [
        "特效", "神效", "奇效", "灵丹", "妙药", "偏方", "秘方",
        "增高", "壮阳", "滋阴", "补肾", "活血", "化瘀",
    ]

    # 通用违禁词
    GENERAL_PROHIBITED = [
        "最", "第一", "顶级", "绝对", "100%", "全网", "独家", "首发",
    ]

    def __init__(self):
        self._patterns = None

    @property
    def patterns(self) -> re.Pattern:
        if self._patterns is None:
            all_words = self.HEALTHCARE_PROHIBITED + self.GENERAL_PROHIBITED
            escaped = [re.escape(w) for w in all_words]
            self._patterns = re.compile("|".join(escaped))
        return self._patterns

    def detect(self, text: str) -> list[str]:
        """检测违禁词"""
        matches = self.patterns.finditer(text)
        return [m.group() for m in matches]

    def has_prohibited(self, text: str) -> bool:
        """检查是否含违禁词"""
        return bool(self.patterns.search(text))
