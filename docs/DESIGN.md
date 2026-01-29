# Design Document: Placebo-Anchored Proxy-Gold DR-Learner

## Executive Summary

This document specifies the implementation of a three-stage placebo-anchored doubly robust estimator for transporting treatment effects across heterogeneous RCTs under covariate shift. The method treats source-trial outcomes as "proxy" labels and target-placebo outcomes as scarce "gold" labels for calibration.

---

## 1. Problem Statement

**Goal**: Estimate patient-level conditional average treatment effects (CATE) τ(x) in a target population by:
1. Leveraging abundant data from source RCTs (proxy labels)
2. Calibrating to target placebo outcomes (gold labels)
3. Handling covariate shift and disconnected trial networks

**Key Challenge**: Source trials may have systematically different baseline risks due to population heterogeneity, making naive pooling biased.

**Solution**: Three-stage estimation with sparse transport-bias correction.

---

## 2. Data Schema

### 2.1 Input Data Structure

```python
# SOURCE TRIALS (multiple sites, c ∈ {1, 2, ..., C})
SourceData = {
    'X_source': np.ndarray,     # shape (n_source, p) - baseline covariates
    'A_source': np.ndarray,     # shape (n_source,) - treatment assignment {0, 1}
    'Y_source': np.ndarray,     # shape (n_source,) - observed outcomes
    'site_ids': np.ndarray,     # shape (n_source,) - site indicators
    'propensity_source': np.ndarray,  # shape (n_source,) - e_c(x), known from design
}

# TARGET TRIAL (single site, c = 0)
TargetData = {
    'X_target': np.ndarray,     # shape (n_target, p) - same feature space as source
    'A_target': np.ndarray,     # shape (n_target,) - treatment assignment
                                # May be all 0s in disconnected setting
    'Y_target': np.ndarray,     # shape (n_target,) - observed outcomes
    'propensity_target': np.ndarray,  # shape (n_target,) - e_0(x), known from design
}
```

### 2.2 Data Requirements

**Source Trials**:
- X_source: Standardized or normalized covariates (for LASSO in Stage 2)
- A_source: Binary treatment (0=placebo, 1=treated)
- Y_source: Continuous outcome (change in clinical marker, survival time, etc.)
- propensity_source: Known from RCT protocol (typically 0.5 for 1:1 randomization)

**Target Trial**:
- X_target: Same p features as source (identical variable definitions)
- A_target: May be all 0s (disconnected) or contain both arms
- Y_target: Placebo outcomes serve as "gold" calibration labels
- propensity_target: Known from RCT protocol

**Constraints**:
1. n_source >> n_target typically (abundant proxy, scarce gold)
2. X_source and X_target have same dimensionality p
3. Covariate supports overlap (mild covariate shift, not severe distribution mismatch)
4. Treatment is randomized within each site (propensities known)

---

## 3. Algorithm Specification

### 3.1 Stage 1: Proxy Model Fitting

**Objective**: Learn outcome regressions from abundant source data

**Input**: (X_source, A_source, Y_source)

**Output**: μ̂^proxy_0(x), μ̂^proxy_1(x)

```python
def stage1_fit_proxy_models(X_source, A_source, Y_source, proxy_learner):
    """
    Stage 1: Fit separate outcome regressions for each arm on pooled sources.
    
    Args:
        X_source: (n_source, p) covariate matrix
        A_source: (n_source,) treatment indicators
        Y_source: (n_source,) outcomes
        proxy_learner: sklearn-style estimator (RF, GBM, etc.)
    
    Returns:
        proxy_models: dict with keys {0, 1} mapping to fitted models
    """
    proxy_models = {}
    
    for arm in [0, 1]:
        # Separate data by treatment arm
        mask_arm = (A_source == arm)
        X_arm = X_source[mask_arm]
        Y_arm = Y_source[mask_arm]
        
        # Fit flexible model (no sparsity constraints here)
        model_arm = clone(proxy_learner)
        model_arm.fit(X_arm, Y_arm)
        
        proxy_models[arm] = model_arm
        
        # Note: pooling across sources assumes their data is exchangeable
        # after Stage 2 correction. No site indicators used here.
    
    return proxy_models
```

