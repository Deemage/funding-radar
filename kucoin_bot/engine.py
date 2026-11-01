"""Движок бэктеста: портфель с комиссиями и прогон стратегии по свечам."""


class Portfolio:
    def __init__(self, cash, fee):
        self.cash = cash
        self.base = 0.0
        self.fee = fee  # доля, 0.001 = 0.1% (базовая комиссия KuCoin spot)
        self.fees_paid = 0.0
        self.trades = []  # (t, side, qty, price)

    def buy(self, qty, price, t):
        cost = qty * price
        fee = cost * self.fee
        if qty <= 0 or cost + fee > self.cash + 1e-9:
            return False
        self.cash -= cost + fee
        self.base += qty
        self.fees_paid += fee
        self.trades.append((t, "buy", qty, price))
        return True

    def sell(self, qty, price, t):
        qty = min(qty, self.base)
        if qty <= 0:
            return False
        proceeds = qty * price
        fee = proceeds * self.fee
        self.cash += proceeds - fee
        self.base -= qty
        self.fees_paid += fee
        self.trades.append((t, "sell", qty, price))
        return True

    def equity(self, price):
        return self.cash + self.base * price


def run(strategy, candles, cash=1000.0, fee=0.001):
    pf = Portfolio(cash, fee)
    strategy.on_start(pf, candles[0])
    curve = []
    for c in candles:
        strategy.on_candle(pf, c)
        curve.append(pf.equity(c.c))
    return stats(strategy.name, pf, candles, curve, cash)


def stats(name, pf, candles, curve, cash):
    peak, max_dd = curve[0], 0.0
    for e in curve:
        peak = max(peak, e)
        max_dd = max(max_dd, (peak - e) / peak)
    final = curve[-1]
    return {
        "name": name,
        "final": final,
        "return_pct": (final / cash - 1) * 100,
        "max_dd_pct": max_dd * 100,
        "trades": len(pf.trades),
        "fees": pf.fees_paid,
        "in_coin_pct": pf.base * candles[-1].c / final * 100 if final else 0,
    }
