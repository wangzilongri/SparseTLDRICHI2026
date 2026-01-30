# Results Index

This document maps all generated figures and tables to their corresponding experiments and source code.

**Last Updated**: 2026-01-28  
**Total Experiments**: 1 + 1 diagnostic analysis  
**Total Outputs**: 10 files (5 tables + 4 figures) + 1 diagnostic report

---

## Directory Structure

```
results/
├── ablation_core/          # Core component ablation study
│   ├── ablation_results.csv           # Raw results (all runs × all methods × all metrics)
│   ├── summary_statistics.csv         # Descriptive statistics (mean, std, median, min, max)
│   ├── pairwise_pehe.csv             # Pairwise Wilcoxon tests for PEHE
│   ├── pairwise_ate_error.csv        # Pairwise Wilcoxon tests for ATE Error
│   ├── pairwise_r2_cate.csv          # Pairwise Wilcoxon tests for R² CATE
│   ├── ablation_comparison.png       # Combined 3-panel comparison plot
│   ├── pehe_boxplot.png              # PEHE comparison (detailed)
│   ├── ate_error_boxplot.png         # ATE Error comparison (detailed)
│   └── r2_cate_boxplot.png           # R² CATE comparison (detailed)
└── diagnostics/            # Diagnostic analyses
    └── diagnostic_analysis.py        # Script for root cause investigation
```

---

## 🔬 Diagnostic Analysis & Fixes Applied

**Full Report**: [`docs/diagnostics/DIAGNOSTIC_REPORT.md`](docs/diagnostics/DIAGNOSTIC_REPORT.md)  
**Quick Summary**: [`docs/diagnostics/DIAGNOSTIC_SUMMARY.md`](docs/diagnostics/DIAGNOSTIC_SUMMARY.md)  
**Fixes Applied**: [`FIXES_APPLIED.md`](FIXES_APPLIED.md)  
**Before/After**: [`docs/diagnostics/BEFORE_AFTER_COMPARISON.md`](docs/diagnostics/BEFORE_AFTER_COMPARISON.md)  
**Script**: [`docs/diagnostics/diagnostic_analysis.py`](docs/diagnostics/diagnostic_analysis.py)

### Summary of Findings

**6 Root Causes Identified**:

1. ❌ **CRITICAL**: Hyperparameter mismatch (Proposed uses different proxy hyperparameters)
2. ⚠️ **CRITICAL**: High cross-fitting variance (pseudo-outcomes have 1.8x true CATE variance)
3. ⚠️ **HIGH**: Small sample per fold (only ~16-21 placebo per training fold)
4. ⚠️ **HIGH**: LASSO overfitting (selects 8 features, true has 2)
5. ℹ️ **MEDIUM**: Pseudo-outcome outliers (10.4% are >3σ from mean)
6. ℹ️ **LOW**: Limited MC runs (20 vs recommended 100)

**Key Metrics from Diagnostic**:
- LASSO selects 8/10 features (true: 2/10)
- Proxy bias before anchoring: +0.547
- Proxy bias after anchoring: -0.036 (70% improvement)
- Pseudo-outcome variance: 1.509 vs true CATE: 0.839 (1.8x ratio)
- Correlation with truth: Proposed 0.438 vs Anchor-Only 0.795

**Recommended Fix** (Priority 0):
```python
# 1. Match baseline hyperparameters
self.proxy_model = RandomForestRegressor(
    max_depth=8,        # ← from 6
    min_samples_leaf=20 # ← from 10
)

# 2. Reduce cross-fitting folds
PlaceboAnchoredDRLearner(n_folds_dr=3)  # ← from 5
```

**Fixes Applied**: 2026-01-28
1. ✅ Matched hyperparameters (max_depth 6→8, min_samples_leaf 10→20)
2. ✅ Reduced cross-fitting folds (5→3)
3. ✅ Added pseudo-outcome clipping (±3σ)
4. ✅ Changed CATE model (GBM → RF)

**Results**: PEHE 1.15 → **0.69** (-40% ✓), R² -0.97 → **0.30** (now positive ✓)

See full analysis in [`docs/diagnostics/BEFORE_AFTER_COMPARISON.md`](docs/diagnostics/BEFORE_AFTER_COMPARISON.md).

---

## Experiment 1: Core Component Ablation Study

**Source Code**: `experiments/ablation_core.py`  
**Run Command**: `python experiments/ablation_core.py`  
**Output Directory**: `results/ablation_core/`  
**Date Generated**: 2026-01-28

### Description

Compares 4 methods to isolate the contribution of each algorithmic component:

