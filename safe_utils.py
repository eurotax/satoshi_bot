import math
import logging
import asyncio
import time
from typing import Any, Union, Optional
from functools import wraps

logger = logging.getLogger(__name__)

def safe_float_convert(value: Any, default: float = 0.0) -> float:
    """
    Safe float conversion with full validation
    Handles None, str, int, float, and edge cases
    """
    if value is None:
        return default
    
    # Handle numeric types
    if isinstance(value, (int, float)):
        if math.isnan(value) or math.isinf(value):
            logger.warning(f"Invalid numeric value: {value}")
            return default
        return float(value)
    
    # Handle string types
    if isinstance(value, str):
        value = value.strip()
        if not value or value.lower() in ('null', 'none', 'undefined'):
            return default
            
        try:
            result = float(value)
            if math.isnan(result) or math.isinf(result):
                return default
            return result
        except (ValueError, OverflowError):
            logger.warning(f"Failed to convert '{value}' to float")
            return default
    
    return default

def safe_int_convert(value: Any, default: int = 0) -> int:
    """Safe int conversion"""
    try:
        float_val = safe_float_convert(value, default)
        return int(float_val)
    except (ValueError, OverflowError):
        return default

def validate_pair_data(pair: dict) -> bool:
    """
    Validate DEXScreener API data structure
    Checks if all required fields are present and valid
    """
    if not isinstance(pair, dict):
        return False
        
    # Check required fields
    required_fields = ['baseToken', 'quoteToken', 'priceUsd']
    for field in required_fields:
        if field not in pair:
            logger.debug(f"Missing field: {field}")
            return False
    
    # Validate token structure
    base_token = pair.get('baseToken', {})
    quote_token = pair.get('quoteToken', {})
    
    if not isinstance(base_token, dict) or not isinstance(quote_token, dict):
        return False
        
    if not base_token.get('symbol') or not quote_token.get('symbol'):
        return False
    
    # Validate price
    price_usd = safe_float_convert(pair.get('priceUsd'))
    if price_usd <= 0:
        return False
    
    return True

def retry_with_exponential_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for automatic retry with exponential backoff
    Used for API calls that may temporarily fail
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries: {e}")
                        raise e
                    
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{max_retries} in {delay}s: {e}")
                    await asyncio.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator

def log_function_call(func):
    """Add logging for debugging"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} completed in {execution_time:.2f}s")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    return wrapper
