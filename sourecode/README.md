# ⚛ AML AI Copilot

> **Quantum-Inspired Crypto AML Platform for Southeast Asia**
> SEA Quantathon 2026 · QCFinOp Team

[![Tests](<https://img.shields.io/badge/tests-28%2F28%20passed-brightgreen>)](#)
[![Python](https://img.shields.io/badge/python-3.14-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-purple)](#)
[![Quapp](https://img.shields.io/badge/platform-Quapp.cloud-orange)](#)

---

## The Problem

Crypto exchanges in Southeast Asia face a **90% false positive rate** in AML alerts — every false alert freezes a legitimate user account and wastes analyst time. Current rule-based systems (Chainalysis, Elliptic) cannot process the complex multi-hop, cross-chain patterns used by sophisticated money launderers.

## Our Solution

**Hybrid Quantum-Agentic AML Platform** combining:

1. **QUBO Optimizer** — converts blockchain transaction graphs into QUBO matrices and solves with quantum-inspired algorithms (Qamelion / Perceval / SimulatedAnnealing). Explicitly penalizes false positives via F-β cost function (β=0.5).
2. **Multi-Agent AI Crew** (CrewAI) — 3 autonomous agents activate on high-risk flags:

   - **Flow Tracer** — traces multi-hop cash flows via Etherscan + The Graph
   - **OSINT Analyst** — cross-references OFAC, EU, UN sanctions + CryptoScamDB
   - **Compliance Officer** — generates SHA-256 audit-ready AML reports
3. **Quapp.cloud Orchestration** — the central Launchpad for Quantum Builders: async middleware connecting Classical HPC + Quantum-as-a-Service across Qamelion (Qudora), Perceval (Quandela), and IBM Quantum backends.

---

## Benchmark Results

| Model                    | False Positive Rate | F-β (β=0.5) |  Graph-Native  |
| ------------------------ | :-----------------: | :-----------: | :-------------: |
| **QUBO-Optimizer** |   **0.0%**   |     0.893     |       ✅       |
| XGBoost                  |        0.0%        |     1.000     | ❌ Tabular only |
| RandomForest             |        0.0%        |     1.000     | ❌ Tabular only |
| GraphSAGE (industry std) |        19.6%        |     0.324     |       ✅       |
| GAT                      |        19.6%        |     0.324     |       ✅       |

> QUBO reduces FPR by **19.6 points** vs GraphSAGE on synthetic scale-free graph data.
> Full Elliptic dataset (203,769 transactions) benchmark in progress.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Implementation-Tasks/AML-AI-Copilot.git
cd AML-AI-Copilot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 4. Run tests (28/28 should pass)
python -m pytest tests/ -v

# 5. Run benchmark
python -m src.quantum.benchmark --demo

# 6. Open Demo UI
# Open demo/index.html in your browser

# 7. Deploy to Quapp.cloud
# See "Quapp Platform Deployment" section below
```

---

## Project Structure

```
AML-AI-Copilot/
├── demo/
│   └── index.html              # POC Demo UI (open in browser)
├── src/
│   ├── config.py               # All settings from .env
│   ├── models.py               # Shared data contracts (13 dataclasses)
│   ├── quantum/
│   │   ├── graph_to_qubo.py    # Graph → QUBO matrix (P0 core)
│   │   ├── hybrid_optimizer.py # Qamelion + Perceval + SA fallback
│   │   └── benchmark.py        # Model comparison suite
│   ├── agents/
│   │   └── multi_agent_crew.py # 3-agent pipeline
│   ├── pipeline/
│   │   ├── handler.py          # Quapp Function entrypoint (handler.py)
│   │   ├── run.py              # CLI entrypoint + pipeline trigger
│   │   └── orchestrator.py     # Quapp YAML loader + task dispatcher
│   ├── tools/
│   │   └── agent_tools.py      # Etherscan, OpenSanctions, ScamDB, Report tools
│   ├── data/
│   │   └── elliptic_loader.py  # Elliptic Bitcoin dataset loader
│   ├── security.py             # Wallet validation, PII masking, rate limiting
│   └── observability.py        # JSON logging, metrics, trace propagation
├── config/
│   └── quapp_hybrid_orchestrator.yaml  # Quapp YAML workflow config
├── tests/
│   ├── test_qubo_mapping.py    # 19 QUBO tests
│   └── test_agents.py          # 9 Agent tests
├── docs/
│   ├── specs/                  # Technical specifications
│   └── LOI_Executive_Summary.md
├── reports/
│   └── benchmark_v1.md         # Latest benchmark results
├── agent-skills/               # Reusable AI agent skill definitions
├── AML_AI_Copilot_Strategic_Report_V3.md
├── .env.example
├── requirements.txt
└── README.md
```

---

## Architecture

```
Wallet Address
      │
      ▼
┌─────────────────────────────────────────┐
│         Quapp.cloud Orchestrator        │  ← Central entry point: async
│   (Launchpad for Quantum Builders)      │    middleware managing HPC + QaaS
│   handler.py → quapp_orchestrator.yaml  │    project lifecycle & task dispatch
└─────────────────┬───────────────────────┘
                  │
        ┌─────────▼─────────┐
        │   QUBO Optimizer   │  ← Quantum-inspired graph optimization
        │   (F-β, β=0.5)    │    Penalizes false positives in cost function
        └─────────┬──────────┘
                  │ risk_score > 0.85
        ┌─────────▼──────────────────────────┐
        │         CrewAI Agents              │
        │  ┌──────────────────────────────┐  │
        │  │ 1. Multi-hop Flow Tracer     │  │  ← Etherscan + The Graph
        │  │ 2. OSINT & KYC Analyst       │  │  ← OpenSanctions + CryptoScamDB
        │  │ 3. AI Compliance Officer     │  │  ← SAR-ready report + SHA-256
        │  └──────────────────────────────┘  │
        └────────────────────────────────────┘
                  │
        ┌─────────▼──────────┐
        │  Compliance Report  │  ← Audit hash, FREEZE / MONITOR / CLEAR
        └────────────────────┘
```

---

## Quapp Platform Deployment

> **Quapp.cloud** is the "Launchpad for Quantum Builders" — the platform through which the AML AI Copilot pipeline is packaged, deployed, and invoked as a serverless quantum function.

### Step 1 — Basic Info

Create a new **Function** on Quapp.cloud:

- **Function name**: `aml-copilot-hybrid`
- **Description**: Hybrid Quantum-Agentic AML pipeline — QUBO optimization + multi-agent investigation for crypto wallet risk scoring
- **SDK**: Select from Quapp-supported SDKs: `Qiskit` | `PennyLane` | `D-Wave Ocean (dimod)` | `AWS Braket`

### Step 2 — Method

Choose **"Start from Scratch"** to use our custom `handler.py` entrypoint for full pipeline control, OR select a **Template** optimized for QUBO combinatorial problems (Step 3).

### Step 3 — Template (if applicable)

If using a template, select the **QUBO / Combinatorial Optimization** template as the closest match to our graph-based AML workload.

### Step 4 — Review the Code

Quapp expects two primary deployment artifacts in `src/pipeline/`:

```
src/pipeline/handler.py        # Function entrypoint — receives wallet input, dispatches pipeline
requirements.txt               # Python dependencies (dimod, crewai, networkx, etc.)
```

The `handler.py` entrypoint signature:

```python
def handler(event: dict) -> dict:
    """
    Quapp Function entrypoint for AML AI Copilot pipeline.

    Args:
        event: {
            "wallet_address": str,   # EIP-55 checksummed wallet
            "backend": str,          # "classical" | "qamelion" | "perceval" | "ibm_quantum"
            "shots": int,            # Number of quantum circuit runs (default: 1024)
            "mode": str              # "hybrid" | "classical" | "quantum_sim"
        }

    Returns:
        {
            "risk_level": str,           # "HIGH" | "MEDIUM" | "LOW"
            "recommended_action": str,   # "FREEZE" | "MONITOR" | "CLEAR"
            "f_beta_score": float,
            "audit_hash": str            # SHA-256 of compliance report
        }
    """
    ...
```

### Step 5 — Deploy

Deploy the Function with the **Hybrid Quantum-HPC computational workflow**:

- Configure `quapp_hybrid_orchestrator.yaml` with HPC worker count and quantum backend selection
- Set `fallback_to_simulator: true` for resilience when QaaS is unavailable
- All pipeline events are logged as structured JSON with `trace_id`

### Job Invocation

After deployment, invoke the AML pipeline from the Quapp dashboard:

1. Navigate to **Functions** in the left sidebar → select `aml-copilot-hybrid`
2. Provide execution parameters:
   - **Provider**: `Quapp` | `Quandela` | `IBM Quantum`
   - **Device**: Select quantum device or simulator
   - **Shots**: Number of quantum circuit runs (e.g., `1024`)
   - **Input**: Wallet address (raw or from data source)
3. Click **"Invoke"** — the new Job appears at the top of the jobs table for status tracking

### Project & Team Setup

- Each team member should be added to the **same Quapp project** (not the default shared project)
- The project creator becomes the **Admin** and adds members via email address
- Members must have an active Quapp account before they can be added
- For **QPU runtime** access (Quandela-sponsored): contact the Quapp support team (Win / Van) via Discord

---

## Core Usage

### QUBO Optimizer

```python
from src.models import TransactionGraph
from src.quantum.hybrid_optimizer import HybridQuantumOptimizer
import networkx as nx

# Build transaction graph
G = nx.scale_free_graph(200, seed=42).to_directed()
# ... add node features (is_mixer, is_bridge, tx_velocity)

tx_graph = TransactionGraph(
    graph=G,
    known_illicit=["0xABC..."],
    known_licit=["0xDEF..."],
)

optimizer = HybridQuantumOptimizer(backend_choice="classical")
result = optimizer.optimize(tx_graph, beta=0.5)

print(f"FPR: {result.false_positive_rate:.3f}")
print(f"F-β: {result.f_beta_score:.3f}")
print(f"Flagged: {result.flagged_wallets}")
```

### Multi-Agent Pipeline

```python
from src.models import AgentInput
from src.agents.multi_agent_crew import run_aml_crew
import uuid

report = run_aml_crew(AgentInput(
    wallet_address="0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
    qubo_risk_score=0.92,
    qubo_flagged_nodes=["0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b"],
    trace_id=str(uuid.uuid4()),
))

print(f"Risk: {report.risk_level}")           # HIGH / MEDIUM / LOW
print(f"Action: {report.recommended_action}") # FREEZE / MONITOR / CLEAR
print(f"Audit Hash: {report.audit_hash}")
```

### Quapp handler.py (Direct Invocation)

```python
from src.pipeline.handler import handler

result = handler({
    "wallet_address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
    "backend": "classical",   # or "qamelion" | "perceval" | "ibm_quantum"
    "shots": 1024,
    "mode": "hybrid"
})

print(result["risk_level"])          # HIGH
print(result["recommended_action"])  # FREEZE
print(result["audit_hash"])          # sha256:...
```

---

## Environment Variables

| Variable                  | Description                                                      | Default       |
| ------------------------- | ---------------------------------------------------------------- | ------------- |
| `QUANTUM_BACKEND`       | `classical` \| `qamelion` \| `perceval` \| `ibm_quantum` | `classical` |
| `ETHERSCAN_API_KEY`     | etherscan.io API key                                             | —            |
| `OPENSANCTIONS_API_KEY` | opensanctions.org API key                                        | —            |
| `ANTHROPIC_API_KEY`     | Claude API key (for LLM agents)                                  | —            |
| `QUBO_RISK_THRESHOLD`   | Flag wallets above this score                                    | `0.85`      |
| `F_BETA`                | β parameter (< 1 = prioritize Precision)                        | `0.5`       |
| `QUAPP_API_KEY`         | Quapp.cloud project API key                                      | —            |
| `IBM_QUANTUM_TOKEN`     | IBM Quantum Network token                                        | —            |

---

## Quantum Backends

| Backend                 | Provider | Technology                    | Quapp Provider Name | Status                      |
| ----------------------- | -------- | ----------------------------- | ------------------- | --------------------------- |
| **Classical SA**  | NumPy    | Simulated Annealing           | `Quapp` (default) | ✅ Default                  |
| **Qamelion**      | Qudora   | Trapped-Ion Emulator (NFQC®) | `Quapp`           | ✅ Ready (install SDK)      |
| **Perceval**      | Quandela | Photonic SDK                  | `Quandela`        | ✅ Ready (QPU-sponsored)    |
| **Qiskit**        | IBM      | Gate-based                    | `IBM Quantum`     | ✅ Quapp-supported SDK      |
| **D-Wave Ocean**  | D-Wave   | Quantum Annealing (dimod)     | `Quapp`           | ✅ Included in requirements |
| **QPU (real HW)** | Quandela | Real quantum hardware         | `Quandela`        | 🔜 Contact support          |

> **QPU Runtime Note:** Real QPU access is sponsored by Quandela. Contact the Quapp support team (Win / Van on Discord) to request QPU runtime credentials.

---

## Data Sources

- **Training**: [Elliptic Bitcoin Dataset](https://www.kaggle.com/datasets/ellipticco/elliptic-data-set) (203,769 transactions)
- **On-chain**: Etherscan API, BSCScan API, The Graph (GraphQL)
- **Sanctions**: OpenSanctions (OFAC, EU, UN, PEPs), CryptoScamDB
- **Analytics**: Dune Analytics (SQL queries for DeFi, Tornado Cash, bridges)
- **Synthetic**: IBM AMLSim (money laundering scenario simulation)

---

## Roadmap

- [X] QUBO optimizer with F-β cost function
- [X] 3-agent CrewAI pipeline
- [X] Benchmark vs GraphSAGE / GAT / XGBoost
- [X] POC Demo UI
- [X] Security hardening + observability
- [ ] **Deploy AML pipeline as Quapp Function** (`handler.py` → Quapp.cloud)
- [ ] Quandela QPU runtime integration (contact support for access)
- [ ] Qamelion trapped-ion hardware integration
- [ ] Elliptic full dataset benchmark
- [ ] Dune Analytics live data pipeline
- [ ] arXiv preprint: "Hybrid Quantum-Agentic Architecture for Crypto AML"
- [ ] LOI with SEA crypto exchange

---

## License

MIT — QCFinOp Team · SEA Quantathon 2026
