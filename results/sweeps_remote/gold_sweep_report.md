# Target budget 2D grid sweep (m₀ × m₁)

**Benchmark ID:** `gold_sweep`

**Generated:** 2026-02-03 08:50

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
| **Sweep param** | `m0` | [100, 500, 1000] |
| n_proxy_total | 20000 | Total source/proxy observations |
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

- **Sweep parameter:** `m0` ∈ [100, 500, 1000]
- **Monte Carlo replicates:** 100 per scenario
- **Methods evaluated:** 12
- **Total runs:** 14400

---

## 6. Results

### Best Methods (averaged across sweep)

| Metric | Best Method | Value | Direction |
|--------|-------------|-------|----------|
| PEHE | **DRLearner_PooledWithSite** | 2.9526 | ↓ lower |
| ATE Error | **ProposedA** | 0.1133 | ↓ lower |
| Spearman ρ | **ProxyOnly** | 0.3449 | ↑ higher |
| Kendall τ | **ProxyOnly** | 0.2367 | ↑ higher |
| Qini AUC | **ProxyOnly** | 0.3588 | ↑ higher |
| Top-10% Ratio | **ProposedB_SourceDR** | -5.8691 | ↑ higher |
| Top-20% Ratio | **ProposedB_SourceDR** | -7.5092 | ↑ higher |
| Calibration R² | **AnchorOnly** | 0.0884 | ↑ higher |
| CATE ECE | **DRLearner_PooledWithSite** | 0.7877 | ↓ lower |
| Policy Value | **ProposedB_SourceDR** | 0.6154 | ↑ higher |
| Policy Regret | **DRLearner_PooledWithSite** | 0.2207 | ↓ lower |

### Core Metrics

| m0 | m1 | Method | PEHE (↓) | ATE Err (↓) | Spearman (↑) | Qini (↑) |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 5.698 ± 2.725 | 3.844 ± 3.144 | 0.621 ± 0.131 | 0.638 ± 0.131 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 9.134 ± 6.425 | 7.316 ± 7.016 | 0.603 ± 0.170 | 0.619 ± 0.171 |
| 100 | 0 | IPWTransport | 4.695 ± 2.514 | 3.154 ± 2.788 | 0.758 ± 0.138 | 0.771 ± 0.137 |
| 100 | 0 | OutcomeModelTransport | 4.705 ± 2.521 | 3.166 ± 2.798 | 0.758 ± 0.138 | 0.771 ± 0.137 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 7.203 ± 3.275 | 4.944 ± 3.997 | 0.380 ± 0.131 | 0.395 ± 0.134 |
| 100 | 0 | ProxyOnly | 6.706 ± 3.216 | 4.489 ± 3.906 | 0.441 ± 0.121 | 0.456 ± 0.123 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 4.000 ± 1.549 | 0.370 ± 0.333 | 0.616 ± 0.101 | 0.633 ± 0.101 |
| 100 | 100 | AnchorPlugin | 6.654 ± 4.447 | 4.968 ± 4.586 | 0.610 ± 0.130 | 0.627 ± 0.131 |
| 100 | 100 | DRLearner_PooledNoSite | 4.558 ± 3.747 | 2.915 ± 3.525 | 0.760 ± 0.156 | 0.774 ± 0.144 |
| 100 | 100 | DRLearner_PooledWithSite | 4.538 ± 3.677 | 2.892 ± 3.442 | 0.760 ± 0.157 | 0.774 ± 0.144 |
| 100 | 100 | EntropyBalancing | 9.707 ± 7.705 | 8.136 ± 7.865 | 0.608 ± 0.195 | 0.623 ± 0.196 |
| 100 | 100 | IPWTransport | 5.944 ± 5.739 | 4.591 ± 5.718 | 0.751 ± 0.165 | 0.766 ± 0.149 |
| 100 | 100 | OutcomeModelTransport | 5.934 ± 5.709 | 4.580 ± 5.687 | 0.751 ± 0.165 | 0.766 ± 0.148 |
| 100 | 100 | ProposedA | 3.667 ± 1.216 | 0.236 ± 0.185 | 0.719 ± 0.046 | 0.734 ± 0.044 |
| 100 | 100 | ProposedB_LinearStepB | 3.803 ± 1.237 | 0.286 ± 0.224 | 0.666 ± 0.079 | 0.682 ± 0.078 |
| 100 | 100 | ProposedB_SourceDR | 8.193 ± 4.510 | 6.301 ± 4.759 | 0.394 ± 0.145 | 0.411 ± 0.137 |
| 100 | 100 | ProxyOnly | 7.663 ± 4.936 | 5.682 ± 5.321 | 0.433 ± 0.122 | 0.448 ± 0.125 |
| 100 | 100 | TargetOnlyDR | 3.769 ± 1.212 | 0.344 ± 0.248 | 0.683 ± 0.053 | 0.699 ± 0.052 |
| 100 | 500 | AnchorOnly | 3.556 ± 0.722 | 0.154 ± 0.126 | 0.721 ± 0.049 | 0.736 ± 0.047 |
| 100 | 500 | AnchorPlugin | 5.753 ± 2.807 | 3.736 ± 3.335 | 0.623 ± 0.138 | 0.639 ± 0.139 |
| 100 | 500 | DRLearner_PooledNoSite | 3.478 ± 1.545 | 1.432 ± 1.094 | 0.764 ± 0.153 | 0.776 ± 0.153 |
| 100 | 500 | DRLearner_PooledWithSite | 3.499 ± 1.562 | 1.452 ± 1.142 | 0.763 ± 0.154 | 0.775 ± 0.153 |
| 100 | 500 | EntropyBalancing | 8.461 ± 6.579 | 6.599 ± 7.059 | 0.602 ± 0.196 | 0.618 ± 0.192 |
| 100 | 500 | IPWTransport | 5.318 ± 2.883 | 3.968 ± 2.970 | 0.745 ± 0.165 | 0.758 ± 0.165 |
| 100 | 500 | OutcomeModelTransport | 5.321 ± 2.889 | 3.967 ± 2.980 | 0.745 ± 0.165 | 0.757 ± 0.166 |
| 100 | 500 | ProposedA | 3.538 ± 0.719 | 0.152 ± 0.116 | 0.729 ± 0.041 | 0.745 ± 0.040 |
| 100 | 500 | ProposedB_LinearStepB | 3.554 ± 0.713 | 0.155 ± 0.120 | 0.724 ± 0.045 | 0.740 ± 0.044 |
| 100 | 500 | ProposedB_SourceDR | 7.430 ± 3.239 | 5.243 ± 3.875 | 0.364 ± 0.143 | 0.381 ± 0.133 |
| 100 | 500 | ProxyOnly | 14.287 ± 8.417 | 12.212 ± 9.349 | 0.388 ± 0.154 | 0.404 ± 0.153 |
| 100 | 500 | TargetOnlyDR | 3.881 ± 0.688 | 0.223 ± 0.161 | 0.651 ± 0.061 | 0.668 ± 0.060 |
| 100 | 1000 | AnchorOnly | 3.722 ± 0.696 | 0.158 ± 0.132 | 0.681 ± 0.052 | 0.697 ± 0.051 |
| 100 | 1000 | AnchorPlugin | 6.503 ± 3.673 | 4.760 ± 4.103 | 0.605 ± 0.145 | 0.621 ± 0.145 |
| 100 | 1000 | DRLearner_PooledNoSite | 3.449 ± 1.551 | 1.192 ± 1.203 | 0.742 ± 0.156 | 0.755 ± 0.154 |
| 100 | 1000 | DRLearner_PooledWithSite | 3.433 ± 1.577 | 1.153 ± 1.206 | 0.741 ± 0.156 | 0.753 ± 0.154 |
| 100 | 1000 | EntropyBalancing | 9.008 ± 5.867 | 7.298 ± 6.305 | 0.605 ± 0.160 | 0.621 ± 0.161 |
| 100 | 1000 | IPWTransport | 5.947 ± 3.929 | 4.575 ± 4.147 | 0.711 ± 0.171 | 0.724 ± 0.170 |
| 100 | 1000 | OutcomeModelTransport | 5.946 ± 3.962 | 4.565 ± 4.186 | 0.711 ± 0.171 | 0.724 ± 0.170 |
| 100 | 1000 | ProposedA | 3.701 ± 0.684 | 0.149 ± 0.127 | 0.685 ± 0.051 | 0.701 ± 0.050 |
| 100 | 1000 | ProposedB_LinearStepB | 3.721 ± 0.698 | 0.156 ± 0.129 | 0.681 ± 0.052 | 0.698 ± 0.051 |
| 100 | 1000 | ProposedB_SourceDR | 7.607 ± 3.977 | 5.403 ± 4.669 | 0.368 ± 0.141 | 0.382 ± 0.140 |
| 100 | 1000 | ProxyOnly | 30.537 ± 18.456 | 27.335 ± 20.078 | 0.345 ± 0.161 | 0.359 ± 0.161 |
| 100 | 1000 | TargetOnlyDR | 4.309 ± 0.709 | 0.231 ± 0.164 | 0.587 ± 0.067 | 0.604 ± 0.068 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 5.870 ± 2.945 | 3.917 ± 3.480 | 0.628 ± 0.128 | 0.645 ± 0.126 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 9.195 ± 6.375 | 7.454 ± 6.839 | 0.597 ± 0.190 | 0.613 ± 0.190 |
| 500 | 0 | IPWTransport | 4.964 ± 2.655 | 3.397 ± 2.790 | 0.736 ± 0.154 | 0.749 ± 0.153 |
| 500 | 0 | OutcomeModelTransport | 4.966 ± 2.662 | 3.411 ± 2.785 | 0.736 ± 0.153 | 0.749 ± 0.152 |
| 500 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 7.255 ± 3.220 | 4.947 ± 3.851 | 0.364 ± 0.112 | 0.378 ± 0.114 |
| 500 | 0 | ProxyOnly | 7.080 ± 3.284 | 5.167 ± 3.831 | 0.490 ± 0.129 | 0.506 ± 0.130 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 4.928 ± 1.203 | 0.349 ± 0.320 | 0.470 ± 0.121 | 0.484 ± 0.123 |
| 500 | 100 | AnchorPlugin | 5.942 ± 2.884 | 4.142 ± 3.484 | 0.641 ± 0.122 | 0.658 ± 0.122 |
| 500 | 100 | DRLearner_PooledNoSite | 3.912 ± 1.692 | 2.188 ± 1.780 | 0.763 ± 0.157 | 0.775 ± 0.156 |
| 500 | 100 | DRLearner_PooledWithSite | 3.475 ± 1.345 | 1.528 ± 1.236 | 0.768 ± 0.154 | 0.780 ± 0.153 |
| 500 | 100 | EntropyBalancing | 9.429 ± 8.647 | 7.820 ± 9.023 | 0.616 ± 0.205 | 0.631 ± 0.208 |
| 500 | 100 | IPWTransport | 5.443 ± 3.024 | 4.107 ± 3.344 | 0.750 ± 0.162 | 0.763 ± 0.161 |
| 500 | 100 | OutcomeModelTransport | 5.463 ± 3.023 | 4.136 ± 3.338 | 0.750 ± 0.163 | 0.762 ± 0.162 |
| 500 | 100 | ProposedA | 3.503 ± 0.603 | 0.164 ± 0.145 | 0.722 ± 0.049 | 0.737 ± 0.047 |
| 500 | 100 | ProposedB_LinearStepB | 4.407 ± 1.060 | 0.273 ± 0.206 | 0.547 ± 0.131 | 0.561 ± 0.133 |
| 500 | 100 | ProposedB_SourceDR | 7.348 ± 3.169 | 5.163 ± 4.006 | 0.394 ± 0.136 | 0.408 ± 0.139 |
| 500 | 100 | ProxyOnly | 6.366 ± 2.750 | 4.191 ± 3.515 | 0.511 ± 0.126 | 0.528 ± 0.127 |
| 500 | 100 | TargetOnlyDR | 4.205 ± 0.854 | 0.297 ± 0.248 | 0.595 ± 0.068 | 0.612 ± 0.068 |
| 500 | 500 | AnchorOnly | 3.508 ± 0.789 | 0.175 ± 0.138 | 0.733 ± 0.044 | 0.749 ± 0.042 |
| 500 | 500 | AnchorPlugin | 5.796 ± 2.956 | 3.944 ± 3.394 | 0.641 ± 0.122 | 0.658 ± 0.122 |
| 500 | 500 | DRLearner_PooledNoSite | 3.353 ± 1.412 | 1.027 ± 0.941 | 0.769 ± 0.130 | 0.782 ± 0.129 |
| 500 | 500 | DRLearner_PooledWithSite | 3.350 ± 1.415 | 1.021 ± 0.947 | 0.770 ± 0.130 | 0.782 ± 0.129 |
| 500 | 500 | EntropyBalancing | 8.699 ± 5.869 | 6.900 ± 6.245 | 0.603 ± 0.182 | 0.619 ± 0.184 |
| 500 | 500 | IPWTransport | 5.219 ± 3.178 | 3.669 ± 3.402 | 0.746 ± 0.144 | 0.760 ± 0.143 |
| 500 | 500 | OutcomeModelTransport | 5.240 ± 3.190 | 3.694 ± 3.418 | 0.746 ± 0.144 | 0.760 ± 0.143 |
| 500 | 500 | ProposedA | 3.473 ± 0.760 | 0.130 ± 0.111 | 0.742 ± 0.033 | 0.758 ± 0.031 |
| 500 | 500 | ProposedB_LinearStepB | 3.463 ± 0.755 | 0.148 ± 0.123 | 0.743 ± 0.037 | 0.759 ± 0.035 |
| 500 | 500 | ProposedB_SourceDR | 7.022 ± 3.217 | 4.784 ± 3.723 | 0.391 ± 0.117 | 0.406 ± 0.120 |
| 500 | 500 | ProxyOnly | 6.936 ± 3.502 | 4.805 ± 4.222 | 0.500 ± 0.125 | 0.517 ± 0.127 |
| 500 | 500 | TargetOnlyDR | 3.473 ± 0.763 | 0.164 ± 0.138 | 0.743 ± 0.037 | 0.759 ± 0.034 |
| 500 | 1000 | AnchorOnly | 3.301 ± 0.736 | 0.139 ± 0.118 | 0.750 ± 0.033 | 0.766 ± 0.032 |
| 500 | 1000 | AnchorPlugin | 5.628 ± 2.811 | 3.764 ± 3.261 | 0.628 ± 0.130 | 0.645 ± 0.130 |
| 500 | 1000 | DRLearner_PooledNoSite | 3.092 ± 1.204 | 0.627 ± 0.547 | 0.769 ± 0.134 | 0.783 ± 0.132 |
| 500 | 1000 | DRLearner_PooledWithSite | 3.104 ± 1.214 | 0.642 ± 0.569 | 0.768 ± 0.134 | 0.781 ± 0.133 |
| 500 | 1000 | EntropyBalancing | 8.501 ± 6.284 | 6.745 ± 6.648 | 0.594 ± 0.214 | 0.616 ± 0.188 |
| 500 | 1000 | IPWTransport | 4.827 ± 2.691 | 3.162 ± 2.972 | 0.736 ± 0.153 | 0.750 ± 0.153 |
| 500 | 1000 | OutcomeModelTransport | 4.855 ± 2.674 | 3.205 ± 2.955 | 0.735 ± 0.153 | 0.749 ± 0.152 |
| 500 | 1000 | ProposedA | 3.327 ± 0.729 | 0.139 ± 0.101 | 0.743 ± 0.033 | 0.759 ± 0.032 |
| 500 | 1000 | ProposedB_LinearStepB | 3.300 ± 0.733 | 0.137 ± 0.108 | 0.750 ± 0.035 | 0.765 ± 0.033 |
| 500 | 1000 | ProposedB_SourceDR | 7.130 ± 3.238 | 4.935 ± 3.863 | 0.379 ± 0.133 | 0.394 ± 0.136 |
| 500 | 1000 | ProxyOnly | 7.953 ± 4.406 | 5.878 ± 5.196 | 0.465 ± 0.144 | 0.480 ± 0.147 |
| 500 | 1000 | TargetOnlyDR | 3.318 ± 0.726 | 0.156 ± 0.127 | 0.745 ± 0.036 | 0.761 ± 0.035 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 5.584 ± 2.610 | 3.703 ± 3.103 | 0.628 ± 0.135 | 0.643 ± 0.136 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 9.428 ± 6.230 | 7.879 ± 6.633 | 0.589 ± 0.179 | 0.605 ± 0.178 |
| 1000 | 0 | IPWTransport | 5.083 ± 3.126 | 3.531 ± 3.436 | 0.742 ± 0.153 | 0.755 ± 0.152 |
| 1000 | 0 | OutcomeModelTransport | 5.069 ± 3.112 | 3.528 ± 3.412 | 0.743 ± 0.152 | 0.756 ± 0.151 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 7.218 ± 3.172 | 5.014 ± 3.917 | 0.396 ± 0.118 | 0.410 ± 0.120 |
| 1000 | 0 | ProxyOnly | 6.578 ± 2.620 | 4.636 ± 3.161 | 0.479 ± 0.134 | 0.495 ± 0.137 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 5.744 ± 1.743 | 0.339 ± 0.265 | 0.428 ± 0.132 | 0.442 ± 0.135 |
| 1000 | 100 | AnchorPlugin | 5.866 ± 2.696 | 4.294 ± 3.240 | 0.655 ± 0.120 | 0.671 ± 0.119 |
| 1000 | 100 | DRLearner_PooledNoSite | 3.686 ± 1.576 | 1.872 ± 1.666 | 0.761 ± 0.138 | 0.772 ± 0.138 |
| 1000 | 100 | DRLearner_PooledWithSite | 3.129 ± 1.170 | 0.946 ± 0.906 | 0.770 ± 0.134 | 0.781 ± 0.133 |
| 1000 | 100 | EntropyBalancing | 7.665 ± 5.283 | 5.898 ± 5.798 | 0.620 ± 0.168 | 0.634 ± 0.169 |
| 1000 | 100 | IPWTransport | 5.166 ± 2.879 | 3.767 ± 3.207 | 0.742 ± 0.147 | 0.754 ± 0.147 |
| 1000 | 100 | OutcomeModelTransport | 5.142 ± 2.888 | 3.729 ± 3.227 | 0.744 ± 0.146 | 0.756 ± 0.147 |
| 1000 | 100 | ProposedA | 3.576 ± 0.657 | 0.178 ± 0.141 | 0.679 ± 0.060 | 0.696 ± 0.059 |
| 1000 | 100 | ProposedB_LinearStepB | 4.834 ± 1.285 | 0.250 ± 0.226 | 0.504 ± 0.112 | 0.520 ± 0.114 |
| 1000 | 100 | ProposedB_SourceDR | 7.736 ± 4.022 | 5.765 ± 4.775 | 0.400 ± 0.125 | 0.414 ± 0.128 |
| 1000 | 100 | ProxyOnly | 6.222 ± 2.565 | 4.242 ± 3.223 | 0.510 ± 0.122 | 0.525 ± 0.124 |
| 1000 | 100 | TargetOnlyDR | 4.527 ± 0.986 | 0.290 ± 0.233 | 0.553 ± 0.079 | 0.570 ± 0.080 |
| 1000 | 500 | AnchorOnly | 3.521 ± 0.717 | 0.161 ± 0.132 | 0.705 ± 0.057 | 0.721 ± 0.056 |
| 1000 | 500 | AnchorPlugin | 5.637 ± 2.686 | 3.774 ± 3.182 | 0.629 ± 0.156 | 0.645 ± 0.156 |
| 1000 | 500 | DRLearner_PooledNoSite | 2.983 ± 1.177 | 0.651 ± 0.550 | 0.783 ± 0.140 | 0.795 ± 0.138 |
| 1000 | 500 | DRLearner_PooledWithSite | 2.953 ± 1.172 | 0.596 ± 0.502 | 0.785 ± 0.139 | 0.796 ± 0.137 |
| 1000 | 500 | EntropyBalancing | 8.421 ± 6.069 | 6.637 ± 6.574 | 0.614 ± 0.171 | 0.629 ± 0.171 |
| 1000 | 500 | IPWTransport | 4.626 ± 2.398 | 3.068 ± 2.658 | 0.755 ± 0.156 | 0.768 ± 0.154 |
| 1000 | 500 | OutcomeModelTransport | 4.632 ± 2.414 | 3.073 ± 2.676 | 0.755 ± 0.156 | 0.768 ± 0.154 |
| 1000 | 500 | ProposedA | 3.341 ± 0.655 | 0.113 ± 0.080 | 0.741 ± 0.037 | 0.757 ± 0.036 |
| 1000 | 500 | ProposedB_LinearStepB | 3.404 ± 0.657 | 0.146 ± 0.112 | 0.727 ± 0.046 | 0.742 ± 0.045 |
| 1000 | 500 | ProposedB_SourceDR | 7.598 ± 3.362 | 5.622 ± 4.061 | 0.402 ± 0.118 | 0.417 ± 0.120 |
| 1000 | 500 | ProxyOnly | 6.046 ± 2.691 | 3.741 ± 3.385 | 0.488 ± 0.141 | 0.504 ± 0.144 |
| 1000 | 500 | TargetOnlyDR | 3.400 ± 0.682 | 0.126 ± 0.098 | 0.731 ± 0.041 | 0.747 ± 0.039 |
| 1000 | 1000 | AnchorOnly | 3.569 ± 0.956 | 0.149 ± 0.121 | 0.742 ± 0.030 | 0.758 ± 0.029 |
| 1000 | 1000 | AnchorPlugin | 6.134 ± 4.395 | 4.283 ± 4.778 | 0.658 ± 0.112 | 0.675 ± 0.110 |
| 1000 | 1000 | DRLearner_PooledNoSite | 3.101 ± 1.455 | 0.683 ± 0.992 | 0.798 ± 0.122 | 0.810 ± 0.119 |
| 1000 | 1000 | DRLearner_PooledWithSite | 3.101 ± 1.457 | 0.679 ± 0.986 | 0.798 ± 0.122 | 0.809 ± 0.120 |
| 1000 | 1000 | EntropyBalancing | 8.839 ± 8.532 | 6.977 ± 8.828 | 0.628 ± 0.183 | 0.645 ± 0.181 |
| 1000 | 1000 | IPWTransport | 5.627 ± 5.077 | 4.147 ± 5.288 | 0.760 ± 0.147 | 0.773 ± 0.145 |
| 1000 | 1000 | OutcomeModelTransport | 5.613 ± 4.896 | 4.123 ± 5.125 | 0.760 ± 0.146 | 0.773 ± 0.143 |
| 1000 | 1000 | ProposedA | 3.586 ± 0.935 | 0.128 ± 0.097 | 0.733 ± 0.029 | 0.748 ± 0.028 |
| 1000 | 1000 | ProposedB_LinearStepB | 3.543 ± 0.933 | 0.128 ± 0.102 | 0.746 ± 0.029 | 0.762 ± 0.028 |
| 1000 | 1000 | ProposedB_SourceDR | 7.760 ± 4.216 | 5.610 ± 4.740 | 0.405 ± 0.114 | 0.420 ± 0.117 |
| 1000 | 1000 | ProxyOnly | 7.316 ± 4.769 | 5.143 ± 5.331 | 0.493 ± 0.121 | 0.510 ± 0.122 |
| 1000 | 1000 | TargetOnlyDR | 3.565 ± 0.938 | 0.135 ± 0.106 | 0.739 ± 0.029 | 0.755 ± 0.028 |

