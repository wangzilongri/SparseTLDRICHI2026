# Fair DGP: Target size × Dimensionality grid (m₀ × p_dim)

**Benchmark ID:** `gold_fair_dim_sweep`

**Generated:** 2026-02-06 05:36

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
| PEHE | **Glmtrans_DR_CrossFit** | 0.2646 | ↓ lower |
| ATE Error | **Glmtrans_Auto** | 0.0227 | ↓ lower |
| Spearman ρ | **Glmtrans_DR_CrossFit** | 0.9985 | ↑ higher |
| Kendall τ | **Glmtrans_DR_CrossFit** | 0.9677 | ↑ higher |
| Qini AUC | **Glmtrans_DR_CrossFit** | 0.9987 | ↑ higher |
| Top-10% Ratio | **Glmtrans_DR_CrossFit** | 0.9992 | ↑ higher |
| Top-20% Ratio | **Glmtrans_Auto** | 0.9984 | ↑ higher |
| Calibration R² | **Glmtrans_DR_CrossFit** | 0.9973 | ↑ higher |
| CATE ECE | **Glmtrans_DR_CrossFit** | 0.0551 | ↓ lower |
| Policy Value | **Glmtrans_Auto** | 4.8128 | ↑ higher |
| Policy Regret | **Glmtrans_DR_CrossFit** | 0.0030 | ↓ lower |

### Core Metrics

| m0 | m1 | Method | PEHE (↓) | ATE Err (↓) | Spearman (↑) | Qini (↑) |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 8.115 ± 1.005 | 0.725 ± 0.535 | 0.374 ± 0.042 | 0.388 ± 0.041 |
| 50 | 50 | AnchorOnly | 5.064 ± 0.575 | 0.538 ± 0.335 | 0.480 ± 0.085 | 0.495 ± 0.089 |
| 50 | 50 | AnchorOnly | 2.798 ± 0.655 | 0.424 ± 0.238 | 0.685 ± 0.041 | 0.704 ± 0.040 |
| 50 | 50 | AnchorOnly | 1.497 ± 0.530 | 0.287 ± 0.208 | 0.792 ± 0.023 | 0.802 ± 0.023 |
| 50 | 50 | AnchorPlugin | 7.611 ± 1.294 | 1.401 ± 0.707 | 0.532 ± 0.089 | 0.549 ± 0.089 |
| 50 | 50 | AnchorPlugin | 4.640 ± 0.729 | 0.692 ± 0.769 | 0.620 ± 0.110 | 0.636 ± 0.106 |
| 50 | 50 | AnchorPlugin | 2.508 ± 0.848 | 0.586 ± 0.363 | 0.740 ± 0.094 | 0.757 ± 0.092 |
| 50 | 50 | AnchorPlugin | 1.692 ± 0.794 | 0.776 ± 0.460 | 0.775 ± 0.111 | 0.785 ± 0.106 |
| 50 | 50 | EntropyBalancing | 5.484 ± 1.926 | 1.062 ± 1.355 | 0.779 ± 0.124 | 0.792 ± 0.120 |
| 50 | 50 | EntropyBalancing | 3.186 ± 1.525 | 1.083 ± 0.837 | 0.839 ± 0.141 | 0.848 ± 0.136 |
| 50 | 50 | EntropyBalancing | 2.453 ± 2.028 | 0.844 ± 1.041 | 0.760 ± 0.277 | 0.772 ± 0.273 |
| 50 | 50 | EntropyBalancing | 1.748 ± 0.267 | 0.757 ± 0.789 | 0.795 ± 0.104 | 0.806 ± 0.098 |
| 50 | 50 | Glmtrans_Auto | 3.875 ± 1.456 | 0.374 ± 0.410 | 0.887 ± 0.064 | 0.895 ± 0.060 |
| 50 | 50 | Glmtrans_Auto | 1.522 ± 0.686 | 0.169 ± 0.156 | 0.959 ± 0.028 | 0.963 ± 0.025 |
| 50 | 50 | Glmtrans_Auto | 0.621 ± 0.129 | 0.060 ± 0.041 | 0.984 ± 0.008 | 0.985 ± 0.007 |
| 50 | 50 | Glmtrans_Auto | 0.500 ± 0.079 | 0.065 ± 0.071 | 0.969 ± 0.037 | 0.971 ± 0.033 |
| 50 | 50 | Glmtrans_DR_CrossFit | 6.677 ± 0.972 | 0.580 ± 0.372 | 0.640 ± 0.056 | 0.659 ± 0.053 |
| 50 | 50 | Glmtrans_DR_CrossFit | 2.554 ± 0.784 | 0.225 ± 0.147 | 0.892 ± 0.043 | 0.900 ± 0.039 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.926 ± 0.359 | 0.133 ± 0.212 | 0.965 ± 0.020 | 0.968 ± 0.020 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.576 ± 0.141 | 0.082 ± 0.070 | 0.957 ± 0.037 | 0.960 ± 0.035 |
| 50 | 50 | Glmtrans_OptionB | 4.829 ± 1.598 | 1.142 ± 1.137 | 0.836 ± 0.091 | 0.847 ± 0.087 |
| 50 | 50 | Glmtrans_OptionB | 3.166 ± 1.591 | 1.124 ± 0.801 | 0.840 ± 0.152 | 0.849 ± 0.146 |
| 50 | 50 | Glmtrans_OptionB | 2.157 ± 1.427 | 0.865 ± 0.717 | 0.819 ± 0.166 | 0.832 ± 0.160 |
| 50 | 50 | Glmtrans_OptionB | 1.613 ± 0.250 | 0.635 ± 0.661 | 0.879 ± 0.063 | 0.886 ± 0.060 |
| 50 | 50 | IPWTransport | 4.849 ± 1.651 | 1.059 ± 1.188 | 0.833 ± 0.094 | 0.844 ± 0.089 |
| 50 | 50 | IPWTransport | 3.129 ± 1.606 | 1.083 ± 0.827 | 0.843 ± 0.149 | 0.852 ± 0.143 |
| 50 | 50 | IPWTransport | 2.478 ± 1.981 | 0.820 ± 1.008 | 0.754 ± 0.271 | 0.767 ± 0.267 |
| 50 | 50 | IPWTransport | 1.774 ± 0.239 | 0.769 ± 0.776 | 0.785 ± 0.113 | 0.797 ± 0.106 |
| 50 | 50 | OutcomeModelTransport | 4.828 ± 1.594 | 1.147 ± 1.133 | 0.836 ± 0.091 | 0.847 ± 0.086 |
| 50 | 50 | OutcomeModelTransport | 3.166 ± 1.596 | 1.126 ± 0.803 | 0.841 ± 0.152 | 0.850 ± 0.146 |
| 50 | 50 | OutcomeModelTransport | 2.499 ± 1.994 | 0.859 ± 1.043 | 0.754 ± 0.269 | 0.767 ± 0.265 |
| 50 | 50 | OutcomeModelTransport | 1.776 ± 0.234 | 0.772 ± 0.776 | 0.784 ± 0.113 | 0.796 ± 0.107 |
| 50 | 50 | ProxyOnly | 8.849 ± 1.144 | 1.829 ± 1.499 | 0.179 ± 0.046 | 0.183 ± 0.050 |
| 50 | 50 | ProxyOnly | 5.685 ± 0.699 | 1.661 ± 1.186 | 0.373 ± 0.052 | 0.386 ± 0.057 |
| 50 | 50 | ProxyOnly | 3.346 ± 0.880 | 0.736 ± 0.638 | 0.489 ± 0.087 | 0.507 ± 0.089 |
| 50 | 50 | ProxyOnly | 2.269 ± 0.877 | 0.903 ± 0.836 | 0.557 ± 0.166 | 0.567 ± 0.164 |
| 50 | 50 | TargetOnlyDR | 8.200 ± 0.984 | 1.011 ± 0.546 | 0.359 ± 0.093 | 0.371 ± 0.091 |
| 50 | 50 | TargetOnlyDR | 5.155 ± 0.565 | 0.647 ± 0.416 | 0.442 ± 0.073 | 0.460 ± 0.074 |
| 50 | 50 | TargetOnlyDR | 2.705 ± 0.478 | 0.238 ± 0.286 | 0.706 ± 0.054 | 0.724 ± 0.049 |
| 50 | 50 | TargetOnlyDR | 1.579 ± 0.414 | 0.272 ± 0.113 | 0.754 ± 0.066 | 0.765 ± 0.065 |
| 100 | 100 | AnchorOnly | 2.895 ± 0.206 | 0.303 ± 0.271 | 0.744 ± 0.083 | 0.759 ± 0.080 |
| 100 | 100 | AnchorOnly | 5.493 ± 1.162 | 0.369 ± 0.236 | 0.558 ± 0.089 | 0.576 ± 0.086 |
| 100 | 100 | AnchorOnly | 1.722 ± 0.635 | 0.095 ± 0.049 | 0.855 ± 0.044 | 0.863 ± 0.040 |
| 100 | 100 | AnchorOnly | 7.330 ± 0.591 | 0.398 ± 0.290 | 0.411 ± 0.069 | 0.429 ± 0.071 |
| 100 | 100 | AnchorPlugin | 2.421 ± 0.583 | 0.374 ± 0.210 | 0.787 ± 0.096 | 0.799 ± 0.094 |
| 100 | 100 | AnchorPlugin | 4.929 ± 1.672 | 1.556 ± 0.877 | 0.678 ± 0.194 | 0.692 ± 0.192 |
| 100 | 100 | AnchorPlugin | 1.955 ± 1.108 | 0.440 ± 0.400 | 0.776 ± 0.201 | 0.787 ± 0.194 |
| 100 | 100 | AnchorPlugin | 6.367 ± 1.138 | 1.408 ± 2.021 | 0.646 ± 0.028 | 0.664 ± 0.030 |
| 100 | 100 | EntropyBalancing | 2.470 ± 0.823 | 0.623 ± 0.329 | 0.778 ± 0.163 | 0.790 ± 0.160 |
| 100 | 100 | EntropyBalancing | 4.415 ± 2.625 | 1.824 ± 1.529 | 0.753 ± 0.244 | 0.766 ± 0.238 |
| 100 | 100 | EntropyBalancing | 1.975 ± 0.997 | 0.357 ± 0.407 | 0.780 ± 0.179 | 0.792 ± 0.170 |
| 100 | 100 | EntropyBalancing | 4.357 ± 0.966 | 0.778 ± 0.640 | 0.836 ± 0.064 | 0.848 ± 0.061 |
| 100 | 100 | Glmtrans_Auto | 0.639 ± 0.190 | 0.102 ± 0.034 | 0.988 ± 0.007 | 0.989 ± 0.006 |
| 100 | 100 | Glmtrans_Auto | 0.812 ± 0.089 | 0.082 ± 0.085 | 0.991 ± 0.003 | 0.992 ± 0.003 |
| 100 | 100 | Glmtrans_Auto | 0.397 ± 0.162 | 0.063 ± 0.055 | 0.992 ± 0.006 | 0.992 ± 0.006 |
| 100 | 100 | Glmtrans_Auto | 1.583 ± 0.689 | 0.162 ± 0.106 | 0.976 ± 0.017 | 0.979 ± 0.016 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.609 ± 0.105 | 0.086 ± 0.040 | 0.988 ± 0.005 | 0.989 ± 0.004 |
| 100 | 100 | Glmtrans_DR_CrossFit | 1.482 ± 0.654 | 0.217 ± 0.073 | 0.973 ± 0.017 | 0.975 ± 0.016 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.393 ± 0.164 | 0.081 ± 0.065 | 0.990 ± 0.009 | 0.991 ± 0.008 |
| 100 | 100 | Glmtrans_DR_CrossFit | 3.040 ± 1.158 | 0.254 ± 0.282 | 0.914 ± 0.054 | 0.922 ± 0.049 |
| 100 | 100 | Glmtrans_OptionB | 2.462 ± 0.813 | 0.604 ± 0.346 | 0.779 ± 0.160 | 0.791 ± 0.157 |
| 100 | 100 | Glmtrans_OptionB | 3.235 ± 1.561 | 1.513 ± 1.256 | 0.899 ± 0.055 | 0.907 ± 0.051 |
| 100 | 100 | Glmtrans_OptionB | 1.987 ± 1.045 | 0.391 ± 0.391 | 0.770 ± 0.191 | 0.782 ± 0.182 |
| 100 | 100 | Glmtrans_OptionB | 3.516 ± 1.420 | 0.759 ± 0.635 | 0.887 ± 0.078 | 0.896 ± 0.074 |
| 100 | 100 | IPWTransport | 2.468 ± 0.815 | 0.617 ± 0.345 | 0.778 ± 0.161 | 0.790 ± 0.158 |
| 100 | 100 | IPWTransport | 4.304 ± 2.620 | 1.926 ± 1.653 | 0.777 ± 0.241 | 0.789 ± 0.234 |
| 100 | 100 | IPWTransport | 1.989 ± 1.024 | 0.361 ± 0.422 | 0.772 ± 0.187 | 0.784 ± 0.178 |
| 100 | 100 | IPWTransport | 3.690 ± 1.274 | 0.758 ± 0.616 | 0.878 ± 0.072 | 0.888 ± 0.069 |
| 100 | 100 | OutcomeModelTransport | 2.462 ± 0.816 | 0.604 ± 0.345 | 0.779 ± 0.160 | 0.791 ± 0.157 |
| 100 | 100 | OutcomeModelTransport | 3.984 ± 2.486 | 1.664 ± 1.324 | 0.798 ± 0.244 | 0.809 ± 0.238 |
| 100 | 100 | OutcomeModelTransport | 1.994 ± 1.029 | 0.338 ± 0.424 | 0.769 ± 0.189 | 0.781 ± 0.181 |
| 100 | 100 | OutcomeModelTransport | 3.512 ± 1.418 | 0.757 ± 0.620 | 0.887 ± 0.078 | 0.896 ± 0.074 |
| 100 | 100 | ProxyOnly | 3.350 ± 0.445 | 0.547 ± 0.502 | 0.571 ± 0.095 | 0.590 ± 0.091 |
| 100 | 100 | ProxyOnly | 5.970 ± 1.133 | 1.079 ± 1.033 | 0.423 ± 0.113 | 0.437 ± 0.110 |
| 100 | 100 | ProxyOnly | 2.429 ± 1.145 | 0.384 ± 0.173 | 0.642 ± 0.265 | 0.653 ± 0.263 |
| 100 | 100 | ProxyOnly | 7.741 ± 0.547 | 1.383 ± 0.620 | 0.303 ± 0.058 | 0.317 ± 0.055 |
| 100 | 100 | TargetOnlyDR | 2.879 ± 0.205 | 0.309 ± 0.305 | 0.748 ± 0.097 | 0.761 ± 0.093 |
| 100 | 100 | TargetOnlyDR | 5.448 ± 1.166 | 0.370 ± 0.167 | 0.559 ± 0.080 | 0.574 ± 0.084 |
| 100 | 100 | TargetOnlyDR | 1.640 ± 0.511 | 0.104 ± 0.064 | 0.866 ± 0.055 | 0.873 ± 0.050 |
| 100 | 100 | TargetOnlyDR | 7.242 ± 0.559 | 0.227 ± 0.175 | 0.458 ± 0.037 | 0.475 ± 0.035 |
| 200 | 200 | AnchorOnly | 2.480 ± 0.596 | 0.142 ± 0.105 | 0.783 ± 0.045 | 0.797 ± 0.040 |
| 200 | 200 | AnchorOnly | 4.546 ± 0.981 | 0.350 ± 0.112 | 0.654 ± 0.054 | 0.669 ± 0.050 |
| 200 | 200 | AnchorOnly | 8.104 ± 1.737 | 0.307 ± 0.180 | 0.507 ± 0.072 | 0.523 ± 0.072 |
| 200 | 200 | AnchorOnly | 1.284 ± 0.565 | 0.086 ± 0.042 | 0.872 ± 0.013 | 0.880 ± 0.011 |
| 200 | 200 | AnchorPlugin | 2.199 ± 0.922 | 0.534 ± 0.443 | 0.812 ± 0.121 | 0.823 ± 0.116 |
| 200 | 200 | AnchorPlugin | 3.540 ± 1.014 | 0.566 ± 0.273 | 0.789 ± 0.049 | 0.803 ± 0.046 |
| 200 | 200 | AnchorPlugin | 7.362 ± 2.520 | 1.835 ± 0.827 | 0.628 ± 0.185 | 0.642 ± 0.184 |
| 200 | 200 | AnchorPlugin | 1.665 ± 1.112 | 0.500 ± 0.448 | 0.783 ± 0.171 | 0.794 ± 0.167 |
| 200 | 200 | EntropyBalancing | 2.188 ± 1.089 | 0.905 ± 0.624 | 0.847 ± 0.197 | 0.856 ± 0.190 |
| 200 | 200 | EntropyBalancing | 2.489 ± 1.360 | 0.499 ± 0.365 | 0.894 ± 0.076 | 0.902 ± 0.072 |
| 200 | 200 | EntropyBalancing | 6.031 ± 3.304 | 0.611 ± 0.693 | 0.738 ± 0.223 | 0.750 ± 0.220 |
| 200 | 200 | EntropyBalancing | 1.723 ± 1.132 | 0.586 ± 0.317 | 0.788 ± 0.224 | 0.798 ± 0.221 |
| 200 | 200 | Glmtrans_Auto | 0.368 ± 0.107 | 0.041 ± 0.026 | 0.994 ± 0.003 | 0.995 ± 0.003 |
| 200 | 200 | Glmtrans_Auto | 0.642 ± 0.203 | 0.049 ± 0.054 | 0.993 ± 0.003 | 0.994 ± 0.003 |
| 200 | 200 | Glmtrans_Auto | 0.911 ± 0.157 | 0.064 ± 0.034 | 0.995 ± 0.002 | 0.995 ± 0.002 |
| 200 | 200 | Glmtrans_Auto | 0.415 ± 0.188 | 0.038 ± 0.024 | 0.986 ± 0.005 | 0.987 ± 0.005 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.335 ± 0.076 | 0.042 ± 0.036 | 0.995 ± 0.003 | 0.996 ± 0.003 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.601 ± 0.191 | 0.056 ± 0.034 | 0.993 ± 0.003 | 0.994 ± 0.003 |
| 200 | 200 | Glmtrans_DR_CrossFit | 1.378 ± 0.417 | 0.093 ± 0.063 | 0.988 ± 0.004 | 0.989 ± 0.004 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.396 ± 0.179 | 0.046 ± 0.027 | 0.987 ± 0.004 | 0.988 ± 0.004 |
| 200 | 200 | Glmtrans_OptionB | 2.151 ± 1.109 | 0.875 ± 0.591 | 0.848 ± 0.198 | 0.857 ± 0.191 |
| 200 | 200 | Glmtrans_OptionB | 2.913 ± 0.828 | 0.616 ± 0.287 | 0.869 ± 0.045 | 0.879 ± 0.043 |
| 200 | 200 | Glmtrans_OptionB | 4.971 ± 2.674 | 0.785 ± 0.720 | 0.838 ± 0.128 | 0.849 ± 0.122 |
| 200 | 200 | Glmtrans_OptionB | 1.513 ± 1.133 | 0.536 ± 0.362 | 0.815 ± 0.237 | 0.823 ± 0.233 |
| 200 | 200 | IPWTransport | 2.184 ± 1.080 | 0.900 ± 0.628 | 0.848 ± 0.197 | 0.857 ± 0.189 |
| 200 | 200 | IPWTransport | 2.363 ± 1.409 | 0.483 ± 0.340 | 0.902 ± 0.077 | 0.910 ± 0.072 |
| 200 | 200 | IPWTransport | 5.669 ± 3.493 | 0.569 ± 0.783 | 0.765 ± 0.229 | 0.775 ± 0.225 |
| 200 | 200 | IPWTransport | 1.730 ± 1.129 | 0.593 ± 0.306 | 0.786 ± 0.222 | 0.797 ± 0.219 |
| 200 | 200 | OutcomeModelTransport | 2.196 ± 1.080 | 0.927 ± 0.640 | 0.849 ± 0.199 | 0.857 ± 0.191 |
| 200 | 200 | OutcomeModelTransport | 2.254 ± 1.467 | 0.538 ± 0.351 | 0.910 ± 0.077 | 0.917 ± 0.072 |
| 200 | 200 | OutcomeModelTransport | 5.612 ± 3.546 | 0.879 ± 0.657 | 0.769 ± 0.230 | 0.780 ± 0.225 |
| 200 | 200 | OutcomeModelTransport | 1.716 ± 1.148 | 0.557 ± 0.325 | 0.786 ± 0.223 | 0.796 ± 0.220 |
| 200 | 200 | ProxyOnly | 2.981 ± 0.709 | 0.548 ± 0.382 | 0.636 ± 0.082 | 0.652 ± 0.078 |
| 200 | 200 | ProxyOnly | 5.072 ± 1.127 | 0.672 ± 0.836 | 0.537 ± 0.065 | 0.554 ± 0.063 |
| 200 | 200 | ProxyOnly | 9.133 ± 1.450 | 2.384 ± 1.858 | 0.378 ± 0.077 | 0.393 ± 0.083 |
| 200 | 200 | ProxyOnly | 2.109 ± 1.101 | 0.708 ± 0.580 | 0.650 ± 0.108 | 0.669 ± 0.102 |
| 200 | 200 | TargetOnlyDR | 2.445 ± 0.540 | 0.130 ± 0.087 | 0.801 ± 0.031 | 0.813 ± 0.028 |
| 200 | 200 | TargetOnlyDR | 4.504 ± 0.988 | 0.316 ± 0.144 | 0.673 ± 0.031 | 0.690 ± 0.030 |
| 200 | 200 | TargetOnlyDR | 7.992 ± 1.611 | 0.235 ± 0.175 | 0.525 ± 0.034 | 0.542 ± 0.035 |
| 200 | 200 | TargetOnlyDR | 1.280 ± 0.595 | 0.096 ± 0.048 | 0.879 ± 0.007 | 0.886 ± 0.005 |
| 500 | 500 | AnchorOnly | 7.682 ± 1.433 | 0.372 ± 0.329 | 0.567 ± 0.041 | 0.585 ± 0.043 |
| 500 | 500 | AnchorOnly | 4.530 ± 0.842 | 0.240 ± 0.209 | 0.673 ± 0.030 | 0.685 ± 0.029 |
| 500 | 500 | AnchorOnly | 1.247 ± 0.321 | 0.035 ± 0.026 | 0.885 ± 0.026 | 0.894 ± 0.022 |
| 500 | 500 | AnchorOnly | 2.620 ± 0.501 | 0.218 ± 0.136 | 0.799 ± 0.022 | 0.814 ± 0.021 |
| 500 | 500 | AnchorPlugin | 6.393 ± 2.112 | 0.959 ± 0.428 | 0.697 ± 0.114 | 0.714 ± 0.109 |
| 500 | 500 | AnchorPlugin | 3.549 ± 0.821 | 0.379 ± 0.313 | 0.776 ± 0.101 | 0.790 ± 0.097 |
| 500 | 500 | AnchorPlugin | 1.421 ± 0.426 | 0.406 ± 0.179 | 0.866 ± 0.050 | 0.876 ± 0.046 |
| 500 | 500 | AnchorPlugin | 3.033 ± 1.031 | 0.259 ± 0.164 | 0.664 ± 0.159 | 0.679 ± 0.157 |
| 500 | 500 | EntropyBalancing | 5.664 ± 2.372 | 0.881 ± 0.800 | 0.782 ± 0.110 | 0.794 ± 0.108 |
| 500 | 500 | EntropyBalancing | 2.688 ± 1.593 | 0.919 ± 0.675 | 0.861 ± 0.186 | 0.867 ± 0.180 |
| 500 | 500 | EntropyBalancing | 1.536 ± 0.658 | 0.710 ± 0.361 | 0.885 ± 0.045 | 0.895 ± 0.041 |
| 500 | 500 | EntropyBalancing | 3.014 ± 1.183 | 0.886 ± 0.446 | 0.690 ± 0.232 | 0.705 ± 0.225 |
| 500 | 500 | Glmtrans_Auto | 0.509 ± 0.058 | 0.030 ± 0.019 | 0.998 ± 0.001 | 0.999 ± 0.001 |
| 500 | 500 | Glmtrans_Auto | 0.453 ± 0.084 | 0.023 ± 0.010 | 0.996 ± 0.003 | 0.997 ± 0.002 |
| 500 | 500 | Glmtrans_Auto | 0.333 ± 0.129 | 0.032 ± 0.028 | 0.991 ± 0.009 | 0.991 ± 0.008 |
| 500 | 500 | Glmtrans_Auto | 0.273 ± 0.065 | 0.035 ± 0.018 | 0.998 ± 0.001 | 0.998 ± 0.001 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.452 ± 0.016 | 0.026 ± 0.016 | 0.998 ± 0.000 | 0.999 ± 0.000 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.417 ± 0.084 | 0.028 ± 0.017 | 0.997 ± 0.003 | 0.997 ± 0.002 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.322 ± 0.133 | 0.039 ± 0.030 | 0.991 ± 0.009 | 0.992 ± 0.009 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.265 ± 0.062 | 0.030 ± 0.019 | 0.998 ± 0.001 | 0.998 ± 0.001 |
| 500 | 500 | Glmtrans_OptionB | 4.876 ± 2.649 | 0.935 ± 0.799 | 0.833 ± 0.126 | 0.843 ± 0.123 |
| 500 | 500 | Glmtrans_OptionB | 2.902 ± 1.152 | 1.070 ± 0.633 | 0.862 ± 0.144 | 0.869 ± 0.139 |
| 500 | 500 | Glmtrans_OptionB | 1.399 ± 0.670 | 0.653 ± 0.312 | 0.909 ± 0.046 | 0.918 ± 0.042 |
| 500 | 500 | Glmtrans_OptionB | 2.961 ± 1.101 | 0.882 ± 0.428 | 0.708 ± 0.207 | 0.723 ± 0.200 |
| 500 | 500 | IPWTransport | 5.366 ± 2.390 | 0.925 ± 0.821 | 0.803 ± 0.108 | 0.814 ± 0.105 |
| 500 | 500 | IPWTransport | 2.659 ± 1.556 | 0.914 ± 0.649 | 0.865 ± 0.179 | 0.872 ± 0.173 |
| 500 | 500 | IPWTransport | 1.537 ± 0.659 | 0.711 ± 0.361 | 0.886 ± 0.045 | 0.896 ± 0.040 |
| 500 | 500 | IPWTransport | 3.009 ± 1.174 | 0.888 ± 0.453 | 0.692 ± 0.229 | 0.707 ± 0.222 |
| 500 | 500 | OutcomeModelTransport | 4.881 ± 2.650 | 0.938 ± 0.806 | 0.833 ± 0.126 | 0.843 ± 0.123 |
| 500 | 500 | OutcomeModelTransport | 2.575 ± 1.456 | 0.945 ± 0.725 | 0.879 ± 0.154 | 0.886 ± 0.149 |
| 500 | 500 | OutcomeModelTransport | 1.520 ± 0.645 | 0.705 ± 0.356 | 0.896 ± 0.032 | 0.905 ± 0.028 |
| 500 | 500 | OutcomeModelTransport | 2.959 ± 1.103 | 0.880 ± 0.424 | 0.708 ± 0.207 | 0.723 ± 0.200 |
| 500 | 500 | ProxyOnly | 8.441 ± 1.649 | 1.961 ± 0.562 | 0.433 ± 0.061 | 0.444 ± 0.060 |
| 500 | 500 | ProxyOnly | 4.894 ± 0.793 | 0.461 ± 0.341 | 0.571 ± 0.061 | 0.589 ± 0.060 |
| 500 | 500 | ProxyOnly | 1.863 ± 0.432 | 0.456 ± 0.578 | 0.734 ± 0.134 | 0.747 ± 0.129 |
| 500 | 500 | ProxyOnly | 3.665 ± 0.937 | 0.681 ± 0.322 | 0.514 ± 0.160 | 0.532 ± 0.162 |
| 500 | 500 | TargetOnlyDR | 7.636 ± 1.403 | 0.390 ± 0.162 | 0.573 ± 0.056 | 0.591 ± 0.056 |
| 500 | 500 | TargetOnlyDR | 4.457 ± 0.807 | 0.214 ± 0.206 | 0.693 ± 0.034 | 0.707 ± 0.034 |
| 500 | 500 | TargetOnlyDR | 1.253 ± 0.336 | 0.045 ± 0.040 | 0.884 ± 0.032 | 0.893 ± 0.028 |
| 500 | 500 | TargetOnlyDR | 2.584 ± 0.485 | 0.189 ± 0.093 | 0.802 ± 0.008 | 0.817 ± 0.008 |

