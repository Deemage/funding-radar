"""Strategy backtests on KuCoin history.

Examples:
  python backtest.py                                  # compare everything on BTC-USDT over 180 days
  python backtest.py --symbol ETH-USDT --days 365
  python backtest.py --grids 30 --range 15            # ±15% grid, 30 cells
  python backtest.py --sweep                          # grid parameter sweep
  python backtest.py --days 730 --walkforward         # fit on year 1, test on year 2
"""
import argparse
import sys
from datetime import datetime, timezone

from data import load_candles
from engine import run
from strategies import DCA, BuyHold, Grid


def fmt_row(r):
    return (f"{r['name']:<46} {r['final']:>10,.2f} {r['return_pct']:>+8.2f}% "
            f"{r['max_dd_pct']:>7.2f}% {r['trades']:>7} {r['fees']:>8.2f} {r['in_coin_pct']:>6.1f}%")


HEADER = (f"{'Стратегия':<46} {'Итог $':>10} {'Доход':>9} {'Просадка':>8} "
          f"{'Сделок':>7} {'Комис.$':>8} {'В монете':>7}")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTC-USDT")
    ap.add_argument("--interval", default="1hour")
    ap.add_argument("--days", type=int, default=180)
    ap.add_argument("--cash", type=float, default=1000)
    ap.add_argument("--fee", type=float, default=0.1, help="комиссия в %%, KuCoin по умолчанию 0.1")
    ap.add_argument("--grids", type=int, default=20)
    ap.add_argument("--range", type=float, default=10, help="диапазон грида ±%% от стартовой цены")
    ap.add_argument("--dca", type=float, default=None, help="сумма DCA за покупку, по умолчанию так, чтобы хватило на весь период")
    ap.add_argument("--reset", type=float, default=5, help="перестройка грида при выходе за диапазон на N%%")
    ap.add_argument("--sweep", action="store_true", help="перебор параметров грида")
    ap.add_argument("--walkforward", action="store_true", help="подбор на 1-й половине, проверка на 2-й")
    args = ap.parse_args()

    candles = load_candles(args.symbol, args.interval, args.days)
    fee = args.fee / 100
    first, last = candles[0], candles[-1]
    d = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")
    print(f"{args.symbol} {args.interval}: {len(candles)} свечей, {d(first.t)} → {d(last.t)}, "
          f"цена {first.o:,.2f} → {last.c:,.2f} ({(last.c / first.o - 1) * 100:+.2f}%)")
    print(f"Капитал ${args.cash:,.0f}, комиссия {args.fee}%\n")
    print(HEADER)
    print("-" * len(HEADER))

    if args.sweep:
        results = [run(make(), candles, args.cash, fee) for make in grid_configs()]
        results.append(run(BuyHold(), candles, args.cash, fee))
        for r in sorted(results, key=lambda r: -r["return_pct"]):
            print(fmt_row(r))
        return

    if args.walkforward:
        walkforward(candles, args, fee)
        return

    for s in baselines(args.dca or round(args.cash / args.days, 2)) + [
        Grid(grids=args.grids, lower_pct=args.range, upper_pct=args.range),
        Grid(grids=args.grids, lower_pct=args.range, upper_pct=args.range, reset_pct=args.reset),
    ]:
        print(fmt_row(run(s, candles, args.cash, fee)))


def baselines(dca_amount):
    return [
        BuyHold(),
        DCA(amount=dca_amount, every_hours=24),
        DCA(amount=dca_amount * 0.7, every_hours=24, dip_pct=5, dip_mult=2),
    ]


def grid_configs():
    """Grid factories for the sweep: range × cell count × reset."""
    return [lambda r=r, g=g, x=x: Grid(grids=g, lower_pct=r, upper_pct=r, reset_pct=x)
            for r in (5, 10, 15, 20, 30) for g in (10, 20, 30, 50) for x in (None, 5)]


def walkforward(candles, args, fee):
    """Fit grid parameters on the first half of history, test honestly on the second."""
    mid = len(candles) // 2
    train, test = candles[:mid], candles[mid:]
    configs = grid_configs()
    ranked = sorted(range(len(configs)), key=lambda i: -run(configs[i](), train, args.cash, fee)["return_pct"])
    top = ranked[:5]

    print(f"Обучение: первая половина ({len(train)} свечей). Топ-5 гридов:")
    for i in top:
        print(fmt_row(run(configs[i](), train, args.cash, fee)))

    move = (test[-1].c / test[0].o - 1) * 100
    print(f"\nПроверка: вторая половина ({len(test)} свечей, цена {move:+.2f}%). Те же 5 гридов + эталоны:")
    for i in top:
        print(fmt_row(run(configs[i](), test, args.cash, fee)))
    for s in baselines(round(args.cash / (args.days / 2), 2)):
        print(fmt_row(run(s, test, args.cash, fee)))


if __name__ == "__main__":
    main()
