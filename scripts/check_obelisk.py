"""
Скрипт проверки работы Обелиска
Комплексная проверка всех компонентов системы
"""

import sys
import os
import asyncio
import json
from pathlib import Path

# Исправление кодировки для Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Добавление пути к проекту
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yaml
import requests
from typing import Dict, Any, List, Optional


def check_config():
    """Проверка конфигурации"""
    print("=" * 60)
    print("📋 Проверка конфигурации")
    print("=" * 60)
    
    try:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        
        if not config_path.exists():
            print(f"❌ Конфигурация не найдена: {config_path}")
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"✅ Конфигурация загружена: {config_path}")
        
        # Проверка обязательных секций
        required_sections = ['obelisk', 'database', 'mqtt_topics']
        missing = [s for s in required_sections if s not in config]
        
        if missing:
            print(f"⚠️ Отсутствуют секции: {missing}")
        else:
            print("✅ Все обязательные секции присутствуют")
        
        # Информация о конфигурации
        if 'obelisk' in config:
            obelisk = config['obelisk']
            print(f"   Host: {obelisk.get('host', 'N/A')}")
            print(f"   Port: {obelisk.get('port', 'N/A')}")
        
        if 'database' in config:
            db = config['database']
            print(f"   Database type: {db.get('type', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки конфигурации: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_imports():
    """Проверка импортов основных модулей"""
    print("\n" + "=" * 60)
    print("📦 Проверка импортов")
    print("=" * 60)
    
    modules_to_check = [
        ('obelisk.api.main', 'FastAPI приложение'),
        ('obelisk.brain.neural_network_builder', 'NeuralNetworkBuilder'),
        ('obelisk.core.engines.unified_engine', 'UnifiedEngine'),
        ('obelisk.veins.gpu_circulatory', 'GPUCirculatorySystem'),
        ('obelisk.neurons.perception.detection_neuron', 'DetectionNeuron'),
        ('obelisk.neurons.perception.tracking_neuron', 'TrackingNeuron'),
        ('obelisk.neurons.communication.mqtt_neuron', 'MQTTNeuron'),
        ('obelisk.neurons.coordination.docker_neuron', 'DockerNeuron'),
    ]
    
    results = []
    for module_name, description in modules_to_check:
        try:
            __import__(module_name)
            print(f"✅ {description}")
            results.append(True)
        except ImportError as e:
            print(f"❌ {description}: {e}")
            results.append(False)
        except Exception as e:
            print(f"⚠️ {description}: {e}")
            results.append(False)
    
    return all(results)


async def check_neural_network():
    """Проверка нейронной сети"""
    print("\n" + "=" * 60)
    print("🧠 Проверка нейронной сети")
    print("=" * 60)
    
    try:
        from obelisk.brain.neural_network_builder import NeuralNetworkBuilder
        
        # Создание строителя
        builder = NeuralNetworkBuilder()
        print("✅ NeuralNetworkBuilder создан")
        
        # Построение сети
        builder.build_network()
        print("✅ Нейронная сеть построена")
        
        # Проверка нейронов
        expected_neurons = [
            'detection_neuron',
            'tracking_neuron',
            'vision_neuron',
            'hub_neuron',
            'task_coordinator_neuron',
            'swarm_coordinator_neuron',
            'mqtt_neuron',
            'docker_neuron'
        ]
        
        print("\n📋 Проверка нейронов:")
        for neuron_name in expected_neurons:
            if neuron_name in builder.neurons:
                neuron = builder.neurons[neuron_name]
                print(f"   ✅ {neuron_name}: {type(neuron).__name__}")
            else:
                print(f"   ⚠️ {neuron_name}: Не найден")
        
        # Проверка GPU системы
        gpu_system = builder.get_gpu_system()
        if gpu_system:
            print("\n🩸 GPU система:")
            print(f"   ✅ Circulatory: {type(gpu_system['circulatory']).__name__}")
            print(f"   ✅ Distributor: {type(gpu_system['distributor']).__name__}")
            print(f"   ✅ Monitor: {type(gpu_system['monitor']).__name__}")
        
        # Проверка коллективного разума
        collective_mind = builder.get_collective_mind()
        if collective_mind:
            print(f"\n🧠 Коллективный разум: {len(builder.neurons)} нейронов зарегистрировано")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки нейронной сети: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_database():
    """Проверка базы данных"""
    print("\n" + "=" * 60)
    print("💾 Проверка базы данных")
    print("=" * 60)
    
    try:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        db_config = config.get('database', {})
        db_type = db_config.get('type', 'sqlite')
        
        print(f"   Database type: {db_type}")
        
        if db_type == 'sqlite':
            sqlite_path = db_config.get('sqlite_path', 'data/obelisk.db')
            db_file = Path(__file__).parent.parent / sqlite_path
            
            if db_file.exists():
                size = db_file.stat().st_size / (1024 * 1024)  # MB
                print(f"   ✅ База данных существует: {db_file}")
                print(f"   Размер: {size:.2f} MB")
            else:
                print(f"   ⚠️ База данных не найдена: {db_file}")
                print(f"   (Будет создана при первом запуске)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки базы данных: {e}")
        return False


def check_mqtt_config():
    """Проверка конфигурации MQTT"""
    print("\n" + "=" * 60)
    print("📡 Проверка конфигурации MQTT")
    print("=" * 60)
    
    try:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'obelisk' in config:
            obelisk_config = config['obelisk']
            mqtt_broker = obelisk_config.get('mqtt_broker', 'localhost')
            mqtt_port = obelisk_config.get('mqtt_port', 1883)
            
            print(f"   Broker: {mqtt_broker}:{mqtt_port}")
            
            # Попытка подключения
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((mqtt_broker, mqtt_port))
                sock.close()
                
                if result == 0:
                    print(f"   ✅ MQTT брокер доступен")
                else:
                    print(f"   ⚠️ MQTT брокер недоступен (порт закрыт)")
                    print(f"   Запустите: docker-compose up -d mosquitto")
            except Exception as e:
                print(f"   ⚠️ Не удалось проверить MQTT: {e}")
        
        if 'mqtt_topics' in config:
            topics = config['mqtt_topics']
            print(f"   ✅ Конфигурация топиков найдена")
            print(f"   Топиков: {len(topics)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки MQTT: {e}")
        return False


def check_api_endpoints():
    """Проверка API endpoints"""
    print("\n" + "=" * 60)
    print("🌐 Проверка API endpoints")
    print("=" * 60)
    
    try:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        host = config.get('obelisk', {}).get('host', 'localhost')
        port = config.get('obelisk', {}).get('port', 8000)
        base_url = f"http://{host}:{port}"
        
        print(f"   Base URL: {base_url}")
        
        endpoints_to_check = [
            ('/', 'Root endpoint'),
            ('/health', 'Health check'),
            ('/docs', 'API documentation'),
        ]
        
        results = []
        for endpoint, description in endpoints_to_check:
            try:
                url = f"{base_url}{endpoint}"
                response = requests.get(url, timeout=2)
                
                if response.status_code == 200:
                    print(f"   ✅ {description}: {response.status_code}")
                    results.append(True)
                else:
                    print(f"   ⚠️ {description}: {response.status_code}")
                    results.append(False)
            except requests.exceptions.ConnectionError:
                print(f"   ⚠️ {description}: Сервер не запущен")
                print(f"   Запустите: python -m obelisk.api.main")
                results.append(False)
            except Exception as e:
                print(f"   ❌ {description}: {e}")
                results.append(False)
        
        return any(results)  # Хотя бы один endpoint доступен
        
    except Exception as e:
        print(f"❌ Ошибка проверки API: {e}")
        return False


async def check_unified_engine():
    """Проверка UnifiedEngine"""
    print("\n" + "=" * 60)
    print("⚙️ Проверка UnifiedEngine")
    print("=" * 60)
    
    try:
        from obelisk.core.engines.unified_engine import UnifiedEngine
        from pathlib import Path
        
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        project_root = Path(__file__).parent.parent
        
        # Создание UnifiedEngine (без полной инициализации)
        engine = UnifiedEngine(config, project_root)
        print("✅ UnifiedEngine создан")
        
        # Проверка компонентов
        components = [
            ('model_engine', 'ModelEngine'),
            ('vision_context', 'VisionContext'),
            ('database', 'Database'),
            ('mqtt_client', 'MQTTClient'),
            ('task_manager', 'TaskManager'),
        ]
        
        print("\n📋 Компоненты (будут инициализированы при запуске):")
        for attr, name in components:
            if hasattr(engine, attr):
                value = getattr(engine, attr)
                status = "✅" if value is not None else "⏳"
                print(f"   {status} {name}")
            else:
                print(f"   ⚠️ {name}: Атрибут не найден")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки UnifiedEngine: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_file_structure():
    """Проверка структуры файлов"""
    print("\n" + "=" * 60)
    print("📁 Проверка структуры файлов")
    print("=" * 60)
    
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        'obelisk',
        'obelisk/api',
        'obelisk/brain',
        'obelisk/core',
        'obelisk/neurons',
        'obelisk/services',
        'obelisk/veins',
        'config',
        'data',
    ]
    
    results = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"   ✅ {dir_path}")
            results.append(True)
        else:
            print(f"   ❌ {dir_path}: Не найден")
            results.append(False)
    
    return all(results)


