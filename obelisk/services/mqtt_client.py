"""
MQTT клиент для коммуникации между устройствами
"""

import paho.mqtt.client as mqtt
import json
import asyncio
from typing import Dict, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class MQTTClient:
    """Асинхронный MQTT клиент"""
    
    def __init__(self, topics: Dict[str, str], config: Dict):
        """
        Инициализация MQTT клиента
        
        Args:
            topics: Словарь с топиками
            config: Конфигурация MQTT брокера
        """
        self.topics = topics
        self.config = config
        self.client = None
        self.callbacks: Dict[str, Callable] = {}
        self.loop = asyncio.get_event_loop()
        self._connected = False
        self._last_disconnect_reason = None
        self._disconnect_count = 0
        
    async def connect(self):
        """Подключение к MQTT брокеру"""
        # Используем уникальный client_id для избежания конфликтов
        import uuid
        client_id = self.config.get('mqtt_client_id', f"obelisk_{uuid.uuid4().hex[:8]}")
        self.client = mqtt.Client(client_id=client_id, clean_session=True)
        
        # Настройка TLS если требуется
        if self.config.get('enable_tls', False):
            self.client.tls_set()
        
        # Аутентификация если требуется
        if self.config.get('mqtt_username'):
            self.client.username_pw_set(
                self.config['mqtt_username'],
                self.config.get('mqtt_password')
            )
        
        # Callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        
        # Подключение
        host = self.config['mqtt_broker']
        port = self.config['mqtt_port']
        
        try:
            self.client.connect_async(host, port, 60)
            self.client.loop_start()
            
            # Ждем подключения
            timeout = 5
            while not self._connected and timeout > 0:
                await asyncio.sleep(0.1)
                timeout -= 0.1
            
            if self._connected:
                # Сбрасываем счетчик отключений при успешном подключении
                self._disconnect_count = 0
                logger.info(f"✅ Подключен к MQTT брокеру {host}:{port} (client_id: {client_id})")
            else:
                logger.error(f"❌ Не удалось подключиться к MQTT брокеру {host}:{port}")
                
        except Exception as e:
            logger.error(f"Ошибка подключения к MQTT: {e}")
            raise
    
    async def disconnect(self):
        """Отключение от MQTT брокера"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self._connected = False
            logger.info("Отключен от MQTT брокера")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback при подключении"""
        if rc == 0:
            self._connected = True
            logger.info("MQTT клиент подключен")
            
            # Подписка на все топики
            for topic_name, topic_path in self.topics.items():
                # Заменить плейсхолдеры в топиках
                if '{robot_id}' in topic_path:
                    # Подписаться на все роботы (wildcard)
                    topic_path = topic_path.replace('{robot_id}', '+')
                
                client.subscribe(topic_path)
                logger.info(f"Подписан на топик: {topic_path}")
        else:
            logger.error(f"Ошибка подключения MQTT: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback при отключении"""
        was_connected = self._connected
        self._connected = False
        
        # rc=0 означает нормальное отключение (вызванное клиентом)
        # rc!=0 означает неожиданное отключение (ошибка сети/сервера)
        if rc == 0:
            # Нормальное отключение - логируем только если было подключение
            if was_connected:
                logger.debug("MQTT клиент отключен (нормальное отключение)")
            # Игнорируем, если не было подключения
        else:
            self._disconnect_count += 1
            
            # Коды ошибок MQTT:
            # 1 = Network error
            # 2 = Protocol error  
            # 3 = Connection refused
            # 4 = Client ID rejected
            # 5 = Authentication failed
            error_messages = {
                1: "Network error",
                2: "Protocol error",
                3: "Connection refused",
                4: "Client ID rejected",
                5: "Authentication failed"
            }
            error_msg = error_messages.get(rc, f"Unknown error (code: {rc})")
            
            # Логируем ошибку только если это первая или повторяется много раз
            if self._disconnect_count == 1 or self._disconnect_count % 10 == 0:
                if was_connected:
                    logger.warning(f"MQTT клиент отключен: {error_msg} (rc={rc}, count={self._disconnect_count})")
                else:
                    logger.debug(f"MQTT подключение не удалось: {error_msg} (rc={rc})")
    
    def _on_message(self, client, userdata, msg):
        """Callback при получении сообщения"""
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Вызов зарегистрированных callback'ов
            for registered_topic, callback in self.callbacks.items():
                if self._topic_matches(topic, registered_topic):
                    # Выполнить callback в event loop
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            # Проверяем, есть ли активный event loop
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    # Если loop запущен, создаем task
                                    asyncio.create_task(callback(topic, payload))
                                else:
                                    # Если loop не запущен, запускаем callback в новом loop
                                    loop.run_until_complete(callback(topic, payload))
                            except RuntimeError:
                                # Нет активного loop, создаем новый
                                try:
                                    self.loop.call_soon_threadsafe(
                                        lambda: asyncio.create_task(callback(topic, payload))
                                    )
                                except Exception as e:
                                    logger.error(f"Ошибка планирования async callback: {e}")
                                    # Fallback - запускаем синхронно, если возможно
                                    if callable(callback):
                                        try:
                                            callback(topic, payload)
                                        except Exception as sync_e:
                                            logger.error(f"Ошибка выполнения callback: {sync_e}")
                        else:
                            # Синхронный callback
                            callback(topic, payload)
                    except Exception as callback_error:
                        logger.error(f"Ошибка вызова callback для {topic}: {callback_error}")
                        
        except json.JSONDecodeError:
            logger.error(f"Ошибка декодирования JSON из топика {topic}")
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения из {topic}: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback при публикации"""
        pass
    
    @staticmethod
    def _topic_matches(topic: str, pattern: str) -> bool:
        """
        Полноценный MQTT wildcard matching (спецификация MQTT 3.1.1):
          +  — один уровень (robots/+/status  совпадает с  robots/abc/status)
          #  — ноль или более уровней (swarm/#  совпадает с  swarm/field/node1/state)
        """
        if pattern == topic:
            return True

        topic_parts = topic.split("/")
        pattern_parts = pattern.split("/")

        ti = 0
        pi = 0
        while pi < len(pattern_parts):
            pat = pattern_parts[pi]

            if pat == "#":
                return True

            if ti >= len(topic_parts):
                return False

            if pat != "+" and pat != topic_parts[ti]:
                return False

            ti += 1
            pi += 1

        return ti == len(topic_parts)
    
    def subscribe(self, topic: str, callback: Callable):
        """
        Подписка на топик с callback
        
        Args:
            topic: Путь топика
            callback: Функция-обработчик (может быть async)
        """
        self.callbacks[topic] = callback
        if self.client and self._connected:
            self.client.subscribe(topic)
            logger.info(f"Подписан на топик: {topic}")
    
    async def publish(self, topic: str, payload: dict, qos: int = 1):
        """
        Публикация сообщения в топик
        
        Args:
            topic: Путь топика
            payload: Словарь с данными (будет сериализован в JSON)
            qos: Quality of Service (0, 1, 2)
        """
        if not self.client or not self._connected:
            logger.warning(f"MQTT не подключен, не могу опубликовать в {topic}")
            return
        
        try:
            message = json.dumps(payload)
            result = self.client.publish(topic, message, qos=qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Опубликовано в {topic}: {payload}")
            else:
                logger.error(f"Ошибка публикации в {topic}: {result.rc}")
                
        except Exception as e:
            logger.error(f"Ошибка публикации в {topic}: {e}")
    
    def is_connected(self) -> bool:
        """Проверка подключения"""
        return self._connected


