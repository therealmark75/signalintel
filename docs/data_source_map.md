# SignalIntel Data-Source Map: 100+ Sources, Ranked for a Single-Developer Flask+SQLite Stack

## TL;DR
- The four highest-value, lowest-friction NEW composite-score components to build next, ranked by signal-per-unit-of-engineering-effort, are: **(1) Analyst-Revision component** (Finnhub `/stock/recommendation` + FMP price-target endpoints — free; Womack 1996 documented a −9.1% six-month drift on sell recommendations); **(2) Earnings-Surprise / PEAD component** (Finnhub `/stock/earnings` + FMP estimates — free; Bernard & Thomas 1989 ~18% annualized SUE-decile spread); **(3) Short-Interest / Squeeze component** (FINRA's free `api.finra.org` daily Reg-SHO + bi-monthly Equity Short Interest feeds; Boehmer/Jones/Zhang 2008 documented 1.16% underperformance over 20 trading days, ~15.6% annualized); and **(4) 13F Institutional-Flow component** (free SEC EDGAR XML parsed in-house via `edgartools`). Each is JSON/REST, free or near-free, and has peer-reviewed predictive evidence.
- Drop **congressional trading** and **ESG** from the composite score and keep them as dashboard surfaces only. The famous Ziobrowski et al. 2004 12%/yr Senate alpha was directly contradicted by Eggers & Hainmueller's "Capitol Losses" (*Journal of Politics* 75(2): 535–551, 2013), which found that "the average congressional portfolio underperformed a passive index fund by 2–3% per year (before expenses)." ESG risk-adjusted returns are explicitly ambiguous per Pedersen, Fitzgibbons & Pomorski 2021 (*JFE* 142(2)). Keep all social/sentiment feeds (Stocktwits, Reddit/ApeWisdom, Google Trends, news-tone) as a STANDALONE "Crowd" dashboard panel — Kmak et al. 2025 (arXiv:2507.22922) showed that "social media sentiment has only a weak correlation with stock prices" and that comment volume and Google search trends predict better than sentiment scoring itself. Blending these into the composite would dilute factor purity.
- Your current FMP + Finnhub + SEC EDGAR + FINRA + FRED stack already covers ~80% of the data needed for 6 new components without paying a cent above $19–$30/mo. Defer Polygon, Unusual Whales, Quiver and Ortex paid tiers until SignalIntel is on paid SaaS plans — they are nice-to-have for the Elite tier dashboards, not gating.

## Key Findings

### Source-landscape summary (~110 sources catalogued across 7 categories)
1. **Fundamental/market APIs (15)** — FMP, Alpha Vantage, Polygon.io, Finnhub, Tiingo, EOD Historical Data (EODHD), Intrinio, Twelve Data, Marketstack, Quandl/Nasdaq Data Link, IEX Cloud (shut down Aug 31 2024), SEC EDGAR data.sec.gov APIs, FINRA Query API, FRED API, BLS API, Xignite, Alpaca Data, yfinance (unofficial Yahoo).
2. **Sentiment / Social (15)** — Stocktwits public `streams/symbol/{TICKER}.json` endpoint, Stocktwits Sentiment API v2 (partner-only Swagger), Reddit official API + PRAW, ApeWisdom (`apewisdom.io/api/v1.0/`), Tradestie WallStreetBets API, Pushshift (now access-restricted), Twitter/X API (now pay-per-use), StockGeist, Sprinklr, RavenPack, AlphaSense, Accern, Finnhub `/news-sentiment` and `/stock/social-sentiment`, Google Trends (pytrends scraper), 4chan /biz/ via ApeWisdom.
3. **News & RSS (18)** — Benzinga (basic free tier + paid Cloud), Benzinga free RSS, Seeking Alpha RSS, MarketWatch RSS, Yahoo Finance RSS (`finance.yahoo.com/rss/headline?s=AAPL`), Reuters, CNBC RSS, Bloomberg (no public API), Finviz news scrape, SEC EDGAR latest-filings RSS feeds, PR Newswire, Business Wire, GlobeNewswire, AccessWire, NewsAPI.org, Marketaux, GDELT, AlphaVantage NEWS_SENTIMENT endpoint.
4. **Short / options / alt (16)** — FINRA Equity Short Interest API (free), Ortex (~$80–$140/mo retail), S3 Partners (institutional, custom), Unusual Whales ($50/mo as of May 2025 — see Caveats), CBOE DataShop, Cheddar Flow, BlackBoxStocks, Quiver Quantitative API ($30/mo Hobbyist, $75/mo Trader), Capitol Trades (scrape), House/Senate STOCK Act PTR scrapers, OpenInsider scrape, USAspending.gov (lobbying/contracts), Patent USPTO public bulk data, Google Patents BigQuery, BLS API.
5. **Analyst ratings (8)** — Finnhub `/stock/recommendation` (free, 60/min), FMP price-target & grades endpoints, Tipranks (scrape), Benzinga Analyst Insights API, Zacks (paid), Refinitiv I/B/E/S (institutional), Nasdaq Data Link Analyst Ratings & Price Targets (ARPT), MarketScreener consensus scrape.
6. **Academic / canonical research (11 papers)** — Jegadeesh & Titman 1993 momentum, Fama-French 1993/2015, Novy-Marx 2013 gross profitability (0.61% monthly FF3 alpha, t=5.62), Frazzini & Pedersen 2014 betting-against-beta, Bernard & Thomas 1989 PEAD (~18% annualized), Boehmer/Jones/Zhang 2008 short interest (1.16%/20 days = 15.6% annualized), Cohen/Malloy/Pomorski 2012 opportunistic insiders (9.8%/yr value-weighted, 21.6%/yr equal-weight, t=6.07), Womack 1996 analyst revisions (−9.1% sell-rec drift), Xing/Zhang/Zhao 2010 option volatility smirk (10.9%/yr), Ziobrowski 2004 vs Eggers & Hainmueller 2013 on congressional trading, Pedersen/Fitzgibbons/Pomorski 2021 ESG-efficient frontier.
7. **FinTwit / reference accounts (~20)** — to be tracked but not mechanically ingested.

### Verdict on the existing engine (v0.14.0)
Momentum (0.35) + Quality (0.30) + Insider (0.25) + Reversion (0.10) + Volume (0.10) is a sensible Fama-French-plus-Jegadeesh skeleton. The blind spots are: no analyst-revision factor (cheap to add), no earnings-surprise factor (cheapest to add), no short-interest factor (free FINRA data), no institutional-flow factor (free EDGAR 13F), and no low-volatility/beta factor (computable from any price feed you already have). All five of those have stronger peer-reviewed evidence than the typical sentiment factor.

## Details

### 1. INSTITUTIONAL / FUNDAMENTAL DATA APIs & FEEDS

| Provider | Free tier | Paid entry | Auth | Format | Notes for SignalIntel |
|---|---|---|---|---|---|
| **FMP** (already integrated) | 250 req/day | $19/mo Starter, $69/mo Premium | API key in URL | JSON REST | Strongest free-tier fundamentals depth — keep as primary fundamentals source |
| **Alpha Vantage** | 25 req/day, 5/min | $49.99/mo (75/min) → up to $249/mo (1200/min) | API key | JSON/CSV | Free tier too tight for 11k tickers; only useful for `NEWS_SENTIMENT` endpoint and macro |
| **Polygon.io** | "Basic" free, 5/min, EOD only | $29/mo Starter (unlimited calls, 15-min delayed, 5yr history), $79/mo Developer (real-time) | API key | JSON REST + WebSocket | Best for minute bars/real-time — overkill for daily SignalIntel; reconsider when you add intraday |
| **Finnhub** | **60 req/min**, US real-time quotes, WebSocket on 50 symbols | $50/mo+ | Token (query or header) | JSON REST + WS | **Best free tier on the market.** Endpoints needed: `/stock/recommendation`, `/stock/earnings`, `/stock/social-sentiment`, `/stock/insider-transactions`, `/news-sentiment`, `/calendar/earnings`. Add this **today**. |
| **Tiingo** | Free Starter (limited daily price data, no news/fundamentals) | $10–$50/mo individual | Token | JSON REST + WS | Good price-data fallback; news/fundamentals are paid add-ons |
| **EODHD** | ~20 req/day | $19.99/mo entry | API key | JSON/CSV | All-in-one (fundamentals+news+global), reasonable alternative to FMP |
| **Intrinio** | None (free trial) | ~$1,500/mo+ enterprise | API key + OAuth | JSON REST | Skip — institutional pricing |
| **Twelve Data** | 800 req/day, 8/min | $29/mo Grow → $329/mo Ultra | API key | JSON REST + WS | Solid backup; broad asset coverage |
| **Marketstack** | 1,000 req/mo | $9.99/mo | API key | JSON REST | Cheap EOD-only fallback |
| **Quandl / Nasdaq Data Link** | Many free datasets | Per-dataset paid | API key | JSON/CSV | Useful for the Analyst Ratings & Price Targets database (ARPT) and Sharadar-style fundamentals |
| **SEC EDGAR data.sec.gov** | **Fully free**, 10 req/sec rate limit (must set User-Agent) | n/a | None (UA required) | JSON + XBRL | Already integrated for legal feeds. Extend to: company facts, 13F-HR, Form 4 ownership, 8-K item parsing. |
| **FINRA Query API** | **Fully free**, public POST endpoint | n/a | None | JSON/CSV | `api.finra.org/data/group/otcMarket/name/regShoDaily` for daily short volume; `EquityShortInterest` for bi-monthly settlement reports |
| **FRED API (St Louis Fed)** | **Fully free**, 32-char API key | n/a | API key | JSON/XML | 800k+ macro time series — needed for sector-regime overlays |
| **BLS API** | Free key required, 500 queries/day | n/a | API key | JSON | CPI/unemployment for macro overlay |
| **Yahoo Finance / yfinance** | Free unofficial scraping | n/a | None | JSON (private) | The pipeline you're already building — keep as price/dividend fallback, but it breaks frequently |
| **IEX Cloud** | **Discontinued Aug 31, 2024** — do not architect around it. |

### 2. SENTIMENT & SOCIAL DATA SOURCES — STANDALONE DASHBOARD ONLY

- **Stocktwits**: Public, undocumented JSON endpoint `https://api.stocktwits.com/api/2/streams/symbol/{TICKER}.json` returns last ~30 messages with `entities.sentiment.basic` ("Bullish"/"Bearish") tags. Unofficial; rate-limit ~200 req/hr per IP empirically. A Sentiment API v2 (`sentiment-v2-api.stocktwits.com`) exists but requires partner approval.
- **Reddit official API**: Free for personal use under 100 queries/minute/OAuth client, BUT commercial/large-scale use was paywalled in mid-2023 at exactly **$0.24 per 1,000 API calls** for apps exceeding 100 queries/minute (per Reddit's June 2023 announcement). Commercial access also requires Reddit approval. Use PRAW with your own client_id/client_secret for r/wallstreetbets, r/stocks, r/investing, r/options as long as you stay below the 100 QPM threshold.
- **Pushshift**: Now access-restricted to Reddit moderators only — do not rely on it.
- **ApeWisdom**: `apewisdom.io/api/v1.0/filter/wallstreetbets` returns ranked mention counts per ticker, paginated 100/page. Free, no key. Great drop-in for a "Reddit buzz" dashboard tile.
- **Tradestie WallStreetBets**: Free, returns per-ticker bullish/bearish + comment counts updated every 15 min.
- **Google Trends**: No official API. `pytrends` library scrapes the public web app; rate-limited (Google will 429 after ~10 rapid queries) — use 60–90s delays. Quiver also resells Google Trends per-company "trend score".
- **Twitter/X**: In early 2026 X discontinued its subscription tiers and switched to **pay-per-use pricing** ($0.005 per post read, $0.01 per post created for new developers). Legacy Basic ($200/mo) and Pro ($5,000/mo) remain only for pre-Feb-2026 subscribers. Practically: pay-per-use is more flexible than the old $100→$200/mo Basic, but still expensive at SignalIntel's likely read volumes. Plan as: dashboard-only ingest of a curated FinTwit watchlist (~50 accounts), not firehose.
- **Finnhub social-sentiment & news-sentiment endpoints**: Already free under the 60/min plan — uses Reddit and Twitter aggregated, pre-scored. This is the easiest way to get a sentiment tile in.
- **News-sentiment APIs**: Alpha Vantage `NEWS_SENTIMENT` (25 req/day free), Marketaux ($0 → $9.99/mo for 100/day), GDELT (free, academic), StockGeist, RavenPack/Accern (enterprise).

### 3. NEWS & RSS FEEDS

| Source | Free RSS? | API option | Endpoint |
|---|---|---|---|
| **SEC EDGAR latest filings** | ✅ Atom feed | data.sec.gov JSON | `sec.gov/cgi-bin/browse-edgar?action=getcurrent&type=8-K&output=atom` |
| **Benzinga free RSS** | ✅ headline-only | "Basic News API" free tier on AWS Marketplace (headline + teaser + link only); paid Cloud APIs deliver embeddable body, TCP push, 130–160 full articles/day plus 600–900 real-time headlines/day | benzinga.com/feed |
| **Yahoo Finance RSS** | ✅ Per-ticker | n/a | `finance.yahoo.com/rss/headline?s=AAPL` |
| **MarketWatch** | ✅ Topic feeds | n/a | `feeds.content.dowjones.io/public/rss/mw_topstories` |
| **Seeking Alpha** | ✅ Per-ticker RSS | Paid API via PRO | `seekingalpha.com/api/sa/combined/AAPL.xml` |
| **CNBC** | ✅ | n/a | Multiple topic feeds |
| **Reuters** | Partial RSS still works | Refinitiv API (enterprise) | various |
| **Bloomberg** | ❌ No public RSS | Enterprise BPIPE only | — |
| **Finviz** | News page is scrapable HTML | n/a | finviz.com/news.ashx |
| **PR Newswire / Business Wire / GlobeNewswire** | ✅ All publish RSS | Paid newsroom APIs | prnewswire.com/rss/ |
| **AlphaVantage NEWS_SENTIMENT** | 25/day free | $49.99/mo+ | `function=NEWS_SENTIMENT&tickers=AAPL` |
| **Marketaux** | 100/day free trial | $9.99/mo+ | api.marketaux.com |
| **GDELT** | Free | n/a | gdeltproject.org |
| **NewsAPI.org** | 100/day dev key | $449/mo commercial | newsapi.org |

### 4. SHORT INTEREST, OPTIONS FLOW & ALTERNATIVE DATA

- **FINRA Equity Short Interest**: Free POST to `api.finra.org/data/group/otcMarket/name/EquityShortInterest` filtered by `settlementDate`. Bi-monthly (settlement dates twice a month per FINRA Rule 4560). Also `regShoDaily` for daily short-sale volume. JSON or CSV. **This is the foundation of your Short-Interest component.**
- **Ortex**: Aggregates global exchange short data + estimated cost-to-borrow + estimated SI from securities-lending feeds. Retail plans ~$80–$140/mo. No free tier. Justifiable only on Pro/Elite SaaS tiers.
- **S3 Partners "Black App"**: Institutional, custom pricing, not appropriate.
- **Unusual Whales**: Retail platform subscription **$50/month** as of the May 2025 price increase (was $48/mo prior; +$25–$50 per API tier announced via the company's X account in May 2025). The developer API exposes options flow, dark pool, GEX, congressional, short interest, prediction markets via REST + WebSocket (WS requires the API Advanced add-on). Historical full-market options trades sold separately at $250/mo. OpenAPI spec at `api.unusualwhales.com/api/openapi`. Kafka and MCP server access available alongside REST/WS.
- **Quiver Quantitative API**: Hobbyist **$30/mo or $300/yr** (Tier 1: Congress, insiders, lobbying, contracts, patents, WSB, Google Trends, corporate flights); Trader **$75/mo or $750/yr** (Tier 1 + 2 datasets); Commercial custom. Python wrapper `pip install quiverquant`. Endpoints: `congress_trading()`, `insiders()`, `sec13F()`, `top_shareholders()`, `lobbying()`, `executive_compensation()`, `news()`. Free web dashboards exist for spot-checking but no programmatic free tier.
- **Capitol Trades** (capitoltrades.com): Free site, scrapable, no official API. Backed by 2iQ. Alternative to Quiver for congressional disclosures.
- **OpenInsider** (openinsider.com): Free, scrape-friendly, mirrors Form 4 with cluster-buy filters. Excellent free augment to SEC Form 4 ingestion you presumably already have.
- **House/Senate PTR filings**: Direct PDF disclosures; community scrapers on GitHub (e.g., `senate-stock-watcher`, `house-stock-watcher`) publish parsed JSON daily on GitHub Pages — free.
- **CBOE DataShop, Cheddar Flow, BlackBoxStocks**: Paid options flow vendors; skip for v1.
- **USAspending.gov**: Free API for federal contract awards (alt-signal for defense/infra names).
- **Google Patents / USPTO Bulk Data**: Free, large download; not low-friction.
- **NOAA / satellite alt-data**: Free public sets but require domain modelling — out of scope.

### 5. ANALYST RATINGS & PRICE TARGETS

- **Finnhub** `/stock/recommendation` — free, returns buy/hold/sell/strong-buy/strong-sell counts per month per ticker. `/stock/price-target` and `/stock/upgrade-downgrade` are on the same free tier. **This is the easiest way to build an Analyst-Revision component today.**
- **FMP** Analyst Estimates & Targets endpoints (price-target-consensus, price-target-summary, ratings-snapshot, grades-summary, historical-grades). Already integrated. Use for back-tested revision signals.
- **Benzinga Analyst Insights API** — paid Cloud tier; rich PT-drift fields.
- **Nasdaq Data Link "Analyst Ratings & Price Targets"** (ARPT) — paid subscription database, professionally curated.
- **Tipranks** — scrape only, anti-bot.
- **Zacks**, **Refinitiv I/B/E/S** — institutional.

### 6. ACADEMIC & ACCREDITED RESEARCH — Which new factors actually have predictive evidence?

For each candidate new factor, the canonical paper, the verbatim alpha number, and a recommendation.

| Factor | Citation | Verbatim finding | Recommendation |
|---|---|---|---|
| **Momentum** (already have) | Jegadeesh & Titman 1993 *JF*; updated 2001 NBER w7159 | Buying winners / selling losers earns ~1%/month; "momentum profits have continued in the 1990s, suggesting that the original results were not a product of data snooping bias" | Keep weight 0.35 |
| **Quality / Profitability** (already have) | Novy-Marx 2013, *JFE* 108(1) | "Profitability, measured by gross profits-to-assets, has roughly the same power as book-to-market predicting the cross-section of average returns" — FF3 alpha 0.61%/mo, t=5.62 | Keep weight 0.30 |
| **Insider** (already have) | Cohen, Malloy & Pomorski 2012, *JF* 67(3) | Opportunistic-trader portfolio earns "value-weighted abnormal returns of 82 basis points per month…180 basis points per month equal-weight (t=6.07)" — 9.8%/yr value-weight, 21.6%/yr equal-weight | Distinguish routine vs opportunistic insiders (subtract the routine cohort) |
| **Short Interest** | Boehmer, Jones & Zhang 2008, *JF* 63(2) | "Heavily shorted stocks underperform lightly shorted stocks by a risk-adjusted average of 1.16% over the following 20 trading days (15.6% annualized). Institutional nonprogram short sales are the most informative; stocks heavily shorted by institutions underperform by 1.43% the next month (19.6% annualized)." | **BUILD — high priority** |
| **PEAD / Earnings Surprise** | Bernard & Thomas 1989, *J. Accounting Research* 27 | Top vs bottom SUE decile hedge produces ~4.2% in 60-day CAR / ~18% annualized; investors "fail to recognize fully the implications of current earnings for future earnings" | **BUILD — highest priority (cheapest)** |
| **Analyst Revisions** | Womack 1996, *JF* 51(1) | "For buy recommendations, the mean postevent drift is modest (+2.4%) and short-lived, but for sell recommendations, the drift is larger (−9.1%) and extends for six months" — 3-day announcement window +3.0% upgrades / −4.7% downgrades | **BUILD — easy, free data** |
| **Low Volatility / BAB** | Frazzini & Pedersen 2014, *JFE* 111(1) | US BAB Sharpe ratio ~0.78; "broad evidence that the relative flatness of the security market line is not isolated to the U.S. stock market but that it is a pervasive global phenomenon" | Trivial to compute from existing price feed |
| **Option Skew / Smirk** | Xing, Zhang & Zhao 2010, *JFQA* 45(3) | "Stocks exhibiting the steepest smirks in their traded options underperform stocks with the least pronounced volatility smirks in their options by 10.9% per year on a risk-adjusted basis" | Defer — needs options chain data |
| **Congressional Trading** | Ziobrowski 2004, *JFQA* 39(4) vs Eggers & Hainmueller 2013, *Journal of Politics* 75(2): 535–551 | Ziobrowski found Senators beat the market by ~12%/yr 1993–98; Eggers & Hainmueller (2013): "in neither period do members of Congress trade with an information advantage…The average congressional portfolio underperformed a passive index fund by 2–3% per year (before expenses)" | **Dashboard only — do not feed composite** |
| **ESG** | Friede/Busch/Bassen 2015 *JSF&I* vs Pedersen/Fitzgibbons/Pomorski 2021, *JFE* 142(2) | Friede et al.: "Roughly 90% of studies find a nonnegative ESG–CFP relation" (corporate performance, not stock returns); Pedersen et al. show risk-adjusted equity returns are ambiguous depending on investor composition | **Dashboard only — do not feed composite** |
| **Social Sentiment** | Kmak et al. 2025 (arXiv 2507.22922) | "Social media sentiment has only a weak correlation with stock prices…simpler metrics, such as the volume of comments and Google search trends, exhibit stronger predictive signals" | **Dashboard only — do not feed composite** |

### 7. FINTWIT / REFERENCE ACCOUNTS — For UX inspiration only

These are widely-followed reference voices; ingestion is impractical at single-dev scale given X's pay-per-use pricing, but you should mirror their *style* of presentation:
- **Newswire/flow**: @unusual_whales, @zerohedge, @DeItaone (Walter Bloomberg), @FirstSquawk, @LiveSquawk
- **Macro/markets**: @JackFarley96, @LizAnnSonders, @SoberLook, @MichaelKantro, @hmeisler
- **Research aggregators**: @ttmygh (Kuppy), @LongShortReport, @MorningBrew, @Quartr_App
- **Reference sites**: ZeroHedge, Hedgeye, AlphaArchitect, Quantpedia, Verdad Capital research, Bespoke Investment Group, ISI Evercore (paywalled)

These should populate a "Curated Voices" sidebar with manually maintained handles rather than ingested signals.

---

## INGESTION-FEASIBILITY RANKING (Top picks for the next 90 days)

Scoring each candidate as **Effort (E, 1=trivial→5=hard) / Signal-Per-Effort (S, 1→5)**:

| New component | Best free source | Effort | Signal/effort | Build order |
|---|---|---|---|---|
| **Earnings-Surprise / PEAD** | Finnhub `/stock/earnings` + FMP `/historical-earning-calendar` | 1 | 5 | **1st** |
| **Analyst-Revision** | Finnhub `/stock/recommendation` + FMP `/historical-grades` | 1 | 5 | **2nd** |
| **Short-Interest / Squeeze** | FINRA `EquityShortInterest` POST API | 2 | 5 | **3rd** |
| **Institutional-Flow (13F Δ)** | SEC EDGAR 13F-HR XML, parsed with `edgartools` or your own | 3 | 4 | **4th** |
| **Low-Volatility / Beta** | Compute from existing FMP/Yahoo price feed | 1 | 3 | **5th** |
| **Options-Skew (deferred)** | Polygon.io paid or Unusual Whales API | 4 | 3 | Defer to Elite tier |
| **News-Event** | SEC EDGAR 8-K RSS + Benzinga RSS (free tier) | 2 | 3 | After (1–5) |

### Dashboard-only surfaces (do NOT feed composite)
- **Sentiment panel**: Finnhub `/stock/social-sentiment`, Stocktwits Bull/Bear streams, ApeWisdom WSB rankings, Google Trends via pytrends, news-tone from Alpha Vantage NEWS_SENTIMENT.
- **Congressional Trades panel**: Quiver Hobbyist API ($30/mo, optional) or scraped Capitol Trades / house-stock-watcher GitHub.
- **ESG panel**: Finnhub `/stock/esg` if available, or FMP ESG endpoint.
- **Options-Flow alert tile**: Unusual Whales for Elite-tier subscribers only.

---

## Recommendations

### Stage 1 (next 2 weeks) — free, no architectural change
1. **Add Finnhub API key** to your secrets manager. 60 req/min is enough to cycle 11k tickers every ~3 hours. Use it for analyst revisions, social sentiment (sidebar only), earnings calendar, and insider transactions.
2. **Build the Earnings-Surprise component** (SUE-style: actual − consensus, normalised by historical surprise std-dev). Allocate provisional weight ~0.10 in the composite, normalised. Backtest before promoting.
3. **Build the Analyst-Revision component**: count of upgrades − downgrades over 90 days, plus PT-change %. Provisional weight ~0.10.

### Stage 2 (weeks 3–6)
4. **Build the Short-Interest component** off the free FINRA bi-monthly + daily Reg-SHO feeds. Compute days-to-cover, SI/float, and SI %-change. Provisional weight ~0.10.
5. **Re-normalise** the composite. Suggested new weight vector: momentum 0.25 / quality 0.20 / insider 0.15 / earnings-surprise 0.10 / analyst-revisions 0.10 / short-interest 0.10 / reversion 0.05 / volume 0.05 — then sector-strength multiplier ±7.5% and legal penalty unchanged.

### Stage 3 (weeks 7–12)
6. **Build the 13F-Flow component** from SEC EDGAR. Compute quarter-over-quarter Δ in number of 13F filers reporting a position and Δ in shares held by the top-20 funds. Provisional weight ~0.05–0.10.
7. **Wire up the Sentiment dashboard** as a standalone Flask blueprint, sourced from Finnhub social-sentiment + Stocktwits + ApeWisdom. Display, but **do not blend into composite**.
8. **Add FRED-based sector-regime overlay** (yield-curve slope, credit spreads) to sharpen the existing sector multiplier.

### Stage 4 (when SaaS revenue justifies)
9. Subscribe to Quiver Hobbyist ($30/mo) for congressional + lobbying + government-contracts dashboards on Pro/Elite tiers.
10. Subscribe to Unusual Whales ($50/mo retail; API Advanced add-on if WebSocket streaming needed) and surface options flow + dark-pool tiles on Elite tier only.
11. Consider Ortex (~$80–$140/mo) for institutional-grade short metrics if user demand for the short-squeeze tile justifies it.

### Threshold benchmarks that would change these recommendations
- If your earnings-surprise component fails to deliver positive IC (information coefficient > 0.02) in a 3-year backtest, demote it before launch.
- If Finnhub rate limits become binding (>30 rate-limit-hits/day in logs), upgrade to their $50/mo plan before adding more components.
- If Polygon launches a cheaper fundamentals tier or if FMP raises prices >50%, re-evaluate the primary fundamentals source.
- If your paid-subscriber base exceeds 200 Pro users, the math for buying Unusual Whales/Quiver/Ortex flips clearly in favour.
- If X's pay-per-use pricing makes a curated 50-account FinTwit feed cost less than $50/mo at your read volume, escalate Twitter ingestion from sidebar-only to a real-time tile.

---

## Caveats

- **IEX Cloud is dead** (August 31, 2024). Any older guide recommending IEX should be discarded. Tiingo still exposes an IEX-branded real-time feed that does work, but it is no longer IEX-the-company's product.
- **Reddit and Twitter/X API terms shifted hard in 2023 and again in early 2026.** Reddit's paid tier is exactly $0.24 per 1,000 API calls for apps over 100 QPM (June 2023 announcement) and requires Reddit approval. X discontinued its old $200/mo Basic and $5,000/mo Pro subscription tiers in early 2026 and moved to pay-per-use ($0.005/post read, $0.01/post created) for new developers — legacy subscribers keep their plans. Any architecture that depends on free Twitter/Reddit firehose access is fragile.
- **Stocktwits public endpoints are undocumented** and not explicitly permitted in their TOS as programmatic access. Treat them as best-effort.
- **Congressional trading alpha is sample-dependent and contested.** The famous ~12%/yr Ziobrowski 2004 Senate result for 1993–1998 was directly contradicted by Eggers & Hainmueller 2013 on 2004–2008 data ("underperformed a passive index fund by 2–3% per year"). Use it as a dashboard novelty tile, not a factor.
- **Social-sentiment predictive power is weak in recent literature.** Kmak et al. 2025 (arXiv:2507.22922, July 2025 submission — note: the arXiv ID 2507.xxxxx encodes July 2025, not 2024) explicitly find that for r/wallstreetbets-style data, comment volume and Google search trends predict prices better than sentiment scoring does. Your decision to keep sentiment out of the composite is academically defensible.
- **PEAD numbers cited from Bernard & Thomas 1989 are the standard textbook restatements of the canonical ~18% annualized SUE-spread result**; the original *Journal of Accounting Research* paper is paywalled and exact verbatim numerical sentences are not freely indexed. Confirm the wording from the JAR PDF before quoting it in any customer-facing whitepaper.
- **All pricing listed here is as of May 2026 and changes frequently** — Unusual Whales raised API tier prices by $25–$50 in May 2025 (retail moved to $50/mo); X overhauled pricing in early 2026; Reddit's pricing dates from 2023 and may have been revised. Re-verify before signing annual contracts.
- **FMP, Finnhub, and the SEC all rate-limit by IP/key and require User-Agent strings.** SEC requires `User-Agent: AppName Contact-Email` and enforces 10 req/sec. Build retry-with-exponential-backoff into your Flask jobs before going live.
- **The 13F dataset is delayed by 45 days** — it is a slow-moving factor, useful for QoQ position changes, not for tactical signals.
- **Sample-size and overfitting risk:** When you stack 7+ factors in a composite, the risk of in-sample overfitting rises rapidly. Hold out a true out-of-sample window (e.g., last 18 months) and only promote a new component to the composite if its out-of-sample IC is positive and its incremental contribution to portfolio Sharpe is positive.