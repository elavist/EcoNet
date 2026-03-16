"""
Активное обучение - "Зародыш интеллекта"
Собирает неопределенные кадры из видео и автоматически дообучает модель
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json
import shutil
import yaml
from collections import deque

from ultralytics import YOLO
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ActiveLearner:
    """
    Система активного обучения - "зародыш интеллекта"
    
    Функции:
    1. Собирает кадры с низкой уверенностью (0.3-0.7)
    2. Собирает кадры с высокой уверенностью для подтверждения
    3. Автоматически размечает кадры (псевдо-лейблы)
    4. Периодически дообучает модель на новых данных
    5. Валидирует и деплоит улучшенную модель
    """
    
    def __init__(self, config: Dict, db, mqtt_client):
        """
        Инициализация активного обучения
        
        Args:
            config: Конфигурация системы
            db: База данных
            mqtt_client: MQTT клиент
        """
        self.config = config
        self.db = db
        self.mqtt_client = mqtt_client
        self.al_config = config.get("active_learning", {})
        
        # Пути
        self.raw_frames_path = Path(config["data_lake"]["raw_frames_path"])
        self.raw_frames_path.mkdir(parents=True, exist_ok=True)
        
        self.labeled_path = Path(config["data_lake"]["labeled_path"])
        self.labeled_path.mkdir(parents=True, exist_ok=True)
        
        self.models_path = Path(config["data_lake"]["models_path"])
        self.models_path.mkdir(parents=True, exist_ok=True)
        
        # Настройки сбора
        self.confidence_lower = self.al_config.get("confidence_lower", 0.3)
        self.confidence_upper = self.al_config.get("confidence_upper", 0.7)
        self.min_samples_for_retrain = self.al_config.get("min_samples_for_retrain", 100)
        
        # Буфер для кадров
        self.uncertain_frames: deque = deque(maxlen=1000)  # Кадры с низкой уверенностью
        self.high_conf_frames: deque = deque(maxlen=500)   # Кадры для подтверждения
        
        # Статистика
        self.collected_frames = 0
        self.auto_labeled_frames = 0
        self.retraining_count = 0
        
        # Модель для автоматической разметки
        self.labeling_model = None
        self._load_labeling_model()
        
        # Флаг работы
        self.running = False
    
    def _load_labeling_model(self):
        """Загрузка модели для автоматической разметки"""
        model_path = self.config.get("model", {}).get("weights_path", "models/cigarette_detector/best.pt")
        if Path(model_path).exists():
            try:
                self.labeling_model = YOLO(model_path)
                logger.info(f"✅ Модель для разметки загружена: {model_path}")
            except Exception as e:
                logger.error(f"Ошибка загрузки модели для разметки: {e}")
        else:
            logger.warning("Модель для разметки не найдена")
    
    async def process_detection(self, detection: Dict, frame: Optional[np.ndarray] = None):
        """
        Обработка детекции для активного обучения
        
        Args:
            detection: Словарь с детекцией
            frame: Кадр изображения (опционально)
        """
        if not self.al_config.get("enabled", False):
            return
        
        confidence = detection.get("confidence", 0)
        frame_id = detection.get("frame_id")
        
        # Сбор неопределенных кадров (0.3 - 0.7)
        if self.confidence_lower <= confidence <= self.confidence_upper:
            if frame is not None and frame_id:
                await self._collect_uncertain_frame(frame, detection, frame_id)
        
        # Сбор кадров с высокой уверенностью для подтверждения (0.85+)
        # Используем для расширения позитивных примеров
        if confidence >= 0.85 and frame is not None and frame_id:
            await self._collect_high_conf_frame(frame, detection, frame_id)
    
    async def _collect_uncertain_frame(self, frame: np.ndarray, detection: Dict, frame_id: str):
        """Сбор неопределенного кадра"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            frame_path = self.raw_frames_path / f"uncertain_{timestamp}_{frame_id}.jpg"
            
            # Сохранить кадр
            cv2.imwrite(str(frame_path), frame)
            
            # Сохранить метаданные
            metadata = {
                "frame_id": frame_id,
                "detection": detection,
                "collected_at": datetime.utcnow().isoformat(),
                "type": "uncertain",
                "confidence": detection.get("confidence")
            }
            
            metadata_path = frame_path.with_suffix(".json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            self.uncertain_frames.append({
                "frame_path": frame_path,
                "metadata_path": metadata_path,
                "detection": detection
            })
            
            self.collected_frames += 1
            
            if self.collected_frames % 10 == 0:
                logger.debug(f"Собрано неопределенных кадров: {len(self.uncertain_frames)}")
            
            # Проверка готовности к дообучению
            if len(self.uncertain_frames) >= self.min_samples_for_retrain:
                logger.info(f"✅ Набрано достаточно кадров для дообучения: {len(self.uncertain_frames)}")
                await self._trigger_retraining()
                
        except Exception as e:
            logger.error(f"Ошибка сбора неопределенного кадра: {e}")
    
    async def _collect_high_conf_frame(self, frame: np.ndarray, detection: Dict, frame_id: str):
        """Сбор кадра с высокой уверенностью для подтверждения"""
        try:
            # Собираем реже (каждый 10-й)
            if len(self.high_conf_frames) % 10 != 0:
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            frame_path = self.raw_frames_path / f"highconf_{timestamp}_{frame_id}.jpg"
            
            cv2.imwrite(str(frame_path), frame)
            
            metadata = {
                "frame_id": frame_id,
                "detection": detection,
                "collected_at": datetime.utcnow().isoformat(),
                "type": "high_confidence",
                "confidence": detection.get("confidence")
            }
            
            metadata_path = frame_path.with_suffix(".json")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            self.high_conf_frames.append({
                "frame_path": frame_path,
                "metadata_path": metadata_path,
                "detection": detection
            })
            
        except Exception as e:
            logger.error(f"Ошибка сбора кадра с высокой уверенностью: {e}")
    
    async def _auto_label_frame(self, frame_path: Path, detection: Dict) -> bool:
        """
        Автоматическая разметка кадра (псевдо-лейблы)
        
        Args:
            frame_path: Путь к кадру
            detection: Детекция для разметки
            
        Returns:
            Успех разметки
        """
        if not self.labeling_model:
            return False
        
        try:
            # Загрузить изображение
            img = cv2.imread(str(frame_path))
            if img is None:
                return False
            
            # Получить детекции от модели с низким порогом для автоматической разметки
            results = self.labeling_model(img, conf=0.25, verbose=False, imgsz=640)
            
            # Создать YOLO формат аннотаций
            h, w = img.shape[:2]
            label_lines = []
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    
                    # Принимаем только классы окурков
                    if cls == 0 or cls == 1 or result.names.get(cls) == 'cig_butt':
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        # Конвертировать в YOLO формат (нормализованные координаты центра)
                        x_center = ((x1 + x2) / 2) / w
                        y_center = ((y1 + y2) / 2) / h
                        width = (x2 - x1) / w
                        height = (y2 - y1) / h
                        
                        # Используем класс 1 (cig_butt) для всех детекций
                        class_id = 1
                        
                        label_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
            
            if label_lines:
                # Сохранить аннотацию
                label_path = self.labeled_path / f"{frame_path.stem}.txt"
                with open(label_path, 'w') as f:
                    f.write('\n'.join(label_lines))
                
                # Скопировать изображение в labeled
                labeled_img_path = self.labeled_path / frame_path.name
                shutil.copy(frame_path, labeled_img_path)
                
                self.auto_labeled_frames += 1
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Ошибка автоматической разметки: {e}")
            return False
    
    async def _trigger_retraining(self):
        """Запуск дообучения на собранных данных"""
        if self.retraining_count > 0 and len(self.uncertain_frames) < self.min_samples_for_retrain * 2:
            return  # Ждем больше данных для второго раунда
        
        logger.info("🧠 Активация интеллекта: начало автоматического дообучения...")
        
        try:
            # 1. Автоматическая разметка собранных кадров
            logger.info(f"📝 Автоматическая разметка {len(self.uncertain_frames)} кадров...")
            
            labeled_count = 0
            for frame_data in list(self.uncertain_frames):
                if await self._auto_label_frame(frame_data["frame_path"], frame_data["detection"]):
                    labeled_count += 1
            
            logger.info(f"✅ Размечено кадров: {labeled_count}/{len(self.uncertain_frames)}")
            
            if labeled_count < 50:  # Минимум для дообучения
                logger.warning(f"⚠️ Недостаточно размеченных кадров: {labeled_count} < 50")
                return
            
            # 2. Добавить размеченные данные в датасет
            await self._merge_labeled_to_dataset()
            
            # 3. Дообучение модели
            await self._retrain_model()
            
            # 4. Очистка обработанных кадров
            self.uncertain_frames.clear()
            self.collected_frames = 0
            
            self.retraining_count += 1
            
        except Exception as e:
            logger.error(f"Ошибка активного обучения: {e}", exc_info=True)
    
    async def _merge_labeled_to_dataset(self):
        """Объединение размеченных данных с основным датасетом"""
        try:
            labeled_images = list(self.labeled_path.glob("*.jpg"))
            
            if not labeled_images:
                logger.warning("Нет размеченных изображений для объединения")
                return
            
            # Копировать в train датасет
            train_images_path = Path(self.config["dataset"]["train_path"])
            train_labels_path = train_images_path.parent.parent / "train" / "labels"
            train_labels_path.mkdir(parents=True, exist_ok=True)
            
            copied = 0
            for img_path in labeled_images:
                label_path = img_path.with_suffix(".txt")
                
                if label_path.exists():
                    # Копировать изображение
                    train_img_path = train_images_path / img_path.name
                    shutil.copy(img_path, train_img_path)
                    
                    # Копировать аннотацию
                    train_label_path = train_labels_path / label_path.name
                    shutil.copy(label_path, train_label_path)
                    
                    copied += 1
            
            logger.info(f"✅ Добавлено в датасет: {copied} изображений")
            
        except Exception as e:
            logger.error(f"Ошибка объединения данных: {e}")
    
    async def _retrain_model(self):
        """Дообучение модели на новых данных"""
        try:
            logger.info("🎓 Начало дообучения модели...")
            
            # Загрузка текущей модели
            model_path = self.config.get("model", {}).get("weights_path", "models/cigarette_detector/best.pt")
            model = YOLO(model_path)
            
            # Параметры дообучения
            data_config = self.config["dataset"]["base_path"] + "/data.yaml"
            
            # Быстрое дообучение (5-10 эпох для incremental learning)
            results = model.train(
                data=data_config,
                epochs=self.al_config.get("retrain_epochs", 10),
                batch=self.al_config.get("retrain_batch_size", 16),
                imgsz=self.config.get("model", {}).get("input_size", 640),
                project="models/cigarette_detector",
                name=f"active_learning_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                save=True,
                exist_ok=True,
                resume=False,
                pretrained=False  # Использовать текущие веса
            )
            
            # Проверка улучшения
            new_precision = results.results_dict.get('metrics/precision(B)', 0)
            new_map = results.results_dict.get('metrics/mAP50(B)', 0)
            
            logger.info(f"📊 Результаты дообучения:")
            logger.info(f"   Precision: {new_precision:.4f} ({new_precision*100:.2f}%)")
            logger.info(f"   mAP@0.5: {new_map:.4f}")
            
            # Проверка улучшения
            min_improvement = self.al_config.get("min_improvement", 0.02)
            
            # Загрузить предыдущую модель для сравнения
            prev_model = YOLO(model_path)
            prev_metrics = prev_model.val(data=data_config, verbose=False)
            prev_precision = prev_metrics.results_dict.get('metrics/precision(B)', 0)
            
            improvement = new_precision - prev_precision
            
            if improvement >= min_improvement:
                logger.info(f"✅ Улучшение на {improvement:.4f} - деплой новой модели")
                
                # Скопировать новую модель
                best_model_path = Path(results.save_dir) / "weights" / "best.pt"
                if best_model_path.exists():
                    target_model = Path(model_path)
                    shutil.copy(best_model_path, target_model)
                    
                    # Обновить модель для разметки
                    self._load_labeling_model()
                    
                    # Уведомить через MQTT
                    if self.mqtt_client:
                        await self.mqtt_client.publish("obelisk/model/update", {
                            "type": "active_learning",
                            "improvement": improvement,
                            "new_precision": new_precision,
                            "model_path": str(target_model)
                        })
                    
                    logger.info("🚀 Новая модель задеплоена!")
            else:
                logger.info(f"⚠️ Улучшение {improvement:.4f} < {min_improvement} - модель не обновлена")
            
        except Exception as e:
            logger.error(f"Ошибка дообучения: {e}", exc_info=True)
    
    async def learning_loop(self):
        """Главный цикл активного обучения"""
        self.running = True
        logger.info("🧠 Активное обучение запущено - 'Зародыш интеллекта' активирован")
        
        while self.running:
            try:
                # Периодическая проверка и дообучение
                await asyncio.sleep(self.al_config.get("check_interval", 3600))  # Каждый час
                
                # Если накопилось достаточно данных, запустить дообучение
                if len(self.uncertain_frames) >= self.min_samples_for_retrain:
                    await self._trigger_retraining()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в learning loop: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        """Остановка активного обучения"""
        self.running = False
        logger.info("Активное обучение остановлено")
    
    def get_statistics(self) -> Dict:
        """Получить статистику активного обучения"""
        return {
            "enabled": self.al_config.get("enabled", False),
            "collected_frames": self.collected_frames,
            "uncertain_frames": len(self.uncertain_frames),
            "high_conf_frames": len(self.high_conf_frames),
            "auto_labeled_frames": self.auto_labeled_frames,
            "retraining_count": self.retraining_count,
            "running": self.running
        }

