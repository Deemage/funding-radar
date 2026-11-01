"""Builds the static site (en + ru) into public/.

  python build.py            # fetch fresh data from all exchanges and build
  python build.py --cached   # build from the previous run's data.json (no network)
"""
import argparse
import html
import json
import os
import shutil
import sys
from collections import defaultdict
from datetime import datetime, timezone

import config
from fetch import collect, enrich, summarize
from i18n import FAQ, GUIDE, LANGS, PREFIX, T

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "public")
DATA = os.path.join(ROOT, "data.json")
STATIC = os.path.join(ROOT, "static")
FEES_ROUND_TRIP = 0.0032  # spot ~0.1% + futures ~0.06%, entry and exit

EXCHANGES = ["kucoin", "okx", "gate"]
EX_NAME = {"kucoin": "KuCoin", "okx": "OKX", "gate": "Gate"}
EX_HOME = {
    "kucoin": "https://www.kucoin.com/futures",
    "okx": "https://www.okx.com/trade-swap/btc-usdt-swap",
    "gate": "https://www.gate.io/futures/USDT/BTC_USDT",
}

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Ccircle cx='16' cy='16' r='14' fill='%230b7a5c'/%3E%3Ccircle cx='16' cy='16' r='8' fill='none' "
           "stroke='white' stroke-width='2.5'/%3E%3Cpath d='M16 16 L26 8' stroke='white' stroke-width='2.5' "
           "stroke-linecap='round'/%3E%3C/svg%3E")

CSS = """
:root{--bg:#f6f6f3;--card:#fff;--text:#1c1c1a;--muted:#6a6a64;--line:#e3e2dc;--accent:#0b7a5c;--accent-ink:#fff;
--pos:#0b7a5c;--neg:#c2410c;--warn:#9a6a00;--chip:#efeee8;
--c-kucoin:#0b7a5c;--c-okx:#d97706;--c-gate:#2563eb}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#111110;--card:#1a1a18;--text:#ecebe5;
--muted:#9a9991;--line:#2b2b28;--accent:#34c597;--accent-ink:#0d1a14;--pos:#34c597;--neg:#f97850;--warn:#e0b341;
--chip:#252522;--c-kucoin:#34c597;--c-okx:#f5a524;--c-gate:#60a5fa}}
:root[data-theme="dark"]{--bg:#111110;--card:#1a1a18;--text:#ecebe5;--muted:#9a9991;--line:#2b2b28;--accent:#34c597;
--accent-ink:#0d1a14;--pos:#34c597;--neg:#f97850;--warn:#e0b341;--chip:#252522;--c-kucoin:#34c597;--c-okx:#f5a524;
--c-gate:#60a5fa}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.6 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--accent)}
.wrap{max-width:1120px;margin:0 auto;padding:0 16px}
header{border-bottom:1px solid var(--line);background:var(--card);position:sticky;top:0;z-index:5}
header .wrap{display:flex;gap:18px;align-items:center;min-height:56px;flex-wrap:wrap}
.logo{display:flex;gap:8px;align-items:center;font-weight:700;text-decoration:none;color:var(--text)}
.logo img{width:22px;height:22px}
header nav{display:flex;gap:16px;font-size:14px;flex:1}
header nav a{color:var(--muted);text-decoration:none}
header nav a:hover{color:var(--text)}
.lang{font-size:13px;font-weight:600;text-decoration:none;border:1px solid var(--line);border-radius:6px;padding:2px 8px;color:var(--muted)}
h1{font-size:30px;line-height:1.2;margin:32px 0 10px;letter-spacing:-.01em}
h2{font-size:20px;margin:36px 0 10px}
.lead{color:var(--muted);max-width:760px;margin:0 0 18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.card .k{color:var(--muted);font-size:13px}
.card .v{font-size:26px;font-weight:650;font-variant-numeric:tabular-nums;line-height:1.3}
a.card{text-decoration:none;color:inherit;transition:border-color .15s}
a.card:hover{border-color:var(--accent)}
.tablebox{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:12px}
table{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums;font-size:14px}
th,td{padding:9px 12px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
th{font-weight:600;color:var(--muted);cursor:pointer;user-select:none;background:var(--card)}
th[aria-sort]::after{content:" ↓"}th[aria-sort="ascending"]::after{content:" ↑"}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover td{background:var(--bg)}
td a{font-weight:600;text-decoration:none}
.pos{color:var(--pos)}.neg{color:var(--neg)}.muted{color:var(--muted)}
.ex{font-size:12px;color:var(--muted);margin-left:4px}
.chip{display:inline-block;font-size:12px;padding:1px 8px;border-radius:99px;background:var(--chip);color:var(--muted);margin-left:4px}
.chip.warn{color:var(--warn)}
.filters{display:flex;gap:18px;flex-wrap:wrap;margin:6px 0 12px;font-size:14px;color:var(--muted)}
.cta{display:inline-block;background:var(--accent);color:var(--accent-ink);padding:10px 18px;border-radius:8px;
text-decoration:none;font-weight:600}
.btn{display:inline-block;border:1px solid var(--line);padding:3px 10px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:600}
.note{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--warn);border-radius:8px;
padding:12px 14px;margin:16px 0;font-size:14px}
.chart{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.chart svg{width:100%;height:auto;display:block}
.legend{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-top:8px}
.legend i{display:inline-block;width:12px;height:3px;border-radius:2px;vertical-align:middle;margin-right:6px}
.calc{display:flex;gap:14px;flex-wrap:wrap;align-items:end}
.calc label{display:flex;flex-direction:column;font-size:13px;color:var(--muted);gap:4px}
.calc input,.calc select{font:inherit;padding:7px 9px;border:1px solid var(--line);border-radius:6px;
background:var(--bg);color:var(--text);min-width:130px}
.calc b{font-size:22px;color:var(--text)}
.prose{max-width:760px}.prose li{margin:4px 0}
.exlinks{display:flex;gap:10px;flex-wrap:wrap}
details{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:8px 0;max-width:820px}
summary{cursor:pointer;font-weight:600}
details p{margin:8px 0 2px;color:var(--muted)}
footer{margin:56px 0 0;padding:22px 0 30px;border-top:1px solid var(--line);color:var(--muted);font-size:13px}
footer .exlinks{margin-bottom:10px}
@media (max-width:640px){h1{font-size:24px}th,td{padding:8px}header nav{order:3;flex-basis:100%;padding-bottom:8px}}
"""

