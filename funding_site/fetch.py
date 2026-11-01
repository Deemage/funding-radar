"""Data collection from all exchanges: current funding, N-day history, per-coin summary."""
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from exchanges import ALL


def apr(hist, start, end, interval_h):
    """APR from actual payments: sum of rates over the period, annualized.
    Independent of the interval: exchanges sometimes change it (8h → 4h → 1h), so mean rate × current interval is wrong."""
    rates = [r for t, r in hist if t >= start]
    if not rates:
        return None
    first = min(t for t, _ in hist if t >= start)
    span_days = min(end - start, end - first + interval_h * 3600) / 86400  # young coin: use its actual history
    return sum(rates) * 365 / span_days * 100


def enrich(m, start, end):
    """Market metrics from its history (m["history"])."""
    hist = m["history"]
    rates = [r for _, r in hist]
    m["apr_7d"] = apr(hist, end - 7 * 86400, end, m["interval_h"])
    m["apr_30d"] = apr(hist, start, end, m["interval_h"])
    m["neg_share"] = sum(r < 0 for r in rates) / len(rates) * 100 if rates else None


def summarize(base, markets):
    """Coin summary: best exchange to hedge on, cross-exchange spread, age and risk."""
    markets = {k: m for k, m in markets.items() if m.get("apr_7d") is not None}
    if not markets:
        return None
    ages = [m["age_days"] for m in markets.values() if m["age_days"] is not None]
    mms = [m["mm"] for m in markets.values() if m.get("mm") is not None]
    hedge = [m for m in markets.values() if m["spot"]]
    best = max(hedge, key=lambda m: m["apr_7d"]) if hedge else None
    spread = None
    if len(markets) >= 2:
        hi = max(markets.values(), key=lambda m: m["apr_7d"])
        lo = min(markets.values(), key=lambda m: m["apr_7d"])
        spread = {"short": hi["exchange"], "long": lo["exchange"], "apr_7d": hi["apr_7d"] - lo["apr_7d"],
                  "now": hi["apr_now"] - lo["apr_now"]}
    return {
        "base": base,
        "markets": markets,
        "turnover": sum(m["turnover"] for m in markets.values()),
        "age_days": max(ages) if ages else None,  # age of the oldest market = age of the coin
        "high_mm": bool(mms) and max(mms) >= 0.02,
        "best": best["exchange"] if best else None,
        "best_apr_7d": best["apr_7d"] if best else None,
        "spread": spread,
    }


def _load_markets(ex, log):
    try:
        ms = ex.markets()
        log(f"{ex.name}: {len(ms)} futures")
        return ms
    except Exception as e:  # exchange unavailable (e.g. region block): build the site without it
        log(f"{ex.name}: unavailable ({e})")
        return []


def _load_history(ex, markets, start, end, log):
    for m in markets:
        try:
            m["history"] = ex.history(m["symbol"], start, end)
        except Exception as e:
            log(f"  {ex.name} {m['symbol']}: history error {e}")
            continue
        enrich(m, start, end)
    log(f"{ex.name}: history loaded ({len(markets)})")


def collect(cfg, log=print):
    now = int(time.time())
    with ThreadPoolExecutor(len(ALL)) as pool:
        per_exchange = list(pool.map(lambda ex: _load_markets(ex, log), ALL))

    coins = defaultdict(dict)
    for ex, markets in zip(ALL, per_exchange):
        for m in markets:
            if m["turnover"] >= cfg.MIN_MARKET_TURNOVER_USD:
                coins[m["base"]][ex.key] = m
    total = lambda b: sum(m["turnover"] for m in coins[b].values())
    bases = sorted((b for b in coins if total(b) >= cfg.MIN_TURNOVER_USD), key=lambda b: -total(b))[:cfg.MAX_COINS]

    start = now - cfg.HISTORY_DAYS * 86400
    with ThreadPoolExecutor(len(ALL)) as pool:
        for ex in ALL:
            markets = [coins[b][ex.key] for b in bases if ex.key in coins[b]]
            pool.submit(_load_history, ex, markets, start, now, log)

    return [c for c in (summarize(b, coins[b]) for b in bases) if c], now
