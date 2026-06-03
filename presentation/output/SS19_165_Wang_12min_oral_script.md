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

First, fit source outcome models using abundant source IPD. Second, use target placebo residuals as gold labels and learn a sparse correction for target baseline risk. Third, form doubly robust pseudo-outcomes. Fourth, regress those pseudo-outcomes on covariates to estimate $\widehat{\tau}(x)$.

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

The metrics cover three goals: accuracy through PEHE and ATE error; targeting through Spearman rank correlation and policy regret; and trust through calibration slope, $R^2$, and expected calibration error.

This matters because a clinically useful CATE model should not only be numerically close. It should rank patients well and support good treatment decisions.

### Slide 14 - Ablation and benchmark summary

Across synthetic sweeps, the proposed methods dominate the ranking table.

Proposed has the best average rank across PEHE, ATE error, Spearman, and regret. Proposed-CF leads the calibration metrics, especially expected calibration error.

The plug-in Proposed estimator is strongest for pointwise CATE accuracy, while the cross-fitted DR version trades a bit of finite-sample PEHE for better calibration.

So Proposed is preferred for pointwise accuracy; Proposed-CF is preferred when calibration or inference is central.

### Slide 15 - Connected targets

The clearest deployment case is small target sample size and high dimension.

At target budget $m_0=150$ and $m_1=100$, TargetOnly worsens quickly as $p$ grows. At $p=20$, PEHE drops from $2.60$ for TargetOnly to $0.50$ for Proposed-CF. At $p=50$, it drops from $4.75$ to $0.73$ for Proposed. At $p=100$, it drops from $7.57$ to $1.71$.

That is the finite-sample message: when target IPD is expensive and p is large, anchored transfer stabilizes the CATE learner.

### Slide 16 - Why the method helps

The ablation explains why this is not generic pooling.

TargetOnly has no transfer, so it has high variance when target treated labels are scarce. ProxyOnly transfers from sources but does not anchor, so it can be biased under covariate shift. AnchorOnly isolates the value of target placebo correction. Proposed and Proposed-CF add the DR CATE learner on top of that anchored baseline.

So the improvement comes from the sequence: use target placebo to correct source models, then use orthogonalized CATE learning for the treatment-effect layer.

### Slide 17 - Robustness

The robustness results show both the strength and the boundary of the method.

As the number of source sites increases from $2$ to $50$, Proposed stays around PEHE $0.84$ to $0.66$ at the scarce target budget, while TargetOnly remains near $5$. Source diversity helps when it is anchored to the target.

When the A5 sparse-shift approximation holds, Proposed-CF is around 0.38 PEHE. As sparsity and nonlinearity violations increase, performance degrades gradually.

The limit is also clear: if the target-source correction is dense or highly nonlinear, the strongest gains shrink.

### Slide 18 - IHDP benchmark

The IHDP benchmark checks the same ideas using real baseline covariates and semi-synthetic outcomes.

In the connected regime, Proposed is strongest across the PEHE cells. At $m_0=25$ and $m_1=100$, Proposed has PEHE $1.57$, compared with $2.05$ for OM-Transport and $3.09$ for TargetOnly.

In the disconnected regime, Proposed-B is competitive and strong for ranking, but the interpretation remains transport-based. At $m_0=25$, Proposed-B has PEHE $2.11$, compared with baselines in the $2.28$ to $2.82$ range.

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

## Expanded Q&A Bank

These are questions that can be answered directly from the paper and appendix. Use short answers first; go deeper only if the questioner asks for technical detail.

### Details About Compared Methods

**Q: What exactly is TargetOnly?**  
A: TargetOnly is a doubly robust learner trained only on target-site data. It uses target placebo and target treated outcomes to fit outcome models and compute DR pseudo-outcomes. It is the no-transfer baseline, so it is high variance when target labels are scarce.

