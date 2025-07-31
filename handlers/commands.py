# === handlers/commands.py ===

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) issued /start")

        welcome = (
            f"👋 Welcome to *Satoshi Signal Bot*, {user.first_name}!\n\n"
            "🔔 Get real-time DEX trading signals\n"
            "📈 Discover trending tokens early\n"
            "💬 Type /help to see available commands."
        )

        await update.message.reply_text(welcome, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"/start error: {e}")
        await update.message.reply_text("❌ Failed to process /start command.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        help_text = (
            "📋 *Available Commands:*\n\n"
            "/start - Start the bot and get welcome info\n"
            "/help - Show this help message\n"
            "/signals - Get real-time filtered DEX signals\n"
            "/vip - Learn about VIP access and benefits\n"
            "/status - Check if the bot is active"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"/help error: {e}")
        await update.message.reply_text("❌ Failed to process /help command.")


async def vip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = (
            "💎 *VIP Membership Info:*\n\n"
            "✅ Full access to high-volume filtered signals\n"
            "✅ Instant alerts from DEX pairs\n"
            "✅ Market sentiment and token quality checks\n"
            "✅ Community & support access\n\n"
            "👉 Join now: [VIP Channel](https://t.me/+sR2qa2jnr6o5MDk0)"
        )
        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"/vip error: {e}")
        await update.message.reply_text("❌ Failed to process /vip command.")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("✅ Bot is active and monitoring DEX pairs.")
    except Exception as e:
        logger.error(f"/status error: {e}")
        await update.message.reply_text("❌ Unable to verify bot status.")
