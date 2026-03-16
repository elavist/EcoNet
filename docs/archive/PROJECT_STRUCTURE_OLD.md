# Структура проекта SWARM CLEANER

## Обзор

Проект организован согласно ТЗ из `Project Family.docx` с модульной архитектурой для самообучающейся ИИ-системы уборки окурков.

## Корневая структура

```
Project '' Family/
├── README.md                    # Основная документация
├── ARCHITECTURE.md              # Детальная архитектура
├── QUICKSTART.md                # Быстрый старт
├── SETUP_GUIDE.md              # Руководство по установке
├── PROJECT_STRUCTURE.md        # Этот файл
├── requirements.txt            # Python зависимости
├── docker-compose.yml          # Docker Compose конфигурация
│
├── obelisk/                    # ⭐ Обелиск - Центральный мозг
│   ├── __init__.py
│   ├── api/                    # FastAPI REST сервер
│   │   ├── main.py            # Точка входа API
│   │   └── routes/            # API эндпоинты
│   │       ├── detection.py   # Детекции
│   │       ├── tasks.py       # Задачи
│   │       ├── robots.py      # Роботы
│   │       ├── models.py      # Модели
│   │       └── system.py      # Система
│   ├── core/                  # Ядро системы
│   │   ├── unified_engine.py  # Универсальный движок
│   │   ├── model_engine.py    # Движок моделей YOLO
│   │   ├── model_testing.py   # Тестирование моделей
│   │   ├── object_tracker.py  # Отслеживание объектов
│   │   └── neural_nodes.py    # Нейронная архитектура
│   └── services/              # Сервисы Обелиска
│       ├── mqtt_client.py     # MQTT клиент
│       ├── task_manager.py    # Менеджер задач
│       ├── database.py        # База данных
│       ├── trainer.py         # Обучение моделей
│       ├── cache_manager.py   # Управление кэшем
│       ├── model_selector.py  # Выбор моделей
│       ├── annotation_tool.py # Инструмент разметки
│       └── media_manager.py   # Управление медиа
│
├── edge/                       # 🔍 Edge Inference
│   ├── __init__.py
│   ├── inference_service/
│   │   ├── detector.py        # Сервис детекции YOLO
│   │   └── __init__.py
│   └── nav_node/              # Навигация (TODO)
│
├── robots/                     # 🤖 Роботы
│   ├── __init__.py
│   ├── collector/             # Робот-сборщик
│   │   ├── collector_robot.py # Основной модуль робота
│   │   └── __init__.py
│   └── mip_bridge/            # Мост для MiP (TODO)
│
├── models/                     # 🧠 Модели YOLO
│   └── cigarette_detector/
│       └── data.yaml          # Конфигурация датасета
│
├── datasets/                   # 📊 Датасеты
│   └── cigarette_butt/        # Датасет окурков
│       ├── train/             # Обучающая выборка
│       ├── valid/             # Валидационная выборка
│       ├── test/              # Тестовая выборка
│       └── data.yaml          # Конфигурация YOLO
│
├── data/                       # 💾 Data Lake
│   ├── raw/                   # Сырые данные
│   │   ├── frames/            # Кадры для активного обучения
│   │   └── annotations/       # Автоматические аннотации
│   ├── labeled/               # Размеченные данные
│   ├── models/                # Обученные модели
│   └── logs/                  # Логи системы
│
├── config/                     # ⚙️ Конфигурация
│   ├── config.yaml            # Главный конфиг
│   └── config.py              # Загрузка конфига
│
├── scripts/                    # 🔧 Скрипты
│   ├── setup_dataset.py       # Настройка датасета
│   ├── train_model.py         # Обучение модели
│   ├── start_system.py        # Запуск всей системы
│   └── __init__.py
│
├── examples/                   # 📝 Примеры
│   ├── test_detection.py      # Тест детектора
│   ├── test_api.py            # Тест API
│   └── __init__.py
│
├── docker/                     # 🐳 Docker
│   └── obelisk/
│       └── Dockerfile         # Dockerfile для Обелиска
│
├── mosquitto/                  # 📡 MQTT
│   └── config/
│       └── mosquitto.conf     # Конфигурация MQTT брокера
│
├── YOLOv8-main/               # 📦 Существующий YOLO код (legacy)
└── Cigarette Butt Detector.v5i.yolov8/  # 📦 Существующий датасет
```

## Описание модулей

### obelisk/ - Центральный мозг

**Назначение:** Управление всей системой, координация роботов, обучение моделей

**Компоненты:**
- `api/` - REST API для внешнего управления
- `services/mqtt_client.py` - Коммуникация через MQTT
- `services/task_manager.py` - Распределение задач между роботами
- `services/database.py` - Хранение всех данных (SQLite)
- `services/trainer.py` - Активное обучение моделей

**Зависимости:** FastAPI, MQTT, SQLite, Ultralytics YOLO

### edge/inference_service/ - Локальная детекция

**Назначение:** Быстрый инференс YOLO на edge устройствах

**Компоненты:**
- `detector.py` - Обработка видеопотоков, детекция, публикация в MQTT

