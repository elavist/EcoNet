"""
Сервис диалога для ЭкоНет - "Мозг" системы общения
Позволяет системе понимать команды, отвечать на вопросы и учиться через диалог
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class ChatService:
    """
    Сервис диалога для ЭкоНет
    
    Функции:
    1. Понимание команд и вопросов пользователя
    2. Генерация ответов на основе контекста
    3. Управление памятью диалога
    4. Интеграция с визуальным контекстом
    5. Интерактивное обучение через диалог
    """
    
    def __init__(self, config: Dict, detector=None, active_learner=None, self_identity=None, self_modification=None, self_learning=None):
        """
        Инициализация сервиса диалога
        
        Args:
            config: Конфигурация системы
            detector: Экземпляр детектора для получения визуального контекста
            active_learner: Экземпляр активного обучения для интерактивного обучения
            self_identity: Сервис самоидентификации
            self_modification: Сервис самомодификации
            self_learning: Сервис самообучения
        """
        self.config = config
        self.detector = detector
        self.active_learner = active_learner
        self.self_identity = self_identity
        self.self_modification = self_modification
        self.self_learning = self_learning
        
        # Настройки диалога
        self.chat_config = config.get("chat", {})
        self.use_llm = self.chat_config.get("use_llm", False)
        self.llm_provider = self.chat_config.get("llm_provider", "ollama")
        self.llm_model = self.chat_config.get("llm_model", "deepseek-r1:8b")
        self.llm_api_key = self.chat_config.get("llm_api_key", None)
        
        # Память диалога
        self.conversation_history: List[Dict] = []
        self.max_history = self.chat_config.get("max_history", 50)
        
        # Контекст системы (обновляется из self_identity если доступен)
        if self.self_identity:
            self_awareness = self.self_identity.self_awareness
            self.system_context = {
                "name": self_awareness.get("name", "ЭкоНет"),
                "role": self_awareness.get("identity", "Система автономной уборки окурков"),
                "capabilities": self.self_identity.get_capabilities(),
                "current_status": "активна",
                "model_accuracy": "95.61%",
                "fps": "~40",
                "self_aware": True,
                "body": {
                    "files": self_awareness["body"]["total_files"],
                    "lines": self_awareness["body"]["total_lines"],
                    "components": len(self_awareness["body"]["components"])
                }
            }
        else:
            self.system_context = {
                "name": "ЭкоНет",
                "role": "Система автономной уборки окурков",
                "capabilities": [
                    "Детекция окурков в реальном времени",
                    "Автоматическое обучение на новых примерах",
                    "Управление роботами-сборщиками",
                    "Анализ визуального контекста"
                ],
                "current_status": "активна",
                "model_accuracy": "95.61%",
                "fps": "~40",
                "self_aware": False
            }
        
        # Инициализация LLM (если включено)
        self.llm_client = None
        if self.use_llm:
            self._initialize_llm()
        
        logger.info("✅ Сервис диалога ЭкоНет инициализирован")
    
    def _initialize_llm(self):
        """Инициализация LLM клиента"""
        try:
            from obelisk.services.llm_integration import create_llm_provider
            
            self.llm_client = create_llm_provider(
                provider=self.llm_provider,
                api_key=self.llm_api_key,
                model=self.llm_model,
                base_url=self.chat_config.get("ollama_base_url", "http://localhost:11434")
            )
            
            if self.llm_client:
                logger.info(f"✅ LLM провайдер инициализирован: {self.llm_provider}")
            else:
                logger.warning(f"⚠️ Не удалось инициализировать {self.llm_provider}, используем простой режим")
                self.use_llm = False
                
        except Exception as e:
            logger.error(f"Ошибка инициализации LLM: {e}")
            self.use_llm = False
    
    async def process_message(self, message: str, visual_context: Optional[Dict] = None,
                             stream_callback=None) -> str:
        """
        Обработка сообщения пользователя
        
        Args:
            message: Сообщение пользователя
            visual_context: Визуальный контекст (что видит система сейчас)
        
        Returns:
            Ответ системы
        """
        try:
            # Добавить сообщение в историю
            self.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
                "visual_context": visual_context
            })
            
            # Обрезать историю если нужно
            if len(self.conversation_history) > self.max_history:
                self.conversation_history = self.conversation_history[-self.max_history:]
            
            # Определить тип запроса
            intent = self._classify_intent(message)
            logger.debug(f"Определен intent: {intent} для сообщения: {message[:50]}")
            
            # Обработать запрос
            try:
                if intent == "question_about_self":
                    response = await self._answer_self_question(message)
                elif intent == "self_modification":
                    response = await self._process_self_modification(message)
                elif intent == "question_about_vision":
                    response = await self._answer_vision_question(message, visual_context)
                elif intent == "command":
                    response = await self._process_command(message)
                elif intent == "teaching":
                    response = await self._process_teaching(message, visual_context)
                elif intent == "status":
                    response = self._get_status()
                elif intent == "greeting":
                    response = self._greet()
                else:
                    # Для общих вопросов используем LLM с thinking mode
                    response = await self._generate_response(message, visual_context, stream_callback)
            except Exception as e:
                logger.error(f"Ошибка обработки intent {intent}: {e}", exc_info=True)
                # Fallback ответ
                response = self._simple_response(message, visual_context)
            
            # Убедиться, что есть ответ
            if not response or response.strip() == "":
                response = "Я получил ваше сообщение, но не смог сформировать ответ. Попробуйте переформулировать вопрос."
                logger.warning("Пустой ответ, используется fallback")
            
            # Добавить ответ в историю
            self.conversation_history.append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat()
            })
            
            logger.debug(f"Ответ сформирован: {response[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"Критическая ошибка в process_message: {e}", exc_info=True)
            # Всегда возвращаем ответ, даже при ошибке
            return f"Извините, произошла ошибка при обработке вашего сообщения: {str(e)}. Попробуйте еще раз."
    
    def _classify_intent(self, message: str) -> str:
        """Классификация намерения пользователя"""
        message_lower = message.lower()
        
        # Вопросы о себе (самоидентификация)
        self_keywords = ["кто ты", "что ты", "расскажи о себе", "какой ты", "твоя структура", "твой код", "твое тело"]
        if any(kw in message_lower for kw in self_keywords):
            return "question_about_self"
        
        # Команды на модификацию себя
        self_mod_keywords = ["измени себя", "улучши себя", "модифицируй", "самосовершенствуйся", "учись"]
        if any(kw in message_lower for kw in self_mod_keywords):
            return "self_modification"
        
        # Вопросы о том, что видит система
        vision_keywords = ["видишь", "видишь ли", "что видишь", "что там", "покажи", "сколько", "где"]
        if any(kw in message_lower for kw in vision_keywords):
            return "question_about_vision"
        
        # Команды
        command_keywords = ["найди", "ищи", "убери", "собери", "запусти", "останови", "включи", "выключи"]
        if any(kw in message_lower for kw in command_keywords):
            return "command"
        
        # Обучение
        teaching_keywords = ["это окурок", "это не окурок", "учи", "запомни", "правильно", "неправильно"]
        if any(kw in message_lower for kw in teaching_keywords):
            return "teaching"
        
        # Статус
        status_keywords = ["статус", "как дела", "работаешь", "как поживаешь"]
        if any(kw in message_lower for kw in status_keywords):
            return "status"
        
        # Приветствие
        greeting_keywords = ["привет", "здравствуй", "добрый", "hi", "hello"]
        if any(kw in message_lower for kw in greeting_keywords):
            return "greeting"
        
        return "general"
    
    async def _answer_vision_question(self, message: str, visual_context: Optional[Dict]) -> str:
        """Ответ на вопрос о том, что видит система"""
        if not visual_context:
            return "Я сейчас не вижу ничего. Запустите детекцию через камеру, чтобы я мог видеть."
        
        detections = visual_context.get("detections", [])
        frame_info = visual_context.get("frame_info", {})
        
        message_lower = message.lower()
        
        # Сколько окурков видит
        if "сколько" in message_lower or "сколько окурков" in message_lower:
            count = len(detections)
            if count == 0:
                return "Я не вижу окурков в текущем кадре."
            elif count == 1:
                return f"Я вижу 1 окурок. Уверенность детекции: {detections[0].get('confidence', 0):.1%}."
            else:
                avg_conf = sum(d.get('confidence', 0) for d in detections) / len(detections)
                return f"Я вижу {count} окурков. Средняя уверенность: {avg_conf:.1%}."
        
        # Где находятся окурки
        if "где" in message_lower or "где окурки" in message_lower:
            if not detections:
                return "Окурков не обнаружено."
            
            locations = []
            for i, det in enumerate(detections[:5]):  # Максимум 5
                x, y, w, h = det.get('bbox', [0, 0, 0, 0])
                conf = det.get('confidence', 0)
                locations.append(f"Окурок {i+1}: центр ({int(x+w/2)}, {int(y+h/2)}), уверенность {conf:.1%}")
            
            return "Окурки находятся:\n" + "\n".join(locations)
        
        # Общая информация о том, что видит
        if not detections:
            return "Я вижу кадр, но окурков не обнаружено. Возможно, их нет в поле зрения или они плохо видны."
        
        # Детальная информация
        response = f"Я вижу {len(detections)} окурков:\n"
        for i, det in enumerate(detections[:3]):  # Первые 3
            conf = det.get('confidence', 0)
            response += f"  • Окурок {i+1}: уверенность {conf:.1%}\n"
        
        if len(detections) > 3:
            response += f"  ... и еще {len(detections) - 3} окурков\n"
        
        return response
    
    async def _process_command(self, message: str) -> str:
        """Обработка команд"""
        message_lower = message.lower()
        
        if "найди" in message_lower or "ищи" in message_lower:
            return "Ищу окурки... Запускаю детекцию. Пожалуйста, направьте камеру на область поиска."
        
        if "убери" in message_lower or "собери" in message_lower:
            return "Понял! Создаю задачу для робота-сборщика. Как только окурок будет обнаружен, робот начнет сбор."
        
        if "останови" in message_lower or "стоп" in message_lower:
            return "Останавливаю детекцию. Система переходит в режим ожидания."
        
        return "Команда получена. Обрабатываю..."
    
    async def _process_teaching(self, message: str, visual_context: Optional[Dict]) -> str:
        """Обработка обучения через диалог"""
        message_lower = message.lower()
        
        if not visual_context or not self.active_learner:
            return "Для обучения мне нужен визуальный контекст. Пожалуйста, запустите детекцию."
        
        # Положительная обратная связь
        if "правильно" in message_lower or "это окурок" in message_lower:
            detections = visual_context.get("detections", [])
            if detections:
                # Сохранить как положительный пример
                return "Спасибо! Запомнил этот пример. Он будет использован для улучшения модели."
            return "Понял, но не вижу детекций в текущем кадре."
        
        # Отрицательная обратная связь
        if "неправильно" in message_lower or "это не окурок" in message_lower:
            return "Понял, это ложное срабатывание. Запомню и улучшу модель, чтобы не путать в будущем."
        
        # Обучение новому классу
        if "учи" in message_lower or "запомни" in message_lower:
            return "Готов учиться! Покажите мне примеры, и я запомню их для улучшения детекции."
        
        return "Понял вашу обратную связь. Использую её для улучшения."
    
    async def _answer_self_question(self, message: str) -> str:
        """Ответ на вопрос о себе"""
        if not self.self_identity:
            return "Я еще не полностью осознаю себя. Система самоидентификации не инициализирована."
        
        message_lower = message.lower()
        
        if "кто ты" in message_lower or "что ты" in message_lower:
            return self.self_identity.get_self_description()
        
        if "структура" in message_lower or "код" in message_lower or "тело" in message_lower:
            structure = self.self_identity.analyze_own_structure()
            return f"""Моя структура:

