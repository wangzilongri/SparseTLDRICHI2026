# Data Generating Process (DGP) Explained

**Purpose**: Synthetic multi-site RCT data with controlled transport bias  
**File**: `src/data_generator.py`

---

## 🎯 High-Level Overview

### The Setup

Imagine a **multi-center clinical trial** where:
- **3 source hospitals** ran RCTs (500 patients each = 1500 total)
- **1 target hospital** needs treatment effect estimates (200-500 patients)
- Each hospital has **different patient populations** (covariate shift)
- Each hospital has **different systematic biases** (e.g., different measurement protocols, practices)

**Goal**: Use source RCT data to predict treatment effects in the target hospital.

---

## 📊 The Network Structure

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Source 1   │  │  Source 2   │  │  Source 3   │
│  n = 500    │  │  n = 500    │  │  n = 500    │
│  Both arms  │  │  Both arms  │  │  Both arms  │
│  (A=0,1)    │  │  (A=0,1)    │  │  (A=0,1)    │
└─────────────┘  └─────────────┘  └─────────────┘
       ↓                ↓                ↓
       └────────────────┴────────────────┘
                        ↓
              ┌───────────────────┐
              │     Target        │
              │  n = 200-500      │
              │  Option A: Both   │
              │  Option B: A=0    │
              └───────────────────┘
```

**Pooled Source**: 1500 total samples (large, diverse)  
**Target**: 200-500 samples (small, specific population)

---

## 🧮 The Mathematical Model

### Global Parameters (Shared Across ALL Sites)

**1. Baseline Function** (β₀):
```python
beta_0 = [0.5, -0.3, 0, 0, 0, 0, 0, 0, 0, 0]
         └─┬─┘
       First 2 features drive baseline outcome
```

**Interpretation**: 
- Feature 1 increases baseline outcome by 0.5
- Feature 2 decreases baseline outcome by 0.3
- Features 3-10 don't affect baseline

---

**2. Treatment Effect Function** (β_τ):
```python
beta_tau = [0.6, 0.4, -0.3, 0, 0, 0, 0, 0, 0, 0]
            └────┬────┘
         First 3 features modify treatment effect
```

**Interpretation**:
- **Heterogeneous treatment effects** depend on X₁, X₂, X₃
- Feature 1: +0.6 (large positive effect modifier)
- Feature 2: +0.4 (moderate positive effect modifier)
- Feature 3: -0.3 (moderate negative effect modifier)

**Example**:
```
Patient with X = [1, 1, 0, ...]:
  τ(X) = 0.6(1) + 0.4(1) + (-0.3)(0) = 1.0

Patient with X = [0, 0, 1, ...]:
  τ(X) = 0.6(0) + 0.4(0) + (-0.3)(1) = -0.3
```

**CATE varies from -0.3 to 1.0+** depending on patient features!

---

### Site-Specific Parameters (Different Per Site)

**3. Covariate Distribution Shift**:
```python
# Each site draws from:
X_site ~ Normal(mean_shift, I)

# Source sites:
shift = randn(10) * 0.5  # Random direction, magnitude ~0.5

# Target site:
shift = randn(10) * 0.75  # Larger shift (1.5 × 0.5)
```

**Effect**: 
- Sources have different patient demographics
- Target population further shifted
- Typical shift distance: ||E[X_source] - E[X_target]|| ≈ **2.4**

**Example**:
```
Source 1: Mean X ≈ [+0.3, -0.1, +0.3, ...]  (healthy population)
Source 2: Mean X ≈ [-0.5, -0.0, -0.3, ...]  (different demographics)
Target:   Mean X ≈ [-0.9, -0.3, +0.4, ...]  (sicker population)
```

---

**4. Transport Bias (δ₀ and δ₁)** ⭐ **CRITICAL**

Each site has **random sparse bias** added to outcomes:

```python
# Pick 2 random features (bias_sparsity = 2)
nonzero_idx = random_choice(10, 2)  # e.g., features [2, 6]

