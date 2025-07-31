# === utils.py ===

import httpx
import logging
from config import MIN_VOLUME, MIN_LIQUIDITY, MIN_PRICE_CHANGE

logger = logging.getLogger(__name__)


async def fetch_dex_data():
    """Fetch top Solana pairs from DEXScreener"""
    url = "https://api.dexscreener.com/latest/dex/pairs/solana"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("pairs", [])
    except Exception as e:
        logger.error(f"Error fetching DEX data: {e}")
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


# === handlers/alerts.py ===

from telegram import Update
from telegram.ext import ContextTypes
from utils import fetch_dex_data, filter_signals, format_signals
import logging

logger = logging.getLogger(__name__)


async def signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        raw_pairs = await fetch_dex_data()
        filtered = filter_signals(raw_pairs)
        message = format_signals(filtered, vip=False)
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"/signals command error: {e}")
        await update.message.reply_text("❌ Failed to fetch signals.")


async def vip_signals_push(context: ContextTypes.DEFAULT_TYPE):
    try:
        channel_id = context.job.data
        raw_pairs = await fetch_dex_data()
        filtered = filter_signals(raw_pairs)
        message = format_signals(filtered, vip=True)
        await context.bot.send_message(
            chat_id=channel_id,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info(f"Sent VIP signals to {channel_id}")
    except Exception as e:
        logger.error(f"Error in VIP signal push: {e}")


async def public_signals_push(context: ContextTypes.DEFAULT_TYPE):
    try:
        channel_id = context.job.data
        raw_pairs = await fetch_dex_data()
        filtered = filter_signals(raw_pairs)
        message = format_signals(filtered, vip=False)
        await context.bot.send_message(
            chat_id=channel_id,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info(f"Sent public signals to {channel_id}")
    except Exception as e:
        logger.error(f"Error in public signal push: {e}")