JS = """
document.querySelectorAll('table[data-sortable]').forEach(t=>{
  const ths=[...t.tHead.rows[0].cells];
  ths.forEach((th,i)=>th.addEventListener('click',()=>{
    const asc=th.getAttribute('aria-sort')==='descending';
    ths.forEach(h=>h.removeAttribute('aria-sort'));
    th.setAttribute('aria-sort',asc?'ascending':'descending');
    const rows=[...t.tBodies[0].rows];
    const val=r=>{const v=r.cells[i].dataset.v;return v===undefined?r.cells[i].textContent.trim():parseFloat(v)};
    rows.sort((a,b)=>{const x=val(a),y=val(b);const c=typeof x==='number'?x-y:String(x).localeCompare(y);return asc?c:-c});
    rows.forEach(r=>t.tBodies[0].appendChild(r));
  }));
});
const f=document.getElementById('filters');
if(f){const apply=()=>{document.querySelectorAll('#all tbody tr').forEach(r=>{
  r.hidden=(f.spot.checked&&r.dataset.spot!=='1')||(f.risky.checked&&r.dataset.risky==='1')})};
  f.addEventListener('change',apply);apply();}
document.querySelectorAll('[data-ts]').forEach(e=>{
  e.textContent=new Date(+e.dataset.ts*1000).toLocaleString(document.documentElement.lang,{dateStyle:'short',timeStyle:'short'})});
"""


def esc(s):
    return html.escape(str(s))


def ref(exchange, url):
    q = config.REFERRAL_QUERY.get(exchange, "")
    return f"{url}{'&' if '?' in url else '?'}{q}" if q else url


def signup(exchange):
    """Link for the main exchange button: the ready-made referral link, else the futures page with the referral param."""
    return config.REFERRAL_LINK.get(exchange) or ref(exchange, EX_HOME[exchange])


def exchange_buttons(t):
    """'Where to trade' buttons, only for exchanges that have a referral link or param."""
    partners = [e for e in EXCHANGES if config.REFERRAL_LINK.get(e) or config.REFERRAL_QUERY.get(e)]
    return "".join(f'<a class="cta" href="{esc(signup(e))}" rel="sponsored noopener" target="_blank">'
                   f'{t["open_ex"].format(ex=EX_NAME[e])}</a>' for e in partners)


def pct(v, digits=1):
    if v is None:
        return '<span class="muted">—</span>'
    cls = "pos" if v > 0 else "neg" if v < 0 else "muted"
    return f'<span class="{cls}">{v:+.{digits}f}%</span>'


