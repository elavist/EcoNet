# Тестовая инфраструктура ЭКОНЕТ (EcoNet)

Полноценная система тестирования всех компонентов системы с использованием нейронной архитектуры и GPU венозной системы.

**Статус (2025-11-21):** ✅ Тесты полностью переработаны и готовы к использованию
- ✅ Тесты подключены к GPU венозной системе (Veins)
- ✅ Прогресс-мониторинг каждые 5-10 секунд
- ✅ Все тесты синхронные, используют mock объекты (нет зависаний)
- ✅ 15 тестов в 3 группах, все проходят за 0.17 секунды
- ✅ Последовательное выполнение групп тестов

## 🚀 Быстрый запуск

**Рекомендуется - через TestEngine (с нейронной архитектурой):**
```bash
# Windows
tests\run_all_via_test_engine.bat

# Linux/Mac
python tests/run_all_via_test_engine.py
```

**Напрямую через pytest:**
```bash
# Все тесты
pytest tests/ -v

# Только unit тесты
pytest tests/unit/ -v

# Конкретный файл
pytest tests/unit/test_model_testing.py -v
```

## 📁 Структура тестов

```
tests/
├── __init__.py
├── conftest.py                    # Конфигурация pytest и фикстуры
├── README.md                       # Этот файл
├── run_all_via_test_engine.py     # Основной скрипт запуска через TestEngine
├── run_all_via_test_engine.bat    # Windows скрипт запуска
├── FINE_TUNING_STRATEGY.md         # Стратегия дообучения на одном файле
├── unit/                           # Unit тесты
│   ├── __init__.py
│   ├── test_unified_engine.py
│   ├── test_model_engine.py
│   ├── test_object_tracker.py
│   ├── test_model_testing.py
│   ├── test_test_engine.py
│   └── test_neural_nodes.py
├── integration/                    # Интеграционные тесты
│   ├── __init__.py
│   ├── test_full_pipeline.py
│   └── test_pre_post_deployment.py
├── calibration/                    # Тесты калибровки
│   ├── __init__.py
│   ├── test_model_calibration.py
│   └── test_fine_tuning_calibration.py
└── services/                       # Тесты сервисов
    ├── __init__.py
    └── test_trainer.py
```

## 🧪 Типы тестов

### 1. Unit тесты (`tests/unit/`)

Тестируют отдельные компоненты изолированно:

- **test_unified_engine.py** - тесты UnifiedEngine
- **test_model_engine.py** - тесты ModelEngine
- **test_object_tracker.py** - тесты ObjectTracker
- **test_model_testing.py** - тесты ModelTester (3 группы: Basic, WithMock, Safety)
- **test_test_engine.py** - тесты TestEngine
- **test_neural_nodes.py** - тесты нейронных узлов

### 2. Интеграционные тесты (`tests/integration/`)

Тестируют взаимодействие компонентов:

- **test_full_pipeline.py** - тесты полного пайплайна работы системы
- **test_pre_post_deployment.py** - тесты до и после деплоя

### 3. Тесты калибровки (`tests/calibration/`)

Тестируют калибровку параметров и производительность:

- **test_model_calibration.py** - тесты калибровки модели
- **test_fine_tuning_calibration.py** - тесты калибровки дообучения

### 4. Тесты сервисов (`tests/services/`)

Тестируют сервисы системы:

- **test_trainer.py** - тесты TrainerService

## 🔧 TestEngine - Нейронная архитектура для тестов

TestEngine использует нейронную архитектуру для координации тестов:

- **TestRunnerNeuron** - запуск тестов
- **TestCoordinatorNeuron** - координация тестов
- **TestHubNeuron** - центральный узел информации
- **TestAnalyzerNeuron** - анализ результатов

### Преимущества TestEngine:

1. **GPU венозная система** - автоматическое управление GPU ресурсами
2. **Прогресс-мониторинг** - видимый прогресс каждые 5-10 секунд
3. **Подробная статистика** - детальная информация о выполнении тестов
4. **Нейронная координация** - умное распределение ресурсов

## 📊 Запуск тестов

### Запуск всех тестов

```bash
# Через TestEngine (рекомендуется)
tests\run_all_via_test_engine.bat

# Напрямую через pytest
pytest tests/ -v
```

### Запуск конкретной категории тестов

```bash
# Только unit тесты
pytest tests/unit/ -v

# Только интеграционные тесты
pytest tests/integration/ -v

# Только тесты калибровки
pytest tests/calibration/ -v

# Только тесты сервисов
pytest tests/services/ -v
```

