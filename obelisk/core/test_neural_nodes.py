"""
Нейронные узлы для тестового движка ЭкоНет
Специализированные нейроны для управления тестами
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque
import threading
import subprocess
import sys

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import NeuralConnection, ComponentState

logger = logging.getLogger(__name__)


class TestRunnerNeuron(NeuralNode):
    """
    Нейрон для запуска тестов
    Отвечает за выполнение тестовых сценариев
    """
    
    def __init__(self, test_engine):
        """
        Инициализация TestRunnerNeuron
        
        Args:
            test_engine: Ссылка на TestEngine
        """
        super().__init__("test_runner_neuron", "test_runner")
        self.test_engine = test_engine
        self.running_tests = {}
        self.test_results = deque(maxlen=1000)
        self.state = ComponentState.READY
        
        logger.info("🧪 TestRunnerNeuron создан")
    
    async def run_test(self, test_name: str, test_path: str = None) -> Dict[str, Any]:
        """
        Запуск теста
        ВАЖНО: Тесты выполняются СТРОГО ПОСЛЕДОВАТЕЛЬНО (блокировка в TestCoordinatorNeuron)
        
        Args:
            test_name: Имя теста или группы тестов
            test_path: Путь к файлу тестов
        
        Returns:
            Результаты выполнения теста
        """
        # ИСПРАВЛЕНИЕ: Проверка на параллельный запуск
        if test_name in self.running_tests:
            logger.warning(f"⚠️ Тест {test_name} уже выполняется - это не должно происходить!")
            # Ждем завершения предыдущего запуска (на случай race condition)
            while test_name in self.running_tests:
                await asyncio.sleep(0.1)
            # Если все еще выполняется, возвращаем ошибку
            if test_name in self.running_tests:
                return {"error": "Test already running", "test_name": test_name}
        
        self.running_tests[test_name] = datetime.now()
        start_time = datetime.now()
        
        try:
            logger.info(f"🧪 Запуск теста: {test_name}")
            
            # Формирование команды pytest
            test_file = test_path or "tests/unit/test_model_testing.py"
            test_target = f"{test_file}::{test_name}"
            
            # ИСПРАВЛЕНИЕ: Используем asyncio.create_subprocess_exec вместо subprocess.run
            # Это не блокирует event loop
            # УБРАНЫ таймауты - даем тестам завершиться естественным образом
            # Оставляем только защиту от реальных зависаний (10 минут)
            timeout_seconds = 600.0  # 10 минут - защита от реальных зависаний
            
            try:
                # Запрос GPU через венозную систему (если доступна)
                gpu_info = None
                gpu_task_id = None
                if self.test_engine and self.test_engine.gpu_circulatory:
                    try:
                        gpu_task_id = f"test_{test_name}_{start_time.timestamp()}"
                        gpu_info = await asyncio.wait_for(
                            self.test_engine.gpu_circulatory.request_gpu(
                                gpu_task_id, priority=7, memory_required=0.1
                            ),
                            timeout=2.0
                        )
                        if gpu_info:
                            logger.info(f"🩸 GPU выделен для теста {test_name}: {gpu_info.get('device', 'unknown')}")
                    except Exception as e:
                        logger.debug(f"GPU недоступен для теста {test_name}: {e}")
                
                # Запуск через asyncio subprocess с прогрессом
                process = await asyncio.create_subprocess_exec(
                    sys.executable, "-m", "pytest", test_target, "-v", "--tb=line",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # ИСПРАВЛЕНИЕ: Добавлен прогресс-мониторинг
                start_time = datetime.now()
                progress_task = None
                
                async def show_progress():
                    """Показ прогресса выполнения теста"""
                    elapsed = 0
                    while True:
                        await asyncio.sleep(5.0)  # Обновление каждые 5 секунд
                        elapsed = (datetime.now() - start_time).total_seconds()
                        if process.returncode is None:
                            logger.info(f"⏳ Тест {test_name} выполняется... ({elapsed:.1f}s / {timeout_seconds:.0f}s)")
                        else:
                            break
                
                # Запуск мониторинга прогресса
                progress_task = asyncio.create_task(show_progress())
                
                # Ожидание завершения с таймаутом
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout_seconds
                    )
                    
                    # Остановка мониторинга прогресса
                    if progress_task:
                        progress_task.cancel()
                        try:
                            await progress_task
                        except asyncio.CancelledError:
                            pass
                    
                    # Декодирование вывода
                    stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
                    stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
                    returncode = process.returncode
                    
                except asyncio.TimeoutError:
                    # Остановка мониторинга прогресса
                    if progress_task:
                        progress_task.cancel()
                        try:
                            await progress_task
                        except asyncio.CancelledError:
                            pass
                    
                    # ИСПРАВЛЕНИЕ: Агрессивное прерывание процесса на Windows
                    logger.warning(f"⏱️ Тест {test_name} превысил таймаут ({timeout_seconds}s), прерываем...")
                    try:
                        # На Windows сначала terminate, потом kill
                        if process.returncode is None:
                            try:
                                process.terminate()
                                # Даем время на завершение
                                try:
                                    await asyncio.wait_for(process.wait(), timeout=2.0)
                                except asyncio.TimeoutError:
                                    # Если не завершился, убиваем принудительно
                                    process.kill()
                                    await asyncio.wait_for(process.wait(), timeout=1.0)
                            except Exception as e:
                                logger.debug(f"Ошибка при завершении процесса: {e}")
                                try:
                                    process.kill()
                                    await asyncio.wait_for(process.wait(), timeout=1.0)
                                except Exception:
                                    pass
                    except Exception as e:
                        logger.debug(f"Ошибка при прерывании процесса: {e}")
                    
                    # Освобождение GPU
                    if gpu_info and gpu_task_id and self.test_engine and self.test_engine.gpu_circulatory:
                        try:
                            await self.test_engine.gpu_circulatory.release_gpu(gpu_task_id)
                        except Exception:
                            pass
                    
                    error_result = {
                        "test_name": test_name,
                        "success": False,
                        "error": f"Timeout expired ({timeout_seconds}s)",
                        "timestamp": datetime.now().isoformat(),
                        "duration": (datetime.now() - start_time).total_seconds()
                    }
                    self.test_results.append(error_result)
                    return error_result
                
                # Освобождение GPU
                if gpu_info and self.test_engine and self.test_engine.gpu_circulatory:
                    try:
                        # Используем оригинальный task_id
                        original_task_id = f"test_{test_name}_{start_time.timestamp()}"
                        await self.test_engine.gpu_circulatory.release_gpu(original_task_id)
                    except Exception:
                        pass
                
                duration = (datetime.now() - start_time).total_seconds()
                test_result = {
                    "test_name": test_name,
                    "success": returncode == 0,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "returncode": returncode,
                    "timestamp": datetime.now().isoformat(),
                    "duration": duration,
                    "gpu_used": gpu_info is not None
                }
                
                logger.info(f"✅ Тест {test_name} завершен за {duration:.2f}s (успех: {returncode == 0})")
                
                self.test_results.append(test_result)
                
                # Отправка результата в Hub
                if "test_hub_neuron" in self.outgoing_connections:
                    self.send(test_result, "test_hub_neuron")
                
                return test_result
                
            except Exception as e:
                error_result = {
                    "test_name": test_name,
                    "success": False,
                    "error": f"Process error: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "duration": (datetime.now() - start_time).total_seconds()
                }
                self.test_results.append(error_result)
                logger.error(f"❌ Ошибка выполнения теста {test_name}: {e}")
                return error_result
            
        except Exception as e:
            error_result = {
                "test_name": test_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "duration": (datetime.now() - start_time).total_seconds() if 'start_time' in locals() else 0
            }
            self.test_results.append(error_result)
            logger.error(f"❌ Ошибка выполнения теста {test_name}: {e}")
            return error_result
            
        finally:
            if test_name in self.running_tests:
                del self.running_tests[test_name]


class TestCoordinatorNeuron(NeuralNode):
    """
    Нейрон-координатор тестов
    Управляет последовательностью выполнения тестов
    ОБЕСПЕЧИВАЕТ СТРОГО ПОСЛЕДОВАТЕЛЬНОЕ ВЫПОЛНЕНИЕ С СОБЛЮДЕНИЕМ ИЕРАРХИИ
    """
    
    def __init__(self, test_engine):
        """
        Инициализация TestCoordinatorNeuron
        
        Args:
            test_engine: Ссылка на TestEngine
        """
        super().__init__("test_coordinator_neuron", "test_coordinator")
        self.test_engine = test_engine
        self.test_queue = asyncio.Queue()
        self.current_test = None
        self.state = ComponentState.READY
        
        # ИСПРАВЛЕНИЕ: Блокировка для последовательного выполнения тестов
        # Гарантирует, что тесты выполняются строго один за другим, соблюдая иерархию
        self._execution_lock = asyncio.Lock()
        self._test_order = []  # Порядок выполнения тестов для соблюдения иерархии
        
        logger.info("🎯 TestCoordinatorNeuron создан (с блокировкой последовательного выполнения)")
    
    async def run_test_group(self, group_name: str, test_path: str = None) -> Dict[str, Any]:
        """
        Запуск группы тестов через TestRunnerNeuron
        ВАЖНО: Тесты выполняются СТРОГО ПОСЛЕДОВАТЕЛЬНО с соблюдением иерархии
        
        Args:
            group_name: Имя группы тестов
            test_path: Путь к файлу тестов
        
        Returns:
            Результаты выполнения группы тестов
        """
        # ИСПРАВЛЕНИЕ: Используем блокировку для последовательного выполнения
        # Это гарантирует, что тесты не будут запускаться параллельно
        async with self._execution_lock:
            logger.info(f"🎯 Координация запуска группы тестов: {group_name} (последовательно)")
            
            # Проверка, что предыдущий тест завершился
            if self.current_test is not None:
                logger.warning(f"⚠️ Предыдущий тест {self.current_test} еще не завершен, ожидание...")
                # Ждем завершения предыдущего теста (должен быть уже завершен из-за lock)
                # Но на всякий случай проверяем
                while self.current_test is not None:
                    await asyncio.sleep(0.1)
            
            # Устанавливаем текущий тест
            self.current_test = group_name
            self._test_order.append(group_name)
            
            try:
                # Отправка команды TestRunnerNeuron
                if "test_runner_neuron" in self.outgoing_connections:
                    # Получаем TestRunnerNeuron через связь
                    runner_connection = self.outgoing_connections["test_runner_neuron"]
                    
                    # Создаем задачу для запуска теста
                    if hasattr(runner_connection, 'target') and hasattr(runner_connection.target, 'run_test'):
                        result = await runner_connection.target.run_test(group_name, test_path)
                        return result
                
                # Fallback: прямое выполнение
                logger.warning("⚠️ TestRunnerNeuron недоступен, используем fallback")
                return {"error": "TestRunnerNeuron not available"}
            
            finally:
                # Освобождаем текущий тест
                self.current_test = None
                logger.info(f"✅ Группа тестов {group_name} завершена, блокировка снята")


class TestHubNeuron(NeuralNode):
    """
    Центральный узел информации о тестах
    Собирает и хранит информацию о всех тестах
    """
    
    def __init__(self):
        """Инициализация TestHubNeuron"""
        super().__init__("test_hub_neuron", "test_hub")
        self.test_info = {}
        self.test_data = []
        self.test_history = deque(maxlen=1000)
        self.statistics = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "skipped_tests": 0,
            "test_groups": {}
        }
        self.state = ComponentState.READY
        
        logger.info("📊 TestHubNeuron создан")
    
    def receive(self, data: Any, source: str = "unknown"):
        """Прием данных о тестах"""
        super().receive(data, source)
        
        # Обработка результатов тестов
        if isinstance(data, dict) and "test_name" in data:
            test_name = data["test_name"]
            self.test_info[test_name] = data
            self.test_data.append(data)
            self.test_history.append({
                "test_name": test_name,
                "data": data,
                "source": source,
                "timestamp": datetime.now()
            })
            
            # Обновление статистики
            if data.get("success"):
                self.statistics["passed_tests"] += 1
            else:
                self.statistics["failed_tests"] += 1
            
            self.statistics["total_tests"] += 1
            
            # Группировка по группам тестов
            if "Test" in test_name:
                group_name = test_name.split("::")[0] if "::" in test_name else test_name
                if group_name not in self.statistics["test_groups"]:
                    self.statistics["test_groups"][group_name] = {
                        "total": 0,
                        "passed": 0,
                        "failed": 0
                    }
                
                group_stats = self.statistics["test_groups"][group_name]
                group_stats["total"] += 1
                if data.get("success"):
                    group_stats["passed"] += 1
                else:
                    group_stats["failed"] += 1
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики тестов"""
        return self.statistics.copy()
    
    def get_test_info(self, test_name: str) -> Optional[Dict[str, Any]]:
        """Получение информации о конкретном тесте"""
        return self.test_info.get(test_name)


