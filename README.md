# 🐝 ЭКОНЕТ (EcoNet) - Автономная Система Роя для Очистки От Мусора

**Статус (2025-11-22):** ✅ Проект полностью функционален и готов к использованию
- ✅ Система успешно запускается и работает стабильно
- ✅ Все компоненты инициализируются корректно
- ✅ Создана четкая иерархическая структура
- ✅ Реализован коллективный разум с нейронной архитектурой
- ✅ Создана GPU венозная система (поддержка RTX GPU)
- ✅ 4 базовых нейрона в активной архитектуре (yolo, deepseek, coordinator, information_hub)
- ✅ Система самоидентификации активирована
- ✅ Все файлы мигрированы в новую структуру
- ✅ Документация актуализирована и очищена
- ✅ Система тестирования полностью переработана (15 тестов, 100% проходят)
- ✅ Убраны ограничения FPS для видео
- ✅ Material Design GUI полностью функционален
- ✅ Автоматический запуск через `scripts/start_econet_system.py`
- ✅ FP32 модель (FP16 отключен для стабильности)

## 🤖 ЭкоНет - Интеллектуальная Система Роя

**ЭкоНет** - это автономная интеллектуальная система роя роботов для очистки территорий от мусора. Система объединяет:
- **Коллективный разум** - искусственный интеллект из 4 базовых нейронов (расширяется до 10+)
- **YOLO** - детекция мусора (глаза системы, FP32 модель)
- **GPU венозная система** - централизованное управление GPU ресурсами (поддержка NVIDIA RTX)
- **Нейронная архитектура** - все компоненты пронизаны нейронами для синхронизации
- **Система самоидентификации** - ЭкоНет осознает себя и может самосовершенствоваться
- **Активное обучение** - автоматическое улучшение моделей на основе опыта
- **Рой роботов** - автономная координация множества роботов-сборщиков через MQTT
- **Material Design GUI** - современный интерфейс для управления
- **Инструменты разметки** - ручная и автоматическая разметка для обучения

Система может **видеть**, **учиться**, **осознавать себя** и **координировать рой роботов** для эффективной очистки!

**Быстрый старт:**
```powershell
# Через скрипт запуска (рекомендуется)
python scripts/start_econet_system.py

# Или через батник (Windows)
ЗАПУСТИТЬ_ЭКОНЕТ.bat

# Или только GUI
python -m obelisk.ui.gui_material
```

---

## Архитектура проекта

Полная архитектура самообучающейся ИИ-системы для уборки окурков сигарет.

### Структура проекта

```
Project_econet/
├── obelisk/              # ⭐ Центральный мозг системы
│   ├── brain/            # 🧠 Мозг - Коллективный разум
│   ├── neurons/          # 🧬 Нейроны - Все узлы системы
│   ├── veins/            # 🩸 Вены - GPU система
│   ├── core/             # 💪 Ядро - Движки, процессоры, менеджеры
│   │   ├── engines/      # Движки (UnifiedEngine, ModelEngine, TestEngine)
│   │   ├── processors/   # Процессоры (ObjectTracker)
│   │   └── managers/     # Менеджеры (GPU Manager)
│   ├── services/         # 🔧 Сервисы (Database, Cache, Trainer и др.)
│   ├── api/              # 🌐 API (REST, Neural)
│   └── ui/               # 🎨 UI (Material Design, Cyberpunk, Modern)
├── edge/                 # Edge inference устройства
│   ├── inference_service/# Сервис локального инференса
│   └── nav_node/         # Навигационный модуль
├── robots/               # Роботы и контроллеры
│   ├── collector/        # Робот-сборщик
│   └── mip_bridge/       # Мост для MiP роботов
├── models/               # YOLO модели и конфигурация
│   └── cigarette_detector/
├── data/                 # Data Lake
│   ├── raw/              # Сырые кадры
│   ├── labeled/          # Размеченные данные
│   ├── models/           # Обученные веса моделей
│   └── logs/             # Логи системы
├── datasets/             # Датасеты
│   └── cigarette_butt/   # Датасет окурков
├── config/               # Конфигурационные файлы
├── scripts/              # Вспомогательные скрипты
└── docs/                 # Документация

```

## Компоненты системы

