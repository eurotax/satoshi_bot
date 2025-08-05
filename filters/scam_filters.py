# === filters/scam_filters.py ===

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def has_sufficient_trading_activity(pair_data: Dict[str, Any]) -> bool:
    """Check if pair has sufficient trading activity to be considered legitimate."""
    try:
        txns = pair_data.get("txns", {})
        
        # Check 1h activity
        h1_txns = txns.get("h1", {})
        h1_buys = h1_txns.get("buys", 0)
        h1_sells = h1_txns.get("sells", 0)
        h1_total = h1_buys + h1_sells
        
        # Check 24h activity  
        h24_txns = txns.get("h24", {})
        h24_buys = h24_txns.get("buys", 0)
        h24_sells = h24_txns.get("sells", 0)
        h24_total = h24_buys + h24_sells
        
        # Minimum trading activity requirements
        min_h1_txns = 5
        min_h24_txns = 20
        
        return h1_total >= min_h1_txns and h24_total >= min_h24_txns
        
    except Exception as e:
        logger.warning(f"Error checking trading activity: {e}")
        return False


def has_balanced_trading(pair_data: Dict[str, Any]) -> bool:
    """Check if trading is balanced (not just all buys or all sells)."""
    try:
        txns = pair_data.get("txns", {})
        h1_txns = txns.get("h1", {})
        
        buys = h1_txns.get("buys", 0)
        sells = h1_txns.get("sells", 0)
        
        if buys + sells == 0:
            return False
            
        # Calculate buy/sell ratio
        total_txns = buys + sells
        buy_ratio = buys / total_txns
        
        # Healthy ratio should be between 20% and 80% buys
        return 0.2 <= buy_ratio <= 0.8
        
    except Exception as e:
        logger.warning(f"Error checking trading balance: {e}")
        return False


def has_reasonable_market_cap(pair_data: Dict[str, Any]) -> bool:
    """Check if market cap is within reasonable bounds."""
    try:
        market_cap = pair_data.get("marketCap")
        
        if not market_cap or market_cap <= 0:
            # No market cap data available - can't determine
            return True
            
        # Avoid very low market cap (potential scams) and extremely high market cap
        min_market_cap = 1000  # $1k minimum
        max_market_cap = 100_000_000  # $100M maximum for new tokens
        
        return min_market_cap <= market_cap <= max_market_cap
        
    except Exception as e:
        logger.warning(f"Error checking market cap: {e}")
        return True  # Default to True if can't determine


def has_sufficient_liquidity_depth(pair_data: Dict[str, Any]) -> bool:
    """Check if liquidity is sufficient and not artificially inflated."""
    try:
        liquidity = pair_data.get("liquidity", {})
        liquidity_usd = float(liquidity.get("usd", 0))
        
        volume = pair_data.get("volume", {})
        volume_24h = float(volume.get("h24", 0))
        
        if liquidity_usd <= 0 or volume_24h <= 0:
            return False
            
        # Volume to liquidity ratio check
        # Healthy pairs usually have volume/liquidity ratio between 0.1 and 5
        ratio = volume_24h / liquidity_usd
        
        return 0.1 <= ratio <= 5.0
        
    except Exception as e:
        logger.warning(f"Error checking liquidity depth: {e}")
        return False


def is_pair_age_reasonable(pair_data: Dict[str, Any]) -> bool:
    """Check if pair is not too new (potential honeypot)."""
    try:
        import time
        
        pair_created_at = pair_data.get("pairCreatedAt")
        
        if not pair_created_at:
            return True  # Can't determine age
            
        current_timestamp = int(time.time() * 1000)  # Current time in milliseconds
        pair_age_hours = (current_timestamp - pair_created_at) / (1000 * 60 * 60)
        
        # Pair should be at least 1 hour old to have some trading history
        min_age_hours = 1
        
        return pair_age_hours >= min_age_hours
        
    except Exception as e:
        logger.warning(f"Error checking pair age: {e}")
        return True


def has_token_info(pair_data: Dict[str, Any]) -> bool:
    """Check if tokens have basic information available."""
    try:
        base_token = pair_data.get("baseToken", {})
        quote_token = pair_data.get("quoteToken", {})
        
        # Check if tokens have names and symbols
        base_name = base_token.get("name", "").strip()
        base_symbol = base_token.get("symbol", "").strip()
        quote_symbol = quote_token.get("symbol", "").strip()
        
        # Base token should have name and symbol
        if not base_name or not base_symbol:
            return False
            
        # Quote token should have symbol
        if not quote_symbol:
            return False
            
        # Check for suspicious patterns in names/symbols
        suspicious_patterns = ["test", "fake", "scam", "rug"]
        
        for pattern in suspicious_patterns:
            if (pattern in base_name.lower() or 
                pattern in base_symbol.lower() or 
                pattern in quote_symbol.lower()):
                return False
                
        return True
        
    except Exception as e:
        logger.warning(f"Error checking token info: {e}")
        return False


def passes_scam_filters(pair_data: Dict[str, Any]) -> bool:
    """
    Run all scam detection filters on a trading pair.
    Returns True if pair passes all checks (appears legitimate).
    """
    try:
        checks = [
            ("trading_activity", has_sufficient_trading_activity(pair_data)),
            ("balanced_trading", has_balanced_trading(pair_data)),
            ("market_cap", has_reasonable_market_cap(pair_data)),
            ("liquidity_depth", has_sufficient_liquidity_depth(pair_data)),
            ("pair_age", is_pair_age_reasonable(pair_data)),
            ("token_info", has_token_info(pair_data))
        ]
        
        failed_checks = [name for name, passed in checks if not passed]
        
        if failed_checks:
            pair_name = f"{pair_data.get('baseToken', {}).get('symbol', '?')}/{pair_data.get('quoteToken', {}).get('symbol', '?')}"
            logger.debug(f"Pair {pair_name} failed scam filters: {failed_checks}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error in scam filters: {e}")
        return False


# Legacy functions for backward compatibility
def is_renounced(pair_data: Dict[str, Any]) -> bool:
    """Legacy function - DEXScreener doesn't provide renounce data."""
    logger.warning("is_renounced() called but DEXScreener doesn't provide this data")
    return True  # Default to True since we can't check


def is_lp_locked(pair_data: Dict[str, Any]) -> bool:
    """Legacy function - DEXScreener doesn't provide LP lock data."""
    logger.warning("is_lp_locked() called but DEXScreener doesn't provide this data")
    return True  # Default to True since we can't check


def has_safe_tax(pair_data: Dict[str, Any]) -> bool:
    """Legacy function - DEXScreener doesn't provide tax data."""
    logger.warning("has_safe_tax() called but DEXScreener doesn't provide this data")
    return True  # Default to True since we can't check
