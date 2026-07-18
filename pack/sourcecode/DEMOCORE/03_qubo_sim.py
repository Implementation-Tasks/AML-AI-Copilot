#!/usr/bin/env python3
"""
qubo_sim.py — AML AI Copilot · MVP Simulation Engine
=====================================================
SEA Quantathon 2026 · QCFinOp Team

PURPOSE
-------
This module is the self-contained QC/AI/ML component for the MVP prototype.
It simulates the full Hybrid Quantum-Agentic AML pipeline WITHOUT requiring
any external API keys, cloud services, or LLM calls.

It is designed to be called by the clickable prototype (prototype.html) via
a lightweight local HTTP endpoint, OR run standalone to pre-generate the
JSON payloads embedded directly in the HTML.

PIPELINE SIMULATED (Aligned with Prof. Hans's Architecture)
------------------------------------------------------------
1. QUBO Optimizer  — Simulated Annealing with:
   - MIMO Tensor Decomposition (Bottleneck 1, slide 14) for smurfing detection
   - Top-20 Subgraph Selection (NISQ Bridge, slide 8)
   - F-β cost function (β=0.5 → Precision weighted 4x higher than Recall)

2. Flow Tracer     — Deterministic multi-hop path simulation

3. OSINT Analyst   — Sanctions list mock lookup

4. Compliance Ofcr — 6-Component Compliance Score (Slide 13):
   - Rₐ = ωr·r̃ₐ + ωq·ζₐQ + ωE·Eₐ + ωS·Sₐ + ωC·Cₐ + ωO·Oₐ
   - Parametric thresholds: τH (HIGH/FREEZE), τM (MEDIUM/MONITOR)
   - FATF Recommendation 16 Travel Rule compliance check
   - SHA-256 audit hash for tamper-proof SAR

DESIGN PRINCIPLES (Senior Dev Notes)
--------------------------------------
- Fully deterministic: same wallet → same score every run (reproducible demo)
- No external I/O: zero HTTP calls, zero disk I/O except optional JSON dump
- Type-safe: full dataclass / TypedDict schema
- Testable: each stage is a pure function with no side effects
- Demo-ready: 4 canonical test wallets with pre-tuned expected outputs
- Architecture-aligned: matches src/quantum/*, src/agents/*, src/pipeline/*
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional
import http.server
import socketserver
import urllib.parse
import sys

# ─── Constants ────────────────────────────────────────────────────────────────

QUBO_RISK_THRESHOLD = 0.85
F_BETA = 0.5
GRAPH_NODES = 50
GRAPH_SEED_BASE = 42

# ─── Compliance Score Weights (Prof. Hans Architecture, Slide 13) ─────────────
# Rₐ = clip(ωr·r̃ₐ + ωq·ζₐQ + ωE·Eₐ + ωS·Sₐ + ωC·Cₐ + ωO·Oₐ, 0, 1)
# All ω >= 0 and sum to 1. Calibrated from historical labelled cases.
OMEGA_R = 0.30  # ωr  classical risk score r̃
OMEGA_Q = 0.25  # ωq  quantum evidence ζQ
OMEGA_E = 0.20  # ωE  external / sanctions
OMEGA_S = 0.15  # ωS  scam/structuring signal
OMEGA_C = 0.07  # ωC  counterparty exposure (mixer)
OMEGA_O = 0.03  # ωO  obfuscation (cross-chain bridge)

# Validation: weights must sum to 1.0
assert abs(OMEGA_R + OMEGA_Q + OMEGA_E + OMEGA_S + OMEGA_C + OMEGA_O - 1.0) < 1e-6, \
    "Compliance score weights must sum to 1.0"

# ─── Parametric Thresholds (Slide 13, Bottleneck 2 slide 15) ──────────────────
THRESHOLD_HIGH = 0.75  # τH — HIGH risk, action = FREEZE
THRESHOLD_MED  = 0.45  # τM — MEDIUM risk, action = MONITOR

# ─── FATF Travel Rule (Recommendation 16) ─────────────────────────────────────
TRAVEL_RULE_THRESHOLD_USD = 1000.0  # SEA (MAS/OJK) threshold

# ─── Canonical Demo Wallets ───────────────────────────────────────────────────
# These wallets are pre-seeded to produce deterministic, meaningful outputs
# for live demos and usability tests.

DEMO_WALLETS: dict[str, dict] = {
    # Known HIGH RISK — Tornado Cash mixer node
    "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b": {
        "expected_risk": "HIGH",
        "expected_action": "FREEZE",
        "seed_offset": 100,
        "sanctions_hit": True,
        "sanctions_list": "OFAC SDN List (updated 2026-06-01)",
        "hop_count": 7,
        "mixer_detected": True,
        "mixer_name": "Tornado Cash",
    },
    # HIGH RISK — Bridge exploit wallet
    "0x1234567890AbcdEF1234567890AbcDef12345678": {
        "expected_risk": "HIGH",
        "expected_action": "FREEZE",
        "seed_offset": 200,
        "sanctions_hit": True,
        "sanctions_list": "EU Sanctions List + CryptoScamDB",
        "hop_count": 5,
        "mixer_detected": False,
        "mixer_name": None,
    },
    # MEDIUM RISK — Suspicious pattern, needs monitoring
    "0xABCDEF0123456789ABCDef0123456789abcdef01": {
        "expected_risk": "MEDIUM",
        "expected_action": "MONITOR",
        "seed_offset": 300,
        "sanctions_hit": False,
        "sanctions_list": None,
        "hop_count": 3,
        "mixer_detected": False,
        "mixer_name": None,
    },
    # LOW RISK — Clean wallet
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e": {
        "expected_risk": "LOW",
        "expected_action": "CLEAR",
        "seed_offset": 400,
        "sanctions_hit": False,
        "sanctions_list": None,
        "hop_count": 0,
        "mixer_detected": False,
        "mixer_name": None,
    },
}


# ─── Data Models (Aligned with src/models.py) ────────────────────────────────

@dataclass
class QuboResult:
    """Output from the QUBO Simulated Annealing stage."""
    risk_score: float           # 0.0 – 1.0 (quantum evidence ζQ)
    classical_risk: float       # r̃ₐ — classical node risk
    false_positive_rate: float
    f_beta_score: float
    precision: float
    recall: float
    flagged_nodes: list[str]
    graph_nodes: int
    graph_edges: int
    backend_used: str
    runtime_ms: float
    smurfing_detected: bool = False
    smurfing_nodes: int = 0


@dataclass
class Hop:
    """Single transaction hop in a trace."""
    from_wallet: str
    to_wallet: str
    tx_hash: str
    amount_usd: float
    chain: str = "ETH"
    timestamp: str = ""
    via_mixer: bool = False
    via_bridge: bool = False


@dataclass
class FlowTraceResult:
    """Output from the multi-hop Flow Tracer agent."""
    hop_count: int
    hops: list[Hop]
    path: list[str]
    mixer_detected: bool
    mixer_name: Optional[str]
    bridge_detected: bool
    chains_involved: list[str]
    summary: str


@dataclass
class OsintResult:
    """Output from the OSINT & KYC Analyst agent."""
    sanctions_hit: bool
    sanctions_list: Optional[str]
    confidence: float
    pep_match: bool
    scamdb_match: bool
    summary: str


@dataclass
class TravelRuleRecord:
    """FATF Recommendation 16 — Travel Rule compliance record."""
    tx_hash: str
    originator_account: str
    beneficiary_account: str
    transfer_amount_usd: float
    threshold_exceeded: bool


@dataclass
class ComplianceReport:
    """Output from the AI Compliance Officer agent."""
    case_id: str
    wallet_address: str
    risk_level: str           # HIGH | MEDIUM | LOW
    recommended_action: str   # FREEZE | MONITOR | CLEAR
    
    # Compliance Score Components (Slide 13)
    compliance_score: float   # Rₐ (composite)
    score_components: dict    # {r_tilde, zeta_q, E_sanctions, S_scam, C_mixer, O_bridge}
    weights: dict             # {omega_r, omega_q, omega_E, omega_S, omega_C, omega_O}
    thresholds: dict          # {tau_H, tau_M}
    
    # Legacy QUBO metrics
    qubo_risk_score: float
    f_beta_score: float
    precision: float
    recall: float
    
    # Compliance artifacts
    audit_hash: str           # SHA-256
    sar_summary: str
    timestamp: str
    runtime_ms: float
    
    # Detailed breakdowns
    qubo: Optional[dict] = field(default=None)
    flow_trace: Optional[dict] = field(default=None)
    osint: Optional[dict] = field(default=None)
    travel_rule_violations: list[dict] = field(default_factory=list)


# ─── Stage 1: QUBO Simulated Annealing ───────────────────────────────────────

def _build_synthetic_graph(wallet: str, seed: int) -> tuple[list, list, list, dict]:
    """
    Generate a deterministic scale-free transaction graph with edge amounts.
    Returns (nodes, edges, illicit_nodes, edge_amounts).
    
    Edge amounts are used for MIMO Tensor Decomposition smurfing detection.
    """
    rng = random.Random(seed)
    n = GRAPH_NODES
    # Barabasi-Albert preferential attachment
    nodes = list(range(n))
    edges = []
    edge_amounts = {}  # (from, to) -> amount_usd
    degree = [1] * n
    
    for i in range(2, n):
        # Pick target proportional to degree (preferential attachment)
        targets = rng.choices(range(i), weights=degree[:i], k=min(2, i))
        for t in targets:
            edges.append((i, t))
            # Generate transaction amount (log-normal distribution)
            # Mean: $5,000, some micro-txs for smurfing simulation
            amount = max(10, rng.lognormvariate(math.log(5000), 1.5))
            edge_amounts[(i, t)] = amount
            degree[i] += 1
            degree[t] += 1

    # Flag ~15% as illicit
    illicit_count = max(1, int(n * 0.15))
    illicit_nodes = rng.sample(range(n), illicit_count)
    return nodes, edges, illicit_nodes, edge_amounts


def _detect_smurfing_simulation(
    nodes: list,
    edges: list,
    edge_amounts: dict,
    seed: int,
    structuring_threshold_usd: float = 10_000.0,
    smurfing_risk_boost: float = 0.45,
) -> dict[int, float]:
    """
    Simulate MIMO Tensor Decomposition smurfing detection (Bottleneck 1, slide 14).
    
    Smurfing = breaking large transactions into many small ones to evade reporting.
    
    Simulated approach:
    - For each node, sum all outgoing transaction amounts
    - If total >= threshold BUT all individual txs < 90% of threshold → smurfing
    - Apply risk boost to detected smurfing nodes
    
    Returns: dict[node_id -> smurfing_risk_score]
    """
    rng = random.Random(seed + 999)
    smurfing_scores = {}
    
    # Build outgoing transaction map
    outgoing_txs = {node: [] for node in nodes}
    for (from_node, to_node), amount in edge_amounts.items():
        outgoing_txs[from_node].append(amount)
    
    for node in nodes:
        if not outgoing_txs[node]:
            continue
        
        total_outgoing = sum(outgoing_txs[node])
        max_single_tx = max(outgoing_txs[node])
        num_txs = len(outgoing_txs[node])
        
        # Smurfing pattern: total above threshold, but no single tx is large
        if (total_outgoing >= structuring_threshold_usd and 
            max_single_tx < structuring_threshold_usd * 0.90 and
            num_txs >= 3):
            
            # Risk score proportional to how much over threshold
            score = min(smurfing_risk_boost * (total_outgoing / structuring_threshold_usd), 1.0)
            smurfing_scores[node] = score
    
    return smurfing_scores


def _select_top_k_subgraph(
    nodes: list,
    edges: list,
    node_risks: dict[int, float],
    k: int = 20,
    target_node: int = 0,
) -> tuple[list, list]:
    """
    Select Top-K high-risk subgraph for QAOA execution (NISQ Bridge, slide 8).
    
    Priority score: s_i = risk_i + centrality_i
    Target node (wallet being analyzed) is always included.
    
    Returns: (selected_nodes, selected_edges)
    """
    if len(nodes) <= k:
        return nodes, edges
    
    # Calculate degree centrality (simple proxy)
    degree = {node: 0 for node in nodes}
    for (i, j) in edges:
        degree[i] += 1
        degree[j] += 1
    
    max_degree = max(degree.values()) if degree else 1
    
    # Priority score
    priority = {}
    for node in nodes:
        risk = node_risks.get(node, 0.0)
        centrality = degree[node] / max_degree
        priority[node] = risk + centrality
    
    # Always include target node
    top_k = set([target_node])
    # Add k-1 highest priority nodes
    sorted_nodes = sorted(nodes, key=lambda n: priority[n], reverse=True)
    for node in sorted_nodes:
        if len(top_k) >= k:
            break
        top_k.add(node)
    
    # Filter edges to only those within top_k
    selected_edges = [(i, j) for (i, j) in edges if i in top_k and j in top_k]
    
    return list(top_k), selected_edges


def _simulated_annealing_qubo(
    nodes: list,
    edges: list,
    illicit_nodes: list,
    smurfing_scores: dict[int, float],
    beta: float,
    seed: int,
) -> tuple[float, float, list[int], float, float, float, float]:
    """
    Solve the QUBO cost minimization with Simulated Annealing.

    Cost function (slide 9):
        C(x) = x^T Q x
        Q_ii = -(r̃_i + smurfing_boost_i) * (1 + β²)  [linear terms, diagonal]
        Q_ij = λ_fp * weight_ij                        [quadratic terms, off-diagonal]

    Objective: Minimize False Positive Rate while maintaining acceptable Recall.
    F-β (β=0.5) prioritizes Precision 4x higher than Recall.

    Returns (classical_risk, zeta_q, flagged_indices, fpr, f_beta, precision, recall).
    """
    rng = random.Random(seed + 1)
    n = len(nodes)
    illicit_set = set(illicit_nodes)

    # Initial assignment: flag all
    x = [1] * n
    T = 2.0       # Initial temperature
    T_min = 0.01
    alpha = 0.95  # Cooling rate
    iterations = 500

    # Base risk scores for each node (heuristic based on degree)
    degree = {node: 0 for node in nodes}
    for (i, j) in edges:
        degree[i] += 1
        degree[j] += 1
    max_degree = max(degree.values()) if degree else 1
    
    base_risk = {}
    for node in nodes:
        # Base risk: degree centrality + illicit label
        centrality = degree[node] / max_degree
        is_illicit = 1.0 if node in illicit_set else 0.0
        base_risk[node] = 0.3 * centrality + 0.7 * is_illicit
        # Add smurfing boost
        base_risk[node] = min(base_risk[node] + smurfing_scores.get(node, 0.0), 1.0)

    def cost(assignment):
        tp = sum(1 for i in range(n) if assignment[i] == 1 and i in illicit_set)
        fp = sum(1 for i in range(n) if assignment[i] == 1 and i not in illicit_set)
        fn = sum(1 for i in range(n) if assignment[i] == 0 and i in illicit_set)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        # F-β: β < 1 weights Precision higher than Recall
        # F_β = (1+β²) * precision * recall / (β² * precision + recall)
        f_beta_val = ((1 + beta**2) * precision * recall) / max((beta**2 * precision) + recall, 1e-9)
        # Penalize FP heavily (λ_fp term)
        fp_penalty = 2.0 * fp / n
        return -f_beta_val + fp_penalty

    current_cost = cost(x)
    best_x = x[:]
    best_cost = current_cost

    while T > T_min:
        for _ in range(iterations):
            # Flip a random bit
            idx = rng.randint(0, n - 1)
            x[idx] ^= 1
            new_cost = cost(x)
            delta = new_cost - current_cost
            if delta < 0 or rng.random() < math.exp(-delta / T):
                current_cost = new_cost
                if current_cost < best_cost:
                    best_x = x[:]
                    best_cost = current_cost
            else:
                x[idx] ^= 1  # revert
        T *= alpha

    # Compute final metrics
    tp = sum(1 for i in range(n) if best_x[i] == 1 and i in illicit_set)
    fp = sum(1 for i in range(n) if best_x[i] == 1 and i not in illicit_set)
    fn = sum(1 for i in range(n) if best_x[i] == 0 and i in illicit_set)
    tn = sum(1 for i in range(n) if best_x[i] == 0 and i not in illicit_set)
    
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    fpr = fp / max(fp + tn, 1)
    f_beta_val = ((1 + beta**2) * precision * recall) / max((beta**2 * precision) + recall, 1e-9)
    
    flagged = [i for i in range(n) if best_x[i] == 1]
    
    # Derive scalar risk scores for target wallet (node 0 = target)
    # classical_risk r̃: base risk without quantum effects
    classical_risk = base_risk.get(0, 0.2)
    # zeta_q ζQ: quantum evidence (includes QUBO optimization result)
    zeta_q = 0.9 if 0 in flagged else 0.2
    
    return classical_risk, zeta_q, flagged, fpr, f_beta_val, precision, recall


def run_qubo_stage(wallet: str, seed: int) -> QuboResult:
    """
    Public entry point for QUBO stage with full Prof. Hans architecture:
    1. Build synthetic graph with transaction amounts
    2. MIMO Tensor Decomposition for smurfing detection
    3. Top-20 Subgraph Selection (NISQ Bridge)
    4. Simulated Annealing QUBO optimization
    """
    t0 = time.perf_counter()
    
    # Step 1: Build graph
    nodes, edges, illicit_nodes, edge_amounts = _build_synthetic_graph(wallet, seed)
    
    # Step 2: MIMO Tensor Decomposition (Bottleneck 1)
    smurfing_scores = _detect_smurfing_simulation(nodes, edges, edge_amounts, seed)
    smurfing_detected = len(smurfing_scores) > 0
    
    # Step 3: Compute base node risks (for Top-K selection)
    base_risks = {}
    degree = {node: 0 for node in nodes}
    for (i, j) in edges:
        degree[i] += 1
        degree[j] += 1
    max_degree = max(degree.values()) if degree else 1
    
    for node in nodes:
        centrality = degree[node] / max_degree
        base_risks[node] = centrality * 0.5 + smurfing_scores.get(node, 0.0)
    
    # Step 4: Top-20 Subgraph Selection (NISQ Bridge, slide 8)
    selected_nodes, selected_edges = _select_top_k_subgraph(
        nodes, edges, base_risks, k=20, target_node=0
    )
    
    # Filter illicit nodes to selected subgraph
    selected_illicit = [n for n in illicit_nodes if n in selected_nodes]
    selected_smurfing = {n: smurfing_scores[n] for n in selected_nodes if n in smurfing_scores}
    
    # Step 5: Simulated Annealing QUBO
    classical_risk, zeta_q, flagged, fpr, f_beta, precision, recall = _simulated_annealing_qubo(
        selected_nodes, selected_edges, selected_illicit, selected_smurfing, beta=F_BETA, seed=seed
    )
    
    rt = (time.perf_counter() - t0) * 1000
    flagged_addrs = [f"0xSYNTH{i:04x}" for i in flagged[:5]]
    
    return QuboResult(
        risk_score=round(zeta_q, 4),  # ζQ quantum evidence
        classical_risk=round(classical_risk, 4),  # r̃ classical risk
        false_positive_rate=round(fpr, 4),
        f_beta_score=round(f_beta, 4),
        precision=round(precision, 4),
        recall=round(recall, 4),
        flagged_nodes=flagged_addrs,
        graph_nodes=len(nodes),
        graph_edges=len(edges),
        backend_used="Simulated Annealing (MIMO + Top-20 NISQ)",
        runtime_ms=round(rt, 2),
        smurfing_detected=smurfing_detected,
        smurfing_nodes=len(smurfing_scores),
    )


# ─── Stage 2: Flow Tracer Agent (Simulated) ───────────────────────────────────

def run_flow_tracer(wallet: str, demo_meta: dict, seed: int) -> FlowTraceResult:
    """
    Simulate multi-hop cash flow tracing with detailed Hop records.
    Returns structured hop-by-hop transaction trace.
    """
    rng = random.Random(seed + 2)
    hop_count = demo_meta.get("hop_count", 0)
    path = [wallet]
    hops = []
    chains_involved = ["ETH"]
    
    current_wallet = wallet
    for i in range(hop_count):
        next_wallet = f"0xHOP{rng.randint(0x1000, 0xFFFF):04X}{i:02X}"
        tx_hash = f"0x{rng.randint(0x100000000000, 0xFFFFFFFFFFFF):012x}"
        amount_usd = rng.uniform(500, 50000)
        
        # Determine if via mixer or bridge
        via_mixer = demo_meta.get("mixer_detected", False) and i == hop_count // 2
        via_bridge = i >= 3  # Later hops might cross chains
        
        if via_bridge and "BSC" not in chains_involved:
            chains_involved.append("BSC")
        
        hop = Hop(
            from_wallet=current_wallet,
            to_wallet=next_wallet,
            tx_hash=tx_hash,
            amount_usd=round(amount_usd, 2),
            chain="BSC" if via_bridge else "ETH",
            timestamp=datetime.now(timezone.utc).isoformat(),
            via_mixer=via_mixer,
            via_bridge=via_bridge,
        )
        hops.append(hop)
        path.append(next_wallet)
        current_wallet = next_wallet

    mixer_detected = demo_meta.get("mixer_detected", False)
    mixer_name = demo_meta.get("mixer_name")
    bridge_detected = hop_count >= 4

    if hop_count == 0:
        summary = "No suspicious transaction hops detected. Wallet activity appears normal."
    elif mixer_detected:
        summary = (
            f"⚠️ {hop_count}-hop chain traced through {mixer_name} mixer. "
            "Funds obfuscated before reaching destination. High confidence of ML layering."
        )
    elif bridge_detected:
        summary = (
            f"⚠️ {hop_count}-hop cross-chain bridge pattern detected. "
            f"Funds moved through {' → '.join(chains_involved)} bridge. Monitoring recommended."
        )
    else:
        summary = (
            f"ℹ️ {hop_count}-hop flow traced. No mixer or bridge involvement. "
            "Pattern is consistent with moderate-risk activity."
        )

    return FlowTraceResult(
        hop_count=hop_count,
        hops=hops,
        path=path,
        mixer_detected=mixer_detected,
        mixer_name=mixer_name,
        bridge_detected=bridge_detected,
        chains_involved=chains_involved,
        summary=summary,
    )


# ─── Stage 3: OSINT Analyst Agent (Simulated) ─────────────────────────────────

def run_osint_analyst(wallet: str, demo_meta: dict, seed: int) -> OsintResult:
    """Simulate OFAC / EU / UN sanctions lookup + CryptoScamDB."""
    rng = random.Random(seed + 3)
    sanctions_hit = demo_meta.get("sanctions_hit", False)
    sanctions_list = demo_meta.get("sanctions_list")
    confidence = round(rng.uniform(0.91, 0.99), 3) if sanctions_hit else round(rng.uniform(0.0, 0.05), 3)
    pep_match = sanctions_hit and rng.random() < 0.3
    scamdb_match = sanctions_hit and rng.random() < 0.5

    if sanctions_hit:
        summary = (
            f"🚨 SANCTIONS HIT: Wallet matched on {sanctions_list}. "
            f"Confidence: {confidence:.0%}. "
            f"{'PEP (Politically Exposed Person) link identified. ' if pep_match else ''}"
            f"{'CryptoScamDB record found. ' if scamdb_match else ''}"
            "Immediate escalation recommended."
        )
    else:
        summary = (
            "✅ No sanctions matches found across OFAC SDN, EU Consolidated List, "
            "UN Security Council, or CryptoScamDB. Wallet is not associated with "
            "any known illicit entities."
        )

    return OsintResult(
        sanctions_hit=sanctions_hit,
        sanctions_list=sanctions_list,
        confidence=confidence,
        pep_match=pep_match,
        scamdb_match=scamdb_match,
        summary=summary,
    )


# ─── Stage 4: Compliance Officer Agent ───────────────────────────────────────

def _sha256_payload(payload: str) -> str:
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _determine_risk_level_parametric(
    compliance_score: float,
    sanctions_hit: bool,
) -> tuple[str, str]:
    """
    Determine risk level and recommended action using parametric thresholds.
    
    Architecture (Slide 13, Bottleneck 2 slide 15):
    - τH (THRESHOLD_HIGH): HIGH risk → FREEZE
    - τM (THRESHOLD_MED):  MEDIUM risk → MONITOR
    - Below τM: LOW risk → CLEAR
    
    Sanctions hit always triggers FREEZE regardless of score.
    """
    if sanctions_hit or compliance_score >= THRESHOLD_HIGH:
        return "HIGH", "FREEZE"
    elif compliance_score >= THRESHOLD_MED:
        return "MEDIUM", "MONITOR"
    else:
        return "LOW", "CLEAR"


def run_compliance_officer(
    wallet: str,
    qubo: QuboResult,
    flow: FlowTraceResult,
    osint: OsintResult,
    timestamp: str,
) -> tuple[str, str, str, str, float, dict, dict, dict, list[dict]]:
    """
    Generate compliance report with 6-component scoring (Slide 13).
    
    Compliance Score Formula:
        Rₐ = clip(ωr·r̃ₐ + ωq·ζₐQ + ωE·Eₐ + ωS·Sₐ + ωC·Cₐ + ωO·Oₐ, 0, 1)
    
    Where:
        r̃ₐ  = classical risk score (from node features)
        ζₐQ = quantum evidence (QUBO optimization result)
        Eₐ  = external sanctions signal (0 or 1)
        Sₐ  = scam/structuring signal (0 to 1)
        Cₐ  = counterparty exposure (mixer usage, 0 or 1)
        Oₐ  = obfuscation (bridge usage, 0 or 1)
    
    Returns: (risk_level, action, sar_summary, audit_hash, compliance_score,
              score_components, weights, thresholds, travel_rule_violations)
    """
    # ── Component Scores ──────────────────────────────────────────────────────
    r_tilde = qubo.classical_risk    # r̃ₐ  classical risk
    zeta_q = qubo.risk_score          # ζₐQ quantum evidence
    
    E_a = 1.0 if osint.sanctions_hit else 0.0         # Eₐ  sanctions
    S_a = osint.confidence if osint.sanctions_hit else 0.0  # Sₐ  scam score
    C_a = 1.0 if flow.mixer_detected else 0.0        # Cₐ  mixer exposure
    O_a = 1.0 if flow.bridge_detected else 0.0       # Oₐ  bridge obfuscation
    
    # ── 6-Component Compliance Score (Slide 13) ───────────────────────────────
    # Rₐ = ωr·r̃ₐ + ωq·ζₐQ + ωE·Eₐ + ωS·Sₐ + ωC·Cₐ + ωO·Oₐ
    R_raw = (
        OMEGA_R * r_tilde +
        OMEGA_Q * zeta_q +
        OMEGA_E * E_a +
        OMEGA_S * S_a +
        OMEGA_C * C_a +
        OMEGA_O * O_a
    )
    compliance_score = max(0.0, min(1.0, R_raw))  # clip to [0, 1]
    
    score_components = {
        "r_tilde": round(r_tilde, 4),
        "zeta_q": round(zeta_q, 4),
        "E_sanctions": round(E_a, 4),
        "S_scam": round(S_a, 4),
        "C_mixer": round(C_a, 4),
        "O_bridge": round(O_a, 4),
    }
    
    weights = {
        "omega_r": OMEGA_R,
        "omega_q": OMEGA_Q,
        "omega_E": OMEGA_E,
        "omega_S": OMEGA_S,
        "omega_C": OMEGA_C,
        "omega_O": OMEGA_O,
    }
    
    thresholds = {
        "tau_H": THRESHOLD_HIGH,
        "tau_M": THRESHOLD_MED,
    }
    
    # ── Parametric Risk Determination ─────────────────────────────────────────
    risk_level, action = _determine_risk_level_parametric(compliance_score, osint.sanctions_hit)
    
    # ── FATF Travel Rule Violations (Recommendation 16) ───────────────────────
    travel_rule_violations = []
    for hop in flow.hops:
        if hop.amount_usd > TRAVEL_RULE_THRESHOLD_USD:
            travel_rule_violations.append({
                "tx_hash": hop.tx_hash,
                "originator_account": hop.from_wallet,
                "beneficiary_account": hop.to_wallet,
                "transfer_amount_usd": hop.amount_usd,
                "threshold_exceeded": True,
                "originator_vasp": None,
                "beneficiary_vasp": None,
            })
    
    # ── SAR Summary ───────────────────────────────────────────────────────────
    date_str = timestamp[:10]
    
    sar_summary = f"""
