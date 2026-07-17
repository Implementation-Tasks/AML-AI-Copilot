"""
Graph -> QUBO Matrix Converter (P0 Critical)

Converts a blockchain transaction graph (NetworkX DiGraph) into a
Quadratic Unconstrained Binary Optimization (QUBO) matrix for use
with quantum-inspired solvers (Qamelion, Perceval, SimAnneal).

Objective: Minimize False Positive Rate while keeping Recall acceptable.
Cost function prioritizes Precision (F-beta with beta=0.5).

Pipeline (Bottleneck 1 -- MIMO Tensor Module integrated, slide 14):
    Graph --> [MIMO Tensor Decomposition] --> r~_i elevated for smurfing nodes
           --> [Top-20 Subgraph Selection (slide 8)] --> QUBO --> QAOA --> Binary flags
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


# ============================================================
# Bottleneck 1: MIMO Tensor Decomposition -- Smurfing Detection
# (Mentorship Review slide 14)
# ============================================================

def detect_smurfing_via_tensor(
    graph,
    structuring_threshold_usd=10_000.0,
    time_window_seconds=86_400.0,
    n_components=3,
    smurfing_risk_boost=0.45,
):
    """
    MIMO-style tensor decomposition for smurfing / structuring detection.

    Rationale (slide 14 -- Bottleneck 1):
        Smurfing = financial equivalent of radar RCS reduction.
        Individual micro-transactions fall below reporting thresholds.
        MIMO spatial multiplexing + coherent integration recovers the signal.

    Steps:
        1. Build wallet x time-bucket matrix T[w, t] = sum(amount_usd)
        2. Truncated SVD (rank-r CP approximation) on T
        3. Reconstructed T_hat reveals correlated micro-tx clusters
        4. Wallets where reconstructed total >= threshold but max single tx < threshold
           => smurfing_risk_boost applied to r~_i

    Returns:
        Dict[wallet_address -> smurfing_risk_score] (0.0 if not detected)
    """
    smurfing_scores = {}
    wallets = list(graph.nodes())
    if not wallets:
        return smurfing_scores

    wallet_idx = {w: i for i, w in enumerate(wallets)}
    now_ts = time.time()

    edges_with_ts = []
    for u, v, data in graph.edges(data=True):
        amount = float(data.get("amount_usd", 0.0))
        ts = float(data.get("timestamp", now_ts))
        if amount > 0:
            edges_with_ts.append((u, v, amount, ts))

    if not edges_with_ts:
        return smurfing_scores

    all_ts = [e[3] for e in edges_with_ts]
    t_min, t_max = min(all_ts), max(all_ts)
    time_range = max(t_max - t_min, time_window_seconds)
    n_buckets = max(int(time_range / time_window_seconds) + 1, 2)
    n_wallets = len(wallets)

    T = np.zeros((n_wallets, n_buckets), dtype=np.float64)
    for u, _, amount, ts in edges_with_ts:
        if u in wallet_idx:
            bucket = min(int((ts - t_min) / time_window_seconds), n_buckets - 1)
            T[wallet_idx[u], bucket] += amount

    rank = min(n_components, min(T.shape) - 1)
    if rank < 1:
        return smurfing_scores

    try:
        U, S, Vt = np.linalg.svd(T, full_matrices=False)
        T_hat = (U[:, :rank] * S[:rank]) @ Vt[:rank, :]
    except np.linalg.LinAlgError:
        logger.warning("[MIMOTensor] SVD failed -- skipping smurfing detection")
        return smurfing_scores

    for w, idx in wallet_idx.items():
        reconstructed_total = float(T_hat[idx].sum())
        raw_col = T[idx]
        raw_max_tx = float(raw_col.max()) if raw_col.any() else 0.0
        raw_total = float(raw_col.sum())

        if (
            reconstructed_total >= structuring_threshold_usd
            and raw_max_tx < structuring_threshold_usd * 0.90
            and raw_total > 0
        ):
            score = min(smurfing_risk_boost * (reconstructed_total / structuring_threshold_usd), 1.0)
            smurfing_scores[w] = score
            logger.info(
                "[MIMOTensor] Smurfing | wallet=%s reconstructed=$%.0f max_single=$%.0f score=%.3f",
                w, reconstructed_total, raw_max_tx, score,
            )

    if smurfing_scores:
        logger.info("[MIMOTensor] %d smurfing originator(s) via rank-%d SVD", len(smurfing_scores), rank)
    return smurfing_scores


# ============================================================
# Top-20 Subgraph Modularization -- NISQ Bridge (slide 8)
# ============================================================

def select_top_k_subgraph(graph, risk_scores, k=20, seed_wallet=None,
                           lambda_r=0.50, lambda_n=0.30, lambda_p=0.20):
    """
    Select Top-K high-risk subgraph for QAOA execution (slide 8).

    Priority score:
        s_i = lambda_r * r~_i + lambda_n * Centrality_i
              + lambda_p * PathRisk_i + lambda_a * I[i=a]

    Seed wallet a is always enforced (lambda_a -> infinity).
    Returns subgraph G[V_k] with |V_k| <= k -- quantum-ready NISQ size.
    """
    nodes = list(graph.nodes())
    if len(nodes) <= k:
        return graph

    degree_centrality = nx.degree_centrality(graph)
    path_risks = {}
    for node in nodes:
        nbrs = list(graph.predecessors(node)) + list(graph.successors(node))
        path_risks[node] = (
            sum(risk_scores.get(n, 0.0) for n in nbrs) / max(len(nbrs), 1)
        )

    priority = {
        node: (
            lambda_r * risk_scores.get(node, 0.0)
            + lambda_n * degree_centrality.get(node, 0.0)
            + lambda_p * path_risks.get(node, 0.0)
            + (1.0 if node == seed_wallet else 0.0)
        )
        for node in nodes
    }

    top_k_nodes = set(sorted(priority, key=priority.__getitem__, reverse=True)[:k])
    if seed_wallet and seed_wallet in graph:
        top_k_nodes.add(seed_wallet)

    subgraph = graph.subgraph(top_k_nodes).copy()
    logger.info("[TopK] n=%d nodes selected for QAOA (full graph: %d)", len(top_k_nodes), len(nodes))
    return subgraph


# ============================================================
# Feature Extraction
# ============================================================

def _extract_node_risk_scores(graph, smurfing_scores=None):
    """
    Heuristic r~_i per wallet from graph topology + MIMO smurfing boost.
    Used as diagonal linear terms q_i in QUBO matrix.
    """
    scores = {}
    in_degree = dict(graph.in_degree())
    out_degree = dict(graph.out_degree())
    total_nodes = max(graph.number_of_nodes(), 1)

    for node in graph.nodes():
        fan_out = out_degree.get(node, 0) / total_nodes
        fan_in  = in_degree.get(node, 0) / total_nodes
        d = graph.nodes[node]
        is_mixer   = float(d.get("is_mixer",   0))
        is_bridge  = float(d.get("is_bridge",  0))
        tx_velocity= float(d.get("tx_velocity",0.0))

        base = (
            0.30 * fan_out
            + 0.20 * fan_in
            + 0.25 * is_mixer
            + 0.15 * is_bridge
            + 0.10 * min(tx_velocity / 100.0, 1.0)
        )
        smurfing_boost = (smurfing_scores or {}).get(node, 0.0)
        scores[node] = min(base + smurfing_boost, 1.0)
    return scores


def _extract_edge_coupling(graph, nodes):
    """
    Edge coupling q_ij (quadratic QUBO terms).
    Higher weight -> flagging both endpoints penalized.
    """
    node_idx = {node: i for i, node in enumerate(nodes)}
    coupling = {}
    for u, v, data in graph.edges(data=True):
        if u not in node_idx or v not in node_idx:
            continue
        i, j = node_idx[u], node_idx[v]
        amount = float(data.get("amount_usd", 0.0))
        weight = min(amount / 1_000_000, 1.0)
        coupling[(i, j)] = weight
    return coupling


# ============================================================
# QUBO Builder  C(x) = x^T Q x  (slide 9)
# ============================================================

def map_graph_to_qubo(tx_graph, beta=F_BETA, lambda_fp=2.0, run_mimo_detection=True):
    """
    Convert a transaction graph to QUBO matrix C(x) = x^T Q x.

    Pipeline:
        1. MIMO Tensor Decomposition -> smurfing scores -> r~_i boost
        2. Top-20 Subgraph Selection  -> NISQ-ready G20
        3. Build Q matrix (linear + quadratic terms)

    Args:
        tx_graph:           TransactionGraph
        beta:               F-beta (0.5 -> Precision x2)
        lambda_fp:          False-positive penalty
        run_mimo_detection: Enable MIMO smurfing pre-processing (default True)

    Returns:
        QUBOResult(qubo_matrix, variable_mapping, estimated_energy)
    """
    graph = tx_graph.graph
    n_nodes = graph.number_of_nodes()

    if n_nodes == 0:
        raise ValueError("Cannot build QUBO: graph has no nodes")
    if n_nodes > QUBO_MAX_NODES:
        raise ValueError(
            f"Graph has {n_nodes} nodes > QUBO_MAX_NODES={QUBO_MAX_NODES}. "
            "Apply subgraph sampling first."
        )

    t0 = time.perf_counter()

    # Step 1: MIMO Tensor Decomposition (Bottleneck 1)
    smurfing_scores = {}
    if run_mimo_detection:
        smurfing_scores = detect_smurfing_via_tensor(graph)

    # Step 2: Top-20 Subgraph Selection (NISQ Bridge, slide 8)
    prelim_risk = _extract_node_risk_scores(graph, smurfing_scores)
    seed = getattr(tx_graph, "seed_wallet", None)
    if n_nodes > 20:
        graph = select_top_k_subgraph(graph, prelim_risk, k=20, seed_wallet=seed)
        n_nodes = graph.number_of_nodes()
        logger.info("[QUBO] Subgraph: n=%d nodes (NISQ-ready)", n_nodes)

    # Step 3: Build Q matrix
    nodes = list(graph.nodes())
    variable_mapping = {i: node for i, node in enumerate(nodes)}
    logger.info("[QUBO] Building Q matrix | n=%d | beta=%.2f | lambda=%.2f", n_nodes, beta, lambda_fp)

    Q = np.zeros((n_nodes, n_nodes), dtype=np.float64)

    risk_scores = _extract_node_risk_scores(graph, smurfing_scores)
    for i, node in enumerate(nodes):
        Q[i, i] = -risk_scores.get(node, 0.0) * (1 + beta ** 2)

    coupling = _extract_edge_coupling(graph, nodes)
    for (i, j), weight in coupling.items():
        penalty = lambda_fp * weight
        Q[i, j] += penalty
        Q[j, i] += penalty

    node_idx = {node: i for i, node in enumerate(nodes)}
    for licit_wallet in tx_graph.known_licit:
        if licit_wallet in node_idx:
            Q[node_idx[licit_wallet], node_idx[licit_wallet]] += lambda_fp * 5.0

    estimated_energy = float(np.sum(np.diag(Q)[np.diag(Q) < 0]))
    elapsed = time.perf_counter() - t0
    logger.info(
        "[QUBO] Done in %.3fs | shape=%s | energy~=%.4f | smurfing_nodes=%d",
        elapsed, Q.shape, estimated_energy, len(smurfing_scores),
    )

    return QUBOResult(
        qubo_matrix=Q,
        variable_mapping=variable_mapping,
        estimated_energy=estimated_energy,
        backend_used="pending",
    )


def compute_f_beta(precision, recall, beta=F_BETA):
    """Compute F-beta score. beta < 1 weights Precision higher than Recall."""
    if precision + recall == 0:
        return 0.0
    return (1 + beta ** 2) * precision * recall / ((beta ** 2 * precision) + recall)


def evaluate_qubo_solution(solution, variable_mapping, ground_truth_illicit,
                            ground_truth_licit, beta=F_BETA):
    """
    Evaluate QUBO binary solution against ground truth labels.
    Returns dict: precision, recall, f_beta, fpr, tp, fp, fn, tn.
    """
    flagged = {variable_mapping[i] for i, v in solution.items() if v == 1}
    tp = len(flagged & ground_truth_illicit)
    fp = len(flagged & ground_truth_licit)
    fn = len(ground_truth_illicit - flagged)
    tn = len(ground_truth_licit - flagged)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    fpr       = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    f_beta    = compute_f_beta(precision, recall, beta)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f_beta_score": round(f_beta, 4),
        "false_positive_rate": round(fpr, 4),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }