# ⚛ AML AI Copilot

> **Quantum-Inspired Crypto AML Platform for Southeast Asia**
> SEA Quantathon 2026 · QCFinOp Team

[![Tests](https://img.shields.io/badge/tests-28%2F28%20passed-brightgreen)](#)
[![Python](https://img.shields.io/badge/python-3.14-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-purple)](#)
[![Quapp](https://img.shields.io/badge/platform-Quapp.cloud-orange)](#)

---

## 🌟 Project Overview

Crypto exchanges in Southeast Asia face a **90% false positive rate** in AML alerts — every false alert freezes a legitimate user account and wastes analyst time. Current rule-based systems cannot process the complex multi-hop, cross-chain patterns used by sophisticated money launderers.

**Our Solution:**  
A **Hybrid Quantum-Agentic AML Platform** combining the power of quantum-inspired computing and autonomous AI agents:

1. **QUBO Optimizer**: Converts blockchain transaction graphs into QUBO matrices and solves them with quantum-inspired algorithms (Qamelion / Perceval / Simulated Annealing). Explicitly penalizes false positives via the F-β cost function (β=0.5).
2. **Multi-Agent AI Crew (CrewAI)**: 3 autonomous agents activate on high-risk flags:
   - *Flow Tracer*: Traces multi-hop cash flows via Etherscan + The Graph.
   - *OSINT Analyst*: Cross-references OFAC, EU, UN sanctions + CryptoScamDB.
   - *Compliance Officer*: Generates SHA-256 audit-ready AML reports.
3. **Quapp.cloud Orchestration**: The central Launchpad for Quantum Builders acting as async middleware connecting Classical HPC + Quantum-as-a-Service.

---

## 📁 Project Structure

The repository is organized as follows:

```text
AML-AI-Copilot 8.7/
├── sourecode/               # 💻 Main Source Code (AI & Quantum Systems)
│   ├── src/                 # Core logic (QUBO, AI Agents, Data Pipelines)
│   ├── tests/               # Automated Test Suite (Unit tests)
│   ├── DEMOCORE/            # 🚀 MVP and Prototype (Static web UI & QUBO Sim)
│   ├── README.md            # Detailed technical documentation for the backend
│   ├── AML_AI_Copilot_Strategic_Report_V3.md  # Tech & Business Strategy Report
│   └── requirements.txt     # Python dependencies
│
├── corematerials/           # 📚 Core References (PDFs)
│   └── Research papers on AI & Quantum Computing in Financial Crime.
│
├── archive/                 # 🗄️ Archived and old data
│
└── README.md                # 📄 Master Project Overview (This file)
```

---

## 🚀 Quick Start

### 1. Interactive Demo Prototype (No setup required)
The MVP prototype is designed to run directly in your browser without any backend servers:
- Open `sourecode/DEMOCORE/04_prototype.html` in any modern browser (Chrome/Edge/Firefox).
- Experience the complete workflow (Input Wallet -> QUBO Analysis -> AI Agents Analysis -> Compliance Report).

### 2. Backend System Setup
To run the core backend components locally (Requires Python 3.14):

```bash
# 1. Navigate to the source code directory
cd sourecode

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env with your API keys (Etherscan, OpenSanctions, Anthropic, etc.)

# 4. Run tests (Ensure 28/28 pass)
python -m pytest tests/ -v

# 5. Run the Benchmark suite
python -m src.quantum.benchmark --demo
```

### 3. Run DemoCore Simulation (Python)
The `DEMOCORE` folder includes a script to simulate the analysis pipeline without needing real API keys:
```bash
cd sourecode/DEMOCORE

# Analyze a specific demo wallet
python 03_qubo_sim.py 0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b
```

---

## 📊 Benchmark Results

Compared to industry-standard GraphSAGE models, our QUBO Optimizer delivers exceptional performance:

| Model                    | False Positive Rate (FPR) | F-β Score (β=0.5) | Graph-Native Processing |
| ------------------------ | :-----------------: | :-----------: | :-------------: |
| **QUBO-Optimizer**       |   **0.0%**          |     **0.893**     |       ✅       |
| GraphSAGE (Standard)     |        19.6%        |     0.324     |       ✅       |

> **QUBO reduces the FPR by 19.6 percentage points** compared to GraphSAGE on synthetic scale-free graph data.

---

## 🏗 System Architecture

```text
Wallet Address Input
       │
       ▼
 ┌─────────────────────────────────────────┐
 │         Quapp.cloud Orchestrator        │  ← Central Async Middleware (HPC + QaaS)
 └─────────────────┬───────────────────────┘
                   │
         ┌─────────▼─────────┐
         │   QUBO Optimizer  │  ← Quantum-inspired optimization penalizing false positives
         └─────────┬─────────┘
                   │ If risk_score > 0.85
         ┌─────────▼──────────────────────────┐
         │         CrewAI Agents              │
         │  1. Multi-hop Flow Tracer          │
         │  2. OSINT & KYC Analyst            │
         │  3. AI Compliance Officer          │
         └────────────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Compliance Report │  ← Verdict: FREEZE / MONITOR / CLEAR
         └────────────────────┘
```

---

## 📄 Key Documents to Read

1. **[Backend Architecture & Technical Specs](sourecode/README.md)**: Deep dive into the Quapp handler architecture, hybrid quantum implementations, and environment variables.
2. **[Strategic Report V3](sourecode/AML_AI_Copilot_Strategic_Report_V3.md)**: Analysis of startup feasibility, Bounty Hunting business model, hardware-agnostic quantum strategy, and Q&A.
3. **[UX/UI Wireframes & MVP Scope](sourecode/DEMOCORE/02_UX_WIREFRAME.md)**: Detailed user flow and MVP definitions for the platform's interface.

---
*MIT License — QCFinOp Team · SEA Quantathon 2026*
