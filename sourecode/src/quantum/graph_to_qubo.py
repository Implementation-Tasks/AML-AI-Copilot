"""
Graph → QUBO Matrix Converter (P0 Critical)

Converts a blockchain transaction graph (NetworkX DiGraph) into a
Quadratic Unconstrained Binary Optimization (QUBO) matrix for use
with quantum-inspired solvers (Qamelion, Perceval, SimAnneal).

Objective: Minimize False Positive Rate while keeping Recall acceptable.
Cost function prioritizes Precision (F-β with β=0.5).
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import networkx as nx
import numpy as np

from src.config import F_BETA, QUBO_MAX_NODES
from src.models import QUBOResult, TransactionGraph

logger = logging.getLogger(__name__)


# ─── Feature Extraction ───────────────────────────────────────────────────────

def _extract_node_risk_scores(graph: nx.DiGraph) -> dict[str, float]:
    """
    Heuristic risk scores per wallet node based on graph topology.
    Used as diagonal (linear) terms in the QUBO matrix.
    """
    scores: dict[str, float] = {}
    in_degree = dict(graph.in_degree())
    out_degree = dict(graph.out_degree())
    total_nodes = max(graph.number_of_nodes(), 1)

    for node in graph.nodes():
        # Fan-out pattern: many outgoing → potential smurfing
        fan_out_ratio = out_degree.get(node, 0) / total_nodes
        # Fan-in pattern: many incoming → potential aggregator (layering)
        fan_in_ratio = in_degree.get(node, 0) / total_nodes

        # Node attributes (set externally from Dune/Etherscan data)
        node_data = graph.nodes[node]
        is_mixer = float(node_data.get("is_mixer", 0))
        is_bridge = float(node_data.get("is_bridge", 0))
        tx_velocity = float(node_data.get("tx_velocity", 0.0))  # txs/hour

        risk = (
            0.30 * fan_out_ratio
            + 0.20 * fan_in_ratio
            + 0.25 * is_mixer
            + 0.15 * is_bridge
            + 0.10 * min(tx_velocity / 100.0, 1.0)
        )
        scores[node] = min(risk, 1.0)

    return scores


def _extract_edge_coupling(graph: nx.DiGraph, nodes: list[str]) -> dict[tuple[int, int], float]:
    """
    Edge coupling strengths (quadratic QUBO terms).
    Higher coupling = flagging both nodes is expensive (penalizes over-flagging).
    """
    node_idx = {node: i for i, node in enumerate(nodes)}
    coupling: dict[tuple[int, int], float] = {}

    for u, v, data in graph.edges(data=True):
        if u not in node_idx or v not in node_idx:
            continue
        i, j = node_idx[u], node_idx[v]
        amount = float(data.get("amount_usd", 0.0))
        # Normalize edge weight: large transfers → strong coupling
        weight = min(amount / 1_000_000, 1.0)  # cap at $1M
        coupling[(i, j)] = weight

    return coupling


# ─── QUBO Builder ─────────────────────────────────────────────────────────────

def map_graph_to_qubo(
    tx_graph: TransactionGraph,
    beta: float = F_BETA,
    lambda_fp: float = 2.0,
) -> QUBOResult:
    """
    Convert a transaction graph to a QUBO matrix.

    QUBO Cost Function:
        C(x) = -Σ(risk_i × x_i)           # maximize true positive detection
               + λ × Σ(coupling_ij × x_i × x_j)  # penalize correlated FPs

    Where:
        x_i ∈ {0, 1} — binary: flag this wallet (1) or not (0)
        beta < 1      — prioritize Precision over Recall

    Args:
        tx_graph:  TransactionGraph with graph, features, ground truth
        beta:      F-β parameter (default 0.5 → Precision weighted 2x)
        lambda_fp: False-positive penalty coefficient (default 2.0)

    Returns:
        QUBOResult with qubo_matrix, variable_mapping, estimated_energy
    """
    graph = tx_graph.graph
    n_nodes = graph.number_of_nodes()

    if n_nodes == 0:
        raise ValueError("Cannot build QUBO: graph has no nodes")
    if n_nodes > QUBO_MAX_NODES:
        raise ValueError(
            f"Graph has {n_nodes} nodes, exceeds QUBO_MAX_NODES={QUBO_MAX_NODES}. "
            "Consider subgraph sampling before QUBO mapping."
        )

    start_time = time.perf_counter()
    nodes = list(graph.nodes())
    variable_mapping = {i: node for i, node in enumerate(nodes)}

    logger.info(f"Building QUBO matrix for {n_nodes} nodes, β={beta}, λ={lambda_fp}")

    # Initialise Q matrix (N×N, float64)
    Q = np.zeros((n_nodes, n_nodes), dtype=np.float64)

    # ── Linear terms (diagonal): reward flagging high-risk nodes ──────────────
    risk_scores = _extract_node_risk_scores(graph)
    for i, node in enumerate(nodes):
        # Negative = QUBO minimization rewards flagging (reward = -risk)
        Q[i, i] = -risk_scores.get(node, 0.0) * (1 + beta ** 2)

    # ── Quadratic terms (off-diagonal): penalize correlated false positives ───
    coupling = _extract_edge_coupling(graph, nodes)
    for (i, j), weight in coupling.items():
        penalty = lambda_fp * weight
        Q[i, j] += penalty
        Q[j, i] += penalty  # symmetrize

    # ── Known licit nodes: strong penalty for flagging ────────────────────────
    node_idx = {node: i for i, node in enumerate(nodes)}
    for licit_wallet in tx_graph.known_licit:
        if licit_wallet in node_idx:
            idx = node_idx[licit_wallet]
            Q[idx, idx] += lambda_fp * 5.0  # heavy penalty

    # ── Estimated ground state energy ─────────────────────────────────────────
    # Lower bound: sum of negative diagonals (all high-risk flagged)
    estimated_energy = float(np.sum(np.diag(Q)[np.diag(Q) < 0]))

    elapsed = time.perf_counter() - start_time
    logger.info(f"QUBO matrix built in {elapsed:.3f}s | shape={Q.shape} | energy≈{estimated_energy:.4f}")

    return QUBOResult(
        qubo_matrix=Q,
        variable_mapping=variable_mapping,
        estimated_energy=estimated_energy,
        backend_used="pending",  # set by HybridQuantumOptimizer after solve
    )


def compute_f_beta(precision: float, recall: float, beta: float = F_BETA) -> float:
    """Compute F-β score. β < 1 weights Precision higher than Recall."""
    if precision + recall == 0:
        return 0.0
    numerator = (1 + beta ** 2) * precision * recall
    denominator = (beta ** 2 * precision) + recall
    return numerator / denominator


def evaluate_qubo_solution(
    solution: dict[int, int],
    variable_mapping: dict[int, str],
    ground_truth_illicit: set[str],
    ground_truth_licit: set[str],
    beta: float = F_BETA,
) -> dict[str, float]:
    """
    Evaluate a QUBO binary solution against ground truth labels.

    Args:
        solution:               {variable_index: 0|1} from solver
        variable_mapping:       {index: wallet_address}
        ground_truth_illicit:   Set of known-illicit wallets
        ground_truth_licit:     Set of known-licit wallets
        beta:                   F-β parameter

    Returns:
        dict with precision, recall, f_beta, fpr, tp, fp, fn, tn
    """
    flagged = {variable_mapping[i] for i, v in solution.items() if v == 1}
    all_labelled = ground_truth_illicit | ground_truth_licit

    tp = len(flagged & ground_truth_illicit)
    fp = len(flagged & ground_truth_licit)
    fn = len(ground_truth_illicit - flagged)
    tn = len(ground_truth_licit - flagged)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    f_beta = compute_f_beta(precision, recall, beta)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f_beta_score": round(f_beta, 4),
        "false_positive_rate": round(fpr, 4),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }
