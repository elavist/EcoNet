# Руководство по установке и настройке

## Системные требования

- Python 3.8+
- 8GB+ RAM (рекомендуется 16GB)
- SSD для хранения данных
- GPU (опционально, для обучения моделей)
- Docker и Docker Compose (опционально, для MQTT брокера)

## Пошаговая установка

### Шаг 1: Клонирование и подготовка

```bash
# Если проект уже есть, перейти в директорию
cd "Project '' Family"

# Создать виртуальное окружение (рекомендуется)
python -m venv venv

# Активировать виртуальное окружение
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### Шаг 2: Установка зависимостей

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 3: Настройка датасета

Существующий датасет `Cigarette Butt Detector.v5i.yolov8` нужно интегрировать:

```bash
python scripts/setup_dataset.py
```

Этот скрипт:
- ✅ Создаст структуру `datasets/cigarette_butt/`
- ✅ Скопирует/создаст ссылки на изображения и метки
- ✅ Создаст `datasets/cigarette_butt/data.yaml`
- ✅ Обновит `config/config.yaml`

**Проверка:**
```bash
ls datasets/cigarette_butt/
# Должны быть директории: train, valid, test, и файл data.yaml
```

### Шаг 4: Обучение модели (если нужно)

Если у вас уже есть обученная модель `best.pt`, разместите её в:
```
models/cigarette_detector/best.pt
```

И обновите путь в `config/config.yaml`:
```yaml
model:
  weights_path: "models/cigarette_detector/best.pt"
```

**Или обучите новую модель:**
```bash
python scripts/train_model.py
```

Это займет время (зависит от железа):
- CPU: ~4-8 часов для 100 эпох
- GPU: ~30-60 минут для 100 эпох

### Шаг 5: Настройка MQTT брокера

#### Вариант A: Docker (рекомендуется)

```bash
# Создать директории для Mosquitto
mkdir -p mosquitto/config mosquitto/data mosquitto/log

# Запустить MQTT брокер
docker-compose up -d mosquitto

# Проверить статус
docker ps | grep mosquitto
```

#### Вариант B: Локальная установка

**Windows:**
1. Скачать Mosquitto: https://mosquitto.org/download/
2. Установить
3. Запустить из установочной директории:
```bash
mosquitto -c mosquitto/config/mosquitto.conf
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients

# Копировать конфигурацию
sudo cp mosquitto/config/mosquitto.conf /etc/mosquitto/conf.d/

# Запустить
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

**Mac:**
```bash
brew install mosquitto
brew services start mosquitto
```

### Шаг 6: Проверка конфигурации

Откройте `config/config.yaml` и проверьте:

```yaml
obelisk:
  host: "localhost"
  port: 8000
  mqtt_broker: "localhost"  # Или IP адрес
  mqtt_port: 1883

model:
  weights_path: "models/cigarette_detector/best.pt"  # Должен существовать
  data_config: "datasets/cigarette_butt/data.yaml"

dataset:
  base_path: "datasets/cigarette_butt"
```

### Шаг 7: Создание директорий

```bash
# Создать структуру Data Lake
mkdir -p data/raw/frames
mkdir -p data/raw/annotations
mkdir -p data/labeled
mkdir -p data/models
mkdir -p data/logs
```

Или просто запустить систему - директории создадутся автоматически.

### Шаг 8: Первый запуск

#### Быстрый тест детектора:

```bash
# Тест на изображении
python examples/test_detection.py --mode image

# Тест на камере
python examples/test_detection.py --mode video
```

#### Запуск системы:

**Вариант 1: Полный запуск через скрипт (РЕКОМЕНДУЕТСЯ):**
```bash
python scripts/start_econet_system.py
```

Или через батник (Windows):
```bash
ЗАПУСТИТЬ_ЭКОНЕТ.bat
```