async def main():
    """Главная функция проверки"""
    print("\n" + "=" * 60)
    print("🔧 ПРОВЕРКА РАБОТЫ ОБЕЛИСКА")
    print("=" * 60)
    
    results = []
    
    # 1. Проверка структуры файлов
    results.append(("File Structure", check_file_structure()))
    
    # 2. Проверка конфигурации
    results.append(("Configuration", check_config()))
    
    # 3. Проверка импортов
    results.append(("Imports", check_imports()))
    
    # 4. Проверка нейронной сети
    results.append(("Neural Network", await check_neural_network()))
    
    # 5. Проверка базы данных
    results.append(("Database", check_database()))
    
    # 6. Проверка MQTT
    results.append(("MQTT Config", check_mqtt_config()))
    
    # 7. Проверка UnifiedEngine
    results.append(("UnifiedEngine", await check_unified_engine()))
    
    # 8. Проверка API (опционально, если сервер запущен)
    results.append(("API Endpoints", check_api_endpoints()))
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ПРОВЕРКИ")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n   Всего проверок: {len(results)}")
    print(f"   Пройдено: {passed}")
    print(f"   Не пройдено: {failed}")
    
    print("\n" + "=" * 60)
    if failed == 0:
        print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
        print("   Обелиск готов к работе!")
    elif passed > failed:
        print("⚠️ БОЛЬШИНСТВО ПРОВЕРОК ПРОЙДЕНО")
        print("   Некоторые компоненты требуют внимания")
    else:
        print("❌ МНОГИЕ ПРОВЕРКИ НЕ ПРОЙДЕНЫ")
        print("   Требуется исправление проблем")
    print("=" * 60)
    
    # Рекомендации
    if failed > 0:
        print("\n💡 РЕКОМЕНДАЦИИ:")
        if not results[7][1]:  # API не доступен
            print("   - Запустите Обелиск: python -m obelisk.api.main")
        if not results[5][1]:  # MQTT не доступен
            print("   - Запустите MQTT брокер: docker-compose up -d mosquitto")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

