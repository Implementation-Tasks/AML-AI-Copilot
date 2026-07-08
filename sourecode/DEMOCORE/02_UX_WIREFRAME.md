# 🖌️ UX Wireframe — AML AI Copilot MVP
**SEA Quantathon 2026 · QCFinOp Team**
**Feature:** Instant Wallet Risk Verdict
**Date:** 2026-07-04

---

## User Flow Overview

```
[Welcome / Hero Screen]
        |
        | User types / pastes wallet address
        v
[Input + Validate Screen]
        |
        | Click "ANALYZE WALLET"
        v
[Live Progress Screen]  ← 3-step animated pipeline
   Step 1: QUBO Graph Analysis (0–3s)
   Step 2: AI Agent Investigation (3–7s)
   Step 3: Generating Report (7–9s)
        |
        v
[Verdict Screen]
   ┌─ Risk Badge (HIGH/MED/LOW)
   ├─ QUBO Score gauge
   ├─ Agent findings summary
   ├─ Audit Hash + Copy button
   └─ Case ID
        |
        | Click "ANALYZE ANOTHER" or "EXPORT REPORT"
        v
[Reset to Input Screen]
```

---

## Screen 1 — Hero / Landing

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚛ AML AI Copilot                           [SEA Quantathon]   │
│                                                                 │
│       Quantum-Powered Crypto AML Detection                      │
│   Stop money laundering before it moves — in under 10 seconds  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📋 Try a demo wallet:                                   │   │
│  │  [HIGH RISK] [MEDIUM RISK] [LOW RISK] [CLEAN]            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│   [        Enter wallet address (0x...)         ] [ANALYZE →]  │
│                                                                 │
│   ✅ 0% False Positive Rate   ✅ SHA-256 Audit Hash            │
│   ✅ Quantum-Inspired QUBO    ✅ 3-Agent Investigation          │
└─────────────────────────────────────────────────────────────────┘
```

**Design notes:**
- Dark background (#0a0f1e), gradient text headline
- Demo buttons are pre-filled shortcuts, not separate screens
- Stats bar below input builds credibility instantly

---

## Screen 2 — Wallet Input (Validated State)

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚛ AML AI Copilot                                              │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │ 0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b  ✓ valid    │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   Backend: [○ Classical SA] [○ Qamelion] [○ Perceval]          │
│   Mode:    [● Hybrid] [○ Classical] [○ Quantum Sim]            │
│                                                                 │
│                 [ 🔍 ANALYZE WALLET ]                           │
│                                                                 │
│   ────────────────────────────────────────────────────────     │
│   Recent scans:  0x1a2b... HIGH   |   0x9f8e... LOW            │
└─────────────────────────────────────────────────────────────────┘
```

**Design notes:**
- Green checkmark on valid EIP-55 address; red X + error on invalid
- Backend/mode selectors are cosmetic in MVP (all resolve to SA)
- Recent scans stored in localStorage

---

## Screen 3 — Analysis Progress (Live Pipeline)

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚛ AML AI Copilot                                              │
│                                                                 │
│   Analyzing: 0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b        │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  ⚛ Step 1: QUBO Graph Analysis          ███████░░░ 70%  │  │
│   │    Building 50-node transaction graph...                 │  │
│   │                                                          │  │
│   │  🤖 Step 2: AI Agent Investigation      ░░░░░░░░░░  0%  │  │
│   │    Waiting...                                            │  │
│   │                                                          │  │
│   │  📋 Step 3: Compliance Report           ░░░░░░░░░░  0%  │  │
│   │    Waiting...                                            │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   [Live log]:  Initializing SA optimizer... nodes=50           │
└─────────────────────────────────────────────────────────────────┘
```

**Design notes:**
- Steps animate sequentially with progress bars (CSS animation)
- Live log textarea scrolls with status messages
- Cannot cancel mid-analysis (simplicity)

---

## Screen 4a — Verdict: HIGH RISK / FREEZE

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚛ AML AI Copilot                  Case: AML-20260704-D90E2F   │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │  🔴  HIGH RISK                     ⛔ FREEZE ACCOUNT      │ │
│   │      QUBO Score: 0.932             F-β Score: 0.893       │ │
│   └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│   ┌── Agent Findings ────────────────────────────────────────┐ │
│   │  🔗 Flow Tracer:   7-hop chain via Tornado Cash mixer    │ │
│   │  🔍 OSINT Analyst: Match on OFAC SDN List (0.97 conf)    │ │
│   │  📋 Compliance:    SAR filed · SHA-256 audit hash below   │ │
│   └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│   Audit Hash:  sha256:7f4a9c2e1b...d8f3a1      [📋 COPY]       │
│                                                                 │
│   [🔄 ANALYZE ANOTHER]          [⬇️ EXPORT PDF REPORT]         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Screen 4b — Verdict: LOW RISK / CLEAR

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚛ AML AI Copilot                  Case: AML-20260704-CLEAR    │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐ │
│   │  🟢  LOW RISK                      ✅ CLEAR TO PROCEED    │ │
│   │      QUBO Score: 0.124             No agents activated    │ │
│   └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│   This wallet does not match any illicit pattern in our        │
│   quantum-optimized transaction graph. No OFAC/UN/EU           │
│   sanctions match detected.                                     │
│                                                                 │
│   [🔄 ANALYZE ANOTHER]                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Map

| Component | ID | Type | Notes |
|---|---|---|---|
| Wallet input field | `#wallet-input` | `<input type="text">` | EIP-55 validation onBlur |
| Analyze button | `#analyze-btn` | `<button>` | Triggers pipeline simulation |
| Demo wallet buttons | `#demo-high`, `#demo-med`, `#demo-low`, `#demo-clean` | `<button>` | Pre-fills input |
| Progress steps | `.step-1`, `.step-2`, `.step-3` | `<div>` | CSS progress bar animation |
| Risk badge | `#risk-badge` | `<div>` | Class toggles: `risk-high`, `risk-med`, `risk-low` |
| Action badge | `#action-badge` | `<div>` | FREEZE / MONITOR / CLEAR |
| QUBO score | `#qubo-score` | `<span>` | Gauge visual |
| Audit hash | `#audit-hash` | `<code>` | Truncated + copy |
| Copy button | `#copy-hash-btn` | `<button>` | Clipboard API |
| Export button | `#export-btn` | `<button>` | Print-to-PDF or JSON download |
| Analyze another | `#reset-btn` | `<button>` | Clears state, back to input |

---

## Color System

| Token | Value | Usage |
|---|---|---|
| `--bg-primary` | `#0a0f1e` | Page background |
| `--bg-card` | `#111827` | Card surfaces |
| `--accent-quantum` | `#6c63ff` | Primary CTA, step icons |
| `--risk-high` | `#ef4444` | HIGH badge, FREEZE |
| `--risk-med` | `#f59e0b` | MEDIUM badge, MONITOR |
| `--risk-low` | `#22c55e` | LOW badge, CLEAR |
| `--text-primary` | `#f9fafb` | Headings |
| `--text-secondary` | `#94a3b8` | Supporting text |
| `--border` | `#1e293b` | Card borders |

---

*Wireframe Owner: QCFinOp Team · SEA Quantathon 2026*
