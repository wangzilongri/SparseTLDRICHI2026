"""
Transport and IPD Meta-Analysis Baselines

Implements baselines for comparison as requested by reviewers. Each method
is documented with its paper reference and exact implementation details.

## Paper References:

1. Dahabreh et al. (2023) "Efficient and robust methods for causally 
   interpretable meta-analysis: Synthesizing evidence from multiple 
   randomized trials"
   - Defines g-formula, IPW, and augmented (DR) transport estimators
   - Key equations: Eq. (8) for augmented estimator

2. Hong et al. (2025) "Estimating target population treatment effects 
   in meta-analysis with individual participant data"
   - Selection weights: w = ê(X) / (1-ê(X)) for RCT participants (Eq. 3)
   - Two-stage: per-trial TATE estimation then meta-analytic pooling

3. Rott (2024) "Causally interpretable meta-analysis"
   - Outcome-model transport: fit g_a on studies, average on target X
   - φ̂(a,a') = mean_{target X}[ĝ_a(X) - ĝ_{a'}(X)]

## Important Notes:

- Transport estimators naturally estimate ATE/TATE, not pointwise CATE
- For CATE prediction benchmarks, we use weighted outcome models per arm
- Methods are adapted to return τ̂(x) = μ̂₁(x) - μ̂₀(x) for PEHE evaluation
- ATE estimates are also available via estimate_tate() methods
"""

import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.linear_model import LogisticRegression, Ridge, LassoCV
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from typing import Optional, Dict, Any, Tuple
import warnings


# =============================================================================
# IPW Transport Estimator (Hong et al. 2025)
# =============================================================================

class IPWTransportEstimator(BaseEstimator, RegressorMixin):
    """
    Inverse Probability Weighting (IPW) Transport Estimator.
    
    Implements Hong et al. (2025) selection weighting approach:
    
    ALGORITHM:
    1. Stack source (S=0) + target (S=1) covariates
    2. Fit selection model: ê(x) = P(S=1 | X=x)
    3. For source units, compute weights: w = ê(X) / (1-ê(X))  [Hong Eq. 3]
    4. Fit weighted outcome models μ̂_a(x) on source with weights w
    5. Predict CATE as τ̂(x) = μ̂₁(x) - μ̂₀(x)
    
    For TATE estimation, we compute:
        TATE = Σᵢ wᵢ Aᵢ Yᵢ / Σᵢ wᵢ Aᵢ - Σᵢ wᵢ (1-Aᵢ) Yᵢ / Σᵢ wᵢ (1-Aᵢ)
    
    NOTE: This is adapted for CATE prediction benchmarks. The true IPW transport
    estimator naturally estimates ATE/TATE, not pointwise CATE. We use weighted
    outcome regression to enable CATE prediction for PEHE evaluation.
    
    References:
        Hong et al. (2025) Eq. (3): w_j = ê_j / (1 - ê_j)
        Westreich et al. (2017) for transportability framework
    """
    
    def __init__(self, stabilized: bool = True, trim_weights: float = 0.01,
                 random_state: int = 42):
        """
        Parameters
        ----------
        stabilized : bool
            Use stabilized IPW weights (multiply by marginal odds)
        trim_weights : float
            Trim propensity scores to [trim, 1-trim] for stability
        random_state : int
            Random seed
        """
        self.stabilized = stabilized
        self.trim_weights = trim_weights
        self.random_state = random_state
        
        # Fitted components
        self.site_model_ = None
        self.outcome_model_0_ = None
        self.outcome_model_1_ = None
        self.scaler_ = None
        self.weights_ = None
        self.tate_ = None  # Estimated TATE
        
    def fit(self, X_source, A_source, Y_source, c_source,
            X_target, A_target=None, Y_target=None, **kwargs):
        """
        Fit IPW transport estimator following Hong et al. (2025).
        
        Parameters
        ----------
        X_source : array (n_source, p)
            Source covariates (from RCTs/trials)
        A_source : array (n_source,)
            Source treatment indicators
        Y_source : array (n_source,)
            Source outcomes
        c_source : array (n_source,)
            Source site indicators (not used in basic IPW)
        X_target : array (n_target, p)
            Target covariates (target population)
        A_target, Y_target : arrays, optional
            Target outcomes (not used for estimation, only for evaluation)
        """
        n_source = len(X_source)
        n_target = len(X_target)
        
        # Scale features
        self.scaler_ = StandardScaler()
        X_source_scaled = self.scaler_.fit_transform(X_source)
        X_target_scaled = self.scaler_.transform(X_target)
        
        # Step 1: Stack source (S=0) + target (S=1)
        # Following Hong notation: S=0 for trial, S=1 for target
        X_combined = np.vstack([X_source_scaled, X_target_scaled])
        S_combined = np.concatenate([
            np.zeros(n_source),  # S=0 for source/trials
            np.ones(n_target)    # S=1 for target
        ])
        
        # Step 2: Fit selection model ê(x) = P(S=1 | X)
        self.site_model_ = LogisticRegression(
            C=1.0, max_iter=1000, random_state=self.random_state
        )
        self.site_model_.fit(X_combined, S_combined)
        
        # Step 3: Compute Hong selection weights for source: w = ê/(1-ê)
        ps_source = self.site_model_.predict_proba(X_source_scaled)[:, 1]
        ps_source = np.clip(ps_source, self.trim_weights, 1 - self.trim_weights)
        
        # Hong Eq. (3): w = ê / (1 - ê)
        weights = ps_source / (1 - ps_source)
        
        if self.stabilized:
            # Stabilized weights: multiply by marginal odds ratio
            p_target = n_target / (n_source + n_target)
            weights = weights * (1 - p_target) / p_target
            
        # Normalize weights to sum to n_source
        weights = weights / weights.sum() * n_source
        self.weights_ = weights
        
        # Step 4: Fit weighted outcome models per arm
        mask_0 = A_source == 0
        mask_1 = A_source == 1
        
        self.outcome_model_0_ = Ridge(alpha=1.0)
        self.outcome_model_1_ = Ridge(alpha=1.0)
        
        if mask_0.sum() > 0:
            self.outcome_model_0_.fit(
                X_source_scaled[mask_0], 
                Y_source[mask_0],
                sample_weight=weights[mask_0]
            )
        
        if mask_1.sum() > 0:
            self.outcome_model_1_.fit(
                X_source_scaled[mask_1],
                Y_source[mask_1],
                sample_weight=weights[mask_1]
            )
        
        # Also compute TATE for ATE evaluation
        self.tate_ = self._compute_tate(A_source, Y_source, weights)
        
        return self
    
    def _compute_tate(self, A, Y, weights):
        """Compute weighted TATE (Horvitz-Thompson style)."""
        mask_1 = A == 1
        mask_0 = A == 0
        
        # Weighted mean for each arm
        if weights[mask_1].sum() > 0:
            mu1_weighted = np.sum(weights[mask_1] * Y[mask_1]) / np.sum(weights[mask_1])
        else:
            mu1_weighted = 0
            
        if weights[mask_0].sum() > 0:
            mu0_weighted = np.sum(weights[mask_0] * Y[mask_0]) / np.sum(weights[mask_0])
        else:
            mu0_weighted = 0
            
        return mu1_weighted - mu0_weighted
    
    def predict(self, X):
        """
        Predict CATE using weighted outcome models.
        
        NOTE: This is an adaptation for CATE benchmarks. True IPW transport
        estimates ATE/TATE, not pointwise CATE. Use estimate_tate() for ATE.
        """
        X_scaled = self.scaler_.transform(X)
        mu_0 = self.outcome_model_0_.predict(X_scaled)
        mu_1 = self.outcome_model_1_.predict(X_scaled)
        return mu_1 - mu_0
    
    def estimate_tate(self):
        """Return the estimated TATE (target average treatment effect)."""
        return self.tate_
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        return {
            'method': 'IPWTransport',
            'stabilized': self.stabilized,
            'tate': self.tate_,
            'effective_sample_size': 1.0 / np.sum((self.weights_ / self.weights_.sum()) ** 2) if self.weights_ is not None else None
        }


