# Fair DGP: Target size × Dimensionality grid (m₀ × p_dim)

**Benchmark ID:** `gold_fair_dim_sweep`

**Generated:** 2026-02-06 05:14

---

## 1. Motivation

**Research Question:** How do target sample size and feature dimensionality jointly affect estimator performance under fair DGP settings?

**Why This Matters:**
This 2D grid explores the interaction between:
1. **Target size (m₀ = m₁):** More target data → less need for transfer
2. **Dimensionality (d):** Higher d → harder estimation, potentially more benefit from source data

**Key Grid:**
- Target: m₀ = m₁ ∈ {50, 100, 200, 500}
- Dimension: d ∈ {10, 20, 50, 100}
- Total: 4 × 4 = 16 scenarios

**Critical Trade-offs:**
- Low d + large m₀: Target-only methods may suffice
- High d + small m₀: Transfer learning becomes essential
- The "break-even" point depends on SNR and overlap

**DGP Settings (Fair):**
- SNR ≈ 3-4 (nontransfer_scale = 0.1)
- Overlap AUC ≈ 0.75 (overlap_lambda = 0.25)
- Controlled intercept drift (scale = 0.5)
- 20,000 source observations across 10 sites

---

## 2. Simulation Setup

**Fair DGP with Variable Dimensionality:**

Uses standard synthetic DGP with fair settings optimized for method comparison:
- **Covariates:** X ~ N(0, I_d) with variable d
- **Treatment:** A ~ Bernoulli(e(X)) with logistic propensity
- **Outcome:** Y = μ_A(X) + ε with heterogeneous effects
- **Transfer:** Controlled nontransfer component (SNR ≈ 3-4)
- **Sites:** 10 source sites with moderate covariate shift

### Swept Parameters (Varied Across Scenarios)

| Parameter | Values | Description |
|-----------|--------|-------------|
| **m0** | `[50, 100, 200, 500]` | Target placebo/control sample size (n₀) |
| **p_dim** | `[10, 20, 50, 100]` | Covariate dimension (d). Higher d = harder estimation. |

### Coupled Parameters (Derived from Swept)

| Parameter | Coupling | Description |
|-----------|----------|-------------|
| **m1** | `= m0` | Target treated sample size (n₁). If 0, only Option B methods are feasible. |

### Fixed Parameters (Held Constant)

| Parameter | Value | Description |
|-----------|-------|-------------|
| n_proxy_total | `20000` | Total source/proxy observations across all sites |
| C_sources | `10` | Number of source sites (K) |
| nontransfer_scale | `0.1` | Scale of non-transferable component (σᵥ). Higher = less transfer benefit. |
| use_fair_dgp | `True` | Parameter: use_fair_dgp |
| overlap_lambda | `0.25` | Covariate distribution divergence (0=identical, 1=disjoint) |
| intercept_drift_scale | `0.5` | Scale of arm-specific intercept drift across sites |

### Experimental Design Summary

- **Sweep type:** `2d`
- **Number of swept parameters:** 2
- **Number of coupled parameters:** 1
- **Number of fixed parameters:** 6
- **Total unique scenarios:** 16

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

### 4.1 Method Summary Table

| Method | Category | Target Placebo | Target Treated | Source | Description |
|--------|----------|----------------|----------------|--------|-------------|
| **TargetOnlyDR** | Baseline | ✓ | ✓ | ✗ | Target-only DR learner (no transfer) |
| **ProxyOnly** | Baseline | ✗ | ✗ | ✓ | Source-only proxy (no target correction) |
| **Glmtrans_Auto** | Transfer Learning | ✓ | ✓ | ✓ | glmtrans with auto source detection |
| **Glmtrans_DR_CrossFit** | Transfer Learning | ✓ | ✓ | ✓ | glmtrans with CROSS-FITTED DR (RECOMMENDED) |
| **Glmtrans_OptionB** | Transfer Learning | ✓ | ✗ | ✓ | Option B: glmtrans source detection + Source-DR CATE |
| **AnchorOnly** | Anchor | ✓ | ✓ | ✓ | Placebo-anchored with DR (needs target treated) |
| **AnchorPlugin** | Anchor | ✓ | ✗ | ✓ | Placebo-anchored plug-in (no DR) |
| **IPWTransport** | Transport | ✓ | ✗ | ✓ | IPW-weighted outcome models |
| **EntropyBalancing** | Transport | ✓ | ✗ | ✓ | Entropy balancing weights |
| **OutcomeModelTransport** | Transport | ✓ | ✗ | ✓ | Unweighted outcome models |

### 4.2 Method Implementation Details

#### TargetOnlyDR

**Category:** Baseline

**Description:** Target-only DR learner (no transfer)

**Data Requirements:** Target placebo (A=0), Target treated (A=1)

**Pseudo-code:**
```
1. Fit μ̂₀(x) on target controls: (X_target[A=0], Y_target[A=0])
2. Fit μ̂₁(x) on target treated: (X_target[A=1], Y_target[A=1])
3. Compute DR pseudo-outcomes on target:
   Γᵢ = (Aᵢ/ê)(Yᵢ - μ̂₁(Xᵢ)) + μ̂₁(Xᵢ) - ((1-Aᵢ)/(1-ê))(Yᵢ - μ̂₀(Xᵢ)) - μ̂₀(Xᵢ)
4. Fit τ̂(x) on (X_target, Γ) using Lasso
```

**Reference:** Kennedy (2020) - Doubly Robust Learner

---

#### ProxyOnly

**Category:** Baseline

**Description:** Source-only proxy (no target correction)

**Data Requirements:** Source data

**Pseudo-code:**
```
1. Pool all source data by treatment arm
2. Fit μ̂₀^src(x) on source controls
3. Fit μ̂₁^src(x) on source treated
4. Predict: τ̂(x) = μ̂₁^src(x) - μ̂₀^src(x)
```

**Reference:** Naive source pooling baseline

---

#### Glmtrans_Auto

**Category:** Transfer Learning

**Description:** glmtrans with auto source detection

**Data Requirements:** Target placebo (A=0), Target treated (A=1), Source data

**Pseudo-code:**
```
For each outcome model (μ₀ and μ₁):
  1. SOURCE DETECTION: Identify transferable sources
     - Fit target-only model, compute CV loss L_target
     - For each source k: compute loss L_k
     - Source k transferable if L_k ≤ C₀ · L_target
  2. TRANSFER STEP: Pool transferable sources
     - Fit elastic-net on pooled source data → ŵ_A
  3. DEBIAS STEP: Correct on target
     - Compute residuals: r = Y_target - X_target · ŵ_A
     - Fit elastic-net on residuals → δ̂_A
  4. FINAL: β̂ = ŵ_A + δ̂_A

CATE: τ̂(x) = μ̂₁(x) - μ̂₀(x)
```

**Reference:** Tian & Feng (2023) JASA

---

#### Glmtrans_DR_CrossFit

**Category:** Transfer Learning

**Description:** glmtrans with CROSS-FITTED DR (RECOMMENDED)

**Data Requirements:** Target placebo (A=0), Target treated (A=1), Source data

**Pseudo-code:**
```
For k = 1, ..., K folds:
  1. Split target into train (fold ≠ k) and test (fold = k)
  2. Fit glmtrans on train target + ALL sources
  3. Get OUT-OF-FOLD predictions μ̂₀[test], μ̂₁[test]
  4. Fit ridge logistic propensity on train target
  5. Get OUT-OF-FOLD ê[test]

After cross-fitting:
  6. Clip propensities: ê_clipped = clip(ê, 0.05, 0.95)
  7. Compute DR pseudo-outcomes (using OOF estimates):
     Γᵢ = μ̂₁(Xᵢ) - μ̂₀(Xᵢ) + (Aᵢ-ê)/(ê(1-ê)) · residual
  8. Fit τ̂(x) on (X_target, Γ) using Lasso

Diagnostics:
  - Var(Γ) / Var(μ̂₁-μ̂₀): If >> 1, DR is hurting
  - Max inverse weight: If > 20, weights are unstable
```

**Reference:** Advisor-recommended cross-fitted DR construction

---

#### Glmtrans_OptionB

**Category:** Transfer Learning

**Description:** Option B: glmtrans source detection + Source-DR CATE

**Data Requirements:** Target placebo (A=0), Source data

**Pseudo-code:**
```
Stage 0 (Source Detection - Control Arm ONLY):
  # This is the ONLY place glmtrans theory applies
  1. Target placebo: (X_t, Y_t(0))
  2. Source controls: [(X_sk[A=0], Y_sk(0)) for k in 1..K]
  3. Run glmtrans(target, sources, family="gaussian", transfer.source.id="auto")
  4. Return selected sources: Ŝ₀ ⊂ {1,...,K}
  # Uses ONLY Y_target(0) - exactly as glmtrans was designed

Stage 1 (Restrict to Selected Sources - NO WEIGHTING):
  # Simply subset. No soft selection, no importance weighting.
  D_src^good = ∪_{k ∈ Ŝ₀} D_k

Stage 2 (Source-DR CATE):
  # DR learning happens WHERE IDENTIFICATION HOLDS: on sources
  1. Fit μ̂₀^src on X_good[A=0], Y_good[A=0]
  2. Fit μ̂₁^src on X_good[A=1], Y_good[A=1]  
  3. ê = mean(A) on selected sources
  4. DR pseudo-outcomes on SOURCES:
     Γᵢ = μ̂₁(Xᵢ) - μ̂₀(Xᵢ) + (Aᵢ-ê)/(ê(1-ê)) · (Yᵢ - μ̂_{Aᵢ}(Xᵢ))
  5. Fit τ̂^src(x) = E[Γ|X=x] on source pseudo-outcomes

Stage 3 (Transport to Target):
  # Direct transport - relies on structural similarity encoded by Ŝ₀
  τ̂_target(x) := τ̂^src(x)
  # No further correction (we have no target treated data)

VALID FOR: Placebo-only target (m₁=0)
IDENTIFICATION: Via transferable source selection + DR on sources
```

**Reference:** Advisor construction based on Tian & Feng (2023) JASA

---

#### AnchorOnly

**Category:** Anchor

**Description:** Placebo-anchored with DR (needs target treated)

**Data Requirements:** Target placebo (A=0), Target treated (A=1), Source data

**Pseudo-code:**
```
1. Fit source proxy: μ̂₀^src(x) on pooled source controls
2. Compute residuals on target placebo: δ̂₀(x) = Y - μ̂₀^src(X)
3. Fit correction: δ̂₀(x) using Lasso on target placebo residuals
4. Corrected μ̂₀(x) = μ̂₀^src(x) + δ̂₀(x)
5. Fit μ̂₁(x) directly on target treated
6. DR pseudo-outcomes + CATE model
```

**Reference:** Placebo-anchored transfer

---

#### AnchorPlugin

**Category:** Anchor

**Description:** Placebo-anchored plug-in (no DR)

**Data Requirements:** Target placebo (A=0), Source data

**Pseudo-code:**
```
1. Fit source proxy: μ̂₀^src(x), μ̂₁^src(x)
2. Compute residuals on target placebo
3. Fit correction δ̂₀(x) on residuals
4. Plug-in: τ̂(x) = μ̂₁^src(x) - (μ̂₀^src(x) + δ̂₀(x))
   (No DR pseudo-outcomes, no target treated needed)
```

**Reference:** Plug-in variant of anchor

---

#### IPWTransport

**Category:** Transport

**Description:** IPW-weighted outcome models

**Data Requirements:** Target placebo (A=0), Source data

**Pseudo-code:**
```
1. Estimate site membership: P(S=target|X)
2. Compute IPW weights: w(x) = P(S=target|X) / P(S=source|X)
3. Fit weighted outcome models on source:
   μ̂ₐ = argmin Σᵢ wᵢ·(Yᵢ - μ(Xᵢ))²
4. Predict: τ̂(x) = μ̂₁(x) - μ̂₀(x)
```

**Reference:** Hong et al. - IPW transport

---

#### EntropyBalancing

**Category:** Transport

**Description:** Entropy balancing weights

**Data Requirements:** Target placebo (A=0), Source data

**Pseudo-code:**
```
1. Find weights w that balance source to target:
   Σᵢ wᵢ·Xᵢ = X̄_target (moment matching)
   max Σᵢ wᵢ·log(wᵢ) (max entropy)
2. Fit weighted outcome models
3. Predict: τ̂(x) = μ̂₁(x) - μ̂₀(x)
```

**Reference:** Hainmueller (2012)

---

#### OutcomeModelTransport

**Category:** Transport

**Description:** Unweighted outcome models

**Data Requirements:** Target placebo (A=0), Source data

**Pseudo-code:**
```
1. Fit outcome models on source (unweighted):
   μ̂ₐ^src on (X_source[A=a], Y_source[A=a])
2. Predict on target: τ̂(x) = μ̂₁^src(x) - μ̂₀^src(x)
   (Assumes outcome model generalizes across sites)
```

**Reference:** Baseline - no reweighting

---

---

## 5. Experiment Summary

- **Sweep parameter:** `m0` ∈ [50, 100, 200, 500]
- **Monte Carlo replicates:** 5 per scenario
- **Methods evaluated:** 10
- **Total runs:** 800

---

## 6. Results

### Best Methods (averaged across sweep)

| Metric | Best Method | Value | Direction |
|--------|-------------|-------|----------|
| PEHE | **Glmtrans_DR_CrossFit** | 0.2644 | ↓ lower |
| ATE Error | **Glmtrans_DR_CrossFit** | 0.0216 | ↓ lower |
| Spearman ρ | **Glmtrans_DR_CrossFit** | 0.9985 | ↑ higher |
| Kendall τ | **Glmtrans_DR_CrossFit** | 0.9681 | ↑ higher |
| Qini AUC | **Glmtrans_DR_CrossFit** | 0.9987 | ↑ higher |
| Top-10% Ratio | **Glmtrans_DR_CrossFit** | 0.9991 | ↑ higher |
| Top-20% Ratio | **Glmtrans_DR_CrossFit** | 0.9983 | ↑ higher |
| Calibration R² | **Glmtrans_DR_CrossFit** | 0.9974 | ↑ higher |
| CATE ECE | **Glmtrans_DR_CrossFit** | 0.0542 | ↓ lower |
| Policy Value | **Glmtrans_Auto** | 4.8139 | ↑ higher |
| Policy Regret | **Glmtrans_DR_CrossFit** | 0.0035 | ↓ lower |

### Core Metrics

