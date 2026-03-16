"""
Сервис для выбора модели из сохраненных версий обучения
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional
import shutil
from datetime import datetime
import csv
import yaml

logger = logging.getLogger(__name__)


class ModelSelector:
    """Сервис для выбора и управления моделями из сохраненных версий"""
    
    def __init__(self, config: Dict, project_root: Path):
        """
        Инициализация селектора моделей
        
        Args:
            config: Конфигурация системы
            project_root: Корень проекта
        """
        self.config = config
        self.project_root = project_root
        self.models_base = Path(config.get("data_lake", {}).get("models_path", "data/models"))
        self.model_config = config.get("model", {})
        
    def get_available_models(self) -> List[Dict]:
        """
        Получить список доступных моделей из сохраненных версий обучения
        
        Returns:
            Список словарей с информацией о моделях
        """
        models = []
        
        try:
            # Текущая активная модель
            current_model_path = Path(self.model_config.get("weights_path", "models/cigarette_detector/best.pt"))
            if not current_model_path.is_absolute():
                current_model_path = self.project_root / current_model_path
            
            # Добавляем текущую модель
            if current_model_path.exists():
                models.append({
                    "name": "Текущая (best.pt)",
                    "path": str(current_model_path.relative_to(self.project_root)),
                    "full_path": str(current_model_path),
                    "type": "current",
                    "size": current_model_path.stat().st_size,
                    "modified": datetime.fromtimestamp(current_model_path.stat().st_mtime)
                })
            
            # Поиск моделей в папках обучения
            training_paths = [
                self.project_root / "models" / "cigarette_detector",
                self.models_base / "cigarette_detector",
            ]
            
            for training_base in training_paths:
                if not training_base.exists():
                    continue
                
                # Поиск всех папок с результатами обучения
                for training_dir in training_base.iterdir():
                    if not training_dir.is_dir() or training_dir.name in ["backups", "weights"]:
                        continue
                    
                    weights_dir = training_dir / "weights"
                    if weights_dir.exists():
                        # Ищем best.pt и last.pt
                        for model_file in weights_dir.glob("*.pt"):
                            model_name = f"{training_dir.name} ({model_file.name})"
                            
                            # Проверяем, не дубликат ли это
                            model_path = str(model_file.relative_to(self.project_root))
                            if any(m["path"] == model_path for m in models):
                                continue
                            
                            # Получаем полную информацию о модели включая метрики
                            model_info = self.get_model_info(str(model_file))
                            if model_info:
                                model_info.update({
                                    "type": "training",
                                    "training_dir": training_dir.name,
                                    "weight_type": model_file.stem,  # best или last
                                })
                                models.append(model_info)
                            else:
                                # Если не удалось получить полную информацию, добавляем базовую
                                models.append({
                                    "name": model_name,
                                    "path": model_path,
                                    "full_path": str(model_file),
                                    "type": "training",
                                    "training_dir": training_dir.name,
                                    "weight_type": model_file.stem,
                                    "size": model_file.stat().st_size,
                                    "modified": datetime.fromtimestamp(model_file.stat().st_mtime)
                                })
                
                # Поиск моделей напрямую в папке
                for model_file in training_base.glob("*.pt"):
                    if model_file.name == "best.pt" and current_model_path.samefile(model_file):
                        continue  # Уже добавлена как текущая
                    
                    model_name = model_file.name
                    model_path = str(model_file.relative_to(self.project_root))
                    
                    # Проверяем дубликаты
                    if any(m["path"] == model_path for m in models):
                        continue
                    
                    models.append({
                        "name": model_name,
                        "path": model_path,
                        "full_path": str(model_file),
                        "type": "direct",
                        "size": model_file.stat().st_size,
                        "modified": datetime.fromtimestamp(model_file.stat().st_mtime)
                    })
            
            # Сортируем по дате изменения (новые первыми)
            models.sort(key=lambda x: x["modified"], reverse=True)
            
            logger.info(f"✅ Найдено доступных моделей: {len(models)}")
            return models
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка моделей: {e}", exc_info=True)
            return []
    
    def select_model(self, model_path: str, backup_current: bool = True) -> bool:
        """
        Выбрать модель и скопировать её как best.pt
        
        Args:
            model_path: Путь к выбранной модели (относительно project_root)
            backup_current: Создать резервную копию текущей модели
            
        Returns:
            True если успешно
        """
        try:
            # Путь к выбранной модели
            source_path = Path(model_path) if Path(model_path).is_absolute() else self.project_root / model_path
            
            if not source_path.exists():
                logger.error(f"❌ Модель не найдена: {source_path}")
                return False
            
            # Путь к целевой модели
            target_dir = self.project_root / "models" / "cigarette_detector"
            target_dir.mkdir(parents=True, exist_ok=True)
            target_path = target_dir / "best.pt"
            
            # Создание резервной копии текущей модели
            if backup_current and target_path.exists():
                backup_dir = target_dir / "backups"
                backup_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"best_backup_{timestamp}.pt"
                shutil.copy2(target_path, backup_path)
                logger.info(f"✅ Резервная копия создана: {backup_path}")
            
            # Копирование выбранной модели
            shutil.copy2(source_path, target_path)
            logger.info(f"✅ Модель выбрана и скопирована: {source_path} -> {target_path}")
            
            # Обновление конфига (опционально, если нужно)
            # self.config["model"]["weights_path"] = str(target_path.relative_to(self.project_root))
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка выбора модели: {e}", exc_info=True)
            return False
    
    def _parse_results_csv(self, results_csv_path: Path) -> Optional[Dict]:
        """
        Парсить results.csv для получения метрик
        
        Args:
            results_csv_path: Путь к results.csv
            
        Returns:
            Словарь с метриками или None
        """
        try:
            if not results_csv_path.exists():
                return None
            
            with open(results_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if not rows:
                    return None
                
                # Берем последнюю строку (финальные метрики)
                last_row = rows[-1]
                
                metrics = {}
                
                # Парсим метрики из CSV
                for key in last_row.keys():
                    value = last_row[key].strip()
                    if value and value != '':
                        # Пропускаем колонки, которые не являются метриками
                        if key in ['epoch', 'time']:
                            try:
                                metrics[key] = float(value)
                            except (ValueError, TypeError):
                                pass
                            continue
                        
                        # Сохраняем все метрики
                        try:
                            # Пробуем преобразовать в float
                            metrics[key] = float(value)
                        except (ValueError, TypeError):
                            metrics[key] = value
                
                return metrics
                
        except Exception as e:
            logger.warning(f"⚠️ Не удалось прочитать results.csv: {e}")
            return None
    
    def _get_training_metrics(self, model_path: Path) -> Dict:
        """
        Получить метрики обучения модели
        
        Args:
            model_path: Путь к файлу модели
            
        Returns:
            Словарь с метриками
        """
        metrics = {
            "map50": None,
            "map50_95": None,
            "precision": None,
            "recall": None,
            "epochs": None,
            "training_dir": None
        }
        
        try:
            # Ищем results.csv в папке обучения
            # Модель может быть в структуре: .../train/weights/best.pt
            # или .../train123/weights/best.pt
            
            # Вариант 1: results.csv в родительской папке weights
            weights_dir = model_path.parent
            if weights_dir.name == "weights":
                training_dir = weights_dir.parent
                results_csv = training_dir / "results.csv"
                
                if results_csv.exists():
                    csv_metrics = self._parse_results_csv(results_csv)
                    if csv_metrics:
                        # Извлекаем метрики из CSV
                        # Формат CSV YOLO: metrics/mAP50(B), metrics/precision(B), metrics/recall(B) и т.д.
                        for key, value in csv_metrics.items():
                            if isinstance(value, str):
                                continue  # Пропускаем строковые значения
                            
                            key_lower = key.lower()
                            
                            # mAP@0.5
                            if "map50(b)" in key_lower or key == "metrics/mAP50(B)":
                                metrics["map50"] = float(value)
                            # mAP@0.5:0.95
                            elif "map50-95(b)" in key_lower or key == "metrics/mAP50-95(B)":
                                metrics["map50_95"] = float(value)
                            # Precision
                            elif "precision(b)" in key_lower or key == "metrics/precision(B)":
                                metrics["precision"] = float(value)
                            # Recall
                            elif "recall(b)" in key_lower or key == "metrics/recall(B)":
                                metrics["recall"] = float(value)
                            # Epochs (берем последнюю эпоху из CSV)
                            elif key.lower() == "epoch" and metrics["epochs"] is None:
                                try:
                                    metrics["epochs"] = int(float(value))
                                except:
                                    pass
                        
                        metrics["training_dir"] = training_dir.name
                        
                        # Если нашли хотя бы одну метрику - возвращаем
                        if any(v is not None for v in [metrics["map50"], metrics["precision"], metrics["recall"]]):
                            return metrics
            
            # Вариант 2: ищем args.yaml для получения информации об обучении
            if weights_dir.name == "weights":
                training_dir = weights_dir.parent
                args_yaml = training_dir / "args.yaml"
                
                if args_yaml.exists():
                    try:
                        with open(args_yaml, 'r', encoding='utf-8') as f:
                            args_data = yaml.safe_load(f)
                            if args_data:
                                if "epochs" in args_data:
                                    metrics["epochs"] = args_data["epochs"]
                                if metrics["training_dir"] is None:
                                    metrics["training_dir"] = training_dir.name
                    except Exception as e:
                        logger.debug(f"Не удалось прочитать args.yaml: {e}")
            
            # Вариант 3: проверяем, можем ли загрузить модель и получить метрики напрямую
            # (это медленно, поэтому только если нет CSV)
            if all(v is None for v in [metrics["map50"], metrics["precision"], metrics["recall"]]):
                try:
                    from ultralytics import YOLO
                    
                    # Проверяем, есть ли data.yaml для валидации
                    data_yaml = self.project_root / "models" / "cigarette_detector" / "data.yaml"
                    if not data_yaml.exists():
                        data_yaml = self.project_root / "datasets" / "cigarette_butt" / "data.yaml"
                    
                    if data_yaml.exists():
                        model = YOLO(str(model_path))
                        val_results = model.val(data=str(data_yaml), verbose=False, plots=False)
                        
                        if val_results and hasattr(val_results, 'results_dict'):
                            metrics["map50"] = val_results.results_dict.get('metrics/mAP50(B)', None)
                            metrics["map50_95"] = val_results.results_dict.get('metrics/mAP50-95(B)', None)
                            metrics["precision"] = val_results.results_dict.get('metrics/precision(B)', None)
                            metrics["recall"] = val_results.results_dict.get('metrics/recall(B)', None)
                            
                except Exception as e:
                    logger.debug(f"Не удалось получить метрики через валидацию: {e}")
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка получения метрик обучения: {e}")
        
        return metrics
    
    def get_model_info(self, model_path: str) -> Optional[Dict]:
        """
        Получить информацию о модели включая метрики
        
        Args:
            model_path: Путь к модели
            
        Returns:
            Словарь с информацией или None
        """
        try:
            model_file = Path(model_path) if Path(model_path).is_absolute() else self.project_root / model_path
            
            if not model_file.exists():
                return None
            
            # Базовая информация
            info = {
                "name": model_file.name,
                "path": str(model_file.relative_to(self.project_root)),
                "full_path": str(model_file),
                "size": model_file.stat().st_size,
                "size_mb": model_file.stat().st_size / (1024 * 1024),
                "modified": datetime.fromtimestamp(model_file.stat().st_mtime),
                "exists": True
            }
            
            # Получаем метрики обучения
            metrics = self._get_training_metrics(model_file)
            info.update(metrics)
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о модели: {e}", exc_info=True)
            return None

