import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Welcome to Satoshi Signal Bot!")

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Available commands:\n/start\n/help\n/vip")

# /vip command
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *Satoshi Signal Lab VIP Access*\n\n"
        "✅ Full access to all signals\n"
        "✅ DEX / Binance / KuCoin alerts\n\n"
        "💎 Join VIP now: [Click here](https://t.me/YOUR_VIP_CHANNEL)",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# Start the bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("vip", vip))

    app.run_polling()
