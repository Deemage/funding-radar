"""Historical candle loading from the public KuCoin API (no keys needed)."""
import csv
import json
import os
import time
import urllib.request
from collections import namedtuple

Candle = namedtuple("Candle", "t o h l c v")

API = "https://api.kucoin.com/api/v1/market/candles"
INTERVALS = {
    "1min": 60, "5min": 300, "15min": 900, "30min": 1800,
    "1hour": 3600, "4hour": 14400, "1day": 86400,
}
MAX_PER_REQUEST = 1500
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CACHE_TTL = 6 * 3600


def fetch_candles(symbol, interval, start, end):
    """Candles in [start, end), ascending by time. KuCoin returns up to 1500 per request."""
    step = INTERVALS[interval]
    rows = {}
    cursor = end
    while cursor > start:
        chunk_start = max(start, cursor - step * MAX_PER_REQUEST)
        url = f"{API}?type={interval}&symbol={symbol}&startAt={chunk_start}&endAt={cursor}"
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = json.load(resp)
        if body.get("code") != "200000":
            raise RuntimeError(f"KuCoin API error: {body}")
        # KuCoin format: [time, open, close, high, low, volume, turnover]
        for t, o, c, h, l, v, _ in body["data"]:
            t = int(t)
            rows[t] = Candle(t, float(o), float(h), float(l), float(c), float(v))
        cursor = chunk_start
        time.sleep(0.25)  # stay under the rate limit
    return [rows[t] for t in sorted(rows) if start <= t < end]


FUTURES_API = "https://api-futures.kucoin.com/api/v1/kline/query"
FUTURES_PER_REQUEST = 200


def fetch_futures_candles(symbol, start, end):
    """Hourly perpetual futures candles (closest to what KuCoin uses for liquidation)."""
    rows = {}
    cursor = start
    while cursor < end:
        chunk_end = min(end, cursor + 3600 * FUTURES_PER_REQUEST)
        url = f"{FUTURES_API}?symbol={symbol}&granularity=60&from={cursor * 1000}&to={chunk_end * 1000}"
        with urllib.request.urlopen(url, timeout=30) as resp:
            body = json.load(resp)
        if body.get("code") != "200000":
            raise RuntimeError(f"KuCoin Futures API error: {body}")
        # format: [time_ms, open, high, low, close, volume, ...]
        for r in body["data"] or []:
            t, o, h, l, c, v = r[:6]
            t //= 1000
            rows[t] = Candle(t, float(o), float(h), float(l), float(c), float(v))
        cursor = chunk_end
        time.sleep(0.2)
    return [rows[t] for t in sorted(rows) if start <= t < end]


def _cached(path, fetch):
    if os.path.exists(path) and time.time() - os.path.getmtime(path) < CACHE_TTL:
        with open(path, newline="") as f:
            return [Candle(int(r[0]), *map(float, r[1:])) for r in csv.reader(f)]
    candles = fetch()
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(candles)
    return candles


def load_candles(symbol="BTC-USDT", interval="1hour", days=180):
    """Candles for the last `days` days, cached in CSV."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    step = INTERVALS[interval]
    end = int(time.time()) // step * step  # closed candles only
    return _cached(os.path.join(CACHE_DIR, f"{symbol}_{interval}_{days}d.csv"),
                   lambda: fetch_candles(symbol, interval, end - days * 86400, end))


def load_futures_candles(futures_symbol, days=365):
    """Hourly futures candles (e.g. XBTUSDTM) for the last `days` days, cached."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    end = int(time.time()) // 3600 * 3600
    return _cached(os.path.join(CACHE_DIR, f"fut_{futures_symbol}_1hour_{days}d.csv"),
                   lambda: fetch_futures_candles(futures_symbol, end - days * 86400, end))