| m0 | m1 | Method | PEHE (↓) | ATE Err (↓) | Spearman (↑) | Qini (↑) |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 8.101 ± 0.990 | 0.716 ± 0.577 | 0.381 ± 0.043 | 0.396 ± 0.040 |
| 50 | 50 | AnchorOnly | 5.064 ± 0.568 | 0.532 ± 0.331 | 0.479 ± 0.083 | 0.495 ± 0.087 |
| 50 | 50 | AnchorOnly | 2.801 ± 0.658 | 0.426 ± 0.246 | 0.684 ± 0.044 | 0.703 ± 0.043 |
| 50 | 50 | AnchorOnly | 1.499 ± 0.531 | 0.291 ± 0.210 | 0.792 ± 0.022 | 0.801 ± 0.023 |
| 50 | 50 | AnchorPlugin | 7.611 ± 1.294 | 1.401 ± 0.707 | 0.532 ± 0.089 | 0.549 ± 0.089 |
| 50 | 50 | AnchorPlugin | 4.640 ± 0.729 | 0.692 ± 0.769 | 0.620 ± 0.110 | 0.636 ± 0.106 |
| 50 | 50 | AnchorPlugin | 2.508 ± 0.848 | 0.586 ± 0.363 | 0.740 ± 0.094 | 0.757 ± 0.092 |
| 50 | 50 | AnchorPlugin | 1.692 ± 0.794 | 0.776 ± 0.460 | 0.775 ± 0.111 | 0.785 ± 0.106 |
| 50 | 50 | EntropyBalancing | 5.484 ± 1.926 | 1.062 ± 1.355 | 0.779 ± 0.124 | 0.792 ± 0.120 |
| 50 | 50 | EntropyBalancing | 3.186 ± 1.525 | 1.083 ± 0.837 | 0.839 ± 0.141 | 0.848 ± 0.136 |
| 50 | 50 | EntropyBalancing | 2.453 ± 2.028 | 0.844 ± 1.041 | 0.760 ± 0.277 | 0.772 ± 0.273 |
| 50 | 50 | EntropyBalancing | 1.748 ± 0.267 | 0.757 ± 0.789 | 0.795 ± 0.104 | 0.806 ± 0.098 |
| 50 | 50 | Glmtrans_Auto | 3.796 ± 1.806 | 0.389 ± 0.397 | 0.887 ± 0.087 | 0.895 ± 0.082 |
| 50 | 50 | Glmtrans_Auto | 1.627 ± 1.013 | 0.122 ± 0.145 | 0.947 ± 0.062 | 0.951 ± 0.057 |
| 50 | 50 | Glmtrans_Auto | 0.601 ± 0.133 | 0.036 ± 0.017 | 0.984 ± 0.008 | 0.986 ± 0.007 |
| 50 | 50 | Glmtrans_Auto | 0.577 ± 0.093 | 0.073 ± 0.060 | 0.963 ± 0.037 | 0.966 ± 0.034 |
| 50 | 50 | Glmtrans_DR_CrossFit | 7.172 ± 1.301 | 0.886 ± 0.538 | 0.585 ± 0.120 | 0.604 ± 0.119 |
| 50 | 50 | Glmtrans_DR_CrossFit | 2.462 ± 0.556 | 0.222 ± 0.187 | 0.900 ± 0.028 | 0.908 ± 0.026 |
| 50 | 50 | Glmtrans_DR_CrossFit | 1.192 ± 0.448 | 0.324 ± 0.222 | 0.947 ± 0.035 | 0.951 ± 0.033 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.597 ± 0.169 | 0.117 ± 0.120 | 0.950 ± 0.051 | 0.954 ± 0.048 |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 50 | 50 | IPWTransport | 4.849 ± 1.651 | 1.059 ± 1.188 | 0.833 ± 0.094 | 0.844 ± 0.089 |
| 50 | 50 | IPWTransport | 3.129 ± 1.606 | 1.083 ± 0.827 | 0.843 ± 0.149 | 0.852 ± 0.143 |
| 50 | 50 | IPWTransport | 2.478 ± 1.981 | 0.820 ± 1.008 | 0.754 ± 0.271 | 0.767 ± 0.267 |
| 50 | 50 | IPWTransport | 1.774 ± 0.239 | 0.769 ± 0.776 | 0.785 ± 0.113 | 0.797 ± 0.106 |
| 50 | 50 | OutcomeModelTransport | 4.828 ± 1.594 | 1.147 ± 1.133 | 0.836 ± 0.091 | 0.847 ± 0.086 |
| 50 | 50 | OutcomeModelTransport | 3.166 ± 1.596 | 1.126 ± 0.803 | 0.841 ± 0.152 | 0.850 ± 0.146 |
| 50 | 50 | OutcomeModelTransport | 2.499 ± 1.994 | 0.859 ± 1.043 | 0.754 ± 0.269 | 0.767 ± 0.265 |
| 50 | 50 | OutcomeModelTransport | 1.776 ± 0.234 | 0.772 ± 0.776 | 0.784 ± 0.113 | 0.796 ± 0.107 |
| 50 | 50 | ProxyOnly | 8.849 ± 1.137 | 1.832 ± 1.422 | 0.174 ± 0.045 | 0.178 ± 0.050 |
| 50 | 50 | ProxyOnly | 5.706 ± 0.684 | 1.680 ± 1.203 | 0.369 ± 0.054 | 0.382 ± 0.058 |
| 50 | 50 | ProxyOnly | 3.359 ± 0.883 | 0.757 ± 0.647 | 0.486 ± 0.088 | 0.504 ± 0.090 |
| 50 | 50 | ProxyOnly | 2.267 ± 0.876 | 0.908 ± 0.831 | 0.556 ± 0.169 | 0.566 ± 0.167 |
| 50 | 50 | TargetOnlyDR | 8.224 ± 1.001 | 1.016 ± 0.521 | 0.353 ± 0.096 | 0.364 ± 0.095 |
| 50 | 50 | TargetOnlyDR | 5.145 ± 0.562 | 0.623 ± 0.437 | 0.443 ± 0.075 | 0.462 ± 0.076 |
| 50 | 50 | TargetOnlyDR | 2.706 ± 0.474 | 0.242 ± 0.286 | 0.707 ± 0.054 | 0.725 ± 0.050 |
| 50 | 50 | TargetOnlyDR | 1.585 ± 0.418 | 0.274 ± 0.112 | 0.752 ± 0.063 | 0.762 ± 0.062 |
| 100 | 100 | AnchorOnly | 2.890 ± 0.207 | 0.302 ± 0.271 | 0.744 ± 0.082 | 0.759 ± 0.079 |
| 100 | 100 | AnchorOnly | 5.492 ± 1.162 | 0.373 ± 0.245 | 0.558 ± 0.089 | 0.576 ± 0.087 |
| 100 | 100 | AnchorOnly | 1.722 ± 0.632 | 0.096 ± 0.046 | 0.855 ± 0.045 | 0.863 ± 0.041 |
| 100 | 100 | AnchorOnly | 7.337 ± 0.593 | 0.396 ± 0.302 | 0.408 ± 0.072 | 0.427 ± 0.074 |
| 100 | 100 | AnchorPlugin | 2.421 ± 0.583 | 0.374 ± 0.210 | 0.787 ± 0.096 | 0.799 ± 0.094 |
| 100 | 100 | AnchorPlugin | 4.929 ± 1.672 | 1.556 ± 0.877 | 0.678 ± 0.194 | 0.692 ± 0.192 |
| 100 | 100 | AnchorPlugin | 1.955 ± 1.108 | 0.440 ± 0.400 | 0.776 ± 0.201 | 0.787 ± 0.194 |
| 100 | 100 | AnchorPlugin | 6.367 ± 1.138 | 1.408 ± 2.021 | 0.646 ± 0.028 | 0.664 ± 0.030 |
| 100 | 100 | EntropyBalancing | 2.470 ± 0.823 | 0.623 ± 0.329 | 0.778 ± 0.163 | 0.790 ± 0.160 |
| 100 | 100 | EntropyBalancing | 4.415 ± 2.625 | 1.824 ± 1.529 | 0.753 ± 0.244 | 0.766 ± 0.238 |
| 100 | 100 | EntropyBalancing | 1.975 ± 0.997 | 0.357 ± 0.407 | 0.780 ± 0.179 | 0.792 ± 0.170 |
| 100 | 100 | EntropyBalancing | 4.357 ± 0.966 | 0.778 ± 0.640 | 0.836 ± 0.064 | 0.848 ± 0.061 |
| 100 | 100 | Glmtrans_Auto | 0.607 ± 0.147 | 0.094 ± 0.047 | 0.988 ± 0.005 | 0.990 ± 0.004 |
| 100 | 100 | Glmtrans_Auto | 0.802 ± 0.103 | 0.083 ± 0.084 | 0.992 ± 0.003 | 0.992 ± 0.002 |
| 100 | 100 | Glmtrans_Auto | 0.421 ± 0.155 | 0.060 ± 0.053 | 0.991 ± 0.007 | 0.992 ± 0.007 |
| 100 | 100 | Glmtrans_Auto | 1.461 ± 0.626 | 0.156 ± 0.101 | 0.979 ± 0.016 | 0.982 ± 0.014 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.577 ± 0.148 | 0.080 ± 0.057 | 0.989 ± 0.005 | 0.990 ± 0.005 |
| 100 | 100 | Glmtrans_DR_CrossFit | 1.569 ± 0.987 | 0.114 ± 0.135 | 0.966 ± 0.035 | 0.969 ± 0.032 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.385 ± 0.173 | 0.056 ± 0.041 | 0.990 ± 0.009 | 0.991 ± 0.008 |
| 100 | 100 | Glmtrans_DR_CrossFit | 3.131 ± 1.590 | 0.213 ± 0.153 | 0.897 ± 0.093 | 0.906 ± 0.086 |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 100 | 100 | IPWTransport | 2.468 ± 0.815 | 0.617 ± 0.345 | 0.778 ± 0.161 | 0.790 ± 0.158 |
| 100 | 100 | IPWTransport | 4.304 ± 2.620 | 1.926 ± 1.653 | 0.777 ± 0.241 | 0.789 ± 0.234 |
| 100 | 100 | IPWTransport | 1.989 ± 1.024 | 0.361 ± 0.422 | 0.772 ± 0.187 | 0.784 ± 0.178 |
| 100 | 100 | IPWTransport | 3.690 ± 1.274 | 0.758 ± 0.616 | 0.878 ± 0.072 | 0.888 ± 0.069 |
| 100 | 100 | OutcomeModelTransport | 2.462 ± 0.816 | 0.604 ± 0.345 | 0.779 ± 0.160 | 0.791 ± 0.157 |
| 100 | 100 | OutcomeModelTransport | 3.984 ± 2.486 | 1.664 ± 1.324 | 0.798 ± 0.244 | 0.809 ± 0.238 |
| 100 | 100 | OutcomeModelTransport | 1.994 ± 1.029 | 0.338 ± 0.424 | 0.769 ± 0.189 | 0.781 ± 0.181 |
| 100 | 100 | OutcomeModelTransport | 3.512 ± 1.418 | 0.757 ± 0.620 | 0.887 ± 0.078 | 0.896 ± 0.074 |
| 100 | 100 | ProxyOnly | 3.345 ± 0.445 | 0.545 ± 0.499 | 0.572 ± 0.096 | 0.591 ± 0.092 |
| 100 | 100 | ProxyOnly | 5.960 ± 1.134 | 1.079 ± 1.031 | 0.426 ± 0.111 | 0.441 ± 0.109 |
| 100 | 100 | ProxyOnly | 2.428 ± 1.143 | 0.386 ± 0.172 | 0.643 ± 0.263 | 0.654 ± 0.262 |
| 100 | 100 | ProxyOnly | 7.735 ± 0.554 | 1.354 ± 0.626 | 0.303 ± 0.056 | 0.316 ± 0.054 |
| 100 | 100 | TargetOnlyDR | 2.877 ± 0.205 | 0.311 ± 0.301 | 0.748 ± 0.096 | 0.761 ± 0.092 |
| 100 | 100 | TargetOnlyDR | 5.442 ± 1.168 | 0.372 ± 0.170 | 0.563 ± 0.084 | 0.578 ± 0.087 |
| 100 | 100 | TargetOnlyDR | 1.639 ± 0.507 | 0.101 ± 0.063 | 0.866 ± 0.054 | 0.873 ± 0.050 |
| 100 | 100 | TargetOnlyDR | 7.242 ± 0.579 | 0.200 ± 0.185 | 0.459 ± 0.036 | 0.478 ± 0.034 |
| 200 | 200 | AnchorOnly | 2.480 ± 0.596 | 0.142 ± 0.105 | 0.783 ± 0.045 | 0.797 ± 0.040 |
| 200 | 200 | AnchorOnly | 4.550 ± 0.987 | 0.353 ± 0.110 | 0.653 ± 0.052 | 0.669 ± 0.048 |
| 200 | 200 | AnchorOnly | 8.101 ± 1.738 | 0.295 ± 0.186 | 0.506 ± 0.073 | 0.523 ± 0.073 |
| 200 | 200 | AnchorOnly | 1.284 ± 0.563 | 0.088 ± 0.043 | 0.872 ± 0.013 | 0.880 ± 0.010 |
| 200 | 200 | AnchorPlugin | 2.199 ± 0.922 | 0.534 ± 0.443 | 0.812 ± 0.121 | 0.823 ± 0.116 |
| 200 | 200 | AnchorPlugin | 3.540 ± 1.014 | 0.566 ± 0.273 | 0.789 ± 0.049 | 0.803 ± 0.046 |
| 200 | 200 | AnchorPlugin | 7.362 ± 2.520 | 1.835 ± 0.827 | 0.628 ± 0.185 | 0.642 ± 0.184 |
| 200 | 200 | AnchorPlugin | 1.665 ± 1.112 | 0.500 ± 0.448 | 0.783 ± 0.171 | 0.794 ± 0.167 |
| 200 | 200 | EntropyBalancing | 2.188 ± 1.089 | 0.905 ± 0.624 | 0.847 ± 0.197 | 0.856 ± 0.190 |
| 200 | 200 | EntropyBalancing | 2.489 ± 1.360 | 0.499 ± 0.365 | 0.894 ± 0.076 | 0.902 ± 0.072 |
| 200 | 200 | EntropyBalancing | 6.031 ± 3.304 | 0.611 ± 0.693 | 0.738 ± 0.223 | 0.750 ± 0.220 |
| 200 | 200 | EntropyBalancing | 1.723 ± 1.132 | 0.586 ± 0.317 | 0.788 ± 0.224 | 0.798 ± 0.221 |
| 200 | 200 | Glmtrans_Auto | 0.371 ± 0.111 | 0.038 ± 0.026 | 0.994 ± 0.004 | 0.995 ± 0.003 |
| 200 | 200 | Glmtrans_Auto | 0.629 ± 0.185 | 0.046 ± 0.042 | 0.993 ± 0.003 | 0.994 ± 0.003 |
| 200 | 200 | Glmtrans_Auto | 0.903 ± 0.186 | 0.059 ± 0.027 | 0.995 ± 0.002 | 0.995 ± 0.002 |
| 200 | 200 | Glmtrans_Auto | 0.398 ± 0.177 | 0.040 ± 0.023 | 0.987 ± 0.005 | 0.988 ± 0.004 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.333 ± 0.083 | 0.037 ± 0.026 | 0.995 ± 0.003 | 0.996 ± 0.003 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.600 ± 0.212 | 0.063 ± 0.046 | 0.993 ± 0.003 | 0.994 ± 0.003 |
| 200 | 200 | Glmtrans_DR_CrossFit | 1.334 ± 0.369 | 0.099 ± 0.098 | 0.988 ± 0.003 | 0.990 ± 0.002 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.400 ± 0.180 | 0.034 ± 0.022 | 0.986 ± 0.005 | 0.987 ± 0.004 |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 200 | 200 | IPWTransport | 2.184 ± 1.080 | 0.900 ± 0.628 | 0.848 ± 0.197 | 0.857 ± 0.189 |
| 200 | 200 | IPWTransport | 2.363 ± 1.409 | 0.483 ± 0.340 | 0.902 ± 0.077 | 0.910 ± 0.072 |
| 200 | 200 | IPWTransport | 5.669 ± 3.493 | 0.569 ± 0.783 | 0.765 ± 0.229 | 0.775 ± 0.225 |
| 200 | 200 | IPWTransport | 1.730 ± 1.129 | 0.593 ± 0.306 | 0.786 ± 0.222 | 0.797 ± 0.219 |
| 200 | 200 | OutcomeModelTransport | 2.196 ± 1.080 | 0.927 ± 0.640 | 0.849 ± 0.199 | 0.857 ± 0.191 |
| 200 | 200 | OutcomeModelTransport | 2.254 ± 1.467 | 0.538 ± 0.351 | 0.910 ± 0.077 | 0.917 ± 0.072 |
| 200 | 200 | OutcomeModelTransport | 5.612 ± 3.546 | 0.879 ± 0.657 | 0.769 ± 0.230 | 0.780 ± 0.225 |
| 200 | 200 | OutcomeModelTransport | 1.716 ± 1.148 | 0.557 ± 0.325 | 0.786 ± 0.223 | 0.796 ± 0.220 |
| 200 | 200 | ProxyOnly | 2.980 ± 0.706 | 0.547 ± 0.382 | 0.636 ± 0.083 | 0.652 ± 0.079 |
| 200 | 200 | ProxyOnly | 5.077 ± 1.125 | 0.677 ± 0.833 | 0.535 ± 0.063 | 0.553 ± 0.062 |
| 200 | 200 | ProxyOnly | 9.136 ± 1.445 | 2.400 ± 1.865 | 0.378 ± 0.079 | 0.393 ± 0.084 |
| 200 | 200 | ProxyOnly | 2.109 ± 1.102 | 0.709 ± 0.580 | 0.650 ± 0.109 | 0.669 ± 0.102 |
| 200 | 200 | TargetOnlyDR | 2.445 ± 0.540 | 0.131 ± 0.087 | 0.802 ± 0.032 | 0.814 ± 0.029 |
| 200 | 200 | TargetOnlyDR | 4.505 ± 0.990 | 0.317 ± 0.133 | 0.673 ± 0.030 | 0.689 ± 0.029 |
| 200 | 200 | TargetOnlyDR | 7.987 ± 1.609 | 0.234 ± 0.192 | 0.526 ± 0.033 | 0.544 ± 0.034 |
| 200 | 200 | TargetOnlyDR | 1.279 ± 0.594 | 0.096 ± 0.046 | 0.879 ± 0.006 | 0.886 ± 0.005 |
| 500 | 500 | AnchorOnly | 7.688 ± 1.435 | 0.368 ± 0.336 | 0.565 ± 0.040 | 0.583 ± 0.042 |
| 500 | 500 | AnchorOnly | 4.530 ± 0.842 | 0.241 ± 0.207 | 0.673 ± 0.030 | 0.685 ± 0.029 |
| 500 | 500 | AnchorOnly | 1.248 ± 0.321 | 0.035 ± 0.025 | 0.885 ± 0.026 | 0.894 ± 0.023 |
| 500 | 500 | AnchorOnly | 2.619 ± 0.501 | 0.216 ± 0.134 | 0.799 ± 0.022 | 0.814 ± 0.021 |
| 500 | 500 | AnchorPlugin | 6.393 ± 2.112 | 0.959 ± 0.428 | 0.697 ± 0.114 | 0.714 ± 0.109 |
| 500 | 500 | AnchorPlugin | 3.549 ± 0.821 | 0.379 ± 0.313 | 0.776 ± 0.101 | 0.790 ± 0.097 |
| 500 | 500 | AnchorPlugin | 1.421 ± 0.426 | 0.406 ± 0.179 | 0.866 ± 0.050 | 0.876 ± 0.046 |
| 500 | 500 | AnchorPlugin | 3.033 ± 1.031 | 0.259 ± 0.164 | 0.664 ± 0.159 | 0.679 ± 0.157 |
| 500 | 500 | EntropyBalancing | 5.664 ± 2.372 | 0.881 ± 0.800 | 0.782 ± 0.110 | 0.794 ± 0.108 |
| 500 | 500 | EntropyBalancing | 2.688 ± 1.593 | 0.919 ± 0.675 | 0.861 ± 0.186 | 0.867 ± 0.180 |
| 500 | 500 | EntropyBalancing | 1.536 ± 0.658 | 0.710 ± 0.361 | 0.885 ± 0.045 | 0.895 ± 0.041 |
| 500 | 500 | EntropyBalancing | 3.014 ± 1.183 | 0.886 ± 0.446 | 0.690 ± 0.232 | 0.705 ± 0.225 |
| 500 | 500 | Glmtrans_Auto | 0.524 ± 0.056 | 0.026 ± 0.018 | 0.998 ± 0.001 | 0.999 ± 0.001 |
| 500 | 500 | Glmtrans_Auto | 0.453 ± 0.087 | 0.023 ± 0.011 | 0.996 ± 0.003 | 0.997 ± 0.002 |
| 500 | 500 | Glmtrans_Auto | 0.335 ± 0.123 | 0.036 ± 0.026 | 0.991 ± 0.009 | 0.991 ± 0.008 |
| 500 | 500 | Glmtrans_Auto | 0.283 ± 0.083 | 0.033 ± 0.016 | 0.998 ± 0.001 | 0.998 ± 0.001 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.445 ± 0.026 | 0.023 ± 0.012 | 0.998 ± 0.001 | 0.999 ± 0.000 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.413 ± 0.084 | 0.022 ± 0.014 | 0.997 ± 0.003 | 0.997 ± 0.002 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.323 ± 0.131 | 0.040 ± 0.029 | 0.991 ± 0.009 | 0.992 ± 0.009 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.264 ± 0.064 | 0.033 ± 0.021 | 0.998 ± 0.001 | 0.998 ± 0.001 |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 500 | 500 | IPWTransport | 5.366 ± 2.390 | 0.925 ± 0.821 | 0.803 ± 0.108 | 0.814 ± 0.105 |
| 500 | 500 | IPWTransport | 2.659 ± 1.556 | 0.914 ± 0.649 | 0.865 ± 0.179 | 0.872 ± 0.173 |
| 500 | 500 | IPWTransport | 1.537 ± 0.659 | 0.711 ± 0.361 | 0.886 ± 0.045 | 0.896 ± 0.040 |
| 500 | 500 | IPWTransport | 3.009 ± 1.174 | 0.888 ± 0.453 | 0.692 ± 0.229 | 0.707 ± 0.222 |
| 500 | 500 | OutcomeModelTransport | 4.881 ± 2.650 | 0.938 ± 0.806 | 0.833 ± 0.126 | 0.843 ± 0.123 |
| 500 | 500 | OutcomeModelTransport | 2.575 ± 1.456 | 0.945 ± 0.725 | 0.879 ± 0.154 | 0.886 ± 0.149 |
| 500 | 500 | OutcomeModelTransport | 1.520 ± 0.645 | 0.705 ± 0.356 | 0.896 ± 0.032 | 0.905 ± 0.028 |
| 500 | 500 | OutcomeModelTransport | 2.959 ± 1.103 | 0.880 ± 0.424 | 0.708 ± 0.207 | 0.723 ± 0.200 |
| 500 | 500 | ProxyOnly | 8.444 ± 1.647 | 1.964 ± 0.564 | 0.432 ± 0.061 | 0.443 ± 0.060 |
| 500 | 500 | ProxyOnly | 4.896 ± 0.795 | 0.459 ± 0.343 | 0.571 ± 0.061 | 0.589 ± 0.060 |
| 500 | 500 | ProxyOnly | 1.863 ± 0.431 | 0.456 ± 0.579 | 0.734 ± 0.134 | 0.747 ± 0.129 |
| 500 | 500 | ProxyOnly | 3.666 ± 0.935 | 0.681 ± 0.323 | 0.514 ± 0.160 | 0.532 ± 0.161 |
| 500 | 500 | TargetOnlyDR | 7.634 ± 1.405 | 0.394 ± 0.161 | 0.574 ± 0.056 | 0.592 ± 0.056 |
| 500 | 500 | TargetOnlyDR | 4.458 ± 0.807 | 0.215 ± 0.205 | 0.693 ± 0.034 | 0.707 ± 0.035 |
| 500 | 500 | TargetOnlyDR | 1.252 ± 0.337 | 0.045 ± 0.041 | 0.884 ± 0.033 | 0.893 ± 0.028 |
| 500 | 500 | TargetOnlyDR | 2.583 ± 0.484 | 0.190 ± 0.093 | 0.802 ± 0.008 | 0.818 ± 0.009 |

