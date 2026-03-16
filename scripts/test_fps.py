"""
Тест FPS детектора
Показывает реальную скорость обработки
"""

import cv2
import asyncio
import time
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from edge.inference_service.detector import CigaretteDetector
import yaml


async def test_fps(source: str = "0", duration: int = 30, input_size: int = 640):
    """
    Тест FPS детектора
    
    Args:
        source: Источник видео (IP адрес, путь к файлу, или 0 для камеры)
        duration: Длительность теста в секундах
        input_size: Размер входного изображения (320/416/640)
    """
    print("=" * 70)
    print("ТЕСТ FPS ДЕТЕКТОРА")
    print("=" * 70)
    print(f"Источник: {source}")
    print(f"Длительность: {duration} секунд")
    print(f"Размер входного изображения: {input_size}")
    print("=" * 70)
    
    # Загрузка конфигурации
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Обновить размер входного изображения
    config["model"]["input_size"] = input_size
    
    # Создание детектора
    detector = CigaretteDetector(config)
    detector.input_size = input_size
    
    print(f"✅ Детектор создан")
    print(f"   Устройство: {detector.device}")
    print(f"   Размер: {input_size}x{input_size}")
    
    # Подключение к источнику
    if source == "0" or source.isdigit():
        stream_source = int(source) if source.isdigit() else 0
    elif Path(source).exists():
        stream_source = source
    else:
        stream_source = f"http://{source}:8080/video"
    
    cap = cv2.VideoCapture(stream_source)
    
    if not cap.isOpened():
        print(f"❌ Не удалось открыть источник: {stream_source}")
        return
    
    # Получить FPS источника
    source_fps = cap.get(cv2.CAP_PROP_FPS) or 30
    print(f"📹 Источник: {stream_source}")
    print(f"   FPS источника: {source_fps:.1f}")
    print(f"\n🚀 Начало теста...")
    print("=" * 70)
    
    frame_times = []
    inference_times = []
    frames_processed = 0
    detections_count = 0
    start_time = time.time()
    
    try:
        while True:
            elapsed = time.time() - start_time
            if elapsed >= duration:
                break
            
            ret, frame = cap.read()
            if not ret:
                break
            
            # Измерить время inference
            inference_start = time.time()
            detections = await detector.detect_frame(frame, frame_id=f"frame_{frames_processed}")
            inference_time = time.time() - inference_start
            
            frame_time = time.time()
            frame_times.append(frame_time)
            inference_times.append(inference_time)
            frames_processed += 1
            
            if detections:
                detections_count += len(detections)
            
            # Показывать прогресс каждую секунду
            if frames_processed % int(source_fps) == 0:
                current_fps = len(frame_times) / (frame_times[-1] - frame_times[0]) if len(frame_times) > 1 else 0
                avg_inference = sum(inference_times) / len(inference_times) if inference_times else 0
                theoretical_fps = 1.0 / avg_inference if avg_inference > 0 else 0
                print(f"  {int(elapsed)}s: {frames_processed} кадров | "
                      f"Текущий FPS: {current_fps:.1f} | "
                      f"Inference: {avg_inference*1000:.1f}ms ({theoretical_fps:.1f} FPS) | "
                      f"Детекций: {detections_count}")
    
    except KeyboardInterrupt:
        print("\n⏹️ Остановка по запросу пользователя")
    finally:
        cap.release()
        
        # Вычислить итоговую статистику
        total_time = time.time() - start_time
        avg_fps = frames_processed / total_time if total_time > 0 else 0
        
        if inference_times:
            avg_inference = sum(inference_times) / len(inference_times)
            min_inference = min(inference_times)
            max_inference = max(inference_times)
            theoretical_fps = 1.0 / avg_inference if avg_inference > 0 else 0
        else:
            avg_inference = min_inference = max_inference = theoretical_fps = 0
        
        print("\n" + "=" * 70)
        print("РЕЗУЛЬТАТЫ ТЕСТА FPS")
        print("=" * 70)
        print(f"Время теста: {total_time:.1f} секунд")
        print(f"Обработано кадров: {frames_processed}")
        print(f"Найдено детекций: {detections_count}")
        print()
        print(f"📊 ПРОИЗВОДИТЕЛЬНОСТЬ:")
        print(f"   Средний FPS: {avg_fps:.2f}")
        print(f"   Теоретический FPS (inference): {theoretical_fps:.2f}")
        print(f"   Среднее время inference: {avg_inference*1000:.2f} ms")
        print(f"   Минимальное время: {min_inference*1000:.2f} ms")
        print(f"   Максимальное время: {max_inference*1000:.2f} ms")
        print()
        
        # Рекомендации
        print("💡 РЕКОМЕНДАЦИИ:")
        if avg_inference > 50:  # Больше 50ms
            print(f"   ⚠️ Inference медленный ({avg_inference*1000:.1f}ms)")
            print(f"   💡 Попробуйте:")
            print(f"      - Уменьшить input_size: {input_size} -> 416 или 320")
            print(f"      - Использовать GPU: измените edge.device = 'cuda:0'")
            print(f"      - Экспортировать в ONNX: python scripts\\optimize_for_fps.py")
        elif theoretical_fps >= 30:
            print(f"   ✅ Отличная производительность! ({theoretical_fps:.1f} FPS)")
        else:
            print(f"   ⚠️ Можно улучшить:")
            print(f"      - Уменьшить input_size для большей скорости")
        
        print("=" * 70)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Тест FPS детектора")
    parser.add_argument("--source", type=str, default="0",
                       help="Источник: IP адрес, путь к видео, или 0 для камеры")
    parser.add_argument("--duration", type=int, default=30,
                       help="Длительность теста в секундах")
    parser.add_argument("--imgsz", type=int, default=640, choices=[320, 416, 640],
                       help="Размер входного изображения (320/416/640)")
    
    args = parser.parse_args()
    
    asyncio.run(test_fps(args.source, args.duration, args.imgsz))

