"""
Скрипт для проверки что модель загружена на GPU
Проверяет что используется PT модель и она на GPU
"""

import torch
import yaml
from pathlib import Path
from ultralytics import YOLO


def check_gpu_model():
    """Проверка что модель загружена на GPU"""
    print("=" * 70)
    print("ПРОВЕРКА ЗАГРУЗКИ МОДЕЛИ НА GPU")
    print("=" * 70)
    
    # Загрузка конфигурации
    config_path = Path("config/config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Проверка GPU
    cuda_available = torch.cuda.is_available()
    print(f"\n✅ CUDA доступен: {cuda_available}")
    
    if cuda_available:
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"✅ GPU: {gpu_name} ({gpu_memory:.1f} GB)")
    else:
        print("❌ CUDA недоступен")
        return
    
    # Проверка модели
    model_path = config.get("model", {}).get("weights_path", "models/cigarette_detector/best.pt")
    model_path_obj = Path(model_path) if Path(model_path).is_absolute() else Path(__file__).parent.parent / model_path
    
    pt_path = model_path_obj
    onnx_path = model_path_obj.with_suffix('.onnx')
    
    print(f"\n📁 Модель:")
    print(f"   PT: {pt_path.exists()} ({pt_path})")
    print(f"   ONNX: {onnx_path.exists()} ({onnx_path})")
    
    # Загрузка модели
    if pt_path.exists():
        print(f"\n🚀 Загрузка PT модели: {pt_path}")
        model = YOLO(str(pt_path))
        
        # Проверка устройства
        device_config = config.get("model_engine", {}).get("device") or config.get("edge", {}).get("device", "cpu")
        print(f"   Устройство из конфига: {device_config}")
        
        if "cuda" in str(device_config).lower():
            device_id = int(device_config.split(':')[-1]) if ':' in str(device_config) else 0
            device = f"cuda:{device_id}"
            
            # Проверка что модель использует GPU
            try:
                # Создаем тестовое изображение
                import numpy as np
                test_image = np.zeros((640, 640, 3), dtype=np.uint8)
                
                # Инференс на GPU
                print(f"\n🧪 Тест инференса на GPU: {device}")
                results = model(test_image, device=device, verbose=False)
                
                # Проверка использования GPU
                if torch.cuda.is_available():
                    memory_allocated = torch.cuda.memory_allocated(device_id) / (1024**2)  # MB
                    memory_reserved = torch.cuda.memory_reserved(device_id) / (1024**2)  # MB
                    print(f"   ✅ Память GPU выделена: {memory_allocated:.2f} MB")
                    print(f"   ✅ Память GPU зарезервирована: {memory_reserved:.2f} MB")
                    
                    if memory_allocated > 0:
                        print(f"\n✅ МОДЕЛЬ РАБОТАЕТ НА GPU!")
                    else:
                        print(f"\n⚠️ МОДЕЛЬ НЕ ИСПОЛЬЗУЕТ GPU (память не выделена)")
                else:
                    print(f"\n❌ CUDA недоступен после загрузки модели")
                
            except Exception as e:
                print(f"   ❌ Ошибка теста GPU: {e}")
        else:
            print(f"\n⚠️ Устройство в конфиге не GPU: {device_config}")
    else:
        print(f"\n❌ PT модель не найдена: {pt_path}")
        if onnx_path.exists():
            print(f"   ⚠️ ONNX модель найдена: {onnx_path}")
            print(f"   💡 Рекомендация: Используйте PT модель для максимальной производительности на GPU")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    check_gpu_model()