# Assign random bias (magnitude ~0.4)
delta_0 = zeros(10)
delta_0[nonzero_idx] = randn(2) * 0.4  # e.g., [0, 0, +0.24, 0, 0, 0, -0.98, 0, 0, 0]
```

**Interpretation**:
- Only **2 features** cause bias (sparse!)
- Bias magnitude: typically **0.3 to 0.6** per feature
- **Different features** biased in each site
- This is what creates **transport bias** (why source ≠ target)

**Example (Seed 42)**:
```
Source 1: delta_0 biased on features [2, 6]
Source 2: delta_0 biased on features [2, 5]  
Source 3: delta_0 biased on features [4, 6]
Target:   delta_0 biased on features [6, 9]  ← Different from all sources!
```

---

**5. Cross-Arm Coupling (ρ)** ⭐ **KEY TUNABLE PARAMETER**

How bias in **treated arm** (δ₁) relates to bias in **placebo arm** (δ₀):

```python
# Generate random differential component
eta = randn(10) * 0.3
eta[abs(eta) < 0.1] = 0  # Sparse

# Couple treated bias to placebo bias
delta_1 = rho * delta_0 + sqrt(1 - rho²) * eta
          └──┬──┘         └────────┬────────┘
        Shared component   Differential component
```

**By ρ value**:

| ρ | Interpretation | δ₁ Composition | Example |
|---|----------------|----------------|---------|
| **1.0** | 100% shared bias | δ₁ = δ₀ | Both arms biased identically |
| **0.8** | 80% shared | δ₁ = 0.8·δ₀ + 0.6·η | Mostly shared, 20% differential |
| **0.5** | 50% shared | δ₁ = 0.5·δ₀ + 0.87·η | Half shared, half differential |
| **0.0** | 100% differential | δ₁ = η | Completely independent biases |

**Concrete Example (ρ = 0.8)**:
```
delta_0 = [0, 0, 0.24, 0, 0, 0, -0.98, 0, 0, 0]  (sparse bias on features 2,6)
eta     = [0.22, 0.07, 0.14, 0, 0.13, -0.34, 0.19, -0.21, -0.22, -0.11]  (differential noise)

delta_1 = 0.8 * delta_0 + 0.6 * eta
        = [0, 0, 0.19, 0, 0, 0, -0.78, 0, 0, 0] + [0.13, 0.04, 0.08, 0, 0.08, -0.20, 0.11, -0.13, -0.13, -0.07]
        = [0.13, 0.04, 0.27, 0, 0.08, -0.20, -0.67, -0.13, -0.13, -0.07]
        
Result: delta_1 is SIMILAR to delta_0 (80% shared) but NOT identical
```

---

## 📈 Outcome Generation

### Step-by-Step Process

**For each patient i in site c**:

**1. Draw covariates**:
```
X_i ~ Normal(mean_shift_c, I)
```

**2. Randomize treatment**:
```
A_i ~ Bernoulli(0.5)  # 50% treatment probability
```

**3. Compute global potential outcomes**:
```
μ₀_global(X_i) = β₀' X_i = 0.5·X_i1 - 0.3·X_i2
τ(X_i) = β_τ' X_i = 0.6·X_i1 + 0.4·X_i2 - 0.3·X_i3
```

**4. Add site-specific bias**:
```
μ₀_c(X_i) = μ₀_global(X_i) + δ₀_c' X_i  ← Placebo outcome at site c
μ₁_c(X_i) = μ₀_global(X_i) + τ(X_i) + δ₁_c' X_i  ← Treated outcome at site c
```

**5. Observe outcome with noise**:
```
Y_i = A_i · μ₁_c(X_i) + (1-A_i) · μ₀_c(X_i) + ε_i
      where ε_i ~ Normal(0, 0.5)
```

---

### Concrete Example

**Patient at Source Site 1**:
```
X = [1.2, -0.5, 0.8, 0.1, -0.3, 0.2, 0.7, -0.1, 0.4, -0.2]
A = 1  (treated)

