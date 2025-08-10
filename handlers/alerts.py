# === handlers/alerts.py - NAPRAWIONY Z RETRY LOGIC ===
# Zastąp zawartość tego pliku

import logging
import asyncio
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from telegram import Update
from telegram.ext import ContextTypes
from dex.screener import get_filtered_signals, format_signals_message
from safe_utils import log_function_call

logger = logging.getLogger(__name__)

class EnhancedSignalHandler:
    """
    🛡️ NAPRAWIA: Signal delivery failures
    Robust signal handling z comprehensive error recovery
    """
    
    @staticmethod
    async def fetch_signals_with_retry(limit: int = 5, max_attempts: int = 3) -> Optional[List[Dict[str, Any]]]:
        """
        🔄 NAPRAWIA: Empty signals due to API failures
        Multi-attempt signal fetching z backoff
        """
        for attempt in range(max_attempts):
            try:
                logger.debug(f"Fetching signals, attempt {attempt + 1}/{max_attempts}")
                
                # Add small delay between attempts
                if attempt > 0:
                    delay = 2 ** attempt  # Exponential backoff
                    logger.info(f"⏳ Waiting {delay}s before retry...")
                    await asyncio.sleep(delay)
                
                signals = await get_filtered_signals(limit=limit)
                
                if signals:
                    logger.info(f"✅ Fetched {len(signals)} signals on attempt {attempt + 1}")
                    return signals
                else:
                    logger.warning(f"⚠️ No signals returned on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.warning(f"❌ Attempt {attempt + 1} failed: {e}")
                
                if attempt == max_attempts - 1:
                    logger.error(f"💥 All {max_attempts} attempts failed")
                    return None
        
        return None
    
    @staticmethod
    async def send_message_with_retry(context, chat_id: str, message: str, max_attempts: int = 3) -> bool:
        """
        📤 NAPRAWIA: Message delivery failures
        Retry logic for Telegram message sending
        """
        for attempt in range(max_attempts):
            try:
                if attempt > 0:
                    delay = min(2 ** attempt, 10)  # Max 10 seconds delay
                    logger.info(f"⏳ Retrying message send in {delay}s...")
                    await asyncio.sleep(delay)
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode="Markdown",
                    disable_web_page_preview=True,
                    read_timeout=30,
                    write_timeout=30
                )
                
                logger.info(f"✅ Message sent successfully on attempt {attempt + 1}")
                return True
                
            except Exception as e:
                logger.warning(f"❌ Message send attempt {attempt + 1} failed: {e}")
                
                # Handle specific Telegram errors
                error_str = str(e).lower()
                if "flood" in error_str or "too many" in error_str:
                    # Rate limit hit - wait longer
                    await asyncio.sleep(60)
                elif "chat not found" in error_str:
                    # Chat doesn't exist - don't retry
                    logger.error(f"💥 Chat {chat_id} not found - stopping retries")
                    return False
                elif "bot was blocked" in error_str:
                    # Bot blocked - don't retry
                    logger.error(f"💥 Bot blocked in chat {chat_id}")
                    return False
        
        logger.error(f"💥 Failed to send message after {max_attempts} attempts")
        return False
    
    @staticmethod
    def validate_message_content(message: str) -> bool:
        """
        ✅ NAPRAWIA: Invalid messages causing Telegram errors
        """
        if not message or len(message.strip()) < 10:
            return False
        
        # Check for basic required content
        required_indicators = ["📈", "📉", "💰", "📊"]
        if not any(indicator in message for indicator in required_indicators):
            return False
        
        # Check message length (Telegram limit is 4096 chars)
        if len(message) > 4000:  # Leave some buffer
            return False
        
        return True

