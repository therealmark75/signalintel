# scrapers/calendar_scraper.py
# ─────────────────────────────────────────────────
# Phase 3: Economic calendar scraper.
# Pulls upcoming high-impact events from FinViz,
# flags which sectors/tickers are affected.
# ─────────────────────────────────────────────────

import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://finviz.com/",
}

def get_earnings_calendar(days_ahead: int = 7) -> list[dict]:
    """
    Scrape upcoming earnings from FinViz earnings calendar.
    Returns list of {ticker, company, date, time (before/after market)}
    """
    url = "https://finviz.com/calendar.ashx?v=3"
    earnings = []

    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue
                ticker = cells[0].get_text(strip=True)
                if not ticker or len(ticker) > 6:
                    continue
                earnings.append({
                    "ticker":  ticker,
                    "company": cells[1].get_text(strip=True) if len(cells) > 1 else "",
                    "date":    cells[2].get_text(strip=True) if len(cells) > 2 else "",
                    "timing":  cells[3].get_text(strip=True) if len(cells) > 3 else "",
                })

    except Exception as e:
        logger.warning(f"Earnings calendar scrape failed: {e}")

    return earnings


def flag_tickers_near_events(
    tickers: list[str],
    events:  list[dict],
    earnings:list[dict],
) -> dict[str, list[str]]:
    """
    For each ticker, return list of upcoming event warnings.
    Used to add context to signal output.
    """
    warnings = {}
    earnings_tickers = {e["ticker"]: e for e in earnings}

    for ticker in tickers:
        ticker_warnings = []

        # Check earnings
        if ticker in earnings_tickers:
            e = earnings_tickers[ticker]
            ticker_warnings.append(
                f"⚡ Earnings {e.get('date','')} {e.get('timing','')}"
            )

        warnings[ticker] = ticker_warnings

    return warnings
