# Sparse Transfer Learning for DR-Learner (ICHI 2026)

Implementation of the Placebo-Anchored DR-Learner for Meta-Analysis, featuring a three-stage estimator for transfer learning under covariate shift.

## Overview

This project implements:
- **Stage 1**: Flexible proxy models on abundant source data
- **Stage 2**: Sparse LASSO correction using target placebo outcomes (gold labels)
- **Stage 3**: Doubly robust CATE estimation with cross-fitting

## Setup

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   cd /Users/zilongwang/Sparse_TL_DR_ICHI2026
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # OR
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   
   *Note: If you encounter SSL certificate errors on macOS, use:*
   ```bash
   pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
   ```

4. **Verify installation**:
   ```bash
   python -c "import numpy; import pandas; import sklearn; import matplotlib; import seaborn; print('✓ All packages imported successfully')"
   ```

### Installed Packages

- **numpy** (2.4.1): Numerical computing
- **pandas** (3.0.0): Data manipulation
- **scikit-learn** (1.8.0): Machine learning algorithms
- **matplotlib** (3.10.8): Visualization
- **seaborn** (0.13.2): Statistical data visualization

## Usage

### Running the Main Script

```bash
source venv/bin/activate
python src/scratch_estimator.py
```

This will:
1. Run an ablation study comparing different estimation methods
2. Generate visualizations comparing method performance
3. Display PEHE (Precision in Estimation of Heterogeneous Effects) metrics

### Using the PlaceboAnchoredDRLearner

```python
from src.scratch_estimator import PlaceboAnchoredDRLearner, MultiSiteSimulator

# Generate or load your data
simulator = MultiSiteSimulator()
data = simulator.generate_network(disconnected=True)

# Extract source and target data
X_source, A_source, Y_source, prop_source = simulator.pool_sources(data)
X_target = data['target']['X']
A_target = data['target']['A']
Y_target = data['target']['Y']

# Fit the model
model = PlaceboAnchoredDRLearner(option='B', n_folds_dr=5)
model.fit(X_source, A_source, Y_source, 
          X_target, A_target, Y_target)

# Predict treatment effects
cate_predictions = model.predict(X_target)
```

## Quick Links

- ⭐ **[results/ablation_options/RESULTS_EXPLAINED.md](results/ablation_options/RESULTS_EXPLAINED.md)**: **NEWEST!** Option A vs B explained
- 🎯 **[docs/OPTIONS_EXPLAINED.md](docs/OPTIONS_EXPLAINED.md)**: **NEW!** What are Options A and B?
- ✅ **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)**: **START HERE** - Complete summary
- 🚀 **[docs/diagnostics/100_RUNS_RESULTS.md](docs/diagnostics/100_RUNS_RESULTS.md)**: Publication-quality 100-run results (parallel)
- 🔧 **[FIXES_APPLIED.md](FIXES_APPLIED.md)**: What was fixed and why (40% improvement!)
- 📊 **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)**: Original session summary
- 🔬 **[docs/diagnostics/](docs/diagnostics/)**: Diagnostic analysis (4,000 lines)
  - **[PROXY_ANCHOR_IDENTICAL.md](docs/diagnostics/PROXY_ANCHOR_IDENTICAL.md)**: Why Proxy ≈ Anchor?
  - **[BEFORE_AFTER_COMPARISON.md](docs/diagnostics/BEFORE_AFTER_COMPARISON.md)**: Results comparison (20 runs)
  - **[DIAGNOSTIC_REPORT.md](docs/diagnostics/DIAGNOSTIC_REPORT.md)**: Complete root cause analysis
  - **[DIAGNOSTIC_SUMMARY.md](docs/diagnostics/DIAGNOSTIC_SUMMARY.md)**: Quick reference
- 📑 **[RESULTS_INDEX.md](RESULTS_INDEX.md)**: Guide to all figures and tables
- 📁 **[docs/](docs/)**: Design and planning documents
- 🧪 **[experiments/](experiments/)**: Experiment runners
- 📈 **[results/](results/)**: All generated figures and tables

## Project Structure