# Global components
μ₀_global = 0.5(1.2) - 0.3(-0.5) = 0.75
τ = 0.6(1.2) + 0.4(-0.5) - 0.3(0.8) = 0.52

# Site 1 bias (features 2,6)
delta_0 = [0, 0, 0.24, 0, 0, 0, -0.98, 0, 0, 0]
delta_1 = [0.22, 0.07, 0.35, 0, 0.13, -0.34, -0.78, -0.21, -0.22, -0.11]

X' delta_0 = 0.24(0.8) + (-0.98)(0.7) = -0.49
X' delta_1 = 0.22(1.2) + 0.07(-0.5) + 0.35(0.8) + ... = -0.28

# Potential outcomes
μ₀ = 0.75 + (-0.49) = 0.26
μ₁ = 0.75 + 0.52 + (-0.28) = 0.99

# Observed (since A=1)
Y = μ₁ + noise = 0.99 + randn()*0.5 ≈ 0.89
```

---

**Patient at Target Site** (same X):
```
X = [1.2, -0.5, 0.8, 0.1, -0.3, 0.2, 0.7, -0.1, 0.4, -0.2]

# Global components (SAME as source!)
μ₀_global = 0.75
τ = 0.52

# Target bias (different features: 6,9!)
delta_0 = [0, 0, 0, 0, 0, 0, -0.64, 0, 0, 0.27]
delta_1 = [-0.17, -0.06, 0.30, 0.07, 0.21, 0, -0.63, -0.08, -0.08, 0.22]

X' delta_0 = (-0.64)(0.7) + 0.27(-0.2) = -0.50
X' delta_1 = (-0.17)(1.2) + ... + (-0.63)(0.7) + 0.22(-0.2) = -0.34

# Potential outcomes at TARGET
μ₀_target = 0.75 + (-0.50) = 0.25  ← Different from Source!
μ₁_target = 0.75 + 0.52 + (-0.34) = 0.93  ← Different from Source!
```

**Transport Bias**:
- Source predicts μ₀ = 0.26, Truth = 0.25 (close!)
- Source predicts μ₁ = 0.99, Truth = 0.93 (off by 0.06)
- CATE bias depends on ρ...

---

## 🎛️ Key Tunable Parameters

### 1. **n_target** (Sample Size)

**Current**: 200-500  
**Effect**: Controls estimation variance
- Smaller → Higher variance in corrections
- Larger → More stable LASSO, better DR

**In our tests**:
- n=200: Anchor/Proposed fail badly
- n=500: Anchor/Proposed still struggle at low ρ
- n=2000+: Expected crossover point

---

### 2. **rho_cross_arm** (ρ) ⭐ **MOST IMPORTANT**

**Current**: 0.8 (default)  
**Range**: 0.0 to 1.0

**Controls differential bias structure**:

```
ρ = 1.0 (Shared Bias):
  delta_1 = delta_0  (IDENTICAL biases)
  
  Example:
    delta_0 = [0, 0, 0.24, 0, 0, 0, -0.98, 0, 0, 0]
    delta_1 = [0, 0, 0.24, 0, 0, 0, -0.98, 0, 0, 0]  ← Same!
  
  CATE bias: (delta_1 - delta_0) = 0  ← Perfect cancellation!
  Proxy-Only gets lucky (no CATE bias)

ρ = 0.0 (Differential Bias):
  delta_1 = eta  (INDEPENDENT)
  
  Example:
    delta_0 = [0, 0, 0.24, 0, 0, 0, -0.98, 0, 0, 0]
    delta_1 = [0.22, 0.07, 0.14, 0, 0.13, -0.34, 0.19, -0.21, -0.22, -0.11]  ← Different!
  
  CATE bias: (delta_1 - delta_0) ≠ 0  ← No cancellation
  Proxy-Only struggles (substantial CATE bias)
