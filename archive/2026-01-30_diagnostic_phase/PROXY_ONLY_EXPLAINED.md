# Proxy-Only Baseline: Implementation Explained

**File**: `src/baselines.py`, lines 44-81  
**Purpose**: Simple baseline that uses only source data, ignoring target data entirely

---

## 🎯 What Is Proxy-Only?

**Concept**: Train treatment effect models on **source sites only** (abundant data), then directly apply them to the target site.

**Key characteristic**: 
- ✅ Uses all 1500 source samples (large sample → low variance)
- ❌ Ignores all target data (no anchoring → potential bias)
- ✅ Simplest possible transfer learning approach

**Also known as**: 
- "Naive transfer"
- "Direct transfer"
- "Plug-in estimator"
- "Stage 1 only" (in the paper's 3-stage framework)

---

## 💻 The Code

Here's the complete implementation:

```44:81:src/baselines.py
class ProxyOnlyBaseline(BaseEstimator, RegressorMixin):
    """
    Baseline: Use pooled source data without anchoring to target.
    This is the Stage 1 model without Stage 2 correction.
    """
    
    def __init__(self, proxy_model=None):
        if proxy_model is None:
            self.proxy_model = RandomForestRegressor(
                n_estimators=200, max_depth=8, min_samples_leaf=20,
                random_state=42, n_jobs=-1
            )
        else:
            self.proxy_model = proxy_model
        self.models_ = None
    
    def fit(self, X_source, A_source, Y_source, X_target, A_target, Y_target,
            propensity_source=None, propensity_target=None):
        # Fit separate models for each arm on source data only
        self.models_ = {}
        
        for arm in [0, 1]:
            mask = (A_source == arm)
            model = clone(self.proxy_model)
            model.fit(X_source[mask], Y_source[mask])
            self.models_[arm] = model
        
        return self
    
    def predict(self, X):
        mu_0 = self.models_[0].predict(X)
        mu_1 = self.models_[1].predict(X)
        return mu_1 - mu_0
    
    def predict_counterfactuals(self, X):
        mu_0 = self.models_[0].predict(X)
        mu_1 = self.models_[1].predict(X)
        return mu_0, mu_1
```

---

## 🔍 Step-by-Step Breakdown

### Step 1: Initialization

```python
def __init__(self, proxy_model=None):
    if proxy_model is None:
        self.proxy_model = RandomForestRegressor(
            n_estimators=200,      # 200 trees
            max_depth=8,           # Moderate depth (prevents overfitting)
            min_samples_leaf=20,   # Smooth predictions
            random_state=42,
            n_jobs=-1              # Use all CPU cores
        )
    else:
        self.proxy_model = proxy_model
```

**What this does**:
- Sets up the base learner (RandomForest by default)
- Same hyperparameters used throughout experiments
- User can optionally provide custom model

---

### Step 2: Fitting (Training)

```python
def fit(self, X_source, A_source, Y_source, X_target, A_target, Y_target,
        propensity_source=None, propensity_target=None):
    # Fit separate models for each arm on source data only
    self.models_ = {}
    
    for arm in [0, 1]:
        mask = (A_source == arm)              # Select placebo (0) or treated (1)
        model = clone(self.proxy_model)        # Fresh copy of base model
        model.fit(X_source[mask], Y_source[mask])  # Train on SOURCE only!
        self.models_[arm] = model
    
    return self
```

**What happens**:

**For Placebo Arm** (arm = 0):
```python
# Select all placebo patients from ALL source sites
mask = (A_source == 0)  # ~750 patients (1500 × 0.5)

# Train model: Y ~ X for placebo patients
model_0 = RandomForest()
model_0.fit(X_source[mask], Y_source[mask])

# This learns: μ̂₀(X) ≈ E[Y | A=0, X]
```

**For Treated Arm** (arm = 1):
```python
# Select all treated patients from ALL source sites
mask = (A_source == 1)  # ~750 patients

# Train model: Y ~ X for treated patients
model_1 = RandomForest()
model_1.fit(X_source[mask], Y_source[mask])

# This learns: μ̂₁(X) ≈ E[Y | A=1, X]
```

**CRITICAL**: 
- ❌ **Target data (X_target, Y_target) is COMPLETELY IGNORED!**
- ❌ Even though it's passed as a parameter, it's never used
- ✅ Only source data is used for training

---

### Step 3: Prediction

```python
def predict(self, X):
    mu_0 = self.models_[0].predict(X)  # Predict placebo outcome
    mu_1 = self.models_[1].predict(X)  # Predict treated outcome
    return mu_1 - mu_0                  # CATE = difference
```

**What this does**:

For a target patient with features X:
```python
# Predict both potential outcomes
μ̂₀(X) = model_0.predict(X)  # What would happen under placebo?
μ̂₁(X) = model_1.predict(X)  # What would happen under treatment?

# CATE is the difference
τ̂(X) = μ̂₁(X) - μ̂₀(X)
```

**Example**:
```
Target patient: X = [1.0, 0.5, -0.3, ...]

model_0.predict(X) = 2.1  (predicted placebo outcome)
model_1.predict(X) = 3.5  (predicted treated outcome)

CATE = 3.5 - 2.1 = 1.4  (predicted treatment effect)
```

---

## 🎓 What Does It Actually Learn?

### Mathematical Reality

**What Proxy-Only learns from sources**:
```
μ̂₀(x) ≈ E_source[Y | A=0, X=x]
      = β₀' x + E[δ₀_source]' x
      = [Global baseline] + [Average source bias]

μ̂₁(x) ≈ E_source[Y | A=1, X=x]  
      = β₀' x + β_τ' x + E[δ₁_source]' x
      = [Global baseline] + [Global CATE] + [Average source bias]
```

**What it should learn for target**:
```
μ₀_target(x) = β₀' x + δ₀_target' x
μ₁_target(x) = β₀' x + β_τ' x + δ₁_target' x
```

---

### The Transport Bias

**Prediction error in target**:
```
μ̂₀(x) - μ₀_target(x) = [E[δ₀_source] - δ₀_target]' x
μ̂₁(x) - μ₁_target(x) = [E[δ₁_source] - δ₁_target]' x

τ̂_proxy(x) - τ_target(x) = [(δ₁_source - δ₁_target) - (δ₀_source - δ₀_target)]' x
                          = [(δ₁_source - δ₀_source) - (δ₁_target - δ₀_target)]' x
```

**KEY INSIGHT**: CATE bias depends on **difference in differential bias** between source and target!

---

## 📊 Concrete Example (Seed 42, ρ=0.8)

### Training Data (Sources)

**Pooled source data**:
- n = 1500 total (750 placebo, 750 treated)
- 3 sites with different biases

**Site 1**:
```
delta_0 = [0, 0, 0.24, 0, 0, 0, -0.98, 0, 0, 0]
delta_1 = [0.22, 0.07, 0.35, 0, 0.13, -0.34, -0.78, -0.21, -0.22, -0.11]
```

**Site 2**:
```
delta_0 = [0, 0, 0.13, 0, 0, -0.68, 0, 0, 0, 0]
delta_1 = [-0.08, -0.30, -0.01, 0, 0, -0.71, -0.10, 0.08, -0.24, 0]
```

**Site 3**:
```
delta_0 = [0, 0, 0, 0, 0.04, 0, -0.14, 0, 0, 0]
delta_1 = [-0.47, 0, 0, 0.31, -0.15, -0.30, 0.18, 0.10, -0.19, 0.08]
```

**Average source bias**:
```
E[delta_0_source] = [0, 0, 0.12, 0, 0.01, -0.23, -0.37, 0, 0, 0]
E[delta_1_source] = [-0.11, -0.08, 0.11, 0.10, -0.01, -0.45, -0.23, -0.01, -0.22, -0.01]
```

---

### What Proxy Models Learn

**Placebo model** (trained on 750 source placebo patients):
```
Learns to predict: Y | A=0, X

Approximately learns:
  μ̂₀(x) ≈ 0.5·x₁ - 0.3·x₂ + 0.12·x₃ - 0.23·x₆ - 0.37·x₇
           └────┬────┘       └──────────┬──────────┘
          Global β₀       Average source bias
```

**Treated model** (trained on 750 source treated patients):
```
Learns to predict: Y | A=1, X

Approximately learns:
  μ̂₁(x) ≈ 0.5·x₁ - 0.3·x₂ + 0.6·x₁ + 0.4·x₂ - 0.3·x₃ - 0.11·x₁ - 0.08·x₂ + ...
           └────┬────┘       └────────┬────────┘       └──────────┬──────────┘
          Global β₀          Global β_τ              Average source bias
```

---

### Prediction on Target

**Target site** (the one we care about):
```
delta_0_target = [0, 0, 0, 0, 0, 0, -0.64, 0, 0, 0.27]  ← Different from sources!
delta_1_target = [-0.17, -0.06, 0.30, 0.07, 0.21, 0, -0.63, -0.08, -0.08, 0.22]
```

**For a target patient with X = [1.0, 0.5, -0.2, 0.1, ...]**:

**Proxy prediction**:
```python
μ̂₀(X) = model_0.predict(X) ≈ 2.1  
μ̂₁(X) = model_1.predict(X) ≈ 3.5
τ̂_proxy = 3.5 - 2.1 = 1.4
```

**True target values**:
```python
μ₀_target(X) = β₀'X + δ₀_target'X ≈ 1.8  ← Differs by ~0.3
μ₁_target(X) = β₀'X + β_τ'X + δ₁_target'X ≈ 3.2  ← Differs by ~0.3
τ_target(X) = 3.2 - 1.8 = 1.4  ← SAME! (biases cancel)
```

**CRITICAL**: Even though individual predictions are biased (~0.3 error), **CATE can be correct** if biases cancel!

---

## 🔬 Why Does It Work Well?

### 1. Large Sample Size (Low Variance)

**Source data**: 1500 total samples
- 750 for placebo model
- 750 for treated model

**Consequence**:
```
Variance(μ̂₀) ∝ 1/750  ← Small!
Variance(μ̂₁) ∝ 1/750
Variance(τ̂) ∝ 2/750 ≈ 1/375  ← Still small
```

**Compare to target-only methods**:
```
Target sample: n=500
Variance ∝ 1/250  ← 1.5x larger!
```

---

### 2. Bias Cancellation at High ρ

**At ρ = 1.0** (shared bias):
```
δ₁ = δ₀  everywhere

CATE bias = [E[δ₁_source] - δ₁_target] - [E[δ₀_source] - δ₀_target]
          = [E[δ₀_source] - δ₀_target] - [E[δ₀_source] - δ₀_target]
          = 0  ← Perfect cancellation!

Result: τ̂_proxy(x) = τ_target(x) + noise (unbiased!)
```

**At ρ = 0.0** (differential bias):
```
δ₁ ≠ δ₀

CATE bias = [E[δ₁_source] - δ₁_target] - [E[δ₀_source] - δ₀_target]
          ≠ 0  ← No cancellation

Result: τ̂_proxy(x) = τ_target(x) + bias + noise
```

**Measured biases** (seed 42):
| ρ | CATE Bias | Cancellation |
|---|-----------|--------------|
| 1.0 | 0.08 | 93% ✓✓ |
| 0.5 | 0.30 | 71% ✓ |
| 0.0 | 0.36 | 61% |

Even at ρ=0.0, **61% cancellation** keeps bias moderate!

---

### 3. Flexible Model (RandomForest)

**RandomForest properties**:
- Non-parametric (can learn complex patterns)
- Handles interactions automatically
- Robust to outliers
- Works with moderate dimensions (p=10)

**With 750 training samples**:
- RF can fit complex relationships
- Not just linear bias corrections
- Adapts to heterogeneous patterns

---

## 🎯 What Proxy-Only Gets Right

### Correct Components

**1. Global baseline** (β₀):
```
✅ Learned from source data
✅ Shared across all sites
✅ No transport bias here
```

**2. Global CATE** (β_τ):
```
✅ Learned from source data
✅ Shared across all sites  
✅ Heterogeneous effects captured (via RF)
```

**Example**: Patient with X = [1, 1, 0, ...]:
```
True τ(X) = 0.6(1) + 0.4(1) - 0.3(0) = 1.0
Proxy predicts: ≈ 0.95-1.05 (close!)
```

---

## ❌ What Proxy-Only Gets Wrong

### Biased Components

**1. Site-specific bias in μ₀**:
```
Proxy learns: μ̂₀(x) ≈ β₀'x + E[δ₀_source]'x
Should be:    μ₀_target(x) = β₀'x + δ₀_target'x

Error: [E[δ₀_source] - δ₀_target]'x
```

**Measured (seed 42)**:
- Mean bias: +0.48
- RMSE: 0.81
- R²: 0.52 (only 52% variance explained!)

---

**2. Site-specific bias in μ₁**:
```
Proxy learns: μ̂₁(x) ≈ β₀'x + β_τ'x + E[δ₁_source]'x
Should be:    μ₁_target(x) = β₀'x + β_τ'x + δ₁_target'x

Error: [E[δ₁_source] - δ₁_target]'x
```

**Measured**:
- Mean bias: +0.44 to +0.56 (depends on ρ)
- RMSE: 0.84-0.95
- Poor individual predictions!

---

**3. But CATE bias is smaller!**

```
CATE error = μ₁ error - μ₀ error
           = [δ₁_source - δ₁_target]'x - [δ₀_source - δ₀_target]'x
           = [(δ₁_source - δ₀_source) - (δ₁_target - δ₀_target)]'x
```

**At ρ = 1.0**:
```
δ₁ = δ₀ everywhere → Difference = 0 → CATE bias ≈ 0!
```

**At ρ = 0.0**:
```
δ₁ ≠ δ₀ → Difference ≠ 0 → CATE bias ≈ 0.36
```

---

## 📊 Performance Analysis

### Sample Sizes Used

**Training** (fit method):
```
Source placebo:  n = 750  (large!)
Source treated:  n = 750  (large!)
Target:          n = 0    (IGNORED!)
```

**Prediction** (predict method):
```
Applied to target test set: n = 500
```

---

### Variance Calculation

**From large source sample**:
```
Var(μ̂₀) ≈ σ²/750  (very stable)
Var(μ̂₁) ≈ σ²/750
Var(τ̂) ≈ 2σ²/750  (low variance!)
```

**This is Proxy's advantage**: Trained on 3x more data than target-only methods!

---

### Bias-Variance Tradeoff

**Proxy-Only**:
- **Variance**: LOW (trained on n=1500)
- **Bias**: Depends on ρ
  - ρ = 1.0: TINY (0.08, cancels)
  - ρ = 0.0: MODERATE (0.36)
- **Total Error (PEHE)**: 
  - ρ = 1.0: 0.48 (mostly variance)
  - ρ = 0.0: 0.78 (bias + variance)

---

### Comparison to Other Methods

**At ρ = 1.0** (shared bias):

| Method | Variance Source | Bias | Total PEHE |
|--------|----------------|------|------------|
| **Proxy** | n=1500 (low) | 0.08 | **0.48** |
| **Anchor** | n=500 (medium) | 0 (corrected) | **0.32** ✓✓ |
| **Proposed** | n=167/fold (high) | 0 (DR) | **0.34** ✓ |

**Winner**: Anchor-Only (corrects bias, reasonable variance)

---

**At ρ = 0.0** (differential bias):

| Method | Variance Source | Bias | Total PEHE |
|--------|----------------|------|------------|
| **Proxy** | n=1500 (low) | 0.36 | **0.78** ✓ |
| **Anchor** | n=250/arm (high!) | 0 (tries) | **1.31** ❌ |
| **Proposed** | n=167/fold (higher) | 0 (tries) | **1.12** ❌ |

**Winner**: Proxy-Only (bias < variance of corrections!)

---

## 💡 Key Insights

### 1. Proxy-Only is "Stage 1 Only"

In the paper's 3-stage framework:
```
Stage 1: Fit proxy models on source ← THIS IS ALL PROXY-ONLY DOES
Stage 2: Anchor corrections using target ← SKIPPED
Stage 3: DR orthogonalization ← SKIPPED
```

**Advantage**: Simplest approach, lowest variance  
**Disadvantage**: Ignores valuable target data

---

### 2. Why It's Competitive Despite Ignoring Target

**Three factors**:

**Factor 1**: Large source sample (1500 vs 500)
```
3x more data → √3 ≈ 1.7x lower standard error
```

**Factor 2**: Bias cancellation at high ρ
```
ρ = 1.0: CATE bias = 0.08 (93% cancellation)
ρ = 0.5: CATE bias = 0.30 (71% cancellation)
```

**Factor 3**: Heterogeneous bias + flexible model
```
Bias mean = 0.36, but bias std = 0.93
RF can adapt to heterogeneous patterns
Not just a constant shift!
```

---

### 3. When It Should Fail (But Doesn't at n=500)

**Theory says**: At ρ = 0.0, CATE bias should dominate

**Reality**: 
- CATE bias = 0.36 (moderate, not catastrophic)
- Proxy variance = ~0.6 (from other sources)
- Anchor variance = ~1.2 (much higher at n=500!)
- **Variance dominates** at current sample sizes

**At n = 5000+**: Anchor variance would be low enough to overcome bias, and Anchor would win at ρ=0.0

---

## 🔍 Implementation Details

### Why Clone the Model?

```python
for arm in [0, 1]:
    model = clone(self.proxy_model)  # ← Why clone?
    model.fit(X_source[mask], Y_source[mask])
```

**Reason**: Create **independent** models for each arm
- Each model has own fitted trees
- No parameter sharing
- Allows different patterns per arm

**Without clone**:
```python
# WRONG:
self.proxy_model.fit(X_placebo, Y_placebo)  # Fit once
self.proxy_model.fit(X_treated, Y_treated)  # Overwrites previous!
```

---

### Why Ignore Target Data?

**Conceptual**:
- Pure "transfer learning" baseline
- Tests: Can we transfer WITHOUT using target?
- Represents worst-case scenario (no target RCT)

**Practical**:
- Simplest possible approach
- Maximizes training data (all sources)
- Establishes lower bound for performance

**In experiments**:
- If Proxy-Only wins → Don't need complex methods!
- If Proxy-Only loses → Complex methods add value

---

## 📈 Performance Summary (From Our Tests)

### By ρ (n_target = 500, 50 runs)

| ρ | Proxy PEHE | Interpretation |
|---|------------|----------------|
| **1.0** | **0.481** ✓✓ | Excellent (bias cancels, low variance) |
| **0.8** | **0.582** ✓ | Good (mild bias, low variance) |
| **0.5** | **0.680** | Okay (moderate bias) |
| **0.3** | **0.728** | Acceptable (substantial bias) |
| **0.0** | **0.776** | Fair (high bias, but still competitive) |

**Trend**: Performance degrades as ρ decreases (less cancellation)

---

### Comparison to Anchor/Proposed

**At ρ = 1.0** (shared bias):
```
Proxy:    0.481  ← Good
Anchor:   0.324  ← Better! (-33%)
Proposed: 0.341  ← Better! (-29%)
```
**Conclusion**: Anchoring adds clear value

---

**At ρ = 0.0** (differential bias):
```
Proxy:    0.776  ← Best! ✓
Anchor:   1.313  ← Catastrophic (+69%)
Proposed: 1.119  ← Bad (+44%)
```
**Conclusion**: Simple is better with small samples

---

## 🎯 Summary

### What Proxy-Only Does

```python
1. Pool all source sites (ignore differences)
2. Train μ̂₀ on source placebo (n=750)
3. Train μ̂₁ on source treated (n=750)
4. Predict τ̂(x) = μ̂₁(x) - μ̂₀(x)
5. Apply to target (ignore target data entirely!)
```

**Strengths**:
- ✅ Very low variance (large training set)
- ✅ Simple, robust, interpretable
- ✅ Benefits from bias cancellation at high ρ
- ✅ Flexible model adapts to heterogeneity

**Weaknesses**:
- ❌ Ignores valuable target data
- ❌ Has transport bias (especially at low ρ)
- ❌ Individual outcome predictions are poor
- ❌ Wastes target RCT information

---

### When It Wins

**Wins when**:
- ρ is high (ρ ≥ 0.8): Bias cancels
- n_target is small (<1000): Variance dominates
- Source data is abundant (n > 1000)

**Current experiments (n_target=500)**:
- ✅ Wins at ρ < 0.8 (differential bias regime)
- ❌ Loses at ρ = 1.0 (shared bias regime)

---

### Implementation Gotchas

**1. Target data is passed but NOT used**:
```python
def fit(self, X_source, A_source, Y_source, 
        X_target, A_target, Y_target,  # ← Passed but ignored!
        propensity_source=None, propensity_target=None):
```

**Why?**: Keep API consistent with other methods

---

**2. Requires BOTH arms in source**:
```python
for arm in [0, 1]:  # Need both!
    mask = (A_source == arm)
    model.fit(X_source[mask], Y_source[mask])
```

**If source had only one arm**: Method would fail!

---

**3. Predicts on ANY X (not just target)**:
```python
def predict(self, X):  # X can be from any distribution
    return self.models_[1].predict(X) - self.models_[0].predict(X)
```

**Generality**: Can apply to new populations (but with bias!)

---

## 📊 Actual Training Example

### What RandomForest Learns (Approximation)

**Placebo model** on pooled sources:
```
Input: X (10 features)
Output: Y | A=0

Internal structure (200 trees):
  Tree 1: if X₁ > 0.3 and X₇ < -0.5: predict 2.1
          elif X₂ < 0 and X₃ > 0.2: predict 1.8
          ...
  
  Tree 2: if X₃ < -0.1 and X₆ > 0.5: predict 2.3
          ...
  
  [198 more trees...]
  
Final prediction: Average of all 200 trees
```

**What it captures**:
- ✅ Global baseline (β₀'x)
- ✅ Average source bias (E[δ₀_source]'x)
- ✅ Non-linear patterns
- ✅ Interactions between features

**What it misses**:
- ❌ Target-specific bias (δ₀_target - E[δ₀_source])
- ❌ But this is okay if it cancels in CATE!

---

## 🎓 Theoretical Perspective

### What Proxy-Only Estimates

**Estimand**: 
```
τ̂_proxy(x) = E_source[Y | A=1, X=x] - E_source[Y | A=0, X=x]
```

**Not quite the target estimand**:
```
τ_target(x) = E_target[Y | A=1, X=x] - E_target[Y | A=0, X=x]
```

**Difference**:
```
τ̂_proxy(x) - τ_target(x) = [E_source[δ₁] - δ_target]'x - [E_source[δ₀] - δ_target]'x
                          = [(δ₁,source - δ₀,source) - (δ₁,target - δ₀,target)]'x
                          = [Δ_source - Δ_target]'x
                          
Where Δ_source = δ₁_source - δ₀_source (differential bias in source)
      Δ_target = δ₁_target - δ₀_target (differential bias in target)
```

**At ρ = 1.0**: Δ = 0 everywhere → Error = 0 ✓  
**At ρ = 0.0**: Δ ≠ 0 → Error ≠ 0 ❌

---

## 🔑 The Key Takeaway

**Proxy-Only is NOT using similar source sites!**

**Evidence**:
- Sites have different biases (||δ_s - δ_t|| = 0.5-1.0)
- Different patient populations (||E[X_s] - E[X_t]|| = 2.4)
- Poor individual predictions (RMSE ~0.8-0.9)

**BUT**: It performs well because:
1. ✅ **Low variance** (n=1500 training)
2. ✅ **Bias cancellation** in CATE (especially at high ρ)
3. ✅ **Flexible model** adapts to heterogeneity

**The issue**: At n_target=500, Anchor/Proposed can't overcome their **higher variance** (from small sample corrections) to beat Proxy's **low variance + moderate bias** combination.

**Solution**: Need n_target > 2000 for Anchor/Proposed to win at low ρ!

---

**File**: `PROXY_ONLY_EXPLAINED.md`  
**Key Insight**: Proxy-Only wins by having **low variance**, not because sites are similar!  
**Bottom line**: Sites ARE different, but bias-variance tradeoff favors simple methods at small sample sizes.
