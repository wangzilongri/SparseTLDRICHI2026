# Fair OptionB evaluation: m₀ × m₁ grid with controlled DGP

**Benchmark ID:** `gold_fair_sweep`

**Generated:** 2026-02-05 12:51

---

## 1. Motivation

**Research Question:** How does OptionB (ProposedB_SourceDR) perform when its assumptions are *approximately satisfied*?

**Why This Matters:**
- Previous sweeps used adversarial DGP settings (SNR < 1, AUC = 1.0, high drift)
- This led to "catastrophic failure" for OptionB that was structurally guaranteed
- This sweep uses **fair settings** where OptionB assumptions hold:
  - SNR ≥ 2 (cross-arm transfer signal present)
  - Overlap AUC ~ 0.75 (moderate, not degenerate)
  - Intercept drift controlled (σ_α = 0.5)

**Expected Behavior:**
- **ProposedB_SourceDR** should show moderate performance (not catastrophic failure)
- At m₁ = 0, ProposedB_SourceDR is the only Proposed variant that works
- As m₁ increases, ProposedA should outperform ProposedB variants
- The gap between ProposedA and ProposedB_SourceDR reflects the value of target treated data

---

## 2. Simulation Setup

**Fair DGP for OptionB Evaluation:**

Uses `FairSyntheticRCTConfig` with advisor-recommended settings:

**Cross-arm Transfer (A6):**
- `nontransfer_scale_target = 0.1` → SNR ≈ 3-4
- This means: ‖M*β₀‖ >> ‖ν‖ (transfer signal dominates)

**Covariate Overlap:**
- `overlap_lambda = 0.25` → AUC ≈ 0.75
- This means: Source models can generalize to target (not pure extrapolation)

**Intercept Drift:**
- `intercept_drift_scale = 0.5` → σ_α = 0.5
- This means: Arm means are stable across replications

**Outcome Model:**
$$\mu_{a,c}(x) = \alpha_{a,c} + x^\top b_a + x^\top \beta_{a,c} + \text{nonlin}(x)$$

where $\beta_{1,c} = M^* \beta_{0,c} + \nu_c$ with small $\nu_c$.

### Parameter Summary

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Sweep param** | `m0` | [100, 500, 1000] |
| n_proxy_total | 20000 | Total source/proxy observations |
| C_sources | 10 | Number of source sites |
| nontransfer_scale | 0.1 | Scale of non-transferable component (σ) |
| use_fair_dgp | True | See documentation |
| overlap_lambda | 0.25 | See documentation |
| intercept_drift_scale | 0.5 | See documentation |

---

## 3. Metrics & Interpretation

| Metric | Direction | Description |
|--------|-----------|-------------|
| **PEHE (Precision in Estimating Heterogeneous Effects)** | ↓ lower is better | Root mean squared error of CATE predictions. Measures how accurately the estimat... |
| **ATE Absolute Error** | ↓ lower is better | Absolute difference between estimated and true average treatment effect.... |
| **ATE Bias (Signed)** | ↑ closer to 0 is better | Signed bias in ATE estimate. Positive = overestimate, negative = underestimate.... |
| **Spearman Rank Correlation** | ↑ higher is better | Rank correlation between predicted and true treatment effects.... |
| **Kendall Rank Correlation** | ↑ higher is better | Kendall tau-b correlation. More robust to ties than Spearman.... |
| **Qini AUC (Oracle)** | ↑ higher is better | Area under the Qini curve. Measures ranking quality for treatment targeting.... |
| **Top-10% Uplift Capture Ratio** | ↑ higher is better | Fraction of maximum uplift captured when treating top 10% by predicted CATE.... |
| **Top-20% Uplift Capture Ratio** | ↑ higher is better | Fraction of maximum uplift captured when treating top 20% by predicted CATE.... |
| **Top-30% Uplift Capture Ratio** | ↑ higher is better | Fraction of maximum uplift captured when treating top 30%.... |
| **Calibration Slope** | ↑ closer to 1 is better | Slope of regression of true τ on predicted τ̂. Ideal = 1.0.... |
| **Calibration R²** | ↑ higher is better | Variance explained by predictions. Measures calibration quality.... |
| **CATE ECE (Expected Calibration Error)** | ↓ lower is better | Expected calibration error for CATE. Binned average miscalibration.... |
| **Policy Value (Treat if τ̂ > 0)** | ↑ higher is better | Expected outcome under threshold-based treatment policy.... |
| **Policy Regret vs Oracle** | ↓ lower is better | Gap between oracle policy value and estimated policy value.... |
| **Policy Value (Treat Top 20%)** | ↑ higher is better | Expected outcome when treating top 20% by predicted CATE.... |
| **Policy Regret (Top 20% Budget)** | ↓ lower is better | Regret compared to oracle top-20% policy.... |
| **μ₀ RMSE (Control Outcome)** | ↓ lower is better | RMSE of predicted control outcomes. Measures nuisance estimation quality.... |

### Detailed Metric Definitions

**PEHE (Precision in Estimating Heterogeneous Effects)**

- Formula: $\sqrt{\frac{1}{n}\sum_i (\hat{\tau}(x_i) - \tau(x_i))^2}$
- Direction: **lower is better**
- A PEHE of 0.5 means predictions are off by 0.5 units on average.

**ATE Absolute Error**

- Formula: $|\hat{\text{ATE}} - \text{ATE}|$
- Direction: **lower is better**
- Important for policy decisions about whether to adopt treatment broadly.

**ATE Bias (Signed)**

- Formula: $\hat{\text{ATE}} - \text{ATE}$
- Direction: **closer to 0 is better**
- Shows systematic over/under-estimation tendencies.

**Spearman Rank Correlation**

- Formula: $\rho(\text{rank}(\hat{\tau}), \text{rank}(\tau))$
- Direction: **higher is better**
- 1.0 = perfect ranking, 0.0 = random. Critical for targeting interventions.

**Kendall Rank Correlation**

- Formula: $\tau_K(\hat{\tau}, \tau)$
- Direction: **higher is better**
- Alternative ranking metric; useful when ties are common.

**Qini AUC (Oracle)**

- Formula: Normalized AUC of cumulative uplift curve
- Direction: **higher is better**
- 1.0 = oracle ranking, 0.0 = random. Simulation-only metric using true τ.

**Top-10% Uplift Capture Ratio**

- Formula: $\frac{\bar{\tau}_{top10\%\ by\ \hat{\tau}}}{\bar{\tau}_{top10\%\ by\ \tau}}$
- Direction: **higher is better**
- 1.0 = oracle selection. Measures targeting efficiency for top patients.

**Top-20% Uplift Capture Ratio**

- Formula: $\frac{\bar{\tau}_{top20\%\ by\ \hat{\tau}}}{\bar{\tau}_{top20\%\ by\ \tau}}$
- Direction: **higher is better**
- 1.0 = oracle selection. Less stringent than top-10%.

**Top-30% Uplift Capture Ratio**

- Formula: $\frac{\bar{\tau}_{top30\%\ by\ \hat{\tau}}}{\bar{\tau}_{top30\%\ by\ \tau}}$
- Direction: **higher is better**
- Less stringent targeting metric.

**Calibration Slope**

- Formula: $\beta$ in $\tau = \alpha + \beta \hat{\tau}$
- Direction: **closer to 1 is better**
- <1 = overconfident predictions, >1 = underconfident.

**Calibration R²**

- Formula: $R^2$ of calibration regression
- Direction: **higher is better**
- Higher R² means predictions track true effects well.

**CATE ECE (Expected Calibration Error)**

- Formula: $\sum_b \frac{n_b}{n} |E[\tau | \hat{\tau} \in b] - E[\hat{\tau} | \hat{\tau} \in b]|$
- Direction: **lower is better**
- Lower ECE means better calibration across prediction ranges.

**Policy Value (Treat if τ̂ > 0)**

- Formula: $E[\mu_0 + \pi(\hat{\tau}) \cdot \tau]$ where $\pi(\hat{\tau}) = 1\{\hat{\tau} > 0\}$
- Direction: **higher is better**
- Higher value = better treatment decisions based on predictions.

**Policy Regret vs Oracle**

- Formula: $V(\pi^*) - V(\hat{\pi})$
- Direction: **lower is better**
- Lower regret = closer to optimal treatment decisions.

**Policy Value (Treat Top 20%)**

- Formula: $E[\mu_0 + \pi_{top20\%}(\hat{\tau}) \cdot \tau]$
- Direction: **higher is better**
- Budget-constrained policy evaluation.

**Policy Regret (Top 20% Budget)**

- Formula: $V(\pi^*_{top20\%}) - V(\hat{\pi}_{top20\%})$
- Direction: **lower is better**
- Budget-constrained regret.

**μ₀ RMSE (Control Outcome)**

- Formula: $\sqrt{\frac{1}{n}\sum_i (\hat{\mu}_0(x_i) - \mu_0(x_i))^2}$
- Direction: **lower is better**
- Important diagnostic; poor μ₀ estimation can propagate to CATE errors.

---

## 4. Methods Compared

| Method | Uses Target Placebo | Uses Source Data | Description |
|--------|---------------------|------------------|-------------|
| **TargetOnlyDR** | ✗ | ✗ | See documentation |
| **ProxyOnly** | ✗ | ✓ | Uses only source data, ignores target |
| **AnchorOnly** | ✓ | ✗ | Uses only target placebo data |
| **AnchorPlugin** | ✗ | ✗ | See documentation |
| **ProposedA** | ✓ | ✓ | Proposed: separate proxy + separate correction (residual) |
| **ProposedA_Together** | ✗ | ✗ | Proposed: separate proxy + joint correction (residual) |
| **ProposedA_JointProxy** | ✗ | ✗ | Proposed: joint proxy + separate correction (residual) |
| **ProposedA_FullyJoint** | ✗ | ✗ | Proposed: joint proxy + joint correction (residual) |
| **ProposedA_Direct** | ✗ | ✗ | Proposed: separate + direct fitting |
| **ProposedA_Together_Direct** | ✗ | ✗ | Proposed: joint correction + direct fitting |
| **ProposedA_FullyDirect** | ✗ | ✗ | Proposed: fully joint + direct fitting |
| **ProposedA_NoCrossfit** | ✗ | ✗ | Proposed: residual, no cross-fitting |
| **ProposedA_Direct_NoCrossfit** | ✗ | ✗ | Proposed: direct, no cross-fitting |
| **ProposedA_Together_NoCrossfit** | ✗ | ✗ | Proposed: joint + no cross-fitting |
| **ProposedA_Together_Direct_NoCrossfit** | ✗ | ✗ | Proposed: joint + direct + no cross-fitting |
| **ProposedB_LinearStepB** | ✓ | ✓ | Proposed (Option B): placebo-anchored with linear Step B |
| **ProposedB_SourceDR** | ✗ | ✗ | Proposed (Option B): source-DR for placebo-only target |
| **IPWTransport** | ✗ | ✗ | See documentation |
| **EntropyBalancing** | ✗ | ✗ | See documentation |
| **OutcomeModelTransport** | ✗ | ✗ | See documentation |
| **DRLearner_PooledWithSite** | ✗ | ✗ | See documentation |
| **DRLearner_PooledNoSite** | ✗ | ✗ | See documentation |

---

## 5. Experiment Summary

- **Sweep parameter:** `m0` ∈ [100, 500, 1000]
- **Monte Carlo replicates:** 2 per scenario
- **Methods evaluated:** 22
- **Total runs:** 528

---

## 6. Results

### Best Methods (averaged across sweep)

| Metric | Best Method | Value | Direction |
|--------|-------------|-------|----------|
| PEHE | **DRLearner_PooledWithSite** | 1.0945 | ↓ lower |
| ATE Error | **ProposedA_JointProxy** | 0.0200 | ↓ lower |
| Spearman ρ | **ProposedA_FullyJoint** | 0.3637 | ↑ higher |
| Kendall τ | **ProposedA_FullyJoint** | 0.2487 | ↑ higher |
| Qini AUC | **ProposedA_FullyJoint** | 0.3770 | ↑ higher |
| Top-10% Ratio | **ProposedA_FullyDirect** | 0.2321 | ↑ higher |
| Top-20% Ratio | **ProxyOnly** | 0.2822 | ↑ higher |
| Calibration R² | **ProposedA_FullyDirect** | 0.0382 | ↑ higher |
| CATE ECE | **DRLearner_PooledWithSite** | 0.2336 | ↓ lower |
| Policy Value | **ProposedB_SourceDR** | 0.7720 | ↑ higher |
| Policy Regret | **DRLearner_PooledWithSite** | 0.0742 | ↓ lower |

### Core Metrics

