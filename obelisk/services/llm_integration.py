"""
Интеграция различных LLM провайдеров для ЭкоНет
Поддержка: Groq, Ollama, Google Gemini, Hugging Face, Together AI
"""

import logging
import os
from typing import Optional, List, Dict
import json

logger = logging.getLogger(__name__)


class LLMProvider:
    """Базовый класс для LLM провайдеров"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "default"):
        self.api_key = api_key
        self.model = model
    
    async def generate(self, messages: List[Dict], **kwargs) -> str:
        """Генерация ответа"""
        raise NotImplementedError


class GroqProvider(LLMProvider):
    """Groq API - самый быстрый, рекомендуется!"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-70b-versatile"):
        super().__init__(api_key, model)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Инициализация Groq клиента"""
        try:
            from groq import Groq
            if self.api_key:
                self.client = Groq(api_key=self.api_key)
            else:
                # Попытка получить из переменной окружения
                api_key = os.getenv("GROQ_API_KEY")
                if api_key:
                    self.client = Groq(api_key=api_key)
                else:
                    logger.warning("⚠️ Groq API ключ не найден")
        except ImportError:
            logger.warning("⚠️ groq не установлен. Установите: pip install groq")
        except Exception as e:
            logger.error(f"Ошибка инициализации Groq: {e}")
    
    async def generate(self, messages: List[Dict], **kwargs) -> str:
        """Генерация ответа через Groq"""
        if not self.client:
            raise Exception("Groq клиент не инициализирован")
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 500),
                top_p=kwargs.get("top_p", 1.0)
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Ошибка Groq API: {e}")
            raise


class OllamaProvider(LLMProvider):
    """Ollama - локальный, приватный (рекомендуется для ЭкоНет)"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama3.1:8b", base_url: str = "http://localhost:11434"):
        super().__init__(api_key, model)
        self.base_url = base_url
        self._check_availability()
    
    def _check_availability(self):
        """Проверка доступности Ollama"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                logger.info(f"✅ Ollama обнаружен. Доступные модели: {', '.join(model_names[:3])}")
                
                # Проверка что нужная модель установлена
                if self.model not in model_names:
                    logger.warning(f"⚠️ Модель {self.model} не найдена. Установите: ollama pull {self.model}")
            else:
                # Ollama не используется в текущей версии
                pass
        except requests.exceptions.ConnectionError:
            # Ollama не используется в текущей версии, предупреждение отключено
            pass
        except Exception as e:
            # Ollama не используется в текущей версии
            pass
    
    async def generate(self, messages: List[Dict], stream_callback=None, **kwargs) -> str:
        """Генерация ответа через Ollama с поддержкой streaming и thinking mode"""
        try:
            import aiohttp
        except ImportError:
            raise Exception("aiohttp не установлен. Установите: pip install aiohttp")
        
        try:
            # Проверяем, поддерживает ли модель thinking (DeepSeek)
            use_streaming = stream_callback is not None or "deepseek" in self.model.lower()
            
            async with aiohttp.ClientSession() as session:
                if use_streaming:
                    # Streaming режим для thinking mode
                    async with session.post(
                        f"{self.base_url}/api/chat",
                        json={
                            "model": self.model,
                            "messages": messages,
                            "stream": True,
                            "options": {
                                "temperature": kwargs.get("temperature", 0.7),
                                "num_predict": kwargs.get("max_tokens", 2000)
                            }
                        },
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        if response.status == 200:
                            full_response = ""
                            thinking_content = ""
                            in_thinking = False
                            
                            async for line in response.content:
                                if not line:
                                    continue
                                    
                                try:
                                    line_text = line.decode('utf-8').strip()
                                    if not line_text or line_text == "data: [DONE]":
                                        continue
                                    
                                    if line_text.startswith("data: "):
                                        line_text = line_text[6:]
                                    
                                    chunk = json.loads(line_text)
                                    
                                    # Проверяем thinking mode (DeepSeek)
                                    if chunk.get("message", {}).get("content"):
                                        content = chunk["message"]["content"]
                                        
                                        # DeepSeek использует <think> теги
                                        if "<think>" in content.lower() or "thinking" in content.lower():
                                            in_thinking = True
                                            thinking_content += content
                                            if stream_callback:
                                                await stream_callback("thinking", content)
                                        elif "</think>" in content.lower() or (in_thinking and "</think>" not in content.lower()):
                                            thinking_content += content
                                            if stream_callback:
                                                await stream_callback("thinking", content)
                                            if "</think>" in content.lower():
                                                in_thinking = False
                                                if stream_callback:
                                                    await stream_callback("thinking_done", thinking_content)
                                        else:
                                            full_response += content
                                            if stream_callback:
                                                await stream_callback("content", content)
                                    elif chunk.get("done", False):
                                        break
                                        
                                except json.JSONDecodeError:
                                    continue
                                except Exception as e:
                                    logger.debug(f"Ошибка парсинга chunk: {e}")
                                    continue
                            
                            return full_response.strip() if full_response else thinking_content.strip()
                        else:
                            error_text = await response.text()
                            raise Exception(f"Ollama API error {response.status}: {error_text}")
                else:
                    # Обычный режим без streaming
                    async with session.post(
                        f"{self.base_url}/api/chat",
                        json={
                            "model": self.model,
                            "messages": messages,
                            "stream": False,
                            "options": {
                                "temperature": kwargs.get("temperature", 0.7),
                                "num_predict": kwargs.get("max_tokens", 2000)
                            }
                        },
                        timeout=aiohttp.ClientTimeout(total=120)
                    ) as response:
                        if response.status == 200:
                            content_type = response.headers.get('Content-Type', '')
                            if 'application/json' in content_type:
                                data = await response.json()
                                return data.get("message", {}).get("content", "")
                            else:
                                text = await response.text()
                                try:
                                    data = json.loads(text)
                                    return data.get("message", {}).get("content", text)
                                except:
                                    return text
                        else:
                            error_text = await response.text()
                            raise Exception(f"Ollama API error {response.status}: {error_text}")
        except aiohttp.ClientConnectorError:
            raise Exception("Ollama не запущен. Запустите: ollama serve")
        except Exception as e:
            logger.error(f"Ошибка Ollama API: {e}")
            raise
    


class GeminiProvider(LLMProvider):
    """Google Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        super().__init__(api_key, model)
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Инициализация Gemini клиента"""
        try:
            import google.generativeai as genai
            if self.api_key:
                genai.configure(api_key=self.api_key)
            else:
                api_key = os.getenv("GEMINI_API_KEY")
                if api_key:
                    genai.configure(api_key=api_key)
                else:
                    logger.warning("⚠️ Gemini API ключ не найден")
            
            self.client = genai.GenerativeModel(self.model)
        except ImportError:
            logger.warning("⚠️ google-generativeai не установлен. Установите: pip install google-generativeai")
        except Exception as e:
            logger.error(f"Ошибка инициализации Gemini: {e}")
    
    async def generate(self, messages: List[Dict], **kwargs) -> str:
        """Генерация ответа через Gemini"""
        if not self.client:
            raise Exception("Gemini клиент не инициализирован")
        
        try:
            # Конвертация сообщений для Gemini
            chat = self.client.start_chat(history=[])
            
            # Отправка сообщений
            last_message = messages[-1].get("content", "")
            response = chat.send_message(
                last_message,
                generation_config={
                    "temperature": kwargs.get("temperature", 0.7),
                    "max_output_tokens": kwargs.get("max_tokens", 500)
                }
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Ошибка Gemini API: {e}")
            raise


class HuggingFaceProvider(LLMProvider):
    """Hugging Face Inference API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/Llama-3.1-8B-Instruct"):
        super().__init__(api_key, model)
        self.api_url = f"https://api-inference.huggingface.co/models/{model}"
    
    async def generate(self, messages: List[Dict], **kwargs) -> str:
        """Генерация ответа через Hugging Face"""
        try:
            import aiohttp
            
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                api_key = os.getenv("HUGGINGFACE_API_KEY")
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
            
            # Конвертация сообщений
            prompt = self._messages_to_prompt(messages)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json={
                        "inputs": prompt,
                        "parameters": {
                            "temperature": kwargs.get("temperature", 0.7),
                            "max_new_tokens": kwargs.get("max_tokens", 500),
                            "return_full_text": False
                        }
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and len(data) > 0:
                            return data[0].get("generated_text", "")
                        return str(data)
                    else:
                        raise Exception(f"HuggingFace API error: {response.status}")
        except Exception as e:
            logger.error(f"Ошибка HuggingFace API: {e}")
            raise
    
    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """Конвертация сообщений в промпт"""
        prompt_parts = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            prompt_parts.append(f"{role.capitalize()}: {content}")
        return "\n".join(prompt_parts)


class TogetherAIProvider(LLMProvider):
    """Together AI API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "meta-llama/Llama-3.1-70b-chat-hf"):
        super().__init__(api_key, model)
        self.api_url = "https://api.together.xyz/v1/chat/completions"
    
    async def generate(self, messages: List[Dict], **kwargs) -> str:
        """Генерация ответа через Together AI"""
        try:
            import aiohttp
            
            headers = {
                "Content-Type": "application/json"
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            else:
                api_key = os.getenv("TOGETHER_API_KEY")
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_tokens": kwargs.get("max_tokens", 500)
                    },
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        raise Exception(f"Together AI API error: {response.status}")
        except Exception as e:
            logger.error(f"Ошибка Together AI API: {e}")
            raise


class LLMEngineAdapter:
    """Адаптер: LLMProvider -> интерфейс DeepSeekNeuron (process_message / think)"""
    
    SYSTEM_PROMPT = (
        "Ты — DeepSeek-нейрон системы EcoNet (автономная роботизированная уборка). "
        "Отвечай кратко, по делу, на языке пользователя. "
        "Ты можешь анализировать данные детекций, давать рекомендации по задачам, "
        "отвечать на вопросы о системе."
    )
    
    def __init__(self, provider: LLMProvider):
        self.provider = provider
    
    async def process_message(self, message: str, context: Optional[Dict] = None) -> str:
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]
        if context:
            messages.append({"role": "system", "content": f"Контекст: {json.dumps(context, ensure_ascii=False, default=str)}"})
        messages.append({"role": "user", "content": message})
        return await self.provider.generate(messages, max_tokens=2000)
    
    async def think(self, prompt: str) -> str:
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Подумай пошагово: {prompt}"}
        ]
        return await self.provider.generate(messages, max_tokens=4000)


def create_llm_provider(provider: str, api_key: Optional[str] = None, model: Optional[str] = None, **kwargs) -> Optional[LLMProvider]:
    """
    Создание LLM провайдера
    
    Args:
        provider: Название провайдера (groq, ollama, gemini, huggingface, togetherai)
        api_key: API ключ (опционально, можно через переменные окружения)
        model: Название модели (опционально)
    
    Returns:
        Экземпляр провайдера или None
    """
    provider = provider.lower()
    
    if provider == "groq":
        return GroqProvider(
            api_key=api_key or os.getenv("GROQ_API_KEY"),
            model=model or "llama-3.1-70b-versatile"
        )
    
    elif provider == "ollama":
        return OllamaProvider(
            api_key=api_key,
            model=model or "llama3.1:8b",
            base_url=kwargs.get("base_url", "http://localhost:11434")
        )
    
    elif provider == "gemini":
        return GeminiProvider(
            api_key=api_key or os.getenv("GEMINI_API_KEY"),
            model=model or "gemini-1.5-flash"
        )
    
    elif provider == "huggingface":
        return HuggingFaceProvider(
            api_key=api_key or os.getenv("HUGGINGFACE_API_KEY"),
            model=model or "meta-llama/Llama-3.1-8B-Instruct"
        )
    
    elif provider == "togetherai":
        return TogetherAIProvider(
            api_key=api_key or os.getenv("TOGETHER_API_KEY"),
            model=model or "meta-llama/Llama-3.1-70b-chat-hf"
        )
    
    else:
        logger.warning(f"⚠️ Неизвестный провайдер: {provider}")
        return None

