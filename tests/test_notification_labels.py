"""
P13 regression tests for Telegram notification builders.

Catches: a notification builder leaking raw internal signal codes
(STRONG_BUY, BUY, STRONG_HOLD, HOLD, WEAK_HOLD, SELL, STRONG_SELL) into
user-facing message text instead of the display labels from
signals.signal_labels.tier_short (Very Strong, Strong, Stable, Neutral,
Soft, Bearish, Very Bearish). Origin: the daily-summary builder
(job_daily_summary) printed s['rating'].replace('_',' '), leaking "BUY"
to subscribers, while the watchlist builder already translated correctly.

Ignores: the internal-code emoji lookup (_RATING_EMOJI is keyed by code,
which is correct and internal), the score value, and Telegram transport
(send_alert is stubbed; no real HTTP).
"""
import main


def test_daily_summary_uses_display_labels_not_raw_codes(monkeypatch):
    """The daily-summary message must render the display label and never
    the raw internal code.

    Signal: tier_short('BUY') == 'Strong' appears in the message.
    Silence: the raw code 'BUY' (and its space-swapped 'STRONG BUY' form)
             must NOT appear. The synthetic ticker (LRCX) is chosen to
             contain no 'BUY' substring so the absence assertion is
             unambiguous.
    """
    captured = {}

    def fake_get_top_signals(db_path, limit=5):
        return [{"ticker": "LRCX", "rating": "BUY", "composite_score": 73.0}]

    def fake_send_alert(message):
        captured["message"] = message
        return True

    # job_daily_summary does `from database.db import get_top_signals` at
    # call time, so patch the source module attribute; send_alert is bound
    # at main module import, so patch it on main.
    monkeypatch.setattr("database.db.get_top_signals", fake_get_top_signals)
    monkeypatch.setattr(main, "send_alert", fake_send_alert)

    main.job_daily_summary()

    msg = captured.get("message")
    assert msg is not None, "daily summary did not send a message"
    # Signal: the display label fired.
    assert "Strong" in msg, f"display label 'Strong' missing from: {msg!r}"
    # Silence: no raw internal code leaked.
    assert "BUY" not in msg, f"raw code 'BUY' leaked into: {msg!r}"
    assert "STRONG BUY" not in msg, f"space-swapped code leaked into: {msg!r}"