1. **No-Transfer**: Target placebo only (cannot predict heterogeneity)
2. **Proxy-Only**: Stage 1 only (pooled sources, no anchoring)
3. **Anchor-Only**: Stage 1 + 2 (anchoring, no DR correction)
4. **Proposed (Full)**: Stage 1 + 2 + 3 (full method with DR correction)

### Configuration

| Parameter | Value | Description |
|-----------|-------|-------------|
| `n_runs` | 20 | Monte Carlo replications |
| `n_features` | 10 | Number of baseline covariates |
| `n_effect_modifiers` | 3 | Number of covariates that modify treatment effect |
| `n_source_sites` | 3 | Number of source RCTs |
| `source_per_site` | 500 | Patients per source site (1,500 total) |
| `n_target` | 200 | Target site sample size (~100 placebo) |
| `disconnected` | True | Target has no treated arm (tests Option B) |
| `covariate_shift_scale` | 0.5 | Magnitude of covariate distribution shift |
| `bias_sparsity` | 2 | Number of non-zero transport bias coefficients |
| `seed` | 42 | Random seed for reproducibility |

---

## Tables

### Table 1: Raw Results (All Runs)
**File**: `results/ablation_core/ablation_results.csv`  
**Source**: `experiments/ablation_core.py` (line 76-123)  
**Format**: CSV (80 rows × 8 columns)

**Columns**:
- `Method`: Method name (No-Transfer, Proxy-Only, Anchor-Only, Proposed (Full))
- `Run`: Monte Carlo run index (0-19)
- `PEHE`: Precision in Estimation of Heterogeneous Effects (lower is better)
- `ATE_Error`: Absolute error in average treatment effect (lower is better)
- `Bias_ATE`: Signed bias in ATE (negative = underestimate, positive = overestimate)
- `R2_CATE`: R² for CATE predictions (higher is better)
- `Cal_RMSE_mu0`: Calibration RMSE for placebo outcome model
- `Cal_RMSE_mu1`: Calibration RMSE for treated outcome model

**Usage**: This is the complete dataset for all analyses. Use for:
- Replicating statistical tests
- Creating custom visualizations
- Verifying results

**Example Rows**:
```csv
Method,Run,PEHE,ATE_Error,Bias_ATE,R2_CATE,Cal_RMSE_mu0,Cal_RMSE_mu1
No-Transfer,0,1.086,0.690,0.690,-0.676,0.955,1.576
Proxy-Only,0,0.571,0.237,0.237,0.537,0.830,1.196
Anchor-Only,0,0.571,0.237,0.237,0.537,0.244,0.897
Proposed (Full),0,1.269,0.270,0.270,-1.289,,
```

---

### Table 2: Summary Statistics
**File**: `results/ablation_core/summary_statistics.csv`  
**Source**: `experiments/ablation_core.py` (line 230-234)  
**Format**: CSV (4 methods × 15 columns)

**Columns**: For each metric (PEHE, ATE_Error, Bias_ATE, R2_CATE, Cal_RMSE_mu0, Cal_RMSE_mu1):
- `mean`: Average across 20 runs
- `std`: Standard deviation
- `median`: Median value
- `min`: Minimum value
- `max`: Maximum value

**Key Findings**:
| Method | PEHE (mean±std) | ATE Error (mean±std) | R² CATE (mean±std) |
|--------|----------------|----------------------|-------------------|
| **Anchor-Only** | **0.608 ± 0.161** ⭐ | 0.186 ± 0.122 | **0.501 ± 0.499** ⭐ |
| **Proxy-Only** | **0.608 ± 0.161** ⭐ | 0.186 ± 0.122 | **0.501 ± 0.499** ⭐ |
| No-Transfer | 1.024 ± 0.141 | 0.462 ± 0.355 | -0.678 ± 0.543 |
| Proposed (Full) | 1.149 ± 0.145 ⚠️ | 0.238 ± 0.095 | -0.971 ± 0.689 |

