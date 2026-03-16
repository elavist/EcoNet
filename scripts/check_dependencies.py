"""
Скрипт для проверки всех зависимостей проекта
Находит все импорты и сравнивает с requirements.txt
"""
import ast
import os
import sys
from pathlib import Path
from typing import Set, Dict, List
import re

# Стандартная библиотека Python (не нужно в requirements.txt)
STDLIB_MODULES = {
    'os', 'sys', 'json', 'logging', 'pathlib', 'typing', 'datetime', 'time',
    'asyncio', 'threading', 'multiprocessing', 'concurrent', 'collections',
    'functools', 'itertools', 'hashlib', 'base64', 'urllib', 'http',
    'socket', 'email', 'uuid', 'enum', 'abc', 'copy', 'pickle', 'sqlite3',
    'shutil', 'tempfile', 'glob', 're', 'math', 'random', 'string', 'io',
    'csv', 'xml', 'html', 'contextlib', 'dataclasses', 'traceback', 'warnings',
    'importlib', 'inspect', 'ast', 'builtins', 'weakref', 'gc', 'ctypes',
    'struct', 'array', 'bisect', 'heapq', 'queue', 'sched', 'locale',
    'calendar', 'codecs', 'unicodedata', 'textwrap', 'stringprep', 'readline',
    'rlcompleter', 'difflib', 'textwrap', 'string', 'pprint', 'reprlib',
    'html', 'http', 'urllib', 'email', 'json', 'mailcap', 'mailbox',
    'mimetypes', 'base64', 'binhex', 'binascii', 'quopri', 'uu', 'secrets',
    'argparse', 'platform', 'signal', 'subprocess', 'tkinter'
}

# Локальные модули проекта (не нужно в requirements.txt)
LOCAL_PACKAGES = {'obelisk', 'edge', 'robots', 'scripts', 'tests', 'config'}

