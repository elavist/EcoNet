"""
Пример использования API Обелиска
"""

import requests
import json
from datetime import datetime


BASE_URL = "http://localhost:8000"


def test_health():
    """Проверка здоровья системы"""
    print("Проверка здоровья системы...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()


def test_create_detection():
    """Создание тестовой детекции"""
    print("Создание тестовой детекции...")
    
    detection = {
        "source": "test_camera",
        "bbox": [100, 100, 50, 50],  # x, y, width, height
        "class_name": "cig_butt",
        "confidence": 0.85,
        "frame_id": "test_frame_001",
        "location": [55.7558, 37.6173]  # Москва
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/detections/",
        json=detection
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Detection created: {json.dumps(response.json(), indent=2)}")
        return response.json()["id"]
    else:
        print(f"Error: {response.text}")
        return None


def test_get_detections():
    """Получение списка детекций"""
    print("Получение списка детекций...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/detections/",
        params={"limit": 10}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        detections = response.json()
        print(f"Found {len(detections)} detections")
        for det in detections[:3]:  # Показать первые 3
            print(f"  - {det['id']}: {det['class_name']} ({det['confidence']:.2f})")
    else:
        print(f"Error: {response.text}")
    print()


def test_create_task():
    """Создание задачи"""
    print("Создание задачи...")
    
    task = {
        "type": "collect",
        "target_bbox": [100, 100, 50, 50],
        "target_location": [0.0, 0.0],  # Относительные координаты
        "frame_id": "test_frame_001",
        "priority": 2,
        "timeout": 300
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/tasks/",
        json=task
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Task created: {json.dumps(response.json(), indent=2)}")
        return response.json()["task_id"]
    else:
        print(f"Error: {response.text}")
        return None


def test_get_tasks():
    """Получение списка задач"""
    print("Получение списка задач...")
    
    response = requests.get(
        f"{BASE_URL}/api/v1/tasks/",
        params={"limit": 10}
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        tasks = response.json()
        print(f"Found {len(tasks)} tasks")
        for task in tasks[:3]:  # Показать первые 3
            print(f"  - {task['task_id']}: {task['type']} ({task['status']})")
    else:
        print(f"Error: {response.text}")
    print()


def test_get_robots():
    """Получение списка роботов"""
    print("Получение списка роботов...")
    
    response = requests.get(f"{BASE_URL}/api/v1/robots/")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        robots = response.json()
        print(f"Found {len(robots)} robots")
        for robot in robots:
            print(f"  - {robot['robot_id']}: {robot['state']} (battery: {robot['battery']}%)")
    else:
        print(f"Error: {response.text}")
    print()


def test_get_models():
    """Получение списка моделей"""
    print("Получение списка моделей...")
    
    response = requests.get(f"{BASE_URL}/api/v1/models/")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        models = response.json()
        print(f"Found {len(models)} models")
        for model in models:
            print(f"  - {model['name']} v{model['version']}: mAP={model.get('mAP', 0):.4f}")
    else:
        print(f"Error: {response.text}")
    print()


def test_system_status():
    """Получение статуса системы"""
    print("Получение статуса системы...")
    
    response = requests.get(f"{BASE_URL}/api/v1/system/status")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        status = response.json()
        print(f"System Status: {status['status']}")
        print(f"Services: {json.dumps(status['services'], indent=2)}")
        print(f"Statistics: {json.dumps(status['statistics'], indent=2)}")
    else:
        print(f"Error: {response.text}")
    print()


def main():
    """Главная функция"""
    print("=" * 60)
    print("Тестирование API Обелиска")
    print("=" * 60)
    print()
    
    try:
        # Базовые проверки
        test_health()
        test_system_status()
        
        # Детекции
        test_create_detection()
        test_get_detections()
        
        # Задачи
        test_create_task()
        test_get_tasks()
        
        # Роботы
        test_get_robots()
        
        # Модели
        test_get_models()
        
        print("=" * 60)
        print("Тестирование завершено")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка: Не удалось подключиться к Обелиску")
        print("Убедитесь, что Обелиск запущен: python -m obelisk.api.main")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()

