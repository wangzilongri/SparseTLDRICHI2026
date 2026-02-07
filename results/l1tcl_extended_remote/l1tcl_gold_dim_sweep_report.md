# L1-TCL Extended: Gold budget × Dimensionality grid (m0 × d)

**Benchmark ID:** `l1tcl_gold_dim_sweep`

**Generated:** 2026-02-06 02:53

---

## 1. Motivation

**Research Question:** How do target sample size and dimensionality jointly affect transfer learning?

**Why This Matters:**
This 2D grid explores the interaction between:
1. **Gold budget (m0)**: More target data → less need for transfer
2. **Dimensionality (d)**: Higher d → harder estimation, more benefit from source data

**Key Grid:**
- Target: m₀ = m₁ ∈ {50, 100, 200, 500}
- Dimension: d ∈ {10, 20, 50, 100}
- Total: 4 × 4 = 16 scenarios

**Critical Trade-offs:**
- Small m0 + low d: Transfer dominates (easy problem, limited target data)
- Small m0 + high d: Transfer critical (hard problem, limited target data)
- Large m0 + low d: Target-only competitive (easy problem, ample target data)
- Large m0 + high d: Interesting regime - does transfer still help?

---

## 2. Simulation Setup

**L1-TCL DGP (Extended)**:
- Covariates: X ~ N(0, I_d) with d ∈ {10, 20, 50, 100}
- Propensity: P(Z=1|X) = sigmoid(X^T β) 
- Source-target difference: Δβ is 10%-sparse
- Outcome: Y = τZ + α^T X + ε with constant τ = -0.067
- 10 source sites with 500 samples each (5000 total)

### Parameter Summary

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Sweep param** | `m0` | [50, 100, 200, 500] |
| n_proxy_total | 5000 | Total source/proxy observations |
| C_sources | 10 | Number of source sites |
| a5_effective_sparsity | 0.1 | See documentation |
| use_l1tcl_dgp | True | See documentation |

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
| **ProposedA_FullyDirect** | ✗ | ✗ | Proposed: fully joint + direct fitting |
| **ProposedB_LinearStepB** | ✓ | ✓ | Proposed (Option B): placebo-anchored with linear Step B |
| **ProposedB_SourceDR** | ✗ | ✗ | Proposed (Option B): source-DR for placebo-only target |
| **IPWTransport** | ✗ | ✗ | See documentation |
| **EntropyBalancing** | ✗ | ✗ | See documentation |
| **OutcomeModelTransport** | ✗ | ✗ | See documentation |
| **DRLearner_PooledWithSite** | ✗ | ✗ | See documentation |
| **DRLearner_PooledNoSite** | ✗ | ✗ | See documentation |

---

## 5. Experiment Summary

- **Sweep parameter:** `m0` ∈ [50, 100, 200, 500]
- **Monte Carlo replicates:** 20 per scenario
- **Methods evaluated:** 12
- **Total runs:** 3840

---

## 6. Results

### Best Methods (averaged across sweep)

| Metric | Best Method | Value | Direction |
|--------|-------------|-------|----------|
| PEHE | **DRLearner_PooledNoSite** | 0.0459 | ↓ lower |
| ATE Error | **ProposedB_SourceDR** | 0.0183 | ↓ lower |
| Qini AUC | **AnchorOnly** | 0.0000 | ↑ higher |
| Calibration R² | **AnchorOnly** | 1.0000 | ↑ higher |
| CATE ECE | **DRLearner_PooledNoSite** | 0.0374 | ↓ lower |
| Policy Value | **ProposedB_SourceDR** | 0.2017 | ↑ higher |
| Policy Regret | **DRLearner_PooledWithSite** | 0.0036 | ↓ lower |

### Core Metrics

