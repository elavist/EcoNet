# 🎯 Интеграция профессионального трекинга в нейронную сеть ЭкоНет

## Обзор

Реализована профессиональная система трекинга объектов на основе алгоритма **ByteTrack**, интегрированная в нейронную сеть ЭкоНет. Система позволяет отслеживать каждый окурок в реальном времени и координировать работу роя роботов.

**Все нейроны подключены к GPU системе (veins) для оптимизации производительности.**

## Архитектура трекинга

### Поток данных

```
YOLO Detection → Detection Neuron → Tracking Neuron → Hub Neuron → MQTT Neuron → Рой роботов
                     ↓                    ↓                ↓
                  Детекции          Отслеженные      Координация
                                   объекты с ID      работы роя
```

### Компоненты

#### 1. ByteTracker (`obelisk/core/processors/byte_tracker.py`)

Профессиональный трекер объектов на основе алгоритма ByteTrack:

- **Преимущества ByteTrack:**
  - Использует все детекции (даже с низкой уверенностью) для лучшего трекинга
  - Высокая точность в реальном времени
  - Устойчивость к окклюзиям и перекрытиям
  - Эффективное восстановление потерянных треков

- **Параметры:**
  - `track_thresh`: Порог для создания новых треков (0.5)
  - `high_thresh`: Высокий порог для детекций (0.6)
  - `match_thresh`: Порог для сопоставления треков (0.8)
  - `track_buffer`: Буфер кадров для потерянных треков (30)
  - `min_box_area`: Минимальная площадь бокса (10)

#### 2. TrackingNeuron (`obelisk/neurons/perception/tracking_neuron.py`)

Нейрон трекинга, интегрированный в нейронную сеть:

- **Функции:**
  - Получение детекций от Detection Neuron
  - Обработка через ByteTracker
  - Отправка отслеженных объектов в Hub и MQTT
  - Хранение истории треков

- **Методы:**
  - `think()`: Обработка детекций и трекинг
  - `get_tracked_object(track_id)`: Получить информацию о треке
  - `get_all_tracked_objects()`: Получить все активные треки
  - `get_track_history(track_id)`: Получить историю трека

## Интеграция в нейронную сеть

### Связи нейронов

```
Detection Neuron
    ↓ (data)
Tracking Neuron
    ↓ (data)
Hub Neuron ← → MQTT Neuron → Рой роботов
```

### Новые нейроны

1. **Docker Neuron** (`docker_neuron.py`)
   - Управление Docker контейнерами
   - Мониторинг статуса контейнеров
   - Связь: Docker ↔ Hub

2. **MQTT Neuron** (`mqtt_neuron.py`)
   - Управление MQTT сообщениями
   - Публикация/подписка на топики
   - Связь: MQTT ↔ Hub, Detection → MQTT, Tracking → MQTT

3. **Tracking Neuron** (`tracking_neuron.py`)
   - Профессиональный трекинг объектов
   - Отслеживание окурков в реальном времени
   - Связь: Detection → Tracking → Hub → MQTT

## Использование

### Инициализация

```python
from obelisk.brain.neural_network_builder import NeuralNetworkBuilder

# Создание строителя нейронной сети
builder = NeuralNetworkBuilder(unified_engine)
builder.build_network()

# Доступ к нейронам
tracking_neuron = builder.neurons["tracking_neuron"]
mqtt_neuron = builder.neurons["mqtt_neuron"]
docker_neuron = builder.neurons["docker_neuron"]
```

### Трекинг объектов

```python
# Детекции от YOLO
detections = [
    {
        "bbox": [100, 200, 150, 250],  # [x1, y1, x2, y2]
        "confidence": 0.85,
        "class": 0  # окурок
    }
]

# Обработка через Tracking Neuron
context = {
    "detections": detections,
    "frame_number": 1
}

result = await tracking_neuron.think(context)

# Результат содержит отслеженные объекты с track_id
tracked_objects = result["detections"]
for obj in tracked_objects:
    print(f"Track ID: {obj['track_id']}, Position: {obj['bbox']}")
```

### Получение информации о треках

```python
# Получить все активные треки
active_tracks = tracking_neuron.get_all_tracked_objects()

# Получить информацию о конкретном треке
track_info = tracking_neuron.get_tracked_object(track_id=1)

# Получить историю трека
track_history = tracking_neuron.get_track_history(track_id=1, limit=10)

# Статистика трекинга
stats = tracking_neuron.get_statistics()
```

### MQTT коммуникация

```python
# Публикация отслеженных объектов через MQTT
context = {
    "action": "publish",
    "topic": "swarm/tracking/objects",
    "payload": {
        "frame_number": 1,
        "tracks": tracked_objects
    }
}

await mqtt_neuron.think(context)
```

### Docker управление

```python
# Получение статуса контейнеров
context = {
    "action": "status"
}

status = await docker_neuron.think(context)

# Запуск контейнера
context = {
    "action": "start",
    "container": "swarm-cleaner-obelisk"
}

result = await docker_neuron.think(context)
```

## Логика работы

### Поток обработки кадра

1. **YOLO Detection** → Детекция окурков на кадре
2. **Detection Neuron** → Получение детекций
3. **Tracking Neuron** → Трекинг объектов через ByteTrack
   - Сопоставление с существующими треками
   - Создание новых треков
   - Восстановление потерянных треков
4. **Hub Neuron** → Синхронизация данных
5. **MQTT Neuron** → Отправка координат окурков рою роботов
6. **Рой роботов** → Получение координат и выполнение задач

### Диалог через нейронную связь

Все нейроны общаются через нейронную сеть:

- **Detection → Tracking**: Детекции для трекинга
- **Tracking → Hub**: Отслеженные объекты
- **Hub → MQTT**: Координаты для роя
- **MQTT → Рой**: Команды и координаты
- **Рой → MQTT**: Статусы выполнения
- **MQTT → Hub**: Обратная связь от роя
- **Hub → Tracking**: Обновления и команды

## Преимущества

1. **Профессиональный трекинг**: ByteTrack обеспечивает высокую точность
2. **Реальное время**: Оптимизирован для работы в реальном времени
3. **Устойчивость**: Восстановление потерянных треков
4. **Координация**: Интеграция с роем роботов через MQTT
5. **Масштабируемость**: Легко добавлять новые нейроны

## Конфигурация

### Настройка трекера

```python
tracker_config = {
    "frame_rate": 30,
    "track_thresh": 0.5,      # Порог для новых треков
    "high_thresh": 0.6,       # Высокий порог детекций
    "match_thresh": 0.8,      # Порог сопоставления
    "track_buffer": 30,       # Буфер для потерянных треков
    "min_box_area": 10,       # Минимальная площадь
    "mot_thresh": 0.8         # Порог MOT метрики
}

tracking_neuron = TrackingNeuron(tracker_config)
```

## Статистика и мониторинг

```python
# Статистика трекинга
stats = tracking_neuron.get_statistics()
print(f"Активных треков: {stats['active_tracks']}")
print(f"Всего треков: {stats['track_statistics']['total_tracks']}")

# Статистика MQTT
mqtt_stats = mqtt_neuron.get_statistics()
print(f"Отправлено сообщений: {mqtt_stats['messages_sent']}")

# Статистика Docker
docker_stats = docker_neuron.get_statistics()
print(f"Контейнеров: {docker_stats['containers_count']}")
```

## Заключение

Система трекинга полностью интегрирована в нейронную сеть ЭкоНет и готова к использованию. Все нейроны общаются через профессиональный диалог, обеспечивая координацию работы роя роботов в реальном времени.

