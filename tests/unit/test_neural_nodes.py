"""
Unit тесты для нейронных узлов тестового движка
Тестирование TestRunnerNeuron, TestCoordinatorNeuron, TestHubNeuron, TestAnalyzerNeuron
"""

import pytest
import asyncio
from pathlib import Path


class TestTestRunnerNeuron:
    """Тесты TestRunnerNeuron"""
    
    def test_creation(self, test_config):
        """Тест создания TestRunnerNeuron"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestRunnerNeuron
        
        engine = TestEngine(test_config)
        neuron = TestRunnerNeuron(engine)
        
        assert neuron is not None
        assert neuron.name == "test_runner_neuron"
        assert neuron.node_type == "test_runner"
        assert hasattr(neuron, 'test_results')
        assert hasattr(neuron, 'running_tests')
        assert isinstance(neuron.running_tests, dict)
    
    @pytest.mark.asyncio
    async def test_run_test_invalid(self, test_config):
        """Тест запуска несуществующего теста"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestRunnerNeuron
        
        engine = TestEngine(test_config)
        neuron = TestRunnerNeuron(engine)
        
        # Запуск несуществующего теста
        result = await neuron.run_test("NonExistentTest", "tests/unit/test_model_testing.py")
        
        assert isinstance(result, dict)
        assert "test_name" in result
        assert result["test_name"] == "NonExistentTest"
        # Тест должен завершиться с ошибкой (несуществующий тест)
        assert result.get("success", False) is False or "error" in result
    
    def test_connections(self, test_config):
        """Тест связей TestRunnerNeuron"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestRunnerNeuron, TestHubNeuron
        from obelisk.core.neural_sync import NeuralConnection
        
        engine = TestEngine(test_config)
        runner = TestRunnerNeuron(engine)
        hub = TestHubNeuron()
        
        # Создание связи
        conn = NeuralConnection("test_runner_neuron", "test_hub_neuron", "data")
        conn.target = hub
        runner.connect_to(hub, conn)
        
        assert "test_hub_neuron" in runner.outgoing_connections
        assert runner.outgoing_connections["test_hub_neuron"] == conn


class TestTestCoordinatorNeuron:
    """Тесты TestCoordinatorNeuron"""
    
    def test_creation(self, test_config):
        """Тест создания TestCoordinatorNeuron"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestCoordinatorNeuron
        
        engine = TestEngine(test_config)
        neuron = TestCoordinatorNeuron(engine)
        
        assert neuron is not None
        assert neuron.name == "test_coordinator_neuron"
        assert neuron.node_type == "test_coordinator"
        assert hasattr(neuron, 'test_engine')
    
    @pytest.mark.asyncio
    async def test_run_test_group_invalid(self, test_config):
        """Тест запуска несуществующей группы тестов"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestCoordinatorNeuron
        
        engine = TestEngine(test_config)
        neuron = TestCoordinatorNeuron(engine)
        
        # Запуск несуществующей группы
        result = await neuron.run_test_group("NonExistentGroup", "tests/unit/test_model_testing.py")
        
        assert isinstance(result, dict)
        # Должна быть ошибка или неуспешный результат
        assert "error" in result or result.get("success", False) is False
    
    def test_connections(self, test_config):
        """Тест связей TestCoordinatorNeuron"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestCoordinatorNeuron, TestRunnerNeuron, TestHubNeuron
        from obelisk.core.neural_sync import NeuralConnection
        
        engine = TestEngine(test_config)
        coordinator = TestCoordinatorNeuron(engine)
        runner = TestRunnerNeuron(engine)
        hub = TestHubNeuron()
        
        # Создание связей
        conn1 = NeuralConnection("test_coordinator_neuron", "test_runner_neuron", "command")
        conn1.target = runner
        coordinator.connect_to(runner, conn1)
        
        conn2 = NeuralConnection("test_coordinator_neuron", "test_hub_neuron", "data")
        conn2.target = hub
        coordinator.connect_to(hub, conn2)
        
        assert "test_runner_neuron" in coordinator.outgoing_connections
        assert "test_hub_neuron" in coordinator.outgoing_connections


