"""
Unit тесты для ModelTesting
Полностью синхронные тесты без зависаний
"""

import pytest
import numpy as np


# ============================================================================
# ГРУППА 1: БАЗОВЫЕ ТЕСТЫ (без unified_engine) - ВСЕГДА РАБОТАЮТ
# ============================================================================

class TestModelTesterBasic:
    """Базовые тесты ModelTester - синхронные, быстрые, без зависимостей"""
    
    @pytest.mark.unit
    def test_initialization(self):
        """Тест инициализации ModelTester"""
        from obelisk.core.model_testing import ModelTester
        
        tester = ModelTester(None)
        assert tester is not None
        assert tester.unified_engine is None
        assert hasattr(tester, 'test_results')
        assert isinstance(tester.test_results, list)
    
    @pytest.mark.unit
    def test_initialization_with_gpu(self):
        """Тест инициализации ModelTester с GPU венозной системой"""
        from obelisk.core.model_testing import ModelTester
        
        tester = ModelTester(None, gpu_circulatory=None)
        assert tester is not None
        assert tester.gpu_circulatory is None
    
    @pytest.mark.unit
    def test_is_model_loaded_none(self):
        """Тест проверки модели при None unified_engine"""
        from obelisk.core.model_testing import ModelTester
        
        tester = ModelTester(None)
        assert tester.is_model_loaded() is False
    
    @pytest.mark.unit
    def test_get_model_info_none(self):
        """Тест получения информации о модели при None"""
        from obelisk.core.model_testing import ModelTester
        
        tester = ModelTester(None)
        info = tester.get_model_info()
        
        assert isinstance(info, dict)
        assert info["loaded"] is False
        assert info["count"] == 0
        assert info["device"] == "unknown"
        assert isinstance(info["names"], list)
        assert len(info["names"]) == 0
    
    @pytest.mark.unit
    def test_create_test_frame(self):
        """Тест создания тестового кадра"""
        from obelisk.core.model_testing import ModelTester
        
        tester = ModelTester(None)
        frame = tester._create_test_frame()
        
        assert frame is not None
        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)
        assert frame.dtype == np.uint8
    
    @pytest.mark.unit
    def test_create_test_frame_custom_size(self):
        """Тест создания тестового кадра с кастомным размером"""
        from obelisk.core.model_testing import ModelTester
        
        tester = ModelTester(None)
        frame = tester._create_test_frame(width=320, height=240)
        
        assert frame.shape == (240, 320, 3)
        assert frame.dtype == np.uint8
    
    @pytest.mark.unit
    def test_get_test_summary_empty(self):
        """Тест получения сводки тестов при пустых результатах"""
        from obelisk.core.model_testing import ModelTester
        
        tester = ModelTester(None)
        summary = tester.get_test_summary()
        
        assert isinstance(summary, str)
        assert "Тесты не выполнялись" in summary


# ============================================================================
# ГРУППА 2: ТЕСТЫ С MOCK ENGINE (без реального unified_engine)
# ============================================================================

class TestModelTesterWithMock:
    """Тесты ModelTester с mock unified_engine - без зависаний"""
    
    @pytest.mark.unit
    def test_is_model_loaded_with_mock_engine_no_model_engine(self):
        """Тест проверки модели с mock engine без model_engine"""
        from obelisk.core.model_testing import ModelTester
        
        class MockEngine:
            pass
        
        mock_engine = MockEngine()
        tester = ModelTester(mock_engine)
        
        assert tester.is_model_loaded() is False
    
    @pytest.mark.unit
    def test_is_model_loaded_with_mock_engine_empty_models(self):
        """Тест проверки модели с mock engine с пустыми моделями"""
        from obelisk.core.model_testing import ModelTester
        
        class MockModelEngine:
            def __init__(self):
                self.models = {}
        
        class MockEngine:
            def __init__(self):
                self.model_engine = MockModelEngine()
        
        mock_engine = MockEngine()
        tester = ModelTester(mock_engine)
        
        assert tester.is_model_loaded() is False
    
    @pytest.mark.unit
    def test_is_model_loaded_with_mock_engine_with_models(self):
        """Тест проверки модели с mock engine с моделями"""
        from obelisk.core.model_testing import ModelTester
        
        class MockModelEngine:
            def __init__(self):
                self.models = {"primary": "mock_model"}
        
        class MockEngine:
            def __init__(self):
                self.model_engine = MockModelEngine()
        
        mock_engine = MockEngine()
        tester = ModelTester(mock_engine)
        
        assert tester.is_model_loaded() is True
    
    @pytest.mark.unit
    def test_get_model_info_with_mock_engine(self):
        """Тест получения информации о модели с mock engine"""
        from obelisk.core.model_testing import ModelTester
        
        class MockModelEngine:
            def __init__(self):
                self.models = {"primary": "mock_model", "secondary": "mock_model2"}
                self.device = "cuda:0"
        
        class MockEngine:
            def __init__(self):
                self.model_engine = MockModelEngine()
        
        mock_engine = MockEngine()
        tester = ModelTester(mock_engine)
        info = tester.get_model_info()
        
        assert isinstance(info, dict)
        assert info["loaded"] is True
        assert info["count"] == 2
        assert info["device"] == "cuda:0"
        assert len(info["names"]) == 2
        assert "primary" in info["names"]
        assert "secondary" in info["names"]


# ============================================================================
# ГРУППА 3: ТЕСТЫ БЕЗОПАСНОСТИ (проверка граничных случаев)
# ============================================================================

class TestModelTesterSafety:
    """Тесты безопасности и граничных случаев"""
    
    @pytest.mark.unit
    def test_is_model_loaded_without_model_engine(self):
        """Тест проверки модели без model_engine"""
        from obelisk.core.model_testing import ModelTester
        
        class MockEngine:
            pass
        
        mock_engine = MockEngine()
        tester = ModelTester(mock_engine)
        
        assert tester.is_model_loaded() is False
    
    @pytest.mark.unit
    def test_is_model_loaded_with_none_model_engine(self):
        """Тест проверки модели с None model_engine"""
        from obelisk.core.model_testing import ModelTester
        
        class MockEngine:
            def __init__(self):
                self.model_engine = None
        
        mock_engine = MockEngine()
        tester = ModelTester(mock_engine)
        
        assert tester.is_model_loaded() is False
    
    @pytest.mark.unit
    def test_get_model_info_with_empty_models(self):
        """Тест получения информации с пустыми моделями"""
        from obelisk.core.model_testing import ModelTester
        
        class MockModelEngine:
            def __init__(self):
                self.models = {}
                self.device = "cpu"
        
        class MockEngine:
            def __init__(self):
                self.model_engine = MockModelEngine()
        
        mock_engine = MockEngine()
        tester = ModelTester(mock_engine)
        info = tester.get_model_info()
        
        assert info["loaded"] is False
        assert info["count"] == 0
        # Когда модели пустые, device должен быть "unknown" (модель не загружена)
        assert info["device"] == "unknown"
    
    @pytest.mark.unit
    def test_get_model_info_without_device(self):
        """Тест получения информации без device"""
        from obelisk.core.model_testing import ModelTester
        
        class MockModelEngine:
            def __init__(self):
                self.models = {"primary": "mock_model"}
                # Нет device
        
        class MockEngine:
            def __init__(self):
                self.model_engine = MockModelEngine()
        
        mock_engine = MockEngine()
        tester = ModelTester(mock_engine)
        info = tester.get_model_info()
        
        assert info["loaded"] is True
        assert info["device"] == "unknown"  # Должен быть unknown если нет device
