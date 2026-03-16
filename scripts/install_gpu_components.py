"""
Скрипт для установки компонентов для обучения на GPU
Автоматически определяет нужные версии и устанавливает их
"""

import sys
import subprocess
import os

def run_command(command, check=True):
    """Выполнить команду"""
    print(f"\n{'='*70}")
    print(f"Выполнение: {command}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"✅ Успешно выполнено")
        if result.stdout:
            print(result.stdout)
    else:
        print(f"❌ Ошибка: {result.stderr}")
        if result.stdout:
            print(result.stdout)
    
    return result.returncode == 0

def check_nvidia_smi():
    """Проверка наличия NVIDIA драйверов"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Парсим версию CUDA
            for line in result.stdout.split('\n'):
                if 'CUDA Version:' in line:
                    cuda_version = line.split('CUDA Version:')[1].split()[0]
                    print(f"✅ NVIDIA драйверы найдены")
                    print(f"   CUDA Version: {cuda_version}")
                    return True, cuda_version
            return True, None
        return False, None
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"❌ nvidia-smi не найден: {e}")
        return False, None

def get_pytorch_cuda_version():
    """Определить версию PyTorch CUDA для установки"""
    # Проверяем доступную CUDA версию
    found, cuda_version = check_nvidia_smi()
    
    if not found:
        print("⚠️ NVIDIA драйверы не найдены - используем CPU версию")
        return None
    
    # PyTorch поддерживает CUDA 12.1 и 11.8 (они обратно совместимы)
    # Рекомендуем CUDA 12.1
    print(f"\n📌 Рекомендуемая версия PyTorch CUDA: 12.1")
    print(f"   (совместима с CUDA {cuda_version} если доступна)")
    
    return "cu121"  # CUDA 12.1

def install_pytorch_cuda(cuda_version="cu121"):
    """Установка PyTorch с CUDA"""
    print("\n" + "="*70)
    print("ШАГ 1: УДАЛЕНИЕ СТАРОЙ ВЕРСИИ PYTORCH (CPU ONLY)")
    print("="*70)
    
    # Удаление старой версии
    run_command("pip uninstall torch torchvision torchaudio -y", check=False)
    
    print("\n" + "="*70)
    print(f"ШАГ 2: УСТАНОВКА PYTORCH С CUDA {cuda_version.replace('cu', '')}")
    print("="*70)
    
    # Установка с CUDA
    url = f"https://download.pytorch.org/whl/{cuda_version}"
    success = run_command(f"pip install torch torchvision torchaudio --index-url {url}")
    
    if success:
        # Проверка установки
        print("\n" + "="*70)
        print("ПРОВЕРКА УСТАНОВКИ PYTORCH С CUDA")
        print("="*70)
        
        check_code = """
import torch
print(f"PyTorch версия: {torch.__version__}")
print(f"CUDA доступен: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA версия: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
else:
    print("❌ CUDA недоступен в PyTorch")
"""
        
        result = subprocess.run([sys.executable, "-c", check_code], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0 and "CUDA доступен: True" in result.stdout
    else:
        return False

def install_onnxruntime_gpu():
    """Установка ONNX Runtime с GPU поддержкой"""
    print("\n" + "="*70)
    print("ШАГ 3: УСТАНОВКА ONNX RUNTIME GPU")
    print("="*70)
    
    # Удаление старой версии (если есть)
    run_command("pip uninstall onnxruntime -y", check=False)
    
    # Установка GPU версии
    success = run_command("pip install onnxruntime-gpu")
    
    if success:
        # Проверка установки
        print("\n" + "="*70)
        print("ПРОВЕРКА УСТАНОВКИ ONNX RUNTIME GPU")
        print("="*70)
        
        check_code = """
import onnxruntime as ort
providers = ort.get_available_providers()
print(f"Доступные провайдеры: {providers}")
if 'CUDAExecutionProvider' in providers:
    print("✅ CUDAExecutionProvider доступен")
else:
    print("❌ CUDAExecutionProvider недоступен")
"""
        
        result = subprocess.run([sys.executable, "-c", check_code], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
    else:
        return False

def main():
    """Главная функция"""
    print("="*70)
    print("УСТАНОВКА КОМПОНЕНТОВ ДЛЯ ОБУЧЕНИЯ НА GPU")
    print("="*70)
    
    # Проверка NVIDIA драйверов
    found, cuda_version = check_nvidia_smi()
    
    if not found:
        print("\n❌ NVIDIA драйверы не найдены!")
        print("   Установите NVIDIA драйверы перед продолжением")
        print("   См. https://www.nvidia.com/Download/index.aspx")
        return False
    
    print(f"\n✅ NVIDIA драйверы найдены (CUDA {cuda_version})")
    
    # Определить версию PyTorch CUDA
    pytorch_cuda = get_pytorch_cuda_version()
    
    if pytorch_cuda:
        # Установить PyTorch с CUDA
        pytorch_ok = install_pytorch_cuda(pytorch_cuda)
        
        if not pytorch_ok:
            print("\n❌ Ошибка установки PyTorch с CUDA")
            return False
    else:
        print("\n⚠️ Пропуск установки PyTorch с CUDA (драйверы не найдены)")
        pytorch_ok = False
    
    # Установить ONNX Runtime GPU
    onnx_ok = install_onnxruntime_gpu()
    
    # Итоги
    print("\n" + "="*70)
    print("ИТОГИ УСТАНОВКИ")
    print("="*70)
    
    if pytorch_ok:
        print("✅ PyTorch с CUDA установлен")
    else:
        print("❌ PyTorch с CUDA не установлен")
    
    if onnx_ok:
        print("✅ ONNX Runtime GPU установлен")
    else:
        print("❌ ONNX Runtime GPU не установлен")
    
    if pytorch_ok and onnx_ok:
        print("\n✅ ВСЕ КОМПОНЕНТЫ УСТАНОВЛЕНЫ!")
        print("\n   Теперь запустите проверку:")
        print("   python scripts\\check_gpu_components.py")
    else:
        print("\n⚠️ НЕКОТОРЫЕ КОМПОНЕНТЫ НЕ УСТАНОВЛЕНЫ")
        print("   Проверьте ошибки выше")
    
    print("="*70)
    
    return pytorch_ok and onnx_ok

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Установка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

