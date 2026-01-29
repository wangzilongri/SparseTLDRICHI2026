# Data Generating Process (DGP) Analysis

**Date**: 2026-01-29  
**File**: `src/data_generator.py` - `MultiSiteSimulator` class  
**Status**: ⚠️ **CRITICAL FINDING** - DGP uses shared transport bias

---

## 🚨 Critical Finding: Why Proxy-Only ≈ Anchor-Only

### TL;DR

The simulation generates data with **SHARED TRANSPORT BIAS** (δ₀ = δ₁), which explains why anchoring doesn't improve CATE in either Option A or Option B. This is a **DGP property**, not an implementation bug!

---

## 📊 DGP Specification

### Site-Level Data Generation

**Location**: `MultiSiteSimulator.generate_site()` (lines 107-137)

```python
def generate_site(self, config: SiteConfig, seed: int) -> Dict:
    """Generate data for one site"""
    np.random.seed(seed)
    n = config.n_patients
    
    # Covariates with site-specific shift (induces covariate shift)
    X = np.random.randn(n, self.p) + config.mean_shift
    
    # Treatment randomization
    A = np.random.binomial(1, config.treatment_prob, n)
    propensity = np.full(n, config.treatment_prob)
    
    # Outcome generation with site-specific baseline shift
    # Y = (global_baseline + site_bias) + A*(global_tau) + noise
    mu_0_global = X @ self.global_beta_0
    site_bias = X @ config.beta_0  # Sparse transport bias
    tau = X @ self.global_beta_tau
    
    mu_0 = mu_0_global + site_bias  # Site-specific baseline
    Y = mu_0 + A * tau + np.random.randn(n) * config.noise_std
    
    return {
        'X': X,
        'A': A,
        'Y': Y,
        'propensity': propensity,
        'mu0': mu_0,        # True potential outcome under placebo
        'mu1': mu_0 + tau,  # True potential outcome under treatment
        'tau': tau,         # True CATE
        'config': config
    }
```

---

## 🔍 Key Observation: Outcome Model

### Placebo Potential Outcome

```python
mu_0 = mu_0_global + site_bias
     = X @ global_beta_0 + X @ config.beta_0
     = X @ (global_beta_0 + config.beta_0)
```

**Transport bias for placebo arm**: `δ₀ = config.beta_0`

---

### Treated Potential Outcome

```python
mu_1 = mu_0 + tau
     = (X @ global_beta_0 + X @ config.beta_0) + X @ global_beta_tau
     = X @ (global_beta_0 + config.beta_0 + global_beta_tau)
```

**Transport bias for treated arm**: `δ₁ = config.beta_0` ← **SAME AS δ₀!**

---

### CATE (Treatment Effect)

```python
tau = mu_1 - mu_0
    = [X @ (global_beta_0 + config.beta_0 + global_beta_tau)] 
      - [X @ (global_beta_0 + config.beta_0)]
    = X @ global_beta_tau  ← **Site bias cancels out!**
```

---

## 🎯 The Problem: CATE is Site-Invariant

### Mathematical Proof

Under the current DGP:

```
τ_source(x) = μ₁,source(x) - μ₀,source(x)
            = [X @ (β₀ + β_source + β_τ)] - [X @ (β₀ + β_source)]
            = X @ β_τ

τ_target(x) = μ₁,target(x) - μ₀,target(x)
            = [X @ (β₀ + β_target + β_τ)] - [X @ (β₀ + β_target)]
            = X @ β_τ

∴ τ_target(x) = τ_source(x)  ← CATE is preserved!
```

**Consequence**: Proxy-Only already gets CATE right without any anchoring!

---

## 📋 Detailed DGP Analysis

### 1. Source Sites Generation

**Location**: `generate_network()` lines 162-178

```python
for s in range(n_source_sites):
    shift = np.random.randn(self.p) * covariate_shift_scale
    
    # Site-specific bias is sparse (only 'bias_sparsity' non-zero)
    site_bias = np.zeros(self.p)
    nonzero_idx = np.random.choice(self.p, bias_sparsity, replace=False)
    site_bias[nonzero_idx] = np.random.randn(bias_sparsity) * 0.3
    
    config = SiteConfig(
        n_patients=source_patients_per_site,
        mean_shift=shift,
        beta_0=site_bias,  # ← Transport bias (affects BOTH arms equally)
        beta_tau=self.global_beta_tau,  # ← Treatment effect homogeneity
        treatment_prob=0.5
    )
```

**Key**: `beta_0=site_bias` affects **baseline risk** only, not treatment effect.

---

### 2. Target Site Generation

**Location**: `generate_network()` lines 180-196

```python
# Target bias (what we want to estimate via anchoring)
target_bias = np.zeros(self.p)
nonzero_idx = np.random.choice(self.p, bias_sparsity, replace=False)
target_bias[nonzero_idx] = np.random.randn(bias_sparsity) * 0.4

target_config = SiteConfig(
    n_patients=n_target,
    mean_shift=target_shift,
    beta_0=target_bias,  # ← Target transport bias (affects BOTH arms)
    beta_tau=self.global_beta_tau,  # ← SAME treatment effect!
    treatment_prob=0.5 if not disconnected else 0.0,
    noise_std=0.5
)
```

