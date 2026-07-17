"""
Elliptic Dataset Loader — Baseline Training Data

Loads the Kaggle Elliptic Bitcoin dataset:
  - elliptic_txs_features.csv  (203,769 transactions × 167 features)
  - elliptic_txs_classes.csv   (labels: 1=illicit, 2=licit, unknown)

Dataset: https://www.kaggle.com/datasets/ellipticco/elliptic-data-set
Paper: Weber et al. "Anti-Money Laundering in Bitcoin: Experimenting with Graph Convolutional Networks" (2019)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import networkx as nx
import numpy as np
import pandas as pd

from src.config import ELLIPTIC_DATASET_PATH, ELLIPTIC_LABELS_PATH, ELLIPTIC_EDGES_PATH
from src.models import TransactionGraph

logger = logging.getLogger(__name__)


def load_elliptic_dataset(
    features_path: Optional[Path] = None,
    labels_path: Optional[Path] = None,
    edges_path: Optional[Path] = None,
    max_rows: Optional[int] = None,
) -> TransactionGraph:
    """
    Load Elliptic dataset and return as TransactionGraph.

    Args:
        features_path: Path to elliptic_txs_features.csv
        labels_path:   Path to elliptic_txs_classes.csv
        edges_path:    Path to elliptic_txs_edgelist.csv
        max_rows:      Limit rows for testing (None = full dataset)

    Returns:
        TransactionGraph ready for QUBO mapping or GNN baseline training
    """
    fp = Path(features_path or ELLIPTIC_DATASET_PATH)
    lp = Path(labels_path or ELLIPTIC_LABELS_PATH)
    ep = Path(edges_path or ELLIPTIC_EDGES_PATH)

    if not fp.exists():
        raise FileNotFoundError(f"Elliptic features file not found: {fp}")
    if not lp.exists():
        raise FileNotFoundError(f"Elliptic labels file not found: {lp}")
    if not ep.exists():
        logger.warning(f"Elliptic edges file not found: {ep}. Graph will have no edges.")

    logger.info(f"Loading Elliptic dataset from {fp}")

    # Load features (column 0 = txId, columns 1-167 = features)
    features_df = pd.read_csv(fp, header=None, nrows=max_rows)
    features_df.columns = ["txId"] + [f"f{i}" for i in range(1, len(features_df.columns))]
    features_df["txId"] = features_df["txId"].astype(str)

    # Load labels (txId, class: "1"=illicit, "2"=licit, "unknown")
    labels_df = pd.read_csv(lp)
    labels_df["txId"] = labels_df["txId"].astype(str)
    labels_df["class"] = labels_df["class"].astype(str)

    # Merge
    df = features_df.merge(labels_df, on="txId", how="left")
    df["class"] = df["class"].fillna("unknown")

    illicit = df[df["class"] == "1"]["txId"].tolist()
    licit = df[df["class"] == "2"]["txId"].tolist()

    logger.info(
        f"Loaded {len(df)} transactions | "
        f"illicit={len(illicit)} ({len(illicit)/len(df)*100:.1f}%) | "
        f"licit={len(licit)} ({len(licit)/len(df)*100:.1f}%) | "
        f"unknown={len(df) - len(illicit) - len(licit)}"
    )

    # Build NetworkX graph
    G = nx.DiGraph()
    feature_cols = [c for c in df.columns if c.startswith("f")]

    for _, row in df.iterrows():
        G.add_node(
            row["txId"],
            features=row[feature_cols].values.astype(np.float32),
            label=row["class"],
            is_mixer=0,
            is_bridge=0,
            tx_velocity=float(row.get("f1", 0)),  # f1 = timestep proxy
        )

    # Load edges if available
    if ep.exists():
        logger.info(f"Loading Elliptic edges from {ep}")
        edges_df = pd.read_csv(ep)
        edges_df["txId1"] = edges_df["txId1"].astype(str)
        edges_df["txId2"] = edges_df["txId2"].astype(str)
        
        # Only add edges between nodes that exist in our (possibly subsetted) dataframe
        valid_nodes = set(df["txId"].tolist())
        edges_filtered = edges_df[edges_df["txId1"].isin(valid_nodes) & edges_df["txId2"].isin(valid_nodes)]
        
        edge_list = list(zip(edges_filtered["txId1"], edges_filtered["txId2"]))
        G.add_edges_from(edge_list)
        logger.info(f"Added {len(edge_list)} edges to the graph.")

    # Node features dict
    node_features = {
        row["txId"]: row[feature_cols].values.astype(np.float32)
        for _, row in df.iterrows()
    }

    return TransactionGraph(
        graph=G,
        node_features=node_features,
        known_illicit=illicit,
        known_licit=licit,
        source_dataset="elliptic_bitcoin",
    )


def get_train_test_split(
    tx_graph: TransactionGraph,
    test_ratio: float = 0.20,
    seed: int = 42,
) -> Tuple[TransactionGraph, TransactionGraph]:
    """
    Split TransactionGraph into train/test subgraphs (80/20 default).
    Only labelled nodes are split — unknown nodes go to train.
    """
    rng = np.random.default_rng(seed)
    labelled = tx_graph.known_illicit + tx_graph.known_licit
    rng.shuffle(labelled)

    split_idx = int(len(labelled) * (1 - test_ratio))
    train_ids = set(labelled[:split_idx])
    test_ids = set(labelled[split_idx:])

    # All unknown nodes → train
    all_nodes = set(tx_graph.graph.nodes())
    unlabelled = all_nodes - set(tx_graph.known_illicit) - set(tx_graph.known_licit)
    train_ids |= unlabelled

    train_graph = tx_graph.graph.subgraph(train_ids).copy()
    test_graph = tx_graph.graph.subgraph(test_ids).copy()

    train_tx = TransactionGraph(
        graph=train_graph,
        node_features={k: v for k, v in tx_graph.node_features.items() if k in train_ids},
        known_illicit=[w for w in tx_graph.known_illicit if w in train_ids],
        known_licit=[w for w in tx_graph.known_licit if w in train_ids],
        source_dataset=tx_graph.source_dataset + "_train",
    )
    test_tx = TransactionGraph(
        graph=test_graph,
        node_features={k: v for k, v in tx_graph.node_features.items() if k in test_ids},
        known_illicit=[w for w in tx_graph.known_illicit if w in test_ids],
        known_licit=[w for w in tx_graph.known_licit if w in test_ids],
        source_dataset=tx_graph.source_dataset + "_test",
    )

    logger.info(
        f"Train: {len(train_graph.nodes())} nodes "
        f"({len(train_tx.known_illicit)} illicit, {len(train_tx.known_licit)} licit) | "
        f"Test: {len(test_graph.nodes())} nodes "
        f"({len(test_tx.known_illicit)} illicit, {len(test_tx.known_licit)} licit)"
    )
    return train_tx, test_tx
