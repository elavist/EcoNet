"""
Нейрон трекинга объектов ЭкоНет
Профессиональный трекинг окурков в реальном времени через ByteTrack
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import ComponentState
from obelisk.core.processors.byte_tracker import ByteTracker
from obelisk.veins.gpu_circulatory import GPUCirculatorySystem
from obelisk.veins.gpu_distributor import GPUDistributor
from obelisk.veins.gpu_monitor import GPUMonitor

logger = logging.getLogger(__name__)


class TrackingNeuron(NeuralNode):
    """
    Нейрон трекинга объектов - отслеживание окурков в реальном времени
    Использует ByteTrack для профессионального трекинга
    Подключен к GPU системе для оптимизации
    """
    
    def __init__(self, tracker_config: Optional[Dict[str, Any]] = None,
                 gpu_circulatory: Optional[GPUCirculatorySystem] = None,
                 gpu_distributor: Optional[GPUDistributor] = None,
                 gpu_monitor: Optional[GPUMonitor] = None):
        """
        Инициализация TrackingNeuron
        
        Args:
            tracker_config: Конфигурация трекера
            gpu_circulatory: GPU система кровообращения
            gpu_distributor: GPU распределитель
            gpu_monitor: GPU монитор
        """
        super().__init__("tracking_neuron", "perception")
        
        # GPU система
        self.gpu_circulatory = gpu_circulatory
        self.gpu_distributor = gpu_distributor
        self.gpu_monitor = gpu_monitor
        self.gpu_task_id = None
        self.gpu_enabled = gpu_circulatory is not None
        
        # Конфигурация трекера
        config = tracker_config or {}
        self.tracker = ByteTracker(
            frame_rate=config.get("frame_rate", 30),
            track_thresh=config.get("track_thresh", 0.5),
            high_thresh=config.get("high_thresh", 0.6),
            match_thresh=config.get("match_thresh", 0.8),
            track_buffer=config.get("track_buffer", 30),
            min_box_area=config.get("min_box_area", 10),
            mot_thresh=config.get("mot_thresh", 0.8)
        )
        
        self.tracked_objects_history = deque(maxlen=1000)
        self.frame_number = 0
        self.state = ComponentState.READY
        
        logger.info(f"🎯 TrackingNeuron создан (GPU: {'✅' if self.gpu_enabled else '❌'})")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Процесс мышления нейрона трекинга"""
        detections = context.get("detections", [])
        frame_number = context.get("frame_number", None)
        
        if not detections:
            return {
                "action": "skip",
                "reason": "Нет детекций для трекинга",
                "confidence": 0.0
            }
        
        try:
            # Запрос GPU ресурсов для трекинга (если доступно)
            gpu_info = None
            if self.gpu_enabled and self.gpu_circulatory:
                task_id = f"tracking_{self.frame_number}"
                gpu_info = await self.gpu_circulatory.request_gpu(
                    task_id=task_id,
                    priority=7,  # Высокий приоритет для трекинга
                    memory_required=0.05  # Трекинг требует мало памяти
                )
                if gpu_info:
                    self.gpu_task_id = task_id
            
            # Обновление трекера
            tracked_detections = self.tracker.update(detections, frame_number)
            
            if frame_number is not None:
                self.frame_number = frame_number
            else:
                self.frame_number += 1
            
            # Освобождение GPU после обработки
            if self.gpu_task_id and self.gpu_circulatory:
                await self.gpu_circulatory.release_gpu(self.gpu_task_id)
                self.gpu_task_id = None
            
            # Сохранение в историю
            self.tracked_objects_history.append({
                "frame_number": self.frame_number,
                "detections": tracked_detections,
                "timestamp": datetime.now(),
                "gpu_used": gpu_info is not None
            })
            
            # Отправка через нейронную сеть
            self.broadcast({
                "type": "tracked_detections",
                "data": {
                    "frame_number": self.frame_number,
                    "detections": tracked_detections,
                    "track_statistics": self.tracker.get_track_statistics(),
                    "gpu_info": gpu_info
                },
                "source": self.name
            })
            
            return {
                "action": "track",
                "detections": tracked_detections,
                "track_count": len([d for d in tracked_detections if d.get("tracked", False)]),
                "confidence": 0.9,
                "statistics": self.tracker.get_track_statistics(),
                "gpu_used": gpu_info is not None
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка трекинга: {e}", exc_info=True)
            
            # Освобождение GPU в случае ошибки
            if self.gpu_task_id and self.gpu_circulatory:
                await self.gpu_circulatory.release_gpu(self.gpu_task_id)
                self.gpu_task_id = None
            
            return {
                "action": "error",
                "error": str(e),
                "confidence": 0.0
            }
    
    def receive(self, data: Any, source: str = "unknown"):
        """Прием данных от других нейронов"""
        super().receive(data, source)
        
        # Если это детекции от Detection Neuron
        if isinstance(data, dict):
            if data.get("type") == "detections":
                detections = data.get("data", [])
                frame_number = data.get("frame_number")
                
                # Автоматическая обработка через think
                import asyncio
                context = {
                    "detections": detections,
                    "frame_number": frame_number
                }
                asyncio.create_task(self.think(context))
    
    def get_tracked_object(self, track_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о конкретном треке"""
        for entry in reversed(self.tracked_objects_history):
            for det in entry.get("detections", []):
                if det.get("track_id") == track_id:
                    return det
        return None
    
    def get_all_tracked_objects(self) -> List[Dict[str, Any]]:
        """Получить все активные треки"""
        if not self.tracked_objects_history:
            return []
        
        # Получаем последние детекции
        last_entry = self.tracked_objects_history[-1]
        return [det for det in last_entry.get("detections", []) if det.get("tracked", False)]
    
    def get_track_history(self, track_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить историю конкретного трека"""
        history = []
        for entry in reversed(self.tracked_objects_history):
            for det in entry.get("detections", []):
                if det.get("track_id") == track_id:
                    history.append({
                        "frame_number": entry["frame_number"],
                        "detection": det,
                        "timestamp": entry["timestamp"]
                    })
                    if len(history) >= limit:
                        return history
        return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики трекинга"""
        track_stats = self.tracker.get_track_statistics()
        
        stats = {
            "frame_number": self.frame_number,
            "track_statistics": track_stats,
            "history_size": len(self.tracked_objects_history),
            "active_tracks": len(self.get_all_tracked_objects()),
            "gpu_enabled": self.gpu_enabled
        }
        
        # Добавление статистики GPU если доступно
        if self.gpu_monitor:
            gpu_stats = self.gpu_monitor.get_gpu_stats()
            if gpu_stats:
                stats["gpu_stats"] = gpu_stats
        
        if self.gpu_circulatory:
            gpu_circ_stats = self.gpu_circulatory.get_statistics()
            stats["gpu_circulatory_stats"] = gpu_circ_stats
        
        return stats
    
    def reset(self):
        """Сброс трекера"""
        self.tracker.reset()
        self.tracked_objects_history.clear()
        self.frame_number = 0
        logger.info("🔄 TrackingNeuron сброшен")

