"""
合规闭环链：检查 → 修正 → 重新检查

解决"合规检查发现问题但正文 Agent 不知道"的痛点。
利用结构化反馈让正文 Agent 精准修改，而非全文重写。
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ComplianceChain:
    """
    合规闭环链

    用法：
        chain = ComplianceChain(max_rounds=2)
        final_article, report = chain.execute(
            article_agent=article_agent,
            compliance_agent=compliance_agent,
            title="标题",
            article="正文",
            tags=["#标签"],
            brand_taboos=["禁忌词"],
        )
    """

    def __init__(self, max_rounds: int = 2):
        """
        Args:
            max_rounds: 最大修正轮数
        """
        self._max_rounds = max_rounds

    def execute(
        self,
        article_agent,
        compliance_agent,
        title: str,
        article: str,
        tags: list[str],
        brand_taboos: list[str],
    ) -> tuple[str, object]:
        """
        执行合规闭环

        Args:
            article_agent: ArticleAgent 实例
            compliance_agent: ComplianceAgent 实例
            title: 标题
            article: 正文
            tags: 标签列表
            brand_taboos: 品牌禁忌词

        Returns:
            (final_article, final_report): 修正后的正文和最终合规报告
        """
        current_article = article

        for round_idx in range(self._max_rounds):
            logger.info(f"Compliance check round {round_idx + 1}/{self._max_rounds}")

            # 合规检查
            report = compliance_agent.check(
                title=title,
                article=current_article,
                tags=tags,
                brand_taboos=brand_taboos,
            )

            # 没有 P0 问题，通过
            if not report.has_p0_issues:
                logger.info(f"Compliance check passed at round {round_idx + 1}")
                return current_article, report

            # 最后一轮仍不通过，降级返回
            if round_idx == self._max_rounds - 1:
                logger.warning(f"Compliance check still has P0 issues after {self._max_rounds} rounds")
                return current_article, report

            # 结构化修正
            logger.info(f"P0 issues found, generating correction request")
            correction = compliance_agent.generate_correction_request(report)

            # 正文 Agent 精准修改
            note = article_agent.generate_with_correction(
                title=title,
                material_pack={"brand": {"taboos": brand_taboos}},
                correction=correction,
            )

            current_article = note.article
            logger.info(f"Article corrected, length: {len(current_article)}")

        return current_article, report
