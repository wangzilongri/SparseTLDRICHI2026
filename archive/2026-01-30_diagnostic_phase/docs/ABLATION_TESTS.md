# Ablation Test Specification

## Overview

This document specifies comprehensive ablation tests for the Placebo-Anchored DR-Learner, extending beyond the manuscript's original experiments.

---

## 1. Core Component Ablations (PRIORITY 1)

**Goal**: Isolate the contribution of each algorithmic stage

### Methods to Compare

| Method | Stage 1 (Proxy) | Stage 2 (Anchor) | Stage 3 (DR) | Use Case |
|--------|----------------|------------------|--------------|----------|
| **No-Transfer** | ✗ | ✗ | ✗ | Target placebo only baseline |
| **Proxy-Only** | ✓ | ✗ | ✗ | Tests: Do we need anchoring? |
| **Proxy+DR** | ✓ | ✗ | ✓ | Tests: Can DR alone handle shift? |
| **Anchor-Only** | ✓ | ✓ | ✗ | Tests: Do we need DR correction? |
| **Proposed (Full)** | ✓ | ✓ | ✓ | Complete method |

### Metrics (for each method)

1. **PEHE** (Precision in Estimation of Heterogeneous Effects)
   - √E[(τ(x) - τ̂(x))²]
   - Primary metric for patient-level accuracy

2. **ATE Error**
   - |E[τ(x)] - E[τ̂(x)]|
   - Population-level accuracy

3. **Calibration RMSE (μ₀)**
   - √E[(μ₀(x) - μ̂₀(x))²]
   - Baseline risk calibration

4. **Calibration RMSE (μ₁)**
   - √E[(μ₁(x) - μ̂₁(x))²]
   - Treated outcome calibration

5. **R² (CATE)**
   - Fraction of heterogeneity variance explained

### Expected Results

| Method | PEHE | ATE Error | Cal(μ₀) | Cal(μ₁) | Notes |
|--------|------|-----------|---------|---------|-------|
| No-Transfer | **Worst** | High | Best | N/A | Cannot extrapolate |
| Proxy-Only | Medium | Medium | Bad | Bad | Inherits source bias |
| Proxy+DR | Medium | Medium-Low | Bad | Bad | DR helps but not enough |
| Anchor-Only | Medium-Low | **Best** | Best | Good | Good marginal effect |
| Proposed | **Best** | Low | Best | Best | Optimal balance |

### Implementation

```python
def run_core_ablation(data, n_runs=20):
    """Run core component ablation study."""
    methods = {
        'No-Transfer': NoTransferBaseline(),
        'Proxy-Only': ProxyOnlyBaseline(),
        'Proxy+DR': ProxyDRBaseline(),  # NEW
        'Anchor-Only': AnchorOnlyBaseline(),
        'Proposed': PlaceboAnchoredDRLearner()
    }
    
    results = []
    for run in range(n_runs):
        data_run = generate_data(seed=1000 + run)
        
        for name, model in methods.items():
            model.fit(...)
            metrics = evaluate_all_metrics(model, data_run)
            metrics['Method'] = name
            results.append(metrics)
    
    return pd.DataFrame(results)
```

---

## 2. Architectural Ablations (PRIORITY 2)

**Goal**: Test sensitivity to modeling choices

### 2.1 Proxy Model Complexity

Vary Stage 1 learner:

```python
proxy_learners = {
    'Linear': LinearRegression(),
    'Ridge': RidgeCV(),
    'RandomForest-Shallow': RandomForestRegressor(max_depth=3),
    'RandomForest-Deep': RandomForestRegressor(max_depth=10),
    'GradientBoosting': GradientBoostingRegressor(),
    'NeuralNet-Small': MLPRegressor(hidden_layers=(50, 25))
}
```

**Research Question**: How much does Stage 1 flexibility matter given Stage 2 correction?

### 2.2 Sparsity-Inducing Mechanism

Vary Stage 2 correction:

```python
correction_methods = {
    'LASSO': LassoCV(),                    # ℓ₁ penalty (sparse)
    'Ridge': RidgeCV(),                    # ℓ₂ penalty (dense)
    'ElasticNet': ElasticNetCV(),          # ℓ₁ + ℓ₂
    'OLS': LinearRegression(),             # No regularization
    'AdaptiveLASSO': AdaptiveLassoCV(),    # Weighted ℓ₁
}
```

