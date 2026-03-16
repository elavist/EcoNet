"""
Принятие решений ЭкоНет
Высший уровень принятия решений на основе коллективного разума
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from obelisk.brain.collective_mind import CollectiveMind

logger = logging.getLogger(__name__)


class DecisionMaker:
    """
    Принятие решений на основе коллективного разума
    """
    
    def __init__(self, collective_mind: CollectiveMind):
        """
        Инициализация DecisionMaker
        
        Args:
            collective_mind: Коллективный разум
        """
        self.collective_mind = collective_mind
        self.decision_history = []
        
        logger.info("🎯 DecisionMaker инициализирован")
    
    async def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Принятие решения на основе коллективного разума
        
        Args:
            context: Контекст для принятия решения
        
        Returns:
            Решение
        """
        logger.info("🤔 Начало процесса принятия решения...")
        
        # Получение решения от коллективного разума
        decision = await self.collective_mind.think(context)
        
        # Сохранение в историю
        self.decision_history.append({
            "decision": decision,
            "context": context,
            "timestamp": datetime.now()
        })
        
        logger.info(f"✅ Решение принято: {decision.get('action', 'unknown')}")
        
        return decision
    
    def get_decision_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получение истории решений"""
        return self.decision_history[-limit:]

