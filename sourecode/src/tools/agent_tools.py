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
from datetime import datetime, timezone
from typing import Any, Optional

import httpx

from src.config import (
    ETHERSCAN_API_KEY,
    OPENSANCTIONS_API_KEY,
)
from src.models import ToolOutput
from src.tools.opensanctions_client import OpenSanctionsClient
from src.data.price_oracle import convert_native_to_usd

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
    Multi-hop transaction tracer using Etherscan / BSCScan / TronScan APIs.
    Supports ETH, BSC, and Tron (TRC-20 USDT — critical for SEA laundering).
    Includes pagination for wallets with >100 transactions.
    """
    name = "etherscan_api_tool"
    CHAIN_APIS = {
        "eth":  "https://api.etherscan.io/api",
        "bsc":  "https://api.bscscan.com/api",
        "tron": "https://apilist.tronscanapi.com/api/transaction",  # TronScan public API
    }
    EXPLORER_URLS = {
        "eth":  "https://etherscan.io/address/{}",
        "bsc":  "https://bscscan.com/address/{}",
        "tron": "https://tronscan.org/#/address/{}",
    }
    # Native coin per chain (for USD conversion)
    CHAIN_COINS = {"eth": "eth", "bsc": "bnb", "tron": "trx"}

    def _execute(
        self,
        wallet_address: str,
        chain: str = "eth",
        max_hops: int = 5,
    ) -> ToolOutput:
        if chain == "tron":
            return self._execute_tron(wallet_address, max_hops)
        return self._execute_evm(wallet_address, chain, max_hops)

    def _execute_evm(self, wallet_address: str, chain: str, max_hops: int) -> ToolOutput:
        """Fetch EVM chain (ETH/BSC) transactions with pagination."""
        api_key  = ETHERSCAN_API_KEY
        base_url = self.CHAIN_APIS.get(chain, self.CHAIN_APIS["eth"])
        coin     = self.CHAIN_COINS.get(chain, "eth")

        all_txs: list[dict] = []
        page = 1
        while len(all_txs) < max(max_hops * 10, 100):
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(base_url, params={
                    "module":     "account",
                    "action":     "txlist",
                    "address":    wallet_address,
                    "startblock": 0,
                    "endblock":   99999999,
                    "sort":       "desc",
                    "apikey":     api_key,
                    "offset":     100,
                    "page":       page,
                })
                resp.raise_for_status()
                tx_data = resp.json()

            page_txs = tx_data.get("result", [])
            if isinstance(page_txs, str):
                # API error string (e.g. rate limit, invalid key)
                if page == 1:
                    return ToolOutput(success=False, data={}, confidence_score=0.0, error=page_txs)
                break
            if not page_txs:
                break  # No more pages

            all_txs.extend(page_txs)
            page += 1
            time.sleep(0.2)  # Respect 5 req/s free-tier limit

        # Build hop list with live USD conversion (no hard-code!)
        hops = []
        for tx in all_txs[:max_hops]:
            value_native = int(tx.get("value", 0)) / 1e18
            hops.append({
                "from":      tx.get("from", ""),
                "to":        tx.get("to", ""),
                "hash":      tx.get("hash", ""),
                "value_native": value_native,
                "value_usd":    convert_native_to_usd(value_native, coin),  # ← Live price
                "timestamp": datetime.fromtimestamp(
                    int(tx.get("timeStamp", 0)), timezone.utc
                ).isoformat(),
                "chain": chain,
            })

        explorer_url = self.EXPLORER_URLS.get(chain, "").format(wallet_address)
        return ToolOutput(
            success=True,
            data={
                "wallet":    wallet_address,
                "chain":     chain,
                "hops":      hops,
                "total_txs": len(all_txs),
            },
            confidence_score=0.90,
            evidence_links=[explorer_url],
        )

    def _execute_tron(self, wallet_address: str, max_hops: int) -> ToolOutput:
        """Fetch Tron TRC-20 transactions (critical for USDT laundering in SEA)."""
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(
                    "https://apilist.tronscanapi.com/api/transaction",
                    params={
                        "address": wallet_address,
                        "limit":   min(max_hops * 5, 50),
                        "start":   0,
                        "sort":    "-timestamp",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            raw_txs = data.get("data", [])
            hops = []
            for tx in raw_txs[:max_hops]:
                value_trx = float(tx.get("amount", 0)) / 1_000_000  # SUN → TRX
                hops.append({
                    "from":         tx.get("ownerAddress", ""),
                    "to":           tx.get("toAddress", ""),
                    "hash":         tx.get("hash", ""),
                    "value_native": value_trx,
                    "value_usd":    convert_native_to_usd(value_trx, "trx"),
                    "timestamp":    datetime.fromtimestamp(
                        int(tx.get("timestamp", 0)) / 1000, timezone.utc
                    ).isoformat(),
                    "chain": "tron",
                })

            return ToolOutput(
                success=True,
                data={
                    "wallet":    wallet_address,
                    "chain":     "tron",
                    "hops":      hops,
                    "total_txs": data.get("total", len(raw_txs)),
                },
                confidence_score=0.85,
                evidence_links=[f"https://tronscan.org/#/address/{wallet_address}"],
            )
        except Exception as exc:
            return ToolOutput(
                success=False,
                data={},
                confidence_score=0.0,
                error=f"Tron API error: {exc}",
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
            "generated_at": datetime.now(timezone.utc).isoformat() + "Z",
            "version": "1.0",
            "risk_level": case_data.get("risk_level", "UNKNOWN"),
            "qubo_risk_score": case_data.get("qubo_risk_score", 0.0),
            "f_beta_score": case_data.get("f_beta_score", 0.0),
            "recommended_action": case_data.get("recommended_action", "MONITOR"),
            "flow_trace": case_data.get("flow_trace", {}),
            "threat_intel": case_data.get("threat_intel", {}),
            "travel_rule_violations": case_data.get("travel_rule_violations", []),
            "summary": case_data.get("summary", ""),
        }

        # Compute audit hash
        report_bytes = json.dumps(report, sort_keys=True).encode()
        audit_hash = hashlib.sha256(report_bytes).hexdigest()
        report["audit_hash"] = audit_hash

        # Save to file
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        
        json_path = out_path / f"{case_id}.json"
        json_path.write_text(json.dumps(report, indent=2))
        
        # Generate PDF (SAR format)
        pdf_path = out_path / f"{case_id}.pdf"
        pdf_generated = False
        try:
            self._generate_pdf(report, str(pdf_path))
            pdf_generated = True
        except ImportError:
            logger.warning("[ReportGenerator] reportlab not installed; skipping PDF generation.")
        except Exception as e:
            logger.warning(f"[ReportGenerator] PDF generation failed: {e}")

        final_path = pdf_path if pdf_generated else json_path

        return ToolOutput(
            success=True,
            data={"report": report, "file_path": str(final_path)},
            confidence_score=1.0,
            evidence_links=[str(final_path)],
        )

    def _generate_pdf(self, report: dict, output_path: str):
        """Generate SAR-ready PDF following FinCEN/MAS format."""
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(output_path, pagesize=A4)
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        h2 = styles['Heading2']
        normal = styles['Normal']
        
        elements = []
        
        # Header
        elements.append(Paragraph(f"Suspicious Activity Report (SAR) - {report['case_id']}", title_style))
        elements.append(Spacer(1, 12))
        
        # Metadata
        elements.append(Paragraph(f"<b>Generated At:</b> {report['generated_at']}", normal))
        elements.append(Paragraph(f"<b>Audit Hash:</b> {report['audit_hash']}", normal))
        elements.append(Spacer(1, 12))
        
        # Risk Summary
        elements.append(Paragraph("1. Risk Assessment", h2))
        risk_color = colors.red if report['risk_level'] == 'HIGH' else (colors.orange if report['risk_level'] == 'MEDIUM' else colors.green)
        
        data = [
            ["Risk Level", "QUBO Risk Score", "F-Beta Score", "Recommended Action"],
            [report['risk_level'], f"{report['qubo_risk_score']:.2f}", f"{report['f_beta_score']:.2f}", report['recommended_action']]
        ]
        t = Table(data, colWidths=[100, 100, 100, 150])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (0,1), risk_color),
            ('TEXTCOLOR', (0,1), (0,1), colors.whitesmoke if report['risk_level'] != 'LOW' else colors.black),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))
        
        # Summary Text
        elements.append(Paragraph("2. Executive Summary", h2))
        elements.append(Paragraph(report['summary'], normal))
        elements.append(Spacer(1, 12))
        
        # Travel Rule Violations
        elements.append(Paragraph("3. FATF Travel Rule Violations (R.16)", h2))
        violations = report.get('travel_rule_violations', [])
        if violations:
            v_data = [["Tx Hash", "Amount (USD)", "Originator", "Beneficiary"]]
            for v in violations:
                v_data.append([
                    v.get('tx_hash', '')[:10] + '...',
                    f"${v.get('amount_usd', 0):.2f}",
                    v.get('originator', '')[:15] + '...',
                    v.get('beneficiary', '')[:15] + '...'
                ])
            vt = Table(v_data, colWidths=[100, 80, 130, 130])
            vt.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (1,1), (1,-1), 'RIGHT'),
            ]))
            elements.append(vt)
        else:
            elements.append(Paragraph("No FATF Travel Rule violations detected.", normal))
            
        doc.build(elements)
