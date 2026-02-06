"""
Fair Synthetic RCT Generator for OptionB Evaluation

This extends synthetic_data_v2.py with additional knobs recommended by advisor
for fair evaluation of source-only transport methods (OptionB/SourceDR):

1. Controlled nontransfer scale (SNR ladder)
2. Overlap control (covariate mixture)
3. Arm-specific intercept drift control
4. Structured (not adversarial) nontransfer component

Key fairness principles:
- OptionB should be tested where its assumptions APPROXIMATELY hold
- Violations should be explicit and separately swept
- Report SNR, overlap AUC, drift SD alongside metrics

Usage:
    from synthetic_data_v2_fair import FairSyntheticRCTConfig, FairSyntheticRCTGenerator
    
    # Fair regime for OptionB
    config = FairSyntheticRCTConfig(
        nontransfer_scale_target=0.1,  # SNR ≥ 2
        overlap_lambda=0.25,            # AUC ~ 0.7
        intercept_drift_scale=0.5,      # Mild drift
    )
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional, List
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from scipy.stats import spearmanr
import warnings


@dataclass
class FairSyntheticRCTConfig:
    """
    Configuration for fair synthetic RCT generation.
    
    Extends SyntheticRCTConfig with advisor-recommended knobs:
    - overlap_lambda: Controls covariate shift (0 = same as source, 1 = fully shifted)
    - intercept_drift_scale: Arm-specific intercept variance
    - nu_support_overlap: How much νₜ overlaps with β₀ₜ support
    - nu_coefficient_corr: Correlation between νₜ and β₀ₜ coefficients
    """
    
    # Basic dimensions
    n_features: int = 30
    n_source_sites: int = 10
    n_target: int = 500
    n_source_per_site: int = 500
    treatment_prob: float = 0.5
    noise_std: float = 0.5
    
    # ═══════════════════════════════════════════════════════════════════════
    # ADVISOR CHANGE 1: Controlled nontransfer (SNR ladder)
    # ═══════════════════════════════════════════════════════════════════════
    nontransfer_scale_source: float = 0.05   # Small for sources
    nontransfer_scale_target: float = 0.1    # DEFAULT: Fair (SNR ≥ 2)
    # Old default was 0.3 which gives SNR < 1 (unfair)
    
    # ═══════════════════════════════════════════════════════════════════════
    # ADVISOR CHANGE 2: Overlap control (covariate mixture)
    # ═══════════════════════════════════════════════════════════════════════
    overlap_lambda: float = 0.25  # 0 = same as source, 1 = fully shifted
    # Controls: X_t = (1-λ)X_s + λ(X_s + Δ)
    # λ = 0 → AUC ~ 0.5 (ideal overlap)
    # λ = 0.5 → AUC ~ 0.75-0.85 (realistic)
    # λ = 0.75 → AUC ~ 0.9 (hard)
    
    covariate_shift_scale: float = 1.0  # Scale of Δ when λ > 0
    
    # ═══════════════════════════════════════════════════════════════════════
    # ADVISOR CHANGE 3: Intercept drift control
    # ═══════════════════════════════════════════════════════════════════════
    intercept_drift_scale: float = 0.5  # σ_α for arm-specific intercepts
    # α_{a,c} ~ N(0, σ_α²)
    # Main plots: σ_α ≤ 1
    # Stress test: σ_α = 2
    
    # ═══════════════════════════════════════════════════════════════════════
    # ADVISOR CHANGE 4: Structured nontransfer (not adversarial)
    # ═══════════════════════════════════════════════════════════════════════
    nu_support_overlap: float = 0.5  # Fraction of νₜ support that overlaps β₀ₜ
    nu_coefficient_corr: float = 0.0  # Correlation between νₜ and β₀ₜ coefficients
    nu_sparse: bool = True  # If True, νₜ is sparse; if False, dense
    
    # ═══════════════════════════════════════════════════════════════════════
    # Original A5/A6 parameters (kept for compatibility)
    # ═══════════════════════════════════════════════════════════════════════
    dev_sparsity: int = 5  # Increased for better identifiability
    dev_scale: float = 0.4
    shared_support_frac: float = 0.6
    
    transfer_rank: int = 3
    transfer_strength: float = 1.0
    transfer_structure: str = "low_rank"
    
    # ═══════════════════════════════════════════════════════════════════════
    # A5 VIOLATION PARAMETERS (Reviewer sensitivity analysis)
    # ═══════════════════════════════════════════════════════════════════════
    # These control how badly A5 (sparse linear correction) is violated.
    # Default values = A5 holds. Sweep these to test robustness.
    
    # --- A. Non-sparse bias violations ---
    
    # A5.1: Sparsity ratio s/p (0.05 = sparse, 1.0 = dense)
    # Interpolates from sparse (A5 holds) to dense (A5 violated)
    # The L2 norm is held constant, only sparsity changes
    a5_sparsity_ratio: float = 0.05  # Default: sparse (5% of features)
    
    # A5.2: Coefficient decay α for approximate sparsity
    # |β|_(j) ∝ j^(-α), α→∞ = sparse, α=0 = flat/dense
    # Values: {2.0, 1.0, 0.5, 0.0} where 2.0 ≈ sparse, 0.0 = uniform
    a5_decay_alpha: float = 2.0  # Default: near-sparse (fast decay)
    
    # A5.3: Violation strength η = ||β^⊥||_2 / ||β^(s)||_2
    # β = β^(s) + β^⊥ where β^(s) is s-sparse, β^⊥ is dense residual
    # η=0 means purely sparse, η=2 means dense component dominates
    a5_violation_eta: float = 0.0  # Default: no dense residual
    
    # --- B. Nonlinear bias violations ---
    
    # A5.4: Nonlinearity mixture weight λ
    # δ(x) = (1-λ)·x^T β + λ·g(x)
    # λ=0 = linear (A5 holds), λ=1 = fully nonlinear (A5 violated)
    a5_nonlin_lambda: float = 0.0  # Default: linear
    
    # A5.5: Nonlinear function type
    # 'additive': g(x) = Σ_j a_j·sin(ω·x_j)  (smooth, still "simple")
    # 'interaction': g(x) = Σ_{j,k} a_jk·x_j·x_k  (pairwise interactions)
    # 'threshold': g(x) = Σ_j a_j·1{x_j > t_j}  (discontinuous)
    a5_nonlin_type: str = 'additive'
    
    # A5.6: Nonlinear support size (how many features g touches)
    # None = use a5_sparsity_ratio * p
    a5_nonlin_support: Optional[int] = None
    
    # A5.7: Nonlinear strength (controls Var(g(X)) relative to Var(x^T β))
    # This ensures nonlinear component has comparable signal to linear
    a5_nonlin_strength: float = 1.0
    
    # A5.8: Frequency for additive sinusoidal nonlinearity
    a5_nonlin_omega: float = 2.0
    
    # Proxy
    proxy_nonlinear_scale: float = 0.3  # Reduced for cleaner signal
    
    # Disconnected target
    target_treated_frac: Optional[float] = None
    treatment_prob_target: Optional[float] = None
    
    # Reproducibility
    random_state: int = 42


class FairSyntheticRCTGenerator:
    """
    DGP with fair evaluation knobs for OptionB.
    
    Key changes from original:
    1. Arm-specific intercepts α_{a,c}
    2. Controllable overlap via mixture
    3. Structured (sparse) nontransfer component
    4. Reports fairness diagnostics (SNR, AUC, drift)
    5. A5 violation controls (non-sparse and nonlinear deviations)
    """
    
    def __init__(self, config: FairSyntheticRCTConfig = None):
        self.config = config or FairSyntheticRCTConfig()
        self.rng = np.random.default_rng(self.config.random_state)
        
        p = self.config.n_features
        C = self.config.n_source_sites
        
        # ═════════════════════════════════════════════════════════════════
        # A5 violation: Generate nonlinear basis coefficients (shared)
        # ═════════════════════════════════════════════════════════════════
        self._setup_a5_nonlinear_basis()
        
        # ═════════════════════════════════════════════════════════════════
        # Sparsity allocation
        # ═════════════════════════════════════════════════════════════════
        s_total = self.config.dev_sparsity
        s_shared = max(1, int(s_total * self.config.shared_support_frac))
        s_idio = s_total - s_shared
        
        self.shared_support = self.rng.choice(p, size=s_shared, replace=False)
        remaining = list(set(range(p)) - set(self.shared_support))
        
        # ═════════════════════════════════════════════════════════════════
        # Proxy coefficients (shared across sites)
        # ═════════════════════════════════════════════════════════════════
        self.b0_proxy = self.rng.normal(0, 0.5, size=p)
        self.b1_proxy = self.rng.normal(0, 0.5, size=p)
        
        # Nonlinearity coefficients
        if self.config.proxy_nonlinear_scale > 0:
            self.proxy_nonlin_coef0 = self.rng.normal(0, 1.0, size=2)
            self.proxy_nonlin_coef1 = self.rng.normal(0, 1.0, size=2)
        
        # ═════════════════════════════════════════════════════════════════
        # Transfer operator M* (A6)
        # ═════════════════════════════════════════════════════════════════
        r = min(self.config.transfer_rank, p)
        
        if self.config.transfer_structure == "rhoI":
            self.M_star = self.config.transfer_strength * np.eye(p)
        elif self.config.transfer_structure == "diag":
            d = self.rng.normal(self.config.transfer_strength, 0.2, size=p)
            self.M_star = np.diag(d)
        else:  # "low_rank"
            U = self.rng.normal(0, 1.0, size=(p, r))
            V = self.rng.normal(0, 1.0, size=(p, r))
            self.M_star = self.config.transfer_strength * (U @ V.T) / max(1, r)
        
        # ═════════════════════════════════════════════════════════════════
        # Site-specific parameters
        # ═════════════════════════════════════════════════════════════════
        self.site_shifts = {}
        self.arm_intercepts = {}  # NEW: α_{a,c}
        self.beta0 = {}
        self.beta1 = {}
        self.nu = {}
        
        # Generate for sources (c=1,...,C) and target (c=0)
        for c in range(0, C + 1):
            is_target = (c == 0)
            
            # ─────────────────────────────────────────────────────────────
            # CHANGE 2: Covariate shift (controllable overlap)
            # ─────────────────────────────────────────────────────────────
            if is_target:
                # Target shift depends on overlap_lambda
                # λ=0: same distribution as sources
                # λ=1: maximally shifted
                shift_scale = self.config.overlap_lambda * self.config.covariate_shift_scale
                self.site_shifts[c] = self.rng.normal(0, shift_scale, size=p)
            else:
                # Source shifts are small/zero for clean source learning
                self.site_shifts[c] = self.rng.normal(0, 0.1, size=p)
            
            # ─────────────────────────────────────────────────────────────
            # CHANGE 3: Arm-specific intercepts α_{a,c}
            # ─────────────────────────────────────────────────────────────
            sigma_alpha = self.config.intercept_drift_scale
            self.arm_intercepts[c] = {
                0: self.rng.normal(0, sigma_alpha),  # Placebo intercept
                1: self.rng.normal(0, sigma_alpha),  # Treated intercept
            }
            
            # ─────────────────────────────────────────────────────────────
            # Placebo deviation β_{0,c} with A5 violation controls
            # ─────────────────────────────────────────────────────────────
            # Check if using A5 violation parameters (non-default values)
            use_a5_beta = (
                self.config.a5_sparsity_ratio != 0.05 or 
                self.config.a5_decay_alpha != 2.0 or
                self.config.a5_violation_eta != 0.0
            )
            
            if use_a5_beta:
                # Use controlled A5 violation coefficients
                # Target L2 norm based on dev_scale and expected sparse support
                target_norm = self.config.dev_scale * np.sqrt(s_total)
                beta0_c = self._generate_a5_deviation_beta(target_l2_norm=target_norm)
            else:
                # Original sparse generation (for backward compatibility)
                beta0_c = np.zeros(p)
                beta0_c[self.shared_support] = self.rng.normal(
                    0, self.config.dev_scale, size=len(self.shared_support)
                )
                
                if s_idio > 0 and len(remaining) > 0:
                    idio_size = min(s_idio, len(remaining))
                    idio_support = self.rng.choice(remaining, size=idio_size, replace=False)
                    beta0_c[idio_support] = self.rng.normal(
                        0, self.config.dev_scale * 0.5, size=idio_size
                    )
            
            # ─────────────────────────────────────────────────────────────
            # CHANGE 4: Structured nontransfer component ν_c
            # ─────────────────────────────────────────────────────────────
            nu_scale = (self.config.nontransfer_scale_target if is_target 
                       else self.config.nontransfer_scale_source)
            
            if self.config.nu_sparse:
                # Sparse νₜ with controllable support overlap
                nu_c = np.zeros(p)
                
                # Determine support
                beta0_support = np.where(np.abs(beta0_c) > 1e-8)[0]
                n_overlap = max(1, int(len(beta0_support) * self.config.nu_support_overlap))
                n_new = s_total - n_overlap
                
                # Overlapping support
                if len(beta0_support) > 0 and n_overlap > 0:
                    overlap_idx = self.rng.choice(
                        beta0_support, 
                        size=min(n_overlap, len(beta0_support)), 
                        replace=False
                    )
                    
                    if self.config.nu_coefficient_corr > 0:
                        # Correlated coefficients
                        nu_c[overlap_idx] = (
                            self.config.nu_coefficient_corr * beta0_c[overlap_idx] +
                            np.sqrt(1 - self.config.nu_coefficient_corr**2) * 
                            self.rng.normal(0, nu_scale, size=len(overlap_idx))
                        )
                    else:
                        nu_c[overlap_idx] = self.rng.normal(0, nu_scale, size=len(overlap_idx))
                
                # New support (not in β₀)
                non_beta0_support = list(set(range(p)) - set(beta0_support))
                if n_new > 0 and len(non_beta0_support) > 0:
                    new_idx = self.rng.choice(
                        non_beta0_support,
                        size=min(n_new, len(non_beta0_support)),
                        replace=False
                    )
                    nu_c[new_idx] = self.rng.normal(0, nu_scale, size=len(new_idx))
            else:
                # Dense νₜ (original behavior)
                nu_c = self.rng.normal(0, nu_scale, size=p)
            
            # ─────────────────────────────────────────────────────────────
            # Cross-arm transfer (A6): β₁ = M*β₀ + ν
            # ─────────────────────────────────────────────────────────────
            beta1_c = self.M_star @ beta0_c + nu_c
            
            # Store
            self.beta0[c] = beta0_c
            self.beta1[c] = beta1_c
            self.nu[c] = nu_c
    
    def _setup_a5_nonlinear_basis(self):
        """
        Set up the nonlinear basis functions for A5 violations.
        
        This creates shared nonlinear basis coefficients that will be used
        when a5_nonlin_lambda > 0 to add nonlinear deviations.
        """
        p = self.config.n_features
        
        # Determine nonlinear support size
        if self.config.a5_nonlin_support is not None:
            nonlin_support_size = min(self.config.a5_nonlin_support, p)
        else:
            nonlin_support_size = max(5, int(self.config.a5_sparsity_ratio * p))
        
        # Select which features the nonlinearity touches
        self.a5_nonlin_features = self.rng.choice(p, size=nonlin_support_size, replace=False)
        
        # Generate coefficients for each nonlinear type
        nonlin_type = self.config.a5_nonlin_type
        strength = self.config.a5_nonlin_strength
        
        if nonlin_type == 'additive':
            # g(x) = Σ_j a_j · sin(ω · x_j)
            self.a5_nonlin_coef = self.rng.normal(0, strength, size=nonlin_support_size)
            
        elif nonlin_type == 'interaction':
            # g(x) = Σ_{j<k} a_jk · x_j · x_k
            n_pairs = min(nonlin_support_size * (nonlin_support_size - 1) // 2, 50)
            if nonlin_support_size >= 2:
                # Generate interaction pairs
                pairs = []
                for i, fi in enumerate(self.a5_nonlin_features):
                    for j, fj in enumerate(self.a5_nonlin_features):
                        if i < j:
                            pairs.append((fi, fj))
                if len(pairs) > n_pairs:
                    pair_idx = self.rng.choice(len(pairs), size=n_pairs, replace=False)
                    pairs = [pairs[i] for i in pair_idx]
                self.a5_interaction_pairs = pairs
                self.a5_interaction_coef = self.rng.normal(0, strength / np.sqrt(max(1, len(pairs))), 
                                                           size=len(pairs))
            else:
                self.a5_interaction_pairs = []
                self.a5_interaction_coef = np.array([])
                
        elif nonlin_type == 'threshold':
            # g(x) = Σ_j a_j · 1{x_j > t_j}
            self.a5_nonlin_coef = self.rng.normal(0, strength, size=nonlin_support_size)
            self.a5_thresholds = self.rng.normal(0, 0.5, size=nonlin_support_size)
        
        else:
            raise ValueError(f"Unknown a5_nonlin_type: {nonlin_type}")
    
    def _compute_a5_nonlinear(self, X: np.ndarray) -> np.ndarray:
        """
        Compute the nonlinear component g(X) for A5 violations.
        
        Returns:
            g(X) array of shape (n_samples,)
        """
        nonlin_type = self.config.a5_nonlin_type
        omega = self.config.a5_nonlin_omega
        
        if nonlin_type == 'additive':
            # g(x) = Σ_j a_j · sin(ω · x_j)
            X_sub = X[:, self.a5_nonlin_features]
            g = np.sum(self.a5_nonlin_coef * np.sin(omega * X_sub), axis=1)
            
        elif nonlin_type == 'interaction':
            # g(x) = Σ_{j,k} a_jk · x_j · x_k
            g = np.zeros(X.shape[0])
            for (fi, fj), coef in zip(self.a5_interaction_pairs, self.a5_interaction_coef):
                g += coef * X[:, fi] * X[:, fj]
                
        elif nonlin_type == 'threshold':
            # g(x) = Σ_j a_j · 1{x_j > t_j}
            X_sub = X[:, self.a5_nonlin_features]
            indicators = (X_sub > self.a5_thresholds).astype(float)
            g = np.sum(self.a5_nonlin_coef * indicators, axis=1)
        
        else:
            g = np.zeros(X.shape[0])
        
        return g
    
    def _generate_a5_deviation_beta(self, target_l2_norm: float = 1.0) -> np.ndarray:
        """
        Generate deviation coefficients β with controlled sparsity pattern.
        
        Uses the A5 violation parameters to create:
        1. Controlled sparsity ratio (a5_sparsity_ratio)
        2. Decaying coefficients (a5_decay_alpha)  
        3. Dense residual component (a5_violation_eta)
        
        Args:
            target_l2_norm: Target L2 norm for the coefficient vector
            
        Returns:
            beta: Coefficient vector of shape (p,)
        """
        p = self.config.n_features
        sparsity_ratio = self.config.a5_sparsity_ratio
        decay_alpha = self.config.a5_decay_alpha
        violation_eta = self.config.a5_violation_eta
        
        # Number of "main" non-zero coefficients
        s = max(1, int(sparsity_ratio * p))
        
        # Step 1: Generate sparse component β^(s) with decaying magnitudes
        support = self.rng.choice(p, size=s, replace=False)
        
        # Generate magnitudes with power-law decay: |β|_(j) ∝ j^(-α)
        if decay_alpha > 0:
            ranks = np.arange(1, s + 1)
            magnitudes = ranks ** (-decay_alpha)
        else:
            # α = 0: uniform magnitudes (maximally dense within support)
            magnitudes = np.ones(s)
        
        # Random signs
        signs = self.rng.choice([-1, 1], size=s)
        sparse_coef = signs * magnitudes
        
        # Normalize sparse component to unit L2
        sparse_coef = sparse_coef / (np.linalg.norm(sparse_coef) + 1e-10)
        
        # Build sparse beta
        beta_sparse = np.zeros(p)
        beta_sparse[support] = sparse_coef
        
        # Step 2: Add dense residual component β^⊥ if η > 0
        if violation_eta > 0:
            # Generate dense noise orthogonal-ish to sparse support
            beta_dense = self.rng.normal(0, 1, size=p)
            # Zero out sparse support to make it "orthogonal"
            beta_dense[support] = 0
            # Normalize to have ||β^⊥||_2 / ||β^(s)||_2 = η
            if np.linalg.norm(beta_dense) > 1e-10:
                beta_dense = beta_dense / np.linalg.norm(beta_dense) * violation_eta
            
            beta = beta_sparse + beta_dense
        else:
            beta = beta_sparse
        
        # Step 3: Rescale to target L2 norm
        if np.linalg.norm(beta) > 1e-10:
            beta = beta * target_l2_norm / np.linalg.norm(beta)
        
        return beta
    
    def _mu(self, X: np.ndarray, site_id: int, arm: int) -> np.ndarray:
        """
        Compute μ_{a,c}(x) = α_{a,c} + x^T b_a + nonlin(x) + δ_{a,c}(x).
        
        Where the site-specific deviation δ_{a,c}(x) is:
            δ(x) = (1 - λ) · x^T β_{a,c} + λ · g(x)
        
        - λ = a5_nonlin_lambda controls linear vs nonlinear mixture
        - g(x) is the nonlinear function (additive, interaction, or threshold)
        
        NEW: Includes arm-specific intercept α_{a,c} and A5 violation controls.
        """
        p = self.config.n_features
        
        # Arm-specific intercept (CHANGE 3)
        alpha = self.arm_intercepts[site_id][arm]
        
        # Get linear deviation coefficient
        if arm == 0:
            base = X @ self.b0_proxy
            beta_dev = self.beta0[site_id]
            
            if self.config.proxy_nonlinear_scale > 0:
                c0, c1 = self.proxy_nonlin_coef0
                base = base + self.config.proxy_nonlinear_scale * (
                    c0 * np.sin(X[:, 0]) + c1 * 0.5 * X[:, 1]**2
                )
        else:
            base = X @ self.b1_proxy
            beta_dev = self.beta1[site_id]
            
            if self.config.proxy_nonlinear_scale > 0:
                c0, c1 = self.proxy_nonlin_coef1
                base = base + self.config.proxy_nonlinear_scale * (
                    c0 * np.sin(X[:, 0]) + c1 * 0.5 * X[:, 1]**2
                )
        
        # ═══════════════════════════════════════════════════════════════════
        # A5 VIOLATION: Mixture of linear and nonlinear deviation
        # δ(x) = (1 - λ) · x^T β + λ · g(x)
        # ═══════════════════════════════════════════════════════════════════
        lam = self.config.a5_nonlin_lambda
        
        # Linear component: x^T β
        dev_linear = X @ beta_dev
        
        if lam > 0:
            # Nonlinear component: g(x)
            dev_nonlin = self._compute_a5_nonlinear(X)
            
            # Normalize nonlinear component to match linear variance
            # This ensures λ controls the *relative* contribution
            var_linear = np.var(dev_linear) + 1e-10
            var_nonlin = np.var(dev_nonlin) + 1e-10
            dev_nonlin = dev_nonlin * np.sqrt(var_linear / var_nonlin)
            
            # Mixture
            dev = (1 - lam) * dev_linear + lam * dev_nonlin
        else:
            dev = dev_linear
        
        return alpha + base + dev
    
    def generate_site_data(self, site_id: int, n_samples: int) -> Dict:
        """Generate data for one site."""
        p = self.config.n_features
        
        # Covariates with site-specific shift
        shift = self.site_shifts[site_id]
        X = self.rng.normal(0, 1.0, size=(n_samples, p)) + shift
        
        # Treatment assignment
        if site_id == 0:  # Target
            if self.config.target_treated_frac is not None:
                A = self.rng.binomial(1, self.config.target_treated_frac, size=n_samples)
            else:
                e = self.config.treatment_prob_target or self.config.treatment_prob
                A = self.rng.binomial(1, e, size=n_samples)
        else:
            A = self.rng.binomial(1, self.config.treatment_prob, size=n_samples)
        
        # Potential outcomes
        mu0 = self._mu(X, site_id, arm=0)
        mu1 = self._mu(X, site_id, arm=1)
        tau = mu1 - mu0
        
        # Observed outcome
        eps = self.rng.normal(0, self.config.noise_std, size=n_samples)
        Y = mu0 + A * tau + eps
        
        c = np.full(n_samples, site_id, dtype=int)
        
        return dict(X=X, A=A, Y=Y, tau_true=tau, mu0_true=mu0, mu1_true=mu1, c=c)
    
    def generate_full_dataset(self) -> Tuple[Dict, Dict]:
        """Generate complete multi-site dataset."""
        # Sources
        source_datasets = [
            self.generate_site_data(c, self.config.n_source_per_site)
            for c in range(1, self.config.n_source_sites + 1)
        ]
        
        source_data = {}
        for key in source_datasets[0].keys():
            if key == 'X':
                source_data[key] = np.vstack([d[key] for d in source_datasets])
            else:
                source_data[key] = np.concatenate([d[key] for d in source_datasets])
        
        # Target
        target_data = self.generate_site_data(0, self.config.n_target)
        
        return source_data, target_data
    
    def get_fairness_diagnostics(self) -> Dict:
        """
        Compute fairness diagnostics for OptionB evaluation.
        
        Returns metrics that determine whether OptionB assumptions hold:
        - SNR: |M*β₀ₜ| / |νₜ| (should be ≥ 1 for fair test)
        - cross_arm_corr: correlation of placebo/treated effects
        - overlap_auc: source vs target classifier AUC (should be < 0.85)
        - intercept_drift_sd: SD of arm means across replications
        """
        diag = {}
        
        # ═════════════════════════════════════════════════════════════════
        # Target transfer quality (A2)
        # ═════════════════════════════════════════════════════════════════
        beta0_t = self.beta0[0]
        beta1_t = self.beta1[0]
        nu_t = self.nu[0]
        
        M_beta0_t = self.M_star @ beta0_t
        
        diag['target_M_beta0_norm'] = float(np.linalg.norm(M_beta0_t))
        diag['target_nu_norm'] = float(np.linalg.norm(nu_t))
        diag['target_SNR'] = float(np.linalg.norm(M_beta0_t) / (np.linalg.norm(nu_t) + 1e-10))
        
        # Cosine similarity
        if np.linalg.norm(beta1_t) > 1e-10 and np.linalg.norm(M_beta0_t) > 1e-10:
            diag['target_cosine_sim'] = float(
                np.dot(beta1_t, M_beta0_t) / (np.linalg.norm(beta1_t) * np.linalg.norm(M_beta0_t))
            )
        else:
            diag['target_cosine_sim'] = 0.0
        
        # ═════════════════════════════════════════════════════════════════
        # Cross-arm correlation on target distribution
        # ═════════════════════════════════════════════════════════════════
        # Generate sample to compute correlation
        X_sample = self.rng.normal(0, 1.0, size=(1000, self.config.n_features))
        X_sample = X_sample + self.site_shifts[0]
        
        xb0 = X_sample @ beta0_t
        xb1 = X_sample @ beta1_t
        
        if np.std(xb0) > 1e-10 and np.std(xb1) > 1e-10:
            corr, _ = spearmanr(xb0, xb1)
            diag['cross_arm_corr'] = float(corr)
        else:
            diag['cross_arm_corr'] = 0.0
        
        # ═════════════════════════════════════════════════════════════════
        # Overlap AUC (A3)
        # ═════════════════════════════════════════════════════════════════
        source_data, target_data = self.generate_full_dataset()
        
        X_all = np.vstack([source_data['X'], target_data['X']])
        y_all = np.concatenate([
            np.zeros(len(source_data['X'])), 
            np.ones(len(target_data['X']))
        ])
        
        try:
            clf = LogisticRegression(max_iter=1000, random_state=self.config.random_state)
            clf.fit(X_all, y_all)
            probs = clf.predict_proba(X_all)[:, 1]
            diag['overlap_auc'] = float(roc_auc_score(y_all, probs))
        except:
            diag['overlap_auc'] = 0.5
        
        # ═════════════════════════════════════════════════════════════════
        # Intercept drift (A1)
        # ═════════════════════════════════════════════════════════════════
        diag['target_alpha_0'] = float(self.arm_intercepts[0][0])
        diag['target_alpha_1'] = float(self.arm_intercepts[0][1])
        diag['intercept_drift_scale'] = self.config.intercept_drift_scale
        
        # Arm means
        diag['E_mu0'] = float(np.mean(target_data['mu0_true']))
        diag['E_mu1'] = float(np.mean(target_data['mu1_true']))
        diag['E_tau'] = float(np.mean(target_data['tau_true']))
        
        # ═════════════════════════════════════════════════════════════════
        # A5 Violation Diagnostics (sparsity and nonlinearity)
        # ═════════════════════════════════════════════════════════════════
        p = self.config.n_features
        
        # A5.1: Effective sparsity (fraction of coefficients with significant mass)
        beta0_t_abs = np.abs(beta0_t)
        total_mass = np.sum(beta0_t_abs)
        if total_mass > 1e-10:
            # Count features that contribute at least 1% of total mass
            significant_threshold = 0.01 * total_mass
            n_significant = np.sum(beta0_t_abs > significant_threshold / p)
            diag['a5_effective_sparsity'] = float(n_significant / p)
        else:
            diag['a5_effective_sparsity'] = 0.0
        
        # A5.2: Decay rate (how concentrated is the mass in top coefficients)
        sorted_abs = np.sort(beta0_t_abs)[::-1]
        cumsum = np.cumsum(sorted_abs) / (np.sum(sorted_abs) + 1e-10)
        # Find how many coefficients needed for 90% of mass
        n_for_90 = np.searchsorted(cumsum, 0.9) + 1
        diag['a5_n_for_90pct_mass'] = int(n_for_90)
        diag['a5_mass_concentration'] = float(n_for_90 / p)  # 0 = concentrated, 1 = diffuse
        
        # A5.3: Nonlinearity contribution
        diag['a5_nonlin_lambda'] = self.config.a5_nonlin_lambda
        diag['a5_nonlin_type'] = self.config.a5_nonlin_type
        
        # Compute variance decomposition if nonlinearity is present
        if self.config.a5_nonlin_lambda > 0:
            X_test = target_data['X']
            dev_linear = X_test @ beta0_t
            dev_nonlin = self._compute_a5_nonlinear(X_test)
            
            var_linear = np.var(dev_linear)
            var_nonlin = np.var(dev_nonlin)
            
            diag['a5_var_linear'] = float(var_linear)
            diag['a5_var_nonlinear'] = float(var_nonlin)
            diag['a5_nonlin_var_ratio'] = float(var_nonlin / (var_linear + 1e-10))
        else:
            diag['a5_var_linear'] = float(np.var(target_data['X'] @ beta0_t))
            diag['a5_var_nonlinear'] = 0.0
            diag['a5_nonlin_var_ratio'] = 0.0
        
        # Store A5 config values for reference
        diag['a5_sparsity_ratio_config'] = self.config.a5_sparsity_ratio
        diag['a5_decay_alpha_config'] = self.config.a5_decay_alpha
        diag['a5_violation_eta_config'] = self.config.a5_violation_eta
        
        # ═════════════════════════════════════════════════════════════════
        # Fairness assessment
        # ═════════════════════════════════════════════════════════════════
        diag['fair_for_optionB'] = (
            diag['target_SNR'] >= 1.0 and 
            diag['overlap_auc'] < 0.90 and 
            abs(diag['target_alpha_0']) < 2.0 and 
            abs(diag['target_alpha_1']) < 2.0
        )
        
        if not diag['fair_for_optionB']:
            reasons = []
            if diag['target_SNR'] < 1.0:
                reasons.append(f"SNR={diag['target_SNR']:.2f}<1 (nontransfer dominates)")
            if diag['overlap_auc'] >= 0.90:
                reasons.append(f"AUC={diag['overlap_auc']:.2f}>=0.9 (poor overlap)")
            if abs(diag['target_alpha_0']) >= 2.0 or abs(diag['target_alpha_1']) >= 2.0:
                reasons.append(f"intercepts={diag['target_alpha_0']:.1f},{diag['target_alpha_1']:.1f} (high drift)")
            diag['unfairness_reasons'] = reasons
        else:
            diag['unfairness_reasons'] = []
        
        return diag


# ═════════════════════════════════════════════════════════════════════════════
# Convenience functions for fair sweeps
# ═════════════════════════════════════════════════════════════════════════════

def generate_fair_dataset(
    nontransfer_scale_target: float = 0.1,
    overlap_lambda: float = 0.25,
    intercept_drift_scale: float = 0.5,
    random_state: int = 42,
    **kwargs
) -> Tuple[Dict, Dict, FairSyntheticRCTGenerator]:
    """
    Generate dataset with fair evaluation settings for OptionB.
    
    Default settings give:
    - SNR ≈ 2-3 (transfer signal present)
    - Overlap AUC ≈ 0.7-0.8 (moderate)
    - Intercept drift SD ≈ 0.5 (controlled)
    """
    config = FairSyntheticRCTConfig(
        nontransfer_scale_target=nontransfer_scale_target,
        overlap_lambda=overlap_lambda,
        intercept_drift_scale=intercept_drift_scale,
        random_state=random_state,
        **kwargs
    )
    
    gen = FairSyntheticRCTGenerator(config)
    source, target = gen.generate_full_dataset()
    
    return source, target, gen


def generate_stress_test_dataset(
    nontransfer_scale_target: float = 0.3,
    overlap_lambda: float = 0.75,
    intercept_drift_scale: float = 2.0,
    random_state: int = 42,
    **kwargs
) -> Tuple[Dict, Dict, FairSyntheticRCTGenerator]:
    """
    Generate dataset where OptionB assumptions are VIOLATED.
    
    Use for negative control / stress test:
    - SNR < 1 (nontransfer dominates)
    - Overlap AUC > 0.9 (poor overlap)
    - High intercept drift
    """
    config = FairSyntheticRCTConfig(
        nontransfer_scale_target=nontransfer_scale_target,
        overlap_lambda=overlap_lambda,
        intercept_drift_scale=intercept_drift_scale,
        random_state=random_state,
        **kwargs
    )
    
    gen = FairSyntheticRCTGenerator(config)
    source, target = gen.generate_full_dataset()
    
    return source, target, gen


# ═════════════════════════════════════════════════════════════════════════════
# Sweep configurations (advisor-recommended)
# ═════════════════════════════════════════════════════════════════════════════

FAIR_SWEEP_CONFIGS = {
    # Sweep A: Cross-arm validity (primary)
    # Fix overlap good, drift small
    'cross_arm_validity': {
        'description': 'Test OptionB across SNR ladder (fair overlap, low drift)',
        'fixed': {
            'overlap_lambda': 0.25,
            'intercept_drift_scale': 0.5,
        },
        'sweep': {
            'nontransfer_scale_target': [0.0, 0.05, 0.1, 0.2, 0.3],
        },
        'fairness_gate': 'target_SNR',
        'main_regime': 'SNR >= 1',
        'stress_regime': 'SNR < 1',
    },
    
    # Sweep B: Overlap stress
    # Fix SNR high
    'overlap_stress': {
        'description': 'Test OptionB across overlap ladder (high SNR, low drift)',
        'fixed': {
            'nontransfer_scale_target': 0.0,  # Perfect transfer
            'intercept_drift_scale': 0.5,
        },
        'sweep': {
            'overlap_lambda': [0.0, 0.25, 0.5, 0.75, 1.0],
        },
        'fairness_gate': 'overlap_auc',
        'main_regime': 'AUC < 0.85',
        'stress_regime': 'AUC >= 0.9',
    },
    
    # Sweep C: Drift stress
    # Fix SNR high, overlap good
    'drift_stress': {
        'description': 'Test OptionB across intercept drift ladder',
        'fixed': {
            'nontransfer_scale_target': 0.0,
            'overlap_lambda': 0.25,
        },
        'sweep': {
            'intercept_drift_scale': [0.0, 0.5, 1.0, 2.0, 4.0],
        },
        'fairness_gate': 'intercept_drift_scale',
        'main_regime': 'drift <= 1',
        'stress_regime': 'drift > 2',
    },
    
    # Combined fair sweep (2D: SNR × overlap)
    'fair_grid': {
        'description': '2D grid of SNR × overlap for comprehensive evaluation',
        'sweep': {
            'nontransfer_scale_target': [0.0, 0.1, 0.2],
            'overlap_lambda': [0.0, 0.25, 0.5],
        },
        'fixed': {
            'intercept_drift_scale': 0.5,
        },
    },
}


# ═════════════════════════════════════════════════════════════════════════════
# A5 VIOLATION SWEEP CONFIGS (Reviewer sensitivity analysis)
# ═════════════════════════════════════════════════════════════════════════════
#
# These sweeps test how methods degrade when Assumption A5 (sparse linear
# correction) is violated. Two axes: non-sparse and nonlinear.
#
# Recommended minimal grid (reviewer-proof):
#   - Sparsity ratio: s/p ∈ {0.05, 0.2, 1.0}
#   - Nonlinearity mix: λ ∈ {0, 0.5, 1}
#   - Nonlinear family: {additive, interaction}
# That's 3 × 3 × 2 = 18 settings per MC rep

A5_SWEEP_CONFIGS = {
    
    # ═══════════════════════════════════════════════════════════════════════
    # A. Non-sparse bias violations
    # ═══════════════════════════════════════════════════════════════════════
    
    'a5_sparsity': {
        'description': 'Sweep sparsity ratio s/p (A5 violation via dense coefficients)',
        'narrative': 'Interpolate from sparse (A5 holds) to dense (A5 violated), L2 norm fixed.',
        'fixed': {
            'overlap_lambda': 0.25,  # Fair overlap
            'intercept_drift_scale': 0.5,  # Low drift
            'nontransfer_scale_target': 0.1,  # Fair SNR
            'a5_decay_alpha': 2.0,  # Keep decay fast
            'a5_violation_eta': 0.0,  # No dense residual
            'a5_nonlin_lambda': 0.0,  # Pure linear
        },
        'sweep': {
            'a5_sparsity_ratio': [0.02, 0.05, 0.10, 0.20, 0.50, 1.00],
        },
        'diagnostic_key': 'a5_effective_sparsity',
        'a5_holds_when': 'sparsity_ratio <= 0.1',
    },
    
    'a5_decay': {
        'description': 'Sweep coefficient decay α (approximate sparsity)',
        'narrative': 'Test "compressible" vs truly sparse; α→∞ = sparse, α=0 = flat/dense.',
        'fixed': {
            'overlap_lambda': 0.25,
            'intercept_drift_scale': 0.5,
            'nontransfer_scale_target': 0.1,
            'a5_sparsity_ratio': 0.2,  # 20% support
            'a5_violation_eta': 0.0,
            'a5_nonlin_lambda': 0.0,
        },
        'sweep': {
            'a5_decay_alpha': [2.0, 1.0, 0.5, 0.0],  # 2.0 = near-sparse, 0.0 = uniform
        },
        'diagnostic_key': 'a5_mass_concentration',
        'a5_holds_when': 'decay_alpha >= 1.0',
    },
    
    'a5_dense_residual': {
        'description': 'Sweep violation strength η = ||β^⊥||/||β^(s)|| (dense noise)',
        'narrative': 'Progressively inject non-sparse components while keeping sparse part.',
        'fixed': {
            'overlap_lambda': 0.25,
            'intercept_drift_scale': 0.5,
            'nontransfer_scale_target': 0.1,
            'a5_sparsity_ratio': 0.05,  # Sparse main component
            'a5_decay_alpha': 2.0,
            'a5_nonlin_lambda': 0.0,
        },
        'sweep': {
            'a5_violation_eta': [0.0, 0.25, 0.5, 1.0, 2.0],
        },
        'diagnostic_key': 'a5_effective_sparsity',
        'a5_holds_when': 'violation_eta <= 0.25',
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # B. Nonlinear bias violations
    # ═══════════════════════════════════════════════════════════════════════
    
    'a5_nonlinear_additive': {
        'description': 'Sweep nonlinearity mixture λ with additive g(x) = Σ sin(ωx_j)',
        'narrative': 'Test mild smooth mis-specification. Still "simple" but violates linearity.',
        'fixed': {
            'overlap_lambda': 0.25,
            'intercept_drift_scale': 0.5,
            'nontransfer_scale_target': 0.1,
            'a5_sparsity_ratio': 0.05,  # Sparse linear part
            'a5_decay_alpha': 2.0,
            'a5_violation_eta': 0.0,
            'a5_nonlin_type': 'additive',
            'a5_nonlin_omega': 2.0,
        },
        'sweep': {
            'a5_nonlin_lambda': [0.0, 0.25, 0.5, 0.75, 1.0],
        },
        'diagnostic_key': 'a5_nonlin_var_ratio',
        'a5_holds_when': 'nonlin_lambda <= 0.25',
    },
    
    'a5_nonlinear_interaction': {
        'description': 'Sweep nonlinearity mixture λ with interactions g(x) = Σ x_j·x_k',
        'narrative': 'Test epistatic/interaction violations. Harder to capture with linear methods.',
        'fixed': {
            'overlap_lambda': 0.25,
            'intercept_drift_scale': 0.5,
            'nontransfer_scale_target': 0.1,
            'a5_sparsity_ratio': 0.05,
            'a5_decay_alpha': 2.0,
            'a5_violation_eta': 0.0,
            'a5_nonlin_type': 'interaction',
        },
        'sweep': {
            'a5_nonlin_lambda': [0.0, 0.25, 0.5, 0.75, 1.0],
        },
        'diagnostic_key': 'a5_nonlin_var_ratio',
        'a5_holds_when': 'nonlin_lambda <= 0.25',
    },
    
    'a5_nonlinear_threshold': {
        'description': 'Sweep nonlinearity mixture λ with threshold g(x) = Σ 1{x_j > t_j}',
        'narrative': 'Test discontinuous violations. Hardest case for smooth methods.',
        'fixed': {
            'overlap_lambda': 0.25,
            'intercept_drift_scale': 0.5,
            'nontransfer_scale_target': 0.1,
            'a5_sparsity_ratio': 0.05,
            'a5_decay_alpha': 2.0,
            'a5_violation_eta': 0.0,
            'a5_nonlin_type': 'threshold',
        },
        'sweep': {
            'a5_nonlin_lambda': [0.0, 0.25, 0.5, 0.75, 1.0],
        },
        'diagnostic_key': 'a5_nonlin_var_ratio',
        'a5_holds_when': 'nonlin_lambda <= 0.25',
    },
    
    # ═══════════════════════════════════════════════════════════════════════
    # C. Combined sweeps (reviewer-proof minimal grid)
    # ═══════════════════════════════════════════════════════════════════════
    
    'a5_sparsity_x_nonlin': {
        'description': '2D grid: sparsity × nonlinearity (additive)',
        'narrative': 'Compact 3×3 grid covering both violation axes.',
        'fixed': {
            'overlap_lambda': 0.25,
            'intercept_drift_scale': 0.5,
            'nontransfer_scale_target': 0.1,
            'a5_decay_alpha': 2.0,
            'a5_violation_eta': 0.0,
            'a5_nonlin_type': 'additive',
        },
        'sweep': {
            'a5_sparsity_ratio': [0.05, 0.2, 1.0],
            'a5_nonlin_lambda': [0.0, 0.5, 1.0],
        },
        'total_scenarios': '3 × 3 = 9',
    },
    
    'a5_full_grid': {
        'description': 'Full A5 sensitivity: sparsity × nonlinearity × nonlin_type',
        'narrative': 'Complete reviewer-proof grid: 3 × 3 × 2 = 18 scenarios.',
        'fixed': {
            'overlap_lambda': 0.25,
            'intercept_drift_scale': 0.5,
            'nontransfer_scale_target': 0.1,
            'a5_decay_alpha': 2.0,
            'a5_violation_eta': 0.0,
        },
        'sweep': {
            'a5_sparsity_ratio': [0.05, 0.2, 1.0],
            'a5_nonlin_lambda': [0.0, 0.5, 1.0],
            'a5_nonlin_type': ['additive', 'interaction'],
        },
        'total_scenarios': '3 × 3 × 2 = 18',
    },
}


if __name__ == '__main__':
    # Quick test
    print("Testing FairSyntheticRCTGenerator...")
    
    # Fair regime
    source, target, gen = generate_fair_dataset(random_state=42)
    diag = gen.get_fairness_diagnostics()
    
    print("\n=== Fair Regime ===")
    print(f"SNR: {diag['target_SNR']:.2f}")
    print(f"Overlap AUC: {diag['overlap_auc']:.2f}")
    print(f"Cross-arm corr: {diag['cross_arm_corr']:.2f}")
    print(f"Fair for OptionB: {diag['fair_for_optionB']}")
    
    # Stress test
    source, target, gen = generate_stress_test_dataset(random_state=42)
    diag = gen.get_fairness_diagnostics()
    
    print("\n=== Stress Test ===")
    print(f"SNR: {diag['target_SNR']:.2f}")
    print(f"Overlap AUC: {diag['overlap_auc']:.2f}")
    print(f"Cross-arm corr: {diag['cross_arm_corr']:.2f}")
    print(f"Fair for OptionB: {diag['fair_for_optionB']}")
    if diag['unfairness_reasons']:
        print(f"Reasons: {diag['unfairness_reasons']}")
