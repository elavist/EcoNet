"""
Скрипт отладки ЭкоНет
Проверяет все компоненты и выводит детальную информацию
"""

import sys
import asyncio
from pathlib import Path

# Добавление корня проекта в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

import yaml
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def debug_unified_engine():
    """Отладка UnifiedEngine"""
    print("="*70)
    print("ОТЛАДКА UNIFIED ENGINE")
    print("="*70)
    
    try:
        from obelisk.core.engines.unified_engine import UnifiedEngine
        
        # Загрузка конфигурации
        config_path = root_dir / "config" / "config.yaml"
        print(f"\n[1] Загрузка конфигурации: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("[OK] Конфигурация загружена")
        
        # Создание движка
        print("\n[2] Создание UnifiedEngine...")
        engine = UnifiedEngine(config, project_root=root_dir)
        print("[OK] UnifiedEngine создан")
        
        # Инициализация
        print("\n[3] Инициализация компонентов...")
        await engine.initialize()
        print("[OK] Инициализация завершена")
        
        # Проверка компонентов
        print("\n[4] Проверка компонентов:")
        stats = engine.get_statistics()
        components = stats.get('components', {})
        
        for name, status in components.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {name}: {status}")
        
        # Проверка готовности
        print(f"\n[5] Готовность системы: {engine.is_ready()}")
        
        print("\n" + "="*70)
        print("[SUCCESS] Отладка завершена успешно!")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Ошибка отладки: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Главная функция"""
    try:
        result = asyncio.run(debug_unified_engine())
        return 0 if result else 1
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        return 1
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

