# Slide Rationale: Transfer Learning for Meta-analysis — ICHI 2026 (15 min)

This document is a speaker-prep companion for the 12-slide ICHI 2026 oral presentation. For each slide it records: the exact paper sections and results the slide draws from, the design decisions and why they were made, and the rhetorical logic connecting each slide to the next. Transition paragraphs are in prose; anchors and rationale are in bullets for quick scanning before a talk.

---

## Narrative arc

The 12 slides follow a three-act structure:

| Act | Slides | Clock | Purpose |
|-----|--------|-------|---------|
| Setup | 01–03 | 0:00–3:00 | Problem exists; existing solutions fail; research question is formed |
| Method | 04–06 | 3:00–7:15 | Core idea; estimator pipeline; regime distinction |
| Evidence | 07–12 | 7:15–15:00 | What was tested; ranking; finite-sample advantage; disconnected regime; real data; takeaways |

Three minutes of problem framing before any method is intentional: the method's appeal depends entirely on whether the audience accepts the gap. The 8-minute method-plus-setup block versus 6.5-minute results block follows the ICHI 15-minute talk convention where motivation competes with evidence.

---

## Slide 01 — Title (0:00–0:30)

**Paper anchor**
- Title verbatim from the paper header.
- Subtitle "Placebo-anchored proxy-gold learning for target-specific treatment effects" surfaces the proxy-gold framing from the abstract; it does not appear verbatim in the paper but is a precise one-line compression of the abstract's first paragraph.
- "Research Paper" is a placeholder for the session/track name, which was not available at build time (deviation log).

**Design rationale**
- 30 seconds; the slide earns its time while the speaker states the conference context and reads the title aloud.
- No bullets or equations — the method name itself is the signal.
- Subtitle appears here, not on slide 04, because it gives the audience a label ("proxy-gold") before the setup begins. That label will pay off when slide 04 reuses the exact words.

The title names the problem (covariate shift in meta-analysis) but gives no sense of why it is hard. Slide 02 opens the "why it's hard" argument.

---

## Slide 02 — Clinical trial evidence rarely lands in the target population (0:30–1:45)

**Paper anchor**
- Introduction, Section 1, the three-part problem identification: enrollment heterogeneity (RCT sites differ by eligibility and geography), baseline risk drift (shared comparator not automatically exchangeable under covariate shift), and need for patient-level CATEs rather than average effects.
- The bottom claim line — "The decision target is patient-level and local; the available evidence is multi-site and shifted" — is a direct compression of lines 96–114.

**Design rationale**
- Three numbered cards (01, 02, 03) structure a 75-second argument without bullet fatigue.
- Cards are ordered by audience accessibility: 01 (different patients enrolled) is the most intuitive, 02 (baseline risk differences) is intermediate, 03 (need CATEs not averages) is the most technical. The audience gets a gradient from "obvious" to "the actual research gap."
- The claim at the bottom is written to be readable verbatim as the closing sentence of the slide — the speaker can deliver it as a thesis statement before moving on.

Slide 02 establishes that the problem exists. It does not yet say why existing solutions fail. Slide 03 delivers that.

---

## Slide 03 — The gap: standard transport needs conditions the target lacks (1:45–3:00)

**Paper anchor**
- Introduction, lines 101–114: two classical conditions that existing network meta-analysis and transport methods require — network connectivity (target shares a comparator arm with the source network) and shared-comparator exchangeability (placebo arms comparable after measured adjustment).
- The third row of the contrast table (average effect vs. individualized decisions) maps to lines 113–118: the methodological gap for patient-level CATE in disconnected settings.

**Design rationale**
- Two-column layout (Common assumption / Failure mode in this talk) makes the logical gap visible as a spatial contrast — the speaker walks across each row without needing to narrate both columns.
- This is the longest setup slide (75 sec) because the gap needs to be felt before the solution lands. The audience should leave this slide asking: "what do you do when the target is disconnected and shifted?"
- The bottom claim line ("The hard case is weakly connected or disconnected target evidence under covariate shift") is a precise formulation of the research question. It tells the audience exactly which case the talk addresses.

The problem frame is now complete. The audience has a research question. Slide 04 answers it in one sentence, then unpacks the answer in four steps.

---

## Slide 04 — Core idea: target placebo is the gold calibration signal (3:00–4:15)

**Paper anchor**
- Section 2.2 (Data and Proxy-Gold Setup), lines 171–188: formal definition of proxy signal (source-trial IPD outcome models, abundant but miscalibrated for the target) versus gold labels (target placebo outcomes, scarce but directly revealing local baseline risk).
- The four-step sequence (proxy signal → gold anchor → sparse correction → DR learner) mirrors the paper's Section 3 method development order, but is presented here in intuitive language before the estimator details arrive on slide 05.

