# Component 15: Filing Narrative (10-K Reality Check)

> **STATUS: CANDIDATE UNDER EVALUATION. NOT A LIVE COMPONENT.**
> This component is not implemented, not scored, and not part of the composite.
> No weight is assigned. Placement (composite versus dashboard-only) is undecided.
> This document is a placeholder recording the concept and the evidentiary bar it must clear.
> Last updated: 4 June 2026.

## Theory

Annual and quarterly filings (10-K, 10-Q) carry management narrative that can drift from the reported numbers: tone, hedging, disclosed-risk language, and year-over-year changes in how a business describes itself. The thesis under evaluation is that the gap between narrative and numbers carries information about future returns, in the spirit of post-earnings-announcement drift rather than social-media sentiment.

## Proposed signal mechanism

A structured-prompt LLM pipeline reads the latest filing for each ticker and emits a narrative-versus-numbers reading (e.g. management-tone or disclosed-risk drift relative to reported fundamentals). SEC EDGAR is already a live source in the platform. Refresh cadence is low (quarterly or annual per issuer), so cost per ticker per year is bounded.

## Formula

TBD. No formula is defined. No weight is assigned.

## Empirical validation

NONE YET. Before any weight is assigned, this component must pass an external-data event study in the same mould as the analyst_mom validation: a measurable, directional, statistically separable relationship between the extracted signal and forward returns against a sector benchmark. Until that bar is cleared, the default placement is dashboard-only and the component contributes zero to the composite. The COMPOSITE PURITY INVARIANT applies in full.

## Citations

Bernard and Thomas (post-earnings-announcement drift) is the closest prior. Per-component canonical citations are tracked in docs/data_source_map.md and will be attached here if and when the component graduates from candidate to live.

## Open questions

- Is the extracted signal a scoring input, or a per-ticker narrative artefact for the ticker page, /methodology content, and an Elite feature?
- If scoring: does it fill the queued News Sentiment slot (component 15) or sit alongside it?
- Composite versus dashboard-only placement.
- Pipeline shape and batch cadence.
