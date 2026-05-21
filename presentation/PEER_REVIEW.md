# Peer Review: ICHI 2026 Slide Deck
## Transfer Learning for Meta-analysis Under Covariate Shift

**Review date:** 2026-05-21  
**Slides reviewed:** 12 slides (`presentation/layout/slide-01.layout.json` – `slide-12.layout.json`)  
**Visual inspection:** `presentation/preview/slide-01.png` – `slide-12.png`  
**Reference paper:** `main.tex` + `Tables/` (all table source files verified directly)  
**Method:** Image-based visual audit + quantitative claim verification against raw table `.tex` files

---

## Summary Statement

The deck communicates the paper's core narrative accurately and the majority of quantitative claims are exact matches to the paper's tables. The three-act structure (problem → method → evidence) is appropriate for a 15-minute ICHI slot. However, two findings require correction before delivery: a reproducibility failure in the Proposed-B average rank number on Slide 08 (cannot be verified from Table I using the same averaging method applied to other methods), and a silent omission of two methods (EntropyBal, AnchorOnly) from the ranking bar chart. Two additional visual issues need attention on Slides 08 and 12.

**Overall recommendation:** Minor revisions required — corrections to Slide 08 are mandatory before delivery; Slide 12 visual fix is strongly recommended.

**Strengths:**
- All IHDP and dimension-sweep quantitative claims are exact matches to the paper's tables (Slides 09–11)
- The regime distinction (identified vs. working-model transport) is consistently and honestly flagged across all results slides (Slides 06, 10, 11)
- 15-minute pacing is tight and disciplined (30 seconds per slide average, correctly front-loaded on motivation)

**Weaknesses:**
- Proposed-B's average rank figure on Slide 08 is not reproducible from Table I
- Two comparison methods are silently removed from the ranking display
- Closing slide (Slide 12) has text too small for auditorium visibility

---

## Major Issues (Must Fix Before Delivery)

### M1 — Slide 08: Proposed-B average rank is not reproducible from Table I

**Location:** Slide 08 ranking bar chart, Proposed-B bar labeled 2.8  
**Paper reference:** `Tables/P3_Avg_Rank_Summary.tex`

The slide displays Proposed-B's average rank as **2.8**. Verifying from the table source:

| Metric | Proposed | Proposed-CF | Proposed-B |
|--------|----------|-------------|------------|
| PEHE | 1.4 | 1.6 | 2.7 |
| ATE | 1.2 | 1.7 | **5.0** |
| Spearman (τ) | 1.3 | 2.1 | 2.8 |
| Regret | 1.4 | 1.8 | 2.8 |
| **4-metric avg** | **1.325 → 1.3 ✓** | **1.8 ✓** | **3.325 ≠ 2.8 ✗** |

The 1.3 and 1.8 figures for Proposed and Proposed-CF are exact matches using the 4-metric performance average (PEHE + ATE + Spearman + Regret). For Proposed-B, applying the same formula gives 3.325. The displayed value of 2.8 matches only the 3-metric average excluding ATE: (2.7 + 2.8 + 2.8) / 3 = 2.77 ≈ 2.8.

**Why this matters:** Proposed-B's ATE rank of 5.0 is the single largest weakness of the disconnected variant — it performs well on pointwise CATE metrics (PEHE, Spearman) but poorly on population-average ATE because working-model transport does not target identification of the marginal effect. Dropping ATE from the average conceals the most theoretically motivated limitation of Option B, which the paper's own Theorem 2 acknowledges.

