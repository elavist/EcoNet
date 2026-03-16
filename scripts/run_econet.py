"""
Команда запуска ЭкоНет
Единая точка входа для запуска системы
"""

import sys
import os
from pathlib import Path

# Установка кодировки UTF-8 для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Добавить корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

def main():
    """Главная функция запуска ЭкоНет"""
    print("="*70)
    print("ЭКОНЕТ - Автономная Система Роя для Очистки От Мусора")
    print("="*70)
    print("\nЗапуск графического интерфейса...")
    print("="*70)
    
    try:
        # Попытка использовать Material Design интерфейс
        try:
            from obelisk.ui.gui_material import MaterialEcoNetGUI
            print("Используется Material Design интерфейс")
            app = MaterialEcoNetGUI()
            app.run()
        except ImportError as e:
            # Fallback на современный интерфейс (CustomTkinter)
            print(f"Material Design недоступен: {e}")
            print("Переключение на современный интерфейс (CustomTkinter)...")
            try:
                from obelisk.ui.gui_modern import ModernEcoNetGUI
                app = ModernEcoNetGUI()
                app.run()
            except ImportError:
                # Fallback на киберпанк интерфейс (Tkinter)
                print("CustomTkinter не установлен, используется киберпанк интерфейс")
                from obelisk.ui.gui_app_cyberpunk import EcoNetCyberpunkGUI
                import tkinter as tk
                root = tk.Tk()
                app = EcoNetCyberpunkGUI(root)
                root.mainloop()
        
    except KeyboardInterrupt:
        print("\n\nОстановка ЭкоНет...")
        sys.exit(0)
    except Exception as e:
        print(f"\nОшибка запуска: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

