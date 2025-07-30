import requests

def fetch_dex_signals(min_volume_usd=10000, min_change_1h=20):
    url = "https://api.dexscreener.com/latest/dex/pairs"
    res = requests.get(url, timeout=10)
    if res.status_code != 200:
        return []

    pairs = res.json().get("pairs", [])
    signals = []

    for pair in pairs:
        try:
            volume = float(pair["volume"]["h1"])
            change = float(pair["priceChange"]["h1"])
            if volume >= min_volume_usd and change >= min_change_1h:
                signals.append({
                    "name": pair["baseToken"]["name"],
                    "symbol": pair["baseToken"]["symbol"],
                    "dex": pair["dexId"],
                    "price": float(pair["priceUsd"]),
                    "change": change,
                    "url": pair["url"],
                })
        except Exception:
            continue

    return signals
