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

PIPELINE SIMULATED
------------------
1. QUBO Optimizer  — Simulated Annealing on synthetic scale-free graph
2. Flow Tracer     — Deterministic multi-hop path simulation
3. OSINT Analyst   — Sanctions list mock lookup
4. Compliance Ofcr — SAR summary + SHA-256 audit hash

DESIGN PRINCIPLES (Senior Dev Notes)
--------------------------------------
- Fully deterministic: same wallet → same score every run (reproducible demo)
- No external I/O: zero HTTP calls, zero disk I/O except optional JSON dump
- Type-safe: full dataclass / TypedDict schema
- Testable: each stage is a pure function with no side effects
- Demo-ready: 4 canonical test wallets with pre-tuned expected outputs
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


# ─── Data Models ──────────────────────────────────────────────────────────────

@dataclass
class QuboResult:
    """Output from the QUBO Simulated Annealing stage."""
    risk_score: float           # 0.0 – 1.0
    false_positive_rate: float
    f_beta_score: float
    flagged_nodes: list[str]
    graph_nodes: int
    graph_edges: int
    backend_used: str
    runtime_ms: float


@dataclass
class FlowTraceResult:
    """Output from the multi-hop Flow Tracer agent."""
    hop_count: int
    path: list[str]
    mixer_detected: bool
    mixer_name: Optional[str]
    bridge_detected: bool
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
class ComplianceReport:
    """Output from the AI Compliance Officer agent."""
    case_id: str
    wallet_address: str
    risk_level: str           # HIGH | MEDIUM | LOW
    recommended_action: str   # FREEZE | MONITOR | CLEAR
    qubo_risk_score: float
    f_beta_score: float
    audit_hash: str           # SHA-256
    sar_summary: str
    timestamp: str
    runtime_ms: float
    qubo: Optional[dict] = field(default=None)
    flow_trace: Optional[dict] = field(default=None)
    osint: Optional[dict] = field(default=None)


# ─── Stage 1: QUBO Simulated Annealing ───────────────────────────────────────

def _build_synthetic_graph(wallet: str, seed: int) -> tuple[list, list, list]:
    """
    Generate a deterministic scale-free transaction graph.
    Returns (nodes, edges, illicit_nodes).
    """
    rng = random.Random(seed)
    n = GRAPH_NODES
    # Barabasi-Albert preferential attachment
    nodes = list(range(n))
    edges = []
    degree = [1] * n
    for i in range(2, n):
        # Pick target proportional to degree (preferential attachment)
        targets = rng.choices(range(i), weights=degree[:i], k=min(2, i))
        for t in targets:
            edges.append((i, t))
            degree[i] += 1
            degree[t] += 1

    # Flag ~15% as illicit
    illicit_count = max(1, int(n * 0.15))
    illicit_nodes = rng.sample(range(n), illicit_count)
    return nodes, edges, illicit_nodes


