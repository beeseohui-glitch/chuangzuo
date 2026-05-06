"""
KnowledgeLoader 测试
"""

import pytest
import tempfile
from pathlib import Path


class TestKnowledgeLoader:
    """知识加载器测试"""

    def setup_method(self):
        """创建临时知识库目录"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.kb_path = Path(self.temp_dir.name)

        # 创建测试分类目录
        health_dir = self.kb_path / "health_product"
        health_dir.mkdir()

        # 创建测试Markdown文件
        (health_dir / "liver_protection.md").write_text(
            "# 护肝片知识\n\n护肝片是一种常见的保健品...\n\n#护肝 #保健品",
            encoding="utf-8"
        )
        (health_dir / "sleep_health.md").write_text(
            "# 睡眠健康\n\n良好的睡眠对健康至关重要...\n\n#睡眠 #健康",
            encoding="utf-8"
        )

    def teardown_method(self):
        self.temp_dir.cleanup()

    def test_load_from_markdown_dir(self):
        """测试从Markdown目录加载"""
        from sync.knowledge_loader import KnowledgeLoader

        loader = KnowledgeLoader(kb_source_dir=str(self.kb_path))
        entries = loader.load_from_markdown_dir("health_product")

        assert len(entries) == 2
        assert all(e.category == "health_product" for e in entries)

    def test_load_from_markdown_dir_empty_category(self):
        """测试加载空分类"""
        from sync.knowledge_loader import KnowledgeLoader

        loader = KnowledgeLoader(kb_source_dir=str(self.kb_path))
        entries = loader.load_from_markdown_dir("nonexistent")

        assert len(entries) == 0

    def test_import_single_file(self):
        """测试导入单个文件"""
        from sync.knowledge_loader import KnowledgeLoader

        loader = KnowledgeLoader(kb_source_dir=str(self.kb_path))
        file_path = self.kb_path / "health_product" / "liver_protection.md"

        entry = loader.import_single_file(str(file_path), "health_product")

        assert entry is not None
        assert entry.category == "health_product"
        assert entry.source == "file"
        assert entry.id.startswith("kb_")

    def test_import_single_file_not_exists(self):
        """测试导入不存在的文件"""
        from sync.knowledge_loader import KnowledgeLoader

        loader = KnowledgeLoader(kb_source_dir=str(self.kb_path))
        entry = loader.import_single_file("nonexistent.md", "test")

        assert entry is None

    def test_get_kb_stats(self):
        """测试获取知识库统计"""
        from sync.knowledge_loader import KnowledgeLoader

        loader = KnowledgeLoader(kb_source_dir=str(self.kb_path))
        stats = loader.get_kb_stats("health_product")

        assert stats["total_files"] == 2
        assert stats["total_size"] > 0

    def test_extract_tags(self):
        """测试标签提取"""
        from sync.knowledge_loader import KnowledgeLoader

        loader = KnowledgeLoader()
        content = "# 标题\n\n内容 #tag1 #tag2 更多内容 #tag3"

        tags = loader._extract_tags(content)

        assert len(tags) == 3
        assert "tag1" in tags
        assert "tag2" in tags
        assert "tag3" in tags

    def test_extract_title(self):
        """测试标题提取"""
        from sync.knowledge_loader import KnowledgeLoader

        loader = KnowledgeLoader()
        content = "# 这是标题\n\n内容"

        title = loader._extract_title(content, "default")

        assert title == "这是标题"

    def test_extract_title_no_header(self):
        """测试无标题头的内容"""
        from sync.knowledge_loader import KnowledgeLoader

        loader = KnowledgeLoader()
        content = "这只是普通文本"

        title = loader._extract_title(content, "default")

        assert title == "default"

    def test_generate_id(self):
        """测试ID生成"""
        from sync.knowledge_loader import KnowledgeLoader

        loader = KnowledgeLoader()
        id1 = loader._generate_id("content1")
        id2 = loader._generate_id("content2")

        assert id1 != id2
        assert id1.startswith("kb_")
        assert id2.startswith("kb_")