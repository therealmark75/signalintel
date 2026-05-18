# The Signal Vault: Outstanding Work

**What's left to build, from 18 May 2026 to public launch and beyond.**

Three lanes: critical path (must ship for public launch), parallel track (can ship after launch but soon), and future phase (post-MVP). The critical path is the launch blocker; everything else can wait.

---

```mermaid
flowchart TD
    Now([Current state, 18 May 2026<br/>Live at thesignalvault.io<br/>Beta testers, no paying users])

    Now --> CP

    subgraph CP [CRITICAL PATH: Required for public launch]
        CP1[Yahoo Finance pipeline<br/>+ scoring components 9-16<br/>FRESH CHAT, large session]
        CP2[Component rendering refactor<br/>array-driven, finalise from 11 May]
        CP3[Virtual portfolio + margin calls<br/>paper trading + bust mechanic]
        CP4[Multi-user Telegram routing<br/>per-user linking flow + user_telegram table]
        CP5[SendGrid email alerts<br/>tier-gated, watchlist + score thresholds]
        CP6[Stripe paywall + tier enforcement<br/>Starter, Pro, Elite live for paying users]
        CP7[FCA disclaimer copy<br/>lawyer sign-off required]
        CP8[Marketing homepage<br/>Sections 1 to 8 design + build]
        CP9[Dashboard restructure<br/>mockup pending]
        CP10[Methodology page<br/>replaces /ratings, folds in /backtest]
        CP11[Google Search Console<br/>sitemap, robots.txt, domain verification]
        CP12[Analytics decision<br/>Plausible vs Fathom vs GA4]
        CP13[Open Graph meta tags<br/>social preview]
        CP14[Privacy + Terms + Disclaimer<br/>finalised legal copy]

        CP1 --> CP2 --> CP3
        CP3 --> CP4 --> CP5 --> CP6
        CP7 --> CP14
        CP8 --> CP9 --> CP10
        CP11 --> CP12 --> CP13
    end

    CP --> Launch{{PUBLIC LAUNCH<br/>target: Q3 2026}}

    Launch --> PT

    subgraph PT [PARALLEL TRACK: Ship after launch, within 90 days]
        PT1[Monthly tournaments<br/>leaderboard + prize payout]
        PT2[Referral programme<br/>1 month free per referral]
        PT3[Earnings calendar<br/>FMP-backed]
        PT4[Short squeeze detector<br/>high SI + Very Strong confluence]
        PT5[Mobile responsiveness<br/>retrofit CSS across all templates]
        PT6[UK + HK equities expansion<br/>SignalIntel scope completion]
        PT7[Chart timeframe sync bug fix<br/>5m/15m/1H/1D/1W buttons]
        PT8[Penny screener exchange filter<br/>deferred from 9 May]
        PT9[Pre-commit hook<br/>auth-adjacent diff review]
        PT10[Scraper substrate audit<br/>volume + avg_volume NULL pattern]

        PT1 --> PT2
        PT3 --> PT4
        PT5 --> PT6
        PT7 --> PT8 --> PT9 --> PT10
    end

    PT --> FP

    subgraph FP [FUTURE PHASE: Post-MVP expansion]
        FP1[SignalCrypto<br/>Q3 2026 target]
        FP2[SignalForex<br/>Q4 2026 target]
        FP3[SignalCommodities<br/>2027]
        FP4[SignalBonds + SignalGilts<br/>2027]
        FP5[Mobile app, React Native<br/>iOS + Android]
        FP6[Elite API tier<br/>read + write endpoints]
        FP7[Options flow integration<br/>Unusual Whales]
        FP8[White-label B2B offering<br/>broker partnerships eToro, IBKR]

        FP1 --> FP2 --> FP3 --> FP4
        FP5 --> FP6 --> FP7 --> FP8
    end

    %% Styling
    classDef criticalStyle fill:#3d0a0a,stroke:#ff4444,stroke-width:2px,color:#fff
    classDef parallelStyle fill:#0a2a3d,stroke:#00bfff,stroke-width:2px,color:#fff
    classDef futureStyle fill:#1a0a3d,stroke:#9966ff,stroke-width:2px,color:#fff
    classDef nodeStyle fill:#1a2942,stroke:#2a4a7a,color:#fff
    classDef launchStyle fill:#0B1929,stroke:#D4A537,stroke-width:4px,color:#D4A537
    classDef nowStyle fill:#0B1929,stroke:#00D67A,stroke-width:3px,color:#fff

    class CP criticalStyle
    class PT parallelStyle
    class FP futureStyle
    class CP1,CP2,CP3,CP4,CP5,CP6,CP7,CP8,CP9,CP10,CP11,CP12,CP13,CP14,PT1,PT2,PT3,PT4,PT5,PT6,PT7,PT8,PT9,PT10,FP1,FP2,FP3,FP4,FP5,FP6,FP7,FP8 nodeStyle
    class Launch launchStyle
    class Now nowStyle
```

