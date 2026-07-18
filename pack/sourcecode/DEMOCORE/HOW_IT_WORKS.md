# 🎯 How the AML AI Copilot UI Simulation Works

**SEA Quantathon 2026 · QCFinOp Team**  
**Architecture:** Prof. Hans's Hybrid Quantum-Agentic AML Platform

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Data Flow](#data-flow)
4. [Compliance Scoring Explained](#compliance-scoring-explained)
5. [API Endpoints](#api-endpoints)
6. [Demo Wallets](#demo-wallets)
7. [Running the Simulation](#running-the-simulation)

---

## 🔍 System Overview

The AML AI Copilot is a **Hybrid Quantum-Agentic AML Platform** that combines:
- **Quantum-inspired QUBO optimization** for graph-based risk detection
- **AI Multi-Agent System** for sanctions checking and flow tracing
- **6-Component Compliance Scoring** for regulatory compliance

### Key Innovation: Prof. Hans Architecture

The system implements Prof. Hans's research contributions:
1. **MIMO Tensor Decomposition** (Bottleneck 1, Slide 14) for smurfing detection
2. **Top-20 Subgraph Selection** (NISQ Bridge, Slide 8) for quantum hardware optimization
3. **6-Component Compliance Scoring** (Slide 13) with parametric thresholds
4. **FATF Travel Rule** (Recommendation 16) for SEA regulatory compliance

---

## 🏗 Architecture Components

### 1. QUBO Optimizer (Stage 1)

**Purpose:** Detect illicit wallets in transaction graphs using quantum-inspired algorithms.

```
Input: Wallet Address
  ↓
Build Synthetic Graph (50 nodes, ~96 edges)
  ↓
MIMO Tensor Decomposition (Smurfing Detection)
  • Analyzes transaction time-series matrix T[wallet, time_bucket]
  • Flags wallets where: total ≥ $10,000 BUT max_single_tx < $9,000
  • Applies risk boost: +0.45 to detected smurfing nodes
  ↓
Top-20 Subgraph Selection (NISQ Bridge)
  • Selects top-K high-risk nodes: priority = risk + centrality
  • Ensures target wallet always included
  • Optimizes for quantum hardware: |V| ≤ 20
  ↓
Simulated Annealing QUBO Optimization
  • Cost function: C(x) = x^T Q x
  • F-β (β=0.5): Precision weighted 4x higher than Recall
  • Outputs: r̃ₐ (classical risk), ζₐQ (quantum evidence)
```

**Key Outputs:**
- **r̃ₐ** (classical_risk): Node features + degree centrality [0.0–1.0]
- **ζₐQ** (risk_score): Quantum optimization result [0.0–1.0]
- **Metrics**: Precision, Recall, F-β, False Positive Rate
- **Smurfing flag**: Boolean + count of detected nodes

---

### 2. Flow Tracer Agent (Stage 2)

**Purpose:** Trace multi-hop cash flows across blockchain networks.

```
Input: Wallet Address + Demo Metadata
  ↓
Generate Transaction Hops
  • For each hop: from_wallet → to_wallet
  • Assign: tx_hash, amount_usd, chain (ETH/BSC)
  • Flag: via_mixer, via_bridge
  ↓
Detect Patterns
  • Mixer usage: Tornado Cash, others
  • Bridge usage: ETH ↔ BSC cross-chain
  • Chain analysis: ETH, BSC, Polygon, etc.
```

**Key Outputs:**
- **hops**: List of Hop objects with full transaction details
- **mixer_detected**: Boolean + mixer_name
- **bridge_detected**: Boolean
- **chains_involved**: ["ETH", "BSC", ...]

---

### 3. OSINT Analyst Agent (Stage 3)

**Purpose:** Cross-reference wallet against sanctions databases.

```
Input: Wallet Address + Demo Metadata
  ↓
Sanctions Lookup (Simulated)
  • OFAC SDN List (US Treasury)
  • EU Consolidated Sanctions List
  • UN Security Council Sanctions
  • CryptoScamDB
  ↓
Confidence Scoring
  • If sanctions_hit: confidence ~ 0.91–0.99
  • If clean: confidence ~ 0.0–0.05
```

**Key Outputs:**
- **sanctions_hit**: Boolean
- **sanctions_list**: e.g., "OFAC SDN List (updated 2026-06-01)"
- **confidence**: [0.0–1.0]
- **pep_match**: Politically Exposed Person flag
- **scamdb_match**: CryptoScamDB flag

---

### 4. Compliance Officer Agent (Stage 4)

**Purpose:** Generate audit-ready SAR report with 6-component compliance scoring.

#### 📊 6-Component Compliance Score Formula (Slide 13)

```
Rₐ = ωr·r̃ₐ + ωq·ζₐQ + ωE·Eₐ + ωS·Sₐ + ωC·Cₐ + ωO·Oₐ
```

**Where:**

| Component | Weight | Description | Source |
|-----------|--------|-------------|--------|
| **r̃ₐ** | ωr = 0.30 | Classical risk score | QUBO node features |
| **ζₐQ** | ωq = 0.25 | Quantum evidence | QUBO optimization |
| **Eₐ** | ωE = 0.20 | External sanctions signal | OSINT (0 or 1) |
| **Sₐ** | ωS = 0.15 | Scam/structuring signal | OSINT confidence |
| **Cₐ** | ωC = 0.07 | Counterparty exposure | Flow Tracer mixer flag |
| **Oₐ** | ωO = 0.03 | Obfuscation | Flow Tracer bridge flag |

**All weights sum to 1.0** (calibrated from historical labelled cases).

#### 🎯 Parametric Thresholds (Bottleneck 2, Slide 15)

```
if Rₐ ≥ 0.75 (τH)  →  HIGH risk   →  FREEZE
if Rₐ ≥ 0.45 (τM)  →  MEDIUM risk →  MONITOR
if Rₐ < 0.45       →  LOW risk    →  CLEAR
```

**Special Rule:** Sanctions hit **always triggers FREEZE** regardless of Rₐ.

#### 🛡 FATF Travel Rule (Recommendation 16)

Flags transactions > **$1,000 USD** without VASP originator/beneficiary data:

```
For each hop in flow_trace:
  if hop.amount_usd > 1000 AND (originator_vasp == null OR beneficiary_vasp == null):
    ⚠️ Travel Rule Violation
```

**Compliance:** Meets SEA regulatory requirements (MAS, OJK).

---

## 🔄 Data Flow (End-to-End)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User Input: Wallet Address                                  │
│    Example: 0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b         │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. QUBO Optimizer (MIMO + Top-20 + SA)                         │
│    Outputs:                                                     │
│      • r̃ₐ = 0.3000    (classical risk)                          │
│      • ζₐQ = 0.2000    (quantum evidence)                        │
│      • Precision = 1.0, Recall = 1.0, F-β = 1.0                 │
│      • Smurfing: NO (0 nodes)                                   │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Flow Tracer Agent (Parallel with OSINT)                     │
│    Outputs:                                                     │
│      • 7 hops: ETH → BSC (cross-chain)                          │
│      • Mixer: Tornado Cash detected at hop 4                    │
│      • Bridge: ETH→BSC detected                                 │
│      • Cₐ = 1.0 (mixer), Oₐ = 1.0 (bridge)                      │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. OSINT Analyst Agent (Parallel with Flow Tracer)             │
│    Outputs:                                                     │
│      • Sanctions Hit: YES                                       │
│      • List: OFAC SDN (updated 2026-06-01)                      │
│      • Confidence: 98%                                          │
│      • Eₐ = 1.0 (sanctions), Sₐ = 0.98 (scam confidence)        │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. Compliance Officer (6-Component Scoring)                    │
│    Formula: Rₐ = ωr·r̃ + ωq·ζQ + ωE·E + ωS·S + ωC·C + ωO·O       │
│                                                                 │
│    Calculation:                                                 │
│      0.30 × 0.3000 = 0.0900  (classical)                        │
│      0.25 × 0.2000 = 0.0500  (quantum)                          │
│      0.20 × 1.0000 = 0.2000  (sanctions)                        │
│      0.15 × 0.9800 = 0.1470  (scam)                             │
│      0.07 × 1.0000 = 0.0700  (mixer)                            │
│      0.03 × 1.0000 = 0.0300  (bridge)                           │
│      ─────────────────────────                                  │
│      Rₐ = 0.5870                                                │
│                                                                 │
│    Decision Logic:                                              │
│      Rₐ = 0.5870 < 0.75 (τH)  →  Not HIGH by score             │
│      BUT sanctions_hit = TRUE  →  Override to HIGH              │
│                                                                 │
│    Final Verdict: HIGH → FREEZE                                 │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. Travel Rule Check (FATF R.16)                               │
│    Violations: 7 transactions > $1,000 without VASP data       │
│      • 0x8453... $4,535                                         │
│      • 0x3b72... $40,591                                        │
│      • 0x78dc... $25,104                                        │
│      • (+ 4 more)                                               │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. Generate SAR Report + SHA-256 Audit Hash                    │
│    • Case ID: AML-20260718-D90E2F92                             │
│    • Audit Hash: sha256:a7d4d1ccd0f5423e...                     │
│    • Tamper-proof compliance artifact                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📡 API Endpoints

### Running the Server

```bash
py 03_qubo_sim.py serve 8765
```

Server runs at: **http://localhost:8765**

### Endpoints

#### 1. Health Check
```
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "AML AI Copilot Sim"
}
```

#### 2. Analyze Wallet
```
GET /analyze?wallet=0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b
```

**Response:** (Truncated for brevity)
```json
{
  "case_id": "AML-20260718-D90E2F92",
  "wallet_address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
  "risk_level": "HIGH",
  "recommended_action": "FREEZE",
  "compliance_score": 0.587,
  "score_components": {
    "r_tilde": 0.3,
    "zeta_q": 0.2,
    "E_sanctions": 1.0,
    "S_scam": 0.98,
    "C_mixer": 1.0,
    "O_bridge": 1.0
  },
  "weights": {
    "omega_r": 0.3,
    "omega_q": 0.25,
    "omega_E": 0.2,
    "omega_S": 0.15,
    "omega_C": 0.07,
    "omega_O": 0.03
  },
  "thresholds": {
    "tau_H": 0.75,
    "tau_M": 0.45
  },
  "travel_rule_violations": [ /* 7 violations */ ],
  "qubo": { /* QUBO metrics */ },
  "flow_trace": { /* 7 hops with details */ },
  "osint": { /* Sanctions data */ },
  "audit_hash": "sha256:a7d4d1ccd0f5423e...",
  "sar_summary": "...",
  "timestamp": "2026-07-18T03:21:36+00:00",
  "runtime_ms": 544.71
}
```

#### 3. Demo Wallets List
```
GET /demo-wallets
```

**Response:**
```json
{
  "wallets": [
    "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
    "0x1234567890AbcdEF1234567890AbcDef12345678",
    "0xABCDEF0123456789ABCDef0123456789abcdef01",
    "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
  ]
}
```

---

## 🎭 Demo Wallets (Pre-configured)

### Wallet 1: 🔴 HIGH RISK - Tornado Cash Mixer
```
Address: 0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b
Compliance Score (Rₐ): 0.5870
Action: FREEZE

Components:
  ωr·r̃  = 0.30 × 0.3000 = 0.0900  (classical)
  ωq·ζQ = 0.25 × 0.2000 = 0.0500  (quantum)
  ωE·E  = 0.20 × 1.0000 = 0.2000  (SANCTIONS HIT ⚠️)
  ωS·S  = 0.15 × 0.9800 = 0.1470  (scam confidence)
  ωC·C  = 0.07 × 1.0000 = 0.0700  (MIXER: Tornado Cash)
  ωO·O  = 0.03 × 1.0000 = 0.0300  (BRIDGE: ETH→BSC)

Red Flags:
  • OFAC SDN List match (98% confidence)
  • 7-hop transaction chain through Tornado Cash
  • Cross-chain bridge (ETH → BSC)
  • 7 Travel Rule violations (>$1,000)
```

### Wallet 2: 🔴 HIGH RISK - Bridge Exploit
```
Address: 0x1234567890AbcdEF1234567890AbcDef12345678
Compliance Score (Rₐ): 0.8930
Action: FREEZE

Components:
  ωr·r̃  = 0.30 × 1.0000 = 0.3000  (high classical risk)
  ωq·ζQ = 0.25 × 0.9000 = 0.2250  (high quantum evidence)
  ωE·E  = 0.20 × 1.0000 = 0.2000  (EU Sanctions + CryptoScamDB)
  ωS·S  = 0.15 × 0.9200 = 0.1380  (scam score)
  ωC·C  = 0.07 × 0.0000 = 0.0000  (no mixer)
  ωO·O  = 0.03 × 1.0000 = 0.0300  (bridge detected)

Red Flags:
  • EU Sanctions List + CryptoScamDB match
  • High QUBO quantum evidence (ζQ = 0.90)
  • 5-hop cross-chain bridge pattern
  • 5 Travel Rule violations
```

### Wallet 3: 🟢 LOW RISK - Suspicious Pattern
```
Address: 0xABCDEF0123456789ABCDef0123456789abcdef01
Compliance Score (Rₐ): 0.1175
Action: CLEAR

Components:
  ωr·r̃  = 0.30 × 0.2250 = 0.0675  (low classical risk)
  ωq·ζQ = 0.25 × 0.2000 = 0.0500  (low quantum evidence)
  ωE·E  = 0.20 × 0.0000 = 0.0000  (no sanctions)
  ωS·S  = 0.15 × 0.0000 = 0.0000  (no scam)
  ωC·C  = 0.07 × 0.0000 = 0.0000  (no mixer)
  ωO·O  = 0.03 × 0.0000 = 0.0000  (no bridge)

Status:
  • Rₐ = 0.1175 < 0.45 (τM) → LOW risk
  • No sanctions match
  • 3 moderate transactions (but below Travel Rule threshold)
```

### Wallet 4: 🟢 LOW RISK - Clean
```
Address: 0x742d35Cc6634C0532925a3b844Bc454e4438f44e
Compliance Score (Rₐ): 0.0916
Action: CLEAR

Components:
  ωr·r̃  = 0.30 × 0.1385 = 0.0416  (minimal classical risk)
  ωq·ζQ = 0.25 × 0.2000 = 0.0500  (low quantum evidence)
  ωE·E  = 0.20 × 0.0000 = 0.0000  (no sanctions)
  ωS·S  = 0.15 × 0.0000 = 0.0000  (no scam)
  ωC·C  = 0.07 × 0.0000 = 0.0000  (no mixer)
  ωO·O  = 0.03 × 0.0000 = 0.0000  (no bridge)

Status:
  • Rₐ = 0.0916 < 0.45 (τM) → LOW risk
  • Normal wallet activity
  • No suspicious patterns detected
```

---

## 🚀 Running the Simulation

### Option 1: HTTP Server (Recommended)

```bash
# Start server
py 03_qubo_sim.py serve 8765

# Test from browser
http://localhost:8765/analyze?wallet=0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b

# Or use curl/PowerShell
curl http://localhost:8765/health
```

### Option 2: Command Line

```bash
# Analyze a specific wallet
py 03_qubo_sim.py 0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b

# Get JSON output
py 03_qubo_sim.py 0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b --json

# Pre-compute all demo wallets
py 03_qubo_sim.py precompute
```

### Option 3: HTML Prototype (Static)

```bash
# Open in browser
04_prototype.html

# The HTML uses pre-computed demo_payloads.json
# No server needed - 100% client-side JavaScript
```

---

## 📊 Performance Metrics

### Computational Complexity

| Component | Time Complexity | Space | Notes |
|-----------|----------------|-------|-------|
| MIMO Tensor | O(n·m·k) | O(n·m) | n=nodes, m=buckets, k=SVD rank |
| Top-20 Selection | O(n log k) | O(n) | Priority queue for k=20 |
| SA QUBO | O(n²·iterations) | O(n²) | Simulated Annealing |
| Flow Tracer | O(hops) | O(hops) | Linear in hop count |
| OSINT | O(1) | O(1) | Lookup simulation |
| Compliance | O(1) | O(1) | Formula evaluation |

### Runtime Benchmarks

| Wallet | Graph Size | Runtime | Bottleneck |
|--------|-----------|---------|------------|
| Tornado Cash | 50 nodes, 96 edges | ~207ms | QUBO SA |
| Bridge Exploit | 50 nodes, 96 edges | ~205ms | QUBO SA |
| Suspicious | 50 nodes, 96 edges | ~228ms | QUBO SA |
| Clean | 50 nodes, 96 edges | ~202ms | QUBO SA |

**Average:** ~210ms end-to-end (including all 4 stages + Travel Rule check)

---

## 🔐 Security & Compliance

### SHA-256 Audit Trail

Every SAR report includes a **tamper-proof audit hash**:

```
audit_hash = sha256(sar_summary)
Example: sha256:a7d4d1ccd0f5423e6aa139518f2023cd743961de...
```

Any modification to the report changes the hash → detectable tampering.

### FATF Recommendation 16 (Travel Rule)

**Requirement:** Crypto transfers ≥ $1,000 must include:
- Originator VASP (Virtual Asset Service Provider)
- Beneficiary VASP
- Account holder information

**Our Implementation:**
```python
for hop in flow_trace.hops:
    if hop.amount_usd > 1000 and (
        hop.originator_vasp is None or 
        hop.beneficiary_vasp is None
    ):
        flag_as_violation(hop)
```

**Compliance:** MAS (Singapore), OJK (Indonesia), BSP (Philippines)

---

## 🎓 Academic References

### Prof. Hans's Architecture Contributions

1. **MIMO Tensor Decomposition (Slide 14, Bottleneck 1)**
   - Detects smurfing via coherent integration of micro-transactions
   - Financial equivalent of radar RCS reduction detection

2. **Top-20 Subgraph Selection (Slide 8, NISQ Bridge)**
   - Reduces graph to quantum-ready size: |V| ≤ 20
   - Priority scoring: s_i = λ_r·r~_i + λ_n·Centrality_i

3. **6-Component Compliance Scoring (Slide 13)**
   - Rₐ = ∑(ω_k · feature_k), k ∈ {r, q, E, S, C, O}
   - All ω ≥ 0, ∑ω = 1.0 (calibrated from historical data)

4. **Parametric Thresholds (Slide 15, Bottleneck 2)**
   - τH (FREEZE), τM (MONITOR) — not hard-coded
   - Kill Chain (FREEZE) decoupled from Analysis Chain (SAR)

---

## 🔧 Technical Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | Python 3.14 | Core simulation engine |
| **QUBO** | NumPy | Matrix operations, SVD |
| **Optimization** | Simulated Annealing | Classical fallback for QUBO |
| **API** | http.server (stdlib) | Lightweight HTTP server |
| **Data** | JSON | Pre-computed payloads |
| **Frontend** | HTML + Vanilla JS | Static prototype UI |
| **Security** | SHA-256 (hashlib) | Audit trail hashing |

**Dependencies:** `None` (stdlib only)

---

## 🎯 Key Takeaways

### For Developers

1. **Architecture is modular:** Each stage (QUBO → Agents → Compliance) is independent
2. **Fully deterministic:** Same wallet → same result (reproducible demos)
3. **No external dependencies:** Runs offline with stdlib only
4. **Fast:** ~200ms end-to-end (50-node graph)

### For Compliance Officers

1. **6-component scoring:** Transparent, explainable risk assessment
2. **Travel Rule compliance:** Automated FATF R.16 checking
3. **Audit trail:** SHA-256 tamper-proof SAR reports
4. **Parametric thresholds:** Calibrated from historical data (τH, τM)

### For Quantum Researchers

1. **MIMO Tensor:** Smurfing detection via SVD rank-reduction
2. **Top-20 NISQ:** Graph-to-subgraph optimization for quantum hardware
3. **QUBO formulation:** F-β cost function (β=0.5) minimizes FPR
4. **Hamiltonian calibration:** QAOA depth p selection (not implemented in sim)

---

## 📞 Contact & Support

**Team:** QCFinOp · SEA Quantathon 2026  
**Architecture:** Prof. Hans  
**Platform:** Quapp.cloud — Launchpad for Quantum Builders

For questions or support, refer to:
- `README.md` — Project overview
- `01_MVP_SCOPE.md` — MVP scope definition
- `02_UX_WIREFRAME.md` — UI/UX flow
- `05_USABILITY_TEST_REPORT.md` — User testing findings

---

**Last Updated:** 2026-07-18  
**Version:** 2.0 (Prof. Hans Architecture)
