"""
Refinement 2 -- Weight Sensitivity Analysis
============================================
Mentorship Review slide 18 -- Refinement #2:
"Conduct a brief sensitivity / ablation analysis:
  - How does verdict distribution shift under +/-20% weight perturbation?
  - What is the false-positive rate surface?"

Outputs:
  1. Verdict distribution (FREEZE/MONITOR/CLEAR) under omega perturbation
  2. FPR surface plot across (omega_r, omega_q) grid
  3. Threshold sensitivity: tau_H and tau_M sweep
  4. JSON report saved to reports/

Usage:
    python weight_sensitivity_analysis.py [--n-samples 500] [--out-dir reports/]
"""
from __future__ import annotations

import json
import logging
import sys
from itertools import product
from pathlib import Path

import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")


# Base calibration weights (Slide 13 standard formula)
OMEGA_BASE = {
    "omega_r": 0.30,   # classical risk r~
    "omega_q": 0.25,   # quantum evidence zeta_Q
    "omega_E": 0.20,   # external sanctions E
    "omega_S": 0.15,   # scam/structuring S
    "omega_C": 0.07,   # counterparty C
    "omega_O": 0.03,   # obfuscation O
}

TAU_H_BASE = 0.75  # FREEZE threshold
TAU_M_BASE = 0.45  # MONITOR threshold
PERTURBATION = 0.20  # +/-20% weight perturbation (slide 18)


def _normalise_weights(w: dict[str, float]) -> dict[str, float]:
    """Normalise weights so they sum to 1.0."""
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}


def _compute_R(scores: dict, weights: dict) -> float:
    """
    R_a = clip(omega_r*r~ + omega_q*zeta_Q + omega_E*E + omega_S*S + omega_C*C + omega_O*O, 0, 1)
    """
    raw = (
        weights["omega_r"] * scores["r_tilde"]
        + weights["omega_q"] * scores["zeta_q"]
        + weights["omega_E"] * scores["E"]
        + weights["omega_S"] * scores["S"]
        + weights["omega_C"] * scores["C"]
        + weights["omega_O"] * scores["O"]
    )
    return float(np.clip(raw, 0.0, 1.0))


def _verdict(R: float, tau_H: float, tau_M: float) -> str:
    if R >= tau_H:
        return "FREEZE"
    elif R >= tau_M:
        return "MONITOR"
    return "CLEAR"


def _simulate_population(n: int = 500, seed: int = 42) -> list[dict]:
    """
    Simulate a diverse wallet population for sensitivity testing.
    Mix: 20% high-risk (illicit), 30% medium, 50% low-risk (licit).
    """
    rng = np.random.default_rng(seed)
    samples = []

    for _ in range(n):
        risk_class = rng.choice(["high", "med", "low"], p=[0.20, 0.30, 0.50])

        if risk_class == "high":
            r_t   = rng.uniform(0.65, 1.0)
            zeta  = rng.uniform(0.70, 1.0)
            E     = rng.choice([0.0, 1.0], p=[0.30, 0.70])
            S     = rng.uniform(0.50, 1.0)
            C     = rng.choice([0.0, 1.0], p=[0.40, 0.60])
            O     = rng.choice([0.0, 1.0], p=[0.50, 0.50])
            true_illicit = True
        elif risk_class == "med":
            r_t   = rng.uniform(0.35, 0.70)
            zeta  = rng.uniform(0.30, 0.70)
            E     = rng.choice([0.0, 1.0], p=[0.80, 0.20])
            S     = rng.uniform(0.20, 0.60)
            C     = rng.choice([0.0, 1.0], p=[0.70, 0.30])
            O     = 0.0
            true_illicit = rng.random() < 0.40
        else:
            r_t   = rng.uniform(0.0, 0.40)
            zeta  = rng.uniform(0.0, 0.35)
            E     = 0.0
            S     = rng.uniform(0.0, 0.25)
            C     = 0.0
            O     = 0.0
            true_illicit = False

        samples.append({
            "r_tilde":      float(r_t),
            "zeta_q":       float(zeta),
            "E":            float(E),
            "S":            float(S),
            "C":            float(C),
            "O":            float(O),
            "true_illicit": true_illicit,
        })

    return samples


