# === jobs/scheduler.py ===

import logging
from telegram.ext import ContextTypes, JobQueue
from dex.screener import get_filtered_signals, format_signals_message
from config import VIP_CHANNEL_ID, PUBLIC_CHANNEL_ID

logger = logging.getLogger(__name__)


async def publish_signals_job(context: ContextTypes.DEFAULT_TYPE):
    try:
        # Pobierz ID kanału z kontekstu zadania
        channel_id = context.job.data

        # Pobierz dane i sformatuj wiadomość
        signals = await get_filtered_signals()
        if not signals:
            logger.info(f"Brak sygnałów spełniających kryteria dla {channel_id}")
            return

        message = format_signals_message(signals, vip=(channel_id == VIP_CHANNEL_ID))

        await context.bot.send_message(
            chat_id=channel_id,
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info(f"Wysłano sygnały do kanału {channel_id}")

    except Exception as e:
        logger.error(f"Błąd podczas publikacji sygnałów: {e}")


def schedule_jobs(job_queue: JobQueue) -> None:
    """Register periodic signal publishing jobs."""
    # VIP channel updates every 15 minutes
    job_queue.run_repeating(
        publish_signals_job,
        interval=900,
        first=60,
        data=VIP_CHANNEL_ID,
        name="vip_signals",
    )

    # Public channel updates every 8 hours
    job_queue.run_repeating(
        publish_signals_job,
        interval=28800,
        first=300,
        data=PUBLIC_CHANNEL_ID,
        name="public_signals",
    )