def money(v, t):
    if v >= 1e9:
        return f"${v / 1e9:.1f} {t['billion']}"
    if v >= 1e6:
        return f"${v / 1e6:.1f} {t['million']}"
    return f"${v / 1e3:.0f} {t['thousand']}"


def risky(c):
    return (c["age_days"] is not None and c["age_days"] < config.YOUNG_DAYS) or c["high_mm"]


def chips(c, t):
    out = []
    if c["age_days"] is not None and c["age_days"] < config.YOUNG_DAYS:
        out.append(f'<span class="chip warn" title="{esc(t["chip_new_t"].format(days=config.YOUNG_DAYS))}">'
                   f'{esc(t["chip_new"].format(d=c["age_days"]))}</span>')
    if c["high_mm"]:
        out.append(f'<span class="chip warn" title="{esc(t["chip_mm_t"])}">{esc(t["chip_mm"])}</span>')
    if not c["best"]:
        out.append(f'<span class="chip" title="{esc(t["chip_nospot_t"])}">{esc(t["chip_nospot"])}</span>')
    return "".join(out)


def faq_block(items):
    """FAQ: HTML for the page and FAQPage JSON-LD for <head>."""
    body = "".join(f"<details><summary>{esc(q)}</summary><p>{esc(a)}</p></details>" for q, a in items)
    ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]},
        ensure_ascii=False)
    return body, f'<script type="application/ld+json">{ld}</script>'


def has_cx(c):
    """A coin-on-exchange page exists only if the coin trades on 2+ exchanges, otherwise it duplicates the coin page."""
    return len(c["markets"]) >= 2


def cx_path(c, ex):
    return f"coin/{c['base']}/{ex}.html"


def apr_list(c, key):
    """'OKX +12.3%, Gate +8.1%': the coin's exchanges sorted by the metric, descending."""
    ms = sorted((m for m in c["markets"].values() if m[key] is not None), key=lambda m: -m[key])
    return ", ".join(f"{EX_NAME[m['exchange']]} {m[key]:+.1f}%" for m in ms)


