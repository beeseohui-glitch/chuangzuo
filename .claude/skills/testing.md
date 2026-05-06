# 测试规范

## 测试要求
- 每个Agent必须有对应测试文件 tests/test_{agent_name}.py
- 每个Tool必须有对应测试文件 tests/test_{tool_name}.py
- 测试使用 pytest 框架

## 测试分类
1. 单元测试：测试单个Tool的输入输出
2. Agent测试：测试Agent能否正确输出（需要Mock LLM）
3. 集成测试：测试Flow完整执行

## Mock策略
- 开发阶段：使用MiniMax真实API（消耗token但最真实）
- 测试阶段：Mock LLM返回固定结果（省token）

## 测试文件模板
```python
import pytest
from agents.xxx_agent import XxxAgent

class TestXxxAgent:
    def setup_method(self):
        self.agent = XxxAgent()

    def test_agent_output_format(self):
        """测试输出格式是否符合预期"""
        result = self.agent.agent.kickoff(...)
        assert result is not None
