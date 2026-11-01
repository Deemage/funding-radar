"""Сканер фандинг-арбитража по всем ликвидным фьючерсам KuCoin.

Честная проверка: монеты отбираются по фандингу первого полугодия,
а доход стратегии считается только на втором (которое отбор «не видел»).

Примеры:
  python scan.py                         # топ-40 по обороту, история 365 дней
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
    """Бессрочные USDT-фьючерсы, у которых есть такая же пара на споте, по убыванию оборота."""
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
    ap.add_argument("--min-turnover", type=float, default=5, help="мин. оборот фьючерса за 24ч, млн $")
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--cash", type=float, default=1000)
    ap.add_argument("--leverage", type=float, default=2)
    ap.add_argument("--pick", type=int, default=10, help="сколько монет отбирать по 1-му полугодию")
    args = ap.parse_args()

    pairs = liquid_pairs(args.top, args.min_turnover)
    print(f"Сканирую {len(pairs)} монет, история {args.days} дн., плечо шорта {args.leverage:g}x...", flush=True)
    rows = []
    for i, (sym, _, mm, _) in enumerate(pairs, 1):
        try:
            r = scan_one(sym, mm, args)
        except Exception as e:  # одна битая монета не должна валить весь скан
            print(f"  [{i}/{len(pairs)}] {sym}: ошибка {e}", flush=True)
            continue
        print(f"  [{i}/{len(pairs)}] {sym}: " + ("мало истории" if r is None else f"фандинг {r['apr_h1']:.1f}% → {r['apr_h2']:.1f}%"), flush=True)
        if r:
            rows.append(r)

    # монеты без фандинга в 1-м полугодии (фьючерс появился позже) — в конец
    rows.sort(key=lambda r: -r["apr_h1"] if r["apr_h1"] == r["apr_h1"] else float("inf"))
    header = (f"\n{'Монета':<12} {'Дней':>5} {'Фанд.1п':>8} {'Фанд.2п':>8} {'Отр.2п':>7} "
              f"{'Арб 2п год.':>11} {'Просадка':>8} {'Ликв.':>5} {'Ребал.':>6} {'MM':>6}")
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r['sym']:<12} {r['days']:>5} {r['apr_h1']:>+7.1f}% {r['apr_h2']:>+7.1f}% {r['neg_h2']:>6.0f}% "
              f"{r['sim_apr']:>+10.2f}% {r['sim_dd']:>7.2f}% {r['liq']:>5} {r['rebal']:>6} {r['mm'] * 100:>5.1f}%")

    full = [r for r in rows if r["days"] >= args.days - 2]
    picked = full[:args.pick]
    if picked:
        avg = lambda xs: statistics.mean(xs)
        print(f"\nОтбор: топ-{len(picked)} по фандингу 1-го полугодия (только монеты с полной историей)")
        print(f"  фандинг 1п: {avg([r['apr_h1'] for r in picked]):.1f}% → 2п: {avg([r['apr_h2'] for r in picked]):.1f}% годовых")
        print(f"  арбитраж на 2п (поровну во все): {avg([r['sim_apr'] for r in picked]):+.2f}% годовых, "
              f"худшая монета {min(r['sim_apr'] for r in picked):+.2f}%, ликвидаций {sum(r['liq'] for r in picked)}")
        for ref in ("BTC-USDT", "ETH-USDT"):
            r = next((r for r in rows if r["sym"] == ref), None)
            if r:
                print(f"  для сравнения {ref}: {r['sim_apr']:+.2f}% годовых")


if __name__ == "__main__":
    main()
