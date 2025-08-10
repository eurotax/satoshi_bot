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
    Memory-safe job manager that prevents job accumulation
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
            
            logger.info(f"Job '{name}' added. Active jobs: {len(self.jobs)}")
            return job
            
        except Exception as e:
            logger.error(f"Failed to add job '{name}': {e}")
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
            logger.info(f"Cleaned up {len(completed)} completed jobs")
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
                logger.info(f"Removed old job: {name}")
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
        Enhanced error handling
        """
        logger.error("BOT ERROR DETECTED", exc_info=context.error)
        
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
                    "❌ An error occurred. Bot is automatically recovering.\n"
                    "Please try again shortly.",
                    timeout=10
                )
            except Exception as notify_error:
                logger.error(f"Failed to notify user: {notify_error}")
        
        # Memory cleanup on critical errors
        if isinstance(context.error, MemoryError):
            logger.critical("MEMORY ERROR - forcing cleanup")
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
            logger.info(f"Signal {signum} received, shutting down...")
            asyncio.create_task(self._graceful_shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _graceful_shutdown(self):
        """Clean shutdown procedure"""
        logger.info("Starting graceful shutdown...")
        
        try:
            # Stop application
            if self.application:
                await self.application.stop()
                logger.info("Application stopped")
            
            # Cleanup HTTP connections
            try:
                from dex.screener import cleanup
                await cleanup()
                logger.info("HTTP connections closed")
            except Exception as e:
                logger.warning(f"HTTP cleanup error: {e}")
            
            # Force garbage collection
            gc.collect()
            logger.info("Memory cleanup completed")
            
            self._shutdown_event.set()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        finally:
            logger.info("Graceful shutdown completed")
    
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
                        f"Bot stats - Memory: {memory_mb:.1f}MB, "
                        f"Uptime: {uptime_hours:.1f}h, Jobs: {job_stats['active_jobs']}"
                    )
                
                # Warning thresholds
                if memory_mb > 512:
                    logger.warning(f"High memory usage: {memory_mb:.1f}MB")
                    
                if memory_mb > 1024:
                    logger.critical(f"Critical memory: {memory_mb:.1f}MB - forcing cleanup")
                    gc.collect()
                    self.job_manager._cleanup_completed_jobs()
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Memory monitor error: {e}")
                await asyncio.sleep(60)
    
    def _setup_handlers(self):
        """Setup all bot handlers"""
        if not self.application:
            raise RuntimeError("Application not initialized")
        
        # Add error handler FIRST
        self.application.add_error_handler(self._enhanced_error_handler)
        
        # Command handlers
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("vip", vip_command))
        self.application.add_handler(CommandHandler("status", status_command))
        self.application.add_handler(CommandHandler("signals", signals_command))
        
        # Schedule jobs with memory-safe manager
        self.job_manager.add_job(
            job_queue=self.application.job_queue,
            callback=vip_signals_push,
            interval=900,  # 15 minutes
            first=60,      # Start after 1 minute
            data=VIP_CHANNEL_ID,
            name="vip_signals"
        )
        
        self.job_manager.add_job(
            job_queue=self.application.job_queue,
            callback=public_signals_push,
            interval=28800,  # 8 hours
            first=300,       # Start after 5 minutes
            data=PUBLIC_CHANNEL_ID,
            name="public_signals"
        )
        
        logger.info("All handlers and jobs configured")
    
    async def run_polling(self):
        """Run bot in polling mode"""
        logger.info("Starting polling mode...")
        
        try:
            await self.application.initialize()
            await self.application.start()
            
            # Start background monitoring
            monitor_task = asyncio.create_task(self._memory_monitor())
            
            # Start polling
            await self.application.updater.start_polling(
                allowed_updates=None,
                drop_pending_updates=True,  # Clear old updates
                timeout=30,
                poll_interval=1.0,
                bootstrap_retries=3
            )
            
            logger.info("Bot polling started successfully")
            
            # Wait for shutdown signal
            await self._shutdown_event.wait()
            
            # Cleanup
            monitor_task.cancel()
            
        except Exception as e:
            logger.error(f"Error in polling mode: {e}")
            raise
        finally:
            await self._graceful_shutdown()
    
    async def run_webhook(self, webhook_url: str):
        """Run bot in webhook mode"""
        path = f"/{BOT_TOKEN}"
        listen_port = int(os.getenv("PORT", 8443))
        
        logger.info(f"Starting webhook mode: {webhook_url}")
        
        try:
            await self.application.initialize()
            await self.application.start()
            
            # Start background monitoring
            monitor_task = asyncio.create_task(self._memory_monitor())
            
            # Start webhook
            await self.application.run_webhook(
                listen="0.0.0.0",
                port=listen_port,
                url_path=path,
                webhook_url=f"{webhook_url}{path}",
                allowed_updates=None,
                drop_pending_updates=True,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30
            )
            
            # Cleanup
            monitor_task.cancel()
            
        except Exception as e:
            logger.error(f"Error in webhook mode: {e}")
            raise
        finally:
            await self._graceful_shutdown()
    
    async def start(self):
        """Main bot startup"""
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not found in environment")
            return
        
        logger.info("SATOSHI SIGNAL BOT STARTING...")
        logger.info(f"Start time: {datetime.now()}")
        logger.info(f"Python version: {os.sys.version}")
        
        try:
            # Create application
            self.application = (
                Application.builder()
                .token(BOT_TOKEN)
                .read_timeout(30)
                .write_timeout(30)
                .connect_timeout(30)
                .pool_timeout(30)
                .concurrent_updates(True)
                .build()
            )
            
            self._running = True
            
            # Setup signal handlers
            await self._setup_signal_handlers()
            
            # Setup all handlers
            self._setup_handlers()
            
            # Choose run mode
            webhook_url = os.getenv("WEBHOOK_URL")
            
            if webhook_url and self._validate_webhook_url(webhook_url):
                logger.info(f"Using webhook mode: {webhook_url}")
                await self.run_webhook(webhook_url)
            else:
                if webhook_url:
                    logger.warning(f"Invalid WEBHOOK_URL: {webhook_url}")
                logger.info("Using polling mode")
                await self.run_polling()
                
        except Exception as e:
            logger.error(f"Critical startup error: {e}", exc_info=True)
            raise
        finally:
            self._running = False
            logger.info("Bot stopped")

# Global bot instance
bot_app = SafeBotApplication()

def main():
    """
    Main entry point with proper async handling
    """
    try:
        # Set up better event loop for better performance
        if os.name == 'nt':  # Windows
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        else:  # Unix/Linux - use default event loop (uvloop not compatible with Python 3.13)
            logger.info("Using default asyncio event loop")
        
        # Run bot
        asyncio.run(bot_app.start())
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