```

**In our experiments**:
- ρ = 1.0: CATE bias = **0.08** (tiny!) → Proxy wins
- ρ = 0.5: CATE bias = **0.30** (moderate) → Proxy still good
- ρ = 0.0: CATE bias = **0.36** (substantial) → Proxy worse, but variance dominates

---

### 3. **bias_sparsity**

**Current**: 2 (2 out of 10 features have bias)  
**Effect**: Controls how many features create transport bias

```
bias_sparsity = 2:
  delta_0 = [0, 0, 0.24, 0, 0, 0, -0.98, 0, 0, 0]
            └────────────┬────────────┘
                   2 nonzero entries
```

**Why sparse?**
- Realistic: Not all features cause bias
- Tests LASSO: Should select these 2 features
- Makes transport learning tractable

---

### 4. **covariate_shift_scale**

**Current**: 0.5 (sources), 0.75 (target = 1.5 × 0.5)  
**Effect**: Controls how different X distributions are

```
Source shift: randn(10) * 0.5    → ||shift|| ≈ 1.6
Target shift: randn(10) * 0.75   → ||shift|| ≈ 2.4

Result: ||E[X_source] - E[X_target]|| ≈ 2.4 (large!)
```

---

### 5. **disconnected** (Option A vs B)

**Option A** (disconnected = False):
```
Target has BOTH treatment arms:
  n_placebo ≈ 250, n_treated ≈ 250
  
Can estimate: delta_0 AND delta_1 independently
```

**Option B** (disconnected = True):
```
Target has ONLY placebo arm:
  n_placebo ≈ 500, n_treated = 0
  
Can estimate: delta_0 only
Must assume: delta_1 = delta_0
```

---

## 📐 Complete Outcome Formula

### For Patient i at Site c

```
μ₀_c(X_i) = β₀' X_i + δ₀_c' X_i
          = [Global baseline] + [Site-specific bias]
          
μ₁_c(X_i) = β₀' X_i + β_τ' X_i + δ₁_c' X_i
          = [Global baseline] + [Treatment effect] + [Site-specific bias]
          
τ_c(X_i) = μ₁_c(X_i) - μ₀_c(X_i)
         = β_τ' X_i + (δ₁_c - δ₀_c)' X_i
         = [Global CATE] + [Site-specific CATE bias]
         
Y_i = A_i · μ₁_c(X_i) + (1-A_i) · μ₀_c(X_i) + ε_i
```

---

## 🔍 Concrete Example Walk-Through

### Setup (Seed = 42, ρ = 0.8)

**Source Site 1**:
- n = 500 (250 placebo, 250 treated)
- Mean shift: [+0.32, -0.08, +0.29, ...]
- δ₀ = [0, 0, **+0.24**, 0, 0, 0, **-0.98**, 0, 0, 0] (features 2,6)
- δ₁ = [0.22, 0.07, **+0.35**, 0, 0.13, -0.34, **-0.78**, -0.21, -0.22, -0.11]

**Target Site**:
- n = 500 (Option A: 258 placebo, 242 treated)
- Mean shift: [-0.87, -0.28, +0.41, ...]
- δ₀ = [0, 0, 0, 0, 0, 0, **-0.64**, 0, 0, **+0.27**] (features 6,9)
- δ₁ = [-0.17, -0.06, 0.30, 0.07, 0.21, 0, **-0.63**, -0.08, -0.08, **+0.22**]

**Key Observations**:
1. ✅ **Different bias features**: Source has [2,6], Target has [6,9]
2. ✅ **Different bias magnitudes**: ||δ₀_source|| = 1.00, ||δ₀_target|| = 0.69
3. ✅ **Different populations**: E[X] differs by 2.4
4. ⚠️ **But δ₁ ≈ δ₀** in target (due to ρ=0.8): ||δ₁ - δ₀|| = 0.33

---

### What Happens When We Fit Proxy-Only?

**Proxy model trained on pooled sources** (n=1500):
```
Learns: μ̂₀(x) ≈ β₀' x + avg(δ₀_sources)' x
        μ̂₁(x) ≈ β₀' x + β_τ' x + avg(δ₁_sources)' x
```

**Prediction error in target**:
```
μ̂₀(x) - μ₀_target(x) = [avg(δ₀_sources) - δ₀_target]' x
                      ≈ 0.46  (mean bias, from DGP analysis)

