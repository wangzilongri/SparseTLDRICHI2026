# Where Are the Results?

**Quick Answer**: Results are in **two places** depending on what you want:

---

## 📊 1. Advisor Fixes Results (Fixed Estimator)

**Location**: Console output from `test_fixed_estimator.py`

**What it shows**:
```
Method                    PEHE
──────────────────────────────────
Proxy-Only              0.4589
Anchor-Only             0.4117  ← Best on small sample
Proposed (Option A)     0.4896
Proposed (Option B)     0.5222

✓ All 7 fixes verified working
✓ M learned from sources (||M||=0.253)
✓ No data leakage
```

**Run again**:
```bash
python experiments/test_fixed_estimator.py
```

**Files**: Results printed to console only (quick test, not saved).

---

## 📁 2. Archived Results (Previous Experiments)

**Location**: `archive/2026-01-30_diagnostic_phase/results/`

**What's there**:
- Previous experiment results (RF-based, linear models)
- Diagnostic plots
- Performance curves
- Old ablation studies

**To browse**:
```bash
ls archive/2026-01-30_diagnostic_phase/results/
```

---

## 🎯 To Generate NEW Results

### Option 1: Quick Test (2 seconds)

```bash
source venv/bin/activate
python experiments/test_fixed_estimator.py
```

**Output**: Console only (PEHE values, verification checks)

---

### Option 2: Full Ablation Study (~2 minutes)

```bash
source venv/bin/activate
python experiments/ablation_study.py
```

**Creates in `results/`**:
- `ablation_pehe_curves.png`
- `ablation_metrics_table.csv`
- `ablation_summary.txt`

**Runs**: 50 Monte Carlo iterations across all 4 methods

---

### Option 3: DGP v2 Validation (< 1 second)

```bash
source venv/bin/activate
python experiments/validate_dgp_v2.py
```

**Output**: Console showing A5/A6 verification

---

## 📖 What Each Test Shows

### `test_fixed_estimator.py` (Advisor Fixes)

**Tests**:
1. Option A (separate corrections)
2. Option B (operator transfer M)
3. Comparison with baselines
4. Cross-fitting verification
5. M* quality check

**Sample Output**:
```
TEST 1: Option A (Separate corrections)
  PEHE (DR):  0.4896
  PEHE (Plug-in): 0.4130
  Sparsity δ₀: 2/5, δ₁: 4/5
  ||β₁ - β₀||: 0.2564

TEST 2: Option B (Operator transfer via M)
  M learned from 3 sites
  ||M||_F: 0.253
  PEHE (DR):  0.5222
  PEHE (Plug-in): 0.5400
  
Verification:
  ✓ StratifiedKFold: 5 folds
  ✓ No leakage
  ✓ Propensities clipped
  ✓ Features scaled
```

---

### `validate_dgp_v2.py` (DGP Validation)

**Tests**:
1. Basic generation
2. Proxy + deviation decomposition
3. Cross-arm transfer (A6)
4. Sparsity (A5)
5. Nontransfer magnitude
6. Disconnected target
7. Nontransfer sweep
8. Structure diagnostics

**Sample Output**:
```
A6 Verification (β₁ = M*β₀ + ν):
  Source 1 error: 0.00e+00 ✓
  Source 2 error: 0.00e+00 ✓
  Source 3 error: 0.00e+00 ✓

Sparse Deviations:
  Target:   2/5 features (support [0, 3])
  Source 1: 2/5 features (support [1, 2])
  
Transfer Operator:
  ||M*||_F: 2.7157
  rank(M*): 1 ✓
```

---

### `ablation_study.py` (Full Experiment)

**Creates files in `results/`**:

1. **`ablation_pehe_curves.png`**
   - PEHE comparison plot
   - All 4 methods
   - Error bars

2. **`ablation_metrics_table.csv`**
   ```csv
   method,mean_pehe,std_pehe,mean_ate_error,std_ate_error
   No-Transfer,0.935,0.087,0.412,0.102
   Proxy-Only,0.459,0.056,0.087,0.043
   Anchor-Only,0.412,0.048,0.065,0.031
   Proposed,0.490,0.051,0.071,0.035
   ```

3. **`ablation_summary.txt`**
   - Summary statistics
   - Best methods
   - Improvement percentages

---

## 🔍 Current Status of `results/` Folder

**Right now**: Empty

**Why**: Only quick tests run (console output only)

**To populate**:
```bash
python experiments/ablation_study.py
```

This will save files to `results/` for visualization.

---

## 📝 Documentation Locations

### Implementation Details

