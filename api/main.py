"""
API接口模块 - FastAPI接口供前端调用
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(__name__)


class CreateNoteRequest(BaseModel):
    """创建笔记请求"""
    topic: str
    platform: str = "xiaohongshu"
    brand: Optional[str] = None
    product: Optional[str] = None


class CreateNoteResponse(BaseModel):
    """创建笔记响应"""
    success: bool
    note_id: Optional[str] = None
    data: Optional[dict] = None
    error: Optional[str] = None


@app.post("/api/notes", response_model=CreateNoteResponse)
async def create_note(req: CreateNoteRequest) -> CreateNoteResponse:
    """创建笔记"""
    try:
        from app import run_content_creation

        result = run_content_creation(req.topic)

        return CreateNoteResponse(
            success=True,
            note_id=None,
            data=result.model_dump(),
        )
    except Exception as e:
        return CreateNoteResponse(
            success=False,
            error=str(e)
        )


@app.get("/api/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