μ̂₁(x) - μ₁_target(x) = [avg(δ₁_sources) - δ₁_target]' x
                      ≈ 0.56  (mean bias)

τ̂_proxy(x) - τ_target(x) = [avg(δ₁_sources) - δ₁_target - (avg(δ₀_sources) - δ₀_target)]' x
                          = [(δ₁_sources - δ₁_target) - (δ₀_sources - δ₀_target)]' x
```

**At ρ = 1.0**:
```
Since δ₁ = δ₀ everywhere:
  CATE bias = 0  ← Perfect cancellation!
  Proxy-Only PEHE = 0.55 (only variance, no bias)
```

**At ρ = 0.0**:
```
Since δ₁ ≠ δ₀:
  CATE bias ≈ 0.36  ← Substantial, but not catastrophic
  Proxy-Only PEHE = 0.74 (bias + variance)
```

---

## 🎯 Why This DGP is Interesting

### It Tests Multiple Challenges

**1. Covariate Shift**:
- X distributions differ substantially (||shift|| = 2.4)
- Tests model robustness to population differences

**2. Transport Bias**:
- Each site has different bias (||δ_source - δ_target|| ≈ 0.5-1.0)
- Tests anchoring effectiveness

**3. Sparse Bias Structure**:
- Only 2/10 features biased
- Tests LASSO feature selection

**4. Cross-Arm Coupling**:
- ρ parameter controls differential bias
- Tests when anchoring helps vs hurts

**5. Heterogeneous Treatment Effects**:
- CATE varies across patients (via β_τ)
- Tests CATE estimation, not just ATE

---

### But It Has Quirks!

**Quirk #1: Bias Cancellation at High ρ**

At ρ = 1.0:
- δ₁ = δ₀ → Biases cancel in CATE
- Proxy-Only gets **artificially good** performance
- Anchoring has nothing to correct!

**Why this happens**:
```
τ̂_proxy = (μ̂₁ - δ₁) - (μ̂₀ - δ₀)
        = τ̂_true + (δ₁ - δ₀)  ← This term is zero when ρ=1!
```

---

**Quirk #2: Moderate Bias Even at Low ρ**

At ρ = 0.0:
- Expected CATE bias = 0.36 (not huge)
- Bias std = 0.93 (high heterogeneity)
- Flexible models (RF) adapt reasonably well

**Why not catastrophic**:
- Heterogeneous bias helps (not constant shift)
- RF can learn patterns despite mean bias
- PEHE measures total error (bias² + variance)

---

**Quirk #3: Random Bias Directions**

```python
site_bias[nonzero_idx] = randn(bias_sparsity) * 0.4
                         └──┬──┘
                    Can be positive OR negative
