# === utils.py ===

import httpx
import logging
from typing import List, Dict, Any
from config import MIN_VOLUME, MIN_LIQUIDITY, MIN_PRICE_CHANGE

logger = logging.getLogger(__name__)


async def fetch_dex_data() -> List[Dict[str, Any]]:
    """
    Fetch DEX data using the search API for trending tokens.
    This is the main data fetching function.
    """
    # Import inside function to avoid circular imports
    from dex.screener import fetch_trending_pairs
    return await fetch_trending_pairs()


def is_legit_token(pair: Dict[str, Any]) -> bool:
    """
    Determine if a token/pair appears legitimate using available data.
    This replaces the old broken logic with proper checks.
    """
    # Import inside function to avoid circular imports
    from filters.scam_filters import passes_scam_filters
    return passes_scam_filters(pair)


def filter_signals(pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter trading pairs based on volume, liquidity, price change, and legitimacy.
    This is the main filtering function used throughout the app.
    """
    filtered = []
    
    for pair in pairs:
        try:
            # Extract metrics with safe conversion
            volume_data = pair.get("volume", {})
            volume_24h = float(volume_data.get("h24", 0)) if volume_data.get("h24") else 0
            
            liquidity_data = pair.get("liquidity", {})
            liquidity_usd = float(liquidity_data.get("usd", 0)) if liquidity_data.get("usd") else 0
            
            price_change_data = pair.get("priceChange", {})
            price_change_1h = float(price_change_data.get("h1", 0)) if price_change_data.get("h1") else 0
            
            # Apply basic filters
            if volume_24h < MIN_VOLUME:
                continue
                
            if liquidity_usd < MIN_LIQUIDITY:
                continue
                
            if abs(price_change_1h) < MIN_PRICE_CHANGE:
                continue
                
            # Apply legitimacy filters
            if not is_legit_token(pair):
                continue
                
            filtered.append(pair)
            
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"Skipping malformed pair: {e}")
            continue
    
    # Sort by volume descending
    filtered.sort(key=lambda x: float(x.get("volume", {}).get("h24", 0)), reverse=True)
    return filtered


def format_signals(pairs: List[Dict[str, Any]], vip: bool = False) -> str:
    """
    Format trading pairs into a Telegram message.
    This function maintains backward compatibility.
    """
    # Import inside function to avoid circular imports
    from dex.screener import format_signals_message
    return format_signals_message(pairs, vip)


def format_pair_message(pair: Dict[str, Any], include_meta: bool = False) -> str:
    """
    Format a single trading pair into a Telegram message.
    Updated to use real DEXScreener API structure with safe number formatting.
    """
    try:
        # Extract token information
        base_token = pair.get("baseToken", {})
        quote_token = pair.get("quoteToken", {})
        
        base_symbol = base_token.get("symbol", "?")
        quote_symbol = quote_token.get("symbol", "?")
        pair_name = f"{base_symbol}/{quote_symbol}"
        
        # Extract price and change with safe conversion
        price_usd_str = pair.get("priceUsd", "0")
        try:
            price_usd = float(price_usd_str) if price_usd_str else 0
        except (ValueError, TypeError):
            price_usd = 0
            
        price_change_data = pair.get("priceChange", {})
        change_1h_str = price_change_data.get("h1", "0")
        try:
            change_1h = float(change_1h_str) if change_1h_str else 0
        except (ValueError, TypeError):
            change_1h = 0
        
        # Get URL
        url = pair.get("url", "")
        
        # Choose emoji
        emoji = "📈" if change_1h > 0 else "📉"
        
        # Format price with appropriate precision
        if price_usd >= 1:
            price_str = f"${price_usd:.4f}"
        elif price_usd >= 0.0001:
            price_str = f"${price_usd:.8f}"
        else:
            price_str = f"${price_usd:.12f}"
        
        # Basic message
        message = f"{emoji} [{pair_name}]({url})\n💰 {price_str} ({change_1h:+.2f}%)"
        
        # Add metadata if requested
        if include_meta:
            volume_data = pair.get("volume", {})
            volume_24h_str = volume_data.get("h24", "0")
            try:
                volume_24h = float(volume_24h_str) if volume_24h_str else 0
            except (ValueError, TypeError):
                volume_24h = 0
                
            liquidity_data = pair.get("liquidity", {})
            liquidity_usd_str = liquidity_data.get("usd", "0")
            try:
                liquidity_usd = float(liquidity_usd_str) if liquidity_usd_str else 0
            except (ValueError, TypeError):
                liquidity_usd = 0
            
            message += (
                f"\n📊 Volume 24h: ${volume_24h:,.0f}"
                f"\n🔒 Liquidity: ${liquidity_usd:,.0f}"
            )
        
        return message
        
    except Exception as e:
        logger.error(f"Error formatting pair message: {e}")
        return "❌ Error formatting pair data"


# Legacy compatibility functions
async def fetch_pairs() -> List[Dict[str, Any]]:
    """Legacy wrapper for fetch_dex_data() - used in tests."""
    return await fetch_dex_data()


def filter_pairs(pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Legacy wrapper for filter_signals() - used in tests."""
    return filter_signals(pairs)
