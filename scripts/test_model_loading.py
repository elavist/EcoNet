"""
Тест загрузки модели для диагностики
"""

import sys
from pathlib import Path

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_model_loading():
    """Тест загрузки модели"""
    print("=" * 70)
    print("ТЕСТ ЗАГРУЗКИ МОДЕЛИ")
    print("=" * 70)
    
    # Загрузка конфигурации
    config_path = project_root / "config" / "config.yaml"
    print(f"\n1. Загрузка конфигурации: {config_path}")
    if not config_path.exists():
        print(f"❌ Конфигурация не найдена: {config_path}")
        return False
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    print("✅ Конфигурация загружена")
    
    # Проверка пути модели
    model_path = config.get("model", {}).get("weights_path", "models/cigarette_detector/best.pt")
    print(f"\n2. Проверка пути модели: {model_path}")
    
    # Проверка модели из config
    model_path_obj = Path(model_path) if Path(model_path).is_absolute() else project_root / model_path
    print(f"   Полный путь: {model_path_obj.absolute()}")
    print(f"   Существует: {model_path_obj.exists()}")
    print(f"   Расширение: {model_path_obj.suffix}")
    print(f"   Является .pt: {model_path_obj.suffix == '.pt'}")
    
    if not model_path_obj.exists():
        print(f"❌ Модель не найдена: {model_path_obj}")
        return False
    
    # Проверка модели из model_engine
    model_engine_config = config.get("model_engine", {}).get("models", [])
    print(f"\n3. Проверка моделей из model_engine: {len(model_engine_config)} моделей")
    
    for model_cfg in model_engine_config:
        if not model_cfg.get("enabled", True):
            print(f"   ⏭️  Модель {model_cfg.get('name')} отключена")
            continue
        
        model_name = model_cfg.get("name", "model")
        model_path_config = model_cfg.get("path")
        
        if not model_path_config:
            print(f"   ❌ Путь модели не указан для {model_name}")
            continue
        
        print(f"\n   Модель: {model_name}")
        print(f"   Путь: {model_path_config}")
        
        # Проверка существования модели
        model_path_obj_config = Path(model_path_config) if Path(model_path_config).is_absolute() else project_root / model_path_config
        print(f"   Полный путь: {model_path_obj_config.absolute()}")
        print(f"   Существует: {model_path_obj_config.exists()}")
        print(f"   Расширение: {model_path_obj_config.suffix}")
        print(f"   Является .pt: {model_path_obj_config.suffix == '.pt'}")
        
        if not model_path_obj_config.exists():
            print(f"   ❌ Модель {model_name} не найдена: {model_path_obj_config}")
            continue
        
        # Попытка загрузки модели
        print(f"\n4. Попытка загрузки модели {model_name}...")
        try:
            from ultralytics import YOLO
            print(f"   Загрузка YOLO модели: {model_path_obj_config}")
            model = YOLO(str(model_path_obj_config))
            print(f"   ✅ Модель {model_name} загружена успешно!")
            
            # Проверка устройства
            device = config.get("model_engine", {}).get("device", "cpu")
            print(f"   Устройство из конфига: {device}")
            
            if device != "cpu":
                try:
                    import torch
                    if torch.cuda.is_available():
                        print(f"   CUDA доступен: {torch.cuda.get_device_name(0)}")
                        model.to(device)
                        print(f"   ✅ Модель перемещена на {device}")
                    else:
                        print(f"   ⚠️ CUDA недоступен, используем CPU")
                except Exception as e:
                    print(f"   ⚠️ Ошибка при перемещении на GPU: {e}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Ошибка загрузки модели {model_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    print("\n❌ Не удалось загрузить ни одну модель")
    return False

if __name__ == "__main__":
    success = test_model_loading()
    sys.exit(0 if success else 1)

