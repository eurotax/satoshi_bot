import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
import httpx
import asyncio

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")

        welcome_message = (
            f"👋 Welcome to Satoshi Signal Bot!\n\n"
            "🔔 Get the latest crypto signals and market alerts\n"
            "📊 Access real-time insights and analysis\n\n"
            "Type /help to view available commands"
        )

        await update.message.reply_text(welcome_message)
    except Exception as e:
        logger.error(f"Error in /start: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        help_text = (
            "📋 *Available Commands:*\n\n"
            "/start - Start the bot and receive a welcome message\n"
            "/help - Show this help message\n"
            "/vip - Info about VIP access\n"
            "/status - Check bot status\n"
            "/signals - Get current market signals\n\n"
            "Need more help? Contact our support team!"
        )

        await update.message.reply_text(help_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in /help: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

# /vip command
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        vip_message = (
            "🚀 *Satoshi Signal Lab - VIP Access*\n\n"
            "✅ Full access to all premium signals\n"
            "✅ DEX / Binance / KuCoin alerts\n"
            "✅ Real-time market analysis\n"
            "✅ Private VIP community\n"
            "✅ 24/7 Support\n\n"
            "💎 Join VIP: [Click here](https://t.me/YOUR_VIP_CHANNEL)\n"
            "💰 Special pricing available!"
        )

        await update.message.reply_text(vip_message, parse_mode='Markdown', disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in /vip: {e}")
        await update.message.reply_text("An error occurred. Please try again.")

# /status command
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🟢 Bot is running!\n📡 All systems operational")
    except Exception as e:
        logger.error(f"Error in /status: {e}")
        await update.message.reply_text("Error while checking status.")

# /signals command (live integration)
async def signals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        url = "https://api.dexscreener.com/latest/dex/pairs/solana"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
            data = response.json()
        
        signals = data["pairs"][:5]
        message = "*Top 5 Solana Pairs on DEXScreener:*\n\n"
        for pair in signals:
            name = pair["baseToken"]["symbol"] + "/" + pair["quoteToken"]["symbol"]
            price = pair["priceUsd"]
            change = pair["priceChange"]["h1"]
            link = pair["url"]
            message += f"🔹 [{name}]({link}) - ${price} ({change}%)\n"

        await update.message.reply_text(message, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Error in /signals: {e}")
        await update.message.reply_text("Failed to fetch signals.")

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception while handling update: {context.error}")

# Main function
def main():
    if not TOKEN:
        logger.error("BOT_TOKEN is not set in environment variables!")
        print("Error: BOT_TOKEN is missing!")
        return

    logger.info("Starting Satoshi Signal Bot...")

    try:
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("vip", vip))
        application.add_handler(CommandHandler("status", status))
        application.add_handler(CommandHandler("signals", signals))

        application.add_error_handler(error_handler)

        logger.info("Bot started successfully.")
        print("Bot is running. Press Ctrl+C to stop.")

        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except Exception as e:
        logger.error(f"Startup error: {e}")
        print(f"Critical error: {e}")

if __name__ == "__main__":
    main()