### 1. Обелиск (Obelisk) - Центральный мозг
- **API**: FastAPI REST API для управления системой
- **UnifiedEngine**: Универсальный движок координации
- **ModelEngine**: Управление YOLO моделями с ансамблем
- **Material Design GUI**: Современный интерфейс для управления
- **Trainer**: Сервис активного обучения и дообучения моделей
- **MQTT Client**: Централизованная коммуникация между устройствами
- **Task Manager**: Распределение задач между роботами
- **CacheManager**: Управление кэшем системы
- **ModelSelector**: Выбор моделей из версий
- **AnnotationTool**: Инструмент ручной разметки

### 2. Edge Inference
- Локальный инференс YOLOv8 для быстрого отклика
- Оптимизация для Raspberry Pi / Jetson
- Публикация детекций в MQTT

### 3. Роботы
- **Collector**: RC-машинки с вакуумом и манипулятором
- **MiP Bridge**: Ретранслятор BLE → MQTT для MiP роботов

### 4. Data Lake
- Хранение всех данных для активного обучения
- Автоматическое управление датасетами
- Версионирование моделей

## 🚀 Быстрый старт

### Требования
- Python 3.8+
- Docker и Docker Compose (для MQTT брокера)
- 8GB+ RAM (рекомендуется 16GB)
- GPU (опционально, для обучения)

### Установка

```bash
# 1. Установка зависимостей
pip install -r requirements.txt

# 2. Настройка датасета (интеграция существующего)
python scripts/setup_dataset.py

# 3. Обучение модели (опционально, если нет готовой)
python scripts/train_model.py

# 4. Запуск MQTT брокера
docker-compose up -d mosquitto

# 5. Запуск всей системы
python scripts/start_system.py --all
```

