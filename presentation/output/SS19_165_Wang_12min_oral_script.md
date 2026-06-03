# SS19_165_Wang 12-Minute Oral Presentation Script

Source deck: `SS19_165_Wang.pptx`  
Main talk scope: slides 1-19 only. Slides 20-49 are appendix/Q&A backup.  
Target duration: 12:00. The slide timing pills in the deck are calibrated to a longer 15-minute arc, so this script compresses the main story.

## Timing Map

| Slide | Target time | Purpose |
|---|---:|---|
| 1 | 0:00-0:20 | Title and one-sentence problem |
| 2 | 0:20-0:55 | Why target applicability is hard |
| 3 | 0:55-1:25 | Clinical trial evidence problem |
| 4 | 1:25-2:05 | Standard transport gap |
| 5 | 2:05-2:35 | Core idea: placebo as calibration |
| 6 | 2:35-3:00 | Proxy-gold framing |
| 7 | 3:00-3:20 | Sparse correction bridge |
| 8 | 3:20-3:45 | Connected vs placebo-only scenarios |
| 9 | 3:45-4:25 | Pipeline overview |
| 10 | 4:25-5:10 | Stage 1: sparse transfer |
| 11 | 5:10-5:55 | Stage 2: DR CATE learning |
| 12 | 5:55-6:35 | Regime-specific interpretation |
| 13 | 6:35-7:05 | Evaluation setup |
| 14 | 7:05-7:40 | Synthetic ablation/ranking summary |
| 15 | 7:40-8:25 | Connected finite-sample result |
| 16 | 8:25-9:05 | Why the method helps |
| 17 | 9:05-9:50 | Robustness and limits |
| 18 | 9:50-10:50 | IHDP benchmark |
| 19 | 10:50-12:00 | Takeaways and Q&A transition |

## Slide-By-Slide Script

### Slide 1 - Title

Good morning. I am Zilong Wang from Georgia Tech, and this work is about transfer learning for meta-analysis under covariate shift.

The short version is this: clinical trial evidence is often abundant, but not in the exact population where decisions are made. We use source trials as a high-volume proxy signal, and target placebo outcomes as the gold calibration signal for target-specific treatment effects.

### Slide 2 - How applicable are other RCT site results to the target site?

The motivating question is simple: if another trial site observed a treatment effect, how applicable is that result to my target site?

That question is difficult because RCT sites can enroll very different patients. Eligibility, geography, baseline risk, and case mix can all shift. Even if treatment is randomized within each site, the target population may not look like the source population.

For clinical decisions, we usually need more than a marginal average effect. We need patient-level CATEs, rankings for targeting, regret for treatment rules, and calibrated local predictions.

### Slide 3 - Potential problems

There are three linked problems.

First, pooling can estimate the wrong population if source patients and target patients differ. Second, a shared placebo or comparator arm is not automatically exchangeable when baseline risk drifts. Third, an average treatment effect may not answer the operational question, which is often: who should be treated in this target cohort?

So the paper asks whether transfer can be calibrated to the target population in a way that supports individualized decisions.

### Slide 4 - The gap

Standard transport and IPD network meta-analysis usually need two conditions.

One is network connectivity: the target trial should connect to the evidence network through a shared comparator arm. The other is shared-comparator comparability: after adjustment, comparator arms should be exchangeable.

Those are exactly the conditions that become fragile here. The target may be weakly connected, or placebo-only for the treatment of interest. Even when a placebo arm exists, residual baseline drift can make direct transfer biased.

That is the methodological gap: we want calibrated patient-level CATEs under covariate shift, including settings where the target evidence is weakly connected or disconnected.

### Slide 5 - Core idea 1

The core idea is to treat the target placebo arm as the calibration signal.

Source trial outcomes are abundant, so they are useful for learning low-variance outcome models. But they can be miscalibrated for the target population. Target placebo outcomes are scarce, but they reveal the target site's baseline risk directly.

So we use source data as the proxy signal and target placebo outcomes as the gold signal for baseline risk. The sparse correction bridges those two.

### Slide 6 - Core idea 2

This is the proxy-gold transfer learning view.

The source and target tasks share a feature space, but the source outcome model may be shifted away from the target outcome model. The key assumption is not that sites are identical. It is that the correction needed to move from proxy to gold is lower complexity than the full outcome model.