### Targeting / Ranking Metrics

| m0 | m1 | Method | Top-10% (↑) | Top-20% (↑) | Kendall (↑) |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 0.366 ± 0.204 | 0.379 ± 0.235 | 0.255 ± 0.029 |
| 50 | 50 | AnchorOnly | 0.418 ± 0.274 | 0.443 ± 0.248 | 0.333 ± 0.063 |
| 50 | 50 | AnchorOnly | 0.637 ± 0.182 | 0.619 ± 0.182 | 0.497 ± 0.036 |
| 50 | 50 | AnchorOnly | 0.815 ± 0.045 | 0.805 ± 0.046 | 0.598 ± 0.025 |
| 50 | 50 | AnchorPlugin | 0.531 ± 0.167 | 0.543 ± 0.185 | 0.373 ± 0.068 |
| 50 | 50 | AnchorPlugin | 0.619 ± 0.169 | 0.613 ± 0.161 | 0.443 ± 0.089 |
| 50 | 50 | AnchorPlugin | 0.717 ± 0.140 | 0.693 ± 0.175 | 0.552 ± 0.086 |
| 50 | 50 | AnchorPlugin | 0.800 ± 0.123 | 0.782 ± 0.143 | 0.592 ± 0.127 |
| 50 | 50 | EntropyBalancing | 0.765 ± 0.169 | 0.766 ± 0.201 | 0.596 ± 0.127 |
| 50 | 50 | EntropyBalancing | 0.834 ± 0.163 | 0.838 ± 0.169 | 0.671 ± 0.159 |
| 50 | 50 | EntropyBalancing | 0.705 ± 0.434 | 0.671 ± 0.501 | 0.609 ± 0.255 |
| 50 | 50 | EntropyBalancing | 0.823 ± 0.081 | 0.822 ± 0.098 | 0.612 ± 0.124 |
| 50 | 50 | Glmtrans_Auto | 0.901 ± 0.060 | 0.879 ± 0.086 | 0.715 ± 0.090 |
| 50 | 50 | Glmtrans_Auto | 0.964 ± 0.030 | 0.960 ± 0.034 | 0.836 ± 0.062 |
| 50 | 50 | Glmtrans_Auto | 0.984 ± 0.004 | 0.983 ± 0.006 | 0.895 ± 0.024 |
| 50 | 50 | Glmtrans_Auto | 0.974 ± 0.021 | 0.976 ± 0.016 | 0.866 ± 0.076 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.646 ± 0.130 | 0.635 ± 0.141 | 0.459 ± 0.046 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.896 ± 0.050 | 0.899 ± 0.054 | 0.719 ± 0.059 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.965 ± 0.013 | 0.964 ± 0.013 | 0.847 ± 0.046 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.959 ± 0.033 | 0.960 ± 0.036 | 0.837 ± 0.077 |
| 50 | 50 | Glmtrans_OptionB | 0.805 ± 0.157 | 0.827 ± 0.136 | 0.653 ± 0.100 |
| 50 | 50 | Glmtrans_OptionB | 0.846 ± 0.160 | 0.830 ± 0.190 | 0.677 ± 0.171 |
| 50 | 50 | Glmtrans_OptionB | 0.806 ± 0.233 | 0.785 ± 0.265 | 0.660 ± 0.188 |
| 50 | 50 | Glmtrans_OptionB | 0.887 ± 0.079 | 0.891 ± 0.073 | 0.704 ± 0.085 |
| 50 | 50 | IPWTransport | 0.810 ± 0.156 | 0.820 ± 0.140 | 0.649 ± 0.102 |
| 50 | 50 | IPWTransport | 0.852 ± 0.154 | 0.836 ± 0.184 | 0.680 ± 0.169 |
| 50 | 50 | IPWTransport | 0.723 ± 0.405 | 0.666 ± 0.499 | 0.602 ± 0.249 |
| 50 | 50 | IPWTransport | 0.816 ± 0.094 | 0.814 ± 0.107 | 0.602 ± 0.129 |
| 50 | 50 | OutcomeModelTransport | 0.806 ± 0.159 | 0.827 ± 0.137 | 0.653 ± 0.100 |
| 50 | 50 | OutcomeModelTransport | 0.845 ± 0.163 | 0.829 ± 0.190 | 0.677 ± 0.171 |
| 50 | 50 | OutcomeModelTransport | 0.723 ± 0.402 | 0.663 ± 0.501 | 0.601 ± 0.247 |
| 50 | 50 | OutcomeModelTransport | 0.814 ± 0.095 | 0.814 ± 0.110 | 0.602 ± 0.129 |
| 50 | 50 | ProxyOnly | 0.175 ± 0.130 | 0.173 ± 0.162 | 0.120 ± 0.031 |
| 50 | 50 | ProxyOnly | 0.366 ± 0.152 | 0.377 ± 0.148 | 0.254 ± 0.037 |
| 50 | 50 | ProxyOnly | 0.393 ± 0.193 | 0.355 ± 0.250 | 0.341 ± 0.068 |
| 50 | 50 | ProxyOnly | 0.524 ± 0.165 | 0.559 ± 0.205 | 0.399 ± 0.142 |
| 50 | 50 | TargetOnlyDR | 0.373 ± 0.158 | 0.382 ± 0.190 | 0.245 ± 0.066 |
| 50 | 50 | TargetOnlyDR | 0.418 ± 0.226 | 0.434 ± 0.236 | 0.305 ± 0.053 |
| 50 | 50 | TargetOnlyDR | 0.698 ± 0.070 | 0.675 ± 0.106 | 0.516 ± 0.048 |
| 50 | 50 | TargetOnlyDR | 0.773 ± 0.063 | 0.783 ± 0.037 | 0.562 ± 0.061 |
| 100 | 100 | AnchorOnly | 0.753 ± 0.112 | 0.768 ± 0.116 | 0.553 ± 0.076 |
| 100 | 100 | AnchorOnly | 0.551 ± 0.131 | 0.564 ± 0.115 | 0.394 ± 0.071 |
| 100 | 100 | AnchorOnly | 0.815 ± 0.143 | 0.838 ± 0.085 | 0.671 ± 0.052 |
| 100 | 100 | AnchorOnly | 0.503 ± 0.071 | 0.505 ± 0.091 | 0.282 ± 0.051 |
| 100 | 100 | AnchorPlugin | 0.806 ± 0.108 | 0.812 ± 0.092 | 0.598 ± 0.094 |
| 100 | 100 | AnchorPlugin | 0.670 ± 0.207 | 0.654 ± 0.213 | 0.501 ± 0.158 |
| 100 | 100 | AnchorPlugin | 0.739 ± 0.273 | 0.708 ± 0.370 | 0.610 ± 0.195 |
| 100 | 100 | AnchorPlugin | 0.693 ± 0.079 | 0.692 ± 0.095 | 0.462 ± 0.025 |
| 100 | 100 | EntropyBalancing | 0.813 ± 0.136 | 0.807 ± 0.144 | 0.600 ± 0.154 |
| 100 | 100 | EntropyBalancing | 0.771 ± 0.247 | 0.759 ± 0.244 | 0.593 ± 0.226 |
| 100 | 100 | EntropyBalancing | 0.737 ± 0.244 | 0.724 ± 0.264 | 0.618 ± 0.203 |
| 100 | 100 | EntropyBalancing | 0.856 ± 0.056 | 0.853 ± 0.055 | 0.650 ± 0.078 |
| 100 | 100 | Glmtrans_Auto | 0.991 ± 0.006 | 0.991 ± 0.004 | 0.911 ± 0.024 |
| 100 | 100 | Glmtrans_Auto | 0.992 ± 0.004 | 0.989 ± 0.007 | 0.921 ± 0.016 |
| 100 | 100 | Glmtrans_Auto | 0.991 ± 0.009 | 0.992 ± 0.007 | 0.930 ± 0.028 |
| 100 | 100 | Glmtrans_Auto | 0.982 ± 0.013 | 0.981 ± 0.015 | 0.875 ± 0.049 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.993 ± 0.003 | 0.991 ± 0.003 | 0.911 ± 0.017 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.973 ± 0.018 | 0.969 ± 0.022 | 0.863 ± 0.040 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.989 ± 0.010 | 0.990 ± 0.007 | 0.927 ± 0.036 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.931 ± 0.049 | 0.931 ± 0.051 | 0.757 ± 0.084 |
| 100 | 100 | Glmtrans_OptionB | 0.818 ± 0.134 | 0.811 ± 0.140 | 0.600 ± 0.153 |
| 100 | 100 | Glmtrans_OptionB | 0.916 ± 0.034 | 0.908 ± 0.042 | 0.736 ± 0.092 |
| 100 | 100 | Glmtrans_OptionB | 0.735 ± 0.243 | 0.711 ± 0.294 | 0.615 ± 0.220 |
| 100 | 100 | Glmtrans_OptionB | 0.908 ± 0.062 | 0.904 ± 0.062 | 0.726 ± 0.120 |
| 100 | 100 | IPWTransport | 0.817 ± 0.131 | 0.810 ± 0.142 | 0.600 ± 0.154 |
| 100 | 100 | IPWTransport | 0.802 ± 0.237 | 0.778 ± 0.242 | 0.619 ± 0.226 |
| 100 | 100 | IPWTransport | 0.739 ± 0.243 | 0.712 ± 0.290 | 0.612 ± 0.210 |
| 100 | 100 | IPWTransport | 0.899 ± 0.056 | 0.891 ± 0.062 | 0.710 ± 0.109 |
| 100 | 100 | OutcomeModelTransport | 0.819 ± 0.133 | 0.812 ± 0.139 | 0.601 ± 0.153 |
| 100 | 100 | OutcomeModelTransport | 0.805 ± 0.247 | 0.801 ± 0.239 | 0.644 ± 0.229 |
| 100 | 100 | OutcomeModelTransport | 0.734 ± 0.242 | 0.710 ± 0.293 | 0.610 ± 0.212 |
| 100 | 100 | OutcomeModelTransport | 0.909 ± 0.062 | 0.904 ± 0.063 | 0.726 ± 0.120 |
| 100 | 100 | ProxyOnly | 0.659 ± 0.098 | 0.658 ± 0.100 | 0.404 ± 0.076 |
| 100 | 100 | ProxyOnly | 0.371 ± 0.204 | 0.337 ± 0.272 | 0.290 ± 0.082 |
| 100 | 100 | ProxyOnly | 0.567 ± 0.436 | 0.513 ± 0.535 | 0.478 ± 0.211 |
| 100 | 100 | ProxyOnly | 0.348 ± 0.159 | 0.366 ± 0.139 | 0.205 ± 0.039 |
| 100 | 100 | TargetOnlyDR | 0.738 ± 0.111 | 0.768 ± 0.097 | 0.557 ± 0.089 |
| 100 | 100 | TargetOnlyDR | 0.550 ± 0.095 | 0.542 ± 0.115 | 0.393 ± 0.062 |
| 100 | 100 | TargetOnlyDR | 0.830 ± 0.057 | 0.852 ± 0.046 | 0.686 ± 0.065 |
| 100 | 100 | TargetOnlyDR | 0.488 ± 0.122 | 0.518 ± 0.121 | 0.316 ± 0.027 |
| 200 | 200 | AnchorOnly | 0.779 ± 0.124 | 0.746 ± 0.208 | 0.590 ± 0.043 |
| 200 | 200 | AnchorOnly | 0.641 ± 0.111 | 0.641 ± 0.115 | 0.469 ± 0.045 |
| 200 | 200 | AnchorOnly | 0.541 ± 0.073 | 0.535 ± 0.119 | 0.353 ± 0.054 |
| 200 | 200 | AnchorOnly | 0.884 ± 0.036 | 0.891 ± 0.041 | 0.689 ± 0.015 |
| 200 | 200 | AnchorPlugin | 0.810 ± 0.118 | 0.772 ± 0.177 | 0.630 ± 0.119 |
| 200 | 200 | AnchorPlugin | 0.774 ± 0.046 | 0.778 ± 0.049 | 0.594 ± 0.049 |
| 200 | 200 | AnchorPlugin | 0.688 ± 0.153 | 0.678 ± 0.152 | 0.457 ± 0.151 |
| 200 | 200 | AnchorPlugin | 0.838 ± 0.137 | 0.821 ± 0.151 | 0.612 ± 0.170 |
| 200 | 200 | EntropyBalancing | 0.858 ± 0.137 | 0.861 ± 0.137 | 0.694 ± 0.199 |
| 200 | 200 | EntropyBalancing | 0.901 ± 0.072 | 0.896 ± 0.072 | 0.734 ± 0.113 |
| 200 | 200 | EntropyBalancing | 0.785 ± 0.169 | 0.781 ± 0.165 | 0.570 ± 0.203 |
| 200 | 200 | EntropyBalancing | 0.823 ± 0.199 | 0.826 ± 0.192 | 0.623 ± 0.203 |
| 200 | 200 | Glmtrans_Auto | 0.994 ± 0.005 | 0.994 ± 0.005 | 0.941 ± 0.021 |
| 200 | 200 | Glmtrans_Auto | 0.993 ± 0.006 | 0.993 ± 0.004 | 0.933 ± 0.015 |
| 200 | 200 | Glmtrans_Auto | 0.994 ± 0.003 | 0.995 ± 0.002 | 0.939 ± 0.012 |
| 200 | 200 | Glmtrans_Auto | 0.988 ± 0.008 | 0.987 ± 0.009 | 0.909 ± 0.022 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.995 ± 0.005 | 0.994 ± 0.005 | 0.944 ± 0.018 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.992 ± 0.006 | 0.993 ± 0.003 | 0.934 ± 0.017 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.988 ± 0.004 | 0.990 ± 0.003 | 0.907 ± 0.016 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.990 ± 0.004 | 0.989 ± 0.005 | 0.912 ± 0.019 |
| 200 | 200 | Glmtrans_OptionB | 0.860 ± 0.136 | 0.867 ± 0.135 | 0.697 ± 0.202 |
| 200 | 200 | Glmtrans_OptionB | 0.861 ± 0.038 | 0.858 ± 0.033 | 0.687 ± 0.055 |
| 200 | 200 | Glmtrans_OptionB | 0.869 ± 0.085 | 0.865 ± 0.099 | 0.667 ± 0.147 |
| 200 | 200 | Glmtrans_OptionB | 0.848 ± 0.210 | 0.850 ± 0.200 | 0.663 ± 0.225 |
| 200 | 200 | IPWTransport | 0.861 ± 0.132 | 0.865 ± 0.136 | 0.696 ± 0.200 |
| 200 | 200 | IPWTransport | 0.909 ± 0.069 | 0.902 ± 0.073 | 0.749 ± 0.120 |
| 200 | 200 | IPWTransport | 0.807 ± 0.171 | 0.808 ± 0.173 | 0.604 ± 0.221 |
| 200 | 200 | IPWTransport | 0.823 ± 0.198 | 0.828 ± 0.190 | 0.621 ± 0.201 |
| 200 | 200 | OutcomeModelTransport | 0.861 ± 0.137 | 0.865 ± 0.135 | 0.698 ± 0.203 |
| 200 | 200 | OutcomeModelTransport | 0.909 ± 0.075 | 0.907 ± 0.077 | 0.765 ± 0.128 |
| 200 | 200 | OutcomeModelTransport | 0.816 ± 0.160 | 0.801 ± 0.187 | 0.612 ± 0.228 |
| 200 | 200 | OutcomeModelTransport | 0.822 ± 0.197 | 0.826 ± 0.191 | 0.620 ± 0.202 |
| 200 | 200 | ProxyOnly | 0.542 ± 0.297 | 0.485 ± 0.498 | 0.456 ± 0.070 |
| 200 | 200 | ProxyOnly | 0.516 ± 0.115 | 0.527 ± 0.109 | 0.375 ± 0.050 |
| 200 | 200 | ProxyOnly | 0.428 ± 0.047 | 0.440 ± 0.065 | 0.258 ± 0.055 |
| 200 | 200 | ProxyOnly | 0.729 ± 0.112 | 0.708 ± 0.114 | 0.472 ± 0.090 |
| 200 | 200 | TargetOnlyDR | 0.778 ± 0.150 | 0.734 ± 0.228 | 0.608 ± 0.032 |
| 200 | 200 | TargetOnlyDR | 0.670 ± 0.075 | 0.670 ± 0.080 | 0.486 ± 0.027 |
| 200 | 200 | TargetOnlyDR | 0.580 ± 0.071 | 0.554 ± 0.084 | 0.366 ± 0.025 |
| 200 | 200 | TargetOnlyDR | 0.904 ± 0.030 | 0.906 ± 0.023 | 0.696 ± 0.008 |
| 500 | 500 | AnchorOnly | 0.596 ± 0.109 | 0.583 ± 0.153 | 0.398 ± 0.032 |
| 500 | 500 | AnchorOnly | 0.646 ± 0.059 | 0.629 ± 0.080 | 0.485 ± 0.026 |
| 500 | 500 | AnchorOnly | 0.882 ± 0.022 | 0.891 ± 0.043 | 0.706 ± 0.035 |
| 500 | 500 | AnchorOnly | 0.794 ± 0.051 | 0.786 ± 0.084 | 0.606 ± 0.022 |
| 500 | 500 | AnchorPlugin | 0.707 ± 0.128 | 0.715 ± 0.124 | 0.511 ± 0.095 |
| 500 | 500 | AnchorPlugin | 0.784 ± 0.091 | 0.782 ± 0.091 | 0.586 ± 0.093 |
| 500 | 500 | AnchorPlugin | 0.889 ± 0.033 | 0.873 ± 0.039 | 0.685 ± 0.065 |
| 500 | 500 | AnchorPlugin | 0.672 ± 0.123 | 0.660 ± 0.135 | 0.487 ± 0.136 |
| 500 | 500 | EntropyBalancing | 0.779 ± 0.132 | 0.784 ± 0.119 | 0.593 ± 0.103 |
| 500 | 500 | EntropyBalancing | 0.851 ± 0.193 | 0.860 ± 0.184 | 0.715 ± 0.201 |
| 500 | 500 | EntropyBalancing | 0.896 ± 0.054 | 0.884 ± 0.064 | 0.711 ± 0.058 |
| 500 | 500 | EntropyBalancing | 0.725 ± 0.189 | 0.700 ± 0.165 | 0.524 ± 0.205 |
| 500 | 500 | Glmtrans_Auto | 0.999 ± 0.001 | 0.998 ± 0.001 | 0.967 ± 0.007 |
| 500 | 500 | Glmtrans_Auto | 0.997 ± 0.003 | 0.996 ± 0.002 | 0.954 ± 0.015 |
| 500 | 500 | Glmtrans_Auto | 0.993 ± 0.005 | 0.991 ± 0.006 | 0.930 ± 0.028 |
| 500 | 500 | Glmtrans_Auto | 0.998 ± 0.001 | 0.998 ± 0.001 | 0.964 ± 0.005 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.999 ± 0.000 | 0.998 ± 0.001 | 0.968 ± 0.005 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.997 ± 0.003 | 0.996 ± 0.005 | 0.956 ± 0.014 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.993 ± 0.005 | 0.993 ± 0.005 | 0.933 ± 0.031 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.998 ± 0.001 | 0.998 ± 0.001 | 0.964 ± 0.004 |
| 500 | 500 | Glmtrans_OptionB | 0.839 ± 0.130 | 0.834 ± 0.140 | 0.655 ± 0.127 |
| 500 | 500 | Glmtrans_OptionB | 0.849 ± 0.163 | 0.857 ± 0.144 | 0.698 ± 0.155 |
| 500 | 500 | Glmtrans_OptionB | 0.922 ± 0.044 | 0.922 ± 0.037 | 0.749 ± 0.072 |
| 500 | 500 | Glmtrans_OptionB | 0.737 ± 0.172 | 0.725 ± 0.144 | 0.537 ± 0.186 |
| 500 | 500 | IPWTransport | 0.808 ± 0.132 | 0.796 ± 0.113 | 0.616 ± 0.104 |
| 500 | 500 | IPWTransport | 0.855 ± 0.191 | 0.862 ± 0.180 | 0.719 ± 0.196 |
| 500 | 500 | IPWTransport | 0.896 ± 0.054 | 0.884 ± 0.064 | 0.712 ± 0.058 |
| 500 | 500 | IPWTransport | 0.728 ± 0.184 | 0.701 ± 0.163 | 0.525 ± 0.202 |
| 500 | 500 | OutcomeModelTransport | 0.841 ± 0.129 | 0.834 ± 0.140 | 0.655 ± 0.127 |
| 500 | 500 | OutcomeModelTransport | 0.871 ± 0.174 | 0.880 ± 0.152 | 0.733 ± 0.179 |
| 500 | 500 | OutcomeModelTransport | 0.904 ± 0.051 | 0.887 ± 0.080 | 0.725 ± 0.043 |
| 500 | 500 | OutcomeModelTransport | 0.737 ± 0.171 | 0.726 ± 0.143 | 0.537 ± 0.186 |
| 500 | 500 | ProxyOnly | 0.433 ± 0.134 | 0.415 ± 0.135 | 0.297 ± 0.044 |
| 500 | 500 | ProxyOnly | 0.583 ± 0.074 | 0.585 ± 0.084 | 0.402 ± 0.049 |
| 500 | 500 | ProxyOnly | 0.748 ± 0.106 | 0.741 ± 0.108 | 0.550 ± 0.129 |
| 500 | 500 | ProxyOnly | 0.532 ± 0.182 | 0.505 ± 0.233 | 0.362 ± 0.121 |
| 500 | 500 | TargetOnlyDR | 0.615 ± 0.079 | 0.570 ± 0.137 | 0.403 ± 0.045 |
| 500 | 500 | TargetOnlyDR | 0.684 ± 0.061 | 0.679 ± 0.076 | 0.502 ± 0.030 |
| 500 | 500 | TargetOnlyDR | 0.894 ± 0.016 | 0.891 ± 0.041 | 0.706 ± 0.043 |
| 500 | 500 | TargetOnlyDR | 0.810 ± 0.053 | 0.791 ± 0.067 | 0.610 ± 0.007 |

