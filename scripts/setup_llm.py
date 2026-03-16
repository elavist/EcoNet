"""
Скрипт для настройки LLM в ЭкоНет
Помогает выбрать и настроить лучший бесплатный LLM
"""

import sys
from pathlib import Path
import yaml

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))


def setup_groq():
    """Настройка Groq (рекомендуется)"""
    print("\n" + "="*70)
    print("🚀 НАСТРОЙКА GROQ (РЕКОМЕНДУЕТСЯ)")
    print("="*70)
    print("\nGroq - самый быстрый бесплатный LLM!")
    print("Бесплатный tier: 14,400 запросов/день")
    print("\nШаги:")
    print("1. Перейдите на https://console.groq.com")
    print("2. Создайте бесплатный аккаунт")
    print("3. Получите API ключ")
    print("4. Введите ключ ниже (или нажмите Enter для пропуска)\n")
    
    api_key = input("Введите Groq API ключ (или Enter для пропуска): ").strip()
    
    if api_key:
        config_path = project_root / "config" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'chat' not in config:
            config['chat'] = {}
        
        config['chat']['use_llm'] = True
        config['chat']['llm_provider'] = "groq"
        config['chat']['llm_model'] = "llama-3.1-70b-versatile"
        config['chat']['llm_api_key'] = api_key
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print("\n✅ Groq настроен! ЭкоНет теперь умнее!")
        print("\nУстановите библиотеку:")
        print("pip install groq")
    else:
        print("\n⚠️ Настройка пропущена. Вы можете настроить позже.")


def setup_ollama():
    """Настройка Ollama (локальный)"""
    print("\n" + "="*70)
    print("🏠 НАСТРОЙКА OLLAMA (ЛОКАЛЬНЫЙ, ПРИВАТНЫЙ)")
    print("="*70)
    print("\nOllama - полностью бесплатный и приватный!")
    print("\n📋 Шаги установки:")
    print("1. Установите Ollama: https://ollama.ai/download")
    print("   (Рекомендуется установка на ПК, не в корень проекта)")
    print("2. Запустите: ollama serve")
    print("3. Скачайте модель: ollama pull llama3.1:8b")
    print("\n🔍 Проверяю доступность Ollama...\n")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            print("✅ Ollama обнаружен!")
            
            # Показать доступные модели
            models_data = response.json().get("models", [])
            if models_data:
                print("\n📦 Доступные модели:")
                for model in models_data[:5]:
                    print(f"   • {model.get('name', 'unknown')}")
            
            # Выбор модели
            print("\n💡 Рекомендуемые модели для ЭкоНет:")
            print("   1. llama3.1:8b - быстрая, хороший баланс (рекомендуется)")
            print("   2. mistral:7b - отличная поддержка русского")
            print("   3. qwen2.5:7b - специально для русского")
            
            model_choice = input("\nВведите название модели (или Enter для llama3.1:8b): ").strip()
            if not model_choice:
                model_choice = "llama3.1:8b"
            
            # Проверка что модель установлена
            model_names = [m.get("name", "") for m in models_data]
            if model_choice not in model_names:
                print(f"\n⚠️ Модель {model_choice} не найдена в списке.")
                install = input(f"Скачать модель {model_choice}? (y/n): ").strip().lower()
                if install == 'y':
                    print(f"\n📥 Скачиваю {model_choice}...")
                    print(f"   Запустите в отдельном терминале: ollama pull {model_choice}")
                    print("   Затем запустите этот скрипт снова.")
                else:
                    print("⚠️ Настройка отменена. Установите модель вручную.")
                    return
            
            config_path = project_root / "config" / "config.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            if 'chat' not in config:
                config['chat'] = {}
            
            config['chat']['use_llm'] = True
            config['chat']['llm_provider'] = "ollama"
            config['chat']['llm_model'] = model_choice
            config['chat']['llm_api_key'] = None  # Не нужен для Ollama
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
            
            print(f"\n✅ Ollama настроен!")
            print(f"   Модель: {model_choice}")
            print(f"   URL: http://localhost:11434")
            print("\n🎉 ЭкоНет теперь использует локальный Ollama!")
        else:
            print("⚠️ Ollama не запущен.")
            print("\n💡 Запустите Ollama:")
            print("   1. Если установлен: ollama serve")
            print("   2. Или откройте приложение Ollama")
    except requests.exceptions.ConnectionError:
        print("⚠️ Ollama не запущен или не установлен.")
        print("\n📥 Установка Ollama:")
        print("   1. Скачайте: https://ollama.ai/download")
        print("   2. Установите (рекомендуется в стандартную папку)")
        print("   3. Запустите: ollama serve")
        print("   4. Скачайте модель: ollama pull llama3.1:8b")
        print("   5. Запустите этот скрипт снова")
    except Exception as e:
        print(f"⚠️ Ошибка: {e}")
        print("   Убедитесь что Ollama установлен и запущен")


def setup_gemini():
    """Настройка Google Gemini"""
    print("\n" + "="*70)
    print("🧠 НАСТРОЙКА GOOGLE GEMINI")
    print("="*70)
    print("\nGemini - хороший баланс скорости и качества!")
    print("Бесплатный tier: 60 запросов/мин")
    print("\nШаги:")
    print("1. Перейдите на https://aistudio.google.com")
    print("2. Создайте аккаунт Google")
    print("3. Получите API ключ")
    print("4. Введите ключ ниже (или нажмите Enter для пропуска)\n")
    
    api_key = input("Введите Gemini API ключ (или Enter для пропуска): ").strip()
    
    if api_key:
        config_path = project_root / "config" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if 'chat' not in config:
            config['chat'] = {}
        
        config['chat']['use_llm'] = True
        config['chat']['llm_provider'] = "gemini"
        config['chat']['llm_model'] = "gemini-1.5-flash"
        config['chat']['llm_api_key'] = api_key
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
        print("\n✅ Gemini настроен!")
        print("\nУстановите библиотеку:")
        print("pip install google-generativeai")
    else:
        print("\n⚠️ Настройка пропущена.")


def main():
    """Главная функция"""
    print("\n" + "="*70)
    print("🤖 НАСТРОЙКА LLM ДЛЯ ЭКОНЕТ")
    print("="*70)
    print("\nВыберите LLM провайдер:")
    print("\n1. Groq (РЕКОМЕНДУЕТСЯ) - самый быстрый, 14,400 запросов/день")
    print("2. Ollama - локальный, приватный, полностью бесплатный")
    print("3. Google Gemini - хороший баланс, 60 запросов/мин")
    print("4. Показать сравнение всех вариантов")
    print("5. Выход")
    
    choice = input("\nВаш выбор (1-5): ").strip()
    
    if choice == "1":
        setup_groq()
    elif choice == "2":
        setup_ollama()
    elif choice == "3":
        setup_gemini()
    elif choice == "4":
        print("\n" + "="*70)
        print("📊 СРАВНЕНИЕ LLM ПРОВАЙДЕРОВ")
        print("="*70)
        print("\nСм. LLM_INTEGRATION_GUIDE.md для подробного сравнения")
        print("\nКратко:")
        print("• Groq - самый быстрый, лучший для начала")
        print("• Ollama - приватный, локальный")
        print("• Gemini - хорошее качество, мультимодальный")
    else:
        print("\nВыход.")


if __name__ == "__main__":
    main()

