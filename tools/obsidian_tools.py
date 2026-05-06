"""
Obsidian 工具 - Markdown 文件读取、搜索、链接追踪
"""

import os
import re
from pathlib import Path
from typing import Optional
import frontmatter
from crewai.tools import BaseTool
from pydantic import Field


class ObsidianReaderTool(BaseTool):
    """Obsidian Markdown 读取工具"""

    name: str = "obsidian_reader"
    description: str = "读取 Obsidian Markdown 文件并提取内容和元数据"

    def __init__(self, vault_path: Optional[str] = None):
        super().__init__()
        self.vault_path = Path(vault_path) if vault_path else None

    def _run(self, file_path: str) -> dict:
        """
        BaseTool 接口 - 读取 Markdown 文件

        Args:
            file_path: 文件路径（相对于 vault 或绝对路径）

        Returns:
            dict: 包含 content, metadata, links 的字典
        """
        full_path = self._resolve_path(file_path)

        if not full_path.exists():
            return {
                "error": f"File not found: {file_path}",
                "content": "",
                "metadata": {},
                "links": [],
            }

        try:
            post = frontmatter.loads(full_path.read_text(encoding="utf-8"))

            return {
                "content": post.content,
                "metadata": dict(post.metadata),
                "links": self._extract_links(post.content),
                "file_path": str(full_path),
            }

        except Exception as e:
            return {
                "error": str(e),
                "content": "",
                "metadata": {},
                "links": [],
            }

    def _resolve_path(self, file_path: str) -> Path:
        """解析文件路径"""
        if self.vault_path is None:
            return Path(file_path)

        path = Path(file_path)
        if path.is_absolute():
            return path

        return self.vault_path / path

    def _extract_links(self, content: str) -> list[str]:
        """提取 Markdown 中的链接"""
        wiki_links = re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)

        links = []
        links.extend(wiki_links)
        links.extend([link for _, link in md_links if not link.startswith("http")])

        return links

    def read_folder(self, folder_path: str, recursive: bool = True) -> list[dict]:
        """读取文件夹下所有 Markdown 文件"""
        if self.vault_path is None:
            return []

        full_path = self._resolve_path(folder_path)

        if not full_path.exists():
            return []

        pattern = "**/*.md" if recursive else "*.md"
        files = list(full_path.glob(pattern))

        results = []
        for file in files:
            result = self._run(str(file.relative_to(self.vault_path)))
            result["file_path"] = str(file)
            results.append(result)

        return results


class ObsidianSearchTool(BaseTool):
    """Obsidian 搜索工具"""

    name: str = "obsidian_search"
    description: str = "在 Obsidian Vault 中搜索文件"

    def __init__(self, vault_path: Optional[str] = None):
        super().__init__()
        self.vault_path = Path(vault_path) if vault_path else None

    def _run(
        self,
        query: str,
        folder: Optional[str] = None,
        file_type: str = "md",
    ) -> list[dict]:
        """
        BaseTool 接口 - 搜索文件

        Args:
            query: 搜索关键词
            folder: 可选的限定文件夹
            file_type: 文件类型

        Returns:
            list[dict]: 匹配的文件列表
        """
        if self.vault_path is None:
            return []

        search_path = self.vault_path
        if folder:
            search_path = search_path / folder

        pattern = f"**/*.{file_type}"
        files = list(search_path.glob(pattern))

        results = []
        query_lower = query.lower()

        for file in files:
            try:
                content = file.read_text(encoding="utf-8").lower()

                if query_lower in content:
                    line_num = self._find_line_number(content, query_lower)
                    results.append({
                        "file_path": str(file),
                        "relative_path": str(file.relative_to(self.vault_path)),
                        "match_line": line_num,
                    })

            except Exception:
                continue

        return results

    def _find_line_number(self, content: str, query: str) -> int:
        """查找匹配的行号"""
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            if query in line:
                return i
        return 0


class ObsidianLinkTrackerTool(BaseTool):
    """Obsidian 双向链接追踪工具"""

    name: str = "obsidian_link_tracker"
    description: str = "追踪 Obsidian 文件的双向链接关系"

    def __init__(self, vault_path: Optional[str] = None):
        super().__init__()
        self.vault_path = Path(vault_path) if vault_path else None
        self._backlinks_cache: dict[str, list[str]] = {}

    def _run(self, file_path: str) -> dict:
        """
        BaseTool 接口 - 获取文件链接信息

        Args:
            file_path: 文件路径

        Returns:
            dict: 包含 forward_links 和 backlinks 的字典
        """
        if self.vault_path is None:
            return {"forward_links": [], "backlinks": []}

        full_path = self.vault_path / file_path

        if not full_path.exists():
            return {"forward_links": [], "backlinks": []}

        try:
            content = full_path.read_text(encoding="utf-8")
            forward_links = self._extract_wiki_links(content)
            backlinks = self._find_backlinks(file_path)

            return {
                "forward_links": forward_links,
                "backlinks": backlinks,
            }

        except Exception as e:
            return {"forward_links": [], "backlinks": [], "error": str(e)}

    def _extract_wiki_links(self, content: str) -> list[str]:
        """提取 wiki 链接"""
        return re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)

    def _find_backlinks(self, target_file: str) -> list[str]:
        """查找指向目标文件的所有文件"""
        if self.vault_path is None:
            return []

        if target_file in self._backlinks_cache:
            return self._backlinks_cache[target_file]

        backlinks = []
        target_name = Path(target_file).stem

        pattern = "**/*.md"
        files = list(self.vault_path.glob(pattern))

        for file in files:
            if file.name == target_file:
                continue

            try:
                content = file.read_text(encoding="utf-8")
                links = self._extract_wiki_links(content)

                if any(target_name in link for link in links):
                    backlinks.append(str(file.relative_to(self.vault_path)))

            except Exception:
                continue

        self._backlinks_cache[target_file] = backlinks
        return backlinks

    def clear_cache(self):
        """清空 backlinks 缓存"""
        self._backlinks_cache.clear()
