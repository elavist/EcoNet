"""
Анализ использования скриптов в проекте
Определяет какие скрипты актуальны, а какие можно удалить
"""

import sys
import io
from pathlib import Path
import re
from collections import defaultdict

# Настройка кодировки
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def find_script_references(script_name, project_root):
    """Найти все упоминания скрипта в проекте"""
    references = {
        'in_code': [],
        'in_docs': [],
        'in_bat': [],
        'imports': []
    }
    
    # Поиск в Python файлах
    for py_file in project_root.rglob("*.py"):
        if 'scripts' in str(py_file):
            continue  # Пропускаем сами скрипты
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            if script_name in content:
                references['in_code'].append(str(py_file.relative_to(project_root)))
        except:
            pass
    
    # Поиск в документации
    for md_file in project_root.rglob("*.md"):
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
            if script_name in content:
                references['in_docs'].append(str(md_file.relative_to(project_root)))
        except:
            pass
    
    # Поиск в bat файлах
    for bat_file in project_root.rglob("*.bat"):
        try:
            content = bat_file.read_text(encoding='utf-8', errors='ignore')
            if script_name in content:
                references['in_bat'].append(str(bat_file.relative_to(project_root)))
        except:
            pass
    
    # Поиск импортов
    script_path = project_root / "scripts" / script_name
    if script_path.exists():
        try:
            content = script_path.read_text(encoding='utf-8', errors='ignore')
            # Проверяем есть ли if __name__ == "__main__"
            if '__main__' in content:
                references['imports'].append('has_main')
        except:
            pass
    
    return references

def analyze_script(script_path, project_root):
    """Анализ одного скрипта"""
    script_name = script_path.name
    script_stem = script_path.stem
    
    # Базовая информация
    info = {
        'name': script_name,
        'path': str(script_path.relative_to(project_root)),
        'size': script_path.stat().st_size,
        'references': find_script_references(script_name, project_root),
        'references_stem': find_script_references(script_stem, project_root),
        'total_refs': 0,
        'status': 'unknown'
    }
    
    # Подсчет ссылок
    info['total_refs'] = (
        len(info['references']['in_code']) +
        len(info['references']['in_docs']) +
        len(info['references']['in_bat'])
    )
    
    # Определение статуса
    if info['total_refs'] > 5:
        info['status'] = 'active'
    elif info['total_refs'] > 0:
        info['status'] = 'used'
    else:
        info['status'] = 'unused'
    
    # Проверка на дубликаты
    if 'install' in script_name.lower() and 'gpu' in script_name.lower():
        info['category'] = 'gpu_setup'
    elif 'check' in script_name.lower() and 'gpu' in script_name.lower():
        info['category'] = 'gpu_check'
    elif 'chat' in script_name.lower():
        info['category'] = 'chat'  # Возможно устарело
    elif 'test' in script_name.lower():
        info['category'] = 'testing'
    elif 'train' in script_name.lower() or 'retrain' in script_name.lower():
        info['category'] = 'training'
    elif 'setup' in script_name.lower():
        info['category'] = 'setup'
    else:
        info['category'] = 'other'
    
    return info

def main():
    """Главная функция"""
    project_root = Path(__file__).parent.parent
    scripts_dir = project_root / "scripts"
    
    print("=" * 70)
    print("АНАЛИЗ ИСПОЛЬЗОВАНИЯ СКРИПТОВ")
    print("=" * 70)
    
    # Сбор всех скриптов
    scripts = []
    for script_file in sorted(scripts_dir.glob("*.py")):
        if script_file.name == "__init__.py" or script_file.name == "analyze_scripts_usage.py":
            continue
        scripts.append(analyze_script(script_file, project_root))
    
    # Группировка по статусу
    by_status = defaultdict(list)
    by_category = defaultdict(list)
    
    for script in scripts:
        by_status[script['status']].append(script)
        by_category[script['category']].append(script)
    
    # Вывод результатов
    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТЫ АНАЛИЗА")
    print("=" * 70)
    
    # Активные скрипты
    print("\n✅ АКТИВНЫЕ СКРИПТЫ (используются часто):")
    for script in sorted(by_status['active'], key=lambda x: x['total_refs'], reverse=True):
        print(f"  {script['name']:<40} {script['total_refs']:>3} ссылок")
        if script['references']['in_docs']:
            print(f"    Документация: {len(script['references']['in_docs'])} файлов")
    
    # Используемые скрипты
    print("\n📋 ИСПОЛЬЗУЕМЫЕ СКРИПТЫ (упоминаются):")
    for script in sorted(by_status['used'], key=lambda x: x['total_refs'], reverse=True):
        print(f"  {script['name']:<40} {script['total_refs']:>3} ссылок")
    
    # Неиспользуемые скрипты
    print("\n❌ НЕИСПОЛЬЗУЕМЫЕ СКРИПТЫ (нет ссылок):")
    for script in sorted(by_status['unused'], key=lambda x: x['name']):
        print(f"  {script['name']:<40} {script['category']}")
    
    # Группировка по категориям
    print("\n" + "=" * 70)
    print("ГРУППИРОВКА ПО КАТЕГОРИЯМ")
    print("=" * 70)
    
    for category in sorted(by_category.keys()):
        scripts_in_cat = by_category[category]
        print(f"\n{category.upper()}:")
        for script in sorted(scripts_in_cat, key=lambda x: x['total_refs'], reverse=True):
            status_icon = "✅" if script['status'] == 'active' else "📋" if script['status'] == 'used' else "❌"
            print(f"  {status_icon} {script['name']:<35} {script['total_refs']:>3} ссылок")
    
    # Рекомендации
    print("\n" + "=" * 70)
    print("РЕКОМЕНДАЦИИ")
    print("=" * 70)
    
    # Дубликаты GPU установки
    gpu_setup = [s for s in scripts if s['category'] == 'gpu_setup']
    if len(gpu_setup) > 1:
        print(f"\n⚠️ Найдены дубликаты GPU установки ({len(gpu_setup)} скрипта):")
        for script in gpu_setup:
            print(f"  - {script['name']} ({script['total_refs']} ссылок)")
        print("  Рекомендация: Оставить один основной скрипт")
    
    # Дубликаты GPU проверки
    gpu_check = [s for s in scripts if s['category'] == 'gpu_check']
    if len(gpu_check) > 1:
        print(f"\n⚠️ Найдены дубликаты GPU проверки ({len(gpu_check)} скрипта):")
        for script in gpu_check:
            print(f"  - {script['name']} ({script['total_refs']} ссылок)")
        print("  Рекомендация: Оставить один основной скрипт")
    
    # Устаревшие chat скрипты
    chat_scripts = [s for s in scripts if s['category'] == 'chat']
    if chat_scripts:
        print(f"\n⚠️ Найдены chat скрипты ({len(chat_scripts)} скриптов):")
        for script in chat_scripts:
            print(f"  - {script['name']} ({script['total_refs']} ссылок)")
        print("  Рекомендация: Проверить актуальность (LLM может быть удален)")
    
    # Неиспользуемые скрипты
    unused = by_status['unused']
    if unused:
        print(f"\n🗑️ Неиспользуемые скрипты ({len(unused)}):")
        for script in unused:
            print(f"  - {script['name']} ({script['category']})")
        print("  Рекомендация: Рассмотреть удаление или архивацию")
    
    # Итоговая статистика
    print("\n" + "=" * 70)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)
    print(f"Всего скриптов: {len(scripts)}")
    print(f"  Активных: {len(by_status['active'])}")
    print(f"  Используемых: {len(by_status['used'])}")
    print(f"  Неиспользуемых: {len(by_status['unused'])}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

