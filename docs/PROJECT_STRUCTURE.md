# Структура проекта ЭКОНЕТ

**Обновлено:** 2025-11-21

## 📐 Иерархическая структура

```
Project_econet/
├── obelisk/                    # ⭐ Центральный мозг системы
│   ├── brain/                  # 🧠 Мозг - Высший уровень
│   │   ├── collective_mind.py  # Коллективный разум
│   │   ├── consciousness.py    # Сознание системы
│   │   ├── decision_maker.py   # Принятие решений
│   │   └── neural_network_builder.py  # Строитель сети
│   │
│   ├── neurons/                # 🧬 Нейроны - Все узлы
│   │   ├── perception/         # Восприятие
│   │   │   ├── vision_neuron.py
│   │   │   └── detection_neuron.py
│   │   ├── coordination/       # Координация
│   │   │   ├── task_coordinator_neuron.py
│   │   │   └── swarm_coordinator_neuron.py
│   │   ├── memory/             # Память
│   │   │   ├── experience_neuron.py
│   │   │   └── short_term_memory_neuron.py
│   │   ├── learning/            # Обучение
│   │   │   └── active_learning_neuron.py
│   │   ├── analysis/           # Анализ
│   │   │   └── analyzer_neuron.py
│   │   └── communication/      # Коммуникация
│   │       └── hub_neuron.py
│   │
│   ├── veins/                  # 🩸 Вены - GPU система
│   │   ├── gpu_circulatory.py  # GPU кровообращение
│   │   ├── gpu_distributor.py  # Распределитель GPU
│   │   ├── gpu_monitor.py      # Мониторинг GPU
│   │   └── gpu_scheduler.py    # Планировщик GPU
│   │
│   ├── core/                   # 💪 Ядро системы
│   │   ├── engines/            # Движки
│   │   │   ├── unified_engine.py
│   │   │   ├── model_engine.py
│   │   │   └── test_engine.py
│   │   ├── processors/         # Процессоры
│   │   │   └── object_tracker.py
│   │   ├── managers/          # Менеджеры
│   │   │   ├── gpu_manager.py
│   │   │   └── gpu_test_manager.py
│   │   ├── neural_sync.py     # Нейронная синхронизация
│   │   └── neural_nodes.py     # Нейронные узлы
│   │
│   ├── services/               # 🔧 Сервисы
│   │   ├── data/              # Данные
│   │   ├── learning/          # Обучение
│   │   ├── communication/     # Коммуникация
│   │   └── tools/             # Инструменты
│   │
│   ├── api/                    # 🌐 API
│   │   ├── rest/              # REST API
│   │   └── neural/            # Нейронный API
│   │
│   └── ui/                     # 🎨 UI
│       ├── gui/               # GUI
│       └── neural_ui/         # Нейронный UI
│
├── config/                     # Конфигурация
├── scripts/                    # Скрипты
├── tests/                      # Тесты
├── data/                       # Data Lake
├── models/                     # Модели
└── docs/                       # Документация
```

## 🧠 Мозг системы (Brain)

Высший уровень координации и принятия решений:

- **CollectiveMind** - объединяет все нейроны в единое сознание
- **Consciousness** - управление состоянием сознания
- **DecisionMaker** - принятие решений на основе коллективного разума
- **NeuralNetworkBuilder** - автоматическое построение нейронной сети

## 🧬 Нейроны (Neurons)

Все компоненты системы представлены как нейроны:

### Восприятие (Perception)
- VisionNeuron - обработка визуальной информации
- DetectionNeuron - детекция объектов

### Координация (Coordination)
- TaskCoordinatorNeuron - координация задач
- SwarmCoordinatorNeuron - координация роя роботов

### Память (Memory)
- ExperienceNeuron - накопление опыта
- ShortTermMemoryNeuron - краткосрочная память

### Обучение (Learning)
- ActiveLearningNeuron - активное обучение

### Анализ (Analysis)
- AnalyzerNeuron - анализ данных

### Коммуникация (Communication)
- HubNeuron - центральный хаб коммуникации

## 🩸 GPU Венозная система (Veins)

GPU как кровеносная система проекта:

- **GPUCirculatorySystem** - распределение GPU ресурсов
- **GPUDistributor** - умное распределение между задачами
- **GPUMonitor** - мониторинг состояния GPU
- **GPUScheduler** - планирование использования GPU

## 💪 Ядро (Core)

Базовые движки и процессоры:

### Движки (Engines)
- UnifiedEngine - универсальный движок координации
- ModelEngine - управление YOLO моделями
- TestEngine - тестовый движок

### Процессоры (Processors)
- ObjectTracker - отслеживание объектов

### Менеджеры (Managers)
- GPUMemoryManager - управление GPU памятью
- GPUTestManager - GPU для тестов

## 🔧 Сервисы (Services)

Специализированные сервисы:
- Database - база данных
- CacheManager - управление кэшем
- MediaManager - управление медиа
- ActiveLearner - активное обучение
- Trainer - обучение моделей
- TaskManager - управление задачами
- MQTTClient - MQTT коммуникация
- VisionContext - визуальный контекст

## 🌐 API

- REST API - FastAPI для управления системой
- Neural API - нейронный интерфейс

## 🎨 UI

- Material Design GUI - современный интерфейс
- Cyberpunk GUI - киберпанк тема
- Modern GUI - современная тема
- Neural UI - нейронный интерфейс

## 📊 Статистика структуры

- **Нейронов**: 9
- **GPU компонентов**: 4
- **Мозговых компонентов**: 4
- **Движков**: 3
- **Процессоров**: 1
- **Менеджеров**: 2

## 🎯 Принципы организации

1. **Разделение обязанностей** - каждый модуль в своей категории
2. **Нейронная архитектура** - все компоненты пронизаны нейронами
3. **GPU как вены** - централизованное управление GPU
4. **Коллективный разум** - единое сознание из множества нейронов
5. **Четкая иерархия** - brain → neurons → core → services