| m0 | m1 | Method | PEHE (↓) | ATE Err (↓) | Spearman (↑) | Qini (↑) |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 2.458 ± 0.184 | 0.622 ± 0.026 | 0.803 ± 0.041 | 0.818 ± 0.039 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 2.064 ± 0.088 | 0.328 ± 0.050 | 0.863 ± 0.000 | 0.877 ± 0.002 |
| 100 | 0 | IPWTransport | 1.947 ± 0.018 | 0.367 ± 0.105 | 0.876 ± 0.009 | 0.890 ± 0.006 |
| 100 | 0 | OutcomeModelTransport | 1.889 ± 0.014 | 0.434 ± 0.143 | 0.884 ± 0.013 | 0.897 ± 0.010 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 3.253 ± 0.008 | 0.646 ± 0.614 | 0.636 ± 0.028 | 0.659 ± 0.021 |
| 100 | 0 | ProxyOnly | 3.706 ± 0.482 | 0.786 ± 0.613 | 0.476 ± 0.126 | 0.492 ± 0.124 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 3.439 ± 0.197 | 0.795 ± 0.531 | 0.653 ± 0.006 | 0.670 ± 0.002 |
| 100 | 100 | AnchorPlugin | 2.680 ± 0.083 | 0.660 ± 0.352 | 0.779 ± 0.083 | 0.791 ± 0.082 |
| 100 | 100 | DRLearner_PooledNoSite | 1.670 ± 0.360 | 0.073 ± 0.045 | 0.904 ± 0.062 | 0.912 ± 0.057 |
| 100 | 100 | DRLearner_PooledWithSite | 1.667 ± 0.357 | 0.067 ± 0.041 | 0.905 ± 0.062 | 0.913 ± 0.057 |
| 100 | 100 | EntropyBalancing | 1.707 ± 0.415 | 0.057 ± 0.023 | 0.900 ± 0.068 | 0.909 ± 0.063 |
| 100 | 100 | IPWTransport | 1.706 ± 0.399 | 0.104 ± 0.044 | 0.900 ± 0.067 | 0.909 ± 0.062 |
| 100 | 100 | OutcomeModelTransport | 1.687 ± 0.363 | 0.070 ± 0.043 | 0.903 ± 0.063 | 0.911 ± 0.058 |
| 100 | 100 | ProposedA | 3.373 ± 0.277 | 0.577 ± 0.450 | 0.660 ± 0.008 | 0.677 ± 0.010 |
| 100 | 100 | ProposedA_Direct | 3.325 ± 0.487 | 0.417 ± 0.270 | 0.690 ± 0.054 | 0.703 ± 0.049 |
| 100 | 100 | ProposedA_Direct_NoCrossfit | 3.337 ± 0.491 | 0.428 ± 0.318 | 0.682 ± 0.055 | 0.695 ± 0.052 |
| 100 | 100 | ProposedA_FullyDirect | 3.303 ± 0.296 | 0.365 ± 0.470 | 0.698 ± 0.033 | 0.714 ± 0.029 |
| 100 | 100 | ProposedA_FullyJoint | 3.317 ± 0.312 | 0.465 ± 0.422 | 0.681 ± 0.040 | 0.698 ± 0.036 |
| 100 | 100 | ProposedA_JointProxy | 3.353 ± 0.322 | 0.513 ± 0.411 | 0.671 ± 0.002 | 0.686 ± 0.004 |
| 100 | 100 | ProposedA_NoCrossfit | 3.366 ± 0.325 | 0.535 ± 0.442 | 0.659 ± 0.005 | 0.674 ± 0.006 |
| 100 | 100 | ProposedA_Together | 3.324 ± 0.315 | 0.476 ± 0.491 | 0.666 ± 0.022 | 0.684 ± 0.020 |
| 100 | 100 | ProposedA_Together_Direct | 3.303 ± 0.296 | 0.365 ± 0.470 | 0.698 ± 0.033 | 0.714 ± 0.029 |
| 100 | 100 | ProposedA_Together_Direct_NoCrossfit | 3.403 ± 0.358 | 0.337 ± 0.392 | 0.689 ± 0.040 | 0.705 ± 0.039 |
| 100 | 100 | ProposedA_Together_NoCrossfit | 3.344 ± 0.396 | 0.446 ± 0.398 | 0.678 ± 0.043 | 0.694 ± 0.042 |
| 100 | 100 | ProposedB_LinearStepB | 3.389 ± 0.220 | 0.665 ± 0.543 | 0.661 ± 0.026 | 0.675 ± 0.025 |
| 100 | 100 | ProposedB_SourceDR | 3.540 ± 0.252 | 1.259 ± 0.528 | 0.639 ± 0.016 | 0.660 ± 0.011 |
| 100 | 100 | ProxyOnly | 3.687 ± 0.454 | 0.999 ± 0.203 | 0.537 ± 0.009 | 0.559 ± 0.009 |
| 100 | 100 | TargetOnlyDR | 3.491 ± 0.178 | 0.732 ± 0.396 | 0.599 ± 0.030 | 0.618 ± 0.027 |
| 100 | 500 | AnchorOnly | 2.852 ± 0.252 | 0.177 ± 0.058 | 0.763 ± 0.004 | 0.779 ± 0.002 |
| 100 | 500 | AnchorPlugin | 2.218 ± 0.198 | 0.316 ± 0.047 | 0.821 ± 0.073 | 0.834 ± 0.066 |
| 100 | 500 | DRLearner_PooledNoSite | 1.642 ± 0.838 | 0.291 ± 0.108 | 0.879 ± 0.123 | 0.890 ± 0.113 |
| 100 | 500 | DRLearner_PooledWithSite | 1.663 ± 0.837 | 0.267 ± 0.046 | 0.876 ± 0.126 | 0.887 ± 0.116 |
| 100 | 500 | EntropyBalancing | 1.742 ± 0.908 | 0.296 ± 0.022 | 0.863 ± 0.142 | 0.874 ± 0.132 |
| 100 | 500 | IPWTransport | 1.713 ± 0.884 | 0.288 ± 0.060 | 0.868 ± 0.136 | 0.879 ± 0.126 |
| 100 | 500 | OutcomeModelTransport | 1.706 ± 0.858 | 0.297 ± 0.053 | 0.870 ± 0.132 | 0.881 ± 0.122 |
| 100 | 500 | ProposedA | 2.853 ± 0.234 | 0.176 ± 0.076 | 0.757 ± 0.006 | 0.773 ± 0.004 |
| 100 | 500 | ProposedA_Direct | 2.824 ± 0.201 | 0.169 ± 0.105 | 0.763 ± 0.009 | 0.777 ± 0.009 |
| 100 | 500 | ProposedA_Direct_NoCrossfit | 2.839 ± 0.154 | 0.168 ± 0.093 | 0.760 ± 0.006 | 0.775 ± 0.005 |
| 100 | 500 | ProposedA_FullyDirect | 3.684 ± 0.005 | 0.329 ± 0.249 | 0.565 ± 0.055 | 0.584 ± 0.052 |
| 100 | 500 | ProposedA_FullyJoint | 3.450 ± 0.066 | 0.228 ± 0.177 | 0.634 ± 0.020 | 0.650 ± 0.021 |
| 100 | 500 | ProposedA_JointProxy | 2.840 ± 0.202 | 0.122 ± 0.061 | 0.762 ± 0.009 | 0.778 ± 0.007 |
| 100 | 500 | ProposedA_NoCrossfit | 2.840 ± 0.208 | 0.174 ± 0.066 | 0.759 ± 0.002 | 0.774 ± 0.001 |
| 100 | 500 | ProposedA_Together | 3.236 ± 0.012 | 0.177 ± 0.110 | 0.651 ± 0.041 | 0.668 ± 0.039 |
| 100 | 500 | ProposedA_Together_Direct | 3.684 ± 0.005 | 0.329 ± 0.249 | 0.565 ± 0.055 | 0.584 ± 0.052 |
| 100 | 500 | ProposedA_Together_Direct_NoCrossfit | 3.707 ± 0.057 | 0.342 ± 0.259 | 0.557 ± 0.066 | 0.577 ± 0.063 |
| 100 | 500 | ProposedA_Together_NoCrossfit | 3.242 ± 0.006 | 0.193 ± 0.077 | 0.649 ± 0.046 | 0.666 ± 0.044 |
| 100 | 500 | ProposedB_LinearStepB | 2.868 ± 0.246 | 0.154 ± 0.067 | 0.751 ± 0.007 | 0.767 ± 0.006 |
| 100 | 500 | ProposedB_SourceDR | 3.125 ± 0.098 | 0.452 ± 0.212 | 0.637 ± 0.142 | 0.654 ± 0.137 |
| 100 | 500 | ProxyOnly | 6.003 ± 1.664 | 3.367 ± 1.299 | 0.406 ± 0.021 | 0.427 ± 0.026 |
| 100 | 500 | TargetOnlyDR | 3.134 ± 0.314 | 0.216 ± 0.208 | 0.685 ± 0.004 | 0.703 ± 0.003 |
| 100 | 1000 | AnchorOnly | 3.631 ± 0.094 | 0.095 ± 0.069 | 0.647 ± 0.077 | 0.665 ± 0.075 |
| 100 | 1000 | AnchorPlugin | 2.754 ± 0.816 | 0.023 ± 0.004 | 0.769 ± 0.135 | 0.782 ± 0.133 |
| 100 | 1000 | DRLearner_PooledNoSite | 1.799 ± 1.076 | 0.440 ± 0.011 | 0.901 ± 0.106 | 0.908 ± 0.099 |
| 100 | 1000 | DRLearner_PooledWithSite | 1.811 ± 1.079 | 0.376 ± 0.124 | 0.898 ± 0.111 | 0.905 ± 0.104 |
| 100 | 1000 | EntropyBalancing | 1.897 ± 1.096 | 0.498 ± 0.143 | 0.891 ± 0.120 | 0.899 ± 0.112 |
| 100 | 1000 | IPWTransport | 1.936 ± 1.124 | 0.535 ± 0.139 | 0.887 ± 0.126 | 0.895 ± 0.118 |
| 100 | 1000 | OutcomeModelTransport | 1.925 ± 1.137 | 0.437 ± 0.148 | 0.885 ± 0.126 | 0.893 ± 0.118 |
| 100 | 1000 | ProposedA | 3.643 ± 0.092 | 0.116 ± 0.086 | 0.642 ± 0.079 | 0.662 ± 0.079 |
| 100 | 1000 | ProposedA_Direct | 3.408 ± 0.058 | 0.106 ± 0.101 | 0.723 ± 0.033 | 0.739 ± 0.031 |
| 100 | 1000 | ProposedA_Direct_NoCrossfit | 3.383 ± 0.082 | 0.103 ± 0.065 | 0.727 ± 0.041 | 0.743 ± 0.039 |
| 100 | 1000 | ProposedA_FullyDirect | 5.379 ± 0.666 | 0.277 ± 0.366 | 0.381 ± 0.010 | 0.393 ± 0.023 |
| 100 | 1000 | ProposedA_FullyJoint | 5.062 ± 0.644 | 0.424 ± 0.372 | 0.364 ± 0.040 | 0.377 ± 0.048 |
| 100 | 1000 | ProposedA_JointProxy | 3.531 ± 0.039 | 0.068 ± 0.001 | 0.683 ± 0.031 | 0.699 ± 0.031 |
| 100 | 1000 | ProposedA_NoCrossfit | 3.467 ± 0.085 | 0.084 ± 0.000 | 0.682 ± 0.053 | 0.700 ± 0.049 |
| 100 | 1000 | ProposedA_Together | 4.900 ± 0.733 | 0.383 ± 0.359 | 0.449 ± 0.028 | 0.461 ± 0.017 |
| 100 | 1000 | ProposedA_Together_Direct | 5.379 ± 0.666 | 0.277 ± 0.366 | 0.381 ± 0.010 | 0.393 ± 0.023 |
| 100 | 1000 | ProposedA_Together_Direct_NoCrossfit | 5.223 ± 0.649 | 0.269 ± 0.342 | 0.394 ± 0.014 | 0.405 ± 0.029 |
| 100 | 1000 | ProposedA_Together_NoCrossfit | 4.853 ± 0.699 | 0.344 ± 0.326 | 0.448 ± 0.032 | 0.460 ± 0.024 |
| 100 | 1000 | ProposedB_LinearStepB | 3.622 ± 0.069 | 0.132 ± 0.057 | 0.649 ± 0.072 | 0.669 ± 0.071 |
| 100 | 1000 | ProposedB_SourceDR | 3.840 ± 0.445 | 0.440 ± 0.027 | 0.528 ± 0.156 | 0.544 ± 0.160 |
| 100 | 1000 | ProxyOnly | 9.373 ± 2.196 | 3.970 ± 3.182 | 0.401 ± 0.086 | 0.415 ± 0.090 |
| 100 | 1000 | TargetOnlyDR | 4.729 ± 0.328 | 0.409 ± 0.568 | 0.423 ± 0.065 | 0.440 ± 0.068 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 3.023 ± 0.765 | 0.737 ± 0.039 | 0.719 ± 0.146 | 0.734 ± 0.142 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 3.121 ± 1.297 | 0.209 ± 0.177 | 0.678 ± 0.237 | 0.691 ± 0.235 |
| 500 | 0 | IPWTransport | 3.106 ± 1.279 | 0.215 ± 0.155 | 0.681 ± 0.233 | 0.695 ± 0.231 |
| 500 | 0 | OutcomeModelTransport | 3.084 ± 1.264 | 0.199 ± 0.213 | 0.686 ± 0.229 | 0.699 ± 0.227 |
| 500 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 3.895 ± 0.838 | 0.747 ± 0.063 | 0.446 ± 0.300 | 0.463 ± 0.301 |
| 500 | 0 | ProxyOnly | 3.888 ± 0.465 | 1.600 ± 0.298 | 0.578 ± 0.161 | 0.597 ± 0.156 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 4.297 ± 0.362 | 0.690 ± 0.267 | 0.586 ± 0.112 | 0.606 ± 0.108 |
| 500 | 100 | AnchorPlugin | 3.129 ± 0.414 | 0.643 ± 0.676 | 0.774 ± 0.071 | 0.792 ± 0.071 |
| 500 | 100 | DRLearner_PooledNoSite | 2.336 ± 0.251 | 0.927 ± 0.469 | 0.887 ± 0.046 | 0.898 ± 0.040 |
| 500 | 100 | DRLearner_PooledWithSite | 2.297 ± 0.227 | 0.895 ± 0.480 | 0.891 ± 0.042 | 0.901 ± 0.037 |
| 500 | 100 | EntropyBalancing | 2.595 ± 0.332 | 1.033 ± 0.557 | 0.861 ± 0.067 | 0.874 ± 0.059 |
| 500 | 100 | IPWTransport | 2.578 ± 0.317 | 1.035 ± 0.576 | 0.864 ± 0.066 | 0.877 ± 0.058 |
| 500 | 100 | OutcomeModelTransport | 2.409 ± 0.199 | 1.012 ± 0.513 | 0.883 ± 0.044 | 0.895 ± 0.039 |
| 500 | 100 | ProposedA | 3.539 ± 0.170 | 0.259 ± 0.119 | 0.717 ± 0.013 | 0.738 ± 0.014 |
| 500 | 100 | ProposedA_Direct | 3.477 ± 0.090 | 0.187 ± 0.112 | 0.719 ± 0.019 | 0.742 ± 0.014 |
| 500 | 100 | ProposedA_Direct_NoCrossfit | 3.490 ± 0.104 | 0.200 ± 0.094 | 0.721 ± 0.006 | 0.743 ± 0.003 |
| 500 | 100 | ProposedA_FullyDirect | 4.935 ± 0.293 | 0.257 ± 0.226 | 0.455 ± 0.055 | 0.471 ± 0.053 |
| 500 | 100 | ProposedA_FullyJoint | 4.611 ± 0.250 | 0.416 ± 0.213 | 0.494 ± 0.037 | 0.510 ± 0.034 |
| 500 | 100 | ProposedA_JointProxy | 3.521 ± 0.129 | 0.304 ± 0.194 | 0.717 ± 0.007 | 0.738 ± 0.007 |
| 500 | 100 | ProposedA_NoCrossfit | 3.490 ± 0.153 | 0.274 ± 0.133 | 0.725 ± 0.028 | 0.746 ± 0.028 |
| 500 | 100 | ProposedA_Together | 4.317 ± 0.253 | 0.589 ± 0.208 | 0.555 ± 0.048 | 0.573 ± 0.040 |
| 500 | 100 | ProposedA_Together_Direct | 4.935 ± 0.293 | 0.257 ± 0.226 | 0.455 ± 0.055 | 0.471 ± 0.053 |
| 500 | 100 | ProposedA_Together_Direct_NoCrossfit | 4.916 ± 0.305 | 0.259 ± 0.256 | 0.459 ± 0.052 | 0.475 ± 0.052 |
| 500 | 100 | ProposedA_Together_NoCrossfit | 4.274 ± 0.214 | 0.587 ± 0.204 | 0.556 ± 0.036 | 0.573 ± 0.028 |
| 500 | 100 | ProposedB_LinearStepB | 3.453 ± 0.125 | 0.234 ± 0.144 | 0.745 ± 0.017 | 0.765 ± 0.017 |
| 500 | 100 | ProposedB_SourceDR | 4.251 ± 0.124 | 1.287 ± 1.403 | 0.585 ± 0.050 | 0.608 ± 0.052 |
| 500 | 100 | ProxyOnly | 3.912 ± 0.262 | 0.413 ± 0.351 | 0.621 ± 0.066 | 0.643 ± 0.069 |
| 500 | 100 | TargetOnlyDR | 4.302 ± 0.392 | 0.591 ± 0.424 | 0.545 ± 0.068 | 0.565 ± 0.063 |
| 500 | 500 | AnchorOnly | 3.403 ± 0.613 | 0.149 ± 0.196 | 0.799 ± 0.012 | 0.811 ± 0.012 |
| 500 | 500 | AnchorPlugin | 2.765 ± 0.589 | 0.513 ± 0.464 | 0.847 ± 0.002 | 0.857 ± 0.001 |
| 500 | 500 | DRLearner_PooledNoSite | 2.394 ± 0.142 | 0.774 ± 0.803 | 0.894 ± 0.015 | 0.902 ± 0.011 |
| 500 | 500 | DRLearner_PooledWithSite | 2.391 ± 0.157 | 0.782 ± 0.797 | 0.895 ± 0.013 | 0.902 ± 0.009 |
| 500 | 500 | EntropyBalancing | 2.583 ± 0.014 | 0.898 ± 0.993 | 0.880 ± 0.020 | 0.888 ± 0.016 |
| 500 | 500 | IPWTransport | 2.583 ± 0.011 | 0.903 ± 1.018 | 0.881 ± 0.019 | 0.889 ± 0.015 |
| 500 | 500 | OutcomeModelTransport | 2.560 ± 0.071 | 0.893 ± 0.958 | 0.882 ± 0.015 | 0.891 ± 0.012 |
| 500 | 500 | ProposedA | 3.438 ± 0.586 | 0.244 ± 0.150 | 0.796 ± 0.035 | 0.806 ± 0.033 |
| 500 | 500 | ProposedA_Direct | 3.440 ± 0.566 | 0.214 ± 0.146 | 0.794 ± 0.029 | 0.805 ± 0.027 |
| 500 | 500 | ProposedA_Direct_NoCrossfit | 3.442 ± 0.569 | 0.214 ± 0.142 | 0.795 ± 0.029 | 0.806 ± 0.029 |
| 500 | 500 | ProposedA_FullyDirect | 3.436 ± 0.555 | 0.206 ± 0.175 | 0.792 ± 0.026 | 0.804 ± 0.026 |
| 500 | 500 | ProposedA_FullyJoint | 3.439 ± 0.586 | 0.241 ± 0.142 | 0.793 ± 0.030 | 0.803 ± 0.029 |
| 500 | 500 | ProposedA_JointProxy | 3.424 ± 0.591 | 0.246 ± 0.122 | 0.800 ± 0.034 | 0.810 ± 0.033 |
| 500 | 500 | ProposedA_NoCrossfit | 3.443 ± 0.588 | 0.231 ± 0.142 | 0.796 ± 0.035 | 0.806 ± 0.033 |
| 500 | 500 | ProposedA_Together | 3.448 ± 0.564 | 0.258 ± 0.183 | 0.794 ± 0.028 | 0.804 ± 0.028 |
| 500 | 500 | ProposedA_Together_Direct | 3.436 ± 0.555 | 0.206 ± 0.175 | 0.792 ± 0.026 | 0.804 ± 0.026 |
| 500 | 500 | ProposedA_Together_Direct_NoCrossfit | 3.468 ± 0.570 | 0.213 ± 0.134 | 0.792 ± 0.030 | 0.803 ± 0.030 |
| 500 | 500 | ProposedA_Together_NoCrossfit | 3.451 ± 0.586 | 0.254 ± 0.154 | 0.793 ± 0.032 | 0.804 ± 0.031 |
| 500 | 500 | ProposedB_LinearStepB | 3.449 ± 0.598 | 0.245 ± 0.199 | 0.787 ± 0.029 | 0.798 ± 0.028 |
| 500 | 500 | ProposedB_SourceDR | 3.870 ± 0.792 | 0.110 ± 0.049 | 0.638 ± 0.006 | 0.653 ± 0.001 |
| 500 | 500 | ProxyOnly | 4.105 ± 0.618 | 0.959 ± 0.036 | 0.618 ± 0.104 | 0.630 ± 0.103 |
| 500 | 500 | TargetOnlyDR | 3.383 ± 0.599 | 0.214 ± 0.203 | 0.794 ± 0.031 | 0.805 ± 0.030 |
| 500 | 1000 | AnchorOnly | 3.388 ± 0.227 | 0.080 ± 0.047 | 0.703 ± 0.057 | 0.718 ± 0.059 |
| 500 | 1000 | AnchorPlugin | 3.062 ± 0.069 | 0.780 ± 0.868 | 0.788 ± 0.008 | 0.802 ± 0.010 |
| 500 | 1000 | DRLearner_PooledNoSite | 2.465 ± 0.452 | 0.561 ± 0.002 | 0.849 ± 0.057 | 0.860 ± 0.056 |
| 500 | 1000 | DRLearner_PooledWithSite | 2.499 ± 0.440 | 0.585 ± 0.031 | 0.845 ± 0.056 | 0.856 ± 0.056 |
| 500 | 1000 | EntropyBalancing | 2.689 ± 0.397 | 0.718 ± 0.045 | 0.820 ± 0.054 | 0.833 ± 0.054 |
| 500 | 1000 | IPWTransport | 2.696 ± 0.415 | 0.716 ± 0.042 | 0.819 ± 0.056 | 0.832 ± 0.057 |
| 500 | 1000 | OutcomeModelTransport | 2.714 ± 0.455 | 0.708 ± 0.075 | 0.816 ± 0.065 | 0.829 ± 0.065 |
| 500 | 1000 | ProposedA | 3.393 ± 0.233 | 0.116 ± 0.007 | 0.698 ± 0.063 | 0.715 ± 0.063 |
| 500 | 1000 | ProposedA_Direct | 3.384 ± 0.252 | 0.115 ± 0.023 | 0.706 ± 0.075 | 0.722 ± 0.074 |
| 500 | 1000 | ProposedA_Direct_NoCrossfit | 3.388 ± 0.246 | 0.113 ± 0.023 | 0.703 ± 0.072 | 0.720 ± 0.072 |
| 500 | 1000 | ProposedA_FullyDirect | 3.414 ± 0.209 | 0.241 ± 0.089 | 0.698 ± 0.061 | 0.715 ± 0.061 |
| 500 | 1000 | ProposedA_FullyJoint | 3.407 ± 0.238 | 0.212 ± 0.071 | 0.702 ± 0.077 | 0.719 ± 0.076 |
| 500 | 1000 | ProposedA_JointProxy | 3.407 ± 0.258 | 0.099 ± 0.017 | 0.695 ± 0.071 | 0.712 ± 0.072 |
| 500 | 1000 | ProposedA_NoCrossfit | 3.392 ± 0.239 | 0.114 ± 0.003 | 0.697 ± 0.064 | 0.714 ± 0.065 |
| 500 | 1000 | ProposedA_Together | 3.376 ± 0.221 | 0.210 ± 0.081 | 0.705 ± 0.062 | 0.722 ± 0.063 |
| 500 | 1000 | ProposedA_Together_Direct | 3.414 ± 0.209 | 0.241 ± 0.089 | 0.698 ± 0.061 | 0.715 ± 0.061 |
| 500 | 1000 | ProposedA_Together_Direct_NoCrossfit | 3.417 ± 0.211 | 0.225 ± 0.056 | 0.703 ± 0.063 | 0.720 ± 0.064 |
| 500 | 1000 | ProposedA_Together_NoCrossfit | 3.406 ± 0.231 | 0.221 ± 0.070 | 0.699 ± 0.069 | 0.717 ± 0.070 |
| 500 | 1000 | ProposedB_LinearStepB | 3.392 ± 0.226 | 0.112 ± 0.021 | 0.699 ± 0.059 | 0.716 ± 0.060 |
| 500 | 1000 | ProposedB_SourceDR | 4.064 ± 0.365 | 1.172 ± 0.236 | 0.541 ± 0.135 | 0.561 ± 0.138 |
| 500 | 1000 | ProxyOnly | 4.089 ± 0.013 | 1.297 ± 0.082 | 0.558 ± 0.028 | 0.577 ± 0.026 |
| 500 | 1000 | TargetOnlyDR | 3.355 ± 0.184 | 0.116 ± 0.065 | 0.711 ± 0.051 | 0.727 ± 0.049 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 2.157 ± 0.454 | 0.879 ± 0.268 | 0.870 ± 0.084 | 0.879 ± 0.078 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 1.612 ± 0.224 | 0.445 ± 0.197 | 0.927 ± 0.029 | 0.932 ± 0.028 |
| 1000 | 0 | IPWTransport | 1.618 ± 0.233 | 0.447 ± 0.199 | 0.926 ± 0.030 | 0.932 ± 0.029 |
| 1000 | 0 | OutcomeModelTransport | 1.548 ± 0.157 | 0.428 ± 0.193 | 0.932 ± 0.021 | 0.937 ± 0.019 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 3.511 ± 0.242 | 0.654 ± 0.292 | 0.594 ± 0.016 | 0.609 ± 0.018 |
| 1000 | 0 | ProxyOnly | 3.770 ± 0.568 | 1.378 ± 0.640 | 0.572 ± 0.028 | 0.588 ± 0.036 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 3.788 ± 0.343 | 0.128 ± 0.085 | 0.633 ± 0.016 | 0.653 ± 0.019 |
| 1000 | 100 | AnchorPlugin | 2.264 ± 0.156 | 0.403 ± 0.538 | 0.866 ± 0.063 | 0.876 ± 0.060 |
| 1000 | 100 | DRLearner_PooledNoSite | 1.155 ± 0.640 | 0.483 ± 0.074 | 0.961 ± 0.044 | 0.964 ± 0.041 |
| 1000 | 100 | DRLearner_PooledWithSite | 1.094 ± 0.703 | 0.420 ± 0.217 | 0.962 ± 0.042 | 0.966 ± 0.039 |
| 1000 | 100 | EntropyBalancing | 1.381 ± 0.988 | 0.540 ± 0.336 | 0.940 ± 0.072 | 0.944 ± 0.067 |
| 1000 | 100 | IPWTransport | 1.397 ± 1.005 | 0.545 ± 0.342 | 0.938 ± 0.074 | 0.943 ± 0.069 |
| 1000 | 100 | OutcomeModelTransport | 1.192 ± 0.777 | 0.526 ± 0.305 | 0.958 ± 0.048 | 0.962 ± 0.044 |
| 1000 | 100 | ProposedA | 3.196 ± 0.416 | 0.137 ± 0.061 | 0.736 ± 0.005 | 0.751 ± 0.006 |
| 1000 | 100 | ProposedA_Direct | 3.144 ± 0.424 | 0.046 ± 0.059 | 0.747 ± 0.003 | 0.761 ± 0.004 |
| 1000 | 100 | ProposedA_Direct_NoCrossfit | 3.121 ± 0.414 | 0.057 ± 0.067 | 0.750 ± 0.005 | 0.764 ± 0.005 |
| 1000 | 100 | ProposedA_FullyDirect | 4.432 ± 0.615 | 0.204 ± 0.096 | 0.518 ± 0.068 | 0.537 ± 0.075 |
| 1000 | 100 | ProposedA_FullyJoint | 4.341 ± 0.553 | 0.163 ± 0.028 | 0.578 ± 0.034 | 0.595 ± 0.042 |
| 1000 | 100 | ProposedA_JointProxy | 3.201 ± 0.379 | 0.106 ± 0.074 | 0.729 ± 0.014 | 0.744 ± 0.015 |
| 1000 | 100 | ProposedA_NoCrossfit | 3.153 ± 0.420 | 0.128 ± 0.082 | 0.743 ± 0.001 | 0.757 ± 0.002 |
| 1000 | 100 | ProposedA_Together | 3.992 ± 0.704 | 0.098 ± 0.127 | 0.604 ± 0.059 | 0.620 ± 0.064 |
| 1000 | 100 | ProposedA_Together_Direct | 4.432 ± 0.615 | 0.204 ± 0.096 | 0.518 ± 0.068 | 0.537 ± 0.075 |
| 1000 | 100 | ProposedA_Together_Direct_NoCrossfit | 4.424 ± 0.608 | 0.204 ± 0.112 | 0.527 ± 0.058 | 0.546 ± 0.064 |
| 1000 | 100 | ProposedA_Together_NoCrossfit | 3.962 ± 0.710 | 0.098 ± 0.111 | 0.615 ± 0.048 | 0.629 ± 0.054 |
| 1000 | 100 | ProposedB_LinearStepB | 3.342 ± 0.461 | 0.097 ± 0.024 | 0.705 ± 0.025 | 0.721 ± 0.024 |
| 1000 | 100 | ProposedB_SourceDR | 3.467 ± 0.331 | 0.710 ± 0.091 | 0.676 ± 0.016 | 0.690 ± 0.008 |
| 1000 | 100 | ProxyOnly | 3.430 ± 0.464 | 0.502 ± 0.506 | 0.702 ± 0.022 | 0.717 ± 0.020 |
| 1000 | 100 | TargetOnlyDR | 4.214 ± 0.144 | 0.217 ± 0.268 | 0.598 ± 0.023 | 0.617 ± 0.020 |
| 1000 | 500 | AnchorOnly | 3.228 ± 0.457 | 0.153 ± 0.063 | 0.767 ± 0.028 | 0.777 ± 0.026 |
| 1000 | 500 | AnchorPlugin | 2.858 ± 0.436 | 0.544 ± 0.507 | 0.806 ± 0.013 | 0.817 ± 0.017 |
| 1000 | 500 | DRLearner_PooledNoSite | 1.765 ± 0.190 | 0.973 ± 0.053 | 0.953 ± 0.001 | 0.956 ± 0.001 |
| 1000 | 500 | DRLearner_PooledWithSite | 1.726 ± 0.218 | 0.927 ± 0.003 | 0.954 ± 0.001 | 0.957 ± 0.001 |
| 1000 | 500 | EntropyBalancing | 2.025 ± 0.253 | 1.180 ± 0.052 | 0.938 ± 0.000 | 0.942 ± 0.000 |
| 1000 | 500 | IPWTransport | 2.023 ± 0.250 | 1.184 ± 0.053 | 0.938 ± 0.000 | 0.943 ± 0.000 |
| 1000 | 500 | OutcomeModelTransport | 1.931 ± 0.236 | 1.146 ± 0.030 | 0.947 ± 0.002 | 0.951 ± 0.001 |
| 1000 | 500 | ProposedA | 3.236 ± 0.550 | 0.047 ± 0.005 | 0.769 ± 0.004 | 0.777 ± 0.003 |
| 1000 | 500 | ProposedA_Direct | 3.263 ± 0.569 | 0.025 ± 0.030 | 0.761 ± 0.007 | 0.769 ± 0.007 |
| 1000 | 500 | ProposedA_Direct_NoCrossfit | 3.266 ± 0.570 | 0.022 ± 0.026 | 0.760 ± 0.007 | 0.768 ± 0.007 |
| 1000 | 500 | ProposedA_FullyDirect | 3.281 ± 0.490 | 0.147 ± 0.024 | 0.764 ± 0.023 | 0.773 ± 0.021 |
| 1000 | 500 | ProposedA_FullyJoint | 3.271 ± 0.522 | 0.128 ± 0.045 | 0.763 ± 0.015 | 0.772 ± 0.014 |
| 1000 | 500 | ProposedA_JointProxy | 3.237 ± 0.562 | 0.020 ± 0.017 | 0.767 ± 0.002 | 0.775 ± 0.002 |
| 1000 | 500 | ProposedA_NoCrossfit | 3.232 ± 0.556 | 0.045 ± 0.001 | 0.767 ± 0.000 | 0.776 ± 0.000 |
| 1000 | 500 | ProposedA_Together | 3.228 ± 0.476 | 0.083 ± 0.028 | 0.770 ± 0.024 | 0.779 ± 0.023 |
| 1000 | 500 | ProposedA_Together_Direct | 3.281 ± 0.490 | 0.147 ± 0.024 | 0.764 ± 0.023 | 0.773 ± 0.021 |
| 1000 | 500 | ProposedA_Together_Direct_NoCrossfit | 3.314 ± 0.507 | 0.146 ± 0.003 | 0.759 ± 0.014 | 0.768 ± 0.014 |
| 1000 | 500 | ProposedA_Together_NoCrossfit | 3.238 ± 0.501 | 0.080 ± 0.042 | 0.769 ± 0.019 | 0.778 ± 0.018 |
| 1000 | 500 | ProposedB_LinearStepB | 3.209 ± 0.550 | 0.036 ± 0.038 | 0.777 ± 0.002 | 0.786 ± 0.002 |
| 1000 | 500 | ProposedB_SourceDR | 3.876 ± 0.806 | 1.363 ± 0.441 | 0.671 ± 0.033 | 0.683 ± 0.035 |
| 1000 | 500 | ProxyOnly | 3.878 ± 0.727 | 0.392 ± 0.548 | 0.613 ± 0.051 | 0.623 ± 0.056 |
| 1000 | 500 | TargetOnlyDR | 3.243 ± 0.553 | 0.137 ± 0.081 | 0.767 ± 0.017 | 0.778 ± 0.015 |
| 1000 | 1000 | AnchorOnly | 3.014 ± 0.407 | 0.125 ± 0.014 | 0.750 ± 0.017 | 0.765 ± 0.014 |
| 1000 | 1000 | AnchorPlugin | 2.916 ± 0.157 | 0.648 ± 0.226 | 0.719 ± 0.057 | 0.733 ± 0.054 |
| 1000 | 1000 | DRLearner_PooledNoSite | 2.668 ± 0.071 | 0.359 ± 0.352 | 0.775 ± 0.044 | 0.788 ± 0.040 |
| 1000 | 1000 | DRLearner_PooledWithSite | 2.660 ± 0.082 | 0.349 ± 0.344 | 0.776 ± 0.041 | 0.789 ± 0.038 |
| 1000 | 1000 | EntropyBalancing | 3.019 ± 0.029 | 0.579 ± 0.449 | 0.723 ± 0.054 | 0.737 ± 0.050 |
| 1000 | 1000 | IPWTransport | 3.021 ± 0.025 | 0.583 ± 0.445 | 0.722 ± 0.055 | 0.736 ± 0.052 |
| 1000 | 1000 | OutcomeModelTransport | 2.966 ± 0.125 | 0.527 ± 0.493 | 0.728 ± 0.038 | 0.742 ± 0.035 |
| 1000 | 1000 | ProposedA | 2.993 ± 0.389 | 0.144 ± 0.039 | 0.742 ± 0.009 | 0.759 ± 0.008 |
| 1000 | 1000 | ProposedA_Direct | 3.004 ± 0.391 | 0.153 ± 0.053 | 0.737 ± 0.005 | 0.754 ± 0.004 |
| 1000 | 1000 | ProposedA_Direct_NoCrossfit | 3.005 ± 0.388 | 0.152 ± 0.046 | 0.737 ± 0.003 | 0.753 ± 0.002 |
| 1000 | 1000 | ProposedA_FullyDirect | 2.996 ± 0.401 | 0.130 ± 0.031 | 0.742 ± 0.014 | 0.759 ± 0.012 |
| 1000 | 1000 | ProposedA_FullyJoint | 3.005 ± 0.392 | 0.147 ± 0.036 | 0.745 ± 0.015 | 0.761 ± 0.013 |
| 1000 | 1000 | ProposedA_JointProxy | 3.007 ± 0.382 | 0.155 ± 0.055 | 0.741 ± 0.007 | 0.758 ± 0.005 |
| 1000 | 1000 | ProposedA_NoCrossfit | 2.995 ± 0.393 | 0.140 ± 0.040 | 0.740 ± 0.009 | 0.757 ± 0.008 |
| 1000 | 1000 | ProposedA_Together | 2.983 ± 0.387 | 0.130 ± 0.021 | 0.745 ± 0.011 | 0.763 ± 0.009 |
| 1000 | 1000 | ProposedA_Together_Direct | 2.996 ± 0.401 | 0.130 ± 0.031 | 0.742 ± 0.014 | 0.759 ± 0.012 |
| 1000 | 1000 | ProposedA_Together_Direct_NoCrossfit | 3.013 ± 0.408 | 0.127 ± 0.031 | 0.739 ± 0.014 | 0.756 ± 0.012 |
| 1000 | 1000 | ProposedA_Together_NoCrossfit | 3.003 ± 0.392 | 0.139 ± 0.015 | 0.740 ± 0.010 | 0.757 ± 0.007 |
| 1000 | 1000 | ProposedB_LinearStepB | 2.984 ± 0.395 | 0.146 ± 0.069 | 0.749 ± 0.011 | 0.764 ± 0.011 |
| 1000 | 1000 | ProposedB_SourceDR | 3.708 ± 0.395 | 0.761 ± 0.042 | 0.498 ± 0.049 | 0.510 ± 0.048 |
| 1000 | 1000 | ProxyOnly | 3.778 ± 0.109 | 0.979 ± 0.406 | 0.487 ± 0.081 | 0.500 ± 0.078 |
| 1000 | 1000 | TargetOnlyDR | 2.972 ± 0.384 | 0.156 ± 0.061 | 0.753 ± 0.010 | 0.769 ± 0.007 |

### Targeting / Ranking Metrics

