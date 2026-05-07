"""
创作接口

- POST /api/v1/create/start          提交创作需求，触发 Flow
- GET  /api/v1/create/{task_id}/status 查询任务状态
- WS   /ws/create/{task_id}           实时状态推送
- POST /api/v1/create/{task_id}/select-title  用户选择标题
- POST /api/v1/create/{task_id}/p2-decision   P2 问题处理
- GET  /api/v1/create/{task_id}/result        获取最终笔记包
"""

import asyncio
import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel

from api.db import get_db_conn
from api.deps import require_tenant, UserInfo
from fastapi import Depends

router = APIRouter(prefix="/api/v1/create", tags=["创作"])


# ── 任务状态 ──────────────────────────────────────────────


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_TITLE_SELECTION = "awaiting_title_selection"
    AWAITING_P2_DECISION = "awaiting_p2_decision"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskRecord(BaseModel):
    task_id: str
    user_id: str
    enterprise_id: str
    status: TaskStatus = TaskStatus.PENDING
    progress: int = 0
    current_step: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None
    title_options: Optional[list[dict]] = None
    p2_issues: Optional[list[dict]] = None
    created_at: str = ""
    updated_at: str = ""


# ── 内存任务存储（开发模式）─────────────────────────────────

_tasks: dict[str, TaskRecord] = {}
_ws_connections: dict[str, list[WebSocket]] = {}

# 内存笔记存储（开发模式 fallback，当数据库写入失败时使用）
_memory_notes: list[dict] = []
_memory_note_id_counter = 1000


def get_memory_notes(enterprise_id: str) -> list[dict]:
    """获取指定企业的内存笔记"""
    return [n for n in _memory_notes if n.get("enterprise_id") == enterprise_id]


async def _broadcast(task_id: str, data: dict):
    """向所有监听该 task_id 的 WebSocket 连接广播"""
    connections = _ws_connections.get(task_id, [])
    dead = []
    for ws in connections:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connections.remove(ws)


def _update_task(task_id: str, **kwargs):
    """更新任务状态并记录时间"""
    task = _tasks.get(task_id)
    if not task:
        return
    for k, v in kwargs.items():
        setattr(task, k, v)
    task.updated_at = datetime.now().isoformat()


async def _run_creation_flow(task_id: str, input_data: dict):
    """后台执行真实创作 Flow"""
    from api.flow_runner import run_creation_flow
    await run_creation_flow(task_id, input_data, _update_task, _broadcast)


# ── 请求/响应模型 ─────────────────────────────────────────


class CreateStartRequest(BaseModel):
    product: str
    scene: Optional[str] = None
    persona: Optional[str] = None
    platform: str = "xiaohongshu"


class SelectTitleRequest(BaseModel):
    title_index: int


class P2DecisionRequest(BaseModel):
    accept: bool
    custom_text: Optional[str] = None


# ── 接口 ──────────────────────────────────────────────────


@router.post("/start")
async def start_creation(
    req: CreateStartRequest,
    background_tasks: BackgroundTasks,
    user: UserInfo = Depends(require_tenant),
):
    """提交创作需求，触发 Flow"""
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    now = datetime.now().isoformat()

    task = TaskRecord(
        task_id=task_id,
        user_id=user.user_id,
        enterprise_id=user.enterprise_id or "",
        status=TaskStatus.PENDING,
        created_at=now,
        updated_at=now,
    )
    _tasks[task_id] = task

    input_data = {
        "product": req.product,
        "scene": req.scene,
        "persona": req.persona,
        "platform": req.platform,
        "enterprise_id": user.enterprise_id,
    }

    background_tasks.add_task(_run_creation_flow, task_id, input_data)

    return {"task_id": task_id, "status": TaskStatus.PENDING}


@router.get("/{task_id}/status")
async def get_task_status(
    task_id: str,
    user: UserInfo = Depends(require_tenant),
):
    """查询任务状态"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "任务不存在"})
    if task.user_id != user.user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN", "message": "无权访问该任务"})

    return {
        "task_id": task.task_id,
        "status": task.status,
        "progress": task.progress,
        "current_step": task.current_step,
        "error": task.error,
    }


@router.post("/{task_id}/select-title")
async def select_title(
    task_id: str,
    req: SelectTitleRequest,
    user: UserInfo = Depends(require_tenant),
):
    """用户选择标题"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "任务不存在"})
    if task.user_id != user.user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN", "message": "无权访问该任务"})
    if task.status != TaskStatus.AWAITING_TITLE_SELECTION:
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "当前不在标题选择阶段"})

    if task.title_options and 0 <= req.title_index < len(task.title_options):
        selected = task.title_options[req.title_index]
        _update_task(task_id, status=TaskStatus.RUNNING)
        await _broadcast(task_id, {"type": "title_selected", "title": selected})
        # 通知 flow_runner 用户已选择标题
        from api.flow_runner import signal_title_selection
        signal_title_selection(task_id, req.title_index)
        return {"selected": selected}

    raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "无效的标题索引"})


@router.post("/{task_id}/p2-decision")
async def p2_decision(
    task_id: str,
    req: P2DecisionRequest,
    user: UserInfo = Depends(require_tenant),
):
    """P2 问题处理"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "任务不存在"})
    if task.user_id != user.user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN", "message": "无权访问该任务"})
    if task.status != TaskStatus.AWAITING_P2_DECISION:
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "当前不在 P2 决策阶段"})

    _update_task(task_id, status=TaskStatus.RUNNING)
    await _broadcast(task_id, {"type": "p2_decided", "accept": req.accept})
    # 通知 flow_runner 用户已做决策
    from api.flow_runner import signal_p2_decision
    signal_p2_decision(task_id, req.accept)

    return {"accepted": req.accept}


@router.get("/{task_id}/result")
async def get_result(
    task_id: str,
    user: UserInfo = Depends(require_tenant),
):
    """获取最终笔记包"""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail={"error": "NOT_FOUND", "message": "任务不存在"})
    if task.user_id != user.user_id:
        raise HTTPException(status_code=403, detail={"error": "FORBIDDEN", "message": "无权访问该任务"})
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail={"error": "BAD_REQUEST", "message": "任务尚未完成"})

    return {"task_id": task.task_id, "result": task.result}


# ── WebSocket ─────────────────────────────────────────────


@router.websocket("/ws/{task_id}")
async def websocket_create(websocket: WebSocket, task_id: str):
    """WebSocket 实时状态推送"""
    await websocket.accept()

    if task_id not in _ws_connections:
        _ws_connections[task_id] = []
    _ws_connections[task_id].append(websocket)

    # 如果任务已完成，立即推送结果
    task = _tasks.get(task_id)
    if task and task.status == TaskStatus.COMPLETED:
        await websocket.send_json({"type": "completed", "result": task.result})
    elif task and task.status == TaskStatus.FAILED:
        await websocket.send_json({"type": "failed", "error": task.error})

    try:
        while True:
            # 保持连接，等待客户端消息或断开
            await websocket.receive_text()
    except WebSocketDisconnect:
        if task_id in _ws_connections:
            _ws_connections[task_id] = [
                ws for ws in _ws_connections[task_id] if ws != websocket
            ]