**Design rationale**
- This is the conceptual hook — the single idea the audience should be able to repeat after the talk. It arrives before the detailed pipeline (slide 05) so the audience can hold the concept before the math.
- Four boxes are sequentially numbered to make the dependency chain visible: proxy → anchor → correct → learn. The ordering also mirrors the actual computation, so there is no mismatch when slide 05 re-uses the same structure at a more technical level.
- The title is the key sentence of the talk. "Target placebo is the gold calibration signal" should be memorable enough to survive the commute home.
- 75-second budget enforces one sentence per step. The speaker elaborates verbally; the slide holds the skeleton.

Slide 04 establishes the core idea intuitively. Slide 05 re-visits the same four steps at the estimator level — what is actually computed.

---

## Slide 05 — Estimator pipeline: anchor first, orthogonalize second (4:15–6:00)

**Paper anchor**
- Section 3 (Proposed Framework), lines 295–391: the full three-variant estimator (Proposed, Proposed-CF, Proposed-B).
- Step 1 (fit source models, arm-specific glmtrans): lines 307–350. Propensities noted as "known" because randomization within sites is a design feature under Assumption A2.
- Step 2 (anchor baseline via target placebo): two-step transfer — pooled source estimation followed by sparse debiasing — lines 335–355.
- Step 3 (DR pseudo-outcomes with cross-fitting, Proposed-CF): lines 363–380.
- Step 4 (estimate CATE, evaluate policy): connects to Theorem 1's Neyman-orthogonal expansion at n₀^(−1/2) rate (lines 377–378).

**Design rationale**
- Same four-box visual as slide 04 but with technical language ("mu0 and mu1", "DR pseudo-outcomes", "tau(x)"). The parallel structure creates a "zoom-in" effect: same shape, higher resolution.
- The title "anchor first, orthogonalize second" is the key methodological instruction. Anchoring before DR matters because miscalibrated baseline risk, if not corrected first, propagates into the pseudo-outcomes and undermines the orthogonality guarantee.
- This is the longest method slide (105 seconds) because the speaker needs to explain why cross-fitting matters: it allows nuisance learners to converge at slower-than-parametric rates without biasing the final CATE estimator.
- Noting propensities as "known by design" is worth emphasizing verbally — this is a structural advantage over observational transport, not an additional assumption.

Slide 05 describes a single pipeline. But the estimand and its identification status depend on whether the target has treated outcomes. Slide 06 makes the regime split explicit.

---

## Slide 06 — Two target regimes, two interpretations (6:00–7:15)

**Paper anchor**
- Theorem 1 (connected targets, lines 377–378): DR estimator is Neyman-orthogonal, admits pointwise asymptotic linear expansion at n₀^(−1/2) rate. This is a target-identified estimand.
- Theorem 2 (disconnected targets, lines 390–391): transport error decomposes into estimation error on selected sources, structural transport bias, and placebo-screening error. The estimand is a working-model transport, not nonparametrically identified.
- The "What to say" callout ("The talk should separate what is identified from what is transported; that distinction is the methodological honesty") echoes the conclusion (Section 5, lines 553–563).

**Design rationale**
- Two-column layout (Connected / Disconnected) enforces the paper's central regime distinction. The audience must leave knowing that Option A and Option B are not interchangeable claims — the confidence warranted by Theorem 1 does not transfer to Theorem 2.
- The "What to say" callout is embedded in the slide body rather than in presenter notes. This was deliberate: the distinction is important enough to be visible during delivery, not just during preparation.
- Slide 06 is at the 7:15 mark — just past the method midpoint. Placing the regime distinction here (after the pipeline, before the results) ensures that when results slides show "Proposed-B" the audience already has the interpretive frame: working-model transport, not identified.
- No equations. The theorems are stated in plain language to keep the argument accessible; anyone wanting the formal version is directed to the paper.

The method and its theoretical scope are now established. Slide 07 introduces the evaluation design — a 75-second roadmap for the four results slides that follow.

---

## Slide 07 — Evaluation: accuracy, targeting, regret, and calibration (7:15–8:30)

**Paper anchor**
- Section 4 (Experiments), lines 398–449: synthetic DGP design, evaluation metrics, baselines.
- Four boxes map to the four evaluation categories in the paper: synthetic RCTs (controlled DGP, 100 Monte Carlo replicates), ablations (TargetOnly, ProxyOnly, AnchorOnly, transport baselines, Proposed variants), stress tests (budget/dimension/source/A5 violation sweeps), IHDP benchmark (real covariates, semi-synthetic outcomes, 50 realizations).
- The four metrics in the slide title (accuracy, targeting, regret, calibration) compress the paper's five metrics: "accuracy" covers both PEHE and absolute ATE error; targeting is the Spearman rank correlation; regret and calibration are verbatim.

