"""
Быстрый тест системы с IP Webcam (телефон)
Подключается к IP Webcam и показывает детекции в реальном времени
"""

import cv2
import asyncio
import logging
import sys
from pathlib import Path
import argparse

# Добавить корень проекта в путь
sys.path.append(str(Path(__file__).parent.parent))

from edge.inference_service.detector import CigaretteDetector
import yaml

# Настройка логирования (более подробное для отладки)
logging.basicConfig(
    level=logging.DEBUG,  # DEBUG для детальной информации
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_ip_webcam_url(ip_address: str, port: int = 8080, use_mjpeg: bool = True) -> str:
    """
    Получить URL для IP Webcam
    
    Args:
        ip_address: IP адрес телефона (например, "192.168.1.100")
        port: Порт IP Webcam (по умолчанию 8080)
        use_mjpeg: Использовать MJPEG (True) или RTSP (False)
    
    Returns:
        URL потока
    """
    if use_mjpeg:
        # HTTP MJPEG поток (обычно работает надежнее)
        return f"http://{ip_address}:{port}/video"
    else:
        # RTSP поток (нужна специальная настройка в IP Webcam)
        return f"rtsp://{ip_address}:8086/h264_pcm.sdp"


async def test_with_ip_webcam(ip_address: str, port: int = 8080, show_video: bool = True, 
                              conf_threshold: float = None, enable_active_learning: bool = False):
    """
    Тестирование детектора с IP Webcam
    
    Args:
        ip_address: IP адрес телефона
        port: Порт IP Webcam
        show_video: Показывать видео с детекциями
    """
    print("=" * 60)
    print("Тест детекции окурков с IP Webcam")
    print("=" * 60)
    
    # Загрузка конфигурации
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Создание детектора
    detector = CigaretteDetector(config)
    
    # Установить порог уверенности если указан
    if conf_threshold is not None:
        detector.confidence_threshold = conf_threshold
        logger.info(f"Порог уверенности установлен вручную: {conf_threshold}")
    
    logger.info(f"Порог уверенности: {detector.confidence_threshold}")
    logger.info(f"Размер входного изображения: {detector.input_size}")
    
    # Инициализация активного обучения
    active_learner = None
    if enable_active_learning:
        logger.info("🧠 Инициализация активного обучения...")
        try:
            from obelisk.services.active_learner import ActiveLearner
            from obelisk.services.database import Database
            from obelisk.services.mqtt_client import MQTTClient
            
            db = Database(config['database'])
            await db.init()
            
            mqtt_client = MQTTClient(config['mqtt_topics'], config['obelisk'])
            try:
                await mqtt_client.connect()
            except:
                logger.warning("MQTT недоступен, активное обучение продолжит без него")
            
            active_learner = ActiveLearner(config, db, mqtt_client)
            learning_task = asyncio.create_task(active_learner.learning_loop())
            logger.info("✅ Активное обучение активировано - система будет учиться на видео")
        except Exception as e:
            logger.warning(f"Не удалось инициализировать активное обучение: {e}")
            logger.info("Продолжаем без активного обучения")
    
    # Инициализация MQTT (опционально, если нужна отправка детекций)
    try:
        await detector.initialize_mqtt()
        mqtt_available = True
    except Exception as e:
        logger.warning(f"MQTT недоступен: {e}. Продолжаем без MQTT")
        mqtt_available = False
    
    # Специальная обработка для локальной камеры
    if ip_address == "0" or ip_address == "localhost":
        stream_url = int(ip_address) if ip_address.isdigit() else 0
        logger.info("Использование локальной веб-камеры")
    else:
        # Получить URL потока
        stream_url = get_ip_webcam_url(ip_address, port, use_mjpeg=True)
        logger.info(f"Подключение к IP Webcam: {stream_url}")
    
    # Попробовать подключиться
    if isinstance(stream_url, str):
        cap = cv2.VideoCapture(stream_url)
    else:
        cap = cv2.VideoCapture(stream_url)
    
    if not cap.isOpened():
        logger.error(f"❌ Не удалось подключиться к {stream_url}")
        logger.info("💡 Проверьте:")
        logger.info("   1. IP Webcam запущен на телефоне")
        logger.info("   2. Телефон и компьютер в одной Wi-Fi сети")
        logger.info("   3. IP адрес правильный")
        logger.info("   4. В IP Webcam включен 'Start server'")
        
        # Попробовать RTSP
        rtsp_url = get_ip_webcam_url(ip_address, 8086, use_mjpeg=False)
        logger.info(f"\nПопытка подключения через RTSP: {rtsp_url}")
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            logger.error("❌ RTSP тоже не работает")
            return
        
        stream_url = rtsp_url
        logger.info("✅ Подключение через RTSP успешно")
    else:
        logger.info("✅ Подключение к IP Webcam успешно")
    
    # Настройки отображения
    frame_count = 0
    detection_count = 0
    fps_start_time = cv2.getTickCount()
    fps_counter = 0
    
    print("\n" + "=" * 60)
    print("Детекция запущена! Нажмите 'q' для выхода")
    print("=" * 60)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Не удалось прочитать кадр. Повторная попытка...")
                await asyncio.sleep(1)
                continue
            
            # Детекция
            detections = await detector.detect_frame(frame, frame_id=f"frame_{frame_count}")
            
            # Активное обучение: передать детекции для анализа
            if active_learner and detections:
                for det in detections:
                    await active_learner.process_detection(det, frame)
            
            # Отладочная информация (каждые 10 кадров или при обнаружении)
            if len(detections) > 0:
                logger.info(f"🎯 Кадр {frame_count}: найдено {len(detections)} окурков!")
                for det in detections:
                    logger.info(f"   ✅ Окурок: уверенность {det['confidence']:.3f}, bbox {det['bbox']}")
            elif frame_count % 50 == 0:
                logger.debug(f"Кадр {frame_count}: детекций не найдено (порог: {detector.confidence_threshold})")
            
            # Отображение результатов
            if show_video:
                # Рисование детекций
                for det in detections:
                    x, y, w, h = det['bbox']
                    conf = det['confidence']
                    class_name = det['class_name']
                    
                    # Bounding box (зеленый для окурков)
                    color = (0, 255, 0) if class_name == 'cig_butt' else (255, 0, 0)
                    cv2.rectangle(frame, (int(x), int(y)), (int(x+w), int(y+h)), color, 2)
                    
                    # Текст с уверенностью
                    label = f"{class_name} {conf:.2f}"
                    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                    cv2.rectangle(frame, (int(x), int(y) - label_size[1] - 10), 
                                 (int(x) + label_size[0], int(y)), color, -1)
                    cv2.putText(frame, label, (int(x), int(y) - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    detection_count += 1
                
                # FPS
                fps_counter += 1
                if fps_counter % 30 == 0:
                    fps_end_time = cv2.getTickCount()
                    fps = 30 / ((fps_end_time - fps_start_time) / cv2.getTickFrequency())
                    fps_start_time = fps_end_time
                    logger.info(f"FPS: {fps:.1f} | Кадров: {frame_count} | Детекций: {detection_count}")
                
                # Статистика на кадре
                stats_text = f"Frames: {frame_count} | Detections: {detection_count} | Conf: {detector.confidence_threshold}"
                cv2.putText(frame, stats_text, (10, 30),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                # Предупреждение если детекций нет долго
                if frame_count > 100 and detection_count == 0:
                    warning_text = "No detections! Try lower --conf threshold"
                    cv2.putText(frame, warning_text, (10, 60),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # Статистика активного обучения
                if active_learner:
                    al_stats = active_learner.get_statistics()
                    al_text = f"Active Learning: {al_stats['collected_frames']} collected, {al_stats['retraining_count']} retrains"
                    cv2.putText(frame, al_text, (10, frame.shape[0] - 30),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                
                # Показать кадр
                cv2.imshow('SWARM CLEANER - Детекция окурков', frame)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            frame_count += 1
            
            # Логирование каждые 100 кадров
            if frame_count % 100 == 0:
                logger.info(f"Обработано кадров: {frame_count}, найдено детекций: {detection_count}")
    
    except KeyboardInterrupt:
        logger.info("Остановка по запросу пользователя")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # Остановка активного обучения
        if active_learner:
            active_learner.stop()
            al_stats = active_learner.get_statistics()
            logger.info("\n" + "=" * 60)
            logger.info("СТАТИСТИКА АКТИВНОГО ОБУЧЕНИЯ")
            logger.info("=" * 60)
            logger.info(f"Собрано кадров: {al_stats['collected_frames']}")
            logger.info(f"Автоматически размечено: {al_stats['auto_labeled_frames']}")
            logger.info(f"Раундов дообучения: {al_stats['retraining_count']}")
            logger.info("=" * 60)
        
        logger.info(f"\nИтоги: обработано {frame_count} кадров, найдено {detection_count} детекций")


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="Тест детекции окурков с IP Webcam",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  
  # Использование локальной веб-камеры
  python scripts/test_with_webcam.py --ip 0
  
  # Подключение к IP Webcam на 192.168.1.100
  python scripts/test_with_webcam.py --ip 192.168.1.100
  
  # С нестандартным портом
  python scripts/test_with_webcam.py --ip 192.168.1.100 --port 8080
  
  # Без отображения видео (только логи)
  python scripts/test_with_webcam.py --ip 192.168.1.100 --no-video

Как найти IP адрес телефона:
  1. Запустите IP Webcam на телефоне
  2. Нажмите "Start server"
  3. IP адрес отобразится в приложении (например: 192.168.1.100:8080)
  4. Используйте этот IP в команде выше (только IP, без порта)
        """
    )
    
    parser.add_argument("--ip", type=str, default="0",
                       help="IP адрес телефона с IP Webcam (например, 192.168.1.100) или '0' для локальной камеры")
    parser.add_argument("--port", type=int, default=8080,
                       help="Порт IP Webcam (по умолчанию 8080)")
    parser.add_argument("--no-video", action="store_true",
                       help="Не показывать видео (только логи)")
    parser.add_argument("--conf", type=float, default=None,
                       help="Порог уверенности (по умолчанию из конфига)")
    parser.add_argument("--active-learning", action="store_true",
                       help="Включить активное обучение (система будет учиться на видео)")
    
    args = parser.parse_args()
    
    asyncio.run(test_with_ip_webcam(args.ip, args.port, show_video=not args.no_video, 
                                   conf_threshold=args.conf, enable_active_learning=args.active_learning))


if __name__ == "__main__":
    main()

