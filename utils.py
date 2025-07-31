import httpx
import logging
from config import MIN_VOLUME, MIN_LIQUIDITY, MIN_PRICE_CHANGE

logger = logging.getLogger(__name__)

DEXSCREENER_URL = "https://api.dexscreener.com/latest/dex/pairs/solana"


async def fetch_pairs():
    """Pobiera dane z DEXScreener API"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(DEXSCREENER_URL)
            response.raise_for_status()
            data = response.json()
            return data.get("pairs", [])
    except Exception as e:
        logger.error(f"fetch_pairs error: {e}")
        return []


def filter_pairs(pairs):
    """Filtruje pary według określonych progów"""
    filtered = []
    for pair in pairs:
        try:
            volume = float(pair.get("volume", {}).get("h24", 0))
            liquidity = float(pair.get("liquidity", {}).get("usd", 0))
            price_change = float(pair.get("priceChange", {}).get("h1", 0))

            if volume >= MIN_VOLUME and liquidity >= MIN_LIQUIDITY and abs(price_change) >= MIN_PRICE_CHANGE:
                filtered.append(pair)
        except Exception as e:
            logger.warning(f"Skipping pair due to error: {e}")
            continue

    return filtered


def format_pair_message(pair, include_meta=False):
    """Formatuje wiadomość o pojedynczym sygnale"""
    try:
        base = pair["baseToken"]["symbol"]
        quote = pair["quoteToken"]["symbol"]
        name = f"{base}/{quote}"
        price = pair["priceUsd"]
        change = pair["priceChange"]["h1"]
        link = pair["url"]

        emoji = "📈" if float(change) > 0 else "📉"

        msg = f"{emoji} [{name}]({link})\n💰 ${price} ({change}%)"

        if include_meta:
            volume = pair["volume"]["h24"]
            liquidity = pair["liquidity"]["usd"]
            msg += f"\n🔄 Volume: ${volume}\n💧 Liquidity: ${liquidity}"

        return msg
    except Exception as e:
        logger.warning(f"Error formatting pair: {e}")
        return ""

