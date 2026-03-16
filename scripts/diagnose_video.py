"""
Диагностика проблемы с детекцией на видео
Показывает детальную информацию о том, что происходит
"""

import cv2
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from ultralytics import YOLO
import numpy as np

print("=" * 60)
print("ДИАГНОСТИКА ДЕТЕКЦИИ НА ВИДЕО")
print("=" * 60)

# Загрузка модели
model_path = "models/cigarette_detector/best.pt"
print(f"\n1. Загрузка модели: {model_path}")
model = YOLO(model_path)
print(f"   ✅ Модель загружена")
print(f"   Классы: {model.names}")

# Тест на статическом изображении
print(f"\n2. Тест на статическом изображении из датасета...")
test_image_path = Path("datasets/cigarette_butt/test/images")
if test_image_path.exists():
    test_images = list(test_image_path.glob("*.jpg"))
    if test_images:
        img_path = test_images[0]
        print(f"   Изображение: {img_path.name}")
        img = cv2.imread(str(img_path))
        
        # Тест с разными порогами
        for conf in [0.2, 0.3, 0.5]:
            results = model(img, conf=conf, verbose=False)
            detections = results[0].boxes
            print(f"   Порог {conf}: найдено {len(detections)} детекций")
            if len(detections) > 0:
                for i, box in enumerate(detections):
                    print(f"      Детекция {i+1}: уверенность {float(box.conf[0]):.3f}")

# Тест на видео потоке
print(f"\n3. Тест на видео потоке...")
print("   Введите источник видео:")
print("   - IP адрес телефона (например: 192.168.1.100)")
print("   - '0' для локальной камеры")
print("   - Путь к видео файлу")
source = input("   > ").strip()

if source == "0" or source.isdigit():
    source = int(source) if source.isdigit() else 0
    print(f"   Подключение к локальной камере...")
else:
    if not source.startswith("http") and not source.startswith("rtsp"):
        # Предполагаем IP адрес
        source = f"http://{source}:8080/video"
    print(f"   Подключение к: {source}")

cap = cv2.VideoCapture(source)

if not cap.isOpened():
    print(f"   ❌ Не удалось открыть поток: {source}")
    print("   Проверьте:")
    print("   - IP Webcam запущен на телефоне")
    print("   - Телефон и компьютер в одной Wi-Fi сети")
    print("   - IP адрес правильный")
    exit(1)

print(f"   ✅ Поток открыт")
print(f"   Разрешение: {int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")
print(f"   FPS: {cap.get(cv2.CAP_PROP_FPS)}")

# Обработка нескольких кадров
print(f"\n4. Обработка кадров (нажмите 'q' для выхода)...")
print("   Пороги уверенности: 0.2, 0.3, 0.5")
print("   Смотрите в консоль для деталей\n")

frame_count = 0
detection_count = 0

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("   ⚠️ Не удалось прочитать кадр")
            break
        
        frame_count += 1
        
        # Тест с разными порогами
        if frame_count % 30 == 0:  # Каждые 30 кадров
            print(f"\n   Кадр {frame_count}:")
            
            for conf_threshold in [0.2, 0.3, 0.5]:
                results = model(frame, conf=conf_threshold, verbose=False, imgsz=640)
                boxes = results[0].boxes
                
                if len(boxes) > 0:
                    print(f"      Порог {conf_threshold}: найдено {len(boxes)} детекций")
                    for i, box in enumerate(boxes):
                        conf = float(box.conf[0])
                        cls = int(box.cls[0])
                        class_name = model.names[cls]
                        print(f"         {i+1}. {class_name}: {conf:.3f}")
                    detection_count += len(boxes)
                else:
                    print(f"      Порог {conf_threshold}: детекций не найдено")
            
            # Показать статистику
            print(f"   Всего обработано кадров: {frame_count}")
            print(f"   Всего найдено детекций: {detection_count}")
        
        # Отображение с самым низким порогом
        results = model(frame, conf=0.2, verbose=False, imgsz=640)
        boxes = results[0].boxes
        
        # Рисование детекций
        for box in boxes:
            conf = float(box.conf[0])
            cls = int(box.cls[0])
            if cls == 1 or model.names[cls] == 'cig_butt':
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
                label = f"cig_butt {conf:.2f}"
                cv2.putText(frame, label, (int(x1), int(y1)-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Показать кадр
        cv2.imshow('Diagnostics - Press Q to exit', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\n   Остановка по запросу пользователя")

finally:
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\n" + "=" * 60)
    print("ИТОГИ ДИАГНОСТИКИ")
    print("=" * 60)
    print(f"Обработано кадров: {frame_count}")
    print(f"Найдено детекций: {detection_count}")
    
    if detection_count == 0:
        print("\n⚠️ Детекции не найдены!")
        print("Возможные причины:")
        print("1. Окурки слишком маленькие на видео")
        print("2. Плохое освещение")
        print("3. Угол съемки не подходит")
        print("4. Модель не обучена достаточно хорошо")
        print("\nРекомендации:")
        print("- Поднесите камеру ближе к окуркам")
        print("- Улучшите освещение")
        print("- Попробуйте переобучить модель")
    else:
        print(f"\n✅ Детекции найдены! Система работает.")

