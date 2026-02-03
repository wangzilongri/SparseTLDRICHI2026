# Target budget 2D grid sweep (m₀ × m₁)

**Benchmark ID:** `gold_sweep`

**Generated:** 2026-02-03 02:06

---

## 1. Motivation

**Research Question:** How does the amount of target data (m₀ placebo, m₁ treated) jointly affect estimator performance?

**Why This Matters:**
- In clinical trials, placebo/control arms are expensive and ethically constrained
- The amount of treated data in target varies: from 0 (external control) to balanced RCT
- This 2D sweep shows the full landscape of performance vs data availability
- m₁ = 0 row shows "disconnected target" scenario (only Option B feasible)
- m₁ > 0 rows show "connected target" scenarios (Option A also feasible)

**Expected Behavior:**
- **ProxyOnly** should be insensitive to both m₀ and m₁ (uses only source data)
- **AnchorOnly/ProposedB** should improve with m₀ but be insensitive to m₁
- **ProposedA** should improve with both m₀ AND m₁
- At m₁ = 0, ProposedA is infeasible (NaN)
- At large m₁, ProposedA should outperform ProposedB

---

## 2. Simulation Setup

**Data Generating Process:**

The simulation generates data from a multi-site RCT setting where treatment effects
differ between source sites and the target population.

**Fixed Parameters:**
- **Covariates:** $X \in \mathbb{R}^{30}$
- **Source sites:** C = 10 sites with 2,000 total observations
- **Non-transfer component:** $\sigma_{\text{nontransfer}} = 0.3$ (moderate)

**What Varies (2D Grid):**
- **m₀** (target placebo): {25, 50, 100, 200}
- **m₁** (target treated): {0, 25, 50, 100}
- Total: 16 scenarios per method

### Parameter Summary

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Sweep param** | `m0` | [25, 50, 100, 200] |
| n_proxy_total | 2000 | Total source/proxy observations |
| C_sources | 10 | Number of source sites |
| nontransfer_scale | 0.3 | Scale of non-transferable component (σ) |

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
| **ProposedA** | ✓ | ✓ | Proposed (Option A): requires target treated |
| **ProposedB_LinearStepB** | ✓ | ✓ | Proposed (Option B): placebo-anchored with linear Step B |
| **ProposedB_SourceDR** | ✗ | ✗ | See documentation |
| **IPWTransport** | ✗ | ✗ | See documentation |
| **EntropyBalancing** | ✗ | ✗ | See documentation |
| **OutcomeModelTransport** | ✗ | ✗ | See documentation |
| **DRLearner_PooledWithSite** | ✗ | ✗ | See documentation |
| **DRLearner_PooledNoSite** | ✗ | ✗ | See documentation |

---

## 5. Experiment Summary

- **Sweep parameter:** `m0` ∈ [25, 50, 100, 200]
- **Monte Carlo replicates:** 100 per scenario
- **Methods evaluated:** 12
- **Total runs:** 19200

---

## 6. Results

### Best Methods (averaged across sweep)

| Metric | Best Method | Value | Direction |
|--------|-------------|-------|----------|
| PEHE | **DRLearner_PooledWithSite** | 2.6377 | ↓ lower |
| ATE Error | **ProposedA** | 0.2166 | ↓ lower |
| Spearman ρ | **ProxyOnly** | 0.2464 | ↑ higher |
| Kendall τ | **ProxyOnly** | 0.1679 | ↑ higher |
| Qini AUC | **ProxyOnly** | 0.2643 | ↑ higher |
| Top-10% Ratio | **ProxyOnly** | -6.8097 | ↑ higher |
| Top-20% Ratio | **ProposedB_LinearStepB** | -75.1582 | ↑ higher |
| Calibration R² | **AnchorOnly** | 0.0447 | ↑ higher |
| CATE ECE | **DRLearner_PooledWithSite** | 0.6016 | ↓ lower |
| Policy Value | **ProposedB_SourceDR** | 0.9226 | ↑ higher |
| Policy Regret | **DRLearner_PooledWithSite** | 0.1821 | ↓ lower |

### Core Metrics

| m0 | m1 | Method | PEHE (↓) | ATE Err (↓) | Spearman (↑) | Qini (↑) |
|---|---|---|---|---|---|
| 25 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 25 | 0 | AnchorPlugin | 6.140 ± 3.345 | 3.995 ± 3.733 | 0.525 ± 0.148 | 0.540 ± 0.150 |
| 25 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 25 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 25 | 0 | EntropyBalancing | 7.574 ± 3.723 | 5.476 ± 4.081 | 0.542 ± 0.185 | 0.556 ± 0.188 |
| 25 | 0 | IPWTransport | 5.271 ± 3.417 | 3.694 ± 3.626 | 0.730 ± 0.144 | 0.742 ± 0.144 |
| 25 | 0 | OutcomeModelTransport | 5.268 ± 3.421 | 3.686 ± 3.634 | 0.730 ± 0.144 | 0.742 ± 0.144 |
| 25 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 25 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 25 | 0 | ProposedB_SourceDR | 6.957 ± 3.555 | 4.661 ± 4.163 | 0.392 ± 0.145 | 0.406 ± 0.147 |
| 25 | 0 | ProxyOnly | 7.481 ± 3.766 | 5.290 ± 4.364 | 0.299 ± 0.130 | 0.312 ± 0.128 |
| 25 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 25 | 25 | AnchorOnly | 4.626 ± 0.987 | 0.749 ± 0.539 | 0.423 ± 0.142 | 0.437 ± 0.145 |
| 25 | 25 | AnchorPlugin | 6.319 ± 2.939 | 4.203 ± 3.529 | 0.529 ± 0.144 | 0.545 ± 0.145 |
| 25 | 25 | DRLearner_PooledNoSite | 3.648 ± 1.384 | 1.619 ± 1.344 | 0.757 ± 0.128 | 0.770 ± 0.126 |
| 25 | 25 | DRLearner_PooledWithSite | 3.658 ± 1.380 | 1.639 ± 1.349 | 0.758 ± 0.128 | 0.771 ± 0.125 |
| 25 | 25 | EntropyBalancing | 7.192 ± 4.302 | 5.065 ± 4.804 | 0.561 ± 0.181 | 0.577 ± 0.183 |
| 25 | 25 | IPWTransport | 5.296 ± 2.954 | 3.846 ± 3.249 | 0.742 ± 0.136 | 0.755 ± 0.134 |
| 25 | 25 | OutcomeModelTransport | 5.294 ± 2.958 | 3.841 ± 3.253 | 0.742 ± 0.137 | 0.755 ± 0.134 |
| 25 | 25 | ProposedA | 4.311 ± 0.807 | 0.645 ± 0.493 | 0.499 ± 0.110 | 0.515 ± 0.110 |
| 25 | 25 | ProposedB_LinearStepB | 4.574 ± 0.960 | 0.740 ± 0.554 | 0.426 ± 0.140 | 0.440 ± 0.143 |
| 25 | 25 | ProposedB_SourceDR | 7.128 ± 3.340 | 4.824 ± 4.127 | 0.421 ± 0.129 | 0.434 ± 0.131 |
| 25 | 25 | ProxyOnly | 7.841 ± 4.152 | 5.650 ± 4.839 | 0.293 ± 0.145 | 0.305 ± 0.143 |
| 25 | 25 | TargetOnlyDR | 4.358 ± 0.836 | 0.657 ± 0.426 | 0.478 ± 0.113 | 0.494 ± 0.114 |
| 25 | 50 | AnchorOnly | 4.261 ± 0.853 | 0.516 ± 0.352 | 0.503 ± 0.105 | 0.519 ± 0.105 |
| 25 | 50 | AnchorPlugin | 6.704 ± 3.516 | 4.695 ± 4.110 | 0.504 ± 0.128 | 0.522 ± 0.129 |
| 25 | 50 | DRLearner_PooledNoSite | 3.342 ± 1.288 | 1.092 ± 1.134 | 0.760 ± 0.128 | 0.773 ± 0.125 |
| 25 | 50 | DRLearner_PooledWithSite | 3.359 ± 1.303 | 1.132 ± 1.162 | 0.760 ± 0.128 | 0.773 ± 0.125 |
| 25 | 50 | EntropyBalancing | 7.252 ± 4.287 | 5.239 ± 4.752 | 0.574 ± 0.200 | 0.589 ± 0.201 |
| 25 | 50 | IPWTransport | 5.078 ± 3.073 | 3.570 ± 3.360 | 0.739 ± 0.141 | 0.753 ± 0.138 |
| 25 | 50 | OutcomeModelTransport | 5.080 ± 3.081 | 3.579 ± 3.362 | 0.739 ± 0.141 | 0.753 ± 0.138 |
| 25 | 50 | ProposedA | 4.045 ± 0.779 | 0.470 ± 0.344 | 0.575 ± 0.073 | 0.593 ± 0.072 |
| 25 | 50 | ProposedB_LinearStepB | 4.222 ± 0.857 | 0.514 ± 0.362 | 0.514 ± 0.103 | 0.530 ± 0.103 |
| 25 | 50 | ProposedB_SourceDR | 7.675 ± 4.034 | 5.465 ± 4.901 | 0.401 ± 0.138 | 0.417 ± 0.136 |
| 25 | 50 | ProxyOnly | 9.770 ± 5.721 | 7.813 ± 6.535 | 0.276 ± 0.137 | 0.289 ± 0.134 |
| 25 | 50 | TargetOnlyDR | 4.167 ± 0.792 | 0.601 ± 0.468 | 0.534 ± 0.088 | 0.550 ± 0.088 |
| 25 | 100 | AnchorOnly | 4.190 ± 0.844 | 0.516 ± 0.414 | 0.563 ± 0.100 | 0.579 ± 0.101 |
| 25 | 100 | AnchorPlugin | 6.104 ± 3.144 | 3.868 ± 3.594 | 0.507 ± 0.159 | 0.524 ± 0.154 |
| 25 | 100 | DRLearner_PooledNoSite | 3.195 ± 1.378 | 0.811 ± 0.783 | 0.760 ± 0.163 | 0.772 ± 0.162 |
| 25 | 100 | DRLearner_PooledWithSite | 3.210 ± 1.384 | 0.833 ± 0.795 | 0.759 ± 0.164 | 0.770 ± 0.162 |
| 25 | 100 | EntropyBalancing | 7.133 ± 4.103 | 4.992 ± 4.424 | 0.544 ± 0.222 | 0.563 ± 0.212 |
| 25 | 100 | IPWTransport | 5.185 ± 3.675 | 3.704 ± 3.826 | 0.731 ± 0.186 | 0.743 ± 0.185 |
| 25 | 100 | OutcomeModelTransport | 5.181 ± 3.645 | 3.704 ± 3.792 | 0.731 ± 0.185 | 0.743 ± 0.185 |
| 25 | 100 | ProposedA | 4.124 ± 0.766 | 0.488 ± 0.385 | 0.589 ± 0.097 | 0.604 ± 0.097 |
| 25 | 100 | ProposedB_LinearStepB | 4.153 ± 0.783 | 0.524 ± 0.393 | 0.569 ± 0.093 | 0.584 ± 0.093 |
| 25 | 100 | ProposedB_SourceDR | 6.883 ± 3.572 | 4.571 ± 4.134 | 0.406 ± 0.145 | 0.420 ± 0.146 |
| 25 | 100 | ProxyOnly | 13.721 ± 8.661 | 11.479 ± 9.734 | 0.246 ± 0.168 | 0.264 ± 0.156 |
| 25 | 100 | TargetOnlyDR | 4.346 ± 0.869 | 0.617 ± 0.450 | 0.543 ± 0.098 | 0.559 ± 0.098 |
| 50 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 50 | 0 | AnchorPlugin | 6.124 ± 3.314 | 4.140 ± 3.766 | 0.584 ± 0.152 | 0.601 ± 0.153 |
| 50 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 50 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 50 | 0 | EntropyBalancing | 7.569 ± 4.595 | 5.591 ± 5.003 | 0.563 ± 0.194 | 0.580 ± 0.191 |
| 50 | 0 | IPWTransport | 5.422 ± 3.044 | 3.901 ± 3.303 | 0.735 ± 0.165 | 0.748 ± 0.165 |
| 50 | 0 | OutcomeModelTransport | 5.417 ± 3.041 | 3.892 ± 3.301 | 0.735 ± 0.165 | 0.748 ± 0.164 |
| 50 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 50 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 50 | 0 | ProposedB_SourceDR | 7.579 ± 3.729 | 5.547 ± 4.322 | 0.418 ± 0.145 | 0.434 ± 0.143 |
| 50 | 0 | ProxyOnly | 7.303 ± 3.853 | 5.041 ± 4.497 | 0.370 ± 0.142 | 0.384 ± 0.145 |
| 50 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 50 | 25 | AnchorOnly | 5.479 ± 2.144 | 0.786 ± 0.700 | 0.367 ± 0.151 | 0.381 ± 0.156 |
| 50 | 25 | AnchorPlugin | 6.657 ± 4.109 | 4.841 ± 4.436 | 0.604 ± 0.136 | 0.621 ± 0.137 |
| 50 | 25 | DRLearner_PooledNoSite | 3.671 ± 2.096 | 1.484 ± 1.757 | 0.763 ± 0.147 | 0.776 ± 0.145 |
| 50 | 25 | DRLearner_PooledWithSite | 3.571 ± 1.948 | 1.323 ± 1.519 | 0.765 ± 0.146 | 0.777 ± 0.144 |
| 50 | 25 | EntropyBalancing | 7.841 ± 4.488 | 5.878 ± 4.972 | 0.575 ± 0.164 | 0.591 ± 0.164 |
| 50 | 25 | IPWTransport | 5.479 ± 4.065 | 3.956 ± 4.170 | 0.744 ± 0.161 | 0.757 ± 0.160 |
| 50 | 25 | OutcomeModelTransport | 5.466 ± 4.112 | 3.918 ± 4.234 | 0.744 ± 0.162 | 0.757 ± 0.161 |
| 50 | 25 | ProposedA | 4.546 ± 1.230 | 0.731 ± 0.501 | 0.515 ± 0.094 | 0.532 ± 0.093 |
| 50 | 25 | ProposedB_LinearStepB | 5.078 ± 1.874 | 0.672 ± 0.630 | 0.424 ± 0.143 | 0.438 ± 0.148 |
| 50 | 25 | ProposedB_SourceDR | 7.843 ± 4.044 | 5.750 ± 4.526 | 0.404 ± 0.153 | 0.421 ± 0.152 |
| 50 | 25 | ProxyOnly | 7.310 ± 4.065 | 5.066 ± 4.506 | 0.396 ± 0.138 | 0.412 ± 0.137 |
| 50 | 25 | TargetOnlyDR | 4.698 ± 1.316 | 0.741 ± 0.579 | 0.472 ± 0.104 | 0.488 ± 0.105 |
| 50 | 50 | AnchorOnly | 4.295 ± 0.946 | 0.502 ± 0.396 | 0.545 ± 0.112 | 0.561 ± 0.113 |
| 50 | 50 | AnchorPlugin | 6.270 ± 3.435 | 4.412 ± 3.948 | 0.607 ± 0.137 | 0.624 ± 0.137 |
| 50 | 50 | DRLearner_PooledNoSite | 3.446 ± 1.382 | 1.164 ± 1.020 | 0.757 ± 0.153 | 0.770 ± 0.151 |
| 50 | 50 | DRLearner_PooledWithSite | 3.445 ± 1.375 | 1.166 ± 1.018 | 0.757 ± 0.153 | 0.770 ± 0.152 |
| 50 | 50 | EntropyBalancing | 7.858 ± 4.584 | 5.941 ± 5.039 | 0.560 ± 0.192 | 0.577 ± 0.188 |
| 50 | 50 | IPWTransport | 5.792 ± 3.517 | 4.373 ± 3.784 | 0.731 ± 0.167 | 0.745 ± 0.166 |
| 50 | 50 | OutcomeModelTransport | 5.824 ± 3.527 | 4.417 ± 3.790 | 0.731 ± 0.167 | 0.745 ± 0.166 |
| 50 | 50 | ProposedA | 3.946 ± 0.668 | 0.381 ± 0.297 | 0.650 ± 0.065 | 0.666 ± 0.064 |
| 50 | 50 | ProposedB_LinearStepB | 4.195 ± 0.834 | 0.456 ± 0.372 | 0.566 ± 0.111 | 0.582 ± 0.113 |
| 50 | 50 | ProposedB_SourceDR | 7.570 ± 4.318 | 5.291 ± 5.096 | 0.405 ± 0.119 | 0.421 ± 0.122 |
| 50 | 50 | ProxyOnly | 7.331 ± 3.850 | 5.082 ± 4.616 | 0.415 ± 0.110 | 0.429 ± 0.113 |
| 50 | 50 | TargetOnlyDR | 4.023 ± 0.687 | 0.457 ± 0.341 | 0.614 ± 0.072 | 0.631 ± 0.072 |
| 50 | 100 | AnchorOnly | 3.914 ± 0.937 | 0.407 ± 0.317 | 0.639 ± 0.075 | 0.655 ± 0.075 |
| 50 | 100 | AnchorPlugin | 5.639 ± 2.484 | 3.524 ± 2.867 | 0.585 ± 0.141 | 0.602 ± 0.142 |
| 50 | 100 | DRLearner_PooledNoSite | 3.190 ± 1.487 | 0.652 ± 0.633 | 0.768 ± 0.136 | 0.780 ± 0.134 |
| 50 | 100 | DRLearner_PooledWithSite | 3.195 ± 1.492 | 0.676 ± 0.621 | 0.767 ± 0.137 | 0.780 ± 0.135 |
| 50 | 100 | EntropyBalancing | 7.395 ± 4.175 | 5.345 ± 4.434 | 0.558 ± 0.182 | 0.573 ± 0.184 |
| 50 | 100 | IPWTransport | 5.035 ± 3.214 | 3.343 ± 3.366 | 0.731 ± 0.162 | 0.744 ± 0.162 |
| 50 | 100 | OutcomeModelTransport | 5.051 ± 3.223 | 3.382 ± 3.359 | 0.731 ± 0.162 | 0.744 ± 0.162 |
| 50 | 100 | ProposedA | 3.794 ± 0.871 | 0.381 ± 0.225 | 0.685 ± 0.064 | 0.700 ± 0.063 |
| 50 | 100 | ProposedB_LinearStepB | 3.906 ± 0.952 | 0.396 ± 0.292 | 0.638 ± 0.089 | 0.653 ± 0.089 |
| 50 | 100 | ProposedB_SourceDR | 7.072 ± 3.031 | 4.818 ± 3.620 | 0.404 ± 0.131 | 0.419 ± 0.134 |
| 50 | 100 | ProxyOnly | 8.467 ± 4.487 | 6.275 ± 5.170 | 0.344 ± 0.130 | 0.357 ± 0.132 |
| 50 | 100 | TargetOnlyDR | 3.894 ± 0.858 | 0.444 ± 0.313 | 0.643 ± 0.068 | 0.659 ± 0.067 |
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 6.029 ± 2.682 | 4.233 ± 3.136 | 0.619 ± 0.127 | 0.634 ± 0.127 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 7.956 ± 4.173 | 6.015 ± 4.588 | 0.532 ± 0.186 | 0.548 ± 0.189 |
| 100 | 0 | IPWTransport | 5.402 ± 3.427 | 3.885 ± 3.523 | 0.713 ± 0.177 | 0.726 ± 0.176 |
| 100 | 0 | OutcomeModelTransport | 5.423 ± 3.445 | 3.913 ± 3.540 | 0.713 ± 0.177 | 0.726 ± 0.176 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 7.159 ± 3.867 | 4.842 ± 4.497 | 0.397 ± 0.125 | 0.412 ± 0.128 |
| 100 | 0 | ProxyOnly | 7.484 ± 3.391 | 5.444 ± 4.170 | 0.447 ± 0.131 | 0.462 ± 0.133 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 100 | 25 | AnchorOnly | 6.144 ± 2.361 | 0.820 ± 0.758 | 0.319 ± 0.144 | 0.332 ± 0.145 |
| 100 | 25 | AnchorPlugin | 5.959 ± 3.085 | 4.179 ± 3.589 | 0.636 ± 0.132 | 0.653 ± 0.131 |
| 100 | 25 | DRLearner_PooledNoSite | 3.293 ± 1.228 | 1.175 ± 1.023 | 0.775 ± 0.114 | 0.788 ± 0.110 |
| 100 | 25 | DRLearner_PooledWithSite | 3.145 ± 1.094 | 0.886 ± 0.719 | 0.779 ± 0.113 | 0.792 ± 0.109 |
| 100 | 25 | EntropyBalancing | 6.998 ± 3.461 | 5.114 ± 3.983 | 0.583 ± 0.156 | 0.599 ± 0.156 |
| 100 | 25 | IPWTransport | 5.275 ± 2.820 | 3.915 ± 3.101 | 0.753 ± 0.129 | 0.766 ± 0.126 |
| 100 | 25 | OutcomeModelTransport | 5.301 ± 2.929 | 3.949 ± 3.200 | 0.753 ± 0.130 | 0.766 ± 0.127 |
| 100 | 25 | ProposedA | 4.645 ± 1.245 | 0.504 ± 0.430 | 0.498 ± 0.116 | 0.513 ± 0.118 |
| 100 | 25 | ProposedB_LinearStepB | 5.343 ± 1.860 | 0.671 ± 0.595 | 0.410 ± 0.170 | 0.424 ± 0.172 |
| 100 | 25 | ProposedB_SourceDR | 7.306 ± 3.633 | 5.104 ± 4.362 | 0.411 ± 0.126 | 0.425 ± 0.129 |
| 100 | 25 | ProxyOnly | 6.506 ± 2.935 | 4.316 ± 3.510 | 0.464 ± 0.140 | 0.478 ± 0.143 |
| 100 | 25 | TargetOnlyDR | 5.052 ± 1.280 | 0.654 ± 0.516 | 0.419 ± 0.118 | 0.433 ± 0.120 |
| 100 | 50 | AnchorOnly | 4.570 ± 1.022 | 0.484 ± 0.325 | 0.480 ± 0.134 | 0.495 ± 0.136 |
| 100 | 50 | AnchorPlugin | 6.013 ± 2.563 | 4.344 ± 3.066 | 0.640 ± 0.124 | 0.656 ± 0.124 |
| 100 | 50 | DRLearner_PooledNoSite | 3.063 ± 1.143 | 0.903 ± 0.769 | 0.788 ± 0.129 | 0.800 ± 0.127 |
| 100 | 50 | DRLearner_PooledWithSite | 3.012 ± 1.113 | 0.802 ± 0.691 | 0.791 ± 0.127 | 0.802 ± 0.125 |
| 100 | 50 | EntropyBalancing | 8.095 ± 4.241 | 6.356 ± 4.808 | 0.594 ± 0.187 | 0.610 ± 0.188 |
| 100 | 50 | IPWTransport | 5.033 ± 3.143 | 3.610 ± 3.439 | 0.761 ± 0.148 | 0.773 ± 0.146 |
| 100 | 50 | OutcomeModelTransport | 5.034 ± 3.151 | 3.612 ± 3.445 | 0.761 ± 0.148 | 0.773 ± 0.146 |
| 100 | 50 | ProposedA | 3.745 ± 0.678 | 0.282 ± 0.222 | 0.679 ± 0.061 | 0.693 ± 0.060 |
| 100 | 50 | ProposedB_LinearStepB | 4.133 ± 0.832 | 0.396 ± 0.243 | 0.566 ± 0.110 | 0.582 ± 0.111 |
| 100 | 50 | ProposedB_SourceDR | 7.329 ± 2.924 | 5.284 ± 3.685 | 0.435 ± 0.142 | 0.451 ± 0.141 |
| 100 | 50 | ProxyOnly | 6.574 ± 2.622 | 4.468 ± 3.269 | 0.464 ± 0.122 | 0.479 ± 0.124 |
| 100 | 50 | TargetOnlyDR | 4.008 ± 0.833 | 0.406 ± 0.303 | 0.601 ± 0.082 | 0.617 ± 0.082 |
| 100 | 100 | AnchorOnly | 3.826 ± 0.731 | 0.328 ± 0.311 | 0.626 ± 0.101 | 0.643 ± 0.100 |
| 100 | 100 | AnchorPlugin | 5.767 ± 2.603 | 4.015 ± 3.201 | 0.633 ± 0.113 | 0.650 ± 0.111 |
| 100 | 100 | DRLearner_PooledNoSite | 2.956 ± 0.956 | 0.570 ± 0.486 | 0.779 ± 0.120 | 0.791 ± 0.118 |
| 100 | 100 | DRLearner_PooledWithSite | 2.956 ± 0.961 | 0.576 ± 0.488 | 0.779 ± 0.120 | 0.792 ± 0.118 |
| 100 | 100 | EntropyBalancing | 7.371 ± 3.344 | 5.479 ± 3.905 | 0.560 ± 0.159 | 0.576 ± 0.159 |
| 100 | 100 | IPWTransport | 4.884 ± 2.710 | 3.349 ± 3.050 | 0.738 ± 0.144 | 0.752 ± 0.143 |
| 100 | 100 | OutcomeModelTransport | 4.877 ± 2.689 | 3.356 ± 3.028 | 0.740 ± 0.143 | 0.753 ± 0.141 |
| 100 | 100 | ProposedA | 3.518 ± 0.661 | 0.248 ± 0.195 | 0.726 ± 0.050 | 0.741 ± 0.048 |
| 100 | 100 | ProposedB_LinearStepB | 3.660 ± 0.697 | 0.293 ± 0.215 | 0.672 ± 0.078 | 0.688 ± 0.077 |
| 100 | 100 | ProposedB_SourceDR | 7.533 ± 3.433 | 5.581 ± 4.206 | 0.432 ± 0.119 | 0.447 ± 0.122 |
| 100 | 100 | ProxyOnly | 6.530 ± 2.727 | 4.391 ± 3.500 | 0.463 ± 0.113 | 0.478 ± 0.115 |
| 100 | 100 | TargetOnlyDR | 3.603 ± 0.664 | 0.322 ± 0.294 | 0.688 ± 0.057 | 0.703 ± 0.056 |
| 200 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 200 | 0 | AnchorPlugin | 5.916 ± 2.684 | 4.181 ± 3.108 | 0.639 ± 0.125 | 0.656 ± 0.123 |
| 200 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 200 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 200 | 0 | EntropyBalancing | 6.863 ± 3.499 | 4.745 ± 4.025 | 0.586 ± 0.182 | 0.602 ± 0.183 |
| 200 | 0 | IPWTransport | 4.881 ± 3.005 | 3.327 ± 3.247 | 0.757 ± 0.135 | 0.770 ± 0.132 |
| 200 | 0 | OutcomeModelTransport | 4.855 ± 3.016 | 3.304 ± 3.246 | 0.757 ± 0.135 | 0.770 ± 0.132 |
| 200 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 200 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 200 | 0 | ProposedB_SourceDR | 7.301 ± 3.119 | 5.243 ± 3.732 | 0.422 ± 0.131 | 0.436 ± 0.134 |
| 200 | 0 | ProxyOnly | 6.966 ± 3.203 | 4.867 ± 3.932 | 0.491 ± 0.123 | 0.507 ± 0.124 |
| 200 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 200 | 25 | AnchorOnly | 7.691 ± 2.635 | 0.796 ± 0.588 | 0.265 ± 0.119 | 0.276 ± 0.122 |
| 200 | 25 | AnchorPlugin | 5.887 ± 2.934 | 4.107 ± 3.371 | 0.636 ± 0.125 | 0.652 ± 0.125 |
| 200 | 25 | DRLearner_PooledNoSite | 3.225 ± 1.310 | 0.953 ± 0.985 | 0.777 ± 0.137 | 0.789 ± 0.134 |
| 200 | 25 | DRLearner_PooledWithSite | 3.047 ± 1.179 | 0.606 ± 0.627 | 0.784 ± 0.132 | 0.796 ± 0.129 |
| 200 | 25 | EntropyBalancing | 7.546 ± 3.894 | 5.424 ± 4.499 | 0.566 ± 0.197 | 0.581 ± 0.197 |
| 200 | 25 | IPWTransport | 5.148 ± 3.726 | 3.613 ± 3.982 | 0.748 ± 0.159 | 0.761 ± 0.157 |
| 200 | 25 | OutcomeModelTransport | 5.135 ± 3.735 | 3.595 ± 3.993 | 0.748 ± 0.159 | 0.761 ± 0.157 |
| 200 | 25 | ProposedA | 5.677 ± 1.391 | 0.635 ± 0.442 | 0.440 ± 0.115 | 0.455 ± 0.116 |
| 200 | 25 | ProposedB_LinearStepB | 6.444 ± 2.107 | 0.584 ± 0.480 | 0.369 ± 0.149 | 0.382 ± 0.154 |
| 200 | 25 | ProposedB_SourceDR | 7.409 ± 3.684 | 5.347 ± 4.295 | 0.429 ± 0.133 | 0.444 ± 0.136 |
| 200 | 25 | ProxyOnly | 6.370 ± 2.771 | 4.096 ± 3.374 | 0.481 ± 0.124 | 0.498 ± 0.127 |
| 200 | 25 | TargetOnlyDR | 6.344 ± 1.291 | 0.657 ± 0.540 | 0.351 ± 0.098 | 0.364 ± 0.101 |
| 200 | 50 | AnchorOnly | 5.365 ± 1.843 | 0.437 ± 0.387 | 0.404 ± 0.145 | 0.417 ± 0.149 |
| 200 | 50 | AnchorPlugin | 5.754 ± 3.020 | 3.918 ± 3.557 | 0.636 ± 0.118 | 0.653 ± 0.117 |
| 200 | 50 | DRLearner_PooledNoSite | 3.036 ± 1.206 | 0.758 ± 0.635 | 0.779 ± 0.130 | 0.791 ± 0.127 |
| 200 | 50 | DRLearner_PooledWithSite | 2.954 ± 1.167 | 0.615 ± 0.493 | 0.784 ± 0.126 | 0.796 ± 0.123 |
| 200 | 50 | EntropyBalancing | 8.065 ± 5.231 | 6.320 ± 5.531 | 0.556 ± 0.176 | 0.571 ± 0.177 |
| 200 | 50 | IPWTransport | 5.352 ± 3.327 | 3.971 ± 3.542 | 0.737 ± 0.157 | 0.750 ± 0.155 |
| 200 | 50 | OutcomeModelTransport | 5.388 ± 3.366 | 4.027 ± 3.569 | 0.737 ± 0.157 | 0.750 ± 0.156 |
| 200 | 50 | ProposedA | 3.685 ± 0.738 | 0.277 ± 0.224 | 0.675 ± 0.071 | 0.691 ± 0.070 |
| 200 | 50 | ProposedB_LinearStepB | 4.549 ± 1.324 | 0.402 ± 0.294 | 0.503 ± 0.153 | 0.518 ± 0.155 |
| 200 | 50 | ProposedB_SourceDR | 6.803 ± 3.595 | 4.592 ± 4.201 | 0.420 ± 0.139 | 0.437 ± 0.135 |
| 200 | 50 | ProxyOnly | 6.279 ± 2.880 | 4.136 ± 3.499 | 0.499 ± 0.130 | 0.515 ± 0.132 |
| 200 | 50 | TargetOnlyDR | 4.469 ± 1.211 | 0.414 ± 0.290 | 0.526 ± 0.095 | 0.542 ± 0.094 |
| 200 | 100 | AnchorOnly | 3.991 ± 0.848 | 0.312 ± 0.234 | 0.588 ± 0.111 | 0.604 ± 0.111 |
| 200 | 100 | AnchorPlugin | 5.499 ± 2.300 | 3.804 ± 2.833 | 0.651 ± 0.111 | 0.667 ± 0.111 |
| 200 | 100 | DRLearner_PooledNoSite | 2.654 ± 0.803 | 0.368 ± 0.290 | 0.816 ± 0.097 | 0.828 ± 0.093 |
| 200 | 100 | DRLearner_PooledWithSite | 2.638 ± 0.801 | 0.350 ± 0.272 | 0.818 ± 0.096 | 0.830 ± 0.093 |
| 200 | 100 | EntropyBalancing | 7.527 ± 3.884 | 5.762 ± 4.354 | 0.589 ± 0.173 | 0.605 ± 0.174 |
| 200 | 100 | IPWTransport | 4.489 ± 2.229 | 3.048 ± 2.581 | 0.773 ± 0.120 | 0.786 ± 0.117 |
| 200 | 100 | OutcomeModelTransport | 4.464 ± 2.166 | 3.016 ± 2.523 | 0.774 ± 0.118 | 0.787 ± 0.116 |
| 200 | 100 | ProposedA | 3.398 ± 0.592 | 0.217 ± 0.149 | 0.740 ± 0.046 | 0.755 ± 0.044 |
| 200 | 100 | ProposedB_LinearStepB | 3.709 ± 0.723 | 0.271 ± 0.175 | 0.651 ± 0.104 | 0.667 ± 0.103 |
| 200 | 100 | ProposedB_SourceDR | 6.857 ± 3.013 | 4.794 ± 3.681 | 0.430 ± 0.124 | 0.446 ± 0.126 |
| 200 | 100 | ProxyOnly | 6.045 ± 2.240 | 3.937 ± 2.911 | 0.495 ± 0.123 | 0.510 ± 0.124 |
| 200 | 100 | TargetOnlyDR | 3.580 ± 0.660 | 0.283 ± 0.228 | 0.688 ± 0.060 | 0.704 ± 0.059 |

