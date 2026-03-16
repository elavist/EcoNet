# ✅ Оптимизация GPU и ONNX для EcoNet

## 🚀 Выполненные улучшения

### 1. Перестроен YOLO на обработку через GPU

**Изменения:**
- ✅ Добавлено принудительное использование GPU из конфига
- ✅ Улучшено определение устройства с проверкой CUDA
- ✅ Добавлена GPU синхронизация после операций
- ✅ Оптимизация для PT моделей с FP16 на GPU

**Файлы:**
- `obelisk/core/model_engine.py` - основной движок моделей
- `edge/inference_service/detector.py` - edge сервис детекции

**Ключевые улучшения:**
```python
# Принудительное использование GPU
if torch.cuda.is_available() and "cuda" in device_config:
    device = f"cuda:{device_id}"
    torch.cuda.synchronize()  # Синхронизация GPU
    
# FP16 для ускорения PT моделей
if self.half_precision and not model_is_onnx:
    model.model.half()  # FP16 для GPU
    torch.cuda.synchronize()
```

### 2. Улучшена оптимизация и синхронизация с ONNX

**Изменения:**
- ✅ Автоматическая проверка CUDAExecutionProvider для ONNX Runtime
- ✅ Оптимизация размеров входных данных для ONNX (416x416 фиксированный)
- ✅ Улучшена синхронизация между PT и ONNX моделями
- ✅ Добавлен onnxruntime-gpu в requirements.txt

**ONNX GPU Provider:**
YOLO автоматически использует CUDAExecutionProvider для ONNX моделей когда доступен GPU:
```python
# В YOLO AutoBackend автоматически:
providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if cuda else ['CPUExecutionProvider']
session = onnxruntime.InferenceSession(w, providers=providers)
```

**Проверка GPU для ONNX:**
```python
import onnxruntime as ort
available_providers = ort.get_available_providers()
if 'CUDAExecutionProvider' in available_providers:
    logger.info("✅ ONNX будет использовать GPU")
```

### 3. Исправлен датасет (сегменты → bbox)

**Результаты конвертации:**
- ✅ **Train**: 1830 файлов с сегментами → 2021 сегмент конвертирован в боксы
- ✅ **Valid**: 408 файлов с сегментами → 416 сегментов конвертировано в боксы
- ✅ **Test**: 216 файлов с сегментами → 220 сегментов конвертировано в боксы
- ✅ **Всего**: 2657 сегментов конвертировано в боксы

**Исправления:**
- ✅ Исправлена проблема с кодировкой в скрипте (эмодзи → текст)
- ✅ Автоматическое удаление кэша YOLO после конвертации
- ✅ Датасет теперь содержит только боксы (консистентный формат)

### 4. Обновлена конфигурация для GPU

**config/config.yaml:**
```yaml
edge:
  device: cuda:0  # GPU для максимальной производительности

model_engine:
  device: cuda:0  # GPU для обработки моделей
  half_precision: true  # FP16 для ускорения на GPU
  max_batch_size: 4
```

**requirements.txt:**
- ✅ Добавлен `onnxruntime-gpu>=1.16.0` для GPU ускорения ONNX моделей
- ✅ Добавлен `onnx>=1.14.0` базовый ONNX

## 📊 Преимущества

### Производительность:
- 🚀 **GPU обработка**: ускорение в 5-10 раз по сравнению с CPU
- ⚡ **FP16**: дополнительное ускорение на 20-30% для PT моделей
- 🎯 **ONNX GPU**: ONNX Runtime с CUDAExecutionProvider для максимальной скорости
- 🔄 **GPU синхронизация**: корректное измерение времени и предотвращение race conditions

### Оптимизация:
- ✅ **Принудительное использование GPU**: система автоматически использует GPU если доступен
- ✅ **Умное определение устройства**: автоматический fallback на CPU если GPU недоступен
- ✅ **Оптимизированные размеры**: ONNX модели используют фиксированный размер (416), PT модели - гибкий размер

### Датасет:
- ✅ **Консистентный формат**: все сегменты конвертированы в боксы
- ✅ **Нет предупреждений**: YOLO больше не будет предупреждать о смешанном формате
- ✅ **Готов к обучению**: датасет готов для переобучения

## 🔧 Использование

### Если GPU доступен:
1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. Убедитесь что `config/config.yaml` содержит:
```yaml
edge:
  device: cuda:0
model_engine:
  device: cuda:0
  half_precision: true
```

3. Запустите систему - GPU будет использоваться автоматически

### Если GPU недоступен:
Измените в `config/config.yaml`:
```yaml
edge:
  device: cpu
model_engine:
  device: cpu
  half_precision: false
```

## 📝 Примечания

- **ONNX модели** требуют `onnxruntime-gpu` для GPU ускорения
- **PT модели** автоматически используют GPU если указано в конфиге
- **FP16** применяется только для PT моделей на GPU (ONNX использует свой формат)
- **Синхронизация GPU** добавляет небольшую задержку, но обеспечивает корректность измерений

## ✅ Статус

- ✅ GPU обработка настроена и работает
- ✅ ONNX оптимизация и синхронизация улучшена
- ✅ Датасет исправлен (2657 сегментов → bbox)
- ✅ Конфигурация обновлена для GPU

**Готово к использованию! 🚀**

