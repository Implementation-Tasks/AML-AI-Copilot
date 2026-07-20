"""
AML AI Copilot — FastAPI Backend Server
Run: py314 server.py
Then open: demo/index.html in your browser
"""
import logging
import uuid

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="AML AI Copilot API", version="1.0.0")

# Allow browser to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the demo UI at /demo
app.mount("/demo", StaticFiles(directory="DEMOCORE"), name="demo")


# ── Request/Response models ───────────────────────────────────────────────────

class ScreenRequest(BaseModel):
    wallet_address: str
    qubo_risk_score: float = 0.85
    dataset: str = "default"


class BenchmarkRequest(BaseModel):
    demo: bool = True


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return FileResponse("DEMOCORE/04_prototype.html")


@app.get("/health")
def health():
    return {"status": "ok", "service": "AML AI Copilot"}


@app.post("/api/screen")
def screen_wallet(req: ScreenRequest):
    """Run the full 3-agent AML pipeline on a wallet address."""
    from src.models import AgentInput
    from src.agents.multi_agent_crew import run_aml_crew

    report = run_aml_crew(AgentInput(
        wallet_address=req.wallet_address,
        qubo_risk_score=req.qubo_risk_score,
        qubo_flagged_nodes=[req.wallet_address],
        trace_id=str(uuid.uuid4()),
    ))

    return {
        "case_id":            report.case_id,
        "wallet_address":     report.wallet_address,
        "risk_level":         report.risk_level,
        "recommended_action": report.recommended_action,
        "qubo_risk_score":    report.qubo_risk_score,
        "f_beta_score":       report.f_beta_score,
        "precision":          report.precision,
        "recall":             report.recall,
        "audit_hash":         report.audit_hash,
        "report_file":        report.pdf_url,
        "flow_trace": {
            "total_hops":      report.flow_trace.total_hops,
            "chains_involved": report.flow_trace.chains_involved,
            "mixers_used":     report.flow_trace.mixers_used,
            "bridges_used":    report.flow_trace.bridges_used,
        },
        "threat_intel": {
            "sanctions_hits": [
                {
                    "entity_name": h.entity_name,
                    "list_name":   h.list_name,
                    "confidence":  h.confidence,
                    "source_url":  h.source_url,
                }
                for h in report.threat_intel.sanctions_hits
            ],
            "scam_score":      report.threat_intel.scam_score,
            "scam_categories": report.threat_intel.scam_categories,
        },
        "summary": report.summary,
    }


@app.post("/api/benchmark")
def run_benchmark(req: BenchmarkRequest):
    """Run the QUBO benchmark suite."""
    import subprocess, sys, json, re

    cmd = [sys.executable, "-m", "src.quantum.benchmark"]
    if req.demo:
        cmd.append("--demo")

    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "success":  result.returncode == 0,
        "output":   result.stdout,
        "errors":   result.stderr,
    }


def _get_backend_from_env() -> str:
    """Read backend from .env file (set by launcher.py)"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    backend = os.getenv("QUANTUM_BACKEND", "classical")
    
    # Validate backend
    valid_backends = ["classical", "quandela", "qudora"]
    if backend not in valid_backends:
        print(f"  ⚠️  Invalid backend: {backend}. Fallback to classical.")
        backend = "classical"
    
    # Check SDK availability and warn if missing
    if backend == "quandela":
        try:
            import perceval  # noqa
            print(f"  ✅ Perceval: OK")
        except ImportError:
            print("  ⚠️  perceval-quandela not installed! Fallback to classical.")
            backend = "classical"
    
    elif backend == "qudora":
        try:
            import qudora_sdk  # noqa
            print(f"  ✅ Qudora SDK: OK")
        except ImportError:
            print("  ⚠️  qudora-sdk not installed! Fallback to classical.")
            backend = "classical"
    
    return backend


def _free_port(port: int):
    """Kill any process holding the port before binding."""
    import subprocess, platform
    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    pid = line.strip().split()[-1]
                    subprocess.run(["taskkill", "/F", "/PID", pid],
                                   capture_output=True)
                    print(f"  🔪 Freed port {port} (PID {pid})")
        else:
            subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True)
    except Exception as e:
        print(f"  ⚠️  Could not free port {port}: {e}")


if __name__ == "__main__":
    PORT = 7860
    backend = _get_backend_from_env()
    _free_port(PORT)          # Automatically free old port
    import time; time.sleep(0.5)  # Wait for OS release
    print("═" * 60)
    print(f"  🚀 Starting AML AI Copilot Server...")
    print(f"  🔬 Quantum Backend : {backend.upper()}")
    print(f"  🌐 UI              : http://localhost:{PORT}")
    print(f"  📡 API             : http://localhost:{PORT}/api/screen")
    print(f"  📖 Docs            : http://localhost:{PORT}/docs")
    print(f"\n  💡 Tip: Use launcher.py to change the backend")
    print("═" * 60 + "\n")
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, reload=False)

