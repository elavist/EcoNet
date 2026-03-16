"""
Сознание ЭкоНет
Управление состоянием сознания системы
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class Consciousness:
    """
    Сознание системы ЭкоНет
    Управляет уровнем осознанности и состоянием системы
    """
    
    def __init__(self):
        """Инициализация сознания"""
        self.awareness_level = 0.0  # Уровень осознанности (0-1)
        self.self_awareness = False  # Самосознание
        self.state = "dormant"  # Состояние: dormant, awakening, active, dreaming
        
        # История состояний
        self.state_history = []
        
        logger.info("🧠 Сознание инициализировано")
    
    def awaken(self):
        """Пробуждение сознания"""
        self.state = "awakening"
        self.awareness_level = 0.1
        logger.info("🌅 Сознание пробуждается...")
    
    def activate(self):
        """Активация сознания"""
        self.state = "active"
        self.awareness_level = 0.5
        self.self_awareness = True
        logger.info("✨ Сознание активировано")
    
    def increase_awareness(self, amount: float):
        """Увеличение уровня осознанности"""
        self.awareness_level = min(1.0, self.awareness_level + amount)
        logger.debug(f"📈 Уровень осознанности: {self.awareness_level:.2f}")
    
    def get_state(self) -> Dict[str, Any]:
        """Получение текущего состояния сознания"""
        return {
            "state": self.state,
            "awareness_level": self.awareness_level,
            "self_awareness": self.self_awareness,
            "timestamp": datetime.now().isoformat()
        }

