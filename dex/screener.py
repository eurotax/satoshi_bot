# === dex/screener.py ===

import httpx
import logging
from config import MIN_VOLUME, MIN_LIQUIDITY, MIN_PRICE_CHANGE
from utils import format_pair_message, format_signals

logger = logging.getLogger(__name__)

DEXSCREENER_API = "https://api.dexscreener.com/latest/dex/pairs/solana"

async def fetch_dex_data():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(DEXSCREENER_API, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("pairs", [])
    except Exception as e:
        logger.error(f"[dex/screener] Failed to fetch data: {e}")
        return []

def filter_signals(pairs: list) -> list:
    filtered = []
    for pair in pairs:
        try:
            volume = float(pair.get("volume", {}).get("h24", 0))
            liquidity = float(pair.get("liquidity", {}).get("usd", 0))
            price_change = float(pair.get("priceChange", {}).get("h1", 0))

            if volume >= MIN_VOLUME and liquidity >= MIN_LIQUIDITY and abs(price_change) >= MIN_PRICE_CHANGE:
                filtered.append(pair)
        except Exception as e:
            logger.warning(f"[dex/screener] Skipping malformed pair: {e}")
    return filtered

async def get_filtered_signals() -> list:
    """Return a list of filtered trading pairs."""
    raw_pairs = await fetch_dex_data()
    return filter_signals(raw_pairs)[:5]


async def get_filtered_signal_messages() -> list:
    pairs = await get_filtered_signals()
    return [format_pair_message(pair) for pair in pairs]


def format_signals_message(pairs: list, vip: bool = False) -> str:
    return format_signals(pairs, vip)
