"""
Test Suite: Multi-Agent AML Crew
Skill: test-driven-development + debugging-and-error-recovery
"""
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.models import AgentInput, FlowTraceResult, Hop, SanctionMatch, ThreatIntelResult, ToolOutput
from src.agents.multi_agent_crew import (
    run_aml_crew,
    run_compliance_officer,
    run_flow_tracer,
    run_osint_analyst,
)


# ─── Test Data ────────────────────────────────────────────────────────────────

KNOWN_ILLICIT_WALLET = "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b"  # Tornado Cash
KNOWN_CLEAN_WALLET = "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B"   # Vitalik (safe)

SAMPLE_AGENT_INPUT = AgentInput(
    wallet_address=KNOWN_ILLICIT_WALLET,
    qubo_risk_score=0.92,
    qubo_flagged_nodes=[KNOWN_ILLICIT_WALLET],
    trace_id=str(uuid.uuid4()),
)

SAMPLE_FLOW_TRACE = FlowTraceResult(
    origin_wallet=KNOWN_ILLICIT_WALLET,
    hops=[
        Hop(
            from_wallet=KNOWN_ILLICIT_WALLET,
            to_wallet="0xABCD1234",
            tx_hash="0xTX1",
            amount_usd=50_000,
            chain="eth",
            timestamp=datetime.now(timezone.utc),
            via_mixer=True,
        )
    ],
    bridges_used=["ETH→BSC Bridge"],
    mixers_used=["Tornado Cash"],
    total_hops=1,
    chains_involved=["eth", "bsc"],
)

SAMPLE_THREAT_INTEL = ThreatIntelResult(
    wallet_address=KNOWN_ILLICIT_WALLET,
    sanctions_hits=[
        SanctionMatch(
            wallet_address=KNOWN_ILLICIT_WALLET,
            list_name="OFAC_SDN",
            entity_name="Lazarus Group",
            confidence=0.95,
            source_url="https://www.opensanctions.org/entities/test",
        )
    ],
    scam_score=0.88,
    scam_categories=["phishing", "malware"],
    sources_checked=["OpenSanctions", "CryptoScamDB"],
)


# ─── Flow Tracer Tests ────────────────────────────────────────────────────────

class TestFlowTracerAgent:

    @patch("src.agents.multi_agent_crew.EtherscanAPITool")
    @patch("src.agents.multi_agent_crew.GraphQueryTool")
    def test_returns_flow_trace_result(self, mock_graph, mock_etherscan):
        """Flow tracer should return FlowTraceResult regardless of API data."""
        mock_tool = MagicMock()
        mock_tool.run.return_value = ToolOutput(
            success=True,
            data={"hops": [], "total_txs": 0},
            confidence_score=0.8,
        )
        mock_etherscan.return_value = mock_tool
        mock_graph.return_value = mock_tool

        result = run_flow_tracer(KNOWN_ILLICIT_WALLET, "trace-123")
        assert isinstance(result, FlowTraceResult)
        assert result.origin_wallet == KNOWN_ILLICIT_WALLET

    @patch("src.agents.multi_agent_crew.EtherscanAPITool")
    @patch("src.agents.multi_agent_crew.GraphQueryTool")
    def test_detects_tornado_cash(self, mock_graph, mock_etherscan):
        """Should set via_mixer=True when Tornado Cash activity detected."""
        mock_eth_tool = MagicMock()
        mock_eth_tool.run.return_value = ToolOutput(
            success=True,
            data={
                "hops": [{
                    "from": KNOWN_ILLICIT_WALLET,
                    "to": "0xABCD",
                    "hash": "0xTX",
                    "value_eth": 1.0,
                    "timestamp": "2024-01-01T00:00:00",
                }],
                "total_txs": 1,
            },
            confidence_score=0.9,
        )
        mock_tornado_tool = MagicMock()
        mock_tornado_tool.run.return_value = ToolOutput(
            success=True,
            data={"count": 5, "swaps": []},  # count > 0 = Tornado activity
            confidence_score=0.9,
        )
        mock_etherscan.return_value = mock_eth_tool
        mock_graph.return_value = mock_tornado_tool

        result = run_flow_tracer(KNOWN_ILLICIT_WALLET, "trace-456")
        assert "Tornado Cash" in result.mixers_used

    @patch("src.agents.multi_agent_crew.EtherscanAPITool")
    @patch("src.agents.multi_agent_crew.GraphQueryTool")
    def test_api_failure_returns_empty_trace(self, mock_graph, mock_etherscan):
        """On API failure, should return empty FlowTraceResult (not raise)."""
        mock_tool = MagicMock()
        mock_tool.run.return_value = ToolOutput(
            success=False, data={}, confidence_score=0.0, error="API Error"
        )
        mock_etherscan.return_value = mock_tool
        mock_graph.return_value = mock_tool

        result = run_flow_tracer(KNOWN_ILLICIT_WALLET, "trace-789")
        assert isinstance(result, FlowTraceResult)
        assert result.total_hops == 0