### Targeting / Ranking Metrics

| m0 | m1 | Method | Top-10% (↑) | Top-20% (↑) | Kendall (↑) |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 0.402 ± 0.197 | 0.402 ± 0.225 | 0.260 ± 0.030 |
| 50 | 50 | AnchorOnly | 0.419 ± 0.277 | 0.453 ± 0.241 | 0.333 ± 0.061 |
| 50 | 50 | AnchorOnly | 0.619 ± 0.189 | 0.618 ± 0.180 | 0.497 ± 0.038 |
| 50 | 50 | AnchorOnly | 0.813 ± 0.043 | 0.803 ± 0.047 | 0.598 ± 0.025 |
| 50 | 50 | AnchorPlugin | 0.531 ± 0.167 | 0.543 ± 0.185 | 0.373 ± 0.068 |
| 50 | 50 | AnchorPlugin | 0.619 ± 0.169 | 0.613 ± 0.161 | 0.443 ± 0.089 |
| 50 | 50 | AnchorPlugin | 0.717 ± 0.140 | 0.693 ± 0.175 | 0.552 ± 0.086 |
| 50 | 50 | AnchorPlugin | 0.800 ± 0.123 | 0.782 ± 0.143 | 0.592 ± 0.127 |
| 50 | 50 | EntropyBalancing | 0.765 ± 0.169 | 0.766 ± 0.201 | 0.596 ± 0.127 |
| 50 | 50 | EntropyBalancing | 0.834 ± 0.163 | 0.838 ± 0.169 | 0.671 ± 0.159 |
| 50 | 50 | EntropyBalancing | 0.705 ± 0.434 | 0.671 ± 0.501 | 0.609 ± 0.255 |
| 50 | 50 | EntropyBalancing | 0.823 ± 0.081 | 0.822 ± 0.098 | 0.612 ± 0.124 |
| 50 | 50 | Glmtrans_Auto | 0.878 ± 0.120 | 0.861 ± 0.149 | 0.723 ± 0.117 |
| 50 | 50 | Glmtrans_Auto | 0.943 ± 0.077 | 0.946 ± 0.071 | 0.823 ± 0.104 |
| 50 | 50 | Glmtrans_Auto | 0.984 ± 0.006 | 0.984 ± 0.006 | 0.897 ± 0.027 |
| 50 | 50 | Glmtrans_Auto | 0.970 ± 0.019 | 0.972 ± 0.016 | 0.850 ± 0.073 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.581 ± 0.248 | 0.558 ± 0.263 | 0.417 ± 0.097 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.902 ± 0.042 | 0.891 ± 0.054 | 0.726 ± 0.038 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.947 ± 0.040 | 0.931 ± 0.053 | 0.810 ± 0.064 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.956 ± 0.044 | 0.952 ± 0.051 | 0.829 ± 0.099 |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | IPWTransport | 0.810 ± 0.156 | 0.820 ± 0.140 | 0.649 ± 0.102 |
| 50 | 50 | IPWTransport | 0.852 ± 0.154 | 0.836 ± 0.184 | 0.680 ± 0.169 |
| 50 | 50 | IPWTransport | 0.723 ± 0.405 | 0.666 ± 0.499 | 0.602 ± 0.249 |
| 50 | 50 | IPWTransport | 0.816 ± 0.094 | 0.814 ± 0.107 | 0.602 ± 0.129 |
| 50 | 50 | OutcomeModelTransport | 0.806 ± 0.159 | 0.827 ± 0.137 | 0.653 ± 0.100 |
| 50 | 50 | OutcomeModelTransport | 0.845 ± 0.163 | 0.829 ± 0.190 | 0.677 ± 0.171 |
| 50 | 50 | OutcomeModelTransport | 0.723 ± 0.402 | 0.663 ± 0.501 | 0.601 ± 0.247 |
| 50 | 50 | OutcomeModelTransport | 0.814 ± 0.095 | 0.814 ± 0.110 | 0.602 ± 0.129 |
| 50 | 50 | ProxyOnly | 0.158 ± 0.122 | 0.173 ± 0.145 | 0.117 ± 0.031 |
| 50 | 50 | ProxyOnly | 0.347 ± 0.140 | 0.356 ± 0.158 | 0.251 ± 0.038 |
| 50 | 50 | ProxyOnly | 0.383 ± 0.204 | 0.348 ± 0.247 | 0.338 ± 0.068 |
| 50 | 50 | ProxyOnly | 0.529 ± 0.169 | 0.541 ± 0.223 | 0.398 ± 0.145 |
| 50 | 50 | TargetOnlyDR | 0.390 ± 0.154 | 0.362 ± 0.197 | 0.241 ± 0.068 |
| 50 | 50 | TargetOnlyDR | 0.430 ± 0.216 | 0.425 ± 0.233 | 0.306 ± 0.054 |
| 50 | 50 | TargetOnlyDR | 0.696 ± 0.078 | 0.678 ± 0.099 | 0.517 ± 0.048 |
| 50 | 50 | TargetOnlyDR | 0.775 ± 0.066 | 0.781 ± 0.037 | 0.559 ± 0.058 |
| 100 | 100 | AnchorOnly | 0.759 ± 0.106 | 0.769 ± 0.114 | 0.553 ± 0.075 |
| 100 | 100 | AnchorOnly | 0.547 ± 0.140 | 0.562 ± 0.118 | 0.395 ± 0.071 |
| 100 | 100 | AnchorOnly | 0.816 ± 0.141 | 0.838 ± 0.083 | 0.671 ± 0.052 |
| 100 | 100 | AnchorOnly | 0.514 ± 0.068 | 0.501 ± 0.099 | 0.280 ± 0.053 |
| 100 | 100 | AnchorPlugin | 0.806 ± 0.108 | 0.812 ± 0.092 | 0.598 ± 0.094 |
| 100 | 100 | AnchorPlugin | 0.670 ± 0.207 | 0.654 ± 0.213 | 0.501 ± 0.158 |
| 100 | 100 | AnchorPlugin | 0.739 ± 0.273 | 0.708 ± 0.370 | 0.610 ± 0.195 |
| 100 | 100 | AnchorPlugin | 0.693 ± 0.079 | 0.692 ± 0.095 | 0.462 ± 0.025 |
| 100 | 100 | EntropyBalancing | 0.813 ± 0.136 | 0.807 ± 0.144 | 0.600 ± 0.154 |
| 100 | 100 | EntropyBalancing | 0.771 ± 0.247 | 0.759 ± 0.244 | 0.593 ± 0.226 |
| 100 | 100 | EntropyBalancing | 0.737 ± 0.244 | 0.724 ± 0.264 | 0.618 ± 0.203 |
| 100 | 100 | EntropyBalancing | 0.856 ± 0.056 | 0.853 ± 0.055 | 0.650 ± 0.078 |
| 100 | 100 | Glmtrans_Auto | 0.993 ± 0.004 | 0.991 ± 0.004 | 0.913 ± 0.018 |
| 100 | 100 | Glmtrans_Auto | 0.992 ± 0.005 | 0.988 ± 0.007 | 0.924 ± 0.012 |
| 100 | 100 | Glmtrans_Auto | 0.989 ± 0.011 | 0.992 ± 0.006 | 0.928 ± 0.028 |
| 100 | 100 | Glmtrans_Auto | 0.985 ± 0.009 | 0.985 ± 0.010 | 0.884 ± 0.044 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.994 ± 0.003 | 0.990 ± 0.004 | 0.915 ± 0.022 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.962 ± 0.040 | 0.963 ± 0.030 | 0.855 ± 0.071 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.988 ± 0.012 | 0.990 ± 0.008 | 0.926 ± 0.036 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.924 ± 0.073 | 0.920 ± 0.081 | 0.744 ± 0.129 |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | IPWTransport | 0.817 ± 0.131 | 0.810 ± 0.142 | 0.600 ± 0.154 |
| 100 | 100 | IPWTransport | 0.802 ± 0.237 | 0.778 ± 0.242 | 0.619 ± 0.226 |
| 100 | 100 | IPWTransport | 0.739 ± 0.243 | 0.712 ± 0.290 | 0.612 ± 0.210 |
| 100 | 100 | IPWTransport | 0.899 ± 0.056 | 0.891 ± 0.062 | 0.710 ± 0.109 |
| 100 | 100 | OutcomeModelTransport | 0.819 ± 0.133 | 0.812 ± 0.139 | 0.601 ± 0.153 |
| 100 | 100 | OutcomeModelTransport | 0.805 ± 0.247 | 0.801 ± 0.239 | 0.644 ± 0.229 |
| 100 | 100 | OutcomeModelTransport | 0.734 ± 0.242 | 0.710 ± 0.293 | 0.610 ± 0.212 |
| 100 | 100 | OutcomeModelTransport | 0.909 ± 0.062 | 0.904 ± 0.063 | 0.726 ± 0.120 |
| 100 | 100 | ProxyOnly | 0.659 ± 0.091 | 0.665 ± 0.092 | 0.406 ± 0.077 |
| 100 | 100 | ProxyOnly | 0.369 ± 0.214 | 0.352 ± 0.260 | 0.292 ± 0.080 |
| 100 | 100 | ProxyOnly | 0.565 ± 0.445 | 0.519 ± 0.528 | 0.479 ± 0.210 |
| 100 | 100 | ProxyOnly | 0.332 ± 0.171 | 0.367 ± 0.135 | 0.205 ± 0.038 |
| 100 | 100 | TargetOnlyDR | 0.738 ± 0.111 | 0.770 ± 0.097 | 0.557 ± 0.088 |
| 100 | 100 | TargetOnlyDR | 0.553 ± 0.088 | 0.546 ± 0.113 | 0.396 ± 0.065 |
| 100 | 100 | TargetOnlyDR | 0.827 ± 0.057 | 0.852 ± 0.047 | 0.686 ± 0.064 |
| 100 | 100 | TargetOnlyDR | 0.504 ± 0.100 | 0.533 ± 0.109 | 0.317 ± 0.026 |
| 200 | 200 | AnchorOnly | 0.772 ± 0.127 | 0.760 ± 0.184 | 0.590 ± 0.044 |
| 200 | 200 | AnchorOnly | 0.643 ± 0.120 | 0.634 ± 0.115 | 0.469 ± 0.043 |
| 200 | 200 | AnchorOnly | 0.552 ± 0.068 | 0.536 ± 0.112 | 0.353 ± 0.055 |
| 200 | 200 | AnchorOnly | 0.883 ± 0.039 | 0.892 ± 0.042 | 0.689 ± 0.015 |
| 200 | 200 | AnchorPlugin | 0.810 ± 0.118 | 0.772 ± 0.177 | 0.630 ± 0.119 |
| 200 | 200 | AnchorPlugin | 0.774 ± 0.046 | 0.778 ± 0.049 | 0.594 ± 0.049 |
| 200 | 200 | AnchorPlugin | 0.688 ± 0.153 | 0.678 ± 0.152 | 0.457 ± 0.151 |
| 200 | 200 | AnchorPlugin | 0.838 ± 0.137 | 0.821 ± 0.151 | 0.612 ± 0.170 |
| 200 | 200 | EntropyBalancing | 0.858 ± 0.137 | 0.861 ± 0.137 | 0.694 ± 0.199 |
| 200 | 200 | EntropyBalancing | 0.901 ± 0.072 | 0.896 ± 0.072 | 0.734 ± 0.113 |
| 200 | 200 | EntropyBalancing | 0.785 ± 0.169 | 0.781 ± 0.165 | 0.570 ± 0.203 |
| 200 | 200 | EntropyBalancing | 0.823 ± 0.199 | 0.826 ± 0.192 | 0.623 ± 0.203 |
| 200 | 200 | Glmtrans_Auto | 0.993 ± 0.006 | 0.994 ± 0.006 | 0.940 ± 0.023 |
| 200 | 200 | Glmtrans_Auto | 0.993 ± 0.005 | 0.993 ± 0.004 | 0.934 ± 0.015 |
| 200 | 200 | Glmtrans_Auto | 0.995 ± 0.002 | 0.995 ± 0.002 | 0.940 ± 0.013 |
| 200 | 200 | Glmtrans_Auto | 0.989 ± 0.007 | 0.989 ± 0.007 | 0.911 ± 0.019 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.995 ± 0.005 | 0.994 ± 0.005 | 0.944 ± 0.018 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.992 ± 0.007 | 0.993 ± 0.005 | 0.935 ± 0.019 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.988 ± 0.005 | 0.991 ± 0.003 | 0.909 ± 0.010 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.989 ± 0.003 | 0.989 ± 0.005 | 0.909 ± 0.019 |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | IPWTransport | 0.861 ± 0.132 | 0.865 ± 0.136 | 0.696 ± 0.200 |
| 200 | 200 | IPWTransport | 0.909 ± 0.069 | 0.902 ± 0.073 | 0.749 ± 0.120 |
| 200 | 200 | IPWTransport | 0.807 ± 0.171 | 0.808 ± 0.173 | 0.604 ± 0.221 |
| 200 | 200 | IPWTransport | 0.823 ± 0.198 | 0.828 ± 0.190 | 0.621 ± 0.201 |
| 200 | 200 | OutcomeModelTransport | 0.861 ± 0.137 | 0.865 ± 0.135 | 0.698 ± 0.203 |
| 200 | 200 | OutcomeModelTransport | 0.909 ± 0.075 | 0.907 ± 0.077 | 0.765 ± 0.128 |
| 200 | 200 | OutcomeModelTransport | 0.816 ± 0.160 | 0.801 ± 0.187 | 0.612 ± 0.228 |
| 200 | 200 | OutcomeModelTransport | 0.822 ± 0.197 | 0.826 ± 0.191 | 0.620 ± 0.202 |
| 200 | 200 | ProxyOnly | 0.537 ± 0.306 | 0.491 ± 0.492 | 0.456 ± 0.070 |
| 200 | 200 | ProxyOnly | 0.530 ± 0.111 | 0.528 ± 0.108 | 0.374 ± 0.049 |
| 200 | 200 | ProxyOnly | 0.433 ± 0.048 | 0.436 ± 0.060 | 0.258 ± 0.056 |
| 200 | 200 | ProxyOnly | 0.727 ± 0.111 | 0.709 ± 0.110 | 0.472 ± 0.090 |
| 200 | 200 | TargetOnlyDR | 0.786 ± 0.135 | 0.735 ± 0.228 | 0.608 ± 0.032 |
| 200 | 200 | TargetOnlyDR | 0.669 ± 0.085 | 0.666 ± 0.079 | 0.486 ± 0.027 |
| 200 | 200 | TargetOnlyDR | 0.574 ± 0.058 | 0.555 ± 0.076 | 0.367 ± 0.024 |
| 200 | 200 | TargetOnlyDR | 0.905 ± 0.027 | 0.906 ± 0.024 | 0.696 ± 0.008 |
| 500 | 500 | AnchorOnly | 0.598 ± 0.111 | 0.588 ± 0.151 | 0.397 ± 0.031 |
| 500 | 500 | AnchorOnly | 0.648 ± 0.054 | 0.629 ± 0.078 | 0.485 ± 0.026 |
| 500 | 500 | AnchorOnly | 0.884 ± 0.022 | 0.891 ± 0.043 | 0.706 ± 0.035 |
| 500 | 500 | AnchorOnly | 0.794 ± 0.051 | 0.787 ± 0.086 | 0.606 ± 0.022 |
| 500 | 500 | AnchorPlugin | 0.707 ± 0.128 | 0.715 ± 0.124 | 0.511 ± 0.095 |
| 500 | 500 | AnchorPlugin | 0.784 ± 0.091 | 0.782 ± 0.091 | 0.586 ± 0.093 |
| 500 | 500 | AnchorPlugin | 0.889 ± 0.033 | 0.873 ± 0.039 | 0.685 ± 0.065 |
| 500 | 500 | AnchorPlugin | 0.672 ± 0.123 | 0.660 ± 0.135 | 0.487 ± 0.136 |
| 500 | 500 | EntropyBalancing | 0.779 ± 0.132 | 0.784 ± 0.119 | 0.593 ± 0.103 |
| 500 | 500 | EntropyBalancing | 0.851 ± 0.193 | 0.860 ± 0.184 | 0.715 ± 0.201 |
| 500 | 500 | EntropyBalancing | 0.896 ± 0.054 | 0.884 ± 0.064 | 0.711 ± 0.058 |
| 500 | 500 | EntropyBalancing | 0.725 ± 0.189 | 0.700 ± 0.165 | 0.524 ± 0.205 |
| 500 | 500 | Glmtrans_Auto | 0.999 ± 0.001 | 0.998 ± 0.001 | 0.966 ± 0.007 |
| 500 | 500 | Glmtrans_Auto | 0.997 ± 0.002 | 0.996 ± 0.002 | 0.955 ± 0.015 |
| 500 | 500 | Glmtrans_Auto | 0.993 ± 0.005 | 0.991 ± 0.006 | 0.929 ± 0.027 |
| 500 | 500 | Glmtrans_Auto | 0.998 ± 0.002 | 0.998 ± 0.001 | 0.962 ± 0.008 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.999 ± 0.000 | 0.998 ± 0.001 | 0.968 ± 0.007 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.996 ± 0.003 | 0.996 ± 0.005 | 0.956 ± 0.014 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.993 ± 0.005 | 0.992 ± 0.005 | 0.933 ± 0.030 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.998 ± 0.002 | 0.998 ± 0.001 | 0.964 ± 0.005 |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | IPWTransport | 0.808 ± 0.132 | 0.796 ± 0.113 | 0.616 ± 0.104 |
| 500 | 500 | IPWTransport | 0.855 ± 0.191 | 0.862 ± 0.180 | 0.719 ± 0.196 |
| 500 | 500 | IPWTransport | 0.896 ± 0.054 | 0.884 ± 0.064 | 0.712 ± 0.058 |
| 500 | 500 | IPWTransport | 0.728 ± 0.184 | 0.701 ± 0.163 | 0.525 ± 0.202 |
| 500 | 500 | OutcomeModelTransport | 0.841 ± 0.129 | 0.834 ± 0.140 | 0.655 ± 0.127 |
| 500 | 500 | OutcomeModelTransport | 0.871 ± 0.174 | 0.880 ± 0.152 | 0.733 ± 0.179 |
| 500 | 500 | OutcomeModelTransport | 0.904 ± 0.051 | 0.887 ± 0.080 | 0.725 ± 0.043 |
| 500 | 500 | OutcomeModelTransport | 0.737 ± 0.171 | 0.726 ± 0.143 | 0.537 ± 0.186 |
| 500 | 500 | ProxyOnly | 0.434 ± 0.143 | 0.412 ± 0.134 | 0.297 ± 0.043 |
| 500 | 500 | ProxyOnly | 0.584 ± 0.083 | 0.582 ± 0.081 | 0.402 ± 0.048 |
| 500 | 500 | ProxyOnly | 0.747 ± 0.103 | 0.744 ± 0.106 | 0.550 ± 0.129 |
| 500 | 500 | ProxyOnly | 0.535 ± 0.183 | 0.506 ± 0.235 | 0.362 ± 0.120 |
| 500 | 500 | TargetOnlyDR | 0.616 ± 0.084 | 0.573 ± 0.134 | 0.403 ± 0.045 |
| 500 | 500 | TargetOnlyDR | 0.680 ± 0.061 | 0.678 ± 0.078 | 0.502 ± 0.031 |
| 500 | 500 | TargetOnlyDR | 0.894 ± 0.013 | 0.891 ± 0.041 | 0.706 ± 0.043 |
| 500 | 500 | TargetOnlyDR | 0.808 ± 0.052 | 0.792 ± 0.068 | 0.610 ± 0.007 |

