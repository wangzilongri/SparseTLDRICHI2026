# Transfer Learning for Meta-analysis Under Covariate Shift

Code for the paper **"Transfer Learning for Meta-analysis Under Covariate Shift"**, accepted at IEEE ICHI 2026.

---

## Overview

This repository implements a **placebo-anchored transport framework** for estimating patient-level heterogeneous treatment effects (CATE) across heterogeneous randomized controlled trials (RCTs) under covariate shift.

The core idea is to treat source-trial outcomes as abundant but potentially miscalibrated *proxy* signals, and target-trial placebo outcomes as scarce but high-fidelity *gold* labels for baseline risk calibration. Source transfer uses `glmtrans` (ℓ₁-penalized GLM with automatic source detection); CATE estimation uses doubly robust (DR) cross-fitting.

Three estimator variants are provided:

| Estimator | Description |
|-----------|-------------|
| **Proposed** | Plug-in CATE: `glmtrans` per arm → `τ̂(x) = μ̂₁(x) − μ̂₀(x)` |
| **Proposed-CF** | Cross-fitted doubly robust CATE on top of `glmtrans` outcome models |
| **Proposed-B** | Disconnected targets (placebo-only): source detection via target placebo, source-DR CATE transported to target |

---

## Requirements

### Python

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Dependencies: `numpy`, `scipy`, `pandas`, `scikit-learn`, `matplotlib`, `seaborn`, `tqdm`.

### R and glmtrans (required for proposed methods)

The proposed methods use the [`glmtrans`](https://cran.r-project.org/package=glmtrans) R package (Tian & Feng, JASA 2023). **Requires R 4.4+.**

```bash
Rscript -e 'install.packages("glmtrans", repos="https://cloud.r-project.org")'
```

Or use the setup script (handles Python + R):

```bash
./setup.sh
source activate.sh
```

To verify the glmtrans wrapper is working:

```bash
python -m src.glmtrans_wrapper --status
```

---

## Project Structure

```
├── src/
│   ├── synthetic_data_v2_fair.py   # Fair DGP (FairSyntheticRCTGenerator)
│   ├── ihdp_data.py                # IHDP data loader
│   ├── ihdp_multisite.py           # IHDP multi-site construction (k-means)
│   ├── glmtrans_wrapper.py         # Python–R bridge for glmtrans
│   ├── estimator_fixed.py          # Proposed / Proposed-CF / Proposed-B
│   ├── transport_baselines.py      # IPW-Transport, OM-Transport, EntropyBal
│   ├── metrics.py                  # PEHE, ATE error, Spearman, regret, ECE
│   ├── benchmark_runner.py         # Monte Carlo sweep runner
│   ├── benchmark_schema.py         # Method registry, scenario definitions
│   ├── benchmark_aggregation.py    # Results aggregation and LaTeX table export
│   └── benchmark_adapters.py       # Data / method factory wrappers
│
├── experiments/
│   ├── core_sweeps.py              # Synthetic sweeps (dim, sources, A5, disconnected)
│   ├── ihdp_sweeps.py              # IHDP connected / disconnected sweeps
│   ├── run_ihdp.py                 # IHDP entry point (run + table generation)
│   ├── fair_optionb_sweeps.py      # Disconnected-regime sensitivity sweeps
│   └── sensitivity_analysis.py     # Additional robustness checks
│
├── scripts/
│   ├── generate_avg_rank_summary.py
│   └── run_ablation_report.sh
│
├── results/                        # Output directory (created at runtime)
├── requirements.txt
└── setup.sh
```

---

## Reproducing Paper Experiments

All experiments use **R = 100 Monte Carlo replicates** and are parallelized via `--n_jobs`.

### Synthetic Experiments (§4)

**Table 1 — Average rank summary across metrics:**
```bash
python -m experiments.core_sweeps --sweep gold_fair_dim --n_rep 100 --n_jobs -1 \
    --output results/dim_sweep
```

**Table 2 — Target budget × Dimensionality (PEHE):**
```bash
python -m experiments.core_sweeps --sweep gold_fair_dim --n_rep 100 --n_jobs -1 \
    --output results/dim_sweep
```

**Table 3 — Source site scaling (PEHE):**
```bash
python -m experiments.core_sweeps --sweep gold_fair_sources --n_rep 100 --n_jobs -1 \
    --output results/sources_sweep
```

**Table 4 — Sensitivity to A5 violations (PEHE):**
```bash
python -m experiments.core_sweeps --sweep a5_violation --n_rep 100 --n_jobs -1 \
    --output results/a5_sweep
```

**Table 5 — Disconnected regime (placebo-only target):**
```bash
python -m experiments.core_sweeps --sweep gold_fair_dim --n_rep 100 --n_jobs -1 \
    --output results/dim_sweep
# The m₁=0 column of the dim sweep corresponds to the disconnected regime.
```

**Run all synthetic sweeps at once:**
```bash
python -m experiments.core_sweeps --sweep all_fair --n_rep 100 --n_jobs -1 \
    --output results/fair_sweeps
```

### IHDP Semi-Synthetic Experiments (§5)

```bash
# Full run (50 IHDP realizations, connected + disconnected)
python experiments/run_ihdp.py --full --n_jobs -1

# Quick test (5 realizations)
python experiments/run_ihdp.py --quick

# Generate LaTeX tables from existing results
python experiments/run_ihdp.py --tables_only --output results/ihdp
```

---

## Methods

### Proposed Methods

| Name | Class | Notes |
|------|-------|-------|
| `Proposed` | `Glmtrans_Auto` | Plug-in CATE via glmtrans (Option A) |
| `Proposed-CF` | `Glmtrans_DR_CrossFit` | DR cross-fitted CATE (Option A) |
| `Proposed-B` | `Glmtrans_OptionB` | Disconnected target (Option B, m₁ = 0) |

### Baselines

| Name | Description |
|------|-------------|
| `TargetOnly` | DR learner on target data only (no transfer) |
| `ProxyOnly` | Pooled source outcome models, no anchoring |
| `IPW-Transport` | Inverse probability weighting transportability estimator |
| `OM-Transport` | Outcome model transport estimator |
| `EntropyBal` | Entropy balancing for covariate shift |
| `AnchorOnly` | Placebo-anchored outcome models without DR cross-fitting |

---

## Evaluation Metrics

| Metric | Description |
|--------|-------------|
| PEHE | √(mean squared error of individual CATE estimates); lower is better |
| ATE error | Absolute error of marginal ATE estimate; lower is better |
| Spearman | Rank correlation between estimated and true CATE; higher is better |
| Policy regret | Value loss of threshold policy vs. oracle; lower is better |
| ECE | Expected calibration error of CATE predictions; lower is better |

---

## Citation

> Wang, Z., Abdeen, A., & Ayer, T. (2026). Transfer Learning for Meta-analysis Under Covariate Shift. *IEEE International Conference on Health Informatics (ICHI).*

BibTeX entry will be added upon publication.
