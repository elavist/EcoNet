"""
Конвертация сегментов (полигонов) в боксы в датасете
YOLO автоматически конвертирует сегменты в боксы, но лучше иметь консистентный датасет
"""

from pathlib import Path
from typing import Tuple
import numpy as np


def segments2boxes(segments):
    """
    Конвертировать сегменты (полигоны) в боксы (bounding boxes)
    
    Args:
        segments: Список сегментов, каждый сегмент - массив точек [x1, y1, x2, y2, ...]
    
    Returns:
        Боксы в формате [x_center, y_center, width, height] (нормализованные)
    """
    boxes = []
    for segment in segments:
        # Сегмент: [x1, y1, x2, y2, x3, y3, ...]
        # Преобразуем в массив точек
        points = np.array(segment).reshape(-1, 2)
        
        # Найти bounding box
        x_min, y_min = points.min(axis=0)
        x_max, y_max = points.max(axis=0)
        
        # Конвертировать в формат YOLO (x_center, y_center, width, height)
        x_center = (x_min + x_max) / 2
        y_center = (y_min + y_max) / 2
        width = x_max - x_min
        height = y_max - y_min
        
        boxes.append([x_center, y_center, width, height])
    
    return boxes


def convert_label_file(label_path: Path) -> Tuple[bool, int]:
    """
    Конвертировать файл с сегментами в боксы
    
    Args:
        label_path: Путь к файлу аннотаций
    
    Returns:
        (были_сегменты, количество_конвертированных)
    """
    if not label_path.exists():
        return False, 0
    
    with open(label_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    converted_lines = []
    had_segments = False
    converted_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split()
        if len(parts) < 5:
            continue  # Пропустить некорректные строки
        
        class_id = parts[0]
        coords = [float(x) for x in parts[1:]]
        
        # Проверить, это сегмент (более 4 координат) или бокс (ровно 4)
        if len(coords) > 4:
            # Это сегмент - конвертировать в бокс
            had_segments = True
            boxes = segments2boxes([coords])
            if boxes:
                box = boxes[0]
                # Формат YOLO: class x_center y_center width height
                converted_line = f"{class_id} {box[0]:.6f} {box[1]:.6f} {box[2]:.6f} {box[3]:.6f}\n"
                converted_lines.append(converted_line)
                converted_count += 1
        else:
            # Это уже бокс - оставить как есть
            converted_lines.append(line + '\n')
    
    # Сохранить конвертированный файл
    if had_segments:
        with open(label_path, 'w', encoding='utf-8') as f:
            f.writelines(converted_lines)
    
    return had_segments, converted_count


def check_and_convert_dataset(dataset_path: Path, dry_run: bool = False):
    """
    Проверить и конвертировать весь датасет
    
    Args:
        dataset_path: Путь к датасету (datasets/cigarette_butt)
        dry_run: Только проверить, не конвертировать
    """
    import sys
    import io
    
    # Настройка кодировки для корректного вывода
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("=" * 70)
    print("ПРОВЕРКА И КОНВЕРТАЦИЯ СЕГМЕНТОВ В БОКСЫ")
    if dry_run:
        print("РЕЖИМ ПРОВЕРКИ (dry-run) - файлы не будут изменены")
    print("=" * 70)
    
    splits = ["train", "valid", "test"]
    total_segments = 0
    total_converted = 0
    total_files_with_segments = 0
    
    for split in splits:
        labels_path = dataset_path / split / "labels"
        
        if not labels_path.exists():
            print(f"[WARN] {split}/labels не найден, пропуск")
            continue
        
        print(f"\nПроверка {split}/labels...")
        
        label_files = list(labels_path.glob("*.txt"))
        print(f"   Найдено файлов: {len(label_files)}")
        
        split_segments = 0
        split_converted = 0
        split_files_with_segments = 0
        
        for label_file in label_files:
            if dry_run:
                # Только проверка без конвертации
                with open(label_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        parts = line.strip().split()
                        if len(parts) > 5:  # Сегмент
                            split_files_with_segments += 1
                            split_segments += 1
                            break
            else:
                had_segments, converted = convert_label_file(label_file)
                
                if had_segments:
                    split_files_with_segments += 1
                    split_segments += converted
                    split_converted += converted
        
        print(f"   Файлов с сегментами: {split_files_with_segments}")
        if not dry_run:
            print(f"   Конвертировано сегментов: {split_converted}")
        
        total_segments += split_segments
        total_converted += split_converted
        total_files_with_segments += split_files_with_segments
    
    print("\n" + "=" * 70)
    print("ИТОГИ")
    print("=" * 70)
    print(f"Всего файлов с сегментами: {total_files_with_segments}")
    if not dry_run:
        print(f"Всего конвертировано сегментов: {total_converted}")
    
    if total_files_with_segments > 0:
        if dry_run:
            print(f"\n[WARN] Найдены файлы с сегментами!")
            print(f"   Запустите без --dry-run для конвертации:")
            print(f"   python scripts\\convert_segments_to_boxes.py")
        else:
            print(f"\n[OK] Датасет очищен! Все сегменты конвертированы в боксы.")
            print(f"   Теперь датасет содержит только боксы (консистентный формат).")
            
            # Удалить кэш
            print(f"\nУдаление кэша YOLO...")
            cache_files = list(dataset_path.glob("**/labels.cache"))
            for cache_file in cache_files:
                try:
                    cache_file.unlink()
                    print(f"   Удален: {cache_file}")
                except Exception as e:
                    print(f"   [WARN] Не удалось удалить {cache_file}: {e}")
            
            print(f"\n[INFO] Рекомендуется перезапустить обучение:")
            print(f"   python scripts\\retrain_full_dataset.py")
    else:
        print(f"\n[OK] Датасет уже содержит только боксы - конвертация не требуется.")
    
    print("=" * 70)


def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Конвертация сегментов в боксы в датасете YOLO"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="datasets/cigarette_butt",
        help="Путь к датасету (по умолчанию: datasets/cigarette_butt)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только проверить, не конвертировать"
    )
    
    args = parser.parse_args()
    
    dataset_path = Path(args.dataset)
    
    if not dataset_path.exists():
        print(f"❌ Датасет не найден: {dataset_path}")
        return
    
    check_and_convert_dataset(dataset_path, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

