# ✅ Исправление Краша при Запуске

## Проблема
```
AttributeError: 'MaterialEcoNetGUI' object has no attribute '_update_timeline'
```

## Причина
При переделке системы видео на `SimpleVideoDisplay` был удален метод `_update_timeline()`, но его вызов остался в `__init__`.

## Решение
✅ Убран вызов несуществующего метода `_update_timeline()` из `__init__`

**Изменение:**
```python
# Было:
self.update_video()
self._update_timeline()  # ❌ Метод не существует

# Стало:
self.update_video()  # ✅ Только обновление видео
```

## Статус: ✅ ИСПРАВЛЕНО

Теперь программа должна запускаться без ошибок.