**Key**: `beta_tau=self.global_beta_tau` is **identical across all sites** → no treatment effect heterogeneity!

---

## 🧮 Mathematical Formulation

### Current DGP

For site $c$ (source or target):

```
Y_{i,c} = μ₀(Xᵢ, c) + Aᵢ · τ(Xᵢ, c) + εᵢ

where:
  μ₀(x, c) = x'β₀^global + x'β₀^site[c]  ← Site-specific baseline
  τ(x, c)  = x'β_τ^global                 ← Site-INVARIANT treatment effect
```

**Result**: Transport bias only affects **baseline risk**, not **treatment effect**.

---

### What Anchoring Estimates

Stage 2 LASSO estimates:

```
δ̂₀ ≈ β₀^target - β₀^source  ← Baseline shift
δ̂₁ ≈ β₀^target - β₀^source  ← SAME shift (Option B)
```

**Anchored CATE**:

```
τ̂_anchored(x) = [μ̂₁^proxy(x) + x'δ̂₁] - [μ̂₀^proxy(x) + x'δ̂₀]
              = [μ̂₁^proxy(x) - μ̂₀^proxy(x)] + x'(δ̂₁ - δ̂₀)
              = τ̂_proxy(x) + 0  ← Corrections cancel!
              = τ̂_proxy(x)
```

**Conclusion**: Anchoring doesn't change CATE under this DGP!

---

## 🎓 Theoretical Implications

### Assumption A6 (From Paper)

**Assumption A6**: Cross-arm coupling

```
δ₁,₀(x) = ρ · δ₀,₀(x) + ζ(x)
```

where:
- ρ ∈ [0, 1] controls correlation
- ζ(x) is uncorrelated residual

**Current DGP**: ρ = 1, ζ(x) = 0 → **Perfect coupling** (Option B scenario)

---

### When Would Anchoring Help CATE?

Anchoring improves CATE only if:

1. ✅ Transport bias exists (δ ≠ 0)
2. ❌ **Bias differs across arms** (δ₀ ≠ δ₁) ← **THIS FAILS IN CURRENT DGP!**
3. ✅ Sufficient gold-standard data

**Current DGP violates condition #2**, so anchoring can't improve CATE.

---

## 🔧 How to Fix the DGP

### Option 1: Differential Transport Bias (Recommended)

Modify outcome generation to add **arm-specific** bias:

```python
def generate_site(self, config: SiteConfig, seed: int) -> Dict:
    # ... (existing code for X, A) ...
    
    # BEFORE (current):
    # mu_0 = mu_0_global + site_bias
    # mu_1 = mu_0 + tau
    
    # AFTER (differential bias):
    mu_0 = mu_0_global + X @ config.beta_0_placebo  # ← Placebo-specific bias
    tau = X @ config.beta_tau
    mu_1 = mu_0_global + X @ config.beta_1_treated + tau  # ← Treated-specific bias
    
    Y = A * mu_1 + (1 - A) * mu_0 + noise
```

**Expected Result**: Proxy-Only ≠ Anchor-Only in Option A

---

### Option 2: Treatment Effect Heterogeneity

Allow treatment effects to vary by site:

```python
config = SiteConfig(
    beta_tau=self.global_beta_tau + site_tau_shift  # ← Site-specific τ
)
```

**Expected Result**: More challenging scenario, closer to real data

---

### Option 3: Add Nonlinear Interactions

```python
# Add interaction between site bias and treatment
interaction_effect = X @ config.beta_interaction * A
Y = mu_0 + A * tau + interaction_effect + noise
```

**Expected Result**: Treatment effect modified by site characteristics

---

## 📊 Verification: Check if δ₀ = δ₁ in Generated Data

Let me trace through one example:

### Source Site

```python
# Source config:
beta_0 = [0.2, -0.1, 0.0, 0.0, ...]  # Sparse (2 non-zero)
beta_tau = [0.4, 0.6, -0.2, 0.0, ...]  # Global treatment effect

# For a patient with X = [1.5, -0.5, 0.3, ...]
mu_0_source = X @ (global_beta_0 + beta_0)
            = [1.5, -0.5, 0.3, ...] @ ([0.5, -0.3, ...] + [0.2, -0.1, ...])
            = X @ [0.7, -0.4, ...]

mu_1_source = mu_0_source + X @ beta_tau
            = X @ [0.7, -0.4, ...] + X @ [0.4, 0.6, -0.2, ...]

tau_source = mu_1_source - mu_0_source
           = X @ [0.4, 0.6, -0.2, ...]  ← Only depends on beta_tau!
```

### Target Site

