"""
Observability & Instrumentation Module
Skill: observability-and-instrumentation

Structured JSON logging, metrics, trace ID propagation.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Generator

# ─── JSON Log Formatter ───────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON for log aggregation systems.

    Output:
    {"ts":"2026-06-26T02:30:00Z","level":"INFO","logger":"src.agents","msg":"...","trace_id":"..."}
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Attach trace_id if present
        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id
        # Attach extra fields
        for key in ("wallet", "case_id", "risk_level", "action", "backend", "runtime_s"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        # Attach exception info
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(level: str = "INFO", json_output: bool = True) -> None:
    """
    Configure root logger with JSON formatter.
    Call this once at application startup.
    """
    handler = logging.StreamHandler()
    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s — %(message)s"))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


# ─── Trace Context ────────────────────────────────────────────────────────────

_CURRENT_TRACE_ID: str = ""


def new_trace_id() -> str:
    """Generate a new UUID trace ID."""
    return str(uuid.uuid4())


@contextmanager
def trace_context(trace_id: str | None = None) -> Generator[str, None, None]:
    """
    Context manager that attaches a trace_id to all log records within scope.

    Usage:
        with trace_context() as tid:
            logger.info("Starting pipeline")  # log will include trace_id=tid
    """
    global _CURRENT_TRACE_ID
    tid = trace_id or new_trace_id()
    old = _CURRENT_TRACE_ID
    _CURRENT_TRACE_ID = tid

    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.trace_id = tid
        return record

    logging.setLogRecordFactory(record_factory)
    try:
        yield tid
    finally:
        _CURRENT_TRACE_ID = old
        logging.setLogRecordFactory(old_factory)


# ─── Simple Metrics ───────────────────────────────────────────────────────────

class Metrics:
    """
    In-process metrics counters. In production, replace with Prometheus client.

    Tracks:
        - aml_alerts_total
        - false_positive_rate (rolling)
        - agent_latency_seconds (per agent)
    """

    def __init__(self):
        self._counters: dict[str, float] = {}
        self._histograms: dict[str, list[float]] = {}
        self._gauges: dict[str, float] = {}

    def increment(self, name: str, value: float = 1.0, labels: dict | None = None) -> None:
        key = self._key(name, labels)
        self._counters[key] = self._counters.get(key, 0.0) + value

    def gauge(self, name: str, value: float, labels: dict | None = None) -> None:
        key = self._key(name, labels)
        self._gauges[key] = value

    def histogram(self, name: str, value: float, labels: dict | None = None) -> None:
        key = self._key(name, labels)
        self._histograms.setdefault(key, []).append(value)

    def summary(self) -> dict:
        result: dict[str, Any] = {"counters": self._counters, "gauges": self._gauges}
        for k, vals in self._histograms.items():
            if vals:
                result.setdefault("histograms", {})[k] = {
                    "count": len(vals),
                    "mean": round(sum(vals) / len(vals), 4),
                    "p50": round(sorted(vals)[len(vals) // 2], 4),
                    "p95": round(sorted(vals)[int(len(vals) * 0.95)], 4),
                    "max": round(max(vals), 4),
                }
        return result

    @staticmethod
    def _key(name: str, labels: dict | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    @contextmanager
    def timer(self, name: str, labels: dict | None = None) -> Generator[None, None, None]:
        """Context manager to record elapsed time as histogram."""
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = time.perf_counter() - start
            self.histogram(name, elapsed, labels)


# Global metrics instance (singleton pattern)
metrics = Metrics()


# ─── Timed Decorator ─────────────────────────────────────────────────────────

def timed(metric_name: str):
    """Decorator to record function latency as a metric histogram."""
    def decorator(func):
        from functools import wraps
        @wraps(func)
        def wrapper(*args, **kwargs):
            with metrics.timer(metric_name, labels={"func": func.__name__}):
                return func(*args, **kwargs)
        return wrapper
    return decorator
