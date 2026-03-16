"""
Нейрон MQTT коммуникации ЭкоНет
Управление MQTT сообщениями через нейронную сеть
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import ComponentState

logger = logging.getLogger(__name__)


class MQTTNeuron(NeuralNode):
    """
    Нейрон MQTT коммуникации - управление MQTT сообщениями
    """
    
    def __init__(self, mqtt_client=None):
        """
        Инициализация MQTTNeuron
        
        Args:
            mqtt_client: MQTT клиент сервис
        """
        super().__init__("mqtt_neuron", "communication")
        self.mqtt_client = mqtt_client
        self.messages_sent = 0
        self.messages_received = 0
        self.message_history = deque(maxlen=1000)
        self.subscribed_topics = set()
        self.state = ComponentState.READY
        
        logger.info("📡 MQTTNeuron создан")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Процесс мышления нейрона MQTT"""
        action = context.get("action", "publish")
        
        try:
            if action == "publish":
                topic = context.get("topic")
                payload = context.get("payload", {})
                qos = context.get("qos", 1)
                
                if not topic:
                    return {
                        "action": "error",
                        "error": "Топик не указан",
                        "confidence": 0.0
                    }
                
                result = await self._publish_message(topic, payload, qos)
                return {
                    "action": "publish",
                    "topic": topic,
                    "success": result,
                    "confidence": 0.9 if result else 0.0
                }
            
            elif action == "subscribe":
                topic = context.get("topic")
                if not topic:
                    return {
                        "action": "error",
                        "error": "Топик не указан",
                        "confidence": 0.0
                    }
                
                result = await self._subscribe_topic(topic)
                return {
                    "action": "subscribe",
                    "topic": topic,
                    "success": result,
                    "confidence": 0.9 if result else 0.0
                }
            
            elif action == "status":
                status = self._get_connection_status()
                return {
                    "action": "status",
                    "status": status,
                    "confidence": 1.0
                }
            
            else:
                return {
                    "action": "unknown",
                    "error": f"Неизвестное действие: {action}",
                    "confidence": 0.0
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка MQTT нейрона: {e}")
            return {
                "action": "error",
                "error": str(e),
                "confidence": 0.0
            }
    
    async def _publish_message(self, topic: str, payload: Dict[str, Any], qos: int = 1) -> bool:
        """Публикация сообщения в MQTT"""
        if not self.mqtt_client:
            logger.warning("MQTT клиент не доступен")
            return False
        
        try:
            await self.mqtt_client.publish(topic, payload, qos=qos)
            self.messages_sent += 1
            
            # Сохранение в историю
            self.message_history.append({
                "type": "sent",
                "topic": topic,
                "payload": payload,
                "timestamp": datetime.now()
            })
            
            # Отправка через нейронную сеть
            self.broadcast({
                "type": "mqtt_message_sent",
                "data": {
                    "topic": topic,
                    "payload": payload
                },
                "source": self.name
            })
            
            logger.debug(f"📤 MQTT сообщение отправлено в {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка публикации MQTT: {e}")
            return False
    
    async def _subscribe_topic(self, topic: str) -> bool:
        """Подписка на MQTT топик"""
        if not self.mqtt_client:
            logger.warning("MQTT клиент не доступен")
            return False
        
        try:
            # Создаем callback для обработки сообщений
            async def message_callback(topic_received: str, payload: Dict[str, Any]):
                """Callback для обработки входящих сообщений"""
                self.messages_received += 1
                
                # Сохранение в историю
                self.message_history.append({
                    "type": "received",
                    "topic": topic_received,
                    "payload": payload,
                    "timestamp": datetime.now()
                })
                
                # Отправка через нейронную сеть
                self.broadcast({
                    "type": "mqtt_message_received",
                    "data": {
                        "topic": topic_received,
                        "payload": payload
                    },
                    "source": self.name
                })
                
                logger.debug(f"📥 MQTT сообщение получено из {topic_received}")
            
            self.mqtt_client.subscribe(topic, message_callback)
            self.subscribed_topics.add(topic)
            
            logger.info(f"📡 Подписка на топик: {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подписки на топик: {e}")
            return False
    
    def _get_connection_status(self) -> Dict[str, Any]:
        """Получение статуса подключения"""
        is_connected = False
        if self.mqtt_client:
            is_connected = self.mqtt_client.is_connected()
        
        return {
            "connected": is_connected,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "subscribed_topics": list(self.subscribed_topics),
            "history_size": len(self.message_history)
        }
    
    def receive(self, data: Any, source: str = "unknown"):
        """Прием данных от других нейронов"""
        super().receive(data, source)
        
        # Если это команда на публикацию MQTT
        if isinstance(data, dict) and data.get("type") == "mqtt_publish_request":
            topic = data.get("topic")
            payload = data.get("payload", {})
            qos = data.get("qos", 1)
            
            # Асинхронная публикация
            import asyncio
            asyncio.create_task(self._publish_message(topic, payload, qos))
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики MQTT нейрона"""
        return {
            "connected": self.mqtt_client.is_connected() if self.mqtt_client else False,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "subscribed_topics": list(self.subscribed_topics),
            "history_size": len(self.message_history),
            "last_messages": list(self.message_history)[-10:] if self.message_history else []
        }