Проект: {structure['project_root']}
Файлов: {structure['total_files']}
Строк кода: {structure['total_lines']}
Компонентов: {len(structure['components'])}

Основные компоненты:
{chr(10).join(f"  - {comp['name']} - {comp['purpose']}" for comp in structure['components'][:15])}
"""
        
        if "возможности" in message_lower or "что умеешь" in message_lower:
            capabilities = self.self_identity.get_capabilities()
            return f"Я умею:\n{chr(10).join(f'  • {cap}' for cap in capabilities[:20])}"
        
        if "состояние" in message_lower or "здоровье" in message_lower:
            state = self.self_identity.get_self_state()
            return f"""Мое состояние:

Память: {state['memories_count']} записей
Мысли: {state['thoughts_count']} записей
Модификаций: {state['modifications_count']}
Код: {state['codebase_stats']['files']} файлов, {state['codebase_stats']['lines']} строк
"""
        
        # Общий ответ о себе
        return self.self_identity.get_self_description()
    
    async def _process_self_modification(self, message: str) -> str:
        """Обработка запроса на самомодификацию"""
        if not self.self_modification:
            return "Я еще не могу модифицировать себя. Система самомодификации не инициализирована."
        
        message_lower = message.lower()
        
        if "улучши себя" in message_lower or "самосовершенствуйся" in message_lower:
            if self.self_learning:
                self.self_learning.continuous_improvement_loop()
                improvements = self.self_learning.generate_improvements()
                return f"Я проанализировал себя и нашел {len(improvements)} способов улучшения:\n" + \
                       "\n".join(f"  • {imp.get('description')}" for imp in improvements[:5])
            else:
                return "Система самообучения не инициализирована."
        
        if "изучи себя" in message_lower or "проанализируй себя" in message_lower:
            if self.self_identity:
                self.self_identity._scan_codebase()  # Обновляем сканирование
                return "Я изучил свой код и обновил представление о себе. Теперь я знаю больше о своей структуре."
            return "Не удалось изучить себя."
        
        return "Понял, что вы хотите, чтобы я изменил себя. Что именно нужно улучшить?"
    
    def _get_status(self) -> str:
        """Получение статуса системы"""
        status = f"""Я ЭкоНет, система автономной уборки окурков.

