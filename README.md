# Placebo-Anchored DR-Learner for Transfer Learning

**Status**: Fresh start after diagnostic phase  
**Date**: January 30, 2026

---

## Overview

Three-stage doubly robust learner for transferring treatment effect estimates from multiple source RCTs to a target population under covariate shift.

---

## Quick Start

### Installation

**Option 1: Quick Setup (Recommended)**
```bash
# Run the setup script (handles Python + R)
./setup.sh

# Activate environment
source activate.sh
```

**Option 2: Manual Setup**
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Unix/Mac
# or: venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### R/glmtrans Setup (Optional but Recommended)

The `glmtrans` R package (Tian & Feng, JASA 2023) provides state-of-the-art transfer learning methods. **Requires R 4.4+**.

**Check status:**
```bash
cd src && python -m glmtrans_wrapper --status
```

**If R 4.4+ is not installed:**
```bash
# Option A: Let setup.sh install R locally (no root needed)
./setup.sh  # Will prompt to install R 4.4.2

# Option B: Install R locally manually
mkdir -p ~/local && cd ~/local
wget https://cran.r-project.org/src/base/R-4/R-4.4.2.tar.gz
tar -xzf R-4.4.2.tar.gz && cd R-4.4.2
./configure --prefix=$HOME/local/R-4.4.2 --enable-R-shlib
make -j 4 && make install
export PATH=$HOME/local/R-4.4.2/bin:$PATH

# Option C: Use conda
conda create -n r44 r-base=4.4 -c conda-forge
conda activate r44
```

**Install glmtrans package:**
```bash
Rscript -e 'install.packages("glmtrans", repos="https://cloud.r-project.org")'
```

**Using a custom R library path:**
```bash
# If glmtrans is installed elsewhere
export GLMTRANS_R_LIBS=/path/to/R/library
# or
export R_LIBS_USER=/path/to/R/library
```

**Note:** If R/glmtrans is not available, the benchmark will automatically use Python-only fallback methods (`ProposedA_FullyDirect`, `ProposedB_SourceDR`).

### Run Experiments

```bash
# Quick test of all estimators
python experiments/test_estimators.py

# Full ablation study (20 runs)
python experiments/ablation_study.py

# Run benchmark sweeps
python -m experiments.core_sweeps --sweep gold_fair_dim --n_rep 20 --output results/my_sweep

# Run all fair sweeps
python -m experiments.core_sweeps --sweep all_fair --n_rep 20 --output results/fair_sweeps

# See all available sweeps
python -m experiments.core_sweeps --help
```

---

## Available Benchmark Sweeps

### Fair DGP Sweeps (Recommended)

These sweeps use a **fair DGP** designed for honest method comparison with controlled assumptions.

| Sweep | Command | Grid | Description |
|-------|---------|------|-------------|
| **gold_fair_dim** | `--sweep gold_fair_dim` | 5×4 (m₁×p) | Target budget × Dimensionality. Varies m₁∈{0,50,100,200,500} with m₀=m₁+50, p∈{10,20,50,100}. Generates heatmaps with (m₀,m₁) tuples. |
| **gold_fair_sources** | `--sweep gold_fair_sources` | 5×5 (C×m₁) | Source sites × Target budget. Varies C∈{2,5,10,20,50} sites (1000 samples each), m₁∈{0,50,100,200,500}. Tests multi-site heterogeneity value. |
| **gold_fair** | `--sweep gold_fair` | 4×4 (m₀×m₁) | Classic target budget grid. Varies m₀∈{50,100,200,500}, m₁∈{0,50,100,200}. |
| **snr_ladder** | `--sweep snr_ladder` | 1D (6 pts) | SNR stress test. Varies nontransfer_scale∈{0,0.05,0.1,0.2,0.3,0.4}. Tests where cross-arm transfer breaks down. |
| **overlap_ladder** | `--sweep overlap_ladder` | 1D (5 pts) | Overlap stress test. Varies overlap_λ∈{0,0.25,0.5,0.75,1.0}. Tests covariate shift sensitivity. |
| **drift_ladder** | `--sweep drift_ladder` | 1D (5 pts) | Intercept drift stress. Varies drift_scale∈{0,0.5,1.0,2.0,4.0}. Tests arm baseline variance. |
| **all_fair** | `--sweep all_fair` | All above | Runs all fair sweeps sequentially. |