# =============================================================================
# Entropy Balancing Estimator
# =============================================================================

class EntropyBalancingEstimator(BaseEstimator, RegressorMixin):
    """
    Entropy Balancing Transport Estimator.
    
    Alternative to IPW that finds weights by solving an optimization problem
    to exactly balance covariate moments between source and target.
    
    ALGORITHM:
    1. Compute target covariate means: m_target = mean(X_target)
    2. Find weights w for source that minimize entropy: min Σ w log(w)
       subject to: Σ w X_source = m_target (moment matching)
    3. Fit weighted outcome models with balancing weights
    4. Predict CATE as τ̂(x) = μ̂₁(x) - μ̂₀(x)
    
    References:
        Hainmueller (2012) "Entropy Balancing for Causal Effects"
    """
    
    def __init__(self, max_iter: int = 100, tol: float = 1e-6,
                 random_state: int = 42):
        self.max_iter = max_iter
        self.tol = tol
        self.random_state = random_state
        
        self.weights_ = None
        self.outcome_model_0_ = None
        self.outcome_model_1_ = None
        self.scaler_ = None
        self.tate_ = None
        
    def _entropy_balance(self, X_source, X_target):
        """
        Compute entropy balancing weights via iterative algorithm.
        
        Solves: min_w Σ w log(w) s.t. Σ w X_source = mean(X_target), Σ w = 1
        Using Lagrangian dual approach.
        """
        n_source = len(X_source)
        
        # Target moments (means)
        target_means = X_target.mean(axis=0)
        
        # Initialize weights uniformly
        weights = np.ones(n_source) / n_source
        
        # Lagrange multipliers
        n_features = X_source.shape[1]
        lambdas = np.zeros(n_features)
        
        for iteration in range(self.max_iter):
            # Update weights: w_i ∝ exp(-λ^T x_i)
            log_weights = -X_source @ lambdas
            log_weights = log_weights - log_weights.max()  # numerical stability
            weights = np.exp(log_weights)
            weights = weights / weights.sum()
            
            # Check balance
            current_means = (weights[:, None] * X_source).sum(axis=0)
            imbalance = current_means - target_means
            
            if np.max(np.abs(imbalance)) < self.tol:
                break
                
            # Gradient step on lambdas
            step_size = 0.5 / (iteration + 1)
            lambdas = lambdas + step_size * imbalance
        
        return weights * n_source  # Scale to sum to n_source
    
    def fit(self, X_source, A_source, Y_source, c_source,
            X_target, A_target=None, Y_target=None, **kwargs):
        """Fit entropy balancing estimator."""
        # Scale features
        self.scaler_ = StandardScaler()
        X_source_scaled = self.scaler_.fit_transform(X_source)
        X_target_scaled = self.scaler_.transform(X_target)
        
        # Compute balancing weights
        self.weights_ = self._entropy_balance(X_source_scaled, X_target_scaled)
        
        # Fit weighted outcome models
        mask_0 = A_source == 0
        mask_1 = A_source == 1
        
        self.outcome_model_0_ = Ridge(alpha=1.0)
        self.outcome_model_1_ = Ridge(alpha=1.0)
        
        if mask_0.sum() > 0:
            self.outcome_model_0_.fit(
                X_source_scaled[mask_0],
                Y_source[mask_0],
                sample_weight=self.weights_[mask_0]
            )
            
        if mask_1.sum() > 0:
            self.outcome_model_1_.fit(
                X_source_scaled[mask_1],
                Y_source[mask_1],
                sample_weight=self.weights_[mask_1]
            )
        
        # Compute TATE
        self.tate_ = self._compute_tate(A_source, Y_source, self.weights_)
        
        return self
    
    def _compute_tate(self, A, Y, weights):
        """Compute weighted TATE."""
        mask_1 = A == 1
        mask_0 = A == 0
        
        if weights[mask_1].sum() > 0:
            mu1 = np.sum(weights[mask_1] * Y[mask_1]) / np.sum(weights[mask_1])
        else:
            mu1 = 0
            
        if weights[mask_0].sum() > 0:
            mu0 = np.sum(weights[mask_0] * Y[mask_0]) / np.sum(weights[mask_0])
        else:
            mu0 = 0
            
        return mu1 - mu0
    
    def predict(self, X):
        """Predict CATE using balanced outcome models."""
        X_scaled = self.scaler_.transform(X)
        mu_0 = self.outcome_model_0_.predict(X_scaled)
        mu_1 = self.outcome_model_1_.predict(X_scaled)
        return mu_1 - mu_0
    
    def estimate_tate(self):
        """Return the estimated TATE."""
        return self.tate_
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        return {
            'method': 'EntropyBalancing',
            'tate': self.tate_,
            'effective_sample_size': 1.0 / np.sum((self.weights_ / self.weights_.sum()) ** 2) if self.weights_ is not None else None
        }


