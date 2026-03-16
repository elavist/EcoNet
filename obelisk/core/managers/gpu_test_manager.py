"""
GPU Manager для тестов
Позволяет тестам использовать GPU параллельно с основной системой
"""

import logging
import threading
from typing import Optional
from obelisk.core.managers.gpu_manager import GPUResourceManager, GPUStats

logger = logging.getLogger(__name__)


class GPUTestManager:
    """
    Менеджер GPU для тестов
    Позволяет тестам использовать GPU без конфликтов с основной системой
    """
    
    def __init__(self, device_id: int = 0):
        """
        Инициализация менеджера GPU для тестов
        
        Args:
            device_id: ID GPU устройства
        """
        self.device_id = device_id
        self.device = f"cuda:{device_id}" if device_id >= 0 else "cpu"
        self.torch = None
        self.cuda_available = False
        
        # Блокировка для потокобезопасности
        self._lock = threading.Lock()
        
        # Инициализация PyTorch
        self._init_torch()
    
    def _init_torch(self):
        """Инициализация PyTorch для работы с GPU"""
        try:
            import torch
            self.torch = torch
            self.cuda_available = torch.cuda.is_available()
            
            if self.cuda_available:
                logger.info(f"✅ GPU Test Manager инициализирован для устройства: {self.device}")
            else:
                logger.warning("⚠️ CUDA недоступен - тесты будут использовать CPU")
                
        except ImportError:
            logger.warning("⚠️ PyTorch не установлен - GPU Test Manager недоступен")
            self.cuda_available = False
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации GPU Test Manager: {e}")
            self.cuda_available = False
    
    def get_stats(self) -> Optional[GPUStats]:
        """
        Получить статистику использования GPU для тестов
        
        Returns:
            GPUStats или None если GPU недоступен
        """
        if not self.cuda_available or not self.torch:
            return None
        
        try:
            with self._lock:
                # Информация о памяти
                total_memory = self.torch.cuda.get_device_properties(self.device_id).total_memory
                allocated_memory = self.torch.cuda.memory_allocated(self.device_id)
                reserved_memory = self.torch.cuda.memory_reserved(self.device_id)
                
                total_memory_gb = total_memory / (1024**3)
                used_memory_gb = reserved_memory / (1024**3)
                free_memory_gb = total_memory_gb - used_memory_gb
                usage_percent = (used_memory_gb / total_memory_gb) * 100
                
                return GPUStats(
                    total_memory_gb=total_memory_gb,
                    used_memory_gb=used_memory_gb,
                    free_memory_gb=free_memory_gb,
                    usage_percent=usage_percent,
                    temperature=None,
                    utilization_percent=None
                )
        except Exception as e:
            logger.error(f"Ошибка получения статистики GPU для тестов: {e}")
            return None
    
    def cleanup(self):
        """Очистка памяти GPU после тестов"""
        if not self.cuda_available or not self.torch:
            return
        
        with self._lock:
            logger.info("🧹 Очистка памяти GPU после тестов...")
            self.torch.cuda.empty_cache()
            self.torch.cuda.synchronize()
            
            stats = self.get_stats()
            if stats:
                logger.info(f"✅ Память GPU очищена. Использование: {stats.usage_percent:.1f}%")
    
    def reserve_gpu_for_tests(self) -> bool:
        """
        Резервирование GPU для тестов
        
        Returns:
            True если GPU доступен для тестов
        """
        if not self.cuda_available:
            return False
        
        stats = self.get_stats()
        if not stats:
            return False
        
        # Проверяем доступность GPU для тестов
        # Тесты могут использовать GPU если доступно хотя бы 1 GB
        if stats.free_memory_gb >= 1.0:
            logger.info(f"✅ GPU доступен для тестов: {stats.free_memory_gb:.2f} GB свободно")
            return True
        else:
            logger.warning(f"⚠️ Недостаточно памяти GPU для тестов: {stats.free_memory_gb:.2f} GB")
            return False


# Глобальный экземпляр менеджера GPU для тестов
_test_gpu_manager: Optional[GPUTestManager] = None


def get_test_gpu_manager(device_id: int = 0) -> GPUTestManager:
    """
    Получить глобальный экземпляр менеджера GPU для тестов
    
    Args:
        device_id: ID GPU устройства
        
    Returns:
        GPUTestManager
    """
    global _test_gpu_manager
    
    if _test_gpu_manager is None:
        _test_gpu_manager = GPUTestManager(device_id=device_id)
    
    return _test_gpu_manager


def cleanup_test_gpu():
    """Глобальная очистка памяти GPU после тестов"""
    global _test_gpu_manager
    if _test_gpu_manager:
        _test_gpu_manager.cleanup()

