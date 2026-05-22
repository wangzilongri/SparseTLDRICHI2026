# Slide Rationale: Transfer Learning for Meta-analysis — ICHI 2026 (15 min)

This document is a speaker-prep companion for the 12-slide ICHI 2026 oral presentation. For each slide it records: the exact paper sections and results the slide draws from, the design decisions and why they were made, and the rhetorical logic connecting each slide to the next. Transition paragraphs are in prose; anchors and rationale are in bullets for quick scanning before a talk.

---

## Narrative arc

The 12 slides follow a three-act structure:

| Act | Slides | Click target | Purpose |
|-----|--------|-------------|---------|
| Setup | 01–03 | 0:00–3:00 | Problem exists; existing solutions fail; research question is formed |
| Method | 04–06 | 3:00–7:15 | Core idea; estimator pipeline; regime distinction |
| Evidence | 07–12 | 7:15–15:00 | What was tested; ranking; finite-sample advantage; disconnected regime; real data; takeaways |

Three minutes of problem framing before any method is intentional: the method's appeal depends entirely on whether the audience accepts the gap. The 8-minute method-plus-setup block versus 6.5-minute results block follows the ICHI 15-minute talk convention where motivation competes with evidence.

---

## Transition design

Slide transitions serve a rhetorical function, not merely an aesthetic one. Three tiers are used:

| Tier | Description | Type | Duration | Applied at |
|------|-------------|------|----------|-----------|
| **Act break** | Audience needs a visual beat to reset between major narrative phases | Fade | 700 ms | 01→02, 05→06, 11→12 |
| **Argument pivot** | A major rhetorical turn that answers or redirects the previous slide's question | Cover-right or Push-left | 500 ms | 03→04, 06→07, 09→10, 10→11 |
| **Within-section cut** | Continuing the same argument; any pause would falsely signal a new topic | Cut (instant) | 0 ms | 02→03, 04→05, 07→08, 08→09 |

**Total transition time:** 3 × 700 ms + 4 × 500 ms = 4.1 seconds across the 15-minute talk. Negligible for content timing, visible to the audience as pacing control.

**Timing pill convention:** Slides that follow a 700 ms fade have their pill start time advanced by 1 second (0:31, 6:01, 13:46) to reflect the speaking time actually available after the transition completes. Slides following a 500 ms pivot or cut retain the nominal start time — sub-second adjustments are noise at this resolution.

**Implementation note:** `setTransition(slide, type, durationMs)` in `build_ichi_talk.mjs` attempts to set transitions via the artifact tool's slide API. If the API does not expose transitions on the installed version, the function degrades silently and transitions should be applied manually in PowerPoint: open the PPTX, select each slide, and apply the type and duration listed in the table above.

---

## Slide 01 — Title (0:00–0:30) · Transition in: none (first slide)

**Paper anchor**
- Title verbatim from the paper header.
- Subtitle "Placebo-anchored proxy-gold learning for target-specific treatment effects" surfaces the proxy-gold framing from the abstract.
- "Research Paper" is a placeholder for the session/track name (replace before delivery).

**Design rationale**
- 30 seconds; no bullets or equations — the method name itself is the signal.
- Subtitle appears here, before slide 04, so the audience has a label ("proxy-gold") before the setup begins. That label pays off when slide 04 reuses the exact words.

The title names the problem but gives no sense of why it is hard. Slide 02 opens the "why it's hard" argument.

---

## Slide 02 — Clinical trial evidence rarely lands in the target population (0:31–1:45) · Transition in: fade 700 ms

The 1-second shift from 0:30 to 0:31 reflects the 700 ms fade from the title slide.

**Paper anchor**
- Introduction, Section 1: enrollment heterogeneity, baseline risk drift, and need for patient-level CATEs.
- Claim line: direct compression of lines 96–114.

**Design rationale**
- Three numbered cards (01–03) structure a 74-second argument without bullet fatigue.
- Cards are ordered by accessibility: 01 (different patients enrolled) is intuitive; 02 (baseline risk differences) is intermediate; 03 (need CATEs not averages) is the actual research gap.
- The fade from slide 01 signals "this is a new thought, not a continuation of the title."

Slide 02 establishes that the problem exists. Slide 03 shows why existing solutions fail.

---

