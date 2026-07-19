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

### Option A — Mở demo trong trình duyệt (không cần cài gì)

Mở file này trực tiếp trong Chrome/Edge/Firefox:

```
pack/sourcecode/DEMOCORE/04_prototype.html
```

Trải nghiệm đầy đủ workflow: Input Wallet → QUBO Analysis → AI Agents → Compliance Report.

---

### Option B — Chạy Full Backend System

#### Bước 1: Cài Python dependencies

```powershell
cd "pack/sourcecode"
py -m pip install -r requirements.txt
py -m pip install fastapi uvicorn[standard]
```

#### Bước 2: Cấu hình API Keys

```powershell
# Copy file mẫu
copy .env.example .env

# Mở và điền API keys
notepad .env
```

Các key quan trọng trong `.env`:

| Key | Bắt buộc | Dịch vụ |
|-----|----------|---------|
| `ANTHROPIC_API_KEY` | ✅ Bắt buộc | Claude AI agents |
| `ETHERSCAN_API_KEY` | 🟡 Khuyến nghị | Live blockchain data |
| `OPENSANCTIONS_API_KEY` | 🟢 Tùy chọn | Sanctions database |
| `QUAPP_API_KEY` | 🟢 Tùy chọn | Quantum cloud (Qudora) |

#### Bước 3: Khởi động ứng dụng

```powershell
py launcher.py
```

Launcher sẽ hiển thị menu chọn **Quantum Backend** rồi khởi động server.

---

## ⚛ Quantum Backend Selector

Khi chạy `py launcher.py`, hệ thống sẽ hiển thị bảng chọn backend:

```
════════════════════════════════════════════════════════════════════════
  ⚛  AML AI COPILOT  —  QUANTUM BACKEND SELECTOR
════════════════════════════════════════════════════════════════════════

  Backend     Tên                      Loại               Trạng thái
  ──────────────────────────────────────────────────────────────────
  qudora      Qamelion (trapped-ion)   ⚛ Lượng tử thật   ✅ Đang chạy
  quandela    Perceval (photonic)      ⚛ Lượng tử thật   ✅ Đang chạy v1.2.4
  classical   Simulated Annealing      💻 Classical CPU   ✅ Đang chạy
  ──────────────────────────────────────────────────────────────────

  Chọn backend muốn sử dụng:
  [1] qudora     — Trapped-ion quantum emulator từ Qudora  (Cần QUAPP_API_KEY)
  [2] quandela   — Photonic quantum simulator từ Quandela
  [3] classical  — Classical optimization, không cần SDK lượng tử (mặc định)
```

| Backend | SDK | Mô tả |
|---------|-----|-------|
| `qudora` | `qudora-sdk` (+ Qiskit 2.1.2) | Trapped-ion quantum emulator từ Qudora Cloud |
| `quandela` | `perceval-quandela 1.2.4` | Photonic quantum circuit simulator từ Quandela |
| `classical` | Không cần SDK | Simulated Annealing — luôn khả dụng |

> **Cài SDK quantum (tuỳ chọn):**
> ```powershell
> py -m pip install perceval-quandela   # Quandela
> py -m pip install qudora-sdk          # Qudora (Qiskit-based)
> ```
> Nếu SDK chưa cài, launcher sẽ tự động hỏi có muốn cài ngay không. Nếu từ chối, fallback về `classical`.

---

## 🌐 Web Interface

Sau khi khởi động, truy cập:

| Endpoint | Mô tả |
|----------|-------|
| **http://localhost:7860** | 🖥️ Giao diện Web UI chính |
| http://localhost:7860/api/screen | 📡 POST API — phân tích wallet |
| http://localhost:7860/api/benchmark | 📊 POST API — chạy QUBO benchmark |
| http://localhost:7860/docs | 📖 Swagger API documentation |
| http://localhost:7860/health | ❤️ Health check |

### Ví dụ gọi API

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

| File | Nội dung |
|------|----------|
| [`HUONG_DAN_CHAY_FULL_PROJECT.md`](HUONG_DAN_CHAY_FULL_PROJECT.md) | Hướng dẫn chi tiết từng bước chạy full project |
| [`TOM_TAT_HE_THONG.md`](TOM_TAT_HE_THONG.md) | Tóm tắt kiến trúc hệ thống |
| [`DEMOCORE/04_prototype.html`](DEMOCORE/04_prototype.html) | MVP prototype UI (mở thẳng trong browser) |
| [`.env.example`](.env.example) | Mẫu cấu hình API keys |

---

## 🔧 Troubleshooting

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| `Port already in use` | Port 7860 bị chiếm | Đóng ứng dụng cũ hoặc đổi port trong `server.py` |
| `ModuleNotFoundError: crewai` | Chưa cài dependencies | `py -m pip install -r requirements.txt` |
| `AuthenticationError` | API key sai | Kiểm tra lại `.env` |
| SDK `❌ chưa cài` trong launcher | Chưa cài perceval/qudora | Chạy launcher → chọn backend → chọn cài ngay |
| `python-dotenv could not parse line 35` | `.env` có dòng text không hợp lệ | Kiểm tra `.env` chỉ có dạng `KEY=VALUE` |

---

*MIT License — QCFinOp Team · SEA Quantathon 2026 · Platform: Quapp.cloud*