### Targeting / Ranking Metrics

| m0 | m1 | Method | Top-10% (↑) | Top-20% (↑) | Kendall (↑) |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 0.081 ± 3.739 | 0.049 ± 2.115 | 0.448 ± 0.106 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 0.034 ± 3.598 | -0.239 ± 4.146 | 0.437 ± 0.138 |
| 100 | 0 | IPWTransport | 0.281 ± 3.647 | 0.435 ± 1.392 | 0.576 ± 0.127 |
| 100 | 0 | OutcomeModelTransport | 0.281 ± 3.647 | 0.435 ± 1.391 | 0.576 ± 0.126 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | -0.587 ± 6.022 | -0.958 ± 6.016 | 0.262 ± 0.093 |
| 100 | 0 | ProxyOnly | -0.175 ± 3.684 | -0.481 ± 3.733 | 0.305 ± 0.088 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 0.308 ± 1.564 | 0.390 ± 1.172 | 0.441 ± 0.082 |
| 100 | 100 | AnchorPlugin | 0.270 ± 1.676 | 0.318 ± 1.286 | 0.438 ± 0.103 |
| 100 | 100 | DRLearner_PooledNoSite | 0.516 ± 1.300 | 0.521 ± 1.095 | 0.578 ± 0.135 |
| 100 | 100 | DRLearner_PooledWithSite | 0.514 ± 1.311 | 0.521 ± 1.094 | 0.578 ± 0.135 |
| 100 | 100 | EntropyBalancing | 0.298 ± 1.583 | 0.320 ± 1.262 | 0.442 ± 0.155 |
| 100 | 100 | IPWTransport | 0.496 ± 1.362 | 0.509 ± 1.131 | 0.570 ± 0.140 |
| 100 | 100 | OutcomeModelTransport | 0.496 ± 1.362 | 0.508 ± 1.131 | 0.571 ± 0.140 |
| 100 | 100 | ProposedA | 0.453 ± 1.495 | 0.559 ± 0.750 | 0.528 ± 0.042 |
| 100 | 100 | ProposedB_LinearStepB | 0.414 ± 1.333 | 0.495 ± 0.850 | 0.482 ± 0.066 |
| 100 | 100 | ProposedB_SourceDR | -0.064 ± 2.250 | -0.035 ± 1.792 | 0.272 ± 0.103 |
| 100 | 100 | ProxyOnly | -0.083 ± 2.471 | 0.038 ± 1.666 | 0.299 ± 0.087 |
| 100 | 100 | TargetOnlyDR | 0.396 ± 1.557 | 0.503 ± 0.859 | 0.495 ± 0.046 |
| 100 | 500 | AnchorOnly | 0.552 ± 0.822 | 0.236 ± 2.823 | 0.530 ± 0.044 |
| 100 | 500 | AnchorPlugin | 0.410 ± 1.053 | 0.183 ± 2.245 | 0.449 ± 0.109 |
| 100 | 500 | DRLearner_PooledNoSite | 0.630 ± 0.634 | 0.590 ± 0.749 | 0.584 ± 0.137 |
| 100 | 500 | DRLearner_PooledWithSite | 0.628 ± 0.645 | 0.587 ± 0.757 | 0.583 ± 0.137 |
| 100 | 500 | EntropyBalancing | 0.395 ± 0.852 | 0.216 ± 1.765 | 0.437 ± 0.155 |
| 100 | 500 | IPWTransport | 0.605 ± 0.664 | 0.559 ± 0.782 | 0.566 ± 0.143 |
| 100 | 500 | OutcomeModelTransport | 0.603 ± 0.662 | 0.559 ± 0.782 | 0.566 ± 0.144 |
| 100 | 500 | ProposedA | 0.560 ± 0.819 | 0.201 ± 3.156 | 0.538 ± 0.039 |
| 100 | 500 | ProposedB_LinearStepB | 0.550 ± 0.841 | 0.216 ± 3.000 | 0.533 ± 0.042 |
| 100 | 500 | ProposedB_SourceDR | -0.126 ± 2.488 | -0.564 ± 5.002 | 0.251 ± 0.100 |
| 100 | 500 | ProxyOnly | -0.086 ± 2.135 | -0.789 ± 6.229 | 0.268 ± 0.110 |
| 100 | 500 | TargetOnlyDR | 0.376 ± 1.278 | 0.053 ± 3.348 | 0.471 ± 0.052 |
| 100 | 1000 | AnchorOnly | 0.404 ± 1.690 | 0.661 ± 0.440 | 0.495 ± 0.045 |
| 100 | 1000 | AnchorPlugin | 0.227 ± 2.002 | 0.529 ± 0.818 | 0.435 ± 0.116 |
| 100 | 1000 | DRLearner_PooledNoSite | 0.343 ± 2.229 | 0.658 ± 0.832 | 0.563 ± 0.142 |
| 100 | 1000 | DRLearner_PooledWithSite | 0.340 ± 2.254 | 0.657 ± 0.834 | 0.562 ± 0.142 |
| 100 | 1000 | EntropyBalancing | 0.016 ± 3.475 | 0.505 ± 0.981 | 0.437 ± 0.130 |
| 100 | 1000 | IPWTransport | 0.278 ± 2.537 | 0.627 ± 0.884 | 0.535 ± 0.150 |
| 100 | 1000 | OutcomeModelTransport | 0.279 ± 2.538 | 0.627 ± 0.884 | 0.534 ± 0.150 |
| 100 | 1000 | ProposedA | 0.409 ± 1.652 | 0.664 ± 0.429 | 0.498 ± 0.044 |
| 100 | 1000 | ProposedB_LinearStepB | 0.427 ± 1.510 | 0.668 ± 0.410 | 0.496 ± 0.045 |
| 100 | 1000 | ProposedB_SourceDR | -0.300 ± 3.382 | 0.260 ± 1.180 | 0.253 ± 0.100 |
| 100 | 1000 | ProxyOnly | -0.261 ± 3.417 | 0.230 ± 1.107 | 0.237 ± 0.113 |
| 100 | 1000 | TargetOnlyDR | 0.166 ± 2.308 | 0.559 ± 0.523 | 0.418 ± 0.054 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | -2.465 ± 26.484 | -0.390 ± 8.154 | 0.454 ± 0.104 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | -3.040 ± 32.340 | -0.080 ± 4.473 | 0.433 ± 0.150 |
| 500 | 0 | IPWTransport | -2.422 ± 28.958 | 0.300 ± 3.098 | 0.557 ± 0.139 |
| 500 | 0 | OutcomeModelTransport | -2.364 ± 28.399 | 0.298 ± 3.116 | 0.557 ± 0.138 |
| 500 | 0 | ProposedA | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | -5.869 ± 54.977 | -0.918 ± 9.038 | 0.250 ± 0.080 |
| 500 | 0 | ProxyOnly | -4.582 ± 45.250 | -0.876 ± 10.609 | 0.342 ± 0.096 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 0.136 ± 1.572 | 0.277 ± 1.170 | 0.329 ± 0.090 |
| 500 | 100 | AnchorPlugin | 0.447 ± 0.886 | 0.467 ± 1.060 | 0.464 ± 0.099 |
| 500 | 100 | DRLearner_PooledNoSite | 0.622 ± 0.840 | 0.666 ± 0.773 | 0.585 ± 0.143 |
| 500 | 100 | DRLearner_PooledWithSite | 0.635 ± 0.762 | 0.666 ± 0.795 | 0.590 ± 0.141 |
| 500 | 100 | EntropyBalancing | 0.239 ± 2.319 | 0.457 ± 1.201 | 0.451 ± 0.164 |
| 500 | 100 | IPWTransport | 0.610 ± 0.861 | 0.654 ± 0.785 | 0.573 ± 0.146 |
| 500 | 100 | OutcomeModelTransport | 0.611 ± 0.861 | 0.655 ± 0.784 | 0.572 ± 0.147 |
| 500 | 100 | ProposedA | 0.521 ± 0.908 | 0.569 ± 0.883 | 0.531 ± 0.044 |
| 500 | 100 | ProposedB_LinearStepB | 0.194 ± 1.760 | 0.360 ± 1.038 | 0.389 ± 0.101 |
| 500 | 100 | ProposedB_SourceDR | 0.002 ± 1.891 | 0.130 ± 1.600 | 0.271 ± 0.097 |
| 500 | 100 | ProxyOnly | 0.227 ± 1.268 | 0.253 ± 1.564 | 0.359 ± 0.094 |
| 500 | 100 | TargetOnlyDR | 0.323 ± 1.100 | 0.410 ± 1.087 | 0.423 ± 0.055 |
| 500 | 500 | AnchorOnly | 0.532 ± 1.192 | 0.189 ± 2.706 | 0.541 ± 0.040 |
| 500 | 500 | AnchorPlugin | 0.387 ± 1.127 | -0.315 ± 4.874 | 0.464 ± 0.102 |
| 500 | 500 | DRLearner_PooledNoSite | 0.665 ± 0.487 | 0.151 ± 3.852 | 0.587 ± 0.122 |
| 500 | 500 | DRLearner_PooledWithSite | 0.665 ± 0.481 | 0.160 ± 3.753 | 0.587 ± 0.122 |
| 500 | 500 | EntropyBalancing | 0.312 ± 1.115 | -0.647 ± 6.153 | 0.438 ± 0.146 |
| 500 | 500 | IPWTransport | 0.625 ± 0.564 | 0.064 ± 4.202 | 0.565 ± 0.130 |
| 500 | 500 | OutcomeModelTransport | 0.627 ± 0.568 | 0.057 ± 4.287 | 0.565 ± 0.131 |
| 500 | 500 | ProposedA | 0.547 ± 1.050 | 0.140 ± 3.094 | 0.549 ± 0.031 |
| 500 | 500 | ProposedB_LinearStepB | 0.554 ± 1.028 | 0.158 ± 2.997 | 0.550 ± 0.034 |
| 500 | 500 | ProposedB_SourceDR | -0.093 ± 2.508 | -1.046 ± 7.152 | 0.269 ± 0.084 |
| 500 | 500 | ProxyOnly | 0.086 ± 1.972 | -0.922 ± 7.671 | 0.350 ± 0.094 |
| 500 | 500 | TargetOnlyDR | 0.540 ± 1.288 | 0.206 ± 2.655 | 0.551 ± 0.034 |
| 500 | 1000 | AnchorOnly | 0.390 ± 3.351 | 0.480 ± 2.353 | 0.557 ± 0.032 |
| 500 | 1000 | AnchorPlugin | 0.301 ± 2.947 | 0.116 ± 4.581 | 0.454 ± 0.106 |
| 500 | 1000 | DRLearner_PooledNoSite | 0.638 ± 1.266 | 0.457 ± 2.754 | 0.586 ± 0.121 |
| 500 | 1000 | DRLearner_PooledWithSite | 0.636 ± 1.266 | 0.456 ± 2.754 | 0.585 ± 0.122 |
| 500 | 1000 | EntropyBalancing | 0.401 ± 1.760 | 0.173 ± 3.183 | 0.432 ± 0.167 |
| 500 | 1000 | IPWTransport | 0.586 ± 1.417 | 0.393 ± 3.011 | 0.555 ± 0.133 |
| 500 | 1000 | OutcomeModelTransport | 0.580 ± 1.466 | 0.395 ± 2.982 | 0.554 ± 0.133 |
| 500 | 1000 | ProposedA | 0.378 ± 3.431 | 0.298 ± 4.077 | 0.550 ± 0.032 |
| 500 | 1000 | ProposedB_LinearStepB | 0.380 ± 3.474 | 0.458 ± 2.590 | 0.556 ± 0.034 |
| 500 | 1000 | ProposedB_SourceDR | -0.398 ± 6.895 | -0.461 ± 7.122 | 0.261 ± 0.095 |
| 500 | 1000 | ProxyOnly | -0.072 ± 4.550 | -0.461 ± 8.048 | 0.324 ± 0.108 |
| 500 | 1000 | TargetOnlyDR | 0.352 ± 3.684 | 0.416 ± 3.001 | 0.553 ± 0.035 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | -0.173 ± 4.550 | -3.500 ± 29.066 | 0.454 ± 0.111 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | -0.339 ± 5.430 | -5.180 ± 44.086 | 0.425 ± 0.141 |
| 1000 | 0 | IPWTransport | 0.144 ± 3.906 | -1.560 ± 16.148 | 0.563 ± 0.137 |
| 1000 | 0 | OutcomeModelTransport | 0.161 ± 3.770 | -1.592 ± 16.431 | 0.563 ± 0.137 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | -0.758 ± 6.121 | -7.509 ± 53.997 | 0.273 ± 0.085 |
| 1000 | 0 | ProxyOnly | -0.672 ± 6.824 | -5.077 ± 38.688 | 0.335 ± 0.101 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | -2.627 ± 16.479 | -0.408 ± 4.685 | 0.299 ± 0.098 |
| 1000 | 100 | AnchorPlugin | -1.032 ± 9.597 | 0.020 ± 3.528 | 0.476 ± 0.099 |
| 1000 | 100 | DRLearner_PooledNoSite | -0.454 ± 6.834 | 0.371 ± 2.205 | 0.578 ± 0.125 |
| 1000 | 100 | DRLearner_PooledWithSite | -0.367 ± 6.440 | 0.398 ± 2.108 | 0.587 ± 0.122 |
| 1000 | 100 | EntropyBalancing | -1.094 ± 9.607 | 0.042 ± 3.197 | 0.451 ± 0.139 |
| 1000 | 100 | IPWTransport | -0.558 ± 7.359 | 0.335 ± 2.249 | 0.561 ± 0.129 |
| 1000 | 100 | OutcomeModelTransport | -0.573 ± 7.451 | 0.339 ± 2.256 | 0.562 ± 0.129 |
| 1000 | 100 | ProposedA | -1.113 ± 9.979 | 0.205 ± 2.678 | 0.494 ± 0.051 |
| 1000 | 100 | ProposedB_LinearStepB | -2.694 ± 17.610 | -0.198 ± 3.931 | 0.356 ± 0.084 |
| 1000 | 100 | ProposedB_SourceDR | -2.635 ± 17.096 | -0.534 ± 4.821 | 0.276 ± 0.091 |
| 1000 | 100 | ProxyOnly | -2.657 ± 18.896 | -0.362 ± 4.970 | 0.358 ± 0.092 |
| 1000 | 100 | TargetOnlyDR | -2.388 ± 16.252 | -0.206 ± 4.470 | 0.391 ± 0.062 |
| 1000 | 500 | AnchorOnly | -0.320 ± 8.198 | 0.658 ± 0.551 | 0.515 ± 0.050 |
| 1000 | 500 | AnchorPlugin | -0.113 ± 5.373 | 0.583 ± 0.464 | 0.456 ± 0.125 |
| 1000 | 500 | DRLearner_PooledNoSite | 0.491 ± 1.940 | 0.761 ± 0.284 | 0.604 ± 0.132 |
| 1000 | 500 | DRLearner_PooledWithSite | 0.497 ± 1.911 | 0.764 ± 0.283 | 0.605 ± 0.131 |
| 1000 | 500 | EntropyBalancing | -0.258 ± 6.254 | 0.580 ± 0.443 | 0.446 ± 0.141 |
| 1000 | 500 | IPWTransport | 0.378 ± 2.639 | 0.732 ± 0.305 | 0.576 ± 0.140 |
| 1000 | 500 | OutcomeModelTransport | 0.381 ± 2.626 | 0.732 ± 0.304 | 0.576 ± 0.140 |
| 1000 | 500 | ProposedA | 0.245 ± 3.414 | 0.679 ± 0.508 | 0.548 ± 0.035 |
| 1000 | 500 | ProposedB_LinearStepB | -0.179 ± 7.335 | 0.683 ± 0.446 | 0.535 ± 0.042 |
| 1000 | 500 | ProposedB_SourceDR | -0.554 ± 6.012 | 0.285 ± 1.080 | 0.277 ± 0.085 |
| 1000 | 500 | ProxyOnly | -0.613 ± 8.201 | 0.411 ± 0.750 | 0.342 ± 0.106 |
| 1000 | 500 | TargetOnlyDR | 0.172 ± 3.933 | 0.673 ± 0.527 | 0.539 ± 0.038 |
| 1000 | 1000 | AnchorOnly | 0.519 ± 1.179 | 0.649 ± 0.414 | 0.549 ± 0.028 |
| 1000 | 1000 | AnchorPlugin | 0.175 ± 3.012 | 0.575 ± 0.435 | 0.478 ± 0.094 |
| 1000 | 1000 | DRLearner_PooledNoSite | 0.484 ± 1.945 | 0.737 ± 0.346 | 0.617 ± 0.119 |
| 1000 | 1000 | DRLearner_PooledWithSite | 0.482 ± 1.954 | 0.736 ± 0.347 | 0.616 ± 0.120 |
| 1000 | 1000 | EntropyBalancing | 0.110 ± 2.941 | 0.501 ± 0.554 | 0.460 ± 0.152 |
| 1000 | 1000 | IPWTransport | 0.401 ± 2.239 | 0.687 ± 0.411 | 0.580 ± 0.135 |
| 1000 | 1000 | OutcomeModelTransport | 0.407 ± 2.229 | 0.688 ± 0.410 | 0.580 ± 0.134 |
| 1000 | 1000 | ProposedA | 0.430 ± 1.590 | 0.644 ± 0.427 | 0.540 ± 0.027 |
| 1000 | 1000 | ProposedB_LinearStepB | 0.514 ± 1.188 | 0.661 ± 0.401 | 0.553 ± 0.027 |
| 1000 | 1000 | ProposedB_SourceDR | -0.242 ± 3.499 | 0.215 ± 0.919 | 0.279 ± 0.082 |
| 1000 | 1000 | ProxyOnly | -0.176 ± 4.045 | 0.366 ± 0.653 | 0.345 ± 0.090 |
| 1000 | 1000 | TargetOnlyDR | 0.440 ± 1.628 | 0.653 ± 0.403 | 0.546 ± 0.027 |

### ATE Estimation

| m0 | m1 | Method | ATE Est | ATE Err (↓) | ATE Bias |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | -0.862 ± 4.298 | 3.844 ± 3.144 | -0.162 ± 4.979 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 0.563 ± 9.388 | 7.316 ± 7.016 | 1.263 ± 10.084 |
| 100 | 0 | IPWTransport | -0.901 ± 5.468 | 3.154 ± 2.788 | -0.201 ± 4.217 |
| 100 | 0 | OutcomeModelTransport | -0.917 ± 5.468 | 3.166 ± 2.798 | -0.217 ± 4.231 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | -0.672 ± 2.475 | 4.944 ± 3.997 | 0.028 ± 6.377 |
| 100 | 0 | ProxyOnly | -0.771 ± 7.111 | 4.489 ± 3.906 | -0.071 ± 5.967 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 0.629 ± 8.745 | 0.370 ± 0.333 | 0.147 ± 0.477 |
| 100 | 100 | AnchorPlugin | 0.406 ± 5.546 | 4.968 ± 4.586 | -0.076 ± 6.779 |
| 100 | 100 | DRLearner_PooledNoSite | 0.323 ± 6.812 | 2.915 ± 3.525 | -0.159 ± 4.580 |
| 100 | 100 | DRLearner_PooledWithSite | 0.299 ± 6.801 | 2.892 ± 3.442 | -0.183 ± 4.501 |
| 100 | 100 | EntropyBalancing | 0.976 ± 10.982 | 8.136 ± 7.865 | 0.494 ± 11.334 |
| 100 | 100 | IPWTransport | 0.253 ± 7.082 | 4.591 ± 5.718 | -0.230 ± 7.344 |
| 100 | 100 | OutcomeModelTransport | 0.240 ± 7.075 | 4.580 ± 5.687 | -0.242 ± 7.313 |
| 100 | 100 | ProposedA | 0.519 ± 8.784 | 0.236 ± 0.185 | 0.036 ± 0.299 |
| 100 | 100 | ProposedB_LinearStepB | 0.534 ± 8.779 | 0.286 ± 0.224 | 0.052 ± 0.361 |
| 100 | 100 | ProposedB_SourceDR | -0.018 ± 2.955 | 6.301 ± 4.759 | -0.500 ± 7.906 |
| 100 | 100 | ProxyOnly | 0.758 ± 8.533 | 5.682 ± 5.321 | 0.276 ± 7.800 |
| 100 | 100 | TargetOnlyDR | 0.615 ± 8.786 | 0.344 ± 0.248 | 0.133 ± 0.404 |
| 100 | 500 | AnchorOnly | -0.648 ± 7.198 | 0.154 ± 0.126 | -0.006 ± 0.199 |
| 100 | 500 | AnchorPlugin | -0.454 ± 4.589 | 3.736 ± 3.335 | 0.189 ± 5.018 |
| 100 | 500 | DRLearner_PooledNoSite | -0.500 ± 6.455 | 1.432 ± 1.094 | 0.143 ± 1.802 |
| 100 | 500 | DRLearner_PooledWithSite | -0.524 ± 6.400 | 1.452 ± 1.142 | 0.119 ± 1.849 |
| 100 | 500 | EntropyBalancing | 0.612 ± 9.540 | 6.599 ± 7.059 | 1.255 ± 9.603 |
| 100 | 500 | IPWTransport | -0.305 ± 6.045 | 3.968 ± 2.970 | 0.338 ± 4.961 |
| 100 | 500 | OutcomeModelTransport | -0.308 ± 6.031 | 3.967 ± 2.980 | 0.335 ± 4.966 |
| 100 | 500 | ProposedA | -0.655 ± 7.210 | 0.152 ± 0.116 | -0.013 ± 0.191 |
| 100 | 500 | ProposedB_LinearStepB | -0.653 ± 7.205 | 0.155 ± 0.120 | -0.011 ± 0.196 |
| 100 | 500 | ProposedB_SourceDR | -0.342 ± 2.339 | 5.243 ± 3.875 | 0.301 ± 6.534 |
| 100 | 500 | ProxyOnly | -2.334 ± 19.111 | 12.212 ± 9.349 | -1.691 ± 15.335 |
| 100 | 500 | TargetOnlyDR | -0.622 ± 7.238 | 0.223 ± 0.161 | 0.020 ± 0.276 |
| 100 | 1000 | AnchorOnly | 0.590 ± 8.103 | 0.158 ± 0.132 | -0.002 ± 0.207 |
| 100 | 1000 | AnchorPlugin | -0.378 ± 5.519 | 4.760 ± 4.103 | -0.970 ± 6.227 |
| 100 | 1000 | DRLearner_PooledNoSite | 0.384 ± 7.359 | 1.192 ± 1.203 | -0.208 ± 1.684 |
| 100 | 1000 | DRLearner_PooledWithSite | 0.420 ± 7.348 | 1.153 ± 1.206 | -0.172 ± 1.664 |
| 100 | 1000 | EntropyBalancing | -0.040 ± 11.085 | 7.298 ± 6.305 | -0.632 ± 9.651 |
| 100 | 1000 | IPWTransport | -0.342 ± 6.947 | 4.575 ± 4.147 | -0.935 ± 6.120 |
| 100 | 1000 | OutcomeModelTransport | -0.336 ± 6.947 | 4.565 ± 4.186 | -0.928 ± 6.140 |
| 100 | 1000 | ProposedA | 0.591 ± 8.127 | 0.149 ± 0.127 | -0.001 ± 0.196 |
| 100 | 1000 | ProposedB_LinearStepB | 0.588 ± 8.119 | 0.156 ± 0.129 | -0.004 ± 0.203 |
| 100 | 1000 | ProposedB_SourceDR | -0.086 ± 2.926 | 5.403 ± 4.669 | -0.678 ± 7.128 |
| 100 | 1000 | ProxyOnly | -1.064 ± 37.231 | 27.335 ± 20.078 | -1.656 ± 33.986 |
| 100 | 1000 | TargetOnlyDR | 0.604 ± 8.118 | 0.231 ± 0.164 | 0.012 ± 0.284 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 0.407 ± 5.332 | 3.917 ± 3.480 | -0.387 ± 5.240 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 1.398 ± 11.875 | 7.454 ± 6.839 | 0.604 ± 10.125 |
| 500 | 0 | IPWTransport | 0.758 ± 6.196 | 3.397 ± 2.790 | -0.036 ± 4.409 |
| 500 | 0 | OutcomeModelTransport | 0.760 ± 6.157 | 3.411 ± 2.785 | -0.035 ± 4.417 |
| 500 | 0 | ProposedA | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 0.081 ± 3.059 | 4.947 ± 3.851 | -0.714 ± 6.248 |
| 500 | 0 | ProxyOnly | 0.570 ± 8.096 | 5.167 ± 3.831 | -0.224 ± 6.449 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 0.057 ± 7.212 | 0.349 ± 0.320 | -0.036 ± 0.473 |
| 500 | 100 | AnchorPlugin | -0.074 ± 4.926 | 4.142 ± 3.484 | -0.167 ± 5.425 |
| 500 | 100 | DRLearner_PooledNoSite | 0.219 ± 6.105 | 2.188 ± 1.780 | 0.127 ± 2.826 |
| 500 | 100 | DRLearner_PooledWithSite | 0.199 ± 6.373 | 1.528 ± 1.236 | 0.106 ± 1.968 |
| 500 | 100 | EntropyBalancing | 0.589 ± 11.905 | 7.820 ± 9.023 | 0.497 ± 11.956 |
| 500 | 100 | IPWTransport | 0.403 ± 6.070 | 4.107 ± 3.344 | 0.310 ± 5.303 |
| 500 | 100 | OutcomeModelTransport | 0.431 ± 6.069 | 4.136 ± 3.338 | 0.338 ± 5.321 |
| 500 | 100 | ProposedA | 0.071 ± 7.340 | 0.164 ± 0.145 | -0.022 ± 0.219 |
| 500 | 100 | ProposedB_LinearStepB | 0.056 ± 7.312 | 0.273 ± 0.206 | -0.036 ± 0.341 |
| 500 | 100 | ProposedB_SourceDR | 0.586 ± 2.889 | 5.163 ± 4.006 | 0.494 ± 6.536 |
| 500 | 100 | ProxyOnly | -0.170 ± 5.383 | 4.191 ± 3.515 | -0.262 ± 5.480 |
| 500 | 100 | TargetOnlyDR | 0.037 ± 7.322 | 0.297 ± 0.248 | -0.056 ± 0.384 |
| 500 | 500 | AnchorOnly | -1.273 ± 6.373 | 0.175 ± 0.138 | 0.018 ± 0.223 |
| 500 | 500 | AnchorPlugin | 0.140 ± 4.891 | 3.944 ± 3.394 | 1.431 ± 5.016 |
| 500 | 500 | DRLearner_PooledNoSite | -1.025 ± 5.692 | 1.027 ± 0.941 | 0.266 ± 1.371 |
| 500 | 500 | DRLearner_PooledWithSite | -1.028 ± 5.686 | 1.021 ± 0.947 | 0.263 ± 1.371 |
| 500 | 500 | EntropyBalancing | 0.736 ± 9.990 | 6.900 ± 6.245 | 2.027 ± 9.107 |
| 500 | 500 | IPWTransport | -0.361 ± 5.392 | 3.669 ± 3.402 | 0.930 ± 4.929 |
| 500 | 500 | OutcomeModelTransport | -0.348 ± 5.342 | 3.694 ± 3.418 | 0.943 ± 4.957 |
| 500 | 500 | ProposedA | -1.291 ± 6.402 | 0.130 ± 0.111 | -0.000 ± 0.172 |
| 500 | 500 | ProposedB_LinearStepB | -1.278 ± 6.405 | 0.148 ± 0.123 | 0.013 ± 0.193 |
| 500 | 500 | ProposedB_SourceDR | -0.198 ± 3.010 | 4.784 ± 3.723 | 1.093 ± 5.981 |
| 500 | 500 | ProxyOnly | 0.381 ± 7.445 | 4.805 ± 4.222 | 1.672 ± 6.190 |
| 500 | 500 | TargetOnlyDR | -1.297 ± 6.407 | 0.164 ± 0.138 | -0.006 ± 0.215 |
| 500 | 1000 | AnchorOnly | 1.131 ± 6.903 | 0.139 ± 0.118 | 0.010 ± 0.183 |
| 500 | 1000 | AnchorPlugin | 0.998 ± 4.951 | 3.764 ± 3.261 | -0.122 ± 4.993 |
| 500 | 1000 | DRLearner_PooledNoSite | 1.135 ± 6.523 | 0.627 ± 0.547 | 0.014 ± 0.834 |
| 500 | 1000 | DRLearner_PooledWithSite | 1.131 ± 6.512 | 0.642 ± 0.569 | 0.010 ± 0.860 |
| 500 | 1000 | EntropyBalancing | 2.372 ± 9.544 | 6.745 ± 6.648 | 1.251 ± 9.411 |
| 500 | 1000 | IPWTransport | 1.171 ± 5.983 | 3.162 ± 2.972 | 0.050 ± 4.351 |
| 500 | 1000 | OutcomeModelTransport | 1.176 ± 6.011 | 3.205 ± 2.955 | 0.055 ± 4.371 |
| 500 | 1000 | ProposedA | 1.121 ± 6.906 | 0.139 ± 0.101 | 0.000 ± 0.172 |
| 500 | 1000 | ProposedB_LinearStepB | 1.122 ± 6.898 | 0.137 ± 0.108 | 0.001 ± 0.175 |
| 500 | 1000 | ProposedB_SourceDR | 0.262 ± 2.990 | 4.935 ± 3.863 | -0.859 ± 6.227 |
| 500 | 1000 | ProxyOnly | 2.167 ± 10.082 | 5.878 ± 5.196 | 1.046 ± 7.797 |
| 500 | 1000 | TargetOnlyDR | 1.130 ± 6.914 | 0.156 ± 0.127 | 0.009 ± 0.202 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | -0.785 ± 4.704 | 3.703 ± 3.103 | 0.386 ± 4.830 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | -2.392 ± 9.838 | 7.879 ± 6.633 | -1.221 ± 10.257 |
| 1000 | 0 | IPWTransport | -1.221 ± 5.577 | 3.531 ± 3.436 | -0.050 ± 4.940 |
| 1000 | 0 | OutcomeModelTransport | -1.188 ± 5.623 | 3.528 ± 3.412 | -0.017 ± 4.921 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | -0.030 ± 3.090 | 5.014 ± 3.917 | 1.141 ± 6.278 |
| 1000 | 0 | ProxyOnly | -1.220 ± 7.473 | 4.636 ± 3.161 | -0.049 ± 5.630 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | -1.640 ± 8.310 | 0.339 ± 0.265 | 0.056 ± 0.428 |
| 1000 | 100 | AnchorPlugin | -1.394 ± 5.247 | 4.294 ± 3.240 | 0.302 ± 5.388 |
| 1000 | 100 | DRLearner_PooledNoSite | -1.880 ± 6.940 | 1.872 ± 1.666 | -0.184 ± 2.506 |
| 1000 | 100 | DRLearner_PooledWithSite | -1.810 ± 7.522 | 0.946 ± 0.906 | -0.114 ± 1.308 |
| 1000 | 100 | EntropyBalancing | -1.252 ± 9.863 | 5.898 ± 5.798 | 0.444 ± 8.280 |
| 1000 | 100 | IPWTransport | -2.111 ± 6.270 | 3.767 ± 3.207 | -0.415 ± 4.944 |
| 1000 | 100 | OutcomeModelTransport | -2.081 ± 6.281 | 3.729 ± 3.227 | -0.385 ± 4.930 |
| 1000 | 100 | ProposedA | -1.650 ± 8.304 | 0.178 ± 0.141 | 0.046 ± 0.223 |
| 1000 | 100 | ProposedB_LinearStepB | -1.636 ± 8.329 | 0.250 ± 0.226 | 0.059 ± 0.332 |
| 1000 | 100 | ProposedB_SourceDR | -0.631 ± 3.047 | 5.765 ± 4.775 | 1.065 ± 7.431 |
| 1000 | 100 | ProxyOnly | -1.463 ± 5.491 | 4.242 ± 3.223 | 0.233 ± 5.340 |
| 1000 | 100 | TargetOnlyDR | -1.684 ± 8.385 | 0.290 ± 0.233 | 0.012 ± 0.373 |
| 1000 | 500 | AnchorOnly | 0.258 ± 7.435 | 0.161 ± 0.132 | 0.005 ± 0.209 |
| 1000 | 500 | AnchorPlugin | 0.142 ± 5.188 | 3.774 ± 3.182 | -0.112 ± 4.950 |
| 1000 | 500 | DRLearner_PooledNoSite | 0.192 ± 7.130 | 0.651 ± 0.550 | -0.061 ± 0.853 |
| 1000 | 500 | DRLearner_PooledWithSite | 0.201 ± 7.150 | 0.596 ± 0.502 | -0.052 ± 0.780 |
| 1000 | 500 | EntropyBalancing | -1.509 ± 10.199 | 6.637 ± 6.574 | -1.762 ± 9.197 |
| 1000 | 500 | IPWTransport | -0.242 ± 6.568 | 3.068 ± 2.658 | -0.496 ± 4.041 |
| 1000 | 500 | OutcomeModelTransport | -0.176 ± 6.550 | 3.073 ± 2.676 | -0.429 ± 4.064 |
| 1000 | 500 | ProposedA | 0.253 ± 7.499 | 0.113 ± 0.080 | -0.000 ± 0.139 |
| 1000 | 500 | ProposedB_LinearStepB | 0.250 ± 7.471 | 0.146 ± 0.112 | -0.003 ± 0.185 |
| 1000 | 500 | ProposedB_SourceDR | 0.051 ± 2.926 | 5.622 ± 4.061 | -0.203 ± 6.956 |
| 1000 | 500 | ProxyOnly | 0.064 ± 6.513 | 3.741 ± 3.385 | -0.189 ± 5.055 |
| 1000 | 500 | TargetOnlyDR | 0.246 ± 7.478 | 0.126 ± 0.098 | -0.008 ± 0.160 |
| 1000 | 1000 | AnchorOnly | 0.155 ± 8.178 | 0.149 ± 0.121 | -0.022 ± 0.191 |
| 1000 | 1000 | AnchorPlugin | 0.220 ± 5.672 | 4.283 ± 4.778 | 0.043 ± 6.430 |
| 1000 | 1000 | DRLearner_PooledNoSite | 0.139 ± 7.577 | 0.683 ± 0.992 | -0.039 ± 1.206 |
| 1000 | 1000 | DRLearner_PooledWithSite | 0.137 ± 7.581 | 0.679 ± 0.986 | -0.041 ± 1.199 |
| 1000 | 1000 | EntropyBalancing | -0.517 ± 12.153 | 6.977 ± 8.828 | -0.695 ± 11.252 |
| 1000 | 1000 | IPWTransport | 0.028 ± 6.679 | 4.147 ± 5.288 | -0.149 ± 6.732 |
| 1000 | 1000 | OutcomeModelTransport | 0.041 ± 6.647 | 4.123 ± 5.125 | -0.136 ± 6.589 |
| 1000 | 1000 | ProposedA | 0.155 ± 8.211 | 0.128 ± 0.097 | -0.022 ± 0.160 |
| 1000 | 1000 | ProposedB_LinearStepB | 0.164 ± 8.211 | 0.128 ± 0.102 | -0.014 ± 0.163 |
| 1000 | 1000 | ProposedB_SourceDR | 0.203 ± 3.326 | 5.610 ± 4.740 | 0.026 ± 7.366 |
| 1000 | 1000 | ProxyOnly | 0.247 ± 8.464 | 5.143 ± 5.331 | 0.069 ± 7.425 |
| 1000 | 1000 | TargetOnlyDR | 0.162 ± 8.203 | 0.135 ± 0.106 | -0.015 ± 0.172 |

