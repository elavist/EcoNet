# 🩸 Интеграция GPU Veins (Вен) в нейронную сеть ЭкоНет

## Обзор

GPU система ЭкоНет работает как кровеносная система организма - распределяет ресурсы GPU между всеми нейронами для оптимальной производительности.

## Архитектура GPU системы

### Компоненты

1. **GPUCirculatorySystem** (`obelisk/veins/gpu_circulatory.py`)
   - Распределение GPU ресурсов
   - Управление очередью запросов
   - Выделение и освобождение GPU

2. **GPUDistributor** (`obelisk/veins/gpu_distributor.py`)
   - Умное распределение GPU между задачами
   - Приоритизация задач
   - Стратегии распределения (fair, priority, performance)

3. **GPUMonitor** (`obelisk/veins/gpu_monitor.py`)
   - Мониторинг состояния GPU
   - Статистика использования памяти
   - История загрузки

4. **GPUScheduler** (`obelisk/veins/gpu_scheduler.py`)
   - Планирование использования GPU
   - Отложенное выполнение задач

## Подключение нейронов к GPU

### Нейроны с GPU поддержкой

#### 1. DetectionNeuron
- **GPU использование**: Через ModelEngine (YOLO)
- **Мониторинг**: GPUMonitor отслеживает использование
- **Статус**: ✅ Подключен

```python
detection_neuron = DetectionNeuron(
    model_engine=model_engine,  # Использует GPU для YOLO
    gpu_monitor=gpu_monitor      # Мониторинг GPU
)
```

#### 2. TrackingNeuron
- **GPU использование**: Оптимизация трекинга через ByteTrack
- **Система**: Полная интеграция с GPU системой
- **Статус**: ✅ Подключен

```python
tracking_neuron = TrackingNeuron(
    gpu_circulatory=gpu_circulatory,  # Выделение GPU
    gpu_distributor=gpu_distributor,   # Распределение
    gpu_monitor=gpu_monitor            # Мониторинг
)
```

#### 3. DockerNeuron
- **GPU использование**: Не требуется (управление контейнерами)
- **Статус**: ❌ Не подключен (не требуется)

#### 4. MQTTNeuron
- **GPU использование**: Не требуется (сетевая коммуникация)
- **Статус**: ❌ Не подключен (не требуется)

### Проверка подключений

#### Старые нейроны

1. **DetectionNeuron** ✅
   - Использует GPU через ModelEngine
   - Мониторинг через GPUMonitor
   - Статистика GPU доступна

2. **VisionNeuron** ⚠️
   - Не требует GPU напрямую
   - Использует VisionContext (может использовать GPU опосредованно)

3. **HubNeuron** ❌
   - Не требует GPU (коммуникация)

4. **TaskCoordinatorNeuron** ❌
   - Не требует GPU (координация)

5. **SwarmCoordinatorNeuron** ❌
   - Не требует GPU (координация роя)

## Использование GPU системы

### Инициализация

```python
from obelisk.brain.neural_network_builder import NeuralNetworkBuilder
from obelisk.veins.gpu_circulatory import GPUCirculatorySystem
from obelisk.veins.gpu_distributor import GPUDistributor
from obelisk.veins.gpu_monitor import GPUMonitor

# GPU система создается автоматически в NeuralNetworkBuilder
builder = NeuralNetworkBuilder(unified_engine)
builder.build_network()

# Доступ к GPU системе
gpu_system = builder.get_gpu_system()
circulatory = gpu_system["circulatory"]
distributor = gpu_system["distributor"]
monitor = gpu_system["monitor"]
```

### Запрос GPU ресурсов

```python
# Запрос GPU для задачи
gpu_info = await circulatory.request_gpu(
    task_id="tracking_frame_1",
    priority=7,              # Приоритет (1-10)
    memory_required=0.05     # Требуемая память (0-1)
)

if gpu_info:
    device = gpu_info["device"]  # "cuda:0"
    # Использование GPU
    # ...
    
    # Освобождение GPU
    await circulatory.release_gpu("tracking_frame_1")
```

