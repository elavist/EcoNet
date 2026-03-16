"""
Менеджер медиа файлов
Управление загрузкой, копированием и хранением видео и фото
"""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json
import pickle

logger = logging.getLogger(__name__)


class MediaManager:
    """Менеджер медиа файлов для ЭкоНет"""
    
    def __init__(self, project_root: Path, media_dir: str = "data/media"):
        """
        Инициализация менеджера медиа
        
        Args:
            project_root: Корневая папка проекта
            media_dir: Относительный путь к папке медиа
        """
        self.project_root = Path(project_root)
        self.media_dir = self.project_root / media_dir
        self.videos_dir = self.media_dir / "videos"
        self.photos_dir = self.media_dir / "photos"
        self.detections_dir = self.media_dir / "detections"  # Папка для сохраненных детекций
        self.metadata_file = self.media_dir / "metadata.json"
        
        # Создание директорий
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        self.detections_dir.mkdir(parents=True, exist_ok=True)
        
        # Загрузка метаданных
        self.metadata = self._load_metadata()
        
        logger.info(f"✅ MediaManager инициализирован: {self.media_dir}")
    
    def _load_metadata(self) -> Dict:
        """Загрузка метаданных о файлах"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Ошибка загрузки метаданных: {e}")
        return {"videos": [], "photos": []}
    
    def _save_metadata(self):
        """Сохранение метаданных"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных: {e}")
    
    def import_file(self, source_path: str, file_type: str = "video") -> Optional[Dict]:
        """
        Импорт файла (копирование в проект)
        
        Args:
            source_path: Путь к исходному файлу
            file_type: Тип файла ("video" или "photo")
            
        Returns:
            Метаданные импортированного файла или None при ошибке
        """
        try:
            source = Path(source_path)
            if not source.exists():
                logger.error(f"Файл не найден: {source_path}")
                return None
            
            # Определение типа файла по расширению
            if file_type == "video":
                ext = source.suffix.lower()
                video_exts = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
                if ext not in video_exts:
                    logger.warning(f"Файл {source_path} не похож на видео")
                
                target_dir = self.videos_dir
                metadata_key = "videos"
            elif file_type == "photo":
                ext = source.suffix.lower()
                photo_exts = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
                if ext not in photo_exts:
                    logger.warning(f"Файл {source_path} не похож на фото")
                
                target_dir = self.photos_dir
                metadata_key = "photos"
            else:
                logger.error(f"Неизвестный тип файла: {file_type}")
                return None
            
            # Генерация уникального имени (с timestamp)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{timestamp}_{source.name}"
            target_path = target_dir / new_name
            
            # Копирование файла
            logger.info(f"📁 Копирование {file_type}: {source.name} → {new_name}")
            shutil.copy2(source, target_path)
            
            # Получение размера файла
            file_size = target_path.stat().st_size
            
            # Создание метаданных
            file_metadata = {
                "id": f"{file_type}_{timestamp}",
                "original_name": source.name,
                "name": new_name,
                "path": str(target_path.relative_to(self.project_root)),
                "full_path": str(target_path),
                "file_type": file_type,
                "size": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "imported_at": datetime.now().isoformat(),
                "source_path": str(source),
                "processed": False,  # Флаг обработки YOLO
                "detections_file": None,  # Путь к файлу с детекциями
                "processing_status": "pending"  # pending, processing, completed, error
            }
            
            # Добавление в метаданные
            if metadata_key not in self.metadata:
                self.metadata[metadata_key] = []
            self.metadata[metadata_key].append(file_metadata)
            self._save_metadata()
            
            logger.info(f"✅ Файл импортирован: {new_name} ({file_metadata['size_mb']} MB)")
            return file_metadata
            
        except Exception as e:
            logger.error(f"Ошибка импорта файла: {e}", exc_info=True)
            return None
    
    def get_files(self, file_type: Optional[str] = None) -> List[Dict]:
        """
        Получить список файлов
        
        Args:
            file_type: Тип файла ("video", "photo") или None для всех
            
        Returns:
            Список метаданных файлов
        """
        if file_type == "video":
            return self.metadata.get("videos", [])
        elif file_type == "photo":
            return self.metadata.get("photos", [])
        else:
            # Все файлы
            all_files = self.metadata.get("videos", []) + self.metadata.get("photos", [])
            # Сортировка по дате импорта (новые сначала)
            all_files.sort(key=lambda x: x.get("imported_at", ""), reverse=True)
            return all_files
    
    def get_file(self, file_id: str) -> Optional[Dict]:
        """Получить метаданные файла по ID"""
        for file_type in ["videos", "photos"]:
            for file_meta in self.metadata.get(file_type, []):
                if file_meta.get("id") == file_id:
                    return file_meta
        return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        Удалить файл
        
        Args:
            file_id: ID файла
            
        Returns:
            True если успешно
        """
        try:
            file_meta = self.get_file(file_id)
            if not file_meta:
                logger.error(f"Файл не найден: {file_id}")
                return False
            
            # Удаление файла
            file_path = Path(file_meta["full_path"])
            if file_path.exists():
                file_path.unlink()
                logger.info(f"🗑️ Файл удален: {file_path.name}")
            
            # Удаление из метаданных
            file_type = file_meta["file_type"]
            metadata_key = f"{file_type}s"
            if metadata_key in self.metadata:
                self.metadata[metadata_key] = [
                    f for f in self.metadata[metadata_key] if f.get("id") != file_id
                ]
                self._save_metadata()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления файла: {e}", exc_info=True)
            return False
    
    def get_file_path(self, file_id: str) -> Optional[Path]:
        """Получить полный путь к файлу по ID"""
        file_meta = self.get_file(file_id)
        if file_meta:
            return Path(file_meta["full_path"])
        return None
    
    def save_detections(self, file_id: str, detections_data: Dict) -> bool:
        """
        Сохранить детекции для файла
        
        Args:
            file_id: ID файла
            detections_data: Словарь с детекциями {frame_number: [detections]}
            
        Returns:
            True если успешно
        """
        try:
            file_meta = self.get_file(file_id)
            if not file_meta:
                logger.error(f"Файл не найден: {file_id}")
                return False
            
            # Путь к файлу детекций
            detections_file = self.detections_dir / f"{file_id}_detections.pkl"
            
            # Сохранение детекций
            with open(detections_file, 'wb') as f:
                pickle.dump(detections_data, f)
            
            # Обновление метаданных
            file_meta["detections_file"] = str(detections_file.relative_to(self.project_root))
            file_meta["processed"] = True
            file_meta["processing_status"] = "completed"
            self._save_metadata()
            
            logger.info(f"✅ Детекции сохранены: {detections_file.name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения детекций: {e}", exc_info=True)
            return False
    
    def load_detections(self, file_id: str) -> Optional[Dict]:
        """
        Загрузить детекции для файла
        
        Args:
            file_id: ID файла
            
        Returns:
            Словарь с детекциями {frame_number: [detections]} или None
        """
        try:
            file_meta = self.get_file(file_id)
            if not file_meta:
                return None
            
            detections_path = file_meta.get("detections_file")
            if not detections_path:
                return None
            
            # Полный путь к файлу
            detections_file = self.project_root / detections_path
            if not detections_file.exists():
                logger.warning(f"Файл детекций не найден: {detections_file}")
                return None
            
            # Загрузка детекций
            with open(detections_file, 'rb') as f:
                detections_data = pickle.load(f)
            
            logger.debug(f"✅ Детекции загружены: {file_id}")
            return detections_data
            
        except Exception as e:
            logger.error(f"Ошибка загрузки детекций: {e}", exc_info=True)
            return None
    
    def update_processing_status(self, file_id: str, status: str):
        """Обновить статус обработки файла"""
        try:
            file_meta = self.get_file(file_id)
            if file_meta:
                file_meta["processing_status"] = status
                self._save_metadata()
        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {e}")

