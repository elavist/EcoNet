"""
FieldNode — узел в полевой архитектуре роя.

Каждый узел поддерживает вектор состояния:
    E_i  — эффективность (вычисляется из R, C, B)
    R_i  — ресурсы (память, энергия)
    C_i  — вычислительная мощность
    B_i  — пропускная способность сети
    T_i  — плотность задач
    Φ_i  — потенциал нагрузки  (T_i − R_i)

Узел хранит список соседей и историю состояния для анализа трендов.
"""

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import deque

logger = logging.getLogger(__name__)


@dataclass
class NodeState:
    """Снимок состояния узла в момент времени *t*."""
    timestamp: float
    efficiency: float
    resources: float
    compute: float
    bandwidth: float
    tasks: float
    potential: float


class FieldNode:
    """
    Один узел в распределённой полевой сети.

    Поддерживает локальное состояние, список соседей и историю.
    Вычисления O(k) на каждом тике, где k — степень узла.
    """

    def __init__(
        self,
        node_id: str,
        *,
        alpha: float = 0.4,
        beta: float = 0.4,
        gamma: float = 0.2,
        history_size: int = 500,
    ):
        self.node_id = node_id

        # Весовые коэффициенты поля эффективности
        assert math.isclose(alpha + beta + gamma, 1.0, rel_tol=1e-6), \
            "α + β + γ must equal 1"
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma

        # Вектор состояния
        self._resources: float = 1.0
        self._compute: float = 1.0
        self._bandwidth: float = 1.0
        self._tasks: float = 0.0
        self._efficiency: float = 0.0
        self._potential: float = 0.0
        self._source: float = 0.0  # S_i — локальный источник

        # Соседи: node_id -> FieldNode (или удалённый прокси)
        self.neighbors: Dict[str, "FieldNode"] = {}

        # Метаданные
        self.metadata: Dict[str, Any] = {}
        self._history: deque[NodeState] = deque(maxlen=history_size)
        self._created_at = time.time()
        self._tick_count = 0

        self._recompute_efficiency()
        logger.debug("FieldNode '%s' created (α=%.2f β=%.2f γ=%.2f)",
                      node_id, alpha, beta, gamma)

    # ------------------------------------------------------------------
    # Свойства с автоматическим пересчётом
    # ------------------------------------------------------------------

    @property
    def resources(self) -> float:
        return self._resources

    @resources.setter
    def resources(self, value: float):
        self._resources = max(0.0, value)
        self._recompute_efficiency()

    @property
    def compute(self) -> float:
        return self._compute

    @compute.setter
    def compute(self, value: float):
        self._compute = max(0.0, value)
        self._recompute_efficiency()

    @property
    def bandwidth(self) -> float:
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, value: float):
        self._bandwidth = max(0.0, value)
        self._recompute_efficiency()

    @property
    def tasks(self) -> float:
        return self._tasks

    @tasks.setter
    def tasks(self, value: float):
        self._tasks = max(0.0, value)
        self._recompute_potential()

    @property
    def efficiency(self) -> float:
        return self._efficiency

    @property
    def potential(self) -> float:
        return self._potential

    @property
    def source(self) -> float:
        return self._source

    @source.setter
    def source(self, value: float):
        self._source = value

    # ------------------------------------------------------------------
    # Вычисления
    # ------------------------------------------------------------------

    def _recompute_efficiency(self):
        """E_i = αR_i + βC_i + γB_i"""
        self._efficiency = (
            self.alpha * self._resources
            + self.beta * self._compute
            + self.gamma * self._bandwidth
        )
        self._recompute_potential()

    def _recompute_potential(self):
        """Φ_i = T_i − R_i  (перегруз > 0, недогруз < 0)"""
        self._potential = self._tasks - self._resources

    # ------------------------------------------------------------------
    # Связи
    # ------------------------------------------------------------------

    def add_neighbor(self, neighbor: "FieldNode"):
        """Двусторонняя связь с соседом."""
        if neighbor.node_id == self.node_id:
            return
        self.neighbors[neighbor.node_id] = neighbor
        if self.node_id not in neighbor.neighbors:
            neighbor.neighbors[self.node_id] = self

    def remove_neighbor(self, node_id: str):
        neighbor = self.neighbors.pop(node_id, None)
        if neighbor and self.node_id in neighbor.neighbors:
            del neighbor.neighbors[self.node_id]

    @property
    def degree(self) -> int:
        return len(self.neighbors)

    # ------------------------------------------------------------------
    # Градиент поля эффективности
    # ------------------------------------------------------------------

    def efficiency_gradient(self) -> Dict[str, float]:
        """
        ∇E по направлению к каждому соседу.
        Положительный градиент → сосед эффективнее.
        """
        return {
            nid: n.efficiency - self._efficiency
            for nid, n in self.neighbors.items()
        }

    def potential_gradient(self) -> Dict[str, float]:
        """
        ∇Φ по направлению к каждому соседу.
        Задачи текут в сторону отрицательного потенциала.
        """
        return {
            nid: n.potential - self._potential
            for nid, n in self.neighbors.items()
        }

    def best_efficiency_neighbor(self) -> Optional[str]:
        """Сосед с наивысшей эффективностью."""
        if not self.neighbors:
            return None
        return max(self.neighbors, key=lambda nid: self.neighbors[nid].efficiency)

    # ------------------------------------------------------------------
    # Снимки и история
    # ------------------------------------------------------------------

    def snapshot(self) -> NodeState:
        """Текущий снимок состояния."""
        return NodeState(
            timestamp=time.time(),
            efficiency=self._efficiency,
            resources=self._resources,
            compute=self._compute,
            bandwidth=self._bandwidth,
            tasks=self._tasks,
            potential=self._potential,
        )

    def record_history(self):
        """Сохранить текущее состояние в историю."""
        self._history.append(self.snapshot())

    @property
    def history(self) -> List[NodeState]:
        return list(self._history)

    # ------------------------------------------------------------------
    # Сериализация (для обмена по сети)
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "efficiency": round(self._efficiency, 6),
            "resources": round(self._resources, 6),
            "compute": round(self._compute, 6),
            "bandwidth": round(self._bandwidth, 6),
            "tasks": round(self._tasks, 6),
            "potential": round(self._potential, 6),
            "source": round(self._source, 6),
            "degree": self.degree,
            "tick": self._tick_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], **kwargs) -> "FieldNode":
        node = cls(data["node_id"], **kwargs)
        node._resources = data.get("resources", 1.0)
        node._compute = data.get("compute", 1.0)
        node._bandwidth = data.get("bandwidth", 1.0)
        node._tasks = data.get("tasks", 0.0)
        node._source = data.get("source", 0.0)
        node._tick_count = data.get("tick", 0)
        node.metadata = data.get("metadata", {})
        node._recompute_efficiency()
        return node

    def __repr__(self):
        return (
            f"FieldNode({self.node_id!r}, E={self._efficiency:.3f}, "
            f"Φ={self._potential:.3f}, deg={self.degree})"
        )
