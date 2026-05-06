"""
知识库批量导入工具
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime

from sync.obsidian_client import ObsidianClient
from models import KnowledgeEntry


class KnowledgeLoader:
    """知识库批量导入工具"""

    def __init__(
        self,
        obsidian_client: Optional[ObsidianClient] = None,
        kb_source_dir: Optional[str] = None,
    ):
        """
        初始化知识加载器

        Args:
            obsidian_client: Obsidian客户端
            kb_source_dir: 知识库源目录（kb/目录下）
        """
        self.obsidian = obsidian_client or ObsidianClient()
        self.source_dir = Path(kb_source_dir or os.path.join(os.getcwd(), "kb"))

    def load_from_markdown_dir(
        self,
        category: str,
        folder: str = "",
    ) -> list[KnowledgeEntry]:
        """
        从Markdown目录批量导入知识

        Args:
            category: 分类（如 health_product, ai_tech）
            folder: 子文件夹

        Returns:
            导入的知识条目列表
        """
        target_dir = self.source_dir / category / folder

        if not target_dir.exists():
            return []

        entries = []
        for md_file in target_dir.rglob("*.md"):
            entry = self._parse_markdown_file(md_file, category)
            if entry:
                entries.append(entry)

        return entries

    def load_from_obsidian_vault(
        self,
        folder: str = "",
        category: Optional[str] = None,
    ) -> list[KnowledgeEntry]:
        """
        从Obsidian笔记库导入知识

        Args:
            folder: 笔记库子文件夹
            category: 分类（默认使用文件夹名）

        Returns:
            导入的知识条目列表
        """
        notes = self.obsidian.list_notes(folder)
        entries = []

        for note in notes:
            path = note["path"]
            content = self.obsidian.read_note(path)

            if not content:
                continue

            # 从路径提取分类
            note_category = category or self._extract_category_from_path(path)

            entry = KnowledgeEntry(
                id=self._generate_id(content),
                title=self._extract_title(content, note["name"]),
                content=content,
                category=note_category,
                tags=self._extract_tags(content),
                source="obsidian",
                source_url=f"obsidian://{path}",
            )
            entries.append(entry)

        return entries

    def import_single_file(
        self,
        file_path: str,
        category: str,
        title: Optional[str] = None,
    ) -> Optional[KnowledgeEntry]:
        """
        导入单个文件

        Args:
            file_path: 文件路径
            category: 分类
            title: 标题（默认使用文件名）

        Returns:
            导入的知识条目
        """
        path = Path(file_path)

        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        entry = KnowledgeEntry(
            id=self._generate_id(content),
            title=title or path.stem,
            content=content,
            category=category,
            tags=self._extract_tags(content),
            source="file",
            source_url=str(path.absolute()),
        )

        return entry

    def _parse_markdown_file(self, file_path: Path, category: str) -> Optional[KnowledgeEntry]:
        """解析Markdown文件为知识条目"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                return None

            # 提取标题（第一个 # 开头的内容）
            title = self._extract_title(content, file_path.stem)

            # 提取标签
            tags = self._extract_tags(content)

            # 生成ID
            entry_id = self._generate_id(content)

            return KnowledgeEntry(
                id=entry_id,
                title=title,
                content=content,
                category=category,
                tags=tags,
                source="markdown",
                source_url=str(file_path.absolute()),
            )
        except Exception:
            return None

    def _extract_title(self, content: str, default: str) -> str:
        """提取标题"""
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return default

    def _extract_tags(self, content: str) -> list[str]:
        """提取标签"""
        tags = re.findall(r'#([a-zA-Z0-9_/-]+)', content)
        return list(set(tags))

    def _extract_category_from_path(self, path: str) -> str:
        """从路径提取分类"""
        parts = Path(path).parts
        if len(parts) > 1:
            return parts[0]
        return "general"

    def _generate_id(self, content: str) -> str:
        """生成知识条目ID"""
        hash_str = hashlib.md5(content.encode()).hexdigest()[:12]
        return f"kb_{datetime.now().strftime('%Y%m%d')}_{hash_str}"

    def get_kb_stats(self, category: str = "") -> dict:
        """
        获取知识库统计信息

        Args:
            category: 分类，为空则统计全部

        Returns:
            统计信息
        """
        if category:
            target_dir = self.source_dir / category
        else:
            target_dir = self.source_dir

        if not target_dir.exists():
            return {"total_files": 0, "total_size": 0}

        files = list(target_dir.rglob("*.md"))
        total_size = sum(f.stat().st_size for f in files)

        return {
            "total_files": len(files),
            "total_size": total_size,
            "size_mb": round(total_size / 1024 / 1024, 2),
        }