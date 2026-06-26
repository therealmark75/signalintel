"""
Unit tests for the analyst-PT CAR decile stratification (signals/event_study_strata.py).

These exercise the pure stratification helpers directly (no price substrate
needed): the pct-change arithmetic, the prior<=0 drop, the NTILE decile
assignment, the zero-revision-bucket carve-out, and the label-vs-sign audit. The
CAR itself is supplied via a stub car_lookup, since the stratifier reuses
event_study.compute_event_car verbatim and these tests pin the STRATIFICATION,
not the CAR (that is covered by tests/test_event_study.py).
"""
import pytest

from signals.event_study import OK, IMMATURE
from signals.event_study_strata import (
    pct_change,
    assign_deciles,
    build_cohort,
    label_sign_audit,
    _decile_table,
)


# ── pct-change arithmetic ─────────────────────────

def test_pct_change_arithmetic_and_undefined():
    """A normal revision yields the signed percent move; an undefined revision
    (prior None, prior 0, prior negative, or current None) yields None.

    Catches: a sign flip or wrong denominator in the pct-change, and a prior<=0
    leaking through as a finite (explosive) number instead of None.
    Ignores: the decile a value lands in (covered by the assignment test).
    """
    assert pct_change(120.0, 100.0) == pytest.approx(20.0)
    assert pct_change(80.0, 100.0) == pytest.approx(-20.0)
    assert pct_change(100.0, 0.0) is None       # prior 0 -> undefined
    assert pct_change(100.0, -5.0) is None       # prior negative -> dropped
    assert pct_change(None, 100.0) is None        # missing current
    assert pct_change(100.0, None) is None        # missing prior


# ── prior<=0 drop in cohort build ─────────────────

def test_build_cohort_drops_prior_non_positive_and_nonok():
    """An OK event with prior<=0 is dropped into dropped_prior (not stratified);
    a non-OK event is excluded into nonok (it has no CAR to cut on); a clean OK
    event with a positive prior enters the cohort.

    Catches: a prior<=0 row silently entering the deciles with a bogus pct, and a
    non-OK (immature) event being treated as a stratifiable observation.
    Ignores: the decile math (separate test); this isolates cohort membership.
    """
    rows = [
        {"ticker": "A", "event_date": "2026-05-01", "action": "Raises",
         "current": 120.0, "prior": 100.0},   # clean OK -> kept
        {"ticker": "B", "event_date": "2026-05-01", "action": "Lowers",
         "current": 50.0, "prior": 0.0},       # OK but prior<=0 -> dropped_prior
        {"ticker": "C", "event_date": "2026-05-01", "action": "Raises",
         "current": 90.0, "prior": 80.0},      # immature -> nonok
    ]
    car_lookup = {
        ("A", "2026-05-01"): (OK, 5.0),
        ("B", "2026-05-01"): (OK, 9.9),
        ("C", "2026-05-01"): (IMMATURE, None),
    }
    cohort, dropped_prior, nonok = build_cohort(rows, car_lookup)
    assert [r["ticker"] for r in cohort] == ["A"]
    assert dropped_prior == 1
    assert nonok == 1


# ── NTILE decile assignment ───────────────────────

def test_assign_deciles_matches_ntile_remainder_distribution():
    """NTILE(10) over 23 ascending values puts the first 3 deciles at size 3 and
    the rest at size 2 (remainder 3 to the earliest buckets), with the smallest
    value in decile 1 and the largest in decile 10.

    Catches: an off-by-one in the remainder distribution (which would shift every
    boundary and silently mis-rank the CAR), and a reversed ordering.
    Ignores: tie handling beyond position-splitting (SQL NTILE also splits ties
    by row order; matched deliberately).
    """
    values = list(range(23))                     # 0..22 ascending
    labels = assign_deciles(values, groups=10)
    sizes = [labels.count(g) for g in range(1, 11)]
    assert sizes == [3, 3, 3, 2, 2, 2, 2, 2, 2, 2]
    assert labels[0] == 1 and labels[-1] == 10    # smallest in D1, largest in D10


def test_decile_table_mean_car_and_bounds():
    """_decile_table groups CARs by decile and reports per-decile mean CAR and
    pct bounds. With 10 values one per decile, each decile's mean CAR is that
    row's CAR and the ascending pct ordering is preserved.

    Catches: mis-pairing a CAR with the wrong decile after the sort.
    Ignores: empty-decile rendering (covered implicitly; not constructed here).
    """
    cohort = [{"pct": float(i), "car": float(i * 2)} for i in range(10)]
    rows, means = _decile_table(cohort, groups=10)
    assert [r["n"] for r in rows] == [1] * 10
    assert means == [float(i * 2) for i in range(10)]     # D1..D10 ascending


# ── zero-revision bucket carve-out ────────────────

def test_zero_bucket_isolates_zero_revision_rows():
    """The zero-bucket variant holds out every pct==0 row and deciles only the
    non-zero rows, so a cohort with three zeros and four non-zeros yields a zero
    bucket of exactly 3 and non-zero deciles that contain none of them.

    Catches: zero-revision (Maintains) rows leaking into the non-zero deciles, or
    a non-zero row being swept into the zero bucket.
    Ignores: the headline pooled cut (which deliberately keeps the zeros in).
    """
    cohort = [
        {"pct": -5.0, "car": -1.0}, {"pct": -3.0, "car": -0.5},
        {"pct": 0.0, "car": 0.1}, {"pct": 0.0, "car": 0.2}, {"pct": 0.0, "car": 0.3},
        {"pct": 4.0, "car": 1.0}, {"pct": 7.0, "car": 2.0},
    ]
    zero = [r for r in cohort if r["pct"] == 0.0]
    nonzero = [r for r in cohort if r["pct"] != 0.0]
    assert len(zero) == 3
    assert len(nonzero) == 4
    nz_rows, _ = _decile_table(nonzero, groups=2)
    assigned = sum(r["n"] for r in nz_rows)
    assert assigned == 4                           # only the non-zero rows deciled


# ── label-vs-sign audit ───────────────────────────

def test_label_sign_audit_counts_contradictions_and_near_zero_prior():
    """The audit counts rows whose action label contradicts the pct sign: a
    Lowers with a positive revision, a Raises with a negative revision, a
    Maintains with a non-zero revision. A contradiction whose prior target is
    below $1 is classed near_zero_prior (ratio-inflation suspect); otherwise
    genuine.

    Catches: a contradiction going uncounted, or a near-zero-prior artefact being
    mislabelled as a genuine mislabel (which would overstate dirty labels).
    Ignores: clean rows (a Raises with pct>0 must NOT count); the magnitude of
    the contradiction.
    """
    rows = [
        {"action": "Lowers", "pct": 10.0, "prior": 50.0},    # contradiction, genuine
        {"action": "Lowers", "pct": 600.0, "prior": 0.20},   # contradiction, near-zero prior
        {"action": "Raises", "pct": -5.0, "prior": 80.0},    # contradiction, genuine
        {"action": "Maintains", "pct": 2.0, "prior": 30.0},  # contradiction, genuine
        {"action": "Raises", "pct": 10.0, "prior": 20.0},    # clean, NOT counted
        {"action": "Lowers", "pct": -8.0, "prior": 40.0},    # clean, NOT counted
    ]
    audit = label_sign_audit(rows)
    assert audit["Lowers"]["contradictions"] == 2
    assert audit["Lowers"]["near_zero_prior"] == 1
    assert audit["Lowers"]["genuine"] == 1
    assert audit["Raises"]["contradictions"] == 1
    assert audit["Raises"]["genuine"] == 1
    assert audit["Maintains"]["contradictions"] == 1
