"""
Скрипт для обучения модели YOLO на датасете окурков
Обучение с нуля на чистом датасете через GPU
"""

import yaml
from pathlib import Path
from ultralytics import YOLO
import torch


def train_model():
    """Обучение модели YOLO с нуля на GPU"""
    
    # Загрузка конфигурации
    config_path = Path("config/config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    model_config = config.get("model", {})
    dataset_config = config.get("dataset", {})
    model_engine_config = config.get("model_engine", {})
    
    # Определение устройства (GPU/CPU)
    device_config = model_engine_config.get("device") or config.get("edge", {}).get("device", "cpu")
    
    # Проверка доступности GPU
    if "cuda" in str(device_config).lower() or "gpu" in str(device_config).lower():
        if torch.cuda.is_available():
            device = device_config if ':' in str(device_config) else "cuda:0"
            device_id = device.split(':')[-1] if ':' in device else "0"
            gpu_name = torch.cuda.get_device_name(int(device_id))
            gpu_memory = torch.cuda.get_device_properties(int(device_id)).total_memory / (1024**3)
            print(f"✅ GPU доступен: {gpu_name} ({gpu_memory:.1f} GB)")
            device = f"cuda:{device_id}"
        else:
            print("⚠️ GPU запрошен, но недоступен. Используется CPU")
            device = "cpu"
    else:
        device = "cpu"
        print("ℹ️ Используется CPU")
    
    # Параметры обучения
    model_name = model_config.get("name", "yolov8n")
    data_config = dataset_config.get("base_path") + "/data.yaml"
    epochs = 100
    batch_size = 16 if device == "cpu" else 32  # Больший батч на GPU
    imgsz = model_config.get("input_size", 640)
    
    # Увеличение батча для GPU для максимальной эффективности
    if device != "cpu":
        # Определяем оптимальный батч на основе памяти GPU
        if torch.cuda.is_available():
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            if gpu_memory_gb >= 8:
                batch_size = 32
            elif gpu_memory_gb >= 4:
                batch_size = 16
            else:
                batch_size = 8
    
    print("=" * 70)
    print("ОБУЧЕНИЕ МОДЕЛИ YOLO ДЛЯ ДЕТЕКЦИИ ОКУРКОВ")
    print("Обучение с нуля на чистом датасете")
    print("=" * 70)
    print(f"Модель: {model_name}.pt")
    print(f"Датасет: {data_config}")
    print(f"Устройство: {device}")
    print(f"Эпохи: {epochs}")
    print(f"Размер батча: {batch_size}")
    print(f"Размер изображения: {imgsz}")
    
    if device != "cpu" and torch.cuda.is_available():
        device_id = int(device.split(':')[-1])
        gpu_name = torch.cuda.get_device_name(device_id)
        gpu_memory = torch.cuda.get_device_properties(device_id).total_memory / (1024**3)
        print(f"GPU: {gpu_name}")
        print(f"Память GPU: {gpu_memory:.1f} GB")
        print(f"⚠️ Время обучения на GPU: ~20-40 минут")
    else:
        print(f"⚠️ Время обучения на CPU: ~2-4 часа")
    
    print("=" * 70)
    
    # Загрузка модели (предобученная для обучения с нуля)
    print(f"\n📦 Загрузка предобученной модели {model_name}.pt...")
    model = YOLO(f"{model_name}.pt")
    
    # Обучение с оптимизацией для GPU
    print(f"\n🚀 Начало обучения...")
    print(f"   Устройство: {device}")
    print(f"   Размер батча: {batch_size}")
    
    train_args = {
        "data": data_config,
        "epochs": epochs,
        "batch": batch_size,
        "imgsz": imgsz,
        "device": device,  # Явное указание устройства
        "project": "models/cigarette_detector",
        "name": "train",
        "save": True,
        "exist_ok": True,
        "verbose": True,
        "plots": True,  # Графики обучения
        "val": True,  # Валидация
    }
    
    # Дополнительные оптимизации для GPU
    if device != "cpu":
        train_args["amp"] = True  # Automatic Mixed Precision для ускорения
        train_args["workers"] = 8  # Больше воркеров для загрузки данных
        train_args["cache"] = "ram" if gpu_memory >= 8 else False  # Кэширование на RAM для больших GPU
    else:
        train_args["workers"] = 4  # Меньше воркеров на CPU
    
    # Обучение
    results = model.train(**train_args)
    
    # Вывести результаты
    print("\n" + "=" * 70)
    print("ОБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 70)
    print(f"Лучшая модель: models/cigarette_detector/train/weights/best.pt")
    
    # Метрики из результатов
    metrics = results.results_dict if hasattr(results, 'results_dict') else {}
    map50 = metrics.get('metrics/mAP50(B)', 0)
    precision = metrics.get('metrics/precision(B)', 0)
    recall = metrics.get('metrics/recall(B)', 0)
    
    print(f"\n📊 РЕЗУЛЬТАТЫ:")
    print(f"   mAP@0.5: {map50:.4f}")
    print(f"   Precision: {precision:.4f} ({precision*100:.2f}%)")
    print(f"   Recall: {recall:.4f} ({recall*100:.2f}%)")
    print("=" * 70)
    
    # Скопировать лучшую модель в основную директорию
    best_model = Path("models/cigarette_detector/train/weights/best.pt")
    target_model = Path(model_config.get("weights_path", "models/cigarette_detector/best.pt"))
    target_model.parent.mkdir(parents=True, exist_ok=True)
    
    if best_model.exists():
        import shutil
        shutil.copy(best_model, target_model)
        print(f"Модель скопирована в: {target_model}")
    
    return results


if __name__ == "__main__":
    train_model()


