# Option A vs Option B: Understanding Transport Bias Correction

**Date**: 2026-01-28  
**Purpose**: Explain the key differences between Option A and Option B in the Placebo-Anchored DR-Learner

---

## 🎯 Quick Summary

| Feature | Option A (Connected) | Option B (Disconnected) |
|---------|---------------------|------------------------|
| **Target has treated arm?** | ✅ Yes | ❌ No |
| **Can estimate δ₁?** | ✅ Yes (from treated data) | ❌ No (must assume) |
| **Bias assumption** | δ₀ ≠ δ₁ (separate) | δ₁ = δ₀ (shared) |
| **Anchoring affects CATE?** | ✅ Yes (improves PEHE) | ❌ No (preserves CATE) |
| **Anchoring affects calibration?** | ✅ Yes | ✅ Yes |
| **Use case** | RCTs with partial data | Observational studies |

---

## 📖 Theoretical Background

### The Transport Bias Problem

When transferring models from source to target populations, systematic differences cause **transport bias**:

```
μ₀,target(x) = μ₀,source(x) + δ₀(x)    ← Placebo arm bias
μ₁,target(x) = μ₁,source(x) + δ₁(x)    ← Treated arm bias
```

**Key question**: Are δ₀ and δ₁ the same or different?

---

## 🔵 Option A: Connected Target (Separate Bias)

### Setup

The target population has data from **both arms** (placebo + treated):
- Can anchor placebo arm using gold-standard placebo data
- Can anchor treated arm using gold-standard treated data
- Estimate **separate** corrections: δ₀(x) and δ₁(x)

### Stage 2: Anchoring

```python
# Placebo correction (using target placebo data)
Y_resid_0 = Y_target[A==0] - proxy_0.predict(X_target[A==0])
lasso_0.fit(X_target[A==0], Y_resid_0)
δ₀ = lasso_0.coef_

# Treated correction (using target treated data)
Y_resid_1 = Y_target[A==1] - proxy_1.predict(X_target[A==1])
lasso_1.fit(X_target[A==1], Y_resid_1)
δ₁ = lasso_1.coef_  # ← Different from δ₀!
```

### Corrected Predictions

```
μ₀,corrected(x) = proxy_0(x) + X @ δ₀
μ₁,corrected(x) = proxy_1(x) + X @ δ₁  ← Uses different δ₁
τ(x) = μ₁,corrected(x) - μ₀,corrected(x)
     = [proxy_1(x) - proxy_0(x)] + X @ (δ₁ - δ₀)
```

**Key**: The term `X @ (δ₁ - δ₀)` is **non-zero**, so CATE changes!

### When Does This Help?

✅ **CATE estimation**: Anchoring improves PEHE because δ₁ ≠ δ₀  
✅ **Calibration**: Both μ₀ and μ₁ are better calibrated  
✅ **Heterogeneity**: Can detect differential transport bias across subgroups

### Expected Results

| Metric | Proxy-Only | Anchor-Only | Difference |
|--------|------------|-------------|------------|
| PEHE | 0.65 | 0.48 | **-26%** ⭐ |
| R² CATE | 0.40 | 0.58 | **+45%** ⭐ |
| Cal_RMSE_mu0 | 0.87 | 0.26 | **-70%** ⭐ |
| Cal_RMSE_mu1 | 1.30 | 0.35 | **-73%** ⭐ |

**Anchoring helps for BOTH CATE and calibration!**

---

## 🔴 Option B: Disconnected Target (Shared Bias)

### Setup

The target population has data from **only placebo arm**:
- Can anchor placebo arm using gold-standard placebo data
- **Cannot** anchor treated arm (no treated data)
- Must **assume** shared bias: δ₁ = δ₀

### Stage 2: Anchoring

```python
# Placebo correction (using target placebo data)
Y_resid_0 = Y_target[A==0] - proxy_0.predict(X_target[A==0])
lasso.fit(X_target[A==0], Y_resid_0)
δ₀ = lasso.coef_

# Assume shared bias (no treated data to estimate δ₁)
δ₁ = δ₀  # ← SAME as δ₀!
```

### Corrected Predictions

```
μ₀,corrected(x) = proxy_0(x) + X @ δ₀
μ₁,corrected(x) = proxy_1(x) + X @ δ₀  ← Uses SAME δ₀
τ(x) = μ₁,corrected(x) - μ₀,corrected(x)
     = [proxy_1(x) - proxy_0(x)] + X @ (δ₀ - δ₀)
     = proxy_1(x) - proxy_0(x)  ← SAME as Proxy-Only!
```

**Key**: The corrections **cancel out** when taking the difference!

### When Does This Help?

❌ **CATE estimation**: Anchoring does NOT improve PEHE (corrections cancel)  
✅ **Calibration**: Both μ₀ and μ₁ are still better calibrated  
✅ **Counterfactual predictions**: Individual potential outcomes are improved

### Expected Results

| Metric | Proxy-Only | Anchor-Only | Difference |
|--------|------------|-------------|------------|
| PEHE | 0.58 | 0.58 | **±0%** (identical) |
| R² CATE | 0.43 | 0.44 | **±0%** (identical) |
| Cal_RMSE_mu0 | 0.87 | 0.26 | **-70%** ⭐ |
| Cal_RMSE_mu1 | 1.30 | 0.91 | **-30%** ⭐ |

**Anchoring helps for calibration, but NOT CATE!**

---

## 🧮 Mathematical Proof