## Slide 03 — The gap: standard transport needs conditions the target lacks (1:45–3:00) · Transition in: cut 0 ms

Cut from slide 02: the gap slide continues the same problem-setup argument — any pause would falsely imply the problem framing is complete.

**Paper anchor**
- Introduction, lines 101–114: network connectivity and shared-comparator exchangeability as classical conditions, and why they fail in the disconnected, shifted setting.

**Design rationale**
- Two-column layout (Common assumption / Failure mode in this talk) makes the logical gap visible as spatial contrast.
- Longest setup slide (75 s) because the gap must be felt before the solution lands.
- Claim line ("weakly connected or disconnected target evidence under covariate shift") is the exact research question.

The problem frame is complete. Slide 04 answers it.

---

## Slide 04 — Core idea: target placebo is the gold calibration signal (3:00–4:15) · Transition in: cover-right 500 ms

Cover-right is the most assertive forward motion available: it literally sweeps the problem slide away and reveals the answer. The pivot from "gap" to "solution" is the talk's single most important rhetorical moment.

**Paper anchor**
- Section 2.2 (Data and Proxy-Gold Setup), lines 171–188: formal proxy-gold distinction.
- Four-step sequence (proxy → anchor → correct → learn) mirrors the paper's Section 3 development order in intuitive language.

**Design rationale**
- Conceptual hook before the detailed pipeline. The audience needs to hold the concept before the math arrives on slide 05.
- The title ("target placebo is the gold calibration signal") is the talk's single most memorable sentence.
- 75-second budget enforces one sentence per step; the speaker elaborates verbally.

Slide 04 establishes the core idea intuitively. Slide 05 re-visits the same four steps at estimator level.

---

## Slide 05 — Estimator pipeline: anchor first, orthogonalize second (4:15–6:00) · Transition in: cut 0 ms

Cut from slide 04: the pipeline slide zooms into the same four-step frame at higher resolution. Any transition would falsely signal a new concept rather than an elaboration.

**Paper anchor**
- Section 3 (Proposed Framework), lines 295–391.
- Step 1: arm-specific glmtrans, lines 307–350. Propensities noted as "known" under A2.
- Step 2: anchor via target placebo, lines 335–355.
- Step 3: DR pseudo-outcomes with cross-fitting (Proposed-CF), lines 363–380.
- Step 4: estimate CATE → Theorem 1's n₀^{-1/2} rate (lines 377–378).

**Design rationale**
- Same four-box visual as slide 04 with technical language ("mu0 and mu1", "DR pseudo-outcomes"). Parallel structure creates a zoom-in effect: same shape, higher resolution.
- Longest method slide (105 s) because cross-fitting needs explanation: slower nuisance convergence rates still yield valid inference because propensities are known.
- The title "anchor first, orthogonalize second" is the key methodological instruction. Anchoring before DR matters because miscalibrated baseline risk propagates into pseudo-outcomes and undermines orthogonality.

Slide 05 describes a single pipeline. Slide 06 splits it into two interpretive regimes.

---

## Slide 06 — Two target regimes, two interpretations (6:01–7:15) · Transition in: fade 700 ms

Fade signals a genuine section break: the "how it works" block ends here and the "what it means theoretically" frame begins. The 1-second pill adjustment (6:00 → 6:01) reflects the 700 ms fade.

**Paper anchor**
- Theorem 1 (connected): DR estimator is Neyman-orthogonal, n₀^{-1/2} asymptotically linear expansion, identified target-site CATE.
- Theorem 2 (disconnected): transport error decomposes into estimation error, structural transport bias (ε_τ), and screening error O_p(η^{1/2}).
- "What to say" callout echoes Section 5 conclusion: the regime distinction is the methodological honesty.

**Design rationale**
- Two-column layout enforces the central regime distinction. Option A and Option B carry different guarantees; the audience must leave knowing they are not interchangeable.
- "What to say" is embedded in the slide body, not presenter notes — the distinction is important enough to be visible during delivery.
- No equations: the theorems are stated in plain language. Anyone wanting the formal version is directed to the paper.

The method and its scope are established. Slide 07 opens the evidence block.

---

## Slide 07 — Evaluation: accuracy, targeting, regret, and calibration (7:15–8:30) · Transition in: push-left 500 ms

