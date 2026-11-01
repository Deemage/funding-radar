"""Site settings. Change things here; no need to touch the rest of the code."""

# Published site URL (used for sitemap, canonical and hreflang), no trailing slash
SITE_URL = "https://deemage.github.io/funding-radar"

# Referral params appended to every link to the exchange.
# Taken from the exchange's affiliate dashboard, e.g. "rcode=ABC123" (KuCoin).
# Empty means plain links.
REFERRAL_QUERY = {
    "kucoin": "rcode=Z6CDGYKB",
    "okx": "",
    "gate": "",
}

# Ready-made referral links from the affiliate dashboard; the main 'Open exchange' buttons point to them.
# Without a link, the button points to the futures page with the REFERRAL_QUERY param.
REFERRAL_LINK = {
    "kucoin": "https://www.kucoin.com/r/rf/Z6CDGYKB",
    "okx": "https://web3.okx.com/join/MYPROFIT",  # OKX Wallet (Web3) referral, not the exchange one
}

# Which coins to show
MIN_MARKET_TURNOVER_USD = 300_000   # count a market on an exchange from this 24h turnover
MIN_TURNOVER_USD = 2_000_000        # show a coin from this total turnover across exchanges
MAX_COINS = 150                     # how many coins (by turnover, descending)
HISTORY_DAYS = 30                   # funding history depth
YOUNG_DAYS = 90                     # coins younger than this are flagged as higher risk

# Telegram channel (alerts). Token and channel id come from the environment variables
# TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (on GitHub, in Secrets).
TELEGRAM_LANG = "ru"
TELEGRAM_POST_HOURS_UTC = [7, 19]   # hours to post the digest at
