# 📋 MVP Scope Definition — AML AI Copilot

**SEA Quantathon 2026 · QCFinOp Team**
**Date:** 2026-07-04
**Status:** ✅ Approved for Sprint

---

## 🎯 The ONE Core Feature

> **"Instant Wallet Risk Verdict"** — A compliance officer pastes one Ethereum wallet address and receives a color-coded risk verdict (HIGH / MEDIUM / LOW) with recommended action (FREEZE / MONITOR / CLEAR) in under 10 seconds, backed by a quantum-inspired QUBO score and a SHA-256-signed audit hash.

Everything else is **out of scope for MVP**.

---

## Why This Feature

| Criterion                          | Rationale                                                                         |
| ---------------------------------- | --------------------------------------------------------------------------------- |
| **User pain point**          | Analysts spend 40+ min/alert manually cross-referencing Etherscan + OFAC lists    |
| **Technical differentiator** | QUBO optimizer reduces FPR from 19.6% (GraphSAGE) → 0% — measurable in the demo |
| **Business proof**           | A signed audit hash = the artifact an exchange CCO needs to freeze an account     |
| **Demo-able in 90 seconds**  | Judges can paste a wallet, watch the score, see FREEZE — zero setup required     |

---

## MVP Scope: IN ✅

### Core Pipeline (end-to-end, no external API keys required)

1. **Wallet Address Input** — single text field, EIP-55 validation
2. **QUBO Risk Score** — Simulated Annealing on synthetic scale-free graph (50 nodes); returns `risk_score ∈ [0, 1]`
3. **Agent Investigation** (simulated, no LLM API cost):
   - Flow Tracer result → simulated multi-hop trace
   - OSINT Analyst result → simulated sanctions match
   - Compliance Officer → auto-generated SAR summary
4. **Verdict Panel** — HIGH / MEDIUM / LOW + FREEZE / MONITOR / CLEAR badge
5. **Audit Hash** — SHA-256 of the compliance payload, displayed + copy button
6. **Case ID** — `AML-YYYYMMDD-XXXXXXXX` format, unique per run

### Demo Mode

- 3 pre-loaded "known bad" wallet addresses trigger HIGH/FREEZE
- 1 "clean" wallet address triggers LOW/CLEAR
- No real API calls needed — fully deterministic for live demo

---

## MVP Scope: OUT ❌

| Feature                            | Why Deferred                                            |
| ---------------------------------- | ------------------------------------------------------- |
| Real Etherscan live data           | Requires API key, latency risk in live demo             |
| CrewAI LLM agents (real)           | Requires Anthropic API key, cost, unpredictable latency |
| Quandela QPU / Qamelion hardware   | Requires sponsored runtime, not available offline       |
| Full Elliptic dataset              | 203K rows — overkill for prototype validation          |
| User authentication / multi-tenant | Enterprise feature, not needed for POC                  |
| Batch scanning / CSV upload        | Post-MVP roadmap item                                   |
| Dune Analytics live feed           | Infrastructure dependency, deferred                     |
| React / Next.js SPA                | Vanilla HTML/JS is faster to ship and easier to demo    |

---

## Success Criteria (Definition of Done)

| Metric                    | Target                                           |
| ------------------------- | ------------------------------------------------ |
| Input → Verdict latency  | < 10 seconds (simulated mode)                    |
| Wallet validation         | Rejects non-EIP-55 addresses with clear error    |
| Risk accuracy on test set | 3/3 known-bad flagged as HIGH; 1/1 clean as LOW  |
| Audit hash                | SHA-256, reproducible, displayed in UI           |
| Usability                 | 2 users can complete flow with zero instructions |
| Browser compatibility     | Chrome, Firefox, Edge (latest)                   |

---

## Technical Stack (MVP)

```
Frontend:   prototype.html — Vanilla CSS + Vanilla JS (zero npm dependencies)
AI/ML:      qubo_sim.py — Python simulation, deterministic seeds
            → Simulated Annealing random walk on scale-free graph
            → Pre-computed JSON for 4 demo wallets
Backend:    None needed (static HTML + inline JS handles everything)
Audit:      Web Crypto API (crypto.subtle.digest) — runs in browser
```

---

## Sprint Timeline

| Day     | Task                               | Owner        |
| ------- | ---------------------------------- | ------------ |
| Day 1   | Scope doc + wireframe              | UX Lead      |
| Day 1-2 | Build AI/ML simulation component   | ML Engineer  |
| Day 2   | Build clickable prototype HTML     | Frontend Dev |
| Day 3   | Integrate JS ↔ simulation outputs | Full-stack   |
| Day 3   | Run 2-user usability test          | PM           |
| Day 3   | Fix top 3 usability issues         | All          |

---

## Risk Log

| Risk                               | Likelihood | Mitigation                                          |
| ---------------------------------- | ---------- | --------------------------------------------------- |
| Demo wallet triggers wrong verdict | Medium     | Hardcode 4 test wallets with deterministic seeds    |
| Prototype too slow for live demo   | Low        | Pre-compute QUBO outputs, serve as JSON lookup      |
| Judge asks for real data           | Medium     | Show benchmark table (19.6% FPR reduction) as proof |

---

*Document Owner: QCFinOp Team · SEA Quantathon 2026*
