"""
Тест детекции со всеми порогами одновременно
Показывает детекции на разных порогах разными цветами
"""

import cv2
import asyncio
import logging
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from ultralytics import YOLO
import numpy as np
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_all_thresholds(ip_address: str, port: int = 8080):
    """Тест со всеми порогами одновременно"""
    
    # Загрузка конфигурации
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Загрузка модели
    model_path = config.get("model", {}).get("weights_path", "models/cigarette_detector/best.pt")
    model = YOLO(model_path)
    logger.info(f"✅ Модель загружена: {model_path}")
    
    # Пороги для тестирования
    thresholds = [0.2, 0.3, 0.5]
    colors = [(0, 255, 0), (255, 255, 0), (0, 255, 255)]  # Зеленый, Желтый, Голубой
    
    # Подключение к потоку
    if ip_address == "0" or ip_address == "localhost":
        stream_url = 0
        logger.info("Использование локальной веб-камеры")
    else:
        stream_url = f"http://{ip_address}:{port}/video"
        logger.info(f"Подключение к IP Webcam: {stream_url}")
    
    cap = cv2.VideoCapture(stream_url)
    
    if not cap.isOpened():
        logger.error(f"❌ Не удалось подключиться к {stream_url}")
        return
    
    logger.info("✅ Подключение успешно")
    logger.info("=" * 60)
    logger.info("ТЕСТ СО ВСЕМИ ПОРОГАМИ")
    logger.info("=" * 60)
    logger.info("Зеленый = порог 0.2")
    logger.info("Желтый = порог 0.3")
    logger.info("Голубой = порог 0.5")
    logger.info("Нажмите 'q' для выхода")
    logger.info("=" * 60)
    
    frame_count = 0
    detections_by_threshold = {t: 0 for t in thresholds}
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Детекция со всеми порогами
            all_detections = {}
            for threshold in thresholds:
                results = model(frame, conf=threshold, verbose=False, imgsz=640)
                boxes = results[0].boxes
                all_detections[threshold] = boxes
                
                if len(boxes) > 0:
                    detections_by_threshold[threshold] += len(boxes)
            
            # Рисование детекций разными цветами
            for i, threshold in enumerate(thresholds):
                boxes = all_detections[threshold]
                color = colors[i]
                
                for box in boxes:
                    conf = float(box.conf[0])
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    # Рисовать только если это новый детект (не нарисован более низким порогом)
                    # Для простоты рисуем все, но разными цветами
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    label = f"conf={threshold} {conf:.2f}"
                    cv2.putText(frame, label, (int(x1), int(y1)-10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Статистика на кадре
            stats = f"Frame: {frame_count} | "
            for threshold in thresholds:
                count = detections_by_threshold[threshold]
                stats += f"T{threshold}:{count} "
            cv2.putText(frame, stats, (10, frame.shape[0] - 20),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Логирование каждые 50 кадров
            if frame_count % 50 == 0:
                logger.info(f"Кадр {frame_count}:")
                for threshold in thresholds:
                    count = len(all_detections[threshold])
                    total = detections_by_threshold[threshold]
                    logger.info(f"  Порог {threshold}: {count} на этом кадре, всего {total}")
            
            cv2.imshow('Multi-Threshold Detection - Press Q to exit', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    except KeyboardInterrupt:
        logger.info("Остановка по запросу пользователя")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        logger.info("\n" + "=" * 60)
        logger.info("ИТОГИ")
        logger.info("=" * 60)
        logger.info(f"Обработано кадров: {frame_count}")
        for threshold in thresholds:
            logger.info(f"Порог {threshold}: найдено {detections_by_threshold[threshold]} детекций")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Тест со всеми порогами")
    parser.add_argument("--ip", type=str, default="0", help="IP адрес или 0 для локальной камеры")
    parser.add_argument("--port", type=int, default=8080, help="Порт IP Webcam")
    
    args = parser.parse_args()
    
    test_all_thresholds(args.ip, args.port)

