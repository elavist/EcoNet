# 🖥️ Запуск графического интерфейса ЭкоНет

## Автоматический запуск (рекомендуется)

Система теперь автоматически запускает GUI интерфейс вместе с API сервером:

```bash
python scripts/start_econet_system.py
```

Или двойной клик на файл:
```
ЗАПУСТИТЬ_ЭКОНЕТ.bat
```

Это запустит:
1. ✅ MQTT брокер (если доступен)
2. ✅ API сервер Обелиск (http://localhost:8000)
3. ✅ Графический интерфейс (GUI)

## Запуск только API сервера (без GUI)

Если нужен только API сервер без графического интерфейса:

```bash
python scripts/start_econet_system.py --no-gui
```

## Запуск только GUI (без скрипта запуска)

Если API сервер уже запущен и нужно только GUI:

```bash
python scripts/run_econet.py
```

Или:

```bash
python scripts/run_gui.py
```

## Доступные GUI интерфейсы

Система автоматически выберет лучший доступный интерфейс:

1. **Material Design** (если установлен CustomTkinter) - `obelisk/ui/gui_material.py`
2. **Modern GUI** (CustomTkinter) - `obelisk/ui/gui_modern.py`
3. **Cyberpunk GUI** (Tkinter) - `obelisk/ui/gui_app_cyberpunk.py` - fallback

## Устранение проблем

### GUI не открывается

1. **Проверьте, что API сервер запущен:**
   ```bash
   python -m obelisk.api.main
   ```

2. **Запустите GUI отдельно:**
   ```bash
   python scripts/run_econet.py
   ```

3. **Проверьте зависимости:**
   ```bash
   pip install customtkinter  # Для современного интерфейса
   ```

### GUI открывается, но нет видео

1. Убедитесь, что источник видео доступен (камера, файл, IP-камера)
2. Проверьте настройки в конфигурации
3. Откройте веб-интерфейс: http://localhost:8000/chat

## Веб-интерфейс (альтернатива)

Если GUI не работает, можно использовать веб-интерфейс:

1. Запустите API сервер:
   ```bash
   python -m obelisk.api.main
   ```

2. Откройте в браузере:
   - **Чат:** http://localhost:8000/chat
   - **Документация API:** http://localhost:8000/docs

## Дополнительная информация

- API сервер: http://localhost:8000
- Документация API: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Веб-чат: http://localhost:8000/chat

