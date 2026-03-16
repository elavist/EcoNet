"""
Комплексная проверка системы перед обучением модели на GPU
Проверяет готовность к обучению новой модели с нуля
"""

import sys
import os
from pathlib import Path
import yaml
import io

# Настройка кодировки для корректного вывода
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def print_header(text):
    """Печать заголовка"""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)

def print_section(text):
    """Печать секции"""
    print(f"\n{'-' * 70}")
    print(f"  {text}")
    print(f"{'-' * 70}")

def check_result(condition, ok_msg, fail_msg):
    """Проверка результата"""
    if condition:
        print(f"  [OK] {ok_msg}")
        return True
    else:
        print(f"  [FAIL] {fail_msg}")
        return False

def check_gpu():
    """Проверка доступности GPU"""
    print_section("Проверка GPU")
    
    results = []
    
    try:
        import torch
        
        # Проверка CUDA доступности
        cuda_available = torch.cuda.is_available()
        results.append(check_result(
            cuda_available,
            "CUDA доступен",
            "CUDA недоступен - проверьте установку PyTorch с CUDA поддержкой"
        ))
        
        if cuda_available:
            # Информация о GPU
            gpu_count = torch.cuda.device_count()
            print(f"  [INFO] Количество GPU: {gpu_count}")
            
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                props = torch.cuda.get_device_properties(i)
                memory_gb = props.total_memory / (1024**3)
                print(f"  [INFO] GPU {i}: {gpu_name}")
                print(f"  [INFO]   Память: {memory_gb:.1f} GB")
            
            # Проверка текущего устройства
            current_device = torch.cuda.current_device()
            print(f"  [INFO] Текущее устройство: cuda:{current_device}")
            
            # Тест выделения памяти на GPU
            try:
                test_tensor = torch.zeros(1000, 1000, device='cuda')
                del test_tensor
                torch.cuda.empty_cache()
                results.append(check_result(
                    True,
                    "GPU память доступна для операций",
                    "Ошибка выделения памяти на GPU"
                ))
            except Exception as e:
                results.append(check_result(
                    False,
                    "",
                    f"Ошибка выделения памяти на GPU: {e}"
                ))
        else:
            print("  [WARN] GPU недоступен - обучение будет выполняться на CPU (медленно!)")
            
    except ImportError:
        results.append(check_result(
            False,
            "",
            "PyTorch не установлен - установите: pip install torch torchvision"
        ))
    
    return all(results)

def check_dependencies():
    """Проверка зависимостей"""
    print_section("Проверка зависимостей")
    
    results = []
    required_packages = {
        'torch': 'PyTorch',
        'torchvision': 'TorchVision',
        'ultralytics': 'Ultralytics YOLO',
        'onnxruntime': 'ONNX Runtime',
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'yaml': 'PyYAML',
    }
    
    for package, name in required_packages.items():
        try:
            if package == 'cv2':
                import cv2
            elif package == 'yaml':
                import yaml
            else:
                __import__(package)
            results.append(check_result(True, f"{name} установлен", f"{name} не установлен"))
        except ImportError:
            results.append(check_result(False, "", f"{name} не установлен"))
    
    # Проверка ONNX Runtime GPU
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        has_cuda_provider = 'CUDAExecutionProvider' in providers
        results.append(check_result(
            has_cuda_provider or True,  # Не критично, но желательно
            f"ONNX Runtime GPU provider доступен: {has_cuda_provider}",
            f"ONNX Runtime GPU provider недоступен (для ONNX моделей будет использоваться CPU)"
        ))
        if has_cuda_provider:
            print(f"  [INFO] Доступные ONNX providers: {providers}")
    except ImportError:
        results.append(check_result(
            False,
            "",
            "onnxruntime не установлен - установите: pip install onnxruntime-gpu"
        ))
    
    return all(results)