### Policy / Decision Metrics

| m0 | m1 | Method | Policy Value (↑) | Regret (↓) | Value Top20 (↑) | Regret Top20 (↓) |
|---|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 2.432 ± 4.472 | 1.066 ± 1.192 | 1.302 ± 3.691 | 0.494 ± 0.256 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 1.645 ± 4.608 | 1.853 ± 2.237 | 1.279 ± 3.718 | 0.517 ± 0.308 |
| 100 | 0 | IPWTransport | 2.728 ± 4.346 | 0.770 ± 1.001 | 1.478 ± 3.701 | 0.317 ± 0.242 |
| 100 | 0 | OutcomeModelTransport | 2.722 ± 4.343 | 0.776 ± 1.008 | 1.478 ± 3.701 | 0.317 ± 0.242 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 1.533 ± 4.371 | 1.965 ± 1.685 | 0.964 ± 3.706 | 0.831 ± 0.320 |
| 100 | 0 | ProxyOnly | 2.186 ± 4.876 | 1.312 ± 1.820 | 1.062 ± 3.723 | 0.734 ± 0.276 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 3.389 ± 5.050 | 0.306 ± 0.304 | 0.467 ± 4.062 | 0.513 ± 0.264 |
| 100 | 100 | AnchorPlugin | 2.180 ± 5.836 | 1.514 ± 2.789 | 0.434 ± 4.113 | 0.547 ± 0.542 |
| 100 | 100 | DRLearner_PooledNoSite | 2.956 ± 5.861 | 0.738 ± 2.226 | 0.619 ± 4.133 | 0.362 ± 0.624 |
| 100 | 100 | DRLearner_PooledWithSite | 2.969 ± 5.827 | 0.725 ± 2.171 | 0.619 ± 4.133 | 0.362 ± 0.621 |
| 100 | 100 | EntropyBalancing | 1.889 ± 5.858 | 1.806 ± 2.538 | 0.427 ± 4.133 | 0.553 ± 0.509 |
| 100 | 100 | IPWTransport | 2.536 ± 6.077 | 1.159 ± 2.675 | 0.603 ± 4.147 | 0.378 ± 0.665 |
| 100 | 100 | OutcomeModelTransport | 2.544 ± 6.058 | 1.151 ± 2.649 | 0.603 ± 4.147 | 0.377 ± 0.665 |
| 100 | 100 | ProposedA | 3.427 ± 5.039 | 0.267 ± 0.251 | 0.622 ± 4.033 | 0.359 ± 0.111 |
| 100 | 100 | ProposedB_LinearStepB | 3.413 ± 5.039 | 0.281 ± 0.272 | 0.550 ± 4.042 | 0.431 ± 0.164 |
| 100 | 100 | ProposedB_SourceDR | 1.312 ± 5.920 | 2.382 ± 3.089 | 0.121 ± 4.156 | 0.860 ± 0.674 |
| 100 | 100 | ProxyOnly | 1.734 ± 5.991 | 1.960 ± 3.765 | 0.207 ± 4.085 | 0.773 ± 0.422 |
| 100 | 100 | TargetOnlyDR | 3.409 ± 5.042 | 0.285 ± 0.272 | 0.573 ± 4.050 | 0.408 ± 0.144 |
| 100 | 500 | AnchorOnly | 3.249 ± 4.098 | 0.294 ± 0.218 | 1.293 ± 3.592 | 0.351 ± 0.092 |
| 100 | 500 | AnchorPlugin | 2.550 ± 4.238 | 0.994 ± 1.236 | 1.146 ± 3.602 | 0.498 ± 0.312 |
| 100 | 500 | DRLearner_PooledNoSite | 3.221 ± 4.095 | 0.322 ± 0.457 | 1.312 ± 3.594 | 0.333 ± 0.332 |
| 100 | 500 | DRLearner_PooledWithSite | 3.214 ± 4.100 | 0.329 ± 0.464 | 1.310 ± 3.594 | 0.334 ± 0.336 |
| 100 | 500 | EntropyBalancing | 1.868 ± 4.259 | 1.675 ± 2.197 | 1.110 ± 3.616 | 0.534 ± 0.352 |
| 100 | 500 | IPWTransport | 2.746 ± 4.163 | 0.798 ± 1.131 | 1.281 ± 3.593 | 0.363 ± 0.365 |
| 100 | 500 | OutcomeModelTransport | 2.745 ± 4.160 | 0.799 ± 1.133 | 1.280 ± 3.593 | 0.364 ± 0.367 |
| 100 | 500 | ProposedA | 3.248 ± 4.092 | 0.296 ± 0.221 | 1.305 ± 3.584 | 0.339 ± 0.080 |
| 100 | 500 | ProposedB_LinearStepB | 3.245 ± 4.096 | 0.299 ± 0.222 | 1.305 ± 3.594 | 0.339 ± 0.076 |
| 100 | 500 | ProposedB_SourceDR | 1.346 ± 4.416 | 2.197 ± 2.144 | 0.781 ± 3.611 | 0.863 ± 0.387 |
| 100 | 500 | ProxyOnly | 2.234 ± 4.102 | 1.309 ± 1.905 | 0.816 ± 3.613 | 0.828 ± 0.346 |
| 100 | 500 | TargetOnlyDR | 3.185 ± 4.116 | 0.358 ± 0.267 | 1.209 ± 3.600 | 0.435 ± 0.093 |
| 100 | 1000 | AnchorOnly | 4.001 ± 4.070 | 0.295 ± 0.232 | 1.364 ± 3.697 | 0.406 ± 0.095 |
| 100 | 1000 | AnchorPlugin | 3.105 ± 3.591 | 1.192 ± 1.607 | 1.247 ± 3.676 | 0.522 ± 0.264 |
| 100 | 1000 | DRLearner_PooledNoSite | 4.042 ± 4.069 | 0.255 ± 0.278 | 1.425 ± 3.686 | 0.345 ± 0.288 |
| 100 | 1000 | DRLearner_PooledWithSite | 4.049 ± 4.066 | 0.248 ± 0.263 | 1.422 ± 3.686 | 0.348 ± 0.295 |
| 100 | 1000 | EntropyBalancing | 2.814 ± 4.448 | 1.483 ± 1.940 | 1.252 ± 3.702 | 0.518 ± 0.270 |
| 100 | 1000 | IPWTransport | 3.236 ± 3.939 | 1.061 ± 1.785 | 1.383 ± 3.684 | 0.386 ± 0.334 |
| 100 | 1000 | OutcomeModelTransport | 3.227 ± 3.977 | 1.070 ± 1.876 | 1.382 ± 3.684 | 0.388 ± 0.337 |
| 100 | 1000 | ProposedA | 4.007 ± 4.071 | 0.290 ± 0.231 | 1.367 ± 3.699 | 0.402 ± 0.090 |
| 100 | 1000 | ProposedB_LinearStepB | 4.002 ± 4.071 | 0.295 ± 0.235 | 1.361 ± 3.699 | 0.408 ± 0.097 |
| 100 | 1000 | ProposedB_SourceDR | 2.334 ± 4.095 | 1.963 ± 2.114 | 0.917 ± 3.682 | 0.852 ± 0.327 |
| 100 | 1000 | ProxyOnly | 2.177 ± 4.455 | 2.120 ± 3.462 | 0.890 ± 3.697 | 0.879 ± 0.313 |
| 100 | 1000 | TargetOnlyDR | 3.922 ± 4.091 | 0.375 ± 0.300 | 1.239 ± 3.703 | 0.531 ± 0.106 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 2.300 ± 4.278 | 1.231 ± 1.627 | 0.828 ± 3.882 | 0.500 ± 0.269 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 2.070 ± 4.304 | 1.460 ± 2.350 | 0.788 ± 3.850 | 0.540 ± 0.334 |
| 500 | 0 | IPWTransport | 2.736 ± 4.280 | 0.795 ± 1.032 | 0.963 ± 3.846 | 0.365 ± 0.323 |
| 500 | 0 | OutcomeModelTransport | 2.733 ± 4.285 | 0.798 ± 1.037 | 0.963 ± 3.846 | 0.364 ± 0.323 |
| 500 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 1.447 ± 4.578 | 2.084 ± 1.891 | 0.454 ± 3.867 | 0.874 ± 0.281 |
| 500 | 0 | ProxyOnly | 2.121 ± 4.392 | 1.409 ± 1.967 | 0.634 ± 3.876 | 0.694 ± 0.272 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 3.395 ± 4.250 | 0.483 ± 0.401 | 0.991 ± 3.599 | 0.698 ± 0.207 |
| 500 | 100 | AnchorPlugin | 2.670 ± 4.225 | 1.208 ± 1.397 | 1.218 ± 3.607 | 0.471 ± 0.230 |
| 500 | 100 | DRLearner_PooledNoSite | 3.476 ± 4.140 | 0.402 ± 0.445 | 1.376 ± 3.593 | 0.313 ± 0.258 |
| 500 | 100 | DRLearner_PooledWithSite | 3.563 ± 4.146 | 0.315 ± 0.345 | 1.382 ± 3.593 | 0.308 ± 0.255 |
| 500 | 100 | EntropyBalancing | 2.040 ± 5.011 | 1.838 ± 2.593 | 1.181 ± 3.618 | 0.508 ± 0.351 |
| 500 | 100 | IPWTransport | 2.866 ± 4.087 | 1.012 ± 1.455 | 1.359 ± 3.591 | 0.330 ± 0.265 |
| 500 | 100 | OutcomeModelTransport | 2.861 ± 4.072 | 1.017 ± 1.432 | 1.360 ± 3.592 | 0.329 ± 0.264 |
| 500 | 100 | ProposedA | 3.567 ± 4.190 | 0.310 ± 0.229 | 1.336 ± 3.618 | 0.353 ± 0.089 |
| 500 | 100 | ProposedB_LinearStepB | 3.429 ± 4.239 | 0.449 ± 0.371 | 1.102 ± 3.621 | 0.587 ± 0.188 |
| 500 | 100 | ProposedB_SourceDR | 1.943 ± 4.437 | 1.934 ± 1.846 | 0.891 ± 3.614 | 0.798 ± 0.265 |
| 500 | 100 | ProxyOnly | 2.484 ± 4.535 | 1.394 ± 1.780 | 1.039 ± 3.619 | 0.650 ± 0.263 |
| 500 | 100 | TargetOnlyDR | 3.447 ± 4.225 | 0.431 ± 0.332 | 1.175 ± 3.627 | 0.514 ± 0.141 |
| 500 | 500 | AnchorOnly | 2.214 ± 4.235 | 0.329 ± 0.210 | 0.781 ± 3.736 | 0.343 ± 0.108 |
| 500 | 500 | AnchorPlugin | 1.380 ± 4.744 | 1.164 ± 1.336 | 0.649 ± 3.730 | 0.475 ± 0.226 |
| 500 | 500 | DRLearner_PooledNoSite | 2.242 ± 4.200 | 0.302 ± 0.295 | 0.808 ± 3.715 | 0.315 ± 0.237 |
| 500 | 500 | DRLearner_PooledWithSite | 2.243 ± 4.199 | 0.300 ± 0.292 | 0.809 ± 3.716 | 0.315 ± 0.237 |
| 500 | 500 | EntropyBalancing | 1.038 ± 4.741 | 1.505 ± 2.031 | 0.585 ± 3.767 | 0.538 ± 0.329 |
| 500 | 500 | IPWTransport | 1.621 ± 4.467 | 0.923 ± 1.298 | 0.773 ± 3.713 | 0.350 ± 0.267 |
| 500 | 500 | OutcomeModelTransport | 1.619 ± 4.481 | 0.924 ± 1.294 | 0.773 ± 3.712 | 0.351 ± 0.268 |
| 500 | 500 | ProposedA | 2.221 ± 4.233 | 0.323 ± 0.199 | 0.793 ± 3.732 | 0.331 ± 0.078 |
| 500 | 500 | ProposedB_LinearStepB | 2.228 ± 4.233 | 0.316 ± 0.195 | 0.792 ± 3.734 | 0.331 ± 0.086 |
| 500 | 500 | ProposedB_SourceDR | 0.615 ± 4.454 | 1.928 ± 1.890 | 0.308 ± 3.716 | 0.816 ± 0.283 |
| 500 | 500 | ProxyOnly | 1.164 ± 4.962 | 1.380 ± 1.589 | 0.450 ± 3.719 | 0.673 ± 0.251 |
| 500 | 500 | TargetOnlyDR | 2.221 ± 4.241 | 0.323 ± 0.199 | 0.797 ± 3.725 | 0.326 ± 0.078 |
| 500 | 1000 | AnchorOnly | 2.868 ± 3.999 | 0.268 ± 0.194 | 0.484 ± 3.458 | 0.311 ± 0.093 |
| 500 | 1000 | AnchorPlugin | 2.064 ± 3.897 | 1.073 ± 1.486 | 0.314 ± 3.473 | 0.481 ± 0.224 |
| 500 | 1000 | DRLearner_PooledNoSite | 2.887 ± 3.982 | 0.250 ± 0.269 | 0.490 ± 3.468 | 0.304 ± 0.223 |
| 500 | 1000 | DRLearner_PooledWithSite | 2.884 ± 3.983 | 0.252 ± 0.272 | 0.489 ± 3.467 | 0.306 ± 0.225 |
| 500 | 1000 | EntropyBalancing | 1.490 ± 4.128 | 1.646 ± 2.514 | 0.261 ± 3.457 | 0.533 ± 0.370 |
| 500 | 1000 | IPWTransport | 2.403 ± 3.836 | 0.733 ± 0.994 | 0.444 ± 3.475 | 0.350 ± 0.265 |
| 500 | 1000 | OutcomeModelTransport | 2.405 ± 3.861 | 0.731 ± 0.943 | 0.443 ± 3.475 | 0.352 ± 0.266 |
| 500 | 1000 | ProposedA | 2.869 ± 3.998 | 0.268 ± 0.192 | 0.475 ± 3.461 | 0.319 ± 0.087 |
| 500 | 1000 | ProposedB_LinearStepB | 2.875 ± 3.997 | 0.262 ± 0.190 | 0.483 ± 3.461 | 0.312 ± 0.094 |
| 500 | 1000 | ProposedB_SourceDR | 1.259 ± 4.023 | 1.877 ± 2.232 | -0.041 ± 3.461 | 0.835 ± 0.289 |
| 500 | 1000 | ProxyOnly | 1.714 ± 4.590 | 1.422 ± 2.094 | 0.083 ± 3.492 | 0.711 ± 0.314 |
| 500 | 1000 | TargetOnlyDR | 2.873 ± 3.991 | 0.263 ± 0.188 | 0.479 ± 3.452 | 0.315 ± 0.083 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 2.286 ± 4.503 | 1.071 ± 1.297 | 1.227 ± 3.885 | 0.492 ± 0.228 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 1.476 ± 4.203 | 1.880 ± 2.053 | 1.179 ± 3.892 | 0.540 ± 0.301 |
| 1000 | 0 | IPWTransport | 2.563 ± 4.331 | 0.793 ± 1.220 | 1.378 ± 3.893 | 0.342 ± 0.255 |
| 1000 | 0 | OutcomeModelTransport | 2.574 ± 4.333 | 0.782 ± 1.202 | 1.379 ± 3.892 | 0.341 ± 0.254 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 1.293 ± 4.505 | 2.064 ± 1.932 | 0.927 ± 3.879 | 0.792 ± 0.239 |
| 1000 | 0 | ProxyOnly | 2.153 ± 4.632 | 1.203 ± 1.492 | 1.027 ± 3.894 | 0.693 ± 0.254 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 3.826 ± 4.059 | 0.442 ± 0.459 | 1.530 ± 3.366 | 0.734 ± 0.237 |
| 1000 | 100 | AnchorPlugin | 3.308 ± 4.282 | 0.960 ± 1.032 | 1.840 ± 3.325 | 0.424 ± 0.178 |
| 1000 | 100 | DRLearner_PooledNoSite | 3.934 ± 4.044 | 0.334 ± 0.463 | 1.956 ± 3.339 | 0.308 ± 0.241 |
| 1000 | 100 | DRLearner_PooledWithSite | 4.029 ± 3.992 | 0.239 ± 0.326 | 1.969 ± 3.337 | 0.295 ± 0.232 |
| 1000 | 100 | EntropyBalancing | 3.037 ± 4.362 | 1.231 ± 1.519 | 1.780 ± 3.346 | 0.483 ± 0.260 |
| 1000 | 100 | IPWTransport | 3.521 ± 4.272 | 0.748 ± 0.975 | 1.932 ± 3.344 | 0.331 ± 0.256 |
| 1000 | 100 | OutcomeModelTransport | 3.526 ± 4.270 | 0.743 ± 0.985 | 1.934 ± 3.344 | 0.330 ± 0.257 |
| 1000 | 100 | ProposedA | 3.990 ± 3.992 | 0.278 ± 0.248 | 1.874 ± 3.333 | 0.390 ± 0.099 |
| 1000 | 100 | ProposedB_LinearStepB | 3.878 ± 4.033 | 0.390 ± 0.368 | 1.649 ± 3.344 | 0.615 ± 0.188 |
| 1000 | 100 | ProposedB_SourceDR | 2.362 ± 4.643 | 1.906 ± 2.423 | 1.488 ± 3.344 | 0.776 ± 0.254 |
| 1000 | 100 | ProxyOnly | 3.256 ± 4.414 | 1.012 ± 1.165 | 1.657 ± 3.330 | 0.606 ± 0.197 |
| 1000 | 100 | TargetOnlyDR | 3.880 ± 4.017 | 0.388 ± 0.354 | 1.709 ± 3.329 | 0.555 ± 0.138 |
| 1000 | 500 | AnchorOnly | 3.421 ± 4.153 | 0.276 ± 0.229 | 1.047 ± 3.575 | 0.373 ± 0.115 |
| 1000 | 500 | AnchorPlugin | 2.620 ± 4.167 | 1.077 ± 1.299 | 0.937 ± 3.579 | 0.482 ± 0.255 |
| 1000 | 500 | DRLearner_PooledNoSite | 3.470 ± 4.155 | 0.227 ± 0.277 | 1.129 ± 3.597 | 0.291 ± 0.249 |
| 1000 | 500 | DRLearner_PooledWithSite | 3.475 ± 4.154 | 0.222 ± 0.274 | 1.132 ± 3.598 | 0.287 ± 0.246 |
| 1000 | 500 | EntropyBalancing | 2.068 ± 4.250 | 1.630 ± 2.197 | 0.909 ± 3.594 | 0.511 ± 0.305 |
| 1000 | 500 | IPWTransport | 2.982 ± 4.340 | 0.716 ± 1.104 | 1.090 ± 3.597 | 0.330 ± 0.281 |
| 1000 | 500 | OutcomeModelTransport | 2.985 ± 4.338 | 0.712 ± 1.097 | 1.090 ± 3.597 | 0.330 ± 0.281 |
| 1000 | 500 | ProposedA | 3.442 ± 4.150 | 0.255 ± 0.199 | 1.095 ± 3.577 | 0.324 ± 0.080 |
| 1000 | 500 | ProposedB_LinearStepB | 3.441 ± 4.152 | 0.256 ± 0.203 | 1.076 ± 3.574 | 0.344 ± 0.090 |
| 1000 | 500 | ProposedB_SourceDR | 1.559 ± 4.213 | 2.139 ± 1.997 | 0.648 ± 3.556 | 0.772 ± 0.255 |
| 1000 | 500 | ProxyOnly | 2.492 ± 4.336 | 1.206 ± 1.582 | 0.760 ± 3.588 | 0.659 ± 0.247 |
| 1000 | 500 | TargetOnlyDR | 3.434 ± 4.157 | 0.263 ± 0.212 | 1.088 ± 3.580 | 0.332 ± 0.087 |
| 1000 | 1000 | AnchorOnly | 3.536 ± 5.282 | 0.275 ± 0.239 | 1.042 ± 4.047 | 0.350 ± 0.123 |
| 1000 | 1000 | AnchorPlugin | 2.556 ± 4.054 | 1.255 ± 3.165 | 0.920 ± 4.010 | 0.472 ± 0.292 |
| 1000 | 1000 | DRLearner_PooledNoSite | 3.589 ± 5.287 | 0.221 ± 0.262 | 1.110 ± 4.072 | 0.282 ± 0.208 |
| 1000 | 1000 | DRLearner_PooledWithSite | 3.590 ± 5.287 | 0.221 ± 0.262 | 1.110 ± 4.071 | 0.282 ± 0.209 |
| 1000 | 1000 | EntropyBalancing | 2.296 ± 3.971 | 1.514 ± 3.624 | 0.864 ± 3.964 | 0.529 ± 0.436 |
| 1000 | 1000 | IPWTransport | 2.580 ± 4.295 | 1.231 ± 3.577 | 1.053 ± 4.044 | 0.339 ± 0.281 |
| 1000 | 1000 | OutcomeModelTransport | 2.603 ± 4.332 | 1.207 ± 3.360 | 1.055 ± 4.051 | 0.337 ± 0.269 |
| 1000 | 1000 | ProposedA | 3.535 ± 5.284 | 0.276 ± 0.235 | 1.035 ± 4.060 | 0.357 ± 0.098 |
| 1000 | 1000 | ProposedB_LinearStepB | 3.542 ± 5.280 | 0.269 ± 0.231 | 1.050 ± 4.056 | 0.342 ± 0.109 |
| 1000 | 1000 | ProposedB_SourceDR | 1.690 ± 4.226 | 2.121 ± 3.040 | 0.570 ± 4.022 | 0.823 ± 0.317 |
| 1000 | 1000 | ProxyOnly | 2.328 ± 4.283 | 1.483 ± 3.525 | 0.706 ± 4.016 | 0.686 ± 0.311 |
| 1000 | 1000 | TargetOnlyDR | 3.543 ± 5.282 | 0.268 ± 0.225 | 1.041 ± 4.062 | 0.352 ± 0.106 |

