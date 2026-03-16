"""
Инструмент для ручной разметки (annotation) изображений для обучения
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import shutil
from datetime import datetime
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class AnnotationTool:
    """Инструмент для ручной разметки изображений"""
    
    def __init__(self, config: Dict, project_root: Path):
        """
        Инициализация инструмента разметки
        
        Args:
            config: Конфигурация системы
            project_root: Корень проекта
        """
        self.config = config
        self.project_root = project_root
        self.dataset_config = config.get("dataset", {})
        dataset_base_path = self.dataset_config.get("base_path", "datasets/cigarette_butt")
        self.dataset_base = Path(dataset_base_path) if Path(dataset_base_path).is_absolute() else self.project_root / dataset_base_path
        self.train_images = self.dataset_base / "train" / "images"
        self.train_labels = self.dataset_base / "train" / "labels"
        
        # Создание директорий
        self.train_images.mkdir(parents=True, exist_ok=True)
        self.train_labels.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✅ AnnotationTool инициализирован: {self.train_images}")
        
    def save_annotation(self, image_path: Path, bboxes: List[Dict], save_annotated_image: bool = True) -> Dict:
        """
        Сохранить аннотацию изображения
        
        Args:
            image_path: Путь к исходному изображению
            bboxes: Список боксов [{"bbox": [x, y, w, h], "class": int, "confidence": 1.0}, ...]
            save_annotated_image: Сохранить изображение с нарисованными боксами
            
        Returns:
            Словарь с результатами сохранения
        """
        try:
            if not image_path.exists():
                logger.error(f"❌ Изображение не найдено: {image_path}")
                return {"success": False, "error": "Изображение не найдено"}
            
            # Загрузка изображения
            image = cv2.imread(str(image_path))
            if image is None:
                logger.error(f"❌ Не удалось загрузить изображение: {image_path}")
                return {"success": False, "error": "Не удалось загрузить изображение"}
            
            # Генерация уникального имени файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = image_path.stem
            image_filename = f"{base_name}_{timestamp}.jpg"
            label_filename = f"{base_name}_{timestamp}.txt"
            annotated_filename = f"{base_name}_{timestamp}_annotated.jpg"
            
            # Пути для сохранения
            saved_image_path = self.train_images / image_filename
            saved_label_path = self.train_labels / label_filename
            annotated_image_path = self.train_images / annotated_filename if save_annotated_image else None
            
            # Копирование оригинала
            shutil.copy2(image_path, saved_image_path)
            logger.info(f"✅ Изображение сохранено: {saved_image_path}")
            
            # Сохранение аннотаций в формате YOLO (класс x_center y_center width height - нормализованные)
            image_height, image_width = image.shape[:2]
            yolo_annotations = []
            
            for bbox in bboxes:
                x, y, w, h = bbox.get("bbox", [0, 0, 0, 0])
                class_id = bbox.get("class", 0)
                
                # Конвертация в формат YOLO (нормализованные координаты)
                x_center = (x + w / 2) / image_width
                y_center = (y + h / 2) / image_height
                width_norm = w / image_width
                height_norm = h / image_height
                
                # Формат YOLO: class_id x_center y_center width height
                yolo_annotations.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width_norm:.6f} {height_norm:.6f}")
            
            # Сохранение аннотаций
            with open(saved_label_path, 'w') as f:
                f.write('\n'.join(yolo_annotations))
            logger.info(f"✅ Аннотации сохранены: {saved_label_path} ({len(yolo_annotations)} объектов)")
            
            # Сохранение изображения с нарисованными боксами
            if save_annotated_image and annotated_image_path:
                annotated_image = image.copy()
                
                for bbox in bboxes:
                    x, y, w, h = bbox.get("bbox", [0, 0, 0, 0])
                    class_id = bbox.get("class", 0)
                    confidence = bbox.get("confidence", 1.0)
                    
                    # Рисование бокса
                    x1, y1 = int(x), int(y)
                    x2, y2 = int(x + w), int(y + h)
                    
                    # Цвет для бокса (зеленый для 100% confidence)
                    color = (0, 255, 0) if confidence >= 1.0 else (0, 165, 255)
                    thickness = 2
                    
                    cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, thickness)
                    
                    # Текст с меткой
                    label_text = f"class_{class_id} {confidence*100:.0f}%"
                    cv2.putText(annotated_image, label_text, (x1, y1 - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
                cv2.imwrite(str(annotated_image_path), annotated_image)
                logger.info(f"✅ Размеченное изображение сохранено: {annotated_image_path}")
            
            return {
                "success": True,
                "image_path": str(saved_image_path.relative_to(self.project_root)),
                "label_path": str(saved_label_path.relative_to(self.project_root)),
                "annotated_image_path": str(annotated_image_path.relative_to(self.project_root)) if annotated_image_path else None,
                "bboxes_count": len(bboxes)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения аннотации: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def add_label(self, image_path: Path, bbox: Dict, class_id: int = 0) -> bool:
        """
        Добавить метку к изображению (быстрый метод для одного бокса)
        
        Args:
            image_path: Путь к изображению
            bbox: Бокс {"bbox": [x, y, w, h], "confidence": 1.0}
            class_id: ID класса (по умолчанию 0 - cig_butt)
            
        Returns:
            True если успешно
        """
        bbox["class"] = class_id
        bbox["confidence"] = 1.0  # 100% confidence для ручной разметки
        
        result = self.save_annotation(image_path, [bbox], save_annotated_image=True)
        return result.get("success", False)