### Запуск конкретного файла тестов

```bash
# Тесты UnifiedEngine
pytest tests/unit/test_unified_engine.py -v

# Тесты ModelEngine
pytest tests/unit/test_model_engine.py -v

# Тесты ObjectTracker
pytest tests/unit/test_object_tracker.py -v
```

### Запуск конкретного теста

```bash
# Запустить один тест
pytest tests/unit/test_unified_engine.py::TestUnifiedEngine::test_initialization -v

# Запустить все тесты в классе
pytest tests/unit/test_unified_engine.py::TestUnifiedEngine -v
```

## 🎯 Фикстуры (Fixtures)

Все фикстуры определены в `tests/conftest.py`:

### Основные фикстуры

- **`project_root`** - корневая директория проекта
- **`test_config`** - тестовая конфигурация
- **`temp_dir`** - временная директория для тестов (автоматически очищается)
- **`temp_data_dir`** - временная директория для данных
- **`test_image`** - тестовое изображение (640x480)
- **`test_video`** - тестовое видео файл

### Компоненты системы

- **`unified_engine`** - инициализированный UnifiedEngine (таймаут 2 минуты)
- **`model_engine`** - инициализированный ModelEngine
- **`object_tracker`** - инициализированный ObjectTracker
- **`test_engine`** - инициализированный TestEngine

### Моки

- **`mock_database`** - мок базы данных
- **`mock_mqtt_client`** - мок MQTT клиента

## 📝 Написание новых тестов

### Шаблон unit теста

```python
import pytest
from obelisk.core.some_module import SomeClass


class TestSomeClass:
    """Тесты SomeClass"""
    
    def test_initialization(self, test_config):
        """Тест инициализации"""
        obj = SomeClass(test_config)
        assert obj is not None
    
    @pytest.mark.asyncio
    async def test_async_method(self, some_fixture):
        """Тест асинхронного метода"""
        result = await some_fixture.async_method()
        assert result is not None
```

### Шаблон интеграционного теста

```python
import pytest


class TestIntegration:
    """Интеграционные тесты"""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self, unified_engine, test_image):
        """Тест полного пайплайна"""
        # 1. Шаг 1
        result1 = await unified_engine.step1(test_image)
        
        # 2. Шаг 2
        result2 = await unified_engine.step2(result1)
        
        # 3. Проверка результата
        assert result2 is not None
```

## ⚙️ Параметры запуска

### Параллельный запуск

Для ускорения тестов можно использовать `pytest-xdist`:

```bash
pip install pytest-xdist

# Запустить тесты параллельно на 4 ядрах
pytest tests/ -n 4
```

### Покрытие кода (Code Coverage)

Для проверки покрытия кода тестами:

```bash
pip install pytest-cov

# Запустить тесты с покрытием
pytest tests/ --cov=obelisk --cov-report=html

# Просмотреть отчет
# Откроется HTML файл в браузере: htmlcov/index.html
```

## 🔍 Отладка тестов

### Подробный вывод

```bash
# С подробным выводом
pytest tests/ -v -s

# С полным traceback
pytest tests/ -v --tb=long

# Остановка на первой ошибке
pytest tests/ -v -x
```

### Запуск только упавших тестов

```bash
# Запустить только упавшие тесты из предыдущего запуска
pytest tests/ --lf

# Запустить упавшие тесты и новые
pytest tests/ --ff
```

## 📚 Полезные ссылки

- [Документация pytest](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Стратегия дообучения](FINE_TUNING_STRATEGY.md)

## ⚠️ Важные замечания

1. **Синхронные тесты** - все тесты ModelTester полностью синхронные, используют mock объекты
2. **GPU ресурсы** - автоматически запрашиваются и освобождаются через венозную систему
3. **Прогресс-мониторинг** - обновления каждые 5-10 секунд
4. **Последовательное выполнение** - группы тестов выполняются строго последовательно
5. **Быстрота** - все 15 тестов выполняются за ~0.17 секунды

## 🎯 Рекомендации

1. **Запускайте тесты перед коммитом:**
   ```bash
   tests\run_all_via_test_engine.bat
   ```

2. **Проверяйте покрытие кода:**
   ```bash
   pytest tests/ --cov=obelisk --cov-report=term-missing
   ```

3. **Добавляйте новые тесты** при добавлении нового функционала

4. **Обновляйте тесты** при изменении API