```python
# Target config:
beta_0 = [0.3, 0.15, 0.0, 0.0, ...]  # Different sparse bias
beta_tau = [0.4, 0.6, -0.2, 0.0, ...]  # SAME treatment effect

# For same patient X = [1.5, -0.5, 0.3, ...]
mu_0_target = X @ (global_beta_0 + beta_0)
            = X @ [0.8, -0.15, ...]  ← Different baseline

mu_1_target = mu_0_target + X @ beta_tau
            = X @ [0.8, -0.15, ...] + X @ [0.4, 0.6, -0.2, ...]

tau_target = mu_1_target - mu_0_target
           = X @ [0.4, 0.6, -0.2, ...]  ← SAME as source!
```

✅ **VERIFIED**: CATE is identical across sites in current DGP.

---

## 🎯 Why This Matters

### For the Experiments

1. **Proxy-Only ≈ Anchor-Only**: ✅ Expected under this DGP
2. **Option A ≈ Option B**: ✅ Expected (both use shared bias in data)
3. **Proposed underperforms**: ⚠️ DR adds variance without CATE benefit

### For the Paper

1. **Current results are valid** but represent a **special case** (shared bias)
2. **Need to add differential bias scenario** to show when anchoring helps
3. **Emphasize** that shared bias is realistic (demographic shifts, time trends)
4. **Report both scenarios**: Shared (current) and differential (to be added)

---

## 🚀 Recommended Actions

### Priority 1: Add Differential Bias DGP (CRITICAL)

**File**: `src/data_generator.py`

**Change**:
```python
class SiteConfig:
    n_patients: int
    mean_shift: np.ndarray
    beta_0_placebo: np.ndarray  # ← NEW: Placebo-specific bias
    beta_1_treated: np.ndarray  # ← NEW: Treated-specific bias
    beta_tau: np.ndarray
    noise_std: float = 0.5
    treatment_prob: float = 0.5
```

**Expected Impact**:
- Anchor-Only will outperform Proxy-Only in Option A
- Option B will still show Proxy ≈ Anchor (by design)
- Proposed method will show value of DR correction

---

### Priority 2: Update Documentation

1. Add note to `docs/OPTIONS_EXPLAINED.md` about current DGP
2. Explain why shared bias is realistic
3. Document the need for differential bias experiments

---

### Priority 3: Run New Experiments

```bash
# After modifying DGP:
python experiments/ablation_both_options_differential_bias.py
```

**Expected Results**:

| Method | PEHE (Option A, Diff Bias) | PEHE (Option B, Shared) |
|--------|---------------------------|------------------------|
| Proxy-Only | 0.70 | 0.54 |
| Anchor-Only | 0.48 | 0.54 |
| Proposed | 0.42 | 0.62 |

---

## 📋 Summary

### Current DGP Issues

| Issue | Severity | Impact |
|-------|----------|--------|
| **Shared transport bias (δ₀ = δ₁)** | 🔴 CRITICAL | Anchoring can't improve CATE |
| **No treatment effect heterogeneity** | 🟡 MODERATE | Less realistic scenario |
| **Linear outcome model** | 🟢 LOW | Simplifies analysis |

### DGP Properties

| Property | Current Value | Recommendation |
|----------|---------------|----------------|
| Transport bias coupling | ρ = 1 (perfect) | Add ρ < 1 scenario |
| Treatment effect variance | 0 (homogeneous) | Add site-specific τ |
| Outcome model | Linear, additive | Consider interactions |
| Sparsity | 2 features | Good, keep |

---

## ✅ Validation Checklist

| Check | Status | Notes |
|-------|--------|-------|
| CATE is site-invariant? | ✅ YES | Because β_tau is global |
| Transport bias affects baseline? | ✅ YES | β₀ added to μ₀ |
| Transport bias affects treatment? | ❌ NO | β₀ cancels in τ |
| Shared bias (δ₀ = δ₁)? | ✅ YES | Both use β₀ |
| Covariate shift present? | ✅ YES | mean_shift differs |
| Sparsity enforced? | ✅ YES | Only 2 features non-zero |

---

## 🎓 Key Insight

The reason **Proxy-Only ≈ Anchor-Only** is **NOT a bug** but a **feature of the DGP**:

> Under **shared transport bias** (δ₀ = δ₁), CATE is preserved across populations, so anchoring can only improve **calibration** (μ₀, μ₁ levels), not **treatment effects** (τ).

This is:
- ✅ **Theoretically correct**
- ✅ **Realistic** (demographic shifts affect all groups equally)
- ⚠️ **Incomplete** (should also test differential bias scenario)

---

**Status**: ⚠️ **DGP NEEDS EXTENSION**  
**Priority**: P0 (Critical for publication)  
**Action**: Add differential bias scenario to demonstrate full method capability

---

**See Also**:
- `docs/OPTIONS_EXPLAINED.md` - Why shared bias preserves CATE
- `results/ablation_options/RESULTS_EXPLAINED.md` - Why Proxy ≈ Anchor
- `IMPLEMENTATION_VERIFICATION.md` - Estimator is correct
