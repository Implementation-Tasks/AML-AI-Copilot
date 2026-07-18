# MENTORSHIP REVIEW: Hybrid Quantum-Agentic AML System
**QAOA-Oriented Architecture for Anti-Money Laundering & False Positive Reduction | Architectural Bottlenecks & Next Steps**

* **Presenter:** Prof. Minseok Han
* **Date:** July 15th, 2026

---

## 01. System Motivation & Scope

### Motivation: Why Graph + Quantum for AML?
* **Isolation Problem:** A suspicious wallet often looks normal when viewed alone. Patterns emerge only across multi-hop fund flows, rapid movement, structuring, and risky counterparties.
* **Combinatorial Explosion:** Multi-hop transaction networks create combinatorial risk limits that classical exhaustive search cannot scale. QUBO (Quadratic Unconstrained Binary Optimization) maps this naturally to quantum optimization.
* **False Positive Burden:** Compliance teams are overwhelmed by alerts. The objective explicitly prioritizes Precision ($F_{\beta}$ with $\beta=0.5$) and penalizes over-flagging of known licit entities.

### Scope: Threat Model & NISQ Realism
* **Threat Coverage:**
  * Structuring/Smurfing (fragmented micro-transfers)
  * Layering across multiple hops & chains
  * Cross-border / cross-chain obfuscation
  * Mixer, bridge, and sanctioned entity exposure
  * Rapid fund movement (velocity anomalies)
* **NISQ Constraint Strategy:**
  * $1 \text{ qubit} = 1 \text{ wallet decision}$.
  * If hardware $\le 20$ qubits, the full graph is reduced via classical modularization into a high-risk Top-20 subgraph.
  * QAOA is applied only to this focused combinatorial core.
  * This preserves AML logic while remaining executable on near-term devices.

---

## 02. Architecture & Mathematical Core

### Hybrid Pipeline at a Glance
```
[01 Wallet Input] ──(0x validation)──> 
[02 On-Chain Graph] ──(Directed Tx)──> 
[03 Risk Features] ──(11 indicators)──> 
[04 Top-20 Subgraph] ──(NISQ ready)──> 
[05 QUBO Matrix] ──(C(x) = xᵀQx)──> 
[06 QAOA Solve] ──(Binary flags)──> 
[07 Agent Enrich] ──(OSINT + Flow)──> 
[08 Verdict & Audit] ──(SHA-256 JSON)
```

* **Key Design Principle:** Classical layers handle data ingestion, feature engineering, subgraph selection, and final compliance scoring. Quantum (QAOA) is reserved exclusively for the combinatorial binary flagging decision on the critical Top-20 wallets. Multi-agent AI then supplies explainability and off-chain enrichment that pure quantum output cannot provide.

### Classical Layer: Transaction Graph & Raw AML Features
* **Directed Graph Construction:**
  $$G=(V,E), \quad e_{ij}=(i, j, A_{ij}, t_{ij}, c_{ij})$$
  Bounded by hop distance $H$ from seed wallet $a$ and global node capacity $|V| \le N_{\max}$. Let $T_i$ be the set of edges incident on wallet $i$.
* **Core Feature Set (Selected):**
  * $y_{\text{amt}}$: Amount anomaly vs. peer median/MAD (Median Absolute Deviation)
  * $y_{\text{freq}}$: Transaction frequency in $\Delta T$
  * $y_{\text{struct}}$: Structuring/smurfing ratio
  * $y_{\text{rapid}}$: Max exponential velocity score
  * $y_{\text{seq}}$: Rapid in-out sequence ratio
  * $y_{\text{net}}$: PageRank + Centrality composite
  * $y_{\text{crypto}}$: Mixer/bridge/obfuscation flag
  * $y_{\text{cp}}$: Max external counterparty risk