class Page:
    """One page in one language version: knows its own path and builds relative links."""

    def __init__(self, lang, path):
        self.lang, self.path = lang, PREFIX[lang] + path
        self.root = "../" * self.path.count("/")
        self.t = T[lang]

    def link(self, path, lang=None):
        return self.root + PREFIX[lang or self.lang] + path

    def render(self, title, desc, body, updated, head=""):
        t, other = self.t, "en" if self.lang == "ru" else "ru"
        bare = self.path[len(PREFIX[self.lang]):]
        alternates = "".join(f'<link rel="alternate" hreflang="{l}" href="{config.SITE_URL}/{PREFIX[l]}{bare}">'
                             for l in LANGS)
        ts = datetime.fromtimestamp(updated, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        exlinks = "".join(f'<a href="{self.link(f"exchange/{e}.html")}">{EX_NAME[e]}</a>' for e in EXCHANGES)
        return f"""<!doctype html>
<html lang="{self.lang}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{config.SITE_URL}/{self.path}">{alternates}
<link rel="alternate" hreflang="x-default" href="{config.SITE_URL}/{bare}">
<link rel="icon" href="{FAVICON}">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{config.SITE_URL}/{self.path}">
<meta property="og:site_name" content="{esc(t['site'])}">
<style>{CSS}</style>{head}
</head><body>
<header><div class="wrap">
<a class="logo" href="{self.link('index.html')}"><img src="{FAVICON}" alt="">{esc(t['site'])}</a>
<nav><a href="{self.link('index.html')}">{t['nav_rates']}</a><a href="{self.link('index.html')}#spreads">{t['nav_spreads']}</a>
<a href="{self.link('guide.html')}">{t['nav_guide']}</a></nav>
<a class="lang" href="{self.link(bare, other)}" hreflang="{other}" title="{esc(t['switch_title'])}">{t['switch']}</a>
</div></header>
<main class="wrap">{body}</main>
<footer class="wrap"><div class="exlinks">{t['by_exchange']}: {exlinks}</div>
{t['footer']} <span data-ts="{updated}">{ts}</span>. {t['footer_risk']}</footer>
<script>{JS}</script>
</body></html>"""


def index_page(lang, coins, updated):
    p = Page(lang, "index.html")
    t = p.t
    coin = lambda c: p.link(f"coin/{c['base']}.html")

    solid = [c for c in coins if c["best"] and not risky(c)]
    cards = "".join(
        f'<a class="card" href="{coin(c)}"><div class="k">{esc(c["base"])}</div><div class="v">{pct(c["best_apr_7d"])}</div>'
        f'<div class="k">{t["card_sub"].format(ex=EX_NAME[c["best"]])}</div></a>'
        for c in sorted(solid, key=lambda c: -c["best_apr_7d"])[:4])
    btc = next((c for c in coins if c["base"] == "BTC" and c["best"]), None)
    btc_note = f'<p class="muted">{t["btc_note"].format(apr=pct(btc["best_apr_7d"]), ex=EX_NAME[btc["best"]])}</p>' if btc else ""

    spread_rows = []
    for c in sorted((c for c in coins if c["spread"] and not risky(c)), key=lambda c: -c["spread"]["apr_7d"])[:10]:
        s, m = c["spread"], c["markets"]
        spread_rows.append(
            f'<tr><td><a href="{coin(c)}">{esc(c["base"])}</a></td>'
            f'<td data-v="{m[s["short"]]["apr_7d"]:.3f}">{EX_NAME[s["short"]]} {pct(m[s["short"]]["apr_7d"])}</td>'
            f'<td data-v="{m[s["long"]]["apr_7d"]:.3f}">{EX_NAME[s["long"]]} {pct(m[s["long"]]["apr_7d"])}</td>'
            f'<td data-v="{s["apr_7d"]:.3f}"><b>{pct(s["apr_7d"])}</b></td><td data-v="{s["now"]:.3f}">{pct(s["now"])}</td></tr>')

    rows = []
    for c in sorted(coins, key=lambda c: -(c["best_apr_7d"] if c["best_apr_7d"] is not None else -1e9)):
        best = (f'{pct(c["best_apr_7d"])}<span class="ex">{EX_NAME[c["best"]]}</span>' if c["best"]
                else '<span class="muted">—</span>')
        cells = "".join(
            f'<td data-v="{c["markets"][e]["apr_7d"]:.3f}">{pct(c["markets"][e]["apr_7d"])}</td>' if e in c["markets"]
            else '<td data-v="-99999"><span class="muted">—</span></td>' for e in EXCHANGES)
        rows.append(
            f'<tr data-spot="{int(bool(c["best"]))}" data-risky="{int(risky(c))}">'
            f'<td><a href="{coin(c)}">{esc(c["base"])}</a>{chips(c, t)}</td>'
            f'<td data-v="{c["best_apr_7d"] if c["best_apr_7d"] is not None else -99999:.3f}">{best}</td>{cells}'
            f'<td data-v="{c["turnover"]:.0f}">{money(c["turnover"], t)}</td></tr>')

    faq_html, faq_head = faq_block(FAQ[lang])

    body = f"""
<h1>{t['index_h1']}</h1>
<p class="lead">{t['index_lead'].format(guide=p.link('guide.html'))}</p>
<h2>{t['top_h2']}</h2>
<p class="muted" style="margin:0">{t['top_note'].format(days=config.YOUNG_DAYS)}</p>
<div class="cards">{cards}</div>
{btc_note}
<h2 id="spreads">{t['spreads_h2']}</h2>
<p class="lead">{t['spreads_lead']}</p>
<div class="tablebox"><table data-sortable><thead><tr><th>{t['col_coin']}</th><th>{t['col_short']}</th>
<th>{t['col_long']}</th><th aria-sort="descending">{t['col_spread7']}</th><th>{t['col_spread_now']}</th></tr></thead>
<tbody>{''.join(spread_rows)}</tbody></table></div>
<h2>{t['all_h2']}</h2>
<form class="filters" id="filters">
<label><input type="checkbox" name="spot" checked> {t['f_spot']}</label>
<label><input type="checkbox" name="risky"> {t['f_risky']}</label></form>
<div class="tablebox"><table data-sortable id="all"><thead><tr><th>{t['col_coin']}</th>
<th aria-sort="descending">{t['col_best']}</th>{''.join(f'<th>{EX_NAME[e]}</th>' for e in EXCHANGES)}
<th>{t['col_turnover']}</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>{t['where_h2']}</h2>
<div class="exlinks">{exchange_buttons(t)}</div>
<h2>{t['faq_h2']}</h2>{faq_html}
"""
    return p, p.render(t["index_title"].format(n=len(coins)), t["index_desc"], body, updated, faq_head)


def exchange_page(lang, ex, coins, updated):
    p = Page(lang, f"exchange/{ex}.html")
    t = p.t
    listed = sorted((c for c in coins if ex in c["markets"]), key=lambda c: -c["markets"][ex]["apr_7d"])
    rows = []
    for c in listed:
        m = c["markets"][ex]
        rows.append(
            f'<tr><td><a href="{p.link(cx_path(c, ex) if has_cx(c) else f"coin/{c["base"]}.html")}">{esc(c["base"])}</a>'
            f'{chips(c, t)}</td>'
            f'<td data-v="{m["apr_now"]:.3f}">{pct(m["apr_now"])}</td>'
            f'<td data-v="{m["apr_7d"]:.3f}">{pct(m["apr_7d"])}</td>'
            f'<td data-v="{m["apr_30d"] or 0:.3f}">{pct(m["apr_30d"])}</td>'
            f'<td data-v="{m["neg_share"] or 0:.1f}">{m["neg_share"] or 0:.0f}%</td>'
            f'<td data-v="{m["interval_h"]}">{m["interval_h"]:g} {t["hours"]}</td>'
            f'<td data-v="{m["turnover"]:.0f}">{money(m["turnover"], t)}</td>'
            f'<td>{t["yes"] if m["spot"] else t["no"]}</td></tr>')
    name = EX_NAME[ex]
    body = f"""
<h1>{t['ex_h1'].format(ex=name)}</h1>
<p class="lead">{t['ex_lead'].format(n=len(listed), ex=name, min=f"{config.MIN_MARKET_TURNOVER_USD:,}".replace(',', ' '),
                                      home=p.link('index.html'))}</p>
<div class="tablebox"><table data-sortable><thead><tr><th>{t['col_coin']}</th><th>{t['col_now']}</th>
<th aria-sort="descending">{t['col_7d']}</th><th>{t['col_30d']}</th><th title="{esc(t['col_neg_t'])}">{t['col_neg']}</th>
<th>{t['col_interval']}</th><th>{t['col_turnover']}</th><th>{t['col_spot']}</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>
<p style="margin-top:20px"><a class="cta" href="{esc(signup(ex))}" rel="sponsored noopener" target="_blank">{t['open_ex'].format(ex=name)}</a></p>
"""
    return p, p.render(t["ex_title"].format(ex=name, n=len(listed)), t["ex_desc"].format(ex=name), body, updated)


def daily_apr(history):
    """Daily (UTC) funding as APR: sum of the day's rates × 365."""
    days = defaultdict(float)
    for ts, r in history:
        days[ts // 86400] += r
    return {d: s * 365 * 100 for d, s in days.items()}


def chart_svg(series):
    """series: {exchange: {day: apr}} → SVG with one line per exchange."""
    days = sorted({d for s in series.values() for d in s})
    if len(days) < 2:
        return ""
    vals = sorted(abs(v) for s in series.values() for v in s.values())
    cap = max(vals[int(len(vals) * 0.95)] * 1.5, 10)  # so single outliers don't flatten the chart
    clip = lambda v: max(-cap, min(cap, v))
    top = max(max(clip(v) for s in series.values() for v in s.values()), 0)
    bottom = min(min(clip(v) for s in series.values() for v in s.values()), 0)
    w, h, left = 680, 230, 44
    span = (top - bottom) or 1
    x = lambda d: left + (d - days[0]) / (days[-1] - days[0]) * (w - left - 4)
    y = lambda v: 10 + (top - clip(v)) / span * (h - 20)
    lines = []
    for ex in EXCHANGES:
        s = series.get(ex)
        if not s:
            continue
        pts = " ".join(f"{x(d):.1f},{y(v):.1f}" for d, v in sorted(s.items()))
        lines.append(f'<polyline points="{pts}" fill="none" stroke="var(--c-{ex})" stroke-width="2" '
                     f'stroke-linejoin="round" stroke-linecap="round"><title>{EX_NAME[ex]}</title></polyline>')
    fmt = lambda d: datetime.fromtimestamp(d * 86400, timezone.utc).strftime("%d.%m")
    grid = "".join(f'<line x1="{left}" x2="{w}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="var(--line)"/>'
                   f'<text x="{left - 6}" y="{y(v) + 4:.1f}" text-anchor="end">{v:.0f}%</text>'
                   for v in sorted({top, 0, bottom}))
    return (f'<svg viewBox="0 0 {w} {h + 18}" role="img" style="font-size:11px;fill:var(--muted)">{grid}{"".join(lines)}'
            f'<text x="{left}" y="{h + 14}">{fmt(days[0])}</text>'
            f'<text x="{w}" y="{h + 14}" text-anchor="end">{fmt(days[-1])}</text></svg>')


def coin_text(c, t):
    m = c["markets"]
    names = [EX_NAME[e] for e in EXCHANGES if e in m]
    out = t["txt_markets"].format(b=c["base"], n=len(names), list=", ".join(names))
    if c["best"]:
        out += t["txt_best"].format(ex=EX_NAME[c["best"]], apr=f'{c["best_apr_7d"]:+.1f}%')
    liquid = max(m.values(), key=lambda x: x["turnover"])
    if liquid["neg_share"] is not None:
        out += t["txt_neg"].format(ex=EX_NAME[liquid["exchange"]], neg=f'{liquid["neg_share"]:.0f}')
    if c["spread"] and len(m) >= 2:
        s = c["spread"]
        out += t["txt_spread"].format(s=f'{s["apr_7d"]:+.1f}%', hi=EX_NAME[s["short"]], lo=EX_NAME[s["long"]])
    if c["age_days"] is not None and c["age_days"] < config.YOUNG_DAYS:
        out += t["txt_young"].format(d=c["age_days"])
    return out


def coin_page(lang, c, updated):
    p = Page(lang, f"coin/{c['base']}.html")
    t, b, m = p.t, esc(c["base"]), c["markets"]
    liquid = max(m.values(), key=lambda x: x["turnover"])

    rows = []
    for e in EXCHANGES:
        if e not in m:
            continue
        x = m[e]
        rows.append(
            f'<tr><td><a href="{p.link(cx_path(c, e) if has_cx(c) else f"exchange/{e}.html")}">{EX_NAME[e]}</a></td>'
            f'<td data-v="{x["apr_now"]:.3f}">{pct(x["apr_now"])}</td><td data-v="{x["apr_7d"]:.3f}">{pct(x["apr_7d"])}</td>'
            f'<td data-v="{x["apr_30d"] or 0:.3f}">{pct(x["apr_30d"])}</td>'
            f'<td data-v="{x["neg_share"] or 0:.1f}">{x["neg_share"] or 0:.0f}%</td>'
            f'<td data-v="{x["interval_h"]}">{x["interval_h"]:g} {t["hours"]}</td>'
            f'<td data-v="{x["turnover"]:.0f}">{money(x["turnover"], t)}</td><td>{t["yes"] if x["spot"] else t["no"]}</td>'
            f'<td><a class="btn" href="{esc(ref(e, x["url"]))}" rel="sponsored noopener" target="_blank">{t["trade"]}</a></td></tr>')

    hedgeable = [m[e] for e in EXCHANGES if e in m and m[e]["spot"]]
    if hedgeable:
        best = max(hedgeable, key=lambda x: x["apr_7d"])
        options = "".join(f'<option value="{x["apr_30d"] or 0:.4f}"{" selected" if x is best else ""}>'
                          f'{EX_NAME[x["exchange"]]} ({x["apr_30d"] or 0:+.1f}%)</option>' for x in hedgeable)
        calc = f"""<h2>{t['calc_h2']}</h2><p class="muted">{t['calc_note']}</p>
<form class="calc" oninput="calc()"><label>{t['calc_ex']}<select id="ex">{options}</select></label>
<label>{t['calc_cap']}<input id="cap" type="number" value="1000" min="1"></label>
<label>{t['calc_lev']}<select id="lev"><option value="1">{t['lev1']}</option><option value="2" selected>2x</option>
<option value="3">3x</option></select></label>
<label>{t['calc_month']}<b id="month"></b></label><label>{t['calc_fees']}<b id="fees"></b></label></form>
<script>function calc(){{const a=+document.getElementById('ex').value,cap=+document.getElementById('cap').value||0,
l=+document.getElementById('lev').value,pos=cap*l/(l+1);
document.getElementById('month').textContent='$'+(pos*a/100/12).toFixed(2);
document.getElementById('fees').textContent='$'+(pos*{FEES_ROUND_TRIP}).toFixed(2)}}calc();</script>"""
    else:
        calc = f'<div class="note">{t["no_hedge"].format(b=b)}</div>'

    series = {e: daily_apr(m[e]["history"]) for e in EXCHANGES if e in m}
    legend = "".join(f'<span><i style="background:var(--c-{e})"></i>{EX_NAME[e]}</span>' for e in EXCHANGES if e in m)
    spread = c["spread"]
    faq_html, faq_head = "", ""
    if has_cx(c):
        faq_html, faq_head = faq_block([
            (t["q_cmp"].format(b=c["base"]), t["a_cmp"].format(list=apr_list(c, "apr_7d"))),
            (t["q_avg"].format(b=c["base"]), t["a_avg"].format(list=apr_list(c, "apr_30d"))),
        ])
        faq_html = f"<h2>{t['faq_h2']}</h2>{faq_html}"
    body = f"""
<h1>{t['coin_h1'].format(b=b)}</h1>
<p class="lead">{esc(coin_text(c, t))}</p>
{f'<div class="note">{t["risk_note"]}</div>' if risky(c) else ''}
<div class="cards">
<div class="card"><div class="k">{t['coin_cards_best']}</div><div class="v">{pct(c['best_apr_7d'])}</div>
<div class="k">{EX_NAME[c['best']] if c['best'] else '—'}</div></div>
<div class="card"><div class="k">{t['coin_cards_spread']}</div><div class="v">{pct(spread['apr_7d']) if spread else pct(None)}</div>
<div class="k">{f"{EX_NAME[spread['short']]} / {EX_NAME[spread['long']]}" if spread else '—'}</div></div>
<div class="card"><div class="k">{t['coin_cards_turnover']}</div><div class="v">{money(c['turnover'], t)}</div></div>
<div class="card"><div class="k">{t['coin_cards_neg']}</div><div class="v">{liquid['neg_share'] or 0:.0f}%</div>
<div class="k">{EX_NAME[liquid['exchange']]}</div></div>
</div>
<h2>{t['coin_table_h2']}</h2>
<div class="tablebox"><table data-sortable><thead><tr><th>{t['col_ex']}</th><th>{t['col_now']}</th><th>{t['col_7d']}</th>
<th>{t['col_30d']}</th><th title="{esc(t['col_neg_t'])}">{t['col_neg']}</th><th>{t['col_interval']}</th>
<th>{t['col_turnover']}</th><th>{t['col_spot']}</th><th></th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>
<h2>{t['chart_h2']}</h2>
<div class="chart">{chart_svg(series)}<div class="legend">{legend}</div></div>
{calc}
{faq_html}
<p style="margin-top:24px"><a href="{p.link('guide.html')}">{t['guide_link']}</a> · <a href="{p.link('index.html')}">{t['back']}</a></p>
"""
    apr = f"{c['best_apr_7d']:+.1f}%" if c["best"] else f"{liquid['apr_7d']:+.1f}%"
    ex = EX_NAME[c["best"] or liquid["exchange"]]
    return p, p.render(t["coin_title"].format(b=c["base"], apr=apr), t["coin_desc"].format(b=c["base"], apr=apr, ex=ex),
                       body, updated, faq_head)


def coin_exchange_page(lang, c, ex, updated):
    """A coin on one exchange: targets queries like 'BTC funding rate OKX'."""
    p = Page(lang, cx_path(c, ex))
    t, b, m, name = p.t, c["base"], c["markets"][ex], EX_NAME[ex]
    f = lambda v: f"{v:+.1f}%" if v is not None else "—"
    nums = dict(b=b, ex=name, h=f"{m['interval_h']:g}", rate=f"{m['rate'] * 100:+.4f}%", now=f(m["apr_now"]),
                d7=f(m["apr_7d"]), d30=f(m["apr_30d"]), neg=f"{m['neg_share'] or 0:.0f}")

    days = {d: a for d, a in daily_apr(m["history"]).items() if d < updated // 86400}  # skip today's incomplete day
    fmt = lambda d: datetime.fromtimestamp(d * 86400, timezone.utc).strftime("%Y-%m-%d")
    hist_rows = "".join(f'<tr><td>{fmt(d)}</td><td data-v="{a / 365:.4f}">{pct(a / 365, 3)}</td>'
                        f'<td data-v="{a:.3f}">{pct(a)}</td></tr>' for d, a in sorted(days.items(), reverse=True)[:14])

    others = "".join(
        f'<a class="card" href="{p.link(cx_path(c, e))}"><div class="k">{EX_NAME[e]}</div>'
        f'<div class="v">{pct(c["markets"][e]["apr_7d"])}</div><div class="k">{t["card_sub"].format(ex=EX_NAME[e])}</div></a>'
        for e in EXCHANGES if e in c["markets"] and e != ex)

    hedge = (t["cx_spot"] if m["spot"] else t["cx_nospot"]).format(b=b, ex=name)
    faq_html, faq_head = faq_block([
        (t["q_now"].format(b=b, ex=name), t["a_now"].format(**nums)),
        (t["q_cmp"].format(b=b), t["a_cmp"].format(list=apr_list(c, "apr_7d"))),
        (t["q_hedge"].format(b=b, ex=name), hedge),
    ])

    body = f"""
<p class="muted" style="margin:20px 0 0"><a href="{p.link('index.html')}">{t['nav_rates']}</a> ›
<a href="{p.link(f'coin/{b}.html')}">{esc(b)}</a> › {name}</p>
<h1 style="margin-top:8px">{t['cx_h1'].format(b=esc(b), ex=name)}</h1>
<p class="lead">{esc(t['cx_lead'].format(**nums))}</p>
{f'<div class="note">{t["risk_note"]}</div>' if risky(c) else ''}
<div class="cards">
<div class="card"><div class="k">{t['cx_card_rate']}</div><div class="v">{pct(m['rate'] * 100, 4)}</div>
<div class="k">{t['col_interval']}: {m['interval_h']:g} {t['hours']}</div></div>
<div class="card"><div class="k">{t['cx_card_now']}</div><div class="v">{pct(m['apr_now'])}</div></div>
<div class="card"><div class="k">{t['col_7d']}</div><div class="v">{pct(m['apr_7d'])}</div></div>
<div class="card"><div class="k">{t['col_30d']}</div><div class="v">{pct(m['apr_30d'])}</div></div>
</div>
<p>{esc(hedge)}</p>
<p><a class="cta" href="{esc(ref(ex, m['url']))}" rel="sponsored noopener" target="_blank">{t['trade']} {esc(b)} — {name}</a></p>
<h2>{t['chart_h2']}</h2>
<div class="chart">{chart_svg({ex: days})}</div>
<h2>{t['cx_hist_h2'].format(b=esc(b), ex=name)}</h2>
<div class="tablebox"><table data-sortable><thead><tr><th aria-sort="descending">{t['col_date']}</th>
<th>{t['col_day_sum']}</th><th>{t['col_apr']}</th></tr></thead><tbody>{hist_rows}</tbody></table></div>
<h2>{t['cx_other_h2'].format(b=esc(b))}</h2>
<div class="cards">{others}</div>
<p><a href="{p.link(f'coin/{b}.html')}">{t['cx_compare']} →</a></p>
<h2>{t['faq_h2']}</h2>{faq_html}
<p style="margin-top:24px"><a href="{p.link(f'exchange/{ex}.html')}">{t['ex_h1'].format(ex=name)}</a> ·
<a href="{p.link('guide.html')}">{t['guide_link']}</a></p>
"""
    return p, p.render(t["cx_title"].format(b=b, ex=name, apr=nums["d7"]), t["cx_desc"].format(**nums), body, updated,
                       faq_head)


def guide_page(lang, updated):
    p = Page(lang, "guide.html")
    g = GUIDE[lang]
    body = (f'<div class="prose">{g["body"]}<p><a href="{p.link("index.html")}">{p.t["nav_rates"]} →</a></p>'
            f'<h2>{p.t["where_h2"]}</h2><div class="exlinks">{exchange_buttons(p.t)}</div></div>')
    return p, p.render(g["title"], g["desc"], body, updated)


def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--cached", action="store_true")
    args = ap.parse_args()

    if args.cached:
        with open(DATA, encoding="utf-8") as f:
            saved = json.load(f)
        updated = saved["updated"]
        # recompute metrics from saved history so formula changes apply without refetching
        start = updated - config.HISTORY_DAYS * 86400
        for c in saved["coins"]:
            for m in c["markets"].values():
                enrich(m, start, updated)
        coins = [s for s in (summarize(c["base"], c["markets"]) for c in saved["coins"]) if s]
    else:
        print("Собираю данные с бирж...", flush=True)
        coins, updated = collect(config, log=lambda msg: print(msg, flush=True))
        with open(DATA, "w", encoding="utf-8") as f:
            json.dump({"updated": updated, "coins": coins}, f)

    pages = []
    for lang in LANGS:
        pages.append(index_page(lang, coins, updated))
        pages.append(guide_page(lang, updated))
        pages += [exchange_page(lang, ex, coins, updated) for ex in EXCHANGES]
        pages += [coin_page(lang, c, updated) for c in coins]
        pages += [coin_exchange_page(lang, c, e, updated) for c in coins if has_cx(c) for e in c["markets"]]
    for p, text in pages:
        write(p.path, text)

    lastmod = datetime.fromtimestamp(updated, timezone.utc).strftime("%Y-%m-%d")
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{config.SITE_URL}/{p.path}</loc><lastmod>{lastmod}</lastmod></url>\n" for p, _ in pages)
          + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {config.SITE_URL}/sitemap.xml\n")
    write(".nojekyll", "")
    # files copied as-is to the site root (e.g. Google Search Console verification)
    if os.path.isdir(STATIC):
        shutil.copytree(STATIC, OUT, dirs_exist_ok=True)
    print(f"Готово: {len(coins)} монет, {len(pages)} страниц в {OUT}")


if __name__ == "__main__":
    main()
