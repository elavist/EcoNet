"""
Модуль трекинга объектов с порогом совпадения 86%
Отслеживание объектов между кадрами для экономии ресурсов
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import deque
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """
    Вычисление IoU (Intersection over Union) между двумя боксами
    
    Args:
        box1: [x, y, w, h]
        box2: [x, y, w, h]
    
    Returns:
        IoU значение от 0 до 1
    """
    x1_1, y1_1, w1, h1 = box1
    x2_1, y2_1 = x1_1 + w1, y1_1 + h1
    
    x1_2, y1_2, w2, h2 = box2
    x2_2, y2_2 = x1_2 + w2, y1_2 + h2
    
    # Пересечение
    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)
    
    if xi2 <= xi1 or yi2 <= yi1:
        return 0.0
    
    inter_area = (xi2 - xi1) * (yi2 - yi1)
    
    # Объединение
    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area
    
    if union_area == 0:
        return 0.0
    
    return inter_area / union_area


class TrackedObject:
    """Отслеживаемый объект"""
    
    def __init__(self, track_id: int, bbox: List[float], confidence: float, 
                 class_id: int, frame_number: int):
        """
        Инициализация отслеживаемого объекта
        
        Args:
            track_id: Уникальный ID трека
            bbox: [x, y, w, h]
            confidence: Уверенность детекции
            class_id: ID класса
            frame_number: Номер кадра
        """
        self.track_id = track_id
        self.bbox = bbox  # [x, y, w, h]
        self.confidence = confidence
        self.class_id = class_id
        self.first_seen_frame = frame_number
        self.last_seen_frame = frame_number
        self.frames_count = 1
        self.bbox_history = deque([bbox], maxlen=10)  # История позиций
        self.confidence_history = deque([confidence], maxlen=10)
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # Средняя позиция для сглаживания
        self.avg_bbox = bbox.copy()
    
    def update(self, bbox: List[float], confidence: float, frame_number: int):
        """Обновление позиции объекта"""
        self.bbox = bbox
        self.confidence = confidence
        self.last_seen_frame = frame_number
        self.frames_count += 1
        self.last_updated = datetime.now()
        
        # Обновление истории
        self.bbox_history.append(bbox)
        self.confidence_history.append(confidence)
        
        # Вычисление средней позиции (простое сглаживание)
        if len(self.bbox_history) > 1:
            avg_x = sum(b[0] for b in self.bbox_history) / len(self.bbox_history)
            avg_y = sum(b[1] for b in self.bbox_history) / len(self.bbox_history)
            avg_w = sum(b[2] for b in self.bbox_history) / len(self.bbox_history)
            avg_h = sum(b[3] for b in self.bbox_history) / len(self.bbox_history)
            self.avg_bbox = [avg_x, avg_y, avg_w, avg_h]
        else:
            self.avg_bbox = bbox.copy()
    
    def predict_next_bbox(self) -> List[float]:
        """Предсказание следующей позиции (простая экстраполяция)"""
        if len(self.bbox_history) < 2:
            return self.bbox.copy()
        
        # Простая линейная экстраполяция
        prev_bbox = list(self.bbox_history[-2])
        curr_bbox = list(self.bbox_history[-1])
        
        dx = curr_bbox[0] - prev_bbox[0]
        dy = curr_bbox[1] - prev_bbox[1]
        
        predicted = [
            curr_bbox[0] + dx,
            curr_bbox[1] + dy,
            curr_bbox[2],
            curr_bbox[3]
        ]
        
        return predicted


class ObjectTracker:
    """
    Трекер объектов с порогом совпадения 86% (IoU > 0.86)
    Запоминает и отслеживает объекты между кадрами
    """
    
    def __init__(self, iou_threshold: float = 0.86, max_missed_frames: int = 5):
        """
        Инициализация трекера
        
        Args:
            iou_threshold: Порог IoU для совпадения (по умолчанию 0.86 = 86%)
            max_missed_frames: Максимальное количество пропущенных кадров до удаления трека
        """
        self.iou_threshold = iou_threshold
        self.max_missed_frames = max_missed_frames
        self.tracked_objects: Dict[int, TrackedObject] = {}
        self.next_track_id = 1
        self.frame_number = 0
    
    def update(self, detections: List[Dict], frame_number: Optional[int] = None) -> List[Dict]:
        """
        Обновление трекеров на основе новых детекций
        
        Args:
            detections: Список детекций [{"bbox": [x,y,w,h], "confidence": float, "class": int}, ...]
            frame_number: Номер кадра
        
        Returns:
            Детекции с добавленными track_id
        """
        if frame_number is None:
            frame_number = self.frame_number
        else:
            self.frame_number = frame_number
        
        # Увеличиваем счетчик пропущенных кадров для всех существующих треков
        tracks_to_remove = []
        for track_id, track in self.tracked_objects.items():
            missed_frames = frame_number - track.last_seen_frame
            if missed_frames > self.max_missed_frames:
                tracks_to_remove.append(track_id)
        
        # Удаляем старые треки
        for track_id in tracks_to_remove:
            del self.tracked_objects[track_id]
            logger.debug(f"🗑️ Удален трек {track_id} (пропущено {self.max_missed_frames} кадров)")
        
        # Сопоставление детекций с существующими треками
        matched_detections = set()
        matched_tracks = set()
        
        # Матрица IoU между треками и детекциями
        if detections and self.tracked_objects:
            iou_matrix = np.zeros((len(self.tracked_objects), len(detections)))
            
            track_ids = list(self.tracked_objects.keys())
            for i, track_id in enumerate(track_ids):
                track = self.tracked_objects[track_id]
                # Используем предсказанную позицию для сопоставления
                predicted_bbox = track.predict_next_bbox()
                
                for j, det in enumerate(detections):
                    iou = calculate_iou(predicted_bbox, det['bbox'])
                    iou_matrix[i, j] = iou
            
            # Жадное сопоставление (greedy matching)
            while True:
                # Находим максимальный IoU
                max_iou = np.max(iou_matrix)
                if max_iou < self.iou_threshold:
                    break
                
                # Находим индексы максимального IoU
                track_idx, det_idx = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)
                
                # Сопоставляем трек и детекцию
                track_id = track_ids[track_idx]
                det = detections[det_idx]
                
                # Обновляем трек
                self.tracked_objects[track_id].update(
                    det['bbox'],
                    det.get('confidence', 0.0),
                    frame_number
                )
                
                # Добавляем track_id к детекции
                det['track_id'] = track_id
                det['tracked'] = True
                
                matched_detections.add(det_idx)
                matched_tracks.add(track_idx)
                
                # Удаляем строку и столбец из матрицы
                iou_matrix[track_idx, :] = 0
                iou_matrix[:, det_idx] = 0
        
        # Создаем новые треки для несопоставленных детекций
        for i, det in enumerate(detections):
            if i not in matched_detections:
                track_id = self.next_track_id
                self.next_track_id += 1
                
                new_track = TrackedObject(
                    track_id,
                    det['bbox'],
                    det.get('confidence', 0.0),
                    det.get('class', 0),
                    frame_number
                )
                
                self.tracked_objects[track_id] = new_track
                det['track_id'] = track_id
                det['tracked'] = False  # Новый трек
                
                logger.debug(f"🆕 Создан новый трек {track_id}")
        
        # Возвращаем детекции с track_id (все детекции уже имеют track_id)
        return detections
    
    def get_track_statistics(self) -> Dict:
        """Получить статистику треков"""
        if not self.tracked_objects:
            return {
                "active_tracks": 0,
                "total_tracks": self.next_track_id - 1,
                "avg_frames_per_track": 0
            }
        
        avg_frames = sum(t.frames_count for t in self.tracked_objects.values()) / len(self.tracked_objects)
        
        return {
            "active_tracks": len(self.tracked_objects),
            "total_tracks": self.next_track_id - 1,
            "avg_frames_per_track": avg_frames
        }
    
    def reset(self):
        """Сброс трекера"""
        self.tracked_objects.clear()
        self.next_track_id = 1
        self.frame_number = 0
        logger.info("🔄 Трекер сброшен")