| m0 | m1 | Method | PEHE (↓) | ATE Err (↓) | Spearman (↑) | Qini (↑) |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 0.326 ± 0.044 | 0.104 ± 0.080 | N/A | 0.000 ± 0.000 |
| 50 | 50 | AnchorOnly | 0.468 ± 0.108 | 0.133 ± 0.120 | N/A | 0.000 ± 0.000 |
| 50 | 50 | AnchorOnly | 0.331 ± 0.045 | 0.093 ± 0.065 | N/A | 0.000 ± 0.000 |
| 50 | 50 | AnchorOnly | 0.378 ± 0.060 | 0.133 ± 0.101 | N/A | 0.000 ± 0.000 |
| 50 | 50 | AnchorPlugin | 0.215 ± 0.082 | 0.090 ± 0.079 | N/A | 0.000 ± 0.000 |
| 50 | 50 | AnchorPlugin | 0.706 ± 0.316 | 0.453 ± 0.326 | N/A | 0.000 ± 0.000 |
| 50 | 50 | AnchorPlugin | 0.301 ± 0.118 | 0.188 ± 0.125 | N/A | 0.000 ± 0.000 |
| 50 | 50 | AnchorPlugin | 0.555 ± 0.193 | 0.405 ± 0.234 | N/A | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledNoSite | 0.055 ± 0.017 | 0.031 ± 0.022 | N/A | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledNoSite | 0.160 ± 0.032 | 0.064 ± 0.057 | N/A | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledNoSite | 0.068 ± 0.016 | 0.035 ± 0.024 | N/A | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledNoSite | 0.109 ± 0.016 | 0.047 ± 0.032 | N/A | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledWithSite | 0.055 ± 0.016 | 0.031 ± 0.021 | N/A | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledWithSite | 0.160 ± 0.032 | 0.064 ± 0.057 | N/A | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledWithSite | 0.068 ± 0.016 | 0.035 ± 0.024 | N/A | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledWithSite | 0.109 ± 0.017 | 0.047 ± 0.033 | N/A | 0.000 ± 0.000 |
| 50 | 50 | EntropyBalancing | 0.263 ± 0.142 | 0.126 ± 0.123 | N/A | 0.000 ± 0.000 |
| 50 | 50 | EntropyBalancing | 1.167 ± 0.295 | 0.510 ± 0.455 | N/A | 0.000 ± 0.000 |
| 50 | 50 | EntropyBalancing | 0.497 ± 0.159 | 0.222 ± 0.188 | N/A | 0.000 ± 0.000 |
| 50 | 50 | EntropyBalancing | 1.228 ± 0.413 | 0.661 ± 0.563 | N/A | 0.000 ± 0.000 |
| 50 | 50 | IPWTransport | 0.168 ± 0.085 | 0.105 ± 0.089 | N/A | 0.000 ± 0.000 |
| 50 | 50 | IPWTransport | 0.164 ± 0.036 | 0.068 ± 0.064 | N/A | 0.000 ± 0.000 |
| 50 | 50 | IPWTransport | 0.227 ± 0.091 | 0.134 ± 0.111 | N/A | 0.000 ± 0.000 |
| 50 | 50 | IPWTransport | 0.144 ± 0.036 | 0.095 ± 0.052 | N/A | 0.000 ± 0.000 |
| 50 | 50 | OutcomeModelTransport | 0.061 ± 0.026 | 0.039 ± 0.030 | N/A | 0.000 ± 0.000 |
| 50 | 50 | OutcomeModelTransport | 0.165 ± 0.038 | 0.072 ± 0.063 | N/A | 0.000 ± 0.000 |
| 50 | 50 | OutcomeModelTransport | 0.073 ± 0.023 | 0.041 ± 0.032 | N/A | 0.000 ± 0.000 |
| 50 | 50 | OutcomeModelTransport | 0.127 ± 0.031 | 0.074 ± 0.049 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedA_FullyDirect | 0.341 ± 0.044 | 0.107 ± 0.079 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedA_FullyDirect | 0.451 ± 0.047 | 0.166 ± 0.113 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedA_FullyDirect | 0.323 ± 0.051 | 0.090 ± 0.066 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedA_FullyDirect | 0.364 ± 0.069 | 0.144 ± 0.103 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_LinearStepB | 0.327 ± 0.041 | 0.103 ± 0.080 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_LinearStepB | 0.447 ± 0.100 | 0.128 ± 0.102 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_LinearStepB | 0.328 ± 0.040 | 0.094 ± 0.062 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_LinearStepB | 0.358 ± 0.052 | 0.129 ± 0.098 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_SourceDR | 0.080 ± 0.034 | 0.037 ± 0.035 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_SourceDR | 0.092 ± 0.022 | 0.035 ± 0.027 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_SourceDR | 0.067 ± 0.016 | 0.031 ± 0.019 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_SourceDR | 0.078 ± 0.022 | 0.024 ± 0.016 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProxyOnly | 0.427 ± 0.138 | 0.189 ± 0.188 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProxyOnly | 1.019 ± 0.599 | 0.855 ± 0.658 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProxyOnly | 0.560 ± 0.244 | 0.375 ± 0.302 | N/A | 0.000 ± 0.000 |
| 50 | 50 | ProxyOnly | 0.979 ± 0.476 | 0.844 ± 0.527 | N/A | 0.000 ± 0.000 |
| 50 | 50 | TargetOnlyDR | 0.348 ± 0.058 | 0.112 ± 0.084 | N/A | 0.000 ± 0.000 |
| 50 | 50 | TargetOnlyDR | 0.533 ± 0.120 | 0.162 ± 0.153 | N/A | 0.000 ± 0.000 |
| 50 | 50 | TargetOnlyDR | 0.361 ± 0.050 | 0.088 ± 0.073 | N/A | 0.000 ± 0.000 |
| 50 | 50 | TargetOnlyDR | 0.422 ± 0.084 | 0.157 ± 0.126 | N/A | 0.000 ± 0.000 |
| 100 | 100 | AnchorOnly | 0.299 ± 0.058 | 0.057 ± 0.038 | N/A | 0.000 ± 0.000 |
| 100 | 100 | AnchorOnly | 0.340 ± 0.060 | 0.086 ± 0.076 | N/A | 0.000 ± 0.000 |
| 100 | 100 | AnchorOnly | 0.274 ± 0.044 | 0.064 ± 0.049 | N/A | 0.000 ± 0.000 |
| 100 | 100 | AnchorOnly | 0.263 ± 0.032 | 0.052 ± 0.039 | N/A | 0.000 ± 0.000 |
| 100 | 100 | AnchorPlugin | 0.550 ± 0.165 | 0.314 ± 0.235 | N/A | 0.000 ± 0.000 |
| 100 | 100 | AnchorPlugin | 0.808 ± 0.305 | 0.470 ± 0.388 | N/A | 0.000 ± 0.000 |
| 100 | 100 | AnchorPlugin | 0.321 ± 0.121 | 0.189 ± 0.146 | N/A | 0.000 ± 0.000 |
| 100 | 100 | AnchorPlugin | 0.190 ± 0.038 | 0.071 ± 0.054 | N/A | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledNoSite | 0.103 ± 0.017 | 0.041 ± 0.029 | N/A | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledNoSite | 0.151 ± 0.015 | 0.048 ± 0.039 | N/A | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledNoSite | 0.064 ± 0.011 | 0.025 ± 0.021 | N/A | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledNoSite | 0.046 ± 0.016 | 0.026 ± 0.019 | N/A | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledWithSite | 0.102 ± 0.016 | 0.040 ± 0.029 | N/A | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledWithSite | 0.152 ± 0.015 | 0.048 ± 0.040 | N/A | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledWithSite | 0.065 ± 0.012 | 0.025 ± 0.021 | N/A | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledWithSite | 0.046 ± 0.016 | 0.026 ± 0.020 | N/A | 0.000 ± 0.000 |
| 100 | 100 | EntropyBalancing | 1.174 ± 0.376 | 0.593 ± 0.521 | N/A | 0.000 ± 0.000 |
| 100 | 100 | EntropyBalancing | 1.147 ± 0.230 | 0.464 ± 0.365 | N/A | 0.000 ± 0.000 |
| 100 | 100 | EntropyBalancing | 0.592 ± 0.340 | 0.307 ± 0.339 | N/A | 0.000 ± 0.000 |
| 100 | 100 | EntropyBalancing | 0.179 ± 0.089 | 0.058 ± 0.059 | N/A | 0.000 ± 0.000 |
| 100 | 100 | IPWTransport | 0.166 ± 0.060 | 0.109 ± 0.070 | N/A | 0.000 ± 0.000 |
| 100 | 100 | IPWTransport | 0.183 ± 0.046 | 0.105 ± 0.070 | N/A | 0.000 ± 0.000 |
| 100 | 100 | IPWTransport | 0.259 ± 0.092 | 0.143 ± 0.110 | N/A | 0.000 ± 0.000 |
| 100 | 100 | IPWTransport | 0.156 ± 0.091 | 0.065 ± 0.084 | N/A | 0.000 ± 0.000 |
| 100 | 100 | OutcomeModelTransport | 0.114 ± 0.026 | 0.057 ± 0.043 | N/A | 0.000 ± 0.000 |
| 100 | 100 | OutcomeModelTransport | 0.180 ± 0.047 | 0.099 ± 0.073 | N/A | 0.000 ± 0.000 |
| 100 | 100 | OutcomeModelTransport | 0.073 ± 0.024 | 0.039 ± 0.032 | N/A | 0.000 ± 0.000 |
| 100 | 100 | OutcomeModelTransport | 0.048 ± 0.018 | 0.028 ± 0.021 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedA_FullyDirect | 0.245 ± 0.034 | 0.063 ± 0.051 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedA_FullyDirect | 0.290 ± 0.050 | 0.087 ± 0.073 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedA_FullyDirect | 0.244 ± 0.035 | 0.060 ± 0.056 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedA_FullyDirect | 0.259 ± 0.028 | 0.051 ± 0.036 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_LinearStepB | 0.282 ± 0.056 | 0.053 ± 0.037 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_LinearStepB | 0.310 ± 0.061 | 0.089 ± 0.068 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_LinearStepB | 0.264 ± 0.041 | 0.064 ± 0.048 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_LinearStepB | 0.260 ± 0.029 | 0.053 ± 0.040 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_SourceDR | 0.069 ± 0.033 | 0.020 ± 0.018 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_SourceDR | 0.088 ± 0.028 | 0.028 ± 0.026 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_SourceDR | 0.065 ± 0.018 | 0.024 ± 0.021 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_SourceDR | 0.061 ± 0.013 | 0.019 ± 0.015 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProxyOnly | 0.795 ± 0.424 | 0.609 ± 0.525 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProxyOnly | 1.074 ± 0.664 | 0.934 ± 0.728 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProxyOnly | 0.581 ± 0.250 | 0.401 ± 0.315 | N/A | 0.000 ± 0.000 |
| 100 | 100 | ProxyOnly | 0.377 ± 0.068 | 0.143 ± 0.095 | N/A | 0.000 ± 0.000 |
| 100 | 100 | TargetOnlyDR | 0.314 ± 0.038 | 0.066 ± 0.055 | N/A | 0.000 ± 0.000 |
| 100 | 100 | TargetOnlyDR | 0.378 ± 0.046 | 0.099 ± 0.073 | N/A | 0.000 ± 0.000 |
| 100 | 100 | TargetOnlyDR | 0.293 ± 0.047 | 0.063 ± 0.046 | N/A | 0.000 ± 0.000 |
| 100 | 100 | TargetOnlyDR | 0.269 ± 0.042 | 0.062 ± 0.041 | N/A | 0.000 ± 0.000 |
| 200 | 200 | AnchorOnly | 0.249 ± 0.055 | 0.064 ± 0.061 | N/A | 0.000 ± 0.000 |
| 200 | 200 | AnchorOnly | 0.203 ± 0.033 | 0.052 ± 0.041 | N/A | 0.000 ± 0.000 |
| 200 | 200 | AnchorOnly | 0.212 ± 0.026 | 0.053 ± 0.041 | N/A | 0.000 ± 0.000 |
| 200 | 200 | AnchorOnly | 0.213 ± 0.051 | 0.043 ± 0.030 | N/A | 0.000 ± 0.000 |
| 200 | 200 | AnchorPlugin | 0.976 ± 0.300 | 0.452 ± 0.403 | N/A | 0.000 ± 0.000 |
| 200 | 200 | AnchorPlugin | 0.170 ± 0.028 | 0.052 ± 0.035 | N/A | 0.000 ± 0.000 |
| 200 | 200 | AnchorPlugin | 0.626 ± 0.211 | 0.334 ± 0.281 | N/A | 0.000 ± 0.000 |
| 200 | 200 | AnchorPlugin | 0.331 ± 0.090 | 0.179 ± 0.122 | N/A | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledNoSite | 0.145 ± 0.015 | 0.042 ± 0.029 | N/A | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledNoSite | 0.052 ± 0.018 | 0.031 ± 0.023 | N/A | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledNoSite | 0.101 ± 0.012 | 0.035 ± 0.025 | N/A | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledNoSite | 0.067 ± 0.014 | 0.031 ± 0.024 | N/A | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledWithSite | 0.145 ± 0.015 | 0.042 ± 0.028 | N/A | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledWithSite | 0.052 ± 0.018 | 0.031 ± 0.023 | N/A | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledWithSite | 0.101 ± 0.012 | 0.034 ± 0.026 | N/A | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledWithSite | 0.068 ± 0.014 | 0.030 ± 0.024 | N/A | 0.000 ± 0.000 |
| 200 | 200 | EntropyBalancing | 1.113 ± 0.207 | 0.457 ± 0.340 | N/A | 0.000 ± 0.000 |
| 200 | 200 | EntropyBalancing | 0.214 ± 0.093 | 0.095 ± 0.065 | N/A | 0.000 ± 0.000 |
| 200 | 200 | EntropyBalancing | 1.354 ± 0.686 | 0.837 ± 0.829 | N/A | 0.000 ± 0.000 |
| 200 | 200 | EntropyBalancing | 0.529 ± 0.265 | 0.286 ± 0.275 | N/A | 0.000 ± 0.000 |
| 200 | 200 | IPWTransport | 0.181 ± 0.046 | 0.096 ± 0.074 | N/A | 0.000 ± 0.000 |
| 200 | 200 | IPWTransport | 0.202 ± 0.072 | 0.093 ± 0.067 | N/A | 0.000 ± 0.000 |
| 200 | 200 | IPWTransport | 0.198 ± 0.079 | 0.122 ± 0.096 | N/A | 0.000 ± 0.000 |
| 200 | 200 | IPWTransport | 0.316 ± 0.114 | 0.158 ± 0.135 | N/A | 0.000 ± 0.000 |
| 200 | 200 | OutcomeModelTransport | 0.182 ± 0.047 | 0.100 ± 0.074 | N/A | 0.000 ± 0.000 |
| 200 | 200 | OutcomeModelTransport | 0.052 ± 0.018 | 0.032 ± 0.021 | N/A | 0.000 ± 0.000 |
| 200 | 200 | OutcomeModelTransport | 0.112 ± 0.021 | 0.051 ± 0.037 | N/A | 0.000 ± 0.000 |
| 200 | 200 | OutcomeModelTransport | 0.085 ± 0.025 | 0.052 ± 0.036 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedA_FullyDirect | 0.185 ± 0.023 | 0.049 ± 0.042 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedA_FullyDirect | 0.198 ± 0.029 | 0.053 ± 0.037 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedA_FullyDirect | 0.176 ± 0.021 | 0.042 ± 0.037 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedA_FullyDirect | 0.191 ± 0.028 | 0.043 ± 0.035 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_LinearStepB | 0.198 ± 0.039 | 0.052 ± 0.044 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_LinearStepB | 0.203 ± 0.034 | 0.052 ± 0.041 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_LinearStepB | 0.186 ± 0.022 | 0.047 ± 0.037 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_LinearStepB | 0.209 ± 0.046 | 0.040 ± 0.033 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_SourceDR | 0.068 ± 0.017 | 0.021 ± 0.021 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_SourceDR | 0.067 ± 0.018 | 0.026 ± 0.019 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_SourceDR | 0.059 ± 0.014 | 0.021 ± 0.015 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_SourceDR | 0.065 ± 0.015 | 0.025 ± 0.021 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProxyOnly | 1.058 ± 0.765 | 0.912 ± 0.824 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProxyOnly | 0.303 ± 0.081 | 0.111 ± 0.081 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProxyOnly | 0.783 ± 0.457 | 0.649 ± 0.517 | N/A | 0.000 ± 0.000 |
| 200 | 200 | ProxyOnly | 0.521 ± 0.187 | 0.357 ± 0.233 | N/A | 0.000 ± 0.000 |
| 200 | 200 | TargetOnlyDR | 0.304 ± 0.050 | 0.078 ± 0.078 | N/A | 0.000 ± 0.000 |
| 200 | 200 | TargetOnlyDR | 0.203 ± 0.026 | 0.055 ± 0.040 | N/A | 0.000 ± 0.000 |
| 200 | 200 | TargetOnlyDR | 0.237 ± 0.028 | 0.059 ± 0.043 | N/A | 0.000 ± 0.000 |
| 200 | 200 | TargetOnlyDR | 0.217 ± 0.038 | 0.053 ± 0.035 | N/A | 0.000 ± 0.000 |
| 500 | 500 | AnchorOnly | 0.140 ± 0.018 | 0.029 ± 0.021 | N/A | 0.000 ± 0.000 |
| 500 | 500 | AnchorOnly | 0.126 ± 0.017 | 0.024 ± 0.023 | N/A | 0.000 ± 0.000 |
| 500 | 500 | AnchorOnly | 0.175 ± 0.043 | 0.047 ± 0.027 | N/A | 0.000 ± 0.000 |
| 500 | 500 | AnchorOnly | 0.134 ± 0.019 | 0.028 ± 0.025 | N/A | 0.000 ± 0.000 |
| 500 | 500 | AnchorPlugin | 0.200 ± 0.042 | 0.084 ± 0.060 | N/A | 0.000 ± 0.000 |
| 500 | 500 | AnchorPlugin | 0.313 ± 0.064 | 0.133 ± 0.085 | N/A | 0.000 ± 0.000 |
| 500 | 500 | AnchorPlugin | 1.180 ± 0.385 | 0.778 ± 0.508 | N/A | 0.000 ± 0.000 |
| 500 | 500 | AnchorPlugin | 0.630 ± 0.112 | 0.291 ± 0.195 | N/A | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledNoSite | 0.046 ± 0.015 | 0.026 ± 0.017 | N/A | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledNoSite | 0.059 ± 0.012 | 0.020 ± 0.016 | N/A | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledNoSite | 0.133 ± 0.008 | 0.025 ± 0.017 | N/A | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledNoSite | 0.092 ± 0.008 | 0.022 ± 0.015 | N/A | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledWithSite | 0.046 ± 0.015 | 0.026 ± 0.017 | N/A | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledWithSite | 0.059 ± 0.012 | 0.020 ± 0.015 | N/A | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledWithSite | 0.133 ± 0.008 | 0.025 ± 0.017 | N/A | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledWithSite | 0.093 ± 0.008 | 0.023 ± 0.015 | N/A | 0.000 ± 0.000 |
| 500 | 500 | EntropyBalancing | 0.233 ± 0.144 | 0.087 ± 0.113 | N/A | 0.000 ± 0.000 |
| 500 | 500 | EntropyBalancing | 0.442 ± 0.174 | 0.200 ± 0.133 | N/A | 0.000 ± 0.000 |
| 500 | 500 | EntropyBalancing | 1.158 ± 0.262 | 0.480 ± 0.401 | N/A | 0.000 ± 0.000 |
| 500 | 500 | EntropyBalancing | 1.141 ± 0.266 | 0.653 ± 0.393 | N/A | 0.000 ± 0.000 |
| 500 | 500 | IPWTransport | 0.240 ± 0.121 | 0.083 ± 0.098 | N/A | 0.000 ± 0.000 |
| 500 | 500 | IPWTransport | 0.329 ± 0.083 | 0.138 ± 0.083 | N/A | 0.000 ± 0.000 |
| 500 | 500 | IPWTransport | 0.168 ± 0.042 | 0.082 ± 0.067 | N/A | 0.000 ± 0.000 |
| 500 | 500 | IPWTransport | 0.213 ± 0.075 | 0.139 ± 0.085 | N/A | 0.000 ± 0.000 |
| 500 | 500 | OutcomeModelTransport | 0.054 ± 0.018 | 0.032 ± 0.023 | N/A | 0.000 ± 0.000 |
| 500 | 500 | OutcomeModelTransport | 0.070 ± 0.014 | 0.032 ± 0.024 | N/A | 0.000 ± 0.000 |
| 500 | 500 | OutcomeModelTransport | 0.163 ± 0.027 | 0.078 ± 0.051 | N/A | 0.000 ± 0.000 |
| 500 | 500 | OutcomeModelTransport | 0.111 ± 0.027 | 0.046 ± 0.043 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedA_FullyDirect | 0.134 ± 0.017 | 0.032 ± 0.021 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedA_FullyDirect | 0.122 ± 0.020 | 0.023 ± 0.020 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedA_FullyDirect | 0.115 ± 0.017 | 0.029 ± 0.020 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedA_FullyDirect | 0.116 ± 0.014 | 0.028 ± 0.023 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_LinearStepB | 0.140 ± 0.018 | 0.029 ± 0.020 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_LinearStepB | 0.125 ± 0.017 | 0.024 ± 0.021 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_LinearStepB | 0.120 ± 0.021 | 0.031 ± 0.022 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_LinearStepB | 0.120 ± 0.015 | 0.027 ± 0.022 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_SourceDR | 0.062 ± 0.020 | 0.022 ± 0.020 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_SourceDR | 0.064 ± 0.013 | 0.018 ± 0.017 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_SourceDR | 0.066 ± 0.020 | 0.026 ± 0.025 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_SourceDR | 0.059 ± 0.017 | 0.019 ± 0.021 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProxyOnly | 0.292 ± 0.092 | 0.154 ± 0.111 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProxyOnly | 0.423 ± 0.146 | 0.284 ± 0.180 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProxyOnly | 1.641 ± 0.941 | 1.564 ± 0.976 | N/A | 0.000 ± 0.000 |
| 500 | 500 | ProxyOnly | 0.732 ± 0.347 | 0.581 ± 0.407 | N/A | 0.000 ± 0.000 |
| 500 | 500 | TargetOnlyDR | 0.139 ± 0.019 | 0.030 ± 0.022 | N/A | 0.000 ± 0.000 |
| 500 | 500 | TargetOnlyDR | 0.133 ± 0.022 | 0.023 ± 0.028 | N/A | 0.000 ± 0.000 |
| 500 | 500 | TargetOnlyDR | 0.207 ± 0.026 | 0.064 ± 0.047 | N/A | 0.000 ± 0.000 |
| 500 | 500 | TargetOnlyDR | 0.162 ± 0.022 | 0.031 ± 0.028 | N/A | 0.000 ± 0.000 |

### Targeting / Ranking Metrics

