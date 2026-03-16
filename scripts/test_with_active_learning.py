"""
Тестирование с активным обучением
Система будет учиться во время просмотра видео
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from edge.inference_service.detector import CigaretteDetector
from obelisk.services.active_learner import ActiveLearner
from obelisk.services.database import Database
from obelisk.services.mqtt_client import MQTTClient
import yaml
import cv2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_with_active_learning(source: str, conf_threshold: float = 0.3):
    """
    Тестирование с активным обучением
    
    Args:
        source: Источник видео (IP адрес, путь к файлу, или 0 для камеры)
        conf_threshold: Порог уверенности
    """
    logger.info("=" * 70)
    logger.info("ТЕСТИРОВАНИЕ С АКТИВНЫМ ОБУЧЕНИЕМ")
    logger.info("🧠 'Зародыш интеллекта' активирован")
    logger.info("=" * 70)
    
    # Загрузка конфигурации
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Включить активное обучение если выключено
    if not config.get("active_learning", {}).get("enabled", False):
        config["active_learning"]["enabled"] = True
        logger.info("✅ Активное обучение включено в конфиге")
    
    # Инициализация компонентов
    logger.info("\nИнициализация компонентов...")
    
    # База данных
    db = Database(config['database'])
    await db.init()
    logger.info("✅ База данных инициализирована")
    
    # MQTT (опционально)
    mqtt_client = None
    try:
        mqtt_client = MQTTClient(config['mqtt_topics'], config['obelisk'])
        await mqtt_client.connect()
        logger.info("✅ MQTT подключен")
    except Exception as e:
        logger.warning(f"MQTT недоступен: {e}. Продолжаем без MQTT")
    
    # Активное обучение
    active_learner = ActiveLearner(config, db, mqtt_client)
    learning_task = asyncio.create_task(active_learner.learning_loop())
    logger.info("✅ Активное обучение запущено")
    
    # Детектор
    detector = CigaretteDetector(config)
    detector.confidence_threshold = conf_threshold
    logger.info("✅ Детектор готов")
    
    # Подключение к источнику
    if source == "0" or source.isdigit():
        stream_source = int(source) if source.isdigit() else 0
        logger.info("Использование локальной камеры")
    else:
        # Проверить, это файл или IP
        if Path(source).exists():
            stream_source = source
            logger.info(f"Видеофайл: {source}")
        else:
            # Предполагаем IP адрес
            stream_source = f"http://{source}:8080/video"
            logger.info(f"IP Webcam: {stream_source}")
    
    cap = cv2.VideoCapture(stream_source)
    
    if not cap.isOpened():
        logger.error(f"❌ Не удалось открыть источник: {stream_source}")
        return
    
    logger.info("✅ Источник открыт")
    logger.info("\n" + "=" * 70)
    logger.info("НАЧАЛО ОБРАБОТКИ")
    logger.info("Система будет:")
    logger.info("  1. Детектировать окурки в реальном времени")
    logger.info("  2. Собирать неопределенные кадры для обучения")
    logger.info("  3. Автоматически размечать и дообучать модель")
    logger.info("=" * 70)
    logger.info("Нажмите 'q' для выхода\n")
    
    frame_count = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            
            # Детекция
            detections = await detector.detect_frame(frame, frame_id=f"frame_{frame_count}")
            
            # Активное обучение
            if detections:
                for det in detections:
                    await active_learner.process_detection(det, frame)
            
            # Отображение
            for det in detections:
                x, y, w, h = det['bbox']
                conf = det['confidence']
                cv2.rectangle(frame, (int(x), int(y)), (int(x+w), int(y+h)), (0, 255, 0), 2)
                label = f"cig_butt {conf:.2f}"
                cv2.putText(frame, label, (int(x), int(y)-10),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Статистика на кадре
            al_stats = active_learner.get_statistics()
            stats_text = f"Frame: {frame_count} | Det: {len(detections)} | Collected: {al_stats['collected_frames']}"
            cv2.putText(frame, stats_text, (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            cv2.imshow('Active Learning - Press Q to exit', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            # Логирование каждые 100 кадров
            if frame_count % 100 == 0:
                logger.info(f"Кадр {frame_count}: детекций {len(detections)}, собрано {al_stats['collected_frames']} кадров")
    
    except KeyboardInterrupt:
        logger.info("Остановка по запросу пользователя")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # Остановка активного обучения
        active_learner.stop()
        learning_task.cancel()
        
        # Финальная статистика
        final_stats = active_learner.get_statistics()
        
        logger.info("\n" + "=" * 70)
        logger.info("ИТОГОВАЯ СТАТИСТИКА")
        logger.info("=" * 70)
        logger.info(f"Обработано кадров: {frame_count}")
        logger.info(f"Найдено детекций: {detector.detection_count}")
        logger.info(f"\n🧠 АКТИВНОЕ ОБУЧЕНИЕ:")
        logger.info(f"   Собрано кадров: {final_stats['collected_frames']}")
        logger.info(f"   Неопределенных кадров: {final_stats['uncertain_frames']}")
        logger.info(f"   Автоматически размечено: {final_stats['auto_labeled_frames']}")
        logger.info(f"   Раундов дообучения: {final_stats['retraining_count']}")
        logger.info("=" * 70)
        
        if final_stats['retraining_count'] > 0:
            logger.info("✅ Модель была дообучена во время просмотра!")
        
        await db.close()
        if mqtt_client:
            await mqtt_client.disconnect()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Тест с активным обучением")
    parser.add_argument("--source", type=str, default="0",
                       help="Источник: IP адрес, путь к видео, или 0 для камеры")
    parser.add_argument("--conf", type=float, default=0.3,
                       help="Порог уверенности")
    
    args = parser.parse_args()
    
    asyncio.run(test_with_active_learning(args.source, args.conf))

