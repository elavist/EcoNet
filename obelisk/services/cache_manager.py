"""
Менеджер кэша для очистки временных данных
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional
import shutil

logger = logging.getLogger(__name__)


class CacheManager:
    """Менеджер для управления кэшем системы"""
    
    def __init__(self, config: Dict, project_root: Path):
        """
        Инициализация менеджера кэша
        
        Args:
            config: Конфигурация системы
            project_root: Корень проекта
        """
        self.config = config
        self.project_root = project_root
        self.data_lake = config.get("data_lake", {})
        
    def clear_detection_cache(self, unified_engine) -> bool:
        """
        Очистка кэша детекций в UnifiedEngine
        
        Args:
            unified_engine: Экземпляр UnifiedEngine
            
        Returns:
            True если успешно
        """
        try:
            if hasattr(unified_engine, 'detection_cache'):
                cache_size = len(unified_engine.detection_cache)
                unified_engine.detection_cache.clear()
                logger.info(f"✅ Кэш детекций очищен: {cache_size} записей")
                return True
            else:
                logger.warning("⚠️ UnifiedEngine не имеет detection_cache")
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша детекций: {e}", exc_info=True)
            return False
    
    def clear_dataset_cache(self) -> Dict[str, int]:
        """
        Очистка кэша датасетов (.cache файлы)
        
        Returns:
            Словарь с результатами очистки
        """
        results = {
            "cleared_files": 0,
            "total_size": 0,
            "errors": []
        }
        
        try:
            dataset_base = Path(self.data_lake.get("base_path", "data"))
            
            # Поиск всех .cache файлов
            cache_files = list(dataset_base.rglob("*.cache"))
            cache_files.extend(list(Path("datasets").rglob("*.cache")))
            
            for cache_file in cache_files:
                try:
                    file_size = cache_file.stat().st_size
                    cache_file.unlink()
                    results["cleared_files"] += 1
                    results["total_size"] += file_size
                    logger.debug(f"🗑️ Удален кэш: {cache_file}")
                except Exception as e:
                    results["errors"].append(str(e))
                    logger.warning(f"⚠️ Не удалось удалить {cache_file}: {e}")
            
            if results["cleared_files"] > 0:
                logger.info(f"✅ Очищено кэшей датасетов: {results['cleared_files']} файлов ({results['total_size'] / 1024:.2f} KB)")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки кэша датасетов: {e}", exc_info=True)
            results["errors"].append(str(e))
            return results
    
    def clear_temp_files(self) -> Dict[str, int]:
        """
        Очистка временных файлов
        
        Returns:
            Словарь с результатами очистки
        """
        results = {
            "cleared_files": 0,
            "total_size": 0,
            "errors": []
        }
        
        try:
            temp_dirs = [
                Path("__pycache__"),
                Path(".pytest_cache"),
                Path(".mypy_cache"),
            ]
            
            # Поиск __pycache__ директорий
            for pycache_dir in Path(self.project_root).rglob("__pycache__"):
                try:
                    if pycache_dir.is_dir():
                        size = sum(f.stat().st_size for f in pycache_dir.rglob("*") if f.is_file())
                        shutil.rmtree(pycache_dir)
                        results["cleared_files"] += 1
                        results["total_size"] += size
                        logger.debug(f"🗑️ Удален __pycache__: {pycache_dir}")
                except Exception as e:
                    results["errors"].append(str(e))
                    logger.warning(f"⚠️ Не удалось удалить {pycache_dir}: {e}")
            
            if results["cleared_files"] > 0:
                logger.info(f"✅ Очищено временных файлов: {results['cleared_files']} директорий ({results['total_size'] / 1024:.2f} KB)")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки временных файлов: {e}", exc_info=True)
            results["errors"].append(str(e))
            return results
    
    def clear_all_cache(self, unified_engine=None) -> Dict[str, any]:
        """
        Полная очистка всего кэша
        
        Args:
            unified_engine: Экземпляр UnifiedEngine (опционально)
            
        Returns:
            Словарь с результатами очистки
        """
        results = {
            "detection_cache": False,
            "dataset_cache": {},
            "temp_files": {},
            "total_cleared": 0,
            "total_size": 0
        }
        
        logger.info("🧹 Начало полной очистки кэша...")
        
        # Очистка кэша детекций
        if unified_engine:
            results["detection_cache"] = self.clear_detection_cache(unified_engine)
        
        # Очистка кэша датасетов
        results["dataset_cache"] = self.clear_dataset_cache()
        results["total_cleared"] += results["dataset_cache"]["cleared_files"]
        results["total_size"] += results["dataset_cache"]["total_size"]
        
        # Очистка временных файлов
        results["temp_files"] = self.clear_temp_files()
        results["total_cleared"] += results["temp_files"]["cleared_files"]
        results["total_size"] += results["temp_files"]["total_size"]
        
        logger.info(f"✅ Полная очистка завершена: {results['total_cleared']} файлов ({results['total_size'] / 1024:.2f} KB)")
        
        return results

