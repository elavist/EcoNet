# ✅ Исправление ошибки запуска Обелиска

## Проблема

При запуске Обелиска возникала ошибка:
```
TypeError: TaskManager.__init__() missing 1 required positional argument: 'mqtt_client'
```

Ошибка происходила в `obelisk/api/main.py` на строке 53 при инициализации `TaskManager`.

## Причина

Неправильный порядок аргументов при создании `TaskManager`. 

**Сигнатура `TaskManager.__init__()`:**
```python
def __init__(self, config: Dict, database, mqtt_client):
```

**Неправильный вызов:**
```python
task_manager = TaskManager(mqtt_client, db)  # ❌ Неправильный порядок и не хватает config
```

## Решение

Исправлен вызов `TaskManager` в `obelisk/api/main.py`:

### Было:
```python
task_manager = TaskManager(mqtt_client, db)
```

### Стало:
```python
task_manager = TaskManager(config, db, mqtt_client)
```

## Результат

✅ Ошибка исправлена  
✅ `TaskManager` инициализируется с правильными аргументами  
✅ Импорт модуля успешен  
✅ Обелиск готов к запуску

## Проверка

Импорт модуля успешен:
```bash
python -c "from obelisk.api.main import app; print('Import successful')"
# Output: Import successful
```

## Запуск

Теперь Обелиск должен запускаться без ошибок:

```bash
python -m obelisk.api.main
```

## Статус

✅ **Исправлено и готово к использованию**