Citation: Edward H. Kennedy (2023), "Towards optimal doubly robust estimation of heterogeneous causal effects"; Kennedy (2024), "Semiparametric doubly robust targeted double machine learning: a review."

Core equation, matching the paper's DR pseudo-outcome, Eq. (1):

$$
\psi_i =
\widehat{\mu}_1^{(-k)}(X_i)
- \widehat{\mu}_0^{(-k)}(X_i)
+ \frac{A_i-e(X_i)}{e(X_i)\{1-e(X_i)\}}
\left\{Y_i-\widehat{\mu}_{A_i}^{(-k)}(X_i)\right\}.
$$

**Q: What is ProxyOnly?**  
A: ProxyOnly pools source data to fit arm-specific outcome models and applies them directly to the target. It tests transfer without target anchoring. It can have low variance but is vulnerable to source-target bias under covariate shift.

Citation: internal baseline in this paper, conceptually contrasted with Hamsa Bastani (2021), "Predicting with proxies: Transfer learning in high dimension."

Core equation:

$$
\widehat{\tau}_{\mathrm{proxy}}(x)
= \widehat{\mu}^{\mathrm{proxy}}_1(x)
- \widehat{\mu}^{\mathrm{proxy}}_0(x).
$$

**Q: What do IPW-Transport and OM-Transport do?**  
A: IPW-Transport estimates a source-versus-target selection model and reweights source observations toward the target covariate distribution. OM-Transport fits source outcome models and averages predicted treatment effects over target covariates.

Citations: Daniel Westreich, Jessie K. Edwards, Catherine R. Lesko, Elizabeth Stuart, and Stephen R. Cole (2017), "Transportability of trial results using inverse odds of sampling weights"; Issa J. Dahabreh, Sarah E. Robertson, Eric J. Tchetgen Tchetgen, Elizabeth A. Stuart, and Miguel A. Hernan (2019), "Generalizing causal inferences from randomized trials: counterfactual and graphical identification."

IPW-style odds weight:

$$
\widehat{w}(x)=\frac{1-\widehat{s}(x)}{\widehat{s}(x)},
\qquad
\widehat{s}(x)=\Pr(S=\mathrm{source}\mid X=x).
$$

Outcome-model transport estimand:

$$
\widehat{\tau}_{\mathrm{OM}}
=
\frac{1}{m}
\sum_{i:S_i=0}
\left\{\widehat{g}_1(X_i)-\widehat{g}_0(X_i)\right\}.
$$

**Q: What is EntropyBal?**  
A: EntropyBal is entropy balancing for covariate shift. It chooses source weights that match target covariate moments, then uses those weights in outcome estimation.

Citation: Jens Hainmueller (2012), "Entropy balancing for causal effects: A multivariate reweighting method to produce balanced samples in observational studies."

Core optimization:

$$
\min_{\{w_i\}}
\sum_{i:S_i=1} w_i\log w_i
\quad
\text{s.t.}
\quad
\sum_{i:S_i=1} w_i X_i=\overline{X}_{\mathrm{target}},
\quad
\sum_{i:S_i=1} w_i=1.
$$

**Q: What is AnchorOnly?**  
A: AnchorOnly isolates the placebo-anchoring contribution. It uses target placebo residuals to correct source outcome models, but it does not include the full proposed transfer-plus-CATE pipeline performance.

Citations: Hamsa Bastani (2021), "Predicting with proxies: Transfer learning in high dimension"; Ye Tian and Yang Feng (2023), "Transfer learning under high-dimensional generalized linear models."

Core sparse correction equations from the paper's Stage 1:

$$
\widehat{w}^{\widehat{\mathcal A}_a}
\in
\arg\min_w
\left[
\sum_{c\in\{0\}\cup\widehat{\mathcal A}_a}
\sum_{i\in\mathcal D_{a,c}}
\left(Y_i-X_i^\top w\right)^2
+\lambda_w\|w\|_1
\right],
$$

