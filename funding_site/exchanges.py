"""Exchange adapters. Each one does two things:
  markets()                    → list of USDT perpetuals in a common format
  history(symbol, start, end)  → [(time_sec, rate)] in ascending order
All APIs are public, no keys needed.
"""
import json
import time
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (funding-site)"}


def get(url, pause=0.1):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as resp:
                data = json.load(resp)
            time.sleep(pause)
            return data
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))


def market(exchange, base, symbol, rate, interval_h, next_funding, turnover, price, spot, url, listed, mm=None):
    return {
        "exchange": exchange, "base": base, "symbol": symbol,
        "rate": rate, "interval_h": interval_h, "per_year": 365 * 24 / interval_h,
        "apr_now": rate * 365 * 24 / interval_h * 100,
        "next_funding": next_funding, "turnover": turnover, "price": price,
        "spot": spot, "url": url, "age_days": int((time.time() - listed) // 86400) if listed else None, "mm": mm,
    }


class KuCoin:
    name = "KuCoin"
    key = "kucoin"
    API = "https://api-futures.kucoin.com/api/v1"

    def markets(self):
        spot = {s["symbol"] for s in get("https://api.kucoin.com/api/v2/symbols")["data"] if s["enableTrading"]}
        out = []
        for c in get(f"{self.API}/contracts/active")["data"]:
            if c["quoteCurrency"] != "USDT" or c["expireDate"] is not None or c["isInverse"]:
                continue
            if c.get("fundingFeeRate") is None:
                continue
            base = "BTC" if c["baseCurrency"] == "XBT" else c["baseCurrency"]
            out.append(market(
                self.key, base, c["symbol"], float(c["fundingFeeRate"]), c["fundingRateGranularity"] / 3_600_000,
                c["nextFundingRateDateTime"] // 1000, float(c["turnoverOf24h"] or 0), float(c["markPrice"]),
                f"{base}-USDT" in spot, f"https://www.kucoin.com/futures/trade/{c['symbol']}",
                c["firstOpenDate"] // 1000, float(c["maintainMargin"])))
        return out

    def history(self, symbol, start, end):
        out, window, cursor = {}, 30 * 86400, start
        while cursor < end:
            chunk_end = min(end, cursor + window)
            rows = get(f"{self.API}/contract/funding-rates?symbol={symbol}&from={cursor * 1000}&to={chunk_end * 1000}")["data"] or []
            if len(rows) >= 100 and window > 3600:  # 100-row limit, so narrow the window
                window //= 2
                continue
            for r in rows:
                out[r["timepoint"] // 1000] = float(r["fundingRate"])
            cursor = chunk_end
        return sorted(out.items())


class OKX:
    name = "OKX"
    key = "okx"
    API = "https://www.okx.com/api/v5"

    def markets(self):
        spot = {s["instId"] for s in get(f"{self.API}/public/instruments?instType=SPOT")["data"] if s["state"] == "live"}
        insts = {i["instId"]: i for i in get(f"{self.API}/public/instruments?instType=SWAP")["data"]
                 if i["settleCcy"] == "USDT" and i["state"] == "live"}
        tickers = {t["instId"]: t for t in get(f"{self.API}/market/tickers?instType=SWAP")["data"]}
        out = []
        for f in get(f"{self.API}/public/funding-rate?instId=ANY")["data"]:
            i, t = insts.get(f["instId"]), tickers.get(f["instId"])
            if not i or not t or not f.get("fundingRate"):
                continue
            base = f["instId"].split("-")[0]
            interval = (int(f["nextFundingTime"]) - int(f["fundingTime"])) / 3_600_000 if f.get("nextFundingTime") else 8
            price = float(t["last"] or 0)
            out.append(market(
                self.key, base, f["instId"], float(f["fundingRate"]), interval or 8,
                int(f["fundingTime"]) // 1000, float(t["volCcy24h"] or 0) * price, price,
                f"{base}-USDT" in spot, f"https://www.okx.com/trade-swap/{f['instId'].lower()}",
                int(i["listTime"]) // 1000 if i.get("listTime") else None))
        return out

    def history(self, symbol, start, end):
        out, after = {}, end * 1000
        while True:
            rows = get(f"{self.API}/public/funding-rate-history?instId={symbol}&limit=100&after={after}", pause=0.25)["data"]
            if not rows:
                break
            for r in rows:
                out[int(r["fundingTime"]) // 1000] = float(r["realizedRate"] or r["fundingRate"])
            after = min(int(r["fundingTime"]) for r in rows)
            if after <= start * 1000 or len(rows) < 100:
                break
        return sorted((t, r) for t, r in out.items() if t >= start)


class Gate:
    name = "Gate"
    key = "gate"
    API = "https://api.gateio.ws/api/v4"

    def markets(self):
        spot = {p["id"] for p in get(f"{self.API}/spot/currency_pairs") if p["trade_status"] == "tradable"}
        tickers = {t["contract"]: t for t in get(f"{self.API}/futures/usdt/tickers")}
        out = []
        for c in get(f"{self.API}/futures/usdt/contracts"):
            t = tickers.get(c["name"])
            if not t or c.get("in_delisting") or c.get("status", "trading") != "trading":
                continue
            base = c["name"].split("_")[0]
            out.append(market(
                self.key, base, c["name"], float(c["funding_rate"]), c["funding_interval"] / 3600,
                c["funding_next_apply"], float(t.get("volume_24h_quote") or 0), float(c["mark_price"]),
                c["name"] in spot, f"https://www.gate.io/futures/USDT/{c['name']}",
                c.get("launch_time") or c.get("create_time"), float(c["maintenance_rate"])))
        return out

    def history(self, symbol, start, end):
        rows = get(f"{self.API}/futures/usdt/funding_rate?contract={symbol}&limit=1000&from={start}&to={end}")
        return sorted((int(r["t"]), float(r["r"])) for r in rows)


# Bybit is not included: its API returns 403 to requests from GitHub Actions servers.
ALL = [KuCoin(), OKX(), Gate()]
