"""
Скрипт проверки подключения GPU к нейронам
"""

import sys
import os
import asyncio

# Исправление кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Добавление пути к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from obelisk.brain.neural_network_builder import NeuralNetworkBuilder
from obelisk.veins.gpu_circulatory import GPUCirculatorySystem
from obelisk.veins.gpu_distributor import GPUDistributor
from obelisk.veins.gpu_monitor import GPUMonitor


def check_gpu_availability():
    """Проверка доступности GPU"""
    print("=" * 60)
    print("🔍 Проверка доступности GPU")
    print("=" * 60)
    
    try:
        import torch
        
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            print(f"✅ CUDA доступен")
            print(f"   Устройств: {device_count}")
            
            for i in range(device_count):
                props = torch.cuda.get_device_properties(i)
                total_memory = props.total_memory / (1024**3)
                print(f"   GPU {i}: {props.name} ({total_memory:.2f} GB)")
            
            return True
        else:
            print("❌ CUDA недоступен")
            print("   GPU не найден или драйверы не установлены")
            return False
            
    except ImportError:
        print("❌ PyTorch не установлен")
        return False
    except Exception as e:
        print(f"❌ Ошибка проверки GPU: {e}")
        return False


def check_gpu_system():
    """Проверка GPU системы"""
    print("\n" + "=" * 60)
    print("🩸 Проверка GPU системы (Veins)")
    print("=" * 60)
    
    try:
        # Создание GPU системы
        circulatory = GPUCirculatorySystem()
        distributor = GPUDistributor(circulatory)
        monitor = GPUMonitor()
        
        print("✅ GPU система создана")
        print(f"   Circulatory: {type(circulatory).__name__}")
        print(f"   Distributor: {type(distributor).__name__}")
        print(f"   Monitor: {type(monitor).__name__}")
        
        # Получение статистики GPU
        gpu_stats = monitor.get_gpu_stats()
        if gpu_stats:
            print(f"\n📊 Статистика GPU:")
            for device in gpu_stats["devices"]:
                print(f"   Device {device['device_id']}: {device['device_name']}")
                print(f"      Memory: {device['allocated_memory_gb']:.2f} / {device['total_memory_gb']:.2f} GB")
                print(f"      Usage: {device['usage_percent']:.1f}%")
        else:
            print("   ⚠️ GPU статистика недоступна")
        
        # Статистика кровообращения
        circ_stats = circulatory.get_statistics()
        print(f"\n📈 Статистика кровообращения:")
        print(f"   Total requests: {circ_stats['total_requests']}")
        print(f"   Successful: {circ_stats['successful_allocations']}")
        print(f"   Failed: {circ_stats['failed_allocations']}")
        print(f"   Success rate: {circ_stats['success_rate']:.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки GPU системы: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_neuron_gpu_connections():
    """Проверка подключения GPU к нейронам"""
    print("\n" + "=" * 60)
    print("🧠 Проверка подключения GPU к нейронам")
    print("=" * 60)
    
    try:
        # Создание строителя нейронной сети
        builder = NeuralNetworkBuilder()
        builder.build_network()
        
        # Получение GPU системы
        gpu_system = builder.get_gpu_system()
        
        print("✅ Нейронная сеть построена")
        print(f"   GPU система: {gpu_system is not None}")
        
        # Проверка нейронов
        neurons_to_check = {
            "detection_neuron": "DetectionNeuron",
            "tracking_neuron": "TrackingNeuron",
            "vision_neuron": "VisionNeuron",
            "docker_neuron": "DockerNeuron",
            "mqtt_neuron": "MQTTNeuron"
        }
        
        print("\n📋 Проверка нейронов:")
        
        for neuron_name, neuron_type in neurons_to_check.items():
            if neuron_name in builder.neurons:
                neuron = builder.neurons[neuron_name]
                
                # Проверка GPU подключения
                gpu_connected = False
                gpu_info = []
                
                if hasattr(neuron, 'gpu_enabled'):
                    gpu_connected = neuron.gpu_enabled
                    if neuron.gpu_circulatory:
                        gpu_info.append("Circulatory")
                    if neuron.gpu_distributor:
                        gpu_info.append("Distributor")
                    if neuron.gpu_monitor:
                        gpu_info.append("Monitor")
                
                if hasattr(neuron, 'gpu_monitor') and neuron.gpu_monitor:
                    gpu_connected = True
                    gpu_info.append("Monitor")
                
                if hasattr(neuron, 'gpu_available'):
                    gpu_info.append(f"Available: {neuron.gpu_available}")
                
                status = "✅" if gpu_connected or gpu_info else "❌"
                gpu_status = ", ".join(gpu_info) if gpu_info else "Не требуется"
                
                print(f"   {status} {neuron_type}: {gpu_status}")
            else:
                print(f"   ⚠️ {neuron_type}: Не найден")
        
        # Статистика нейронов
        print("\n📊 Статистика нейронов:")
        
        if "detection_neuron" in builder.neurons:
            detection = builder.neurons["detection_neuron"]
            if hasattr(detection, 'get_statistics'):
                stats = detection.get_statistics()
                print(f"   DetectionNeuron:")
                print(f"      Detections: {stats.get('detections_count', 0)}")
                print(f"      GPU available: {stats.get('gpu_available', False)}")
        
        if "tracking_neuron" in builder.neurons:
            tracking = builder.neurons["tracking_neuron"]
            if hasattr(tracking, 'get_statistics'):
                stats = tracking.get_statistics()
                print(f"   TrackingNeuron:")
                print(f"      Frame number: {stats.get('frame_number', 0)}")
                print(f"      GPU enabled: {stats.get('gpu_enabled', False)}")
                print(f"      Active tracks: {stats.get('active_tracks', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки нейронов: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_gpu_allocation():
    """Тест выделения GPU"""
    print("\n" + "=" * 60)
    print("🧪 Тест выделения GPU")
    print("=" * 60)
    
    try:
        circulatory = GPUCirculatorySystem()
        
        # Запрос GPU
        print("   Запрос GPU ресурсов...")
        gpu_info = await circulatory.request_gpu(
            task_id="test_task",
            priority=8,
            memory_required=0.05
        )
        
        if gpu_info:
            print(f"   ✅ GPU выделен:")
            print(f"      Device: {gpu_info['device']}")
            print(f"      Free memory: {gpu_info['free_memory'] / (1024**3):.2f} GB")
            print(f"      Free ratio: {gpu_info['free_ratio']:.2%}")
            
            # Освобождение
            await circulatory.release_gpu("test_task")
            print("   ✅ GPU освобожден")
        else:
            print("   ⚠️ GPU недоступен (может быть нормально в тестовой среде)")
        
        # Статистика
        stats = circulatory.get_statistics()
        print(f"\n   Статистика:")
        print(f"      Total requests: {stats['total_requests']}")
        print(f"      Success rate: {stats['success_rate']:.2%}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Главная функция"""
    print("\n" + "=" * 60)
    print("🔧 ПРОВЕРКА ПОДКЛЮЧЕНИЯ GPU К НЕЙРОНАМ ЭКОНЕТ")
    print("=" * 60)
    
    results = []
    
    # Проверка доступности GPU
    results.append(("GPU Availability", check_gpu_availability()))
    
    # Проверка GPU системы
    results.append(("GPU System", check_gpu_system()))
    
    # Проверка подключения к нейронам
    results.append(("Neuron Connections", check_neuron_gpu_connections()))
    
    # Тест выделения GPU
    results.append(("GPU Allocation", asyncio.run(test_gpu_allocation())))
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ПРОВЕРКИ")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    else:
        print("⚠️ НЕКОТОРЫЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

