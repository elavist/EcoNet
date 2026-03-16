"""
API роуты для диалога с ЭкоНет
"""

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatMessage(BaseModel):
    """Модель сообщения для диалога"""
    message: str
    visual_context: Optional[Dict] = None


class ChatResponse(BaseModel):
    """Модель ответа от ЭкоНет"""
    response: str
    timestamp: str
    visual_context: Optional[Dict] = None


class ConversationHistory(BaseModel):
    """История диалога"""
    history: List[Dict]


@router.post("/message", response_model=ChatResponse)
async def send_message(chat_message: ChatMessage, request: Request):
    """
    Отправить сообщение ЭкоНет
    
    Примеры:
    - "Что видишь?"
    - "Сколько окурков?"
    - "Это окурок" (для обучения)
    """
    if not hasattr(request.app.state, 'chat_service'):
        raise HTTPException(status_code=503, detail="Сервис диалога не инициализирован")
    
    chat_service = request.app.state.chat_service
    
    try:
        response = await chat_service.process_message(
            chat_message.message,
            chat_message.visual_context
        )
        
        return ChatResponse(
            response=response,
            timestamp=chat_service.conversation_history[-1]["timestamp"] if chat_service.conversation_history else datetime.now().isoformat(),
            visual_context=chat_message.visual_context
        )
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка обработки сообщения: {str(e)}")


@router.get("/history", response_model=ConversationHistory)
async def get_history(request: Request):
    """Получить историю диалога"""
    if not hasattr(request.app.state, 'chat_service'):
        raise HTTPException(status_code=503, detail="Сервис диалога не инициализирован")
    
    chat_service = request.app.state.chat_service
    return ConversationHistory(history=chat_service.get_conversation_history())


@router.delete("/history")
async def clear_history(request: Request):
    """Очистить историю диалога"""
    if not hasattr(request.app.state, 'chat_service'):
        raise HTTPException(status_code=503, detail="Сервис диалога не инициализирован")
    
    chat_service = request.app.state.chat_service
    chat_service.clear_history()
    return {"message": "История диалога очищена"}


@router.websocket("/ws")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket для интерактивного диалога с ЭкоНет
    
    Формат сообщений:
    - От клиента: {"message": "текст сообщения", "visual_context": {...}}
    - К клиенту: {"response": "ответ ЭкоНет", "timestamp": "...", "visual_context": {...}}
    """
    await websocket.accept()
    logger.info("WebSocket соединение установлено")
    
    # Получение chat_service из app.state через scope
    chat_service = None
    try:
        # Получаем app через websocket scope (FastAPI/Starlette способ)
        app = websocket.scope.get('app')
        if app and hasattr(app.state, 'chat_service'):
            chat_service = app.state.chat_service
            logger.info("✅ ChatService получен из app.state")
        else:
            logger.warning("⚠️ ChatService не найден в app.state")
    except Exception as e:
        logger.warning(f"Не удалось получить chat_service: {e}")
    
    try:
        while True:
            # Получение сообщения
            data = await websocket.receive_json()
            message = data.get("message", "")
            visual_context = data.get("visual_context", None)
            
            if not message:
                await websocket.send_json({
                    "error": "Пустое сообщение"
                })
                continue
            
            # Обработка специальных команд
            if message.lower() in ["quit", "exit"]:
                await websocket.send_json({
                    "response": "До свидания! 👋",
                    "type": "system"
                })
                break
            
            # Обработка сообщения
            if chat_service:
                try:
                    response = await chat_service.process_message(message, visual_context)
                    timestamp = chat_service.conversation_history[-1]["timestamp"] if chat_service.conversation_history else datetime.now().isoformat()
                except Exception as e:
                    logger.error(f"Ошибка обработки сообщения: {e}")
                    response = f"Произошла ошибка: {str(e)}"
                    timestamp = datetime.now().isoformat()
            else:
                response = "Сервис диалога не инициализирован. Используйте CLI интерфейс."
                timestamp = datetime.now().isoformat()
            
            # Отправка ответа
            await websocket.send_json({
                "response": response,
                "timestamp": timestamp,
                "visual_context": visual_context
            })
    
    except WebSocketDisconnect:
        logger.info("WebSocket соединение закрыто")
    except Exception as e:
        logger.error(f"Ошибка WebSocket: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "error": f"Ошибка: {str(e)}"
            })
        except:
            pass

