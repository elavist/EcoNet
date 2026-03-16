"""
FieldScheduler — планировщик задач на основе градиентов поля.

Задачи мигрируют к узлам с наибольшей эффективностью
и наименьшим потенциалом нагрузки (Φ_i < 0 → узел недогружен).

Реализует:
    • Gradient-driven task assignment: задача → узел с max(E) и min(Φ)
    • Автоматическую миграцию задач при изменении поля
    • Потоковую балансировку: J_ij = −k(Φ_j − Φ_i)
    • Приоритизацию по типу задачи
"""

import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

from obelisk.swarm.field_node import FieldNode
from obelisk.swarm.efficiency_field import EfficiencyField

logger = logging.getLogger(__name__)


class TaskState(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    MIGRATING = "migrating"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class FieldTask:
    """Задача в полевом планировщике."""
    task_id: str
    task_type: str = "collect"
    priority: float = 1.0
    assigned_node: Optional[str] = None
    state: TaskState = TaskState.PENDING
    created_at: float = field(default_factory=time.time)
    assigned_at: Optional[float] = None
    completed_at: Optional[float] = None
    migration_count: int = 0
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "priority": self.priority,
            "assigned_node": self.assigned_node,
            "state": self.state.value,
            "created_at": self.created_at,
            "assigned_at": self.assigned_at,
            "completed_at": self.completed_at,
            "migration_count": self.migration_count,
            "payload": self.payload,
        }