```
Sparse_TL_DR_ICHI2026/
├── README.md                      # This file
├── IMPLEMENTATION_SUMMARY.md      # 📊 What we've done & next steps
├── RESULTS_INDEX.md               # 📑 Guide to all figures & tables
├── requirements.txt               # Python dependencies
├── venv/                         # Virtual environment
├── docs/                         # 📁 Design & planning documents
│   ├── DESIGN.md                # Algorithm specification
│   ├── QUICK_REFERENCE.md       # One-page summary
│   ├── ABLATION_TESTS.md        # Test plan
│   ├── REVIEWER_EXPERIMENTS.md  # Additional experiments
│   ├── GAP_ANALYSIS.md          # What's missing
│   ├── PRIORITY_CHECKLIST.md    # Action items
│   └── diagnostics/             # 🔬 Diagnostic analysis
│       ├── DIAGNOSTIC_REPORT.md     # Complete root cause analysis
│       ├── DIAGNOSTIC_SUMMARY.md    # Quick reference
│       ├── REVIEW_COMPLETE.md       # Executive summary
│       ├── COMPLETION_SUMMARY.md    # Session summary
│       └── diagnostic_analysis.py   # Diagnostic script
├── src/                          # Source code
│   ├── scratch_estimator.py     # Main implementation (✅ FIXED)
│   ├── data_generator.py        # ✅ Synthetic RCT data
│   ├── evaluation.py            # ✅ Metrics + tests
│   └── baselines.py             # ✅ Baseline methods
├── experiments/                  # 🧪 Experiment runners
│   ├── ablation_both_options.py # ⭐ NEW: Option A vs B comparison
│   ├── ablation_core_parallel.py # ✅ Parallel 100-run ablations
│   ├── ablation_core.py         # ✅ Core ablations (original)
│   └── diagnostic_analysis.py → # Symlink to docs/diagnostics/
└── results/                      # 📈 Generated outputs
    ├── ablation_options/        # ⭐ NEW: Option A vs B results
    │   ├── RESULTS_EXPLAINED.md # Detailed explanation
    │   ├── *.csv                # Summary tables
    │   └── *.png                # Comparison figures
    └── ablation_core/           # Experiment 1 results
        ├── *.csv                # 5 tables
        └── *.png                # 4 figures
```

## Documentation

All design and planning documents are in the **`docs/`** folder:

### Implementation Guides

- **[docs/DESIGN.md](docs/DESIGN.md)**: Complete algorithm specification with pseudocode
- **[docs/OPTIONS_EXPLAINED.md](docs/OPTIONS_EXPLAINED.md)**: ⭐ **NEW!** What are Option A and Option B?
- **[docs/QUICK_REFERENCE.md](docs/QUICK_REFERENCE.md)**: One-page summary

### Experimental Plans

- **[docs/ABLATION_TESTS.md](docs/ABLATION_TESTS.md)**: Original ablation test plan
- **[docs/REVIEWER_EXPERIMENTS.md](docs/REVIEWER_EXPERIMENTS.md)**: Additional experiments for reviewer
- **[docs/GAP_ANALYSIS.md](docs/GAP_ANALYSIS.md)**: Gap analysis with priorities
- **[docs/PRIORITY_CHECKLIST.md](docs/PRIORITY_CHECKLIST.md)**: Action items and timeline

### Results

- **[results/ablation_options/RESULTS_EXPLAINED.md](results/ablation_options/RESULTS_EXPLAINED.md)**: ⭐ **NEW!** Option A vs B comparison explained
- **[RESULTS_INDEX.md](RESULTS_INDEX.md)**: Complete guide mapping figures/tables to experiments
- **[results/](results/)**: All generated tables (CSV) and figures (PNG)

### Running Experiments

```bash
# Recommended: Compare Option A (connected) vs Option B (disconnected)
python experiments/ablation_both_options.py

# Parallel execution with 100 runs
python experiments/ablation_core_parallel.py

# Original ablation study
python experiments/ablation_core.py
```

## Data Schema

### Source Trials (Multiple sites pooled)
- `X_source`: Baseline covariates (n_source, n_features)
- `A_source`: Treatment assignment (1=treated, 0=placebo)
- `Y_source`: Observed outcomes
- `propensity_source`: Optional propensity scores

### Target Trial (Single site)
- `X_target`: Same feature space as source
- `A_target`: Treatment assignment (can be all zeros for disconnected setting)
- `Y_target`: Observed outcomes
- `propensity_target`: Optional propensity scores

## Deactivating the Environment

When you're done working:
```bash
deactivate
```

## Troubleshooting

### SSL Certificate Errors
If you encounter SSL errors during installation, use the `--trusted-host` flags as shown in step 3 above.

### Matplotlib Cache Warnings
These warnings are harmless and occur during first-time setup. Matplotlib will create a temporary cache directory automatically.

## Citation

If you use this code, please cite:
```
Transfer Learning for Meta-analysis Under Covariate Shift (IEEE ICHI 2026)
```