### Calibration Metrics

| m0 | m1 | Method | Slope (→1) | Intercept (→0) | R² (↑) | ECE (↓) | MCE (↓) |
|---|---|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 0.876 ± 0.215 | -0.049 ± 5.071 | 0.420 ± 0.153 | 3.918 ± 3.095 | 5.322 ± 3.318 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 0.602 ± 0.225 | -0.857 ± 6.548 | 0.413 ± 0.195 | 7.617 ± 6.781 | 11.187 ± 8.687 |
| 100 | 0 | IPWTransport | 0.907 ± 0.172 | 0.077 ± 4.136 | 0.612 ± 0.182 | 3.217 ± 2.738 | 4.322 ± 3.208 |
| 100 | 0 | OutcomeModelTransport | 0.907 ± 0.172 | 0.088 ± 4.146 | 0.612 ± 0.182 | 3.229 ± 2.747 | 4.333 ± 3.217 |
| 100 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 0.876 ± 0.461 | 0.042 ± 6.486 | 0.153 ± 0.094 | 5.085 ± 3.864 | 7.366 ± 4.542 |
| 100 | 0 | ProxyOnly | 0.991 ± 0.385 | -0.000 ± 6.163 | 0.217 ± 0.100 | 4.605 ± 3.805 | 6.092 ± 4.093 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 1.253 ± 0.360 | -0.046 ± 3.483 | 0.396 ± 0.114 | 0.984 ± 0.565 | 2.411 ± 1.270 |
| 100 | 100 | AnchorPlugin | 0.856 ± 0.194 | 0.210 ± 6.500 | 0.409 ± 0.143 | 5.006 ± 4.554 | 6.424 ± 5.727 |
| 100 | 100 | DRLearner_PooledNoSite | 0.905 ± 0.243 | 0.174 ± 4.166 | 0.619 ± 0.176 | 2.991 ± 3.479 | 4.188 ± 4.637 |
| 100 | 100 | DRLearner_PooledWithSite | 0.905 ± 0.245 | 0.182 ± 4.180 | 0.619 ± 0.177 | 2.968 ± 3.396 | 4.165 ± 4.571 |
| 100 | 100 | EntropyBalancing | 0.615 ± 0.240 | 0.400 ± 7.626 | 0.425 ± 0.205 | 8.255 ± 7.783 | 11.994 ± 10.306 |
| 100 | 100 | IPWTransport | 0.894 ± 0.261 | 0.660 ± 5.500 | 0.609 ± 0.180 | 4.660 ± 5.672 | 5.947 ± 7.304 |
| 100 | 100 | OutcomeModelTransport | 0.894 ± 0.260 | 0.664 ± 5.470 | 0.609 ± 0.179 | 4.647 ± 5.643 | 5.931 ± 7.281 |
| 100 | 100 | ProposedA | 1.619 ± 0.270 | -0.002 ± 6.640 | 0.527 ± 0.065 | 1.233 ± 0.674 | 2.977 ± 1.562 |
| 100 | 100 | ProposedB_LinearStepB | 1.397 ± 0.334 | 0.326 ± 4.250 | 0.458 ± 0.099 | 1.038 ± 0.587 | 2.468 ± 1.472 |
| 100 | 100 | ProposedB_SourceDR | 0.923 ± 0.560 | 0.758 ± 7.461 | 0.168 ± 0.093 | 6.354 ± 4.703 | 8.688 ± 5.970 |
| 100 | 100 | ProxyOnly | 0.993 ± 0.352 | -0.269 ± 7.922 | 0.208 ± 0.094 | 5.748 ± 5.267 | 7.124 ± 5.682 |
| 100 | 100 | TargetOnlyDR | 1.481 ± 0.284 | 0.073 ± 5.455 | 0.476 ± 0.070 | 1.091 ± 0.522 | 2.596 ± 1.206 |
| 100 | 500 | AnchorOnly | 1.478 ± 0.256 | 0.142 ± 4.126 | 0.531 ± 0.072 | 1.039 ± 0.392 | 2.567 ± 0.886 |
| 100 | 500 | AnchorPlugin | 0.924 ± 0.242 | -0.188 ± 5.146 | 0.425 ± 0.148 | 3.821 ± 3.261 | 5.213 ± 3.698 |
| 100 | 500 | DRLearner_PooledNoSite | 0.940 ± 0.181 | -0.071 ± 2.036 | 0.624 ± 0.192 | 1.508 ± 1.058 | 2.501 ± 1.591 |
| 100 | 500 | DRLearner_PooledWithSite | 0.939 ± 0.182 | -0.059 ± 2.096 | 0.623 ± 0.192 | 1.532 ± 1.103 | 2.532 ± 1.659 |
| 100 | 500 | EntropyBalancing | 0.627 ± 0.259 | -0.644 ± 5.964 | 0.419 ± 0.199 | 6.842 ± 6.892 | 10.217 ± 8.769 |
| 100 | 500 | IPWTransport | 0.918 ± 0.201 | -0.256 ± 4.618 | 0.600 ± 0.197 | 3.989 ± 2.948 | 5.140 ± 3.403 |
| 100 | 500 | OutcomeModelTransport | 0.917 ± 0.201 | -0.252 ± 4.630 | 0.600 ± 0.197 | 3.990 ± 2.956 | 5.140 ± 3.412 |
| 100 | 500 | ProposedA | 1.519 ± 0.258 | 0.253 ± 4.339 | 0.543 ± 0.063 | 1.078 ± 0.409 | 2.754 ± 0.952 |
| 100 | 500 | ProposedB_LinearStepB | 1.504 ± 0.272 | 0.237 ± 4.696 | 0.535 ± 0.069 | 1.071 ± 0.404 | 2.691 ± 0.942 |
| 100 | 500 | ProposedB_SourceDR | 0.915 ± 0.617 | -0.172 ± 6.863 | 0.146 ± 0.088 | 5.347 ± 3.790 | 7.299 ± 4.083 |
| 100 | 500 | ProxyOnly | 0.339 ± 0.149 | 0.413 ± 5.952 | 0.182 ± 0.114 | 12.565 ± 9.003 | 18.820 ± 10.137 |
| 100 | 500 | TargetOnlyDR | 1.226 ± 0.258 | 0.152 ± 2.934 | 0.389 ± 0.106 | 0.957 ± 0.335 | 2.193 ± 0.761 |
| 100 | 1000 | AnchorOnly | 1.294 ± 0.246 | -0.111 ± 3.112 | 0.443 ± 0.099 | 0.914 ± 0.346 | 2.160 ± 0.770 |
| 100 | 1000 | AnchorPlugin | 0.870 ± 0.249 | 0.758 ± 6.092 | 0.401 ± 0.162 | 4.824 ± 4.051 | 6.430 ± 4.866 |
| 100 | 1000 | DRLearner_PooledNoSite | 0.911 ± 0.187 | -0.075 ± 2.517 | 0.591 ± 0.201 | 1.326 ± 1.183 | 2.342 ± 1.841 |
| 100 | 1000 | DRLearner_PooledWithSite | 0.910 ± 0.188 | -0.111 ± 2.524 | 0.590 ± 0.201 | 1.285 ± 1.194 | 2.313 ± 1.928 |
| 100 | 1000 | EntropyBalancing | 0.598 ± 0.215 | 0.722 ± 6.347 | 0.409 ± 0.184 | 7.470 ± 6.166 | 11.370 ± 8.300 |
| 100 | 1000 | IPWTransport | 0.875 ± 0.203 | 0.576 ± 5.548 | 0.552 ± 0.211 | 4.602 ± 4.123 | 5.876 ± 4.861 |
| 100 | 1000 | OutcomeModelTransport | 0.874 ± 0.204 | 0.574 ± 5.547 | 0.552 ± 0.211 | 4.596 ± 4.159 | 5.860 ± 4.899 |
| 100 | 1000 | ProposedA | 1.298 ± 0.233 | -0.052 ± 3.461 | 0.448 ± 0.096 | 0.913 ± 0.340 | 2.166 ± 0.785 |
| 100 | 1000 | ProposedB_LinearStepB | 1.299 ± 0.260 | 0.015 ± 3.394 | 0.444 ± 0.099 | 0.914 ± 0.349 | 2.161 ± 0.831 |
| 100 | 1000 | ProposedB_SourceDR | 0.875 ± 0.441 | 0.407 ± 7.264 | 0.152 ± 0.096 | 5.541 ± 4.552 | 7.478 ± 5.104 |
| 100 | 1000 | ProxyOnly | 0.166 ± 0.097 | 0.732 ± 7.178 | 0.150 ± 0.103 | 28.344 ± 18.988 | 43.952 ± 23.207 |
| 100 | 1000 | TargetOnlyDR | 0.854 ± 0.300 | 0.091 ± 2.912 | 0.248 ± 0.116 | 0.875 ± 0.309 | 2.057 ± 0.805 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 0.902 ± 0.230 | 0.356 ± 5.299 | 0.429 ± 0.151 | 4.050 ± 3.361 | 5.359 ± 3.710 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 0.600 ± 0.227 | 0.365 ± 5.939 | 0.410 ± 0.198 | 7.615 ± 6.751 | 11.345 ± 8.563 |
| 500 | 0 | IPWTransport | 0.891 ± 0.199 | 0.125 ± 4.418 | 0.583 ± 0.196 | 3.447 ± 2.743 | 4.697 ± 3.397 |
| 500 | 0 | OutcomeModelTransport | 0.891 ± 0.198 | 0.124 ± 4.433 | 0.584 ± 0.196 | 3.453 ± 2.747 | 4.715 ± 3.418 |
| 500 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 0.836 ± 0.392 | 0.543 ± 6.148 | 0.134 ± 0.084 | 5.095 ± 3.720 | 7.160 ± 4.043 |
| 500 | 0 | ProxyOnly | 1.019 ± 0.334 | 0.142 ± 6.815 | 0.269 ± 0.120 | 5.217 ± 3.774 | 6.690 ± 4.137 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 0.568 ± 0.267 | 0.188 ± 4.495 | 0.160 ± 0.099 | 1.469 ± 0.737 | 4.648 ± 2.823 |
| 500 | 100 | AnchorPlugin | 0.900 ± 0.196 | 0.137 ± 5.438 | 0.444 ± 0.146 | 4.205 ± 3.423 | 5.382 ± 3.686 |
| 500 | 100 | DRLearner_PooledNoSite | 0.922 ± 0.203 | -0.105 ± 3.049 | 0.625 ± 0.202 | 2.260 ± 1.726 | 3.422 ± 2.333 |
| 500 | 100 | DRLearner_PooledWithSite | 0.926 ± 0.201 | -0.069 ± 2.410 | 0.632 ± 0.200 | 1.637 ± 1.191 | 2.733 ± 1.823 |
| 500 | 100 | EntropyBalancing | 0.632 ± 0.258 | -0.475 ± 6.296 | 0.440 ± 0.218 | 7.974 ± 8.919 | 11.481 ± 11.515 |
| 500 | 100 | IPWTransport | 0.907 ± 0.208 | -0.340 ± 5.096 | 0.607 ± 0.206 | 4.154 ± 3.296 | 5.384 ± 3.857 |
| 500 | 100 | OutcomeModelTransport | 0.907 ± 0.208 | -0.361 ± 5.113 | 0.607 ± 0.206 | 4.183 ± 3.289 | 5.423 ± 3.846 |
| 500 | 100 | ProposedA | 1.448 ± 0.229 | -0.285 ± 3.568 | 0.525 ± 0.077 | 1.008 ± 0.322 | 2.499 ± 0.930 |
| 500 | 100 | ProposedB_LinearStepB | 0.847 ± 0.384 | 0.099 ± 3.128 | 0.264 ± 0.140 | 1.191 ± 0.631 | 3.504 ± 2.532 |
| 500 | 100 | ProposedB_SourceDR | 0.877 ± 0.464 | -0.628 ± 6.550 | 0.166 ± 0.102 | 5.274 ± 3.894 | 7.202 ± 4.196 |
| 500 | 100 | ProxyOnly | 1.320 ± 0.424 | 0.184 ± 5.733 | 0.288 ± 0.118 | 4.319 ± 3.394 | 5.944 ± 3.590 |
| 500 | 100 | TargetOnlyDR | 0.933 ± 0.276 | 0.631 ± 1.924 | 0.277 ± 0.100 | 0.962 ± 0.324 | 2.176 ± 0.789 |
| 500 | 500 | AnchorOnly | 1.422 ± 0.216 | 0.310 ± 2.432 | 0.554 ± 0.061 | 0.967 ± 0.321 | 2.413 ± 0.788 |
| 500 | 500 | AnchorPlugin | 0.923 ± 0.206 | -1.335 ± 4.939 | 0.446 ± 0.148 | 3.989 ± 3.355 | 5.214 ± 3.658 |
| 500 | 500 | DRLearner_PooledNoSite | 0.938 ± 0.174 | -0.284 ± 1.868 | 0.627 ± 0.178 | 1.166 ± 0.913 | 2.134 ± 1.459 |
| 500 | 500 | DRLearner_PooledWithSite | 0.939 ± 0.174 | -0.282 ± 1.871 | 0.627 ± 0.178 | 1.164 ± 0.918 | 2.136 ± 1.469 |
| 500 | 500 | EntropyBalancing | 0.606 ± 0.226 | -1.592 ± 5.533 | 0.415 ± 0.204 | 7.082 ± 6.104 | 10.915 ± 8.426 |
| 500 | 500 | IPWTransport | 0.913 ± 0.185 | -1.113 ± 4.548 | 0.596 ± 0.189 | 3.708 ± 3.365 | 4.895 ± 3.988 |
| 500 | 500 | OutcomeModelTransport | 0.913 ± 0.185 | -1.123 ± 4.576 | 0.596 ± 0.190 | 3.737 ± 3.378 | 4.924 ± 4.001 |
| 500 | 500 | ProposedA | 1.478 ± 0.187 | 0.561 ± 3.231 | 0.570 ± 0.047 | 1.002 ± 0.330 | 2.595 ± 0.781 |
| 500 | 500 | ProposedB_LinearStepB | 1.452 ± 0.193 | 0.385 ± 2.736 | 0.570 ± 0.049 | 0.991 ± 0.340 | 2.508 ± 0.818 |
| 500 | 500 | ProposedB_SourceDR | 0.885 ± 0.467 | -0.991 ± 5.787 | 0.163 ± 0.096 | 4.874 ± 3.633 | 6.793 ± 4.129 |
| 500 | 500 | ProxyOnly | 1.031 ± 0.352 | -1.660 ± 6.187 | 0.278 ± 0.120 | 4.889 ± 4.140 | 6.484 ± 4.363 |
| 500 | 500 | TargetOnlyDR | 1.478 ± 0.215 | 0.602 ± 3.389 | 0.572 ± 0.052 | 1.033 ± 0.379 | 2.627 ± 0.830 |
| 500 | 1000 | AnchorOnly | 1.425 ± 0.174 | -0.523 ± 2.828 | 0.581 ± 0.050 | 0.920 ± 0.265 | 2.400 ± 0.772 |
| 500 | 1000 | AnchorPlugin | 0.886 ± 0.218 | 0.380 ± 4.894 | 0.430 ± 0.150 | 3.844 ± 3.194 | 5.188 ± 3.410 |
| 500 | 1000 | DRLearner_PooledNoSite | 0.943 ± 0.185 | 0.123 ± 1.908 | 0.630 ± 0.173 | 0.826 ± 0.564 | 1.705 ± 1.219 |
| 500 | 1000 | DRLearner_PooledWithSite | 0.941 ± 0.185 | 0.130 ± 1.938 | 0.629 ± 0.173 | 0.840 ± 0.582 | 1.723 ± 1.238 |
| 500 | 1000 | EntropyBalancing | 0.613 ± 0.266 | -0.460 ± 5.915 | 0.419 ± 0.197 | 6.950 ± 6.512 | 10.524 ± 8.793 |
| 500 | 1000 | IPWTransport | 0.903 ± 0.200 | 0.017 ± 4.362 | 0.585 ± 0.186 | 3.248 ± 2.912 | 4.358 ± 3.409 |
| 500 | 1000 | OutcomeModelTransport | 0.903 ± 0.199 | 0.021 ± 4.388 | 0.585 ± 0.186 | 3.288 ± 2.896 | 4.405 ± 3.399 |
| 500 | 1000 | ProposedA | 1.431 ± 0.167 | -0.499 ± 3.057 | 0.573 ± 0.049 | 0.900 ± 0.287 | 2.305 ± 0.738 |
| 500 | 1000 | ProposedB_LinearStepB | 1.430 ± 0.180 | -0.578 ± 3.027 | 0.583 ± 0.051 | 0.912 ± 0.289 | 2.351 ± 0.796 |
| 500 | 1000 | ProposedB_SourceDR | 0.932 ± 0.580 | 0.861 ± 6.077 | 0.157 ± 0.095 | 5.048 ± 3.747 | 7.118 ± 4.374 |
| 500 | 1000 | ProxyOnly | 0.654 ± 0.237 | -0.195 ± 5.846 | 0.248 ± 0.136 | 6.066 ± 5.028 | 8.419 ± 5.426 |
| 500 | 1000 | TargetOnlyDR | 1.428 ± 0.162 | -0.624 ± 3.090 | 0.576 ± 0.053 | 0.922 ± 0.281 | 2.395 ± 0.742 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 0.899 ± 0.222 | -0.627 ± 4.693 | 0.430 ± 0.160 | 3.776 ± 3.035 | 4.978 ± 3.220 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 0.601 ± 0.212 | 0.155 ± 6.721 | 0.398 ± 0.188 | 7.986 ± 6.535 | 11.597 ± 8.382 |
| 1000 | 0 | IPWTransport | 0.912 ± 0.230 | -0.119 ± 4.345 | 0.592 ± 0.200 | 3.616 ± 3.368 | 4.849 ± 4.067 |
| 1000 | 0 | OutcomeModelTransport | 0.912 ± 0.229 | -0.156 ± 4.327 | 0.593 ± 0.200 | 3.613 ± 3.342 | 4.838 ± 4.036 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 0.931 ± 0.523 | -1.147 ± 6.031 | 0.162 ± 0.093 | 5.115 ± 3.833 | 7.167 ± 4.091 |
| 1000 | 0 | ProxyOnly | 0.929 ± 0.318 | -0.250 ± 5.307 | 0.262 ± 0.130 | 4.676 ± 3.115 | 6.103 ± 3.463 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 0.328 ± 0.227 | -1.200 ± 6.602 | 0.088 ± 0.091 | 1.741 ± 0.718 | 6.508 ± 4.110 |
| 1000 | 100 | AnchorPlugin | 0.889 ± 0.202 | -0.565 ± 5.414 | 0.461 ± 0.147 | 4.363 ± 3.170 | 5.662 ± 3.438 |
| 1000 | 100 | DRLearner_PooledNoSite | 0.899 ± 0.158 | 0.030 ± 2.887 | 0.614 ± 0.178 | 1.954 ± 1.614 | 2.916 ± 1.974 |
| 1000 | 100 | DRLearner_PooledWithSite | 0.907 ± 0.153 | 0.017 ± 1.992 | 0.627 ± 0.175 | 1.099 ± 0.849 | 1.965 ± 1.320 |
| 1000 | 100 | EntropyBalancing | 0.640 ± 0.229 | -0.870 ± 6.067 | 0.429 ± 0.193 | 6.147 ± 5.617 | 9.185 ± 7.211 |
| 1000 | 100 | IPWTransport | 0.880 ± 0.172 | 0.100 ± 4.866 | 0.589 ± 0.185 | 3.808 ± 3.169 | 4.920 ± 3.580 |
| 1000 | 100 | OutcomeModelTransport | 0.882 ± 0.169 | 0.088 ± 4.856 | 0.591 ± 0.184 | 3.778 ± 3.182 | 4.870 ± 3.584 |
| 1000 | 100 | ProposedA | 1.274 ± 0.279 | 0.222 ± 3.468 | 0.443 ± 0.108 | 0.865 ± 0.315 | 2.091 ± 0.773 |
| 1000 | 100 | ProposedB_LinearStepB | 0.545 ± 0.306 | -0.788 ± 4.907 | 0.156 ± 0.118 | 1.271 ± 0.522 | 4.143 ± 3.060 |
| 1000 | 100 | ProposedB_SourceDR | 0.888 ± 0.419 | -1.028 ± 7.285 | 0.170 ± 0.105 | 5.866 ± 4.673 | 7.807 ± 4.823 |
| 1000 | 100 | ProxyOnly | 1.251 ± 0.437 | 0.144 ± 5.464 | 0.284 ± 0.128 | 4.340 ± 3.123 | 6.119 ± 3.230 |
| 1000 | 100 | TargetOnlyDR | 0.644 ± 0.259 | -0.457 ± 3.445 | 0.176 ± 0.106 | 1.011 ± 0.300 | 2.357 ± 0.842 |
| 1000 | 500 | AnchorOnly | 1.366 ± 0.300 | 0.044 ± 2.828 | 0.500 ± 0.086 | 0.940 ± 0.367 | 2.278 ± 0.906 |
| 1000 | 500 | AnchorPlugin | 0.860 ± 0.242 | 0.115 ± 4.994 | 0.437 ± 0.174 | 3.863 ± 3.110 | 5.260 ± 3.532 |
| 1000 | 500 | DRLearner_PooledNoSite | 0.946 ± 0.172 | 0.089 ± 1.490 | 0.650 ± 0.188 | 0.838 ± 0.547 | 1.676 ± 1.067 |
| 1000 | 500 | DRLearner_PooledWithSite | 0.948 ± 0.171 | 0.079 ± 1.444 | 0.652 ± 0.188 | 0.788 ± 0.510 | 1.611 ± 1.041 |
| 1000 | 500 | EntropyBalancing | 0.614 ± 0.204 | 0.910 ± 6.230 | 0.424 ± 0.199 | 6.899 ± 6.398 | 10.278 ± 8.083 |
| 1000 | 500 | IPWTransport | 0.915 ± 0.192 | 0.472 ± 3.980 | 0.613 ± 0.199 | 3.142 ± 2.602 | 4.199 ± 3.004 |
| 1000 | 500 | OutcomeModelTransport | 0.915 ± 0.192 | 0.410 ± 4.003 | 0.612 ± 0.199 | 3.144 ± 2.623 | 4.210 ± 3.016 |
| 1000 | 500 | ProposedA | 1.483 ± 0.198 | 0.079 ± 3.929 | 0.571 ± 0.053 | 0.960 ± 0.323 | 2.389 ± 0.839 |
| 1000 | 500 | ProposedB_LinearStepB | 1.410 ± 0.261 | -0.001 ± 2.977 | 0.540 ± 0.070 | 0.912 ± 0.354 | 2.237 ± 0.875 |
| 1000 | 500 | ProposedB_SourceDR | 0.868 ± 0.406 | 0.057 ± 7.041 | 0.170 ± 0.099 | 5.691 ± 3.990 | 7.473 ± 4.183 |
| 1000 | 500 | ProxyOnly | 1.073 ± 0.441 | 0.301 ± 5.446 | 0.268 ± 0.133 | 3.867 ± 3.295 | 5.464 ± 3.579 |
| 1000 | 500 | TargetOnlyDR | 1.485 ± 0.227 | 0.186 ± 4.235 | 0.553 ± 0.060 | 0.976 ± 0.344 | 2.451 ± 0.829 |
| 1000 | 1000 | AnchorOnly | 1.443 ± 0.207 | -0.143 ± 3.698 | 0.566 ± 0.044 | 1.024 ± 0.398 | 2.505 ± 0.926 |
| 1000 | 1000 | AnchorPlugin | 0.928 ± 0.219 | 0.036 ± 6.368 | 0.464 ± 0.136 | 4.345 ± 4.731 | 5.670 ± 4.930 |
| 1000 | 1000 | DRLearner_PooledNoSite | 0.970 ± 0.187 | 0.015 ± 1.559 | 0.669 ± 0.172 | 0.920 ± 0.977 | 1.875 ± 1.662 |
| 1000 | 1000 | DRLearner_PooledWithSite | 0.970 ± 0.187 | 0.023 ± 1.548 | 0.669 ± 0.172 | 0.914 ± 0.972 | 1.871 ± 1.653 |
| 1000 | 1000 | EntropyBalancing | 0.633 ± 0.229 | 0.431 ± 6.330 | 0.447 ± 0.210 | 7.218 ± 8.700 | 10.806 ± 11.255 |
| 1000 | 1000 | IPWTransport | 0.932 ± 0.201 | 0.371 ± 6.643 | 0.617 ± 0.195 | 4.221 ± 5.244 | 5.461 ± 5.615 |
| 1000 | 1000 | OutcomeModelTransport | 0.933 ± 0.205 | 0.360 ± 6.496 | 0.617 ± 0.194 | 4.203 ± 5.075 | 5.456 ± 5.560 |
| 1000 | 1000 | ProposedA | 1.433 ± 0.166 | -0.178 ± 3.546 | 0.557 ± 0.040 | 0.954 ± 0.336 | 2.430 ± 0.879 |
| 1000 | 1000 | ProposedB_LinearStepB | 1.458 ± 0.187 | -0.216 ± 3.861 | 0.575 ± 0.043 | 1.009 ± 0.369 | 2.528 ± 0.909 |
| 1000 | 1000 | ProposedB_SourceDR | 0.907 ± 0.407 | -0.157 ± 7.607 | 0.168 ± 0.095 | 5.656 ± 4.697 | 7.867 ± 5.270 |
| 1000 | 1000 | ProxyOnly | 0.947 ± 0.325 | 0.324 ± 7.005 | 0.271 ± 0.115 | 5.223 ± 5.267 | 6.945 ± 5.818 |
| 1000 | 1000 | TargetOnlyDR | 1.447 ± 0.179 | -0.218 ± 3.778 | 0.566 ± 0.042 | 0.987 ± 0.385 | 2.554 ± 0.974 |

