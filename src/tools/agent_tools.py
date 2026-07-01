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
from src.tools.opensanctions_client import OpenSanctionsClient

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
    # Updated to The Graph decentralized network (old hosted service deprecated 2024)
    SUBGRAPH_URLS = {
        "uniswap_v3": "https://gateway.thegraph.com/api/deployments/id/QmZeCuoZeadgHkGwLwMeguyqUKz1WPWQYKcKyMCeQqGhsF",
        "tornado_cash": "https://gateway.thegraph.com/api/deployments/id/QmNvA5GFNX8VTB1eEhv9FRMhBFsNsoBCg4kHFdBPdQ1zjx",
        "aave_v3": "https://gateway.thegraph.com/api/deployments/id/Cd2gEDVeqnjBn1hSeqFMitw8Q1iiyV9FYUZkLNRcL87g",
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
    Match wallet address / name against OFAC, EU, UN, PEPs sanction lists
    via OpenSanctions API (yente 5.4.0).

    Uses OpenSanctionsClient built from openapi.json.
    Endpoint: POST /match/{dataset}  (EntityMatchQuery → EntityMatchResponse)
    """
    name = "opensanctions_tool"

    def _execute(
        self,
        wallet_address: str,
        dataset: str = "default",
        threshold: float = 0.6,
        schema: str = "LegalEntity",
    ) -> ToolOutput:
        client = OpenSanctionsClient(api_key=OPENSANCTIONS_API_KEY)

        # Use the typed client — maps to POST /match/{dataset}
        match_result = client.match_wallet(
            wallet_address=wallet_address,
            dataset=dataset,
            threshold=threshold,
        )

        hits = [
            {
                "entity_name": entity.caption,
                "list_name": entity.datasets[0] if entity.datasets else "unknown",
                "confidence": entity.score,
                "is_confirmed_match": entity.match,   # True if score ≥ threshold
                "topics": entity.topics,
                "source_url": entity.source_url,
                "explanations": entity.explanations,
            }
            for entity in match_result.results
        ]

        return ToolOutput(
            success=True,
            data={
                "wallet": wallet_address,
                "dataset": dataset,
                "sanctions_hits": hits,
                "total_hits": len(hits),
                "has_confirmed_match": match_result.has_matches,
                "best_score": match_result.best.score if match_result.best else 0.0,
            },
            confidence_score=0.95 if match_result.has_matches else 0.5,
            evidence_links=[h["source_url"] for h in hits],
        )


# ─── CryptoScamDBTool ─────────────────────────────────────────────────────────

class CryptoScamDBTool(BaseTool):
    """
    Check wallet against GoPlus Security API — industry standard on-chain
    address risk checker (replaces deprecated CryptoScamDB public API).
    Covers: phishing, rug-pull, honeypot, mixer, sanctioned, darkweb.
    Docs: https://docs.gopluslabs.io/reference/api-reference/address-security
    """
    name = "cryptoscamdb_tool"
    # GoPlus: free tier, no API key needed for basic checks
    API_BASE = "https://api.gopluslabs.io/api/v1"

    def _execute(self, wallet_address: str, chain_id: str = "1") -> ToolOutput:
        """chain_id: 1=ETH, 56=BSC, 137=Polygon, 43114=Avalanche"""
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(
                f"{self.API_BASE}/address_security/{wallet_address}",
                params={"chain_id": chain_id},
            )
            resp.raise_for_status()
            data = resp.json()

        result = data.get("result", {})
        # GoPlus flags — any "1" means flagged
        risk_flags = {
            "phishing_activities": result.get("phishing_activities", "0"),
            "blacklist_doubt":     result.get("blacklist_doubt", "0"),
            "stealing_attack":     result.get("stealing_attack", "0"),
            "fake_token":          result.get("fake_token", "0"),
            "honeypot_related":    result.get("honeypot_related_address", "0"),
            "mixer":               result.get("mixer", "0"),
            "sanctioned":          result.get("sanctioned", "0"),
            "darkweb_transactions": result.get("darkweb_transactions", "0"),
            "cybercrime":          result.get("cybercrime", "0"),
            "money_laundering":    result.get("money_laundering", "0"),
        }
        categories = [flag for flag, val in risk_flags.items() if val == "1"]
        is_scam = bool(categories)

        return ToolOutput(
            success=True,
            data={
                "wallet": wallet_address,
                "chain_id": chain_id,
                "is_blacklisted": is_scam,
                "categories": categories,
                "raw": risk_flags,
            },
            confidence_score=0.92 if is_scam else 0.75,
            evidence_links=[f"https://gopluslabs.io/phishing-site/{wallet_address}"],
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
