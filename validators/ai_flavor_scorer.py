"""
AI Flavor Scorer - AI味多维度评分器
"""

import re
from typing import Optional


class AIFlavorScorer:
    """
    AI味评分器 - 基于规则的多维度评估

    评分维度：
    1. 句式多样性 (0-20分)
    2. 口语化程度 (0-20分)
    3. 结构模式 (0-20分)
    4. 生活细节 (0-20分)
    5. 轻微不完美 (0-20分)
    """

    # 口语化语气词
    COLLOQUIAL_WORDS = [
        "啊", "呀", "哇", "呢", "吧", "嘛", "哦", "哈", "诶", "呃",
        "真的", "其实", "说实话", "说真的", "本来", "当然", "居然",
        "简直", "简直了", "太", "挺", "蛮", "还", "就", "都",
    ]

    # AI工整结构标志
    AI_STRUCTURES = [
        r"首先", r"其次", r"最后",
        r"第一", r"第二", r"第三", r"第四", r"第五",
        r"一方面", r"另一方面",
        r"综上所述",
        r"值得一提的是",
        r"从.+角度",
        r"不得不",
        r"众所周知",
    ]

    # 非正式表达
    INFORMAL_PATTERNS = [
        r"真的.+了",
        r"太.+了吧",
        r"谁懂啊",
        r"救命",
        r"哭死",
        r"绝绝子",
        r"yyds",
        r"绝了",
        r"好家伙",
        r"笑死",
    ]

    def __init__(self):
        self._ai_pattern = re.compile("|".join(self.AI_STRUCTURES))
        self._informal_pattern = re.compile("|".join(self.INFORMAL_PATTERNS), re.IGNORECASE)

    def score(self, text: str) -> int:
        """
        计算AI味评分

        Args:
            text: 待评分文本

        Returns:
            int: 总分 0-100
        """
        if not text:
            return 0

        sentence_score = self._score_sentence_diversity(text)
        colloquial_score = self._score_colloquial_level(text)
        structure_score = self._score_structure_pattern(text)
        detail_score = self._score_life_details(text)
        imperfection_score = self._score_slight_imperfection(text)

        total = (
            sentence_score
            + colloquial_score
            + structure_score
            + detail_score
            + imperfection_score
        )

        return min(100, max(0, total))

    def _score_sentence_diversity(self, text: str) -> int:
        """
        句式多样性评分 (0-20分)

        评估方法：长短句比例、句式类型分布
        """
        sentences = self._split_sentences(text)

        if len(sentences) < 3:
            return 5

        # 计算句子长度标准差
        lengths = [len(s) for s in sentences]
        avg_length = sum(lengths) / len(lengths)

        if avg_length == 0:
            return 0

        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5

        # 标准差越大，句式越多样
        # 理想标准差在 30-80 之间
        if 30 <= std_dev <= 80:
            return 20
        elif 20 <= std_dev < 30 or 80 < std_dev <= 100:
            return 15
        elif 10 <= std_dev < 20 or 100 < std_dev <= 120:
            return 10
        else:
            return 5

    def _score_colloquial_level(self, text: str) -> int:
        """
        口语化程度评分 (0-20分)

        评估方法：语气词密度、口语化表达占比
        """
        colloquial_count = 0
        for word in self.COLLOQUIAL_WORDS:
            colloquial_count += text.count(word)

        # 语气词密度
        density = colloquial_count / max(len(text), 1) * 1000

        if density >= 5:
            return 20
        elif density >= 3:
            return 15
        elif density >= 1:
            return 10
        elif density >= 0.5:
            return 5
        else:
            return 0

    def _score_structure_pattern(self, text: str) -> int:
        """
        结构模式评分 (0-20分)

        评估方法：是否避免工整排比、是否使用非标准段落结构
        """
        # 统计AI工整结构出现次数
        ai_matches = len(self._ai_pattern.findall(text))

        if ai_matches == 0:
            return 20
        elif ai_matches == 1:
            return 15
        elif ai_matches == 2:
            return 10
        elif ai_matches <= 4:
            return 5
        else:
            return 0

    def _score_life_details(self, text: str) -> int:
        """
        生活细节评分 (0-20分)

        评估方法：具体场景描述、感官细节、时间/地点信息
        """
        score = 0

        # 时间信息
        time_patterns = [
            r"早上", r"中午", r"下午", r"晚上", r"半夜",
            r"周一|周二|周三|周四|周五|周六|周日",
            r"周末", r"工作日",
            r"昨天", r"今天", r"明天", r"上周", r"下周",
        ]
        for pattern in time_patterns:
            if re.search(pattern, text):
                score += 3
                break

        # 地点信息
        location_patterns = [
            r"在家里", r"在公司", r"在学校", r"在办公室",
            r"在车上", r"在地铁", r"在公交",
            r"在家", r"出门", r"回家",
        ]
        for pattern in location_patterns:
            if re.search(pattern, text):
                score += 3
                break

        # 感官细节
        sense_patterns = [
            r"闻起来", r"看起来", r"摸起来", r"吃起来",
            r"味道", r"口感", r"颜色", r"质地",
        ]
        for pattern in sense_patterns:
            if re.search(pattern, text):
                score += 3
                break

        # 具体场景
        scene_patterns = [
            r"加班", r"熬夜", r"约会", r"聚会", r"旅游",
            r"健身", r"跑步", r"做饭", r"吃饭",
        ]
        for pattern in scene_patterns:
            if re.search(pattern, text):
                score += 3
                break

        # 情绪表达
        emotion_patterns = [
            r"开心", r"兴奋", r"满足", r"舒服", r"轻松",
            r"焦虑", r"担心", r"烦恼", r"难受",
        ]
        for pattern in emotion_patterns:
            if re.search(pattern, text):
                score += 3
                break

        return min(20, score)

    def _score_slight_imperfection(self, text: str) -> int:
        """
        轻微不完美评分 (0-20分)

        评估方法：是否有口语化省略、非正式表达、情绪化用语
        """
        score = 0

        # 非正式表达
        informal_matches = len(self._informal_pattern.findall(text))
        if informal_matches >= 2:
            score += 10
        elif informal_matches == 1:
            score += 5

        # 感叹句
        exclamation_count = len(re.findall(r"!|！|\?|？", text))
        if exclamation_count >= 3:
            score += 5
        elif exclamation_count >= 1:
            score += 3

        # 口语化省略（主语省略、谓语省略等）
        omission_patterns = [
            r"^真好", r"^太棒", r"^超喜欢",
            r"真的.*啊", r".*就这样.*",
        ]
        for pattern in omission_patterns:
            if re.search(pattern, text):
                score += 3
                break

        return min(20, score)

    def _split_sentences(self, text: str) -> list[str]:
        """拆分句子"""
        sentences = re.split(r"[.。!！?？;；\n]", text)
        return [s.strip() for s in sentences if s.strip()]

    def get_score_breakdown(self, text: str) -> dict:
        """
        获取详细评分分解

        Args:
            text: 待评分文本

        Returns:
            dict: 各维度得分和总分
        """
        return {
            "sentence_diversity": self._score_sentence_diversity(text),
            "colloquial_level": self._score_colloquial_level(text),
            "structure_pattern": self._score_structure_pattern(text),
            "life_details": self._score_life_details(text),
            "slight_imperfection": self._score_slight_imperfection(text),
            "total": self.score(text),
        }


class TextAnalyzer:
    """文本分析工具"""

    @staticmethod
    def count_chinese_chars(text: str) -> int:
        """统计中文字符数"""
        return len(re.findall(r"[一-鿿]", text))

    @staticmethod
    def count_sentences(text: str) -> int:
        """统计句子数"""
        return len(re.split(r"[.。!！?？;；\n]", text))

    @staticmethod
    def extract_keywords(text: str, top_n: int = 10) -> list[str]:
        """提取关键词（简单实现）"""
        # 移除标点和空格
        clean_text = re.sub(r"[^一-鿿]", "", text)

        # 统计字符频率
        char_freq = {}
        for char in clean_text:
            char_freq[char] = char_freq.get(char, 0) + 1

        # 排序
        sorted_chars = sorted(char_freq.items(), key=lambda x: x[1], reverse=True)

        return [char for char, _ in sorted_chars[:top_n]]
