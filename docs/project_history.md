# The Signal Vault: Project History

**From inception to 18 May 2026.**

The journey of building SignalIntel under the Signal Vault parent brand, structured as five distinct phases. Each phase had its own focus, its own constraints, and its own unlock at the end. This is the story of how a personal backtesting script became a multi-product fintech platform.

---

```mermaid
flowchart TD
    Start([Project inception<br/>Personal trading tool]) --> P0

    subgraph P0 [PHASE 0: Foundation, ~April 2026]
        P0A[Flask + SQLite scaffold<br/>Mac Mini, port 5001]
        P0B[FinViz screener scraper<br/>~11,000 US tickers]
        P0C[Initial scoring engine v0.1<br/>basic composite score]
        P0D[7-tier signal taxonomy<br/>Very Strong to Very Bearish]
        P0A --> P0B --> P0C --> P0D
    end

    P0 --> P1

    subgraph P1 [PHASE 1: Core Product Build, late April to early May]
        P1A[Watchlist CRUD<br/>multi-watchlist support]
        P1B[Ticker detail pages<br/>radar, scorecard, signal strip]
        P1C[Global search + keyboard nav]
        P1D[Insider trade tracking<br/>FinViz feed]
        P1E[Rating change history<br/>13,903 rows backfilled]
        P1F[Backtest engine<br/>/backtest page shipped]
        P1G[Telegram alerts<br/>Mark-only at this stage]
        P1A --> P1B --> P1C --> P1D
        P1D --> P1E --> P1F --> P1G
    end

    P1 --> P2

    subgraph P2 [PHASE 2: Scoring Sophistication, 8-12 May]
        P2A[SEC EDGAR legal-risk scraper<br/>Form 4 + 10-K + 8-K monitoring]
        P2B[Legal penalty wired into composite<br/>additive, MINOR to CRIMINAL]
        P2C[Sector strength multiplier<br/>plus or minus 7.5 percent]
        P2D[Reversion Position A NULL handling<br/>per-input neutral contribution]
        P2E[Scoring engine v0.12.0<br/>5 components, normalised]
        P2F[Component registry refactor<br/>array-driven rendering]
        P2G[Schema migration: exchange column<br/>moved to ticker_metadata]
        P2A --> P2B --> P2C
        P2C --> P2D --> P2E
        P2E --> P2F --> P2G
    end

    P2 --> P3

    subgraph P3 [PHASE 2b: Test Suite + Process Discipline, 13-17 May]
        P3A[Pytest harness expanded<br/>206 to 247 tests]
        P3B[P1 to P18 process invariants<br/>documented in scoring_invariants.md]
        P3C[Phase 1 diagnostic + Phase 2 implementation pattern<br/>proven across 4 audits in one day]
        P3D[Schema-coupling tripwire tests<br/>BUG B class catcher]
        P3E[FMP entitlement observability<br/>3 commits, Telegram dedup]
        P3F[FinViz circuit breaker<br/>threshold=10, threading.Lock]
        P3G[run_log table<br/>per-job SUCCESS or FAILED tracking]
        P3A --> P3B --> P3C
        P3C --> P3D --> P3E --> P3F --> P3G
    end

    P3 --> P4

    subgraph P4 [PHASE 2c: Infrastructure + Brand, 14-18 May]
        P4A[Domain purchased<br/>thesignalvault.io via GoDaddy]
        P4B[Cloudflare Tunnel deployed<br/>HTTPS, edge in London]
        P4C[Project tree migration<br/>~/Documents to ~/signalintel]
        P4D[LaunchAgent + LaunchDaemon<br/>gunicorn + cloudflared survive reboot]
        P4E[Brand system established<br/>Signal Vault master + SignalIntel product]
        P4F[Vision infographic v3<br/>12-section platform reference]
        P4G[Tier matrix locked<br/>Free, Starter, Pro, Elite]
        P4A --> P4B --> P4C --> P4D
        P4D --> P4E --> P4F --> P4G
    end

    P4 --> Current

    Current([Current state, 18 May 2026<br/>247 tests passing<br/>Live at thesignalvault.io<br/>Brand locked, infrastructure stable])

    %% Styling
    classDef phaseStyle fill:#0B1929,stroke:#D4A537,stroke-width:2px,color:#fff
    classDef nodeStyle fill:#1a2942,stroke:#2a4a7a,color:#fff
    classDef startEnd fill:#0B1929,stroke:#00D67A,stroke-width:3px,color:#fff

    class P0,P1,P2,P3,P4 phaseStyle
    class P0A,P0B,P0C,P0D,P1A,P1B,P1C,P1D,P1E,P1F,P1G,P2A,P2B,P2C,P2D,P2E,P2F,P2G,P3A,P3B,P3C,P3D,P3E,P3F,P3G,P4A,P4B,P4C,P4D,P4E,P4F,P4G nodeStyle
    class Start,Current startEnd
```

---

## Phase narrative

### Phase 0: Foundation (April 2026)

Personal trading tool, not a product. Flask scaffold on Mac Mini, port 5001. FinViz screener scraper hitting roughly 11,000 US tickers. First composite score formula (v0.1). The 7-tier signal taxonomy was established here, deliberately descriptive (Very Strong, Stable, Bearish) rather than directive (Buy, Hold, Sell) to sidestep FCA regulated-advice territory.

### Phase 1: Core Product Build (late April to early May 2026)

Watchlist CRUD, ticker detail pages, global search, insider trade tracking, rating change history (13,903 historical changes backfilled in one shot), backtest engine, and Telegram alerts wired to Mark's personal bot. The product became usable as a daily trading tool for one user.

### Phase 2: Scoring Sophistication (8 to 12 May 2026)

The composite score got serious. SEC EDGAR legal-risk scraper added with additive penalties from MINOR (-5) through to CRIMINAL (-60). Sector strength multiplier (plus or minus 7.5 percent). Position A NULL handling for the reversion component (per-input neutral contribution rather than penalising missing data). Scoring engine versioned at v0.12.0 with 5 components and normalisation. Component registry refactor moved the ticker page from hardcoded rendering to array-driven, unlocking the Yahoo components 9-16 work that would follow.

### Phase 2b: Test Suite + Process Discipline (13 to 17 May 2026)

The test count grew from 206 to 247. The P1 to P18 process invariants were codified in `docs/scoring_invariants.md` (NULL equals neutral, diagnose before fixing, audit all surfaces not just symptom site, descriptive language only, audit entries must be empirical, and so on). The Phase 1 diagnostic + Phase 2 implementation pattern proved itself, four audits and four implementations in a single day on 17 May without drift. FMP entitlement observability shipped on 18 May, closing an 11-day silent-failure gap on the economic calendar cron.

### Phase 2c: Infrastructure + Brand (14 to 18 May 2026)

Domain purchased, Cloudflare Tunnel deployed, project tree migrated out of `~/Documents/` to bypass macOS TCC restrictions, LaunchAgent and LaunchDaemon configured for reboot survival. Then the brand work: Signal Vault master brand logo, SignalIntel product brand with documented family system extending to four future products (SignalCrypto, SignalForex, SignalCommodities, SignalBonds), and the 12-section vision infographic. Tier matrix locked.

### Current state

247 tests passing, site live over HTTPS at thesignalvault.io, scoring engine at v0.13.0, brand system locked, infrastructure stable. Two beta testers giving feedback. The product is functional and the foundation is laid for the next phase: monetisation, multi-user notifications, and the Yahoo components expansion.