### Targeting / Ranking Metrics

| m0 | m1 | Method | Top-10% (↑) | Top-20% (↑) | Kendall (↑) |
|---|---|---|---|---|---|
| 25 | 0 | AnchorOnly | N/A | N/A | N/A |
| 25 | 0 | AnchorPlugin | 0.211 ± 1.566 | 0.476 ± 0.755 | 0.371 ± 0.112 |
| 25 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 25 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 25 | 0 | EntropyBalancing | 0.109 ± 2.913 | 0.523 ± 0.659 | 0.387 ± 0.141 |
| 25 | 0 | IPWTransport | 0.468 ± 1.921 | 0.740 ± 0.267 | 0.548 ± 0.126 |
| 25 | 0 | OutcomeModelTransport | 0.469 ± 1.921 | 0.740 ± 0.266 | 0.548 ± 0.127 |
| 25 | 0 | ProposedA | N/A | N/A | N/A |
| 25 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 25 | 0 | ProposedB_SourceDR | 0.029 ± 1.957 | 0.317 ± 0.884 | 0.271 ± 0.105 |
| 25 | 0 | ProxyOnly | -0.038 ± 1.747 | 0.167 ± 1.209 | 0.204 ± 0.091 |
| 25 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 25 | 25 | AnchorOnly | -0.580 ± 5.929 | 0.309 ± 0.870 | 0.292 ± 0.103 |
| 25 | 25 | AnchorPlugin | -0.159 ± 3.696 | 0.392 ± 1.015 | 0.373 ± 0.110 |
| 25 | 25 | DRLearner_PooledNoSite | 0.571 ± 1.114 | 0.736 ± 0.282 | 0.574 ± 0.118 |
| 25 | 25 | DRLearner_PooledWithSite | 0.571 ± 1.122 | 0.736 ± 0.284 | 0.574 ± 0.118 |
| 25 | 25 | EntropyBalancing | -0.069 ± 3.624 | 0.493 ± 0.627 | 0.401 ± 0.139 |
| 25 | 25 | IPWTransport | 0.521 ± 1.333 | 0.720 ± 0.299 | 0.559 ± 0.123 |
| 25 | 25 | OutcomeModelTransport | 0.522 ± 1.325 | 0.721 ± 0.299 | 0.559 ± 0.123 |
| 25 | 25 | ProposedA | -0.430 ± 5.375 | 0.357 ± 1.014 | 0.349 ± 0.083 |
| 25 | 25 | ProposedB_LinearStepB | -0.600 ± 6.083 | 0.307 ± 0.960 | 0.294 ± 0.101 |
| 25 | 25 | ProposedB_SourceDR | -0.591 ± 5.992 | 0.316 ± 0.885 | 0.291 ± 0.093 |
| 25 | 25 | ProxyOnly | -1.031 ± 7.309 | 0.117 ± 1.180 | 0.199 ± 0.101 |
| 25 | 25 | TargetOnlyDR | -0.455 ± 5.455 | 0.368 ± 0.793 | 0.333 ± 0.085 |
| 25 | 50 | AnchorOnly | -0.358 ± 6.106 | -0.432 ± 6.439 | 0.351 ± 0.079 |
| 25 | 50 | AnchorPlugin | -0.379 ± 6.642 | -0.593 ± 7.977 | 0.354 ± 0.097 |
| 25 | 50 | DRLearner_PooledNoSite | 0.561 ± 1.511 | 0.427 ± 2.436 | 0.577 ± 0.121 |
| 25 | 50 | DRLearner_PooledWithSite | 0.559 ± 1.555 | 0.433 ± 2.407 | 0.577 ± 0.121 |
| 25 | 50 | EntropyBalancing | 0.052 ± 3.819 | -0.092 ± 4.053 | 0.414 ± 0.156 |
| 25 | 50 | IPWTransport | 0.530 ± 1.615 | 0.392 ± 2.593 | 0.558 ± 0.130 |
| 25 | 50 | OutcomeModelTransport | 0.535 ± 1.568 | 0.393 ± 2.593 | 0.558 ± 0.129 |
| 25 | 50 | ProposedA | -0.337 ± 6.616 | -0.409 ± 6.586 | 0.407 ± 0.058 |
| 25 | 50 | ProposedB_LinearStepB | -0.330 ± 6.225 | -0.260 ± 5.155 | 0.359 ± 0.078 |
| 25 | 50 | ProposedB_SourceDR | -0.597 ± 7.653 | -0.612 ± 6.275 | 0.277 ± 0.099 |
| 25 | 50 | ProxyOnly | -1.023 ± 9.567 | -1.260 ± 10.431 | 0.188 ± 0.095 |
| 25 | 50 | TargetOnlyDR | -0.320 ± 6.177 | -0.509 ± 7.008 | 0.375 ± 0.067 |
| 25 | 100 | AnchorOnly | 0.250 ± 1.399 | 0.130 ± 2.086 | 0.399 ± 0.079 |
| 25 | 100 | AnchorPlugin | 0.235 ± 1.360 | -0.144 ± 4.127 | 0.357 ± 0.119 |
| 25 | 100 | DRLearner_PooledNoSite | 0.676 ± 0.436 | 0.516 ± 1.111 | 0.583 ± 0.148 |
| 25 | 100 | DRLearner_PooledWithSite | 0.667 ± 0.460 | 0.513 ± 1.110 | 0.582 ± 0.148 |
| 25 | 100 | EntropyBalancing | 0.223 ± 2.145 | 0.059 ± 3.027 | 0.392 ± 0.171 |
| 25 | 100 | IPWTransport | 0.612 ± 0.582 | 0.442 ± 1.297 | 0.556 ± 0.161 |
| 25 | 100 | OutcomeModelTransport | 0.614 ± 0.574 | 0.442 ± 1.296 | 0.556 ± 0.161 |
| 25 | 100 | ProposedA | 0.253 ± 1.416 | 0.235 ± 1.517 | 0.420 ± 0.077 |
| 25 | 100 | ProposedB_LinearStepB | 0.259 ± 1.295 | 0.132 ± 2.058 | 0.403 ± 0.074 |
| 25 | 100 | ProposedB_SourceDR | 0.059 ± 1.742 | -0.273 ± 3.397 | 0.281 ± 0.105 |
| 25 | 100 | ProxyOnly | -0.109 ± 1.819 | -0.581 ± 4.944 | 0.168 ± 0.116 |
| 25 | 100 | TargetOnlyDR | 0.171 ± 1.591 | 0.125 ± 1.844 | 0.383 ± 0.075 |
| 50 | 0 | AnchorOnly | N/A | N/A | N/A |
| 50 | 0 | AnchorPlugin | 0.284 ± 2.068 | -2.066 ± 22.903 | 0.418 ± 0.119 |
| 50 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 50 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 50 | 0 | EntropyBalancing | 0.186 ± 2.319 | -3.005 ± 30.417 | 0.405 ± 0.150 |
| 50 | 0 | IPWTransport | 0.503 ± 1.606 | -2.655 ± 30.696 | 0.556 ± 0.142 |
| 50 | 0 | OutcomeModelTransport | 0.500 ± 1.625 | -2.654 ± 30.697 | 0.556 ± 0.142 |
| 50 | 0 | ProposedA | N/A | N/A | N/A |
| 50 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 50 | 0 | ProposedB_SourceDR | 0.036 ± 2.266 | -2.742 ± 26.462 | 0.289 ± 0.103 |
| 50 | 0 | ProxyOnly | 0.037 ± 2.016 | -2.705 ± 25.307 | 0.254 ± 0.101 |
| 50 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 50 | 25 | AnchorOnly | -5.628 ± 46.412 | -0.378 ± 3.840 | 0.253 ± 0.107 |
| 50 | 25 | AnchorPlugin | -4.200 ± 39.783 | 0.257 ± 1.445 | 0.434 ± 0.107 |
| 50 | 25 | DRLearner_PooledNoSite | -2.385 ± 27.692 | 0.512 ± 1.203 | 0.582 ± 0.132 |
| 50 | 25 | DRLearner_PooledWithSite | -2.304 ± 26.997 | 0.515 ± 1.198 | 0.584 ± 0.131 |
| 50 | 25 | EntropyBalancing | -5.036 ± 47.294 | 0.089 ± 2.169 | 0.412 ± 0.131 |
| 50 | 25 | IPWTransport | -2.271 ± 26.288 | 0.484 ± 1.237 | 0.565 ± 0.141 |
| 50 | 25 | OutcomeModelTransport | -2.160 ± 25.230 | 0.483 ± 1.243 | 0.565 ± 0.142 |
| 50 | 25 | ProposedA | -6.549 ± 59.123 | 0.008 ± 2.300 | 0.361 ± 0.070 |
| 50 | 25 | ProposedB_LinearStepB | -5.350 ± 46.576 | -0.238 ± 3.283 | 0.294 ± 0.103 |
| 50 | 25 | ProposedB_SourceDR | -4.888 ± 40.195 | -0.210 ± 2.762 | 0.279 ± 0.108 |
| 50 | 25 | ProxyOnly | -6.810 ± 59.406 | -0.250 ± 3.035 | 0.273 ± 0.097 |
| 50 | 25 | TargetOnlyDR | -5.710 ± 50.513 | -0.029 ± 2.125 | 0.328 ± 0.077 |
| 50 | 50 | AnchorOnly | 0.339 ± 0.773 | 0.239 ± 1.138 | 0.384 ± 0.086 |
| 50 | 50 | AnchorPlugin | 0.401 ± 0.806 | 0.320 ± 0.987 | 0.437 ± 0.112 |
| 50 | 50 | DRLearner_PooledNoSite | 0.675 ± 0.461 | 0.620 ± 0.749 | 0.578 ± 0.139 |
| 50 | 50 | DRLearner_PooledWithSite | 0.675 ± 0.461 | 0.622 ± 0.744 | 0.578 ± 0.139 |
| 50 | 50 | EntropyBalancing | 0.346 ± 0.981 | 0.316 ± 0.961 | 0.402 ± 0.149 |
| 50 | 50 | IPWTransport | 0.638 ± 0.523 | 0.590 ± 0.768 | 0.554 ± 0.148 |
| 50 | 50 | OutcomeModelTransport | 0.637 ± 0.523 | 0.590 ± 0.773 | 0.554 ± 0.147 |
| 50 | 50 | ProposedA | 0.494 ± 0.542 | 0.397 ± 0.812 | 0.468 ± 0.055 |
| 50 | 50 | ProposedB_LinearStepB | 0.336 ± 0.842 | 0.248 ± 1.123 | 0.401 ± 0.086 |
| 50 | 50 | ProposedB_SourceDR | 0.165 ± 1.018 | 0.051 ± 1.208 | 0.280 ± 0.086 |
| 50 | 50 | ProxyOnly | 0.107 ± 1.112 | 0.048 ± 1.169 | 0.286 ± 0.080 |
| 50 | 50 | TargetOnlyDR | 0.415 ± 0.769 | 0.352 ± 0.853 | 0.439 ± 0.059 |
| 50 | 100 | AnchorOnly | 0.349 ± 1.432 | 0.366 ± 1.578 | 0.459 ± 0.062 |
| 50 | 100 | AnchorPlugin | 0.365 ± 0.882 | 0.192 ± 2.092 | 0.419 ± 0.112 |
| 50 | 100 | DRLearner_PooledNoSite | 0.671 ± 0.377 | 0.565 ± 1.009 | 0.586 ± 0.127 |
| 50 | 100 | DRLearner_PooledWithSite | 0.669 ± 0.382 | 0.565 ± 0.991 | 0.586 ± 0.128 |
| 50 | 100 | EntropyBalancing | 0.340 ± 0.941 | 0.297 ± 1.266 | 0.400 ± 0.144 |
| 50 | 100 | IPWTransport | 0.617 ± 0.449 | 0.488 ± 1.199 | 0.552 ± 0.143 |
| 50 | 100 | OutcomeModelTransport | 0.617 ± 0.448 | 0.487 ± 1.198 | 0.552 ± 0.143 |
| 50 | 100 | ProposedA | 0.409 ± 1.383 | 0.501 ± 1.001 | 0.498 ± 0.055 |
| 50 | 100 | ProposedB_LinearStepB | 0.305 ± 1.634 | 0.355 ± 1.596 | 0.458 ± 0.072 |
| 50 | 100 | ProposedB_SourceDR | -0.045 ± 2.132 | -0.188 ± 3.068 | 0.279 ± 0.094 |
| 50 | 100 | ProxyOnly | -0.138 ± 2.208 | -0.284 ± 3.330 | 0.235 ± 0.093 |
| 50 | 100 | TargetOnlyDR | 0.345 ± 1.385 | 0.373 ± 1.441 | 0.462 ± 0.058 |
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 0.199 ± 2.628 | -0.660 ± 10.092 | 0.445 ± 0.103 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | -0.117 ± 4.721 | -1.267 ± 14.230 | 0.380 ± 0.142 |
| 100 | 0 | IPWTransport | 0.396 ± 2.419 | -0.166 ± 7.145 | 0.537 ± 0.154 |
| 100 | 0 | OutcomeModelTransport | 0.395 ± 2.419 | -0.169 ± 7.145 | 0.537 ± 0.154 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | -0.523 ± 6.059 | -2.841 ± 26.366 | 0.274 ± 0.089 |
| 100 | 0 | ProxyOnly | -0.226 ± 3.916 | -2.562 ± 24.348 | 0.311 ± 0.101 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 25 | AnchorOnly | -0.029 ± 1.431 | -0.578 ± 3.084 | 0.219 ± 0.102 |
| 100 | 25 | AnchorPlugin | 0.473 ± 0.555 | 0.082 ± 2.144 | 0.460 ± 0.106 |
| 100 | 25 | DRLearner_PooledNoSite | 0.709 ± 0.275 | 0.537 ± 0.894 | 0.592 ± 0.112 |
| 100 | 25 | DRLearner_PooledWithSite | 0.713 ± 0.273 | 0.550 ± 0.844 | 0.596 ± 0.111 |
| 100 | 25 | EntropyBalancing | 0.398 ± 0.785 | 0.113 ± 1.604 | 0.418 ± 0.125 |
| 100 | 25 | IPWTransport | 0.678 ± 0.311 | 0.501 ± 0.937 | 0.571 ± 0.121 |
| 100 | 25 | OutcomeModelTransport | 0.678 ± 0.314 | 0.499 ± 0.945 | 0.570 ± 0.122 |
| 100 | 25 | ProposedA | 0.157 ± 1.067 | -0.217 ± 2.472 | 0.350 ± 0.086 |
| 100 | 25 | ProposedB_LinearStepB | 0.086 ± 1.300 | -0.314 ± 2.539 | 0.286 ± 0.123 |
| 100 | 25 | ProposedB_SourceDR | 0.149 ± 1.057 | -0.333 ± 2.661 | 0.284 ± 0.090 |
| 100 | 25 | ProxyOnly | 0.235 ± 0.757 | -0.353 ± 3.124 | 0.323 ± 0.103 |
| 100 | 25 | TargetOnlyDR | 0.061 ± 0.997 | -0.397 ± 2.719 | 0.291 ± 0.086 |
| 100 | 50 | AnchorOnly | -0.915 ± 10.598 | 0.084 ± 2.010 | 0.336 ± 0.101 |
| 100 | 50 | AnchorPlugin | -0.094 ± 5.013 | 0.314 ± 1.506 | 0.463 ± 0.102 |
| 100 | 50 | DRLearner_PooledNoSite | 0.439 ± 2.204 | 0.672 ± 0.551 | 0.607 ± 0.125 |
| 100 | 50 | DRLearner_PooledWithSite | 0.426 ± 2.370 | 0.676 ± 0.543 | 0.610 ± 0.124 |
| 100 | 50 | EntropyBalancing | -0.141 ± 4.849 | 0.370 ± 0.856 | 0.431 ± 0.150 |
| 100 | 50 | IPWTransport | 0.359 ± 2.536 | 0.624 ± 0.682 | 0.581 ± 0.136 |
| 100 | 50 | OutcomeModelTransport | 0.358 ± 2.536 | 0.616 ± 0.734 | 0.581 ± 0.136 |
| 100 | 50 | ProposedA | 0.017 ± 4.655 | 0.433 ± 1.032 | 0.492 ± 0.053 |
| 100 | 50 | ProposedB_LinearStepB | -0.485 ± 7.670 | 0.281 ± 1.247 | 0.401 ± 0.086 |
| 100 | 50 | ProposedB_SourceDR | -0.593 ± 6.925 | 0.073 ± 1.680 | 0.302 ± 0.102 |
| 100 | 50 | ProxyOnly | -0.579 ± 7.158 | -0.013 ± 1.994 | 0.323 ± 0.091 |
| 100 | 50 | TargetOnlyDR | -0.213 ± 5.489 | 0.276 ± 1.429 | 0.429 ± 0.067 |
| 100 | 100 | AnchorOnly | 0.265 ± 1.531 | 0.031 ± 5.291 | 0.450 ± 0.081 |
| 100 | 100 | AnchorPlugin | 0.276 ± 1.499 | 0.028 ± 5.108 | 0.456 ± 0.093 |
| 100 | 100 | DRLearner_PooledNoSite | 0.586 ± 0.858 | 0.001 ± 6.679 | 0.597 ± 0.118 |
| 100 | 100 | DRLearner_PooledWithSite | 0.585 ± 0.867 | -0.014 ± 6.824 | 0.597 ± 0.118 |
| 100 | 100 | EntropyBalancing | 0.060 ± 2.154 | -0.840 ± 12.009 | 0.400 ± 0.127 |
| 100 | 100 | IPWTransport | 0.513 ± 1.027 | -0.132 ± 7.463 | 0.558 ± 0.133 |
| 100 | 100 | OutcomeModelTransport | 0.511 ± 1.068 | -0.131 ± 7.488 | 0.560 ± 0.132 |
| 100 | 100 | ProposedA | 0.504 ± 0.868 | 0.179 ± 4.777 | 0.534 ± 0.046 |
| 100 | 100 | ProposedB_LinearStepB | 0.387 ± 1.154 | 0.236 ± 3.878 | 0.488 ± 0.066 |
| 100 | 100 | ProposedB_SourceDR | -0.121 ± 2.145 | -1.252 ± 14.285 | 0.299 ± 0.086 |
| 100 | 100 | ProxyOnly | -0.101 ± 2.397 | -0.366 ± 6.924 | 0.321 ± 0.084 |
| 100 | 100 | TargetOnlyDR | 0.369 ± 1.337 | 0.195 ± 4.277 | 0.500 ± 0.049 |
| 200 | 0 | AnchorOnly | N/A | N/A | N/A |
| 200 | 0 | AnchorPlugin | 0.388 ± 1.288 | 0.278 ± 2.458 | 0.462 ± 0.103 |
| 200 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 200 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 200 | 0 | EntropyBalancing | 0.342 ± 1.368 | 0.240 ± 2.422 | 0.423 ± 0.145 |
| 200 | 0 | IPWTransport | 0.645 ± 0.844 | 0.586 ± 1.219 | 0.575 ± 0.126 |
| 200 | 0 | OutcomeModelTransport | 0.647 ± 0.835 | 0.588 ± 1.213 | 0.576 ± 0.126 |
| 200 | 0 | ProposedA | N/A | N/A | N/A |
| 200 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 200 | 0 | ProposedB_SourceDR | 0.097 ± 1.453 | -0.036 ± 2.749 | 0.292 ± 0.095 |
| 200 | 0 | ProxyOnly | 0.128 ± 1.554 | -0.142 ± 3.873 | 0.343 ± 0.093 |
| 200 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 200 | 25 | AnchorOnly | -2.617 ± 23.494 | -74.523 ± 684.394 | 0.181 ± 0.083 |
| 200 | 25 | AnchorPlugin | -0.285 ± 7.050 | -16.017 ± 151.076 | 0.459 ± 0.103 |
| 200 | 25 | DRLearner_PooledNoSite | 0.244 ± 4.144 | -11.085 ± 108.120 | 0.597 ± 0.131 |
| 200 | 25 | DRLearner_PooledWithSite | 0.246 ± 4.182 | -10.305 ± 101.017 | 0.604 ± 0.129 |
| 200 | 25 | EntropyBalancing | -0.722 ± 10.794 | -31.996 ± 298.022 | 0.408 ± 0.154 |
| 200 | 25 | IPWTransport | 0.122 ± 4.913 | -12.347 ± 119.409 | 0.570 ± 0.145 |
| 200 | 25 | OutcomeModelTransport | 0.130 ± 4.860 | -12.348 ± 119.409 | 0.570 ± 0.145 |
| 200 | 25 | ProposedA | -1.629 ± 15.499 | -38.598 ± 355.377 | 0.307 ± 0.085 |
| 200 | 25 | ProposedB_LinearStepB | -1.585 ± 15.368 | -75.158 ± 692.762 | 0.256 ± 0.106 |
| 200 | 25 | ProposedB_SourceDR | -1.474 ± 15.242 | -37.336 ± 344.458 | 0.297 ± 0.097 |
| 200 | 25 | ProxyOnly | -1.623 ± 17.482 | -38.893 ± 359.762 | 0.336 ± 0.091 |
| 200 | 25 | TargetOnlyDR | -2.650 ± 23.745 | -33.732 ± 309.458 | 0.242 ± 0.070 |
| 200 | 50 | AnchorOnly | -0.511 ± 4.519 | 0.244 ± 1.255 | 0.280 ± 0.104 |
| 200 | 50 | AnchorPlugin | 0.130 ± 2.953 | 0.531 ± 0.818 | 0.460 ± 0.098 |
| 200 | 50 | DRLearner_PooledNoSite | 0.571 ± 1.316 | 0.743 ± 0.331 | 0.598 ± 0.126 |
| 200 | 50 | DRLearner_PooledWithSite | 0.581 ± 1.290 | 0.751 ± 0.315 | 0.603 ± 0.124 |
| 200 | 50 | EntropyBalancing | 0.026 ± 3.600 | 0.417 ± 0.934 | 0.397 ± 0.136 |
| 200 | 50 | IPWTransport | 0.514 ± 1.419 | 0.702 ± 0.378 | 0.559 ± 0.143 |
| 200 | 50 | OutcomeModelTransport | 0.513 ± 1.421 | 0.700 ± 0.382 | 0.559 ± 0.143 |
| 200 | 50 | ProposedA | 0.204 ± 2.716 | 0.574 ± 0.622 | 0.491 ± 0.061 |
| 200 | 50 | ProposedB_LinearStepB | -0.039 ± 2.848 | 0.383 ± 0.868 | 0.356 ± 0.115 |
| 200 | 50 | ProposedB_SourceDR | -0.395 ± 4.570 | 0.206 ± 1.374 | 0.291 ± 0.100 |
| 200 | 50 | ProxyOnly | -0.091 ± 3.154 | 0.322 ± 1.129 | 0.350 ± 0.097 |
| 200 | 50 | TargetOnlyDR | -0.311 ± 4.294 | 0.309 ± 1.328 | 0.371 ± 0.074 |
| 200 | 100 | AnchorOnly | -0.151 ± 3.969 | 0.302 ± 1.227 | 0.420 ± 0.087 |
| 200 | 100 | AnchorPlugin | -0.111 ± 5.067 | 0.467 ± 0.814 | 0.472 ± 0.094 |
| 200 | 100 | DRLearner_PooledNoSite | 0.471 ± 2.193 | 0.717 ± 0.462 | 0.634 ± 0.102 |
| 200 | 100 | DRLearner_PooledWithSite | 0.468 ± 2.264 | 0.718 ± 0.461 | 0.636 ± 0.102 |
| 200 | 100 | EntropyBalancing | -0.499 ± 7.395 | 0.311 ± 1.238 | 0.425 ± 0.139 |
| 200 | 100 | IPWTransport | 0.350 ± 2.770 | 0.655 ± 0.545 | 0.590 ± 0.116 |
| 200 | 100 | OutcomeModelTransport | 0.354 ± 2.763 | 0.657 ± 0.545 | 0.590 ± 0.115 |
| 200 | 100 | ProposedA | 0.224 ± 3.015 | 0.533 ± 0.893 | 0.548 ± 0.043 |
| 200 | 100 | ProposedB_LinearStepB | 0.093 ± 2.860 | 0.402 ± 1.093 | 0.471 ± 0.083 |
| 200 | 100 | ProposedB_SourceDR | -0.557 ± 5.643 | 0.015 ± 1.657 | 0.298 ± 0.089 |
| 200 | 100 | ProxyOnly | -0.597 ± 7.012 | 0.202 ± 1.203 | 0.346 ± 0.091 |
| 200 | 100 | TargetOnlyDR | 0.111 ± 2.924 | 0.474 ± 0.906 | 0.501 ± 0.052 |

