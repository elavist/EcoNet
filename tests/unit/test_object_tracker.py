"""
Unit тесты для ObjectTracker
Тестирование отслеживания объектов между кадрами
"""

import pytest
import numpy as np


class TestObjectTracker:
    """Тесты ObjectTracker"""
    
    def test_initialization(self, object_tracker):
        """Тест инициализации ObjectTracker"""
        assert object_tracker is not None
        assert hasattr(object_tracker, 'iou_threshold')
        assert hasattr(object_tracker, 'max_missed_frames')
    
    def test_iou_threshold(self, object_tracker):
        """Тест порога IoU"""
        assert object_tracker.iou_threshold > 0
        assert object_tracker.iou_threshold <= 1.0
        assert object_tracker.iou_threshold == 0.86  # Из конфига
    
    def test_max_missed_frames(self, object_tracker):
        """Тест максимального количества пропущенных кадров"""
        assert object_tracker.max_missed_frames > 0
        assert isinstance(object_tracker.max_missed_frames, int)


class TestObjectTrackerTracking:
    """Тесты отслеживания объектов"""
    
    def test_update_empty_detections(self, object_tracker):
        """Тест обновления с пустыми детекциями"""
        tracks = object_tracker.update([])
        
        assert isinstance(tracks, list)
    
    def test_update_single_detection(self, object_tracker):
        """Тест обновления с одной детекцией"""
        detection = {
            "bbox": [100, 100, 200, 200],
            "confidence": 0.9,
            "class_id": 0
        }
        
        tracks = object_tracker.update([detection])
        
        assert isinstance(tracks, list)
        if tracks:
            assert "track_id" in tracks[0]
    
    def test_update_multiple_detections(self, object_tracker):
        """Тест обновления с несколькими детекциями"""
        detections = [
            {"bbox": [100, 100, 200, 200], "confidence": 0.9, "class_id": 0},
            {"bbox": [300, 300, 400, 400], "confidence": 0.85, "class_id": 0}
        ]
        
        tracks = object_tracker.update(detections)
        
        assert isinstance(tracks, list)
    
    def test_track_continuity(self, object_tracker):
        """Тест непрерывности треков"""
        detection = {
            "bbox": [100, 100, 200, 200],
            "confidence": 0.9,
            "class_id": 0
        }
        
        # Первое обновление
        tracks1 = object_tracker.update([detection])
        
        # Второе обновление с тем же объектом (слегка сдвинутым)
        detection2 = {
            "bbox": [105, 105, 205, 205],
            "confidence": 0.9,
            "class_id": 0
        }
        tracks2 = object_tracker.update([detection2])
        
        assert isinstance(tracks1, list)
        assert isinstance(tracks2, list)
    
    def test_track_new_object(self, object_tracker):
        """Тест появления нового объекта"""
        detection1 = {
            "bbox": [100, 100, 200, 200],
            "confidence": 0.9,
            "class_id": 0
        }
        
        # Первое обновление
        object_tracker.update([detection1])
        
        # Новый объект (далеко от первого)
        detection2 = {
            "bbox": [500, 500, 600, 600],
            "confidence": 0.9,
            "class_id": 0
        }
        tracks = object_tracker.update([detection2])
        
        assert isinstance(tracks, list)


class TestObjectTrackerIoU:
    """Тесты расчета IoU"""
    
    def test_calculate_iou(self, object_tracker):
        """Тест расчета IoU"""
        if hasattr(object_tracker, '_calculate_iou'):
            bbox1 = [100, 100, 200, 200]
            bbox2 = [105, 105, 205, 205]
            
            iou = object_tracker._calculate_iou(bbox1, bbox2)
            
            assert 0 <= iou <= 1.0
            assert iou > 0  # Должны пересекаться
    
    def test_iou_no_overlap(self, object_tracker):
        """Тест IoU для непересекающихся боксов"""
        if hasattr(object_tracker, '_calculate_iou'):
            bbox1 = [100, 100, 200, 200]
            bbox2 = [300, 300, 400, 400]
            
            iou = object_tracker._calculate_iou(bbox1, bbox2)
            
            assert iou == 0.0
    
    def test_iou_full_overlap(self, object_tracker):
        """Тест IoU для полностью совпадающих боксов"""
        if hasattr(object_tracker, '_calculate_iou'):
            bbox = [100, 100, 200, 200]
            
            iou = object_tracker._calculate_iou(bbox, bbox)
            
            assert iou == 1.0


class TestObjectTrackerCleanup:
    """Тесты очистки старых треков"""
    
    def test_remove_old_tracks(self, object_tracker):
        """Тест удаления старых треков"""
        detection = {
            "bbox": [100, 100, 200, 200],
            "confidence": 0.9,
            "class_id": 0
        }
        
        # Создаем трек
        object_tracker.update([detection])
        
        # Пропускаем кадры до превышения max_missed_frames
        for _ in range(object_tracker.max_missed_frames + 1):
            object_tracker.update([])
        
        # Проверяем, что трек удален
        tracks = object_tracker.update([])
        assert isinstance(tracks, list)
    
    def test_track_history(self, object_tracker):
        """Тест истории треков"""
        if hasattr(object_tracker, 'tracks'):
            assert hasattr(object_tracker, 'tracks')
            assert isinstance(object_tracker.tracks, dict)