# =============================================================================
# AIPW Transport Estimator (Dahabreh et al. 2023)
# =============================================================================

class AIPWTransportEstimator(BaseEstimator, RegressorMixin):
    """
    Augmented IPW (AIPW/DR) Transport Estimator.
    
    Implements Dahabreh et al. (2023) Eq. (8) augmented estimator for TATE.
    
    ALGORITHM (Dahabreh Eq. 8):
    
    For each arm a ∈ {0, 1}, the augmented estimator is:
    
    ψ̂_aug(a) = (1/n_target) Σᵢ [
        I(Rᵢ=1, Aᵢ=a) × ((1-p̂(Xᵢ)) / (p̂(Xᵢ) × ê_a(Xᵢ))) × (Yᵢ - ĝ_a(Xᵢ))
        + I(Rᵢ=0) × ĝ_a(Xᵢ)
    ]
    
    Where:
    - R=1: in trials (source); R=0: in target
    - p̂(x) = P(R=1|X=x) selection/participation model
    - ê_a(x) = P(A=a|X, R=1) treatment propensity in trials (or P(A=a|X, c, R=1)
      if trial_specific_propensity=True)
    - ĝ_a(x) = E[Y|X=x, R=1, A=a] outcome model from trials
    
    TATE = ψ̂_aug(1) - ψ̂_aug(0)
    
    TRIAL-SPECIFIC PROPENSITY (Dahabreh et al. recommend):
    If randomization ratios vary across trials, set trial_specific_propensity=True
    to include site indicators in the propensity model. This prevents bias from
    pooling trials with different randomization protocols.
    
    NOTE: AIPW naturally estimates ATE/TATE, not pointwise CATE. For CATE
    prediction benchmarks, we use the outcome model component ĝ₁(x) - ĝ₀(x).
    The proper TATE estimate is available via estimate_tate().
    
    References:
        Dahabreh et al. (2023) Eq. (8) - Augmented transport estimator
        Dahabreh et al. (2019) - DR transport foundations
    """
    
    def __init__(
        self,
        trim_weights: float = 0.01,
        random_state: int = 42,
        trial_specific_propensity: bool = False
    ):
        """
        Parameters
        ----------
        trim_weights : float
            Clip propensity scores to [trim, 1-trim] for stability
        random_state : int
            Random seed
        trial_specific_propensity : bool
            If True, include site indicators in propensity model to handle
            trial-specific randomization ratios (Dahabreh et al. recommend this
            when trials have different randomization protocols)
        """
        self.trim_weights = trim_weights
        self.random_state = random_state
        self.trial_specific_propensity = trial_specific_propensity
        
        self.site_model_ = None       # p̂(x) = P(R=1|X)
        self.prop_model_ = None       # ê_a(x) = P(A=1|X, R=1) or P(A=1|X, c, R=1)
        self.prop_encoder_ = None     # OneHot encoder for trial-specific propensity
        self.outcome_model_0_ = None  # ĝ₀(x)
        self.outcome_model_1_ = None  # ĝ₁(x)
        self.scaler_ = None
        self.tate_ = None
        self.psi_1_ = None  # ψ̂_aug(1)
        self.psi_0_ = None  # ψ̂_aug(0)
        
    def fit(self, X_source, A_source, Y_source, c_source,
            X_target, A_target=None, Y_target=None, **kwargs):
        """
        Fit AIPW transport estimator following Dahabreh et al. (2023).
        """
        n_source = len(X_source)
        n_target = len(X_target)
        
        # Scale features
        self.scaler_ = StandardScaler()
        X_source_scaled = self.scaler_.fit_transform(X_source)
        X_target_scaled = self.scaler_.transform(X_target)
        
        # Step 1: Fit selection model p̂(x) = P(R=1|X)
        # R=1 for source (trials), R=0 for target
        X_combined = np.vstack([X_source_scaled, X_target_scaled])
        R_combined = np.concatenate([
            np.ones(n_source),   # R=1 for source
            np.zeros(n_target)   # R=0 for target
        ])
        
        self.site_model_ = LogisticRegression(
            C=1.0, max_iter=1000, random_state=self.random_state
        )
        self.site_model_.fit(X_combined, R_combined)
        
        # Step 2: Fit treatment propensity in trials ê_a(x) = P(A=1|X, R=1)
        # If trial_specific_propensity=True, include site indicators to handle
        # different randomization ratios across trials (Dahabreh et al. recommend)
        self.prop_model_ = LogisticRegression(
            C=1.0, max_iter=1000, random_state=self.random_state
        )
        
        if self.trial_specific_propensity:
            if c_source is None:
                raise ValueError("c_source must be provided when trial_specific_propensity=True")
            
            # Use OneHotEncoder for site indicators in propensity model
            # Handle sklearn version differences for sparse_output arg
            try:
                self.prop_encoder_ = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
            except TypeError:
                self.prop_encoder_ = OneHotEncoder(sparse=False, handle_unknown="ignore")
            
            C_oh = self.prop_encoder_.fit_transform(np.asarray(c_source).reshape(-1, 1))
            X_prop = np.hstack([X_source_scaled, C_oh])
            self.prop_model_.fit(X_prop, A_source)
        else:
            self.prop_model_.fit(X_source_scaled, A_source)
        
        # Step 3: Fit outcome models ĝ_a(x) = E[Y|X, R=1, A=a]
        mask_0 = A_source == 0
        mask_1 = A_source == 1
        
        self.outcome_model_0_ = Ridge(alpha=1.0)
        self.outcome_model_1_ = Ridge(alpha=1.0)
        
        self.outcome_model_0_.fit(X_source_scaled[mask_0], Y_source[mask_0])
        self.outcome_model_1_.fit(X_source_scaled[mask_1], Y_source[mask_1])
        
        # Step 4: Compute augmented estimator (Dahabreh Eq. 8)
        self._compute_augmented_estimator(
            X_source_scaled, A_source, Y_source, X_target_scaled, c_source=c_source
        )
        
        return self
    
    def _compute_augmented_estimator(self, X_source, A_source, Y_source, X_target, c_source=None):
        """
        Compute Dahabreh Eq. (8) augmented estimator.
        
        ψ̂_aug(a) = (1/n_target) Σᵢ [
            I(Rᵢ=1, Aᵢ=a) × ((1-p̂(Xᵢ)) / (p̂(Xᵢ) × ê_a(Xᵢ))) × (Yᵢ - ĝ_a(Xᵢ))
            + I(Rᵢ=0) × ĝ_a(Xᵢ)
        ]
        """
        n_source = len(X_source)
        n_target = len(X_target)
        
        # Get predictions for source
        p_source = self.site_model_.predict_proba(X_source)[:, 1]  # P(R=1|X)
        p_source = np.clip(p_source, self.trim_weights, 1 - self.trim_weights)
        
        # Get treatment propensity ê(x) or ê(x,c) if trial-specific
        if self.prop_encoder_ is not None:
            if c_source is None:
                raise ValueError("c_source must be provided when trial_specific_propensity=True")
            C_oh = self.prop_encoder_.transform(np.asarray(c_source).reshape(-1, 1))
            X_prop = np.hstack([X_source, C_oh])
            e_source = self.prop_model_.predict_proba(X_prop)[:, 1]  # P(A=1|X, c, R=1)
        else:
            e_source = self.prop_model_.predict_proba(X_source)[:, 1]  # P(A=1|X, R=1)
        e_source = np.clip(e_source, self.trim_weights, 1 - self.trim_weights)
        
        g0_source = self.outcome_model_0_.predict(X_source)  # ĝ₀(X) for source
        g1_source = self.outcome_model_1_.predict(X_source)  # ĝ₁(X) for source
        
        # Get predictions for target
        g0_target = self.outcome_model_0_.predict(X_target)  # ĝ₀(X) for target
        g1_target = self.outcome_model_1_.predict(X_target)  # ĝ₁(X) for target
        
        # Compute ψ̂_aug(1) - treated arm
        # Trial contribution: I(R=1, A=1) × ((1-p̂)/(p̂ × ê₁)) × (Y - ĝ₁)
        mask_1 = A_source == 1
        weights_1 = (1 - p_source) / (p_source * e_source)
        trial_term_1 = np.sum(mask_1 * weights_1 * (Y_source - g1_source))
        
        # Target contribution: I(R=0) × ĝ₁
        target_term_1 = np.sum(g1_target)
        
        self.psi_1_ = (trial_term_1 + target_term_1) / n_target
        
        # Compute ψ̂_aug(0) - control arm
        # Trial contribution: I(R=1, A=0) × ((1-p̂)/(p̂ × (1-ê₁))) × (Y - ĝ₀)
        mask_0 = A_source == 0
        weights_0 = (1 - p_source) / (p_source * (1 - e_source))
        trial_term_0 = np.sum(mask_0 * weights_0 * (Y_source - g0_source))
        
        # Target contribution: I(R=0) × ĝ₀
        target_term_0 = np.sum(g0_target)
        
        self.psi_0_ = (trial_term_0 + target_term_0) / n_target
        
        # TATE = ψ̂_aug(1) - ψ̂_aug(0)
        self.tate_ = self.psi_1_ - self.psi_0_
    
    def predict(self, X):
        """
        Predict CATE using outcome model component.
        
        NOTE: AIPW is an ATE estimator, not CATE. This returns the outcome
        model difference ĝ₁(x) - ĝ₀(x) for CATE benchmarking purposes.
        Use estimate_tate() for the proper DR transport ATE estimate.
        """
        X_scaled = self.scaler_.transform(X)
        mu_0 = self.outcome_model_0_.predict(X_scaled)
        mu_1 = self.outcome_model_1_.predict(X_scaled)
        return mu_1 - mu_0
    
    def estimate_tate(self):
        """Return the Dahabreh Eq. (8) augmented TATE estimate."""
        return self.tate_
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        return {
            'method': 'AIPWTransport (Dahabreh Eq. 8)',
            'tate': self.tate_,
            'psi_1': self.psi_1_,
            'psi_0': self.psi_0_
        }


