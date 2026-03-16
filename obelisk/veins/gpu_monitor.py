"""
GPU Монитор ЭкоНет
Мониторинг состояния GPU
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
import threading

logger = logging.getLogger(__name__)


class GPUMonitor:
    """
    GPU Монитор - отслеживание состояния GPU
    """
    
    def __init__(self):
        """Инициализация GPUMonitor"""
        self.gpu_stats_history = deque(maxlen=1000)
        self.monitoring_active = False
        self.lock = threading.Lock()
        
        logger.info("📊 GPUMonitor создан")
    
    def start_monitoring(self):
        """Запуск мониторинга"""
        self.monitoring_active = True
        logger.info("🔍 Мониторинг GPU запущен")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring_active = False
        logger.info("⏹️ Мониторинг GPU остановлен")
    
    def get_gpu_stats(self) -> Optional[Dict[str, Any]]:
        """Получение статистики GPU"""
        try:
            import torch
            
            if not torch.cuda.is_available():
                return None
            
            device_count = torch.cuda.device_count()
            stats = {
                "devices": [],
                "timestamp": datetime.now().isoformat()
            }
            
            for device_id in range(device_count):
                device = f"cuda:{device_id}"
                props = torch.cuda.get_device_properties(device_id)
                
                total_memory = props.total_memory
                allocated_memory = torch.cuda.memory_allocated(device_id)
                reserved_memory = torch.cuda.memory_reserved(device_id)
                free_memory = total_memory - reserved_memory
                
                device_stats = {
                    "device_id": device_id,
                    "device_name": props.name,
                    "total_memory_gb": total_memory / (1024**3),
                    "allocated_memory_gb": allocated_memory / (1024**3),
                    "reserved_memory_gb": reserved_memory / (1024**3),
                    "free_memory_gb": free_memory / (1024**3),
                    "usage_percent": (reserved_memory / total_memory) * 100
                }
                
                stats["devices"].append(device_stats)
            
            # Сохранение в историю
            with self.lock:
                self.gpu_stats_history.append(stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики GPU: {e}")
            return None
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Получение истории статистики"""
        with self.lock:
            return list(self.gpu_stats_history)[-limit:]

