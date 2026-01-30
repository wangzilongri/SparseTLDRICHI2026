# Linear Models Dramatically Outperform Random Forests

**Date**: January 29, 2026  
**Key Finding**: DGP is approximately linear/additive → Linear models 73-87% better than RF

---

## Executive Summary

When switching from Random Forest to linear models (Ridge + Elastic Net):
- ✅ **Proxy-Only improves 73%** (0.217 vs 0.808 at ρ=1.0)
- ✅ **Anchor-Only improves 87%** (0.077 vs 0.609 at ρ=1.0)
- ⚠️ **But Proposed doesn't win** (0.238 vs Anchor 0.069)

**Conclusion**: The DGP is linear/additive, making parametric models superior. However, Stage 3 (DR) is still adding noise even with hyperparameter optimization.

---

## Why Linear Models Excel

### DGP Structure is Additive

**Outcome model**:
```
Y = β_global · X + γ_a · X_effect_mod + δ_a^(site) · X + ε
    └───┬───┘   └──────┬────────┘   └──────┬──────┘
    Linear      Linear (subset)      Linear (sparse)
```

**All components are linear/additive!**
- No interactions
- No non-linear transformations
- No threshold effects

**Implication**: Linear models (Ridge, LASSO) should be **optimal** for this DGP, while Random Forests are overfitting to noise.

---

## Benchmark Results: Linear vs RF

### At ρ=1.0 (Shared Bias, n=2000, seed=42)

| Method | Model Type | PEHE | Winner |
|--------|-----------|------|--------|
| **Proxy-Only** | Ridge (CV) | **0.217** | - |
| Proxy-Only | RF (fixed) | 0.808 | - |
| **Improvement** | - | **+73%** ✓✓ | Linear wins |
|  |  |  |  |
| **Anchor-Only** | Ridge + Elastic Net | **0.077** ✓✓✓ | **BEST** |
| Anchor-Only | RF + LASSO | 0.609 | - |
| **Improvement** | - | **+87%** ✓✓✓ | Linear wins |
|  |  |  |  |
| **Proposed (Full)** | Ridge + EN + RF(tuned) | 0.238 | - |
| Proposed (Full) | RF (fixed) | 0.789 | - |
| **Improvement** | - | **+70%** ✓✓ | Linear better |

---

## Monte Carlo Results (30 runs, n=2000)

### Performance by ρ (Improved Linear Estimators)

| ρ | Proxy | Anchor | Proposed | Winner |
|---|-------|--------|----------|--------|
| 0.3 | **0.995** | 1.591 | 1.496 | **Proxy** |
| 0.5 | **0.828** | 1.260 | 1.178 | **Proxy** |
| 0.8 | **0.537** | 0.766 | 0.740 | **Proxy** |
| 1.0 | 0.228 | **0.069** ✓✓✓ | 0.238 | **Anchor** |

**PROPOSED WINS: 0/4 scenarios**

---

## Critical Issue: Proposed Underperforms Even With Linear Models

### At ρ=1.0 (where it should excel):

**Anchor-Only**: 0.069 PEHE (excellent!)  
**Proposed (Full)**: 0.238 PEHE (worse!)

**Gap**: Proposed is **3.4x worse** than Anchor despite having Stage 3 (DR)!

### Why might this be happening?

**Hypothesis 1: Stage 3 adds noise**
- Even with hyperparameter tuning, fitting RF on pseudo-outcomes might be overfitting
- Pseudo-outcomes have inherent noise from Stage 2 corrections
- At ρ=1.0, Anchor corrections are already very accurate (δ₁ ≈ δ₀)
- DR step trying to "improve" something that's already good → adds variance

**Hypothesis 2: Hyperparameter tuning is overfitting**
- GridSearchCV on pseudo-outcomes (which have noise) might select overfit hyperparameters
- Test set performance suffers even though CV score looks good

**Hypothesis 3: Linear CATE model needed**
- Stage 3 currently uses RF even when Stages 1 & 2 are linear
- Should try Ridge for Stage 3 as well

---

## Test: What if Stage 3 uses Ridge instead of RF?

Let me rerun with Stage 3 = Ridge:

```python
proposed_ridge = ImprovedPlaceboAnchoredDRLearner(
    stage1_model='ridge',
    stage1_alpha='cv',
    stage2_model='elasticnet',
    stage3_model='ridge',  # ← Linear for Stage 3 too!
    stage3_tune=True,
    option='A'
)
```

**Expected**: Should be closer to Anchor performance, maybe even better!

---

## Implications

### 1. Random Forest was hiding the true pattern

With RF (original benchmarks):
- ρ=1.0: Proposed wins +60% (0.264 vs 0.667 Proxy)
- RF was overfitting, making all methods look worse
- Proposed won because DR stabilization helped most with noisy RF fits

With Linear (improved):
- ρ=1.0: Anchor dominates (0.069)
- Proxy very good (0.228)
- Proposed worse (0.238)
- Linear models are so accurate that Stage 3 adds noise rather than signal

### 2. The DGP design favors linear models

**Current DGP**:
```python
μ_a(X) = X @ β_global + X_effect_mod @ γ_a + X @ δ_a + ε
```

This is **perfectly linear**. Ridge/LASSO are optimal estimators!

**For more realistic comparison**, we might need:
- Non-linear DGP (interactions, thresholds)
- Or stick with linear models (more interpretable, faster, better for this DGP)

### 3. Need to diagnose Stage 3

Why is Proposed (with tuned Stage 3) worse than Anchor at ρ=1.0?

Possibilities:
- RF on pseudo-outcomes still overfits
- Hyperparameter tuning on noisy pseudo-outcomes is unstable
- Should use simpler Stage 3 (Ridge, not RF)

---

## Recommendations

### Near-term:

1. ✅ **Test Stage 3 = Ridge** (all linear pipeline)
2. ✅ **Compare linear vs RF results** side-by-side
3. ✅ **Document the architectural choice** (why RF vs linear?)

### For Paper:

**Option A: Use Linear Models** (better aligned with DGP)
- Pro: Dramatically better performance (70-87% improvement)
- Pro: More interpretable
- Pro: Faster
- Con: Less general (assumes additive structure)

**Option B: Use Non-linear DGP** (justify RF)
- Add interaction terms: β_interact · (X_i × X_j)
- Add non-linear features: β_nl · f(X)
- This would justify RF and make methods more comparable

**Option C: Report Both**
- Show linear results (optimal for this DGP)
- Show RF results (robust to model misspecification)
- Discuss trade-offs

---

## Action Items

1. **Test all-linear pipeline** (Stage 3 = Ridge)
2. **Compare linear vs RF systematically** across all ρ
3. **Investigate why Proposed-Linear underperforms** at ρ=1.0
4. **Decide on modeling approach** for paper (linear vs RF vs both)

---

## Current Status

**Implemented**:
- ✅ `src/improved_estimator.py` - Linear Stages 1 & 2, flexible Stage 3
- ✅ `src/improved_baselines.py` - Linear versions of all baselines
- ✅ Hyperparameter optimization for Stages 2 & 3
- ✅ Test script showing linear >> RF

**Next**:
- Test Stage 3 = Ridge (full linear pipeline)
- Diagnose why DR adds noise with linear models
- Create comparison figure (linear vs RF)