| m0 | m1 | Method | Top-10% (↑) | Top-20% (↑) | Kendall (↑) |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | N/A | N/A | N/A |
| 50 | 50 | AnchorOnly | N/A | N/A | N/A |
| 50 | 50 | AnchorOnly | N/A | N/A | N/A |
| 50 | 50 | AnchorOnly | N/A | N/A | N/A |
| 50 | 50 | AnchorPlugin | N/A | N/A | N/A |
| 50 | 50 | AnchorPlugin | N/A | N/A | N/A |
| 50 | 50 | AnchorPlugin | N/A | N/A | N/A |
| 50 | 50 | AnchorPlugin | N/A | N/A | N/A |
| 50 | 50 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 50 | 50 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 50 | 50 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 50 | 50 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 50 | 50 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 50 | 50 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 50 | 50 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 50 | 50 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 50 | 50 | EntropyBalancing | N/A | N/A | N/A |
| 50 | 50 | EntropyBalancing | N/A | N/A | N/A |
| 50 | 50 | EntropyBalancing | N/A | N/A | N/A |
| 50 | 50 | EntropyBalancing | N/A | N/A | N/A |
| 50 | 50 | IPWTransport | N/A | N/A | N/A |
| 50 | 50 | IPWTransport | N/A | N/A | N/A |
| 50 | 50 | IPWTransport | N/A | N/A | N/A |
| 50 | 50 | IPWTransport | N/A | N/A | N/A |
| 50 | 50 | OutcomeModelTransport | N/A | N/A | N/A |
| 50 | 50 | OutcomeModelTransport | N/A | N/A | N/A |
| 50 | 50 | OutcomeModelTransport | N/A | N/A | N/A |
| 50 | 50 | OutcomeModelTransport | N/A | N/A | N/A |
| 50 | 50 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 50 | 50 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 50 | 50 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 50 | 50 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 50 | 50 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 50 | 50 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 50 | 50 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 50 | 50 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 50 | 50 | ProposedB_SourceDR | N/A | N/A | N/A |
| 50 | 50 | ProposedB_SourceDR | N/A | N/A | N/A |
| 50 | 50 | ProposedB_SourceDR | N/A | N/A | N/A |
| 50 | 50 | ProposedB_SourceDR | N/A | N/A | N/A |
| 50 | 50 | ProxyOnly | N/A | N/A | N/A |
| 50 | 50 | ProxyOnly | N/A | N/A | N/A |
| 50 | 50 | ProxyOnly | N/A | N/A | N/A |
| 50 | 50 | ProxyOnly | N/A | N/A | N/A |
| 50 | 50 | TargetOnlyDR | N/A | N/A | N/A |
| 50 | 50 | TargetOnlyDR | N/A | N/A | N/A |
| 50 | 50 | TargetOnlyDR | N/A | N/A | N/A |
| 50 | 50 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | N/A | N/A | N/A |
| 100 | 100 | AnchorOnly | N/A | N/A | N/A |
| 100 | 100 | AnchorPlugin | N/A | N/A | N/A |
| 100 | 100 | AnchorPlugin | N/A | N/A | N/A |
| 100 | 100 | AnchorPlugin | N/A | N/A | N/A |
| 100 | 100 | AnchorPlugin | N/A | N/A | N/A |
| 100 | 100 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 100 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 100 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 100 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 100 | 100 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 100 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 100 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 100 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 100 | 100 | EntropyBalancing | N/A | N/A | N/A |
| 100 | 100 | EntropyBalancing | N/A | N/A | N/A |
| 100 | 100 | EntropyBalancing | N/A | N/A | N/A |
| 100 | 100 | EntropyBalancing | N/A | N/A | N/A |
| 100 | 100 | IPWTransport | N/A | N/A | N/A |
| 100 | 100 | IPWTransport | N/A | N/A | N/A |
| 100 | 100 | IPWTransport | N/A | N/A | N/A |
| 100 | 100 | IPWTransport | N/A | N/A | N/A |
| 100 | 100 | OutcomeModelTransport | N/A | N/A | N/A |
| 100 | 100 | OutcomeModelTransport | N/A | N/A | N/A |
| 100 | 100 | OutcomeModelTransport | N/A | N/A | N/A |
| 100 | 100 | OutcomeModelTransport | N/A | N/A | N/A |
| 100 | 100 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 100 | 100 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 100 | 100 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 100 | 100 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 100 | 100 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 100 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 100 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 100 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 100 | 100 | ProposedB_SourceDR | N/A | N/A | N/A |
| 100 | 100 | ProposedB_SourceDR | N/A | N/A | N/A |
| 100 | 100 | ProposedB_SourceDR | N/A | N/A | N/A |
| 100 | 100 | ProposedB_SourceDR | N/A | N/A | N/A |
| 100 | 100 | ProxyOnly | N/A | N/A | N/A |
| 100 | 100 | ProxyOnly | N/A | N/A | N/A |
| 100 | 100 | ProxyOnly | N/A | N/A | N/A |
| 100 | 100 | ProxyOnly | N/A | N/A | N/A |
| 100 | 100 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | TargetOnlyDR | N/A | N/A | N/A |
| 100 | 100 | TargetOnlyDR | N/A | N/A | N/A |
| 200 | 200 | AnchorOnly | N/A | N/A | N/A |
| 200 | 200 | AnchorOnly | N/A | N/A | N/A |
| 200 | 200 | AnchorOnly | N/A | N/A | N/A |
| 200 | 200 | AnchorOnly | N/A | N/A | N/A |
| 200 | 200 | AnchorPlugin | N/A | N/A | N/A |
| 200 | 200 | AnchorPlugin | N/A | N/A | N/A |
| 200 | 200 | AnchorPlugin | N/A | N/A | N/A |
| 200 | 200 | AnchorPlugin | N/A | N/A | N/A |
| 200 | 200 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 200 | 200 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 200 | 200 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 200 | 200 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 200 | 200 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 200 | 200 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 200 | 200 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 200 | 200 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 200 | 200 | EntropyBalancing | N/A | N/A | N/A |
| 200 | 200 | EntropyBalancing | N/A | N/A | N/A |
| 200 | 200 | EntropyBalancing | N/A | N/A | N/A |
| 200 | 200 | EntropyBalancing | N/A | N/A | N/A |
| 200 | 200 | IPWTransport | N/A | N/A | N/A |
| 200 | 200 | IPWTransport | N/A | N/A | N/A |
| 200 | 200 | IPWTransport | N/A | N/A | N/A |
| 200 | 200 | IPWTransport | N/A | N/A | N/A |
| 200 | 200 | OutcomeModelTransport | N/A | N/A | N/A |
| 200 | 200 | OutcomeModelTransport | N/A | N/A | N/A |
| 200 | 200 | OutcomeModelTransport | N/A | N/A | N/A |
| 200 | 200 | OutcomeModelTransport | N/A | N/A | N/A |
| 200 | 200 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 200 | 200 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 200 | 200 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 200 | 200 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 200 | 200 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 200 | 200 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 200 | 200 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 200 | 200 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 200 | 200 | ProposedB_SourceDR | N/A | N/A | N/A |
| 200 | 200 | ProposedB_SourceDR | N/A | N/A | N/A |
| 200 | 200 | ProposedB_SourceDR | N/A | N/A | N/A |
| 200 | 200 | ProposedB_SourceDR | N/A | N/A | N/A |
| 200 | 200 | ProxyOnly | N/A | N/A | N/A |
| 200 | 200 | ProxyOnly | N/A | N/A | N/A |
| 200 | 200 | ProxyOnly | N/A | N/A | N/A |
| 200 | 200 | ProxyOnly | N/A | N/A | N/A |
| 200 | 200 | TargetOnlyDR | N/A | N/A | N/A |
| 200 | 200 | TargetOnlyDR | N/A | N/A | N/A |
| 200 | 200 | TargetOnlyDR | N/A | N/A | N/A |
| 200 | 200 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 500 | AnchorOnly | N/A | N/A | N/A |
| 500 | 500 | AnchorOnly | N/A | N/A | N/A |
| 500 | 500 | AnchorOnly | N/A | N/A | N/A |
| 500 | 500 | AnchorOnly | N/A | N/A | N/A |
| 500 | 500 | AnchorPlugin | N/A | N/A | N/A |
| 500 | 500 | AnchorPlugin | N/A | N/A | N/A |
| 500 | 500 | AnchorPlugin | N/A | N/A | N/A |
| 500 | 500 | AnchorPlugin | N/A | N/A | N/A |
| 500 | 500 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 500 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 500 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 500 | DRLearner_PooledNoSite | N/A | N/A | N/A |
| 500 | 500 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 500 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 500 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 500 | DRLearner_PooledWithSite | N/A | N/A | N/A |
| 500 | 500 | EntropyBalancing | N/A | N/A | N/A |
| 500 | 500 | EntropyBalancing | N/A | N/A | N/A |
| 500 | 500 | EntropyBalancing | N/A | N/A | N/A |
| 500 | 500 | EntropyBalancing | N/A | N/A | N/A |
| 500 | 500 | IPWTransport | N/A | N/A | N/A |
| 500 | 500 | IPWTransport | N/A | N/A | N/A |
| 500 | 500 | IPWTransport | N/A | N/A | N/A |
| 500 | 500 | IPWTransport | N/A | N/A | N/A |
| 500 | 500 | OutcomeModelTransport | N/A | N/A | N/A |
| 500 | 500 | OutcomeModelTransport | N/A | N/A | N/A |
| 500 | 500 | OutcomeModelTransport | N/A | N/A | N/A |
| 500 | 500 | OutcomeModelTransport | N/A | N/A | N/A |
| 500 | 500 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 500 | 500 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 500 | 500 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 500 | 500 | ProposedA_FullyDirect | N/A | N/A | N/A |
| 500 | 500 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 500 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 500 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 500 | ProposedB_LinearStepB | N/A | N/A | N/A |
| 500 | 500 | ProposedB_SourceDR | N/A | N/A | N/A |
| 500 | 500 | ProposedB_SourceDR | N/A | N/A | N/A |
| 500 | 500 | ProposedB_SourceDR | N/A | N/A | N/A |
| 500 | 500 | ProposedB_SourceDR | N/A | N/A | N/A |
| 500 | 500 | ProxyOnly | N/A | N/A | N/A |
| 500 | 500 | ProxyOnly | N/A | N/A | N/A |
| 500 | 500 | ProxyOnly | N/A | N/A | N/A |
| 500 | 500 | ProxyOnly | N/A | N/A | N/A |
| 500 | 500 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 500 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 500 | TargetOnlyDR | N/A | N/A | N/A |
| 500 | 500 | TargetOnlyDR | N/A | N/A | N/A |

### ATE Estimation

