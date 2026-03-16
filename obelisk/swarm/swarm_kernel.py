"""
SwarmKernel — ядро операционной системы роя (SwarmOS).

Оркестрирует цикл:
    1. Измерить локальное состояние          (Node Runtime)
    2. Вычислить источник эффективности      (Field)
    3. Выполнить диффузию поля               (EfficiencyField.step)
    4. Запланировать агентов / задачи         (FieldScheduler)
    5. Обновить маршрутизацию / коммуникацию (FieldCommunication)

Может работать как асинхронный фоновый цикл.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

from obelisk.swarm.field_node import FieldNode
from obelisk.swarm.efficiency_field import EfficiencyField

logger = logging.getLogger(__name__)


class KernelState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class SwarmKernel:
    """
    Ядро SwarmOS.

    Управляет жизненным циклом полевой архитектуры:
    создание узлов, диффузия, планирование, диагностика.
    """

    def __init__(self, config: Optional[Dict] = None):
        cfg = config or {}
        swarm_cfg = cfg.get("swarm_field", {})

        self.field = EfficiencyField(
            diffusion_coeff=swarm_cfg.get("diffusion_coeff", 0.1),
            decay_factor=swarm_cfg.get("decay_factor", 0.01),
            mobility_coeff=swarm_cfg.get("mobility_coeff", 0.05),
            noise_scale=swarm_cfg.get("noise_scale", 0.001),
        )

        self._alpha = swarm_cfg.get("alpha", 0.4)
        self._beta = swarm_cfg.get("beta", 0.4)
        self._gamma = swarm_cfg.get("gamma", 0.2)

        self._tick_interval: float = swarm_cfg.get("tick_interval", 1.0)
        self._state = KernelState.STOPPED
        self._loop_task: Optional[asyncio.Task] = None

        # Обработчики пост-тика (field_scheduler, field_comm, и т.д.)
        self._post_tick_hooks: List[Callable] = []

        # Статистика
        self._total_ticks = 0
        self._uptime_start: Optional[float] = None

        logger.info("SwarmKernel initialized (D=%.3f λ=%.3f k=%.3f interval=%.1fs)",
                     self.field.D, self.field.lam, self.field.k, self._tick_interval)

    # ------------------------------------------------------------------
    # Управление узлами
    # ------------------------------------------------------------------

    def create_node(self, node_id: str, **kwargs) -> FieldNode:
        """Создать и зарегистрировать узел."""
        node = FieldNode(
            node_id,
            alpha=kwargs.get("alpha", self._alpha),
            beta=kwargs.get("beta", self._beta),
            gamma=kwargs.get("gamma", self._gamma),
        )
        for key in ("resources", "compute", "bandwidth", "tasks", "source"):
            if key in kwargs:
                setattr(node, key, kwargs[key])
        if kwargs.get("metadata"):
            node.metadata.update(kwargs["metadata"])

        self.field.register_node(node)
        return node

    def remove_node(self, node_id: str):
        self.field.unregister_node(node_id)

    def get_node(self, node_id: str) -> Optional[FieldNode]:
        return self.field.nodes.get(node_id)

    def connect_nodes(self, id_a: str, id_b: str):
        """Установить соседство."""
        a = self.field.nodes.get(id_a)
        b = self.field.nodes.get(id_b)
        if a and b:
            a.add_neighbor(b)

    def build_full_mesh(self):
        """Полносвязная топология (для небольших кластеров)."""
        ids = list(self.field.nodes.keys())
        for i, a_id in enumerate(ids):
            for b_id in ids[i + 1:]:
                self.connect_nodes(a_id, b_id)

    def build_ring(self):
        """Кольцевая топология."""
        ids = list(self.field.nodes.keys())
        for i in range(len(ids)):
            self.connect_nodes(ids[i], ids[(i + 1) % len(ids)])

    # ------------------------------------------------------------------
    # Хуки
    # ------------------------------------------------------------------

    def add_post_tick_hook(self, hook: Callable):
        """Добавить обработчик, вызываемый после каждого тика."""
        self._post_tick_hooks.append(hook)

    # ------------------------------------------------------------------
    # Жизненный цикл
    # ------------------------------------------------------------------

    async def start(self):
        """Запустить фоновый цикл ядра."""
        if self._state == KernelState.RUNNING:
            logger.warning("SwarmKernel already running")
            return

        self._state = KernelState.STARTING
        self._uptime_start = time.time()
        self._loop_task = asyncio.create_task(self._kernel_loop())
        self._state = KernelState.RUNNING
        logger.info("SwarmKernel started")

    async def stop(self):
        """Остановить ядро."""
        self._state = KernelState.STOPPED
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        logger.info("SwarmKernel stopped (total ticks: %d)", self._total_ticks)

    def pause(self):
        self._state = KernelState.PAUSED

    def resume(self):
        if self._state == KernelState.PAUSED:
            self._state = KernelState.RUNNING

    async def _kernel_loop(self):
        """Главный цикл ядра."""
        while self._state in (KernelState.RUNNING, KernelState.PAUSED):
            try:
                if self._state == KernelState.RUNNING:
                    stats = self._do_tick()
                    await self._run_post_tick_hooks(stats)

                await asyncio.sleep(self._tick_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("SwarmKernel tick error: %s", e, exc_info=True)
                self._state = KernelState.ERROR
                await asyncio.sleep(5)
                self._state = KernelState.RUNNING

    def _do_tick(self) -> Dict[str, Any]:
        """Один тик ядра (синхронный)."""
        stats = self.field.step()
        self._total_ticks += 1
        return stats

    async def _run_post_tick_hooks(self, stats: Dict[str, Any]):
        for hook in self._post_tick_hooks:
            try:
                result = hook(stats)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error("Post-tick hook error: %s", e)

    # ------------------------------------------------------------------
    # Одноразовый тик (для тестирования или ручного управления)
    # ------------------------------------------------------------------

    def tick(self) -> Dict[str, Any]:
        """Выполнить один тик без запуска цикла."""
        return self._do_tick()

    # ------------------------------------------------------------------
    # Диагностика
    # ------------------------------------------------------------------

    @property
    def state(self) -> KernelState:
        return self._state

    def diagnostics(self) -> Dict[str, Any]:
        uptime = time.time() - self._uptime_start if self._uptime_start else 0
        return {
            "state": self._state.value,
            "total_ticks": self._total_ticks,
            "uptime_seconds": round(uptime, 1),
            "tick_interval": self._tick_interval,
            "hooks": len(self._post_tick_hooks),
            "field": self.field.field_stats(),
        }

    def get_node_states(self) -> Dict[str, Dict]:
        """Состояние всех узлов."""
        return {nid: node.to_dict() for nid, node in self.field.nodes.items()}
