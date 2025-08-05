# === bot.py ===

import logging
import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler

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


def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set in .env file")
        return

    application = Application.builder().token(BOT_TOKEN).build()

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

    logger.info("Bot started. Use Ctrl+C to stop.")

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
            )
        else:
            logger.error("Invalid WEBHOOK_URL '%s'. Falling back to polling mode.", webhook_url)
            application.run_polling(allowed_updates=None)
    else:
        application.run_polling(allowed_updates=None)


if __name__ == "__main__":
    main()

