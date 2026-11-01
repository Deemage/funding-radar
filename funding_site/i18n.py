"""Тексты сайта на русском и английском."""

LANGS = ["en", "ru"]
PREFIX = {"en": "", "ru": "ru/"}  # где лежит версия сайта; основная (en) — в корне

T = {
    "ru": {
        "site": "Фандинг Радар",
        "nav_rates": "Ставки", "nav_spreads": "Спреды", "nav_guide": "Гайд",
        "switch": "EN", "switch_title": "English version",
        "footer": "Данные: публичные API KuCoin, OKX и Gate. Обновлено",
        "footer_risk": "Не является финансовой рекомендацией. Торговля деривативами связана с высоким риском. "
                       "Ссылки на биржи могут быть партнёрскими.",
        "by_exchange": "По биржам",
        "million": "млн", "billion": "млрд", "thousand": "тыс",
        "hours": "ч", "days": "дн.",
        # главная
        "index_title": "Ставки фандинга сегодня: KuCoin, OKX, Gate — {n} монет",
        "index_desc": "Ставки фандинга бессрочных фьючерсов на 3 биржах в годовых: текущие, за 7 и 30 дней, "
                      "межбиржевые спреды и риски по каждой монете. Обновляется каждый час.",
        "index_h1": "Ставки фандинга на 3 биржах",
        "index_lead": "Фандинг всех ликвидных бессрочных USDT-фьючерсов KuCoin, OKX и Gate в пересчёте на годовые. "
                      "Положительный фандинг платят лонги шортам — на этом строится дельта-нейтральный арбитраж. "
                      "<a href=\"{guide}\">Как это работает и чем рискуете</a>.",
        "top_h2": "Самый высокий фандинг за неделю",
        "top_note": "Монеты старше {days} дней, без повышенной маржи, с парой на споте той же биржи — их можно захеджировать.",
        "card_sub": "годовых за 7 дней на {ex}",
        "btc_note": "Для сравнения BTC: {apr} годовых за 7 дней на {ex}.",
        "spreads_h2": "Межбиржевые спреды",
        "spreads_lead": "Шорт там, где фандинг выше, лонг там, где ниже: цена гасится, вы получаете разницу ставок. "
                        "Нужен капитал на двух биржах, а шорт может ликвидировать при резком росте.",
        "col_coin": "Монета", "col_short": "Шорт на", "col_long": "Лонг на",
        "col_spread7": "Спред 7 дн.", "col_spread_now": "Спред сейчас",
        "all_h2": "Все монеты",
        "f_spot": "только с хеджем на споте", "f_risky": "скрыть новые и рискованные",
        "col_best": "Лучшая (7 дн.)", "col_turnover": "Оборот 24ч", "col_risk": "Риски",
        "chip_new": "новая, {d} дн.", "chip_new_t": "Торгуется меньше {days} дней",
        "chip_mm": "высокая маржа", "chip_mm_t": "Биржа требует повышенную маржу — считает монету рискованной",
        "chip_nospot": "нет спота", "chip_nospot_t": "Ни на одной бирже нет пары на споте — захеджировать нельзя",
        "faq_h2": "Частые вопросы",
        "where_h2": "Где торговать",
        # биржа
        "ex_title": "Ставки фандинга {ex} сегодня — {n} фьючерсов в годовых",
        "ex_desc": "Фандинг бессрочных фьючерсов {ex}: текущий и средний за 7 и 30 дней в годовых, доля "
                   "отрицательных выплат, оборот. Обновляется каждый час.",
        "ex_h1": "Фандинг на {ex}",
        "ex_lead": "{n} бессрочных USDT-фьючерсов {ex} с оборотом от ${min} в сутки. Сравнить с другими биржами — "
                   "на <a href=\"{home}\">главной</a>.",
        "col_now": "Сейчас", "col_7d": "7 дней", "col_30d": "30 дней", "col_neg": "Отриц.",
        "col_neg_t": "Доля выплат с отрицательной ставкой за 30 дней", "col_interval": "Интервал",
        "col_spot": "Спот", "yes": "есть", "no": "нет",
        "open_ex": "Открыть {ex}",
        # монета
        "coin_title": "Фандинг {b} сегодня: {apr} годовых — KuCoin, OKX, Gate",
        "coin_desc": "Ставка фандинга {b} на 3 биржах: лучшая {apr} годовых за 7 дней на {ex}. "
                     "Сравнение бирж, график за 30 дней, спред и калькулятор арбитража.",
        "coin_h1": "Фандинг {b}",
        "coin_cards_best": "Лучший хедж (7 дн.)", "coin_cards_spread": "Спред бирж (7 дн.)",
        "coin_cards_turnover": "Оборот фьючерсов 24ч", "coin_cards_neg": "Отриц. выплат (30 дн.)",
        "coin_table_h2": "Сравнение бирж",
        "col_ex": "Биржа", "col_trade": "", "trade": "Торговать",
        "chart_h2": "Фандинг по дням, % годовых",
        "calc_h2": "Сколько дал бы арбитраж «спот + шорт»",
        "calc_note": "Оценка по средней ставке за 30 дней на выбранной бирже. Прошлое не гарантирует будущего.",
        "calc_ex": "Биржа", "calc_cap": "Капитал, $", "calc_lev": "Плечо шорта", "calc_month": "За месяц",
        "calc_fees": "Комиссии вход+выход", "lev1": "1x — надёжнее",
        "no_hedge": "Ни на одной из бирж нет пары {b} на споте — классический арбитраж «спот + шорт» невозможен.",
        "risk_note": "<b>Повышенный риск.</b> У молодых и малоликвидных монет бывают выстрелы цены на десятки процентов "
                     "за час. Шорт может ликвидировать даже без плеча — это перекроет фандинг за месяцы.",
        "back": "Все монеты", "guide_link": "Как работает арбитраж фандинга",
        # автотекст монеты
        "txt_markets": "{b} торгуется фьючерсами на {n} из 3 отслеживаемых бирж: {list}.",
        "txt_best": " Самый высокий фандинг за неделю с возможностью хеджа на споте — на {ex}: {apr} годовых.",
        "txt_neg": " За 30 дней на {ex} {neg}% выплат были отрицательными — в эти периоды шорт платит сам.",
        "txt_spread": " Разница ставок между биржами за неделю — {s} годовых (шорт на {hi}, лонг на {lo}).",
        "txt_young": " Монета торгуется всего {d} дней — история короткая, а риск резких движений высокий.",
    },
    "en": {
        "site": "Funding Radar",
        "nav_rates": "Rates", "nav_spreads": "Spreads", "nav_guide": "Guide",
        "switch": "RU", "switch_title": "Русская версия",
        "footer": "Data: public APIs of KuCoin, OKX and Gate. Updated",
        "footer_risk": "Not financial advice. Derivatives trading involves high risk. Exchange links may be affiliate links.",
        "by_exchange": "By exchange",
        "million": "M", "billion": "B", "thousand": "K",
        "hours": "h", "days": "d",
        "index_title": "Funding rates today: KuCoin, OKX, Gate — {n} coins",
        "index_desc": "Perpetual futures funding rates on 3 exchanges, annualized: current, 7-day and 30-day averages, "
                      "cross-exchange spreads and risk flags. Updated hourly.",
        "index_h1": "Funding rates on 3 exchanges",
        "index_lead": "Funding rates for every liquid USDT perpetual on KuCoin, OKX and Gate, annualized. "
                      "Positive funding means longs pay shorts — the basis of delta-neutral funding arbitrage. "
                      "<a href=\"{guide}\">How it works and what can go wrong</a>.",
        "top_h2": "Highest funding this week",
        "top_note": "Coins older than {days} days, normal margin, with a spot pair on the same exchange — so they can be hedged.",
        "card_sub": "APR over 7 days on {ex}",
        "btc_note": "For reference, BTC: {apr} APR over 7 days on {ex}.",
        "spreads_h2": "Cross-exchange spreads",
        "spreads_lead": "Short where funding is higher, long where it is lower: price moves cancel out and you collect the difference. "
                        "Requires capital on two exchanges, and the short can get liquidated on a sharp pump.",
        "col_coin": "Coin", "col_short": "Short on", "col_long": "Long on",
        "col_spread7": "7d spread", "col_spread_now": "Spread now",
        "all_h2": "All coins",
        "f_spot": "only with spot hedge", "f_risky": "hide new and risky",
        "col_best": "Best (7d)", "col_turnover": "24h volume", "col_risk": "Risks",
        "chip_new": "new, {d}d", "chip_new_t": "Trading for less than {days} days",
        "chip_mm": "high margin", "chip_mm_t": "The exchange requires higher margin — it considers the coin risky",
        "chip_nospot": "no spot", "chip_nospot_t": "No spot pair on any exchange — cannot be hedged",
        "faq_h2": "FAQ",
        "where_h2": "Where to trade",
        "ex_title": "{ex} funding rates today — {n} perpetuals, annualized",
        "ex_desc": "{ex} perpetual futures funding: current, 7-day and 30-day average APR, share of negative payments, volume. "
                   "Updated hourly.",
        "ex_h1": "{ex} funding rates",
        "ex_lead": "{n} USDT perpetuals on {ex} with daily volume above ${min}. Compare with other exchanges "
                   "on the <a href=\"{home}\">main page</a>.",
        "col_now": "Now", "col_7d": "7 days", "col_30d": "30 days", "col_neg": "Neg.",
        "col_neg_t": "Share of negative payments over 30 days", "col_interval": "Interval",
        "col_spot": "Spot", "yes": "yes", "no": "no",
        "open_ex": "Open {ex}",
        "coin_title": "{b} funding rate today: {apr} APR — KuCoin, OKX, Gate",
        "coin_desc": "{b} funding rate on 3 exchanges: best {apr} APR over 7 days on {ex}. "
                     "Exchange comparison, 30-day chart, spread and arbitrage calculator.",
        "coin_h1": "{b} funding rate",
        "coin_cards_best": "Best hedgeable (7d)", "coin_cards_spread": "Exchange spread (7d)",
        "coin_cards_turnover": "Futures volume 24h", "coin_cards_neg": "Negative payments (30d)",
        "coin_table_h2": "Exchange comparison",
        "col_ex": "Exchange", "col_trade": "", "trade": "Trade",
        "chart_h2": "Daily funding, % APR",
        "calc_h2": "What spot + short arbitrage would have earned",
        "calc_note": "Estimate based on the 30-day average rate on the selected exchange. Past results do not guarantee future returns.",
        "calc_ex": "Exchange", "calc_cap": "Capital, $", "calc_lev": "Short leverage", "calc_month": "Per month",
        "calc_fees": "Entry + exit fees", "lev1": "1x — safer",
        "no_hedge": "None of the exchanges lists {b} on spot — classic spot + short arbitrage is not possible.",
        "risk_note": "<b>Elevated risk.</b> Young and illiquid coins can pump tens of percent within an hour. "
                     "The short can be liquidated even without leverage — wiping out months of funding.",
        "back": "All coins", "guide_link": "How funding arbitrage works",
        "txt_markets": "{b} perpetuals trade on {n} of the 3 tracked exchanges: {list}.",
        "txt_best": " The highest 7-day funding with a spot hedge available is on {ex}: {apr} APR.",
        "txt_neg": " Over 30 days, {neg}% of payments on {ex} were negative — during those periods the short pays.",
        "txt_spread": " The 7-day rate difference between exchanges is {s} APR (short on {hi}, long on {lo}).",
        "txt_young": " The coin has only been trading for {d} days — short history and high risk of sharp moves.",
    },
}

