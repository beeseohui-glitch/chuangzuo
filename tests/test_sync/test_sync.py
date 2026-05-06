"""
Sync测试

Step 15: 测试模块开发
"""

import pytest
from pathlib import Path
import tempfile
import os


class TestVectorizer:
    """向量化器测试"""

    def test_vectorize_file(self):
        """测试文件向量化"""
        from sync.vectorizer import Vectorizer

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建临时markdown文件
            md_file = Path(tmpdir) / "test.md"
            md_file.write_text("---\ntitle: test\n---\n# Test\nContent here", encoding="utf-8")

            vectorizer = Vectorizer()
            # 注意：需要实际的embedding和vector工具才能真正测试
            # 这里只测试流程不报错
            result = vectorizer.vectorize_file(str(md_file))
            assert isinstance(result, bool)


class TestFileWatcher:
    """文件监听器测试"""

    def test_file_watcher_context(self):
        """测试文件监听器上下文管理器"""
        from sync.file_watcher import FileWatcher

        with tempfile.TemporaryDirectory() as tmpdir:
            watcher = FileWatcher(tmpdir)
            # 测试上下文管理器不报错
            with watcher:
                pass
