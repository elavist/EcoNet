"""
Тесты подключения GPU к нейронам
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from obelisk.neurons.perception.detection_neuron import DetectionNeuron
from obelisk.neurons.perception.tracking_neuron import TrackingNeuron
from obelisk.veins.gpu_circulatory import GPUCirculatorySystem
from obelisk.veins.gpu_distributor import GPUDistributor
from obelisk.veins.gpu_monitor import GPUMonitor


@pytest.fixture
def gpu_system():
    """Создание GPU системы"""
    circulatory = GPUCirculatorySystem()
    distributor = GPUDistributor(circulatory)
    monitor = GPUMonitor()
    return {
        "circulatory": circulatory,
        "distributor": distributor,
        "monitor": monitor
    }


@pytest.fixture
def mock_model_engine():
    """Мок ModelEngine"""
    engine = Mock()
    engine.detect = AsyncMock(return_value=[
        {
            "bbox": [100, 200, 150, 250],
            "confidence": 0.85,
            "class": 0
        }
    ])
    return engine


class TestDetectionNeuronGPU:
    """Тесты DetectionNeuron с GPU"""
    
    @pytest.mark.asyncio
    async def test_detection_neuron_with_gpu_monitor(self, gpu_system, mock_model_engine):
        """Тест DetectionNeuron с GPU монитором"""
        neuron = DetectionNeuron(
            model_engine=mock_model_engine,
            gpu_monitor=gpu_system["monitor"]
        )
        
        assert neuron.gpu_monitor is not None
        assert neuron.gpu_available is True or neuron.gpu_available is False
        
        # Тест обработки кадра
        context = {"frame": Mock()}
        result = await neuron.think(context)
        
        assert result["action"] == "detect"
        assert "gpu_available" in result
        assert "detections" in result
    
    @pytest.mark.asyncio
    async def test_detection_neuron_statistics(self, gpu_system, mock_model_engine):
        """Тест статистики DetectionNeuron"""
        neuron = DetectionNeuron(
            model_engine=mock_model_engine,
            gpu_monitor=gpu_system["monitor"]
        )
        
        # Обработка нескольких кадров
        for _ in range(3):
            context = {"frame": Mock()}
            await neuron.think(context)
        
        stats = neuron.get_statistics()
        
        assert stats["detections_count"] == 3
        assert "gpu_available" in stats
        assert "gpu_usage_count" in stats


class TestTrackingNeuronGPU:
    """Тесты TrackingNeuron с GPU"""
    
    @pytest.mark.asyncio
    async def test_tracking_neuron_with_gpu(self, gpu_system):
        """Тест TrackingNeuron с GPU системой"""
        neuron = TrackingNeuron(
            gpu_circulatory=gpu_system["circulatory"],
            gpu_distributor=gpu_system["distributor"],
            gpu_monitor=gpu_system["monitor"]
        )
        
        assert neuron.gpu_enabled is True
        assert neuron.gpu_circulatory is not None
        assert neuron.gpu_distributor is not None
        assert neuron.gpu_monitor is not None
        
        # Тест трекинга
        detections = [
            {
                "bbox": [100, 200, 150, 250],
                "confidence": 0.85,
                "class": 0
            }
        ]
        
        context = {
            "detections": detections,
            "frame_number": 1
        }
        
        result = await neuron.think(context)
        
        assert result["action"] == "track"
        assert "detections" in result
        assert "gpu_used" in result
    
    @pytest.mark.asyncio
    async def test_tracking_neuron_without_gpu(self):
        """Тест TrackingNeuron без GPU"""
        neuron = TrackingNeuron()
        
        assert neuron.gpu_enabled is False
        assert neuron.gpu_circulatory is None
        
        # Трекинг должен работать и без GPU
        detections = [
            {
                "bbox": [100, 200, 150, 250],
                "confidence": 0.85,
                "class": 0
            }
        ]
        
        context = {
            "detections": detections,
            "frame_number": 1
        }
        
        result = await neuron.think(context)
        
        assert result["action"] == "track"
        assert result["gpu_used"] is False
    
    @pytest.mark.asyncio
    async def test_tracking_neuron_statistics(self, gpu_system):
        """Тест статистики TrackingNeuron"""
        neuron = TrackingNeuron(
            gpu_circulatory=gpu_system["circulatory"],
            gpu_distributor=gpu_system["distributor"],
            gpu_monitor=gpu_system["monitor"]
        )
        
        # Обработка нескольких кадров
        for i in range(5):
            detections = [
                {
                    "bbox": [100 + i, 200 + i, 150 + i, 250 + i],
                    "confidence": 0.85,
                    "class": 0
                }
            ]
            context = {
                "detections": detections,
                "frame_number": i + 1
            }
            await neuron.think(context)
        
        stats = neuron.get_statistics()
        
        assert stats["frame_number"] == 5
        assert stats["gpu_enabled"] is True
        assert "track_statistics" in stats
        assert "gpu_stats" in stats or "gpu_circulatory_stats" in stats


class TestGPUSystemIntegration:
    """Тесты интеграции GPU системы"""
    
    @pytest.mark.asyncio
    async def test_gpu_circulatory_allocation(self, gpu_system):
        """Тест выделения GPU ресурсов"""
        circulatory = gpu_system["circulatory"]
        
        # Запрос GPU
        gpu_info = await circulatory.request_gpu(
            task_id="test_task",
            priority=8,
            memory_required=0.1
        )
        
        # GPU может быть недоступен в тестовой среде
        if gpu_info:
            assert "device" in gpu_info
            assert "device_id" in gpu_info
            
            # Освобождение
            await circulatory.release_gpu("test_task")
        
        stats = circulatory.get_statistics()
        assert "total_requests" in stats
        assert "successful_allocations" in stats
    
    def test_gpu_monitor_stats(self, gpu_system):
        """Тест мониторинга GPU"""
        monitor = gpu_system["monitor"]
        
        stats = monitor.get_gpu_stats()
        
        # GPU может быть недоступен
        if stats:
            assert "devices" in stats
            assert "timestamp" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

