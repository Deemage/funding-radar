"""Сводка в Telegram-канал по данным последней сборки (data.json).

  python alerts.py --dry     # показать сообщение, ничего не отправляя
  python alerts.py           # отправить, если сейчас час из TELEGRAM_POST_HOURS_UTC
  python alerts.py --force   # отправить в любом случае

Токен бота и id канала берутся из переменных окружения TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID.
Бота создаёшь сам через @BotFather и добавляешь администратором в свой канал.
"""
import argparse
import html
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import config
from build import DATA, EX_NAME, risky

TEXT = {
    "ru": {
        "title": "📡 <b>Фандинг: сводка</b>",
        "top": "<b>Высокий фандинг с хеджем на споте</b> (7 дн., годовых):",
        "spreads": "<b>Межбиржевые спреды</b> (7 дн.):",
        "line_spread": "{b}: шорт {hi}, лонг {lo} — {s}",
        "more": "Все ставки и графики",
        "risk": "Не финансовая рекомендация. Высокий фандинг = высокий риск.",
    },
    "en": {
        "title": "📡 <b>Funding digest</b>",
        "top": "<b>High funding with spot hedge</b> (7d APR):",
        "spreads": "<b>Cross-exchange spreads</b> (7d):",
        "line_spread": "{b}: short {hi}, long {lo} — {s}",
        "more": "All rates and charts",
        "risk": "Not financial advice. High funding = high risk.",
    },
}


def message(coins, lang):
    t = TEXT[lang]
    solid = [c for c in coins if c["best"] and not risky(c)]
    top = sorted(solid, key=lambda c: -c["best_apr_7d"])[:5]
    spreads = sorted((c for c in coins if c["spread"] and not risky(c)), key=lambda c: -c["spread"]["apr_7d"])[:3]
    prefix = "" if lang == "ru" else "en/"
    lines = [t["title"], "", t["top"]]
    lines += [f"• <a href=\"{config.SITE_URL}/{prefix}coin/{html.escape(c['base'])}.html\">{html.escape(c['base'])}</a> "
              f"{c['best_apr_7d']:+.1f}% — {EX_NAME[c['best']]}" for c in top]
    if spreads:
        lines += ["", t["spreads"]]
        lines += ["• " + t["line_spread"].format(b=html.escape(c["base"]), hi=EX_NAME[c["spread"]["short"]],
                                                 lo=EX_NAME[c["spread"]["long"]], s=f"{c['spread']['apr_7d']:+.1f}%")
                  for c in spreads]
    lines += ["", f"<a href=\"{config.SITE_URL}/{prefix}index.html\">{t['more']}</a>", f"<i>{t['risk']}</i>"]
    return "\n".join(lines)


def send(text):
    token, chat = os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"]
    payload = urllib.parse.urlencode({"chat_id": chat, "text": text, "parse_mode": "HTML",
                                      "disable_web_page_preview": "true"}).encode()
    with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", payload, timeout=30) as resp:
        return json.load(resp)["ok"]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    with open(DATA, encoding="utf-8") as f:
        coins = json.load(f)["coins"]
    text = message(coins, config.TELEGRAM_LANG)
    if args.dry:
        print(text)
        return
    if not os.environ.get("TELEGRAM_BOT_TOKEN") or not os.environ.get("TELEGRAM_CHAT_ID"):
        print("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID не заданы — пропускаю")
        return
    if not args.force and datetime.now(timezone.utc).hour not in config.TELEGRAM_POST_HOURS_UTC:
        print("Сейчас не время публикации — пропускаю")
        return
    print("Отправлено" if send(text) else "Telegram вернул ошибку")


if __name__ == "__main__":
    main()