### ATE Estimation

| m0 | m1 | Method | ATE Est | ATE Err (↓) | ATE Bias |
|---|---|---|---|---|---|
| 25 | 0 | AnchorOnly | N/A | N/A | N/A |
| 25 | 0 | AnchorPlugin | 0.427 ± 5.242 | 3.995 ± 3.733 | -0.755 ± 5.429 |
| 25 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 25 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 25 | 0 | EntropyBalancing | 0.241 ± 6.062 | 5.476 ± 4.081 | -0.941 ± 6.785 |
| 25 | 0 | IPWTransport | 0.410 ± 6.525 | 3.694 ± 3.626 | -0.772 ± 5.131 |
| 25 | 0 | OutcomeModelTransport | 0.424 ± 6.536 | 3.686 ± 3.634 | -0.758 ± 5.133 |
| 25 | 0 | ProposedA | N/A | N/A | N/A |
| 25 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 25 | 0 | ProposedB_SourceDR | 0.159 ± 2.878 | 4.661 ± 4.163 | -1.023 ± 6.182 |
| 25 | 0 | ProxyOnly | 0.710 ± 7.993 | 5.290 ± 4.364 | -0.472 ± 6.861 |
| 25 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 25 | 25 | AnchorOnly | 0.686 ± 6.847 | 0.749 ± 0.539 | 0.075 ± 0.922 |
| 25 | 25 | AnchorPlugin | -0.445 ± 4.703 | 4.203 ± 3.529 | -1.056 ± 5.401 |
| 25 | 25 | DRLearner_PooledNoSite | 0.237 ± 5.809 | 1.619 ± 1.344 | -0.374 ± 2.077 |
| 25 | 25 | DRLearner_PooledWithSite | 0.241 ± 5.798 | 1.639 ± 1.349 | -0.369 ± 2.096 |
| 25 | 25 | EntropyBalancing | -0.389 ± 6.790 | 5.065 ± 4.804 | -1.000 ± 6.927 |
| 25 | 25 | IPWTransport | -0.198 ± 5.359 | 3.846 ± 3.249 | -0.808 ± 4.983 |
| 25 | 25 | OutcomeModelTransport | -0.195 ± 5.378 | 3.841 ± 3.253 | -0.806 ± 4.983 |
| 25 | 25 | ProposedA | 0.667 ± 6.735 | 0.645 ± 0.493 | 0.056 ± 0.812 |
| 25 | 25 | ProposedB_LinearStepB | 0.757 ± 6.796 | 0.740 ± 0.554 | 0.146 ± 0.916 |
| 25 | 25 | ProposedB_SourceDR | -0.628 ± 3.217 | 4.824 ± 4.127 | -1.239 ± 6.244 |
| 25 | 25 | ProxyOnly | -0.299 ± 8.222 | 5.650 ± 4.839 | -0.910 ± 7.404 |
| 25 | 25 | TargetOnlyDR | 0.585 ± 6.778 | 0.657 ± 0.426 | -0.026 ± 0.786 |
| 25 | 50 | AnchorOnly | -0.612 ± 7.607 | 0.516 ± 0.352 | -0.049 ± 0.625 |
| 25 | 50 | AnchorPlugin | -0.091 ± 4.945 | 4.695 ± 4.110 | 0.473 ± 6.240 |
| 25 | 50 | DRLearner_PooledNoSite | -0.453 ± 6.921 | 1.092 ± 1.134 | 0.111 ± 1.574 |
| 25 | 50 | DRLearner_PooledWithSite | -0.447 ± 6.907 | 1.132 ± 1.162 | 0.116 ± 1.622 |
| 25 | 50 | EntropyBalancing | 0.465 ± 6.237 | 5.239 ± 4.752 | 1.028 ± 7.017 |
| 25 | 50 | IPWTransport | -0.152 ± 6.480 | 3.570 ± 3.360 | 0.411 ± 4.898 |
| 25 | 50 | OutcomeModelTransport | -0.165 ± 6.474 | 3.579 ± 3.362 | 0.399 ± 4.907 |
| 25 | 50 | ProposedA | -0.655 ± 7.586 | 0.470 ± 0.344 | -0.091 ± 0.578 |
| 25 | 50 | ProposedB_LinearStepB | -0.588 ± 7.552 | 0.514 ± 0.362 | -0.024 ± 0.631 |
| 25 | 50 | ProposedB_SourceDR | 0.197 ± 2.791 | 5.465 ± 4.901 | 0.761 ± 7.321 |
| 25 | 50 | ProxyOnly | -0.426 ± 12.049 | 7.813 ± 6.535 | 0.138 ± 10.215 |
| 25 | 50 | TargetOnlyDR | -0.676 ± 7.645 | 0.601 ± 0.468 | -0.112 ± 0.756 |
| 25 | 100 | AnchorOnly | 0.245 ± 6.617 | 0.516 ± 0.414 | 0.098 ± 0.656 |
| 25 | 100 | AnchorPlugin | 0.195 ± 4.500 | 3.868 ± 3.594 | 0.049 ± 5.294 |
| 25 | 100 | DRLearner_PooledNoSite | 0.262 ± 6.030 | 0.811 ± 0.783 | 0.115 ± 1.124 |
| 25 | 100 | DRLearner_PooledWithSite | 0.239 ± 6.029 | 0.833 ± 0.795 | 0.092 ± 1.151 |
| 25 | 100 | EntropyBalancing | -0.804 ± 5.959 | 4.992 ± 4.424 | -0.950 ± 6.621 |
| 25 | 100 | IPWTransport | 0.312 ± 5.517 | 3.704 ± 3.826 | 0.165 ± 5.336 |
| 25 | 100 | OutcomeModelTransport | 0.324 ± 5.533 | 3.704 ± 3.792 | 0.178 ± 5.311 |
| 25 | 100 | ProposedA | 0.253 ± 6.659 | 0.488 ± 0.385 | 0.106 ± 0.615 |
| 25 | 100 | ProposedB_LinearStepB | 0.251 ± 6.594 | 0.524 ± 0.393 | 0.104 ± 0.649 |
| 25 | 100 | ProposedB_SourceDR | 0.044 ± 2.775 | 4.571 ± 4.134 | -0.103 ± 6.179 |
| 25 | 100 | ProxyOnly | 1.522 ± 17.239 | 11.479 ± 9.734 | 1.375 ± 15.031 |
| 25 | 100 | TargetOnlyDR | 0.248 ± 6.654 | 0.617 ± 0.450 | 0.102 ± 0.759 |
| 50 | 0 | AnchorOnly | N/A | N/A | N/A |
| 50 | 0 | AnchorPlugin | 0.602 ± 5.367 | 4.140 ± 3.766 | 0.497 ± 5.590 |
| 50 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 50 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 50 | 0 | EntropyBalancing | 1.253 ± 6.528 | 5.591 ± 5.003 | 1.147 ± 7.435 |
| 50 | 0 | IPWTransport | 0.635 ± 6.581 | 3.901 ± 3.303 | 0.530 ± 5.098 |
| 50 | 0 | OutcomeModelTransport | 0.610 ± 6.554 | 3.892 ± 3.301 | 0.505 ± 5.093 |
| 50 | 0 | ProposedA | N/A | N/A | N/A |
| 50 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 50 | 0 | ProposedB_SourceDR | 0.218 ± 2.812 | 5.547 ± 4.322 | 0.113 ± 7.054 |
| 50 | 0 | ProxyOnly | 1.038 ± 8.648 | 5.041 ± 4.497 | 0.933 ± 6.709 |
| 50 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 50 | 25 | AnchorOnly | 0.143 ± 8.136 | 0.786 ± 0.700 | -0.077 ± 1.053 |
| 50 | 25 | AnchorPlugin | -0.370 ± 4.630 | 4.841 ± 4.436 | -0.589 ± 6.557 |
| 50 | 25 | DRLearner_PooledNoSite | -0.139 ± 6.774 | 1.484 ± 1.757 | -0.358 ± 2.276 |
| 50 | 25 | DRLearner_PooledWithSite | -0.087 ± 6.859 | 1.323 ± 1.519 | -0.307 ± 1.995 |
| 50 | 25 | EntropyBalancing | -0.810 ± 6.509 | 5.878 ± 4.972 | -1.030 ± 7.652 |
| 50 | 25 | IPWTransport | -0.536 ± 6.315 | 3.956 ± 4.170 | -0.756 ± 5.711 |
| 50 | 25 | OutcomeModelTransport | -0.553 ± 6.322 | 3.918 ± 4.234 | -0.772 ± 5.730 |
| 50 | 25 | ProposedA | 0.171 ± 7.866 | 0.731 ± 0.501 | -0.049 ± 0.888 |
| 50 | 25 | ProposedB_LinearStepB | 0.096 ± 8.069 | 0.672 ± 0.630 | -0.123 ± 0.916 |
| 50 | 25 | ProposedB_SourceDR | -0.204 ± 2.495 | 5.750 ± 4.526 | -0.423 ± 7.329 |
| 50 | 25 | ProxyOnly | -0.324 ± 5.900 | 5.066 ± 4.506 | -0.543 ± 6.777 |
| 50 | 25 | TargetOnlyDR | 0.065 ± 7.870 | 0.741 ± 0.579 | -0.154 ± 0.931 |
| 50 | 50 | AnchorOnly | -0.668 ± 7.503 | 0.502 ± 0.396 | 0.127 ± 0.629 |
| 50 | 50 | AnchorPlugin | -0.193 ± 4.614 | 4.412 ± 3.948 | 0.601 ± 5.906 |
| 50 | 50 | DRLearner_PooledNoSite | -0.477 ± 6.711 | 1.164 ± 1.020 | 0.317 ± 1.519 |
| 50 | 50 | DRLearner_PooledWithSite | -0.502 ± 6.717 | 1.166 ± 1.018 | 0.293 ± 1.524 |
| 50 | 50 | EntropyBalancing | 0.394 ± 7.080 | 5.941 ± 5.039 | 1.188 ± 7.721 |
| 50 | 50 | IPWTransport | 0.119 ± 5.908 | 4.373 ± 3.784 | 0.913 ± 5.726 |
| 50 | 50 | OutcomeModelTransport | 0.116 ± 5.866 | 4.417 ± 3.790 | 0.910 ± 5.765 |
| 50 | 50 | ProposedA | -0.712 ± 7.415 | 0.381 ± 0.297 | 0.082 ± 0.478 |
| 50 | 50 | ProposedB_LinearStepB | -0.685 ± 7.448 | 0.456 ± 0.372 | 0.109 ± 0.580 |
| 50 | 50 | ProposedB_SourceDR | 0.437 ± 2.596 | 5.291 ± 5.096 | 1.232 ± 7.261 |
| 50 | 50 | ProxyOnly | -0.772 ± 7.667 | 5.082 ± 4.616 | 0.022 ± 6.884 |
| 50 | 50 | TargetOnlyDR | -0.715 ± 7.435 | 0.457 ± 0.341 | 0.079 ± 0.567 |
| 50 | 100 | AnchorOnly | 0.419 ± 6.686 | 0.407 ± 0.317 | 0.055 ± 0.514 |
| 50 | 100 | AnchorPlugin | 0.166 ± 4.549 | 3.524 ± 2.867 | -0.198 ± 4.552 |
| 50 | 100 | DRLearner_PooledNoSite | 0.333 ± 6.226 | 0.652 ± 0.633 | -0.032 ± 0.911 |
| 50 | 100 | DRLearner_PooledWithSite | 0.323 ± 6.224 | 0.676 ± 0.621 | -0.042 ± 0.920 |
| 50 | 100 | EntropyBalancing | 0.479 ± 6.259 | 5.345 ± 4.434 | 0.114 ± 6.965 |
| 50 | 100 | IPWTransport | 0.160 ± 5.091 | 3.343 ± 3.366 | -0.205 ± 4.751 |
| 50 | 100 | OutcomeModelTransport | 0.128 ± 5.068 | 3.382 ± 3.359 | -0.236 ± 4.772 |
| 50 | 100 | ProposedA | 0.399 ± 6.772 | 0.381 ± 0.225 | 0.035 ± 0.443 |
| 50 | 100 | ProposedB_LinearStepB | 0.416 ± 6.712 | 0.396 ± 0.292 | 0.051 ± 0.490 |
| 50 | 100 | ProposedB_SourceDR | -0.355 ± 2.673 | 4.818 ± 3.620 | -0.720 ± 6.003 |
| 50 | 100 | ProxyOnly | 1.047 ± 10.632 | 6.275 ± 5.170 | 0.683 ± 8.126 |
| 50 | 100 | TargetOnlyDR | 0.423 ± 6.735 | 0.444 ± 0.313 | 0.059 ± 0.542 |
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | -0.554 ± 5.298 | 4.233 ± 3.136 | 0.419 ± 5.268 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | -0.066 ± 6.152 | 6.015 ± 4.588 | 0.907 ± 7.535 |
| 100 | 0 | IPWTransport | 0.008 ± 5.957 | 3.885 ± 3.523 | 0.982 ± 5.166 |
| 100 | 0 | OutcomeModelTransport | 0.004 ± 5.976 | 3.913 ± 3.540 | 0.978 ± 5.199 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | -0.111 ± 2.574 | 4.842 ± 4.497 | 0.863 ± 6.569 |
| 100 | 0 | ProxyOnly | -0.929 ± 8.835 | 5.444 ± 4.170 | 0.044 ± 6.879 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 25 | AnchorOnly | -0.516 ± 7.988 | 0.820 ± 0.758 | -0.101 ± 1.115 |
| 100 | 25 | AnchorPlugin | -0.380 ± 4.641 | 4.179 ± 3.589 | 0.034 ± 5.524 |
| 100 | 25 | DRLearner_PooledNoSite | -0.524 ± 6.847 | 1.175 ± 1.023 | -0.110 ± 1.558 |
| 100 | 25 | DRLearner_PooledWithSite | -0.464 ± 7.030 | 0.886 ± 0.719 | -0.050 ± 1.143 |
| 100 | 25 | EntropyBalancing | -0.187 ± 5.947 | 5.114 ± 3.983 | 0.228 ± 6.498 |
| 100 | 25 | IPWTransport | -0.463 ± 6.280 | 3.915 ± 3.101 | -0.049 ± 5.010 |
| 100 | 25 | OutcomeModelTransport | -0.479 ± 6.270 | 3.949 ± 3.200 | -0.064 ± 5.097 |
| 100 | 25 | ProposedA | -0.392 ± 7.676 | 0.504 ± 0.430 | 0.022 ± 0.664 |
| 100 | 25 | ProposedB_LinearStepB | -0.445 ± 7.732 | 0.671 ± 0.595 | -0.031 ± 0.899 |
| 100 | 25 | ProposedB_SourceDR | -0.245 ± 2.658 | 5.104 ± 4.362 | 0.169 ± 6.732 |
| 100 | 25 | ProxyOnly | -0.439 ± 5.218 | 4.316 ± 3.510 | -0.025 ± 5.579 |
| 100 | 25 | TargetOnlyDR | -0.473 ± 7.728 | 0.654 ± 0.516 | -0.058 ± 0.833 |
| 100 | 50 | AnchorOnly | -0.539 ± 7.263 | 0.484 ± 0.325 | 0.016 ± 0.585 |
| 100 | 50 | AnchorPlugin | -0.239 ± 5.184 | 4.344 ± 3.066 | 0.315 ± 5.326 |
| 100 | 50 | DRLearner_PooledNoSite | -0.471 ± 6.705 | 0.903 ± 0.769 | 0.083 ± 1.187 |
| 100 | 50 | DRLearner_PooledWithSite | -0.449 ± 6.725 | 0.802 ± 0.691 | 0.106 ± 1.056 |
| 100 | 50 | EntropyBalancing | -1.114 ± 7.229 | 6.356 ± 4.808 | -0.560 ± 7.975 |
| 100 | 50 | IPWTransport | -0.275 ± 6.485 | 3.610 ± 3.439 | 0.279 ± 4.991 |
| 100 | 50 | OutcomeModelTransport | -0.227 ± 6.466 | 3.612 ± 3.445 | 0.328 ± 4.994 |
| 100 | 50 | ProposedA | -0.581 ± 7.202 | 0.282 ± 0.222 | -0.026 ± 0.359 |
| 100 | 50 | ProposedB_LinearStepB | -0.540 ± 7.200 | 0.396 ± 0.243 | 0.015 ± 0.467 |
| 100 | 50 | ProposedB_SourceDR | 0.222 ± 2.959 | 5.284 ± 3.685 | 0.777 ± 6.417 |
| 100 | 50 | ProxyOnly | -0.568 ± 6.623 | 4.468 ± 3.269 | -0.014 ± 5.554 |
| 100 | 50 | TargetOnlyDR | -0.552 ± 7.138 | 0.406 ± 0.303 | 0.002 ± 0.508 |
| 100 | 100 | AnchorOnly | 0.178 ± 7.733 | 0.328 ± 0.311 | 0.020 ± 0.453 |
| 100 | 100 | AnchorPlugin | 0.103 ± 4.688 | 4.015 ± 3.201 | -0.055 ± 5.150 |
| 100 | 100 | DRLearner_PooledNoSite | 0.132 ± 7.388 | 0.570 ± 0.486 | -0.026 ± 0.751 |
| 100 | 100 | DRLearner_PooledWithSite | 0.120 ± 7.381 | 0.576 ± 0.488 | -0.038 ± 0.757 |
| 100 | 100 | EntropyBalancing | 0.128 ± 6.970 | 5.479 ± 3.905 | -0.030 ± 6.750 |
| 100 | 100 | IPWTransport | -0.131 ± 6.287 | 3.349 ± 3.050 | -0.289 ± 4.533 |
| 100 | 100 | OutcomeModelTransport | -0.180 ± 6.319 | 3.356 ± 3.028 | -0.337 ± 4.520 |
| 100 | 100 | ProposedA | 0.135 ± 7.728 | 0.248 ± 0.195 | -0.023 ± 0.316 |
| 100 | 100 | ProposedB_LinearStepB | 0.158 ± 7.737 | 0.293 ± 0.215 | -0.000 ± 0.365 |
| 100 | 100 | ProposedB_SourceDR | 0.150 ± 2.358 | 5.581 ± 4.206 | -0.007 ± 7.011 |
| 100 | 100 | ProxyOnly | 0.240 ± 7.825 | 4.391 ± 3.500 | 0.082 ± 5.632 |
| 100 | 100 | TargetOnlyDR | 0.151 ± 7.704 | 0.322 ± 0.294 | -0.007 ± 0.437 |
| 200 | 0 | AnchorOnly | N/A | N/A | N/A |
| 200 | 0 | AnchorPlugin | 0.672 ± 4.800 | 4.181 ± 3.108 | -0.239 ± 5.221 |
| 200 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 200 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 200 | 0 | EntropyBalancing | 0.529 ± 5.464 | 4.745 ± 4.025 | -0.382 ± 6.228 |
| 200 | 0 | IPWTransport | 0.693 ± 6.125 | 3.327 ± 3.247 | -0.218 ± 4.656 |
| 200 | 0 | OutcomeModelTransport | 0.756 ± 6.066 | 3.304 ± 3.246 | -0.155 ± 4.640 |
| 200 | 0 | ProposedA | N/A | N/A | N/A |
| 200 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 200 | 0 | ProposedB_SourceDR | 0.210 ± 2.492 | 5.243 ± 3.732 | -0.701 ± 6.418 |
| 200 | 0 | ProxyOnly | 1.172 ± 7.677 | 4.867 ± 3.932 | 0.261 ± 6.271 |
| 200 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 200 | 25 | AnchorOnly | 0.449 ± 8.217 | 0.796 ± 0.588 | -0.062 ± 0.991 |
| 200 | 25 | AnchorPlugin | 0.163 ± 5.313 | 4.107 ± 3.371 | -0.348 ± 5.318 |
| 200 | 25 | DRLearner_PooledNoSite | 0.492 ± 7.158 | 0.953 ± 0.985 | -0.019 ± 1.374 |
| 200 | 25 | DRLearner_PooledWithSite | 0.524 ± 7.494 | 0.606 ± 0.627 | 0.013 ± 0.874 |
| 200 | 25 | EntropyBalancing | 0.526 ± 6.200 | 5.424 ± 4.499 | 0.015 ± 7.068 |
| 200 | 25 | IPWTransport | 0.404 ± 5.848 | 3.613 ± 3.982 | -0.107 ± 5.388 |
| 200 | 25 | OutcomeModelTransport | 0.412 ± 5.818 | 3.595 ± 3.993 | -0.099 ± 5.384 |
| 200 | 25 | ProposedA | 0.515 ± 7.916 | 0.635 ± 0.442 | 0.004 ± 0.776 |
| 200 | 25 | ProposedB_LinearStepB | 0.519 ± 8.156 | 0.584 ± 0.480 | 0.008 ± 0.758 |
| 200 | 25 | ProposedB_SourceDR | 0.500 ± 2.605 | 5.347 ± 4.295 | -0.011 ± 6.879 |
| 200 | 25 | ProxyOnly | 0.123 ± 5.699 | 4.096 ± 3.374 | -0.388 ± 5.309 |
| 200 | 25 | TargetOnlyDR | 0.535 ± 7.968 | 0.657 ± 0.540 | 0.024 ± 0.852 |
| 200 | 50 | AnchorOnly | 1.010 ± 7.353 | 0.437 ± 0.387 | 0.029 ± 0.584 |
| 200 | 50 | AnchorPlugin | -0.363 ± 5.200 | 3.918 ± 3.557 | -1.344 ± 5.131 |
| 200 | 50 | DRLearner_PooledNoSite | 0.869 ± 6.819 | 0.758 ± 0.635 | -0.112 ± 0.986 |
| 200 | 50 | DRLearner_PooledWithSite | 0.901 ± 6.905 | 0.615 ± 0.493 | -0.080 ± 0.787 |
| 200 | 50 | EntropyBalancing | 0.564 ± 6.664 | 6.320 ± 5.531 | -0.417 ± 8.412 |
| 200 | 50 | IPWTransport | 0.052 ± 5.466 | 3.971 ± 3.542 | -0.929 ± 5.254 |
| 200 | 50 | OutcomeModelTransport | 0.122 ± 5.486 | 4.027 ± 3.569 | -0.859 ± 5.327 |
| 200 | 50 | ProposedA | 0.971 ± 7.239 | 0.277 ± 0.224 | -0.010 ± 0.357 |
| 200 | 50 | ProposedB_LinearStepB | 0.934 ± 7.380 | 0.402 ± 0.294 | -0.047 ± 0.498 |
| 200 | 50 | ProposedB_SourceDR | -0.196 ± 2.672 | 4.592 ± 4.201 | -1.177 ± 6.127 |
| 200 | 50 | ProxyOnly | -0.356 ± 5.932 | 4.136 ± 3.499 | -1.337 ± 5.265 |
| 200 | 50 | TargetOnlyDR | 0.968 ± 7.298 | 0.414 ± 0.290 | -0.013 ± 0.507 |
| 200 | 100 | AnchorOnly | 0.645 ± 7.031 | 0.312 ± 0.234 | 0.042 ± 0.389 |
| 200 | 100 | AnchorPlugin | 0.438 ± 4.701 | 3.804 ± 2.833 | -0.165 ± 4.756 |
| 200 | 100 | DRLearner_PooledNoSite | 0.561 ± 6.795 | 0.368 ± 0.290 | -0.042 ± 0.468 |
| 200 | 100 | DRLearner_PooledWithSite | 0.567 ± 6.796 | 0.350 ± 0.272 | -0.037 ± 0.443 |
| 200 | 100 | EntropyBalancing | -0.704 ± 6.380 | 5.762 ± 4.354 | -1.307 ± 7.125 |
| 200 | 100 | IPWTransport | 0.187 ± 5.604 | 3.048 ± 2.581 | -0.416 ± 3.983 |
| 200 | 100 | OutcomeModelTransport | 0.232 ± 5.597 | 3.016 ± 2.523 | -0.371 ± 3.926 |
| 200 | 100 | ProposedA | 0.639 ± 7.052 | 0.217 ± 0.149 | 0.036 ± 0.261 |
| 200 | 100 | ProposedB_LinearStepB | 0.676 ± 7.060 | 0.271 ± 0.175 | 0.073 ± 0.316 |
| 200 | 100 | ProposedB_SourceDR | 0.228 ± 2.647 | 4.794 ± 3.681 | -0.375 ± 6.051 |
| 200 | 100 | ProxyOnly | 0.567 ± 6.050 | 3.937 ± 2.911 | -0.036 ± 4.912 |
| 200 | 100 | TargetOnlyDR | 0.633 ± 7.056 | 0.283 ± 0.228 | 0.030 ± 0.363 |

