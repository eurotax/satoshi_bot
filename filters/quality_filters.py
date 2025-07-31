# === filters/quality_filters.py ===

def is_volume_sufficient(volume_usd: float, min_volume: float) -> bool:
    return volume_usd >= min_volume

def is_liquidity_sufficient(liquidity_usd: float, min_liquidity: float) -> bool:
    return liquidity_usd >= min_liquidity

def is_price_change_significant(change_pct: float, min_change: float) -> bool:
    return abs(change_pct) >= min_change
