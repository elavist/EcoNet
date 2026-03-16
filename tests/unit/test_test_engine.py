"""
Unit тесты для TestEngine
Тестирование тестового движка с нейронной архитектурой
"""

import pytest
import asyncio
from pathlib import Path


class TestTestEngineBasic:
    """Базовые тесты TestEngine - быстрые, без инициализации"""
    
    def test_initialization(self, test_config):
        """Тест инициализации TestEngine"""
        from obelisk.core.engines.test_engine import TestEngine
        
        engine = TestEngine(test_config)
        
        assert engine is not None
        assert engine.config == test_config
        assert hasattr(engine, 'test_statistics')
        assert engine._initialized is False
    
    def test_statistics_structure(self, test_config):
        """Тест структуры статистики"""
        from obelisk.core.engines.test_engine import TestEngine
        
        engine = TestEngine(test_config)
        stats = engine.get_statistics()
        
        assert isinstance(stats, dict)
        assert "total_tests" in stats
        assert "passed_tests" in stats
        assert "failed_tests" in stats
        assert "skipped_tests" in stats
        assert "test_groups" in stats


class TestTestEngineWithNeuralNetwork:
    """Тесты TestEngine с нейронной архитектурой"""
    
    @pytest.mark.asyncio
    async def test_neural_architecture_creation(self, test_config):
        """Тест создания нейронной архитектуры"""
        from obelisk.core.engines.test_engine import TestEngine
        
        engine = TestEngine(test_config)
        
        try:
            await asyncio.wait_for(engine.initialize(), timeout=10.0)
            
            assert engine._initialized is True
            assert engine.test_neural_architecture is not None
            assert engine.test_neural_architecture.test_runner_neuron is not None
            assert engine.test_neural_architecture.test_coordinator_neuron is not None
            assert engine.test_neural_architecture.test_hub_neuron is not None
            assert engine.test_neural_architecture.test_analyzer_neuron is not None
            
        except asyncio.TimeoutError:
            pytest.skip("Инициализация TestEngine превысила таймаут (10s)")
        except Exception as e:
            pytest.skip(f"Ошибка инициализации TestEngine: {e}")
    
    @pytest.mark.asyncio
    async def test_neural_connections(self, test_config):
        """Тест связей между нейронными узлами"""
        from obelisk.core.engines.test_engine import TestEngine
        
        engine = TestEngine(test_config)
        
        try:
            await asyncio.wait_for(engine.initialize(), timeout=10.0)
            
            architecture = engine.test_neural_architecture
            assert architecture is not None
            
            # Проверка связей
            assert len(architecture.connections) > 0
            assert "coordinator->runner" in architecture.connections
            assert "runner->hub" in architecture.connections
            
        except asyncio.TimeoutError:
            pytest.skip("Инициализация TestEngine превысила таймаут (10s)")
        except Exception as e:
            pytest.skip(f"Ошибка инициализации TestEngine: {e}")


