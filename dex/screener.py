# === dex/screener.py ===

import httpx
import logging
from config import MIN_VOLUME, MIN_LIQUIDITY, MIN_PRICE_CHANGE


logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fetch and filter data from the DEXScreener API.  Helper utilities here are
# used by both the command handlers and the scheduled jobs.
# ---------------------------------------------------------------------------

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

def format_signal_message(pair: dict) -> str:
    """Return a markdown formatted message for a single trading pair."""
    base = pair.get("baseToken", {}).get("symbol", "")
    quote = pair.get("quoteToken", {}).get("symbol", "")
    name = f"{base}/{quote}"
    price = float(pair.get("priceUsd", 0))
    change = float(pair.get("priceChange", {}).get("h1", 0))
    volume = float(pair.get("volume", {}).get("h24", 0))
    liquidity = float(pair.get("liquidity", {}).get("usd", 0))
    url = pair.get("url", "")
    emoji = "📈" if change > 0 else "📉"

    return (
        f"{emoji} [{name}]({url})\n"
        f"💰 Price: `${price:.6f}`\n"
        f"💹 1h Change: `{change:.2f}%`\n"
        f"📊 Volume 24h: `${volume:,.0f}`\n"
        f"🔒 Liquidity: `${liquidity:,.0f}`"
    )

async def get_filtered_signals(limit: int = 5) -> list:
    """Fetch and filter pairs, returning up to ``limit`` results."""
    raw_pairs = await fetch_dex_data()
    return filter_signals(raw_pairs)[:limit]

def format_signals_message(pairs: list, vip: bool = False) -> str:
    """Compose a multi-line message from filtered pairs."""
    if not pairs:
        return "⚠️ No high-quality signals found right now."

    header = "💎 *VIP SIGNALS*\n\n" if vip else "📊 *Top Crypto Pairs Today*\n\n"
    body = "\n\n".join(format_signal_message(p) for p in pairs)
    footer = (
        "🔒 *Private signals for VIP members only.*"
        if vip
        else "💎 Want more? [Join VIP](https://t.me/+sR2qa2jnr6o5MDk0) for exclusive updates!"
    )
    return header + body + "\n\n" + footer

async def get_filtered_signal_messages():
    raw_pairs = await fetch_dex_data()
    top_signals = filter_signals(raw_pairs)[:5]
    return [format_signal_message(pair) for pair in top_signals]
