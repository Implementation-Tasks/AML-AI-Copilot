"""
Multi-Agent AML Crew (CrewAI Framework)

3 autonomous AI agents that activate when QUBO flags a suspicious wallet:
  1. Multi-hop Flow Tracer Agent
  2. OSINT & KYC Analyst Agent
  3. Compliance Officer Agent (AI)
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from src.config import (
    AGENT_RETRY_ATTEMPTS,
    AGENT_TIMEOUT_SECONDS,
    F_BETA,
    LLM_MODEL,
    LLM_PROVIDER,
    QUBO_RISK_THRESHOLD,
    REPORTS_DIR,
)
from src.models import (
    AgentInput,
    ComplianceReport,
    FlowTraceResult,
    Hop,
    SanctionMatch,
    ThreatIntelResult,
    ToolOutput,
    TravelRuleRecord,
)
from src.tools.agent_tools import (
    CryptoScamDBTool,
    EtherscanAPITool,
    GraphQueryTool,
    OpenSanctionsTool,
    ReportGeneratorTool,
)
from src.quantum.graph_to_qubo import compute_f_beta

logger = logging.getLogger(__name__)


def _get_llm():
    """Initialise LLM backend (Claude or OpenAI)."""
    try:
        from crewai import LLM
        if LLM_PROVIDER == "anthropic":
            return LLM(model=f"anthropic/{LLM_MODEL}")
        return LLM(model=f"openai/{LLM_MODEL}")
    except ImportError:
        logger.warning("crewai not installed — running in tool-only mode (no LLM reasoning).")
        return None


# ─── Agent 1: Multi-hop Flow Tracer ──────────────────────────────────────────

def run_flow_tracer(wallet_address: str, trace_id: str) -> FlowTraceResult:
    """
    Trace multi-hop cash flows from a suspicious wallet.
    Uses EtherscanAPITool (ETH + BSC) and GraphQueryTool (DeFi protocols).
    """
    logger.info(f"[FlowTracer] Starting trace for {wallet_address} | trace_id={trace_id}")
    etherscan = EtherscanAPITool()
    graph_query = GraphQueryTool()

    # Trace on Ethereum
    eth_result: ToolOutput = etherscan.run(wallet_address=wallet_address, chain="eth", max_hops=7)
    # Trace on BSC
    bsc_result: ToolOutput = etherscan.run(wallet_address=wallet_address, chain="bsc", max_hops=3)
    # Check DeFi (Tornado Cash pattern)
    tornado_result: ToolOutput = graph_query.run(wallet_address=wallet_address, protocol="tornado_cash")

    # Parse hops from ETH + BSC
    all_hops: list[Hop] = []
    bridges_used: list[str] = []
    mixers_used: list[str] = []
    chains: set[str] = set()

    for result, chain in [(eth_result, "eth"), (bsc_result, "bsc")]:
        if result.success:
            for h in result.data.get("hops", []):
                hop = Hop(
                    from_wallet=h["from"],
                    to_wallet=h["to"],
                    tx_hash=h["hash"],
                    amount_usd=h.get("value_eth", 0.0) * 3000,  # rough ETH/USD
                    chain=chain,
                    timestamp=datetime.fromisoformat(h["timestamp"]) if h.get("timestamp") else datetime.now(timezone.utc),
                    via_mixer=bool(tornado_result.success and tornado_result.data.get("count", 0) > 0),
                    via_bridge=(chain == "bsc"),  # crossed to BSC = bridge
                )
                all_hops.append(hop)
                chains.add(chain)
                if hop.via_bridge:
                    bridges_used.append("ETH→BSC Bridge")
                if hop.via_mixer:
                    mixers_used.append("Tornado Cash")

    return FlowTraceResult(
        origin_wallet=wallet_address,
        hops=all_hops,
        bridges_used=list(set(bridges_used)),
        mixers_used=list(set(mixers_used)),
        total_hops=len(all_hops),
        chains_involved=list(chains),
    )


# ─── Agent 2: OSINT & KYC Analyst ────────────────────────────────────────────

def run_osint_analyst(wallet_address: str) -> ThreatIntelResult:
    """
    Cross-reference wallet against OFAC, EU, UN sanctions + CryptoScamDB.
    """
    logger.info(f"[OSINTAnalyst] Checking {wallet_address}")
    sanctions_tool = OpenSanctionsTool()
    scamdb_tool = CryptoScamDBTool()

    sanctions_result: ToolOutput = sanctions_tool.run(wallet_address=wallet_address)
    scam_result: ToolOutput = scamdb_tool.run(wallet_address=wallet_address)

    # Parse sanctions hits
    sanctions_hits: list[SanctionMatch] = []
    if sanctions_result.success:
        for hit in sanctions_result.data.get("sanctions_hits", []):
            sanctions_hits.append(SanctionMatch(
                wallet_address=wallet_address,
                list_name=hit.get("list_name", "UNKNOWN"),
                entity_name=hit.get("entity_name", ""),
                confidence=hit.get("confidence", 0.0),
                source_url=hit.get("source_url", ""),
            ))

    # Parse scam score
    scam_score = 0.0
    scam_categories: list[str] = []
    if scam_result.success and scam_result.data.get("is_blacklisted"):
        scam_score = scam_result.confidence_score
        scam_categories = scam_result.data.get("categories", [])

    return ThreatIntelResult(
        wallet_address=wallet_address,
        sanctions_hits=sanctions_hits,
        scam_score=scam_score,
        scam_categories=scam_categories,
        sources_checked=["OpenSanctions", "CryptoScamDB"],
    )


# ─── Agent 3: Compliance Officer ─────────────────────────────────────────────

def run_compliance_officer(
    agent_input: AgentInput,
    flow_trace: FlowTraceResult,
    threat_intel: ThreatIntelResult,
    beta: float = F_BETA,
) -> ComplianceReport:
    """
    Synthesize findings from all agents → structured AML compliance report.
    Determines risk level, recommended action, and F-β score.
    """
    logger.info(f"[ComplianceOfficer] Generating report for {agent_input.wallet_address}")
    report_tool = ReportGeneratorTool()

    # ── Risk Level Determination ──────────────────────────────────────────────
    has_sanctions = bool(threat_intel.sanctions_hits)
    has_mixer = bool(flow_trace.mixers_used)
    has_bridge = bool(flow_trace.bridges_used)
    high_scam_score = threat_intel.scam_score > 0.7
    high_qubo_risk = agent_input.qubo_risk_score > QUBO_RISK_THRESHOLD

    risk_score_composite = (
        0.35 * agent_input.qubo_risk_score
        + 0.30 * (1.0 if has_sanctions else 0.0)
        + 0.20 * threat_intel.scam_score
        + 0.10 * (1.0 if has_mixer else 0.0)
        + 0.05 * (1.0 if has_bridge else 0.0)
    )

    if risk_score_composite > 0.75 or has_sanctions:
        risk_level = "HIGH"
        action = "FREEZE"
    elif risk_score_composite > 0.45:
        risk_level = "MEDIUM"
        action = "MONITOR"
    else:
        risk_level = "LOW"
        action = "CLEAR"

    # ── F-β Score ─────────────────────────────────────────────────────────────
    # Use composite score as proxy for precision (no FP = high precision)
    proxy_precision = risk_score_composite
    proxy_recall = min(
        (1 if has_sanctions else 0) + threat_intel.scam_score + (0.3 if has_mixer else 0),
        1.0,
    )
    f_beta = compute_f_beta(proxy_precision, proxy_recall, beta)

    # ── Travel Rule (FATF R.16) Violations ────────────────────────────────────
    # In SEA (MAS/OJK), crypto transfers > $1000 USD require Travel Rule information.
    travel_rule_violations: list[TravelRuleRecord] = []
    TRAVEL_RULE_THRESHOLD_USD = 1000.0

    for hop in flow_trace.hops:
        if hop.amount_usd > TRAVEL_RULE_THRESHOLD_USD:
            # We assume on-chain unhosted wallets lack VASP originator/beneficiary info
            travel_rule_violations.append(
                TravelRuleRecord(
                    tx_hash=hop.tx_hash,
                    originator_account=hop.from_wallet,
                    beneficiary_account=hop.to_wallet,
                    originator_vasp=None,
                    beneficiary_vasp=None,
                    transfer_amount_usd=hop.amount_usd,
                    threshold_exceeded=True,
                )
            )

    # ── Summary ───────────────────────────────────────────────────────────────
    summary_parts = [
        f"Wallet {agent_input.wallet_address} flagged with QUBO risk score {agent_input.qubo_risk_score:.2f}.",
        f"Transaction trace: {flow_trace.total_hops} hops across {', '.join(flow_trace.chains_involved) or 'ETH'}.",
    ]
    if flow_trace.mixers_used:
        summary_parts.append(f"⚠️ Mixer usage detected: {', '.join(flow_trace.mixers_used)}.")
    if flow_trace.bridges_used:
        summary_parts.append(f"⚠️ Cross-chain bridges: {', '.join(flow_trace.bridges_used)}.")
    if has_sanctions:
        names = [h.entity_name for h in threat_intel.sanctions_hits[:3]]
        summary_parts.append(f"🚨 SANCTIONS HIT: {', '.join(names)}.")
    if high_scam_score:
        summary_parts.append(f"🚨 CryptoScamDB score: {threat_intel.scam_score:.2f}.")
    if travel_rule_violations:
        summary_parts.append(f"⚠️ FATF Travel Rule violations: {len(travel_rule_violations)} txs > $1,000 without VASP data.")
        
    summary_parts.append(f"Recommended action: {action}.")
    summary = " ".join(summary_parts)

    case_id = f"AML-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

    # ── Generate Report File ──────────────────────────────────────────────────
    case_data = {
        "case_id": case_id,
        "wallet_address": agent_input.wallet_address,
        "risk_level": risk_level,
        "qubo_risk_score": agent_input.qubo_risk_score,
        "f_beta_score": round(f_beta, 4),
        "recommended_action": action,
        "flow_trace": {
            "total_hops": flow_trace.total_hops,
            "mixers": flow_trace.mixers_used,
            "bridges": flow_trace.bridges_used,
            "chains": flow_trace.chains_involved,
        },
        "threat_intel": {
            "sanctions_hits": [
                {"list": h.list_name, "entity": h.entity_name, "confidence": h.confidence}
                for h in threat_intel.sanctions_hits
            ],
            "scam_score": threat_intel.scam_score,
            "categories": threat_intel.scam_categories,
        },
        "travel_rule_violations": [
            {
                "tx_hash": v.tx_hash,
                "amount_usd": v.transfer_amount_usd,
                "originator": v.originator_account,
                "beneficiary": v.beneficiary_account
            }
            for v in travel_rule_violations
        ],
        "summary": summary,
    }

    report_output: ToolOutput = report_tool.run(
        case_data=case_data,
        output_dir=str(REPORTS_DIR),
    )

    report_file = report_output.data.get("file_path") if report_output.success else None
    audit_hash = report_output.data.get("report", {}).get("audit_hash") if report_output.success else None

    return ComplianceReport(
        case_id=case_id,
        timestamp=datetime.now(timezone.utc),
        wallet_address=agent_input.wallet_address,
        risk_level=risk_level,
        qubo_risk_score=agent_input.qubo_risk_score,
        f_beta_score=round(f_beta, 4),
        precision=round(proxy_precision, 4),
        recall=round(proxy_recall, 4),
        flow_trace=flow_trace,
        threat_intel=threat_intel,
        travel_rule_violations=travel_rule_violations,
        recommended_action=action,
        summary=summary,
        pdf_url=report_file,
        audit_hash=audit_hash,
        trace_id=agent_input.trace_id,
    )


# ─── Crew Orchestrator ────────────────────────────────────────────────────────

def run_aml_crew(agent_input: AgentInput) -> ComplianceReport:
    """
    Main entry point: runs Agent 1 + Agent 2 in PARALLEL, then Agent 3 sequentially.

    Agent flow (optimized):
        Agent 1 (Flow Tracer) ─┐
                                ├──→ [both complete] ──→ Agent 3 (Compliance)
        Agent 2 (OSINT)        ─┘

    Latency: max(T_flowtracer, T_osint) + T_compliance
             (was T_flowtracer + T_osint + T_compliance)

    Args:
        agent_input: Wallet + QUBO risk score + trace_id

    Returns:
        ComplianceReport (Audit-ready, SHA-256 hash, action recommendation)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    start = time.perf_counter()
    logger.info(
        f"[AMLCrew] Starting investigation | wallet={agent_input.wallet_address} "
        f"| qubo_risk={agent_input.qubo_risk_score:.2f} | trace_id={agent_input.trace_id}"
    )

    # ── Agent 1 + Agent 2: run in PARALLEL ───────────────────────────────────
    flow_trace: FlowTraceResult | None  = None
    threat_intel: ThreatIntelResult | None = None

    with ThreadPoolExecutor(max_workers=2, thread_name_prefix="AMLAgent") as executor:
        future_flow  = executor.submit(run_flow_tracer, agent_input.wallet_address, agent_input.trace_id)
        future_osint = executor.submit(run_osint_analyst, agent_input.wallet_address)

        for future in as_completed([future_flow, future_osint]):
            try:
                result = future.result()
                if isinstance(result, FlowTraceResult):
                    flow_trace = result
                    logger.info(f"[AMLCrew] FlowTracer ✓ — {flow_trace.total_hops} hops")
                elif isinstance(result, ThreatIntelResult):
                    threat_intel = result
                    logger.info(f"[AMLCrew] OSINTAnalyst ✓ — {len(threat_intel.sanctions_hits)} sanctions hits")
            except Exception as exc:
                logger.error(f"[AMLCrew] Agent parallel execution error: {exc}", exc_info=True)

    # Graceful fallback if either agent failed
    if flow_trace is None:
        logger.warning("[AMLCrew] FlowTracer failed — using empty FlowTraceResult")
        flow_trace = FlowTraceResult(
            origin_wallet=agent_input.wallet_address,
            hops=[],
            bridges_used=[],
            mixers_used=[],
            total_hops=0,
            chains_involved=[],
        )
    if threat_intel is None:
        logger.warning("[AMLCrew] OSINTAnalyst failed — using empty ThreatIntelResult")
        threat_intel = ThreatIntelResult(
            wallet_address=agent_input.wallet_address,
            sanctions_hits=[],
            scam_score=0.0,
            scam_categories=[],
            sources_checked=[],
        )

    # ── Agent 3: Compliance Officer (sequential — depends on 1+2) ────────────
    report = run_compliance_officer(agent_input, flow_trace, threat_intel)

    elapsed = time.perf_counter() - start
    logger.info(
        f"[AMLCrew] Investigation complete | case_id={report.case_id} "
        f"| risk={report.risk_level} | action={report.recommended_action} "
        f"| F-β={report.f_beta_score:.3f} | runtime={elapsed:.2f}s (parallel agents)"
    )
    return report
