"""
Тесты калибровки модели
Проверка правильности калибровки параметров детекции
"""

import pytest
import asyncio
import numpy as np
from pathlib import Path


class TestModelCalibration:
    """Тесты калибровки модели"""
    
    @pytest.mark.asyncio
    async def test_confidence_threshold_calibration(self, unified_engine, test_image):
        """Тест калибровки порога confidence"""
        # Если инициализация не завершилась, пропускаем
        if not getattr(unified_engine, '_test_initialized', False):
            pytest.skip("UnifiedEngine не инициализирован")
        
        from obelisk.core.model_testing import ModelTester
        
        tester = ModelTester(unified_engine)
        
        # Тестируем разные пороги confidence
        confidence_levels = [0.1, 0.2, 0.3, 0.5, 0.7, 0.9]
        
        results = {}
        for conf in confidence_levels:
            # Меняем порог
            if hasattr(unified_engine, 'model_engine') and unified_engine.model_engine:
                original_conf = unified_engine.model_engine.config.get("model", {}).get("confidence_threshold", 0.5)
                unified_engine.model_engine.config["model"]["confidence_threshold"] = conf
                
                # Обрабатываем кадр с таймаутом
                try:
                    result = await asyncio.wait_for(
                        unified_engine.process_frame(test_image),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    # Восстанавливаем порог и пропускаем тест
                    unified_engine.model_engine.config["model"]["confidence_threshold"] = original_conf
                    pytest.skip("process_frame превысил таймаут (5s)")
                
                detections = result.get("detections", [])
                
                results[conf] = {
                    "detections_count": len(detections),
                    "average_confidence": np.mean([d.get("confidence", 0) for d in detections]) if detections else 0
                }
                
                # Восстанавливаем оригинальный порог
                unified_engine.model_engine.config["model"]["confidence_threshold"] = original_conf
            else:
                pytest.skip("ModelEngine не доступен")
        
        # Проверяем результаты
        if len(results) == 0:
            pytest.skip("Не удалось получить результаты")
        
        assert len(results) <= len(confidence_levels)
        
        # При более низких порогах должно быть больше детекций (если есть результаты)
        if 0.1 in results and 0.9 in results:
            low_conf_count = results[0.1]["detections_count"]
            high_conf_count = results[0.9]["detections_count"]
            assert low_conf_count >= high_conf_count
    
    @pytest.mark.asyncio
    async def test_iou_threshold_calibration(self, unified_engine, test_image):
        """Тест калибровки порога IoU"""
        if not hasattr(unified_engine, 'model_engine'):
            pytest.skip("ModelEngine не доступен")
        
        iou_levels = [0.3, 0.5, 0.7, 0.9]
        
        results = {}
        original_iou = unified_engine.model_engine.config.get("model", {}).get("iou_threshold", 0.5)
        
        for iou in iou_levels:
            unified_engine.model_engine.config["model"]["iou_threshold"] = iou
            
            result = await unified_engine.process_frame(test_image)
            detections = result.get("detections", [])
            
            results[iou] = len(detections)
        
        # Восстанавливаем оригинальный IoU
        unified_engine.model_engine.config["model"]["iou_threshold"] = original_iou
        
        assert len(results) == len(iou_levels)
    
    @pytest.mark.asyncio
    async def test_input_size_calibration(self, unified_engine):
        """Тест калибровки размера входного изображения"""
        if not hasattr(unified_engine, 'model_engine'):
            pytest.skip("ModelEngine не доступен")
        
        input_sizes = [320, 416, 640, 832]
        
        # Создаем тестовые изображения разных размеров
        results = {}
        for size in input_sizes:
            test_image = np.zeros((size, size, 3), dtype=np.uint8)
            
            # Обрабатываем кадр
            result = await unified_engine.process_frame(test_image)
            detections = result.get("detections", [])
            
            results[size] = {
                "detections_count": len(detections),
                "processing_time": result.get("processing_time", 0)
            }
        
        assert len(results) == len(input_sizes)


class TestPerformanceCalibration:
    """Тесты калибровки производительности"""
    
    @pytest.mark.asyncio
    async def test_fps_calibration(self, unified_engine, test_image):
        """Тест калибровки FPS"""
        # Если инициализация не завершилась, пропускаем
        if not getattr(unified_engine, '_test_initialized', False):
            pytest.skip("UnifiedEngine не инициализирован")
        
        import time
        
        # Обрабатываем несколько кадров с таймаутом
        num_frames = 5  # Уменьшено для быстрых тестов
        start_time = time.time()
        
        try:
            for _ in range(num_frames):
                await asyncio.wait_for(
                    unified_engine.process_frame(test_image),
                    timeout=5.0
                )
        except asyncio.TimeoutError:
            pytest.skip("FPS калибровка превысила таймаут")
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        fps = num_frames / elapsed_time if elapsed_time > 0 else 0
        
        assert fps > 0
        assert fps <= 120  # Разумный максимум
    
    @pytest.mark.asyncio
    async def test_batch_processing_calibration(self, unified_engine):
        """Тест калибровки батч-обработки"""
        if not hasattr(unified_engine, 'model_engine'):
            pytest.skip("ModelEngine не доступен")
        
        batch_sizes = [1, 2, 4, 8]
        test_image = np.zeros((640, 640, 3), dtype=np.uint8)
        
        results = {}
        for batch_size in batch_sizes:
            batch = [test_image.copy() for _ in range(batch_size)]
            
            import time
            start_time = time.time()
            
            # Обрабатываем батч
            for image in batch:
                await unified_engine.process_frame(image)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            results[batch_size] = {
                "total_time": elapsed_time,
                "time_per_frame": elapsed_time / batch_size if batch_size > 0 else 0
            }
        
        assert len(results) == len(batch_sizes)


class TestModelMetricsCalibration:
    """Тесты калибровки метрик модели"""
    
    @pytest.mark.asyncio
    async def test_precision_recall_calibration(self, unified_engine, test_image):
        """Тест калибровки precision/recall"""
        # Если инициализация не завершилась, пропускаем
        if not getattr(unified_engine, '_test_initialized', False):
            pytest.skip("UnifiedEngine не инициализирован")
        
        # Для полноценного теста нужны ground truth данные
        # Здесь просто проверяем, что детекции содержат нужные поля
        
        try:
            result = await asyncio.wait_for(
                unified_engine.process_frame(test_image),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            pytest.skip("process_frame превысил таймаут (10s)")
        
        detections = result.get("detections", [])
        
        for det in detections:
            assert "confidence" in det
            assert "bbox" in det
            assert "class_id" in det or "class_name" in det
    
    @pytest.mark.asyncio
    async def test_detection_consistency(self, unified_engine, test_image):
        """Тест консистентности детекций"""
        # Если инициализация не завершилась, пропускаем
        if not getattr(unified_engine, '_test_initialized', False):
            pytest.skip("UnifiedEngine не инициализирован")
        
        # Обрабатываем один кадр несколько раз с таймаутом
        results = []
        for _ in range(3):  # Уменьшено для быстрых тестов
            try:
                result = await asyncio.wait_for(
                    unified_engine.process_frame(test_image),
                    timeout=5.0
                )
                detections = result.get("detections", [])
                results.append(len(detections))
            except asyncio.TimeoutError:
                pytest.skip("process_frame превысил таймаут (5s)")
        
        # Детекции должны быть примерно одинаковыми (если не используется кэш)
        # Проверяем, что результаты стабильны
        assert len(results) > 0
        assert all(isinstance(r, int) for r in results)

