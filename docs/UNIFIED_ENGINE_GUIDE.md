# UnifiedEngine - Единый движок ЭкоНет

## Описание

`UnifiedEngine` - это **сплав всех моделей и механик** ЭкоНет в единую оптимизированную систему.

## Архитектура

UnifiedEngine объединяет:

### 1. Модели
- **YOLO модели** (детекция) - через `ModelEngine`
- **Ансамбль моделей** - поддержка нескольких моделей одновременно

### 2. Core (Ядро системы)
- **ModelEngine** - управление YOLO моделями с ансамблем
- **ModelTesting** - тестирование моделей при запуске
- **ObjectTracker** - отслеживание объектов между кадрами
- **NeuralNodes** - нейронная архитектура (3 нейрона)

### 3. Сервисы
- **MediaManager** - управление медиа файлами
- **CacheManager** - управление кэшем системы
- **ModelSelector** - выбор моделей из версий
- **AnnotationTool** - инструмент ручной разметки
- **VisionContext** - визуальный анализ
- **SelfIdentityService** - самоидентификация
- **SelfModificationService** - самомодификация
- **SelfLearningService** - самообучение
- **ActiveLearner** - активное обучение
- **Trainer** - обучение моделей
- **Database** - база данных
- **MQTTClient** - MQTT коммуникация
- **TaskManager** - управление задачами

### 3. Оптимизация
- **Параллельная обработка** - асинхронные задачи
- **Кэширование** - детекции и LLM запросы
- **ThreadPoolExecutor** - пул потоков для оптимизации
- **Статистика** - отслеживание производительности

## Использование

```python
from obelisk.core.unified_engine import UnifiedEngine
import yaml

# Загрузка конфигурации
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Создание движка
engine = UnifiedEngine(config)

# Инициализация (асинхронная)
await engine.initialize()

# Обработка кадра (включает детекцию и визуальный анализ)
result = await engine.process_frame(frame)
detections = result["detections"]
visual_context = result["visual_context"]

# Получение статистики
stats = engine.get_stats()
print(f"Обработано кадров: {stats['frames_processed']}")
print(f"Найдено детекций: {stats['total_detections']}")
response = await engine.process_message("Что видишь?", visual_context)

# Получение статистики
stats = engine.get_statistics()
```

## API

### `initialize()`
Инициализация всех компонентов системы

### `process_frame(frame, frame_id=None)`
Обработка кадра через все системы:
- Детекция через ModelEngine
- Визуальный анализ через VisionContext
- Возвращает объединенные результаты

### `process_message(message, visual_context=None, stream_callback=None)`
Обработка сообщения через DeepSeek:
- Использует ChatService
- Интегрирует визуальный контекст
- Поддерживает streaming

### `get_statistics()`
Полная статистика системы:
- Производительность
- Статус компонентов
- Метрики моделей

### `optimize_performance()`
Оптимизация производительности:
- Очистка кэшей
- Оптимизация компонентов

### `shutdown()`
Корректное завершение работы

## Преимущества

1. **Единая точка входа** - все через один движок
2. **Оптимизация** - параллельная обработка, кэширование
3. **Масштабируемость** - легко добавлять новые компоненты
4. **Производительность** - высший уровень оптимизации
5. **Интеграция** - все модели и механики работают вместе

## Поток данных

```
Кадр → UnifiedEngine → ModelEngine (YOLO) → Детекции
                    → VisionContext → Визуальный контекст
                    
Сообщение → UnifiedEngine → ChatService → DeepSeek → Ответ
```

## Статистика

Движок отслеживает:
- Количество обработанных кадров
- Количество детекций
- Количество LLM запросов
- Средний FPS
- Среднее время детекции
- Среднее время LLM ответа

## Оптимизация

1. **Кэширование** - детекции и LLM запросы кэшируются
2. **Параллелизм** - асинхронная обработка
3. **Пул потоков** - ThreadPoolExecutor для тяжелых операций
4. **Очереди** - управление нагрузкой через очереди

