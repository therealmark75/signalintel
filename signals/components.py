# signals/components.py
"""
Canonical component registry. Single source of truth for:
- signals/scorer.py (which fields exist on TickerSignal)
- database/db.py (insert_signal_scores column list, projection helper)
- web/app.py (allowed_sorts, projection helper consumers, context processor)
- Jinja templates (via context processor)
- web/templates/ticker.html JS (via JSON injection)

Adding a new component = add one entry here + write the scorer function.
Render method bodies (getValue/stripRenderer/chipRenderer) live JS-side,
looked up by key from a JS function table in ticker.html.

Field provenance (Phase 3 Step 1, ported verbatim, not authored):
- The 8 original components (momentum, quality, insider, reversion, volume,
  value, sector, legal): label, tooltip, dot_color, radar_index, in_strip,
  null_overlay from the JS COMPONENTS array in web/templates/ticker.html
  lines 388-480.
- weight: from signals/scorer.py:707-718 (compute_composite default weights).
  Components not in the weighted composite (value, sector, legal, and the
  altman penalty) carry weight 0.0; sector is a multiplicative modifier and
  legal/altman are additive penalties.
- sortable: True for momentum, quality, insider, sector only, matching the
  component columns in web/app.py allowed_sorts (lines 2044-2051).
- surfaces: per the Phase 1 inventory of current per-surface visibility.
  We preserve current visibility, not expand it.
- The 5 v0.17.0 sub-scores (earnings, piotroski, inst_own, analyst_mom,
  altman_penalty): labels and tooltips locked by Athena (Phase 3 Step 1
  final field sheet); they render on no surface today (surfaces=('ticker',),
  in_strip=False, no radar slot).
- value and legal carry db_column='' (no signal_scores column): value is
  computed client-side from target_upside; legal_penalty is sourced from the
  legal_risk table, not signal_scores.
"""

from dataclasses import dataclass
from typing import Optional

VALID_SURFACES = ('ticker', 'screener', 'dashboard', 'watchlist', 'industry', 'signals')


@dataclass(frozen=True)
class Component:
    key: str
    db_column: str
    label: str
    tooltip: str
    weight: float
    surfaces: tuple
    is_penalty: bool = False
    is_modifier: bool = False
    dot_color: Optional[str] = None
    radar_index: Optional[int] = None
    sortable: bool = False
    in_strip: bool = True
    null_overlay: bool = False
    introduced_version: str = '0.9.0'

    def __post_init__(self):
        # Surface validation
        for s in self.surfaces:
            if s not in VALID_SURFACES:
                raise ValueError(f"Component {self.key}: invalid surface {s!r}, valid={VALID_SURFACES}")
        # Penalty/modifier mutual exclusion
        if self.is_penalty and self.is_modifier:
            raise ValueError(f"Component {self.key}: cannot be both penalty and modifier")


