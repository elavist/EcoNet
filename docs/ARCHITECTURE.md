# Полная архитектура проекта SWARM CLEANER

## Обзор системы

SWARM CLEANER - это самообучающаяся ИИ-система для автономной уборки окурков сигарет с использованием роя роботов.

## Структура проекта

```
swarm-cleaner/
├── obelisk/                 # Центральный мозг системы
│   ├── api/                 # FastAPI REST сервер
│   │   ├── main.py          # Главный сервер
│   │   └── routes/          # API роуты
│   │       ├── detection.py # Детекции
│   │       ├── tasks.py     # Задачи
│   │       ├── robots.py    # Роботы
│   │       ├── models.py    # Модели
│   │       └── system.py    # Система
│   ├── core/                # Ядро системы
│   │   ├── unified_engine.py  # Универсальный движок
│   │   ├── model_engine.py    # Движок моделей YOLO
│   │   ├── model_testing.py   # Тестирование моделей
│   │   ├── object_tracker.py  # Отслеживание объектов
│   │   └── neural_nodes.py    # Нейронная архитектура
│   ├── services/            # Сервисы
│   │   ├── mqtt_client.py   # MQTT клиент
│   │   ├── task_manager.py  # Менеджер задач
│   │   ├── database.py      # База данных
│   │   ├── trainer.py       # Обучение моделей
│   │   ├── cache_manager.py # Управление кэшем
│   │   ├── model_selector.py # Выбор моделей
│   │   ├── annotation_tool.py # Инструмент разметки
│   │   └── media_manager.py # Управление медиа
│   └── ui/                  # Material Design GUI
│       ├── gui_material.py  # Главный интерфейс
│       ├── annotation_widget.py # Виджет разметки
│       └── video_display_simple.py # Видеоплеер
│
├── edge/                    # Edge inference устройства
│   └── inference_service/
│       └── detector.py      # Сервис детекции
│
├── robots/                  # Роботы
│   ├── collector/           # Робот-сборщик
│   │   └── collector_robot.py
│   └── mip_bridge/          # Мост для MiP (TODO)
│
├── models/                  # YOLO модели
│   └── cigarette_detector/
│       └── data.yaml        # Конфигурация датасета
│
├── datasets/                # Датасеты
│   └── cigarette_butt/      # Датасет окурков (символические ссылки)
│
├── data/                    # Data Lake
│   ├── raw/                 # Сырые данные
│   │   ├── frames/          # Кадры
│   │   └── annotations/     # Аннотации
│   ├── labeled/             # Размеченные данные
│   ├── models/              # Обученные модели
│   └── logs/                # Логи
│
├── config/                  # Конфигурация
│   ├── config.yaml          # Главный конфиг
│   └── config.py            # Загрузка конфига
│
├── scripts/                 # Вспомогательные скрипты
│   ├── setup_dataset.py     # Настройка датасета
│   └── train_model.py       # Обучение модели
│
├── docker-compose.yml       # Docker Compose
├── requirements.txt         # Python зависимости
└── README.md                # Документация

```

## Компоненты системы

### 1. Обелиск (Obelisk) - Центральный мозг

#### API (FastAPI)
- **Эндпоинты:**
  - `GET /` - Корневой эндпоинт
  - `GET /health` - Проверка здоровья
  - `POST /api/v1/detections` - Создать детекцию
  - `GET /api/v1/detections` - Список детекций
  - `POST /api/v1/tasks` - Создать задачу
  - `GET /api/v1/tasks` - Список задач
  - `GET /api/v1/robots` - Список роботов
  - `POST /api/v1/models/train` - Запустить обучение
  - `POST /api/v1/models/{id}/deploy` - Деплой модели

#### Core (Ядро системы)

**UnifiedEngine (`core/unified_engine.py`)**
- Универсальный движок координации всех компонентов
- Управление детекцией, задачами, роем роботов
- Нейронная архитектура (3 нейрона: YOLO, Coordinator, Information Hub)

