"""
Оптимизация модели для максимального FPS
Экспортирует модель в ONNX и настраивает параметры
"""

from pathlib import Path
from ultralytics import YOLO
import yaml


def optimize_model_for_fps():
    """Оптимизация модели для максимального FPS"""
    
    print("=" * 70)
    print("ОПТИМИЗАЦИЯ МОДЕЛИ ДЛЯ МАКСИМАЛЬНОГО FPS")
    print("=" * 70)
    
    # Загрузка конфигурации
    config_path = Path("config/config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    model_path = Path(config.get("model", {}).get("weights_path", "models/cigarette_detector/best.pt"))
    
    if not model_path.exists():
        print(f"❌ Модель не найдена: {model_path}")
        return
    
    print(f"📦 Загрузка модели: {model_path}")
    model = YOLO(str(model_path))
    
    # 1. Экспорт в ONNX (быстрее чем PyTorch)
    print("\n1️⃣ Экспорт в ONNX формат...")
    onnx_path = model_path.parent / f"{model_path.stem}.onnx"
    
    try:
        model.export(
            format="onnx",
            imgsz=416,  # Уменьшенный размер для скорости
            simplify=True,
            opset=13,
            dynamic=False,  # Статический размер для скорости
            half=False  # FP32 для совместимости, можно FP16 если GPU поддерживает
        )
        
        # Найти созданный ONNX файл
        exported_path = model_path.parent / f"{model_path.stem}.onnx"
        if not exported_path.exists():
            # Может быть создан в runs/export
            runs_export = Path("runs/export")
            if runs_export.exists():
                onnx_files = list(runs_export.glob("**/*.onnx"))
                if onnx_files:
                    exported_path = onnx_files[-1]  # Последний
        
        if exported_path.exists():
            print(f"✅ ONNX модель сохранена: {exported_path}")
            print(f"   Размер: {exported_path.stat().st_size / (1024*1024):.2f} MB")
        else:
            print("⚠️ ONNX файл не найден после экспорта")
            
    except Exception as e:
        print(f"⚠️ Ошибка экспорта в ONNX: {e}")
        print("💡 Продолжаем с PyTorch моделью")
    
    # 2. Обновление конфигурации для максимального FPS
    print("\n2️⃣ Обновление конфигурации для максимального FPS...")
    
    # Оптимизированные параметры
    config_updates = {
        "model": {
            "input_size": 416,  # Уменьшено с 640 для скорости (меньше точность, больше FPS)
            "confidence_threshold": 0.5,
            "iou_threshold": 0.45,
            "max_detections": 100,  # Уменьшено для скорости
        },
        "edge": {
            "device": "cpu",  # Изменить на "cuda:0" если есть GPU
            "inference_interval": 0.0,  # Минимальный интервал (максимум FPS)
            "max_queue_size": 50,  # Уменьшено для меньшей задержки
        }
    }
    
    # Обновить конфиг
    for key, value in config_updates.items():
        if key in config:
            config[key].update(value)
        else:
            config[key] = value
    
    # Сохранить оптимизированную конфигурацию
    optimized_config_path = Path("config/config_optimized_fps.yaml")
    with open(optimized_config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ Оптимизированная конфигурация: {optimized_config_path}")
    
    # 3. Рекомендации
    print("\n" + "=" * 70)
    print("РЕКОМЕНДАЦИИ ДЛЯ МАКСИМАЛЬНОГО FPS")
    print("=" * 70)
    print("1. Используйте GPU (если доступен):")
    print("   Измените в config: edge.device = 'cuda:0'")
    print()
    print("2. Уменьшите размер входного изображения:")
    print("   input_size: 416 или 320 (вместо 640)")
    print("   - 640: лучше точность, медленнее")
    print("   - 416: баланс скорости и точности")
    print("   - 320: максимальная скорость, меньше точность")
    print()
    print("3. Используйте ONNX модель (если экспортирована):")
    print("   model = YOLO('models/cigarette_detector/best.onnx')")
    print()
    print("4. Пропускайте кадры (skip frames):")
    print("   Обрабатывайте каждый 2-й или 3-й кадр")
    print()
    print("5. Уменьшите max_detections:")
    print("   max_detections: 50-100 (вместо 300)")
    print()
    print("6. Используйте более легкую модель:")
    print("   yolov8n (nano) вместо yolov8s/m/l")
    print("=" * 70)
    
    # 4. Бенчмарк скорости
    print("\n📊 Тестирование скорости...")
    try:
        import cv2
        import numpy as np
        import time
        
        test_img = np.zeros((640, 640, 3), dtype=np.uint8)
        
        # Теплый запуск
        _ = model(test_img, imgsz=416, verbose=False)
        
        # Тест скорости
        times = []
        for _ in range(10):
            start = time.time()
            _ = model(test_img, imgsz=416, verbose=False)
            times.append(time.time() - start)
        
        avg_time = sum(times) / len(times)
        fps = 1.0 / avg_time
        
        print(f"   Среднее время inference: {avg_time*1000:.2f} ms")
        print(f"   Теоретический FPS: {fps:.1f}")
        
        # С 640
        times_640 = []
        for _ in range(5):
            start = time.time()
            _ = model(test_img, imgsz=640, verbose=False)
            times_640.append(time.time() - start)
        
        avg_time_640 = sum(times_640) / len(times_640)
        fps_640 = 1.0 / avg_time_640
        
        print(f"\n   Сравнение:")
        print(f"   640x640: {avg_time_640*1000:.2f} ms ({fps_640:.1f} FPS)")
        print(f"   416x416: {avg_time*1000:.2f} ms ({fps:.1f} FPS)")
        print(f"   Улучшение: {fps/fps_640:.2f}x быстрее")
        
    except Exception as e:
        print(f"⚠️ Ошибка теста скорости: {e}")
    
    print("\n✅ Оптимизация завершена!")
    print("💡 Используйте оптимизированную конфигурацию для максимального FPS")


if __name__ == "__main__":
    optimize_model_for_fps()

