# EcoNet — Главная документация

**Версия:** 1.3 (Circular Economy + Full Recycling Cycle)  
**Обновлено:** 2026-03-17  
**Статус:** ✅ Полностью функциональна — 10/10 компонентов

---

## Оглавление

1. [Миссия проекта](#миссия-проекта)
2. [Полный цикл переработки](#полный-цикл-переработки)
3. [Быстрый старт](#быстрый-старт)
4. [Архитектура системы](#архитектура-системы)
5. [GPU-оптимизации (v1.2)](#gpu-оптимизации-v12)
6. [Нейронная архитектура](#нейронная-архитектура)
7. [SwarmOS — полевая архитектура роя](#swarmos--полевая-архитектура-роя)
8. [GPU Veins — кровообращение](#gpu-veins--кровообращение)
9. [DeepSeek LLM](#deepseek-llm)
10. [Документация по модулям](#документация-по-модулям)
11. [API](#api)
12. [Конфигурация](#конфигурация)
13. [Тестирование](#тестирование)
14. [Текущий статус](#текущий-статус)
15. [Потенциал платформы](#потенциал-платформы)
16. [История версий](#история-версий)

---

## Миссия проекта

EcoNet — это не программа-детектор и не робот-пылесос. Это **автономная экосистема замкнутого цикла**, которая:

1. **Находит** мусор (окурки) с помощью компьютерного зрения (YOLOv8, 97 FPS)
2. **Собирает** роем автономных роботов, координируемых через SwarmOS
3. **Перерабатывает** — очистка, разделение компонентов, дробление
4. **Производит** — теплоизоляционные плиты и другие строительные материалы
5. **Питает себя** — биогаз из табака + солнечные панели = энергетическая автономность

**Аналогов нет.** Существующие проекты останавливаются на этапе "обнаружил" или "собрал". EcoNet идёт до конечного продукта с рыночной стоимостью.

---

## Полный цикл переработки

### Circular Economy — замкнутая экономика

```
    ┌─────────────────────────────────────────────────────────────┐
    │                    OBELISK (мобильная база)                  │
    │                                                              │
    │  ☀️ Солнечные панели ──────────────────────────►  ⚡ Энергия │
    │                                                      │      │
    │  ┌──────────┐   ┌──────────┐   ┌──────────┐        │      │
    │  │  Приём   │──►│  Очистка │──►│Разделение│        │      │
    │  │  сырья   │   │  от смол │   │компонент.│        │      │
    │  └──────────┘   └──────────┘   └────┬─────┘        │      │
    │                                      │              │      │
    │                        ┌─────────────┼──────────┐   │      │
    │                        ▼             ▼          │   │      │
    │                   ┌─────────┐  ┌──────────┐     │   │      │
    │                   │  Табак  │  │ Ацетат-  │     │   │      │
    │                   │+ смолы  │  │целлюлоза │     │   │      │
    │                   └────┬────┘  └────┬─────┘     │   │      │
    │                        │            │           │   │      │
    │                        ▼            ▼           │   │      │
    │                   ┌─────────┐  ┌──────────┐     │   │      │
    │                   │ Биогаз  │  │Дробление │     │   │      │
    │                   │(пиролиз)│  │Прессовка │     │   │      │
    │                   └────┬────┘  └────┬─────┘     │   │      │
    │                        │            │           │   │      │
    │                        ▼            ▼           │   │      │
    │                   ⚡ Энергия   🧱 ПРОДУКЦИЯ:    │   │      │
    │                   для роя     • Теплоизол.     │   │      │
    │                        │        плиты          │   │      │
    │                        │      • Плитка         │   │      │
    │                        │      • Лавки          │   │      │
    │                        │      • Подставки      │   │      │
    │                        ▼                        │   │      │
    │               ┌──────────────┐                  │   │      │
    │               │  Зарядка     │◄─────────────────┘   │      │
    │               │  роботов     │◄─────────────────────┘      │
    │               └──────────────┘                              │
    └─────────────────────────────────────────────────────────────┘
                              ▲
                              │ возврат с добычей
                    ┌─────────┴─────────┐
                    │   Рой роботов     │
                    │   (SwarmOS)       │
                    │   + дрон-разведчик│
                    └───────────────────┘
```

### Этапы переработки

| Этап | Процесс | Результат |
|---|---|---|
| **1. Сбор** | Роботы подбирают окурки манипулятором | Сырьё в контейнере робота |
| **2. Приём** | Робот возвращается в Obelisk, сдаёт сырьё | Сырьё в бункере базы |
| **3. Очистка** | Удаление никотина, смол, загрязнений | Чистая ацетатцеллюлоза + табачная масса |
| **4. Разделение** | Ацетатцеллюлоза (фильтр) отделяется от табака и бумаги | Два потока сырья |
| **5a. Дробление** | Ацетатцеллюлоза измельчается | Гранулы / волокно |
| **5b. Пиролиз** | Табак + бумага → термическое разложение | Биогаз (метан, CO, H₂) |
| **6a. Прессование** | Гранулы + связующее → пресс | Теплоизоляционные плиты |
| **6b. Генерация** | Биогаз → генератор | Электроэнергия для роя |
| **7. Подзарядка** | Солнечные панели + биогаз → аккумуляторы | Полная автономность |

### Конечные продукты

| Продукт | Применение | Основа |
|---|---|---|
| **Теплоизоляционные плиты** | Строительство, утепление | Ацетатцеллюлоза |
| **Тротуарная плитка** | Благоустройство | Ацетатцеллюлоза + полимер |
| **Садовые лавки** | Городская мебель | Ацетатцеллюлоза + композит |
| **Цветочные подставки** | Озеленение | Ацетатцеллюлоза |

### Энергетический баланс

| Источник энергии | Вклад | Назначение |
|---|---|---|
| **Биогаз (пиролиз табака)** | ~40-60% | Подзарядка роботов |
| **Солнечные панели (крыша Obelisk)** | ~30-40% | Базовое питание |
| **Сетевое подключение (опционально)** | ~10-20% | Резерв, ночная зарядка |

Цель: **≥80% энергетической автономности** при полной загрузке.

---

## Быстрый старт

### Требования

- Python 3.8+
- NVIDIA GPU с CUDA (RTX рекомендуется для FP16 Tensor Cores)
- 8+ GB RAM (16 GB рекомендуется)
- Ollama (опционально, для DeepSeek LLM чата)

### Установка и запуск

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск GUI
python scripts/run_gui.py

# Или полная система (API + GUI)
python scripts/start_econet_system.py

# Windows
ЗАПУСТИТЬ_ЭКОНЕТ.bat
```

**Подробнее:** [QUICKSTART.md](docs/QUICKSTART.md) | [SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

---

## Архитектура системы

EcoNet состоит из следующих подсистем:

### 1. UnifiedEngine — центральный движок

Координирует все компоненты системы. Инициализирует 10 подсистем:

| # | Компонент | Назначение |
|---|---|---|
| 1 | **ModelEngine** | YOLO inference (FP16, cuDNN, GPU warmup) |
| 2 | **VisionContext** | Анализ визуального контекста |
| 3 | **Self-Awareness** | Самоидентификация + самомодификация + самообучение |
| 4 | **ActiveLearner** | Автоматическое улучшение модели |
| 5 | **Database** | SQLite / PostgreSQL |
| 6 | **MQTT Client** | Коммуникация между устройствами |
| 7 | **TaskManager** | Распределение задач (классический + полевой) |
| 8 | **NeuralArchitecture** | 4 нейрона + 9 связей |
| 9 | **SwarmOS** | Полевая координация роя |
| 10 | **GPU Veins** | Мониторинг и распределение GPU |

### 2. ModelEngine — YOLO детекция

- Загрузка PT моделей на GPU с FP16
- GPU warmup при старте (устраняет холодный первый кадр)
- cuDNN benchmark для автоподбора алгоритмов конволюций
- TF32 для ускорения matmul на Ampere GPU
- Поддержка ансамбля моделей (weighted voting)
- Интеграция с GPU Manager для мониторинга VRAM

**Бенчмарк (RTX 3070 Laptop, 8 GB VRAM):**

| Параметр | Значение |
|---|---|
| Inference time | 10.3 ms/frame |
| FPS | 97 |
| VRAM usage | 0.04 GB (YOLOv8n) |
| Precision | FP16 (Tensor Cores) |

### 3. Obelisk — мобильная база

Мобильный командно-перерабатывающий центр:

- **Транспорт** — перевозка роя роботов к месту работы
- **Хранение** — док-станции для роботов, контейнеры для сырья
- **Переработка** — модули очистки, дробления, прессования
- **Энергия** — солнечные панели, генератор на биогазе, зарядные станции
- **Мозг** — GPU-сервер с UnifiedEngine, управление всей операцией

### 4. Material Design GUI

- Real-time видео с детекциями (камера / файл / IP-поток)
- Scrollable статус-панель: GPU, VRAM, FPS, нейроны, MQTT, Swarm, Veins
- DeepSeek чат в отдельном окне
- Frame-dropping для стабильного UI
- `ImageTk.PhotoImage` вместо CTkImage для минимального overhead
- IP-камера через Material Design диалог

### 5. Edge Inference

- Локальный YOLO inference для быстрого отклика
- Оптимизация для Raspberry Pi / Jetson Nano
- Публикация детекций в MQTT

### 6. Роботы

- **Collector** — робот-сборщик с вакуумом и манипулятором
- **MiP Bridge** — ретранслятор BLE → MQTT для MiP роботов
- Координация через MQTT + SwarmOS

### 7. Data Lake

- Хранение кадров для Active Learning
- Автоматическое управление датасетами
- Версионирование моделей

---

## GPU-оптимизации (v1.2)

### Что включено

| Оптимизация | Где | Эффект |
|---|---|---|
| **FP16** | `model_engine.py` | Tensor Cores, 2x меньше VRAM |
| **cuDNN benchmark** | `gpu_manager.py` | Auto-tuned conv алгоритмы (+10-30%) |
| **TF32** | `gpu_manager.py` | Ampere matmul acceleration |
| **GPU warmup** | `model_engine.py` | Прогрев при загрузке модели |
| **No GPU sync** | `model_engine.py` | `torch.cuda.synchronize()` убран из hot path |
| **Expandable segments** | `gpu_manager.py` | Меньше фрагментация CUDA memory |
| **Frame-dropping** | `gui_material.py` | Пропуск кадров при перегрузке GUI |
| **Inference guard** | `gui_material.py` | Один YOLO inference за раз |
| **Veins monitoring** | `unified_engine.py` | GPU stats в real-time |

### Файлы конфигурации

```yaml
# config/config.yaml
model_engine:
  device: cuda:0
  half_precision: true       # FP16 Tensor Cores
  cudnn_benchmark: true      # Auto-tuned convolutions
  tf32: true                 # Ampere matmul

performance:
  frame_skip: 0              # Обработка ВСЕХ кадров
  batch_processing: true
  max_cache_size: 200
  target_fps: 120
```

---

## Нейронная архитектура

4 базовых нейрона, связанных через Information Hub:

### Нейроны

| Нейрон | Тип | Назначение |
|---|---|---|
| `yolo_neuron` | Perception | Детекция объектов через ModelEngine |
| `deepseek_neuron` | Analysis | LLM анализ и принятие решений (Ollama) |
| `coordinator_neuron` | Coordination | Координация задач через TaskManager |
| `information_hub` | Memory | Центральная синхронизация данных |

### Связи (9 штук)

```
yolo_neuron ↔ information_hub
deepseek_neuron ↔ information_hub
coordinator_neuron ↔ information_hub
yolo_neuron → deepseek_neuron
deepseek_neuron → coordinator_neuron
coordinator_neuron → yolo_neuron
```

### Поток данных

1. **YOLO** детектирует объекты на кадре
2. Результаты отправляются в **Information Hub**
3. **DeepSeek** анализирует контекст (если подключён)
4. **Coordinator** распределяет задачи роботам
5. Все данные синхронизируются через Hub

**Подробнее:** [NEURAL_ARCHITECTURE_4_NODES.md](docs/NEURAL_ARCHITECTURE_4_NODES.md)

---

## SwarmOS — полевая архитектура роя

Децентрализованная координация, основанная на физической модели полей.

### Математическая модель

```
Эффективность:       E_i = αR_i + βC_i + γB_i          (α + β + γ = 1)
Диффузия:            E_i(t+1) = E_i(t) + D·Σ(E_j − E_i) + S_i − λ·E_i
Потенциал нагрузки:  Φ_i = T_i − R_i
Поток задач:         J_ij = −k·(Φ_j − Φ_i)
Энергия системы:     H = Σ(T_i − R_i)²                 (убывает → баланс)
```

### Модули (`obelisk/swarm/`)

| Модуль | Класс | Назначение |
|---|---|---|
| `field_node.py` | FieldNode | Узел с вектором состояния |
| `efficiency_field.py` | EfficiencyField | Диффузия поля, потоки, энергия |
| `swarm_kernel.py` | SwarmKernel | Ядро ОС роя (async цикл) |
| `field_scheduler.py` | FieldScheduler | Назначение задач по градиентам |
| `field_communication.py` | FieldCommunication | Мост MQTT ↔ поле |

### Свойства

- Нет единой точки отказа
- Автобалансировка нагрузки через `J_ij = −k·(Φ_j − Φ_i)`
- Масштабирование: O(N·k) на тик
- Фазовые переходы: `slow_exploration → self_organization → rapid_convergence`
- 4 начальных узла: `obelisk_core`, `yolo_detector`, `task_coordinator`, `information_hub`

### Конфигурация

```yaml
swarm_field:
  enabled: true
  alpha: 0.4          # Вес ресурсов
  beta: 0.4           # Вес вычислений
  gamma: 0.2          # Вес пропускной способности
  diffusion_coeff: 0.1
  decay_factor: 0.01
  mobility_coeff: 0.05
  tick_interval: 1.0
  topology: full_mesh
```

### MQTT-топики

| Топик | Описание |
|---|---|
| `swarm/field/{node_id}/state` | Периодическая публикация состояния узла |
| `swarm/field/{node_id}/flow` | Потоки задач между узлами |
| `swarm/field/announce` | Объявление о входе/выходе узлов |

**Теоретическая база:** `Полевая архитектура роя (Field-Based Architecture)/`

---

## GPU Veins — кровообращение

Система "кровообращения" GPU ресурсов (`obelisk/veins/`):

| Модуль | Назначение |
|---|---|
| `gpu_circulatory.py` | Запрос / выделение / освобождение GPU |
| `gpu_monitor.py` | Мониторинг VRAM, температуры, утилизации |
| `gpu_scheduler.py` | Планирование задач с приоритетами |
| `gpu_distributor.py` | Распределение между конкурирующими задачами |

Veins интегрированы в UnifiedEngine (v1.2):
- GPUCirculatorySystem запускается при инициализации
- GPUMonitor ведёт мониторинг в real-time
- Статистика отображается в GUI (панель "Veins")
- При тестировании модели ресурсы запрашиваются/освобождаются через Veins

---

## DeepSeek LLM

Интеграция с LLM для анализа и чата:

- **Провайдер по умолчанию:** Ollama (локальный)
- **Модель:** deepseek-r1:8b
- **Доступ из GUI:** кнопка "DeepSeek" → отдельное окно чата
- **Поддерживаемые провайдеры:** Ollama, Groq, Gemini, HuggingFace, TogetherAI

```yaml
chat:
  enabled: true
  llm_provider: ollama
  llm_model: deepseek-r1:8b
  ollama_base_url: http://localhost:11434
```

---

## Документация по модулям

### Основная

| Документ | Описание |
|---|---|
| [README.md](README.md) | Обзор проекта, метрики, быстрый старт |
| [QUICKSTART.md](docs/QUICKSTART.md) | Пошаговая установка за 5 минут |
| [SETUP_GUIDE.md](docs/SETUP_GUIDE.md) | Детальная настройка |
| [INSTALL_GUIDE.md](docs/INSTALL_GUIDE.md) | Решение проблем с зависимостями |

### Архитектура

| Документ | Описание |
|---|---|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Техническая архитектура |
| [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | Структура файлов |
| [SYSTEM_ARCHITECTURE_COMPLETE.md](docs/SYSTEM_ARCHITECTURE_COMPLETE.md) | Полная архитектура |
| [ECONET_HIERARCHY.md](docs/ECONET_HIERARCHY.md) | Иерархия компонентов |

### Нейроны и Swarm

| Документ | Описание |
|---|---|
| [NEURAL_ARCHITECTURE_4_NODES.md](docs/NEURAL_ARCHITECTURE_4_NODES.md) | 4 нейрона |
| [NEURON_HIERARCHY_COMPLETE.md](docs/NEURON_HIERARCHY_COMPLETE.md) | Полная иерархия нейронов |
| [ECONET_SWARM_SYSTEM.md](docs/ECONET_SWARM_SYSTEM.md) | Система роя |

### Модели и обучение

| Документ | Описание |
|---|---|
| [UNIFIED_ENGINE_GUIDE.md](docs/UNIFIED_ENGINE_GUIDE.md) | UnifiedEngine |
| [MODEL_ENGINE_GUIDE.md](docs/MODEL_ENGINE_GUIDE.md) | ModelEngine + ансамбль |
| [ACTIVE_LEARNING_GUIDE.md](docs/ACTIVE_LEARNING_GUIDE.md) | Active Learning |
| [TRAINING_GUIDE.md](docs/TRAINING_GUIDE.md) | Обучение YOLO моделей |

### GUI и инструменты

| Документ | Описание |
|---|---|
| [MATERIAL_DESIGN_INTERFACE.md](docs/MATERIAL_DESIGN_INTERFACE.md) | GUI |
| [ANNOTATION_TOOL_GUIDE.md](docs/ANNOTATION_TOOL_GUIDE.md) | Инструмент разметки |
| [CACHE_AND_MODEL_SELECTOR.md](docs/CACHE_AND_MODEL_SELECTOR.md) | Кэш и модели |
| [SELF_AWARENESS.md](docs/SELF_AWARENESS.md) | Самоосознание |

### Тестирование

| Документ | Описание |
|---|---|
| [tests/README.md](tests/README.md) | Документация по тестам |
| [tests/TESTING_MECHANICS.md](tests/TESTING_MECHANICS.md) | Механика тестирования |

---

## API

**URL:** `http://localhost:8000`  
**Swagger:** `http://localhost:8000/docs`

### Эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/system/status` | Статус всех сервисов |
| GET | `/system/swarm/field` | Статус SwarmOS |
| GET | `/system/swarm/nodes` | Состояние узлов поля |
| GET | `/system/swarm/nodes/{id}` | Конкретный узел |
| GET | `/system/deepseek/status` | Статус DeepSeek |
| POST | `/detection/frame` | Детекция на кадре |

---

## Конфигурация

Единый файл: `config/config.yaml`

### Ключевые секции

| Секция | Описание |
|---|---|
| `model_engine` | GPU device, FP16, cuDNN, batch size |
| `model` | YOLO параметры (threshold, input_size, max_detections) |
| `performance` | Frame skip, cache, target FPS |
| `swarm_field` | SwarmOS: D, λ, k, α, β, γ, topology |
| `chat` | LLM: provider, model, base_url |
| `active_learning` | Confidence bounds, retrain epochs |
| `obelisk` | API host/port, MQTT broker |

---

## Тестирование

```bash
# Unit тесты
pytest tests/unit/ -v

# Все тесты
pytest tests/ -v
```

15 тестов, 100% pass rate. Покрытие: UnifiedEngine, SwarmOS, нейронная архитектура, MQTT.

---

## Текущий статус

### Работающие компоненты (10/10)

| Компонент | Статус | Детали |
|---|---|---|
| ModelEngine | ✅ | FP16 на cuda:0, 97 FPS |
| VisionContext | ✅ | Анализ визуального контекста |
| Self-Awareness | ✅ | 141 файл, 30K+ строк |
| ActiveLearner | ✅ | Автоулучшение модели |
| Database | ✅ | SQLite (`data/obelisk.db`) |
| MQTT | ✅ | localhost:1883 |
| TaskManager | ✅ | Классический + полевой |
| NeuralArchitecture | ✅ | 4 нейрона, 9 связей |
| SwarmOS | ✅ | 4 узла, full_mesh, running |
| GPU Veins | ✅ | Мониторинг + распределение |

### GUI статус-панель

| Показатель | Пример значения |
|---|---|
| GPU | RTX 3070 [FP16 cuDNN] |
| GPU Память | 0.04 / 8.0 GB |
| FPS | 60 (ограничение камеры) |
| Время инф. | 10.3 ms |
| Нейроны | 4: YOLO, DeepSeek, Coord, Hub |
| Swarm | 4 узла |
| Veins | OK |

---

## Потенциал платформы

Архитектура EcoNet модульна и универсальна. Ядро (SwarmOS, GPU pipeline, нейроархитектура, Veins) не зависит от типа задачи:

| Применение | Модель | Роботы | Выход |
|---|---|---|---|
| **Уборка города** | YOLO (окурки) | Наземные коллекторы | Стройматериалы |
| **Разминирование** | YOLO (мины) + магнитометр | Дроны (коаксиальные) | Карта мин + маркировка |
| **Агротехника** | YOLO (вредители, болезни) | Наземные/воздушные | Карта обработки |
| **Инспекция** | YOLO (дефекты) | Дроны | Отчёт о состоянии |

Для адаптации достаточно:
1. Переобучить YOLO на новый датасет
2. Настроить `config.yaml` (классы, пороги)
3. Добавить специфичные нейроны (если нужны)

Ядро остаётся неизменным.

---

## История версий

### v1.3 (2026-03-17) — Circular Economy

- ✅ Документация полного цикла переработки
- ✅ Описание энергетического баланса (биогаз + солнечные панели)
- ✅ Перечень конечных продуктов (плиты, плитка, лавки)
- ✅ Концепт-арты в README (Obelisk, роботы, facility)
- ✅ Секция «Потенциал платформы» (разминирование, агро, инспекция)
- ✅ Обновлены README.md и MAIN_DOCUMENTATION.md

### v1.2 (2026-03-16) — GPU Full Power + Veins

- ✅ FP16 inference (Tensor Cores)
- ✅ cuDNN benchmark + TF32 (Ampere)
- ✅ GPU warmup при загрузке модели
- ✅ Убран `torch.cuda.synchronize()` из hot path
- ✅ GPU Veins интегрированы в UnifiedEngine
- ✅ Frame-dropping + inference guard в GUI
- ✅ `ImageTk.PhotoImage` вместо CTkImage
- ✅ YOLO на каждом кадре (`_detect_every_n = 1`)
- ✅ Фикс `total_mem` → `total_memory` в GUI
- ✅ DeepSeek чат в отдельном окне
- ✅ Scrollable статус-панель с GPU/Veins/Swarm метриками
- ✅ Material Design диалог для IP-камеры
- ✅ `parallel_vision` отключён (не блокирует YOLO)

### v1.1 (2026-03-15) — SwarmOS

- ✅ Полевая архитектура роя (5 модулей в `obelisk/swarm/`)
- ✅ Конфигурация `swarm_field` в `config/config.yaml`
- ✅ TaskManager: полевой планировщик
- ✅ API эндпоинты: `/system/swarm/field`, `/system/swarm/nodes`
- ✅ MQTT-топики: `swarm/field/+/state`, `swarm/field/announce`

### v1.0 (2025-11) — Начальный релиз

- ✅ YOLOv8 детекция (FP32)
- ✅ 4 базовых нейрона
- ✅ Material Design GUI
- ✅ GPU венозная система
- ✅ Active Learning
- ✅ Self-Awareness
- ✅ MQTT коммуникация

---

## Устранение неполадок

### Проблемы с GPU

```bash
# Проверка CUDA
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"

# Проверка cuDNN
python -c "import torch; print('cuDNN:', torch.backends.cudnn.version())"

# Проверка FP16
python -c "import torch; cap = torch.cuda.get_device_capability(0); print('FP16 Tensor Cores:', cap[0] >= 7)"
```

### Проблемы с камерой

- Убедитесь, что камера не занята другим приложением
- Для IP-камеры: используйте формат `http://IP:PORT/video`
- Windows: система пробует DSHOW → MSMF → ANY автоматически

### Логи

- Системные: `data/logs/system.log`
- Проверка зависимостей: `python scripts/check_dependencies.py`

---

**Автор:** Андреев Никита  
**Лицензия:** MIT