| m0 | m1 | Method | Top-10% (↑) | Top-20% (↑) | Kendall (↑) |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 0.818 ± 0.018 | 0.772 ± 0.006 | 0.608 ± 0.042 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 0.866 ± 0.019 | 0.856 ± 0.027 | 0.681 ± 0.004 |
| 100 | 0 | IPWTransport | 0.882 ± 0.010 | 0.873 ± 0.009 | 0.698 ± 0.007 |
| 100 | 0 | OutcomeModelTransport | 0.877 ± 0.026 | 0.883 ± 0.003 | 0.708 ± 0.013 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 100 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 0.590 ± 0.101 | 0.621 ± 0.053 | 0.455 ± 0.021 |
| 100 | 0 | ProxyOnly | 0.422 ± 0.026 | 0.384 ± 0.043 | 0.332 ± 0.088 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 0.715 ± 0.065 | 0.678 ± 0.143 | 0.469 ± 0.003 |
| 100 | 100 | AnchorPlugin | 0.789 ± 0.008 | 0.790 ± 0.010 | 0.586 ± 0.086 |
| 100 | 100 | DRLearner_PooledNoSite | 0.920 ± 0.016 | 0.935 ± 0.016 | 0.739 ± 0.091 |
| 100 | 100 | DRLearner_PooledWithSite | 0.921 ± 0.013 | 0.936 ± 0.014 | 0.739 ± 0.091 |
| 100 | 100 | EntropyBalancing | 0.920 ± 0.022 | 0.933 ± 0.021 | 0.734 ± 0.099 |
| 100 | 100 | IPWTransport | 0.921 ± 0.014 | 0.933 ± 0.018 | 0.734 ± 0.097 |
| 100 | 100 | OutcomeModelTransport | 0.920 ± 0.016 | 0.935 ± 0.016 | 0.737 ± 0.092 |
| 100 | 100 | ProposedA | 0.722 ± 0.163 | 0.711 ± 0.152 | 0.475 ± 0.007 |
| 100 | 100 | ProposedA_Direct | 0.660 ± 0.236 | 0.699 ± 0.200 | 0.501 ± 0.049 |
| 100 | 100 | ProposedA_Direct_NoCrossfit | 0.648 ± 0.238 | 0.680 ± 0.223 | 0.494 ± 0.049 |
| 100 | 100 | ProposedA_FullyDirect | 0.693 ± 0.157 | 0.716 ± 0.158 | 0.508 ± 0.032 |
| 100 | 100 | ProposedA_FullyJoint | 0.712 ± 0.166 | 0.723 ± 0.131 | 0.492 ± 0.035 |
| 100 | 100 | ProposedA_JointProxy | 0.679 ± 0.194 | 0.684 ± 0.161 | 0.485 ± 0.002 |
| 100 | 100 | ProposedA_NoCrossfit | 0.667 ± 0.188 | 0.695 ± 0.170 | 0.474 ± 0.005 |
| 100 | 100 | ProposedA_Together | 0.693 ± 0.189 | 0.688 ± 0.181 | 0.480 ± 0.023 |
| 100 | 100 | ProposedA_Together_Direct | 0.693 ± 0.157 | 0.716 ± 0.158 | 0.508 ± 0.032 |
| 100 | 100 | ProposedA_Together_Direct_NoCrossfit | 0.644 ± 0.242 | 0.721 ± 0.171 | 0.500 ± 0.038 |
| 100 | 100 | ProposedA_Together_NoCrossfit | 0.681 ± 0.198 | 0.683 ± 0.179 | 0.490 ± 0.040 |
| 100 | 100 | ProposedB_LinearStepB | 0.697 ± 0.182 | 0.689 ± 0.182 | 0.475 ± 0.019 |
| 100 | 100 | ProposedB_SourceDR | 0.675 ± 0.196 | 0.649 ± 0.187 | 0.458 ± 0.013 |
| 100 | 100 | ProxyOnly | 0.584 ± 0.116 | 0.559 ± 0.221 | 0.376 ± 0.006 |
| 100 | 100 | TargetOnlyDR | 0.646 ± 0.084 | 0.590 ± 0.167 | 0.423 ± 0.024 |
| 100 | 500 | AnchorOnly | 0.752 ± 0.001 | 0.722 ± 0.055 | 0.566 ± 0.004 |
| 100 | 500 | AnchorPlugin | 0.802 ± 0.087 | 0.816 ± 0.081 | 0.630 ± 0.078 |
| 100 | 500 | DRLearner_PooledNoSite | 0.901 ± 0.089 | 0.890 ± 0.115 | 0.723 ± 0.171 |
| 100 | 500 | DRLearner_PooledWithSite | 0.884 ± 0.105 | 0.889 ± 0.116 | 0.718 ± 0.173 |
| 100 | 500 | EntropyBalancing | 0.869 ± 0.126 | 0.865 ± 0.145 | 0.704 ± 0.189 |
| 100 | 500 | IPWTransport | 0.879 ± 0.109 | 0.874 ± 0.130 | 0.709 ± 0.183 |
| 100 | 500 | OutcomeModelTransport | 0.886 ± 0.105 | 0.885 ± 0.121 | 0.711 ± 0.178 |
| 100 | 500 | ProposedA | 0.748 ± 0.001 | 0.711 ± 0.024 | 0.561 ± 0.006 |
| 100 | 500 | ProposedA_Direct | 0.770 ± 0.023 | 0.724 ± 0.039 | 0.566 ± 0.009 |
| 100 | 500 | ProposedA_Direct_NoCrossfit | 0.767 ± 0.019 | 0.719 ± 0.034 | 0.564 ± 0.006 |
| 100 | 500 | ProposedA_FullyDirect | 0.492 ± 0.022 | 0.526 ± 0.021 | 0.398 ± 0.043 |
| 100 | 500 | ProposedA_FullyJoint | 0.595 ± 0.018 | 0.628 ± 0.011 | 0.453 ± 0.013 |
| 100 | 500 | ProposedA_JointProxy | 0.769 ± 0.031 | 0.731 ± 0.021 | 0.566 ± 0.008 |
| 100 | 500 | ProposedA_NoCrossfit | 0.789 ± 0.044 | 0.717 ± 0.039 | 0.562 ± 0.000 |
| 100 | 500 | ProposedA_Together | 0.639 ± 0.047 | 0.616 ± 0.027 | 0.467 ± 0.032 |
| 100 | 500 | ProposedA_Together_Direct | 0.492 ± 0.022 | 0.526 ± 0.021 | 0.398 ± 0.043 |
| 100 | 500 | ProposedA_Together_Direct_NoCrossfit | 0.478 ± 0.026 | 0.503 ± 0.033 | 0.392 ± 0.051 |
| 100 | 500 | ProposedA_Together_NoCrossfit | 0.607 ± 0.038 | 0.620 ± 0.035 | 0.466 ± 0.034 |
| 100 | 500 | ProposedB_LinearStepB | 0.759 ± 0.026 | 0.692 ± 0.032 | 0.555 ± 0.007 |
| 100 | 500 | ProposedB_SourceDR | 0.597 ± 0.107 | 0.625 ± 0.131 | 0.456 ± 0.119 |
| 100 | 500 | ProxyOnly | 0.326 ± 0.049 | 0.282 ± 0.049 | 0.277 ± 0.019 |
| 100 | 500 | TargetOnlyDR | 0.681 ± 0.001 | 0.674 ± 0.031 | 0.498 ± 0.002 |
| 100 | 1000 | AnchorOnly | 0.708 ± 0.066 | 0.673 ± 0.068 | 0.468 ± 0.061 |
| 100 | 1000 | AnchorPlugin | 0.819 ± 0.113 | 0.827 ± 0.122 | 0.583 ± 0.134 |
| 100 | 1000 | DRLearner_PooledNoSite | 0.923 ± 0.088 | 0.917 ± 0.090 | 0.750 ± 0.166 |
| 100 | 1000 | DRLearner_PooledWithSite | 0.918 ± 0.100 | 0.917 ± 0.089 | 0.747 ± 0.171 |
| 100 | 1000 | EntropyBalancing | 0.915 ± 0.099 | 0.910 ± 0.100 | 0.739 ± 0.180 |
| 100 | 1000 | IPWTransport | 0.909 ± 0.110 | 0.907 ± 0.103 | 0.735 ± 0.187 |
| 100 | 1000 | OutcomeModelTransport | 0.907 ± 0.116 | 0.904 ± 0.107 | 0.731 ± 0.185 |
| 100 | 1000 | ProposedA | 0.723 ± 0.084 | 0.677 ± 0.100 | 0.463 ± 0.064 |
| 100 | 1000 | ProposedA_Direct | 0.729 ± 0.031 | 0.731 ± 0.024 | 0.530 ± 0.028 |
| 100 | 1000 | ProposedA_Direct_NoCrossfit | 0.744 ± 0.057 | 0.743 ± 0.045 | 0.535 ± 0.035 |
| 100 | 1000 | ProposedA_FullyDirect | 0.415 ± 0.060 | 0.515 ± 0.090 | 0.263 ± 0.009 |
| 100 | 1000 | ProposedA_FullyJoint | 0.414 ± 0.124 | 0.513 ± 0.125 | 0.249 ± 0.028 |
| 100 | 1000 | ProposedA_JointProxy | 0.694 ± 0.024 | 0.707 ± 0.032 | 0.500 ± 0.023 |
| 100 | 1000 | ProposedA_NoCrossfit | 0.736 ± 0.074 | 0.695 ± 0.076 | 0.498 ± 0.044 |
| 100 | 1000 | ProposedA_Together | 0.472 ± 0.186 | 0.542 ± 0.063 | 0.313 ± 0.021 |
| 100 | 1000 | ProposedA_Together_Direct | 0.415 ± 0.060 | 0.515 ± 0.090 | 0.263 ± 0.009 |
| 100 | 1000 | ProposedA_Together_Direct_NoCrossfit | 0.433 ± 0.116 | 0.508 ± 0.113 | 0.272 ± 0.012 |
| 100 | 1000 | ProposedA_Together_NoCrossfit | 0.501 ± 0.117 | 0.572 ± 0.018 | 0.310 ± 0.021 |
| 100 | 1000 | ProposedB_LinearStepB | 0.731 ± 0.070 | 0.675 ± 0.099 | 0.469 ± 0.058 |
| 100 | 1000 | ProposedB_SourceDR | 0.588 ± 0.118 | 0.601 ± 0.140 | 0.371 ± 0.119 |
| 100 | 1000 | ProxyOnly | 0.412 ± 0.169 | 0.492 ± 0.104 | 0.274 ± 0.059 |
| 100 | 1000 | TargetOnlyDR | 0.478 ± 0.016 | 0.550 ± 0.010 | 0.294 ± 0.048 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 0.761 ± 0.093 | 0.781 ± 0.102 | 0.534 ± 0.135 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 0.753 ± 0.176 | 0.754 ± 0.165 | 0.506 ± 0.214 |
| 500 | 0 | IPWTransport | 0.754 ± 0.175 | 0.757 ± 0.162 | 0.509 ± 0.211 |
| 500 | 0 | OutcomeModelTransport | 0.760 ± 0.165 | 0.760 ± 0.164 | 0.513 ± 0.208 |
| 500 | 0 | ProposedA | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 500 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 0.541 ± 0.338 | 0.558 ± 0.256 | 0.316 ± 0.222 |
| 500 | 0 | ProxyOnly | 0.655 ± 0.085 | 0.672 ± 0.132 | 0.412 ± 0.126 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 0.589 ± 0.071 | 0.589 ± 0.103 | 0.416 ± 0.091 |
| 500 | 100 | AnchorPlugin | 0.761 ± 0.126 | 0.731 ± 0.073 | 0.583 ± 0.073 |
| 500 | 100 | DRLearner_PooledNoSite | 0.883 ± 0.019 | 0.868 ± 0.051 | 0.711 ± 0.061 |
| 500 | 100 | DRLearner_PooledWithSite | 0.888 ± 0.012 | 0.870 ± 0.055 | 0.716 ± 0.057 |
| 500 | 100 | EntropyBalancing | 0.846 ± 0.043 | 0.836 ± 0.067 | 0.679 ± 0.081 |
| 500 | 100 | IPWTransport | 0.861 ± 0.022 | 0.844 ± 0.064 | 0.683 ± 0.081 |
| 500 | 100 | OutcomeModelTransport | 0.880 ± 0.016 | 0.863 ± 0.053 | 0.706 ± 0.058 |
| 500 | 100 | ProposedA | 0.712 ± 0.027 | 0.687 ± 0.020 | 0.526 ± 0.012 |
| 500 | 100 | ProposedA_Direct | 0.765 ± 0.005 | 0.727 ± 0.022 | 0.529 ± 0.015 |
| 500 | 100 | ProposedA_Direct_NoCrossfit | 0.779 ± 0.024 | 0.730 ± 0.005 | 0.531 ± 0.005 |
| 500 | 100 | ProposedA_FullyDirect | 0.232 ± 0.015 | 0.332 ± 0.060 | 0.315 ± 0.039 |
| 500 | 100 | ProposedA_FullyJoint | 0.266 ± 0.047 | 0.399 ± 0.081 | 0.344 ± 0.026 |
| 500 | 100 | ProposedA_JointProxy | 0.737 ± 0.019 | 0.704 ± 0.000 | 0.527 ± 0.007 |
| 500 | 100 | ProposedA_NoCrossfit | 0.739 ± 0.038 | 0.719 ± 0.008 | 0.534 ± 0.026 |
| 500 | 100 | ProposedA_Together | 0.478 ± 0.084 | 0.529 ± 0.041 | 0.390 ± 0.038 |
| 500 | 100 | ProposedA_Together_Direct | 0.232 ± 0.015 | 0.332 ± 0.060 | 0.315 ± 0.039 |
| 500 | 100 | ProposedA_Together_Direct_NoCrossfit | 0.236 ± 0.016 | 0.329 ± 0.051 | 0.318 ± 0.035 |
| 500 | 100 | ProposedA_Together_NoCrossfit | 0.461 ± 0.013 | 0.522 ± 0.004 | 0.389 ± 0.028 |
| 500 | 100 | ProposedB_LinearStepB | 0.733 ± 0.042 | 0.708 ± 0.024 | 0.553 ± 0.015 |
| 500 | 100 | ProposedB_SourceDR | 0.539 ± 0.100 | 0.516 ± 0.015 | 0.413 ± 0.040 |
| 500 | 100 | ProxyOnly | 0.533 ± 0.105 | 0.588 ± 0.025 | 0.442 ± 0.056 |
| 500 | 100 | TargetOnlyDR | 0.354 ± 0.102 | 0.435 ± 0.055 | 0.383 ± 0.052 |
| 500 | 500 | AnchorOnly | 0.847 ± 0.006 | 0.826 ± 0.005 | 0.603 ± 0.010 |
| 500 | 500 | AnchorPlugin | 0.852 ± 0.040 | 0.842 ± 0.029 | 0.657 ± 0.004 |
| 500 | 500 | DRLearner_PooledNoSite | 0.898 ± 0.002 | 0.893 ± 0.013 | 0.717 ± 0.019 |
| 500 | 500 | DRLearner_PooledWithSite | 0.899 ± 0.003 | 0.897 ± 0.008 | 0.718 ± 0.016 |
| 500 | 500 | EntropyBalancing | 0.865 ± 0.025 | 0.867 ± 0.014 | 0.698 ± 0.025 |
| 500 | 500 | IPWTransport | 0.866 ± 0.020 | 0.869 ± 0.017 | 0.699 ± 0.023 |
| 500 | 500 | OutcomeModelTransport | 0.884 ± 0.004 | 0.882 ± 0.007 | 0.702 ± 0.019 |
| 500 | 500 | ProposedA | 0.832 ± 0.012 | 0.827 ± 0.009 | 0.600 ± 0.033 |
| 500 | 500 | ProposedA_Direct | 0.830 ± 0.006 | 0.815 ± 0.003 | 0.598 ± 0.026 |
| 500 | 500 | ProposedA_Direct_NoCrossfit | 0.828 ± 0.001 | 0.815 ± 0.008 | 0.599 ± 0.026 |
| 500 | 500 | ProposedA_FullyDirect | 0.837 ± 0.020 | 0.830 ± 0.008 | 0.597 ± 0.024 |
| 500 | 500 | ProposedA_FullyJoint | 0.817 ± 0.015 | 0.807 ± 0.013 | 0.597 ± 0.028 |
| 500 | 500 | ProposedA_JointProxy | 0.844 ± 0.011 | 0.819 ± 0.002 | 0.604 ± 0.032 |
| 500 | 500 | ProposedA_NoCrossfit | 0.823 ± 0.012 | 0.823 ± 0.001 | 0.600 ± 0.034 |
| 500 | 500 | ProposedA_Together | 0.824 ± 0.014 | 0.829 ± 0.034 | 0.598 ± 0.027 |
| 500 | 500 | ProposedA_Together_Direct | 0.837 ± 0.020 | 0.830 ± 0.008 | 0.597 ± 0.024 |
| 500 | 500 | ProposedA_Together_Direct_NoCrossfit | 0.829 ± 0.022 | 0.824 ± 0.005 | 0.596 ± 0.028 |
| 500 | 500 | ProposedA_Together_NoCrossfit | 0.825 ± 0.019 | 0.822 ± 0.027 | 0.597 ± 0.030 |
| 500 | 500 | ProposedB_LinearStepB | 0.807 ± 0.017 | 0.798 ± 0.017 | 0.590 ± 0.026 |
| 500 | 500 | ProposedB_SourceDR | 0.676 ± 0.005 | 0.679 ± 0.030 | 0.458 ± 0.003 |
| 500 | 500 | ProxyOnly | 0.626 ± 0.168 | 0.611 ± 0.125 | 0.441 ± 0.084 |
| 500 | 500 | TargetOnlyDR | 0.829 ± 0.037 | 0.786 ± 0.053 | 0.598 ± 0.030 |
| 500 | 1000 | AnchorOnly | 0.695 ± 0.010 | 0.746 ± 0.044 | 0.513 ± 0.051 |
| 500 | 1000 | AnchorPlugin | 0.818 ± 0.015 | 0.825 ± 0.010 | 0.592 ± 0.009 |
| 500 | 1000 | DRLearner_PooledNoSite | 0.887 ± 0.041 | 0.879 ± 0.062 | 0.663 ± 0.069 |
| 500 | 1000 | DRLearner_PooledWithSite | 0.887 ± 0.041 | 0.873 ± 0.054 | 0.658 ± 0.068 |
| 500 | 1000 | EntropyBalancing | 0.842 ± 0.058 | 0.867 ± 0.049 | 0.630 ± 0.061 |
| 500 | 1000 | IPWTransport | 0.840 ± 0.064 | 0.868 ± 0.056 | 0.628 ± 0.064 |
| 500 | 1000 | OutcomeModelTransport | 0.848 ± 0.077 | 0.857 ± 0.050 | 0.626 ± 0.074 |
| 500 | 1000 | ProposedA | 0.695 ± 0.027 | 0.744 ± 0.038 | 0.507 ± 0.055 |
| 500 | 1000 | ProposedA_Direct | 0.706 ± 0.031 | 0.745 ± 0.048 | 0.515 ± 0.067 |
| 500 | 1000 | ProposedA_Direct_NoCrossfit | 0.699 ± 0.024 | 0.740 ± 0.059 | 0.513 ± 0.064 |
| 500 | 1000 | ProposedA_FullyDirect | 0.740 ± 0.035 | 0.727 ± 0.035 | 0.508 ± 0.053 |
| 500 | 1000 | ProposedA_FullyJoint | 0.733 ± 0.012 | 0.734 ± 0.049 | 0.512 ± 0.068 |
| 500 | 1000 | ProposedA_JointProxy | 0.689 ± 0.014 | 0.727 ± 0.062 | 0.506 ± 0.063 |
| 500 | 1000 | ProposedA_NoCrossfit | 0.688 ± 0.022 | 0.738 ± 0.038 | 0.506 ± 0.057 |
| 500 | 1000 | ProposedA_Together | 0.732 ± 0.007 | 0.729 ± 0.023 | 0.515 ± 0.056 |
| 500 | 1000 | ProposedA_Together_Direct | 0.740 ± 0.035 | 0.727 ± 0.035 | 0.508 ± 0.053 |
| 500 | 1000 | ProposedA_Together_Direct_NoCrossfit | 0.747 ± 0.018 | 0.726 ± 0.033 | 0.513 ± 0.056 |
| 500 | 1000 | ProposedA_Together_NoCrossfit | 0.736 ± 0.012 | 0.736 ± 0.029 | 0.510 ± 0.061 |
| 500 | 1000 | ProposedB_LinearStepB | 0.689 ± 0.002 | 0.732 ± 0.035 | 0.510 ± 0.052 |
| 500 | 1000 | ProposedB_SourceDR | 0.608 ± 0.102 | 0.623 ± 0.111 | 0.379 ± 0.107 |
| 500 | 1000 | ProxyOnly | 0.550 ± 0.097 | 0.603 ± 0.045 | 0.392 ± 0.020 |
| 500 | 1000 | TargetOnlyDR | 0.678 ± 0.014 | 0.750 ± 0.035 | 0.520 ± 0.044 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 0.904 ± 0.036 | 0.913 ± 0.036 | 0.694 ± 0.110 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 0.933 ± 0.027 | 0.936 ± 0.017 | 0.768 ± 0.048 |
| 1000 | 0 | IPWTransport | 0.933 ± 0.027 | 0.937 ± 0.011 | 0.767 ± 0.050 |
| 1000 | 0 | OutcomeModelTransport | 0.944 ± 0.012 | 0.934 ± 0.020 | 0.776 ± 0.034 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 0.620 ± 0.012 | 0.640 ± 0.050 | 0.419 ± 0.017 |
| 1000 | 0 | ProxyOnly | 0.586 ± 0.143 | 0.624 ± 0.089 | 0.402 ± 0.020 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 0.632 ± 0.082 | 0.682 ± 0.063 | 0.455 ± 0.015 |
| 1000 | 100 | AnchorPlugin | 0.888 ± 0.052 | 0.894 ± 0.061 | 0.684 ± 0.080 |
| 1000 | 100 | DRLearner_PooledNoSite | 0.970 ± 0.035 | 0.972 ± 0.031 | 0.848 ± 0.107 |
| 1000 | 100 | DRLearner_PooledWithSite | 0.974 ± 0.032 | 0.972 ± 0.031 | 0.852 ± 0.107 |
| 1000 | 100 | EntropyBalancing | 0.957 ± 0.056 | 0.946 ± 0.061 | 0.814 ± 0.145 |
| 1000 | 100 | IPWTransport | 0.957 ± 0.056 | 0.946 ± 0.061 | 0.811 ± 0.147 |
| 1000 | 100 | OutcomeModelTransport | 0.970 ± 0.035 | 0.970 ± 0.032 | 0.843 ± 0.113 |
| 1000 | 100 | ProposedA | 0.794 ± 0.007 | 0.800 ± 0.031 | 0.543 ± 0.007 |
| 1000 | 100 | ProposedA_Direct | 0.811 ± 0.015 | 0.806 ± 0.033 | 0.554 ± 0.004 |
| 1000 | 100 | ProposedA_Direct_NoCrossfit | 0.832 ± 0.006 | 0.813 ± 0.020 | 0.557 ± 0.007 |
| 1000 | 100 | ProposedA_FullyDirect | 0.545 ± 0.069 | 0.612 ± 0.118 | 0.363 ± 0.051 |
| 1000 | 100 | ProposedA_FullyJoint | 0.613 ± 0.083 | 0.645 ± 0.068 | 0.409 ± 0.028 |
| 1000 | 100 | ProposedA_JointProxy | 0.802 ± 0.004 | 0.795 ± 0.019 | 0.535 ± 0.012 |
| 1000 | 100 | ProposedA_NoCrossfit | 0.839 ± 0.002 | 0.813 ± 0.018 | 0.551 ± 0.002 |
| 1000 | 100 | ProposedA_Together | 0.652 ± 0.139 | 0.671 ± 0.125 | 0.430 ± 0.051 |
| 1000 | 100 | ProposedA_Together_Direct | 0.545 ± 0.069 | 0.612 ± 0.118 | 0.363 ± 0.051 |
| 1000 | 100 | ProposedA_Together_Direct_NoCrossfit | 0.542 ± 0.096 | 0.578 ± 0.125 | 0.369 ± 0.044 |
| 1000 | 100 | ProposedA_Together_NoCrossfit | 0.667 ± 0.135 | 0.681 ± 0.084 | 0.438 ± 0.042 |
| 1000 | 100 | ProposedB_LinearStepB | 0.733 ± 0.017 | 0.741 ± 0.004 | 0.515 ± 0.020 |
| 1000 | 100 | ProposedB_SourceDR | 0.739 ± 0.011 | 0.725 ± 0.055 | 0.487 ± 0.012 |
| 1000 | 100 | ProxyOnly | 0.769 ± 0.029 | 0.746 ± 0.026 | 0.512 ± 0.019 |
| 1000 | 100 | TargetOnlyDR | 0.594 ± 0.075 | 0.693 ± 0.028 | 0.428 ± 0.013 |
| 1000 | 500 | AnchorOnly | 0.769 ± 0.028 | 0.761 ± 0.062 | 0.570 ± 0.026 |
| 1000 | 500 | AnchorPlugin | 0.811 ± 0.056 | 0.805 ± 0.056 | 0.611 ± 0.019 |
| 1000 | 500 | DRLearner_PooledNoSite | 0.950 ± 0.016 | 0.951 ± 0.008 | 0.812 ± 0.002 |
| 1000 | 500 | DRLearner_PooledWithSite | 0.951 ± 0.014 | 0.954 ± 0.011 | 0.814 ± 0.002 |
| 1000 | 500 | EntropyBalancing | 0.944 ± 0.016 | 0.939 ± 0.015 | 0.783 ± 0.001 |
| 1000 | 500 | IPWTransport | 0.943 ± 0.015 | 0.940 ± 0.017 | 0.784 ± 0.001 |
| 1000 | 500 | OutcomeModelTransport | 0.947 ± 0.016 | 0.945 ± 0.013 | 0.800 ± 0.003 |
| 1000 | 500 | ProposedA | 0.754 ± 0.059 | 0.776 ± 0.050 | 0.572 ± 0.005 |
| 1000 | 500 | ProposedA_Direct | 0.772 ± 0.032 | 0.789 ± 0.024 | 0.565 ± 0.006 |
| 1000 | 500 | ProposedA_Direct_NoCrossfit | 0.779 ± 0.021 | 0.783 ± 0.036 | 0.564 ± 0.006 |
| 1000 | 500 | ProposedA_FullyDirect | 0.781 ± 0.012 | 0.777 ± 0.026 | 0.567 ± 0.024 |
| 1000 | 500 | ProposedA_FullyJoint | 0.793 ± 0.038 | 0.775 ± 0.014 | 0.566 ± 0.015 |
| 1000 | 500 | ProposedA_JointProxy | 0.793 ± 0.034 | 0.783 ± 0.047 | 0.569 ± 0.000 |
| 1000 | 500 | ProposedA_NoCrossfit | 0.758 ± 0.057 | 0.780 ± 0.039 | 0.570 ± 0.001 |
| 1000 | 500 | ProposedA_Together | 0.794 ± 0.022 | 0.770 ± 0.015 | 0.572 ± 0.024 |
| 1000 | 500 | ProposedA_Together_Direct | 0.781 ± 0.012 | 0.777 ± 0.026 | 0.567 ± 0.024 |
| 1000 | 500 | ProposedA_Together_Direct_NoCrossfit | 0.790 ± 0.011 | 0.779 ± 0.022 | 0.561 ± 0.016 |
| 1000 | 500 | ProposedA_Together_NoCrossfit | 0.798 ± 0.028 | 0.769 ± 0.029 | 0.571 ± 0.019 |
| 1000 | 500 | ProposedB_LinearStepB | 0.788 ± 0.051 | 0.786 ± 0.052 | 0.581 ± 0.002 |
| 1000 | 500 | ProposedB_SourceDR | 0.688 ± 0.098 | 0.671 ± 0.086 | 0.482 ± 0.030 |
| 1000 | 500 | ProxyOnly | 0.655 ± 0.118 | 0.634 ± 0.121 | 0.436 ± 0.040 |
| 1000 | 500 | TargetOnlyDR | 0.787 ± 0.013 | 0.777 ± 0.009 | 0.572 ± 0.019 |
| 1000 | 1000 | AnchorOnly | 0.808 ± 0.001 | 0.746 ± 0.004 | 0.556 ± 0.015 |
| 1000 | 1000 | AnchorPlugin | 0.731 ± 0.023 | 0.715 ± 0.030 | 0.528 ± 0.048 |
| 1000 | 1000 | DRLearner_PooledNoSite | 0.757 ± 0.032 | 0.740 ± 0.047 | 0.579 ± 0.042 |
| 1000 | 1000 | DRLearner_PooledWithSite | 0.758 ± 0.029 | 0.741 ± 0.049 | 0.580 ± 0.040 |
| 1000 | 1000 | EntropyBalancing | 0.695 ± 0.027 | 0.687 ± 0.057 | 0.528 ± 0.047 |
| 1000 | 1000 | IPWTransport | 0.693 ± 0.052 | 0.689 ± 0.059 | 0.528 ± 0.049 |
| 1000 | 1000 | OutcomeModelTransport | 0.703 ± 0.022 | 0.690 ± 0.041 | 0.533 ± 0.033 |
| 1000 | 1000 | ProposedA | 0.772 ± 0.008 | 0.752 ± 0.019 | 0.549 ± 0.009 |
| 1000 | 1000 | ProposedA_Direct | 0.779 ± 0.017 | 0.745 ± 0.020 | 0.543 ± 0.006 |
| 1000 | 1000 | ProposedA_Direct_NoCrossfit | 0.773 ± 0.011 | 0.754 ± 0.021 | 0.543 ± 0.004 |
| 1000 | 1000 | ProposedA_FullyDirect | 0.776 ± 0.028 | 0.762 ± 0.013 | 0.548 ± 0.013 |
| 1000 | 1000 | ProposedA_FullyJoint | 0.801 ± 0.001 | 0.735 ± 0.008 | 0.552 ± 0.015 |
| 1000 | 1000 | ProposedA_JointProxy | 0.793 ± 0.016 | 0.749 ± 0.002 | 0.548 ± 0.008 |
| 1000 | 1000 | ProposedA_NoCrossfit | 0.778 ± 0.018 | 0.743 ± 0.026 | 0.547 ± 0.010 |
| 1000 | 1000 | ProposedA_Together | 0.795 ± 0.021 | 0.764 ± 0.018 | 0.553 ± 0.010 |
| 1000 | 1000 | ProposedA_Together_Direct | 0.776 ± 0.028 | 0.762 ± 0.013 | 0.548 ± 0.013 |
| 1000 | 1000 | ProposedA_Together_Direct_NoCrossfit | 0.789 ± 0.008 | 0.760 ± 0.005 | 0.546 ± 0.013 |
| 1000 | 1000 | ProposedA_Together_NoCrossfit | 0.775 ± 0.013 | 0.737 ± 0.036 | 0.547 ± 0.009 |
| 1000 | 1000 | ProposedB_LinearStepB | 0.779 ± 0.052 | 0.758 ± 0.000 | 0.553 ± 0.014 |
| 1000 | 1000 | ProposedB_SourceDR | 0.456 ± 0.057 | 0.445 ± 0.062 | 0.345 ± 0.036 |
| 1000 | 1000 | ProxyOnly | 0.497 ± 0.129 | 0.477 ± 0.176 | 0.338 ± 0.062 |
| 1000 | 1000 | TargetOnlyDR | 0.806 ± 0.010 | 0.745 ± 0.035 | 0.559 ± 0.009 |

### ATE Estimation

