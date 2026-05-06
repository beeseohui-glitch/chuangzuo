


# Flow 工作流开发规范

## 适用场景
当编写 flows/ 目录下的任何文件时，必须遵循本规范。

## Flow 文件结构

```python
from crewai.flow.flow import Flow, listen, start, and_
from pydantic import BaseModel

class XxxState(BaseModel):
    input_data: str = ""
    result: dict = {}

class XxxFlow(Flow[XxxState]):

    @start()
    def step_1(self):
        """第一步说明"""
        return "step_1_done"

    @listen(step_1)
    def step_2(self):
        """第二步说明"""
        return "step_2_done"
