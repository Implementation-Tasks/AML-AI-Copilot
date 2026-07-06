"""
AML AI Copilot — Project Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

# === API Keys ===
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
DUNE_API_KEY = os.getenv("DUNE_API_KEY", "")
OPENSANCTIONS_API_KEY = os.getenv("OPENSANCTIONS_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
QUAPP_API_KEY = os.getenv("QUAPP_API_KEY", "")

# === Quantum Backend ===
QUANTUM_BACKEND = os.getenv("QUANTUM_BACKEND", "qudora")  # qudora | quandela | classical
QUANTUM_TIMEOUT_SECONDS = int(os.getenv("QUANTUM_TIMEOUT_SECONDS", "30"))
QUBO_MAX_NODES = int(os.getenv("QUBO_MAX_NODES", "500"))

# === Agent Settings ===
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")  # anthropic | openai
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-5")
AGENT_RETRY_ATTEMPTS = int(os.getenv("AGENT_RETRY_ATTEMPTS", "3"))
AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "300"))

# === AML Thresholds ===
QUBO_RISK_THRESHOLD = float(os.getenv("QUBO_RISK_THRESHOLD", "0.85"))
F_BETA = float(os.getenv("F_BETA", "0.5"))  # β < 1 → Precision > Recall

# === Data Paths ===
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
ELLIPTIC_DATASET_PATH = DATA_DIR / "elliptic_txs_features.csv"
ELLIPTIC_LABELS_PATH = DATA_DIR / "elliptic_txs_classes.csv"
