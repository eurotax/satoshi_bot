"""Background publishing utilities for Telegram alerts."""

import logging
from telegram.ext import ContextTypes
from dex.screener import get_filtered_signals, format_signals_message
from config import VIP_CHANNEL_ID

logger = logging.getLogger(__name__)


async def build_message(vip: bool) -> str:
    """Fetch pairs from DEXScreener and format them for Telegram."""
    pairs = await get_filtered_signals()
    return format_signals_message(pairs, vip)


async def publish_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback to publish signals to a channel."""
    try:
        channel_id = context.job.data
        vip = channel_id == VIP_CHANNEL_ID
        message = await build_message(vip)
        if not message:
            logger.info("No message generated for %s", channel_id)
            return
        await context.bot.send_message(
            chat_id=channel_id,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        logger.info("Signals published to %s", channel_id)
    except Exception as exc:
        logger.error("Publishing job failed: %s", exc)
