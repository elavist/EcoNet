"""
Скрипт для создания новой структуры проекта
"""
import os
from pathlib import Path

# Структура директорий
structure = [
    "obelisk/brain",
    "obelisk/neurons/perception",
    "obelisk/neurons/coordination",
    "obelisk/neurons/memory",
    "obelisk/neurons/learning",
    "obelisk/neurons/analysis",
    "obelisk/neurons/communication",
    "obelisk/veins",
    "obelisk/core/engines",
    "obelisk/core/processors",
    "obelisk/core/managers",
    "obelisk/services/data",
    "obelisk/services/learning",
    "obelisk/services/communication",
    "obelisk/services/tools",
    "obelisk/api/rest",
    "obelisk/api/neural",
    "obelisk/ui/gui",
    "obelisk/ui/neural_ui",
]

# Создание директорий
for dir_path in structure:
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    # Создание __init__.py
    init_file = Path(dir_path) / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""\n"""\n')

print("Structure created successfully")