### Risk Scoring: Normalization, Masking & Node Risk Score
* **Robust Percentile Normalization:**
  $$\varphi_{i}^{k} = \text{clip}\left( \frac{y_{i}^{k} - \text{median}(y^k)}{P_{98}(y^k) - \text{median}(y^k) + \epsilon}, 0, 1 \right)$$
* **Dynamic Masking:** $m_{i}^{k} = 1$ if feature $k$ is available, else $0$ (prevents false bias from missing data).
* **Unified Node Risk Score:**
  $$r_{i} = \frac{\sum_{k} m_{i}^{k} w_{k} \varphi_{i}^{k}}{\sum_{k} m_{i}^{k} w_{k} + \epsilon} \quad \rightarrow \quad \tilde{r}_{i} = \text{clip}(r_{i}, 0, 1)$$
  * Weights $w_{k}$ are calibrated from historical labeled cases.
  * The final clipped score $\tilde{r}_{i}$ becomes the primary classical signal fed into both subgraph selection and the linear term of the QUBO.

### NISQ Bridge: Top-20 Subgraph Modularization
* **Priority Score:**
  $$s_{i} = \lambda_{r} \tilde{r}_{i} + \lambda_{c} \text{Centrality}_{i} + \lambda_{p} \text{PathRisk}_{i} + \Lambda_{\text{seed}} \mathbb{I}[i = a]$$
  $$V_{20} = \text{TopK}_{20}(V, s) \quad \text{where } a \in V_{20} \text{ is always enforced.}$$
  $$G_{20} = G[V_{20}]$$
  $$n = |V_{20}| \le 20, \quad x_{i} \in \{0, 1\} \text{ (flag decision)}$$
* **Why This Matters:**
  1. Keeps quantum circuit depth and qubit count within NISQ reach.
  2. Preserves the highest-risk combinatorial core.
  3. Classical priority scoring is fully auditable.
  4. Seed wallet is never dropped from the subgraph.
  5. Enables fair classical vs. quantum benchmarking.

---

## 03. QUBO & Ising Mapping

### QUBO Core: Transforming AML Risk into QUBO
$$C(x) = \sum_{i} q_{i} x_{i} + \sum_{i < j} q_{ij} x_{i} x_{j} = x^{T} Q x$$

* **Linear Term (Node):**
  $$q_{i} = -\alpha(1 + \beta^{2})\tilde{r}_{i} + \mu_{L} L_{i}$$
  * Rewards flagging of high-risk wallets.
  * $\beta = 0.5$ prioritizes Precision ($F_{\beta}$).
  * $\mu_{L}$ penalizes known licit wallets ($L_{i} = 1$).
  * $\alpha$ scales the overall risk contribution.
* **Pairwise Term (Edge):**
  $$q_{ij} = \lambda_{\text{FP}} u_{ij} - \eta e_{ij}$$
  $$u_{ij} = (1 - e_{ij}) \cdot \min\left( \frac{A_{ij}}{A_{\max}}, 1 \right)$$
  * $e_{ij}$ represents the edge risk score.
  * $\lambda_{\text{FP}}$ suppresses weak-evidence pairs (explicit false-positive control).
  * $\eta$ rewards true risk coupling.

### Ising Mapping: QUBO $\rightarrow$ Ising Hamiltonian
Variables map as $x_{i} = (1 - z_{i})/2$, where $z_{i} \in \{+1, -1\}$.

* **Constant:**
  $$C_{0} = \frac{1}{2} \sum_{i} q_{i} + \frac{1}{4} \sum_{i < j} q_{ij}$$
* **Linear Field:**
  $$h_{i} = -\frac{1}{2} q_{i} - \frac{1}{4} \sum_{j \ne i} q_{ij}$$
* **Coupling:**
  $$J_{ij} = \frac{1}{4} q_{ij}$$
