# Placebo-Anchored DR-Learner for Transfer Learning

**Status**: Fresh start after diagnostic phase  
**Date**: January 30, 2026

---

## Overview

Three-stage doubly robust learner for transferring treatment effect estimates from multiple source RCTs to a target population under covariate shift.

---

## Quick Start

### Installation

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Unix/Mac
# or: venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```python
from src.scratch_estimator_fixed import PlaceboAnchoredDRLearner

# Initialize
model = PlaceboAnchoredDRLearner(option='A', verbose=True)

# Fit (Option A: both arms in target)
model.fit(X_source, A_source, Y_source,
          X_target, A_target, Y_target)

# Predict
tau_hat = model.predict(X_target)  # Stage-3 DR estimate
tau_plugin = model.predict_tau_plugin(X_target)  # Plug-in estimate
```

---

## Key Findings (from Diagnostic Phase)

### ✅ Success Regime

**Option A (both arms in target), ρ ≥ 0.8, n ≥ 2000**:
- +60% improvement at ρ=1.0 (vs Proxy-Only)
- +6% improvement at ρ=0.8 (vs Proxy-Only)
- +15-35% improvement over Anchor-Only

### ⚠️ Limitations

- **Low correlation (ρ < 0.5)**: Use Proxy-Only (variance explosion)
- **Option B (shared bias)**: Corrections cancel in CATE predictions
- **Disconnected target**: No DR signal, use Anchor-Only

---

## Project Structure

```
├── src/                          # Source code
│   ├── scratch_estimator_fixed.py    # FIXED implementation (use this!)
│   ├── scratch_estimator.py          # Original implementation
│   ├── baselines.py                  # Baseline methods (RF)
│   ├── improved_*.py                 # Linear model variants
│   ├── data_generator.py             # Multi-site simulator
│   └── evaluation.py                 # Metrics
│
├── archive/                      # Previous diagnostic work
│   └── 2026-01-30_diagnostic_phase/
│       ├── README_ARCHIVE.md         # Complete diagnostic summary
│       ├── experiments/              # All diagnostic experiments
│       ├── docs/                     # Analysis documents
│       └── *.md                      # Findings and reports
│
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## Implementation Details

### Three-Stage Estimator

**Stage 1**: Fit proxy outcome models on source data
```python
μ̂₀^proxy(x), μ̂₁^proxy(x) ← RandomForest(X_source, Y_source | A)
```

**Stage 2**: Estimate sparse transport bias corrections using target placebo data
```python
δ̂₀ ← LassoCV(X_target[A=0], Y_target - μ̂₀^proxy)
δ̂₁ ← LassoCV(X_target[A=1], Y_target - μ̂₁^proxy)  # Option A only
```

**Stage 3**: Doubly robust CATE estimation with cross-fitting
```python
ψᵢ = τ̂(Xᵢ) + [(Aᵢ - e(Xᵢ)) / (e(Xᵢ)(1 - e(Xᵢ)))] * (Yᵢ - μ̂_{Aᵢ}^anch(Xᵢ))
τ̂_DR(x) ← RandomForest(X_target, ψ)
```

### Fixed Implementation Features

1. **Disconnected target detection**: Skips DR noise injection when A=0 only
2. **Adaptive CV**: Uses KFold for single-arm target (not StratifiedKFold)
3. **Plug-in tau**: Exposes `predict_tau_plugin()` for comparison
4. **Diagnostics**: `get_correction_vectors()` for inspection

---

## Key Results Reference

### Option A Performance (RF models, n=2000, 50 runs)

| ρ | Proxy | Anchor | **Proposed** | Winner |
|---|-------|--------|--------------|--------|
| 1.0 | 0.667 | 0.408 | **0.264** | **Proposed (+60%)** ✓✓✓ |
| 0.8 | 0.759 | 0.874 | **0.713** | **Proposed (+6%)** ✓ |
| 0.5 | **0.895** | 1.298 | 1.104 | Proxy |

**Variance Mechanism**: 9x cancellation at ρ=1.0, 2-3x explosion at ρ=0.3

---

## When to Use This Method

### ✅ Use Proposed (Full DR)
- Both treatment arms in target (Option A)
- High correlation (ρ ≥ 0.8, shared bias regime)
- Large sample size (n ≥ 2000)

### ⚠️ Use Anchor-Only (Stages 1+2)
- Disconnected target (placebo-only)
- Option B with shared bias assumption
- Moderate sample size (n = 1000-2000)

### ⚠️ Use Proxy-Only (Stage 1)
- Low correlation (ρ < 0.5)
- Small sample size (n < 1000)
- No target data available

---

## Diagnostic Phase Archive

All diagnostic work from January 2026 is archived in:
```
archive/2026-01-30_diagnostic_phase/
```

**Key documents**:
- `README_ARCHIVE.md` - Complete summary of findings
- `FINAL_STATUS.md` - Detailed status and results
- `ADVISOR_FIXES_SUMMARY.md` - Implementation fixes
- `QUICK_REFERENCE.md` - One-page decision guide

**Accomplishments**:
- ✅ 5 comprehensive diagnostic checks completed
- ✅ Variance mechanism confirmed (covariance loss)
- ✅ Option B cancellation proven mathematically
- ✅ Advisor feedback implemented and tested
- ✅ RF vs Linear model comparison completed

---

## Citation

Based on: "Transfer Learning for Meta-analysis Under Covariate Shift" (IEEE)

See `archive/2026-01-30_diagnostic_phase/docs/` for original paper and reviewer responses.

---

## Next Steps

1. Focus on Option A experiments (both arms in target)
2. Use RF models for main results (shows method value)
3. Create publication-ready figures from diagnostic phase
4. Write methods section based on working implementation
5. Prepare honest limitations section

---

## Contact

For questions about the diagnostic phase, see archived documents in `archive/2026-01-30_diagnostic_phase/`.

**Status**: ✅ Ready for fresh implementation phase focused on publication