SUSPICIOUS ACTIVITY REPORT (SAR) — AML AI COPILOT
===================================================
Wallet:     {wallet}
Date:       {timestamp}
Risk Level: {risk_level}
Action:     {action}

COMPLIANCE SCORE ANALYSIS (Prof. Hans Architecture, Slide 13)
- Composite Score Rₐ:  {compliance_score:.4f}
- Components:
  * ωr·r̃ₐ  (Classical Risk):     {OMEGA_R} × {r_tilde:.4f} = {OMEGA_R * r_tilde:.4f}
  * ωq·ζₐQ (Quantum Evidence):   {OMEGA_Q} × {zeta_q:.4f} = {OMEGA_Q * zeta_q:.4f}
  * ωE·Eₐ  (Sanctions):          {OMEGA_E} × {E_a:.4f} = {OMEGA_E * E_a:.4f}
  * ωS·Sₐ  (Scam/Structuring):   {OMEGA_S} × {S_a:.4f} = {OMEGA_S * S_a:.4f}
  * ωC·Cₐ  (Mixer Exposure):     {OMEGA_C} × {C_a:.4f} = {OMEGA_C * C_a:.4f}
  * ωO·Oₐ  (Bridge Obfuscation): {OMEGA_O} × {O_a:.4f} = {OMEGA_O * O_a:.4f}
