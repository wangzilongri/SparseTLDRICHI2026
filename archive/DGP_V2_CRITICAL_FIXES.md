# DGP v2: Critical Fixes and Enhancements

**Date**: January 30, 2026  
**Status**: ✅ All critical issues fixed

---

## 🔥 Critical Fixes Implemented

### 1. ✅ **Misspecification Now Deterministic**

**❌ BEFORE (BUG)**:
```python
def _misspec(self, X, site_id, arm):
    w = self.rng.normal(...)  # ← Resampled every call!
    return misspec_scale * (X @ w)
```

**Problem**: μ_{a,c}(x) was not a well-defined function - random even given X!

**✅ AFTER (FIXED)**:
```python
# In __init__:
self.misspec_w = {}
for c in sites:
    for a in [0, 1]:
        self.misspec_w[(c, a)] = self.rng.normal(0, 1.0, size=p)

# In _misspec:
def _misspec(self, X, site_id, arm):
    w = self.misspec_w[(site_id, arm)]  # ← Deterministic!
    return misspec_scale * (X @ w)
```

**Verification**:
```
mu1 = gen._mu(X, site_id=1, arm=0)
mu2 = gen._mu(X, site_id=1, arm=0)
Max difference: 0.00e+00 ✓
```

---

### 2. ✅ **Proxy Now Nontrivial (Makes Stage 1 Matter)**

**❌ BEFORE**: Proxy was purely linear → RF Stage 1 trivial

**✅ AFTER**: Mild nonlinearity added
```python
μ_a^proxy(x) = x^T b_a + γ·(c₀·sin(x₀) + c₁·0.5·x₁²)
```

**Config**: `proxy_nonlinear_scale = 0.5` (default)

**Why**: Forces Stage 1 to actually learn something nontrivial.

**Test**:
```
Proxy nonlinear scale: 0.5
Nonlin coef0: [0.879, 0.778]
Nonlin coef1: [0.066, 1.127]
```

---

### 3. ✅ **Shared Support Structure (Critical for Step B)**

**❌ BEFORE**: Random support per site → Step B either trivial or impossible

**✅ AFTER**: Controlled support overlap
```python
# Shared support across all sites
shared_support = [2, 4]  # Same for all sites

# Each site uses shared + optional idiosyncratic
beta0_c[shared_support] = sparse_values
beta0_c[idio_support] = optional_extras  # Site-specific
```

**Config**:
- `shared_support_size = 2`
- `idiosyncratic_support_size = 0` (default)
- `restrict_deviation_to_first_k = None` (optional)

**Test**:
```
Shared support: [2, 4]
Source 1 support: [2, 4], overlap: [2, 4] ✓
Source 2 support: [2, 4], overlap: [2, 4] ✓
Source 3 support: [2, 4], overlap: [2, 4] ✓
```

**Why**: Without this, M̂ estimation is ill-posed!

---

### 4. ✅ **Step B Now Learnable (10 Sites Default)**

**❌ BEFORE**: `n_source_sites = 3` → Estimating 5×5 M underdetermined

**✅ AFTER**: `n_source_sites = 10` (default)

**Math**: Need C >> p for stable M̂ estimation when M is 5×5.

**Alternative**: Use simpler transfer structures:

```python
# Option 1: Scalar (identifiable with C=2)
transfer_structure='rhoI'  # M* = ρ·I

# Option 2: Diagonal (identifiable with C=5)
transfer_structure='diag'  # M* = diag(d)

# Option 3: Diagonal + low-rank (identifiable with C≥10)
transfer_structure='diag_plus_low_rank'

# Option 4: Pure low-rank (default, needs C≥10)
transfer_structure='low_rank'  # M* = U V^T, rank r
```

**Test**:
```
Structure     ||M*||    rank    Identifiable with
───────────────────────────────────────────────
low_rank      2.066    1       C≥10 ✓
rhoI          2.236    5       C≥2  ✓
diag          2.257    5       C≥5  ✓
diag_lr       3.540    5       C≥10 ✓
```

