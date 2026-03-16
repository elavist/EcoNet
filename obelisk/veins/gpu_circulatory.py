"""
GPU Кровообращение ЭкоНет
GPU как вены системы - распределение ресурсов
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
import threading

logger = logging.getLogger(__name__)


class GPUCirculatorySystem:
    """
    GPU Кровообращение - распределение GPU ресурсов как венозная система
    """
    
    def __init__(self):
        """Инициализация GPU кровообращения"""
        self.gpu_resources = {}  # Ресурсы GPU
        self.gpu_requests = deque(maxlen=1000)  # Очередь запросов
        self.active_tasks = {}  # Активные задачи на GPU
        self.gpu_load_history = deque(maxlen=1000)  # История загрузки
        
        # Блокировки
        self.lock = threading.Lock()
        
        # Статистика
        self.total_requests = 0
        self.successful_allocations = 0
        self.failed_allocations = 0
        
        logger.info("🩸 GPU Кровообращение инициализировано")
    
    async def request_gpu(self, task_id: str, priority: int = 5, 
                        memory_required: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Запрос GPU ресурсов
        
        Args:
            task_id: ID задачи
            priority: Приоритет (1-10, 10 - высший)
            memory_required: Требуемая память (0-1, доля от доступной)
        
        Returns:
            Информация о выделенном GPU или None
        """
        with self.lock:
            self.total_requests += 1
            
            # Добавление запроса в очередь
            request = {
                "task_id": task_id,
                "priority": priority,
                "memory_required": memory_required,
                "timestamp": datetime.now(),
                "status": "pending"
            }
            self.gpu_requests.append(request)
            
            # Попытка выделения ресурсов
            gpu_info = await self._allocate_gpu(task_id, memory_required)
            
            if gpu_info:
                self.successful_allocations += 1
                request["status"] = "allocated"
                self.active_tasks[task_id] = {
                    "gpu_info": gpu_info,
                    "request": request,
                    "start_time": datetime.now()
                }
                logger.info(f"✅ GPU выделен для задачи {task_id}")
                return gpu_info
            else:
                self.failed_allocations += 1
                request["status"] = "failed"
                logger.warning(f"⚠️ Не удалось выделить GPU для задачи {task_id}")
                return None
    
    async def _allocate_gpu(self, task_id: str, memory_required: float) -> Optional[Dict[str, Any]]:
        """
        Выделение GPU ресурсов
        
        Args:
            task_id: ID задачи
            memory_required: Требуемая память
        
        Returns:
            Информация о GPU или None
        """
        try:
            import torch
            
            if not torch.cuda.is_available():
                return None
            
            # Получение информации о доступных GPU
            device_count = torch.cuda.device_count()
            
            # Поиск свободного GPU
            for device_id in range(device_count):
                device = f"cuda:{device_id}"
                
                # Проверка доступной памяти
                total_memory = torch.cuda.get_device_properties(device_id).total_memory
                allocated_memory = torch.cuda.memory_allocated(device_id)
                reserved_memory = torch.cuda.memory_reserved(device_id)
                
                free_memory = total_memory - reserved_memory
                free_ratio = free_memory / total_memory
                
                # Проверка достаточности памяти
                if free_ratio >= memory_required:
                    return {
                        "device": device,
                        "device_id": device_id,
                        "total_memory": total_memory,
                        "allocated_memory": allocated_memory,
                        "reserved_memory": reserved_memory,
                        "free_memory": free_memory,
                        "free_ratio": free_ratio
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка выделения GPU: {e}")
            return None
    
    async def release_gpu(self, task_id: str):
        """
        Освобождение GPU ресурсов
        
        Args:
            task_id: ID задачи
        """
        with self.lock:
            if task_id in self.active_tasks:
                task_info = self.active_tasks[task_id]
                duration = (datetime.now() - task_info["start_time"]).total_seconds()
                
                # Очистка памяти GPU
                try:
                    import torch
                    gpu_info = task_info["gpu_info"]
                    device_id = gpu_info["device_id"]
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize(device_id)
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка очистки GPU: {e}")
                
                del self.active_tasks[task_id]
                logger.info(f"🔄 GPU освобожден для задачи {task_id} (длительность: {duration:.2f}s)")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики GPU кровообращения"""
        with self.lock:
            return {
                "total_requests": self.total_requests,
                "successful_allocations": self.successful_allocations,
                "failed_allocations": self.failed_allocations,
                "active_tasks": len(self.active_tasks),
                "success_rate": self.successful_allocations / self.total_requests if self.total_requests > 0 else 0,
                "pending_requests": len([r for r in self.gpu_requests if r["status"] == "pending"])
            }