### ATE Estimation

| m0 | m1 | Method | ATE Est | ATE Err (↓) | ATE Bias |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 0.718 ± 2.918 | 0.725 ± 0.535 | 0.680 ± 0.604 |
| 50 | 50 | AnchorOnly | 0.171 ± 2.430 | 0.538 ± 0.335 | 0.108 ± 0.678 |
| 50 | 50 | AnchorOnly | -0.441 ± 0.954 | 0.424 ± 0.238 | 0.362 ± 0.343 |
| 50 | 50 | AnchorOnly | 0.399 ± 0.761 | 0.287 ± 0.208 | 0.287 ± 0.208 |
| 50 | 50 | AnchorPlugin | -0.192 ± 1.662 | 1.401 ± 0.707 | -0.229 ± 1.700 |
| 50 | 50 | AnchorPlugin | -0.032 ± 1.244 | 0.692 ± 0.769 | -0.095 ± 1.086 |
| 50 | 50 | AnchorPlugin | -0.680 ± 0.494 | 0.586 ± 0.363 | 0.123 ± 0.736 |
| 50 | 50 | AnchorPlugin | 0.184 ± 0.425 | 0.776 ± 0.460 | 0.072 ± 0.979 |
| 50 | 50 | EntropyBalancing | 0.114 ± 1.338 | 1.062 ± 1.355 | 0.076 ± 1.800 |
| 50 | 50 | EntropyBalancing | -0.088 ± 1.442 | 1.083 ± 0.837 | -0.152 ± 1.462 |
| 50 | 50 | EntropyBalancing | -0.239 ± 0.464 | 0.844 ± 1.041 | 0.564 ± 1.255 |
| 50 | 50 | EntropyBalancing | -0.472 ± 0.296 | 0.757 ± 0.789 | -0.584 ± 0.955 |
| 50 | 50 | Glmtrans_Auto | 0.110 ± 2.768 | 0.374 ± 0.410 | 0.072 ± 0.580 |
| 50 | 50 | Glmtrans_Auto | 0.110 ± 2.036 | 0.169 ± 0.156 | 0.046 ± 0.239 |
| 50 | 50 | Glmtrans_Auto | -0.781 ± 1.095 | 0.060 ± 0.041 | 0.023 ± 0.074 |
| 50 | 50 | Glmtrans_Auto | 0.176 ± 0.871 | 0.065 ± 0.071 | 0.065 ± 0.071 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.340 ± 2.976 | 0.580 ± 0.372 | 0.303 ± 0.666 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.061 ± 2.059 | 0.225 ± 0.147 | -0.003 ± 0.291 |
| 50 | 50 | Glmtrans_DR_CrossFit | -0.912 ± 1.053 | 0.133 ± 0.212 | -0.109 ± 0.228 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.181 ± 0.863 | 0.082 ± 0.070 | 0.069 ± 0.086 |
| 50 | 50 | Glmtrans_OptionB | 0.203 ± 1.620 | 1.142 ± 1.137 | 0.166 ± 1.700 |
| 50 | 50 | Glmtrans_OptionB | -0.144 ± 1.330 | 1.124 ± 0.801 | -0.208 ± 1.472 |
| 50 | 50 | Glmtrans_OptionB | -0.552 ± 0.367 | 0.865 ± 0.717 | 0.251 ± 1.170 |
| 50 | 50 | Glmtrans_OptionB | 0.209 ± 0.798 | 0.635 ± 0.661 | 0.097 ± 0.964 |
| 50 | 50 | IPWTransport | 0.193 ± 1.479 | 1.059 ± 1.188 | 0.156 ± 1.668 |
| 50 | 50 | IPWTransport | -0.087 ± 1.367 | 1.083 ± 0.827 | -0.151 ± 1.456 |
| 50 | 50 | IPWTransport | -0.275 ± 0.453 | 0.820 ± 1.008 | 0.528 ± 1.227 |
| 50 | 50 | IPWTransport | -0.474 ± 0.279 | 0.769 ± 0.776 | -0.585 ± 0.956 |
| 50 | 50 | OutcomeModelTransport | 0.206 ± 1.630 | 1.147 ± 1.133 | 0.169 ± 1.700 |
| 50 | 50 | OutcomeModelTransport | -0.140 ± 1.332 | 1.126 ± 0.803 | -0.204 ± 1.475 |
| 50 | 50 | OutcomeModelTransport | -0.236 ± 0.466 | 0.859 ± 1.043 | 0.568 ± 1.268 |
| 50 | 50 | OutcomeModelTransport | -0.480 ± 0.279 | 0.772 ± 0.776 | -0.592 ± 0.953 |
| 50 | 50 | ProxyOnly | -0.347 ± 3.513 | 1.829 ± 1.499 | -0.384 ± 2.499 |
| 50 | 50 | ProxyOnly | -0.039 ± 3.223 | 1.661 ± 1.186 | -0.103 ± 2.200 |
| 50 | 50 | ProxyOnly | -1.451 ± 1.281 | 0.736 ± 0.638 | -0.648 ± 0.748 |
| 50 | 50 | ProxyOnly | 0.812 ± 0.795 | 0.903 ± 0.836 | 0.701 ± 1.051 |
| 50 | 50 | TargetOnlyDR | 0.582 ± 3.430 | 1.011 ± 0.546 | 0.544 ± 1.098 |
| 50 | 50 | TargetOnlyDR | 0.213 ± 2.580 | 0.647 ± 0.416 | 0.149 ± 0.818 |
| 50 | 50 | TargetOnlyDR | -0.566 ± 1.073 | 0.238 ± 0.286 | 0.238 ± 0.286 |
| 50 | 50 | TargetOnlyDR | 0.384 ± 0.772 | 0.272 ± 0.113 | 0.272 ± 0.113 |
| 100 | 100 | AnchorOnly | 0.970 ± 0.627 | 0.303 ± 0.271 | 0.118 ± 0.413 |
| 100 | 100 | AnchorOnly | -0.191 ± 3.127 | 0.369 ± 0.236 | -0.259 ± 0.377 |
| 100 | 100 | AnchorOnly | -0.601 ± 1.069 | 0.095 ± 0.049 | 0.029 ± 0.112 |
| 100 | 100 | AnchorOnly | 1.608 ± 3.501 | 0.398 ± 0.290 | -0.254 ± 0.449 |
| 100 | 100 | AnchorPlugin | 0.620 ± 0.654 | 0.374 ± 0.210 | -0.231 ± 0.390 |
| 100 | 100 | AnchorPlugin | -0.414 ± 1.212 | 1.556 ± 0.877 | -0.482 ± 1.872 |
| 100 | 100 | AnchorPlugin | -0.385 ± 0.558 | 0.440 ± 0.400 | 0.245 ± 0.571 |
| 100 | 100 | AnchorPlugin | 0.656 ± 2.078 | 1.408 ± 2.021 | -1.205 ± 2.178 |
| 100 | 100 | EntropyBalancing | 0.315 ± 0.709 | 0.623 ± 0.329 | -0.537 ± 0.482 |
| 100 | 100 | EntropyBalancing | -0.792 ± 1.147 | 1.824 ± 1.529 | -0.860 ± 2.360 |
| 100 | 100 | EntropyBalancing | -0.277 ± 0.594 | 0.357 ± 0.407 | 0.353 ± 0.411 |
| 100 | 100 | EntropyBalancing | 1.110 ± 3.321 | 0.778 ± 0.640 | -0.752 ± 0.678 |
| 100 | 100 | Glmtrans_Auto | 0.891 ± 0.410 | 0.102 ± 0.034 | 0.040 ± 0.110 |
| 100 | 100 | Glmtrans_Auto | 0.071 ± 2.817 | 0.082 ± 0.085 | 0.003 ± 0.126 |
| 100 | 100 | Glmtrans_Auto | -0.630 ± 1.015 | 0.063 ± 0.055 | 0.000 ± 0.089 |
| 100 | 100 | Glmtrans_Auto | 1.879 ± 3.612 | 0.162 ± 0.106 | 0.017 ± 0.209 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.881 ± 0.390 | 0.086 ± 0.040 | 0.029 ± 0.099 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.048 ± 2.846 | 0.217 ± 0.073 | -0.020 ± 0.253 |
| 100 | 100 | Glmtrans_DR_CrossFit | -0.637 ± 1.006 | 0.081 ± 0.065 | -0.007 ± 0.111 |
| 100 | 100 | Glmtrans_DR_CrossFit | 1.620 ± 3.517 | 0.254 ± 0.282 | -0.242 ± 0.295 |
| 100 | 100 | Glmtrans_OptionB | 0.307 ± 0.692 | 0.604 ± 0.346 | -0.544 ± 0.452 |
| 100 | 100 | Glmtrans_OptionB | -0.687 ± 1.243 | 1.513 ± 1.256 | -0.755 ± 1.931 |
| 100 | 100 | Glmtrans_OptionB | -0.346 ± 0.559 | 0.391 ± 0.391 | 0.284 ± 0.494 |
| 100 | 100 | Glmtrans_OptionB | 1.207 ± 3.291 | 0.759 ± 0.635 | -0.655 ± 0.766 |
| 100 | 100 | IPWTransport | 0.304 ± 0.702 | 0.617 ± 0.345 | -0.547 ± 0.470 |
| 100 | 100 | IPWTransport | -0.891 ± 1.102 | 1.926 ± 1.653 | -0.959 ± 2.495 |
| 100 | 100 | IPWTransport | -0.272 ± 0.580 | 0.361 ± 0.422 | 0.358 ± 0.425 |
| 100 | 100 | IPWTransport | 1.194 ± 3.289 | 0.758 ± 0.616 | -0.668 ± 0.735 |
| 100 | 100 | OutcomeModelTransport | 0.308 ± 0.694 | 0.604 ± 0.345 | -0.544 ± 0.454 |
| 100 | 100 | OutcomeModelTransport | -0.734 ± 1.264 | 1.664 ± 1.324 | -0.802 ± 2.100 |
| 100 | 100 | OutcomeModelTransport | -0.296 ± 0.564 | 0.338 ± 0.424 | 0.334 ± 0.428 |
| 100 | 100 | OutcomeModelTransport | 1.215 ± 3.308 | 0.757 ± 0.620 | -0.647 ± 0.760 |
| 100 | 100 | ProxyOnly | 0.890 ± 1.029 | 0.547 ± 0.502 | 0.039 ± 0.790 |
| 100 | 100 | ProxyOnly | -0.382 ± 2.403 | 1.079 ± 1.033 | -0.450 ± 1.506 |
| 100 | 100 | ProxyOnly | -0.614 ± 0.870 | 0.384 ± 0.173 | 0.016 ± 0.462 |
| 100 | 100 | ProxyOnly | 1.442 ± 3.791 | 1.383 ± 0.620 | -0.419 ± 1.598 |
| 100 | 100 | TargetOnlyDR | 0.848 ± 0.673 | 0.309 ± 0.305 | -0.004 ± 0.461 |
| 100 | 100 | TargetOnlyDR | -0.070 ± 3.129 | 0.370 ± 0.167 | -0.138 ± 0.418 |
| 100 | 100 | TargetOnlyDR | -0.629 ± 1.089 | 0.104 ± 0.064 | 0.001 ± 0.133 |
| 100 | 100 | TargetOnlyDR | 1.635 ± 3.872 | 0.227 ± 0.175 | -0.227 ± 0.175 |
| 200 | 200 | AnchorOnly | -0.031 ± 1.646 | 0.142 ± 0.105 | -0.068 ± 0.174 |
| 200 | 200 | AnchorOnly | -0.445 ± 1.037 | 0.350 ± 0.112 | 0.266 ± 0.277 |
| 200 | 200 | AnchorOnly | 1.324 ± 2.052 | 0.307 ± 0.180 | -0.109 ± 0.368 |
| 200 | 200 | AnchorOnly | 0.642 ± 0.536 | 0.086 ± 0.042 | -0.045 ± 0.092 |
| 200 | 200 | AnchorPlugin | -0.146 ± 1.169 | 0.534 ± 0.443 | -0.184 ± 0.715 |
| 200 | 200 | AnchorPlugin | -0.562 ± 0.627 | 0.566 ± 0.273 | 0.149 ± 0.668 |
| 200 | 200 | AnchorPlugin | -0.402 ± 2.135 | 1.835 ± 0.827 | -1.835 ± 0.827 |
| 200 | 200 | AnchorPlugin | 0.224 ± 0.323 | 0.500 ± 0.448 | -0.463 ± 0.494 |
| 200 | 200 | EntropyBalancing | -0.112 ± 1.182 | 0.905 ± 0.624 | -0.149 ± 1.177 |
| 200 | 200 | EntropyBalancing | -0.818 ± 1.506 | 0.499 ± 0.365 | -0.107 ± 0.656 |
| 200 | 200 | EntropyBalancing | 0.944 ± 1.766 | 0.611 ± 0.693 | -0.489 ± 0.806 |
| 200 | 200 | EntropyBalancing | 0.156 ± 0.675 | 0.586 ± 0.317 | -0.531 ± 0.420 |
| 200 | 200 | Glmtrans_Auto | 0.048 ± 1.774 | 0.041 ± 0.026 | 0.011 ± 0.051 |
| 200 | 200 | Glmtrans_Auto | -0.664 ± 0.979 | 0.049 ± 0.054 | 0.047 ± 0.055 |
| 200 | 200 | Glmtrans_Auto | 1.459 ± 1.746 | 0.064 ± 0.034 | 0.026 ± 0.073 |
| 200 | 200 | Glmtrans_Auto | 0.697 ± 0.575 | 0.038 ± 0.024 | 0.010 ± 0.048 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.060 ± 1.781 | 0.042 ± 0.036 | 0.023 ± 0.054 |
| 200 | 200 | Glmtrans_DR_CrossFit | -0.655 ± 0.965 | 0.056 ± 0.034 | 0.056 ± 0.034 |
| 200 | 200 | Glmtrans_DR_CrossFit | 1.456 ± 1.783 | 0.093 ± 0.063 | 0.023 ± 0.118 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.691 ± 0.574 | 0.046 ± 0.027 | 0.004 ± 0.058 |
| 200 | 200 | Glmtrans_OptionB | -0.056 ± 1.153 | 0.875 ± 0.591 | -0.093 ± 1.138 |
| 200 | 200 | Glmtrans_OptionB | -0.314 ± 1.391 | 0.616 ± 0.287 | 0.397 ± 0.599 |
| 200 | 200 | Glmtrans_OptionB | 0.686 ± 1.967 | 0.785 ± 0.720 | -0.747 ± 0.769 |
| 200 | 200 | Glmtrans_OptionB | 0.151 ± 0.605 | 0.536 ± 0.362 | -0.536 ± 0.362 |
| 200 | 200 | IPWTransport | -0.103 ± 1.199 | 0.900 ± 0.628 | -0.140 ± 1.176 |
| 200 | 200 | IPWTransport | -0.821 ± 1.484 | 0.483 ± 0.340 | -0.110 ± 0.626 |
| 200 | 200 | IPWTransport | 0.966 ± 1.825 | 0.569 ± 0.783 | -0.466 ± 0.864 |
| 200 | 200 | IPWTransport | 0.155 ± 0.686 | 0.593 ± 0.306 | -0.532 ± 0.425 |
| 200 | 200 | OutcomeModelTransport | -0.108 ± 1.160 | 0.927 ± 0.640 | -0.145 ± 1.208 |
| 200 | 200 | OutcomeModelTransport | -0.765 ± 1.558 | 0.538 ± 0.351 | -0.053 ± 0.694 |
| 200 | 200 | OutcomeModelTransport | 0.717 ± 2.079 | 0.879 ± 0.657 | -0.716 ± 0.870 |
| 200 | 200 | OutcomeModelTransport | 0.182 ± 0.659 | 0.557 ± 0.325 | -0.505 ± 0.418 |
| 200 | 200 | ProxyOnly | -0.137 ± 1.518 | 0.548 ± 0.382 | -0.174 ± 0.696 |
| 200 | 200 | ProxyOnly | -1.059 ± 0.891 | 0.672 ± 0.836 | -0.348 ± 1.054 |
| 200 | 200 | ProxyOnly | -0.707 ± 3.621 | 2.384 ± 1.858 | -2.140 ± 2.198 |
| 200 | 200 | ProxyOnly | 0.229 ± 0.420 | 0.708 ± 0.580 | -0.458 ± 0.837 |
| 200 | 200 | TargetOnlyDR | -0.022 ± 1.714 | 0.130 ± 0.087 | -0.059 ± 0.156 |
| 200 | 200 | TargetOnlyDR | -0.566 ± 1.113 | 0.316 ± 0.144 | 0.146 ± 0.345 |
| 200 | 200 | TargetOnlyDR | 1.398 ± 1.943 | 0.235 ± 0.175 | -0.035 ± 0.313 |
| 200 | 200 | TargetOnlyDR | 0.646 ± 0.516 | 0.096 ± 0.048 | -0.041 ± 0.108 |
| 500 | 500 | AnchorOnly | -0.597 ± 2.357 | 0.372 ± 0.329 | -0.372 ± 0.329 |
| 500 | 500 | AnchorOnly | -0.687 ± 1.011 | 0.240 ± 0.209 | 0.109 ± 0.317 |
| 500 | 500 | AnchorOnly | 0.125 ± 1.309 | 0.035 ± 0.026 | 0.014 ± 0.044 |
| 500 | 500 | AnchorOnly | -0.064 ± 1.591 | 0.218 ± 0.136 | 0.049 ± 0.273 |
| 500 | 500 | AnchorPlugin | -0.274 ± 2.279 | 0.959 ± 0.428 | -0.048 ± 1.154 |
| 500 | 500 | AnchorPlugin | -0.636 ± 0.554 | 0.379 ± 0.313 | 0.160 ± 0.495 |
| 500 | 500 | AnchorPlugin | 0.258 ± 1.104 | 0.406 ± 0.179 | 0.148 ± 0.459 |
| 500 | 500 | AnchorPlugin | -0.133 ± 1.272 | 0.259 ± 0.164 | -0.021 ± 0.332 |
| 500 | 500 | EntropyBalancing | -0.237 ± 2.907 | 0.881 ± 0.800 | -0.011 ± 1.269 |
| 500 | 500 | EntropyBalancing | -0.152 ± 1.380 | 0.919 ± 0.675 | 0.645 ± 0.997 |
| 500 | 500 | EntropyBalancing | -0.037 ± 0.563 | 0.710 ± 0.361 | -0.148 ± 0.857 |
| 500 | 500 | EntropyBalancing | -0.102 ± 0.411 | 0.886 ± 0.446 | 0.011 ± 1.086 |
| 500 | 500 | Glmtrans_Auto | -0.206 ± 2.356 | 0.030 ± 0.019 | 0.020 ± 0.031 |
| 500 | 500 | Glmtrans_Auto | -0.800 ± 0.806 | 0.023 ± 0.010 | -0.003 ± 0.027 |
| 500 | 500 | Glmtrans_Auto | 0.117 ± 1.317 | 0.032 ± 0.028 | 0.006 ± 0.045 |
| 500 | 500 | Glmtrans_Auto | -0.115 ± 1.407 | 0.035 ± 0.018 | -0.002 ± 0.043 |
| 500 | 500 | Glmtrans_DR_CrossFit | -0.200 ± 2.360 | 0.026 ± 0.016 | 0.026 ± 0.016 |
| 500 | 500 | Glmtrans_DR_CrossFit | -0.803 ± 0.808 | 0.028 ± 0.017 | -0.007 ± 0.034 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.114 ± 1.327 | 0.039 ± 0.030 | 0.004 ± 0.052 |
| 500 | 500 | Glmtrans_DR_CrossFit | -0.117 ± 1.410 | 0.030 ± 0.019 | -0.005 ± 0.039 |
| 500 | 500 | Glmtrans_OptionB | -0.271 ± 2.800 | 0.935 ± 0.799 | -0.045 ± 1.315 |
| 500 | 500 | Glmtrans_OptionB | -0.308 ± 1.809 | 1.070 ± 0.633 | 0.488 ± 1.239 |
| 500 | 500 | Glmtrans_OptionB | -0.086 ± 0.680 | 0.653 ± 0.312 | -0.197 ± 0.763 |
| 500 | 500 | Glmtrans_OptionB | -0.108 ± 0.408 | 0.882 ± 0.428 | 0.005 ± 1.074 |
| 500 | 500 | IPWTransport | -0.232 ± 2.871 | 0.925 ± 0.821 | -0.006 ± 1.320 |
| 500 | 500 | IPWTransport | -0.175 ± 1.364 | 0.914 ± 0.649 | 0.621 ± 0.991 |
| 500 | 500 | IPWTransport | -0.038 ± 0.564 | 0.711 ± 0.361 | -0.149 ± 0.857 |
| 500 | 500 | IPWTransport | -0.100 ± 0.412 | 0.888 ± 0.453 | 0.013 ± 1.092 |
| 500 | 500 | OutcomeModelTransport | -0.268 ± 2.815 | 0.938 ± 0.806 | -0.042 ± 1.322 |
| 500 | 500 | OutcomeModelTransport | -0.068 ± 1.382 | 0.945 ± 0.725 | 0.729 ± 0.989 |
| 500 | 500 | OutcomeModelTransport | -0.032 ± 0.567 | 0.705 ± 0.356 | -0.143 ± 0.850 |
| 500 | 500 | OutcomeModelTransport | -0.109 ± 0.411 | 0.880 ± 0.424 | 0.003 ± 1.071 |
| 500 | 500 | ProxyOnly | -0.676 ± 3.534 | 1.961 ± 0.562 | -0.450 ± 2.207 |
| 500 | 500 | ProxyOnly | -0.983 ± 0.665 | 0.461 ± 0.341 | -0.187 ± 0.582 |
| 500 | 500 | ProxyOnly | 0.458 ± 1.727 | 0.456 ± 0.578 | 0.347 ± 0.666 |
| 500 | 500 | ProxyOnly | -0.166 ± 2.142 | 0.681 ± 0.322 | -0.054 ± 0.824 |
| 500 | 500 | TargetOnlyDR | -0.494 ± 2.524 | 0.390 ± 0.162 | -0.269 ± 0.355 |
| 500 | 500 | TargetOnlyDR | -0.696 ± 0.948 | 0.214 ± 0.206 | 0.101 ± 0.295 |
| 500 | 500 | TargetOnlyDR | 0.082 ± 1.326 | 0.045 ± 0.040 | -0.028 ± 0.056 |
| 500 | 500 | TargetOnlyDR | -0.127 ± 1.493 | 0.189 ± 0.093 | -0.014 ± 0.230 |

