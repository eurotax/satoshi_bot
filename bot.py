# === bot.py === 

import logging
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from handlers.commands import (
    start_command,
    help_command,
    vip_command,
    status_command,
)
from handlers.alerts import signals_command, vip_signals_push, public_signals_push
from config import VIP_CHANNEL_ID, PUBLIC_CHANNEL_ID

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def _is_valid_webhook(url: str) -> bool:
    """Validate webhook URL format."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        if not parsed.netloc:
            return False
        # Accessing port property validates the port if provided
        _ = parsed.port
        return True
    except Exception:
        return False


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors that occur in the bot."""
    logger.error("Exception while handling an update:", exc_info=context.error)
    
    # Send error message to user if possible
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Wystąpił błąd. Spróbuj ponownie za chwilę."
            )
        except Exception:
            pass


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set in .env file")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    # Add error handler - WAŻNE!
    application.add_error_handler(error_handler)

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("vip", vip_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("signals", signals_command))

    # Schedule automatic signal publishing
    application.job_queue.run_repeating(
        vip_signals_push,
        interval=900,  # 15 minutes
        first=60,
        data=VIP_CHANNEL_ID,
        name="vip_signals"
    )

    application.job_queue.run_repeating(
        public_signals_push,
        interval=28800,  # 8 hours
        first=300,
        data=PUBLIC_CHANNEL_ID,
        name="public_signals"
    )

    logger.info("Bot started successfully")

    # Check for webhook mode - PREFERUJ WEBHOOK na Render
    webhook_url = os.getenv("WEBHOOK_URL")
    if webhook_url:
        if _is_valid_webhook(webhook_url):
            path = f"/{BOT_TOKEN}"
            listen_port = int(os.getenv("PORT", 8443))
            logger.info("Starting webhook at %s", webhook_url)
            application.run_webhook(
                listen="0.0.0.0",
                port=listen_port,
                url_path=path,
                webhook_url=f"{webhook_url}{path}",
                allowed_updates=None,
                drop_pending_updates=True,  # WAŻNE: usuń pending updates
            )
        else:
            logger.error("Invalid WEBHOOK_URL '%s'. Falling back to polling mode.", webhook_url)
            application.run_polling(
                allowed_updates=None,
                drop_pending_updates=True  # WAŻNE: usuń pending updates
            )
    else:
        logger.info("Starting polling mode")
        application.run_polling(
            allowed_updates=None,
            drop_pending_updates=True  # WAŻNE: usuń pending updates
        )


if __name__ == "__main__":
    main()
