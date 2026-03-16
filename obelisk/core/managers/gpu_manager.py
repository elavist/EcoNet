"""
Менеджер GPU с ограничением использования до 85%
Управление ресурсами GPU для оптимальной производительности
"""

import logging
import threading
import time
from typing import Optional, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GPUStats:
    """Статистика использования GPU"""
    total_memory_gb: float
    used_memory_gb: float
    free_memory_gb: float
    usage_percent: float
    temperature: Optional[float] = None
    utilization_percent: Optional[float] = None


class GPUMemoryManager:
    """
    Менеджер памяти GPU - максимальное использование всей мощности
    Автоматически управляет памятью для оптимальной производительности
    """
    
    def __init__(self, max_usage_percent: float = 0.99, device_id: int = 0):
        """
        Инициализация менеджера памяти GPU
        
        Args:
            max_usage_percent: Максимальный процент использования GPU (0.99 = 99% для максимальной мощности)
            device_id: ID GPU устройства
        """
        self.max_usage_percent = max_usage_percent  # 99% для максимальной мощности
        self.device_id = device_id
        self.torch = None
        self.cuda_available = False
        
        # Блокировка для потокобезопасности
        self._lock = threading.Lock()
        
        # Статистика
        self._last_check_time = 0
        self._check_interval = 1.0  # Проверка каждую секунду
        
        # Инициализация PyTorch
        self._init_torch()
    
    def _init_torch(self):
        """Инициализация PyTorch для работы с GPU — ПОЛНАЯ МОЩНОСТЬ"""
        try:
            import torch
            self.torch = torch
            self.cuda_available = torch.cuda.is_available()
            
            if self.cuda_available:
                props = torch.cuda.get_device_properties(self.device_id)
                total_memory = props.total_memory
                max_memory = int(total_memory * self.max_usage_percent)
                
                torch.cuda.set_per_process_memory_fraction(self.max_usage_percent, self.device_id)
                
                # cuDNN: автоподбор алгоритма (10-30% ускорение конволюций)
                torch.backends.cudnn.enabled = True
                torch.backends.cudnn.benchmark = True
                
                # TF32 для Ampere+ GPU (RTX 30xx): ускорение matmul без потери точности
                if hasattr(torch.backends, 'cuda'):
                    if hasattr(torch.backends.cuda, 'matmul'):
                        torch.backends.cuda.matmul.allow_tf32 = True
                    if hasattr(torch.backends.cudnn, 'allow_tf32'):
                        torch.backends.cudnn.allow_tf32 = True
                
                # CUDA memory allocator: expandable segments для меньшей фрагментации
                import os
                os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True')
                
                logger.info(f"✅ GPU Memory Manager — ПОЛНАЯ МОЩНОСТЬ")
                logger.info(f"   GPU: {props.name} (cuda:{self.device_id})")
                logger.info(f"   VRAM: {max_memory / (1024**3):.2f} GB ({self.max_usage_percent*100:.0f}%)")
                logger.info(f"   cuDNN benchmark: ON")
                logger.info(f"   TF32 (Ampere): ON")
                logger.info(f"   FP16 Tensor Cores: READY")
            else:
                logger.warning("⚠️ CUDA недоступен — CPU mode")
                
        except ImportError:
            logger.warning("⚠️ PyTorch не установлен")
            self.cuda_available = False
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации GPU Manager: {e}")
            self.cuda_available = False
    
    def get_stats(self) -> Optional[GPUStats]:
        """
        Получить статистику использования GPU
        
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
                
                # Попытка получить температуру (может быть недоступна)
                temperature = None
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_id)
                    temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                except:
                    pass
                
                # Попытка получить утилизацию (может быть недоступна)
                utilization = None
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_id)
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle).gpu
                except:
                    pass
                
                return GPUStats(
                    total_memory_gb=total_memory_gb,
                    used_memory_gb=used_memory_gb,
                    free_memory_gb=free_memory_gb,
                    usage_percent=usage_percent,
                    temperature=temperature,
                    utilization_percent=utilization
                )
        except Exception as e:
            logger.error(f"Ошибка получения статистики GPU: {e}")
            return None
    
    def check_and_cleanup(self) -> bool:
        """
        Проверить использование GPU и очистить кэш при необходимости
        
        Returns:
            True если память была очищена
        """
        if not self.cuda_available or not self.torch:
            return False
        
        # Проверяем не слишком часто
        current_time = time.time()
        if current_time - self._last_check_time < self._check_interval:
            return False
        
        self._last_check_time = current_time
        
        stats = self.get_stats()
        if not stats:
            return False
        
        # Очищаем кэш только при критическом использовании (>95%)
        # При максимальной мощности используем всю память, очистка только при необходимости
        critical_threshold = 95.0  # Очистка только при >95%
        
        if stats.usage_percent > critical_threshold:
            logger.info(f"🧹 Критическое использование GPU: {stats.usage_percent:.1f}% - очистка кэша")
            
            with self._lock:
                # Очистка кэша PyTorch
                self.torch.cuda.empty_cache()
                self.torch.cuda.synchronize()
                
                # Проверяем снова
                new_stats = self.get_stats()
                if new_stats:
                    logger.info(f"✅ Кэш очищен. Текущее использование: {new_stats.usage_percent:.1f}%")
                    return True
        
        return False
    
    def reserve_memory(self, size_gb: float) -> bool:
        """
        Зарезервировать память на GPU (для планирования)
        
        Args:
            size_gb: Размер памяти в GB
            
        Returns:
            True если память доступна
        """
        if not self.cuda_available:
            return False
        
        stats = self.get_stats()
        if not stats:
            return False
        
        # Проверяем, что после резервирования не превысим лимит
        future_usage = stats.used_memory_gb + size_gb
        future_percent = (future_usage / stats.total_memory_gb) * 100
        
        if future_percent > (self.max_usage_percent * 100):
            logger.warning(f"⚠️ Недостаточно памяти GPU для резервирования {size_gb:.2f} GB")
            logger.warning(f"   Текущее использование: {stats.usage_percent:.1f}%")
            logger.warning(f"   После резервирования: {future_percent:.1f}% (лимит: {self.max_usage_percent*100:.1f}%)")
            return False
        
        return True
    
    def cleanup(self):
        """Принудительная очистка памяти GPU"""
        if not self.cuda_available or not self.torch:
            return
        
        with self._lock:
            logger.info("🧹 Принудительная очистка памяти GPU...")
            self.torch.cuda.empty_cache()
            self.torch.cuda.synchronize()
            
            stats = self.get_stats()
            if stats:
                logger.info(f"✅ Память очищена. Использование: {stats.usage_percent:.1f}%")


class GPUResourceManager:
    """
    Менеджер ресурсов GPU с автоматическим управлением
    МАКСИМАЛЬНОЕ использование GPU для ЭКОНЕТ
    """
    
    def __init__(self, max_usage_percent: float = 0.99, device_id: int = 0):
        """
        Инициализация менеджера ресурсов GPU
        
        Args:
            max_usage_percent: Максимальный процент использования (0.0-1.0)
            device_id: ID GPU устройства
        """
        self.max_usage_percent = max_usage_percent
        self.device_id = device_id
        self.memory_manager = GPUMemoryManager(max_usage_percent, device_id)
        
        # Настройки для оптимизации
        self.optimal_batch_size = None
        self.optimal_input_size = None
        
        # Инициализация оптимальных параметров
        self._calculate_optimal_params()
    
    def _calculate_optimal_params(self):
        """Вычисление оптимальных параметров на основе доступной памяти GPU"""
        if not self.memory_manager.cuda_available:
            # Для CPU используем стандартные значения
            self.optimal_batch_size = 1
            self.optimal_input_size = 640
            return
        
        stats = self.memory_manager.get_stats()
        if not stats:
            self.optimal_batch_size = 1
            self.optimal_input_size = 640
            return
        
        # Вычисляем оптимальный batch size на основе доступной памяти
        # Используем максимум памяти для максимальной производительности
        available_memory_gb = stats.free_memory_gb * 0.95  # 95% от доступной памяти
        
        # Оптимизация для максимальной мощности GPU
        # Примерная оценка: 1 кадр 640x640 требует ~0.1-0.2 GB на GPU
        if available_memory_gb >= 16:
            self.optimal_batch_size = 32  # Максимальный batch для большой памяти
            self.optimal_input_size = 640
        elif available_memory_gb >= 12:
            self.optimal_batch_size = 24
            self.optimal_input_size = 640
        elif available_memory_gb >= 8:
            self.optimal_batch_size = 16  # Увеличенный batch
            self.optimal_input_size = 640
        elif available_memory_gb >= 6:
            self.optimal_batch_size = 12
            self.optimal_input_size = 640
        elif available_memory_gb >= 4:
            self.optimal_batch_size = 8
            self.optimal_input_size = 640
        elif available_memory_gb >= 2:
            self.optimal_batch_size = 4
            self.optimal_input_size = 640
        else:
            self.optimal_batch_size = 2
            self.optimal_input_size = 640
        
        logger.info(f"✅ Оптимальные параметры GPU:")
        logger.info(f"   Batch size: {self.optimal_batch_size}")
        logger.info(f"   Input size: {self.optimal_input_size}")
        logger.info(f"   Доступная память: {available_memory_gb:.2f} GB")
    
    def get_optimal_batch_size(self) -> int:
        """Получить оптимальный размер батча"""
        # Периодически пересчитываем (вдруг память освободилась)
        self._calculate_optimal_params()
        return self.optimal_batch_size
    
    def get_optimal_input_size(self) -> int:
        """Получить оптимальный размер входного изображения"""
        return self.optimal_input_size
    
    def get_stats(self) -> Optional[GPUStats]:
        """Получить статистику GPU"""
        return self.memory_manager.get_stats()
    
    def check_and_cleanup(self) -> bool:
        """Проверить и очистить память при необходимости"""
        return self.memory_manager.check_and_cleanup()
    
    def cleanup(self):
        """Принудительная очистка памяти"""
        self.memory_manager.cleanup()
    
    def reserve_memory(self, size_gb: float) -> bool:
        """Зарезервировать память"""
        return self.memory_manager.reserve_memory(size_gb)


# Глобальный экземпляр менеджера GPU
_gpu_manager: Optional[GPUResourceManager] = None


def get_gpu_manager(device_id: int = 0, max_usage_percent: float = 0.99) -> GPUResourceManager:
    """
    Получить глобальный экземпляр менеджера GPU
    
    Args:
        device_id: ID GPU устройства
        max_usage_percent: Максимальный процент использования (0.0-1.0)
        
    Returns:
        GPUResourceManager
    """
    global _gpu_manager
    
    if _gpu_manager is None:
        _gpu_manager = GPUResourceManager(max_usage_percent=max_usage_percent, device_id=device_id)
    
    return _gpu_manager


def cleanup_gpu():
    """Глобальная очистка памяти GPU"""
    global _gpu_manager
    if _gpu_manager:
        _gpu_manager.cleanup()

