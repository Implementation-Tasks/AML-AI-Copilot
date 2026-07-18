"""
Price Oracle — CoinGecko API
Replaces hard-coded ETH/USD = $3,000 with live market data.

Supported coins: ETH, BNB (BSC), MATIC, TRX, SOL
Fallback: cached last-known price if API unavailable.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ── Fallback cache (last-known prices) ────────────────────────────────────────
_PRICE_CACHE: dict[str, float] = {
    "eth":    3_500.0,
    "bnb":      600.0,
    "matic":      1.0,
    "trx":        0.12,
    "sol":      180.0,
}
_CACHE_TIMESTAMP: dict[str, float] = {}
_CACHE_TTL_SECONDS = 300  # 5 minutes


# ── CoinGecko coin ID map ─────────────────────────────────────────────────────
_COINGECKO_IDS = {
    "eth":   "ethereum",
    "bsc":   "binancecoin",
    "bnb":   "binancecoin",
    "matic": "matic-network",
    "tron":  "tron",
    "trx":   "tron",
    "sol":   "solana",
    "btc":   "bitcoin",
}

_COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"


def get_price_usd(coin_symbol: str) -> float:
    """
    Fetch current USD price for a coin symbol.

    Args:
        coin_symbol: "eth" | "bnb" | "matic" | "trx" | "sol" | "btc"

    Returns:
        float USD price. Falls back to cached value if API fails.
    """
    symbol = coin_symbol.lower()
    coin_id = _COINGECKO_IDS.get(symbol)

    if coin_id is None:
        logger.warning(f"[PriceOracle] Unknown coin '{symbol}', using fallback 1.0")
        return 1.0

    # Return cached value if fresh
    now = time.monotonic()
    if symbol in _CACHE_TIMESTAMP:
        if now - _CACHE_TIMESTAMP[symbol] < _CACHE_TTL_SECONDS:
            cached = _PRICE_CACHE.get(symbol, 1.0)
            logger.debug(f"[PriceOracle] Cache hit: {symbol}=${cached:.2f}")
            return cached

    # Fetch from CoinGecko
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(_COINGECKO_API, params={
                "ids": coin_id,
                "vs_currencies": "usd",
            })
            resp.raise_for_status()
            data = resp.json()

        price = float(data[coin_id]["usd"])
        _PRICE_CACHE[symbol] = price
        _CACHE_TIMESTAMP[symbol] = now
        logger.info(f"[PriceOracle] Live price: {symbol.upper()}=${price:,.2f}")
        return price

    except Exception as exc:
        fallback = _PRICE_CACHE.get(symbol, 1.0)
        logger.warning(
            f"[PriceOracle] API failed for '{symbol}': {exc}. "
            f"Using fallback ${fallback:.2f}"
        )
        return fallback


def convert_native_to_usd(amount_native: float, coin_symbol: str) -> float:
    """
    Convert a native coin amount to USD equivalent.

    Args:
        amount_native: Amount in native units (e.g., ETH, BNB, TRX)
        coin_symbol:   Coin symbol (case-insensitive)

    Returns:
        USD equivalent as float
    """
    if amount_native <= 0:
        return 0.0
    price = get_price_usd(coin_symbol)
    return amount_native * price


def get_supported_coins() -> list[str]:
    """Return list of supported coin symbols."""
    return list(_COINGECKO_IDS.keys())