**Research Question**: Is sparsity assumption (A5) critical?

### 2.3 CATE Model Complexity

Vary Stage 3 learner:

```python
cate_learners = {
    'Linear': LinearRegression(),
    'KernelRidge': KernelRidge(kernel='rbf'),
    'RandomForest': RandomForestRegressor(),
    'GradientBoosting': GradientBoostingRegressor(),
    'CausalForest': CausalForest()  # if available
}
```

### 2.4 Cross-Fitting Variants

```python
crossfit_strategies = {
    'K=2': 2,
    'K=3': 3,
    'K=5': 5,
    'K=10': 10,
    'No-CrossFit': 1,  # Fit on all, no splitting
}
```

**Research Question**: Bias-variance tradeoff in cross-fitting

### 2.5 Intercept in Stage 2

```python
fit_intercept_options = {
    'With-Intercept': True,   # Absorbs global shift
    'No-Intercept': False,    # Forces correction through covariates
}
```

**Research Question**: Can intercept capture non-covariate shift?

---

## 3. Data Regime Ablations (PRIORITY 3)

**Goal**: Characterize sample efficiency and data requirements

### 3.1 Gold Budget Sweep

```python
gold_budget = [10, 20, 50, 100, 200, 500, 1000]
# For each m₀, measure performance
```

**Expected**: Diminishing returns curve; find minimum viable m₀

### 3.2 Proxy Budget Sweep

```python
proxy_budget = [100, 500, 1000, 2000, 5000, 10000]
# n_source total across all sites
```

**Expected**: Proxy-Only and Proposed both improve, but Proposed benefits more

### 3.3 Target Treated Fraction

```python
treated_fractions = [0.0, 0.1, 0.2, 0.3, 0.5]
# Vary n₁ / (n₀ + n₁) in target
```

**Research Question**: At what point does Option A outperform Option B?

### 3.4 Number of Source Sites

```python
n_source_sites = [1, 2, 3, 5, 10, 20]
# Hold total n_source constant, vary heterogeneity
```

**Research Question**: Does pooling many heterogeneous sites hurt or help?

### 3.5 Proxy-Gold Budget Tradeoff

```python
# Fixed total budget: n_proxy + n_gold = N
for gold_frac in [0.1, 0.2, 0.3, 0.5]:
    n_gold = int(N * gold_frac)
    n_proxy = N - n_gold
```

**Research Question**: Optimal allocation of data collection budget

---

## 4. Robustness to Violations (PRIORITY 1)

**Goal**: Stress-test working assumptions

### 4.1 Covariate Shift Magnitude (Assumption A4)

```python
shift_scales = [0.0, 0.3, 0.5, 0.8, 1.0, 1.5, 2.0, 3.0]
# Generate: X_target ~ N(shift, I), X_source ~ N(0, I)
# Measure: d_TV(P(X|target), P(X|source))
```

**Expected**: 
- All methods degrade as shift increases
- Proposed degrades most gracefully
- Proxy-Only collapses first

**Metric**: Plot PEHE vs shift_scale for all methods

### 4.2 Transport Bias Sparsity (Assumption A5)

```python
true_sparsities = [1, 2, 3, 5, 8, 10, 20]  # ||δ||₀
# Generate δ with controlled sparsity
```

**Expected**:
- LASSO recovers well when s ≤ 3
- Performance degrades for s > 5
- Converges to Proxy-Only as s → p

**Metric**: Plot PEHE vs sparsity for Proposed

### 4.3 Cross-Arm Coupling Strength (Assumption A6)

```python
rho_values = [0.0, 0.3, 0.5, 0.7, 0.9, 0.95, 1.0]
# δ_{1,0} = ρ * δ_{0,0} + √(1-ρ²) * η
```

**Expected**:
- Option B works when ρ ≥ 0.7
- Option A insensitive to ρ (if target has treated)
- Shared bias assumption valid in most settings

**Metric**: Plot PEHE(Option B) and PEHE(Option A) vs ρ

### 4.4 Outcome Model Misspecification

Test non-linear ground truth:

```python
dgp_variants = {
    'Linear': lambda X: β'X,
    'Quadratic': lambda X: β'X + γ'(X²),
    'Interactions-2way': lambda X: β'X + Σᵢⱼ θᵢⱼ Xᵢ Xⱼ,
    'Piecewise-Linear': lambda X: β₁'X if X[0]>0 else β₂'X,
    'Sigmoid': lambda X: 1/(1 + exp(-β'X)),
}
```

**Expected**:
- Flexible proxy models (RF, GBM) handle non-linearity
- Linear proxy fails on non-linear DGP
- LASSO correction assumes linear transport bias (may fail)

### 4.5 Propensity Violations

#### 4.5.1 Unequal Randomization

```python
propensities = [0.2, 0.3, 0.5, 0.7, 0.8]
# Within-site randomization probability
```

**Expected**: DR robust as long as e_c known

#### 4.5.2 Overlap Violations

```python
overlap_strengths = {
    'Strong': e(x) ∈ [0.2, 0.8],
    'Moderate': e(x) ∈ [0.1, 0.9],
    'Weak': e(x) ∈ [0.05, 0.95],
    'Violated': e(x) ∈ [0.01, 0.99],
}
```

**Expected**: DR breaks down in 'Violated' regime

#### 4.5.3 Propensity Estimation Error

```python
# True: e(x) = 0.5 (known)
# Estimated: ê(x) ~ N(0.5, σ²)
estimation_errors = [0.0, 0.05, 0.1, 0.15, 0.2]
```

**Research Question**: How sensitive is DR to propensity misspecification?

### 4.6 Heteroskedastic Noise

```python
noise_models = {
    'Homoskedastic': lambda X: σ,
    'Covariate-Dependent': lambda X: σ * (1 + 0.5 * X[0]²),
    'Treatment-Dependent': lambda X, A: σ * (1 + 0.5 * A),
}
```

**Expected**: DR estimator still consistent, but efficiency loss

---

## 5. Comparative Baselines (PRIORITY 2)

**Goal**: Compare against state-of-the-art methods

### Methods

1. **IPD Network Meta-Analysis**
   - Standard frequentist IPD-NMA with random effects
   - Requires: Connected network (fails in disconnected setting)
   - Implementation: `netmeta` R package or custom

2. **TMLE with Inverse Probability Weighting**
   - Targeted maximum likelihood with transport weights
   - Reference: van der Laan (2011)
   - Implementation: `tmle` package

3. **Causal Forest (Target Only)**
   - No transfer learning, rich target data baseline
   - Reference: Wager & Athey (2018)
   - Implementation: `grf` package

4. **Augmented IPW (Multi-Site)**
   - AIPW with site indicators as covariates
   - Reference: Robins et al. (1995)

5. **Multi-Task Proxy-Gold (Bastani et al. 2021)**
   - Direct comparison to our methodological predecessor
   - Differences: assumes linear proxy, no DR layer

6. **Domain Adaptation via Importance Weighting**
   - Covariate shift correction via density ratio
   - Reference: Shimodaira (2000)

### Comparison Protocol

```python
baselines = {
    'Proposed': PlaceboAnchoredDRLearner(),
    'IPD-NMA': IPDNetworkMetaAnalysis(),
    'TMLE-Transport': TMLETransport(),
    'CausalForest': CausalForestBaseline(),
    'AIPW-MultiSite': AIPWMultiSite(),
    'Bastani2021': ProxyGoldLearner(),  # Linear only
    'DomainAdapt': DensityRatioWeighting()
}

# Test on multiple scenarios
scenarios = ['disconnected', 'mild_shift', 'severe_shift', 'sparse_gold']
```

---

## 6. Negative Controls & Diagnostics (PRIORITY 3)

**Goal**: Validate implementation correctness

### 6.1 Null Treatment Effect

```python
# DGP: τ(x) ≡ 0 (no treatment effect)
# Expected: All methods should predict τ̂(x) ≈ 0
```

### 6.2 Null Transport Bias

```python
# DGP: δ_{a,c} ≡ 0 (no site heterogeneity)
# Expected: Proxy-Only = Proposed (anchoring unnecessary)
```

### 6.3 Known Null Covariates

```python
# Include X_null with β_null = 0
# Expected: LASSO should select δ_null = 0
```

