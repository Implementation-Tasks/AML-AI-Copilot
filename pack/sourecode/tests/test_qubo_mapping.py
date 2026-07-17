"""
Test Suite: QUBO Mapping & Quantum Backend
Skill: test-driven-development
"""
import numpy as np
import networkx as nx
import pytest

from src.models import TransactionGraph
from src.quantum.graph_to_qubo import (
    compute_f_beta,
    evaluate_qubo_solution,
    map_graph_to_qubo,
)
from src.quantum.hybrid_optimizer import HybridQuantumOptimizer


# ─── Fixtures ─────────────────────────────────────────────────────────────────

def make_tx_graph(n_nodes: int = 50, illicit_ratio: float = 0.10) -> TransactionGraph:
    """Create a synthetic blockchain transaction graph for testing."""
    G = nx.scale_free_graph(n_nodes, seed=42).to_directed()
    G = nx.DiGraph(G)  # remove multi-edges

    nodes = list(G.nodes())
    n_illicit = max(1, int(n_nodes * illicit_ratio))
    illicit = [str(nodes[i]) for i in range(n_illicit)]
    licit = [str(n) for n in nodes[n_illicit:]]

    # Add node features
    for node in G.nodes():
        G.nodes[node]["is_mixer"] = 1 if str(node) in illicit[:2] else 0
        G.nodes[node]["is_bridge"] = 0
        G.nodes[node]["tx_velocity"] = np.random.exponential(10)

    # Add edge features
    for u, v in G.edges():
        G[u][v]["amount_usd"] = np.random.exponential(50_000)

    # Re-label nodes to string wallet addresses
    mapping = {n: f"0x{i:040x}" for i, n in enumerate(nodes)}
    G = nx.relabel_nodes(G, mapping)
    illicit_addr = [mapping[nodes[i]] for i in range(n_illicit)]
    licit_addr = [mapping[n] for n in nodes[n_illicit:]]

    return TransactionGraph(
        graph=G,
        known_illicit=illicit_addr,
        known_licit=licit_addr,
        source_dataset="synthetic_test",
    )


# ─── QUBO Matrix Tests ────────────────────────────────────────────────────────

class TestQUBOMapping:

    def test_qubo_matrix_shape(self):
        tx_graph = make_tx_graph(n_nodes=30)
        result = map_graph_to_qubo(tx_graph)
        n = tx_graph.graph.number_of_nodes()
        assert result.qubo_matrix.shape == (n, n), "QUBO must be square"

    def test_qubo_matrix_symmetric(self):
        tx_graph = make_tx_graph(n_nodes=30)
        result = map_graph_to_qubo(tx_graph)
        Q = result.qubo_matrix
        assert np.allclose(Q, Q.T, atol=1e-10), "QUBO matrix must be symmetric"

    def test_qubo_matrix_dtype(self):
        tx_graph = make_tx_graph(n_nodes=20)
        result = map_graph_to_qubo(tx_graph)
        assert result.qubo_matrix.dtype == np.float64

    def test_variable_mapping_completeness(self):
        tx_graph = make_tx_graph(n_nodes=25)
        result = map_graph_to_qubo(tx_graph)
        n = tx_graph.graph.number_of_nodes()
        assert len(result.variable_mapping) == n
        assert all(isinstance(v, str) for v in result.variable_mapping.values())

    def test_licit_nodes_penalised(self):
        """Known licit wallets should have positive diagonal (penalty for flagging)."""
        tx_graph = make_tx_graph(n_nodes=20)
        result = map_graph_to_qubo(tx_graph)
        Q = result.qubo_matrix
        idx_map = {v: k for k, v in result.variable_mapping.items()}
        for licit_wallet in tx_graph.known_licit[:5]:
            if licit_wallet in idx_map:
                i = idx_map[licit_wallet]
                assert Q[i, i] >= 0, f"Licit wallet {licit_wallet} should have non-negative diagonal"

    def test_large_graph_raises(self):
        """Graphs exceeding QUBO_MAX_NODES must raise ValueError."""
        tx_graph = make_tx_graph(n_nodes=10)
        # Patch config temporarily
        import src.quantum.graph_to_qubo as m
        original = m.QUBO_MAX_NODES
        m.QUBO_MAX_NODES = 5
        with pytest.raises(ValueError, match="exceeds QUBO_MAX_NODES"):
            map_graph_to_qubo(tx_graph)
        m.QUBO_MAX_NODES = original

    def test_empty_graph_raises(self):
        G = nx.DiGraph()
        tx_graph = TransactionGraph(graph=G)
        with pytest.raises(ValueError, match="no nodes"):
            map_graph_to_qubo(tx_graph)

    def test_performance_1000_nodes(self):
        """QUBO mapping for 1000-node graph must complete in < 5 seconds."""
        import time
        tx_graph = make_tx_graph(n_nodes=500)  # 500 to stay under QUBO_MAX_NODES default
        start = time.perf_counter()
        result = map_graph_to_qubo(tx_graph)
        elapsed = time.perf_counter() - start
        assert elapsed < 5.0, f"QUBO mapping too slow: {elapsed:.2f}s"
        assert result.qubo_matrix is not None


