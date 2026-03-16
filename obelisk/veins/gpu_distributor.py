"""
GPU Распределитель ЭкоНет
Распределение GPU ресурсов между задачами
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
import threading

from obelisk.veins.gpu_circulatory import GPUCirculatorySystem

logger = logging.getLogger(__name__)


class GPUDistributor:
    """
    GPU Распределитель - умное распределение GPU ресурсов
    """
    
    def __init__(self, circulatory_system: GPUCirculatorySystem):
        """
        Инициализация GPUDistributor
        
        Args:
            circulatory_system: Система GPU кровообращения
        """
        self.circulatory = circulatory_system
        self.distribution_strategy = "fair"  # fair, priority, performance
        self.task_priorities = {}  # Приоритеты задач
        self.lock = threading.Lock()
        
        logger.info("⚡ GPUDistributor создан")
    
    async def distribute_gpu(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Распределение GPU между задачами
        
        Args:
            tasks: Список задач
        
        Returns:
            Результат распределения
        """
        distribution_result = {
            "allocated": [],
            "pending": [],
            "failed": []
        }
        
        # Сортировка задач по приоритету
        sorted_tasks = sorted(
            tasks,
            key=lambda t: self.task_priorities.get(t.get("id", ""), 5),
            reverse=True
        )
        
        for task in sorted_tasks:
            task_id = task.get("id", f"task_{datetime.now().timestamp()}")
            priority = self.task_priorities.get(task_id, 5)
            memory_required = task.get("memory_required", 0.1)
            
            gpu_info = await self.circulatory.request_gpu(
                task_id, priority, memory_required
            )
            
            if gpu_info:
                distribution_result["allocated"].append({
                    "task_id": task_id,
                    "gpu_info": gpu_info
                })
            else:
                distribution_result["pending"].append({
                    "task_id": task_id,
                    "reason": "GPU недоступен"
                })
        
        return distribution_result
    
    def set_task_priority(self, task_id: str, priority: int):
        """Установка приоритета задачи"""
        with self.lock:
            self.task_priorities[task_id] = priority
            logger.debug(f"📊 Приоритет задачи {task_id} установлен: {priority}")
    
    def set_distribution_strategy(self, strategy: str):
        """Установка стратегии распределения"""
        if strategy in ["fair", "priority", "performance"]:
            self.distribution_strategy = strategy
            logger.info(f"📈 Стратегия распределения GPU: {strategy}")

