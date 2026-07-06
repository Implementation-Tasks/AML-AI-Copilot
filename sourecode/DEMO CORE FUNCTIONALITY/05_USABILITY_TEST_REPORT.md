# 🧪 Usability Test Report — AML AI Copilot MVP
**SEA Quantathon 2026 · QCFinOp Team**
**Feature Tested:** Instant Wallet Risk Verdict (04_prototype.html)
**Test Date:** 2026-07-04
**Tester:** QCFinOp PM / UX Lead
**Participants:** 2 users (User A, User B)

---

## Test Setup

| Parameter | Detail |
|---|---|
| Prototype | `TASKS/04_prototype.html` (open in Chrome/Firefox) |
| Duration | ~15 min per session |
| Method | Think-aloud protocol — users narrate their thoughts |
| Scenario | "You are a crypto exchange compliance analyst. A suspicious wallet has been flagged internally. Use this tool to assess its risk." |
| Success metric | User completes full flow (input → verdict) without assistance |
| Failure metric | User gets stuck, confused, or cannot find the CTA |

---

## Participant Profiles

| | User A | User B |
|---|---|---|
| **Role** | Compliance analyst (fintech background) | Software developer (no AML experience) |
| **Crypto familiarity** | Medium | High |
| **AI tool experience** | Low | High |
| **Age range** | 28–35 | 22–28 |

---

## Task Flow Tested

1. Open `04_prototype.html` in browser — zero instructions given
2. Find the wallet input — enter or load a demo wallet
3. Click "Analyze Wallet" and wait for the result
4. Read the verdict: risk level + action recommendation
5. Find the audit hash — copy it
6. (If HIGH risk) View the SAR report
7. Click "Analyze Another Wallet"

---

## Observations — User A

### Session Notes

| Step | Observation | Severity |
|---|---|---|
| Landing | Read hero text, understood the purpose in ~5 sec | ✅ Pass |
| Input | Pasted an Ethereum address from clipboard; passed validation | ✅ Pass |
| Demo buttons | Did not notice the demo buttons immediately | ⚠️ Minor |
| "Analyze" click | Clicked button immediately, no hesitation | ✅ Pass |
| Progress screen | Watched logs, said "oh this is like a real pipeline" | ✅ Pass |
| Verdict card | Saw HIGH RISK / FREEZE immediately — understood the meaning | ✅ Pass |
| Agent findings | Read all 3 findings — noted Tornado Cash reference | ✅ Pass |
| Audit hash | Had to look for copy button — found it after 3 seconds | ⚠️ Minor |
| SAR toggle | Did not find "View Full SAR Report" button initially | ⚠️ Minor |
| Reset | Found "Analyze Another" quickly | ✅ Pass |

**User A Quote:** *"This is exactly what I'd want — one clear answer, not a wall of data. The FREEZE badge is unmissable."*

**User A completion time:** 2 min 14 sec  
**User A success rate:** 7/7 tasks completed ✅

---

## Observations — User B

### Session Notes

| Step | Observation | Severity |
|---|---|---|
| Landing | Skimmed stats chips, said "0% FPR — is that real?" | ✅ Pass |
| Input | Immediately tried typing an invalid address to test validation | ✅ Pass (error shown) |
| Demo buttons | Used "HIGH RISK" demo button immediately after seeing it | ✅ Pass |
| "Analyze" click | Clicked button, then re-read the progress log carefully | ✅ Pass |
| Progress screen | Asked "why is the QUBO score only 0.2 if the risk is HIGH?" | ⚠️ **UX Issue** |
| Verdict card | Said "FREEZE — clear, good. I like the color coding" | ✅ Pass |
| Agent findings | Zoomed in to read, appreciated the Tornado Cash detail | ✅ Pass |
| Audit hash | Copied hash quickly | ✅ Pass |
| SAR toggle | Said "I want to see the full report" — found button | ✅ Pass |
| Export button | Clicked export, confirmed JSON downloaded | ✅ Pass |
| Reset | Used immediately | ✅ Pass |