### Policy / Decision Metrics

| m0 | m1 | Method | Policy Value (↑) | Regret (↓) | Value Top20 (↑) | Regret Top20 (↓) |
|---|---|---|---|---|---|---|
| 25 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 25 | 0 | AnchorPlugin | 2.493 ± 4.566 | 1.247 ± 1.589 | 0.713 ± 4.068 | 0.646 ± 0.347 |
| 25 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 25 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 25 | 0 | EntropyBalancing | 2.084 ± 4.602 | 1.656 ± 1.712 | 0.737 ± 4.077 | 0.622 ± 0.400 |
| 25 | 0 | IPWTransport | 2.837 ± 4.705 | 0.903 ± 1.404 | 0.988 ± 4.074 | 0.371 ± 0.327 |
| 25 | 0 | OutcomeModelTransport | 2.841 ± 4.697 | 0.899 ± 1.404 | 0.988 ± 4.072 | 0.371 ± 0.331 |
| 25 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 25 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 25 | 0 | ProposedB_SourceDR | 2.091 ± 4.587 | 1.649 ± 1.775 | 0.526 ± 4.050 | 0.832 ± 0.358 |
| 25 | 0 | ProxyOnly | 1.891 ± 4.837 | 1.849 ± 2.321 | 0.409 ± 4.035 | 0.949 ± 0.399 |
| 25 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 25 | 25 | AnchorOnly | 3.147 ± 4.012 | 0.542 ± 0.475 | 0.771 ± 3.632 | 0.770 ± 0.248 |
| 25 | 25 | AnchorPlugin | 2.300 ± 3.757 | 1.389 ± 1.613 | 0.914 ± 3.617 | 0.627 ± 0.278 |
| 25 | 25 | DRLearner_PooledNoSite | 3.342 ± 3.918 | 0.347 ± 0.376 | 1.216 ± 3.651 | 0.326 ± 0.217 |
| 25 | 25 | DRLearner_PooledWithSite | 3.342 ± 3.917 | 0.347 ± 0.377 | 1.216 ± 3.651 | 0.326 ± 0.218 |
| 25 | 25 | EntropyBalancing | 2.177 ± 4.209 | 1.512 ± 1.985 | 0.950 ± 3.622 | 0.592 ± 0.316 |
| 25 | 25 | IPWTransport | 2.726 ± 4.115 | 0.962 ± 1.476 | 1.193 ± 3.655 | 0.348 ± 0.232 |
| 25 | 25 | OutcomeModelTransport | 2.729 ± 4.109 | 0.960 ± 1.472 | 1.194 ± 3.654 | 0.348 ± 0.232 |
| 25 | 25 | ProposedA | 3.198 ± 4.017 | 0.491 ± 0.425 | 0.879 ± 3.621 | 0.662 ± 0.192 |
| 25 | 25 | ProposedB_LinearStepB | 3.150 ± 4.012 | 0.539 ± 0.478 | 0.778 ± 3.640 | 0.763 ± 0.253 |
| 25 | 25 | ProposedB_SourceDR | 1.707 ± 3.893 | 1.982 ± 2.305 | 0.767 ± 3.630 | 0.774 ± 0.277 |
| 25 | 25 | ProxyOnly | 1.908 ± 4.527 | 1.781 ± 2.146 | 0.580 ± 3.625 | 0.962 ± 0.313 |
| 25 | 25 | TargetOnlyDR | 3.190 ± 4.006 | 0.498 ± 0.426 | 0.851 ± 3.617 | 0.690 ± 0.201 |
| 25 | 50 | AnchorOnly | 2.989 ± 4.462 | 0.443 ± 0.351 | 0.799 ± 3.906 | 0.661 ± 0.194 |
| 25 | 50 | AnchorPlugin | 1.826 ± 4.576 | 1.605 ± 2.361 | 0.807 ± 3.874 | 0.654 ± 0.250 |
| 25 | 50 | DRLearner_PooledNoSite | 3.129 ± 4.422 | 0.302 ± 0.348 | 1.142 ± 3.890 | 0.319 ± 0.240 |
| 25 | 50 | DRLearner_PooledWithSite | 3.126 ± 4.421 | 0.305 ± 0.348 | 1.143 ± 3.889 | 0.318 ± 0.240 |
| 25 | 50 | EntropyBalancing | 1.854 ± 4.930 | 1.578 ± 2.651 | 0.897 ± 3.900 | 0.564 ± 0.363 |
| 25 | 50 | IPWTransport | 2.523 ± 4.408 | 0.908 ± 1.638 | 1.112 ± 3.890 | 0.349 ± 0.270 |
| 25 | 50 | OutcomeModelTransport | 2.524 ± 4.407 | 0.908 ± 1.640 | 1.112 ± 3.890 | 0.348 ± 0.270 |
| 25 | 50 | ProposedA | 3.021 ± 4.461 | 0.410 ± 0.326 | 0.893 ± 3.897 | 0.567 ± 0.172 |
| 25 | 50 | ProposedB_LinearStepB | 2.988 ± 4.463 | 0.443 ± 0.358 | 0.815 ± 3.911 | 0.646 ± 0.193 |
| 25 | 50 | ProposedB_SourceDR | 1.049 ± 5.197 | 2.383 ± 2.818 | 0.670 ± 3.874 | 0.791 ± 0.283 |
| 25 | 50 | ProxyOnly | 1.664 ± 4.813 | 1.767 ± 2.623 | 0.499 ± 3.888 | 0.962 ± 0.269 |
| 25 | 50 | TargetOnlyDR | 2.991 ± 4.467 | 0.441 ± 0.354 | 0.854 ± 3.909 | 0.607 ± 0.167 |
| 25 | 100 | AnchorOnly | 2.450 ± 4.205 | 0.468 ± 0.325 | 0.454 ± 3.658 | 0.584 ± 0.175 |
| 25 | 100 | AnchorPlugin | 1.516 ± 4.626 | 1.402 ± 1.672 | 0.370 ± 3.666 | 0.668 ± 0.361 |
| 25 | 100 | DRLearner_PooledNoSite | 2.641 ± 4.181 | 0.276 ± 0.271 | 0.715 ± 3.633 | 0.323 ± 0.292 |
| 25 | 100 | DRLearner_PooledWithSite | 2.638 ± 4.183 | 0.280 ± 0.274 | 0.713 ± 3.634 | 0.324 ± 0.290 |
| 25 | 100 | EntropyBalancing | 1.329 ± 4.081 | 1.588 ± 2.293 | 0.411 ± 3.658 | 0.627 ± 0.450 |
| 25 | 100 | IPWTransport | 1.832 ± 4.059 | 1.085 ± 2.393 | 0.670 ± 3.633 | 0.368 ± 0.339 |
| 25 | 100 | OutcomeModelTransport | 1.837 ± 4.055 | 1.081 ± 2.341 | 0.670 ± 3.632 | 0.368 ± 0.337 |
| 25 | 100 | ProposedA | 2.472 ± 4.194 | 0.446 ± 0.311 | 0.497 ± 3.640 | 0.541 ± 0.131 |
| 25 | 100 | ProposedB_LinearStepB | 2.455 ± 4.209 | 0.463 ± 0.324 | 0.462 ± 3.673 | 0.575 ± 0.164 |
| 25 | 100 | ProposedB_SourceDR | 0.923 ± 4.433 | 1.995 ± 2.283 | 0.229 ± 3.675 | 0.808 ± 0.339 |
| 25 | 100 | ProxyOnly | 1.023 ± 4.976 | 1.894 ± 2.329 | 0.016 ± 3.675 | 1.022 ± 0.408 |
| 25 | 100 | TargetOnlyDR | 2.435 ± 4.224 | 0.482 ± 0.347 | 0.425 ± 3.669 | 0.612 ± 0.158 |
| 50 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 50 | 0 | AnchorPlugin | 1.923 ± 5.598 | 1.177 ± 1.563 | 0.236 ± 4.199 | 0.557 ± 0.341 |
| 50 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 50 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 50 | 0 | EntropyBalancing | 1.544 ± 5.510 | 1.556 ± 2.196 | 0.210 ± 4.206 | 0.582 ± 0.445 |
| 50 | 0 | IPWTransport | 2.199 ± 5.366 | 0.901 ± 1.398 | 0.435 ± 4.217 | 0.357 ± 0.373 |
| 50 | 0 | OutcomeModelTransport | 2.201 ± 5.368 | 0.899 ± 1.378 | 0.435 ± 4.217 | 0.357 ± 0.369 |
| 50 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 50 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 50 | 0 | ProposedB_SourceDR | 1.200 ± 5.311 | 1.900 ± 2.063 | 0.000 ± 4.205 | 0.792 ± 0.394 |
| 50 | 0 | ProxyOnly | 1.665 ± 5.829 | 1.435 ± 1.957 | -0.061 ± 4.206 | 0.853 ± 0.331 |
| 50 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 50 | 25 | AnchorOnly | 3.418 ± 4.923 | 0.560 ± 0.549 | 0.770 ± 3.467 | 0.907 ± 0.424 |
| 50 | 25 | AnchorPlugin | 2.258 ± 4.556 | 1.720 ± 2.547 | 1.118 ± 3.499 | 0.559 ± 0.344 |
| 50 | 25 | DRLearner_PooledNoSite | 3.629 ± 4.772 | 0.349 ± 0.545 | 1.331 ± 3.528 | 0.346 ± 0.336 |
| 50 | 25 | DRLearner_PooledWithSite | 3.665 ± 4.795 | 0.312 ± 0.437 | 1.334 ± 3.531 | 0.343 ± 0.328 |
| 50 | 25 | EntropyBalancing | 2.253 ± 4.954 | 1.724 ± 2.241 | 1.078 ± 3.525 | 0.599 ± 0.350 |
| 50 | 25 | IPWTransport | 2.936 ± 4.941 | 1.041 ± 2.019 | 1.296 ± 3.517 | 0.381 ± 0.387 |
| 50 | 25 | OutcomeModelTransport | 2.936 ± 4.939 | 1.042 ± 2.034 | 1.296 ± 3.517 | 0.381 ± 0.387 |
| 50 | 25 | ProposedA | 3.525 ± 4.897 | 0.453 ± 0.378 | 1.011 ± 3.528 | 0.666 ± 0.237 |
| 50 | 25 | ProposedB_LinearStepB | 3.444 ± 4.918 | 0.534 ± 0.539 | 0.862 ± 3.489 | 0.815 ± 0.377 |
| 50 | 25 | ProposedB_SourceDR | 1.565 ± 4.748 | 2.413 ± 2.693 | 0.819 ± 3.497 | 0.858 ± 0.431 |
| 50 | 25 | ProxyOnly | 1.987 ± 4.735 | 1.990 ± 2.931 | 0.808 ± 3.489 | 0.869 ± 0.408 |
| 50 | 25 | TargetOnlyDR | 3.475 ± 4.904 | 0.502 ± 0.416 | 0.937 ± 3.504 | 0.740 ± 0.299 |
| 50 | 50 | AnchorOnly | 2.955 ± 4.570 | 0.475 ± 0.343 | 1.080 ± 3.815 | 0.612 ± 0.221 |
| 50 | 50 | AnchorPlugin | 2.111 ± 4.455 | 1.320 ± 1.623 | 1.166 ± 3.844 | 0.527 ± 0.229 |
| 50 | 50 | DRLearner_PooledNoSite | 3.113 ± 4.527 | 0.317 ± 0.337 | 1.361 ± 3.842 | 0.332 ± 0.244 |
| 50 | 50 | DRLearner_PooledWithSite | 3.113 ± 4.523 | 0.318 ± 0.340 | 1.361 ± 3.840 | 0.331 ± 0.243 |
| 50 | 50 | EntropyBalancing | 1.933 ± 4.560 | 1.497 ± 1.393 | 1.089 ± 3.806 | 0.603 ± 0.336 |
| 50 | 50 | IPWTransport | 2.331 ± 4.472 | 1.099 ± 1.598 | 1.323 ± 3.835 | 0.370 ± 0.271 |
| 50 | 50 | OutcomeModelTransport | 2.314 ± 4.472 | 1.116 ± 1.599 | 1.322 ± 3.836 | 0.370 ± 0.271 |
| 50 | 50 | ProposedA | 3.003 ± 4.561 | 0.428 ± 0.297 | 1.226 ± 3.811 | 0.466 ± 0.120 |
| 50 | 50 | ProposedB_LinearStepB | 2.963 ± 4.557 | 0.468 ± 0.331 | 1.104 ± 3.795 | 0.589 ± 0.202 |
| 50 | 50 | ProposedB_SourceDR | 0.970 ± 4.403 | 2.461 ± 2.871 | 0.896 ± 3.845 | 0.797 ± 0.234 |
| 50 | 50 | ProxyOnly | 1.822 ± 4.630 | 1.609 ± 2.138 | 0.890 ± 3.839 | 0.803 ± 0.220 |
| 50 | 50 | TargetOnlyDR | 2.980 ± 4.565 | 0.451 ± 0.322 | 1.178 ± 3.809 | 0.515 ± 0.129 |
| 50 | 100 | AnchorOnly | 2.586 ± 3.919 | 0.389 ± 0.290 | 0.462 ± 3.654 | 0.469 ± 0.152 |
| 50 | 100 | AnchorPlugin | 1.892 ± 3.896 | 1.082 ± 1.338 | 0.367 ± 3.614 | 0.564 ± 0.303 |
| 50 | 100 | DRLearner_PooledNoSite | 2.711 ± 3.881 | 0.264 ± 0.293 | 0.596 ± 3.651 | 0.335 ± 0.302 |
| 50 | 100 | DRLearner_PooledWithSite | 2.710 ± 3.881 | 0.264 ± 0.292 | 0.595 ± 3.650 | 0.336 ± 0.305 |
| 50 | 100 | EntropyBalancing | 1.421 ± 4.154 | 1.554 ± 1.776 | 0.319 ± 3.664 | 0.612 ± 0.376 |
| 50 | 100 | IPWTransport | 1.989 ± 3.899 | 0.986 ± 1.515 | 0.536 ± 3.660 | 0.395 ± 0.380 |
| 50 | 100 | OutcomeModelTransport | 1.973 ± 3.867 | 1.002 ± 1.552 | 0.536 ± 3.659 | 0.395 ± 0.379 |
| 50 | 100 | ProposedA | 2.613 ± 3.920 | 0.362 ± 0.260 | 0.522 ± 3.662 | 0.409 ± 0.133 |
| 50 | 100 | ProposedB_LinearStepB | 2.586 ± 3.913 | 0.389 ± 0.289 | 0.463 ± 3.654 | 0.468 ± 0.168 |
| 50 | 100 | ProposedB_SourceDR | 1.030 ± 4.049 | 1.945 ± 2.029 | 0.104 ± 3.664 | 0.827 ± 0.367 |
| 50 | 100 | ProxyOnly | 1.574 ± 4.116 | 1.401 ± 1.824 | 0.029 ± 3.600 | 0.902 ± 0.336 |
| 50 | 100 | TargetOnlyDR | 2.587 ± 3.941 | 0.388 ± 0.289 | 0.460 ± 3.662 | 0.471 ± 0.130 |
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 2.244 ± 4.366 | 1.144 ± 1.155 | 1.225 ± 4.332 | 0.502 ± 0.227 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 1.558 ± 4.511 | 1.829 ± 1.936 | 1.095 ± 4.305 | 0.632 ± 0.340 |
| 100 | 0 | IPWTransport | 2.374 ± 4.246 | 1.014 ± 1.971 | 1.332 ± 4.283 | 0.395 ± 0.368 |
| 100 | 0 | OutcomeModelTransport | 2.362 ± 4.254 | 1.026 ± 2.048 | 1.331 ± 4.282 | 0.396 ± 0.368 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 1.372 ± 4.637 | 2.016 ± 2.077 | 0.899 ± 4.272 | 0.829 ± 0.317 |
| 100 | 0 | ProxyOnly | 1.828 ± 4.579 | 1.559 ± 1.822 | 0.978 ± 4.343 | 0.749 ± 0.263 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 100 | 25 | AnchorOnly | 3.319 ± 4.581 | 0.568 ± 0.506 | 0.894 ± 3.260 | 0.916 ± 0.270 |
| 100 | 25 | AnchorPlugin | 2.796 ± 3.971 | 1.092 ± 1.327 | 1.330 ± 3.295 | 0.480 ± 0.226 |
| 100 | 25 | DRLearner_PooledNoSite | 3.639 ± 4.434 | 0.248 ± 0.246 | 1.509 ± 3.302 | 0.301 ± 0.194 |
| 100 | 25 | DRLearner_PooledWithSite | 3.652 ± 4.434 | 0.235 ± 0.235 | 1.515 ± 3.301 | 0.295 ± 0.190 |
| 100 | 25 | EntropyBalancing | 2.416 ± 4.343 | 1.471 ± 1.884 | 1.262 ± 3.331 | 0.549 ± 0.252 |
| 100 | 25 | IPWTransport | 3.130 ± 4.303 | 0.758 ± 1.071 | 1.477 ± 3.302 | 0.333 ± 0.219 |
| 100 | 25 | OutcomeModelTransport | 3.109 ± 4.220 | 0.779 ± 1.123 | 1.476 ± 3.300 | 0.334 ± 0.223 |
| 100 | 25 | ProposedA | 3.405 ± 4.523 | 0.483 ± 0.383 | 1.118 ± 3.312 | 0.692 ± 0.248 |
| 100 | 25 | ProposedB_LinearStepB | 3.358 ± 4.561 | 0.529 ± 0.425 | 1.028 ± 3.250 | 0.782 ± 0.275 |
| 100 | 25 | ProposedB_SourceDR | 2.015 ± 4.500 | 1.873 ± 2.095 | 1.020 ± 3.338 | 0.790 ± 0.268 |
| 100 | 25 | ProxyOnly | 2.652 ± 4.120 | 1.235 ± 1.679 | 1.098 ± 3.297 | 0.712 ± 0.277 |
| 100 | 25 | TargetOnlyDR | 3.330 ± 4.557 | 0.558 ± 0.437 | 1.005 ± 3.295 | 0.806 ± 0.250 |
| 100 | 50 | AnchorOnly | 3.250 ± 3.941 | 0.409 ± 0.371 | 1.044 ± 3.682 | 0.685 ± 0.231 |
| 100 | 50 | AnchorPlugin | 2.557 ± 4.153 | 1.101 ± 1.237 | 1.255 ± 3.685 | 0.473 ± 0.223 |
| 100 | 50 | DRLearner_PooledNoSite | 3.407 ± 3.876 | 0.252 ± 0.305 | 1.450 ± 3.682 | 0.278 ± 0.215 |
| 100 | 50 | DRLearner_PooledWithSite | 3.421 ± 3.877 | 0.238 ± 0.275 | 1.453 ± 3.682 | 0.275 ± 0.210 |
| 100 | 50 | EntropyBalancing | 1.934 ± 4.094 | 1.724 ± 1.606 | 1.190 ± 3.670 | 0.539 ± 0.305 |
| 100 | 50 | IPWTransport | 2.823 ± 4.134 | 0.835 ± 1.400 | 1.414 ± 3.680 | 0.314 ± 0.240 |
| 100 | 50 | OutcomeModelTransport | 2.811 ± 4.150 | 0.848 ± 1.424 | 1.412 ± 3.680 | 0.316 ± 0.241 |
| 100 | 50 | ProposedA | 3.326 ± 3.897 | 0.333 ± 0.277 | 1.303 ± 3.659 | 0.426 ± 0.132 |
| 100 | 50 | ProposedB_LinearStepB | 3.297 ± 3.901 | 0.362 ± 0.306 | 1.158 ± 3.652 | 0.571 ± 0.186 |
| 100 | 50 | ProposedB_SourceDR | 1.497 ± 4.471 | 2.162 ± 2.308 | 0.982 ± 3.703 | 0.746 ± 0.282 |
| 100 | 50 | ProxyOnly | 2.408 ± 4.218 | 1.250 ± 1.523 | 1.020 ± 3.695 | 0.708 ± 0.222 |
| 100 | 50 | TargetOnlyDR | 3.292 ± 3.914 | 0.366 ± 0.305 | 1.192 ± 3.685 | 0.536 ± 0.175 |
| 100 | 100 | AnchorOnly | 3.023 ± 4.020 | 0.313 ± 0.281 | 0.550 ± 3.630 | 0.475 ± 0.161 |
| 100 | 100 | AnchorPlugin | 2.412 ± 4.229 | 0.924 ± 1.128 | 0.566 ± 3.614 | 0.459 ± 0.163 |
| 100 | 100 | DRLearner_PooledNoSite | 3.141 ± 3.959 | 0.195 ± 0.220 | 0.744 ± 3.613 | 0.281 ± 0.180 |
| 100 | 100 | DRLearner_PooledWithSite | 3.142 ± 3.959 | 0.194 ± 0.219 | 0.744 ± 3.611 | 0.281 ± 0.180 |
| 100 | 100 | EntropyBalancing | 1.961 ± 4.164 | 1.375 ± 1.378 | 0.459 ± 3.602 | 0.567 ± 0.244 |
| 100 | 100 | IPWTransport | 2.541 ± 4.131 | 0.795 ± 1.351 | 0.689 ± 3.613 | 0.336 ± 0.216 |
| 100 | 100 | OutcomeModelTransport | 2.551 ± 4.114 | 0.784 ± 1.344 | 0.691 ± 3.613 | 0.334 ± 0.213 |
| 100 | 100 | ProposedA | 3.064 ± 3.983 | 0.272 ± 0.248 | 0.683 ± 3.606 | 0.343 ± 0.103 |
| 100 | 100 | ProposedB_LinearStepB | 3.051 ± 4.000 | 0.285 ± 0.256 | 0.616 ± 3.628 | 0.410 ± 0.132 |
| 100 | 100 | ProposedB_SourceDR | 1.387 ± 4.206 | 1.949 ± 1.932 | 0.284 ± 3.594 | 0.741 ± 0.228 |
| 100 | 100 | ProxyOnly | 2.308 ± 4.533 | 1.028 ± 1.459 | 0.333 ± 3.628 | 0.693 ± 0.179 |
| 100 | 100 | TargetOnlyDR | 3.050 ± 4.005 | 0.285 ± 0.256 | 0.628 ± 3.606 | 0.397 ± 0.109 |
| 200 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 200 | 0 | AnchorPlugin | 2.486 ± 4.362 | 1.156 ± 1.626 | 0.775 ± 3.766 | 0.481 ± 0.243 |
| 200 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 200 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 200 | 0 | EntropyBalancing | 2.053 ± 4.382 | 1.589 ± 1.956 | 0.699 ± 3.743 | 0.557 ± 0.303 |
| 200 | 0 | IPWTransport | 2.905 ± 4.128 | 0.737 ± 1.359 | 0.920 ± 3.742 | 0.337 ± 0.246 |
| 200 | 0 | OutcomeModelTransport | 2.919 ± 4.130 | 0.724 ± 1.362 | 0.920 ± 3.741 | 0.336 ± 0.247 |
| 200 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 200 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 200 | 0 | ProposedB_SourceDR | 1.640 ± 4.121 | 2.002 ± 2.059 | 0.471 ± 3.743 | 0.785 ± 0.288 |
| 200 | 0 | ProxyOnly | 2.254 ± 4.612 | 1.388 ± 2.143 | 0.575 ± 3.766 | 0.681 ± 0.248 |
| 200 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 200 | 25 | AnchorOnly | 3.370 ± 4.367 | 0.719 ± 0.659 | 0.670 ± 3.994 | 1.033 ± 0.272 |
| 200 | 25 | AnchorPlugin | 2.951 ± 4.271 | 1.139 ± 1.625 | 1.213 ± 4.035 | 0.490 ± 0.214 |
| 200 | 25 | DRLearner_PooledNoSite | 3.862 ± 4.253 | 0.227 ± 0.255 | 1.404 ± 4.033 | 0.299 ± 0.228 |
| 200 | 25 | DRLearner_PooledWithSite | 3.891 ± 4.244 | 0.198 ± 0.212 | 1.413 ± 4.036 | 0.290 ± 0.218 |
| 200 | 25 | EntropyBalancing | 2.493 ± 4.170 | 1.596 ± 1.611 | 1.109 ± 4.008 | 0.594 ± 0.334 |
| 200 | 25 | IPWTransport | 3.168 ± 4.240 | 0.921 ± 1.811 | 1.363 ± 4.028 | 0.340 ± 0.268 |
| 200 | 25 | OutcomeModelTransport | 3.174 ± 4.240 | 0.915 ± 1.809 | 1.363 ± 4.028 | 0.340 ± 0.268 |
| 200 | 25 | ProposedA | 3.519 ± 4.310 | 0.570 ± 0.367 | 0.919 ± 4.033 | 0.784 ± 0.223 |
| 200 | 25 | ProposedB_LinearStepB | 3.485 ± 4.352 | 0.605 ± 0.509 | 0.824 ± 4.033 | 0.878 ± 0.259 |
| 200 | 25 | ProposedB_SourceDR | 2.008 ± 4.373 | 2.082 ± 2.280 | 0.925 ± 4.018 | 0.778 ± 0.288 |
| 200 | 25 | ProxyOnly | 2.741 ± 4.439 | 1.348 ± 1.888 | 1.005 ± 4.002 | 0.698 ± 0.256 |
| 200 | 25 | TargetOnlyDR | 3.446 ± 4.347 | 0.643 ± 0.418 | 0.790 ± 4.014 | 0.913 ± 0.203 |
| 200 | 50 | AnchorOnly | 3.463 ± 3.991 | 0.515 ± 0.465 | 0.844 ± 3.693 | 0.802 ± 0.263 |
| 200 | 50 | AnchorPlugin | 2.816 ± 3.690 | 1.162 ± 1.601 | 1.182 ± 3.758 | 0.464 ± 0.205 |
| 200 | 50 | DRLearner_PooledNoSite | 3.743 ± 3.975 | 0.234 ± 0.291 | 1.353 ± 3.737 | 0.293 ± 0.234 |
| 200 | 50 | DRLearner_PooledWithSite | 3.760 ± 3.969 | 0.218 ± 0.252 | 1.360 ± 3.736 | 0.285 ± 0.223 |
| 200 | 50 | EntropyBalancing | 2.176 ± 3.787 | 1.801 ± 1.892 | 1.056 ± 3.748 | 0.590 ± 0.327 |
| 200 | 50 | IPWTransport | 3.026 ± 3.794 | 0.951 ± 1.210 | 1.293 ± 3.736 | 0.352 ± 0.305 |
| 200 | 50 | OutcomeModelTransport | 3.009 ± 3.822 | 0.969 ± 1.242 | 1.293 ± 3.736 | 0.352 ± 0.305 |
| 200 | 50 | ProposedA | 3.644 ± 4.001 | 0.334 ± 0.244 | 1.235 ± 3.762 | 0.411 ± 0.108 |
| 200 | 50 | ProposedB_LinearStepB | 3.527 ± 4.011 | 0.451 ± 0.377 | 1.007 ± 3.747 | 0.639 ± 0.243 |
| 200 | 50 | ProposedB_SourceDR | 2.471 ± 4.018 | 1.506 ± 1.735 | 0.861 ± 3.734 | 0.784 ± 0.325 |
| 200 | 50 | ProxyOnly | 2.634 ± 3.899 | 1.344 ± 1.956 | 0.998 ± 3.780 | 0.647 ± 0.248 |
| 200 | 50 | TargetOnlyDR | 3.532 ± 4.030 | 0.445 ± 0.346 | 1.018 ± 3.745 | 0.627 ± 0.213 |
| 200 | 100 | AnchorOnly | 2.944 ± 4.133 | 0.352 ± 0.284 | 0.549 ± 3.446 | 0.530 ± 0.179 |
| 200 | 100 | AnchorPlugin | 2.246 ± 4.515 | 1.050 ± 1.316 | 0.644 ± 3.449 | 0.434 ± 0.161 |
| 200 | 100 | DRLearner_PooledNoSite | 3.113 ± 4.075 | 0.183 ± 0.174 | 0.845 ± 3.438 | 0.233 ± 0.138 |
| 200 | 100 | DRLearner_PooledWithSite | 3.114 ± 4.075 | 0.182 ± 0.173 | 0.848 ± 3.439 | 0.230 ± 0.137 |
| 200 | 100 | EntropyBalancing | 1.634 ± 4.339 | 1.662 ± 1.744 | 0.558 ± 3.461 | 0.520 ± 0.269 |
| 200 | 100 | IPWTransport | 2.577 ± 4.145 | 0.719 ± 1.005 | 0.789 ± 3.442 | 0.290 ± 0.183 |
| 200 | 100 | OutcomeModelTransport | 2.593 ± 4.153 | 0.703 ± 0.970 | 0.790 ± 3.442 | 0.288 ± 0.182 |
| 200 | 100 | ProposedA | 3.022 ± 4.089 | 0.274 ± 0.195 | 0.754 ± 3.437 | 0.324 ± 0.086 |
| 200 | 100 | ProposedB_LinearStepB | 2.967 ± 4.112 | 0.329 ± 0.253 | 0.639 ± 3.409 | 0.439 ± 0.150 |
| 200 | 100 | ProposedB_SourceDR | 1.558 ± 4.111 | 1.738 ± 1.821 | 0.337 ± 3.442 | 0.742 ± 0.238 |
| 200 | 100 | ProxyOnly | 2.007 ± 4.857 | 1.289 ± 1.607 | 0.449 ± 3.430 | 0.629 ± 0.189 |
| 200 | 100 | TargetOnlyDR | 2.996 ± 4.094 | 0.300 ± 0.223 | 0.687 ± 3.438 | 0.391 ± 0.120 |