### ATE Estimation

| m0 | m1 | Method | ATE Est | ATE Err (↓) | ATE Bias |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 0.716 ± 2.917 | 0.716 ± 0.577 | 0.678 ± 0.631 |
| 50 | 50 | AnchorOnly | 0.166 ± 2.423 | 0.532 ± 0.331 | 0.102 ± 0.671 |
| 50 | 50 | AnchorOnly | -0.437 ± 0.939 | 0.426 ± 0.246 | 0.366 ± 0.346 |
| 50 | 50 | AnchorOnly | 0.403 ± 0.754 | 0.291 ± 0.210 | 0.291 ± 0.210 |
| 50 | 50 | AnchorPlugin | -0.192 ± 1.662 | 1.401 ± 0.707 | -0.229 ± 1.700 |
| 50 | 50 | AnchorPlugin | -0.032 ± 1.244 | 0.692 ± 0.769 | -0.095 ± 1.086 |
| 50 | 50 | AnchorPlugin | -0.680 ± 0.494 | 0.586 ± 0.363 | 0.123 ± 0.736 |
| 50 | 50 | AnchorPlugin | 0.184 ± 0.425 | 0.776 ± 0.460 | 0.072 ± 0.979 |
| 50 | 50 | EntropyBalancing | 0.114 ± 1.338 | 1.062 ± 1.355 | 0.076 ± 1.800 |
| 50 | 50 | EntropyBalancing | -0.088 ± 1.442 | 1.083 ± 0.837 | -0.152 ± 1.462 |
| 50 | 50 | EntropyBalancing | -0.239 ± 0.464 | 0.844 ± 1.041 | 0.564 ± 1.255 |
| 50 | 50 | EntropyBalancing | -0.472 ± 0.296 | 0.757 ± 0.789 | -0.584 ± 0.955 |
| 50 | 50 | Glmtrans_Auto | 0.087 ± 2.800 | 0.389 ± 0.397 | 0.050 ± 0.586 |
| 50 | 50 | Glmtrans_Auto | 0.171 ± 1.985 | 0.122 ± 0.145 | 0.107 ± 0.159 |
| 50 | 50 | Glmtrans_Auto | -0.796 ± 1.120 | 0.036 ± 0.017 | 0.007 ± 0.043 |
| 50 | 50 | Glmtrans_Auto | 0.184 ± 0.873 | 0.073 ± 0.060 | 0.073 ± 0.060 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.607 ± 3.236 | 0.886 ± 0.538 | 0.569 ± 0.929 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.142 ± 1.907 | 0.222 ± 0.187 | 0.078 ± 0.298 |
| 50 | 50 | Glmtrans_DR_CrossFit | -0.985 ± 0.873 | 0.324 ± 0.222 | -0.181 ± 0.373 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.199 ± 0.946 | 0.117 ± 0.120 | 0.087 ± 0.148 |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | IPWTransport | 0.193 ± 1.479 | 1.059 ± 1.188 | 0.156 ± 1.668 |
| 50 | 50 | IPWTransport | -0.087 ± 1.367 | 1.083 ± 0.827 | -0.151 ± 1.456 |
| 50 | 50 | IPWTransport | -0.275 ± 0.453 | 0.820 ± 1.008 | 0.528 ± 1.227 |
| 50 | 50 | IPWTransport | -0.474 ± 0.279 | 0.769 ± 0.776 | -0.585 ± 0.956 |
| 50 | 50 | OutcomeModelTransport | 0.206 ± 1.630 | 1.147 ± 1.133 | 0.169 ± 1.700 |
| 50 | 50 | OutcomeModelTransport | -0.140 ± 1.332 | 1.126 ± 0.803 | -0.204 ± 1.475 |
| 50 | 50 | OutcomeModelTransport | -0.236 ± 0.466 | 0.859 ± 1.043 | 0.568 ± 1.268 |
| 50 | 50 | OutcomeModelTransport | -0.480 ± 0.279 | 0.772 ± 0.776 | -0.592 ± 0.953 |
| 50 | 50 | ProxyOnly | -0.388 ± 3.464 | 1.832 ± 1.422 | -0.426 ± 2.448 |
| 50 | 50 | ProxyOnly | -0.038 ± 3.246 | 1.680 ± 1.203 | -0.102 ± 2.228 |
| 50 | 50 | ProxyOnly | -1.460 ± 1.283 | 0.757 ± 0.647 | -0.657 ± 0.772 |
| 50 | 50 | ProxyOnly | 0.803 ± 0.808 | 0.908 ± 0.831 | 0.691 ± 1.060 |
| 50 | 50 | TargetOnlyDR | 0.597 ± 3.422 | 1.016 ± 0.521 | 0.560 ± 1.082 |
| 50 | 50 | TargetOnlyDR | 0.176 ± 2.570 | 0.623 ± 0.437 | 0.113 ± 0.813 |
| 50 | 50 | TargetOnlyDR | -0.562 ± 1.089 | 0.242 ± 0.286 | 0.242 ± 0.286 |
| 50 | 50 | TargetOnlyDR | 0.386 ± 0.776 | 0.274 ± 0.112 | 0.274 ± 0.112 |
| 100 | 100 | AnchorOnly | 0.972 ± 0.627 | 0.302 ± 0.271 | 0.121 ± 0.412 |
| 100 | 100 | AnchorOnly | -0.202 ± 3.126 | 0.373 ± 0.245 | -0.270 ± 0.378 |
| 100 | 100 | AnchorOnly | -0.603 ± 1.069 | 0.096 ± 0.046 | 0.027 ± 0.112 |
| 100 | 100 | AnchorOnly | 1.596 ± 3.478 | 0.396 ± 0.302 | -0.266 ± 0.446 |
| 100 | 100 | AnchorPlugin | 0.620 ± 0.654 | 0.374 ± 0.210 | -0.231 ± 0.390 |
| 100 | 100 | AnchorPlugin | -0.414 ± 1.212 | 1.556 ± 0.877 | -0.482 ± 1.872 |
| 100 | 100 | AnchorPlugin | -0.385 ± 0.558 | 0.440 ± 0.400 | 0.245 ± 0.571 |
| 100 | 100 | AnchorPlugin | 0.656 ± 2.078 | 1.408 ± 2.021 | -1.205 ± 2.178 |
| 100 | 100 | EntropyBalancing | 0.315 ± 0.709 | 0.623 ± 0.329 | -0.537 ± 0.482 |
| 100 | 100 | EntropyBalancing | -0.792 ± 1.147 | 1.824 ± 1.529 | -0.860 ± 2.360 |
| 100 | 100 | EntropyBalancing | -0.277 ± 0.594 | 0.357 ± 0.407 | 0.353 ± 0.411 |
| 100 | 100 | EntropyBalancing | 1.110 ± 3.321 | 0.778 ± 0.640 | -0.752 ± 0.678 |
| 100 | 100 | Glmtrans_Auto | 0.884 ± 0.405 | 0.094 ± 0.047 | 0.032 ± 0.109 |
| 100 | 100 | Glmtrans_Auto | 0.069 ± 2.812 | 0.083 ± 0.084 | 0.001 ± 0.125 |
| 100 | 100 | Glmtrans_Auto | -0.628 ± 1.007 | 0.060 ± 0.053 | 0.002 ± 0.085 |
| 100 | 100 | Glmtrans_Auto | 1.898 ± 3.627 | 0.156 ± 0.101 | 0.036 ± 0.197 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.868 ± 0.385 | 0.080 ± 0.057 | 0.016 ± 0.104 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.058 ± 2.820 | 0.114 ± 0.135 | -0.010 ± 0.185 |
| 100 | 100 | Glmtrans_DR_CrossFit | -0.652 ± 0.980 | 0.056 ± 0.041 | -0.022 ± 0.071 |
| 100 | 100 | Glmtrans_DR_CrossFit | 1.759 ± 3.607 | 0.213 ± 0.153 | -0.103 ± 0.259 |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | IPWTransport | 0.304 ± 0.702 | 0.617 ± 0.345 | -0.547 ± 0.470 |
| 100 | 100 | IPWTransport | -0.891 ± 1.102 | 1.926 ± 1.653 | -0.959 ± 2.495 |
| 100 | 100 | IPWTransport | -0.272 ± 0.580 | 0.361 ± 0.422 | 0.358 ± 0.425 |
| 100 | 100 | IPWTransport | 1.194 ± 3.289 | 0.758 ± 0.616 | -0.668 ± 0.735 |
| 100 | 100 | OutcomeModelTransport | 0.308 ± 0.694 | 0.604 ± 0.345 | -0.544 ± 0.454 |
| 100 | 100 | OutcomeModelTransport | -0.734 ± 1.264 | 1.664 ± 1.324 | -0.802 ± 2.100 |
| 100 | 100 | OutcomeModelTransport | -0.296 ± 0.564 | 0.338 ± 0.424 | 0.334 ± 0.428 |
| 100 | 100 | OutcomeModelTransport | 1.215 ± 3.308 | 0.757 ± 0.620 | -0.647 ± 0.760 |
| 100 | 100 | ProxyOnly | 0.889 ± 1.027 | 0.545 ± 0.499 | 0.038 ± 0.787 |
| 100 | 100 | ProxyOnly | -0.379 ± 2.393 | 1.079 ± 1.031 | -0.447 ± 1.507 |
| 100 | 100 | ProxyOnly | -0.615 ± 0.871 | 0.386 ± 0.172 | 0.016 ± 0.464 |
| 100 | 100 | ProxyOnly | 1.457 ± 3.759 | 1.354 ± 0.626 | -0.405 ± 1.574 |
| 100 | 100 | TargetOnlyDR | 0.848 ± 0.669 | 0.311 ± 0.301 | -0.004 ± 0.460 |
| 100 | 100 | TargetOnlyDR | -0.067 ± 3.136 | 0.372 ± 0.170 | -0.135 ± 0.423 |
| 100 | 100 | TargetOnlyDR | -0.628 ± 1.086 | 0.101 ± 0.063 | 0.002 ± 0.130 |
| 100 | 100 | TargetOnlyDR | 1.662 ± 3.892 | 0.200 ± 0.185 | -0.200 ± 0.185 |
| 200 | 200 | AnchorOnly | -0.032 ± 1.645 | 0.142 ± 0.105 | -0.070 ± 0.174 |
| 200 | 200 | AnchorOnly | -0.446 ± 1.037 | 0.353 ± 0.110 | 0.266 ± 0.282 |
| 200 | 200 | AnchorOnly | 1.333 ± 2.049 | 0.295 ± 0.186 | -0.100 ± 0.362 |
| 200 | 200 | AnchorOnly | 0.641 ± 0.538 | 0.088 ± 0.043 | -0.046 ± 0.093 |
| 200 | 200 | AnchorPlugin | -0.146 ± 1.169 | 0.534 ± 0.443 | -0.184 ± 0.715 |
| 200 | 200 | AnchorPlugin | -0.562 ± 0.627 | 0.566 ± 0.273 | 0.149 ± 0.668 |
| 200 | 200 | AnchorPlugin | -0.402 ± 2.135 | 1.835 ± 0.827 | -1.835 ± 0.827 |
| 200 | 200 | AnchorPlugin | 0.224 ± 0.323 | 0.500 ± 0.448 | -0.463 ± 0.494 |
| 200 | 200 | EntropyBalancing | -0.112 ± 1.182 | 0.905 ± 0.624 | -0.149 ± 1.177 |
| 200 | 200 | EntropyBalancing | -0.818 ± 1.506 | 0.499 ± 0.365 | -0.107 ± 0.656 |
| 200 | 200 | EntropyBalancing | 0.944 ± 1.766 | 0.611 ± 0.693 | -0.489 ± 0.806 |
| 200 | 200 | EntropyBalancing | 0.156 ± 0.675 | 0.586 ± 0.317 | -0.531 ± 0.420 |
| 200 | 200 | Glmtrans_Auto | 0.047 ± 1.770 | 0.038 ± 0.026 | 0.010 ± 0.049 |
| 200 | 200 | Glmtrans_Auto | -0.666 ± 0.971 | 0.046 ± 0.042 | 0.046 ± 0.042 |
| 200 | 200 | Glmtrans_Auto | 1.465 ± 1.738 | 0.059 ± 0.027 | 0.032 ± 0.061 |
| 200 | 200 | Glmtrans_Auto | 0.698 ± 0.578 | 0.040 ± 0.023 | 0.011 ± 0.048 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.065 ± 1.788 | 0.037 ± 0.026 | 0.028 ± 0.036 |
| 200 | 200 | Glmtrans_DR_CrossFit | -0.663 ± 0.945 | 0.063 ± 0.046 | 0.048 ± 0.064 |
| 200 | 200 | Glmtrans_DR_CrossFit | 1.460 ± 1.671 | 0.099 ± 0.098 | 0.027 ± 0.144 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.691 ± 0.584 | 0.034 ± 0.022 | 0.004 ± 0.043 |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | IPWTransport | -0.103 ± 1.199 | 0.900 ± 0.628 | -0.140 ± 1.176 |
| 200 | 200 | IPWTransport | -0.821 ± 1.484 | 0.483 ± 0.340 | -0.110 ± 0.626 |
| 200 | 200 | IPWTransport | 0.966 ± 1.825 | 0.569 ± 0.783 | -0.466 ± 0.864 |
| 200 | 200 | IPWTransport | 0.155 ± 0.686 | 0.593 ± 0.306 | -0.532 ± 0.425 |
| 200 | 200 | OutcomeModelTransport | -0.108 ± 1.160 | 0.927 ± 0.640 | -0.145 ± 1.208 |
| 200 | 200 | OutcomeModelTransport | -0.765 ± 1.558 | 0.538 ± 0.351 | -0.053 ± 0.694 |
| 200 | 200 | OutcomeModelTransport | 0.717 ± 2.079 | 0.879 ± 0.657 | -0.716 ± 0.870 |
| 200 | 200 | OutcomeModelTransport | 0.182 ± 0.659 | 0.557 ± 0.325 | -0.505 ± 0.418 |
| 200 | 200 | ProxyOnly | -0.136 ± 1.514 | 0.547 ± 0.382 | -0.173 ± 0.695 |
| 200 | 200 | ProxyOnly | -1.052 ± 0.896 | 0.677 ± 0.833 | -0.340 ± 1.059 |
| 200 | 200 | ProxyOnly | -0.721 ± 3.631 | 2.400 ± 1.865 | -2.154 ± 2.208 |
| 200 | 200 | ProxyOnly | 0.229 ± 0.421 | 0.709 ± 0.580 | -0.458 ± 0.838 |
| 200 | 200 | TargetOnlyDR | -0.022 ± 1.713 | 0.131 ± 0.087 | -0.059 ± 0.158 |
| 200 | 200 | TargetOnlyDR | -0.573 ± 1.118 | 0.317 ± 0.133 | 0.138 ± 0.346 |
| 200 | 200 | TargetOnlyDR | 1.400 ± 1.960 | 0.234 ± 0.192 | -0.033 ± 0.322 |
| 200 | 200 | TargetOnlyDR | 0.648 ± 0.517 | 0.096 ± 0.046 | -0.039 ± 0.108 |
| 500 | 500 | AnchorOnly | -0.594 ± 2.358 | 0.368 ± 0.336 | -0.368 ± 0.336 |
| 500 | 500 | AnchorOnly | -0.686 ± 1.010 | 0.241 ± 0.207 | 0.110 ± 0.317 |
| 500 | 500 | AnchorOnly | 0.125 ± 1.308 | 0.035 ± 0.025 | 0.014 ± 0.043 |
| 500 | 500 | AnchorOnly | -0.065 ± 1.589 | 0.216 ± 0.134 | 0.047 ± 0.271 |
| 500 | 500 | AnchorPlugin | -0.274 ± 2.279 | 0.959 ± 0.428 | -0.048 ± 1.154 |
| 500 | 500 | AnchorPlugin | -0.636 ± 0.554 | 0.379 ± 0.313 | 0.160 ± 0.495 |
| 500 | 500 | AnchorPlugin | 0.258 ± 1.104 | 0.406 ± 0.179 | 0.148 ± 0.459 |
| 500 | 500 | AnchorPlugin | -0.133 ± 1.272 | 0.259 ± 0.164 | -0.021 ± 0.332 |
| 500 | 500 | EntropyBalancing | -0.237 ± 2.907 | 0.881 ± 0.800 | -0.011 ± 1.269 |
| 500 | 500 | EntropyBalancing | -0.152 ± 1.380 | 0.919 ± 0.675 | 0.645 ± 0.997 |
| 500 | 500 | EntropyBalancing | -0.037 ± 0.563 | 0.710 ± 0.361 | -0.148 ± 0.857 |
| 500 | 500 | EntropyBalancing | -0.102 ± 0.411 | 0.886 ± 0.446 | 0.011 ± 1.086 |
| 500 | 500 | Glmtrans_Auto | -0.209 ± 2.363 | 0.026 ± 0.018 | 0.017 ± 0.027 |
| 500 | 500 | Glmtrans_Auto | -0.801 ± 0.807 | 0.023 ± 0.011 | -0.004 ± 0.028 |
| 500 | 500 | Glmtrans_Auto | 0.117 ± 1.319 | 0.036 ± 0.026 | 0.006 ± 0.048 |
| 500 | 500 | Glmtrans_Auto | -0.113 ± 1.406 | 0.033 ± 0.016 | -0.000 ± 0.040 |
| 500 | 500 | Glmtrans_DR_CrossFit | -0.206 ± 2.362 | 0.023 ± 0.012 | 0.020 ± 0.017 |
| 500 | 500 | Glmtrans_DR_CrossFit | -0.805 ± 0.804 | 0.022 ± 0.014 | -0.009 ± 0.026 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.114 ± 1.325 | 0.040 ± 0.029 | 0.003 ± 0.053 |
| 500 | 500 | Glmtrans_DR_CrossFit | -0.116 ± 1.413 | 0.033 ± 0.021 | -0.003 ± 0.042 |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | IPWTransport | -0.232 ± 2.871 | 0.925 ± 0.821 | -0.006 ± 1.320 |
| 500 | 500 | IPWTransport | -0.175 ± 1.364 | 0.914 ± 0.649 | 0.621 ± 0.991 |
| 500 | 500 | IPWTransport | -0.038 ± 0.564 | 0.711 ± 0.361 | -0.149 ± 0.857 |
| 500 | 500 | IPWTransport | -0.100 ± 0.412 | 0.888 ± 0.453 | 0.013 ± 1.092 |
| 500 | 500 | OutcomeModelTransport | -0.268 ± 2.815 | 0.938 ± 0.806 | -0.042 ± 1.322 |
| 500 | 500 | OutcomeModelTransport | -0.068 ± 1.382 | 0.945 ± 0.725 | 0.729 ± 0.989 |
| 500 | 500 | OutcomeModelTransport | -0.032 ± 0.567 | 0.705 ± 0.356 | -0.143 ± 0.850 |
| 500 | 500 | OutcomeModelTransport | -0.109 ± 0.411 | 0.880 ± 0.424 | 0.003 ± 1.071 |
| 500 | 500 | ProxyOnly | -0.679 ± 3.536 | 1.964 ± 0.564 | -0.453 ± 2.210 |
| 500 | 500 | ProxyOnly | -0.988 ± 0.664 | 0.459 ± 0.343 | -0.192 ± 0.579 |
| 500 | 500 | ProxyOnly | 0.459 ± 1.727 | 0.456 ± 0.579 | 0.348 ± 0.666 |
| 500 | 500 | ProxyOnly | -0.167 ± 2.142 | 0.681 ± 0.323 | -0.055 ± 0.825 |
| 500 | 500 | TargetOnlyDR | -0.497 ± 2.525 | 0.394 ± 0.161 | -0.271 ± 0.357 |
| 500 | 500 | TargetOnlyDR | -0.696 ± 0.949 | 0.215 ± 0.205 | 0.100 ± 0.296 |
| 500 | 500 | TargetOnlyDR | 0.082 ± 1.326 | 0.045 ± 0.041 | -0.029 ± 0.056 |
| 500 | 500 | TargetOnlyDR | -0.126 ± 1.494 | 0.190 ± 0.093 | -0.013 ± 0.232 |

