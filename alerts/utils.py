import logging

logger = logging.getLogger(__name__)

def format_signal_message(pair: dict) -> str:
    """Format a single pair from DEX Screener into a Telegram markdown message."""
    try:
        name = f"{pair['baseToken']['symbol']}/{pair['quoteToken']['symbol']}"
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
    except Exception as e:
        logger.error(f"[format_signal_message] Failed to format pair: {e}")
        return ""
