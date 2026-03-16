"""
Нейрон опыта ЭкоНет
Хранение и использование опыта системы
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import ComponentState

logger = logging.getLogger(__name__)


class ExperienceNeuron(NeuralNode):
    """
    Нейрон опыта - накопление и использование опыта
    """
    
    def __init__(self, database=None):
        """
        Инициализация ExperienceNeuron
        
        Args:
            database: Database сервис для хранения опыта
        """
        super().__init__("experience_neuron", "memory")
        self.database = database
        self.experiences = deque(maxlen=10000)  # Краткосрочная память
        self.experience_count = 0
        self.state = ComponentState.READY
        
        logger.info("🧠 ExperienceNeuron создан")
    
    def store_experience(self, experience: Dict[str, Any]):
        """Сохранение опыта"""
        experience_with_timestamp = {
            **experience,
            "timestamp": datetime.now(),
            "id": self.experience_count
        }
        
        self.experiences.append(experience_with_timestamp)
        self.experience_count += 1
        
        # Сохранение в базу данных если доступна
        if self.database:
            try:
                self.database.store_experience(experience_with_timestamp)
            except Exception as e:
                logger.warning(f"⚠️ Не удалось сохранить опыт в БД: {e}")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Процесс мышления на основе опыта"""
        # Поиск похожего опыта
        similar_experiences = self._find_similar_experiences(context)
        
        if similar_experiences:
            # Использование опыта для принятия решения
            best_experience = similar_experiences[0]
            
            return {
                "action": "use_experience",
                "experience": best_experience,
                "similar_count": len(similar_experiences),
                "confidence": 0.7
            }
        else:
            return {
                "action": "learn_new",
                "reason": "Нет похожего опыта",
                "confidence": 0.3
            }
    
    def _find_similar_experiences(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Поиск похожего опыта"""
        # Простой поиск по ключевым словам
        context_keys = set(context.keys())
        similar = []
        
        for experience in self.experiences:
            exp_keys = set(experience.keys())
            # Если есть пересечение ключей
            if context_keys & exp_keys:
                similar.append(experience)
        
        return similar[:5]  # Возвращаем топ-5
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики опыта"""
        return {
            "total_experiences": self.experience_count,
            "stored_experiences": len(self.experiences),
            "database_available": self.database is not None
        }

