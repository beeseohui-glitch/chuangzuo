"""
素材检索 Tool - 三层知识库检索 + 素材包组装

检索优先级：
  第一层：企业私有库（data_level='tenant', enterprise_id=当前企业）- 最精准
  第二层：行业知识库（data_level='platform', platform_category='industry'）- 补充
  第三层：公共知识库（data_level='platform', platform_category='public'）- 兜底

对租户透明：不暴露数据来源层级
"""

import json
import time
import hashlib
import logging
from typing import Optional
from collections import defaultdict

from crewai.tools import BaseTool
from pydantic import Field

from models import (
    MaterialPack,
    BrandInfo,
    ProductInfo,
    PersonaInfo,
    SceneInfo,
    ComplianceRules,
)
from tools.vector_tools import VectorStoreTool
from tools.embedding_tools import LocalEmbeddingTool

logger = logging.getLogger(__name__)

# 缓存 TTL（秒）
CACHE_TTL = 1800  # 30 分钟

from tools.cache_tools import TTLCache


class MaterialSearchTool(BaseTool):
    """素材检索工具 - 三层知识库语义检索"""

    name: str = "material_search"
    description: str = (
        "从知识库检索素材并组装素材包。"
        "输入产品名称、场景和人群描述，返回结构化的品牌/产品/人群/场景/合规信息。"
    )

    def __init__(
        self,
        vector_store: Optional[VectorStoreTool] = None,
        embedding_tool: Optional[LocalEmbeddingTool] = None,
    ):
        super().__init__()
        self._vector_store = vector_store
        self._embedding_tool = embedding_tool
        self._cache = TTLCache(CACHE_TTL)

    @property
    def vector_store(self) -> VectorStoreTool:
        if self._vector_store is None:
            self._vector_store = VectorStoreTool()
        return self._vector_store

    @property
    def embedding_tool(self) -> LocalEmbeddingTool:
        if self._embedding_tool is None:
            self._embedding_tool = LocalEmbeddingTool()
        return self._embedding_tool

    def _run(
        self,
        product: str,
        scene: str = "",
        persona: str = "",
        enterprise_id: str = "",
    ) -> str:
        """
        BaseTool 接口 - 检索素材

        Args:
            product: 产品名称
            scene: 场景描述
            persona: 人群描述
            enterprise_id: 企业ID

        Returns:
            str: JSON 格式的素材包
        """
        pack = self.search(
            product=product,
            scene=scene,
            persona=persona,
            enterprise_id=enterprise_id,
        )
        return pack.model_dump_json(indent=2)

    def search(
        self,
        product: str,
        scene: str = "",
        persona: str = "",
        enterprise_id: str = "",
    ) -> MaterialPack:
        """
        检索素材并组装素材包

        Args:
            product: 产品名称
            scene: 场景描述
            persona: 人群描述
            enterprise_id: 企业ID

        Returns:
            MaterialPack: 结构化素材包
        """
        # 构建检索查询
        query_parts = [product]
        if scene:
            query_parts.append(scene)
        if persona:
            query_parts.append(persona)
        query = " ".join(query_parts)

        # 检查缓存
        cache_key = self._cache_key(query, enterprise_id)
        cached = self._get_cached(cache_key)
        if cached is not None:
            logger.info(f"Material search cache hit for: {query[:30]}")
            return cached

        # 编码查询
        query_embedding = self.embedding_tool.encode(query)[0].tolist()

        # 三层检索
        all_results = []

        # 第一层：企业私有库（最精准）
        if enterprise_id:
            self.vector_store.set_session_context(
                enterprise_id=enterprise_id,
                is_agent=True,
            )
            private_results = self.vector_store.search(
                embedding=query_embedding,
                top_k=10,
                data_level="tenant",
                enterprise_id=enterprise_id,
                min_similarity=0.3,
            )
            all_results.extend(private_results)
            logger.info(f"Private KB: {len(private_results)} results")

        # 第二层：行业知识库（补充）
        self.vector_store.set_session_context(is_agent=True)
        industry_results = self.vector_store.search(
            embedding=query_embedding,
            top_k=5,
            data_level="platform",
            platform_category="industry",
            min_similarity=0.3,
        )
        all_results.extend(industry_results)
        logger.info(f"Industry KB: {len(industry_results)} results")

        # 第三层：公共知识库（兜底）
        public_results = self.vector_store.search(
            embedding=query_embedding,
            top_k=5,
            data_level="platform",
            platform_category="public",
            min_similarity=0.3,
        )
        all_results.extend(public_results)
        logger.info(f"Public KB: {len(public_results)} results")

        # 清除会话上下文
        try:
            self.vector_store.clear_session_context()
        except Exception:
            pass

        # 组装素材包
        pack = self._assemble_material_pack(all_results, product)

        # 写入缓存
        self._put_cache(cache_key, pack)

        return pack

    def _assemble_material_pack(
        self,
        results: list[dict],
        product_name: str,
    ) -> MaterialPack:
        """
        组装素材包 - 对租户透明，不暴露数据来源层级

        Args:
            results: 所有检索结果（已按相似度排序）
            product_name: 产品名称

        Returns:
            MaterialPack: 结构化素材包
        """
        # 按 category 分组
        by_category = defaultdict(list)
        for r in results:
            cat = r.get("category", "unknown")
            by_category[cat].append(r)

        # 提取品牌信息
        brand = self._extract_brand(by_category, product_name)

        # 提取产品信息
        product = self._extract_product(by_category, product_name)

        # 提取人群画像
        persona = self._extract_persona(by_category)

        # 提取场景信息
        scenes = self._extract_scenes(by_category)

        # 提取合规规则
        compliance = self._extract_compliance(by_category)

        # 检查缺失字段
        missing_fields = []
        if not brand or not brand.name:
            missing_fields.append("brand")
        if not product or not product.name:
            missing_fields.append("product")
        if not persona or not persona.profile:
            missing_fields.append("persona")

        return MaterialPack(
            brand=brand,
            product=product,
            persona=persona,
            scene=scenes,
            compliance=compliance,
            missing_fields=missing_fields,
        )

    def _extract_brand(self, by_category: dict, product_name: str) -> Optional[BrandInfo]:
        """提取品牌信息"""
        import re

        # 优先从 brand 类别提取
        brand_entries = by_category.get("brand", [])
        # 如果没有 brand 类别，从所有结果中查找品牌相关信息
        if not brand_entries:
            all_entries = []
            for entries in by_category.values():
                all_entries.extend(entries)
            brand_entries = [
                e for e in all_entries
                if any(kw in e.get("title", "") + e.get("content", "")
                       for kw in ["品牌", "公司", "企业", "调性"])
            ]

        if not brand_entries:
            # 用产品名作为品牌名的兜底
            brand_name = product_name.split("-")[0] if "-" in product_name else product_name
            return BrandInfo(name=brand_name, tone=[], taboos=[])

        content = brand_entries[0].get("content", "")
        title = brand_entries[0].get("title", "")
        # 尝试从标题或内容中提取品牌名
        brand_name = title.replace("品牌介绍", "").replace("品牌调性", "").strip()
        if not brand_name:
            match = re.search(r'(\S{2,8})(?:品牌|公司|企业)', content)
            if match:
                brand_name = match.group(1)
            else:
                brand_name = product_name.split("-")[0] if "-" in product_name else product_name

        # 提取调性词和禁忌词
        tone = []
        taboos = []
        for entry in brand_entries:
            tags = entry.get("tags", [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []
            tone.extend([t for t in tags if "调性" in t or "风格" in t])
            content_lower = entry.get("content", "").lower()
            if "禁忌" in content_lower or "不能" in content_lower:
                taboos.append(entry.get("content", "")[:50])

        return BrandInfo(
            name=brand_name,
            tone=tone[:5],
            taboos=taboos[:3],
        )

    def _extract_product(self, by_category: dict, product_name: str) -> Optional[ProductInfo]:
        """提取产品信息"""
        # 优先从 product 类别提取
        product_entries = by_category.get("product", [])
        # 如果没有 product 类别，从所有结果中查找产品相关信息
        if not product_entries:
            all_entries = []
            for entries in by_category.values():
                all_entries.extend(entries)
            product_entries = [
                e for e in all_entries
                if any(kw in e.get("title", "") + e.get("content", "")
                       for kw in ["产品", "卖点", "成分", "功效", "特点"])
            ]

        if not product_entries:
            # 用产品名作为兜底
            return ProductInfo(
                name=product_name,
                selling_points=["待补充"],
                ingredients=[],
                evidence={},
            )

        selling_points = []
        ingredients = []
        evidence = {}

        for entry in product_entries:
            content = entry.get("content", "")
            tags = entry.get("tags", [])
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except json.JSONDecodeError:
                    tags = []

            # 提取卖点
            for tag in tags:
                if "卖点" in tag or "优势" in tag:
                    selling_points.append(tag)

            # 从内容中提取关键信息
            lines = content.split("\n")
            for line in lines:
                line = line.strip()
                if any(kw in line for kw in ["卖点", "优势", "特点"]):
                    selling_points.append(line)
                if any(kw in line for kw in ["成分", "原料", "配方"]):
                    ingredients.append(line)

        return ProductInfo(
            name=product_name,
            selling_points=selling_points[:5] or ["待补充"],
            ingredients=ingredients[:5],
            evidence=evidence,
        )

    def _extract_persona(self, by_category: dict) -> Optional[PersonaInfo]:
        """提取人群画像"""
        persona_entries = by_category.get("persona", []) + by_category.get("pain_point", [])
        # 如果没有 persona 类别，从所有结果中查找人群相关信息
        if not persona_entries:
            all_entries = []
            for entries in by_category.values():
                all_entries.extend(entries)
            persona_entries = [
                e for e in all_entries
                if any(kw in e.get("title", "") + e.get("content", "")
                       for kw in ["人群", "画像", "用户", "目标", "痛点", "需求"])
            ]

        if not persona_entries:
            return PersonaInfo(profile="待补充", pain_points=[], language_style="")

        profile = persona_entries[0].get("content", "")[:200]
        pain_points = []
        language_style = ""

        for entry in persona_entries:
            content = entry.get("content", "")
            if "痛点" in content:
                lines = content.split("\n")
                for line in lines:
                    if "痛点" in line:
                        pain_points.append(line.strip())

        return PersonaInfo(
            profile=profile,
            pain_points=pain_points[:3],
            language_style=language_style,
        )

    def _extract_scenes(self, by_category: dict) -> list[SceneInfo]:
        """提取场景信息"""
        scene_entries = by_category.get("scene", [])
        # 如果没有 scene 类别，从所有结果中查找场景相关信息
        if not scene_entries:
            all_entries = []
            for entries in by_category.values():
                all_entries.extend(entries)
            scene_entries = [
                e for e in all_entries
                if any(kw in e.get("title", "") + e.get("content", "")
                       for kw in ["场景", "使用", "用法", "时机"])
            ]

        if not scene_entries:
            return [SceneInfo(description="待补充", usage_method="")]

        scenes = []
        for entry in scene_entries[:3]:
            content = entry.get("content", "")
            scenes.append(SceneInfo(
                description=content[:100],
                usage_method="",
            ))
        return scenes

    def _extract_compliance(self, by_category: dict) -> Optional[ComplianceRules]:
        """提取合规规则"""
        compliance_entries = by_category.get("compliance", []) + by_category.get("rule", [])
        # 如果没有 compliance 类别，从所有结果中查找合规相关信息
        if not compliance_entries:
            all_entries = []
            for entries in by_category.values():
                all_entries.extend(entries)
            compliance_entries = [
                e for e in all_entries
                if any(kw in e.get("title", "") + e.get("content", "")
                       for kw in ["合规", "规则", "禁忌", "禁止", "注意"])
            ]

        if not compliance_entries:
            return ComplianceRules(rules=[], forbidden_groups=[])

        rules = []
        forbidden_groups = []
        for entry in compliance_entries:
            content = entry.get("content", "")
            rules.append(content[:100])
            if "禁忌" in content or "禁止" in content:
                forbidden_groups.append(content[:50])

        return ComplianceRules(
            rules=rules[:5],
            forbidden_groups=forbidden_groups[:3],
        )

    def _cache_key(self, query: str, enterprise_id: str) -> str:
        """生成缓存 key"""
        content = f"{query}:{enterprise_id}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cached(self, key: str) -> Optional[MaterialPack]:
        """获取缓存"""
        data = self._cache.get(key)
        if data is not None:
            return MaterialPack(**data)
        return None

    def _put_cache(self, key: str, pack: MaterialPack):
        """写入缓存"""
        self._cache.put(key, pack.model_dump())

    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
