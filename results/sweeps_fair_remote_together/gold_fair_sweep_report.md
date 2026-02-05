# Fair OptionB evaluation: m₀ × m₁ grid with controlled DGP

**Benchmark ID:** `gold_fair_sweep`

**Generated:** 2026-02-05 04:49

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
| **ProposedA** | ✓ | ✓ | Proposed (Option A): separate proxy μ₀,μ₁ + separate correction δ₀,δ₁ |
| **ProposedA_Together** | ✗ | ✗ | Proposed (Option A): separate proxy + joint correction δ(X,A) |
| **ProposedA_JointProxy** | ✗ | ✗ | Proposed (Option A): joint proxy μ(X,A) + separate correction |
| **ProposedA_FullyJoint** | ✗ | ✗ | Proposed (Option A): joint proxy + joint correction (fully pooled) |
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
- **Monte Carlo replicates:** 20 per scenario
- **Methods evaluated:** 15
- **Total runs:** 3600

---

## 6. Results

### Best Methods (averaged across sweep)

| Metric | Best Method | Value | Direction |
|--------|-------------|-------|----------|
| PEHE | **DRLearner_PooledNoSite** | 2.0220 | ↓ lower |
| ATE Error | **ProposedA_FullyJoint** | 0.1003 | ↓ lower |
| Spearman ρ | **ProxyOnly** | 0.3583 | ↑ higher |
| Kendall τ | **ProxyOnly** | 0.2462 | ↑ higher |
| Qini AUC | **ProxyOnly** | 0.3730 | ↑ higher |
| Top-10% Ratio | **ProxyOnly** | 0.3483 | ↑ higher |
| Top-20% Ratio | **ProxyOnly** | 0.3253 | ↑ higher |
| Calibration R² | **ProposedA_FullyJoint** | 0.0877 | ↑ higher |
| CATE ECE | **DRLearner_PooledNoSite** | 0.6293 | ↓ lower |
| Policy Value | **ProxyOnly** | 0.6995 | ↑ higher |
| Policy Regret | **DRLearner_PooledNoSite** | 0.2251 | ↓ lower |

### Core Metrics

| m0 | m1 | Method | PEHE (↓) | ATE Err (↓) | Spearman (↑) | Qini (↑) |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 2.756 ± 0.856 | 0.637 ± 0.404 | 0.775 ± 0.114 | 0.787 ± 0.112 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 2.207 ± 0.909 | 0.643 ± 0.556 | 0.861 ± 0.105 | 0.871 ± 0.100 |
| 100 | 0 | IPWTransport | 2.171 ± 0.914 | 0.642 ± 0.547 | 0.865 ± 0.105 | 0.875 ± 0.099 |
| 100 | 0 | OutcomeModelTransport | 2.160 ± 0.922 | 0.650 ± 0.552 | 0.867 ± 0.105 | 0.876 ± 0.099 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 3.608 ± 0.656 | 0.862 ± 0.634 | 0.617 ± 0.086 | 0.634 ± 0.084 |
| 100 | 0 | ProxyOnly | 3.865 ± 0.711 | 0.684 ± 0.546 | 0.517 ± 0.125 | 0.533 ± 0.125 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 3.456 ± 0.534 | 0.344 ± 0.268 | 0.701 ± 0.061 | 0.717 ± 0.059 |
| 100 | 100 | AnchorPlugin | 2.973 ± 0.771 | 0.671 ± 0.406 | 0.753 ± 0.124 | 0.767 ± 0.121 |
| 100 | 100 | DRLearner_PooledNoSite | 2.409 ± 1.014 | 0.723 ± 0.607 | 0.841 ± 0.131 | 0.851 ± 0.126 |
| 100 | 100 | DRLearner_PooledWithSite | 2.405 ± 1.011 | 0.722 ± 0.606 | 0.841 ± 0.131 | 0.852 ± 0.126 |
| 100 | 100 | EntropyBalancing | 2.479 ± 1.020 | 0.745 ± 0.641 | 0.832 ± 0.135 | 0.843 ± 0.129 |
| 100 | 100 | IPWTransport | 2.447 ± 1.028 | 0.742 ± 0.628 | 0.836 ± 0.135 | 0.846 ± 0.130 |
| 100 | 100 | OutcomeModelTransport | 2.440 ± 1.026 | 0.743 ± 0.631 | 0.837 ± 0.134 | 0.848 ± 0.129 |
| 100 | 100 | ProposedA | 3.376 ± 0.466 | 0.320 ± 0.205 | 0.721 ± 0.054 | 0.737 ± 0.053 |
| 100 | 100 | ProposedA_FullyJoint | 3.390 ± 0.477 | 0.341 ± 0.175 | 0.724 ± 0.049 | 0.740 ± 0.046 |
| 100 | 100 | ProposedA_JointProxy | 3.369 ± 0.486 | 0.300 ± 0.193 | 0.729 ± 0.057 | 0.744 ± 0.056 |
| 100 | 100 | ProposedA_Together | 3.379 ± 0.461 | 0.306 ± 0.194 | 0.728 ± 0.052 | 0.744 ± 0.050 |
| 100 | 100 | ProposedB_LinearStepB | 3.377 ± 0.453 | 0.290 ± 0.254 | 0.721 ± 0.056 | 0.737 ± 0.054 |
| 100 | 100 | ProposedB_SourceDR | 3.930 ± 0.640 | 1.173 ± 0.819 | 0.590 ± 0.087 | 0.609 ± 0.086 |
| 100 | 100 | ProxyOnly | 4.006 ± 0.598 | 0.657 ± 0.416 | 0.516 ± 0.118 | 0.533 ± 0.120 |
| 100 | 100 | TargetOnlyDR | 3.490 ± 0.461 | 0.438 ± 0.222 | 0.680 ± 0.071 | 0.697 ± 0.068 |
| 100 | 500 | AnchorOnly | 3.175 ± 0.624 | 0.154 ± 0.094 | 0.737 ± 0.048 | 0.753 ± 0.046 |
| 100 | 500 | AnchorPlugin | 2.864 ± 0.622 | 0.550 ± 0.399 | 0.751 ± 0.108 | 0.765 ± 0.104 |
| 100 | 500 | DRLearner_PooledNoSite | 2.168 ± 0.942 | 0.604 ± 0.488 | 0.856 ± 0.119 | 0.866 ± 0.113 |
| 100 | 500 | DRLearner_PooledWithSite | 2.195 ± 0.960 | 0.619 ± 0.481 | 0.852 ± 0.123 | 0.862 ± 0.117 |
| 100 | 500 | EntropyBalancing | 2.344 ± 0.975 | 0.683 ± 0.492 | 0.833 ± 0.130 | 0.843 ± 0.124 |
| 100 | 500 | IPWTransport | 2.291 ± 0.992 | 0.691 ± 0.488 | 0.840 ± 0.130 | 0.851 ± 0.124 |
| 100 | 500 | OutcomeModelTransport | 2.277 ± 0.994 | 0.675 ± 0.521 | 0.843 ± 0.130 | 0.853 ± 0.124 |
| 100 | 500 | ProposedA | 3.187 ± 0.632 | 0.132 ± 0.088 | 0.730 ± 0.047 | 0.746 ± 0.045 |
| 100 | 500 | ProposedA_FullyJoint | 4.090 ± 1.071 | 0.279 ± 0.226 | 0.561 ± 0.052 | 0.580 ± 0.052 |
| 100 | 500 | ProposedA_JointProxy | 3.190 ± 0.616 | 0.146 ± 0.101 | 0.731 ± 0.044 | 0.747 ± 0.041 |
| 100 | 500 | ProposedA_Together | 3.807 ± 0.925 | 0.222 ± 0.181 | 0.606 ± 0.054 | 0.624 ± 0.054 |
| 100 | 500 | ProposedB_LinearStepB | 3.196 ± 0.625 | 0.141 ± 0.096 | 0.732 ± 0.049 | 0.748 ± 0.046 |
| 100 | 500 | ProposedB_SourceDR | 3.737 ± 0.772 | 0.807 ± 0.620 | 0.560 ± 0.132 | 0.577 ± 0.131 |
| 100 | 500 | ProxyOnly | 5.859 ± 1.383 | 2.577 ± 1.877 | 0.381 ± 0.102 | 0.397 ± 0.104 |
| 100 | 500 | TargetOnlyDR | 3.546 ± 0.677 | 0.245 ± 0.192 | 0.645 ± 0.063 | 0.662 ± 0.063 |
| 100 | 1000 | AnchorOnly | 3.177 ± 0.517 | 0.113 ± 0.073 | 0.709 ± 0.043 | 0.725 ± 0.043 |
| 100 | 1000 | AnchorPlugin | 2.726 ± 0.768 | 0.546 ± 0.637 | 0.772 ± 0.119 | 0.785 ± 0.117 |
| 100 | 1000 | DRLearner_PooledNoSite | 2.022 ± 0.906 | 0.574 ± 0.462 | 0.876 ± 0.117 | 0.884 ± 0.112 |
| 100 | 1000 | DRLearner_PooledWithSite | 2.064 ± 0.950 | 0.586 ± 0.470 | 0.869 ± 0.125 | 0.878 ± 0.121 |
| 100 | 1000 | EntropyBalancing | 2.201 ± 0.974 | 0.675 ± 0.526 | 0.855 ± 0.138 | 0.865 ± 0.134 |
| 100 | 1000 | IPWTransport | 2.198 ± 0.994 | 0.680 ± 0.533 | 0.855 ± 0.138 | 0.865 ± 0.134 |
| 100 | 1000 | OutcomeModelTransport | 2.200 ± 1.000 | 0.677 ± 0.530 | 0.855 ± 0.138 | 0.864 ± 0.134 |
| 100 | 1000 | ProposedA | 3.194 ± 0.509 | 0.123 ± 0.072 | 0.704 ± 0.043 | 0.721 ± 0.043 |
| 100 | 1000 | ProposedA_FullyJoint | 4.771 ± 0.755 | 0.377 ± 0.350 | 0.496 ± 0.069 | 0.512 ± 0.070 |
| 100 | 1000 | ProposedA_JointProxy | 3.174 ± 0.507 | 0.130 ± 0.093 | 0.710 ± 0.039 | 0.726 ± 0.039 |
| 100 | 1000 | ProposedA_Together | 4.300 ± 0.690 | 0.323 ± 0.258 | 0.535 ± 0.059 | 0.552 ± 0.061 |
| 100 | 1000 | ProposedB_LinearStepB | 3.190 ± 0.508 | 0.118 ± 0.073 | 0.705 ± 0.041 | 0.721 ± 0.041 |
| 100 | 1000 | ProposedB_SourceDR | 3.603 ± 0.752 | 0.760 ± 0.779 | 0.599 ± 0.102 | 0.616 ± 0.102 |
| 100 | 1000 | ProxyOnly | 10.485 ± 3.093 | 5.624 ± 4.031 | 0.358 ± 0.145 | 0.373 ± 0.148 |
| 100 | 1000 | TargetOnlyDR | 4.018 ± 0.666 | 0.259 ± 0.215 | 0.557 ± 0.078 | 0.574 ± 0.078 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 2.924 ± 0.852 | 0.758 ± 0.610 | 0.768 ± 0.107 | 0.781 ± 0.104 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 2.578 ± 1.252 | 0.829 ± 0.620 | 0.822 ± 0.180 | 0.832 ± 0.177 |
| 500 | 0 | IPWTransport | 2.577 ± 1.250 | 0.836 ± 0.617 | 0.823 ± 0.179 | 0.833 ± 0.176 |
| 500 | 0 | OutcomeModelTransport | 2.548 ± 1.268 | 0.818 ± 0.631 | 0.826 ± 0.177 | 0.836 ± 0.173 |
| 500 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 3.788 ± 0.916 | 0.940 ± 0.580 | 0.560 ± 0.171 | 0.576 ± 0.172 |
| 500 | 0 | ProxyOnly | 3.868 ± 0.847 | 1.154 ± 0.759 | 0.574 ± 0.130 | 0.591 ± 0.130 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 4.027 ± 1.093 | 0.321 ± 0.219 | 0.623 ± 0.073 | 0.640 ± 0.072 |
| 500 | 100 | AnchorPlugin | 3.110 ± 1.041 | 0.644 ± 0.527 | 0.760 ± 0.109 | 0.774 ± 0.105 |
| 500 | 100 | DRLearner_PooledNoSite | 2.595 ± 1.200 | 0.656 ± 0.535 | 0.839 ± 0.117 | 0.850 ± 0.111 |
| 500 | 100 | DRLearner_PooledWithSite | 2.556 ± 1.176 | 0.651 ± 0.516 | 0.844 ± 0.112 | 0.855 ± 0.107 |
| 500 | 100 | EntropyBalancing | 2.665 ± 1.201 | 0.707 ± 0.577 | 0.834 ± 0.120 | 0.845 ± 0.115 |
| 500 | 100 | IPWTransport | 2.662 ± 1.200 | 0.705 ± 0.577 | 0.834 ± 0.120 | 0.845 ± 0.115 |
| 500 | 100 | OutcomeModelTransport | 2.651 ± 1.211 | 0.712 ± 0.574 | 0.834 ± 0.120 | 0.845 ± 0.114 |
| 500 | 100 | ProposedA | 3.366 ± 0.705 | 0.198 ± 0.170 | 0.741 ± 0.032 | 0.756 ± 0.032 |
| 500 | 100 | ProposedA_FullyJoint | 4.338 ± 0.915 | 0.257 ± 0.219 | 0.582 ± 0.053 | 0.598 ± 0.052 |
| 500 | 100 | ProposedA_JointProxy | 3.368 ± 0.713 | 0.163 ± 0.186 | 0.742 ± 0.033 | 0.757 ± 0.032 |
| 500 | 100 | ProposedA_Together | 4.034 ± 0.953 | 0.256 ± 0.203 | 0.619 ± 0.052 | 0.635 ± 0.050 |
| 500 | 100 | ProposedB_LinearStepB | 3.401 ± 0.689 | 0.205 ± 0.182 | 0.731 ± 0.030 | 0.746 ± 0.029 |
| 500 | 100 | ProposedB_SourceDR | 4.016 ± 0.982 | 0.898 ± 0.653 | 0.583 ± 0.105 | 0.600 ± 0.106 |
| 500 | 100 | ProxyOnly | 3.991 ± 1.042 | 0.718 ± 0.576 | 0.596 ± 0.112 | 0.613 ± 0.111 |
| 500 | 100 | TargetOnlyDR | 4.044 ± 0.977 | 0.300 ± 0.229 | 0.625 ± 0.064 | 0.641 ± 0.064 |
| 500 | 500 | AnchorOnly | 2.912 ± 0.500 | 0.116 ± 0.092 | 0.752 ± 0.035 | 0.768 ± 0.031 |
| 500 | 500 | AnchorPlugin | 2.703 ± 0.728 | 0.693 ± 0.438 | 0.775 ± 0.111 | 0.788 ± 0.108 |
| 500 | 500 | DRLearner_PooledNoSite | 2.192 ± 0.744 | 0.757 ± 0.458 | 0.866 ± 0.080 | 0.876 ± 0.075 |
| 500 | 500 | DRLearner_PooledWithSite | 2.187 ± 0.745 | 0.752 ± 0.459 | 0.866 ± 0.080 | 0.877 ± 0.075 |
| 500 | 500 | EntropyBalancing | 2.350 ± 0.788 | 0.875 ± 0.523 | 0.849 ± 0.091 | 0.860 ± 0.087 |
| 500 | 500 | IPWTransport | 2.346 ± 0.786 | 0.877 ± 0.523 | 0.849 ± 0.091 | 0.860 ± 0.086 |
| 500 | 500 | OutcomeModelTransport | 2.341 ± 0.785 | 0.877 ± 0.526 | 0.851 ± 0.090 | 0.862 ± 0.086 |
| 500 | 500 | ProposedA | 2.916 ± 0.508 | 0.103 ± 0.080 | 0.751 ± 0.030 | 0.766 ± 0.027 |
| 500 | 500 | ProposedA_FullyJoint | 2.920 ± 0.505 | 0.100 ± 0.074 | 0.748 ± 0.028 | 0.764 ± 0.025 |
| 500 | 500 | ProposedA_JointProxy | 2.917 ± 0.506 | 0.100 ± 0.074 | 0.749 ± 0.030 | 0.765 ± 0.027 |
| 500 | 500 | ProposedA_Together | 2.919 ± 0.506 | 0.105 ± 0.082 | 0.749 ± 0.029 | 0.765 ± 0.026 |
| 500 | 500 | ProposedB_LinearStepB | 2.918 ± 0.512 | 0.105 ± 0.084 | 0.749 ± 0.033 | 0.765 ± 0.029 |
| 500 | 500 | ProposedB_SourceDR | 3.526 ± 0.634 | 0.854 ± 0.633 | 0.610 ± 0.090 | 0.625 ± 0.086 |
| 500 | 500 | ProxyOnly | 3.551 ± 0.772 | 0.894 ± 0.459 | 0.597 ± 0.141 | 0.612 ± 0.142 |
| 500 | 500 | TargetOnlyDR | 2.907 ± 0.492 | 0.115 ± 0.099 | 0.752 ± 0.032 | 0.767 ± 0.028 |
| 500 | 1000 | AnchorOnly | 3.200 ± 0.521 | 0.123 ± 0.089 | 0.730 ± 0.031 | 0.746 ± 0.030 |
| 500 | 1000 | AnchorPlugin | 2.877 ± 0.747 | 0.621 ± 0.541 | 0.767 ± 0.107 | 0.780 ± 0.106 |
| 500 | 1000 | DRLearner_PooledNoSite | 2.118 ± 0.912 | 0.566 ± 0.390 | 0.872 ± 0.103 | 0.880 ± 0.099 |
| 500 | 1000 | DRLearner_PooledWithSite | 2.144 ± 0.927 | 0.574 ± 0.400 | 0.868 ± 0.106 | 0.877 ± 0.103 |
| 500 | 1000 | EntropyBalancing | 2.397 ± 1.066 | 0.729 ± 0.542 | 0.838 ± 0.139 | 0.848 ± 0.136 |
| 500 | 1000 | IPWTransport | 2.392 ± 1.061 | 0.732 ± 0.548 | 0.839 ± 0.137 | 0.849 ± 0.134 |
| 500 | 1000 | OutcomeModelTransport | 2.337 ± 1.022 | 0.700 ± 0.506 | 0.846 ± 0.126 | 0.856 ± 0.123 |
| 500 | 1000 | ProposedA | 3.210 ± 0.536 | 0.112 ± 0.076 | 0.724 ± 0.029 | 0.740 ± 0.028 |
| 500 | 1000 | ProposedA_FullyJoint | 3.279 ± 0.549 | 0.145 ± 0.075 | 0.701 ± 0.032 | 0.719 ± 0.030 |
| 500 | 1000 | ProposedA_JointProxy | 3.211 ± 0.539 | 0.110 ± 0.078 | 0.722 ± 0.030 | 0.739 ± 0.029 |
| 500 | 1000 | ProposedA_Together | 3.249 ± 0.547 | 0.144 ± 0.071 | 0.710 ± 0.029 | 0.727 ± 0.028 |
| 500 | 1000 | ProposedB_LinearStepB | 3.205 ± 0.540 | 0.107 ± 0.072 | 0.726 ± 0.030 | 0.742 ± 0.029 |
| 500 | 1000 | ProposedB_SourceDR | 3.854 ± 0.715 | 0.911 ± 0.730 | 0.559 ± 0.105 | 0.577 ± 0.106 |
| 500 | 1000 | ProxyOnly | 3.989 ± 0.668 | 1.114 ± 0.802 | 0.531 ± 0.109 | 0.546 ± 0.111 |
| 500 | 1000 | TargetOnlyDR | 3.211 ± 0.507 | 0.134 ± 0.099 | 0.725 ± 0.026 | 0.742 ± 0.025 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 2.672 ± 0.590 | 0.683 ± 0.540 | 0.802 ± 0.071 | 0.814 ± 0.068 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 2.331 ± 0.732 | 0.904 ± 0.563 | 0.861 ± 0.085 | 0.870 ± 0.080 |
| 1000 | 0 | IPWTransport | 2.335 ± 0.736 | 0.904 ± 0.563 | 0.860 ± 0.085 | 0.870 ± 0.080 |
| 1000 | 0 | OutcomeModelTransport | 2.301 ± 0.730 | 0.894 ± 0.577 | 0.866 ± 0.081 | 0.875 ± 0.076 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 3.770 ± 0.547 | 1.104 ± 0.621 | 0.583 ± 0.070 | 0.598 ± 0.070 |
| 1000 | 0 | ProxyOnly | 3.699 ± 0.563 | 0.866 ± 0.717 | 0.608 ± 0.078 | 0.624 ± 0.077 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 4.663 ± 1.739 | 0.286 ± 0.364 | 0.561 ± 0.065 | 0.578 ± 0.066 |
| 1000 | 100 | AnchorPlugin | 3.110 ± 1.468 | 0.710 ± 0.452 | 0.764 ± 0.140 | 0.777 ± 0.137 |
| 1000 | 100 | DRLearner_PooledNoSite | 2.670 ± 1.764 | 0.671 ± 0.609 | 0.822 ± 0.179 | 0.833 ± 0.177 |
| 1000 | 100 | DRLearner_PooledWithSite | 2.595 ± 1.697 | 0.639 ± 0.582 | 0.833 ± 0.167 | 0.843 ± 0.164 |
| 1000 | 100 | EntropyBalancing | 2.809 ± 1.783 | 0.782 ± 0.690 | 0.808 ± 0.186 | 0.818 ± 0.184 |
| 1000 | 100 | IPWTransport | 2.817 ± 1.782 | 0.783 ± 0.692 | 0.807 ± 0.186 | 0.817 ± 0.184 |
| 1000 | 100 | OutcomeModelTransport | 2.764 ± 1.790 | 0.771 ± 0.683 | 0.814 ± 0.184 | 0.825 ± 0.182 |
| 1000 | 100 | ProposedA | 3.516 ± 1.010 | 0.158 ± 0.104 | 0.699 ± 0.043 | 0.715 ± 0.042 |
| 1000 | 100 | ProposedA_FullyJoint | 5.026 ± 1.697 | 0.416 ± 0.458 | 0.505 ± 0.060 | 0.522 ± 0.059 |
| 1000 | 100 | ProposedA_JointProxy | 3.529 ± 1.024 | 0.164 ± 0.137 | 0.694 ± 0.046 | 0.711 ± 0.044 |
| 1000 | 100 | ProposedA_Together | 4.742 ± 1.757 | 0.341 ± 0.376 | 0.539 ± 0.063 | 0.555 ± 0.064 |
| 1000 | 100 | ProposedB_LinearStepB | 3.668 ± 1.122 | 0.198 ± 0.085 | 0.666 ± 0.056 | 0.684 ± 0.055 |
| 1000 | 100 | ProposedB_SourceDR | 4.116 ± 1.489 | 1.034 ± 0.662 | 0.563 ± 0.134 | 0.579 ± 0.136 |
| 1000 | 100 | ProxyOnly | 3.996 ± 1.448 | 0.764 ± 0.462 | 0.605 ± 0.119 | 0.621 ± 0.119 |
| 1000 | 100 | TargetOnlyDR | 4.636 ± 1.576 | 0.330 ± 0.332 | 0.547 ± 0.056 | 0.564 ± 0.057 |
| 1000 | 500 | AnchorOnly | 3.455 ± 0.877 | 0.147 ± 0.153 | 0.733 ± 0.042 | 0.747 ± 0.041 |
| 1000 | 500 | AnchorPlugin | 3.325 ± 1.352 | 0.788 ± 0.528 | 0.736 ± 0.143 | 0.750 ± 0.141 |
| 1000 | 500 | DRLearner_PooledNoSite | 2.696 ± 1.585 | 0.763 ± 0.447 | 0.829 ± 0.172 | 0.839 ± 0.168 |
| 1000 | 500 | DRLearner_PooledWithSite | 2.644 ± 1.549 | 0.726 ± 0.422 | 0.835 ± 0.165 | 0.845 ± 0.161 |
| 1000 | 500 | EntropyBalancing | 2.906 ± 1.677 | 0.913 ± 0.538 | 0.805 ± 0.193 | 0.815 ± 0.189 |
| 1000 | 500 | IPWTransport | 2.906 ± 1.679 | 0.911 ± 0.537 | 0.805 ± 0.193 | 0.815 ± 0.190 |
| 1000 | 500 | OutcomeModelTransport | 2.894 ± 1.681 | 0.926 ± 0.547 | 0.807 ± 0.195 | 0.817 ± 0.191 |
| 1000 | 500 | ProposedA | 3.347 ± 0.793 | 0.113 ± 0.125 | 0.752 ± 0.023 | 0.765 ± 0.022 |
| 1000 | 500 | ProposedA_FullyJoint | 3.435 ± 0.819 | 0.123 ± 0.126 | 0.735 ± 0.038 | 0.749 ± 0.037 |
| 1000 | 500 | ProposedA_JointProxy | 3.353 ± 0.791 | 0.108 ± 0.120 | 0.750 ± 0.021 | 0.763 ± 0.020 |
| 1000 | 500 | ProposedA_Together | 3.402 ± 0.814 | 0.118 ± 0.137 | 0.740 ± 0.036 | 0.754 ± 0.035 |
| 1000 | 500 | ProposedB_LinearStepB | 3.352 ± 0.798 | 0.120 ± 0.123 | 0.752 ± 0.024 | 0.766 ± 0.023 |
| 1000 | 500 | ProposedB_SourceDR | 4.128 ± 1.182 | 0.941 ± 0.586 | 0.573 ± 0.160 | 0.587 ± 0.161 |
| 1000 | 500 | ProxyOnly | 4.116 ± 1.213 | 0.825 ± 0.644 | 0.570 ± 0.146 | 0.585 ± 0.146 |
| 1000 | 500 | TargetOnlyDR | 3.388 ± 0.819 | 0.153 ± 0.171 | 0.745 ± 0.038 | 0.759 ± 0.038 |
| 1000 | 1000 | AnchorOnly | 3.193 ± 0.764 | 0.145 ± 0.094 | 0.738 ± 0.026 | 0.753 ± 0.024 |
| 1000 | 1000 | AnchorPlugin | 2.989 ± 1.346 | 0.676 ± 0.448 | 0.755 ± 0.145 | 0.768 ± 0.145 |
| 1000 | 1000 | DRLearner_PooledNoSite | 2.290 ± 1.392 | 0.539 ± 0.423 | 0.858 ± 0.139 | 0.866 ± 0.137 |
| 1000 | 1000 | DRLearner_PooledWithSite | 2.290 ± 1.394 | 0.537 ± 0.424 | 0.858 ± 0.140 | 0.866 ± 0.138 |
| 1000 | 1000 | EntropyBalancing | 2.616 ± 1.587 | 0.721 ± 0.583 | 0.816 ± 0.182 | 0.825 ± 0.181 |
| 1000 | 1000 | IPWTransport | 2.619 ± 1.587 | 0.725 ± 0.583 | 0.816 ± 0.183 | 0.824 ± 0.181 |
| 1000 | 1000 | OutcomeModelTransport | 2.560 ± 1.551 | 0.705 ± 0.581 | 0.824 ± 0.175 | 0.833 ± 0.173 |
| 1000 | 1000 | ProposedA | 3.180 ± 0.736 | 0.118 ± 0.071 | 0.736 ± 0.030 | 0.751 ± 0.028 |
| 1000 | 1000 | ProposedA_FullyJoint | 3.177 ± 0.734 | 0.126 ± 0.076 | 0.737 ± 0.029 | 0.752 ± 0.028 |
| 1000 | 1000 | ProposedA_JointProxy | 3.179 ± 0.732 | 0.119 ± 0.076 | 0.737 ± 0.030 | 0.752 ± 0.028 |
| 1000 | 1000 | ProposedA_Together | 3.175 ± 0.735 | 0.120 ± 0.078 | 0.737 ± 0.030 | 0.752 ± 0.028 |
| 1000 | 1000 | ProposedB_LinearStepB | 3.176 ± 0.737 | 0.116 ± 0.080 | 0.740 ± 0.029 | 0.755 ± 0.028 |
| 1000 | 1000 | ProposedB_SourceDR | 3.870 ± 1.175 | 1.046 ± 0.639 | 0.593 ± 0.126 | 0.607 ± 0.130 |
| 1000 | 1000 | ProxyOnly | 3.867 ± 1.172 | 0.869 ± 0.641 | 0.571 ± 0.132 | 0.586 ± 0.134 |
| 1000 | 1000 | TargetOnlyDR | 3.159 ± 0.761 | 0.147 ± 0.084 | 0.744 ± 0.022 | 0.759 ± 0.021 |

