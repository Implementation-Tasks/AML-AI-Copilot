# 🧑‍🏫 Mentorship Review — Prof. Hans · 15/07/2026
## Hybrid Quantum-Agentic AML · QCFinOp Team

---

## 📋 Tổng hợp nội dung buổi họp

### Điểm mạnh được Giáo sư ghi nhận (Slide 17)
| Khía cạnh | Đánh giá |
|---|---|
| **Architecture Soundness** | Graph-to-QUBO mapping là cách tiếp cận rất hiệu quả để áp dụng quantum vào bảo mật tài chính. Isolation problem được xác định đúng. |
| **Feature Engineering** | 11 AML indicators + dynamic masking + robust percentile normalization → đầu vào ổn định, không thiên lệch (bias-resistant). |
| **NISQ Practicality** | Top-20 modularization phản ánh đúng các ràng buộc của phần cứng lượng tử hiện tại (NISQ). |
| **Hybrid Handover** | Multi-agent AI layer giải quyết đúng vấn đề explainability gap của raw quantum bitstrings. SHA-256 audit trail là feature compliance mạnh. |

---

## ⚡ 3 Bottleneck Giáo sư Xác Định

### Bottleneck 1 — Smurfing / Stealth Transactions (Slide 14)
> **Vấn đề:** Các giao dịch nhỏ lẻ phân mảnh (smurfing) hoạt động giống như mục tiêu tàng hình trên radar (low Radar Cross Section). Hệ thống hiện tại có thể bỏ qua.
>
> **Đề xuất của GS:** Áp dụng **Multi-dimensional tensor decomposition** trên tensor tương tác (wallet × time). Dùng spatial correlation algorithms tương tự **MIMO reconstruction** để gom các micro-transaction phân mảnh thành một threat signature trước khi đưa vào QUBO stage.

> [!IMPORTANT]
> GS Hans đặc biệt nhấn mạnh sự tương đồng giữa MIMO (5G) và bài toán mapping của chúng ta — đây là insight rất quan trọng để phát triển pre-processing pipeline.

### Bottleneck 2 — Interception Latency (Slide 15)
> **Vấn đề:** Pipeline hiện tại: `QAOA → CrewAI Agents → FREEZE decision`. Multi-agent LLM không deterministic, gây trễ seconds-to-minutes — không đạt yêu cầu real-time interception.
>
> **Đề xuất (CIWS-Inspired Decoupling):**
> - **Kill Chain:** QAOA/QUBO optimizer tự động trigger **FREEZE ngay lập tức** khi vượt ngưỡng (qua smart-contract hoặc API).
> - **Analysis Chain:** CrewAI agents chạy **song song (parallel)**, chỉ để tạo SAR-ready compliance report & audit trail.

### Bottleneck 3 — Physical-Layer Anti-Spoofing (Slide 16)
> **Vấn đề:** Nếu adversary biết hệ thống dùng Etherscan/The Graph, họ có thể inject Sybil data, exploit RPC delays, hoặc poison telemetry stream.
>
> **Đề xuất bảo vệ:**
> 1. Multi-node RPC consensus — query nhiều independent nodes và cross-verify state hash
> 2. Strict cryptographic payload signing trước khi chấp nhận dữ liệu
> 3. Threshold routing: nếu verification fails → flag "jammed/spoofed" và fallback sang redundancy pipeline
> 4. Hard timeouts trên Quapp.cloud orchestrator để ngăn pipeline blocking

---

## 🔧 2 Refinements Kỹ Thuật Cần Thực Hiện (Slide 18)

### Refinement 1 — Hamiltonian Calibration
- Định nghĩa rõ ràng giới hạn chấp nhận được cho **QAOA depth parameter p**
- Vẽ trade-off curve: **circuit noise vs approximation ratio** trên target hardware/simulator
- Mục tiêu: chứng minh khả năng **practical NISQ readiness**

### Refinement 2 — Classical Weight Sensitivity Analysis
- Phân tích sensitivity/ablation cho các classical weights **ωk** và thresholds **τM, τH**
- Câu hỏi cần trả lời: Verdict distribution thay đổi thế nào khi weight ±20%?
- Vẽ **false-positive rate surface**

---

## 📬 Q&A Summary

