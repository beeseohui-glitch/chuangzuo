"""
Obsidian 客户端 - 封装 Obsidian API 操作
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime


class ObsidianClient:
    """Obsidian 笔记库客户端"""

    def __init__(
        self,
        vault_path: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """
        初始化 Obsidian 客户端

        Args:
            vault_path: 笔记库路径，默认从环境变量读取
            api_key: Obsidian API Key（用于Local REST API插件）
        """
        self.vault_path = Path(vault_path or os.getenv("OBSIDIAN_VAULT_PATH", ""))
        self.api_key = api_key or os.getenv("OBSIDIAN_API_KEY", "")
        self._notes_cache = {}

    def list_notes(self, folder: str = "") -> list[dict]:
        """
        列出笔记文件

        Args:
            folder: 子文件夹路径，为空则列出根目录

        Returns:
            笔记文件列表
        """
        target_path = self.vault_path / folder if folder else self.vault_path

        if not target_path.exists():
            return []

        notes = []
        for f in target_path.rglob("*.md"):
            rel_path = f.relative_to(self.vault_path)
            notes.append({
                "path": str(rel_path),
                "name": f.stem,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "size": f.stat().st_size,
            })

        return notes

    def read_note(self, path: str) -> Optional[str]:
        """
        读取笔记内容

        Args:
            path: 笔记路径

        Returns:
            笔记内容
        """
        file_path = self.vault_path / path

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    def write_note(self, path: str, content: str, auto_create_dirs: bool = True) -> bool:
        """
        写入笔记

        Args:
            path: 笔记路径
            content: 笔记内容
            auto_create_dirs: 是否自动创建父目录

        Returns:
            是否成功
        """
        file_path = self.vault_path / path

        if auto_create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def create_note_from_template(
        self,
        template_name: str,
        output_path: str,
        variables: dict,
    ) -> bool:
        """
        从模板创建笔记

        Args:
            template_name: 模板文件名
            output_path: 输出路径
            variables: 模板变量

        Returns:
            是否成功
        """
        template_path = self.vault_path / "_templates" / template_name

        if not template_path.exists():
            return False

        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template = f.read()

            # 替换模板变量
            content = template
            for key, value in variables.items():
                content = content.replace(f"{{{{{key}}}}}", str(value))

            return self.write_note(output_path, content)
        except Exception:
            return False

    def get_note_metadata(self, path: str) -> Optional[dict]:
        """
        获取笔记元数据

        Args:
            path: 笔记路径

        Returns:
            元数据字典
        """
        file_path = self.vault_path / path

        if not file_path.exists():
            return None

        stat = file_path.stat()
        return {
            "path": path,
            "name": file_path.stem,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "size": stat.st_size,
            "extension": file_path.suffix,
        }

    def search_notes(self, query: str, folder: str = "") -> list[dict]:
        """
        在笔记中搜索内容

        Args:
            query: 搜索关键词
            folder: 搜索文件夹

        Returns:
            匹配的笔记列表
        """
        target_path = self.vault_path / folder if folder else self.vault_path

        if not target_path.exists():
            return []

        results = []
        for f in target_path.rglob("*.md"):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    content = file.read()
                    if query.lower() in content.lower():
                        rel_path = f.relative_to(self.vault_path)
                        results.append({
                            "path": str(rel_path),
                            "name": f.stem,
                            "snippet": self._extract_snippet(content, query),
                        })
            except Exception:
                continue

        return results

    def _extract_snippet(self, content: str, query: str, context_chars: int = 100) -> str:
        """提取搜索关键词周围的片段"""
        lower_content = content.lower()
        lower_query = query.lower()

        pos = lower_content.find(lower_query)
        if pos == -1:
            return content[:context_chars * 2] + "..."

        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(query) + context_chars)

        snippet = content[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def get_all_tags(self) -> list[str]:
        """获取所有笔记中的标签"""
        tags = set()
        notes = self.list_notes()

        for note in notes:
            content = self.read_note(note["path"])
            if content:
                # 简单提取 #tag 格式
                import re
                found_tags = re.findall(r'#([a-zA-Z0-9_/-]+)', content)
                tags.update(found_tags)

        return sorted(list(tags))

    def get_backlinks(self, path: str) -> list[dict]:
        """
        获取指向指定笔记的反向链接

        Args:
            path: 笔记路径

        Returns:
            反向链接列表
        """
        note_name = Path(path).stem
        backlinks = []

        for f in self.vault_path.rglob("*.md"):
            try:
                with open(f, "r", encoding="utf-8") as file:
                    content = file.read()
                    # 查找 [[笔记名]] 格式
                    if f"[[{note_name}]]" in content or f"[[{Path(path).name}]]" in content:
                        rel_path = f.relative_to(self.vault_path)
                        backlinks.append({
                            "path": str(rel_path),
                            "name": f.stem,
                        })
            except Exception:
                continue

        return backlinks

    def calculate_file_hash(self, path: str) -> Optional[str]:
        """计算文件的MD5哈希"""
        file_path = self.vault_path / path

        if not file_path.exists():
            return None

        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return None

    def exists(self, path: str) -> bool:
        """检查笔记是否存在"""
        return (self.vault_path / path).exists()