# ─── OSINT Analyst Tests ──────────────────────────────────────────────────────

class TestOSINTAnalystAgent:

    @patch("src.agents.multi_agent_crew.OpenSanctionsTool")
    @patch("src.agents.multi_agent_crew.CryptoScamDBTool")
    def test_returns_threat_intel_result(self, mock_scam, mock_sanctions):
        mock_tool = MagicMock()
        mock_tool.run.return_value = ToolOutput(
            success=True,
            data={"sanctions_hits": [], "is_blacklisted": False, "categories": []},
            confidence_score=0.5,
        )
        mock_sanctions.return_value = mock_tool
        mock_scam.return_value = mock_tool

        result = run_osint_analyst(KNOWN_CLEAN_WALLET)
        assert isinstance(result, ThreatIntelResult)
        assert result.wallet_address == KNOWN_CLEAN_WALLET

    @patch("src.agents.multi_agent_crew.OpenSanctionsTool")
    @patch("src.agents.multi_agent_crew.CryptoScamDBTool")
    def test_detects_ofac_match(self, mock_scam, mock_sanctions):
        mock_sanctions_tool = MagicMock()
        mock_sanctions_tool.run.return_value = ToolOutput(
            success=True,
            data={
                "sanctions_hits": [{
                    "list_name": "OFAC_SDN",
                    "entity_name": "Lazarus Group",
                    "confidence": 0.95,
                    "source_url": "https://opensanctions.org/test",
                }],
            },
            confidence_score=0.95,
        )
        mock_scam_tool = MagicMock()
        mock_scam_tool.run.return_value = ToolOutput(
            success=True,
            data={"is_blacklisted": False, "categories": []},
            confidence_score=0.5,
        )
        mock_sanctions.return_value = mock_sanctions_tool
        mock_scam.return_value = mock_scam_tool

        result = run_osint_analyst(KNOWN_ILLICIT_WALLET)
        assert len(result.sanctions_hits) == 1
        assert result.sanctions_hits[0].list_name == "OFAC_SDN"


# ─── Compliance Officer Tests ─────────────────────────────────────────────────