### Calibration Metrics

| m0 | m1 | Method | Slope (→1) | Intercept (→0) | R² (↑) | ECE (↓) | MCE (↓) |
|---|---|---|---|---|---|---|---|
| 25 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 25 | 0 | AnchorPlugin | 0.866 ± 0.271 | 0.855 ± 5.175 | 0.310 ± 0.146 | 4.068 ± 3.675 | 5.548 ± 4.782 |
| 25 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 25 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 25 | 0 | EntropyBalancing | 0.598 ± 0.259 | 1.050 ± 5.933 | 0.344 ± 0.180 | 5.748 ± 3.889 | 9.314 ± 5.950 |
| 25 | 0 | IPWTransport | 0.878 ± 0.181 | 0.761 ± 4.569 | 0.569 ± 0.182 | 3.743 ± 3.587 | 5.015 ± 4.316 |
| 25 | 0 | OutcomeModelTransport | 0.878 ± 0.182 | 0.745 ± 4.563 | 0.570 ± 0.182 | 3.741 ± 3.590 | 4.999 ± 4.315 |
| 25 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 25 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 25 | 0 | ProposedB_SourceDR | 1.041 ± 0.523 | 0.991 ± 5.910 | 0.172 ± 0.114 | 4.765 ± 4.073 | 6.548 ± 4.820 |
| 25 | 0 | ProxyOnly | 0.894 ± 0.527 | 0.685 ± 6.335 | 0.112 ± 0.081 | 5.349 ± 4.302 | 6.861 ± 4.894 |
| 25 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 25 | 25 | AnchorOnly | 0.868 ± 0.402 | 0.215 ± 3.300 | 0.206 ± 0.115 | 1.258 ± 0.787 | 2.846 ± 1.928 |
| 25 | 25 | AnchorPlugin | 0.874 ± 0.319 | 0.752 ± 5.148 | 0.314 ± 0.145 | 4.287 ± 3.457 | 6.015 ± 4.065 |
| 25 | 25 | DRLearner_PooledNoSite | 0.928 ± 0.180 | 0.437 ± 2.388 | 0.608 ± 0.171 | 1.710 ± 1.286 | 2.809 ± 1.850 |
| 25 | 25 | DRLearner_PooledWithSite | 0.929 ± 0.178 | 0.434 ± 2.408 | 0.608 ± 0.171 | 1.731 ± 1.293 | 2.808 ± 1.819 |
| 25 | 25 | EntropyBalancing | 0.657 ± 0.280 | 0.761 ± 5.593 | 0.365 ± 0.178 | 5.328 ± 4.642 | 8.311 ± 6.460 |
| 25 | 25 | IPWTransport | 0.912 ± 0.186 | 0.769 ± 4.819 | 0.587 ± 0.178 | 3.883 ± 3.212 | 5.102 ± 3.686 |
| 25 | 25 | OutcomeModelTransport | 0.912 ± 0.186 | 0.763 ± 4.808 | 0.587 ± 0.178 | 3.874 ± 3.222 | 5.101 ± 3.703 |
| 25 | 25 | ProposedA | 1.122 ± 0.352 | -0.306 ± 2.531 | 0.268 ± 0.109 | 0.989 ± 0.463 | 2.260 ± 1.157 |
| 25 | 25 | ProposedB_LinearStepB | 0.882 ± 0.372 | 0.082 ± 3.241 | 0.209 ± 0.111 | 1.168 ± 0.676 | 2.635 ± 1.641 |
| 25 | 25 | ProposedB_SourceDR | 1.176 ± 0.707 | 0.970 ± 6.096 | 0.191 ± 0.102 | 4.951 ± 4.008 | 7.015 ± 4.682 |
| 25 | 25 | ProxyOnly | 0.792 ± 0.462 | 0.875 ± 6.186 | 0.110 ± 0.086 | 5.698 ± 4.794 | 7.390 ± 5.247 |
| 25 | 25 | TargetOnlyDR | 1.056 ± 0.334 | -0.043 ± 2.527 | 0.250 ± 0.113 | 0.967 ± 0.444 | 2.187 ± 1.083 |
| 25 | 50 | AnchorOnly | 0.994 ± 0.343 | 0.029 ± 2.840 | 0.267 ± 0.106 | 0.948 ± 0.488 | 2.340 ± 1.362 |
| 25 | 50 | AnchorPlugin | 0.866 ± 0.286 | -0.387 ± 5.860 | 0.286 ± 0.125 | 4.810 ± 4.025 | 6.304 ± 4.505 |
| 25 | 50 | DRLearner_PooledNoSite | 0.911 ± 0.177 | -0.009 ± 2.153 | 0.613 ± 0.175 | 1.271 ± 1.065 | 2.311 ± 1.524 |
| 25 | 50 | DRLearner_PooledWithSite | 0.911 ± 0.177 | -0.012 ± 2.207 | 0.614 ± 0.175 | 1.305 ± 1.093 | 2.358 ± 1.578 |
| 25 | 50 | EntropyBalancing | 0.651 ± 0.297 | -0.591 ± 6.071 | 0.388 ± 0.200 | 5.495 ± 4.608 | 8.644 ± 6.117 |
| 25 | 50 | IPWTransport | 0.892 ± 0.191 | -0.380 ± 4.684 | 0.586 ± 0.186 | 3.635 ± 3.311 | 4.886 ± 3.758 |
| 25 | 50 | OutcomeModelTransport | 0.892 ± 0.191 | -0.367 ± 4.682 | 0.586 ± 0.186 | 3.638 ± 3.317 | 4.903 ± 3.767 |
| 25 | 50 | ProposedA | 1.271 ± 0.305 | 0.743 ± 2.929 | 0.336 ± 0.092 | 0.964 ± 0.359 | 2.224 ± 0.858 |
| 25 | 50 | ProposedB_LinearStepB | 1.045 ± 0.339 | 0.119 ± 2.908 | 0.278 ± 0.107 | 0.954 ± 0.440 | 2.298 ± 1.205 |
| 25 | 50 | ProposedB_SourceDR | 1.024 ± 0.544 | -0.789 ± 7.175 | 0.175 ± 0.106 | 5.652 ± 4.756 | 7.580 ± 5.036 |
| 25 | 50 | ProxyOnly | 0.595 ± 0.383 | 0.063 ± 7.491 | 0.099 ± 0.079 | 7.944 ± 6.425 | 10.196 ± 7.045 |
| 25 | 50 | TargetOnlyDR | 1.112 ± 0.299 | 0.455 ± 2.423 | 0.294 ± 0.100 | 0.944 ± 0.428 | 2.112 ± 1.095 |
| 25 | 100 | AnchorOnly | 0.998 ± 0.325 | 0.056 ± 2.247 | 0.305 ± 0.122 | 1.006 ± 0.421 | 2.518 ± 1.227 |
| 25 | 100 | AnchorPlugin | 0.878 ± 0.346 | 0.109 ± 5.578 | 0.294 ± 0.145 | 3.977 ± 3.507 | 5.635 ± 4.480 |
| 25 | 100 | DRLearner_PooledNoSite | 0.923 ± 0.193 | 0.108 ± 1.932 | 0.621 ± 0.211 | 1.014 ± 0.741 | 1.958 ± 1.338 |
| 25 | 100 | DRLearner_PooledWithSite | 0.922 ± 0.194 | 0.119 ± 1.953 | 0.619 ± 0.211 | 1.033 ± 0.752 | 1.967 ± 1.350 |
| 25 | 100 | EntropyBalancing | 0.607 ± 0.290 | 0.376 ± 5.633 | 0.362 ± 0.211 | 5.237 ± 4.297 | 8.498 ± 6.416 |
| 25 | 100 | IPWTransport | 0.889 ± 0.221 | -0.008 ± 4.918 | 0.585 ± 0.224 | 3.769 ± 3.776 | 4.990 ± 4.348 |
| 25 | 100 | OutcomeModelTransport | 0.889 ± 0.221 | -0.016 ± 4.922 | 0.585 ± 0.223 | 3.766 ± 3.744 | 4.986 ± 4.277 |
| 25 | 100 | ProposedA | 1.091 ± 0.362 | 0.128 ± 3.282 | 0.328 ± 0.125 | 1.046 ± 0.399 | 2.536 ± 1.236 |
| 25 | 100 | ProposedB_LinearStepB | 1.029 ± 0.315 | 0.273 ± 2.163 | 0.311 ± 0.117 | 1.012 ± 0.388 | 2.424 ± 1.050 |
| 25 | 100 | ProposedB_SourceDR | 1.118 ± 0.675 | -0.035 ± 6.225 | 0.173 ± 0.104 | 4.723 ± 4.012 | 6.770 ± 4.990 |
| 25 | 100 | ProxyOnly | 0.287 ± 0.229 | 0.139 ± 6.998 | 0.092 ± 0.084 | 11.959 ± 9.294 | 16.886 ± 10.503 |
| 25 | 100 | TargetOnlyDR | 0.928 ± 0.343 | -0.075 ± 2.181 | 0.272 ± 0.117 | 1.048 ± 0.437 | 2.689 ± 1.683 |
| 50 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 50 | 0 | AnchorPlugin | 0.883 ± 0.275 | -0.534 ± 5.543 | 0.382 ± 0.161 | 4.210 ± 3.705 | 5.636 ± 4.106 |
| 50 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 50 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 50 | 0 | EntropyBalancing | 0.625 ± 0.272 | -0.659 ± 6.700 | 0.372 ± 0.189 | 5.852 ± 4.823 | 8.980 ± 6.460 |
| 50 | 0 | IPWTransport | 0.871 ± 0.214 | -0.553 ± 5.054 | 0.586 ± 0.193 | 3.961 ± 3.259 | 5.299 ± 3.804 |
| 50 | 0 | OutcomeModelTransport | 0.871 ± 0.213 | -0.534 ± 5.056 | 0.586 ± 0.193 | 3.954 ± 3.256 | 5.293 ± 3.796 |
| 50 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 50 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 50 | 0 | ProposedB_SourceDR | 1.135 ± 0.614 | -0.032 ± 7.237 | 0.191 ± 0.100 | 5.635 ± 4.235 | 7.560 ± 4.516 |
| 50 | 0 | ProxyOnly | 0.913 ± 0.451 | -0.856 ± 6.726 | 0.164 ± 0.107 | 5.108 ± 4.436 | 6.732 ± 4.876 |
| 50 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 50 | 25 | AnchorOnly | 0.628 ± 0.416 | 0.180 ± 5.415 | 0.152 ± 0.107 | 2.017 ± 1.712 | 5.608 ± 4.857 |
| 50 | 25 | AnchorPlugin | 0.956 ± 0.251 | 0.466 ± 6.512 | 0.402 ± 0.146 | 4.883 ± 4.400 | 6.186 ± 4.682 |
| 50 | 25 | DRLearner_PooledNoSite | 0.932 ± 0.171 | 0.335 ± 2.625 | 0.622 ± 0.187 | 1.612 ± 1.711 | 2.607 ± 2.302 |
| 50 | 25 | DRLearner_PooledWithSite | 0.934 ± 0.169 | 0.287 ± 2.423 | 0.624 ± 0.187 | 1.455 ± 1.479 | 2.435 ± 2.071 |
| 50 | 25 | EntropyBalancing | 0.662 ± 0.247 | 0.820 ± 6.571 | 0.374 ± 0.180 | 6.080 ± 4.814 | 9.114 ± 6.032 |
| 50 | 25 | IPWTransport | 0.909 ± 0.180 | 0.671 ± 5.393 | 0.598 ± 0.198 | 4.026 ± 4.119 | 5.125 ± 4.664 |
| 50 | 25 | OutcomeModelTransport | 0.909 ± 0.181 | 0.672 ± 5.384 | 0.598 ± 0.198 | 4.000 ± 4.173 | 5.098 ± 4.750 |
| 50 | 25 | ProposedA | 1.059 ± 0.389 | -0.119 ± 3.332 | 0.265 ± 0.102 | 1.124 ± 0.452 | 2.826 ± 1.886 |
| 50 | 25 | ProposedB_LinearStepB | 0.777 ± 0.416 | 0.586 ± 4.140 | 0.197 ± 0.113 | 1.586 ± 1.465 | 4.310 ± 4.027 |
| 50 | 25 | ProposedB_SourceDR | 1.129 ± 0.567 | 0.441 ± 7.148 | 0.182 ± 0.103 | 5.799 ± 4.490 | 7.727 ± 4.926 |
| 50 | 25 | ProxyOnly | 1.284 ± 0.584 | 0.659 ± 7.406 | 0.181 ± 0.095 | 5.125 ± 4.454 | 6.805 ± 4.782 |
| 50 | 25 | TargetOnlyDR | 0.899 ± 0.356 | 0.054 ± 2.859 | 0.222 ± 0.106 | 1.138 ± 0.591 | 2.931 ± 2.119 |
| 50 | 50 | AnchorOnly | 1.060 ± 0.366 | -0.311 ± 3.331 | 0.313 ± 0.117 | 1.021 ± 0.528 | 2.465 ± 1.260 |
| 50 | 50 | AnchorPlugin | 0.938 ± 0.257 | -0.442 ± 5.834 | 0.405 ± 0.160 | 4.474 ± 3.896 | 5.855 ± 4.194 |
| 50 | 50 | DRLearner_PooledNoSite | 0.917 ± 0.185 | -0.325 ± 2.077 | 0.615 ± 0.196 | 1.320 ± 1.053 | 2.363 ± 1.956 |
| 50 | 50 | DRLearner_PooledWithSite | 0.917 ± 0.184 | -0.299 ± 2.069 | 0.615 ± 0.196 | 1.323 ± 1.049 | 2.365 ± 1.944 |
| 50 | 50 | EntropyBalancing | 0.667 ± 0.289 | -1.213 ± 6.283 | 0.368 ± 0.192 | 6.112 ± 4.890 | 9.213 ± 6.767 |
| 50 | 50 | IPWTransport | 0.890 ± 0.196 | -0.764 ± 5.359 | 0.582 ± 0.207 | 4.449 ± 3.742 | 5.673 ± 4.319 |
| 50 | 50 | OutcomeModelTransport | 0.890 ± 0.195 | -0.762 ± 5.402 | 0.582 ± 0.207 | 4.493 ± 3.748 | 5.708 ± 4.323 |
| 50 | 50 | ProposedA | 1.492 ± 0.342 | 0.211 ± 3.828 | 0.430 ± 0.085 | 1.117 ± 0.370 | 2.566 ± 0.857 |
| 50 | 50 | ProposedB_LinearStepB | 1.141 ± 0.378 | -0.566 ± 2.981 | 0.339 ± 0.119 | 0.980 ± 0.488 | 2.393 ± 1.151 |
| 50 | 50 | ProposedB_SourceDR | 1.078 ± 0.583 | -1.075 ± 7.271 | 0.175 ± 0.092 | 5.439 ± 4.971 | 7.319 ± 5.285 |
| 50 | 50 | ProxyOnly | 1.054 ± 0.438 | 0.088 ± 6.664 | 0.190 ± 0.096 | 5.141 ± 4.561 | 6.618 ± 4.881 |
| 50 | 50 | TargetOnlyDR | 1.313 ± 0.301 | -0.009 ± 3.549 | 0.387 ± 0.091 | 0.990 ± 0.358 | 2.271 ± 0.811 |
| 50 | 100 | AnchorOnly | 1.339 ± 0.343 | 0.079 ± 2.840 | 0.420 ± 0.102 | 1.018 ± 0.387 | 2.312 ± 0.983 |
| 50 | 100 | AnchorPlugin | 0.932 ± 0.268 | 0.235 ± 4.518 | 0.380 ± 0.156 | 3.592 ± 2.805 | 4.963 ± 3.272 |
| 50 | 100 | DRLearner_PooledNoSite | 0.951 ± 0.153 | 0.066 ± 1.365 | 0.626 ± 0.184 | 0.834 ± 0.599 | 1.649 ± 1.098 |
| 50 | 100 | DRLearner_PooledWithSite | 0.953 ± 0.154 | 0.072 ± 1.372 | 0.625 ± 0.185 | 0.846 ± 0.597 | 1.655 ± 1.119 |
| 50 | 100 | EntropyBalancing | 0.634 ± 0.255 | 0.235 ± 5.736 | 0.361 ± 0.197 | 5.550 ± 4.304 | 8.872 ± 6.186 |
| 50 | 100 | IPWTransport | 0.906 ± 0.170 | 0.326 ± 4.678 | 0.579 ± 0.203 | 3.418 ± 3.307 | 4.506 ± 3.763 |
| 50 | 100 | OutcomeModelTransport | 0.906 ± 0.170 | 0.350 ± 4.711 | 0.579 ± 0.203 | 3.449 ± 3.307 | 4.538 ± 3.746 |
| 50 | 100 | ProposedA | 1.561 ± 0.355 | 0.171 ± 4.235 | 0.481 ± 0.088 | 1.162 ± 0.428 | 2.807 ± 0.937 |
| 50 | 100 | ProposedB_LinearStepB | 1.352 ± 0.334 | -0.016 ± 2.869 | 0.423 ± 0.107 | 0.999 ± 0.357 | 2.362 ± 0.889 |
| 50 | 100 | ProposedB_SourceDR | 1.284 ± 0.661 | 1.108 ± 5.999 | 0.173 ± 0.099 | 4.942 ± 3.489 | 6.876 ± 3.700 |
| 50 | 100 | ProxyOnly | 0.618 ± 0.279 | -0.451 ± 5.974 | 0.140 ± 0.099 | 6.425 ± 5.099 | 8.723 ± 5.521 |
| 50 | 100 | TargetOnlyDR | 1.348 ± 0.305 | -0.061 ± 2.821 | 0.421 ± 0.095 | 1.001 ± 0.408 | 2.326 ± 1.048 |
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 0.927 ± 0.230 | -0.204 ± 5.051 | 0.415 ± 0.148 | 4.269 ± 3.094 | 5.547 ± 3.580 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 0.608 ± 0.261 | -0.635 ± 6.275 | 0.335 ± 0.182 | 6.224 ± 4.419 | 9.520 ± 5.899 |
| 100 | 0 | IPWTransport | 0.856 ± 0.199 | -0.851 ± 5.096 | 0.557 ± 0.212 | 3.941 ± 3.482 | 5.215 ± 4.044 |
| 100 | 0 | OutcomeModelTransport | 0.855 ± 0.201 | -0.855 ± 5.103 | 0.557 ± 0.212 | 3.970 ± 3.497 | 5.238 ± 4.098 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 1.111 ± 0.598 | -1.056 ± 6.356 | 0.169 ± 0.095 | 4.922 ± 4.427 | 6.625 ± 4.716 |
| 100 | 0 | ProxyOnly | 1.019 ± 0.372 | 0.485 ± 7.174 | 0.224 ± 0.124 | 5.508 ± 4.101 | 7.059 ± 4.560 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 100 | 25 | AnchorOnly | 0.361 ± 0.249 | -0.356 ± 6.174 | 0.093 ± 0.075 | 2.541 ± 1.896 | 8.898 ± 6.828 |
| 100 | 25 | AnchorPlugin | 0.946 ± 0.245 | -0.095 ± 5.537 | 0.439 ± 0.151 | 4.250 ± 3.521 | 5.577 ± 3.823 |
| 100 | 25 | DRLearner_PooledNoSite | 0.958 ± 0.159 | 0.094 ± 2.117 | 0.633 ± 0.164 | 1.284 ± 0.966 | 2.219 ± 1.301 |
| 100 | 25 | DRLearner_PooledWithSite | 0.962 ± 0.158 | 0.051 ± 1.840 | 0.638 ± 0.163 | 1.028 ± 0.656 | 1.911 ± 1.085 |
| 100 | 25 | EntropyBalancing | 0.682 ± 0.225 | -0.057 ± 6.068 | 0.383 ± 0.177 | 5.247 ± 3.874 | 7.914 ± 4.780 |
| 100 | 25 | IPWTransport | 0.935 ± 0.171 | -0.040 ± 4.920 | 0.602 ± 0.177 | 3.949 ± 3.066 | 5.056 ± 3.357 |
| 100 | 25 | OutcomeModelTransport | 0.935 ± 0.173 | -0.037 ± 4.991 | 0.602 ± 0.178 | 3.978 ± 3.169 | 5.099 ± 3.496 |
| 100 | 25 | ProposedA | 0.750 ± 0.346 | -0.316 ± 3.556 | 0.219 ± 0.120 | 1.107 ± 0.622 | 3.610 ± 3.036 |
| 100 | 25 | ProposedB_LinearStepB | 0.559 ± 0.370 | -0.119 ± 5.184 | 0.169 ± 0.130 | 1.952 ± 1.521 | 6.353 ± 5.663 |
| 100 | 25 | ProposedB_SourceDR | 1.040 ± 0.498 | -0.440 ± 6.873 | 0.179 ± 0.096 | 5.211 ± 4.269 | 7.111 ± 4.579 |
| 100 | 25 | ProxyOnly | 1.428 ± 0.608 | 0.261 ± 6.991 | 0.239 ± 0.121 | 4.402 ± 3.433 | 6.224 ± 3.753 |
| 100 | 25 | TargetOnlyDR | 0.551 ± 0.308 | -0.180 ± 4.368 | 0.143 ± 0.105 | 1.386 ± 0.706 | 4.642 ± 2.914 |
| 100 | 50 | AnchorOnly | 0.760 ± 0.345 | -0.603 ± 3.034 | 0.234 ± 0.132 | 1.254 ± 0.726 | 3.600 ± 2.173 |
| 100 | 50 | AnchorPlugin | 0.948 ± 0.233 | -0.324 ± 4.917 | 0.443 ± 0.148 | 4.367 ± 3.042 | 5.630 ± 3.420 |
| 100 | 50 | DRLearner_PooledNoSite | 0.952 ± 0.159 | -0.133 ± 1.722 | 0.656 ± 0.182 | 1.039 ± 0.720 | 1.936 ± 1.212 |
| 100 | 50 | DRLearner_PooledWithSite | 0.957 ± 0.157 | -0.158 ± 1.632 | 0.659 ± 0.180 | 0.956 ± 0.645 | 1.813 ± 1.107 |
| 100 | 50 | EntropyBalancing | 0.680 ± 0.275 | -0.077 ± 6.264 | 0.406 ± 0.205 | 6.524 ± 4.657 | 9.495 ± 6.368 |
| 100 | 50 | IPWTransport | 0.924 ± 0.180 | -0.246 ± 4.574 | 0.619 ± 0.197 | 3.665 ± 3.393 | 4.769 ± 3.877 |
| 100 | 50 | OutcomeModelTransport | 0.925 ± 0.180 | -0.284 ± 4.581 | 0.619 ± 0.197 | 3.664 ± 3.401 | 4.770 ± 3.867 |
| 100 | 50 | ProposedA | 1.447 ± 0.318 | 0.324 ± 4.151 | 0.464 ± 0.087 | 1.039 ± 0.340 | 2.441 ± 0.858 |
| 100 | 50 | ProposedB_LinearStepB | 1.029 ± 0.348 | -0.377 ± 2.789 | 0.327 ± 0.128 | 0.949 ± 0.415 | 2.508 ± 1.446 |
| 100 | 50 | ProposedB_SourceDR | 1.186 ± 0.587 | -0.757 ± 6.566 | 0.204 ± 0.110 | 5.378 ± 3.582 | 7.463 ± 3.859 |
| 100 | 50 | ProxyOnly | 1.242 ± 0.469 | 0.489 ± 6.436 | 0.235 ± 0.118 | 4.515 ± 3.217 | 6.111 ± 3.401 |
| 100 | 50 | TargetOnlyDR | 1.131 ± 0.269 | 0.207 ± 2.321 | 0.354 ± 0.115 | 0.868 ± 0.344 | 2.017 ± 0.893 |
| 100 | 100 | AnchorOnly | 1.246 ± 0.381 | 0.129 ± 2.850 | 0.402 ± 0.120 | 0.976 ± 0.383 | 2.313 ± 0.963 |
| 100 | 100 | AnchorPlugin | 0.930 ± 0.217 | -0.011 ± 5.025 | 0.432 ± 0.138 | 4.072 ± 3.146 | 5.286 ± 3.284 |
| 100 | 100 | DRLearner_PooledNoSite | 0.929 ± 0.165 | 0.028 ± 1.391 | 0.640 ± 0.172 | 0.807 ± 0.455 | 1.664 ± 0.913 |
| 100 | 100 | DRLearner_PooledWithSite | 0.930 ± 0.165 | 0.034 ± 1.387 | 0.640 ± 0.172 | 0.809 ± 0.463 | 1.656 ± 0.916 |
| 100 | 100 | EntropyBalancing | 0.633 ± 0.245 | 0.106 ± 5.951 | 0.356 ± 0.178 | 5.679 ± 3.734 | 8.770 ± 4.884 |
| 100 | 100 | IPWTransport | 0.885 ± 0.187 | 0.271 ± 4.494 | 0.585 ± 0.195 | 3.439 ± 2.977 | 4.636 ± 3.344 |
| 100 | 100 | OutcomeModelTransport | 0.887 ± 0.183 | 0.307 ± 4.486 | 0.586 ± 0.194 | 3.440 ± 2.955 | 4.613 ± 3.315 |
| 100 | 100 | ProposedA | 1.614 ± 0.291 | -0.192 ± 4.951 | 0.538 ± 0.074 | 1.149 ± 0.353 | 2.873 ± 0.789 |
| 100 | 100 | ProposedB_LinearStepB | 1.383 ± 0.330 | -0.067 ± 3.241 | 0.461 ± 0.103 | 0.976 ± 0.383 | 2.415 ± 0.974 |
| 100 | 100 | ProposedB_SourceDR | 1.159 ± 0.599 | 0.081 ± 6.699 | 0.198 ± 0.099 | 5.688 ± 4.088 | 7.471 ± 4.439 |
| 100 | 100 | ProxyOnly | 1.059 ± 0.391 | -0.369 ± 6.582 | 0.235 ± 0.108 | 4.476 ± 3.420 | 5.854 ± 3.579 |
| 100 | 100 | TargetOnlyDR | 1.432 ± 0.258 | -0.159 ± 3.878 | 0.483 ± 0.078 | 1.011 ± 0.358 | 2.410 ± 0.933 |
| 200 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 200 | 0 | AnchorPlugin | 0.933 ± 0.224 | 0.260 ± 5.278 | 0.440 ± 0.151 | 4.251 ± 3.033 | 5.548 ± 3.247 |
| 200 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 200 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 200 | 0 | EntropyBalancing | 0.699 ± 0.286 | 0.417 ± 5.857 | 0.396 ± 0.197 | 5.010 ± 3.880 | 7.812 ± 5.292 |
| 200 | 0 | IPWTransport | 0.918 ± 0.175 | 0.182 ± 4.581 | 0.609 ± 0.185 | 3.392 ± 3.195 | 4.519 ± 3.533 |
| 200 | 0 | OutcomeModelTransport | 0.920 ± 0.174 | 0.126 ± 4.576 | 0.610 ± 0.185 | 3.365 ± 3.199 | 4.476 ± 3.493 |
| 200 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 200 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 200 | 0 | ProposedB_SourceDR | 1.143 ± 0.574 | 0.786 ± 6.416 | 0.190 ± 0.100 | 5.338 ± 3.624 | 7.282 ± 3.850 |
| 200 | 0 | ProxyOnly | 1.031 ± 0.396 | -0.413 ± 6.375 | 0.261 ± 0.119 | 4.967 ± 3.841 | 6.566 ± 4.272 |
| 200 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 200 | 25 | AnchorOnly | 0.169 ± 0.135 | 0.415 ± 6.854 | 0.045 ± 0.048 | 3.302 ± 1.904 | 13.539 ± 7.578 |
| 200 | 25 | AnchorPlugin | 0.962 ± 0.234 | 0.458 ± 5.605 | 0.436 ± 0.152 | 4.137 ± 3.346 | 5.431 ± 3.708 |
| 200 | 25 | DRLearner_PooledNoSite | 0.940 ± 0.165 | 0.047 ± 2.315 | 0.640 ± 0.191 | 1.113 ± 0.951 | 2.021 ± 1.567 |
| 200 | 25 | DRLearner_PooledWithSite | 0.946 ± 0.161 | 0.042 ± 1.919 | 0.650 ± 0.186 | 0.808 ± 0.634 | 1.640 ± 1.281 |
| 200 | 25 | EntropyBalancing | 0.621 ± 0.262 | 0.172 ± 6.869 | 0.376 ± 0.202 | 5.769 ± 4.261 | 9.025 ± 5.692 |
| 200 | 25 | IPWTransport | 0.910 ± 0.189 | 0.182 ± 5.395 | 0.603 ± 0.209 | 3.670 ± 3.946 | 4.837 ± 4.538 |
| 200 | 25 | OutcomeModelTransport | 0.911 ± 0.189 | 0.179 ± 5.388 | 0.603 ± 0.209 | 3.648 ± 3.958 | 4.810 ± 4.527 |
| 200 | 25 | ProposedA | 0.428 ± 0.301 | 0.223 ± 5.097 | 0.116 ± 0.099 | 1.607 ± 0.627 | 6.037 ± 3.572 |
| 200 | 25 | ProposedB_LinearStepB | 0.340 ± 0.273 | 0.259 ± 5.843 | 0.096 ± 0.092 | 2.388 ± 1.483 | 10.182 ± 6.626 |
| 200 | 25 | ProposedB_SourceDR | 1.205 ± 0.700 | -0.136 ± 6.782 | 0.195 ± 0.100 | 5.412 ± 4.228 | 7.232 ± 4.555 |
| 200 | 25 | ProxyOnly | 1.476 ± 0.572 | 0.259 ± 6.939 | 0.254 ± 0.115 | 4.197 ± 3.280 | 6.095 ± 3.606 |
| 200 | 25 | TargetOnlyDR | 0.250 ± 0.160 | 0.286 ± 5.845 | 0.058 ± 0.049 | 2.021 ± 0.600 | 7.352 ± 3.188 |
| 200 | 50 | AnchorOnly | 0.499 ± 0.317 | 0.588 ± 5.068 | 0.137 ± 0.100 | 1.831 ± 1.227 | 6.512 ± 5.067 |
| 200 | 50 | AnchorPlugin | 0.911 ± 0.231 | 1.309 ± 4.976 | 0.438 ± 0.145 | 4.007 ± 3.477 | 5.301 ± 3.658 |
| 200 | 50 | DRLearner_PooledNoSite | 0.933 ± 0.166 | 0.227 ± 1.633 | 0.641 ± 0.181 | 0.945 ± 0.621 | 1.841 ± 1.246 |
| 200 | 50 | DRLearner_PooledWithSite | 0.941 ± 0.161 | 0.207 ± 1.463 | 0.649 ± 0.178 | 0.811 ± 0.513 | 1.637 ± 1.096 |
| 200 | 50 | EntropyBalancing | 0.620 ± 0.245 | 0.805 ± 6.733 | 0.356 ± 0.183 | 6.449 ± 5.435 | 9.716 ± 7.415 |
| 200 | 50 | IPWTransport | 0.887 ± 0.191 | 0.908 ± 5.324 | 0.585 ± 0.205 | 4.031 ± 3.493 | 5.270 ± 3.901 |
| 200 | 50 | OutcomeModelTransport | 0.887 ± 0.192 | 0.849 ± 5.379 | 0.585 ± 0.205 | 4.089 ± 3.515 | 5.311 ± 3.936 |
| 200 | 50 | ProposedA | 1.318 ± 0.342 | -0.893 ± 3.981 | 0.444 ± 0.114 | 0.969 ± 0.421 | 2.384 ± 1.114 |
| 200 | 50 | ProposedB_LinearStepB | 0.773 ± 0.394 | 0.579 ± 3.448 | 0.238 ± 0.144 | 1.341 ± 0.899 | 4.287 ± 3.519 |
| 200 | 50 | ProposedB_SourceDR | 1.049 ± 0.506 | 0.892 ± 6.130 | 0.193 ± 0.107 | 4.717 ± 4.099 | 6.468 ± 4.259 |
| 200 | 50 | ProxyOnly | 1.367 ± 0.533 | 1.176 ± 6.901 | 0.273 ± 0.123 | 4.250 ± 3.400 | 5.969 ± 3.656 |
| 200 | 50 | TargetOnlyDR | 0.732 ± 0.275 | 0.297 ± 2.892 | 0.213 ± 0.118 | 1.081 ± 0.469 | 2.888 ± 1.917 |
| 200 | 100 | AnchorOnly | 0.993 ± 0.339 | 0.091 ± 2.774 | 0.332 ± 0.127 | 0.997 ± 0.463 | 2.747 ± 1.652 |
| 200 | 100 | AnchorPlugin | 0.916 ± 0.208 | 0.177 ± 4.797 | 0.454 ± 0.141 | 3.844 ± 2.792 | 5.115 ± 2.980 |
| 200 | 100 | DRLearner_PooledNoSite | 0.960 ± 0.155 | 0.065 ± 1.313 | 0.693 ± 0.146 | 0.611 ± 0.332 | 1.341 ± 0.756 |
| 200 | 100 | DRLearner_PooledWithSite | 0.962 ± 0.153 | 0.060 ± 1.295 | 0.696 ± 0.145 | 0.602 ± 0.320 | 1.331 ± 0.721 |
| 200 | 100 | EntropyBalancing | 0.664 ± 0.271 | 0.456 ± 5.844 | 0.395 ± 0.194 | 5.891 ± 4.282 | 9.011 ± 6.228 |
| 200 | 100 | IPWTransport | 0.917 ± 0.166 | 0.323 ± 4.015 | 0.630 ± 0.171 | 3.102 ± 2.531 | 4.182 ± 2.852 |
| 200 | 100 | OutcomeModelTransport | 0.917 ± 0.166 | 0.283 ± 3.980 | 0.631 ± 0.170 | 3.079 ± 2.465 | 4.143 ± 2.763 |
| 200 | 100 | ProposedA | 1.573 ± 0.285 | -0.806 ± 4.796 | 0.560 ± 0.065 | 1.103 ± 0.332 | 2.762 ± 0.792 |
| 200 | 100 | ProposedB_LinearStepB | 1.230 ± 0.369 | -0.458 ± 3.197 | 0.430 ± 0.124 | 0.985 ± 0.432 | 2.426 ± 1.216 |
| 200 | 100 | ProposedB_SourceDR | 1.069 ± 0.506 | 0.517 ± 6.121 | 0.194 ± 0.095 | 4.873 ± 3.606 | 6.644 ± 3.875 |
| 200 | 100 | ProxyOnly | 1.171 ± 0.412 | 0.049 ± 5.480 | 0.264 ± 0.117 | 4.049 ± 2.799 | 5.562 ± 2.888 |
| 200 | 100 | TargetOnlyDR | 1.350 ± 0.275 | -0.237 ± 3.586 | 0.469 ± 0.089 | 0.961 ± 0.317 | 2.250 ± 0.815 |

