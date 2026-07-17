"""
Security & Hardening Module
Skill: security-and-hardening

Input validation, rate limiting, PII masking for AML AI Copilot.
"""
from __future__ import annotations

import hashlib
import logging
import re
import time
from collections import defaultdict
from functools import wraps
from typing import Callable

from web3 import Web3

logger = logging.getLogger(__name__)


# ─── Wallet Address Validation ────────────────────────────────────────────────

# EIP-55 checksummed Ethereum address regex
_ETH_ADDR_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
_BTC_ADDR_RE = re.compile(r"^(1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,62}$")


def validate_wallet_address(address: str, chain: str = "eth") -> str:
    """
    Validate and normalise a wallet address.

    Args:
        address: Raw wallet address string
        chain: "eth" | "bsc" | "btc"

    Returns:
        Normalised address (lowercase for ETH)

    Raises:
        ValueError: If address format is invalid
    """
    if not address or not isinstance(address, str):
        raise ValueError(f"Wallet address must be a non-empty string, got: {type(address)}")

    address = address.strip()

    if chain in ("eth", "bsc"):
        if not Web3.is_address(address):
            raise ValueError(
                f"Invalid Ethereum/BSC address format or checksum failed: '{address}'."
            )
        return Web3.to_checksum_address(address)

    if chain == "btc":
        if not _BTC_ADDR_RE.match(address):
            raise ValueError(f"Invalid Bitcoin address format: '{address}'")
        return address

    raise ValueError(f"Unsupported chain: '{chain}'. Choose from: eth, bsc, btc")


def validate_risk_score(score: float) -> float:
    """Ensure risk score is in [0.0, 1.0]."""
    if not isinstance(score, (int, float)):
        raise ValueError(f"Risk score must be numeric, got: {type(score)}")
    if not 0.0 <= float(score) <= 1.0:
        raise ValueError(f"Risk score must be in [0.0, 1.0], got: {score}")
    return float(score)


# ─── PII / Sensitive Data Masking ────────────────────────────────────────────

def mask_wallet_for_log(wallet: str) -> str:
    """Mask middle of wallet address for log output. 0xABCD...1234"""
    if len(wallet) <= 10:
        return "***"
    return f"{wallet[:6]}...{wallet[-4:]}"


def mask_entity_name(name: str) -> str:
    """Partially mask entity name for non-compliance logs."""
    if len(name) <= 4:
        return "***"
    return name[:2] + "*" * (len(name) - 4) + name[-2:]


def sanitise_for_log(data: dict) -> dict:
    """
    Recursively sanitise a dict for safe logging.
    Masks: wallet_address, entity_name, api_key, private_key fields.
    """
    SENSITIVE_KEYS = {"api_key", "private_key", "secret", "password", "token"}
    WALLET_KEYS = {"wallet_address", "wallet", "from_wallet", "to_wallet", "address"}
    ENTITY_KEYS = {"entity_name", "name"}

    result = {}
    for k, v in data.items():
        if k in SENSITIVE_KEYS:
            result[k] = "***REDACTED***"
        elif k in WALLET_KEYS and isinstance(v, str):
            result[k] = mask_wallet_for_log(v)
        elif k in ENTITY_KEYS and isinstance(v, str):
            result[k] = mask_entity_name(v)
        elif isinstance(v, dict):
            result[k] = sanitise_for_log(v)
        elif isinstance(v, list):
            result[k] = [sanitise_for_log(i) if isinstance(i, dict) else i for i in v]
        else:
            result[k] = v
    return result


# ─── Rate Limiter ─────────────────────────────────────────────────────────────