def check_dataset():
    """Проверка датасета"""
    print_section("Проверка датасета")
    
    results = []
    dataset_path = Path("datasets/cigarette_butt")
    
    if not dataset_path.exists():
        results.append(check_result(
            False,
            "",
            f"Датасет не найден: {dataset_path}"
        ))
        return False
    
    print(f"  [INFO] Путь к датасету: {dataset_path}")
    
    # Проверка структуры датасета
    splits = ["train", "valid", "test"]
    total_images = 0
    total_labels = 0
    total_segments = 0
    
    for split in splits:
        images_path = dataset_path / split / "images"
        labels_path = dataset_path / split / "labels"
        
        if not images_path.exists():
            results.append(check_result(
                False,
                "",
                f"{split}/images не найден"
            ))
            continue
        
        if not labels_path.exists():
            results.append(check_result(
                False,
                "",
                f"{split}/labels не найден"
            ))
            continue
        
        # Подсчет файлов
        image_files = list(images_path.glob("*.jpg")) + list(images_path.glob("*.png"))
        label_files = list(labels_path.glob("*.txt"))
        
        split_images = len(image_files)
        split_labels = len(label_files)
        total_images += split_images
        total_labels += split_labels
        
        # Проверка наличия сегментов (полигонов)
        segments_count = 0
        for label_file in label_files[:100]:  # Проверяем первые 100 файлов
            try:
                with open(label_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) > 5:  # Сегмент имеет более 5 значений (class + координаты)
                            segments_count += 1
                            break
            except Exception:
                pass
        
        if segments_count > 0:
            total_segments += segments_count
            print(f"  [WARN] {split}: найдены файлы с сегментами (полигоны) - нужно конвертировать в боксы")
            print(f"         Запустите: python scripts\\convert_segments_to_boxes.py")
        
        results.append(check_result(
            split_images > 0 and split_labels > 0,
            f"{split}: {split_images} изображений, {split_labels} аннотаций",
            f"{split}: отсутствуют изображения или аннотации"
        ))
        
        # Проверка соответствия количества
        if split_images != split_labels:
            print(f"  [WARN] {split}: несоответствие количества изображений ({split_images}) и аннотаций ({split_labels})")
    
    print(f"  [INFO] Всего изображений: {total_images}")
    print(f"  [INFO] Всего аннотаций: {total_labels}")
    
    if total_segments > 0:
        results.append(check_result(
            False,
            "",
            f"Найдены сегменты (полигоны) в датасете - требуется конвертация в боксы"
        ))
    
    # Проверка data.yaml
    data_yaml = dataset_path / "data.yaml"
    if data_yaml.exists():
        try:
            with open(data_yaml, 'r', encoding='utf-8') as f:
                data_config = yaml.safe_load(f)
                print(f"  [INFO] Классов: {data_config.get('nc', 'N/A')}")
                print(f"  [INFO] Имена классов: {data_config.get('names', [])}")
                results.append(check_result(True, "data.yaml корректен", "data.yaml некорректен"))
        except Exception as e:
            results.append(check_result(False, "", f"Ошибка чтения data.yaml: {e}"))
    else:
        results.append(check_result(False, "", "data.yaml не найден"))
    
    return all(results)

def check_config():
    """Проверка конфигурации"""
    print_section("Проверка конфигурации")
    
    results = []
    config_path = Path("config/config.yaml")
    
    if not config_path.exists():
        results.append(check_result(False, "", "config.yaml не найден"))
        return False
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Проверка GPU настроек
        edge_device = config.get("edge", {}).get("device", "cpu")
        model_engine_device = config.get("model_engine", {}).get("device", "cpu")
        
        print(f"  [INFO] edge.device: {edge_device}")
        print(f"  [INFO] model_engine.device: {model_engine_device}")
        
        has_gpu_config = "cuda" in str(edge_device).lower() or "cuda" in str(model_engine_device).lower()
        
        results.append(check_result(
            True,
            "Конфигурация загружена",
            "Ошибка загрузки конфигурации"
        ))
        
        if has_gpu_config:
            print(f"  [INFO] GPU настроен в конфиге: {model_engine_device}")
        else:
            print(f"  [WARN] GPU не настроен в конфиге - обучение будет на CPU")
            print(f"         Установите в config.yaml:")
            print(f"         edge:")
            print(f"           device: cuda:0")
            print(f"         model_engine:")
            print(f"           device: cuda:0")
        
        # Проверка параметров модели
        model_config = config.get("model", {})
        print(f"  [INFO] input_size: {model_config.get('input_size', 'N/A')}")
        print(f"  [INFO] confidence_threshold: {model_config.get('confidence_threshold', 'N/A')}")
        
    except Exception as e:
        results.append(check_result(False, "", f"Ошибка чтения конфигурации: {e}"))
    
    return all(results)

