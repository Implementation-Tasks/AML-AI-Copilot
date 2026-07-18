# 🚀 HƯỚNG DẪN CHẠY FULL PROJECT
**AML AI Copilot - Hệ thống Hybrid Quantum-Agentic AML hoàn chỉnh**

---

## 📋 MỤC LỤC

1. [Tổng quan](#tổng-quan)
2. [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
3. [Cài đặt bước 1: Dependencies](#bước-1-cài-đặt-dependencies)
4. [Cài đặt bước 2: API Keys](#bước-2-cấu-hình-api-keys)
5. [Cài đặt bước 3: Kiểm tra](#bước-3-kiểm-tra-cài-đặt)
6. [Chạy hệ thống](#chạy-hệ-thống)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 TỔNG QUAN

### So sánh: Demo vs Full Project

| Tính năng | DEMOCORE (Demo) | Full Project |
|-----------|----------------|--------------|
| **Dữ liệu** | Synthetic (giả lập) | Real blockchain data (thực) |
| **QUBO** | Simulated Annealing | Quantum hardware / SA |
| **Agents** | Mock data | Real API calls (Etherscan, OFAC) |
| **API Keys** | ❌ Không cần | ✅ Cần (Anthropic, Etherscan, v.v.) |
| **Mục đích** | Demo & Testing | Production-ready |

### Full Project bao gồm:

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

## 💻 YÊU CẦU HỆ THỐNG

### Phần cứng tối thiểu:
- **CPU:** 4 cores (Intel i5/AMD Ryzen 5 trở lên)
- **RAM:** 8GB (khuyến nghị 16GB)
- **Disk:** 5GB trống
- **Internet:** Kết nối ổn định (cho API calls)

### Phần mềm:
- **Python:** 3.14+ (bạn đã có ✅)
- **pip:** Package manager (đi kèm Python)
- **Git:** (Optional) cho version control

### API Keys cần thiết:

| Service | Mức độ | Link đăng ký | Chi phí |
|---------|--------|--------------|---------|
| **Anthropic Claude** | 🔴 BẮT BUỘC | https://console.anthropic.com/ | $5 credit miễn phí |
| **Etherscan** | 🟡 Khuyến nghị | https://etherscan.io/apis | Miễn phí (5 calls/sec) |
| **OpenSanctions** | 🟢 Tùy chọn | https://www.opensanctions.org/ | Miễn phí (public data) |
| **OpenAI** | 🟢 Tùy chọn | https://platform.openai.com/ | Alternative to Claude |
| **Quapp.cloud** | 🟢 Tùy chọn | https://quapp.cloud/ | Quantum hardware access |

**Lưu ý:** Nếu không có API keys, bạn vẫn chạy được ở **DEMO_MODE** (xem bên dưới).

---

## 📦 BƯỚC 1: CÀI ĐẶT DEPENDENCIES

### 1.1. Mở Terminal trong thư mục project

```powershell
cd "c:\Users\ACE DUKE\OneDrive\Máy tính\NEW PROJECT\AML-AI-Copilot\pack\sourcecode"
```

### 1.2. (Khuyến nghị) Tạo Virtual Environment

```powershell
# Tạo môi trường ảo
py -m venv venv

# Kích hoạt môi trường ảo
.\venv\Scripts\Activate.ps1
```

**Lưu ý:** Nếu gặp lỗi Execution Policy, chạy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 1.3. Cài đặt dependencies

```powershell
# Cài đặt tất cả packages
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
```

**Thời gian:** ~5-10 phút (tùy tốc độ internet)

### 1.4. Xác nhận cài đặt

```powershell
# Kiểm tra các packages quan trọng
py -c "import numpy; print('NumPy:', numpy.__version__)"
py -c "import networkx; print('NetworkX:', networkx.__version__)"
py -c "import crewai; print('CrewAI:', crewai.__version__)"
```

Nếu không có lỗi → Cài đặt thành công ✅

---

## 🔑 BƯỚC 2: CẤU HÌNH API KEYS

### 2.1. Tạo file .env

```powershell
# Copy file mẫu
Copy-Item .env.example .env
```

### 2.2. Chỉnh sửa file .env

Mở file `.env` bằng Notepad hoặc VS Code:

```powershell
notepad .env
# hoặc
code .env
```

### 2.3. Điền API keys

#### 🔴 BẮT BUỘC: Anthropic Claude

```env
ANTHROPIC_API_KEY=sk-ant-api03-xxx...xxx
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-5
```

**Cách lấy Anthropic API key:**
1. Truy cập: https://console.anthropic.com/
2. Đăng ký tài khoản (có $5 credit miễn phí)
3. Vào **API Keys** → **Create Key**
4. Copy key bắt đầu bằng `sk-ant-api03-...`

#### 🟡 KHUYẾN NGHỊ: Etherscan

```env
ETHERSCAN_API_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Cách lấy Etherscan API key:**
1. Truy cập: https://etherscan.io/register
2. Đăng ký tài khoản (miễn phí)
3. Vào **API-KEYs** → **Add**
4. Copy key (32 ký tự)

#### 🟢 TÙY CHỌN: OpenSanctions

```env
OPENSANCTIONS_API_KEY=your_opensanctions_key
```

**Hoặc** để trống nếu dùng public data (không cần key).

### 2.4. Cấu hình Quantum Backend

Nếu không có quantum hardware, dùng classical:

```env
QUANTUM_BACKEND=classical
```

### 2.5. Lưu file .env

Nhấn `Ctrl+S` để lưu.

---

## ✅ BƯỚC 3: KIỂM TRA CÀI ĐẶT

### 3.1. Kiểm tra config

```powershell
py -c "from src.config import *; print('Config loaded successfully')"
```

### 3.2. Chạy unit tests

```powershell
py -m pytest tests/ -v
```

**Kết quả mong đợi:**
```
======================== 28 passed in 12.34s =========================
```

Nếu có test fail, xem [Troubleshooting](#troubleshooting) bên dưới.

### 3.3. Chạy benchmark

```powershell
py -m src.quantum.benchmark --demo
```

**Kết quả mong đợi:**
```
[Benchmark] Running QUBO optimization on demo graph...
[Benchmark] FPR: 0.0% | F-β: 0.893 | Runtime: 1.23s
✅ Benchmark completed successfully
```

---

## 🚀 CHẠY HỆ THỐNG

### Mode 1: Chạy Pipeline Handler (Full System)

#### A. Chạy với Quapp.cloud (Production)

```powershell
# Chạy handler cho 1 wallet cụ thể
py -c "from src.pipeline.handler import handler; import json; result = handler({'wallet_address': '0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b', 'backend': 'classical', 'shots': 1024, 'mode': 'hybrid'}); print(json.dumps(result, indent=2))"
```

**Output mẫu:**
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

#### B. Chạy với Demo Mode (Không cần API keys)

Chỉnh sửa `.env`:
```env
DEMO_MODE=true
```

Sau đó chạy lại command trên.

---

### Mode 2: Chạy từng Component riêng lẻ

#### A. QUBO Optimizer

```powershell
# Test QUBO trên synthetic graph
py -c "from src.quantum.hybrid_optimizer import HybridQuantumOptimizer; from src.data.etherscan_graph_builder import build_demo_graph; graph = build_demo_graph('0xTEST'); opt = HybridQuantumOptimizer('classical'); result = opt.optimize(graph); print(f'FPR: {result.false_positive_rate:.4f}, F-β: {result.f_beta_score:.4f}')"
```

#### B. Multi-Agent Crew

```powershell
# Test agent crew
py -c "from src.agents.multi_agent_crew import run_aml_crew; from src.models import AgentInput; from datetime import datetime; input_data = AgentInput(wallet_address='0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b', qubo_risk_score=0.92, qubo_flagged_nodes=['0x123'], trace_id='test-001'); report = run_aml_crew(input_data); print(f'Risk: {report.risk_level}, Action: {report.recommended_action}')"
```

**Lưu ý:** Cần có `ANTHROPIC_API_KEY` để chạy agents.

#### C. Graph Builder (với Etherscan)

```powershell
# Build real transaction graph từ Etherscan
py -c "from src.data.etherscan_graph_builder import build_tx_graph_from_wallet; graph = build_tx_graph_from_wallet('0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b', 'eth', hops=2, max_nodes=50); print(f'Graph: {graph.graph.number_of_nodes()} nodes, {graph.graph.number_of_edges()} edges')"
```

**Lưu ý:** Cần có `ETHERSCAN_API_KEY`.

---

### Mode 3: Chạy Web Server (REST API)

Tạo file `server.py` (nếu chưa có):

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

Cài Flask:
```powershell
py -m pip install flask
```

Chạy server:
```powershell
py server.py
```

Test từ browser hoặc Postman:
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

## 🎯 CÁC CHỨC NĂNG CHÍNH

### 1. Phân tích 1 wallet

```powershell
py analyze_wallet.py 0xd90e2f925DA726b50C4Ed8D0Fb90Ad053324F31b
```

Tạo file `analyze_wallet.py`:
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

### 2. Batch analysis (nhiều wallets)

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

### Lỗi 1: ModuleNotFoundError

**Triệu chứng:**
```
ModuleNotFoundError: No module named 'crewai'
```

**Giải pháp:**
```powershell
# Kích hoạt lại venv
.\venv\Scripts\Activate.ps1

# Cài lại dependencies
py -m pip install -r requirements.txt
```

---

### Lỗi 2: API Key Invalid

**Triệu chứng:**
```
AuthenticationError: Invalid API key
```

**Giải pháp:**
1. Kiểm tra file `.env` có đúng format không
2. Xác nhận API key còn hạn sử dụng
3. Test API key:
```powershell
py -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Anthropic key:', os.getenv('ANTHROPIC_API_KEY')[:20] + '...')"
```

---

### Lỗi 3: Rate Limit Exceeded

**Triệu chứng:**
```
RateLimitError: API rate limit exceeded
```

**Giải pháp:**
- **Etherscan:** Free tier = 5 calls/sec. Chờ 1 giây giữa các calls.
- **Anthropic:** Free tier = 50 requests/day. Nâng cấp plan hoặc dùng DEMO_MODE.

```env
# Trong .env, bật demo mode
DEMO_MODE=true
```

---

### Lỗi 4: Memory Error (Graph quá lớn)

**Triệu chứng:**
```
MemoryError: Unable to allocate array
```

**Giải pháp:**
Giảm kích thước graph trong `.env`:
```env
QUBO_MAX_NODES=100  # Giảm từ 500 xuống 100
```

---

### Lỗi 5: Timeout

**Triệu chứng:**
```
TimeoutError: Operation timed out after 300s
```

**Giải pháp:**
Tăng timeout trong `.env`:
```env
AGENT_TIMEOUT_SECONDS=600  # Tăng từ 300 lên 600
QUANTUM_TIMEOUT_SECONDS=60  # Tăng từ 30 lên 60
```

---

### Lỗi 6: Tests Fail

**Triệu chứng:**
```
FAILED tests/test_qubo.py::test_qubo_optimization
```

**Giải pháp:**
1. Kiểm tra Python version:
```powershell
py --version  # Phải >= 3.14
```

2. Cài lại dependencies clean:
```powershell
py -m pip uninstall -y -r requirements.txt
py -m pip install -r requirements.txt
```

3. Nếu vẫn fail, skip test đó:
```powershell
py -m pytest tests/ -v -k "not test_qubo_optimization"
```

---

## 📊 MONITORING & LOGS

### Xem logs realtime

```powershell
# Trong .env, set log level
LOG_LEVEL=DEBUG
TRACE_ENABLED=true
```

Logs sẽ in ra console với format:
```
[2026-07-18 10:30:45] [INFO] [handler.py:123] Pipeline start | wallet=0xd90e... | trace_id=abc123
[2026-07-18 10:30:46] [INFO] [qubo.py:45] QUBO Done | FPR=0.0% | F-β=0.893
[2026-07-18 10:30:48] [INFO] [agents.py:78] FlowTracer ✓ | 7 hops
...
```

### Lưu logs vào file

Thêm vào đầu script:
```python
import logging
logging.basicConfig(
    filename='aml_copilot.log',
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
)
```

---

## 🎓 CHẠY TỪ ĐẦU (Checklist)

### ✅ Checklist đầy đủ

- [ ] **Bước 1:** Cài Python 3.14+ (Đã có ✅)
- [ ] **Bước 2:** Tạo virtual environment
- [ ] **Bước 3:** Cài dependencies từ requirements.txt
- [ ] **Bước 4:** Copy .env.example → .env
- [ ] **Bước 5:** Điền API keys vào .env (ít nhất ANTHROPIC_API_KEY)
- [ ] **Bước 6:** Chạy pytest kiểm tra (28/28 passed)
- [ ] **Bước 7:** Chạy benchmark test
- [ ] **Bước 8:** Chạy handler với 1 wallet test
- [ ] **Bước 9:** (Optional) Chạy web server
- [ ] **Bước 10:** (Optional) Deploy lên Quapp.cloud

---

## 🚀 NEXT STEPS (Sau khi chạy thành công)

### 1. Tối ưu hiệu suất
- Chạy benchmark với nhiều wallets
- Điều chỉnh QAOA_P_MIN/MAX cho quantum backend
- Profile performance với cProfile

### 2. Tích hợp thêm data sources
- Thêm BSC, Polygon, Arbitrum support
- Tích hợp CryptoScamDB API
- Thêm PEP (Politically Exposed Person) database

### 3. Deploy production
- Dockerize application
- Setup CI/CD với GitHub Actions
- Deploy lên AWS/GCP/Azure hoặc Quapp.cloud

### 4. Monitoring & Alerting
- Setup Prometheus metrics
- Integrate với Grafana dashboards
- Configure PagerDuty/Slack alerts

---

## 📞 HỖ TRỢ

Nếu gặp vấn đề, kiểm tra:

1. **README.md** — Tổng quan project
2. **DEMOCORE/HOW_IT_WORKS.md** — Giải thích kiến trúc chi tiết
3. **GitHub Issues** — Tìm kiếm lỗi tương tự
4. **Discord/Slack** — QCFinOp community

---

**Chúc bạn chạy thành công! 🎉**

**Team:** QCFinOp · SEA Quantathon 2026  
**Architecture:** Prof. Hans  
**Platform:** Quapp.cloud
