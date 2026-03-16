"""
Центральный хаб-нейрон ЭкоНет
Центральный узел коммуникации всех нейронов
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import ComponentState

logger = logging.getLogger(__name__)


class HubNeuron(NeuralNode):
    """
    Центральный хаб-нейрон - синхронизация всех нейронов
    """
    
    def __init__(self):
        """Инициализация HubNeuron"""
        super().__init__("hub_neuron", "communication")
        self.messages_received = 0
        self.messages_routed = 0
        self.connected_neurons = set()
        self.message_history = deque(maxlen=10000)
        self.state = ComponentState.READY
        
        logger.info("🌐 HubNeuron создан")
    
    def connect_neuron(self, neuron_name: str):
        """Подключение нейрона к хабу"""
        self.connected_neurons.add(neuron_name)
        logger.info(f"🔗 Нейрон '{neuron_name}' подключен к хабу")
    
    def receive(self, data: Any, source: str = "unknown"):
        """Прием данных от нейронов"""
        super().receive(data, source)
        
        self.messages_received += 1
        
        # Сохранение в историю
        self.message_history.append({
            "data": data,
            "source": source,
            "timestamp": datetime.now()
        })
        
        # Маршрутизация к другим нейронам
        self._route_message(data, source)
    
    def _route_message(self, data: Any, source: str):
        """Маршрутизация сообщения к другим нейронам"""
        # Определение целевых нейронов на основе типа данных
        target_neurons = self._determine_targets(data, source)
        
        for target in target_neurons:
            if target in self.outgoing_connections:
                self.send(data, target)
                self.messages_routed += 1
    
    def _determine_targets(self, data: Any, source: str) -> List[str]:
        """Определение целевых нейронов для маршрутизации"""
        targets = []
        
        # Если это детекции, отправляем координатору задач
        if isinstance(data, dict) and "detections" in data:
            targets.append("task_coordinator_neuron")
        
        # Если это задачи, отправляем координатору роя
        if isinstance(data, dict) and "tasks" in data:
            targets.append("swarm_coordinator_neuron")
        
        return targets
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Процесс мышления хаба"""
        return {
            "action": "route",
            "connected_neurons": len(self.connected_neurons),
            "messages_received": self.messages_received,
            "messages_routed": self.messages_routed,
            "confidence": 1.0
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики хаба"""
        return {
            "connected_neurons": len(self.connected_neurons),
            "messages_received": self.messages_received,
            "messages_routed": self.messages_routed,
            "message_history_size": len(self.message_history)
        }

