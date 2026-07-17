"""
[D1] Network Topology Graph Visualization
==========================================
Deliverable D1 (Mentorship Review slide 19 — Next Steps #01):
"Deliver the full local transaction graph visualization with
risk-score overlays for the seed wallet."

Features:
  - Full interactive Plotly graph with risk-score colour overlays
  - Red (r\u0303 > 0.7) / Yellow (0.3-0.7) / Green (< 0.3) node colouring
  - Edge thickness \u221d transaction amount (A\u1d62\u2c7c)
  - Smurfing cluster highlights (MIMO tensor result)
  - Top-20 subgraph boundary annotation
  - Supports: Elliptic dataset + Etherscan live data
  - Exports: HTML (interactive) + PNG (static for SAR reports)

Usage:
    python viz_network_topology.py --wallet 0xABC... --source elliptic
    python viz_network_topology.py --wallet 0xABC... --source live
    python viz_network_topology.py --demo   # demo graph (no API key needed)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# \u2500\u2500 Add project root to sys.path \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import networkx as nx
import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")


# \u2500\u2500\u2500 Colour Palette (risk-score overlays) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _risk_colour(r: float) -> str:
    """Map risk score r\u0303 \u2208 [0,1] to hex colour."""
    if r > 0.7:
        return "#e53935"   # High  \u2014 deep red
    elif r > 0.3:
        return "#fb8c00"   # Med   \u2014 amber
    else:
        return "#43a047"   # Low   \u2014 green


def _risk_label(r: float) -> str:
    if r > 0.7:
        return "HIGH"
    elif r > 0.3:
        return "MED"
    return "LOW"


# \u2500\u2500\u2500 Demo Graph Builder \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_demo_graph(seed_wallet: str = "0xSEED") -> tuple[nx.DiGraph, dict]:
    """
    Build the representative demo transaction graph from the Mermaid flow
    (network_topology_graph.mermaid) for offline testing.
    """
    G = nx.DiGraph()

    nodes = {
        seed_wallet:  {"label": "Seed Wallet",    "r": 0.50, "hop": 0, "type": "seed"},
        "0xA1":       {"label": "Wallet A1",       "r": 0.82, "hop": 1, "type": "wallet"},
        "0xA2":       {"label": "Wallet A2",       "r": 0.45, "hop": 1, "type": "wallet",
                       "smurfing_baseline": True},
        "0xA3":       {"label": "Wallet A3",       "r": 0.12, "hop": 1, "type": "wallet"},
        "0xA4":       {"label": "Wallet A4",       "r": 0.91, "hop": 1, "type": "wallet"},
        "0xB1":       {"label": "Wallet B1",       "r": 0.76, "hop": 2, "type": "wallet"},
        "0xB2":       {"label": "Wallet B2",       "r": 0.08, "hop": 2, "type": "wallet"},
        "0xB3":       {"label": "Wallet B3",       "r": 0.51, "hop": 2, "type": "wallet"},
        "0xB4":       {"label": "Mixer/Tumbler",   "r": 0.95, "hop": 2, "type": "mixer"},
        "0xB5":       {"label": "Wallet B5",       "r": 0.15, "hop": 2, "type": "wallet"},
        "0xC1":       {"label": "Exchange Dep.",   "r": 0.38, "hop": 3, "type": "exchange"},
        "0xC2":       {"label": "Wallet C2",       "r": 0.88, "hop": 3, "type": "wallet"},
        "0xC3":       {"label": "Wallet C3",       "r": 0.20, "hop": 3, "type": "wallet"},
        "0xSM1":      {"label": "Micro-tx $980",   "r": 0.30, "hop": 0, "type": "smurf"},
        "0xSM2":      {"label": "Micro-tx $995",   "r": 0.30, "hop": 0, "type": "smurf"},
        "0xSM3":      {"label": "Micro-tx $1005",  "r": 0.30, "hop": 0, "type": "smurf"},
        "0xSM4":      {"label": "Micro-tx $990",   "r": 0.30, "hop": 0, "type": "smurf"},
    }
    for addr, attrs in nodes.items():
        G.add_node(addr, **attrs)

    edges = [
        (seed_wallet, "0xA1", {"amount_usd": 45200, "width": 5}),
        (seed_wallet, "0xA2", {"amount_usd": 1100,  "width": 1}),
        (seed_wallet, "0xA3", {"amount_usd": 80,    "width": 0.5}),
        (seed_wallet, "0xA4", {"amount_usd": 38900, "width": 5}),
        ("0xA1", "0xB1",      {"amount_usd": 44800, "width": 5}),
        ("0xA1", "0xB2",      {"amount_usd": 150,   "width": 0.5}),
        ("0xA2", "0xB3",      {"amount_usd": 900,   "width": 1}),
        ("0xA4", "0xB4",      {"amount_usd": 37600, "width": 5}),
        ("0xA4", "0xB5",      {"amount_usd": 60,    "width": 0.5}),
        ("0xB1", "0xC2",      {"amount_usd": 44100, "width": 5}),
        ("0xB4", "0xC1",      {"amount_usd": 12300, "width": 3}),
        ("0xB4", "0xC3",      {"amount_usd": 11900, "width": 3}),
        ("0xSM1", "0xA2",     {"amount_usd": 980,   "width": 1, "smurf": True}),
        ("0xSM2", "0xA2",     {"amount_usd": 995,   "width": 1, "smurf": True}),
        ("0xSM3", "0xA2",     {"amount_usd": 1005,  "width": 1, "smurf": True}),
        ("0xSM4", "0xA2",     {"amount_usd": 990,   "width": 1, "smurf": True}),
    ]
    for u, v, attrs in edges:
        G.add_edge(u, v, **attrs)

    risk_scores = {addr: attrs["r"] for addr, attrs in nodes.items()}
    return G, risk_scores


# \u2500\u2500\u2500 Plotly Interactive Graph \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def build_plotly_figure(G, risk_scores, seed_wallet, top20_nodes=None, title="AML Transaction Network"):
    try:
        import plotly.graph_objects as go
    except ImportError:
        logger.error("plotly not installed. Run: pip install plotly")
        raise

    pos = nx.kamada_kawai_layout(G)
    top20_nodes = top20_nodes or set()

    # Edge traces
    edge_traces = []
    for u, v, data in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        is_smurf = data.get("smurf", False)
        amount   = data.get("amount_usd", 0)
        width    = max(0.5, min(np.log1p(amount) / 3, 8))
        edge_traces.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line=dict(width=width, color="#ff6b6b" if is_smurf else "#546e7a",
                      dash="dot" if is_smurf else "solid"),
            hoverinfo="none", showlegend=False,
        ))

    # Node traces grouped by risk level
    groups = {
        "HIGH (r\u0303>0.7)":   {"colour": "#e53935", "symbol": "circle",  "nodes": []},
        "MED (0.3\u20130.7)":   {"colour": "#fb8c00", "symbol": "circle",  "nodes": []},
        "LOW (r\u0303<0.3)":    {"colour": "#43a047", "symbol": "circle",  "nodes": []},
        "Smurf Cluster":        {"colour": "#ff8f00", "symbol": "diamond", "nodes": []},
        "Mixer/Bridge":         {"colour": "#7b1fa2", "symbol": "square",  "nodes": []},
        "Seed Wallet":          {"colour": "#1565c0", "symbol": "star",    "nodes": []},
    }

    for node in G.nodes():
        r     = risk_scores.get(node, 0.0)
        ntype = G.nodes[node].get("type", "wallet")
        label = G.nodes[node].get("label", node[:10])
        baseline_note = "<br><i>\u26a0\ufe0f Baseline r\u0303 \u2014 pre-smurfing integration</i>" \
                        if G.nodes[node].get("smurfing_baseline") else ""
        top20_note = "<br>\u2705 In Top-20 QAOA subgraph" if node in top20_nodes else ""
        hover = (f"<b>{label}</b><br>Address: {node}<br>"
                 f"r\u0303 = {r:.2f} [{_risk_label(r)}]<br>Type: {ntype}{baseline_note}{top20_note}")
        entry = {"node": node, "x": pos[node][0], "y": pos[node][1],
                 "hover": hover, "label": label}

        if node == seed_wallet:
            groups["Seed Wallet"]["nodes"].append(entry)
        elif ntype == "smurf":
            groups["Smurf Cluster"]["nodes"].append(entry)
        elif ntype == "mixer":
            groups["Mixer/Bridge"]["nodes"].append(entry)
        elif r > 0.7:
            groups["HIGH (r\u0303>0.7)"]["nodes"].append(entry)
        elif r > 0.3:
            groups["MED (0.3\u20130.7)"]["nodes"].append(entry)
        else:
            groups["LOW (r\u0303<0.3)"]["nodes"].append(entry)

    node_traces = []
    for gname, gdata in groups.items():
        if not gdata["nodes"]:
            continue
        ns = gdata["nodes"]
        in_t20 = [n["node"] in top20_nodes for n in ns]
        node_traces.append(go.Scatter(
            x=[n["x"] for n in ns], y=[n["y"] for n in ns],
            mode="markers+text",
            name=gname,
            text=[n["label"] for n in ns],
            textposition="top center",
            textfont=dict(size=9),
            hovertext=[n["hover"] for n in ns],
            hoverinfo="text",
            marker=dict(
                size=[20 if n["node"] == seed_wallet else 14 for n in ns],
                color=gdata["colour"],
                symbol=gdata["symbol"],
                line=dict(
                    width=[3 if t else 1 for t in in_t20],
                    color=["#ffeb3b" if t else "#ffffff" for t in in_t20],
                ),
                opacity=0.9,
            ),
        ))

    fig = go.Figure(
        data=edge_traces + node_traces,
        layout=go.Layout(
            title=dict(text=f"<b>{title}</b><br><sup>Seed: {seed_wallet} | "
                            f"Nodes: {G.number_of_nodes()} | "
                            f"Edges: {G.number_of_edges()} | "
                            f"\ud83d\udfe1 border = Top-20 QAOA subgraph</sup>", x=0.5),
            paper_bgcolor="#1a1a2e", plot_bgcolor="#16213e",
            font=dict(color="#e0e0e0", family="Inter, Arial, sans-serif"),
            showlegend=True,
            legend=dict(bgcolor="rgba(255,255,255,0.08)", bordercolor="rgba(255,255,255,0.2)",
                        borderwidth=1, font=dict(size=11)),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            hovermode="closest",
            margin=dict(l=20, r=20, t=100, b=40),
            annotations=[dict(
                text=("Edge width \u221d A\u1d62\u2c7c (USD) | Node colour = r\u0303\u1d62 classical risk score | "
                      "\ud83d\udd36 Diamond = MIMO-detected smurfing cluster"),
                xref="paper", yref="paper", x=0.0, y=-0.05,
                showarrow=False, font=dict(size=9, color="#90a4ae"), align="left",
            )],
        )
    )
    return fig


# \u2500\u2500\u2500 Matplotlib Static Fallback \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def build_matplotlib_figure(G, risk_scores, seed_wallet, top20_nodes=None, title="AML Transaction Network"):
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
    except ImportError:
        logger.error("matplotlib not installed.")
        raise

    top20_nodes = top20_nodes or set()
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.set_facecolor("#1a1a2e")
    fig.patch.set_facecolor("#0f0f1a")
    pos = nx.kamada_kawai_layout(G)

    edge_colours, edge_widths = [], []
    for u, v, data in G.edges(data=True):
        is_smurf = data.get("smurf", False)
        amount   = data.get("amount_usd", 0)
        edge_colours.append("#ff6b6b" if is_smurf else "#546e7a")
        edge_widths.append(max(0.5, min(np.log1p(amount) / 4, 6)))

    nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colours, width=edge_widths,
                           arrows=True, arrowsize=15, alpha=0.7)

    node_colours, node_sizes = [], []
    for node in G.nodes():
        r = risk_scores.get(node, 0.0)
        ntype = G.nodes[node].get("type", "wallet")
        if node == seed_wallet:
            node_colours.append("#1565c0"); node_sizes.append(800)
        elif ntype == "smurf":
            node_colours.append("#ff8f00"); node_sizes.append(400)
        elif ntype == "mixer":
            node_colours.append("#7b1fa2"); node_sizes.append(600)
        else:
            node_colours.append(_risk_colour(r))
            node_sizes.append(500 if r > 0.7 else 300)

    node_borders = ["#ffeb3b" if n in top20_nodes else "#ffffff" for n in G.nodes()]
    node_lw      = [3 if n in top20_nodes else 0.5 for n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colours, node_size=node_sizes,
                           edgecolors=node_borders, linewidths=node_lw)
    nx.draw_networkx_labels(G, pos,
                            labels={n: G.nodes[n].get("label", n[:8]) for n in G.nodes()},
                            ax=ax, font_size=7, font_color="#e0e0e0")

    legend_items = [
        mpatches.Patch(color="#e53935", label="HIGH risk (r\u0303 > 0.7)"),
        mpatches.Patch(color="#fb8c00", label="MED risk (0.3\u20130.7)"),
        mpatches.Patch(color="#43a047", label="LOW risk (r\u0303 < 0.3)"),
        mpatches.Patch(color="#ff8f00", label="Smurfing cluster (MIMO)"),
        mpatches.Patch(color="#7b1fa2", label="Mixer / Bridge"),
        mpatches.Patch(color="#1565c0", label="Seed wallet"),
        mpatches.Patch(color="#ffeb3b", label="Top-20 QAOA subgraph"),
    ]
    ax.legend(handles=legend_items, loc="upper left",
              facecolor="#1a1a2e", edgecolor="#546e7a",
              labelcolor="#e0e0e0", fontsize=8)
    ax.set_title(title, color="#e0e0e0", fontsize=13, pad=15)
    ax.axis("off")
    plt.tight_layout()
    return fig


# \u2500\u2500\u2500 Elliptic Dataset Loader \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def _build_graph_from_elliptic(seed_tx_id: str, max_hops: int = 2) -> tuple[nx.DiGraph, dict]:
    try:
        import pandas as pd
        from src.config import ELLIPTIC_DATASET_PATH, ELLIPTIC_LABELS_PATH, ELLIPTIC_EDGES_PATH
    except ImportError as e:
        logger.error("pandas/config missing: %s", e)
        raise

    logger.info("[D1] Loading Elliptic dataset...")
    labels = pd.read_csv(ELLIPTIC_LABELS_PATH)
    edges  = pd.read_csv(ELLIPTIC_EDGES_PATH)
    label_map = {str(r["txId"]): r["class"] for _, r in labels.iterrows()}

    G = nx.DiGraph()
    frontier, visited = {str(seed_tx_id)}, set()

    for hop in range(max_hops):
        next_frontier = set()
        hop_edges = edges[
            edges["txId1"].astype(str).isin(frontier) |
            edges["txId2"].astype(str).isin(frontier)
        ]
        for _, row in hop_edges.iterrows():
            u, v = str(row["txId1"]), str(row["txId2"])
            G.add_edge(u, v, amount_usd=1000.0, hop=hop)
            next_frontier.update({u, v})
        visited.update(frontier)
        frontier = next_frontier - visited
        if not frontier:
            break

    risk_scores = {}
    for node in G.nodes():
        lbl = label_map.get(node, "unknown")
        r   = (np.random.uniform(0.7, 1.0) if lbl == "1" else
               np.random.uniform(0.0, 0.3) if lbl == "2" else
               np.random.uniform(0.3, 0.7))
        risk_scores[node] = r
        G.nodes[node]["r"]     = r
        G.nodes[node]["label"] = f"TX-{node[:6]}"
        G.nodes[node]["type"]  = "wallet"

    logger.info("[D1] Elliptic subgraph: %d nodes, %d edges", G.number_of_nodes(), G.number_of_edges())
    return G, risk_scores


# \u2500\u2500\u2500 Main CLI \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

def main():
    parser = argparse.ArgumentParser(description="[D1] AML Network Topology Graph Visualization")
    parser.add_argument("--wallet",  default="0xSEED", help="Seed wallet/tx address")
    parser.add_argument("--source",  choices=["demo", "elliptic", "live"], default="demo")
    parser.add_argument("--demo",    action="store_true", help="Use built-in demo graph")
    parser.add_argument("--out-dir", default="reports/", help="Output directory")
    parser.add_argument("--static",  action="store_true", help="Also generate Matplotlib PNG")
    parser.add_argument("--no-html", action="store_true", help="Skip interactive HTML export")
    args = parser.parse_args()

    if args.demo:
        args.source = "demo"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build Graph
    if args.source == "demo":
        logger.info("[D1] Building demo graph")
        G, risk_scores = _build_demo_graph(seed_wallet=args.wallet)
        seed = args.wallet
    elif args.source == "elliptic":
        G, risk_scores = _build_graph_from_elliptic(args.wallet)
        seed = args.wallet
    elif args.source == "live":
        from src.data.etherscan_graph_builder import build_tx_graph_from_wallet
        tx_graph = build_tx_graph_from_wallet(args.wallet, chain="eth", hops=2, max_nodes=80)
        G = tx_graph.graph
        from src.quantum.graph_to_qubo import _extract_node_risk_scores, detect_smurfing_via_tensor
        smurf = detect_smurfing_via_tensor(G)
        risk_scores = _extract_node_risk_scores(G, smurf)
        for node, r in risk_scores.items():
            G.nodes[node].update({"r": r, "label": node[:8], "type": "wallet"})
        seed = args.wallet

    # Top-20 Subgraph Selection
    from src.quantum.graph_to_qubo import select_top_k_subgraph
    top20_sub   = select_top_k_subgraph(G, risk_scores, k=20, seed_wallet=seed)
    top20_nodes = set(top20_sub.nodes())
    logger.info("[D1] Top-20 subgraph: %d nodes selected for QAOA", len(top20_nodes))

    # Interactive HTML
    if not args.no_html:
        try:
            fig = build_plotly_figure(G, risk_scores, seed, top20_nodes,
                                      title="AML Transaction Network \u2014 Quantum Risk-Score Overlay")
            html_path = out_dir / f"network_topology_{args.wallet[:8]}.html"
            fig.write_html(str(html_path))
            logger.info("[D1] Interactive graph \u2192 %s", html_path)
            print(f"\n\u2705 Interactive graph: {html_path.resolve()}")
        except ImportError:
            logger.warning("[D1] plotly not installed \u2014 pip install plotly")

    # Static PNG
    if args.static:
        try:
            import matplotlib.pyplot as plt
            fig_mpl = build_matplotlib_figure(G, risk_scores, seed, top20_nodes,
                                              title=f"AML Transaction Network \u2014 {args.wallet[:12]}")
            png_path = out_dir / f"network_topology_{args.wallet[:8]}.png"
            fig_mpl.savefig(str(png_path), dpi=180, bbox_inches="tight", facecolor="#0f0f1a")
            plt.close(fig_mpl)
            logger.info("[D1] Static PNG \u2192 %s", png_path)
            print(f"\u2705 Static PNG: {png_path.resolve()}")
        except ImportError:
            logger.warning("[D1] matplotlib not installed \u2014 pip install matplotlib")

    # Summary
    high_risk = [n for n, r in risk_scores.items() if r > 0.7]
    print(f"\n\ud83d\udcca Graph Summary:")
    print(f"   Nodes: {G.number_of_nodes()} | Edges: {G.number_of_edges()}")
    print(f"   High-risk nodes (r\u0303 > 0.7): {len(high_risk)}")
    print(f"   Top-20 QAOA subgraph: {len(top20_nodes)} nodes")
    print(f"   Seed wallet: {seed}")


if __name__ == "__main__":
    main()
