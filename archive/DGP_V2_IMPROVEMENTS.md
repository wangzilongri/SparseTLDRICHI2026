# DGP v2: Improved Synthetic Data Generator

**Date**: January 30, 2026  
**Status**: ✅ Validated and working

---

## 🎯 Summary of Improvements

The improved DGP (v2) **properly implements Assumptions A5 and A6** from the paper, making it a faithful testbed for the three-stage estimator.

### Key Improvements

| # | Improvement | Why It Matters |
|---|-------------|----------------|
| 1 | **Proxy + Deviation Decomposition** | Matches paper's decomposition |
| 2 | **Cross-Arm Transfer (A6)** | Tests Option B / Step B properly |
| 3 | **Sparse Deviations (A5)** | Validates LASSO corrections |
| 4 | **Controllable Nontransfer** | Degradation knob for robustness |
| 5 | **Disconnected Target Support** | Tests Option B realistically |
| 6 | **Proper RNG** | Reproducible experiments |
| 7 | **Diagnostic Methods** | Verify M* is learnable |

---

## 📐 Mathematical Structure

### DGP Formula

```
μ_{a,c}(x) = x^T b_a + x^T β_{a,c} + r_{a,c}(x)
            └─proxy─┘  └─deviation─┘  └misspec┘

where:
  • b_a: Shared proxy coefficients (learnable from sources)
  • β_{a,c}: Site-specific deviations (sparse, A5)
  • β_{1,c} = M* β_{0,c} + ν_c  (cross-arm transfer, A6)
  • r_{a,c}(x): Optional misspecification

Outcomes:
  Y = μ_{0,c}(X) + A × τ_c(X) + ε
  where τ_c(X) = μ_{1,c}(X) - μ_{0,c}(X)
```

---

## 🔍 What Was Wrong with V1

### ❌ Problem 1: No A5 Decomposition

**V1**:
```python
# Single global coefficients
mu0 = X @ beta_0
tau = X @ beta_tau
Y = mu0 + A * tau + noise
```

**Issue**: No separation between proxy (shared) and site-specific deviations.

**V2**:
```python
# Explicit decomposition
mu_{0,c} = X @ b0_proxy + X @ beta0_c
mu_{1,c} = X @ b1_proxy + X @ beta1_c
```

---

### ❌ Problem 2: No A6 Cross-Arm Coupling

**V1**:
```python
# Independent corrections
beta0_c = random_sparse_vector()
beta1_c = random_sparse_vector()  # Unrelated!
```

**Issue**: Option B / Step B has nothing to learn!

**V2**:
```python
# Low-rank transfer operator
M_star = U @ V.T  (rank r)
beta1_c = M_star @ beta0_c + nu_c  # A6 structure!
```

---

### ❌ Problem 3: Nuisance Features Confound

**V1**: All features matter through baseline (no true sparse support).

**V2**: Sparse corrections with explicit support (2/5 features).

---

### ❌ Problem 4: No Degradation Control

**V1**: No knob to vary cross-arm validity.

**V2**: Tune `nontransfer_scale_target` to degrade Option B performance.

---

## ✅ V2 Validation Results

### Test 1: Basic Generation ✓

```
Source: 1500 samples from 3 sites
  Placebo: 763, Treated: 737

Target: 200 samples
  Placebo: 100, Treated: 100
```

---

### Test 2: Decomposition ✓

```
Placebo decomposition error: 0.000000
Treated decomposition error: 0.000000

Proxy coefficients:
  b0_proxy: [ 0.152, -0.520,  0.375,  0.470, -0.976]
  b1_proxy: [-0.651,  0.064, -0.158, -0.008, -0.427]
```

✅ **mu = proxy + deviation** holds exactly

---

### Test 3: Cross-Arm Transfer (A6) ✓

```
Transfer operator M*:
  ||M*||_F = 2.7157
  rank(M*) = 1

Verifying β₁ = M*β₀ + ν for sources:
  Source 1 error: 0.00e+00 ✓
  Source 2 error: 0.00e+00 ✓
  Source 3 error: 0.00e+00 ✓
```

✅ **A6 structure** holds perfectly

