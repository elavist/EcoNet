"""
Скрипт для настройки существующего датасета
Создает символические ссылки и конфигурацию для интеграции с системой
"""

import shutil
from pathlib import Path
import yaml


def setup_dataset():
    """Настройка датасета для использования в системе"""
    
    # Пути
    current_dataset_path = Path("Cigarette Butt Detector.v5i.yolov8")
    target_dataset_path = Path("datasets/cigarette_butt")
    
    # Создать целевую структуру
    target_dataset_path.mkdir(parents=True, exist_ok=True)
    
    # Копировать или создать символические ссылки (на Windows копируем)
    import platform
    is_windows = platform.system() == "Windows"
    
    print("Настройка датасета...")
    print(f"Источник: {current_dataset_path}")
    print(f"Цель: {target_dataset_path}")
    
    # Копировать структуру датасета
    for split in ["train", "valid", "test"]:
        source_images = current_dataset_path / split / "images"
        source_labels = current_dataset_path / split / "labels"
        
        target_images = target_dataset_path / split / "images"
        target_labels = target_dataset_path / split / "labels"
        
        if source_images.exists():
            if is_windows:
                # Копировать на Windows
                if target_images.exists():
                    print(f"Пропуск {split}/images (уже существует)")
                else:
                    shutil.copytree(source_images, target_images)
                    print(f"Скопирован {split}/images")
            else:
                # Символическая ссылка на Linux/Mac
                if target_images.exists():
                    target_images.unlink()
                target_images.symlink_to(source_images.absolute())
                print(f"Создана ссылка {split}/images")
        
        if source_labels.exists():
            if is_windows:
                if target_labels.exists():
                    print(f"Пропуск {split}/labels (уже существует)")
                else:
                    shutil.copytree(source_labels, target_labels)
                    print(f"Скопирован {split}/labels")
            else:
                if target_labels.exists():
                    target_labels.unlink()
                target_labels.symlink_to(source_labels.absolute())
                print(f"Создана ссылка {split}/labels")
    
    # Создать data.yaml в целевой директории
    data_yaml_path = target_dataset_path / "data.yaml"
    
    # Используем относительные пути от файла data.yaml
    data_config = {
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": 2,
        "names": {
            0: '0',
            1: 'cig_butt'
        }
    }
    
    with open(data_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data_config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"Создан {data_yaml_path}")
    
    # Обновить конфигурацию системы
    config_path = Path("config/config.yaml")
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Обновить пути к датасету
        config["dataset"]["base_path"] = str(target_dataset_path)
        config["dataset"]["train_path"] = str(target_dataset_path / "train" / "images")
        config["dataset"]["val_path"] = str(target_dataset_path / "valid" / "images")
        config["dataset"]["test_path"] = str(target_dataset_path / "test" / "images")
        config["model"]["data_config"] = str(data_yaml_path)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"Обновлена конфигурация: {config_path}")
    
    print("✅ Датaset настроен успешно!")


if __name__ == "__main__":
    setup_dataset()


