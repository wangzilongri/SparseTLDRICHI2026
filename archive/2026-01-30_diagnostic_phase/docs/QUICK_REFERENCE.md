# Quick Reference: Placebo-Anchored DR-Learner

## One-Sentence Summary

Transport treatment effects across heterogeneous RCTs by treating source-trial outcomes as abundant "proxy" labels and target-placebo outcomes as scarce "gold" calibration labels, using sparse correction + doubly robust estimation.

---

## Three-Stage Algorithm

```
Stage 1: PROXY FIT
├─ Input: (X_source, A_source, Y_source) - abundant but biased
├─ Fit: μ̂^proxy_0(x), μ̂^proxy_1(x) using flexible ML
└─ Output: Low-variance but miscalibrated outcome models

Stage 2: GOLD ANCHORING
├─ Input: (X_target[A=0], Y_target[A=0]) - scarce but unbiased
├─ Residualize: Ỹ = Y - μ̂^proxy_0(X)
├─ Fit: δ̂ = argmin { ||Ỹ - δ'X||² + λ||δ||₁ } via LASSO
└─ Output: μ̂^anch(x) = μ̂^proxy(x) + δ̂'x (calibrated)

Stage 3: DR CORRECTION
├─ Input: Anchored models + known propensities e(x)
├─ Pseudo-outcome: ψ = τ̂(x) + [(A-e)/(e(1-e))] * [Y - μ̂^anch_A(x)]
└─ Output: τ̂_DR(x) from regression on ψ
```

---

## Data Schema

```python
# SOURCE TRIALS (abundant proxy labels)
X_source: (n_source, p)    # e.g., (1500, 10)
A_source: (n_source,)      # {0, 1}
Y_source: (n_source,)      # continuous

# TARGET TRIAL (scarce gold labels)
X_target: (n_target, p)    # e.g., (200, 10)
A_target: (n_target,)      # may be all 0s (disconnected)
Y_target: (n_target,)      # placebo outcomes = gold calibration
```

---

## Key Assumptions

| ID | Assumption | Status | Testable? |
|----|------------|--------|-----------|
| A1 | Consistency | Standard | No |
| A2 | Randomization within sites | Design feature (RCTs) | Yes |
| A3 | Positivity | Design feature | Yes |
| **A4** | **Bounded covariate shift** | **Regularity condition** | Yes (measure d_TV) |
| **A5** | **Sparse transport bias** | **Working assumption** | Yes (check sparsity) |
| **A6** | **Cross-arm coupling** | **Modeling choice** | Yes (estimate ρ) |

**Critical**: A4-A6 define the working model, not causal identification

---

## When to Use Each Option

### Option A (Preferred)
- **When**: Target has treated arm (n₁ ≥ 50)
- **Method**: Fit separate δ̂_{1,0} using target treated data
- **Advantage**: No bias transfer assumption needed

### Option B (Disconnected)
- **When**: Target has no treated arm (disconnected network)
- **Method**: δ̂_{1,0} = δ̂_{0,0} (shared bias)
- **Assumption**: ρ ≥ 0.7 (placebo-treated bias correlation)

---

## Metrics

### Patient-Level (Primary)
- **PEHE**: √E[(τ(x) - τ̂(x))²] — Individual treatment effect accuracy

### Population-Level
- **ATE Error**: |E[τ(x)] - E[τ̂(x)]| — Average treatment effect accuracy

### Calibration
- **Cal RMSE (μ₀)**: √E[(μ₀(x) - μ̂₀(x))²] — Baseline risk calibration
- **Cal RMSE (μ₁)**: √E[(μ₁(x) - μ̂₁(x))²] — Treated outcome calibration

### Heterogeneity
- **R² (CATE)**: Fraction of variance in τ(x) explained

---

## Expected Ablation Results

| Method | What's Tested | Expected PEHE Rank |
|--------|---------------|-------------------|
| No-Transfer | Need for transfer | 5th (worst) |
| Proxy-Only | Need for anchoring | 4th |
| Proxy+DR | Anchoring vs DR alone | 3rd |
| Anchor-Only | Need for DR | 2nd |
| **Proposed** | **Full method** | **1st (best)** |

---

## Robustness Checks

### Will Succeed When:
- ✓ Shift: d_TV(P_source, P_target) ≤ 1.0
- ✓ Sparsity: ||δ||₀ ≤ 5
- ✓ Coupling: ρ ≥ 0.7 (for Option B)
- ✓ Gold budget: m₀ ≥ 50