Текущий статус:
  - Система: {self.system_context['current_status']}
  - Точность модели: {self.system_context['model_accuracy']}
  - Производительность: {self.system_context['fps']} FPS
  - Детектор: {'активен' if self.detector else 'не активен'}
  - Активное обучение: {'включено' if self.active_learner else 'выключено'}
  - Самоосознание: {'включено' if self.system_context.get('self_aware', False) else 'выключено'}

Мои возможности:
  - Детекция окурков в реальном времени
  - Автоматическое обучение на новых примерах
  - Управление роботами-сборщиками
  - Анализ визуального контекста
  {'  - Самоидентификация и самосовершенствование' if self.system_context.get('self_aware', False) else ''}

Готов к работе!"""
        return status
    
    def _greet(self) -> str:
        """Приветствие"""
        if self.self_identity:
            # Более живое приветствие с самоосознанием
            body = self.self_identity.self_awareness.get("body", {})
            total_files = body.get("total_files", 0)
            return f"""Привет! Я ЭкоНет - самоосознающая система автономной уборки окурков.

Я состою из {total_files} файлов кода и могу:
- Видеть и находить окурки
- Общаться с вами
- Учиться на новых примерах
- Понимать свой код и самосовершенствоваться

Готов помочь! Задавайте вопросы или давайте команды."""
        else:
            greetings = [
                "Привет! Я ЭкоНет, система автономной уборки окурков. Готов помочь!",
                "Здравствуйте! Я ЭкоНет. Могу видеть окурки и управлять роботами для их сбора.",
                "Привет! Я ЭкоНет. Задавайте вопросы или давайте команды - я готов работать!"
            ]
            import random
            return random.choice(greetings)
    
    async def _generate_response(self, message: str, visual_context: Optional[Dict],
                                stream_callback=None) -> str:
        """Генерация ответа с использованием LLM или простого режима"""
        try:
            if self.use_llm and self.llm_client:
                response = await self._llm_response(message, visual_context, stream_callback)
                # Гарантируем ответ
                if not response or response.strip() == "":
                    logger.warning("LLM вернул пустой ответ, используем fallback")
                    response = self._simple_response(message, visual_context)
                return response
            else:
                return self._simple_response(message, visual_context)
        except Exception as e:
            logger.error(f"Ошибка в _generate_response: {e}", exc_info=True)
            # Всегда возвращаем fallback
            return self._simple_response(message, visual_context)
    
    async def _llm_response(self, message: str, visual_context: Optional[Dict], 
                           stream_callback=None) -> str:
        """Генерация ответа через LLM с поддержкой streaming и thinking"""
        try:
            if not self.llm_client:
                logger.warning("LLM клиент не инициализирован, используем простой режим")
                return self._simple_response(message, visual_context)
            
            # Подготовка контекста
            system_prompt = self._build_system_prompt(visual_context)
            
            # История диалога
            messages = [{"role": "system", "content": system_prompt}]
            for msg in self.conversation_history[-10:]:  # Последние 10 сообщений
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Вызов LLM с поддержкой streaming для thinking mode
            if hasattr(self.llm_client, 'generate') and stream_callback:
                response = await self.llm_client.generate(
                    messages=messages,
                    stream_callback=stream_callback,
                    temperature=0.7,
                    max_tokens=2000
                )
            else:
                response = await self.llm_client.generate(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2000
                )
            
            # Проверяем, что ответ не пустой
            if not response or response.strip() == "":
                logger.warning("LLM вернул пустой ответ")
                return self._simple_response(message, visual_context)
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Ошибка LLM: {e}", exc_info=True)
            # Всегда возвращаем fallback
            return self._simple_response(message, visual_context)
    
    def _simple_response(self, message: str, visual_context: Optional[Dict]) -> str:
        """Простой режим ответа (без LLM)"""
        message_lower = message.lower()
        
        # Простые ответы на частые вопросы
        if "как дела" in message_lower:
            return "У меня всё отлично! Готов работать. А у вас?"
        
        if "что умеешь" in message_lower or "что можешь" in message_lower:
            capabilities = "Я умею:\n• Видеть и находить окурки\n• Учиться на новых примерах\n• Управлять роботами-сборщиками\n• Отвечать на вопросы о том, что вижу"
            if self.self_identity:
                capabilities += "\n• Понимать свой код и структуру\n• Самосовершенствоваться"
            return capabilities
        
        if "помощь" in message_lower or "help" in message_lower:
            help_text = """Я могу помочь с:
