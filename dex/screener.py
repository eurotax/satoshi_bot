import httpx
import logging
import asyncio
from typing import List, Dict, Any, Optional
from config import MIN_VOLUME, MIN_LIQUIDITY, MIN_PRICE_CHANGE
from safe_utils import safe_float_convert, validate_pair_data, retry_with_exponential_backoff, log_function_call

logger = logging.getLogger(__name__)

class HTTPClientManager:
    """
    Singleton HTTP client manager
    Fixes connection pool leaks
    """
    _instance = None
    _client = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with proper configuration"""
        if self._client is None or self._client.is_closed:
            async with self._lock:
                if self._client is None or self._client.is_closed:
                    self._client = httpx.AsyncClient(
                        timeout=httpx.Timeout(30.0),
                        limits=httpx.Limits(
                            max_connections=10,
                            max_keepalive_connections=5
                        ),
                        headers={'User-Agent': 'SatoshiSignalBot/1.0'}
                    )
                    logger.info("HTTP client initialized")
        return self._client
    
    async def close(self):
        """Cleanup HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            logger.info("HTTP client closed")

# Global instance
http_manager = HTTPClientManager()

@retry_with_exponential_backoff(max_retries=3, base_delay=1.0)
@log_function_call
async def fetch_trending_pairs(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch trending pairs with retry logic and better error handling
    """
    # Smaller set of reliable queries
    trending_queries = ["SOL", "USDC", "BONK", "WIF", "JUP"]
    all_pairs = []
    
    try:
        client = await http_manager.get_client()
        
        async def fetch_single_query(query: str) -> List[Dict[str, Any]]:
            """Fetch data for single query with error handling"""
            try:
                logger.debug(f"Fetching pairs for query: {query}")
                response = await client.get(
                    "https://api.dexscreener.com/latest/dex/search",
                    params={"q": query},
                    timeout=15
                )
                response.raise_for_status()
                
                data = response.json()
                pairs = data.get("pairs", [])
                
                if not pairs:
                    logger.warning(f"No pairs returned for query: {query}")
                    return []
                
                # Filter and validate
                valid_pairs = []
                for pair in pairs[:15]:  # Take more to filter from
                    if (pair.get("chainId") == "solana" and 
                        validate_pair_data(pair)):
                        valid_pairs.append(pair)
                
                logger.info(f"Query '{query}': {len(valid_pairs)} valid pairs")
                return valid_pairs
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit
                    logger.warning(f"Rate limited for query '{query}', skipping")
                    await asyncio.sleep(2)
                else:
                    logger.warning(f"HTTP {e.response.status_code} for query '{query}'")
                return []
            except Exception as e:
                logger.warning(f"Error fetching query '{query}': {e}")
                return []
        
        # Fetch with delay between requests to avoid rate limits
        for i, query in enumerate(trending_queries):
            if i > 0:
                await asyncio.sleep(0.5)  # Small delay between requests
            
            pairs = await fetch_single_query(query)
            all_pairs.extend(pairs)
        
        # Remove duplicates
        seen_addresses = set()
        unique_pairs = []
        for pair in all_pairs:
            addr = pair.get("pairAddress")
            if addr and addr not in seen_addresses:
                seen_addresses.add(addr)
                unique_pairs.append(pair)
        
        logger.info(f"Total unique pairs fetched: {len(unique_pairs)}")
        return unique_pairs[:limit]
        
    except Exception as e:
        logger.error(f"Critical error in fetch_trending_pairs: {e}")
        return []

def filter_signals(pairs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enhanced signal filtering with comprehensive validation
    """
    if not pairs:
        logger.warning("No pairs to filter")
        return []
    
    filtered = []
    stats = {
        'input_count': len(pairs),
        'validation_failed': 0,
        'volume_failed': 0,
        'liquidity_failed': 0,
        'price_change_failed': 0,
        'quality_failed': 0,
        'passed': 0
    }
    
    for pair in pairs:
        try:
            # Validate structure first
            if not validate_pair_data(pair):
                stats['validation_failed'] += 1
                continue
            
            # Extract with safe conversion
            volume_data = pair.get("volume", {})
            volume_24h = safe_float_convert(volume_data.get("h24"))
            
            liquidity_data = pair.get("liquidity", {})
            liquidity_usd = safe_float_convert(liquidity_data.get("usd"))
            
            price_change_data = pair.get("priceChange", {})
            price_change_1h = safe_float_convert(price_change_data.get("h1"))
            
            # Apply filters
            if volume_24h < MIN_VOLUME:
                stats['volume_failed'] += 1
                continue
                
            if liquidity_usd < MIN_LIQUIDITY:
                stats['liquidity_failed'] += 1
                continue
                
            if abs(price_change_1h) < MIN_PRICE_CHANGE:
                stats['price_change_failed'] += 1
                continue
            
            # Quality check
            if not is_quality_pair(pair):
                stats['quality_failed'] += 1
                continue
            
            filtered.append(pair)
            stats['passed'] += 1
            
        except Exception as e:
            logger.warning(f"Error processing pair: {e}")
            stats['validation_failed'] += 1
            continue
    
    # Log filtering results
    logger.info(f"Filter results: {stats}")
    
    # Sort by volume (best first)
    filtered.sort(
        key=lambda x: safe_float_convert(x.get("volume", {}).get("h24")), 
        reverse=True
    )
    
    return filtered

def is_quality_pair(pair: Dict[str, Any]) -> bool:
    """
    Enhanced quality checks with comprehensive validation
    """
    try:
        # Check trading activity
        txns = pair.get("txns", {})
        h1_txns = txns.get("h1", {})
        
        if not h1_txns:
            return False
            
        buys = safe_int_convert(h1_txns.get("buys"))
        sells = safe_int_convert(h1_txns.get("sells"))
        total_txns = buys + sells
        
        # Minimum activity (avoid dead tokens)
        if total_txns < 10:  # Increased threshold
            return False
        
        # Check buy/sell balance (avoid obvious pump/dumps)
        if total_txns > 0:
            buy_ratio = buys / total_txns
            if buy_ratio < 0.15 or buy_ratio > 0.85:  # Too imbalanced
                return False
        
        # Market cap check
        market_cap = safe_float_convert(pair.get("marketCap"))
        if market_cap > 0:
            # Avoid micro caps (scam risk) and huge caps (low growth)
            if market_cap < 5000 or market_cap > 50_000_000:
                return False
        
        # Liquidity to volume ratio check
        liquidity = safe_float_convert(pair.get("liquidity", {}).get("usd"))
        volume = safe_float_convert(pair.get("volume", {}).get("h24"))
        
        if liquidity > 0 and volume > 0:
            ratio = volume / liquidity
            if ratio < 0.2 or ratio > 5:  # Suspicious ratio
                return False
        
        # Check for suspicious token names
        base_token = pair.get("baseToken", {})
        token_name = base_token.get("name", "").lower()
        token_symbol = base_token.get("symbol", "").lower()
        
        suspicious_words = ["test", "fake", "scam", "rug", "honeypot", "dead"]
        for word in suspicious_words:
            if word in token_name or word in token_symbol:
                return False
        
        return True
        
    except