**ModelEngine (`core/model_engine.py`)**
- Управление YOLO моделями
- Поддержка ансамбля моделей (weighted, majority, average voting)
- Оптимизация производительности (ONNX, GPU, FP16, batching)
- Приоритет PT моделей над ONNX для гибкости размера

**ModelTesting (`core/model_testing.py`)**
- Тестирование моделей при запуске
- Проверка готовности к работе
- Тестирование с разными параметрами confidence

**ObjectTracker (`core/object_tracker.py`)**
- Отслеживание объектов между кадрами
- IoU-based tracking (IoU >86%)
- Оптимизация детекций (избегание повторной детекции)

#### Сервисы

**MQTT Client (`services/mqtt_client.py`)**
- Подключение к MQTT брокеру
- Публикация/подписка на топики
- Асинхронная обработка сообщений

**Task Manager (`task_manager.py`)**
- Создание задач на основе детекций
- Распределение задач между роботами
- Мониторинг выполнения задач
- Обработка таймаутов

**Database (`database.py`)**
- SQLite база данных (MVP)
- Таблицы: detections, tasks, robots, models
- CRUD операции для всех сущностей

**Trainer (`services/trainer.py`)**
- Обучение YOLO моделей
- Активное обучение (Active Learning)
- Деплой моделей на edge устройства
- Версионирование моделей

**CacheManager (`services/cache_manager.py`)**
- Управление кэшем детекций
- Очистка кэша датасетов (.cache файлы)
- Очистка временных файлов (__pycache__)

**ModelSelector (`services/model_selector.py`)**
- Выбор моделей из сохраненных версий обучения
- Автоматическое копирование и резервное копирование
- Получение списка доступных моделей

**AnnotationTool (`services/annotation_tool.py`)**
- Инструмент ручной разметки
- Сохранение в формате YOLO
- Автоматическое добавление в датасет для обучения
- Сохранение оригинала и размеченного изображения

**MediaManager (`services/media_manager.py`)**
- Управление медиа файлами
- Импорт, удаление, список файлов
- Хранение метаданных и детекций
- Предобработка видео

#### UI (Material Design GUI)

**MaterialEcoNetGUI (`ui/gui_material.py`)**
- Главный интерфейс приложения
- Видеоплеер с управлением (play, pause, stop, seek)
- Инструменты разметки
- Выбор модели и очистка кэша
- Статистика обработки видео

**AnnotationWidget (`ui/annotation_widget.py`)**
- Виджет ручной разметки
- Рисование боксов мышью (drag & drop)
- Сохранение с confidence 100%

**SimpleVideoDisplay (`ui/video_display_simple.py`)**
- Видеоплеер для отображения потоков
- Многопоточная обработка кадров

### 2. Edge Inference Service

**Detector (`edge/inference_service/detector.py`)**
- Локальный инференс YOLO
- Обработка видеопотоков (RTSP, камера, файл)
- Публикация детекций в MQTT
- Поддержка различных источников видео

### 3. Роботы

**Collector Robot (`robots/collector/collector_robot.py`)**
- Подписка на задачи через MQTT
- Навигация к цели
- Сбор объектов (вакуум + манипулятор)
- Публикация статуса и телеметрии
- Heartbeat для мониторинга

### 4. Data Lake

**Структура:**
- `data/raw/frames/` - Сырые кадры
- `data/raw/annotations/` - Автоматические аннотации
- `data/labeled/` - Размеченные данные для обучения
- `data/models/` - Обученные веса моделей
- `data/logs/` - Логи системы

### 5. Активное обучение (Active Learning)

**Процесс:**
1. Сбор кадров с низкой уверенностью (confidence 0.3-0.7)
2. Сохранение в `data/raw/active_learning/`
3. Разметка оператором или полуавтоматически
4. Добавление в тренировочный датасет
5. Дообучение модели (20 эпох)
6. Валидация и деплой при улучшении

## Поток данных

### 1. Детекция
```
Источник видео (телефон/камера)
  ↓
Edge Detector (YOLO inference)
  ↓
MQTT: obelisk/detection
  ↓
Обелиск API → Database
  ↓
Task Manager → Создание задачи
```

