"""
Полевая архитектура роя (Field-Based Swarm Architecture)

Реализация децентрализованной координации на основе
динамического поля эффективности и градиентной миграции задач.

Архитектура SwarmOS:
- SwarmKernel    — ядро, обновляющее поля диффузии
- NodeRuntime    — поддержка локального состояния узлов
- FieldScheduler — миграция задач по градиентам потенциала
- FieldComm      — обмен состоянием между соседями через MQTT
"""

from obelisk.swarm.field_node import FieldNode
from obelisk.swarm.efficiency_field import EfficiencyField
from obelisk.swarm.swarm_kernel import SwarmKernel
from obelisk.swarm.field_scheduler import FieldScheduler
from obelisk.swarm.field_communication import FieldCommunication

__all__ = [
    "FieldNode",
    "EfficiencyField",
    "SwarmKernel",
    "FieldScheduler",
    "FieldCommunication",
]