**Implementation Notes**:
- Use flexible learners: RandomForest, GradientBoosting, or Neural Networks
- No regularization needed (abundant data, low variance)
- Pooling is justified because systematic site bias is addressed in Stage 2
- Cross-validation for hyperparameters (e.g., tree depth, learning rate)

---

### 3.2 Stage 2: Gold Correction with LASSO

**Objective**: Estimate sparse transport bias δ_{a,c} using target outcomes

#### 3.2.1 Placebo Arm Correction (Always Performed)

**Input**: 
- X_target[A_target==0], Y_target[A_target==0] (gold placebo labels)
- μ̂^proxy_0 from Stage 1

**Output**: δ̂_{0,0} (sparse correction vector)

```python
def stage2_placebo_correction(X_target, Y_target, A_target, 
                              mu_proxy_0, lasso_cv_folds=5):
    """
    Stage 2a: Estimate sparse transport bias for placebo arm using LASSO.
    
    Args:
        X_target: (n_target, p) target covariates
        Y_target: (n_target,) target outcomes
        A_target: (n_target,) target treatment indicators
        mu_proxy_0: fitted proxy model for placebo arm
        lasso_cv_folds: number of CV folds for lambda selection
    
    Returns:
        delta_0: (p,) sparse correction vector
        intercept_0: scalar intercept (if fit_intercept=True)
        lasso_model: fitted LassoCV object
    """
    # Extract placebo samples from target (gold labels)
    mask_placebo = (A_target == 0)
    X_gold_0 = X_target[mask_placebo]
    Y_gold_0 = Y_target[mask_placebo]
    m_0 = len(Y_gold_0)
    
    if m_0 < 10:
        warnings.warn(f"Only {m_0} target placebo samples - correction may be unstable")
        return np.zeros(X_target.shape[1]), 0.0, None
    
    # Compute residuals: Ỹ = Y - μ̂^proxy_0(X)
    Y_residual = Y_gold_0 - mu_proxy_0.predict(X_gold_0)
    
    # Fit LASSO to estimate sparse correction: δ̂_{0,0}
    # Solves: argmin_δ { (1/m_0) Σ(Ỹ_j - δ'X_j)² + λ||δ||_1 }
    lasso = LassoCV(
        cv=lasso_cv_folds,
        fit_intercept=True,  # Can absorb global bias shift
        max_iter=5000,
        random_state=42
    )
    lasso.fit(X_gold_0, Y_residual)
    
    delta_0 = lasso.coef_
    intercept_0 = lasso.intercept_
    
    # Report sparsity
    sparsity = np.sum(np.abs(delta_0) > 1e-6)
    print(f"  Placebo correction: ||δ||_0 = {sparsity}/{len(delta_0)}, "
          f"λ = {lasso.alpha_:.4f}")
    
    return delta_0, intercept_0, lasso
```

#### 3.2.2 Treated Arm Correction (Option A vs Option B)

**Option A**: Target has treated arm (preferred when available)

```python
def stage2_treated_correction_optionA(X_target, Y_target, A_target,
                                      mu_proxy_1, lasso_cv_folds=5):
    """
    Stage 2b (Option A): Estimate treated arm correction using target treated data.
    """
    mask_treated = (A_target == 1)
    X_gold_1 = X_target[mask_treated]
    Y_gold_1 = Y_target[mask_treated]
    m_1 = len(Y_gold_1)
    
    if m_1 < 10:
        warnings.warn(f"Only {m_1} target treated samples - using Option B")
        return None, None, None
    
    Y_residual = Y_gold_1 - mu_proxy_1.predict(X_gold_1)
    
    lasso = LassoCV(
        cv=lasso_cv_folds,
        fit_intercept=True,
        max_iter=5000,
        random_state=42
    )
    lasso.fit(X_gold_1, Y_residual)
    
    delta_1 = lasso.coef_
    intercept_1 = lasso.intercept_
    
    sparsity = np.sum(np.abs(delta_1) > 1e-6)
    print(f"  Treated correction: ||δ||_0 = {sparsity}/{len(delta_1)}, "
          f"λ = {lasso.alpha_:.4f}")
    
    return delta_1, intercept_1, lasso
```

