# === config.py ===

# Minimalne wymagania do filtrowania sygnałów
MIN_VOLUME = 10000          # Min. wolumen obrotu 24h w USD
MIN_LIQUIDITY = 5000        # Min. płynność w USD
MIN_PRICE_CHANGE = 10       # Min. zmiana ceny w % w ciągu 1h

# Telegram channel IDs (upewnij się, że są prawidłowe)
VIP_CHANNEL_ID = "-1002726810570"       # Jeśli masz inny, zaktualizuj
PUBLIC_CHANNEL_ID = "@SatoshiSignalLab"

# Bybit monitoring configuration
BYBIT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
BYBIT_ALERT_PERCENT = 5.0  # alert when 24h change exceeds this percent