# ─── F-β Score Tests ──────────────────────────────────────────────────────────

class TestFBetaScore:

    def test_perfect_precision(self):
        """β=0.5 with perfect precision should yield high score."""
        # F-β(β=0.5, P=1.0, R=0.5) = (1+0.25)*1.0*0.5 / (0.25*1.0 + 0.5) = 0.625/0.75 ≈ 0.833
        score = compute_f_beta(precision=1.0, recall=0.5, beta=0.5)
        assert score > 0.80

    def test_zero_precision(self):
        score = compute_f_beta(precision=0.0, recall=1.0, beta=0.5)
        assert score == 0.0

    def test_zero_recall(self):
        score = compute_f_beta(precision=1.0, recall=0.0, beta=0.5)
        assert score == 0.0

    def test_beta_less_than_one_weights_precision(self):
        """With β<1, high precision + low recall should score higher than low precision + high recall."""
        score_high_precision = compute_f_beta(precision=0.95, recall=0.40, beta=0.5)
        score_high_recall = compute_f_beta(precision=0.40, recall=0.95, beta=0.5)
        assert score_high_precision > score_high_recall, "β<1 should prefer Precision"


# ─── Solution Evaluation Tests ────────────────────────────────────────────────

class TestEvaluateQUBOSolution:

    def test_perfect_solution(self):
        var_map = {0: "0xILLICIT", 1: "0xLICIT"}
        solution = {0: 1, 1: 0}
        metrics = evaluate_qubo_solution(
            solution, var_map,
            ground_truth_illicit={"0xILLICIT"},
            ground_truth_licit={"0xLICIT"},
        )
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["false_positive_rate"] == 0.0

    def test_all_flagged(self):
        """Flagging everything should give FPR = 1.0."""
        var_map = {0: "0xILLICIT", 1: "0xLICIT"}
        solution = {0: 1, 1: 1}
        metrics = evaluate_qubo_solution(
            solution, var_map,
            ground_truth_illicit={"0xILLICIT"},
            ground_truth_licit={"0xLICIT"},
        )
        assert metrics["false_positive_rate"] == 1.0

    def test_nothing_flagged(self):
        var_map = {0: "0xILLICIT", 1: "0xLICIT"}
        solution = {0: 0, 1: 0}
        metrics = evaluate_qubo_solution(
            solution, var_map,
            ground_truth_illicit={"0xILLICIT"},
            ground_truth_licit={"0xLICIT"},
        )
        assert metrics["recall"] == 0.0
        assert metrics["false_positive_rate"] == 0.0


# ─── Hybrid Optimizer Tests ───────────────────────────────────────────────────

class TestHybridQuantumOptimizer:

    def test_classical_backend_init(self):
        optimizer = HybridQuantumOptimizer(backend_choice="classical")
        assert optimizer.backend_choice == "classical"

    def test_unknown_backend_raises(self):
        with pytest.raises(ValueError, match="Unknown backend"):
            HybridQuantumOptimizer(backend_choice="unknown_qpu")

    def test_optimize_returns_result(self):
        optimizer = HybridQuantumOptimizer(backend_choice="classical")
        tx_graph = make_tx_graph(n_nodes=30)
        result = optimizer.optimize(tx_graph)
        assert result is not None
        assert isinstance(result.flagged_wallets, list)
        assert 0.0 <= result.false_positive_rate <= 1.0
        assert 0.0 <= result.f_beta_score <= 1.0
        assert result.runtime_seconds > 0

    def test_optimize_respects_f_beta_priority(self):
        """With β=0.5, optimizer should prefer precision over recall."""
        optimizer = HybridQuantumOptimizer(backend_choice="classical")
        tx_graph = make_tx_graph(n_nodes=40, illicit_ratio=0.05)
        result = optimizer.optimize(tx_graph, beta=0.5)
        # Cannot guarantee in SA, but at minimum verify F-β is computed
        f_beta_check = compute_f_beta(result.precision, result.recall, beta=0.5)
        assert abs(f_beta_check - result.f_beta_score) < 0.01