$$
\widehat{\delta}_a
\in
\arg\min_\delta
\left[
\sum_{i\in\mathcal D_{a,0}}
\left\{Y_i-X_i^\top
\left(\widehat{w}^{\widehat{\mathcal A}_a}+\delta\right)\right\}^2
+\lambda_\delta\|\delta\|_1
\right],
$$

$$
\widehat{\beta}_a
=
\widehat{w}^{\widehat{\mathcal A}_a}
+\widehat{\delta}_a,
\qquad
\widehat{\mu}_a(x)=x^\top\widehat{\beta}_a.
$$

**Q: What is Proposed?**  
A: Proposed applies glmtrans separately to each arm with automatic source selection, then estimates CATE by the plug-in difference. In the experiments, it tends to be strongest for pointwise PEHE.

Citation: Ye Tian and Yang Feng (2023), "Transfer learning under high-dimensional generalized linear models."

Core equation:

$$
\widehat{\tau}(x)
=
\widehat{\mu}_1(x)-\widehat{\mu}_0(x).
$$

**Q: What is Proposed-CF?**  
A: Proposed-CF adds cross-fitted doubly robust pseudo-outcomes on top of the anchored outcome models. It is designed to reduce overfitting and improve calibration. In the experiments, it leads calibration metrics such as ECE.

Citations: Edward H. Kennedy (2023), "Towards optimal doubly robust estimation of heterogeneous causal effects"; Victor Chernozhukov, Denis Chetverikov, Mert Demirer, Esther Duflo, Christian Hansen, Whitney Newey, and James Robins (2018), "Double/debiased machine learning for treatment and structural parameters."

Paper Eq. (1), reused after anchoring:

$$
\widehat{\tau}_{\mathrm{DR}}(\cdot)
\approx
\mathbb E[\psi\mid X=\cdot].
$$

**Q: What is Proposed-B?**  
A: Proposed-B is the disconnected-regime variant for $m_1=0$. It uses target placebo data to screen compatible sources, learns a source-based DR CATE model, and transports that CATE model to the target under Assumption A6.

Citations: Ye Tian and Yang Feng (2023), "Transfer learning under high-dimensional generalized linear models"; Edward H. Kennedy (2023), "Towards optimal doubly robust estimation of heterogeneous causal effects."

Source-screening condition from the paper:

$$
\widehat{L}_0^{(c)}-\widehat{L}_0^{(0)}
\le
C_0\,\widehat{\sigma}.
$$

Transport step:

$$
\widehat{\tau}_{\mathrm{target}}(x)
:=
\widehat{\tau}^{\mathrm{src}}(x).
$$

**Q: Why use glmtrans?**  
A: glmtrans provides high-dimensional GLM transfer learning with automatic source detection. It is a natural match for the paper's sparse correction idea: use source data for variance reduction, then debias with target data.

Citation: Ye Tian and Yang Feng (2023), "Transfer learning under high-dimensional generalized linear models."

**Q: Why is known propensity important?**  
A: These are randomized-trial settings, so the propensity is known by design. That removes one nuisance estimation problem from the DR learner and strengthens the orthogonality argument.

Core point:

$$
e(X_i)=\Pr(A_i=1\mid X_i)
$$

is known by randomization rather than estimated from observational treatment assignment.

### Structural Assumptions For The Zero-Shot / Disconnected Regime

Here "zero-shot" means no target treated outcomes are used: $m_1=0$. The target has placebo outcomes only.

**Q: Is the target CATE identified in the zero-shot regime?**  
A: No. With target placebo data only, the target treatment effect is not identified from target data alone. Proposed-B is a working-model screen-then-transport estimator, not a design-based identified CATE estimator.

**Q: What does Assumption A6 require?**  
A: A6 requires that there exists a set of good source trials whose placebo outcome functions are close to the target on the target covariate support, and whose CATE functions are also close to the target. It also requires the placebo-screening step to select sources contained in that good set with high probability.

Paper form:

$$
\left\|\mu_{0,c}-\mu_{0,0}\right\|_{L_2(P_0)}
\le
\epsilon_0,
\qquad
\left\|\tau_c-\tau_0\right\|_{L_2(P_0)}
\le
\epsilon_\tau,
$$

for all $c\in\mathcal C_0^\star$, and

$$
\Pr\left(\widehat{\mathcal C}_0\subseteq\mathcal C_0^\star\right)
\ge
1-\eta.
$$

**Q: What are $\epsilon_0$ and $\epsilon_\tau$ in A6?**  
A: $\epsilon_0$ bounds placebo-model mismatch between a good source and the target. $\epsilon_\tau$ bounds CATE mismatch between a good source and the target. $\epsilon_\tau$ is the irreducible transport bias: more source data cannot remove it if the source CATE is structurally different from the target CATE.

**Q: Why can placebo screening help with treatment-effect transport?**  
A: It helps only under the working condition that placebo compatibility is informative about CATE compatibility. The method screens sources using target placebo outcomes because those are observed in the zero-shot target. A6 is the explicit assumption connecting that screen to CATE transport.

**Q: What happens if A6 fails?**  
A: If placebo-compatible sources have different treatment-effect functions from the target, Proposed-B can be biased. The paper labels this as structural transport bias rather than sampling error.

**Q: Is Proposed-B causal or predictive?**  
A: In the disconnected regime, it is causal only under explicit transport assumptions. The safest language is: "transport-based scenario analysis under A6," not "identified target causal effect."

**Q: Why is this still useful if it is not identified?**  
A: Many trial settings have a target placebo arm but no treated arm for the treatment of interest. Proposed-B gives a transparent way to use placebo information to screen sources and quantify where the remaining transport assumption enters.

**Q: How should I say this in the talk if challenged?**  
A: "I agree the disconnected CATE is not identified from target data alone. That is why we separate Option A and Option B. Option B estimates a working-model transported CATE, and Theorem 2 explicitly includes the structural transport bias term."

### Datasets And Evaluation Details

**Q: What synthetic data are used?**  
A: The synthetic DGP is a multi-center RCT design with explicit covariate shift. There are $C$ source sites plus one target site. Covariates follow site-specific normal distributions, with source-target overlap calibrated to about AUC $0.75$ for source-versus-target classification.

**Q: How many synthetic replicates are run?**  
A: All synthetic scenarios use $R=100$ Monte Carlo replicates.

**Q: What dimensions are tested?**  
A: The dimension sweep uses $p\in\{10,20,50,100\}$.

**Q: What target budgets are tested in the main dimension sweep?**  
A: The main PEHE table uses target budgets $50/0$, $150/100$, and $550/500$, where the notation is $m_0/m_1$: target placebo sample size / target treated sample size. The $50/0$ column is the disconnected, placebo-only setting.

**Q: How large are the synthetic source datasets?**  
A: In the main synthetic setup, source sites contribute $20{,}000$ total observations, typically $2{,}000$ per source site when $C=10$. In source-scaling sweeps, $C$ varies over $\{2,5,10,20,50\}$, with $1{,}000$ samples per site in the paper description.

**Q: What is varied in the A5 sensitivity experiment?**  
A: The A5 sensitivity varies sparsity ratio $s/p$ over $\{0.05,0.20,1.00\}$ in the table and nonlinearity $\Gamma$ over $\{0,0.5,1.0\}$. The strongest setting is sparse and linear; dense or nonlinear corrections weaken the advantage.

**Q: What metrics are reported?**  
A: PEHE for pointwise CATE accuracy, absolute ATE error for marginal accuracy, Spearman for ranking quality, policy regret for decision quality, and calibration metrics including slope, $R^2$, and ECE.

**Q: What is the IHDP benchmark?**  
A: IHDP is a semi-synthetic benchmark built from real baseline covariates from the Infant Health and Development Program. It has $25$ baseline features: $19$ binary and $6$ continuous. Outcomes are generated semi-synthetically, so ground-truth treatment effects are known.

