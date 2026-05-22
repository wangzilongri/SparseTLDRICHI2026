# Main Deck / Appendix Next Steps

## Current diagnosis

The appendix is now the strongest theoretical asset in the presentation package. It faithfully decomposes the three foundation papers and the paper's own theorem structure. The main 12-slide deck has also been repaired into a cleaner method-to-results arc in `presentation/output/transfer-learning-meta-analysis-ichi-2026-talk.results-arc.pptx`.

The next pass should not simply append more material. The right move is to treat the results-arc deck as the current main candidate, use the appendix as the source of truth for any remaining theoretical tightening, then keep the fuller derivations available for Q&A.

## Latest handover: results-arc repair

The most recent repair pass created `presentation/repair_results_arc.mjs`, using `presentation/output/transfer-learning-meta-analysis-ichi-2026-talk.repaired.pptx` as input and writing:

- `presentation/output/transfer-learning-meta-analysis-ichi-2026-talk.results-arc.pptx`
- `presentation/preview-results-arc/slide-01.png` through `slide-12.png`

Rationale for the change: the earlier results section jumped too quickly into summary ranking evidence. The repaired flow now uses the paper's experimental structure:

1. Slide 07 defines the evaluation setup: regimes, comparators, and metrics.
2. Slide 08 starts with the connected finite-sample result, where the practical gain is easiest to understand.
3. Slide 09 explains why the gain is not generic pooling: target placebo anchoring plus DR CATE learning.
4. Slide 10 gives robustness and boundary conditions: source diversity helps; A5 violations degrade performance.
5. Slide 11 closes with IHDP and keeps disconnected targets labeled as transport-based rather than identified.

Important QA lesson from this pass: covering stale slide text with white boxes is not enough. Old titles and speaker-planning phrases remained in the PPTX XML even when invisible in the PNG previews. Future repairs should delete stale text shapes before redrawing a slide and then scan the PPTX internals for meta-commentary, old titles, and ASCII math fallbacks.

## Blocking QA note

Before editing slides, apply the persistent QA checklist in `SLIDE_QA_RULES.md`: no visible meta-commentary, no text/image overlap, and no unverified equation rendering.

Also apply the hidden-text rule from the results-arc repair: do not accept a slide as clean only because the rendered PNG looks clean. Inspect the PPTX text layer or run an XML scan for phrases such as "what to say", "talk move", "we should present", "slide should", "opening evidence", and old slide titles.

The rendered previews in `presentation/preview/` appear stale relative to `presentation/build_ichi_talk.mjs`. The current repaired previews live in `presentation/preview-results-arc/`.

Example: an earlier preview/render mismatch left old slide 06 text visible in `presentation/preview/`. Before any final visual judgment, rebuild or repair the main deck and regenerate previews from the actual candidate PPTX.

Also, `presentation/preview-appendix/` only contains slides 01-17. The Kennedy and theorem/proof-sketch sections exist in `build_appendix.mjs` as S[17]-S[29], but their preview PNGs were not generated in the last visible render. These need rendering before the appendix can be fully judged.

## Proposed editing sequence

1. Regenerate main and appendix previews from the current scripts.
2. Run a contact-sheet audit for:
   - main slides 04-06, 08, 12
   - appendix slides A07, A16, A19, A20, A23, A25-A29
3. Repair the main 12-slide deck first.
4. Build an optional 3-slide Extended Methods block after slide 12 only if the audience or slot allows it.
5. Re-render and perform auditorium-readability QA.

## Main deck priorities

| Priority | Main slide | Problem | Appendix source to use | Recommended action |
|----------|------------|---------|------------------------|--------------------|
| P0 | Slide 06, Two target regimes | Preview/render mismatch suggests current QA artifacts are stale. The slide is central to the talk's truthfulness. | Our theorem slides A25-A29 | Rebuild previews. Then ensure the visible slide says identified CATE for connected, working-model transport for disconnected, and explicitly separates Theorem 1 from Theorem 2. |
| P1 | Slide 05, Estimator pipeline | The four-step pipeline is visually clean, but it compresses too much theory into tiny formulas and does not clearly show why sparse correction and DR learning are separate layers. | A07 Bastani mapping, A23 Kennedy anchored DR learner | Keep the 4-step shape, but sharpen each step into "source proxy -> target placebo residual -> sparse anchor -> DR pseudo-outcome". Consider replacing the small formulas with one readable bottom equation or a concise "two layers" callout. |
| P1 | Slide 04, Core idea | Strong concept slide, but it should set up the exact proxy-gold mapping that A07 later proves. | A02-A04 and A07 | Make the figure/copy explicitly say "source proxy is low variance but biased; target placebo is gold for baseline risk; sparse residual correction debiases the proxy." |
| Done | Slide 08, Connected finite-sample result | The results section previously opened too abruptly with average ranks. | Table II dimension sweep | Results-arc repair now starts with PEHE at m0=150, m1=100 for p=20/50/100. The ranking table issue is superseded in the current candidate deck. |
| P2 | Slide 10, Disconnected targets | Good honesty frame, but A6/theorem language can be more operational. | A11 source detection, A14 negative transfer, A28-A29 Theorem 2 | Add one compact phrase: "screen compatible sources, then transport under A6." Avoid implying identification. |
| P2 | Slide 12, Takeaways | The takeaway text is meaningful but visually crowded on the burgundy panel in the current preview. | Claim spine from slides 04-11 | Enlarge and separate the three takeaway lines. Consider dropping contact details to smaller footer treatment or moving them below "Questions?". |

