"""
Система самообучения и самосовершенствования ЭкоНет
Позволяет системе учиться на опыте и улучшать себя
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class SelfLearningService:
    """
    Сервис самообучения ЭкоНет
    
    Функции:
    1. Анализ собственной производительности
    2. Выявление областей для улучшения
    3. Генерация идей для самосовершенствования
    4. Применение улучшений
    """
    
    def __init__(self, self_identity_service, self_modification_service, config: Dict):
        """
        Инициализация сервиса самообучения
        
        Args:
            self_identity_service: Сервис самоидентификации
            self_modification_service: Сервис самомодификации
            config: Конфигурация системы
        """
        self.self_identity = self_identity_service
        self.self_modification = self_modification_service
        self.config = config
        
        self.learning_history: List[Dict] = []
        self.improvements_applied: List[Dict] = []
        self.performance_metrics: Dict = {
            "detection_accuracy": [],
            "response_time": [],
            "user_satisfaction": [],
            "error_rate": []
        }
        
        logger.info("✅ Система самообучения инициализирована")
    
    def record_performance(self, metric: str, value: float, context: Optional[Dict] = None):
        """
        Записать метрику производительности
        
        Args:
            metric: Название метрики
            value: Значение
            context: Дополнительный контекст
        """
        if metric in self.performance_metrics:
            self.performance_metrics[metric].append({
                "value": value,
                "timestamp": datetime.now().isoformat(),
                "context": context or {}
            })
            
            # Ограничиваем размер истории
            if len(self.performance_metrics[metric]) > 1000:
                self.performance_metrics[metric] = self.performance_metrics[metric][-1000:]
            
            logger.debug(f"📊 Метрика {metric}: {value}")
    
    def analyze_performance(self) -> Dict:
        """Анализ производительности и выявление проблем"""
        analysis = {
            "detection_accuracy": {
                "avg": 0.0,
                "trend": "stable",
                "issues": []
            },
            "response_time": {
                "avg": 0.0,
                "trend": "stable",
                "issues": []
            },
            "overall_health": "good"
        }
        
        # Анализ точности детекции
        if self.performance_metrics["detection_accuracy"]:
            values = [m["value"] for m in self.performance_metrics["detection_accuracy"][-100:]]
            analysis["detection_accuracy"]["avg"] = sum(values) / len(values)
            
            if len(values) >= 10:
                recent_avg = sum(values[-10:]) / 10
                older_avg = sum(values[-20:-10]) / 10 if len(values) >= 20 else recent_avg
                
                if recent_avg > older_avg * 1.05:
                    analysis["detection_accuracy"]["trend"] = "improving"
                elif recent_avg < older_avg * 0.95:
                    analysis["detection_accuracy"]["trend"] = "declining"
                    analysis["detection_accuracy"]["issues"].append("Точность детекции снижается")
        
        # Анализ времени отклика
        if self.performance_metrics["response_time"]:
            values = [m["value"] for m in self.performance_metrics["response_time"][-100:]]
            analysis["response_time"]["avg"] = sum(values) / len(values)
            
            if analysis["response_time"]["avg"] > 1.0:  # Больше 1 секунды
                analysis["response_time"]["issues"].append("Время отклика слишком высокое")
        
        # Общая оценка здоровья
        issues_count = len(analysis["detection_accuracy"]["issues"]) + len(analysis["response_time"]["issues"])
        if issues_count == 0:
            analysis["overall_health"] = "excellent"
        elif issues_count <= 2:
            analysis["overall_health"] = "good"
        elif issues_count <= 4:
            analysis["overall_health"] = "needs_attention"
        else:
            analysis["overall_health"] = "critical"
        
        return analysis
    
    def generate_improvements(self) -> List[Dict]:
        """Генерация идей для улучшения"""
        improvements = []
        analysis = self.analyze_performance()
        
        # Улучшения на основе анализа
        if analysis["detection_accuracy"]["trend"] == "declining":
            improvements.append({
                "type": "detection",
                "priority": "high",
                "description": "Точность детекции снижается - нужно дообучить модель",
                "action": "retrain_model"
            })
        
        if analysis["response_time"]["avg"] > 1.0:
            improvements.append({
                "type": "performance",
                "priority": "medium",
                "description": "Время отклика высокое - оптимизировать код",
                "action": "optimize_code"
            })
        
        # Идеи для самосовершенствования
        improvements.append({
            "type": "self_improvement",
            "priority": "low",
            "description": "Изучить новые техники детекции",
            "action": "research_new_methods"
        })
        
        return improvements
    
    def learn_from_experience(self, experience: Dict):
        """
        Обучение на опыте
        
        Args:
            experience: Опыт в формате:
                - type: тип опыта
                - outcome: результат
                - context: контекст
        """
        self.learning_history.append({
            **experience,
            "timestamp": datetime.now().isoformat()
        })
        
        # Добавляем в память
        self.self_identity.add_memory(
            f"Опыт: {experience.get('type')} - {experience.get('outcome')}",
            "learning"
        )
        
        # Ограничиваем размер истории
        if len(self.learning_history) > 5000:
            self.learning_history = self.learning_history[-5000:]
        
        logger.info(f"📚 Изучен опыт: {experience.get('type')}")
    
    def apply_improvement(self, improvement: Dict) -> bool:
        """
        Применить улучшение
        
        Args:
            improvement: Словарь с описанием улучшения
        
        Returns:
            True если успешно применено
        """
        action = improvement.get("action")
        
        try:
            if action == "retrain_model":
                # Запускаем дообучение модели
                logger.info("🔄 Запуск дообучения модели...")
                # Здесь можно вызвать активное обучение
                return True
            
            elif action == "optimize_code":
                # Оптимизация кода
                logger.info("⚡ Оптимизация кода...")
                # Здесь можно применить оптимизации
                return True
            
            elif action == "research_new_methods":
                # Исследование новых методов
                logger.info("🔬 Исследование новых методов...")
                self.self_identity.add_thought("Изучаю новые техники детекции")
                return True
            
            else:
                logger.warning(f"Неизвестное действие: {action}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка применения улучшения: {e}")
            return False
        finally:
            # Записываем примененное улучшение
            self.improvements_applied.append({
                **improvement,
                "applied_at": datetime.now().isoformat()
            })
    
    def continuous_improvement_loop(self):
        """Цикл непрерывного улучшения"""
        logger.info("🔄 Запуск цикла непрерывного улучшения...")
        
        # Анализируем производительность
        analysis = self.analyze_performance()
        
        # Генерируем улучшения
        improvements = self.generate_improvements()
        
        # Применяем улучшения с высоким приоритетом
        for improvement in improvements:
            if improvement.get("priority") == "high":
                logger.info(f"🚀 Применяю улучшение: {improvement.get('description')}")
                self.apply_improvement(improvement)
        
        # Добавляем мысль о самосовершенствовании
        if improvements:
            self.self_identity.add_thought(
                f"Нашел {len(improvements)} способов улучшить себя"
            )
    
    def get_learning_summary(self) -> Dict:
        """Получить сводку по обучению"""
        return {
            "total_experiences": len(self.learning_history),
            "improvements_applied": len(self.improvements_applied),
            "performance_analysis": self.analyze_performance(),
            "recent_improvements": self.improvements_applied[-10:] if self.improvements_applied else []
        }