def extract_imports_from_file(file_path: Path) -> Set[str]:
    """Извлекает все импорты из файла"""
    imports = set()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Парсинг через AST
        try:
            tree = ast.parse(content, filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name.split('.')[0]
                        imports.add(module)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module = node.module.split('.')[0]
                        imports.add(module)
        except SyntaxError:
            # Если не удалось распарсить, используем regex
            pass
        
        # Дополнительная проверка через regex для случаев, которые AST может пропустить
        import_pattern = r'^import\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'
        from_pattern = r'^from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z0-9_]*)*)\s+import'
        
        for line in content.split('\n'):
            # Убираем комментарии
            line = line.split('#')[0].strip()
            
            # Проверяем import
            match = re.match(import_pattern, line)
            if match:
                module = match.group(1).split('.')[0]
                imports.add(module)
            
            # Проверяем from ... import
            match = re.match(from_pattern, line)
            if match:
                module = match.group(1).split('.')[0]
                imports.add(module)
    
    except Exception as e:
        print(f"Ошибка при чтении {file_path}: {e}")
    
    return imports

def scan_project_for_imports(project_root: Path) -> Dict[str, Set[str]]:
    """Сканирует весь проект на наличие импортов"""
    imports_by_file = {}
    all_imports = set()
    
    # Директории для сканирования
    scan_dirs = ['obelisk', 'edge', 'robots', 'scripts']
    
    for dir_name in scan_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            continue
        
        for py_file in dir_path.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            
            file_imports = extract_imports_from_file(py_file)
            if file_imports:
                imports_by_file[str(py_file.relative_to(project_root))] = file_imports
                all_imports.update(file_imports)
    
    return {
        'by_file': imports_by_file,
        'all': all_imports
    }

def load_requirements(requirements_path: Path) -> Set[str]:
    """Загружает зависимости из requirements.txt"""
    requirements = set()
    
    if not requirements_path.exists():
        return requirements
    
    with open(requirements_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Извлекаем имя пакета (до >= или ==)
            package = re.split(r'[>=<!=]', line)[0].strip()
            # Убираем экстра зависимости (например, uvicorn[standard] -> uvicorn)
            package = package.split('[')[0].strip()
            requirements.add(package.lower())
    
    return requirements

def map_import_to_package(import_name: str) -> str:
    """Маппинг имени импорта на имя пакета в PyPI"""
    mapping = {
        'cv2': 'opencv-python',
        'PIL': 'pillow',
        'Image': 'pillow',
        'skimage': 'scikit-image',
        'sklearn': 'scikit-learn',
        'yaml': 'pyyaml',
        'dotenv': 'python-dotenv',
        'paho': 'paho-mqtt',
        'paho.mqtt': 'paho-mqtt',
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn',
        'pydantic': 'pydantic',
        'sqlalchemy': 'sqlalchemy',
        'alembic': 'alembic',
        'aiosqlite': 'aiosqlite',
        'pandas': 'pandas',
        'numpy': 'numpy',
        'ultralytics': 'ultralytics',
        'torch': 'torch',
        'torchvision': 'torchvision',
        'tqdm': 'tqdm',
        'pytest': 'pytest',
        'requests': 'requests',
        'aiohttp': 'aiohttp',
        'websockets': 'websockets',
        'mlflow': 'mlflow',
        'wandb': 'wandb',
        'openai': 'openai',
        'groq': 'groq',
        'google': 'google-generativeai',  # google может быть google-generativeai
        'google.generativeai': 'google-generativeai',
        'google.generative': 'google-generativeai',
        'customtkinter': 'customtkinter',
        'tkinter': None,  # Встроено в Python
        'psycopg2': 'psycopg2-binary',
        'onnxruntime': 'onnxruntime',
        'pynvml': 'pynvml',
    }
    
    # Проверяем точное совпадение
    if import_name in mapping:
        return mapping[import_name]
    
    # Проверяем начало (проверяем наиболее специфичные первыми)
    for key, value in sorted(mapping.items(), key=lambda x: -len(x[0])):
        if import_name.startswith(key):
            return value
    
    # Если не найдено, возвращаем имя импорта
    return import_name.lower().replace('_', '-')

def main():
    project_root = Path(__file__).parent.parent
    requirements_path = project_root / 'requirements.txt'
    
    print("[SCAN] Scanning project for imports...")
    print("=" * 60)
    
    # Сканируем проект
    imports_data = scan_project_for_imports(project_root)
    all_imports = imports_data['all']
    
    # Фильтруем стандартную библиотеку и локальные модули
    external_imports = {
        imp for imp in all_imports
        if imp not in STDLIB_MODULES and imp not in LOCAL_PACKAGES
    }
    
    print(f"\n[INFO] Found unique external imports: {len(external_imports)}")
    print(f"       Total imports: {len(all_imports)}")
    
    # Загружаем requirements.txt
    requirements = load_requirements(requirements_path)
    print(f"\n[INFO] Dependencies in requirements.txt: {len(requirements)}")
    
    # Преобразуем импорты в названия пакетов
    required_packages = set()
    import_to_package_map = {}
    
    for imp in external_imports:
        package = map_import_to_package(imp)
        if package:  # Если None, значит это встроенный модуль
            required_packages.add(package)
            import_to_package_map[imp] = package
    
    # Находим недостающие зависимости
    missing = required_packages - requirements
    extra = requirements - required_packages
    
    print("\n" + "=" * 60)
    print("[RESULTS] Dependency Check Results")
    print("=" * 60)
    
    if missing:
        print(f"\n[ERROR] MISSING dependencies ({len(missing)}):")
        for package in sorted(missing):
            # Находим импорты, которые требуют этот пакет
            related_imports = [
                imp for imp, pkg in import_to_package_map.items()
                if pkg == package
            ]
            print(f"   * {package}")
            if related_imports:
                print(f"     (used via: {', '.join(related_imports[:3])})")
    
    if extra:
        print(f"\n[WARN] UNUSED dependencies ({len(extra)}):")
        for package in sorted(extra):
            print(f"   * {package}")
    
    if not missing and not extra:
        print("\n[OK] All dependencies are correct!")
    
    # Показываем все внешние импорты
    print(f"\n[ALL] All external imports in project ({len(external_imports)}):")
    for imp in sorted(external_imports):
        package = map_import_to_package(imp)
        status = "[OK]" if package in requirements else "[MISS]"
        print(f"   {status} {imp:20s} -> {package or '(builtin)'}")
    
    # Генерируем список для добавления в requirements.txt
    if missing:
        print("\n" + "=" * 60)
        print("[ADD] Add these to requirements.txt:")
        print("=" * 60)
        for package in sorted(missing):
            print(f"{package}")
    
    return len(missing) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