## Appendix promotion decisions

| Appendix slide | Role | Decision | Why |
|----------------|------|----------|-----|
| A07, Bastani -> our estimator | Explains sparse correction in the language of the paper's first-stage anchor. | Promote as optional Extended Methods slide 13. | This is the most direct bridge between the main pipeline and the formal foundation. |
| A23, Kennedy in our estimator | Explains why the DR layer sits on top of the anchored baseline. | Promote as optional Extended Methods slide 14, after preview is regenerated. | This answers the most likely methods question about pseudo-outcomes and cross-fitting. |
| A16, Tian and Feng -> our multi-source setting | Explains K-source pooling and compatible source selection. | Promote only for statistical audience; otherwise keep for Q&A. | It is valuable but less necessary for a clinical/health-informatics audience than A07 and A23. |
| A25-A29, our theorem and proof sketches | Formal guarantee backup. | Keep in appendix, not main. | Too dense for 15 minutes, but essential during Q&A if someone asks for the exact rate statement or proof idea. |
| A19-A20, Kennedy pseudo-outcome and cross-fitting | Mechanism backup. | Keep in appendix unless slide 05 remains unclear after repair. | Useful for Q&A; probably too much for main unless the talk becomes methods-heavy. |
| A11-A14, Trans-GLM detection and negative transfer | Source-screening backup. | Keep in appendix; cite verbally on slide 10. | Supports the disconnected regime without overloading the main flow. |

## Claim spine to enforce

Every main slide should do exactly one job:

| Slide | Claim job |
|-------|-----------|
| 01 | Name the problem and method. |
| 02 | Clinical trial evidence is shifted relative to the target population. |
| 03 | Standard transport/NMA assumptions fail in the hard target setting. |
| 04 | Target placebo is the gold baseline-risk calibration signal. |
| 05 | The estimator has two layers: sparse baseline anchoring, then DR CATE learning. |
| 06 | Connected and disconnected targets support different claims and guarantees. |
| 07 | Evaluation measures accuracy, targeting, regret, and calibration. |
| 08 | Transfer pays off most when target labels are scarce. |
| 09 | The gain comes from anchoring plus DR CATE learning, not generic pooling. |
| 10 | Source diversity helps, and A5 violations degrade performance gradually. |
| 11 | IHDP shows the same pattern under real covariate shift. |
| 12 | Takeaways: anchor, separate claims, evaluate decisions. |

## Extended Methods mini-block

If adding optional slides after the 12-slide talk, use this order:

| New slide | Source | Title | Purpose |
|-----------|--------|-------|---------|
| 13 | A07 | Sparse correction is Bastani's proxy-gold debiasing step | Formalizes slide 04/05 without derailing the main talk. |
| 14 | A23 | Anchored DR learner: Kennedy on top of sparse baseline correction | Explains pseudo-outcomes, anchoring, and why cross-fitting matters. |
| 15 | A16 or A26 | Multi-source transfer / connected theorem | Choose A16 for source-selection questions; choose A26 for theorem-rate questions. |

These slides should be labeled "Extended Methods" and placed after the takeaways, not inserted into slides 01-12. The 15-minute timing should remain calibrated to the original 12-slide structure.

## Final QA gates

- Rebuild PPTX and PNG previews from current scripts.
- Verify no slide text layer contains hidden old titles, planning phrases, or speaker instructions.
- Verify slide 12 timing pill is 13:46-15:00 if the transition scheme is retained.
- Generate appendix previews for Kennedy and theorem slides.
- Inspect contact sheets at thumbnail size for claim readability.
- Inspect slide 05 and slide 12 at full size for formula/text legibility.
- Confirm notes panes no longer contain inherited template authoring notes.
- Confirm no "see appendix" labels are added to main slides 01-12.