class TestTestHubNeuron:
    """Тесты TestHubNeuron"""
    
    def test_creation(self):
        """Тест создания TestHubNeuron"""
        from obelisk.core.test_neural_nodes import TestHubNeuron
        
        neuron = TestHubNeuron()
        
        assert neuron is not None
        assert neuron.name == "test_hub_neuron"
        assert neuron.node_type == "test_hub"
        assert hasattr(neuron, 'statistics')
        assert hasattr(neuron, 'test_data')
    
    def test_get_statistics(self):
        """Тест получения статистики"""
        from obelisk.core.test_neural_nodes import TestHubNeuron
        
        neuron = TestHubNeuron()
        stats = neuron.get_statistics()
        
        assert isinstance(stats, dict)
        assert "total_tests" in stats
        assert "passed_tests" in stats
        assert "failed_tests" in stats
        assert "skipped_tests" in stats
    
    def test_receive_data(self):
        """Тест получения данных"""
        from obelisk.core.test_neural_nodes import TestHubNeuron
        
        neuron = TestHubNeuron()
        
        # Отправка тестовых данных
        test_data = {
            "test_name": "test_example",
            "success": True,
            "timestamp": "2025-01-20T10:00:00"
        }
        
        neuron.receive(test_data, "test_runner_neuron")
        
        # Проверяем, что данные сохранены
        assert len(neuron.test_data) > 0
    
    def test_get_test_info(self):
        """Тест получения информации о тесте"""
        from obelisk.core.test_neural_nodes import TestHubNeuron
        
        neuron = TestHubNeuron()
        
        # Добавляем тестовые данные
        test_data = {
            "test_name": "test_example",
            "success": True,
            "timestamp": "2025-01-20T10:00:00"
        }
        neuron.receive(test_data, "test_runner_neuron")
        
        # Получаем информацию
        info = neuron.get_test_info("test_example")
        
        assert info is not None
        assert info["test_name"] == "test_example"


class TestTestAnalyzerNeuron:
    """Тесты TestAnalyzerNeuron"""
    
    def test_creation(self, test_config):
        """Тест создания TestAnalyzerNeuron"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestAnalyzerNeuron
        
        engine = TestEngine(test_config)
        neuron = TestAnalyzerNeuron(engine)
        
        assert neuron is not None
        assert neuron.name == "test_analyzer_neuron"
        assert neuron.node_type == "test_analyzer"
        assert hasattr(neuron, 'test_engine')
    
    @pytest.mark.asyncio
    async def test_analyze_results(self, test_config):
        """Тест анализа результатов"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestAnalyzerNeuron
        
        engine = TestEngine(test_config)
        neuron = TestAnalyzerNeuron(engine)
        
        # Тестовые результаты
        test_results = {
            "total": 10,
            "passed": 8,
            "failed": 1,
            "skipped": 1
        }
        
        analysis = await neuron.analyze(test_results)
        
        assert isinstance(analysis, dict)
        assert "summary" in analysis
        assert "recommendations" in analysis
        assert analysis["summary"]["total"] == 10
        assert analysis["summary"]["passed"] == 8
        assert analysis["summary"]["failed"] == 1
        assert analysis["summary"]["skipped"] == 1
    
    @pytest.mark.asyncio
    async def test_analyze_empty_results(self, test_config):
        """Тест анализа пустых результатов"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestAnalyzerNeuron
        
        engine = TestEngine(test_config)
        neuron = TestAnalyzerNeuron(engine)
        
        # Пустые результаты
        test_results = {}
        
        analysis = await neuron.analyze(test_results)
        
        assert isinstance(analysis, dict)
        assert "summary" in analysis


class TestTestNeuralArchitecture:
    """Тесты TestNeuralArchitecture"""
    
    @pytest.mark.asyncio
    async def test_architecture_creation(self, test_config):
        """Тест создания нейронной архитектуры"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestNeuralArchitecture
        
        engine = TestEngine(test_config)
        architecture = TestNeuralArchitecture()
        architecture.create_architecture(test_engine=engine)
        
        assert architecture.test_runner_neuron is not None
        assert architecture.test_coordinator_neuron is not None
        assert architecture.test_hub_neuron is not None
        assert architecture.test_analyzer_neuron is not None
        
        # Проверяем связи
        assert len(architecture.connections) > 0
        assert "coordinator->runner" in architecture.connections
        assert "runner->hub" in architecture.connections
    
    @pytest.mark.asyncio
    async def test_architecture_connections(self, test_config):
        """Тест связей в архитектуре"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestNeuralArchitecture
        
        engine = TestEngine(test_config)
        architecture = TestNeuralArchitecture()
        architecture.create_architecture(test_engine=engine)
        
        # Проверяем связи между узлами
        coordinator = architecture.test_coordinator_neuron
        runner = architecture.test_runner_neuron
        hub = architecture.test_hub_neuron
        
        # Coordinator должен быть связан с Runner
        assert "test_runner_neuron" in coordinator.outgoing_connections
        
        # Runner должен быть связан с Hub
        assert "test_hub_neuron" in runner.outgoing_connections
        
        # Coordinator должен быть связан с Hub
        assert "test_hub_neuron" in coordinator.outgoing_connections

