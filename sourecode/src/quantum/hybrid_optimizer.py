"""
HybridQuantumOptimizer — orchestrates QUBO solving across backends.
Supports: Qamelion (Qudora trapped-ion), Perceval (Quandela photonic),
          SimulatedAnnealing (classical fallback).
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


class HybridQuantumOptimizer:
    """
    Hardware-agnostic QUBO optimizer.

    Usage:
        optimizer = HybridQuantumOptimizer(backend_choice="qudora")
        result = optimizer.optimize(tx_graph)
    """

    SUPPORTED_BACKENDS = {"qudora", "quandela", "classical"}

    def __init__(self, backend_choice: str = QUANTUM_BACKEND):
        if backend_choice not in self.SUPPORTED_BACKENDS:
            raise ValueError(f"Unknown backend '{backend_choice}'. Choose from {self.SUPPORTED_BACKENDS}")
        self.backend_choice = backend_choice
        self._backend = None
        self._setup_backend()

    # ─── Backend Initialisation ───────────────────────────────────────────────

    def _setup_backend(self) -> None:
        if self.backend_choice == "qudora":
            self._init_qudora()
        elif self.backend_choice == "quandela":
            self._init_quandela()
        else:
            logger.info("Using classical SimulatedAnnealing backend.")

    def _init_qudora(self) -> None:
        try:
            import quamelion_emulator as qudora
            self._backend = qudora.QamelionSimulator(noise_model="nisq_standard")
            logger.info("✅ Qamelion Emulator connected. Ready for QAOA/QUBO.")
        except ImportError:
            logger.warning("⚠️  quamelion_emulator not installed. Falling back to classical.")
            self.backend_choice = "classical"

    def _init_quandela(self) -> None:
        try:
            import perceval as pcvl
            self._backend = pcvl.Processor("SLOS")
            logger.info("✅ Perceval SDK initialized. Ready for photonic circuit design.")
        except ImportError:
            logger.warning("⚠️  perceval not installed. Falling back to classical.")
            self.backend_choice = "classical"

    # ─── Solvers ─────────────────────────────────────────────────────────────

    def _solve_with_qudora(self, qubo_matrix: np.ndarray) -> dict[int, int]:
        """Run QUBO on Qamelion trapped-ion emulator."""
        result = self._backend.solve_qubo(qubo_matrix)
        return {i: int(v) for i, v in enumerate(result.best_sample)}

    def _solve_with_quandela(self, qubo_matrix: np.ndarray) -> dict[int, int]:
        """Run QUBO on Perceval photonic simulator."""
        # Perceval requires unitary decomposition — approximate via SA for now
        logger.info("Perceval: running simulated annealing approximation.")
        return self._solve_classical(qubo_matrix)

    def _solve_classical(self, qubo_matrix: np.ndarray) -> dict[int, int]:
        """
        Classical Simulated Annealing fallback.
        Pure NumPy — no external dependencies required.
        """
        n = qubo_matrix.shape[0]
        x = np.random.randint(0, 2, size=n)

        def energy(x_vec: np.ndarray) -> float:
            return float(x_vec @ qubo_matrix @ x_vec)

        current_energy = energy(x)
        T = 1.0
        T_min = 1e-4
        alpha = 0.995

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
        Dispatch QUBO solve to appropriate backend with timeout + fallback.

        Returns:
            dict mapping variable_index → 0|1 (binary solution)
        """
        start = time.perf_counter()
        try:
            if self.backend_choice == "qudora" and self._backend:
                solution = self._solve_with_qudora(qubo_matrix)
            elif self.backend_choice == "quandela" and self._backend:
                solution = self._solve_with_quandela(qubo_matrix)
            else:
                solution = self._solve_classical(qubo_matrix)

            elapsed = time.perf_counter() - start
            if elapsed > QUANTUM_TIMEOUT_SECONDS:
                logger.warning(f"Backend timeout ({elapsed:.1f}s > {QUANTUM_TIMEOUT_SECONDS}s). "
                               "Consider falling back to classical.")
            logger.info(f"QUBO solved in {elapsed:.3f}s via {self.backend_choice}")
            return solution

        except Exception as exc:
            logger.error(f"Backend '{self.backend_choice}' failed: {exc}. Falling back to classical SA.")
            return self._solve_classical(qubo_matrix)

    # ─── Main Entrypoint ─────────────────────────────────────────────────────

    def optimize(
        self,
        tx_graph: TransactionGraph,
        beta: float = F_BETA,
    ) -> OptimizationResult:
        """
        Full pipeline: TransactionGraph → QUBO → Solve → Evaluate.

        Args:
            tx_graph: Blockchain transaction graph with ground truth labels
            beta:     F-β parameter (default 0.5 from config)

        Returns:
            OptimizationResult with flagged_wallets, risk_scores, FPR, F-β
        """
        start = time.perf_counter()

        # Step 1: Map graph to QUBO
        qubo_result: QUBOResult = map_graph_to_qubo(tx_graph, beta=beta)
        qubo_result.backend_used = self.backend_choice

        # Step 2: Solve QUBO
        solution = self.run_qubo_optimization(qubo_result.qubo_matrix)

        # Step 3: Decode solution → wallet addresses
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
            f"Optimization complete | FPR={metrics['false_positive_rate']:.3f} "
            f"| F-β={metrics['f_beta_score']:.3f} | runtime={elapsed:.2f}s"
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