---

### Test 4: Sparsity (A5) ✓

```
Expected sparsity: 2/5

Site       Sparsity    Support
────────────────────────────────
Target     2/5         [0, 3]
Source 1   2/5         [1, 2]
Source 2   2/5         [1, 3]
Source 3   2/5         [3, 4]
```

✅ **Sparse deviations** as designed

---

### Test 5: Nontransfer Magnitude ✓

```
Expected scales:
  Source: 0.05
  Target: 0.30

Site       ||ν||      Expected    Ratio
─────────────────────────────────────────
Target     0.726      0.671       1.08
Source 1   0.057      0.112       0.51
Source 2   0.131      0.112       1.17
Source 3   0.101      0.112       0.90

Target vs Source: 7.55x larger! ✓
```

✅ **Controllable degradation** working

---

### Test 6: Disconnected Target ✓

```
Target treatment distribution:
  Placebo: 200
  Treated: 0   ← Disconnected!

Ground truth still available:
  tau_true: (200,)   ← For evaluation
  mu1_true: (200,)   ← Counterfactual
```

✅ **Option B scenario** supported

---

### Test 7: Nontransfer Sweep ✓

```
Scale      ||ν_target||   Mean |τ|
────────────────────────────────────
0.00       0.000          1.737
0.10       0.242          1.930
0.30       0.726          2.370  ← Default
0.50       1.211          2.860
0.80       1.937          3.628
```

✅ **Smooth degradation** as ν increases

---

## 🎛️ Configuration Knobs

### Basic Dimensions

```python
config = SyntheticRCTConfig(
    n_features=5,
    n_source_sites=3,
    n_target=200,
    n_source_per_site=500,
    treatment_prob=0.5,
    noise_std=0.5,
)
```

### Covariate Shift

```python
covariate_shift_scale=1.0,         # Source shift magnitude
target_shift_multiplier=1.5,       # Target has more shift
```

### A5: Sparse Deviations

```python
dev_sparsity=2,                    # Nonzeros in β_{0,c}
dev_scale=0.4,                     # Magnitude of deviations
```

### A6: Transfer Operator

```python
transfer_rank=1,                   # rank(M*)
transfer_strength=1.0,             # Scales M*
nontransfer_scale_source=0.05,     # Small ν for sources
nontransfer_scale_target=0.3,      # Large ν for target (knob!)
```

### Misspecification (Stress Test)

```python
misspec_scale=0.0,                 # Set >0 to add r_{a,c}(x)
misspec_nonlinear=False,           # Linear vs nonlinear
```

### Disconnected Target

```python
target_treated_frac=None,          # None = RCT (50/50)
                                    # 0.0 = fully disconnected
```

---

## 📖 Usage Examples

### Example 1: Standard RCT

```python
from src.synthetic_data_v2 import generate_synthetic_rct

source, target, gen = generate_synthetic_rct(
    n_source_sites=3,
    n_target=200,
    random_state=42
)

print(f"Source: {source['X'].shape}")
print(f"Target: {target['X'].shape}")
print(f"Mean CATE: {np.mean(target['tau_true']):.4f}")
```

---

### Example 2: Disconnected Target (Option B)

```python
from src.synthetic_data_v2 import generate_disconnected_target

source, target, gen = generate_disconnected_target(
    n_target=200,
    nontransfer_scale_target=0.5,  # Harder problem
    random_state=42
)

print(f"Target placebo: {np.sum(target['A'] == 0)}")
print(f"Target treated: {np.sum(target['A'] == 1)}")  # = 0!
print(f"Still have tau_true for evaluation")
```

---

### Example 3: Sweep Nontransfer (Degradation)

```python
from src.synthetic_data_v2 import sweep_nontransfer

datasets = sweep_nontransfer(
    nontransfer_scales=[0.0, 0.1, 0.3, 0.5, 0.8],
    n_target=200,
    random_state=42
)

for scale, (source, target, gen) in zip(scales, datasets):
    # Test estimator performance as ν increases
    ...
```

---

### Example 4: Get Diagnostics

