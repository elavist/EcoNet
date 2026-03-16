"""
Скрипт для переноса Ollama в папку проекта
Создает локальную копию Ollama в tools/ollama/
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def get_ollama_paths():
    """Найти пути к Ollama"""
    paths = []
    
    # Стандартные пути установки Ollama на Windows
    user_profile = os.getenv('USERPROFILE', '')
    if user_profile:
        standard_paths = [
            Path(user_profile) / "AppData" / "Local" / "Programs" / "Ollama",
            Path(user_profile) / ".ollama",
            Path("C:") / "Program Files" / "Ollama",
            Path("C:") / "Program Files (x86)" / "Ollama",
        ]
        paths.extend(standard_paths)
    
    # Добавляем путь указанный пользователем (если есть)
    custom_path = Path(r"C:\Users\elavi\AppData\Local\Programs\Ollama")
    if custom_path.exists() and custom_path not in paths:
        paths.insert(0, custom_path)  # Приоритет пользовательскому пути
    
    # Проверка через команду ollama
    try:
        result = subprocess.run(["ollama", "show", "serve", "--path"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            paths.append(Path(result.stdout.strip()))
    except:
        pass
    
    return paths

def find_ollama():
    """Найти установленный Ollama"""
    print("🔍 Поиск Ollama...")
    
    # Сначала проверяем пользовательский путь (приоритет)
    custom_path = Path(r"C:\Users\elavi\AppData\Local\Programs\Ollama")
    if custom_path.exists():
        ollama_exe = custom_path / "ollama.exe" if sys.platform == "win32" else custom_path / "ollama"
        if ollama_exe.exists():
            print(f"✅ Ollama найден по указанному пути: {custom_path}")
            return custom_path
    
    # Проверка через команду
    try:
        result = subprocess.run(["ollama", "--version"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print(f"✅ Ollama найден в PATH")
            print(f"   Версия: {result.stdout.strip()}")
            
            # Попытка найти исполняемый файл
            which_result = subprocess.run(["where", "ollama"] if sys.platform == "win32" else ["which", "ollama"],
                                         capture_output=True, text=True, timeout=5)
            if which_result.returncode == 0:
                ollama_exe = Path(which_result.stdout.strip().split('\n')[0])
                ollama_dir = ollama_exe.parent.parent
                print(f"   Путь: {ollama_dir}")
                return ollama_dir
    except Exception as e:
        print(f"   ⚠️ Ollama не найден в PATH: {e}")
    
    # Поиск в стандартных путях
    paths = get_ollama_paths()
    for path in paths:
        if path.exists():
            ollama_exe = path / "ollama.exe" if sys.platform == "win32" else path / "ollama"
            if ollama_exe.exists():
                print(f"✅ Ollama найден: {path}")
                return path
    
    print("❌ Ollama не найден")
    print(f"💡 Проверьте путь: {custom_path}")
    return None

def copy_ollama_to_project(ollama_path: Path, project_root: Path):
    """Копирование Ollama в папку проекта"""
    tools_dir = project_root / "tools"
    ollama_dir = tools_dir / "ollama"
    
    print(f"\n📦 Копирование Ollama...")
    print(f"   Из: {ollama_path}")
    print(f"   В: {ollama_dir}")
    
    try:
        # Создание директории
        ollama_dir.mkdir(parents=True, exist_ok=True)
        
        # Копирование файлов
        if sys.platform == "win32":
            # Windows: копируем ollama.exe и необходимые файлы
            files_to_copy = [
                "ollama.exe",
                "ollama.dll" if (ollama_path / "ollama.dll").exists() else None,
            ]
            
            for file in files_to_copy:
                if file and (ollama_path / file).exists():
                    shutil.copy2(ollama_path / file, ollama_dir / file)
                    print(f"   ✅ Скопирован: {file}")
        else:
            # Linux/Mac: копируем бинарный файл
            shutil.copy2(ollama_path / "ollama", ollama_dir / "ollama")
            # Установка прав на выполнение
            os.chmod(ollama_dir / "ollama", 0o755)
            print(f"   ✅ Скопирован: ollama")
        
        print(f"\n✅ Ollama скопирован в: {ollama_dir}")
        return ollama_dir
        
    except Exception as e:
        print(f"❌ Ошибка копирования: {e}")
        return None

def create_run_script(ollama_dir: Path, project_root: Path):
    """Создание скрипта для запуска Ollama"""
    if sys.platform == "win32":
        script_path = project_root / "tools" / "ollama" / "start_ollama.bat"
        script_content = f"""@echo off
cd /d "%~dp0"
echo Запуск Ollama из папки проекта...
ollama.exe serve
pause
"""
    else:
        script_path = project_root / "tools" / "ollama" / "start_ollama.sh"
        script_content = f"""#!/bin/bash
cd "$(dirname "$0")"
echo "Запуск Ollama из папки проекта..."
./ollama serve
"""
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        if sys.platform != "win32":
            os.chmod(script_path, 0o755)
        
        print(f"✅ Создан скрипт запуска: {script_path}")
        return script_path
    except Exception as e:
        print(f"⚠️ Не удалось создать скрипт: {e}")
        return None

def update_config(project_root: Path):
    """Обновление конфига для использования локального Ollama"""
    config_path = project_root / "config" / "config.yaml"
    
    if not config_path.exists():
        print(f"⚠️ Конфиг не найден: {config_path}")
        return
    
    try:
        import yaml
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Обновление пути к Ollama
        if 'chat' not in config:
            config['chat'] = {}
        
        ollama_dir = project_root / "tools" / "ollama"
        ollama_exe = ollama_dir / ("ollama.exe" if sys.platform == "win32" else "ollama")
        
        if ollama_exe.exists():
            config['chat']['ollama_path'] = str(ollama_exe)
            print(f"✅ Конфиг обновлен: ollama_path = {ollama_exe}")
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
        
    except Exception as e:
        print(f"⚠️ Ошибка обновления конфига: {e}")

def main():
    """Главная функция"""
    print("="*70)
    print("🔄 ПЕРЕНОС OLLAMA В ПАПКУ ПРОЕКТА")
    print("="*70)
    
    project_root = Path(__file__).parent.parent
    
    # Поиск Ollama
    ollama_path = find_ollama()
    if not ollama_path:
        print("\n❌ Ollama не найден!")
        print("\n💡 Решения:")
        print("   1. Установите Ollama: https://ollama.ai/download")
        print("   2. Или укажите путь вручную в скрипте")
        return
    
    # Копирование
    ollama_dir = copy_ollama_to_project(ollama_path, project_root)
    if not ollama_dir:
        return
    
    # Создание скрипта запуска
    create_run_script(ollama_dir, project_root)
    
    # Обновление конфига
    update_config(project_root)
    
    print("\n" + "="*70)
    print("✅ ГОТОВО!")
    print("="*70)
    print(f"\n📁 Ollama находится в: {ollama_dir}")
    print(f"\n🚀 Для запуска:")
    if sys.platform == "win32":
        print(f"   {ollama_dir / 'start_ollama.bat'}")
    else:
        print(f"   {ollama_dir / 'start_ollama.sh'}")
    print("\n💡 Или используйте системную версию: ollama serve")
    print("\n📝 Примечание: Модели Ollama хранятся в:")
    print(f"   {Path.home() / '.ollama' / 'models'}")

if __name__ == "__main__":
    main()

