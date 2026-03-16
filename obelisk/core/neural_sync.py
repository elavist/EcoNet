"""
Архитектура мышления AI - Нейронные связи
Синхронизация и общение между компонентами ЭкоНет
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import threading
from collections import deque

logger = logging.getLogger(__name__)


class ComponentState(Enum):
    """Состояния компонентов"""
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    PAUSED = "paused"


class NeuralConnection:
    """
    Нейронная связь между компонентами
    Обеспечивает общение и синхронизацию
    """
    
    def __init__(self, source: str, target: str, connection_type: str = "data"):
        """
        Args:
            source: Источник данных
            target: Получатель данных
            connection_type: Тип связи (data, signal, feedback)
        """
        self.source = source
        self.target = target
        self.connection_type = connection_type
        self.callbacks: List[Callable] = []
        self.data_buffer = deque(maxlen=100)  # Буфер последних данных
        self.active = True
    
    def send(self, data: Any):
        """Отправка данных через связь"""
        if not self.active:
            return
        
        # Сохранение в буфер
        self.data_buffer.append({
            "data": data,
            "timestamp": datetime.now(),
            "source": self.source
        })
        
        # Вызов всех callback'ов
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(data))
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Ошибка в callback связи {self.source}->{self.target}: {e}")
    
    def subscribe(self, callback: Callable):
        """Подписка на данные"""
        self.callbacks.append(callback)
    
    def get_latest(self) -> Optional[Any]:
        """Получить последние данные"""
        if self.data_buffer:
            return self.data_buffer[-1]["data"]
        return None


class NeuralNetwork:
    """
    Нейронная сеть компонентов ЭкоНет
    Управляет связями и синхронизацией
    """
    
    def __init__(self):
        self.components: Dict[str, Any] = {}  # Компоненты системы
        self.connections: Dict[str, NeuralConnection] = {}  # Связи между компонентами
        self.states: Dict[str, ComponentState] = {}  # Состояния компонентов
        self.sync_lock = threading.Lock()
        self.event_loop = None
    
    def register_component(self, name: str, component: Any):
        """Регистрация компонента"""
        with self.sync_lock:
            self.components[name] = component
            self.states[name] = ComponentState.INITIALIZING
            logger.info(f"🧠 Компонент '{name}' зарегистрирован")
    
    def create_connection(self, source: str, target: str, connection_type: str = "data") -> NeuralConnection:
        """Создание нейронной связи"""
        connection_key = f"{source}->{target}"
        connection = NeuralConnection(source, target, connection_type)
        self.connections[connection_key] = connection
        logger.info(f"🔗 Связь создана: {source} -> {target} ({connection_type})")
        return connection
    
    def connect(self, source: str, target: str, callback: Optional[Callable] = None, 
                connection_type: str = "data"):
        """Подключение компонентов с callback"""
        connection_key = f"{source}->{target}"
        
        if connection_key not in self.connections:
            self.create_connection(source, target, connection_type)
        
        connection = self.connections[connection_key]
        
        if callback:
            connection.subscribe(callback)
        
        return connection
    
    def send_signal(self, source: str, target: str, data: Any):
        """Отправка сигнала между компонентами"""
        connection_key = f"{source}->{target}"
        if connection_key in self.connections:
            self.connections[connection_key].send(data)
        else:
            logger.warning(f"Связь {connection_key} не найдена")
    
    def get_connection(self, source: str, target: str) -> Optional[NeuralConnection]:
        """Получить связь"""
        connection_key = f"{source}->{target}"
        return self.connections.get(connection_key)
    
    def set_state(self, component: str, state: ComponentState):
        """Установка состояния компонента"""
        with self.sync_lock:
            old_state = self.states.get(component)
            self.states[component] = state
            logger.info(f"📊 {component}: {old_state} -> {state}")
    
    def get_state(self, component: str) -> ComponentState:
        """Получить состояние компонента"""
        return self.states.get(component, ComponentState.ERROR)
    
    def is_ready(self, component: str) -> bool:
        """Проверка готовности компонента"""
        return self.get_state(component) == ComponentState.READY
    
    def wait_for_ready(self, component: str, timeout: float = 10.0) -> bool:
        """Ожидание готовности компонента"""
        start_time = datetime.now()
        while (datetime.now() - start_time).total_seconds() < timeout:
            if self.is_ready(component):
                return True
            asyncio.sleep(0.1)
        return False
    
    def get_all_connections(self) -> Dict[str, NeuralConnection]:
        """Получить все связи"""
        return self.connections.copy()
    
    def diagnose(self) -> Dict[str, Any]:
        """Диагностика системы"""
        diagnosis = {
            "components": {},
            "connections": {},
            "health": "healthy"
        }
        
        # Диагностика компонентов
        for name, component in self.components.items():
            state = self.get_state(name)
            diagnosis["components"][name] = {
                "state": state.value,
                "ready": state == ComponentState.READY,
                "registered": True
            }
        
        # Диагностика связей
        for key, connection in self.connections.items():
            diagnosis["connections"][key] = {
                "active": connection.active,
                "buffer_size": len(connection.data_buffer),
                "subscribers": len(connection.callbacks)
            }
        
        # Общее здоровье
        error_count = sum(1 for s in self.states.values() if s == ComponentState.ERROR)
        if error_count > 0:
            diagnosis["health"] = "error"
        elif any(s == ComponentState.INITIALIZING for s in self.states.values()):
            diagnosis["health"] = "initializing"
        
        return diagnosis


# Глобальный экземпляр нейронной сети
_neural_network: Optional[NeuralNetwork] = None


def get_neural_network() -> NeuralNetwork:
    """Получить глобальный экземпляр нейронной сети"""
    global _neural_network
    if _neural_network is None:
        _neural_network = NeuralNetwork()
    return _neural_network


def reset_neural_network():
    """Сброс нейронной сети (для тестирования)"""
    global _neural_network
    _neural_network = None

