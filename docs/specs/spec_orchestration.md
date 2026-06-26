# Spec: Core Orchestration Layer (Quapp Platform)

## Objective
Quapp.cloud đóng vai trò middleware điều phối bất đồng bộ giữa:
- **Classical HPC** (8 workers) — xử lý dữ liệu blockchain thô
- **Quantum Backend** (Qamelion/Quandela) — chạy QUBO optimization
- **Multi-Agent System** (CrewAI) — nhận kết quả quantum, tự động điều tra

**User story:** Khi một địa chỉ ví mới được nạp vào hệ thống, pipeline tự động chạy end-to-end mà không cần can thiệp thủ công.

## Tech Stack
- **Orchestration**: Quapp.cloud v1.0 (YAML config)
- **Async runtime**: Python asyncio + Celery (task queue)
- **HPC workers**: 8 classical workers (Docker containers)
- **Quantum backends**: Qamelion Emulator + Perceval SDK

## Commands
```bash
# Start orchestrator
docker-compose up -d quapp-orchestrator

# Run pipeline for a wallet
python -m src.pipeline.run --wallet 0xABC... --mode hybrid

# Check task status
python -m src.pipeline.status --task-id <uuid>

# Run tests
pytest tests/test_orchestration.py -v

# Lint
ruff check src/ && mypy src/
```

## Project Structure
```
src/
  pipeline/
    run.py          → CLI entrypoint + pipeline trigger
    orchestrator.py → Quapp YAML loader + task dispatcher
    status.py       → Task status polling
  data/
    dune_extractor.py
    elliptic_loader.py
    opensanctions_client.py
    cryptoscamdb_client.py
  quantum/
    hybrid_optimizer.py   → HybridQuantumOptimizer class
    graph_to_qubo.py      → Graph → QUBO matrix converter
  agents/
    multi_agent_crew.py
  tools/
    graph_query_tool.py
    etherscan_tool.py
    opensanctions_tool.py
    cryptoscamdb_tool.py
    report_generator_tool.py
config/
  quapp_hybrid_orchestrator.yaml
tests/
  test_orchestration.py
  test_data_pipeline.py
  test_qubo_mapping.py
  test_agents.py
```

## Code Style
```python
# Naming: snake_case functions, PascalCase classes
# Type hints: required on all public functions
# Docstrings: Google-style

async def dispatch_pipeline(wallet_address: str, mode: str = "hybrid") -> PipelineResult:
    """
    Dispatch AML analysis pipeline for a given wallet.

    Args:
        wallet_address: Ethereum-compatible wallet address (checksummed)
        mode: "hybrid" | "classical" | "quantum_sim"

    Returns:
        PipelineResult with task_id, status, and result_url
    """
    ...
```

## Testing Strategy
- **Framework**: pytest + pytest-asyncio
- **Location**: `tests/` directory, mirrors `src/` structure
- **Coverage target**: ≥ 80% on `src/pipeline/` and `src/quantum/`
- **Test levels**:
  - Unit: mock external APIs, test logic isolation
  - Integration: real Elliptic dataset, mock quantum backend
  - E2E: known illicit wallet → correct AML report

## Boundaries
- **Always do**: Validate wallet addresses (EIP-55 checksum), log all pipeline events as JSON, use `.env` for API keys
- **Ask first**: Change Quapp YAML schema, add new quantum backend, modify HPC worker count
- **Never do**: Commit real API keys, skip input validation, disable fallback_to_simulator in production

## Success Criteria
- [ ] Pipeline dispatches async task for a wallet address in < 1s
- [ ] HPC + Quantum results merged correctly before Agent handoff
- [ ] `fallback_to_simulator: true` works when QaaS unavailable
- [ ] All pipeline events logged as structured JSON with `trace_id`

## Open Questions
- Quapp.cloud API key format? (cần team confirm)
- HPC worker autoscaling threshold? (hiện hardcode 8)