**Option B**: Disconnected target (no treated arm)

```python
def stage2_treated_correction_optionB(delta_0, intercept_0):
    """
    Stage 2b (Option B): Shared bias assumption for disconnected setting.
    
    Assumes: δ_{1,0} = δ_{0,0} (Assumption A6 with ρ=1, ζ=0)
    
    This is a working assumption, not an identification result.
    """
    print(f"  Treated correction: using shared bias (Option B)")
    return delta_0, intercept_0
```

#### 3.2.3 Anchored Outcome Models

```python
def construct_anchored_models(mu_proxy_0, mu_proxy_1, 
                              delta_0, delta_1, 
                              intercept_0, intercept_1):
    """
    Construct anchored outcome regressions:
        μ̂^anch_{a,c}(x) = μ̂^proxy_a(x) + δ̂'_{a,c}x + b_{a,c}
    
    Returns:
        mu_anch_0, mu_anch_1: callable functions
    """
    def mu_anch_0(X):
        return mu_proxy_0.predict(X) + X @ delta_0 + intercept_0
    
    def mu_anch_1(X):
        return mu_proxy_1.predict(X) + X @ delta_1 + intercept_1
    
    return mu_anch_0, mu_anch_1
```

---

### 3.3 Stage 3: Doubly Robust Pseudo-Outcomes with Cross-Fitting

**Objective**: Construct orthogonalized pseudo-outcomes and fit final CATE model

#### 3.3.1 Pseudo-Outcome Construction

```python
def compute_dr_pseudo_outcomes(X, A, Y, propensity, mu_anch_0, mu_anch_1):
    """
    Compute doubly robust pseudo-outcomes:
    
    ψ_i = τ̂(X_i) + [(A_i - e(X_i)) / (e(X_i)(1 - e(X_i)))] * [Y_i - μ̂^anch_{A_i}(X_i)]
    
    where τ̂(x) = μ̂^anch_1(x) - μ̂^anch_0(x)
    
    Args:
        X: (n, p) covariates
        A: (n,) treatment indicators
        Y: (n,) outcomes
        propensity: (n,) or scalar - e(X) = P(A=1|X)
        mu_anch_0, mu_anch_1: anchored outcome functions
    
    Returns:
        psi: (n,) pseudo-outcomes
        tau_initial: (n,) initial CATE estimates (used in DR correction)
    """
    n = len(X)
    
    # Ensure propensity is array
    if np.isscalar(propensity):
        propensity = np.full(n, propensity)
    
    # Initial CATE estimate (before DR correction)
    mu_0_pred = mu_anch_0(X)
    mu_1_pred = mu_anch_1(X)
    tau_initial = mu_1_pred - mu_0_pred
    
    # Compute DR pseudo-outcomes
    psi = np.zeros(n)
    for i in range(n):
        e_i = propensity[i]
        a_i = A[i]
        y_i = Y[i]
        
        # Select appropriate anchored prediction
        mu_a_i = mu_1_pred[i] if a_i == 1 else mu_0_pred[i]
        
        # Doubly robust correction term
        # Avoid division by zero
        if e_i * (1 - e_i) < 1e-6:
            dr_correction = 0.0
        else:
            dr_correction = ((a_i - e_i) / (e_i * (1 - e_i))) * (y_i - mu_a_i)
        
        psi[i] = tau_initial[i] + dr_correction
    
    return psi, tau_initial
```

#### 3.3.2 Cross-Fitting Implementation