@log_function_call
async def signals_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    🎯 NAPRAWIONY /signals command
    Enhanced error handling i user feedback
    """
    user_id = update.effective_user.id if update.effective_user else "unknown"
    chat_id = update.effective_chat.id
    
    try:
        logger.info(f"👤 /signals command from user {user_id}")
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # Fetch signals with retry
        pairs = await EnhancedSignalHandler.fetch_signals_with_retry(limit=5, max_attempts=3)
        
        if not pairs:
            message = (
                "⚠️ *Brak sygnałów*\n\n"
                "Nie mogę pobrać sygnałów wysokiej jakości w tym momencie.\n"
                "Spróbuj ponownie za kilka minut.\n\n"
                "💡 *Możliwe przyczyny:*\n"
                "• Niska aktywność na rynku\n"
                "• Problemy z API\n"
                "• Wszystkie pary nie spełniają kryteriów jakości"
            )
        else:
            message = format_signals_message(pairs, vip=False)
        
        # Validate message before sending
        if not EnhancedSignalHandler.validate_message_content(message):
            message = "❌ Błąd formatowania sygnałów. Spróbuj ponownie za chwilę."
        
        # Send with retry
        success = await EnhancedSignalHandler.send_message_with_retry(
            context, chat_id, message, max_attempts=2
        )
        
        if success:
            logger.info(f"✅ Successfully responded to /signals for user {user_id}")
        else:
            logger.error(f"💥 Failed to respond to /signals for user {user_id}")
        
    except Exception as e:
        logger.error(f"💥 Critical error in signals_command for user {user_id}: {e}", exc_info=True)
        
        # Fallback error message
        try:
            await update.message.reply_text(
                "❌ Wystąpił nieoczekiwany błąd.\n"
                "Bot automatycznie się naprawia. Spróbuj ponownie za chwilę.",
                timeout=10
            )
        except Exception as fallback_error:
            logger.error(f"💥 Even fallback failed: {fallback_error}")

@log_function_call
async def vip_signals_push(context: ContextTypes.DEFAULT_TYPE):
    """
    💎 Enhanced VIP signals push
    """
    await _enhanced_signal_push(
        context=context,
        is_vip=True,
        signal_count=3,
        channel_name="VIP"
    )

@log_function_call
async def public_signals_push(context: ContextTypes.DEFAULT_TYPE):
    """
    📊 Enhanced public signals push
    """
    await _enhanced_signal_push(
        context=context,
        is_vip=False,
        signal_count=5,
        channel_name="Public"
    )

async def _enhanced_signal_push(context: ContextTypes.DEFAULT_TYPE, is_vip: bool, signal_count: int, channel_name: str):
    """
    🚀 NAPRAWIONY: Core signal pushing with comprehensive monitoring
    """
    start_time = time.time()
    
    try:
        # Get channel ID from job context
        chat_id = context.job.data
        
        logger.info(f"📤 Starting {channel_name} signal push to {chat_id}")
        
        # Validate chat_id
        if not chat_id:
            logger.error(f"💥 No chat_id provided for {channel_name} push")
            return
        
        # Fetch signals with enhanced retry
        signals = await EnhancedSignalHandler.fetch_signals_with_retry(
            limit=signal_count, 
            max_attempts=3
        )
        
        if not signals:
            logger.warning(f"⚠️ No signals available for {channel_name} push")
            # Don't send empty messages to channels
            return
        
        # Format message
        message = format_signals_message(signals, vip=is_vip)
        
        # Validate message content
        if not EnhancedSignalHandler.validate_message_content(message):
            logger.error(f"💥 Invalid message content for {channel_name} push")
            return
        
        # Send with retry
        success = await EnhancedSignalHandler.send_message_with_retry(
            context, chat_id, message, max_attempts=3
        )
        
        # Log results with metrics
        execution_time = time.time() - start_time
        
        if success:
            logger.info(
                f"✅ [{channel_name}] Published {len(signals)} signals to {chat_id} "
                f"in {execution_time:.2f}s"
            )
            
            # Log signal details for monitoring
            signal_details = []
            for signal in signals:
                base_token = signal.get('baseToken', {})
                price_change = signal.get('priceChange', {})
                signal_details.append({
                    'symbol': base_token.get('symbol', 'Unknown'),
                    'price_change_1h': price_change.get('h1', 0),
                    'volume_24h': signal.get('volume', {}).get('h24', 0)
                })
            
            logger.debug(f"📊 {channel_name} signal details: {signal_details}")
            
        else:
            logger.error(
                f"💥 [{channel_name}] Failed to publish signals to {chat_id} "
                f"after {execution_time:.2f}s"
            )
        
    except Exception as e:
        execution_time = time.time() - start_time
        logger.error(
            f"💥 [{channel_name}] Critical error in signal push after {execution_time:.2f}s: {e}",
            exc_info=True
        )

# Legacy compatibility functions (keep for backward compatibility)
async def fetch_and_format_signals(context, is_vip=True, include_footer=True):
    """
    ⚠️ DEPRECATED: Use new functions above
    Kept for backward compatibility only
    """
    logger.warning("📝 Using deprecated function fetch_and_format_signals")
    
    try:
        pairs = await EnhancedSignalHandler.fetch_signals_with_retry(limit=5)
        if pairs:
            return format_signals_message(pairs, vip=is_vip)
        else:
            return "⚠️ Brak dostępnych sygnałów"
    except Exception as e:
        logger.error(f"💥 Legacy function error: {e}")
        return "❌ Błąd podczas pobierania sygnałów"

# Health check for signals system
async def signals_health_check() -> Dict[str, Any]:
    """
    🏥 Health check for signals system
    Returns status of signal generation capability
    """
    start_time = time.time()
    
    try:
        # Test signal fetching
        test_signals = await EnhancedSignalHandler.fetch_signals_with_retry(limit=1, max_attempts=1)
        
        execution_time = time.time() - start_time
        
        return {
            'status': 'healthy' if test_signals else 'degraded',
            'signals_available': len(test_signals) if test_signals else 0,
            'response_time_seconds': execution_time,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        execution_time = time.time() - start_time
        return {
            'status': 'unhealthy',
            'error': str(e),
            'response_time_seconds': execution_time,
            'timestamp': datetime.now().isoformat()
        }
