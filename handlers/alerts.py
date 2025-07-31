# === handlers/alerts.py ===

import logging
import httpx
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

API_URL = "https://api.dexscreener.com/latest/dex/pairs/solana"

# Komenda /signals (dla użytkowników)
async def signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = await fetch_and_format_signals(context, include_footer=True)
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"[signals_command] {e}")
        await update.message.reply_text("⚠️ Failed to fetch signals.")

# Automatyczna publikacja na kanałach
async def vip_signals_push(context: ContextTypes.DEFAULT_TYPE):
    await push_signals_to_channel(context, is_vip=True)

async def public_signals_push(context: ContextTypes.DEFAULT_TYPE):
    await push_signals_to_channel(context, is_vip=False)

# Publikacja do kanału
async def push_signals_to_channel(context: ContextTypes.DEFAULT_TYPE, is_vip: bool):
    try:
        chat_id = context.job.data
        message = await fetch_and_format_signals(context, is_vip=is_vip, include_footer=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info(f"[{chat_id}] Signals sent.")
    except Exception as e:
        logger.error(f"[push_signals_to_channel] {e}")

# Pobierz i przygotuj wiadomość
async def fetch_and_format_signals(context, is_vip=True, include_footer=True):
    async with httpx.AsyncClient() as client:
        response = await client.get(API_URL, timeout=10)
        data = response.json()

    pairs = data.get("pairs", [])[:5]
    message = "💎 *VIP SIGNALS*\n\n" if is_vip else "📊 *Market Update*\n\n"

    for pair in pairs:
        base = pair["baseToken"]["symbol"]
        quote = pair["quoteToken"]["symbol"]
        name = f"{base}/{quote}"
        price = pair["priceUsd"]
        change = pair["priceChange"]["h1"]
        link = pair["url"]
        emoji = "📈" if float(change) > 0 else "📉"
        message += f"{emoji} [{name}]({link})\n💰 ${price} ({change}%)\n\n"

    if include_footer:
        if is_vip:
            message += "🧠 *Exclusive analysis for VIP members only!*"
        else:
            message += "🔔 Join [VIP Channel](https://t.me/+sR2qa2jnr6o5MDk0) for real-time alerts."

    return message
