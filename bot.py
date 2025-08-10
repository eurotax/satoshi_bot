import logging
import os
import asyncio
import gc
import time
from datetime import datetime
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
    """Simplified bot application with polling only"""
    def __init__(self):
        self.application: Optional[Application] = None
        self.job_manager = MemorySafeJobManager()
        self._start_time = time.time()
    
    async def _enhanced_error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Enhanced error handling"""
        logger.error("BOT ERROR DETECTED", exc_info=context.error)
        
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
        
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Bot is automatically recovering.\n"
                    "Please try again shortly.",
                    timeout=10
                )
            except Exception as notify_error:
                logger.error(f"Failed to notify user: {notify_error}")
        
        if isinstance(context.error, MemoryError):
            logger.critical("MEMORY ERROR - forcing cleanup")
            gc.collect()
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            return psutil.Process().memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    async def _memory_monitor(self):
        """Background memory monitoring"""
        while True:
            try:
                memory_mb = self._get_memory_usage()
                uptime_hours = (time.time() - self._start_time) / 3600
                
                # Log stats every hour
                if int(uptime_hours) % 1 == 0 and int(uptime_hours) > 0:
                    job_stats = self.job_manager.get_stats()
                    logger.info(
                        f"Bot stats - Memory: {memory_mb:.1f}MB, "
                        f"Uptime: {uptime_hours:.1f}h, Jobs: {job_stats['active_jobs']}"
                    )
                
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
        
        self.application.add_error_handler(self._enhanced_error_handler)
        
        self.application.add_handler(CommandHandler("start", start_command))
        self.application.add_handler(CommandHandler("help", help_command))
        self.application.add_handler(CommandHandler("vip", vip_command))
        self.application.add_handler(CommandHandler("status", status_command))
        self.application.add_handler(CommandHandler("signals", signals_command))
        
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
    
    async def run(self):
        """Main bot execution - POLLING ONLY"""
        if not BOT_TOKEN:
            logger.error("BOT_TOKEN not found in environment")
            return
        
        logger.info("SATOSHI SIGNAL BOT STARTING...")
        logger.info(f"Start time: {datetime.now()}")
        logger.info("Using POLLING mode (webhook disabled)")
        
        try:
            # Create application
            self.application = (
                Application.builder()
                .token(BOT_TOKEN)
                .build()
            )
            
            # Setup handlers
            self._setup_handlers()
            
            # Start memory monitoring
            monitor_task = asyncio.create_task(self._memory_monitor())
            
            # Start polling
            logger.info("Starting bot polling...")
            await self.application.run_polling(
                allowed_updates=None,
                drop_pending_updates=True,
                timeout=30,
                poll_interval=2.0
            )
            
            # This line won't be reached in normal operation
            monitor_task.cancel()
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Critical startup error: {e}", exc_info=True)
        finally:
            logger.info("Bot stopped")

# Global bot instance
bot_app = SafeBotApplication()

def main():
    """Simple main function for polling mode"""
    try:
        logger.info("Starting Satoshi Signal Bot in polling mode...")
        asyncio.run(bot_app.run())
        
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main()
