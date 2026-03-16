"""
Нейрон координации роя ЭкоНет
Координация роя роботов
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import ComponentState

logger = logging.getLogger(__name__)


class SwarmCoordinatorNeuron(NeuralNode):
    """
    Нейрон координации роя - управление роем роботов
    """
    
    def __init__(self, task_manager=None, mqtt_client=None):
        """
        Инициализация SwarmCoordinatorNeuron
        
        Args:
            task_manager: TaskManager сервис
            mqtt_client: MQTT клиент для связи с роботами
        """
        super().__init__("swarm_coordinator_neuron", "coordination")
        self.task_manager = task_manager
        self.mqtt_client = mqtt_client
        self.robots_connected = 0
        self.tasks_distributed = 0
        self.state = ComponentState.READY
        
        logger.info("🐝 SwarmCoordinatorNeuron создан")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Процесс мышления нейрона координации роя"""
        tasks = context.get("tasks", [])
        
        if not tasks:
            return {
                "action": "wait",
                "reason": "Нет задач для распределения",
                "confidence": 0.0
            }
        
        if not self.task_manager:
            return {
                "action": "skip",
                "reason": "TaskManager недоступен",
                "confidence": 0.0
            }
        
        try:
            # Распределение задач между роботами
            distributed = await self._distribute_tasks(tasks)
            
            self.tasks_distributed += len(distributed)
            
            return {
                "action": "coordinate_swarm",
                "distributed_tasks": distributed,
                "tasks_count": len(distributed),
                "confidence": 0.8,
                "total_distributed": self.tasks_distributed
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка координации роя: {e}")
            return {
                "action": "error",
                "error": str(e),
                "confidence": 0.0
            }
    
    async def _distribute_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Распределение задач между роботами"""
        distributed = []
        
        for task in tasks:
            # Отправка задачи через MQTT если доступен
            if self.mqtt_client:
                try:
                    await self.mqtt_client.publish_task(task)
                    distributed.append(task)
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось отправить задачу: {e}")
            else:
                # Локальное выполнение
                distributed.append(task)
        
        return distributed