Citation: Jennifer L. Hill (2011), "Bayesian nonparametric modeling for causal inference."

**Q: How is IHDP turned into a multi-site setting?**  
A: The paper partitions IHDP subjects into $C=6$ clusters using k-means on standardized covariates. One cluster is the target site and the remaining clusters are source sites, inducing real covariate shift.

**Q: How many IHDP realizations are used?**  
A: The IHDP experiments use $50$ standard NPCI-style realizations.

**Q: What IHDP budgets are evaluated?**  
A: The connected IHDP regime sweeps $m_0$ and $m_1$ over $\{25,50,100\}$. The disconnected IHDP regime sets $m_1=0$ and sweeps $m_0$ over $\{25,50,100,200\}$.

**Q: What is the headline IHDP result?**  
A: In connected IHDP, Proposed is best in all $9$ PEHE cells in the displayed table. At $m_0=25$ and $m_1=100$, Proposed has PEHE $1.57$ versus $2.05$ for OM-Transport and $3.09$ for TargetOnly. In disconnected IHDP at $m_0=25$, Proposed-B has PEHE $2.11$ versus baselines from $2.28$ to $2.82$.

### Theoretical Results: Technical Voice And Layman Voice

**Q: What is the technical statement of Theorem 1?**  
Technical voice: In the connected target regime, under A1-A3, bounded propensities, finite moments, cross-fitting, stable Gram conditions, and consistent nuisance outcome regressions, the cross-fitted DR CATE estimator is asymptotically linear:

$$
\sqrt{n_0}
\left\{
\widehat{\tau}_{\mathrm{DR}}(x)-\tau_0(x)
\right\}
\Rightarrow
N\left(0,V(x)\right).
$$

Layman voice: When the target has both placebo and treated patients, the method estimates a real target-population treatment effect. Because treatment is randomized and the nuisance models are cross-fitted, small errors in the first-stage outcome models do not dominate the final CATE estimate.

**Q: Why does Theorem 1 need cross-fitting?**  
Technical voice: Cross-fitting separates nuisance training from pseudo-outcome evaluation, so the nuisance error is independent of the held-out evaluation fold. This controls the empirical-process remainder and supports the asymptotic linear expansion.

Layman voice: We do not let the model grade its own homework. Each pseudo-outcome is built using models trained on other data, which reduces overfitting bias.

**Q: What is the role of known propensity in Theorem 1?**  
Technical voice: The propensity score $e_0(x)$ is known by randomization, so the usual product-error term involving propensity estimation disappears. This weakens the nuisance burden relative to observational settings.

Layman voice: Since the trial randomized treatment, we already know the treatment probability. That removes one major source of statistical uncertainty.

**Q: What is the technical statement of Theorem 2?**  
Technical voice: In the disconnected regime, $\tau_0$ is not identified from target data alone. Theorem 2 bounds the $L_2(P_0)$ error of Proposed-B by three terms:

$$
\left\|\widehat{\tau}_B-\tau_0\right\|_{L_2(P_0)}
\le
\left\|\widehat{\tau}_B-\tau^\star\right\|_{L_2(P_0)}
+\epsilon_\tau
+O_p\left(\eta^{1/2}\right).
$$

Layman voice: In a placebo-only target trial, the method cannot magically learn the target treatment effect. Its error comes from how well the source learner estimates effects, how different the source effects are from the target effects, and whether the placebo screen accidentally lets in bad sources.

**Q: What is the most important term in Theorem 2?**  
A: $\epsilon_\tau$. It is the structural CATE transport bias. If the selected source CATEs are far from the target CATE, adding more data cannot fix that; the transported estimand is simply centered on the wrong effect function.