# =============================================================================
# Outcome Model Transport (Rott 2024)
# =============================================================================

class OutcomeModelTransportEstimator(BaseEstimator, RegressorMixin):
    """
    Outcome Model Transport Estimator (Rott 2024).
    
    Implements the outcome-model transport approach:
    
    ALGORITHM:
    1. Pool all trial/source IPD: {(X, A, Y)}
    2. Fit outcome models: ĝ_a(x) = E[Y | X=x, A=a] using pooled data
    3. Transport to target by averaging predictions on target X:
       φ̂(1,0) = mean_{target X}[ĝ₁(X) - ĝ₀(X)]
    
    This is the simplest "transport" approach - it relies solely on the
    outcome model being correctly specified and transportable.
    
    For CATE prediction: τ̂(x) = ĝ₁(x) - ĝ₀(x)
    
    References:
        Rott (2024) - Causally interpretable meta-analysis
        "Outcome model approach: fit g_a on studies, average on target X"
    """
    
    def __init__(self, include_site: bool = False, random_state: int = 42):
        """
        Parameters
        ----------
        include_site : bool
            If True, include site indicators in outcome model
        """
        self.include_site = include_site
        self.random_state = random_state
        
        self.outcome_model_0_ = None
        self.outcome_model_1_ = None
        self.scaler_ = None
        self.n_sites_ = None
        self.tate_ = None
        
    def fit(self, X_source, A_source, Y_source, c_source,
            X_target, A_target=None, Y_target=None, **kwargs):
        """Fit outcome model transport estimator."""
        # Scale features
        self.scaler_ = StandardScaler()
        X_source_scaled = self.scaler_.fit_transform(X_source)
        X_target_scaled = self.scaler_.transform(X_target)
        
        # Optionally add site indicators
        if self.include_site:
            self.n_sites_ = int(c_source.max()) + 1
            site_dummies = np.zeros((len(X_source), self.n_sites_))
            for i, s in enumerate(c_source):
                site_dummies[i, int(s)] = 1
            X_aug = np.hstack([X_source_scaled, site_dummies])
        else:
            X_aug = X_source_scaled
            self.n_sites_ = 0
        
        # Fit outcome models ĝ_a(x) on pooled source data
        mask_0 = A_source == 0
        mask_1 = A_source == 1
        
        self.outcome_model_0_ = Ridge(alpha=1.0)
        self.outcome_model_1_ = Ridge(alpha=1.0)
        
        self.outcome_model_0_.fit(X_aug[mask_0], Y_source[mask_0])
        self.outcome_model_1_.fit(X_aug[mask_1], Y_source[mask_1])
        
        # Compute TATE by averaging on target X
        # For target, use zero site dummies (marginalizes over sites)
        if self.include_site:
            site_zeros = np.zeros((len(X_target), self.n_sites_))
            X_target_aug = np.hstack([X_target_scaled, site_zeros])
        else:
            X_target_aug = X_target_scaled
        
        g0_target = self.outcome_model_0_.predict(X_target_aug)
        g1_target = self.outcome_model_1_.predict(X_target_aug)
        
        # φ̂(1,0) = mean_{target X}[ĝ₁(X) - ĝ₀(X)]
        self.tate_ = np.mean(g1_target - g0_target)
        
        return self
    
    def predict(self, X):
        """Predict CATE as ĝ₁(x) - ĝ₀(x)."""
        X_scaled = self.scaler_.transform(X)
        
        if self.include_site and self.n_sites_ > 0:
            # For prediction, use zero site dummies
            site_zeros = np.zeros((len(X), self.n_sites_))
            X_aug = np.hstack([X_scaled, site_zeros])
        else:
            X_aug = X_scaled
        
        mu_0 = self.outcome_model_0_.predict(X_aug)
        mu_1 = self.outcome_model_1_.predict(X_aug)
        return mu_1 - mu_0
    
    def estimate_tate(self):
        """Return the outcome-model TATE estimate."""
        return self.tate_
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        return {
            'method': 'OutcomeModelTransport (Rott)',
            'include_site': self.include_site,
            'n_sites': self.n_sites_,
            'tate': self.tate_
        }


