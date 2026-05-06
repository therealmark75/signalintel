"""
Signal label migration completeness tests (P13).
Verifies that signal_labels.py is correct and that templates contain no old directive language.
"""
import subprocess
import os
import pytest

from signals.signal_labels import SIGNAL_TIERS, tier_label, tier_short, tier_colour

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "web", "templates")

ALL_TIERS = ["STRONG_BUY", "BUY", "STRONG_HOLD", "HOLD", "WEAK_HOLD", "SELL", "STRONG_SELL"]

EXPECTED_LABELS = {
    "STRONG_BUY":  "Very Strong Signal",
    "BUY":         "Strong Signal",
    "STRONG_HOLD": "Stable Signal",
    "HOLD":        "Neutral Signal",
    "WEAK_HOLD":   "Soft Signal",
    "SELL":        "Bearish Signal",
    "STRONG_SELL": "Strong Bearish Signal",
}

EXPECTED_SHORT = {
    "STRONG_BUY":  "Very Strong",
    "BUY":         "Strong",
    "STRONG_HOLD": "Stable",
    "HOLD":        "Neutral",
    "WEAK_HOLD":   "Soft",
    "SELL":        "Bearish",
    "STRONG_SELL": "Very Bearish",
}


def test_signal_tiers_has_all_keys():
    """SIGNAL_TIERS must contain all 7 rating keys."""
    missing = set(ALL_TIERS) - set(SIGNAL_TIERS.keys())
    assert not missing, f"SIGNAL_TIERS is missing: {missing}"


def test_signal_tiers_required_sub_keys():
    """Each tier entry must have label, short, colour, and min_score."""
    required = {"label", "short", "colour", "min_score"}
    for tier, data in SIGNAL_TIERS.items():
        missing = required - set(data.keys())
        assert not missing, f"SIGNAL_TIERS['{tier}'] missing sub-keys: {missing}"


@pytest.mark.parametrize("rating,expected", EXPECTED_LABELS.items())
def test_tier_label_values(rating, expected):
    """tier_label() must return the canonical descriptive label for each tier."""
    assert tier_label(rating) == expected, \
        f"tier_label('{rating}') = '{tier_label(rating)}' — expected '{expected}'"


@pytest.mark.parametrize("rating,expected", EXPECTED_SHORT.items())
def test_tier_short_values(rating, expected):
    """tier_short() must return the canonical short label for each tier."""
    assert tier_short(rating) == expected, \
        f"tier_short('{rating}') = '{tier_short(rating)}' — expected '{expected}'"


def test_tier_label_unknown_falls_back():
    """tier_label() on an unknown key must return the key itself, not raise."""
    assert tier_label("UNKNOWN_TIER") == "UNKNOWN_TIER"


def test_tier_short_unknown_falls_back():
    """tier_short() on an unknown key must return the key itself, not raise."""
    assert tier_short("UNKNOWN_TIER") == "UNKNOWN_TIER"


def test_tier_colour_all_tiers():
    """tier_colour() must return a non-empty string for each tier."""
    for rating in ALL_TIERS:
        c = tier_colour(rating)
        assert c and isinstance(c, str), f"tier_colour('{rating}') returned '{c}'"


def test_templates_contain_no_directive_buy_sell_labels():
    """
    P1.2 absence test: templates must not contain old directive Buy/Sell display labels.
    Excludes FinViz analyst scale labels (legitimate external references).
    Excludes internal value= attributes and Python constants.
    """
    # Patterns that must not appear in user-facing display text
    banned_patterns = [
        "Strong Buy",
        "Strong Sell",
        "Weak Hold",
        "Strong Hold",
    ]
    # Lines that are permitted to contain these patterns
    allowed_substrings = [
        'value=',        # checkbox value attributes (internal constants)
        'FinViz',        # FinViz analyst scale labels
        'analyst',       # analyst recommendation context
        '==',            # Python comparisons
        "data-rating=",  # internal data attributes
        "rating-STRONG", # CSS class names
        "1=Strong Buy",           # FinViz analyst scale legend (ticker.html)
        "Scale:",                  # FinViz analyst scale legend (ticker.html)
        "['','Strong Buy'",        # FinViz analyst scale JS array (ticker.html:833)
    ]

    violations = []
    for fname in os.listdir(TEMPLATE_DIR):
        if not fname.endswith(".html"):
            continue
        fpath = os.path.join(TEMPLATE_DIR, fname)
        with open(fpath) as f:
            for lineno, line in enumerate(f, 1):
                for pattern in banned_patterns:
                    if pattern in line:
                        if not any(allowed in line for allowed in allowed_substrings):
                            violations.append(f"{fname}:{lineno}: {line.rstrip()}")

    assert not violations, (
        f"Old directive language found in templates ({len(violations)} hits):\n"
        + "\n".join(violations[:15])
    )


def test_theme_labels_are_descriptive():
    """P13/P14: theme labels must not use old directive language."""
    from config.themes import THEMES
    banned = ["Strong Buy", "Buy the Dip", "Insider Buying Surge"]
    for theme in THEMES:
        for phrase in banned:
            assert phrase not in theme["label"], \
                f"Theme '{theme['id']}' still has directive label: '{theme['label']}'"


def test_nav_uses_signal_tiers_label():
    """_nav.html must say 'Signal Tiers', not the old 'Rating Tiers'."""
    nav_path = os.path.join(TEMPLATE_DIR, "_nav.html")
    with open(nav_path) as f:
        content = f.read()
    assert "Rating Tiers" not in content, "_nav.html still says 'Rating Tiers'"
    assert "Signal Tiers" in content, "_nav.html does not say 'Signal Tiers'"
