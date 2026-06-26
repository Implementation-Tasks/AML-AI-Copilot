# Spec: Quantum-Ready Backend (HybridQuantumOptimizer)

## Objective
Chuyển đổi blockchain transaction graph thành bài toán QUBO, chạy quantum-inspired optimization để minimize False Positive Rate (FPR) trong AML detection.

**Mục tiêu**: FPR < 10% (baseline GraphSAGE ~30%) | F-β score (β=0.5) > 0.90

## Tech Stack
- **QUBO Formulation**: D-Wave Ocean SDK (dimod library)
- **Quantum Simulator A**: Qamelion Emulator (Qudora, noise_model="nisq_standard")  
- **Quantum Simulator B**: Perceval SDK (Quandela, photonic architecture)
- **Classical Fallback**: SimulatedAnnealing + Tensor Networks (tensorcircuit)
- **Graph Processing**: NetworkX + DGL (Deep Graph Library)
- **Benchmark**: Scikit-learn (GNN baselines), XGBoost

## Objective Function (F-β với β < 1)
```
F_β = (1 + β²) × Precision × Recall / (β² × Precision + Recall)

Precision = TP / (TP + FP)   ← tối đa hóa (giảm False Positives)
Recall    = TP / (TP + FN)

β = 0.5  → Precision quan trọng gấp đôi Recall
```

**QUBO Cost Function:**
```
C(x) = -Σ(precision_i × x_i) + λ × Σ(false_positive_ij × x_i × x_j)
```

## Commands
```bash
# Test QUBO mapping
pytest tests/test_qubo_mapping.py -v

# Run benchmark vs baselines
python -m src.quantum.benchmark --dataset elliptic --output reports/

# Test specific backend
python -m src.quantum.hybrid_optimizer --backend qudora --test-mode

# Validate QUBO output
python -m src.quantum.validate --qubo-matrix output/qubo_sample.npy
```

## Data Contracts

### Input: Transaction Graph
```python
@dataclass
class TransactionGraph:
    graph: nx.DiGraph             # nodes=wallets, edges=transactions
    node_features: dict[str, np.ndarray]  # wallet features
    edge_features: dict[tuple, np.ndarray]  # tx features
    known_illicit: list[str]      # ground truth labels
    known_licit: list[str]
```

### Output: QUBO Matrix
```python
@dataclass
class QUBOResult:
    qubo_matrix: np.ndarray       # Q matrix (N×N)
    variable_mapping: dict[int, str]  # index → wallet_address
    estimated_energy: float
    backend_used: str             # "qudora" | "quandela" | "classical"
```

### Optimization Result
```python
@dataclass
class OptimizationResult:
    flagged_wallets: list[str]    # High-risk wallets
    risk_scores: dict[str, float] # wallet → score (0.0–1.0)
    false_positive_rate: float
    f_beta_score: float
    precision: float
    recall: float
    runtime_seconds: float
```

## Testing Strategy
- **Unit**: `test_graph_to_qubo.py` — validate matrix shape, symmetry, energy bounds
- **Integration**: Elliptic dataset (203,769 transactions, 2% illicit)
- **Benchmark**: So sánh FPR vs. GraphSAGE / GAT / XGBoost
- **Regression**: FPR không được tăng sau mỗi PR

## Boundaries
- **Always do**: Log backend choice + runtime, validate QUBO matrix (symmetric, correct size), fallback to classical nếu quantum backend timeout > 30s
- **Ask first**: Thay đổi β parameter, switch quantum backend provider, modify QUBO cost function structure
- **Never do**: Run QUBO trên graph > 10,000 nodes (memory overflow risk), disable fallback, skip validation

## Success Criteria
- [ ] `map_graph_to_qubo(nx.Graph(1000 nodes))` hoàn thành trong < 5s
- [ ] QUBO matrix output: square, symmetric, dtype=float64
- [ ] Qamelion Emulator kết nối thành công với `noise_model="nisq_standard"`
- [ ] FPR trên Elliptic test set < 10%
- [ ] F-β (β=0.5) trên Elliptic test set > 0.90
- [ ] Benchmark report: QUBO outperforms GraphSAGE, GAT, XGBoost trên FPR metric

## Open Questions
- Qubo matrix size limit an toàn cho Qamelion? (ước tính 500×500?)
- Có dùng QAOA hay Simulated Annealing làm solver mặc định?