class TestAnalyzerNeuron(NeuralNode):
    """
    Нейрон для анализа результатов тестов
    Анализирует результаты и предоставляет выводы
    """
    
    def __init__(self, test_engine):
        """
        Инициализация TestAnalyzerNeuron
        
        Args:
            test_engine: Ссылка на TestEngine
        """
        super().__init__("test_analyzer_neuron", "test_analyzer")
        self.test_engine = test_engine
        self.analysis_cache = {}
        self.state = ComponentState.READY
        
        logger.info("🔍 TestAnalyzerNeuron создан")
    
    async def analyze(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализ результатов тестов
        
        Args:
            results: Результаты выполнения тестов
        
        Returns:
            Анализ результатов
        """
        logger.info("🔍 Анализ результатов тестов...")
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "summary": {},
            "recommendations": [],
            "issues": []
        }
        
        # Базовый анализ
        if isinstance(results, dict):
            total = results.get("total", 0)
            passed = results.get("passed", 0)
            failed = results.get("failed", 0)
            skipped = results.get("skipped", 0)
            
            analysis["summary"] = {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "success_rate": (passed / total * 100) if total > 0 else 0
            }
            
            # Рекомендации
            if failed > 0:
                analysis["issues"].append(f"Обнаружено {failed} неудачных тестов")
                analysis["recommendations"].append("Проверьте логи неудачных тестов")
            
            if skipped > 0:
                analysis["recommendations"].append(f"{skipped} тестов пропущено - проверьте зависимости")
            
            if passed == total and total > 0:
                analysis["recommendations"].append("Все тесты прошли успешно! ✅")
        
        # Кэширование анализа
        cache_key = f"{results.get('test_name', 'unknown')}_{datetime.now().strftime('%Y%m%d')}"
        self.analysis_cache[cache_key] = analysis
        
        # Отправка анализа в Hub
        self.send(analysis, "test_hub_neuron")
        
        return analysis


class TestNeuralArchitecture:
    """
    Архитектура нейронной сети для тестов
    Управляет связями между тестовыми нейронами
    """
    
    def __init__(self):
        self.test_runner_neuron: Optional[TestRunnerNeuron] = None
        self.test_coordinator_neuron: Optional[TestCoordinatorNeuron] = None
        self.test_hub_neuron: Optional[TestHubNeuron] = None
        self.test_analyzer_neuron: Optional[TestAnalyzerNeuron] = None
        
        self.connections: Dict[str, NeuralConnection] = {}
    
    def create_architecture(self, test_engine):
        """Создание архитектуры тестовой нейронной сети"""
        # 1. Создание узлов
        self.test_runner_neuron = TestRunnerNeuron(test_engine)
        self.test_coordinator_neuron = TestCoordinatorNeuron(test_engine)
        self.test_hub_neuron = TestHubNeuron()
        self.test_analyzer_neuron = TestAnalyzerNeuron(test_engine)
        
        # 2. Создание связей
        # Coordinator -> Runner
        conn1 = NeuralConnection("test_coordinator_neuron", "test_runner_neuron", "command")
        conn1.target = self.test_runner_neuron  # Устанавливаем target для доступа
        self.test_coordinator_neuron.connect_to(self.test_runner_neuron, conn1)
        self.connections["coordinator->runner"] = conn1
        
        # Runner -> Hub
        conn2 = NeuralConnection("test_runner_neuron", "test_hub_neuron", "data")
        conn2.target = self.test_hub_neuron
        self.test_runner_neuron.connect_to(self.test_hub_neuron, conn2)
        self.connections["runner->hub"] = conn2
        
        # Coordinator -> Hub
        conn3 = NeuralConnection("test_coordinator_neuron", "test_hub_neuron", "data")
        conn3.target = self.test_hub_neuron
        self.test_coordinator_neuron.connect_to(self.test_hub_neuron, conn3)
        self.connections["coordinator->hub"] = conn3
        
        # Analyzer -> Hub
        conn4 = NeuralConnection("test_analyzer_neuron", "test_hub_neuron", "data")
        conn4.target = self.test_hub_neuron
        self.test_analyzer_neuron.connect_to(self.test_hub_neuron, conn4)
        self.connections["analyzer->hub"] = conn4
        
        # Hub -> Analyzer (обратная связь)
        conn5 = NeuralConnection("test_hub_neuron", "test_analyzer_neuron", "request")
        conn5.target = self.test_analyzer_neuron
        self.test_hub_neuron.connect_to(self.test_analyzer_neuron, conn5)
        self.connections["hub->analyzer"] = conn5
        
        # Hub -> Coordinator (обратная связь)
        conn6 = NeuralConnection("test_hub_neuron", "test_coordinator_neuron", "feedback")
        conn6.target = self.test_coordinator_neuron
        self.test_hub_neuron.connect_to(self.test_coordinator_neuron, conn6)
        self.connections["hub->coordinator"] = conn6
        
        logger.info("✅ Тестовая нейронная архитектура создана: 4 узла, 6 связей")
        
        # Установка состояний
        self.test_runner_neuron.state = ComponentState.READY
        self.test_coordinator_neuron.state = ComponentState.READY
        self.test_hub_neuron.state = ComponentState.READY
        self.test_analyzer_neuron.state = ComponentState.READY