Push-left is the strongest directional transition available and is reserved for this single location: the method-to-evidence pivot. The audience should feel the talk shift gears. Note: the push takes 500 ms so the pill remains 7:15 (sub-second adjustment omitted).

**Paper anchor**
- Section 4 (Experiments), lines 398–449: synthetic DGP design, evaluation metrics, baselines.
- Four boxes map directly to results slides 08–11 (synthetic ranking, finite-sample, disconnected, IHDP).

**Design rationale**
- Roadmap slide: 75 seconds to establish "here is what we tested" before the specific results arrive.
- The four boxes correspond visually to results slides 08–11, so the speaker can gesture back ("we are now in the stress-test box").

Results land in order of scope: most aggregate (08) → most targeted (09) → most constrained (10) → most ecologically valid (11).

---

## Slide 08 — Synthetic summary: proposed methods dominate the ranking table (8:30–10:00) · Transition in: cut 0 ms

Cut from slide 07: the ranking table is the first evidence delivery, directly following the roadmap. No pause warranted.

**Paper anchor**
- Table I (Average Rank Summary), Section 4, lines 481–490.
- Proposed avg rank 1.3 (PEHE+ATE+Spearman+Regret average: (1.4+1.2+1.3+1.4)/4 = 1.325). ✓
- Proposed-CF avg rank 1.8 (verified). ✓
- **Proposed-B avg rank 3.3** — corrected from the 2.8 error in the original build (peer review M1). The correct 4-metric average is (2.7+5.0+2.8+2.8)/4 = 3.325. ATE rank 5.0 was previously dropped, concealing the largest weakness of Option B.
- **Footnote added** for AnchorOnly (≈6.5) and EntropyBal (≈5.5) — both omitted for space (peer review M2). AnchorOnly is the key ablation for the DR orthogonalization claim on slide 05; its omission from the chart without disclosure was a scientific transparency issue. The footnote resolves it.

**Design rationale**
- Ranked bar chart rather than the full 7×6 Table I: one number per method is parseable in 90 seconds; the full table is not.
- Proposed-CF's calibration advantage is called out separately because the talk must not conflate pointwise accuracy (Proposed) with calibration (Proposed-CF).

Slide 08 makes the aggregate claim. Slide 09 shows where and why the gap is largest.

---

## Slide 09 — Small target samples are where transfer pays off (10:00–11:15) · Transition in: cut 0 ms

Cut: continuing the same synthetic evidence block, zooming into the specific finite-sample regime.

**Paper anchor**
- Table II (Dimension Sweep PEHE), lines 492–498. Three exact numbers at target budget (m₀=150, m₁=100):
  - p=100: TargetOnly 7.57 → Proposed 1.71 ✓
  - p=50: TargetOnly 4.75 → Proposed 0.73 ✓
  - p=20: TargetOnly 2.60 → Proposed-CF 0.50 ✓

**Design rationale**
- "Talk move" callout tells the speaker: this is the finite-sample argument for deploying the method. The method is strongest exactly where target IPD is most expensive to collect.
- PEHE arrows (7.57→1.71) shown as transformations, not table cells — the visual compression communicates magnitude faster.
- TargetOnly is the right comparator: the claim is about transfer value when you have target data but not enough of it.

---

## Slide 10 — Disconnected targets: useful, but label the assumption (11:15–12:30) · Transition in: fade 500 ms

Fade marks the connected-to-disconnected regime pivot. The audience's interpretive frame needs to shift: Proposed-B targets a transported estimand, not an identified one.

**Paper anchor**
- Table V (Disconnected PEHE, m₀=50), lines 516–522.
- Assumption A6 (Screening-valid transportability), lines 270–282.
- Theorem 2: transport error = estimation error + ε_τ + O_p(η^{1/2}).

**Design rationale**
- "Useful, but label the assumption" is the methodological honesty principle applied directly. The speaker must say explicitly that Proposed-B is a working-model transport estimate.
- A6 callout is the only assumption named by number in the results — deliberate: the audience connects assumption to result, not just to the theory section.
- ProxyOnly is the comparator: in the disconnected regime, the baseline is using source models directly without screening or anchoring.

---

## Slide 11 — IHDP benchmark: real covariate shift tells the same story (12:30–13:45) · Transition in: fade 500 ms