```python
source, target, gen = generate_synthetic_rct()

diag = gen.get_diagnostics()

print(f"M* norm: {diag['M_star_norm']:.4f}")
print(f"M* rank: {diag['M_star_rank']}")
print(f"Target sparsity: {diag['target_sparsity']}/5")
print(f"Target ||ν||: {diag['target_nu_norm']:.4f}")

# Verify A6 holds
for c in range(1, 4):
    print(f"Source {c} A6 error: {diag[f'source_{c}_A6_error']:.2e}")
```

---

## 🧪 Why This Tests the Estimator Properly

### Stage 1: Proxy Models

**What it estimates**: μ̂_a^proxy(x) ≈ x^T b_a

**V2 advantage**: Explicit shared coefficients b_a across sources.

---

### Stage 2: Sparse Corrections

**What it estimates**: δ̂_{a,c}(x) = x^T β̂_{a,c}

**V2 advantage**:
- True β_{a,c} is sparse (A5) → LASSO should work well
- Support varies by site → tests adaptivity

---

### Stage 3 / Step B: Cross-Arm Transfer

**What it estimates**: M̂ such that β_{1,c} ≈ M̂ β_{0,c}

**V2 advantage**:
- True M* exists with known rank → recoverable!
- ν_c controls how well M̂ works → tunable degradation
- Can verify: ||M̂ - M*||_F

---

## 📊 Recommended Experiments

### Experiment 1: Verify Step B Recovery

```python
# Generate data
source, target, gen = generate_synthetic_rct(
    transfer_rank=1,
    nontransfer_scale_target=0.1,  # Easy case
    random_state=42
)

# Fit estimator with Option B
model_b = PlaceboAnchoredDRLearner(option='B')
model_b.fit(...)

# Get learned M
M_hat = model_b.M_hat_

# Compare to true M*
M_star = gen.M_star
recovery_error = np.linalg.norm(M_hat - M_star, 'fro')

print(f"||M̂ - M*||_F: {recovery_error:.4f}")
```

---

### Experiment 2: Degradation Sweep

```python
scales = [0.0, 0.1, 0.2, 0.4, 0.8]
results = {'Proposed (A)': [], 'Proposed (B)': []}

for scale in scales:
    source, target, gen = generate_synthetic_rct(
        nontransfer_scale_target=scale
    )
    
    # Fit both options
    model_a = PlaceboAnchoredDRLearner(option='A')
    model_b = PlaceboAnchoredDRLearner(option='B')
    
    # ... fit and evaluate ...
    
    results['Proposed (A)'].append(pehe_a)
    results['Proposed (B)'].append(pehe_b)

# Plot PEHE vs nontransfer scale
plt.plot(scales, results['Proposed (A)'], label='Option A')
plt.plot(scales, results['Proposed (B)'], label='Option B')
plt.xlabel('Nontransfer scale')
plt.ylabel('PEHE')
plt.legend()
```

**Expected**: Option B degrades as ν increases.

---

### Experiment 3: Disconnected Target

```python
# Generate disconnected target
source, target, gen = generate_disconnected_target(
    nontransfer_scale_target=0.3
)

# Option A should fail (no treated data)
# Option B should work (via Step B)

model_b = PlaceboAnchoredDRLearner(option='B')
model_b.fit(source, target)

tau_pred = model_b.predict(target['X'])
pehe = np.sqrt(np.mean((target['tau_true'] - tau_pred)**2))

print(f"Option B on disconnected target: PEHE = {pehe:.4f}")
```

---

### Experiment 4: Varying Transfer Rank

```python
ranks = [1, 2, 3, 4, 5]
recovery_errors = []

for r in ranks:
    source, target, gen = generate_synthetic_rct(
        transfer_rank=r,
        random_state=42
    )
    
    # Fit Step B
    # ... estimate M̂ ...
    
    # Compare to true M*
    error = np.linalg.norm(M_hat - gen.M_star, 'fro')
    recovery_errors.append(error)

plt.plot(ranks, recovery_errors)
plt.xlabel('True rank(M*)')
plt.ylabel('||M̂ - M*||_F')
plt.title('M* Recovery vs Rank')
```

---

## 🎨 Visualizations