```python
def stage3_crossfit_dr_learner(X_target, A_target, Y_target, propensity_target,
                               proxy_models, delta_0, delta_1, 
                               intercept_0, intercept_1,
                               cate_learner, n_folds=5):
    """
    Stage 3: Fit final CATE model using cross-fitted DR pseudo-outcomes.
    
    Cross-fitting procedure:
    1. Split target data into K folds
    2. For each fold k:
       a. Fit corrections δ on training folds
       b. Compute pseudo-outcomes ψ on validation fold
    3. Fit final CATE model on all pseudo-outcomes
    
    Args:
        X_target: (n_target, p) target covariates
        A_target: (n_target,) target treatments
        Y_target: (n_target,) target outcomes
        propensity_target: (n_target,) known propensities
        proxy_models: dict {0: model_0, 1: model_1} from Stage 1
        delta_0, delta_1: correction vectors (from single fit)
        intercept_0, intercept_1: correction intercepts
        cate_learner: sklearn-style estimator for final CATE
        n_folds: number of cross-fitting folds
    
    Returns:
        cate_model: fitted model for τ̂_DR(x)
        pseudo_outcomes: (n_target,) pseudo-outcomes
        fold_corrections: list of corrections per fold (for diagnostics)
    """
    n = len(X_target)
    pseudo_outcomes = np.zeros(n)
    fold_corrections = []
    
    # Stratified K-fold (stratify by treatment to ensure balance)
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_target, A_target)):
        # --- Split data ---
        X_train, X_val = X_target[train_idx], X_target[val_idx]
        A_train, A_val = A_target[train_idx], A_target[val_idx]
        Y_train, Y_val = Y_target[train_idx], Y_target[val_idx]
        prop_val = propensity_target[val_idx]
        
        # --- Fit corrections on training fold ---
        delta_0_fold, int_0_fold, _ = stage2_placebo_correction(
            X_train, Y_train, A_train, 
            proxy_models[0], lasso_cv_folds=3
        )
        
        # Check for treated samples in training fold
        if np.sum(A_train == 1) >= 10:
            delta_1_fold, int_1_fold, _ = stage2_treated_correction_optionA(
                X_train, Y_train, A_train,
                proxy_models[1], lasso_cv_folds=3
            )
            if delta_1_fold is None:
                delta_1_fold, int_1_fold = stage2_treated_correction_optionB(
                    delta_0_fold, int_0_fold
                )
        else:
            delta_1_fold, int_1_fold = stage2_treated_correction_optionB(
                delta_0_fold, int_0_fold
            )
        
        fold_corrections.append({
            'delta_0': delta_0_fold,
            'delta_1': delta_1_fold,
            'intercept_0': int_0_fold,
            'intercept_1': int_1_fold
        })
        
        # --- Construct anchored models for validation fold ---
        mu_anch_0, mu_anch_1 = construct_anchored_models(
            proxy_models[0], proxy_models[1],
            delta_0_fold, delta_1_fold,
            int_0_fold, int_1_fold
        )
        
        # --- Compute pseudo-outcomes on validation fold ---
        psi_val, _ = compute_dr_pseudo_outcomes(
            X_val, A_val, Y_val, prop_val,
            mu_anch_0, mu_anch_1
        )
        
        pseudo_outcomes[val_idx] = psi_val
    
    # --- Fit final CATE model on all pseudo-outcomes ---
    if np.any(np.isnan(pseudo_outcomes)):
        warnings.warn("NaN in pseudo-outcomes, filtering")
        mask = ~np.isnan(pseudo_outcomes)
        cate_model = clone(cate_learner)
        cate_model.fit(X_target[mask], pseudo_outcomes[mask])
    else:
        cate_model = clone(cate_learner)
        cate_model.fit(X_target, pseudo_outcomes)
    
    return cate_model, pseudo_outcomes, fold_corrections
```

---

### 3.4 Complete Pipeline