That is what makes small target placebo samples useful: they learn the correction, not the whole model.

### Slide 7 - Target placebo as gold calibration

Said another way, placebo outcomes at the target site are not just another control group. They are the anchor for the target population.

They tell us how baseline risk behaves locally. Once we correct the source-based placebo model to match that local baseline risk, the downstream CATE learner starts from a better-calibrated outcome model.

This is why the method is "placebo anchored" rather than just pooled transfer.

### Slide 8 - Connected vs placebo-only scenarios

There are two target scenarios.

In the connected case, the target has both placebo and treated outcomes, even if the treated sample is small. Then we can estimate a target-site CATE with target identification and use the source data to stabilize nuisance estimation.

In the placebo-only case, treated target outcomes are unavailable. Then the target CATE is not identified from target data alone. In that regime, the method becomes a screen-then-transport procedure under an explicit working transport assumption.

That distinction is important for everything that follows.

### Slide 9 - Estimator pipeline

The estimator has two layers.

First, fit source outcome models using abundant source IPD. Second, use target placebo residuals as gold labels and learn a sparse correction for target baseline risk. Third, form doubly robust pseudo-outcomes. Fourth, regress those pseudo-outcomes on covariates to estimate tau_hat of x.

Conceptually, Bastani and Tian-Feng supply the sparse proxy-gold anchoring layer, while Kennedy's DR learner supplies the orthogonal CATE layer.

### Slide 10 - Stage 1: Anchor + Sparse Transfer

Stage 1 is the anchoring step.

For each treatment arm, we start with source outcome models learned through glmtrans. Because these are randomized trials, the propensity is known by design.

For the placebo arm, we look at target placebo residuals: what does the source placebo model get wrong locally? A LASSO correction learns a low-complexity adjustment, producing an anchored baseline risk model.

Target placebo data are used where they are most informative: correcting baseline risk, rather than relearning every coefficient from a small sample.

### Slide 11 - Stage 2: Doubly Robust CATE Estimation

Stage 2 turns the anchored outcome models into CATE estimates.

We build doubly robust pseudo-outcomes using the anchored control model, the treated outcome model, and the known randomized propensity. With cross-fitting, each pseudo-outcome uses nuisance models trained out of fold, reducing overfitting bias.

Then we regress the pseudo-outcomes on covariates to estimate heterogeneous effects. This is the step that moves from calibrated outcome prediction to patient-level treatment-effect learning.

That is why we evaluate ranking, regret, and calibration, not only prediction error.

### Slide 12 - Two target regimes

The guarantees are different in the two regimes.

In the connected target case, where treated and placebo target outcomes are available, the estimator targets an identified target-site CATE. Theorem 1 gives a Neyman-orthogonal expansion, with the known randomized propensity playing an important role.

In the disconnected case, where the target has placebo only, we should not call the result identified. Proposed-B screens source trials using target placebo compatibility, then transports a source-learned CATE under Assumption A6.

So the honest language is: connected estimates are identified target CATEs; disconnected estimates are working-model transport analyses.

### Slide 13 - Evaluation setup

The experiments are designed around that same distinction.

We evaluate connected and disconnected target regimes. We compare against TargetOnly, ProxyOnly, transport baselines, EntropyBal, AnchorOnly, Proposed, Proposed-CF, and Proposed-B.

The metrics cover three goals: accuracy through PEHE and ATE error; targeting through Spearman rank correlation and policy regret; and trust through calibration slope, R-squared, and expected calibration error.

This matters because a clinically useful CATE model should not only be numerically close. It should rank patients well and support good treatment decisions.

### Slide 14 - Ablation and benchmark summary

Across synthetic sweeps, the proposed methods dominate the ranking table.

Proposed has the best average rank across PEHE, ATE error, Spearman, and regret. Proposed-CF leads the calibration metrics, especially expected calibration error.

The plug-in Proposed estimator is strongest for pointwise CATE accuracy, while the cross-fitted DR version trades a bit of finite-sample PEHE for better calibration.

So Proposed is preferred for pointwise accuracy; Proposed-CF is preferred when calibration or inference is central.

### Slide 15 - Connected targets