| m0 | m1 | Method | ATE Est | ATE Err (↓) | ATE Bias |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | -0.917 ± 0.143 | 0.622 ± 0.026 | 0.018 ± 0.880 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | -0.608 ± 0.686 | 0.328 ± 0.050 | 0.328 ± 0.050 |
| 100 | 0 | IPWTransport | -0.569 ± 0.631 | 0.367 ± 0.105 | 0.367 ± 0.105 |
| 100 | 0 | OutcomeModelTransport | -0.502 ± 0.594 | 0.434 ± 0.143 | 0.434 ± 0.143 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 100 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | -0.289 ± 0.123 | 0.646 ± 0.614 | 0.646 ± 0.614 |
| 100 | 0 | ProxyOnly | -1.369 ± 0.375 | 0.786 ± 0.613 | -0.434 ± 1.111 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 1.151 ± 3.804 | 0.795 ± 0.531 | 0.795 ± 0.531 |
| 100 | 100 | AnchorPlugin | 0.605 ± 2.340 | 0.660 ± 0.352 | 0.249 ± 0.934 |
| 100 | 100 | DRLearner_PooledNoSite | 0.429 ± 3.318 | 0.073 ± 0.045 | 0.073 ± 0.045 |
| 100 | 100 | DRLearner_PooledWithSite | 0.423 ± 3.314 | 0.067 ± 0.041 | 0.067 ± 0.041 |
| 100 | 100 | EntropyBalancing | 0.414 ± 3.250 | 0.057 ± 0.023 | 0.057 ± 0.023 |
| 100 | 100 | IPWTransport | 0.461 ± 3.318 | 0.104 ± 0.044 | 0.104 ± 0.044 |
| 100 | 100 | OutcomeModelTransport | 0.426 ± 3.316 | 0.070 ± 0.043 | 0.070 ± 0.043 |
| 100 | 100 | ProposedA | 0.934 ± 3.724 | 0.577 ± 0.450 | 0.577 ± 0.450 |
| 100 | 100 | ProposedA_Direct | 0.774 ± 3.543 | 0.417 ± 0.270 | 0.417 ± 0.270 |
| 100 | 100 | ProposedA_Direct_NoCrossfit | 0.785 ± 3.591 | 0.428 ± 0.318 | 0.428 ± 0.318 |
| 100 | 100 | ProposedA_FullyDirect | 0.689 ± 3.790 | 0.365 ± 0.470 | 0.333 ± 0.516 |
| 100 | 100 | ProposedA_FullyJoint | 0.821 ± 3.696 | 0.465 ± 0.422 | 0.465 ± 0.422 |
| 100 | 100 | ProposedA_JointProxy | 0.870 ± 3.684 | 0.513 ± 0.411 | 0.513 ± 0.411 |
| 100 | 100 | ProposedA_NoCrossfit | 0.891 ± 3.715 | 0.535 ± 0.442 | 0.535 ± 0.442 |
| 100 | 100 | ProposedA_Together | 0.833 ± 3.765 | 0.476 ± 0.491 | 0.476 ± 0.491 |
| 100 | 100 | ProposedA_Together_Direct | 0.689 ± 3.790 | 0.365 ± 0.470 | 0.333 ± 0.516 |
| 100 | 100 | ProposedA_Together_Direct_NoCrossfit | 0.694 ± 3.665 | 0.337 ± 0.392 | 0.337 ± 0.392 |
| 100 | 100 | ProposedA_Together_NoCrossfit | 0.803 ± 3.672 | 0.446 ± 0.398 | 0.446 ± 0.398 |
| 100 | 100 | ProposedB_LinearStepB | 1.021 ± 3.816 | 0.665 ± 0.543 | 0.665 ± 0.543 |
| 100 | 100 | ProposedB_SourceDR | -0.017 ± 1.493 | 1.259 ± 0.528 | -0.374 ± 1.780 |
| 100 | 100 | ProxyOnly | 1.355 ± 3.071 | 0.999 ± 0.203 | 0.999 ± 0.203 |
| 100 | 100 | TargetOnlyDR | 1.088 ± 3.670 | 0.732 ± 0.396 | 0.732 ± 0.396 |
| 100 | 500 | AnchorOnly | -0.378 ± 0.382 | 0.177 ± 0.058 | 0.177 ± 0.058 |
| 100 | 500 | AnchorPlugin | -0.872 ± 0.393 | 0.316 ± 0.047 | -0.316 ± 0.047 |
| 100 | 500 | DRLearner_PooledNoSite | -0.479 ± 0.852 | 0.291 ± 0.108 | 0.077 ± 0.412 |
| 100 | 500 | DRLearner_PooledWithSite | -0.522 ± 0.818 | 0.267 ± 0.046 | 0.033 ± 0.378 |
| 100 | 500 | EntropyBalancing | -0.540 ± 0.858 | 0.296 ± 0.022 | 0.015 ± 0.418 |
| 100 | 500 | IPWTransport | -0.513 ± 0.847 | 0.288 ± 0.060 | 0.042 ± 0.407 |
| 100 | 500 | OutcomeModelTransport | -0.518 ± 0.860 | 0.297 ± 0.053 | 0.037 ± 0.420 |
| 100 | 500 | ProposedA | -0.379 ± 0.364 | 0.176 ± 0.076 | 0.176 ± 0.076 |
| 100 | 500 | ProposedA_Direct | -0.386 ± 0.335 | 0.169 ± 0.105 | 0.169 ± 0.105 |
| 100 | 500 | ProposedA_Direct_NoCrossfit | -0.387 ± 0.347 | 0.168 ± 0.093 | 0.168 ± 0.093 |
| 100 | 500 | ProposedA_FullyDirect | -0.379 ± 0.026 | 0.329 ± 0.249 | 0.176 ± 0.465 |
| 100 | 500 | ProposedA_FullyJoint | -0.430 ± 0.117 | 0.228 ± 0.177 | 0.125 ± 0.323 |
| 100 | 500 | ProposedA_JointProxy | -0.433 ± 0.379 | 0.122 ± 0.061 | 0.122 ± 0.061 |
| 100 | 500 | ProposedA_NoCrossfit | -0.381 ± 0.374 | 0.174 ± 0.066 | 0.174 ± 0.066 |
| 100 | 500 | ProposedA_Together | -0.477 ± 0.190 | 0.177 ± 0.110 | 0.078 ± 0.250 |
| 100 | 500 | ProposedA_Together_Direct | -0.379 ± 0.026 | 0.329 ± 0.249 | 0.176 ± 0.465 |
| 100 | 500 | ProposedA_Together_Direct_NoCrossfit | -0.372 ± 0.044 | 0.342 ± 0.259 | 0.183 ± 0.483 |
| 100 | 500 | ProposedA_Together_NoCrossfit | -0.501 ± 0.166 | 0.193 ± 0.077 | 0.055 ± 0.274 |
| 100 | 500 | ProposedB_LinearStepB | -0.402 ± 0.373 | 0.154 ± 0.067 | 0.154 ± 0.067 |
| 100 | 500 | ProposedB_SourceDR | -0.103 ± 0.228 | 0.452 ± 0.212 | 0.452 ± 0.212 |
| 100 | 500 | ProxyOnly | -3.922 ± 0.859 | 3.367 ± 1.299 | -3.367 ± 1.299 |
| 100 | 500 | TargetOnlyDR | -0.339 ± 0.232 | 0.216 ± 0.208 | 0.216 ± 0.208 |
| 100 | 1000 | AnchorOnly | 0.939 ± 0.031 | 0.095 ± 0.069 | 0.095 ± 0.069 |
| 100 | 1000 | AnchorPlugin | 0.841 ± 0.068 | 0.023 ± 0.004 | -0.003 ± 0.032 |
| 100 | 1000 | DRLearner_PooledNoSite | 0.836 ± 0.722 | 0.440 ± 0.011 | -0.008 ± 0.622 |
| 100 | 1000 | DRLearner_PooledWithSite | 0.932 ± 0.632 | 0.376 ± 0.124 | 0.088 ± 0.532 |
| 100 | 1000 | EntropyBalancing | 0.945 ± 0.804 | 0.498 ± 0.143 | 0.101 ± 0.704 |
| 100 | 1000 | IPWTransport | 0.943 ± 0.856 | 0.535 ± 0.139 | 0.099 ± 0.756 |
| 100 | 1000 | OutcomeModelTransport | 0.949 ± 0.717 | 0.437 ± 0.148 | 0.105 ± 0.617 |
| 100 | 1000 | ProposedA | 0.960 ± 0.014 | 0.116 ± 0.086 | 0.116 ± 0.086 |
| 100 | 1000 | ProposedA_Direct | 0.950 ± 0.201 | 0.106 ± 0.101 | 0.106 ± 0.101 |
| 100 | 1000 | ProposedA_Direct_NoCrossfit | 0.947 ± 0.165 | 0.103 ± 0.065 | 0.103 ± 0.065 |
| 100 | 1000 | ProposedA_FullyDirect | 1.121 ± 0.266 | 0.277 ± 0.366 | 0.277 ± 0.366 |
| 100 | 1000 | ProposedA_FullyJoint | 1.107 ± 0.500 | 0.424 ± 0.372 | 0.263 ± 0.600 |
| 100 | 1000 | ProposedA_JointProxy | 0.912 ± 0.099 | 0.068 ± 0.001 | 0.068 ± 0.001 |
| 100 | 1000 | ProposedA_NoCrossfit | 0.929 ± 0.100 | 0.084 ± 0.000 | 0.084 ± 0.000 |
| 100 | 1000 | ProposedA_Together | 1.098 ± 0.442 | 0.383 ± 0.359 | 0.254 ± 0.542 |
| 100 | 1000 | ProposedA_Together_Direct | 1.121 ± 0.266 | 0.277 ± 0.366 | 0.277 ± 0.366 |
| 100 | 1000 | ProposedA_Together_Direct_NoCrossfit | 1.113 ± 0.242 | 0.269 ± 0.342 | 0.269 ± 0.342 |
| 100 | 1000 | ProposedA_Together_NoCrossfit | 1.074 ± 0.387 | 0.344 ± 0.326 | 0.230 ± 0.486 |
| 100 | 1000 | ProposedB_LinearStepB | 0.976 ± 0.043 | 0.132 ± 0.057 | 0.132 ± 0.057 |
| 100 | 1000 | ProposedB_SourceDR | 0.404 ± 0.127 | 0.440 ± 0.027 | -0.440 ± 0.027 |
| 100 | 1000 | ProxyOnly | 3.094 ± 5.515 | 3.970 ± 3.182 | 2.250 ± 5.615 |
| 100 | 1000 | TargetOnlyDR | 1.253 ± 0.468 | 0.409 ± 0.568 | 0.409 ± 0.568 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 1.014 ± 1.348 | 0.737 ± 0.039 | 0.028 ± 1.043 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 1.111 ± 0.600 | 0.209 ± 0.177 | 0.125 ± 0.295 |
| 500 | 0 | IPWTransport | 1.095 ± 0.609 | 0.215 ± 0.155 | 0.109 ± 0.304 |
| 500 | 0 | OutcomeModelTransport | 1.184 ± 0.518 | 0.199 ± 0.213 | 0.199 ± 0.213 |
| 500 | 0 | ProposedA | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 500 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 0.239 ± 0.242 | 0.747 ± 0.063 | -0.747 ± 0.063 |
| 500 | 0 | ProxyOnly | 1.197 ± 2.567 | 1.600 ± 0.298 | 0.211 ± 2.263 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | -1.739 ± 0.432 | 0.690 ± 0.267 | -0.690 ± 0.267 |
| 500 | 100 | AnchorPlugin | -0.406 ± 0.023 | 0.643 ± 0.676 | 0.643 ± 0.676 |
| 500 | 100 | DRLearner_PooledNoSite | -0.122 ± 0.231 | 0.927 ± 0.469 | 0.927 ± 0.469 |
| 500 | 100 | DRLearner_PooledWithSite | -0.154 ± 0.220 | 0.895 ± 0.480 | 0.895 ± 0.480 |
| 500 | 100 | EntropyBalancing | -0.017 ± 0.143 | 1.033 ± 0.557 | 1.033 ± 0.557 |
| 500 | 100 | IPWTransport | -0.014 ± 0.123 | 1.035 ± 0.576 | 1.035 ± 0.576 |
| 500 | 100 | OutcomeModelTransport | -0.037 ± 0.187 | 1.012 ± 0.513 | 1.012 ± 0.513 |
| 500 | 100 | ProposedA | -1.309 ± 0.818 | 0.259 ± 0.119 | -0.259 ± 0.119 |
| 500 | 100 | ProposedA_Direct | -1.237 ± 0.812 | 0.187 ± 0.112 | -0.187 ± 0.112 |
| 500 | 100 | ProposedA_Direct_NoCrossfit | -1.249 ± 0.793 | 0.200 ± 0.094 | -0.200 ± 0.094 |
| 500 | 100 | ProposedA_FullyDirect | -1.306 ± 0.474 | 0.257 ± 0.226 | -0.257 ± 0.226 |
| 500 | 100 | ProposedA_FullyJoint | -1.465 ± 0.486 | 0.416 ± 0.213 | -0.416 ± 0.213 |
| 500 | 100 | ProposedA_JointProxy | -1.353 ± 0.893 | 0.304 ± 0.194 | -0.304 ± 0.194 |
| 500 | 100 | ProposedA_NoCrossfit | -1.323 ± 0.833 | 0.274 ± 0.133 | -0.274 ± 0.133 |
| 500 | 100 | ProposedA_Together | -1.638 ± 0.492 | 0.589 ± 0.208 | -0.589 ± 0.208 |
| 500 | 100 | ProposedA_Together_Direct | -1.306 ± 0.474 | 0.257 ± 0.226 | -0.257 ± 0.226 |
| 500 | 100 | ProposedA_Together_Direct_NoCrossfit | -1.308 ± 0.444 | 0.259 ± 0.256 | -0.259 ± 0.256 |
| 500 | 100 | ProposedA_Together_NoCrossfit | -1.636 ± 0.496 | 0.587 ± 0.204 | -0.587 ± 0.204 |
| 500 | 100 | ProposedB_LinearStepB | -1.284 ± 0.844 | 0.234 ± 0.144 | -0.234 ± 0.144 |
| 500 | 100 | ProposedB_SourceDR | 0.238 ± 0.703 | 1.287 ± 1.403 | 1.287 ± 1.403 |
| 500 | 100 | ProxyOnly | -0.801 ± 0.115 | 0.413 ± 0.351 | 0.248 ± 0.585 |
| 500 | 100 | TargetOnlyDR | -1.641 ± 0.276 | 0.591 ± 0.424 | -0.591 ± 0.424 |
| 500 | 500 | AnchorOnly | -0.023 ± 0.771 | 0.149 ± 0.196 | 0.138 ± 0.210 |
| 500 | 500 | AnchorPlugin | -0.489 ± 1.286 | 0.513 ± 0.464 | -0.328 ± 0.726 |
| 500 | 500 | DRLearner_PooledNoSite | -0.729 ± 1.655 | 0.774 ± 0.803 | -0.568 ± 1.095 |
| 500 | 500 | DRLearner_PooledWithSite | -0.725 ± 1.666 | 0.782 ± 0.797 | -0.563 ± 1.105 |
| 500 | 500 | EntropyBalancing | -0.864 ± 1.831 | 0.898 ± 0.993 | -0.702 ± 1.270 |
| 500 | 500 | IPWTransport | -0.881 ± 1.837 | 0.903 ± 1.018 | -0.720 ± 1.277 |
| 500 | 500 | OutcomeModelTransport | -0.838 ± 1.823 | 0.893 ± 0.958 | -0.677 ± 1.263 |
| 500 | 500 | ProposedA | -0.056 ± 0.905 | 0.244 ± 0.150 | 0.106 ± 0.345 |
| 500 | 500 | ProposedA_Direct | -0.058 ± 0.862 | 0.214 ± 0.146 | 0.103 ± 0.302 |
| 500 | 500 | ProposedA_Direct_NoCrossfit | -0.061 ± 0.863 | 0.214 ± 0.142 | 0.101 ± 0.302 |
| 500 | 500 | ProposedA_FullyDirect | -0.037 ± 0.851 | 0.206 ± 0.175 | 0.124 ± 0.291 |
| 500 | 500 | ProposedA_FullyJoint | -0.061 ± 0.901 | 0.241 ± 0.142 | 0.101 ± 0.340 |
| 500 | 500 | ProposedA_JointProxy | -0.075 ± 0.908 | 0.246 ± 0.122 | 0.086 ± 0.348 |
| 500 | 500 | ProposedA_NoCrossfit | -0.061 ± 0.888 | 0.231 ± 0.142 | 0.100 ± 0.327 |
| 500 | 500 | ProposedA_Together | -0.032 ± 0.926 | 0.258 ± 0.183 | 0.129 ± 0.366 |
| 500 | 500 | ProposedA_Together_Direct | -0.037 ± 0.851 | 0.206 ± 0.175 | 0.124 ± 0.291 |
| 500 | 500 | ProposedA_Together_Direct_NoCrossfit | -0.067 ± 0.861 | 0.213 ± 0.134 | 0.095 ± 0.301 |
| 500 | 500 | ProposedA_Together_NoCrossfit | -0.052 ± 0.920 | 0.254 ± 0.154 | 0.109 ± 0.360 |
| 500 | 500 | ProposedB_LinearStepB | -0.020 ± 0.907 | 0.245 ± 0.199 | 0.141 ± 0.346 |
| 500 | 500 | ProposedB_SourceDR | -0.127 ± 0.404 | 0.110 ± 0.049 | 0.034 ± 0.156 |
| 500 | 500 | ProxyOnly | -0.187 ± 1.916 | 0.959 ± 0.036 | -0.025 ± 1.356 |
| 500 | 500 | TargetOnlyDR | 0.053 ± 0.763 | 0.214 ± 0.203 | 0.214 ± 0.203 |
| 500 | 1000 | AnchorOnly | 1.015 ± 0.034 | 0.080 ± 0.047 | 0.033 ± 0.113 |
| 500 | 1000 | AnchorPlugin | 0.201 ± 0.948 | 0.780 ± 0.868 | -0.780 ± 0.868 |
| 500 | 1000 | DRLearner_PooledNoSite | 0.421 ± 0.078 | 0.561 ± 0.002 | -0.561 ± 0.002 |
| 500 | 1000 | DRLearner_PooledWithSite | 0.396 ± 0.111 | 0.585 ± 0.031 | -0.585 ± 0.031 |
| 500 | 1000 | EntropyBalancing | 0.263 ± 0.125 | 0.718 ± 0.045 | -0.718 ± 0.045 |
| 500 | 1000 | IPWTransport | 0.266 ± 0.121 | 0.716 ± 0.042 | -0.716 ± 0.042 |
| 500 | 1000 | OutcomeModelTransport | 0.273 ± 0.155 | 0.708 ± 0.075 | -0.708 ± 0.075 |
| 500 | 1000 | ProposedA | 1.097 ± 0.072 | 0.116 ± 0.007 | 0.116 ± 0.007 |
| 500 | 1000 | ProposedA_Direct | 1.096 ± 0.056 | 0.115 ± 0.023 | 0.115 ± 0.023 |
| 500 | 1000 | ProposedA_Direct_NoCrossfit | 1.094 ± 0.057 | 0.113 ± 0.023 | 0.113 ± 0.023 |
| 500 | 1000 | ProposedA_FullyDirect | 1.222 ± 0.169 | 0.241 ± 0.089 | 0.241 ± 0.089 |
| 500 | 1000 | ProposedA_FullyJoint | 1.193 ± 0.150 | 0.212 ± 0.071 | 0.212 ± 0.071 |
| 500 | 1000 | ProposedA_JointProxy | 1.081 ± 0.062 | 0.099 ± 0.017 | 0.099 ± 0.017 |
| 500 | 1000 | ProposedA_NoCrossfit | 1.096 ± 0.083 | 0.114 ± 0.003 | 0.114 ± 0.003 |
| 500 | 1000 | ProposedA_Together | 1.192 ± 0.161 | 0.210 ± 0.081 | 0.210 ± 0.081 |
| 500 | 1000 | ProposedA_Together_Direct | 1.222 ± 0.169 | 0.241 ± 0.089 | 0.241 ± 0.089 |
| 500 | 1000 | ProposedA_Together_Direct_NoCrossfit | 1.206 ± 0.135 | 0.225 ± 0.056 | 0.225 ± 0.056 |
| 500 | 1000 | ProposedA_Together_NoCrossfit | 1.202 ± 0.150 | 0.221 ± 0.070 | 0.221 ± 0.070 |
| 500 | 1000 | ProposedB_LinearStepB | 1.094 ± 0.059 | 0.112 ± 0.021 | 0.112 ± 0.021 |
| 500 | 1000 | ProposedB_SourceDR | -0.190 ± 0.315 | 1.172 ± 0.236 | -1.172 ± 0.236 |
| 500 | 1000 | ProxyOnly | 0.924 ± 1.915 | 1.297 ± 0.082 | -0.058 ± 1.835 |
| 500 | 1000 | TargetOnlyDR | 1.098 ± 0.015 | 0.116 ± 0.065 | 0.116 ± 0.065 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | -0.089 ± 0.810 | 0.879 ± 0.268 | -0.879 ± 0.268 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 0.650 ± 0.449 | 0.445 ± 0.197 | -0.139 ± 0.629 |
| 1000 | 0 | IPWTransport | 0.649 ± 0.446 | 0.447 ± 0.199 | -0.141 ± 0.632 |
| 1000 | 0 | OutcomeModelTransport | 0.653 ± 0.473 | 0.428 ± 0.193 | -0.137 ± 0.606 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 0.583 ± 0.153 | 0.654 ± 0.292 | -0.207 ± 0.925 |
| 1000 | 0 | ProxyOnly | -0.588 ± 1.718 | 1.378 ± 0.640 | -1.378 ± 0.640 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 0.948 ± 0.022 | 0.128 ± 0.085 | 0.060 ± 0.181 |
| 1000 | 100 | AnchorPlugin | 0.485 ± 0.380 | 0.403 ± 0.538 | -0.403 ± 0.538 |
| 1000 | 100 | DRLearner_PooledNoSite | 0.405 ± 0.232 | 0.483 ± 0.074 | -0.483 ± 0.074 |
| 1000 | 100 | DRLearner_PooledWithSite | 0.467 ± 0.375 | 0.420 ± 0.217 | -0.420 ± 0.217 |
| 1000 | 100 | EntropyBalancing | 0.347 ± 0.495 | 0.540 ± 0.336 | -0.540 ± 0.336 |
| 1000 | 100 | IPWTransport | 0.342 ± 0.501 | 0.545 ± 0.342 | -0.545 ± 0.342 |
| 1000 | 100 | OutcomeModelTransport | 0.361 ± 0.464 | 0.526 ± 0.305 | -0.526 ± 0.305 |
| 1000 | 100 | ProposedA | 0.844 ± 0.035 | 0.137 ± 0.061 | -0.043 ± 0.194 |
| 1000 | 100 | ProposedA_Direct | 0.846 ± 0.094 | 0.046 ± 0.059 | -0.042 ± 0.065 |
| 1000 | 100 | ProposedA_Direct_NoCrossfit | 0.840 ± 0.079 | 0.057 ± 0.067 | -0.047 ± 0.080 |
| 1000 | 100 | ProposedA_FullyDirect | 0.955 ± 0.130 | 0.204 ± 0.096 | 0.068 ± 0.289 |
| 1000 | 100 | ProposedA_FullyJoint | 0.907 ± 0.072 | 0.163 ± 0.028 | 0.020 ± 0.231 |
| 1000 | 100 | ProposedA_JointProxy | 0.835 ± 0.009 | 0.106 ± 0.074 | -0.053 ± 0.149 |
| 1000 | 100 | ProposedA_NoCrossfit | 0.829 ± 0.022 | 0.128 ± 0.082 | -0.058 ± 0.181 |
| 1000 | 100 | ProposedA_Together | 0.798 ± 0.020 | 0.098 ± 0.127 | -0.090 ± 0.139 |
| 1000 | 100 | ProposedA_Together_Direct | 0.955 ± 0.130 | 0.204 ± 0.096 | 0.068 ± 0.289 |
| 1000 | 100 | ProposedA_Together_Direct_NoCrossfit | 0.967 ± 0.130 | 0.204 ± 0.112 | 0.079 ± 0.289 |
| 1000 | 100 | ProposedA_Together_NoCrossfit | 0.809 ± 0.021 | 0.098 ± 0.111 | -0.079 ± 0.138 |
| 1000 | 100 | ProposedB_LinearStepB | 0.791 ± 0.135 | 0.097 ± 0.024 | -0.097 ± 0.024 |
| 1000 | 100 | ProposedB_SourceDR | 0.177 ± 0.249 | 0.710 ± 0.091 | -0.710 ± 0.091 |
| 1000 | 100 | ProxyOnly | 0.530 ± 0.551 | 0.502 ± 0.506 | -0.358 ± 0.710 |
| 1000 | 100 | TargetOnlyDR | 1.104 ± 0.109 | 0.217 ± 0.268 | 0.217 ± 0.268 |
| 1000 | 500 | AnchorOnly | 0.029 ± 2.072 | 0.153 ± 0.063 | -0.045 ± 0.216 |
| 1000 | 500 | AnchorPlugin | -0.285 ± 1.086 | 0.544 ± 0.507 | -0.359 ± 0.770 |
| 1000 | 500 | DRLearner_PooledNoSite | 0.036 ± 0.480 | 0.973 ± 0.053 | -0.037 ± 1.376 |
| 1000 | 500 | DRLearner_PooledWithSite | 0.076 ± 0.545 | 0.927 ± 0.003 | 0.002 ± 1.311 |
| 1000 | 500 | EntropyBalancing | 0.111 ± 0.187 | 1.180 ± 0.052 | 0.037 ± 1.669 |
| 1000 | 500 | IPWTransport | 0.111 ± 0.182 | 1.184 ± 0.053 | 0.038 ± 1.674 |
| 1000 | 500 | OutcomeModelTransport | 0.095 ± 0.235 | 1.146 ± 0.030 | 0.021 ± 1.620 |
| 1000 | 500 | ProposedA | 0.121 ± 1.851 | 0.047 ± 0.005 | 0.047 ± 0.005 |
| 1000 | 500 | ProposedA_Direct | 0.098 ± 1.885 | 0.025 ± 0.030 | 0.025 ± 0.030 |
| 1000 | 500 | ProposedA_Direct_NoCrossfit | 0.092 ± 1.886 | 0.022 ± 0.026 | 0.019 ± 0.031 |
| 1000 | 500 | ProposedA_FullyDirect | 0.057 ± 2.063 | 0.147 ± 0.024 | -0.017 ± 0.207 |
| 1000 | 500 | ProposedA_FullyJoint | 0.042 ± 2.037 | 0.128 ± 0.045 | -0.032 ± 0.182 |
| 1000 | 500 | ProposedA_JointProxy | 0.086 ± 1.884 | 0.020 ± 0.017 | 0.012 ± 0.028 |
| 1000 | 500 | ProposedA_NoCrossfit | 0.118 ± 1.855 | 0.045 ± 0.001 | 0.045 ± 0.001 |
| 1000 | 500 | ProposedA_Together | 0.094 ± 1.974 | 0.083 ± 0.028 | 0.020 ± 0.118 |
| 1000 | 500 | ProposedA_Together_Direct | 0.057 ± 2.063 | 0.147 ± 0.024 | -0.017 ± 0.207 |
| 1000 | 500 | ProposedA_Together_Direct_NoCrossfit | 0.072 ± 2.062 | 0.146 ± 0.003 | -0.002 ± 0.206 |
| 1000 | 500 | ProposedA_Together_NoCrossfit | 0.103 ± 1.969 | 0.080 ± 0.042 | 0.030 ± 0.113 |
| 1000 | 500 | ProposedB_LinearStepB | 0.110 ± 1.894 | 0.036 ± 0.038 | 0.036 ± 0.038 |
| 1000 | 500 | ProposedB_SourceDR | 0.386 ± 0.072 | 1.363 ± 0.441 | 0.312 ± 1.928 |
| 1000 | 500 | ProxyOnly | -0.318 ± 1.307 | 0.392 ± 0.548 | -0.392 ± 0.548 |
| 1000 | 500 | TargetOnlyDR | 0.017 ± 2.049 | 0.137 ± 0.081 | -0.057 ± 0.193 |
| 1000 | 1000 | AnchorOnly | -0.716 ± 0.005 | 0.125 ± 0.014 | -0.010 ± 0.176 |
| 1000 | 1000 | AnchorPlugin | -0.547 ± 1.098 | 0.648 ± 0.226 | 0.160 ± 0.916 |
| 1000 | 1000 | DRLearner_PooledNoSite | -0.457 ± 0.690 | 0.359 ± 0.352 | 0.249 ± 0.508 |
| 1000 | 1000 | DRLearner_PooledWithSite | -0.463 ± 0.676 | 0.349 ± 0.344 | 0.243 ± 0.494 |
| 1000 | 1000 | EntropyBalancing | -0.389 ± 1.001 | 0.579 ± 0.449 | 0.318 ± 0.819 |
| 1000 | 1000 | IPWTransport | -0.392 ± 1.006 | 0.583 ± 0.445 | 0.314 ± 0.824 |
| 1000 | 1000 | OutcomeModelTransport | -0.357 ± 0.927 | 0.527 ± 0.493 | 0.349 ± 0.745 |
| 1000 | 1000 | ProposedA | -0.734 ± 0.022 | 0.144 ± 0.039 | -0.027 ± 0.204 |
| 1000 | 1000 | ProposedA_Direct | -0.744 ± 0.034 | 0.153 ± 0.053 | -0.038 ± 0.216 |
| 1000 | 1000 | ProposedA_Direct_NoCrossfit | -0.739 ± 0.034 | 0.152 ± 0.046 | -0.032 ± 0.215 |
| 1000 | 1000 | ProposedA_FullyDirect | -0.728 ± 0.002 | 0.130 ± 0.031 | -0.022 ± 0.184 |
| 1000 | 1000 | ProposedA_FullyJoint | -0.732 ± 0.026 | 0.147 ± 0.036 | -0.025 ± 0.207 |
| 1000 | 1000 | ProposedA_JointProxy | -0.745 ± 0.037 | 0.155 ± 0.055 | -0.039 ± 0.219 |
| 1000 | 1000 | ProposedA_NoCrossfit | -0.735 ± 0.016 | 0.140 ± 0.040 | -0.029 ± 0.198 |
| 1000 | 1000 | ProposedA_Together | -0.721 ± 0.002 | 0.130 ± 0.021 | -0.015 ± 0.184 |
| 1000 | 1000 | ProposedA_Together_Direct | -0.728 ± 0.002 | 0.130 ± 0.031 | -0.022 ± 0.184 |
| 1000 | 1000 | ProposedA_Together_Direct_NoCrossfit | -0.728 ± 0.002 | 0.127 ± 0.031 | -0.022 ± 0.179 |
| 1000 | 1000 | ProposedA_Together_NoCrossfit | -0.717 ± 0.015 | 0.139 ± 0.015 | -0.011 ± 0.197 |
| 1000 | 1000 | ProposedB_LinearStepB | -0.755 ± 0.024 | 0.146 ± 0.069 | -0.049 ± 0.206 |
| 1000 | 1000 | ProposedB_SourceDR | 0.055 ± 0.224 | 0.761 ± 0.042 | 0.761 ± 0.042 |
| 1000 | 1000 | ProxyOnly | -0.994 ± 1.566 | 0.979 ± 0.406 | -0.287 ± 1.384 |
| 1000 | 1000 | TargetOnlyDR | -0.663 ± 0.039 | 0.156 ± 0.061 | 0.043 ± 0.221 |

### Policy / Decision Metrics