### Policy / Decision Metrics

| m0 | m1 | Method | Policy Value (↑) | Regret (↓) | Value Top20 (↑) | Regret Top20 (↓) |
|---|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 1.265 ± 1.280 | 2.073 ± 0.243 | 0.717 ± 1.339 | 1.450 ± 0.314 |
| 50 | 50 | AnchorOnly | 1.238 ± 0.827 | 1.179 ± 0.301 | 0.740 ± 0.944 | 0.836 ± 0.232 |
| 50 | 50 | AnchorOnly | 1.411 ± 0.558 | 0.410 ± 0.087 | 1.243 ± 0.474 | 0.306 ± 0.108 |
| 50 | 50 | AnchorOnly | 0.403 ± 0.525 | 0.177 ± 0.069 | 0.075 ± 0.461 | 0.131 ± 0.042 |
| 50 | 50 | AnchorPlugin | 1.753 ± 1.326 | 1.584 ± 0.385 | 1.092 ± 1.420 | 1.075 ± 0.318 |
| 50 | 50 | AnchorPlugin | 1.559 ± 0.642 | 0.857 ± 0.315 | 0.964 ± 0.824 | 0.612 ± 0.250 |
| 50 | 50 | AnchorPlugin | 1.442 ± 0.517 | 0.380 ± 0.207 | 1.296 ± 0.451 | 0.254 ± 0.123 |
| 50 | 50 | AnchorPlugin | 0.293 ± 0.594 | 0.287 ± 0.200 | 0.060 ± 0.425 | 0.146 ± 0.106 |
| 50 | 50 | EntropyBalancing | 2.569 ± 1.284 | 0.769 ± 0.486 | 1.642 ± 1.389 | 0.525 ± 0.367 |
| 50 | 50 | EntropyBalancing | 2.005 ± 0.626 | 0.412 ± 0.341 | 1.316 ± 0.851 | 0.260 ± 0.266 |
| 50 | 50 | EntropyBalancing | 1.369 ± 0.687 | 0.452 ± 0.616 | 1.288 ± 0.423 | 0.261 ± 0.363 |
| 50 | 50 | EntropyBalancing | 0.299 ± 0.508 | 0.281 ± 0.137 | 0.095 ± 0.440 | 0.111 ± 0.054 |
| 50 | 50 | Glmtrans_Auto | 2.980 ± 1.089 | 0.358 ± 0.206 | 1.887 ± 1.383 | 0.280 ± 0.174 |
| 50 | 50 | Glmtrans_Auto | 2.332 ± 0.822 | 0.084 ± 0.065 | 1.513 ± 1.019 | 0.063 ± 0.052 |
| 50 | 50 | Glmtrans_Auto | 1.801 ± 0.622 | 0.021 ± 0.008 | 1.536 ± 0.538 | 0.014 ± 0.006 |
| 50 | 50 | Glmtrans_Auto | 0.563 ± 0.544 | 0.017 ± 0.012 | 0.191 ± 0.464 | 0.015 ± 0.009 |
| 50 | 50 | Glmtrans_DR_CrossFit | 2.187 ± 1.168 | 1.151 ± 0.246 | 1.313 ± 1.399 | 0.854 ± 0.222 |
| 50 | 50 | Glmtrans_DR_CrossFit | 2.191 ± 0.764 | 0.226 ± 0.128 | 1.417 ± 0.988 | 0.159 ± 0.084 |
| 50 | 50 | Glmtrans_DR_CrossFit | 1.775 ± 0.597 | 0.047 ± 0.033 | 1.518 ± 0.531 | 0.032 ± 0.017 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.550 ± 0.557 | 0.030 ± 0.022 | 0.183 ± 0.471 | 0.023 ± 0.014 |
| 50 | 50 | Glmtrans_OptionB | 2.771 ± 1.129 | 0.566 ± 0.302 | 1.776 ± 1.357 | 0.391 ± 0.240 |
| 50 | 50 | Glmtrans_OptionB | 2.009 ± 0.609 | 0.408 ± 0.346 | 1.303 ± 0.824 | 0.273 ± 0.299 |
| 50 | 50 | Glmtrans_OptionB | 1.470 ± 0.543 | 0.351 ± 0.377 | 1.374 ± 0.427 | 0.176 ± 0.193 |
| 50 | 50 | Glmtrans_OptionB | 0.402 ± 0.587 | 0.178 ± 0.079 | 0.137 ± 0.467 | 0.069 ± 0.040 |
| 50 | 50 | IPWTransport | 2.753 ± 1.145 | 0.584 ± 0.345 | 1.758 ± 1.383 | 0.409 ± 0.256 |
| 50 | 50 | IPWTransport | 2.007 ± 0.611 | 0.409 ± 0.353 | 1.313 ± 0.829 | 0.263 ± 0.290 |
| 50 | 50 | IPWTransport | 1.366 ± 0.667 | 0.455 ± 0.591 | 1.284 ± 0.420 | 0.266 ± 0.362 |
| 50 | 50 | IPWTransport | 0.292 ± 0.504 | 0.288 ± 0.132 | 0.090 ± 0.436 | 0.116 ± 0.059 |
| 50 | 50 | OutcomeModelTransport | 2.770 ± 1.132 | 0.567 ± 0.303 | 1.777 ± 1.352 | 0.390 ± 0.241 |
| 50 | 50 | OutcomeModelTransport | 2.011 ± 0.610 | 0.406 ± 0.342 | 1.302 ± 0.824 | 0.274 ± 0.299 |
| 50 | 50 | OutcomeModelTransport | 1.359 ± 0.668 | 0.462 ± 0.594 | 1.281 ± 0.420 | 0.268 ± 0.363 |
| 50 | 50 | OutcomeModelTransport | 0.291 ± 0.505 | 0.289 ± 0.132 | 0.090 ± 0.435 | 0.116 ± 0.060 |
| 50 | 50 | ProxyOnly | 0.487 ± 1.500 | 2.851 ± 0.595 | 0.191 ± 1.590 | 1.976 ± 0.322 |
| 50 | 50 | ProxyOnly | 0.786 ± 1.138 | 1.631 ± 0.557 | 0.596 ± 0.887 | 0.980 ± 0.193 |
| 50 | 50 | ProxyOnly | 1.112 ± 0.386 | 0.710 ± 0.271 | 1.032 ± 0.472 | 0.518 ± 0.120 |
| 50 | 50 | ProxyOnly | -0.039 ± 0.833 | 0.619 ± 0.459 | -0.099 ± 0.450 | 0.305 ± 0.153 |
| 50 | 50 | TargetOnlyDR | 1.164 ± 1.364 | 2.174 ± 0.370 | 0.713 ± 1.421 | 1.455 ± 0.271 |
| 50 | 50 | TargetOnlyDR | 1.230 ± 0.824 | 1.187 ± 0.251 | 0.725 ± 0.947 | 0.852 ± 0.196 |
| 50 | 50 | TargetOnlyDR | 1.422 ± 0.589 | 0.399 ± 0.049 | 1.287 ± 0.544 | 0.262 ± 0.031 |
| 50 | 50 | TargetOnlyDR | 0.386 ± 0.539 | 0.194 ± 0.047 | 0.062 ± 0.457 | 0.144 ± 0.029 |
| 100 | 100 | AnchorOnly | 1.228 ± 0.317 | 0.393 ± 0.128 | 0.552 ± 0.366 | 0.287 ± 0.119 |
| 100 | 100 | AnchorOnly | 1.808 ± 1.039 | 1.149 ± 0.350 | 1.223 ± 0.522 | 0.751 ± 0.297 |
| 100 | 100 | AnchorOnly | 1.075 ± 0.206 | 0.196 ± 0.108 | 0.906 ± 0.219 | 0.117 ± 0.057 |
| 100 | 100 | AnchorOnly | 2.403 ± 1.915 | 1.498 ± 0.411 | 0.831 ± 1.031 | 1.230 ± 0.156 |
| 100 | 100 | AnchorPlugin | 1.304 ± 0.353 | 0.317 ± 0.158 | 0.592 ± 0.494 | 0.246 ± 0.143 |
| 100 | 100 | AnchorPlugin | 2.073 ± 0.989 | 0.884 ± 0.683 | 1.347 ± 0.445 | 0.627 ± 0.541 |
| 100 | 100 | AnchorPlugin | 1.001 ± 0.314 | 0.269 ± 0.282 | 0.827 ± 0.187 | 0.197 ± 0.239 |
| 100 | 100 | AnchorPlugin | 2.856 ± 1.487 | 1.045 ± 0.278 | 1.313 ± 0.957 | 0.749 ± 0.113 |
| 100 | 100 | EntropyBalancing | 1.258 ± 0.454 | 0.362 ± 0.262 | 0.581 ± 0.556 | 0.257 ± 0.215 |
| 100 | 100 | EntropyBalancing | 2.091 ± 0.788 | 0.866 ± 0.886 | 1.464 ± 0.488 | 0.509 ± 0.594 |
| 100 | 100 | EntropyBalancing | 1.018 ± 0.310 | 0.252 ± 0.211 | 0.837 ± 0.213 | 0.186 ± 0.160 |
| 100 | 100 | EntropyBalancing | 3.460 ± 1.552 | 0.441 ± 0.130 | 1.690 ± 0.945 | 0.372 ± 0.167 |
| 100 | 100 | Glmtrans_Auto | 1.601 ± 0.243 | 0.020 ± 0.010 | 0.827 ± 0.401 | 0.012 ± 0.006 |
| 100 | 100 | Glmtrans_Auto | 2.940 ± 1.109 | 0.017 ± 0.004 | 1.956 ± 0.607 | 0.017 ± 0.007 |
| 100 | 100 | Glmtrans_Auto | 1.261 ± 0.245 | 0.010 ± 0.007 | 1.017 ± 0.264 | 0.006 ± 0.006 |
| 100 | 100 | Glmtrans_Auto | 3.837 ± 1.631 | 0.064 ± 0.040 | 2.012 ± 1.027 | 0.050 ± 0.040 |
| 100 | 100 | Glmtrans_DR_CrossFit | 1.603 ± 0.241 | 0.018 ± 0.005 | 0.826 ± 0.401 | 0.012 ± 0.004 |
| 100 | 100 | Glmtrans_DR_CrossFit | 2.888 ± 1.089 | 0.069 ± 0.065 | 1.923 ± 0.581 | 0.050 ± 0.045 |
| 100 | 100 | Glmtrans_DR_CrossFit | 1.261 ± 0.249 | 0.010 ± 0.006 | 1.017 ± 0.265 | 0.007 ± 0.005 |
| 100 | 100 | Glmtrans_DR_CrossFit | 3.663 ± 1.585 | 0.238 ± 0.169 | 1.891 ± 0.969 | 0.170 ± 0.118 |
| 100 | 100 | Glmtrans_OptionB | 1.268 ± 0.443 | 0.352 ± 0.250 | 0.587 ± 0.551 | 0.251 ± 0.209 |
| 100 | 100 | Glmtrans_OptionB | 2.593 ± 0.884 | 0.364 ± 0.267 | 1.793 ± 0.546 | 0.181 ± 0.116 |
| 100 | 100 | Glmtrans_OptionB | 0.994 ± 0.308 | 0.276 ± 0.231 | 0.831 ± 0.214 | 0.193 ± 0.180 |
| 100 | 100 | Glmtrans_OptionB | 3.584 ± 1.541 | 0.317 ± 0.187 | 1.808 ± 0.958 | 0.254 ± 0.208 |
| 100 | 100 | IPWTransport | 1.267 ± 0.444 | 0.354 ± 0.252 | 0.585 ± 0.555 | 0.253 ± 0.212 |
| 100 | 100 | IPWTransport | 2.131 ± 0.808 | 0.826 ± 0.891 | 1.505 ± 0.462 | 0.468 ± 0.579 |
| 100 | 100 | IPWTransport | 1.002 ± 0.307 | 0.268 ± 0.222 | 0.831 ± 0.214 | 0.193 ± 0.177 |
| 100 | 100 | IPWTransport | 3.562 ± 1.538 | 0.338 ± 0.166 | 1.781 ± 0.938 | 0.281 ± 0.197 |
| 100 | 100 | OutcomeModelTransport | 1.266 ± 0.446 | 0.354 ± 0.253 | 0.588 ± 0.550 | 0.250 ± 0.208 |
| 100 | 100 | OutcomeModelTransport | 2.278 ± 0.945 | 0.679 ± 0.838 | 1.564 ± 0.422 | 0.409 ± 0.565 |
| 100 | 100 | OutcomeModelTransport | 0.993 ± 0.308 | 0.278 ± 0.232 | 0.830 ± 0.213 | 0.194 ± 0.179 |
| 100 | 100 | OutcomeModelTransport | 3.586 ± 1.540 | 0.315 ± 0.187 | 1.808 ± 0.956 | 0.254 ± 0.208 |
| 100 | 100 | ProxyOnly | 0.946 ± 0.260 | 0.675 ± 0.182 | 0.397 ± 0.445 | 0.441 ± 0.156 |
| 100 | 100 | ProxyOnly | 1.492 ± 1.048 | 1.466 ± 0.586 | 0.919 ± 0.567 | 1.054 ± 0.331 |
| 100 | 100 | ProxyOnly | 0.834 ± 0.332 | 0.436 ± 0.297 | 0.685 ± 0.233 | 0.338 ± 0.343 |
| 100 | 100 | ProxyOnly | 2.127 ± 2.087 | 1.773 ± 0.712 | 0.503 ± 1.073 | 1.559 ± 0.082 |
| 100 | 100 | TargetOnlyDR | 1.238 ± 0.297 | 0.383 ± 0.121 | 0.548 ± 0.388 | 0.290 ± 0.105 |
| 100 | 100 | TargetOnlyDR | 1.816 ± 0.992 | 1.141 ± 0.439 | 1.214 ± 0.511 | 0.759 ± 0.198 |
| 100 | 100 | TargetOnlyDR | 1.106 ± 0.197 | 0.165 ± 0.092 | 0.914 ± 0.244 | 0.109 ± 0.042 |
| 100 | 100 | TargetOnlyDR | 2.391 ± 1.939 | 1.510 ± 0.387 | 0.885 ± 1.011 | 1.177 ± 0.054 |
| 200 | 200 | AnchorOnly | 1.358 ± 0.576 | 0.276 ± 0.087 | 0.845 ± 0.508 | 0.187 ± 0.029 |
| 200 | 200 | AnchorOnly | 1.592 ± 0.617 | 0.797 ± 0.146 | 1.375 ± 0.610 | 0.500 ± 0.137 |
| 200 | 200 | AnchorOnly | 2.996 ± 1.342 | 1.833 ± 0.543 | 1.934 ± 1.597 | 1.300 ± 0.391 |
| 200 | 200 | AnchorOnly | 1.123 ± 0.670 | 0.121 ± 0.059 | 0.591 ± 0.414 | 0.089 ± 0.054 |
| 200 | 200 | AnchorPlugin | 1.386 ± 0.505 | 0.248 ± 0.174 | 0.826 ± 0.522 | 0.206 ± 0.194 |
| 200 | 200 | AnchorPlugin | 1.929 ± 0.621 | 0.460 ± 0.155 | 1.541 ± 0.670 | 0.334 ± 0.162 |
| 200 | 200 | AnchorPlugin | 3.339 ± 1.481 | 1.490 ± 0.861 | 2.222 ± 1.969 | 1.013 ± 0.737 |
| 200 | 200 | AnchorPlugin | 0.984 ± 0.582 | 0.261 ± 0.306 | 0.511 ± 0.387 | 0.170 ± 0.211 |
| 200 | 200 | EntropyBalancing | 1.350 ± 0.465 | 0.284 ± 0.271 | 0.846 ± 0.574 | 0.185 ± 0.280 |
| 200 | 200 | EntropyBalancing | 2.144 ± 0.670 | 0.245 ± 0.206 | 1.712 ± 0.671 | 0.163 ± 0.138 |
| 200 | 200 | EntropyBalancing | 3.883 ± 1.633 | 0.946 ± 0.851 | 2.513 ± 2.082 | 0.722 ± 0.695 |
| 200 | 200 | EntropyBalancing | 0.963 ± 0.564 | 0.282 ± 0.350 | 0.490 ± 0.363 | 0.190 ± 0.266 |
| 200 | 200 | Glmtrans_Auto | 1.628 ± 0.629 | 0.006 ± 0.003 | 1.027 ± 0.507 | 0.004 ± 0.002 |
| 200 | 200 | Glmtrans_Auto | 2.377 ± 0.571 | 0.012 ± 0.003 | 1.865 ± 0.551 | 0.010 ± 0.006 |
| 200 | 200 | Glmtrans_Auto | 4.813 ± 0.906 | 0.016 ± 0.005 | 3.221 ± 1.406 | 0.013 ± 0.004 |
| 200 | 200 | Glmtrans_Auto | 1.234 ± 0.725 | 0.010 ± 0.005 | 0.671 ± 0.460 | 0.009 ± 0.005 |
| 200 | 200 | Glmtrans_DR_CrossFit | 1.628 ± 0.629 | 0.005 ± 0.003 | 1.028 ± 0.507 | 0.004 ± 0.002 |
| 200 | 200 | Glmtrans_DR_CrossFit | 2.375 ± 0.570 | 0.014 ± 0.007 | 1.866 ± 0.551 | 0.009 ± 0.005 |
| 200 | 200 | Glmtrans_DR_CrossFit | 4.785 ± 0.934 | 0.044 ± 0.026 | 3.205 ± 1.415 | 0.029 ± 0.009 |
| 200 | 200 | Glmtrans_DR_CrossFit | 1.234 ± 0.721 | 0.011 ± 0.006 | 0.672 ± 0.459 | 0.009 ± 0.005 |
| 200 | 200 | Glmtrans_OptionB | 1.357 ± 0.475 | 0.276 ± 0.272 | 0.854 ± 0.574 | 0.177 ± 0.273 |
| 200 | 200 | Glmtrans_OptionB | 2.102 ± 0.567 | 0.287 ± 0.157 | 1.662 ± 0.616 | 0.213 ± 0.111 |
| 200 | 200 | Glmtrans_OptionB | 4.177 ± 1.284 | 0.652 ± 0.531 | 2.787 ± 1.738 | 0.447 ± 0.420 |
| 200 | 200 | Glmtrans_OptionB | 1.005 ± 0.635 | 0.239 ± 0.357 | 0.521 ± 0.424 | 0.160 ± 0.272 |
| 200 | 200 | IPWTransport | 1.352 ± 0.470 | 0.282 ± 0.266 | 0.850 ± 0.575 | 0.182 ± 0.277 |
| 200 | 200 | IPWTransport | 2.161 ± 0.669 | 0.228 ± 0.214 | 1.719 ± 0.675 | 0.156 ± 0.144 |
| 200 | 200 | IPWTransport | 3.952 ± 1.621 | 0.877 ± 0.851 | 2.580 ± 2.078 | 0.654 ± 0.700 |
| 200 | 200 | IPWTransport | 0.963 ± 0.563 | 0.281 ± 0.348 | 0.492 ± 0.362 | 0.189 ± 0.264 |
| 200 | 200 | OutcomeModelTransport | 1.350 ± 0.475 | 0.284 ± 0.261 | 0.851 ± 0.576 | 0.181 ± 0.275 |
| 200 | 200 | OutcomeModelTransport | 2.170 ± 0.666 | 0.219 ± 0.219 | 1.722 ± 0.683 | 0.153 ± 0.159 |
| 200 | 200 | OutcomeModelTransport | 3.938 ± 1.608 | 0.891 ± 0.860 | 2.549 ± 2.108 | 0.685 ± 0.751 |
| 200 | 200 | OutcomeModelTransport | 0.971 ± 0.567 | 0.274 ± 0.341 | 0.491 ± 0.363 | 0.190 ± 0.265 |
| 200 | 200 | ProxyOnly | 1.175 ± 0.609 | 0.459 ± 0.131 | 0.663 ± 0.496 | 0.369 ± 0.124 |
| 200 | 200 | ProxyOnly | 1.230 ± 0.406 | 1.159 ± 0.327 | 1.200 ± 0.676 | 0.675 ± 0.175 |
| 200 | 200 | ProxyOnly | 2.071 ± 0.769 | 2.758 ± 0.209 | 1.622 ± 1.866 | 1.613 ± 0.545 |
| 200 | 200 | ProxyOnly | 0.810 ± 0.507 | 0.434 ± 0.338 | 0.418 ± 0.291 | 0.262 ± 0.198 |
| 200 | 200 | TargetOnlyDR | 1.384 ± 0.582 | 0.250 ± 0.061 | 0.840 ± 0.499 | 0.192 ± 0.024 |
| 200 | 200 | TargetOnlyDR | 1.667 ± 0.623 | 0.722 ± 0.200 | 1.413 ± 0.557 | 0.462 ± 0.105 |
| 200 | 200 | TargetOnlyDR | 3.081 ± 1.206 | 1.748 ± 0.363 | 1.994 ± 1.516 | 1.240 ± 0.280 |
| 200 | 200 | TargetOnlyDR | 1.132 ± 0.674 | 0.113 ± 0.057 | 0.604 ± 0.428 | 0.077 ± 0.037 |
| 500 | 500 | AnchorOnly | 2.437 ± 1.071 | 1.528 ± 0.336 | 1.871 ± 1.101 | 0.956 ± 0.144 |
| 500 | 500 | AnchorOnly | 1.874 ± 0.504 | 0.730 ± 0.213 | 1.562 ± 0.537 | 0.532 ± 0.138 |
| 500 | 500 | AnchorOnly | 0.801 ± 0.754 | 0.097 ± 0.040 | 0.400 ± 0.885 | 0.074 ± 0.025 |
| 500 | 500 | AnchorOnly | 1.627 ± 0.507 | 0.317 ± 0.077 | 1.186 ± 0.811 | 0.217 ± 0.030 |
| 500 | 500 | AnchorPlugin | 2.881 ± 1.150 | 1.084 ± 0.703 | 2.114 ± 1.262 | 0.713 ± 0.460 |
| 500 | 500 | AnchorPlugin | 2.110 ± 0.482 | 0.494 ± 0.224 | 1.773 ± 0.539 | 0.320 ± 0.159 |
| 500 | 500 | AnchorPlugin | 0.778 ± 0.771 | 0.120 ± 0.057 | 0.385 ± 0.898 | 0.088 ± 0.030 |
| 500 | 500 | AnchorPlugin | 1.403 ± 0.669 | 0.541 ± 0.343 | 1.020 ± 0.950 | 0.382 ± 0.224 |
| 500 | 500 | EntropyBalancing | 3.181 ± 1.071 | 0.784 ± 0.620 | 2.274 ± 1.249 | 0.553 ± 0.435 |
| 500 | 500 | EntropyBalancing | 2.283 ± 0.540 | 0.321 ± 0.389 | 1.888 ± 0.510 | 0.206 ± 0.273 |
| 500 | 500 | EntropyBalancing | 0.750 ± 0.710 | 0.148 ± 0.097 | 0.395 ± 0.875 | 0.078 ± 0.039 |
| 500 | 500 | EntropyBalancing | 1.378 ± 0.782 | 0.566 ± 0.429 | 1.037 ± 1.045 | 0.365 ± 0.285 |
| 500 | 500 | Glmtrans_Auto | 3.961 ± 0.885 | 0.004 ± 0.002 | 2.823 ± 1.133 | 0.004 ± 0.002 |
| 500 | 500 | Glmtrans_Auto | 2.595 ± 0.574 | 0.009 ± 0.005 | 2.088 ± 0.542 | 0.005 ± 0.002 |
| 500 | 500 | Glmtrans_Auto | 0.890 ± 0.763 | 0.008 ± 0.007 | 0.467 ± 0.895 | 0.006 ± 0.004 |
| 500 | 500 | Glmtrans_Auto | 1.941 ± 0.500 | 0.003 ± 0.001 | 1.400 ± 0.811 | 0.002 ± 0.001 |
| 500 | 500 | Glmtrans_DR_CrossFit | 3.962 ± 0.886 | 0.003 ± 0.001 | 2.823 ± 1.131 | 0.004 ± 0.002 |
| 500 | 500 | Glmtrans_DR_CrossFit | 2.596 ± 0.572 | 0.008 ± 0.005 | 2.088 ± 0.540 | 0.005 ± 0.005 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.890 ± 0.764 | 0.007 ± 0.007 | 0.468 ± 0.896 | 0.005 ± 0.005 |
| 500 | 500 | Glmtrans_DR_CrossFit | 1.941 ± 0.501 | 0.003 ± 0.001 | 1.400 ± 0.811 | 0.002 ± 0.001 |
| 500 | 500 | Glmtrans_OptionB | 3.339 ± 1.102 | 0.625 ± 0.636 | 2.382 ± 1.287 | 0.445 ± 0.485 |
| 500 | 500 | Glmtrans_OptionB | 2.267 ± 0.554 | 0.337 ± 0.342 | 1.889 ± 0.510 | 0.204 ± 0.214 |
| 500 | 500 | Glmtrans_OptionB | 0.760 ± 0.725 | 0.138 ± 0.080 | 0.414 ± 0.894 | 0.060 ± 0.037 |
| 500 | 500 | Glmtrans_OptionB | 1.417 ± 0.741 | 0.528 ± 0.376 | 1.074 ± 1.008 | 0.328 ± 0.243 |
| 500 | 500 | IPWTransport | 3.263 ± 1.070 | 0.702 ± 0.555 | 2.301 ± 1.269 | 0.526 ± 0.419 |
| 500 | 500 | IPWTransport | 2.290 ± 0.536 | 0.314 ± 0.386 | 1.890 ± 0.510 | 0.203 ± 0.267 |
| 500 | 500 | IPWTransport | 0.749 ± 0.710 | 0.149 ± 0.098 | 0.396 ± 0.875 | 0.078 ± 0.038 |
| 500 | 500 | IPWTransport | 1.379 ± 0.782 | 0.565 ± 0.429 | 1.039 ± 1.040 | 0.363 ± 0.280 |
| 500 | 500 | OutcomeModelTransport | 3.339 ± 1.104 | 0.625 ± 0.645 | 2.383 ± 1.287 | 0.444 ± 0.485 |
| 500 | 500 | OutcomeModelTransport | 2.302 ± 0.523 | 0.302 ± 0.367 | 1.916 ± 0.502 | 0.178 ± 0.225 |
| 500 | 500 | OutcomeModelTransport | 0.760 ± 0.725 | 0.138 ± 0.079 | 0.403 ± 0.877 | 0.070 ± 0.030 |
| 500 | 500 | OutcomeModelTransport | 1.416 ± 0.743 | 0.528 ± 0.377 | 1.075 ± 1.007 | 0.327 ± 0.242 |
| 500 | 500 | ProxyOnly | 1.667 ± 1.307 | 2.297 ± 0.641 | 1.406 ± 1.297 | 1.421 ± 0.523 |
| 500 | 500 | ProxyOnly | 1.683 ± 0.375 | 0.921 ± 0.252 | 1.511 ± 0.494 | 0.582 ± 0.094 |
| 500 | 500 | ProxyOnly | 0.623 ± 0.819 | 0.274 ± 0.145 | 0.290 ± 0.892 | 0.183 ± 0.091 |
| 500 | 500 | ProxyOnly | 1.176 ± 0.624 | 0.768 ± 0.366 | 0.863 ± 0.949 | 0.539 ± 0.311 |
| 500 | 500 | TargetOnlyDR | 2.466 ± 1.083 | 1.498 ± 0.360 | 1.828 ± 1.137 | 0.999 ± 0.192 |
| 500 | 500 | TargetOnlyDR | 1.921 ± 0.555 | 0.683 ± 0.211 | 1.635 ± 0.579 | 0.459 ± 0.120 |
| 500 | 500 | TargetOnlyDR | 0.803 ± 0.755 | 0.095 ± 0.041 | 0.400 ± 0.888 | 0.073 ± 0.023 |
| 500 | 500 | TargetOnlyDR | 1.634 ± 0.495 | 0.310 ± 0.093 | 1.187 ± 0.827 | 0.215 ± 0.028 |

