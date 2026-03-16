# Исправление проблем с тестами

## Проблемы которые были исправлены

### 1. ✅ pytest-asyncio не был правильно настроен

**Проблема**: Все async тесты падали с ошибкой "async def functions are not natively supported"

**Решение**:
- Создан `pytest.ini` с настройками для `pytest-asyncio`
- Убрана кастомная `event_loop` фикстура из `conftest.py` (она конфликтовала с pytest-asyncio)
- Установлены все необходимые пакеты: `pytest-asyncio`, `pytest-cov`, `pytest-xdist`, `pytest-mock`

### 2. ✅ pytest-cov не был установлен

**Проблема**: Команда `--cov=obelisk` не работала

**Решение**: Установлен `pytest-cov`

### 3. ✅ Неизвестные маркеры

**Проблема**: Предупреждения о неизвестных маркерах `pytest.mark.asyncio`

**Решение**: Добавлены маркеры в `pytest.ini`:
- `asyncio` - для async тестов
- `slow` - для медленных тестов
- `integration` - для интеграционных тестов
- `unit` - для unit тестов
- `calibration` - для тестов калибровки
- `services` - для тестов сервисов

## Как теперь запускать тесты

### Все тесты
```bash
pytest tests/ -v
```

### С покрытием кода
```bash
pytest tests/ --cov=obelisk --cov-report=html
```

### Только async тесты
```bash
pytest tests/ -m asyncio -v
```

### Без async тестов
```bash
pytest tests/ -m "not asyncio" -v
```

### Параллельно
```bash
pytest tests/ -n 4
```

## Файлы которые были созданы/изменены

1. **pytest.ini** - новая конфигурация pytest
2. **tests/conftest.py** - убрана конфликтующая event_loop фикстура
3. **tests/unit/test_model_engine.py** - исправлен тест test_detection_format

## Следующие шаги

1. Запустить тесты снова:
   ```bash
   pytest tests/ -v
   ```

2. Проверить покрытие кода:
   ```bash
   pytest tests/ --cov=obelisk --cov-report=html
   ```

3. Все async тесты теперь должны работать!