* **Cost Hamiltonian (Circuit-ready):**
  $$H_{C} = \sum_{i} h_{i} Z_{i} + \sum_{i < j} J_{ij} Z_{i} Z_{j}$$
  * *Note:* Constant $C_{0}$ is omitted from the quantum circuit (does not change the $\text{argmin}$ bitstring).

### QAOA Execution: Optimization Circuit & Binary Output
* **QAOA State Preparation:**
  $$|\psi(\gamma,\beta)\rangle = \prod_{l=1}^{p} e^{-i \beta_{l} H_{M}} e^{-i \gamma_{l} H_{C}} |+\rangle^{\otimes n}$$
  * Mixer: $H_{M} = \sum_{i} X_{i}$
  * Classical optimizer: $(\gamma^{*}, \beta^{*}) = \arg\min \langle \psi(\gamma,\beta) | H_{C} | \psi(\gamma,\beta) \rangle$
  * Measurement $\rightarrow$ bitstring $b \in \{0, 1\}^{n}$, yielding direct mapping $x_{i} = b_{i}$.
* **Quantum Evidence Score:**
  $$q_{i}^{Q} = \frac{1}{M} \sum_{m=1}^{M} b_{i}^{(m)}$$
  $$\zeta_{i}^{Q} = \frac{b_{i}^{*} + q_{i}^{Q}}{2}$$
  * Marginal flag probability from shots ($q_{i}^{Q}$) + best sampled solution ($b_{i}^{*}$), combined into a single quantum evidence score $\zeta_{i}^{Q}$ for the downstream classical agent.

---

## 04. Multi-Agent Compliance Layer

### Multi-Agent Compliance Investigation Roles
* **Flow Tracer:** Maps multi-hop fund paths from flagged wallets, reconstructs layering sequences, and quantifies velocity and volume concentration.
* **OSINT Analyst:** Queries OpenSanctions, CryptoScamDB, PEP lists, and adverse media. Returns normalized external risk scores: $E$ (Exposure), $S$ (Sanctions), $C$ (CryptoScam), $O$ (Other).
* **Compliance Officer:** Aggregates quantum evidence $\zeta_{a}^{Q}$ with off-chain signals into a final score $R_{a}$. Applies deterministic FREEZE / MONITOR / CLEAR rules.

### Decision: Final Compliance Score & Action Rules
$$R_{a} = \text{clip}\left( \omega_{r} \tilde{r}_{a} + \omega_{q} \zeta_{a}^{Q} + \omega_{E} E_{a} + \omega_{S} S_{a} + \omega_{C} C_{a} + \omega_{O} O_{a}, 0, 1 \right)$$
* *Constraint:* All weights $\omega \ge 0$ and $\sum \omega = 1$. Weights and thresholds are calibrated on historical labeled cases.

#### Action Rules:
* 🔴 **FREEZE:** $R \ge \tau_{H}$ or confirmed Sanctions/PEP hit.
* 🟡 **MONITOR:** $\tau_{M} \le R < \tau_{H}$.
* 🟢 **CLEAR:** $R < \tau_{M}$.

---

## 05. Architectural Bottlenecks

### Bottleneck 1: Stealth Transactions (Smurfing Low-RCS Targets)
* **Radar Analogy:** When a target's Radar Cross Section (RCS) is minimized, single-sensor detection fails. MIMO spatial multiplexing + coherent integration over time recovers the signal from the noise floor. Smurfing is the financial equivalent of RCS reduction: many small, seemingly disconnected transfers that individually fall below reporting thresholds.
* **Proposed Enhancement:** Multi-dimensional tensor decomposition of the wallet-time interaction tensor. Apply spatial correlation algorithms (analogous to MIMO reconstruction) to cluster fragmented micro-transactions into a single high-probability threat signature before they reach the QUBO stage.

### Bottleneck 2: Interception Latency (Agentic Halting vs. CIWS)
* **Current Path (Potential Bottleneck):**
  `QUBO/QAOA (risk score ≥ 0.85) ──> CrewAI Multi-Agent (Flow Tracer + OSINT + Compliance) ──> FREEZE decision`
  * Multi-agent LLM frameworks are non-deterministic and introduce seconds-to-minutes of latency. This is incompatible with true real-time interception.
