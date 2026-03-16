"""
Тестовый движок ЭкоНет
Отдельный движок для управления тестами с собственной нейронной архитектурой
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import threading

from obelisk.core.neural_sync import get_neural_network, ComponentState
from obelisk.core.test_neural_nodes import TestNeuralArchitecture

logger = logging.getLogger(__name__)


class TestEngine:
    """
    Тестовый движок ЭкоНет
    Управляет тестами через нейронную архитектуру
    
    Архитектура:
    1. TestRunnerNeuron - запуск и выполнение тестов
    2. TestCoordinatorNeuron - координация тестов
    3. TestHubNeuron - центральный узел информации о тестах
    4. TestAnalyzerNeuron - анализ результатов тестов
    """
    
    def __init__(self, config: Dict, project_root: Optional[Path] = None):
        """
        Инициализация тестового движка
        
        Args:
            config: Конфигурация системы
            project_root: Корневая директория проекта
        """
        self.config = config
        self.project_root = project_root or Path(__file__).parent.parent.parent
        
        # Состояние
        self._initialized = False
        self._initialization_lock = asyncio.Lock()
        
        # Компоненты
        self.test_runner = None
        self.test_coordinator = None
        self.test_analyzer = None
        
        # Нейронная сеть
        self.neural_network = get_neural_network()
        self.test_neural_architecture: Optional[TestNeuralArchitecture] = None
        
        # GPU Венозная система (Veins) - подключение к GPU
        self.gpu_circulatory = None
        self.gpu_distributor = None
        self._init_gpu_veins()
        
        # Статистика тестов
        self.test_statistics = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_groups": {},
            "last_run": None
        }
        
        logger.info("🧪 TestEngine создан")
    
    def _init_gpu_veins(self):
        """Инициализация подключения к GPU венозной системе"""
        try:
            from obelisk.veins.gpu_circulatory import GPUCirculatorySystem
            from obelisk.veins.gpu_distributor import GPUDistributor
            
            self.gpu_circulatory = GPUCirculatorySystem()
            self.gpu_distributor = GPUDistributor(self.gpu_circulatory)
            
            logger.info("🩸 TestEngine подключен к GPU венозной системе")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось подключить к GPU венозной системе: {e}")
            self.gpu_circulatory = None
            self.gpu_distributor = None
    
    async def initialize(self):
        """Асинхронная инициализация тестового движка"""
        if self._initialized:
            return
        
        async with self._initialization_lock:
            if self._initialized:
                return
            
            logger.info("🚀 Инициализация TestEngine...")
            
            try:
                # 1. Инициализация компонентов тестирования
                await self._init_test_components()
                
                # 2. Создание нейронной архитектуры для тестов
                await self._setup_test_neural_architecture()
                
                self._initialized = True
                logger.info("✅ TestEngine инициализирован успешно")
                
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации TestEngine: {e}", exc_info=True)
                raise
    
    async def _init_test_components(self):
        """Инициализация компонентов тестирования"""
        try:
            from obelisk.core.model_testing import ModelTester
            
            # Создаем компоненты для тестирования
            # Они будут использоваться нейронными узлами
            logger.info("🔧 Инициализация компонентов тестирования...")
            
            # Создаем ModelTester с интеграцией GPU венозной системы
            # ModelTester будет использовать gpu_circulatory для выделения ресурсов
            self.model_tester = None  # Будет создан при необходимости с unified_engine
            
            # Регистрация в нейронной сети
            self.neural_network.register_component("test_engine", self)
            self.neural_network.set_state("test_engine", ComponentState.READY)
            
            logger.info("✅ Компоненты тестирования инициализированы (с GPU венозной системой)")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации компонентов тестирования: {e}", exc_info=True)
            self.neural_network.set_state("test_engine", ComponentState.ERROR)
            raise
    
    async def _setup_test_neural_architecture(self):
        """Создание нейронной архитектуры для тестов"""
        try:
            logger.info("🧠 Создание нейронной архитектуры для тестов...")
            
            # Создание архитектуры тестовой нейронной сети
            self.test_neural_architecture = TestNeuralArchitecture()
            self.test_neural_architecture.create_architecture(
                test_engine=self
            )
            
            logger.info("✅ Тестовая нейронная архитектура создана:")
            logger.info("  1. TestRunnerNeuron - запуск тестов")
            logger.info("  2. TestCoordinatorNeuron - координация тестов")
            logger.info("  3. TestHubNeuron - центральный узел информации")
            logger.info("  4. TestAnalyzerNeuron - анализ результатов")
            
            # Регистрация узлов в общей нейронной сети
            if self.test_neural_architecture.test_runner_neuron:
                self.neural_network.register_component(
                    "test_runner_neuron",
                    self.test_neural_architecture.test_runner_neuron
                )
            if self.test_neural_architecture.test_coordinator_neuron:
                self.neural_network.register_component(
                    "test_coordinator_neuron",
                    self.test_neural_architecture.test_coordinator_neuron
                )
            if self.test_neural_architecture.test_hub_neuron:
                self.neural_network.register_component(
                    "test_hub_neuron",
                    self.test_neural_architecture.test_hub_neuron
                )
            if self.test_neural_architecture.test_analyzer_neuron:
                self.neural_network.register_component(
                    "test_analyzer_neuron",
                    self.test_neural_architecture.test_analyzer_neuron
                )
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания тестовой нейронной архитектуры: {e}", exc_info=True)
            raise
    
    async def run_test_group(self, group_name: str, test_path: str = None) -> Dict[str, Any]:
        """
        Запуск группы тестов через нейронную сеть
        ВАЖНО: Тесты выполняются СТРОГО ПОСЛЕДОВАТЕЛЬНО с соблюдением иерархии
        
        Args:
            group_name: Имя группы тестов (например, "TestModelTesterBasic")
            test_path: Путь к файлу тестов (опционально)
        
        Returns:
            Результаты выполнения тестов
        """
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"🧪 Запуск группы тестов: {group_name} (последовательно)")
        
        # ИСПРАВЛЕНИЕ: СТРОГО ПОСЛЕДОВАТЕЛЬНОЕ ВЫПОЛНЕНИЕ
        # TestCoordinatorNeuron имеет блокировку для гарантии последовательности
        if self.test_neural_architecture and self.test_neural_architecture.test_coordinator_neuron:
            # Блокировка внутри TestCoordinatorNeuron гарантирует последовательность
            result = await self.test_neural_architecture.test_coordinator_neuron.run_test_group(
                group_name, test_path
            )
            
            # Обновление статистики
            self._update_statistics_from_result(group_name, result)
            
            return result
        
        # Fallback: прямой запуск (тоже последовательно)
        result = await self._run_tests_direct(group_name, test_path)
        
        # Обновление статистики
        self._update_statistics_from_result(group_name, result)
        
        return result
    
    def _update_statistics_from_result(self, group_name: str, result: Dict[str, Any]):
        """Обновление статистики на основе результата теста"""
        if group_name not in self.test_statistics["test_groups"]:
            self.test_statistics["test_groups"][group_name] = {
                "runs": 0,
                "successful": 0,
                "failed": 0,
                "last_run": None
            }
        
        group_stats = self.test_statistics["test_groups"][group_name]
        group_stats["runs"] += 1
        group_stats["last_run"] = result.get("timestamp", datetime.now().isoformat())
        
        if result.get("success", False):
            group_stats["successful"] += 1
            self.test_statistics["passed_tests"] += 1
        else:
            group_stats["failed"] += 1
            self.test_statistics["failed_tests"] += 1
        
        self.test_statistics["total_tests"] += 1
        self.test_statistics["last_run"] = datetime.now().isoformat()
    
    async def _run_tests_direct(self, group_name: str, test_path: str = None) -> Dict[str, Any]:
        """Прямой запуск тестов (fallback)"""
        import sys
        
        test_file = test_path or "tests/unit/test_model_testing.py"
        test_class = f"{test_file}::{group_name}"
        
        # ИСПРАВЛЕНИЕ: Используем asyncio.create_subprocess_exec вместо subprocess.run
        # УБРАНЫ таймауты - даем тестам завершиться естественным образом
        # Оставляем только защиту от реальных зависаний (10 минут)
        timeout_seconds = 600.0  # 10 минут - защита от реальных зависаний
        
        try:
            # Запуск через asyncio subprocess
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pytest", test_class, "-v", "--tb=line",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Ожидание завершения с таймаутом
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout_seconds
                )
                
                # Декодирование вывода
                stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
                stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
                returncode = process.returncode
                
                return {
                    "group_name": group_name,
                    "success": returncode == 0,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "returncode": returncode,
                    "timestamp": datetime.now().isoformat()
                }
                
            except asyncio.TimeoutError:
                # Прерываем процесс при таймауте
                logger.warning(f"⏱️ Группа тестов {group_name} превысила таймаут ({timeout_seconds}s), прерываем...")
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
                
                return {
                    "group_name": group_name,
                    "success": False,
                    "error": f"Timeout expired ({timeout_seconds}s)",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка запуска тестов {group_name}: {e}")
            return {
                "group_name": group_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def analyze_test_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализ результатов тестов через нейронную сеть
        
        Args:
            results: Результаты выполнения тестов
        
        Returns:
            Анализ результатов
        """
        if not self._initialized:
            await self.initialize()
        
        if self.test_neural_architecture and self.test_neural_architecture.test_analyzer_neuron:
            analysis = await self.test_neural_architecture.test_analyzer_neuron.analyze(results)
            return analysis
        
        # Fallback: простой анализ
        return {
            "total": results.get("total", 0),
            "passed": results.get("passed", 0),
            "failed": results.get("failed", 0),
            "skipped": results.get("skipped", 0)
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение подробной статистики тестов"""
        stats = self.test_statistics.copy()
        
        # Добавляем подробную информацию
        if self.test_neural_architecture and self.test_neural_architecture.test_hub_neuron:
            hub_stats = self.test_neural_architecture.test_hub_neuron.get_statistics()
            stats["hub_statistics"] = hub_stats
        
        # Добавляем информацию о последних запусках
        if self.test_neural_architecture and self.test_neural_architecture.test_runner_neuron:
            runner = self.test_neural_architecture.test_runner_neuron
            stats["recent_tests"] = list(runner.test_results)[-10:] if runner.test_results else []
            stats["running_tests_count"] = len(runner.running_tests)
        
        # Добавляем информацию о нейронной архитектуре
        if self.test_neural_architecture:
            stats["neural_architecture"] = {
                "nodes_count": 4,
                "connections_count": len(self.test_neural_architecture.connections),
                "nodes": {
                    "test_runner": self.test_neural_architecture.test_runner_neuron is not None,
                    "test_coordinator": self.test_neural_architecture.test_coordinator_neuron is not None,
                    "test_hub": self.test_neural_architecture.test_hub_neuron is not None,
                    "test_analyzer": self.test_neural_architecture.test_analyzer_neuron is not None,
                }
            }
        
        return stats
    
    async def shutdown(self):
        """Завершение работы тестового движка"""
        if not self._initialized:
            return
        
        logger.info("🛑 Завершение работы TestEngine...")
        
        # Очистка нейронной архитектуры
        if self.test_neural_architecture:
            # Отключение узлов
            pass
        
        self._initialized = False
        logger.info("✅ TestEngine завершен")

