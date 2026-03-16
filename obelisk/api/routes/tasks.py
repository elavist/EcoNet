"""
Роуты для работы с задачами
"""

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

router = APIRouter()


class TaskType(str, Enum):
    """Типы задач"""
    COLLECT = "collect"
    PATROL = "patrol"
    RETURN = "return"


class TaskStatus(str, Enum):
    """Статусы задач"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskRequest(BaseModel):
    """Запрос на создание задачи"""
    type: TaskType
    target_bbox: List[float]
    target_location: List[float]
    frame_id: Optional[str] = None
    priority: int = 1  # 1-5, где 5 - высший приоритет
    timeout: int = 300  # секунды


class TaskResponse(BaseModel):
    """Ответ с информацией о задаче"""
    task_id: str
    type: TaskType
    status: TaskStatus
    target_bbox: List[float]
    target_location: List[float]
    priority: int
    assigned_to: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout: int


@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskRequest, request: Request):
    """Создать новую задачу"""
    task_manager = request.app.state.task_manager
    
    task_data = {
        "type": task.type.value,
        "target": {
            "bbox": task.target_bbox,
            "location": task.target_location,
            "frame": task.frame_id
        },
        "priority": task.priority,
        "timeout": task.timeout
    }
    
    created_task = await task_manager.create_task(task_data)
    return TaskResponse(**created_task)


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    request: Request,
    status: Optional[TaskStatus] = None,
    assigned_to: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Получить список задач"""
    task_manager = request.app.state.task_manager
    tasks = await task_manager.get_tasks(status=status, assigned_to=assigned_to, limit=limit, offset=offset)
    return [TaskResponse(**task) for task in tasks]


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, request: Request):
    """Получить конкретную задачу"""
    task_manager = request.app.state.task_manager
    task = await task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse(**task)


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str, request: Request):
    """Отменить задачу"""
    task_manager = request.app.state.task_manager
    success = await task_manager.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "cancelled", "task_id": task_id}


