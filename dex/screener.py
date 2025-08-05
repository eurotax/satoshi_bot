# === dex/screener.py ===

import httpx
import logging
from typing import List, Dict, Any, Optional
from config import MIN_VOLUME, MIN_LIQUIDITY, MIN_PRICE_CHANGE

logger = logging.getLogger(__name__)

# Use search endpoint instead of direct pairs endpoint
DEXSCREENER_SEARCH_API = "https://api.dexscreener.com/latest/dex/search"
DEXSCREENER_PAIRS_API = "https://api.dexscreener.com/latest/dex/pairs"


async def fetch_trending_pairs(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetch trending pairs using search endpoint with popular tokens."""
    trending_queries = ["SOL", "BONK", "JUP", "WIF", "PEPE"]
    all_pairs = []
    
    try:
        async with httpx.AsyncClient() as client:
            for query in trending_queries:
                try:
                    response = await client.get(
                        DEXSCREENER_SEARCH_API,
                        params={"q": query},
                        timeout=10
                    )
                    response.raise_for_status()
                    data = response.json()
                    pairs = data.get("pairs", [])
                    
                    # Filter only Solana pairs
                    solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
                    all_pairs.extend(solana_pairs[:10])  # Top 10 per query
                    
                except Exception as e:
                    logger.warning(f"Failed to fetch pairs for query '{query}': {e}")
                    continue
                    
        # Remove duplicates based on pairAddress
        seen_addresses = set()
        unique_pairs = []
        for pair in all_pairs:
            addr = pair.get("pairAddress")
            if addr and addr not in seen_addresses:
                seen_addresses.add(addr)
                unique_pairs.append(pair)
                
        return unique_pairs[:limit]
        
    except Exception as e:
        logger.error(f"[dex/screener] Failed to fetch trending pairs: {e}")
        return []


async def fetch_pair_by_address(chain_id: str, pair_id: str) -> Optional[Dict[str, Any]]:
    """Fetch specific pair by chain and pair address."""
    try:
        async with httpx.AsyncClient() as client:
            url = f"{DEXSCREENER_PAIRS_API}/{chain_id}/{pair_id}"
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            pairs = data.get("pairs", [])
            return pairs[0] if pairs else None
    except Exception as e:
        logger.error(f"[dex/screener] Failed to fetch pair {pair_id}: {e}")
        return None


def filter_signals(pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter pairs based on volume, liquidity, and price change criteria."""
    filtered = []
    
    for pair in pairs:
        try:
            # Extract volume (24h)
            volume_data = pair.get("volume", {})
            volume_24h = float(volume_data.get("h24", 0))
            
            # Extract liquidity
            liquidity_data = pair.get("liquidity", {})
            liquidity_usd = float(liquidity_data.get("usd", 0))
            
            # Extract price change (1h)
            price_change_data = pair.get("priceChange", {})
            price_change_1h = float(price_change_data.get("h1", 0))
            
            # Apply filters
            if (
                volume_24h >= MIN_VOLUME
                and liquidity_usd >= MIN_LIQUIDITY
                and abs(price_change_1h) >= MIN_PRICE_CHANGE
                and is_quality_pair(pair)
            ):
                filtered.append(pair)
                
        except (ValueError, TypeError, KeyError) as e:
            logger.warning(f"[dex/screener] Skipping malformed pair: {e}")
            continue
            
    # Sort by volume descending
    filtered.sort(key=lambda x: float(x.get("volume", {}).get("h24", 0)), reverse=True)
    return filtered


def is_quality_pair(pair: Dict[str, Any]) -> bool:
    """Basic quality checks for trading pairs."""
    try:
        # Check if pair has basic required data
        base_token = pair.get("baseToken", {})
        quote_token = pair.get("quoteToken", {})
        
        if not base_token.get("symbol") or not quote_token.get("symbol"):
            return False
            
        # Check if pair has recent trading activity
        txns = pair.get("txns", {})
        h1_txns = txns.get("h1", {})
        
        if not h1_txns:
            return False
            
        buys = h1_txns.get("buys", 0)
        sells = h1_txns.get("sells", 0)
        
        # Must have at least some trading activity
        if buys + sells < 5:
            return False
            
        # Check market cap (if available)
        market_cap = pair.get("marketCap")
        if market_cap and market_cap > 0:
            # Skip very low market cap tokens (potential scams)
            if market_cap < 1000:  # Less than $1k market cap
                return False
                
        return True
        
    except Exception as e:
        logger.warning(f"Error in quality check: {e}")
        return False


async def get_filtered_signals(limit: int = 5) -> List[Dict[str, Any]]:
    """Get filtered and sorted trading signals."""
    raw_pairs = await fetch_trending_pairs(limit * 10)  # Fetch more to filter from
    filtered_pairs = filter_signals(raw_pairs)
    return filtered_pairs[:limit]


def format_pair_message(pair: Dict[str, Any]) -> str:
    """Format a single pair as Telegram message with proper data extraction."""
    try:
        # Extract token info
        base_token = pair.get("baseToken", {})
        quote_token = pair.get("quoteToken", {})
        
        base_symbol = base_token.get("symbol", "?")
        quote_symbol = quote_token.get("symbol", "?")
        pair_name = f"{base_symbol}/{quote_symbol}"
        
        # Extract price and changes
        price_usd = float(pair.get("priceUsd", 0))
        price_change = pair.get("priceChange", {})
        change_1h = float(price_change.get("h1", 0))
        change_24h = float(price_change.get("h24", 0))
        
        # Extract volume and liquidity
        volume = float(pair.get("volume", {}).get("h24", 0))
        liquidity = float(pair.get("liquidity", {}).get("usd", 0))
        
        # Get DEXScreener URL
        url = pair.get("url", "")
        
        # Choose emoji based on price change
        emoji = "📈" if change_1h > 0 else "📉"
        
        # Format message
        message = (
            f"{emoji} [{pair_name}]({url})\n"
            f"💰 ${price_usd:.8f}\n"
            f"📊 1h: {change_1h:+.2f}% | 24h: {change_24h:+.2f}%\n"
            f"💹 Volume: ${volume:,.0f}\n"
            f"🔒 Liquidity: ${liquidity:,.0f}"
        )
        
        return message
        
    except Exception as e:
        logger.error(f"Error formatting pair message: {e}")
        return "❌ Error formatting pair data"


def format_signals_message(pairs: List[Dict[str, Any]], vip: bool = False) -> str:
    """Format multiple pairs into a complete Telegram message."""
    if not pairs:
        return "⚠️ No high-quality signals found right now. Check back later!"
        
    # Header
    header = "💎 *VIP SIGNALS* 💎\n\n" if vip else "📊 *CRYPTO SIGNALS* 📊\n\n"
    
    # Format each pair
    pair_messages = []
    for i, pair in enumerate(pairs, 1):
        pair_msg = format_pair_message(pair)
        pair_messages.append(f"**{i}.** {pair_msg}")
    
    body = "\n\n".join(pair_messages)
    
    # Footer
    if vip:
        footer = "\n\n🔒 *Exclusive VIP analysis*\n⚡ *Real-time alerts*"
    else:
        footer = "\n\n💎 [Join VIP](https://t.me/+sR2qa2jnr6o5MDk0) for exclusive signals!"
    
    return header + body + footer