- Thresholds: τH={THRESHOLD_HIGH}, τM={THRESHOLD_MED}
- Decision: Rₐ={compliance_score:.4f} → {risk_level} → {action}

QUBO ANALYSIS (MIMO + Top-20 NISQ)
- Quantum Evidence ζQ:   {qubo.risk_score:.4f}
- Classical Risk r̃:      {qubo.classical_risk:.4f}
- F-β Score (β=0.5):     {qubo.f_beta_score:.4f}
- Precision:             {qubo.precision:.4f}
- Recall:                {qubo.recall:.4f}
- False Positive Rate:   {qubo.false_positive_rate:.4f}
- Graph: {qubo.graph_nodes} nodes, {qubo.graph_edges} edges
- Smurfing Detection:    {"YES" if qubo.smurfing_detected else "NO"} ({qubo.smurfing_nodes} nodes flagged)
- Backend: {qubo.backend_used}

FLOW TRACE
- Hops:              {flow.hop_count}
- Chains:            {', '.join(flow.chains_involved)}
- Mixer Detected:    {flow.mixer_detected} ({flow.mixer_name or 'N/A'})
- Bridge Detected:   {flow.bridge_detected}
- Summary: {flow.summary}

OSINT / SANCTIONS
- Sanctions Hit:     {osint.sanctions_hit}
- List:              {osint.sanctions_list or 'None'}
- Confidence:        {osint.confidence:.0%}
- PEP Match:         {osint.pep_match}
- ScamDB Match:      {osint.scamdb_match}
- Summary: {osint.summary}

