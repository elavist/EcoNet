# Быстрый старт - SWARM CLEANER

## Шаг 1: Установка зависимостей

```bash
pip install -r requirements.txt
```

## Шаг 2: Настройка датасета

Существующий датасет в `Cigarette Butt Detector.v5i.yolov8` нужно интегрировать в систему:

```bash
python scripts/setup_dataset.py
```

Этот скрипт:
- Создаст символические ссылки или скопирует данные в `datasets/cigarette_butt/`
- Создаст `datasets/cigarette_butt/data.yaml`
- Обновит конфигурацию в `config/config.yaml`

## Шаг 3: Обучение модели (опционально)

Если у вас уже есть обученная модель, пропустите этот шаг.

Для обучения новой модели:

```bash
python scripts/train_model.py
```

Модель будет сохранена в `models/cigarette_detector/best.pt`

## Шаг 4: Запуск MQTT брокера

### Вариант A: Docker (рекомендуется)

```bash
docker-compose up -d mosquitto
```

### Вариант B: Локальная установка

Установите Mosquitto и запустите:
```bash
mosquitto -c mosquitto/config/mosquitto.conf
```

## Шаг 5: Запуск системы

### Вариант A: Полный запуск через скрипт (РЕКОМЕНДУЕТСЯ)

```bash
python scripts/start_econet_system.py
```

Или через батник (Windows):
```bash
ЗАПУСТИТЬ_ЭКОНЕТ.bat
```

Скрипт автоматически:
- ✅ Проверяет MQTT брокер
- ✅ Запускает Обелиск (API сервер)
- ✅ Инициализирует все компоненты (база данных, MQTT, нейроны, GPU система)
- ✅ Запускает GUI интерфейс
- ✅ Проверяет здоровье системы
- ✅ Отображает статус всех сервисов

**Опции запуска:**
```bash
# Запуск без GUI (только API)
python scripts/start_econet_system.py --no-gui
```

### Вариант B: Запуск компонентов по отдельности

**1. Обелиск (центральный мозг) - API:**
```bash
python -m obelisk.api.main
```

Откройте в браузере: http://localhost:8000/docs

**2. GUI интерфейс (Material Design):**
```bash
python -m obelisk.ui.gui_material
```

GUI включает:
- Видеоплеер с управлением
- Детекцию в реальном времени
- Инструменты разметки
- Выбор модели
- Очистку кэша

**2. Edge Detector (детектор на видеопотоке):**
```bash
cd edge/inference_service
python detector.py --source 0  # 0 = веб-камера, или RTSP URL
```

**3. Collector Robot (робот-сборщик):**
```bash
cd robots/collector
python collector_robot.py --robot-id collector_01
```

## Проверка работы

### 1. Проверка Обелиска

```bash
curl http://localhost:8000/health
```

Должен вернуть:
```json
{
  "status": "healthy",
  "services": {
    "mqtt": true,
    "database": true,
    "task_manager": true,
    "neural_network": true,
    "gpu_system": true,
    "collective_mind": true
  }
}
```

### 2. Проверка API

Откройте Swagger UI: http://localhost:8000/docs

### 3. Проверка детекций

Edge Detector должен публиковать детекции в MQTT топик `obelisk/detection`.

Проверить через API:
```bash
curl http://localhost:8000/api/v1/detections
```

### 4. Проверка задач

После получения детекции, Обелиск автоматически создаст задачу.

Проверить задачи:
```bash
curl http://localhost:8000/api/v1/tasks
```

## Тестирование с видеофайлом

```bash
python edge/inference_service/detector.py --source path/to/video.mp4
```

## Тестирование с RTSP потоком

```bash
python edge/inference_service/detector.py --source rtsp://user:password@ip:port/stream
```

## Мониторинг

### Логи

Логи системы находятся в `data/logs/system.log`

### Статистика через API

```bash
curl http://localhost:8000/api/v1/system/status
```

### Статистика роботов

```bash
curl http://localhost:8000/api/v1/robots
```

## Следующие шаги

1. **Обучение модели:** Если модель не обучена, используйте `scripts/train_model.py`
2. **Активное обучение:** Включите в `config/config.yaml`:
   ```yaml
   active_learning:
     enabled: true
   ```
3. **Настройка роботов:** Подключите реальное оборудование в `robots/collector/collector_robot.py`
4. **GUI интерфейс:** Запустите Material Design GUI:
   ```bash
   python -m obelisk.ui.gui_material
   ```

## Устранение неполадок

### MQTT не подключается
- Проверьте, запущен ли Mosquitto: `docker ps`
- Проверьте конфигурацию в `config/config.yaml`

### Модель не найдена
- Убедитесь, что путь в `config/config.yaml` → `model.weights_path` правильный
- Или обучите модель: `python scripts/train_model.py`

### Ошибки импорта
- Убедитесь, что установлены все зависимости: `pip install -r requirements.txt`
- Проверьте, что вы запускаете скрипты из корневой директории проекта

### База данных SQLite
- База данных создается автоматически при первом запуске
- Расположение: `data/obelisk.db` (или путь из конфигурации)

## Документация

- `README.md` - Общая информация
- `ARCHITECTURE.md` - Детальная архитектура системы
- `config/config.yaml` - Конфигурация всех компонентов

