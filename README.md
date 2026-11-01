# Funding Radar

**Live site: https://deemage.github.io/funding-radar/**

Free, hourly-updated funding rates for perpetual futures on **KuCoin, OKX and Gate**:
current rates, 7- and 30-day APR, cross-exchange spreads, charts and a profit calculator for 150 coins.
Available in English and Russian (`/ru/`).

## Features

- Funding rates from three exchanges in one table, sorted by APR
- Per-coin pages with 30-day funding history charts and a calculator
- Cross-exchange funding spreads (short where funding is high, long where it is low)
- Risk flags: young listings, high maintenance margin, frequently negative funding
- A guide to funding-rate arbitrage based on two years of backtests
- Optional Telegram digest twice a day

## How it works

GitHub Actions runs `funding_site/build.py` every hour: it pulls public exchange APIs, generates static HTML
and deploys it to GitHub Pages. No server, no database, no API keys.

- `funding_site/` — the site: data collection (`fetch.py`, `exchanges.py`), generator (`build.py`),
  texts (`i18n.py`), Telegram digest (`alerts.py`), settings (`config.py`: site URL, referral links, filters)
- `kucoin_bot/` — strategy backtests (grid, DCA, funding arbitrage, rotation) on KuCoin history

## Run locally

Python 3.12, standard library only.

```bash
cd funding_site
python build.py
python -m http.server 8765 --directory public
```

Then open http://localhost:8765.

## Telegram digest

Create a bot via @BotFather, add it as an admin to your channel, then add `TELEGRAM_BOT_TOKEN` and
`TELEGRAM_CHAT_ID` under Settings → Secrets and variables → Actions.

## Disclaimer

Not financial advice. High funding usually means high risk. Some exchange links are referral links.
