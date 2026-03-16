"""
Тест UnifiedEngine
Проверка инициализации и работы единого движка
"""

import sys
import asyncio
from pathlib import Path

# Добавление корня проекта в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import yaml
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_unified_engine():
    """Тест UnifiedEngine"""
    print("="*70)
    print("ТЕСТ UNIFIED ENGINE")
    print("="*70)
    
    try:
        from obelisk.core.engines.unified_engine import UnifiedEngine
        
        # Загрузка конфигурации
        config_path = root_dir / "config" / "config.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        print("\n[1/3] Создание UnifiedEngine...")
        engine = UnifiedEngine(config, project_root=root_dir)
        print("[OK] UnifiedEngine создан")
        
        print("\n[2/3] Инициализация компонентов...")
        await engine.initialize()
        print("[OK] Компоненты инициализированы")
        
        print("\n[3/3] Проверка статистики...")
        stats = engine.get_statistics()
        print(f"[OK] Статистика получена:")
        print(f"  - Компонентов: {len([k for k, v in stats.get('components', {}).items() if v])}")
        print(f"  - Модель движок: {stats.get('components', {}).get('model_engine', False)}")
        print(f"  - LLM движок: {stats.get('components', {}).get('llm_engine', False)}")
        print(f"  - Chat сервис: {stats.get('components', {}).get('chat_service', False)}")
        print(f"  - Self-awareness: {stats.get('components', {}).get('self_awareness', False)}")
        
        print("\n" + "="*70)
        print("[SUCCESS] UnifiedEngine работает корректно!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Главная функция"""
    try:
        result = asyncio.run(test_unified_engine())
        return 0 if result else 1
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