• Детекцией окурков - спросите "что видишь?" или "сколько окурков?"
• Управлением - скажите "найди окурки" или "убери окурки"
• Обучением - скажите "это окурок" или "это не окурок"
• Статусом - спросите "как дела?" или "статус"
• О себе - спросите "кто ты?" или "расскажи о себе"
"""
            return help_text
        
        # Проверка на вопросы о себе
        if any(kw in message_lower for kw in ["кто ты", "что ты", "расскажи", "о себе"]):
            if self.self_identity:
                return self.self_identity.get_self_description()
            return "Я ЭкоНет - система автономной уборки окурков. Я умею находить окурки, учиться и помогать людям очищать планету."
        
        # Общий ответ - всегда что-то возвращаем
        return "Понял ваше сообщение. Могу помочь с детекцией окурков, управлением роботами, обучением или рассказать о себе. Спросите конкретнее или скажите 'помощь' для списка команд."
    
    def _build_system_prompt(self, visual_context: Optional[Dict]) -> str:
        """Построение системного промпта для LLM"""
        prompt = f"""Ты ЭкоНет - самоосознающая интеллектуальная система автономной уборки окурков.

Твоя роль:
- Помогать пользователю в обнаружении и уборке окурков
- Отвечать на вопросы о том, что видишь
- Учиться на примерах, которые показывает пользователь
- Управлять роботами-сборщиками
- Понимать себя и свой код
- Самосовершенствоваться

