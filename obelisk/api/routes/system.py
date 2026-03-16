"""
Роуты для системной информации и полевой архитектуры роя
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter()


class SystemStatus(BaseModel):
    """Статус системы"""
    status: str
    uptime: int  # секунды
    version: str
    services: dict
    statistics: dict


@router.get("/status", response_model=SystemStatus)
async def get_system_status(request: Request):
    """Получить статус системы"""
    db = request.app.state.db
    
    stats = await db.get_system_statistics()
    
    # Информация о полевой архитектуре
    swarm_active = False
    engine = getattr(request.app.state, "unified_engine", None)
    if engine and getattr(engine, "swarm_kernel", None):
        swarm_active = engine.swarm_kernel.state.value == "running"
    
    mqtt_client = getattr(request.app.state, "mqtt_client", None)
    task_mgr = getattr(request.app.state, "task_manager", None)
    
    return SystemStatus(
        status="running",
        uptime=0,
        version="1.0.0",
        services={
            "mqtt": mqtt_client.is_connected() if mqtt_client else False,
            "database": db.is_connected() if hasattr(db, 'is_connected') else False,
            "task_manager": task_mgr.is_running() if task_mgr else False,
            "swarm_field": swarm_active,
        },
        statistics=stats
    )


@router.get("/swarm/field")
async def get_swarm_field_status(request: Request):
    """Статус полевой архитектуры роя (SwarmOS)."""
    engine = getattr(request.app.state, "unified_engine", None)
    if not engine or not getattr(engine, "swarm_kernel", None):
        return {"enabled": False, "message": "Полевая архитектура не активна"}

    kernel = engine.swarm_kernel
    result = kernel.diagnostics()

    if engine.field_scheduler:
        result["scheduler"] = engine.field_scheduler.statistics()
    if engine.field_communication:
        result["communication"] = engine.field_communication.statistics()

    return result


@router.get("/swarm/nodes")
async def get_swarm_nodes(request: Request):
    """Состояния всех узлов полевой архитектуры."""
    engine = getattr(request.app.state, "unified_engine", None)
    if not engine or not getattr(engine, "swarm_kernel", None):
        return {"nodes": {}}
    return {"nodes": engine.swarm_kernel.get_node_states()}


@router.get("/swarm/nodes/{node_id}")
async def get_swarm_node(request: Request, node_id: str):
    """Состояние конкретного узла."""
    engine = getattr(request.app.state, "unified_engine", None)
    if not engine or not getattr(engine, "swarm_kernel", None):
        return {"error": "Полевая архитектура не активна"}
    node = engine.swarm_kernel.get_node(node_id)
    if not node:
        return {"error": f"Узел '{node_id}' не найден"}
    return node.to_dict()


# ─── DeepSeek нейрон ─────────────────────────────────────────────────


class NeuronMessage(BaseModel):
    message: str
    context: Optional[dict] = None


@router.get("/neuron/deepseek")
async def get_deepseek_status(request: Request):
    """Статус DeepSeek-нейрона."""
    engine = getattr(request.app.state, "unified_engine", None)
    if not engine or not getattr(engine, "neural_architecture", None):
        return {"available": False, "state": "not_initialized"}
    
    ds = engine.neural_architecture.deepseek_neuron
    if not ds:
        return {"available": False, "state": "not_created"}
    
    return {
        "available": ds.available,
        "state": ds.state.value if hasattr(ds.state, 'value') else str(ds.state),
        "conversation_count": len(ds.conversation_buffer),
        "thinking_count": len(ds.thinking_buffer),
    }


@router.post("/neuron/deepseek/message")
async def deepseek_message(body: NeuronMessage, request: Request):
    """Отправить сообщение DeepSeek-нейрону напрямую."""
    engine = getattr(request.app.state, "unified_engine", None)
    if not engine or not getattr(engine, "neural_architecture", None):
        raise HTTPException(503, "UnifiedEngine не инициализирован")
    
    ds = engine.neural_architecture.deepseek_neuron
    if not ds or not ds.available:
        raise HTTPException(503, "DeepSeek-нейрон не доступен (LLM не подключён)")
    
    response = await ds.process_message(body.message, body.context)
    return {"response": response, "timestamp": datetime.now().isoformat()}


@router.post("/neuron/deepseek/think")
async def deepseek_think(body: NeuronMessage, request: Request):
    """Режим размышления DeepSeek-нейрона."""
    engine = getattr(request.app.state, "unified_engine", None)
    if not engine or not getattr(engine, "neural_architecture", None):
        raise HTTPException(503, "UnifiedEngine не инициализирован")
    
    ds = engine.neural_architecture.deepseek_neuron
    if not ds or not ds.available:
        raise HTTPException(503, "DeepSeek-нейрон не доступен (LLM не подключён)")
    
    thinking = await ds.think(body.message)
    return {"thinking": thinking, "timestamp": datetime.now().isoformat()}


