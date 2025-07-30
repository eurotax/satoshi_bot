import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# Wczytaj token z pliku .env lub zmiennej środowiskowej
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Konfiguracja logowania
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Komenda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Witamy w Satoshi Signal Bot!")

# Komenda /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Dostępne komendy:\n/start\n/help\n/vip")

# Komenda /vip
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *Satoshi Signal Lab VIP Access*\n\n"
        "✅ Pełen dostęp do sygnałów\n"
        "✅ Alerty DEX/Binance/KuCoin\n\n"
        "💎 Dołącz do VIP: [Kliknij tutaj](https://t.me/TWOJ_KANAL_VIP)",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# Uruchomienie aplikacji
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("vip", vip))

    app.run_polling()