| m0 | m1 | Method | ATE Est | ATE Err (↓) | ATE Bias |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | -0.042 ± 0.131 | 0.104 ± 0.080 | 0.025 ± 0.131 |
| 50 | 50 | AnchorOnly | -0.157 ± 0.157 | 0.133 ± 0.120 | -0.090 ± 0.157 |
| 50 | 50 | AnchorOnly | -0.071 ± 0.115 | 0.093 ± 0.065 | -0.004 ± 0.115 |
| 50 | 50 | AnchorOnly | -0.010 ± 0.159 | 0.133 ± 0.101 | 0.057 ± 0.159 |
| 50 | 50 | AnchorPlugin | -0.087 ± 0.120 | 0.090 ± 0.079 | -0.020 ± 0.120 |
| 50 | 50 | AnchorPlugin | -0.135 ± 0.564 | 0.453 ± 0.326 | -0.068 ± 0.564 |
| 50 | 50 | AnchorPlugin | -0.064 ± 0.230 | 0.188 ± 0.125 | 0.003 ± 0.230 |
| 50 | 50 | AnchorPlugin | 0.086 ± 0.450 | 0.405 ± 0.234 | 0.153 ± 0.450 |
| 50 | 50 | DRLearner_PooledNoSite | -0.069 ± 0.038 | 0.031 ± 0.022 | -0.002 ± 0.038 |
| 50 | 50 | DRLearner_PooledNoSite | -0.047 ± 0.085 | 0.064 ± 0.057 | 0.020 ± 0.085 |
| 50 | 50 | DRLearner_PooledNoSite | -0.077 ± 0.042 | 0.035 ± 0.024 | -0.010 ± 0.042 |
| 50 | 50 | DRLearner_PooledNoSite | -0.056 ± 0.057 | 0.047 ± 0.032 | 0.011 ± 0.057 |
| 50 | 50 | DRLearner_PooledWithSite | -0.069 ± 0.038 | 0.031 ± 0.021 | -0.002 ± 0.038 |
| 50 | 50 | DRLearner_PooledWithSite | -0.047 ± 0.085 | 0.064 ± 0.057 | 0.020 ± 0.085 |
| 50 | 50 | DRLearner_PooledWithSite | -0.077 ± 0.042 | 0.035 ± 0.024 | -0.010 ± 0.042 |
| 50 | 50 | DRLearner_PooledWithSite | -0.055 ± 0.057 | 0.047 ± 0.033 | 0.012 ± 0.057 |
| 50 | 50 | EntropyBalancing | -0.076 ± 0.178 | 0.126 ± 0.123 | -0.009 ± 0.178 |
| 50 | 50 | EntropyBalancing | 0.342 ± 0.552 | 0.510 ± 0.455 | 0.409 ± 0.552 |
| 50 | 50 | EntropyBalancing | -0.142 ± 0.285 | 0.222 ± 0.188 | -0.075 ± 0.285 |
| 50 | 50 | EntropyBalancing | -0.062 ± 0.881 | 0.661 ± 0.563 | 0.005 ± 0.881 |
| 50 | 50 | IPWTransport | -0.085 ± 0.139 | 0.105 ± 0.089 | -0.018 ± 0.139 |
| 50 | 50 | IPWTransport | -0.032 ± 0.088 | 0.068 ± 0.064 | 0.035 ± 0.088 |
| 50 | 50 | IPWTransport | -0.111 ± 0.171 | 0.134 ± 0.111 | -0.044 ± 0.171 |
| 50 | 50 | IPWTransport | -0.039 ± 0.107 | 0.095 ± 0.052 | 0.028 ± 0.107 |
| 50 | 50 | OutcomeModelTransport | -0.070 ± 0.049 | 0.039 ± 0.030 | -0.003 ± 0.049 |
| 50 | 50 | OutcomeModelTransport | -0.029 ± 0.089 | 0.072 ± 0.063 | 0.038 ± 0.089 |
| 50 | 50 | OutcomeModelTransport | -0.078 ± 0.051 | 0.041 ± 0.032 | -0.011 ± 0.051 |
| 50 | 50 | OutcomeModelTransport | -0.062 ± 0.090 | 0.074 ± 0.049 | 0.005 ± 0.090 |
| 50 | 50 | ProposedA_FullyDirect | -0.054 ± 0.134 | 0.107 ± 0.079 | 0.013 ± 0.134 |
| 50 | 50 | ProposedA_FullyDirect | -0.171 ± 0.174 | 0.166 ± 0.113 | -0.104 ± 0.174 |
| 50 | 50 | ProposedA_FullyDirect | -0.067 ± 0.114 | 0.090 ± 0.066 | -0.000 ± 0.114 |
| 50 | 50 | ProposedA_FullyDirect | -0.028 ± 0.176 | 0.144 ± 0.103 | 0.039 ± 0.176 |
| 50 | 50 | ProposedB_LinearStepB | -0.043 ± 0.131 | 0.103 ± 0.080 | 0.024 ± 0.131 |
| 50 | 50 | ProposedB_LinearStepB | -0.130 ± 0.153 | 0.128 ± 0.102 | -0.063 ± 0.153 |
| 50 | 50 | ProposedB_LinearStepB | -0.074 ± 0.114 | 0.094 ± 0.062 | -0.007 ± 0.114 |
| 50 | 50 | ProposedB_LinearStepB | -0.015 ± 0.156 | 0.129 ± 0.098 | 0.052 ± 0.156 |
| 50 | 50 | ProposedB_SourceDR | -0.066 ± 0.051 | 0.037 ± 0.035 | 0.001 ± 0.051 |
| 50 | 50 | ProposedB_SourceDR | -0.070 ± 0.045 | 0.035 ± 0.027 | -0.003 ± 0.045 |
| 50 | 50 | ProposedB_SourceDR | -0.083 ± 0.033 | 0.031 ± 0.019 | -0.016 ± 0.033 |
| 50 | 50 | ProposedB_SourceDR | -0.073 ± 0.029 | 0.024 ± 0.016 | -0.006 ± 0.029 |
| 50 | 50 | ProxyOnly | -0.106 ± 0.267 | 0.189 ± 0.188 | -0.039 ± 0.267 |
| 50 | 50 | ProxyOnly | -0.269 ± 1.077 | 0.855 ± 0.658 | -0.202 ± 1.077 |
| 50 | 50 | ProxyOnly | -0.039 ± 0.489 | 0.375 ± 0.302 | 0.028 ± 0.489 |
| 50 | 50 | ProxyOnly | 0.251 ± 0.959 | 0.844 ± 0.527 | 0.318 ± 0.959 |
| 50 | 50 | TargetOnlyDR | -0.036 ± 0.139 | 0.112 ± 0.084 | 0.031 ± 0.139 |
| 50 | 50 | TargetOnlyDR | -0.181 ± 0.193 | 0.162 ± 0.153 | -0.114 ± 0.193 |
| 50 | 50 | TargetOnlyDR | -0.066 ± 0.116 | 0.088 ± 0.073 | 0.001 ± 0.116 |
| 50 | 50 | TargetOnlyDR | 0.012 ± 0.187 | 0.157 ± 0.126 | 0.079 ± 0.187 |
| 100 | 100 | AnchorOnly | -0.086 ± 0.067 | 0.057 ± 0.038 | -0.019 ± 0.067 |
| 100 | 100 | AnchorOnly | -0.053 ± 0.115 | 0.086 ± 0.076 | 0.014 ± 0.115 |
| 100 | 100 | AnchorOnly | -0.068 ± 0.082 | 0.064 ± 0.049 | -0.001 ± 0.082 |
| 100 | 100 | AnchorOnly | -0.082 ± 0.065 | 0.052 ± 0.039 | -0.015 ± 0.065 |
| 100 | 100 | AnchorPlugin | -0.120 ± 0.395 | 0.314 ± 0.235 | -0.053 ± 0.395 |
| 100 | 100 | AnchorPlugin | -0.026 ± 0.618 | 0.470 ± 0.388 | 0.041 ± 0.618 |
| 100 | 100 | AnchorPlugin | -0.086 ± 0.242 | 0.189 ± 0.146 | -0.019 ± 0.242 |
| 100 | 100 | AnchorPlugin | -0.083 ± 0.089 | 0.071 ± 0.054 | -0.016 ± 0.089 |
| 100 | 100 | DRLearner_PooledNoSite | -0.078 ± 0.050 | 0.041 ± 0.029 | -0.011 ± 0.050 |
| 100 | 100 | DRLearner_PooledNoSite | -0.077 ± 0.062 | 0.048 ± 0.039 | -0.010 ± 0.062 |
| 100 | 100 | DRLearner_PooledNoSite | -0.077 ± 0.031 | 0.025 ± 0.021 | -0.010 ± 0.031 |
| 100 | 100 | DRLearner_PooledNoSite | -0.076 ± 0.032 | 0.026 ± 0.019 | -0.009 ± 0.032 |
| 100 | 100 | DRLearner_PooledWithSite | -0.078 ± 0.049 | 0.040 ± 0.029 | -0.011 ± 0.049 |
| 100 | 100 | DRLearner_PooledWithSite | -0.079 ± 0.062 | 0.048 ± 0.040 | -0.012 ± 0.062 |
| 100 | 100 | DRLearner_PooledWithSite | -0.078 ± 0.032 | 0.025 ± 0.021 | -0.011 ± 0.032 |
| 100 | 100 | DRLearner_PooledWithSite | -0.077 ± 0.032 | 0.026 ± 0.020 | -0.010 ± 0.032 |
| 100 | 100 | EntropyBalancing | 0.047 ± 0.792 | 0.593 ± 0.521 | 0.114 ± 0.792 |
| 100 | 100 | EntropyBalancing | -0.052 ± 0.600 | 0.464 ± 0.365 | 0.015 ± 0.600 |
| 100 | 100 | EntropyBalancing | -0.124 ± 0.458 | 0.307 ± 0.339 | -0.057 ± 0.458 |
| 100 | 100 | EntropyBalancing | -0.053 ± 0.083 | 0.058 ± 0.059 | 0.014 ± 0.083 |
| 100 | 100 | IPWTransport | -0.030 ± 0.126 | 0.109 ± 0.070 | 0.037 ± 0.126 |
| 100 | 100 | IPWTransport | -0.078 ± 0.128 | 0.105 ± 0.070 | -0.011 ± 0.128 |
| 100 | 100 | IPWTransport | -0.100 ± 0.180 | 0.143 ± 0.110 | -0.033 ± 0.180 |
| 100 | 100 | IPWTransport | -0.045 ± 0.105 | 0.065 ± 0.084 | 0.022 ± 0.105 |
| 100 | 100 | OutcomeModelTransport | -0.085 ± 0.070 | 0.057 ± 0.043 | -0.018 ± 0.070 |
| 100 | 100 | OutcomeModelTransport | -0.074 ± 0.126 | 0.099 ± 0.073 | -0.007 ± 0.126 |
| 100 | 100 | OutcomeModelTransport | -0.079 ± 0.050 | 0.039 ± 0.032 | -0.012 ± 0.050 |
| 100 | 100 | OutcomeModelTransport | -0.076 ± 0.034 | 0.028 ± 0.021 | -0.009 ± 0.034 |
| 100 | 100 | ProposedA_FullyDirect | -0.055 ± 0.081 | 0.063 ± 0.051 | 0.012 ± 0.081 |
| 100 | 100 | ProposedA_FullyDirect | -0.046 ± 0.113 | 0.087 ± 0.073 | 0.021 ± 0.113 |
| 100 | 100 | ProposedA_FullyDirect | -0.072 ± 0.083 | 0.060 ± 0.056 | -0.005 ± 0.083 |
| 100 | 100 | ProposedA_FullyDirect | -0.080 ± 0.062 | 0.051 ± 0.036 | -0.013 ± 0.062 |
| 100 | 100 | ProposedB_LinearStepB | -0.080 ± 0.065 | 0.053 ± 0.037 | -0.013 ± 0.065 |
| 100 | 100 | ProposedB_LinearStepB | -0.066 ± 0.114 | 0.089 ± 0.068 | 0.001 ± 0.114 |
| 100 | 100 | ProposedB_LinearStepB | -0.068 ± 0.082 | 0.064 ± 0.048 | -0.001 ± 0.082 |
| 100 | 100 | ProposedB_LinearStepB | -0.083 ± 0.065 | 0.053 ± 0.040 | -0.016 ± 0.065 |
| 100 | 100 | ProposedB_SourceDR | -0.065 ± 0.027 | 0.020 ± 0.018 | 0.002 ± 0.027 |
| 100 | 100 | ProposedB_SourceDR | -0.065 ± 0.038 | 0.028 ± 0.026 | 0.002 ± 0.038 |
| 100 | 100 | ProposedB_SourceDR | -0.068 ± 0.033 | 0.024 ± 0.021 | -0.001 ± 0.033 |
| 100 | 100 | ProposedB_SourceDR | -0.074 ± 0.024 | 0.019 ± 0.015 | -0.007 ± 0.024 |
| 100 | 100 | ProxyOnly | -0.195 ± 0.806 | 0.609 ± 0.525 | -0.128 ± 0.806 |
| 100 | 100 | ProxyOnly | 0.049 ± 1.197 | 0.934 ± 0.728 | 0.116 ± 1.197 |
| 100 | 100 | ProxyOnly | -0.111 ± 0.516 | 0.401 ± 0.315 | -0.044 ± 0.516 |
| 100 | 100 | ProxyOnly | -0.089 ± 0.173 | 0.143 ± 0.095 | -0.022 ± 0.173 |
| 100 | 100 | TargetOnlyDR | -0.100 ± 0.081 | 0.066 ± 0.055 | -0.033 ± 0.081 |
| 100 | 100 | TargetOnlyDR | -0.047 ± 0.123 | 0.099 ± 0.073 | 0.020 ± 0.123 |
| 100 | 100 | TargetOnlyDR | -0.056 ± 0.079 | 0.063 ± 0.046 | 0.011 ± 0.079 |
| 100 | 100 | TargetOnlyDR | -0.083 ± 0.074 | 0.062 ± 0.041 | -0.016 ± 0.074 |
| 200 | 200 | AnchorOnly | -0.076 ± 0.089 | 0.064 ± 0.061 | -0.009 ± 0.089 |
| 200 | 200 | AnchorOnly | -0.079 ± 0.066 | 0.052 ± 0.041 | -0.012 ± 0.066 |
| 200 | 200 | AnchorOnly | -0.067 ± 0.068 | 0.053 ± 0.041 | -0.000 ± 0.068 |
| 200 | 200 | AnchorOnly | -0.056 ± 0.052 | 0.043 ± 0.030 | 0.011 ± 0.052 |
| 200 | 200 | AnchorPlugin | -0.056 ± 0.614 | 0.452 ± 0.403 | 0.011 ± 0.614 |
| 200 | 200 | AnchorPlugin | -0.088 ± 0.060 | 0.052 ± 0.035 | -0.021 ± 0.060 |
| 200 | 200 | AnchorPlugin | 0.045 ± 0.428 | 0.334 ± 0.281 | 0.112 ± 0.428 |
| 200 | 200 | AnchorPlugin | -0.154 ± 0.201 | 0.179 ± 0.122 | -0.087 ± 0.201 |
| 200 | 200 | DRLearner_PooledNoSite | -0.079 ± 0.050 | 0.042 ± 0.029 | -0.012 ± 0.050 |
| 200 | 200 | DRLearner_PooledNoSite | -0.063 ± 0.039 | 0.031 ± 0.023 | 0.004 ± 0.039 |
| 200 | 200 | DRLearner_PooledNoSite | -0.079 ± 0.042 | 0.035 ± 0.025 | -0.012 ± 0.042 |
| 200 | 200 | DRLearner_PooledNoSite | -0.066 ± 0.039 | 0.031 ± 0.024 | 0.001 ± 0.039 |
| 200 | 200 | DRLearner_PooledWithSite | -0.079 ± 0.050 | 0.042 ± 0.028 | -0.012 ± 0.050 |
| 200 | 200 | DRLearner_PooledWithSite | -0.063 ± 0.039 | 0.031 ± 0.023 | 0.004 ± 0.039 |
| 200 | 200 | DRLearner_PooledWithSite | -0.078 ± 0.042 | 0.034 ± 0.026 | -0.011 ± 0.042 |
| 200 | 200 | DRLearner_PooledWithSite | -0.066 ± 0.039 | 0.030 ± 0.024 | 0.001 ± 0.039 |
| 200 | 200 | EntropyBalancing | -0.232 ± 0.554 | 0.457 ± 0.340 | -0.165 ± 0.554 |
| 200 | 200 | EntropyBalancing | -0.047 ± 0.115 | 0.095 ± 0.065 | 0.020 ± 0.115 |
| 200 | 200 | EntropyBalancing | -0.094 ± 1.193 | 0.837 ± 0.829 | -0.027 ± 1.193 |
| 200 | 200 | EntropyBalancing | -0.115 ± 0.399 | 0.286 ± 0.275 | -0.048 ± 0.399 |
| 200 | 200 | IPWTransport | -0.072 ± 0.123 | 0.096 ± 0.074 | -0.005 ± 0.123 |
| 200 | 200 | IPWTransport | -0.039 ± 0.112 | 0.093 ± 0.067 | 0.028 ± 0.112 |
| 200 | 200 | IPWTransport | -0.028 ± 0.152 | 0.122 ± 0.096 | 0.039 ± 0.152 |
| 200 | 200 | IPWTransport | -0.085 ± 0.210 | 0.158 ± 0.135 | -0.018 ± 0.210 |
| 200 | 200 | OutcomeModelTransport | -0.069 ± 0.126 | 0.100 ± 0.074 | -0.002 ± 0.126 |
| 200 | 200 | OutcomeModelTransport | -0.055 ± 0.037 | 0.032 ± 0.021 | 0.012 ± 0.037 |
| 200 | 200 | OutcomeModelTransport | -0.075 ± 0.063 | 0.051 ± 0.037 | -0.008 ± 0.063 |
| 200 | 200 | OutcomeModelTransport | -0.078 ± 0.064 | 0.052 ± 0.036 | -0.011 ± 0.064 |
| 200 | 200 | ProposedA_FullyDirect | -0.082 ± 0.063 | 0.049 ± 0.042 | -0.015 ± 0.063 |
| 200 | 200 | ProposedA_FullyDirect | -0.082 ± 0.064 | 0.053 ± 0.037 | -0.015 ± 0.064 |
| 200 | 200 | ProposedA_FullyDirect | -0.072 ± 0.056 | 0.042 ± 0.037 | -0.005 ± 0.056 |
| 200 | 200 | ProposedA_FullyDirect | -0.055 ± 0.055 | 0.043 ± 0.035 | 0.012 ± 0.055 |
| 200 | 200 | ProposedB_LinearStepB | -0.080 ± 0.068 | 0.052 ± 0.044 | -0.013 ± 0.068 |
| 200 | 200 | ProposedB_LinearStepB | -0.079 ± 0.066 | 0.052 ± 0.041 | -0.012 ± 0.066 |
| 200 | 200 | ProposedB_LinearStepB | -0.066 ± 0.061 | 0.047 ± 0.037 | 0.001 ± 0.061 |
| 200 | 200 | ProposedB_LinearStepB | -0.057 ± 0.052 | 0.040 ± 0.033 | 0.010 ± 0.052 |
| 200 | 200 | ProposedB_SourceDR | -0.074 ± 0.029 | 0.021 ± 0.021 | -0.007 ± 0.029 |
| 200 | 200 | ProposedB_SourceDR | -0.056 ± 0.030 | 0.026 ± 0.019 | 0.011 ± 0.030 |
| 200 | 200 | ProposedB_SourceDR | -0.068 ± 0.026 | 0.021 ± 0.015 | -0.001 ± 0.026 |
| 200 | 200 | ProposedB_SourceDR | -0.071 ± 0.032 | 0.025 ± 0.021 | -0.004 ± 0.032 |
| 200 | 200 | ProxyOnly | -0.030 ± 1.247 | 0.912 ± 0.824 | 0.037 ± 1.247 |
| 200 | 200 | ProxyOnly | -0.129 ± 0.124 | 0.111 ± 0.081 | -0.062 ± 0.124 |
| 200 | 200 | ProxyOnly | 0.181 ± 0.804 | 0.649 ± 0.517 | 0.248 ± 0.804 |
| 200 | 200 | ProxyOnly | -0.234 ± 0.399 | 0.357 ± 0.233 | -0.167 ± 0.399 |
| 200 | 200 | TargetOnlyDR | -0.064 ± 0.112 | 0.078 ± 0.078 | 0.003 ± 0.112 |
| 200 | 200 | TargetOnlyDR | -0.075 ± 0.069 | 0.055 ± 0.040 | -0.008 ± 0.069 |
| 200 | 200 | TargetOnlyDR | -0.070 ± 0.074 | 0.059 ± 0.043 | -0.003 ± 0.074 |
| 200 | 200 | TargetOnlyDR | -0.058 ± 0.064 | 0.053 ± 0.035 | 0.009 ± 0.064 |
| 500 | 500 | AnchorOnly | -0.058 ± 0.035 | 0.029 ± 0.021 | 0.009 ± 0.035 |
| 500 | 500 | AnchorOnly | -0.081 ± 0.030 | 0.024 ± 0.023 | -0.014 ± 0.030 |
| 500 | 500 | AnchorOnly | -0.077 ± 0.054 | 0.047 ± 0.027 | -0.010 ± 0.054 |
| 500 | 500 | AnchorOnly | -0.069 ± 0.038 | 0.028 ± 0.025 | -0.002 ± 0.038 |
| 500 | 500 | AnchorPlugin | -0.089 ± 0.102 | 0.084 ± 0.060 | -0.022 ± 0.102 |
| 500 | 500 | AnchorPlugin | -0.070 ± 0.161 | 0.133 ± 0.085 | -0.003 ± 0.161 |
| 500 | 500 | AnchorPlugin | -0.163 ± 0.941 | 0.778 ± 0.508 | -0.096 ± 0.941 |
| 500 | 500 | AnchorPlugin | 0.113 ± 0.305 | 0.291 ± 0.195 | 0.180 ± 0.305 |
| 500 | 500 | DRLearner_PooledNoSite | -0.060 ± 0.031 | 0.026 ± 0.017 | 0.007 ± 0.031 |
| 500 | 500 | DRLearner_PooledNoSite | -0.080 ± 0.022 | 0.020 ± 0.016 | -0.013 ± 0.022 |
| 500 | 500 | DRLearner_PooledNoSite | -0.066 ± 0.031 | 0.025 ± 0.017 | 0.001 ± 0.031 |
| 500 | 500 | DRLearner_PooledNoSite | -0.065 ± 0.027 | 0.022 ± 0.015 | 0.002 ± 0.027 |
| 500 | 500 | DRLearner_PooledWithSite | -0.060 ± 0.031 | 0.026 ± 0.017 | 0.007 ± 0.031 |
| 500 | 500 | DRLearner_PooledWithSite | -0.079 ± 0.022 | 0.020 ± 0.015 | -0.012 ± 0.022 |
| 500 | 500 | DRLearner_PooledWithSite | -0.066 ± 0.031 | 0.025 ± 0.017 | 0.001 ± 0.031 |
| 500 | 500 | DRLearner_PooledWithSite | -0.065 ± 0.028 | 0.023 ± 0.015 | 0.002 ± 0.028 |
| 500 | 500 | EntropyBalancing | -0.082 ± 0.143 | 0.087 ± 0.113 | -0.015 ± 0.143 |
| 500 | 500 | EntropyBalancing | -0.108 ± 0.241 | 0.200 ± 0.133 | -0.041 ± 0.241 |
| 500 | 500 | EntropyBalancing | 0.149 ± 0.595 | 0.480 ± 0.401 | 0.216 ± 0.595 |
| 500 | 500 | EntropyBalancing | -0.095 ± 0.777 | 0.653 ± 0.393 | -0.028 ± 0.777 |
| 500 | 500 | IPWTransport | -0.072 ± 0.130 | 0.083 ± 0.098 | -0.005 ± 0.130 |
| 500 | 500 | IPWTransport | -0.094 ± 0.161 | 0.138 ± 0.083 | -0.027 ± 0.161 |
| 500 | 500 | IPWTransport | -0.031 ± 0.101 | 0.082 ± 0.067 | 0.036 ± 0.101 |
| 500 | 500 | IPWTransport | -0.097 ± 0.163 | 0.139 ± 0.085 | -0.030 ± 0.163 |
| 500 | 500 | OutcomeModelTransport | -0.063 ± 0.040 | 0.032 ± 0.023 | 0.004 ± 0.040 |
| 500 | 500 | OutcomeModelTransport | -0.080 ± 0.039 | 0.032 ± 0.024 | -0.013 ± 0.039 |
| 500 | 500 | OutcomeModelTransport | -0.049 ± 0.093 | 0.078 ± 0.051 | 0.018 ± 0.093 |
| 500 | 500 | OutcomeModelTransport | -0.069 ± 0.064 | 0.046 ± 0.043 | -0.002 ± 0.064 |
| 500 | 500 | ProposedA_FullyDirect | -0.058 ± 0.038 | 0.032 ± 0.021 | 0.009 ± 0.038 |
| 500 | 500 | ProposedA_FullyDirect | -0.080 ± 0.028 | 0.023 ± 0.020 | -0.013 ± 0.028 |
| 500 | 500 | ProposedA_FullyDirect | -0.070 ± 0.036 | 0.029 ± 0.020 | -0.003 ± 0.036 |
| 500 | 500 | ProposedA_FullyDirect | -0.067 ± 0.036 | 0.028 ± 0.023 | 0.000 ± 0.036 |
| 500 | 500 | ProposedB_LinearStepB | -0.058 ± 0.035 | 0.029 ± 0.020 | 0.009 ± 0.035 |
| 500 | 500 | ProposedB_LinearStepB | -0.082 ± 0.028 | 0.024 ± 0.021 | -0.015 ± 0.028 |
| 500 | 500 | ProposedB_LinearStepB | -0.069 ± 0.038 | 0.031 ± 0.022 | -0.002 ± 0.038 |
| 500 | 500 | ProposedB_LinearStepB | -0.066 ± 0.035 | 0.027 ± 0.022 | 0.001 ± 0.035 |
| 500 | 500 | ProposedB_SourceDR | -0.062 ± 0.030 | 0.022 ± 0.020 | 0.005 ± 0.030 |
| 500 | 500 | ProposedB_SourceDR | -0.066 ± 0.025 | 0.018 ± 0.017 | 0.001 ± 0.025 |
| 500 | 500 | ProposedB_SourceDR | -0.060 ± 0.036 | 0.026 ± 0.025 | 0.007 ± 0.036 |
| 500 | 500 | ProposedB_SourceDR | -0.071 ± 0.028 | 0.019 ± 0.021 | -0.004 ± 0.028 |
| 500 | 500 | ProxyOnly | -0.114 ± 0.187 | 0.154 ± 0.111 | -0.047 ± 0.187 |
| 500 | 500 | ProxyOnly | -0.065 ± 0.343 | 0.284 ± 0.180 | 0.002 ± 0.343 |
| 500 | 500 | ProxyOnly | -0.288 ± 1.864 | 1.564 ± 0.976 | -0.221 ± 1.864 |
| 500 | 500 | ProxyOnly | 0.315 ± 0.606 | 0.581 ± 0.407 | 0.382 ± 0.606 |
| 500 | 500 | TargetOnlyDR | -0.057 ± 0.037 | 0.030 ± 0.022 | 0.010 ± 0.037 |
| 500 | 500 | TargetOnlyDR | -0.084 ± 0.032 | 0.023 ± 0.028 | -0.017 ± 0.032 |
| 500 | 500 | TargetOnlyDR | -0.097 ± 0.074 | 0.064 ± 0.047 | -0.030 ± 0.074 |
| 500 | 500 | TargetOnlyDR | -0.072 ± 0.042 | 0.031 ± 0.028 | -0.005 ± 0.042 |

