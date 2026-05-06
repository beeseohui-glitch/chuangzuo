# TDD（测试驱动开发）规则

## 核心原则
在编写实现代码之前，必须先编写测试代码。

## 工作流程
1. 先理解需求，定义输入输出
2. 编写测试文件，定义测试用例
3. 运行测试（此时应该失败）
4. 编写实现代码
5. 运行测试（此时应该通过）
6. 如果不通过，修改代码直到通过

## 适用场景
- 开发新的 Agent（agents/目录下的文件）
- 开发新的 Tool（tools/目录下的文件）
- 开发新的 Flow（flows/目录下的文件）

## 测试文件规范
- 测试文件放在 tests/ 目录
- 文件名：test_{被测模块名}.py
- 使用 pytest 框架
- 每个测试函数以 test_ 开头
- 测试函数必须有 docstring 说明测试目的

## 测试覆盖要求
每个 Agent 至少测试：
1. 初始化是否正常
2. 输出格式是否符合 Pydantic 模型
3. 边界情况（空输入、异常输入）

每个 Tool 至少测试：
1. 正常输入的输出
2. 异常输入的错误处理
3. 边界情况

## 示例
```python
# tests/test_compliance_tools.py
import pytest
from tools.compliance_tools import ComplianceCheckTool

class TestComplianceCheckTool:
    def setup_method(self):
        self.tool = ComplianceCheckTool()

    def test_detect_absolute_word(self):
        """测试能否检测出绝对化用语"""
        result = self.tool._run("这是最好的护肝片", "xiaohongshu", "health")
        assert len(result) > 0
        assert any("绝对化用语" in str(issue) for issue in result)

    def test_normal_content_passes(self):
        """测试正常内容应通过检查"""
        result = self.tool._run("这款护肝片含有水飞蓟成分", "xiaohongshu", "health")
        assert len(result) == 0
