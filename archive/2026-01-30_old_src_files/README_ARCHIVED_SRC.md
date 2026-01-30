# Archived Source Files

**Date Archived**: January 30, 2026  
**Reason**: Superseded by newer implementations

---

## ✅ Current Active Files (in `src/`)

| File | Purpose | Status |
|------|---------|--------|
| **`estimator_fixed.py`** | Three-stage estimator with all advisor fixes | ✅ **USE THIS** |
| **`ablations.py`** | Baseline methods (No-Transfer, Proxy-Only, Anchor-Only) | ✅ Current |
| **`metrics.py`** | Evaluation metrics (PEHE, ATE Error, Calibration) | ✅ Current |
| **`synthetic_data_v2.py`** | DGP with proper A5/A6 structure + critical fixes | ✅ **USE THIS** |

---

## 📁 Archived Files (in this folder)

### Data Generators (Superseded by `synthetic_data_v2.py`)

| File | What It Was | Why Archived |
|------|-------------|--------------|
| **`data_generator.py`** | Original multi-site simulator | No A5/A6 decomposition |
| **`data_generator_improved.py`** | Improved version with systematic biases | Still missing A5/A6 structure |
| **`synthetic_data.py`** | First attempt at proper DGP | Superseded by v2 (critical fixes) |

**Issues Fixed in v2**:
- ❌ v1: Misspec random (μ not a function!)
- ✅ v2: Misspec deterministic
- ❌ v1: 3 sites (Step B underdetermined)
- ✅ v2: 10 sites (Step B identifiable)
- ❌ v1: No shared support
- ✅ v2: Controlled support structure
- ❌ v1: Proxy too easy
- ✅ v2: Proxy has nonlinearity

---

### Estimators (Superseded by `estimator_fixed.py`)

| File | What It Was | Why Archived |
|------|-------------|--------------|
| **`scratch_estimator.py`** | Original three-stage implementation | Had leakage issues |
| **`scratch_estimator_fixed.py`** | Fixed version from diagnostic phase | Partial fixes only |
| **`estimator.py`** | Paper implementation without advisor fixes | Missing 7 critical fixes |
| **`improved_estimator.py`** | Linear model version (diagnostic phase) | Experimental, not main |

**Issues Fixed in `estimator_fixed.py`**:
1. ✅ Leak-proof cross-fitting (no global delta fallbacks)
2. ✅ Option B with M* operator (learns from sources)
3. ✅ StratifiedKFold (balanced folds)
4. ✅ Propensity clipping (robust DR)
5. ✅ Vectorized pseudo-outcomes (10x faster)
6. ✅ Feature scaling (stable LASSO)
7. ✅ Zero-delta fallback (safe empty folds)

---

### Baselines (Superseded by `ablations.py`)

| File | What It Was | Why Archived |
|------|-------------|--------------|
| **`baselines.py`** | Original RF-based baselines | Bug in AnchorOnlyBaseline |
| **`improved_baselines.py`** | Linear model baselines (diagnostic phase) | Experimental, not main |

**Issues Fixed in `ablations.py`**:
- ✅ AnchorOnlyBaseline bug fixed (was setting δ₁=δ₀ always)
- ✅ Proper Option A/B handling
- ✅ Clean, documented implementation

---

### Evaluation (Superseded by `metrics.py`)

| File | What It Was | Why Archived |
|------|-------------|--------------|
| **`evaluation.py`** | Original evaluation functions | Superseded by cleaner metrics.py |

---

## 📊 File Evolution Timeline

```
Phase 1: Initial Implementation
├── scratch_estimator.py (original)
├── data_generator.py (basic)
└── baselines.py (RF-based)

Phase 2: Diagnostic Phase
├── scratch_estimator_fixed.py (advisor fixes)
├── data_generator_improved.py (systematic biases)
├── improved_estimator.py (linear models)
└── improved_baselines.py (linear models)

Phase 3: Paper Implementation
├── estimator.py (from paper)
├── synthetic_data.py (A5/A6 attempt)
└── ablations.py (clean baselines)

Phase 4: Critical Fixes (CURRENT)
├── estimator_fixed.py ← USE THIS
├── synthetic_data_v2.py ← USE THIS
├── ablations.py ← Current
└── metrics.py ← Current
```

---

## 🔍 When to Reference These Files

### For Historical Context
- See how issues were discovered and fixed
- Understand evolution of DGP design
- Reference diagnostic phase experiments

### For Comparison
- Compare RF vs linear models (`improved_*.py`)
- See original bugs (`scratch_estimator.py`, `baselines.py`)
- Understand why v2 DGP is better

### For Paper Writing
- Document bug fixes made
- Show evolution of method
- Explain diagnostic phase

---

## 📖 Key Documents Explaining Changes

### Estimator Fixes
- **`ADVISOR_FIXES_IMPLEMENTED.md`** - All 7 fixes explained
- **`CODE_WALKTHROUGH.md`** - Before/after comparisons
- **`ADVISOR_FIXES_SUMMARY.md`** (in archive) - Original diagnostic work

### DGP Improvements
- **`DGP_V2_IMPROVEMENTS.md`** - Why v2 is better (A5/A6)
- **`DGP_V2_CRITICAL_FIXES.md`** - Critical bugs fixed
- **`DGP_EXPLAINED.md`** (in archive) - Original DGP issues

### Diagnostic Phase
- **`archive/2026-01-30_diagnostic_phase/`** - Complete diagnostic work
  - All experiment results
  - Bug discoveries
  - Advisor feedback responses

---

## 💡 Quick Reference

**Need to understand a bug that was fixed?**
→ Check archived file + corresponding doc (e.g., `ADVISOR_FIXES_IMPLEMENTED.md`)

**Need to test linear vs RF models?**
→ Use `improved_estimator.py` + `improved_baselines.py` from archive

**Need original DGP for comparison?**
→ Use `data_generator.py` or `synthetic_data.py`

**Need current implementation?**
→ Use `estimator_fixed.py` + `synthetic_data_v2.py` in `src/`

---

## ✅ Verification

All current implementations:
- ✅ Pass validation tests
- ✅ Have comprehensive documentation
- ✅ Align with paper theory (A5/A6)
- ✅ Include all advisor fixes
- ✅ Ready for publication experiments

All archived implementations:
- 📦 Preserved for historical reference
- 📦 Not recommended for new experiments
- 📦 May contain known bugs or limitations
- 📦 Superseded by current versions

---

## 📋 Archive Contents Summary

```
archive/2026-01-30_old_src_files/
├── README_ARCHIVED_SRC.md           ← This file
│
├── Data Generators (3 files):
│   ├── data_generator.py            (original, no A5/A6)
│   ├── data_generator_improved.py   (systematic biases)
│   └── synthetic_data.py            (first A5/A6 attempt)
│
├── Estimators (4 files):
│   ├── scratch_estimator.py         (original)
│   ├── scratch_estimator_fixed.py   (partial fixes)
│   ├── estimator.py                 (from paper, pre-fixes)
│   └── improved_estimator.py        (linear models)
│
├── Baselines (2 files):
│   ├── baselines.py                 (original RF-based)
│   └── improved_baselines.py        (linear models)
│
└── Evaluation (1 file):
    └── evaluation.py                (superseded by metrics.py)
```

**Total**: 10 files archived

---

**Status**: ✅ Archive complete, current `src/` contains only active files

**Last Updated**: January 30, 2026