**Design rationale**
- This slide exists so the speaker can say "here is what we tested" in 75 seconds and the audience has a roadmap for the four results slides.
- The four boxes on slide 07 correspond directly to results slides 08–11, so the speaker can gesture back to this slide ("we are now in the stress-test box").
- "Controlled covariate shift, known potential outcomes, 100 Monte Carlo replicates" surfaces the three key experimental design properties that validate the evaluation: ground truth is observable, randomness is controlled, and replication is sufficient.

Results now land in order of scope: most aggregate (overall ranking) → most targeted (finite-sample behavior) → most constrained (disconnected regime) → most ecologically valid (real data).

---

## Slide 08 — Synthetic summary: proposed methods dominate the ranking table (8:30–10:00)

**Paper anchor**
- Table I (Average Rank Summary), Section 4, lines 481–490: Proposed avg rank 1.3, Proposed-CF 1.8, Proposed-B 2.8, OM-Transport 4.2, IPW-Transport 5.0, TargetOnly 6.0, ProxyOnly 8.5.
- The claim line is a direct compression of the table's headline: rank 1 on PEHE, ATE, Spearman, and regret for Proposed; rank 1 on ECE/calibration slope for Proposed-CF.

**Design rationale**
- Average rank across all metrics is shown as a ranked list rather than the full 7×6 Table I because a single number per method is parseable in 90 seconds; a full cross-metric table is not.
- Proposed-CF's calibration advantage is explicitly called out rather than subsumed into "Proposed wins" because the talk must not overstate. Proposed-CF trades lower pointwise PEHE for better-calibrated predictions — that trade-off matters for decision use.
- The deviation log notes that "the template has no chart-specific source slide" — the ranked-list format was the deviation that allowed a clean results claim without requiring a paper-native figure. Charts were added as editable elements inside inherited content areas.

Slide 08 makes the aggregate claim. The natural follow-up question is "when does the method's advantage appear?" Slide 09 answers with the specific condition where the gap is largest.

---

## Slide 09 — Small target samples are where transfer pays off (10:00–11:15)

**Paper anchor**
- Table II (Dimension Sweep PEHE), Section 4, lines 492–498: p ∈ {10, 20, 50, 100} crossed with target budgets (m₀, m₁) ∈ {(25,25), (25,100), (50,50), (50,100), (100,100)}.
- Three data points on the slide are pulled directly from Table II at target budget (m₀+m₁ = 250) for p = 100, 50, 20:
  - p=100: TargetOnly PEHE 7.57 → Proposed PEHE 1.71
  - p=50: TargetOnly PEHE 4.75 → Proposed PEHE 0.73
  - p=20: TargetOnly PEHE 2.60 → Proposed-CF PEHE 0.50

**Design rationale**
- The "Talk move" callout is a speaker stage direction embedded in the slide: "show this as the finite-sample reason for the method — it is strongest where target IPD is most expensive." That framing is the answer to the implicit audience question "why does this matter in practice beyond a ranking table?"
- PEHE arrows (7.57→1.71) are shown as transformations rather than table cells because the visual metaphor of compression communicates magnitude faster. The audience should immediately feel "that's a four-to-one improvement."
- TargetOnly is the right comparator here, not ProxyOnly. The claim is about the value of transfer when you have target data but not enough of it — comparing against TargetOnly is scientifically honest and most relevant to the deployment scenario.
- Proposed-CF appears at p=20 rather than Proposed because at moderate dimension and modest budget the CF variant slightly dominates — citing the right variant matters for accuracy.

Slides 08–09 cover the connected regime. Slide 10 addresses the harder case: what if there is no target treated arm at all.

---

## Slide 10 — Disconnected targets: useful, but label the assumption (11:15–12:30)

**Paper anchor**
- Table V (Disconnected PEHE, m₀=50, p ∈ {10, 20, 50, 100}), Section 4, lines 516–522: Proposed-B is best or near-best across dimensions.
- Assumption A6 (Screening-valid transportability), Section 2.2, lines 270–282: the working-model restriction that makes source screening in the disconnected regime principled but not nonparametrically identified.
- Theorem 2 (lines 390–391): transport error decomposes into estimation error, structural transport bias, and placebo-screening error — the error is bounded but the estimand is not identified.