class FieldScheduler:
    """
    Планировщик задач, управляемый полем эффективности.

    Вместо центрального назначения, задачи «стекают» к узлам
    с наибольшей привлекательностью через градиенты поля.
    """

    def __init__(
        self,
        efficiency_field: EfficiencyField,
        *,
        migration_threshold: float = 0.15,
        max_migrations: int = 5,
    ):
        """
        Args:
            efficiency_field: ссылка на поле эффективности
            migration_threshold: минимальный перепад Φ для миграции
            max_migrations: максимальное число миграций одной задачи
        """
        self.field = efficiency_field
        self.migration_threshold = migration_threshold
        self.max_migrations = max_migrations

        self._tasks: Dict[str, FieldTask] = {}
        self._node_tasks: Dict[str, List[str]] = defaultdict(list)

        # Статистика
        self._total_assigned = 0
        self._total_migrations = 0
        self._total_completed = 0

    # ------------------------------------------------------------------
    # Управление задачами
    # ------------------------------------------------------------------

    def submit_task(self, task_id: str, **kwargs) -> FieldTask:
        """Добавить задачу в планировщик."""
        task = FieldTask(task_id=task_id, **kwargs)
        self._tasks[task_id] = task
        logger.debug("FieldScheduler: task '%s' submitted (type=%s, priority=%.1f)",
                      task_id, task.task_type, task.priority)
        return task

    def complete_task(self, task_id: str):
        """Пометить задачу как выполненную."""
        task = self._tasks.get(task_id)
        if not task:
            return
        task.state = TaskState.COMPLETED
        task.completed_at = time.time()
        if task.assigned_node:
            self._remove_from_node(task.assigned_node, task_id)
            node = self.field.nodes.get(task.assigned_node)
            if node:
                node.tasks = max(0, node.tasks - task.priority)
        self._total_completed += 1

    def fail_task(self, task_id: str):
        """Пометить задачу как провалившуюся, вернуть в очередь."""
        task = self._tasks.get(task_id)
        if not task:
            return
        if task.assigned_node:
            self._remove_from_node(task.assigned_node, task_id)
            node = self.field.nodes.get(task.assigned_node)
            if node:
                node.tasks = max(0, node.tasks - task.priority)
        task.state = TaskState.PENDING
        task.assigned_node = None

    def cancel_task(self, task_id: str):
        task = self._tasks.pop(task_id, None)
        if task and task.assigned_node:
            self._remove_from_node(task.assigned_node, task_id)

    # ------------------------------------------------------------------
    # Назначение (вызывается как post-tick hook ядра)
    # ------------------------------------------------------------------

    def schedule(self, _tick_stats: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Один раунд планирования.

        1. Назначить ожидающие задачи на оптимальные узлы
        2. Мигрировать уже назначенные задачи при изменении поля

        Returns:
            Статистика раунда.
        """
        assigned = self._assign_pending()
        migrated = self._migrate_active()

        return {
            "assigned": assigned,
            "migrated": migrated,
            "pending": sum(1 for t in self._tasks.values() if t.state == TaskState.PENDING),
            "active": sum(1 for t in self._tasks.values() if t.state in (TaskState.ASSIGNED, TaskState.EXECUTING)),
            "completed": self._total_completed,
        }

    def _assign_pending(self) -> int:
        """Назначить ожидающие задачи на узлы с наилучшим потенциалом."""
        count = 0
        pending = [
            t for t in self._tasks.values()
            if t.state == TaskState.PENDING
        ]
        pending.sort(key=lambda t: t.priority, reverse=True)

        for task in pending:
            best_node = self._find_best_node(task)
            if best_node:
                self._assign_to_node(task, best_node)
                count += 1

        return count

    def _migrate_active(self) -> int:
        """Мигрировать задачи, если сосед значительно лучше текущего узла."""
        count = 0
        active = [
            t for t in self._tasks.values()
            if t.state == TaskState.ASSIGNED and t.migration_count < self.max_migrations
        ]

        for task in active:
            if not task.assigned_node:
                continue
            current = self.field.nodes.get(task.assigned_node)
            if not current:
                continue

            for nid, neighbor in current.neighbors.items():
                phi_diff = current.potential - neighbor.potential
                if phi_diff > self.migration_threshold:
                    self._remove_from_node(task.assigned_node, task.task_id)
                    current.tasks = max(0, current.tasks - task.priority)
                    self._assign_to_node(task, nid)
                    task.migration_count += 1
                    self._total_migrations += 1
                    count += 1
                    break

        return count

    # ------------------------------------------------------------------
    # Выбор узла
    # ------------------------------------------------------------------

    def _find_best_node(self, task: FieldTask) -> Optional[str]:
        """
        Выбрать узел с наибольшей эффективностью и наименьшим потенциалом.

        Скор = E_i − w·Φ_i  (чем выше E и ниже Φ, тем лучше)
        """
        if not self.field.nodes:
            return None

        best_id = None
        best_score = float("-inf")

        for nid, node in self.field.nodes.items():
            score = node.efficiency - 0.5 * node.potential
            if score > best_score:
                best_score = score
                best_id = nid

        return best_id

    def _assign_to_node(self, task: FieldTask, node_id: str):
        task.assigned_node = node_id
        task.assigned_at = time.time()
        task.state = TaskState.ASSIGNED
        self._node_tasks[node_id].append(task.task_id)

        node = self.field.nodes.get(node_id)
        if node:
            node.tasks += task.priority

        self._total_assigned += 1
        logger.debug("Task '%s' assigned to node '%s' (E=%.3f, Φ=%.3f)",
                      task.task_id, node_id,
                      node.efficiency if node else 0,
                      node.potential if node else 0)

    def _remove_from_node(self, node_id: str, task_id: str):
        tasks = self._node_tasks.get(node_id, [])
        if task_id in tasks:
            tasks.remove(task_id)

    # ------------------------------------------------------------------
    # Запросы
    # ------------------------------------------------------------------

    def get_task(self, task_id: str) -> Optional[FieldTask]:
        return self._tasks.get(task_id)

    def get_node_tasks(self, node_id: str) -> List[FieldTask]:
        task_ids = self._node_tasks.get(node_id, [])
        return [self._tasks[tid] for tid in task_ids if tid in self._tasks]

    def pending_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.state == TaskState.PENDING)

    def statistics(self) -> Dict[str, Any]:
        states = defaultdict(int)
        for t in self._tasks.values():
            states[t.state.value] += 1

        return {
            "total_tasks": len(self._tasks),
            "by_state": dict(states),
            "total_assigned": self._total_assigned,
            "total_migrations": self._total_migrations,
            "total_completed": self._total_completed,
            "migration_threshold": self.migration_threshold,
        }