### L1-TCL Sweeps (Alternative DGP)

Based on arXiv 2305.09126v3. Uses constant ATE with propensity score transfer.

| Sweep | Command | Grid | Description |
|-------|---------|------|-------------|
| **l1tcl** | `--sweep l1tcl` | 1D (5 pts) | Basic L1-TCL. Varies target size m∈{50,100,200,500,1000}. |
| **l1tcl_dim** | `--sweep l1tcl_dim` | 1D (4 pts) | Dimensionality. Varies p∈{10,20,50,100}. |
| **l1tcl_sparsity** | `--sweep l1tcl_sparsity` | 1D (5 pts) | PS sparsity. Varies s/p∈{0.02,0.06,0.1,0.14,0.2}. |
| **l1tcl_gold** | `--sweep l1tcl_gold` | 2D (5×4) | Target budget × m₁ grid. |
| **l1tcl_gold_dim** | `--sweep l1tcl_gold_dim` | 2D (5×4) | Target budget × Dimensionality. |
| **l1tcl_full** | `--sweep l1tcl_full` | 2D (4×4) | Full d×s grid for paper replication. |

### Legacy Sweeps

| Sweep | Command | Description |
|-------|---------|-------------|
| **gold** | `--sweep gold` | Original target budget grid (no fair DGP). |
| **gold_option_a** | `--sweep gold_option_a` | Option A specific sweep. |
| **proxy** | `--sweep proxy` | Proxy sample size sweep. |
| **imbalance** | `--sweep imbalance` | Site imbalance sweep. |

### Example Commands

```bash
# Run the main 2D heatmap sweep (recommended first experiment)
python -m experiments.core_sweeps --sweep gold_fair_dim --n_rep 20 --n_jobs 10 \
    --output results/gold_fair_dim

# Run source site scaling experiment
python -m experiments.core_sweeps --sweep gold_fair_sources --n_rep 20 --n_jobs 10 \
    --output results/gold_fair_sources

# Run stress tests (SNR, overlap, drift)
python -m experiments.core_sweeps --sweep snr_ladder --n_rep 50 --output results/snr_stress
python -m experiments.core_sweeps --sweep overlap_ladder --n_rep 50 --output results/overlap_stress
python -m experiments.core_sweeps --sweep drift_ladder --n_rep 50 --output results/drift_stress

# Run on remote cluster with more parallelism
python -m experiments.core_sweeps --sweep gold_fair_dim --n_rep 100 --n_jobs 40 \
    --output results/gold_fair_dim_production
```

### A5 Violation Sweeps (Sensitivity Analysis)

For testing robustness when Assumption A5 (sparse linear correction) is violated. **See full documentation: [`docs/A5_VIOLATION_SWEEPS.md`](docs/A5_VIOLATION_SWEEPS.md)**

**Integrated sweep (recommended):**

```bash
# Run the 2D heatmap sweep: Sparsity × Nonlinearity
python -m experiments.core_sweeps --sweep a5_violation --n_rep 50 --output results/a5_violation
```

| Axis | Values | Meaning |
|------|--------|---------|
| Sparsity (s/p) | `{0.05, 0.20, 1.0}` | Sparse → Dense coefficients |
| Nonlinearity (λ) | `{0.0, 0.5, 1.0}` | Linear → Nonlinear correction |

**Expected outcome:**
- Strong at (0.05, 0): A5 holds
- Graceful degradation as violations increase
- Convergence toward TargetOnlyDR at (1.0, 1.0)

**Manual sweeps** (for more fine-grained control):

| Config | Varies | Tests |
|--------|--------|-------|
| `a5_sparsity` | s/p ratio | Dense vs sparse coefficients |
| `a5_decay` | Decay α | Approximate sparsity |
| `a5_dense_residual` | η ratio | Dense noise injection |
| `a5_nonlinear_additive` | λ | Smooth nonlinear violations |

### Basic Usage

```python
from src.estimator import PlaceboAnchoredDRLearner

# Initialize
model = PlaceboAnchoredDRLearner(option='A', verbose=True)

# Fit (Option A: both arms in target)
model.fit(X_source, A_source, Y_source, c_source,
          X_target, A_target, Y_target)

# Predict
tau_hat = model.predict(X_target)  # Stage-3 DR estimate
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