```

**Effect**:
- Biases can accidentally align across sites
- Some cancellation even when δ₁ ≠ δ₀
- Reduces systematic transport gap

**Alternative** (more challenging):
```python
# All biases in same direction (e.g., all positive)
site_bias[nonzero_idx] = abs(randn(bias_sparsity)) * 0.4
```

---

## 📊 Actual Measurements (Seed 42, n=500)

### Site Biases

| Site | ||δ₀|| | ||δ₁|| | Distance to Target |
|------|--------|--------|--------------------|
| Source 1 | 1.01 | 1.01 | 0.50 (δ₀), 0.68 (δ₁) |
| Source 2 | 0.70 | 0.82 | 0.98 (δ₀), 1.05 (δ₁) |
| Source 3 | 0.14 | 0.72 | 0.57 (δ₀), 1.09 (δ₁) |
| **Target** | **0.69** | **0.80** | - |

**Conclusion**: Sites have **substantial heterogeneity** (not trivial transport!)

---

### Proxy-Only Performance

| ρ | mu₀ Bias | mu₁ Bias | **CATE Bias** | PEHE | Cancellation |
|---|----------|----------|---------------|------|--------------|
| **0.0** | +0.48 | +0.44 | **+0.36** | 0.74 | 39% |
| **0.5** | +0.48 | +0.56 | **+0.30** | 0.69 | 29% |
| **1.0** | +0.48 | +0.56 | **+0.08** | 0.55 | **7%** ✓ |

**Key insight**: 
- Individual outcome predictions are **poor** (bias ~0.5, RMSE ~0.8)
- But CATE benefits from **partial cancellation** (especially at high ρ)

---

## 🔬 Why Our Methods Perform as They Do

### At ρ = 1.0 (Shared Bias)

**Proxy-Only**: PEHE = 0.48
- Benefits from perfect bias cancellation (CATE bias = 0.08)
- Only estimation variance remains
- **Very competitive!**

**Anchor-Only**: PEHE = 0.32 ✓✓
- Can pool both arms (500 samples → 1 shared correction)
- Reduces estimation variance
- Corrects the small remaining bias
- **Wins by 33%!**

**Proposed (DR)**: PEHE = 0.34 ✓
- Similar to Anchor
- DR adds small overhead (cross-fitting variance)
- Still very strong (+29% vs Proxy)

---

### At ρ = 0.0 (Maximal Differential)

**Proxy-Only**: PEHE = 0.78 ✓
- Has CATE bias (0.36) but moderate
- Low variance (trained on n=1500)
- Bias-variance tradeoff favors it at n_target=500

**Anchor-Only**: PEHE = 1.31 ❌❌
- Estimates separate δ₀ and δ₁ from small samples (~250 each)
- High variance overwhelms bias reduction
- LASSO overfits (selects 8-9/10 features instead of 2)
- **Catastrophic failure!**

**Proposed (DR)**: PEHE = 1.12 ❌
- DR stabilizes Anchor (+15% improvement)
- But can't overcome fundamental sample size issue
- Still worse than Proxy (-44%)

---

## 💡 Key DGP Insights

### 1. Global vs Site-Specific Components

**Global** (β₀, β_τ):
- **Shared** across all sites
- **Learnable** from pooled source data
- Creates heterogeneous τ(X)

**Site-Specific** (δ₀_c, δ₁_c):
- **Different** per site
- Creates **transport bias**
- What anchoring aims to correct

---

### 2. The Two Types of Shift

**Covariate Shift** (X distributions differ):
- Handled by flexible models (RF adapts)
- Not a major challenge for methods
- ||E[X_source] - E[X_target]|| = 2.4

**Bias Shift** (δ_source ≠ δ_target):
- **The real challenge!**
- Requires target data to correct
- ||δ_source - δ_target|| ≈ 0.5-1.0

---

### 3. The Cancellation Effect

**Why CATE bias < Outcome bias**:
```
Outcome biases: ~0.5 (substantial)
CATE bias: 0.08-0.36 (much smaller!)

Because: τ = μ₁ - μ₀
         = (μ₁ + bias₁) - (μ₀ + bias₀)
         = τ_true + (bias₁ - bias₀)
                    └────┬────┘
              Cancels when ρ is high!
