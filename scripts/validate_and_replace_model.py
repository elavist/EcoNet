"""
Валидация новой модели, сравнение со старой и замена
Удаление старых моделей и очистка кэша
"""

import sys
import io
from pathlib import Path
import yaml
import shutil
from datetime import datetime

# Настройка кодировки
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def print_header(text):
    """Печать заголовка"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_section(text):
    """Печать секции"""
    print(f"\n{'-' * 70}")
    print(f"  {text}")
    print(f"{'-' * 70}")

def validate_model(model_path, data_yaml):
    """Валидация модели"""
    from ultralytics import YOLO
    import torch
    import tempfile
    import shutil
    
    print(f"  Загрузка модели: {model_path}")
    
    if not model_path.exists():
        print(f"  [FAIL] Модель не найдена: {model_path}")
        return None
    
    # Обходим проблему с кавычками в имени папки через временную копию
    temp_model_path = None
    try:
        # Создаем временную копию модели без проблемных символов в пути
        temp_dir = Path(tempfile.gettempdir())
        temp_model_path = temp_dir / f"temp_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pt"
        
        print(f"  [INFO] Создание временной копии модели...")
        shutil.copy2(model_path, temp_model_path)
        
        # Загружаем модель из временного пути (без кавычек)
        model = YOLO(str(temp_model_path))
    except Exception as e:
        print(f"  [WARN] Не удалось использовать временную копию: {e}")
        # Fallback: попытка прямой загрузки
        try:
            model = YOLO(model_path)
        except Exception as e2:
            print(f"  [FAIL] Не удалось загрузить модель: {e2}")
            return None
    finally:
        # Очистка временного файла после загрузки
        # (не удаляем сразу, так как YOLO может кэшировать путь)
        # Удалим в конце функции
        pass
    
    # Сохраняем путь для очистки
    temp_file_to_clean = temp_model_path
    
    # Переместить на GPU если доступен
    if torch.cuda.is_available():
        model.to("cuda:0")
        print(f"  [INFO] Модель загружена на GPU")
    
    print(f"  [INFO] Запуск валидации...")
    
    try:
        # Валидация с отключением интернета (избежать ошибок GitHub API)
        data_yaml_str = str(data_yaml.resolve()) if data_yaml.exists() else str(data_yaml)
        results = model.val(
            data=data_yaml_str,
            imgsz=640,
            conf=0.001,  # Низкий порог для полной оценки
            iou=0.6,
            device="cuda:0" if torch.cuda.is_available() else "cpu",
            verbose=False,
            plots=False  # Не строить графики для сравнения
        )
        
        # Извлечь метрики
        metrics = {}
        if hasattr(results, 'results_dict'):
            metrics = results.results_dict
        elif hasattr(results, 'box'):
            metrics = {
                'metrics/mAP50(B)': results.box.map50 if hasattr(results.box, 'map50') else 0,
                'metrics/mAP50-95(B)': results.box.map if hasattr(results.box, 'map') else 0,
                'metrics/precision(B)': results.box.mp if hasattr(results.box, 'mp') else 0,
                'metrics/recall(B)': results.box.mr if hasattr(results.box, 'mr') else 0,
            }
        
        result = {
            'map50': metrics.get('metrics/mAP50(B)', 0),
            'map50_95': metrics.get('metrics/mAP50-95(B)', 0),
            'precision': metrics.get('metrics/precision(B)', 0),
            'recall': metrics.get('metrics/recall(B)', 0),
            'f1': 2 * (metrics.get('metrics/precision(B)', 0) * metrics.get('metrics/recall(B)', 0)) / 
                  (metrics.get('metrics/precision(B)', 0) + metrics.get('metrics/recall(B)', 0) + 1e-8)
        }
        
        # Очистка временного файла
        if 'temp_file_to_clean' in locals() and temp_file_to_clean and temp_file_to_clean.exists():
            try:
                temp_file_to_clean.unlink()
            except:
                pass
        
        return result
    except Exception as e:
        print(f"  [ERROR] Ошибка валидации: {e}")
        import traceback
        traceback.print_exc()
        
        # Очистка временного файла при ошибке
        if 'temp_file_to_clean' in locals() and temp_file_to_clean and temp_file_to_clean.exists():
            try:
                temp_file_to_clean.unlink()
            except:
                pass
        
        return None

def compare_models(old_metrics, new_metrics):
    """Сравнение метрик двух моделей"""
    if not old_metrics or not new_metrics:
        return None
    
    comparison = {}
    
    metrics_names = {
        'map50': 'mAP@0.5',
        'map50_95': 'mAP@0.5:0.95',
        'precision': 'Precision',
        'recall': 'Recall',
        'f1': 'F1-Score'
    }
    
    for key, name in metrics_names.items():
        old_val = old_metrics.get(key, 0)
        new_val = new_metrics.get(key, 0)
        diff = new_val - old_val
        diff_percent = (diff / old_val * 100) if old_val > 0 else 0
        
        comparison[key] = {
            'name': name,
            'old': old_val,
            'new': new_val,
            'diff': diff,
            'diff_percent': diff_percent,
            'better': diff > 0
        }
    
    return comparison

def main():
    """Главная функция"""
    print_header("ВАЛИДАЦИЯ И ЗАМЕНА МОДЕЛИ")
    
    # Пути (используем абсолютные пути для избежания проблем с пробелами)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    config_path = project_root / "config" / "config.yaml"
    
    # Загрузка конфигурации
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    dataset_config = config.get("dataset", {})
    model_config = config.get("model", {})
    
    data_yaml = project_root / dataset_config.get("base_path", "datasets/cigarette_butt") / "data.yaml"
    
    # Новая модель (только что обученная на GPU)
    new_model_path = (project_root / "models" / "cigarette_detector" / "train" / "weights" / "best.pt").resolve()
    
    # Старая модель (текущая) - разрешить путь относительно project_root
    old_model_path_str = model_config.get("weights_path", "models/cigarette_detector/best.pt")
    if Path(old_model_path_str).is_absolute():
        old_model_path = Path(old_model_path_str).resolve()
    else:
        old_model_path = (project_root / old_model_path_str).resolve()
    
    # Целевой путь для новой модели
    target_model_path = (project_root / "models" / "cigarette_detector" / "best.pt").resolve()
    
    # Также разрешить data_yaml
    data_yaml = data_yaml.resolve() if data_yaml.exists() else data_yaml
    
    print_section("1. ВАЛИДАЦИЯ НОВОЙ МОДЕЛИ")
    
    if not new_model_path.exists():
        print(f"  [FAIL] Новая модель не найдена: {new_model_path}")
        return False
    
    new_metrics = validate_model(new_model_path, data_yaml)
    
    if not new_metrics:
        print("  [FAIL] Не удалось провести валидацию новой модели")
        return False
    
    print(f"\n  [OK] Валидация новой модели завершена")
    print(f"  mAP@0.5: {new_metrics['map50']:.4f}")
    print(f"  mAP@0.5:0.95: {new_metrics['map50_95']:.4f}")
    print(f"  Precision: {new_metrics['precision']:.4f} ({new_metrics['precision']*100:.2f}%)")
    print(f"  Recall: {new_metrics['recall']:.4f} ({new_metrics['recall']*100:.2f}%)")
    print(f"  F1-Score: {new_metrics['f1']:.4f}")
    
    # Валидация старой модели для сравнения
    old_metrics = None
    if old_model_path.exists() and old_model_path != new_model_path:
        print_section("2. ВАЛИДАЦИЯ СТАРОЙ МОДЕЛИ (для сравнения)")
        old_metrics = validate_model(old_model_path, data_yaml)
        
        if old_metrics:
            print(f"\n  [OK] Валидация старой модели завершена")
            print(f"  mAP@0.5: {old_metrics['map50']:.4f}")
            print(f"  mAP@0.5:0.95: {old_metrics['map50_95']:.4f}")
            print(f"  Precision: {old_metrics['precision']:.4f} ({old_metrics['precision']*100:.2f}%)")
            print(f"  Recall: {old_metrics['recall']:.4f} ({old_metrics['recall']*100:.2f}%)")
            print(f"  F1-Score: {old_metrics['f1']:.4f}")
        else:
            print("  [WARN] Не удалось провести валидацию старой модели")
    
    # Сравнение моделей
    if old_metrics:
        print_section("3. СРАВНЕНИЕ МОДЕЛЕЙ")
        comparison = compare_models(old_metrics, new_metrics)
        
        if comparison:
            print(f"\n  {'Метрика':<20} {'Старая':<10} {'Новая':<10} {'Разница':<12} {'Улучшение':<10}")
            print(f"  {'-'*70}")
            
            for key, comp in comparison.items():
                status = "[+]" if comp['better'] else "[-]"
                diff_sign = "+" if comp['diff'] >= 0 else ""
                print(f"  {comp['name']:<20} {comp['old']:.4f}     {comp['new']:.4f}     {diff_sign}{comp['diff']:.4f} ({diff_sign}{comp['diff_percent']:.2f}%) {status}")
            
            # Подсчет улучшений
            improvements = sum(1 for c in comparison.values() if c['better'])
            total = len(comparison)
            
            print(f"\n  Улучшено метрик: {improvements}/{total}")
            
            if improvements > total / 2:
                print(f"  [OK] Новая модель лучше по большинству метрик")
            else:
                print(f"  [WARN] Новая модель не улучшила большинство метрик")
    
    # Замена модели
    print_section("4. ЗАМЕНА МОДЕЛИ")
    
    # Создать бэкап старой модели
    if old_model_path.exists() and old_model_path != new_model_path:
        backup_dir = project_root / "models" / "cigarette_detector" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"best_backup_{timestamp}.pt"
        
        print(f"  Создание бэкапа старой модели...")
        shutil.copy(old_model_path, backup_path)
        print(f"  [OK] Бэкап создан: {backup_path}")
    
    # Копирование новой модели
    print(f"  Копирование новой модели...")
    target_model_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(new_model_path, target_model_path)
    print(f"  [OK] Новая модель скопирована: {target_model_path}")
    
    # Удаление старых моделей
    print_section("5. УДАЛЕНИЕ СТАРЫХ МОДЕЛЕЙ")
    
    # Поиск старых моделей
    models_dir = project_root / "models" / "cigarette_detector"
    old_dirs = []
    
    # Старые директории обучения (кроме train)
    if models_dir.exists():
        for item in models_dir.iterdir():
            if item.is_dir() and item.name not in ["train", "backups"]:
                old_dirs.append(item)
                print(f"  Найдена старая директория: {item.name}")
    
    # Удаление старых директорий
    deleted_count = 0
    for old_dir in old_dirs:
        try:
            print(f"  Удаление: {old_dir}")
            shutil.rmtree(old_dir)
            print(f"  [OK] Удалено: {old_dir.name}")
            deleted_count += 1
        except Exception as e:
            print(f"  [WARN] Не удалось удалить {old_dir.name}: {e}")
    
    if deleted_count == 0:
        print(f"  [INFO] Старые директории не найдены")
    else:
        print(f"  [OK] Удалено директорий: {deleted_count}")
    
    # Очистка кэша
    print_section("6. ОЧИСТКА КЭША")
    
    cache_paths = [
        project_root / "datasets" / "cigarette_butt" / "train" / "labels.cache",
        project_root / "datasets" / "cigarette_butt" / "valid" / "labels.cache",
        project_root / "datasets" / "cigarette_butt" / "test" / "labels.cache",
        project_root / "__pycache__",
        project_root / "obelisk" / "__pycache__",
        project_root / "obelisk" / "core" / "__pycache__",
    ]
    
    # Найти все __pycache__
    pycache_dirs = list(project_root.rglob("__pycache__"))
    
    deleted_cache = 0
    
    # Удалить файлы кэша
    for cache_path in cache_paths:
        if cache_path.exists():
            try:
                if cache_path.is_file():
                    cache_path.unlink()
                    print(f"  [OK] Удален кэш: {cache_path.name}")
                elif cache_path.is_dir():
                    shutil.rmtree(cache_path)
                    print(f"  [OK] Удален кэш: {cache_path}")
                deleted_cache += 1
            except Exception as e:
                print(f"  [WARN] Не удалось удалить {cache_path}: {e}")
    
    # Удалить все __pycache__ директории
    for pycache_dir in pycache_dirs:
        try:
            shutil.rmtree(pycache_dir)
            deleted_cache += 1
        except Exception as e:
            pass  # Игнорируем ошибки для __pycache__
    
    if deleted_cache > 0:
        print(f"  [OK] Удалено кэш-файлов: {deleted_cache}")
    else:
        print(f"  [INFO] Кэш не найден или уже очищен")
    
    # Итоги
    print_header("ИТОГИ")
    
    print(f"\n  Новая модель:")
    print(f"    Путь: {target_model_path}")
    print(f"    mAP@0.5: {new_metrics['map50']:.4f}")
    print(f"    mAP@0.5:0.95: {new_metrics['map50_95']:.4f}")
    print(f"    Precision: {new_metrics['precision']:.4f} ({new_metrics['precision']*100:.2f}%)")
    print(f"    Recall: {new_metrics['recall']:.4f} ({new_metrics['recall']*100:.2f}%)")
    
    if old_metrics and comparison:
        improvements = sum(1 for c in comparison.values() if c['better'])
        print(f"\n  Сравнение со старой моделью:")
        print(f"    Улучшено метрик: {improvements}/{len(comparison)}")
    
    print(f"\n  [OK] Замена модели завершена успешно!")
    print(f"  [OK] Старые модели удалены")
    print(f"  [OK] Кэш очищен")
    print(f"\n  Модель готова к использованию: {target_model_path}")
    
    print("\n" + "=" * 70)
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n[WARN] Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