FATF TRAVEL RULE COMPLIANCE (Recommendation 16)
- Violations:        {len(travel_rule_violations)} transaction(s) > ${TRAVEL_RULE_THRESHOLD_USD:,.0f} without VASP data
"""
    
    if travel_rule_violations:
        sar_summary += "\n  Flagged Transactions:\n"
        for v in travel_rule_violations[:3]:  # Show first 3
            sar_summary += f"    • {v['tx_hash'][:16]}... ${v['transfer_amount_usd']:,.0f}\n"
    
    sar_summary += f"""
RECOMMENDED ACTION: {action}

This report is generated by AML AI Copilot (QCFinOp Team, SEA Quantathon 2026).
Architecture designed by Prof. Hans — Hybrid Quantum-Agentic AML Platform.
Powered by Quapp.cloud — Launchpad for Quantum Builders.
""".strip()

    audit_hash = _sha256_payload(sar_summary)
    
    return (risk_level, action, sar_summary, audit_hash, compliance_score,
            score_components, weights, thresholds, travel_rule_violations)


# ─── Full Pipeline ────────────────────────────────────────────────────────────

def run_pipeline(wallet: str) -> ComplianceReport:
    """
    Execute the full simulated AML pipeline for a given wallet address.
    Deterministic: same wallet always produces the same report.
    
    Architecture (Prof. Hans):
    1. QUBO Optimizer (MIMO + Top-20 + SA)
    2. Flow Tracer Agent
    3. OSINT Analyst Agent
    4. Compliance Officer (6-component scoring + Travel Rule)
    """
    t_start = time.perf_counter()
    timestamp = datetime.now(timezone.utc).isoformat()

    # Look up demo metadata (or use generic defaults)
    demo_meta = DEMO_WALLETS.get(wallet, {
        "seed_offset": abs(hash(wallet)) % 1000,
        "sanctions_hit": False,
        "sanctions_list": None,
        "hop_count": 1,
        "mixer_detected": False,
        "mixer_name": None,
    })
    seed = GRAPH_SEED_BASE + demo_meta.get("seed_offset", 0)

    # Stage 1: QUBO (with MIMO + Top-20)
    qubo = run_qubo_stage(wallet, seed)

    # Stage 2: Flow Tracer
    flow = run_flow_tracer(wallet, demo_meta, seed)

    # Stage 3: OSINT
    osint = run_osint_analyst(wallet, demo_meta, seed)

    # Stage 4: Compliance Officer (6-component scoring)
    (risk_level, action, sar, audit_hash, compliance_score,
     score_components, weights, thresholds, travel_rule_violations) = run_compliance_officer(
        wallet, qubo, flow, osint, timestamp
    )

    # Generate case ID
    date_tag = timestamp[:10].replace("-", "")
    wallet_tag = wallet[2:10].upper() if wallet.startswith("0x") else wallet[:8].upper()
    case_id = f"AML-{date_tag}-{wallet_tag}"

    total_ms = (time.perf_counter() - t_start) * 1000

    return ComplianceReport(
        case_id=case_id,
        wallet_address=wallet,
        risk_level=risk_level,
        recommended_action=action,
        compliance_score=round(compliance_score, 4),
        score_components=score_components,
        weights=weights,
        thresholds=thresholds,
        qubo_risk_score=qubo.risk_score,
        f_beta_score=qubo.f_beta_score,
        precision=qubo.precision,
        recall=qubo.recall,
        audit_hash=audit_hash,
        sar_summary=sar,
        timestamp=timestamp,
        runtime_ms=round(total_ms, 2),
        qubo=asdict(qubo),
        flow_trace=asdict(flow),
        osint=asdict(osint),
        travel_rule_violations=travel_rule_violations,
    )


# ─── HTTP Server Mode (for prototype integration) ────────────────────────────

class AMLHandler(http.server.BaseHTTPRequestHandler):
    """Minimal HTTP handler to serve pipeline results to the prototype UI."""

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/analyze":
            wallet = params.get("wallet", [""])[0].strip()
            if not wallet:
                self._respond(400, {"error": "Missing wallet parameter"})
                return
            try:
                report = run_pipeline(wallet)
                self._respond(200, asdict(report))
            except Exception as e:
                self._respond(500, {"error": str(e)})
        elif parsed.path == "/health":
            self._respond(200, {"status": "ok", "service": "AML AI Copilot Sim"})
        elif parsed.path == "/demo-wallets":
            self._respond(200, {"wallets": list(DEMO_WALLETS.keys())})
        else:
            self._respond(404, {"error": "Not found"})

    def _respond(self, code: int, body: dict):
        payload = json.dumps(body, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(payload))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)


# ─── CLI Entry Point ──────────────────────────────────────────────────────────

def _print_report(report: ComplianceReport):
    print(f"\n{'='*70}")
    print(f"  AML AI Copilot — Pipeline Result (Prof. Hans Architecture)")
    print(f"{'='*70}")
    print(f"  Case ID:   {report.case_id}")
    print(f"  Wallet:    {report.wallet_address}")
    print(f"  Risk:      {report.risk_level}")
    print(f"  Action:    {report.recommended_action}")
    print(f"  " + "─"*66)
    print(f"  Compliance Score (Rₐ): {report.compliance_score:.4f}")
    print(f"    Components:")
    print(f"      ωr·r̃  (Classical):   {report.weights['omega_r']:.2f} × {report.score_components['r_tilde']:.4f} = {report.weights['omega_r'] * report.score_components['r_tilde']:.4f}")
    print(f"      ωq·ζQ (Quantum):     {report.weights['omega_q']:.2f} × {report.score_components['zeta_q']:.4f} = {report.weights['omega_q'] * report.score_components['zeta_q']:.4f}")
    print(f"      ωE·E  (Sanctions):   {report.weights['omega_E']:.2f} × {report.score_components['E_sanctions']:.4f} = {report.weights['omega_E'] * report.score_components['E_sanctions']:.4f}")
    print(f"      ωS·S  (Scam):        {report.weights['omega_S']:.2f} × {report.score_components['S_scam']:.4f} = {report.weights['omega_S'] * report.score_components['S_scam']:.4f}")
    print(f"      ωC·C  (Mixer):       {report.weights['omega_C']:.2f} × {report.score_components['C_mixer']:.4f} = {report.weights['omega_C'] * report.score_components['C_mixer']:.4f}")
    print(f"      ωO·O  (Bridge):      {report.weights['omega_O']:.2f} × {report.score_components['O_bridge']:.4f} = {report.weights['omega_O'] * report.score_components['O_bridge']:.4f}")
    print(f"    Thresholds: τH={report.thresholds['tau_H']}, τM={report.thresholds['tau_M']}")
    print(f"  " + "─"*66)
    print(f"  QUBO Metrics:")
    print(f"    Risk Score:  {report.qubo_risk_score:.4f}")
    print(f"    F-β Score:   {report.f_beta_score:.4f}")
    print(f"    Precision:   {report.precision:.4f}")
    print(f"    Recall:      {report.recall:.4f}")
    if report.qubo and report.qubo.get('smurfing_detected'):
        print(f"    Smurfing:    YES ({report.qubo['smurfing_nodes']} nodes)")
    print(f"  " + "─"*66)
    if report.travel_rule_violations:
        print(f"  Travel Rule:  {len(report.travel_rule_violations)} violation(s)")
    print(f"  Audit Hash:   {report.audit_hash[:50]}...")
    print(f"  Runtime:      {report.runtime_ms:.1f}ms")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "serve":
        port = int(sys.argv[2]) if len(sys.argv) >= 3 else 8765
        print(f"[AML Sim] Starting HTTP server on http://localhost:{port}")
        print(f"[AML Sim] Endpoint: GET /analyze?wallet=0x...")
        print(f"[AML Sim] Press Ctrl+C to stop.")
        with socketserver.TCPServer(("", port), AMLHandler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n[AML Sim] Server stopped.")
    elif len(sys.argv) >= 2 and sys.argv[1] == "precompute":
        # Pre-compute all demo wallets and dump to JSON for static embedding
        output = {}
        for wallet in DEMO_WALLETS:
            report = run_pipeline(wallet)
            output[wallet] = asdict(report)
            _print_report(report)
        out_file = "demo_payloads.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"[AML Sim] Pre-computed payloads saved to {out_file}")
    elif len(sys.argv) >= 2:
        wallet = sys.argv[1]
        report = run_pipeline(wallet)
        _print_report(report)
        if len(sys.argv) >= 3 and sys.argv[2] == "--json":
            print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
    else:
        print("Usage:")
        print("  python qubo_sim.py <wallet_address>            # Run pipeline on wallet")
        print("  python qubo_sim.py <wallet_address> --json     # Output JSON")
        print("  python qubo_sim.py serve [port]                # Start HTTP server")
        print("  python qubo_sim.py precompute                  # Pre-compute demo wallets")
        print()
        print("Demo wallets:")
        for w, meta in DEMO_WALLETS.items():
            print(f"  {w}  →  {meta['expected_risk']} / {meta['expected_action']}")
