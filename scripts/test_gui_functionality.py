"""
Тест функциональности GUI ЭкоНет
Проверка всех компонентов интерфейса
"""

import sys
from pathlib import Path

# Добавление корня проекта в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def test_imports():
    """Тест импортов"""
    print("="*70)
    print("ТЕСТ ИМПОРТОВ")
    print("="*70)
    
    try:
        from obelisk.ui.gui_app_cyberpunk import (
            EcoNetCyberpunkGUI, CyberButton, CyberPanel,
            CyberVideoPanel, CyberChatPanel, CyberStatusPanel, CYBERPUNK
        )
        print("[OK] Все импорты успешны")
        print(f"[OK] Цветовая схема загружена: {len(CYBERPUNK)} цветов")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка импорта: {e}")
        return False

def test_config():
    """Тест конфигурации"""
    print("\n" + "="*70)
    print("ТЕСТ КОНФИГУРАЦИИ")
    print("="*70)
    
    try:
        import yaml
        config_path = root_dir / "config" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print(f"[OK] Конфигурация загружена: {config_path}")
        print(f"[OK] LLM провайдер: {config.get('chat', {}).get('llm_provider', 'N/A')}")
        print(f"[OK] LLM модель: {config.get('chat', {}).get('llm_model', 'N/A')}")
        print(f"[OK] Self-awareness: {config.get('self_awareness', {}).get('enabled', False)}")
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка конфигурации: {e}")
        return False

def test_model():
    """Тест модели"""
    print("\n" + "="*70)
    print("ТЕСТ МОДЕЛИ")
    print("="*70)
    
    try:
        import yaml
        config_path = root_dir / "config" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        model_path_str = config.get("model", {}).get("weights_path", 
                                                     "models/cigarette_detector/best.pt")
        model_path = root_dir / model_path_str if not Path(model_path_str).is_absolute() else Path(model_path_str)
        
        if model_path.exists():
            print(f"[OK] Модель найдена: {model_path}")
            print(f"[OK] Размер: {model_path.stat().st_size / 1024 / 1024:.1f} MB")
        else:
            print(f"[WARNING] Модель не найдена: {model_path}")
        
        # Проверка ONNX
        onnx_path = model_path.with_suffix('.onnx')
        if onnx_path.exists():
            print(f"[OK] ONNX модель найдена: {onnx_path}")
        else:
            print(f"[INFO] ONNX модель не найдена (будет использована PT)")
        
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка проверки модели: {e}")
        return False

def test_services():
    """Тест сервисов"""
    print("\n" + "="*70)
    print("ТЕСТ СЕРВИСОВ")
    print("="*70)
    
    try:
        from obelisk.services.self_identity import SelfIdentityService
        from obelisk.services.self_modification import SelfModificationService
        from obelisk.services.self_learning import SelfLearningService
        from obelisk.services.chat_service import ChatService
        from obelisk.services.vision_context import VisionContext
        from edge.inference_service.detector import CigaretteDetector
        
        print("[OK] SelfIdentityService импортирован")
        print("[OK] SelfModificationService импортирован")
        print("[OK] SelfLearningService импортирован")
        print("[OK] ChatService импортирован")
        print("[OK] VisionContext импортирован")
        print("[OK] CigaretteDetector импортирован")
        
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка импорта сервисов: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_integration():
    """Тест интеграции LLM"""
    print("\n" + "="*70)
    print("ТЕСТ LLM ИНТЕГРАЦИИ")
    print("="*70)
    
    try:
        from obelisk.services.llm_integration import OllamaProvider
        import yaml
        
        config_path = root_dir / "config" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        model = config.get('chat', {}).get('llm_model', 'deepseek-v3.1:671b-cloud')
        provider = OllamaProvider(model=model)
        
        print(f"[OK] OllamaProvider создан")
        print(f"[OK] Модель: {model}")
        print(f"[OK] Base URL: {provider.base_url}")
        
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка LLM интеграции: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("\n" + "="*70)
    print("ТЕСТИРОВАНИЕ ФУНКЦИОНАЛЬНОСТИ GUI ЭКОНЕТ")
    print("="*70 + "\n")
    
    results = []
    results.append(("Импорты", test_imports()))
    results.append(("Конфигурация", test_config()))
    results.append(("Модель", test_model()))
    results.append(("Сервисы", test_services()))
    results.append(("LLM интеграция", test_llm_integration()))
    
    print("\n" + "="*70)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("="*70)
    
    for name, result in results:
        status = "[OK]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("[SUCCESS] Все тесты пройдены успешно!")
    else:
        print("[WARNING] Некоторые тесты не пройдены")
    print("="*70 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