| m0 | m1 | Method | Policy Value (↑) | Regret (↓) | Value Top20 (↑) | Regret Top20 (↓) |
|---|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 1.981 ± 0.091 | 0.306 ± 0.058 | 1.824 ± 0.200 | 0.217 ± 0.034 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 2.085 ± 0.025 | 0.202 ± 0.007 | 1.906 ± 0.166 | 0.134 ± 0.001 |
| 100 | 0 | IPWTransport | 2.098 ± 0.047 | 0.189 ± 0.015 | 1.920 ± 0.180 | 0.120 ± 0.014 |
| 100 | 0 | OutcomeModelTransport | 2.103 ± 0.048 | 0.184 ± 0.016 | 1.929 ± 0.189 | 0.111 ± 0.023 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 1.718 ± 0.028 | 0.568 ± 0.004 | 1.684 ± 0.182 | 0.356 ± 0.015 |
| 100 | 0 | ProxyOnly | 1.478 ± 0.345 | 0.809 ± 0.313 | 1.450 ± 0.314 | 0.590 ± 0.148 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 1.614 ± 0.789 | 0.531 ± 0.027 | 0.892 ± 0.220 | 0.376 ± 0.027 |
| 100 | 100 | AnchorPlugin | 1.850 ± 0.791 | 0.295 ± 0.025 | 1.003 ± 0.336 | 0.266 ± 0.089 |
| 100 | 100 | DRLearner_PooledNoSite | 2.029 ± 0.763 | 0.115 ± 0.053 | 1.182 ± 0.298 | 0.086 ± 0.051 |
| 100 | 100 | DRLearner_PooledWithSite | 2.031 ± 0.766 | 0.113 ± 0.051 | 1.184 ± 0.296 | 0.084 ± 0.049 |
| 100 | 100 | EntropyBalancing | 2.021 ± 0.753 | 0.124 ± 0.063 | 1.178 ± 0.306 | 0.091 ± 0.059 |
| 100 | 100 | IPWTransport | 2.027 ± 0.757 | 0.118 ± 0.059 | 1.178 ± 0.303 | 0.090 ± 0.056 |
| 100 | 100 | OutcomeModelTransport | 2.028 ± 0.760 | 0.117 ± 0.056 | 1.182 ± 0.298 | 0.086 ± 0.051 |
| 100 | 100 | ProposedA | 1.623 ± 0.788 | 0.521 ± 0.029 | 0.936 ± 0.194 | 0.332 ± 0.053 |
| 100 | 100 | ProposedA_Direct | 1.605 ± 0.869 | 0.540 ± 0.052 | 0.933 ± 0.138 | 0.335 ± 0.109 |
| 100 | 100 | ProposedA_Direct_NoCrossfit | 1.578 ± 0.903 | 0.566 ± 0.086 | 0.914 ± 0.118 | 0.354 ± 0.129 |
| 100 | 100 | ProposedA_FullyDirect | 1.615 ± 0.805 | 0.530 ± 0.011 | 0.945 ± 0.183 | 0.323 ± 0.064 |
| 100 | 100 | ProposedA_FullyJoint | 1.636 ± 0.775 | 0.509 ± 0.042 | 0.947 ± 0.214 | 0.321 ± 0.033 |
| 100 | 100 | ProposedA_JointProxy | 1.621 ± 0.834 | 0.523 ± 0.018 | 0.905 ± 0.194 | 0.363 ± 0.053 |
| 100 | 100 | ProposedA_NoCrossfit | 1.625 ± 0.822 | 0.519 ± 0.006 | 0.921 ± 0.178 | 0.347 ± 0.069 |
| 100 | 100 | ProposedA_Together | 1.621 ± 0.824 | 0.524 ± 0.008 | 0.915 ± 0.167 | 0.353 ± 0.080 |
| 100 | 100 | ProposedA_Together_Direct | 1.615 ± 0.805 | 0.530 ± 0.011 | 0.945 ± 0.183 | 0.323 ± 0.064 |
| 100 | 100 | ProposedA_Together_Direct_NoCrossfit | 1.566 ± 0.855 | 0.578 ± 0.039 | 0.954 ± 0.164 | 0.314 ± 0.083 |
| 100 | 100 | ProposedA_Together_NoCrossfit | 1.600 ± 0.843 | 0.545 ± 0.027 | 0.908 ± 0.173 | 0.360 ± 0.074 |
| 100 | 100 | ProposedB_LinearStepB | 1.624 ± 0.815 | 0.520 ± 0.001 | 0.916 ± 0.165 | 0.352 ± 0.082 |
| 100 | 100 | ProposedB_SourceDR | 1.638 ± 0.821 | 0.506 ± 0.005 | 0.866 ± 0.179 | 0.402 ± 0.068 |
| 100 | 100 | ProxyOnly | 1.510 ± 1.020 | 0.634 ± 0.204 | 0.760 ± 0.179 | 0.508 ± 0.068 |
| 100 | 100 | TargetOnlyDR | 1.560 ± 0.861 | 0.584 ± 0.045 | 0.786 ± 0.233 | 0.482 ± 0.014 |
| 100 | 500 | AnchorOnly | 1.508 ± 0.323 | 0.339 ± 0.054 | 1.244 ± 0.386 | 0.283 ± 0.065 |
| 100 | 500 | AnchorPlugin | 1.584 ± 0.438 | 0.263 ± 0.061 | 1.342 ± 0.527 | 0.185 ± 0.076 |
| 100 | 500 | DRLearner_PooledNoSite | 1.676 ± 0.545 | 0.171 ± 0.168 | 1.417 ± 0.564 | 0.110 ± 0.113 |
| 100 | 500 | DRLearner_PooledWithSite | 1.675 ± 0.547 | 0.172 ± 0.170 | 1.416 ± 0.565 | 0.111 ± 0.114 |
| 100 | 500 | EntropyBalancing | 1.663 ± 0.570 | 0.184 ± 0.193 | 1.392 ± 0.594 | 0.134 ± 0.143 |
| 100 | 500 | IPWTransport | 1.664 ± 0.566 | 0.183 ± 0.189 | 1.401 ± 0.578 | 0.125 ± 0.127 |
| 100 | 500 | OutcomeModelTransport | 1.661 ± 0.557 | 0.187 ± 0.179 | 1.412 ± 0.569 | 0.114 ± 0.118 |
| 100 | 500 | ProposedA | 1.476 ± 0.286 | 0.372 ± 0.091 | 1.234 ± 0.417 | 0.293 ± 0.034 |
| 100 | 500 | ProposedA_Direct | 1.508 ± 0.357 | 0.340 ± 0.020 | 1.247 ± 0.402 | 0.280 ± 0.049 |
| 100 | 500 | ProposedA_Direct_NoCrossfit | 1.504 ± 0.349 | 0.344 ± 0.028 | 1.241 ± 0.407 | 0.285 ± 0.044 |
| 100 | 500 | ProposedA_FullyDirect | 1.256 ± 0.429 | 0.591 ± 0.052 | 1.048 ± 0.457 | 0.479 ± 0.006 |
| 100 | 500 | ProposedA_FullyJoint | 1.339 ± 0.358 | 0.508 ± 0.019 | 1.150 ± 0.428 | 0.376 ± 0.024 |
| 100 | 500 | ProposedA_JointProxy | 1.498 ± 0.303 | 0.350 ± 0.074 | 1.254 ± 0.421 | 0.273 ± 0.030 |
| 100 | 500 | ProposedA_NoCrossfit | 1.497 ± 0.326 | 0.350 ± 0.051 | 1.240 ± 0.403 | 0.287 ± 0.048 |
| 100 | 500 | ProposedA_Together | 1.317 ± 0.383 | 0.531 ± 0.006 | 1.138 ± 0.412 | 0.389 ± 0.039 |
| 100 | 500 | ProposedA_Together_Direct | 1.256 ± 0.429 | 0.591 ± 0.052 | 1.048 ± 0.457 | 0.479 ± 0.006 |
| 100 | 500 | ProposedA_Together_Direct_NoCrossfit | 1.257 ± 0.465 | 0.590 ± 0.087 | 1.025 ± 0.468 | 0.502 ± 0.017 |
| 100 | 500 | ProposedA_Together_NoCrossfit | 1.310 ± 0.368 | 0.537 ± 0.009 | 1.142 ± 0.403 | 0.384 ± 0.048 |
| 100 | 500 | ProposedB_LinearStepB | 1.471 ± 0.282 | 0.377 ± 0.095 | 1.215 ± 0.409 | 0.312 ± 0.042 |
| 100 | 500 | ProposedB_SourceDR | 1.292 ± 0.529 | 0.555 ± 0.152 | 1.149 ± 0.571 | 0.377 ± 0.120 |
| 100 | 500 | ProxyOnly | 0.821 ± 0.321 | 1.026 ± 0.056 | 0.800 ± 0.378 | 0.727 ± 0.073 |
| 100 | 500 | TargetOnlyDR | 1.385 ± 0.353 | 0.463 ± 0.024 | 1.196 ± 0.409 | 0.331 ± 0.042 |
| 100 | 1000 | AnchorOnly | 1.811 ± 0.032 | 0.551 ± 0.093 | 1.051 ± 0.010 | 0.468 ± 0.100 |
| 100 | 1000 | AnchorPlugin | 1.960 ± 0.344 | 0.401 ± 0.219 | 1.272 ± 0.264 | 0.248 ± 0.174 |
| 100 | 1000 | DRLearner_PooledNoSite | 2.194 ± 0.299 | 0.167 ± 0.174 | 1.401 ± 0.218 | 0.118 ± 0.128 |
| 100 | 1000 | DRLearner_PooledWithSite | 2.195 ± 0.298 | 0.166 ± 0.172 | 1.400 ± 0.217 | 0.119 ± 0.127 |
| 100 | 1000 | EntropyBalancing | 2.167 ± 0.328 | 0.195 ± 0.203 | 1.391 ± 0.232 | 0.129 ± 0.142 |
| 100 | 1000 | IPWTransport | 2.155 ± 0.340 | 0.206 ± 0.214 | 1.387 ± 0.237 | 0.133 ± 0.147 |
| 100 | 1000 | OutcomeModelTransport | 2.163 ± 0.337 | 0.198 ± 0.212 | 1.383 ± 0.243 | 0.137 ± 0.153 |
| 100 | 1000 | ProposedA | 1.769 ± 0.079 | 0.592 ± 0.047 | 1.056 ± 0.056 | 0.463 ± 0.146 |
| 100 | 1000 | ProposedA_Direct | 1.935 ± 0.077 | 0.426 ± 0.048 | 1.134 ± 0.053 | 0.386 ± 0.037 |
| 100 | 1000 | ProposedA_Direct_NoCrossfit | 1.926 ± 0.067 | 0.436 ± 0.059 | 1.151 ± 0.024 | 0.368 ± 0.066 |
| 100 | 1000 | ProposedA_FullyDirect | 1.034 ± 0.232 | 1.328 ± 0.107 | 0.825 ± 0.215 | 0.695 ± 0.125 |
| 100 | 1000 | ProposedA_FullyJoint | 1.138 ± 0.355 | 1.223 ± 0.230 | 0.822 ± 0.266 | 0.697 ± 0.176 |
| 100 | 1000 | ProposedA_JointProxy | 1.887 ± 0.112 | 0.474 ± 0.014 | 1.100 ± 0.041 | 0.420 ± 0.049 |
| 100 | 1000 | ProposedA_NoCrossfit | 1.847 ± 0.093 | 0.514 ± 0.033 | 1.082 ± 0.021 | 0.438 ± 0.111 |
| 100 | 1000 | ProposedA_Together | 1.088 ± 0.273 | 1.273 ± 0.148 | 0.863 ± 0.176 | 0.656 ± 0.086 |
| 100 | 1000 | ProposedA_Together_Direct | 1.034 ± 0.232 | 1.328 ± 0.107 | 0.825 ± 0.215 | 0.695 ± 0.125 |
| 100 | 1000 | ProposedA_Together_Direct_NoCrossfit | 1.066 ± 0.226 | 1.296 ± 0.100 | 0.815 ± 0.248 | 0.704 ± 0.158 |
| 100 | 1000 | ProposedA_Together_NoCrossfit | 1.096 ± 0.297 | 1.265 ± 0.172 | 0.905 ± 0.112 | 0.614 ± 0.022 |
| 100 | 1000 | ProposedB_LinearStepB | 1.789 ± 0.071 | 0.573 ± 0.054 | 1.053 ± 0.055 | 0.467 ± 0.145 |
| 100 | 1000 | ProposedB_SourceDR | 1.578 ± 0.405 | 0.784 ± 0.279 | 0.948 ± 0.287 | 0.571 ± 0.197 |
| 100 | 1000 | ProxyOnly | 1.291 ± 0.227 | 1.070 ± 0.102 | 0.792 ± 0.235 | 0.728 ± 0.145 |
| 100 | 1000 | TargetOnlyDR | 1.322 ± 0.091 | 1.039 ± 0.217 | 0.874 ± 0.071 | 0.645 ± 0.019 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 1.283 ± 0.758 | 0.475 ± 0.285 | 0.608 ± 1.005 | 0.315 ± 0.147 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 1.205 ± 0.571 | 0.552 ± 0.472 | 0.569 ± 0.915 | 0.353 ± 0.237 |
| 500 | 0 | IPWTransport | 1.202 ± 0.566 | 0.555 ± 0.477 | 0.572 ± 0.919 | 0.350 ± 0.232 |
| 500 | 0 | OutcomeModelTransport | 1.204 ± 0.580 | 0.554 ± 0.463 | 0.577 ± 0.916 | 0.346 ± 0.236 |
| 500 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 0.772 ± 0.412 | 0.985 ± 0.631 | 0.287 ± 0.784 | 0.636 ± 0.368 |
| 500 | 0 | ProxyOnly | 0.854 ± 0.813 | 0.904 ± 0.230 | 0.450 ± 0.961 | 0.472 ± 0.191 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 1.282 ± 0.346 | 0.903 ± 0.283 | 1.402 ± 0.450 | 0.475 ± 0.199 |
| 500 | 100 | AnchorPlugin | 1.799 ± 0.163 | 0.387 ± 0.099 | 1.566 ± 0.388 | 0.311 ± 0.136 |
| 500 | 100 | DRLearner_PooledNoSite | 1.935 ± 0.129 | 0.250 ± 0.065 | 1.723 ± 0.335 | 0.154 ± 0.084 |
| 500 | 100 | DRLearner_PooledWithSite | 1.947 ± 0.117 | 0.238 ± 0.053 | 1.725 ± 0.339 | 0.152 ± 0.088 |
| 500 | 100 | EntropyBalancing | 1.905 ± 0.158 | 0.281 ± 0.094 | 1.685 ± 0.359 | 0.192 ± 0.108 |
| 500 | 100 | IPWTransport | 1.907 ± 0.161 | 0.279 ± 0.097 | 1.694 ± 0.355 | 0.183 ± 0.103 |
| 500 | 100 | OutcomeModelTransport | 1.918 ± 0.125 | 0.268 ± 0.061 | 1.717 ± 0.338 | 0.159 ± 0.087 |
| 500 | 100 | ProposedA | 1.645 ± 0.122 | 0.541 ± 0.059 | 1.525 ± 0.291 | 0.351 ± 0.040 |
| 500 | 100 | ProposedA_Direct | 1.719 ± 0.096 | 0.467 ± 0.032 | 1.571 ± 0.281 | 0.306 ± 0.030 |
| 500 | 100 | ProposedA_Direct_NoCrossfit | 1.683 ± 0.149 | 0.503 ± 0.085 | 1.572 ± 0.300 | 0.305 ± 0.049 |
| 500 | 100 | ProposedA_FullyDirect | 1.068 ± 0.207 | 1.118 ± 0.143 | 1.129 ± 0.317 | 0.748 ± 0.065 |
| 500 | 100 | ProposedA_FullyJoint | 1.134 ± 0.161 | 1.051 ± 0.097 | 1.207 ± 0.279 | 0.670 ± 0.028 |
| 500 | 100 | ProposedA_JointProxy | 1.651 ± 0.091 | 0.535 ± 0.027 | 1.542 ± 0.311 | 0.335 ± 0.060 |
| 500 | 100 | ProposedA_NoCrossfit | 1.620 ± 0.139 | 0.565 ± 0.076 | 1.559 ± 0.316 | 0.318 ± 0.065 |
| 500 | 100 | ProposedA_Together | 1.328 ± 0.291 | 0.857 ± 0.227 | 1.341 ± 0.392 | 0.536 ± 0.140 |
| 500 | 100 | ProposedA_Together_Direct | 1.068 ± 0.207 | 1.118 ± 0.143 | 1.129 ± 0.317 | 0.748 ± 0.065 |
| 500 | 100 | ProposedA_Together_Direct_NoCrossfit | 1.003 ± 0.271 | 1.183 ± 0.207 | 1.125 ± 0.328 | 0.752 ± 0.076 |
| 500 | 100 | ProposedA_Together_NoCrossfit | 1.336 ± 0.285 | 0.850 ± 0.221 | 1.338 ± 0.342 | 0.539 ± 0.091 |
| 500 | 100 | ProposedB_LinearStepB | 1.661 ± 0.092 | 0.524 ± 0.028 | 1.545 ± 0.337 | 0.332 ± 0.085 |
| 500 | 100 | ProposedB_SourceDR | 1.289 ± 0.053 | 0.897 ± 0.011 | 1.332 ± 0.330 | 0.545 ± 0.079 |
| 500 | 100 | ProxyOnly | 1.517 ± 0.230 | 0.668 ± 0.167 | 1.409 ± 0.362 | 0.468 ± 0.111 |
| 500 | 100 | TargetOnlyDR | 1.146 ± 0.128 | 1.039 ± 0.065 | 1.245 ± 0.302 | 0.632 ± 0.051 |
| 500 | 500 | AnchorOnly | 1.836 ± 0.191 | 0.367 ± 0.083 | 1.412 ± 0.123 | 0.239 ± 0.076 |
| 500 | 500 | AnchorPlugin | 1.902 ± 0.225 | 0.302 ± 0.049 | 1.441 ± 0.070 | 0.210 ± 0.023 |
| 500 | 500 | DRLearner_PooledNoSite | 1.985 ± 0.325 | 0.219 ± 0.051 | 1.507 ± 0.072 | 0.144 ± 0.025 |
| 500 | 500 | DRLearner_PooledWithSite | 1.987 ± 0.320 | 0.217 ± 0.046 | 1.511 ± 0.077 | 0.140 ± 0.029 |
| 500 | 500 | EntropyBalancing | 1.952 ± 0.349 | 0.252 ± 0.075 | 1.472 ± 0.080 | 0.179 ± 0.033 |
| 500 | 500 | IPWTransport | 1.955 ± 0.346 | 0.248 ± 0.072 | 1.476 ± 0.076 | 0.175 ± 0.029 |
| 500 | 500 | OutcomeModelTransport | 1.956 ± 0.334 | 0.247 ± 0.060 | 1.491 ± 0.085 | 0.160 ± 0.038 |
| 500 | 500 | ProposedA | 1.765 ± 0.097 | 0.439 ± 0.176 | 1.413 ± 0.128 | 0.238 ± 0.081 |
| 500 | 500 | ProposedA_Direct | 1.778 ± 0.118 | 0.425 ± 0.155 | 1.399 ± 0.117 | 0.252 ± 0.070 |
| 500 | 500 | ProposedA_Direct_NoCrossfit | 1.769 ± 0.121 | 0.434 ± 0.153 | 1.397 ± 0.131 | 0.254 ± 0.084 |
| 500 | 500 | ProposedA_FullyDirect | 1.778 ± 0.118 | 0.425 ± 0.155 | 1.416 ± 0.126 | 0.235 ± 0.079 |
| 500 | 500 | ProposedA_FullyJoint | 1.769 ± 0.127 | 0.434 ± 0.146 | 1.384 ± 0.142 | 0.267 ± 0.095 |
| 500 | 500 | ProposedA_JointProxy | 1.791 ± 0.159 | 0.413 ± 0.114 | 1.404 ± 0.116 | 0.247 ± 0.069 |
| 500 | 500 | ProposedA_NoCrossfit | 1.783 ± 0.125 | 0.420 ± 0.149 | 1.410 ± 0.115 | 0.241 ± 0.068 |
| 500 | 500 | ProposedA_Together | 1.771 ± 0.132 | 0.433 ± 0.142 | 1.411 ± 0.162 | 0.240 ± 0.114 |
| 500 | 500 | ProposedA_Together_Direct | 1.778 ± 0.118 | 0.425 ± 0.155 | 1.416 ± 0.126 | 0.235 ± 0.079 |
| 500 | 500 | ProposedA_Together_Direct_NoCrossfit | 1.793 ± 0.138 | 0.411 ± 0.135 | 1.409 ± 0.124 | 0.242 ± 0.076 |
| 500 | 500 | ProposedA_Together_NoCrossfit | 1.752 ± 0.138 | 0.452 ± 0.135 | 1.403 ± 0.155 | 0.248 ± 0.108 |
| 500 | 500 | ProposedB_LinearStepB | 1.804 ± 0.132 | 0.399 ± 0.142 | 1.372 ± 0.150 | 0.279 ± 0.103 |
| 500 | 500 | ProposedB_SourceDR | 1.502 ± 0.098 | 0.702 ± 0.175 | 1.206 ± 0.215 | 0.445 ± 0.168 |
| 500 | 500 | ProxyOnly | 1.342 ± 0.336 | 0.861 ± 0.062 | 1.144 ± 0.031 | 0.507 ± 0.016 |
| 500 | 500 | TargetOnlyDR | 1.834 ± 0.142 | 0.369 ± 0.131 | 1.348 ± 0.204 | 0.303 ± 0.157 |
| 500 | 1000 | AnchorOnly | 1.701 ± 1.164 | 0.510 ± 0.110 | 0.944 ± 1.179 | 0.383 ± 0.072 |
| 500 | 1000 | AnchorPlugin | 1.812 ± 0.975 | 0.399 ± 0.079 | 1.063 ± 1.126 | 0.264 ± 0.019 |
| 500 | 1000 | DRLearner_PooledNoSite | 1.950 ± 1.146 | 0.261 ± 0.092 | 1.144 ± 1.203 | 0.183 ± 0.096 |
| 500 | 1000 | DRLearner_PooledWithSite | 1.938 ± 1.149 | 0.273 ± 0.094 | 1.135 ± 1.191 | 0.192 ± 0.084 |
| 500 | 1000 | EntropyBalancing | 1.891 ± 1.132 | 0.320 ± 0.078 | 1.126 ± 1.184 | 0.201 ± 0.076 |
| 500 | 1000 | IPWTransport | 1.892 ± 1.139 | 0.319 ± 0.084 | 1.127 ± 1.195 | 0.200 ± 0.087 |
| 500 | 1000 | OutcomeModelTransport | 1.896 ± 1.142 | 0.315 ± 0.088 | 1.111 ± 1.187 | 0.216 ± 0.079 |
| 500 | 1000 | ProposedA | 1.715 ± 1.159 | 0.496 ± 0.105 | 0.941 ± 1.171 | 0.386 ± 0.063 |
| 500 | 1000 | ProposedA_Direct | 1.723 ± 1.195 | 0.488 ± 0.140 | 0.942 ± 1.186 | 0.385 ± 0.079 |
| 500 | 1000 | ProposedA_Direct_NoCrossfit | 1.712 ± 1.187 | 0.499 ± 0.133 | 0.935 ± 1.202 | 0.392 ± 0.094 |
| 500 | 1000 | ProposedA_FullyDirect | 1.686 ± 1.192 | 0.525 ± 0.138 | 0.916 ± 1.167 | 0.411 ± 0.059 |
| 500 | 1000 | ProposedA_FullyJoint | 1.696 ± 1.209 | 0.515 ± 0.155 | 0.926 ± 1.188 | 0.401 ± 0.080 |
| 500 | 1000 | ProposedA_JointProxy | 1.706 ± 1.189 | 0.505 ± 0.134 | 0.915 ± 1.207 | 0.412 ± 0.100 |
| 500 | 1000 | ProposedA_NoCrossfit | 1.711 ± 1.166 | 0.500 ± 0.112 | 0.932 ± 1.170 | 0.395 ± 0.063 |
| 500 | 1000 | ProposedA_Together | 1.693 ± 1.226 | 0.518 ± 0.171 | 0.918 ± 1.148 | 0.409 ± 0.040 |
| 500 | 1000 | ProposedA_Together_Direct | 1.686 ± 1.192 | 0.525 ± 0.138 | 0.916 ± 1.167 | 0.411 ± 0.059 |
| 500 | 1000 | ProposedA_Together_Direct_NoCrossfit | 1.692 ± 1.177 | 0.519 ± 0.123 | 0.914 ± 1.164 | 0.413 ± 0.056 |
| 500 | 1000 | ProposedA_Together_NoCrossfit | 1.702 ± 1.212 | 0.509 ± 0.158 | 0.929 ± 1.157 | 0.398 ± 0.049 |
| 500 | 1000 | ProposedB_LinearStepB | 1.706 ± 1.139 | 0.505 ± 0.085 | 0.922 ± 1.166 | 0.404 ± 0.058 |
| 500 | 1000 | ProposedB_SourceDR | 1.321 ± 1.308 | 0.889 ± 0.253 | 0.757 ± 1.283 | 0.569 ± 0.176 |
| 500 | 1000 | ProxyOnly | 1.289 ± 0.986 | 0.922 ± 0.068 | 0.728 ± 1.185 | 0.599 ± 0.077 |
| 500 | 1000 | TargetOnlyDR | 1.728 ± 1.143 | 0.483 ± 0.089 | 0.949 ± 1.166 | 0.378 ± 0.059 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 1.926 ± 0.036 | 0.265 ± 0.135 | 1.279 ± 0.213 | 0.119 ± 0.059 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 2.077 ± 0.122 | 0.114 ± 0.049 | 1.313 ± 0.139 | 0.085 ± 0.014 |
| 1000 | 0 | IPWTransport | 2.072 ± 0.117 | 0.120 ± 0.054 | 1.314 ± 0.146 | 0.084 ± 0.007 |
| 1000 | 0 | OutcomeModelTransport | 2.091 ± 0.141 | 0.100 ± 0.030 | 1.311 ± 0.135 | 0.087 ± 0.018 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 1.526 ± 0.280 | 0.665 ± 0.109 | 0.918 ± 0.135 | 0.480 ± 0.019 |
| 1000 | 0 | ProxyOnly | 1.368 ± 0.512 | 0.823 ± 0.341 | 0.899 ± 0.086 | 0.499 ± 0.068 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 1.432 ± 0.745 | 0.637 ± 0.039 | 0.772 ± 0.551 | 0.465 ± 0.124 |
| 1000 | 100 | AnchorPlugin | 1.841 ± 0.854 | 0.229 ± 0.071 | 1.086 ± 0.752 | 0.150 ± 0.078 |
| 1000 | 100 | DRLearner_PooledNoSite | 1.994 ± 0.864 | 0.075 ± 0.080 | 1.198 ± 0.716 | 0.039 ± 0.042 |
| 1000 | 100 | DRLearner_PooledWithSite | 1.995 ± 0.871 | 0.074 ± 0.087 | 1.198 ± 0.717 | 0.038 ± 0.042 |
| 1000 | 100 | EntropyBalancing | 1.953 ± 0.926 | 0.117 ± 0.142 | 1.161 ± 0.758 | 0.075 ± 0.083 |
| 1000 | 100 | IPWTransport | 1.954 ± 0.924 | 0.116 ± 0.141 | 1.161 ± 0.758 | 0.075 ± 0.083 |
| 1000 | 100 | OutcomeModelTransport | 1.985 ± 0.880 | 0.084 ± 0.096 | 1.194 ± 0.718 | 0.042 ± 0.043 |
| 1000 | 100 | ProposedA | 1.590 ± 0.786 | 0.480 ± 0.003 | 0.948 ± 0.699 | 0.288 ± 0.024 |
| 1000 | 100 | ProposedA_Direct | 1.626 ± 0.740 | 0.444 ± 0.043 | 0.957 ± 0.703 | 0.279 ± 0.028 |
| 1000 | 100 | ProposedA_Direct_NoCrossfit | 1.654 ± 0.785 | 0.415 ± 0.001 | 0.966 ± 0.684 | 0.271 ± 0.009 |
| 1000 | 100 | ProposedA_FullyDirect | 1.136 ± 0.526 | 0.934 ± 0.258 | 0.668 ± 0.463 | 0.569 ± 0.212 |
| 1000 | 100 | ProposedA_FullyJoint | 1.215 ± 0.505 | 0.854 ± 0.278 | 0.718 ± 0.539 | 0.519 ± 0.136 |
| 1000 | 100 | ProposedA_JointProxy | 1.605 ± 0.832 | 0.465 ± 0.048 | 0.940 ± 0.681 | 0.296 ± 0.007 |
| 1000 | 100 | ProposedA_NoCrossfit | 1.614 ± 0.800 | 0.456 ± 0.017 | 0.966 ± 0.681 | 0.271 ± 0.006 |
| 1000 | 100 | ProposedA_Together | 1.255 ± 0.575 | 0.815 ± 0.209 | 0.752 ± 0.460 | 0.484 ± 0.215 |
| 1000 | 100 | ProposedA_Together_Direct | 1.136 ± 0.526 | 0.934 ± 0.258 | 0.668 ± 0.463 | 0.569 ± 0.212 |
| 1000 | 100 | ProposedA_Together_Direct_NoCrossfit | 1.136 ± 0.558 | 0.933 ± 0.226 | 0.618 ± 0.450 | 0.618 ± 0.225 |
| 1000 | 100 | ProposedA_Together_NoCrossfit | 1.299 ± 0.566 | 0.771 ± 0.217 | 0.769 ± 0.519 | 0.468 ± 0.155 |
| 1000 | 100 | ProposedB_LinearStepB | 1.594 ± 0.692 | 0.475 ± 0.091 | 0.862 ± 0.654 | 0.375 ± 0.020 |
| 1000 | 100 | ProposedB_SourceDR | 1.471 ± 0.752 | 0.598 ± 0.031 | 0.841 ± 0.726 | 0.396 ± 0.051 |
| 1000 | 100 | ProxyOnly | 1.519 ± 0.751 | 0.550 ± 0.033 | 0.867 ± 0.611 | 0.370 ± 0.064 |
| 1000 | 100 | TargetOnlyDR | 1.249 ± 0.720 | 0.821 ± 0.064 | 0.793 ± 0.683 | 0.444 ± 0.009 |
| 1000 | 500 | AnchorOnly | 1.573 ± 0.262 | 0.404 ± 0.067 | 0.972 ± 0.755 | 0.316 ± 0.036 |
| 1000 | 500 | AnchorPlugin | 1.606 ± 0.271 | 0.371 ± 0.058 | 1.031 ± 0.755 | 0.257 ± 0.036 |
| 1000 | 500 | DRLearner_PooledNoSite | 1.858 ± 0.334 | 0.120 ± 0.005 | 1.223 ± 0.790 | 0.065 ± 0.001 |
| 1000 | 500 | DRLearner_PooledWithSite | 1.869 ± 0.336 | 0.108 ± 0.007 | 1.227 ± 0.785 | 0.061 ± 0.006 |
| 1000 | 500 | EntropyBalancing | 1.812 ± 0.319 | 0.166 ± 0.010 | 1.208 ± 0.783 | 0.080 ± 0.008 |
| 1000 | 500 | IPWTransport | 1.812 ± 0.320 | 0.166 ± 0.009 | 1.209 ± 0.781 | 0.079 ± 0.010 |
| 1000 | 500 | OutcomeModelTransport | 1.833 ± 0.322 | 0.145 ± 0.007 | 1.215 ± 0.784 | 0.073 ± 0.007 |
| 1000 | 500 | ProposedA | 1.556 ± 0.201 | 0.421 ± 0.128 | 0.992 ± 0.768 | 0.297 ± 0.023 |
| 1000 | 500 | ProposedA_Direct | 1.544 ± 0.163 | 0.434 ± 0.166 | 1.007 ± 0.801 | 0.281 ± 0.010 |
| 1000 | 500 | ProposedA_Direct_NoCrossfit | 1.541 ± 0.162 | 0.437 ± 0.167 | 1.000 ± 0.786 | 0.288 ± 0.005 |
| 1000 | 500 | ProposedA_FullyDirect | 1.561 ± 0.219 | 0.416 ± 0.109 | 0.990 ± 0.801 | 0.298 ± 0.010 |
| 1000 | 500 | ProposedA_FullyJoint | 1.565 ± 0.194 | 0.412 ± 0.135 | 0.987 ± 0.817 | 0.301 ± 0.026 |
| 1000 | 500 | ProposedA_JointProxy | 1.555 ± 0.193 | 0.422 ± 0.136 | 1.000 ± 0.771 | 0.288 ± 0.020 |
| 1000 | 500 | ProposedA_NoCrossfit | 1.536 ± 0.189 | 0.442 ± 0.140 | 0.995 ± 0.783 | 0.293 ± 0.008 |
| 1000 | 500 | ProposedA_Together | 1.582 ± 0.234 | 0.395 ± 0.095 | 0.980 ± 0.817 | 0.308 ± 0.026 |
| 1000 | 500 | ProposedA_Together_Direct | 1.561 ± 0.219 | 0.416 ± 0.109 | 0.990 ± 0.801 | 0.298 ± 0.010 |
| 1000 | 500 | ProposedA_Together_Direct_NoCrossfit | 1.546 ± 0.246 | 0.431 ± 0.083 | 0.992 ± 0.806 | 0.296 ± 0.015 |
| 1000 | 500 | ProposedA_Together_NoCrossfit | 1.557 ± 0.210 | 0.420 ± 0.119 | 0.980 ± 0.798 | 0.308 ± 0.008 |
| 1000 | 500 | ProposedB_LinearStepB | 1.569 ± 0.181 | 0.409 ± 0.148 | 1.005 ± 0.763 | 0.283 ± 0.028 |
| 1000 | 500 | ProposedB_SourceDR | 1.273 ± 0.031 | 0.704 ± 0.298 | 0.853 ± 0.742 | 0.435 ± 0.049 |
| 1000 | 500 | ProxyOnly | 1.262 ± 0.102 | 0.716 ± 0.227 | 0.807 ± 0.701 | 0.481 ± 0.090 |
| 1000 | 500 | TargetOnlyDR | 1.612 ± 0.257 | 0.366 ± 0.072 | 0.988 ± 0.824 | 0.300 ± 0.033 |
| 1000 | 1000 | AnchorOnly | 1.500 ± 0.610 | 0.452 ± 0.065 | 1.359 ± 0.687 | 0.263 ± 0.039 |
| 1000 | 1000 | AnchorPlugin | 1.462 ± 0.536 | 0.489 ± 0.008 | 1.329 ± 0.665 | 0.293 ± 0.017 |
| 1000 | 1000 | DRLearner_PooledNoSite | 1.568 ± 0.518 | 0.383 ± 0.027 | 1.356 ± 0.643 | 0.265 ± 0.005 |
| 1000 | 1000 | DRLearner_PooledWithSite | 1.570 ± 0.517 | 0.382 ± 0.028 | 1.358 ± 0.641 | 0.264 ± 0.007 |
| 1000 | 1000 | EntropyBalancing | 1.472 ± 0.519 | 0.480 ± 0.026 | 1.303 ± 0.642 | 0.319 ± 0.007 |
| 1000 | 1000 | IPWTransport | 1.474 ± 0.519 | 0.477 ± 0.026 | 1.304 ± 0.640 | 0.317 ± 0.009 |
| 1000 | 1000 | OutcomeModelTransport | 1.476 ± 0.542 | 0.475 ± 0.002 | 1.304 ± 0.658 | 0.318 ± 0.009 |
| 1000 | 1000 | ProposedA | 1.527 ± 0.575 | 0.424 ± 0.031 | 1.367 ± 0.670 | 0.255 ± 0.021 |
| 1000 | 1000 | ProposedA_Direct | 1.533 ± 0.551 | 0.419 ± 0.006 | 1.359 ± 0.670 | 0.263 ± 0.022 |
| 1000 | 1000 | ProposedA_Direct_NoCrossfit | 1.531 ± 0.559 | 0.421 ± 0.015 | 1.368 ± 0.668 | 0.253 ± 0.019 |
| 1000 | 1000 | ProposedA_FullyDirect | 1.522 ± 0.587 | 0.429 ± 0.042 | 1.376 ± 0.674 | 0.245 ± 0.026 |
| 1000 | 1000 | ProposedA_FullyJoint | 1.531 ± 0.570 | 0.421 ± 0.025 | 1.348 ± 0.684 | 0.273 ± 0.036 |
| 1000 | 1000 | ProposedA_JointProxy | 1.531 ± 0.578 | 0.420 ± 0.034 | 1.362 ± 0.689 | 0.259 ± 0.040 |
| 1000 | 1000 | ProposedA_NoCrossfit | 1.530 ± 0.570 | 0.422 ± 0.025 | 1.358 ± 0.664 | 0.264 ± 0.016 |
| 1000 | 1000 | ProposedA_Together | 1.533 ± 0.577 | 0.418 ± 0.032 | 1.379 ± 0.669 | 0.243 ± 0.021 |
| 1000 | 1000 | ProposedA_Together_Direct | 1.522 ± 0.587 | 0.429 ± 0.042 | 1.376 ± 0.674 | 0.245 ± 0.026 |
| 1000 | 1000 | ProposedA_Together_Direct_NoCrossfit | 1.526 ± 0.594 | 0.425 ± 0.049 | 1.374 ± 0.684 | 0.248 ± 0.035 |
| 1000 | 1000 | ProposedA_Together_NoCrossfit | 1.527 ± 0.591 | 0.425 ± 0.046 | 1.352 ± 0.655 | 0.269 ± 0.007 |
| 1000 | 1000 | ProposedB_LinearStepB | 1.545 ± 0.553 | 0.407 ± 0.008 | 1.371 ± 0.689 | 0.251 ± 0.041 |
| 1000 | 1000 | ProposedB_SourceDR | 1.087 ± 0.564 | 0.865 ± 0.019 | 1.052 ± 0.677 | 0.570 ± 0.029 |
| 1000 | 1000 | ProxyOnly | 1.083 ± 0.572 | 0.869 ± 0.027 | 1.095 ± 0.554 | 0.527 ± 0.095 |
| 1000 | 1000 | TargetOnlyDR | 1.535 ± 0.619 | 0.416 ± 0.074 | 1.360 ± 0.655 | 0.261 ± 0.006 |