```python
class PlaceboAnchoredDRLearner:
    """
    Three-stage placebo-anchored doubly robust learner for RCT transport.
    
    Parameters
    ----------
    proxy_learner : sklearn estimator
        Flexible model for Stage 1 (default: RandomForest)
    cate_learner : sklearn estimator
        Model for Stage 3 CATE regression (default: GradientBoosting)
    option : {'A', 'B'}
        'A': use target treated data if available
        'B': shared bias for disconnected setting
    n_folds : int
        Number of cross-fitting folds
    lasso_cv_folds : int
        CV folds for LASSO lambda selection
    """
    
    def __init__(self, proxy_learner=None, cate_learner=None, 
                 option='B', n_folds=5, lasso_cv_folds=5):
        self.proxy_learner = proxy_learner or RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=20,
            random_state=42, n_jobs=-1
        )
        self.cate_learner = cate_learner or GradientBoostingRegressor(
            n_estimators=100, max_depth=4, learning_rate=0.05,
            random_state=42
        )
        self.option = option
        self.n_folds = n_folds
        self.lasso_cv_folds = lasso_cv_folds
        
        # Fitted attributes
        self.proxy_models_ = None
        self.delta_placebo_ = None
        self.delta_treated_ = None
        self.cate_model_ = None
    
    def fit(self, X_source, A_source, Y_source,
            X_target, A_target, Y_target,
            propensity_source=None, propensity_target=None):
        """
        Fit the three-stage estimator.
        
        Parameters
        ----------
        X_source : (n_source, p) array
        A_source : (n_source,) array
        Y_source : (n_source,) array
        X_target : (n_target, p) array
        A_target : (n_target,) array
        Y_target : (n_target,) array
        propensity_source : (n_source,) array or None
        propensity_target : (n_target,) array or None
        
        Returns
        -------
        self : fitted estimator
        """
        # Validate inputs
        # [validation code omitted for brevity]
        
        # Stage 1: Proxy models
        print("Stage 1: Fitting proxy models on source data...")
        self.proxy_models_ = stage1_fit_proxy_models(
            X_source, A_source, Y_source, self.proxy_learner
        )
        
        # Stage 2 & 3: Anchoring and DR with cross-fitting
        print(f"Stage 2-3: Anchoring (Option {self.option}) + DR cross-fitting...")
        self.cate_model_, pseudo_outcomes, fold_corrections = \
            stage3_crossfit_dr_learner(
                X_target, A_target, Y_target, propensity_target,
                self.proxy_models_, 
                None, None, None, None,  # Will be fit in cross-fitting
                self.cate_learner, self.n_folds
            )
        
        # Store average corrections for interpretation
        self.delta_placebo_ = np.mean([fc['delta_0'] for fc in fold_corrections], axis=0)
        self.delta_treated_ = np.mean([fc['delta_1'] for fc in fold_corrections], axis=0)
        
        return self
    
    def predict(self, X):
        """
        Predict CATE τ̂(x) for new patients.
        
        Parameters
        ----------
        X : (n_samples, p) array
        
        Returns
        -------
        tau : (n_samples,) array of predicted treatment effects
        """
        check_is_fitted(self, 'cate_model_')
        return self.cate_model_.predict(X)
    
    def predict_counterfactuals(self, X, delta_placebo=None, delta_treated=None):
        """
        Predict counterfactual outcomes μ_0(x), μ_1(x).
        
        Returns
        -------
        mu_0, mu_1 : (n_samples,) arrays
        """
        check_is_fitted(self, 'proxy_models_')
        
        if delta_placebo is None:
            delta_placebo = self.delta_placebo_
        if delta_treated is None:
            delta_treated = self.delta_treated_
        
        mu_0 = self.proxy_models_[0].predict(X) + X @ delta_placebo
        mu_1 = self.proxy_models_[1].predict(X) + X @ delta_treated
        
        return mu_0, mu_1
```

---

## 4. Evaluation Metrics