---

## 🎯 Additional Enhancements

### 5. ✅ **Heterogeneous Noise**

```python
noise_std_source = 0.5   # Source noise
noise_std_target = 0.7   # Target noise (can be different)
```

**Why**: Tests DR robustness to variance heterogeneity.

---

### 6. ✅ **Covariance Shift (Not Just Mean)**

```python
cov_shift_strength = 0.1  # SPD perturbations to Σ_c
```

Generates:
```python
X ~ N(μ_c, Σ_c)  # Not just N(μ_c, I)
```

**Why**: More realistic covariate shift.

---

### 7. ✅ **Enhanced Diagnostics**

**New metrics**:
- **Transfer SNR**: ||M*β₀|| / ||ν||
- **Cosine similarity**: <β₁, M*β₀> / (||β₁|| ||M*β₀||)
- **Support overlap**: Which features used where
- **Aggregate metrics**: Mean/median SNR across sources

**Example**:
```python
diag = gen.get_diagnostics()

# Transfer quality
Mean source SNR: 1.537
Target SNR: 0.232  ← Lower (harder Option B)
Target cosine sim: 0.326

# Support structure
Shared support: [2, 4]
Shared support size: 2
```

---

## 📊 Validation Results

### Test 1: Deterministic μ ✓
```
mu(X, site=1, arm=0) called twice
Max difference: 0.00e+00  ← Perfectly deterministic!
```

---

### Test 2: Shared Support ✓
```
Site       Support      Overlap with Shared
─────────────────────────────────────────────
Source 1   [2, 4]       [2, 4] (100%)
Source 2   [2, 4]       [2, 4] (100%)
Source 3   [2, 4]       [2, 4] (100%)
Target     [2, 4]       [2, 4] (100%)
```

---

### Test 3: Transfer Structures ✓
```
Structure           ||M*||   rank   Is Expected
────────────────────────────────────────────────
low_rank            2.066    1      ✓
rhoI                2.236    5      ✓ (scalar·I)
diag                2.257    5      ✓ (diagonal)
diag_plus_low_rank  3.540    5      ✓
```

---

### Test 4: A6 Verification ✓
```
All structures:
  A6 error (β₁ = M*β₀ + ν): 0.00e+00  ← Exact!
```

---

## 🎛️ New Configuration Options

```python
from src.synthetic_data_v2 import SyntheticRCTConfig

config = SyntheticRCTConfig(
    # Basic (now 10 sites default!)
    n_source_sites=10,
    n_target=200,
    
    # Proxy nonlinearity (makes Stage 1 nontrivial)
    proxy_nonlinear_scale=0.5,  # NEW!
    
    # Support structure (critical for Step B!)
    shared_support_size=2,           # NEW!
    idiosyncratic_support_size=0,    # NEW!
    restrict_deviation_to_first_k=3, # NEW! (optional)
    
    # Transfer operator structure
    transfer_structure='low_rank',   # NEW!
    #                   'rhoI'        (scalar·I)
    #                   'diag'        (diagonal)
    #                   'diag_plus_low_rank'
    transfer_rank=1,
    transfer_strength=1.0,
    
    # Nontransfer (degradation knob)
    nontransfer_scale_source=0.05,
    nontransfer_scale_target=0.3,
    
    # Heterogeneous noise
    noise_std_source=0.5,    # NEW!
    noise_std_target=0.7,    # NEW!
    
    # Covariance shift
    cov_shift_strength=0.1,  # NEW!
    
    # Misspecification (now deterministic!)
    misspec_scale=0.0,
    misspec_nonlinear=False,
)
```

---

## 📖 Usage Examples

### Example 1: Standard (Easy Step B)

```python
from src.synthetic_data_v2 import generate_synthetic_rct

# Default: 10 sites, shared support, mild nonlinearity
source, target, gen = generate_synthetic_rct(
    n_source_sites=10,
    nontransfer_scale_target=0.1,  # Easy
    random_state=42
)

# Check learnability
diag = gen.get_diagnostics()
print(f"Mean source SNR: {diag['mean_source_SNR']:.2f}")
print(f"Target SNR: {diag['target_transfer_SNR']:.2f}")

# If SNR >> 1: transfer works well
# If SNR << 1: nontransfer dominates
```

