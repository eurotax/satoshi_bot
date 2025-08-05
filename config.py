# === config.py ===

# Minimalne wymagania do filtrowania sygnałów (dostosowane do rzeczywistości)
MIN_VOLUME = 50000          # Min. wolumen obrotu 24h w USD ($50k)
MIN_LIQUIDITY = 10000       # Min. płynność w USD ($10k)
MIN_PRICE_CHANGE = 5        # Min. zmiana ceny w % w ciągu 1h (5%)

# Telegram channel IDs
VIP_CHANNEL_ID = "-1002726810570"       # VIP channel (private)
PUBLIC_CHANNEL_ID = "@SatoshiSignalLab" # Public channel

# Signal publishing intervals (in seconds)
VIP_INTERVAL = 900      # 15 minutes for VIP
PUBLIC_INTERVAL = 28800 # 8 hours for public

# Quality filters
MIN_TRANSACTIONS_1H = 5     # Minimum transactions in 1 hour
MIN_TRANSACTIONS_24H = 20   # Minimum transactions in 24 hours
MIN_MARKET_CAP = 1000       # Minimum market cap in USD
MAX_MARKET_CAP = 100000000  # Maximum market cap in USD ($100M)

# Trading balance filters
MIN_BUY_RATIO = 0.2  # At least 20% of transactions should be buys
MAX_BUY_RATIO = 0.8  # At most 80% of transactions should be buys

# Liquidity depth filters
MIN_VOLUME_LIQUIDITY_RATIO = 0.1  # Volume should be at least 10% of liquidity
MAX_VOLUME_LIQUIDITY_RATIO = 5.0  # Volume shouldn't be more than 5x liquidity

# Age filters
MIN_PAIR_AGE_HOURS = 1  # Pair should be at least 1 hour old

# Bybit monitoring configuration (legacy - może być usunięte)
BYBIT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
BYBIT_ALERT_PERCENT = 5.0  # alert when 24h change exceeds this percent

# DEXScreener API configuration
DEXSCREENER_TIMEOUT = 10  # Request timeout in seconds
MAX_PAIRS_PER_QUERY = 10  # Maximum pairs to fetch per search query