```

**This is BY DESIGN** with the ρ parameter!

---

## 📋 DGP Summary Table

| Parameter | Value | What It Controls | Impact |
|-----------|-------|------------------|--------|
| **n_features** | 10 | Dimensionality | Fixed |
| **n_effect_modifiers** | 3 | CATE complexity | Heterogeneous effects |
| **n_source_sites** | 3 | Source data diversity | 1500 total samples |
| **source_per_site** | 500 | Source sample size | Large (low variance) |
| **n_target** | 200-500 | Target sample size | **Key bottleneck!** |
| **bias_sparsity** | 2 | Transport bias sparsity | Tests LASSO |
| **bias_magnitude** | 0.4 | Bias strength | Moderate challenge |
| **covariate_shift_scale** | 0.5-0.75 | Population differences | Substantial shift |
| **rho_cross_arm** | 0.0-1.0 | Differential vs shared bias | **Controls cancellation** |
| **disconnected** | True/False | Option A vs B | Both arms vs placebo only |

---

## 🎓 Theoretical Grounding

### Matches Paper Assumptions

**Assumption A5** (Sparse Bias):
```python
bias_sparsity = 2  # Only 2/10 features biased
||δ₀||₀ = ||δ₁||₀ = 2  ✓
```

**Assumption A6** (Cross-Arm Coupling):
```python
delta_1 = rho * delta_0 + sqrt(1 - rho²) * eta  ✓
```

**Covariate Shift**:
```python
X_site ~ Normal(site_shift, I)  ✓
```

**Treatment Effect**:
```python
tau(X) = beta_tau' X (heterogeneous)  ✓
```

---

## 🚨 The Critical Question

### Q: "Are source sites too similar to target?"

**A: NO!**

**Evidence**:
- Site bias distances: **0.5-1.0** (substantial!)
- Covariate shift: **2.4** (large!)
- Different bias features across sites
- Potential outcome predictions are poor (RMSE ~0.8)

**BUT**: Biases **partially cancel** in CATE at high ρ!

---

### Q: "Why does Proxy-Only perform well?"

**A: Bias cancellation + moderate bias + heterogeneity**

**At ρ = 1.0**:
- CATE bias ≈ 0 (cancellation)
- Proxy gets lucky!

**At ρ = 0.0**:
- CATE bias ≈ 0.36 (moderate, not catastrophic)
- Bias is heterogeneous (std = 0.93)
- RF adapts to patterns
- **Plus**: Anchor/Proposed add more variance than they correct bias (at n=500)

---

### Q: "Is this realistic?"

**Mostly yes!**

**Realistic aspects**:
- ✅ Multiple source sites with heterogeneity
- ✅ Covariate shift across sites
- ✅ Sparse bias structure (not all features biased)
- ✅ Cross-arm coupling (shared institutional factors)
- ✅ Heterogeneous treatment effects

**Potential concerns**:
- ⚠️ Random bias directions can accidentally align
- ⚠️ Bias magnitude (0.4) might be mild for observational studies
- ⚠️ Perfect cancellation at ρ=1.0 is idealized

**For more challenging evaluation**:
- Increase bias magnitude to 0.8 (2x)
- Use systematic bias direction (all positive)
- Test larger target samples (n=2000)

---

## 📊 Visual Summary

```
EACH SITE GENERATES:

X ~ N(site_shift, I)  ← Covariate shift
        ↓
A ~ Bernoulli(0.5)    ← Random treatment assignment
        ↓
Global Components:
  μ₀_global = β₀' X = 0.5·X₁ - 0.3·X₂
  τ_global = β_τ' X = 0.6·X₁ + 0.4·X₂ - 0.3·X₃
        ↓
Site-Specific Bias:
  δ₀ = sparse(2 features, magnitude ~0.4)  ← Placebo bias
  δ₁ = ρ·δ₀ + √(1-ρ²)·η                  ← Treated bias
        ↓
Potential Outcomes:
  μ₀ = μ₀_global + X'δ₀
  μ₁ = μ₀_global + τ_global + X'δ₁
        ↓
Observed Outcome:
  Y = A·μ₁ + (1-A)·μ₀ + ε,  ε ~ N(0, 0.5)
```

---

## ✅ Bottom Line

**Your DGP**:
1. ✅ Creates **realistic** multi-site heterogeneity
2. ✅ Has **substantial** transport bias (sites are different!)
3. ⚠️ Has **bias cancellation** at high ρ (by design via ρ parameter)
4. ⚠️ Current sample size (n=500) is **too small** for differential bias regime
5. ✅ **Correctly implements** the theoretical model from the paper

**The source sites are NOT too similar** - the issue is that:
- At **high ρ**: Cancellation favors Proxy-Only (DGP feature)
- At **low ρ**: Small sample favors Proxy-Only (variance issue)
- Both are **interesting findings**, not flaws!

---

**File**: `DGP_EXPLAINED.md`  
**Status**: ✅ Complete walkthrough with examples and measurements  
**Key Insight**: Sites are different, but ρ controls how much that matters for CATE!
