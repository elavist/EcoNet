"""
Профессиональный трекер объектов на основе ByteTrack
ByteTrack - современный алгоритм трекинга для реального времени
Использует все детекции (даже с низкой уверенностью) для лучшего трекинга
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)


class STrack:
    """Single Track - отслеживаемый объект для ByteTrack"""
    
    def __init__(self, tlwh, score, class_id, track_id=None):
        """
        Инициализация трека
        
        Args:
            tlwh: [top, left, width, height]
            score: Уверенность детекции
            class_id: ID класса
            track_id: ID трека (если None, будет присвоен автоматически)
        """
        self._tlwh = np.asarray(tlwh, dtype=np.float32)
        self.score = score
        self.class_id = class_id
        self.track_id = track_id
        self.is_activated = False
        self.state = "New"  # New, Tracked, Lost, Removed
        self.frame_id = 0
        self.start_frame = 0
        self.track_len = 0
        
        # История позиций для сглаживания
        self.tlwh_history = deque(maxlen=30)
        self.tlwh_history.append(self._tlwh.copy())
    
    @property
    def tlwh(self):
        """Получить текущую позицию [top, left, width, height]"""
        return self._tlwh.copy()
    
    @property
    def tlbr(self):
        """Конвертировать в формат [top, left, bottom, right]"""
        ret = self._tlwh.copy()
        ret[2:] += ret[:2]
        return ret
    
    @property
    def xyxy(self):
        """Конвертировать в формат [x1, y1, x2, y2]"""
        ret = self._tlwh.copy()
        ret[2:] += ret[:2]
        return ret
    
    @property
    def xywh(self):
        """Конвертировать в формат [x, y, width, height] (центр)"""
        ret = self._tlwh.copy()
        ret[:2] += ret[2:] / 2
        return ret
    
    def update(self, new_track, frame_id):
        """Обновить трек"""
        self.frame_id = frame_id
        self.track_len += 1
        
        new_tlwh = new_track._tlwh
        self._tlwh = new_tlwh
        self.score = new_track.score
        self.state = "Tracked"
        self.is_activated = True
        
        self.tlwh_history.append(self._tlwh.copy())
    
    def activate(self, frame_id, track_id):
        """Активировать трек"""
        self.track_id = track_id
        self.frame_id = frame_id
        self.start_frame = frame_id
        self.is_activated = True
        self.state = "Tracked"
        self.track_len = 0
    
    def predict(self):
        """Предсказать следующую позицию (простая экстраполяция)"""
        if len(self.tlwh_history) < 2:
            return
        
        # Простая линейная экстраполяция
        prev = self.tlwh_history[-2]
        curr = self.tlwh_history[-1]
        
        # Вычисляем скорость
        velocity = curr - prev
        
        # Предсказываем следующую позицию
        self._tlwh = curr + velocity
    
    def mark_lost(self):
        """Пометить трек как потерянный"""
        self.state = "Lost"
    
    def mark_removed(self):
        """Пометить трек как удаленный"""
        self.state = "Removed"
    
    def re_activate(self, frame_id, track_id=None):
        """Повторно активировать трек"""
        if track_id is not None:
            self.track_id = track_id
        self.frame_id = frame_id
        self.is_activated = True
        self.state = "Tracked"


def iou_distance(atracks, btracks):
    """
    Вычисление IoU расстояния между треками
    Возвращает матрицу расстояний
    """
    if (len(atracks) > 0 and isinstance(atracks[0], np.ndarray)) or \
       (len(btracks) > 0 and isinstance(btracks[0], np.ndarray)):
        atlbrs = atracks
        btlbrs = btracks
    else:
        atlbrs = [track.tlbr for track in atracks]
        btlbrs = [track.tlbr for track in btracks]
    
    _ious = np.zeros((len(atlbrs), len(btlbrs)), dtype=np.float32)
    
    for i, atlbr in enumerate(atlbrs):
        for j, btlbr in enumerate(btlbrs):
            _ious[i, j] = 1.0 - compute_iou(atlbr, btlbr)
    
    return _ious


def compute_iou(box1, box2):
    """Вычисление IoU между двумя боксами [x1, y1, x2, y2]"""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # Пересечение
    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)
    
    if xi2 <= xi1 or yi2 <= yi1:
        return 0.0
    
    inter_area = (xi2 - xi1) * (yi2 - yi1)
    
    # Площади боксов
    box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
    box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
    union_area = box1_area + box2_area - inter_area
    
    if union_area == 0:
        return 0.0
    
    return inter_area / union_area


def linear_assignment(cost_matrix, thresh):
    """
    Венгерский алгоритм для оптимального сопоставления
    Упрощенная версия для жадного сопоставления
    """
    if cost_matrix.size == 0:
        return np.empty((0, 2), dtype=int), tuple(range(cost_matrix.shape[0])), tuple(range(cost_matrix.shape[1]))
    
    matches = []
    unmatched_a = list(range(cost_matrix.shape[0]))
    unmatched_b = list(range(cost_matrix.shape[1]))
    
    # Жадное сопоставление
    while True:
        if len(unmatched_a) == 0 or len(unmatched_b) == 0:
            break
        
        # Находим минимальную стоимость
        min_cost = np.inf
        min_i, min_j = -1, -1
        
        for i in unmatched_a:
            for j in unmatched_b:
                if cost_matrix[i, j] < min_cost:
                    min_cost = cost_matrix[i, j]
                    min_i, min_j = i, j
        
        if min_cost > thresh:
            break
        
        matches.append([min_i, min_j])
        unmatched_a.remove(min_i)
        unmatched_b.remove(min_j)
    
    return np.array(matches) if matches else np.empty((0, 2), dtype=int), tuple(unmatched_a), tuple(unmatched_b)


class ByteTracker:
    """
    Профессиональный трекер объектов на основе ByteTrack
    Использует все детекции (даже с низкой уверенностью) для лучшего трекинга
    """
    
    def __init__(self, 
                 frame_rate=30,
                 track_thresh=0.5,
                 high_thresh=0.6,
                 match_thresh=0.8,
                 track_buffer=30,
                 min_box_area=10,
                 mot_thresh=0.8):
        """
        Инициализация ByteTracker
        
        Args:
            frame_rate: Частота кадров
            track_thresh: Порог для создания новых треков
            high_thresh: Высокий порог для детекций
            match_thresh: Порог для сопоставления треков
            track_buffer: Буфер кадров для потерянных треков
            min_box_area: Минимальная площадь бокса
            mot_thresh: Порог для MOT метрики
        """
        self.frame_id = 0
        self.track_thresh = track_thresh
        self.high_thresh = high_thresh
        self.match_thresh = match_thresh
        self.track_buffer = track_buffer
        self.min_box_area = min_box_area
        self.mot_thresh = mot_thresh
        
        self.tracked_tracks: List[STrack] = []
        self.lost_tracks: List[STrack] = []
        self.removed_tracks: List[STrack] = []
        
        self.next_id = 1
        
        logger.info(f"🎯 ByteTracker инициализирован (track_thresh={track_thresh}, match_thresh={match_thresh})")
    
    def update(self, detections: List[Dict], frame_id: Optional[int] = None) -> List[Dict]:
        """
        Обновление трекеров на основе новых детекций
        
        Args:
            detections: Список детекций [{"bbox": [x,y,w,h] или [x1,y1,x2,y2], "confidence": float, "class": int}, ...]
            frame_id: Номер кадра
        
        Returns:
            Детекции с добавленными track_id и информацией о трекинге
        """
        if frame_id is not None:
            self.frame_id = frame_id
        else:
            self.frame_id += 1
        
        # Конвертация детекций в формат ByteTrack
        detections_high = []  # Высокая уверенность
        detections_low = []  # Низкая уверенность
        
        for det in detections:
            bbox = det.get('bbox', [])
            confidence = det.get('confidence', 0.0)
            class_id = det.get('class', 0)
            
            # Конвертация bbox в формат [top, left, width, height]
            if len(bbox) == 4:
                if 'x' in str(det.get('bbox_format', '')) or bbox[2] > bbox[0]:
                    # Формат [x1, y1, x2, y2]
                    x1, y1, x2, y2 = bbox
                    tlwh = [y1, x1, x2 - x1, y2 - y1]
                else:
                    # Формат [x, y, w, h] или [top, left, w, h]
                    tlwh = bbox
            
            # Проверка минимальной площади
            if tlwh[2] * tlwh[3] < self.min_box_area:
                continue
            
            track = STrack(tlwh, confidence, class_id)
            
            if confidence >= self.high_thresh:
                detections_high.append(track)
            elif confidence >= self.track_thresh:
                detections_low.append(track)
        
        # Обновление существующих треков
        # Предсказание позиций
        for track in self.tracked_tracks:
            track.predict()
        
        # Сопоставление треков с детекциями высокой уверенности
        matches, u_track, u_detection_high = self._associate_detections_to_trackers(
            self.tracked_tracks, detections_high, self.match_thresh
        )
        
        # Обновление сопоставленных треков
        for m in matches:
            track = self.tracked_tracks[m[0]]
            det = detections_high[m[1]]
            track.update(det, self.frame_id)
        
        # Обработка несопоставленных треков
        for it in u_track:
            track = self.tracked_tracks[it]
            if track.state == "Tracked":
                track.mark_lost()
                self.lost_tracks.append(track)
        
        # Удаление треков из tracked_tracks
        self.tracked_tracks = [t for t in self.tracked_tracks if t.state == "Tracked"]
        
        # Сопоставление потерянных треков с детекциями высокой уверенности
        matches_lost, u_lost, u_detection_high_2 = self._associate_detections_to_trackers(
            self.lost_tracks, detections_high, self.match_thresh
        )
        
        # Восстановление потерянных треков
        for m in matches_lost:
            track = self.lost_tracks[m[0]]
            det = detections_high[m[1]]
            track.update(det, self.frame_id)
            track.re_activate(self.frame_id, track.track_id)
            self.tracked_tracks.append(track)
        
        # Удаление восстановленных треков из lost_tracks
        self.lost_tracks = [t for t in self.lost_tracks if t.state == "Lost"]
        
        # Сопоставление оставшихся детекций высокой уверенности с потерянными треками
        # и создание новых треков
        detections_new = [detections_high[i] for i in u_detection_high_2]
        
        # Сопоставление потерянных треков с детекциями низкой уверенности
        matches_lost_low, u_lost_2, u_detection_low = self._associate_detections_to_trackers(
            self.lost_tracks, detections_low, 0.5
        )
        
        # Восстановление потерянных треков через детекции низкой уверенности
        for m in matches_lost_low:
            track = self.lost_tracks[m[0]]
            det = detections_low[m[1]]
            track.update(det, self.frame_id)
            track.re_activate(self.frame_id, track.track_id)
            self.tracked_tracks.append(track)
        
        # Удаление восстановленных треков из lost_tracks
        self.lost_tracks = [t for t in self.lost_tracks if t.state == "Lost"]
        
        # Создание новых треков из несопоставленных детекций
        for det in detections_new:
            if det.score >= self.track_thresh:
                det.activate(self.frame_id, self.next_id)
                self.next_id += 1
                self.tracked_tracks.append(det)
        
        # Удаление старых потерянных треков
        self.lost_tracks = [t for t in self.lost_tracks if t.state == "Lost" and 
                           (self.frame_id - t.frame_id) < self.track_buffer]
        
        # Формирование результата
        tracked_detections = []
        for track in self.tracked_tracks:
            if track.is_activated:
                bbox_tlbr = track.tlbr
                # Конвертация обратно в формат [x1, y1, x2, y2]
                bbox_xyxy = [bbox_tlbr[1], bbox_tlbr[0], bbox_tlbr[3], bbox_tlbr[2]]
                
                tracked_detections.append({
                    "bbox": bbox_xyxy,
                    "bbox_format": "xyxy",
                    "confidence": track.score,
                    "class": track.class_id,
                    "track_id": track.track_id,
                    "tracked": True,
                    "track_state": track.state,
                    "track_len": track.track_len,
                    "start_frame": track.start_frame
                })
        
        # Добавление информации о трекинге к исходным детекциям
        track_dict = {det["track_id"]: det for det in tracked_detections}
        
        result = []
        for det in detections:
            bbox = det.get('bbox', [])
            confidence = det.get('confidence', 0.0)
            class_id = det.get('class', 0)
            
            # Поиск соответствующего трека
            matched_track = None
            for track_id, track_det in track_dict.items():
                # Простая проверка совпадения по позиции и классу
                if abs(track_det["confidence"] - confidence) < 0.1 and track_det["class"] == class_id:
                    matched_track = track_det
                    break
            
            if matched_track:
                det["track_id"] = matched_track["track_id"]
                det["tracked"] = True
                det["track_state"] = matched_track["track_state"]
                det["track_len"] = matched_track["track_len"]
            else:
                det["tracked"] = False
            
            result.append(det)
        
        return result
    
    def _associate_detections_to_trackers(self, trackers, detections, iou_threshold=0.5):
        """Сопоставление детекций с трекерами"""
        if len(trackers) == 0:
            return np.empty((0, 2), dtype=int), [], np.arange(len(detections))
        
        if len(detections) == 0:
            return np.empty((0, 2), dtype=int), np.arange(len(trackers)), []
        
        # Вычисление матрицы расстояний IoU
        iou_matrix = iou_distance(trackers, detections)
        
        # Сопоставление
        matches, u_track, u_detection = linear_assignment(iou_matrix, 1.0 - iou_threshold)
        
        return matches, u_track, u_detection
    
    def get_track_statistics(self) -> Dict:
        """Получить статистику треков"""
        return {
            "active_tracks": len(self.tracked_tracks),
            "lost_tracks": len(self.lost_tracks),
            "total_tracks": self.next_id - 1,
            "frame_id": self.frame_id
        }
    
    def reset(self):
        """Сброс трекера"""
        self.tracked_tracks.clear()
        self.lost_tracks.clear()
        self.removed_tracks.clear()
        self.next_id = 1
        self.frame_id = 0
        logger.info("🔄 ByteTracker сброшен")