**Fix options:**
- **Option A (preferred):** Correct Proposed-B's bar to 3.3 (4-metric average). Add a footnote: "Proposed-B's ATE rank (5.0) reflects the non-identified nature of the disconnected estimand; pointwise PEHE/Spearman ranks are 2.7 and 2.8."
- **Option B:** Show a separate column for performance vs. calibration ranks (matching the table's two-panel structure) and let Proposed-B's ATE figure speak for itself.
- **Option C (minimum):** Add a verbal disclosure during delivery: "Proposed-B's 2.8 reflects PEHE and ranking metrics — on ATE it ranks 5th, consistent with Option B being working-model transport, not identified."

---

### M2 — Slide 08: EntropyBal and AnchorOnly silently omitted from the ranking display

**Location:** Slide 08 ranking bar chart (7 bars shown, paper Table I has 9 methods)  
**Paper reference:** `Tables/P3_Avg_Rank_Summary.tex`

The paper's Table I includes 9 methods. The slide shows only 7:

| Present on slide | Missing from slide |
|------------------|--------------------|
| Proposed | **AnchorOnly** |
| Proposed-CF | **EntropyBal** |
| Proposed-B | |
| OM-Transport | |
| IPW-Transport | |
| TargetOnly | |
| ProxyOnly | |

**AnchorOnly** is the most important omission. It is the key ablation isolating the contribution of the DR orthogonalization step — the difference between Proposed and AnchorOnly is the direct empirical evidence for Slide 05's claim that cross-fitting matters. AnchorOnly's ranks from the table: PEHE 7.7, ATE 3.1, Spearman 7.6, Regret 7.4 — it performs worse than TargetOnly on PEHE and Spearman, which is a strong result for the paper's method claim. Omitting it from the slide removes the most pointed ablation evidence.

**EntropyBal** is a standard baseline; its omission is less critical but leaves the comparison set undisclosed.

A conference reviewer or audience member familiar with the paper's ablation table may ask directly why AnchorOnly is missing. There is no defensible scientific reason to omit it.

**Fix:** Add a one-line disclosure to the bar chart: "7 of 9 methods shown; AnchorOnly (avg rank ~6.5) and EntropyBal (~5.5) omitted for space — see Table I." Alternatively, reduce bar chart font size to fit all 9 methods, or split the chart into a two-panel layout (ablations | baselines).

---

## Minor Issues (Strongly Recommended)

### m1 — Slide 08: Dual "1.3" callout boxes are ambiguous

**Location:** Right-hand summary panel on Slide 08

The slide shows two large "1.3" callout boxes: one labeled "Proposed avg rank" and one labeled "CF calibration rank / best ECE average rank." Both show the same number for different methods measuring different things. Under rapid reading or at a distance, this reads as Proposed-CF also having avg rank 1.3, which is not the case (CF avg rank = 1.8).

**Fix:** Differentiate labels more sharply. For the second callout, use "1.3 ECE rank (Proposed-CF)" and increase label font size. Or remove the duplicate callout and let the bar chart carry the Proposed-CF message.

---

### m2 — Slide 12: Closing slide text too small for auditorium viewing

**Location:** Left-side text panel on Slide 12

The visual audit identified text on the closing slide as small against the burgundy box background. The three takeaway lines and the contact information are the most important content of the entire talk (the audience's last visible frame). Estimated font size from preview puts body text below 18pt effective size at 1280×720.

**Fix:** Increase takeaway text to minimum 24pt; contact line to minimum 18pt. If needed, remove the full-width background image or reduce its opacity to ensure the text reads cleanly from the back of the room.

---

### m3 — Slide 05: "Estimate CATE" step conflates estimation and evaluation

**Location:** Slide 05, Step 4 box: "Estimate CATE → Predict tau(x), evaluate ranking, calibration, and treatment policy regret"

Ranking, calibration, and policy regret are evaluation metrics, not outputs of the CATE estimator. A technically precise audience member may object that the estimator outputs τ̂(x) — the evaluation is done post-hoc against ground truth.

**Impact:** Low — this is a presentation convenience, not a scientific misrepresentation. But if asked, the speaker should be ready to clarify.

**Fix (optional):** Revise to "Predict τ̂(x); evaluate PEHE, calibration, and policy regret" to signal that evaluation is a separate downstream step. Or leave as-is and prepare a verbal clarification.

---

## Verified Claims (No Issues)

| Slide | Claim | Verdict |
|-------|-------|---------|
| 09 | p=100: TargetOnly 7.57 → Proposed 1.71 | Exact match to Table II ✓ |
| 09 | p=50: TargetOnly 4.75 → Proposed 0.73 | Exact match to Table II ✓ |
| 09 | p=20: TargetOnly 2.60 → Proposed-CF 0.50 | Exact match to Table II ✓ |
| 09 | Budget (m₀=150, m₁=100) | Confirmed in table row headers ✓ |
| 10 | Proposed-B best on disconnected PEHE (m₀=50, all p) | Best in all 4 cells from Table IV ✓ |
| 11 | IHDP connected (25,100): 1.57 vs 2.05 vs 3.09 | Exact match to Table V ✓ |
| 11 | Proposed best in 9/9 IHDP connected PEHE cells | Verified all 9 cells ✓ |
| 11 | IHDP disconnected (m₀=25): 2.11 vs 2.28–2.82 | Proposed-B 2.11 exact; range 2.28–2.82 captures all four baselines (OM 2.28, IPW 2.30, ProxyOnly 2.64, EB 2.82) ✓ |
| 11 | Proposed-B lowest PEHE at all placebo budgets | Best at m₀=25,50,100,200 from Table VI ✓ |
| 08 | Proposed avg rank 1.3 (PEHE/ATE/τ/Regret) | (1.4+1.2+1.3+1.4)/4 = 1.325 ✓ |
| 08 | Proposed-CF avg rank 1.8 | (1.6+1.7+2.1+1.8)/4 = 1.8 ✓ |
| 08 | Proposed-CF leads ECE calibration (rank 1.3) | ECE 1.3 from Table I ✓ |
| 06 | Connected target → identified Neyman-orthogonal CATE | Theorem 1, confirmed ✓ |
| 06 | Disconnected target → working-model screen-then-transport under A6 | Theorem 2 + A6, confirmed ✓ |
| 10 | A6 callout: screen-then-transport supports scenario analysis, not identification | Correct and appropriately caveated ✓ |
| 11 | "Interpret under the working transport condition" on IHDP disconnected | Correct repetition of A6 caveat ✓ |

---

## Regime Distinction Audit

This is the most methodologically critical aspect of the talk. Assessment by slide:

| Slide | Regime handling |
|-------|----------------|
| 06 | Explicit two-column Connected/Disconnected split with "What to say" note on identification vs. transport — correct |
| 07 | No regime reference needed (evaluation setup slide) — OK |
| 08 | Shows Proposed-B alongside Proposed/Proposed-CF without labeling it as disconnected-only — **minor gap**: a listener who hasn't retained Slide 06 may not know Proposed-B operates on a different estimand |
| 09 | Connected regime only (m₁ > 0) — no regime label, but slide context makes this clear |
| 10 | A6 callout explicitly labels disconnected regime — correct |
| 11 | "Interpret under the working transport condition" on disconnected card — correct |

**Recommendation for Slide 08:** Add "(disconnected)" in small text beside Proposed-B in the bar chart, matching the regime framing established on Slide 06. This is a 2-word fix with high payoff.

---

## Method Description Accuracy (Slides 04–05)

All four conceptual steps on Slide 04 and the four pipeline steps on Slide 05 are technically accurate against Sections 2.2 and 3 of the paper. The only technical imprecision is the Step 4 / Slide 05 issue noted in m3 above. The claim that propensities are "known by design" (Slide 05, Step 1) correctly reflects Assumption A2 and is worth emphasizing verbally as a structural advantage over observational transport.

---

## Priority Summary

| ID | Slide | Issue | Severity | Action |
|----|-------|-------|----------|--------|
| M1 | 08 | Proposed-B avg rank 2.8 is not reproducible; correct value ~3.3 | **Major** | Fix number or add ATE disclosure |
| M2 | 08 | AnchorOnly and EntropyBal silently omitted | **Major** | Add disclosure footnote or include in chart |
| m1 | 08 | Dual "1.3" callouts ambiguous across methods | Minor | Differentiate labels |
| m2 | 12 | Closing slide text too small for auditorium | Minor | Increase font size |
| m3 | 05 | Step 4 conflates estimation with evaluation | Minor | Optional verbal clarification |
| — | 08 | Add "(disconnected)" label to Proposed-B bar | Minor | 2-word fix |
