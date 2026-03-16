"""
FieldCommunication — слой коммуникации полевой архитектуры.

Мост между полевой моделью и MQTT-транспортом:
    • Периодическая публикация состояния узла в MQTT
    • Приём состояний соседей и обновление прокси-узлов
    • Интеграция удалённых роботов/edge-устройств в поле

MQTT-топики:
    swarm/field/{node_id}/state   — состояние узла (pub)
    swarm/field/+/state           — состояния соседей (sub)
    swarm/field/{node_id}/flow    — потоки задач (pub)
    swarm/field/announce          — объявление о входе/выходе узла
"""

import asyncio
import json
import logging
import time
from typing import Dict, Optional, Any, Callable

from obelisk.swarm.field_node import FieldNode

logger = logging.getLogger(__name__)

TOPIC_STATE = "swarm/field/{node_id}/state"
TOPIC_STATE_WILDCARD = "swarm/field/+/state"
TOPIC_FLOW = "swarm/field/{node_id}/flow"
TOPIC_ANNOUNCE = "swarm/field/announce"


class FieldCommunication:
    """
    Коммуникационный слой полевой архитектуры.

    Транслирует локальные состояния узлов в MQTT и обратно,
    создавая прокси-узлы для удалённых участников роя.
    """

    def __init__(
        self,
        mqtt_client,
        swarm_kernel,
        *,
        broadcast_interval: float = 2.0,
        stale_timeout: float = 30.0,
    ):
        """
        Args:
            mqtt_client: MQTTClient из obelisk.services
            swarm_kernel: SwarmKernel
            broadcast_interval: интервал публикации состояний (сек)
            stale_timeout: время, после которого узел считается недоступным
        """
        self._mqtt = mqtt_client
        self._kernel = swarm_kernel
        self._broadcast_interval = broadcast_interval
        self._stale_timeout = stale_timeout

        self._remote_timestamps: Dict[str, float] = {}
        self._running = False
        self._broadcast_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None

        self._local_node_ids: set = set()

        # Счётчики
        self._msgs_sent = 0
        self._msgs_received = 0

    # ------------------------------------------------------------------
    # Жизненный цикл
    # ------------------------------------------------------------------

    async def start(self):
        """Запустить слой коммуникации."""
        if self._running:
            return

        self._running = True

        if self._mqtt:
            self._mqtt.subscribe(TOPIC_STATE_WILDCARD, self._on_remote_state)
            self._mqtt.subscribe(TOPIC_ANNOUNCE, self._on_announce)

        self._broadcast_task = asyncio.create_task(self._broadcast_loop())
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

        # Объявить все локальные узлы
        await self._announce_all("join")

        logger.info("FieldCommunication started (interval=%.1fs, stale=%.0fs)",
                     self._broadcast_interval, self._stale_timeout)

    async def stop(self):
        """Остановить слой коммуникации."""
        self._running = False

        await self._announce_all("leave")

        for task in (self._broadcast_task, self._cleanup_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info("FieldCommunication stopped (sent=%d, received=%d)",
                     self._msgs_sent, self._msgs_received)

    # ------------------------------------------------------------------
    # Регистрация локальных узлов
    # ------------------------------------------------------------------

    def register_local_node(self, node_id: str):
        """Пометить узел как локальный (его состояние будет публиковаться)."""
        self._local_node_ids.add(node_id)

    def unregister_local_node(self, node_id: str):
        self._local_node_ids.discard(node_id)

    # ------------------------------------------------------------------
    # Публикация
    # ------------------------------------------------------------------

    async def _broadcast_loop(self):
        """Периодическая публикация состояний локальных узлов."""
        while self._running:
            try:
                await self._broadcast_states()
                await asyncio.sleep(self._broadcast_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("FieldCommunication broadcast error: %s", e)
                await asyncio.sleep(5)

    async def _broadcast_states(self):
        """Опубликовать состояния всех локальных узлов."""
        if not self._mqtt or not self._mqtt.is_connected():
            return

        for node_id in self._local_node_ids:
            node = self._kernel.get_node(node_id)
            if not node:
                continue

            topic = TOPIC_STATE.format(node_id=node_id)
            payload = node.to_dict()
            payload["_ts"] = time.time()
            payload["_neighbors"] = list(node.neighbors.keys())

            await self._mqtt.publish(topic, payload, qos=0)
            self._msgs_sent += 1

    async def _announce_all(self, action: str):
        """Объявить join/leave для всех локальных узлов."""
        if not self._mqtt or not self._mqtt.is_connected():
            return

        for node_id in self._local_node_ids:
            await self._mqtt.publish(TOPIC_ANNOUNCE, {
                "node_id": node_id,
                "action": action,
                "timestamp": time.time(),
            }, qos=1)

    # ------------------------------------------------------------------
    # Приём
    # ------------------------------------------------------------------

    def _on_remote_state(self, topic: str, payload: Dict):
        """Обработка состояния удалённого узла."""
        try:
            remote_id = payload.get("node_id")
            if not remote_id or remote_id in self._local_node_ids:
                return

            self._msgs_received += 1
            self._remote_timestamps[remote_id] = time.time()

            existing = self._kernel.get_node(remote_id)
            if existing:
                existing._resources = payload.get("resources", existing._resources)
                existing._compute = payload.get("compute", existing._compute)
                existing._bandwidth = payload.get("bandwidth", existing._bandwidth)
                existing._tasks = payload.get("tasks", existing._tasks)
                existing._source = payload.get("source", existing._source)
                existing._recompute_efficiency()
            else:
                node = self._kernel.create_node(
                    remote_id,
                    resources=payload.get("resources", 1.0),
                    compute=payload.get("compute", 1.0),
                    bandwidth=payload.get("bandwidth", 1.0),
                    tasks=payload.get("tasks", 0.0),
                    metadata={"remote": True},
                )

                remote_neighbors = payload.get("_neighbors", [])
                for nid in remote_neighbors:
                    if nid in self._kernel.field.nodes:
                        self._kernel.connect_nodes(remote_id, nid)

                for local_id in self._local_node_ids:
                    self._kernel.connect_nodes(remote_id, local_id)

                logger.info("FieldComm: remote node '%s' added to field", remote_id)

        except Exception as e:
            logger.error("FieldComm: error processing remote state: %s", e)

    def _on_announce(self, topic: str, payload: Dict):
        """Обработка объявления входа/выхода узла."""
        try:
            node_id = payload.get("node_id")
            action = payload.get("action")

            if not node_id or node_id in self._local_node_ids:
                return

            if action == "leave":
                self._kernel.remove_node(node_id)
                self._remote_timestamps.pop(node_id, None)
                logger.info("FieldComm: remote node '%s' left the swarm", node_id)

        except Exception as e:
            logger.error("FieldComm: error processing announce: %s", e)

    # ------------------------------------------------------------------
    # Очистка устаревших узлов
    # ------------------------------------------------------------------

    async def _cleanup_loop(self):
        """Удаление узлов, которые не обновлялись дольше stale_timeout."""
        while self._running:
            try:
                now = time.time()
                stale = [
                    nid for nid, ts in self._remote_timestamps.items()
                    if now - ts > self._stale_timeout
                ]
                for nid in stale:
                    self._kernel.remove_node(nid)
                    self._remote_timestamps.pop(nid, None)
                    logger.warning("FieldComm: node '%s' removed (stale)", nid)

                await asyncio.sleep(self._stale_timeout / 2)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("FieldComm cleanup error: %s", e)
                await asyncio.sleep(10)

    # ------------------------------------------------------------------
    # Публикация потоков задач
    # ------------------------------------------------------------------

    async def publish_task_flow(self, node_id: str, target_id: str, flow: float):
        """Опубликовать информацию о потоке задач."""
        if not self._mqtt or not self._mqtt.is_connected():
            return

        topic = TOPIC_FLOW.format(node_id=node_id)
        await self._mqtt.publish(topic, {
            "from": node_id,
            "to": target_id,
            "flow": round(flow, 6),
            "timestamp": time.time(),
        }, qos=0)

    # ------------------------------------------------------------------
    # Диагностика
    # ------------------------------------------------------------------

    def statistics(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "local_nodes": len(self._local_node_ids),
            "remote_nodes": len(self._remote_timestamps),
            "msgs_sent": self._msgs_sent,
            "msgs_received": self._msgs_received,
            "broadcast_interval": self._broadcast_interval,
            "stale_timeout": self._stale_timeout,
        }