### Targeting / Ranking Metrics

| m0 | m1 | Method | Top-10% (↑) | Top-20% (↑) | Kendall (↑) |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 0.787 ± 0.092 | 0.790 ± 0.092 | 0.589 ± 0.110 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 0.876 ± 0.085 | 0.875 ± 0.091 | 0.695 ± 0.127 |
| 100 | 0 | IPWTransport | 0.882 ± 0.084 | 0.878 ± 0.091 | 0.700 ± 0.126 |
| 100 | 0 | OutcomeModelTransport | 0.881 ± 0.084 | 0.880 ± 0.091 | 0.702 ± 0.126 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 0.624 ± 0.103 | 0.630 ± 0.115 | 0.440 ± 0.069 |
| 100 | 0 | ProxyOnly | 0.539 ± 0.136 | 0.531 ± 0.163 | 0.363 ± 0.093 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 0.669 ± 0.112 | 0.658 ± 0.146 | 0.512 ± 0.053 |
| 100 | 100 | AnchorPlugin | 0.735 ± 0.143 | 0.716 ± 0.191 | 0.570 ± 0.121 |
| 100 | 100 | DRLearner_PooledNoSite | 0.843 ± 0.143 | 0.831 ± 0.160 | 0.677 ± 0.152 |
| 100 | 100 | DRLearner_PooledWithSite | 0.844 ± 0.143 | 0.832 ± 0.158 | 0.678 ± 0.151 |
| 100 | 100 | EntropyBalancing | 0.832 ± 0.154 | 0.815 ± 0.180 | 0.667 ± 0.153 |
| 100 | 100 | IPWTransport | 0.834 ± 0.161 | 0.824 ± 0.167 | 0.672 ± 0.155 |
| 100 | 100 | OutcomeModelTransport | 0.838 ± 0.151 | 0.827 ± 0.164 | 0.673 ± 0.154 |
| 100 | 100 | ProposedA | 0.691 ± 0.134 | 0.673 ± 0.158 | 0.531 ± 0.050 |
| 100 | 100 | ProposedA_FullyJoint | 0.691 ± 0.130 | 0.667 ± 0.165 | 0.533 ± 0.044 |
| 100 | 100 | ProposedA_JointProxy | 0.691 ± 0.126 | 0.671 ± 0.154 | 0.539 ± 0.052 |
| 100 | 100 | ProposedA_Together | 0.692 ± 0.157 | 0.674 ± 0.180 | 0.537 ± 0.048 |
| 100 | 100 | ProposedB_LinearStepB | 0.706 ± 0.125 | 0.674 ± 0.162 | 0.531 ± 0.052 |
| 100 | 100 | ProposedB_SourceDR | 0.554 ± 0.174 | 0.503 ± 0.264 | 0.418 ± 0.069 |
| 100 | 100 | ProxyOnly | 0.439 ± 0.261 | 0.412 ± 0.330 | 0.363 ± 0.090 |
| 100 | 100 | TargetOnlyDR | 0.655 ± 0.133 | 0.630 ± 0.184 | 0.495 ± 0.060 |
| 100 | 500 | AnchorOnly | 0.737 ± 0.063 | 0.726 ± 0.093 | 0.545 ± 0.043 |
| 100 | 500 | AnchorPlugin | 0.742 ± 0.121 | 0.744 ± 0.136 | 0.564 ± 0.100 |
| 100 | 500 | DRLearner_PooledNoSite | 0.859 ± 0.121 | 0.856 ± 0.129 | 0.695 ± 0.145 |
| 100 | 500 | DRLearner_PooledWithSite | 0.854 ± 0.123 | 0.852 ± 0.132 | 0.690 ± 0.148 |
| 100 | 500 | EntropyBalancing | 0.836 ± 0.136 | 0.832 ± 0.141 | 0.667 ± 0.151 |
| 100 | 500 | IPWTransport | 0.844 ± 0.131 | 0.842 ± 0.137 | 0.677 ± 0.153 |
| 100 | 500 | OutcomeModelTransport | 0.846 ± 0.130 | 0.845 ± 0.140 | 0.680 ± 0.153 |
| 100 | 500 | ProposedA | 0.740 ± 0.068 | 0.723 ± 0.084 | 0.538 ± 0.041 |
| 100 | 500 | ProposedA_FullyJoint | 0.492 ± 0.143 | 0.540 ± 0.156 | 0.397 ± 0.042 |
| 100 | 500 | ProposedA_JointProxy | 0.736 ± 0.049 | 0.721 ± 0.090 | 0.539 ± 0.038 |
| 100 | 500 | ProposedA_Together | 0.562 ± 0.113 | 0.585 ± 0.136 | 0.432 ± 0.045 |
| 100 | 500 | ProposedB_LinearStepB | 0.739 ± 0.053 | 0.731 ± 0.082 | 0.541 ± 0.044 |
| 100 | 500 | ProposedB_SourceDR | 0.552 ± 0.125 | 0.544 ± 0.136 | 0.397 ± 0.103 |
| 100 | 500 | ProxyOnly | 0.348 ± 0.238 | 0.325 ± 0.290 | 0.260 ± 0.072 |
| 100 | 500 | TargetOnlyDR | 0.628 ± 0.099 | 0.630 ± 0.136 | 0.465 ± 0.053 |
| 100 | 1000 | AnchorOnly | 0.711 ± 0.078 | 0.696 ± 0.101 | 0.519 ± 0.038 |
| 100 | 1000 | AnchorPlugin | 0.776 ± 0.131 | 0.776 ± 0.129 | 0.587 ± 0.113 |
| 100 | 1000 | DRLearner_PooledNoSite | 0.882 ± 0.118 | 0.879 ± 0.120 | 0.718 ± 0.138 |
| 100 | 1000 | DRLearner_PooledWithSite | 0.874 ± 0.130 | 0.872 ± 0.127 | 0.711 ± 0.144 |
| 100 | 1000 | EntropyBalancing | 0.862 ± 0.139 | 0.860 ± 0.134 | 0.694 ± 0.150 |
| 100 | 1000 | IPWTransport | 0.862 ± 0.142 | 0.860 ± 0.136 | 0.695 ± 0.152 |
| 100 | 1000 | OutcomeModelTransport | 0.861 ± 0.141 | 0.859 ± 0.137 | 0.695 ± 0.153 |
| 100 | 1000 | ProposedA | 0.706 ± 0.073 | 0.700 ± 0.092 | 0.515 ± 0.038 |
| 100 | 1000 | ProposedA_FullyJoint | 0.391 ± 0.122 | 0.463 ± 0.135 | 0.347 ± 0.051 |
| 100 | 1000 | ProposedA_JointProxy | 0.708 ± 0.067 | 0.700 ± 0.085 | 0.520 ± 0.035 |
| 100 | 1000 | ProposedA_Together | 0.474 ± 0.115 | 0.518 ± 0.102 | 0.375 ± 0.045 |
| 100 | 1000 | ProposedB_LinearStepB | 0.706 ± 0.074 | 0.700 ± 0.088 | 0.516 ± 0.037 |
| 100 | 1000 | ProposedB_SourceDR | 0.597 ± 0.122 | 0.579 ± 0.140 | 0.426 ± 0.080 |
| 100 | 1000 | ProxyOnly | 0.350 ± 0.204 | 0.334 ± 0.239 | 0.246 ± 0.103 |
| 100 | 1000 | TargetOnlyDR | 0.504 ± 0.100 | 0.552 ± 0.130 | 0.394 ± 0.061 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 0.784 ± 0.111 | 0.775 ± 0.145 | 0.580 ± 0.098 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 0.825 ± 0.190 | 0.821 ± 0.200 | 0.655 ± 0.168 |
| 500 | 0 | IPWTransport | 0.825 ± 0.191 | 0.822 ± 0.198 | 0.655 ± 0.167 |
| 500 | 0 | OutcomeModelTransport | 0.828 ± 0.190 | 0.824 ± 0.199 | 0.662 ± 0.171 |
| 500 | 0 | ProposedA | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 0.593 ± 0.201 | 0.577 ± 0.215 | 0.398 ± 0.126 |
| 500 | 0 | ProxyOnly | 0.594 ± 0.184 | 0.587 ± 0.195 | 0.409 ± 0.101 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 0.577 ± 0.105 | 0.589 ± 0.113 | 0.447 ± 0.060 |
| 500 | 100 | AnchorPlugin | 0.743 ± 0.105 | 0.730 ± 0.118 | 0.572 ± 0.100 |
| 500 | 100 | DRLearner_PooledNoSite | 0.828 ± 0.119 | 0.831 ± 0.122 | 0.667 ± 0.131 |
| 500 | 100 | DRLearner_PooledWithSite | 0.834 ± 0.114 | 0.835 ± 0.120 | 0.673 ± 0.128 |
| 500 | 100 | EntropyBalancing | 0.821 ± 0.127 | 0.826 ± 0.123 | 0.661 ± 0.131 |
| 500 | 100 | IPWTransport | 0.822 ± 0.128 | 0.826 ± 0.123 | 0.661 ± 0.131 |
| 500 | 100 | OutcomeModelTransport | 0.822 ± 0.122 | 0.825 ± 0.126 | 0.662 ± 0.133 |
| 500 | 100 | ProposedA | 0.730 ± 0.076 | 0.712 ± 0.084 | 0.547 ± 0.030 |
| 500 | 100 | ProposedA_FullyJoint | 0.450 ± 0.127 | 0.501 ± 0.142 | 0.413 ± 0.042 |
| 500 | 100 | ProposedA_JointProxy | 0.739 ± 0.076 | 0.711 ± 0.110 | 0.548 ± 0.031 |
| 500 | 100 | ProposedA_Together | 0.537 ± 0.092 | 0.564 ± 0.120 | 0.442 ± 0.043 |
| 500 | 100 | ProposedB_LinearStepB | 0.713 ± 0.072 | 0.693 ± 0.115 | 0.538 ± 0.027 |
| 500 | 100 | ProposedB_SourceDR | 0.545 ± 0.125 | 0.529 ± 0.121 | 0.413 ± 0.082 |
| 500 | 100 | ProxyOnly | 0.584 ± 0.131 | 0.557 ± 0.150 | 0.424 ± 0.087 |
| 500 | 100 | TargetOnlyDR | 0.550 ± 0.111 | 0.570 ± 0.130 | 0.447 ± 0.052 |
| 500 | 500 | AnchorOnly | 0.766 ± 0.080 | 0.750 ± 0.088 | 0.559 ± 0.032 |
| 500 | 500 | AnchorPlugin | 0.768 ± 0.125 | 0.772 ± 0.130 | 0.589 ± 0.103 |
| 500 | 500 | DRLearner_PooledNoSite | 0.862 ± 0.100 | 0.864 ± 0.102 | 0.693 ± 0.098 |
| 500 | 500 | DRLearner_PooledWithSite | 0.862 ± 0.101 | 0.865 ± 0.103 | 0.693 ± 0.098 |
| 500 | 500 | EntropyBalancing | 0.843 ± 0.113 | 0.849 ± 0.107 | 0.672 ± 0.105 |
| 500 | 500 | IPWTransport | 0.843 ± 0.113 | 0.849 ± 0.107 | 0.673 ± 0.105 |
| 500 | 500 | OutcomeModelTransport | 0.844 ± 0.116 | 0.851 ± 0.110 | 0.676 ± 0.105 |
| 500 | 500 | ProposedA | 0.768 ± 0.083 | 0.753 ± 0.092 | 0.558 ± 0.028 |
| 500 | 500 | ProposedA_FullyJoint | 0.766 ± 0.072 | 0.751 ± 0.084 | 0.556 ± 0.026 |
| 500 | 500 | ProposedA_JointProxy | 0.768 ± 0.076 | 0.743 ± 0.090 | 0.556 ± 0.028 |
| 500 | 500 | ProposedA_Together | 0.772 ± 0.070 | 0.752 ± 0.095 | 0.556 ± 0.027 |
| 500 | 500 | ProposedB_LinearStepB | 0.768 ± 0.071 | 0.749 ± 0.088 | 0.556 ± 0.030 |
| 500 | 500 | ProposedB_SourceDR | 0.608 ± 0.117 | 0.599 ± 0.135 | 0.434 ± 0.072 |
| 500 | 500 | ProxyOnly | 0.570 ± 0.188 | 0.565 ± 0.192 | 0.426 ± 0.107 |
| 500 | 500 | TargetOnlyDR | 0.771 ± 0.068 | 0.745 ± 0.083 | 0.559 ± 0.029 |
| 500 | 1000 | AnchorOnly | 0.738 ± 0.068 | 0.721 ± 0.099 | 0.538 ± 0.028 |
| 500 | 1000 | AnchorPlugin | 0.780 ± 0.095 | 0.775 ± 0.102 | 0.579 ± 0.095 |
| 500 | 1000 | DRLearner_PooledNoSite | 0.885 ± 0.080 | 0.878 ± 0.082 | 0.706 ± 0.118 |
| 500 | 1000 | DRLearner_PooledWithSite | 0.883 ± 0.081 | 0.875 ± 0.084 | 0.702 ± 0.121 |
| 500 | 1000 | EntropyBalancing | 0.849 ± 0.109 | 0.852 ± 0.107 | 0.668 ± 0.138 |
| 500 | 1000 | IPWTransport | 0.852 ± 0.106 | 0.853 ± 0.108 | 0.669 ± 0.137 |
| 500 | 1000 | OutcomeModelTransport | 0.861 ± 0.099 | 0.855 ± 0.099 | 0.677 ± 0.133 |
| 500 | 1000 | ProposedA | 0.735 ± 0.061 | 0.722 ± 0.082 | 0.532 ± 0.026 |
| 500 | 1000 | ProposedA_FullyJoint | 0.731 ± 0.076 | 0.699 ± 0.088 | 0.512 ± 0.028 |
| 500 | 1000 | ProposedA_JointProxy | 0.729 ± 0.070 | 0.724 ± 0.085 | 0.531 ± 0.028 |
| 500 | 1000 | ProposedA_Together | 0.736 ± 0.081 | 0.708 ± 0.097 | 0.520 ± 0.027 |
| 500 | 1000 | ProposedB_LinearStepB | 0.734 ± 0.066 | 0.724 ± 0.077 | 0.534 ± 0.027 |
| 500 | 1000 | ProposedB_SourceDR | 0.576 ± 0.111 | 0.557 ± 0.139 | 0.395 ± 0.081 |
| 500 | 1000 | ProxyOnly | 0.551 ± 0.145 | 0.533 ± 0.195 | 0.373 ± 0.082 |
| 500 | 1000 | TargetOnlyDR | 0.739 ± 0.067 | 0.731 ± 0.089 | 0.534 ± 0.024 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 0.828 ± 0.070 | 0.837 ± 0.069 | 0.613 ± 0.077 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 0.883 ± 0.072 | 0.886 ± 0.073 | 0.689 ± 0.106 |
| 1000 | 0 | IPWTransport | 0.883 ± 0.072 | 0.886 ± 0.074 | 0.688 ± 0.107 |
| 1000 | 0 | OutcomeModelTransport | 0.884 ± 0.071 | 0.888 ± 0.070 | 0.694 ± 0.105 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 0.648 ± 0.070 | 0.644 ± 0.097 | 0.412 ± 0.055 |
| 1000 | 0 | ProxyOnly | 0.659 ± 0.082 | 0.668 ± 0.093 | 0.433 ± 0.063 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 0.500 ± 0.119 | 0.538 ± 0.154 | 0.396 ± 0.051 |
| 1000 | 100 | AnchorPlugin | 0.771 ± 0.145 | 0.769 ± 0.152 | 0.580 ± 0.124 |
| 1000 | 100 | DRLearner_PooledNoSite | 0.828 ± 0.185 | 0.824 ± 0.179 | 0.662 ± 0.179 |
| 1000 | 100 | DRLearner_PooledWithSite | 0.840 ± 0.168 | 0.837 ± 0.163 | 0.673 ± 0.171 |
| 1000 | 100 | EntropyBalancing | 0.814 ± 0.193 | 0.808 ± 0.191 | 0.646 ± 0.184 |
| 1000 | 100 | IPWTransport | 0.814 ± 0.193 | 0.808 ± 0.191 | 0.645 ± 0.184 |
| 1000 | 100 | OutcomeModelTransport | 0.820 ± 0.191 | 0.817 ± 0.184 | 0.653 ± 0.182 |
| 1000 | 100 | ProposedA | 0.713 ± 0.079 | 0.704 ± 0.104 | 0.509 ± 0.039 |
| 1000 | 100 | ProposedA_FullyJoint | 0.424 ± 0.149 | 0.479 ± 0.178 | 0.353 ± 0.045 |
| 1000 | 100 | ProposedA_JointProxy | 0.713 ± 0.096 | 0.705 ± 0.114 | 0.506 ± 0.042 |
| 1000 | 100 | ProposedA_Together | 0.496 ± 0.141 | 0.533 ± 0.163 | 0.379 ± 0.050 |
| 1000 | 100 | ProposedB_LinearStepB | 0.647 ± 0.159 | 0.658 ± 0.160 | 0.483 ± 0.047 |
| 1000 | 100 | ProposedB_SourceDR | 0.559 ± 0.185 | 0.542 ± 0.209 | 0.398 ± 0.100 |
| 1000 | 100 | ProxyOnly | 0.609 ± 0.173 | 0.608 ± 0.162 | 0.433 ± 0.092 |
| 1000 | 100 | TargetOnlyDR | 0.461 ± 0.136 | 0.544 ± 0.143 | 0.387 ± 0.045 |
| 1000 | 500 | AnchorOnly | 0.768 ± 0.056 | 0.769 ± 0.054 | 0.540 ± 0.038 |
| 1000 | 500 | AnchorPlugin | 0.767 ± 0.152 | 0.767 ± 0.147 | 0.552 ± 0.121 |
| 1000 | 500 | DRLearner_PooledNoSite | 0.845 ± 0.162 | 0.848 ± 0.169 | 0.666 ± 0.171 |
| 1000 | 500 | DRLearner_PooledWithSite | 0.853 ± 0.150 | 0.854 ± 0.164 | 0.673 ± 0.166 |
| 1000 | 500 | EntropyBalancing | 0.827 ± 0.184 | 0.830 ± 0.186 | 0.640 ± 0.181 |
| 1000 | 500 | IPWTransport | 0.826 ± 0.188 | 0.830 ± 0.184 | 0.640 ± 0.181 |
| 1000 | 500 | OutcomeModelTransport | 0.825 ± 0.190 | 0.831 ± 0.184 | 0.644 ± 0.185 |
| 1000 | 500 | ProposedA | 0.777 ± 0.054 | 0.777 ± 0.050 | 0.557 ± 0.022 |
| 1000 | 500 | ProposedA_FullyJoint | 0.771 ± 0.065 | 0.763 ± 0.069 | 0.542 ± 0.034 |
| 1000 | 500 | ProposedA_JointProxy | 0.780 ± 0.061 | 0.775 ± 0.052 | 0.555 ± 0.020 |
| 1000 | 500 | ProposedA_Together | 0.772 ± 0.062 | 0.770 ± 0.064 | 0.547 ± 0.033 |
| 1000 | 500 | ProposedB_LinearStepB | 0.783 ± 0.041 | 0.784 ± 0.043 | 0.558 ± 0.024 |
| 1000 | 500 | ProposedB_SourceDR | 0.604 ± 0.215 | 0.611 ± 0.192 | 0.407 ± 0.117 |
| 1000 | 500 | ProxyOnly | 0.618 ± 0.149 | 0.616 ± 0.158 | 0.406 ± 0.112 |
| 1000 | 500 | TargetOnlyDR | 0.786 ± 0.052 | 0.781 ± 0.053 | 0.552 ± 0.035 |
| 1000 | 1000 | AnchorOnly | 0.728 ± 0.063 | 0.714 ± 0.055 | 0.545 ± 0.024 |
| 1000 | 1000 | AnchorPlugin | 0.735 ± 0.205 | 0.727 ± 0.198 | 0.573 ± 0.128 |
| 1000 | 1000 | DRLearner_PooledNoSite | 0.845 ± 0.165 | 0.838 ± 0.173 | 0.699 ± 0.155 |
| 1000 | 1000 | DRLearner_PooledWithSite | 0.844 ± 0.165 | 0.839 ± 0.172 | 0.699 ± 0.155 |
| 1000 | 1000 | EntropyBalancing | 0.791 ± 0.227 | 0.790 ± 0.233 | 0.655 ± 0.183 |
| 1000 | 1000 | IPWTransport | 0.789 ± 0.230 | 0.790 ± 0.234 | 0.654 ± 0.183 |
| 1000 | 1000 | OutcomeModelTransport | 0.803 ± 0.214 | 0.801 ± 0.217 | 0.663 ± 0.178 |
| 1000 | 1000 | ProposedA | 0.718 ± 0.069 | 0.714 ± 0.055 | 0.543 ± 0.027 |
| 1000 | 1000 | ProposedA_FullyJoint | 0.725 ± 0.071 | 0.717 ± 0.050 | 0.543 ± 0.026 |
| 1000 | 1000 | ProposedA_JointProxy | 0.722 ± 0.068 | 0.716 ± 0.053 | 0.543 ± 0.027 |
| 1000 | 1000 | ProposedA_Together | 0.725 ± 0.074 | 0.719 ± 0.053 | 0.544 ± 0.027 |
| 1000 | 1000 | ProposedB_LinearStepB | 0.723 ± 0.069 | 0.717 ± 0.055 | 0.546 ± 0.026 |
| 1000 | 1000 | ProposedB_SourceDR | 0.565 ± 0.164 | 0.541 ± 0.172 | 0.422 ± 0.095 |
| 1000 | 1000 | ProxyOnly | 0.521 ± 0.206 | 0.511 ± 0.217 | 0.405 ± 0.101 |
| 1000 | 1000 | TargetOnlyDR | 0.735 ± 0.059 | 0.718 ± 0.054 | 0.550 ± 0.020 |

