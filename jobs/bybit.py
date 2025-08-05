# === jobs/bybit.py ===

"""Background task that publishes Bybit pump/dump alerts."""

import logging
from telegram.ext import ContextTypes
from config import BYBIT_SYMBOLS, BYBIT_ALERT_PERCENT, VIP_CHANNEL_ID
from bybit.signals import fetch_ticker, extract_change_pct, format_alert

logger = logging.getLogger(__name__)


async def bybit_alert_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    for symbol in BYBIT_SYMBOLS:
        ticker = await fetch_ticker(symbol)
        if not ticker:
            continue
        change = extract_change_pct(ticker)
        if abs(change) < BYBIT_ALERT_PERCENT:
            continue
        try:
            last_price = float(ticker.get("lastPrice", 0))
        except Exception:
            last_price = 0.0
        message = format_alert(symbol, last_price, change)
        try:
            await context.bot.send_message(VIP_CHANNEL_ID, message)
        except Exception as exc:
            logger.error("[bybit] Failed to send alert: %s", exc)
