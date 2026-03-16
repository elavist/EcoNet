"""
Нейрон краткосрочной памяти ЭкоНет
Краткосрочное хранение информации
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque

from obelisk.core.neural_nodes import NeuralNode
from obelisk.core.neural_sync import ComponentState

logger = logging.getLogger(__name__)


class ShortTermMemoryNeuron(NeuralNode):
    """
    Нейрон краткосрочной памяти - хранение информации на короткое время
    """
    
    def __init__(self, max_size: int = 1000, retention_time: int = 300):
        """
        Инициализация ShortTermMemoryNeuron
        
        Args:
            max_size: Максимальный размер памяти
            retention_time: Время хранения в секундах (по умолчанию 5 минут)
        """
        super().__init__("short_term_memory_neuron", "memory")
        self.memory = deque(maxlen=max_size)
        self.retention_time = retention_time
        self.state = ComponentState.READY
        
        logger.info("💭 ShortTermMemoryNeuron создан")
    
    def store(self, key: str, value: Any):
        """Сохранение в краткосрочную память"""
        self.memory.append({
            "key": key,
            "value": value,
            "timestamp": datetime.now()
        })
        logger.debug(f"💾 Сохранено в краткосрочную память: {key}")
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Получение из краткосрочной памяти"""
        # Поиск с конца (последние записи)
        for item in reversed(self.memory):
            if item["key"] == key:
                # Проверка времени хранения
                age = (datetime.now() - item["timestamp"]).total_seconds()
                if age < self.retention_time:
                    return item["value"]
                else:
                    # Удаление устаревших записей
                    self.memory.remove(item)
        
        return None
    
    def cleanup_old(self):
        """Очистка устаревших записей"""
        now = datetime.now()
        to_remove = []
        
        for item in self.memory:
            age = (now - item["timestamp"]).total_seconds()
            if age > self.retention_time:
                to_remove.append(item)
        
        for item in to_remove:
            if item in self.memory:
                self.memory.remove(item)
        
        if to_remove:
            logger.debug(f"🧹 Очищено {len(to_remove)} устаревших записей")
    
    async def think(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Процесс мышления нейрона краткосрочной памяти"""
        action = context.get("action", "store")
        key = context.get("key")
        value = context.get("value")
        
        if action == "store" and key and value:
            self.store(key, value)
            return {
                "action": "stored",
                "key": key,
                "confidence": 1.0
            }
        elif action == "retrieve" and key:
            retrieved = self.retrieve(key)
            return {
                "action": "retrieved",
                "key": key,
                "value": retrieved,
                "found": retrieved is not None,
                "confidence": 1.0 if retrieved else 0.0
            }
        elif action == "cleanup":
            self.cleanup_old()
            return {
                "action": "cleaned",
                "confidence": 1.0
            }
        else:
            return {
                "action": "skip",
                "reason": "Неизвестное действие",
                "confidence": 0.0
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получение статистики памяти"""
        return {
            "size": len(self.memory),
            "max_size": self.memory.maxlen,
            "retention_time": self.retention_time
        }

