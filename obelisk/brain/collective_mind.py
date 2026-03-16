"""
Коллективный разум ЭкоНет
Объединяет все нейроны в единое сознание
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import deque

from obelisk.core.neural_sync import get_neural_network, ComponentState

logger = logging.getLogger(__name__)


class CollectiveMind:
    """
    Коллективный разум ЭкоНет
    Объединяет все нейроны в единое сознание для принятия решений
    """
    
    def __init__(self):
        """Инициализация коллективного разума"""
        self.neural_network = get_neural_network()
        self.neurons = {}  # Все зарегистрированные нейроны
        self.consciousness_level = 0.0  # Уровень сознания (0-1)
        self.collective_memory = deque(maxlen=10000)  # Коллективная память
        self.decisions_history = deque(maxlen=1000)  # История решений
        
        # Состояния компонентов
        self.component_states = {}
        
        # Статистика
        self.total_decisions = 0
        self.successful_decisions = 0
        
        logger.info("🧠 Коллективный разум инициализирован")
    
    def register_neuron(self, name: str, neuron: Any):
        """
        Регистрация нейрона в коллективном разуме
        
        Args:
            name: Имя нейрона
            neuron: Экземпляр нейрона
        """
        self.neurons[name] = neuron
        self.neural_network.register_component(name, neuron)
        logger.info(f"🧬 Нейрон '{name}' зарегистрирован в коллективном разуме")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Процесс мышления коллективного разума
        
        Args:
            context: Контекст для принятия решения
        
        Returns:
            Решение коллективного разума
        """
        logger.info("💭 Коллективный разум начинает процесс мышления...")
        
        # Сбор информации от всех нейронов
        neuron_opinions = {}
        for name, neuron in self.neurons.items():
            if hasattr(neuron, 'think') and callable(neuron.think):
                try:
                    opinion = await neuron.think(context)
                    neuron_opinions[name] = opinion
                except Exception as e:
                    logger.warning(f"⚠️ Нейрон '{name}' не смог высказать мнение: {e}")
        
        # Анализ мнений
        decision = self._synthesize_decision(neuron_opinions, context)
        
        # Сохранение в коллективную память
        self.collective_memory.append({
            "context": context,
            "opinions": neuron_opinions,
            "decision": decision,
            "timestamp": datetime.now()
        })
        
        # Обновление истории решений
        self.decisions_history.append(decision)
        self.total_decisions += 1
        
        if decision.get("success"):
            self.successful_decisions += 1
        
        # Обновление уровня сознания
        self._update_consciousness_level()
        
        logger.info(f"✅ Коллективный разум принял решение: {decision.get('action', 'unknown')}")
        
        return decision
    
    def _synthesize_decision(self, opinions: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Синтез решения из мнений нейронов
        
        Args:
            opinions: Мнения нейронов
            context: Контекст
        
        Returns:
            Финальное решение
        """
        # Простой алгоритм синтеза (можно улучшить)
        if not opinions:
            return {
                "action": "wait",
                "reason": "Нет мнений от нейронов",
                "success": False
            }
        
        # Подсчет голосов за каждое действие
        action_votes = {}
        for neuron_name, opinion in opinions.items():
            action = opinion.get("action", "wait")
            confidence = opinion.get("confidence", 0.5)
            
            if action not in action_votes:
                action_votes[action] = 0
            action_votes[action] += confidence
        
        # Выбор действия с максимальным количеством голосов
        if action_votes:
            best_action = max(action_votes.items(), key=lambda x: x[1])
            return {
                "action": best_action[0],
                "confidence": best_action[1] / len(opinions),
                "votes": action_votes,
                "opinions_count": len(opinions),
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "action": "wait",
            "reason": "Недостаточно данных",
            "success": False
        }
    
    def _update_consciousness_level(self):
        """Обновление уровня сознания на основе успешности решений"""
        if self.total_decisions > 0:
            success_rate = self.successful_decisions / self.total_decisions
            # Уровень сознания зависит от успешности решений и количества нейронов
            neuron_factor = min(len(self.neurons) / 20.0, 1.0)  # Максимум при 20+ нейронах
            self.consciousness_level = success_rate * neuron_factor
        else:
            self.consciousness_level = 0.0
    
    def get_consciousness_level(self) -> float:
        """Получение текущего уровня сознания"""
        return self.consciousness_level
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики коллективного разума"""
        return {
            "consciousness_level": self.consciousness_level,
            "total_neurons": len(self.neurons),
            "total_decisions": self.total_decisions,
            "successful_decisions": self.successful_decisions,
            "success_rate": self.successful_decisions / self.total_decisions if self.total_decisions > 0 else 0,
            "memory_size": len(self.collective_memory),
            "decisions_history_size": len(self.decisions_history)
        }

