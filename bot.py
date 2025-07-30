import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(level=logging.INFO)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Satoshi Signal Bot!\n\n"
        "Use /help to view available commands."
    )

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Welcome message\n"
        "/help - Show this help menu\n"
        "/vip - Info about VIP access"
    )

# /vip command
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 *Satoshi Signal Lab VIP Access*\n\n"
        "✅ Full access to all trading signals\n"
        "✅ Real-time alerts on DEXScanner / Binance / KuCoin\n"
        "✅ Early info about new tokens & sniper activity\n\n"
        "💎 Join VIP now: [Access VIP Channel](https://t.me/YOUR_VIP_CHANNEL_LINK)\n"
        "_Or complete your subscription to unlock VIP access._",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# Run the bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("vip", vip))
    app.run_polling()