# =============================================================================
# Hong Two-Stage Meta-Analysis (Hong et al. 2025)
# =============================================================================

class HongTwoStageEstimator(BaseEstimator, RegressorMixin):
    """
    Hong et al. (2025) Two-Stage TATE Estimator.
    
    Implements the full Hong procedure for IPD meta-analysis with 
    target population generalizability:
    
    ALGORITHM:
    
    FIRST STAGE (per-trial):
    For each trial i:
    1. Stack trial i + target covariates
    2. Fit selection model: êᵢ(x) = P(S=1|X)  where S=0 for trial, S=1 for target
    3. Compute weights: wᵢⱼ = êᵢ(Xⱼ) / (1 - êᵢ(Xⱼ)) for trial j participants
    4. Estimate TATEᵢ using weighted estimator within trial i
    
    SECOND STAGE (meta-analysis):
    5. Pool {TATEᵢ} using random-effects meta-analysis (DerSimonian-Laird)
    
    For CATE prediction: We use the pooled TATE as a constant prediction
    (or weighted average of per-trial outcome models).
    
    References:
        Hong et al. (2025) - Full two-stage procedure
    """
    
    def __init__(self, meta_method: str = 'random', random_state: int = 42):
        """
        Parameters
        ----------
        meta_method : str
            'fixed' or 'random' effects meta-analysis
        """
        self.meta_method = meta_method
        self.random_state = random_state
        
        self.site_tates_ = None      # Per-site TATE estimates
        self.site_variances_ = None  # Per-site variance estimates
        self.pooled_tate_ = None     # Meta-analyzed TATE
        self.tau2_ = None            # Between-study variance
        self.scaler_ = None
        self.outcome_model_0_ = None
        self.outcome_model_1_ = None
        
    def fit(self, X_source, A_source, Y_source, c_source,
            X_target, A_target=None, Y_target=None, **kwargs):
        """
        Fit Hong two-stage estimator.
        """
        # Scale features
        self.scaler_ = StandardScaler()
        X_source_scaled = self.scaler_.fit_transform(X_source)
        X_target_scaled = self.scaler_.transform(X_target)
        
        n_target = len(X_target)
        
        # Identify unique sites
        unique_sites = np.unique(c_source)
        n_sites = len(unique_sites)
        
        self.site_tates_ = []
        self.site_variances_ = []
        
        # FIRST STAGE: Per-site TATE estimation
        for site in unique_sites:
            site_mask = c_source == site
            X_site = X_source_scaled[site_mask]
            A_site = A_source[site_mask]
            Y_site = Y_source[site_mask]
            n_site = len(X_site)
            
            # Skip sites with too few samples or missing arms
            if n_site < 10 or np.sum(A_site == 0) < 2 or np.sum(A_site == 1) < 2:
                continue
            
            # Stack site + target for selection model
            X_combined = np.vstack([X_site, X_target_scaled])
            S_combined = np.concatenate([
                np.zeros(n_site),  # S=0 for trial
                np.ones(n_target)  # S=1 for target
            ])
            
            # Fit site-specific selection model
            site_model = LogisticRegression(C=1.0, max_iter=1000)
            try:
                site_model.fit(X_combined, S_combined)
            except:
                continue
            
            # Compute Hong weights for this site
            ps = site_model.predict_proba(X_site)[:, 1]
            ps = np.clip(ps, 0.01, 0.99)
            weights = ps / (1 - ps)
            weights = weights / weights.sum() * n_site
            
            # Weighted TATE estimate for this site
            mask_1 = A_site == 1
            mask_0 = A_site == 0
            
            mu1_w = np.sum(weights[mask_1] * Y_site[mask_1]) / np.sum(weights[mask_1])
            mu0_w = np.sum(weights[mask_0] * Y_site[mask_0]) / np.sum(weights[mask_0])
            tate_site = mu1_w - mu0_w
            
            # Variance estimate (simplified)
            var1 = np.var(Y_site[mask_1]) / np.sum(mask_1)
            var0 = np.var(Y_site[mask_0]) / np.sum(mask_0)
            var_site = var1 + var0
            
            self.site_tates_.append(tate_site)
            self.site_variances_.append(var_site)
        
        self.site_tates_ = np.array(self.site_tates_)
        self.site_variances_ = np.array(self.site_variances_)
        
        # SECOND STAGE: Meta-analysis
        if len(self.site_tates_) > 0:
            if self.meta_method == 'fixed':
                # Fixed effects: inverse-variance weighted average
                w = 1.0 / self.site_variances_
                self.pooled_tate_ = np.sum(w * self.site_tates_) / np.sum(w)
                self.tau2_ = 0.0
            else:
                # Random effects: DerSimonian-Laird
                self.pooled_tate_, self.tau2_ = self._dersimonian_laird(
                    self.site_tates_, self.site_variances_
                )
        else:
            self.pooled_tate_ = 0.0
            self.tau2_ = 0.0
        
        # Fit WEIGHTED outcome models for CATE prediction (consistent with Hong methodology)
        # Use pooled selection weights across all sites
        all_weights = np.ones(len(X_source))  # Default weights
        
        # Recompute weights for all source units using pooled selection model
        X_combined_all = np.vstack([X_source_scaled, X_target_scaled])
        S_combined_all = np.concatenate([
            np.zeros(len(X_source)),
            np.ones(n_target)
        ])
        
        pooled_selection_model = LogisticRegression(C=1.0, max_iter=1000)
        try:
            pooled_selection_model.fit(X_combined_all, S_combined_all)
            ps_source = pooled_selection_model.predict_proba(X_source_scaled)[:, 1]
            ps_source = np.clip(ps_source, 0.01, 0.99)
            all_weights = ps_source / (1 - ps_source)
            all_weights = all_weights / all_weights.sum() * len(X_source)
        except:
            pass  # Fall back to uniform weights
        
        mask_0 = A_source == 0
        mask_1 = A_source == 1
        
        self.outcome_model_0_ = Ridge(alpha=1.0)
        self.outcome_model_1_ = Ridge(alpha=1.0)
        
        # Fit with selection weights (consistent with TATE estimation)
        self.outcome_model_0_.fit(
            X_source_scaled[mask_0], Y_source[mask_0],
            sample_weight=all_weights[mask_0]
        )
        self.outcome_model_1_.fit(
            X_source_scaled[mask_1], Y_source[mask_1],
            sample_weight=all_weights[mask_1]
        )
        
        return self
    
    def _dersimonian_laird(self, effects, variances):
        """DerSimonian-Laird random effects meta-analysis."""
        k = len(effects)
        if k == 0:
            return 0.0, 0.0
        if k == 1:
            return effects[0], 0.0
        
        w = 1.0 / variances
        
        # Fixed effect estimate
        theta_fe = np.sum(w * effects) / np.sum(w)
        
        # Q statistic
        Q = np.sum(w * (effects - theta_fe) ** 2)
        
        # Between-study variance
        c = np.sum(w) - np.sum(w ** 2) / np.sum(w)
        tau2 = max(0, (Q - (k - 1)) / c)
        
        # Random effects estimate
        w_re = 1.0 / (variances + tau2)
        theta_re = np.sum(w_re * effects) / np.sum(w_re)
        
        return theta_re, tau2
    
    def predict(self, X):
        """
        Predict CATE using pooled outcome models.
        
        NOTE: The Hong procedure estimates a single TATE, not pointwise CATE.
        For CATE benchmarking, we return outcome model differences.
        """
        X_scaled = self.scaler_.transform(X)
        mu_0 = self.outcome_model_0_.predict(X_scaled)
        mu_1 = self.outcome_model_1_.predict(X_scaled)
        return mu_1 - mu_0
    
    def estimate_tate(self):
        """Return the meta-analyzed TATE estimate."""
        return self.pooled_tate_
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        return {
            'method': 'HongTwoStage',
            'meta_method': self.meta_method,
            'pooled_tate': self.pooled_tate_,
            'tau2': self.tau2_,
            'n_sites_included': len(self.site_tates_),
            'site_tates': self.site_tates_.tolist() if len(self.site_tates_) > 0 else []
        }


