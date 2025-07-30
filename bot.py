import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Satoshi Signal Lab! 🚀")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start – Welcome\n"
        "/help – Show this help\n"
        "/free – Today's free signal\n"
        "/subscribe – Info about premium access"
    )

async def free_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📈 Free Signal:\n"
        "TOKEN: $XYZ\n"
        "Buy zone: 0.0012–0.0016\n"
        "Target: 0.0025\n"
        "Stop-loss: 0.0009"
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 Premium Access:\n"
        "• 3–5 signals/day\n"
        "• DEX alerts\n"
        "• Presale analysis\n\n"
        "Join: https://t.me/your_vip_channel"
    )

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("free", free_signal))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.run_polling()
