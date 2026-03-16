# ✅ Исправление предупреждения uvicorn

## Проблема

При запуске Обелиска появлялось предупреждение:
```
WARNING:  You must pass the application as an import string to enable 'reload' or 'workers'.
```

## Решение

Исправлен способ запуска uvicorn в `obelisk/api/main.py`:

### Было:
```python
if __name__ == "__main__":
    port = config['obelisk']['port']
    host = config['obelisk']['host']
    uvicorn.run(app, host=host, port=port, reload=True)
```

### Стало:
```python
if __name__ == "__main__":
    port = config['obelisk']['port']
    host = config['obelisk']['host']
    # Используем строку импорта для поддержки reload
    uvicorn.run("obelisk.api.main:app", host=host, port=port, reload=True)
```

## Объяснение

Для использования функции `reload=True` в uvicorn необходимо передавать приложение как строку импорта (`"module:app"`), а не как объект приложения. Это позволяет uvicorn правильно отслеживать изменения в файлах и автоматически перезагружать сервер.

## Результат

✅ Предупреждение устранено  
✅ Автоматическая перезагрузка работает корректно  
✅ Сервер запускается без предупреждений

## Запуск

Теперь Обелиск можно запускать без предупреждений:

```bash
python -m obelisk.api.main
```

## Дополнительно

Создан скрипт для тестирования API:
```bash
python scripts/test_obelisk_api.py
```

Этот скрипт:
- Ожидает запуска сервера
- Проверяет все основные endpoints
- Показывает статус системы
- Выводит детальную информацию о сервисах