# =============================================================================
# IPD Random Effects Estimator (Standard Meta-Analysis)
# =============================================================================

class IPDRandomEffectsEstimator(BaseEstimator, RegressorMixin):
    """
    IPD Random Effects Meta-Analysis Estimator.
    
    Standard two-stage IPD meta-analysis:
    1. Estimate within-site treatment effects
    2. Pool using DerSimonian-Laird random effects
    
    NOTE: This is standard meta-analysis, NOT the causally-interpretable
    "transport to target" estimand. It estimates the average effect across
    studies, not the effect in a specific target population.
    
    For target-population inference, use HongTwoStageEstimator instead.
    
    References:
        Riley et al. (2021) - IPD meta-analysis methods
        DerSimonian & Laird (1986) - Random effects meta-analysis
    """
    
    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        
        self.site_effects_ = None
        self.site_variances_ = None
        self.pooled_effect_ = None
        self.tau2_ = None
        self.scaler_ = None
        self.outcome_model_0_ = None
        self.outcome_model_1_ = None
        
    def fit(self, X_source, A_source, Y_source, c_source,
            X_target, A_target=None, Y_target=None, **kwargs):
        """Fit IPD random effects model."""
        # Scale features
        self.scaler_ = StandardScaler()
        X_source_scaled = self.scaler_.fit_transform(X_source)
        
        # Stage 1: Within-site effect estimates
        unique_sites = np.unique(c_source)
        self.site_effects_ = []
        self.site_variances_ = []
        
        for site in unique_sites:
            site_mask = c_source == site
            A_site = A_source[site_mask]
            Y_site = Y_source[site_mask]
            
            n1 = np.sum(A_site == 1)
            n0 = np.sum(A_site == 0)
            
            if n1 < 2 or n0 < 2:
                continue
            
            # Simple difference in means
            mu1 = np.mean(Y_site[A_site == 1])
            mu0 = np.mean(Y_site[A_site == 0])
            effect = mu1 - mu0
            
            # Variance
            var1 = np.var(Y_site[A_site == 1], ddof=1) / n1
            var0 = np.var(Y_site[A_site == 0], ddof=1) / n0
            variance = var1 + var0
            
            self.site_effects_.append(effect)
            self.site_variances_.append(variance)
        
        self.site_effects_ = np.array(self.site_effects_)
        self.site_variances_ = np.array(self.site_variances_)
        
        # Stage 2: Random effects pooling
        if len(self.site_effects_) > 0:
            self.pooled_effect_, self.tau2_ = self._dersimonian_laird(
                self.site_effects_, self.site_variances_
            )
        else:
            self.pooled_effect_ = 0.0
            self.tau2_ = 0.0
        
        # Fit pooled outcome models for CATE prediction
        mask_0 = A_source == 0
        mask_1 = A_source == 1
        
        self.outcome_model_0_ = Ridge(alpha=1.0)
        self.outcome_model_1_ = Ridge(alpha=1.0)
        
        self.outcome_model_0_.fit(X_source_scaled[mask_0], Y_source[mask_0])
        self.outcome_model_1_.fit(X_source_scaled[mask_1], Y_source[mask_1])
        
        return self
    
    def _dersimonian_laird(self, effects, variances):
        """DerSimonian-Laird random effects meta-analysis."""
        k = len(effects)
        if k == 0:
            return 0.0, 0.0
        if k == 1:
            return effects[0], 0.0
        
        w = 1.0 / variances
        theta_fe = np.sum(w * effects) / np.sum(w)
        Q = np.sum(w * (effects - theta_fe) ** 2)
        c = np.sum(w) - np.sum(w ** 2) / np.sum(w)
        tau2 = max(0, (Q - (k - 1)) / c)
        
        w_re = 1.0 / (variances + tau2)
        theta_re = np.sum(w_re * effects) / np.sum(w_re)
        
        return theta_re, tau2
    
    def predict(self, X):
        """Predict CATE using pooled outcome models."""
        X_scaled = self.scaler_.transform(X)
        mu_0 = self.outcome_model_0_.predict(X_scaled)
        mu_1 = self.outcome_model_1_.predict(X_scaled)
        return mu_1 - mu_0
    
    def estimate_tate(self):
        """
        Return the pooled effect estimate.
        
        NOTE: This is the average effect across studies, not a target-population
        TATE. For target-population inference, use HongTwoStageEstimator.
        """
        return self.pooled_effect_
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        return {
            'method': 'IPDRandomEffects (standard MA, not target-specific)',
            'pooled_effect': self.pooled_effect_,
            'tau2': self.tau2_,
            'n_sites': len(self.site_effects_),
            'site_effects': self.site_effects_.tolist() if len(self.site_effects_) > 0 else []
        }


