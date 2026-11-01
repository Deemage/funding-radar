"""Funding arbitrage backtest on KuCoin: coin on spot + short perpetual of the same size.
The coin's price cancels out; income = funding that longs pay to shorts.

Examples:
  python arb.py                                     # BTC, ETH, SOL over 2 years
  python arb.py --symbols BTC-USDT --leverage 3
  python arb.py --enter-apr 15                      # smart mode enters only when funding > 15% APR

Simplifications: futures priced at spot (basis ignored), market orders (taker),
liquidation checked against the hourly candle high.
"""
import argparse
import statistics
import sys
from collections import deque
from datetime import datetime, timezone

from data import load_candles
from funding import futures_symbol, load_funding

YEAR = 365 * 86400


class FundingArb:
    def __init__(self, cash=1000.0, leverage=2.0, spot_fee=0.001, fut_fee=0.0006, mm=0.005,
                 smart=False, enter_apr=10.0, exit_apr=0.0, lookback=9, events_per_year=3 * 365):
        self.cash = cash
        self.L = leverage
        self.spot_fee, self.fut_fee, self.mm = spot_fee, fut_fee, mm
        self.smart = smart
        self.enter_apr, self.exit_apr = enter_apr, exit_apr
        self.recent = deque(maxlen=lookback)
        self.events_per_year = events_per_year
        self.q = 0.0       # coins on spot = short size
        self.entry = 0.0   # short entry price
        self.margin = 0.0  # futures account margin (including funding received)
        self.funding_got = self.fees = 0.0
        self.rebalances = self.liquidations = self.switches = 0
        self.hours_in = 0

    def fut_equity(self, p):
        return self.margin + self.q * (self.entry - p)

    def equity(self, p):
        return self.cash + self.q * p + self.fut_equity(p)

    def _resize(self, p, target_q):
        """Resize the position to target_q coins (spot and short together); margin = remaining capital."""
        total = self.equity(p)
        fee = abs(target_q - self.q) * p * (self.spot_fee + self.fut_fee)
        self.fees += fee
        self.q, self.entry = target_q, p
        if target_q:
            self.margin, self.cash = total - fee - target_q * p, 0.0
        else:
            self.margin, self.cash = 0.0, total - fee

    def open(self, p):
        self._resize(p, self.equity(p) * self.L / (self.L + 1) / p)

    def close(self, p):
        self._resize(p, 0.0)

    def on_funding(self, rate, p):
        self.recent.append(rate)
        if self.q:
            pay = self.q * p * rate  # positive funding: longs pay shorts
            self.margin += pay
            self.funding_got += pay
        if not self.smart or len(self.recent) < self.recent.maxlen:
            return
        apr = statistics.mean(self.recent) * self.events_per_year * 100
        if not self.q and apr >= self.enter_apr:
            self.open(p)
            self.switches += 1
        elif self.q and apr < self.exit_apr:
            self.close(p)
            self.switches += 1

    def on_candle(self, c, fut_high=None):
        """fut_high is the hourly futures high, used for the liquidation check: thin alts can have
        +100% spot wicks that never happened on futures (or in the mark price)."""
        if not self.q:
            return
        self.hours_in += 1
        high = fut_high or c.h
        if self.fut_equity(high) <= self.mm * self.q * high:
            # short liquidated: futures account goes to zero, spot is left unhedged
            self.liquidations += 1
            self.margin, self.entry = 0.0, c.c  # futures account = 0, only spot remains
            self.open(c.c)
            return
        ratio = self.fut_equity(c.c) / (self.q * c.c)
        target = 1 / self.L
        if ratio < target * 0.5 or ratio > target * 2:
            self.open(c.c)
            self.rebalances += 1


def simulate(arb, candles, funding, fut_high=None):
    """fut_high: {hour: futures high} for liquidation checks; without it, spot is used."""
    fut_high = fut_high or {}
    by_hour = {c.t: c for c in candles}
    events = deque(f for f in funding if f[0] >= candles[0].t)
    if not arb.smart:
        arb.open(candles[0].o)
    peak, max_dd = arb.equity(candles[0].o), 0.0
    for c in candles:
        while events and events[0][0] < c.t + 3600:
            t, rate = events.popleft()
            arb.on_funding(rate, by_hour.get(t // 3600 * 3600, c).o)
        arb.on_candle(c, fut_high.get(c.t))
        e = arb.equity(c.c)
        peak = max(peak, e)
        max_dd = max(max_dd, (peak - e) / peak)
    return arb.equity(candles[-1].c), max_dd


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", default="BTC-USDT,ETH-USDT,SOL-USDT")
    ap.add_argument("--days", type=int, default=730)
    ap.add_argument("--cash", type=float, default=1000)
    ap.add_argument("--leverage", type=float, default=2, help="short leverage; 2 = a third of capital as margin")
    ap.add_argument("--fut-fee", type=float, default=0.06, help="futures fee %%, taker 0.06")
    ap.add_argument("--spot-fee", type=float, default=0.1)
    ap.add_argument("--enter-apr", type=float, default=10)
    args = ap.parse_args()

    print(f"Capital ${args.cash:,.0f}, short leverage {args.leverage:g}x, fees spot {args.spot_fee}% / futures {args.fut_fee}%\n")
    header = (f"{'Coin':<10} {'Mode':<18} {'Final $':>9} {'Return':>8} {'APR':>8} {'Max DD':>8} "
              f"{'Funding$':>9} {'Fees $':>8} {'Rebal.':>6} {'Liq.':>5} {'In pos.':>9}")
    print(header)
    print("-" * len(header))
    for sym in args.symbols.split(","):
        candles = load_candles(sym, "1hour", args.days)
        funding = load_funding(sym, args.days)
        if not funding:
            print(f"{sym:<10} no futures {futures_symbol(sym)}")
            continue
        gaps = [b[0] - a[0] for a, b in zip(funding, funding[1:])]
        per_year = YEAR / statistics.median(gaps)
        rates = [r for _, r in funding]
        years = (candles[-1].t - candles[0].t) / YEAR

        for label, smart in (("always in position", False), (f"only >{args.enter_apr:g}% APR", True)):
            arb = FundingArb(args.cash, args.leverage, args.spot_fee / 100, args.fut_fee / 100,
                             smart=smart, enter_apr=args.enter_apr, events_per_year=per_year)
            final, dd = simulate(arb, candles, funding)
            ret = final / args.cash - 1
            apr = ((1 + ret) ** (1 / years) - 1) * 100 if ret > -1 else -100
            print(f"{sym:<10} {label:<18} {final:>9,.2f} {ret * 100:>+7.2f}% {apr:>+7.2f}% {dd * 100:>7.2f}% "
                  f"{arb.funding_got:>9.2f} {arb.fees:>8.2f} {arb.rebalances:>6} {arb.liquidations:>5} "
                  f"{arb.hours_in / len(candles) * 100:>8.1f}%")
        neg = sum(r < 0 for r in rates) / len(rates) * 100
        avg_apr = statistics.mean(rates) * per_year * 100
        start = datetime.fromtimestamp(funding[0][0], timezone.utc).strftime("%Y-%m-%d")
        print(f"{'':<10} funding since {start}: mean {avg_apr:.1f}% APR, negative {neg:.0f}% of the time\n")


if __name__ == "__main__":
    main()