| # | Câu hỏi | Câu trả lời của GS |
|---|---|---|
| 1 | Nguồn dữ liệu AML | Dùng **virtual data + mixed data** — khả thi nhất cho dự án |
| 2 | Hướng nghiên cứu & Model Validation | Ưu tiên số 1: **upgrade và hoàn thiện architecture hiện tại** |
| 3 | MIMO Architecture | MIMO có sự tương đồng lớn với dự án; được dùng một phần trong mapping process (VD: MIMO trong 5G) |
| 4 | Algorithm Optimization vs Qiskit Platform | Tiếp cận từng bước. **Ưu tiên #1: Algorithm Optimization** → sau đó mới áp dụng lên platform khác |
| 5 | Kênh liên lạc | Zalo hoặc Gmail; GS sẽ dùng **Email** là kênh chính |
| 6 | Next Steps | GS Hans đến **Quy Nhơn thứ 6 tuần tới** để giới thiệu thêm về các quantum simulators khác |

---

## 🗺️ 4 Deliverables Tiếp Theo (Slide 19)

> [!IMPORTANT]
> Đây là các deliverables cụ thể GS yêu cầu trước buổi **30-min Virtual Deep-Dive** (trong vòng 2 tuần):

| # | Deliverable | Mô tả |
|---|---|---|
| **D1** | Network Topology Graph | Full local transaction graph visualization với risk-score overlays cho seed wallet |
| **D2** | Signal Processing Flowchart | Chi tiết classical pre-processing + **tensor-decomposition pipeline** cho stealth detection |
| **D3** | Fault Tree Analysis (FTA) | Systematic identification of single points of failure trong hybrid kill-chain & analysis-chain |
| **D4** | 30-min Virtual Deep-Dive | Schedule trong 2 tuần tới để review 3 deliverables trên |

---

## 👥 Phân Công Nhiệm Vụ — Post-Mentorship Sprint

> Dựa trên feedback của GS Hans, đây là phân công nhiệm vụ theo vai trò từng thành viên:

---

### 🧑‍💼 Thành — Nhóm Trưởng · Prompt Engineer

**Trách nhiệm chính:** Điều phối tổng thể + tối ưu hóa AI Agent layer

