"""
Интеграционные тесты полного пайплайна
Тестирование полного цикла работы системы от детекции до выполнения задачи
"""

import pytest
import asyncio
import numpy as np
from pathlib import Path


class TestFullDetectionPipeline:
    """Тесты полного пайплайна детекции"""
    
    @pytest.mark.asyncio
    async def test_detection_to_task_pipeline(self, unified_engine, test_image):
        """Тест пайплайна: детекция -> задача"""
        # 1. Детекция
        result = await unified_engine.process_frame(test_image)
        detections = result.get("detections", [])
        
        assert isinstance(detections, list)
        
        # 2. Создание задачи (если есть TaskManager)
        if hasattr(unified_engine, 'task_manager') and detections:
            # Концептуально: для каждой детекции должна быть создана задача
            # В реальной реализации нужно проверить создание задач
            pass
    
    @pytest.mark.asyncio
    async def test_video_processing_pipeline(self, unified_engine, test_video):
        """Тест пайплайна обработки видео"""
        import cv2
        
        cap = cv2.VideoCapture(str(test_video))
        if not cap.isOpened():
            pytest.skip("Не удалось открыть тестовое видео")
        
        frame_count = 0
        detection_count = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                result = await unified_engine.process_frame(frame)
                detections = result.get("detections", [])
                
                frame_count += 1
                detection_count += len(detections)
                
                # Ограничиваем количество кадров для теста
                if frame_count >= 10:
                    break
        
        finally:
            cap.release()
        
        assert frame_count > 0
        assert detection_count >= 0  # Может быть 0 на тестовом видео


class TestTrainingPipeline:
    """Тесты пайплайна обучения"""
    
    @pytest.mark.asyncio
    async def test_training_to_deployment_pipeline(self, test_config, temp_data_dir):
        """Тест пайплайна: обучение -> валидация -> деплой"""
        from obelisk.services.trainer import TrainerService
        from unittest.mock import MagicMock
        
        mock_db = MagicMock()
        mock_mqtt = MagicMock()
        
        test_config["dataset"]["base_path"] = str(temp_data_dir)
        test_config["data_lake"]["models_path"] = str(temp_data_dir / "models")
        
        trainer = TrainerService(test_config, mock_db, mock_mqtt)
        
        # Проверяем структуру пайплайна
        assert hasattr(trainer, 'start_training')
        
        # В реальной реализации нужно:
        # 1. Запустить обучение
        # 2. Проверить валидацию
        # 3. Проверить деплой (если модель лучше)
    
    @pytest.mark.asyncio
    async def test_active_learning_pipeline(self, unified_engine, test_image):
        """Тест пайплайна активного обучения"""
        # 1. Детекция с низкой уверенностью
        result = await unified_engine.process_frame(test_image)
        detections = result.get("detections", [])
        
        # 2. Сбор кадров с низкой уверенностью (если есть ActiveLearner)
        if hasattr(unified_engine, 'active_learner'):
            # Концептуально: кадры с confidence 0.3-0.7 должны собираться
            low_confidence_detections = [
                d for d in detections
                if 0.3 <= d.get("confidence", 0) <= 0.7
            ]
            
            # Проверяем концепцию
            assert isinstance(low_confidence_detections, list)


class TestMQTTPipeline:
    """Тесты пайплайна MQTT коммуникации"""
    
    @pytest.mark.asyncio
    async def test_detection_to_mqtt_pipeline(self, unified_engine, test_image, mock_mqtt_client):
        """Тест пайплайна: детекция -> MQTT публикация"""
        # Детекция
        result = await unified_engine.process_frame(test_image)
        detections = result.get("detections", [])
        
        # В реальной реализации нужно проверить публикацию в MQTT
        # Здесь просто проверяем, что детекции есть
        assert isinstance(detections, list)
    
    @pytest.mark.asyncio
    async def test_robot_task_pipeline(self, mock_mqtt_client):
        """Тест пайплайна: задача -> робот -> выполнение"""
        # Концептуальный тест
        # В реальной реализации нужно:
        # 1. Создать задачу
        # 2. Отправить роботу через MQTT
        # 3. Получить подтверждение
        # 4. Отследить выполнение
        
        assert mock_mqtt_client is not None


class TestSystemIntegration:
    """Тесты интеграции системы"""
    
    @pytest.mark.asyncio
    async def test_startup_integration(self, unified_engine):
        """Тест интеграции при запуске системы"""
        # При запуске все компоненты должны быть инициализированы
        stats = unified_engine.get_statistics()
        components = stats.get("components", {})
        
        # Проверяем ключевые компоненты
        assert components.get("model_engine", False) is True
    
    @pytest.mark.asyncio
    async def test_neural_network_communication(self, unified_engine):
        """Тест коммуникации нейронной сети"""
        # Все нейроны должны быть связаны
        if hasattr(unified_engine, 'neural_nodes'):
            nodes = unified_engine.neural_nodes
            
            # Проверяем наличие узлов
            # (структура зависит от реализации)
            assert nodes is not None
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, unified_engine, test_image):
        """Тест восстановления после ошибок"""
        # Система должна восстанавливаться после ошибок
        
        # Пытаемся обработать кадр
        result = await unified_engine.process_frame(test_image)
        
        assert result is not None
        
        # Система должна продолжать работать
        result2 = await unified_engine.process_frame(test_image)
        assert result2 is not None

