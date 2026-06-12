# Candles Gap Sentimentor — daily TradingView screener

A static page that renders a daily snapshot of a TradingView screener.
No backend: a scheduled job writes `data.json`, and `index.html` displays it.

```
data source (TradingView)  ->  fetch_screener.py  ->  data.json  ->  index.html renders it
                                (run on a schedule)     (committed)     (GitHub Pages)
```

## File layout (place these at the repo ROOT)

```
index.html                          <- the page (fetches data.json)
data.json                           <- the data (starts as sample, then auto-updated)
scripts/fetch_screener.py           <- pulls the screener
.github/workflows/update-screener.yml  <- runs the script on a daily schedule
```

## Configure your screen

Edit the CONFIG block at the top of `scripts/fetch_screener.py`:
`MARKET`, `COLUMNS`, `FILTERS`, `SORT_BY`, `MAX_ROWS`. These mirror the
filters/columns you set in the TradingView Screener UI.

## ⚠️ Important: TradingView blocks datacenter IPs

The TradingView scanner endpoint is unofficial and **frequently returns 403 to
cloud/datacenter IPs** — which can include GitHub Actions runners. If the
scheduled job fails with HTTP 403, the GitHub-hosted approach won't work for you.
Two reliable alternatives:

### Option A (most reliable) — run the fetch on your own machine
TradingView allows normal residential IPs. Schedule the script locally:

- **Windows Task Scheduler**: run daily ->
  `python C:\path\to\scripts\fetch_screener.py`
  then `git add data.json && git commit -m "update" && git push`
  (a tiny `.bat` wrapper does all three).

This pushes a fresh `data.json` to the repo each day; GitHub Pages updates
automatically. No server, no API keys.

### Option B (zero API risk) — manual CSV export
Use the TradingView Screener's **Export CSV** button and convert it to
`data.json` (or use a CSV-upload version of the page). Slower, but never blocked.

## Test locally

```
python scripts/fetch_screener.py     # writes data.json
python -m http.server 8000           # then open http://localhost:8000
```

This tool is for personal/educational use. The TradingView endpoint is
undocumented and subject to their Terms of Service — don't build a commercial
product on it.
