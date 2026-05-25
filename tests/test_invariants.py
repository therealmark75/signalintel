"""
Scoring invariants — data correctness rules from docs/scoring_invariants.md.
All tests are read-only against the live DB via the `latest_signals` fixture.
"""
import pytest

VALID_RATINGS = {"STRONG_BUY", "BUY", "STRONG_HOLD", "HOLD", "WEAK_HOLD", "SELL", "STRONG_SELL"}


def test_composite_score_range(latest_signals):
    """Invariant 5: composite_score must be in [0, 100]."""
    for row in latest_signals:
        s = row["composite_score"]
        if s is not None:
            assert 0 <= s <= 100, f"{row['ticker']} composite_score={s} out of range"


def test_legal_penalty_non_positive(db):
    """Invariant 5: legal penalty must be ≤ 0 (never a boost)."""
    rows = db.execute("SELECT ticker, penalty FROM legal_risk").fetchall()
    for row in rows:
        p = row["penalty"]
        if p is not None:
            assert p <= 0, f"{row['ticker']} legal penalty={p} is positive"


def test_component_scores_in_range(latest_signals):
    """Invariant 5: momentum, quality, insider, reversion all in [0, 100]."""
    components = ["momentum_score", "quality_score", "insider_score", "reversion_score"]
    for row in latest_signals:
        for col in components:
            s = row[col]
            if s is not None:
                assert 0 <= s <= 100, f"{row['ticker']} {col}={s} out of range"


def test_v017_sub_scores_persisted(db, latest_signals):
    """v0.17.0+ rows must persist the five component sub-scores
    (earnings_score, piotroski_score, inst_own_score, analyst_mom_score,
    altman_penalty). Pre-0.17 rows are NULL by design — the test
    self-skips when the latest batch is older than v0.17.

    The persistence is a prerequisite for the OOS gate's graduating bar
    (forward IC + incremental Sharpe of any single component); without
    it, marginal IC cannot be isolated from stored history.

    Catches: regression where main.py drops one of the five values on the
             way into score_rows (the failure mode the persistence change
             was banked to prevent), OR a future schema migration that
             accidentally removes one of the columns.
    Ignores: pre-0.17 historical rows (their NULL sub-scores are correct;
             no backfill applies), and the magnitude of the values (the
             range invariant for momentum/quality/insider/reversion in
             test_component_scores_in_range is sufficient; this test
             checks PRESENCE, not value).
    """
    if not latest_signals:
        pytest.skip("signal_scores is empty")
    latest_version = latest_signals[0]["scoring_version"]
    if latest_version is None or tuple(int(x) for x in latest_version.split(".")) < (0, 17, 0):
        pytest.skip(f"latest scoring_version={latest_version} predates v0.17.0 sub-score persistence")

    sub_score_cols = ("earnings_score", "piotroski_score", "inst_own_score",
                      "analyst_mom_score", "altman_penalty")

    # SIGNAL — at v0.17+ at least SOME rows must carry non-NULL sub-scores
    # for each component. P5 allows a single ticker to legitimately have a
    # neutral (50.0) earnings_score, but the WHOLE COLUMN being NULL across
    # every row of a v0.17 batch is the exact failure mode that motivates
    # this test (the values get computed in memory then dropped at insert).
    for col in sub_score_cols:
        n_non_null = sum(1 for r in latest_signals if r[col] is not None)
        assert n_non_null > 0, (
            f"v{latest_version} batch persists ZERO non-NULL values for {col} "
            f"across {len(latest_signals)} rows — the in-memory scores are being "
            f"dropped on the way into signal_scores"
        )

    # SILENCE — the column being PRESENT in the schema is necessary but
    # not sufficient; check that the PRAGMA actually exposes all five.
    pragma_cols = {r["name"] for r in db.execute("PRAGMA table_info(signal_scores)").fetchall()}
    missing = [c for c in sub_score_cols if c not in pragma_cols]
    assert not missing, f"signal_scores schema missing sub-score columns: {missing}"


def test_all_ratings_valid(latest_signals):
    """Invariant 5: every rating must be one of the 7 known tiers."""
    for row in latest_signals:
        assert row["rating"] in VALID_RATINGS, \
            f"{row['ticker']} has unknown rating '{row['rating']}'"


def test_rating_matches_score_band(latest_signals):
    """
    Invariant 5: rating must be broadly consistent with composite_score.
    Mirrors assign_rating() from signals/scorer.py (same branch order).
    Allows up to 0.5% mismatch to tolerate boundary rounding in stored scores.
    Skips rows where insider_score or composite_score is NULL.
    """
    def expected_rating(composite, insider, reversion):
        if composite is None or insider is None:
            return None
        rv = reversion or 0
        if composite >= 72 and insider >= 65:
            return "STRONG_BUY"
        if composite >= 62:
            return "BUY"
        if rv >= 75:
            return "HOLD"
        if composite < 25 and insider <= 20:
            return "STRONG_SELL"
        if composite < 38 and insider <= 35:
            return "WEAK_HOLD"
        if composite < 45:
            return "SELL"
        return "STRONG_HOLD"

    mismatches = []
    checked = 0
    for row in latest_signals:
        exp = expected_rating(row["composite_score"], row["insider_score"], row["reversion_score"])
        if exp is None:
            continue
        checked += 1
        if row["rating"] != exp:
            mismatches.append(
                f"{row['ticker']}: score={row['composite_score']} insider={row['insider_score']} "
                f"reversion={row['reversion_score']} expected={exp} actual={row['rating']}"
            )

    max_allowed = max(5, int(checked * 0.005))  # 0.5% tolerance
    assert len(mismatches) <= max_allowed, (
        f"{len(mismatches)}/{checked} rating/score mismatches (max allowed {max_allowed}):\n"
        + "\n".join(mismatches[:15])
    )


def test_sector_modifier_range(latest_signals):
    """
    Invariant: sector_modifier_applied must be in [-7.5, +7.5].
    Skipped if all rows have NULL modifier (modifier not yet active).
    """
    non_null = [row for row in latest_signals if row["sector_modifier_applied"] is not None]
    if not non_null:
        pytest.skip("sector_modifier_applied is all NULL — sector modifier not yet active")
    for row in non_null:
        m = row["sector_modifier_applied"]
        assert -7.5 <= m <= 7.5, f"{row['ticker']} sector_modifier_applied={m} out of range"