FAQ = {
    "ru": [
        ("Что такое ставка фандинга?",
         "Периодический платёж между лонгами и шортами бессрочного фьючерса. Он удерживает цену фьючерса рядом со спотом: "
         "если фьючерс дороже, лонги платят шортам, если дешевле — наоборот. Биржи списывают его каждые 1–8 часов."),
        ("Как пересчитывается в годовые?",
         "Ставка за один интервал × количество выплат в году. Например, 0.01% каждые 8 часов = 0.01% × 3 × 365 ≈ 11% годовых."),
        ("Как заработать на фандинге?",
         "Купить монету на споте и открыть шорт фьючерса на ту же сумму. Движение цены гасится, остаётся фандинг. "
         "Подробности и реальная доходность — в гайде."),
        ("Почему у одной монеты разный фандинг на разных биржах?",
         "У каждой биржи свои трейдеры, свой перекос лонгов и шортов и своя формула. Разница — это межбиржевой спред, "
         "на нём тоже можно зарабатывать: шорт там, где ставка выше, лонг там, где ниже."),
        ("Насколько это безопасно?",
         "Цена гасится, но риски остаются: ликвидация шорта при резком росте, отрицательный фандинг, комиссии и риск самой биржи. "
         "Высокие ставки почти всегда означают высокий риск."),
        ("Как часто обновляются данные?",
         "Каждый час, напрямую из публичных API бирж."),
    ],
    "en": [
        ("What is a funding rate?",
         "A periodic payment between longs and shorts of a perpetual future. It keeps the futures price close to spot: "
         "when futures trade above spot, longs pay shorts, and vice versa. Exchanges settle it every 1–8 hours."),
        ("How is it annualized?",
         "Rate per interval × number of payments per year. For example, 0.01% every 8 hours = 0.01% × 3 × 365 ≈ 11% APR."),
        ("How do you earn from funding?",
         "Buy the coin on spot and open a short perpetual for the same amount. Price moves cancel out and you keep the funding. "
         "Details and real-world returns are in the guide."),
        ("Why does the same coin have different funding on different exchanges?",
         "Each exchange has its own traders, its own long/short imbalance and its own formula. The difference is a "
         "cross-exchange spread you can also trade: short where the rate is higher, long where it is lower."),
        ("Is it safe?",
         "Price risk is hedged, but other risks remain: liquidation of the short on a sharp pump, negative funding, fees and "
         "exchange risk. High rates almost always mean high risk."),
        ("How often is the data updated?",
         "Every hour, straight from the exchanges' public APIs."),
    ],
}

