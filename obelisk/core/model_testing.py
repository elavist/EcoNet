"""
Простой модуль тестирования модели
Интегрирован с нейронной архитектурой и GPU венозной системой
"""

import logging
import asyncio
import numpy as np
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ModelTester:
    """
    Простой класс для тестирования модели
    Интегрирован с нейронной архитектурой и GPU венозной системой
    """
    
    def __init__(self, unified_engine, gpu_circulatory=None):
        """
        Инициализация тестера
        
        Args:
            unified_engine: UnifiedEngine для обработки кадров
            gpu_circulatory: GPU венозная система (опционально)
        """
        self.unified_engine = unified_engine
        self.gpu_circulatory = gpu_circulatory
        self.test_results = []
    
    def is_model_loaded(self) -> bool:
        """
        Простая проверка: загружена ли модель
        
        Returns:
            True если модель загружена, False иначе
        """
        if not self.unified_engine:
            return False
        
        if not hasattr(self.unified_engine, 'model_engine'):
            return False
        
        model_engine = self.unified_engine.model_engine
        if not model_engine:
            return False
        
        if not hasattr(model_engine, 'models'):
            return False
        
        models = model_engine.models
        return bool(models and len(models) > 0)
    
    def get_model_info(self) -> Dict:
        """
        Получить информацию о модели
        
        Returns:
            Словарь с информацией о модели
        """
        info = {
            "loaded": False,
            "count": 0,
            "device": "unknown",
            "names": []
        }
        
        if not self.is_model_loaded():
            return info
        
        model_engine = self.unified_engine.model_engine
        models = model_engine.models
        
        info["loaded"] = True
        info["count"] = len(models)
        info["device"] = getattr(model_engine, 'device', 'unknown')
        info["names"] = list(models.keys())
        
        return info
    
    async def test_single_frame(self, use_gpu: bool = True, timeout: float = 5.0) -> Dict:
        """
        Простой тест: обработать один кадр
        Интегрирован с GPU венозной системой
        ИСПРАВЛЕНИЕ: Добавлен таймаут для предотвращения зависаний
        
        Args:
            use_gpu: Использовать GPU венозную систему для выделения ресурсов
            timeout: Таймаут для process_frame (по умолчанию 5 секунд)
        
        Returns:
            Результаты теста
        """
        result = {
            "success": False,
            "detections": 0,
            "error": None,
            "gpu_used": False
        }
        
        if not self.is_model_loaded():
            result["error"] = "Модель не загружена"
            return result
        
        gpu_info = None
        gpu_task_id = None
        
        try:
            # Запрос GPU через венозную систему (если доступна)
            if use_gpu and self.gpu_circulatory:
                try:
                    import time
                    gpu_task_id = f"model_test_{int(time.time())}"
                    gpu_info = await asyncio.wait_for(
                        self.gpu_circulatory.request_gpu(
                            gpu_task_id, priority=7, memory_required=0.1
                        ),
                        timeout=1.0  # Короткий таймаут для GPU запроса
                    )
                    if gpu_info:
                        result["gpu_used"] = True
                        logger.info(f"🩸 GPU выделен для теста модели: {gpu_info.get('device', 'unknown')}")
                except asyncio.TimeoutError:
                    logger.debug("GPU запрос превысил таймаут (1s), продолжаем без GPU")
                except Exception as e:
                    logger.debug(f"GPU недоступен для теста модели: {e}")
            
            # Создаем простой тестовый кадр
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # ИСПРАВЛЕНИЕ: Обрабатываем кадр с таймаутом для предотвращения зависаний
            try:
                output = await asyncio.wait_for(
                    self.unified_engine.process_frame(test_frame),
                    timeout=timeout
                )
                
                detections = output.get("detections", [])
                result["success"] = True
                result["detections"] = len(detections)
                
            except asyncio.TimeoutError:
                result["error"] = f"Таймаут обработки кадра ({timeout}s)"
                logger.warning(f"⏱️ Тест кадра превысил таймаут ({timeout}s)")
            except Exception as e:
                result["error"] = f"Ошибка process_frame: {str(e)}"
                logger.error(f"Ошибка теста кадра: {e}")
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Критическая ошибка теста кадра: {e}")
        
        finally:
            # Освобождение GPU
            if gpu_info and gpu_task_id and self.gpu_circulatory:
                try:
                    await asyncio.wait_for(
                        self.gpu_circulatory.release_gpu(gpu_task_id),
                        timeout=1.0
                    )
                except Exception:
                    pass
        
        return result
    
    def _create_test_frame(self, width: int = 640, height: int = 480) -> np.ndarray:
        """Создание тестового кадра"""
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        for y in range(height):
            intensity = int(255 * (y / height))
            frame[y, :] = [intensity // 3, intensity // 2, intensity]
        return frame
    
    def get_test_summary(self) -> str:
        """Получить краткую сводку тестов"""
        if not self.test_results:
            return "Тесты не выполнялись"
        
        summary = "Результаты тестирования:\n"
        for result in self.test_results:
            summary += f"- {result.get('test_name', 'Unknown')}: {result.get('status', 'Unknown')}\n"
        
        return summary
