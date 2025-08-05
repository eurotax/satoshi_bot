# === handlers/alerts.py ===

import logging
from telegram import Update
from telegram.ext import ContextTypes
from dex.screener import get_filtered_signals, format_signals_message

logger = logging.getLogger(__name__)


async def signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /signals command - show current signals to user."""
    try:
        # Get filtered signals
        pairs = await get_filtered_signals(limit=5)
        
        if not pairs:
            message = "⚠️ No high-quality signals available right now. Try again later!"
        else:
            message = format_signals_message(pairs, vip=False)
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        
        logger.info(f"Signals command executed for user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"[signals_command] Error: {e}")
        await update.message.reply_text(
            "❌ Failed to fetch signals. Please try again later.",
            parse_mode="Markdown"
        )


async def vip_signals_push(context: ContextTypes.DEFAULT_TYPE):
    """Push VIP signals to VIP channel (every 15 minutes)."""
    await push_signals_to_channel(context, is_vip=True)


async def public_signals_push(context: ContextTypes.DEFAULT_TYPE):
    """Push public signals to public channel (every 8 hours)."""
    await push_signals_to_channel(context, is_vip=False)


async def push_signals_to_channel(context: ContextTypes.DEFAULT_TYPE, is_vip: bool):
    """Generic function to push signals to any channel."""
    try:
        # Get channel ID from job data
        chat_id = context.job.data
        
        # Determine signal count based on channel type
        signal_count = 3 if is_vip else 5
        
        # Fetch filtered signals
        pairs = await get_filtered_signals(limit=signal_count)
        
        if not pairs:
            logger.info(f"No signals to publish to {chat_id}")
            return
        
        # Format message
        message = format_signals_message(pairs, vip=is_vip)
        
        # Send to channel
        await context.bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        
        channel_type = "VIP" if is_vip else "Public"
        logger.info(f"[{channel_type}] Published {len(pairs)} signals to {chat_id}")
        
    except Exception as e:
        channel_type = "VIP" if is_vip else "Public"
        logger.error(f"[{channel_type}] Failed to push signals: {e}")


async def fetch_and_format_signals(context, is_vip=True, include_footer=True):
    """
    DEPRECATED: Legacy function for backward compatibility.
    Use get_filtered_signals() and format_signals_message() instead.
    """
    logger.warning("Using deprecated fetch_and_format_signals(). Please update to use new functions.")
    
    try:
        pairs = await get_filtered_signals(limit=5)
        return format_signals_message(pairs, vip=is_vip)
    except Exception as e:
        logger.error(f"Legacy function error: {e}")
        return "❌ Failed to fetch signals"
