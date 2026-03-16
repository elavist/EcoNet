"""
Архитектура из 4 специальных нейронов ЭкоНет
1. YOLO-нейрон - соединен с YOLO
2. DeepSeek-нейрон - соединен с DeepSeek
3. Координатор-нейрон - соединен с TaskManager/Coordinator
4. Хаб-информации - центральный узел синхронизации

Каждый нейрон может быть связан с узлом полевой архитектуры (FieldNode),
что позволяет учитывать поле эффективности при принятии решений.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
from datetime import datetime
from collections import deque
import threading

from obelisk.core.neural_sync import NeuralConnection, ComponentState

if TYPE_CHECKING:
    from obelisk.swarm.field_node import FieldNode

logger = logging.getLogger(__name__)


class NeuralNode:
    """
    Базовый класс для нейронного узла
    Обеспечивает коммуникацию и синхронизацию
    """
    
    def __init__(self, name: str, node_type: str):
        """
        Инициализация нейронного узла
        
        Args:
            name: Имя узла
            node_type: Тип узла (yolo, deepseek, coordinator, hub)
        """
        self.name = name
        self.node_type = node_type
        self.state = ComponentState.INITIALIZING
        
        # Связи с другими узлами
        self.incoming_connections: Dict[str, NeuralConnection] = {}
        self.outgoing_connections: Dict[str, NeuralConnection] = {}
        
        # Буфер данных
        self.data_buffer = deque(maxlen=1000)
        self.message_queue = asyncio.Queue(maxsize=1000)
        
        # Блокировки
        self.lock = threading.Lock()
        
        # Связь с полевой архитектурой роя
        self._field_node: Optional["FieldNode"] = None
        
        # Статистика
        self.messages_received = 0
        self.messages_sent = 0
        self.last_activity = datetime.now()
        
        logger.info(f"🧠 Нейронный узел '{name}' ({node_type}) создан")
    
    def connect_to(self, target: 'NeuralNode', connection: NeuralConnection):
        """Подключение к целевому узлу"""
        self.outgoing_connections[target.name] = connection
        target.incoming_connections[self.name] = connection
        logger.info(f"🔗 {self.name} -> {target.name}")
    
    def receive(self, data: Any, source: str = "unknown"):
        """Прием данных от источника"""
        with self.lock:
            self.data_buffer.append({
                "data": data,
                "source": source,
                "timestamp": datetime.now()
            })
            self.messages_received += 1
            self.last_activity = datetime.now()
            
            try:
                self.message_queue.put_nowait({
                    "data": data,
                    "source": source,
                    "timestamp": datetime.now()
                })
            except asyncio.QueueFull:
                # Очистка старых сообщений
                try:
                    self.message_queue.get_nowait()
                    self.message_queue.put_nowait({
                        "data": data,
                        "source": source,
                        "timestamp": datetime.now()
                    })
                except asyncio.QueueEmpty:
                    pass
    
    def send(self, data: Any, target: str):
        """Отправка данных целевому узлу"""
        if target in self.outgoing_connections:
            connection = self.outgoing_connections[target]
            connection.send(data)
            self.messages_sent += 1
            self.last_activity = datetime.now()
    
    def broadcast(self, data: Any):
        """Широковещательная отправка всем подключенным узлам"""
        for target, connection in self.outgoing_connections.items():
            connection.send(data)
        self.messages_sent += len(self.outgoing_connections)
        self.last_activity = datetime.now()
    
    def get_latest(self) -> Optional[Any]:
        """Получить последние данные"""
        if self.data_buffer:
            return self.data_buffer[-1]["data"]
        return None
    
    def set_state(self, state: ComponentState):
        """Установка состояния"""
        with self.lock:
            old_state = self.state
            self.state = state
            logger.info(f"📊 {self.name}: {old_state.value} -> {state.value}")

    # ------------------------------------------------------------------
    # Интеграция с полевой архитектурой
    # ------------------------------------------------------------------

    def bind_field_node(self, field_node: "FieldNode"):
        """Привязать нейрон к узлу полевой архитектуры."""
        self._field_node = field_node
        logger.info(f"🌐 {self.name} привязан к полевому узлу '{field_node.node_id}'")

    @property
    def field_node(self) -> Optional["FieldNode"]:
        return self._field_node

    @property
    def field_efficiency(self) -> float:
        """Эффективность связанного полевого узла."""
        return self._field_node.efficiency if self._field_node else 0.0

    @property
    def field_potential(self) -> float:
        """Потенциал нагрузки связанного полевого узла."""
        return self._field_node.potential if self._field_node else 0.0

    def update_field_state(self, *, resources: float = None, compute: float = None,
                           bandwidth: float = None, tasks: float = None):
        """Обновить параметры связанного полевого узла из нейрона."""
        if not self._field_node:
            return
        if resources is not None:
            self._field_node.resources = resources
        if compute is not None:
            self._field_node.compute = compute
        if bandwidth is not None:
            self._field_node.bandwidth = bandwidth
        if tasks is not None:
            self._field_node.tasks = tasks


class YOLONeuron(NeuralNode):
    """
    YOLO-нейрон
    Соединен с ModelEngine для детекции объектов
    """
    
    def __init__(self, model_engine):
        super().__init__("yolo_neuron", "yolo")
        self.model_engine = model_engine
        self.detections_buffer = deque(maxlen=100)
        self.set_state(ComponentState.READY)
    
    async def process_frame(self, frame) -> List[Dict]:
        """Обработка кадра через YOLO"""
        if not self.model_engine:
            return []
        
        try:
            self.set_state(ComponentState.PROCESSING)
            detections = await self.model_engine.detect_frame(frame)
            
            # Сохранение в буфер
            self.detections_buffer.append({
                "detections": detections,
                "timestamp": datetime.now()
            })
            
            # Отправка через нейронную сеть
            self.broadcast({
                "type": "detections",
                "data": detections,
                "source": self.name
            })
            
            self.set_state(ComponentState.READY)
            return detections
            
        except Exception as e:
            logger.error(f"Ошибка в YOLO-нейроне: {e}", exc_info=True)
            self.set_state(ComponentState.ERROR)
            return []


class DeepSeekNeuron(NeuralNode):
    """
    DeepSeek-нейрон (опциональный)
    Соединен с LLM Engine (DeepSeek) для обработки текста и размышлений.
    Если LLM Engine не предоставлен, нейрон переходит в режим PAUSED.
    """
    
    def __init__(self, llm_engine):
        super().__init__("deepseek_neuron", "deepseek")
        self.llm_engine = llm_engine
        self.conversation_buffer = deque(maxlen=200)
        self.thinking_buffer = deque(maxlen=100)
        if self.llm_engine:
            self.set_state(ComponentState.READY)
        else:
            self.set_state(ComponentState.PAUSED)
            logger.info("DeepSeek-нейрон создан в режиме PAUSED (LLM не подключён)")

    @property
    def available(self) -> bool:
        return self.llm_engine is not None

    async def process_message(self, message: str, context: Optional[Dict] = None) -> str:
        """Обработка сообщения через DeepSeek"""
        if not self.llm_engine:
            return ""
        
        try:
            self.set_state(ComponentState.PROCESSING)
            response = await self.llm_engine.process_message(message, context)
            
            self.conversation_buffer.append({
                "message": message,
                "response": response,
                "timestamp": datetime.now()
            })
            
            self.broadcast({
                "type": "llm_response",
                "data": response,
                "source": self.name,
                "original_message": message
            })
            
            self.set_state(ComponentState.READY)
            return response
            
        except Exception as e:
            logger.error(f"Ошибка в DeepSeek-нейроне: {e}", exc_info=True)
            self.set_state(ComponentState.ERROR)
            return f"Ошибка обработки: {e}"
    
    async def think(self, prompt: str) -> str:
        """Режим размышления (thinking mode)"""
        if not self.llm_engine:
            return ""
        
        try:
            thinking = await self.llm_engine.think(prompt)
            
            self.thinking_buffer.append({
                "prompt": prompt,
                "thinking": thinking,
                "timestamp": datetime.now()
            })
            
            self.broadcast({
                "type": "thinking",
                "data": thinking,
                "source": self.name
            })
            
            return thinking
            
        except Exception as e:
            logger.error(f"Ошибка размышления: {e}", exc_info=True)
            return ""


class CoordinatorNeuron(NeuralNode):
    """
    Координатор-нейрон
    Соединен с TaskManager для координации задач и управления системой
    """
    
    def __init__(self, task_manager):
        super().__init__("coordinator_neuron", "coordinator")
        self.task_manager = task_manager
        self.tasks_buffer = deque(maxlen=200)
        self.set_state(ComponentState.READY)
    
    async def create_task(self, task_data: Dict) -> str:
        """Создание новой задачи"""
        if not self.task_manager:
            return ""
        
        try:
            self.set_state(ComponentState.PROCESSING)
            task_id = await self.task_manager.create_task(task_data)
            
            # Сохранение в буфер
            self.tasks_buffer.append({
                "task_id": task_id,
                "task_data": task_data,
                "timestamp": datetime.now()
            })
            
            # Отправка через нейронную сеть
            self.broadcast({
                "type": "task_created",
                "data": {"task_id": task_id, "task_data": task_data},
                "source": self.name
            })
            
            self.set_state(ComponentState.READY)
            return task_id
            
        except Exception as e:
            logger.error(f"Ошибка в Coordinator-нейроне: {e}", exc_info=True)
            self.set_state(ComponentState.ERROR)
            return ""
    
    async def get_task_status(self, task_id: str) -> Dict:
        """Получение статуса задачи"""
        if not self.task_manager:
            return {}
        
        try:
            status = await self.task_manager.get_task_status(task_id)
            
            # Отправка статуса
            self.broadcast({
                "type": "task_status",
                "data": {"task_id": task_id, "status": status},
                "source": self.name
            })
            
            return status
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса задачи: {e}", exc_info=True)
            return {}


class InformationHubNeuron(NeuralNode):
    """
    Хаб-информации (центральный узел)
    Собирает, синхронизирует и распределяет информацию между всеми узлами
    """
    
    def __init__(self):
        super().__init__("information_hub", "hub")
        
        # Хранилище информации
        self.info_store: Dict[str, Any] = {}
        self.info_history = deque(maxlen=1000)
        
        # Индексы по типам информации
        self.info_by_type: Dict[str, List[Dict]] = {
            "detections": [],
            "llm_responses": [],
            "tasks": [],
            "thinking": [],
            "system_events": []
        }
        
        # Подписчики на типы информации
        self.subscribers: Dict[str, List[Callable]] = {}
        
        self.set_state(ComponentState.READY)
    
    def store_info(self, info_type: str, data: Any, source: str = "unknown"):
        """Сохранение информации в хаб"""
        info_entry = {
            "type": info_type,
            "data": data,
            "source": source,
            "timestamp": datetime.now()
        }
        
        # Сохранение в общее хранилище
        key = f"{info_type}_{len(self.info_history)}"
        self.info_store[key] = info_entry
        self.info_history.append(info_entry)
        
        # Сохранение по типу
        if info_type in self.info_by_type:
            self.info_by_type[info_type].append(info_entry)
            # Ограничение размера (последние 100)
            if len(self.info_by_type[info_type]) > 100:
                self.info_by_type[info_type].pop(0)
        
        # Уведомление подписчиков
        if info_type in self.subscribers:
            for callback in self.subscribers[info_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(info_entry))
                    else:
                        callback(info_entry)
                except Exception as e:
                    logger.error(f"Ошибка в подписчике {info_type}: {e}")
        
        # Автоматическая обработка входящих данных
        self._process_incoming_data(info_entry)
    
    def _process_incoming_data(self, info_entry: Dict):
        """Автоматическая обработка входящих данных"""
        info_type = info_entry.get("type")
        data = info_entry.get("data")
        
        if info_type == "detections":
            # Детекции: отправляем в DeepSeek для анализа
            self.broadcast({
                "type": "detections_for_analysis",
                "data": data,
                "source": self.name
            })
        
        elif info_type == "llm_response":
            # Ответы LLM: сохраняем и синхронизируем
            self.broadcast({
                "type": "llm_response_synced",
                "data": data,
                "source": self.name
            })
        
        elif info_type == "task_created":
            # Новые задачи: уведомляем все узлы
            self.broadcast({
                "type": "task_notification",
                "data": data,
                "source": self.name
            })
    
    def subscribe(self, info_type: str, callback: Callable):
        """Подписка на тип информации"""
        if info_type not in self.subscribers:
            self.subscribers[info_type] = []
        self.subscribers[info_type].append(callback)
    
    def get_info(self, info_type: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Получение информации"""
        if info_type:
            return list(self.info_by_type.get(info_type, []))[-limit:]
        return list(self.info_history)[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики хаба"""
        stats = {
            "total_info": len(self.info_history),
            "info_by_type": {k: len(v) for k, v in self.info_by_type.items()},
            "subscribers": {k: len(v) for k, v in self.subscribers.items()},
            "connections": {
                "incoming": len(self.incoming_connections),
                "outgoing": len(self.outgoing_connections)
            },
            "messages_received": self.messages_received,
            "messages_sent": self.messages_sent,
            "last_activity": self.last_activity.isoformat()
        }
        if self._field_node:
            stats["field"] = {
                "efficiency": round(self._field_node.efficiency, 4),
                "potential": round(self._field_node.potential, 4),
                "degree": self._field_node.degree,
            }
        return stats
    
    # Переопределение receive для автоматической обработки
    def receive(self, data: Any, source: str = "unknown"):
        """Прием данных с автоматической обработкой"""
        super().receive(data, source)
        
        # Если данные в формате хаба, обрабатываем
        if isinstance(data, dict) and "type" in data:
            self.store_info(data["type"], data.get("data"), source)


class NeuralNetworkArchitecture:
    """
    Архитектура нейронной сети из 4 узлов
    Управляет связями и синхронизацией
    """
    
    def __init__(self):
        self.yolo_neuron: Optional[YOLONeuron] = None
        self.deepseek_neuron: Optional[DeepSeekNeuron] = None
        self.coordinator_neuron: Optional[CoordinatorNeuron] = None
        self.hub_neuron: Optional[InformationHubNeuron] = None
        
        self.connections: Dict[str, NeuralConnection] = {}
    
    def create_architecture(self, model_engine, llm_engine, task_manager):
        """Создание архитектуры с 4 нейронами"""
        # 1. Создание узлов
        self.yolo_neuron = YOLONeuron(model_engine)
        self.deepseek_neuron = DeepSeekNeuron(llm_engine)
        self.coordinator_neuron = CoordinatorNeuron(task_manager)
        self.hub_neuron = InformationHubNeuron()
        
        # 2. Создание связей
        # YOLO -> Hub
        conn1 = NeuralConnection("yolo_neuron", "information_hub", "data")
        self.yolo_neuron.connect_to(self.hub_neuron, conn1)
        self.connections["yolo->hub"] = conn1
        
        # DeepSeek -> Hub
        conn2 = NeuralConnection("deepseek_neuron", "information_hub", "data")
        self.deepseek_neuron.connect_to(self.hub_neuron, conn2)
        self.connections["deepseek->hub"] = conn2
        
        # Coordinator -> Hub
        conn3 = NeuralConnection("coordinator_neuron", "information_hub", "data")
        self.coordinator_neuron.connect_to(self.hub_neuron, conn3)
        self.connections["coordinator->hub"] = conn3
        
        # Hub -> YOLO (обратная связь)
        conn4 = NeuralConnection("information_hub", "yolo_neuron", "feedback")
        self.hub_neuron.connect_to(self.yolo_neuron, conn4)
        self.connections["hub->yolo"] = conn4
        
        # Hub -> DeepSeek (обратная связь)
        conn5 = NeuralConnection("information_hub", "deepseek_neuron", "feedback")
        self.hub_neuron.connect_to(self.deepseek_neuron, conn5)
        self.connections["hub->deepseek"] = conn5
        
        # Hub -> Coordinator (обратная связь)
        conn6 = NeuralConnection("information_hub", "coordinator_neuron", "feedback")
        self.hub_neuron.connect_to(self.coordinator_neuron, conn6)
        self.connections["hub->coordinator"] = conn6
        
        # Прямые связи между узлами
        # YOLO -> DeepSeek (детекции для анализа)
        conn7 = NeuralConnection("yolo_neuron", "deepseek_neuron", "data")
        self.yolo_neuron.connect_to(self.deepseek_neuron, conn7)
        self.connections["yolo->deepseek"] = conn7
        
        # DeepSeek -> Coordinator (команды управления)
        conn8 = NeuralConnection("deepseek_neuron", "coordinator_neuron", "signal")
        self.deepseek_neuron.connect_to(self.coordinator_neuron, conn8)
        self.connections["deepseek->coordinator"] = conn8
        
        # Coordinator -> YOLO (управление детекцией)
        conn9 = NeuralConnection("coordinator_neuron", "yolo_neuron", "signal")
        self.coordinator_neuron.connect_to(self.yolo_neuron, conn9)
        self.connections["coordinator->yolo"] = conn9
        
        logger.info("✅ Нейронная архитектура создана: 4 узла, 9 связей")
        
        # Настройка подписок хаба
        self._setup_hub_subscriptions()
    
    def _setup_hub_subscriptions(self):
        """Настройка подписок хаба на данные от узлов"""
        # Хаб подписывается на все типы данных
        if self.hub_neuron:
            # Подписка на детекции от YOLO
            if "yolo->hub" in self.connections:
                self.connections["yolo->hub"].subscribe(
                    lambda data: self.hub_neuron.store_info("detections", data, "yolo_neuron")
                )
            
            # Подписка на ответы от DeepSeek
            if "deepseek->hub" in self.connections:
                self.connections["deepseek->hub"].subscribe(
                    lambda data: self.hub_neuron.store_info("llm_responses", data, "deepseek_neuron")
                )
            
            # Подписка на задачи от Coordinator
            if "coordinator->hub" in self.connections:
                self.connections["coordinator->hub"].subscribe(
                    lambda data: self.hub_neuron.store_info("tasks", data, "coordinator_neuron")
                )
    
    def get_all_nodes(self) -> Dict[str, NeuralNode]:
        """Получить все узлы"""
        return {
            "yolo": self.yolo_neuron,
            "deepseek": self.deepseek_neuron,
            "coordinator": self.coordinator_neuron,
            "hub": self.hub_neuron
        }
    
    def diagnose(self) -> Dict[str, Any]:
        """Диагностика архитектуры"""
        diagnosis = {
            "nodes": {},
            "connections": {},
            "health": "healthy"
        }
        
        # Диагностика узлов
        if self.yolo_neuron:
            diagnosis["nodes"]["yolo"] = {
                "state": self.yolo_neuron.state.value,
                "messages_received": self.yolo_neuron.messages_received,
                "messages_sent": self.yolo_neuron.messages_sent
            }
        
        if self.deepseek_neuron:
            diagnosis["nodes"]["deepseek"] = {
                "state": self.deepseek_neuron.state.value,
                "messages_received": self.deepseek_neuron.messages_received,
                "messages_sent": self.deepseek_neuron.messages_sent
            }
        
        if self.coordinator_neuron:
            diagnosis["nodes"]["coordinator"] = {
                "state": self.coordinator_neuron.state.value,
                "messages_received": self.coordinator_neuron.messages_received,
                "messages_sent": self.coordinator_neuron.messages_sent
            }
        
        if self.hub_neuron:
            diagnosis["nodes"]["hub"] = {
                "state": self.hub_neuron.state.value,
                "statistics": self.hub_neuron.get_statistics()
            }
        
        # Диагностика связей
        for name, conn in self.connections.items():
            diagnosis["connections"][name] = {
                "active": conn.active,
                "buffer_size": len(conn.data_buffer),
                "subscribers": len(conn.callbacks)
            }
        
        # Полевая архитектура
        all_nodes = [self.yolo_neuron, self.deepseek_neuron,
                     self.coordinator_neuron, self.hub_neuron]
        for node in all_nodes:
            if node and node.field_node:
                if "field" not in diagnosis:
                    diagnosis["field"] = {}
                diagnosis["field"][node.name] = {
                    "efficiency": round(node.field_efficiency, 4),
                    "potential": round(node.field_potential, 4),
                }
        
        # Общее здоровье
        error_count = sum(1 for node in all_nodes
                         if node and node.state == ComponentState.ERROR)
        
        if error_count > 0:
            diagnosis["health"] = "error"
        elif any(node and node.state == ComponentState.INITIALIZING 
                for node in all_nodes):
            diagnosis["health"] = "initializing"
        
        return diagnosis

