"""
Тесты полевой архитектуры роя (SwarmOS)

Покрывает:
  - FieldNode: состояние, градиенты, сериализация
  - EfficiencyField: диффузия, потоки задач, энергия
  - SwarmKernel: создание узлов, топологии, тики
  - FieldScheduler: назначение, миграция, завершение задач
  - MQTTClient._topic_matches: MQTT wildcard matching
"""

import pytest
import math
import time

from obelisk.swarm.field_node import FieldNode
from obelisk.swarm.efficiency_field import EfficiencyField
from obelisk.swarm.swarm_kernel import SwarmKernel, KernelState
from obelisk.swarm.field_scheduler import FieldScheduler, TaskState
from obelisk.services.mqtt_client import MQTTClient


# ======================================================================
# FieldNode
# ======================================================================

class TestFieldNode:

    def test_efficiency_formula(self):
        """E_i = αR_i + βC_i + γB_i"""
        node = FieldNode("n1", alpha=0.5, beta=0.3, gamma=0.2)
        node._resources = 2.0
        node._compute = 4.0
        node._bandwidth = 5.0
        node._recompute_efficiency()
        expected = 0.5 * 2.0 + 0.3 * 4.0 + 0.2 * 5.0
        assert math.isclose(node.efficiency, expected, rel_tol=1e-9)

    def test_potential_formula(self):
        """Φ_i = T_i − R_i"""
        node = FieldNode("n1")
        node._resources = 3.0
        node._tasks = 5.0
        node._recompute_potential()
        assert math.isclose(node.potential, 2.0)

    def test_neighbors_bidirectional(self):
        a = FieldNode("a")
        b = FieldNode("b")
        a.add_neighbor(b)
        assert "b" in a.neighbors
        assert "a" in b.neighbors
        assert a.degree == 1

    def test_remove_neighbor(self):
        a = FieldNode("a")
        b = FieldNode("b")
        a.add_neighbor(b)
        a.remove_neighbor("b")
        assert "b" not in a.neighbors
        assert "a" not in b.neighbors

    def test_self_neighbor_ignored(self):
        a = FieldNode("a")
        a.add_neighbor(a)
        assert a.degree == 0

    def test_efficiency_gradient(self):
        a = FieldNode("a")
        b = FieldNode("b")
        a.add_neighbor(b)
        b._resources = 10.0
        b._recompute_efficiency()
        grad = a.efficiency_gradient()
        assert grad["b"] == b.efficiency - a.efficiency

    def test_serialization_roundtrip(self):
        node = FieldNode("test", alpha=0.3, beta=0.5, gamma=0.2)
        node._resources = 2.5
        node._compute = 3.0
        node._bandwidth = 1.0
        node._tasks = 1.5
        node._recompute_efficiency()
        data = node.to_dict()

        restored = FieldNode.from_dict(data, alpha=0.3, beta=0.5, gamma=0.2)
        assert restored.node_id == "test"
        assert math.isclose(restored.efficiency, node.efficiency, rel_tol=1e-6)
        assert math.isclose(restored.potential, node.potential, rel_tol=1e-6)

    def test_alpha_beta_gamma_validation(self):
        with pytest.raises(AssertionError):
            FieldNode("bad", alpha=0.5, beta=0.5, gamma=0.5)

    def test_resources_non_negative(self):
        node = FieldNode("n")
        node.resources = -10
        assert node.resources == 0.0

    def test_snapshot_history(self):
        node = FieldNode("n")
        node.record_history()
        node._resources = 5.0
        node._recompute_efficiency()
        node.record_history()
        assert len(node.history) == 2
        assert node.history[1].resources == 5.0


# ======================================================================
# EfficiencyField
# ======================================================================

