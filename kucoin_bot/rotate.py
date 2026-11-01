"""Фандинг-арбитраж с ротацией: раз в N дней переотбираем монеты по фандингу за прошлый период.

Каждый период:
  - считаем средний фандинг каждой монеты за последние `lookback` дней (только прошлое, без подглядывания);
  - отбрасываем фьючерсы младше `min_age` дней и монеты с фандингом ниже `min_apr`;
  - берём топ-N; выбывшие закрываем, новые открываем, оставшиеся не трогаем (экономим комиссии).

Примеры:
  python rotate.py                       # топ-5, окно 30 дн., возраст от 90 дн., фандинг от 10%
  python rotate.py --n 10 --min-apr 5
  python rotate.py --sweep               # перебор параметров
"""
import argparse
import bisect
import statistics
import sys
from datetime import datetime, timezone

from arb import YEAR, FundingArb, simulate
from data import load_candles, load_futures_candles
from funding import futures_symbol, load_funding
from scan import liquid_pairs

DAY = 86400


class Coin:
    def __init__(self, sym, mm, listed, candles, funding, fut_candles):
        self.sym, self.mm, self.listed = sym, mm, listed
        self.candles = candles
        self.by_hour = {c.t: c for c in candles}
        self.fut_high = {c.t: c.h for c in fut_candles}
        self.times = [t for t, _ in funding]
        self.rates = [r for _, r in funding]
        self.per_year = YEAR / statistics.median(b - a for a, b in zip(self.times, self.times[1:]))

    def rates_between(self, start, end):
        return self.rates[bisect.bisect_left(self.times, start):bisect.bisect_left(self.times, end)]

    def apr(self, start, end):
        rates = self.rates_between(start, end)
        return statistics.mean(rates) * self.per_year * 100 if len(rates) >= 3 else None


def load_universe(args):
    coins = {}
    pairs = liquid_pairs(args.top, args.min_turnover)
    print(f"Загружаю {len(pairs)} монет...", flush=True)
    for sym, _, mm, listed in pairs:
        try:
            candles = load_candles(sym, "1hour", args.days)
            funding = load_funding(sym, args.days)
            fut = load_futures_candles(futures_symbol(sym), args.days)
        except Exception as e:
            print(f"  {sym}: ошибка {e}", flush=True)
            continue
        if len(candles) > 24 * 30 and len(funding) >= 20:
            coins[sym] = Coin(sym, mm, listed, candles, funding, fut)
            print(f"  {sym} готово", flush=True)
    return coins


def pick(coins, t, n, lookback, min_age, min_apr):
    scored = []
    for coin in coins.values():
        if t - coin.listed < min_age * DAY or t not in coin.by_hour:
            continue
        apr = coin.apr(t - lookback * DAY, t)
        if apr is not None and apr >= min_apr:
            scored.append((apr, coin.sym))
    scored.sort(reverse=True)
    return scored[:n]


def rotate(coins, cash=1000.0, n=5, lookback=30, period=30, min_age=90, min_apr=10.0, leverage=2.0, log=False):
    start = min(c.candles[0].t for c in coins.values()) + lookback * DAY
    end = max(c.candles[-1].t for c in coins.values())
    active, last_price = {}, {}
    fees = liquidations = opened = 0
    next_rotation = start
    peak, max_dd = cash, 0.0
    month_start_equity = cash

    def equity():
        return cash + sum(a.equity(last_price[s]) for s, a in active.items())

    for t in range(start, end + 3600, 3600):
        if t >= next_rotation:
            picks = pick(coins, t, n, lookback, min_age, min_apr)
            wanted = {s for _, s in picks}
            total = equity()
            if log and t > start:
                d = datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")
                print(f"  {d}  капитал {total:>9,.2f} ({(total / month_start_equity - 1) * 100:+.2f}% за период)")
            month_start_equity = total
            for s in list(active):
                if s not in wanted:
                    arb = active.pop(s)
                    arb.close(last_price[s])
                    cash += arb.cash
                    fees += arb.fees
                    liquidations += arb.liquidations
            new = [s for _, s in picks if s not in active]
            for s in new:
                size = min(cash / len(new), total / n) if new else 0
                if size < 1:
                    continue
                c = coins[s].by_hour[t]
                arb = FundingArb(size, leverage, mm=coins[s].mm, events_per_year=coins[s].per_year)
                arb.open(c.o)
                active[s] = arb
                last_price[s] = c.o
                cash -= size
                opened += 1
            if log:
                d = datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")
                desc = ", ".join(f"{s.split('-')[0]} {a:.0f}%" for a, s in picks) or "нет кандидатов — сидим в USDT"
                print(f"  {d}  в позиции: {desc}")
            next_rotation = t + period * DAY

        for s, arb in active.items():
            coin = coins[s]
            c = coin.by_hour.get(t)
            if c is None:
                continue
            i = bisect.bisect_left(coin.times, t)
            while i < len(coin.times) and coin.times[i] < t + 3600:
                arb.on_funding(coin.rates[i], c.o)
                i += 1
            arb.on_candle(c, coin.fut_high.get(t))
            last_price[s] = c.c

        e = equity()
        peak = max(peak, e)
        max_dd = max(max_dd, (peak - e) / peak)

    final = equity()
    fees += sum(a.fees for a in active.values())
    liquidations += sum(a.liquidations for a in active.values())
    years = (end - start) / YEAR
    return {"final": final, "start": start, "end": end, "years": years, "max_dd": max_dd * 100,
            "fees": fees, "liq": liquidations, "opened": opened}