def check_model_loading():
    """Проверка загрузки модели на GPU"""
    print_section("Тест загрузки модели на GPU")
    
    results = []
    
    try:
        from ultralytics import YOLO
        import torch
        
        # Попытка загрузить модель
        print("  [INFO] Загрузка тестовой модели...")
        model = YOLO("yolov8n.pt")  # Предобученная модель для теста
        
        if torch.cuda.is_available():
            print("  [INFO] Перемещение модели на GPU...")
            try:
                model.to("cuda:0")
                
                # Тест инференса на GPU
                import numpy as np
                import cv2
                
                # Создать тестовое изображение
                test_image = np.zeros((640, 640, 3), dtype=np.uint8)
                
                print("  [INFO] Тест инференса на GPU...")
                results_gpu = model(test_image, device="cuda:0", verbose=False)
                
                results.append(check_result(
                    True,
                    "Модель успешно загружена и работает на GPU",
                    "Ошибка загрузки модели на GPU"
                ))
                
                print(f"  [INFO] Инференс выполнен успешно на GPU")
                
            except Exception as e:
                results.append(check_result(
                    False,
                    "",
                    f"Ошибка загрузки модели на GPU: {e}"
                ))
        else:
            print("  [WARN] GPU недоступен - пропуск теста GPU")
            results.append(check_result(True, "Модель загружена (CPU)", ""))
            
    except ImportError:
        results.append(check_result(
            False,
            "",
            "Ultralytics YOLO не установлен"
        ))
    except Exception as e:
        results.append(check_result(
            False,
            "",
            f"Ошибка загрузки модели: {e}"
        ))
    
    return all(results)

def check_training_ready():
    """Проверка готовности к обучению"""
    print_section("Готовность к обучению")
    
    checks = []
    
    # Проверка датасета
    dataset_path = Path("datasets/cigarette_butt/data.yaml")
    checks.append((
        dataset_path.exists(),
        "Датасет готов",
        "Датасет не найден или не настроен"
    ))
    
    # Проверка наличия изображений
    train_images = Path("datasets/cigarette_butt/train/images")
    checks.append((
        train_images.exists() and len(list(train_images.glob("*.jpg"))) > 0,
        "Обучающие изображения найдены",
        "Обучающие изображения не найдены"
    ))
    
    # Проверка наличия аннотаций
    train_labels = Path("datasets/cigarette_butt/train/labels")
    checks.append((
        train_labels.exists() and len(list(train_labels.glob("*.txt"))) > 0,
        "Аннотации найдены",
        "Аннотации не найдены"
    ))
    
    results = []
    for condition, ok_msg, fail_msg in checks:
        results.append(check_result(condition, ok_msg, fail_msg))
    
    return all(results)

def main():
    """Главная функция проверки"""
    print_header("ПРОВЕРКА СИСТЕМЫ ПЕРЕД ОБУЧЕНИЕМ НА GPU")
    
    checks = {
        "GPU": check_gpu(),
        "Зависимости": check_dependencies(),
        "Датасет": check_dataset(),
        "Конфигурация": check_config(),
        "Загрузка модели": check_model_loading(),
        "Готовность к обучению": check_training_ready(),
    }
    
    print_header("ИТОГИ ПРОВЕРКИ")
    
    all_passed = all(checks.values())
    
    for name, passed in checks.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {name}")
    
    print("\n" + "=" * 70)
    
    if all_passed:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
        print("   Система готова к обучению модели на GPU")
        print("\n   Запустите обучение:")
        print("   python scripts\\train_model.py")
    else:
        print("❌ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        print("   Исправьте проблемы перед обучением")
    
    print("=" * 70 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