### ATE Estimation

| m0 | m1 | Method | ATE Est | ATE Err (↓) | ATE Bias |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 0.193 ± 0.841 | 0.637 ± 0.404 | -0.079 ± 0.764 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 0.196 ± 0.863 | 0.643 ± 0.556 | -0.076 ± 0.859 |
| 100 | 0 | IPWTransport | 0.190 ± 0.853 | 0.642 ± 0.547 | -0.082 ± 0.852 |
| 100 | 0 | OutcomeModelTransport | 0.208 ± 0.840 | 0.650 ± 0.552 | -0.064 ± 0.864 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 0.173 ± 0.425 | 0.862 ± 0.634 | -0.099 ± 1.083 |
| 100 | 0 | ProxyOnly | 0.178 ± 1.196 | 0.684 ± 0.546 | -0.094 ± 0.884 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | -0.389 ± 2.057 | 0.344 ± 0.268 | 0.134 ± 0.421 |
| 100 | 100 | AnchorPlugin | -0.357 ± 1.411 | 0.671 ± 0.406 | 0.167 ± 0.780 |
| 100 | 100 | DRLearner_PooledNoSite | -0.290 ± 1.391 | 0.723 ± 0.607 | 0.233 ± 0.928 |
| 100 | 100 | DRLearner_PooledWithSite | -0.290 ± 1.391 | 0.722 ± 0.606 | 0.233 ± 0.926 |
| 100 | 100 | EntropyBalancing | -0.285 ± 1.373 | 0.745 ± 0.641 | 0.239 ± 0.967 |
| 100 | 100 | IPWTransport | -0.307 ± 1.386 | 0.742 ± 0.628 | 0.217 ± 0.961 |
| 100 | 100 | OutcomeModelTransport | -0.283 ± 1.378 | 0.743 ± 0.631 | 0.240 ± 0.958 |
| 100 | 100 | ProposedA | -0.348 ± 2.027 | 0.320 ± 0.205 | 0.176 ± 0.342 |
| 100 | 100 | ProposedA_FullyJoint | -0.343 ± 1.986 | 0.341 ± 0.175 | 0.181 ± 0.344 |
| 100 | 100 | ProposedA_JointProxy | -0.363 ± 2.011 | 0.300 ± 0.193 | 0.161 ± 0.323 |
| 100 | 100 | ProposedA_Together | -0.345 ± 1.973 | 0.306 ± 0.194 | 0.179 ± 0.321 |
| 100 | 100 | ProposedB_LinearStepB | -0.322 ± 2.027 | 0.290 ± 0.254 | 0.202 ± 0.332 |
| 100 | 100 | ProposedB_SourceDR | -0.217 ± 0.583 | 1.173 ± 0.819 | 0.307 ± 1.421 |
| 100 | 100 | ProxyOnly | -0.313 ± 2.001 | 0.657 ± 0.416 | 0.210 ± 0.762 |
| 100 | 100 | TargetOnlyDR | -0.308 ± 1.905 | 0.438 ± 0.222 | 0.216 ± 0.450 |
| 100 | 500 | AnchorOnly | -0.102 ± 1.058 | 0.154 ± 0.094 | 0.044 ± 0.178 |
| 100 | 500 | AnchorPlugin | -0.032 ± 0.961 | 0.550 ± 0.399 | 0.114 ± 0.681 |
| 100 | 500 | DRLearner_PooledNoSite | 0.018 ± 0.875 | 0.604 ± 0.488 | 0.164 ± 0.771 |
| 100 | 500 | DRLearner_PooledWithSite | 0.018 ± 0.893 | 0.619 ± 0.481 | 0.164 ± 0.778 |
| 100 | 500 | EntropyBalancing | 0.034 ± 0.932 | 0.683 ± 0.492 | 0.180 ± 0.836 |
| 100 | 500 | IPWTransport | 0.042 ± 0.931 | 0.691 ± 0.488 | 0.189 ± 0.839 |
| 100 | 500 | OutcomeModelTransport | 0.036 ± 0.911 | 0.675 ± 0.521 | 0.182 ± 0.846 |
| 100 | 500 | ProposedA | -0.084 ± 1.079 | 0.132 ± 0.088 | 0.062 ± 0.148 |
| 100 | 500 | ProposedA_FullyJoint | 0.048 ± 1.155 | 0.279 ± 0.226 | 0.195 ± 0.305 |
| 100 | 500 | ProposedA_JointProxy | -0.109 ± 1.086 | 0.146 ± 0.101 | 0.038 ± 0.176 |
| 100 | 500 | ProposedA_Together | 0.010 ± 1.137 | 0.222 ± 0.181 | 0.156 ± 0.243 |
| 100 | 500 | ProposedB_LinearStepB | -0.087 ± 1.080 | 0.141 ± 0.096 | 0.059 ± 0.162 |
| 100 | 500 | ProposedB_SourceDR | 0.122 ± 0.556 | 0.807 ± 0.620 | 0.269 ± 0.997 |
| 100 | 500 | ProxyOnly | -0.389 ± 4.003 | 2.577 ± 1.877 | -0.243 ± 3.233 |
| 100 | 500 | TargetOnlyDR | -0.100 ± 1.060 | 0.245 ± 0.192 | 0.047 ± 0.312 |
| 100 | 1000 | AnchorOnly | -0.243 ± 1.166 | 0.113 ± 0.073 | 0.030 ± 0.133 |
| 100 | 1000 | AnchorPlugin | -0.127 ± 1.088 | 0.546 ± 0.637 | 0.145 ± 0.835 |
| 100 | 1000 | DRLearner_PooledNoSite | -0.099 ± 0.827 | 0.574 ± 0.462 | 0.174 ± 0.727 |
| 100 | 1000 | DRLearner_PooledWithSite | -0.082 ± 0.850 | 0.586 ± 0.470 | 0.191 ± 0.737 |
| 100 | 1000 | EntropyBalancing | -0.058 ± 0.855 | 0.675 ± 0.526 | 0.215 ± 0.841 |
| 100 | 1000 | IPWTransport | -0.068 ± 0.841 | 0.680 ± 0.533 | 0.205 ± 0.852 |
| 100 | 1000 | OutcomeModelTransport | -0.050 ± 0.852 | 0.677 ± 0.530 | 0.222 ± 0.843 |
| 100 | 1000 | ProposedA | -0.245 ± 1.172 | 0.123 ± 0.072 | 0.028 ± 0.142 |
| 100 | 1000 | ProposedA_FullyJoint | -0.233 ± 1.311 | 0.377 ± 0.350 | 0.040 ± 0.520 |
| 100 | 1000 | ProposedA_JointProxy | -0.244 ± 1.156 | 0.130 ± 0.093 | 0.029 ± 0.160 |
| 100 | 1000 | ProposedA_Together | -0.246 ± 1.289 | 0.323 ± 0.258 | 0.027 ± 0.419 |
| 100 | 1000 | ProposedB_LinearStepB | -0.248 ± 1.172 | 0.118 ± 0.073 | 0.025 ± 0.139 |
| 100 | 1000 | ProposedB_SourceDR | -0.093 ± 0.576 | 0.760 ± 0.779 | 0.180 ± 1.086 |
| 100 | 1000 | ProxyOnly | -0.998 ± 7.740 | 5.624 ± 4.031 | -0.725 ± 6.999 |
| 100 | 1000 | TargetOnlyDR | -0.194 ± 1.264 | 0.259 ± 0.215 | 0.078 ± 0.332 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 0.452 ± 0.926 | 0.758 ± 0.610 | 0.279 ± 0.946 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 0.611 ± 0.773 | 0.829 ± 0.620 | 0.439 ± 0.952 |
| 500 | 0 | IPWTransport | 0.612 ± 0.774 | 0.836 ± 0.617 | 0.440 ± 0.955 |
| 500 | 0 | OutcomeModelTransport | 0.602 ± 0.778 | 0.818 ± 0.631 | 0.429 ± 0.953 |
| 500 | 0 | ProposedA | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 0.289 ± 0.465 | 0.940 ± 0.580 | 0.116 ± 1.119 |
| 500 | 0 | ProxyOnly | 0.509 ± 1.584 | 1.154 ± 0.759 | 0.336 ± 1.363 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | -0.722 ± 1.237 | 0.321 ± 0.219 | -0.009 ± 0.395 |
| 500 | 100 | AnchorPlugin | -0.401 ± 1.302 | 0.644 ± 0.527 | 0.312 ± 0.782 |
| 500 | 100 | DRLearner_PooledNoSite | -0.219 ± 1.247 | 0.656 ± 0.535 | 0.494 ± 0.695 |
| 500 | 100 | DRLearner_PooledWithSite | -0.214 ± 1.232 | 0.651 ± 0.516 | 0.499 ± 0.671 |
| 500 | 100 | EntropyBalancing | -0.183 ± 1.256 | 0.707 ± 0.577 | 0.530 ± 0.750 |
| 500 | 100 | IPWTransport | -0.186 ± 1.253 | 0.705 ± 0.577 | 0.526 ± 0.751 |
| 500 | 100 | OutcomeModelTransport | -0.171 ± 1.259 | 0.712 ± 0.574 | 0.541 ± 0.745 |
| 500 | 100 | ProposedA | -0.753 ± 1.220 | 0.198 ± 0.170 | -0.040 ± 0.262 |
| 500 | 100 | ProposedA_FullyJoint | -0.726 ± 1.209 | 0.257 ± 0.219 | -0.013 ± 0.342 |
| 500 | 100 | ProposedA_JointProxy | -0.751 ± 1.206 | 0.163 ± 0.186 | -0.038 ± 0.247 |
| 500 | 100 | ProposedA_Together | -0.724 ± 1.225 | 0.256 ± 0.203 | -0.011 ± 0.332 |
| 500 | 100 | ProposedB_LinearStepB | -0.720 ± 1.224 | 0.205 ± 0.182 | -0.007 ± 0.278 |
| 500 | 100 | ProposedB_SourceDR | -0.004 ± 0.669 | 0.898 ± 0.653 | 0.709 ± 0.864 |
| 500 | 100 | ProxyOnly | -0.478 ± 1.424 | 0.718 ± 0.576 | 0.234 ± 0.904 |
| 500 | 100 | TargetOnlyDR | -0.759 ± 1.174 | 0.300 ± 0.229 | -0.046 ± 0.380 |
| 500 | 500 | AnchorOnly | -0.122 ± 1.118 | 0.116 ± 0.092 | 0.052 ± 0.141 |
| 500 | 500 | AnchorPlugin | -0.346 ± 0.796 | 0.693 ± 0.438 | -0.172 ± 0.816 |
| 500 | 500 | DRLearner_PooledNoSite | -0.345 ± 0.942 | 0.757 ± 0.458 | -0.171 ± 0.884 |
| 500 | 500 | DRLearner_PooledWithSite | -0.343 ± 0.945 | 0.752 ± 0.459 | -0.169 ± 0.881 |
| 500 | 500 | EntropyBalancing | -0.372 ± 0.962 | 0.875 ± 0.523 | -0.198 ± 1.019 |
| 500 | 500 | IPWTransport | -0.373 ± 0.957 | 0.877 ± 0.523 | -0.199 ± 1.021 |
| 500 | 500 | OutcomeModelTransport | -0.371 ± 0.981 | 0.877 ± 0.526 | -0.197 ± 1.022 |
| 500 | 500 | ProposedA | -0.160 ± 1.154 | 0.103 ± 0.080 | 0.014 ± 0.132 |
| 500 | 500 | ProposedA_FullyJoint | -0.151 ± 1.160 | 0.100 ± 0.074 | 0.022 ± 0.125 |
| 500 | 500 | ProposedA_JointProxy | -0.151 ± 1.159 | 0.100 ± 0.074 | 0.022 ± 0.124 |
| 500 | 500 | ProposedA_Together | -0.156 ± 1.153 | 0.105 ± 0.082 | 0.018 ± 0.135 |
| 500 | 500 | ProposedB_LinearStepB | -0.150 ± 1.138 | 0.105 ± 0.084 | 0.024 ± 0.134 |
| 500 | 500 | ProposedB_SourceDR | -0.237 ± 0.436 | 0.854 ± 0.633 | -0.063 ± 1.079 |
| 500 | 500 | ProxyOnly | -0.436 ± 1.361 | 0.894 ± 0.459 | -0.262 ± 0.990 |
| 500 | 500 | TargetOnlyDR | -0.139 ± 1.148 | 0.115 ± 0.099 | 0.035 ± 0.149 |
| 500 | 1000 | AnchorOnly | 0.115 ± 1.343 | 0.123 ± 0.089 | -0.014 ± 0.154 |
| 500 | 1000 | AnchorPlugin | -0.024 ± 0.964 | 0.621 ± 0.541 | -0.154 ± 0.821 |
| 500 | 1000 | DRLearner_PooledNoSite | 0.018 ± 1.018 | 0.566 ± 0.390 | -0.112 ± 0.691 |
| 500 | 1000 | DRLearner_PooledWithSite | 0.003 ± 1.019 | 0.574 ± 0.400 | -0.127 ± 0.700 |
| 500 | 1000 | EntropyBalancing | -0.073 ± 0.998 | 0.729 ± 0.542 | -0.202 ± 0.900 |
| 500 | 1000 | IPWTransport | -0.080 ± 1.000 | 0.732 ± 0.548 | -0.209 ± 0.904 |
| 500 | 1000 | OutcomeModelTransport | -0.032 ± 0.989 | 0.700 ± 0.506 | -0.161 ± 0.863 |
| 500 | 1000 | ProposedA | 0.135 ± 1.361 | 0.112 ± 0.076 | 0.005 ± 0.138 |
| 500 | 1000 | ProposedA_FullyJoint | 0.170 ± 1.383 | 0.145 ± 0.075 | 0.040 ± 0.161 |
| 500 | 1000 | ProposedA_JointProxy | 0.139 ± 1.358 | 0.110 ± 0.078 | 0.009 ± 0.137 |
| 500 | 1000 | ProposedA_Together | 0.154 ± 1.387 | 0.144 ± 0.071 | 0.024 ± 0.162 |
| 500 | 1000 | ProposedB_LinearStepB | 0.143 ± 1.357 | 0.107 ± 0.072 | 0.013 ± 0.131 |
| 500 | 1000 | ProposedB_SourceDR | -0.187 ± 0.536 | 0.911 ± 0.730 | -0.317 ± 1.141 |
| 500 | 1000 | ProxyOnly | 0.142 ± 2.082 | 1.114 ± 0.802 | 0.012 ± 1.396 |
| 500 | 1000 | TargetOnlyDR | 0.151 ± 1.354 | 0.134 ± 0.099 | 0.021 ± 0.168 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 0.537 ± 0.867 | 0.683 ± 0.540 | -0.450 ± 0.755 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 0.529 ± 0.832 | 0.904 ± 0.563 | -0.458 ± 0.978 |
| 1000 | 0 | IPWTransport | 0.528 ± 0.833 | 0.904 ± 0.563 | -0.459 ± 0.977 |
| 1000 | 0 | OutcomeModelTransport | 0.533 ± 0.837 | 0.894 ± 0.577 | -0.454 ± 0.978 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 0.265 ± 0.497 | 1.104 ± 0.621 | -0.722 ± 1.058 |
| 1000 | 0 | ProxyOnly | 0.882 ± 1.643 | 0.866 ± 0.717 | -0.105 ± 1.136 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | -0.066 ± 1.616 | 0.286 ± 0.364 | -0.074 ± 0.461 |
| 1000 | 100 | AnchorPlugin | -0.389 ± 1.084 | 0.710 ± 0.452 | -0.397 ± 0.755 |
| 1000 | 100 | DRLearner_PooledNoSite | -0.217 ± 1.094 | 0.671 ± 0.609 | -0.225 ± 0.890 |
| 1000 | 100 | DRLearner_PooledWithSite | -0.175 ± 1.119 | 0.639 ± 0.582 | -0.182 ± 0.856 |
| 1000 | 100 | EntropyBalancing | -0.213 ± 1.097 | 0.782 ± 0.690 | -0.221 ± 1.033 |
| 1000 | 100 | IPWTransport | -0.214 ± 1.097 | 0.783 ± 0.692 | -0.222 ± 1.036 |
| 1000 | 100 | OutcomeModelTransport | -0.202 ± 1.108 | 0.771 ± 0.683 | -0.210 ± 1.023 |
| 1000 | 100 | ProposedA | 0.032 ± 1.356 | 0.158 ± 0.104 | 0.025 ± 0.191 |
| 1000 | 100 | ProposedA_FullyJoint | -0.105 ± 1.661 | 0.416 ± 0.458 | -0.113 ± 0.615 |
| 1000 | 100 | ProposedA_JointProxy | 0.021 ± 1.357 | 0.164 ± 0.137 | 0.013 ± 0.217 |
| 1000 | 100 | ProposedA_Together | -0.081 ± 1.616 | 0.341 ± 0.376 | -0.089 ± 0.505 |
| 1000 | 100 | ProposedB_LinearStepB | 0.037 ± 1.411 | 0.198 ± 0.085 | 0.029 ± 0.218 |
| 1000 | 100 | ProposedB_SourceDR | -0.164 ± 0.668 | 1.034 ± 0.662 | -0.172 ± 1.238 |
| 1000 | 100 | ProxyOnly | -0.408 ± 1.143 | 0.764 ± 0.462 | -0.416 ± 0.804 |
| 1000 | 100 | TargetOnlyDR | -0.011 ± 1.588 | 0.330 ± 0.332 | -0.019 ± 0.474 |
| 1000 | 500 | AnchorOnly | 0.633 ± 1.088 | 0.147 ± 0.153 | -0.037 ± 0.211 |
| 1000 | 500 | AnchorPlugin | 0.534 ± 1.005 | 0.788 ± 0.528 | -0.136 ± 0.955 |
| 1000 | 500 | DRLearner_PooledNoSite | 0.576 ± 0.902 | 0.763 ± 0.447 | -0.095 ± 0.896 |
| 1000 | 500 | DRLearner_PooledWithSite | 0.579 ± 0.876 | 0.726 ± 0.422 | -0.092 ± 0.851 |
| 1000 | 500 | EntropyBalancing | 0.573 ± 0.962 | 0.913 ± 0.538 | -0.098 ± 1.075 |
| 1000 | 500 | IPWTransport | 0.573 ± 0.961 | 0.911 ± 0.537 | -0.098 ± 1.073 |
| 1000 | 500 | OutcomeModelTransport | 0.567 ± 0.974 | 0.926 ± 0.547 | -0.103 ± 1.091 |
| 1000 | 500 | ProposedA | 0.627 ± 1.052 | 0.113 ± 0.125 | -0.043 ± 0.164 |
| 1000 | 500 | ProposedA_FullyJoint | 0.633 ± 1.072 | 0.123 ± 0.126 | -0.037 ± 0.174 |
| 1000 | 500 | ProposedA_JointProxy | 0.622 ± 1.051 | 0.108 ± 0.120 | -0.049 ± 0.156 |
| 1000 | 500 | ProposedA_Together | 0.636 ± 1.074 | 0.118 ± 0.137 | -0.035 ± 0.180 |
| 1000 | 500 | ProposedB_LinearStepB | 0.623 ± 1.064 | 0.120 ± 0.123 | -0.047 ± 0.167 |
| 1000 | 500 | ProposedB_SourceDR | 0.307 ± 0.444 | 0.941 ± 0.586 | -0.363 ± 1.066 |
| 1000 | 500 | ProxyOnly | 0.623 ± 1.240 | 0.825 ± 0.644 | -0.047 ± 1.063 |
| 1000 | 500 | TargetOnlyDR | 0.650 ± 1.091 | 0.153 ± 0.171 | -0.020 ± 0.231 |
| 1000 | 1000 | AnchorOnly | -0.851 ± 1.347 | 0.145 ± 0.094 | -0.027 ± 0.174 |
| 1000 | 1000 | AnchorPlugin | -0.196 ± 1.219 | 0.676 ± 0.448 | 0.627 ± 0.517 |
| 1000 | 1000 | DRLearner_PooledNoSite | -0.423 ± 1.126 | 0.539 ± 0.423 | 0.400 ± 0.562 |
| 1000 | 1000 | DRLearner_PooledWithSite | -0.423 ± 1.124 | 0.537 ± 0.424 | 0.401 ± 0.561 |
| 1000 | 1000 | EntropyBalancing | -0.304 ± 1.151 | 0.721 ± 0.583 | 0.519 ± 0.777 |
| 1000 | 1000 | IPWTransport | -0.304 ± 1.154 | 0.725 ± 0.583 | 0.519 ± 0.780 |
| 1000 | 1000 | OutcomeModelTransport | -0.297 ± 1.117 | 0.705 ± 0.581 | 0.526 ± 0.755 |
| 1000 | 1000 | ProposedA | -0.837 ± 1.317 | 0.118 ± 0.071 | -0.014 ± 0.140 |
| 1000 | 1000 | ProposedA_FullyJoint | -0.842 ± 1.325 | 0.126 ± 0.076 | -0.018 ± 0.149 |
| 1000 | 1000 | ProposedA_JointProxy | -0.843 ± 1.315 | 0.119 ± 0.076 | -0.019 ± 0.143 |
| 1000 | 1000 | ProposedA_Together | -0.837 ± 1.327 | 0.120 ± 0.078 | -0.014 ± 0.145 |
| 1000 | 1000 | ProposedB_LinearStepB | -0.844 ± 1.325 | 0.116 ± 0.080 | -0.021 ± 0.142 |
| 1000 | 1000 | ProposedB_SourceDR | -0.025 ± 0.543 | 1.046 ± 0.639 | 0.798 ± 0.943 |
| 1000 | 1000 | ProxyOnly | -0.283 ± 1.836 | 0.869 ± 0.641 | 0.540 ± 0.948 |
| 1000 | 1000 | TargetOnlyDR | -0.841 ± 1.329 | 0.147 ± 0.084 | -0.017 ± 0.172 |