### 2. Выполнение задачи
```
Task Manager
  ↓
MQTT: obelisk/tasks
  ↓
Collector Robot (подписка)
  ↓
Навигация к цели
  ↓
Сбор объекта
  ↓
MQTT: obelisk/tasks/completed
  ↓
Task Manager → Обновление статуса
```

### 3. Активное обучение
```
Детекции с низкой уверенностью
  ↓
Сохранение в Data Lake
  ↓
Сбор образцов (min_samples_for_retrain)
  ↓
Разметка (через встроенный инструмент AnnotationTool или CVAT / LabelImg)
  ↓
Добавление в датасет
  ↓
Trainer Service → Дообучение
  ↓
Валидация → mAP улучшение?
  ↓
Деплой на edge устройства (OTA)
```

## MQTT Топики

### Детекции
- `obelisk/detection` - Новые детекции (publish: edge detector)
- Формат: `{id, source, timestamp, bbox, class_name, confidence, frame_id, location}`

### Задачи
- `obelisk/tasks` - Новые задачи (publish: obelisk)
- `robots/{robot_id}/tasks` - Задачи для конкретного робота
- `obelisk/tasks/completed` - Завершенные задачи
- `obelisk/tasks/failed` - Неудачные задачи

### Роботы
- `robots/{robot_id}/status` - Статус робота
- `robots/{robot_id}/telemetry` - Телеметрия
- `robots/{robot_id}/heartbeat` - Heartbeat
- `robots/{robot_id}/commands` - Команды роботу

### Модели
- `obelisk/model/update` - Обновление модели (OTA)
- `obelisk/model/training_completed` - Завершение обучения
- `obelisk/model/training_failed` - Ошибка обучения

### Система
- `obelisk/system/status` - Статус системы

## База данных

