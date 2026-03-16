"""
Тестирование детекции окурков на видеофайле
Сохраняет результаты: видео с bounding boxes, JSON статистику
"""

import cv2
import asyncio
import logging
import sys
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from edge.inference_service.detector import CigaretteDetector
from obelisk.services.active_learner import ActiveLearner
from obelisk.services.database import Database
from obelisk.services.mqtt_client import MQTTClient
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_output_paths(video_path: Path, output_dir: Path = None):
    """Получить пути для выходных файлов"""
    if output_dir is None:
        output_dir = Path("data/results")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    video_name = video_path.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    output_video = output_dir / f"{video_name}_detected_{timestamp}.mp4"
    output_json = output_dir / f"{video_name}_stats_{timestamp}.json"
    
    return output_video, output_json, output_dir


async def test_video_file(video_path: str, conf_threshold: float = 0.3, 
                         save_output: bool = True, show_video: bool = True,
                         enable_active_learning: bool = False):
    """
    Тестирование детекции на видеофайле
    
    Args:
        video_path: Путь к видеофайлу
        conf_threshold: Порог уверенности
        save_output: Сохранять ли результат
        show_video: Показывать ли видео во время обработки
    """
    video_path = Path(video_path)
    
    if not video_path.exists():
        logger.error(f"❌ Видеофайл не найден: {video_path}")
        return
    
    logger.info("=" * 60)
    logger.info("ТЕСТИРОВАНИЕ НА ВИДЕОФАЙЛЕ")
    logger.info("=" * 60)
    logger.info(f"Видео: {video_path}")
    logger.info(f"Порог уверенности: {conf_threshold}")
    logger.info("=" * 60)
    
    # Загрузка конфигурации
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Создание детектора
    detector = CigaretteDetector(config)
    detector.confidence_threshold = conf_threshold
    logger.info(f"✅ Модель загружена")
    
    # Инициализация активного обучения
    active_learner = None
    if enable_active_learning:
        logger.info("🧠 Инициализация активного обучения...")
        try:
            # Инициализация компонентов для активного обучения
            db = Database(config['database'])
            await db.init()
            
            mqtt_client = MQTTClient(config['mqtt_topics'], config['obelisk'])
            try:
                await mqtt_client.connect()
            except:
                logger.warning("MQTT недоступен, активное обучение продолжит без него")
            
            active_learner = ActiveLearner(config, db, mqtt_client)
            
            # Запуск цикла обучения в фоне
            learning_task = asyncio.create_task(active_learner.learning_loop())
            
            logger.info("✅ Активное обучение активировано - система будет учиться на видео")
        except Exception as e:
            logger.warning(f"Не удалось инициализировать активное обучение: {e}")
            logger.info("Продолжаем без активного обучения")
    
    # Открытие видео
    cap = cv2.VideoCapture(str(video_path))
    
    if not cap.isOpened():
        logger.error(f"❌ Не удалось открыть видео: {video_path}")
        return
    
    # Получение параметров видео
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0
    
    logger.info(f"Параметры видео:")
    logger.info(f"  Разрешение: {width}x{height}")
    logger.info(f"  FPS: {fps}")
    logger.info(f"  Кадров: {total_frames}")
    logger.info(f"  Длительность: {duration:.2f} сек")
    
    # Настройка записи выходного видео
    output_video_writer = None
    if save_output:
        output_video, output_json, output_dir = get_output_paths(video_path)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_video_writer = cv2.VideoWriter(
            str(output_video), fourcc, fps, (width, height)
        )
        logger.info(f"📹 Результат будет сохранен: {output_video}")
        logger.info(f"📊 Статистика будет сохранена: {output_json}")
    
    # Статистика
    all_detections: List[Dict] = []
    frames_with_detections = 0
    total_detections = 0
    confidences = []
    start_time = datetime.now()
    
    logger.info("\n" + "=" * 60)
    logger.info("ОБРАБОТКА ВИДЕО")
    logger.info("Нажмите 'q' для досрочной остановки")
    logger.info("=" * 60)
    
    frame_number = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.info("✅ Достигнут конец видео")
                break
            
            frame_number += 1
            
            # Детекция
            detections = await detector.detect_frame(frame, frame_id=f"frame_{frame_number}")
            
            # Активное обучение: передать детекции для анализа
            if active_learner and detections:
                for det in detections:
                    await active_learner.process_detection(det, frame)
            
            # Обновление статистики
            if len(detections) > 0:
                frames_with_detections += 1
                total_detections += len(detections)
                
                for det in detections:
                    confidences.append(det['confidence'])
                    all_detections.append({
                        "frame": frame_number,
                        "timestamp": frame_number / fps if fps > 0 else 0,
                        "bbox": det['bbox'],
                        "confidence": det['confidence'],
                        "class": det['class_name']
                    })
            
            # Рисование детекций
            for det in detections:
                x, y, w, h = det['bbox']
                conf = det['confidence']
                
                # Bounding box (зеленый)
                color = (0, 255, 0)
                cv2.rectangle(frame, (int(x), int(y)), (int(x+w), int(y+h)), color, 2)
                
                # Текст с уверенностью
                label = f"cig_butt {conf:.2f}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                cv2.rectangle(frame, (int(x), int(y) - label_size[1] - 10), 
                             (int(x) + label_size[0], int(y)), color, -1)
                cv2.putText(frame, label, (int(x), int(y) - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Статистика на кадре
            progress = (frame_number / total_frames * 100) if total_frames > 0 else 0
            stats_text = f"Frame: {frame_number}/{total_frames} ({progress:.1f}%) | Detections: {total_detections} | Frames w/ det: {frames_with_detections}"
            cv2.putText(frame, stats_text, (10, 30),
                      cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            # Показ видео
            if show_video:
                cv2.imshow('Video Detection - Press Q to stop', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    logger.info("⏹️ Остановка по запросу пользователя")
                    break
            
            # Сохранение кадра
            if output_video_writer:
                output_video_writer.write(frame)
            
            # Логирование прогресса
            if frame_number % 100 == 0:
                logger.info(f"Обработано: {frame_number}/{total_frames} кадров ({progress:.1f}%) | Найдено: {total_detections} детекций")
    
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка по прерыванию")
    finally:
        cap.release()
        if output_video_writer:
            output_video_writer.release()
        if show_video:
            cv2.destroyAllWindows()
        
        # Вычисление финальной статистики
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        min_confidence = min(confidences) if confidences else 0
        max_confidence = max(confidences) if confidences else 0
        
        # Сохранение статистики
        stats = {
            "video_file": str(video_path),
            "video_info": {
                "width": width,
                "height": height,
                "fps": fps,
                "total_frames": total_frames,
                "duration_seconds": duration
            },
            "detection_settings": {
                "confidence_threshold": conf_threshold,
                "model_path": config.get("model", {}).get("weights_path")
            },
            "results": {
                "total_frames_processed": frame_number,
                "frames_with_detections": frames_with_detections,
                "total_detections": total_detections,
                "detection_rate": frames_with_detections / frame_number if frame_number > 0 else 0,
                "avg_detections_per_frame": total_detections / frame_number if frame_number > 0 else 0
            },
            "confidence_stats": {
                "average": avg_confidence,
                "min": min_confidence,
                "max": max_confidence,
                "total_detections": len(confidences)
            },
            "processing": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "processing_time_seconds": processing_time,
                "frames_per_second": frame_number / processing_time if processing_time > 0 else 0
            },
            "detections": all_detections
        }
        
        if save_output:
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ Статистика сохранена: {output_json}")
        
        # Остановка активного обучения
        if active_learner:
            active_learner.stop()
            al_stats = active_learner.get_statistics()
            logger.info("\n" + "=" * 60)
            logger.info("СТАТИСТИКА АКТИВНОГО ОБУЧЕНИЯ")
            logger.info("=" * 60)
            logger.info(f"Собрано кадров: {al_stats['collected_frames']}")
            logger.info(f"Неопределенных кадров: {al_stats['uncertain_frames']}")
            logger.info(f"Автоматически размечено: {al_stats['auto_labeled_frames']}")
            logger.info(f"Раундов дообучения: {al_stats['retraining_count']}")
            logger.info("=" * 60)
        
        # Вывод итогов
        logger.info("\n" + "=" * 60)
        logger.info("ИТОГИ ТЕСТИРОВАНИЯ")
        logger.info("=" * 60)
        logger.info(f"Обработано кадров: {frame_number}/{total_frames}")
        logger.info(f"Кадров с детекциями: {frames_with_detections} ({frames_with_detections/frame_number*100:.1f}%)")
        logger.info(f"Всего найдено окурков: {total_detections}")
        logger.info(f"Средняя уверенность: {avg_confidence:.3f}")
        logger.info(f"Минимальная уверенность: {min_confidence:.3f}")
        logger.info(f"Максимальная уверенность: {max_confidence:.3f}")
        logger.info(f"Время обработки: {processing_time:.2f} сек")
        logger.info(f"Скорость: {frame_number/processing_time:.1f} FPS" if processing_time > 0 else "")
        if save_output:
            logger.info(f"Результат сохранен: {output_video}")
            logger.info(f"Статистика сохранена: {output_json}")
        logger.info("=" * 60)


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Тестирование детекции окурков на видеофайле",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  
  # Базовый тест
  python scripts\test_video_file.py "video.mp4"
  
  # С настройкой порога уверенности
  python scripts\test_video_file.py "video.mp4" --conf 0.3
  
  # Без сохранения результата (только просмотр)
  python scripts\test_video_file.py "video.mp4" --no-save
  
  # Без показа видео (быстрее, только обработка)
  python scripts\test_video_file.py "video.mp4" --no-show
  
  # Все опции
  python scripts\test_video_file.py "video.mp4" --conf 0.5 --output-dir "results"
        """
    )
    
    parser.add_argument("video", type=str, help="Путь к видеофайлу")
    parser.add_argument("--conf", type=float, default=0.3,
                       help="Порог уверенности (по умолчанию 0.3)")
    parser.add_argument("--output-dir", type=str, default=None,
                       help="Директория для сохранения результатов (по умолчанию data/results)")
    parser.add_argument("--no-save", action="store_true",
                       help="Не сохранять результат (только просмотр)")
    parser.add_argument("--no-show", action="store_true",
                       help="Не показывать видео во время обработки (быстрее)")
    parser.add_argument("--active-learning", action="store_true",
                       help="Включить активное обучение (система будет учиться на видео)")
    
    args = parser.parse_args()
    
    asyncio.run(test_video_file(
        video_path=args.video,
        conf_threshold=args.conf,
        save_output=not args.no_save,
        show_video=not args.no_show,
        enable_active_learning=args.active_learning
    ))


if __name__ == "__main__":
    main()

