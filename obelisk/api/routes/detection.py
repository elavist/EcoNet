"""
Роуты для работы с детекциями
"""

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class DetectionResponse(BaseModel):
    """Модель ответа детекции"""
    id: str
    source: str
    timestamp: datetime
    bbox: List[float]
    class_name: str
    confidence: float
    frame_id: Optional[str] = None
    location: Optional[List[float]] = None


class DetectionRequest(BaseModel):
    """Модель запроса детекции"""
    source: str
    bbox: List[float]
    class_name: str
    confidence: float
    frame_id: Optional[str] = None
    location: Optional[List[float]] = None


@router.post("/", response_model=DetectionResponse)
async def create_detection(detection: DetectionRequest, request: Request):
    """Создать новую детекцию"""
    db = request.app.state.db
    mqtt_client = request.app.state.mqtt_client
    
    # Сохранить в БД
    detection_id = await db.save_detection(detection.dict())
    
    # Опубликовать в MQTT
    detection_data = {
        "id": detection_id,
        "timestamp": datetime.utcnow().isoformat(),
        **detection.dict()
    }
    await mqtt_client.publish("obelisk/detection", detection_data)
    
    return DetectionResponse(
        id=detection_id,
        timestamp=datetime.utcnow(),
        **detection.dict()
    )


@router.get("/", response_model=List[DetectionResponse])
async def get_detections(
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    source: Optional[str] = None,
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0)
):
    """Получить список детекций"""
    db = request.app.state.db
    detections = await db.get_detections(limit=limit, offset=offset, source=source, min_confidence=min_confidence)
    return detections


@router.get("/{detection_id}", response_model=DetectionResponse)
async def get_detection(detection_id: str, request: Request):
    """Получить конкретную детекцию"""
    db = request.app.state.db
    detection = await db.get_detection(detection_id)
    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found")
    return detection