### Why CATE is Preserved Under Option B

**Assumption**: Transport bias affects both arms equally  
```
δ₀(x) = δ₁(x) = δ(x)
```

**True CATE**:
```
τ_target(x) = μ₁,target(x) - μ₀,target(x)
            = [μ₁,source(x) + δ(x)] - [μ₀,source(x) + δ(x)]
            = μ₁,source(x) - μ₀,source(x)
            = τ_source(x)
```

**Therefore**: CATE is **preserved** across populations under shared bias!

This is why:
- Proxy-Only already gets CATE right (no correction needed)
- Anchor-Only doesn't improve CATE (corrections cancel)
- But both get **levels** wrong (need anchoring for calibration)

---

## 🔬 When to Use Each Option

### Use Option A When:

1. ✅ You have an **RCT** with both arms in the target population
2. ✅ You have **sufficient treated arm data** (n ≥ 50 per arm)
3. ✅ Transport bias may **differ across arms** (e.g., drug side effects)
4. ✅ You need accurate **counterfactual predictions** (policy decisions)
5. ✅ You want to **test** if δ₁ = δ₀ (can compare Option A vs B)

**Examples**:
- Multi-site RCT with partial data
- Clinical trial with varying demographics
- A/B test with regional differences

---

### Use Option B When:

1. ✅ You have **only observational data** in the target (no treated arm)
2. ✅ You have **gold-standard placebo** (e.g., historical controls)
3. ✅ Transport bias is likely **shared** (demographic shifts, time trends)
4. ✅ Your goal is **calibrating counterfactuals**, not estimating CATE
5. ✅ You have **limited target data** (insufficient for two LASSO models)

**Examples**:
- Observational study with historical RCT data
- Pre-market approval with post-market surveillance (no control)
- Synthetic controls for policy evaluation

---

## 🎓 Practical Implications

### For Practitioners

1. **Option A is more powerful** but requires more data and assumptions
2. **Option B is more robust** when treated arm is unavailable
3. **Start with Option B** if you're unsure (more conservative)
4. **Test the assumption**: Run both and compare (δ₁ = δ₀?)

### For the Paper

1. **Report both options** to show robustness
2. **Emphasize Option B** for observational settings (more realistic)
3. **Use Option A** to demonstrate full potential when data is available
4. **Compare** to show when anchoring helps CATE vs calibration only

---

## 📊 Experimental Setup

### Simulation Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Features (d) | 10 | Baseline covariates |
| Effect modifiers (s) | 3 | Interact with treatment |
| Source sites | 3 | Multi-site RCT |
| Target sample (n) | 200 | Split 50/50 for Option A, 100% placebo for Option B |
| Monte Carlo runs | 100 | Publication quality |

### Data Generation

**Option A (connected=True)**:
```python
data = simulator.generate_network(
    n_source_sites=3,
    n_target=200,
    disconnected=False  # ← Has both arms (100 placebo, 100 treated)
)
```

**Option B (disconnected=True)**:
```python
data = simulator.generate_network(
    n_source_sites=3,
    n_target=200,
    disconnected=True  # ← Only placebo (200 placebo, 0 treated)
)
```

---

## 🚀 Running the Experiments

### Quick Start

```bash
# Run both options (100 iterations each)
python experiments/ablation_both_options.py

# Results saved to:
# - results/ablation_options/option_a_results.csv
# - results/ablation_options/option_b_results.csv
# - results/ablation_options/option_comparison.png
```

### Output Structure

```
results/ablation_options/
├── option_a_results.csv           # Raw results for Option A
├── option_b_results.csv           # Raw results for Option B
├── ablation_both_options.csv      # Combined results
├── option_a_summary.csv           # Statistical summary (A)
├── option_b_summary.csv           # Statistical summary (B)
├── option_summary_table.csv       # Side-by-side comparison
├── option_comparison.png          # 2x3 grid (all metrics)
├── pehe_comparison.png            # PEHE: A vs B
├── ate_error_comparison.png       # ATE: A vs B
└── r2_cate_comparison.png         # R²: A vs B
```

---

## 📝 Interpreting Results

### Key Comparisons

1. **Within each option**: Compare Proxy vs Anchor vs Proposed
2. **Across options**: Compare Option A vs B for same method
3. **Proxy vs Anchor**: Should differ in A, identical in B

### Expected Findings

| Comparison | Expected Result | Interpretation |
|------------|-----------------|----------------|
| Anchor-Only vs Proxy-Only (Option A) | Anchor >> Proxy | Anchoring helps CATE |
| Anchor-Only vs Proxy-Only (Option B) | Anchor ≈ Proxy | Corrections cancel |
| Proposed vs Anchor-Only (Option A) | Proposed > Anchor | DR further improves |
| Proposed vs Anchor-Only (Option B) | Proposed > Anchor | DR improves despite cancellation |

---

## 🎯 Key Takeaways

1. **Option A**: Full power when you have treated arm data
2. **Option B**: Conservative approach when treated arm is unavailable
3. **Shared bias assumption**: Critical for interpreting Option B results
4. **Calibration always improves**: Even when CATE is preserved
5. **DR (Stage 3) always helps**: Orthogonalization reduces variance

---

**See Also**:
- `docs/DESIGN.md` - Full technical specification
- `experiments/ablation_both_options.py` - Implementation
- `docs/diagnostics/PROXY_ANCHOR_IDENTICAL.md` - Why they're identical in Option B

**Last Updated**: 2026-01-28