**Особенности:**
- Поддержка RTSP, веб-камеры, файлов
- Низкая задержка (<100ms)
- Автоматическая публикация детекций

### robots/collector/ - Робот-сборщик

**Назначение:** Физический сбор окурков

**Компоненты:**
- `collector_robot.py` - Логика робота, управление моторами, вакуумом

**Особенности:**
- Подписка на задачи через MQTT
- Публикация статуса и телеметрии
- Heartbeat для мониторинга

### models/ - Модели YOLO

**Назначение:** Хранение обученных моделей и конфигурации

**Файлы:**
- `cigarette_detector/data.yaml` - Связь с датасетом

**Пути моделей:**
- `models/cigarette_detector/best.pt` - Активная модель
- `data/models/model_*.pt` - Версионированные модели

### datasets/ - Датасеты

**Назначение:** Хранение данных для обучения

**Структура:**
- `train/` - Обучающая выборка (7029 изображений)
- `valid/` - Валидационная (1581 изображение)
- `test/` - Тестовая (789 изображений)
- `data.yaml` - Конфигурация для YOLO

**Примечание:** Использует символические ссылки на исходный датасет

### data/ - Data Lake

**Назначение:** Хранение всех данных системы

**Структура:**
- `raw/frames/` - Сырые кадры для активного обучения
- `raw/annotations/` - Автоматические аннотации
- `labeled/` - Размеченные данные
- `models/` - Обученные модели (версионированные)
- `logs/` - Логи системы

### config/ - Конфигурация

**Назначение:** Централизованная конфигурация всей системы

**Файлы:**
- `config.yaml` - Главный конфиг (YAML)
- `config.py` - Python модуль для загрузки

**Секции конфига:**
- `obelisk` - Настройки центрального сервера
- `database` - База данных
- `model` - YOLO модель
- `dataset` - Датасет
- `active_learning` - Активное обучение
- `data_lake` - Пути Data Lake
- `edge` - Edge inference
- `robots` - Роботы
- `mqtt_topics` - MQTT топики
- `logging` - Логирование

### scripts/ - Вспомогательные скрипты

**Скрипты:**
- `setup_dataset.py` - Интеграция существующего датасета
- `train_model.py` - Обучение модели YOLO
- `start_system.py` - Запуск всех компонентов
- `clean_project.py` - Очистка проекта от временных файлов (__pycache__, .cache)

### examples/ - Примеры использования

**Примеры:**
- `test_detection.py` - Тестирование детектора
- `test_api.py` - Тестирование REST API

## Потоки данных

### 1. Детекция → Задача → Сбор

```
Edge Detector
  ↓ (MQTT: obelisk/detection)
Обелиск (Task Manager)
  ↓ (MQTT: obelisk/tasks)
Collector Robot
  ↓ (MQTT: obelisk/tasks/completed)
Обелиск (Database)
```

### 2. Активное обучение

```
Детекции (низкая уверенность)
  ↓
Data Lake (raw/frames)
  ↓
Разметка (оператор/CVAT)
  ↓
Data Lake (labeled)
  ↓
Trainer Service
  ↓
Обучение (fine-tuning)
  ↓
Валидация
  ↓
Деплой (MQTT: obelisk/model/update)
  ↓
Edge Detector (обновление модели)
```

## Интеграция с существующими компонентами

### YOLOv8-main/
- **Статус:** Legacy код, не используется напрямую
- **Использование:** Используем библиотеку `ultralytics` из PyPI
- **Примечание:** Можно удалить после проверки работы

### Cigarette Butt Detector.v5i.yolov8/
- **Статус:** Исходный датасет
- **Интеграция:** `scripts/setup_dataset.py` создает ссылки в `datasets/cigarette_butt/`
- **Сохранение:** Исходный датасет остается нетронутым

## Расширение системы

### Добавление нового робота

1. Создать модуль в `robots/new_robot/`
2. Реализовать интерфейс, совместимый с MQTT топиками
3. Добавить в `task_manager.py` поддержку нового типа задач

### Добавление нового источника детекции

1. Расширить `edge/inference_service/detector.py`
2. Добавить поддержку нового типа источника
3. Обновить конфигурацию

### Добавление новых классов объектов

1. Обновить датасет и разметить новый класс
2. Изменить `data.yaml`: `nc: 3`, добавить класс в `names`
3. Переобучить модель

## Рекомендации по разработке

1. **Модульность:** Каждый компонент независим и тестируем
2. **Конфигурация:** Все настройки в `config/config.yaml`
3. **Логирование:** Использовать стандартный `logging`
4. **Асинхронность:** Использовать `asyncio` для I/O операций
5. **Типизация:** Использовать type hints где возможно
6. **Документация:** Docstrings для всех функций и классов

## Файлы для разработчиков

- `ARCHITECTURE.md` - Полная техническая документация
- `SETUP_GUIDE.md` - Руководство по установке
- `QUICKSTART.md` - Быстрый старт
- `README.md` - Обзор проекта

## Файлы для пользователей

- `QUICKSTART.md` - Быстрый старт
- `examples/test_detection.py` - Примеры использования
- `config/config.yaml` - Настройка системы