def _evaluate_weights(
    population: list[dict],
    weights: dict[str, float],
    tau_H: float = TAU_H_BASE,
    tau_M: float = TAU_M_BASE,
) -> dict:
    """Evaluate weights on population. Returns verdict distribution + FPR."""
    verdicts = {"FREEZE": 0, "MONITOR": 0, "CLEAR": 0}
    tp = fp = fn = tn = 0

    for s in population:
        R = _compute_R(s, weights)
        v = _verdict(R, tau_H, tau_M)
        verdicts[v] += 1
        flagged = (v == "FREEZE")
        if flagged and s["true_illicit"]:     tp += 1
        elif flagged and not s["true_illicit"]: fp += 1
        elif not flagged and s["true_illicit"]: fn += 1
        else:                                   tn += 1

    n = len(population)
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f_beta    = ((1 + 0.5**2) * precision * recall / ((0.5**2 * precision) + recall)
                 if (precision + recall) > 0 else 0.0)

    return {
        "freeze_pct":   round(verdicts["FREEZE"] / n * 100, 2),
        "monitor_pct":  round(verdicts["MONITOR"] / n * 100, 2),
        "clear_pct":    round(verdicts["CLEAR"] / n * 100, 2),
        "fpr":          round(fpr, 4),
        "precision":    round(precision, 4),
        "recall":       round(recall, 4),
        "f_beta":       round(f_beta, 4),
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
    }


def run_weight_perturbation_analysis(population: list[dict]) -> list[dict]:
    """
    For each omega_k, perturb by +/-20% (renormalise), evaluate impact.
    Slide 18: "How does verdict distribution shift under +-20% weight perturbation?"
    """
    results = []

    # Baseline
    base_norm = _normalise_weights(OMEGA_BASE)
    baseline  = _evaluate_weights(population, base_norm)
    results.append({"perturbation": "baseline", "weights": base_norm, **baseline})

    for key in OMEGA_BASE:
        for delta_pct, label in [(PERTURBATION, f"+{int(PERTURBATION*100)}%"),
                                  (-PERTURBATION, f"-{int(PERTURBATION*100)}%")]:
            perturbed = dict(OMEGA_BASE)
            perturbed[key] = max(0.001, perturbed[key] * (1 + delta_pct))
            perturbed_norm = _normalise_weights(perturbed)
            metrics = _evaluate_weights(population, perturbed_norm)

            results.append({
                "perturbation":  f"{key} {label}",
                "key":           key,
                "delta_pct":     label,
                "perturbed_val": round(perturbed_norm[key], 4),
                "base_val":      round(base_norm[key], 4),
                "weights":       {k: round(v, 4) for k, v in perturbed_norm.items()},
                **metrics,
                "fpr_delta":    round(metrics["fpr"] - baseline["fpr"], 4),
                "freeze_delta": round(metrics["freeze_pct"] - baseline["freeze_pct"], 2),
            })

    return results


def run_fpr_surface(population: list[dict], grid_size: int = 10) -> dict:
    """
    Compute FPR surface over (omega_r, omega_q) 2D grid.
    All other weights kept proportional to their base values.
    Slide 18: "What is the false-positive rate surface?"
    """
    logger.info("[Sensitivity] Computing FPR surface (%dx%d grid)...", grid_size, grid_size)

    omega_r_range = np.linspace(0.05, 0.60, grid_size)
    omega_q_range = np.linspace(0.05, 0.60, grid_size)
    fpr_grid      = np.zeros((grid_size, grid_size))
    fbeta_grid    = np.zeros((grid_size, grid_size))

    # Remaining weights (E, S, C, O) — scale proportionally
    remaining_base = {
        "omega_E": OMEGA_BASE["omega_E"],
        "omega_S": OMEGA_BASE["omega_S"],
        "omega_C": OMEGA_BASE["omega_C"],
        "omega_O": OMEGA_BASE["omega_O"],
    }
    remaining_sum = sum(remaining_base.values())

    for i, w_r in enumerate(omega_r_range):
        for j, w_q in enumerate(omega_q_range):
            remaining_budget = max(0.001, 1.0 - w_r - w_q)
            scale = remaining_budget / remaining_sum
            weights = {
                "omega_r": w_r,
                "omega_q": w_q,
                "omega_E": remaining_base["omega_E"] * scale,
                "omega_S": remaining_base["omega_S"] * scale,
                "omega_C": remaining_base["omega_C"] * scale,
                "omega_O": remaining_base["omega_O"] * scale,
            }
            metrics = _evaluate_weights(population, weights)
            fpr_grid[i, j]   = metrics["fpr"]
            fbeta_grid[i, j] = metrics["f_beta"]

    return {
        "omega_r_axis": omega_r_range.tolist(),
        "omega_q_axis": omega_q_range.tolist(),
        "fpr_grid":     fpr_grid.tolist(),
        "fbeta_grid":   fbeta_grid.tolist(),
    }