### Policy / Decision Metrics

| m0 | m1 | Method | Policy Value (↑) | Regret (↓) | Value Top20 (↑) | Regret Top20 (↓) |
|---|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 1.244 ± 1.264 | 2.093 ± 0.227 | 0.771 ± 1.340 | 1.397 ± 0.304 |
| 50 | 50 | AnchorOnly | 1.234 ± 0.829 | 1.182 ± 0.291 | 0.755 ± 0.947 | 0.821 ± 0.222 |
| 50 | 50 | AnchorOnly | 1.411 ± 0.553 | 0.410 ± 0.095 | 1.241 ± 0.465 | 0.308 ± 0.108 |
| 50 | 50 | AnchorOnly | 0.406 ± 0.528 | 0.174 ± 0.065 | 0.073 ± 0.461 | 0.133 ± 0.044 |
| 50 | 50 | AnchorPlugin | 1.753 ± 1.326 | 1.584 ± 0.385 | 1.092 ± 1.420 | 1.075 ± 0.318 |
| 50 | 50 | AnchorPlugin | 1.559 ± 0.642 | 0.857 ± 0.315 | 0.964 ± 0.824 | 0.612 ± 0.250 |
| 50 | 50 | AnchorPlugin | 1.442 ± 0.517 | 0.380 ± 0.207 | 1.296 ± 0.451 | 0.254 ± 0.123 |
| 50 | 50 | AnchorPlugin | 0.293 ± 0.594 | 0.287 ± 0.200 | 0.060 ± 0.425 | 0.146 ± 0.106 |
| 50 | 50 | EntropyBalancing | 2.569 ± 1.284 | 0.769 ± 0.486 | 1.642 ± 1.389 | 0.525 ± 0.367 |
| 50 | 50 | EntropyBalancing | 2.005 ± 0.626 | 0.412 ± 0.341 | 1.316 ± 0.851 | 0.260 ± 0.266 |
| 50 | 50 | EntropyBalancing | 1.369 ± 0.687 | 0.452 ± 0.616 | 1.288 ± 0.423 | 0.261 ± 0.363 |
| 50 | 50 | EntropyBalancing | 0.299 ± 0.508 | 0.281 ± 0.137 | 0.095 ± 0.440 | 0.111 ± 0.054 |
| 50 | 50 | Glmtrans_Auto | 2.966 ± 1.083 | 0.371 ± 0.311 | 1.861 ± 1.306 | 0.306 ± 0.267 |
| 50 | 50 | Glmtrans_Auto | 2.306 ± 0.824 | 0.111 ± 0.139 | 1.493 ± 1.002 | 0.083 ± 0.107 |
| 50 | 50 | Glmtrans_Auto | 1.804 ± 0.621 | 0.018 ± 0.008 | 1.536 ± 0.539 | 0.014 ± 0.005 |
| 50 | 50 | Glmtrans_Auto | 0.559 ± 0.545 | 0.021 ± 0.012 | 0.188 ± 0.467 | 0.018 ± 0.008 |
| 50 | 50 | Glmtrans_DR_CrossFit | 1.955 ± 0.869 | 1.382 ± 0.442 | 1.156 ± 1.172 | 1.011 ± 0.421 |
| 50 | 50 | Glmtrans_DR_CrossFit | 2.207 ± 0.834 | 0.209 ± 0.077 | 1.410 ± 1.016 | 0.166 ± 0.071 |
| 50 | 50 | Glmtrans_DR_CrossFit | 1.753 ± 0.609 | 0.069 ± 0.039 | 1.495 ± 0.522 | 0.055 ± 0.032 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.546 ± 0.561 | 0.034 ± 0.031 | 0.180 ± 0.473 | 0.026 ± 0.021 |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 50 | 50 | IPWTransport | 2.753 ± 1.145 | 0.584 ± 0.345 | 1.758 ± 1.383 | 0.409 ± 0.256 |
| 50 | 50 | IPWTransport | 2.007 ± 0.611 | 0.409 ± 0.353 | 1.313 ± 0.829 | 0.263 ± 0.290 |
| 50 | 50 | IPWTransport | 1.366 ± 0.667 | 0.455 ± 0.591 | 1.284 ± 0.420 | 0.266 ± 0.362 |
| 50 | 50 | IPWTransport | 0.292 ± 0.504 | 0.288 ± 0.132 | 0.090 ± 0.436 | 0.116 ± 0.059 |
| 50 | 50 | OutcomeModelTransport | 2.770 ± 1.132 | 0.567 ± 0.303 | 1.777 ± 1.352 | 0.390 ± 0.241 |
| 50 | 50 | OutcomeModelTransport | 2.011 ± 0.610 | 0.406 ± 0.342 | 1.302 ± 0.824 | 0.274 ± 0.299 |
| 50 | 50 | OutcomeModelTransport | 1.359 ± 0.668 | 0.462 ± 0.594 | 1.281 ± 0.420 | 0.268 ± 0.363 |
| 50 | 50 | OutcomeModelTransport | 0.291 ± 0.505 | 0.289 ± 0.132 | 0.090 ± 0.435 | 0.116 ± 0.060 |
| 50 | 50 | ProxyOnly | 0.507 ± 1.501 | 2.831 ± 0.604 | 0.185 ± 1.627 | 1.982 ± 0.330 |
| 50 | 50 | ProxyOnly | 0.767 ± 1.149 | 1.650 ± 0.569 | 0.566 ± 0.879 | 1.010 ± 0.196 |
| 50 | 50 | ProxyOnly | 1.109 ± 0.389 | 0.713 ± 0.271 | 1.024 ± 0.462 | 0.526 ± 0.122 |
| 50 | 50 | ProxyOnly | -0.032 ± 0.833 | 0.612 ± 0.458 | -0.112 ± 0.450 | 0.318 ± 0.164 |
| 50 | 50 | TargetOnlyDR | 1.146 ± 1.388 | 2.191 ± 0.376 | 0.663 ± 1.413 | 1.504 ± 0.286 |
| 50 | 50 | TargetOnlyDR | 1.230 ± 0.832 | 1.187 ± 0.243 | 0.708 ± 0.941 | 0.868 ± 0.198 |
| 50 | 50 | TargetOnlyDR | 1.423 ± 0.598 | 0.399 ± 0.042 | 1.289 ± 0.544 | 0.261 ± 0.026 |
| 50 | 50 | TargetOnlyDR | 0.389 ± 0.547 | 0.191 ± 0.043 | 0.061 ± 0.456 | 0.145 ± 0.031 |
| 100 | 100 | AnchorOnly | 1.235 ± 0.313 | 0.385 ± 0.127 | 0.553 ± 0.366 | 0.286 ± 0.114 |
| 100 | 100 | AnchorOnly | 1.805 ± 1.031 | 1.152 ± 0.389 | 1.219 ± 0.525 | 0.754 ± 0.307 |
| 100 | 100 | AnchorOnly | 1.075 ± 0.207 | 0.196 ± 0.108 | 0.906 ± 0.219 | 0.117 ± 0.056 |
| 100 | 100 | AnchorOnly | 2.401 ± 1.912 | 1.500 ± 0.418 | 0.824 ± 1.002 | 1.238 ± 0.158 |
| 100 | 100 | AnchorPlugin | 1.304 ± 0.353 | 0.317 ± 0.158 | 0.592 ± 0.494 | 0.246 ± 0.143 |
| 100 | 100 | AnchorPlugin | 2.073 ± 0.989 | 0.884 ± 0.683 | 1.347 ± 0.445 | 0.627 ± 0.541 |
| 100 | 100 | AnchorPlugin | 1.001 ± 0.314 | 0.269 ± 0.282 | 0.827 ± 0.187 | 0.197 ± 0.239 |
| 100 | 100 | AnchorPlugin | 2.856 ± 1.487 | 1.045 ± 0.278 | 1.313 ± 0.957 | 0.749 ± 0.113 |
| 100 | 100 | EntropyBalancing | 1.258 ± 0.454 | 0.362 ± 0.262 | 0.581 ± 0.556 | 0.257 ± 0.215 |
| 100 | 100 | EntropyBalancing | 2.091 ± 0.788 | 0.866 ± 0.886 | 1.464 ± 0.488 | 0.509 ± 0.594 |
| 100 | 100 | EntropyBalancing | 1.018 ± 0.310 | 0.252 ± 0.211 | 0.837 ± 0.213 | 0.186 ± 0.160 |
| 100 | 100 | EntropyBalancing | 3.460 ± 1.552 | 0.441 ± 0.130 | 1.690 ± 0.945 | 0.372 ± 0.167 |
| 100 | 100 | Glmtrans_Auto | 1.602 ± 0.242 | 0.019 ± 0.008 | 0.827 ± 0.400 | 0.011 ± 0.006 |
| 100 | 100 | Glmtrans_Auto | 2.942 ± 1.107 | 0.015 ± 0.003 | 1.955 ± 0.608 | 0.018 ± 0.006 |
| 100 | 100 | Glmtrans_Auto | 1.260 ± 0.247 | 0.010 ± 0.008 | 1.018 ± 0.264 | 0.006 ± 0.005 |
| 100 | 100 | Glmtrans_Auto | 3.850 ± 1.626 | 0.051 ± 0.033 | 2.021 ± 1.029 | 0.041 ± 0.037 |
| 100 | 100 | Glmtrans_DR_CrossFit | 1.603 ± 0.245 | 0.018 ± 0.008 | 0.825 ± 0.402 | 0.013 ± 0.006 |
| 100 | 100 | Glmtrans_DR_CrossFit | 2.864 ± 1.070 | 0.093 ± 0.126 | 1.910 ± 0.562 | 0.063 ± 0.069 |
| 100 | 100 | Glmtrans_DR_CrossFit | 1.261 ± 0.247 | 0.010 ± 0.008 | 1.016 ± 0.264 | 0.007 ± 0.007 |
| 100 | 100 | Glmtrans_DR_CrossFit | 3.622 ± 1.607 | 0.279 ± 0.262 | 1.863 ± 0.959 | 0.199 ± 0.186 |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 100 | 100 | IPWTransport | 1.267 ± 0.444 | 0.354 ± 0.252 | 0.585 ± 0.555 | 0.253 ± 0.212 |
| 100 | 100 | IPWTransport | 2.131 ± 0.808 | 0.826 ± 0.891 | 1.505 ± 0.462 | 0.468 ± 0.579 |
| 100 | 100 | IPWTransport | 1.002 ± 0.307 | 0.268 ± 0.222 | 0.831 ± 0.214 | 0.193 ± 0.177 |
| 100 | 100 | IPWTransport | 3.562 ± 1.538 | 0.338 ± 0.166 | 1.781 ± 0.938 | 0.281 ± 0.197 |
| 100 | 100 | OutcomeModelTransport | 1.266 ± 0.446 | 0.354 ± 0.253 | 0.588 ± 0.550 | 0.250 ± 0.208 |
| 100 | 100 | OutcomeModelTransport | 2.278 ± 0.945 | 0.679 ± 0.838 | 1.564 ± 0.422 | 0.409 ± 0.565 |
| 100 | 100 | OutcomeModelTransport | 0.993 ± 0.308 | 0.278 ± 0.232 | 0.830 ± 0.213 | 0.194 ± 0.179 |
| 100 | 100 | OutcomeModelTransport | 3.586 ± 1.540 | 0.315 ± 0.187 | 1.808 ± 0.956 | 0.254 ± 0.208 |
| 100 | 100 | ProxyOnly | 0.953 ± 0.266 | 0.668 ± 0.182 | 0.407 ± 0.444 | 0.432 ± 0.145 |
| 100 | 100 | ProxyOnly | 1.529 ± 1.039 | 1.428 ± 0.553 | 0.943 ± 0.568 | 1.031 ± 0.297 |
| 100 | 100 | ProxyOnly | 0.836 ± 0.328 | 0.435 ± 0.292 | 0.690 ± 0.234 | 0.333 ± 0.339 |
| 100 | 100 | ProxyOnly | 2.139 ± 2.082 | 1.762 ± 0.680 | 0.503 ± 1.063 | 1.559 ± 0.096 |
| 100 | 100 | TargetOnlyDR | 1.240 ± 0.292 | 0.381 ± 0.117 | 0.550 ± 0.394 | 0.289 ± 0.107 |
| 100 | 100 | TargetOnlyDR | 1.820 ± 0.993 | 1.137 ± 0.420 | 1.221 ± 0.511 | 0.753 ± 0.196 |
| 100 | 100 | TargetOnlyDR | 1.102 ± 0.200 | 0.169 ± 0.090 | 0.915 ± 0.245 | 0.108 ± 0.039 |
| 100 | 100 | TargetOnlyDR | 2.416 ± 1.914 | 1.485 ± 0.362 | 0.915 ± 0.990 | 1.147 ± 0.095 |
| 200 | 200 | AnchorOnly | 1.357 ± 0.573 | 0.277 ± 0.090 | 0.850 ± 0.514 | 0.182 ± 0.034 |
| 200 | 200 | AnchorOnly | 1.593 ± 0.616 | 0.796 ± 0.151 | 1.366 ± 0.605 | 0.509 ± 0.133 |
| 200 | 200 | AnchorOnly | 2.992 ± 1.328 | 1.837 ± 0.540 | 1.936 ± 1.582 | 1.298 ± 0.387 |
| 200 | 200 | AnchorOnly | 1.122 ± 0.672 | 0.122 ± 0.058 | 0.592 ± 0.415 | 0.089 ± 0.054 |
| 200 | 200 | AnchorPlugin | 1.386 ± 0.505 | 0.248 ± 0.174 | 0.826 ± 0.522 | 0.206 ± 0.194 |
| 200 | 200 | AnchorPlugin | 1.929 ± 0.621 | 0.460 ± 0.155 | 1.541 ± 0.670 | 0.334 ± 0.162 |
| 200 | 200 | AnchorPlugin | 3.339 ± 1.481 | 1.490 ± 0.861 | 2.222 ± 1.969 | 1.013 ± 0.737 |
| 200 | 200 | AnchorPlugin | 0.984 ± 0.582 | 0.261 ± 0.306 | 0.511 ± 0.387 | 0.170 ± 0.211 |
| 200 | 200 | EntropyBalancing | 1.350 ± 0.465 | 0.284 ± 0.271 | 0.846 ± 0.574 | 0.185 ± 0.280 |
| 200 | 200 | EntropyBalancing | 2.144 ± 0.670 | 0.245 ± 0.206 | 1.712 ± 0.671 | 0.163 ± 0.138 |
| 200 | 200 | EntropyBalancing | 3.883 ± 1.633 | 0.946 ± 0.851 | 2.513 ± 2.082 | 0.722 ± 0.695 |
| 200 | 200 | EntropyBalancing | 0.963 ± 0.564 | 0.282 ± 0.350 | 0.490 ± 0.363 | 0.190 ± 0.266 |
| 200 | 200 | Glmtrans_Auto | 1.628 ± 0.629 | 0.006 ± 0.003 | 1.027 ± 0.507 | 0.005 ± 0.003 |
| 200 | 200 | Glmtrans_Auto | 2.377 ± 0.572 | 0.012 ± 0.003 | 1.865 ± 0.550 | 0.010 ± 0.005 |
| 200 | 200 | Glmtrans_Auto | 4.814 ± 0.906 | 0.015 ± 0.006 | 3.221 ± 1.406 | 0.014 ± 0.005 |
| 200 | 200 | Glmtrans_Auto | 1.234 ± 0.723 | 0.011 ± 0.006 | 0.672 ± 0.460 | 0.008 ± 0.005 |
| 200 | 200 | Glmtrans_DR_CrossFit | 1.629 ± 0.629 | 0.005 ± 0.003 | 1.027 ± 0.508 | 0.004 ± 0.003 |
| 200 | 200 | Glmtrans_DR_CrossFit | 2.376 ± 0.568 | 0.013 ± 0.009 | 1.865 ± 0.548 | 0.010 ± 0.007 |
| 200 | 200 | Glmtrans_DR_CrossFit | 4.791 ± 0.915 | 0.038 ± 0.015 | 3.210 ± 1.412 | 0.024 ± 0.009 |
| 200 | 200 | Glmtrans_DR_CrossFit | 1.234 ± 0.723 | 0.010 ± 0.005 | 0.672 ± 0.460 | 0.009 ± 0.005 |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 200 | 200 | IPWTransport | 1.352 ± 0.470 | 0.282 ± 0.266 | 0.850 ± 0.575 | 0.182 ± 0.277 |
| 200 | 200 | IPWTransport | 2.161 ± 0.669 | 0.228 ± 0.214 | 1.719 ± 0.675 | 0.156 ± 0.144 |
| 200 | 200 | IPWTransport | 3.952 ± 1.621 | 0.877 ± 0.851 | 2.580 ± 2.078 | 0.654 ± 0.700 |
| 200 | 200 | IPWTransport | 0.963 ± 0.563 | 0.281 ± 0.348 | 0.492 ± 0.362 | 0.189 ± 0.264 |
| 200 | 200 | OutcomeModelTransport | 1.350 ± 0.475 | 0.284 ± 0.261 | 0.851 ± 0.576 | 0.181 ± 0.275 |
| 200 | 200 | OutcomeModelTransport | 2.170 ± 0.666 | 0.219 ± 0.219 | 1.722 ± 0.683 | 0.153 ± 0.159 |
| 200 | 200 | OutcomeModelTransport | 3.938 ± 1.608 | 0.891 ± 0.860 | 2.549 ± 2.108 | 0.685 ± 0.751 |
| 200 | 200 | OutcomeModelTransport | 0.971 ± 0.567 | 0.274 ± 0.341 | 0.491 ± 0.363 | 0.190 ± 0.265 |
| 200 | 200 | ProxyOnly | 1.183 ± 0.616 | 0.451 ± 0.126 | 0.668 ± 0.493 | 0.364 ± 0.120 |
| 200 | 200 | ProxyOnly | 1.228 ± 0.411 | 1.161 ± 0.318 | 1.201 ± 0.676 | 0.674 ± 0.179 |
| 200 | 200 | ProxyOnly | 2.048 ± 0.756 | 2.781 ± 0.202 | 1.613 ± 1.868 | 1.621 ± 0.529 |
| 200 | 200 | ProxyOnly | 0.812 ± 0.509 | 0.433 ± 0.342 | 0.418 ± 0.290 | 0.262 ± 0.196 |
| 200 | 200 | TargetOnlyDR | 1.386 ± 0.586 | 0.248 ± 0.058 | 0.841 ± 0.501 | 0.191 ± 0.022 |
| 200 | 200 | TargetOnlyDR | 1.654 ± 0.630 | 0.735 ± 0.200 | 1.408 ± 0.557 | 0.468 ± 0.099 |
| 200 | 200 | TargetOnlyDR | 3.087 ± 1.204 | 1.742 ± 0.360 | 1.991 ± 1.530 | 1.243 ± 0.287 |
| 200 | 200 | TargetOnlyDR | 1.131 ± 0.672 | 0.114 ± 0.059 | 0.604 ± 0.430 | 0.076 ± 0.035 |
| 500 | 500 | AnchorOnly | 2.438 ± 1.088 | 1.527 ± 0.351 | 1.884 ± 1.093 | 0.943 ± 0.133 |
| 500 | 500 | AnchorOnly | 1.884 ± 0.509 | 0.720 ± 0.202 | 1.563 ± 0.535 | 0.530 ± 0.134 |
| 500 | 500 | AnchorOnly | 0.802 ± 0.753 | 0.095 ± 0.039 | 0.400 ± 0.885 | 0.073 ± 0.025 |
| 500 | 500 | AnchorOnly | 1.626 ± 0.506 | 0.318 ± 0.076 | 1.187 ± 0.810 | 0.215 ± 0.031 |
| 500 | 500 | AnchorPlugin | 2.881 ± 1.150 | 1.084 ± 0.703 | 2.114 ± 1.262 | 0.713 ± 0.460 |
| 500 | 500 | AnchorPlugin | 2.110 ± 0.482 | 0.494 ± 0.224 | 1.773 ± 0.539 | 0.320 ± 0.159 |
| 500 | 500 | AnchorPlugin | 0.778 ± 0.771 | 0.120 ± 0.057 | 0.385 ± 0.898 | 0.088 ± 0.030 |
| 500 | 500 | AnchorPlugin | 1.403 ± 0.669 | 0.541 ± 0.343 | 1.020 ± 0.950 | 0.382 ± 0.224 |
| 500 | 500 | EntropyBalancing | 3.181 ± 1.071 | 0.784 ± 0.620 | 2.274 ± 1.249 | 0.553 ± 0.435 |
| 500 | 500 | EntropyBalancing | 2.283 ± 0.540 | 0.321 ± 0.389 | 1.888 ± 0.510 | 0.206 ± 0.273 |
| 500 | 500 | EntropyBalancing | 0.750 ± 0.710 | 0.148 ± 0.097 | 0.395 ± 0.875 | 0.078 ± 0.039 |
| 500 | 500 | EntropyBalancing | 1.378 ± 0.782 | 0.566 ± 0.429 | 1.037 ± 1.045 | 0.365 ± 0.285 |
| 500 | 500 | Glmtrans_Auto | 3.960 ± 0.885 | 0.005 ± 0.002 | 2.823 ± 1.132 | 0.004 ± 0.002 |
| 500 | 500 | Glmtrans_Auto | 2.595 ± 0.573 | 0.009 ± 0.005 | 2.088 ± 0.542 | 0.005 ± 0.003 |
| 500 | 500 | Glmtrans_Auto | 0.890 ± 0.763 | 0.008 ± 0.007 | 0.467 ± 0.895 | 0.006 ± 0.004 |
| 500 | 500 | Glmtrans_Auto | 1.940 ± 0.500 | 0.004 ± 0.001 | 1.400 ± 0.811 | 0.002 ± 0.001 |
| 500 | 500 | Glmtrans_DR_CrossFit | 3.960 ± 0.886 | 0.004 ± 0.002 | 2.823 ± 1.132 | 0.004 ± 0.002 |
| 500 | 500 | Glmtrans_DR_CrossFit | 2.597 ± 0.572 | 0.007 ± 0.005 | 2.089 ± 0.541 | 0.005 ± 0.005 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.891 ± 0.764 | 0.007 ± 0.007 | 0.468 ± 0.896 | 0.006 ± 0.005 |
| 500 | 500 | Glmtrans_DR_CrossFit | 1.941 ± 0.500 | 0.003 ± 0.001 | 1.400 ± 0.811 | 0.002 ± 0.001 |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A |
| 500 | 500 | IPWTransport | 3.263 ± 1.070 | 0.702 ± 0.555 | 2.301 ± 1.269 | 0.526 ± 0.419 |
| 500 | 500 | IPWTransport | 2.290 ± 0.536 | 0.314 ± 0.386 | 1.890 ± 0.510 | 0.203 ± 0.267 |
| 500 | 500 | IPWTransport | 0.749 ± 0.710 | 0.149 ± 0.098 | 0.396 ± 0.875 | 0.078 ± 0.038 |
| 500 | 500 | IPWTransport | 1.379 ± 0.782 | 0.565 ± 0.429 | 1.039 ± 1.040 | 0.363 ± 0.280 |
| 500 | 500 | OutcomeModelTransport | 3.339 ± 1.104 | 0.625 ± 0.645 | 2.383 ± 1.287 | 0.444 ± 0.485 |
| 500 | 500 | OutcomeModelTransport | 2.302 ± 0.523 | 0.302 ± 0.367 | 1.916 ± 0.502 | 0.178 ± 0.225 |
| 500 | 500 | OutcomeModelTransport | 0.760 ± 0.725 | 0.138 ± 0.079 | 0.403 ± 0.877 | 0.070 ± 0.030 |
| 500 | 500 | OutcomeModelTransport | 1.416 ± 0.743 | 0.528 ± 0.377 | 1.075 ± 1.007 | 0.327 ± 0.242 |
| 500 | 500 | ProxyOnly | 1.656 ± 1.299 | 2.309 ± 0.642 | 1.407 ± 1.260 | 1.419 ± 0.476 |
| 500 | 500 | ProxyOnly | 1.680 ± 0.380 | 0.924 ± 0.248 | 1.508 ± 0.499 | 0.585 ± 0.086 |
| 500 | 500 | ProxyOnly | 0.627 ± 0.820 | 0.271 ± 0.146 | 0.291 ± 0.894 | 0.182 ± 0.090 |
| 500 | 500 | ProxyOnly | 1.177 ± 0.619 | 0.767 ± 0.360 | 0.866 ± 0.947 | 0.536 ± 0.305 |
| 500 | 500 | TargetOnlyDR | 2.483 ± 1.096 | 1.482 ± 0.357 | 1.831 ± 1.150 | 0.996 ± 0.199 |
| 500 | 500 | TargetOnlyDR | 1.919 ± 0.556 | 0.685 ± 0.208 | 1.632 ± 0.573 | 0.461 ± 0.121 |
| 500 | 500 | TargetOnlyDR | 0.803 ± 0.755 | 0.095 ± 0.041 | 0.400 ± 0.888 | 0.073 ± 0.023 |
| 500 | 500 | TargetOnlyDR | 1.633 ± 0.495 | 0.311 ± 0.096 | 1.189 ± 0.826 | 0.213 ± 0.028 |

