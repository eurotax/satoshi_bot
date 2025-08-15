import logging
import os
import asyncio
import gc
import time
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

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


def _is_valid_webhook(url: str) -> bool:
    """Return True if the given URL looks like an HTTP(S) webhook endpoint."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in {"http", "https"}:
        return False

    if not parsed.netloc:
        return False

    try:
        # Accessing ``parsed.port`` will raise ``ValueError`` if the port is invalid
        _ = parsed.port
    except ValueError:
        return False

    return True

# Enhanced logging setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MemorySafeJobManager:
    """Memory-safe job manager that prevents job accumulation"""
    def __init__(self):
        self.jobs = {}
        self.max_jobs = 20
        self.last_cleanup = time.time()
        self.cleanup_interval = 600
    
    def add_job(self, job_queue, callback, interval: int, first: int, data: any, name: str):
        """Add job with automatic memory management"""
        try:
            self._maybe_cleanup()
            
            if len(self.jobs) >= self.max_jobs:
                logger.warning(f"Too many jobs ({len(self.jobs)}), cleaning up")
                self._force_cleanup()
            
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
            gc.collect()
    
    def _force_cleanup(self):
        """Force cleanup of old jobs"""
        now = time.time()
        old_jobs = []
        
        for name, info in self.jobs.items():
            age = now - info['created']
            if age > 3600:
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

class SimpleBotApplication:
    """Ultra-simple bot application that bypasses problematic run_* methods"""
    def __init__(self):
        self.application: Optional[Application] = None
        self.job_manager = MemorySafeJobManager()
        self._start_time = time.time()
        self._running = False
    
    async def _enhanced_error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Enhanced error handling"""
        logger.error("BOT ERROR DETECTED", exc_info=context.error)
        
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again shortly.",
                    timeout=10
                )
            except Exception as notify_error:
                logger.error(f"Failed to notify user: {notify_error}")
        
        if isinstance(context.error, MemoryError):
            logger.critical("MEMORY ERROR - forcing cleanup")
            gc.collect()
    
    def _setup_handlers(self):
        """Setup all bot handlers"""
        if not self.application:
            raise RuntimeError("Application not initialized")
        
        self.application.add_error_handler(self._enhanced_error_handler)
        
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("vip", vip_command))
        self.application.add_handler(CommandHandler("status", status_command))
        self.application.add_handler(CommandHandler("signals", signals_command))
        
        # Add jobs
        self.job_manager.add_job(
            job_queue=self.application.job_queue,
            callback=vip_signals_push,
            interval=900,
            first=60,
            data=VIP_CHANNEL_ID,
            name="vip_signals"
        )
        
        self.job_manager.add_job(
            job_queue=self.application.job_queue,
            callback=public_signals_push,
            interval=28800,
            first=300,
            data=PUBLIC_CHANNEL_ID,
            name="public_signals"
        )
        
        logger.info("All handlers and jobs configured")
    
    async def _polling_loop(self):
        """Manual polling loop that avoids problematic run_polling"""
        logger.info("Starting manual polling loop...")
        
        # Initialize and start application manually
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(
            poll_interval=2.0,
            timeout=30,
            allowed_updates=None,
            drop_pending_updates=True
        )
        
        logger.info("Bot is now running and polling for updates...")
        
        # Keep the bot running
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Polling loop cancelled")
        except Exception as e:
            logger.error(f"Error in polling loop: {e}")
        finally:
            # Cleanup
            try:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                logger.info("Application shutdown completed")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
    
    async def run(self):
        """Main bot execution"""
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not found in environment")
            return
        
        logger.info("SATOSHI SIGNAL BOT STARTING...")
        logger.info(f"Start time: {datetime.now()}")
        logger.info("Using MANUAL POLLING mode")
        
        try:
            # Create application
            self.application = Application.builder().token(BOT_TOKEN).build()
            
            # Setup handlers
            self._setup_handlers()
            
            # Start running
            self._running = True
            
            # Start polling loop
            await self._polling_loop()
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self._running = False
        except Exception as e:
            logger.error(f"Critical startup error: {e}", exc_info=True)
            self._running = False
        finally:
            logger.info("Bot stopped")

# Global bot instance
bot_app = SimpleBotApplication()

def main():
    """Ultra-simple main function"""
    try:
        logger.info("Starting Satoshi Signal Bot...")
        asyncio.run(bot_app.run())
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main()
