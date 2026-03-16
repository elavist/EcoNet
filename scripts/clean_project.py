"""
Скрипт для очистки проекта от ненужных файлов
"""
import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_pycache():
    """Очистка всех __pycache__ директорий"""
    project_root = Path(__file__).parent.parent
    removed_count = 0
    total_size = 0
    
    for pycache_dir in project_root.rglob("__pycache__"):
        try:
            if pycache_dir.is_dir():
                # Подсчет размера
                size = sum(f.stat().st_size for f in pycache_dir.rglob("*") if f.is_file())
                shutil.rmtree(pycache_dir)
                removed_count += 1
                total_size += size
                logger.info(f"✅ Удален: {pycache_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить {pycache_dir}: {e}")
    
    logger.info(f"✅ Очищено __pycache__: {removed_count} директорий ({total_size / 1024:.2f} KB)")
    return removed_count, total_size


def clean_pyc_files():
    """Очистка всех .pyc файлов"""
    project_root = Path(__file__).parent.parent
    removed_count = 0
    total_size = 0
    
    for pyc_file in project_root.rglob("*.pyc"):
        try:
            size = pyc_file.stat().st_size
            pyc_file.unlink()
            removed_count += 1
            total_size += size
            logger.debug(f"✅ Удален: {pyc_file}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить {pyc_file}: {e}")
    
    logger.info(f"✅ Очищено .pyc файлов: {removed_count} файлов ({total_size / 1024:.2f} KB)")
    return removed_count, total_size


def clean_cache_files():
    """Очистка .cache файлов"""
    project_root = Path(__file__).parent.parent
    removed_count = 0
    total_size = 0
    
    # Игнорируем YOLOv8-main (внешняя библиотека)
    for cache_file in project_root.rglob("*.cache"):
        if "YOLOv8-main" in str(cache_file):
            continue
        try:
            size = cache_file.stat().st_size
            cache_file.unlink()
            removed_count += 1
            total_size += size
            logger.info(f"✅ Удален: {cache_file}")
        except Exception as e:
            logger.warning(f"⚠️ Не удалось удалить {cache_file}: {e}")
    
    logger.info(f"✅ Очищено .cache файлов: {removed_count} файлов ({total_size / 1024:.2f} KB)")
    return removed_count, total_size


def main():
    """Главная функция очистки"""
    logger.info("🧹 Начало очистки проекта...")
    
    total_removed = 0
    total_size = 0
    
    # Очистка __pycache__
    count, size = clean_pycache()
    total_removed += count
    total_size += size
    
    # Очистка .pyc файлов
    count, size = clean_pyc_files()
    total_removed += count
    total_size += size
    
    # Очистка .cache файлов (кроме YOLOv8)
    count, size = clean_cache_files()
    total_removed += count
    total_size += size
    
    logger.info(f"✅ Очистка завершена: {total_removed} элементов, {total_size / 1024:.2f} KB")


if __name__ == "__main__":
    main()