### Policy / Decision Metrics

| m0 | m1 | Method | Policy Value (↑) | Regret (↓) | Value Top20 (↑) | Regret Top20 (↓) |
|---|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 1.540 ± 0.460 | 0.377 ± 0.271 | 0.956 ± 0.661 | 0.273 ± 0.178 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 1.669 ± 0.528 | 0.248 ± 0.194 | 1.068 ± 0.648 | 0.161 ± 0.132 |
| 100 | 0 | IPWTransport | 1.676 ± 0.530 | 0.241 ± 0.193 | 1.071 ± 0.648 | 0.158 ± 0.134 |
| 100 | 0 | OutcomeModelTransport | 1.676 ± 0.526 | 0.241 ± 0.194 | 1.073 ± 0.650 | 0.156 ± 0.135 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 1.257 ± 0.454 | 0.660 ± 0.217 | 0.776 ± 0.614 | 0.453 ± 0.136 |
| 100 | 0 | ProxyOnly | 1.058 ± 0.453 | 0.859 ± 0.383 | 0.648 ± 0.600 | 0.581 ± 0.220 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 1.264 ± 0.662 | 0.534 ± 0.202 | 0.893 ± 0.855 | 0.356 ± 0.114 |
| 100 | 100 | AnchorPlugin | 1.380 ± 0.671 | 0.418 ± 0.250 | 0.953 ± 0.870 | 0.296 ± 0.165 |
| 100 | 100 | DRLearner_PooledNoSite | 1.505 ± 0.706 | 0.293 ± 0.258 | 1.062 ± 0.895 | 0.187 ± 0.181 |
| 100 | 100 | DRLearner_PooledWithSite | 1.505 ± 0.708 | 0.292 ± 0.260 | 1.062 ± 0.896 | 0.187 ± 0.181 |
| 100 | 100 | EntropyBalancing | 1.484 ± 0.708 | 0.314 ± 0.271 | 1.047 ± 0.890 | 0.202 ± 0.192 |
| 100 | 100 | IPWTransport | 1.493 ± 0.710 | 0.305 ± 0.269 | 1.054 ± 0.894 | 0.195 ± 0.190 |
| 100 | 100 | OutcomeModelTransport | 1.494 ± 0.710 | 0.303 ± 0.269 | 1.056 ± 0.898 | 0.193 ± 0.190 |
| 100 | 100 | ProposedA | 1.300 ± 0.669 | 0.498 ± 0.157 | 0.909 ± 0.872 | 0.340 ± 0.124 |
| 100 | 100 | ProposedA_FullyJoint | 1.301 ± 0.660 | 0.497 ± 0.135 | 0.909 ± 0.858 | 0.340 ± 0.105 |
| 100 | 100 | ProposedA_JointProxy | 1.305 ± 0.675 | 0.493 ± 0.180 | 0.903 ± 0.875 | 0.346 ± 0.147 |
| 100 | 100 | ProposedA_Together | 1.307 ± 0.671 | 0.490 ± 0.132 | 0.923 ± 0.855 | 0.326 ± 0.089 |
| 100 | 100 | ProposedB_LinearStepB | 1.299 ± 0.662 | 0.499 ± 0.150 | 0.915 ± 0.847 | 0.334 ± 0.118 |
| 100 | 100 | ProposedB_SourceDR | 1.061 ± 0.711 | 0.737 ± 0.211 | 0.751 ± 0.879 | 0.498 ± 0.134 |
| 100 | 100 | ProxyOnly | 0.973 ± 0.752 | 0.825 ± 0.324 | 0.657 ± 0.886 | 0.592 ± 0.187 |
| 100 | 100 | TargetOnlyDR | 1.254 ± 0.654 | 0.544 ± 0.162 | 0.878 ± 0.833 | 0.371 ± 0.100 |
| 100 | 500 | AnchorOnly | 1.406 ± 0.722 | 0.441 ± 0.131 | 1.006 ± 0.766 | 0.308 ± 0.062 |
| 100 | 500 | AnchorPlugin | 1.446 ± 0.776 | 0.401 ± 0.155 | 1.027 ± 0.825 | 0.287 ± 0.125 |
| 100 | 500 | DRLearner_PooledNoSite | 1.602 ± 0.800 | 0.245 ± 0.201 | 1.148 ± 0.842 | 0.166 ± 0.148 |
| 100 | 500 | DRLearner_PooledWithSite | 1.594 ± 0.802 | 0.253 ± 0.208 | 1.144 ± 0.844 | 0.170 ± 0.151 |
| 100 | 500 | EntropyBalancing | 1.562 ± 0.798 | 0.285 ± 0.217 | 1.121 ± 0.847 | 0.193 ± 0.158 |
| 100 | 500 | IPWTransport | 1.574 ± 0.802 | 0.273 ± 0.218 | 1.131 ± 0.846 | 0.182 ± 0.157 |
| 100 | 500 | OutcomeModelTransport | 1.577 ± 0.804 | 0.270 ± 0.222 | 1.135 ± 0.845 | 0.179 ± 0.162 |
| 100 | 500 | ProposedA | 1.390 ± 0.721 | 0.457 ± 0.123 | 0.999 ± 0.767 | 0.314 ± 0.065 |
| 100 | 500 | ProposedA_FullyJoint | 1.048 ± 0.657 | 0.799 ± 0.332 | 0.784 ± 0.719 | 0.530 ± 0.176 |
| 100 | 500 | ProposedA_JointProxy | 1.392 ± 0.711 | 0.455 ± 0.125 | 0.999 ± 0.782 | 0.314 ± 0.060 |
| 100 | 500 | ProposedA_Together | 1.160 ± 0.659 | 0.687 ± 0.227 | 0.842 ± 0.743 | 0.472 ± 0.119 |
| 100 | 500 | ProposedB_LinearStepB | 1.391 ± 0.721 | 0.456 ± 0.127 | 1.008 ± 0.769 | 0.306 ± 0.067 |
| 100 | 500 | ProposedB_SourceDR | 1.061 ± 0.747 | 0.786 ± 0.288 | 0.784 ± 0.825 | 0.530 ± 0.169 |
| 100 | 500 | ProxyOnly | 0.797 ± 0.757 | 1.050 ± 0.265 | 0.570 ± 0.759 | 0.744 ± 0.161 |
| 100 | 500 | TargetOnlyDR | 1.244 ± 0.655 | 0.603 ± 0.212 | 0.898 ± 0.741 | 0.416 ± 0.105 |
| 100 | 1000 | AnchorOnly | 1.308 ± 0.624 | 0.475 ± 0.101 | 0.941 ± 0.747 | 0.336 ± 0.078 |
| 100 | 1000 | AnchorPlugin | 1.393 ± 0.630 | 0.390 ± 0.211 | 1.028 ± 0.733 | 0.249 ± 0.143 |
| 100 | 1000 | DRLearner_PooledNoSite | 1.558 ± 0.622 | 0.225 ± 0.206 | 1.135 ± 0.741 | 0.142 ± 0.149 |
| 100 | 1000 | DRLearner_PooledWithSite | 1.546 ± 0.626 | 0.236 ± 0.223 | 1.127 ± 0.741 | 0.150 ± 0.158 |
| 100 | 1000 | EntropyBalancing | 1.518 ± 0.632 | 0.265 ± 0.244 | 1.112 ± 0.745 | 0.165 ± 0.168 |
| 100 | 1000 | IPWTransport | 1.516 ± 0.628 | 0.266 ± 0.240 | 1.112 ± 0.742 | 0.165 ± 0.170 |
| 100 | 1000 | OutcomeModelTransport | 1.517 ± 0.627 | 0.266 ± 0.244 | 1.111 ± 0.743 | 0.166 ± 0.172 |
| 100 | 1000 | ProposedA | 1.303 ± 0.611 | 0.479 ± 0.094 | 0.944 ± 0.740 | 0.332 ± 0.075 |
| 100 | 1000 | ProposedA_FullyJoint | 0.817 ± 0.615 | 0.966 ± 0.262 | 0.675 ± 0.702 | 0.602 ± 0.133 |
| 100 | 1000 | ProposedA_JointProxy | 1.302 ± 0.626 | 0.481 ± 0.103 | 0.943 ± 0.747 | 0.334 ± 0.064 |
| 100 | 1000 | ProposedA_Together | 0.965 ± 0.585 | 0.818 ± 0.249 | 0.734 ± 0.730 | 0.543 ± 0.105 |
| 100 | 1000 | ProposedB_LinearStepB | 1.308 ± 0.614 | 0.475 ± 0.092 | 0.943 ± 0.742 | 0.334 ± 0.072 |
| 100 | 1000 | ProposedB_SourceDR | 1.074 ± 0.641 | 0.709 ± 0.222 | 0.803 ± 0.746 | 0.474 ± 0.151 |
| 100 | 1000 | ProxyOnly | 0.700 ± 0.689 | 1.083 ± 0.305 | 0.542 ± 0.719 | 0.735 ± 0.208 |
| 100 | 1000 | TargetOnlyDR | 1.038 ± 0.608 | 0.745 ± 0.180 | 0.777 ± 0.753 | 0.500 ± 0.118 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 1.347 ± 0.736 | 0.429 ± 0.244 | 0.846 ± 0.674 | 0.277 ± 0.177 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 1.422 ± 0.747 | 0.354 ± 0.390 | 0.903 ± 0.668 | 0.220 ± 0.249 |
| 500 | 0 | IPWTransport | 1.422 ± 0.747 | 0.354 ± 0.391 | 0.905 ± 0.669 | 0.218 ± 0.247 |
| 500 | 0 | OutcomeModelTransport | 1.426 ± 0.742 | 0.350 ± 0.387 | 0.908 ± 0.665 | 0.215 ± 0.248 |
| 500 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 0.974 ± 0.739 | 0.802 ± 0.436 | 0.601 ± 0.649 | 0.522 ± 0.259 |
| 500 | 0 | ProxyOnly | 0.928 ± 0.881 | 0.848 ± 0.350 | 0.618 ± 0.663 | 0.505 ± 0.211 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 1.148 ± 0.799 | 0.725 ± 0.327 | 0.987 ± 0.954 | 0.462 ± 0.160 |
| 500 | 100 | AnchorPlugin | 1.428 ± 0.894 | 0.446 ± 0.282 | 1.135 ± 0.955 | 0.314 ± 0.187 |
| 500 | 100 | DRLearner_PooledNoSite | 1.545 ± 0.885 | 0.328 ± 0.263 | 1.239 ± 0.959 | 0.210 ± 0.194 |
| 500 | 100 | DRLearner_PooledWithSite | 1.558 ± 0.884 | 0.315 ± 0.250 | 1.245 ± 0.965 | 0.204 ± 0.187 |
| 500 | 100 | EntropyBalancing | 1.536 ± 0.879 | 0.337 ± 0.278 | 1.233 ± 0.953 | 0.215 ± 0.198 |
| 500 | 100 | IPWTransport | 1.536 ± 0.884 | 0.337 ± 0.276 | 1.233 ± 0.956 | 0.215 ± 0.196 |
| 500 | 100 | OutcomeModelTransport | 1.532 ± 0.879 | 0.341 ± 0.276 | 1.232 ± 0.957 | 0.216 ± 0.199 |
| 500 | 100 | ProposedA | 1.402 ± 0.864 | 0.471 ± 0.130 | 1.133 ± 0.967 | 0.315 ± 0.070 |
| 500 | 100 | ProposedA_FullyJoint | 1.081 ± 0.813 | 0.792 ± 0.253 | 0.902 ± 0.957 | 0.546 ± 0.127 |
| 500 | 100 | ProposedA_JointProxy | 1.410 ± 0.859 | 0.463 ± 0.133 | 1.137 ± 0.972 | 0.312 ± 0.077 |
| 500 | 100 | ProposedA_Together | 1.178 ± 0.824 | 0.695 ± 0.240 | 0.965 ± 0.958 | 0.484 ± 0.135 |
| 500 | 100 | ProposedB_LinearStepB | 1.402 ± 0.879 | 0.471 ± 0.130 | 1.117 ± 0.969 | 0.332 ± 0.075 |
| 500 | 100 | ProposedB_SourceDR | 1.069 ± 0.868 | 0.805 ± 0.348 | 0.904 ± 0.961 | 0.545 ± 0.225 |
| 500 | 100 | ProxyOnly | 1.067 ± 0.939 | 0.806 ± 0.429 | 0.944 ± 0.940 | 0.504 ± 0.229 |
| 500 | 100 | TargetOnlyDR | 1.178 ± 0.788 | 0.695 ± 0.300 | 0.973 ± 0.945 | 0.476 ± 0.144 |
| 500 | 500 | AnchorOnly | 1.384 ± 0.596 | 0.392 ± 0.085 | 0.997 ± 0.628 | 0.266 ± 0.060 |
| 500 | 500 | AnchorPlugin | 1.391 ± 0.648 | 0.385 ± 0.211 | 1.008 ± 0.657 | 0.255 ± 0.148 |
| 500 | 500 | DRLearner_PooledNoSite | 1.530 ± 0.621 | 0.246 ± 0.144 | 1.110 ± 0.650 | 0.152 ± 0.124 |
| 500 | 500 | DRLearner_PooledWithSite | 1.531 ± 0.620 | 0.245 ± 0.144 | 1.110 ± 0.648 | 0.152 ± 0.125 |
| 500 | 500 | EntropyBalancing | 1.493 ± 0.620 | 0.283 ± 0.165 | 1.093 ± 0.640 | 0.170 ± 0.130 |
| 500 | 500 | IPWTransport | 1.494 ± 0.618 | 0.281 ± 0.163 | 1.093 ± 0.642 | 0.170 ± 0.131 |
| 500 | 500 | OutcomeModelTransport | 1.496 ± 0.619 | 0.280 ± 0.164 | 1.094 ± 0.650 | 0.168 ± 0.133 |
| 500 | 500 | ProposedA | 1.375 ± 0.594 | 0.401 ± 0.105 | 1.001 ± 0.627 | 0.262 ± 0.058 |
| 500 | 500 | ProposedA_FullyJoint | 1.370 ± 0.585 | 0.406 ± 0.098 | 0.996 ± 0.628 | 0.267 ± 0.054 |
| 500 | 500 | ProposedA_JointProxy | 1.374 ± 0.598 | 0.402 ± 0.091 | 0.989 ± 0.627 | 0.273 ± 0.053 |
| 500 | 500 | ProposedA_Together | 1.376 ± 0.591 | 0.400 ± 0.097 | 0.999 ± 0.625 | 0.264 ± 0.060 |
| 500 | 500 | ProposedB_LinearStepB | 1.384 ± 0.590 | 0.392 ± 0.101 | 0.994 ± 0.619 | 0.269 ± 0.060 |
| 500 | 500 | ProposedB_SourceDR | 1.097 ± 0.565 | 0.679 ± 0.184 | 0.825 ± 0.593 | 0.438 ± 0.141 |
| 500 | 500 | ProxyOnly | 1.048 ± 0.638 | 0.728 ± 0.296 | 0.785 ± 0.644 | 0.478 ± 0.200 |
| 500 | 500 | TargetOnlyDR | 1.394 ± 0.596 | 0.382 ± 0.077 | 0.988 ± 0.637 | 0.274 ± 0.064 |
| 500 | 1000 | AnchorOnly | 1.330 ± 0.640 | 0.440 ± 0.095 | 0.786 ± 0.630 | 0.330 ± 0.072 |
| 500 | 1000 | AnchorPlugin | 1.351 ± 0.631 | 0.419 ± 0.268 | 0.840 ± 0.649 | 0.276 ± 0.159 |
| 500 | 1000 | DRLearner_PooledNoSite | 1.533 ± 0.626 | 0.237 ± 0.219 | 0.960 ± 0.643 | 0.155 ± 0.139 |
| 500 | 1000 | DRLearner_PooledWithSite | 1.524 ± 0.626 | 0.246 ± 0.233 | 0.956 ± 0.643 | 0.160 ± 0.143 |
| 500 | 1000 | EntropyBalancing | 1.448 ± 0.642 | 0.322 ± 0.356 | 0.923 ± 0.658 | 0.192 ± 0.192 |
| 500 | 1000 | IPWTransport | 1.450 ± 0.641 | 0.320 ± 0.348 | 0.925 ± 0.659 | 0.191 ± 0.192 |
| 500 | 1000 | OutcomeModelTransport | 1.470 ± 0.637 | 0.300 ± 0.304 | 0.929 ± 0.651 | 0.186 ± 0.172 |
| 500 | 1000 | ProposedA | 1.313 ± 0.647 | 0.458 ± 0.109 | 0.783 ± 0.644 | 0.332 ± 0.074 |
| 500 | 1000 | ProposedA_FullyJoint | 1.274 ± 0.644 | 0.497 ± 0.130 | 0.756 ± 0.639 | 0.360 ± 0.079 |
| 500 | 1000 | ProposedA_JointProxy | 1.323 ± 0.642 | 0.447 ± 0.113 | 0.784 ± 0.639 | 0.332 ± 0.084 |
| 500 | 1000 | ProposedA_Together | 1.280 ± 0.639 | 0.490 ± 0.131 | 0.768 ± 0.631 | 0.347 ± 0.080 |
| 500 | 1000 | ProposedB_LinearStepB | 1.321 ± 0.647 | 0.449 ± 0.105 | 0.784 ± 0.644 | 0.332 ± 0.079 |
| 500 | 1000 | ProposedB_SourceDR | 0.956 ± 0.681 | 0.814 ± 0.356 | 0.581 ± 0.682 | 0.534 ± 0.171 |
| 500 | 1000 | ProxyOnly | 0.896 ± 0.692 | 0.875 ± 0.274 | 0.567 ± 0.648 | 0.549 ± 0.159 |
| 500 | 1000 | TargetOnlyDR | 1.323 ± 0.641 | 0.447 ± 0.098 | 0.795 ± 0.634 | 0.320 ± 0.076 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 1.381 ± 0.629 | 0.344 ± 0.133 | 0.578 ± 0.757 | 0.226 ± 0.101 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 1.456 ± 0.674 | 0.270 ± 0.168 | 0.646 ± 0.771 | 0.158 ± 0.100 |
| 1000 | 0 | IPWTransport | 1.454 ± 0.675 | 0.271 ± 0.169 | 0.645 ± 0.771 | 0.159 ± 0.100 |
| 1000 | 0 | OutcomeModelTransport | 1.464 ± 0.663 | 0.261 ± 0.159 | 0.647 ± 0.767 | 0.158 ± 0.101 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 0.970 ± 0.607 | 0.756 ± 0.176 | 0.314 ± 0.721 | 0.491 ± 0.119 |
| 1000 | 0 | ProxyOnly | 0.999 ± 0.616 | 0.727 ± 0.182 | 0.344 ± 0.729 | 0.460 ± 0.133 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 1.432 ± 0.625 | 0.844 ± 0.410 | 1.050 ± 0.717 | 0.594 ± 0.260 |
| 1000 | 100 | AnchorPlugin | 1.798 ± 0.709 | 0.479 ± 0.427 | 1.325 ± 0.726 | 0.319 ± 0.296 |
| 1000 | 100 | DRLearner_PooledNoSite | 1.887 ± 0.772 | 0.389 ± 0.506 | 1.389 ± 0.739 | 0.255 ± 0.349 |
| 1000 | 100 | DRLearner_PooledWithSite | 1.912 ± 0.772 | 0.365 ± 0.472 | 1.408 ± 0.739 | 0.235 ± 0.317 |
| 1000 | 100 | EntropyBalancing | 1.848 ± 0.769 | 0.429 ± 0.516 | 1.368 ± 0.741 | 0.275 ± 0.372 |
| 1000 | 100 | IPWTransport | 1.846 ± 0.767 | 0.430 ± 0.518 | 1.368 ± 0.742 | 0.276 ± 0.372 |
| 1000 | 100 | OutcomeModelTransport | 1.859 ± 0.773 | 0.417 ± 0.529 | 1.380 ± 0.742 | 0.264 ± 0.357 |
| 1000 | 100 | ProposedA | 1.747 ± 0.787 | 0.530 ± 0.165 | 1.276 ± 0.773 | 0.368 ± 0.124 |
| 1000 | 100 | ProposedA_FullyJoint | 1.237 ± 0.716 | 1.039 ± 0.452 | 0.982 ± 0.702 | 0.661 ± 0.272 |
| 1000 | 100 | ProposedA_JointProxy | 1.747 ± 0.770 | 0.529 ± 0.181 | 1.278 ± 0.798 | 0.365 ± 0.127 |
| 1000 | 100 | ProposedA_Together | 1.353 ± 0.689 | 0.923 ± 0.424 | 1.044 ± 0.719 | 0.600 ± 0.265 |
| 1000 | 100 | ProposedB_LinearStepB | 1.691 ± 0.767 | 0.585 ± 0.199 | 1.224 ± 0.779 | 0.419 ± 0.151 |
| 1000 | 100 | ProposedB_SourceDR | 1.392 ± 0.781 | 0.884 ± 0.532 | 1.046 ± 0.718 | 0.597 ± 0.370 |
| 1000 | 100 | ProxyOnly | 1.462 ± 0.682 | 0.814 ± 0.520 | 1.127 ± 0.734 | 0.516 ± 0.305 |
| 1000 | 100 | TargetOnlyDR | 1.398 ± 0.632 | 0.878 ± 0.375 | 1.059 ± 0.726 | 0.585 ± 0.232 |
| 1000 | 500 | AnchorOnly | 1.267 ± 0.678 | 0.477 ± 0.204 | 0.552 ± 0.705 | 0.342 ± 0.108 |
| 1000 | 500 | AnchorPlugin | 1.186 ± 0.847 | 0.559 ± 0.490 | 0.530 ± 0.802 | 0.364 ± 0.327 |
| 1000 | 500 | DRLearner_PooledNoSite | 1.342 ± 0.885 | 0.403 ± 0.522 | 0.640 ± 0.825 | 0.254 ± 0.359 |
| 1000 | 500 | DRLearner_PooledWithSite | 1.363 ± 0.863 | 0.381 ± 0.487 | 0.649 ± 0.819 | 0.245 ± 0.350 |
| 1000 | 500 | EntropyBalancing | 1.277 ± 0.919 | 0.468 ± 0.579 | 0.608 ± 0.844 | 0.286 ± 0.398 |
| 1000 | 500 | IPWTransport | 1.276 ± 0.923 | 0.469 ± 0.583 | 0.609 ± 0.842 | 0.285 ± 0.395 |
| 1000 | 500 | OutcomeModelTransport | 1.285 ± 0.928 | 0.460 ± 0.586 | 0.612 ± 0.842 | 0.282 ± 0.393 |
| 1000 | 500 | ProposedA | 1.305 ± 0.658 | 0.440 ± 0.146 | 0.565 ± 0.712 | 0.329 ± 0.100 |
| 1000 | 500 | ProposedA_FullyJoint | 1.277 ± 0.660 | 0.468 ± 0.155 | 0.545 ± 0.721 | 0.349 ± 0.119 |
| 1000 | 500 | ProposedA_JointProxy | 1.306 ± 0.648 | 0.439 ± 0.139 | 0.562 ± 0.709 | 0.332 ± 0.107 |
| 1000 | 500 | ProposedA_Together | 1.287 ± 0.666 | 0.457 ± 0.156 | 0.556 ± 0.715 | 0.338 ± 0.108 |
| 1000 | 500 | ProposedB_LinearStepB | 1.309 ± 0.662 | 0.436 ± 0.139 | 0.576 ± 0.700 | 0.318 ± 0.084 |
| 1000 | 500 | ProposedB_SourceDR | 0.853 ± 0.861 | 0.892 ± 0.555 | 0.288 ± 0.865 | 0.606 ± 0.458 |
| 1000 | 500 | ProxyOnly | 0.835 ± 0.919 | 0.910 ± 0.608 | 0.316 ± 0.785 | 0.578 ± 0.321 |
| 1000 | 500 | TargetOnlyDR | 1.289 ± 0.666 | 0.456 ± 0.164 | 0.571 ± 0.709 | 0.323 ± 0.101 |
| 1000 | 1000 | AnchorOnly | 1.224 ± 0.736 | 0.443 ± 0.109 | 0.978 ± 0.915 | 0.307 ± 0.069 |
| 1000 | 1000 | AnchorPlugin | 1.202 ± 0.635 | 0.465 ± 0.378 | 0.972 ± 0.809 | 0.313 ± 0.291 |
| 1000 | 1000 | DRLearner_PooledNoSite | 1.385 ± 0.643 | 0.282 ± 0.335 | 1.094 ± 0.833 | 0.192 ± 0.255 |
| 1000 | 1000 | DRLearner_PooledWithSite | 1.384 ± 0.642 | 0.283 ± 0.340 | 1.094 ± 0.834 | 0.191 ± 0.255 |
| 1000 | 1000 | EntropyBalancing | 1.286 ± 0.615 | 0.381 ± 0.438 | 1.035 ± 0.797 | 0.250 ± 0.337 |
| 1000 | 1000 | IPWTransport | 1.284 ± 0.609 | 0.383 ± 0.442 | 1.035 ± 0.795 | 0.250 ± 0.339 |
| 1000 | 1000 | OutcomeModelTransport | 1.300 ± 0.633 | 0.367 ± 0.436 | 1.048 ± 0.815 | 0.237 ± 0.319 |
| 1000 | 1000 | ProposedA | 1.215 ± 0.731 | 0.452 ± 0.130 | 0.979 ± 0.914 | 0.307 ± 0.071 |
| 1000 | 1000 | ProposedA_FullyJoint | 1.224 ± 0.739 | 0.443 ± 0.121 | 0.983 ± 0.917 | 0.303 ± 0.063 |
| 1000 | 1000 | ProposedA_JointProxy | 1.225 ± 0.733 | 0.443 ± 0.117 | 0.981 ± 0.919 | 0.304 ± 0.063 |
| 1000 | 1000 | ProposedA_Together | 1.221 ± 0.740 | 0.446 ± 0.119 | 0.984 ± 0.922 | 0.301 ± 0.064 |
| 1000 | 1000 | ProposedB_LinearStepB | 1.224 ± 0.737 | 0.443 ± 0.114 | 0.982 ± 0.912 | 0.303 ± 0.067 |
| 1000 | 1000 | ProposedB_SourceDR | 0.917 ± 0.705 | 0.750 ± 0.387 | 0.783 ± 0.870 | 0.502 ± 0.265 |
| 1000 | 1000 | ProxyOnly | 0.869 ± 0.751 | 0.798 ± 0.385 | 0.742 ± 0.834 | 0.543 ± 0.313 |
| 1000 | 1000 | TargetOnlyDR | 1.235 ± 0.735 | 0.432 ± 0.105 | 0.983 ± 0.914 | 0.303 ± 0.071 |