```python
def evaluate_transport_performance(tau_true, tau_pred, 
                                   mu0_true, mu0_pred,
                                   mu1_true, mu1_pred):
    """
    Comprehensive evaluation for transport learning.
    
    Returns
    -------
    metrics : dict with keys:
        - 'PEHE': Precision in Estimation of Heterogeneous Effects
        - 'ATE_Error': Absolute error in average treatment effect
        - 'Bias_ATE': Signed bias in ATE
        - 'Calibration_RMSE_mu0': Calibration error for placebo
        - 'Calibration_RMSE_mu1': Calibration error for treated
        - 'R2_CATE': R² for CATE predictions
    """
    # PEHE: √E[(τ(x) - τ̂(x))²]
    pehe = np.sqrt(np.mean((tau_true - tau_pred)**2))
    
    # ATE error: |E[τ(x)] - E[τ̂(x)]|
    ate_true = np.mean(tau_true)
    ate_pred = np.mean(tau_pred)
    ate_error = np.abs(ate_true - ate_pred)
    bias_ate = ate_pred - ate_true
    
    # Calibration: RMSE for outcome models
    cal_mu0 = np.sqrt(np.mean((mu0_true - mu0_pred)**2))
    cal_mu1 = np.sqrt(np.mean((mu1_true - mu1_pred)**2))
    
    # R² for heterogeneity capture
    r2_cate = r2_score(tau_true, tau_pred) if np.var(tau_true) > 0 else 0.0
    
    return {
        'PEHE': pehe,
        'ATE_Error': ate_error,
        'Bias_ATE': bias_ate,
        'Calibration_RMSE_mu0': cal_mu0,
        'Calibration_RMSE_mu1': cal_mu1,
        'R2_CATE': r2_cate
    }
```

---

## 5. Proposed Ablation Tests (Updated)

The manuscript's ablation tests are good but can be extended. Here are comprehensive ablation experiments:

### 5.1 Core Component Ablations

**Purpose**: Isolate contribution of each algorithmic component

| Ablation | Description | What's Removed | Expected Result |
|----------|-------------|----------------|-----------------|
| **No-Transfer** | Target placebo only, constant CATE | Proxy, Anchoring, DR | Fails to predict heterogeneity |
| **Proxy-Only** | Pooled sources, no calibration | Anchoring (Stage 2) | Biased baseline, poor calibration |
| **Anchor-Only** | Placebo anchoring, no DR | DR orthogonalization (Stage 3) | Good ATE, higher PEHE |
| **Proxy+DR (No Anchor)** | DR without anchoring | Anchoring (Stage 2) | Tests if DR alone handles shift |
| **Full Proposed** | All three stages | None | Best overall |

### 5.2 Architectural Ablations

**Purpose**: Test modeling choices

| Ablation | Variation | Tests |
|----------|-----------|-------|
| **Proxy Model Complexity** | Linear → RF → GBM → Neural Net | Nonlinearity in Stage 1 |
| **CATE Model Complexity** | Linear → Kernel → RF | Stage 3 flexibility |
| **Sparsity Mechanism** | LASSO → Ridge → Elastic Net → OLS | Importance of ℓ₁ penalty |
| **No Intercept in Stage 2** | fit_intercept=False | Global shift vs covariate-dependent shift |

### 5.3 Data Regime Ablations

**Purpose**: Characterize sample efficiency

| Ablation | Sweep Range | Tests |
|----------|-------------|-------|
| **Gold Budget** | m₀ ∈ {20, 50, 100, 200, 500} | Diminishing returns of target data |
| **Proxy Budget** | n_source ∈ {500, 1k, 2k, 5k} | Value of abundant source data |
| **Target Treated Ratio** | n₁/(n₀+n₁) ∈ {0, 0.2, 0.5} | Option A vs B crossover |
| **Number of Sources** | C ∈ {1, 3, 5, 10} | Multi-site pooling benefit |

### 5.4 Robustness to Assumption Violations

**Purpose**: Stress-test working assumptions

#### 5.4.1 Covariate Shift Severity (Assumption A4)

```python
# Vary shift magnitude
shift_scale ∈ [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
# Measure: TV distance between P(X|c=0) and P(X|c>0)
```

**Expected**: Performance degrades smoothly as shift increases

#### 5.4.2 Transport Bias Sparsity (Assumption A5)

```python
# Vary true sparsity of δ
s_true ∈ [1, 2, 3, 5, 10, p]  # where p=total features
# Generate δ with ||δ||_0 = s_true
```

**Expected**: LASSO recovers well when s_true ≤ 3, degrades beyond

#### 5.4.3 Cross-Arm Coupling Strength (Assumption A6)

```python
# Vary correlation between δ_{0,0} and δ_{1,0}
ρ ∈ [0.0, 0.3, 0.5, 0.7, 0.9, 1.0]
# δ_{1,0} = ρ * δ_{0,0} + √(1-ρ²) * η
```