GUIDE = {
    "ru": {
        "title": "Арбитраж фандинга: как работает, сколько приносит и чем рискуете",
        "desc": "Как заработать на ставках фандинга: спот + шорт и межбиржевой спред. Реальная доходность на 2 годах "
                "истории, риски ликвидации и почему высокий фандинг — не бесплатные деньги.",
        "body": """
<h1>Арбитраж фандинга: как работает и сколько реально приносит</h1>
<p class="lead">Разбор на реальной часовой истории KuCoin за 2024–2026 годы: где доход, где риски и почему высокий фандинг —
не бесплатные деньги.</p>
<h2>Что такое фандинг</h2>
<p>У бессрочных фьючерсов нет даты экспирации. Чтобы цена фьючерса не отрывалась от спота, биржа каждые 1–8 часов
списывает платёж с одной стороны и отдаёт другой. Когда лонгов больше и фьючерс дороже спота, ставка положительная —
<b>лонги платят шортам</b>. Когда наоборот — шорты платят лонгам.</p>
<h2>Стратегия 1: спот + шорт на одной бирже</h2>
<ol><li>Покупаете монету на споте на сумму X.</li>
<li>Открываете шорт бессрочного фьючерса на ту же сумму X.</li>
<li>Движение цены взаимно гасится.</li>
<li>Остаётся фандинг, который шорт получает каждые несколько часов.</li></ol>
<p>Плюс — всё на одной бирже, позиция простая. Минус — часть капитала уходит на маржу шорта, поэтому доходность
на весь капитал ниже ставки фандинга.</p>
<h2>Стратегия 2: межбиржевой спред</h2>
<p>Шорт фьючерса на бирже, где фандинг выше, и лонг фьючерса той же монеты на бирже, где ниже. Цена гасится,
вы получаете разницу ставок. Нужен капитал на двух биржах, и обе ноги — фьючерсы, то есть обе могут ликвидировать.</p>
<h2>Сколько это приносило на истории</h2>
<p>Тест на часовых данных KuCoin с комиссиями (спот 0.1%, фьючерс 0.06%) и плечом шорта 2x:</p>
<ul><li><b>BTC, ETH, SOL за 2 года:</b> 3–5% годовых на капитал, просадка около 1%, ни одной ликвидации.</li>
<li><b>Ротация по альтам с самым высоким фандингом:</b> около 6% годовых в обычные месяцы, но один выстрел цены
на одной монете (+196% за час) за месяц съел прибыль за год.</li>
<li><b>«Входить только при высоком фандинге»</b> оказалось хуже, чем держать позицию всегда: комиссии за входы и
выходы съедают выгоду.</li></ul>
<h2>Риски</h2>
<ul><li><b>Ликвидация шорта.</b> При резком росте убыток шорта растёт быстрее, чем вы успеваете довнести маржу.
Чем выше плечо, тем меньший рост нужен.</li>
<li><b>Отрицательный фандинг.</b> 20–40% времени даже у BTC ставка отрицательная, и шорт платит сам.</li>
<li><b>Высокий фандинг — плата за риск.</b> Ставки 50–100% годовых бывают у монет, которые прямо сейчас разгоняют.</li>
<li><b>Минимальный размер позиции.</b> У BTC на некоторых биржах минимальный контракт около $80.</li>
<li><b>Риск биржи.</b> Все средства лежат на бирже.</li></ul>
<div class="note">Это не финансовая рекомендация. Цифры — результат исторического теста и не гарантируют доходности в будущем.</div>
""",
    },
    "en": {
        "title": "Funding rate arbitrage: how it works, real returns and risks",
        "desc": "How to earn from funding rates: spot + short and cross-exchange spreads. Real returns on 2 years of data, "
                "liquidation risk and why high funding is not free money.",
        "body": """
<h1>Funding rate arbitrage: how it works and what it really returns</h1>
<p class="lead">A breakdown based on two years of hourly KuCoin data (2024–2026): where the returns are, where the risks are,
and why high funding is not free money.</p>
<h2>What funding is</h2>
<p>Perpetual futures never expire. To keep the futures price close to spot, the exchange charges one side and pays the other
every 1–8 hours. When longs dominate and futures trade above spot, the rate is positive — <b>longs pay shorts</b>.
Otherwise shorts pay longs.</p>
<h2>Strategy 1: spot + short on one exchange</h2>
<ol><li>Buy the coin on spot for amount X.</li>
<li>Open a perpetual short for the same amount X.</li>
<li>Price moves cancel each other out.</li>
<li>You keep the funding paid to the short every few hours.</li></ol>
<p>Upside: one exchange, simple position. Downside: part of the capital sits as short margin, so the return on total capital
is lower than the funding rate.</p>
<h2>Strategy 2: cross-exchange spread</h2>
<p>Short the perpetual where funding is higher and long the same coin's perpetual where it is lower. Price cancels out and
you collect the rate difference. You need capital on two exchanges, and both legs are futures, so both can be liquidated.</p>
<h2>Historical returns</h2>
<p>Backtest on hourly KuCoin data with fees (spot 0.1%, futures 0.06%) and 2x short leverage:</p>
<ul><li><b>BTC, ETH, SOL over 2 years:</b> 3–5% APR on capital, ~1% drawdown, zero liquidations.</li>
<li><b>Rotating into the highest-funding altcoins:</b> about 6% APR in normal months — but a single pump on one coin
(+196% within an hour) wiped out a year of profit in one month.</li>
<li><b>“Only enter when funding is high”</b> did worse than staying in the position: entry and exit fees ate the benefit.</li></ul>
<h2>Risks</h2>
<ul><li><b>Short liquidation.</b> On a sharp pump the short's loss grows faster than you can add margin. Higher leverage
means a smaller move is enough.</li>
<li><b>Negative funding.</b> Even BTC spends 20–40% of the time with a negative rate, and then the short pays.</li>
<li><b>High funding is a risk premium.</b> 50–100% APR rates show up on coins that are being pumped right now.</li>
<li><b>Minimum position size.</b> On some exchanges the minimum BTC contract is about $80.</li>
<li><b>Exchange risk.</b> All funds sit on the exchange.</li></ul>
<div class="note">Not financial advice. Figures come from a historical backtest and do not guarantee future returns.</div>
""",
    },
}