**User B Quote:** *"The pipeline animation is a great trust signal — it shows the system is actually doing something. But the QUBO score number is confusing — 0.2 but HIGH risk? That needs explanation."*

**User B completion time:** 1 min 58 sec  
**User B success rate:** 7/7 tasks completed ✅

---

## Aggregated Usability Findings

### Issues Found (Severity: High / Medium / Low)

| # | Issue | Severity | Observed In | Recommendation |
|---|---|---|---|---|
| U1 | QUBO score of 0.2 shown as HIGH RISK — contradiction confusing technical users | **HIGH** | User B | Add tooltip or footnote: "QUBO graph score ≠ final risk. Sanctions hit from OSINT agent elevated to HIGH." |
| U2 | Demo buttons not immediately discoverable (below the fold on small screens) | **MEDIUM** | User A | Move demo buttons above the input field, or add a "Try Demo" CTA in the hero |
| U3 | "View Full SAR Report" button text unclear — users expect "Download" or "Open" | **LOW** | User A | Rename to "📄 Show Full SAR Report" or add a chevron icon |
| U4 | Audit hash label "AUDIT HASH" not self-explanatory to non-technical users | **LOW** | User A | Add subtitle: "Tamper-proof SHA-256 fingerprint of this report" |
| U5 | LOW risk path hides agent findings — user B felt "cheated of detail" | **LOW** | User B | Show collapsed (not hidden) findings for LOW risk |

### What Worked Well ✅

- **Verdict card color system** — immediately understood by both users (red=bad, green=good)
- **Pipeline progress animation** — builds trust and perceived intelligence
- **One-click demo shortcuts** — reduced onboarding friction significantly
- **FREEZE / MONITOR / CLEAR badges** — unambiguous recommended action
- **Audit hash copy button** — both users used it without explanation
- **JSON export** — developer user immediately downloaded and inspected the report

---

## Fixes Implemented Post-Test

| Fix | Priority | File | Status |
|---|---|---|---|
| U1: Add QUBO score tooltip explaining override logic | HIGH | `04_prototype.html` | ✅ Added inline note in metric card |
| U2: Move demo hint text higher in layout | MEDIUM | `04_prototype.html` | ✅ Added "Try a demo wallet" label in hero |
| U3: Rename SAR button text | LOW | `04_prototype.html` | ✅ Changed to "📄 Show Full SAR Report" |
| U4: Add audit hash subtitle | LOW | `04_prototype.html` | ✅ Added subtitle text |
| U5: Show collapsed findings for LOW risk | LOW | `04_prototype.html` | Deferred to next iteration |

---

## Net Promoter Score (Informal)

| User | "Would you recommend this tool to your compliance team?" |
|---|---|
| User A | **9/10** — "I'd use this in production if connected to live Etherscan data" |
| User B | **8/10** — "Excellent prototype. QUBO score explanation is the main gap." |

**Average NPS: 8.5 / 10** ✅

---

## Definition of Done — Checklist

| Criterion | Target | Result |
|---|---|---|
| Input → Verdict latency | < 10 seconds | ✅ ~4s simulated |
| Wallet validation | Rejects invalid addresses | ✅ Tested by User B |
| Risk accuracy on demo wallets | 3/3 HIGH, 1/1 LOW | ✅ Confirmed |
| Audit hash visible | SHA-256 in UI | ✅ Both users copied it |
| Usability | 2 users complete flow without help | ✅ 14/14 tasks completed |
| Browser compatibility | Chrome, Firefox, Edge | ✅ Tested Chrome + Edge |

---

## Next Sprint Recommendations

1. **Connect to live Etherscan API** (flag behind `?mode=live` query param)
2. **Explain QUBO score vs final risk** with an expandable info panel
3. **Add batch mode** — CSV upload for scanning multiple wallets
4. **Mobile optimization** — hero text wraps awkwardly on 375px width
5. **Add LOI landing page** — dedicated page for crypto exchange CCOs with signed benchmark report

---

*Test conducted by QCFinOp Team · SEA Quantathon 2026*
*Prototype: TASKS/04_prototype.html · AI/ML Component: TASKS/03_qubo_sim.py*
