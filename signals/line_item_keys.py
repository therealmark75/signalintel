"""
Canonical vocabulary layer for financial_statements line item keys.

Raw yfinance strings (PascalCase) are stored verbatim in
financial_statements.line_item_key — no normalisation at write time.
Scorer functions reference this module's constants rather than raw yfinance
strings so that if yfinance renames a field in a future version, only this
file needs updating and no scorer logic changes.

Usage:
    from signals.line_item_keys import INCOME_KEYS, BALANCE_KEYS, CASHFLOW_KEYS
    from signals.line_item_keys import PIOTROSKI_LOOKUPS, ALTMAN_LOOKUPS

    raw_key = INCOME_KEYS["net_income"]   # "NetIncome"
    stmt, raw = PIOTROSKI_LOOKUPS["net_income"]  # ("INCOME", "NetIncome")
"""

# ── Income statement ──────────────────────────────────────────────────────────
# Keys verified against yfinance 1.2.0 AAPL income statement, 2026-05-14.
INCOME_KEYS = {
    "total_revenue":     "TotalRevenue",
    "gross_profit":      "GrossProfit",
    "operating_income":  "OperatingIncome",
    "ebit":              "EBIT",
    "ebitda":            "EBITDA",
    "net_income":        "NetIncome",
    "diluted_eps":       "DilutedEPS",
    "cost_of_revenue":   "CostOfRevenue",
    "sga":               "SellingGeneralAndAdministration",
    "rd_expense":        "ResearchAndDevelopment",
    "pretax_income":     "PretaxIncome",
    "tax_provision":     "TaxProvision",
}

# ── Balance sheet ─────────────────────────────────────────────────────────────
# Keys verified against yfinance 1.2.0 AAPL balance sheet, 2026-05-14.
# Note: common_stock_equity is NOT present in yfinance 1.2.0 output;
#       omitted intentionally to avoid silent key-miss in enrichment queries.
BALANCE_KEYS = {
    "total_assets":          "TotalAssets",
    "total_liabilities":     "TotalLiabilitiesNetMinorityInterest",
    "total_debt":            "TotalDebt",
    "long_term_debt":        "LongTermDebt",
    "current_assets":        "CurrentAssets",
    "current_liabilities":   "CurrentLiabilities",
    "working_capital":       "WorkingCapital",
    "retained_earnings":     "RetainedEarnings",
    "cash_and_equivalents":  "CashAndCashEquivalents",
    "shares_outstanding":    "OrdinarySharesNumber",
    "accounts_receivable":   "AccountsReceivable",
    "inventory":             "Inventory",
    "net_ppe":               "NetPPE",
    "accounts_payable":      "AccountsPayable",
    "net_debt":              "NetDebt",
}

# ── Cash flow statement ───────────────────────────────────────────────────────
# Keys verified against yfinance 1.2.0 AAPL cash flow statement, 2026-05-14.
CASHFLOW_KEYS = {
    "operating_cash_flow": "OperatingCashFlow",
    "free_cash_flow":      "FreeCashFlow",
    "capex":               "CapitalExpenditure",
    "depreciation":        "DepreciationAndAmortization",
    "stock_comp":          "StockBasedCompensation",
    "financing_cash_flow": "FinancingCashFlow",
    "investing_cash_flow": "InvestingCashFlow",
}

# ── Scorer lookup sets ────────────────────────────────────────────────────────
# Each entry: canonical_name -> (statement_type, raw_yfinance_key)
# Used by enrichment map builder in db.py to extract values for scorer functions.

# Piotroski F-Score (9 binary signals) — Phase 2b-ii
PIOTROSKI_LOOKUPS = {
    "net_income":          ("INCOME",   INCOME_KEYS["net_income"]),
    "total_assets":        ("BALANCE",  BALANCE_KEYS["total_assets"]),
    "operating_cash_flow": ("CASHFLOW", CASHFLOW_KEYS["operating_cash_flow"]),
    "long_term_debt":      ("BALANCE",  BALANCE_KEYS["long_term_debt"]),
    "current_assets":      ("BALANCE",  BALANCE_KEYS["current_assets"]),
    "current_liabilities": ("BALANCE",  BALANCE_KEYS["current_liabilities"]),
    "shares_outstanding":  ("BALANCE",  BALANCE_KEYS["shares_outstanding"]),
    "gross_profit":        ("INCOME",   INCOME_KEYS["gross_profit"]),
    "total_revenue":       ("INCOME",   INCOME_KEYS["total_revenue"]),
}

# Altman Z-Score — Phase 2b-ii
# X1 = WorkingCapital / TotalAssets
# X2 = RetainedEarnings / TotalAssets
# X3 = EBIT / TotalAssets
# X4 = MarketCap / TotalLiabilities  (market_cap sourced from ticker_data_rows, not financial_statements)
# X5 = TotalRevenue / TotalAssets
ALTMAN_LOOKUPS = {
    "working_capital":   ("BALANCE",  BALANCE_KEYS["working_capital"]),
    "total_assets":      ("BALANCE",  BALANCE_KEYS["total_assets"]),
    "retained_earnings": ("BALANCE",  BALANCE_KEYS["retained_earnings"]),
    "ebit":              ("INCOME",   INCOME_KEYS["ebit"]),
    "total_liabilities": ("BALANCE",  BALANCE_KEYS["total_liabilities"]),
    "total_revenue":     ("INCOME",   INCOME_KEYS["total_revenue"]),
    # market_cap: from ticker_data_rows["market_cap"], not financial_statements
}
