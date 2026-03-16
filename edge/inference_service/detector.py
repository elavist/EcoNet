"""
Сервис детекции окурков с использованием YOLO
Публикует детекции в MQTT топик
"""

import cv2
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict
import json
import time
from datetime import datetime

from ultralytics import YOLO
import paho.mqtt.client as mqtt

# Импорт из корня проекта
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import yaml

logger = logging.getLogger(__name__)


class CigaretteDetector:
    """Детектор окурков на базе YOLO"""
    
    def __init__(self, config: Dict):
        """
        Инициализация детектора
        
        Args:
            config: Конфигурация системы
        """
        self.config = config
        self.model_config = config.get("model", {})
        self.mqtt_config = config.get("obelisk", {})
        
        # Загрузка модели - ПРИОРИТЕТ PT МОДЕЛИ (максимальная точность и производительность на GPU)
        # ONNX отключен - он теряет точность и не дообрабатывает кадры правильно
        model_path = self.model_config.get("weights_path", "models/cigarette_detector/best.pt")
        model_path_obj = Path(model_path) if Path(model_path).is_absolute() else Path(__file__).parent.parent.parent / model_path
        
        # ПРИОРИТЕТ PT МОДЕЛИ - лучшая точность и производительность на GPU
        if model_path_obj.exists() and model_path_obj.suffix == '.pt':
            self.model = YOLO(str(model_path_obj))
            logger.info(f"✅ PT модель загружена (максимальная точность): {model_path_obj}")
        elif model_path_obj.exists():
            # Если путь существует но не .pt, пробуем загрузить
            self.model = YOLO(str(model_path_obj))
            logger.info(f"✅ Модель загружена: {model_path_obj}")
        else:
            # Загрузить предобученную модель (PT только!)
            model_name = self.model_config.get("name", "yolov8n")
            self.model = YOLO(f"{model_name}.pt")
            logger.warning(f"Модель не найдена, используется предобученная PT модель: {model_name}.pt")
        
        # Параметры детекции
        self.confidence_threshold = self.model_config.get("confidence_threshold", 0.5)
        self.iou_threshold = self.model_config.get("iou_threshold", 0.45)
        self.input_size = self.model_config.get("input_size", 640)
        
        # Оптимизация производительности - принудительное использование GPU
        self.device = config.get("edge", {}).get("device", "cpu")
        if self.device and self.device != "cpu":
            try:
                import torch
                # Принудительное использование GPU
                if torch.cuda.is_available() and ("cuda" in str(self.device).lower() or "gpu" in str(self.device).lower()):
                    device_id = self.device.split(':')[-1] if ':' in str(self.device) else "0"
                    self.device = f"cuda:{device_id}"
                    
                    # Переместить модель на GPU
                    self.model.to(self.device)
                    
                    # Синхронизация GPU
                    torch.cuda.synchronize()
                    
                    gpu_name = torch.cuda.get_device_name(int(device_id))
                    logger.info(f"✅ Модель загружена на GPU: {gpu_name} ({self.device})")
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() and "mps" in str(self.device).lower():
                    self.device = "mps"
                    self.model.to(self.device)
                    logger.info(f"✅ Модель загружена на Apple MPS (Metal)")
                else:
                    logger.warning(f"⚠️ GPU запрошен в конфиге, но недоступен. Используется CPU.")
                    self.device = "cpu"
            except Exception as e:
                logger.warning(f"Не удалось загрузить на {self.device}: {e}")
                self.device = "cpu"
        else:
            logger.info("ℹ️ Используется CPU")
        
        # MQTT клиент
        self.mqtt_client = None
        self.source_id = f"detector_{int(time.time())}"
        
        # Статистика
        self.detection_count = 0
        self.frame_count = 0
    
    async def initialize_mqtt(self):
        """Инициализация MQTT клиента"""
        self.mqtt_client = mqtt.Client(client_id=self.source_id)
        
        if self.mqtt_config.get("mqtt_username"):
            self.mqtt_client.username_pw_set(
                self.mqtt_config["mqtt_username"],
                self.mqtt_config.get("mqtt_password")
            )
        
        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                logger.info("✅ Подключен к MQTT брокеру")
            else:
                logger.error(f"❌ Ошибка подключения MQTT: {rc}")
        
        def on_disconnect(client, userdata, rc):
            logger.warning("Отключен от MQTT брокера")
        
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_disconnect = on_disconnect
        
        host = self.mqtt_config["mqtt_broker"]
        port = self.mqtt_config["mqtt_port"]
        self.mqtt_client.connect_async(host, port, 60)
        self.mqtt_client.loop_start()
        
        # Ждем подключения
        await asyncio.sleep(1)
    
    async def detect_frame(self, frame: cv2.Mat, frame_id: Optional[str] = None) -> List[Dict]:
        """
        Детекция окурков на кадре
        
        Args:
            frame: Кадр изображения (OpenCV format)
            frame_id: ID кадра (опционально)
            
        Returns:
            Список детекций
        """
        self.frame_count += 1
        
        # Инференс с оптимизацией для GPU
        inference_kwargs = {
            "imgsz": self.input_size,
            "conf": self.confidence_threshold,
            "iou": self.iou_threshold,
            "verbose": False,
            "device": self.device if hasattr(self, 'device') and self.device != "cpu" else None
        }
        
        # Используем FP32 для совместимости (FP16 отключен)
        inference_kwargs["half"] = False  # FP32 для совместимости
        
        results = self.model(frame, **inference_kwargs)
        
        # Синхронизация GPU после инференса
        if hasattr(self, 'device') and self.device != "cpu":
            try:
                import torch
                if torch.cuda.is_available() and "cuda" in self.device:
                    torch.cuda.synchronize()
            except Exception:
                pass
        
        # Логирование для отладки (каждые 100 кадров)
        if self.frame_count % 100 == 0:
            total_boxes = sum(len(r.boxes) for r in results)
            if total_boxes > 0:
                logger.info(f"Кадр {self.frame_count}: модель нашла {total_boxes} боксов (порог: {self.confidence_threshold})")
        
        detections = []
        
        for result in results:
            boxes = result.boxes
            
            # Логирование всех найденных боксов для отладки
            if len(boxes) > 0:
                logger.debug(f"Найдено {len(boxes)} боксов на кадре {self.frame_count}")
            
            for box in boxes:
                # Для GPU данные могут быть на GPU, перемещаем на CPU для обработки
                if hasattr(self, 'device') and self.device != "cpu":
                    conf = float(box.conf[0].cpu().item())
                    cls = int(box.cls[0].cpu().item())
                    x1, y1, x2, y2 = box.xyxy[0].cpu().tolist()
                else:
                    conf = float(box.conf[0].item())
                    cls = int(box.cls[0].item())
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                
                # Получить имя класса
                class_name = result.names.get(cls, f"class_{cls}")
                
                # Логирование всех детекций для отладки
                logger.debug(f"Детекция: класс={cls} ({class_name}), уверенность={conf:.3f}")
                
                # Фильтр: принимаем все детекции как окурки
                # В датасете есть классы 0 и 1, оба могут быть окурками
                # Принимаем все детекции с достаточной уверенностью
                # (модель обучена только на окурках, поэтому все детекции = окурки)
                is_cigarette_butt = True  # Принимаем все детекции как окурки
                
                if is_cigarette_butt:
                    detection = {
                        "source": self.source_id,
                        "timestamp": datetime.utcnow().isoformat(),
                        "bbox": [x1, y1, x2 - x1, y2 - y1],  # x, y, width, height
                        "class_name": "cig_butt",
                        "confidence": conf,
                        "frame_id": frame_id or f"frame_{self.frame_count}",
                        "location": None  # TODO: добавить геолокацию
                    }
                    
                    detections.append(detection)
                    self.detection_count += 1
                    
                    logger.info(f"✅ Найден окурок: уверенность {conf:.3f}, bbox [{x1:.0f}, {y1:.0f}, {x2-x1:.0f}, {y2-y1:.0f}]")
                    
                    # Опубликовать в MQTT
                    if self.mqtt_client and self.mqtt_client.is_connected():
                        topic = self.config["mqtt_topics"]["detection"]
                        detection_id = f"det_{int(time.time())}_{self.detection_count}"
                        detection["id"] = detection_id
                        
                        self.mqtt_client.publish(topic, json.dumps(detection))
                        logger.debug(f"Детекция опубликована в MQTT: confidence={conf:.2f}")
                else:
                    # Логируем пропущенные детекции только если уверенность низкая
                    if conf >= 0.3:  # Только если уверенность выше 0.3
                        logger.debug(f"Пропущена детекция класса {cls} ({class_name}) с уверенностью {conf:.3f}")
        
        return detections
    
    async def process_stream(self, stream_source: str, interval: float = 0.1, active_learner=None):
        """
        Обработка видеопотока
        
        Args:
            stream_source: Источник потока (RTSP URL, путь к файлу, или номер камеры)
            interval: Интервал между обработкой кадров (секунды)
            active_learner: Активный обучатель для сбора данных (опционально)
        """
        cap = cv2.VideoCapture(stream_source)
        
        if not cap.isOpened():
            logger.error(f"Не удалось открыть поток: {stream_source}")
            return
        
        logger.info(f"Обработка потока: {stream_source}")
        if active_learner:
            logger.info("🧠 Активное обучение включено - система будет учиться во время просмотра")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Не удалось прочитать кадр")
                    await asyncio.sleep(1)
                    continue
                
                # Детекция
                detections = await self.detect_frame(frame)
                
                # Активное обучение: передать детекции и кадр для анализа
                if active_learner and detections:
                    for det in detections:
                        await active_learner.process_detection(det, frame)
                
                # Вывести статистику
                if self.frame_count % 100 == 0:
                    logger.info(f"Обработано кадров: {self.frame_count}, детекций: {self.detection_count}")
                    if active_learner:
                        stats = active_learner.get_statistics()
                        logger.info(f"🧠 Активное обучение: собрано {stats['collected_frames']} кадров")
                
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Остановка обработки потока")
        finally:
            cap.release()
    
    async def process_image(self, image_path: str) -> List[Dict]:
        """
        Обработка одиночного изображения
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Список детекций
        """
        frame = cv2.imread(image_path)
        if frame is None:
            logger.error(f"Не удалось загрузить изображение: {image_path}")
            return []
        
        detections = await self.detect_frame(frame, frame_id=Path(image_path).name)
        return detections
    
    def get_statistics(self) -> Dict:
        """Получить статистику детектора"""
        return {
            "frames_processed": self.frame_count,
            "detections_count": self.detection_count,
            "source_id": self.source_id,
            "mqtt_connected": self.mqtt_client.is_connected() if self.mqtt_client else False
        }


async def main():
    """Главная функция для запуска детектора"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cigarette Detector Service")
    parser.add_argument("--source", type=str, default="0", help="Источник видео (RTSP URL, файл, или номер камеры)")
    parser.add_argument("--config", type=str, default="config/config.yaml", help="Путь к конфигурации")
    args = parser.parse_args()
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Загрузка конфигурации
    if Path(args.config).is_absolute():
        config_path = Path(args.config)
    else:
        config_path = project_root / args.config
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Создание детектора
    detector = CigaretteDetector(config)
    
    # Инициализация MQTT
    await detector.initialize_mqtt()
    
    # Обработка потока
    if args.source.isdigit():
        source = int(args.source)
    else:
        source = args.source
    
    await detector.process_stream(source, interval=config.get("edge", {}).get("inference_interval", 0.1))


if __name__ == "__main__":
    asyncio.run(main())


