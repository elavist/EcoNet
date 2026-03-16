"""
Ядро ЭкоНет - универсальные движки и системы
"""

# Импорты из новой структуры с обратной совместимостью
from obelisk.core.engines import UnifiedEngine, ModelEngine, TestEngine
from obelisk.core.processors import ObjectTracker
from obelisk.core.managers import get_gpu_manager, GPUMemoryManager, GPUTestManager, get_test_gpu_manager

__all__ = [
    'UnifiedEngine', 
    'ModelEngine', 
    'TestEngine',
    'ObjectTracker',
    'get_gpu_manager',
    'GPUMemoryManager',
    'GPUTestManager',
    'get_test_gpu_manager'
]

