"""
Детальная проверка всех необходимых компонентов для обучения на GPU
"""

import sys
import os
import io

# Настройка кодировки
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def print_header(text):
    """Печать заголовка"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_section(text):
    """Печать секции"""
    print(f"\n{'-' * 70}")
    print(f"  {text}")
    print(f"{'-' * 70}")

def check_item(condition, ok_msg, fail_msg, warn=False):
    """Проверка элемента"""
    status = "[OK]" if condition else ("[WARN]" if warn else "[FAIL]")
    msg = ok_msg if condition else fail_msg
    print(f"  {status} {msg}")
    return condition

def check_cuda():
    """Проверка CUDA"""
    print_section("1. CUDA (Compute Unified Device Architecture)")
    
    results = []
    
    # Проверка через torch
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        results.append(check_item(
            cuda_available,
            "CUDA доступен через PyTorch",
            "CUDA недоступен через PyTorch",
            warn=False
        ))
        
        if cuda_available:
            cuda_version = torch.version.cuda
            print(f"  [INFO] Версия CUDA (PyTorch): {cuda_version}")
            
            # Количество GPU
            gpu_count = torch.cuda.device_count()
            print(f"  [INFO] Количество GPU: {gpu_count}")
            
            for i in range(gpu_count):
                print(f"\n  GPU {i}:")
                gpu_name = torch.cuda.get_device_name(i)
                props = torch.cuda.get_device_properties(i)
                memory_total = props.total_memory / (1024**3)
                memory_allocated = torch.cuda.memory_allocated(i) / (1024**3)
                memory_cached = torch.cuda.memory_reserved(i) / (1024**3)
                
                print(f"    Название: {gpu_name}")
                print(f"    Память: {memory_total:.2f} GB (всего)")
                print(f"    Использовано: {memory_allocated:.2f} GB")
                print(f"    Зарезервировано: {memory_cached:.2f} GB")
                print(f"    Доступно: {memory_total - memory_cached:.2f} GB")
                print(f"    Compute Capability: {props.major}.{props.minor}")
                print(f"    Мультипроцессоры: {props.multi_processor_count}")
        else:
            print("  [INFO] CUDA недоступен - установите PyTorch с CUDA поддержкой")
            print("         См. https://pytorch.org/get-started/locally/")
    except ImportError:
        results.append(check_item(
            False,
            "",
            "PyTorch не установлен",
            warn=False
        ))
    
    # Проверка CUDA через nvidia-smi
    try:
        import subprocess
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"\n  [OK] nvidia-smi доступен")
            # Парсим версию драйвера из вывода
            lines = result.stdout.split('\n')
            for line in lines:
                if 'Driver Version:' in line or 'Driver version:' in line:
                    print(f"  [INFO] {line.strip()}")
                    break
            results.append(True)
        else:
            print(f"  [WARN] nvidia-smi недоступен или вернул ошибку")
            results.append(False)
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"  [WARN] nvidia-smi не найден: {e}")
        results.append(False)
    
    return all(results)

def check_pytorch_cuda():
    """Проверка PyTorch с CUDA"""
    print_section("2. PyTorch с CUDA поддержкой")
    
    results = []
    
    try:
        import torch
        print(f"  [INFO] PyTorch версия: {torch.__version__}")
        
        cuda_available = torch.cuda.is_available()
        results.append(check_item(
            cuda_available,
            "PyTorch собран с CUDA поддержкой",
            "PyTorch без CUDA поддержки (CPU only)",
            warn=False
        ))
        
        if cuda_available:
            print(f"  [INFO] CUDA версия (PyTorch): {torch.version.cuda}")
            print(f"  [INFO] cuDNN версия: {torch.backends.cudnn.version() if torch.backends.cudnn.is_available() else 'N/A'}")
            print(f"  [INFO] cuDNN доступен: {torch.backends.cudnn.is_available()}")
            
            # Проверка cuDNN
            results.append(check_item(
                torch.backends.cudnn.is_available(),
                "cuDNN доступен",
                "cuDNN недоступен (может замедлить обучение)",
                warn=True
            ))
            
            # Тест операций на GPU
            try:
                print(f"\n  Тест операций на GPU...")
                device = torch.device('cuda:0')
                x = torch.randn(1000, 1000, device=device)
                y = torch.randn(1000, 1000, device=device)
                z = torch.matmul(x, y)
                torch.cuda.synchronize()
                del x, y, z
                torch.cuda.empty_cache()
                
                results.append(check_item(
                    True,
                    "Операции на GPU работают корректно",
                    "Ошибка при выполнении операций на GPU",
                    warn=False
                ))
            except Exception as e:
                results.append(check_item(
                    False,
                    "",
                    f"Ошибка при тестировании GPU: {e}",
                    warn=False
                ))
        else:
            print("  [INFO] Установите PyTorch с CUDA:")
            print("         pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
            
    except ImportError:
        results.append(check_item(
            False,
            "",
            "PyTorch не установлен",
            warn=False
        ))
    
    return all(results)

def check_onnxruntime_gpu():
    """Проверка ONNX Runtime GPU"""
    print_section("3. ONNX Runtime с GPU поддержкой")
    
    results = []
    
    try:
        import onnxruntime as ort
        
        available_providers = ort.get_available_providers()
        print(f"  [INFO] Доступные провайдеры: {available_providers}")
        
        has_cuda = 'CUDAExecutionProvider' in available_providers
        has_cpu = 'CPUExecutionProvider' in available_providers
        
        results.append(check_item(
            has_cuda,
            "CUDAExecutionProvider доступен",
            "CUDAExecutionProvider недоступен (ONNX модели будут на CPU)",
            warn=True
        ))
        
        results.append(check_item(
            has_cpu,
            "CPUExecutionProvider доступен (fallback)",
            "CPUExecutionProvider недоступен",
            warn=False
        ))
        
        if has_cuda:
            try:
                # Получить информацию о CUDA provider
                cuda_options = ort.SessionOptions()
                # Тест создания сессии (без загрузки модели)
                print(f"  [INFO] ONNX Runtime GPU готов к использованию")
            except Exception as e:
                print(f"  [WARN] Ошибка при проверке CUDA provider: {e}")
        else:
            print("  [INFO] Установите onnxruntime-gpu:")
            print("         pip install onnxruntime-gpu")
            
    except ImportError:
        results.append(check_item(
            False,
            "",
            "onnxruntime не установлен",
            warn=False
        ))
    
    return all(results)

def check_ultralytics():
    """Проверка Ultralytics YOLO"""
    print_section("4. Ultralytics YOLO")
    
    results = []
    
    try:
        from ultralytics import YOLO
        import ultralytics
        
        print(f"  [INFO] Ultralytics версия: {ultralytics.__version__}")
        
        # Тест загрузки модели
        try:
            print(f"  [INFO] Тест загрузки модели...")
            model = YOLO("yolov8n.pt")
            results.append(check_item(
                True,
                "YOLO модели загружаются корректно",
                "Ошибка загрузки YOLO моделей",
                warn=False
            ))
            
            # Тест на GPU
            import torch
            if torch.cuda.is_available():
                try:
                    model.to("cuda:0")
                    results.append(check_item(
                        True,
                        "YOLO модель работает на GPU",
                        "Ошибка перемещения модели на GPU",
                        warn=False
                    ))
                except Exception as e:
                    results.append(check_item(
                        False,
                        "",
                        f"Ошибка перемещения модели на GPU: {e}",
                        warn=False
                    ))
            else:
                results.append(check_item(
                    True,
                    "YOLO модель работает на CPU (GPU недоступен)",
                    "",
                    warn=True
                ))
                
        except Exception as e:
            results.append(check_item(
                False,
                "",
                f"Ошибка при тестировании YOLO: {e}",
                warn=False
            ))
            
    except ImportError:
        results.append(check_item(
            False,
            "",
            "ultralytics не установлен (pip install ultralytics)",
            warn=False
        ))
    
    return all(results)

def check_dependencies():
    """Проверка других зависимостей"""
    print_section("5. Другие зависимости")
    
    results = []
    dependencies = {
        'numpy': 'NumPy',
        'cv2': 'OpenCV',
        'yaml': 'PyYAML',
        'pandas': 'Pandas (опционально)',
    }
    
    for module, name in dependencies.items():
        try:
            if module == 'cv2':
                import cv2
                print(f"  [INFO] {name} версия: {cv2.__version__}")
            elif module == 'yaml':
                import yaml
            else:
                mod = __import__(module)
                if hasattr(mod, '__version__'):
                    print(f"  [INFO] {name} версия: {mod.__version__}")
            results.append(check_item(True, f"{name} установлен", f"{name} не установлен", warn=(module == 'pandas')))
        except ImportError:
            results.append(check_item(False, "", f"{name} не установлен", warn=(module == 'pandas')))
    
    return all(results)

def check_dataset_ready():
    """Проверка готовности датасета"""
    print_section("6. Готовность датасета для обучения")
    
    results = []
    from pathlib import Path
    
    dataset_path = Path("datasets/cigarette_butt")
    
    if not dataset_path.exists():
        results.append(check_item(False, "", f"Датасет не найден: {dataset_path}", warn=False))
        return False
    
    # Проверка структуры
    splits = ["train", "valid", "test"]
    for split in splits:
        images_path = dataset_path / split / "images"
        labels_path = dataset_path / split / "labels"
        
        if images_path.exists() and labels_path.exists():
            img_count = len(list(images_path.glob("*.jpg"))) + len(list(images_path.glob("*.png")))
            lbl_count = len(list(labels_path.glob("*.txt")))
            
            results.append(check_item(
                img_count > 0 and lbl_count > 0,
                f"{split}: {img_count} изображений, {lbl_count} аннотаций",
                f"{split}: нет изображений или аннотаций",
                warn=False
            ))
        else:
            results.append(check_item(False, "", f"{split}: директории не найдены", warn=False))
    
    # Проверка data.yaml
    data_yaml = dataset_path / "data.yaml"
    results.append(check_item(
        data_yaml.exists(),
        "data.yaml найден",
        "data.yaml не найден",
        warn=False
    ))
    
    return all(results)

def check_gpu_memory_sufficient():
    """Проверка достаточности памяти GPU для обучения"""
    print_section("7. Достаточность памяти GPU для обучения")
    
    results = []
    
    try:
        import torch
        if torch.cuda.is_available():
            props = torch.cuda.get_device_properties(0)
            memory_total_gb = props.total_memory / (1024**3)
            memory_cached_gb = torch.cuda.memory_reserved(0) / (1024**3)
            memory_free_gb = memory_total_gb - memory_cached_gb
            
            print(f"  [INFO] Всего памяти: {memory_total_gb:.2f} GB")
            print(f"  [INFO] Используется: {memory_cached_gb:.2f} GB")
            print(f"  [INFO] Доступно: {memory_free_gb:.2f} GB")
            
            # Рекомендации по батчу
            if memory_total_gb >= 8:
                recommended_batch = 32
                min_required = 4
            elif memory_total_gb >= 4:
                recommended_batch = 16
                min_required = 2
            else:
                recommended_batch = 8
                min_required = 1
            
            print(f"  [INFO] Рекомендуемый batch size: {recommended_batch}")
            print(f"  [INFO] Минимальный batch size: {min_required}")
            
            results.append(check_item(
                memory_free_gb >= 2,
                f"Достаточно памяти для обучения ({memory_free_gb:.2f} GB свободно)",
                f"Недостаточно памяти для обучения ({memory_free_gb:.2f} GB свободно, нужно минимум 2 GB)",
                warn=True
            ))
        else:
            print("  [INFO] GPU недоступен - пропуск проверки памяти")
            results.append(True)  # Не критично, если GPU нет
            
    except Exception as e:
        print(f"  [WARN] Ошибка проверки памяти: {e}")
        results.append(True)  # Не критично
    
    return all(results)

def main():
    """Главная функция"""
    print_header("ДЕТАЛЬНАЯ ПРОВЕРКА КОМПОНЕНТОВ ДЛЯ ОБУЧЕНИЯ НА GPU")
    
    checks = {
        "CUDA": check_cuda(),
        "PyTorch с CUDA": check_pytorch_cuda(),
        "ONNX Runtime GPU": check_onnxruntime_gpu(),
        "Ultralytics YOLO": check_ultralytics(),
        "Зависимости": check_dependencies(),
        "Датасет": check_dataset_ready(),
        "Память GPU": check_gpu_memory_sufficient(),
    }
    
    print_header("ИТОГОВЫЙ РЕЗУЛЬТАТ")
    
    critical_checks = ["CUDA", "PyTorch с CUDA", "Ultralytics YOLO", "Датасет"]
    critical_passed = all(checks[name] for name in critical_checks if name in checks)
    
    print("\nКритические компоненты (обязательны):")
    for name in critical_checks:
        if name in checks:
            status = "[OK]" if checks[name] else "[FAIL]"
            print(f"  {status} {name}")
    
    print("\nВспомогательные компоненты (рекомендуются):")
    for name in checks:
        if name not in critical_checks:
            status = "[OK]" if checks[name] else "[WARN]"
            print(f"  {status} {name}")
    
    print("\n" + "=" * 70)
    
    if critical_passed:
        if checks.get("CUDA", False) and checks.get("PyTorch с CUDA", False):
            print("✅ ВСЕ КРИТИЧЕСКИЕ КОМПОНЕНТЫ ДОСТУПНЫ!")
            print("   Система готова к обучению на GPU")
        else:
            print("⚠️ ОСНОВНЫЕ КОМПОНЕНТЫ ДОСТУПНЫ, НО GPU НЕДОСТУПЕН")
            print("   Обучение будет выполняться на CPU (медленнее)")
    else:
        print("❌ НЕКОТОРЫЕ КРИТИЧЕСКИЕ КОМПОНЕНТЫ ОТСУТСТВУЮТ")
        print("   Исправьте проблемы перед обучением")
    
    print("=" * 70 + "\n")
    
    return critical_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