### Extended Targeting Metrics

| m0 | m1 | Method | Top-10% Captured | Top-20% Captured | Top-30% Ratio (↑) |
|---|---|---|---|---|---|
| 25 | 0 | AnchorOnly | N/A | N/A | N/A |
| 25 | 0 | AnchorPlugin | 5.628 ± 6.990 | 4.760 ± 6.986 | 0.413 ± 1.103 |
| 25 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 25 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 25 | 0 | EntropyBalancing | 5.783 ± 6.949 | 4.879 ± 7.006 | 0.457 ± 1.071 |
| 25 | 0 | IPWTransport | 7.370 ± 6.971 | 6.137 ± 7.009 | 0.701 ± 0.524 |
| 25 | 0 | OutcomeModelTransport | 7.373 ± 6.973 | 6.137 ± 7.009 | 0.701 ± 0.522 |
| 25 | 0 | ProposedA | N/A | N/A | N/A |
| 25 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 25 | 0 | ProposedB_SourceDR | 4.546 ± 7.006 | 3.828 ± 7.075 | 0.218 ± 1.558 |
| 25 | 0 | ProxyOnly | 3.750 ± 6.867 | 3.243 ± 6.928 | 0.036 ± 1.892 |
| 25 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 25 | 25 | AnchorOnly | 4.331 ± 6.909 | 3.613 ± 6.798 | 0.212 ± 1.354 |
| 25 | 25 | AnchorPlugin | 5.260 ± 7.022 | 4.327 ± 6.933 | 0.359 ± 1.013 |
| 25 | 25 | DRLearner_PooledNoSite | 7.149 ± 6.882 | 5.837 ± 6.833 | 0.727 ± 0.307 |
| 25 | 25 | DRLearner_PooledWithSite | 7.147 ± 6.889 | 5.836 ± 6.825 | 0.727 ± 0.308 |
| 25 | 25 | EntropyBalancing | 5.555 ± 7.003 | 4.507 ± 6.897 | 0.405 ± 1.166 |
| 25 | 25 | IPWTransport | 7.005 ± 6.893 | 5.724 ± 6.819 | 0.712 ± 0.321 |
| 25 | 25 | OutcomeModelTransport | 7.004 ± 6.890 | 5.726 ± 6.815 | 0.711 ± 0.320 |
| 25 | 25 | ProposedA | 5.010 ± 7.063 | 4.152 ± 6.951 | 0.308 ± 1.171 |
| 25 | 25 | ProposedB_LinearStepB | 4.381 ± 6.847 | 3.648 ± 6.800 | 0.221 ± 1.306 |
| 25 | 25 | ProposedB_SourceDR | 4.345 ± 6.865 | 3.593 ± 6.856 | 0.255 ± 1.055 |
| 25 | 25 | ProxyOnly | 3.113 ± 6.917 | 2.656 ± 6.842 | -0.017 ± 1.773 |
| 25 | 25 | TargetOnlyDR | 4.783 ± 7.024 | 4.014 ± 6.922 | 0.265 ± 1.293 |
| 25 | 50 | AnchorOnly | 3.673 ± 7.847 | 2.892 ± 7.764 | 0.344 ± 0.943 |
| 25 | 50 | AnchorPlugin | 3.787 ± 7.696 | 2.930 ± 7.649 | 0.389 ± 0.684 |
| 25 | 50 | DRLearner_PooledNoSite | 5.941 ± 7.425 | 4.606 ± 7.445 | 0.712 ± 0.320 |
| 25 | 50 | DRLearner_PooledWithSite | 5.942 ± 7.401 | 4.612 ± 7.450 | 0.711 ± 0.327 |
| 25 | 50 | EntropyBalancing | 4.398 ± 7.820 | 3.380 ± 7.732 | 0.450 ± 0.735 |
| 25 | 50 | IPWTransport | 5.756 ± 7.429 | 4.456 ± 7.456 | 0.688 ± 0.346 |
| 25 | 50 | OutcomeModelTransport | 5.755 ± 7.430 | 4.458 ± 7.455 | 0.688 ± 0.347 |
| 25 | 50 | ProposedA | 4.222 ± 7.562 | 3.364 ± 7.551 | 0.394 ± 1.143 |
| 25 | 50 | ProposedB_LinearStepB | 3.815 ± 7.851 | 2.971 ± 7.751 | 0.342 ± 0.997 |
| 25 | 50 | ProposedB_SourceDR | 3.008 ± 7.627 | 2.245 ± 7.527 | 0.253 ± 0.773 |
| 25 | 50 | ProxyOnly | 1.949 ± 7.734 | 1.391 ± 7.681 | 0.012 ± 1.319 |
| 25 | 50 | TargetOnlyDR | 4.038 ± 7.484 | 3.167 ± 7.509 | 0.377 ± 0.864 |
| 25 | 100 | AnchorOnly | 4.891 ± 6.917 | 4.054 ± 6.693 | 0.319 ± 1.242 |
| 25 | 100 | AnchorPlugin | 4.436 ± 6.466 | 3.633 ± 6.459 | 0.240 ± 1.403 |
| 25 | 100 | DRLearner_PooledNoSite | 6.662 ± 6.554 | 5.357 ± 6.498 | 0.485 ± 1.458 |
| 25 | 100 | DRLearner_PooledWithSite | 6.638 ± 6.552 | 5.351 ± 6.489 | 0.476 ± 1.505 |
| 25 | 100 | EntropyBalancing | 4.746 ± 6.657 | 3.838 ± 6.558 | 0.230 ± 1.636 |
| 25 | 100 | IPWTransport | 6.388 ± 6.532 | 5.134 ± 6.462 | 0.413 ± 1.728 |
| 25 | 100 | OutcomeModelTransport | 6.392 ± 6.540 | 5.133 ± 6.463 | 0.413 ± 1.728 |
| 25 | 100 | ProposedA | 5.001 ± 6.674 | 4.267 ± 6.581 | 0.354 ± 1.194 |
| 25 | 100 | ProposedB_LinearStepB | 4.884 ± 6.793 | 4.096 ± 6.613 | 0.337 ± 1.147 |
| 25 | 100 | ProposedB_SourceDR | 3.655 ± 6.665 | 2.930 ± 6.660 | 0.007 ± 2.000 |
| 25 | 100 | ProxyOnly | 2.326 ± 6.436 | 1.863 ± 6.450 | -0.132 ± 2.035 |
| 25 | 100 | TargetOnlyDR | 4.520 ± 6.701 | 3.911 ± 6.615 | 0.290 ± 1.329 |
| 50 | 0 | AnchorOnly | N/A | N/A | N/A |
| 50 | 0 | AnchorPlugin | 5.111 ± 8.263 | 4.144 ± 8.135 | 0.357 ± 0.897 |
| 50 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 50 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 50 | 0 | EntropyBalancing | 5.007 ± 8.538 | 4.018 ± 8.352 | 0.349 ± 0.991 |
| 50 | 0 | IPWTransport | 6.416 ± 8.390 | 5.141 ± 8.259 | 0.594 ± 0.696 |
| 50 | 0 | OutcomeModelTransport | 6.413 ± 8.389 | 5.142 ± 8.251 | 0.598 ± 0.685 |
| 50 | 0 | ProposedA | N/A | N/A | N/A |
| 50 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 50 | 0 | ProposedB_SourceDR | 3.724 ± 8.013 | 2.968 ± 8.015 | 0.083 ± 1.290 |
| 50 | 0 | ProxyOnly | 3.340 ± 8.074 | 2.660 ± 8.064 | 0.000 ± 1.431 |
| 50 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 50 | 25 | AnchorOnly | 3.308 ± 7.850 | 2.762 ± 7.771 | -0.448 ± 5.652 |
| 50 | 25 | AnchorPlugin | 5.520 ± 7.853 | 4.505 ± 7.836 | 0.156 ± 2.493 |
| 50 | 25 | DRLearner_PooledNoSite | 6.905 ± 7.931 | 5.567 ± 7.918 | 0.639 ± 0.789 |
| 50 | 25 | DRLearner_PooledWithSite | 6.937 ± 7.945 | 5.582 ± 7.917 | 0.640 ± 0.772 |
| 50 | 25 | EntropyBalancing | 5.305 ± 7.978 | 4.303 ± 7.920 | 0.303 ± 1.355 |
| 50 | 25 | IPWTransport | 6.697 ± 7.859 | 5.395 ± 7.880 | 0.613 ± 0.863 |
| 50 | 25 | OutcomeModelTransport | 6.693 ± 7.859 | 5.395 ± 7.872 | 0.610 ± 0.879 |
| 50 | 25 | ProposedA | 4.668 ± 8.220 | 3.969 ± 8.130 | -0.031 ± 3.281 |
| 50 | 25 | ProposedB_LinearStepB | 3.878 ± 7.587 | 3.222 ± 7.586 | -0.333 ± 5.187 |
| 50 | 25 | ProposedB_SourceDR | 3.697 ± 7.817 | 3.008 ± 7.737 | -0.202 ± 3.448 |
| 50 | 25 | ProxyOnly | 3.670 ± 7.916 | 2.954 ± 7.851 | -0.232 ± 3.404 |
| 50 | 25 | TargetOnlyDR | 4.272 ± 8.167 | 3.599 ± 8.030 | -0.065 ± 2.827 |
| 50 | 50 | AnchorOnly | 3.985 ± 7.712 | 3.116 ± 7.685 | -3.071 ± 31.004 |
| 50 | 50 | AnchorPlugin | 4.662 ± 7.666 | 3.545 ± 7.544 | -2.832 ± 29.813 |
| 50 | 50 | DRLearner_PooledNoSite | 5.872 ± 7.633 | 4.521 ± 7.548 | -0.106 ± 7.477 |
| 50 | 50 | DRLearner_PooledWithSite | 5.869 ± 7.612 | 4.521 ± 7.549 | -0.119 ± 7.578 |
| 50 | 50 | EntropyBalancing | 4.132 ± 7.616 | 3.162 ± 7.553 | -2.508 ± 26.767 |
| 50 | 50 | IPWTransport | 5.635 ± 7.630 | 4.331 ± 7.552 | -0.306 ± 9.006 |
| 50 | 50 | OutcomeModelTransport | 5.632 ± 7.633 | 4.329 ± 7.555 | -0.303 ± 8.980 |
| 50 | 50 | ProposedA | 4.982 ± 7.619 | 3.848 ± 7.517 | -1.891 ± 21.855 |
| 50 | 50 | ProposedB_LinearStepB | 4.160 ± 7.938 | 3.235 ± 7.736 | -4.142 ± 40.607 |
| 50 | 50 | ProposedB_SourceDR | 3.058 ± 7.528 | 2.195 ± 7.466 | -5.275 ± 49.172 |
| 50 | 50 | ProxyOnly | 2.854 ± 7.598 | 2.166 ± 7.507 | -2.932 ± 28.456 |
| 50 | 50 | TargetOnlyDR | 4.650 ± 7.527 | 3.605 ± 7.511 | -1.526 ± 18.224 |
| 50 | 100 | AnchorOnly | 6.061 ± 7.211 | 4.940 ± 7.075 | 0.381 ± 1.191 |
| 50 | 100 | AnchorPlugin | 5.488 ± 7.039 | 4.465 ± 6.903 | 0.221 ± 1.645 |
| 50 | 100 | DRLearner_PooledNoSite | 6.924 ± 6.705 | 5.611 ± 6.720 | 0.577 ± 0.819 |
| 50 | 100 | DRLearner_PooledWithSite | 6.916 ± 6.709 | 5.606 ± 6.726 | 0.576 ± 0.828 |
| 50 | 100 | EntropyBalancing | 5.207 ± 6.727 | 4.225 ± 6.701 | 0.123 ± 2.171 |
| 50 | 100 | IPWTransport | 6.560 ± 6.545 | 5.311 ± 6.581 | 0.514 ± 0.945 |
| 50 | 100 | OutcomeModelTransport | 6.561 ± 6.542 | 5.309 ± 6.575 | 0.514 ± 0.942 |
| 50 | 100 | ProposedA | 6.425 ± 7.199 | 5.240 ± 7.107 | 0.476 ± 0.903 |
| 50 | 100 | ProposedB_LinearStepB | 6.048 ± 7.273 | 4.945 ± 7.092 | 0.329 ± 1.499 |
| 50 | 100 | ProposedB_SourceDR | 3.827 ± 6.552 | 3.152 ± 6.623 | -0.137 ± 2.508 |
| 50 | 100 | ProxyOnly | 3.395 ± 6.969 | 2.776 ± 6.943 | -0.207 ± 2.143 |
| 50 | 100 | TargetOnlyDR | 6.005 ± 7.170 | 4.932 ± 7.033 | 0.351 ± 1.406 |
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 4.476 ± 6.734 | 3.409 ± 6.782 | 0.109 ± 2.724 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 3.720 ± 7.031 | 2.759 ± 6.987 | -0.237 ± 4.408 |
| 100 | 0 | IPWTransport | 5.180 ± 7.302 | 3.944 ± 7.216 | 0.297 ± 3.041 |
| 100 | 0 | OutcomeModelTransport | 5.171 ± 7.329 | 3.940 ± 7.215 | 0.307 ± 2.983 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 2.458 ± 7.174 | 1.776 ± 7.092 | -0.577 ± 5.139 |
| 100 | 0 | ProxyOnly | 2.947 ± 6.712 | 2.174 ± 6.745 | -0.425 ± 4.496 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 25 | AnchorOnly | 2.331 ± 7.671 | 1.852 ± 7.723 | -0.380 ± 3.658 |
| 100 | 25 | AnchorPlugin | 5.133 ± 7.721 | 4.030 ± 7.642 | 0.266 ± 1.685 |
| 100 | 25 | DRLearner_PooledNoSite | 6.289 ± 7.638 | 4.927 ± 7.598 | 0.573 ± 1.045 |
| 100 | 25 | DRLearner_PooledWithSite | 6.315 ± 7.653 | 4.957 ± 7.601 | 0.577 ± 1.043 |
| 100 | 25 | EntropyBalancing | 4.724 ± 7.529 | 3.689 ± 7.491 | 0.218 ± 1.846 |
| 100 | 25 | IPWTransport | 6.090 ± 7.580 | 4.768 ± 7.563 | 0.524 ± 1.194 |
| 100 | 25 | OutcomeModelTransport | 6.083 ± 7.567 | 4.762 ± 7.549 | 0.525 ± 1.193 |
| 100 | 25 | ProposedA | 3.447 ± 7.974 | 2.972 ± 7.804 | 0.075 ± 2.070 |
| 100 | 25 | ProposedB_LinearStepB | 3.152 ± 7.914 | 2.521 ± 7.776 | -0.389 ± 4.074 |
| 100 | 25 | ProposedB_SourceDR | 3.284 ± 7.601 | 2.481 ± 7.581 | -0.214 ± 3.021 |
| 100 | 25 | ProxyOnly | 3.675 ± 7.750 | 2.872 ± 7.687 | -0.101 ± 2.595 |
| 100 | 25 | TargetOnlyDR | 2.673 ± 7.805 | 2.405 ± 7.771 | -0.224 ± 3.168 |
| 100 | 50 | AnchorOnly | 3.612 ± 7.337 | 2.850 ± 7.252 | 0.202 ± 1.230 |
| 100 | 50 | AnchorPlugin | 5.038 ± 7.429 | 3.908 ± 7.233 | 0.408 ± 0.878 |
| 100 | 50 | DRLearner_PooledNoSite | 6.263 ± 7.358 | 4.884 ± 7.289 | 0.648 ± 0.630 |
| 100 | 50 | DRLearner_PooledWithSite | 6.279 ± 7.358 | 4.898 ± 7.285 | 0.649 ± 0.639 |
| 100 | 50 | EntropyBalancing | 4.668 ± 7.347 | 3.580 ± 7.214 | 0.278 ± 1.254 |
| 100 | 50 | IPWTransport | 6.032 ± 7.419 | 4.704 ± 7.336 | 0.608 ± 0.688 |
| 100 | 50 | OutcomeModelTransport | 6.028 ± 7.416 | 4.695 ± 7.333 | 0.609 ± 0.686 |
| 100 | 50 | ProposedA | 5.202 ± 7.254 | 4.146 ± 7.193 | 0.505 ± 0.724 |
| 100 | 50 | ProposedB_LinearStepB | 4.322 ± 7.367 | 3.422 ± 7.275 | 0.326 ± 0.962 |
| 100 | 50 | ProposedB_SourceDR | 3.242 ± 7.135 | 2.544 ± 7.126 | 0.086 ± 1.330 |
| 100 | 50 | ProxyOnly | 3.523 ± 7.249 | 2.735 ± 7.203 | 0.103 ± 1.429 |
| 100 | 50 | TargetOnlyDR | 4.473 ± 7.258 | 3.594 ± 7.176 | 0.378 ± 0.887 |
| 100 | 100 | AnchorOnly | 5.486 ± 7.958 | 4.465 ± 7.861 | 0.412 ± 1.485 |
| 100 | 100 | AnchorPlugin | 5.625 ± 7.891 | 4.547 ± 7.860 | 0.331 ± 1.821 |
| 100 | 100 | DRLearner_PooledNoSite | 6.777 ± 7.904 | 5.435 ± 7.807 | 0.544 ± 1.712 |
| 100 | 100 | DRLearner_PooledWithSite | 6.787 ± 7.904 | 5.437 ± 7.814 | 0.545 ± 1.704 |
| 100 | 100 | EntropyBalancing | 4.979 ± 8.057 | 4.009 ± 7.984 | 0.138 ± 2.585 |
| 100 | 100 | IPWTransport | 6.433 ± 7.885 | 5.161 ± 7.812 | 0.466 ± 1.984 |
| 100 | 100 | OutcomeModelTransport | 6.451 ± 7.887 | 5.172 ± 7.814 | 0.468 ± 1.984 |
| 100 | 100 | ProposedA | 6.345 ± 7.986 | 5.129 ± 7.899 | 0.565 ± 0.973 |
| 100 | 100 | ProposedB_LinearStepB | 5.868 ± 7.935 | 4.794 ± 7.833 | 0.488 ± 1.169 |
| 100 | 100 | ProposedB_SourceDR | 3.835 ± 7.887 | 3.138 ± 7.785 | -0.076 ± 3.013 |
| 100 | 100 | ProxyOnly | 4.174 ± 7.810 | 3.378 ± 7.774 | 0.019 ± 2.625 |
| 100 | 100 | TargetOnlyDR | 5.953 ± 8.019 | 4.857 ± 7.903 | 0.495 ± 1.205 |
| 200 | 0 | AnchorOnly | N/A | N/A | N/A |
| 200 | 0 | AnchorPlugin | 6.548 ± 7.502 | 5.410 ± 7.409 | 0.566 ± 0.747 |
| 200 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 200 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 200 | 0 | EntropyBalancing | 6.048 ± 7.630 | 5.030 ± 7.495 | 0.529 ± 0.676 |
| 200 | 0 | IPWTransport | 7.476 ± 7.375 | 6.132 ± 7.311 | 0.756 ± 0.326 |
| 200 | 0 | OutcomeModelTransport | 7.471 ± 7.378 | 6.135 ± 7.314 | 0.756 ± 0.329 |
| 200 | 0 | ProposedA | N/A | N/A | N/A |
| 200 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 200 | 0 | ProposedB_SourceDR | 4.574 ± 7.324 | 3.890 ± 7.251 | 0.281 ± 1.159 |
| 200 | 0 | ProxyOnly | 5.290 ± 7.520 | 4.411 ± 7.425 | 0.342 ± 1.124 |
| 200 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 200 | 25 | AnchorOnly | 2.628 ± 7.868 | 2.283 ± 7.828 | -0.027 ± 1.480 |
| 200 | 25 | AnchorPlugin | 6.063 ± 7.898 | 4.995 ± 7.855 | 0.504 ± 0.762 |
| 200 | 25 | DRLearner_PooledNoSite | 7.347 ± 8.012 | 5.953 ± 7.942 | 0.748 ± 0.339 |
| 200 | 25 | DRLearner_PooledWithSite | 7.398 ± 8.006 | 5.997 ± 7.929 | 0.757 ± 0.325 |
| 200 | 25 | EntropyBalancing | 5.551 ± 8.211 | 4.475 ± 8.087 | 0.457 ± 0.635 |
| 200 | 25 | IPWTransport | 7.073 ± 8.067 | 5.748 ± 8.010 | 0.715 ± 0.391 |
| 200 | 25 | OutcomeModelTransport | 7.071 ± 8.055 | 5.747 ± 8.007 | 0.715 ± 0.394 |
| 200 | 25 | ProposedA | 3.667 ± 8.214 | 3.527 ± 8.083 | 0.203 ± 1.220 |
| 200 | 25 | ProposedB_LinearStepB | 3.429 ± 7.745 | 3.055 ± 7.802 | 0.134 ± 1.232 |
| 200 | 25 | ProposedB_SourceDR | 4.286 ± 7.969 | 3.557 ± 7.928 | 0.244 ± 1.030 |
| 200 | 25 | ProxyOnly | 4.804 ± 8.038 | 3.955 ± 8.008 | 0.294 ± 1.056 |
| 200 | 25 | TargetOnlyDR | 2.800 ± 8.116 | 2.880 ± 8.076 | 0.070 ± 1.335 |
| 200 | 50 | AnchorOnly | 4.128 ± 7.233 | 3.660 ± 7.172 | 0.220 ± 1.205 |
| 200 | 50 | AnchorPlugin | 6.464 ± 7.175 | 5.352 ± 7.166 | 0.486 ± 0.857 |
| 200 | 50 | DRLearner_PooledNoSite | 7.546 ± 7.404 | 6.204 ± 7.365 | 0.697 ± 0.519 |
| 200 | 50 | DRLearner_PooledWithSite | 7.595 ± 7.385 | 6.244 ± 7.350 | 0.707 ± 0.500 |
| 200 | 50 | EntropyBalancing | 5.701 ± 7.568 | 4.723 ± 7.495 | 0.362 ± 1.044 |
| 200 | 50 | IPWTransport | 7.178 ± 7.536 | 5.908 ± 7.438 | 0.643 ± 0.622 |
| 200 | 50 | OutcomeModelTransport | 7.187 ± 7.532 | 5.909 ± 7.439 | 0.639 ± 0.635 |
| 200 | 50 | ProposedA | 6.653 ± 7.282 | 5.615 ± 7.245 | 0.535 ± 0.686 |
| 200 | 50 | ProposedB_LinearStepB | 5.297 ± 6.912 | 4.474 ± 6.933 | 0.304 ± 1.133 |
| 200 | 50 | ProposedB_SourceDR | 4.501 ± 7.575 | 3.748 ± 7.454 | 0.077 ± 1.772 |
| 200 | 50 | ProxyOnly | 5.294 ± 7.101 | 4.434 ± 7.080 | 0.227 ± 1.419 |
| 200 | 50 | TargetOnlyDR | 4.991 ± 7.252 | 4.534 ± 7.168 | 0.310 ± 1.142 |
| 200 | 100 | AnchorOnly | 5.411 ± 6.930 | 4.565 ± 6.994 | 0.402 ± 1.238 |
| 200 | 100 | AnchorPlugin | 6.110 ± 7.108 | 5.040 ± 7.110 | 0.453 ± 1.286 |
| 200 | 100 | DRLearner_PooledNoSite | 7.450 ± 7.270 | 6.049 ± 7.217 | 0.733 ± 0.519 |
| 200 | 100 | DRLearner_PooledWithSite | 7.463 ± 7.273 | 6.062 ± 7.221 | 0.731 ± 0.543 |
| 200 | 100 | EntropyBalancing | 5.638 ± 7.371 | 4.611 ± 7.236 | 0.289 ± 2.341 |
| 200 | 100 | IPWTransport | 7.095 ± 7.250 | 5.765 ± 7.206 | 0.664 ± 0.661 |
| 200 | 100 | OutcomeModelTransport | 7.093 ± 7.247 | 5.773 ± 7.205 | 0.660 ± 0.702 |
| 200 | 100 | ProposedA | 6.852 ± 7.266 | 5.591 ± 7.232 | 0.590 ± 1.005 |
| 200 | 100 | ProposedB_LinearStepB | 6.043 ± 7.177 | 5.017 ± 7.166 | 0.512 ± 0.851 |
| 200 | 100 | ProposedB_SourceDR | 4.288 ± 6.980 | 3.504 ± 6.965 | 0.159 ± 1.608 |
| 200 | 100 | ProxyOnly | 4.917 ± 7.187 | 4.065 ± 7.085 | 0.251 ± 1.422 |
| 200 | 100 | TargetOnlyDR | 6.287 ± 7.176 | 5.255 ± 7.152 | 0.555 ± 0.870 |

---

## 7. Plots

### PEHE vs Sweep Parameter (↓ lower is better)

![PEHE](gold_sweep_pehe.png)

### ATE Error vs Sweep Parameter (↓ lower is better)

![ATE Error](gold_sweep_ate.png)

### Spearman Correlation vs Sweep Parameter (↑ higher is better)

![Correlation](gold_sweep_corr.png)

---

## 8. Key Findings

1. **Best overall PEHE:** DRLearner_PooledWithSite achieves lowest average PEHE (2.638)
2. **Proposed vs ProxyOnly:** Proposed reduces PEHE by 27.9% on average
3. **Best ranking:** DRLearner_PooledWithSite achieves highest Spearman correlation (0.818)

---

## Appendix: Configuration

```python
sweep_param = 'm0'
sweep_values = [25, 50, 100, 200]
base_scenario = {'n_proxy_total': 2000, 'C_sources': 10, 'nontransfer_scale': 0.3}
```

