"""
Безопасная очистка неиспользуемых .md файлов
Архивирует отчеты и удаляет явно устаревшие документы
"""

import sys
import io
from pathlib import Path
import shutil
from datetime import datetime

# Настройка кодировки
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Критические файлы - НИКОГДА не удалять
CRITICAL_FILES = [
    'README.md',
    'ARCHITECTURE.md',
    'SETUP_GUIDE.md',
    'QUICKSTART.md',
    'PROJECT_STRUCTURE.md',
]

# Файлы для архивации (отчеты о фиксах и статусах)
FILES_TO_ARCHIVE = [
    # Отчеты о фиксах (fix_report)
    'BUGFIX_CRASHES.md',
    'CODE_REVIEW_AND_FIXES.md',
    'CRASH_FIX_APPLIED.md',
    'CTKIMAGE_FIX.md',
    'DETECTION_DEBUG_FIX.md',
    'DOCUMENTATION_FIXES.md',
    'EVENT_LOOP_FIX.md',
    'FIXED_AND_READY.md',
    'FIXES_APPLIED.md',
    'LOGICAL_ERRORS_FIXED.md',
    'ONNX_PT_PRIORITY_FIX.md',
    'ONNX_SIZE_FIX.md',
    'QUICK_FIX.md',
    'SYNTAX_ERROR_FIXED.md',
    'SYNTAX_FIX.md',
    'VIDEO_CRASH_FIX.md',
    'VIDEO_DETECTION_FIX.md',
    'VIDEO_DISPLAY_FIX.md',
    'VIDEO_FIX_COMPLETE.md',
    'VIDEO_FIX.md',
    'VIDEO_PREPROCESSING_FIX.md',
    
    # Отчеты о статусах (status_report)
    'COMPREHENSIVE_CHECK.md',
    'DOCUMENTATION_STATUS.md',
    'DOCUMENTATION_VERIFICATION_REPORT.md',
    'FINAL_CHECK_REPORT.md',
    'FINAL_STATUS.md',
    'MODEL_STATUS_INFO.md',
    'SYSTEM_CHECK.md',
    
    # Отчеты об обновлениях (update)
    'DETECTION_MAXIMIZATION_SUMMARY.md',
    'DOCUMENTATION_SUMMARY.md',
    'IMPROVEMENTS_SUMMARY.md',
    'SUMMARY_2025_UPDATE.md',
    
    # Отчеты об оптимизации
    'FPS_OPTIMIZATION_60.md',
    'FPS_OPTIMIZATIONS_APPLIED.md',
    'GPU_OPTIMIZATION_UPDATE.md',
    'MAX_DETECTION_OPTIMIZATION.md',
    'RESOURCE_OPTIMIZATION.md',
    
    # Временные отчеты
    'AUTO_PROCESSING_AND_TESTING.md',
    'DETECTION_DIAGNOSTICS.md',
    'DOCUMENTATION_COMPLETE_REVIEW.md',
    'FINAL_CODE_REVIEW.md',
    'FULL_SETUP_AND_TEST.md',
    'GPU_COMPONENTS_CHECK_RESULT.md',
    'GPU_INSTALLATION_SUCCESS.md',
    'GPU_SETUP_SUMMARY.md',
    'OBJECT_TRACKING_AND_STATS.md',
    'QUICK_START_SELF_AWARENESS.md',
    'QUICK_TEST.md',
    'SCRIPTS_CLEANUP_COMPLETE.md',
    'SCRIPTS_CLEANUP_REPORT.md',
    'SCRIPTS_FINAL_REPORT.md',
    'SCRIPTS_STATUS_FINAL.md',
    'PRE_TRAINING_CHECK_SUMMARY.md',
]

# Файлы для удаления (явно устаревшие или дубликаты)
FILES_TO_REMOVE = [
    # Устаревшие guide (есть более новые версии)
    'LLM_INTEGRATION_GUIDE.md',  # LLM удален
    'MODERN_INTERFACE_GUIDE.md',  # Дубликат MATERIAL_DESIGN_INTERFACE.md
    'GUI_GUIDE.md',  # Дубликат MATERIAL_DESIGN_INTERFACE.md
    'VIDEO_TESTING_GUIDE.md',  # Дубликат TESTING_WITH_WEBCAM.md
    'DATASET_CLEANUP_GUIDE.md',  # Информация есть в других местах
    
    # Устаревшие компоненты
    'TEST_VIDEO_STEP_BY_STEP.md',  # Дубликат VIDEO_TESTING_GUIDE.md
    'VIDEO_PLAYER_INTEGRATION.md',  # Видеоплеер удален
    'ECONET_UNIFIED_ARCHITECTURE.md',  # Дубликат ARCHITECTURE.md
    
    # Временные файлы
    'TRAINING_GPU_READY.md',  # Информация в других файлах
]

def main():
    """Главная функция"""
    project_root = Path(__file__).parent.parent
    archive_dir = project_root / "docs" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("ОЧИСТКА НЕИСПОЛЬЗУЕМЫХ .MD ФАЙЛОВ")
    print("=" * 70)
    
    # Архивирование
    print("\n1. АРХИВИРОВАНИЕ ОТЧЕТОВ")
    print("-" * 70)
    
    archived_count = 0
    for md_name in FILES_TO_ARCHIVE:
        md_path = project_root / md_name
        if md_path.exists():
            try:
                archive_path = archive_dir / md_name
                shutil.move(str(md_path), str(archive_path))
                print(f"  [OK] Архивирован: {md_name}")
                archived_count += 1
            except Exception as e:
                print(f"  [FAIL] Не удалось архивировать {md_name}: {e}")
        else:
            print(f"  [INFO] Не найден: {md_name}")
    
    # Удаление устаревших
    print("\n2. УДАЛЕНИЕ УСТАРЕВШИХ ФАЙЛОВ")
    print("-" * 70)
    
    removed_count = 0
    for md_name in FILES_TO_REMOVE:
        md_path = project_root / md_name
        if md_path.exists():
            # Проверка что это не критический файл
            if md_name in CRITICAL_FILES:
                print(f"  [SKIP] Критический файл, пропуск: {md_name}")
                continue
            
            try:
                md_path.unlink()
                print(f"  [OK] Удален: {md_name}")
                removed_count += 1
            except Exception as e:
                print(f"  [FAIL] Не удалось удалить {md_name}: {e}")
        else:
            print(f"  [INFO] Не найден: {md_name}")
    
    # Итоги
    print("\n" + "=" * 70)
    print("ИТОГИ")
    print("=" * 70)
    print(f"Архивировано файлов: {archived_count}")
    print(f"Удалено файлов: {removed_count}")
    print(f"Всего обработано: {archived_count + removed_count}")
    print(f"\nАрхив: {archive_dir}")
    print("\n✅ Очистка завершена!")
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

