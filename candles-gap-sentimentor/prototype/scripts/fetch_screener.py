#!/usr/bin/env python3
"""
Fetch a TradingView screener into data.json.

Calls TradingView's (unofficial, undocumented) scanner endpoint — the same data
source the TradingView Screener UI uses. Personal / educational use only; the
endpoint is undocumented and can change without notice.

This script has your EXACT screen embedded (US pre-market gappers). To change the
screen, recapture the `scan` request payload from DevTools and replace
REQUEST_PAYLOAD below. DISPLAY picks which of the returned columns to show.

Run locally:  python scripts/fetch_screener.py
In CI:        run by .github/workflows/update-screener.yml on a daily schedule.
"""

import json
import sys
import datetime
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# 1) The exact request captured from your TradingView screener (verbatim).
# ---------------------------------------------------------------------------
SCAN_URL = "https://scanner.tradingview.com/america/scan?label-product=screener-stock"

REQUEST_PAYLOAD = {
    "columns": [
        "ticker-view", "premarket_change", "change_from_open", "premarket_close",
        "type", "typespecs", "pricescale", "minmov", "fractional", "minmove2",
        "currency", "country.tr", "country_code_fund", "float_shares_percent_current",
        "premarket_volume", "float_shares_outstanding_current", "market_cap_basic",
        "fundamental_currency_code", "sector.tr", "market", "sector", "exchange.tr",
        "source-logoid",
    ],
    "filter": [
        {"left": "exchange", "operation": "in_range", "right": ["AMEX", "CBOE", "NASDAQ", "NYSE", "OTC"]},
        {"left": "premarket_change", "operation": "greater", "right": 25},
        {"left": "premarket_close", "operation": "egreater", "right": 1},
        {"left": "premarket_volume", "operation": "greater", "right": 100000},
    ],
    "ignore_unknown_fields": False,
    "options": {"lang": "en"},
    "range": [0, 100],
    "sort": {"sortBy": "premarket_change", "sortOrder": "desc"},
    "markets": ["america"],
    "filter2": {
        "operator": "and",
        "operands": [
            {"operation": {"operator": "or", "operands": [
                {"operation": {"operator": "and", "operands": [
                    {"expression": {"left": "type", "operation": "equal", "right": "stock"}},
                    {"expression": {"left": "typespecs", "operation": "has", "right": ["common"]}}]}},
                {"operation": {"operator": "and", "operands": [
                    {"expression": {"left": "type", "operation": "equal", "right": "dr"}}]}},
                {"operation": {"operator": "and", "operands": [
                    {"expression": {"left": "type", "operation": "equal", "right": "stock"}},
                    {"expression": {"left": "typespecs", "operation": "has", "right": ["preferred"]}}]}},
            ]}},
            {"operation": {"operator": "or", "operands": [
                {"operation": {"operator": "and", "operands": [
                    {"expression": {"left": "type", "operation": "equal", "right": "stock"}},
                    {"expression": {"left": "typespecs", "operation": "has", "right": ["common"]}}]}},
                {"operation": {"operator": "and", "operands": [
                    {"expression": {"left": "type", "operation": "equal", "right": "stock"}},
                    {"expression": {"left": "typespecs", "operation": "has", "right": ["preferred"]}}]}},
                {"operation": {"operator": "and", "operands": [
                    {"expression": {"left": "type", "operation": "equal", "right": "dr"}}]}},
                {"operation": {"operator": "and", "operands": [
                    {"expression": {"left": "type", "operation": "equal", "right": "fund"}},
                    {"expression": {"left": "typespecs", "operation": "has_none_of", "right": ["etf", "mutual"]}}]}},
            ]}},
            {"expression": {"left": "typespecs", "operation": "has_none_of", "right": ["pre-ipo"]}},
        ],
    },
}

# ---------------------------------------------------------------------------
# 2) Which columns to actually SHOW on the page (subset of what we request).
#    "left" must be a requested column id (or "symbol", derived from the ticker).
#    "fmt": pct | price | vol | money | text
# ---------------------------------------------------------------------------
DISPLAY = [
    {"left": "symbol",                           "label": "Symbol",      "fmt": "text"},
    {"left": "premarket_change",                 "label": "PM Chg %",    "fmt": "pct"},
    {"left": "change_from_open",                 "label": "From Open %", "fmt": "pct"},
    {"left": "premarket_close",                  "label": "PM Price",    "fmt": "price"},
    {"left": "premarket_volume",                 "label": "PM Vol",      "fmt": "vol"},
    {"left": "float_shares_percent_current",     "label": "Float %",     "fmt": "pct"},
    {"left": "float_shares_outstanding_current", "label": "Float Sh",    "fmt": "vol"},
    {"left": "market_cap_basic",                 "label": "Mkt Cap",     "fmt": "money"},
    {"left": "sector",                           "label": "Sector",      "fmt": "text"},
    {"left": "exchange.tr",                       "label": "Exch",        "fmt": "text"},
]

OUTPUT = "data.json"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/",
}

# ---------------------------------------------------------------------------


def fetch():
    body = json.dumps(REQUEST_PAYLOAD).encode("utf-8")
    req = urllib.request.Request(SCAN_URL, data=body, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def to_rows(raw):
    # response "d" arrays map positionally to REQUEST_PAYLOAD["columns"]
    idx = {name: i for i, name in enumerate(REQUEST_PAYLOAD["columns"])}
    rows = []
    for item in raw.get("data", []):
        d = item.get("d", [])
        s = item.get("s", "")  # e.g. "NASDAQ:AAPL"
        get = lambda key: (d[idx[key]] if key in idx and idx[key] < len(d) else None)
        row = {"_ticker": s, "symbol": s.split(":")[-1] if s else ""}
        for col in DISPLAY:
            if col["left"] == "symbol":
                continue
            row[col["left"]] = get(col["left"])
        rows.append(row)
    return rows


def main():
    try:
        raw = fetch()
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code}: {e.reason}", file=sys.stderr)
        print("If this is 403 on a GitHub Actions runner, TradingView is blocking the "
              "datacenter IP — see README for the local-scheduler fallback.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"Fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    rows = to_rows(raw)
    out = {
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": "TradingView pre-market gappers (america)",
        "total_count": raw.get("totalCount"),
        "columns": DISPLAY,
        "rows": rows,
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(rows)} rows to {OUTPUT} (total matching: {out['total_count']}).")


if __name__ == "__main__":
    main()
