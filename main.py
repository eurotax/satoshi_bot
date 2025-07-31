# === main.py ===

import logging
from telegram.ext import Application
from telegram.ext import CommandHandler
from handlers.commands import start, help_command, vip, status, signals
from jobs.scheduler import schedule_jobs
from config import VIP_CHANNEL_ID, PUBLIC_CHANNEL_ID
from dotenv import load_dotenv
import os

# Wczytaj zmienne środowiskowe
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Konfiguracja logowania
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    if not TOKEN:
        logger.error("Brak BOT_TOKEN w zmiennych środowiskowych")
        print("❌ BOT_TOKEN nie został ustawiony w .env")
        return

    logger.info("Uruchamianie Satoshi Signal Bot...")
    print("🚀 Start bota...")

    application = Application.builder().token(TOKEN).build()

    # Rejestracja komend
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("vip", vip))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("signals", signals))

    # Harmonogram publikacji
    schedule_jobs(application.job_queue)

    logger.info("✅ Bot uruchomiony pomyślnie")
    print("✅ Bot nasłuchuje. Wciśnij Ctrl+C aby zatrzymać.")

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "edited_message", "channel_post"]
    )


if __name__ == "__main__":
    main()
