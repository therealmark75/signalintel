# SignalIntel Test Suite

Automated pytest suite covering smoke tests, scoring invariants, data integrity, theme coherence, and signal label migration completeness.

## Run

```bash
source venv/bin/activate
pytest              # run all tests
pytest -ra -q       # short summary of skips and failures
pytest tests/test_smoke.py          # smoke only
pytest tests/test_invariants.py     # scoring invariants only
```

## Test files

| File | What it covers |
|---|---|
| `conftest.py` | Shared fixtures: `db`, `flask_app`, `client`, `latest_run_date`, `latest_signals` |
| `test_smoke.py` | Every page route returns 200; every API route returns 200 + valid JSON |
| `test_invariants.py` | Composite/component score ranges, legal penalty ≤ 0, rating/score consistency |
| `test_data_integrity.py` | Data freshness (< 48h), no duplicates, rating distribution, orphan count |
| `test_themes.py` | Theme field completeness, legally_clean LEFT JOIN confirmation, `/api/theme-counts` coverage |
| `test_signal_labels.py` | `SIGNAL_TIERS` correctness, `tier_label()`/`tier_short()` values, template absence grep |

## Auth

All page routes require a logged-in session. The `client` fixture injects `session['user_id'] = 2` (user `markn`) into the Flask test session automatically.

## Conditional skips

Two tests skip rather than fail when their data prerequisites don't exist yet:

- `test_target_price_coverage` — skips if `fmp_price_targets` not yet populated (currently 0%)
- `test_sector_modifier_range` — skips if `composite_score_raw` is all NULL (modifier not yet active)

## DB

Tests connect read-only to `data/trading_system.db` (path resolved via `config.settings.DATABASE_PATH`). Tests never write to the database.
