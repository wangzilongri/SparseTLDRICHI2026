# Quick Reference: When Does the Method Work?

---

## ✅ SUCCESS: Option A, High ρ, Large n

**Scenario**: Both arms in target, shared bias regime  
**Sample size**: n ≥ 2000  
**Correlation**: ρ ≥ 0.8

**Results**:
```
ρ=1.0: Proposed +60% vs Proxy (0.264 vs 0.667) ✓✓✓
ρ=0.8: Proposed  +6% vs Proxy (0.713 vs 0.759) ✓
```

**Why**: δ₁ ≈ δ₀ → high covariance → variance cancellation → DR helps

---

## ⚠️ LIMITATION: Low ρ

**Scenario**: Weakly correlated biases  
**Correlation**: ρ < 0.5

**Results**:
```
ρ=0.5: Proxy wins (0.895 vs Proposed 1.104)
ρ=0.3: Proxy wins (0.995 vs Proposed 1.381)
```

**Why**: δ₁ ⊥ δ₀ → variance explosion → Proxy safer

**Recommendation**: **Use Proxy-Only**

---

## ⚠️ LIMITATION: Option B (Shared Bias)

**Scenario**: Force δ₁ = δ₀ assumption

**Result**:
```
Plug-in CATE = Proxy CATE (corrections cancel!)
```

**Why**: τ̂ = [μ̂₁ + δᵀx] - [μ̂₀ + δᵀx] = μ̂₁ - μ̂₀

**Recommendation**: **Use Anchor-Only** (improves μ calibration, not CATE)

---

## ⚠️ LIMITATION: Disconnected Target

**Scenario**: Placebo-only target (no treated arm)

**Result**:
```
All methods ≈ equal (no DR signal)
Stage 3 can add noise
```

**Why**: No treated data → no orthogonal signal → DR doesn't help

**Recommendation**: **Use Anchor-Only (Stages 1+2)** or **Proxy-Only**

---

## Model Choice

**RF Models**: Proposed wins clearly (+60% at ρ=1.0)  
**Linear Models**: All methods excellent when DGP linear  

**Recommendation**: Use RF for main results (robust), Linear for sensitivity

---

## Quick Decision Tree

```
Do you have both arms in target?
│
├─ YES: Option A
│   │
│   ├─ Is ρ ≥ 0.8 and n ≥ 2000?
│   │   │
│   │   ├─ YES: ✅ USE PROPOSED (+6-60% improvement!)
│   │   └─ NO:  ⚠️  Use Proxy-Only (lower variance)
│   │
│   └─ END
│
└─ NO: Disconnected
    │
    └─ ⚠️ Use Anchor-Only or Proxy-Only
       (Stage 3 has no signal)
```

---

## Key Numbers (Memorize These!)

**Success**:
- ρ=1.0, n=2000: **+60.4%** improvement ✓✓✓
- ρ=0.8, n=2000: **+6.1%** improvement ✓

**Mechanism**:
- Variance cancellation: **9x** at ρ=1.0
- Variance explosion: **2-3x** at ρ=0.3

**Diagnostics**:
- True |δ₁-δ₀| → 0 as ρ → 1 ✓
- Cov(δ̂₁, δ̂₀) drives variance ✓
- Shared correction fixes catastrophe (+29%) ✓

---

## Paper Claims (Be Precise!)

✅ **DO say**:
- "6-60% improvement in Option A at ρ≥0.8, n≥2000"
- "Variance mechanism confirmed by diagnostics"
- "DR stabilization provides 15-35% benefit over direct anchoring"

❌ **DON'T say**:
- "Always better than proxy methods"
- "Works in all disconnected settings"
- "Option B improves CATE predictions"

---

## Files to Read

**For comprehensive understanding**:
1. `FINAL_SUMMARY_FOR_ADVISOR.md`
2. `ADVISOR_FIXES_SUMMARY.md`
3. `FINAL_STATUS.md`

**For specific topics**:
- Diagnostics: `ADVISOR_RESPONSE.md`
- RF vs Linear: `COMPLETE_RESULTS_COMPARISON.md`
- Fixes: `ADVISOR_FIXES_SUMMARY.md`

---

## Implementation

**Fixed version**: `src/scratch_estimator_fixed.py`

**Key features**:
```python
# Detects disconnected target
model._is_disconnected_target_  # True/False

# Two predictions
tau_plugin = model.predict_tau_plugin(X)   # Stage 1+2 only
tau_dr = model.predict(X)                  # Full DR (Stage 3)

# Diagnostics
corrections = model.get_correction_vectors()
print(corrections['disconnected_target'])
print(corrections['sparsity_placebo'])
```

---

**Status**: ✅ COMPLETE AND READY FOR PUBLICATION ✅
