"""
Анализ использования .md файлов в проекте
Определяет какие документы актуальны, а какие можно удалить
"""

import sys
import io
from pathlib import Path
import re
from collections import defaultdict
from datetime import datetime

# Настройка кодировки
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def find_md_references(md_filename, project_root):
    """Найти все упоминания .md файла в проекте"""
    references = {
        'in_readme': False,
        'in_code': [],
        'in_docs': [],
        'in_bat': [],
        'link_count': 0
    }
    
    md_stem = Path(md_filename).stem.lower()
    
    # Поиск в README
    readme_path = project_root / "README.md"
    if readme_path.exists():
        try:
            content = readme_path.read_text(encoding='utf-8', errors='ignore').lower()
            if md_stem in content or md_filename.lower() in content:
                references['in_readme'] = True
                # Подсчет ссылок
                references['link_count'] += len(re.findall(rf'\[.*?\]\(.*?{re.escape(md_stem)}.*?\)', content))
        except:
            pass
    
    # Поиск в других .md файлах
    for md_file in project_root.rglob("*.md"):
        if md_file.name == md_filename:
            continue
        try:
            content = md_file.read_text(encoding='utf-8', errors='ignore')
            # Поиск ссылок
            links = re.findall(rf'\[.*?\]\(.*?{re.escape(md_filename)}.*?\)', content, re.IGNORECASE)
            if links:
                references['in_docs'].append(str(md_file.relative_to(project_root)))
                references['link_count'] += len(links)
            # Поиск упоминаний
            elif md_stem in content.lower() or md_filename.lower() in content.lower():
                references['in_docs'].append(str(md_file.relative_to(project_root)))
        except:
            pass
    
    # Поиск в Python файлах
    for py_file in project_root.rglob("*.py"):
        try:
            content = py_file.read_text(encoding='utf-8', errors='ignore')
            if md_stem in content.lower() or md_filename.lower() in content.lower():
                references['in_code'].append(str(py_file.relative_to(project_root)))
        except:
            pass
    
    # Поиск в bat файлах
    for bat_file in project_root.rglob("*.bat"):
        try:
            content = bat_file.read_text(encoding='utf-8', errors='ignore')
            if md_stem in content.lower() or md_filename.lower() in content.lower():
                references['in_bat'].append(str(bat_file.relative_to(project_root)))
        except:
            pass
    
    return references

def categorize_md_file(md_path):
    """Категоризация .md файла"""
    name = md_path.stem.lower()
    
    # Критические файлы
    if name in ['readme', 'architecture', 'setup_guide', 'quickstart']:
        return 'critical'
    
    # Руководства (guides)
    if 'guide' in name or 'guide' in md_path.parent.name.lower():
        return 'guide'
    
    # Отчеты о фиксах (fixes)
    if 'fix' in name or 'fixes' in name:
        return 'fix_report'
    
    # Статусы и проверки
    if 'status' in name or 'check' in name or 'report' in name:
        return 'status_report'
    
    # Оптимизации
    if 'optimization' in name or 'optimize' in name or 'fps' in name:
        return 'optimization'
    
    # Документация компонентов
    if any(comp in name for comp in ['component', 'model', 'cache', 'annotation', 'video', 'training', 'dataset']):
        return 'component_doc'
    
    # Архитектура
    if 'architecture' in name or 'system' in name or 'hierarchy' in name:
        return 'architecture'
    
    # Обновления
    if 'update' in name or 'summary' in name or 'progress' in name:
        return 'update'
    
    # Прочее
    return 'other'

def analyze_md_file(md_path, project_root):
    """Анализ одного .md файла"""
    md_name = md_path.name
    
    # Базовая информация
    try:
        stat = md_path.stat()
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime)
        age_days = (datetime.now() - mtime).days
    except:
        size = 0
        mtime = None
        age_days = 0
    
    info = {
        'name': md_name,
        'path': str(md_path.relative_to(project_root)),
        'size': size,
        'mtime': mtime,
        'age_days': age_days,
        'category': categorize_md_file(md_path),
        'references': find_md_references(md_name, project_root),
        'total_refs': 0,
        'status': 'unknown'
    }
    
    # Подсчет ссылок
    info['total_refs'] = (
        (1 if info['references']['in_readme'] else 0) +
        len(info['references']['in_docs']) +
        info['references']['link_count']
    )
    
    # Определение статуса
    if info['total_refs'] > 5 or info['category'] == 'critical':
        info['status'] = 'active'
    elif info['total_refs'] > 0:
        info['status'] = 'used'
    elif info['category'] == 'critical':
        info['status'] = 'used'  # Критические файлы всегда used
    else:
        info['status'] = 'unused'
    
    # Проверка на дубликаты и устаревшие отчеты
    if 'fix' in md_name.lower() and age_days > 30:
        info['likely_obsolete'] = True
    else:
        info['likely_obsolete'] = False
    
    return info