* **CIWS-Inspired Decoupling (Recommended):** Separate the *Kill Chain* from the *Analysis Chain*.
  * **Kill Chain:** The QAOA / QUBO optimizer itself triggers an immediate, automated smart-contract or API `FREEZE` halt when the threshold is breached.
  * **Analysis Chain:** CrewAI agents run in parallel, post-engagement, solely to generate the SAR-ready (Suspicious Activity Report) compliance report and audit trail.
  * **Result:** Achieves near-millisecond interception while retaining full explainability.

### Bottleneck 3: Physical-Layer Security (Anti-Spoofing)
* **Threat Surface:** If the adversary knows the system relies on Etherscan, Alchemy, or The Graph, they can:
  * Inject Sybil transaction data.
  * Exploit RPC node delays or forks.
  * Poison the telemetry stream before it reaches the orchestrator.
* **Defense Measures:**
  1. **Multi-node RPC consensus:** Query independent nodes and cross-verify state hash.
  2. **Strict payload signing:** Cryptographic integrity check before acceptance.
  3. **Threshold routing:** If verification fails $\rightarrow$ flag as "jammed/spoofed" and fall back to the redundancy pipeline.
  4. **Quapp.cloud orchestrator:** Enforce hard timeouts to prevent pipeline blocking.

---

## 06. Expert Evaluation Insights
* **Architecture Soundness:** Graph-to-QUBO mapping is a highly effective way to leverage quantum algorithms for financial security. The isolation problem is correctly identified.
* **Feature Engineering:** 11 AML indicators + dynamic masking + robust percentile normalization provide stable, bias-resistant inputs to the quantum stage.
* **NISQ Practicality:** Top-20 modularization mirrors localized constraints used in distributed dynamic systems; preserves structural integrity while remaining executable.
* **Hybrid Handover:** Multi-agent AI layer correctly addresses the explainability gap inherent in raw quantum bitstrings. SHA-256 audit trail is a strong compliance feature.

---

## 07. Refinements & Next Steps

### Recommended Technical Improvements
1. **Hamiltonian Calibration:**
   The QAOA depth parameter $p$ critically influences solution quality versus noise. Explicitly define acceptable bounds for $p$ and demonstrate the trade-off curve between circuit noise and approximation ratio on target hardware (or high-fidelity simulator). This strengthens the claim of practical NISQ readiness.
2. **Classical Weight Sensitivity:**
   Final score $R$ depends on classically calibrated weights $\omega_{k}$ and thresholds $\tau_{M}, \tau_{H}$. Conduct a brief sensitivity / ablation analysis:
   * How does the verdict distribution shift under $\pm 20\%$ weight perturbation?
   * What is the false-positive rate surface?
   * Documenting this robustness will materially strengthen the final system pitch.

### Proposed Collaboration & Mentorship Path
1. **Network Topology Graph (01):** Deliver the full local transaction graph visualization with risk-score overlays for the seed wallet.
2. **Signal Processing Flowchart (02):** Detailed classical pre-processing and tensor-decomposition pipeline for stealth detection.
3. **Fault Tree Analysis (03):** Systematic identification of single points of failure in the hybrid kill-chain and analysis-chain.
4. **30-min Virtual Deep-Dive (04):** Schedule within the next two weeks to review the three deliverables and align on refinement priorities.

---

## Closing
> **Bridging Defense-Grade Signal Processing with Quantum-Financial Security**
> 
> * The architecture is mathematically rigorous and NISQ-aware.
> * The three bottlenecks identified in the mentorship proposal are addressable with concrete engineering actions.
> * We look forward to the Network Topology, Signal Flow, and FTA deliverables.
> 
> **Questions & Discussion**