#### Nhiệm vụ ưu tiên cao:
- [ ] **[D3] Fault Tree Analysis (FTA):** Vẽ fault tree cho cả kill-chain (QAOA → FREEZE) và analysis-chain (CrewAI). Xác định Single Points of Failure (SPOF) trong pipeline hiện tại.
- [ ] **Implement CIWS Decoupling (Bottleneck 2):** Tách FREEZE trigger ra khỏi CrewAI — QAOA tự trigger FREEZE, CrewAI chạy async để tạo report. Sửa file [`handler.py`](file:///C:/Users/ACE%20DUKE/OneDrive/Máy%20tính/AML/AML-AI-Copilot/pack/sourecode/src/pipeline/handler.py) và [`multi_agent_crew.py`](file:///C:/Users/ACE%20DUKE/OneDrive/Máy%20tính/AML/AML-AI-Copilot/pack/sourecode/src/agents/multi_agent_crew.py).
- [ ] **Prompt Engineering cho Compliance Officer:** Cải tiến prompt của Compliance Officer agent để tích hợp quantum evidence score ζQ vào final risk score R một cách rõ ràng hơn.
- [ ] **Email GS Hans:** Soạn email follow-up về next steps và lịch họp 30-min virtual deep-dive.

#### Nhiệm vụ thứ cấp:
- [ ] Điều phối lịch họp nội bộ trước khi GS đến Quy Nhơn (thứ 6 tuần tới)
- [ ] Review và hợp nhất output từ Tú, Syauqi & Farchy

---

### 📊 Tú — Data Scientist

**Trách nhiệm chính:** Dữ liệu, model validation & feature engineering

#### Nhiệm vụ ưu tiên cao:
- [ ] **[D1] Network Topology Graph:** Tạo full visualization của transaction graph với risk-score overlays (dùng NetworkX + Matplotlib hoặc Plotly). Data nguồn: [`elliptic_txs_features.csv`](file:///C:/Users/ACE%20DUKE/OneDrive/Máy%20tính/AML/AML-AI-Copilot/pack/dataset/elliptic_txs_features.csv) + edgelist.
- [ ] **Refinement 2 — Weight Sensitivity Analysis:** Phân tích sensitivity của weights ωk và thresholds (τM, τH) trong final compliance score R. Vẽ false-positive rate surface khi weight thay đổi ±20%.
- [ ] **Virtual + Mixed Data Setup:** Theo khuyến nghị của GS, setup pipeline dùng **IBM AMLSim** để generate virtual data + kết hợp với Elliptic dataset (mixed data approach).

#### Nhiệm vụ thứ cấp:
- [ ] Chạy full Elliptic dataset benchmark (203,769 transactions) — hiện đang `in progress` theo README
- [ ] Chuẩn bị số liệu validation để hỗ trợ Hamiltonian Calibration (cho Syauqi & Farchy)

---

### 🔧 Syauqi & Farchy — Information Engineers

**Trách nhiệm chính:** Quantum core, system architecture & anti-spoofing

#### Nhiệm vụ ưu tiên cao — Syauqi:
- [ ] **[D2] Signal Processing Flowchart — MIMO/Tensor Stage:** Thiết kế và vẽ detailed flowchart cho classical pre-processing pipeline, bao gồm **tensor decomposition stage** cho smurfing detection. Tham chiếu MIMO spatial multiplexing cho phần clustering.
- [ ] **Bottleneck 1 — MIMO Tensor Module:** Prototype module tensor decomposition (wallet × time tensor) sử dụng `numpy` hoặc `tensorly`. Tích hợp vào data pipeline trước QUBO stage trong [`graph_to_qubo.py`](file:///C:/Users/ACE%20DUKE/OneDrive/Máy%20tính/AML/AML-AI-Copilot/pack/sourecode/src/quantum/graph_to_qubo.py).

#### Nhiệm vụ ưu tiên cao — Farchy:
- [ ] **Refinement 1 — Hamiltonian Calibration:** Định nghĩa explicit bounds cho **QAOA depth parameter p**. Vẽ noise-vs-accuracy trade-off curve trên simulator (Qiskit/Perceval). Sửa [`hybrid_optimizer.py`](file:///C:/Users/ACE%20DUKE/OneDrive/Máy%20tính/AML/AML-AI-Copilot/pack/sourecode/src/quantum/hybrid_optimizer.py).
- [ ] **Bottleneck 3 — Anti-Spoofing Layer:** Implement data verification layer trong [`agent_tools.py`](file:///C:/Users/ACE%20DUKE/OneDrive/Máy%20tính/AML/AML-AI-Copilot/pack/sourecode/src/tools/agent_tools.py) và [`security.py`](file:///C:/Users/ACE%20DUKE/OneDrive/Máy%20tính/AML/AML-AI-Copilot/pack/sourecode/src/security.py): multi-node RPC consensus, payload signing, threshold routing.

#### Nhiệm vụ thứ cấp (cả hai):
- [ ] Nghiên cứu các quantum simulators GS Hans sẽ giới thiệu tại Quy Nhơn (chuẩn bị câu hỏi)
- [ ] Chuẩn bị để tích hợp lên Qiskit Platform sau khi algorithm optimization hoàn thành

---

## 📅 Timeline Đề Xuất

```
Tuần này (T2 → T5):
├── Thành:   FTA draft + implement CIWS decoupling
├── Tú:      Network Topology Graph + Sensitivity Analysis setup
├── Syauqi:  Signal Processing Flowchart + Tensor Module prototype
└── Farchy:  QAOA p-parameter calibration + Anti-Spoofing layer

Thứ 6 tuần tới:
└── GS Hans tới Quy Nhơn → giới thiệu quantum simulators mới

Trong 2 tuần:
└── Nộp D1 + D2 + D3 cho GS → Schedule 30-min Virtual Deep-Dive
```

---

## 🔑 Key Insights từ GS Hans

> [!TIP]
> **MIMO analogy là gợi ý kỹ thuật quan trọng nhất:** Tương tự như MIMO trong 5G phục hồi tín hiệu yếu từ nhiễu, hệ thống của chúng ta cần phục hồi các pattern smurfing phân mảnh từ "nhiễu" giao dịch thông thường. Đây là hướng đi cho Bottleneck 1.

> [!NOTE]
> **Priority là algorithm optimization, không phải platform migration.** GS nhấn mạnh: hoàn thiện core algorithm trước, Qiskit/Quapp integration là bước tiếp theo sau khi system đã ổn định.

> [!IMPORTANT]
> **Liên lạc với GS qua Email** — chuẩn bị email follow-up với 3 deliverables và đề xuất lịch 30-min deep-dive.