def _simulated_annealing_qubo(
    nodes: list,
    edges: list,
    illicit_nodes: list,
    beta: float,
    seed: int,
) -> tuple[float, list[int], float, float]:
    """
    Solve the QUBO cost minimization with Simulated Annealing.

    Cost: C(x) = -Σ precision_i*x_i + λ*Σ fp_ij*x_i*x_j
    We minimize FPR while maintaining recall.

    Returns (risk_score, flagged_indices, fpr, f_beta).
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

    def cost(assignment):
        tp = sum(1 for i in range(n) if assignment[i] == 1 and i in illicit_set)
        fp = sum(1 for i in range(n) if assignment[i] == 1 and i not in illicit_set)
        fn = sum(1 for i in range(n) if assignment[i] == 0 and i in illicit_set)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        # Penalize FP heavily (β=0.5: precision weighted 4x recall in denominator)
        fp_penalty = 2.0 * fp / n
        return -(((1 + beta**2) * precision * recall) /
                 max((beta**2 * precision) + recall, 1e-9)) + fp_penalty

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
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    fpr = fp / max(len(nodes) - len(illicit_nodes), 1)
    f_beta = ((1 + beta**2) * precision * recall) / max((beta**2 * precision) + recall, 1e-9)
    flagged = [i for i in range(n) if best_x[i] == 1]
    # Derive scalar risk score for target wallet (node 0 = target)
    risk_score = 0.9 if 0 in flagged else 0.2
    return risk_score, flagged, fpr, f_beta


def run_qubo_stage(wallet: str, seed: int) -> QuboResult:
    """Public entry point for QUBO stage."""
    t0 = time.perf_counter()
    nodes, edges, illicit_nodes = _build_synthetic_graph(wallet, seed)
    risk_score, flagged, fpr, f_beta = _simulated_annealing_qubo(
        nodes, edges, illicit_nodes, beta=F_BETA, seed=seed
    )
    rt = (time.perf_counter() - t0) * 1000
    flagged_addrs = [f"0xSYNTH{i:04x}" for i in flagged[:5]]
    return QuboResult(
        risk_score=round(risk_score, 4),
        false_positive_rate=round(fpr, 4),
        f_beta_score=round(f_beta, 4),
        flagged_nodes=flagged_addrs,
        graph_nodes=len(nodes),
        graph_edges=len(edges),
        backend_used="Simulated Annealing (D-Wave dimod style)",
        runtime_ms=round(rt, 2),
    )


# ─── Stage 2: Flow Tracer Agent (Simulated) ───────────────────────────────────

def run_flow_tracer(wallet: str, demo_meta: dict, seed: int) -> FlowTraceResult:
    """Simulate multi-hop cash flow tracing."""
    rng = random.Random(seed + 2)
    hop_count = demo_meta.get("hop_count", 0)
    path = [wallet]
    for i in range(hop_count):
        path.append(f"0xHOP{rng.randint(0x1000, 0xFFFF):04X}{i:02X}")

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
            "Funds moved through BSC→ETH bridge. Monitoring recommended."
        )
    else:
        summary = (
            f"ℹ️ {hop_count}-hop flow traced. No mixer or bridge involvement. "
            "Pattern is consistent with moderate-risk activity."
        )

    return FlowTraceResult(
        hop_count=hop_count,
        path=path,
        mixer_detected=mixer_detected,
        mixer_name=mixer_name,
        bridge_detected=bridge_detected,
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


def _determine_risk_level(qubo_score: float, sanctions_hit: bool, hop_count: int) -> tuple[str, str]:
    """Determine risk level and recommended action from combined signals."""
    if sanctions_hit or qubo_score >= QUBO_RISK_THRESHOLD:
        return "HIGH", "FREEZE"
    elif qubo_score >= 0.50 or hop_count >= 3:
        return "MEDIUM", "MONITOR"
    else:
        return "LOW", "CLEAR"


def run_compliance_officer(
    wallet: str,
    qubo: QuboResult,
    flow: FlowTraceResult,
    osint: OsintResult,
    timestamp: str,
) -> tuple[str, str, str, str]:
    """Generate SAR summary + audit hash. Returns (risk_level, action, sar, audit_hash)."""
    risk_level, action = _determine_risk_level(qubo.risk_score, osint.sanctions_hit, flow.hop_count)
    date_str = timestamp[:10]

    sar_summary = f"""
SUSPICIOUS ACTIVITY REPORT (SAR) — AML AI COPILOT
===================================================
Wallet:     {wallet}
Date:       {timestamp}
Risk Level: {risk_level}
Action:     {action}

QUBO ANALYSIS
- Risk Score:          {qubo.risk_score:.4f}
- F-β Score (β=0.5):  {qubo.f_beta_score:.4f}
- False Positive Rate: {qubo.false_positive_rate:.4f}
- Graph: {qubo.graph_nodes} nodes, {qubo.graph_edges} edges
- Backend: {qubo.backend_used}

FLOW TRACE
- Hops:              {flow.hop_count}
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

RECOMMENDED ACTION: {action}
This report is generated by AML AI Copilot (QCFinOp Team, SEA Quantathon 2026).
Powered by Quapp.cloud — Launchpad for Quantum Builders.
""".strip()

    audit_hash = _sha256_payload(sar_summary)
    return risk_level, action, sar_summary, audit_hash


# ─── Full Pipeline ────────────────────────────────────────────────────────────

def run_pipeline(wallet: str) -> ComplianceReport:
    """
    Execute the full simulated AML pipeline for a given wallet address.
    Deterministic: same wallet always produces the same report.
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

    # Stage 1: QUBO
    qubo = run_qubo_stage(wallet, seed)

    # Stage 2: Flow Tracer
    flow = run_flow_tracer(wallet, demo_meta, seed)

    # Stage 3: OSINT
    osint = run_osint_analyst(wallet, demo_meta, seed)

    # Stage 4: Compliance Officer
    risk_level, action, sar, audit_hash = run_compliance_officer(
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
        qubo_risk_score=qubo.risk_score,
        f_beta_score=qubo.f_beta_score,
        audit_hash=audit_hash,
        sar_summary=sar,
        timestamp=timestamp,
        runtime_ms=round(total_ms, 2),
        qubo=asdict(qubo),
        flow_trace=asdict(flow),
        osint=asdict(osint),
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
    print(f"\n{'='*60}")
    print(f"  AML AI Copilot — Pipeline Result")
    print(f"{'='*60}")
    print(f"  Case ID:   {report.case_id}")
    print(f"  Wallet:    {report.wallet_address}")
    print(f"  Risk:      {report.risk_level}")
    print(f"  Action:    {report.recommended_action}")
    print(f"  QUBO Score:{report.qubo_risk_score:.4f}")
    print(f"  F-β Score: {report.f_beta_score:.4f}")
    print(f"  Audit Hash:{report.audit_hash}")
    print(f"  Runtime:   {report.runtime_ms:.1f}ms")
    print(f"{'='*60}\n")


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
        out_file = "TASKS/demo_payloads.json"
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