class TestEfficiencyField:

    def _make_field(self, n=4) -> EfficiencyField:
        field = EfficiencyField(
            diffusion_coeff=0.2,
            decay_factor=0.01,
            mobility_coeff=0.1,
            noise_scale=0.0,
        )
        nodes = [FieldNode(f"n{i}") for i in range(n)]
        for node in nodes:
            field.register_node(node)
        for i in range(n):
            for j in range(i + 1, n):
                nodes[i].add_neighbor(nodes[j])
        return field

    def test_register_unregister(self):
        field = EfficiencyField()
        node = FieldNode("x")
        field.register_node(node)
        assert "x" in field.nodes
        field.unregister_node("x")
        assert "x" not in field.nodes

    def test_step_runs(self):
        field = self._make_field()
        stats = field.step()
        assert stats["tick"] == 1
        assert stats["nodes"] == 4

    def test_energy_decreases_with_balancing(self):
        """H = Σ(T_i − R_i)² должна убывать при балансировке нагрузки."""
        field = EfficiencyField(
            diffusion_coeff=0.05,
            decay_factor=0.0,
            mobility_coeff=0.2,
            noise_scale=0.0,
        )
        nodes = [FieldNode(f"n{i}") for i in range(3)]
        for n in nodes:
            field.register_node(n)
        for i in range(3):
            for j in range(i + 1, 3):
                nodes[i].add_neighbor(nodes[j])

        nodes[0]._tasks = 10.0
        nodes[0]._recompute_potential()

        # Пропускаем несколько тиков, чтобы поле стабилизировалось
        for _ in range(10):
            field.step()
        energy_after_warmup = field.system_energy()

        for _ in range(200):
            field.step()
        final_energy = field.system_energy()

        assert final_energy < energy_after_warmup, \
            f"Energy should decrease: {energy_after_warmup:.4f} -> {final_energy:.4f}"

    def test_efficiency_converges(self):
        """При одинаковых источниках эффективности должны сходиться."""
        field = self._make_field(4)
        for _ in range(100):
            field.step()

        efficiencies = [n.efficiency for n in field.nodes.values()]
        spread = max(efficiencies) - min(efficiencies)
        assert spread < 0.5, f"Efficiencies should converge, spread={spread:.4f}"

    def test_field_stats(self):
        field = self._make_field()
        field.step()
        stats = field.field_stats()
        assert "energy" in stats
        assert "phase" in stats
        assert stats["nodes"] == 4

    def test_phase_states(self):
        field = self._make_field()
        assert field.phase_state(eta=0.01, mu_critical=0.05) == "slow_exploration"
        assert field.phase_state(eta=10.0, mu_critical=0.05) == "rapid_convergence"

    def test_node_ranking(self):
        field = self._make_field(3)
        nodes = list(field.nodes.values())
        nodes[0]._resources = 10.0
        nodes[0]._recompute_efficiency()
        ranking = field.node_ranking("efficiency")
        assert ranking[0] == nodes[0].node_id


# ======================================================================
# SwarmKernel
# ======================================================================

class TestSwarmKernel:

    def _make_kernel(self) -> SwarmKernel:
        config = {
            "swarm_field": {
                "diffusion_coeff": 0.1,
                "decay_factor": 0.01,
                "mobility_coeff": 0.05,
                "noise_scale": 0.0,
                "tick_interval": 1.0,
            }
        }
        return SwarmKernel(config)

    def test_create_node(self):
        kernel = self._make_kernel()
        node = kernel.create_node("test_node", resources=2.0)
        assert node.node_id == "test_node"
        assert math.isclose(node.resources, 2.0)
        assert "test_node" in kernel.field.nodes

    def test_remove_node(self):
        kernel = self._make_kernel()
        kernel.create_node("a")
        kernel.remove_node("a")
        assert "a" not in kernel.field.nodes

    def test_connect_nodes(self):
        kernel = self._make_kernel()
        kernel.create_node("a")
        kernel.create_node("b")
        kernel.connect_nodes("a", "b")
        assert "b" in kernel.field.nodes["a"].neighbors

    def test_full_mesh(self):
        kernel = self._make_kernel()
        for i in range(4):
            kernel.create_node(f"n{i}")
        kernel.build_full_mesh()
        for node in kernel.field.nodes.values():
            assert node.degree == 3

    def test_ring(self):
        kernel = self._make_kernel()
        for i in range(5):
            kernel.create_node(f"n{i}")
        kernel.build_ring()
        for node in kernel.field.nodes.values():
            assert node.degree == 2

    def test_manual_tick(self):
        kernel = self._make_kernel()
        kernel.create_node("a")
        kernel.create_node("b")
        kernel.connect_nodes("a", "b")
        stats = kernel.tick()
        assert stats["tick"] == 1

    def test_diagnostics(self):
        kernel = self._make_kernel()
        kernel.create_node("x")
        diag = kernel.diagnostics()
        assert diag["state"] == "stopped"
        assert diag["field"]["nodes"] == 1

    def test_initial_state(self):
        kernel = self._make_kernel()
        assert kernel.state == KernelState.STOPPED


