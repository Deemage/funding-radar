"""Strategies: Buy&Hold (benchmark), DCA, spot grid."""


def price_path(c):
    """Intra-candle price path: green candle open→low→high→close, red open→high→low→close."""
    return [c.o, c.l, c.h, c.c] if c.c >= c.o else [c.o, c.h, c.l, c.c]


class BuyHold:
    name = "Buy & Hold"

    def on_start(self, pf, c):
        pf.buy(pf.cash / (1 + pf.fee) / c.o, c.o, c.t)

    def on_candle(self, pf, c):
        pass


class DCA:
    """Buy a fixed amount every `every_hours`.
    If price drops dip_pct% below the last buy, make an extra buy × dip_mult."""

    def __init__(self, amount=20.0, every_hours=24, dip_pct=0.0, dip_mult=2.0):
        self.amount = amount
        self.every = every_hours * 3600
        self.dip = dip_pct / 100
        self.dip_mult = dip_mult
        self.name = f"DCA ${amount:g}/{every_hours}h" + (f", dip {dip_pct:g}%×{dip_mult:g}" if dip_pct else "")

    def on_start(self, pf, c):
        self.last_t = None
        self.last_price = None

    def _buy(self, pf, usd, c):
        usd = min(usd, pf.cash / (1 + pf.fee))
        if usd >= 0.1 and pf.buy(usd / c.c, c.c, c.t):  # KuCoin minimum order ~0.1 USDT
            self.last_t, self.last_price = c.t, c.c

    def on_candle(self, pf, c):
        if self.last_t is None or c.t - self.last_t >= self.every:
            self._buy(pf, self.amount, c)
        elif self.dip and c.c <= self.last_price * (1 - self.dip):
            self._buy(pf, self.amount * self.dip_mult, c)


class Grid:
    """Classic spot grid, like KuCoin Spot Grid.
    The [lower, upper] range is split into `grids` cells. Each cell either waits to buy
    at its lower level, or holds the coin and waits to sell at its upper level.
    lower/upper can be given as % of the start price (lower_pct/upper_pct).
    reset_pct: if price closes more than reset_pct% outside the range,
    the bot sells everything at market and builds a new grid around the current price (None = never reset)."""

    def __init__(self, grids=20, lower=None, upper=None, lower_pct=10, upper_pct=10, geometric=True,
                 reset_pct=None):
        self.grids = grids
        self.lower, self.upper = lower, upper
        self.lower_pct, self.upper_pct = lower_pct, upper_pct
        self.geometric = geometric
        self.reset_pct = reset_pct
        self.name = f"Grid {grids} cells"
        self.resets = 0

    def on_start(self, pf, c):
        self._build(pf, c.o, c.t, self.lower, self.upper)
        self.cycles = 0

    def _build(self, pf, p, t, lo=None, hi=None):
        lo = lo or p * (1 - self.lower_pct / 100)
        hi = hi or p * (1 + self.upper_pct / 100)
        self.lo, self.hi = lo, hi
        n = self.grids
        if self.geometric:
            r = (hi / lo) ** (1 / n)
            levels = [lo * r ** i for i in range(n + 1)]
        else:
            levels = [lo + (hi - lo) * i / n for i in range(n + 1)]
        self.step_pct = (levels[1] / levels[0] - 1) * 100
        if self.reset_pct is None:
            self.name = f"Grid {n} cells {lo:,.0f}–{hi:,.0f} (step {self.step_pct:.2f}%)"
        else:
            self.name = f"Grid {n} cells ±{self.lower_pct:g}%, reset {self.reset_pct:g}%"

        alloc = pf.cash / n / (1 + pf.fee)
        self.slots = []
        init_qty = 0.0
        for i in range(n):
            s = {"buy": levels[i], "sell": levels[i + 1], "qty": alloc / levels[i], "holding": levels[i] >= p}
            if s["holding"]:
                init_qty += s["qty"]
            self.slots.append(s)
        # fill cells above the current price with coin at market right away, so there is something to sell
        pf.buy(init_qty, p, t)

    def on_candle(self, pf, c):
        if self.reset_pct is not None:
            k = self.reset_pct / 100
            if c.c > self.hi * (1 + k) or c.c < self.lo * (1 - k):
                pf.sell(pf.base, c.c, c.t)
                self._build(pf, c.c, c.t)
                self.resets += 1
                return
        path = price_path(c)
        for a, b in zip(path, path[1:]):
            if b < a:  # price moving down: limit buys fill
                for s in self.slots:
                    if not s["holding"] and b <= s["buy"] < a and pf.buy(s["qty"], s["buy"], c.t):
                        s["holding"] = True
            elif b > a:  # price moving up: limit sells fill
                for s in self.slots:
                    if s["holding"] and a < s["sell"] <= b and pf.sell(s["qty"], s["sell"], c.t):
                        s["holding"] = False
                        self.cycles += 1
