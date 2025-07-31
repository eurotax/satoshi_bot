# === filters/basic_filters.py ===

from config import MIN_VOLUME, MIN_LIQUIDITY, MIN_PRICE_CHANGE

def passes_basic_filters(pair: dict) -> bool:
    try:
        volume = float(pair.get("volume", {}).get("h24", 0))
        liquidity = float(pair.get("liquidity", {}).get("usd", 0))
        price_change = abs(float(pair.get("priceChange", {}).get("h1", 0)))

        if volume < MIN_VOLUME:
            return False
        if liquidity < MIN_LIQUIDITY:
            return False
        if price_change < MIN_PRICE_CHANGE:
            return False

        return True
    except Exception:
        return False
