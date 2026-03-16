"""
Пример использования детектора окурков
"""

import asyncio
import cv2
from pathlib import Path
import sys

# Добавить корень проекта в путь
sys.path.append(str(Path(__file__).parent.parent))

from edge.inference_service.detector import CigaretteDetector
import yaml


async def test_image_detection():
    """Тест детекции на изображении"""
    print("Тест детекции на изображении")
    print("=" * 60)
    
    # Загрузка конфигурации
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Создание детектора
    detector = CigaretteDetector(config)
    
    # Путь к тестовому изображению
    test_image = input("Введите путь к изображению (или нажмите Enter для использования камеры): ").strip()
    
    if not test_image:
        # Использовать камеру
        print("Запуск детекции с веб-камеры...")
        print("Нажмите 'q' для выхода")
        
        cap = cv2.VideoCapture(0)
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Детекция
                detections = await detector.detect_frame(frame)
                
                # Отображение результатов
                for det in detections:
                    x, y, w, h = det['bbox']
                    conf = det['confidence']
                    
                    # Рисование bounding box
                    cv2.rectangle(frame, (int(x), int(y)), (int(x+w), int(y+h)), (0, 255, 0), 2)
                    cv2.putText(frame, f"cig_butt {conf:.2f}", (int(x), int(y-10)),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Показать кадр
                cv2.imshow('Detection', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
        finally:
            cap.release()
            cv2.destroyAllWindows()
    else:
        # Обработка изображения
        if not Path(test_image).exists():
            print(f"Изображение не найдено: {test_image}")
            return
        
        detections = await detector.process_image(test_image)
        
        print(f"\nНайдено детекций: {len(detections)}")
        for i, det in enumerate(detections, 1):
            print(f"\nДетекция {i}:")
            print(f"  Класс: {det['class_name']}")
            print(f"  Уверенность: {det['confidence']:.4f}")
            print(f"  BBox: {det['bbox']}")
        
        # Загрузить и отобразить изображение с bounding boxes
        frame = cv2.imread(test_image)
        for det in detections:
            x, y, w, h = det['bbox']
            conf = det['confidence']
            
            cv2.rectangle(frame, (int(x), int(y)), (int(x+w), int(y+h)), (0, 255, 0), 2)
            cv2.putText(frame, f"cig_butt {conf:.2f}", (int(x), int(y-10)),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.imshow('Detection Result', frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


async def test_video_detection():
    """Тест детекции на видео"""
    print("Тест детекции на видео")
    print("=" * 60)
    
    # Загрузка конфигурации
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Создание детектора
    detector = CigaretteDetector(config)
    
    # Путь к видео
    video_path = input("Введите путь к видео (или нажмите Enter для использования камеры): ").strip()
    
    if not video_path:
        video_path = 0  # Камера
    
    # Запуск обработки потока
    await detector.process_stream(video_path, interval=0.1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Тест детектора окурков")
    parser.add_argument("--mode", choices=["image", "video"], default="image",
                       help="Режим тестирования: image или video")
    
    args = parser.parse_args()
    
    if args.mode == "image":
        asyncio.run(test_image_detection())
    else:
        asyncio.run(test_video_detection())

