"""
Data contracts / shared dataclasses for AML AI Copilot.
All modules import types from here — single source of truth.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import numpy as np
import networkx as nx


# ─── Pipeline ────────────────────────────────────────────────────────────────

@dataclass
class TransactionGraph:
    """Blockchain transaction graph: nodes=wallets, edges=transactions."""
    graph: nx.DiGraph
    node_features: dict[str, np.ndarray] = field(default_factory=dict)
    edge_features: dict[tuple, np.ndarray] = field(default_factory=dict)
    known_illicit: list[str] = field(default_factory=list)
    known_licit: list[str] = field(default_factory=list)
    source_dataset: str = "unknown"


@dataclass
class AgentInput:
    """Input payload handed off from Quantum layer to Agent crew."""
    wallet_address: str
    qubo_risk_score: float        # 0.0 – 1.0
    qubo_flagged_nodes: list[str]
    trace_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PipelineResult:
    """Top-level result of a full pipeline run."""
    task_id: str
    wallet_address: str
    status: str                   # "pending" | "running" | "done" | "error"
    result_url: Optional[str] = None
    error: Optional[str] = None


# ─── Tools ───────────────────────────────────────────────────────────────────

@dataclass
class ToolOutput:
    """Standardised output contract for all Agent tools."""
    success: bool
    data: dict
    confidence_score: float       # 0.0 – 1.0
    evidence_links: list[str] = field(default_factory=list)
    error: Optional[str] = None


# ─── Quantum ─────────────────────────────────────────────────────────────────

@dataclass
class QUBOResult:
    """Result of graph → QUBO mapping."""
    qubo_matrix: np.ndarray
    variable_mapping: dict[int, str]   # index → wallet_address
    estimated_energy: float
    backend_used: str


@dataclass
class OptimizationResult:
    """Result of QUBO optimization run."""
    flagged_wallets: list[str]
    risk_scores: dict[str, float]
    false_positive_rate: float
    f_beta_score: float
    precision: float
    recall: float
    runtime_seconds: float
    backend_used: str


# ─── Agents ──────────────────────────────────────────────────────────────────

@dataclass
class Hop:
    """Single hop in a multi-hop transaction trace."""
    from_wallet: str
    to_wallet: str
    tx_hash: str
    amount_usd: float
    chain: str
    timestamp: datetime
    via_mixer: bool = False
    via_bridge: bool = False


@dataclass
class FlowTraceResult:
    """Output of Multi-hop Flow Tracer Agent."""
    origin_wallet: str
    hops: list[Hop]
    bridges_used: list[str]
    mixers_used: list[str]
    total_hops: int
    chains_involved: list[str]


@dataclass
class SanctionMatch:
    """A single sanctions list match."""
    wallet_address: str
    list_name: str                # "OFAC_SDN" | "EU" | "UN" | "PEPs"
    entity_name: str
    confidence: float
    source_url: str


@dataclass
class ThreatIntelResult:
    """Output of OSINT & KYC Analyst Agent."""
    wallet_address: str
    sanctions_hits: list[SanctionMatch]
    scam_score: float             # 0.0 – 1.0
    scam_categories: list[str]   # "phishing" | "rug-pull" | "malware"
    sources_checked: list[str]


@dataclass
class TravelRuleRecord:
    """FATF Recommendation 16 — Travel Rule compliance record."""
    tx_hash: str
    originator_account: str
    beneficiary_account: str
    originator_vasp: Optional[str] = None
    beneficiary_vasp: Optional[str] = None
    transfer_amount_usd: float = 0.0
    threshold_exceeded: bool = False


@dataclass
class ComplianceReport:
    """Final AML compliance report — Audit-ready."""
    case_id: str
    timestamp: datetime
    wallet_address: str
    risk_level: str               # "HIGH" | "MEDIUM" | "LOW"
    qubo_risk_score: float
    f_beta_score: float
    precision: float
    recall: float
    flow_trace: FlowTraceResult
    threat_intel: ThreatIntelResult
    travel_rule_violations: list[TravelRuleRecord]
    recommended_action: str       # "FREEZE" | "MONITOR" | "CLEAR"
    summary: str
    pdf_url: Optional[str] = None
    audit_hash: Optional[str] = None
    trace_id: Optional[str] = None
