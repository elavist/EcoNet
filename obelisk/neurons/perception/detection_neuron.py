"""
Нейрон детекции ЭкоНет
Детекция объектов на кадрах
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import ComponentState
from obelisk.veins.gpu_monitor import GPUMonitor

logger = logging.getLogger(__name__)


class DetectionNeuron(NeuralNode):
    """
    Нейрон детекции - обнаружение объектов
    Использует GPU через ModelEngine (YOLO)
    """
    
    def __init__(self, model_engine=None, gpu_monitor: Optional[GPUMonitor] = None):
        """
        Инициализация DetectionNeuron
        
        Args:
            model_engine: ModelEngine для детекции (использует GPU)
            gpu_monitor: GPU монитор для отслеживания использования
        """
        super().__init__("detection_neuron", "perception")
        self.model_engine = model_engine
        self.gpu_monitor = gpu_monitor
        self.detections_count = 0
        self.gpu_usage_count = 0
        self.state = ComponentState.READY
        
        # Проверка доступности GPU через model_engine
        self.gpu_available = False
        if model_engine:
            try:
                import torch
                self.gpu_available = torch.cuda.is_available()
            except:
                pass
        
        logger.info(f"🔍 DetectionNeuron создан (GPU: {'✅' if self.gpu_available else '❌'})")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Процесс мышления нейрона детекции
        
        Args:
            context: Контекст с кадром
        
        Returns:
            Мнение нейрона с детекциями
        """
        frame = context.get("frame")
        
        if frame is None:
            return {
                "action": "skip",
                "reason": "Нет кадра для детекции",
                "confidence": 0.0
            }
        
        if not self.model_engine:
            return {
                "action": "skip",
                "reason": "ModelEngine недоступен",
                "confidence": 0.0
            }
        
        try:
            # Мониторинг GPU перед детекцией
            gpu_stats_before = None
            if self.gpu_monitor:
                gpu_stats_before = self.gpu_monitor.get_gpu_stats()
            
            # Детекция через ModelEngine (использует GPU)
            detections = await self.model_engine.detect(frame)
            
            # Мониторинг GPU после детекции
            gpu_stats_after = None
            if self.gpu_monitor:
                gpu_stats_after = self.gpu_monitor.get_gpu_stats()
                if gpu_stats_after:
                    self.gpu_usage_count += 1
            
            self.detections_count += len(detections)
            
            result = {
                "action": "detect",
                "detections": detections,
                "detections_count": len(detections),
                "confidence": 0.9 if detections else 0.1,
                "total_detections": self.detections_count,
                "gpu_available": self.gpu_available
            }
            
            # Добавление информации о GPU если доступно
            if gpu_stats_after:
                result["gpu_stats"] = gpu_stats_after
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка детекции: {e}")
            return {
                "action": "error",
                "error": str(e),
                "confidence": 0.0
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики детекции"""
        stats = {
            "detections_count": self.detections_count,
            "gpu_available": self.gpu_available,
            "gpu_usage_count": self.gpu_usage_count
        }
        
        # Добавление статистики GPU если доступно
        if self.gpu_monitor:
            gpu_stats = self.gpu_monitor.get_gpu_stats()
            if gpu_stats:
                stats["gpu_stats"] = gpu_stats
        
        return stats

