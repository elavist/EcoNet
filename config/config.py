"""
Загрузка конфигурации системы
"""

import yaml
from pathlib import Path
from typing import Dict, Optional


def load_config(config_path: Optional[Path] = None) -> Dict:
    """
    Загрузка конфигурации из YAML файла
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Словарь с конфигурацией
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