Fade signals the move from controlled synthetic evidence to ecological-validity evidence. The pivot from DGP to real covariates is an important credibility shift.

**Paper anchor**
- Section 5 (Real-Life Data), lines 524–550.
- Table VI (IHDP Connected PEHE): Proposed best in 9/9 cells. Shown: m₀=25, m₁=100 → 1.57 vs 2.05 vs 3.09. ✓
- Table VII (IHDP Disconnected PEHE): Proposed-B lowest at all m₀. Shown: m₀=25 → 2.11 vs 2.28–2.82. ✓

**Design rationale**
- Two-card layout (Connected / Disconnected) mirrors slide 06's regime distinction — the parallel reinforces that the regime split applies on real data.
- "Interpret under the working transport condition" on the disconnected card is a deliberate repetition of the A6 reminder from slide 10. Say it again — it is not overcautious, it is correct.
- IHDP is the canonical semi-synthetic CATE benchmark; citing it signals that the evaluation follows established protocol.

Evidence is complete. Slide 12 compresses the talk to three sentences and opens Q&A.

---

## Slide 12 — Takeaways (13:46–15:00) · Transition in: fade 700 ms

Fade at 700 ms is the final act break — the longest fade in the deck, signaling a qualitative shift from data to synthesis. The 1-second pill adjustment (13:45 → 13:46) reflects this.

**Paper anchor**
- Conclusion, Section 5, lines 553–563. Three takeaway lines map to the paper's closing emphases:
  - "Anchor to the target placebo arm" → core methodological contribution (Sections 2.2 and 3).
  - "Separate identified from transported claims" → regime distinction between Theorems 1 and 2.
  - "Evaluate decisions, not only error" → policy regret and CATE calibration metrics (Section 4).

**Design rationale**
- Three lines, no sub-bullets. This is the talk's "tweet" — three things the audience should be able to repeat.
- "Questions?" stays on the takeaway slide so the speaker does not flip away. The takeaway list remains visible during discussion.
- Contact information appears only here, not on slide 01. Front-loading affiliation details interrupts the opening problem frame.

---

## Peer review status

Both major issues from PEER_REVIEW.md have been resolved in the current build:

| ID | Issue | Status | Resolution |
|----|-------|--------|-----------|
| M1 | Proposed-B avg rank shown as 2.8 (ATE rank 5.0 silently dropped) | ✅ Fixed | Bar now shows 3.3 = (2.7+5.0+2.8+2.8)/4. ATE rank 5.0 is the theoretically motivated limitation of working-model transport; concealing it was a scientific transparency failure. |
| M2 | AnchorOnly and EntropyBal silently omitted from ranking chart | ✅ Addressed | Footnote added: "AnchorOnly (avg rank ≈6.5, ablation) and EntropyBal (≈5.5) omitted for space — full 9-method comparison in Table I." The disclosure is present; the key ablation evidence (AnchorOnly isolates the DR orthogonalization contribution) is credited. |
| m1 | Dual "1.3" callouts ambiguous | Open | Slide 08 still shows two 1.3 callouts (Proposed avg rank; Proposed-CF ECE rank). Labels are distinct ("avg rank" vs "ECE rank"). Revisit if auditorium feedback indicates confusion. |
| m2 | Slide 12 text too small | Open | Monitor during rehearsal; increase takeaway font if room is large. |

---

## Appendix integration

The appendix deck (`appendix-lecture-method-foundations.pptx`, built by `build_appendix.mjs`) contains 25+ slides across four sections. The 12 main slides never reference the appendix directly. This section documents how to navigate between them during Q&A and what, if anything, to promote into the main file.

### Appendix slide inventory

Slides are numbered here as they appear in `preview-appendix/` (1-based). Build-script array indices are S[n] (0-based, so preview slide 1 = S[0]).

