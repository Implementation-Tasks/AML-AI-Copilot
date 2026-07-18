"""
Virtual + Mixed Data Setup
==========================
Per Professor Han's recommendation (Q&A.md -- item 1):
"The best and more feasible approach for the project is to use
virtual data and mixed data."

This module:
  1. Generates virtual AML transaction data (AMLSim-style synthetic data)
     without requiring IBM AMLSim installation.
  2. Loads the real Elliptic dataset.
  3. Merges both into a combined mixed dataset for training/validation.

Virtual Data Strategy:
  - Simulates structuring (smurfing), layering, mixer usage patterns
  - Uses configurable parameters to control fraud ratio and graph size
  - Compatible with TransactionGraph and existing QUBO pipeline

Usage:
    python amlsim_data_setup.py --mode virtual --n-wallets 200 --fraud-ratio 0.25
    python amlsim_data_setup.py --mode elliptic
    python amlsim_data_setup.py --mode mixed --n-virtual 300
    python amlsim_data_setup.py --info   # Show dataset statistics
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import networkx as nx
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

# Output paths
OUT_DIR = Path("dataset/virtual/")


# ============================================================
# Virtual AML Data Generator (AMLSim-inspired patterns)
# ============================================================

class VirtualAMLGenerator:
    """
    Generates synthetic AML transaction graphs with realistic fraud patterns.

    Patterns modelled (per Mentorship Review threat model, slide 4):
      1. Structuring / Smurfing   -- many sub-threshold micro-transactions
      2. Layering                 -- multi-hop fund movement A->B->C->...
      3. Mixer / Bridge usage     -- obfuscation nodes
      4. Rapid fund movement      -- velocity anomaly
      5. Cross-chain bridge       -- BSC/ETH bridge pattern
    """

    def __init__(
        self,
        n_wallets:   int   = 200,
        fraud_ratio: float = 0.25,
        seed:        int   = 42,
        max_amount:  float = 1_000_000.0,
    ):
        self.n_wallets   = n_wallets
        self.fraud_ratio = fraud_ratio
        self.rng         = np.random.default_rng(seed)
        self.max_amount  = max_amount

    def _wallet_id(self, i: int) -> str:
        return f"0xVIRT{i:06d}"

    def generate(self) -> tuple[nx.DiGraph, list[str], list[str]]:
        """
        Generate a synthetic AML transaction graph.

        Returns:
            (graph, illicit_wallets, licit_wallets)
        """
        n_illicit = int(self.n_wallets * self.fraud_ratio)
        n_licit   = self.n_wallets - n_illicit

        G = nx.DiGraph()
        illicit_wallets: list[str] = []
        licit_wallets:   list[str] = []

        # Create wallets
        for i in range(self.n_wallets):
            wid     = self._wallet_id(i)
            is_ill  = i < n_illicit
            G.add_node(wid,
                       is_illicit=is_ill,
                       is_mixer=False,
                       is_bridge=False,
                       tx_velocity=0.0)
            if is_ill:
                illicit_wallets.append(wid)
            else:
                licit_wallets.append(wid)

        # Pattern 1: Smurfing clusters
        n_smurf_clusters = max(1, n_illicit // 5)
        for c in range(n_smurf_clusters):
            source = illicit_wallets[c % len(illicit_wallets)]
            target = self.rng.choice(illicit_wallets)
            n_micro = self.rng.integers(4, 12)
            for m in range(n_micro):
                amount = self.rng.uniform(800, 9_999)  # sub-$10k threshold
                ts     = float(self.rng.uniform(0, 86_400))
                G.add_edge(source, target,
                           amount_usd=amount, timestamp=ts,
                           pattern="smurfing")

        # Pattern 2: Layering chains (multi-hop)
        n_layering = max(1, n_illicit // 3)
        for l in range(n_layering):
            chain_len = self.rng.integers(3, 8)
            src = self.rng.choice(illicit_wallets)
            amt = self.rng.uniform(10_000, self.max_amount * 0.5)
            prev = src
            for hop in range(int(chain_len)):
                next_w = self.rng.choice(illicit_wallets)
                if next_w == prev:
                    continue
                amt *= self.rng.uniform(0.85, 0.99)  # fee haircut
                G.add_edge(prev, next_w,
                           amount_usd=amt,
                           timestamp=float(self.rng.uniform(0, 604_800)),
                           pattern="layering", hop=hop)
                prev = next_w

        # Pattern 3: Mixer nodes
        n_mixers = max(1, n_illicit // 8)
        mixer_wallets = []
        for m in range(n_mixers):
            mid = f"0xMIX{m:04d}"
            G.add_node(mid, is_illicit=True, is_mixer=True, is_bridge=False, tx_velocity=0.9)
            mixer_wallets.append(mid)
            illicit_wallets.append(mid)
            # Connect illicit wallets -> mixer -> different illicit wallets
            for _ in range(self.rng.integers(3, 8)):
                src = self.rng.choice(illicit_wallets[:-1])
                dst = self.rng.choice(illicit_wallets[:-1])
                G.add_edge(src, mid,  amount_usd=self.rng.uniform(5_000, 200_000),
                           timestamp=self.rng.uniform(0, 86_400), pattern="mixer_in")
                G.add_edge(mid, dst,  amount_usd=self.rng.uniform(5_000, 200_000),
                           timestamp=self.rng.uniform(0, 86_400), pattern="mixer_out")

        # Pattern 4: Rapid velocity (many txs in short window)
        n_velocity = max(1, n_illicit // 5)
        for v in range(n_velocity):
            src = self.rng.choice(illicit_wallets)
            G.nodes[src]["tx_velocity"] = float(self.rng.uniform(0.7, 1.0))
            for _ in range(self.rng.integers(10, 30)):
                dst = self.rng.choice(licit_wallets)
                G.add_edge(src, dst,
                           amount_usd=self.rng.uniform(100, 5_000),
                           timestamp=self.rng.uniform(0, 3_600),  # 1 hour window
                           pattern="rapid_velocity")

        # Pattern 5: Normal licit transactions (background)
        n_licit_edges = n_licit * 3
        for _ in range(n_licit_edges):
            u = self.rng.choice(licit_wallets)
            v = self.rng.choice(licit_wallets)
            if u != v:
                G.add_edge(u, v,
                           amount_usd=self.rng.uniform(50, 50_000),
                           timestamp=self.rng.uniform(0, 2_592_000),
                           pattern="normal")

        logger.info(
            "[VirtualAML] Generated: %d nodes | %d edges | %d illicit | %d licit",
            G.number_of_nodes(), G.number_of_edges(),
            len(illicit_wallets), len(licit_wallets),
        )
        return G, illicit_wallets, licit_wallets

    def to_transaction_graph(self):
        """Convert to TransactionGraph model for pipeline compatibility."""
        from src.models import TransactionGraph
        G, illicit, licit = self.generate()
        seed = self._wallet_id(0) if G.number_of_nodes() > 0 else "0xVIRT000000"
        return TransactionGraph(
            graph=G,
            seed_wallet=seed,
            known_illicit=illicit,
            known_licit=licit,
        )

    def export_csv(self, out_dir: Path):
        """Export graph to CSV files (nodes + edges) for inspection."""
        G, illicit, licit = self.generate()
        out_dir.mkdir(parents=True, exist_ok=True)

        # Nodes CSV
        import csv
        with open(out_dir / "virtual_nodes.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["wallet_id", "is_illicit", "is_mixer", "tx_velocity"])
            for node, data in G.nodes(data=True):
                writer.writerow([node,
                                  int(data.get("is_illicit", False)),
                                  int(data.get("is_mixer", False)),
                                  round(data.get("tx_velocity", 0.0), 3)])

        # Edges CSV
        with open(out_dir / "virtual_edges.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["from_wallet", "to_wallet", "amount_usd", "timestamp", "pattern"])
            for u, v, data in G.edges(data=True):
                writer.writerow([u, v,
                                  round(data.get("amount_usd", 0), 2),
                                  round(data.get("timestamp", 0), 0),
                                  data.get("pattern", "normal")])

        logger.info("[VirtualAML] Exported CSV -> %s", out_dir)
        return G, illicit, licit


# ============================================================
# Elliptic Dataset Loader
# ============================================================

def load_elliptic_dataset():
    """
    Load the Elliptic Bitcoin dataset into a NetworkX graph.
    Dataset path from config.ELLIPTIC_DIR.
    """
    try:
        import pandas as pd
        from src.config import ELLIPTIC_DATASET_PATH, ELLIPTIC_LABELS_PATH, ELLIPTIC_EDGES_PATH
    except ImportError as e:
        logger.error("pandas/config missing: %s", e)
        raise

    if not Path(ELLIPTIC_DATASET_PATH).exists():
        raise FileNotFoundError(
            f"Elliptic dataset not found at {ELLIPTIC_DATASET_PATH}\n"
            "Download from: https://www.kaggle.com/ellipticco/elliptic-data-set"
        )

    logger.info("[Elliptic] Loading features from %s", ELLIPTIC_DATASET_PATH)
    features = pd.read_csv(ELLIPTIC_DATASET_PATH, header=None)
    labels   = pd.read_csv(ELLIPTIC_LABELS_PATH)
    edges    = pd.read_csv(ELLIPTIC_EDGES_PATH)

    label_map = {str(r["txId"]): r["class"] for _, r in labels.iterrows()}

    G = nx.DiGraph()
    illicit, licit = [], []

    # Add nodes with class labels
    for tx_id in features.iloc[:, 0].astype(str):
        lbl = label_map.get(tx_id, "unknown")
        is_ill = (lbl == "1")
        G.add_node(tx_id, is_illicit=is_ill, is_mixer=False, is_bridge=False, tx_velocity=0.0)
        if lbl == "1":
            illicit.append(tx_id)
        elif lbl == "2":
            licit.append(tx_id)

    # Add edges
    for _, row in edges.iterrows():
        u, v = str(row["txId1"]), str(row["txId2"])
        if G.has_node(u) and G.has_node(v):
            G.add_edge(u, v, amount_usd=1000.0, timestamp=0.0, pattern="elliptic")

    logger.info(
        "[Elliptic] Loaded: %d nodes | %d edges | %d illicit | %d licit",
        G.number_of_nodes(), G.number_of_edges(), len(illicit), len(licit),
    )
    return G, illicit, licit


# ============================================================
# Mixed Dataset Combiner
# ============================================================

def build_mixed_dataset(
    n_virtual: int = 300,
    fraud_ratio: float = 0.25,
    elliptic_sample_size: int = 5000,
    seed: int = 42,
) -> tuple[nx.DiGraph, list[str], list[str]]:
    """
    Combine virtual AMLSim-style data with a sample of the Elliptic dataset.

    Per Prof. Han recommendation: virtual + mixed data approach to:
      1. Control fraud ratio precisely (Elliptic is heavily imbalanced ~2%)
      2. Test pipeline on realistic blockchain graph structure (Elliptic)
      3. Stress-test specific AML patterns (virtual data)

    Returns:
        (combined_graph, illicit_wallets, licit_wallets)
    """
    # Generate virtual data
    gen = VirtualAMLGenerator(n_wallets=n_virtual, fraud_ratio=fraud_ratio, seed=seed)
    G_virtual, v_illicit, v_licit = gen.generate()

    # Prefix virtual nodes to avoid collision
    G_virtual = nx.relabel_nodes(G_virtual, {n: f"VIRT_{n}" for n in G_virtual.nodes()})
    v_illicit = [f"VIRT_{w}" for w in v_illicit]
    v_licit   = [f"VIRT_{w}" for w in v_licit]

    # Try to load Elliptic
    try:
        G_elliptic, e_illicit, e_licit = load_elliptic_dataset()
        # Sample a subset for speed
        rng = np.random.default_rng(seed)
        sample_nodes = set(rng.choice(list(G_elliptic.nodes()), size=min(elliptic_sample_size, G_elliptic.number_of_nodes()), replace=False))
        G_elliptic   = G_elliptic.subgraph(sample_nodes).copy()
        G_elliptic   = nx.relabel_nodes(G_elliptic, {n: f"ELL_{n}" for n in G_elliptic.nodes()})
        e_illicit = [f"ELL_{w}" for w in e_illicit if f"ELL_{w}" in G_elliptic.nodes()]
        e_licit   = [f"ELL_{w}" for w in e_licit   if f"ELL_{w}" in G_elliptic.nodes()]
        have_elliptic = True
        logger.info("[Mixed] Elliptic sample: %d nodes", G_elliptic.number_of_nodes())
    except (FileNotFoundError, ImportError) as exc:
        logger.warning("[Mixed] Elliptic dataset unavailable (%s) — using virtual data only", exc)
        G_elliptic, e_illicit, e_licit = nx.DiGraph(), [], []
        have_elliptic = False

    # Merge graphs
    G_combined = nx.compose(G_virtual, G_elliptic)
    all_illicit = v_illicit + e_illicit
    all_licit   = v_licit   + e_licit

    # Add cross-graph bridge edges (5% of virtual illicit nodes connect to Elliptic)
    if have_elliptic and e_illicit:
        rng = np.random.default_rng(seed + 1)
        n_bridges = max(1, len(v_illicit) // 20)
        for _ in range(n_bridges):
            src = rng.choice(v_illicit)
            dst = rng.choice(e_illicit[:100] if e_illicit else v_illicit)
            G_combined.add_edge(src, dst, amount_usd=float(rng.uniform(5_000, 100_000)),
                                pattern="cross_graph_bridge")

    logger.info(
        "[Mixed] Combined: %d nodes | %d edges | %d illicit | %d licit",
        G_combined.number_of_nodes(), G_combined.number_of_edges(),
        len(all_illicit), len(all_licit),
    )
    return G_combined, all_illicit, all_licit


# ============================================================
# Main CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Virtual + Mixed AML Data Setup")
    parser.add_argument("--mode",        choices=["virtual", "elliptic", "mixed"], default="virtual")
    parser.add_argument("--n-wallets",   type=int,   default=200,  help="Virtual wallets to generate")
    parser.add_argument("--n-virtual",   type=int,   default=300,  help="Virtual wallets for mixed mode")
    parser.add_argument("--fraud-ratio", type=float, default=0.25, help="Fraction of illicit wallets")
    parser.add_argument("--out-dir",     default="dataset/virtual/")
    parser.add_argument("--info",        action="store_true", help="Show dataset info only")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "virtual" or args.info:
        logger.info("[Setup] Generating virtual AML dataset (n=%d, fraud_ratio=%.0f%%)",
                    args.n_wallets, args.fraud_ratio * 100)
        gen = VirtualAMLGenerator(n_wallets=args.n_wallets, fraud_ratio=args.fraud_ratio)
        G, illicit, licit = gen.export_csv(out_dir)

        stats = {
            "mode": "virtual",
            "n_nodes":   G.number_of_nodes(),
            "n_edges":   G.number_of_edges(),
            "n_illicit": len(illicit),
            "n_licit":   len(licit),
            "fraud_ratio": args.fraud_ratio,
            "patterns": ["smurfing", "layering", "mixer", "rapid_velocity", "normal"],
        }

    elif args.mode == "elliptic":
        G, illicit, licit = load_elliptic_dataset()
        stats = {
            "mode": "elliptic",
            "n_nodes":   G.number_of_nodes(),
            "n_edges":   G.number_of_edges(),
            "n_illicit": len(illicit),
            "n_licit":   len(licit),
        }

    elif args.mode == "mixed":
        G, illicit, licit = build_mixed_dataset(n_virtual=args.n_virtual,
                                                 fraud_ratio=args.fraud_ratio)
        stats = {
            "mode": "mixed",
            "n_nodes":   G.number_of_nodes(),
            "n_edges":   G.number_of_edges(),
            "n_illicit": len(illicit),
            "n_licit":   len(licit),
            "n_virtual": args.n_virtual,
        }

    # Save stats
    stats_path = out_dir / f"dataset_stats_{args.mode}.json"
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\n{'='*50}")
    print(f"[{args.mode.upper()}] Dataset Ready")
    print(f"  Nodes:   {stats['n_nodes']:,}")
    print(f"  Edges:   {stats['n_edges']:,}")
    print(f"  Illicit: {stats['n_illicit']:,} ({stats['n_illicit']/max(stats['n_nodes'],1)*100:.1f}%)")
    print(f"  Licit:   {stats['n_licit']:,}")
    print(f"  Output:  {out_dir.resolve()}")
    print(f"  Stats:   {stats_path.resolve()}")
    print(f"{'='*50}\n")
    print("Next: feed this graph into the QUBO pipeline:")
    print("  tx_graph = TransactionGraph(graph=G, seed_wallet=...,")
    print("                              known_illicit=illicit, known_licit=licit)")
    print("  optimizer = HybridQuantumOptimizer()")
    print("  result = optimizer.optimize(tx_graph)")


if __name__ == "__main__":
    main()
