"""
Скрипт для установки зависимостей с обработкой ошибок
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description=""):
    """Выполнить команду с обработкой ошибок"""
    print(f"\n{'='*60}")
    print(f"[INSTALL] {description}")
    print(f"[CMD] {command}")
    print('='*60)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            timeout=300,  # 5 минут таймаут
            capture_output=False
        )
        print(f"\n[OK] {description} - успешно!")
        return True
    except subprocess.TimeoutExpired:
        print(f"\n[ERROR] {description} - таймаут (более 5 минут)")
        return False
    except subprocess.CalledProcessError as e:
        print(f"\n[WARN] {description} - ошибка (код: {e.returncode})")
        print("[INFO] Продолжаем установку остальных зависимостей...")
        return False
    except KeyboardInterrupt:
        print(f"\n[WARN] {description} - прервано пользователем")
        return False

def main():
    project_root = Path(__file__).parent
    requirements_path = project_root / "requirements.txt"
    requirements_optional_path = project_root / "requirements-optional.txt"
    
    print("="*60)
    print("УСТАНОВКА ЗАВИСИМОСТЕЙ ПРОЕКТА")
    print("="*60)
    
    # Обновление pip
    print("\n[STEP 1] Обновление pip...")
    run_command(f"{sys.executable} -m pip install --upgrade pip", "Обновление pip")
    
    # Установка основных зависимостей
    print("\n[STEP 2] Установка основных зависимостей...")
    if requirements_path.exists():
        success = run_command(
            f"{sys.executable} -m pip install -r {requirements_path}",
            "Установка из requirements.txt"
        )
        if not success:
            print("\n[WARN] Некоторые зависимости не установились")
            print("[INFO] Попробуйте установить их вручную или увеличьте таймаут")
    else:
        print(f"[ERROR] Файл {requirements_path} не найден!")
        return False
    
    # Опциональная установка опциональных зависимостей
    print("\n[STEP 3] Опциональные зависимости...")
    if requirements_optional_path.exists():
        response = input("Установить опциональные зависимости (pynvml и др.)? [y/N]: ").strip().lower()
        if response == 'y':
            run_command(
                f"{sys.executable} -m pip install -r {requirements_optional_path}",
                "Установка опциональных зависимостей"
            )
        else:
            print("[INFO] Опциональные зависимости пропущены")
    else:
        print("[INFO] requirements-optional.txt не найден, пропускаем")
    
    # Проверка установки
    print("\n[STEP 4] Проверка установки...")
    check_script = project_root / "scripts" / "check_dependencies.py"
    if check_script.exists():
        print("[INFO] Запуск проверки зависимостей...")
        run_command(
            f"{sys.executable} {check_script}",
            "Проверка зависимостей"
        )
    else:
        print("[WARN] Скрипт проверки зависимостей не найден")
    
    print("\n" + "="*60)
    print("УСТАНОВКА ЗАВЕРШЕНА")
    print("="*60)
    print("\n[INFO] Если были ошибки, см. INSTALL_GUIDE.md для решения проблем")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[INFO] Установка прервана пользователем")
        sys.exit(1)

