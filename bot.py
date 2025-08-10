# === bot.py - NAPRAWIONY GŁÓWNY PLIK ===
# Zastąp zawartość tego pliku

import logging
import os
import asyncio
import signal
import gc
import time
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from handlers.commands import (
    start_command, help_command, vip_command, status_command,
)
from handlers.alerts import signals_command, vip_signals_push, public_signals_push
from config import VIP_CHANNEL_ID, PUBLIC_CHANNEL_ID

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")

# Enhanced logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class MemorySafeJobManager:
    """
    🛡️ NAPRAWIA: Memory leaks w job queue
    PRZED: Jobs accumulate in memory → crash after few hours
    PO: Automatic cleanup → stable memory usage
    """
    def __init__(self):
        self.jobs = {}
        self.max_jobs = 20  # Reasonable limit
        self.last_cleanup = time.time()
        self.cleanup_interval = 600  # 10 minutes
    
    def add_job(self, job_queue, callback, interval: int, first: int, data: any, name: str):
        """Add job with automatic memory management"""
        try:
            # Cleanup old jobs first
            self._maybe_cleanup()
            
            # Check limits
            if len(self.jobs) >= self.max_jobs:
                logger.warning(f"Too many jobs ({len(self.jobs)}), cleaning up")
                self._force_cleanup()
            
            # Add new job
            job = job_queue.run_repeating(
                callback=callback,
                interval=interval,
                first=first,
                data=data,
                name=name
            )
            
            self.jobs[name] = {
                'job': job,
                'created': time.time(),
                'callback': callback.__name__
            }
            
            logger.info(f"✅ Job '{name}' added. Active jobs: {len(self.jobs)}")
            return job
            
        except Exception as e:
            logger.error(f"❌ Failed to add job '{name}': {e}")
            raise
    
    def _maybe_cleanup(self):
        """Cleanup if needed"""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            self._cleanup_completed_jobs()
            self.last_cleanup = now
    
    def _cleanup_completed_jobs(self):
        """Remove completed jobs"""
        completed = []
        for name, info in self.jobs.items():
            job = info['job']
            if hasattr(job, 'removed') and job.removed:
                completed.append(name)
        
        for name in completed:
            del self.jobs[name]
            
        if completed:
            logger.info(f"🧹 Cleaned up {len(completed)} completed jobs")
            gc.collect()  # Force garbage collection
    
    def _force_cleanup(self):
        """Force cleanup of old jobs"""
        now = time.time()
        old_jobs = []
        
        for name, info in self.jobs.items():
            age = now - info['created']
            if age > 3600:  # Older than 1 hour
                old_jobs.append(name)
        
        for name in old_jobs:
            try:
                info = self.jobs[name]
                info['job'].schedule_removal()
                del self.jobs[name]
                logger.info(f"🗑️ Removed old job: {name}")
            except Exception as e:
                logger.warning(f"Failed to remove job {name}: {e}")
        
        gc.collect()
    
    def get_stats(self):
        """Get job statistics"""
        active = sum(1 for info in self.jobs.values() 
                    if not (hasattr(info['job'], 'removed') and info['job'].removed))
        return {
            'total_jobs': len(self.jobs),
            'active_jobs': active,
            'last_cleanup': self.last_cleanup
        }

class SafeBotApplication:
    """
    🚀 NAPRAWIA: Bot crashes and instability
    Comprehensive error handling and recovery
    """
    def __init__(self):
        self.application: Optional[Application] = None
        self.job_manager = MemorySafeJobManager()
        self._shutdown_event = asyncio.Event()
        self._running = False
        self._start_time = time.time()
    
    def _validate_webhook_url(self, url: str) -> bool:
        """Enhanced webhook validation"""
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            
            if parsed.scheme not in ("http", "https"):
                logger.warning(f"Invalid webhook scheme: {parsed.scheme}")
                return False
            
            if not parsed.netloc:
                logger.warning("Empty webhook netloc")
                return False
            
            # Security check
            if parsed.hostname in ('localhost', '127.0.0.1'):
                if os.getenv('ENVIRONMENT') == 'production':
                    logger.error("Localhost webhook in production")
                    return False
                logger.info("Localhost webhook allowed in development")
            
            return True
            
        except Exception as e:
            logger.error(f"Webhook validation error: {e}")
            return False
    
    async def _enhanced_error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        🛡️ NAPRAWIA: Unhandled errors crashing bot
        """
        logger.error("🚨 BOT ERROR DETECTED", exc_info=context.error)
        
        # Collect error context
        error_info = {
            'error_type': type(context.error).__name__,
            'error_message': str(context.error),
            'timestamp': datetime.now().isoformat(),
            'uptime_minutes': (time.time() - self._start_time) / 60
        }
        
        if isinstance(update, Update):
            error_info.update({
                'user_id': update.effective_user.id if update.effective_user else 'unknown',
                'chat_id': update.effective_chat.id if update.effective_chat else 'unknown',
                'message': update.message.text if update.message else 'no_message'
            })
        
        logger.error(f"Error context: {error_info}")
        
        # Try to notify user
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ Wystąpił błąd. Bot automatycznie się naprawia.\n"
                    "Spróbuj ponownie za chwilę.",
                    timeout=10
                )
            except Exception as notify_error:
                logger.error(f"Failed to notify user: {notify_error}")
        
        # Memory cleanup on critical errors
        if isinstance(context.error, MemoryError):
            logger.critical("🧨 MEMORY ERROR - forcing cleanup")
            gc.collect()
            
            # If still critical, try to restart
            if self._get_memory_usage() > 1024:  # Over 1GB
                logger.critical("Memory still high, initiating restart")
                await self._graceful_shutdown()
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            return psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0  # psutil not available
    
    async def _setup_signal_handlers(self):
        """Setup graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"📡 Signal {signum} received, shutting down...")
            asyncio.create_task(self._graceful_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _graceful_shutdown(self):
        """Clean shutdown procedure"""
        logger.info("🛑 Starting graceful shutdown...")
        
        try:
            # Stop application
            if self.application:
                await self.application.stop()
                logger.info("✅ Application stopped")
            
            # Cleanup HTTP connections
            try:
                from dex.screener import cleanup
                await cleanup()
                logger.info("✅ HTTP connections closed")
            except Exception as e:
                logger.warning(f"HTTP cleanup error: {e}")
            
            # Force garbage collection
            gc.collect()
            logger.info("✅ Memory cleanup completed")
            
            self._shutdown_event.set()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            logger.info("🔚 Graceful shutdown completed")
    
    async def _memory_monitor(self):
        """Background memory monitoring"""
        while self._running:
            try:
                memory_mb = self._get_memory_usage()
                uptime_hours = (time.time() - self._start_time) / 3600
                
                # Log memory stats every hour
                if int(uptime_hours) != int(uptime_hours - 0.0167):  # Every hour
                    job_stats = self.job_manager.get_stats()
                    logger.info(
                        f"📊 Bot
