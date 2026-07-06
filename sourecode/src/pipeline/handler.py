"""
Quapp Function Entrypoint — AML AI Copilot
==========================================
This is the handler.py file that Quapp.cloud loads as the Function entrypoint
during Step 4 (Review the Code) of the deployment workflow.

Quapp invokes handler(event) for each Job execution.

Expected event schema:
    {
        "wallet_address": str,   # EIP-55 checksummed Ethereum wallet
        "backend":        str,   # "classical" | "qudora" | "quandela" | "ibm_quantum"
        "shots":          int,   # Number of quantum circuit runs (default: 1024)
        "mode":           str    # "hybrid" | "classical" | "quantum_sim"
    }

Returns:
    {
        "status":             str,   # "success" | "error"
        "case_id":            str,   # e.g. "AML-20260704-A1B2C3D4"
        "wallet_address":     str,
        "risk_level":         str,   # "HIGH" | "MEDIUM" | "LOW"
        "recommended_action": str,   # "FREEZE" | "MONITOR" | "CLEAR"
        "f_beta_score":       float, # F-β (β=0.5)
        "qubo_risk_score":    float,
        "audit_hash":         str,   # SHA-256 of compliance report
        "trace_id":           str,
        "runtime_seconds":    float,
        "error":              str | None
    }
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any

import networkx as nx

from src.config import (
    F_BETA,
    ETHERSCAN_API_KEY,
    QUANTUM_BACKEND,
    QUBO_RISK_THRESHOLD,
)
from src.models import AgentInput, TransactionGraph
from src.quantum.hybrid_optimizer import HybridQuantumOptimizer
from src.agents.multi_agent_crew import run_aml_crew
import logging

from src.security import validate_wallet_address

logger = logging.getLogger(__name__)

# ─── Backend Mapping ──────────────────────────────────────────────────────────
# Maps Quapp provider names (as selected in the Job Invocation UI)
# to internal backend_choice keys used by HybridQuantumOptimizer.

_QUAPP_PROVIDER_MAP: dict[str, str] = {
    # Quapp UI provider name  →  internal backend key
    "quapp":      "classical",   # Quapp default (classical SA)
    "classical":  "classical",   # explicit classical
    "quandela":   "quandela",    # Perceval photonic SDK
    "qudora":     "qudora",      # Qamelion trapped-ion emulator
    "ibm_quantum": "classical",  # IBM Quantum — fallback to classical until Qiskit wired
    "ibm":        "classical",
}

_VALID_MODES = {"hybrid", "classical", "quantum_sim"}


# ─── Input Validation ─────────────────────────────────────────────────────────

def _validate_event(event: dict) -> tuple[str, str, int, str]:
    """
    Parse and validate the Quapp event payload.

    Returns:
        (wallet_address, backend_key, shots, mode)

    Raises:
        ValueError: if required fields are missing or invalid.
    """
    wallet = event.get("wallet_address", "").strip()
    if not wallet:
        raise ValueError("Missing required field: 'wallet_address'")

    # Validate wallet format (EIP-55 checksum via security module).
    # validate_wallet_address raises ValueError on bad input, returns normalised addr.
    try:
        wallet = validate_wallet_address(wallet)
    except ValueError as exc:
        raise ValueError(f"Invalid wallet address: {exc}") from exc

    # Resolve provider → backend key
    raw_backend = str(event.get("backend", QUANTUM_BACKEND)).lower()
    backend_key = _QUAPP_PROVIDER_MAP.get(raw_backend, "classical")
    if raw_backend not in _QUAPP_PROVIDER_MAP:
        logger.warning(
            f"Unknown backend '{raw_backend}' — defaulting to 'classical'. "
            f"Supported: {list(_QUAPP_PROVIDER_MAP.keys())}"
        )

    # shots: number of quantum circuit runs (informational for now)
    shots = int(event.get("shots", 1024))
    if shots < 1:
        raise ValueError(f"'shots' must be >= 1, got {shots}")

    # mode
    mode = str(event.get("mode", "hybrid")).lower()
    if mode not in _VALID_MODES:
        logger.warning(f"Unknown mode '{mode}' — defaulting to 'hybrid'.")
        mode = "hybrid"

    return wallet, backend_key, shots, mode


# ─── QUBO Risk Scoring ────────────────────────────────────────────────

def _run_qubo_stage(
    wallet_address: str,
    backend_key: str,
    trace_id: str,
) -> tuple[float, list[str]]:
    """
    Build a transaction graph for the target wallet and run QUBO optimization.

    Strategy:
        1. If ETHERSCAN_API_KEY is set → build live graph from Etherscan (production)
        2. Fallback: deterministic demo graph (Barabasi-Albert) for offline testing

    Returns:
        (qubo_risk_score, flagged_nodes)
    """
    from src.data.etherscan_graph_builder import build_tx_graph_from_wallet, build_demo_graph

    logger.info(
        f"[QUBO] Building transaction graph for {wallet_address} "
        f"| backend={backend_key} | trace_id={trace_id}"
    )

    # ── Choose data source ──────────────────────────────────────────────────────────────────
    if ETHERSCAN_API_KEY:
        logger.info("[QUBO] ETHERSCAN_API_KEY found — fetching live blockchain data")
        try:
            tx_graph = build_tx_graph_from_wallet(
                wallet_address=wallet_address,
                chain="eth",
                hops=2,
                max_nodes=150,
            )
        except Exception as exc:
            logger.warning(f"[QUBO] Live data fetch failed: {exc}. Falling back to demo graph.")
            tx_graph = build_demo_graph(wallet_address)
    else:
        logger.info("[QUBO] No ETHERSCAN_API_KEY — using deterministic demo graph (Barabasi-Albert)")
        tx_graph = build_demo_graph(wallet_address)

    # ── Run QUBO optimization ─────────────────────────────────────────────────────────────
    optimizer = HybridQuantumOptimizer(backend_choice=backend_key)
    opt_result = optimizer.optimize(tx_graph, beta=F_BETA)

    # Derive a scalar risk score for the target wallet
    risk_score = opt_result.risk_scores.get(wallet_address.lower(), 0.0)
    # If wallet was flagged at all, ensure score exceeds threshold
    if wallet_address.lower() in [w.lower() for w in opt_result.flagged_wallets]:
        risk_score = max(risk_score, QUBO_RISK_THRESHOLD + 0.05)

    logger.info(
        f"[QUBO] Done | FPR={opt_result.false_positive_rate:.3f} "
        f"| F-β={opt_result.f_beta_score:.3f} "
        f"| risk_score={risk_score:.3f} | flagged={len(opt_result.flagged_wallets)} wallets"
    )
    return risk_score, opt_result.flagged_wallets


# ─── Main Handler ─────────────────────────────────────────────────────────────

def handler(event: dict[str, Any]) -> dict[str, Any]:
    """
    Quapp Function entrypoint for AML AI Copilot.

    Invoked by Quapp.cloud for each Job execution. Runs the full
    Hybrid Quantum-Agentic AML pipeline end-to-end:

        Wallet Input
            │
            ▼
        QUBO Optimizer  (graph → QUBO → quantum/classical solve)
            │  risk_score > QUBO_RISK_THRESHOLD
            ▼
        CrewAI Agents   (Flow Tracer → OSINT → Compliance Officer)
            │
            ▼
        Compliance Report (risk_level, action, SHA-256 audit_hash)

    Args:
        event: Quapp Job payload (see module docstring for schema).

    Returns:
        Result dict (see module docstring for schema).
    """
    pipeline_start = time.perf_counter()
    trace_id = str(uuid.uuid4())

    logger.info(
        f"[Handler] Quapp Job received | trace_id={trace_id} | event={event}"
    )

    # ── 1. Validate Input ──────────────────────────────────────────────────────
    try:
        wallet_address, backend_key, shots, mode = _validate_event(event)
    except ValueError as exc:
        logger.error(f"[Handler] Input validation failed: {exc}")
        return {
            "status": "error",
            "error": str(exc),
            "trace_id": trace_id,
            "wallet_address": event.get("wallet_address", ""),
        }

    logger.info(
        f"[Handler] Pipeline start | wallet={wallet_address} "
        f"| backend={backend_key} | shots={shots} | mode={mode}"
    )

    # ── 2. QUBO Optimization Stage ────────────────────────────────────────────
    try:
        qubo_risk_score, flagged_nodes = _run_qubo_stage(
            wallet_address, backend_key, trace_id
        )
    except Exception as exc:
        logger.error(f"[Handler] QUBO stage failed: {exc}", exc_info=True)
        return {
            "status": "error",
            "error": f"QUBO stage failed: {exc}",
            "trace_id": trace_id,
            "wallet_address": wallet_address,
        }

    # ── 3. Agent Investigation Stage (if risk exceeds threshold) ──────────────
    report = None
    if qubo_risk_score >= QUBO_RISK_THRESHOLD or mode == "hybrid":
        logger.info(
            f"[Handler] Activating CrewAI agents | "
            f"qubo_risk_score={qubo_risk_score:.3f} >= threshold={QUBO_RISK_THRESHOLD}"
        )
        try:
            agent_input = AgentInput(
                wallet_address=wallet_address,
                qubo_risk_score=qubo_risk_score,
                qubo_flagged_nodes=flagged_nodes,
                trace_id=trace_id,
            )
            report = run_aml_crew(agent_input)
        except Exception as exc:
            logger.error(f"[Handler] Agent stage failed: {exc}", exc_info=True)
            # Degrade gracefully: return QUBO result without agent enrichment
            elapsed = time.perf_counter() - pipeline_start
            return {
                "status": "partial",
                "case_id": f"AML-PARTIAL-{trace_id[:8].upper()}",
                "wallet_address": wallet_address,
                "risk_level": "HIGH" if qubo_risk_score >= QUBO_RISK_THRESHOLD else "LOW",
                "recommended_action": "MONITOR",
                "qubo_risk_score": round(qubo_risk_score, 4),
                "f_beta_score": None,
                "audit_hash": None,
                "trace_id": trace_id,
                "runtime_seconds": round(elapsed, 3),
                "error": f"Agent stage degraded: {exc}",
            }
    else:
        # Low risk — QUBO alone is sufficient, no agent activation needed
        logger.info(
            f"[Handler] Risk score {qubo_risk_score:.3f} below threshold "
            f"{QUBO_RISK_THRESHOLD} — skipping agent stage."
        )

    # ── 4. Build Response ─────────────────────────────────────────────────────
    elapsed = time.perf_counter() - pipeline_start

    if report:
        result = {
            "status": "success",
            "case_id": report.case_id,
            "wallet_address": report.wallet_address,
            "risk_level": report.risk_level,
            "recommended_action": report.recommended_action,
            "qubo_risk_score": round(qubo_risk_score, 4),
            "f_beta_score": report.f_beta_score,
            "audit_hash": report.audit_hash,
            "trace_id": trace_id,
            "runtime_seconds": round(elapsed, 3),
            "error": None,
        }
    else:
        # Low-risk fast path (no agents activated)
        result = {
            "status": "success",
            "case_id": f"AML-CLEAR-{trace_id[:8].upper()}",
            "wallet_address": wallet_address,
            "risk_level": "LOW",
            "recommended_action": "CLEAR",
            "qubo_risk_score": round(qubo_risk_score, 4),
            "f_beta_score": None,
            "audit_hash": None,
            "trace_id": trace_id,
            "runtime_seconds": round(elapsed, 3),
            "error": None,
        }

    logger.info(
        f"[Handler] Job complete | case_id={result['case_id']} "
        f"| risk={result['risk_level']} | action={result['recommended_action']} "
        f"| runtime={elapsed:.2f}s | trace_id={trace_id}"
    )
    return result
