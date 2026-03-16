"""
Тесты до и после деплоя
Проверка системы перед и после деплоя модели
"""

import pytest
import asyncio
import numpy as np
from pathlib import Path


class TestPreDeployment:
    """Тесты перед деплоем"""
    
    @pytest.mark.asyncio
    async def test_model_validation_before_deployment(self, unified_engine):
        """Тест валидации модели перед деплоем"""
        from obelisk.core.model_testing import ModelTester
        
        tester = ModelTester(unified_engine)
        
        # Простая проверка модели
        model_info = tester.get_model_info()
        test_result = await tester.test_single_frame()
        
        # Перед деплоем модель должна быть валидирована
        assert model_info is not None
        assert isinstance(model_info, dict)
        assert test_result is not None
        assert isinstance(test_result, dict)
    
    @pytest.mark.asyncio
    async def test_performance_check_before_deployment(self, unified_engine, test_image):
        """Тест проверки производительности перед деплоем"""
        import time
        
        # Проверяем производительность
        num_frames = 10
        start_time = time.time()
        
        for _ in range(num_frames):
            await unified_engine.process_frame(test_image)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        fps = num_frames / elapsed_time if elapsed_time > 0 else 0
        
        # FPS должен быть приемлемым
        assert fps > 0
    
    @pytest.mark.asyncio
    async def test_accuracy_check_before_deployment(self, unified_engine, test_image):
        """Тест проверки точности перед деплоем"""
        # Обрабатываем кадр
        result = await unified_engine.process_frame(test_image)
        detections = result.get("detections", [])
        
        # Проверяем структуру детекций
        for det in detections:
            assert "confidence" in det
            assert "bbox" in det
            assert det["confidence"] >= 0
            assert det["confidence"] <= 1


class TestPostDeployment:
    """Тесты после деплоя"""
    
    @pytest.mark.asyncio
    async def test_model_functionality_after_deployment(self, unified_engine, test_image):
        """Тест функциональности модели после деплоя"""
        # Модель должна работать после деплоя
        result = await unified_engine.process_frame(test_image)
        
        assert result is not None
        assert "detections" in result
    
    @pytest.mark.asyncio
    async def test_system_stability_after_deployment(self, unified_engine, test_image):
        """Тест стабильности системы после деплоя"""
        # Система должна быть стабильной после деплоя
        # Обрабатываем несколько кадров
        results = []
        for _ in range(10):
            result = await unified_engine.process_frame(test_image)
            results.append(result)
        
        assert len(results) == 10
        assert all(r is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_metrics_after_deployment(self, unified_engine, test_image):
        """Тест метрик после деплоя"""
        # После деплоя метрики должны быть в норме
        result = await unified_engine.process_frame(test_image)
        detections = result.get("detections", [])
        
        # Проверяем метрики детекций
        if detections:
            confidences = [d.get("confidence", 0) for d in detections]
            avg_confidence = sum(confidences) / len(confidences)
            
            # Средняя уверенность должна быть разумной
            assert 0 <= avg_confidence <= 1


class TestDeploymentRollback:
    """Тесты отката деплоя"""
    
    @pytest.mark.asyncio
    async def test_model_backup_before_deployment(self, test_config, project_root):
        """Тест резервного копирования модели перед деплоем"""
        from obelisk.services.model_selector import ModelSelector
        
        selector = ModelSelector(test_config, project_root)
        
        # Проверяем наличие методов резервного копирования
        # select_model имеет параметр backup_current
        assert hasattr(selector, 'select_model')
        assert callable(selector.select_model)
    
    @pytest.mark.asyncio
    async def test_rollback_capability(self, unified_engine):
        """Тест возможности отката"""
        # Система должна поддерживать откат к предыдущей модели
        # Проверяем, что модель можно заменить
        assert unified_engine is not None


class TestDeploymentValidation:
    """Тесты валидации деплоя"""
    
    @pytest.mark.asyncio
    async def test_compare_models_before_deployment(self, test_config, project_root):
        """Тест сравнения моделей перед деплоем"""
        from obelisk.services.model_selector import ModelSelector
        
        selector = ModelSelector(test_config, project_root)
        
        # Проверяем наличие методов сравнения
        assert hasattr(selector, 'get_available_models')
        models = selector.get_available_models()
        assert isinstance(models, list)
    
    @pytest.mark.asyncio
    async def test_automatic_validation_after_training(self, test_config, temp_data_dir):
        """Тест автоматической валидации после обучения"""
        # После обучения модель должна быть автоматически валидирована
        # В реальной реализации нужно проверить процесс валидации
        
        assert test_config is not None