| Preview # | S[n] | Section | Title |
|-----------|-------|---------|-------|
| 01 | S[0] | Divider | "Appendix: Method Foundations" (Bastani · Tian & Feng · Kennedy) |
| 02 | S[1] | Bastani | Bastani (2021): Predicting with Proxies — overview |
| 03 | S[2] | Bastani | Formal model: shared features, sparse correction |
| 04 | S[3] | Bastani | The joint estimator: two-step LASSO |
| 05 | S[4] | Bastani | Main result: bias sparsity s replaces dimension d |
| 06 | S[5] | Bastani | When the proxy-gold correction works / failure modes |
| 07 | S[6] | Bastani | **How Bastani maps to our estimator** (proxy → μ̂₀^anchor) |
| 08 | S[7] | Bridge | Beyond one proxy: K sources — bridge to Tian & Feng |
| 09 | S[8] | T&F | Tian & Feng (2023): Transfer Learning under High-dimensional GLMs |
| 10 | S[9] | T&F | Setup: K source GLMs + 1 target in high dimension |
| 11 | S[10] | T&F | A-Trans-GLM: two-step algorithm with known A_h |
| 12 | S[11] | T&F | Trans-GLM: data-driven source selection (CV, Theorem 4) |
| 13 | S[12] | T&F | Main theorem: transfer replaces n₀ by n_{A_h} + n₀ |
| 14 | S[13] | T&F | Negative transfer: uninformative sources hurt |
| 15 | S[14] | T&F | Bastani vs Tian & Feng: key differences (comparison table) |
| 16 | S[15] | T&F | **How T&F maps to our multi-source clinical trial setting** |
| 17 | S[16] | Summary | Two papers, one estimator pipeline |
| — | S[17] | Divider | Kennedy (2023): Doubly Robust CATE Estimation |
| — | S[18] | Kennedy | Setup: estimating heterogeneous treatment effects |
| — | S[19] | Kennedy | **The DR pseudo-outcome: efficient influence function for CATE** |
| — | S[20] | Kennedy | **Cross-fitting: separating nuisance training from CATE regression** |
| — | S[21] | Kennedy | Main theorem: product error and optimal rates |
| — | S[22] | Kennedy | Why it works: Neyman orthogonality and the influence function |
| — | S[23] | Kennedy | **Kennedy in our estimator: the anchored DR learner** |
| — | S[24] | Divider | Our Estimator: Rate Statements and Proof Sketches |

**Bolded rows** are the highest-value Q&A targets — they provide the direct "how exactly does X work in your paper?" answer.

Preview images for S[17]–S[24+] (Kennedy + theorems) are not yet generated; they exist in the build script but were not rendered in the last `build_appendix.mjs` run.

---

### Cross-reference: main slides → appendix backup

| Main slide | Likeliest follow-up question | Appendix slides to jump to |
|------------|------------------------------|---------------------------|
| **04** — Core idea (proxy-gold) | "What exactly is the sparse correction step?" | A02–A04 (Bastani overview, formal model, two-step LASSO) |
| **04** — Core idea | "How does Bastani's framework connect to your CATE estimator?" | A07 (Bastani → our estimator mapping) |
| **05** — Estimator pipeline | "What are the pseudo-outcomes? How does cross-fitting work?" | A19 (DR pseudo-outcome), A20 (cross-fitting algorithm) |
| **05** — Estimator pipeline | "Why does the sparse correction help baseline risk estimation?" | A03–A04 (joint estimator, main theorem), A07 |
| **05** — Estimator pipeline | "How do you handle K source trials, not just one?" | A08–A10 (bridge + T&F setup + A-Trans-GLM) |
| **06** — Two regimes | "What is the actual statement of Theorem 1?" | A24+ (our theorems divider + Theorem 1 slide) |
| **06** — Two regimes | "What is A6 (screening-valid transportability)?" | A24+ (Theorem 2 / disconnected proof sketch) |
| **08** — Ranking table | "Why exclude AnchorOnly from the chart?" | No appendix slide; use the on-slide footnote (added via M2 fix) + verbal: "AnchorOnly ranks ~6.5, Table I" |
| **09** — Finite-sample gap | "Is this advantage just because you have more data?" | A12–A13 (T&F main theorem showing exact n_{A_h} improvement; negative transfer slide) |
| **10** — Disconnected | "What is the formal Theorem 2 statement?" | A24+ (Theorem 2 proof sketch) |
| **10** — Disconnected | "How do you detect whether a source is informative?" | A11 (Trans-GLM CV detection algorithm) + A12 (detection consistency Theorem 4) |
| **11** — IHDP | "IHDP is semi-synthetic — does this generalize?" | No appendix slide; handle verbally (cite Hill 2011, Dorie 2019 for IHDP protocol) |

