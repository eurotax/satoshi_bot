import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)

# Importujemy dodatkowe moduły dla lepszej funkcjonalności

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command"""
    user = update.effective_user
    logger.info(f"User {user.id} ({user.username}) started the bot")
    
    welcome_message = (
        f"👋 Welcome to Satoshi Signal Bot, {user.first_name}!\n\n"
        "🔔 Get the latest crypto signals and market alerts\n"
        "📊 Access trading insights and analysis\n\n"
        "Type /help to see available commands"
    )
    
    await update.message.reply_text(welcome_message)

# /help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /help command"""
    help_text = (
        "📋 *Available Commands:*\n\n"
        "/start - Start the bot and see welcome message\n"
        "/help - Show this help message\n" 
        "/vip - Get information about VIP access\n"
        "/status - Check bot status\n\n"
        "Need more help? Contact support!"
    )
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown'
    )

# /vip command
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /vip command"""
    vip_message = (
        "🚀 *Satoshi Signal Lab VIP Access*\n\n"
        "✅ Full access to all premium signals\n"
        "✅ DEX / Binance / KuCoin alerts\n"
        "✅ Real-time market analysis\n"
        "✅ Private VIP community\n"
        "✅ 24/7 support\n\n"
        "💎 Join VIP now: [Click here](https://t.me/YOUR_VIP_CHANNEL)\n"
        "💰 Special pricing available!"
    )
    
    await update.message.reply_text(
        vip_message,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# /status command
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /status command"""
    await update.message.reply_text(
        "🟢 Bot is running smoothly!\n"
        "📡 All systems operational"
    )

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by Updates."""
    logger.error(f"Exception while handling an update: {context.error}")

# Start the bot
def main():
    """Start the bot"""
    if not TOKEN:
        logger.error("BOT_TOKEN not found in environment variables!")
        return
    
    logger.info("Starting Satoshi Signal Bot...")
    
    # Create application
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("vip", vip))
    app.add_handler(CommandHandler("status", status))
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    logger.info("Bot started successfully!")
    
    # Run the bot
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