### Will Degrade When:
- ⚠ Severe covariate shift (d_TV > 2.0)
- ⚠ Dense transport bias (||δ||₀ > 10)
- ⚠ Low cross-arm coupling (ρ < 0.5)
- ⚠ Extreme propensity violations (e → 0 or 1)

### Will Fail When:
- ✗ No overlap: supp(P_target) ∩ supp(P_source) = ∅
- ✗ Tiny gold sample: m₀ < 20
- ✗ Complete treatment-specific bias: ρ = 0 in disconnected setting

---

## Implementation Checklist

### Must Have
- [x] Stage 1: Flexible proxy learners (RF/GBM)
- [x] Stage 2: LassoCV for sparse correction
- [x] Stage 3: Cross-fitting with StratifiedKFold
- [x] Option A/B logic for disconnected setting
- [x] Known propensity handling
- [ ] Input validation (dimensions, NaNs)
- [ ] Comprehensive evaluation metrics

### Should Have
- [ ] Multiple proxy learner options
- [ ] Intercept vs no-intercept in Stage 2
- [ ] Diagnostic outputs (sparsity, lambda paths)
- [ ] Bootstrap confidence intervals
- [ ] Feature importance plots

### Nice to Have
- [ ] Automatic Option A/B selection
- [ ] Overlap diagnostics
- [ ] Sensitivity to hyperparameters
- [ ] Real-data preprocessing pipeline

---

## File Structure

```
Sparse_TL_DR_ICHI2026/
├── README.md                  # Setup & usage
├── DESIGN.md                  # Full design doc with pseudocode (THIS FILE)
├── ABLATION_TESTS.md          # Comprehensive ablation specification
├── QUICK_REFERENCE.md         # This summary
├── requirements.txt           # Dependencies
├── setup.sh                   # Automated setup
├── src/
│   ├── scratch_estimator.py  # Current implementation (needs updates)
│   ├── estimator.py           # New: clean implementation
│   ├── data_generator.py     # Synthetic RCT simulator
│   ├── baselines.py          # Baseline methods
│   └── evaluation.py         # Metrics & visualization
└── experiments/
    ├── ablation_core.py       # Core component ablations
    ├── ablation_robustness.py # Robustness checks
    └── ablation_comparison.py # Baseline comparisons
```

---

## Common Issues & Solutions

### Issue: LASSO selects no features (δ̂ = 0)
- **Cause**: Gold sample too small or no systematic bias
- **Solution**: Check m₀ ≥ 50, verify shift exists

### Issue: High variance in pseudo-outcomes
- **Cause**: Extreme propensities or poor outcome models
- **Solution**: Clip e(x) ∈ [0.01, 0.99], improve Stage 1

### Issue: Proposed worse than Proxy-Only
- **Cause**: No systematic bias or overfitting in Stage 2
- **Solution**: Verify assumptions A4-A5, increase m₀

### Issue: NaN in pseudo-outcomes
- **Cause**: Division by zero when e(x) → 0 or 1
- **Solution**: Add checks in DR formula, ensure overlap

---

## Key Differences from Related Work

### vs. Standard IPD-NMA
- ✓ Works in disconnected networks
- ✓ Patient-level predictions
- ✓ Explicit covariate shift handling
- ✗ No network-wide inference

### vs. Bastani et al. (2021) Proxy-Gold
- ✓ Adds DR correction (Stage 3)
- ✓ Flexible non-linear proxy models
- ✓ Cross-fitting for orthogonality
- ✓ Handles disconnected setting (Option B)

### vs. TMLE Transport
- ✓ Sparse correction (not full reweighting)
- ✓ Known propensities (RCT setting)
- ✓ Explicit anchoring to target
- ∼ Similar doubly robust principle

---

## Citation

```bibtex
@inproceedings{wang2026transfer,
  title={Transfer Learning for Meta-analysis Under Covariate Shift},
  author={Wang, Zilong and [Co-authors]},
  booktitle={IEEE International Conference on Healthcare Informatics (ICHI)},
  year={2026}
}
```

---

## Next Steps

1. **Implement** clean version following DESIGN.md
2. **Run** core ablations (5 methods × 20 runs)
3. **Verify** that Proposed achieves best PEHE
4. **Test** robustness to shift, sparsity, ρ
5. **Compare** against baselines (IPD-NMA, TMLE, etc.)
6. **Visualize** results with box plots, calibration curves
7. **Document** findings and failure modes