The clearest deployment case is small target sample size and high dimension.

At target budget m0=150 and m1=100, TargetOnly worsens quickly as p grows. At p=20, PEHE drops from 2.60 for TargetOnly to 0.50 for Proposed-CF. At p=50, it drops from 4.75 to 0.73 for Proposed. At p=100, it drops from 7.57 to 1.71.

That is the finite-sample message: when target IPD is expensive and p is large, anchored transfer stabilizes the CATE learner.

### Slide 16 - Why the method helps

The ablation explains why this is not generic pooling.

TargetOnly has no transfer, so it has high variance when target treated labels are scarce. ProxyOnly transfers from sources but does not anchor, so it can be biased under covariate shift. AnchorOnly isolates the value of target placebo correction. Proposed and Proposed-CF add the DR CATE learner on top of that anchored baseline.

So the improvement comes from the sequence: use target placebo to correct source models, then use orthogonalized CATE learning for the treatment-effect layer.

### Slide 17 - Robustness

The robustness results show both the strength and the boundary of the method.

As the number of source sites increases from 2 to 50, Proposed stays around PEHE 0.84 to 0.66 at the scarce target budget, while TargetOnly remains near 5. Source diversity helps when it is anchored to the target.

When the A5 sparse-shift approximation holds, Proposed-CF is around 0.38 PEHE. As sparsity and nonlinearity violations increase, performance degrades gradually.

The limit is also clear: if the target-source correction is dense or highly nonlinear, the strongest gains shrink.

### Slide 18 - IHDP benchmark

The IHDP benchmark checks the same ideas using real baseline covariates and semi-synthetic outcomes.

In the connected regime, Proposed is strongest across the PEHE cells. At m0=25 and m1=100, Proposed has PEHE 1.57, compared with 2.05 for OM-Transport and 3.09 for TargetOnly.

In the disconnected regime, Proposed-B is competitive and strong for ranking, but the interpretation remains transport-based. At m0=25, Proposed-B has PEHE 2.11, compared with baselines in the 2.28 to 2.82 range.

So IHDP supports the same story: anchoring helps under real covariate shift, but disconnected targets must be labeled as transported rather than identified.

### Slide 19 - Takeaways

I want to leave you with three takeaways.

First, anchor to the target placebo arm. It is the scarce but high-fidelity signal for local baseline risk, and it makes source transfer more clinically meaningful.

Second, separate identified claims from transported claims. Connected targets support target-identified CATE estimation. Placebo-only targets support screen-then-transport analysis under explicit assumptions.

Third, evaluate decisions, not only error. For patient-level treatment effects, PEHE matters, but so do ranking, policy regret, and calibration.

Overall, the placebo-anchored view turns fragmented multi-trial evidence into calibrated patient-level predictions while making the transport assumptions visible. Thank you. I am happy to take questions.

## If Running Behind

If you are at slide 12 after 7:00, compress slides 13-18 as follows:

- Slide 13: "We evaluate connected and disconnected regimes against no-transfer, unanchored-transfer, transport, and ablation baselines using accuracy, targeting, regret, and calibration."
- Slides 14-16: "The synthetic result is that Proposed leads pointwise performance, Proposed-CF leads calibration, and the gain comes from anchoring plus DR learning rather than generic pooling."
- Slides 17-18: "Robustness and IHDP tell the same story: source diversity helps, A5 violations degrade smoothly, and disconnected results must remain transport-based."

Then spend the final 45-60 seconds on slide 19.

## Q&A Phrases

- If asked about disconnected targets: "The disconnected target CATE is not identified from target data alone. Proposed-B is a working-model screen-then-transport estimator under A6."
- If asked why placebo matters: "The target placebo arm directly reveals local baseline risk, so it is the gold calibration signal for the control outcome model."
- If asked why not pool sources: "Pooling reduces variance but can carry source bias into the target. The sparse correction uses target placebo residuals to remove the target-specific baseline drift."
- If asked about cross-fitting: "Cross-fitting makes pseudo-outcomes out-of-fold, reducing first-order overfitting bias in the DR learner."
- If asked which method to use: "Proposed is strongest for pointwise PEHE in these experiments; Proposed-CF is preferable when CATE calibration or inference is the priority."