# =============================================================================
# DR-Learner Pooled (requires target treated)
# =============================================================================

class DRLearnerPooledEstimator(BaseEstimator, RegressorMixin):
    """
    Pooled DR-Learner for multi-site data.
    
    Standard doubly robust learner pooling all source + target data.
    Requires target treated outcomes for proper DR estimation.
    
    ALGORITHM:
    1. Pool source + target data
    2. Fit propensity model P(A=1|X) on pooled data
    3. Fit outcome models μ̂_a(x) on pooled data
    4. Compute DR pseudo-outcomes on pooled data
    5. Regress pseudo-outcomes on X to get CATE model
    
    NOTE: This is NOT a transport estimator - it requires target treated
    outcomes and estimates effects in the pooled population.
    """
    
    def __init__(self, include_site: bool = True, random_state: int = 42):
        self.include_site = include_site
        self.random_state = random_state
        
        self.propensity_model_ = None
        self.outcome_model_0_ = None
        self.outcome_model_1_ = None
        self.cate_model_ = None
        self.scaler_ = None
        self.n_sites_ = None
        
    def fit(self, X_source, A_source, Y_source, c_source,
            X_target, A_target=None, Y_target=None, 
            propensity_source=None, propensity_target=None, **kwargs):
        """Fit pooled DR-Learner."""
        # Need target treated data
        if A_target is None or Y_target is None:
            raise ValueError("DRLearnerPooled requires target treated data")
        
        # Pool source and target
        X_all = np.vstack([X_source, X_target])
        A_all = np.concatenate([A_source, A_target])
        Y_all = np.concatenate([Y_source, Y_target])
        
        # Site indicators: source sites + target as new site
        self.n_sites_ = int(c_source.max()) + 2
        c_all = np.concatenate([c_source, np.full(len(X_target), self.n_sites_ - 1)])
        
        # Scale features
        self.scaler_ = StandardScaler()
        X_scaled = self.scaler_.fit_transform(X_all)
        
        # Augment with site if requested
        if self.include_site:
            site_dummies = np.zeros((len(X_all), self.n_sites_))
            for i, s in enumerate(c_all):
                site_dummies[i, int(s)] = 1
            X_aug = np.hstack([X_scaled, site_dummies])
        else:
            X_aug = X_scaled
        
        # Propensity model
        self.propensity_model_ = LogisticRegression(
            C=1.0, max_iter=1000, random_state=self.random_state
        )
        self.propensity_model_.fit(X_aug, A_all)
        e_hat = self.propensity_model_.predict_proba(X_aug)[:, 1]
        e_hat = np.clip(e_hat, 0.01, 0.99)
        
        # Outcome models
        mask_0 = A_all == 0
        mask_1 = A_all == 1
        
        self.outcome_model_0_ = Ridge(alpha=1.0)
        self.outcome_model_1_ = Ridge(alpha=1.0)
        
        self.outcome_model_0_.fit(X_aug[mask_0], Y_all[mask_0])
        self.outcome_model_1_.fit(X_aug[mask_1], Y_all[mask_1])
        
        mu_0 = self.outcome_model_0_.predict(X_aug)
        mu_1 = self.outcome_model_1_.predict(X_aug)
        
        # DR pseudo-outcomes
        pseudo = (A_all * (Y_all - mu_1) / e_hat - 
                  (1 - A_all) * (Y_all - mu_0) / (1 - e_hat) +
                  mu_1 - mu_0)
        
        # CATE model (on base features only)
        self.cate_model_ = Ridge(alpha=1.0)
        self.cate_model_.fit(X_scaled, pseudo)
        
        return self
    
    def predict(self, X):
        """Predict CATE."""
        X_scaled = self.scaler_.transform(X)
        return self.cate_model_.predict(X_scaled)
    
    def get_diagnostics(self) -> Dict[str, Any]:
        """Return diagnostic information."""
        return {
            'method': f'DRLearnerPooled (requires target treated)',
            'include_site': self.include_site,
            'n_sites': self.n_sites_
        }


