"""
Анализ и очистка документации
Определяет устаревшие и дублирующиеся документы
"""
import sys
from pathlib import Path
from datetime import datetime
import shutil

# Критические файлы - НИКОГДА не удалять
CRITICAL_FILES = {
    'README.md',
    'ARCHITECTURE.md',
    'SETUP_GUIDE.md',
    'QUICKSTART.md',
    'PROJECT_STRUCTURE.md',
    'PROJECT_COMPLETE_OVERVIEW.md',
    'requirements.txt',
    'pytest.ini',
}

# Файлы для архивации (устаревшие отчеты)
FILES_TO_ARCHIVE = [
    # Старые отчеты о фиксах
    'BUGFIX_CRASHES.md',
    'CODE_REVIEW_AND_FIXES.md',
    'CRASH_FIX_APPLIED.md',
    'CTKIMAGE_FIX.md',
    'DETECTION_DEBUG_FIX.md',
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
    
    # Старые отчеты о статусах
    'COMPREHENSIVE_CHECK.md',
    'DOCUMENTATION_STATUS.md',
    'DOCUMENTATION_VERIFICATION_REPORT.md',
    'FINAL_CHECK_REPORT.md',
    'FINAL_STATUS.md',
    'MODEL_STATUS_INFO.md',
    'SYSTEM_CHECK.md',
    
    # Старые отчеты об обновлениях
    'DETECTION_MAXIMIZATION_SUMMARY.md',
    'DOCUMENTATION_SUMMARY.md',
    'IMPROVEMENTS_SUMMARY.md',
    'SUMMARY_2025_UPDATE.md',
    
    # Старые отчеты об оптимизации
    'FPS_OPTIMIZATION_60.md',
    'FPS_OPTIMIZATIONS_APPLIED.md',
    'GPU_OPTIMIZATION_UPDATE.md',
    'MAX_DETECTION_OPTIMIZATION.md',
    'RESOURCE_OPTIMIZATION.md',
    
    # Дублирующиеся отчеты о реструктуризации
    'RESTRUCTURE_STATUS.md',
    'RESTRUCTURE_SUMMARY.md',
    'RESTRUCTURE_PROGRESS.md',
    
    # Старые отчеты о тестах
    'TESTS_STATUS_REPORT.md',
    'TESTING_INFRASTRUCTURE_COMPLETE.md',
    
    # Устаревшие гайды
    'CHAT_LLM_REMOVAL.md',  # LLM удален
    'ONNX_REMOVED.md',
    'ONNX_VS_PT.md',
    'REMOVE_ONNX.md',
    'VIDEO_PLAYER_REMOVAL.md',
]

# Файлы для удаления (явно устаревшие)
FILES_TO_DELETE = [
    'MD_FILES_ANALYSIS_REPORT.md',
    'MD_FILES_CLEANUP_COMPLETE.md',
    'docx_content.txt',
    'extract_docx.py',
    'read_docx.py',
]

def main():
    """Главная функция"""
    project_root = Path(__file__).parent.parent
    archive_dir = project_root / "docs" / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("АНАЛИЗ И ОЧИСТКА ДОКУМЕНТАЦИИ")
    print("=" * 70)
    
    archived = 0
    deleted = 0
    
    # Архивация файлов
    print("\n[ARCHIVE] Archiving outdated documents:")
    for filename in FILES_TO_ARCHIVE:
        file_path = project_root / filename
        if file_path.exists():
            archive_path = archive_dir / filename
            if not archive_path.exists():
                shutil.move(str(file_path), str(archive_path))
                print(f"  [OK] {filename} -> docs/archive/")
                archived += 1
            else:
                file_path.unlink()  # Удаляем если уже в архиве
                print(f"  [DEL] {filename} (already in archive)")
                deleted += 1
    
    # Удаление файлов
    print("\n[DELETE] Removing outdated files:")
    for filename in FILES_TO_DELETE:
        file_path = project_root / filename
        if file_path.exists():
            file_path.unlink()
            print(f"  [OK] Deleted: {filename}")
            deleted += 1
    
    print("\n" + "=" * 70)
    print(f"РЕЗУЛЬТАТЫ:")
    print(f"  Архивировано: {archived}")
    print(f"  Удалено: {deleted}")
    print("=" * 70)

if __name__ == "__main__":
    main()

