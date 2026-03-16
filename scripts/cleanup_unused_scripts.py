"""
Безопасная очистка неиспользуемых скриптов
Удаляет только явно устаревшие скрипты
"""

import sys
import io
from pathlib import Path
import shutil

# Настройка кодировки
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Список скриптов для удаления (явно устаревшие)
SCRIPTS_TO_REMOVE = [
    # Дубликаты GPU установки
    "complete_gpu_installation.py",
    
    # Устаревшие chat скрипты (LLM удален)
    "chat_with_video.py",
    "chat_with_video_demo.py",
    "test_chat_response.py",
    "check_ollama.py",
    "test_ollama_integration.py",
]

# Скрипты для архивации (возможно еще нужны)
SCRIPTS_TO_ARCHIVE = [
    "check_and_update_model.py",  # Заменен validate_and_replace_model.py
]

def main():
    """Главная функция"""
    scripts_dir = Path(__file__).parent
    archive_dir = scripts_dir / "archive"
    
    print("=" * 70)
    print("ОЧИСТКА НЕИСПОЛЬЗУЕМЫХ СКРИПТОВ")
    print("=" * 70)
    
    # Удаление устаревших скриптов
    print("\n1. УДАЛЕНИЕ УСТАРЕВШИХ СКРИПТОВ")
    print("-" * 70)
    
    removed_count = 0
    for script_name in SCRIPTS_TO_REMOVE:
        script_path = scripts_dir / script_name
        if script_path.exists():
            try:
                script_path.unlink()
                print(f"  [OK] Удален: {script_name}")
                removed_count += 1
            except Exception as e:
                print(f"  [FAIL] Не удалось удалить {script_name}: {e}")
        else:
            print(f"  [INFO] Не найден: {script_name}")
    
    # Архивирование скриптов
    print("\n2. АРХИВИРОВАНИЕ СКРИПТОВ")
    print("-" * 70)
    
    archive_dir.mkdir(exist_ok=True)
    archived_count = 0
    
    for script_name in SCRIPTS_TO_ARCHIVE:
        script_path = scripts_dir / script_name
        if script_path.exists():
            try:
                archive_path = archive_dir / script_name
                shutil.move(str(script_path), str(archive_path))
                print(f"  [OK] Архивирован: {script_name}")
                archived_count += 1
            except Exception as e:
                print(f"  [FAIL] Не удалось архивировать {script_name}: {e}")
        else:
            print(f"  [INFO] Не найден: {script_name}")
    
    # Итоги
    print("\n" + "=" * 70)
    print("ИТОГИ")
    print("=" * 70)
    print(f"Удалено скриптов: {removed_count}")
    print(f"Архивировано скриптов: {archived_count}")
    print(f"\nАрхив: {archive_dir}")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARN] Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