---

### Q&A navigation guide

Print or keep on a tablet beside the laptop during the talk. Jump directly by clicking the thumbnail bar in PowerPoint or pressing slide number + Enter.

| If asked… | Say | Go to appendix slide # |
|-----------|-----|------------------------|
| "How does the sparse correction actually work?" | "Great to dive in — the formal two-step LASSO is in the appendix." | **04** (two-step LASSO) |
| "What's your theoretical guarantee for the connected case?" | "Theorem 1 is in the appendix — let me show the rate." | **S[24+]** (Our theorems section) |
| "Why not just pool all source trials without the selection step?" | "Negative transfer is the reason — here's the formal result." | **14** (negative transfer) |
| "What are pseudo-outcomes?" | "That's the DR pseudo-outcome from Kennedy 2023 — appendix covers it." | **A19** (Kennedy pseudo-outcome) |
| "Does cross-fitting matter in practice?" | "Yes — it's what separates Proposed-CF's ECE advantage. The algorithm is here." | **A20** (cross-fitting) |
| "How does your estimator relate to Bastani?" | "Direct mapping — every term corresponds." | **07** (Bastani → our mapping) |
| "And how does it relate to Tian & Feng?" | "Same slide structure — K-source extension." | **16** (T&F → our mapping) |

---

### Promotion candidates: slides worth inserting into the main deck

These appendix slides are candidates for promotion into an optional **"Extended Methods" block** (slides 13–15, after the current takeaways) if the speaker has 3–5 minutes of buffer or expects a technically sophisticated audience:

| Priority | Appendix slide | Rationale for promotion |
|----------|---------------|------------------------|
| 1 (highest) | **A07 — Bastani → our estimator mapping** | Directly bridges the gap between slide 05's four-step pipeline description and the formal sparse correction. The row-by-row correspondence table (β*_proxy → μ̂₀^proxy, δ̂ → sparse correction, etc.) answers the single most frequent question a statistical methods audience will have. |
| 2 | **A23 — Kennedy in our estimator (anchored DR learner)** | The pseudo-outcome comparison table (standard Kennedy vs. our anchored variant) makes the contribution of the anchoring step concrete. Directly supports slide 05's Step 2 and the Theorem 1 guarantee on slide 06. |
| 3 | **A16 — T&F → our multi-source mapping** | For audiences familiar with glmtrans or the T&F paper; shows exactly how our K-source pooling step inherits the A-Trans-GLM structure. Less critical if the audience is clinically rather than statistically focused. |

**Implementation note:** Do NOT insert these into slides 01–12. The timing pills and transitions are calibrated for the 12-slide structure. Add any promoted slides as new slides 13, 14, 15 with their own timing pills (no transition constraints apply). Label each with a corner tag "(Extended)" so the speaker can skip them cleanly if time is short.

---

### What not to do

- **Do not reorder the appendix.** The Bastani → T&F → Kennedy → Theorems sequence mirrors the paper's theoretical dependency chain and is the correct reading order for a deep-dive audience.
- **Do not merge the two appendix PPTX files.** `appendix-lecture-bastani-tian-feng.pptx` (82 KB) and `appendix-lecture-method-foundations.pptx` (140 KB) serve different audiences (quick background vs. full foundations). Keep them separate.
- **Do not add "see appendix" annotations to slides 01–12.** Visual clutter hurts pacing; navigate verbally during Q&A instead using the table above.
- **Do not generate Kennedy + theorems previews mid-session.** The build is expensive; only rebuild if those slides change. The existing build covers the 17 most-asked-about slides.

---

## Decisions from the deviation log

| Deviation | Reason | Implication for reuse |
|-----------|--------|-----------------------|
| Added editable chart/callout elements inside inherited content areas | No chart-specific source slide in the ICHI template | Audit for theme-change survival at any new venue |
| Omitted standalone acknowledgments slide | 15-minute slot fully committed; acknowledgments spoken on slide 12 | Restore for 20+ minute version |
| Used "Research Paper" as session/track label | Exact ICHI 2026 session assignment not known at build time | Replace before delivery |
| Transition API degrades silently if not supported by artifact tool version | setTransition() wraps calls in try-catch | Apply transitions manually in PowerPoint if needed; see Transition design table above |