def main():
    """Главная функция"""
    project_root = Path(__file__).parent.parent
    
    print("=" * 70)
    print("АНАЛИЗ ИСПОЛЬЗОВАНИЯ .MD ФАЙЛОВ")
    print("=" * 70)
    
    # Сбор всех .md файлов
    md_files = []
    for md_file in sorted(project_root.rglob("*.md")):
        # Пропускаем файлы в подпапках YOLOv8-main
        if 'YOLOv8-main' in str(md_file):
            continue
        md_files.append(analyze_md_file(md_file, project_root))
    
    # Группировка по статусу
    by_status = defaultdict(list)
    by_category = defaultdict(list)
    
    for md in md_files:
        by_status[md['status']].append(md)
        by_category[md['category']].append(md)
    
    # Вывод результатов
    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТЫ АНАЛИЗА")
    print("=" * 70)
    
    # Активные файлы
    print("\n✅ АКТИВНЫЕ ФАЙЛЫ (используются часто):")
    for md in sorted(by_status['active'], key=lambda x: x['total_refs'], reverse=True)[:15]:
        print(f"  {md['name']:<50} {md['total_refs']:>3} ссылок  {md['category']}")
    
    # Используемые файлы
    print("\n📋 ИСПОЛЬЗУЕМЫЕ ФАЙЛЫ (упоминаются):")
    for md in sorted(by_status['used'], key=lambda x: x['total_refs'], reverse=True)[:15]:
        print(f"  {md['name']:<50} {md['total_refs']:>3} ссылок  {md['category']}")
    
    # Неиспользуемые файлы
    print("\n❌ НЕИСПОЛЬЗУЕМЫЕ ФАЙЛЫ (нет ссылок):")
    for md in sorted(by_status['unused'], key=lambda x: x['age_days'], reverse=True):
        obsolete_marker = " [УСТАРЕЛ]" if md['likely_obsolete'] else ""
        print(f"  {md['name']:<50} {md['category']:<20} возраст: {md['age_days']} дней{obsolete_marker}")
    
    # Группировка по категориям
    print("\n" + "=" * 70)
    print("ГРУППИРОВКА ПО КАТЕГОРИЯМ")
    print("=" * 70)
    
    for category in sorted(by_category.keys()):
        files_in_cat = by_category[category]
        print(f"\n{category.upper().replace('_', ' ')} ({len(files_in_cat)} файлов):")
        for md in sorted(files_in_cat, key=lambda x: x['total_refs'], reverse=True)[:10]:
            status_icon = "✅" if md['status'] == 'active' else "📋" if md['status'] == 'used' else "❌"
            obsolete_marker = " [УСТАРЕЛ]" if md['likely_obsolete'] else ""
            print(f"  {status_icon} {md['name']:<45} {md['total_refs']:>3} ссылок{obsolete_marker}")
        if len(files_in_cat) > 10:
            print(f"  ... и еще {len(files_in_cat) - 10} файлов")
    
    # Рекомендации
    print("\n" + "=" * 70)
    print("РЕКОМЕНДАЦИИ")
    print("=" * 70)
    
    # Отчеты о фиксах
    fix_reports = [md for md in md_files if md['category'] == 'fix_report']
    old_fix_reports = [md for md in fix_reports if md['age_days'] > 30 and md['total_refs'] == 0]
    if old_fix_reports:
        print(f"\n⚠️ Найдены старые отчеты о фиксах ({len(old_fix_reports)} файлов):")
        for md in sorted(old_fix_reports, key=lambda x: x['age_days'], reverse=True)[:10]:
            print(f"  - {md['name']} (возраст: {md['age_days']} дней)")
        print("  Рекомендация: Архивировать или удалить (фиксы уже применены)")
    
    # Статусы
    status_reports = [md for md in md_files if md['category'] == 'status_report']
    old_status = [md for md in status_reports if md['age_days'] > 60 and md['total_refs'] == 0]
    if old_status:
        print(f"\n⚠️ Найдены старые отчеты о статусе ({len(old_status)} файлов):")
        for md in sorted(old_status, key=lambda x: x['age_days'], reverse=True)[:10]:
            print(f"  - {md['name']} (возраст: {md['age_days']} дней)")
        print("  Рекомендация: Архивировать или удалить (устаревшие статусы)")
    
    # Обновления
    updates = [md for md in md_files if md['category'] == 'update']
    old_updates = [md for md in updates if md['age_days'] > 90 and md['total_refs'] == 0]
    if old_updates:
        print(f"\n⚠️ Найдены старые отчеты об обновлениях ({len(old_updates)} файлов):")
        for md in sorted(old_updates, key=lambda x: x['age_days'], reverse=True)[:10]:
            print(f"  - {md['name']} (возраст: {md['age_days']} дней)")
        print("  Рекомендация: Архивировать (историческая информация)")
    
    # Неиспользуемые файлы
    unused = by_status['unused']
    if unused:
        print(f"\n🗑️ Неиспользуемые файлы ({len(unused)}):")
        for md in sorted(unused, key=lambda x: x['category']):
            obsolete_marker = " [УСТАРЕЛ]" if md['likely_obsolete'] else ""
            print(f"  - {md['name']:<45} {md['category']:<20}{obsolete_marker}")
        print("  Рекомендация: Рассмотреть удаление или архивацию")
    
    # Итоговая статистика
    print("\n" + "=" * 70)
    print("ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 70)
    print(f"Всего .md файлов: {len(md_files)}")
    print(f"  Активных: {len(by_status['active'])}")
    print(f"  Используемых: {len(by_status['used'])}")
    print(f"  Неиспользуемых: {len(by_status['unused'])}")
    
    # Размеры
    total_size = sum(md['size'] for md in md_files)
    unused_size = sum(md['size'] for md in unused)
    print(f"\nРазмеры:")
    print(f"  Общий размер: {total_size / 1024:.1f} KB ({total_size / (1024*1024):.2f} MB)")
    print(f"  Неиспользуемых: {unused_size / 1024:.1f} KB ({unused_size / (1024*1024):.2f} MB)")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()

