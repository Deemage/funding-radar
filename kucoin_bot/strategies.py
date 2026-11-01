"""Стратегии: Buy&Hold (эталон), DCA, спотовый грид."""


def price_path(c):
    """Внутрисвечной путь цены: зелёная свеча open→low→high→close, красная open→high→low→close."""
    return [c.o, c.l, c.h, c.c] if c.c >= c.o else [c.o, c.h, c.l, c.c]


class BuyHold:
    name = "Buy & Hold"

    def on_start(self, pf, c):
        pf.buy(pf.cash / (1 + pf.fee) / c.o, c.o, c.t)

    def on_candle(self, pf, c):
        pass


class DCA:
    """Покупка на фиксированную сумму раз в `every_hours`.
    Если цена упала на dip_pct% от последней покупки, внеочередная покупка × dip_mult."""

    def __init__(self, amount=20.0, every_hours=24, dip_pct=0.0, dip_mult=2.0):
        self.amount = amount
        self.every = every_hours * 3600
        self.dip = dip_pct / 100
        self.dip_mult = dip_mult
        self.name = f"DCA ${amount:g}/{every_hours}ч" + (f", просадка {dip_pct:g}%×{dip_mult:g}" if dip_pct else "")

    def on_start(self, pf, c):
        self.last_t = None
        self.last_price = None

    def _buy(self, pf, usd, c):
        usd = min(usd, pf.cash / (1 + pf.fee))
        if usd >= 0.1 and pf.buy(usd / c.c, c.c, c.t):  # минимальный ордер KuCoin ~0.1 USDT
            self.last_t, self.last_price = c.t, c.c

    def on_candle(self, pf, c):
        if self.last_t is None or c.t - self.last_t >= self.every:
            self._buy(pf, self.amount, c)
        elif self.dip and c.c <= self.last_price * (1 - self.dip):
            self._buy(pf, self.amount * self.dip_mult, c)


class Grid:
    """Классический спотовый грид, как у KuCoin Spot Grid.
    Диапазон [lower, upper] делится на `grids` ячеек. В каждой ячейке либо ждём покупку
    на нижнем уровне, либо держим монету и ждём продажу на верхнем.
    lower/upper можно задать в % от стартовой цены (lower_pct/upper_pct).
    reset_pct: если цена закрылась дальше чем на reset_pct% за границей диапазона,
    бот продаёт всё по рынку и строит новый грид вокруг текущей цены (None = не перестраивать)."""

    def __init__(self, grids=20, lower=None, upper=None, lower_pct=10, upper_pct=10, geometric=True,
                 reset_pct=None):
        self.grids = grids
        self.lower, self.upper = lower, upper
        self.lower_pct, self.upper_pct = lower_pct, upper_pct
        self.geometric = geometric
        self.reset_pct = reset_pct
        self.name = f"Grid {grids} ячеек"
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
            self.name = f"Grid {n} яч. {lo:,.0f}–{hi:,.0f} (шаг {self.step_pct:.2f}%)"
        else:
            self.name = f"Grid {n} яч. ±{self.lower_pct:g}%, перестройка {self.reset_pct:g}%"

        alloc = pf.cash / n / (1 + pf.fee)
        self.slots = []
        init_qty = 0.0
        for i in range(n):
            s = {"buy": levels[i], "sell": levels[i + 1], "qty": alloc / levels[i], "holding": levels[i] >= p}
            if s["holding"]:
                init_qty += s["qty"]
            self.slots.append(s)
        # ячейки выше текущей цены сразу заполняем монетой по рынку, чтобы было что продавать
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
            if b < a:  # цена идёт вниз, срабатывают лимитные покупки
                for s in self.slots:
                    if not s["holding"] and b <= s["buy"] < a and pf.buy(s["qty"], s["buy"], c.t):
                        s["holding"] = True
            elif b > a:  # цена идёт вверх, срабатывают лимитные продажи
                for s in self.slots:
                    if s["holding"] and a < s["sell"] <= b and pf.sell(s["qty"], s["sell"], c.t):
                        s["holding"] = False
                        self.cycles += 1