### Structure Diagnostics

Run validation to see:

```bash
python experiments/validate_dgp_v2.py
```

Outputs:
- M* matrix (5×5 with rank-1 structure)
- β₀ sparsity patterns (different support per site)
- β₁ computed via A6
- ν magnitude comparison
- A6 verification (reconstruction errors < 1e-10)

---

## 📁 Files

```
src/
├── synthetic_data_v2.py      ← Improved DGP
└── synthetic_data.py         ← Original (for comparison)

experiments/
└── validate_dgp_v2.py        ← Validation tests
```

---

## 🔬 Theory-Code Alignment

### Paper Assumption A5

> "The site-specific deviation functions δ_{a,c} belong to a low-complexity class D (e.g., sparse linear)."

**V2 Implementation**:
```python
beta0_c = np.zeros(p)
support = random_choice(p, size=sparsity)
beta0_c[support] = random_normal(scale)
```

✅ **Sparse linear** as specified

---

### Paper Assumption A6

> "Cross-arm transfer: β_{1,c} = M*·β_{0,c} + ν_c, where M* has rank ≤ r << p."

**V2 Implementation**:
```python
U = random_normal(p, r)
V = random_normal(p, r)
M_star = U @ V.T  # rank r

beta1_c = M_star @ beta0_c + nu_c
```

✅ **Low-rank transfer** as specified

---

### Paper Step B

> "Estimate M̂^(r) by regressing β̂_{1,c} on β̂_{0,c} across source sites c."

**Can now validate**:
```python
# True M* available in gen.M_star
# Estimator's M̂ available in model.M_hat_

# Compare!
np.linalg.norm(M_hat - gen.M_star, 'fro')
```

✅ **Validation possible**

---

## 🎯 Key Takeaways

### For Option A (Separate Corrections)

With V2, Option A properly tests:
- Sparse β₀ estimation (A5)
- Separate β₁ estimation from limited treated data
- DR robustness with correctly structured deviations

---

### For Option B (Operator Transfer)

With V2, Option B properly tests:
- Learning M̂ from sources (actual A6 structure!)
- Applying M̂ to target β̂₀
- Degradation via ||ν₀|| (tunable knob)

**V1 couldn't test this** because β₁ was independent of β₀!

---

### For Step B Validation

With V2, you can:
- Check if M̂ ≈ M* (recovery error)
- Vary rank(M*) to test robustness
- Increase ||ν|| to see degradation
- Verify Step B helps in disconnected targets

---

## ✅ Status

**Implementation**: ✅ Complete  
**Validation**: ✅ All tests passing  
**Theory Alignment**: ✅ A5 and A6 verified  
**Diagnostics**: ✅ M*, β, ν available  

---

## 📖 Next Steps

### 1. Update Existing Experiments

Replace `synthetic_data.py` imports with `synthetic_data_v2.py`:

```python
# Old
from src.synthetic_data import generate_synthetic_rct

# New
from src.synthetic_data_v2 import generate_synthetic_rct
```

API is compatible!

---

### 2. Run New Diagnostics

```python
# Check M* recovery
source, target, gen = generate_synthetic_rct()
model_b = PlaceboAnchoredDRLearner(option='B')
model_b.fit(...)

print(f"True M* norm: {gen.get_diagnostics()['M_star_norm']}")
print(f"Learned M̂ norm: {np.linalg.norm(model_b.M_hat_, 'fro')}")
```

---

### 3. Degradation Experiments

```python
# Sweep nontransfer to find where Option B fails
datasets = sweep_nontransfer([0.0, 0.1, 0.3, 0.5, 0.8])

for scale, (source, target, gen) in zip(scales, datasets):
    # Compare Option A vs Option B
    # Plot PEHE curves
```

---

## 📚 References

- **Paper Section 3.1**: Stage 2 decomposition and A5/A6
- **Appendix B**: Detailed assumptions
- **Response Letter**: Discusses nontransfer component ν

---

**Summary**: ✅ **V2 DGP IS READY FOR PAPER EXPERIMENTS!**

The improved generator properly implements the paper's theoretical framework, enabling rigorous testing of all three stages and both options.