### Calibration Metrics

| m0 | m1 | Method | Slope (→1) | Intercept (→0) | R² (↑) | ECE (↓) | MCE (↓) |
|---|---|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 0.980 ± 0.173 | -0.024 ± 1.035 | 0.672 ± 0.060 | 0.641 ± 0.052 | 1.572 ± 0.180 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 0.849 ± 0.044 | -0.435 ± 0.180 | 0.776 ± 0.008 | 0.589 ± 0.151 | 1.377 ± 0.218 |
| 100 | 0 | IPWTransport | 0.873 ± 0.029 | -0.448 ± 0.202 | 0.798 ± 0.005 | 0.516 ± 0.109 | 1.229 ± 0.396 |
| 100 | 0 | OutcomeModelTransport | 0.888 ± 0.015 | -0.495 ± 0.217 | 0.811 ± 0.011 | 0.525 ± 0.124 | 1.259 ± 0.433 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 1.366 ± 0.170 | -0.551 ± 0.618 | 0.432 ± 0.014 | 0.886 ± 0.275 | 2.040 ± 0.436 |
| 100 | 0 | ProxyOnly | 0.808 ± 0.210 | 0.131 ± 0.751 | 0.239 ± 0.113 | 0.956 ± 0.746 | 2.044 ± 1.707 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 1.517 ± 0.138 | -1.652 ± 2.656 | 0.446 ± 0.012 | 1.041 ± 0.266 | 2.525 ± 0.906 |
| 100 | 100 | AnchorPlugin | 0.899 ± 0.086 | -0.087 ± 1.223 | 0.630 ± 0.129 | 0.748 ± 0.228 | 1.331 ± 0.040 |
| 100 | 100 | DRLearner_PooledNoSite | 0.938 ± 0.042 | 0.023 ± 0.179 | 0.836 ± 0.101 | 0.234 ± 0.099 | 0.520 ± 0.265 |
| 100 | 100 | DRLearner_PooledWithSite | 0.940 ± 0.039 | 0.023 ± 0.176 | 0.837 ± 0.101 | 0.234 ± 0.086 | 0.488 ± 0.225 |
| 100 | 100 | EntropyBalancing | 0.922 ± 0.081 | 0.108 ± 0.311 | 0.832 ± 0.108 | 0.293 ± 0.234 | 0.638 ± 0.431 |
| 100 | 100 | IPWTransport | 0.926 ± 0.062 | 0.032 ± 0.229 | 0.831 ± 0.108 | 0.284 ± 0.155 | 0.588 ± 0.356 |
| 100 | 100 | OutcomeModelTransport | 0.935 ± 0.043 | 0.029 ± 0.190 | 0.833 ± 0.103 | 0.254 ± 0.088 | 0.522 ± 0.265 |
| 100 | 100 | ProposedA | 1.520 ± 0.001 | -1.065 ± 2.389 | 0.454 ± 0.019 | 1.058 ± 0.126 | 2.382 ± 0.578 |
| 100 | 100 | ProposedA_Direct | 1.542 ± 0.268 | -1.311 ± 2.397 | 0.470 ± 0.092 | 1.019 ± 0.076 | 2.364 ± 0.519 |
| 100 | 100 | ProposedA_Direct_NoCrossfit | 1.538 ± 0.254 | -1.307 ± 2.448 | 0.467 ± 0.094 | 0.973 ± 0.115 | 2.611 ± 0.629 |
| 100 | 100 | ProposedA_FullyDirect | 1.721 ± 0.435 | -1.655 ± 3.549 | 0.505 ± 0.053 | 1.066 ± 0.296 | 2.410 ± 1.087 |
| 100 | 100 | ProposedA_FullyJoint | 1.614 ± 0.362 | -1.638 ± 2.989 | 0.486 ± 0.048 | 1.038 ± 0.288 | 2.222 ± 0.978 |
| 100 | 100 | ProposedA_JointProxy | 1.509 ± 0.043 | -1.034 ± 2.324 | 0.456 ± 0.001 | 0.961 ± 0.100 | 2.488 ± 0.076 |
| 100 | 100 | ProposedA_NoCrossfit | 1.535 ± 0.073 | -1.147 ± 2.496 | 0.457 ± 0.009 | 1.016 ± 0.117 | 2.568 ± 0.539 |
| 100 | 100 | ProposedA_Together | 1.524 ± 0.245 | -1.373 ± 2.667 | 0.472 ± 0.034 | 0.941 ± 0.263 | 2.212 ± 1.429 |
| 100 | 100 | ProposedA_Together_Direct | 1.721 ± 0.435 | -1.655 ± 3.549 | 0.505 ± 0.053 | 1.066 ± 0.296 | 2.410 ± 1.087 |
| 100 | 100 | ProposedA_Together_Direct_NoCrossfit | 1.916 ± 0.483 | -1.857 ± 4.085 | 0.489 ± 0.071 | 1.224 ± 0.206 | 3.088 ± 0.743 |
| 100 | 100 | ProposedA_Together_NoCrossfit | 1.662 ± 0.248 | -1.434 ± 3.030 | 0.483 ± 0.062 | 1.000 ± 0.159 | 2.723 ± 1.061 |
| 100 | 100 | ProposedB_LinearStepB | 1.492 ± 0.098 | -0.980 ± 2.321 | 0.453 ± 0.043 | 1.115 ± 0.185 | 2.348 ± 0.130 |
| 100 | 100 | ProposedB_SourceDR | 1.208 ± 0.127 | 0.472 ± 1.467 | 0.427 ± 0.014 | 1.296 ± 0.476 | 2.601 ± 0.850 |
| 100 | 100 | ProxyOnly | 1.086 ± 0.106 | -0.952 ± 0.083 | 0.312 ± 0.013 | 1.003 ± 0.209 | 1.676 ± 0.141 |
| 100 | 100 | TargetOnlyDR | 1.309 ± 0.205 | -1.443 ± 1.752 | 0.384 ± 0.038 | 0.828 ± 0.260 | 1.944 ± 1.335 |
| 100 | 500 | AnchorOnly | 1.694 ± 0.022 | 0.081 ± 0.198 | 0.596 ± 0.004 | 1.061 ± 0.137 | 2.558 ± 0.258 |
| 100 | 500 | AnchorPlugin | 1.073 ± 0.013 | 0.382 ± 0.007 | 0.694 ± 0.108 | 0.395 ± 0.052 | 0.845 ± 0.104 |
| 100 | 500 | DRLearner_PooledNoSite | 0.986 ± 0.013 | -0.089 ± 0.393 | 0.799 ± 0.202 | 0.314 ± 0.141 | 0.532 ± 0.135 |
| 100 | 500 | DRLearner_PooledWithSite | 0.983 ± 0.013 | -0.047 ± 0.357 | 0.794 ± 0.208 | 0.293 ± 0.082 | 0.527 ± 0.079 |
| 100 | 500 | EntropyBalancing | 0.961 ± 0.014 | -0.030 ± 0.392 | 0.772 ± 0.235 | 0.324 ± 0.061 | 0.603 ± 0.090 |
| 100 | 500 | IPWTransport | 0.971 ± 0.005 | -0.055 ± 0.386 | 0.780 ± 0.224 | 0.309 ± 0.090 | 0.543 ± 0.115 |
| 100 | 500 | OutcomeModelTransport | 0.973 ± 0.002 | -0.052 ± 0.395 | 0.784 ± 0.218 | 0.311 ± 0.073 | 0.572 ± 0.068 |
| 100 | 500 | ProposedA | 1.649 ± 0.034 | 0.064 ± 0.147 | 0.586 ± 0.001 | 1.011 ± 0.103 | 2.705 ± 0.278 |
| 100 | 500 | ProposedA_Direct | 1.634 ± 0.088 | 0.061 ± 0.074 | 0.595 ± 0.004 | 0.967 ± 0.049 | 2.564 ± 0.351 |
| 100 | 500 | ProposedA_Direct_NoCrossfit | 1.682 ± 0.184 | 0.064 ± 0.073 | 0.596 ± 0.005 | 0.982 ± 0.001 | 2.483 ± 0.093 |
| 100 | 500 | ProposedA_FullyDirect | 0.861 ± 0.438 | -0.234 ± 0.296 | 0.200 ± 0.099 | 1.116 ± 0.092 | 2.204 ± 0.337 |
| 100 | 500 | ProposedA_FullyJoint | 0.979 ± 0.247 | -0.120 ± 0.219 | 0.266 ± 0.103 | 0.994 ± 0.133 | 2.038 ± 0.078 |
| 100 | 500 | ProposedA_JointProxy | 1.684 ± 0.090 | 0.157 ± 0.160 | 0.597 ± 0.002 | 1.000 ± 0.075 | 2.686 ± 0.422 |
| 100 | 500 | ProposedA_NoCrossfit | 1.664 ± 0.127 | 0.055 ± 0.134 | 0.594 ± 0.007 | 0.955 ± 0.057 | 2.604 ± 0.334 |
| 100 | 500 | ProposedA_Together | 1.069 ± 0.153 | -0.030 ± 0.164 | 0.349 ± 0.119 | 0.775 ± 0.029 | 1.877 ± 0.106 |
| 100 | 500 | ProposedA_Together_Direct | 0.861 ± 0.438 | -0.234 ± 0.296 | 0.200 ± 0.099 | 1.116 ± 0.092 | 2.204 ± 0.337 |
| 100 | 500 | ProposedA_Together_Direct_NoCrossfit | 0.880 ± 0.444 | -0.238 ± 0.313 | 0.186 ± 0.087 | 1.148 ± 0.243 | 2.045 ± 0.587 |
| 100 | 500 | ProposedA_Together_NoCrossfit | 1.119 ± 0.196 | 0.021 ± 0.156 | 0.350 ± 0.127 | 0.777 ± 0.029 | 1.659 ± 0.045 |
| 100 | 500 | ProposedB_LinearStepB | 1.626 ± 0.039 | 0.091 ± 0.151 | 0.575 ± 0.004 | 1.008 ± 0.099 | 2.517 ± 0.307 |
| 100 | 500 | ProposedB_SourceDR | 1.358 ± 0.026 | -0.412 ± 0.127 | 0.425 ± 0.170 | 0.734 ± 0.223 | 1.856 ± 0.294 |
| 100 | 500 | ProxyOnly | 0.384 ± 0.208 | 0.863 ± 0.047 | 0.175 ± 0.044 | 4.200 ± 2.137 | 7.450 ± 3.831 |
| 100 | 500 | TargetOnlyDR | 1.424 ± 0.048 | -0.067 ± 0.094 | 0.431 ± 0.005 | 0.925 ± 0.145 | 1.882 ± 0.022 |
| 100 | 1000 | AnchorOnly | 1.320 ± 0.174 | -0.393 ± 0.222 | 0.391 ± 0.064 | 0.990 ± 0.302 | 2.106 ± 0.288 |
| 100 | 1000 | AnchorPlugin | 0.987 ± 0.097 | 0.010 ± 0.049 | 0.624 ± 0.210 | 0.304 ± 0.108 | 0.570 ± 0.157 |
| 100 | 1000 | DRLearner_PooledNoSite | 0.986 ± 0.003 | 0.020 ± 0.610 | 0.827 ± 0.184 | 0.440 ± 0.011 | 0.633 ± 0.045 |
| 100 | 1000 | DRLearner_PooledWithSite | 0.983 ± 0.003 | -0.073 ± 0.524 | 0.823 ± 0.190 | 0.376 ± 0.124 | 0.610 ± 0.084 |
| 100 | 1000 | EntropyBalancing | 0.968 ± 0.016 | -0.077 ± 0.693 | 0.813 ± 0.204 | 0.498 ± 0.143 | 0.682 ± 0.089 |
| 100 | 1000 | IPWTransport | 0.967 ± 0.018 | -0.075 ± 0.745 | 0.806 ± 0.213 | 0.535 ± 0.139 | 0.798 ± 0.030 |
| 100 | 1000 | OutcomeModelTransport | 0.966 ± 0.018 | -0.079 ± 0.611 | 0.803 ± 0.213 | 0.438 ± 0.147 | 0.636 ± 0.194 |
| 100 | 1000 | ProposedA | 1.352 ± 0.233 | -0.453 ± 0.305 | 0.392 ± 0.071 | 0.992 ± 0.270 | 2.387 ± 0.213 |
| 100 | 1000 | ProposedA_Direct | 1.699 ± 0.059 | -0.764 ± 0.187 | 0.533 ± 0.041 | 1.133 ± 0.206 | 2.893 ± 0.778 |
| 100 | 1000 | ProposedA_Direct_NoCrossfit | 1.704 ± 0.078 | -0.763 ± 0.108 | 0.543 ± 0.054 | 1.142 ± 0.183 | 3.113 ± 0.424 |
| 100 | 1000 | ProposedA_FullyDirect | 0.239 ± 0.140 | 0.594 ± 0.007 | 0.038 ± 0.030 | 1.666 ± 0.530 | 3.975 ± 0.771 |
| 100 | 1000 | ProposedA_FullyJoint | 0.326 ± 0.201 | 0.534 ± 0.040 | 0.059 ± 0.051 | 1.390 ± 0.482 | 3.167 ± 0.002 |
| 100 | 1000 | ProposedA_JointProxy | 1.539 ± 0.191 | -0.549 ± 0.122 | 0.458 ± 0.053 | 1.092 ± 0.130 | 2.670 ± 0.376 |
| 100 | 1000 | ProposedA_NoCrossfit | 1.522 ± 0.192 | -0.560 ± 0.126 | 0.480 ± 0.071 | 1.018 ± 0.166 | 2.814 ± 0.129 |
| 100 | 1000 | ProposedA_Together | 0.401 ± 0.273 | 0.464 ± 0.023 | 0.079 ± 0.072 | 1.436 ± 0.341 | 2.920 ± 0.727 |
| 100 | 1000 | ProposedA_Together_Direct | 0.239 ± 0.140 | 0.594 ± 0.007 | 0.038 ± 0.030 | 1.666 ± 0.530 | 3.975 ± 0.771 |
| 100 | 1000 | ProposedA_Together_Direct_NoCrossfit | 0.272 ± 0.159 | 0.561 ± 0.011 | 0.042 ± 0.031 | 1.560 ± 0.603 | 3.597 ± 0.738 |
| 100 | 1000 | ProposedA_Together_NoCrossfit | 0.414 ± 0.277 | 0.453 ± 0.037 | 0.082 ± 0.074 | 1.372 ± 0.311 | 2.748 ± 0.320 |
| 100 | 1000 | ProposedB_LinearStepB | 1.358 ± 0.152 | -0.477 ± 0.190 | 0.399 ± 0.053 | 1.019 ± 0.236 | 2.365 ± 0.011 |
| 100 | 1000 | ProposedB_SourceDR | 1.084 ± 0.303 | 0.387 ± 0.160 | 0.310 ± 0.167 | 0.616 ± 0.036 | 1.444 ± 0.138 |
| 100 | 1000 | ProxyOnly | 0.205 ± 0.062 | 0.381 ± 1.037 | 0.166 ± 0.081 | 6.507 ± 1.643 | 17.507 ± 7.064 |
| 100 | 1000 | TargetOnlyDR | 0.464 ± 0.177 | 0.221 ± 0.539 | 0.100 ± 0.043 | 1.160 ± 0.341 | 2.531 ± 0.034 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 0.956 ± 0.029 | -0.003 ± 1.013 | 0.548 ± 0.200 | 0.747 ± 0.026 | 1.258 ± 0.259 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 0.822 ± 0.232 | 0.003 ± 0.446 | 0.508 ± 0.322 | 0.705 ± 0.525 | 1.536 ± 1.328 |
| 500 | 0 | IPWTransport | 0.827 ± 0.225 | 0.012 ± 0.446 | 0.511 ± 0.318 | 0.690 ± 0.516 | 1.593 ± 1.375 |
| 500 | 0 | OutcomeModelTransport | 0.838 ± 0.229 | -0.066 ± 0.400 | 0.517 ± 0.314 | 0.716 ± 0.518 | 1.485 ± 1.264 |
| 500 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 0.966 ± 0.478 | 0.698 ± 0.043 | 0.257 ± 0.274 | 0.904 ± 0.120 | 2.469 ± 0.622 |
| 500 | 0 | ProxyOnly | 1.146 ± 0.105 | -0.251 ± 2.513 | 0.356 ± 0.173 | 1.600 ± 0.298 | 2.852 ± 0.041 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 0.931 ± 0.091 | 0.589 ± 0.140 | 0.227 ± 0.032 | 1.260 ± 0.058 | 2.866 ± 0.760 |
| 500 | 100 | AnchorPlugin | 1.080 ± 0.255 | -0.607 ± 0.571 | 0.626 ± 0.124 | 0.832 ± 0.537 | 1.807 ± 1.093 |
| 500 | 100 | DRLearner_PooledNoSite | 0.990 ± 0.057 | -0.922 ± 0.464 | 0.810 ± 0.067 | 0.927 ± 0.469 | 1.333 ± 0.324 |
| 500 | 100 | DRLearner_PooledWithSite | 0.994 ± 0.051 | -0.890 ± 0.473 | 0.815 ± 0.062 | 0.895 ± 0.480 | 1.339 ± 0.289 |
| 500 | 100 | EntropyBalancing | 0.975 ± 0.073 | -1.028 ± 0.559 | 0.768 ± 0.096 | 1.033 ± 0.557 | 1.483 ± 0.316 |
| 500 | 100 | IPWTransport | 0.979 ± 0.073 | -1.031 ± 0.578 | 0.772 ± 0.095 | 1.035 ± 0.576 | 1.516 ± 0.240 |
| 500 | 100 | OutcomeModelTransport | 0.987 ± 0.057 | -1.007 ± 0.513 | 0.804 ± 0.064 | 1.012 ± 0.513 | 1.419 ± 0.267 |
| 500 | 100 | ProposedA | 1.584 ± 0.040 | 1.040 ± 0.649 | 0.535 ± 0.004 | 1.058 ± 0.023 | 2.754 ± 0.224 |
| 500 | 100 | ProposedA_Direct | 1.587 ± 0.065 | 0.939 ± 0.669 | 0.555 ± 0.019 | 1.016 ± 0.088 | 3.101 ± 0.439 |
| 500 | 100 | ProposedA_Direct_NoCrossfit | 1.609 ± 0.099 | 1.000 ± 0.701 | 0.555 ± 0.008 | 1.085 ± 0.031 | 3.280 ± 0.243 |
| 500 | 100 | ProposedA_FullyDirect | 0.435 ± 0.014 | -0.478 ± 0.475 | 0.070 ± 0.007 | 1.208 ± 0.086 | 2.252 ± 0.249 |
| 500 | 100 | ProposedA_FullyJoint | 0.659 ± 0.040 | -0.094 ± 0.438 | 0.125 ± 0.010 | 1.045 ± 0.017 | 2.543 ± 0.666 |
| 500 | 100 | ProposedA_JointProxy | 1.602 ± 0.068 | 1.149 ± 0.824 | 0.547 ± 0.001 | 1.060 ± 0.016 | 3.044 ± 0.380 |
| 500 | 100 | ProposedA_NoCrossfit | 1.634 ± 0.197 | 1.195 ± 0.922 | 0.563 ± 0.030 | 1.077 ± 0.230 | 3.027 ± 0.339 |
| 500 | 100 | ProposedA_Together | 0.922 ± 0.080 | 0.441 ± 0.378 | 0.213 ± 0.003 | 1.032 ± 0.014 | 2.218 ± 0.099 |
| 500 | 100 | ProposedA_Together_Direct | 0.435 ± 0.014 | -0.478 ± 0.475 | 0.070 ± 0.007 | 1.208 ± 0.086 | 2.252 ± 0.249 |
| 500 | 100 | ProposedA_Together_Direct_NoCrossfit | 0.441 ± 0.023 | -0.467 ± 0.473 | 0.065 ± 0.011 | 1.176 ± 0.071 | 2.169 ± 0.333 |
| 500 | 100 | ProposedA_Together_NoCrossfit | 0.978 ± 0.121 | 0.521 ± 0.412 | 0.228 ± 0.012 | 1.031 ± 0.062 | 2.102 ± 0.155 |
| 500 | 100 | ProposedB_LinearStepB | 1.710 ± 0.191 | 1.226 ± 0.987 | 0.589 ± 0.021 | 1.179 ± 0.100 | 3.089 ± 0.346 |
| 500 | 100 | ProposedB_SourceDR | 1.343 ± 0.240 | -1.453 ± 1.701 | 0.364 ± 0.068 | 1.393 ± 1.260 | 3.097 ± 1.951 |
| 500 | 100 | ProxyOnly | 1.593 ± 0.384 | 0.249 ± 0.209 | 0.412 ± 0.090 | 0.952 ± 0.458 | 2.712 ± 1.508 |
| 500 | 100 | TargetOnlyDR | 1.018 ± 0.220 | 0.651 ± 0.058 | 0.225 ± 0.041 | 1.111 ± 0.061 | 2.220 ± 0.435 |
| 500 | 500 | AnchorOnly | 1.757 ± 0.294 | -0.008 ± 0.801 | 0.638 ± 0.009 | 1.390 ± 0.119 | 3.363 ± 0.286 |
| 500 | 500 | AnchorPlugin | 1.200 ± 0.159 | 0.323 ± 0.905 | 0.729 ± 0.005 | 0.905 ± 0.090 | 1.732 ± 0.587 |
| 500 | 500 | DRLearner_PooledNoSite | 1.055 ± 0.106 | 0.520 ± 1.109 | 0.811 ± 0.015 | 0.962 ± 0.538 | 1.475 ± 0.217 |
| 500 | 500 | DRLearner_PooledWithSite | 1.057 ± 0.105 | 0.518 ± 1.124 | 0.812 ± 0.012 | 0.973 ± 0.527 | 1.469 ± 0.187 |
| 500 | 500 | EntropyBalancing | 1.024 ± 0.128 | 0.606 ± 1.204 | 0.786 ± 0.025 | 1.075 ± 0.744 | 1.617 ± 0.825 |
| 500 | 500 | IPWTransport | 1.026 ± 0.123 | 0.630 ± 1.217 | 0.788 ± 0.023 | 1.082 ± 0.764 | 1.546 ± 0.889 |
| 500 | 500 | OutcomeModelTransport | 1.040 ± 0.117 | 0.604 ± 1.239 | 0.791 ± 0.016 | 1.063 ± 0.718 | 1.531 ± 0.610 |
| 500 | 500 | ProposedA | 1.808 ± 0.490 | 0.161 ± 1.104 | 0.636 ± 0.036 | 1.379 ± 0.368 | 3.402 ± 0.642 |
| 500 | 500 | ProposedA_Direct | 1.819 ± 0.477 | 0.150 ± 1.036 | 0.635 ± 0.026 | 1.373 ± 0.346 | 3.310 ± 0.607 |
| 500 | 500 | ProposedA_Direct_NoCrossfit | 1.825 ± 0.482 | 0.157 ± 1.043 | 0.636 ± 0.028 | 1.358 ± 0.368 | 3.324 ± 0.640 |
| 500 | 500 | ProposedA_FullyDirect | 1.801 ± 0.491 | 0.115 ± 0.991 | 0.632 ± 0.025 | 1.320 ± 0.265 | 3.337 ± 0.831 |
| 500 | 500 | ProposedA_FullyJoint | 1.784 ± 0.479 | 0.163 ± 1.076 | 0.631 ± 0.033 | 1.355 ± 0.256 | 3.168 ± 0.778 |
| 500 | 500 | ProposedA_JointProxy | 1.827 ± 0.481 | 0.194 ± 1.135 | 0.646 ± 0.039 | 1.373 ± 0.283 | 3.404 ± 0.674 |
| 500 | 500 | ProposedA_NoCrossfit | 1.816 ± 0.483 | 0.164 ± 1.081 | 0.636 ± 0.035 | 1.383 ± 0.367 | 3.396 ± 0.575 |
| 500 | 500 | ProposedA_Together | 1.827 ± 0.508 | 0.133 ± 1.148 | 0.635 ± 0.029 | 1.367 ± 0.306 | 3.335 ± 0.761 |
| 500 | 500 | ProposedA_Together_Direct | 1.801 ± 0.491 | 0.115 ± 0.991 | 0.632 ± 0.025 | 1.320 ± 0.265 | 3.337 ± 0.831 |
| 500 | 500 | ProposedA_Together_Direct_NoCrossfit | 1.859 ± 0.532 | 0.192 ± 1.076 | 0.633 ± 0.034 | 1.384 ± 0.323 | 3.414 ± 0.736 |
| 500 | 500 | ProposedA_Together_NoCrossfit | 1.823 ± 0.497 | 0.163 ± 1.143 | 0.635 ± 0.035 | 1.368 ± 0.314 | 3.455 ± 0.602 |
| 500 | 500 | ProposedB_LinearStepB | 1.794 ± 0.493 | 0.099 ± 1.076 | 0.630 ± 0.038 | 1.287 ± 0.319 | 3.266 ± 0.530 |
| 500 | 500 | ProposedB_SourceDR | 1.472 ± 0.190 | 0.064 ± 0.059 | 0.427 ± 0.001 | 0.847 ± 0.096 | 2.071 ± 0.116 |
| 500 | 500 | ProxyOnly | 1.596 ± 0.287 | -0.139 ± 2.444 | 0.397 ± 0.136 | 1.263 ± 0.376 | 3.281 ± 1.394 |
| 500 | 500 | TargetOnlyDR | 1.686 ± 0.427 | -0.088 ± 0.703 | 0.631 ± 0.034 | 1.265 ± 0.315 | 3.072 ± 0.875 |
| 500 | 1000 | AnchorOnly | 1.367 ± 0.045 | -0.406 ± 0.171 | 0.511 ± 0.071 | 0.735 ± 0.172 | 2.344 ± 0.277 |
| 500 | 1000 | AnchorPlugin | 1.267 ± 0.085 | 0.686 ± 1.138 | 0.645 ± 0.021 | 1.107 ± 0.406 | 2.166 ± 0.470 |
| 500 | 1000 | DRLearner_PooledNoSite | 1.082 ± 0.073 | 0.529 ± 0.026 | 0.738 ± 0.104 | 0.601 ± 0.055 | 1.313 ± 0.251 |
| 500 | 1000 | DRLearner_PooledWithSite | 1.077 ± 0.074 | 0.558 ± 0.010 | 0.732 ± 0.104 | 0.607 ± 0.062 | 1.325 ± 0.303 |
| 500 | 1000 | EntropyBalancing | 1.063 ± 0.049 | 0.705 ± 0.040 | 0.693 ± 0.098 | 0.722 ± 0.051 | 1.227 ± 0.203 |
| 500 | 1000 | IPWTransport | 1.061 ± 0.052 | 0.702 ± 0.035 | 0.691 ± 0.103 | 0.722 ± 0.051 | 1.228 ± 0.213 |
| 500 | 1000 | OutcomeModelTransport | 1.049 ± 0.087 | 0.702 ± 0.059 | 0.686 ± 0.117 | 0.708 ± 0.075 | 1.347 ± 0.374 |
| 500 | 1000 | ProposedA | 1.336 ± 0.093 | -0.481 ± 0.085 | 0.506 ± 0.079 | 0.722 ± 0.251 | 2.086 ± 0.416 |
| 500 | 1000 | ProposedA_Direct | 1.375 ± 0.126 | -0.522 ± 0.141 | 0.516 ± 0.093 | 0.769 ± 0.350 | 2.198 ± 0.581 |
| 500 | 1000 | ProposedA_Direct_NoCrossfit | 1.372 ± 0.122 | -0.517 ± 0.135 | 0.514 ± 0.090 | 0.726 ± 0.376 | 2.264 ± 0.580 |
| 500 | 1000 | ProposedA_FullyDirect | 1.401 ± 0.106 | -0.721 ± 0.027 | 0.511 ± 0.074 | 0.797 ± 0.291 | 2.017 ± 0.355 |
| 500 | 1000 | ProposedA_FullyJoint | 1.387 ± 0.131 | -0.664 ± 0.027 | 0.512 ± 0.088 | 0.805 ± 0.351 | 2.258 ± 0.490 |
| 500 | 1000 | ProposedA_JointProxy | 1.335 ± 0.110 | -0.458 ± 0.116 | 0.501 ± 0.091 | 0.713 ± 0.289 | 2.135 ± 0.558 |
| 500 | 1000 | ProposedA_NoCrossfit | 1.329 ± 0.101 | -0.471 ± 0.080 | 0.505 ± 0.082 | 0.690 ± 0.272 | 2.064 ± 0.679 |
| 500 | 1000 | ProposedA_Together | 1.385 ± 0.094 | -0.662 ± 0.031 | 0.521 ± 0.076 | 0.822 ± 0.253 | 2.196 ± 0.797 |
| 500 | 1000 | ProposedA_Together_Direct | 1.401 ± 0.106 | -0.721 ± 0.027 | 0.511 ± 0.074 | 0.797 ± 0.291 | 2.017 ± 0.355 |
| 500 | 1000 | ProposedA_Together_Direct_NoCrossfit | 1.451 ± 0.102 | -0.762 ± 0.006 | 0.518 ± 0.076 | 0.887 ± 0.289 | 2.241 ± 0.539 |
| 500 | 1000 | ProposedA_Together_NoCrossfit | 1.389 ± 0.112 | -0.680 ± 0.007 | 0.512 ± 0.083 | 0.785 ± 0.270 | 2.376 ± 0.565 |
| 500 | 1000 | ProposedB_LinearStepB | 1.338 ± 0.074 | -0.480 ± 0.081 | 0.506 ± 0.074 | 0.753 ± 0.193 | 2.134 ± 0.673 |
| 500 | 1000 | ProposedB_SourceDR | 1.324 ± 0.051 | 1.225 ± 0.328 | 0.324 ± 0.151 | 1.184 ± 0.218 | 2.290 ± 0.343 |
| 500 | 1000 | ProxyOnly | 1.133 ± 0.281 | -0.334 ± 2.350 | 0.322 ± 0.014 | 1.297 ± 0.082 | 2.796 ± 0.738 |
| 500 | 1000 | TargetOnlyDR | 1.348 ± 0.036 | -0.499 ± 0.099 | 0.520 ± 0.055 | 0.748 ± 0.216 | 2.205 ± 0.040 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 1.077 ± 0.092 | 0.923 ± 0.197 | 0.774 ± 0.136 | 0.903 ± 0.235 | 1.489 ± 0.157 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 0.997 ± 0.135 | 0.172 ± 0.718 | 0.868 ± 0.054 | 0.517 ± 0.144 | 1.170 ± 0.378 |
| 1000 | 0 | IPWTransport | 0.997 ± 0.137 | 0.173 ± 0.722 | 0.867 ± 0.056 | 0.514 ± 0.151 | 1.177 ± 0.375 |
| 1000 | 0 | OutcomeModelTransport | 0.989 ± 0.108 | 0.169 ± 0.681 | 0.878 ± 0.038 | 0.469 ± 0.142 | 1.000 ± 0.470 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 1.426 ± 0.223 | -0.024 ± 0.990 | 0.369 ± 0.034 | 0.851 ± 0.014 | 2.285 ± 0.522 |
| 1000 | 0 | ProxyOnly | 1.296 ± 0.398 | 1.210 ± 0.914 | 0.340 ± 0.050 | 1.426 ± 0.571 | 2.735 ± 0.502 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 0.979 ± 0.313 | -0.037 ± 0.116 | 0.326 ± 0.044 | 0.795 ± 0.382 | 1.819 ± 0.450 |
| 1000 | 100 | AnchorPlugin | 1.114 ± 0.097 | 0.366 ± 0.535 | 0.770 ± 0.104 | 0.515 ± 0.494 | 1.217 ± 1.146 |
| 1000 | 100 | DRLearner_PooledNoSite | 0.988 ± 0.029 | 0.484 ± 0.083 | 0.932 ± 0.078 | 0.483 ± 0.074 | 0.668 ± 0.140 |
| 1000 | 100 | DRLearner_PooledWithSite | 0.987 ± 0.027 | 0.421 ± 0.225 | 0.935 ± 0.075 | 0.420 ± 0.217 | 0.581 ± 0.281 |
| 1000 | 100 | EntropyBalancing | 0.963 ± 0.081 | 0.533 ± 0.346 | 0.896 ± 0.125 | 0.540 ± 0.336 | 0.915 ± 0.609 |
| 1000 | 100 | IPWTransport | 0.960 ± 0.084 | 0.538 ± 0.351 | 0.893 ± 0.128 | 0.545 ± 0.342 | 0.935 ± 0.648 |
| 1000 | 100 | OutcomeModelTransport | 0.983 ± 0.034 | 0.525 ± 0.309 | 0.927 ± 0.084 | 0.526 ± 0.305 | 0.718 ± 0.394 |
| 1000 | 100 | ProposedA | 1.450 ± 0.350 | -0.330 ± 0.086 | 0.561 ± 0.001 | 0.882 ± 0.411 | 2.118 ± 1.590 |
| 1000 | 100 | ProposedA_Direct | 1.434 ± 0.340 | -0.341 ± 0.263 | 0.575 ± 0.003 | 0.835 ± 0.463 | 2.162 ± 1.537 |
| 1000 | 100 | ProposedA_Direct_NoCrossfit | 1.430 ± 0.317 | -0.326 ± 0.220 | 0.581 ± 0.003 | 0.846 ± 0.473 | 2.318 ± 1.546 |
| 1000 | 100 | ProposedA_FullyDirect | 0.538 ± 0.112 | 0.367 ± 0.336 | 0.162 ± 0.089 | 1.192 ± 0.331 | 2.040 ± 0.153 |
| 1000 | 100 | ProposedA_FullyJoint | 0.569 ± 0.068 | 0.368 ± 0.261 | 0.184 ± 0.099 | 1.237 ± 0.460 | 1.998 ± 0.735 |
| 1000 | 100 | ProposedA_JointProxy | 1.370 ± 0.364 | -0.258 ± 0.158 | 0.548 ± 0.011 | 0.768 ± 0.510 | 1.971 ± 1.594 |
| 1000 | 100 | ProposedA_NoCrossfit | 1.430 ± 0.283 | -0.295 ± 0.044 | 0.571 ± 0.011 | 0.835 ± 0.434 | 2.505 ± 1.595 |
| 1000 | 100 | ProposedA_Together | 0.765 ± 0.101 | 0.278 ± 0.224 | 0.248 ± 0.147 | 1.017 ± 0.395 | 1.882 ± 0.829 |
| 1000 | 100 | ProposedA_Together_Direct | 0.538 ± 0.112 | 0.367 ± 0.336 | 0.162 ± 0.089 | 1.192 ± 0.331 | 2.040 ± 0.153 |
| 1000 | 100 | ProposedA_Together_Direct_NoCrossfit | 0.543 ± 0.113 | 0.356 ± 0.338 | 0.160 ± 0.087 | 1.200 ± 0.405 | 2.110 ± 0.705 |
| 1000 | 100 | ProposedA_Together_NoCrossfit | 0.787 ± 0.114 | 0.252 ± 0.234 | 0.256 ± 0.147 | 1.072 ± 0.371 | 1.762 ± 0.725 |
| 1000 | 100 | ProposedB_LinearStepB | 1.355 ± 0.254 | -0.201 ± 0.225 | 0.493 ± 0.037 | 0.784 ± 0.307 | 1.842 ± 0.628 |
| 1000 | 100 | ProposedB_SourceDR | 1.340 ± 0.203 | 0.625 ± 0.211 | 0.473 ± 0.009 | 0.904 ± 0.077 | 2.266 ± 0.574 |
| 1000 | 100 | ProxyOnly | 1.533 ± 0.188 | 0.128 ± 0.904 | 0.506 ± 0.022 | 1.050 ± 0.281 | 2.812 ± 1.016 |
| 1000 | 100 | TargetOnlyDR | 0.831 ± 0.468 | -0.005 ± 0.268 | 0.230 ± 0.046 | 1.250 ± 0.095 | 2.842 ± 0.254 |
| 1000 | 500 | AnchorOnly | 1.379 ± 0.206 | 0.247 ± 0.996 | 0.593 ± 0.042 | 0.977 ± 0.500 | 2.322 ± 0.953 |
| 1000 | 500 | AnchorPlugin | 0.996 ± 0.046 | 0.383 ± 0.761 | 0.667 ± 0.036 | 0.595 ± 0.436 | 0.999 ± 0.392 |
| 1000 | 500 | DRLearner_PooledNoSite | 1.075 ± 0.067 | 0.051 ± 1.342 | 0.912 ± 0.001 | 0.973 ± 0.053 | 1.642 ± 0.346 |
| 1000 | 500 | DRLearner_PooledWithSite | 1.076 ± 0.062 | 0.009 ± 1.274 | 0.914 ± 0.001 | 0.927 ± 0.003 | 1.554 ± 0.431 |
| 1000 | 500 | EntropyBalancing | 1.057 ± 0.044 | -0.039 ± 1.663 | 0.886 ± 0.002 | 1.180 ± 0.052 | 1.749 ± 0.226 |
| 1000 | 500 | IPWTransport | 1.056 ± 0.042 | -0.040 ± 1.668 | 0.886 ± 0.001 | 1.184 ± 0.053 | 1.727 ± 0.219 |
| 1000 | 500 | OutcomeModelTransport | 1.077 ± 0.070 | -0.020 ± 1.609 | 0.901 ± 0.001 | 1.146 ± 0.030 | 1.829 ± 0.483 |
| 1000 | 500 | ProposedA | 1.422 ± 0.193 | 0.080 ± 0.752 | 0.598 ± 0.011 | 0.909 ± 0.337 | 2.122 ± 0.943 |
| 1000 | 500 | ProposedA_Direct | 1.420 ± 0.154 | 0.079 ± 0.807 | 0.589 ± 0.001 | 0.888 ± 0.195 | 2.201 ± 0.927 |
| 1000 | 500 | ProposedA_Direct_NoCrossfit | 1.417 ± 0.155 | 0.089 ± 0.803 | 0.587 ± 0.001 | 0.911 ± 0.230 | 2.160 ± 1.105 |
| 1000 | 500 | ProposedA_FullyDirect | 1.473 ± 0.220 | 0.217 ± 1.170 | 0.594 ± 0.038 | 1.003 ± 0.427 | 2.439 ± 1.496 |
| 1000 | 500 | ProposedA_FullyJoint | 1.440 ± 0.211 | 0.228 ± 1.069 | 0.591 ± 0.025 | 1.014 ± 0.457 | 2.371 ± 1.206 |
| 1000 | 500 | ProposedA_JointProxy | 1.423 ± 0.182 | 0.123 ± 0.810 | 0.597 ± 0.006 | 0.926 ± 0.362 | 2.215 ± 1.021 |
| 1000 | 500 | ProposedA_NoCrossfit | 1.413 ± 0.176 | 0.069 ± 0.745 | 0.597 ± 0.006 | 0.892 ± 0.304 | 2.158 ± 0.798 |
| 1000 | 500 | ProposedA_Together | 1.427 ± 0.211 | 0.148 ± 0.941 | 0.601 ± 0.038 | 1.008 ± 0.455 | 2.216 ± 1.212 |
| 1000 | 500 | ProposedA_Together_Direct | 1.473 ± 0.220 | 0.217 ± 1.170 | 0.594 ± 0.038 | 1.003 ± 0.427 | 2.439 ± 1.496 |
| 1000 | 500 | ProposedA_Together_Direct_NoCrossfit | 1.492 ± 0.199 | 0.172 ± 1.206 | 0.587 ± 0.030 | 1.002 ± 0.383 | 2.512 ± 1.190 |
| 1000 | 500 | ProposedA_Together_NoCrossfit | 1.425 ± 0.204 | 0.127 ± 0.928 | 0.598 ± 0.028 | 1.000 ± 0.473 | 2.258 ± 1.161 |
| 1000 | 500 | ProposedB_LinearStepB | 1.459 ± 0.178 | 0.082 ± 0.887 | 0.613 ± 0.009 | 1.039 ± 0.278 | 2.337 ± 0.887 |
| 1000 | 500 | ProposedB_SourceDR | 1.376 ± 0.054 | -0.459 ± 1.976 | 0.463 ± 0.051 | 1.407 ± 0.503 | 2.858 ± 0.570 |
| 1000 | 500 | ProxyOnly | 1.177 ± 0.399 | 0.709 ± 0.190 | 0.383 ± 0.060 | 0.797 ± 0.020 | 2.128 ± 0.022 |
| 1000 | 500 | TargetOnlyDR | 1.362 ± 0.213 | 0.269 ± 0.931 | 0.586 ± 0.013 | 0.951 ± 0.525 | 2.501 ± 1.354 |
| 1000 | 1000 | AnchorOnly | 1.759 ± 0.060 | 0.554 ± 0.129 | 0.590 ± 0.024 | 1.082 ± 0.072 | 2.931 ± 0.458 |
| 1000 | 1000 | AnchorPlugin | 0.947 ± 0.174 | -0.284 ± 0.763 | 0.543 ± 0.067 | 0.734 ± 0.105 | 1.309 ± 0.102 |
| 1000 | 1000 | DRLearner_PooledNoSite | 0.919 ± 0.210 | -0.358 ± 0.357 | 0.620 ± 0.060 | 0.655 ± 0.066 | 1.371 ± 0.521 |
| 1000 | 1000 | DRLearner_PooledWithSite | 0.921 ± 0.207 | -0.350 ± 0.345 | 0.622 ± 0.057 | 0.642 ± 0.070 | 1.353 ± 0.531 |
| 1000 | 1000 | EntropyBalancing | 0.850 ± 0.241 | -0.497 ± 0.575 | 0.542 ± 0.070 | 0.982 ± 0.120 | 1.935 ± 0.821 |
| 1000 | 1000 | IPWTransport | 0.849 ± 0.241 | -0.495 ± 0.579 | 0.541 ± 0.072 | 0.990 ± 0.131 | 1.932 ± 0.825 |
| 1000 | 1000 | OutcomeModelTransport | 0.858 ± 0.210 | -0.497 ± 0.539 | 0.551 ± 0.049 | 0.918 ± 0.060 | 1.640 ± 0.757 |
| 1000 | 1000 | ProposedA | 1.677 ± 0.068 | 0.523 ± 0.168 | 0.582 ± 0.018 | 1.024 ± 0.079 | 2.455 ± 0.104 |
| 1000 | 1000 | ProposedA_Direct | 1.659 ± 0.052 | 0.527 ± 0.199 | 0.574 ± 0.015 | 0.973 ± 0.087 | 2.468 ± 0.104 |
| 1000 | 1000 | ProposedA_Direct_NoCrossfit | 1.659 ± 0.039 | 0.519 ± 0.209 | 0.574 ± 0.011 | 0.960 ± 0.100 | 2.427 ± 0.160 |
| 1000 | 1000 | ProposedA_FullyDirect | 1.680 ± 0.067 | 0.517 ± 0.136 | 0.581 ± 0.023 | 0.985 ± 0.012 | 2.426 ± 0.013 |
| 1000 | 1000 | ProposedA_FullyJoint | 1.718 ± 0.095 | 0.549 ± 0.156 | 0.585 ± 0.025 | 1.033 ± 0.023 | 2.653 ± 0.190 |
| 1000 | 1000 | ProposedA_JointProxy | 1.698 ± 0.071 | 0.558 ± 0.191 | 0.580 ± 0.015 | 1.023 ± 0.087 | 2.620 ± 0.115 |
| 1000 | 1000 | ProposedA_NoCrossfit | 1.672 ± 0.073 | 0.522 ± 0.155 | 0.580 ± 0.021 | 1.044 ± 0.138 | 2.448 ± 0.083 |
| 1000 | 1000 | ProposedA_Together | 1.691 ± 0.074 | 0.514 ± 0.132 | 0.589 ± 0.020 | 1.074 ± 0.095 | 2.552 ± 0.054 |
| 1000 | 1000 | ProposedA_Together_Direct | 1.680 ± 0.067 | 0.517 ± 0.136 | 0.581 ± 0.023 | 0.985 ± 0.012 | 2.426 ± 0.013 |
| 1000 | 1000 | ProposedA_Together_Direct_NoCrossfit | 1.696 ± 0.072 | 0.529 ± 0.125 | 0.577 ± 0.026 | 1.004 ± 0.045 | 2.574 ± 0.140 |
| 1000 | 1000 | ProposedA_Together_NoCrossfit | 1.691 ± 0.059 | 0.505 ± 0.165 | 0.581 ± 0.018 | 1.065 ± 0.081 | 2.460 ± 0.147 |
| 1000 | 1000 | ProposedB_LinearStepB | 1.700 ± 0.103 | 0.576 ± 0.145 | 0.591 ± 0.028 | 1.051 ± 0.088 | 2.509 ± 0.152 |
| 1000 | 1000 | ProposedB_SourceDR | 1.296 ± 0.325 | -0.814 ± 0.126 | 0.260 ± 0.050 | 0.827 ± 0.134 | 1.901 ± 1.045 |
| 1000 | 1000 | ProxyOnly | 0.967 ± 0.375 | -0.039 ± 0.960 | 0.257 ± 0.082 | 1.055 ± 0.299 | 2.022 ± 0.939 |
| 1000 | 1000 | TargetOnlyDR | 1.705 ± 0.027 | 0.424 ± 0.231 | 0.597 ± 0.012 | 1.045 ± 0.065 | 2.612 ± 0.267 |

