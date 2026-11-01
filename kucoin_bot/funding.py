"""KuCoin Futures funding rate history (public API, no keys needed)."""
import csv
import json
import os
import time
import urllib.request

from data import CACHE_DIR, CACHE_TTL

API = "https://api-futures.kucoin.com/api/v1/contract/funding-rates"
PAGE_LIMIT = 100  # KuCoin returns at most 100 rows per request


def futures_symbol(spot_symbol):
    """BTC-USDT → XBTUSDTM (KuCoin calls bitcoin XBT on futures)."""
    base, quote = spot_symbol.split("-")
    return ("XBT" if base == "BTC" else base) + quote + "M"


def _get(symbol, start_ms, end_ms):
    url = f"{API}?symbol={symbol}&from={start_ms}&to={end_ms}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        body = json.load(resp)
    if body.get("code") != "200000":
        raise RuntimeError(f"KuCoin Futures API error: {body}")
    time.sleep(0.2)
    return body["data"] or []


def fetch_funding(symbol, start_ms, end_ms):
    """[(time_sec, rate)] ascending. If a window hits the limit, split it in half."""
    out = {}
    window = 30 * 86400 * 1000
    cursor = start_ms
    while cursor < end_ms:
        chunk_end = min(end_ms, cursor + window)
        rows = _get(symbol, cursor, chunk_end)
        if len(rows) >= PAGE_LIMIT and window > 3600 * 1000:
            window //= 2
            continue
        for r in rows:
            out[r["timepoint"] // 1000] = float(r["fundingRate"])
        cursor = chunk_end
    return sorted(out.items())


def load_funding(spot_symbol="BTC-USDT", days=730):
    symbol = futures_symbol(spot_symbol)
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, f"funding_{symbol}_{days}d.csv")
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < CACHE_TTL:
        with open(path, newline="") as f:
            return [(int(t), float(r)) for t, r in csv.reader(f)]

    end = int(time.time()) * 1000
    rows = fetch_funding(symbol, end - days * 86400 * 1000, end)
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    return rows
