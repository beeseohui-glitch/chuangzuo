"""
创作链 - 支持双模式

- full:  选题 → 素材 → 标题 → 正文 → 标签 → 合规（数据驱动）
- quick: 素材 → 标题 → 正文 → 标签 → 合规（用户驱动，兼容现有流程）
"""

import logging
from typing import Any, Optional

from agents.agent_chain import AgentChain
from models.agent_message import AgentChainResult

logger = logging.getLogger(__name__)


class CreationChain:
    """
    创作链 - 封装完整的内容创作流程

    用法：
        # 数据驱动模式（含选题）
        chain = CreationChain(mode="full", enterprise_id="ent_001")
        result = chain.execute({"product": "防晒霜", "category": "beauty"})

        # 用户驱动模式（跳过选题，兼容现有流程）
        chain = CreationChain(mode="quick", enterprise_id="ent_001")
        result = chain.execute({"product": "防晒霜", "persona": "25岁女生"})
    """

    def __init__(self, mode: str = "quick", enterprise_id: str = ""):
        """
        Args:
            mode: "full" 或 "quick"
            enterprise_id: 企业 ID
        """
        if mode not in ("full", "quick"):
            raise ValueError(f"Invalid mode: {mode}. Must be 'full' or 'quick'")
        self._mode = mode
        self._enterprise_id = enterprise_id

    def execute(self, input_data: dict) -> AgentChainResult:
        """
        执行创作链

        Args:
            input_data: 创作输入数据
                - product: 产品名称（必需）
                - persona: 人群描述（可选）
                - scene: 场景（可选）
                - category: 行业分类（full 模式必需）
                - brand_name: 品牌名称（可选）

        Returns:
            AgentChainResult: 执行结果
        """
        if self._mode == "full":
            chain = self._build_full_chain()
        else:
            chain = self._build_quick_chain()

        # 注入 enterprise_id
        input_data["enterprise_id"] = self._enterprise_id

        logger.info(f"Starting {self._mode} creation chain for: {input_data.get('product', 'unknown')}")
        return chain.execute(input_data)

    def _build_full_chain(self) -> AgentChain:
        """
        构建完整创作链（数据驱动模式）

        流程：选题 → 素材 → 标题 → 正文 → 标签 → 合规
        """
        chain = AgentChain()

        # Step 0: 选题推荐
        chain.add_step(
            "topic", "generate_topics",
            lambda ctx: {
                "category": ctx.get("category", "health_product"),
                "product": ctx["product"],
                "brand_name": ctx.get("brand_name", ""),
                "target_persona": ctx.get("persona", ""),
                "num_topics": 5,
            },
        )

        # Step 1: 素材检索（使用选题关键词作为语义锚点）
        chain.add_step(
            "material", "search",
            lambda ctx: {
                "product": ctx["product"],
                "scene": ctx.get("scene"),
                "persona": ctx.get("persona"),
                "enterprise_id": ctx.get("enterprise_id", ""),
            },
        )

        # Step 2: 标题生成（使用选题方向）
        chain.add_step(
            "title", "generate",
            lambda ctx: {
                "topic": self._extract_topic_title(ctx),
                "material_pack": self._extract_material_dict(ctx),
            },
        )

        # Step 3: 正文生成
        chain.add_step(
            "article", "generate",
            lambda ctx: {
                "title": self._extract_selected_title(ctx),
                "material_pack": self._extract_material_dict(ctx),
            },
        )

        # Step 4: 标签生成
        chain.add_step(
            "tag", "generate",
            lambda ctx: {
                "article": self._extract_article(ctx),
                "title": self._extract_selected_title(ctx),
                "material_pack": self._extract_material_dict(ctx),
            },
        )

        # Step 5: 合规检查
        chain.add_step(
            "compliance", "check",
            lambda ctx: {
                "title": self._extract_selected_title(ctx),
                "article": self._extract_article(ctx),
                "tags": self._extract_tags(ctx),
                "brand_taboos": self._extract_brand_taboos(ctx),
            },
        )

        # 添加修正循环：合规 -> 正文
        chain.add_correction_loop(check_step=5, fix_step=3, max_retries=2)

        return chain

    def _build_quick_chain(self) -> AgentChain:
        """
        构建快速创作链（用户驱动模式）

        流程：素材 → 标题 → 正文 → 标签 → 合规（跳过选题）
        """
        chain = AgentChain()

        # Step 0: 素材检索
        chain.add_step(
            "material", "search",
            lambda ctx: {
                "product": ctx["product"],
                "scene": ctx.get("scene"),
                "persona": ctx.get("persona"),
                "enterprise_id": ctx.get("enterprise_id", ""),
            },
        )

        # Step 1: 标题生成
        chain.add_step(
            "title", "generate",
            lambda ctx: {
                "topic": ctx["product"],
                "material_pack": self._extract_material_dict(ctx),
            },
        )

        # Step 2: 正文生成
        chain.add_step(
            "article", "generate",
            lambda ctx: {
                "title": self._extract_selected_title(ctx),
                "material_pack": self._extract_material_dict(ctx),
            },
        )

        # Step 3: 标签生成
        chain.add_step(
            "tag", "generate",
            lambda ctx: {
                "article": self._extract_article(ctx),
                "title": self._extract_selected_title(ctx),
                "material_pack": self._extract_material_dict(ctx),
            },
        )

        # Step 4: 合规检查
        chain.add_step(
            "compliance", "check",
            lambda ctx: {
                "title": self._extract_selected_title(ctx),
                "article": self._extract_article(ctx),
                "tags": self._extract_tags(ctx),
                "brand_taboos": self._extract_brand_taboos(ctx),
            },
        )

        # 添加修正循环：合规 -> 正文
        chain.add_correction_loop(check_step=4, fix_step=2, max_retries=2)

        return chain

    # ── 辅助方法：从 context 提取数据 ──────────────────────

    def _extract_topic_title(self, ctx: dict) -> str:
        """从选题结果中提取第一个选题标题"""
        topic_result = ctx.get("step_0") or ctx.get("step_result")
        if topic_result and hasattr(topic_result, 'topics') and topic_result.topics:
            return topic_result.topics[0].title
        return ctx.get("product", "")

    def _extract_material_dict(self, ctx: dict) -> dict:
        """提取素材包 dict（兼容 MaterialPack 对象和 dict）"""
        # 在 full 模式下素材是 step_1，在 quick 模式下是 step_0
        material = ctx.get("step_1") or ctx.get("step_0")
        if material is None:
            return {}
        if hasattr(material, 'model_dump'):
            return material.model_dump(exclude_none=True)
        return material if isinstance(material, dict) else {}

    def _extract_selected_title(self, ctx: dict) -> str:
        """提取标题"""
        title_result = ctx.get("step_result")
        if title_result and hasattr(title_result, 'titles') and title_result.titles:
            return title_result.titles[0].title
        return ctx.get("product", "")

    def _extract_article(self, ctx: dict) -> str:
        """提取正文"""
        article_result = ctx.get("step_result")
        if article_result and hasattr(article_result, 'article'):
            return article_result.article
        return ""

    def _extract_tags(self, ctx: dict) -> list[str]:
        """提取标签"""
        tags_result = ctx.get("step_result")
        if isinstance(tags_result, list):
            return tags_result
        return []

    def _extract_brand_taboos(self, ctx: dict) -> list[str]:
        """提取品牌禁忌词"""
        material = self._extract_material_dict(ctx)
        brand = material.get("brand") or {}
        return brand.get("taboos") or []