COMPONENTS: tuple = (
    Component(
        key='momentum', db_column='momentum_score', label='Momentum',
        tooltip='Measures price trend strength, RSI momentum and moving average signals. High score = strong upward momentum',
        weight=0.35,
        surfaces=('ticker', 'screener', 'dashboard', 'watchlist', 'industry', 'signals'),
        dot_color='#00d4ff', radar_index=0, sortable=True, in_strip=True,
        null_overlay=True, introduced_version='0.9.0',
    ),
    Component(
        key='quality', db_column='quality_score', label='Quality',
        tooltip='Fundamental quality score based on P/E ratio vs sector average, EPS growth and return on equity',
        weight=0.30,
        surfaces=('ticker', 'screener', 'dashboard', 'watchlist', 'industry', 'signals'),
        dot_color='#00ff88', radar_index=1, sortable=True, in_strip=True,
        null_overlay=True, introduced_version='0.9.0',
    ),
    Component(
        key='insider', db_column='insider_score', label='Insider',
        tooltip='Insider activity score based on recent buying and selling by company directors, officers and major shareholders. 100 = strong cluster buying',
        weight=0.25,
        surfaces=('ticker', 'screener', 'dashboard', 'watchlist', 'industry', 'signals'),
        dot_color='#af52de', radar_index=2, sortable=True, in_strip=True,
        null_overlay=True, introduced_version='0.9.0',
    ),
    Component(
        key='reversion', db_column='reversion_score', label='Reversion',
        tooltip='Mean reversion signal. Low score = price has moved far from average and may revert. High = trending strongly',
        weight=0.10,
        # reversion added to dashboard+industry per Step 5.5 carried-response lens:
        # both responses already carry reversion_score (dashboard _thesis() consumes it).
        # Not a visibility expansion, a correction of an under-listing under the old lens.
        surfaces=('ticker', 'screener', 'signals', 'dashboard', 'industry'),
        dot_color='#facc15', radar_index=3, sortable=False, in_strip=True,
        null_overlay=True, introduced_version='0.9.0',
    ),
    Component(
        key='volume', db_column='volume_score', label='Volume',
        tooltip='Volume Confirmation score. High score = strong volume confirming price move. Low = price move on weak or declining volume.',
        weight=0.10,
        surfaces=('ticker',),
        dot_color='#8b5cf6', radar_index=4, sortable=False, in_strip=True,
        null_overlay=True, introduced_version='0.10.0',
    ),
    Component(
        # value has no signal_scores column: computed client-side from target_upside.
        key='value', db_column='', label='Value',
        tooltip='Value score derived from 12-month price target upside. Above 50 = priced below target (upside), below 50 = priced above target (downside).',
        weight=0.0,
        surfaces=('ticker',),
        dot_color='#ff6b35', radar_index=5, sortable=False, in_strip=False,
        null_overlay=False, introduced_version='0.9.0',
    ),
    Component(
        key='sector', db_column='sector_strength_score', label='Sector',
        tooltip='Sector relative strength based on 7-day performance of the sector ETF (XLK for Technology, XLF for Financial, etc). Top-performing sectors boost composite score; lagging sectors apply a drag. Weight: ±7.5% max.',
        weight=0.0, is_modifier=True,
        surfaces=('ticker', 'screener', 'watchlist'),
        dot_color='#fbbf24', radar_index=6, sortable=True, in_strip=False,
        null_overlay=False, introduced_version='0.9.0',
    ),
    Component(
        # legal has no signal_scores column: legal_penalty is sourced from the legal_risk table.
        key='legal', db_column='', label='Legal',
        tooltip='SEC EDGAR legal risk assessment. Penalises composite score for active enforcement actions, investigations or class actions',
        weight=0.0, is_penalty=True,
        surfaces=('ticker',),
        dot_color=None, radar_index=None, sortable=False, in_strip=True,
        null_overlay=False, introduced_version='0.9.0',
    ),
    Component(
        key='earnings', db_column='earnings_score', label='Earnings',
        tooltip='Earnings surprise quality across the last 4 quarters, decay-weighted toward the most recent. 50 = neutral.',
        weight=0.125,
        surfaces=('ticker',),
        dot_color=None, radar_index=None, sortable=False, in_strip=False,
        null_overlay=False, introduced_version='0.13.0',
    ),
    Component(
        key='piotroski', db_column='piotroski_score', label='Piotroski',
        tooltip='Piotroski F-Score: 9 fundamental-health checks mapped to 0-100. 50 = neutral or insufficient history.',
        weight=0.125,
        surfaces=('ticker',),
        dot_color=None, radar_index=None, sortable=False, in_strip=False,
        null_overlay=False, introduced_version='0.13.0',
    ),
    Component(
        key='inst_own', db_column='inst_own_score', label='Institutional',
        tooltip='Institutional ownership from the top-10 holders. 50 = neutral.',
        weight=0.125,
        surfaces=('ticker',),
        dot_color=None, radar_index=None, sortable=False, in_strip=False,
        null_overlay=False, introduced_version='0.13.0',
    ),
    Component(
        key='analyst_mom', db_column='analyst_mom_score', label='Analyst',
        tooltip='Net analyst rating momentum across the last 90 days. 50 = neutral.',
        weight=0.125,
        surfaces=('ticker',),
        dot_color=None, radar_index=None, sortable=False, in_strip=False,
        null_overlay=False, introduced_version='0.13.0',
    ),
    Component(
        key='altman_penalty', db_column='altman_penalty', label='Altman',
        tooltip="Altman Z'' financial distress penalty applied to composite (0, -10, -30, or -60). 0 = no penalty.",
        weight=0.0, is_penalty=True,
        surfaces=('ticker',),
        dot_color=None, radar_index=None, sortable=False, in_strip=False,
        null_overlay=False, introduced_version='0.13.0',
    ),
)


# Accessors

def all_db_columns() -> tuple:
    """Every component db_column, in canonical order. Skips entries with empty db_column (e.g. 'value')."""
    return tuple(c.db_column for c in COMPONENTS if c.db_column)


def components_for_surface(surface: str) -> tuple:
    if surface not in VALID_SURFACES:
        raise ValueError(f"Invalid surface {surface!r}, valid={VALID_SURFACES}")
    return tuple(c for c in COMPONENTS if surface in c.surfaces)


def sortable_columns() -> tuple:
    return tuple(c.db_column for c in COMPONENTS if c.sortable and c.db_column)


def component_by_key(key: str) -> Component:
    for c in COMPONENTS:
        if c.key == key:
            return c
    raise KeyError(f"No component with key={key!r}")


def to_json_dict() -> list:
    """For JSON injection into ticker.html. JS-friendly camelCase."""
    return [{
        'key': c.key,
        'dbColumn': c.db_column,
        'label': c.label,
        'tooltip': c.tooltip,
        'dotColor': c.dot_color,
        'radarIndex': c.radar_index,
        'inStrip': c.in_strip,
        'nullOverlay': c.null_overlay,
        'isPenalty': c.is_penalty,
        'isModifier': c.is_modifier,
        'surfaces': list(c.surfaces),
        'weight': c.weight,
    } for c in COMPONENTS]
