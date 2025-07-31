# === config.py ===

# Environment variables
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram channel IDs
VIP_CHANNEL_ID = "-1002726810570"  # Replace with actual ID
PUBLIC_CHANNEL_ID = "@SatoshiSignalLab"

# Filtering thresholds
MIN_VOLUME = 10000       # USD - minimalny wolumen 24h
MIN_LIQUIDITY = 5000     # USD - minimalna płynność
MIN_PRICE_CHANGE = 10    # % zmiana ceny w ciągu godziny

# Scheduling intervals (in seconds)
INTERVAL_VIP = 15 * 60       # 15 minutes
INTERVAL_PUBLIC = 8 * 60 * 60  # 8 hours

