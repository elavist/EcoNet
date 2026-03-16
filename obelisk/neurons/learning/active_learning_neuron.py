"""
Нейрон активного обучения ЭкоНет
Активное обучение на основе данных
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import ComponentState

logger = logging.getLogger(__name__)


class ActiveLearningNeuron(NeuralNode):
    """
    Нейрон активного обучения - выбор данных для обучения
    """
    
    def __init__(self, active_learner=None):
        """
        Инициализация ActiveLearningNeuron
        
        Args:
            active_learner: ActiveLearner сервис
        """
        super().__init__("active_learning_neuron", "learning")
        self.active_learner = active_learner
        self.samples_selected = 0
        self.state = ComponentState.READY
        
        logger.info("📚 ActiveLearningNeuron создан")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Процесс мышления нейрона активного обучения"""
        detections = context.get("detections", [])
        frame = context.get("frame")
        
        if not detections or frame is None:
            return {
                "action": "skip",
                "reason": "Нет данных для обучения",
                "confidence": 0.0
            }
        
        if not self.active_learner:
            return {
                "action": "skip",
                "reason": "ActiveLearner недоступен",
                "confidence": 0.0
            }
        
        try:
            # Выбор образцов для обучения
            should_learn = await self.active_learner.should_learn(frame, detections)
            
            if should_learn:
                self.samples_selected += 1
                return {
                    "action": "learn",
                    "should_learn": True,
                    "confidence": 0.8,
                    "samples_selected": self.samples_selected
                }
            else:
                return {
                    "action": "skip_learning",
                    "should_learn": False,
                    "confidence": 0.3
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка активного обучения: {e}")
            return {
                "action": "error",
                "error": str(e),
                "confidence": 0.0
            }

