#!/usr/bin/env python3
"""
Fetch a TradingView screener into data.json.

This calls TradingView's (unofficial, undocumented) scanner endpoint, which is
the same data source the TradingView Screener UI uses. It is intended for
personal / educational use. The endpoint can change without notice.

Configure the screen below: market, columns, filters, sort, and how many rows.
Run locally:  python scripts/fetch_screener.py
In CI it is run by .github/workflows/update-screener.yml on a daily schedule.
"""

import json
import sys
import datetime
import urllib.request
import urllib.error

# ---------------------------------------------------------------------------
# CONFIG — edit this to match your TradingView screener
# ---------------------------------------------------------------------------

# Market scan ("america", "sweden", "crypto", "forex", etc.)
MARKET = "america"

# Columns to pull. left = TradingView field id, label = header shown on the page.
# Find field ids by inspecting your screener columns; common ones below.
COLUMNS = [
    {"left": "name",              "label": "Symbol"},
    {"left": "description",       "label": "Name"},
    {"left": "close",             "label": "Price"},
    {"left": "change",            "label": "Change %"},
    {"left": "volume",            "label": "Volume"},
    {"left": "relative_volume_10d_calc", "label": "Rel Vol"},
    {"left": "gap",               "label": "Gap %"},
    {"left": "market_cap_basic",  "label": "Mkt Cap"},
    {"left": "sector",            "label": "Sector"},
]

# Filters — list of {left, operation, right}. Mirror your screener's filters.
# operations: greater, egreater, less, eless, equal, in_range, nempty, ...
FILTERS = [
    {"left": "market_cap_basic", "operation": "egreater", "right": 300_000_000},
    {"left": "volume",           "operation": "egreater", "right": 500_000},
    # example gap filter: only stocks gapping more than 2% up
    # {"left": "gap", "operation": "egreater", "right": 2},
]

SORT_BY = "gap"        # column to sort on
SORT_ORDER = "desc"    # "desc" or "asc"
MAX_ROWS = 100

OUTPUT = "data.json"

SCANNER_URL = "https://scanner.tradingview.com/{market}/scan"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CandlesGapSentimentor/1.0)",
    "Content-Type": "application/json",
    "Accept": "application/json",
}

# ---------------------------------------------------------------------------


def build_payload():
    return {
        "filter": FILTERS,
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [c["left"] for c in COLUMNS],
        "sort": {"sortBy": SORT_BY, "sortOrder": SORT_ORDER},
        "range": [0, MAX_ROWS],
    }


def fetch():
    url = SCANNER_URL.format(market=MARKET)
    body = json.dumps(build_payload()).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def to_rows(raw):
    keys = [c["left"] for c in COLUMNS]
    rows = []
    for item in raw.get("data", []):
        values = item.get("d", [])
        row = {"_ticker": item.get("s", "")}
        for i, key in enumerate(keys):
            row[key] = values[i] if i < len(values) else None
        rows.append(row)
    return rows


def main():
    try:
        raw = fetch()
    except urllib.error.HTTPError as e:
        print(f"HTTP error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        print(f"Fetch failed: {e}", file=sys.stderr)
        sys.exit(1)

    rows = to_rows(raw)
    out = {
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "source": f"TradingView screener ({MARKET})",
        "total_count": raw.get("totalCount"),
        "columns": COLUMNS,
        "rows": rows,
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(rows)} rows to {OUTPUT} (total matching: {out['total_count']}).")


if __name__ == "__main__":
    main()
