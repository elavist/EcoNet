# TestEngine - Тестовый движок ЭкоНет

## Обзор

`TestEngine` - это отдельный движок для управления тестами с собственной нейронной архитектурой. Он обеспечивает координацию, выполнение и анализ тестов через систему нейронных узлов.

## Архитектура

TestEngine использует нейронную архитектуру из 4 специализированных узлов:

1. **TestRunnerNeuron** - запуск и выполнение тестов
2. **TestCoordinatorNeuron** - координация последовательности тестов
3. **TestHubNeuron** - центральный узел сбора информации о тестах
4. **TestAnalyzerNeuron** - анализ результатов тестов

## Структура связей

```
TestCoordinatorNeuron
    ↓ (command)
TestRunnerNeuron
    ↓ (data)
TestHubNeuron ← (data) ← TestAnalyzerNeuron
    ↓ (feedback)
TestCoordinatorNeuron
```

## Использование

### Базовое использование

```python
from obelisk.core.test_engine import TestEngine
import asyncio

async def main():
    # Создание тестового движка
    config = {...}  # Конфигурация системы
    test_engine = TestEngine(config)
    
    # Инициализация
    await test_engine.initialize()
    
    # Запуск группы тестов
    result = await test_engine.run_test_group("TestModelTesterBasic")
    
    # Анализ результатов
    analysis = await test_engine.analyze_test_results(result)
    
    # Получение статистики
    stats = test_engine.get_statistics()
    
    print(f"Статистика: {stats}")

asyncio.run(main())
```

### Запуск тестов по иерархии

```python
# Группы тестов в порядке выполнения
test_groups = [
    "TestModelTesterBasic",           # Группа 1: быстрые тесты
    "TestModelTesterWithEngine",      # Группа 2: тесты с unified_engine
    "TestModelTesterConfidenceLevels", # Группа 3: тесты с confidence
    "TestModelTesterResults"          # Группа 4: тесты результатов
]

for group in test_groups:
    result = await test_engine.run_test_group(group)
    print(f"{group}: {result['success']}")
```

## Нейронные узлы

### TestRunnerNeuron

Отвечает за выполнение тестов через pytest.

**Методы:**
- `run_test(test_name, test_path)` - запуск теста

**Пример:**
```python
runner = test_engine.test_neural_architecture.test_runner_neuron
result = await runner.run_test("TestModelTesterBasic::test_initialization")
```

### TestCoordinatorNeuron

Координирует последовательность выполнения тестов.

**Методы:**
- `run_test_group(group_name, test_path)` - запуск группы тестов

**Пример:**
```python
coordinator = test_engine.test_neural_architecture.test_coordinator_neuron
result = await coordinator.run_test_group("TestModelTesterBasic")
```

### TestHubNeuron

Собирает и хранит информацию о всех тестах.

**Методы:**
- `get_statistics()` - получение статистики
- `get_test_info(test_name)` - информация о конкретном тесте

**Пример:**
```python
hub = test_engine.test_neural_architecture.test_hub_neuron
stats = hub.get_statistics()
print(f"Всего тестов: {stats['total_tests']}")
```

### TestAnalyzerNeuron

Анализирует результаты тестов и предоставляет рекомендации.

**Методы:**
- `analyze(results)` - анализ результатов

**Пример:**
```python
analyzer = test_engine.test_neural_architecture.test_analyzer_neuron
analysis = await analyzer.analyze(test_results)
print(f"Рекомендации: {analysis['recommendations']}")
```

## Интеграция с существующими тестами

TestEngine может быть использован в существующих тестах:

```python
# tests/unit/test_model_testing.py
@pytest.mark.asyncio
async def test_with_test_engine(test_config):
    from obelisk.core.test_engine import TestEngine
    
    engine = TestEngine(test_config)
    await engine.initialize()
    
    # Запуск тестов через движок
    result = await engine.run_test_group("TestModelTesterBasic")
    assert result["success"] is True
```

## Статистика

TestEngine собирает статистику о выполнении тестов:

```python
stats = test_engine.get_statistics()
# {
#     "total_tests": 10,
#     "passed_tests": 8,
#     "failed_tests": 1,
#     "skipped_tests": 1,
#     "test_groups": {
#         "TestModelTesterBasic": {
#             "total": 3,
#             "passed": 3,
#             "failed": 0
#         }
#     },
#     "last_run": "2025-01-20T12:00:00"
# }
```

## Преимущества

1. **Нейронная архитектура** - координация через нейронные связи
2. **Автоматический анализ** - анализ результатов и рекомендации
3. **Централизованная статистика** - сбор информации о всех тестах
4. **Гибкость** - легко расширяемая архитектура
5. **Интеграция** - работает с существующей системой тестирования

## Файлы

- `obelisk/core/test_engine.py` - основной движок
- `obelisk/core/test_neural_nodes.py` - нейронные узлы
- `tests/unit/test_test_engine.py` - тесты движка

