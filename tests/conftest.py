"""
Конфигурация pytest для тестов ЭКОНЕТ
Фикстуры и утилиты для тестирования
"""

import pytest
import asyncio
import sys
from pathlib import Path
import yaml
import logging
import tempfile
import shutil
from typing import Dict, Any

# Добавление корня проекта в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Настройка логирования для тестов
logging.basicConfig(
    level=logging.WARNING,  # Минимум логов в тестах
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Примечание: event_loop фикстуру создает pytest-asyncio автоматически
# Не нужно создавать свою, это конфликтует с pytest-asyncio

@pytest.fixture(scope="session")
def project_root():
    """Корневая директория проекта"""
    return root_dir


@pytest.fixture(scope="session")
def gpu_test_manager():
    """GPU Manager для тестов"""
    try:
        from obelisk.core.managers.gpu_test_manager import get_test_gpu_manager
        manager = get_test_gpu_manager(device_id=0)
        
        # Резервируем GPU для тестов
        if manager.reserve_gpu_for_tests():
            yield manager
            # Очистка после всех тестов
            manager.cleanup()
        else:
            yield None
    except Exception as e:
        logger.warning(f"Не удалось инициализировать GPU Test Manager: {e}")
        yield None


@pytest.fixture(scope="session")
def test_config():
    """Загрузка тестовой конфигурации"""
    config_path = root_dir / "config" / "config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Модификация конфигурации для тестов
    config["logging"]["level"] = "WARNING"
    config["database"]["sqlite_path"] = "data/test_obelisk.db"
    
    return config


@pytest.fixture(scope="function")
def temp_dir():
    """Временная директория для тестов"""
    temp_path = Path(tempfile.mkdtemp(prefix="econet_test_"))
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def temp_data_dir(temp_dir):
    """Временная директория для данных тестов"""
    data_dir = temp_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Создание поддиректорий
    (data_dir / "media").mkdir()
    (data_dir / "media" / "videos").mkdir()
    (data_dir / "media" / "photos").mkdir()
    (data_dir / "media" / "detections").mkdir()
    (data_dir / "models").mkdir()
    (data_dir / "raw" / "frames").mkdir(parents=True)
    (data_dir / "labeled").mkdir()
    (data_dir / "logs").mkdir()
    
    return data_dir


@pytest.fixture(scope="function")
def test_image():
    """Создание тестового изображения"""
    import numpy as np
    import cv2
    
    # Создаем простое тестовое изображение 640x480
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Добавляем градиент
    for y in range(480):
        intensity = int(255 * (y / 480))
        image[y, :] = [intensity // 3, intensity // 2, intensity]
    
    return image


@pytest.fixture(scope="function")
def test_video(temp_dir):
    """Создание тестового видео файла"""
    import cv2
    import numpy as np
    
    video_path = temp_dir / "test_video.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 20.0, (640, 480))
    
    # Создаем 10 кадров
    for i in range(10):
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        out.write(frame)
    
    out.release()
    return video_path


@pytest.fixture(scope="function")
async def unified_engine(test_config, temp_data_dir, gpu_test_manager):
    """Создание UnifiedEngine для тестов
    
    ЛЕГКОВЕСНАЯ версия - НЕ инициализирует компоненты для быстрых тестов.
    Тесты должны проверять _test_initialized перед использованием компонентов.
    """
    from obelisk.core.engines.unified_engine import UnifiedEngine
    
    # Модифицируем конфигурацию для тестов
    test_config_copy = test_config.copy()
    if "data_lake" in test_config_copy:
        test_config_copy["data_lake"]["base_path"] = str(temp_data_dir)
    
    # ОТКЛЮЧАЕМ все компоненты, которые могут зависать
    if "active_learning" in test_config_copy:
        test_config_copy["active_learning"]["enabled"] = False
    
    # Отключаем MQTT полностью
    if "mqtt_topics" in test_config_copy:
        test_config_copy["mqtt_topics"] = {}
    
    # Отключаем database для тестов
    if "database" in test_config_copy:
        test_config_copy["database"]["enabled"] = False
    
    # ИСПРАВЛЕНИЕ: МОДЕЛЬ ДОЛЖНА ЗАГРУЖАТЬСЯ ПЕРЕД ТЕСТИРОВАНИЕМ
    # Используем CPU для тестов (быстрее и стабильнее)
    if "model_engine" in test_config_copy:
        test_config_copy["model_engine"]["device"] = "cpu"
        # ВКЛЮЧАЕМ загрузку моделей для тестов (если они доступны)
        # Если модели не найдены, тесты будут пропущены
        if "models" in test_config_copy["model_engine"]:
            # Проверяем доступность моделей
            available_models = []
            for model_cfg in test_config_copy["model_engine"]["models"]:
                model_path = model_cfg.get("path")
                if model_path:
                    # Проверяем существование модели
                    model_path_obj = Path(model_path)
                    if not model_path_obj.is_absolute():
                        # Относительный путь - ищем от корня проекта
                        project_root = Path(__file__).parent.parent
                        model_path_obj = (project_root / model_path).resolve()
                    
                    if model_path_obj.exists() and model_path_obj.suffix == '.pt':
                        model_cfg["enabled"] = True
                        available_models.append(model_cfg)
                        logger.info(f"✅ Модель найдена для тестов: {model_path_obj}")
                    else:
                        logger.warning(f"⚠️ Модель не найдена: {model_path_obj} (будет пропущена)")
                        model_cfg["enabled"] = False
                else:
                    model_cfg["enabled"] = False
            
            # Если есть доступные модели, используем их
            if available_models:
                test_config_copy["model_engine"]["models"] = available_models
                logger.info(f"✅ {len(available_models)} модель(ей) будет загружена для тестов")
            else:
                # Если моделей нет, используем основную модель из config.model.weights_path
                if "model" in test_config_copy:
                    main_model_path = test_config_copy["model"].get("weights_path")
                    if main_model_path:
                        main_model_path_obj = Path(main_model_path)
                        if not main_model_path_obj.is_absolute():
                            project_root = Path(__file__).parent.parent
                            main_model_path_obj = (project_root / main_model_path).resolve()
                        
                        if main_model_path_obj.exists() and main_model_path_obj.suffix == '.pt':
                            # Добавляем основную модель
                            test_config_copy["model_engine"]["models"] = [{
                                "name": "primary",
                                "path": str(main_model_path_obj),
                                "weight": 1.0,
                                "enabled": True
                            }]
                            logger.info(f"✅ Основная модель найдена для тестов: {main_model_path_obj}")
                        else:
                            logger.warning(f"⚠️ Основная модель не найдена: {main_model_path_obj}")
                            test_config_copy["model_engine"]["models"] = []
                    else:
                        test_config_copy["model_engine"]["models"] = []
                else:
                    test_config_copy["model_engine"]["models"] = []
    
    # ИСПРАВЛЕНИЕ: НЕ отключаем загрузку модели - она должна загружаться
    # Если модель не найдена, тесты будут пропущены
    # if "model" in test_config_copy:
    #     test_config_copy["model"]["weights_path"] = str(temp_data_dir / "nonexistent" / "model.pt")
    
    engine = UnifiedEngine(test_config_copy, project_root=root_dir)
    
    initialized = False
    init_error = None
    
    try:
        logger.debug("Начало инициализации UnifiedEngine (таймаут: 30s)")
        await asyncio.wait_for(engine.initialize(), timeout=30.0)
        initialized = True
        logger.info("UnifiedEngine инициализирован успешно")
        
        if not engine._initialized:
            initialized = False
            init_error = "initialize() завершился, но _initialized = False"
    except asyncio.TimeoutError:
        logger.warning("Инициализация UnifiedEngine превысила таймаут (30s)")
        init_error = "timeout"
    except Exception as e:
        logger.warning(f"Ошибка инициализации UnifiedEngine: {e}", exc_info=True)
        init_error = f"{type(e).__name__}: {str(e)}"
        
        if hasattr(engine, '_initialized') and engine._initialized:
            initialized = True
    
    engine._test_initialized = initialized
    engine._test_init_error = init_error
    
    if hasattr(engine, '_init_error') and not initialized:
        if not init_error or init_error == "timeout":
            init_error = getattr(engine, '_init_error', init_error)
        engine._test_init_error = init_error
    
    yield engine
    
    try:
        if gpu_test_manager:
            gpu_test_manager.cleanup()
        if hasattr(engine, 'model_engine') and engine.model_engine:
            try:
                if hasattr(engine.model_engine, 'models'):
                    engine.model_engine.models.clear()
            except Exception:
                pass
        if hasattr(engine, 'detection_cache'):
            engine.detection_cache.clear()
    except Exception as e:
        logger.debug(f"Ошибка при очистке ресурсов: {e}")


@pytest.fixture(scope="function")
def model_engine(test_config):
    """Создание ModelEngine для тестов"""
    from obelisk.core.engines.model_engine import ModelEngine
    
    engine = ModelEngine(test_config)
    return engine


@pytest.fixture(scope="function")
def object_tracker(test_config):
    """Создание ObjectTracker для тестов"""
    from obelisk.core.processors.object_tracker import ObjectTracker
    
    config = test_config.get("object_tracking", {})
    tracker = ObjectTracker(
        iou_threshold=config.get("iou_threshold", 0.86),
        max_missed_frames=config.get("max_missed_frames", 5)
    )
    return tracker


@pytest.fixture(scope="function")
def mock_database():
    """Создание мок базы данных"""
    from unittest.mock import MagicMock
    
    db = MagicMock()
    db.execute = MagicMock(return_value=None)
    db.fetchall = MagicMock(return_value=[])
    db.fetchone = MagicMock(return_value=None)
    db.commit = MagicMock()
    
    return db


@pytest.fixture(scope="function")
def mock_mqtt_client():
    """Создание мок MQTT клиента"""
    from unittest.mock import MagicMock, AsyncMock
    
    client = MagicMock()
    client.publish = AsyncMock()
    client.subscribe = AsyncMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.is_connected = MagicMock(return_value=True)
    
    return client


@pytest.fixture(scope="function")
def sample_detection():
    """Образец детекции для тестов"""
    return {
        "class_id": 0,
        "confidence": 0.85,
        "bbox": [100, 100, 200, 200],  # x1, y1, x2, y2
        "class_name": "cig_butt",
        "timestamp": "2025-01-21T10:00:00"
    }


@pytest.fixture(scope="function")
def sample_task(sample_detection):
    """Образец задачи для тестов"""
    return {
        "task_id": "task_001",
        "detection": sample_detection,
        "status": "pending",
        "priority": 1,
        "robot_id": None,
        "created_at": "2025-01-21T10:00:00"
    }


@pytest.fixture(scope="function")
async def test_engine(test_config):
    """Создание TestEngine для тестов
    
    ЛЕГКОВЕСНАЯ версия - инициализирует только базовые компоненты.
    """
    from obelisk.core.engines.test_engine import TestEngine
    
    # Модифицируем конфигурацию для тестов
    test_config_copy = test_config.copy()
    
    # Отключаем тяжелые компоненты
    if "active_learning" in test_config_copy:
        test_config_copy["active_learning"]["enabled"] = False
    
    if "mqtt_topics" in test_config_copy:
        test_config_copy["mqtt_topics"] = {}
    
    if "database" in test_config_copy:
        test_config_copy["database"]["enabled"] = False
    
    engine = TestEngine(test_config_copy, project_root=root_dir)
    
    # БЫСТРАЯ инициализация с таймаутом
    initialized = False
    init_error = None
    
    try:
        await asyncio.wait_for(engine.initialize(), timeout=5.0)
        initialized = True
        logger.debug("✅ TestEngine инициализирован успешно")
    except asyncio.TimeoutError:
        logger.debug("⚠️ Инициализация TestEngine превысила таймаут (5s)")
        init_error = "timeout"
    except Exception as e:
        logger.debug(f"⚠️ Ошибка инициализации TestEngine: {e}")
        init_error = str(e)
    
    # Сохраняем флаг инициализации
    engine._test_initialized = initialized
    engine._test_init_error = init_error
    
    yield engine
    
    # Мгновенная очистка
    try:
        await engine.shutdown()
    except Exception:
        pass

