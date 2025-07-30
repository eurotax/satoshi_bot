import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ExtBot
)

# Ładujemy zmienne środowiskowe
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Konfiguracja logowania
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Komenda /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsługa komendy /start"""
    try:
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")
        
        welcome_message = (
            f"👋 Witaj w Satoshi Signal Bot, {user.first_name}!\n\n"
            "🔔 Otrzymuj najnowsze sygnały krypto i alerty rynkowe\n"
            "📊 Dostęp do analiz i insights tradingowych\n\n"
            "Wpisz /help aby zobaczyć dostępne komendy"
        )
        
        await update.message.reply_text(welcome_message)
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await update.message.reply_text("Wystąpił błąd. Spróbuj ponownie.")

# Komenda /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsługa komendy /help"""
    try:
        help_text = (
            "📋 *Dostępne Komendy:*\n\n"
            "/start - Uruchom bota i zobacz wiadomość powitalną\n"
            "/help - Pokaż tę wiadomość pomocy\n" 
            "/vip - Informacje o dostępie VIP\n"
            "/status - Sprawdź status bota\n\n"
            "Potrzebujesz więcej pomocy? Skontaktuj się z supportem!"
        )
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await update.message.reply_text("Wystąpił błąd. Spróbuj ponownie.")

# Komenda /vip
async def vip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsługa komendy /vip"""
    try:
        vip_message = (
            "🚀 *Satoshi Signal Lab - Dostęp VIP*\n\n"
            "✅ Pełny dostęp do wszystkich premium sygnałów\n"
            "✅ Alerty DEX / Binance / KuCoin\n"
            "✅ Analiza rynku w czasie rzeczywistym\n"
            "✅ Prywatna społeczność VIP\n"
            "✅ Wsparcie 24/7\n\n"
            "💎 Dołącz do VIP: [Kliknij tutaj](https://t.me/YOUR_VIP_CHANNEL)\n"
            "💰 Dostępne specjalne ceny!"
        )
        
        await update.message.reply_text(
            vip_message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Error in vip command: {e}")
        await update.message.reply_text("Wystąpił błąd. Spróbuj ponownie.")

# Komenda /status
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Obsługa komendy /status"""
    try:
        await update.message.reply_text(
            "🟢 Bot działa sprawnie!\n"
            "📡 Wszystkie systemy operacyjne"
        )
    except Exception as e:
        logger.error(f"Error in status command: {e}")
        await update.message.reply_text("Wystąpił błąd przy sprawdzaniu statusu.")

# Handler błędów
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Loguje błędy spowodowane przez aktualizacje."""
    logger.error(f"Exception while handling an update: {context.error}")

# Główna funkcja uruchamiająca bota
def main():
    """Uruchom bota"""
    # Sprawdzenie czy token istnieje
    if not TOKEN:
        logger.error("BOT_TOKEN nie został znaleziony w zmiennych środowiskowych!")
        print("Błąd: BOT_TOKEN nie został ustawiony!")
        return
    
    logger.info("Uruchamianie Satoshi Signal Bot...")
    
    try:
        # Tworzenie aplikacji z poprawioną konfiguracją
        application = Application.builder().token(TOKEN).build()
        
        # Dodawanie handlerów komend
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("vip", vip))
        application.add_handler(CommandHandler("status", status))
        
        # Dodawanie handlera błędów
        application.add_error_handler(error_handler)
        
        logger.info("Bot uruchomiony pomyślnie!")
        print("Bot uruchomiony! Naciśnij Ctrl+C aby zatrzymać.")
        
        # Uruchomienie bota
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
    except Exception as e:
        logger.error(f"Błąd podczas uruchamiania bota: {e}")
        print(f"Błąd krytyczny: {e}")

if __name__ == "__main__":
    main()