**Q: How do Theorem 1 and Theorem 2 differ in one sentence?**  
Technical voice: Theorem 1 gives asymptotic linearity for an identified connected-target CATE; Theorem 2 gives an error decomposition for a non-identified disconnected-target transport estimator.

Layman voice: With target treated data, we estimate the target effect. Without target treated data, we transport an effect from compatible sources and explicitly track the assumption gap.

**Q: What is the theory behind the sparse correction?**  
Technical voice: The proxy-gold step assumes the source-target outcome contrast is low complexity, for example sparse in covariates. Source data estimate the proxy model with low variance; target placebo residuals estimate the sparse correction. This lets the target sample focus on the lower-dimensional bias rather than the full regression function:

$$
\mu_{a,c}(x)
=
\mu^{\mathrm{proxy}}_a(x)
+\delta_{a,c}(x),
\qquad
\delta_{a,c}\in\mathcal D.
$$

Layman voice: The source model is mostly right but locally miscalibrated. The target placebo data tell us which small set of adjustments fixes that miscalibration.

**Q: Does A5 identify the causal effect?**  
A: No. A5 is a regularity or approximation condition for stable transfer. It says the source-target correction is learnable with low complexity. Identification in connected targets comes from randomization and observing both arms in the target; disconnected targets still require A6 transport.

**Q: What should I say if someone asks whether the theory is too model-dependent?**  
A: "The method is intentionally explicit about where the model dependence enters. A5 is the sparse correction condition, and A6 is the disconnected transport condition. The connected case has an identified target estimand; the disconnected case is presented as transport under an assumption, not as nonparametric identification."

## Go Back To Slide X: Q&A Navigation

Use this section during Q&A when you want to return to a visible slide instead of answering from memory. The answer text below is pulled from the manuscript's introduction, assumptions, proposed framework, experiments, IHDP section, and conclusion.

### Go Back To Slide 4 - Why Isn't Standard IPD-NMA Enough?

**Likely question:** "How is this different from standard IPD network meta-analysis or transportability?"

Technical voice: Standard IPD-NMA relies on network connectivity and shared-comparator comparability. The manuscript states that the target trial may be disconnected, for example placebo-only for the treatment of interest, and comparator arms may differ in baseline risk under covariate shift. Standard transport or NMA often returns network-wide or marginal estimands, while this paper targets patient-level CATEs and calibrated target-specific predictions.

Layman voice: Existing meta-analysis tools work best when the evidence network is connected and comparable. Our hard case is when the target population is shifted or only has placebo data. Then we need to calibrate source evidence to the target before making patient-level decisions.

### Go Back To Slides 5-7 - Why Is Target Placebo The Gold Signal?

**Likely question:** "Why do you call the target placebo arm gold?"

Technical voice: In the manuscript's proxy-gold setup, source IPD provides abundant but potentially biased proxy labels, while target placebo outcomes directly reveal the target baseline risk distribution. The target placebo arm estimates the target control outcome function $\mu_{0,0}(x)$ locally, which is exactly where source outcome models can be miscalibrated.

Layman voice: The source trials give us lots of data, but from the wrong population. The target placebo arm gives us fewer outcomes, but from exactly the population we care about. That makes it the calibration anchor.

### Go Back To Slide 6 - What Is The Proxy-Gold Assumption?

**Likely question:** "What is the structural assumption behind proxy-gold transfer?"

Technical voice: The manuscript's A5 condition says that source-target outcome differences can be represented by a low-complexity correction:

$$
\mu_{a,c}(x)=\mu_a^{\mathrm{proxy}}(x)+\delta_{a,c}(x),
\qquad
\delta_{a,c}\in\mathcal D.
$$

The assumption is not that source and target outcomes are identical. It is that the contrast $\delta_{a,c}$ is easier to learn than the full outcome regression.

Layman voice: We do not assume the source model is perfectly right. We assume it is close enough that the target placebo data only need to learn the adjustment.

### Go Back To Slides 9-10 - Where Does The Sparse Correction Enter?