### Extended Targeting Metrics

| m0 | m1 | Method | Top-10% Captured | Top-20% Captured | Top-30% Ratio (↑) |
|---|---|---|---|---|---|
| 100 | 0 | AnchorOnly | N/A | N/A | N/A |
| 100 | 0 | AnchorPlugin | 4.628 ± 6.860 | 3.543 ± 6.825 | 0.278 ± 1.152 |
| 100 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 0 | EntropyBalancing | 4.533 ± 7.115 | 3.427 ± 6.982 | 0.207 ± 1.388 |
| 100 | 0 | IPWTransport | 5.763 ± 6.895 | 4.426 ± 6.824 | 0.532 ± 0.784 |
| 100 | 0 | OutcomeModelTransport | 5.765 ± 6.893 | 4.425 ± 6.823 | 0.533 ± 0.781 |
| 100 | 0 | ProposedA | N/A | N/A | N/A |
| 100 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 0 | ProposedB_SourceDR | 2.498 ± 6.964 | 1.856 ± 6.862 | -0.195 ± 1.891 |
| 100 | 0 | ProxyOnly | 3.154 ± 6.760 | 2.343 ± 6.748 | -0.029 ± 1.582 |
| 100 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | 5.850 ± 8.991 | 4.816 ± 8.823 | -8.344 ± 75.815 |
| 100 | 100 | AnchorPlugin | 5.625 ± 9.142 | 4.649 ± 8.938 | -20.716 ± 180.925 |
| 100 | 100 | DRLearner_PooledNoSite | 6.875 ± 9.329 | 5.572 ± 9.162 | -8.453 ± 77.003 |
| 100 | 100 | DRLearner_PooledWithSite | 6.865 ± 9.337 | 5.572 ± 9.162 | -8.372 ± 76.282 |
| 100 | 100 | EntropyBalancing | 5.687 ± 8.660 | 4.615 ± 8.684 | -18.736 ± 164.488 |
| 100 | 100 | IPWTransport | 6.744 ± 9.441 | 5.494 ± 9.218 | -8.377 ± 76.165 |
| 100 | 100 | OutcomeModelTransport | 6.750 ± 9.444 | 5.495 ± 9.214 | -8.379 ± 76.165 |
| 100 | 100 | ProposedA | 6.859 ± 8.851 | 5.589 ± 8.747 | -6.126 ± 57.894 |
| 100 | 100 | ProposedB_LinearStepB | 6.398 ± 8.833 | 5.227 ± 8.719 | -9.683 ± 88.072 |
| 100 | 100 | ProposedB_SourceDR | 3.790 ± 9.331 | 3.083 ± 9.188 | -14.937 ± 128.133 |
| 100 | 100 | ProxyOnly | 4.164 ± 8.811 | 3.515 ± 8.776 | -25.928 ± 223.605 |
| 100 | 100 | TargetOnlyDR | 6.479 ± 8.726 | 5.341 ± 8.692 | -7.730 ± 71.261 |
| 100 | 500 | AnchorOnly | 5.742 ± 7.264 | 4.459 ± 7.180 | 0.619 ± 0.420 |
| 100 | 500 | AnchorPlugin | 4.825 ± 7.386 | 3.721 ± 7.365 | 0.462 ± 0.644 |
| 100 | 500 | DRLearner_PooledNoSite | 5.835 ± 7.223 | 4.550 ± 7.205 | 0.664 ± 0.436 |
| 100 | 500 | DRLearner_PooledWithSite | 5.833 ± 7.233 | 4.542 ± 7.211 | 0.664 ± 0.435 |
| 100 | 500 | EntropyBalancing | 4.561 ± 7.327 | 3.544 ± 7.254 | 0.433 ± 0.610 |
| 100 | 500 | IPWTransport | 5.662 ± 7.270 | 4.398 ± 7.223 | 0.639 ± 0.470 |
| 100 | 500 | OutcomeModelTransport | 5.652 ± 7.269 | 4.393 ± 7.217 | 0.639 ± 0.469 |
| 100 | 500 | ProposedA | 5.797 ± 7.202 | 4.517 ± 7.169 | 0.625 ± 0.403 |
| 100 | 500 | ProposedB_LinearStepB | 5.785 ± 7.165 | 4.515 ± 7.118 | 0.622 ± 0.411 |
| 100 | 500 | ProposedB_SourceDR | 2.614 ± 7.376 | 1.898 ± 7.332 | 0.071 ± 1.014 |
| 100 | 500 | ProxyOnly | 2.713 ± 7.398 | 2.074 ± 7.337 | 0.107 ± 0.956 |
| 100 | 500 | TargetOnlyDR | 5.026 ± 7.101 | 4.035 ± 7.152 | 0.511 ± 0.559 |
| 100 | 1000 | AnchorOnly | 6.540 ± 8.210 | 5.407 ± 8.072 | -0.934 ± 14.413 |
| 100 | 1000 | AnchorPlugin | 5.839 ± 8.300 | 4.824 ± 8.244 | -0.960 ± 13.876 |
| 100 | 1000 | DRLearner_PooledNoSite | 6.980 ± 8.399 | 5.711 ± 8.368 | 0.068 ± 5.993 |
| 100 | 1000 | DRLearner_PooledWithSite | 6.968 ± 8.400 | 5.696 ± 8.383 | 0.070 ± 5.972 |
| 100 | 1000 | EntropyBalancing | 5.903 ± 8.398 | 4.846 ± 8.296 | -1.721 ± 20.724 |
| 100 | 1000 | IPWTransport | 6.697 ± 8.486 | 5.503 ± 8.421 | -0.065 ± 6.946 |
| 100 | 1000 | OutcomeModelTransport | 6.697 ± 8.487 | 5.497 ± 8.428 | -0.065 ± 6.946 |
| 100 | 1000 | ProposedA | 6.569 ± 8.077 | 5.424 ± 8.058 | -0.806 ± 13.304 |
| 100 | 1000 | ProposedB_LinearStepB | 6.560 ± 8.138 | 5.395 ± 8.056 | -0.814 ± 13.357 |
| 100 | 1000 | ProposedB_SourceDR | 3.886 ± 8.439 | 3.174 ± 8.430 | -2.707 ± 27.093 |
| 100 | 1000 | ProxyOnly | 3.682 ± 8.334 | 3.039 ± 8.228 | -3.381 ± 32.956 |
| 100 | 1000 | TargetOnlyDR | 5.619 ± 8.123 | 4.782 ± 8.042 | -1.415 ± 17.762 |
| 500 | 0 | AnchorOnly | N/A | N/A | N/A |
| 500 | 0 | AnchorPlugin | 6.312 ± 7.297 | 5.198 ± 7.242 | 0.397 ± 1.453 |
| 500 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 0 | EntropyBalancing | 6.051 ± 7.327 | 4.996 ± 7.261 | 0.435 ± 1.275 |
| 500 | 0 | IPWTransport | 7.155 ± 7.271 | 5.872 ± 7.178 | 0.684 ± 0.453 |
| 500 | 0 | OutcomeModelTransport | 7.160 ± 7.274 | 5.874 ± 7.181 | 0.685 ± 0.452 |
| 500 | 0 | ProposedA | N/A | N/A | N/A |
| 500 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 0 | ProposedB_SourceDR | 3.964 ± 7.402 | 3.326 ± 7.346 | -0.079 ± 2.794 |
| 500 | 0 | ProxyOnly | 5.121 ± 7.382 | 4.226 ± 7.301 | 0.121 ± 2.198 |
| 500 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 100 | AnchorOnly | 4.020 ± 7.340 | 3.382 ± 7.345 | 0.202 ± 1.193 |
| 500 | 100 | AnchorPlugin | 5.627 ± 7.392 | 4.514 ± 7.349 | 0.443 ± 0.816 |
| 500 | 100 | DRLearner_PooledNoSite | 6.650 ± 7.399 | 5.308 ± 7.332 | 0.664 ± 0.505 |
| 500 | 100 | DRLearner_PooledWithSite | 6.696 ± 7.399 | 5.333 ± 7.337 | 0.672 ± 0.487 |
| 500 | 100 | EntropyBalancing | 5.415 ± 7.667 | 4.332 ± 7.586 | 0.465 ± 0.742 |
| 500 | 100 | IPWTransport | 6.555 ± 7.397 | 5.221 ± 7.328 | 0.651 ± 0.517 |
| 500 | 100 | OutcomeModelTransport | 6.551 ± 7.396 | 5.224 ± 7.323 | 0.652 ± 0.514 |
| 500 | 100 | ProposedA | 6.363 ± 7.627 | 5.104 ± 7.493 | 0.538 ± 0.764 |
| 500 | 100 | ProposedB_LinearStepB | 4.762 ± 7.355 | 3.938 ± 7.374 | 0.326 ± 0.942 |
| 500 | 100 | ProposedB_SourceDR | 3.545 ± 7.378 | 2.881 ± 7.305 | 0.047 ± 1.455 |
| 500 | 100 | ProxyOnly | 4.563 ± 7.460 | 3.619 ± 7.423 | 0.208 ± 1.243 |
| 500 | 100 | TargetOnlyDR | 5.052 ± 7.404 | 4.299 ± 7.359 | 0.377 ± 0.972 |
| 500 | 500 | AnchorOnly | 5.353 ± 6.475 | 3.955 ± 6.449 | 0.097 ± 4.333 |
| 500 | 500 | AnchorPlugin | 4.484 ± 6.249 | 3.298 ± 6.282 | -0.210 ± 6.057 |
| 500 | 500 | DRLearner_PooledNoSite | 5.503 ± 6.323 | 4.095 ± 6.340 | -0.226 ± 7.993 |
| 500 | 500 | DRLearner_PooledWithSite | 5.502 ± 6.318 | 4.096 ± 6.340 | -0.205 ± 7.827 |
| 500 | 500 | EntropyBalancing | 4.070 ± 6.410 | 2.978 ± 6.363 | -1.706 ± 18.651 |
| 500 | 500 | IPWTransport | 5.269 ± 6.329 | 3.918 ± 6.338 | -0.297 ± 8.275 |
| 500 | 500 | OutcomeModelTransport | 5.271 ± 6.333 | 3.915 ± 6.343 | -0.307 ± 8.381 |
| 500 | 500 | ProposedA | 5.387 ± 6.441 | 4.018 ± 6.382 | 0.104 ± 4.420 |
| 500 | 500 | ProposedB_LinearStepB | 5.410 ± 6.496 | 4.014 ± 6.434 | 0.100 ± 4.379 |
| 500 | 500 | ProposedB_SourceDR | 2.318 ± 6.383 | 1.592 ± 6.412 | -1.000 ± 9.400 |
| 500 | 500 | ProxyOnly | 3.260 ± 6.456 | 2.304 ± 6.486 | -0.329 ± 5.077 |
| 500 | 500 | TargetOnlyDR | 5.420 ± 6.468 | 4.038 ± 6.438 | 0.033 ± 4.997 |
| 500 | 1000 | AnchorOnly | 7.680 ± 7.230 | 6.320 ± 7.118 | 0.747 ± 0.368 |
| 500 | 1000 | AnchorPlugin | 6.601 ± 6.896 | 5.472 ± 6.809 | 0.591 ± 0.659 |
| 500 | 1000 | DRLearner_PooledNoSite | 7.748 ± 6.960 | 6.354 ± 6.894 | 0.739 ± 0.511 |
| 500 | 1000 | DRLearner_PooledWithSite | 7.738 ± 6.959 | 6.347 ± 6.891 | 0.737 ± 0.513 |
| 500 | 1000 | EntropyBalancing | 6.255 ± 6.797 | 5.209 ± 6.748 | 0.541 ± 0.875 |
| 500 | 1000 | IPWTransport | 7.433 ± 6.871 | 6.123 ± 6.830 | 0.698 ± 0.597 |
| 500 | 1000 | OutcomeModelTransport | 7.433 ± 6.876 | 6.115 ± 6.833 | 0.697 ± 0.598 |
| 500 | 1000 | ProposedA | 7.612 ± 7.259 | 6.279 ± 7.125 | 0.738 ± 0.378 |
| 500 | 1000 | ProposedB_LinearStepB | 7.675 ± 7.244 | 6.315 ± 7.105 | 0.739 ± 0.380 |
| 500 | 1000 | ProposedB_SourceDR | 4.391 ± 7.003 | 3.699 ± 7.010 | 0.275 ± 1.212 |
| 500 | 1000 | ProxyOnly | 5.184 ± 7.151 | 4.319 ± 6.993 | 0.409 ± 0.954 |
| 500 | 1000 | TargetOnlyDR | 7.635 ± 7.260 | 6.299 ± 7.150 | 0.736 ± 0.373 |
| 1000 | 0 | AnchorOnly | N/A | N/A | N/A |
| 1000 | 0 | AnchorPlugin | 4.286 ± 6.900 | 3.177 ± 6.892 | -0.731 ± 9.185 |
| 1000 | 0 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 1000 | 0 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 1000 | 0 | EntropyBalancing | 3.966 ± 6.792 | 2.937 ± 6.731 | -0.933 ± 9.300 |
| 1000 | 0 | IPWTransport | 5.225 ± 7.135 | 3.928 ± 7.030 | -0.378 ± 7.089 |
| 1000 | 0 | OutcomeModelTransport | 5.232 ± 7.129 | 3.933 ± 7.029 | -0.456 ± 7.752 |
| 1000 | 0 | ProposedA | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 1000 | 0 | ProposedB_SourceDR | 2.375 ± 6.942 | 1.678 ± 6.920 | -2.384 ± 20.520 |
| 1000 | 0 | ProxyOnly | 3.084 ± 6.897 | 2.175 ± 6.822 | -1.966 ± 17.881 |
| 1000 | 0 | TargetOnlyDR | N/A | N/A | N/A |
| 1000 | 100 | AnchorOnly | 1.647 ± 8.043 | 1.178 ± 8.183 | -0.018 ± 2.170 |
| 1000 | 100 | AnchorPlugin | 3.825 ± 8.412 | 2.727 ± 8.394 | 0.297 ± 1.641 |
| 1000 | 100 | DRLearner_PooledNoSite | 4.556 ± 8.250 | 3.307 ± 8.248 | 0.495 ± 1.292 |
| 1000 | 100 | DRLearner_PooledWithSite | 4.634 ± 8.260 | 3.371 ± 8.256 | 0.521 ± 1.200 |
| 1000 | 100 | EntropyBalancing | 3.457 ± 8.390 | 2.429 ± 8.322 | 0.238 ± 1.784 |
| 1000 | 100 | IPWTransport | 4.410 ± 8.244 | 3.189 ± 8.230 | 0.453 ± 1.393 |
| 1000 | 100 | OutcomeModelTransport | 4.415 ± 8.246 | 3.195 ± 8.229 | 0.457 ± 1.393 |
| 1000 | 100 | ProposedA | 3.988 ± 8.341 | 2.897 ± 8.348 | 0.410 ± 1.296 |
| 1000 | 100 | ProposedB_LinearStepB | 2.342 ± 8.220 | 1.773 ± 8.258 | 0.086 ± 1.983 |
| 1000 | 100 | ProposedB_SourceDR | 1.715 ± 8.145 | 0.966 ± 8.177 | -0.244 ± 2.853 |
| 1000 | 100 | ProxyOnly | 2.738 ± 8.508 | 1.814 ± 8.372 | 0.086 ± 1.884 |
| 1000 | 100 | TargetOnlyDR | 2.631 ± 8.495 | 2.070 ± 8.392 | 0.147 ± 1.851 |
| 1000 | 500 | AnchorOnly | 6.255 ± 7.768 | 5.090 ± 7.677 | 0.654 ± 0.494 |
| 1000 | 500 | AnchorPlugin | 5.633 ± 7.683 | 4.542 ± 7.634 | 0.530 ± 0.645 |
| 1000 | 500 | DRLearner_PooledNoSite | 6.831 ± 7.589 | 5.502 ± 7.558 | 0.735 ± 0.379 |
| 1000 | 500 | DRLearner_PooledWithSite | 6.848 ± 7.591 | 5.518 ± 7.561 | 0.738 ± 0.377 |
| 1000 | 500 | EntropyBalancing | 5.485 ± 7.660 | 4.402 ± 7.572 | 0.539 ± 0.572 |
| 1000 | 500 | IPWTransport | 6.604 ± 7.567 | 5.307 ± 7.530 | 0.706 ± 0.412 |
| 1000 | 500 | OutcomeModelTransport | 6.605 ± 7.565 | 5.307 ± 7.530 | 0.707 ± 0.411 |
| 1000 | 500 | ProposedA | 6.637 ± 7.784 | 5.333 ± 7.715 | 0.671 ± 0.535 |
| 1000 | 500 | ProposedB_LinearStepB | 6.500 ± 7.781 | 5.237 ± 7.699 | 0.669 ± 0.484 |
| 1000 | 500 | ProposedB_SourceDR | 3.773 ± 7.684 | 3.095 ± 7.630 | 0.250 ± 1.140 |
| 1000 | 500 | ProxyOnly | 4.610 ± 7.832 | 3.657 ± 7.718 | 0.361 ± 0.918 |
| 1000 | 500 | TargetOnlyDR | 6.595 ± 7.819 | 5.294 ± 7.715 | 0.655 ± 0.544 |
| 1000 | 1000 | AnchorOnly | 6.937 ± 8.823 | 5.545 ± 8.650 | 0.568 ± 0.997 |
| 1000 | 1000 | AnchorPlugin | 6.135 ± 8.319 | 4.937 ± 8.243 | 0.456 ± 1.217 |
| 1000 | 1000 | DRLearner_PooledNoSite | 7.345 ± 8.830 | 5.886 ± 8.662 | 0.677 ± 0.633 |
| 1000 | 1000 | DRLearner_PooledWithSite | 7.342 ± 8.822 | 5.884 ± 8.658 | 0.676 ± 0.642 |
| 1000 | 1000 | EntropyBalancing | 5.785 ± 8.020 | 4.653 ± 8.011 | 0.311 ± 1.904 |
| 1000 | 1000 | IPWTransport | 6.995 ± 8.594 | 5.599 ± 8.432 | 0.612 ± 0.793 |
| 1000 | 1000 | OutcomeModelTransport | 7.015 ± 8.667 | 5.610 ± 8.480 | 0.613 ± 0.787 |
| 1000 | 1000 | ProposedA | 6.876 ± 8.857 | 5.509 ± 8.694 | 0.572 ± 0.942 |
| 1000 | 1000 | ProposedB_LinearStepB | 6.980 ± 8.869 | 5.586 ± 8.698 | 0.585 ± 0.971 |
| 1000 | 1000 | ProposedB_SourceDR | 3.923 ± 8.348 | 3.183 ± 8.232 | 0.012 ± 2.531 |
| 1000 | 1000 | ProxyOnly | 4.827 ± 8.230 | 3.866 ± 8.230 | 0.107 ± 2.492 |
| 1000 | 1000 | TargetOnlyDR | 6.942 ± 8.857 | 5.537 ± 8.677 | 0.570 ± 0.969 |

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

1. **Best overall PEHE:** DRLearner_PooledWithSite achieves lowest average PEHE (2.953)
2. **Proposed vs ProxyOnly:** Proposed reduces PEHE by 45.4% on average
3. **DRLearner_PooledNoSite:** PEHE improves substantially as m0 increases
4. **DRLearner_PooledWithSite:** PEHE improves substantially as m0 increases
5. **IPWTransport:** PEHE improves substantially as m0 increases
6. **OutcomeModelTransport:** PEHE improves substantially as m0 increases
7. **ProxyOnly:** PEHE improves substantially as m0 increases
8. **Best ranking:** DRLearner_PooledNoSite achieves highest Spearman correlation (0.798)

---

## Appendix: Configuration

```python
sweep_param = 'm0'
sweep_values = [100, 500, 1000]
base_scenario = {'n_proxy_total': 20000, 'C_sources': 10, 'nontransfer_scale': 0.3}
```