# ======================================================================
# FieldScheduler
# ======================================================================

class TestFieldScheduler:

    def _make_scheduler(self):
        field = EfficiencyField(noise_scale=0.0)
        n1 = FieldNode("worker1")
        n1._resources = 5.0
        n1._recompute_efficiency()
        n2 = FieldNode("worker2")
        n2._resources = 1.0
        n2._tasks = 5.0
        n2._recompute_efficiency()
        n1.add_neighbor(n2)
        field.register_node(n1)
        field.register_node(n2)
        return FieldScheduler(field), field

    def test_submit_task(self):
        sched, _ = self._make_scheduler()
        task = sched.submit_task("t1", task_type="collect", priority=2.0)
        assert task.task_id == "t1"
        assert task.state == TaskState.PENDING

    def test_assign_pending(self):
        sched, _ = self._make_scheduler()
        sched.submit_task("t1")
        result = sched.schedule()
        assert result["assigned"] == 1
        task = sched.get_task("t1")
        assert task.state == TaskState.ASSIGNED
        assert task.assigned_node is not None

    def test_task_assigned_to_best_node(self):
        """Задача должна назначаться на узел с max(E) и min(Φ)."""
        sched, _ = self._make_scheduler()
        sched.submit_task("t1")
        sched.schedule()
        task = sched.get_task("t1")
        assert task.assigned_node == "worker1"

    def test_complete_task(self):
        sched, _ = self._make_scheduler()
        sched.submit_task("t1", priority=1.0)
        sched.schedule()
        sched.complete_task("t1")
        task = sched.get_task("t1")
        assert task.state == TaskState.COMPLETED
        assert task.completed_at is not None

    def test_fail_task_returns_to_pending(self):
        sched, _ = self._make_scheduler()
        sched.submit_task("t1")
        sched.schedule()
        sched.fail_task("t1")
        task = sched.get_task("t1")
        assert task.state == TaskState.PENDING

    def test_cancel_task(self):
        sched, _ = self._make_scheduler()
        sched.submit_task("t1")
        sched.cancel_task("t1")
        assert sched.get_task("t1") is None

    def test_statistics(self):
        sched, _ = self._make_scheduler()
        sched.submit_task("t1")
        sched.submit_task("t2")
        sched.schedule()
        stats = sched.statistics()
        assert stats["total_tasks"] == 2
        assert stats["total_assigned"] >= 1

    def test_multiple_tasks_distributed(self):
        sched, _ = self._make_scheduler()
        for i in range(5):
            sched.submit_task(f"t{i}", priority=1.0)
        sched.schedule()
        assert sched.pending_count() == 0


# ======================================================================
# MQTT Wildcard Matching
# ======================================================================

class TestMQTTWildcard:

    def test_exact_match(self):
        assert MQTTClient._topic_matches("a/b/c", "a/b/c") is True

    def test_exact_no_match(self):
        assert MQTTClient._topic_matches("a/b/c", "a/b/d") is False

    def test_single_level_wildcard(self):
        assert MQTTClient._topic_matches("robots/abc/status", "robots/+/status") is True

    def test_single_level_wildcard_wrong_depth(self):
        assert MQTTClient._topic_matches("robots/abc/def/status", "robots/+/status") is False

    def test_multi_level_wildcard(self):
        assert MQTTClient._topic_matches("swarm/field/node1/state", "swarm/#") is True

    def test_multi_level_wildcard_root(self):
        assert MQTTClient._topic_matches("anything/at/all", "#") is True

    def test_multi_level_at_end(self):
        assert MQTTClient._topic_matches("swarm/field/n1/state", "swarm/field/#") is True

    def test_single_wildcard_in_middle(self):
        assert MQTTClient._topic_matches("swarm/field/n1/state", "swarm/+/n1/state") is True

    def test_multiple_single_wildcards(self):
        assert MQTTClient._topic_matches("a/b/c/d", "a/+/c/+") is True

    def test_pattern_longer_than_topic(self):
        assert MQTTClient._topic_matches("a/b", "a/b/c") is False

    def test_topic_longer_than_pattern(self):
        assert MQTTClient._topic_matches("a/b/c", "a/b") is False

    def test_single_level(self):
        assert MQTTClient._topic_matches("status", "status") is True

    def test_empty_segment_match(self):
        assert MQTTClient._topic_matches("a//b", "a/+/b") is True