### Мониторинг GPU

```python
# Получение статистики GPU
gpu_stats = monitor.get_gpu_stats()

if gpu_stats:
    for device in gpu_stats["devices"]:
        print(f"Device: {device['device_name']}")
        print(f"Memory: {device['allocated_memory_gb']:.2f} GB / {device['total_memory_gb']:.2f} GB")
        print(f"Usage: {device['usage_percent']:.1f}%")

# Статистика кровообращения
circ_stats = circulatory.get_statistics()
print(f"Total requests: {circ_stats['total_requests']}")
print(f"Success rate: {circ_stats['success_rate']:.2%}")
```

### Распределение GPU между задачами

```python
# Распределение GPU для нескольких задач
tasks = [
    {"id": "task1", "memory_required": 0.1, "priority": 8},
    {"id": "task2", "memory_required": 0.05, "priority": 5},
    {"id": "task3", "memory_required": 0.2, "priority": 9}
]

result = await distributor.distribute_gpu(tasks)

print(f"Allocated: {len(result['allocated'])}")
print(f"Pending: {len(result['pending'])}")
print(f"Failed: {len(result['failed'])}")
```

## Статистика нейронов

### DetectionNeuron

```python
stats = detection_neuron.get_statistics()

print(f"Detections: {stats['detections_count']}")
print(f"GPU available: {stats['gpu_available']}")
print(f"GPU usage count: {stats['gpu_usage_count']}")

if "gpu_stats" in stats:
    print(f"GPU stats: {stats['gpu_stats']}")
```

### TrackingNeuron

```python
stats = tracking_neuron.get_statistics()

print(f"Frame number: {stats['frame_number']}")
print(f"Active tracks: {stats['active_tracks']}")
print(f"GPU enabled: {stats['gpu_enabled']}")

if "gpu_stats" in stats:
    print(f"GPU stats: {stats['gpu_stats']}")

if "gpu_circulatory_stats" in stats:
    print(f"GPU circulatory: {stats['gpu_circulatory_stats']}")
```

## Тестирование

### Запуск тестов

```bash
# Тесты GPU интеграции
pytest tests/integration/test_gpu_neurons.py -v

# Конкретный тест
pytest tests/integration/test_gpu_neurons.py::TestTrackingNeuronGPU::test_tracking_neuron_with_gpu -v
```

### Проверка подключений

```python
# Скрипт проверки подключений
python scripts/check_gpu_connections.py
```

## Оптимизация

### Приоритеты задач

- **10**: Критические задачи (детекция в реальном времени)
- **8-9**: Высокий приоритет (трекинг)
- **5-7**: Средний приоритет (обработка данных)
- **1-4**: Низкий приоритет (фоновые задачи)

### Стратегии распределения

1. **fair**: Справедливое распределение
2. **priority**: По приоритету задач
3. **performance**: Максимальная производительность

```python
distributor.set_distribution_strategy("priority")
```

## Мониторинг и диагностика

### Проверка состояния GPU

```python
# Запуск мониторинга
monitor.start_monitoring()

# Получение истории
history = monitor.get_history(limit=100)

# Остановка мониторинга
monitor.stop_monitoring()
```

### Диагностика проблем

```python
# Проверка доступности GPU
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"Device count: {torch.cuda.device_count()}")

# Статистика кровообращения
stats = circulatory.get_statistics()
if stats["success_rate"] < 0.8:
    print("⚠️ Низкий процент успешных выделений GPU")
    print(f"Failed: {stats['failed_allocations']}")
```

## Заключение

GPU система полностью интегрирована в нейронную сеть ЭкоНет:

- ✅ **DetectionNeuron**: Использует GPU через ModelEngine
- ✅ **TrackingNeuron**: Полная интеграция с GPU системой
- ✅ **Мониторинг**: Отслеживание использования GPU
- ✅ **Распределение**: Умное распределение ресурсов
- ✅ **Тесты**: Полное покрытие тестами

Все нейроны, требующие GPU, подключены и оптимизированы для работы в реальном времени.

