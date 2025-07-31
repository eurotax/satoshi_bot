# === utils.py ===

import httpx
import logging
from config import MIN_VOLUME, MIN_LIQUIDITY, MIN_PRICE_CHANGE

logger = logging.getLogger(__name__)


async def fetch_dex_data():
    """Fetch top Solana pairs from DEXScreener with basic retries."""
    urls = [
        "https://api.dexscreener.com/latest/dex/pairs/solana",
        "https://api.dexscreener.io/latest/dex/pairs/solana",
    ]
    for attempt in range(3):
        for url in urls:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(url)
                    if response.is_error:
                        logger.warning(
                            "DEXScreener returned %s for %s on attempt %s",
                            response.status_code,
                            url,
                            attempt + 1,
                        )
                        continue
                    data = response.json()
                    return data.get("pairs", [])
            except Exception as e:
                logger.error("Error fetching DEX data from %s: %s", url, e)
    return []


def is_legit_token(pair):
    """Simulate anti-scam heuristics (can be enhanced with on-chain data)"""
    try:
        base = pair.get("baseToken", {})
        tax = pair.get("txns", {}).get("h1", {}).get("buys", 0) + pair.get("txns", {}).get("h1", {}).get("sells", 0)
        renounced = pair.get("pairCreatedAt", 0) > 0  # Placeholder for renounce check
        locked = pair.get("liquidity", {}).get("locked", False)  # Placeholder

        return renounced and locked and tax >= 5
    except:
        return False


def filter_signals(pairs):
    """Filter based on volume, liquidity, and price change"""
    filtered = []
    for pair in pairs:
        try:
            volume = float(pair.get("volume", {}).get("h24", 0))
            liquidity = float(pair.get("liquidity", {}).get("usd", 0))
            change = float(pair.get("priceChange", {}).get("h1", 0))

            if volume >= MIN_VOLUME and liquidity >= MIN_LIQUIDITY and abs(change) >= MIN_PRICE_CHANGE:
                if is_legit_token(pair):
                    filtered.append(pair)
        except Exception as e:
            logger.warning(f"Pair skipped due to parsing error: {e}")
            continue
    return filtered


def format_signals(pairs, vip: bool = False):
    """Format signal messages for Telegram using Markdown"""
    if not pairs:
        return "⚠️ No high-quality signals found right now. Please check again later."

    header = "💎 *VIP SIGNALS*\n\n" if vip else "📊 *Top Crypto Pairs Today*\n\n"
    body = ""

    for pair in pairs:
        name = f"{pair['baseToken']['symbol']}/{pair['quoteToken']['symbol']}"
        price = float(pair.get("priceUsd", 0))
        change = float(pair.get("priceChange", {}).get("h1", 0))
        volume = float(pair.get("volume", {}).get("h24", 0))
        liquidity = float(pair.get("liquidity", {}).get("usd", 0))
        url = pair.get("url", "")
        emoji = "📈" if change > 0 else "📉"

        body += (
            f"{emoji} [{name}]({url})\n"
            f"💰 Price: `${price:.6f}`\n"
            f"💹 1h Change: `{change:.2f}%`\n"
            f"📊 Volume 24h: `${volume:,.0f}`\n"
            f"🔒 Liquidity: `${liquidity:,.0f}`\n\n"
        )

    footer = (
        "🔒 *Private signals for VIP members only.*" if vip
        else "💎 Want more? [Join VIP](https://t.me/+sR2qa2jnr6o5MDk0) for exclusive updates!"
    )
    return header + body + footer


# ---------------------------------------------------------------------------
# Compatibility helpers expected by tests
# ---------------------------------------------------------------------------

async def fetch_pairs():
    """Wrapper used in tests for ``fetch_dex_data``."""
    return await fetch_dex_data()


def filter_pairs(pairs):
    """Wrapper used in tests for ``filter_signals``."""
    return filter_signals(pairs)


def format_pair_message(pair: dict, include_meta: bool = False) -> str:
    """Return Markdown formatted message for a single pair."""
    base = pair.get("baseToken", {}).get("symbol", "")
    quote = pair.get("quoteToken", {}).get("symbol", "")
    name = f"{base}/{quote}".strip("/")
    price = float(pair.get("priceUsd", 0))
    change = float(pair.get("priceChange", {}).get("h1", 0))
    url = pair.get("url", "")
    emoji = "📈" if change > 0 else "📉"

    message = f"{emoji} [{name}]({url})\n💰 ${price:.6f} ({change:+.2f}%)"

    if include_meta:
        volume = float(pair.get("volume", {}).get("h24", 0))
        liquidity = float(pair.get("liquidity", {}).get("usd", 0))
        message += (
            f"\n📊 Volume 24h: ${volume:,.0f}"
            f"\n🔒 Liquidity: ${liquidity:,.0f}"
        )

    return message