### Calibration Metrics

| m0 | m1 | Method | Slope (→1) | Intercept (→0) | R² (↑) | ECE (↓) | MCE (↓) |
|---|---|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 1.031 ± 0.135 | 0.129 ± 0.770 | 0.628 ± 0.161 | 0.730 ± 0.340 | 1.359 ± 0.477 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 0.970 ± 0.136 | 0.081 ± 0.839 | 0.769 ± 0.164 | 0.740 ± 0.512 | 1.414 ± 0.837 |
| 100 | 0 | IPWTransport | 0.978 ± 0.130 | 0.086 ± 0.834 | 0.775 ± 0.164 | 0.725 ± 0.506 | 1.395 ± 0.853 |
| 100 | 0 | OutcomeModelTransport | 0.980 ± 0.127 | 0.071 ± 0.853 | 0.777 ± 0.164 | 0.729 ± 0.517 | 1.381 ± 0.868 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 1.333 ± 0.215 | 0.047 ± 0.998 | 0.405 ± 0.101 | 1.040 ± 0.507 | 2.219 ± 0.860 |
| 100 | 0 | ProxyOnly | 1.200 ± 0.419 | 0.001 ± 1.006 | 0.282 ± 0.117 | 1.022 ± 0.491 | 2.111 ± 0.968 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 1.545 ± 0.265 | 0.109 ± 1.761 | 0.499 ± 0.086 | 1.083 ± 0.328 | 2.548 ± 0.824 |
| 100 | 100 | AnchorPlugin | 1.041 ± 0.208 | -0.183 ± 0.829 | 0.602 ± 0.177 | 0.802 ± 0.370 | 1.592 ± 0.609 |
| 100 | 100 | DRLearner_PooledNoSite | 0.984 ± 0.114 | -0.233 ± 0.928 | 0.741 ± 0.199 | 0.819 ± 0.536 | 1.393 ± 0.790 |
| 100 | 100 | DRLearner_PooledWithSite | 0.985 ± 0.114 | -0.233 ± 0.926 | 0.742 ± 0.199 | 0.818 ± 0.534 | 1.398 ± 0.790 |
| 100 | 100 | EntropyBalancing | 0.970 ± 0.120 | -0.237 ± 0.974 | 0.729 ± 0.204 | 0.840 ± 0.570 | 1.443 ± 0.895 |
| 100 | 100 | IPWTransport | 0.977 ± 0.115 | -0.214 ± 0.963 | 0.734 ± 0.204 | 0.830 ± 0.565 | 1.428 ± 0.881 |
| 100 | 100 | OutcomeModelTransport | 0.980 ± 0.115 | -0.238 ± 0.958 | 0.736 ± 0.203 | 0.840 ± 0.557 | 1.419 ± 0.824 |
| 100 | 100 | ProposedA | 1.604 ± 0.297 | 0.098 ± 1.667 | 0.534 ± 0.078 | 1.112 ± 0.343 | 2.793 ± 0.921 |
| 100 | 100 | ProposedA_FullyJoint | 1.659 ± 0.297 | 0.006 ± 1.684 | 0.540 ± 0.066 | 1.176 ± 0.394 | 2.841 ± 0.890 |
| 100 | 100 | ProposedA_JointProxy | 1.637 ± 0.335 | 0.153 ± 1.652 | 0.544 ± 0.089 | 1.142 ± 0.362 | 2.923 ± 0.948 |
| 100 | 100 | ProposedA_Together | 1.674 ± 0.327 | 0.005 ± 1.642 | 0.546 ± 0.074 | 1.139 ± 0.403 | 2.908 ± 1.021 |
| 100 | 100 | ProposedB_LinearStepB | 1.609 ± 0.305 | 0.014 ± 1.631 | 0.534 ± 0.084 | 1.116 ± 0.377 | 2.912 ± 0.869 |
| 100 | 100 | ProposedB_SourceDR | 1.337 ± 0.355 | -0.239 ± 1.292 | 0.375 ± 0.101 | 1.365 ± 0.691 | 2.694 ± 1.169 |
| 100 | 100 | ProxyOnly | 1.309 ± 0.410 | -0.065 ± 1.327 | 0.287 ± 0.124 | 0.979 ± 0.328 | 2.441 ± 0.855 |
| 100 | 100 | TargetOnlyDR | 1.479 ± 0.297 | -0.036 ± 1.370 | 0.480 ± 0.092 | 1.061 ± 0.313 | 2.470 ± 0.724 |
| 100 | 500 | AnchorOnly | 1.582 ± 0.287 | 0.051 ± 0.612 | 0.561 ± 0.065 | 1.059 ± 0.414 | 2.480 ± 0.923 |
| 100 | 500 | AnchorPlugin | 1.022 ± 0.175 | -0.083 ± 0.636 | 0.595 ± 0.149 | 0.720 ± 0.326 | 1.523 ± 0.665 |
| 100 | 500 | DRLearner_PooledNoSite | 0.985 ± 0.159 | -0.152 ± 0.788 | 0.762 ± 0.188 | 0.782 ± 0.438 | 1.427 ± 0.810 |
| 100 | 500 | DRLearner_PooledWithSite | 0.980 ± 0.161 | -0.148 ± 0.794 | 0.756 ± 0.193 | 0.790 ± 0.441 | 1.457 ± 0.840 |
| 100 | 500 | EntropyBalancing | 0.951 ± 0.164 | -0.153 ± 0.850 | 0.726 ± 0.201 | 0.846 ± 0.460 | 1.583 ± 0.881 |
| 100 | 500 | IPWTransport | 0.965 ± 0.165 | -0.162 ± 0.854 | 0.738 ± 0.202 | 0.848 ± 0.461 | 1.562 ± 0.903 |
| 100 | 500 | OutcomeModelTransport | 0.970 ± 0.167 | -0.159 ± 0.861 | 0.742 ± 0.202 | 0.846 ± 0.480 | 1.553 ± 0.891 |
| 100 | 500 | ProposedA | 1.562 ± 0.273 | 0.028 ± 0.598 | 0.552 ± 0.064 | 1.020 ± 0.376 | 2.436 ± 0.928 |
| 100 | 500 | ProposedA_FullyJoint | 0.792 ± 0.258 | -0.124 ± 0.386 | 0.204 ± 0.091 | 1.035 ± 0.419 | 2.311 ± 0.846 |
| 100 | 500 | ProposedA_JointProxy | 1.577 ± 0.268 | 0.074 ± 0.600 | 0.553 ± 0.055 | 1.033 ± 0.388 | 2.475 ± 0.843 |
| 100 | 500 | ProposedA_Together | 0.986 ± 0.294 | -0.078 ± 0.329 | 0.286 ± 0.118 | 0.927 ± 0.257 | 1.947 ± 0.548 |
| 100 | 500 | ProposedB_LinearStepB | 1.581 ± 0.315 | 0.052 ± 0.623 | 0.553 ± 0.066 | 1.055 ± 0.399 | 2.422 ± 0.868 |
| 100 | 500 | ProposedB_SourceDR | 1.265 ± 0.283 | -0.258 ± 1.039 | 0.349 ± 0.139 | 1.030 ± 0.503 | 2.148 ± 0.774 |
| 100 | 500 | ProxyOnly | 0.390 ± 0.139 | 0.029 ± 0.918 | 0.162 ± 0.073 | 3.406 ± 1.532 | 7.708 ± 3.851 |
| 100 | 500 | TargetOnlyDR | 1.234 ± 0.258 | -0.076 ± 0.456 | 0.380 ± 0.080 | 0.865 ± 0.357 | 1.862 ± 0.747 |
| 100 | 1000 | AnchorOnly | 1.389 ± 0.201 | 0.070 ± 0.555 | 0.503 ± 0.073 | 0.844 ± 0.255 | 2.082 ± 0.788 |
| 100 | 1000 | AnchorPlugin | 0.995 ± 0.136 | -0.130 ± 0.835 | 0.628 ± 0.168 | 0.700 ± 0.568 | 1.262 ± 0.830 |
| 100 | 1000 | DRLearner_PooledNoSite | 0.961 ± 0.117 | -0.173 ± 0.728 | 0.794 ± 0.177 | 0.690 ± 0.423 | 1.234 ± 0.700 |
| 100 | 1000 | DRLearner_PooledWithSite | 0.953 ± 0.126 | -0.188 ± 0.738 | 0.785 ± 0.187 | 0.703 ± 0.462 | 1.283 ± 0.791 |
| 100 | 1000 | EntropyBalancing | 0.936 ± 0.141 | -0.220 ± 0.836 | 0.765 ± 0.199 | 0.815 ± 0.508 | 1.447 ± 0.865 |
| 100 | 1000 | IPWTransport | 0.937 ± 0.141 | -0.208 ± 0.846 | 0.765 ± 0.200 | 0.818 ± 0.516 | 1.455 ± 0.868 |
| 100 | 1000 | OutcomeModelTransport | 0.935 ± 0.140 | -0.222 ± 0.835 | 0.764 ± 0.201 | 0.808 ± 0.519 | 1.446 ± 0.900 |
| 100 | 1000 | ProposedA | 1.366 ± 0.200 | 0.072 ± 0.540 | 0.493 ± 0.075 | 0.822 ± 0.269 | 1.994 ± 0.901 |
| 100 | 1000 | ProposedA_FullyJoint | 0.377 ± 0.169 | -0.160 ± 0.789 | 0.088 ± 0.055 | 1.276 ± 0.346 | 2.970 ± 0.780 |
| 100 | 1000 | ProposedA_JointProxy | 1.388 ± 0.231 | 0.087 ± 0.601 | 0.504 ± 0.070 | 0.820 ± 0.283 | 2.108 ± 0.794 |
| 100 | 1000 | ProposedA_Together | 0.563 ± 0.230 | -0.057 ± 0.641 | 0.151 ± 0.077 | 0.980 ± 0.328 | 2.319 ± 0.711 |
| 100 | 1000 | ProposedB_LinearStepB | 1.370 ± 0.193 | 0.080 ± 0.530 | 0.495 ± 0.070 | 0.818 ± 0.270 | 2.017 ± 0.841 |
| 100 | 1000 | ProposedB_SourceDR | 1.202 ± 0.231 | -0.195 ± 1.094 | 0.387 ± 0.115 | 0.960 ± 0.737 | 1.898 ± 1.033 |
| 100 | 1000 | ProxyOnly | 0.191 ± 0.083 | -0.065 ± 1.199 | 0.154 ± 0.104 | 7.951 ± 3.119 | 18.201 ± 5.540 |
| 100 | 1000 | TargetOnlyDR | 0.717 ± 0.232 | -0.025 ± 0.416 | 0.196 ± 0.103 | 0.867 ± 0.224 | 2.007 ± 0.496 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 1.020 ± 0.162 | -0.326 ± 0.920 | 0.619 ± 0.143 | 0.865 ± 0.552 | 1.529 ± 0.783 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 0.914 ± 0.232 | -0.437 ± 0.906 | 0.721 ± 0.217 | 1.025 ± 0.722 | 1.901 ± 1.405 |
| 500 | 0 | IPWTransport | 0.914 ± 0.231 | -0.437 ± 0.909 | 0.722 ± 0.216 | 1.027 ± 0.721 | 1.906 ± 1.425 |
| 500 | 0 | OutcomeModelTransport | 0.917 ± 0.222 | -0.430 ± 0.913 | 0.727 ± 0.218 | 1.017 ± 0.723 | 1.843 ± 1.420 |
| 500 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 1.122 ± 0.341 | -0.189 ± 1.090 | 0.356 ± 0.144 | 1.087 ± 0.549 | 2.284 ± 0.934 |
| 500 | 0 | ProxyOnly | 1.194 ± 0.283 | -0.536 ± 1.604 | 0.361 ± 0.138 | 1.311 ± 0.685 | 2.520 ± 0.968 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 1.062 ± 0.337 | -0.030 ± 0.683 | 0.316 ± 0.123 | 1.043 ± 0.395 | 2.399 ± 0.901 |
| 500 | 100 | AnchorPlugin | 1.068 ± 0.162 | -0.288 ± 0.810 | 0.608 ± 0.145 | 0.798 ± 0.475 | 1.560 ± 0.752 |
| 500 | 100 | DRLearner_PooledNoSite | 0.989 ± 0.144 | -0.481 ± 0.658 | 0.733 ± 0.176 | 0.773 ± 0.500 | 1.542 ± 1.148 |
| 500 | 100 | DRLearner_PooledWithSite | 0.997 ± 0.147 | -0.486 ± 0.639 | 0.741 ± 0.171 | 0.765 ± 0.492 | 1.546 ± 1.122 |
| 500 | 100 | EntropyBalancing | 0.977 ± 0.143 | -0.515 ± 0.699 | 0.726 ± 0.179 | 0.812 ± 0.553 | 1.539 ± 1.203 |
| 500 | 100 | IPWTransport | 0.978 ± 0.144 | -0.510 ± 0.701 | 0.726 ± 0.179 | 0.808 ± 0.554 | 1.565 ± 1.193 |
| 500 | 100 | OutcomeModelTransport | 0.983 ± 0.146 | -0.524 ± 0.694 | 0.726 ± 0.180 | 0.814 ± 0.546 | 1.605 ± 1.201 |
| 500 | 100 | ProposedA | 1.537 ± 0.259 | 0.407 ± 0.878 | 0.566 ± 0.052 | 1.065 ± 0.372 | 2.776 ± 1.181 |
| 500 | 100 | ProposedA_FullyJoint | 0.834 ± 0.311 | -0.168 ± 0.462 | 0.208 ± 0.094 | 1.146 ± 0.366 | 2.475 ± 0.693 |
| 500 | 100 | ProposedA_JointProxy | 1.558 ± 0.290 | 0.431 ± 0.873 | 0.569 ± 0.052 | 1.061 ± 0.453 | 2.808 ± 1.127 |
| 500 | 100 | ProposedA_Together | 1.056 ± 0.273 | 0.004 ± 0.498 | 0.298 ± 0.084 | 1.000 ± 0.377 | 2.134 ± 0.816 |
| 500 | 100 | ProposedB_LinearStepB | 1.488 ± 0.226 | 0.307 ± 0.837 | 0.544 ± 0.050 | 1.038 ± 0.328 | 2.496 ± 1.056 |
| 500 | 100 | ProposedB_SourceDR | 1.276 ± 0.237 | -0.658 ± 0.869 | 0.367 ± 0.117 | 1.111 ± 0.497 | 2.381 ± 1.013 |
| 500 | 100 | ProxyOnly | 1.557 ± 0.351 | 0.086 ± 1.431 | 0.382 ± 0.120 | 1.169 ± 0.436 | 2.792 ± 1.037 |
| 500 | 100 | TargetOnlyDR | 1.053 ± 0.373 | 0.042 ± 0.610 | 0.307 ± 0.121 | 1.072 ± 0.461 | 2.229 ± 0.777 |
| 500 | 500 | AnchorOnly | 1.470 ± 0.179 | -0.017 ± 0.523 | 0.582 ± 0.047 | 0.888 ± 0.266 | 2.278 ± 0.661 |
| 500 | 500 | AnchorPlugin | 1.020 ± 0.141 | 0.156 ± 0.821 | 0.630 ± 0.153 | 0.821 ± 0.334 | 1.415 ± 0.476 |
| 500 | 500 | DRLearner_PooledNoSite | 0.975 ± 0.091 | 0.168 ± 0.877 | 0.772 ± 0.127 | 0.811 ± 0.420 | 1.396 ± 0.600 |
| 500 | 500 | DRLearner_PooledWithSite | 0.976 ± 0.091 | 0.167 ± 0.874 | 0.773 ± 0.126 | 0.809 ± 0.420 | 1.399 ± 0.609 |
| 500 | 500 | EntropyBalancing | 0.954 ± 0.087 | 0.173 ± 0.995 | 0.746 ± 0.141 | 0.935 ± 0.479 | 1.482 ± 0.672 |
| 500 | 500 | IPWTransport | 0.955 ± 0.086 | 0.175 ± 0.997 | 0.746 ± 0.140 | 0.933 ± 0.485 | 1.489 ± 0.682 |
| 500 | 500 | OutcomeModelTransport | 0.957 ± 0.091 | 0.181 ± 0.999 | 0.749 ± 0.140 | 0.928 ± 0.490 | 1.523 ± 0.707 |
| 500 | 500 | ProposedA | 1.467 ± 0.212 | 0.021 ± 0.583 | 0.580 ± 0.042 | 0.862 ± 0.272 | 2.360 ± 0.665 |
| 500 | 500 | ProposedA_FullyJoint | 1.458 ± 0.201 | 0.013 ± 0.590 | 0.576 ± 0.039 | 0.842 ± 0.255 | 2.238 ± 0.665 |
| 500 | 500 | ProposedA_JointProxy | 1.456 ± 0.201 | 0.024 ± 0.573 | 0.577 ± 0.042 | 0.845 ± 0.262 | 2.291 ± 0.664 |
| 500 | 500 | ProposedA_Together | 1.469 ± 0.219 | 0.015 ± 0.592 | 0.579 ± 0.040 | 0.849 ± 0.270 | 2.323 ± 0.641 |
| 500 | 500 | ProposedB_LinearStepB | 1.463 ± 0.209 | 0.020 ± 0.547 | 0.578 ± 0.044 | 0.854 ± 0.238 | 2.242 ± 0.675 |
| 500 | 500 | ProposedB_SourceDR | 1.331 ± 0.212 | 0.151 ± 1.117 | 0.394 ± 0.104 | 1.046 ± 0.532 | 2.167 ± 0.890 |
| 500 | 500 | ProxyOnly | 1.338 ± 0.403 | 0.312 ± 1.290 | 0.387 ± 0.139 | 1.136 ± 0.387 | 2.390 ± 0.895 |
| 500 | 500 | TargetOnlyDR | 1.464 ± 0.187 | 0.023 ± 0.555 | 0.582 ± 0.042 | 0.882 ± 0.226 | 2.304 ± 0.602 |
| 500 | 1000 | AnchorOnly | 1.551 ± 0.227 | -0.078 ± 0.772 | 0.555 ± 0.042 | 0.933 ± 0.270 | 2.415 ± 0.620 |
| 500 | 1000 | AnchorPlugin | 1.056 ± 0.155 | 0.095 ± 0.882 | 0.620 ± 0.143 | 0.755 ± 0.499 | 1.485 ± 0.901 |
| 500 | 1000 | DRLearner_PooledNoSite | 1.005 ± 0.103 | 0.092 ± 0.713 | 0.786 ± 0.157 | 0.629 ± 0.384 | 1.173 ± 0.651 |
| 500 | 1000 | DRLearner_PooledWithSite | 1.001 ± 0.105 | 0.107 ± 0.722 | 0.781 ± 0.162 | 0.638 ± 0.393 | 1.196 ± 0.709 |
| 500 | 1000 | EntropyBalancing | 0.963 ± 0.141 | 0.174 ± 0.881 | 0.739 ± 0.192 | 0.788 ± 0.536 | 1.440 ± 1.055 |
| 500 | 1000 | IPWTransport | 0.965 ± 0.137 | 0.182 ± 0.883 | 0.740 ± 0.190 | 0.790 ± 0.537 | 1.431 ± 1.037 |
| 500 | 1000 | OutcomeModelTransport | 0.975 ± 0.125 | 0.140 ± 0.861 | 0.748 ± 0.183 | 0.761 ± 0.497 | 1.396 ± 0.930 |
| 500 | 1000 | ProposedA | 1.526 ± 0.204 | -0.099 ± 0.718 | 0.546 ± 0.038 | 0.904 ± 0.249 | 2.292 ± 0.490 |
| 500 | 1000 | ProposedA_FullyJoint | 1.496 ± 0.195 | -0.113 ± 0.756 | 0.517 ± 0.037 | 0.872 ± 0.240 | 2.305 ± 0.529 |
| 500 | 1000 | ProposedA_JointProxy | 1.518 ± 0.197 | -0.099 ± 0.696 | 0.545 ± 0.041 | 0.892 ± 0.239 | 2.339 ± 0.518 |
| 500 | 1000 | ProposedA_Together | 1.503 ± 0.185 | -0.111 ± 0.759 | 0.529 ± 0.039 | 0.875 ± 0.217 | 2.430 ± 0.548 |
| 500 | 1000 | ProposedB_LinearStepB | 1.530 ± 0.197 | -0.085 ± 0.742 | 0.549 ± 0.040 | 0.911 ± 0.238 | 2.277 ± 0.553 |
| 500 | 1000 | ProposedB_SourceDR | 1.291 ± 0.193 | 0.341 ± 1.085 | 0.342 ± 0.110 | 1.133 ± 0.573 | 2.121 ± 0.761 |
| 500 | 1000 | ProxyOnly | 0.928 ± 0.257 | -0.052 ± 1.483 | 0.307 ± 0.103 | 1.279 ± 0.695 | 2.399 ± 0.999 |
| 500 | 1000 | TargetOnlyDR | 1.531 ± 0.245 | -0.135 ± 0.772 | 0.548 ± 0.036 | 0.920 ± 0.271 | 2.388 ± 0.542 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 1.072 ± 0.128 | 0.440 ± 0.700 | 0.666 ± 0.109 | 0.766 ± 0.489 | 1.382 ± 0.848 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 0.959 ± 0.127 | 0.503 ± 0.970 | 0.763 ± 0.135 | 0.988 ± 0.507 | 1.653 ± 0.730 |
| 1000 | 0 | IPWTransport | 0.958 ± 0.128 | 0.504 ± 0.970 | 0.762 ± 0.136 | 0.990 ± 0.504 | 1.661 ± 0.740 |
| 1000 | 0 | OutcomeModelTransport | 0.963 ± 0.112 | 0.493 ± 0.971 | 0.770 ± 0.132 | 0.967 ± 0.518 | 1.559 ± 0.711 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 1.291 ± 0.189 | 0.643 ± 1.075 | 0.361 ± 0.080 | 1.208 ± 0.568 | 2.371 ± 0.930 |
| 1000 | 0 | ProxyOnly | 1.398 ± 0.362 | -0.295 ± 1.618 | 0.391 ± 0.095 | 1.177 ± 0.557 | 2.407 ± 1.123 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 0.627 ± 0.249 | -0.084 ± 0.677 | 0.165 ± 0.095 | 1.140 ± 0.601 | 2.533 ± 1.434 |
| 1000 | 100 | AnchorPlugin | 1.064 ± 0.181 | 0.431 ± 0.722 | 0.619 ± 0.177 | 0.820 ± 0.431 | 1.780 ± 1.063 |
| 1000 | 100 | DRLearner_PooledNoSite | 0.974 ± 0.197 | 0.230 ± 0.842 | 0.724 ± 0.226 | 0.843 ± 0.697 | 1.595 ± 1.509 |
| 1000 | 100 | DRLearner_PooledWithSite | 0.989 ± 0.189 | 0.207 ± 0.815 | 0.738 ± 0.216 | 0.816 ± 0.638 | 1.563 ± 1.309 |
| 1000 | 100 | EntropyBalancing | 0.957 ± 0.207 | 0.212 ± 0.997 | 0.702 ± 0.231 | 0.949 ± 0.762 | 1.735 ± 1.591 |
| 1000 | 100 | IPWTransport | 0.956 ± 0.207 | 0.214 ± 1.000 | 0.701 ± 0.231 | 0.950 ± 0.766 | 1.749 ± 1.608 |
| 1000 | 100 | OutcomeModelTransport | 0.965 ± 0.201 | 0.207 ± 0.982 | 0.712 ± 0.230 | 0.943 ± 0.763 | 1.743 ± 1.626 |
| 1000 | 100 | ProposedA | 1.384 ± 0.226 | -0.139 ± 0.658 | 0.485 ± 0.077 | 0.926 ± 0.389 | 2.201 ± 1.109 |
| 1000 | 100 | ProposedA_FullyJoint | 0.424 ± 0.155 | 0.019 ± 0.888 | 0.094 ± 0.059 | 1.388 ± 0.594 | 2.967 ± 1.355 |
| 1000 | 100 | ProposedA_JointProxy | 1.406 ± 0.185 | -0.043 ± 0.686 | 0.484 ± 0.065 | 0.922 ± 0.390 | 2.282 ± 1.075 |
| 1000 | 100 | ProposedA_Together | 0.598 ± 0.226 | 0.011 ± 0.701 | 0.147 ± 0.086 | 1.207 ± 0.590 | 2.523 ± 1.225 |
| 1000 | 100 | ProposedB_LinearStepB | 1.279 ± 0.270 | -0.129 ± 0.609 | 0.428 ± 0.106 | 0.873 ± 0.327 | 2.226 ± 0.930 |
| 1000 | 100 | ProposedB_SourceDR | 1.271 ± 0.328 | 0.200 ± 1.257 | 0.347 ± 0.121 | 1.198 ± 0.601 | 2.453 ± 1.189 |
| 1000 | 100 | ProxyOnly | 1.627 ± 0.397 | 0.778 ± 1.419 | 0.395 ± 0.123 | 1.187 ± 0.456 | 3.013 ± 1.345 |
| 1000 | 100 | TargetOnlyDR | 0.646 ± 0.220 | -0.103 ± 0.535 | 0.153 ± 0.063 | 1.118 ± 0.378 | 2.492 ± 0.976 |
| 1000 | 500 | AnchorOnly | 1.437 ± 0.207 | -0.237 ± 0.538 | 0.546 ± 0.065 | 0.977 ± 0.397 | 2.408 ± 0.951 |
| 1000 | 500 | AnchorPlugin | 0.998 ± 0.155 | 0.176 ± 0.934 | 0.579 ± 0.172 | 0.867 ± 0.528 | 1.538 ± 0.941 |
| 1000 | 500 | DRLearner_PooledNoSite | 0.979 ± 0.194 | 0.109 ± 0.916 | 0.729 ± 0.226 | 0.897 ± 0.490 | 1.718 ± 0.964 |
| 1000 | 500 | DRLearner_PooledWithSite | 0.989 ± 0.187 | 0.096 ± 0.881 | 0.738 ± 0.220 | 0.863 ± 0.444 | 1.650 ± 0.864 |
| 1000 | 500 | EntropyBalancing | 0.948 ± 0.222 | 0.135 ± 1.046 | 0.698 ± 0.237 | 1.059 ± 0.606 | 1.986 ± 1.283 |
| 1000 | 500 | IPWTransport | 0.947 ± 0.223 | 0.137 ± 1.041 | 0.698 ± 0.238 | 1.053 ± 0.604 | 2.000 ± 1.327 |
| 1000 | 500 | OutcomeModelTransport | 0.947 ± 0.220 | 0.137 ± 1.063 | 0.702 ± 0.241 | 1.079 ± 0.621 | 2.043 ± 1.314 |
| 1000 | 500 | ProposedA | 1.443 ± 0.200 | -0.178 ± 0.426 | 0.579 ± 0.034 | 0.946 ± 0.406 | 2.326 ± 0.973 |
| 1000 | 500 | ProposedA_FullyJoint | 1.458 ± 0.227 | -0.222 ± 0.505 | 0.555 ± 0.051 | 0.983 ± 0.395 | 2.348 ± 0.984 |
| 1000 | 500 | ProposedA_JointProxy | 1.445 ± 0.190 | -0.181 ± 0.434 | 0.577 ± 0.032 | 0.961 ± 0.397 | 2.327 ± 0.849 |
| 1000 | 500 | ProposedA_Together | 1.448 ± 0.212 | -0.204 ± 0.478 | 0.563 ± 0.050 | 0.967 ± 0.384 | 2.326 ± 0.957 |
| 1000 | 500 | ProposedB_LinearStepB | 1.453 ± 0.188 | -0.179 ± 0.460 | 0.579 ± 0.036 | 0.979 ± 0.428 | 2.441 ± 1.013 |
| 1000 | 500 | ProposedB_SourceDR | 1.245 ± 0.390 | 0.212 ± 1.159 | 0.366 ± 0.133 | 1.185 ± 0.438 | 2.577 ± 1.030 |
| 1000 | 500 | ProxyOnly | 1.299 ± 0.304 | -0.117 ± 1.302 | 0.356 ± 0.144 | 1.118 ± 0.476 | 2.420 ± 0.818 |
| 1000 | 500 | TargetOnlyDR | 1.455 ± 0.209 | -0.262 ± 0.575 | 0.570 ± 0.054 | 0.972 ± 0.402 | 2.416 ± 0.971 |
| 1000 | 1000 | AnchorOnly | 1.496 ± 0.221 | 0.453 ± 0.813 | 0.566 ± 0.037 | 0.919 ± 0.383 | 2.332 ± 0.874 |
| 1000 | 1000 | AnchorPlugin | 1.035 ± 0.142 | -0.622 ± 0.506 | 0.610 ± 0.187 | 0.753 ± 0.429 | 1.446 ± 0.797 |
| 1000 | 1000 | DRLearner_PooledNoSite | 1.033 ± 0.171 | -0.368 ± 0.528 | 0.768 ± 0.197 | 0.695 ± 0.459 | 1.353 ± 1.028 |
| 1000 | 1000 | DRLearner_PooledWithSite | 1.031 ± 0.171 | -0.370 ± 0.526 | 0.768 ± 0.198 | 0.699 ± 0.470 | 1.348 ± 1.029 |
| 1000 | 1000 | EntropyBalancing | 0.979 ± 0.208 | -0.556 ± 0.692 | 0.712 ± 0.237 | 0.927 ± 0.588 | 1.656 ± 1.223 |
| 1000 | 1000 | IPWTransport | 0.978 ± 0.206 | -0.560 ± 0.697 | 0.711 ± 0.237 | 0.926 ± 0.582 | 1.659 ± 1.209 |
| 1000 | 1000 | OutcomeModelTransport | 0.992 ± 0.210 | -0.543 ± 0.676 | 0.723 ± 0.227 | 0.895 ± 0.599 | 1.619 ± 1.260 |
| 1000 | 1000 | ProposedA | 1.466 ± 0.187 | 0.396 ± 0.730 | 0.563 ± 0.041 | 0.895 ± 0.333 | 2.217 ± 0.770 |
| 1000 | 1000 | ProposedA_FullyJoint | 1.467 ± 0.177 | 0.402 ± 0.735 | 0.564 ± 0.041 | 0.877 ± 0.315 | 2.272 ± 0.721 |
| 1000 | 1000 | ProposedA_JointProxy | 1.472 ± 0.180 | 0.410 ± 0.744 | 0.564 ± 0.042 | 0.882 ± 0.320 | 2.268 ± 0.756 |
| 1000 | 1000 | ProposedA_Together | 1.464 ± 0.187 | 0.395 ± 0.731 | 0.564 ± 0.042 | 0.894 ± 0.320 | 2.225 ± 0.777 |
| 1000 | 1000 | ProposedB_LinearStepB | 1.483 ± 0.208 | 0.413 ± 0.785 | 0.568 ± 0.042 | 0.895 ± 0.347 | 2.300 ± 0.817 |
| 1000 | 1000 | ProposedB_SourceDR | 1.412 ± 0.417 | -0.740 ± 0.751 | 0.380 ± 0.123 | 1.228 ± 0.681 | 2.716 ± 1.531 |
| 1000 | 1000 | ProxyOnly | 1.167 ± 0.272 | -0.554 ± 1.046 | 0.356 ± 0.135 | 1.065 ± 0.525 | 2.242 ± 0.912 |
| 1000 | 1000 | TargetOnlyDR | 1.476 ± 0.188 | 0.410 ± 0.803 | 0.574 ± 0.034 | 0.901 ± 0.306 | 2.340 ± 0.790 |