**Expected**: Option B works when ρ ≥ 0.7, fails when ρ < 0.5

#### 5.4.4 Outcome Model Misspecification

```python
# True DGP: Y = f(X) + ε
# Test cases:
1. Linear truth, linear proxy → well-specified
2. Nonlinear truth, linear proxy → misspecified Stage 1
3. Interactions: Y = β'X + γ'(X ⊙ A·X) → treatment-covariate interactions
4. Heteroskedastic noise: Var(ε|X) = σ²(X) → non-constant variance
```

**Expected**: Flexible proxy models (RF/GBM) robust to misspecification

#### 5.4.5 Propensity Violations (Assumptions A2, A3)

```python
# Test cases:
1. Unequal randomization: e_c ∈ {0.3, 0.5, 0.7}
2. Mild overlap violation: e_c(x) ∈ [0.1, 0.9]
3. Severe overlap violation: e_c(x) ∈ [0.01, 0.99]
4. Unknown propensity: estimate ê_c(x) with error
```

**Expected**: DR robust to (1-2), fails at (3)

### 5.5 Comparative Baselines (Beyond Paper)

**Purpose**: Compare against state-of-the-art alternatives

| Baseline | Description | Reference |
|----------|-------------|-----------|
| **IPD-NMA** | Standard network meta-analysis | Dias et al. 2013 |
| **TMLE Transport** | Targeted learning with reweighting | van der Laan 2011 |
| **Causal Forest (Target Only)** | No transfer, rich target data | Wager & Athey 2018 |
| **Simple Transfer** | Train on source, test on target | Baseline |
| **AIPW Multi-Site** | Augmented IPW across sites | Robins et al. 1995 |
| **Multi-Task Learner** | Bastani et al. 2021 proxy-gold | Bastani et al. 2021 |

### 5.6 Sensitivity Analyses

#### 5.6.1 Cross-Fitting Fold Number

```python
K ∈ [2, 3, 5, 10]
# Measure bias-variance tradeoff
```

#### 5.6.2 LASSO Path Stability

```python
# Perturb gold samples via bootstrap
# Check if selected features are stable
```

#### 5.6.3 Negative Controls

```python
# Include known null covariates
# Check if δ̂ correctly zeros them out
```

---

## 6. Synthetic Data Generation (Improved)

### 6.1 DGP Specification

