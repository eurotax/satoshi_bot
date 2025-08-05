# === bybit/signals.py ===

"""Utilities for fetching and formatting Bybit market data."""

import logging
from typing import Any, Dict, Optional

import httpx

BYBIT_TICKER_URL = "https://api.bybit.com/v5/market/tickers"

logger = logging.getLogger(__name__)


async def fetch_ticker(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch ticker information for ``symbol`` from Bybit.

    Returns ``None`` if the request fails or no data is returned."""
    params = {"category": "linear", "symbol": symbol}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(BYBIT_TICKER_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json().get("result", {})
            items = data.get("list", [])
            return items[0] if items else None
    except Exception as exc:
        logger.error("[bybit] Failed to fetch %s ticker: %s", symbol, exc)
        return None


def extract_change_pct(ticker: Dict[str, Any]) -> float:
    """Extract 24h price change percentage from a Bybit ticker."""
    try:
        return float(ticker.get("price24hPcnt", 0)) * 100
    except Exception as exc:
        logger.debug("[bybit] Failed to parse price24hPcnt: %s", exc)
        return 0.0


def format_alert(symbol: str, last_price: float, change_pct: float) -> str:
    """Return a human-friendly alert message for Telegram."""
    direction = "📈 Pump" if change_pct >= 0 else "📉 Dump"
    return (
        f"{direction} on {symbol}\n"
        f"Price: {last_price}\n"
        f"24h Change: {change_pct:.2f}%"
    )
