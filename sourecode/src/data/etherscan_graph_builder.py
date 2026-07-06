"""
Etherscan Graph Builder — Live Blockchain Transaction Graph
===========================================================
Replaces the synthetic nx.scale_free_graph(50) stub in handler.py
with a real blockchain transaction graph built from Etherscan API data.

Usage:
    from src.data.etherscan_graph_builder import build_tx_graph_from_wallet
    tx_graph = build_tx_graph_from_wallet("0xABC...", hops=2, max_nodes=150)

Supports: ETH (Ethereum), BSC (BNB Chain)
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import httpx
import networkx as nx

from src.config import ETHERSCAN_API_KEY
from src.data.price_oracle import convert_native_to_usd
from src.models import TransactionGraph

logger = logging.getLogger(__name__)

# ── API endpoints ──────────────────────────────────────────────────────────────
_CHAIN_APIS = {
    "eth": "https://api.etherscan.io/api",
    "bsc": "https://api.bscscan.com/api",
}

# ── Known mixer / bridge / sanctioned contract addresses (partial list) ───────
_KNOWN_MIXERS = {
    # Tornado Cash contracts (OFAC sanctioned 2022)
    "0x47ce0c6eaf42405b1c7b42a3d9c9b95af1e87b6",
    "0x910cbd523d972eb0a6f4cae4618ad62622b39dbf",
    "0x12d66f87a04a9e220c9d7efbd0df01df3c3c9f4",
    # ChipMixer (FBI seized 2023)
    "0x3cbded43efdaf0fc77b9c55f6fc9988fcc9b37f",
}

_KNOWN_BRIDGES = {
    # Multichain (hacked 2023)
    "0xc564ee9f21ed8a2d8e7e76c085740d5e4c5fafbe",
    # Ronin Bridge (hacked $625M 2022)
    "0x1a2a1c938ce3ec39b6d47113c7955baa9dd454f2",
}


def _fetch_transactions(
    wallet_address: str,
    chain: str = "eth",
    max_tx: int = 100,
    api_key: str = "",
) -> list[dict]:
    """
    Fetch recent transactions for a wallet from Etherscan / BSCScan.

    Returns:
        List of transaction dicts. Empty list on error.
    """
    base_url = _CHAIN_APIS.get(chain, _CHAIN_APIS["eth"])
    coin = "eth" if chain == "eth" else "bnb"

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(base_url, params={
                "module":     "account",
                "action":     "txlist",
                "address":    wallet_address,
                "startblock": 0,
                "endblock":   99999999,
                "sort":       "desc",
                "apikey":     api_key or ETHERSCAN_API_KEY,
                "offset":     max_tx,
                "page":       1,
            })
            resp.raise_for_status()
            data = resp.json()

        result = data.get("result", [])
        if isinstance(result, str):
            # Etherscan returns string error messages on failure
            logger.warning(f"[GraphBuilder] Etherscan error for {wallet_address}: {result}")
            return []

        logger.info(f"[GraphBuilder] Fetched {len(result)} txs for {wallet_address} ({chain})")
        return result

    except Exception as exc:
        logger.warning(f"[GraphBuilder] API fetch failed for {wallet_address}: {exc}")
        return []


def _enrich_node_attributes(
    graph: nx.DiGraph,
    wallet_address: str,
    txs: list[dict],
    chain: str,
) -> None:
    """
    Compute and attach risk-relevant node attributes from transaction list.
    Attributes are consumed by graph_to_qubo._extract_node_risk_scores().
    """
    if not txs:
        return

    coin = "eth" if chain == "eth" else "bnb"

    # Compute tx velocity (txs per hour) using last 24h
    now_ts = time.time()
    txs_24h = [
        t for t in txs
        if (now_ts - int(t.get("timeStamp", 0))) < 86400
    ]
    tx_velocity = len(txs_24h)  # txs in last 24h (used as hourly proxy)

    # Detect mixer interactions
    counterparties = {t.get("to", "").lower() for t in txs} | {t.get("from", "").lower() for t in txs}
    is_mixer = int(bool(counterparties & _KNOWN_MIXERS))
    is_bridge = int(bool(counterparties & _KNOWN_BRIDGES))

    # Round-number detection (structuring indicator)
    amounts = [int(t.get("value", 0)) / 1e18 for t in txs if int(t.get("value", 0)) > 0]
    round_tx_ratio = 0.0
    if amounts:
        round_count = sum(1 for a in amounts if abs(a * 10 - round(a * 10)) < 0.001)
        round_tx_ratio = round_count / len(amounts)

    if wallet_address in graph.nodes:
        graph.nodes[wallet_address]["is_mixer"]          = is_mixer
        graph.nodes[wallet_address]["is_bridge"]         = is_bridge
        graph.nodes[wallet_address]["tx_velocity"]       = float(tx_velocity)
        graph.nodes[wallet_address]["round_number_ratio"] = round_tx_ratio
        graph.nodes[wallet_address]["tx_count_24h"]      = len(txs_24h)
        graph.nodes[wallet_address]["chain"]             = chain


def build_tx_graph_from_wallet(
    wallet_address: str,
    chain: str = "eth",
    hops: int = 2,
    max_nodes: int = 150,
    api_key: str = "",
) -> TransactionGraph:
    """
    Build a real blockchain transaction graph centred on a target wallet.

    Replaces the synthetic nx.scale_free_graph(50) stub used in demo mode.

    Algorithm:
        1. Fetch direct transactions of target wallet (hop=1)
        2. For each unique counterparty (up to hop_limit), fetch their txs
        3. Build NetworkX DiGraph: nodes=wallets, edges=transactions
        4. Enrich node attributes (mixer, bridge, velocity, round-tx)
        5. Wrap in TransactionGraph (known_illicit=[target], known_licit=[rest])

    Args:
        wallet_address: Target ERC-20/ETH wallet address (EIP-55 format)
        chain:          "eth" | "bsc"
        hops:           BFS depth (1=direct counterparties, 2=2-hop neighbors)
        max_nodes:      Cap graph size before QUBO mapping
        api_key:        Etherscan API key (falls back to config)

    Returns:
        TransactionGraph ready for QUBO optimization
    """
    logger.info(
        f"[GraphBuilder] Building live graph for {wallet_address} "
        f"| chain={chain} | hops={hops} | max_nodes={max_nodes}"
    )

    G = nx.DiGraph()
    coin = "eth" if chain == "eth" else "bnb"

    visited: set[str] = set()
    queue: list[tuple[str, int]] = [(wallet_address.lower(), 0)]
    known_illicit: list[str] = [wallet_address.lower()]
    known_licit: list[str] = []

    while queue and G.number_of_nodes() < max_nodes:
        current_wallet, depth = queue.pop(0)

        if current_wallet in visited:
            continue
        visited.add(current_wallet)

        txs = _fetch_transactions(current_wallet, chain=chain, max_tx=50, api_key=api_key)

        # Add edges
        for tx in txs:
            from_addr = tx.get("from", "").lower()
            to_addr   = tx.get("to", "").lower()

            if not from_addr or not to_addr:
                continue

            value_native = int(tx.get("value", 0)) / 1e18
            amount_usd   = convert_native_to_usd(value_native, coin)

            G.add_node(from_addr)
            G.add_node(to_addr)
            G.add_edge(from_addr, to_addr, amount_usd=amount_usd, tx_hash=tx.get("hash", ""))

            # Enqueue neighbors for BFS if within hop limit
            if depth < hops:
                for neighbor in [from_addr, to_addr]:
                    if neighbor not in visited and G.number_of_nodes() < max_nodes:
                        queue.append((neighbor, depth + 1))
                        if neighbor != wallet_address.lower() and neighbor not in known_licit:
                            known_licit.append(neighbor)

        # Enrich node attributes
        _enrich_node_attributes(G, current_wallet, txs, chain)

        # Rate limit: max 5 API calls/sec (Etherscan free tier)
        time.sleep(0.2)

    # Ensure target wallet is in graph
    if not G.has_node(wallet_address.lower()):
        G.add_node(wallet_address.lower())

    logger.info(
        f"[GraphBuilder] Graph built: {G.number_of_nodes()} nodes, "
        f"{G.number_of_edges()} edges | illicit={len(known_illicit)} | licit={len(known_licit)}"
    )

    return TransactionGraph(
        graph=G,
        known_illicit=known_illicit,
        known_licit=known_licit[:max_nodes],  # cap licit list
        source_dataset=f"etherscan_live_{chain}",
    )


def build_demo_graph(wallet_address: str, n_nodes: int = 80) -> TransactionGraph:
    """
    Deterministic demo graph (no API calls needed).
    More realistic than scale_free_graph — uses Barabasi-Albert topology
    with hand-crafted risk attributes to simulate laundering patterns.

    Use this when ETHERSCAN_API_KEY is not set or for offline demos.
    """
    import numpy as np
    rng = np.random.default_rng(seed=int(wallet_address[-4:], 16) % 2**31)

    # Barabasi-Albert scale-free graph (closer to real blockchain topology)
    G_ba = nx.barabasi_albert_graph(n=n_nodes, m=3, seed=42)
    G = G_ba.to_directed()

    # Map node IDs to wallet-like addresses
    nodes = list(G.nodes())
    mapping = {nodes[0]: wallet_address.lower()}
    for i, n in enumerate(nodes[1:], 1):
        mapping[n] = f"0x{i:040x}"
    G = nx.relabel_nodes(G, mapping)

    # Target wallet = illicit hub (high fan-out + mixer)
    G.nodes[wallet_address.lower()]["is_mixer"]    = 1
    G.nodes[wallet_address.lower()]["is_bridge"]   = 0
    G.nodes[wallet_address.lower()]["tx_velocity"] = float(rng.integers(80, 150))

    # Random attributes for licit nodes
    for node in list(G.nodes())[1:]:
        G.nodes[node]["is_mixer"]    = int(rng.random() > 0.95)
        G.nodes[node]["is_bridge"]   = int(rng.random() > 0.92)
        G.nodes[node]["tx_velocity"] = float(rng.exponential(10))

    # Edge amounts
    for u, v in G.edges():
        G[u][v]["amount_usd"] = float(rng.exponential(8_000))

    known_illicit = [wallet_address.lower()]
    known_licit   = [mapping[n] for n in nodes[1:]]

    logger.info(
        f"[GraphBuilder] Demo graph built: {G.number_of_nodes()} nodes "
        f"(Barabasi-Albert topology, deterministic seed)"
    )

    return TransactionGraph(
        graph=G,
        known_illicit=known_illicit,
        known_licit=known_licit,
        source_dataset="demo_barabasi_albert",
    )