**Детальные инструкции:** См. [QUICKSTART.md](docs/QUICKSTART.md) и [SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

### Запуск компонентов отдельно

```bash
# Полная система (Обелиск + GUI)
python scripts/start_econet_system.py

# Только Обелиск (центральный мозг, API)
python -m obelisk.api.main
# API будет доступен на http://localhost:8000

# Только GUI (Material Design интерфейс)
python -m obelisk.ui.gui_material

# Запуск без GUI (только API)
python scripts/start_econet_system.py --no-gui

# Edge Detector (детектор на камере)
python edge/inference_service/detector.py --source 0

# Collector Robot (робот-сборщик)
python robots/collector/collector_robot.py --robot-id collector_01
```

## 📚 Документация

### 🎯 Главная документация
- **[MAIN_DOCUMENTATION.md](MAIN_DOCUMENTATION.md)** ⭐ **ГЛАВНЫЙ ФАЙЛ** - полный обзор всей документации

### Основная документация
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Детальная техническая архитектура
- **[PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Структура проекта
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Быстрый старт за 5 минут
- **[SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** - Подробное руководство по установке
- **[INSTALL_GUIDE.md](docs/INSTALL_GUIDE.md)** - Руководство по установке зависимостей

### Функциональная документация
- **[CACHE_AND_MODEL_SELECTOR.md](docs/CACHE_AND_MODEL_SELECTOR.md)** - Очистка кэша и выбор модели
- **[ANNOTATION_TOOL_GUIDE.md](docs/ANNOTATION_TOOL_GUIDE.md)** - Инструмент ручной разметки
- **[ANNOTATION_FEATURES_SUMMARY.md](docs/ANNOTATION_FEATURES_SUMMARY.md)** - Итоговая реализация разметки
- **[MATERIAL_DESIGN_INTERFACE.md](docs/MATERIAL_DESIGN_INTERFACE.md)** - Material Design GUI
- **[UNIFIED_ENGINE_GUIDE.md](docs/UNIFIED_ENGINE_GUIDE.md)** - Руководство по UnifiedEngine
- **[MODEL_ENGINE_GUIDE.md](docs/MODEL_ENGINE_GUIDE.md)** - Ансамбль моделей с улучшенной математикой

### Системная документация
- **[SYSTEM_ARCHITECTURE_COMPLETE.md](docs/SYSTEM_ARCHITECTURE_COMPLETE.md)** - Полная архитектура системы
- **[NEURON_HIERARCHY_COMPLETE.md](docs/NEURON_HIERARCHY_COMPLETE.md)** - Иерархия нейронов (4 базовых + расширенные)
- **[ECONET_SWARM_SYSTEM.md](docs/ECONET_SWARM_SYSTEM.md)** - Система роя для автономной очистки
- **[ECONET_HIERARCHY.md](docs/ECONET_HIERARCHY.md)** - Иерархия компонентов
- **[NEURAL_ARCHITECTURE_4_NODES.md](docs/NEURAL_ARCHITECTURE_4_NODES.md)** - Нейронная архитектура
- **[SELF_AWARENESS.md](docs/SELF_AWARENESS.md)** - Система самоосознания
- **[ACTIVE_LEARNING_GUIDE.md](docs/ACTIVE_LEARNING_GUIDE.md)** - Активное обучение
- **[TRAINING_GUIDE.md](docs/TRAINING_GUIDE.md)** - Руководство по обучению моделей

### Тестирование
- **[tests/README.md](tests/README.md)** - Полная документация по тестированию
- **[tests/TESTING_MECHANICS.md](tests/TESTING_MECHANICS.md)** - Механика тестирования

## 🔬 Активное обучение

Система автоматически:
1. Собирает кадры с низкой уверенностью (0.3-0.7)
2. Сохраняет в Data Lake для разметки
3. Размечает (полуавтоматически или вручную)
4. Переобучает модель (fine-tuning)
5. Валидирует и при улучшении деплоит на edge устройства

**Настройка:**
```yaml
# config/config.yaml
active_learning:
  enabled: true
  confidence_lower: 0.3
  confidence_upper: 0.7
  min_samples_for_retrain: 100
  retrain_epochs: 20
```

## 🧪 Примеры использования

### Тест детектора
```bash
python examples/test_detection.py --mode image
```

### Тест API
```bash
python examples/test_api.py
```

### API документация
Откройте в браузере: http://localhost:8000/docs

## 🏗️ Компоненты системы

1. **ЭкоНет (UnifiedEngine)** - Центральный координатор роя
   - **4 базовых нейрона**:
     - YOLO-нейрон (`yolo_neuron`) - детекция мусора через ModelEngine
     - DeepSeek-нейрон (`deepseek_neuron`) - анализ и принятие решений (LLM, опционально)
     - Coordinator-нейрон (`coordinator_neuron`) - координация задач через TaskManager
     - Information Hub (`information_hub`) - центральная синхронизация всей системы
   - ModelEngine - управление YOLO моделями (FP32, поддержка GPU)
   - GPU венозная система - централизованное управление GPU ресурсами
   - Система самоидентификации - ЭкоНет осознает себя
   - Активное обучение - автоматическое улучшение моделей
   - AnnotationTool - инструменты для ручной разметки
   - CacheManager - управление кэшем системы
   - ModelSelector - выбор моделей из версий обучения

2. **Рой Роботов** - Автономные роботы-сборщики
   - Collector Robot - робот-сборщик с вакуумом
   - Координация через MQTT
   - Умный выбор робота для задач

3. **Edge Detector** - Локальный инференс YOLO

4. **Data Lake** - Хранилище для активного обучения

5. **MQTT Broker** - Коммуникация между устройствами и роботами

## 📊 Существующие компоненты

Проект интегрирует:
- ✅ **YOLOv8** - Уже установлен и настроен
- ✅ **Датасет окурков** - 7029 train + 1581 valid + 789 test изображений
- ✅ **Модель YOLO** - Готова к использованию или обучению

## 🔧 Конфигурация

Все настройки в `config/config.yaml`:
- Обелиск (API, MQTT)
- Модель (YOLO параметры)
- Датасет (пути к данным)
- Активное обучение
- Роботы
- Логирование

## 🐳 Docker

```bash
# Запуск MQTT брокера
docker-compose up -d mosquitto

# Запуск Обелиска (TODO: добавить в docker-compose)
docker build -f docker/obelisk/Dockerfile -t swarm-cleaner-obelisk .
docker run -p 8000:8000 swarm-cleaner-obelisk
```

## 📝 Лицензия

MIT License

## 🤝 Вклад

Проект создан согласно техническому заданию из `Project Family.docx` с полной архитектурой самообучающейся системы.
