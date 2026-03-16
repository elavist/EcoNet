"""
Движок для объединения моделей
Создает единую систему для работы с несколькими моделями детекции
"""

import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import numpy as np
import cv2
import yaml

logger = logging.getLogger(__name__)


class ModelEngine:
    """
    Движок для объединения и управления моделями детекции
    
    Функции:
    1. Загрузка нескольких моделей
    2. Объединение результатов детекции
    3. Взвешенное голосование
    4. Создание единой модели из ансамбля
    5. Оптимизация производительности
    """
    
    def __init__(self, config: Dict):
        """
        Инициализация движка моделей
        
        Args:
            config: Конфигурация системы
        """
        self.config = config
        self.models = {}  # Словарь загруженных моделей
        self.model_weights = {}  # Веса моделей для ансамбля
        self.model_stats = {}  # Статистика по моделям
        self.model_is_onnx = {}  # Флаг ONNX модели для каждой модели
        self.ensemble_enabled = False
        
        # Параметры ансамбля
        self.ensemble_config = config.get("model_engine", {}).get("ensemble", {})
        self.voting_method = self.ensemble_config.get("voting_method", "weighted")  # weighted, majority, average
        self.min_models_agree = self.ensemble_config.get("min_models_agree", 2)
        self.iou_threshold = self.ensemble_config.get("iou_threshold", 0.5)  # Порог IoU для группировки детекций
        
        # ONNX отключен - только PT модели для максимальной точности и производительности
        self.use_onnx = config.get("model_engine", {}).get("use_onnx", False)
        if self.use_onnx:
            logger.warning("⚠️ ONNX включен в конфиге, но рекомендуется использовать только PT модели для максимальной точности")
        
        # Оптимизация производительности — ПОЛНАЯ МОЩНОСТЬ GPU
        self.device = self._get_optimal_device()
        self.half_precision = config.get("model_engine", {}).get("half_precision", True)
        
        # CUDA оптимизации при старте
        if self.device != "cpu":
            try:
                import torch
                if torch.cuda.is_available():
                    # cuDNN benchmark: автоподбор быстрейшего алгоритма конволюций
                    torch.backends.cudnn.benchmark = True
                    torch.backends.cudnn.enabled = True
                    # Expandable memory segments для уменьшения фрагментации
                    if hasattr(torch.cuda, 'memory') and hasattr(torch.cuda.memory, 'set_per_process_memory_fraction'):
                        pass  # уже устанавливается в gpu_manager
                    logger.info("🚀 CUDA оптимизации: cuDNN benchmark=ON, FP16=%s", self.half_precision)
            except Exception as e:
                logger.warning(f"Не удалось применить CUDA оптимизации: {e}")
        
        # Инициализация GPU Manager для МАКСИМАЛЬНОГО использования GPU (99%)
        self.gpu_manager = None
        if self.device != "cpu":
            try:
                from obelisk.core.managers.gpu_manager import get_gpu_manager
                device_id = int(self.device.split(':')[-1]) if ':' in self.device else 0
                # МАКСИМАЛЬНАЯ МОЩНОСТЬ - 99% использования GPU
                self.gpu_manager = get_gpu_manager(device_id=device_id, max_usage_percent=0.99)
                # Используем оптимальный batch size из GPU Manager (максимальный)
                self.max_batch_size = self.gpu_manager.get_optimal_batch_size()
                logger.info(f"🚀 GPU Manager инициализирован - МАКСИМАЛЬНАЯ МОЩНОСТЬ")
                logger.info(f"   Оптимальный batch size: {self.max_batch_size} (максимум)")
                logger.info(f"   ВСЯ МОЩНОСТЬ GPU ДЛЯ ЭКОНЕТ")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать GPU Manager: {e}")
                self.max_batch_size = config.get("model_engine", {}).get("max_batch_size", 16)  # Увеличенный дефолт
        else:
            self.max_batch_size = config.get("model_engine", {}).get("max_batch_size", 4)
        
        # Загрузка моделей
        self._load_models()
    
    def _get_optimal_device(self):
        """Определение оптимального устройства (GPU/CPU)"""
        device_config = self.config.get("edge", {}).get("device") or self.config.get("model_engine", {}).get("device")
        
        # Принудительное использование GPU если указано в конфиге
        if device_config and device_config != "cpu":
            try:
                import torch
                
                # Проверка CUDA GPU
                if torch.cuda.is_available() and ("cuda" in str(device_config).lower() or "gpu" in str(device_config).lower()):
                    device_id = device_config.split(':')[-1] if ':' in str(device_config) else "0"
                    device = f"cuda:{device_id}"
                    
                    # Синхронизация GPU
                    torch.cuda.synchronize()
                    
                    gpu_name = torch.cuda.get_device_name(int(device_id))
                    gpu_memory = torch.cuda.get_device_properties(int(device_id)).total_memory / (1024**3)  # GB
                    logger.info(f"✅ GPU доступен: {gpu_name} ({gpu_memory:.1f} GB)")
                    logger.info(f"🚀 Используется GPU: {device} для максимальной производительности")
                    return device
                
                # Проверка Apple MPS (Metal)
                elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() and "mps" in str(device_config).lower():
                    logger.info("✅ Apple MPS (Metal) доступен")
                    return "mps"
                    
            except Exception as e:
                logger.warning(f"Не удалось определить GPU: {e}")
                if device_config and device_config != "cpu":
                    logger.warning(f"⚠️ GPU запрошен в конфиге, но недоступен. Переключение на CPU.")
        
        logger.info("ℹ️ Используется CPU")
        return "cpu"
    
    def _load_models(self):
        """Загрузка всех моделей из конфигурации"""
        try:
            from ultralytics import YOLO
            
            model_configs = self.config.get("model_engine", {}).get("models", [])
            
            if not model_configs:
                # Используем основную модель по умолчанию
                model_configs = [{
                    "name": "primary",
                    "path": self.config.get("model", {}).get("weights_path", "models/cigarette_detector/best.pt"),
                    "weight": 1.0,
                    "enabled": True
                }]
            
            for model_cfg in model_configs:
                if not model_cfg.get("enabled", True):
                    continue
                
                model_name = model_cfg.get("name", "model")
                model_path = model_cfg.get("path")
                weight = model_cfg.get("weight", 1.0)
                
                if not model_path:
                    logger.warning(f"Путь модели не указан для {model_name}")
                    continue
                
                # Проверка существования модели
                # Правильная обработка пути (решает проблему с кавычками в имени папки)
                if Path(model_path).is_absolute():
                    model_path_obj = Path(model_path)
                else:
                    # Получаем корень проекта правильно (решает проблему с двойными кавычками)
                    # __file__ = obelisk/core/engines/model_engine.py
                    # parent = obelisk/core/engines
                    # parent.parent = obelisk/core
                    # parent.parent.parent = obelisk
                    # parent.parent.parent.parent = Project_econet (корень проекта)
                    project_root = Path(__file__).parent.parent.parent.parent.resolve()
                    model_path_obj = (project_root / model_path).resolve()
                
                logger.debug(f"🔍 Проверка модели: {model_path_obj}")
                logger.debug(f"   Существует: {model_path_obj.exists()}")
                logger.debug(f"   Расширение: {model_path_obj.suffix}")
                
                # Загрузка модели - ТОЛЬКО PT МОДЕЛИ (ONNX отключен - теряет точность и не дообрабатывает кадры)
                # PT модель на GPU с CUDA - максимальная точность и производительность
                is_onnx = False  # ONNX полностью отключен
                
                # ПРИОРИТЕТ ТОЛЬКО PT МОДЕЛИ
                # ONNX отключен по причинам:
                # 1. Теряет точность при конвертации
                # 2. Не дообрабатывает кадры полностью (ваша проблема!)
                # 3. Медленнее на GPU чем PT с CUDA
                # 4. Фиксированный размер входа (ограничивает гибкость)
                if model_path_obj.exists() and model_path_obj.suffix == '.pt':
                    try:
                        # Загрузка PT модели с указанием устройства для GPU
                        # Используем Path объект напрямую для правильной обработки кавычек в имени папки
                        # YOLO может работать с Path объектом напрямую
                        try:
                            # Попытка передать Path объект напрямую (YOLO должен поддерживать)
                            model = YOLO(model_path_obj)
                        except (TypeError, AttributeError):
                            # Fallback: используем абсолютный путь с правильным экранированием
                            import os
                            model_path_str = os.path.normpath(str(model_path_obj.resolve()))
                            logger.debug(f"🔍 Загрузка модели (fallback): {model_path_str}")
                            model = YOLO(model_path_str)
                        
                        if self.device != "cpu":
                            model.to(self.device)  # Явное указание устройства для PT модели
                        is_onnx = False
                        logger.info(f"✅ Модель {model_name} загружена (PT): {model_path_obj}")
                        logger.info(f"   🚀 PT модель на GPU - максимальная точность и производительность")
                    except Exception as e:
                        logger.error(f"❌ Не удалось загрузить PT модель {model_name}: {e}")
                        logger.error(f"   Путь модели: {model_path_obj}")
                        logger.error(f"   Абсолютный путь: {model_path_obj.absolute()}")
                        logger.error(f"   Модель существует: {model_path_obj.exists()}")
                        logger.error(f"   ONNX отключен - используйте PT модель для максимальной точности")
                        import traceback
                        logger.error(traceback.format_exc())
                        continue
                else:
                    logger.error(f"❌ PT модель {model_name} не найдена: {model_path_obj}")
                    logger.error(f"   ONNX отключен - используйте PT модель (.pt)")
                    continue
                
                # Оптимизация модели — ПОЛНАЯ МОЩНОСТЬ GPU
                try:
                    if self.device != "cpu":
                        import torch
                        if torch.cuda.is_available() and "cuda" in self.device:
                            model.to(self.device)
                            # Ultralytics YOLO: НЕ конвертируем модель вручную через .half()
                            # FP16 включается через half=True в inference kwargs —
                            # Ultralytics сам конвертирует input и модель правильно
                            precision = "FP16" if self.half_precision else "FP32"
                            logger.info(f"✅ Модель {model_name}: {precision} на {self.device}")
                            
                            # Прогрев GPU — первый inference медленный, делаем при загрузке
                            try:
                                import numpy as np
                                warmup_frame = np.zeros((640, 640, 3), dtype=np.uint8)
                                model(warmup_frame, imgsz=640, half=self.half_precision, 
                                      verbose=False, device=self.device)
                                torch.cuda.synchronize()
                                logger.info(f"🔥 GPU прогрет для {model_name}")
                            except Exception as e:
                                logger.debug(f"Прогрев GPU пропущен: {e}")
                            
                            torch.cuda.synchronize()
                except Exception as e:
                    logger.warning(f"Не удалось оптимизировать модель {model_name}: {e}")
                
                # Сохранение модели и информации о типе (ONNX или PT)
                self.models[model_name] = model
                self.model_weights[model_name] = weight
                # Сохраняем информацию о том, является ли модель ONNX
                self.model_is_onnx[model_name] = is_onnx
                self.model_stats[model_name] = {
                    "detections_count": 0,
                    "frames_processed": 0,
                    "avg_confidence": 0.0,
                    "last_update": datetime.now()
                }
                logger.info(f"✅ Модель {model_name} добавлена в словарь моделей")
            
            # Проверка успешности загрузки моделей
            if not self.models:
                error_msg = "Не удалось загрузить ни одной модели!"
                logger.error(f"❌ {error_msg}")
                logger.error(f"   Проверьте конфигурацию моделей в config.yaml")
                logger.error(f"   Убедитесь, что файлы моделей существуют")
                logger.error(f"   Модель должна быть в формате .pt (PT модель)")
                logger.error(f"   ONNX модели отключены для максимальной точности")
                raise Exception(error_msg)
            
            logger.info(f"✅ Всего загружено моделей: {len(self.models)}")
            logger.info(f"   Модели: {list(self.models.keys())}")
            
            # Включение ансамбля если несколько моделей
            if len(self.models) > 1:
                self.ensemble_enabled = True
                logger.info(f"✅ Ансамбль моделей активирован: {len(self.models)} моделей")
            else:
                model_name = list(self.models.keys())[0]
                logger.info(f"✅ Загружена одна модель: {model_name}")
                
        except Exception as e:
            logger.error(f"Ошибка загрузки моделей: {e}", exc_info=True)
            logger.error(f"   Количество загруженных моделей: {len(self.models)}")
            if len(self.models) == 0:
                logger.error("   ❌ Модели не загружены! Проверьте путь к модели в config.yaml")
    
    async def detect_frame(self, frame: cv2.Mat, frame_id: Optional[str] = None) -> List[Dict]:
        """
        Детекция на кадре с использованием всех моделей
        
        Args:
            frame: Кадр изображения
            frame_id: ID кадра
            
        Returns:
            Объединенный список детекций
        """
        if not self.models:
            logger.error("❌ Нет загруженных моделей в ModelEngine!")
            return []
        
        if self.ensemble_enabled and len(self.models) > 1:
            return await self._ensemble_detect(frame, frame_id)
        else:
            model_name = list(self.models.keys())[0]
            return await self._single_model_detect(model_name, frame, frame_id)
    
    async def _single_model_detect(self, model_name: str, frame: cv2.Mat, 
                                   frame_id: Optional[str] = None) -> List[Dict]:
        """Детекция одной моделью с оптимизацией"""
        try:
            # Проверка GPU памяти (не чаще 1 раза в секунду)
            if self.gpu_manager:
                self.gpu_manager.check_and_cleanup()
            
            model = self.models[model_name]
            model_config = self.config.get("model", {})
            
            # Оптимизированные параметры для максимального количества детекций
            # Используем оптимальный размер из GPU Manager если доступен
            if self.gpu_manager and self.device != "cpu":
                config_input_size = self.gpu_manager.get_optimal_input_size()
            else:
                config_input_size = model_config.get("input_size", 640)
            
            # PT модели поддерживают любые размеры (ONNX отключен)
            # Используем оптимальный размер из GPU Manager для PT модели
            input_size = config_input_size
            logger.debug(f"🚀 PT модель '{model_name}' - используется размер: {input_size} для максимального количества детекций")
            
            # Инференс с оптимизацией (баланс качества и скорости)
            # YOLO автоматически использует device из модели, но можно явно указать
            inference_kwargs = {
                "imgsz": input_size,
                "conf": model_config.get("confidence_threshold", 0.2),  # Низкий порог для максимального количества детекций
                "iou": model_config.get("iou_threshold", 0.4),  # Мягкая фильтрация
                "verbose": False,
                "stream": False,  # Не используем stream
                "max_det": model_config.get("max_detections", 300),  # Максимум детекций
                "agnostic_nms": False,  # Сохраняем качество детекции
                "retina_masks": False,  # Отключаем для скорости (если не нужны маски)
            }
            
            if self.device != "cpu":
                inference_kwargs["device"] = self.device
                inference_kwargs["half"] = self.half_precision
            
            # ОПТИМИЗАЦИЯ: Убрано избыточное логирование
            logger.debug(f"🚀 YOLO: conf={inference_kwargs.get('conf')}, imgsz={inference_kwargs.get('imgsz')}, device={inference_kwargs.get('device', 'cpu')}")
            
            # Выполнение инференса
            results = model(frame, **inference_kwargs)
            
            # GPU синхронизация убрана из hot path — она убивает throughput
            # torch.cuda.synchronize() вызывается только при необходимости (прогрев, замеры)
            
            detections = []
            for result in results:
                boxes = result.boxes
                logger.debug(f"📦 Найдено {len(boxes)} боксов")
                for box in boxes:
                    # Для GPU данные могут быть на GPU, перемещаем на CPU для обработки
                    if self.device != "cpu":
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = float(box.conf[0].cpu().numpy())
                        cls = int(box.cls[0].cpu().numpy())
                    else:
                        x1, y1, x2, y2 = box.xyxy[0].numpy()
                        conf = float(box.conf[0].numpy())
                        cls = int(box.cls[0].numpy())
                    
                    detections.append({
                        'bbox': [float(x1), float(y1), float(x2-x1), float(y2-y1)],
                        'confidence': conf,
                        'class': cls,
                        'model': model_name,
                        'frame_id': frame_id
                    })
            
            # ОПТИМИЗАЦИЯ: Логирование только при наличии детекций
            if detections:
                logger.debug(f"✅ Детекций: {len(detections)}")
            
            # Обновление статистики
            self.model_stats[model_name]["frames_processed"] += 1
            self.model_stats[model_name]["detections_count"] += len(detections)
            if detections:
                avg_conf = sum(d['confidence'] for d in detections) / len(detections)
                self.model_stats[model_name]["avg_confidence"] = avg_conf
            
            return detections
            
        except Exception as e:
            logger.error(f"Ошибка детекции моделью {model_name}: {e}")
            return []
    
    async def _ensemble_detect(self, frame: cv2.Mat, 
                              frame_id: Optional[str] = None) -> List[Dict]:
        """Детекция ансамблем моделей"""
        try:
            # Параллельная детекция всеми моделями
            tasks = []
            for model_name in self.models.keys():
                tasks.append(self._single_model_detect(model_name, frame, frame_id))
            
            results_list = await asyncio.gather(*tasks)
            
            # Объединение результатов с использованием IoU группировки
            if self.voting_method == "weighted":
                return self._weighted_voting(results_list, self.iou_threshold)
            elif self.voting_method == "majority":
                return self._majority_voting(results_list, self.iou_threshold)
            elif self.voting_method == "average":
                return self._average_voting(results_list, self.iou_threshold)
            else:
                return self._weighted_voting(results_list, self.iou_threshold)
                
        except Exception as e:
            logger.error(f"Ошибка ансамблевой детекции: {e}")
            return []
    
    def _calculate_iou(self, bbox1: List[float], bbox2: List[float]) -> float:
        """
        Вычисление Intersection over Union (IoU) для двух bbox
        
        Args:
            bbox1, bbox2: Bbox в формате [x, y, w, h]
            
        Returns:
            IoU значение от 0 до 1
        """
        # Конвертация в формат [x1, y1, x2, y2]
        x1_1, y1_1, w1, h1 = bbox1
        x2_1, y2_1 = x1_1 + w1, y1_1 + h1
        
        x1_2, y1_2, w2, h2 = bbox2
        x2_2, y2_2 = x1_2 + w2, y1_2 + h2
        
        # Вычисление пересечения
        x1_inter = max(x1_1, x1_2)
        y1_inter = max(y1_1, y1_2)
        x2_inter = min(x2_1, x2_2)
        y2_inter = min(y2_1, y2_2)
        
        if x2_inter <= x1_inter or y2_inter <= y1_inter:
            return 0.0
        
        intersection = (x2_inter - x1_inter) * (y2_inter - y1_inter)
        
        # Вычисление объединения
        area1 = w1 * h1
        area2 = w2 * h2
        union = area1 + area2 - intersection
        
        if union == 0:
            return 0.0
        
        return intersection / union
    
    def _weighted_voting(self, results_list: List[List[Dict]], iou_threshold: float = 0.5) -> List[Dict]:
        """
        Улучшенное взвешенное голосование с IoU группировкой
        
        Args:
            results_list: Список списков детекций от каждой модели
            iou_threshold: Порог IoU для группировки детекций (по умолчанию 0.5)
            
        Returns:
            Объединенный список детекций
        """
        # Сбор всех детекций с весами и статистикой моделей
        all_detections = []
        for model_idx, detections in enumerate(results_list):
            model_name = list(self.models.keys())[model_idx]
            base_weight = self.model_weights.get(model_name, 1.0)
            
            # Динамический вес на основе статистики модели
            model_stat = self.model_stats.get(model_name, {})
            avg_conf = model_stat.get("avg_confidence", 0.5)
            
            # Адаптивный вес: базовая_вес * (1 + avg_confidence) * reliability_factor
            # reliability_factor учитывает историю модели
            reliability_factor = 1.0
            if model_stat.get("frames_processed", 0) > 10:
                # Если модель обработала много кадров, увеличиваем вес на основе средней уверенности
                reliability_factor = 0.8 + (avg_conf * 0.4)  # От 0.8 до 1.2
            
            effective_weight = base_weight * reliability_factor
            
            for det in detections:
                all_detections.append({
                    'detection': det,
                    'model': model_name,
                    'weight': effective_weight,
                    'confidence': det.get('confidence', 0.0)
                })
        
        # Группировка детекций по IoU (кластеры перекрывающихся детекций)
        clusters = []
        used_indices = set()
        
        for i, det_item in enumerate(all_detections):
            if i in used_indices:
                continue
            
            cluster = [det_item]
            used_indices.add(i)
            
            # Поиск всех перекрывающихся детекций
            for j, other_item in enumerate(all_detections):
                if j <= i or j in used_indices:
                    continue
                
                bbox1 = det_item['detection']['bbox']
                bbox2 = other_item['detection']['bbox']
                iou = self._calculate_iou(bbox1, bbox2)
                
                if iou >= iou_threshold:
                    cluster.append(other_item)
                    used_indices.add(j)
            
            clusters.append(cluster)
        
        # Объединение детекций в кластерах
        merged_detections = []
        for cluster in clusters:
            if len(cluster) < self.min_models_agree:
                continue
            
            # Вычисление взвешенного центра и размера bbox
            total_weight = sum(item['weight'] for item in cluster)
            
            # Взвешенное усреднение координат с учетом уверенности
            # Используем confidence как дополнительный вес
            weighted_bbox = [0.0, 0.0, 0.0, 0.0]
            weighted_conf_sum = 0.0
            total_conf_weight = 0.0
            
            for item in cluster:
                conf = item['confidence']
                weight = item['weight']
                # Комбинированный вес: вес модели * уверенность детекции
                conf_weight = weight * conf
                
                bbox = item['detection']['bbox']
                for i in range(4):
                    weighted_bbox[i] += bbox[i] * conf_weight
                
                weighted_conf_sum += conf * conf_weight
                total_conf_weight += conf_weight
            
            # Нормализация
            if total_conf_weight > 0:
                weighted_bbox = [coord / total_conf_weight for coord in weighted_bbox]
                weighted_conf = weighted_conf_sum / total_conf_weight
            else:
                weighted_conf = sum(item['confidence'] for item in cluster) / len(cluster)
            
            # Определение класса (голосование большинством)
            class_votes = {}
            for item in cluster:
                cls = item['detection'].get('class', 0)
                weight = item['weight']
                if cls not in class_votes:
                    class_votes[cls] = 0.0
                class_votes[cls] += weight
            
            best_class = max(class_votes, key=class_votes.get) if class_votes else cluster[0]['detection'].get('class', 0)
            
            merged_detections.append({
                'bbox': weighted_bbox,
                'confidence': min(weighted_conf, 1.0),  # Ограничение сверху
                'class': best_class,
                'models': list(set(item['model'] for item in cluster)),
                'frame_id': cluster[0]['detection'].get('frame_id'),
                'agreement_count': len(cluster)  # Количество согласных моделей
            })
        
        return merged_detections
    
    def _majority_voting(self, results_list: List[List[Dict]], iou_threshold: float = 0.5) -> List[Dict]:
        """
        Улучшенное голосование большинством с IoU группировкой
        
        Args:
            results_list: Список списков детекций от каждой модели
            iou_threshold: Порог IoU для группировки детекций
            
        Returns:
            Объединенный список детекций
        """
        # Сбор всех детекций
        all_detections = []
        for detections in results_list:
            all_detections.extend(detections)
        
        # Группировка по IoU
        clusters = []
        used_indices = set()
        
        for i, det in enumerate(all_detections):
            if i in used_indices:
                continue
            
            cluster = [det]
            used_indices.add(i)
            
            # Поиск перекрывающихся детекций
            for j, other_det in enumerate(all_detections):
                if j <= i or j in used_indices:
                    continue
                
                iou = self._calculate_iou(det['bbox'], other_det['bbox'])
                if iou >= iou_threshold:
                    cluster.append(other_det)
                    used_indices.add(j)
            
            clusters.append(cluster)
        
        # Выбор детекций с достаточным количеством голосов
        merged_detections = []
        for cluster in clusters:
            if len(cluster) >= self.min_models_agree:
                # Используем детекцию с максимальной уверенностью
                best_det = max(cluster, key=lambda d: d['confidence'])
                merged_detections.append(best_det)
        
        return merged_detections
    
    def _average_voting(self, results_list: List[List[Dict]], iou_threshold: float = 0.5) -> List[Dict]:
        """
        Улучшенное усреднение результатов с IoU группировкой
        
        Args:
            results_list: Список списков детекций от каждой модели
            iou_threshold: Порог IoU для группировки детекций
            
        Returns:
            Объединенный список детекций
        """
        # Сбор всех детекций
        all_detections = []
        for detections in results_list:
            all_detections.extend(detections)
        
        # Группировка по IoU
        clusters = []
        used_indices = set()
        
        for i, det in enumerate(all_detections):
            if i in used_indices:
                continue
            
            cluster = [det]
            used_indices.add(i)
            
            # Поиск перекрывающихся детекций
            for j, other_det in enumerate(all_detections):
                if j <= i or j in used_indices:
                    continue
                
                iou = self._calculate_iou(det['bbox'], other_det['bbox'])
                if iou >= iou_threshold:
                    cluster.append(other_det)
                    used_indices.add(j)
            
            clusters.append(cluster)
        
        # Усреднение
        merged_detections = []
        for cluster in clusters:
            if len(cluster) >= self.min_models_agree:
                # Геометрическое усреднение bbox
                avg_bbox = [
                    sum(d['bbox'][i] for d in cluster) / len(cluster)
                    for i in range(4)
                ]
                # Арифметическое усреднение уверенности
                avg_conf = sum(d['confidence'] for d in cluster) / len(cluster)
                
                # Определение класса (голосование большинством)
                class_votes = {}
                for d in cluster:
                    cls = d.get('class', 0)
                    class_votes[cls] = class_votes.get(cls, 0) + 1
                best_class = max(class_votes, key=class_votes.get) if class_votes else cluster[0].get('class', 0)
                
                merged_detections.append({
                    'bbox': avg_bbox,
                    'confidence': avg_conf,
                    'class': best_class,
                    'models': list(set(d.get('model', 'unknown') for d in cluster)),
                    'frame_id': cluster[0].get('frame_id'),
                    'agreement_count': len(cluster)
                })
        
        return merged_detections
    
    def get_statistics(self) -> Dict:
        """Получить статистику по всем моделям"""
        return {
            "models_count": len(self.models),
            "ensemble_enabled": self.ensemble_enabled,
            "voting_method": self.voting_method,
            "models": {
                name: {
                    **stats,
                    "weight": self.model_weights.get(name, 1.0)
                }
                for name, stats in self.model_stats.items()
            }
        }
    
    def add_model(self, name: str, model_path: str, weight: float = 1.0):
        """Добавить новую модель в движок"""
        try:
            from ultralytics import YOLO
            
            model_path_obj = Path(model_path) if Path(model_path).is_absolute() else Path(__file__).parent.parent.parent / model_path
            
            if not model_path_obj.exists():
                logger.error(f"Модель не найдена: {model_path_obj}")
                return False
            
            model = YOLO(str(model_path_obj))
            self.models[name] = model
            self.model_weights[name] = weight
            self.model_stats[name] = {
                "detections_count": 0,
                "frames_processed": 0,
                "avg_confidence": 0.0,
                "last_update": datetime.now()
            }
            
            if len(self.models) > 1:
                self.ensemble_enabled = True
            
            logger.info(f"✅ Модель {name} добавлена в движок")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления модели {name}: {e}")
            return False
    
    def remove_model(self, name: str):
        """Удалить модель из движка"""
        if name in self.models:
            del self.models[name]
            del self.model_weights[name]
            del self.model_stats[name]
            
            if len(self.models) <= 1:
                self.ensemble_enabled = False
            
            logger.info(f"✅ Модель {name} удалена из движка")
            return True
        return False
    
    def set_model_weight(self, name: str, weight: float):
        """Установить вес модели"""
        if name in self.model_weights:
            self.model_weights[name] = weight
            logger.info(f"✅ Вес модели {name} установлен: {weight}")
            return True
        return False

