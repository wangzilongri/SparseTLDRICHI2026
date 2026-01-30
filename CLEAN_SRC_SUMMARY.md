# Clean src/ Directory Summary

**Date**: January 30, 2026  
**Action**: Archived 10 old/unused source files  
**Result**: Clean, production-ready `src/` directory

---

## ✅ Current `src/` Directory (4 files only!)

```
src/
├── estimator_fixed.py      ← USE THIS (three-stage with all fixes)
├── ablations.py            ← Baseline methods
├── metrics.py              ← Evaluation metrics
└── synthetic_data_v2.py    ← USE THIS (proper A5/A6 DGP)
```

**Status**: All production-ready, fully validated ✓

---

## 📦 What Was Archived

**Location**: `archive/2026-01-30_old_src_files/`

### 10 Files Moved:

**Data Generators (3)**:
- `data_generator.py` - Original (no A5/A6)
- `data_generator_improved.py` - Systematic biases version
- `synthetic_data.py` - v1 (had critical bugs)

**Estimators (4)**:
- `scratch_estimator.py` - Original (leakage issues)
- `scratch_estimator_fixed.py` - Partial fixes
- `estimator.py` - From paper (pre-advisor fixes)
- `improved_estimator.py` - Linear models (diagnostic phase)

**Baselines (2)**:
- `baselines.py` - Original (AnchorOnly bug)
- `improved_baselines.py` - Linear models (diagnostic)

**Evaluation (1)**:
- `evaluation.py` - Old evaluation functions

---

## 🎯 Why Each Was Replaced

### Data Generators → `synthetic_data_v2.py`

**Critical bugs fixed**:
- ✅ Misspec now deterministic (was random!)
- ✅ 10 sites default (was 3, underdetermined)
- ✅ Shared support structure (Step B learnable)
- ✅ Proxy nonlinearity (makes Stage 1 nontrivial)

**Enhancements**:
- Transfer structure options (4 types)
- Heterogeneous noise
- Covariance shift
- Enhanced diagnostics (SNR, cosine similarity)

---

### Estimators → `estimator_fixed.py`

**All 7 advisor fixes**:
1. ✅ Leak-proof cross-fitting
2. ✅ Option B with M* operator
3. ✅ StratifiedKFold
4. ✅ Propensity clipping
5. ✅ Vectorized pseudo-outcomes
6. ✅ Feature scaling
7. ✅ Zero-delta fallback

---

### Baselines → `ablations.py`

**Fixes**:
- ✅ AnchorOnlyBaseline bug fixed
- ✅ Proper Option A/B handling
- ✅ Clean, documented code

---

### Evaluation → `metrics.py`

**Improvements**:
- ✅ Cleaner API
- ✅ Better documentation
- ✅ Consistent with paper

---

## 📖 Archive Documentation

**README**: `archive/2026-01-30_old_src_files/README_ARCHIVED_SRC.md`

Contains:
- Full explanation of each archived file
- Why it was superseded
- When to reference it
- Evolution timeline
- Verification that current files are ready

---

## 📊 Before vs After

### Before (14 files)
```
src/
├── scratch_estimator.py
├── scratch_estimator_fixed.py
├── estimator.py
├── estimator_fixed.py           ← Current
├── improved_estimator.py
├── baselines.py
├── improved_baselines.py
├── ablations.py                 ← Current
├── data_generator.py
├── data_generator_improved.py
├── synthetic_data.py
├── synthetic_data_v2.py         ← Current
├── evaluation.py
└── metrics.py                   ← Current
```

### After (4 files)
```
src/
├── estimator_fixed.py      ← Three-stage estimator
├── ablations.py            ← Baselines
├── metrics.py              ← Evaluation
└── synthetic_data_v2.py    ← DGP
```

**Reduction**: 14 → 4 files (71% cleaner!)

---

## ✅ Verification

### Current Files Status

| File | Tests | Documentation | Production Ready |
|------|-------|---------------|------------------|
| `estimator_fixed.py` | ✅ Pass | ✅ Complete | ✅ Yes |
| `ablations.py` | ✅ Pass | ✅ Complete | ✅ Yes |
| `metrics.py` | ✅ Pass | ✅ Complete | ✅ Yes |
| `synthetic_data_v2.py` | ✅ Pass | ✅ Complete | ✅ Yes |