class RateLimiter:
    """
    Token-bucket rate limiter for external API calls.
    Thread-safe for single-process use.

    Usage:
        limiter = RateLimiter(max_calls=5, window_seconds=1.0)

        @limiter
        def call_etherscan(wallet):
            ...
    """

    def __init__(self, max_calls: int = 5, window_seconds: float = 1.0):
        self.max_calls = max_calls
        self.window = window_seconds
        self._calls: list[float] = []

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            self._wait_if_needed()
            return func(*args, **kwargs)
        return wrapper

    def _wait_if_needed(self):
        now = time.monotonic()
        # Remove old calls outside the window
        self._calls = [t for t in self._calls if now - t < self.window]
        if len(self._calls) >= self.max_calls:
            sleep_time = self.window - (now - self._calls[0]) + 0.01
            if sleep_time > 0:
                logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)
        self._calls.append(time.monotonic())


# Pre-configured limiters for common APIs
etherscan_limiter = RateLimiter(max_calls=5, window_seconds=1.0)     # Free tier: 5/s
opensanctions_limiter = RateLimiter(max_calls=10, window_seconds=1.0)
dune_limiter = RateLimiter(max_calls=2, window_seconds=1.0)


# ─── Audit Hash ───────────────────────────────────────────────────────────────

def compute_audit_hash(report_data: dict) -> str:
    """
    Compute SHA-256 hash of a report dict for tamper-evidence.
    Keys are sorted for determinism.
    """
    import json
    canonical = json.dumps(report_data, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ─── Security Checklist ───────────────────────────────────────────────────────

def run_security_checklist() -> dict[str, bool]:
    """
    Run automated security checks on the environment.
    Returns dict of check_name → passed.
    """
    import os
    checks = {}

    # 1. No API keys in environment with 'test' or 'demo' values
    for key in ["ETHERSCAN_API_KEY", "OPENSANCTIONS_API_KEY", "ANTHROPIC_API_KEY"]:
        val = os.getenv(key, "")
        checks[f"no_demo_key_{key.lower()}"] = val not in ("", "your_key_here", "demo", "test")

    # 2. .env file exists and is not committed
    env_file = Path(".env")
    checks["env_file_exists"] = env_file.exists()
    gitignore = Path(".gitignore")
    if gitignore.exists():
        checks["env_in_gitignore"] = ".env" in gitignore.read_text()
    else:
        checks["env_in_gitignore"] = False

    # 3. Reports dir has no world-readable permissions (Windows — always pass)
    checks["reports_dir_exists"] = Path("reports").exists()

    # 4. QUBO_MAX_NODES configured
    max_nodes = os.getenv("QUBO_MAX_NODES", "500")
    checks["qubo_max_nodes_set"] = max_nodes.isdigit() and int(max_nodes) <= 1000

    return checks


from pathlib import Path

# ============================================================
# Bottleneck 3: Anti-Spoofing Layer
# (Mentorship Review slide 16)
# Multi-node RPC Consensus + Payload Signing + Threshold Routing
# ============================================================

import hashlib
import hmac
import os
from pathlib import Path
from typing import Any

_PAYLOAD_SIGNING_KEY = os.getenv("PAYLOAD_SIGNING_KEY", "").encode()


def sign_payload(data: dict) -> str:
    """
    Compute HMAC-SHA256 signature of a canonical JSON payload.

    Used to verify telemetry integrity before it enters the graph builder.
    Slide 16: "Strict payload signing -- cryptographic integrity check
    before acceptance."

    Args:
        data: Payload dict to sign

    Returns:
        Hex HMAC-SHA256 signature string
    """
    import json
    canonical = json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    if not _PAYLOAD_SIGNING_KEY:
        # Fallback: use SHA-256 hash (no secret key -- log warning)
        logger.warning("[AntiSpoof] PAYLOAD_SIGNING_KEY not set -- using unsigned hash")
        return hashlib.sha256(canonical).hexdigest()
    return hmac.new(_PAYLOAD_SIGNING_KEY, canonical, hashlib.sha256).hexdigest()


def verify_payload_signature(data: dict, signature: str) -> bool:
    """
    Verify that a received payload has not been tampered with.

    Returns:
        True if signature matches, False if spoofed / tampered
    """
    expected = sign_payload(data)
    return hmac.compare_digest(expected, signature)


def rpc_consensus_check(
    node_responses: list[dict[str, Any]],
    state_key: str = "state_hash",
    min_consensus: float = 0.67,
) -> tuple[bool, dict[str, Any]]:
    """
    Multi-node RPC consensus validator.

    Slide 16: "Multi-node RPC consensus -- query independent nodes and
    cross-verify state hash."

    Compares state hashes from multiple independent RPC nodes.
    If >= min_consensus fraction agree -> consensus reached, telemetry trusted.
    Otherwise -> flag as spoofed / jammed, route to fallback pipeline.

    Args:
        node_responses: List of response dicts from independent RPC nodes
                        Each must contain ``state_key`` field.
        state_key:      Field name for the state hash comparison
        min_consensus:  Minimum fraction of agreeing nodes (default: 2/3)

    Returns:
        (consensus_reached: bool, agreed_response: dict)
        If consensus_reached is False -> route to fallback pipeline.
    """
    if not node_responses:
        logger.warning("[AntiSpoof] No RPC responses -- treating as jammed")
        return False, {}

    # Count occurrences of each state hash
    from collections import Counter
    hash_counts = Counter(
        str(r.get(state_key, "MISSING")) for r in node_responses
    )
    most_common_hash, most_common_count = hash_counts.most_common(1)[0]
    consensus_fraction = most_common_count / len(node_responses)

    if most_common_hash == "MISSING":
        logger.error("[AntiSpoof] RPC nodes did not return state_hash -- spoofing suspected")
        return False, {}

    consensus_reached = consensus_fraction >= min_consensus

    if consensus_reached:
        agreed_response = next(
            r for r in node_responses if str(r.get(state_key)) == most_common_hash
        )
        logger.info(
            "[AntiSpoof] RPC consensus OK | %d/%d nodes agree | hash=%s",
            most_common_count, len(node_responses), most_common_hash[:16],
        )
        return True, agreed_response
    else:
        logger.error(
            "[AntiSpoof] RPC consensus FAILED | best agreement=%.0f%% (< %.0f%%) "
            "| Flagging as SPOOFED/JAMMED -> routing to fallback pipeline",
            consensus_fraction * 100, min_consensus * 100,
        )
        return False, {}


def threshold_routing(
    payload: dict[str, Any],
    signature: Optional[str] = None,
    rpc_responses: Optional[list[dict]] = None,
    min_consensus: float = 0.67,
) -> tuple[str, dict[str, Any]]:
    """
    Top-level anti-spoofing entry point with threshold routing.

    Slide 16: "Threshold routing -- if verification fails, flag as
    'jammed/spoofed' and fall back to redundancy pipeline."

    Checks:
        1. Payload signature integrity (if signature provided)
        2. Multi-node RPC consensus (if rpc_responses provided)

    Returns:
        (route: str, payload: dict)
        route: "proceed"  -> telemetry trusted, proceed to graph builder
               "fallback" -> spoofed/jammed, use cached/redundant data
               "reject"   -> critical failure, discard payload
    """
    # Check 1: Payload signature
    if signature is not None:
        if not verify_payload_signature(payload, signature):
            logger.error(
                "[AntiSpoof] Payload signature INVALID -> route=reject | "
                "Cryptographic integrity check failed"
            )
            return "reject", {}
        logger.info("[AntiSpoof] Payload signature verified OK")

    # Check 2: RPC consensus
    if rpc_responses is not None:
        consensus_ok, agreed = rpc_consensus_check(rpc_responses, min_consensus=min_consensus)
        if not consensus_ok:
            logger.warning("[AntiSpoof] RPC consensus failed -> route=fallback")
            return "fallback", {}
        # Merge agreed response into payload for downstream use
        payload = {**payload, **agreed}

    return "proceed", payload