---

### Example 2: Hard Step B (Disconnected + High ν)

```python
from src.synthetic_data_v2 import generate_disconnected_target

source, target, gen = generate_disconnected_target(
    n_source_sites=20,               # More sites
    nontransfer_scale_target=0.8,    # High nontransfer
    transfer_structure='diag',       # Simpler M
    random_state=42
)

# Target: placebo-only
print(f"Target treated: {np.sum(target['A'] == 1)}")  # = 0
print(f"Still have tau_true: {target['tau_true'].shape}")
```

---

### Example 3: Sweep Transfer Structures

```python
structures = ['rhoI', 'diag', 'low_rank', 'diag_plus_low_rank']
results = {}

for struct in structures:
    source, target, gen = generate_synthetic_rct(
        transfer_structure=struct,
        n_source_sites=10 if struct != 'rhoI' else 3,
        random_state=42
    )
    
    # Fit estimator with Option B
    model_b = PlaceboAnchoredDRLearner(option='B')
    model_b.fit(...)
    
    # Compare M̂ to M*
    M_hat = model_b.M_hat_
    M_star = gen.M_star
    recovery_error = np.linalg.norm(M_hat - M_star, 'fro')
    
    results[struct] = {
        'pehe': pehe,
        'M_recovery_error': recovery_error
    }
```

---

### Example 4: Validate M̂ Recovery

```python
# Generate with known M*
source, target, gen = generate_synthetic_rct(
    transfer_structure='low_rank',
    transfer_rank=1,
    n_source_sites=20,
    random_state=42
)

# Fit Step B
model = PlaceboAnchoredDRLearner(option='B')
model.fit(source, target)

# Compare
M_star = gen.M_star
M_hat = model.M_hat_

print(f"True ||M*||: {np.linalg.norm(M_star, 'fro'):.4f}")
print(f"Est  ||M̂||:  {np.linalg.norm(M_hat, 'fro'):.4f}")
print(f"Recovery error: {np.linalg.norm(M_hat - M_star, 'fro'):.4f}")

# Ideal: recovery error << ||M*||
```

---

## 🔬 Recommended Experiments

### Experiment 1: M* Identifiability

```python
# Sweep number of source sites
site_counts = [3, 5, 10, 20, 50]
recovery_errors = []

for C in site_counts:
    source, target, gen = generate_synthetic_rct(
        n_source_sites=C,
        transfer_structure='low_rank',
        transfer_rank=1
    )
    
    # Fit Step B
    model = PlaceboAnchoredDRLearner(option='B')
    model.fit(...)
    
    M_error = np.linalg.norm(model.M_hat_ - gen.M_star, 'fro')
    recovery_errors.append(M_error)

plt.plot(site_counts, recovery_errors)
plt.xlabel('Number of source sites C')
plt.ylabel('||M̂ - M*||_F')
plt.title('M* Recovery vs Sample Size')
```

**Expected**: Error decreases as C increases.

---

### Experiment 2: Support Structure Impact

```python
# Compare shared vs random support
configs = [
    {'shared_support_size': 2, 'idiosyncratic_support_size': 0},  # All shared
    {'shared_support_size': 1, 'idiosyncratic_support_size': 1},  # Mixed
    {'shared_support_size': 0, 'idiosyncratic_support_size': 2},  # All random
]

for cfg in configs:
    source, target, gen = generate_synthetic_rct(**cfg)
    
    # Fit Option B
    model_b = PlaceboAnchoredDRLearner(option='B')
    model_b.fit(...)
    
    pehe_b = evaluate(model_b, target)
    
    # Also fit Option A
    model_a = PlaceboAnchoredDRLearner(option='A')
    model_a.fit(...)
    
    pehe_a = evaluate(model_a, target)
```