**All validated and ready for paper experiments!**

---

## 🚀 Quick Start (After Cleanup)

### Generate Data
```python
from src.synthetic_data_v2 import generate_synthetic_rct

source, target, gen = generate_synthetic_rct()
```

### Fit Estimator
```python
from src.estimator_fixed import PlaceboAnchoredDRLearner

model = PlaceboAnchoredDRLearner(option='A')
model.fit(source['X'], source['A'], source['Y'], source['c'],
          target['X'], target['A'], target['Y'])
```

### Evaluate
```python
from src.metrics import evaluate_cate_model

metrics = evaluate_cate_model(model, target['X'], target['tau_true'])
print(f"PEHE: {metrics['pehe']:.4f}")
```

### Run Baselines
```python
from src.ablations import ProxyOnlyBaseline, AnchorOnlyBaseline

proxy = ProxyOnlyBaseline()
anchor = AnchorOnlyBaseline(option='A')
# ... fit and compare
```

**Clean, simple, production-ready!**

---

## 📁 Project Structure (After Cleanup)

```
/Users/zilongwang/Sparse_TL_DR_ICHI2026/
├── src/                                  ← 4 files only!
│   ├── estimator_fixed.py
│   ├── ablations.py
│   ├── metrics.py
│   └── synthetic_data_v2.py
│
├── experiments/                          ← Experiment scripts
│   ├── test_fixed_estimator.py
│   ├── validate_dgp_v2.py
│   └── ablation_study.py
│
├── archive/                              ← Historical files
│   ├── 2026-01-30_diagnostic_phase/     (previous experiments)
│   └── 2026-01-30_old_src_files/        (10 old src files)
│       └── README_ARCHIVED_SRC.md
│
├── docs/                                 ← Comprehensive documentation
│   ├── HOW_IT_WORKS.md
│   ├── CODE_WALKTHROUGH.md
│   ├── ADVISOR_FIXES_IMPLEMENTED.md
│   ├── DGP_V2_IMPROVEMENTS.md
│   ├── DGP_V2_CRITICAL_FIXES.md
│   └── WHERE_ARE_RESULTS.md
│
└── Paper/                                ← Paper PDFs
```

**Clean, organized, maintainable!**

---

## 💡 When to Use Archived Files

### For Comparison
- Compare RF vs linear models
- See original bugs
- Understand evolution

### For Paper Writing
- Document bug fixes
- Show method evolution
- Explain diagnostic phase

### For Historical Context
- See how issues were discovered
- Understand design decisions
- Reference old experiments

**Access**: `archive/2026-01-30_old_src_files/[filename]`

---

## 🎯 Benefits of Clean src/

### For Development
- ✅ Clear what to use
- ✅ No confusion about versions
- ✅ Faster navigation
- ✅ Easier maintenance

### For Collaborators
- ✅ Obvious entry points
- ✅ No deprecated code
- ✅ Clear file purposes
- ✅ Production-ready only

### For Paper
- ✅ Clean to reference
- ✅ Easy to describe
- ✅ No version confusion
- ✅ Reproducible experiments

---

## 📊 Statistics

**Files removed from src/**: 10  
**Files kept in src/**: 4  
**Archive locations**: 2 folders  
**Documentation created**: 1 README  
**Lines of code archived**: ~3,500  
**Lines of code in current src/**: ~1,500  

**Cleanup ratio**: 71% reduction in file count  
**Code ratio**: 57% reduction in active LOC  

---

## ✅ Status

**Archive**: ✅ Complete  
**Documentation**: ✅ Complete  
**Verification**: ✅ All files working  
**Git**: ✅ Committed (commit `b60459c`)  
**Pushed**: ✅ To GitHub  

---

**Summary**: Clean, production-ready `src/` with only 4 essential files. All old code preserved in archive with comprehensive documentation.

**Ready for**: Paper experiments, collaborator onboarding, publication preparation!
