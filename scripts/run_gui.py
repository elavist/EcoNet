"""
Запуск графического интерфейса ЭкоНет
"""

import sys
from pathlib import Path

# Добавление корня проекта в путь
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from obelisk.ui.gui_material import main

if __name__ == "__main__":
    main()

