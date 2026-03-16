"""
Проверка системы ЭкоНет
Проверяет наличие всех необходимых компонентов: модели, зависимости, конфигурация
"""

import sys
from pathlib import Path

# Добавление корня проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_model():
    """Проверка наличия модели"""
    print("\n[МОДЕЛЬ] Проверка модели...")
    
    model_path = project_root / "models" / "cigarette_detector" / "best.pt"
    onnx_path = project_root / "models" / "cigarette_detector" / "best.onnx"
    
    if model_path.exists():
        size = model_path.stat().st_size / (1024 * 1024)  # MB
        print(f"  [OK] Модель PT найдена: {model_path} ({size:.1f} MB)")
    else:
        print(f"  [ERROR] Модель PT не найдена: {model_path}")
    
    if onnx_path.exists():
        size = onnx_path.stat().st_size / (1024 * 1024)  # MB
        print(f"  [OK] Модель ONNX найдена: {onnx_path} ({size:.1f} MB)")
    else:
        print(f"  [WARN] Модель ONNX не найдена (опционально)")
    
    return model_path.exists() or onnx_path.exists()

def check_dependencies():
    """Проверка зависимостей"""
    print("\n[ЗАВИСИМОСТИ] Проверка зависимостей...")
    
    dependencies = {
        'ultralytics': 'YOLO',
        'cv2': 'OpenCV',
        'torch': 'PyTorch',
        'PIL': 'Pillow',
        'yaml': 'PyYAML',
        'fastapi': 'FastAPI',
        'paho.mqtt': 'MQTT',
    }
    
    all_ok = True
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"  [OK] {name}")
        except ImportError:
            print(f"  [ERROR] {name} не установлен")
            all_ok = False
    
    return all_ok

def check_config():
    """Проверка конфигурации"""
    print("\n[КОНФИГ] Проверка конфигурации...")
    
    config_path = project_root / "config" / "config.yaml"
    
    if config_path.exists():
        print(f"  [OK] Конфигурация найдена: {config_path}")
        return True
    else:
        print(f"  [ERROR] Конфигурация не найдена: {config_path}")
        return False

def check_dataset():
    """Проверка датасета"""
    print("\n[ДАТАСЕТ] Проверка датасета...")
    
    dataset_path = project_root / "datasets" / "cigarette_butt"
    
    if dataset_path.exists():
        train_path = dataset_path / "train" / "images"
        valid_path = dataset_path / "valid" / "images"
        
        train_count = len(list(train_path.glob("*.jpg"))) if train_path.exists() else 0
        valid_count = len(list(valid_path.glob("*.jpg"))) if valid_path.exists() else 0
        
        print(f"  [OK] Датасет найден")
        print(f"     Обучающих изображений: {train_count}")
        print(f"     Валидационных изображений: {valid_count}")
        return True
    else:
        print(f"  [WARN] Датасет не найден (опционально для обучения)")
        return False

def main():
    """Главная функция проверки"""
    print("="*70)
    print("ПРОВЕРКА СИСТЕМЫ ЭКОНЕТ")
    print("="*70)
    
    results = {
        'model': check_model(),
        'dependencies': check_dependencies(),
        'config': check_config(),
        'dataset': check_dataset(),
    }
    
    print("\n" + "="*70)
    print("РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
    print("="*70)
    
    for name, result in results.items():
        status = "[OK]" if result else "[ERROR]"
        print(f"  {name.upper()}: {status}")
    
    print("="*70)
    
    # Критические компоненты
    critical = results['model'] and results['dependencies'] and results['config']
    
    if critical:
        print("\n[OK] Система готова к работе!")
        return 0
    else:
        print("\n[ERROR] Обнаружены проблемы. Установите недостающие компоненты.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

