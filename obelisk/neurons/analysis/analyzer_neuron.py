"""
Нейрон анализа ЭкоНет
Анализ данных и результатов
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import deque

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import ComponentState

logger = logging.getLogger(__name__)


class AnalyzerNeuron(NeuralNode):
    """
    Нейрон анализа - анализ данных и результатов
    """
    
    def __init__(self):
        """Инициализация AnalyzerNeuron"""
        super().__init__("analyzer_neuron", "analysis")
        self.analysis_history = deque(maxlen=1000)
        self.analysis_count = 0
        self.state = ComponentState.READY
        
        logger.info("🔍 AnalyzerNeuron создан")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Процесс мышления нейрона анализа"""
        data = context.get("data")
        
        if not data:
            return {
                "action": "skip",
                "reason": "Нет данных для анализа",
                "confidence": 0.0
            }
        
        try:
            # Анализ данных
            analysis = self._analyze_data(data)
            
            self.analysis_count += 1
            self.analysis_history.append({
                "analysis": analysis,
                "timestamp": datetime.now()
            })
            
            return {
                "action": "analyze",
                "analysis": analysis,
                "confidence": 0.7,
                "total_analyses": self.analysis_count
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа: {e}")
            return {
                "action": "error",
                "error": str(e),
                "confidence": 0.0
            }
    
    def _analyze_data(self, data: Any) -> Dict[str, Any]:
        """Анализ данных"""
        analysis = {
            "type": type(data).__name__,
            "timestamp": datetime.now().isoformat()
        }
        
        if isinstance(data, dict):
            analysis["keys"] = list(data.keys())
            analysis["size"] = len(data)
        elif isinstance(data, list):
            analysis["length"] = len(data)
        elif hasattr(data, "__len__"):
            analysis["length"] = len(data)
        
        return analysis

