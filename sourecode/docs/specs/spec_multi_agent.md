# Spec: Multi-Agent System (LangGraph & CrewAI Framework)

## Objective
3 AI Agents tự trị phối hợp điều tra giao dịch đáng ngờ được flagged bởi QUBO optimizer.  
Output cuối cùng: báo cáo AML chuẩn quốc tế (SAR-ready), Audit-ready.

**Trigger**: QUBO optimizer trả về `risk_score > 0.85` → Agents được kích hoạt tự động.

## Tech Stack
- **Framework**: CrewAI 0.28+ (orchestration) + LangGraph (complex flows)
- **LLM Backend**: Claude Sonnet (reasoning) / GPT-4o (fallback)
- **Tools**: Custom tool wrappers (xem `src/tools/`)
- **Output format**: Structured JSON → PDF via ReportLab

## Agent Definitions

### Agent 1: Multi-hop Flow Tracer
```python
role    = "Blockchain Flow Tracer"
goal    = "Truy vết dòng tiền multi-hop từ node bị tình nghi qua ≤ 10 hops"
tools   = [GraphQueryTool, EtherscanAPITool]
output  = FlowTraceResult(hops: list[Hop], bridges: list[str], mixers: list[str])
```

### Agent 2: OSINT & KYC Analyst
```python
role    = "Threat Intelligence Analyst"
goal    = "Xác minh thực thể qua OFAC, EU, UN sanctions + CryptoScamDB"
tools   = [OpenSanctionsTool, CryptoScamDBTool]
output  = ThreatIntelResult(sanctions_hits: list[SanctionMatch], scam_score: float)
```

### Agent 3: Compliance Officer (AI)
```python
role    = "Chief Compliance Officer (AI)"
goal    = "Tổng hợp findings → báo cáo AML chuẩn FATF/FinCEN"
tools   = [ReportGeneratorTool]
input   = FlowTraceResult + ThreatIntelResult + QUBO risk_score
output  = ComplianceReport(pdf_url: str, risk_level: str, f_beta_score: float)
```

## Commands
```bash
# Run agents on a single wallet
python -m src.agents.run --wallet 0xABC... --risk-score 0.92

# Test agent pipeline
pytest tests/test_agents.py -v

# Test specific agent
pytest tests/test_agents.py::test_tracer_agent_tornado_cash -v

# Generate sample report
python -m src.agents.run --demo --wallet SAMPLE_ILLICIT_WALLET
```

## Data Contracts

### Input to Crew
```python
@dataclass
class AgentInput:
    wallet_address: str          # EIP-55 checksummed
    qubo_risk_score: float       # 0.0 – 1.0
    qubo_flagged_nodes: list[str]
    trace_id: str                # Pipeline trace ID
```

### Tool Output Contract
```python
@dataclass
class ToolOutput:
    success: bool
    data: dict
    confidence_score: float      # 0.0 – 1.0
    evidence_links: list[str]    # Source URLs
    error: str | None
```

### Final Report Schema
```python
@dataclass
class ComplianceReport:
    case_id: str
    timestamp: datetime
    risk_level: str              # "HIGH" | "MEDIUM" | "LOW"
    f_beta_score: float          # β=0.5
    flow_trace: FlowTraceResult
    threat_intel: ThreatIntelResult
    recommended_action: str      # "FREEZE" | "MONITOR" | "CLEAR"
    pdf_url: str
    audit_hash: str              # SHA-256 of report content
```

## Testing Strategy
- **Unit**: Mock tất cả API calls, test agent logic isolation
- **Integration**: Real Elliptic dataset wallets (known illicit)
- **Acceptance tests**:
  - Known Tornado Cash wallet → FlowTraceResult.mixers không rỗng
  - OFAC-listed wallet → ThreatIntelResult.sanctions_hits không rỗng
  - ComplianceReport.risk_level == "HIGH" với risk_score > 0.85

## Boundaries
- **Always do**: Log all agent actions với trace_id, validate tool outputs, retry on API failure (3 attempts, exponential backoff)
- **Ask first**: Thêm Agent mới, thay đổi LLM provider, sửa report schema
- **Never do**: Hardcode wallet addresses trong tests, bypass tool output validation, skip audit_hash generation

## Success Criteria
- [ ] Tracer Agent map được ≥ 5 hops qua Tornado Cash trong < 30s
- [ ] OSINT Agent match đúng 100% wallets trong OFAC test set
- [ ] Compliance Report PDF được tạo trong < 60s sau khi nhận AgentInput
- [ ] Stress test: 100 concurrent wallets hoàn thành trong < 5 phút
- [ ] F-β score (β=0.5) trên test set > 0.90

## Open Questions
- LLM provider nào cho production? (Claude vs GPT-4o cost analysis)
- PDF template chuẩn FATF hay tự thiết kế?