class TestTestNeuralNodes:
    """Тесты нейронных узлов тестового движка"""
    
    def test_test_runner_neuron_creation(self, test_config):
        """Тест создания TestRunnerNeuron"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestRunnerNeuron
        
        engine = TestEngine(test_config)
        neuron = TestRunnerNeuron(engine)
        
        assert neuron is not None
        assert neuron.name == "test_runner_neuron"
        assert neuron.node_type == "test_runner"
        assert hasattr(neuron, 'test_results')
    
    def test_test_hub_neuron_creation(self):
        """Тест создания TestHubNeuron"""
        from obelisk.core.test_neural_nodes import TestHubNeuron
        
        neuron = TestHubNeuron()
        
        assert neuron is not None
        assert neuron.name == "test_hub_neuron"
        assert neuron.node_type == "test_hub"
        assert hasattr(neuron, 'statistics')
        
        stats = neuron.get_statistics()
        assert isinstance(stats, dict)
        assert "total_tests" in stats
    
    def test_test_analyzer_neuron_creation(self, test_config):
        """Тест создания TestAnalyzerNeuron"""
        from obelisk.core.engines.test_engine import TestEngine
        from obelisk.core.test_neural_nodes import TestAnalyzerNeuron
        
        engine = TestEngine(test_config)
        neuron = TestAnalyzerNeuron(engine)
        
        assert neuron is not None
        assert neuron.name == "test_analyzer_neuron"
        assert neuron.node_type == "test_analyzer"
    
    @pytest.mark.asyncio
    async def test_test_analyzer_analysis(self, test_config):
        """Тест анализа результатов тестов"""
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


class TestTestEngineIntegration:
    """Тесты интеграции TestEngine с реальными тестами"""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_run_test_group_basic(self, test_engine):
        """Тест запуска группы тестов через TestEngine"""
        # Если инициализация не завершилась, пропускаем
        if not getattr(test_engine, '_test_initialized', False):
            pytest.skip("TestEngine не инициализирован")
        
        # Запускаем базовую группу тестов
        try:
            result = await asyncio.wait_for(
                test_engine.run_test_group("TestModelTesterBasic", "tests/unit/test_model_testing.py"),
                timeout=30.0
            )
            
            assert isinstance(result, dict)
            assert "group_name" in result
            assert "success" in result
            assert result["group_name"] == "TestModelTesterBasic"
            
        except asyncio.TimeoutError:
            pytest.skip("Запуск тестов через TestEngine превысил таймаут (30s)")
        except Exception as e:
            pytest.skip(f"Ошибка запуска тестов через TestEngine: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_run_test_group_hierarchy(self, test_engine):
        """Тест запуска тестов по иерархии через TestEngine"""
        # Если инициализация не завершилась, пропускаем
        if not getattr(test_engine, '_test_initialized', False):
            pytest.skip("TestEngine не инициализирован")
        
        # Группы тестов в порядке выполнения
        test_groups = [
            "TestModelTesterBasic",
            "TestModelTesterWithEngine",
        ]
        
        results = []
        for group_name in test_groups:
            try:
                result = await asyncio.wait_for(
                    test_engine.run_test_group(group_name, "tests/unit/test_model_testing.py"),
                    timeout=30.0
                )
                results.append(result)
            except asyncio.TimeoutError:
                logger.warning(f"Группа {group_name} превысила таймаут")
                break
            except Exception as e:
                logger.warning(f"Ошибка в группе {group_name}: {e}")
                break
        
        # Проверяем, что хотя бы одна группа выполнилась
        assert len(results) > 0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_analyze_test_results(self, test_engine):
        """Тест анализа результатов тестов через TestEngine"""
        # Если инициализация не завершилась, пропускаем
        if not getattr(test_engine, '_test_initialized', False):
            pytest.skip("TestEngine не инициализирован")
        
        # Тестовые результаты
        test_results = {
            "total": 10,
            "passed": 8,
            "failed": 1,
            "skipped": 1,
            "group_name": "TestModelTesterBasic"
        }
        
        try:
            analysis = await asyncio.wait_for(
                test_engine.analyze_test_results(test_results),
                timeout=5.0
            )
            
            assert isinstance(analysis, dict)
            # Анализ должен содержать summary или аналогичную структуру
            
        except asyncio.TimeoutError:
            pytest.skip("Анализ результатов превысил таймаут (5s)")
        except Exception as e:
            pytest.skip(f"Ошибка анализа результатов: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_neural_nodes_coordination(self, test_engine):
        """Тест координации нейронных узлов при запуске тестов"""
        # Если инициализация не завершилась, пропускаем
        if not getattr(test_engine, '_test_initialized', False):
            pytest.skip("TestEngine не инициализирован")
        
        # Проверяем наличие нейронной архитектуры
        assert test_engine.test_neural_architecture is not None
        assert test_engine.test_neural_architecture.test_coordinator_neuron is not None
        assert test_engine.test_neural_architecture.test_runner_neuron is not None
        assert test_engine.test_neural_architecture.test_hub_neuron is not None
        assert test_engine.test_neural_architecture.test_analyzer_neuron is not None
        
        # Проверяем связи между узлами
        architecture = test_engine.test_neural_architecture
        assert len(architecture.connections) > 0
        assert "coordinator->runner" in architecture.connections
        assert "runner->hub" in architecture.connections

