# Funding Radar

Статический сайт со ставками фандинга бессрочных фьючерсов KuCoin, OKX и Gate (ru + en).
GitHub Actions пересобирает его каждый час и публикует на GitHub Pages.

- `funding_site/` — сайт: сбор данных (`fetch.py`, `exchanges.py`), генератор (`build.py`), тексты (`i18n.py`),
  Telegram-сводка (`alerts.py`), настройки (`config.py`: адрес сайта, реферальные параметры, фильтры).
- `kucoin_bot/` — бэктесты стратегий (грид, DCA, фандинг-арбитраж, ротация) на истории KuCoin.

Локально:

```bash
cd funding_site
python build.py
python -m http.server 8765 --directory public
```

Telegram: создать бота через @BotFather, добавить админом в канал, в Settings → Secrets → Actions
репозитория добавить `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`.

Не является финансовой рекомендацией.