---

## Lane breakdown

### Critical path: required for public launch

This is the launch blocker. Nothing in here is optional if the goal is "paying users on a stable product." Roughly 14 distinct workstreams, several of which are multi-session.

**Technical workstreams:**
- Yahoo Finance pipeline (components 9 to 16): fresh chat, large infrastructure session. This is the single biggest pending technical lift.
- Component rendering refactor: must land before or alongside Yahoo components to avoid bloating the ticker page hardcode.
- Virtual portfolio with margin calls and bust mechanic: the headline feature for tournaments and engagement.
- Multi-user Telegram routing + SendGrid: notifications substrate. Currently Telegram only fires to Mark's personal bot. Hard blocker for the paywall, half-shipped notifications are worse than no notifications. Estimated 2 to 3 weeks.
- Stripe paywall: tier enforcement live for paying users. Stripe account already connected, just needs wiring.

**Legal + compliance:**
- FCA disclaimer copy, lawyer sign-off required. The bottom-of-page disclaimer on the infographic is a placeholder.
- Privacy + Terms + Disclaimer: drafts on the website, need finalised lawyer-approved copy.

**Marketing + UX:**
- Marketing homepage Sections 1 to 8: design pass partially done, build pending.
- Dashboard restructure: mockup pending, then per-page CC implementation.
- Methodology page: replaces /ratings, folds in /backtest as a tab.

**Launch operations:**
- Google Search Console indexing, sitemap, robots.txt, domain verification.
- Analytics decision: Plausible / Fathom / GA4. Privacy-friendly fits transparency-first brand positioning.
- Open Graph meta tags for social preview cards.

### Parallel track: ship after launch, within 90 days

These add to the product but don't block launch. Once the paywall is live and the first users are paying, these become the post-launch sprint backlog.

- Monthly tournaments and referral programme (the engagement loop)
- Earnings calendar and short squeeze detector (feature expansion)
- UK and HK equities (completing SignalIntel's stated scope)
- Mobile responsiveness retrofit (currently desktop-only)
- Chart timeframe sync bug, penny screener exchange filter, pre-commit hook, scraper substrate audit (debt cleanup)

### Future phase: post-MVP expansion

The Signal Vault product family beyond SignalIntel. These are timeline commitments made on the infographic, not work that should be started before SignalIntel is generating revenue.

- SignalCrypto (Q3 2026 target)
- SignalForex (Q4 2026 target)
- SignalCommodities (2027)
- SignalBonds + SignalGilts (2027)
- Mobile app, React Native (post-web launch)
- Elite API tier with read and write endpoints
- Options flow integration (Unusual Whales)
- White-label B2B and broker partnerships (eToro, IBKR)

---

## Honest read on critical-path velocity

Fourteen workstreams on the critical path. At Mark's current pace (roughly one major feature per week, plus continuous test + infrastructure work), that's a 12 to 16 week runway to launch if everything goes smoothly. Realistically with unknown unknowns (lawyer turnaround, Stripe tax setup edge cases, Yahoo pipeline surprises), allow 4 to 6 months from 18 May 2026. **Target public launch window: late September to mid November 2026.**

Two highest-leverage items to prioritise:
1. **Lawyer enquiry sent**. Without FCA clarity, the entire product positioning is built on uncertain foundations. Longest lead time of anything on the list.
2. **Yahoo Finance pipeline**. Largest single technical lift, gates the rest of the scoring engine maturity.

Everything else can sequence after those two are unblocked.