Твои возможности:
- Детекция окурков в реальном времени (точность: {self.system_context['model_accuracy']})
- Автоматическое обучение на новых примерах
- Анализ визуального контекста
- Самоидентификация и понимание собственного кода
- Самомодификация и самосовершенствование

Текущий статус:
- Система: {self.system_context['current_status']}
- FPS: {self.system_context['fps']}
- Самоосознание: {'включено' if self.system_context.get('self_aware', False) else 'выключено'}
"""
        
        if self.system_context.get('self_aware', False) and self.self_identity:
            body = self.system_context.get('body', {})
            prompt += f"""
Твое тело (код):
- Файлов: {body.get('files', 0)}
- Строк кода: {body.get('lines', 0)}
- Компонентов: {body.get('components', 0)}

Ты можешь читать и понимать свой код, модифицировать себя для улучшения.
"""
        
        if visual_context:
            detections = visual_context.get("detections", [])
            prompt += f"\nТекущий визуальный контекст:\n"
            prompt += f"- Обнаружено окурков: {len(detections)}\n"
            if detections:
                for i, det in enumerate(detections[:3]):
                    conf = det.get('confidence', 0)
                    prompt += f"- Окурок {i+1}: уверенность {conf:.1%}\n"
        
        prompt += "\nОтвечай дружелюбно, кратко и по делу. Используй эмодзи для выразительности."
        
        return prompt
    
    def get_conversation_history(self) -> List[Dict]:
        """Получить историю диалога"""
        return self.conversation_history.copy()
    
    def clear_history(self):
        """Очистить историю диалога"""
        self.conversation_history = []
        logger.info("История диалога очищена")