```python
def generate_multi_site_rct(
    n_sources=3,
    n_target=200,
    n_per_source=500,
    p=10,
    p_eff=3,  # effect modifiers
    s_bias=2,  # sparsity of transport bias
    shift_scale=0.5,
    rho_cross_arm=0.8,  # correlation between δ_0 and δ_1
    noise_std=0.5,
    disconnected=True,
    seed=42
):
    """
    Generate synthetic multi-center RCT with controlled properties.
    
    Ground Truth Models:
    --------------------
    μ_0(x) = β_0' x  (global baseline)
    τ(x) = β_τ' x[:p_eff]  (treatment effect, only on effect modifiers)
    μ_{0,c}(x) = μ_0(x) + δ_{0,c}' x  (site-specific baseline)
    μ_{1,c}(x) = μ_0(x) + τ(x) + δ_{1,c}' x  (site-specific treated)
    
    where:
    - δ_{a,c} has sparsity ||δ||_0 = s_bias
    - δ_{1,c} = ρ * δ_{0,c} + √(1-ρ²) * η_c  (cross-arm coupling)
    
    Returns:
    --------
    data : dict with keys
        - 'source': list of site dicts
        - 'target': dict for target site
        - 'true_params': ground truth parameters
    """
    np.random.seed(seed)
    
    # Global parameters (shared across sites)
    beta_0 = np.zeros(p)
    beta_0[:2] = [0.5, -0.3]  # sparse baseline
    
    beta_tau = np.zeros(p)
    beta_tau[:p_eff] = [0.6, 0.4, -0.3]  # effect modifiers
    
    def generate_site(n, site_id, shift_mean, is_target):
        # Covariates with site shift
        X = np.random.randn(n, p) + shift_mean
        
        # Randomization
        A = np.random.binomial(1, 0.5, n)
        e = np.full(n, 0.5)
        
        # Site-specific transport bias (sparse)
        delta_0 = np.zeros(p)
        idx_nonzero = np.random.choice(p, s_bias, replace=False)
        delta_0[idx_nonzero] = np.random.randn(s_bias) * 0.4
        
        # Cross-arm coupling
        delta_1 = rho_cross_arm * delta_0 + \
                  np.sqrt(1 - rho_cross_arm**2) * \
                  np.random.randn(p) * 0.3
        delta_1[np.abs(delta_1) < 0.1] = 0  # enforce sparsity
        
        # Potential outcomes
        mu_0_global = X @ beta_0
        tau = X @ beta_tau
        mu_0 = mu_0_global + X @ delta_0
        mu_1 = mu_0_global + tau + X @ delta_1
        
        # Observed outcome
        Y = A * mu_1 + (1 - A) * mu_0 + np.random.randn(n) * noise_std
        
        return {
            'X': X, 'A': A, 'Y': Y, 'propensity': e,
            'mu_0': mu_0, 'mu_1': mu_1, 'tau': tau,
            'delta_0': delta_0, 'delta_1': delta_1,
            'site_id': site_id
        }
    
    # Generate sources
    data = {'source': []}
    for c in range(1, n_sources + 1):
        shift = np.random.randn(p) * shift_scale
        site = generate_site(n_per_source, c, shift, False)
        data['source'].append(site)
    
    # Generate target
    shift_target = np.random.randn(p) * shift_scale * 1.2
    target = generate_site(n_target, 0, shift_target, True)
    
    # Force disconnected if requested
    if disconnected:
        mask_placebo = (target['A'] == 0)
        for key in ['X', 'A', 'Y', 'propensity', 'mu_0', 'mu_1', 'tau']:
            target[key] = target[key][mask_placebo]
    
    data['target'] = target
    data['true_params'] = {
        'beta_0': beta_0,
        'beta_tau': beta_tau,
        'rho': rho_cross_arm
    }
    
    return data
```

---

## 7. Implementation Checklist

- [ ] Implement Stage 1 with multiple proxy learner options
- [ ] Implement Stage 2 with LassoCV and sparse correction
- [ ] Implement Stage 3 with cross-fitting (StratifiedKFold)
- [ ] Add Option A vs Option B logic
- [ ] Implement full PlaceboAnchoredDRLearner class
- [ ] Add comprehensive input validation
- [ ] Implement evaluation metrics
- [ ] Create synthetic data generator with DGP parameters
- [ ] Run core ablation tests (4-5 methods)
- [ ] Run robustness checks (5-6 dimensions)
- [ ] Create visualization suite (box plots, calibration plots)
- [ ] Write unit tests for each stage
- [ ] Document all hyperparameters and their effects
- [ ] Add logging and diagnostic outputs

---

## 8. Key Implementation Decisions

1. **Cross-fitting in Stage 2 vs Stage 3**:
   - Current approach: Cross-fit in Stage 3 only
   - Alternative: Nested cross-fitting in Stage 2
   - Trade-off: Computational cost vs bias reduction

2. **LASSO lambda selection**:
   - Use LassoCV with 5-fold CV on gold samples
   - Consider stability selection for feature importance

3. **Propensity estimation**:
   - RCTs have known propensities (design feature)
   - For robustness checks, can add estimation error

4. **Handling extreme propensities**:
   - Clip to [ε, 1-ε] with ε=0.01
   - Or use overlap weights

5. **Missing data**:
   - Not addressed in paper
   - Could add multiple imputation wrapper

---

## 9. Differences from Current Implementation

The current `scratch_estimator.py` has several differences from the paper:

1. **No cross-fitting in Stage 2**: Current implementation fits corrections once, not per fold
2. **Option A/B logic incomplete**: Needs better handling of disconnected setting
3. **Intercept fitting**: Current uses `fit_intercept=False`, paper suggests including it
4. **Evaluation metrics**: Missing calibration RMSE, only has PEHE and ATE error
5. **Robustness checks**: Not implemented in current version

These should be addressed in the updated implementation.