**Design rationale**
- The title "useful, but label the assumption" is the methodological honesty principle applied directly to the results. The speaker must say explicitly that Proposed-B produces a working-model transport estimate, not a nonparametrically identified one — this is not a caveat to minimize but the technically correct characterization of the claim.
- The A6 callout card is the only place in the entire talk where an assumption number appears by name. This was deliberate: placing A6 on the results slide rather than the methods slide ensures the audience connects the assumption to the result, not just to the theory section.
- ProxyOnly is the comparator on this slide because in the disconnected regime the natural baseline is "use source models directly without screening or anchoring." Proposed-B's advantage over ProxyOnly is what justifies the extra complexity of source selection.

The disconnected regime results are in hand. Slide 11 validates the full story on real data, where covariate shift is not designed but observed.

---

## Slide 11 — IHDP benchmark: real covariate shift tells the same story (12:30–13:45)

**Paper anchor**
- Section 5 (Real-Life Data Experiments), lines 524–550: IHDP semi-synthetic setup, 25 covariates (19 binary, 6 continuous), 50 NPCI-style realizations with known counterfactual outcomes.
- Table VI (IHDP Connected PEHE): Proposed best in 9 of 9 (m₀, m₁) budget cells. Specific numbers on slide: at m₀=25, m₁=100 — Proposed PEHE 1.57 vs. OM-Transport 2.05 vs. TargetOnly 3.09.
- Table VII (IHDP Disconnected PEHE): Proposed-B lowest at all placebo budgets m₀ ∈ {25, 50, 100, 200}. Specific number: at m₀=25 — Proposed-B 2.11 vs. 2.28–2.82 for transport/proxy baselines.

**Design rationale**
- Two-card layout (Connected / Disconnected) uses the same visual structure as the regime distinction on slide 06. The parallel reinforces that the talk's central regime split applies on real data, not only in the synthetic DGP.
- Specific numbers are shown because on real data, magnitudes are the claim. A 30–50% reduction in PEHE on real IHDP covariates is more compelling than a rank ordering.
- "Interpret under the working transport condition" on the disconnected card is a deliberate repetition of the A6 reminder from slide 10. The speaker should say it again here — it is not overly cautious, it is correct.
- IHDP is the canonical semi-synthetic CATE benchmark in the literature; citing it signals that the evaluation follows established protocol, not a custom-designed favorable setting.

Evidence is complete. Slide 12 compresses the entire talk to three sentences and opens Q&A.

---

## Slide 12 — Takeaways (13:45–15:00)

**Paper anchor**
- Conclusion, Section 5, lines 553–563. The three takeaway lines map to the paper's three closing emphases:
  - "Anchor to the target placebo arm" → the core methodological contribution (Sections 2.2 and 3).
  - "Separate identified from transported claims" → the regime distinction between Theorems 1 and 2.
  - "Evaluate decisions, not only error" → the policy regret and CATE calibration metrics (Section 4, evaluation design).

**Design rationale**
- Three lines, no sub-bullets. This is the talk's "tweet" — three things the audience should be able to repeat. The compression is intentional: 75 seconds is enough for three sentences and a question invitation.
- "Questions?" is on the same slide as the takeaways so the speaker does not flip slides to get to Q&A. The takeaway list stays visible during discussion — the audience can re-read it while formulating questions.
- Contact information appears only on slide 12, not on slide 01. This avoids front-loading affiliation details when the audience needs to be focused on the problem framing in the opening 30 seconds.

---

## Peer review findings (see PEER_REVIEW.md for full report)

Two issues from the post-build review require correction before delivery:

- **Slide 08 / M1 — Proposed-B avg rank:** The 2.8 figure is not reproducible from Table I using the same 4-metric average applied to Proposed (1.3) and Proposed-CF (1.8). The correct value is approximately 3.3 — ATE rank 5.0 was silently dropped. The 2.8 reflects only PEHE + Spearman + Regret. Fix before delivery.
- **Slide 08 / M2 — Missing methods:** EntropyBal and AnchorOnly are omitted from the ranking bar chart with no disclosure. AnchorOnly (PEHE rank 7.7) is the key ablation for the DR orthogonalization claim on Slide 05. Add a footnote or include both methods.

---

## Decisions from the deviation log

Three design choices departed from strict template-following and are documented here for reference if the deck is adapted for a different venue:

| Deviation | Reason | Implication for reuse |
|-----------|--------|-----------------------|
| Added editable chart/callout elements inside inherited content areas | The ICHI template has no chart-specific source slide; results needed a visual form that could be built from existing layout frames | Any venue template should be audited for whether these elements survive a theme change |
| Omitted a standalone acknowledgments slide | 15-minute slot is fully committed to claims, method, and validation; acknowledgments can be spoken on slide 12 if needed | A 20+ minute version should restore a dedicated acknowledgments slide |
| Used "Research Paper" as the session/track label | Exact ICHI 2026 session assignment was not known at build time | Replace before delivery once the session schedule is confirmed |
