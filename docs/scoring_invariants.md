# SignalIntel Scoring Invariants

These invariants must hold after every scoring run. Any change to scoring logic must preserve them.

---

## 1. Legal Risk Distribution

- The majority of tickers should have `risk_label = 'None'` (~80–95%)
- `Minor` should be a small minority
- `Moderate`, `High`, `Critical`, `Extreme` should be rare
- A healthy distribution confirms the legal classifier is not over-triggering

**Verified 2026-05-05:** 27 None, 3 Minor (BRCC, COIN, SDOT)

---

## 2. Legal Risk Penalty Values

| Label | Penalty | Effect on Score |
|---|---|---|
| None | 2 | +2 pts bonus |
| Minor | -5 | -5 pts penalty |
| Moderate | -15 | -15 pts penalty |
| High | -25 | -25 pts penalty |
| Critical | -40 | -40 pts penalty |
| Extreme | -60 | -60 pts penalty |

**Note:** `None` penalty=2 is a positive bonus, not a penalty. UI must not display it as a negative number.

---

## 3. Legal Classifier — Hypothetical Phrase Exclusions

Keywords that trigger `Minor` or above must **not** match when surrounded by hypothetical/standard business language. The `is_hypothetical()` function screens a ±400-char context window for excluding phrases including:

- `"paragraph iv"` — patent IV challenges (normal pharma)
- `"we settled our"` — past completed settlements
- `"joint venture"`, `"supply agreement"`, `"license agreement"` — normal commercial contracts
- `"superfund"`, `"national priorities list"`, `"hazardous material releases"`, `"environmental cleanup"` — EPA Superfund (standard disclosure, not active litigation)

---

## 4. Legal Risk HTML Stripping

Before classification, raw SEC EDGAR HTML must be stripped. The `_classify()` function receives plain text, not HTML. Failure to strip produces false positives from CSS/markup strings matching keyword patterns.

---

## 5. Signal Score Components Must Sum Correctly

Composite score = momentum + quality + insider + reversion + legal_penalty

No component may produce a score outside its declared range. Negative penalties must reduce the composite, not increase it.

---

## 6. Short & Ownership Data Source

`short_interest_pct`, `short_ratio`, `inst_own_pct`, `forward_pe`, `peg_ratio`, `price_to_sales`, `price_to_book` are sourced from **individual FinViz ticker pages** (`finvizfinance(ticker).ticker_fundament()`), NOT from the bulk Custom screener view.

Reason: Custom screener view with `columns=` parameter only returns 20 rows regardless of filter size. Individual pages are the only reliable source for these fields.

---

## 7. Discovery Theme Counts — Legally Clean

The `legally_clean` theme must use **LEFT JOIN** against `legal_risk`, treating `NULL` (no record) as clean. Using `INNER JOIN` restricts results to only the ~30 tickers that have been classified, producing a count of ~26 instead of 8,000+.

```sql
-- CORRECT
LEFT JOIN legal_risk lr ON ss.ticker = lr.ticker
WHERE (lr.risk_label IS NULL OR lr.risk_label IN ('None','Minor'))

-- WRONG — only returns tickers already in legal_risk table
JOIN legal_risk lr ON ss.ticker = lr.ticker
WHERE lr.risk_label IN ('None','Minor')
```

---

## 8. Target Price Data Source

12M Target (`target_price`) and Target Upside (`target_upside`) are stored in `fmp_price_targets` and joined/cached into `signal_scores`. Must be non-null for 10,000+ tickers.

---

## 9. Backtest Data Maturity

Rating changes are logged via `detect_rating_changes()` after every scoring run. The backtest module requires ≥30 days of history for reliable statistics. Do not display meaningless averages on fewer than 30 days of data.

**First rating changes logged:** 2026-04-21  
**Reliable stats available from:** 2026-05-21

---

## 10. Filterable/Sortable Tables — State Preservation

All filterable and sortable tables must preserve filter state when sort changes, and preserve sort state when filters change.

The /screener implementation is the reference: all filter + sort state lives in a `state` object, every action updates `state` then calls `load()` which rebuilds the URL. New filterable tables must replicate this pattern, not invent their own.

For client-side sorted tables (dashboard ALL SIGNALS), reading the active filter button's raw rating value from its `onclick` attribute (not textContent) is the correct pattern.

**Applies to:** Dashboard ALL SIGNALS, /screener, /penny/screener, /watchlist

---

## Final Verification — 2026-05-05

| Check | Expected | Actual | Status |
|---|---|---|---|
| legal_risk distribution | Mostly None | 28 None / 3 Minor | ✅ |
| NONE penalty | 0 | 0 | ✅ |
| signal_scores count (latest) | 11,000+ | 11,118 | ✅ |
| target_price coverage | 10,000+ | 11,092 | ✅ |
| legally_clean theme count | 7,000+ | 7,961 | ✅ |
| Dashboard sort preserves filter | Yes | Fixed (Item 14) | ✅ |
| Penny screener Top Rated preset | STRONG_BUY/BUY, score≥70 | Fixed (Item 10) | ✅ |
| Legal None display | "None ✓" no penalty | Fixed (Item 12) | ✅ |
