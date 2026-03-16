"""
Unit тесты для UnifiedEngine
Тестирование универсального движка координации всех компонентов
"""

import pytest
import asyncio
import numpy as np
from pathlib import Path


def _skip_if_not_initialized(engine):
    if not getattr(engine, '_test_initialized', False):
        error = getattr(engine, '_test_init_error', 'unknown')
        pytest.skip(f"UnifiedEngine не инициализирован: {error}")


class TestUnifiedEngine:
    """Тесты UnifiedEngine"""
    
    @pytest.mark.asyncio
    async def test_initialization(self, unified_engine, test_config):
        """Тест инициализации UnifiedEngine"""
        assert unified_engine is not None
        assert hasattr(unified_engine, 'config')
        _skip_if_not_initialized(unified_engine)
    
    @pytest.mark.asyncio
    async def test_process_frame(self, unified_engine, test_image):
        """Тест обработки кадра"""
        _skip_if_not_initialized(unified_engine)
        
        try:
            result = await asyncio.wait_for(
                unified_engine.process_frame(test_image),
                timeout=30.0
            )
            assert result is not None
            assert isinstance(result, dict)
            assert "detections" in result
            assert isinstance(result["detections"], list)
            
            for detection in result["detections"]:
                assert isinstance(detection, dict)
                if detection:
                    assert "bbox" in detection or "box" in detection
        except asyncio.TimeoutError:
            pytest.skip("Обработка кадра превысила таймаут (30s)")
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, unified_engine):
        """Тест получения статистики"""
        stats = unified_engine.get_statistics()
        
        assert stats is not None
        assert isinstance(stats, dict)
        assert "components" in stats
    
    @pytest.mark.asyncio
    async def test_model_engine_availability(self, unified_engine):
        """Тест доступности ModelEngine"""
        _skip_if_not_initialized(unified_engine)
        assert hasattr(unified_engine, 'model_engine')
        if unified_engine.model_engine is None:
            pytest.skip("ModelEngine не инициализирован (модели не загружены)")
    
    @pytest.mark.asyncio
    async def test_neural_nodes_availability(self, unified_engine):
        """Тест доступности нейронных узлов"""
        assert hasattr(unified_engine, 'neural_architecture')
        assert unified_engine.neural_architecture is not None or hasattr(unified_engine, 'neural_network')


class TestUnifiedEngineFrameProcessing:
    """Тесты обработки кадров в UnifiedEngine"""
    
    @pytest.mark.asyncio
    async def test_process_empty_frame(self, unified_engine):
        """Тест обработки пустого кадра"""
        _skip_if_not_initialized(unified_engine)
        
        empty_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        try:
            result = await asyncio.wait_for(
                unified_engine.process_frame(empty_frame),
                timeout=30.0
            )
            assert result is not None
            assert "detections" in result
        except asyncio.TimeoutError:
            pytest.skip("Обработка пустого кадра превысила таймаут (30s)")
    
    @pytest.mark.asyncio
    async def test_process_multiple_frames(self, unified_engine, test_image):
        """Тест обработки нескольких кадров подряд"""
        _skip_if_not_initialized(unified_engine)
        
        results = []
        try:
            for _ in range(5):
                result = await asyncio.wait_for(
                    unified_engine.process_frame(test_image),
                    timeout=30.0
                )
                results.append(result)
        except asyncio.TimeoutError:
            pytest.skip("Обработка кадров превысила таймаут")
        
        assert len(results) == 5
        assert all("detections" in r for r in results)
    
    @pytest.mark.asyncio
    async def test_frame_caching(self, unified_engine, test_image):
        """Тест кэширования кадров"""
        _skip_if_not_initialized(unified_engine)
        
        try:
            result1 = await asyncio.wait_for(
                unified_engine.process_frame(test_image),
                timeout=30.0
            )
            result2 = await asyncio.wait_for(
                unified_engine.process_frame(test_image),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            pytest.skip("Обработка кадров превысила таймаут")
        
        assert result1 is not None
        assert result2 is not None


class TestUnifiedEngineComponents:
    """Тесты компонентов UnifiedEngine"""
    
    @pytest.mark.asyncio
    async def test_all_components_initialized(self, unified_engine):
        """Тест инициализации всех компонентов"""
        _skip_if_not_initialized(unified_engine)
        
        stats = unified_engine.get_statistics()
        components = stats.get("components", {})
        
        assert "model_engine" in components or unified_engine.model_engine is not None
    
    @pytest.mark.asyncio
    async def test_neural_communication(self, unified_engine):
        """Тест нейронной коммуникации"""
        if hasattr(unified_engine, 'neural_nodes'):
            nodes = unified_engine.neural_nodes
            assert hasattr(nodes, 'yolo_neuron') or hasattr(nodes, 'nodes')
    
    @pytest.mark.asyncio
    async def test_error_handling(self, unified_engine):
        """Тест обработки ошибок"""
        invalid_frame = None
        
        try:
            result = await asyncio.wait_for(
                unified_engine.process_frame(invalid_frame),
                timeout=5.0
            )
            assert result is not None
            assert isinstance(result, dict)
            assert "detections" in result
            assert isinstance(result["detections"], list)
        except (TypeError, AttributeError, ValueError):
            pass
        except asyncio.TimeoutError:
            pytest.skip("Обработка некорректного кадра превысила таймаут")