def run_threshold_sensitivity(population: list[dict]) -> list[dict]:
    """
    Sweep tau_H and tau_M to show sensitivity of FPR / FREEZE rate.
    """
    results = []
    for tau_H in np.linspace(0.55, 0.95, 9):
        for tau_M in np.linspace(0.25, 0.65, 9):
            if tau_M >= tau_H:
                continue
            metrics = _evaluate_weights(population, _normalise_weights(OMEGA_BASE),
                                        tau_H=float(tau_H), tau_M=float(tau_M))
            results.append({
                "tau_H": round(float(tau_H), 2),
                "tau_M": round(float(tau_M), 2),
                **metrics,
            })
    return results


def plot_results(perturbation_results: list[dict], surface_data: dict, out_dir: Path):
    """Generate Matplotlib plots for the sensitivity analysis."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.cm as cm
    except ImportError:
        logger.warning("[Sensitivity] matplotlib not installed — skipping plots. pip install matplotlib")
        return

    plt.style.use("dark_background")
    fig_dir = out_dir
    fig_dir.mkdir(parents=True, exist_ok=True)

    # ── Plot 1: FPR delta per weight perturbation ──────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Refinement 2 — Weight Sensitivity Analysis\n"
                 "Compliance Score R_a = clip(omega_r*r~ + omega_q*zeta_Q + omega_E*E + omega_S*S + omega_C*C + omega_O*O, 0,1)",
                 fontsize=10, color="#e0e0e0")

    non_baseline = [r for r in perturbation_results if r["perturbation"] != "baseline"]
    labels   = [f"{r['key']} {r['delta_pct']}" for r in non_baseline]
    fpr_deltas  = [r["fpr_delta"]   for r in non_baseline]
    frz_deltas  = [r["freeze_delta"] for r in non_baseline]

    bar_colours_fpr = ["#e53935" if d > 0 else "#43a047" for d in fpr_deltas]
    bar_colours_frz = ["#e53935" if d > 0 else "#43a047" for d in frz_deltas]

    axes[0].barh(labels, fpr_deltas, color=bar_colours_fpr, alpha=0.8)
    axes[0].axvline(0, color="#ffffff", linewidth=0.8, linestyle="--")
    axes[0].set_xlabel("FPR Change (vs. baseline)", color="#e0e0e0")
    axes[0].set_title("FPR Sensitivity (+/-20% weight perturbation)", color="#e0e0e0")
    axes[0].tick_params(colors="#e0e0e0", axis="both")

    axes[1].barh(labels, frz_deltas, color=bar_colours_frz, alpha=0.8)
    axes[1].axvline(0, color="#ffffff", linewidth=0.8, linestyle="--")
    axes[1].set_xlabel("FREEZE Rate Change % (vs. baseline)", color="#e0e0e0")
    axes[1].set_title("FREEZE Rate Sensitivity", color="#e0e0e0")
    axes[1].tick_params(colors="#e0e0e0", axis="both")

    plt.tight_layout()
    out1 = fig_dir / "weight_sensitivity_bar.png"
    fig.savefig(str(out1), dpi=160, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close(fig)
    logger.info("[Sensitivity] Bar chart -> %s", out1)

    # ── Plot 2: FPR Surface Heatmap ────────────────────────────────────────────
    fpr_grid = np.array(surface_data["fpr_grid"])
    omega_r_ax = np.array(surface_data["omega_r_axis"])
    omega_q_ax = np.array(surface_data["omega_q_axis"])

    fig2, ax2 = plt.subplots(figsize=(8, 7))
    im = ax2.imshow(fpr_grid, aspect="auto", origin="lower",
                    extent=[omega_q_ax[0], omega_q_ax[-1], omega_r_ax[0], omega_r_ax[-1]],
                    cmap="RdYlGn_r", vmin=0, vmax=1)
    fig2.colorbar(im, ax=ax2, label="False-Positive Rate")
    ax2.set_xlabel("omega_q (quantum evidence weight)", color="#e0e0e0")
    ax2.set_ylabel("omega_r (classical risk weight)", color="#e0e0e0")
    ax2.set_title("FPR Surface over (omega_r, omega_q) Grid\n"
                  "Dark green = low FPR, Dark red = high FPR", color="#e0e0e0")
    ax2.tick_params(colors="#e0e0e0", axis="both")

    # Mark baseline point
    ax2.plot(0.25, 0.30, "w*", markersize=14, label="Baseline (omega_r=0.30, omega_q=0.25)")
    ax2.legend(fontsize=8, labelcolor="#e0e0e0", facecolor="#1a1a2e")

    plt.tight_layout()
    out2 = fig_dir / "fpr_surface_heatmap.png"
    fig2.savefig(str(out2), dpi=160, bbox_inches="tight", facecolor="#1a1a2e")
    plt.close(fig2)
    logger.info("[Sensitivity] FPR surface heatmap -> %s", out2)

    print(f"   Sensitivity bar chart: {out1.resolve()}")
    print(f"   FPR surface heatmap:   {out2.resolve()}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="[Refinement 2] Weight Sensitivity Analysis")
    parser.add_argument("--n-samples", type=int, default=500)
    parser.add_argument("--out-dir",   default="reports/sensitivity/")
    parser.add_argument("--no-plots",  action="store_true")
    parser.add_argument("--grid-size", type=int, default=12)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("[Sensitivity] Simulating population (n=%d)...", args.n_samples)
    population = _simulate_population(n=args.n_samples)

    logger.info("[Sensitivity] Running weight perturbation analysis (+/-20%)...")
    perturbation_results = run_weight_perturbation_analysis(population)

    logger.info("[Sensitivity] Computing FPR surface (%dx%d grid)...", args.grid_size, args.grid_size)
    surface_data = run_fpr_surface(population, grid_size=args.grid_size)

    logger.info("[Sensitivity] Running threshold (tau_H, tau_M) sensitivity sweep...")
    threshold_results = run_threshold_sensitivity(population)

    # Print summary
    baseline = next(r for r in perturbation_results if r["perturbation"] == "baseline")
    print(f"\n{'='*60}")
    print(f"BASELINE (omega_r=0.30, omega_q=0.25, omega_E=0.20, ...)")
    print(f"  FREEZE: {baseline['freeze_pct']:.1f}%  |  MONITOR: {baseline['monitor_pct']:.1f}%  |  CLEAR: {baseline['clear_pct']:.1f}%")
    print(f"  FPR={baseline['fpr']:.4f}  F-beta={baseline['f_beta']:.4f}  Precision={baseline['precision']:.4f}")
    print(f"\nMost impactful perturbations:")
    sorted_p = sorted([r for r in perturbation_results if r["perturbation"] != "baseline"],
                      key=lambda x: abs(x["fpr_delta"]), reverse=True)
    for r in sorted_p[:6]:
        print(f"  {r['perturbation']:<25} FPR delta: {r['fpr_delta']:+.4f}  "
              f"FREEZE delta: {r['freeze_delta']:+.1f}%")

    # Best tau combination from threshold sweep
    best_tau = min(threshold_results, key=lambda x: x["fpr"])
    print(f"\nOptimal thresholds (min FPR):")
    print(f"  tau_H={best_tau['tau_H']}  tau_M={best_tau['tau_M']}  "
          f"FPR={best_tau['fpr']:.4f}  F-beta={best_tau['f_beta']:.4f}")
    print(f"{'='*60}")

    # Save JSON report
    report = {
        "analysis": "Refinement 2 — Weight Sensitivity Analysis",
        "slide_ref": "Mentorship Review Slide 18",
        "n_samples": args.n_samples,
        "perturbation_pct": PERTURBATION,
        "baseline": baseline,
        "base_weights": OMEGA_BASE,
        "perturbation_results": perturbation_results,
        "threshold_sensitivity_best": best_tau,
        "fpr_surface": {
            "omega_r_axis": surface_data["omega_r_axis"],
            "omega_q_axis": surface_data["omega_q_axis"],
            "fpr_grid_shape": [len(surface_data["fpr_grid"]), len(surface_data["fpr_grid"][0])],
        },
    }
    report_path = out_dir / "weight_sensitivity_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info("[Sensitivity] Report saved -> %s", report_path)
    print(f"\n   Full report: {report_path.resolve()}")

    if not args.no_plots:
        plot_results(perturbation_results, surface_data, out_dir)


if __name__ == "__main__":
    main()