def report(label, r, cash):
    ret = r["final"] / cash - 1
    apr = ((1 + ret) ** (1 / r["years"]) - 1) * 100 if ret > -1 else -100
    print(f"{label:<44} {r['final']:>9,.2f} {ret * 100:>+7.2f}% {apr:>+7.2f}% {r['max_dd']:>7.2f}% "
          f"{r['fees']:>7.2f} {r['opened']:>6} {r['liq']:>5}")


HEADER = (f"{'Вариант':<44} {'Итог $':>9} {'Доход':>8} {'Годовых':>8} {'Просадка':>8} "
          f"{'Комис.':>7} {'Входов':>6} {'Ликв.':>5}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=40)
    ap.add_argument("--min-turnover", type=float, default=5)
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--cash", type=float, default=1000)
    ap.add_argument("--leverage", type=float, default=2)
    ap.add_argument("--n", type=int, default=5)
    ap.add_argument("--lookback", type=int, default=30)
    ap.add_argument("--period", type=int, default=30)
    ap.add_argument("--min-age", type=int, default=90)
    ap.add_argument("--min-apr", type=float, default=10)
    ap.add_argument("--sweep", action="store_true")
    args = ap.parse_args()

    coins = load_universe(args)
    if not coins:
        sys.exit("Не удалось загрузить ни одной монеты")
    base = dict(cash=args.cash, leverage=args.leverage)

    if not args.sweep:
        print(f"\nРотация: топ-{args.n}, окно {args.lookback} дн., раз в {args.period} дн., "
              f"возраст ≥{args.min_age} дн., фандинг ≥{args.min_apr:g}% годовых")
        r = rotate(coins, n=args.n, lookback=args.lookback, period=args.period,
                   min_age=args.min_age, min_apr=args.min_apr, log=True, **base)
        print("\n" + HEADER)
        print("-" * len(HEADER))
        report("Ротация", r, args.cash)
    else:
        print("\n" + HEADER)
        print("-" * len(HEADER))
        for n in (3, 5, 10):
            for lookback in (14, 30):
                for min_age in (0, 90, 180):
                    for min_apr in (5, 10, 20):
                        r = rotate(coins, n=n, lookback=lookback, period=30, min_age=min_age, min_apr=min_apr, **base)
                        report(f"топ-{n} окно {lookback}д возраст≥{min_age}д фанд≥{min_apr}%", r, args.cash)

    # эталон: BTC и ETH без ротации за тот же период
    for ref in ("BTC-USDT", "ETH-USDT"):
        coin = coins.get(ref)
        if not coin:
            continue
        test = [c for c in coin.candles if c.t >= r["start"]]
        arb = FundingArb(args.cash, args.leverage, mm=coin.mm, events_per_year=coin.per_year)
        final, dd = simulate(arb, test, list(zip(coin.times, coin.rates)), coin.fut_high)
        report(f"{ref} всегда в позиции", {**r, "final": final, "max_dd": dd * 100, "fees": arb.fees,
                                            "opened": 1, "liq": arb.liquidations}, args.cash)


if __name__ == "__main__":
    main()