### Extended Targeting Metrics

| m0 | m1 | Method | Top-10% Captured | Top-20% Captured | Top-30% Ratio (↑) |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 6.174 ± 1.213 | 4.999 ± 1.197 | 0.796 ± 0.093 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 6.911 ± 1.487 | 5.561 ± 1.470 | 0.871 ± 0.093 |
| 100 | 0 | IPWTransport | 6.945 ± 1.427 | 5.573 ± 1.454 | 0.877 ± 0.089 |
| 100 | 0 | OutcomeModelTransport | 6.942 ± 1.445 | 5.584 ± 1.441 | 0.879 ± 0.088 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 100 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 100 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 4.995 ± 1.529 | 4.102 ± 1.535 | 0.630 ± 0.130 |
| 100 | 0 | ProxyOnly | 4.294 ± 1.474 | 3.462 ± 1.463 | 0.526 ± 0.186 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 5.144 ± 2.065 | 4.059 ± 1.990 | 0.595 ± 0.289 |
| 100 | 100 | AnchorPlugin | 5.575 ± 2.095 | 4.358 ± 2.067 | 0.672 ± 0.275 |
| 100 | 100 | DRLearner_PooledNoSite | 6.297 ± 2.115 | 4.904 ± 2.031 | 0.811 ± 0.196 |
| 100 | 100 | DRLearner_PooledWithSite | 6.304 ± 2.110 | 4.904 ± 2.027 | 0.811 ± 0.194 |
| 100 | 100 | EntropyBalancing | 6.226 ± 2.155 | 4.830 ± 2.073 | 0.798 ± 0.213 |
| 100 | 100 | IPWTransport | 6.248 ± 2.169 | 4.865 ± 2.042 | 0.804 ± 0.203 |
| 100 | 100 | OutcomeModelTransport | 6.258 ± 2.119 | 4.874 ± 2.029 | 0.808 ± 0.197 |
| 100 | 100 | ProposedA | 5.292 ± 2.124 | 4.140 ± 2.015 | 0.634 ± 0.257 |
| 100 | 100 | ProposedA_FullyJoint | 5.358 ± 2.242 | 4.141 ± 2.043 | 0.616 ± 0.307 |
| 100 | 100 | ProposedA_JointProxy | 5.298 ± 2.155 | 4.111 ± 2.026 | 0.616 ± 0.263 |
| 100 | 100 | ProposedA_Together | 5.373 ± 2.300 | 4.211 ± 2.109 | 0.608 ± 0.350 |
| 100 | 100 | ProposedB_LinearStepB | 5.416 ± 2.243 | 4.169 ± 2.111 | 0.623 ± 0.300 |
| 100 | 100 | ProposedB_SourceDR | 4.367 ± 2.021 | 3.347 ± 1.995 | 0.419 ± 0.427 |
| 100 | 100 | ProxyOnly | 3.601 ± 2.202 | 2.878 ± 2.076 | 0.327 ± 0.489 |
| 100 | 100 | TargetOnlyDR | 5.122 ± 2.245 | 3.986 ± 2.129 | 0.555 ± 0.326 |
| 100 | 500 | AnchorOnly | 5.666 ± 1.713 | 4.493 ± 1.590 | 0.713 ± 0.128 |
| 100 | 500 | AnchorPlugin | 5.718 ± 1.910 | 4.598 ± 1.713 | 0.732 ± 0.154 |
| 100 | 500 | DRLearner_PooledNoSite | 6.554 ± 2.014 | 5.207 ± 1.794 | 0.856 ± 0.132 |
| 100 | 500 | DRLearner_PooledWithSite | 6.524 ± 2.029 | 5.184 ± 1.795 | 0.851 ± 0.138 |
| 100 | 500 | EntropyBalancing | 6.397 ± 2.053 | 5.069 ± 1.776 | 0.826 ± 0.157 |
| 100 | 500 | IPWTransport | 6.447 ± 2.036 | 5.123 ± 1.777 | 0.839 ± 0.149 |
| 100 | 500 | OutcomeModelTransport | 6.465 ± 2.039 | 5.140 ± 1.802 | 0.842 ± 0.148 |
| 100 | 500 | ProposedA | 5.702 ± 1.752 | 4.463 ± 1.586 | 0.700 ± 0.129 |
| 100 | 500 | ProposedA_FullyJoint | 3.804 ± 1.392 | 3.386 ± 1.469 | 0.538 ± 0.191 |
| 100 | 500 | ProposedA_JointProxy | 5.647 ± 1.665 | 4.463 ± 1.599 | 0.707 ± 0.130 |
| 100 | 500 | ProposedA_Together | 4.358 ± 1.519 | 3.674 ± 1.486 | 0.587 ± 0.151 |
| 100 | 500 | ProposedB_LinearStepB | 5.677 ± 1.670 | 4.507 ± 1.578 | 0.708 ± 0.126 |
| 100 | 500 | ProposedB_SourceDR | 4.259 ± 1.640 | 3.385 ± 1.446 | 0.526 ± 0.175 |
| 100 | 500 | ProxyOnly | 2.939 ± 1.975 | 2.317 ± 1.691 | 0.297 ± 0.356 |
| 100 | 500 | TargetOnlyDR | 4.890 ± 1.781 | 3.954 ± 1.613 | 0.613 ± 0.181 |
| 100 | 1000 | AnchorOnly | 5.295 ± 1.515 | 4.117 ± 1.256 | 0.684 ± 0.119 |
| 100 | 1000 | AnchorPlugin | 5.736 ± 1.663 | 4.555 ± 1.430 | 0.761 ± 0.136 |
| 100 | 1000 | DRLearner_PooledNoSite | 6.448 ± 1.538 | 5.086 ± 1.347 | 0.881 ± 0.113 |
| 100 | 1000 | DRLearner_PooledWithSite | 6.386 ± 1.579 | 5.048 ± 1.365 | 0.873 ± 0.122 |
| 100 | 1000 | EntropyBalancing | 6.293 ± 1.604 | 4.975 ± 1.371 | 0.860 ± 0.133 |
| 100 | 1000 | IPWTransport | 6.296 ± 1.605 | 4.974 ± 1.379 | 0.860 ± 0.140 |
| 100 | 1000 | OutcomeModelTransport | 6.285 ± 1.590 | 4.968 ± 1.375 | 0.858 ± 0.141 |
| 100 | 1000 | ProposedA | 5.261 ± 1.494 | 4.136 ± 1.250 | 0.677 ± 0.119 |
| 100 | 1000 | ProposedA_FullyJoint | 2.924 ± 1.211 | 2.790 ± 1.197 | 0.479 ± 0.165 |
| 100 | 1000 | ProposedA_JointProxy | 5.246 ± 1.410 | 4.128 ± 1.216 | 0.679 ± 0.112 |
| 100 | 1000 | ProposedA_Together | 3.534 ± 1.304 | 3.084 ± 1.095 | 0.515 ± 0.144 |
| 100 | 1000 | ProposedB_LinearStepB | 5.261 ± 1.488 | 4.130 ± 1.230 | 0.684 ± 0.121 |
| 100 | 1000 | ProposedB_SourceDR | 4.406 ± 1.344 | 3.429 ± 1.231 | 0.574 ± 0.154 |
| 100 | 1000 | ProxyOnly | 2.698 ± 1.685 | 2.122 ± 1.547 | 0.297 ± 0.306 |
| 100 | 1000 | TargetOnlyDR | 3.762 ± 1.201 | 3.299 ± 1.225 | 0.533 ± 0.158 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 6.273 ± 1.492 | 4.987 ± 1.483 | 0.768 ± 0.147 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 6.599 ± 2.013 | 5.276 ± 1.806 | 0.815 ± 0.219 |
| 500 | 0 | IPWTransport | 6.596 ± 2.021 | 5.284 ± 1.799 | 0.814 ± 0.218 |
| 500 | 0 | OutcomeModelTransport | 6.620 ± 2.004 | 5.300 ± 1.806 | 0.819 ± 0.211 |
| 500 | 0 | ProposedA | N/A | N/A | N/A |
| 500 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 500 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 500 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 4.788 ± 1.984 | 3.765 ± 1.715 | 0.556 ± 0.239 |
| 500 | 0 | ProxyOnly | 4.814 ± 1.819 | 3.848 ± 1.624 | 0.574 ± 0.220 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 4.406 ± 1.633 | 3.564 ± 1.499 | 0.562 ± 0.163 |
| 500 | 100 | AnchorPlugin | 5.580 ± 1.728 | 4.306 ± 1.597 | 0.716 ± 0.137 |
| 500 | 100 | DRLearner_PooledNoSite | 6.169 ± 1.777 | 4.824 ± 1.572 | 0.818 ± 0.130 |
| 500 | 100 | DRLearner_PooledWithSite | 6.223 ± 1.798 | 4.857 ± 1.591 | 0.825 ± 0.125 |
| 500 | 100 | EntropyBalancing | 6.103 ± 1.745 | 4.798 ± 1.560 | 0.811 ± 0.136 |
| 500 | 100 | IPWTransport | 6.111 ± 1.749 | 4.797 ± 1.562 | 0.811 ± 0.134 |
| 500 | 100 | OutcomeModelTransport | 6.116 ± 1.763 | 4.792 ± 1.576 | 0.811 ± 0.136 |
| 500 | 100 | ProposedA | 5.617 ± 1.992 | 4.298 ± 1.695 | 0.679 ± 0.134 |
| 500 | 100 | ProposedA_FullyJoint | 3.538 ± 1.810 | 3.142 ± 1.665 | 0.504 ± 0.178 |
| 500 | 100 | ProposedA_JointProxy | 5.670 ± 1.973 | 4.315 ± 1.716 | 0.687 ± 0.138 |
| 500 | 100 | ProposedA_Together | 4.131 ± 1.617 | 3.456 ± 1.575 | 0.548 ± 0.164 |
| 500 | 100 | ProposedB_LinearStepB | 5.481 ± 1.919 | 4.217 ± 1.714 | 0.665 ± 0.154 |
| 500 | 100 | ProposedB_SourceDR | 4.122 ± 1.521 | 3.151 ± 1.358 | 0.503 ± 0.168 |
| 500 | 100 | ProxyOnly | 4.427 ± 1.674 | 3.353 ± 1.525 | 0.516 ± 0.200 |
| 500 | 100 | TargetOnlyDR | 4.246 ± 1.745 | 3.496 ± 1.624 | 0.551 ± 0.178 |
| 500 | 500 | AnchorOnly | 5.615 ± 1.736 | 4.378 ± 1.534 | 0.730 ± 0.116 |
| 500 | 500 | AnchorPlugin | 5.562 ± 1.746 | 4.433 ± 1.543 | 0.761 ± 0.135 |
| 500 | 500 | DRLearner_PooledNoSite | 6.212 ± 1.675 | 4.944 ± 1.539 | 0.867 ± 0.090 |
| 500 | 500 | DRLearner_PooledWithSite | 6.217 ± 1.678 | 4.946 ± 1.542 | 0.867 ± 0.090 |
| 500 | 500 | EntropyBalancing | 6.080 ± 1.715 | 4.857 ± 1.539 | 0.848 ± 0.102 |
| 500 | 500 | IPWTransport | 6.085 ± 1.720 | 4.859 ± 1.540 | 0.850 ± 0.101 |
| 500 | 500 | OutcomeModelTransport | 6.084 ± 1.715 | 4.866 ± 1.542 | 0.851 ± 0.103 |
| 500 | 500 | ProposedA | 5.629 ± 1.720 | 4.397 ± 1.525 | 0.735 ± 0.101 |
| 500 | 500 | ProposedA_FullyJoint | 5.611 ± 1.688 | 4.374 ± 1.484 | 0.734 ± 0.094 |
| 500 | 500 | ProposedA_JointProxy | 5.622 ± 1.698 | 4.340 ± 1.507 | 0.733 ± 0.098 |
| 500 | 500 | ProposedA_Together | 5.656 ± 1.691 | 4.388 ± 1.515 | 0.735 ± 0.101 |
| 500 | 500 | ProposedB_LinearStepB | 5.618 ± 1.675 | 4.364 ± 1.486 | 0.737 ± 0.094 |
| 500 | 500 | ProposedB_SourceDR | 4.475 ± 1.610 | 3.517 ± 1.445 | 0.586 ± 0.156 |
| 500 | 500 | ProxyOnly | 4.183 ± 1.920 | 3.318 ± 1.628 | 0.560 ± 0.193 |
| 500 | 500 | TargetOnlyDR | 5.633 ± 1.645 | 4.334 ± 1.449 | 0.736 ± 0.103 |
| 500 | 1000 | AnchorOnly | 5.920 ± 1.815 | 4.717 ± 1.730 | 0.708 ± 0.138 |
| 500 | 1000 | AnchorPlugin | 6.208 ± 1.833 | 4.986 ± 1.692 | 0.770 ± 0.115 |
| 500 | 1000 | DRLearner_PooledNoSite | 6.981 ± 1.831 | 5.590 ± 1.712 | 0.875 ± 0.089 |
| 500 | 1000 | DRLearner_PooledWithSite | 6.967 ± 1.827 | 5.566 ± 1.704 | 0.873 ± 0.089 |
| 500 | 1000 | EntropyBalancing | 6.672 ± 1.789 | 5.404 ± 1.682 | 0.844 ± 0.113 |
| 500 | 1000 | IPWTransport | 6.695 ± 1.786 | 5.412 ± 1.685 | 0.844 ± 0.111 |
| 500 | 1000 | OutcomeModelTransport | 6.778 ± 1.800 | 5.434 ± 1.689 | 0.852 ± 0.102 |
| 500 | 1000 | ProposedA | 5.878 ± 1.741 | 4.705 ± 1.676 | 0.699 ± 0.139 |
| 500 | 1000 | ProposedA_FullyJoint | 5.857 ± 1.771 | 4.566 ± 1.647 | 0.677 ± 0.150 |
| 500 | 1000 | ProposedA_JointProxy | 5.831 ± 1.736 | 4.708 ± 1.635 | 0.703 ± 0.144 |
| 500 | 1000 | ProposedA_Together | 5.900 ± 1.791 | 4.629 ± 1.686 | 0.684 ± 0.159 |
| 500 | 1000 | ProposedB_LinearStepB | 5.876 ± 1.746 | 4.706 ± 1.641 | 0.704 ± 0.138 |
| 500 | 1000 | ProposedB_SourceDR | 4.655 ± 1.649 | 3.694 ± 1.564 | 0.528 ± 0.202 |
| 500 | 1000 | ProxyOnly | 4.514 ± 1.815 | 3.622 ± 1.672 | 0.499 ± 0.270 |
| 500 | 1000 | TargetOnlyDR | 5.912 ± 1.767 | 4.764 ± 1.703 | 0.703 ± 0.156 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 7.188 ± 1.519 | 5.983 ± 1.401 | 0.840 ± 0.070 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 7.650 ± 1.529 | 6.324 ± 1.422 | 0.891 ± 0.071 |
| 1000 | 0 | IPWTransport | 7.644 ± 1.517 | 6.319 ± 1.424 | 0.890 ± 0.072 |
| 1000 | 0 | OutcomeModelTransport | 7.654 ± 1.488 | 6.327 ± 1.386 | 0.895 ± 0.065 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_FullyJoint | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_JointProxy | N/A | N/A | N/A |
| 1000 | 0 | ProposedA_Together | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 5.661 ± 1.441 | 4.662 ± 1.443 | 0.645 ± 0.098 |
| 1000 | 0 | ProxyOnly | 5.751 ± 1.504 | 4.815 ± 1.448 | 0.676 ± 0.094 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 4.188 ± 1.586 | 3.638 ± 1.519 | 0.549 ± 0.181 |
| 1000 | 100 | AnchorPlugin | 6.297 ± 2.000 | 5.014 ± 1.753 | 0.760 ± 0.161 |
| 1000 | 100 | DRLearner_PooledNoSite | 6.695 ± 2.252 | 5.334 ± 1.906 | 0.818 ± 0.184 |
| 1000 | 100 | DRLearner_PooledWithSite | 6.823 ± 2.183 | 5.431 ± 1.862 | 0.830 ± 0.171 |
| 1000 | 100 | EntropyBalancing | 6.589 ± 2.298 | 5.233 ± 1.961 | 0.801 ± 0.192 |
| 1000 | 100 | IPWTransport | 6.590 ± 2.299 | 5.231 ± 1.964 | 0.801 ± 0.192 |
| 1000 | 100 | OutcomeModelTransport | 6.628 ± 2.285 | 5.289 ± 1.922 | 0.809 ± 0.191 |
| 1000 | 100 | ProposedA | 6.011 ± 2.042 | 4.770 ± 1.797 | 0.691 ± 0.131 |
| 1000 | 100 | ProposedA_FullyJoint | 3.612 ± 1.682 | 3.302 ± 1.618 | 0.501 ± 0.207 |
| 1000 | 100 | ProposedA_JointProxy | 6.050 ± 2.130 | 4.782 ± 1.805 | 0.689 ± 0.129 |
| 1000 | 100 | ProposedA_Together | 4.116 ± 1.581 | 3.611 ± 1.534 | 0.531 ± 0.197 |
| 1000 | 100 | ProposedB_LinearStepB | 5.549 ± 2.112 | 4.512 ± 1.755 | 0.645 ± 0.191 |
| 1000 | 100 | ProposedB_SourceDR | 4.599 ± 1.959 | 3.622 ± 1.807 | 0.532 ± 0.246 |
| 1000 | 100 | ProxyOnly | 4.991 ± 1.991 | 4.028 ± 1.669 | 0.590 ± 0.193 |
| 1000 | 100 | TargetOnlyDR | 3.895 ± 1.634 | 3.684 ± 1.590 | 0.556 ± 0.180 |
| 1000 | 500 | AnchorOnly | 7.013 ± 1.420 | 5.736 ± 1.239 | 0.766 ± 0.066 |
| 1000 | 500 | AnchorPlugin | 6.874 ± 1.617 | 5.623 ± 1.349 | 0.772 ± 0.148 |
| 1000 | 500 | DRLearner_PooledNoSite | 7.542 ± 1.622 | 6.172 ± 1.433 | 0.850 ± 0.163 |
| 1000 | 500 | DRLearner_PooledWithSite | 7.630 ± 1.547 | 6.219 ± 1.420 | 0.856 ± 0.157 |
| 1000 | 500 | EntropyBalancing | 7.349 ± 1.791 | 6.014 ± 1.526 | 0.829 ± 0.186 |
| 1000 | 500 | IPWTransport | 7.331 ± 1.823 | 6.018 ± 1.509 | 0.827 ± 0.187 |
| 1000 | 500 | OutcomeModelTransport | 7.325 ± 1.844 | 6.034 ± 1.530 | 0.832 ± 0.185 |
| 1000 | 500 | ProposedA | 7.123 ± 1.555 | 5.799 ± 1.243 | 0.778 ± 0.060 |
| 1000 | 500 | ProposedA_FullyJoint | 7.061 ± 1.523 | 5.699 ± 1.234 | 0.767 ± 0.074 |
| 1000 | 500 | ProposedA_JointProxy | 7.141 ± 1.515 | 5.786 ± 1.239 | 0.783 ± 0.052 |
| 1000 | 500 | ProposedA_Together | 7.059 ± 1.464 | 5.752 ± 1.252 | 0.769 ± 0.069 |
| 1000 | 500 | ProposedB_LinearStepB | 7.157 ± 1.521 | 5.852 ± 1.291 | 0.784 ± 0.053 |
| 1000 | 500 | ProposedB_SourceDR | 5.299 ± 2.229 | 4.413 ± 1.670 | 0.619 ± 0.186 |
| 1000 | 500 | ProxyOnly | 5.551 ± 1.442 | 4.554 ± 1.351 | 0.610 ± 0.176 |
| 1000 | 500 | TargetOnlyDR | 7.182 ± 1.454 | 5.829 ± 1.263 | 0.777 ± 0.081 |
| 1000 | 1000 | AnchorOnly | 5.165 ± 1.342 | 3.946 ± 1.158 | 0.693 ± 0.083 |
| 1000 | 1000 | AnchorPlugin | 5.045 ± 1.668 | 3.913 ± 1.415 | 0.710 ± 0.219 |
| 1000 | 1000 | DRLearner_PooledNoSite | 5.858 ± 1.549 | 4.521 ± 1.352 | 0.827 ± 0.180 |
| 1000 | 1000 | DRLearner_PooledWithSite | 5.854 ± 1.548 | 4.525 ± 1.349 | 0.827 ± 0.181 |
| 1000 | 1000 | EntropyBalancing | 5.421 ± 1.877 | 4.230 ± 1.596 | 0.772 ± 0.251 |
| 1000 | 1000 | IPWTransport | 5.411 ± 1.899 | 4.227 ± 1.604 | 0.772 ± 0.252 |
| 1000 | 1000 | OutcomeModelTransport | 5.523 ± 1.808 | 4.295 ± 1.527 | 0.785 ± 0.231 |
| 1000 | 1000 | ProposedA | 5.099 ± 1.370 | 3.946 ± 1.134 | 0.699 ± 0.067 |
| 1000 | 1000 | ProposedA_FullyJoint | 5.161 ± 1.429 | 3.967 ± 1.146 | 0.691 ± 0.067 |
| 1000 | 1000 | ProposedA_JointProxy | 5.133 ± 1.378 | 3.961 ± 1.159 | 0.695 ± 0.063 |
| 1000 | 1000 | ProposedA_Together | 5.151 ± 1.406 | 3.974 ± 1.142 | 0.702 ± 0.065 |
| 1000 | 1000 | ProposedB_LinearStepB | 5.135 ± 1.377 | 3.964 ± 1.149 | 0.694 ± 0.075 |
| 1000 | 1000 | ProposedB_SourceDR | 3.948 ± 1.578 | 2.970 ± 1.343 | 0.517 ± 0.185 |
| 1000 | 1000 | ProxyOnly | 3.569 ± 1.615 | 2.762 ± 1.435 | 0.491 ± 0.235 |
| 1000 | 1000 | TargetOnlyDR | 5.214 ± 1.338 | 3.966 ± 1.154 | 0.705 ± 0.076 |

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

1. **Best overall PEHE:** DRLearner_PooledNoSite achieves lowest average PEHE (2.022)
2. **Proposed vs ProxyOnly:** Proposed reduces PEHE by 23.3% on average
3. **IPWTransport:** PEHE degrades as m0 increases
4. **Best ranking:** DRLearner_PooledNoSite achieves highest Spearman correlation (0.876)

---

## Appendix: Configuration

```python
sweep_param = 'm0'
sweep_values = [100, 500, 1000]
base_scenario = {'n_proxy_total': 20000, 'C_sources': 10, 'nontransfer_scale': 0.1, 'use_fair_dgp': True, 'overlap_lambda': 0.25, 'intercept_drift_scale': 0.5}
```

