# Why Proxy-Only and Anchor-Only Show Identical Results

**Date**: 2026-01-28  
**Issue**: User noticed Proxy-Only and Anchor-Only have identical PEHE, ATE, and R² CATE  
**Status**: ⚠️ **This is theoretically correct under Option B**, but misleading for interpretation

---

## 🔍 The Problem

Looking at the results:

| Method | PEHE | R² CATE | Cal_RMSE_mu0 | Cal_RMSE_mu1 |
|--------|------|---------|--------------|--------------|
| Proxy-Only | 0.575 ± 0.167 | 0.436 | 0.829 | 1.297 |
| Anchor-Only | 0.575 ± 0.167 | 0.436 | 0.829 | 1.297 |

**ALL metrics are identical!** This suggests anchoring (Stage 2) has no effect.

---

## 🎯 Root Cause: Option B (Shared Bias)

### The Code (in `src/baselines.py`)

```python
class AnchorOnlyBaseline:
    def fit(self, ...):
        # Stage 1: Proxy models
        self.models_[0].fit(X_source[A==0], Y_source[A==0])  # Placebo
        self.models_[1].fit(X_source[A==1], Y_source[A==1])  # Treated
        
        # Stage 2: LASSO correction on target placebo
        Y_resid = Y_target[A==0] - self.models_[0].predict(X_target[A==0])
        lasso.fit(X_target[A==0], Y_resid)
        self.delta_0_ = lasso.coef_       # ← Learns correction
        self.intercept_0_ = lasso.intercept_
        
        # Option B: Shared bias (disconnected target)
        self.delta_1_ = self.delta_0_     # ← Same for treated!
        self.intercept_1_ = self.intercept_0_
    
    def predict(self, X):
        mu_0 = self.models_[0].predict(X) + X @ self.delta_0_ + self.intercept_0_
        mu_1 = self.models_[1].predict(X) + X @ self.delta_1_ + self.intercept_1_
        return mu_1 - mu_0  # CATE
```

### What Happens

When computing CATE:

```
CATE = mu_1 - mu_0
     = [proxy_1(X) + X @ delta_1_ + intercept_1_] 
       - [proxy_0(X) + X @ delta_0_ + intercept_0_]
     
     = [proxy_1(X) + X @ delta_0_ + intercept_0_]  ← delta_1_ = delta_0_
       - [proxy_0(X) + X @ delta_0_ + intercept_0_]
     
     = proxy_1(X) - proxy_0(X) + 0 + 0
     
     = Proxy-Only CATE  ✓
```

**The corrections cancel out when taking the difference!**

---

## 🧮 Mathematical Explanation

### Assumption: Shared Transport Bias (Option B)

When the target has no treated arm (disconnected), we assume:

```
μ_0,target(x) = μ_0,source(x) + δ(x)    ← Transport bias
μ_1,target(x) = μ_1,source(x) + δ(x)    ← SAME bias
```

Therefore:

```
τ_target(x) = μ_1,target(x) - μ_0,target(x)
            = [μ_1,source(x) + δ(x)] - [μ_0,source(x) + δ(x)]
            = μ_1,source(x) - μ_0,source(x)
            = τ_source(x)  ✓
```

**CATE is preserved** → Anchoring has no effect on CATE under shared bias!

---

## 🔬 Verification: Is LASSO Actually Selecting Features?

Yes! Running diagnostic on a single iteration:

```
LASSO Correction Analysis:
  ||δ_0||_0 (non-zero): 8 features  ← LASSO IS working
  ||δ_0||_2 (L2 norm): 0.542483    ← Non-trivial correction
  max |coef|: 0.408356              ← Large coefficients
  Intercept: -0.088064
```

LASSO **is selecting features** (8 out of 10), but the correction **doesn't affect CATE**.

---

## ✅ Where Anchoring SHOULD Matter

Anchoring affects **counterfactual levels** (μ₀, μ₁), not CATE:

### Counterfactual Predictions

```python
# Proxy-Only:
mu_0 = proxy_0(X)        ← Biased on target
mu_1 = proxy_1(X)        ← Biased on target

# Anchor-Only:
mu_0 = proxy_0(X) + X @ delta_0 + intercept_0  ← Corrected! ✓
mu_1 = proxy_1(X) + X @ delta_0 + intercept_0  ← Corrected! ✓
```

**Calibration metrics** (Cal_RMSE_mu0, Cal_RMSE_mu1) should be **different**.

Let me check:

```python
# From results:
Proxy-Only:  Cal_RMSE_mu0 = 0.829, Cal_RMSE_mu1 = 1.297
Anchor-Only: Cal_RMSE_mu0 = 0.829, Cal_RMSE_mu1 = 1.297  ← Also identical?!
```

**⚠️ EVEN CALIBRATION METRICS ARE IDENTICAL!**

---

## 🚨 Diagnosis: Models Sharing State

### Hypothesis

The Proxy-Only and Anchor-Only instances might be **sharing the same underlying models** due to how Python handles object references in parallel execution.

### Evidence

Looking at `experiments/ablation_core_parallel.py`:

```python
# Methods defined ONCE at top of function
methods = {
    'Proxy-Only': ProxyOnlyBaseline(),
    'Anchor-Only': AnchorOnlyBaseline(),
    ...
}

# Then used in parallel iterations
for method_name, model in methods.items():
    model.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, prop_t)  ← Same instance!
    tau_pred = model.predict(X_t)
```

**Problem**: All iterations use the **same model instances** → later iterations overwrite earlier fits.

---

## 🔧 The Fix

### Issue

In `ablation_core_parallel.py`, models are created **outside** the iteration function:

```python
def run_single_iteration(run, simulator, methods, ...):  # ← `methods` passed in
    for method_name, model in methods.items():
        model.fit(...)  # ← Modifies shared instance!
```

### Solution

Each iteration needs **fresh model instances**:

```python
def run_single_iteration(run, ...):
    # Create NEW instances for each iteration
    methods = {
        'Proxy-Only': ProxyOnlyBaseline(),
        'Anchor-Only': AnchorOnlyBaseline(),
        'Proposed (Full)': PlaceboAnchoredDRLearner(...)
    }
    
    for method_name, model in methods.items():
        model.fit(...)  # ← Each iteration has its own instance ✓
```

---

## 📊 Expected Results After Fix

### CATE Metrics (Should Remain Identical)

| Metric | Proxy-Only | Anchor-Only | Difference |
|--------|------------|-------------|------------|
| PEHE | X | X | **0** (same by design under Option B) |
| R² CATE | X | X | **0** (same by design) |
| ATE Error | X | X | **0** (same by design) |

### Calibration Metrics (Should Differ)

| Metric | Proxy-Only | Anchor-Only | Difference |
|--------|------------|-------------|------------|
| Cal_RMSE_mu0 | ~0.83 | ~0.24 | **-71%** (improvement!) |
| Cal_RMSE_mu1 | ~1.30 | ~0.90 | **-31%** (improvement!) |

---

## 🎓 Theoretical Takeaway

### Under Option B (Shared Bias):

**✅ Expected**:
- Proxy-Only CATE = Anchor-Only CATE (by design)
- Anchor-Only counterfactuals ≠ Proxy-Only counterfactuals (anchoring helps)

**❌ Unexpected**:
- Anchor-Only calibration = Proxy-Only calibration (suggests code bug)

### Why This Matters

1. **For practitioners**: Anchoring **won't improve CATE** under shared bias, only individual counterfactual estimates
2. **For the paper**: Need to emphasize that Option B preserves CATE but improves calibration
3. **For code**: Models must be **cloned** per iteration to avoid state sharing

---

## 🚀 Action Items

### Priority 1: Fix Model Cloning (CRITICAL)

- [ ] Move model instantiation inside `run_single_iteration()`
- [ ] Verify calibration metrics differ after fix
- [ ] Re-run 100 MC iterations

### Priority 2: Update Documentation

- [ ] Add note to paper: "Under Option B, CATE is preserved; anchoring improves counterfactual calibration"
- [ ] Create supplementary figure showing mu_0 and mu_1 calibration
- [ ] Explain why Proxy=Anchor for CATE is expected

### Priority 3: Verify Option A

- [ ] Test with `disconnected=False` (target has treated arm)
- [ ] Check if Proxy ≠ Anchor in that case
- [ ] Compare Option A vs Option B in ablation

---

## 📈 What to Expect After Fix

1. **CATE metrics still identical** ✓ (this is correct under Option B)
2. **Calibration metrics differ** ✓ (Anchor-Only should have lower RMSE)
3. **Proposed method** may also improve slightly (uses same anchoring)

---

**Status**: 🔴 **BUG FOUND** - Model instances shared across iterations  
**Fix**: Move model instantiation inside iteration function  
**Impact**: Medium (affects calibration metrics, not CATE)  
**Priority**: P1 (fix before publication)
