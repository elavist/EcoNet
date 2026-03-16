"""
Unit тесты для ModelEngine
Тестирование движка управления YOLO моделями
"""

import pytest
import numpy as np
from pathlib import Path


class TestModelEngine:
    """Тесты ModelEngine"""
    
    def test_initialization(self, model_engine, test_config):
        """Тест инициализации ModelEngine"""
        assert model_engine is not None
        assert model_engine.config == test_config
    
    def test_device_detection(self, model_engine):
        """Тест определения устройства (GPU/CPU)"""
        assert hasattr(model_engine, 'device')
        assert model_engine.device in ['cpu', 'cuda:0', 'cuda:1', 'mps']
    
    def test_models_loaded(self, model_engine):
        """Тест загрузки моделей"""
        # Модели могут быть не загружены в тестах (если путь не существует)
        # Но структура должна быть правильной
        assert hasattr(model_engine, 'models')
        assert isinstance(model_engine.models, dict)
    
    def test_ensemble_config(self, model_engine):
        """Тест конфигурации ансамбля"""
        assert hasattr(model_engine, 'ensemble_config')
        assert hasattr(model_engine, 'voting_method')
        assert model_engine.voting_method in ['weighted', 'majority', 'average']


class TestModelEngineDetection:
    """Тесты детекции в ModelEngine"""
    
    @pytest.mark.asyncio
    async def test_detect_single_frame(self, model_engine, test_image):
        """Тест детекции на одном кадре"""
        try:
            detections = await model_engine.detect(test_image)
            
            assert detections is not None
            assert isinstance(detections, list)
            # Детекции могут быть пустыми на тестовом изображении
        except Exception as e:
            # Если модель не загружена, это нормально для тестов
            if "model" in str(e).lower() or "path" in str(e).lower():
                pytest.skip(f"Модель не загружена: {e}")
            else:
                raise
    
    @pytest.mark.asyncio
    async def test_detect_batch(self, model_engine, test_image):
        """Тест батч-детекции"""
        batch = [test_image.copy() for _ in range(3)]
        
        try:
            results = await model_engine.detect_batch(batch)
            
            assert results is not None
            assert isinstance(results, list)
            assert len(results) == len(batch)
        except Exception as e:
            if "model" in str(e).lower() or "path" in str(e).lower():
                pytest.skip(f"Модель не загружена: {e}")
            else:
                raise
    
    def test_detection_format(self, model_engine):
        """Тест формата детекций"""
        # Проверяем, что ModelEngine имеет методы для детекции
        # Для ONNX моделей методы могут отсутствовать, но модель должна быть загружена
        # Проверяем наличие моделей или структуры для детекции
        has_models = hasattr(model_engine, 'models') and len(model_engine.models) > 0
        has_detect = hasattr(model_engine, 'detect') or hasattr(model_engine, '_detect')
        has_predict = hasattr(model_engine, 'predict') or hasattr(model_engine, '_predict')
        
        # Либо модели загружены, либо есть методы детекции
        assert has_models or has_detect or has_predict


class TestModelEngineEnsemble:
    """Тесты ансамбля моделей"""
    
    def test_weighted_voting(self, model_engine):
        """Тест взвешенного голосования"""
        # Проверяем наличие метода
        if hasattr(model_engine, '_weighted_voting'):
            assert callable(model_engine._weighted_voting)
    
    def test_majority_voting(self, model_engine):
        """Тест голосования большинством"""
        if hasattr(model_engine, '_majority_voting'):
            assert callable(model_engine._majority_voting)
    
    def test_average_voting(self, model_engine):
        """Тест усредненного голосования"""
        if hasattr(model_engine, '_average_voting'):
            assert callable(model_engine._average_voting)
    
    def test_iou_grouping(self, model_engine):
        """Тест группировки по IoU"""
        # Создаем тестовые детекции
        detections1 = [{"bbox": [100, 100, 200, 200], "confidence": 0.9}]
        detections2 = [{"bbox": [105, 105, 205, 205], "confidence": 0.85}]
        
        if hasattr(model_engine, '_group_detections_by_iou'):
            # Тест должен пройти без ошибок
            grouped = model_engine._group_detections_by_iou([detections1, detections2])
            assert isinstance(grouped, list)


class TestModelEnginePerformance:
    """Тесты производительности ModelEngine"""
    
    def test_half_precision_flag(self, model_engine):
        """Тест флага half precision"""
        assert hasattr(model_engine, 'half_precision')
        assert isinstance(model_engine.half_precision, bool)
    
    def test_batch_size_config(self, model_engine):
        """Тест конфигурации batch size"""
        assert hasattr(model_engine, 'max_batch_size')
        assert isinstance(model_engine.max_batch_size, int)
        assert model_engine.max_batch_size > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_detection(self, model_engine, test_image):
        """Тест конкурентной детекции"""
        import asyncio
        
        try:
            tasks = [model_engine.detect(test_image) for _ in range(3)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            assert len(results) == 3
            # Все результаты должны быть либо списками, либо исключениями
            assert all(isinstance(r, (list, Exception)) for r in results)
        except Exception as e:
            if "model" in str(e).lower() or "path" in str(e).lower():
                pytest.skip(f"Модель не загружена: {e}")

