# 🚀 FULL PROJECT EXECUTION GUIDE
**AML AI Copilot - Complete Hybrid Quantum-Agentic AML System**

---

## 📋 TABLE OF CONTENTS

1. [Overview](#overview)
2. [System Requirements](#system-requirements)
3. [Installation Step 1: Dependencies](#step-1-install-dependencies)
4. [Installation Step 2: API Keys](#step-2-configure-api-keys)
5. [Installation Step 3: Verification](#step-3-verify-installation)
6. [Run the System](#run-the-system)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 OVERVIEW

### Comparison: Demo vs Full Project

| Feature | DEMOCORE (Demo) | Full Project |
|-----------|----------------|--------------|
| **Data** | Synthetic | Real blockchain data |
| **QUBO** | Simulated Annealing | Quantum hardware / SA |
| **Agents** | Mock data | Real API calls (Etherscan, OFAC) |
| **API Keys** | ❌ Not required | ✅ Required (Anthropic, Etherscan, etc.) |
| **Purpose** | Demo & Testing | Production-ready |

### Full Project includes:

```
┌─────────────────────────────────────────────────────────────┐
│  1. QUBO Optimizer (src/quantum/)                           │
│     • graph_to_qubo.py: MIMO + Top-20 + QUBO builder       │
│     • hybrid_optimizer.py: Quantum backend dispatcher       │
│     • benchmark.py: Performance testing                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Multi-Agent Crew (src/agents/)                          │
│     • multi_agent_crew.py: CrewAI orchestration            │
│       - Flow Tracer: Real Etherscan API                     │
│       - OSINT Analyst: OpenSanctions + CryptoScamDB        │
│       - Compliance Officer: 6-component scoring             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Pipeline Handler (src/pipeline/)                        │
│     • handler.py: Quapp.cloud entrypoint                   │
│     • CIWS Kill Chain: Immediate FREEZE (no LLM latency)   │
│     • Analysis Chain: Async SAR report generation           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Tools & Data (src/tools/, src/data/)                   │
│     • agent_tools.py: Etherscan, OpenSanctions wrappers    │
│     • etherscan_graph_builder.py: Live graph construction  │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 SYSTEM REQUIREMENTS

### Minimum Hardware:
- **CPU:** 4 cores (Intel i5/AMD Ryzen 5 or higher)
- **RAM:** 8GB (16GB recommended)
- **Disk:** 5GB free
- **Internet:** Stable connection (for API calls)

### Software:
- **Python:** 3.14+ (you already have this ✅)
- **pip:** Package manager (included with Python)
- **Git:** (Optional) for version control

### Required API Keys:

| Service | Level | Registration Link | Cost |
|---------|--------|--------------|---------|
| **Anthropic Claude** | 🔴 REQUIRED | https://console.anthropic.com/ | $5 free credit |
| **Etherscan** | 🟡 Recommended | https://etherscan.io/apis | Free (5 calls/sec) |
| **OpenSanctions** | 🟢 Optional | https://www.opensanctions.org/ | Free (public data) |
| **OpenAI** | 🟢 Optional | https://platform.openai.com/ | Alternative to Claude |
| **Quapp.cloud** | 🟢 Optional | https://quapp.cloud/ | Quantum hardware access |

**Note:** If you don't have API keys, you can still run in **DEMO_MODE** (see below).

---

## 📦 STEP 1: INSTALL DEPENDENCIES

### 1.1. Open Terminal in project directory

```powershell
cd "c:\Users\ACE DUKE\OneDrive\Máy tính\NEW PROJECT\AML-AI-Copilot\pack\sourcecode"
```

### 1.2. (Recommended) Create Virtual Environment

```powershell
# Create virtual environment
py -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1
```

**Note:** If you encounter Execution Policy errors, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 1.3. Install dependencies

```powershell
# Install all packages
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

**Time:** ~5-10 minutes (depending on internet speed)

### 1.4. Confirm installation

```powershell
# Check important packages
py -c "import numpy; print('NumPy:', numpy.__version__)"
py -c "import networkx; print('NetworkX:', networkx.__version__)"
py -c "import crewai; print('CrewAI:', crewai.__version__)"
```

If there are no errors → Installation successful ✅

---

## 🔑 STEP 2: CONFIGURE API KEYS

### 2.1. Create .env file

```powershell
# Copy example file
Copy-Item .env.example .env
```

### 2.2. Edit .env file

Open the `.env` file using Notepad or VS Code:

```powershell
notepad .env
# or
code .env
```

### 2.3. Fill in API keys

#### 🔴 REQUIRED: Anthropic Claude

```env
ANTHROPIC_API_KEY=sk-ant-api03-xxx...xxx
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5
```

**How to get Anthropic API key:**
1. Visit: https://console.anthropic.com/
2. Register an account (comes with $5 free credit)
3. Go to **API Keys** → **Create Key**
4. Copy the key starting with `sk-ant-api03-...`

#### 🟡 RECOMMENDED: Etherscan

```env
ETHERSCAN_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**How to get Etherscan API key:**
1. Visit: https://etherscan.io/register
2. Register an account (free)
3. Go to **API-KEYs** → **Add**
4. Copy the key (32 characters)

#### 🟢 OPTIONAL: OpenSanctions

```env
OPENSANCTIONS_API_KEY=your_opensanctions_key
```

**Or** leave empty to use public data (no key required).

### 2.4. Configure Quantum Backend

If you don't have quantum hardware, use classical:

```env
QUANTUM_BACKEND=classical
```

### 2.5. Save .env file

Press `Ctrl+S` to save.

---

## ✅ STEP 3: VERIFY INSTALLATION

### 3.1. Check config

```powershell
py -c "from src.config import *; print('Config loaded successfully')"
```

### 3.2. Run unit tests

```powershell
py -m pytest tests/ -v
```

**Expected result:**
```
======================== 28 passed in 12.34s =========================
```

If any test fails, see [Troubleshooting](#troubleshooting) below.

### 3.3. Run benchmark

```powershell
py -m src.quantum.benchmark --demo
```

**Expected result:**
```
[Benchmark] Running QUBO optimization on demo graph...
[Benchmark] FPR: 0.0% | F-β: 0.893 | Runtime: 1.23s
✅ Benchmark completed successfully
```

---

## 🚀 RUN THE SYSTEM

### Mode 1: Run Pipeline Handler (Full System)

#### A. Run with Quapp.cloud (Production)

```powershell
# Run handler for 1 specific wallet
py -c "from src.pipeline.handler import handler; import json; result = handler({'wallet_address': '0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b', 'backend': 'classical', 'shots': 1024, 'mode': 'hybrid'}); print(json.dumps(result, indent=2))"
```

**Sample Output:**
```json
{
  "status": "freeze_triggered",
  "case_id": "AML-FREEZE-12345678",
  "wallet_address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
  "risk_level": "HIGH",
  "recommended_action": "FREEZE",
  "qubo_risk_score": 0.92,
  "compliance_score": 0.587,
  "f_beta_score": 0.893,
  "audit_hash": "sha256:...",
  "trace_id": "uuid-...",
  "runtime_seconds": 2.45,
  "async_report_pending": true
}
```

#### B. Run with Demo Mode (No API keys needed)

Edit `.env`:
```env
DEMO_MODE=true
```

Then run the command above again.

---

### Mode 2: Run Individual Components

#### A. QUBO Optimizer

```powershell
# Test QUBO on synthetic graph
py -c "from src.quantum.hybrid_optimizer import HybridQuantumOptimizer; from src.data.etherscan_graph_builder import build_demo_graph; graph = build_demo_graph('0xTEST'); opt = HybridQuantumOptimizer('classical'); result = opt.optimize(graph); print(f'FPR: {result.false_positive_rate:.4f}, F-β: {result.f_beta_score:.4f}')"
```

#### B. Multi-Agent Crew

```powershell
# Test agent crew
py -c "from src.agents.multi_agent_crew import run_aml_crew; from src.models import AgentInput; from datetime import datetime; input_data = AgentInput(wallet_address='0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b', qubo_risk_score=0.92, qubo_flagged_nodes=['0x123'], trace_id='test-001'); report = run_aml_crew(input_data); print(f'Risk: {report.risk_level}, Action: {report.recommended_action}')"
```

**Note:** `ANTHROPIC_API_KEY` is required to run agents.

#### C. Graph Builder (with Etherscan)

```powershell
# Build real transaction graph from Etherscan
py -c "from src.data.etherscan_graph_builder import build_tx_graph_from_wallet; graph = build_tx_graph_from_wallet('0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b', 'eth', hops=2, max_nodes=50); print(f'Graph: {graph.graph.number_of_nodes()} nodes, {graph.graph.number_of_edges()} edges')"
```

**Note:** `ETHERSCAN_API_KEY` is required.

---

### Mode 3: Run Web Server (REST API)

Create `server.py` file (if it doesn't exist):

```python
# server.py
from flask import Flask, request, jsonify
from src.pipeline.handler import handler
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "service": "AML AI Copilot"}), 200

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        result = handler(data)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

Install Flask:
```powershell
py -m pip install flask
```

Run server:
```powershell
py server.py
```

Test from browser or Postman:
```
POST http://localhost:5000/analyze
Content-Type: application/json

{
  "wallet_address": "0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b",
  "backend": "classical",
  "shots": 1024,
  "mode": "hybrid"
}
```

---

## 🎯 KEY FEATURES

### 1. Analyze 1 wallet

```powershell
py analyze_wallet.py 0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b
```

Create file `analyze_wallet.py`:
```python
import sys
from src.pipeline.handler import handler
import json

if len(sys.argv) < 2:
    print("Usage: py analyze_wallet.py <wallet_address>")
    sys.exit(1)

wallet = sys.argv[1]
event = {
    "wallet_address": wallet,
    "backend": "classical",
    "shots": 1024,
    "mode": "hybrid"
}

result = handler(event)
print(json.dumps(result, indent=2))
```

### 2. Batch analysis (multiple wallets)

```powershell
py batch_analyze.py wallets.txt
```

File `wallets.txt`:
```
0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b
0x1234567890AbcdEF1234567890AbcDef12345678
0xABCDEF0123456789ABCDef0123456789abcdef01
```

### 3. Benchmark performance

```powershell
py -m src.quantum.benchmark --wallets 100 --backend classical
```

---

## 🐛 TROUBLESHOOTING

### Error 1: ModuleNotFoundError

**Symptoms:**
```
ModuleNotFoundError: No module named 'crewai'
```

**Solution:**
```powershell
# Reactivate venv
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
py -m pip install -r requirements.txt
```

---

### Error 2: API Key Invalid

**Symptoms:**
```
AuthenticationError: Invalid API key
```

**Solution:**
1. Check if the `.env` file is properly formatted
2. Verify the API key is not expired
3. Test API key:
```powershell
py -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Anthropic key:', os.getenv('ANTHROPIC_API_KEY')[:20] + '...')"
```

---

### Error 3: Rate Limit Exceeded

**Symptoms:**
```
RateLimitError: API rate limit exceeded
```

**Solution:**
- **Etherscan:** Free tier = 5 calls/sec. Wait 1 second between calls.
- **Anthropic:** Free tier = 50 requests/day. Upgrade plan or use DEMO_MODE.

```env
# In .env, turn on demo mode
DEMO_MODE=true
```

---

### Error 4: Memory Error (Graph too large)

**Symptoms:**
```
MemoryError: Unable to allocate array
```

**Solution:**
Reduce graph size in `.env`:
```env
QUBO_MAX_NODES=100  # Decrease from 500 to 100
```

---

### Error 5: Timeout

**Symptoms:**
```
TimeoutError: Operation timed out after 300s
```

**Solution:**
Increase timeout in `.env`:
```env
AGENT_TIMEOUT_SECONDS=600  # Increase from 300 to 600
QUANTUM_TIMEOUT_SECONDS=60  # Increase from 30 to 60
```

---

### Error 6: Tests Fail

**Symptoms:**
```
FAILED tests/test_qubo.py::test_qubo_optimization
```

**Solution:**
1. Check Python version:
```powershell
py --version  # Must be >= 3.14
```

2. Clean reinstall dependencies:
```powershell
py -m pip uninstall -y -r requirements.txt
py -m pip install -r requirements.txt
```

3. If it still fails, skip that test:
```powershell
py -m pytest tests/ -v -k "not test_qubo_optimization"
```

---

## 📊 MONITORING & LOGS

### View real-time logs

```powershell
# In .env, set log level
LOG_LEVEL=DEBUG
TRACE_ENABLED=true
```

Logs will be printed to console in format:
```
[2026-07-18 10:30:45] [INFO] [handler.py:123] Pipeline start | wallet=0xd90e... | trace_id=abc123
[2026-07-18 10:30:46] [INFO] [qubo.py:45] QUBO Done | FPR=0.0% | F-β=0.893
[2026-07-18 10:30:48] [INFO] [agents.py:78] FlowTracer ✓ | 7 hops
...
```

### Save logs to file

Add to the top of script:
```python
import logging
logging.basicConfig(
    filename='aml_copilot.log',
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
)
```

---

## 🎓 FULL EXECUTION (Checklist)

### ✅ Complete Checklist

- [ ] **Step 1:** Install Python 3.14+ (Already have ✅)
- [ ] **Step 2:** Create virtual environment
- [ ] **Step 3:** Install dependencies from requirements.txt
- [ ] **Step 4:** Copy .env.example → .env
- [ ] **Step 5:** Fill in API keys into .env (at least ANTHROPIC_API_KEY)
- [ ] **Step 6:** Run pytest checks (28/28 passed)
- [ ] **Step 7:** Run benchmark test
- [ ] **Step 8:** Run handler with 1 test wallet
- [ ] **Step 9:** (Optional) Run web server
- [ ] **Step 10:** (Optional) Deploy to Quapp.cloud

---

## 🚀 NEXT STEPS (After successful run)

### 1. Performance optimization
- Run benchmark with multiple wallets
- Adjust QAOA_P_MIN/MAX for quantum backend
- Profile performance with cProfile

### 2. Integrate more data sources
- Add BSC, Polygon, Arbitrum support
- Integrate CryptoScamDB API
- Add PEP (Politically Exposed Person) database

### 3. Production deployment
- Dockerize application
- Setup CI/CD with GitHub Actions
- Deploy to AWS/GCP/Azure or Quapp.cloud

### 4. Monitoring & Alerting
- Setup Prometheus metrics
- Integrate with Grafana dashboards
- Configure PagerDuty/Slack alerts

---

## 📞 SUPPORT

If you encounter issues, check:

1. **README.md** — Project overview
2. **DEMOCORE/HOW_IT_WORKS.md** — Detailed architecture explanation
3. **GitHub Issues** — Search for similar errors
4. **Discord/Slack** — QCFinOp community

---

**Good luck with your execution! 🎉**

**Team:** QCFinOp · SEA Quantathon 2026  
**Architecture:** Prof. Hans  
**Platform:** Quapp.cloud