### Calibration Metrics

| m0 | m1 | Method | Slope (→1) | Intercept (→0) | R² (↑) | ECE (↓) | MCE (↓) |
|---|---|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 1.374 ± 0.268 | -1.272 ± 1.709 | 0.154 ± 0.032 | 1.262 ± 0.520 | 2.450 ± 0.620 |
| 50 | 50 | AnchorOnly | 1.200 ± 0.124 | -0.308 ± 1.170 | 0.240 ± 0.087 | 0.909 ± 0.144 | 2.158 ± 0.137 |
| 50 | 50 | AnchorOnly | 1.300 ± 0.116 | -0.305 ± 0.364 | 0.470 ± 0.055 | 0.718 ± 0.302 | 1.844 ± 0.467 |
| 50 | 50 | AnchorOnly | 1.133 ± 0.253 | -0.219 ± 0.219 | 0.625 ± 0.043 | 0.431 ± 0.271 | 0.893 ± 0.638 |
| 50 | 50 | AnchorPlugin | 1.445 ± 0.508 | -0.150 ± 2.068 | 0.305 ± 0.098 | 1.983 ± 0.520 | 4.106 ± 1.484 |
| 50 | 50 | AnchorPlugin | 1.105 ± 0.340 | 0.094 ± 1.069 | 0.412 ± 0.131 | 1.043 ± 0.598 | 2.205 ± 1.321 |
| 50 | 50 | AnchorPlugin | 1.046 ± 0.149 | -0.150 ± 0.858 | 0.580 ± 0.134 | 0.637 ± 0.351 | 1.292 ± 0.534 |
| 50 | 50 | AnchorPlugin | 1.017 ± 0.289 | -0.132 ± 1.035 | 0.625 ± 0.171 | 0.799 ± 0.444 | 1.534 ± 0.862 |
| 50 | 50 | EntropyBalancing | 0.907 ± 0.093 | -0.085 ± 1.800 | 0.638 ± 0.184 | 1.493 ± 0.990 | 2.864 ± 1.390 |
| 50 | 50 | EntropyBalancing | 0.935 ± 0.114 | 0.137 ± 1.459 | 0.733 ± 0.219 | 1.258 ± 0.665 | 1.945 ± 1.030 |
| 50 | 50 | EntropyBalancing | 0.876 ± 0.322 | -0.568 ± 1.237 | 0.659 ± 0.344 | 1.022 ± 1.250 | 2.244 ± 3.272 |
| 50 | 50 | EntropyBalancing | 0.980 ± 0.249 | 0.599 ± 0.870 | 0.652 ± 0.166 | 0.871 ± 0.696 | 1.309 ± 0.765 |
| 50 | 50 | Glmtrans_Auto | 1.057 ± 0.024 | -0.033 ± 0.739 | 0.803 ± 0.147 | 0.559 ± 0.321 | 1.376 ± 0.772 |
| 50 | 50 | Glmtrans_Auto | 1.027 ± 0.025 | -0.092 ± 0.185 | 0.908 ± 0.105 | 0.221 ± 0.119 | 0.432 ± 0.096 |
| 50 | 50 | Glmtrans_Auto | 1.027 ± 0.040 | 0.005 ± 0.045 | 0.971 ± 0.015 | 0.097 ± 0.079 | 0.226 ± 0.182 |
| 50 | 50 | Glmtrans_Auto | 1.088 ± 0.097 | -0.036 ± 0.113 | 0.934 ± 0.063 | 0.201 ± 0.100 | 0.460 ± 0.232 |
| 50 | 50 | Glmtrans_DR_CrossFit | 1.021 ± 0.367 | -0.481 ± 1.653 | 0.376 ± 0.146 | 1.702 ± 0.836 | 3.783 ± 2.285 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.951 ± 0.072 | -0.121 ± 0.269 | 0.824 ± 0.046 | 0.454 ± 0.249 | 1.032 ± 0.521 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.927 ± 0.069 | 0.095 ± 0.389 | 0.905 ± 0.061 | 0.396 ± 0.288 | 0.905 ± 0.679 |
| 50 | 50 | Glmtrans_DR_CrossFit | 1.059 ± 0.048 | -0.079 ± 0.180 | 0.909 ± 0.091 | 0.178 ± 0.085 | 0.360 ± 0.130 |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 50 | 50 | IPWTransport | 1.010 ± 0.062 | -0.163 ± 1.662 | 0.717 ± 0.145 | 1.269 ± 0.987 | 2.001 ± 1.019 |
| 50 | 50 | IPWTransport | 0.947 ± 0.128 | 0.136 ± 1.471 | 0.742 ± 0.229 | 1.277 ± 0.669 | 1.956 ± 0.899 |
| 50 | 50 | IPWTransport | 0.863 ± 0.312 | -0.552 ± 1.228 | 0.650 ± 0.340 | 1.016 ± 1.211 | 2.238 ± 3.027 |
| 50 | 50 | IPWTransport | 0.966 ± 0.265 | 0.592 ± 0.868 | 0.638 ± 0.177 | 0.896 ± 0.670 | 1.361 ± 0.782 |
| 50 | 50 | OutcomeModelTransport | 1.011 ± 0.060 | -0.186 ± 1.699 | 0.722 ± 0.142 | 1.306 ± 0.982 | 2.092 ± 1.039 |
| 50 | 50 | OutcomeModelTransport | 0.946 ± 0.132 | 0.192 ± 1.503 | 0.738 ± 0.231 | 1.305 ± 0.651 | 1.989 ± 0.932 |
| 50 | 50 | OutcomeModelTransport | 0.861 ± 0.311 | -0.578 ± 1.236 | 0.648 ± 0.338 | 1.049 ± 1.242 | 2.274 ± 3.057 |
| 50 | 50 | OutcomeModelTransport | 0.964 ± 0.266 | 0.597 ± 0.866 | 0.637 ± 0.178 | 0.899 ± 0.671 | 1.368 ± 0.778 |
| 50 | 50 | ProxyOnly | 0.746 ± 0.282 | 0.769 ± 2.011 | 0.033 ± 0.017 | 2.082 ± 1.178 | 3.805 ± 1.191 |
| 50 | 50 | ProxyOnly | 1.173 ± 0.426 | 0.203 ± 2.876 | 0.147 ± 0.043 | 1.742 ± 1.140 | 2.796 ± 1.239 |
| 50 | 50 | ProxyOnly | 1.022 ± 0.279 | 0.650 ± 1.023 | 0.249 ± 0.088 | 0.838 ± 0.615 | 2.051 ± 1.472 |
| 50 | 50 | ProxyOnly | 0.999 ± 0.410 | -0.769 ± 1.388 | 0.316 ± 0.190 | 1.047 ± 0.689 | 2.015 ± 1.084 |
| 50 | 50 | TargetOnlyDR | 1.235 ± 0.438 | -0.529 ± 2.272 | 0.136 ± 0.077 | 1.503 ± 0.434 | 2.876 ± 0.746 |
| 50 | 50 | TargetOnlyDR | 1.067 ± 0.162 | -0.425 ± 1.038 | 0.216 ± 0.069 | 0.820 ± 0.259 | 1.639 ± 0.522 |
| 50 | 50 | TargetOnlyDR | 1.413 ± 0.244 | 0.178 ± 0.934 | 0.516 ± 0.071 | 0.782 ± 0.372 | 1.821 ± 0.881 |
| 50 | 50 | TargetOnlyDR | 1.135 ± 0.256 | -0.210 ± 0.233 | 0.559 ± 0.091 | 0.434 ± 0.151 | 1.077 ± 0.413 |
| 100 | 100 | AnchorOnly | 1.588 ± 0.274 | -0.691 ± 0.772 | 0.565 ± 0.121 | 1.022 ± 0.314 | 2.613 ± 0.690 |
| 100 | 100 | AnchorOnly | 1.632 ± 0.553 | 1.244 ± 3.392 | 0.325 ± 0.104 | 1.202 ± 0.408 | 3.290 ± 1.404 |
| 100 | 100 | AnchorOnly | 1.234 ± 0.094 | 0.153 ± 0.425 | 0.726 ± 0.066 | 0.526 ± 0.269 | 1.174 ± 0.532 |
| 100 | 100 | AnchorOnly | 1.492 ± 0.414 | 0.330 ± 1.422 | 0.180 ± 0.069 | 1.248 ± 0.553 | 3.183 ± 1.028 |
| 100 | 100 | AnchorPlugin | 1.030 ± 0.073 | 0.223 ± 0.363 | 0.645 ± 0.140 | 0.440 ± 0.118 | 0.892 ± 0.163 |
| 100 | 100 | AnchorPlugin | 1.064 ± 0.207 | 0.456 ± 1.655 | 0.506 ± 0.230 | 1.670 ± 0.707 | 2.876 ± 1.357 |
| 100 | 100 | AnchorPlugin | 1.068 ± 0.294 | -0.335 ± 0.672 | 0.649 ± 0.270 | 0.644 ± 0.378 | 1.402 ± 0.764 |
| 100 | 100 | AnchorPlugin | 1.140 ± 0.147 | 1.312 ± 1.990 | 0.442 ± 0.038 | 1.744 ± 1.828 | 2.782 ± 1.774 |
| 100 | 100 | EntropyBalancing | 0.932 ± 0.130 | 0.596 ± 0.462 | 0.647 ± 0.225 | 0.740 ± 0.297 | 1.198 ± 0.331 |
| 100 | 100 | EntropyBalancing | 0.882 ± 0.146 | 0.699 ± 2.294 | 0.636 ± 0.312 | 1.925 ± 1.480 | 2.864 ± 1.961 |
| 100 | 100 | EntropyBalancing | 1.096 ± 0.460 | -0.430 ± 0.493 | 0.650 ± 0.263 | 0.767 ± 0.302 | 1.781 ± 0.610 |
| 100 | 100 | EntropyBalancing | 0.925 ± 0.072 | 0.848 ± 0.884 | 0.724 ± 0.102 | 0.993 ± 0.493 | 1.923 ± 0.746 |
| 100 | 100 | Glmtrans_Auto | 1.042 ± 0.032 | -0.077 ± 0.132 | 0.979 ± 0.008 | 0.163 ± 0.068 | 0.387 ± 0.220 |
| 100 | 100 | Glmtrans_Auto | 1.030 ± 0.017 | -0.017 ± 0.191 | 0.985 ± 0.004 | 0.202 ± 0.061 | 0.466 ± 0.111 |
| 100 | 100 | Glmtrans_Auto | 1.014 ± 0.057 | 0.024 ± 0.125 | 0.982 ± 0.016 | 0.131 ± 0.077 | 0.322 ± 0.192 |
| 100 | 100 | Glmtrans_Auto | 1.009 ± 0.014 | -0.040 ± 0.207 | 0.965 ± 0.026 | 0.190 ± 0.077 | 0.416 ± 0.177 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.986 ± 0.020 | -0.006 ± 0.099 | 0.980 ± 0.009 | 0.122 ± 0.033 | 0.248 ± 0.035 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.957 ± 0.031 | -0.002 ± 0.137 | 0.939 ± 0.061 | 0.292 ± 0.158 | 0.666 ± 0.399 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.985 ± 0.034 | 0.019 ± 0.071 | 0.980 ± 0.019 | 0.083 ± 0.048 | 0.159 ± 0.127 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.969 ± 0.070 | 0.266 ± 0.661 | 0.831 ± 0.147 | 0.453 ± 0.392 | 1.099 ± 0.781 |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 100 | 100 | IPWTransport | 0.936 ± 0.128 | 0.601 ± 0.459 | 0.647 ± 0.223 | 0.737 ± 0.308 | 1.160 ± 0.385 |
| 100 | 100 | IPWTransport | 0.918 ± 0.149 | 0.812 ± 2.432 | 0.669 ± 0.309 | 1.991 ± 1.624 | 2.863 ± 2.133 |
| 100 | 100 | IPWTransport | 1.077 ± 0.457 | -0.435 ± 0.513 | 0.641 ± 0.273 | 0.743 ± 0.296 | 1.696 ± 0.550 |
| 100 | 100 | IPWTransport | 0.992 ± 0.048 | 0.722 ± 0.810 | 0.795 ± 0.121 | 0.831 ± 0.532 | 1.484 ± 0.616 |
| 100 | 100 | OutcomeModelTransport | 0.939 ± 0.128 | 0.595 ± 0.447 | 0.648 ± 0.222 | 0.727 ± 0.301 | 1.166 ± 0.400 |
| 100 | 100 | OutcomeModelTransport | 0.935 ± 0.166 | 0.654 ± 2.004 | 0.702 ± 0.314 | 1.728 ± 1.306 | 2.578 ± 1.980 |
| 100 | 100 | OutcomeModelTransport | 1.067 ± 0.456 | -0.402 ± 0.526 | 0.637 ± 0.276 | 0.736 ± 0.299 | 1.642 ± 0.511 |
| 100 | 100 | OutcomeModelTransport | 1.007 ± 0.042 | 0.705 ± 0.825 | 0.810 ± 0.132 | 0.815 ± 0.550 | 1.375 ± 0.628 |
| 100 | 100 | ProxyOnly | 1.119 ± 0.254 | -0.162 ± 0.825 | 0.346 ± 0.117 | 0.871 ± 0.256 | 1.822 ± 0.232 |
| 100 | 100 | ProxyOnly | 1.324 ± 0.317 | 0.564 ± 1.737 | 0.199 ± 0.091 | 1.446 ± 0.717 | 2.793 ± 0.519 |
| 100 | 100 | ProxyOnly | 1.036 ± 0.489 | -0.198 ± 0.867 | 0.472 ± 0.266 | 0.783 ± 0.311 | 1.659 ± 0.881 |
| 100 | 100 | ProxyOnly | 1.265 ± 0.365 | 0.952 ± 1.526 | 0.099 ± 0.032 | 1.519 ± 0.444 | 3.314 ± 0.731 |
| 100 | 100 | TargetOnlyDR | 1.584 ± 0.261 | -0.479 ± 0.851 | 0.571 ± 0.131 | 1.021 ± 0.418 | 2.354 ± 0.749 |
| 100 | 100 | TargetOnlyDR | 1.545 ± 0.582 | 1.008 ± 3.085 | 0.333 ± 0.101 | 1.234 ± 0.423 | 2.831 ± 0.898 |
| 100 | 100 | TargetOnlyDR | 1.205 ± 0.117 | 0.180 ± 0.462 | 0.744 ± 0.067 | 0.500 ± 0.232 | 1.133 ± 0.560 |
| 100 | 100 | TargetOnlyDR | 1.674 ± 0.277 | -0.392 ± 2.745 | 0.211 ± 0.044 | 1.479 ± 0.486 | 3.147 ± 0.941 |
| 200 | 200 | AnchorOnly | 1.551 ± 0.099 | 0.190 ± 0.782 | 0.630 ± 0.063 | 0.859 ± 0.246 | 2.282 ± 0.652 |
| 200 | 200 | AnchorOnly | 1.590 ± 0.307 | -0.208 ± 0.835 | 0.435 ± 0.071 | 1.348 ± 0.589 | 3.321 ± 1.279 |
| 200 | 200 | AnchorOnly | 1.537 ± 0.425 | -0.889 ± 1.719 | 0.266 ± 0.077 | 1.859 ± 0.585 | 4.006 ± 1.095 |
| 200 | 200 | AnchorOnly | 1.141 ± 0.072 | -0.069 ± 0.124 | 0.757 ± 0.013 | 0.370 ± 0.234 | 0.834 ± 0.475 |
| 200 | 200 | AnchorPlugin | 1.074 ± 0.137 | 0.124 ± 0.730 | 0.689 ± 0.174 | 0.656 ± 0.334 | 1.204 ± 0.548 |
| 200 | 200 | AnchorPlugin | 1.093 ± 0.092 | -0.115 ± 0.679 | 0.645 ± 0.072 | 0.747 ± 0.131 | 1.502 ± 0.290 |
| 200 | 200 | AnchorPlugin | 1.027 ± 0.094 | 1.962 ± 0.764 | 0.438 ± 0.220 | 1.883 ± 0.769 | 3.060 ± 0.641 |
| 200 | 200 | AnchorPlugin | 0.904 ± 0.227 | 0.456 ± 0.525 | 0.656 ± 0.236 | 0.586 ± 0.384 | 1.302 ± 0.518 |
| 200 | 200 | EntropyBalancing | 0.992 ± 0.103 | 0.227 ± 1.219 | 0.760 ± 0.277 | 0.954 ± 0.576 | 1.446 ± 0.332 |
| 200 | 200 | EntropyBalancing | 0.962 ± 0.080 | 0.060 ± 0.678 | 0.819 ± 0.127 | 0.604 ± 0.326 | 1.073 ± 0.576 |
| 200 | 200 | EntropyBalancing | 0.897 ± 0.210 | 0.799 ± 0.871 | 0.603 ± 0.294 | 1.374 ± 1.164 | 2.972 ± 2.470 |
| 200 | 200 | EntropyBalancing | 1.002 ± 0.232 | 0.415 ± 0.608 | 0.678 ± 0.287 | 0.697 ± 0.189 | 1.327 ± 0.384 |
| 200 | 200 | Glmtrans_Auto | 1.041 ± 0.016 | -0.014 ± 0.067 | 0.989 ± 0.007 | 0.118 ± 0.034 | 0.269 ± 0.074 |
| 200 | 200 | Glmtrans_Auto | 1.025 ± 0.015 | -0.026 ± 0.053 | 0.988 ± 0.005 | 0.141 ± 0.038 | 0.316 ± 0.113 |
| 200 | 200 | Glmtrans_Auto | 1.024 ± 0.021 | -0.062 ± 0.076 | 0.990 ± 0.004 | 0.203 ± 0.096 | 0.487 ± 0.220 |
| 200 | 200 | Glmtrans_Auto | 1.013 ± 0.042 | -0.008 ± 0.072 | 0.975 ± 0.009 | 0.074 ± 0.052 | 0.182 ± 0.125 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.989 ± 0.008 | -0.034 ± 0.053 | 0.991 ± 0.006 | 0.061 ± 0.017 | 0.124 ± 0.016 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.994 ± 0.017 | -0.046 ± 0.065 | 0.988 ± 0.006 | 0.088 ± 0.055 | 0.221 ± 0.112 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.988 ± 0.012 | -0.014 ± 0.150 | 0.980 ± 0.005 | 0.163 ± 0.090 | 0.458 ± 0.226 |
| 200 | 200 | Glmtrans_DR_CrossFit | 1.006 ± 0.023 | -0.011 ± 0.065 | 0.974 ± 0.009 | 0.065 ± 0.047 | 0.166 ± 0.120 |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 200 | 200 | IPWTransport | 1.000 ± 0.101 | 0.214 ± 1.211 | 0.761 ± 0.277 | 0.952 ± 0.578 | 1.489 ± 0.324 |
| 200 | 200 | IPWTransport | 0.985 ± 0.077 | 0.079 ± 0.675 | 0.833 ± 0.128 | 0.569 ± 0.297 | 1.042 ± 0.521 |
| 200 | 200 | IPWTransport | 0.954 ± 0.219 | 0.741 ± 0.853 | 0.643 ± 0.313 | 1.253 ± 0.988 | 2.875 ± 2.108 |
| 200 | 200 | IPWTransport | 1.006 ± 0.242 | 0.409 ± 0.629 | 0.675 ± 0.285 | 0.706 ± 0.178 | 1.331 ± 0.407 |
| 200 | 200 | OutcomeModelTransport | 1.011 ± 0.098 | 0.210 ± 1.238 | 0.763 ± 0.279 | 0.968 ± 0.599 | 1.530 ± 0.348 |
| 200 | 200 | OutcomeModelTransport | 1.003 ± 0.079 | 0.036 ± 0.775 | 0.846 ± 0.129 | 0.606 ± 0.315 | 1.176 ± 0.655 |
| 200 | 200 | OutcomeModelTransport | 0.960 ± 0.193 | 1.006 ± 0.607 | 0.650 ± 0.320 | 1.330 ± 0.813 | 2.582 ± 1.512 |
| 200 | 200 | OutcomeModelTransport | 1.013 ± 0.246 | 0.383 ± 0.617 | 0.675 ± 0.287 | 0.678 ± 0.217 | 1.220 ± 0.475 |
| 200 | 200 | ProxyOnly | 1.389 ± 0.303 | 0.062 ± 0.706 | 0.416 ± 0.099 | 0.909 ± 0.399 | 1.918 ± 0.937 |
| 200 | 200 | ProxyOnly | 1.615 ± 0.314 | 1.127 ± 1.801 | 0.301 ± 0.073 | 1.282 ± 0.582 | 3.109 ± 1.341 |
| 200 | 200 | ProxyOnly | 1.544 ± 0.292 | 2.753 ± 3.685 | 0.156 ± 0.059 | 2.790 ± 1.361 | 4.692 ± 1.671 |
| 200 | 200 | ProxyOnly | 0.901 ± 0.213 | 0.486 ± 0.773 | 0.453 ± 0.126 | 0.772 ± 0.556 | 1.429 ± 0.570 |
| 200 | 200 | TargetOnlyDR | 1.618 ± 0.110 | 0.027 ± 1.043 | 0.657 ± 0.047 | 0.953 ± 0.305 | 2.392 ± 0.838 |
| 200 | 200 | TargetOnlyDR | 1.710 ± 0.316 | 0.289 ± 1.302 | 0.462 ± 0.046 | 1.507 ± 0.547 | 3.288 ± 1.445 |
| 200 | 200 | TargetOnlyDR | 1.626 ± 0.354 | -1.142 ± 2.247 | 0.290 ± 0.034 | 1.750 ± 0.609 | 4.600 ± 1.061 |
| 200 | 200 | TargetOnlyDR | 1.203 ± 0.112 | -0.132 ± 0.176 | 0.775 ± 0.006 | 0.369 ± 0.272 | 0.881 ± 0.566 |
| 500 | 500 | AnchorOnly | 1.765 ± 0.455 | 0.223 ± 1.975 | 0.325 ± 0.058 | 2.142 ± 0.529 | 5.270 ± 1.510 |
| 500 | 500 | AnchorOnly | 1.643 ± 0.197 | 0.256 ± 0.717 | 0.459 ± 0.032 | 1.341 ± 0.309 | 2.964 ± 0.552 |
| 500 | 500 | AnchorOnly | 1.205 ± 0.137 | -0.056 ± 0.216 | 0.788 ± 0.039 | 0.343 ± 0.182 | 0.815 ± 0.368 |
| 500 | 500 | AnchorOnly | 1.425 ± 0.050 | 0.021 ± 0.920 | 0.658 ± 0.027 | 0.829 ± 0.203 | 2.285 ± 0.638 |
| 500 | 500 | AnchorPlugin | 1.134 ± 0.039 | 0.119 ± 1.292 | 0.520 ± 0.141 | 1.154 ± 0.289 | 2.651 ± 0.612 |
| 500 | 500 | AnchorPlugin | 1.094 ± 0.103 | -0.118 ± 0.501 | 0.632 ± 0.140 | 0.666 ± 0.263 | 1.238 ± 0.547 |
| 500 | 500 | AnchorPlugin | 1.168 ± 0.473 | -0.173 ± 0.296 | 0.766 ± 0.079 | 0.592 ± 0.342 | 1.332 ± 0.968 |
| 500 | 500 | AnchorPlugin | 1.022 ± 0.153 | -0.044 ± 0.541 | 0.482 ± 0.204 | 0.410 ± 0.269 | 0.982 ± 0.563 |
| 500 | 500 | EntropyBalancing | 0.858 ± 0.037 | 0.060 ± 1.082 | 0.635 ± 0.163 | 1.303 ± 0.574 | 2.916 ± 1.386 |
| 500 | 500 | EntropyBalancing | 0.913 ± 0.172 | -0.522 ± 0.896 | 0.777 ± 0.272 | 1.004 ± 0.797 | 2.023 ± 2.014 |
| 500 | 500 | EntropyBalancing | 1.402 ± 0.650 | 0.274 ± 0.729 | 0.803 ± 0.070 | 0.814 ± 0.512 | 1.846 ± 1.451 |
| 500 | 500 | EntropyBalancing | 0.992 ± 0.239 | -0.011 ± 1.135 | 0.534 ± 0.297 | 1.012 ± 0.342 | 1.779 ± 0.360 |
| 500 | 500 | Glmtrans_Auto | 1.028 ± 0.011 | -0.019 ± 0.089 | 0.997 ± 0.001 | 0.189 ± 0.055 | 0.437 ± 0.118 |
| 500 | 500 | Glmtrans_Auto | 1.023 ± 0.013 | 0.020 ± 0.041 | 0.994 ± 0.005 | 0.124 ± 0.052 | 0.282 ± 0.154 |
| 500 | 500 | Glmtrans_Auto | 1.010 ± 0.005 | -0.006 ± 0.057 | 0.981 ± 0.017 | 0.061 ± 0.014 | 0.124 ± 0.019 |
| 500 | 500 | Glmtrans_Auto | 1.019 ± 0.023 | 0.023 ± 0.070 | 0.996 ± 0.002 | 0.074 ± 0.049 | 0.148 ± 0.122 |
| 500 | 500 | Glmtrans_DR_CrossFit | 1.004 ± 0.007 | -0.023 ± 0.020 | 0.997 ± 0.001 | 0.063 ± 0.035 | 0.148 ± 0.097 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.997 ± 0.012 | 0.006 ± 0.030 | 0.994 ± 0.005 | 0.054 ± 0.030 | 0.138 ± 0.065 |
| 500 | 500 | Glmtrans_DR_CrossFit | 1.009 ± 0.012 | -0.012 ± 0.059 | 0.982 ± 0.018 | 0.066 ± 0.014 | 0.127 ± 0.040 |
| 500 | 500 | Glmtrans_DR_CrossFit | 1.009 ± 0.012 | 0.013 ± 0.043 | 0.996 ± 0.001 | 0.059 ± 0.015 | 0.111 ± 0.035 |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A | N/A | N/A |
| 500 | 500 | IPWTransport | 0.904 ± 0.037 | 0.049 ± 1.218 | 0.668 ± 0.163 | 1.181 ± 0.656 | 2.505 ± 1.236 |
| 500 | 500 | IPWTransport | 0.918 ± 0.164 | -0.507 ± 0.904 | 0.782 ± 0.265 | 0.981 ± 0.742 | 1.988 ± 1.963 |
| 500 | 500 | IPWTransport | 1.406 ± 0.659 | 0.277 ± 0.730 | 0.804 ± 0.069 | 0.816 ± 0.514 | 1.850 ± 1.455 |
| 500 | 500 | IPWTransport | 0.996 ± 0.233 | -0.014 ± 1.141 | 0.536 ± 0.294 | 1.014 ± 0.346 | 1.736 ± 0.364 |
| 500 | 500 | OutcomeModelTransport | 0.958 ± 0.023 | 0.061 ± 1.264 | 0.719 ± 0.193 | 1.001 ± 0.731 | 1.793 ± 1.043 |
| 500 | 500 | OutcomeModelTransport | 0.954 ± 0.126 | -0.633 ± 0.922 | 0.800 ± 0.237 | 0.966 ± 0.755 | 1.817 ± 1.649 |
| 500 | 500 | OutcomeModelTransport | 1.449 ± 0.741 | 0.263 ± 0.728 | 0.820 ± 0.050 | 0.838 ± 0.563 | 1.906 ± 1.530 |
| 500 | 500 | OutcomeModelTransport | 1.027 ± 0.222 | -0.016 ± 1.112 | 0.552 ± 0.271 | 0.972 ± 0.352 | 1.769 ± 0.447 |
| 500 | 500 | ProxyOnly | 1.743 ± 0.214 | 1.437 ± 4.950 | 0.199 ± 0.048 | 2.327 ± 0.694 | 5.428 ± 1.790 |
| 500 | 500 | ProxyOnly | 1.696 ± 0.426 | 0.745 ± 1.003 | 0.351 ± 0.069 | 1.282 ± 0.561 | 3.089 ± 1.525 |
| 500 | 500 | ProxyOnly | 0.996 ± 0.309 | -0.413 ± 0.757 | 0.562 ± 0.189 | 0.688 ± 0.440 | 1.422 ± 0.602 |
| 500 | 500 | ProxyOnly | 1.126 ± 0.425 | -0.324 ± 1.209 | 0.294 ± 0.145 | 0.932 ± 0.341 | 2.314 ± 1.032 |
| 500 | 500 | TargetOnlyDR | 1.816 ± 0.566 | -0.207 ± 2.594 | 0.343 ± 0.070 | 1.981 ± 0.566 | 5.341 ± 0.772 |
| 500 | 500 | TargetOnlyDR | 1.719 ± 0.275 | 0.362 ± 0.703 | 0.496 ± 0.049 | 1.374 ± 0.320 | 3.418 ± 0.600 |
| 500 | 500 | TargetOnlyDR | 1.213 ± 0.140 | -0.024 ± 0.263 | 0.788 ± 0.048 | 0.353 ± 0.183 | 0.944 ± 0.609 |
| 500 | 500 | TargetOnlyDR | 1.409 ± 0.105 | 0.137 ± 0.787 | 0.666 ± 0.011 | 0.792 ± 0.195 | 2.317 ± 0.655 |

