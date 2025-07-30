import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to Satoshi Signal Lab 🚀\n\n"
                                    "Use /help to see available commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Available commands:\n"
        "/start – Welcome message\n"
        "/help – Show this help\n"
        "/free – Get today’s free signal\n"
        "/subscribe – Info about the premium channel"
    )

async def free_signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 Today's free signal:\n\n"
                                    "TOKEN: $XYZ\nBUY ZONE: 0.0012–0.0016\nTARGET: 0.0025\nSTOP-LOSS: 0.0009\n\n"
                                    "🚨 Remember: DYOR!")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Unlock access to our Premium Channel!\n\n"
                                    "Get 3–5 daily signals, DEX alerts, pre-market token picks, and more.\n\n"
                                    "Visit: https://t.me/+your_vip_channel_link")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("free", free_signal))
    app.add_handler(CommandHandler("subscribe", subscribe))

    app.run_polling()
