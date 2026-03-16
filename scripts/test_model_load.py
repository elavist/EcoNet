"""
Быстрый тест загрузки модели и детекции
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from ultralytics import YOLO
import cv2
import numpy as np

print("=" * 60)
print("Тест загрузки модели")
print("=" * 60)

# Путь к модели
model_path = "models/cigarette_detector/best.pt"

if Path(model_path).exists():
    print(f"✅ Модель найдена: {model_path}")
    print(f"   Размер файла: {Path(model_path).stat().st_size / 1024 / 1024:.2f} MB")
    
    try:
        # Загрузка модели
        print("\nЗагрузка модели...")
        model = YOLO(model_path)
        print("✅ Модель загружена успешно!")
        
        # Информация о модели
        print(f"\nИнформация о модели:")
        print(f"   Классы: {model.names}")
        print(f"   Количество классов: {len(model.names)}")
        
        # Тест на черном изображении
        print("\nТест детекции на тестовом изображении...")
        test_img = np.zeros((640, 640, 3), dtype=np.uint8)
        
        # Попробовать разные пороги
        for conf_threshold in [0.3, 0.5, 0.7]:
            results = model(test_img, conf=conf_threshold, verbose=False)
            detections = results[0].boxes
            print(f"   Порог {conf_threshold}: найдено {len(detections)} детекций")
        
        # Проверить на реальном изображении из датасета
        test_image_path = Path("datasets/cigarette_butt/test/images")
        if test_image_path.exists():
            test_images = list(test_image_path.glob("*.jpg"))
            if test_images:
                print(f"\nТест на реальном изображении из датасета...")
                test_img_path = test_images[0]
                print(f"   Изображение: {test_img_path.name}")
                
                img = cv2.imread(str(test_img_path))
                if img is not None:
                    results = model(img, conf=0.3, verbose=False)
                    detections = results[0].boxes
                    print(f"   Найдено детекций: {len(detections)}")
                    
                    for i, box in enumerate(detections):
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        class_name = model.names[cls]
                        print(f"   Детекция {i+1}: {class_name} (уверенность: {conf:.3f})")
        
        print("\n" + "=" * 60)
        print("✅ Модель работает корректно!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Ошибка загрузки модели: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"❌ Модель не найдена: {model_path}")
    print(f"   Проверьте путь в config/config.yaml")

