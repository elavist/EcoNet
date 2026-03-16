# 🧠 Полная архитектура системы ЭкоНет

**Обновлено:** 2025-11-22  
**Версия:** 1.0 (Стабильная)  
**Статус:** ✅ Полностью функциональна

---

## 📋 Содержание

1. [Обзор системы](#обзор-системы)
2. [Архитектура системы](#архитектура-системы)
3. [Нейроны (Neurons)](#нейроны-neurons)
4. [Вены (Veins) - GPU система](#вены-veins---gpu-система)
5. [Мозг (Brain)](#мозг-brain)
6. [Взаимодействие компонентов](#взаимодействие-компонентов)
7. [Потоки данных](#потоки-данных)
8. [Статистика и мониторинг](#статистика-и-мониторинг)

---

## 🎯 Обзор системы

**ЭкоНет** - это автономная система роя роботов для сбора окурков, построенная на архитектуре искусственного интеллекта, имитирующей нейронную сеть живого организма.

### Ключевые концепции:

- **Нейроны** - специализированные компоненты, обрабатывающие информацию (восприятие, координация, память, обучение)
- **Вены** - GPU система кровообращения, распределяющая вычислительные ресурсы (поддержка NVIDIA RTX)
- **Мозг** - высший уровень управления (коллективный разум, сознание)
- **Нейронная сеть** - система связей между компонентами для синхронизации
- **Система самоидентификации** - ЭкоНет осознает себя и может самосовершенствоваться

### Текущее состояние системы:

- ✅ **4 базовых нейрона** активно работают (yolo, deepseek, coordinator, information_hub)
- ✅ **GPU венозная система** полностью функциональна (GPUCirculatorySystem, GPUDistributor, GPUMonitor, GPUScheduler)
- ✅ **Система самоидентификации** активирована (SelfIdentityService, SelfModificationService, SelfLearningService)
- ✅ **Активное обучение** включено и работает автоматически
- ✅ **ModelEngine** использует FP32 модель (FP16 отключен для стабильности)
- ✅ **API сервер** доступен на http://localhost:8000
- ✅ **GUI интерфейс** полностью функционален (Material Design)

---

## 🏗️ Архитектура системы

```
┌─────────────────────────────────────────────────────────────┐
│                      МОЗГ (Brain)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Collective   │  │ Consciousness │  │ Decision     │      │
│  │ Mind         │  │              │  │ Maker        │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   НЕЙРОННАЯ СЕТЬ                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            Information Hub (HubNeuron)              │    │
│  │        Центральный узел синхронизации               │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ ВОСПРИЯТИЕ   │   │ КООРДИНАЦИЯ  │   │   ПАМЯТЬ     │
│ (Perception) │   │(Coordination)│   │  (Memory)    │
│              │   │              │   │              │
│ • Vision     │   │ • Task       │   │ • Short Term │
│ • Detection  │   │ • Swarm      │   │ • Experience │
│ • Tracking   │   │              │   │              │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            ВЕНЫ (Veins) - GPU Кровообращение                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Circulatory  │  │ Distributor  │  │   Monitor    │      │
│  │ System       │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐                                          │
│  │   Scheduler  │                                          │
│  └──────────────┘                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧬 Нейроны (Neurons)

Все компоненты системы представлены как нейроны - специализированные узлы, обрабатывающие информацию и взаимодействующие через нейронную сеть.

### Базовый класс: NeuralNode

Все нейроны наследуются от базового класса `NeuralNode`:

```python
class NeuralNode:
    - name: str                    # Имя нейрона
    - category: str                # Категория (perception, coordination, etc.)
    - state: ComponentState        # Состояние (READY, PROCESSING, ERROR)
    - incoming_connections: Dict   # Входящие связи
    - outgoing_connections: Dict   # Исходящие связи
    - messages_received: int       # Получено сообщений
    - messages_sent: int           # Отправлено сообщений
    
    async def think(context)       # Процесс мышления
    def receive(data, source)      # Прием данных
    def send(data, target)         # Отправка данных
    def broadcast(data)            # Широковещательная отправка
    def get_statistics()           # Статистика работы
```

---

### 📡 Восприятие (Perception)

#### 1. VisionNeuron (`obelisk/neurons/perception/vision_neuron.py`)

**Назначение:** Обработка визуальной информации

**Функции:**
- Обработка кадров через VisionContext
- Анализ визуального контекста
- Извлечение информации из изображений

**Параметры:**
- `vision_context`: VisionContext сервис для обработки

**Выходные данные:**
```python
{
    "action": "process",
    "result": {...},              # Результат анализа
    "confidence": 0.8,
    "frames_processed": int
}
```

**Статистика:**
- `processed_frames`: Количество обработанных кадров

**Связи:**
- Входы: Кадры видео
- Выходы: → HubNeuron, → DetectionNeuron

---

#### 2. DetectionNeuron (`obelisk/neurons/perception/detection_neuron.py`)

**Назначение:** Обнаружение объектов на кадрах

**Функции:**
- Детекция объектов через ModelEngine (YOLO)
- Использование GPU для ускорения
- Мониторинг использования GPU

**Параметры:**
- `model_engine`: ModelEngine для детекции (использует GPU)
- `gpu_monitor`: GPUMonitor для отслеживания использования

**Выходные данные:**
```python
{
    "action": "detect",
    "detections": [...],           # Список детекций
    "detections_count": int,
    "confidence": 0.9,
    "total_detections": int,
    "gpu_available": bool,
    "gpu_stats": {...}             # Статистика GPU (если доступно)
}
```

**Статистика:**
- `detections_count`: Общее количество детекций
- `gpu_available`: Доступность GPU
- `gpu_usage_count`: Количество использований GPU

**Связи:**
- Входы: Кадры от VisionNeuron
- Выходы: → HubNeuron, → TrackingNeuron, → TaskCoordinatorNeuron

**GPU интеграция:**
- Использует GPU через ModelEngine
- Мониторит использование через GPUMonitor
- Отслеживает статистику GPU

---

#### 3. TrackingNeuron (`obelisk/neurons/perception/tracking_neuron.py`)

**Назначение:** Отслеживание объектов между кадрами

**Функции:**
- Отслеживание объектов через ByteTracker
- Поддержка GPU ускорения
- История треков

**Параметры:**
- `tracker_config`: Конфигурация трекера
  - `frame_rate`: Частота кадров (по умолчанию 30)
  - `track_thresh`: Порог трекинга (0.5)
  - `high_thresh`: Высокий порог (0.6)
  - `match_thresh`: Порог совпадения (0.8)
  - `track_buffer`: Буфер треков (30)
  - `min_box_area`: Минимальная площадь бокса (10)
  - `mot_thresh`: Порог MOT (0.8)
- `gpu_circulatory`: GPUCirculatorySystem для запроса GPU
- `gpu_distributor`: GPUDistributor для распределения
- `gpu_monitor`: GPUMonitor для мониторинга

**Выходные данные:**
```python
{
    "action": "track",
    "detections": [...],           # Отслеженные детекции
    "track_count": int,
    "confidence": 0.9,
    "statistics": {...},           # Статистика трекинга
    "gpu_used": bool
}
```

**Статистика:**
- `frame_number`: Номер текущего кадра
- `track_statistics`: Статистика ByteTracker
- `history_size`: Размер истории треков
- `active_tracks`: Количество активных треков
- `gpu_enabled`: Включена ли поддержка GPU

**Методы:**
- `get_tracked_object(track_id)`: Получить информацию о треке
- `get_all_tracked_objects()`: Получить все активные треки
- `get_track_history(track_id, limit)`: История конкретного трека
- `reset()`: Сброс трекера

**Связи:**
- Входы: Детекции от DetectionNeuron
- Выходы: → HubNeuron, → TaskCoordinatorNeuron

**GPU интеграция:**
- Запрашивает GPU через GPUCirculatorySystem
- Приоритет трекинга: 7 (высокий)
- Требуемая память: 0.05 (низкая)
- Автоматически освобождает GPU после обработки

---

### 🎯 Координация (Coordination)

#### 4. TaskCoordinatorNeuron (`obelisk/neurons/coordination/task_coordinator_neuron.py`)

**Назначение:** Координация задач на основе детекций

**Функции:**
- Создание задач из детекций
- Управление задачами через TaskManager
- Координация между компонентами

**Параметры:**
- `task_manager`: TaskManager сервис

**Выходные данные:**
```python
{
    "action": "coordinate",
    "tasks": [...],                # Созданные задачи
    "tasks_count": int,
    "confidence": 0.8,
    "total_tasks_created": int
}
```

**Статистика:**
- `tasks_created`: Количество созданных задач
- `tasks_completed`: Количество завершенных задач

**Связи:**
- Входы: Детекции от HubNeuron
- Выходы: → HubNeuron, → SwarmCoordinatorNeuron

---

#### 5. SwarmCoordinatorNeuron (`obelisk/neurons/coordination/swarm_coordinator_neuron.py`)

**Назначение:** Координация роя роботов

**Функции:**
- Распределение задач между роботами
- Отправка задач через MQTT
- Мониторинг выполнения задач

**Параметры:**
- `task_manager`: TaskManager сервис
- `mqtt_client`: MQTT клиент для связи с роботами

**Выходные данные:**
```python
{
    "action": "coordinate_swarm",
    "distributed_tasks": [...],    # Распределенные задачи
    "tasks_count": int,
    "confidence": 0.8,
    "total_distributed": int
}
```

**Статистика:**
- `robots_connected`: Количество подключенных роботов
- `tasks_distributed`: Количество распределенных задач

**Связи:**
- Входы: Задачи от HubNeuron
- Выходы: → MQTT (роботам), → HubNeuron

**MQTT интеграция:**
- Публикует задачи в топик `obelisk/tasks`
- Отправляет задачи конкретным роботам в `robots/{robot_id}/tasks`

---

### 💾 Память (Memory)

#### 6. ShortTermMemoryNeuron (`obelisk/neurons/memory/short_term_memory_neuron.py`)

**Назначение:** Краткосрочное хранение информации

**Функции:**
- Хранение информации на короткое время (по умолчанию 5 минут)
- Быстрый доступ к недавним данным
- Автоматическая очистка устаревших записей

**Параметры:**
- `max_size`: Максимальный размер памяти (по умолчанию 1000)
- `retention_time`: Время хранения в секундах (по умолчанию 300)

**Методы:**
- `store(key, value)`: Сохранение данных
- `retrieve(key)`: Получение данных
- `cleanup_old()`: Очистка устаревших записей

**Выходные данные:**
```python
{
    "action": "stored" | "retrieved" | "cleaned",
    "key": str,
    "value": Any,                  # Для retrieve
    "found": bool,                 # Для retrieve
    "confidence": 1.0
}
```

**Статистика:**
- `size`: Текущий размер памяти
- `max_size`: Максимальный размер
- `retention_time`: Время хранения

**Связи:**
- Входы: Данные от любых нейронов
- Выходы: → HubNeuron (для синхронизации)

---

#### 7. ExperienceNeuron (`obelisk/neurons/memory/experience_neuron.py`)

**Назначение:** Накопление и использование опыта

**Функции:**
- Хранение опыта в краткосрочной памяти (10,000 записей)
- Сохранение опыта в базу данных
- Поиск похожего опыта для принятия решений

**Параметры:**
- `database`: Database сервис для долгосрочного хранения

**Методы:**
- `store_experience(experience)`: Сохранение опыта
- `_find_similar_experiences(context)`: Поиск похожего опыта

**Выходные данные:**
```python
{
    "action": "use_experience" | "learn_new",
    "experience": {...},           # Найденный опыт (если есть)
    "similar_count": int,
    "confidence": 0.7 | 0.3
}
```

**Статистика:**
- `total_experiences`: Общее количество опыта
- `stored_experiences`: Количество в памяти
- `database_available`: Доступность базы данных

**Связи:**
- Входы: Опыт от любых нейронов
- Выходы: → HubNeuron, → ActiveLearningNeuron

---

### 📚 Обучение (Learning)

#### 8. ActiveLearningNeuron (`obelisk/neurons/learning/active_learning_neuron.py`)

**Назначение:** Выбор данных для активного обучения

**Функции:**
- Определение необходимости обучения на основе детекций
- Выбор образцов с низкой уверенностью
- Интеграция с ActiveLearner сервисом

**Параметры:**
- `active_learner`: ActiveLearner сервис

**Выходные данные:**
```python
{
    "action": "learn" | "skip_learning",
    "should_learn": bool,
    "confidence": 0.8 | 0.3,
    "samples_selected": int
}
```

**Статистика:**
- `samples_selected`: Количество выбранных образцов

**Связи:**
- Входы: Детекции от DetectionNeuron
- Выходы: → HubNeuron, → TrainerService

---

### 🔍 Анализ (Analysis)

#### 9. AnalyzerNeuron (`obelisk/neurons/analysis/analyzer_neuron.py`)

**Назначение:** Анализ данных и результатов

**Функции:**
- Анализ различных типов данных
- Извлечение метаинформации
- История анализов

**Выходные данные:**
```python
{
    "action": "analyze",
    "analysis": {
        "type": str,               # Тип данных
        "timestamp": str,
        "keys": [...],             # Ключи (для dict)
        "size": int,               # Размер
        "length": int              # Длина (для list)
    },
    "confidence": 0.7,
    "total_analyses": int
}
```

**Статистика:**
- `analysis_count`: Количество анализов
- `analysis_history`: История (последние 1000)

**Связи:**
- Входы: Данные от любых нейронов
- Выходы: → HubNeuron

---

### 📡 Коммуникация (Communication)

#### 10. HubNeuron (`obelisk/neurons/communication/hub_neuron.py`)

**Назначение:** Центральный узел коммуникации и синхронизации

**Функции:**
- Маршрутизация сообщений между нейронами
- Синхронизация данных
- История всех сообщений

**Методы:**
- `connect_neuron(neuron_name)`: Подключение нейрона
- `receive(data, source)`: Прием данных
- `_route_message(data, source)`: Маршрутизация сообщений
- `_determine_targets(data, source)`: Определение целевых нейронов

**Статистика:**
- `connected_neurons`: Количество подключенных нейронов
- `messages_received`: Получено сообщений
- `messages_routed`: Отправлено сообщений
- `message_history_size`: Размер истории (10,000 записей)

**Маршрутизация:**
- Детекции → TaskCoordinatorNeuron
- Задачи → SwarmCoordinatorNeuron

**Связи:**
- Центральный узел: все нейроны подключены к HubNeuron

---

## 🩸 Вены (Veins) - GPU система

GPU система работает как кровеносная система организма, распределяя вычислительные ресурсы между всеми компонентами.

---

### 1. GPUCirculatorySystem (`obelisk/veins/gpu_circulatory.py`)

**Назначение:** Распределение GPU ресурсов как венозная система

**Функции:**
- Управление очередью запросов на GPU
- Выделение и освобождение GPU ресурсов
- Отслеживание активных задач

**Методы:**
- `request_gpu(task_id, priority, memory_required)`: Запрос GPU ресурсов
  - `task_id`: ID задачи
  - `priority`: Приоритет (1-10, 10 - высший)
  - `memory_required`: Требуемая память (0-1, доля от доступной)
  - Возвращает: Информацию о GPU или None
  
- `release_gpu(task_id)`: Освобождение GPU ресурсов
  - Автоматически очищает память GPU
  - Синхронизирует устройство

- `_allocate_gpu(task_id, memory_required)`: Внутреннее выделение GPU
  - Поиск свободного GPU с достаточной памятью
  - Проверка доступной памяти

**Статистика:**
- `total_requests`: Общее количество запросов
- `successful_allocations`: Успешные выделения
- `failed_allocations`: Неудачные выделения
- `active_tasks`: Количество активных задач
- `success_rate`: Процент успеха
- `pending_requests`: Запросы в ожидании

**Хранение:**
- `gpu_requests`: Очередь запросов (последние 1000)
- `active_tasks`: Словарь активных задач
- `gpu_load_history`: История загрузки (последние 1000)

**Интеграция:**
- Использует PyTorch для управления GPU
- Поддерживает множественные GPU устройства
- Блокировки для thread-safe операций

---

### 2. GPUDistributor (`obelisk/veins/gpu_distributor.py`)

**Назначение:** Умное распределение GPU между задачами

**Функции:**
- Распределение GPU между несколькими задачами
- Приоритизация задач
- Стратегии распределения

**Параметры:**
- `circulatory_system`: GPUCirculatorySystem для запросов

**Стратегии распределения:**
- `fair`: Справедливое распределение
- `priority`: По приоритету задач
- `performance`: По производительности

**Методы:**
- `distribute_gpu(tasks)`: Распределение GPU между задачами
  - Принимает список задач
  - Сортирует по приоритету
  - Выделяет GPU для каждой задачи
  - Возвращает результат распределения

- `set_task_priority(task_id, priority)`: Установка приоритета задачи

- `set_distribution_strategy(strategy)`: Установка стратегии

**Возвращаемые данные:**
```python
{
    "allocated": [...],            # Успешно выделенные задачи
    "pending": [...],              # Задачи в ожидании
    "failed": [...]                # Неудачные задачи
}
```

---

### 3. GPUMonitor (`obelisk/veins/gpu_monitor.py`)

**Назначение:** Мониторинг состояния GPU

**Функции:**
- Отслеживание использования памяти GPU
- История статистики
- Мониторинг загрузки устройств

**Методы:**
- `start_monitoring()`: Запуск мониторинга
- `stop_monitoring()`: Остановка мониторинга
- `get_gpu_stats()`: Получение текущей статистики GPU
- `get_history(limit)`: Получение истории (последние N записей)

**Статистика GPU:**
```python
{
    "devices": [
        {
            "device_id": int,
            "device_name": str,
            "total_memory_gb": float,
            "allocated_memory_gb": float,
            "reserved_memory_gb": float,
            "free_memory_gb": float,
            "usage_percent": float
        }
    ],
    "timestamp": str
}
```

**Хранение:**
- `gpu_stats_history`: История статистики (последние 1000 записей)

**Интеграция:**
- Использует PyTorch для получения информации о GPU
- Поддерживает множественные GPU устройства
- Thread-safe операции

---

### 4. GPUScheduler (`obelisk/veins/gpu_scheduler.py`)

**Назначение:** Планирование использования GPU ресурсов

**Функции:**
- Планирование задач на GPU
- Отложенное выполнение
- Управление расписанием

**Параметры:**
- `circulatory_system`: GPUCirculatorySystem для запросов

**Методы:**
- `schedule_task(task_id, priority, memory_required, scheduled_time)`: Планирование задачи
  - `task_id`: ID задачи
  - `priority`: Приоритет (1-10)
  - `memory_required`: Требуемая память (0-1)
  - `scheduled_time`: Время выполнения (None = немедленно)
  - Возвращает: True если задача запланирована

- `process_schedule()`: Обработка расписания (выполнение готовых задач)

- `get_schedule()`: Получение расписания

- `cancel_task(task_id)`: Отмена запланированной задачи

**Статусы задач:**
- `scheduled`: Запланировано
- `executing`: Выполняется
- `waiting`: Ожидает GPU

**Хранение:**
- `schedule_queue`: Очередь расписания (последние 1000)
- `scheduled_tasks`: Словарь запланированных задач

---

## 🧠 Мозг (Brain)

Высший уровень управления системой.

---

### 1. CollectiveMind (`obelisk/brain/collective_mind.py`)

**Назначение:** Коллективный разум, объединяющий все нейроны

**Функции:**
- Регистрация всех нейронов
- Сбор мнений от всех нейронов
- Синтез коллективных решений
- Управление уровнем сознания

**Методы:**
- `register_neuron(name, neuron)`: Регистрация нейрона
- `think(context)`: Процесс коллективного мышления
  - Собирает мнения от всех нейронов
  - Анализирует мнения
  - Принимает коллективное решение
  - Сохраняет в коллективную память

- `_synthesize_decision(opinions, context)`: Синтез решения
  - Подсчет голосов за каждое действие
  - Выбор действия с максимальным количеством голосов
  - Учет уверенности каждого нейрона

- `_update_consciousness_level()`: Обновление уровня сознания
  - Зависит от успешности решений
  - Учитывает количество нейронов

**Уровень сознания:**
- Вычисляется на основе успешности решений и количества нейронов
- Диапазон: 0.0 - 1.0

**Хранение:**
- `collective_memory`: Коллективная память (последние 10,000 записей)
- `decisions_history`: История решений (последние 1,000)

**Статистика:**
- `consciousness_level`: Уровень сознания
- `total_neurons`: Количество нейронов
- `total_decisions`: Всего решений
- `successful_decisions`: Успешных решений
- `success_rate`: Процент успеха

---

### 2. Consciousness (`obelisk/brain/consciousness.py`)

**Назначение:** Управление состоянием сознания системы

**Функции:**
- Управление уровнем осознанности
- Управление самосознанием
- История состояний

**Состояния:**
- `dormant`: Спящее
- `awakening`: Пробуждающееся
- `active`: Активное
- `dreaming`: Мечтающее

**Методы:**
- `awaken()`: Пробуждение сознания
  - Устанавливает состояние `awakening`
  - Уровень осознанности: 0.1

- `activate()`: Активация сознания
  - Устанавливает состояние `active`
  - Уровень осознанности: 0.5
  - Включает самосознание

- `increase_awareness(amount)`: Увеличение уровня осознанности
  - Добавляет к текущему уровню
  - Максимум: 1.0

- `get_state()`: Получение текущего состояния

**Статистика:**
- `awareness_level`: Уровень осознанности (0-1)
- `self_awareness`: Включено ли самосознание
- `state`: Текущее состояние

---

## 🔄 Взаимодействие компонентов

### Связи между нейронами:

```
VisionNeuron → HubNeuron → TaskCoordinatorNeuron
                    ↓
DetectionNeuron → HubNeuron → TrackingNeuron
                    ↓
TrackingNeuron → HubNeuron → TaskCoordinatorNeuron
                    ↓
TaskCoordinatorNeuron → HubNeuron → SwarmCoordinatorNeuron
                    ↓
SwarmCoordinatorNeuron → MQTT → Роботы
```

### GPU интеграция:

```
DetectionNeuron → ModelEngine → GPU (через PyTorch)
TrackingNeuron → GPUCirculatorySystem → GPU
                              ↓
                    GPUMonitor → Статистика
                              ↓
                    GPUScheduler → Планирование
```

### Поток данных детекции:

```
1. VisionNeuron обрабатывает кадр
   ↓
2. DetectionNeuron детектирует объекты (GPU)
   ↓
3. TrackingNeuron отслеживает объекты (опционально GPU)
   ↓
4. HubNeuron синхронизирует данные
   ↓
5. TaskCoordinatorNeuron создает задачи
   ↓
6. SwarmCoordinatorNeuron распределяет задачи роботам
```

### Поток данных обучения:

```
1. DetectionNeuron получает детекции с низкой уверенностью
   ↓
2. ActiveLearningNeuron выбирает образцы для обучения
   ↓
3. ExperienceNeuron сохраняет опыт
   ↓
4. TrainerService дообучает модель (GPU)
   ↓
5. ExperienceNeuron обновляет опыт на основе результатов
```

---

## 📊 Потоки данных

### 1. Поток детекции и координации

```
[Видео источник]
    ↓
[VisionNeuron] - Обработка кадра
    ↓
[DetectionNeuron] - Детекция объектов (GPU)
    ↓
[TrackingNeuron] - Отслеживание (опционально GPU)
    ↓
[HubNeuron] - Синхронизация
    ├→ [ShortTermMemoryNeuron] - Сохранение в краткосрочную память
    └→ [TaskCoordinatorNeuron] - Создание задач
        ↓
    [SwarmCoordinatorNeuron] - Распределение задач
        ↓
    [MQTT] - Отправка роботам
```

### 2. Поток обучения

```
[DetectionNeuron] - Детекции с низкой уверенностью
    ↓
[ActiveLearningNeuron] - Выбор образцов
    ↓
[ExperienceNeuron] - Сохранение опыта
    ↓
[TrainerService] - Дообучение модели (GPU)
    ↓
[ExperienceNeuron] - Обновление опыта
    ↓
[CollectiveMind] - Коллективное решение о деплое
```

### 3. Поток GPU управления

```
[Запрос на GPU]
    ↓
[GPUScheduler] - Планирование (если запланировано)
    ↓
[GPUCirculatorySystem] - Выделение GPU
    ↓
[GPUMonitor] - Мониторинг использования
    ↓
[GPU устройство] - Выполнение задачи
    ↓
[GPUCirculatorySystem] - Освобождение GPU
    ↓
[GPUMonitor] - Обновление статистики
```

---

## 📈 Статистика и мониторинг

### Статистика нейронов

Каждый нейрон предоставляет метод `get_statistics()`:

```python
{
    "category": str,               # Категория нейрона
    "state": str,                  # Состояние
    "messages_received": int,      # Получено сообщений
    "messages_sent": int,          # Отправлено сообщений
    # ... специфичные для нейрона метрики
}
```

### Статистика GPU системы

```python
{
    "circulatory": {
        "total_requests": int,
        "successful_allocations": int,
        "failed_allocations": int,
        "active_tasks": int,
        "success_rate": float
    },
    "monitor": {
        "devices": [...],          # Статистика каждого GPU
        "history_size": int
    },
    "scheduler": {
        "scheduled_tasks": int,
        "queue_size": int
    }
}
```

### Статистика коллективного разума

```python
{
    "consciousness_level": float,  # Уровень сознания (0-1)
    "total_neurons": int,
    "total_decisions": int,
    "successful_decisions": int,
    "success_rate": float,
    "memory_size": int,
    "decisions_history_size": int
}
```

---

## 🔧 Конфигурация

### Пример конфигурации нейронов:

```yaml
neurons:
  perception:
    vision:
      enabled: true
    detection:
      enabled: true
      gpu_enabled: true
    tracking:
      enabled: true
      gpu_enabled: true
      config:
        frame_rate: 30
        track_thresh: 0.5
  
  coordination:
    task_coordinator:
      enabled: true
    swarm_coordinator:
      enabled: true
  
  memory:
    short_term:
      max_size: 1000
      retention_time: 300
    experience:
      enabled: true

veins:
  gpu:
    circulatory:
      enabled: true
    monitor:
      enabled: true
      history_size: 1000
    scheduler:
      enabled: true
    distributor:
      strategy: "fair"
```

---

## 📝 Примечания

### Производительность:

- **DetectionNeuron** использует GPU через ModelEngine для ускорения детекции
- **TrackingNeuron** опционально использует GPU для оптимизации трекинга
- **GPUCirculatorySystem** управляет выделением GPU для предотвращения конфликтов
- **GPUScheduler** позволяет планировать GPU задачи для оптимального использования

### Масштабируемость:

- Все нейроны работают асинхронно
- GPU система поддерживает множественные GPU устройства
- Нейронная сеть легко расширяется новыми нейронами
- HubNeuron обеспечивает централизованную синхронизацию

### Надежность:

- Каждый нейрон обрабатывает ошибки независимо
- GPU система автоматически освобождает ресурсы при ошибках
- Состояния компонентов отслеживаются через NeuralNetwork
- История операций сохраняется для диагностики

---

## 🚀 Будущие улучшения

- [ ] Веса связей между нейронами для приоритизации
- [ ] Механизм обучения нейронов на основе успешности
- [ ] Динамическое создание временных связей для сложных задач
- [ ] Кэширование часто используемых данных
- [ ] Сжатие данных для оптимизации передачи
- [ ] Распределенная GPU система для кластеров
- [ ] Адаптивное управление приоритетами GPU задач
- [ ] Предиктивное планирование GPU нагрузки

---

**Конец документа**

