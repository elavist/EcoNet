"""
Строитель нейронной сети ЭкоНет
Создает и связывает все нейроны в единую систему
"""

import logging
from typing import Dict, Any, Optional

from obelisk.core.neural_sync import NeuralConnection, get_neural_network
from obelisk.brain.collective_mind import CollectiveMind
from obelisk.neurons.perception.vision_neuron import VisionNeuron
from obelisk.neurons.perception.detection_neuron import DetectionNeuron
from obelisk.neurons.perception.tracking_neuron import TrackingNeuron
from obelisk.neurons.coordination.task_coordinator_neuron import TaskCoordinatorNeuron
from obelisk.neurons.communication.hub_neuron import HubNeuron
from obelisk.neurons.memory.experience_neuron import ExperienceNeuron
from obelisk.neurons.memory.short_term_memory_neuron import ShortTermMemoryNeuron
from obelisk.neurons.learning.active_learning_neuron import ActiveLearningNeuron
from obelisk.neurons.analysis.analyzer_neuron import AnalyzerNeuron
from obelisk.neurons.coordination.swarm_coordinator_neuron import SwarmCoordinatorNeuron
from obelisk.neurons.coordination.docker_neuron import DockerNeuron
from obelisk.neurons.communication.mqtt_neuron import MQTTNeuron
from obelisk.veins.gpu_circulatory import GPUCirculatorySystem
from obelisk.veins.gpu_distributor import GPUDistributor
from obelisk.veins.gpu_monitor import GPUMonitor

logger = logging.getLogger(__name__)


