"""
Скрипт для запуска всей системы
"""

import asyncio
import subprocess
import sys
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def start_mqtt_broker():
    """Запуск MQTT брокера (если не в Docker)"""
    try:
        # Проверить, запущен ли mosquitto
        result = subprocess.run(["mosquitto", "-h"], capture_output=True, text=True)
        logger.info("Mosquitto найден в системе")
        
        # Запустить mosquitto в фоне
        subprocess.Popen(["mosquitto", "-c", "mosquitto/config/mosquitto.conf"])
        logger.info("MQTT брокер запущен")
    except FileNotFoundError:
        logger.warning("Mosquitto не найден. Используйте Docker: docker-compose up -d mosquitto")


def start_obelisk():
    """Запуск Обелиска"""
    logger.info("Запуск Обелиска...")
    obelisk_path = Path(__file__).parent.parent / "obelisk" / "api" / "main.py"
    subprocess.Popen([sys.executable, str(obelisk_path)])
    logger.info("Обелиск запущен на http://localhost:8000")


def start_detector(source="0"):
    """Запуск Edge Detector"""
    logger.info(f"Запуск Edge Detector (источник: {source})...")
    detector_path = Path(__file__).parent.parent / "edge" / "inference_service" / "detector.py"
    subprocess.Popen([sys.executable, str(detector_path), "--source", source])
    logger.info("Edge Detector запущен")


def start_robot(robot_id="collector_01"):
    """Запуск робота-сборщика"""
    logger.info(f"Запуск робота {robot_id}...")
    robot_path = Path(__file__).parent.parent / "robots" / "collector" / "collector_robot.py"
    subprocess.Popen([sys.executable, str(robot_path), "--robot-id", robot_id])
    logger.info(f"Робот {robot_id} запущен")


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Запуск системы SWARM CLEANER")
    parser.add_argument("--mqtt", action="store_true", help="Запустить MQTT брокер")
    parser.add_argument("--obelisk", action="store_true", help="Запустить Обелиск")
    parser.add_argument("--detector", action="store_true", help="Запустить Edge Detector")
    parser.add_argument("--robot", action="store_true", help="Запустить робота")
    parser.add_argument("--all", action="store_true", help="Запустить всё")
    parser.add_argument("--source", type=str, default="0", help="Источник видео для детектора")
    parser.add_argument("--robot-id", type=str, default="collector_01", help="ID робота")
    
    args = parser.parse_args()
    
    if args.all:
        args.mqtt = True
        args.obelisk = True
        args.detector = True
        args.robot = True
    
    print("=" * 60)
    print("SWARM CLEANER - Запуск системы")
    print("=" * 60)
    
    if args.mqtt:
        start_mqtt_broker()
        import time
        time.sleep(2)  # Дать время брокеру запуститься
    
    if args.obelisk:
        start_obelisk()
        import time
        time.sleep(3)  # Дать время Обелиску запуститься
    
    if args.detector:
        start_detector(args.source)
    
    if args.robot:
        start_robot(args.robot_id)
    
    print("=" * 60)
    print("Система запущена!")
    print("Обелиск API: http://localhost:8000")
    print("Документация API: http://localhost:8000/docs")
    print("=" * 60)
    print("Нажмите Ctrl+C для остановки")
    
    try:
        # Бесконечное ожидание
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка системы...")


if __name__ == "__main__":
    main()

