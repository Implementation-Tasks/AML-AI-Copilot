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

# Serve the demo UI at /
app.mount("/demo", StaticFiles(directory="demo"), name="demo")


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
    return FileResponse("demo/index.html")


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


if __name__ == "__main__":
    print("\n===  AML AI Copilot Server starting...")
    print("   UI  -> http://localhost:8000")
    print("   API -> http://localhost:8000/api/screen")
    print("   Docs-> http://localhost:8000/docs\n")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