### Policy / Decision Metrics

| m0 | m1 | Method | Policy Value (↑) | Regret (↓) | Value Top20 (↑) | Regret Top20 (↓) |
|---|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 0.048 ± 0.169 | 0.030 ± 0.012 | 0.065 ± 0.169 | 0.000 ± 0.000 |
| 50 | 50 | AnchorOnly | 0.159 ± 0.653 | 0.024 ± 0.008 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | AnchorOnly | -0.081 ± 0.375 | 0.027 ± 0.009 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | AnchorOnly | -0.189 ± 0.580 | 0.033 ± 0.011 | -0.169 ± 0.579 | 0.000 ± 0.000 |
| 50 | 50 | AnchorPlugin | 0.056 ± 0.174 | 0.022 ± 0.014 | 0.065 ± 0.169 | -0.000 ± 0.000 |
| 50 | 50 | AnchorPlugin | 0.152 ± 0.671 | 0.031 ± 0.021 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | AnchorPlugin | -0.084 ± 0.392 | 0.030 ± 0.021 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | AnchorPlugin | -0.195 ± 0.599 | 0.039 ± 0.024 | -0.169 ± 0.579 | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledNoSite | 0.071 ± 0.171 | 0.007 ± 0.009 | 0.065 ± 0.169 | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledNoSite | 0.157 ± 0.656 | 0.026 ± 0.014 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledNoSite | -0.063 ± 0.379 | 0.009 ± 0.011 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledNoSite | -0.176 ± 0.579 | 0.021 ± 0.013 | -0.169 ± 0.579 | -0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledWithSite | 0.071 ± 0.171 | 0.007 ± 0.009 | 0.065 ± 0.169 | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledWithSite | 0.157 ± 0.656 | 0.026 ± 0.014 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledWithSite | -0.063 ± 0.379 | 0.009 ± 0.010 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | DRLearner_PooledWithSite | -0.176 ± 0.579 | 0.021 ± 0.013 | -0.169 ± 0.579 | 0.000 ± 0.000 |
| 50 | 50 | EntropyBalancing | 0.055 ± 0.169 | 0.024 ± 0.015 | 0.065 ± 0.169 | 0.000 ± 0.000 |
| 50 | 50 | EntropyBalancing | 0.142 ± 0.658 | 0.041 ± 0.012 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | EntropyBalancing | -0.081 ± 0.374 | 0.027 ± 0.014 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | EntropyBalancing | -0.189 ± 0.583 | 0.034 ± 0.018 | -0.169 ± 0.579 | 0.000 ± 0.000 |
| 50 | 50 | IPWTransport | 0.058 ± 0.169 | 0.020 ± 0.018 | 0.065 ± 0.169 | 0.000 ± 0.000 |
| 50 | 50 | IPWTransport | 0.154 ± 0.656 | 0.029 ± 0.014 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | IPWTransport | -0.078 ± 0.372 | 0.024 ± 0.018 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | IPWTransport | -0.183 ± 0.581 | 0.027 ± 0.020 | -0.169 ± 0.579 | -0.000 ± 0.000 |
| 50 | 50 | OutcomeModelTransport | 0.070 ± 0.170 | 0.009 ± 0.011 | 0.065 ± 0.169 | -0.000 ± 0.000 |
| 50 | 50 | OutcomeModelTransport | 0.153 ± 0.656 | 0.029 ± 0.014 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | OutcomeModelTransport | -0.064 ± 0.379 | 0.010 ± 0.012 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | OutcomeModelTransport | -0.177 ± 0.578 | 0.021 ± 0.018 | -0.169 ± 0.579 | 0.000 ± 0.000 |
| 50 | 50 | ProposedA_FullyDirect | 0.049 ± 0.169 | 0.029 ± 0.011 | 0.065 ± 0.169 | 0.000 ± 0.000 |
| 50 | 50 | ProposedA_FullyDirect | 0.160 ± 0.652 | 0.023 ± 0.011 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | ProposedA_FullyDirect | -0.082 ± 0.376 | 0.027 ± 0.009 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | ProposedA_FullyDirect | -0.188 ± 0.580 | 0.033 ± 0.012 | -0.169 ± 0.579 | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_LinearStepB | 0.048 ± 0.169 | 0.030 ± 0.012 | 0.065 ± 0.169 | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_LinearStepB | 0.158 ± 0.653 | 0.025 ± 0.009 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_LinearStepB | -0.081 ± 0.375 | 0.027 ± 0.010 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_LinearStepB | -0.188 ± 0.580 | 0.033 ± 0.012 | -0.169 ± 0.579 | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_SourceDR | 0.068 ± 0.167 | 0.010 ± 0.013 | 0.065 ± 0.169 | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_SourceDR | 0.169 ± 0.652 | 0.013 ± 0.010 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_SourceDR | -0.060 ± 0.375 | 0.005 ± 0.006 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | ProposedB_SourceDR | -0.164 ± 0.579 | 0.008 ± 0.007 | -0.169 ± 0.579 | 0.000 ± 0.000 |
| 50 | 50 | ProxyOnly | 0.051 ± 0.175 | 0.027 ± 0.015 | 0.065 ± 0.169 | 0.000 ± 0.000 |
| 50 | 50 | ProxyOnly | 0.151 ± 0.676 | 0.031 ± 0.027 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | ProxyOnly | -0.087 ± 0.393 | 0.033 ± 0.022 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | ProxyOnly | -0.200 ± 0.602 | 0.045 ± 0.027 | -0.169 ± 0.579 | 0.000 ± 0.000 |
| 50 | 50 | TargetOnlyDR | 0.047 ± 0.169 | 0.031 ± 0.011 | 0.065 ± 0.169 | 0.000 ± 0.000 |
| 50 | 50 | TargetOnlyDR | 0.160 ± 0.652 | 0.022 ± 0.009 | 0.169 ± 0.653 | 0.000 ± 0.000 |
| 50 | 50 | TargetOnlyDR | -0.083 ± 0.376 | 0.028 ± 0.009 | -0.068 ± 0.374 | 0.000 ± 0.000 |
| 50 | 50 | TargetOnlyDR | -0.191 ± 0.581 | 0.035 ± 0.013 | -0.169 ± 0.579 | -0.000 ± 0.000 |
| 100 | 100 | AnchorOnly | 0.175 ± 0.514 | 0.025 ± 0.007 | 0.187 ± 0.515 | 0.000 ± 0.000 |
| 100 | 100 | AnchorOnly | -0.065 ± 0.691 | 0.029 ± 0.010 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | AnchorOnly | -0.047 ± 0.422 | 0.026 ± 0.008 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | AnchorOnly | -0.023 ± 0.187 | 0.025 ± 0.008 | -0.012 ± 0.190 | -0.000 ± 0.000 |
| 100 | 100 | AnchorPlugin | 0.172 ± 0.532 | 0.028 ± 0.019 | 0.187 ± 0.515 | 0.000 ± 0.000 |
| 100 | 100 | AnchorPlugin | -0.070 ± 0.711 | 0.034 ± 0.021 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | AnchorPlugin | -0.048 ± 0.436 | 0.027 ± 0.018 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | AnchorPlugin | -0.020 ± 0.194 | 0.022 ± 0.011 | -0.012 ± 0.190 | -0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledNoSite | 0.185 ± 0.514 | 0.015 ± 0.011 | 0.187 ± 0.515 | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledNoSite | -0.057 ± 0.694 | 0.020 ± 0.010 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledNoSite | -0.029 ± 0.421 | 0.008 ± 0.006 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledNoSite | -0.002 ± 0.189 | 0.004 ± 0.006 | -0.012 ± 0.190 | -0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledWithSite | 0.185 ± 0.514 | 0.015 ± 0.010 | 0.187 ± 0.515 | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledWithSite | -0.056 ± 0.694 | 0.020 ± 0.010 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledWithSite | -0.029 ± 0.421 | 0.008 ± 0.006 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | DRLearner_PooledWithSite | -0.002 ± 0.189 | 0.004 ± 0.005 | -0.012 ± 0.190 | -0.000 ± 0.000 |
| 100 | 100 | EntropyBalancing | 0.166 ± 0.517 | 0.034 ± 0.017 | 0.187 ± 0.515 | 0.000 ± 0.000 |
| 100 | 100 | EntropyBalancing | -0.068 ± 0.694 | 0.032 ± 0.014 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | EntropyBalancing | -0.049 ± 0.420 | 0.028 ± 0.015 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | EntropyBalancing | -0.021 ± 0.188 | 0.023 ± 0.012 | -0.012 ± 0.190 | -0.000 ± 0.000 |
| 100 | 100 | IPWTransport | 0.172 ± 0.520 | 0.028 ± 0.021 | 0.187 ± 0.515 | 0.000 ± 0.000 |
| 100 | 100 | IPWTransport | -0.059 ± 0.694 | 0.023 ± 0.018 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | IPWTransport | -0.043 ± 0.421 | 0.022 ± 0.017 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | IPWTransport | -0.021 ± 0.188 | 0.022 ± 0.014 | -0.012 ± 0.190 | -0.000 ± 0.000 |
| 100 | 100 | OutcomeModelTransport | 0.185 ± 0.514 | 0.015 ± 0.013 | 0.187 ± 0.515 | 0.000 ± 0.000 |
| 100 | 100 | OutcomeModelTransport | -0.060 ± 0.695 | 0.023 ± 0.017 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | OutcomeModelTransport | -0.030 ± 0.419 | 0.010 ± 0.009 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | OutcomeModelTransport | -0.002 ± 0.189 | 0.004 ± 0.006 | -0.012 ± 0.190 | 0.000 ± 0.000 |
| 100 | 100 | ProposedA_FullyDirect | 0.174 ± 0.514 | 0.027 ± 0.009 | 0.187 ± 0.515 | -0.000 ± 0.000 |
| 100 | 100 | ProposedA_FullyDirect | -0.066 ± 0.694 | 0.029 ± 0.011 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | ProposedA_FullyDirect | -0.046 ± 0.423 | 0.025 ± 0.009 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | ProposedA_FullyDirect | -0.023 ± 0.187 | 0.024 ± 0.008 | -0.012 ± 0.190 | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_LinearStepB | 0.175 ± 0.514 | 0.025 ± 0.007 | 0.187 ± 0.515 | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_LinearStepB | -0.064 ± 0.691 | 0.027 ± 0.011 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_LinearStepB | -0.047 ± 0.422 | 0.026 ± 0.008 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_LinearStepB | -0.023 ± 0.187 | 0.024 ± 0.009 | -0.012 ± 0.190 | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_SourceDR | 0.192 ± 0.517 | 0.008 ± 0.007 | 0.187 ± 0.515 | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_SourceDR | -0.048 ± 0.694 | 0.012 ± 0.008 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_SourceDR | -0.028 ± 0.419 | 0.007 ± 0.005 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | ProposedB_SourceDR | -0.004 ± 0.191 | 0.005 ± 0.004 | -0.012 ± 0.190 | -0.000 ± 0.000 |
| 100 | 100 | ProxyOnly | 0.172 ± 0.536 | 0.028 ± 0.024 | 0.187 ± 0.515 | 0.000 ± 0.000 |
| 100 | 100 | ProxyOnly | -0.072 ± 0.715 | 0.036 ± 0.028 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | ProxyOnly | -0.050 ± 0.439 | 0.029 ± 0.023 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | ProxyOnly | -0.026 ± 0.195 | 0.028 ± 0.013 | -0.012 ± 0.190 | 0.000 ± 0.000 |
| 100 | 100 | TargetOnlyDR | 0.176 ± 0.515 | 0.024 ± 0.007 | 0.187 ± 0.515 | 0.000 ± 0.000 |
| 100 | 100 | TargetOnlyDR | -0.066 ± 0.690 | 0.030 ± 0.009 | -0.050 ± 0.691 | 0.000 ± 0.000 |
| 100 | 100 | TargetOnlyDR | -0.048 ± 0.423 | 0.027 ± 0.007 | -0.034 ± 0.420 | 0.000 ± 0.000 |
| 100 | 100 | TargetOnlyDR | -0.023 ± 0.186 | 0.025 ± 0.010 | -0.012 ± 0.190 | -0.000 ± 0.000 |
| 200 | 200 | AnchorOnly | -0.054 ± 0.694 | 0.024 ± 0.009 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | AnchorOnly | 0.024 ± 0.207 | 0.022 ± 0.009 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | AnchorOnly | -0.179 ± 0.642 | 0.025 ± 0.009 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | AnchorOnly | 0.185 ± 0.291 | 0.024 ± 0.008 | 0.196 ± 0.287 | 0.000 ± 0.000 |
| 200 | 200 | AnchorPlugin | -0.061 ± 0.706 | 0.031 ± 0.015 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | AnchorPlugin | 0.026 ± 0.212 | 0.020 ± 0.009 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | AnchorPlugin | -0.190 ± 0.656 | 0.036 ± 0.017 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | AnchorPlugin | 0.189 ± 0.299 | 0.021 ± 0.016 | 0.196 ± 0.287 | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledNoSite | -0.049 ± 0.691 | 0.020 ± 0.008 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledNoSite | 0.038 ± 0.211 | 0.008 ± 0.012 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledNoSite | -0.169 ± 0.640 | 0.015 ± 0.010 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledNoSite | 0.198 ± 0.284 | 0.011 ± 0.010 | 0.196 ± 0.287 | -0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledWithSite | -0.049 ± 0.691 | 0.020 ± 0.008 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledWithSite | 0.038 ± 0.211 | 0.008 ± 0.012 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledWithSite | -0.169 ± 0.640 | 0.015 ± 0.009 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | DRLearner_PooledWithSite | 0.198 ± 0.284 | 0.011 ± 0.010 | 0.196 ± 0.287 | 0.000 ± 0.000 |
| 200 | 200 | EntropyBalancing | -0.058 ± 0.686 | 0.028 ± 0.013 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | EntropyBalancing | 0.020 ± 0.208 | 0.026 ± 0.015 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | EntropyBalancing | -0.185 ± 0.651 | 0.031 ± 0.020 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | EntropyBalancing | 0.185 ± 0.289 | 0.025 ± 0.016 | 0.196 ± 0.287 | 0.000 ± 0.000 |
| 200 | 200 | IPWTransport | -0.053 ± 0.691 | 0.023 ± 0.018 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | IPWTransport | 0.019 ± 0.209 | 0.027 ± 0.016 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | IPWTransport | -0.184 ± 0.643 | 0.030 ± 0.021 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | IPWTransport | 0.185 ± 0.287 | 0.024 ± 0.016 | 0.196 ± 0.287 | 0.000 ± 0.000 |
| 200 | 200 | OutcomeModelTransport | -0.053 ± 0.691 | 0.023 ± 0.019 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | OutcomeModelTransport | 0.036 ± 0.210 | 0.009 ± 0.011 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | OutcomeModelTransport | -0.171 ± 0.641 | 0.017 ± 0.013 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | OutcomeModelTransport | 0.197 ± 0.284 | 0.013 ± 0.015 | 0.196 ± 0.287 | 0.000 ± 0.000 |
| 200 | 200 | ProposedA_FullyDirect | -0.050 ± 0.693 | 0.020 ± 0.009 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | ProposedA_FullyDirect | 0.024 ± 0.208 | 0.022 ± 0.010 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | ProposedA_FullyDirect | -0.176 ± 0.640 | 0.022 ± 0.008 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | ProposedA_FullyDirect | 0.185 ± 0.291 | 0.024 ± 0.009 | 0.196 ± 0.287 | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_LinearStepB | -0.051 ± 0.692 | 0.022 ± 0.009 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_LinearStepB | 0.024 ± 0.207 | 0.022 ± 0.009 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_LinearStepB | -0.177 ± 0.642 | 0.023 ± 0.009 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_LinearStepB | 0.185 ± 0.290 | 0.024 ± 0.008 | 0.196 ± 0.287 | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_SourceDR | -0.038 ± 0.690 | 0.008 ± 0.009 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_SourceDR | 0.035 ± 0.207 | 0.010 ± 0.009 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_SourceDR | -0.161 ± 0.639 | 0.007 ± 0.007 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | ProposedB_SourceDR | 0.202 ± 0.286 | 0.008 ± 0.007 | 0.196 ± 0.287 | 0.000 ± 0.000 |
| 200 | 200 | ProxyOnly | -0.060 ± 0.715 | 0.030 ± 0.029 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | ProxyOnly | 0.024 ± 0.213 | 0.022 ± 0.009 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | ProxyOnly | -0.195 ± 0.662 | 0.041 ± 0.026 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | ProxyOnly | 0.188 ± 0.305 | 0.021 ± 0.021 | 0.196 ± 0.287 | 0.000 ± 0.000 |
| 200 | 200 | TargetOnlyDR | -0.057 ± 0.693 | 0.027 ± 0.010 | -0.043 ± 0.691 | 0.000 ± 0.000 |
| 200 | 200 | TargetOnlyDR | 0.023 ± 0.208 | 0.022 ± 0.010 | 0.032 ± 0.208 | 0.000 ± 0.000 |
| 200 | 200 | TargetOnlyDR | -0.179 ± 0.640 | 0.025 ± 0.009 | -0.167 ± 0.641 | 0.000 ± 0.000 |
| 200 | 200 | TargetOnlyDR | 0.185 ± 0.290 | 0.025 ± 0.009 | 0.196 ± 0.287 | 0.000 ± 0.000 |
| 500 | 500 | AnchorOnly | 0.028 ± 0.292 | 0.019 ± 0.008 | 0.034 ± 0.291 | 0.000 ± 0.000 |
| 500 | 500 | AnchorOnly | 0.027 ± 0.280 | 0.015 ± 0.006 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | AnchorOnly | 0.052 ± 1.109 | 0.021 ± 0.008 | 0.060 ± 1.112 | 0.000 ± 0.000 |
| 500 | 500 | AnchorOnly | -0.170 ± 0.366 | 0.018 ± 0.007 | -0.165 ± 0.366 | 0.000 ± 0.000 |
| 500 | 500 | AnchorPlugin | 0.026 ± 0.301 | 0.022 ± 0.013 | 0.034 ± 0.291 | -0.000 ± 0.000 |
| 500 | 500 | AnchorPlugin | 0.015 ± 0.292 | 0.027 ± 0.014 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | AnchorPlugin | 0.043 ± 1.133 | 0.030 ± 0.022 | 0.060 ± 1.112 | -0.000 ± 0.000 |
| 500 | 500 | AnchorPlugin | -0.191 ± 0.378 | 0.039 ± 0.013 | -0.165 ± 0.366 | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledNoSite | 0.041 ± 0.293 | 0.007 ± 0.010 | 0.034 ± 0.291 | -0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledNoSite | 0.036 ± 0.278 | 0.006 ± 0.004 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledNoSite | 0.052 ± 1.109 | 0.021 ± 0.006 | 0.060 ± 1.112 | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledNoSite | -0.168 ± 0.366 | 0.016 ± 0.006 | -0.165 ± 0.366 | -0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledWithSite | 0.041 ± 0.293 | 0.007 ± 0.010 | 0.034 ± 0.291 | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledWithSite | 0.036 ± 0.278 | 0.006 ± 0.004 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledWithSite | 0.052 ± 1.109 | 0.021 ± 0.006 | 0.060 ± 1.112 | 0.000 ± 0.000 |
| 500 | 500 | DRLearner_PooledWithSite | -0.168 ± 0.366 | 0.016 ± 0.006 | -0.165 ± 0.366 | -0.000 ± 0.000 |
| 500 | 500 | EntropyBalancing | 0.023 ± 0.291 | 0.024 ± 0.011 | 0.034 ± 0.291 | 0.000 ± 0.000 |
| 500 | 500 | EntropyBalancing | 0.014 ± 0.284 | 0.028 ± 0.014 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | EntropyBalancing | 0.037 ± 1.111 | 0.036 ± 0.014 | 0.060 ± 1.112 | 0.000 ± 0.000 |
| 500 | 500 | EntropyBalancing | -0.183 ± 0.368 | 0.031 ± 0.019 | -0.165 ± 0.366 | -0.000 ± 0.000 |
| 500 | 500 | IPWTransport | 0.022 ± 0.291 | 0.025 ± 0.011 | 0.034 ± 0.291 | 0.000 ± 0.000 |
| 500 | 500 | IPWTransport | 0.016 ± 0.283 | 0.026 ± 0.013 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | IPWTransport | 0.044 ± 1.114 | 0.029 ± 0.016 | 0.060 ± 1.112 | -0.000 ± 0.000 |
| 500 | 500 | IPWTransport | -0.174 ± 0.366 | 0.023 ± 0.020 | -0.165 ± 0.366 | 0.000 ± 0.000 |
| 500 | 500 | OutcomeModelTransport | 0.039 ± 0.292 | 0.009 ± 0.013 | 0.034 ± 0.291 | 0.000 ± 0.000 |
| 500 | 500 | OutcomeModelTransport | 0.033 ± 0.278 | 0.008 ± 0.008 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | OutcomeModelTransport | 0.047 ± 1.113 | 0.026 ± 0.015 | 0.060 ± 1.112 | 0.000 ± 0.000 |
| 500 | 500 | OutcomeModelTransport | -0.170 ± 0.365 | 0.018 ± 0.013 | -0.165 ± 0.366 | -0.000 ± 0.000 |
| 500 | 500 | ProposedA_FullyDirect | 0.028 ± 0.291 | 0.019 ± 0.009 | 0.034 ± 0.291 | 0.000 ± 0.000 |
| 500 | 500 | ProposedA_FullyDirect | 0.027 ± 0.280 | 0.015 ± 0.007 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | ProposedA_FullyDirect | 0.056 ± 1.108 | 0.017 ± 0.009 | 0.060 ± 1.112 | -0.000 ± 0.000 |
| 500 | 500 | ProposedA_FullyDirect | -0.168 ± 0.365 | 0.017 ± 0.007 | -0.165 ± 0.366 | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_LinearStepB | 0.028 ± 0.292 | 0.020 ± 0.008 | 0.034 ± 0.291 | -0.000 ± 0.000 |
| 500 | 500 | ProposedB_LinearStepB | 0.027 ± 0.280 | 0.014 ± 0.007 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_LinearStepB | 0.055 ± 1.108 | 0.018 ± 0.009 | 0.060 ± 1.112 | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_LinearStepB | -0.169 ± 0.365 | 0.017 ± 0.007 | -0.165 ± 0.366 | -0.000 ± 0.000 |
| 500 | 500 | ProposedB_SourceDR | 0.040 ± 0.289 | 0.008 ± 0.008 | 0.034 ± 0.291 | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_SourceDR | 0.033 ± 0.280 | 0.008 ± 0.006 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | ProposedB_SourceDR | 0.063 ± 1.106 | 0.010 ± 0.011 | 0.060 ± 1.112 | -0.000 ± 0.000 |
| 500 | 500 | ProposedB_SourceDR | -0.158 ± 0.366 | 0.006 ± 0.004 | -0.165 ± 0.366 | -0.000 ± 0.000 |
| 500 | 500 | ProxyOnly | 0.025 ± 0.306 | 0.023 ± 0.017 | 0.034 ± 0.291 | -0.000 ± 0.000 |
| 500 | 500 | ProxyOnly | 0.014 ± 0.299 | 0.027 ± 0.023 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | ProxyOnly | 0.045 ± 1.141 | 0.028 ± 0.032 | 0.060 ± 1.112 | 0.000 ± 0.000 |
| 500 | 500 | ProxyOnly | -0.198 ± 0.384 | 0.046 ± 0.022 | -0.165 ± 0.366 | 0.000 ± 0.000 |
| 500 | 500 | TargetOnlyDR | 0.028 ± 0.291 | 0.020 ± 0.008 | 0.034 ± 0.291 | 0.000 ± 0.000 |
| 500 | 500 | TargetOnlyDR | 0.027 ± 0.280 | 0.015 ± 0.006 | 0.028 ± 0.280 | 0.000 ± 0.000 |
| 500 | 500 | TargetOnlyDR | 0.053 ± 1.107 | 0.020 ± 0.009 | 0.060 ± 1.112 | -0.000 ± 0.000 |
| 500 | 500 | TargetOnlyDR | -0.171 ± 0.365 | 0.019 ± 0.008 | -0.165 ± 0.366 | -0.000 ± 0.000 |

