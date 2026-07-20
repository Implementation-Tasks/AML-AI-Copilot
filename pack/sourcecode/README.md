# ⚛ AML AI Copilot

> **Quantum-Inspired Crypto AML Platform for Southeast Asia**  
> SEA Quantathon 2026 · QCFinOp Team

[![Tests](https://img.shields.io/badge/tests-28%2F28%20passed-brightgreen)](#)
[![Python](https://img.shields.io/badge/python-3.14-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-purple)](#)
[![Quapp](https://img.shields.io/badge/platform-Quapp.cloud-orange)](#)
[![perceval](https://img.shields.io/badge/SDK-perceval--quandela%201.2.4-blueviolet)](#)
[![qudora](https://img.shields.io/badge/SDK-qudora--sdk%201.1.4-cyan)](#)

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

```text
AML-AI-Copilot/
└── pack/sourcecode/             # 💻 Main Source Code
    ├── launcher.py              # 🚀 Interactive Backend Selector (START HERE)
    ├── server.py                # 🌐 FastAPI Web Server (port 7860)
    ├── quick_start.py           # 🧪 CLI test & demo runner
    ├── src/                     # Core logic
    │   ├── agents/              # CrewAI multi-agent crew
    │   ├── quantum/             # QUBO optimizer (classical/quandela/qudora)
    │   ├── pipeline/            # handler.py — Quapp.cloud entrypoint
    │   ├── data/                # Etherscan graph builder
    │   └── models.py            # Pydantic data models
    ├── DEMOCORE/                # 🖥️ Browser prototype (no setup needed)
    │   └── 04_prototype.html    # Full MVP UI (open directly in browser)
    ├── tests/                   # Automated test suite (28 tests)
    ├── .env                     # API keys & backend config
    ├── requirements.txt         # Python dependencies
    └── README.md                # This file
```

---

## 🚀 Quick Start

### Option A — Open demo in browser (no setup needed)

Open this file directly in Chrome/Edge/Firefox:

```
pack/sourcecode/DEMOCORE/04_prototype.html
```

Experience the full workflow: Input Wallet → QUBO Analysis → AI Agents → Compliance Report.

---

### Option B — Run Full Backend System

#### Step 1: Install Python dependencies

```powershell
cd "pack/sourcecode"
py -m pip install -r requirements.txt
py -m pip install fastapi uvicorn[standard]
```

#### Step 2: Configure API Keys

```powershell
# Copy example file
copy .env.example .env

# Open and fill in API keys
notepad .env
```

Important keys in `.env`:

| Key | Required | Service |
|-----|----------|---------|
| `ANTHROPIC_API_KEY` | ✅ Required | Claude AI agents |
| `ETHERSCAN_API_KEY` | 🟡 Recommended | Live blockchain data |
| `OPENSANCTIONS_API_KEY` | 🟢 Optional | Sanctions database |
| `QUAPP_API_KEY` | 🟢 Optional | Quantum cloud (Qudora) |

#### Step 3: Start the application

```powershell
py launcher.py
```

The launcher will display a menu to choose the **Quantum Backend** and then start the server.

---

## ⚛ Quantum Backend Selector

When running `py launcher.py`, the system will display a backend selection menu:

```
════════════════════════════════════════════════════════════════════════
  ⚛  AML AI COPILOT  —  QUANTUM BACKEND SELECTOR
════════════════════════════════════════════════════════════════════════

  Backend     Name                      Type               Status
  ──────────────────────────────────────────────────────────────────
  qudora      Qamelion (trapped-ion)    ⚛ Quantum Hardware ✅ Running
  quandela    Perceval (photonic)       ⚛ Quantum Hardware ✅ Running v1.2.4
  classical   Simulated Annealing       💻 Classical CPU   ✅ Running
  ──────────────────────────────────────────────────────────────────

  Choose the backend you want to use:
  [1] qudora     — Trapped-ion quantum emulator from Qudora  (Requires QUAPP_API_KEY)
  [2] quandela   — Photonic quantum simulator from Quandela
  [3] classical  — Classical optimization, no quantum SDK required (default)
```

| Backend | SDK | Description |
|---------|-----|-------------|
| `qudora` | `qudora-sdk` (+ Qiskit 2.1.2) | Trapped-ion quantum emulator from Qudora Cloud |
| `quandela` | `perceval-quandela 1.2.4` | Photonic quantum circuit simulator from Quandela |
| `classical` | No SDK required | Simulated Annealing — always available |

> **Install quantum SDK (optional):**
> ```powershell
> py -m pip install perceval-quandela   # Quandela
> py -m pip install qudora-sdk          # Qudora (Qiskit-based)
> ```
> If the SDK is not installed, the launcher will automatically ask if you want to install it now. If declined, it falls back to `classical`.

---

## 🌐 Web Interface

After starting, access:

| Endpoint | Description |
|----------|-------------|
| **http://localhost:7860** | 🖥️ Main Web UI |
| http://localhost:7860/api/screen | 📡 POST API — wallet analysis |
| http://localhost:7860/api/benchmark | 📊 POST API — run QUBO benchmark |
| http://localhost:7860/docs | 📖 Swagger API documentation |
| http://localhost:7860/health | ❤️ Health check |

### API Call Example

```bash
curl -X POST http://localhost:7860/api/screen \
  -H "Content-Type: application/json" \
  -d '{
    "wallet_address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
    "qubo_risk_score": 0.85
  }'
```

**Response:**
```json
{
  "case_id": "AML-20260719-XXXXXXXX",
  "risk_level": "HIGH",
  "recommended_action": "FREEZE",
  "qubo_risk_score": 0.92,
  "f_beta_score": 0.893,
  "audit_hash": "sha256:...",
  "summary": "..."
}
```

---

## 📊 Benchmark Results

| Model | False Positive Rate (FPR) | F-β Score (β=0.5) | Graph-Native |
|-------|:---:|:---:|:---:|
| **QUBO-Optimizer** | **0.0%** | **0.893** | ✅ |
| GraphSAGE (Standard) | 19.6% | 0.324 | ✅ |

> **QUBO reduces FPR by 19.6 percentage points** compared to GraphSAGE on synthetic scale-free graph data.

---

## 🏗 System Architecture

```text
Wallet Address Input
       │
       ▼
 ┌─────────────────────────────────────────┐
 │         Quapp.cloud Orchestrator        │  ← Async Middleware (HPC + QaaS)
 └─────────────────┬───────────────────────┘
                   │
         ┌─────────▼─────────┐
         │   QUBO Optimizer  │  ← quantum/classical backend
         │  (Qudora/Quandela │
         │   /Classical SA)  │
         └─────────┬─────────┘
                   │ risk_score ≥ 0.85
                   ├── CIWS Kill Chain → FREEZE (zero LLM latency)
                   │
         ┌─────────▼──────────────────────────┐
         │         CrewAI Agents (async)      │
         │  1. Multi-hop Flow Tracer          │
         │  2. OSINT & KYC Analyst            │
         │  3. AI Compliance Officer          │
         └────────────────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Compliance Report │  ← FREEZE / MONITOR / CLEAR
         └────────────────────┘
```

### CIWS Kill Chain Architecture

```
QUBO risk_score ≥ 0.85
        │
        ├──► FREEZE immediately (no LLM latency)   ← Kill Chain
        │
        └──► CrewAI async SAR report               ← Analysis Chain
             (seconds to minutes, non-blocking)
```

---

## 📄 Key Documents

| File | Content |
|------|---------|
| [`FULL_PROJECT_GUIDE.md`](FULL_PROJECT_GUIDE.md) | Detailed step-by-step guide to run the full project |
| [`SYSTEM_SUMMARY.md`](SYSTEM_SUMMARY.md) | System architecture summary |
| [`DEMOCORE/04_prototype.html`](DEMOCORE/04_prototype.html) | MVP prototype UI (open directly in browser) |
| [`.env.example`](.env.example) | API keys configuration template |

---

## 🔧 Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `Port already in use` | Port 7860 is occupied | Close the old app or change the port in `server.py` |
| `ModuleNotFoundError: crewai` | Dependencies not installed | `py -m pip install -r requirements.txt` |
| `AuthenticationError` | Invalid API key | Check `.env` again |
| SDK `❌ not installed` in launcher | perceval/qudora not installed | Run launcher → select backend → choose to install now |
| `python-dotenv could not parse line 35` | `.env` has an invalid text line | Check that `.env` only has `KEY=VALUE` format |

---

*MIT License — QCFinOp Team · SEA Quantathon 2026 · Platform: Quapp.cloud*