### Extended Targeting Metrics

| m0 | m1 | Method | Top-10% Captured | Top-20% Captured | Top-30% Ratio (↑) |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 5.155 ± 0.666 | 3.676 ± 0.701 | 0.747 ± 0.008 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 5.460 ± 0.711 | 4.088 ± 0.874 | 0.840 ± 0.041 |
| 100 | 0 | IPWTransport | 5.574 ± 0.908 | 4.158 ± 0.801 | 0.856 ± 0.036 |
| 100 | 0 | OutcomeModelTransport | 5.551 ± 1.004 | 4.202 ± 0.756 | 0.868 ± 0.027 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 100 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 3.774 ± 1.201 | 2.977 ± 0.794 | 0.602 ± 0.029 |
| 100 | 0 | ProxyOnly | 2.650 ± 0.238 | 1.807 ± 0.129 | 0.354 ± 0.077 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 5.681 ± 1.995 | 4.491 ± 2.553 | 0.641 ± 0.216 |
| 100 | 100 | AnchorPlugin | 6.198 ± 1.694 | 5.042 ± 1.975 | 0.801 ± 0.028 |
| 100 | 100 | DRLearner_PooledNoSite | 7.199 ± 1.781 | 5.940 ± 2.163 | 0.928 ± 0.006 |
| 100 | 100 | DRLearner_PooledWithSite | 7.215 ± 1.803 | 5.948 ± 2.175 | 0.929 ± 0.005 |
| 100 | 100 | EntropyBalancing | 7.198 ± 1.736 | 5.917 ± 2.125 | 0.921 ± 0.004 |
| 100 | 100 | IPWTransport | 7.213 ± 1.801 | 5.920 ± 2.142 | 0.921 ± 0.008 |
| 100 | 100 | OutcomeModelTransport | 7.199 ± 1.781 | 5.940 ± 2.163 | 0.928 ± 0.006 |
| 100 | 100 | ProposedA | 5.831 ± 2.775 | 4.709 ± 2.684 | 0.667 ± 0.173 |
| 100 | 100 | ProposedA_Direct | 5.420 ± 3.214 | 4.694 ± 2.966 | 0.683 ± 0.212 |
| 100 | 100 | ProposedA_Direct_NoCrossfit | 5.331 ± 3.209 | 4.601 ± 3.065 | 0.656 ± 0.234 |
| 100 | 100 | ProposedA_FullyDirect | 5.596 ± 2.667 | 4.754 ± 2.740 | 0.701 ± 0.193 |
| 100 | 100 | ProposedA_FullyJoint | 5.757 ± 2.774 | 4.764 ± 2.582 | 0.694 ± 0.200 |
| 100 | 100 | ProposedA_JointProxy | 5.526 ± 2.928 | 4.554 ± 2.682 | 0.666 ± 0.181 |
| 100 | 100 | ProposedA_NoCrossfit | 5.426 ± 2.857 | 4.634 ± 2.763 | 0.668 ± 0.203 |
| 100 | 100 | ProposedA_Together | 5.633 ± 2.921 | 4.602 ± 2.819 | 0.674 ± 0.198 |
| 100 | 100 | ProposedA_Together_Direct | 5.596 ± 2.667 | 4.754 ± 2.740 | 0.701 ± 0.193 |
| 100 | 100 | ProposedA_Together_Direct_NoCrossfit | 5.307 ± 3.230 | 4.801 ± 2.835 | 0.692 ± 0.217 |
| 100 | 100 | ProposedA_Together_NoCrossfit | 5.549 ± 2.963 | 4.569 ± 2.790 | 0.678 ± 0.209 |
| 100 | 100 | ProposedB_LinearStepB | 5.660 ± 2.871 | 4.609 ± 2.827 | 0.682 ± 0.195 |
| 100 | 100 | ProposedB_SourceDR | 5.500 ± 2.935 | 4.358 ± 2.761 | 0.645 ± 0.183 |
| 100 | 100 | ProxyOnly | 4.706 ± 2.122 | 3.829 ± 2.759 | 0.530 ± 0.270 |
| 100 | 100 | TargetOnlyDR | 5.157 ± 1.996 | 3.959 ± 2.491 | 0.568 ± 0.220 |
| 100 | 500 | AnchorOnly | 4.859 ± 0.193 | 3.645 ± 0.162 | 0.730 ± 0.014 |
| 100 | 500 | AnchorPlugin | 5.194 ± 0.776 | 4.134 ± 0.542 | 0.820 ± 0.058 |
| 100 | 500 | DRLearner_PooledNoSite | 5.831 ± 0.815 | 4.509 ± 0.728 | 0.884 ± 0.118 |
| 100 | 500 | DRLearner_PooledWithSite | 5.723 ± 0.911 | 4.505 ± 0.731 | 0.882 ± 0.122 |
| 100 | 500 | EntropyBalancing | 5.629 ± 1.040 | 4.386 ± 0.875 | 0.874 ± 0.128 |
| 100 | 500 | IPWTransport | 5.695 ± 0.936 | 4.432 ± 0.797 | 0.881 ± 0.122 |
| 100 | 500 | OutcomeModelTransport | 5.737 ± 0.910 | 4.486 ± 0.753 | 0.880 ± 0.125 |
| 100 | 500 | ProposedA | 4.832 ± 0.191 | 3.592 ± 0.009 | 0.710 ± 0.029 |
| 100 | 500 | ProposedA_Direct | 4.968 ± 0.057 | 3.660 ± 0.082 | 0.747 ± 0.016 |
| 100 | 500 | ProposedA_Direct_NoCrossfit | 4.951 ± 0.080 | 3.632 ± 0.058 | 0.727 ± 0.036 |
| 100 | 500 | ProposedA_FullyDirect | 3.183 ± 0.270 | 2.663 ± 0.189 | 0.554 ± 0.034 |
| 100 | 500 | ProposedA_FullyJoint | 3.845 ± 0.273 | 3.176 ± 0.043 | 0.631 ± 0.057 |
| 100 | 500 | ProposedA_JointProxy | 4.966 ± 0.006 | 3.694 ± 0.009 | 0.726 ± 0.033 |
| 100 | 500 | ProposedA_NoCrossfit | 5.090 ± 0.074 | 3.623 ± 0.079 | 0.715 ± 0.040 |
| 100 | 500 | ProposedA_Together | 4.131 ± 0.471 | 3.114 ± 0.036 | 0.620 ± 0.035 |
| 100 | 500 | ProposedA_Together_Direct | 3.183 ± 0.270 | 2.663 ± 0.189 | 0.554 ± 0.034 |
| 100 | 500 | ProposedA_Together_Direct_NoCrossfit | 3.085 ± 0.044 | 2.548 ± 0.247 | 0.540 ± 0.003 |
| 100 | 500 | ProposedA_Together_NoCrossfit | 3.928 ± 0.404 | 3.136 ± 0.079 | 0.600 ± 0.038 |
| 100 | 500 | ProposedB_LinearStepB | 4.901 ± 0.032 | 3.499 ± 0.050 | 0.697 ± 0.041 |
| 100 | 500 | ProposedB_SourceDR | 3.869 ± 0.847 | 3.171 ± 0.762 | 0.604 ± 0.164 |
| 100 | 500 | ProxyOnly | 2.098 ± 0.230 | 1.423 ± 0.202 | 0.302 ± 0.096 |
| 100 | 500 | TargetOnlyDR | 4.398 ± 0.185 | 3.405 ± 0.049 | 0.670 ± 0.035 |
| 100 | 1000 | AnchorOnly | 6.254 ± 0.481 | 4.826 ± 0.456 | 0.672 ± 0.085 |
| 100 | 1000 | AnchorPlugin | 7.243 ± 1.118 | 5.930 ± 0.912 | 0.814 ± 0.133 |
| 100 | 1000 | DRLearner_PooledNoSite | 8.162 ± 0.908 | 6.576 ± 0.684 | 0.916 ± 0.092 |
| 100 | 1000 | DRLearner_PooledWithSite | 8.117 ± 1.018 | 6.572 ± 0.679 | 0.913 ± 0.096 |
| 100 | 1000 | EntropyBalancing | 8.093 ± 1.008 | 6.525 ± 0.754 | 0.912 ± 0.096 |
| 100 | 1000 | IPWTransport | 8.039 ± 1.099 | 6.505 ± 0.779 | 0.910 ± 0.100 |
| 100 | 1000 | OutcomeModelTransport | 8.022 ± 1.153 | 6.483 ± 0.806 | 0.905 ± 0.104 |
| 100 | 1000 | ProposedA | 6.385 ± 0.641 | 4.852 ± 0.690 | 0.676 ± 0.121 |
| 100 | 1000 | ProposedA_Direct | 6.435 ± 0.168 | 5.240 ± 0.142 | 0.741 ± 0.024 |
| 100 | 1000 | ProposedA_Direct_NoCrossfit | 6.570 ± 0.400 | 5.326 ± 0.289 | 0.766 ± 0.034 |
| 100 | 1000 | ProposedA_FullyDirect | 3.666 ± 0.593 | 3.694 ± 0.669 | 0.557 ± 0.032 |
| 100 | 1000 | ProposedA_FullyJoint | 3.669 ± 1.151 | 3.682 ± 0.920 | 0.520 ± 0.064 |
| 100 | 1000 | ProposedA_JointProxy | 6.127 ± 0.111 | 5.070 ± 0.203 | 0.702 ± 0.051 |
| 100 | 1000 | ProposedA_NoCrossfit | 6.497 ± 0.550 | 4.980 ± 0.515 | 0.706 ± 0.076 |
| 100 | 1000 | ProposedA_Together | 4.181 ± 1.710 | 3.887 ± 0.471 | 0.562 ± 0.011 |
| 100 | 1000 | ProposedA_Together_Direct | 3.666 ± 0.593 | 3.694 ± 0.669 | 0.557 ± 0.032 |
| 100 | 1000 | ProposedA_Together_Direct_NoCrossfit | 3.835 ± 1.090 | 3.647 ± 0.830 | 0.540 ± 0.055 |
| 100 | 1000 | ProposedA_Together_NoCrossfit | 4.436 ± 1.109 | 4.097 ± 0.154 | 0.571 ± 0.037 |
| 100 | 1000 | ProposedB_LinearStepB | 6.455 ± 0.510 | 4.834 ± 0.681 | 0.694 ± 0.117 |
| 100 | 1000 | ProposedB_SourceDR | 5.204 ± 1.125 | 4.311 ± 1.026 | 0.608 ± 0.140 |
| 100 | 1000 | ProxyOnly | 3.651 ± 1.552 | 3.528 ± 0.767 | 0.494 ± 0.101 |
| 100 | 1000 | TargetOnlyDR | 4.228 ± 0.213 | 3.943 ± 0.051 | 0.520 ± 0.044 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 6.749 ± 0.805 | 5.618 ± 0.732 | 0.769 ± 0.130 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 6.675 ± 1.542 | 5.424 ± 1.181 | 0.751 ± 0.190 |
| 500 | 0 | IPWTransport | 6.681 ± 1.533 | 5.440 ± 1.159 | 0.754 ± 0.188 |
| 500 | 0 | OutcomeModelTransport | 6.737 ± 1.446 | 5.462 ± 1.174 | 0.756 ± 0.180 |
| 500 | 0 | ProposedA | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 500 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 4.790 ± 2.978 | 4.011 ± 1.835 | 0.528 ± 0.271 |
| 500 | 0 | ProxyOnly | 5.805 ± 0.739 | 4.829 ± 0.949 | 0.673 ± 0.142 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 4.286 ± 0.166 | 3.271 ± 0.004 | 0.509 ± 0.159 |
| 500 | 100 | AnchorPlugin | 5.518 ± 0.033 | 4.090 ± 0.314 | 0.725 ± 0.048 |
| 500 | 100 | DRLearner_PooledNoSite | 6.475 ± 0.891 | 4.873 ± 0.577 | 0.870 ± 0.022 |
| 500 | 100 | DRLearner_PooledWithSite | 6.518 ± 0.952 | 4.884 ± 0.557 | 0.875 ± 0.019 |
| 500 | 100 | EntropyBalancing | 6.190 ± 0.673 | 4.683 ± 0.456 | 0.841 ± 0.048 |
| 500 | 100 | IPWTransport | 6.310 ± 0.841 | 4.730 ± 0.480 | 0.841 ± 0.043 |
| 500 | 100 | OutcomeModelTransport | 6.459 ± 0.913 | 4.847 ± 0.564 | 0.863 ± 0.019 |
| 500 | 100 | ProposedA | 5.245 ± 1.029 | 3.887 ± 0.796 | 0.671 ± 0.026 |
| 500 | 100 | ProposedA_Direct | 5.623 ± 0.928 | 4.115 ± 0.847 | 0.675 ± 0.027 |
| 500 | 100 | ProposedA_Direct_NoCrossfit | 5.736 ± 1.089 | 4.120 ± 0.754 | 0.683 ± 0.005 |
| 500 | 100 | ProposedA_FullyDirect | 1.714 ± 0.383 | 1.906 ± 0.670 | 0.377 ± 0.031 |
| 500 | 100 | ProposedA_FullyJoint | 1.981 ± 0.660 | 2.293 ± 0.857 | 0.426 ± 0.000 |
| 500 | 100 | ProposedA_JointProxy | 5.429 ± 1.002 | 3.971 ± 0.699 | 0.687 ± 0.035 |
| 500 | 100 | ProposedA_NoCrossfit | 5.454 ± 1.145 | 4.056 ± 0.671 | 0.680 ± 0.000 |
| 500 | 100 | ProposedA_Together | 3.461 ± 0.062 | 2.964 ± 0.295 | 0.481 ± 0.049 |
| 500 | 100 | ProposedA_Together_Direct | 1.714 ± 0.383 | 1.906 ± 0.670 | 0.377 ± 0.031 |
| 500 | 100 | ProposedA_Together_Direct_NoCrossfit | 1.740 ± 0.395 | 1.883 ± 0.615 | 0.391 ± 0.061 |
| 500 | 100 | ProposedA_Together_NoCrossfit | 3.383 ± 0.443 | 2.949 ± 0.544 | 0.485 ± 0.008 |
| 500 | 100 | ProposedB_LinearStepB | 5.410 ± 1.164 | 3.985 ± 0.570 | 0.687 ± 0.017 |
| 500 | 100 | ProposedB_SourceDR | 3.899 ± 0.102 | 2.918 ± 0.601 | 0.503 ± 0.030 |
| 500 | 100 | ProxyOnly | 3.858 ± 0.146 | 3.304 ± 0.442 | 0.546 ± 0.032 |
| 500 | 100 | TargetOnlyDR | 2.658 ± 1.160 | 2.483 ± 0.743 | 0.432 ± 0.044 |
| 500 | 500 | AnchorOnly | 7.256 ± 1.945 | 5.637 ± 1.601 | 0.799 ± 0.014 |
| 500 | 500 | AnchorPlugin | 7.342 ± 2.249 | 5.781 ± 1.865 | 0.835 ± 0.022 |
| 500 | 500 | DRLearner_PooledNoSite | 7.687 ± 2.024 | 6.111 ± 1.853 | 0.896 ± 0.027 |
| 500 | 500 | DRLearner_PooledWithSite | 7.692 ± 1.988 | 6.133 ± 1.833 | 0.899 ± 0.024 |
| 500 | 500 | EntropyBalancing | 7.432 ± 2.149 | 5.937 ± 1.814 | 0.884 ± 0.033 |
| 500 | 500 | IPWTransport | 7.439 ± 2.111 | 5.956 ± 1.834 | 0.884 ± 0.032 |
| 500 | 500 | OutcomeModelTransport | 7.570 ± 2.015 | 6.032 ± 1.791 | 0.888 ± 0.029 |
| 500 | 500 | ProposedA | 7.114 ± 1.764 | 5.642 ± 1.575 | 0.803 ± 0.018 |
| 500 | 500 | ProposedA_Direct | 7.113 ± 1.907 | 5.573 ± 1.632 | 0.792 ± 0.016 |
| 500 | 500 | ProposedA_Direct_NoCrossfit | 7.091 ± 1.847 | 5.562 ± 1.558 | 0.797 ± 0.015 |
| 500 | 500 | ProposedA_FullyDirect | 7.143 ± 1.704 | 5.658 ± 1.585 | 0.811 ± 0.015 |
| 500 | 500 | ProposedA_FullyJoint | 6.979 ± 1.704 | 5.498 ± 1.505 | 0.804 ± 0.008 |
| 500 | 500 | ProposedA_JointProxy | 7.210 ± 1.792 | 5.596 ± 1.637 | 0.803 ± 0.012 |
| 500 | 500 | ProposedA_NoCrossfit | 7.036 ± 1.743 | 5.627 ± 1.640 | 0.797 ± 0.017 |
| 500 | 500 | ProposedA_Together | 7.039 ± 1.724 | 5.629 ± 1.408 | 0.798 ± 0.023 |
| 500 | 500 | ProposedA_Together_Direct | 7.143 ± 1.704 | 5.658 ± 1.585 | 0.811 ± 0.015 |
| 500 | 500 | ProposedA_Together_Direct_NoCrossfit | 7.075 ± 1.671 | 5.621 ± 1.597 | 0.809 ± 0.020 |
| 500 | 500 | ProposedA_Together_NoCrossfit | 7.046 ± 1.684 | 5.591 ± 1.441 | 0.795 ± 0.009 |
| 500 | 500 | ProposedB_LinearStepB | 6.889 ± 1.664 | 5.436 ± 1.464 | 0.787 ± 0.016 |
| 500 | 500 | ProposedB_SourceDR | 5.793 ± 1.553 | 4.608 ± 1.138 | 0.648 ± 0.042 |
| 500 | 500 | ProxyOnly | 5.546 ± 2.844 | 4.298 ± 2.061 | 0.591 ± 0.164 |
| 500 | 500 | TargetOnlyDR | 7.054 ± 1.537 | 5.314 ± 1.196 | 0.791 ± 0.017 |
| 500 | 1000 | AnchorOnly | 6.409 ± 0.144 | 5.621 ± 0.246 | 0.756 ± 0.056 |
| 500 | 1000 | AnchorPlugin | 7.541 ± 0.194 | 6.215 ± 0.019 | 0.834 ± 0.009 |
| 500 | 1000 | DRLearner_PooledNoSite | 8.175 ± 0.313 | 6.620 ± 0.365 | 0.881 ± 0.029 |
| 500 | 1000 | DRLearner_PooledWithSite | 8.173 ± 0.316 | 6.577 ± 0.307 | 0.878 ± 0.028 |
| 500 | 1000 | EntropyBalancing | 7.758 ± 0.480 | 6.530 ± 0.269 | 0.857 ± 0.031 |
| 500 | 1000 | IPWTransport | 7.740 ± 0.527 | 6.535 ± 0.323 | 0.857 ± 0.030 |
| 500 | 1000 | OutcomeModelTransport | 7.809 ± 0.648 | 6.457 ± 0.282 | 0.860 ± 0.029 |
| 500 | 1000 | ProposedA | 6.406 ± 0.199 | 5.604 ± 0.204 | 0.746 ± 0.072 |
| 500 | 1000 | ProposedA_Direct | 6.505 ± 0.240 | 5.609 ± 0.280 | 0.766 ± 0.065 |
| 500 | 1000 | ProposedA_Direct_NoCrossfit | 6.442 ± 0.172 | 5.575 ± 0.358 | 0.757 ± 0.073 |
| 500 | 1000 | ProposedA_FullyDirect | 6.814 ± 0.272 | 5.478 ± 0.182 | 0.745 ± 0.060 |
| 500 | 1000 | ProposedA_FullyJoint | 6.755 ± 0.061 | 5.529 ± 0.289 | 0.741 ± 0.052 |
| 500 | 1000 | ProposedA_JointProxy | 6.349 ± 0.079 | 5.475 ± 0.385 | 0.744 ± 0.084 |
| 500 | 1000 | ProposedA_NoCrossfit | 6.345 ± 0.154 | 5.559 ± 0.200 | 0.759 ± 0.076 |
| 500 | 1000 | ProposedA_Together | 6.747 ± 0.013 | 5.492 ± 0.087 | 0.761 ± 0.044 |
| 500 | 1000 | ProposedA_Together_Direct | 6.814 ± 0.272 | 5.478 ± 0.182 | 0.745 ± 0.060 |
| 500 | 1000 | ProposedA_Together_Direct_NoCrossfit | 6.882 ± 0.110 | 5.469 ± 0.168 | 0.755 ± 0.050 |
| 500 | 1000 | ProposedA_Together_NoCrossfit | 6.784 ± 0.062 | 5.546 ± 0.134 | 0.747 ± 0.063 |
| 500 | 1000 | ProposedB_LinearStepB | 6.348 ± 0.063 | 5.513 ± 0.178 | 0.759 ± 0.075 |
| 500 | 1000 | ProposedB_SourceDR | 5.601 ± 0.895 | 4.687 ± 0.765 | 0.616 ± 0.142 |
| 500 | 1000 | ProxyOnly | 5.062 ± 0.853 | 4.540 ± 0.273 | 0.616 ± 0.014 |
| 500 | 1000 | TargetOnlyDR | 6.245 ± 0.174 | 5.645 ± 0.180 | 0.784 ± 0.060 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 7.363 ± 0.262 | 6.113 ± 0.382 | 0.911 ± 0.032 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 7.602 ± 0.348 | 6.283 ± 0.748 | 0.945 ± 0.003 |
| 1000 | 0 | IPWTransport | 7.602 ± 0.348 | 6.287 ± 0.712 | 0.944 ± 0.005 |
| 1000 | 0 | OutcomeModelTransport | 7.696 ± 0.480 | 6.270 ± 0.770 | 0.946 ± 0.001 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Direct_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_Direct_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together_NoCrossfit | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 5.056 ± 0.479 | 4.307 ± 0.772 | 0.667 ± 0.096 |
| 1000 | 0 | ProxyOnly | 4.824 ± 1.527 | 4.212 ± 1.017 | 0.628 ± 0.110 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 5.618 ± 0.243 | 4.931 ± 0.100 | 0.730 ± 0.036 |
| 1000 | 100 | AnchorPlugin | 7.957 ± 1.157 | 6.503 ± 0.907 | 0.898 ± 0.039 |
| 1000 | 100 | DRLearner_PooledNoSite | 8.679 ± 1.072 | 7.060 ± 0.726 | 0.967 ± 0.037 |
| 1000 | 100 | DRLearner_PooledWithSite | 8.713 ± 1.046 | 7.063 ± 0.731 | 0.972 ± 0.031 |
| 1000 | 100 | EntropyBalancing | 8.572 ± 1.245 | 6.879 ± 0.934 | 0.955 ± 0.053 |
| 1000 | 100 | IPWTransport | 8.571 ± 1.248 | 6.879 ± 0.934 | 0.956 ± 0.053 |
| 1000 | 100 | OutcomeModelTransport | 8.677 ± 1.073 | 7.044 ± 0.734 | 0.965 ± 0.040 |
| 1000 | 100 | ProposedA | 7.095 ± 0.554 | 5.812 ± 0.640 | 0.794 ± 0.035 |
| 1000 | 100 | ProposedA_Direct | 7.241 ± 0.496 | 5.858 ± 0.660 | 0.792 ± 0.029 |
| 1000 | 100 | ProposedA_Direct_NoCrossfit | 7.430 ± 0.594 | 5.900 ± 0.565 | 0.791 ± 0.022 |
| 1000 | 100 | ProposedA_FullyDirect | 4.839 ± 0.187 | 4.412 ± 0.541 | 0.628 ± 0.112 |
| 1000 | 100 | ProposedA_FullyJoint | 5.442 ± 0.266 | 4.661 ± 0.162 | 0.657 ± 0.101 |
| 1000 | 100 | ProposedA_JointProxy | 7.163 ± 0.587 | 5.773 ± 0.552 | 0.771 ± 0.015 |
| 1000 | 100 | ProposedA_NoCrossfit | 7.496 ± 0.638 | 5.900 ± 0.549 | 0.802 ± 0.012 |
| 1000 | 100 | ProposedA_Together | 5.768 ± 0.730 | 4.833 ± 0.557 | 0.709 ± 0.065 |
| 1000 | 100 | ProposedA_Together_Direct | 4.839 ± 0.187 | 4.412 ± 0.541 | 0.628 ± 0.112 |
| 1000 | 100 | ProposedA_Together_Direct_NoCrossfit | 4.809 ± 0.436 | 4.163 ± 0.604 | 0.637 ± 0.085 |
| 1000 | 100 | ProposedA_Together_NoCrossfit | 5.906 ± 0.684 | 4.915 ± 0.258 | 0.718 ± 0.079 |
| 1000 | 100 | ProposedB_LinearStepB | 6.539 ± 0.416 | 5.379 ± 0.417 | 0.769 ± 0.019 |
| 1000 | 100 | ProposedB_SourceDR | 6.598 ± 0.481 | 5.275 ± 0.775 | 0.725 ± 0.016 |
| 1000 | 100 | ProxyOnly | 6.858 ± 0.339 | 5.406 ± 0.200 | 0.748 ± 0.014 |
| 1000 | 100 | TargetOnlyDR | 5.335 ± 1.138 | 5.037 ± 0.561 | 0.710 ± 0.018 |
| 1000 | 500 | AnchorOnly | 6.447 ± 0.733 | 5.160 ± 1.185 | 0.768 ± 0.048 |
| 1000 | 500 | AnchorPlugin | 6.805 ± 1.001 | 5.455 ± 1.186 | 0.814 ± 0.083 |
| 1000 | 500 | DRLearner_PooledNoSite | 7.951 ± 0.755 | 6.415 ± 1.011 | 0.953 ± 0.022 |
| 1000 | 500 | DRLearner_PooledWithSite | 7.964 ± 0.736 | 6.432 ± 1.032 | 0.955 ± 0.020 |
| 1000 | 500 | EntropyBalancing | 7.903 ± 0.751 | 6.337 ± 1.046 | 0.943 ± 0.031 |
| 1000 | 500 | IPWTransport | 7.894 ± 0.739 | 6.342 ± 1.056 | 0.945 ± 0.029 |
| 1000 | 500 | OutcomeModelTransport | 7.929 ± 0.749 | 6.373 ± 1.038 | 0.949 ± 0.021 |
| 1000 | 500 | ProposedA | 6.327 ± 0.984 | 5.256 ± 1.119 | 0.750 ± 0.090 |
| 1000 | 500 | ProposedA_Direct | 6.471 ± 0.768 | 5.331 ± 0.952 | 0.764 ± 0.079 |
| 1000 | 500 | ProposedA_Direct_NoCrossfit | 6.521 ± 0.688 | 5.296 ± 1.030 | 0.765 ± 0.077 |
| 1000 | 500 | ProposedA_FullyDirect | 6.533 ± 0.409 | 5.249 ± 0.954 | 0.761 ± 0.032 |
| 1000 | 500 | ProposedA_FullyJoint | 6.648 ± 0.833 | 5.232 ± 0.873 | 0.759 ± 0.060 |
| 1000 | 500 | ProposedA_JointProxy | 6.642 ± 0.798 | 5.298 ± 1.105 | 0.757 ± 0.079 |
| 1000 | 500 | ProposedA_NoCrossfit | 6.360 ± 0.975 | 5.275 ± 1.046 | 0.744 ± 0.091 |
| 1000 | 500 | ProposedA_Together | 6.650 ± 0.703 | 5.197 ± 0.871 | 0.761 ± 0.039 |
| 1000 | 500 | ProposedA_Together_Direct | 6.533 ± 0.409 | 5.249 ± 0.954 | 0.761 ± 0.032 |
| 1000 | 500 | ProposedA_Together_Direct_NoCrossfit | 6.609 ± 0.604 | 5.260 ± 0.931 | 0.766 ± 0.037 |
| 1000 | 500 | ProposedA_Together_NoCrossfit | 6.683 ± 0.753 | 5.199 ± 0.966 | 0.773 ± 0.055 |
| 1000 | 500 | ProposedB_LinearStepB | 6.607 ± 0.943 | 5.324 ± 1.142 | 0.759 ± 0.095 |
| 1000 | 500 | ProposedB_SourceDR | 5.786 ± 1.267 | 4.562 ± 1.251 | 0.672 ± 0.142 |
| 1000 | 500 | ProxyOnly | 5.521 ± 1.417 | 4.331 ± 1.454 | 0.597 ± 0.175 |
| 1000 | 500 | TargetOnlyDR | 6.590 ± 0.622 | 5.239 ± 0.840 | 0.790 ± 0.023 |
| 1000 | 1000 | AnchorOnly | 5.339 ± 0.727 | 3.858 ± 0.642 | 0.704 ± 0.027 |
| 1000 | 1000 | AnchorPlugin | 4.838 ± 0.820 | 3.709 ± 0.750 | 0.671 ± 0.084 |
| 1000 | 1000 | DRLearner_PooledNoSite | 5.019 ± 0.898 | 3.847 ± 0.862 | 0.738 ± 0.070 |
| 1000 | 1000 | DRLearner_PooledWithSite | 5.020 ± 0.884 | 3.854 ± 0.872 | 0.740 ± 0.071 |
| 1000 | 1000 | EntropyBalancing | 4.606 ± 0.813 | 3.579 ± 0.868 | 0.675 ± 0.082 |
| 1000 | 1000 | IPWTransport | 4.601 ± 0.971 | 3.587 ± 0.878 | 0.677 ± 0.082 |
| 1000 | 1000 | OutcomeModelTransport | 4.659 ± 0.788 | 3.585 ± 0.789 | 0.686 ± 0.079 |
| 1000 | 1000 | ProposedA | 5.100 ± 0.650 | 3.898 ± 0.728 | 0.720 ± 0.032 |
| 1000 | 1000 | ProposedA_Direct | 5.142 ± 0.595 | 3.860 ± 0.727 | 0.700 ± 0.029 |
| 1000 | 1000 | ProposedA_Direct_NoCrossfit | 5.103 ± 0.628 | 3.907 ± 0.738 | 0.691 ± 0.050 |
| 1000 | 1000 | ProposedA_FullyDirect | 5.117 ± 0.519 | 3.946 ± 0.705 | 0.715 ± 0.028 |
| 1000 | 1000 | ProposedA_FullyJoint | 5.290 ± 0.724 | 3.807 ± 0.656 | 0.708 ± 0.030 |
| 1000 | 1000 | ProposedA_JointProxy | 5.231 ± 0.616 | 3.876 ± 0.634 | 0.717 ± 0.029 |
| 1000 | 1000 | ProposedA_NoCrossfit | 5.132 ± 0.591 | 3.854 ± 0.756 | 0.715 ± 0.035 |
| 1000 | 1000 | ProposedA_Together | 5.246 ± 0.586 | 3.958 ± 0.732 | 0.724 ± 0.024 |
| 1000 | 1000 | ProposedA_Together_Direct | 5.117 ± 0.519 | 3.946 ± 0.705 | 0.715 ± 0.028 |
| 1000 | 1000 | ProposedA_Together_Direct_NoCrossfit | 5.213 ± 0.668 | 3.935 ± 0.660 | 0.708 ± 0.020 |
| 1000 | 1000 | ProposedA_Together_NoCrossfit | 5.118 ± 0.622 | 3.828 ± 0.801 | 0.712 ± 0.028 |
| 1000 | 1000 | ProposedB_LinearStepB | 5.126 ± 0.367 | 3.919 ± 0.632 | 0.726 ± 0.046 |
| 1000 | 1000 | ProposedB_SourceDR | 3.040 ± 0.793 | 2.325 ± 0.691 | 0.410 ± 0.087 |
| 1000 | 1000 | ProxyOnly | 3.341 ± 1.308 | 2.540 ± 1.310 | 0.433 ± 0.141 |
| 1000 | 1000 | TargetOnlyDR | 5.324 ± 0.671 | 3.866 ± 0.803 | 0.714 ± 0.024 |