### Calibration Metrics

| m0 | m1 | Method | Slope (→1) | Intercept (→0) | R² (↑) | ECE (↓) | MCE (↓) |
|---|---|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.256 ± 0.033 | 0.641 ± 0.119 |
| 50 | 50 | AnchorOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.370 ± 0.095 | 0.927 ± 0.212 |
| 50 | 50 | AnchorOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.260 ± 0.036 | 0.648 ± 0.114 |
| 50 | 50 | AnchorOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.299 ± 0.047 | 0.750 ± 0.149 |
| 50 | 50 | AnchorPlugin | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.172 ± 0.069 | 0.417 ± 0.156 |
| 50 | 50 | AnchorPlugin | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.591 ± 0.289 | 1.335 ± 0.534 |
| 50 | 50 | AnchorPlugin | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.249 ± 0.103 | 0.570 ± 0.208 |
| 50 | 50 | AnchorPlugin | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.477 ± 0.187 | 0.997 ± 0.296 |
| 50 | 50 | DRLearner_PooledNoSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.045 ± 0.015 | 0.104 ± 0.030 |
| 50 | 50 | DRLearner_PooledNoSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.130 ± 0.029 | 0.309 ± 0.061 |
| 50 | 50 | DRLearner_PooledNoSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.056 ± 0.014 | 0.132 ± 0.029 |
| 50 | 50 | DRLearner_PooledNoSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.088 ± 0.014 | 0.213 ± 0.035 |
| 50 | 50 | DRLearner_PooledWithSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.045 ± 0.014 | 0.104 ± 0.030 |
| 50 | 50 | DRLearner_PooledWithSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.129 ± 0.029 | 0.308 ± 0.061 |
| 50 | 50 | DRLearner_PooledWithSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.056 ± 0.015 | 0.132 ± 0.029 |
| 50 | 50 | DRLearner_PooledWithSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.088 ± 0.015 | 0.213 ± 0.035 |
| 50 | 50 | EntropyBalancing | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.212 ± 0.118 | 0.513 ± 0.278 |
| 50 | 50 | EntropyBalancing | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.944 ± 0.261 | 2.256 ± 0.566 |
| 50 | 50 | EntropyBalancing | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.402 ± 0.137 | 0.953 ± 0.290 |
| 50 | 50 | EntropyBalancing | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 1.009 ± 0.383 | 2.341 ± 0.694 |
| 50 | 50 | IPWTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.139 ± 0.076 | 0.318 ± 0.146 |
| 50 | 50 | IPWTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.133 ± 0.033 | 0.314 ± 0.069 |
| 50 | 50 | IPWTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.188 ± 0.084 | 0.425 ± 0.153 |
| 50 | 50 | IPWTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.120 ± 0.033 | 0.274 ± 0.059 |
| 50 | 50 | OutcomeModelTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.051 ± 0.024 | 0.115 ± 0.042 |
| 50 | 50 | OutcomeModelTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.134 ± 0.034 | 0.318 ± 0.068 |
| 50 | 50 | OutcomeModelTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.060 ± 0.021 | 0.138 ± 0.038 |
| 50 | 50 | OutcomeModelTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.104 ± 0.029 | 0.241 ± 0.052 |
| 50 | 50 | ProposedA_FullyDirect | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.267 ± 0.037 | 0.672 ± 0.118 |
| 50 | 50 | ProposedA_FullyDirect | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.359 ± 0.042 | 0.885 ± 0.098 |
| 50 | 50 | ProposedA_FullyDirect | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.252 ± 0.040 | 0.644 ± 0.131 |
| 50 | 50 | ProposedA_FullyDirect | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.291 ± 0.064 | 0.708 ± 0.146 |
| 50 | 50 | ProposedB_LinearStepB | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.256 ± 0.032 | 0.640 ± 0.109 |
| 50 | 50 | ProposedB_LinearStepB | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.348 ± 0.082 | 0.905 ± 0.214 |
| 50 | 50 | ProposedB_LinearStepB | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.257 ± 0.032 | 0.643 ± 0.102 |
| 50 | 50 | ProposedB_LinearStepB | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.286 ± 0.045 | 0.696 ± 0.112 |
| 50 | 50 | ProposedB_SourceDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.060 ± 0.028 | 0.168 ± 0.079 |
| 50 | 50 | ProposedB_SourceDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.070 ± 0.017 | 0.189 ± 0.053 |
| 50 | 50 | ProposedB_SourceDR | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.050 ± 0.013 | 0.142 ± 0.037 |
| 50 | 50 | ProposedB_SourceDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.056 ± 0.015 | 0.164 ± 0.054 |
| 50 | 50 | ProxyOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.347 ± 0.122 | 0.818 ± 0.250 |
| 50 | 50 | ProxyOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.922 ± 0.610 | 1.665 ± 0.734 |
| 50 | 50 | ProxyOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.474 ± 0.243 | 1.026 ± 0.353 |
| 50 | 50 | ProxyOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.888 ± 0.477 | 1.566 ± 0.584 |
| 50 | 50 | TargetOnlyDR | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.276 ± 0.050 | 0.684 ± 0.139 |
| 50 | 50 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.419 ± 0.099 | 1.066 ± 0.253 |
| 50 | 50 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.284 ± 0.042 | 0.712 ± 0.122 |
| 50 | 50 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.334 ± 0.059 | 0.834 ± 0.228 |
| 100 | 100 | AnchorOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.231 ± 0.043 | 0.575 ± 0.123 |
| 100 | 100 | AnchorOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.270 ± 0.047 | 0.657 ± 0.131 |
| 100 | 100 | AnchorOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.209 ± 0.037 | 0.539 ± 0.103 |
| 100 | 100 | AnchorOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.205 ± 0.025 | 0.499 ± 0.092 |
| 100 | 100 | AnchorPlugin | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.457 ± 0.153 | 1.033 ± 0.286 |
| 100 | 100 | AnchorPlugin | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.675 ± 0.283 | 1.496 ± 0.518 |
| 100 | 100 | AnchorPlugin | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.266 ± 0.112 | 0.614 ± 0.206 |
| 100 | 100 | AnchorPlugin | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.151 ± 0.031 | 0.368 ± 0.080 |
| 100 | 100 | DRLearner_PooledNoSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.082 ± 0.015 | 0.201 ± 0.033 |
| 100 | 100 | DRLearner_PooledNoSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.121 ± 0.013 | 0.294 ± 0.040 |
| 100 | 100 | DRLearner_PooledNoSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.052 ± 0.010 | 0.124 ± 0.021 |
| 100 | 100 | DRLearner_PooledNoSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.038 ± 0.015 | 0.089 ± 0.028 |
| 100 | 100 | DRLearner_PooledWithSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.082 ± 0.014 | 0.200 ± 0.032 |
| 100 | 100 | DRLearner_PooledWithSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.121 ± 0.013 | 0.294 ± 0.041 |
| 100 | 100 | DRLearner_PooledWithSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.052 ± 0.011 | 0.124 ± 0.022 |
| 100 | 100 | DRLearner_PooledWithSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.038 ± 0.015 | 0.089 ± 0.028 |
| 100 | 100 | EntropyBalancing | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.964 ± 0.341 | 2.218 ± 0.634 |
| 100 | 100 | EntropyBalancing | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.923 ± 0.205 | 2.232 ± 0.449 |
| 100 | 100 | EntropyBalancing | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.485 ± 0.294 | 1.143 ± 0.629 |
| 100 | 100 | EntropyBalancing | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.143 ± 0.072 | 0.349 ± 0.182 |
| 100 | 100 | IPWTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.138 ± 0.054 | 0.312 ± 0.105 |
| 100 | 100 | IPWTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.150 ± 0.045 | 0.351 ± 0.071 |
| 100 | 100 | IPWTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.213 ± 0.082 | 0.493 ± 0.157 |
| 100 | 100 | IPWTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.126 ± 0.078 | 0.303 ± 0.172 |
| 100 | 100 | OutcomeModelTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.093 ± 0.024 | 0.220 ± 0.049 |
| 100 | 100 | OutcomeModelTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.148 ± 0.045 | 0.345 ± 0.074 |
| 100 | 100 | OutcomeModelTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.060 ± 0.023 | 0.139 ± 0.034 |
| 100 | 100 | OutcomeModelTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.039 ± 0.016 | 0.091 ± 0.031 |
| 100 | 100 | ProposedA_FullyDirect | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.191 ± 0.025 | 0.488 ± 0.095 |
| 100 | 100 | ProposedA_FullyDirect | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.232 ± 0.043 | 0.547 ± 0.117 |
| 100 | 100 | ProposedA_FullyDirect | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.189 ± 0.029 | 0.481 ± 0.089 |
| 100 | 100 | ProposedA_FullyDirect | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.200 ± 0.024 | 0.503 ± 0.078 |
| 100 | 100 | ProposedB_LinearStepB | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.218 ± 0.040 | 0.545 ± 0.128 |
| 100 | 100 | ProposedB_LinearStepB | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.246 ± 0.049 | 0.600 ± 0.126 |
| 100 | 100 | ProposedB_LinearStepB | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.202 ± 0.035 | 0.523 ± 0.099 |
| 100 | 100 | ProposedB_LinearStepB | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.203 ± 0.023 | 0.499 ± 0.083 |
| 100 | 100 | ProposedB_SourceDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.047 ± 0.013 | 0.140 ± 0.075 |
| 100 | 100 | ProposedB_SourceDR | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.064 ± 0.019 | 0.181 ± 0.069 |
| 100 | 100 | ProposedB_SourceDR | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.048 ± 0.014 | 0.139 ± 0.048 |
| 100 | 100 | ProposedB_SourceDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.044 ± 0.009 | 0.119 ± 0.026 |
| 100 | 100 | ProxyOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.715 ± 0.438 | 1.318 ± 0.527 |
| 100 | 100 | ProxyOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.988 ± 0.676 | 1.671 ± 0.771 |
| 100 | 100 | ProxyOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.495 ± 0.240 | 1.047 ± 0.389 |
| 100 | 100 | ProxyOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.300 ± 0.058 | 0.751 ± 0.140 |
| 100 | 100 | TargetOnlyDR | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.247 ± 0.030 | 0.600 ± 0.088 |
| 100 | 100 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.300 ± 0.039 | 0.733 ± 0.103 |
| 100 | 100 | TargetOnlyDR | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.223 ± 0.041 | 0.577 ± 0.098 |
| 100 | 100 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.208 ± 0.031 | 0.525 ± 0.115 |
| 200 | 200 | AnchorOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.195 ± 0.044 | 0.480 ± 0.124 |
| 200 | 200 | AnchorOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.152 ± 0.028 | 0.405 ± 0.091 |
| 200 | 200 | AnchorOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.165 ± 0.022 | 0.413 ± 0.061 |
| 200 | 200 | AnchorOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.159 ± 0.034 | 0.423 ± 0.129 |
| 200 | 200 | AnchorPlugin | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.794 ± 0.283 | 1.883 ± 0.482 |
| 200 | 200 | AnchorPlugin | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.135 ± 0.022 | 0.330 ± 0.053 |
| 200 | 200 | AnchorPlugin | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.514 ± 0.190 | 1.192 ± 0.368 |
| 200 | 200 | AnchorPlugin | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.270 ± 0.080 | 0.635 ± 0.161 |
| 200 | 200 | DRLearner_PooledNoSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.116 ± 0.012 | 0.282 ± 0.034 |
| 200 | 200 | DRLearner_PooledNoSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.043 ± 0.016 | 0.098 ± 0.031 |
| 200 | 200 | DRLearner_PooledNoSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.081 ± 0.010 | 0.196 ± 0.028 |
| 200 | 200 | DRLearner_PooledNoSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.055 ± 0.013 | 0.129 ± 0.024 |
| 200 | 200 | DRLearner_PooledWithSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.116 ± 0.012 | 0.282 ± 0.034 |
| 200 | 200 | DRLearner_PooledWithSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.043 ± 0.016 | 0.098 ± 0.031 |
| 200 | 200 | DRLearner_PooledWithSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.081 ± 0.010 | 0.196 ± 0.028 |
| 200 | 200 | DRLearner_PooledWithSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.055 ± 0.013 | 0.130 ± 0.025 |
| 200 | 200 | EntropyBalancing | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.895 ± 0.179 | 2.167 ± 0.415 |
| 200 | 200 | EntropyBalancing | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.172 ± 0.075 | 0.420 ± 0.180 |
| 200 | 200 | EntropyBalancing | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 1.136 ± 0.645 | 2.497 ± 1.057 |
| 200 | 200 | EntropyBalancing | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.431 ± 0.230 | 1.032 ± 0.491 |
| 200 | 200 | IPWTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.149 ± 0.044 | 0.345 ± 0.076 |
| 200 | 200 | IPWTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.163 ± 0.059 | 0.393 ± 0.131 |
| 200 | 200 | IPWTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.165 ± 0.073 | 0.367 ± 0.133 |
| 200 | 200 | IPWTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.257 ± 0.100 | 0.613 ± 0.207 |
| 200 | 200 | OutcomeModelTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.150 ± 0.045 | 0.349 ± 0.075 |
| 200 | 200 | OutcomeModelTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.043 ± 0.016 | 0.100 ± 0.032 |
| 200 | 200 | OutcomeModelTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.091 ± 0.019 | 0.217 ± 0.039 |
| 200 | 200 | OutcomeModelTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.071 ± 0.025 | 0.159 ± 0.038 |
| 200 | 200 | ProposedA_FullyDirect | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.143 ± 0.018 | 0.363 ± 0.056 |
| 200 | 200 | ProposedA_FullyDirect | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.148 ± 0.022 | 0.396 ± 0.083 |
| 200 | 200 | ProposedA_FullyDirect | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.138 ± 0.018 | 0.336 ± 0.052 |
| 200 | 200 | ProposedA_FullyDirect | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.145 ± 0.023 | 0.380 ± 0.071 |
| 200 | 200 | ProposedB_LinearStepB | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.154 ± 0.030 | 0.387 ± 0.074 |
| 200 | 200 | ProposedB_LinearStepB | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.151 ± 0.028 | 0.405 ± 0.092 |
| 200 | 200 | ProposedB_LinearStepB | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.144 ± 0.018 | 0.358 ± 0.052 |
| 200 | 200 | ProposedB_LinearStepB | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.156 ± 0.030 | 0.415 ± 0.119 |
| 200 | 200 | ProposedB_SourceDR | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.051 ± 0.013 | 0.138 ± 0.046 |
| 200 | 200 | ProposedB_SourceDR | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.048 ± 0.014 | 0.140 ± 0.044 |
| 200 | 200 | ProposedB_SourceDR | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.045 ± 0.010 | 0.121 ± 0.033 |
| 200 | 200 | ProposedB_SourceDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.049 ± 0.014 | 0.135 ± 0.033 |
| 200 | 200 | ProxyOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.969 ± 0.779 | 1.673 ± 0.883 |
| 200 | 200 | ProxyOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.235 ± 0.062 | 0.612 ± 0.203 |
| 200 | 200 | ProxyOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.705 ± 0.467 | 1.298 ± 0.572 |
| 200 | 200 | ProxyOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.436 ± 0.181 | 0.979 ± 0.293 |
| 200 | 200 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.239 ± 0.042 | 0.588 ± 0.107 |
| 200 | 200 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.153 ± 0.022 | 0.392 ± 0.066 |
| 200 | 200 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.183 ± 0.022 | 0.475 ± 0.078 |
| 200 | 200 | TargetOnlyDR | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.161 ± 0.027 | 0.429 ± 0.088 |
| 500 | 500 | AnchorOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.103 ± 0.016 | 0.287 ± 0.045 |
| 500 | 500 | AnchorOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.094 ± 0.013 | 0.246 ± 0.033 |
| 500 | 500 | AnchorOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.135 ± 0.032 | 0.346 ± 0.090 |
| 500 | 500 | AnchorOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.100 ± 0.013 | 0.268 ± 0.052 |
| 500 | 500 | AnchorPlugin | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.159 ± 0.038 | 0.396 ± 0.085 |
| 500 | 500 | AnchorPlugin | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.252 ± 0.053 | 0.611 ± 0.130 |
| 500 | 500 | AnchorPlugin | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.985 ± 0.366 | 2.213 ± 0.590 |
| 500 | 500 | AnchorPlugin | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.509 ± 0.102 | 1.229 ± 0.216 |
| 500 | 500 | DRLearner_PooledNoSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.037 ± 0.014 | 0.089 ± 0.026 |
| 500 | 500 | DRLearner_PooledNoSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.047 ± 0.010 | 0.114 ± 0.023 |
| 500 | 500 | DRLearner_PooledNoSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.106 ± 0.007 | 0.253 ± 0.022 |
| 500 | 500 | DRLearner_PooledNoSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.074 ± 0.006 | 0.178 ± 0.016 |
| 500 | 500 | DRLearner_PooledWithSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.038 ± 0.014 | 0.089 ± 0.026 |
| 500 | 500 | DRLearner_PooledWithSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.047 ± 0.010 | 0.114 ± 0.023 |
| 500 | 500 | DRLearner_PooledWithSite | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.106 ± 0.007 | 0.253 ± 0.022 |
| 500 | 500 | DRLearner_PooledWithSite | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.074 ± 0.006 | 0.178 ± 0.015 |
| 500 | 500 | EntropyBalancing | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.186 ± 0.117 | 0.452 ± 0.293 |
| 500 | 500 | EntropyBalancing | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.356 ± 0.140 | 0.869 ± 0.354 |
| 500 | 500 | EntropyBalancing | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.935 ± 0.235 | 2.238 ± 0.492 |
| 500 | 500 | EntropyBalancing | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.934 ± 0.236 | 2.210 ± 0.501 |
| 500 | 500 | IPWTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.192 ± 0.098 | 0.468 ± 0.248 |
| 500 | 500 | IPWTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.265 ± 0.067 | 0.643 ± 0.170 |
| 500 | 500 | IPWTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.137 ± 0.039 | 0.322 ± 0.073 |
| 500 | 500 | IPWTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.177 ± 0.066 | 0.405 ± 0.133 |
| 500 | 500 | OutcomeModelTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.044 ± 0.017 | 0.102 ± 0.032 |
| 500 | 500 | OutcomeModelTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.057 ± 0.012 | 0.133 ± 0.027 |
| 500 | 500 | OutcomeModelTransport | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.132 ± 0.024 | 0.319 ± 0.057 |
| 500 | 500 | OutcomeModelTransport | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.090 ± 0.024 | 0.213 ± 0.052 |
| 500 | 500 | ProposedA_FullyDirect | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.099 ± 0.015 | 0.273 ± 0.041 |
| 500 | 500 | ProposedA_FullyDirect | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.090 ± 0.013 | 0.239 ± 0.041 |
| 500 | 500 | ProposedA_FullyDirect | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.090 ± 0.015 | 0.223 ± 0.034 |
| 500 | 500 | ProposedA_FullyDirect | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.087 ± 0.010 | 0.232 ± 0.042 |
| 500 | 500 | ProposedB_LinearStepB | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.103 ± 0.017 | 0.287 ± 0.045 |
| 500 | 500 | ProposedB_LinearStepB | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.092 ± 0.012 | 0.246 ± 0.035 |
| 500 | 500 | ProposedB_LinearStepB | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.094 ± 0.018 | 0.230 ± 0.040 |
| 500 | 500 | ProposedB_LinearStepB | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.090 ± 0.010 | 0.237 ± 0.041 |
| 500 | 500 | ProposedB_SourceDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.046 ± 0.015 | 0.130 ± 0.045 |
| 500 | 500 | ProposedB_SourceDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.048 ± 0.009 | 0.127 ± 0.027 |
| 500 | 500 | ProposedB_SourceDR | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.050 ± 0.015 | 0.132 ± 0.043 |
| 500 | 500 | ProposedB_SourceDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.045 ± 0.015 | 0.120 ± 0.033 |
| 500 | 500 | ProxyOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.230 ± 0.078 | 0.600 ± 0.199 |
| 500 | 500 | ProxyOnly | 0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.351 ± 0.135 | 0.802 ± 0.240 |
| 500 | 500 | ProxyOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 1.573 ± 0.964 | 2.298 ± 1.009 |
| 500 | 500 | ProxyOnly | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.641 ± 0.352 | 1.256 ± 0.436 |
| 500 | 500 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.102 ± 0.016 | 0.282 ± 0.043 |
| 500 | 500 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.097 ± 0.017 | 0.262 ± 0.042 |
| 500 | 500 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.158 ± 0.024 | 0.397 ± 0.061 |
| 500 | 500 | TargetOnlyDR | -0.000 ± 0.000 | -0.067 ± 0.000 | 1.000 ± 0.000 | 0.116 ± 0.011 | 0.319 ± 0.054 |