### Extended Targeting Metrics

| m0 | m1 | Method | Top-10% Captured | Top-20% Captured | Top-30% Ratio (↑) |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 6.225 ± 3.017 | 5.158 ± 2.885 | 0.354 ± 0.300 |
| 50 | 50 | AnchorOnly | 4.635 ± 3.327 | 4.011 ± 2.749 | 0.449 ± 0.235 |
| 50 | 50 | AnchorOnly | 3.634 ± 1.881 | 2.824 ± 1.539 | 0.599 ± 0.199 |
| 50 | 50 | AnchorOnly | 3.393 ± 0.870 | 2.707 ± 0.705 | 0.809 ± 0.051 |
| 50 | 50 | AnchorPlugin | 8.069 ± 2.571 | 6.765 ± 2.589 | 0.517 ± 0.233 |
| 50 | 50 | AnchorPlugin | 6.293 ± 2.353 | 5.059 ± 2.178 | 0.608 ± 0.185 |
| 50 | 50 | AnchorPlugin | 4.134 ± 1.705 | 3.098 ± 1.502 | 0.647 ± 0.244 |
| 50 | 50 | AnchorPlugin | 3.306 ± 0.825 | 2.644 ± 0.876 | 0.780 ± 0.149 |
| 50 | 50 | EntropyBalancing | 11.669 ± 3.102 | 9.514 ± 3.236 | 0.753 ± 0.210 |
| 50 | 50 | EntropyBalancing | 8.420 ± 2.367 | 6.816 ± 2.247 | 0.839 ± 0.160 |
| 50 | 50 | EntropyBalancing | 4.079 ± 2.857 | 3.058 ± 2.465 | 0.617 ± 0.601 |
| 50 | 50 | EntropyBalancing | 3.467 ± 1.013 | 2.818 ± 0.927 | 0.808 ± 0.105 |
| 50 | 50 | Glmtrans_Auto | 13.381 ± 2.772 | 10.610 ± 2.926 | 0.862 ± 0.166 |
| 50 | 50 | Glmtrans_Auto | 9.544 ± 2.029 | 7.702 ± 1.990 | 0.944 ± 0.075 |
| 50 | 50 | Glmtrans_Auto | 5.586 ± 1.588 | 4.298 ± 1.401 | 0.982 ± 0.009 |
| 50 | 50 | Glmtrans_Auto | 4.056 ± 1.018 | 3.285 ± 0.858 | 0.969 ± 0.025 |
| 50 | 50 | Glmtrans_DR_CrossFit | 9.003 ± 4.076 | 7.085 ± 3.551 | 0.546 ± 0.284 |
| 50 | 50 | Glmtrans_DR_CrossFit | 9.147 ± 1.955 | 7.289 ± 2.014 | 0.895 ± 0.049 |
| 50 | 50 | Glmtrans_DR_CrossFit | 5.389 ± 1.551 | 4.091 ± 1.399 | 0.931 ± 0.053 |
| 50 | 50 | Glmtrans_DR_CrossFit | 4.020 ± 1.089 | 3.244 ± 0.938 | 0.953 ± 0.055 |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | Glmtrans_OptionB | N/A | N/A | N/A |
| 50 | 50 | IPWTransport | 12.354 ± 3.019 | 10.094 ± 2.688 | 0.823 ± 0.161 |
| 50 | 50 | IPWTransport | 8.594 ± 2.284 | 6.802 ± 2.345 | 0.838 ± 0.175 |
| 50 | 50 | IPWTransport | 4.175 ± 2.733 | 3.035 ± 2.454 | 0.616 ± 0.582 |
| 50 | 50 | IPWTransport | 3.443 ± 1.043 | 2.794 ± 0.931 | 0.801 ± 0.109 |
| 50 | 50 | OutcomeModelTransport | 12.299 ± 3.020 | 10.189 ± 2.725 | 0.823 ± 0.156 |
| 50 | 50 | OutcomeModelTransport | 8.518 ± 2.314 | 6.747 ± 2.359 | 0.836 ± 0.181 |
| 50 | 50 | OutcomeModelTransport | 4.177 ± 2.721 | 3.024 ± 2.457 | 0.617 ± 0.583 |
| 50 | 50 | OutcomeModelTransport | 3.436 ± 1.038 | 2.792 ± 0.934 | 0.800 ± 0.110 |
| 50 | 50 | ProxyOnly | 2.460 ± 1.826 | 2.229 ± 1.768 | 0.157 ± 0.213 |
| 50 | 50 | ProxyOnly | 3.619 ± 2.000 | 3.069 ± 2.006 | 0.365 ± 0.179 |
| 50 | 50 | ProxyOnly | 2.412 ± 1.868 | 1.736 ± 1.625 | 0.323 ± 0.306 |
| 50 | 50 | ProxyOnly | 2.163 ± 0.770 | 1.786 ± 0.746 | 0.568 ± 0.220 |
| 50 | 50 | TargetOnlyDR | 6.014 ± 2.538 | 4.622 ± 2.575 | 0.352 ± 0.266 |
| 50 | 50 | TargetOnlyDR | 4.657 ± 2.832 | 3.778 ± 2.646 | 0.423 ± 0.236 |
| 50 | 50 | TargetOnlyDR | 4.031 ± 1.559 | 3.060 ± 1.387 | 0.642 ± 0.120 |
| 50 | 50 | TargetOnlyDR | 3.264 ± 0.985 | 2.648 ± 0.745 | 0.773 ± 0.046 |
| 100 | 100 | AnchorOnly | 5.970 ± 1.312 | 4.993 ± 1.185 | 0.794 ± 0.082 |
| 100 | 100 | AnchorOnly | 6.095 ± 2.982 | 5.231 ± 3.019 | 0.537 ± 0.146 |
| 100 | 100 | AnchorOnly | 3.919 ± 1.331 | 3.132 ± 1.005 | 0.829 ± 0.092 |
| 100 | 100 | AnchorOnly | 8.250 ± 3.024 | 6.802 ± 3.496 | 0.485 ± 0.119 |
| 100 | 100 | AnchorPlugin | 6.237 ± 0.676 | 5.191 ± 0.627 | 0.818 ± 0.087 |
| 100 | 100 | AnchorPlugin | 7.425 ± 3.946 | 5.867 ± 3.663 | 0.652 ± 0.209 |
| 100 | 100 | AnchorPlugin | 3.576 ± 1.762 | 2.734 ± 1.738 | 0.677 ± 0.422 |
| 100 | 100 | AnchorPlugin | 11.109 ± 3.942 | 9.246 ± 4.011 | 0.686 ± 0.103 |
| 100 | 100 | EntropyBalancing | 6.281 ± 0.914 | 5.137 ± 0.835 | 0.812 ± 0.146 |
| 100 | 100 | EntropyBalancing | 8.180 ± 3.237 | 6.454 ± 3.058 | 0.768 ± 0.235 |
| 100 | 100 | EntropyBalancing | 3.606 ± 1.679 | 2.787 ± 1.440 | 0.694 ± 0.317 |
| 100 | 100 | EntropyBalancing | 13.568 ± 3.974 | 11.132 ± 3.689 | 0.863 ± 0.055 |
| 100 | 100 | Glmtrans_Auto | 7.733 ± 0.760 | 6.365 ± 0.700 | 0.992 ± 0.002 |
| 100 | 100 | Glmtrans_Auto | 11.160 ± 4.117 | 8.911 ± 3.833 | 0.990 ± 0.006 |
| 100 | 100 | Glmtrans_Auto | 4.740 ± 1.250 | 3.689 ± 1.030 | 0.991 ± 0.008 |
| 100 | 100 | Glmtrans_Auto | 15.531 ± 4.070 | 12.787 ± 3.957 | 0.985 ± 0.008 |
| 100 | 100 | Glmtrans_DR_CrossFit | 7.740 ± 0.755 | 6.358 ± 0.690 | 0.992 ± 0.003 |
| 100 | 100 | Glmtrans_DR_CrossFit | 10.816 ± 3.990 | 8.684 ± 3.769 | 0.964 ± 0.031 |
| 100 | 100 | Glmtrans_DR_CrossFit | 4.735 ± 1.266 | 3.683 ± 1.030 | 0.990 ± 0.009 |
| 100 | 100 | Glmtrans_DR_CrossFit | 14.620 ± 4.252 | 11.994 ± 4.079 | 0.921 ± 0.071 |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | Glmtrans_OptionB | N/A | N/A | N/A |
| 100 | 100 | IPWTransport | 6.313 ± 0.889 | 5.156 ± 0.825 | 0.810 ± 0.144 |
| 100 | 100 | IPWTransport | 8.617 ± 3.601 | 6.661 ± 3.258 | 0.789 ± 0.241 |
| 100 | 100 | IPWTransport | 3.616 ± 1.677 | 2.755 ± 1.527 | 0.685 ± 0.331 |
| 100 | 100 | IPWTransport | 14.153 ± 3.611 | 11.584 ± 3.647 | 0.897 ± 0.056 |
| 100 | 100 | OutcomeModelTransport | 6.331 ± 0.892 | 5.172 ± 0.808 | 0.813 ± 0.143 |
| 100 | 100 | OutcomeModelTransport | 8.691 ± 3.926 | 6.955 ± 3.632 | 0.801 ± 0.241 |
| 100 | 100 | OutcomeModelTransport | 3.589 ± 1.653 | 2.749 ± 1.535 | 0.680 ± 0.342 |
| 100 | 100 | OutcomeModelTransport | 14.284 ± 3.522 | 11.720 ± 3.553 | 0.908 ± 0.059 |
| 100 | 100 | ProxyOnly | 5.123 ± 0.821 | 4.264 ± 0.742 | 0.643 ± 0.088 |
| 100 | 100 | ProxyOnly | 4.616 ± 3.748 | 3.848 ± 3.561 | 0.305 ± 0.356 |
| 100 | 100 | ProxyOnly | 2.720 ± 2.315 | 2.051 ± 2.091 | 0.441 ± 0.669 |
| 100 | 100 | ProxyOnly | 5.766 ± 4.404 | 5.196 ± 3.623 | 0.401 ± 0.142 |
| 100 | 100 | TargetOnlyDR | 5.807 ± 1.363 | 4.978 ± 1.056 | 0.789 ± 0.080 |
| 100 | 100 | TargetOnlyDR | 6.424 ± 3.206 | 5.237 ± 3.101 | 0.526 ± 0.157 |
| 100 | 100 | TargetOnlyDR | 3.992 ± 1.209 | 3.177 ± 0.933 | 0.845 ± 0.060 |
| 100 | 100 | TargetOnlyDR | 8.253 ± 3.846 | 7.255 ± 3.798 | 0.533 ± 0.129 |
| 200 | 200 | AnchorOnly | 5.258 ± 2.856 | 4.301 ± 2.599 | 0.636 ± 0.460 |
| 200 | 200 | AnchorOnly | 6.052 ± 2.405 | 4.743 ± 2.117 | 0.608 ± 0.147 |
| 200 | 200 | AnchorOnly | 9.721 ± 3.036 | 7.841 ± 3.150 | 0.537 ± 0.133 |
| 200 | 200 | AnchorOnly | 4.567 ± 2.177 | 3.768 ± 1.786 | 0.905 ± 0.036 |
| 200 | 200 | AnchorPlugin | 5.245 ± 2.186 | 4.178 ± 2.119 | 0.688 ± 0.351 |
| 200 | 200 | AnchorPlugin | 7.152 ± 1.557 | 5.616 ± 1.331 | 0.786 ± 0.043 |
| 200 | 200 | AnchorPlugin | 11.476 ± 1.117 | 9.269 ± 1.400 | 0.684 ± 0.151 |
| 200 | 200 | AnchorPlugin | 4.179 ± 1.747 | 3.362 ± 1.436 | 0.826 ± 0.151 |
| 200 | 200 | EntropyBalancing | 5.318 ± 1.885 | 4.283 ± 1.810 | 0.847 ± 0.128 |
| 200 | 200 | EntropyBalancing | 8.320 ± 1.842 | 6.471 ± 1.563 | 0.896 ± 0.067 |
| 200 | 200 | EntropyBalancing | 13.195 ± 2.390 | 10.724 ± 1.776 | 0.778 ± 0.174 |
| 200 | 200 | EntropyBalancing | 3.937 ± 1.525 | 3.258 ± 1.268 | 0.829 ± 0.175 |
| 200 | 200 | Glmtrans_Auto | 6.437 ± 3.004 | 5.187 ± 2.747 | 0.989 ± 0.014 |
| 200 | 200 | Glmtrans_Auto | 9.255 ± 2.488 | 7.237 ± 2.073 | 0.994 ± 0.004 |
| 200 | 200 | Glmtrans_Auto | 17.429 ± 4.929 | 14.264 ± 4.130 | 0.996 ± 0.002 |
| 200 | 200 | Glmtrans_Auto | 5.077 ± 2.377 | 4.170 ± 1.959 | 0.990 ± 0.003 |
| 200 | 200 | Glmtrans_DR_CrossFit | 6.449 ± 3.005 | 5.188 ± 2.746 | 0.992 ± 0.010 |
| 200 | 200 | Glmtrans_DR_CrossFit | 9.250 ± 2.488 | 7.236 ± 2.078 | 0.995 ± 0.003 |
| 200 | 200 | Glmtrans_DR_CrossFit | 17.313 ± 4.887 | 14.212 ± 4.109 | 0.991 ± 0.003 |
| 200 | 200 | Glmtrans_DR_CrossFit | 5.074 ± 2.373 | 4.168 ± 1.957 | 0.989 ± 0.002 |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | Glmtrans_OptionB | N/A | N/A | N/A |
| 200 | 200 | IPWTransport | 5.349 ± 1.918 | 4.299 ± 1.818 | 0.848 ± 0.125 |
| 200 | 200 | IPWTransport | 8.384 ± 1.772 | 6.507 ± 1.522 | 0.902 ± 0.070 |
| 200 | 200 | IPWTransport | 13.553 ± 2.221 | 11.062 ± 1.616 | 0.804 ± 0.181 |
| 200 | 200 | IPWTransport | 3.940 ± 1.526 | 3.268 ± 1.264 | 0.827 ± 0.176 |
| 200 | 200 | OutcomeModelTransport | 5.345 ± 1.912 | 4.303 ± 1.826 | 0.853 ± 0.123 |
| 200 | 200 | OutcomeModelTransport | 8.371 ± 1.712 | 6.522 ± 1.431 | 0.907 ± 0.069 |
| 200 | 200 | OutcomeModelTransport | 13.720 ± 1.749 | 10.906 ± 1.354 | 0.812 ± 0.183 |
| 200 | 200 | OutcomeModelTransport | 3.943 ± 1.532 | 3.263 ± 1.270 | 0.822 ± 0.175 |
| 200 | 200 | ProxyOnly | 3.991 ± 2.563 | 3.391 ± 2.458 | 0.307 ± 0.925 |
| 200 | 200 | ProxyOnly | 4.963 ± 1.752 | 3.915 ± 1.631 | 0.499 ± 0.100 |
| 200 | 200 | ProxyOnly | 7.474 ± 1.715 | 6.226 ± 1.772 | 0.460 ± 0.059 |
| 200 | 200 | ProxyOnly | 3.646 ± 1.459 | 2.899 ± 1.113 | 0.724 ± 0.091 |
| 200 | 200 | TargetOnlyDR | 5.365 ± 2.910 | 4.256 ± 2.671 | 0.617 ± 0.504 |
| 200 | 200 | TargetOnlyDR | 6.344 ± 2.493 | 4.949 ± 2.033 | 0.661 ± 0.075 |
| 200 | 200 | TargetOnlyDR | 10.121 ± 3.343 | 8.116 ± 3.140 | 0.558 ± 0.103 |
| 200 | 200 | TargetOnlyDR | 4.671 ± 2.232 | 3.830 ± 1.810 | 0.904 ± 0.034 |
| 500 | 500 | AnchorOnly | 9.345 ± 3.152 | 7.455 ± 3.116 | 0.557 ± 0.213 |
| 500 | 500 | AnchorOnly | 6.001 ± 1.458 | 4.570 ± 1.285 | 0.631 ± 0.083 |
| 500 | 500 | AnchorOnly | 4.113 ± 1.267 | 3.355 ± 1.376 | 0.887 ± 0.055 |
| 500 | 500 | AnchorOnly | 5.708 ± 2.046 | 4.555 ± 2.001 | 0.777 ± 0.102 |
| 500 | 500 | AnchorPlugin | 10.611 ± 2.101 | 8.605 ± 2.153 | 0.686 ± 0.155 |
| 500 | 500 | AnchorPlugin | 7.191 ± 1.592 | 5.620 ± 1.364 | 0.760 ± 0.106 |
| 500 | 500 | AnchorPlugin | 4.151 ± 1.364 | 3.280 ± 1.373 | 0.862 ± 0.047 |
| 500 | 500 | AnchorPlugin | 4.663 ± 1.159 | 3.719 ± 1.366 | 0.646 ± 0.151 |
| 500 | 500 | EntropyBalancing | 11.712 ± 2.176 | 9.404 ± 2.000 | 0.778 ± 0.113 |
| 500 | 500 | EntropyBalancing | 7.840 ± 2.503 | 6.194 ± 2.015 | 0.849 ± 0.192 |
| 500 | 500 | EntropyBalancing | 4.209 ± 1.400 | 3.332 ± 1.359 | 0.869 ± 0.086 |
| 500 | 500 | EntropyBalancing | 4.962 ± 1.407 | 3.803 ± 1.246 | 0.712 ± 0.158 |
| 500 | 500 | Glmtrans_Auto | 15.260 ± 3.237 | 12.151 ± 2.858 | 0.999 ± 0.001 |
| 500 | 500 | Glmtrans_Auto | 9.215 ± 2.027 | 7.195 ± 1.682 | 0.997 ± 0.004 |
| 500 | 500 | Glmtrans_Auto | 4.643 ± 1.500 | 3.691 ± 1.447 | 0.991 ± 0.008 |
| 500 | 500 | Glmtrans_Auto | 7.091 ± 2.269 | 5.619 ± 2.087 | 0.997 ± 0.003 |
| 500 | 500 | Glmtrans_DR_CrossFit | 15.264 ± 3.231 | 12.152 ± 2.856 | 0.999 ± 0.000 |
| 500 | 500 | Glmtrans_DR_CrossFit | 9.205 ± 2.029 | 7.198 ± 1.692 | 0.996 ± 0.004 |
| 500 | 500 | Glmtrans_DR_CrossFit | 4.644 ± 1.500 | 3.694 ± 1.442 | 0.993 ± 0.006 |
| 500 | 500 | Glmtrans_DR_CrossFit | 7.092 ± 2.264 | 5.618 ± 2.088 | 0.997 ± 0.004 |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | Glmtrans_OptionB | N/A | N/A | N/A |
| 500 | 500 | IPWTransport | 12.094 ± 1.941 | 9.542 ± 1.878 | 0.796 ± 0.116 |
| 500 | 500 | IPWTransport | 7.864 ± 2.477 | 6.206 ± 1.981 | 0.858 ± 0.180 |
| 500 | 500 | IPWTransport | 4.209 ± 1.400 | 3.334 ± 1.362 | 0.869 ± 0.086 |
| 500 | 500 | IPWTransport | 4.985 ± 1.376 | 3.815 ± 1.262 | 0.711 ± 0.156 |
| 500 | 500 | OutcomeModelTransport | 12.588 ± 1.801 | 9.949 ± 1.955 | 0.830 ± 0.137 |
| 500 | 500 | OutcomeModelTransport | 7.998 ± 2.268 | 6.333 ± 1.821 | 0.877 ± 0.149 |
| 500 | 500 | OutcomeModelTransport | 4.260 ± 1.462 | 3.370 ± 1.434 | 0.880 ± 0.099 |
| 500 | 500 | OutcomeModelTransport | 5.066 ± 1.382 | 3.993 ± 1.363 | 0.716 ± 0.151 |
| 500 | 500 | ProxyOnly | 6.595 ± 2.301 | 5.073 ± 2.044 | 0.387 ± 0.181 |
| 500 | 500 | ProxyOnly | 5.471 ± 1.827 | 4.296 ± 1.552 | 0.538 ± 0.100 |
| 500 | 500 | ProxyOnly | 3.518 ± 1.391 | 2.812 ± 1.310 | 0.728 ± 0.121 |
| 500 | 500 | ProxyOnly | 3.795 ± 1.410 | 2.950 ± 1.424 | 0.471 ± 0.297 |
| 500 | 500 | TargetOnlyDR | 9.466 ± 2.430 | 7.188 ± 2.773 | 0.543 ± 0.202 |
| 500 | 500 | TargetOnlyDR | 6.279 ± 1.437 | 4.917 ± 1.324 | 0.669 ± 0.080 |
| 500 | 500 | TargetOnlyDR | 4.190 ± 1.391 | 3.356 ± 1.392 | 0.888 ± 0.046 |
| 500 | 500 | TargetOnlyDR | 5.808 ± 2.099 | 4.564 ± 1.993 | 0.789 ± 0.078 |

