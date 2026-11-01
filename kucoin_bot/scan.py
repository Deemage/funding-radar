"""Funding arbitrage scanner across all liquid KuCoin futures.

Honest test: coins are selected by first-half-year funding,
and strategy returns are measured only on the second half (unseen by the selection).

Examples:
  python scan.py                         # top 40 by turnover, 365 days of history
  python scan.py --top 60 --min-turnover 3
"""
import argparse
import json
import statistics
import sys
import urllib.request

from arb import YEAR, FundingArb, simulate
from data import load_candles
from funding import load_funding

CONTRACTS = "https://api-futures.kucoin.com/api/v1/contracts/active"
SPOT_SYMBOLS = "https://api.kucoin.com/api/v2/symbols"


def get_json(url):
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)["data"]


def liquid_pairs(top, min_turnover):
    """USDT perpetuals that also have a matching spot pair, by turnover descending."""
    spot = {s["symbol"] for s in get_json(SPOT_SYMBOLS) if s["enableTrading"]}
    pairs = []
    for c in get_json(CONTRACTS):
        if c["quoteCurrency"] != "USDT" or c["expireDate"] is not None or c["isInverse"]:
            continue
        base = "BTC" if c["baseCurrency"] == "XBT" else c["baseCurrency"]
        turnover = float(c["turnoverOf24h"] or 0)
        if f"{base}-USDT" in spot and turnover >= min_turnover * 1e6:
            pairs.append((f"{base}-USDT", turnover, float(c["maintainMargin"]), c["firstOpenDate"] // 1000))
    pairs.sort(key=lambda p: -p[1])
    return pairs[:top]


def apr(rates, per_year):
    return statistics.mean(rates) * per_year * 100 if rates else float("nan")


def scan_one(sym, mm, args):
    candles = load_candles(sym, "1hour", args.days)
    funding = load_funding(sym, args.days)
    if len(candles) < 24 * 60 or len(funding) < 20:
        return None
    per_year = YEAR / statistics.median(b[0] - a[0] for a, b in zip(funding, funding[1:]))
    mid_t = candles[len(candles) // 2].t
    h1 = [r for t, r in funding if t < mid_t]
    h2 = [r for t, r in funding if t >= mid_t]
    test = candles[len(candles) // 2:]

    arb = FundingArb(args.cash, args.leverage, mm=mm, events_per_year=per_year)
    final, dd = simulate(arb, test, funding)
    years = (test[-1].t - test[0].t) / YEAR
    ret = final / args.cash - 1
    return {
        "sym": sym,
        "days": (candles[-1].t - candles[0].t) // 86400,
        "apr_h1": apr(h1, per_year),
        "apr_h2": apr(h2, per_year),
        "neg_h2": sum(r < 0 for r in h2) / len(h2) * 100 if h2 else 0,
        "sim_apr": ((1 + ret) ** (1 / years) - 1) * 100 if ret > -1 else -100,
        "sim_dd": dd * 100,
        "liq": arb.liquidations,
        "rebal": arb.rebalances,
        "mm": mm,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--min-turnover", type=float, default=5, help="min futures 24h turnover, $M")
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--cash", type=float, default=1000)
    ap.add_argument("--leverage", type=float, default=2)
    ap.add_argument("--pick", type=int, default=10, help="how many coins to pick by first-half funding")
    args = ap.parse_args()

    pairs = liquid_pairs(args.top, args.min_turnover)
    print(f"Scanning {len(pairs)} coins, {args.days}d history, short leverage {args.leverage:g}x...", flush=True)
    rows = []
    for i, (sym, _, mm, _) in enumerate(pairs, 1):
        try:
            r = scan_one(sym, mm, args)
        except Exception as e:  # one broken coin shouldn't kill the whole scan
            print(f"  [{i}/{len(pairs)}] {sym}: error {e}", flush=True)
            continue
        print(f"  [{i}/{len(pairs)}] {sym}: " + ("not enough history" if r is None else f"funding {r['apr_h1']:.1f}% → {r['apr_h2']:.1f}%"), flush=True)
        if r:
            rows.append(r)

    # coins with no first-half funding (futures listed later) go last
    rows.sort(key=lambda r: -r["apr_h1"] if r["apr_h1"] == r["apr_h1"] else float("inf"))
    header = (f"\n{'Coin':<12} {'Days':>5} {'Fund.H1':>8} {'Fund.H2':>8} {'Neg.H2':>7} "
              f"{'Arb H2 APR':>11} {'Max DD':>8} {'Liq.':>5} {'Rebal.':>6} {'MM':>6}")
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r['sym']:<12} {r['days']:>5} {r['apr_h1']:>+7.1f}% {r['apr_h2']:>+7.1f}% {r['neg_h2']:>6.0f}% "
              f"{r['sim_apr']:>+10.2f}% {r['sim_dd']:>7.2f}% {r['liq']:>5} {r['rebal']:>6} {r['mm'] * 100:>5.1f}%")

    full = [r for r in rows if r["days"] >= args.days - 2]
    picked = full[:args.pick]
    if picked:
        avg = lambda xs: statistics.mean(xs)
        print(f"\nSelection: top {len(picked)} by first-half funding (coins with full history only)")
        print(f"  funding H1: {avg([r['apr_h1'] for r in picked]):.1f}% → H2: {avg([r['apr_h2'] for r in picked]):.1f}% APR")
        print(f"  arbitrage on H2 (equal weights): {avg([r['sim_apr'] for r in picked]):+.2f}% APR, "
              f"worst coin {min(r['sim_apr'] for r in picked):+.2f}%, liquidations {sum(r['liq'] for r in picked)}")
        for ref in ("BTC-USDT", "ETH-USDT"):
            r = next((r for r in rows if r["sym"] == ref), None)
            if r:
                print(f"  for comparison {ref}: {r['sim_apr']:+.2f}% APR")


if __name__ == "__main__":
    main()