---

## 7. Plots

### PEHE vs Sweep Parameter (↓ lower is better)

![PEHE](gold_fair_sweep_pehe.png)

### ATE Error vs Sweep Parameter (↓ lower is better)

![ATE Error](gold_fair_sweep_ate.png)

### Spearman Correlation vs Sweep Parameter (↑ higher is better)

![Correlation](gold_fair_sweep_corr.png)

---

## 8. Key Findings

1. **Best overall PEHE:** DRLearner_PooledWithSite achieves lowest average PEHE (1.094)
2. **Proposed vs ProxyOnly:** Proposed reduces PEHE by 20.7% on average
3. **EntropyBalancing:** PEHE degrades as m0 increases
4. **IPWTransport:** PEHE degrades as m0 increases
5. **OutcomeModelTransport:** PEHE degrades as m0 increases
6. **Best ranking:** DRLearner_PooledWithSite achieves highest Spearman correlation (0.962)

---

## Appendix: Configuration

```python
sweep_param = 'm0'
sweep_values = [100, 500, 1000]
base_scenario = {'n_proxy_total': 20000, 'C_sources': 10, 'nontransfer_scale': 0.1, 'use_fair_dgp': True, 'overlap_lambda': 0.25, 'intercept_drift_scale': 0.5}
```