### 6.4 Perfect Proxy Setting

```python
# DGP: Target distribution = Source distribution
# Expected: Proxy-Only achieves optimal performance
```

### 6.5 Oracle Corrections

```python
# Use true δ_{a,c} instead of estimated δ̂
# Provides upper bound on performance
```

---

## 7. Sensitivity Analyses (PRIORITY 3)

### 7.1 Hyperparameter Sensitivity

| Parameter | Default | Range | Impact |
|-----------|---------|-------|--------|
| `n_folds` | 5 | [2, 3, 5, 10] | Bias-variance tradeoff |
| `lasso_cv_folds` | 5 | [3, 5, 10] | Lambda stability |
| `max_depth` (proxy) | 8 | [3, 5, 8, 12] | Proxy flexibility |
| `n_estimators` (proxy) | 200 | [50, 100, 200, 500] | Variance reduction |

### 7.2 Bootstrap Stability

```python
# Bootstrap target gold samples
for b in range(B_bootstrap):
    indices = resample(range(m_0))
    X_boot, Y_boot = X_gold[indices], Y_gold[indices]
    delta_boot = fit_lasso(X_boot, Y_boot)
    
# Measure: std(δ̂) across bootstraps
```

### 7.3 Feature Selection Stability

```python
# Measure: Jaccard similarity of selected features across folds
selected_features_per_fold = [...]
stability = jaccard(selected_features_per_fold)
```

---

## 8. Visualization Suite

### Required Plots

1. **Box Plots**: PEHE by method (core ablation)
2. **Line Plots**: Metric vs shift_scale (robustness)
3. **Scatter Plots**: True vs Predicted CATE (calibration)
4. **Heatmaps**: Performance across (shift, sparsity) grid
5. **Bar Plots**: Feature importance (which features in δ̂)
6. **Learning Curves**: Performance vs sample size

### Example: Ablation Box Plot

```python
import seaborn as sns
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# PEHE
sns.boxplot(data=results, x='Method', y='PEHE', ax=axes[0])
axes[0].set_title('CATE Estimation Error (PEHE)')

# ATE Error
sns.boxplot(data=results, x='Method', y='ATE_Error', ax=axes[1])
axes[1].set_title('Population Effect Error')

# Calibration
sns.boxplot(data=results, x='Method', y='Calibration_RMSE_mu0', ax=axes[2])
axes[2].set_title('Baseline Risk Calibration')

plt.tight_layout()
```

---

## 9. Experiment Prioritization

### Phase 1: Core Validation (Week 1)
- [ ] Core component ablations (5 methods)
- [ ] Basic robustness: shift, sparsity, rho
- [ ] Negative controls

### Phase 2: Comprehensive Testing (Week 2)
- [ ] Architectural ablations
- [ ] Data regime sweeps
- [ ] Full robustness suite

### Phase 3: Benchmarking (Week 3)
- [ ] Comparative baselines
- [ ] Sensitivity analyses
- [ ] Visualization and reporting

---

## 10. Success Criteria

**Method is successful if**:

1. **Core Ablation**: Proposed achieves lowest PEHE (≥ 80% of runs)
2. **Calibration**: Calibration RMSE ≤ Proxy-Only by 30%+
3. **Robustness**: Maintains advantage under moderate violations (shift ≤ 1.0, s ≤ 5, ρ ≥ 0.7)
4. **Sample Efficiency**: Works with m₀ ≥ 50 (practical gold budget)
5. **Disconnected Setting**: Option B competitive with Option A when ρ ≥ 0.8

**Red Flags**:
- Proposed worse than Proxy-Only in any core ablation
- High sensitivity to hyperparameters
- Collapse under mild assumption violations
- Requires impractically large gold samples (m₀ > 500)

---

## 11. Differences from Manuscript

The manuscript ablations can be improved:

1. **Missing**: Proxy+DR baseline (isolates anchoring contribution)
2. **Limited**: Only 2 baselines (No-Transfer, Proxy-Only)
3. **No**: Architectural ablations (sparsity mechanism, model choices)
4. **Basic**: Data regime tests (only gold budget, not tradeoffs)
5. **Incomplete**: Robustness checks (no misspecification, propensity tests)

This specification addresses all gaps and provides a comprehensive evaluation framework.
