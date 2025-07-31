# === jobs/scheduler.py ===

import logging
from telegram.ext import ContextTypes
from config import VIP_CHANNEL_ID, PUBLIC_CHANNEL_ID
from scheduler.publisher import publish_job

logger = logging.getLogger(__name__)


async def publish_signals_job(context: ContextTypes.DEFAULT_TYPE):
    """Wrapper that delegates publishing to :func:`scheduler.publisher.publish_job`."""
    try:
        await publish_job(context)
    except Exception as e:
        logger.error(f"Błąd podczas publikacji sygnałów: {e}")


def schedule_jobs(job_queue):
    """Register periodic publishing jobs on the provided ``job_queue``."""
    job_queue.run_repeating(
        publish_signals_job,
        interval=900,  # 15 minutes
        first=60,
        data=VIP_CHANNEL_ID,
        name="vip_signals",
    )
    job_queue.run_repeating(
        publish_signals_job,
        interval=28800,  # 8 hours
        first=300,
        data=PUBLIC_CHANNEL_ID,
        name="public_signals",
    )