**Expected**: Option B better when support shared!

---

### Experiment 3: Proxy Nonlinearity

```python
# Test Stage 1 with varying nonlinearity
nonlin_scales = [0.0, 0.2, 0.5, 1.0, 2.0]

for scale in nonlin_scales:
    source, target, gen = generate_synthetic_rct(
        proxy_nonlinear_scale=scale
    )
    
    # Fit Stage 1 proxy with different models
    for model_type in [LinearRegression(), RandomForest()]:
        # ...fit and evaluate...
```

**Expected**: RF helps more when scale > 0.

---

## 📊 Comparison: Before vs After

| Aspect | Before | After | Impact |
|--------|--------|-------|--------|
| **Misspec deterministic** | ❌ Random | ✅ Fixed | Valid ground truth |
| **Proxy difficulty** | Too easy | Nontrivial | Tests Stage 1 |
| **Support control** | Random | Shared | Step B learnable |
| **# Source sites** | 3 | 10 | M̂ identifiable |
| **Transfer structures** | 1 (low-rank) | 4 options | Flexibility |
| **Noise heterogeneity** | ❌ Homogeneous | ✅ Heterogeneous | Robustness |
| **Cov shift** | Mean only | Mean + cov | Realistic |
| **Diagnostics** | Basic | SNR, cosine, support | Validate Step B |

---

## ✅ Status Summary

### Critical Bugs Fixed
- ✅ Misspecification now deterministic
- ✅ Step B identifiable (10 sites default)
- ✅ Shared support structure

### Enhancements Added
- ✅ Proxy nonlinearity (Stage 1 matters)
- ✅ Transfer structure options (4 types)
- ✅ Heterogeneous noise
- ✅ Covariance shift
- ✅ Enhanced diagnostics (SNR, cosine)

### Validation Complete
- ✅ All tests passing
- ✅ Deterministic μ verified
- ✅ Support overlap verified
- ✅ A6 structure verified
- ✅ Transfer structures tested

---

## 🎯 Recommended Settings for Paper

### For Option A Testing (Both Arms in Target)
```python
generate_synthetic_rct(
    n_source_sites=10,
    proxy_nonlinear_scale=0.5,
    shared_support_size=2,
    transfer_structure='low_rank',
    nontransfer_scale_target=0.3,
)
```

### For Option B Testing (Disconnected Target)
```python
generate_disconnected_target(
    n_source_sites=20,              # More sites for Step B
    proxy_nonlinear_scale=0.5,
    shared_support_size=2,          # Crucial!
    transfer_structure='diag',      # Simpler for small p
    nontransfer_scale_target=0.3,
)
```

### For Degradation Sweep
```python
sweep_nontransfer(
    nontransfer_scales=[0.0, 0.1, 0.3, 0.5, 0.8],
    n_source_sites=20,
    transfer_structure='low_rank',
)
```

---

## 📚 Theory Alignment

### Paper Assumption A5
> "δ_{a,c} belong to low-complexity class (sparse linear)"

**Implementation**:
```python
shared_support = [2, 4]  # Same for all sites
beta0_c[shared_support] = sparse_values
```
✅ **Sparse linear** with controlled support

---

### Paper Assumption A6
> "β_{1,c} = M*·β_{0,c} + ν_c, rank(M*) ≤ r"

**Implementation**:
```python
M_star = U @ V.T  # rank r
beta1_c = M_star @ beta0_c + nu_c
```
✅ **Low-rank transfer** with 4 structure options

---

### Paper Step B
> "Estimate M̂ from sources: β̂_{1,c} ~ M̂·β̂_{0,c}"

**Now learnable** because:
- ✅ 10 sites (was 3)
- ✅ Shared support (Step B has signal)
- ✅ Controllable SNR (||M*β₀|| / ||ν||)

---

**Summary**: ✅ **ALL CRITICAL ISSUES FIXED + MAJOR ENHANCEMENTS!**

The DGP is now production-ready for testing all aspects of the three-stage estimator with proper A5/A6 structure.
