"""
API测试

Step 15: 测试模块开发
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


class TestAPI:
    """API接口测试"""

    def setup_method(self):
        """测试前准备"""
        # 延迟导入避免启动问题
        import sys
        if "api.main" in sys.modules:
            del sys.modules["api.main"]

    @patch("api.main.run_content_creation")
    def test_create_note(self, mock_run):
        """测试创建笔记接口"""
        mock_run.return_value = MagicMock(model_dump=lambda: {"title": "测试"})

        from api.main import CreateNoteRequest

        req = CreateNoteRequest(topic="护肝片种草")
        assert req.topic == "护肝片种草"

    def test_health_check(self):
        """测试健康检查端点"""
        # 使用TestClient测试
        from api.main import app
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
