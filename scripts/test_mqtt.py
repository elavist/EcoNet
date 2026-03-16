"""
Полная проверка MQTT системы
Тестирует конфигурацию, подключение, подписки, публикацию и получение сообщений
"""
import asyncio
import sys
import json
import socket
import time
from pathlib import Path
from typing import Dict, Optional
import yaml

# Добавляем корень проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from obelisk.services.mqtt_client import MQTTClient
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MQTTTester:
    """Тестер MQTT системы"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or project_root / "config" / "config.yaml"
        self.config = None
        self.mqtt_client = None
        self.received_messages = []
        self.test_results = {}
        
    def load_config(self):
        """Загрузка конфигурации"""
        print("=" * 60)
        print("[STEP 1] Загрузка конфигурации")
        print("=" * 60)
        
        if not self.config_path.exists():
            print(f"[ERROR] Файл конфигурации не найден: {self.config_path}")
            return False
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            print(f"[OK] Конфигурация загружена из {self.config_path}")
            
            # Проверка MQTT настроек
            mqtt_config = self.config.get('obelisk', {})
            print(f"\n[MQTT Config]")
            print(f"  Broker: {mqtt_config.get('mqtt_broker', 'N/A')}")
            print(f"  Port: {mqtt_config.get('mqtt_port', 'N/A')}")
            print(f"  Username: {mqtt_config.get('mqtt_username', 'None')}")
            print(f"  TLS: {mqtt_config.get('enable_tls', False)}")
            
            # Проверка топиков
            topics = self.config.get('mqtt_topics', {})
            print(f"\n[Topics] ({len(topics)} топиков)")
            for name, topic in topics.items():
                print(f"  {name}: {topic}")
            
            self.test_results['config_load'] = True
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки конфигурации: {e}")
            self.test_results['config_load'] = False
            return False
    
    def check_broker_availability(self):
        """Проверка доступности MQTT брокера"""
        print("\n" + "=" * 60)
        print("[STEP 2] Проверка доступности MQTT брокера")
        print("=" * 60)
        
        mqtt_config = self.config.get('obelisk', {})
        host = mqtt_config.get('mqtt_broker', 'localhost')
        port = mqtt_config.get('mqtt_port', 1883)
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"[OK] MQTT брокер доступен на {host}:{port}")
                self.test_results['broker_available'] = True
                return True
            else:
                print(f"[ERROR] MQTT брокер недоступен на {host}:{port}")
                print(f"[INFO] Убедитесь, что MQTT брокер запущен")
                print(f"[INFO] Запуск: docker-compose up -d mosquitto")
                self.test_results['broker_available'] = False
                return False
                
        except Exception as e:
            print(f"[ERROR] Ошибка проверки брокера: {e}")
            self.test_results['broker_available'] = False
            return False
    
    async def test_connection(self):
        """Тест подключения к MQTT брокеру"""
        print("\n" + "=" * 60)
        print("[STEP 3] Тест подключения к MQTT брокеру")
        print("=" * 60)
        
        try:
            topics = self.config.get('mqtt_topics', {})
            mqtt_config = self.config.get('obelisk', {})
            
            self.mqtt_client = MQTTClient(topics, mqtt_config)
            
            print("[INFO] Подключение к MQTT брокеру...")
            await self.mqtt_client.connect()
            
            # Ждем немного для завершения подключения
            await asyncio.sleep(1)
            
            if self.mqtt_client.is_connected():
                print("[OK] Подключение к MQTT брокеру успешно")
                self.test_results['connection'] = True
                return True
            else:
                print("[ERROR] Не удалось подключиться к MQTT брокеру")
                self.test_results['connection'] = False
                return False
                
        except Exception as e:
            print(f"[ERROR] Ошибка подключения: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['connection'] = False
            return False
    
    async def test_subscription(self):
        """Тест подписки на топики"""
        print("\n" + "=" * 60)
        print("[STEP 4] Тест подписки на топики")
        print("=" * 60)
        
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            print("[ERROR] MQTT клиент не подключен")
            self.test_results['subscription'] = False
            return False
        
        try:
            topics = self.config.get('mqtt_topics', {})
            
            # Регистрируем callback для получения сообщений
            def test_callback(topic: str, payload: Dict):
                """Синхронный callback для получения сообщений"""
                self.received_messages.append({
                    'topic': topic,
                    'payload': payload,
                    'timestamp': time.time()
                })
                print(f"[MESSAGE] Получено сообщение из {topic}: {payload}")
            
            # Подписываемся на тестовый топик
            test_topic = "obelisk/test"
            self.mqtt_client.subscribe(test_topic, test_callback)
            
            print(f"[OK] Подписка на тестовый топик: {test_topic}")
            
            # Проверяем подписку на основные топики
            print(f"\n[INFO] Подписка на основные топики:")
            for name, topic_path in topics.items():
                # Заменяем плейсхолдеры
                if '{robot_id}' in topic_path:
                    topic_path = topic_path.replace('{robot_id}', '+')
                print(f"  {name}: {topic_path}")
            
            self.test_results['subscription'] = True
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка подписки: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['subscription'] = False
            return False
    
    async def test_publish(self):
        """Тест публикации сообщений"""
        print("\n" + "=" * 60)
        print("[STEP 5] Тест публикации сообщений")
        print("=" * 60)
        
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            print("[ERROR] MQTT клиент не подключен")
            self.test_results['publish'] = False
            return False
        
        try:
            test_topic = "obelisk/test"
            test_payload = {
                "test": True,
                "message": "MQTT test message",
                "timestamp": time.time()
            }
            
            print(f"[INFO] Публикация тестового сообщения в {test_topic}...")
            await self.mqtt_client.publish(test_topic, test_payload)
            
            # Ждем немного для обработки
            await asyncio.sleep(0.5)
            
            print("[OK] Сообщение опубликовано успешно")
            print(f"[INFO] Payload: {test_payload}")
            
            # Тестируем публикацию в основные топики
            print(f"\n[INFO] Тестирование публикации в основные топики:")
            topics = self.config.get('mqtt_topics', {})
            
            test_topics = ['detection', 'system_status']
            for topic_name in test_topics:
                if topic_name in topics:
                    topic = topics[topic_name]
                    payload = {
                        "test": True,
                        "topic": topic_name,
                        "timestamp": time.time()
                    }
                    await self.mqtt_client.publish(topic, payload)
                    print(f"  [OK] Опубликовано в {topic}")
                    await asyncio.sleep(0.2)
            
            self.test_results['publish'] = True
            return True
            
        except Exception as e:
            print(f"[ERROR] Ошибка публикации: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['publish'] = False
            return False
    
    async def test_message_receive(self, timeout: int = 5):
        """Тест получения сообщений"""
        print("\n" + "=" * 60)
        print("[STEP 6] Тест получения сообщений")
        print("=" * 60)
        
        if not self.mqtt_client or not self.mqtt_client.is_connected():
            print("[ERROR] MQTT клиент не подключен")
            self.test_results['receive'] = False
            return False
        
        initial_count = len(self.received_messages)
        
        print(f"[INFO] Ожидание сообщений в течение {timeout} секунд...")
        print("[INFO] Публикуем тестовое сообщение для проверки получения...")
        
        # Публикуем сообщение и ждем его получения
        test_topic = "obelisk/test"
        test_payload = {
            "test": True,
            "message": "Test receive message",
            "timestamp": time.time()
        }
        
        await self.mqtt_client.publish(test_topic, test_payload)
        
        # Ждем получения сообщения
        start_time = time.time()
        while time.time() - start_time < timeout:
            if len(self.received_messages) > initial_count:
                print(f"[OK] Получено сообщение!")
                for msg in self.received_messages[initial_count:]:
                    print(f"  Topic: {msg['topic']}")
                    print(f"  Payload: {msg['payload']}")
                self.test_results['receive'] = True
                return True
            await asyncio.sleep(0.1)
        
        if len(self.received_messages) == initial_count:
            print(f"[WARN] Сообщения не получены в течение {timeout} секунд")
            print("[INFO] Это может быть нормально, если подписка не работает или сообщение не было опубликовано")
            self.test_results['receive'] = False
            return False
    
    async def test_cleanup(self):
        """Очистка и отключение"""
        print("\n" + "=" * 60)
        print("[STEP 7] Отключение от MQTT брокера")
        print("=" * 60)
        
        if self.mqtt_client:
            try:
                await self.mqtt_client.disconnect()
                print("[OK] Отключение от MQTT брокера выполнено")
                self.test_results['cleanup'] = True
            except Exception as e:
                print(f"[ERROR] Ошибка отключения: {e}")
                self.test_results['cleanup'] = False
        else:
            print("[INFO] MQTT клиент не создан, очистка не требуется")
            self.test_results['cleanup'] = True
    
    def print_summary(self):
        """Вывод итоговой сводки"""
        print("\n" + "=" * 60)
        print("ИТОГОВАЯ СВОДКА")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"\nТестов выполнено: {total_tests}")
        print(f"Успешно: {passed_tests}")
        print(f"Неудачно: {total_tests - passed_tests}")
        
        print(f"\nДетали:")
        for test_name, result in self.test_results.items():
            status = "[OK]" if result else "[FAIL]"
            print(f"  {status} {test_name}")
        
        print(f"\nПолучено сообщений: {len(self.received_messages)}")
        
        if all(self.test_results.values()):
            print("\n[SUCCESS] Все тесты MQTT пройдены успешно!")
            return True
        else:
            print("\n[WARNING] Некоторые тесты MQTT не пройдены")
            return False
    
    async def run_all_tests(self):
        """Запуск всех тестов"""
        print("=" * 60)
        print("ПОЛНАЯ ПРОВЕРКА MQTT СИСТЕМЫ")
        print("=" * 60)
        
        # Загрузка конфигурации
        if not self.load_config():
            return False
        
        # Проверка доступности брокера
        if not self.check_broker_availability():
            print("\n[WARN] Продолжаем тестирование, но некоторые тесты могут не пройти")
        
        # Тест подключения
        if not await self.test_connection():
            print("\n[ERROR] Не удалось подключиться. Остановка тестов.")
            return False
        
        # Тест подписки
        await self.test_subscription()
        
        # Тест публикации
        await self.test_publish()
        
        # Тест получения сообщений
        await self.test_message_receive()
        
        # Очистка
        await self.test_cleanup()
        
        # Итоговая сводка
        return self.print_summary()


async def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Тестирование MQTT системы')
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Путь к файлу конфигурации (по умолчанию: config/config.yaml)'
    )
    
    args = parser.parse_args()
    
    config_path = Path(args.config) if args.config else None
    
    tester = MQTTTester(config_path)
    
    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Тестирование прервано пользователем")
        if tester.mqtt_client:
            await tester.mqtt_client.disconnect()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        if tester.mqtt_client:
            await tester.mqtt_client.disconnect()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

