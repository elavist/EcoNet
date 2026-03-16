"""
GPU Планировщик ЭкоНет
Планирование использования GPU ресурсов
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
import threading

from obelisk.veins.gpu_circulatory import GPUCirculatorySystem

logger = logging.getLogger(__name__)


class GPUScheduler:
    """
    GPU Планировщик - планирование использования GPU
    """
    
    def __init__(self, circulatory_system: GPUCirculatorySystem):
        """
        Инициализация GPUScheduler
        
        Args:
            circulatory_system: Система GPU кровообращения
        """
        self.circulatory = circulatory_system
        self.schedule_queue = deque(maxlen=1000)
        self.scheduled_tasks = {}
        self.lock = threading.Lock()
        
        logger.info("📅 GPUScheduler создан")
    
    async def schedule_task(self, task_id: str, priority: int = 5,
                          memory_required: float = 0.1,
                          scheduled_time: Optional[datetime] = None) -> bool:
        """
        Планирование задачи на GPU
        
        Args:
            task_id: ID задачи
            priority: Приоритет
            memory_required: Требуемая память
            scheduled_time: Время выполнения (None = немедленно)
        
        Returns:
            True если задача запланирована
        """
        schedule_entry = {
            "task_id": task_id,
            "priority": priority,
            "memory_required": memory_required,
            "scheduled_time": scheduled_time or datetime.now(),
            "created_at": datetime.now(),
            "status": "scheduled"
        }
        
        with self.lock:
            self.schedule_queue.append(schedule_entry)
            self.scheduled_tasks[task_id] = schedule_entry
        
        logger.info(f"📅 Задача {task_id} запланирована на {schedule_entry['scheduled_time']}")
        
        # Если задача на немедленное выполнение
        if not scheduled_time or scheduled_time <= datetime.now():
            await self._execute_scheduled_task(task_id)
        
        return True
    
    async def _execute_scheduled_task(self, task_id: str):
        """Выполнение запланированной задачи"""
        if task_id not in self.scheduled_tasks:
            return
        
        task = self.scheduled_tasks[task_id]
        
        # Запрос GPU через кровообращение
        gpu_info = await self.circulatory.request_gpu(
            task_id,
            task["priority"],
            task["memory_required"]
        )
        
        if gpu_info:
            task["status"] = "executing"
            task["gpu_info"] = gpu_info
            logger.info(f"✅ Задача {task_id} начала выполнение на GPU")
        else:
            task["status"] = "waiting"
            logger.warning(f"⚠️ Задача {task_id} ожидает GPU")
    
    async def process_schedule(self):
        """Обработка расписания - выполнение готовых задач"""
        now = datetime.now()
        ready_tasks = []
        
        with self.lock:
            for task_id, task in self.scheduled_tasks.items():
                if task["status"] == "scheduled" and task["scheduled_time"] <= now:
                    ready_tasks.append(task_id)
        
        for task_id in ready_tasks:
            await self._execute_scheduled_task(task_id)
    
    def get_schedule(self) -> List[Dict[str, Any]]:
        """Получение расписания"""
        with self.lock:
            return list(self.scheduled_tasks.values())
    
    def cancel_task(self, task_id: str) -> bool:
        """Отмена запланированной задачи"""
        with self.lock:
            if task_id in self.scheduled_tasks:
                del self.scheduled_tasks[task_id]
                logger.info(f"❌ Задача {task_id} отменена")
                return True
            return False

