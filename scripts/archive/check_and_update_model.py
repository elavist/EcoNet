"""
Проверка новой модели и применение улучшений
Сравнивает новую модель с текущей и применяет если она лучше
"""

import yaml
from pathlib import Path
from ultralytics import YOLO
import shutil
from datetime import datetime


def check_and_update_model():
    """Проверить новую модель и применить улучшения"""
    
    # Загрузка конфигурации
    config_path = Path("config/config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    model_config = config.get("model", {})
    dataset_config = config.get("dataset", {})
    
    # Пути к моделям
    new_model_path = Path("models/cigarette_detector/retrain_full/weights/best.pt")
    current_model_path = Path(model_config.get("weights_path", "models/cigarette_detector/best.pt"))
    
    data_config = dataset_config.get("base_path") + "/data.yaml"
    
    print("=" * 70)
    print("ПРОВЕРКА И ПРИМЕНЕНИЕ НОВОЙ МОДЕЛИ")
    print("=" * 70)
    
    # Проверка наличия новой модели
    if not new_model_path.exists():
        print(f"❌ Новая модель не найдена: {new_model_path}")
        print("💡 Убедитесь что обучение завершилось корректно")
        return
    
    print(f"✅ Новая модель найдена: {new_model_path}")
    print(f"📅 Размер: {new_model_path.stat().st_size / (1024*1024):.2f} MB")
    print(f"📅 Дата изменения: {datetime.fromtimestamp(new_model_path.stat().st_mtime)}")
    
    # Загрузка текущей модели
    if current_model_path.exists():
        print(f"\n📦 Загрузка текущей модели: {current_model_path}")
        current_model = YOLO(str(current_model_path))
        
        print("📊 Оценка текущей модели...")
        current_metrics = current_model.val(data=data_config, verbose=False)
        
        current_map = current_metrics.results_dict.get('metrics/mAP50(B)', 0)
        current_precision = current_metrics.results_dict.get('metrics/precision(B)', 0)
        current_recall = current_metrics.results_dict.get('metrics/recall(B)', 0)
        
        print(f"   mAP@0.5: {current_map:.4f} ({current_map*100:.2f}%)")
        print(f"   Precision: {current_precision:.4f} ({current_precision*100:.2f}%)")
        print(f"   Recall: {current_recall:.4f} ({current_recall*100:.2f}%)")
    else:
        print(f"\n⚠️ Текущая модель не найдена: {current_model_path}")
        print("💡 Будет создана новая")
        current_map = 0
        current_precision = 0
        current_recall = 0
    
    # Загрузка новой модели
    print(f"\n📦 Загрузка новой модели: {new_model_path}")
    new_model = YOLO(str(new_model_path))
    
    print("📊 Оценка новой модели...")
    new_metrics = new_model.val(data=data_config, verbose=False)
    
    new_map = new_metrics.results_dict.get('metrics/mAP50(B)', 0)
    new_precision = new_metrics.results_dict.get('metrics/precision(B)', 0)
    new_recall = new_metrics.results_dict.get('metrics/recall(B)', 0)
    
    print(f"   mAP@0.5: {new_map:.4f} ({new_map*100:.2f}%)")
    print(f"   Precision: {new_precision:.4f} ({new_precision*100:.2f}%)")
    print(f"   Recall: {new_recall:.4f} ({new_recall*100:.2f}%)")
    
    # Сравнение
    print("\n" + "=" * 70)
    print("СРАВНЕНИЕ МОДЕЛЕЙ")
    print("=" * 70)
    
    improvement_map = new_map - current_map
    improvement_precision = new_precision - current_precision
    improvement_recall = new_recall - current_recall
    
    print(f"\n📈 Улучшение:")
    print(f"   mAP@0.5: {improvement_map:+.4f} ({improvement_map*100:+.2f}%)")
    print(f"   Precision: {improvement_precision:+.4f} ({improvement_precision*100:+.2f}%)")
    print(f"   Recall: {improvement_recall:+.4f} ({improvement_recall*100:+.2f}%)")
    
    # Решение о применении
    print("\n" + "=" * 70)
    
    # Проверка: лучше ли новая модель (хотя бы по одной метрике)
    is_better = (
        improvement_map > 0 or
        improvement_precision > 0 or
        improvement_recall > 0
    )
    
    if is_better:
        print("✅ НОВАЯ МОДЕЛЬ ЛУЧШЕ!")
        
        # Бэкап старой модели
        if current_model_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = Path("models/cigarette_detector/backups")
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f"best_backup_{timestamp}.pt"
            
            shutil.copy(current_model_path, backup_path)
            print(f"📦 Старая модель сохранена: {backup_path}")
        
        # Копирование новой модели
        current_model_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(new_model_path, current_model_path)
        
        print(f"✅ Новая модель применена: {current_model_path}")
        
        # Проверка достижения цели
        if new_precision >= 0.95:
            print("\n🎉 ЦЕЛЬ ДОСТИГНУТА! Precision >= 95%")
        
        print("\n💡 Теперь вы можете использовать новую модель:")
        print(f"   python scripts\\test_with_webcam.py --ip 0 --conf 0.3")
        print(f"   python scripts\\test_video_file.py \"video.mp4\"")
        
    else:
        print("⚠️ НОВАЯ МОДЕЛЬ НЕ ЛУЧШЕ ТЕКУЩЕЙ")
        print("💡 Оставляем текущую модель")
        
        if improvement_map == 0 and improvement_precision == 0 and improvement_recall == 0:
            print("   (Метрики идентичны)")
        else:
            print("   (Некоторые метрики ниже)")
    
    print("=" * 70)
    
    # Итоговая таблица
    print("\n📊 ИТОГОВАЯ ТАБЛИЦА:")
    print(f"{'Метрика':<15} {'Старая':<12} {'Новая':<12} {'Улучшение':<12}")
    print("-" * 70)
    print(f"{'mAP@0.5':<15} {current_map:.4f}     {new_map:.4f}     {improvement_map:+.4f}")
    print(f"{'Precision':<15} {current_precision:.4f}     {new_precision:.4f}     {improvement_precision:+.4f}")
    print(f"{'Recall':<15} {current_recall:.4f}     {new_recall:.4f}     {improvement_recall:+.4f}")
    print("=" * 70)


if __name__ == "__main__":
    check_and_update_model()