### Extended Targeting Metrics

| m0 | m1 | Method | Top-10% Captured | Top-20% Captured | Top-30% Ratio (↑) |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 50 | 50 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 100 | 100 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 200 | 200 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | AnchorOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | AnchorPlugin | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | DRLearner_PooledNoSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | DRLearner_PooledWithSite | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | EntropyBalancing | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | IPWTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | OutcomeModelTransport | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedA_FullyDirect | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedB_LinearStepB | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProposedB_SourceDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | ProxyOnly | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |
| 500 | 500 | TargetOnlyDR | -0.067 ± 0.000 | -0.067 ± 0.000 | N/A |

---

## 7. Plots

### PEHE vs Sweep Parameter (↓ lower is better)

![PEHE](l1tcl_gold_dim_sweep_pehe.png)

### ATE Error vs Sweep Parameter (↓ lower is better)

![ATE Error](l1tcl_gold_dim_sweep_ate.png)

### Spearman Correlation vs Sweep Parameter (↑ higher is better)

![Correlation](l1tcl_gold_dim_sweep_corr.png)

---

## 8. Key Findings

1. **Best overall PEHE:** DRLearner_PooledNoSite achieves lowest average PEHE (0.046)
2. **Best overall ATE Error:** ProposedB_SourceDR achieves lowest average ATE error (0.0183)
3. **Proposed vs ProxyOnly:** Proposed reduces PEHE by 74.8% on average
4. **Lowest policy regret:** DRLearner_PooledWithSite (0.0036)
5. **Scaling:** ProposedB_SourceDR ATE error decreases with higher m0
6. **Note:** Ranking metrics (Spearman, Qini) are NaN for L1-TCL DGP due to constant τ

---

## Appendix: Configuration

```python
sweep_param = 'm0'
sweep_values = [50, 100, 200, 500]
base_scenario = {'n_proxy_total': 5000, 'C_sources': 10, 'a5_effective_sparsity': 0.1, 'use_l1tcl_dgp': True}
```