### Calibration Metrics

| m0 | m1 | Method | Slope (→1) | Intercept (→0) | R² (↑) | ECE (↓) | MCE (↓) |
|---|---|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 1.337 ± 0.245 | -1.161 ± 1.568 | 0.149 ± 0.033 | 1.279 ± 0.473 | 2.276 ± 0.690 |
| 50 | 50 | AnchorOnly | 1.201 ± 0.119 | -0.325 ± 1.184 | 0.240 ± 0.089 | 0.918 ± 0.143 | 2.125 ± 0.251 |
| 50 | 50 | AnchorOnly | 1.302 ± 0.114 | -0.295 ± 0.372 | 0.471 ± 0.050 | 0.714 ± 0.296 | 1.906 ± 0.476 |
| 50 | 50 | AnchorOnly | 1.135 ± 0.249 | -0.218 ± 0.218 | 0.627 ± 0.043 | 0.431 ± 0.281 | 0.894 ± 0.619 |
| 50 | 50 | AnchorPlugin | 1.445 ± 0.508 | -0.150 ± 2.068 | 0.305 ± 0.098 | 1.983 ± 0.520 | 4.106 ± 1.484 |
| 50 | 50 | AnchorPlugin | 1.105 ± 0.340 | 0.094 ± 1.069 | 0.412 ± 0.131 | 1.043 ± 0.598 | 2.205 ± 1.321 |
| 50 | 50 | AnchorPlugin | 1.046 ± 0.149 | -0.150 ± 0.858 | 0.580 ± 0.134 | 0.637 ± 0.351 | 1.292 ± 0.534 |
| 50 | 50 | AnchorPlugin | 1.017 ± 0.289 | -0.132 ± 1.035 | 0.625 ± 0.171 | 0.799 ± 0.444 | 1.534 ± 0.862 |
| 50 | 50 | EntropyBalancing | 0.907 ± 0.093 | -0.085 ± 1.800 | 0.638 ± 0.184 | 1.493 ± 0.990 | 2.864 ± 1.390 |
| 50 | 50 | EntropyBalancing | 0.935 ± 0.114 | 0.137 ± 1.459 | 0.733 ± 0.219 | 1.258 ± 0.665 | 1.945 ± 1.030 |
| 50 | 50 | EntropyBalancing | 0.876 ± 0.322 | -0.568 ± 1.237 | 0.659 ± 0.344 | 1.022 ± 1.250 | 2.244 ± 3.272 |
| 50 | 50 | EntropyBalancing | 0.980 ± 0.249 | 0.599 ± 0.870 | 0.652 ± 0.166 | 0.871 ± 0.696 | 1.309 ± 0.765 |
| 50 | 50 | Glmtrans_Auto | 1.037 ± 0.077 | 0.042 ± 0.837 | 0.802 ± 0.108 | 0.620 ± 0.358 | 1.564 ± 1.130 |
| 50 | 50 | Glmtrans_Auto | 1.013 ± 0.025 | -0.045 ± 0.249 | 0.929 ± 0.049 | 0.214 ± 0.125 | 0.436 ± 0.143 |
| 50 | 50 | Glmtrans_Auto | 1.032 ± 0.043 | -0.012 ± 0.058 | 0.971 ± 0.014 | 0.117 ± 0.081 | 0.272 ± 0.186 |
| 50 | 50 | Glmtrans_Auto | 1.059 ± 0.086 | -0.028 ± 0.090 | 0.944 ± 0.062 | 0.157 ± 0.089 | 0.349 ± 0.199 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.882 ± 0.134 | -0.253 ± 0.603 | 0.435 ± 0.068 | 1.155 ± 0.614 | 2.793 ± 1.385 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.948 ± 0.070 | -0.034 ± 0.252 | 0.811 ± 0.069 | 0.451 ± 0.316 | 0.914 ± 0.784 |
| 50 | 50 | Glmtrans_DR_CrossFit | 0.980 ± 0.039 | 0.107 ± 0.231 | 0.936 ± 0.042 | 0.199 ± 0.177 | 0.428 ± 0.252 |
| 50 | 50 | Glmtrans_DR_CrossFit | 1.061 ± 0.063 | -0.079 ± 0.120 | 0.921 ± 0.067 | 0.131 ± 0.063 | 0.265 ± 0.109 |
| 50 | 50 | Glmtrans_OptionB | 1.016 ± 0.060 | -0.184 ± 1.699 | 0.722 ± 0.142 | 1.304 ± 0.988 | 2.054 ± 1.067 |
| 50 | 50 | Glmtrans_OptionB | 0.951 ± 0.132 | 0.196 ± 1.500 | 0.738 ± 0.231 | 1.300 ± 0.647 | 1.977 ± 0.900 |
| 50 | 50 | Glmtrans_OptionB | 0.944 ± 0.181 | -0.281 ± 1.257 | 0.717 ± 0.251 | 0.886 ± 0.722 | 1.774 ± 1.585 |
| 50 | 50 | Glmtrans_OptionB | 0.908 ± 0.306 | 0.099 ± 0.796 | 0.785 ± 0.107 | 0.896 ± 0.525 | 1.727 ± 0.972 |
| 50 | 50 | IPWTransport | 1.010 ± 0.062 | -0.163 ± 1.662 | 0.717 ± 0.145 | 1.269 ± 0.987 | 2.001 ± 1.019 |
| 50 | 50 | IPWTransport | 0.947 ± 0.128 | 0.136 ± 1.471 | 0.742 ± 0.229 | 1.277 ± 0.669 | 1.956 ± 0.899 |
| 50 | 50 | IPWTransport | 0.863 ± 0.312 | -0.552 ± 1.228 | 0.650 ± 0.340 | 1.016 ± 1.211 | 2.238 ± 3.027 |
| 50 | 50 | IPWTransport | 0.966 ± 0.265 | 0.592 ± 0.868 | 0.638 ± 0.177 | 0.896 ± 0.670 | 1.361 ± 0.782 |
| 50 | 50 | OutcomeModelTransport | 1.011 ± 0.060 | -0.186 ± 1.699 | 0.722 ± 0.142 | 1.306 ± 0.982 | 2.092 ± 1.039 |
| 50 | 50 | OutcomeModelTransport | 0.946 ± 0.132 | 0.192 ± 1.503 | 0.738 ± 0.231 | 1.305 ± 0.651 | 1.989 ± 0.932 |
| 50 | 50 | OutcomeModelTransport | 0.861 ± 0.311 | -0.578 ± 1.236 | 0.648 ± 0.338 | 1.049 ± 1.242 | 2.274 ± 3.057 |
| 50 | 50 | OutcomeModelTransport | 0.964 ± 0.266 | 0.597 ± 0.866 | 0.637 ± 0.178 | 0.899 ± 0.671 | 1.368 ± 0.778 |
| 50 | 50 | ProxyOnly | 0.766 ± 0.290 | 0.740 ± 2.133 | 0.035 ± 0.018 | 2.103 ± 1.227 | 3.609 ± 1.121 |
| 50 | 50 | ProxyOnly | 1.193 ± 0.400 | 0.220 ± 2.880 | 0.151 ± 0.044 | 1.737 ± 1.111 | 2.701 ± 1.371 |
| 50 | 50 | ProxyOnly | 1.038 ± 0.284 | 0.660 ± 1.002 | 0.253 ± 0.088 | 0.833 ± 0.582 | 2.075 ± 1.473 |
| 50 | 50 | ProxyOnly | 1.000 ± 0.412 | -0.785 ± 1.383 | 0.315 ± 0.188 | 1.048 ± 0.690 | 2.002 ± 1.032 |
| 50 | 50 | TargetOnlyDR | 1.255 ± 0.421 | -0.506 ± 2.319 | 0.141 ± 0.076 | 1.405 ± 0.491 | 2.921 ± 0.532 |
| 50 | 50 | TargetOnlyDR | 1.054 ± 0.172 | -0.485 ± 1.060 | 0.214 ± 0.068 | 0.825 ± 0.257 | 1.866 ± 0.468 |
| 50 | 50 | TargetOnlyDR | 1.407 ± 0.235 | 0.168 ± 0.884 | 0.514 ± 0.070 | 0.774 ± 0.360 | 1.770 ± 0.815 |
| 50 | 50 | TargetOnlyDR | 1.136 ± 0.261 | -0.207 ± 0.234 | 0.563 ± 0.096 | 0.427 ± 0.151 | 1.110 ± 0.409 |
| 100 | 100 | AnchorOnly | 1.588 ± 0.283 | -0.685 ± 0.768 | 0.563 ± 0.123 | 1.030 ± 0.309 | 2.608 ± 0.710 |
| 100 | 100 | AnchorOnly | 1.626 ± 0.556 | 1.226 ± 3.387 | 0.324 ± 0.104 | 1.167 ± 0.419 | 3.264 ± 1.378 |
| 100 | 100 | AnchorOnly | 1.235 ± 0.095 | 0.145 ± 0.414 | 0.727 ± 0.067 | 0.525 ± 0.262 | 1.179 ± 0.520 |
| 100 | 100 | AnchorOnly | 1.494 ± 0.393 | 0.253 ± 1.519 | 0.181 ± 0.066 | 1.280 ± 0.526 | 3.287 ± 0.904 |
| 100 | 100 | AnchorPlugin | 1.030 ± 0.073 | 0.223 ± 0.363 | 0.645 ± 0.140 | 0.440 ± 0.118 | 0.892 ± 0.163 |
| 100 | 100 | AnchorPlugin | 1.064 ± 0.207 | 0.456 ± 1.655 | 0.506 ± 0.230 | 1.670 ± 0.707 | 2.876 ± 1.357 |
| 100 | 100 | AnchorPlugin | 1.068 ± 0.294 | -0.335 ± 0.672 | 0.649 ± 0.270 | 0.644 ± 0.378 | 1.402 ± 0.764 |
| 100 | 100 | AnchorPlugin | 1.140 ± 0.147 | 1.312 ± 1.990 | 0.442 ± 0.038 | 1.744 ± 1.828 | 2.782 ± 1.774 |
| 100 | 100 | EntropyBalancing | 0.932 ± 0.130 | 0.596 ± 0.462 | 0.647 ± 0.225 | 0.740 ± 0.297 | 1.198 ± 0.331 |
| 100 | 100 | EntropyBalancing | 0.882 ± 0.146 | 0.699 ± 2.294 | 0.636 ± 0.312 | 1.925 ± 1.480 | 2.864 ± 1.961 |
| 100 | 100 | EntropyBalancing | 1.096 ± 0.460 | -0.430 ± 0.493 | 0.650 ± 0.263 | 0.767 ± 0.302 | 1.781 ± 0.610 |
| 100 | 100 | EntropyBalancing | 0.925 ± 0.072 | 0.848 ± 0.884 | 0.724 ± 0.102 | 0.993 ± 0.493 | 1.923 ± 0.746 |
| 100 | 100 | Glmtrans_Auto | 1.064 ± 0.043 | -0.103 ± 0.142 | 0.978 ± 0.011 | 0.205 ± 0.095 | 0.529 ± 0.261 |
| 100 | 100 | Glmtrans_Auto | 1.025 ± 0.013 | -0.024 ± 0.173 | 0.984 ± 0.006 | 0.182 ± 0.057 | 0.422 ± 0.102 |
| 100 | 100 | Glmtrans_Auto | 1.020 ± 0.030 | 0.028 ± 0.129 | 0.983 ± 0.014 | 0.106 ± 0.072 | 0.239 ± 0.176 |
| 100 | 100 | Glmtrans_Auto | 1.014 ± 0.022 | -0.025 ± 0.208 | 0.959 ± 0.029 | 0.209 ± 0.079 | 0.540 ± 0.282 |
| 100 | 100 | Glmtrans_DR_CrossFit | 1.001 ± 0.048 | -0.042 ± 0.121 | 0.979 ± 0.008 | 0.152 ± 0.038 | 0.400 ± 0.086 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.964 ± 0.054 | 0.030 ± 0.190 | 0.951 ± 0.030 | 0.351 ± 0.183 | 0.852 ± 0.442 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.977 ± 0.036 | 0.000 ± 0.108 | 0.981 ± 0.019 | 0.111 ± 0.065 | 0.229 ± 0.143 |
| 100 | 100 | Glmtrans_DR_CrossFit | 0.949 ± 0.071 | 0.406 ± 0.745 | 0.855 ± 0.087 | 0.558 ± 0.405 | 1.260 ± 1.024 |
| 100 | 100 | Glmtrans_OptionB | 0.943 ± 0.128 | 0.594 ± 0.448 | 0.647 ± 0.222 | 0.725 ± 0.299 | 1.154 ± 0.413 |
| 100 | 100 | Glmtrans_OptionB | 1.074 ± 0.170 | 0.837 ± 1.988 | 0.828 ± 0.091 | 1.628 ± 1.232 | 2.726 ± 1.777 |
| 100 | 100 | Glmtrans_OptionB | 1.077 ± 0.456 | -0.356 ± 0.577 | 0.639 ± 0.279 | 0.743 ± 0.299 | 1.661 ± 0.469 |
| 100 | 100 | Glmtrans_OptionB | 1.013 ± 0.042 | 0.707 ± 0.820 | 0.810 ± 0.132 | 0.831 ± 0.550 | 1.365 ± 0.520 |
| 100 | 100 | IPWTransport | 0.936 ± 0.128 | 0.601 ± 0.459 | 0.647 ± 0.223 | 0.737 ± 0.308 | 1.160 ± 0.385 |
| 100 | 100 | IPWTransport | 0.918 ± 0.149 | 0.812 ± 2.432 | 0.669 ± 0.309 | 1.991 ± 1.624 | 2.863 ± 2.133 |
| 100 | 100 | IPWTransport | 1.077 ± 0.457 | -0.435 ± 0.513 | 0.641 ± 0.273 | 0.743 ± 0.296 | 1.696 ± 0.550 |
| 100 | 100 | IPWTransport | 0.992 ± 0.048 | 0.722 ± 0.810 | 0.795 ± 0.121 | 0.831 ± 0.532 | 1.484 ± 0.616 |
| 100 | 100 | OutcomeModelTransport | 0.939 ± 0.128 | 0.595 ± 0.447 | 0.648 ± 0.222 | 0.727 ± 0.301 | 1.166 ± 0.400 |
| 100 | 100 | OutcomeModelTransport | 0.935 ± 0.166 | 0.654 ± 2.004 | 0.702 ± 0.314 | 1.728 ± 1.306 | 2.578 ± 1.980 |
| 100 | 100 | OutcomeModelTransport | 1.067 ± 0.456 | -0.402 ± 0.526 | 0.637 ± 0.276 | 0.736 ± 0.299 | 1.642 ± 0.511 |
| 100 | 100 | OutcomeModelTransport | 1.007 ± 0.042 | 0.705 ± 0.825 | 0.810 ± 0.132 | 0.815 ± 0.550 | 1.375 ± 0.628 |
| 100 | 100 | ProxyOnly | 1.115 ± 0.251 | -0.159 ± 0.824 | 0.343 ± 0.116 | 0.856 ± 0.268 | 1.811 ± 0.281 |
| 100 | 100 | ProxyOnly | 1.320 ± 0.321 | 0.560 ± 1.751 | 0.196 ± 0.091 | 1.411 ± 0.761 | 2.813 ± 0.476 |
| 100 | 100 | ProxyOnly | 1.033 ± 0.490 | -0.202 ± 0.873 | 0.472 ± 0.267 | 0.795 ± 0.332 | 1.668 ± 0.870 |
| 100 | 100 | ProxyOnly | 1.273 ± 0.373 | 1.009 ± 1.565 | 0.099 ± 0.033 | 1.553 ± 0.431 | 3.130 ± 0.894 |
| 100 | 100 | TargetOnlyDR | 1.584 ± 0.263 | -0.479 ± 0.854 | 0.570 ± 0.132 | 1.031 ± 0.416 | 2.368 ± 0.765 |
| 100 | 100 | TargetOnlyDR | 1.539 ± 0.571 | 1.004 ± 3.014 | 0.330 ± 0.098 | 1.194 ± 0.383 | 2.862 ± 0.907 |
| 100 | 100 | TargetOnlyDR | 1.205 ± 0.116 | 0.182 ± 0.466 | 0.744 ± 0.069 | 0.499 ± 0.243 | 1.141 ± 0.559 |
| 100 | 100 | TargetOnlyDR | 1.679 ± 0.273 | -0.439 ± 2.872 | 0.211 ± 0.038 | 1.457 ± 0.534 | 3.141 ± 0.767 |
| 200 | 200 | AnchorOnly | 1.552 ± 0.101 | 0.190 ± 0.786 | 0.631 ± 0.063 | 0.857 ± 0.256 | 2.334 ± 0.645 |
| 200 | 200 | AnchorOnly | 1.595 ± 0.311 | -0.209 ± 0.836 | 0.437 ± 0.073 | 1.355 ± 0.599 | 3.253 ± 1.266 |
| 200 | 200 | AnchorOnly | 1.542 ± 0.422 | -0.888 ± 1.727 | 0.266 ± 0.076 | 1.807 ± 0.563 | 3.859 ± 1.081 |
| 200 | 200 | AnchorOnly | 1.143 ± 0.072 | -0.072 ± 0.122 | 0.757 ± 0.014 | 0.369 ± 0.233 | 0.818 ± 0.482 |
| 200 | 200 | AnchorPlugin | 1.074 ± 0.137 | 0.124 ± 0.730 | 0.689 ± 0.174 | 0.656 ± 0.334 | 1.204 ± 0.548 |
| 200 | 200 | AnchorPlugin | 1.093 ± 0.092 | -0.115 ± 0.679 | 0.645 ± 0.072 | 0.747 ± 0.131 | 1.502 ± 0.290 |
| 200 | 200 | AnchorPlugin | 1.027 ± 0.094 | 1.962 ± 0.764 | 0.438 ± 0.220 | 1.883 ± 0.769 | 3.060 ± 0.641 |
| 200 | 200 | AnchorPlugin | 0.904 ± 0.227 | 0.456 ± 0.525 | 0.656 ± 0.236 | 0.586 ± 0.384 | 1.302 ± 0.518 |
| 200 | 200 | EntropyBalancing | 0.992 ± 0.103 | 0.227 ± 1.219 | 0.760 ± 0.277 | 0.954 ± 0.576 | 1.446 ± 0.332 |
| 200 | 200 | EntropyBalancing | 0.962 ± 0.080 | 0.060 ± 0.678 | 0.819 ± 0.127 | 0.604 ± 0.326 | 1.073 ± 0.576 |
| 200 | 200 | EntropyBalancing | 0.897 ± 0.210 | 0.799 ± 0.871 | 0.603 ± 0.294 | 1.374 ± 1.164 | 2.972 ± 2.470 |
| 200 | 200 | EntropyBalancing | 1.002 ± 0.232 | 0.415 ± 0.608 | 0.678 ± 0.287 | 0.697 ± 0.189 | 1.327 ± 0.384 |
| 200 | 200 | Glmtrans_Auto | 1.039 ± 0.017 | -0.020 ± 0.066 | 0.990 ± 0.007 | 0.116 ± 0.036 | 0.264 ± 0.080 |
| 200 | 200 | Glmtrans_Auto | 1.029 ± 0.019 | -0.021 ± 0.074 | 0.988 ± 0.005 | 0.170 ± 0.044 | 0.370 ± 0.124 |
| 200 | 200 | Glmtrans_Auto | 1.024 ± 0.018 | -0.054 ± 0.087 | 0.990 ± 0.003 | 0.194 ± 0.088 | 0.464 ± 0.214 |
| 200 | 200 | Glmtrans_Auto | 1.033 ± 0.071 | -0.014 ± 0.081 | 0.974 ± 0.010 | 0.095 ± 0.076 | 0.240 ± 0.199 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.993 ± 0.015 | -0.035 ± 0.073 | 0.991 ± 0.006 | 0.072 ± 0.018 | 0.136 ± 0.042 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.992 ± 0.015 | -0.061 ± 0.037 | 0.988 ± 0.005 | 0.087 ± 0.047 | 0.217 ± 0.152 |
| 200 | 200 | Glmtrans_DR_CrossFit | 0.994 ± 0.033 | 0.015 ± 0.110 | 0.978 ± 0.008 | 0.232 ± 0.167 | 0.519 ± 0.326 |
| 200 | 200 | Glmtrans_DR_CrossFit | 1.007 ± 0.027 | -0.008 ± 0.076 | 0.975 ± 0.008 | 0.073 ± 0.043 | 0.172 ± 0.114 |
| 200 | 200 | Glmtrans_OptionB | 1.001 ± 0.094 | 0.156 ± 1.168 | 0.762 ± 0.279 | 0.915 ± 0.553 | 1.403 ± 0.277 |
| 200 | 200 | Glmtrans_OptionB | 0.917 ± 0.130 | -0.429 ± 0.665 | 0.774 ± 0.073 | 0.828 ± 0.247 | 1.952 ± 0.808 |
| 200 | 200 | Glmtrans_OptionB | 1.071 ± 0.117 | 0.683 ± 0.807 | 0.733 ± 0.199 | 1.097 ± 0.758 | 2.217 ± 1.492 |
| 200 | 200 | Glmtrans_OptionB | 0.984 ± 0.178 | 0.459 ± 0.471 | 0.722 ± 0.310 | 0.648 ± 0.221 | 1.126 ± 0.350 |
| 200 | 200 | IPWTransport | 1.000 ± 0.101 | 0.214 ± 1.211 | 0.761 ± 0.277 | 0.952 ± 0.578 | 1.489 ± 0.324 |
| 200 | 200 | IPWTransport | 0.985 ± 0.077 | 0.079 ± 0.675 | 0.833 ± 0.128 | 0.569 ± 0.297 | 1.042 ± 0.521 |
| 200 | 200 | IPWTransport | 0.954 ± 0.219 | 0.741 ± 0.853 | 0.643 ± 0.313 | 1.253 ± 0.988 | 2.875 ± 2.108 |
| 200 | 200 | IPWTransport | 1.006 ± 0.242 | 0.409 ± 0.629 | 0.675 ± 0.285 | 0.706 ± 0.178 | 1.331 ± 0.407 |
| 200 | 200 | OutcomeModelTransport | 1.011 ± 0.098 | 0.210 ± 1.238 | 0.763 ± 0.279 | 0.968 ± 0.599 | 1.530 ± 0.348 |
| 200 | 200 | OutcomeModelTransport | 1.003 ± 0.079 | 0.036 ± 0.775 | 0.846 ± 0.129 | 0.606 ± 0.315 | 1.176 ± 0.655 |
| 200 | 200 | OutcomeModelTransport | 0.960 ± 0.193 | 1.006 ± 0.607 | 0.650 ± 0.320 | 1.330 ± 0.813 | 2.582 ± 1.512 |
| 200 | 200 | OutcomeModelTransport | 1.013 ± 0.246 | 0.383 ± 0.617 | 0.675 ± 0.287 | 0.678 ± 0.217 | 1.220 ± 0.475 |
| 200 | 200 | ProxyOnly | 1.392 ± 0.306 | 0.068 ± 0.714 | 0.417 ± 0.099 | 0.911 ± 0.383 | 1.931 ± 0.928 |
| 200 | 200 | ProxyOnly | 1.620 ± 0.318 | 1.148 ± 1.803 | 0.303 ± 0.075 | 1.292 ± 0.580 | 3.015 ± 1.328 |
| 200 | 200 | ProxyOnly | 1.542 ± 0.312 | 2.733 ± 3.646 | 0.156 ± 0.059 | 2.748 ± 1.398 | 4.662 ± 1.909 |
| 200 | 200 | ProxyOnly | 0.900 ± 0.213 | 0.485 ± 0.772 | 0.452 ± 0.125 | 0.769 ± 0.546 | 1.403 ± 0.553 |
| 200 | 200 | TargetOnlyDR | 1.616 ± 0.107 | 0.034 ± 1.045 | 0.656 ± 0.046 | 0.950 ± 0.302 | 2.392 ± 0.903 |
| 200 | 200 | TargetOnlyDR | 1.713 ± 0.319 | 0.277 ± 1.295 | 0.463 ± 0.048 | 1.547 ± 0.566 | 3.251 ± 1.324 |
| 200 | 200 | TargetOnlyDR | 1.622 ± 0.357 | -1.141 ± 2.213 | 0.288 ± 0.036 | 1.751 ± 0.579 | 4.771 ± 1.210 |
| 200 | 200 | TargetOnlyDR | 1.202 ± 0.114 | -0.130 ± 0.175 | 0.775 ± 0.006 | 0.369 ± 0.278 | 0.880 ± 0.600 |
| 500 | 500 | AnchorOnly | 1.769 ± 0.461 | 0.211 ± 1.998 | 0.327 ± 0.059 | 2.135 ± 0.599 | 5.191 ± 1.529 |
| 500 | 500 | AnchorOnly | 1.644 ± 0.199 | 0.258 ± 0.719 | 0.460 ± 0.032 | 1.367 ± 0.320 | 2.947 ± 0.557 |
| 500 | 500 | AnchorOnly | 1.205 ± 0.138 | -0.056 ± 0.216 | 0.788 ± 0.039 | 0.339 ± 0.176 | 0.817 ± 0.374 |
| 500 | 500 | AnchorOnly | 1.426 ± 0.051 | 0.018 ± 0.925 | 0.658 ± 0.027 | 0.830 ± 0.212 | 2.305 ± 0.626 |
| 500 | 500 | AnchorPlugin | 1.134 ± 0.039 | 0.119 ± 1.292 | 0.520 ± 0.141 | 1.154 ± 0.289 | 2.651 ± 0.612 |
| 500 | 500 | AnchorPlugin | 1.094 ± 0.103 | -0.118 ± 0.501 | 0.632 ± 0.140 | 0.666 ± 0.263 | 1.238 ± 0.547 |
| 500 | 500 | AnchorPlugin | 1.168 ± 0.473 | -0.173 ± 0.296 | 0.766 ± 0.079 | 0.592 ± 0.342 | 1.332 ± 0.968 |
| 500 | 500 | AnchorPlugin | 1.022 ± 0.153 | -0.044 ± 0.541 | 0.482 ± 0.204 | 0.410 ± 0.269 | 0.982 ± 0.563 |
| 500 | 500 | EntropyBalancing | 0.858 ± 0.037 | 0.060 ± 1.082 | 0.635 ± 0.163 | 1.303 ± 0.574 | 2.916 ± 1.386 |
| 500 | 500 | EntropyBalancing | 0.913 ± 0.172 | -0.522 ± 0.896 | 0.777 ± 0.272 | 1.004 ± 0.797 | 2.023 ± 2.014 |
| 500 | 500 | EntropyBalancing | 1.402 ± 0.650 | 0.274 ± 0.729 | 0.803 ± 0.070 | 0.814 ± 0.512 | 1.846 ± 1.451 |
| 500 | 500 | EntropyBalancing | 0.992 ± 0.239 | -0.011 ± 1.135 | 0.534 ± 0.297 | 1.012 ± 0.342 | 1.779 ± 0.360 |
| 500 | 500 | Glmtrans_Auto | 1.027 ± 0.011 | -0.028 ± 0.073 | 0.997 ± 0.001 | 0.181 ± 0.055 | 0.420 ± 0.112 |
| 500 | 500 | Glmtrans_Auto | 1.026 ± 0.007 | 0.021 ± 0.039 | 0.994 ± 0.005 | 0.128 ± 0.037 | 0.304 ± 0.105 |
| 500 | 500 | Glmtrans_Auto | 1.009 ± 0.011 | -0.012 ± 0.056 | 0.981 ± 0.018 | 0.060 ± 0.020 | 0.138 ± 0.071 |
| 500 | 500 | Glmtrans_Auto | 1.016 ± 0.020 | 0.008 ± 0.040 | 0.996 ± 0.001 | 0.073 ± 0.038 | 0.148 ± 0.099 |
| 500 | 500 | Glmtrans_DR_CrossFit | 1.005 ± 0.005 | -0.026 ± 0.017 | 0.997 ± 0.001 | 0.065 ± 0.018 | 0.144 ± 0.066 |
| 500 | 500 | Glmtrans_DR_CrossFit | 0.993 ± 0.012 | 0.002 ± 0.038 | 0.994 ± 0.005 | 0.058 ± 0.041 | 0.141 ± 0.084 |
| 500 | 500 | Glmtrans_DR_CrossFit | 1.008 ± 0.008 | -0.009 ± 0.061 | 0.982 ± 0.018 | 0.062 ± 0.017 | 0.123 ± 0.040 |
| 500 | 500 | Glmtrans_DR_CrossFit | 1.008 ± 0.010 | 0.013 ± 0.036 | 0.996 ± 0.001 | 0.055 ± 0.013 | 0.105 ± 0.027 |
| 500 | 500 | Glmtrans_OptionB | 0.963 ± 0.023 | 0.065 ± 1.266 | 0.719 ± 0.192 | 0.993 ± 0.724 | 1.731 ± 0.988 |
| 500 | 500 | Glmtrans_OptionB | 0.928 ± 0.124 | -0.479 ± 1.062 | 0.770 ± 0.219 | 1.107 ± 0.661 | 2.192 ± 1.452 |
| 500 | 500 | Glmtrans_OptionB | 1.335 ± 0.797 | 0.188 ± 0.850 | 0.843 ± 0.076 | 0.774 ± 0.546 | 1.740 ± 1.515 |
| 500 | 500 | Glmtrans_OptionB | 1.033 ± 0.223 | -0.017 ± 1.114 | 0.551 ± 0.271 | 0.974 ± 0.355 | 1.776 ± 0.448 |
| 500 | 500 | IPWTransport | 0.904 ± 0.037 | 0.049 ± 1.218 | 0.668 ± 0.163 | 1.181 ± 0.656 | 2.505 ± 1.236 |
| 500 | 500 | IPWTransport | 0.918 ± 0.164 | -0.507 ± 0.904 | 0.782 ± 0.265 | 0.981 ± 0.742 | 1.988 ± 1.963 |
| 500 | 500 | IPWTransport | 1.406 ± 0.659 | 0.277 ± 0.730 | 0.804 ± 0.069 | 0.816 ± 0.514 | 1.850 ± 1.455 |
| 500 | 500 | IPWTransport | 0.996 ± 0.233 | -0.014 ± 1.141 | 0.536 ± 0.294 | 1.014 ± 0.346 | 1.736 ± 0.364 |
| 500 | 500 | OutcomeModelTransport | 0.958 ± 0.023 | 0.061 ± 1.264 | 0.719 ± 0.193 | 1.001 ± 0.731 | 1.793 ± 1.043 |
| 500 | 500 | OutcomeModelTransport | 0.954 ± 0.126 | -0.633 ± 0.922 | 0.800 ± 0.237 | 0.966 ± 0.755 | 1.817 ± 1.649 |
| 500 | 500 | OutcomeModelTransport | 1.449 ± 0.741 | 0.263 ± 0.728 | 0.820 ± 0.050 | 0.838 ± 0.563 | 1.906 ± 1.530 |
| 500 | 500 | OutcomeModelTransport | 1.027 ± 0.222 | -0.016 ± 1.112 | 0.552 ± 0.271 | 0.972 ± 0.352 | 1.769 ± 0.447 |
| 500 | 500 | ProxyOnly | 1.745 ± 0.222 | 1.450 ± 4.966 | 0.200 ± 0.049 | 2.312 ± 0.640 | 5.402 ± 1.818 |
| 500 | 500 | ProxyOnly | 1.693 ± 0.421 | 0.737 ± 1.004 | 0.351 ± 0.069 | 1.311 ± 0.581 | 3.079 ± 1.480 |
| 500 | 500 | ProxyOnly | 0.996 ± 0.309 | -0.412 ± 0.757 | 0.562 ± 0.189 | 0.692 ± 0.438 | 1.419 ± 0.616 |
| 500 | 500 | ProxyOnly | 1.125 ± 0.425 | -0.320 ± 1.208 | 0.295 ± 0.146 | 0.924 ± 0.343 | 2.288 ± 0.930 |
| 500 | 500 | TargetOnlyDR | 1.815 ± 0.562 | -0.211 ± 2.587 | 0.342 ± 0.070 | 2.006 ± 0.593 | 5.378 ± 0.843 |
| 500 | 500 | TargetOnlyDR | 1.718 ± 0.276 | 0.360 ± 0.700 | 0.496 ± 0.048 | 1.362 ± 0.312 | 3.393 ± 0.720 |
| 500 | 500 | TargetOnlyDR | 1.212 ± 0.139 | -0.024 ± 0.264 | 0.787 ± 0.048 | 0.352 ± 0.182 | 0.954 ± 0.613 |
| 500 | 500 | TargetOnlyDR | 1.409 ± 0.105 | 0.137 ± 0.786 | 0.666 ± 0.011 | 0.788 ± 0.196 | 2.331 ± 0.668 |

