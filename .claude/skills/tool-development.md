


# Tool 开发规范

## 适用场景
当编写 tools/ 目录下的任何文件时，必须遵循本规范。

## Tool 文件结构

```python
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class XxxToolInput(BaseModel):
    param1: str = Field(description="参数说明")
    param2: int = Field(default=5, description="参数说明")

class XxxTool(BaseTool):
    name: str = "tool_name"
    description: str = "工具描述"
    args_schema: type[BaseModel] = XxxToolInput

    def _run(self, param1: str, param2: int = 5) -> str:
        try:
            result = do_something(param1, param2)
            return str(result)
        except Exception as e:
            return f"工具执行出错：{str(e)}"