### Таблица: detections
```sql
CREATE TABLE detections (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    bbox TEXT NOT NULL,        -- JSON: [x, y, w, h]
    class_name TEXT NOT NULL,
    confidence REAL NOT NULL,
    frame_id TEXT,
    location TEXT,              -- JSON: [lat, lon]
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица: tasks
```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    type TEXT NOT NULL,         -- collect, patrol, return
    status TEXT NOT NULL,       -- pending, assigned, in_progress, completed, failed
    target TEXT NOT NULL,       -- JSON: {bbox, location, frame}
    priority INTEGER NOT NULL,
    assigned_to TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    timeout INTEGER NOT NULL
);
```

### Таблица: robots
```sql
CREATE TABLE robots (
    robot_id TEXT PRIMARY KEY,
    state TEXT NOT NULL,        -- idle, moving, collecting, returning, charging, error
    battery INTEGER NOT NULL,
    position TEXT NOT NULL,     -- JSON: [x, y]
    current_task TEXT,
    last_heartbeat TEXT NOT NULL,
    capabilities TEXT,          -- JSON: [cap1, cap2, ...]
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица: models
```sql
CREATE TABLE models (
    model_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    path TEXT NOT NULL,
    map REAL,                   -- mAP@0.5
    precision REAL,
    recall REAL,
    is_active INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    deployed_at TEXT
);
```

## Конфигурация

### config/config.yaml

Основные секции:
- `obelisk` - Настройки центрального сервера
- `database` - Настройки БД
- `model` - Параметры YOLO модели
- `dataset` - Пути к датасету
- `active_learning` - Параметры активного обучения
- `data_lake` - Пути Data Lake
- `edge` - Настройки edge inference
- `robots` - Настройки роботов
- `mqtt_topics` - MQTT топики
- `logging` - Логирование

## Установка и запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка датасета
```bash
python scripts/setup_dataset.py
```

### 3. Обучение модели (опционально)
```bash
python scripts/train_model.py
```

### 4. Запуск через Docker Compose
```bash
docker-compose up -d mosquitto
docker-compose up obelisk
```

### 5. Запуск вручную

**Обелиск:**
```bash
cd obelisk
python -m api.main
```

**Edge Detector:**
```bash
cd edge/inference_service
python detector.py --source 0  # 0 = камера, или RTSP URL
```

**Collector Robot:**
```bash
cd robots/collector
python collector_robot.py --robot-id collector_01
```

## Активное обучение - Детали реализации

### Сбор неопределенных образцов

```python
# В TrainerService
async def _collect_uncertain_samples(self):
    # Получить детекции с confidence в диапазоне [0.3, 0.7]
    detections = await self.db.get_detections(
        min_confidence=self.al_config["confidence_lower"],
        max_confidence=self.al_config["confidence_upper"]
    )
    
    # Сохранить кадры для разметки
    for det in detections:
        frame_id = det["frame_id"]
        # Загрузить кадр из Data Lake
        # Сохранить в data/raw/active_learning/
```

### Полуавтоматическая разметка

1. YOLO предлагает bounding box
2. Оператор подтверждает/исправляет
3. Экспорт в COCO/YOLO формат
4. Добавление в тренировочный датасет

### Дообучение

```python
# Fine-tuning на новых данных
model = YOLO("models/cigarette_detector/best.pt")
results = model.train(
    data="datasets/cigarette_butt/data.yaml",
    epochs=20,  # Малое количество для дообучения
    batch=16,
    imgsz=640,
    resume=True  # Продолжить с текущих весов
)
```

### Критерии деплоя

- mAP@0.5 улучшился на ≥ 2%
- Precision ≥ 0.85
- Recall ≥ 0.80
- Валидация на тестовом наборе прошла

## Масштабирование

### Горизонтальное масштабирование
- Несколько Edge Detector на разных источниках
- Несколько Collector Robot
- Балансировка нагрузки на Обелиске (Nginx)

### Вертикальное масштабирование
- GPU для обучения на Обелиске
- Jetson Orin для edge inference
- Больше RAM для обработки больших датасетов

## Безопасность

- MQTT over TLS (в production)
- API ключи для REST API
- Шифрование данных в БД
- Ограничение доступа к камерам (GDPR)

## Мониторинг

- Health checks через `/health`
- Статистика через `/api/v1/system/status`
- Логи в `data/logs/system.log`
- MQTT heartbeat для роботов

## Тестовая инфраструктура

Система включает полноценную тестовую инфраструктуру для проверки всех компонентов от А до Я.

### Структура тестов

```
tests/
├── conftest.py              # Конфигурация pytest и фикстуры
├── README.md                # Документация по тестам
├── FINE_TUNING_STRATEGY.md  # Стратегия дообучения на одном файле
├── unit/                    # Unit тесты
│   ├── test_unified_engine.py
│   ├── test_model_engine.py
│   ├── test_object_tracker.py
│   ├── test_model_testing.py
│   └── test_neural_nodes.py
├── integration/             # Интеграционные тесты
│   ├── test_full_pipeline.py
│   └── test_pre_post_deployment.py
├── calibration/             # Тесты калибровки
│   ├── test_model_calibration.py
│   └── test_fine_tuning_calibration.py
└── services/                # Тесты сервисов
    └── test_trainer.py
```

### Типы тестов

#### 1. Unit тесты (`tests/unit/`)

Тестируют отдельные компоненты изолированно:
- **test_unified_engine.py** - тесты UnifiedEngine (инициализация, обработка кадров, статистика)
- **test_model_engine.py** - тесты ModelEngine (детекция, ансамбль, производительность)
- **test_object_tracker.py** - тесты ObjectTracker (отслеживание, IoU, cleanup)
- **test_model_testing.py** - тесты ModelTester (проверка готовности, уровни confidence)
- **test_neural_nodes.py** - тесты нейронных узлов (коммуникация, синхронизация)

#### 2. Интеграционные тесты (`tests/integration/`)

Тестируют взаимодействие компонентов:
- **test_full_pipeline.py** - тесты полного пайплайна (детекция → задача, видео обработка, обучение → деплой, активное обучение)
- **test_pre_post_deployment.py** - тесты до и после деплоя (валидация модели, проверка производительности, метрики, откат)

#### 3. Тесты калибровки (`tests/calibration/`)

Тестируют калибровку параметров и производительность:
- **test_model_calibration.py** - тесты калибровки модели (confidence threshold, IoU threshold, input size, FPS, batch processing)
- **test_fine_tuning_calibration.py** - тесты калибровки дообучения (дообучение на одном файле, 100 эпох, детекция переобучения, early stopping)

#### 4. Тесты сервисов (`tests/services/`)

Тестируют сервисы системы:
- **test_trainer.py** - тесты TrainerService (обучение, дообучение, валидация)

### Запуск тестов

```bash
# Все тесты
pytest tests/

# Только unit тесты
pytest tests/unit/

# Только интеграционные тесты
pytest tests/integration/

# Только тесты калибровки
pytest tests/calibration/

# С покрытием кода
pytest tests/ --cov=obelisk --cov-report=html

# Параллельно (быстрее)
pytest tests/ -n 4
```

### Фикстуры (Fixtures)

Все фикстуры определены в `tests/conftest.py`:

- **Компоненты системы**: `unified_engine`, `model_engine`, `object_tracker`
- **Данные**: `test_image`, `test_video`, `temp_data_dir`
- **Моки**: `mock_database`, `mock_mqtt_client`
- **Конфигурация**: `test_config`, `project_root`

### Тесты калибровки

Особое внимание уделено тестам калибровки:

1. **Калибровка параметров модели**:
   - Confidence threshold (0.1-0.9)
   - IoU threshold (0.3-0.9)
   - Input size (320-832)

2. **Калибровка производительности**:
   - FPS измерение
   - Batch processing
   - Memory usage

3. **Калибровка дообучения**:
   - Fine-tuning на одном файле с 100 эпохами
   - Детекция переобучения
   - Early stopping
   - Валидация после обучения

### Тесты дообучения на одном файле

Система поддерживает дообучение на одном файле с 100 эпохами для адаптации модели под конкретные условия.

**Стратегия дообучения** (подробнее в `tests/FINE_TUNING_STRATEGY.md`):

1. **Обязательно использовать Data Augmentation** - превращает один файл в множество вариаций
2. **Обязательно использовать Early Stopping** - предотвращает переобучение
3. **Обязательно валидировать** - проверяет, что модель не потеряла обобщающую способность
4. **Обязательно мониторить метрики** - отслеживает все метрики во время обучения

**Риски**:
- Переобучение (Overfitting) - основная проблема
- Потеря общей точности - модель может начать хуже работать на других данных

**Рекомендации**:
- Использовать augmentation (flip, crop, color jitter, rotation, blur)
- Использовать early stopping с patience
- Использовать отдельный validation set
- Использовать learning rate schedule
- Мониторить training/validation loss
- Сохранять лучшую модель во время обучения

### Тесты до и после деплоя

Система включает полный цикл тестирования:

**Перед деплоем**:
- Валидация модели
- Проверка производительности (FPS)
- Проверка точности (precision/recall)
- Сравнение с предыдущей моделью

**После деплоя**:
- Функциональность модели
- Стабильность системы
- Метрики работы

**Откат деплоя**:
- Резервное копирование перед деплоем
- Возможность отката к предыдущей версии

### CI/CD интеграция

Тесты можно интегрировать в CI/CD пайплайн:

```yaml
# GitHub Actions пример
- name: Run tests
  run: pytest tests/ -v --junitxml=report.xml
- name: Upload coverage
  uses: codecov/codecov-action@v2
```

### Документация

- **tests/README.md** - полная документация по тестам
- **tests/FINE_TUNING_STRATEGY.md** - стратегия дообучения на одном файле

## Будущие улучшения

- [ ] ROS 2 интеграция
- [ ] SLAM для навигации
- [ ] Reinforcement Learning для стратегии роя
- [x] Material Design GUI интерфейс (`obelisk/ui/gui_material.py`) - реализовано
- [ ] PostgreSQL вместо SQLite
- [ ] Kubernetes deployment
- [ ] Prometheus метрики

