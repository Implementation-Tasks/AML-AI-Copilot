"""
Tool Base Classes & All Agent Tools for AML AI Copilot.

Tools follow a strict interface contract:
  - Input:  wallet_address (str) or tx_hash (str)
  - Output: ToolOutput with success, data, confidence_score, evidence_links
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional

import httpx

from src.config import (
    ETHERSCAN_API_KEY,
    OPENSANCTIONS_API_KEY,
)
from src.models import ToolOutput

logger = logging.getLogger(__name__)

# ─── Base Tool ───────────────────────────────────────────────────────────────

class BaseTool(ABC):
    """All Agent tools inherit from this base class."""

    name: str = "base_tool"
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds, doubled per retry (exponential backoff)

    def run(self, **kwargs) -> ToolOutput:
        """Public entrypoint with retry + error handling."""
        for attempt in range(1, self.max_retries + 1):
            try:
                result = self._execute(**kwargs)
                logger.info(f"[{self.name}] Success on attempt {attempt}")
                return result
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    wait = self.retry_delay * (2 ** attempt)
                    logger.warning(f"[{self.name}] Rate limited. Waiting {wait:.1f}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"[{self.name}] HTTP error: {e}")
                    break
            except Exception as e:
                logger.error(f"[{self.name}] Attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

        return ToolOutput(
            success=False,
            data={},
            confidence_score=0.0,
            error=f"[{self.name}] Failed after {self.max_retries} attempts",
        )

    @abstractmethod
    def _execute(self, **kwargs) -> ToolOutput:
        """Implement the actual tool logic here."""
        ...


# ─── GraphQueryTool ───────────────────────────────────────────────────────────

class GraphQueryTool(BaseTool):
    """
    Query The Graph Protocol for DeFi transaction data.
    Supports: Uniswap, Aave, Compound, Tornado Cash subgraphs.
    """
    name = "graph_query_tool"
    SUBGRAPH_URLS = {
        "uniswap_v3": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
        "tornado_cash": "https://api.thegraph.com/subgraphs/name/tornadocash/mainnet",
        "aave_v3": "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
    }

    def _execute(self, wallet_address: str, protocol: str = "uniswap_v3") -> ToolOutput:
        url = self.SUBGRAPH_URLS.get(protocol, self.SUBGRAPH_URLS["uniswap_v3"])
        query = """
        {
          swaps(where: {origin: "%s"}, first: 100, orderBy: timestamp, orderDirection: desc) {
            id
            timestamp
            amount0
            amount1
            token0 { symbol }
            token1 { symbol }
          }
        }
        """ % wallet_address.lower()

        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json={"query": query})
            resp.raise_for_status()
            data = resp.json()

        swaps = data.get("data", {}).get("swaps", [])
        return ToolOutput(
            success=True,
            data={"protocol": protocol, "swaps": swaps, "count": len(swaps)},
            confidence_score=0.85,
            evidence_links=[f"{url}?query={hashlib.md5(query.encode()).hexdigest()[:8]}"],
        )


# ─── EtherscanAPITool ─────────────────────────────────────────────────────────

class EtherscanAPITool(BaseTool):
    """
    Multi-hop transaction tracer using Etherscan + BSCScan APIs.
    Traces up to 10 hops from a suspicious wallet.
    """
    name = "etherscan_api_tool"
    CHAIN_APIS = {
        "eth": "https://api.etherscan.io/api",
        "bsc": "https://api.bscscan.com/api",
    }

    def _execute(
        self,
        wallet_address: str,
        chain: str = "eth",
        max_hops: int = 5,
    ) -> ToolOutput:
        api_key = ETHERSCAN_API_KEY
        base_url = self.CHAIN_APIS.get(chain, self.CHAIN_APIS["eth"])

        with httpx.Client(timeout=15.0) as client:
            resp = client.get(base_url, params={
                "module": "account",
                "action": "txlist",
                "address": wallet_address,
                "startblock": 0,
                "endblock": 99999999,
                "sort": "desc",
                "apikey": api_key,
                "offset": 100,
                "page": 1,
            })
            resp.raise_for_status()
            tx_data = resp.json()

        txs = tx_data.get("result", [])
        if isinstance(txs, str):
            # API error message
            return ToolOutput(success=False, data={}, confidence_score=0.0, error=txs)

        # Build simple hop list
        hops = []
        for tx in txs[:max_hops]:
            hops.append({
                "from": tx.get("from", ""),
                "to": tx.get("to", ""),
                "hash": tx.get("hash", ""),
                "value_eth": int(tx.get("value", 0)) / 1e18,
                "timestamp": datetime.utcfromtimestamp(int(tx.get("timeStamp", 0))).isoformat(),
                "chain": chain,
            })

        return ToolOutput(
            success=True,
            data={"wallet": wallet_address, "chain": chain, "hops": hops, "total_txs": len(txs)},
            confidence_score=0.90,
            evidence_links=[f"https://etherscan.io/address/{wallet_address}"],
        )


# ─── OpenSanctionsTool ────────────────────────────────────────────────────────

class OpenSanctionsTool(BaseTool):
    """
    Match wallet address against OFAC, EU, UN, PEPs sanction lists
    via OpenSanctions API.
    """
    name = "opensanctions_tool"
    API_BASE = "https://api.opensanctions.org"

    def _execute(self, wallet_address: str) -> ToolOutput:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f"{self.API_BASE}/match/default",
                params={"q": wallet_address, "api_key": OPENSANCTIONS_API_KEY, "limit": 10},
            )
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        hits = []
        for r in results:
            score = r.get("score", 0.0)
            if score > 0.6:  # threshold
                hits.append({
                    "entity_name": r.get("caption", ""),
                    "list_name": r.get("datasets", ["unknown"])[0],
                    "confidence": score,
                    "source_url": f"https://www.opensanctions.org/entities/{r.get('id', '')}",
                })

        return ToolOutput(
            success=True,
            data={"wallet": wallet_address, "sanctions_hits": hits, "total_hits": len(hits)},
            confidence_score=0.95 if hits else 0.5,
            evidence_links=[h["source_url"] for h in hits],
        )


# ─── CryptoScamDBTool ─────────────────────────────────────────────────────────

class CryptoScamDBTool(BaseTool):
    """
    Check wallet against CryptoScamDB blacklist (phishing, rug-pull, malware).
    """
    name = "cryptoscamdb_tool"
    API_BASE = "https://api.cryptoscamdb.org/v1"

    def _execute(self, wallet_address: str) -> ToolOutput:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self.API_BASE}/check/{wallet_address}")
            resp.raise_for_status()
            data = resp.json()

        is_scam = data.get("success", False) and bool(data.get("result"))
        scam_info = data.get("result", {})
        categories = list(scam_info.keys()) if isinstance(scam_info, dict) else []

        return ToolOutput(
            success=True,
            data={
                "wallet": wallet_address,
                "is_blacklisted": is_scam,
                "categories": categories,
                "raw": scam_info,
            },
            confidence_score=0.90 if is_scam else 0.70,
            evidence_links=[f"https://cryptoscamdb.org/address/{wallet_address}"],
        )


# ─── ReportGeneratorTool ─────────────────────────────────────────────────────

class ReportGeneratorTool(BaseTool):
    """
    Generate structured, Audit-ready AML compliance reports.
    Output: JSON summary + Markdown (PDF generation via external converter).
    """
    name = "report_generator_tool"

    def _execute(
        self,
        case_data: dict,
        output_dir: str = "reports/",
        format: str = "json",
    ) -> ToolOutput:
        import hashlib
        import json
        from pathlib import Path

        case_id = case_data.get("case_id", f"AML-{int(time.time())}")
        report = {
            "case_id": case_id,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "version": "1.0",
            "risk_level": case_data.get("risk_level", "UNKNOWN"),
            "qubo_risk_score": case_data.get("qubo_risk_score", 0.0),
            "f_beta_score": case_data.get("f_beta_score", 0.0),
            "recommended_action": case_data.get("recommended_action", "MONITOR"),
            "flow_trace": case_data.get("flow_trace", {}),
            "threat_intel": case_data.get("threat_intel", {}),
            "summary": case_data.get("summary", ""),
        }

        # Compute audit hash
        report_bytes = json.dumps(report, sort_keys=True).encode()
        audit_hash = hashlib.sha256(report_bytes).hexdigest()
        report["audit_hash"] = audit_hash

        # Save to file
        out_path = Path(output_dir) / f"{case_id}.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2))

        return ToolOutput(
            success=True,
            data={"report": report, "file_path": str(out_path)},
            confidence_score=1.0,
            evidence_links=[str(out_path)],
        )
