"""
ObsidianClient 测试
"""

import pytest
import tempfile
from pathlib import Path


class TestObsidianClient:
    """Obsidian客户端测试"""

    def setup_method(self):
        """创建临时笔记库"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = self.temp_dir.name

        # 创建测试笔记
        self.test_note_path = Path(self.vault_path) / "test_note.md"
        self.test_note_path.write_text("# Test Note\n\nContent here #test", encoding="utf-8")

        # 创建子文件夹
        sub_dir = Path(self.vault_path) / "subfolder"
        sub_dir.mkdir()
        (sub_dir / "sub_note.md").write_text("# Sub Note\n\nSub content", encoding="utf-8")

    def teardown_method(self):
        self.temp_dir.cleanup()

    def test_list_notes(self):
        """测试列出笔记"""
        from sync.obsidian_client import ObsidianClient

        client = ObsidianClient(vault_path=self.vault_path)
        notes = client.list_notes()

        assert len(notes) >= 1
        note_names = [n["name"] for n in notes]
        assert "test_note" in note_names

    def test_read_note(self):
        """测试读取笔记"""
        from sync.obsidian_client import ObsidianClient

        client = ObsidianClient(vault_path=self.vault_path)
        content = client.read_note("test_note.md")

        assert content is not None
        assert "Test Note" in content

    def test_read_nonexistent_note(self):
        """测试读取不存在的笔记"""
        from sync.obsidian_client import ObsidianClient

        client = ObsidianClient(vault_path=self.vault_path)
        content = client.read_note("nonexistent.md")

        assert content is None

    def test_write_note(self):
        """测试写入笔记"""
        from sync.obsidian_client import ObsidianClient

        client = ObsidianClient(vault_path=self.vault_path)
        success = client.write_note("new_note.md", "# New Note\n\nNew content")

        assert success is True
        assert (Path(self.vault_path) / "new_note.md").exists()

    def test_note_metadata(self):
        """测试获取笔记元数据"""
        from sync.obsidian_client import ObsidianClient

        client = ObsidianClient(vault_path=self.vault_path)
        metadata = client.get_note_metadata("test_note.md")

        assert metadata is not None
        assert metadata["name"] == "test_note"
        assert metadata["extension"] == ".md"

    def test_search_notes(self):
        """测试搜索笔记"""
        from sync.obsidian_client import ObsidianClient

        client = ObsidianClient(vault_path=self.vault_path)
        results = client.search_notes("Test")

        assert len(results) >= 1
        assert results[0]["name"] == "test_note"

    def test_get_all_tags(self):
        """测试获取所有标签"""
        from sync.obsidian_client import ObsidianClient

        client = ObsidianClient(vault_path=self.vault_path)
        tags = client.get_all_tags()

        assert "test" in tags

    def test_file_hash(self):
        """测试文件哈希计算"""
        from sync.obsidian_client import ObsidianClient

        client = ObsidianClient(vault_path=self.vault_path)
        hash1 = client.calculate_file_hash("test_note.md")

        assert hash1 is not None
        assert len(hash1) == 32  # MD5 hash length

    def test_exists(self):
        """测试笔记是否存在"""
        from sync.obsidian_client import ObsidianClient

        client = ObsidianClient(vault_path=self.vault_path)
        assert client.exists("test_note.md") is True
        assert client.exists("nonexistent.md") is False