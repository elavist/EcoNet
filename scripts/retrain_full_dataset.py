"""
Дообучение модели на полном датасете (9000+ фото)
С оптимизированными параметрами для достижения >95% точности
"""

import yaml
from pathlib import Path
from ultralytics import YOLO
import shutil
from datetime import datetime

def retrain_full_dataset():
    """Дообучение на полном датасете с оптимизацией для >95% точности"""
    
    # Загрузка конфигурации
    config_path = Path("config/config.yaml")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    model_config = config.get("model", {})
    dataset_config = config.get("dataset", {})
    
    # Путь к текущей обученной модели
    current_model = Path(model_config.get("weights_path", "models/cigarette_detector/best.pt"))
    
    if not current_model.exists():
        print("❌ Текущая модель не найдена!")
        print("Сначала обучите базовую модель: python scripts/train_model.py")
        return
    
    data_config = dataset_config.get("base_path") + "/data.yaml"
    
    # Оптимизированные параметры для достижения >95% точности
    epochs = 150  # Больше эпох для лучшего обучения
    batch_size = 16  # Можно увеличить до 32 если есть GPU
    imgsz = 640
    
    print("=" * 70)
    print("ДООБУЧЕНИЕ МОДЕЛИ НА ПОЛНОМ ДАТАСЕТЕ (9000+ фото)")
    print("Цель: >95% точности (Precision)")
    print("=" * 70)
    print(f"Базовая модель: {current_model}")
    print(f"Датасет: {data_config}")
    print(f"Эпохи: {epochs}")
    print(f"Размер батча: {batch_size}")
    print(f"Размер изображения: {imgsz}")
    print("=" * 70)
    print("⚠️ ВНИМАНИЕ: Это займет много времени:")
    print("   CPU: 4-6 часов")
    print("   GPU: 40-80 минут")
    print("=" * 70)
    
    # Загрузка существующей модели
    print("\n📦 Загрузка существующей модели...")
    model = YOLO(str(current_model))
    
    # Оценка текущей модели
    print("📊 Оценка текущей модели на валидационном наборе...")
    current_metrics = model.val(data=data_config, verbose=False)
    current_map = current_metrics.results_dict.get('metrics/mAP50(B)', 0)
    current_precision = current_metrics.results_dict.get('metrics/precision(B)', 0)
    current_recall = current_metrics.results_dict.get('metrics/recall(B)', 0)
    
    print(f"   Текущий mAP@0.5: {current_map:.4f}")
    print(f"   Текущий Precision: {current_precision:.4f}")
    print(f"   Текущий Recall: {current_recall:.4f}")
    print("✅ Модель загружена\n")
    
    # Дообучение с оптимизированными параметрами
    print("🚀 Начало дообучения...")
    print("   Используются оптимизированные параметры для достижения >95% точности")
    print()
    
    results = model.train(
        # Основные параметры
        data=data_config,
        epochs=epochs,
        batch=batch_size,
        imgsz=imgsz,
        
        # Оптимизация обучения
        optimizer='AdamW',  # AdamW лучше чем SGD для тонкой настройки
        lr0=0.0001,  # Меньшая начальная скорость для дообучения
        lrf=0.01,    # Финальная скорость обучения
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,  # Разогрев
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        
        # Аугментация для разнообразия данных
        augment=True,
        hsv_h=0.015,  # Изменение оттенка
        hsv_s=0.7,    # Изменение насыщенности  
        hsv_v=0.4,    # Изменение яркости
        degrees=10,   # Поворот ±10 градусов
        translate=0.1,  # Смещение до 10%
        scale=0.5,    # Масштабирование
        shear=0.0,    # Сдвиг
        perspective=0.0,  # Перспектива
        flipud=0.0,   # Вертикальное отражение
        fliplr=0.5,   # Горизонтальное отражение (50%)
        mosaic=1.0,   # Mosaic аугментация
        mixup=0.0,    # Mixup выключен для детекции
        copy_paste=0.0,  # Copy-paste выключен
        
        # Регуляризация для предотвращения переобучения
        dropout=0.0,  # Dropout (для YOLOv8 обычно не нужен)
        
        # Дополнительные параметры
        close_mosaic=10,  # Отключить mosaic в последние 10 эпох
        patience=50,      # Early stopping если нет улучшений 50 эпох
        save=True,
        save_period=-1,   # Сохранять только лучшую модель
        val=True,         # Валидация на каждом эпохе
        
        # Проект
        project="models/cigarette_detector",
        name="retrain_full",
        exist_ok=True,
        
        # Использовать текущие веса как начальные
        pretrained=False,  # Уже используем pretrained веса из текущей модели
        resume=False,      # Не продолжать, а начать заново с лучшими параметрами
        
        # Логирование
        verbose=True,
        plots=True,  # Построить графики
    )
    
    # Результаты
    new_map = results.results_dict.get('metrics/mAP50(B)', 0)
    new_precision = results.results_dict.get('metrics/precision(B)', 0)
    new_recall = results.results_dict.get('metrics/recall(B)', 0)
    
    print("\n" + "=" * 70)
    print("ДООБУЧЕНИЕ ЗАВЕРШЕНО!")
    print("=" * 70)
    print(f"Лучшая модель: models/cigarette_detector/retrain_full/weights/best.pt")
    print()
    print("📊 РЕЗУЛЬТАТЫ:")
    print(f"   mAP@0.5: {new_map:.4f}")
    print(f"   Precision: {new_precision:.4f} ({new_precision*100:.2f}%)")
    print(f"   Recall: {new_recall:.4f} ({new_recall*100:.2f}%)")
    print()
    
    # Сравнение
    print("📈 СРАВНЕНИЕ:")
    print(f"   Старая модель:")
    print(f"      mAP@0.5: {current_map:.4f}")
    print(f"      Precision: {current_precision:.4f} ({current_precision*100:.2f}%)")
    print(f"      Recall: {current_recall:.4f} ({current_recall*100:.2f}%)")
    print()
    print(f"   Новая модель:")
    print(f"      mAP@0.5: {new_map:.4f}")
    print(f"      Precision: {new_precision:.4f} ({new_precision*100:.2f}%)")
    print(f"      Recall: {new_recall:.4f} ({new_recall*100:.2f}%)")
    print()
    
    improvement_map = new_map - current_map
    improvement_precision = new_precision - current_precision
    improvement_recall = new_recall - current_recall
    
    print(f"   Улучшение:")
    print(f"      mAP@0.5: {improvement_map:+.4f}")
    print(f"      Precision: {improvement_precision:+.4f} ({improvement_precision*100:+.2f}%)")
    print(f"      Recall: {improvement_recall:+.4f} ({improvement_recall*100:+.2f}%)")
    print()
    
    # Проверка достижения цели
    if new_precision >= 0.95:
        print("🎉 ЦЕЛЬ ДОСТИГНУТА! Precision >= 95%")
    elif new_precision >= 0.90:
        print("✅ Отличный результат! Precision >= 90%")
        print("💡 Можно попробовать больше эпох или улучшить датасет")
    elif new_precision >= 0.85:
        print("✅ Хороший результат! Precision >= 85%")
        print("💡 Рекомендуется дополнительное обучение")
    else:
        print("⚠️ Precision ниже 85%")
        print("💡 Рекомендации:")
        print("   - Проверьте качество разметки датасета")
        print("   - Убедитесь что все 9000+ фото используются")
        print("   - Рассмотрите увеличение количества эпох")
    
    print("=" * 70)
    
    # Скопировать новую модель
    best_model = Path("models/cigarette_detector/retrain_full/weights/best.pt")
    target_model = Path(model_config.get("weights_path", "models/cigarette_detector/best.pt"))
    
    if best_model.exists():
        # Бэкап старой модели
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path("models/cigarette_detector/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_model = backup_dir / f"best_backup_{timestamp}.pt"
        
        if current_model.exists():
            shutil.copy(current_model, backup_model)
            print(f"📦 Старая модель сохранена: {backup_model}")
        
        # Копировать новую модель
        target_model.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(best_model, target_model)
        print(f"✅ Новая модель сохранена: {target_model}")
        print()
        print("💡 Для использования новой модели перезапустите детектор")
    
    return results


if __name__ == "__main__":
    retrain_full_dataset()