Скрипт автоматически:
- Проверяет MQTT брокер
- Запускает Обелиск (API сервер)
- Инициализирует все компоненты:
  - База данных (SQLite)
  - MQTT клиент
  - Менеджер задач
  - Сервис обучения
  - Активное обучение
  - Визуальный контекст
  - GPU венозная система
  - Нейронная сеть (4 базовых нейрона)
  - Система самоидентификации
- Запускает GUI интерфейс
- Проверяет здоровье системы

**Опции запуска:**
```bash
# Запуск без GUI (только API)
python scripts/start_econet_system.py --no-gui
```

**Вариант 2: Запуск компонентов по отдельности:**

# Терминал 1: Обелиск API (центральный мозг)
python -m obelisk.api.main
# API будет доступен на http://localhost:8000

# Терминал 2: GUI интерфейс (Material Design)
python -m obelisk.ui.gui_material

# Терминал 3: Edge Detector (опционально, если не используется GUI)
python edge/inference_service/detector.py --source 0

# Терминал 4: Робот (опционально)
python robots/collector/collector_robot.py --robot-id collector_01
```

### Шаг 9: Проверка работы

1. **Проверка Обелиска:**
```bash
curl http://localhost:8000/health
# Или откройте в браузере: http://localhost:8000/docs
```

2. **Тест API:**
```bash
python examples/test_api.py
```

3. **Проверка детекций:**
```bash
curl http://localhost:8000/api/v1/detections/
```

## Конфигурация для разных окружений

### Разработка (Development)

```yaml
# config/config.yaml
obelisk:
  host: "localhost"
  port: 8000

database:
  type: "sqlite"
  sqlite_path: "data/obelisk_dev.db"

logging:
  level: "DEBUG"
```

### Тестирование (Testing)

```yaml
database:
  type: "sqlite"
  sqlite_path: "data/obelisk_test.db"

active_learning:
  enabled: false  # Отключить для тестов
```

### Продакшн (Production)

```yaml
obelisk:
  host: "0.0.0.0"  # Принимать внешние подключения
  enable_tls: true

database:
  type: "postgresql"
  postgresql:
    host: "postgres.example.com"
    database: "swarm_cleaner_prod"

security:
  enable_encryption: true
  api_key_required: true

logging:
  level: "INFO"
```

## Устранение неполадок

### Проблема: "ModuleNotFoundError: No module named 'ultralytics'"

**Решение:**
```bash
pip install ultralytics>=8.0.0
```

### Проблема: "MQTT connection failed"

**Решение:**
1. Проверить, запущен ли Mosquitto:
```bash
docker ps | grep mosquitto
# Или
ps aux | grep mosquitto
```

2. Проверить конфигурацию в `config/config.yaml`
3. Проверить firewall (порт 1883 должен быть открыт)

### Проблема: "Model not found"

**Решение:**
1. Проверить путь в `config/config.yaml` → `model.weights_path`
2. Обучить модель: `python scripts/train_model.py`
3. Или скачать предобученную модель

### Проблема: "Database is locked" (SQLite)

**Решение:**
- Убедитесь, что только один процесс использует БД
- Закройте другие подключения к `data/obelisk.db`

### Проблема: "CUDA out of memory" (обучение)

**Решение:**
- Уменьшить batch size в `config/config.yaml`:
```yaml
active_learning:
  retrain_batch_size: 8  # Вместо 16
```

### Проблема: Медленная детекция

**Решение:**
- Использовать более легкую модель: `yolov8n` вместо `yolov8s`
- Уменьшить размер изображения:
```yaml
model:
  input_size: 416  # Вместо 640
```

## Следующие шаги

После успешной установки:

1. **Прочитайте** `QUICKSTART.md` для быстрого старта
2. **Изучите** `ARCHITECTURE.md` для понимания системы
3. **Настройте** активное обучение в `config/config.yaml`
4. **Подключите** реальное оборудование роботов
5. **Настройте** мониторинг и логирование

## Получение помощи

Если возникли проблемы:
1. Проверьте логи: `data/logs/system.log`
2. Проверьте документацию в `docs/`
3. Используйте Swagger UI: http://localhost:8000/docs