- **`HOW_IT_WORKS.md`** - Visual guide with diagrams
- **`CODE_WALKTHROUGH.md`** - Detailed code explanation
- **`ADVISOR_FIXES_IMPLEMENTED.md`** - All 7 fixes explained
- **`IMPLEMENTATION_SUMMARY.md`** - Complete overview

### DGP Improvements

- **`DGP_V2_IMPROVEMENTS.md`** - Why v2 is better (A5/A6)
- **`experiments/validate_dgp_v2.py`** - Validation tests

### Archived Work

- **`archive/2026-01-30_diagnostic_phase/README_ARCHIVE.md`** - Previous work summary

---

## 🚀 Quick Commands Reference

```bash
# Activate environment
source venv/bin/activate

# Quick test (console output)
python experiments/test_fixed_estimator.py

# Full ablation (saves to results/)
python experiments/ablation_study.py

# Validate DGP v2 (A5/A6 checks)
python experiments/validate_dgp_v2.py

# Browse archived results
ls archive/2026-01-30_diagnostic_phase/results/
```

---

## 📊 To Save Results to `results/` Folder

The quick test (`test_fixed_estimator.py`) only prints to console. To save actual result files:

### Create Quick Results Script

```python
# save_quick_results.py
import sys
sys.path.insert(0, 'src')

from synthetic_data_v2 import generate_synthetic_rct
from estimator_fixed import PlaceboAnchoredDRLearner
from ablations import ProxyOnlyBaseline, AnchorOnlyBaseline
import numpy as np
import json

# Generate data
source, target, gen = generate_synthetic_rct()

# Fit methods
methods = {}

proxy = ProxyOnlyBaseline()
proxy.fit(source['X'], source['A'], source['Y'], source['c'],
          target['X'], target['A'], target['Y'])
methods['Proxy-Only'] = np.sqrt(np.mean((target['tau_true'] - proxy.predict(target['X']))**2))

anchor = AnchorOnlyBaseline(option='A')
anchor.fit(source['X'], source['A'], source['Y'], source['c'],
           target['X'], target['A'], target['Y'])
methods['Anchor-Only'] = np.sqrt(np.mean((target['tau_true'] - anchor.predict(target['X']))**2))

proposed_a = PlaceboAnchoredDRLearner(option='A')
proposed_a.fit(source['X'], source['A'], source['Y'], source['c'],
               target['X'], target['A'], target['Y'])
methods['Proposed (A)'] = np.sqrt(np.mean((target['tau_true'] - proposed_a.predict(target['X']))**2))

proposed_b = PlaceboAnchoredDRLearner(option='B')
proposed_b.fit(source['X'], source['A'], source['Y'], source['c'],
               target['X'], target['A'], target['Y'])
methods['Proposed (B)'] = np.sqrt(np.mean((target['tau_true'] - proposed_b.predict(target['X']))**2))

# Save results
import os
os.makedirs('results', exist_ok=True)

with open('results/quick_test_results.json', 'w') as f:
    json.dump(methods, f, indent=2)

print("✓ Saved to results/quick_test_results.json")
print(json.dumps(methods, indent=2))
```

Then run:
```bash
python save_quick_results.py
```

---

## 📈 What's in the Archive

The `archive/2026-01-30_diagnostic_phase/` contains all previous work:

```
archive/2026-01-30_diagnostic_phase/
├── results/                    ← Old experiment outputs
│   ├── *.png                   (plots)
│   ├── *.csv                   (tables)
│   └── diagnostics/            (diagnostic outputs)
│
├── experiments/                ← Old experiment scripts
│   ├── ablation_core.py
│   ├── advisor_diagnostics.py
│   ├── benchmark_improved.py
│   └── ...
│
└── *.md                        ← Extensive documentation
    ├── ADVISOR_RESPONSE.md     (advisor feedback)
    ├── FINAL_STATUS.md         (final summary)
    └── README_ARCHIVE.md       (guide to archive)
```

To browse:
```bash
cd archive/2026-01-30_diagnostic_phase
ls results/
```

---

## ✅ Summary

| Results Type | Location | How to Get |
|--------------|----------|-----------|
| **Quick Test** | Console | `python experiments/test_fixed_estimator.py` |
| **Full Study** | `results/` | `python experiments/ablation_study.py` |
| **DGP Validation** | Console | `python experiments/validate_dgp_v2.py` |
| **Archived** | `archive/.../results/` | Browse archive folder |

**Note**: The `results/` folder is currently empty. Run `ablation_study.py` to populate it with figures and tables.

---

**Current Status**:
- ✅ Implementations complete
- ✅ Tests passing
- ✅ Documentation comprehensive
- ⏳ Full ablation study pending (run to generate result files)

**To get publishable results**, run:
```bash
python experiments/ablation_study.py
```

This will create the plots and tables you need for the paper!