class TestComplianceOfficerAgent:

    @patch("src.agents.multi_agent_crew.ReportGeneratorTool")
    def test_high_risk_sanctions_hit(self, mock_report_tool):
        """Wallet with OFAC hit should be classified HIGH RISK and FREEZE."""
        mock_tool = MagicMock()
        mock_tool.run.return_value = ToolOutput(
            success=True,
            data={"report": {"audit_hash": "abc123"}, "file_path": "/reports/test.json"},
            confidence_score=1.0,
        )
        mock_report_tool.return_value = mock_tool

        report = run_compliance_officer(
            SAMPLE_AGENT_INPUT, SAMPLE_FLOW_TRACE, SAMPLE_THREAT_INTEL
        )
        assert report.risk_level == "HIGH"
        assert report.recommended_action == "FREEZE"
        assert report.f_beta_score > 0.0
        assert report.case_id.startswith("AML-")

    @patch("src.agents.multi_agent_crew.ReportGeneratorTool")
    def test_clean_wallet_low_risk(self, mock_report_tool):
        """Clean wallet with no sanctions should be LOW/CLEAR."""
        mock_tool = MagicMock()
        mock_tool.run.return_value = ToolOutput(
            success=True,
            data={"report": {"audit_hash": "def456"}, "file_path": "/reports/clean.json"},
            confidence_score=1.0,
        )
        mock_report_tool.return_value = mock_tool

        clean_input = AgentInput(
            wallet_address=KNOWN_CLEAN_WALLET,
            qubo_risk_score=0.10,
            qubo_flagged_nodes=[],
            trace_id="clean-trace",
        )
        clean_flow = FlowTraceResult(
            origin_wallet=KNOWN_CLEAN_WALLET,
            hops=[], bridges_used=[], mixers_used=[],
            total_hops=0, chains_involved=["eth"],
        )
        clean_intel = ThreatIntelResult(
            wallet_address=KNOWN_CLEAN_WALLET,
            sanctions_hits=[], scam_score=0.0,
            scam_categories=[], sources_checked=["OpenSanctions", "CryptoScamDB"],
        )
        report = run_compliance_officer(clean_input, clean_flow, clean_intel)
        assert report.risk_level in ["LOW", "MEDIUM"]
        assert report.recommended_action in ["CLEAR", "MONITOR"]

    @patch("src.agents.multi_agent_crew.ReportGeneratorTool")
    def test_report_has_audit_hash(self, mock_report_tool):
        """Every report must have an audit hash for tamper-evidence."""
        mock_tool = MagicMock()
        mock_tool.run.return_value = ToolOutput(
            success=True,
            data={"report": {"audit_hash": "sha256_hash_abc"}, "file_path": "/reports/test.json"},
            confidence_score=1.0,
        )
        mock_report_tool.return_value = mock_tool

        report = run_compliance_officer(SAMPLE_AGENT_INPUT, SAMPLE_FLOW_TRACE, SAMPLE_THREAT_INTEL)
        assert report.audit_hash is not None


# ─── End-to-End Crew Test ─────────────────────────────────────────────────────

class TestAMLCrewE2E:

    @patch("src.agents.multi_agent_crew.ReportGeneratorTool")
    @patch("src.agents.multi_agent_crew.CryptoScamDBTool")
    @patch("src.agents.multi_agent_crew.OpenSanctionsTool")
    @patch("src.agents.multi_agent_crew.GraphQueryTool")
    @patch("src.agents.multi_agent_crew.EtherscanAPITool")
    def test_full_crew_pipeline(
        self, mock_eth, mock_graph, mock_sanctions, mock_scam, mock_report
    ):
        """Complete pipeline: AgentInput → ComplianceReport."""
        # Mock all external APIs
        success_output = ToolOutput(
            success=True,
            data={"hops": [], "total_txs": 0, "sanctions_hits": [], "is_blacklisted": False, "categories": []},
            confidence_score=0.8,
        )
        report_output = ToolOutput(
            success=True,
            data={"report": {"audit_hash": "final_hash"}, "file_path": "/reports/e2e.json"},
            confidence_score=1.0,
        )
        for mock in [mock_eth, mock_graph, mock_sanctions, mock_scam]:
            mock.return_value.run.return_value = success_output
        mock_report.return_value.run.return_value = report_output

        report = run_aml_crew(SAMPLE_AGENT_INPUT)

        assert report is not None
        assert report.wallet_address == KNOWN_ILLICIT_WALLET
        assert report.case_id.startswith("AML-")
        assert report.risk_level in ["HIGH", "MEDIUM", "LOW"]
        assert report.recommended_action in ["FREEZE", "MONITOR", "CLEAR"]
        assert 0.0 <= report.f_beta_score <= 1.0
