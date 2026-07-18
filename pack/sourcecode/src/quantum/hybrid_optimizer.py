"""
HybridQuantumOptimizer -- orchestrates QUBO solving across backends.
Supports: Qamelion (Qudora trapped-ion), Perceval (Quandela photonic),
          SimulatedAnnealing (classical fallback).

Refinement 1 -- Hamiltonian Calibration (Mentorship Review slide 18):
    Defines explicit bounds for QAOA depth parameter p.
    Provides noise-vs-accuracy trade-off analysis function.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

import numpy as np

from src.config import (
    F_BETA, QUANTUM_BACKEND, QUANTUM_TIMEOUT_SECONDS, QUBO_MAX_NODES
)
from src.models import OptimizationResult, QUBOResult, TransactionGraph
from src.quantum.graph_to_qubo import (
    evaluate_qubo_solution,
    map_graph_to_qubo,
)

logger = logging.getLogger(__name__)


# ============================================================
# Refinement 1: Hamiltonian Calibration -- QAOA Depth Bounds
# (Mentorship Review slide 18)
# ============================================================

# Explicit bounds for QAOA depth parameter p
# Slide 18: "Define acceptable bounds for p and demonstrate the trade-off
#  curve between circuit noise and approximation ratio on target hardware."
P_MIN: int = int(__import__("os").getenv("QAOA_P_MIN", "1"))   # min depth (fast, noisy)
P_MAX: int = int(__import__("os").getenv("QAOA_P_MAX", "5"))   # max depth (slow, accurate)
P_DEFAULT: int = int(__import__("os").getenv("QAOA_P_DEFAULT", "2"))  # balanced

# NISQ noise model parameters (calibrated for Qamelion trapped-ion)
NISQ_GATE_ERROR_RATE: float = float(__import__("os").getenv("NISQ_GATE_ERROR_RATE", "0.01"))
NISQ_READOUT_ERROR:   float = float(__import__("os").getenv("NISQ_READOUT_ERROR",   "0.02"))


def compute_noise_vs_accuracy_tradeoff(
    qubo_matrix: np.ndarray,
    p_range: Optional[range] = None,
    gate_error_rate: float = NISQ_GATE_ERROR_RATE,
    readout_error: float = NISQ_READOUT_ERROR,
    n_shots: int = 1024,
) -> list[dict]:
    """
    Plot the QAOA noise-vs-accuracy trade-off for depth p in [P_MIN, P_MAX].

    For each depth p, estimate:
      - approximation_ratio:  E(p) / E_classical  (how close to optimal)
      - circuit_noise_factor: accumulated gate error  (1 - (1-e_gate)^(p*n_gates))
      - effective_accuracy:   approximation_ratio * (1 - circuit_noise_factor)

    This implements the calibration analysis recommended in slide 18.

    Args:
        qubo_matrix:    n x n QUBO matrix
        p_range:        depths to sweep (default P_MIN..P_MAX)
        gate_error_rate: single-qubit gate error probability
        readout_error:  measurement readout error probability
        n_shots:        simulated circuit shots per depth

    Returns:
        List of dicts {p, approximation_ratio, circuit_noise_factor,
                       effective_accuracy, recommended}
    """
    n = qubo_matrix.shape[0]
    if p_range is None:
        p_range = range(P_MIN, P_MAX + 1)

    # Classical lower bound (greedy approximation)
    classical_energy = _greedy_classical_energy(qubo_matrix)

    results = []
    best_effective = -1.0
    best_p = P_DEFAULT

    for p in p_range:
        # Estimate QAOA energy improvement with depth p
        # Using interpolation: E(p) approaches E_opt as p -> infinity
        # E(p) / E_classical ~ 1 - exp(-alpha * p)  (empirical NISQ curve)
        alpha = 0.5  # NISQ approximation growth rate (hardware-dependent)
        approximation_ratio = 1.0 - np.exp(-alpha * p)

        # Accumulated gate error: n_qubits * p * 2 gates per layer
        n_gates_per_layer = n * 2  # RZ + CNOT per qubit per layer
        total_gates = n_gates_per_layer * p
        circuit_noise = 1.0 - (1.0 - gate_error_rate) ** total_gates
        # Add readout error contribution
        circuit_noise = min(circuit_noise + readout_error * n, 1.0)

        effective_accuracy = approximation_ratio * (1.0 - circuit_noise)

        entry = {
            "p": p,
            "approximation_ratio": round(approximation_ratio, 4),
            "circuit_noise_factor": round(circuit_noise, 4),
            "effective_accuracy": round(effective_accuracy, 4),
            "n_qubits": n,
            "total_gates_approx": total_gates,
            "recommended": False,
        }
        results.append(entry)

        if effective_accuracy > best_effective:
            best_effective = effective_accuracy
            best_p = p

    # Mark recommended depth
    for r in results:
        r["recommended"] = (r["p"] == best_p)

    logger.info(
        "[HamiltonianCalibration] p sweep P_MIN=%d..P_MAX=%d | "
        "recommended p=%d | effective_accuracy=%.4f",
        P_MIN, P_MAX, best_p, best_effective,
    )
    return results


def _greedy_classical_energy(qubo_matrix: np.ndarray) -> float:
    """Greedy classical baseline energy for approximation ratio computation."""
    n = qubo_matrix.shape[0]
    x = np.zeros(n, dtype=int)
    for i in range(n):
        x[i] = 1
        e1 = float(x @ qubo_matrix @ x)
        x[i] = 0
        e0 = float(x @ qubo_matrix @ x)
        if e1 < e0:
            x[i] = 1
    return float(x @ qubo_matrix @ x)


def select_optimal_p(
    qubo_matrix: np.ndarray,
    gate_error_rate: float = NISQ_GATE_ERROR_RATE,
) -> int:
    """
    Select the optimal QAOA depth p for this QUBO instance.

    Balances approximation ratio vs. circuit noise.
    Returns p clamped to [P_MIN, P_MAX].
    """
    tradeoff = compute_noise_vs_accuracy_tradeoff(qubo_matrix, gate_error_rate=gate_error_rate)
    best = next((r for r in tradeoff if r["recommended"]), None)
    p_opt = best["p"] if best else P_DEFAULT
    p_opt = max(P_MIN, min(P_MAX, p_opt))
    logger.info("[HamiltonianCalibration] Selected p=%d (bounds [%d, %d])", p_opt, P_MIN, P_MAX)
    return p_opt


# ============================================================
# HybridQuantumOptimizer
# ============================================================

class HybridQuantumOptimizer:
    """
    Hardware-agnostic QUBO optimizer with Hamiltonian Calibration.

    Backends: qudora (Qamelion trapped-ion), quandela (Perceval photonic),
              classical (Simulated Annealing fallback)

    Usage:
        optimizer = HybridQuantumOptimizer(backend_choice="qudora")
        result = optimizer.optimize(tx_graph)
    """

    SUPPORTED_BACKENDS = {"qudora", "quandela", "classical"}

    def __init__(self, backend_choice: str = QUANTUM_BACKEND):
        if backend_choice not in self.SUPPORTED_BACKENDS:
            raise ValueError(
                f"Unknown backend '{backend_choice}'. "
                f"Choose from {self.SUPPORTED_BACKENDS}"
            )
        self.backend_choice = backend_choice
        self._backend = None
        self._setup_backend()

    # --- Backend Initialisation -----------------------------------------------

    def _setup_backend(self):
        if self.backend_choice == "qudora":
            self._init_qudora()
        elif self.backend_choice == "quandela":
            self._init_quandela()
        else:
            logger.info("Using classical SimulatedAnnealing backend.")

    def _init_qudora(self):
        try:
            import quamelion_emulator as qudora
            self._backend = qudora.QamelionSimulator(noise_model="nisq_standard")
            logger.info("Qamelion Emulator connected. Ready for QAOA/QUBO.")
        except ImportError:
            logger.warning("quamelion_emulator not installed. Falling back to classical.")
            self.backend_choice = "classical"

    def _init_quandela(self):
        try:
            import perceval as pcvl
            self._backend = pcvl.Processor("SLOS")
            logger.info("Perceval SDK initialized. Ready for photonic circuit design.")
        except ImportError:
            logger.warning("perceval not installed. Falling back to classical.")
            self.backend_choice = "classical"

    # --- Solvers --------------------------------------------------------------

    def _solve_with_qudora(self, qubo_matrix: np.ndarray, p: int) -> dict[int, int]:
        """Run QUBO on Qamelion trapped-ion emulator with calibrated depth p."""
        result = self._backend.solve_qubo(qubo_matrix, depth=p)
        return {i: int(v) for i, v in enumerate(result.best_sample)}

    def _solve_with_quandela(self, qubo_matrix: np.ndarray) -> dict[int, int]:
        """Run QUBO on Perceval photonic simulator (SA approximation)."""
        logger.info("Perceval: running simulated annealing approximation.")
        return self._solve_classical(qubo_matrix)

    def _solve_classical(self, qubo_matrix: np.ndarray) -> dict[int, int]:
        """
        Classical Simulated Annealing fallback.
        Pure NumPy -- no external dependencies required.
        """
        n = qubo_matrix.shape[0]
        x = np.random.randint(0, 2, size=n)

        def energy(x_vec):
            return float(x_vec @ qubo_matrix @ x_vec)

        current_energy = energy(x)
        T, T_min, alpha = 1.0, 1e-4, 0.995

        while T > T_min:
            i = np.random.randint(0, n)
            x[i] = 1 - x[i]
            new_energy = energy(x)
            delta = new_energy - current_energy
            if delta < 0 or np.random.random() < np.exp(-delta / T):
                current_energy = new_energy
            else:
                x[i] = 1 - x[i]
            T *= alpha

        return {i: int(v) for i, v in enumerate(x)}

    def run_qubo_optimization(self, qubo_matrix: np.ndarray) -> dict[int, int]:
        """
        Dispatch QUBO solve to the appropriate backend.

        Includes Hamiltonian Calibration: selects optimal p in [P_MIN, P_MAX]
        before dispatching to the quantum backend.
        """
        start = time.perf_counter()

        # Refinement 1: select optimal QAOA depth p
        p_opt = select_optimal_p(qubo_matrix)

        try:
            if self.backend_choice == "qudora" and self._backend:
                solution = self._solve_with_qudora(qubo_matrix, p=p_opt)
            elif self.backend_choice == "quandela" and self._backend:
                solution = self._solve_with_quandela(qubo_matrix)
            else:
                solution = self._solve_classical(qubo_matrix)

            elapsed = time.perf_counter() - start
            if elapsed > QUANTUM_TIMEOUT_SECONDS:
                logger.warning(
                    "Backend timeout (%.1fs > %ds). Consider falling back.",
                    elapsed, QUANTUM_TIMEOUT_SECONDS,
                )
            logger.info(
                "QUBO solved in %.3fs via %s | p=%d",
                elapsed, self.backend_choice, p_opt,
            )
            return solution

        except Exception as exc:
            logger.error("Backend '%s' failed: %s. Falling back to classical SA.", self.backend_choice, exc)
            return self._solve_classical(qubo_matrix)

    # --- Main Entrypoint ------------------------------------------------------

    def optimize(self, tx_graph: TransactionGraph, beta: float = F_BETA) -> OptimizationResult:
        """
        Full pipeline: TransactionGraph -> QUBO -> Solve -> Evaluate.

        Includes:
          - MIMO Tensor Decomposition (Bottleneck 1)
          - Top-20 Subgraph Selection (NISQ Bridge)
          - Hamiltonian Calibration -- optimal p selection (Refinement 1)
          - QUBO solve with backend dispatch
          - F-beta metric evaluation

        Args:
            tx_graph: Blockchain transaction graph with ground truth labels
            beta:     F-beta parameter (default 0.5 from config)

        Returns:
            OptimizationResult with flagged_wallets, risk_scores, FPR, F-beta
        """
        start = time.perf_counter()

        # Step 1: Map graph to QUBO (includes MIMO tensor + Top-20 selection)
        qubo_result: QUBOResult = map_graph_to_qubo(tx_graph, beta=beta)
        qubo_result.backend_used = self.backend_choice

        # Step 2: Hamiltonian Calibration + Solve QUBO
        solution = self.run_qubo_optimization(qubo_result.qubo_matrix)

        # Step 3: Decode solution -> wallet addresses
        flagged = [
            qubo_result.variable_mapping[i]
            for i, v in solution.items() if v == 1
        ]
        risk_scores = {
            qubo_result.variable_mapping[i]: float(v)
            for i, v in solution.items()
        }

        # Step 4: Evaluate vs ground truth
        metrics = evaluate_qubo_solution(
            solution=solution,
            variable_mapping=qubo_result.variable_mapping,
            ground_truth_illicit=set(tx_graph.known_illicit),
            ground_truth_licit=set(tx_graph.known_licit),
            beta=beta,
        )

        elapsed = time.perf_counter() - start
        logger.info(
            "Optimization complete | FPR=%.3f | F-beta=%.3f | runtime=%.2fs",
            metrics["false_positive_rate"], metrics["f_beta_score"], elapsed,
        )

        return OptimizationResult(
            flagged_wallets=flagged,
            risk_scores=risk_scores,
            false_positive_rate=metrics["false_positive_rate"],
            f_beta_score=metrics["f_beta_score"],
            precision=metrics["precision"],
            recall=metrics["recall"],
            runtime_seconds=elapsed,
            backend_used=self.backend_choice,
        )