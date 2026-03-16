"""
Сервис обучения и дообучения моделей YOLO
Реализует активное обучение (Active Learning)
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import uuid
import yaml
import shutil

from ultralytics import YOLO

logger = logging.getLogger(__name__)


class TrainerService:
    """Сервис обучения моделей"""
    
    def __init__(self, config: Dict, db, mqtt_client):
        """
        Инициализация сервиса обучения
        
        Args:
            config: Конфигурация системы
            db: База данных
            mqtt_client: MQTT клиент для уведомлений
        """
        self.config = config
        self.db = db
        self.mqtt_client = mqtt_client
        self.active_training = None
        self.model_config = config.get("model", {})
        self.al_config = config.get("active_learning", {})
        
        # Пути
        self.models_path = Path(config["data_lake"]["models_path"])
        self.models_path.mkdir(parents=True, exist_ok=True)
        
        self.data_path = Path(config["dataset"]["base_path"])
        self.model_weights_path = Path(self.model_config.get("weights_path", "models/cigarette_detector/best.pt"))
        self.data_config_path = Path(config["dataset"]["base_path"]) / "data.yaml"
    
    async def start_training(self, epochs: int = 100, batch_size: int = 16,
                           learning_rate: Optional[float] = None,
                           resume: bool = False) -> str:
        """
        Запуск обучения модели
        
        Args:
            epochs: Количество эпох
            batch_size: Размер батча
            learning_rate: Скорость обучения (None = default)
            resume: Продолжить с последней модели
            
        Returns:
            ID тренировки
        """
        if self.active_training:
            raise RuntimeError("Training already in progress")
        
        training_id = f"training_{uuid.uuid4().hex[:8]}"
        self.active_training = training_id
        
        # Запустить обучение в отдельной задаче
        asyncio.create_task(self._train_model(training_id, epochs, batch_size, learning_rate, resume))
        
        return training_id
    
    async def _train_model(self, training_id: str, epochs: int, batch_size: int,
                          learning_rate: Optional[float], resume: bool):
        """Асинхронное обучение модели"""
        try:
            logger.info(f"Начало обучения модели {training_id}")
            
            # Загрузить модель
            if resume and self.model_weights_path.exists():
                model = YOLO(str(self.model_weights_path))
                logger.info(f"Продолжение обучения с {self.model_weights_path}")
            else:
                model = YOLO(f"{self.model_config.get('name', 'yolov8n')}.pt")
                logger.info(f"Загрузка предобученной модели {self.model_config.get('name', 'yolov8n')}")
            
            # Параметры обучения
            train_args = {
                "data": str(self.data_config_path),
                "epochs": epochs,
                "batch": batch_size,
                "imgsz": self.model_config.get("input_size", 640),
                "project": str(self.models_path),
                "name": training_id,
                "save": True,
                "exist_ok": True
            }
            
            if learning_rate:
                train_args["lr0"] = learning_rate
            
            # Обучение
            results = model.train(**train_args)
            
            # Сохранить лучшую модель
            best_weights = self.models_path / training_id / "weights" / "best.pt"
            
            if best_weights.exists():
                # Скопировать в основную директорию моделей
                new_model_path = self.models_path / f"model_{training_id}.pt"
                shutil.copy(best_weights, new_model_path)
                
                # Сохранить метрики в БД
                model_id = f"model_{uuid.uuid4().hex[:8]}"
                await self.db.save_model({
                    "model_id": model_id,
                    "name": "cigarette_detector",
                    "version": training_id,
                    "path": str(new_model_path),
                    "map": results.results_dict.get("metrics/mAP50(B)", 0),
                    "precision": results.results_dict.get("metrics/precision(B)", 0),
                    "recall": results.results_dict.get("metrics/recall(B)", 0),
                    "is_active": False,
                    "created_at": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Обучение завершено: mAP={results.results_dict.get('metrics/mAP50(B)', 0):.4f}")
                
                # Уведомить через MQTT
                await self.mqtt_client.publish("obelisk/model/training_completed", {
                    "training_id": training_id,
                    "model_id": model_id,
                    "metrics": {
                        "map": results.results_dict.get("metrics/mAP50(B)", 0),
                        "precision": results.results_dict.get("metrics/precision(B)", 0),
                        "recall": results.results_dict.get("metrics/recall(B)", 0)
                    }
                })
            else:
                logger.error("Не найдены веса модели после обучения")
                
        except Exception as e:
            logger.error(f"Ошибка обучения: {e}", exc_info=True)
            await self.mqtt_client.publish("obelisk/model/training_failed", {
                "training_id": training_id,
                "error": str(e)
            })
        finally:
            self.active_training = None
    
    async def deploy_model(self, model_id: str) -> bool:
        """
        Деплой модели на edge устройства
        
        Args:
            model_id: ID модели
            
        Returns:
            Успех деплоя
        """
        try:
            # Получить модель из БД
            model = await self.db.get_model(model_id)
            if not model:
                return False
            
            # Обновить активную модель
            # Деактивировать старую активную модель
            active_model = await self.db.get_active_model()
            if active_model:
                await self.db.deactivate_model(active_model["model_id"])
            
            # Активировать новую модель
            await self.db.activate_model(model_id)
            
            # Опубликовать обновление модели через MQTT
            await self.mqtt_client.publish("obelisk/model/update", {
                "model_id": model_id,
                "model_path": model["path"],
                "version": model["version"],
                "metrics": {
                    "map": model.get("mAP"),
                    "precision": model.get("precision"),
                    "recall": model.get("recall")
                }
            })
            
            logger.info(f"Модель {model_id} деплоена на edge устройства")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка деплоя модели: {e}")
            return False
    
    async def active_learning_loop(self):
        """Основной цикл активного обучения"""
        if not self.al_config.get("enabled", False):
            return
        
        while True:
            try:
                # Собрать кадры с низкой уверенностью
                await self._collect_uncertain_samples()
                
                # Проверить, достаточно ли данных для переобучения
                samples_count = await self._count_unlabeled_samples()
                
                if samples_count >= self.al_config.get("min_samples_for_retrain", 100):
                    logger.info(f"Найдено {samples_count} образцов для активного обучения")
                    
                    # TODO: Запустить процесс разметки (ручной или автоматический)
                    # После разметки запустить дообучение
                    await self.start_training(
                        epochs=self.al_config.get("retrain_epochs", 20),
                        batch_size=self.al_config.get("retrain_batch_size", 16)
                    )
                
                # Интервал проверки
                await asyncio.sleep(self.al_config.get("collection_interval", 3600))
                
            except Exception as e:
                logger.error(f"Ошибка в active learning loop: {e}")
                await asyncio.sleep(60)
    
    async def _collect_uncertain_samples(self):
        """Собрать образцы с низкой уверенностью для разметки"""
        # Получить детекции с низкой уверенностью из БД
        confidence_lower = self.al_config.get("confidence_lower", 0.3)
        confidence_upper = self.al_config.get("confidence_upper", 0.7)
        
        # TODO: Реализовать выборку кадров для активного обучения
        # Сохранить в data/raw/active_learning/
        
        pass
    
    async def _count_unlabeled_samples(self) -> int:
        """Подсчитать количество неразмеченных образцов"""
        # TODO: Реализовать подсчет
        return 0