---

## 7. Plots

### PEHE vs Sweep Parameter (↓ lower is better)

![PEHE](gold_fair_dim_sweep_pehe.png)

### ATE Error vs Sweep Parameter (↓ lower is better)

![ATE Error](gold_fair_dim_sweep_ate.png)

### Spearman Correlation vs Sweep Parameter (↑ higher is better)

![Correlation](gold_fair_dim_sweep_corr.png)

---

## 8. Key Findings

1. **Best overall PEHE:** Glmtrans_DR_CrossFit achieves lowest average PEHE (0.264)
2. **Best overall ATE Error:** Glmtrans_DR_CrossFit achieves lowest average ATE error (0.0216)
3. **Lowest policy regret:** Glmtrans_DR_CrossFit (0.0035)
4. **Scaling:** Glmtrans_Auto ATE error decreases with higher m0
5. **Best ranking:** Glmtrans_DR_CrossFit achieves highest Spearman correlation (0.998)

---

## Appendix: Configuration

```python
sweep_param = 'm0'
sweep_values = [50, 100, 200, 500]
base_scenario = {'n_proxy_total': 20000, 'C_sources': 10, 'nontransfer_scale': 0.1, 'use_fair_dgp': True, 'overlap_lambda': 0.25, 'intercept_drift_scale': 0.5}
```