**Likely question:** "Where exactly does the method anchor the source model to target data?"

Technical voice: The anchoring occurs in Stage 1. After source detection, the method fits a pooled transfer model and then debiases it using target arm-specific data:

$$
\widehat{\beta}_a
=
\widehat{w}^{\widehat{\mathcal A}_a}
+\widehat{\delta}_a,
\qquad
\widehat{\mu}_a(x)=x^\top\widehat{\beta}_a.
$$

For the placebo arm, $\widehat{\delta}_0$ is learned from target placebo residuals, so the baseline risk model is explicitly calibrated to the target.

Layman voice: First we learn a strong source model. Then we ask: what does this model get wrong in the target placebo patients? The answer becomes the correction.

### Go Back To Slide 10 - What Happens If No Source Is Transferable?

**Likely question:** "Can the method protect against negative transfer?"

Technical voice: The manuscript states that when no sources pass detection, the algorithm reduces to target-only LASSO. Source detection compares cross-validated target loss after pooling a candidate source against target-only loss. A source is used only if

$$
\widehat L_0^{(c)}-\widehat L_0^{(0)}
\le
C_0\widehat\sigma.
$$

Layman voice: If a source looks harmful on target validation data, the method does not force it in. It falls back toward target-only learning.

### Go Back To Slide 11 - What Does The DR Layer Add?

**Likely question:** "Why do you need a doubly robust CATE learner after anchoring?"

Technical voice: Anchoring improves the outcome nuisance models, especially the baseline risk model. The DR layer then forms pseudo-outcomes:

$$
\psi_i =
\widehat{\mu}_1^{(-k)}(X_i)
-\widehat{\mu}_0^{(-k)}(X_i)
+\frac{A_i-e(X_i)}{e(X_i)\{1-e(X_i)\}}
\left\{Y_i-\widehat{\mu}_{A_i}^{(-k)}(X_i)\right\},
$$

and estimates

$$
\widehat\tau_{\mathrm{DR}}(x)\approx \mathbb E[\psi\mid X=x].
$$

Because treatment is randomized, $e(X)$ is known by design, which strengthens the DR construction.

Layman voice: The anchor fixes the baseline-risk model. The DR step then turns corrected outcome predictions plus randomized trial residuals into patient-level treatment effects.

### Go Back To Slide 12 - Are Connected And Disconnected Results The Same Claim?

**Likely question:** "Can you claim identification in the placebo-only regime?"

Technical voice: No. The manuscript explicitly separates connected and disconnected regimes. When $m_1>0$, Option A targets an identified target-site CATE. When $m_1=0$, Option B / Proposed-B is a screen-then-transport working-model estimator under A6, and the target CATE is not identified from target data alone.

Layman voice: With target treated patients, we estimate the target effect. With target placebo only, we transport from compatible sources and clearly label the assumption.

### Go Back To Slide 12 - What Exactly Does A6 Buy You?

**Likely question:** "What is the key zero-shot assumption?"

Technical voice: A6 says there is a good source set $\mathcal C_0^\star$ with both placebo compatibility and CATE proximity on the target covariate support:

$$
\|\mu_{0,c}-\mu_{0,0}\|_{L_2(P_0)}\le\epsilon_0,
\qquad
\|\tau_c-\tau_0\|_{L_2(P_0)}\le\epsilon_\tau,
$$

and the screen selects within that set with probability at least $1-\eta$. This gives the Theorem 2 decomposition into estimation error, structural transport bias, and screening error.

Layman voice: A6 says: the placebo screen must identify sources whose placebo outcomes look like the target and whose treatment effects are also close enough to transport.

### Go Back To Slide 13 - Why These Evaluation Metrics?

**Likely question:** "Why not just report PEHE or ATE error?"

Technical voice: The manuscript evaluates PEHE, ATE error, Spearman rank correlation, policy regret, and CATE calibration. PEHE measures pointwise CATE error:

$$
\mathrm{PEHE}
=
\left[
\frac{1}{n}\sum_{i=1}^n
\{\widehat\tau(X_i)-\tau(X_i)\}^2
\right]^{1/2}.
$$

But patient-level decision support also needs ranking quality, threshold-policy value, and calibration.

Layman voice: A model can have decent average error and still rank patients poorly. We evaluate whether it predicts effects accurately, ranks patients usefully, and supports better treatment decisions.

### Go Back To Slide 15 - When Does Transfer Pay Off Most?

**Likely question:** "What is the clearest finite-sample result?"

Technical voice: In the dimension sweep at target budget $m_0=150,m_1=100$, TargetOnly degrades as $p$ grows. The manuscript's Table II shows PEHE reductions from TargetOnly to Proposed or Proposed-CF: $2.60$ to $0.50$ at $p=20$, $4.75$ to $0.73$ at $p=50$, and $7.57$ to $1.71$ at $p=100$.

Layman voice: Transfer helps most when target data are scarce and the covariate dimension is large. That is exactly the setting where learning only from the target is unstable.

### Go Back To Slide 16 - Is The Gain Just More Data?

**Likely question:** "Is this just pooling source data?"

Technical voice: No. ProxyOnly tests unanchored pooling and performs worse under covariate shift. AnchorOnly isolates the target-placebo correction. Proposed and Proposed-CF combine target-placebo anchoring with the CATE learner. The ablation logic separates variance reduction from calibration and orthogonalization.

Layman voice: More source data helps only if it is corrected to the target. The method is not "just pool everything"; it is "pool, anchor, then learn effects."

### Go Back To Slide 17 - What Happens When A5 Is Violated?

**Likely question:** "How fragile is the sparse correction assumption?"

Technical voice: The manuscript varies sparsity ratio $s/p$ and nonlinearity $\Gamma$. When sparse linear shift holds, Proposed-CF is around PEHE $0.38$. As the correction becomes denser or more nonlinear, PEHE increases gradually rather than failing catastrophically. This supports the claim that the method degrades smoothly toward transport/proxy baselines.

Layman voice: The method works best when the target-source correction is simple. If the correction gets complicated, performance gets worse, but it does not suddenly collapse.

### Go Back To Slide 18 - What Makes IHDP A Useful Check?

**Likely question:** "Synthetic data can be tuned. What does IHDP add?"

Technical voice: IHDP uses real baseline covariates with semi-synthetic outcomes and known potential outcomes. The manuscript constructs $C=6$ sites by k-means clustering standardized covariates, then evaluates $50$ NPCI-style realizations. This preserves real covariate structure while retaining ground truth for PEHE, ranking, regret, and calibration.

Layman voice: IHDP gives us real patient covariates but known treatment effects. It is a more realistic stress test than fully synthetic data.

### Go Back To Slide 18 - How Should We Interpret Disconnected IHDP?

**Likely question:** "If IHDP has known outcomes, why call disconnected results non-identified?"

Technical voice: Ground truth is known for evaluation, but the training data in the disconnected experiment mask target treated outcomes and use only target placebo outcomes for source screening. Therefore the estimator is still in the $m_1=0$ training regime and should be interpreted under A6, not as target-identified.

Layman voice: We hide the target treated outcomes while training, then use them only to score the method afterward. So the method still faces the same placebo-only information problem.

### Go Back To Slide 19 - What Are The Main Limitations?

**Likely question:** "What are the next steps or limitations?"

Technical voice: The manuscript conclusion names several directions: diagnostics and sensitivity analysis for A6, extension beyond GLMs to survival or time-to-event endpoints, richer nuisance learners, better screening such as multi-endpoint screening or representation learning, and uncertainty quantification in small-gold regimes.

Layman voice: The biggest future need is knowing when the disconnected transport assumption is credible. We also want survival outcomes, richer models, better source screening, and better uncertainty intervals when target placebo data are small.
