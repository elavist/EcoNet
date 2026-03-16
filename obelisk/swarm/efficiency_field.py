"""
EfficiencyField — движок диффузии поля эффективности.

Реализует уравнение:
    E_i(t+1) = E_i(t) + D·Σ_{j∈N(i)}(E_j − E_i) + S_i − λ·E_i

и уравнение потока задач:
    J_ij = −k·(Φ_j − Φ_i)

Обеспечивает:
    • распространение информации об эффективности через диффузию
    • автоматическую балансировку нагрузки через потоки задач
    • стабильность при D > 0, λ > 0 (все возмущения затухают)
    • масштабирование O(N·k) на тик, где k — средняя степень узла

Энергия системы (должна убывать):
    H = Σ_i (T_i − R_i)²
"""

import logging
import math
import time
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

from obelisk.swarm.field_node import FieldNode

logger = logging.getLogger(__name__)


class EfficiencyField:
    """
    Распределённое скалярное поле эффективности.

    Ядро полевой архитектуры: обновляет поле каждый тик,
    вычисляет потоки задач и отслеживает энергию системы.
    """

    def __init__(
        self,
        *,
        diffusion_coeff: float = 0.1,
        decay_factor: float = 0.01,
        mobility_coeff: float = 0.05,
        noise_scale: float = 0.001,
    ):
        """
        Args:
            diffusion_coeff: D — коэффициент диффузии поля
            decay_factor:    λ — затухание устаревшей информации
            mobility_coeff:  k — скорость миграции задач
            noise_scale:     σ — амплитуда шума для стохастической разведки
        """
        self.D = diffusion_coeff
        self.lam = decay_factor
        self.k = mobility_coeff
        self.noise_scale = noise_scale

        self._nodes: Dict[str, FieldNode] = {}
        self._tick: int = 0
        self._energy_history: List[float] = []

        # Кэш потоков задач последнего тика
        self._last_flows: Dict[Tuple[str, str], float] = {}

    # ------------------------------------------------------------------
    # Регистрация узлов
    # ------------------------------------------------------------------

    def register_node(self, node: FieldNode):
        self._nodes[node.node_id] = node
        logger.info("EfficiencyField: node '%s' registered (total: %d)",
                     node.node_id, len(self._nodes))

    def unregister_node(self, node_id: str):
        node = self._nodes.pop(node_id, None)
        if node:
            for nid in list(node.neighbors):
                node.remove_neighbor(nid)

    @property
    def nodes(self) -> Dict[str, FieldNode]:
        return self._nodes

    @property
    def tick(self) -> int:
        return self._tick

    # ------------------------------------------------------------------
    # Основной цикл: один тик
    # ------------------------------------------------------------------

    def step(self) -> Dict[str, Any]:
        """
        Выполнить один тик обновления поля.

        Алгоритм (каждый узел):
            1. Вычислить локальный источник S_i
            2. Обменяться E_i с соседями (уже хранятся в neighbors)
            3. Обновить E_i по уравнению диффузии
            4. Вычислить потоки задач J_ij
            5. Обновить T_i с учётом потоков
            6. Записать историю

        Returns:
            Словарь со статистикой тика.
        """
        t0 = time.perf_counter()
        self._tick += 1

        deltas_e: Dict[str, float] = {}
        flows: Dict[Tuple[str, str], float] = {}

        # ---- Фаза 1: вычислить дельты эффективности ----
        for nid, node in self._nodes.items():
            diffusion_sum = 0.0
            for neighbor in node.neighbors.values():
                diffusion_sum += neighbor.efficiency - node.efficiency

            delta = (
                self.D * diffusion_sum
                + node.source
                - self.lam * node.efficiency
            )

            if self.noise_scale > 0:
                import random
                delta += random.gauss(0, self.noise_scale)

            deltas_e[nid] = delta

        # ---- Фаза 2: применить дельты (синхронное обновление) ----
        for nid, node in self._nodes.items():
            new_e = node.efficiency + deltas_e[nid]
            combined = node.alpha + node.beta + node.gamma
            if combined > 0:
                node._resources = max(0.0, node._resources + deltas_e[nid] * (node.alpha / combined))
                node._compute = max(0.0, node._compute + deltas_e[nid] * (node.beta / combined))
                node._bandwidth = max(0.0, node._bandwidth + deltas_e[nid] * (node.gamma / combined))
            node._recompute_efficiency()

        # ---- Фаза 3: потоки задач ----
        task_deltas: Dict[str, float] = defaultdict(float)

        for nid, node in self._nodes.items():
            for neighbor_id, neighbor in node.neighbors.items():
                edge = (nid, neighbor_id)
                reverse = (neighbor_id, nid)
                if reverse in flows:
                    continue

                flow = -self.k * (neighbor.potential - node.potential)
                if flow > 0:
                    flow = min(flow, node.tasks)
                else:
                    flow = max(flow, -neighbor.tasks)
                flows[edge] = flow

                task_deltas[nid] -= flow
                task_deltas[neighbor_id] += flow

        for nid, delta in task_deltas.items():
            if nid in self._nodes:
                self._nodes[nid].tasks = self._nodes[nid].tasks + delta

        self._last_flows = flows

        # ---- Фаза 4: записать историю ----
        for node in self._nodes.values():
            node._tick_count = self._tick
            node.record_history()

        energy = self.system_energy()
        self._energy_history.append(energy)

        dt = time.perf_counter() - t0

        stats = {
            "tick": self._tick,
            "nodes": len(self._nodes),
            "energy": round(energy, 6),
            "flows_count": len(flows),
            "dt_ms": round(dt * 1000, 2),
        }

        if self._tick % 50 == 0:
            logger.info("EfficiencyField tick %d: energy=%.4f nodes=%d dt=%.1fms",
                         self._tick, energy, len(self._nodes), dt * 1000)

        return stats

    # ------------------------------------------------------------------
    # Энергия системы:  H = Σ_i (T_i − R_i)²
    # ------------------------------------------------------------------

    def system_energy(self) -> float:
        """Глобальная энергия дисбаланса — должна убывать."""
        return sum(node.potential ** 2 for node in self._nodes.values())

    def energy_trend(self, window: int = 10) -> Optional[float]:
        """
        Средний тренд энергии за последние *window* тиков.
        Отрицательное значение → система стабилизируется.
        """
        h = self._energy_history
        if len(h) < window + 1:
            return None
        recent = h[-window:]
        return (recent[-1] - recent[0]) / window

    # ------------------------------------------------------------------
    # Критический параметр и фазовое состояние: μ = ηD
    # ------------------------------------------------------------------

    def phase_parameter(self, eta: float = 1.0) -> float:
        """μ = ηD  — параметр фазового перехода роя."""
        return eta * self.D

    def phase_state(self, eta: float = 1.0, mu_critical: float = 0.05) -> str:
        """
        Текущий режим роя:
            slow_exploration  — μ < μ_c
            self_organization — μ ≈ μ_c
            rapid_convergence — μ > μ_c
        """
        mu = self.phase_parameter(eta)
        if mu < mu_critical * 0.8:
            return "slow_exploration"
        elif mu < mu_critical * 1.2:
            return "self_organization"
        return "rapid_convergence"

    # ------------------------------------------------------------------
    # Аналитика
    # ------------------------------------------------------------------

    def field_stats(self) -> Dict[str, Any]:
        """Статистика поля."""
        if not self._nodes:
            return {"nodes": 0}

        efficiencies = [n.efficiency for n in self._nodes.values()]
        potentials = [n.potential for n in self._nodes.values()]
        tasks_list = [n.tasks for n in self._nodes.values()]

        return {
            "tick": self._tick,
            "nodes": len(self._nodes),
            "energy": round(self.system_energy(), 6),
            "energy_trend": self.energy_trend(),
            "phase": self.phase_state(),
            "efficiency": {
                "min": round(min(efficiencies), 4),
                "max": round(max(efficiencies), 4),
                "mean": round(sum(efficiencies) / len(efficiencies), 4),
                "spread": round(max(efficiencies) - min(efficiencies), 4),
            },
            "potential": {
                "min": round(min(potentials), 4),
                "max": round(max(potentials), 4),
                "mean": round(sum(potentials) / len(potentials), 4),
            },
            "tasks": {
                "total": round(sum(tasks_list), 4),
                "max": round(max(tasks_list), 4),
            },
            "flows_last_tick": len(self._last_flows),
            "params": {
                "D": self.D,
                "lambda": self.lam,
                "k": self.k,
                "noise": self.noise_scale,
            },
        }

    def node_ranking(self, key: str = "efficiency", descending: bool = True) -> List[str]:
        """Ранжирование узлов по указанному показателю."""
        getter = {
            "efficiency": lambda n: n.efficiency,
            "potential": lambda n: n.potential,
            "tasks": lambda n: n.tasks,
            "resources": lambda n: n.resources,
        }.get(key, lambda n: n.efficiency)

        return [
            nid for nid, _ in sorted(
                self._nodes.items(),
                key=lambda pair: getter(pair[1]),
                reverse=descending,
            )
        ]

    def get_flow(self, src: str, dst: str) -> float:
        """Поток задач между двумя узлами на последнем тике."""
        return self._last_flows.get((src, dst), -self._last_flows.get((dst, src), 0.0))
