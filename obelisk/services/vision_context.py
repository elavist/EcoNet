"""
Модуль визуального контекста для ЭкоНет
Анализирует что видит система и предоставляет контекст для диалога
"""

import logging
import cv2
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class VisionContext:
    """
    Класс для анализа визуального контекста
    
    Функции:
    1. Анализ текущего кадра
    2. Извлечение информации о детекциях
    3. Анализ сцены (освещение, качество)
    4. Подготовка контекста для диалога
    """
    
    def __init__(self, detector=None):
        """
        Инициализация
        
        Args:
            detector: Экземпляр детектора для получения детекций
        """
        self.detector = detector
        self.current_frame = None
        self.current_detections = []
        self.frame_info = {}
        
    async def analyze_frame(self, frame: np.ndarray, detections: List[Dict]) -> Dict:
        """
        Анализ кадра и создание контекста
        
        Args:
            frame: Кадр изображения
            detections: Список детекций
        
        Returns:
            Словарь с визуальным контекстом
        """
        self.current_frame = frame
        self.current_detections = detections
        
        # Базовая информация о кадре
        height, width = frame.shape[:2]
        self.frame_info = {
            "width": width,
            "height": height,
            "timestamp": datetime.now().isoformat(),
            "detection_count": len(detections)
        }
        
        # Анализ качества изображения
        quality_info = self._analyze_image_quality(frame)
        
        # Анализ детекций
        detection_info = self._analyze_detections(detections, width, height)
        
        # Анализ сцены
        scene_info = self._analyze_scene(frame, detections)
        
        # Сборка контекста
        context = {
            "frame_info": self.frame_info,
            "detections": detections,
            "quality": quality_info,
            "detection_analysis": detection_info,
            "scene_analysis": scene_info,
            "summary": self._create_summary(detections, detection_info, scene_info)
        }
        
        return context
    
    def _analyze_image_quality(self, frame: np.ndarray) -> Dict:
        """Анализ качества изображения"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
        
        # Яркость
        brightness = np.mean(gray)
        
        # Контраст
        contrast = np.std(gray)
        
        # Резкость (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        # Оценка качества
        quality_score = "хорошее"
        if brightness < 50:
            quality_score = "темное"
        elif brightness > 200:
            quality_score = "переэкспонированное"
        elif contrast < 20:
            quality_score = "низкий контраст"
        elif sharpness < 100:
            quality_score = "размытое"
        
        return {
            "brightness": float(brightness),
            "contrast": float(contrast),
            "sharpness": float(sharpness),
            "quality_score": quality_score
        }
    
    def _analyze_detections(self, detections: List[Dict], width: int, height: int) -> Dict:
        """Анализ детекций"""
        if not detections:
            return {
                "count": 0,
                "average_confidence": 0.0,
                "distribution": "нет детекций"
            }
        
        confidences = [d.get('confidence', 0) for d in detections]
        avg_conf = sum(confidences) / len(confidences)
        max_conf = max(confidences)
        min_conf = min(confidences)
        
        # Распределение по кадру
        positions = []
        for det in detections:
            x, y, w, h = det.get('bbox', [0, 0, 0, 0])
            center_x = x + w / 2
            center_y = y + h / 2
            positions.append({
                "x": center_x / width,  # Нормализованные координаты
                "y": center_y / height
            })
        
        # Определение распределения
        distribution = "равномерное"
        if len(positions) > 1:
            x_coords = [p["x"] for p in positions]
            y_coords = [p["y"] for p in positions]
            
            x_std = np.std(x_coords)
            y_std = np.std(y_coords)
            
            if x_std < 0.2 and y_std < 0.2:
                distribution = "скученное"
            elif x_std > 0.4 or y_std > 0.4:
                distribution = "разбросанное"
        
        return {
            "count": len(detections),
            "average_confidence": float(avg_conf),
            "max_confidence": float(max_conf),
            "min_confidence": float(min_conf),
            "distribution": distribution,
            "positions": positions
        }
    
    def _analyze_scene(self, frame: np.ndarray, detections: List[Dict]) -> Dict:
        """Анализ сцены"""
        # Простой анализ цвета (определение типа поверхности)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h_mean = np.mean(hsv[:, :, 0])
        s_mean = np.mean(hsv[:, :, 1])
        v_mean = np.mean(hsv[:, :, 2])
        
        # Определение типа поверхности
        surface_type = "неизвестно"
        if s_mean < 30:  # Низкая насыщенность
            if v_mean > 200:
                surface_type = "светлая поверхность (асфальт, бетон)"
            elif v_mean < 50:
                surface_type = "темная поверхность"
            else:
                surface_type = "серая поверхность"
        else:
            if 40 < h_mean < 80:
                surface_type = "зеленая поверхность (трава)"
            elif 100 < h_mean < 130:
                surface_type = "синяя поверхность"
        
        # Оценка сложности сцены
        complexity = "простая"
        if len(detections) > 5:
            complexity = "сложная (много объектов)"
        elif self.frame_info.get("quality_score") != "хорошее":
            complexity = "сложная (плохое качество)"
        
        return {
            "surface_type": surface_type,
            "complexity": complexity,
            "hue_mean": float(h_mean),
            "saturation_mean": float(s_mean),
            "value_mean": float(v_mean)
        }
    
    def _create_summary(self, detections: List[Dict], detection_info: Dict, scene_info: Dict) -> str:
        """Создание краткого резюме"""
        count = len(detections)
        
        if count == 0:
            return f"Окурков не обнаружено. Сцена: {scene_info['surface_type']}, качество: {self.frame_info.get('quality_score', 'неизвестно')}."
        
        avg_conf = detection_info.get('average_confidence', 0)
        distribution = detection_info.get('distribution', 'неизвестно')
        
        summary = f"Обнаружено {count} окурков (средняя уверенность: {avg_conf:.1%}). "
        summary += f"Распределение: {distribution}. "
        summary += f"Сцена: {scene_info['surface_type']}."
        
        return summary
    
    def get_current_context(self) -> Dict:
        """Получить текущий контекст"""
        return {
            "detections": self.current_detections,
            "frame_info": self.frame_info
        }