class NeuralNetworkBuilder:
    """
    Строитель нейронной сети
    Создает и связывает все нейроны
    """
    
    def __init__(self, unified_engine=None):
        """
        Инициализация строителя
        
        Args:
            unified_engine: UnifiedEngine для доступа к компонентам
        """
        self.unified_engine = unified_engine
        self.collective_mind = CollectiveMind()
        self.neural_network = get_neural_network()
        
        # Нейроны
        self.neurons = {}
        
        # GPU система
        self.gpu_circulatory = GPUCirculatorySystem()
        self.gpu_distributor = GPUDistributor(self.gpu_circulatory)
        self.gpu_monitor = GPUMonitor()
        
        logger.info("🏗️ NeuralNetworkBuilder создан")
    
    def build_network(self):
        """Построение полной нейронной сети"""
        logger.info("🧬 Начало построения нейронной сети...")
        
        # 1. Создание нейронов восприятия
        self._create_perception_neurons()
        
        # 2. Создание нейронов координации
        self._create_coordination_neurons()
        
        # 3. Создание нейронов памяти
        self._create_memory_neurons()
        
        # 4. Создание нейронов коммуникации
        self._create_communication_neurons()
        
        # 5. Создание нейронов обучения
        self._create_learning_neurons()
        
        # 6. Создание нейронов анализа
        self._create_analysis_neurons()
        
        # 7. Создание связей между нейронами
        self._create_connections()
        
        # 6. Регистрация в коллективном разуме
        self._register_in_collective_mind()
        
        logger.info("✅ Нейронная сеть построена")
    
    def _create_perception_neurons(self):
        """Создание нейронов восприятия"""
        vision_context = None
        model_engine = None
        
        if self.unified_engine:
            vision_context = getattr(self.unified_engine, 'vision_context', None)
            model_engine = getattr(self.unified_engine, 'model_engine', None)
        
        # Vision Neuron
        vision_neuron = VisionNeuron(vision_context)
        self.neurons["vision_neuron"] = vision_neuron
        
        # Detection Neuron (использует GPU через model_engine, мониторинг GPU)
        detection_neuron = DetectionNeuron(
            model_engine=model_engine,
            gpu_monitor=self.gpu_monitor
        )
        self.neurons["detection_neuron"] = detection_neuron
        
        # Tracking Neuron (подключен к GPU системе)
        tracking_neuron = TrackingNeuron(
            gpu_circulatory=self.gpu_circulatory,
            gpu_distributor=self.gpu_distributor,
            gpu_monitor=self.gpu_monitor
        )
        self.neurons["tracking_neuron"] = tracking_neuron
        
        logger.info("👁️ Нейроны восприятия созданы (GPU подключен)")
    
    def _create_coordination_neurons(self):
        """Создание нейронов координации"""
        task_manager = None
        mqtt_client = None
        
        if self.unified_engine:
            task_manager = getattr(self.unified_engine, 'task_manager', None)
            mqtt_client = getattr(self.unified_engine, 'mqtt_client', None)
        
        # Task Coordinator Neuron
        task_coordinator = TaskCoordinatorNeuron(task_manager)
        self.neurons["task_coordinator_neuron"] = task_coordinator
        
        # Swarm Coordinator Neuron
        swarm_coordinator = SwarmCoordinatorNeuron(task_manager, mqtt_client)
        self.neurons["swarm_coordinator_neuron"] = swarm_coordinator
        
        # Docker Neuron
        docker_neuron = DockerNeuron()
        self.neurons["docker_neuron"] = docker_neuron
        
        logger.info("📋 Нейроны координации созданы")
    
    def _create_memory_neurons(self):
        """Создание нейронов памяти"""
        database = None
        
        if self.unified_engine:
            database = getattr(self.unified_engine, 'database', None)
        
        # Experience Neuron
        experience_neuron = ExperienceNeuron(database)
        self.neurons["experience_neuron"] = experience_neuron
        
        # Short Term Memory Neuron
        short_term_memory = ShortTermMemoryNeuron()
        self.neurons["short_term_memory_neuron"] = short_term_memory
        
        logger.info("🧠 Нейроны памяти созданы")
    
    def _create_communication_neurons(self):
        """Создание нейронов коммуникации"""
        mqtt_client = None
        
        if self.unified_engine:
            mqtt_client = getattr(self.unified_engine, 'mqtt_client', None)
        
        # Hub Neuron
        hub_neuron = HubNeuron()
        self.neurons["hub_neuron"] = hub_neuron
        
        # MQTT Neuron
        mqtt_neuron = MQTTNeuron(mqtt_client)
        self.neurons["mqtt_neuron"] = mqtt_neuron
        
        logger.info("🌐 Нейроны коммуникации созданы")
    
    def _create_learning_neurons(self):
        """Создание нейронов обучения"""
        active_learner = None
        
        if self.unified_engine:
            active_learner = getattr(self.unified_engine, 'active_learner', None)
        
        # Active Learning Neuron
        active_learning = ActiveLearningNeuron(active_learner)
        self.neurons["active_learning_neuron"] = active_learning
        
        logger.info("📚 Нейроны обучения созданы")
    
    def _create_analysis_neurons(self):
        """Создание нейронов анализа"""
        # Analyzer Neuron
        analyzer = AnalyzerNeuron()
        self.neurons["analyzer_neuron"] = analyzer
        
        logger.info("🔍 Нейроны анализа созданы")
    
    def _create_connections(self):
        """Создание связей между нейронами"""
        # Detection -> Hub
        if "detection_neuron" in self.neurons and "hub_neuron" in self.neurons:
            conn1 = NeuralConnection("detection_neuron", "hub_neuron", "data")
            conn1.target = self.neurons["hub_neuron"]
            self.neurons["detection_neuron"].connect_to(self.neurons["hub_neuron"], conn1)
        
        # Vision -> Hub
        if "vision_neuron" in self.neurons and "hub_neuron" in self.neurons:
            conn2 = NeuralConnection("vision_neuron", "hub_neuron", "data")
            conn2.target = self.neurons["hub_neuron"]
            self.neurons["vision_neuron"].connect_to(self.neurons["hub_neuron"], conn2)
        
        # Hub -> Task Coordinator
        if "hub_neuron" in self.neurons and "task_coordinator_neuron" in self.neurons:
            conn3 = NeuralConnection("hub_neuron", "task_coordinator_neuron", "data")
            conn3.target = self.neurons["task_coordinator_neuron"]
            self.neurons["hub_neuron"].connect_to(self.neurons["task_coordinator_neuron"], conn3)
        
        # Task Coordinator -> Hub (обратная связь)
        if "task_coordinator_neuron" in self.neurons and "hub_neuron" in self.neurons:
            conn4 = NeuralConnection("task_coordinator_neuron", "hub_neuron", "feedback")
            conn4.target = self.neurons["hub_neuron"]
            self.neurons["task_coordinator_neuron"].connect_to(self.neurons["hub_neuron"], conn4)
        
        # Hub -> Experience (сохранение опыта)
        if "hub_neuron" in self.neurons and "experience_neuron" in self.neurons:
            conn5 = NeuralConnection("hub_neuron", "experience_neuron", "data")
            conn5.target = self.neurons["experience_neuron"]
            self.neurons["hub_neuron"].connect_to(self.neurons["experience_neuron"], conn5)
        
        # Hub -> Short Term Memory
        if "hub_neuron" in self.neurons and "short_term_memory_neuron" in self.neurons:
            conn6 = NeuralConnection("hub_neuron", "short_term_memory_neuron", "data")
            conn6.target = self.neurons["short_term_memory_neuron"]
            self.neurons["hub_neuron"].connect_to(self.neurons["short_term_memory_neuron"], conn6)
        
        # Hub -> Active Learning
        if "hub_neuron" in self.neurons and "active_learning_neuron" in self.neurons:
            conn7 = NeuralConnection("hub_neuron", "active_learning_neuron", "data")
            conn7.target = self.neurons["active_learning_neuron"]
            self.neurons["hub_neuron"].connect_to(self.neurons["active_learning_neuron"], conn7)
        
        # Hub -> Analyzer
        if "hub_neuron" in self.neurons and "analyzer_neuron" in self.neurons:
            conn8 = NeuralConnection("hub_neuron", "analyzer_neuron", "data")
            conn8.target = self.neurons["analyzer_neuron"]
            self.neurons["hub_neuron"].connect_to(self.neurons["analyzer_neuron"], conn8)
        
        # Task Coordinator -> Swarm Coordinator
        if "task_coordinator_neuron" in self.neurons and "swarm_coordinator_neuron" in self.neurons:
            conn9 = NeuralConnection("task_coordinator_neuron", "swarm_coordinator_neuron", "data")
            conn9.target = self.neurons["swarm_coordinator_neuron"]
            self.neurons["task_coordinator_neuron"].connect_to(self.neurons["swarm_coordinator_neuron"], conn9)
        
        # Swarm Coordinator -> Hub (обратная связь)
        if "swarm_coordinator_neuron" in self.neurons and "hub_neuron" in self.neurons:
            conn10 = NeuralConnection("swarm_coordinator_neuron", "hub_neuron", "feedback")
            conn10.target = self.neurons["hub_neuron"]
            self.neurons["swarm_coordinator_neuron"].connect_to(self.neurons["hub_neuron"], conn10)
        
        # Docker Neuron -> Hub
        if "docker_neuron" in self.neurons and "hub_neuron" in self.neurons:
            conn11 = NeuralConnection("docker_neuron", "hub_neuron", "data")
            conn11.target = self.neurons["hub_neuron"]
            self.neurons["docker_neuron"].connect_to(self.neurons["hub_neuron"], conn11)
        
        # Hub -> Docker Neuron (обратная связь)
        if "hub_neuron" in self.neurons and "docker_neuron" in self.neurons:
            conn12 = NeuralConnection("hub_neuron", "docker_neuron", "signal")
            conn12.target = self.neurons["docker_neuron"]
            self.neurons["hub_neuron"].connect_to(self.neurons["docker_neuron"], conn12)
        
        # MQTT Neuron -> Hub
        if "mqtt_neuron" in self.neurons and "hub_neuron" in self.neurons:
            conn13 = NeuralConnection("mqtt_neuron", "hub_neuron", "data")
            conn13.target = self.neurons["hub_neuron"]
            self.neurons["mqtt_neuron"].connect_to(self.neurons["hub_neuron"], conn13)
        
        # Hub -> MQTT Neuron (обратная связь)
        if "hub_neuron" in self.neurons and "mqtt_neuron" in self.neurons:
            conn14 = NeuralConnection("hub_neuron", "mqtt_neuron", "signal")
            conn14.target = self.neurons["mqtt_neuron"]
            self.neurons["hub_neuron"].connect_to(self.neurons["mqtt_neuron"], conn14)
        
        # Detection -> MQTT (для отправки детекций через MQTT)
        if "detection_neuron" in self.neurons and "mqtt_neuron" in self.neurons:
            conn15 = NeuralConnection("detection_neuron", "mqtt_neuron", "data")
            conn15.target = self.neurons["mqtt_neuron"]
            self.neurons["detection_neuron"].connect_to(self.neurons["mqtt_neuron"], conn15)
        
        # Detection -> Tracking (детекции для трекинга)
        if "detection_neuron" in self.neurons and "tracking_neuron" in self.neurons:
            conn16 = NeuralConnection("detection_neuron", "tracking_neuron", "data")
            conn16.target = self.neurons["tracking_neuron"]
            self.neurons["detection_neuron"].connect_to(self.neurons["tracking_neuron"], conn16)
        
        # Tracking -> Hub (отслеженные объекты)
        if "tracking_neuron" in self.neurons and "hub_neuron" in self.neurons:
            conn17 = NeuralConnection("tracking_neuron", "hub_neuron", "data")
            conn17.target = self.neurons["hub_neuron"]
            self.neurons["tracking_neuron"].connect_to(self.neurons["hub_neuron"], conn17)
        
        # Tracking -> MQTT (отслеженные объекты для роя)
        if "tracking_neuron" in self.neurons and "mqtt_neuron" in self.neurons:
            conn18 = NeuralConnection("tracking_neuron", "mqtt_neuron", "data")
            conn18.target = self.neurons["mqtt_neuron"]
            self.neurons["tracking_neuron"].connect_to(self.neurons["mqtt_neuron"], conn18)
        
        # Hub -> Tracking (обратная связь)
        if "hub_neuron" in self.neurons and "tracking_neuron" in self.neurons:
            conn19 = NeuralConnection("hub_neuron", "tracking_neuron", "feedback")
            conn19.target = self.neurons["tracking_neuron"]
            self.neurons["hub_neuron"].connect_to(self.neurons["tracking_neuron"], conn19)
        
        logger.info("🔗 Связи между нейронами созданы")
    
    def _register_in_collective_mind(self):
        """Регистрация всех нейронов в коллективном разуме"""
        for name, neuron in self.neurons.items():
            self.collective_mind.register_neuron(name, neuron)
        
        logger.info(f"🧠 {len(self.neurons)} нейронов зарегистрированы в коллективном разуме")
    
    def get_collective_mind(self) -> CollectiveMind:
        """Получение коллективного разума"""
        return self.collective_mind
    
    def get_gpu_system(self) -> Dict[str, Any]:
        """Получение GPU системы"""
        return {
            "circulatory": self.gpu_circulatory,
            "distributor": self.gpu_distributor,
            "monitor": self.gpu_monitor
        }

