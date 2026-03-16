"""
Скрипт для миграции файлов в новую структуру
С сохранением обратной совместимости через алиасы
"""
import shutil
from pathlib import Path

# Маппинг файлов для перемещения
migrations = [
    # Движки -> core/engines/
    {
        "source": "obelisk/core/unified_engine.py",
        "target": "obelisk/core/engines/unified_engine.py",
        "alias": True  # Создать алиас для обратной совместимости
    },
    {
        "source": "obelisk/core/model_engine.py",
        "target": "obelisk/core/engines/model_engine.py",
        "alias": True
    },
    {
        "source": "obelisk/core/test_engine.py",
        "target": "obelisk/core/engines/test_engine.py",
        "alias": True
    },
    
    # Процессоры -> core/processors/
    {
        "source": "obelisk/core/object_tracker.py",
        "target": "obelisk/core/processors/object_tracker.py",
        "alias": True
    },
    
    # Менеджеры -> core/managers/
    {
        "source": "obelisk/core/gpu_manager.py",
        "target": "obelisk/core/managers/gpu_manager.py",
        "alias": True
    },
    {
        "source": "obelisk/core/gpu_test_manager.py",
        "target": "obelisk/core/managers/gpu_test_manager.py",
        "alias": True
    },
]

def create_alias(source_path: Path, target_path: Path):
    """Создание алиаса для обратной совместимости"""
    # Создаем файл-алиас который импортирует из нового места
    relative_path = target_path.relative_to(source_path.parent)
    
    alias_content = f'''"""
Алиас для обратной совместимости
Автоматически создан при миграции
"""
from {relative_path.with_suffix('').as_posix().replace('/', '.')} import *
'''
    
    source_path.write_text(alias_content)
    print(f"Created alias: {source_path} -> {target_path}")

def migrate():
    """Выполнение миграции"""
    root = Path(__file__).parent.parent
    
    for migration in migrations:
        source = root / migration["source"]
        target = root / migration["target"]
        
        if not source.exists():
            print(f"Skipping {source} - file not found")
            continue
        
        # Создаем целевую директорию
        target.parent.mkdir(parents=True, exist_ok=True)
        
        # Копируем файл
        if not target.exists():
            shutil.copy2(source, target)
            print(f"Copied: {source} -> {target}")
        else:
            print(f"Skipping {target} - already exists")
        
        # Создаем алиас если нужно
        if migration.get("alias") and source.exists():
            create_alias(source, target)
    
    print("Migration completed!")

if __name__ == "__main__":
    migrate()

