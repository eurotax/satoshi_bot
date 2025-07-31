# === filters/scam_filters.py ===

import logging

logger = logging.getLogger(__name__)


def is_renounced(pair_data: dict) -> bool:
    try:
        return pair_data.get("pairCreatedByRenounced", False)
    except Exception as e:
        logger.warning(f"Error checking renounce status: {e}")
        return False


def is_lp_locked(pair_data: dict) -> bool:
    try:
        return pair_data.get("liquidityLocked", False)
    except Exception as e:
        logger.warning(f"Error checking LP lock: {e}")
        return False


def has_safe_tax(pair_data: dict) -> bool:
    try:
        buy_tax = pair_data.get("txns", {}).get("buyTax", 0)
        sell_tax = pair_data.get("txns", {}).get("sellTax", 0)
        return buy_tax <= 10 and sell_tax <= 10
    except Exception as e:
        logger.warning(f"Error checking taxes: {e}")
        return False


def passes_scam_filters(pair_data: dict) -> bool:
    """
    Returns True if all scam checks pass
    """
    return is_renounced(pair_data) and is_lp_locked(pair_data) and has_safe_tax(pair_data)