⚠️ **Unexpected**: Proposed underperforms simpler baselines (see IMPLEMENTATION_SUMMARY.md Issue #1)

---

### Table 3: Pairwise Comparisons (PEHE)
**File**: `results/ablation_core/pairwise_pehe.csv`  
**Source**: `src/evaluation.py` `pairwise_wilcoxon()` function  
**Format**: CSV (6 comparisons × 8 columns)

**Columns**:
- `Method1`, `Method2`: Methods being compared
- `Statistic`: Wilcoxon signed-rank test statistic
- `P-value`: Raw p-value
- `P-value (corrected)`: Bonferroni-corrected p-value (α = 0.05 / 6)
- `Significant`: True if p-corrected < 0.05
- `Cohens_d`: Effect size (small: 0.2-0.5, medium: 0.5-0.8, large: >0.8)
- `Effect_Size`: Interpretation (negligible, small, medium, large)
- `Mean_Diff`: Difference in means (Method1 - Method2)

**Significant Findings** (p < 0.05 after Bonferroni):
1. **No-Transfer vs Proxy-Only**: d = 2.809 (large), p < 0.001 ***
2. **No-Transfer vs Anchor-Only**: d = 2.809 (large), p < 0.001 ***
3. **Proxy-Only vs Proposed (Full)**: d = -3.617 (large), p < 0.001 ***
4. **Anchor-Only vs Proposed (Full)**: d = -3.617 (large), p < 0.001 ***

**Interpretation**: 
- No-Transfer is significantly worse than Proxy-Only and Anchor-Only ✓
- Proposed is significantly worse than Proxy-Only and Anchor-Only ⚠️ (unexpected)

---

### Table 4: Pairwise Comparisons (ATE Error)
**File**: `results/ablation_core/pairwise_ate_error.csv`  
**Format**: Same as Table 3, but for ATE Error metric

**Significant Findings** (p < 0.05 after Bonferroni):
1. **No-Transfer vs Proxy-Only**: d = 1.222 (large), p = 0.010 **
2. **No-Transfer vs Anchor-Only**: d = 1.222 (large), p = 0.010 **
3. **No-Transfer vs Proposed (Full)**: d = 1.140 (large), p = 0.014 **

**Interpretation**: 
- All transfer methods significantly better than No-Transfer ✓
- No significant difference between Proxy-Only, Anchor-Only, and Proposed

---

### Table 5: Pairwise Comparisons (R² CATE)
**File**: `results/ablation_core/pairwise_r2_cate.csv`  
**Format**: Same as Table 3, but for R² CATE metric

**Significant Findings** (p < 0.05 after Bonferroni):
1. **No-Transfer vs Proxy-Only**: d = -2.135 (large), p < 0.001 ***
2. **No-Transfer vs Anchor-Only**: d = -2.135 (large), p < 0.001 ***
3. **Proxy-Only vs Proposed (Full)**: d = 2.386 (large), p < 0.001 ***
4. **Anchor-Only vs Proposed (Full)**: d = 2.386 (large), p < 0.001 ***

**Interpretation**: 
- Proxy-Only and Anchor-Only capture heterogeneity well (R² > 0.5) ✓
- No-Transfer cannot capture heterogeneity (R² < 0) ✓
- Proposed has negative R² (worse than constant prediction) ⚠️

---

## Figures

### Figure 1: Combined Ablation Comparison (3-Panel)
**File**: `results/ablation_core/ablation_comparison.png`  
**Source**: `experiments/ablation_core.py` `visualize_results()` function (line 141-198)  
**Format**: PNG (15" × 5", 300 DPI)

**Panels**:
- **Left**: PEHE comparison (box plots)
- **Middle**: ATE Error comparison (box plots)
- **Right**: R² CATE comparison (box plots)

**Purpose**: Overview comparison of all methods across primary metrics

**Key Visual Insights**:
- No-Transfer has highest PEHE (worst individual predictions)
- Proxy-Only and Anchor-Only have identical performance (overlapping boxes)
- Proposed has highest PEHE among transfer methods (unexpected)

**Usage**: Use this as the main figure in papers/presentations

---

### Figure 2: PEHE Comparison (Detailed)
**File**: `results/ablation_core/pehe_boxplot.png`  
**Source**: `experiments/ablation_core.py` (line 247-269)  
**Format**: PNG (8" × 6", 300 DPI)

**Content**: Box plots comparing PEHE across 4 methods

**Statistical Context**:
- Friedman test: χ² = 44.397, **p < 0.001** (methods differ significantly)
- Best: Anchor-Only & Proxy-Only (PEHE ≈ 0.61)
- Worst: Proposed (Full) (PEHE ≈ 1.15)

**Interpretation**:
- Lower is better (closer to true CATE)
- Boxes show median, IQR (25th-75th percentile)
- Whiskers show min/max (excluding outliers)

**Usage**: Use when focusing specifically on patient-level prediction accuracy

---

### Figure 3: ATE Error Comparison (Detailed)
**File**: `results/ablation_core/ate_error_boxplot.png`  
**Source**: `experiments/ablation_core.py` (line 247-269)  
**Format**: PNG (8" × 6", 300 DPI)

**Content**: Box plots comparing ATE Error across 4 methods

**Statistical Context**:
- Friedman test: χ² = 14.274, **p = 0.003** (methods differ significantly)
- Best: Proxy-Only & Anchor-Only (ATE Error ≈ 0.19)
- Worst: No-Transfer (ATE Error ≈ 0.46)

**Interpretation**:
- Lower is better (closer to true population effect)
- All transfer methods much better than No-Transfer
- Proposed performs competitively on population-level metric

**Usage**: Use when focusing on average treatment effect accuracy

---

### Figure 4: R² CATE Comparison (Detailed)
**File**: `results/ablation_core/r2_cate_boxplot.png`  
**Source**: `experiments/ablation_core.py` (line 247-269)  
**Format**: PNG (8" × 6", 300 DPI)

**Content**: Box plots comparing R² CATE across 4 methods

**Statistical Context**:
- Friedman test: χ² = 43.562, **p < 0.001** (methods differ significantly)
- Best: Proxy-Only & Anchor-Only (R² ≈ 0.50)
- Worst: Proposed (Full) (R² ≈ -0.97)

**Interpretation**:
- Higher is better (fraction of heterogeneity variance explained)
- R² < 0 means worse than constant prediction
- Proposed fails to capture treatment effect heterogeneity

**Usage**: Use when focusing on ability to predict individual-level variation

---

## How to Reproduce

### Exact Replication
```bash
cd /Users/zilongwang/Sparse_TL_DR_ICHI2026
source venv/bin/activate
python experiments/ablation_core.py
```

This will regenerate all 10 files in `results/ablation_core/`.

### Custom Configuration
```python
from experiments.ablation_core import run_core_ablation

# Example: 100 runs for publication-quality statistics
results_df = run_core_ablation(
    n_runs=100,          # More runs → better statistical power
    n_features=20,       # More features → harder problem
    disconnected=False,  # Target has treated arm → tests Option A
    seed=12345
)
```

---

## Statistical Tests Summary

All experiments use:
- **Friedman test**: Non-parametric omnibus test (H0: all methods equal)
- **Wilcoxon signed-rank**: Pairwise comparisons (paired samples)
- **Bonferroni correction**: α = 0.05 / (number of comparisons)
- **Cohen's d**: Standardized effect size

**Significance Levels**:
- `***`: p < 0.001 (highly significant)
- `**`: p < 0.01 (significant)
- `*`: p < 0.05 (marginally significant)

---

## Known Issues

See `IMPLEMENTATION_SUMMARY.md` for detailed discussion:

1. **Issue #1**: Proposed underperforms (PEHE 1.15 vs 0.61 for baselines)
   - Possible cause: Cross-fitting variance, hyperparameter tuning
   - Status: Under investigation

2. **Issue #2**: Anchor-Only = Proxy-Only (identical performance)
   - Possible cause: LASSO selecting zero features
   - Status: Under investigation

3. **Issue #3**: Missing calibration metrics for Proposed
   - Cause: No `predict_counterfactuals()` method implemented
   - Status: To be fixed

---

## Future Experiments

Planned experiments (see `docs/PRIORITY_CHECKLIST.md`):

1. **Experiment 2**: Covariate dimensionality sweep (p ∈ {5, 10, 20, 50, 100})
2. **Experiment 3**: Comprehensive baseline comparison (+IPW, +AIPW, +IPD-NMA)
3. **Experiment 4**: Multi-treatment disconnected networks
4. **Experiment 5**: Non-linear transport bias robustness
5. **Experiment 6**: Site imbalance stress test

Each will have its own subdirectory in `results/`.

---

## Citation

When referencing results from this project:

```
Wang et al. (2026). Transfer Learning for Meta-analysis Under Covariate Shift.
Experiments run on: 2026-01-28
Configuration: 20 MC runs, 10 features, disconnected target
Software: Python 3.13.6, scikit-learn 1.8.0
```

---

## Appendix: File Metadata

| File | Size | Rows | Columns | Generated |
|------|------|------|---------|-----------|
| `ablation_results.csv` | 9.5 KB | 80 | 8 | 2026-01-28 23:38 |
| `summary_statistics.csv` | 1.8 KB | 4 | 15 | 2026-01-28 23:38 |
| `pairwise_pehe.csv` | 1.1 KB | 6 | 8 | 2026-01-28 23:38 |
| `pairwise_ate_error.csv` | 1.1 KB | 6 | 8 | 2026-01-28 23:38 |
| `pairwise_r2_cate.csv` | 1.1 KB | 6 | 8 | 2026-01-28 23:38 |
| `ablation_comparison.png` | 167 KB | - | - | 2026-01-28 23:38 |
| `pehe_boxplot.png` | 52 KB | - | - | 2026-01-28 23:38 |
| `ate_error_boxplot.png` | 51 KB | - | - | 2026-01-28 23:38 |
| `r2_cate_boxplot.png` | 52 KB | - | - | 2026-01-28 23:38 |

**Total Storage**: ~350 KB

---

## Questions?

For implementation details, see:
- `IMPLEMENTATION_SUMMARY.md`: Current status and known issues
- `docs/DESIGN.md`: Algorithm specification
- `docs/PRIORITY_CHECKLIST.md`: Action items and timeline
