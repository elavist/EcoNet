"""
Роуты для работы с роботами
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

router = APIRouter()


class RobotState(str, Enum):
    """Состояния робота"""
    IDLE = "idle"
    MOVING = "moving"
    COLLECTING = "collecting"
    RETURNING = "returning"
    CHARGING = "charging"
    ERROR = "error"


class RobotResponse(BaseModel):
    """Информация о роботе"""
    robot_id: str
    state: RobotState
    battery: int  # процент
    position: List[float]
    current_task: Optional[str] = None
    last_heartbeat: datetime
    capabilities: List[str] = []


class RobotTelemetry(BaseModel):
    """Телеметрия робота"""
    robot_id: str
    state: RobotState
    battery: int
    position: List[float]
    velocity: Optional[List[float]] = None
    sensors: Optional[dict] = {}


@router.get("/", response_model=List[RobotResponse])
async def get_robots(request: Request):
    """Получить список всех роботов"""
    db = request.app.state.db
    robots = await db.get_robots()
    return robots


@router.get("/{robot_id}", response_model=RobotResponse)
async def get_robot(robot_id: str, request: Request):
    """Получить информацию о конкретном роботе"""
    db = request.app.state.db
    robot = await db.get_robot(robot_id)
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    return robot


@router.get("/{robot_id}/telemetry", response_model=RobotTelemetry)
async def get_robot_telemetry(robot_id: str, request: Request):
    """Получить телеметрию робота"""
    db = request.app.state.db
    telemetry = await db.get_robot_telemetry(robot_id)
    if not telemetry:
        raise HTTPException(status_code=404, detail="Robot telemetry not found")
    return telemetry


