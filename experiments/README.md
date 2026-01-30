# Experiments: Placebo-Anchored DR-Learner

Implementation of experiments from: *Transfer Learning for Meta-analysis Under Covariate Shift*

---

## Quick Start

```bash
# Activate environment
source venv/bin/activate

# Test all estimators (quick)
python experiments/test_estimators.py

# Run ablation study (20 runs, ~2-3 minutes)
python experiments/ablation_study.py
```

---

## Experiments

### 1. `test_estimators.py` - Quick Test

**Purpose**: Verify all four methods work correctly

**What it does**:
- Generates single synthetic dataset
- Fits all four methods
- Compares PEHE and ATE error
- Takes ~2 seconds

**Output**:
```
Method          PEHE    ATE Error
────────────────────────────────────
No-Transfer    0.9349     0.4129
Proxy-Only     0.4589     0.1102
Anchor-Only    0.4117     0.0026
Proposed       0.5068     0.0279
```

---

### 2. `ablation_study.py` - Full Ablation

**Purpose**: Reproduce Table from paper with statistical reliability

**What it does**:
- Runs 20 Monte Carlo iterations
- Generates synthetic multi-site RCT data each run
- Fits all four methods
- Aggregates mean ± std for all metrics
- Creates visualization plots

**Parameters** (in script):
```python
n_source_sites = 3          # Number of source trials
n_target = 200              # Target sample size
n_source_per_site = 500     # Samples per source
covariate_shift_scale = 1.0 # Strength of population shift
```

**Output**:
- Console: Aggregate statistics
- File: `results/ablation/ablation_comparison.png`

**Runtime**: ~2-3 minutes for 20 runs

---

## Implemented Methods

### 1. No-Transfer Baseline

**File**: `src/ablations.py::NoTransferBaseline`

**What it does**:
- Uses only target placebo data
- Cannot extrapolate to treated arm
- Returns constant CATE = 0

**Tests absence of**: Proxy information from source trials

---

### 2. Proxy-Only Baseline

**File**: `src/ablations.py::ProxyOnlyBaseline`

**What it does**:
- Fits models on pooled source data
- Predicts directly on target
- No calibration using target placebo

**Tests absence of**: Placebo anchoring

---

### 3. Anchor-Only Baseline

**File**: `src/ablations.py::AnchorOnlyBaseline`

**What it does**:
- Stage 1: Proxy models on sources
- Stage 2: Sparse corrections using target placebo
- Returns plug-in CATE (no Stage 3)

**Tests absence of**: Doubly robust orthogonalization

---

### 4. Proposed Method (Full)

**File**: `src/estimator.py::PlaceboAnchoredDRLearner`

**What it does**:
- Stage 1: Proxy models on sources
- Stage 2: Sparse corrections using target placebo
- Stage 3: DR CATE regression with cross-fitting

**Has all components**: Proxy + Anchoring + DR

---

## Evaluation Metrics

**From paper Section 5.3**:

1. **PEHE** (Precision in Estimation of Heterogeneous Effects)
   - sqrt(E[(τ(x) - τ̂(x))²])
   - Lower is better
   - Measures individual-level CATE accuracy

2. **ATE Error**
   - |E[τ(x)] - E[τ̂(x)]|
   - Lower is better
   - Measures population-level accuracy

3. **Calibration RMSE** (μ₀ and μ₁)
   - sqrt(E[(μ(x) - μ̂(x))²])
   - Lower is better
   - Tests baseline risk calibration

---

## Synthetic Data

**Based on paper Section 5.2**:

**Setup**:
- p = 5 covariates
- 3 relevant effect modifiers
- 2 nuisance covariates
- Multiple source sites (default: 3)
- One target site

**Ground truth**:
```
μ₀(x) = β₀ᵀx                    (baseline, all features)
τ(x) = β_τᵀx[:3]                (treatment effect, modifiers only)
Y = μ₀(X) + A·τ(X) + ε          (ε ~ N(0, 0.5²))
```

**Covariate shift**:
- Each site c: X ~ N(μ_c, I)
- μ_c ~ N(0, σ_shift²)
- Target has larger shift (1.5× scale)

**Treatment assignment**:
- Randomized: P(A=1|X) = 0.5
- Propensity known by design (RCT)

---

## Expected Results

**Pattern from paper**:

| Metric | No-Transfer | Proxy-Only | Anchor-Only | **Proposed** |
|--------|-------------|------------|-------------|--------------|
| PEHE | Worst | Better | Better | **Best** |
| ATE Error | Worst | Better | **Best** | Good |
| μ₀ RMSE | N/A | High | **Low** | **Low** |
| μ₁ RMSE | N/A | High | **Low** | **Low** |

**Key findings** (from paper):
1. **No-Transfer** cannot capture heterogeneity (constant CATE)
2. **Proxy-Only** improves but has calibration bias
3. **Anchor-Only** achieves best ATE (direct calibration)
4. **Proposed** balances PEHE and calibration via DR

---

## Customization

### Change Sample Sizes

Edit in `ablation_study.py`:
```python
results = run_multiple_experiments(
    n_runs=20,
    n_source_sites=3,
    n_target=200,        # ← Change this
    n_source_per_site=500  # ← Or this
)
```

### Change Models

Edit in `src/estimator.py` or `src/ablations.py`:
```python
PlaceboAnchoredDRLearner(
    proxy_model=RandomForestRegressor(...),      # ← Replace
    correction_model=LassoCV(...),               # ← Replace
    cate_model=RandomForestRegressor(...),       # ← Replace
)
```

### Change Covariate Shift

Edit in `ablation_study.py`:
```python
results = run_single_experiment(
    covariate_shift_scale=1.0  # ← Increase for more shift
)
```

---

## Troubleshooting

### "No samples with A=0 in source"
- Check that source data includes both treatment arms
- Verify randomization probability is not 0 or 1

### "Insufficient treated samples"
- Option A needs treated outcomes in target
- Will fallback to Option B automatically
- Increase `n_target` if needed

### Poor performance
- Try more Monte Carlo runs (n_runs=50)
- Increase sample sizes
- Tune model hyperparameters
- Check covariate shift isn't too extreme

---

## File Structure

```
experiments/
├── README.md                  # This file
├── test_estimators.py         # Quick test
└── ablation_study.py          # Full ablation

src/
├── estimator.py              # Proposed method
├── ablations.py              # Baseline methods
├── synthetic_data.py         # Data generator
└── metrics.py                # Evaluation

results/
└── ablation/                 # Output directory
    └── ablation_comparison.png
```

---

## References

**Paper**: *Transfer Learning for Meta-analysis Under Covariate Shift*  
**Section 5**: Experiments  
**Table**: Ablation source of benefit  
**Figures**: PEHE, ATE, calibration plots

---

**Status**: ✅ All experiments implemented and tested!
