"""
Нейрон координации задач ЭкоНет
Координация задач между компонентами
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import ComponentState

logger = logging.getLogger(__name__)


class TaskCoordinatorNeuron(NeuralNode):
    """
    Нейрон координации задач - управление задачами
    """
    
    def __init__(self, task_manager=None):
        """
        Инициализация TaskCoordinatorNeuron
        
        Args:
            task_manager: TaskManager сервис
        """
        super().__init__("task_coordinator_neuron", "coordination")
        self.task_manager = task_manager
        self.tasks_created = 0
        self.tasks_completed = 0
        self.state = ComponentState.READY
        
        logger.info("📋 TaskCoordinatorNeuron создан")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Процесс мышления нейрона координации задач
        
        Args:
            context: Контекст с детекциями или задачами
        
        Returns:
            Мнение нейрона о координации задач
        """
        detections = context.get("detections", [])
        
        if not detections:
            return {
                "action": "wait",
                "reason": "Нет детекций для создания задач",
                "confidence": 0.0
            }
        
        if not self.task_manager:
            return {
                "action": "skip",
                "reason": "TaskManager недоступен",
                "confidence": 0.0
            }
        
        try:
            # Создание задач на основе детекций
            tasks = []
            for detection in detections:
                task = await self.task_manager.create_task_from_detection(detection)
                tasks.append(task)
                self.tasks_created += 1
            
            return {
                "action": "coordinate",
                "tasks": tasks,
                "tasks_count": len(tasks),
                "confidence": 0.8,
                "total_tasks_created": self.tasks_created
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка координации задач: {e}")
            return {
                "action": "error",
                "error": str(e),
                "confidence": 0.0
            }

