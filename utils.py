# === utils.py ===

import httpx
import logging
from typing import List, Dict, Any
from config import MIN_VOLUME, MIN_LIQUIDITY, MIN_PRICE_CHANGE
from filters.scam_filters import passes_scam_filters

logger = logging.getLogger(__name__)


async def fetch_dex_data() -> List[Dict[str, Any]]:
    """
    Fetch DEX data using the search API for trending tokens.
    This is the main data fetching function.
    """
    from dex.screener import fetch_trending_pairs
    return await fetch_trending_pairs()


def is_legit_token(pair: Dict[str, Any]) -> bool:
    """
    Determine if a token/pair appears legitimate using available data.
    This replaces the old broken logic with proper checks.
    """
    return passes_scam_filters(pair)


def filter_signals(pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter trading pairs based on volume, liquidity, price change, and legitimacy.
    This is the main filtering function used throughout the app.
    """
    filtered = []
    
    for pair in pairs:
        try:
            # Extract metrics
            volume_data = pair.get("volume", {})
            volume_24h = float(volume_data.get("h24", 0))
            
            liquidity_data = pair.get("liquidity", {})
            liquidity_usd = float(liquidity_data.get("usd", 0))
            
            price_change_data = pair.get("priceChange", {})
            price_change_1h = float(price_change_data.get("h1", 0))
            
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
    from dex.screener import format_signals_message
    return format_signals_message(pairs, vip)


def format_pair_message(pair: Dict[str, Any], include_meta: bool = False) -> str:
    """
    Format a single trading pair into a Telegram message.
    Updated to use real DEXScreener API structure.
    """
    try:
        # Extract token information
        base_token = pair.get("baseToken", {})
        quote_token = pair.get("quoteToken", {})
        
        base_symbol = base_token.get("symbol", "?")
        quote_symbol = quote_token.get("symbol", "?")
        pair_name = f"{base_symbol}/{quote_symbol}"
        
        # Extract price and change
        price_usd = float(pair.get("priceUsd", 0))
        price_change_data = pair.get("priceChange", {})
        change_1h = float(price_change_data.get("h1", 0))
        
        # Get URL
        url = pair.get("url", "")
        
        # Choose emoji
        emoji = "📈" if change_1h > 0 else "📉"
        
        # Basic message
        message = f"{emoji} [{pair_name}]({url})\n💰 ${price_usd:.8f} ({change_1h:+.2f}%)"
        
        # Add metadata if requested
        if include_meta:
            volume_24h = float(pair.get("volume", {}).get("h24", 0))
            liquidity_usd = float(pair.get("liquidity", {}).get("usd", 0))
            
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
