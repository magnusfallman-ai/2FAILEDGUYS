# Cobra Trading → Skatteverket SRU (K4)

A single-file local web app that turns a Cobra Trading / DAS Trader activity report into:

1. **SRU files** (`INFO.SRU` + `BLANKETTER.SRU`) for the Swedish tax form **K4** (income year 2022–2025).
2. **Trading graphs** — cumulative P&L, monthly P&L, top symbols, win/loss distribution.

Everything runs locally in your browser. No data is uploaded anywhere.

## Usage

1. Open `index.html` in any modern browser (just double-click it).
2. Upload your Cobra activity report CSV (or click **Load demo data**).
3. Confirm the auto-detected column mapping.
4. Pick a USD→SEK conversion mode (fixed rate or per-date CSV).
5. Fill in personnummer, name and income year.
6. Review the K4 rows.
7. Download `INFO.SRU` and `BLANKETTER.SRU` and submit to Skatteverket.

## How it works

- **FIFO matching** — Buys and sells are paired in chronological order per symbol. Short positions are detected automatically when the first trade is a sell.
- **Aggregation** — By default, all closed trades for the same symbol are aggregated into one K4 row (Skatteverket's recommended format). You can switch to one-row-per-trade.
- **Commissions** — Added to cost basis / netted from proceeds.
- **FX** — USD amounts are converted to SEK either with a fixed annual rate or with per-date rates supplied as a CSV (`YYYY-MM-DD,rate` per line — e.g. from Riksbanken).
- **SRU format** — Files are emitted in ISO-8859-1 with CRLF line endings, K4 form `K4-{year}P4`, up to 9 rows per `#BLANKETT` block.

## Expected CSV columns

The app auto-detects, but typical Cobra/DAS exports use:

| Field      | Common header names                                          |
|------------|--------------------------------------------------------------|
| Symbol     | `Symbol`, `Ticker`                                           |
| Side       | `B/S`, `Side`, `Action`                                      |
| Quantity   | `Qty`, `Quantity`, `Shares`                                  |
| Price      | `Price`, `Exec Price`                                        |
| Date       | `Date`, `Trade Date`                                         |
| Time       | `Time`, `Trade Time` (optional)                              |
| Commission | `Commission`, `Fees` (optional)                              |

If auto-detection picks the wrong column, fix it in the mapping section.

## Caveats

- **Cost basis from previous years** — If an opening leg is missing from the CSV (you held a position into the year), the matcher will skip the close. Either include the prior buys in the CSV or split-trade manually.
- **Aggregated rows** mix the open and close FX rates per trade. If you want strict accuracy, switch to "one row per closed trade".
- **Always double-check the previewed `BLANKETTER.SRU`** against Skatteverket's instructions for your specific situation. This tool helps you prepare the file but does not give tax advice.
