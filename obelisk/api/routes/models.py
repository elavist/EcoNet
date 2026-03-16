"""
Роуты для работы с моделями
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()


class ModelResponse(BaseModel):
    """Информация о модели"""
    model_id: str
    name: str
    version: str
    path: str
    mAP: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    is_active: bool
    created_at: datetime
    deployed_at: Optional[datetime] = None


class ModelTrainingRequest(BaseModel):
    """Запрос на обучение модели"""
    epochs: int = 100
    batch_size: int = 16
    learning_rate: Optional[float] = None
    resume: bool = False


@router.get("/", response_model=List[ModelResponse])
async def get_models(request: Request):
    """Получить список всех моделей"""
    db = request.app.state.db
    models = await db.get_models()
    return models


@router.get("/active", response_model=ModelResponse)
async def get_active_model(request: Request):
    """Получить активную модель"""
    db = request.app.state.db
    model = await db.get_active_model()
    if not model:
        raise HTTPException(status_code=404, detail="No active model found")
    return model


@router.get("/active-learning/status")
async def get_active_learning_status(request: Request):
    """Получить статус активного обучения"""
    if not hasattr(request.app.state, 'active_learner'):
        raise HTTPException(status_code=404, detail="Active learner not initialized")
    
    active_learner = request.app.state.active_learner
    stats = active_learner.get_statistics()
    
    return {
        "enabled": stats["enabled"],
        "running": stats["running"],
        "collected_frames": stats["collected_frames"],
        "uncertain_frames": stats["uncertain_frames"],
        "auto_labeled_frames": stats["auto_labeled_frames"],
        "retraining_count": stats["retraining_count"]
    }


@router.post("/train")
async def train_model(training_request: ModelTrainingRequest, request: Request):
    """Запустить обучение модели"""
    trainer = request.app.state.trainer
    if not trainer:
        raise HTTPException(status_code=503, detail="Trainer service not available")
    
    training_id = await trainer.start_training(
        epochs=training_request.epochs,
        batch_size=training_request.batch_size,
        learning_rate=training_request.learning_rate,
        resume=training_request.resume
    )
    
    return {
        "status": "training_started",
        "training_id": training_id,
        "message": "Model training started"
    }


@router.post("/{model_id}/deploy")
async def deploy_model(model_id: str, request: Request):
    """Деплоить модель на edge устройства"""
    trainer = request.app.state.trainer
    if not trainer:
        raise HTTPException(status_code=503, detail="Trainer service not available")
    
    success = await trainer.deploy_model(model_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found or deployment failed")
    
    return {
        "status": "deployed",
        "model_id": model_id,
        "message": "Model deployed to edge devices"
    }


