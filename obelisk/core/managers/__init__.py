"""
Менеджеры ЭкоНет
"""

from obelisk.core.managers.gpu_manager import get_gpu_manager, GPUMemoryManager
from obelisk.core.managers.gpu_test_manager import GPUTestManager, get_test_gpu_manager

__all__ = ['get_gpu_manager', 'GPUMemoryManager', 'GPUTestManager', 'get_test_gpu_manager']
