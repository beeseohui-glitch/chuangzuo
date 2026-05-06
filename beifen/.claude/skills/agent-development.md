# Agent 开发规范

## 适用场景
当编写 agents/ 目录下的任何文件时，必须遵循本规范。

## Agent 文件结构

每个 Agent 文件必须包含以下内容：

```python
from crewai import Agent
from config.llm_config import get_llm

class XxxAgent:
    """一句话说明这个Agent的职责"""

    def __init__(self, tools: list = None):
        self.agent = Agent(
            role="角色名称",
            goal="目标描述",
            backstory="背景描述",
            llm=get_llm(),
            tools=tools or [],
            verbose=True,
            allow_delegation=False,
            max_iter=3,
        )
