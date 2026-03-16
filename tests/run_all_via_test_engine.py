"""
Скрипт для запуска всех тестов через TestEngine
Использует нейронную архитектуру для координации тестов
"""

import asyncio
import sys
from pathlib import Path
import yaml
import logging

# ИСПРАВЛЕНИЕ: Настройка кодировки для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Добавление корня проекта в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска тестов через TestEngine"""
    print("="*70)
    print("🧪 Запуск всех тестов через TestEngine")
    print("="*70)
    print()
    
    # Загрузка конфигурации
    config_path = root_dir / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Модификация конфигурации для тестов
    config["logging"]["level"] = "WARNING"
    config["database"]["sqlite_path"] = "data/test_obelisk.db"
    
    # Отключаем тяжелые компоненты
    if "active_learning" in config:
        config["active_learning"]["enabled"] = False
    if "mqtt_topics" in config:
        config["mqtt_topics"] = {}
    if "database" in config:
        config["database"]["enabled"] = False
    
    # Создание TestEngine
    from obelisk.core.engines.test_engine import TestEngine
    
    test_engine = TestEngine(config, project_root=root_dir)
    
    try:
        # Инициализация
        print("🚀 Инициализация TestEngine...")
        await asyncio.wait_for(test_engine.initialize(), timeout=10.0)
        print("✅ TestEngine инициализирован")
        print()
        
        # Группы тестов в порядке выполнения (обновлены под новую структуру)
        test_groups = [
            ("TestModelTesterBasic", "tests/unit/test_model_testing.py"),
            ("TestModelTesterWithMock", "tests/unit/test_model_testing.py"),
            ("TestModelTesterSafety", "tests/unit/test_model_testing.py"),
        ]
        
        all_results = []
        total_groups = len(test_groups)
        
        # ИСПРАВЛЕНИЕ: СТРОГО ПОСЛЕДОВАТЕЛЬНОЕ ВЫПОЛНЕНИЕ С СОБЛЮДЕНИЕМ ИЕРАРХИИ
        # Каждый тест запускается только после полного завершения предыдущего
        for i, (group_name, test_path) in enumerate(test_groups, 1):
            print(f"[{i}/{total_groups}] Запуск группы: {group_name}")
            print("-" * 70)
            
            # ИСПРАВЛЕНИЕ: Явное ожидание завершения предыдущего теста
            if i > 1:
                prev_group = test_groups[i-2][0]
                print(f"⏳ Ожидание завершения предыдущей группы: {prev_group}")
                # Дополнительная проверка - ждем, пока предыдущий тест точно завершился
                await asyncio.sleep(0.5)  # Небольшая пауза для гарантии
            
            # Показываем статус GPU венозной системы
            if test_engine.gpu_circulatory:
                print("🩸 GPU венозная система: подключена")
            else:
                print("⚠️ GPU венозная система: не подключена")
            
            try:
                # ИСПРАВЛЕНИЕ: УБРАНЫ таймауты - даем тестам завершиться естественным образом
                # Оставляем только защиту от реальных зависаний (10 минут)
                timeout = 600.0  # 10 минут - защита от реальных зависаний
                
                # Мониторинг прогресса с периодическим выводом
                import time
                start_time = time.time()
                
                async def monitor_progress():
                    """Мониторинг прогресса выполнения группы тестов"""
                    while True:
                        await asyncio.sleep(10.0)  # Обновление каждые 10 секунд
                        elapsed = time.time() - start_time
                        print(f"   ⏳ Выполняется... ({elapsed:.0f}s)")
                
                # Запуск мониторинга прогресса
                progress_task = asyncio.create_task(monitor_progress())
                
                try:
                    # ИСПРАВЛЕНИЕ: СТРОГО ПОСЛЕДОВАТЕЛЬНЫЙ ЗАПУСК - один тест за раз
                    # Блокировка внутри TestCoordinatorNeuron гарантирует последовательность
                    result = await asyncio.wait_for(
                        test_engine.run_test_group(group_name, test_path),
                        timeout=timeout
                    )
                    
                    # ИСПРАВЛЕНИЕ: Явное ожидание завершения перед переходом к следующему тесту
                    await asyncio.sleep(0.2)  # Небольшая пауза для гарантии завершения
                    
                finally:
                    # Остановка мониторинга прогресса
                    progress_task.cancel()
                    try:
                        await progress_task
                    except asyncio.CancelledError:
                        pass
                
                all_results.append(result)
                
                if result.get("success", False):
                    print(f"✅ {group_name}: Успешно")
                else:
                    print(f"❌ {group_name}: Ошибка")
                    if "error" in result:
                        print(f"   Ошибка: {result['error']}")
                    if "stderr" in result and result["stderr"]:
                        print(f"   Stderr: {result['stderr'][:200]}")
                
            except asyncio.TimeoutError:
                timeout_msg = f"{timeout}s" if 'timeout' in locals() else "таймаут"
                print(f"⏱️ {group_name}: Превышен таймаут ({timeout_msg})")
                all_results.append({
                    "group_name": group_name,
                    "success": False,
                    "error": f"Timeout ({timeout_msg})"
                })
            except Exception as e:
                print(f"❌ {group_name}: Исключение - {e}")
                all_results.append({
                    "group_name": group_name,
                    "success": False,
                    "error": str(e)
                })
            
            print()
        
        # Анализ результатов
        print("="*70)
        print("📊 Анализ результатов")
        print("="*70)
        
        try:
            # Собираем статистику
            total = len(all_results)
            successful = sum(1 for r in all_results if r.get("success", False))
            failed = total - successful
            
            print(f"Всего групп: {total}")
            print(f"Успешно: {successful}")
            print(f"Ошибок: {failed}")
            print()
            
            # Анализ через TestEngine
            if test_engine.test_neural_architecture and test_engine.test_neural_architecture.test_analyzer_neuron:
                analysis = await test_engine.analyze_test_results({
                    "total": total,
                    "passed": successful,
                    "failed": failed,
                    "skipped": 0
                })
                
                if "summary" in analysis:
                    print("Сводка:")
                    for key, value in analysis["summary"].items():
                        print(f"  {key}: {value}")
                
                if "recommendations" in analysis and analysis["recommendations"]:
                    print("\nРекомендации:")
                    for rec in analysis["recommendations"]:
                        print(f"  - {rec}")
            
            # Подробная статистика TestEngine
            stats = test_engine.get_statistics()
            print("\n" + "="*70)
            print("📊 ПОДРОБНАЯ СТАТИСТИКА ТЕСТОВ")
            print("="*70)
            
            # Основная статистика
            print("\n📈 Основная статистика:")
            print(f"  Всего тестов: {stats.get('total_tests', 0)}")
            print(f"  Пройдено: {stats.get('passed_tests', 0)}")
            print(f"  Провалено: {stats.get('failed_tests', 0)}")
            print(f"  Пропущено: {stats.get('skipped_tests', 0)}")
            if stats.get('last_run'):
                print(f"  Последний запуск: {stats['last_run']}")
            
            # Статистика по группам
            if stats.get('test_groups'):
                print("\n📋 Статистика по группам:")
                for group_name, group_stats in stats['test_groups'].items():
                    print(f"  {group_name}:")
                    if isinstance(group_stats, dict):
                        for key, value in group_stats.items():
                            print(f"    {key}: {value}")
                    else:
                        print(f"    {group_stats}")
            
            # Статистика Hub
            if stats.get('hub_statistics'):
                hub_stats = stats['hub_statistics']
                print("\n📊 Статистика Hub:")
                print(f"  Всего тестов: {hub_stats.get('total_tests', 0)}")
                print(f"  Пройдено: {hub_stats.get('passed_tests', 0)}")
                print(f"  Провалено: {hub_stats.get('failed_tests', 0)}")
                print(f"  Пропущено: {hub_stats.get('skipped_tests', 0)}")
            
            # Последние тесты
            if stats.get('recent_tests'):
                print("\n🕐 Последние 10 тестов:")
                for i, test in enumerate(stats['recent_tests'][-10:], 1):
                    status = "✅" if test.get('success') else "❌"
                    duration = test.get('duration', 0)
                    print(f"  {i}. {status} {test.get('test_name', 'Unknown')} ({duration:.2f}s)")
            
            # Нейронная архитектура
            if stats.get('neural_architecture'):
                arch = stats['neural_architecture']
                print("\n🧠 Нейронная архитектура:")
                print(f"  Узлов: {arch.get('nodes_count', 0)}")
                print(f"  Связей: {arch.get('connections_count', 0)}")
                if arch.get('nodes'):
                    print("  Узлы:")
                    for node_name, is_active in arch['nodes'].items():
                        status = "✅" if is_active else "❌"
                        print(f"    {status} {node_name}")
            
            # Детализация по результатам
            print("\n📝 Детализация результатов:")
            for i, result in enumerate(all_results, 1):
                group_name = result.get('group_name', 'Unknown')
                success = result.get('success', False)
                status = "✅" if success else "❌"
                error = result.get('error', '')
                returncode = result.get('returncode', 'N/A')
                
                print(f"\n  {i}. {status} {group_name}")
                print(f"     Успех: {success}")
                if returncode != 'N/A':
                    print(f"     Код возврата: {returncode}")
                if error:
                    print(f"     Ошибка: {error}")
                if result.get('stdout'):
                    stdout_lines = result['stdout'].split('\n')
                    # Показываем последние 3 строки вывода
                    if len(stdout_lines) > 3:
                        print(f"     Вывод (последние 3 строки):")
                        for line in stdout_lines[-3:]:
                            if line.strip():
                                print(f"       {line}")
                    else:
                        print(f"     Вывод: {result['stdout'][:200]}")
            
            print("\n" + "="*70)
            
        except Exception as e:
            logger.error(f"Ошибка анализа результатов: {e}", exc_info=True)
        
        # Итоговый статус
        print()
        print("="*70)
        if failed == 0:
            print("✅ Все тесты завершены успешно!")
        else:
            print(f"⚠️ Завершено с ошибками: {failed} из {total}")
        print("="*70)
        
        return 0 if failed == 0 else 1
        
    except asyncio.TimeoutError:
        print("❌ Инициализация TestEngine превысила таймаут (10s)")
        return 1
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Завершение работы с правильной очисткой процессов
        try:
            # Даем время на завершение всех процессов
            await asyncio.sleep(1.0)
            await test_engine.shutdown()
        except Exception as e:
            logger.debug(f"Ошибка при завершении TestEngine: {e}")
        
        # Дополнительная очистка для Windows
        try:
            import gc
            gc.collect()
        except Exception:
            pass


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