### Extended Targeting Metrics

| m0 | m1 | Method | Top-10% Captured | Top-20% Captured | Top-30% Ratio (↑) |
|---|---|---|---|---|---|
| 50 | 50 | AnchorOnly | 5.671 ± 3.077 | 4.889 ± 2.952 | 0.353 ± 0.280 |
| 50 | 50 | AnchorOnly | 4.615 ± 3.370 | 3.937 ± 2.778 | 0.446 ± 0.234 |
| 50 | 50 | AnchorOnly | 3.721 ± 1.828 | 2.833 ± 1.573 | 0.597 ± 0.198 |
| 50 | 50 | AnchorOnly | 3.409 ± 0.897 | 2.717 ± 0.708 | 0.807 ± 0.054 |
| 50 | 50 | AnchorPlugin | 8.069 ± 2.571 | 6.765 ± 2.589 | 0.517 ± 0.233 |
| 50 | 50 | AnchorPlugin | 6.293 ± 2.353 | 5.059 ± 2.178 | 0.608 ± 0.185 |
| 50 | 50 | AnchorPlugin | 4.134 ± 1.705 | 3.098 ± 1.502 | 0.647 ± 0.244 |
| 50 | 50 | AnchorPlugin | 3.306 ± 0.825 | 2.644 ± 0.876 | 0.780 ± 0.149 |
| 50 | 50 | EntropyBalancing | 11.669 ± 3.102 | 9.514 ± 3.236 | 0.753 ± 0.210 |
| 50 | 50 | EntropyBalancing | 8.420 ± 2.367 | 6.816 ± 2.247 | 0.839 ± 0.160 |
| 50 | 50 | EntropyBalancing | 4.079 ± 2.857 | 3.058 ± 2.465 | 0.617 ± 0.601 |
| 50 | 50 | EntropyBalancing | 3.467 ± 1.013 | 2.818 ± 0.927 | 0.808 ± 0.105 |
| 50 | 50 | Glmtrans_Auto | 13.649 ± 1.968 | 10.741 ± 2.292 | 0.868 ± 0.115 |
| 50 | 50 | Glmtrans_Auto | 9.750 ± 1.864 | 7.802 ± 1.875 | 0.959 ± 0.033 |
| 50 | 50 | Glmtrans_Auto | 5.587 ± 1.584 | 4.297 ± 1.398 | 0.981 ± 0.007 |
| 50 | 50 | Glmtrans_Auto | 4.074 ± 1.031 | 3.299 ± 0.850 | 0.974 ± 0.025 |
| 50 | 50 | Glmtrans_DR_CrossFit | 9.881 ± 2.575 | 7.871 ± 2.479 | 0.629 ± 0.159 |
| 50 | 50 | Glmtrans_DR_CrossFit | 9.065 ± 1.868 | 7.322 ± 1.906 | 0.895 ± 0.050 |
| 50 | 50 | Glmtrans_DR_CrossFit | 5.471 ± 1.511 | 4.205 ± 1.343 | 0.968 ± 0.013 |
| 50 | 50 | Glmtrans_DR_CrossFit | 4.024 ± 1.062 | 3.260 ± 0.895 | 0.959 ± 0.040 |
| 50 | 50 | Glmtrans_OptionB | 12.274 ± 2.988 | 10.184 ± 2.709 | 0.823 ± 0.157 |
| 50 | 50 | Glmtrans_OptionB | 8.528 ± 2.300 | 6.752 ± 2.358 | 0.834 ± 0.181 |
| 50 | 50 | Glmtrans_OptionB | 4.612 ± 2.034 | 3.485 ± 1.748 | 0.744 ± 0.323 |
| 50 | 50 | Glmtrans_OptionB | 3.716 ± 1.006 | 3.027 ± 0.878 | 0.872 ± 0.093 |
| 50 | 50 | IPWTransport | 12.354 ± 3.019 | 10.094 ± 2.688 | 0.823 ± 0.161 |
| 50 | 50 | IPWTransport | 8.594 ± 2.284 | 6.802 ± 2.345 | 0.838 ± 0.175 |
| 50 | 50 | IPWTransport | 4.175 ± 2.733 | 3.035 ± 2.454 | 0.616 ± 0.582 |
| 50 | 50 | IPWTransport | 3.443 ± 1.043 | 2.794 ± 0.931 | 0.801 ± 0.109 |
| 50 | 50 | OutcomeModelTransport | 12.299 ± 3.020 | 10.189 ± 2.725 | 0.823 ± 0.156 |
| 50 | 50 | OutcomeModelTransport | 8.518 ± 2.314 | 6.747 ± 2.359 | 0.836 ± 0.181 |
| 50 | 50 | OutcomeModelTransport | 4.177 ± 2.721 | 3.024 ± 2.457 | 0.617 ± 0.583 |
| 50 | 50 | OutcomeModelTransport | 3.436 ± 1.038 | 2.792 ± 0.934 | 0.800 ± 0.110 |
| 50 | 50 | ProxyOnly | 2.738 ± 2.002 | 2.261 ± 1.924 | 0.172 ± 0.219 |
| 50 | 50 | ProxyOnly | 3.842 ± 2.179 | 3.217 ± 1.946 | 0.353 ± 0.184 |
| 50 | 50 | ProxyOnly | 2.464 ± 1.840 | 1.775 ± 1.663 | 0.334 ± 0.313 |
| 50 | 50 | ProxyOnly | 2.143 ± 0.746 | 1.850 ± 0.708 | 0.568 ± 0.225 |
| 50 | 50 | TargetOnlyDR | 5.783 ± 2.627 | 4.867 ± 2.528 | 0.355 ± 0.244 |
| 50 | 50 | TargetOnlyDR | 4.545 ± 2.865 | 3.860 ± 2.672 | 0.421 ± 0.229 |
| 50 | 50 | TargetOnlyDR | 4.030 ± 1.493 | 3.054 ± 1.417 | 0.638 ± 0.119 |
| 50 | 50 | TargetOnlyDR | 3.250 ± 0.957 | 2.656 ± 0.753 | 0.777 ± 0.047 |
| 100 | 100 | AnchorOnly | 5.928 ± 1.351 | 4.989 ± 1.204 | 0.790 ± 0.093 |
| 100 | 100 | AnchorOnly | 6.173 ± 3.036 | 5.247 ± 3.027 | 0.532 ± 0.147 |
| 100 | 100 | AnchorOnly | 3.910 ± 1.328 | 3.133 ± 1.008 | 0.829 ± 0.091 |
| 100 | 100 | AnchorOnly | 8.075 ± 3.000 | 6.838 ± 3.432 | 0.497 ± 0.120 |
| 100 | 100 | AnchorPlugin | 6.237 ± 0.676 | 5.191 ± 0.627 | 0.818 ± 0.087 |
| 100 | 100 | AnchorPlugin | 7.425 ± 3.946 | 5.867 ± 3.663 | 0.652 ± 0.209 |
| 100 | 100 | AnchorPlugin | 3.576 ± 1.762 | 2.734 ± 1.738 | 0.677 ± 0.422 |
| 100 | 100 | AnchorPlugin | 11.109 ± 3.942 | 9.246 ± 4.011 | 0.686 ± 0.103 |
| 100 | 100 | EntropyBalancing | 6.281 ± 0.914 | 5.137 ± 0.835 | 0.812 ± 0.146 |
| 100 | 100 | EntropyBalancing | 8.180 ± 3.237 | 6.454 ± 3.058 | 0.768 ± 0.235 |
| 100 | 100 | EntropyBalancing | 3.606 ± 1.679 | 2.787 ± 1.440 | 0.694 ± 0.317 |
| 100 | 100 | EntropyBalancing | 13.568 ± 3.974 | 11.132 ± 3.689 | 0.863 ± 0.055 |
| 100 | 100 | Glmtrans_Auto | 7.724 ± 0.762 | 6.364 ± 0.701 | 0.991 ± 0.004 |
| 100 | 100 | Glmtrans_Auto | 11.165 ± 4.122 | 8.916 ± 3.837 | 0.989 ± 0.007 |
| 100 | 100 | Glmtrans_Auto | 4.746 ± 1.243 | 3.688 ± 1.027 | 0.992 ± 0.006 |
| 100 | 100 | Glmtrans_Auto | 15.491 ± 4.115 | 12.741 ± 3.993 | 0.981 ± 0.014 |
| 100 | 100 | Glmtrans_DR_CrossFit | 7.733 ± 0.764 | 6.360 ± 0.701 | 0.991 ± 0.003 |
| 100 | 100 | Glmtrans_DR_CrossFit | 10.966 ± 4.070 | 8.751 ± 3.792 | 0.971 ± 0.019 |
| 100 | 100 | Glmtrans_DR_CrossFit | 4.739 ± 1.258 | 3.685 ± 1.037 | 0.990 ± 0.009 |
| 100 | 100 | Glmtrans_DR_CrossFit | 14.720 ± 4.181 | 12.138 ± 4.044 | 0.928 ± 0.050 |
| 100 | 100 | Glmtrans_OptionB | 6.322 ± 0.902 | 5.165 ± 0.810 | 0.811 ± 0.143 |
| 100 | 100 | Glmtrans_OptionB | 10.215 ± 3.582 | 8.097 ± 3.358 | 0.906 ± 0.046 |
| 100 | 100 | Glmtrans_OptionB | 3.593 ± 1.654 | 2.755 ± 1.540 | 0.680 ± 0.342 |
| 100 | 100 | Glmtrans_OptionB | 14.262 ± 3.476 | 11.720 ± 3.550 | 0.906 ± 0.060 |
| 100 | 100 | IPWTransport | 6.313 ± 0.889 | 5.156 ± 0.825 | 0.810 ± 0.144 |
| 100 | 100 | IPWTransport | 8.617 ± 3.601 | 6.661 ± 3.258 | 0.789 ± 0.241 |
| 100 | 100 | IPWTransport | 3.616 ± 1.677 | 2.755 ± 1.527 | 0.685 ± 0.331 |
| 100 | 100 | IPWTransport | 14.153 ± 3.611 | 11.584 ± 3.647 | 0.897 ± 0.056 |
| 100 | 100 | OutcomeModelTransport | 6.331 ± 0.892 | 5.172 ± 0.808 | 0.813 ± 0.143 |
| 100 | 100 | OutcomeModelTransport | 8.691 ± 3.926 | 6.955 ± 3.632 | 0.801 ± 0.241 |
| 100 | 100 | OutcomeModelTransport | 3.589 ± 1.653 | 2.749 ± 1.535 | 0.680 ± 0.342 |
| 100 | 100 | OutcomeModelTransport | 14.284 ± 3.522 | 11.720 ± 3.553 | 0.908 ± 0.059 |
| 100 | 100 | ProxyOnly | 5.123 ± 0.897 | 4.216 ± 0.781 | 0.636 ± 0.090 |
| 100 | 100 | ProxyOnly | 4.654 ± 3.646 | 3.728 ± 3.599 | 0.297 ± 0.347 |
| 100 | 100 | ProxyOnly | 2.737 ± 2.290 | 2.026 ± 2.100 | 0.439 ± 0.672 |
| 100 | 100 | ProxyOnly | 6.004 ± 4.412 | 5.195 ± 3.701 | 0.411 ± 0.141 |
| 100 | 100 | TargetOnlyDR | 5.807 ± 1.360 | 4.972 ± 1.067 | 0.793 ± 0.077 |
| 100 | 100 | TargetOnlyDR | 6.375 ± 3.173 | 5.205 ± 3.081 | 0.519 ± 0.149 |
| 100 | 100 | TargetOnlyDR | 4.006 ± 1.223 | 3.172 ± 0.918 | 0.846 ± 0.058 |
| 100 | 100 | TargetOnlyDR | 8.050 ± 4.095 | 7.106 ± 3.958 | 0.524 ± 0.137 |
| 200 | 200 | AnchorOnly | 5.299 ± 2.864 | 4.274 ± 2.626 | 0.634 ± 0.471 |
| 200 | 200 | AnchorOnly | 6.049 ± 2.400 | 4.785 ± 2.101 | 0.607 ± 0.148 |
| 200 | 200 | AnchorOnly | 9.525 ± 3.018 | 7.833 ± 3.163 | 0.540 ± 0.138 |
| 200 | 200 | AnchorOnly | 4.571 ± 2.181 | 3.764 ± 1.782 | 0.906 ± 0.035 |
| 200 | 200 | AnchorPlugin | 5.245 ± 2.186 | 4.178 ± 2.119 | 0.688 ± 0.351 |
| 200 | 200 | AnchorPlugin | 7.152 ± 1.557 | 5.616 ± 1.331 | 0.786 ± 0.043 |
| 200 | 200 | AnchorPlugin | 11.476 ± 1.117 | 9.269 ± 1.400 | 0.684 ± 0.151 |
| 200 | 200 | AnchorPlugin | 4.179 ± 1.747 | 3.362 ± 1.436 | 0.826 ± 0.151 |
| 200 | 200 | EntropyBalancing | 5.318 ± 1.885 | 4.283 ± 1.810 | 0.847 ± 0.128 |
| 200 | 200 | EntropyBalancing | 8.320 ± 1.842 | 6.471 ± 1.563 | 0.896 ± 0.067 |
| 200 | 200 | EntropyBalancing | 13.195 ± 2.390 | 10.724 ± 1.776 | 0.778 ± 0.174 |
| 200 | 200 | EntropyBalancing | 3.937 ± 1.525 | 3.258 ± 1.268 | 0.829 ± 0.175 |
| 200 | 200 | Glmtrans_Auto | 6.441 ± 3.003 | 5.188 ± 2.746 | 0.990 ± 0.012 |
| 200 | 200 | Glmtrans_Auto | 9.254 ± 2.486 | 7.239 ± 2.071 | 0.994 ± 0.004 |
| 200 | 200 | Glmtrans_Auto | 17.426 ± 4.939 | 14.268 ± 4.134 | 0.995 ± 0.002 |
| 200 | 200 | Glmtrans_Auto | 5.074 ± 2.376 | 4.164 ± 1.959 | 0.988 ± 0.007 |
| 200 | 200 | Glmtrans_DR_CrossFit | 6.445 ± 2.999 | 5.189 ± 2.748 | 0.993 ± 0.009 |
| 200 | 200 | Glmtrans_DR_CrossFit | 9.246 ± 2.487 | 7.241 ± 2.076 | 0.994 ± 0.004 |
| 200 | 200 | Glmtrans_DR_CrossFit | 17.305 ± 4.874 | 14.188 ± 4.118 | 0.992 ± 0.002 |
| 200 | 200 | Glmtrans_DR_CrossFit | 5.081 ± 2.376 | 4.167 ± 1.953 | 0.990 ± 0.002 |
| 200 | 200 | Glmtrans_OptionB | 5.342 ± 1.909 | 4.323 ± 1.844 | 0.852 ± 0.124 |
| 200 | 200 | Glmtrans_OptionB | 7.992 ± 1.948 | 6.221 ± 1.584 | 0.865 ± 0.019 |
| 200 | 200 | Glmtrans_OptionB | 14.910 ± 2.792 | 12.098 ± 2.241 | 0.867 ± 0.104 |
| 200 | 200 | Glmtrans_OptionB | 4.137 ± 1.933 | 3.411 ± 1.549 | 0.844 ± 0.186 |
| 200 | 200 | IPWTransport | 5.349 ± 1.918 | 4.299 ± 1.818 | 0.848 ± 0.125 |
| 200 | 200 | IPWTransport | 8.384 ± 1.772 | 6.507 ± 1.522 | 0.902 ± 0.070 |
| 200 | 200 | IPWTransport | 13.553 ± 2.221 | 11.062 ± 1.616 | 0.804 ± 0.181 |
| 200 | 200 | IPWTransport | 3.940 ± 1.526 | 3.268 ± 1.264 | 0.827 ± 0.176 |
| 200 | 200 | OutcomeModelTransport | 5.345 ± 1.912 | 4.303 ± 1.826 | 0.853 ± 0.123 |
| 200 | 200 | OutcomeModelTransport | 8.371 ± 1.712 | 6.522 ± 1.431 | 0.907 ± 0.069 |
| 200 | 200 | OutcomeModelTransport | 13.720 ± 1.749 | 10.906 ± 1.354 | 0.812 ± 0.183 |
| 200 | 200 | OutcomeModelTransport | 3.943 ± 1.532 | 3.263 ± 1.270 | 0.822 ± 0.175 |
| 200 | 200 | ProxyOnly | 3.998 ± 2.536 | 3.363 ± 2.447 | 0.317 ± 0.907 |
| 200 | 200 | ProxyOnly | 4.840 ± 1.797 | 3.914 ± 1.658 | 0.497 ± 0.102 |
| 200 | 200 | ProxyOnly | 7.426 ± 1.877 | 6.270 ± 1.747 | 0.463 ± 0.057 |
| 200 | 200 | ProxyOnly | 3.647 ± 1.441 | 2.900 ± 1.115 | 0.729 ± 0.089 |
| 200 | 200 | TargetOnlyDR | 5.348 ± 2.975 | 4.251 ± 2.668 | 0.627 ± 0.476 |
| 200 | 200 | TargetOnlyDR | 6.353 ± 2.431 | 4.978 ± 2.032 | 0.664 ± 0.072 |
| 200 | 200 | TargetOnlyDR | 10.216 ± 3.430 | 8.133 ± 3.243 | 0.559 ± 0.110 |
| 200 | 200 | TargetOnlyDR | 4.668 ± 2.242 | 3.827 ± 1.802 | 0.903 ± 0.034 |
| 500 | 500 | AnchorOnly | 9.310 ± 3.144 | 7.391 ± 3.141 | 0.552 ± 0.220 |
| 500 | 500 | AnchorOnly | 5.984 ± 1.440 | 4.564 ± 1.280 | 0.626 ± 0.080 |
| 500 | 500 | AnchorOnly | 4.102 ± 1.254 | 3.353 ± 1.376 | 0.886 ± 0.054 |
| 500 | 500 | AnchorOnly | 5.713 ± 2.044 | 4.547 ± 1.999 | 0.780 ± 0.100 |
| 500 | 500 | AnchorPlugin | 10.611 ± 2.101 | 8.605 ± 2.153 | 0.686 ± 0.155 |
| 500 | 500 | AnchorPlugin | 7.191 ± 1.592 | 5.620 ± 1.364 | 0.760 ± 0.106 |
| 500 | 500 | AnchorPlugin | 4.151 ± 1.364 | 3.280 ± 1.373 | 0.862 ± 0.047 |
| 500 | 500 | AnchorPlugin | 4.663 ± 1.159 | 3.719 ± 1.366 | 0.646 ± 0.151 |
| 500 | 500 | EntropyBalancing | 11.712 ± 2.176 | 9.404 ± 2.000 | 0.778 ± 0.113 |
| 500 | 500 | EntropyBalancing | 7.840 ± 2.503 | 6.194 ± 2.015 | 0.849 ± 0.192 |
| 500 | 500 | EntropyBalancing | 4.209 ± 1.400 | 3.332 ± 1.359 | 0.869 ± 0.086 |
| 500 | 500 | EntropyBalancing | 4.962 ± 1.407 | 3.803 ± 1.246 | 0.712 ± 0.158 |
| 500 | 500 | Glmtrans_Auto | 15.261 ± 3.238 | 12.152 ± 2.856 | 0.999 ± 0.001 |
| 500 | 500 | Glmtrans_Auto | 9.212 ± 2.030 | 7.197 ± 1.682 | 0.997 ± 0.004 |
| 500 | 500 | Glmtrans_Auto | 4.645 ± 1.500 | 3.692 ± 1.447 | 0.991 ± 0.007 |
| 500 | 500 | Glmtrans_Auto | 7.093 ± 2.268 | 5.620 ± 2.087 | 0.998 ± 0.002 |
| 500 | 500 | Glmtrans_DR_CrossFit | 15.267 ± 3.237 | 12.151 ± 2.861 | 0.999 ± 0.000 |
| 500 | 500 | Glmtrans_DR_CrossFit | 9.208 ± 2.031 | 7.197 ± 1.695 | 0.996 ± 0.004 |
| 500 | 500 | Glmtrans_DR_CrossFit | 4.645 ± 1.501 | 3.694 ± 1.441 | 0.993 ± 0.006 |
| 500 | 500 | Glmtrans_DR_CrossFit | 7.092 ± 2.266 | 5.618 ± 2.087 | 0.998 ± 0.003 |
| 500 | 500 | Glmtrans_OptionB | 12.562 ± 1.843 | 9.945 ± 1.953 | 0.830 ± 0.137 |
| 500 | 500 | Glmtrans_OptionB | 7.833 ± 2.360 | 6.201 ± 1.918 | 0.854 ± 0.139 |
| 500 | 500 | Glmtrans_OptionB | 4.301 ± 1.380 | 3.424 ± 1.332 | 0.923 ± 0.036 |
| 500 | 500 | Glmtrans_OptionB | 5.068 ± 1.383 | 3.988 ± 1.367 | 0.717 ± 0.150 |
| 500 | 500 | IPWTransport | 12.094 ± 1.941 | 9.542 ± 1.878 | 0.796 ± 0.116 |
| 500 | 500 | IPWTransport | 7.864 ± 2.477 | 6.206 ± 1.981 | 0.858 ± 0.180 |
| 500 | 500 | IPWTransport | 4.209 ± 1.400 | 3.334 ± 1.362 | 0.869 ± 0.086 |
| 500 | 500 | IPWTransport | 4.985 ± 1.376 | 3.815 ± 1.262 | 0.711 ± 0.156 |
| 500 | 500 | OutcomeModelTransport | 12.588 ± 1.801 | 9.949 ± 1.955 | 0.830 ± 0.137 |
| 500 | 500 | OutcomeModelTransport | 7.998 ± 2.268 | 6.333 ± 1.821 | 0.877 ± 0.149 |
| 500 | 500 | OutcomeModelTransport | 4.260 ± 1.462 | 3.370 ± 1.434 | 0.880 ± 0.099 |
| 500 | 500 | OutcomeModelTransport | 5.066 ± 1.382 | 3.993 ± 1.363 | 0.716 ± 0.151 |
| 500 | 500 | ProxyOnly | 6.624 ± 2.284 | 5.067 ± 2.008 | 0.381 ± 0.191 |
| 500 | 500 | ProxyOnly | 5.453 ± 1.730 | 4.312 ± 1.570 | 0.542 ± 0.091 |
| 500 | 500 | ProxyOnly | 3.529 ± 1.411 | 2.805 ± 1.319 | 0.727 ± 0.122 |
| 500 | 500 | ProxyOnly | 3.757 ± 1.382 | 2.936 ± 1.412 | 0.470 ± 0.296 |
| 500 | 500 | TargetOnlyDR | 9.479 ± 2.485 | 7.175 ± 2.810 | 0.541 ± 0.209 |
| 500 | 500 | TargetOnlyDR | 6.324 ± 1.484 | 4.928 ± 1.317 | 0.670 ± 0.079 |
| 500 | 500 | TargetOnlyDR | 4.191 ± 1.402 | 3.354 ± 1.393 | 0.888 ± 0.045 |
| 500 | 500 | TargetOnlyDR | 5.822 ± 2.115 | 4.554 ± 1.985 | 0.788 ± 0.080 |

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

1. **Best overall PEHE:** Glmtrans_DR_CrossFit achieves lowest average PEHE (0.265)
2. **Best overall ATE Error:** Glmtrans_Auto achieves lowest average ATE error (0.0227)
3. **Lowest policy regret:** Glmtrans_DR_CrossFit (0.0030)
4. **Scaling:** Glmtrans_Auto ATE error decreases with higher m0
5. **Best ranking:** Glmtrans_DR_CrossFit achieves highest Spearman correlation (0.998)

---

## Appendix: Configuration

```python
sweep_param = 'm0'
sweep_values = [50, 100, 200, 500]
base_scenario = {'n_proxy_total': 20000, 'C_sources': 10, 'nontransfer_scale': 0.1, 'use_fair_dgp': True, 'overlap_lambda': 0.25, 'intercept_drift_scale': 0.5}
```