# =============================================================================
# Factory functions for integration with benchmark
# =============================================================================

def create_transport_baseline_factories(seed: int = 42) -> Dict[str, callable]:
    """
    Create factory functions for transport baselines.
    
    Returns
    -------
    factories : dict
        method_name -> factory callable
    """
    factories = {
        # (1) Reweighting-based transport (Hong et al. 2025)
        'IPWTransport': lambda: IPWTransportEstimator(
            stabilized=True, random_state=seed
        ),
        'EntropyBalancing': lambda: EntropyBalancingEstimator(
            random_state=seed
        ),
        
        # (2) Outcome-regression transport (Rott 2024)
        'OutcomeModelTransport': lambda: OutcomeModelTransportEstimator(
            include_site=False, random_state=seed
        ),
        'OutcomeModelTransport_WithSite': lambda: OutcomeModelTransportEstimator(
            include_site=True, random_state=seed
        ),
        
        # (3) Augmented/doubly robust transport (Dahabreh et al. 2023)
        'AIPWTransport': lambda: AIPWTransportEstimator(
            random_state=seed, trial_specific_propensity=False
        ),
        'AIPWTransport_TrialSpecific': lambda: AIPWTransportEstimator(
            random_state=seed, trial_specific_propensity=True
        ),
        
        # (4) IPD meta-analytic baselines
        'HongTwoStage': lambda: HongTwoStageEstimator(
            meta_method='random', random_state=seed
        ),
        'IPD_RE': lambda: IPDRandomEffectsEstimator(
            random_state=seed
        ),
        
        # DR-Learner variants (require target treated)
        'DRLearner_PooledWithSite': lambda: DRLearnerPooledEstimator(
            include_site=True, random_state=seed
        ),
        'DRLearner_PooledNoSite': lambda: DRLearnerPooledEstimator(
            include_site=False, random_state=seed
        ),
        
        # Backward compatibility aliases
        'PooledRegression_WithSite': lambda: OutcomeModelTransportEstimator(
            include_site=True, random_state=seed
        ),
        'PooledRegression_NoSite': lambda: OutcomeModelTransportEstimator(
            include_site=False, random_state=seed
        ),
    }
    
    return factories
