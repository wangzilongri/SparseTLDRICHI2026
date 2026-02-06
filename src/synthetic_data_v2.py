"""
Improved Synthetic RCT Generator aligned with A5 (sparse deviations) and A6 (cross-arm transfer).

Key improvements:
1. Explicit proxy (shared) + deviation (site-specific) decomposition
2. Cross-arm transfer operator M* with controllable rank and strength
3. Sparse site deviations beta_{0,c} with configurable support
4. Nontransfer component nu_c with different scales for source vs target
5. Optional misspecification r_{a,c}(x) for robustness testing
6. Support for disconnected target (placebo-only)
7. Proper RNG for reproducibility

DGP Structure:
  mu_{a,c}(x) = x^T b_a + x^T beta_{a,c} + r_{a,c}(x)
                └─proxy─┘   └─deviation─┘   └misspec┘
  
  where beta_{1,c} = M* beta_{0,c} + nu_c  (A6)
  
  Y = mu_{0,c}(X) + A * (mu_{1,c}(X) - mu_{0,c}(X)) + eps
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional


@dataclass
class SyntheticRCTConfig:
    """
    Configuration for synthetic RCT generation.
    
    A5 Sparsity Control (ADVISOR FIX #1):
        `dev_sparsity` is THE governing constraint for |β_{0,c}|_0.
        `shared_support_frac` controls what fraction of dev_sparsity is shared.
        
        Effective support:
            s_shared = max(1, int(dev_sparsity * shared_support_frac))
            s_idio = dev_sparsity - s_shared
    
    Step B Identifiability:
        For M* to be learnable, we need rank(B0) >= transfer_rank.
        This requires dev_sparsity >= transfer_rank typically.
        Generator will warn if this condition is violated.
    """
    
    # Basic dimensions
    n_features: int = 30
    n_effect_modifiers: int = 5  # ADVISOR FIX #4: Set restrict_deviation_to_first_k to this for meaningful effect modifiers
    n_source_sites: int = 10     # INCREASED for Step B identifiability
    n_target: int = 200
    n_source_per_site: int = 500
    treatment_prob: float = 0.5              # Default for all sites
    treatment_prob_source: Optional[float] = None  # Override for source sites
    treatment_prob_target: Optional[float] = None  # Override for target site (overlap stress)
    noise_std: float = 0.5
    
    # Covariate shift
    covariate_shift_scale: float = 1.0
    target_shift_multiplier: float = 1.5  # Target has more shift
    cov_shift_strength: float = 0.0       # Optional covariance shift
    
    # Proxy nonlinearity (makes Stage 1 nontrivial)
    proxy_nonlinear_scale: float = 0.5    # Mild nonlinearity in proxy
    
    # ═══════════════════════════════════════════════════════════════════════
    # A5: Site deviation structure (sparse linear)
    # ADVISOR FIX #1: dev_sparsity is THE primary control for |β_{0,c}|_0
    # ═══════════════════════════════════════════════════════════════════════
    dev_sparsity: int = 3                 # TOTAL nonzeros in β_{0,c} (THE governing constraint)
    dev_scale: float = 0.4                # Magnitude of corrections
    shared_support_frac: float = 0.67     # Fraction of dev_sparsity that's shared (e.g., 0.67 → 2/3 shared)
    restrict_deviation_to_first_k: Optional[int] = None  # e.g., 3 for effect modifiers only
    
    # Legacy (DEPRECATED, kept for backward compatibility)
    shared_support_size: Optional[int] = None   # Use shared_support_frac instead
    idiosyncratic_support_size: Optional[int] = None  # Computed from dev_sparsity - shared
    
    # A6: Transfer operator + nontransfer
    transfer_rank: int = 2                # rank(M*) - SHOULD BE <= dev_sparsity for identifiability
    transfer_strength: float = 1.0        # Scales M*
    transfer_structure: str = "low_rank"  # "low_rank", "rhoI", "diag", "diag_plus_low_rank"
    nontransfer_scale_source: float = 0.05  # Small for sources
    nontransfer_scale_target: float = 0.3   # Larger for target (degradation knob)
    
    # Heterogeneous noise
    noise_std_source: Optional[float] = None   # Override source noise
    noise_std_target: Optional[float] = None   # Override target noise
    
    # Misspecification r_{a,c}(x) (stress test)
    misspec_scale: float = 0.0            # Set >0 to test robustness
    misspec_nonlinear: bool = False       # Linear vs nonlinear misspec
    
    # Disconnected target control
    target_treated_frac: Optional[float] = None  # None = RCT; 0.0 = fully disconnected
    
    # Reproducibility
    random_state: int = 42


class SyntheticRCTGenerator:
    """
    DGP aligned with Assumptions A5 and A6.
    
    Decomposition:
        mu_{a,c}(x) = mu_a^proxy(x) + delta_{a,c}(x) + r_{a,c}(x)
                      └─shared────┘   └─sparse dev─┘   └misspec┘
    
    where:
        - mu_a^proxy(x) = x^T b_a (learned from sources)
        - delta_{a,c}(x) = x^T beta_{a,c} (site-specific, sparse)
        - beta_{1,c} = M* beta_{0,c} + nu_c (A6 cross-arm transfer)
        - r_{a,c}(x) optional misspecification
    
    ADVISOR FIX #1: dev_sparsity is THE governing constraint for |β_{0,c}|_0
    ADVISOR FIX #2: Reports rank(B0) and warns if Step B may be ill-posed
    
    Outcomes:
        Y = mu_{0,c}(X) + A * tau_c(X) + eps
        where tau_c(X) = mu_{1,c}(X) - mu_{0,c}(X)
    """
    
    def __init__(self, config: SyntheticRCTConfig = None):
        import warnings
        
        self.config = config or SyntheticRCTConfig()
        self.rng = np.random.default_rng(self.config.random_state)
        
        p = self.config.n_features
        r = min(self.config.transfer_rank, p)
        
        # ═════════════════════════════════════════════════════════════════
        # ADVISOR FINAL FIX #1: Strict sparsity allocation from dev_sparsity
        # dev_sparsity is THE governing constraint - legacy fields ignored
        # ═════════════════════════════════════════════════════════════════
        s_total = self.config.dev_sparsity
        
        # Handle legacy config: IGNORE legacy fields, always use dev_sparsity
        # (Previous soft-override caused confusion; clean policy is clearer)
        if self.config.shared_support_size is not None:
            warnings.warn(
                f"DEPRECATED: shared_support_size is ignored. Use dev_sparsity={s_total} "
                f"and shared_support_frac={self.config.shared_support_frac} instead. "
                f"idiosyncratic_support_size is also ignored."
            )
        
        # Compute requested allocation from dev_sparsity
        s_shared_requested = max(1, int(s_total * self.config.shared_support_frac))
        s_idio_requested = s_total - s_shared_requested
        
        # ═════════════════════════════════════════════════════════════════
        # ADVISOR FINAL FIX #2: Reconcile with available_support
        # Ensure realized sparsity = dev_sparsity when feasible
        # ═════════════════════════════════════════════════════════════════
        available_support = (list(range(self.config.restrict_deviation_to_first_k))
                            if self.config.restrict_deviation_to_first_k is not None
                            else list(range(p)))
        n_available = len(available_support)
        
        # Clamp to available features
        if s_total > n_available:
            warnings.warn(
                f"dev_sparsity ({s_total}) > available features ({n_available}). "
                f"Clamping to {n_available}."
            )
            s_total = n_available
        
        # Sample shared support first
        s_shared_actual = min(s_shared_requested, n_available)
        self.shared_support = self.rng.choice(
            available_support,
            size=s_shared_actual,
            replace=False
        )
        
        # Remaining features for idiosyncratic support
        remaining_support = list(set(available_support) - set(self.shared_support))
        s_idio_actual = min(s_total - s_shared_actual, len(remaining_support))
        
        # Store REALIZED sizes (what we actually use)
        self.s_shared_ = s_shared_actual
        self.s_idio_ = s_idio_actual
        self.s_total_realized_ = s_shared_actual + s_idio_actual
        
        # Warn if we couldn't achieve requested sparsity
        if self.s_total_realized_ < self.config.dev_sparsity:
            warnings.warn(
                f"Realized sparsity ({self.s_total_realized_}) < requested dev_sparsity ({self.config.dev_sparsity}) "
                f"due to limited available_support ({n_available}). "
                f"Increase restrict_deviation_to_first_k or n_features."
            )
        
        # ═════════════════════════════════════════════════════════════════
        # Identifiability check (pre-construction warning)
        # ═════════════════════════════════════════════════════════════════
        if self.s_total_realized_ < self.config.transfer_rank:
            warnings.warn(
                f"Step B identifiability warning: realized sparsity ({self.s_total_realized_}) < transfer_rank ({self.config.transfer_rank}). "
                f"M* may not be learnable beyond a subspace of dimension {self.s_total_realized_}."
            )
        
        # ═════════════════════════════════════════════════════════════════
        # Proxy coefficients (shared across all sites)
        # ═════════════════════════════════════════════════════════════════
        self.b0_proxy = self.rng.normal(0, 0.5, size=p)
        self.b1_proxy = self.rng.normal(0, 0.5, size=p)
        
        # Proxy nonlinearity coefficients (deterministic)
        if self.config.proxy_nonlinear_scale > 0:
            self.proxy_nonlin_coef0 = self.rng.normal(0, 1.0, size=2)
            self.proxy_nonlin_coef1 = self.rng.normal(0, 1.0, size=2)
        
        # ═════════════════════════════════════════════════════════════════
        # Misspecification parameters (FIXED: deterministic per site/arm)
        # ═════════════════════════════════════════════════════════════════
        self.misspec_w = {}
        if self.config.misspec_scale > 0 and not self.config.misspec_nonlinear:
            for c in range(0, self.config.n_source_sites + 1):
                for a in [0, 1]:
                    self.misspec_w[(c, a)] = self.rng.normal(0, 1.0, size=p)
        
        # Store remaining_support for site-specific idiosyncratic sampling
        self.remaining_support_ = remaining_support
        
        # ═════════════════════════════════════════════════════════════════
        # Transfer operator M* (A6 with controllable structure)
        # ═════════════════════════════════════════════════════════════════
        if self.config.transfer_structure == "rhoI":
            # Scalar: M* = ρ·I
            rho = self.config.transfer_strength
            self.M_star = rho * np.eye(p)
            
        elif self.config.transfer_structure == "diag":
            # Diagonal
            d = self.rng.normal(self.config.transfer_strength, 0.2, size=p)
            self.M_star = np.diag(d)
            
        elif self.config.transfer_structure == "diag_plus_low_rank":
            # diag(d) + U V^T
            d = self.rng.normal(0.5, 0.1, size=p)
            U = self.rng.normal(0, 1.0, size=(p, r))
            V = self.rng.normal(0, 1.0, size=(p, r))
            self.M_star = np.diag(d) + self.config.transfer_strength * (U @ V.T) / max(1, r)
            
        else:  # "low_rank" (default)
            # M* = U V^T with rank r
            U = self.rng.normal(0, 1.0, size=(p, r))
            V = self.rng.normal(0, 1.0, size=(p, r))
            self.M_star = self.config.transfer_strength * (U @ V.T) / max(1, r)
        
        # ═════════════════════════════════════════════════════════════════
        # Site-specific parameters
        # ═════════════════════════════════════════════════════════════════
        self.site_shifts = {}     # Covariate mean shift mu_c
        self.site_covs = {}       # Covariance matrices Sigma_c
        self.site_noise_std = {}  # Heterogeneous noise
        self.beta0 = {}           # Placebo deviations
        self.beta1 = {}           # Treated deviations
        self.nu = {}              # Nontransfer component
        
        # Generate for sources (c=1,2,3,...) and target (c=0)
        for c in range(0, self.config.n_source_sites + 1):
            # ─────────────────────────────────────────────────────────────
            # Covariate shift (mean)
            # ─────────────────────────────────────────────────────────────
            shift_scale = (self.config.covariate_shift_scale * 
                          self.config.target_shift_multiplier if c == 0 
                          else self.config.covariate_shift_scale)
            self.site_shifts[c] = self.rng.normal(0, shift_scale, size=p)
            
            # ─────────────────────────────────────────────────────────────
            # Covariance shift (optional)
            # ─────────────────────────────────────────────────────────────
            if self.config.cov_shift_strength > 0:
                # Random SPD perturbation
                A = self.rng.normal(0, self.config.cov_shift_strength, size=(p, p))
                Sigma_c = np.eye(p) + 0.5 * (A + A.T)
                # Ensure positive definite
                eigvals = np.linalg.eigvalsh(Sigma_c)
                if np.min(eigvals) < 0.1:
                    Sigma_c += (0.1 - np.min(eigvals)) * np.eye(p)
                self.site_covs[c] = Sigma_c
            else:
                self.site_covs[c] = np.eye(p)
            
            # ─────────────────────────────────────────────────────────────
            # Heterogeneous noise
            # ─────────────────────────────────────────────────────────────
            if c == 0 and self.config.noise_std_target is not None:
                self.site_noise_std[c] = self.config.noise_std_target
            elif c > 0 and self.config.noise_std_source is not None:
                self.site_noise_std[c] = self.config.noise_std_source
            else:
                self.site_noise_std[c] = self.config.noise_std
            
            # ─────────────────────────────────────────────────────────────
            # ADVISOR FINAL FIX #2: Sparse placebo deviation β_{0,c}
            # Uses pre-computed s_shared_ and s_idio_ (realized sizes)
            # ─────────────────────────────────────────────────────────────
            beta0_c = np.zeros(p)
            
            # Shared support (always included, s_shared_ features)
            beta0_c[self.shared_support] = self.rng.normal(
                0, self.config.dev_scale, size=len(self.shared_support)
            )
            
            # Idiosyncratic support (site-specific extras from remaining_support_)
            if self.s_idio_ > 0 and len(self.remaining_support_) > 0:
                idio_size = min(self.s_idio_, len(self.remaining_support_))
                idio_support = self.rng.choice(
                    self.remaining_support_, size=idio_size, replace=False
                )
                # Slightly smaller magnitude for idiosyncratic
                beta0_c[idio_support] = self.rng.normal(
                    0, self.config.dev_scale * 0.5, size=idio_size
                )
            
            # ─────────────────────────────────────────────────────────────
            # Nontransfer component nu_c
            # ─────────────────────────────────────────────────────────────
            nu_scale = (self.config.nontransfer_scale_target if c == 0 
                       else self.config.nontransfer_scale_source)
            nu_c = self.rng.normal(0, nu_scale, size=p)
            
            # ─────────────────────────────────────────────────────────────
            # Cross-arm transfer (A6)
            # ─────────────────────────────────────────────────────────────
            beta1_c = self.M_star @ beta0_c + nu_c
            
            # Store
            self.beta0[c] = beta0_c
            self.beta1[c] = beta1_c
            self.nu[c] = nu_c
    
    def _misspec(self, X: np.ndarray, site_id: int, arm: int) -> np.ndarray:
        """
        Optional misspecification r_{a,c}(x).
        
        FIXED: Now deterministic (uses pre-sampled parameters).
        Returns residual that's not captured by the linear model.
        """
        if self.config.misspec_scale <= 0:
            return np.zeros(X.shape[0])
        
        if not self.config.misspec_nonlinear:
            # FIXED: Use pre-sampled deterministic w
            w = self.misspec_w[(site_id, arm)]
            return self.config.misspec_scale * (X @ w) / np.sqrt(X.shape[1])
        else:
            # Nonlinear: sin interaction on first two features (already deterministic)
            return self.config.misspec_scale * np.sin(X[:, 0] * X[:, 1])
    
    def _mu(self, X: np.ndarray, site_id: int, arm: int) -> np.ndarray:
        """
        Compute mu_{a,c}(x) = x^T b_a + nonlin(x) + x^T beta_{a,c} + r_{a,c}(x).
        
        NEW: Adds mild nonlinearity to proxy to make Stage 1 nontrivial.
        
        Parameters
        ----------
        X : array-like, shape (n, p)
        site_id : int (0=target, 1,2,3,...)
        arm : int (0=placebo, 1=treated)
        
        Returns
        -------
        mu : array, shape (n,)
        """
        if arm == 0:
            base = X @ self.b0_proxy         # Proxy linear (shared)
            dev = X @ self.beta0[site_id]    # Site deviation (sparse)
            
            # Add mild nonlinearity to proxy
            if self.config.proxy_nonlinear_scale > 0:
                c0, c1 = self.proxy_nonlin_coef0
                base = base + self.config.proxy_nonlinear_scale * (
                    c0 * np.sin(X[:, 0]) + c1 * 0.5 * X[:, 1]**2
                )
        else:
            base = X @ self.b1_proxy
            dev = X @ self.beta1[site_id]
            
            # Add mild nonlinearity to proxy
            if self.config.proxy_nonlinear_scale > 0:
                c0, c1 = self.proxy_nonlin_coef1
                base = base + self.config.proxy_nonlinear_scale * (
                    c0 * np.sin(X[:, 0]) + c1 * 0.5 * X[:, 1]**2
                )
        
        misspec = self._misspec(X, site_id, arm)
        
        return base + dev + misspec
    
    def generate_site_data(self, site_id: int, n_samples: int) -> Dict:
        """
        Generate data for one site.
        
        Parameters
        ----------
        site_id : int
            0 = target, 1,2,3,... = sources
        n_samples : int
            Number of samples
        
        Returns
        -------
        data : dict with keys
            X : array (n, p) - covariates
            A : array (n,) - treatment assignments
            Y : array (n,) - observed outcomes
            tau_true : array (n,) - true CATE
            mu0_true : array (n,) - true mu_0(X)
            mu1_true : array (n,) - true mu_1(X)
            c : array (n,) - site indicator
        """
        p = self.config.n_features
        
        # ═════════════════════════════════════════════════════════════════
        # Covariates X | site (with mean and covariance shift)
        # ═════════════════════════════════════════════════════════════════
        shift = self.site_shifts[site_id]
        Sigma = self.site_covs[site_id]
        
        # Generate from N(0, Sigma), then shift
        if np.allclose(Sigma, np.eye(p)):
            # Fast path: no covariance shift
            X = self.rng.normal(0, 1.0, size=(n_samples, p)) + shift
        else:
            # Cholesky decomposition for covariance
            L = np.linalg.cholesky(Sigma)
            Z = self.rng.normal(0, 1.0, size=(n_samples, p))
            X = Z @ L.T + shift
        
        # ═════════════════════════════════════════════════════════════════
        # Treatment A | site
        # ═════════════════════════════════════════════════════════════════
        if site_id == 0 and self.config.target_treated_frac is not None:
            # Override for disconnected target
            A = self.rng.binomial(1, self.config.target_treated_frac, size=n_samples)
        else:
            # Standard RCT with site-specific propensities
            if site_id == 0:
                # Target site
                e = self.config.treatment_prob_target or self.config.treatment_prob
            else:
                # Source sites
                e = self.config.treatment_prob_source or self.config.treatment_prob
            A = self.rng.binomial(1, e, size=n_samples)
        
        # ═════════════════════════════════════════════════════════════════
        # Potential outcomes
        # ═════════════════════════════════════════════════════════════════
        mu0 = self._mu(X, site_id, arm=0)
        mu1 = self._mu(X, site_id, arm=1)
        tau = mu1 - mu0
        
        # ═════════════════════════════════════════════════════════════════
        # Observed outcome Y (with heterogeneous noise)
        # ═════════════════════════════════════════════════════════════════
        noise_std = self.site_noise_std[site_id]
        eps = self.rng.normal(0, noise_std, size=n_samples)
        Y = mu0 + A * tau + eps
        
        # ═════════════════════════════════════════════════════════════════
        # Site indicator
        # ═════════════════════════════════════════════════════════════════
        c = np.full(n_samples, site_id, dtype=int)
        
        return dict(
            X=X, 
            A=A, 
            Y=Y, 
            tau_true=tau, 
            mu0_true=mu0, 
            mu1_true=mu1, 
            c=c
        )
    
    def generate_full_dataset(self) -> Tuple[Dict, Dict]:
        """
        Generate complete multi-site dataset.
        
        Returns
        -------
        source_data : dict
            Pooled source data (sites 1, 2, 3)
        target_data : dict
            Target data (site 0)
        """
        # Generate source sites
        source_datasets = [
            self.generate_site_data(c, self.config.n_source_per_site)
            for c in range(1, self.config.n_source_sites + 1)
        ]
        
        # Pool sources
        source_data = {}
        for key in source_datasets[0].keys():
            if key == 'X':
                source_data[key] = np.vstack([d[key] for d in source_datasets])
            else:
                source_data[key] = np.concatenate([d[key] for d in source_datasets])
        
        # Generate target
        target_data = self.generate_site_data(0, self.config.n_target)
        
        return source_data, target_data
    
    def get_diagnostics(self) -> Dict:
        """
        Return diagnostic information about the DGP.
        
        ADVISOR FIX #2: Now includes Step B identifiability diagnostics:
        - rank(B0): rank of stacked β_{0,c} matrix across sources
        - identifiability_warning: True if rank(B0) < transfer_rank
        
        Also includes transfer quality metrics (SNR, cosine similarity).
        """
        diag = {
            'n_features': self.config.n_features,
            'n_source_sites': self.config.n_source_sites,
            'b0_proxy': self.b0_proxy,
            'b1_proxy': self.b1_proxy,
            'M_star': self.M_star,
            'M_star_norm': float(np.linalg.norm(self.M_star, 'fro')),
            'M_star_rank': int(np.linalg.matrix_rank(self.M_star)),
            'transfer_structure': self.config.transfer_structure,
            'shared_support': list(self.shared_support),
            'shared_support_size': len(self.shared_support),
            # ADVISOR FINAL FIX: Report REALIZED sparsity allocation
            'dev_sparsity_requested': self.config.dev_sparsity,
            'dev_sparsity_realized': self.s_total_realized_,
            's_shared': self.s_shared_,
            's_idio': self.s_idio_,
        }
        
        # ═════════════════════════════════════════════════════════════════
        # ADVISOR FINAL FIX #3: Step B identifiability + conditioning
        # ═════════════════════════════════════════════════════════════════
        # Build B0 matrix from SOURCE sites only (not target)
        B0_list = [self.beta0[c] for c in range(1, self.config.n_source_sites + 1)]
        B0 = np.column_stack(B0_list) if B0_list else np.zeros((self.config.n_features, 1))
        
        rank_B0 = int(np.linalg.matrix_rank(B0))
        diag['rank_B0'] = rank_B0
        diag['B0_shape'] = B0.shape
        
        # ADVISOR FINAL FIX #3: Add singular value / condition number diagnostics
        svals = np.linalg.svd(B0, compute_uv=False)
        diag['B0_singular_values'] = svals.tolist()
        diag['B0_singular_value_max'] = float(svals[0]) if len(svals) > 0 else 0.0
        diag['B0_singular_value_min'] = float(svals[-1]) if len(svals) > 0 else 0.0
        diag['B0_condition_number'] = float(svals[0] / (svals[-1] + 1e-12)) if len(svals) > 0 else float('inf')
        
        # Check identifiability
        transfer_rank = self.config.transfer_rank
        identifiable = rank_B0 >= transfer_rank
        diag['stepB_identifiable'] = identifiable
        
        # Conditioning warning (even if rank is OK, bad conditioning can cause issues)
        condition_threshold = 100.0  # Heuristic threshold
        well_conditioned = diag['B0_condition_number'] < condition_threshold
        diag['stepB_well_conditioned'] = well_conditioned
        
        if not identifiable:
            diag['identifiability_warning'] = (
                f"rank(B0)={rank_B0} < transfer_rank={transfer_rank}. "
                f"M* is only learnable on a {rank_B0}-dimensional subspace. "
                f"Consider increasing dev_sparsity or n_source_sites."
            )
        elif not well_conditioned:
            diag['identifiability_warning'] = (
                f"B0 is rank-sufficient but poorly conditioned (κ={diag['B0_condition_number']:.1f}). "
                f"Step B may be numerically unstable. Consider increasing s_idio (more site variation)."
            )
        else:
            diag['identifiability_warning'] = None
        
        # Also check dev_sparsity vs transfer_rank
        if self.s_total_realized_ < transfer_rank:
            diag['sparsity_vs_rank_warning'] = (
                f"realized_sparsity={self.s_total_realized_} < transfer_rank={transfer_rank}. "
                f"This limits the effective rank of B0."
            )
        else:
            diag['sparsity_vs_rank_warning'] = None
        
        # ═════════════════════════════════════════════════════════════════
        # Per-site deviations and transfer quality
        # ═════════════════════════════════════════════════════════════════
        for c in range(0, self.config.n_source_sites + 1):
            site_name = 'target' if c == 0 else f'source_{c}'
            beta0_c = self.beta0[c]
            beta1_c = self.beta1[c]
            nu_c = self.nu[c]
            
            diag[f'{site_name}_beta0'] = beta0_c
            diag[f'{site_name}_beta1'] = beta1_c
            diag[f'{site_name}_nu'] = nu_c
            diag[f'{site_name}_sparsity'] = int(np.sum(np.abs(beta0_c) > 1e-6))
            diag[f'{site_name}_support'] = list(np.where(np.abs(beta0_c) > 1e-6)[0])
            diag[f'{site_name}_nu_norm'] = float(np.linalg.norm(nu_c))
            
            # Transfer quality metrics
            M_beta0 = self.M_star @ beta0_c
            diag[f'{site_name}_M_beta0_norm'] = float(np.linalg.norm(M_beta0))
            
            # Signal-to-noise ratio: ||M*β₀|| / ||ν||
            if np.linalg.norm(nu_c) > 1e-10:
                snr = np.linalg.norm(M_beta0) / np.linalg.norm(nu_c)
                diag[f'{site_name}_transfer_SNR'] = float(snr)
            else:
                diag[f'{site_name}_transfer_SNR'] = float('inf')
            
            # Cosine similarity: <β₁, M*β₀> / (||β₁|| ||M*β₀||)
            if np.linalg.norm(beta1_c) > 1e-10 and np.linalg.norm(M_beta0) > 1e-10:
                cosine = np.dot(beta1_c, M_beta0) / (np.linalg.norm(beta1_c) * np.linalg.norm(M_beta0))
                diag[f'{site_name}_cosine_sim'] = float(cosine)
            else:
                diag[f'{site_name}_cosine_sim'] = 0.0
        
        # Verify A6: beta1 ≈ M* beta0 + nu (should be exact by construction)
        for c in range(1, self.config.n_source_sites + 1):
            predicted = self.M_star @ self.beta0[c]
            actual = self.beta1[c] - self.nu[c]
            diag[f'source_{c}_A6_error'] = float(np.linalg.norm(predicted - actual))
        
        # Aggregate metrics
        source_snrs = [diag[f'source_{c}_transfer_SNR'] 
                      for c in range(1, self.config.n_source_sites + 1)
                      if diag[f'source_{c}_transfer_SNR'] != float('inf')]
        if source_snrs:
            diag['mean_source_SNR'] = float(np.mean(source_snrs))
            diag['median_source_SNR'] = float(np.median(source_snrs))
        
        return diag


# ═════════════════════════════════════════════════════════════════════════
# Convenience functions
# ═════════════════════════════════════════════════════════════════════════

def generate_synthetic_rct(
    n_source_sites: int = 10,
    n_target: int = 200,
    n_source_per_site: int = 500,
    random_state: int = 42,
    **config_kwargs
) -> Tuple[Dict, Dict, SyntheticRCTGenerator]:
    """
    Convenience wrapper for generating synthetic RCT data.
    
    ADVISOR FIXES:
    - Default 10 source sites for Step B identifiability
    - dev_sparsity (default 3) controls |β_{0,c}|_0 directly
    - transfer_rank (default 2) should be <= dev_sparsity
    
    Parameters
    ----------
    n_source_sites : int (default 10)
        Number of source sites. More sites help Step B identifiability.
    n_target : int
        Target site sample size
    n_source_per_site : int
        Samples per source site
    random_state : int
        Random seed
    **config_kwargs : additional config overrides
        - dev_sparsity: int (THE control for |β_{0,c}|_0, default 3)
        - shared_support_frac: float (fraction of sparsity that's shared, default 0.67)
        - transfer_rank: int (rank of M*, should be <= dev_sparsity, default 2)
        - transfer_structure: str ("low_rank", "rhoI", "diag", "diag_plus_low_rank")
        - nontransfer_scale_target: float (degradation knob)
        - proxy_nonlinear_scale: float (default 0.5, makes Stage 1 nontrivial)
    
    Returns
    -------
    source_data : dict
    target_data : dict
    generator : SyntheticRCTGenerator (for diagnostics including rank_B0)
    """
    config = SyntheticRCTConfig(
        n_source_sites=n_source_sites,
        n_target=n_target,
        n_source_per_site=n_source_per_site,
        random_state=random_state,
        **config_kwargs
    )
    
    generator = SyntheticRCTGenerator(config)
    source_data, target_data = generator.generate_full_dataset()
    
    return source_data, target_data, generator


def generate_disconnected_target(
    n_source_sites: int = 10,
    n_target: int = 200,
    n_source_per_site: int = 500,
    nontransfer_scale_target: float = 0.3,
    random_state: int = 42,
    **config_kwargs
) -> Tuple[Dict, Dict, SyntheticRCTGenerator]:
    """
    Generate data with disconnected target (placebo-only).
    
    Useful for testing Option B / Step B.
    NEW: Default 10 sites (increased from 3).
    """
    return generate_synthetic_rct(
        n_source_sites=n_source_sites,
        n_target=n_target,
        n_source_per_site=n_source_per_site,
        target_treated_frac=0.0,  # No treated samples!
        nontransfer_scale_target=nontransfer_scale_target,
        random_state=random_state,
        **config_kwargs
    )


def sweep_nontransfer(
    nontransfer_scales: list = [0.0, 0.1, 0.2, 0.4, 0.8],
    n_source_sites: int = 10,
    n_target: int = 200,
    random_state: int = 42
) -> list:
    """
    Generate multiple datasets with varying cross-arm validity.
    
    Returns list of (source, target, generator) tuples.
    NEW: Default 10 sites (increased from 3).
    """
    datasets = []
    for scale in nontransfer_scales:
        source, target, gen = generate_synthetic_rct(
            n_source_sites=n_source_sites,
            n_target=n_target,
            nontransfer_scale_target=scale,
            random_state=random_state
        )
        datasets.append((source, target, gen))
    return datasets


# ═══════════════════════════════════════════════════════════════════════════════
# L1-TCL DGP (from arXiv 2305.09126v3)
# ═══════════════════════════════════════════════════════════════════════════════
# 
# Reference: "Transfer Causal Learning" by the L1-TCL authors
# Key differences from our main DGP:
#   1. Constant ATE τ (no heterogeneous CATE)
#   2. 2 covariates only (X1, X2)
#   3. Focus on propensity score transfer, not outcome model transfer
#   4. Linear outcome: Y = τZ + αX₂ + ε
#
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class L1TCLConfig:
    """
    Configuration for L1-TCL toy DGP (arXiv 2305.09126v3).
    
    DGP Structure:
        Treatment assignment: P(Z=1|X₁,X₂) = sigmoid(β₁X₁ + β₂X₂)
        Outcome: Y = τZ + αX₂ + ε
    
    Key feature: Different propensity score parameters between domains,
    but the outcome model structure is the same (only τ, α can differ).
    """
    
    # Sample sizes
    n_target: int = 100           # Limited target data (the challenge)
    n_source: int = 1000          # Abundant source data
    
    # Covariate distributions
    # Target domain
    mu1_target: float = 0.0       # E[X₁] in target
    mu2_target: float = 2.0       # E[X₂] in target
    # Source domain
    mu1_source: float = 0.0       # E[X₁] in source
    mu2_source: float = 1.0       # E[X₂] in source
    
    # Propensity score: P(Z=1|X) = sigmoid(β₁X₁ + β₂X₂)
    # Target domain
    beta1_target: float = 0.1     # Coefficient for X₁ in target
    beta2_target: float = -0.1    # Coefficient for X₂ in target
    # Source domain (different PS!)
    beta1_source: float = 0.1     # Coefficient for X₁ in source
    beta2_source: float = -0.2    # Coefficient for X₂ in source (KEY DIFFERENCE)
    
    # Outcome model: Y = τZ + αX₂ + ε
    # Target domain
    tau_target: float = -2/30     # ≈ -0.067 (the ATE we want to estimate)
    alpha_target: float = 0.1     # Effect of X₂ on outcome
    # Source domain (can be same or different)
    tau_source: Optional[float] = None   # If None, same as target
    alpha_source: Optional[float] = None # If None, same as target
    
    # Noise
    noise_std: float = 0.5        # std(ε) = 0.5 → Var(ε) = 0.25
    
    # Reproducibility
    random_state: int = 42


class L1TCLGenerator:
    """
    Generator for L1-TCL toy DGP (arXiv 2305.09126v3).
    
    This DGP is designed to study transfer learning for propensity score
    estimation, NOT for CATE estimation. Key characteristics:
    
    1. Constant treatment effect τ (no heterogeneity)
    2. Only 2 covariates (X₁, X₂)
    3. Propensity scores DIFFER between domains (the transfer challenge)
    4. Outcome model is linear: Y = τZ + αX₂ + ε
    
    The goal is to use source domain data to improve PS estimation in
    the target domain, which improves IPW/AIPW estimators for ATE.
    
    DGP Equations:
    
        Covariates:
            X₁ ~ N(μ₁, 1)
            X₂ ~ N(μ₂, 1)
        
        Treatment (propensity score differs by domain):
            P(Z=1|X₁,X₂) = sigmoid(β₁X₁ + β₂X₂)
            where β₁, β₂ are domain-specific
        
        Outcome (same structure, parameters can differ):
            Y = τZ + αX₂ + ε,  ε ~ N(0, σ²)
    
    Example usage:
        >>> config = L1TCLConfig(n_target=100, n_source=1000)
        >>> gen = L1TCLGenerator(config)
        >>> source_data, target_data = gen.generate_full_dataset()
        >>> print(f"True ATE: {config.tau_target:.4f}")
    """
    
    def __init__(self, config: L1TCLConfig = None):
        self.config = config or L1TCLConfig()
        self.rng = np.random.default_rng(self.config.random_state)
        
        # Resolve source parameters (default to target values if not specified)
        self.tau_source = (self.config.tau_source 
                          if self.config.tau_source is not None 
                          else self.config.tau_target)
        self.alpha_source = (self.config.alpha_source 
                            if self.config.alpha_source is not None 
                            else self.config.alpha_target)
    
    @staticmethod
    def sigmoid(x: np.ndarray) -> np.ndarray:
        """Sigmoid function: g(x) = 1 / (1 + exp(x))."""
        # Note: L1-TCL uses g(x) = 1/(1+exp(x)), NOT 1/(1+exp(-x))
        # This means higher linear predictor → LOWER probability
        return 1.0 / (1.0 + np.exp(x))
    
    def _propensity(self, X: np.ndarray, domain: str) -> np.ndarray:
        """
        Compute propensity score P(Z=1|X).
        
        Parameters
        ----------
        X : array, shape (n, 2)
            Covariates [X₁, X₂]
        domain : str
            'target' or 'source'
        """
        if domain == 'target':
            beta1 = self.config.beta1_target
            beta2 = self.config.beta2_target
        else:
            beta1 = self.config.beta1_source
            beta2 = self.config.beta2_source
        
        linear_pred = beta1 * X[:, 0] + beta2 * X[:, 1]
        return self.sigmoid(linear_pred)
    
    def _outcome(self, X: np.ndarray, Z: np.ndarray, domain: str) -> np.ndarray:
        """
        Compute outcome Y = τZ + αX₂ + ε.
        
        Parameters
        ----------
        X : array, shape (n, 2)
        Z : array, shape (n,) - treatment indicator
        domain : str
        """
        if domain == 'target':
            tau = self.config.tau_target
            alpha = self.config.alpha_target
        else:
            tau = self.tau_source
            alpha = self.alpha_source
        
        eps = self.rng.normal(0, self.config.noise_std, size=len(Z))
        Y = tau * Z + alpha * X[:, 1] + eps
        return Y
    
    def generate_domain_data(self, domain: str, n_samples: int = None) -> Dict:
        """
        Generate data for one domain.
        
        Parameters
        ----------
        domain : str
            'target' or 'source'
        n_samples : int, optional
            Override sample size
        
        Returns
        -------
        data : dict with keys
            X : array (n, 2) - covariates
            A : array (n,) - treatment indicator (Z in paper notation)
            Y : array (n,) - observed outcome
            e_true : array (n,) - true propensity score
            tau_true : array (n,) - true CATE (constant)
            mu0_true : array (n,) - E[Y|Z=0, X]
            mu1_true : array (n,) - E[Y|Z=1, X]
        """
        # Determine sample size
        if n_samples is None:
            n_samples = (self.config.n_target if domain == 'target' 
                        else self.config.n_source)
        
        # Get domain-specific parameters
        if domain == 'target':
            mu1 = self.config.mu1_target
            mu2 = self.config.mu2_target
            tau = self.config.tau_target
            alpha = self.config.alpha_target
        else:
            mu1 = self.config.mu1_source
            mu2 = self.config.mu2_source
            tau = self.tau_source
            alpha = self.alpha_source
        
        # Generate covariates
        X1 = self.rng.normal(mu1, 1.0, size=n_samples)
        X2 = self.rng.normal(mu2, 1.0, size=n_samples)
        X = np.column_stack([X1, X2])
        
        # Generate treatment (propensity score model)
        e_true = self._propensity(X, domain)
        Z = self.rng.binomial(1, e_true, size=n_samples)
        
        # Generate outcome
        Y = self._outcome(X, Z, domain)
        
        # Compute true potential outcomes for evaluation
        # Y(0) = αX₂ (no treatment)
        # Y(1) = τ + αX₂ (with treatment)
        mu0_true = alpha * X[:, 1]
        mu1_true = tau + alpha * X[:, 1]
        tau_true = np.full(n_samples, tau)  # Constant CATE
        
        return dict(
            X=X,
            A=Z,
            Y=Y,
            e_true=e_true,
            tau_true=tau_true,
            mu0_true=mu0_true,
            mu1_true=mu1_true,
            c=np.zeros(n_samples, dtype=int) if domain == 'target' else np.ones(n_samples, dtype=int)
        )
    
    def generate_full_dataset(self) -> Tuple[Dict, Dict]:
        """
        Generate complete source and target datasets.
        
        Returns
        -------
        source_data : dict
        target_data : dict
        """
        source_data = self.generate_domain_data('source')
        target_data = self.generate_domain_data('target')
        return source_data, target_data
    
    def get_diagnostics(self) -> Dict:
        """
        Return diagnostic information about the L1-TCL DGP.
        """
        # Compute some theoretical quantities
        # Treatment probability at covariate means
        X_target_mean = np.array([[self.config.mu1_target, self.config.mu2_target]])
        X_source_mean = np.array([[self.config.mu1_source, self.config.mu2_source]])
        
        e_target_at_mean = self._propensity(X_target_mean, 'target')[0]
        e_source_at_mean = self._propensity(X_source_mean, 'source')[0]
        
        # PS parameter difference (the "sparse difference" in L1-TCL)
        delta_beta = np.array([
            self.config.beta1_target - self.config.beta1_source,
            self.config.beta2_target - self.config.beta2_source
        ])
        
        return {
            'dgp_type': 'L1-TCL',
            'n_features': 2,
            'n_target': self.config.n_target,
            'n_source': self.config.n_source,
            
            # Covariate shifts
            'mu_target': [self.config.mu1_target, self.config.mu2_target],
            'mu_source': [self.config.mu1_source, self.config.mu2_source],
            
            # Propensity score parameters
            'beta_target': [self.config.beta1_target, self.config.beta2_target],
            'beta_source': [self.config.beta1_source, self.config.beta2_source],
            'delta_beta': delta_beta.tolist(),
            'delta_beta_sparsity': int(np.sum(np.abs(delta_beta) > 1e-10)),
            
            # Treatment probabilities at covariate means
            'e_target_at_mean': float(e_target_at_mean),
            'e_source_at_mean': float(e_source_at_mean),
            
            # Outcome parameters
            'tau_target': self.config.tau_target,
            'tau_source': self.tau_source,
            'alpha_target': self.config.alpha_target,
            'alpha_source': self.alpha_source,
            'tau_same_across_domains': abs(self.config.tau_target - self.tau_source) < 1e-10,
            
            # Noise
            'noise_std': self.config.noise_std,
            'noise_var': self.config.noise_std ** 2,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# L1-TCL Extended DGP (matching their full experimental setup)
# ═══════════════════════════════════════════════════════════════════════════════
#
# This extends the toy DGP to support:
#   1. Variable dimensionality d ∈ {10, 20, 50, 75, 100}
#   2. Variable sparsity s ∈ {1, 3, 5, 7, 10} in Δβ
#   3. Multiple source sites (like our main DGP)
#
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class L1TCLExtendedConfig:
    """
    Extended L1-TCL configuration matching their full experimental setup.
    
    Key changes from toy DGP:
    - Variable dimensionality d (not just 2)
    - Variable sparsity s in PS parameter difference
    - Multiple source sites (like our main DGP)
    - Outcome model: Y = τZ + α^T X + ε (uses all covariates)
    
    DGP Structure:
        Treatment: P(Z=1|X) = sigmoid(X^T β)  where β ∈ R^d
        Outcome: Y = τZ + α^T X + ε
        
        Source-target difference: Δβ = β_target - β_source is s-sparse
    """
    
    # Dimensionality (paper sweeps: d ∈ {10, 20, 50, 75, 100})
    n_features: int = 20
    
    # Sparsity of PS difference (paper sweeps: s ∈ {1, 3, 5, 7, 10})
    ps_sparsity: int = 3
    
    # Sample sizes (paper sweeps)
    n_target: int = 100                    # Paper: n ∈ {100, 200, 500}
    n_source_per_site: int = 500           # Paper: n_s ∈ {2000, 3000, 5000} (single source)
    n_source_sites: int = 10               # OUR ADDITION: multiple sources like main DGP
    
    # Covariate distribution
    covariate_shift_scale: float = 0.5     # Mean shift between domains
    target_shift_multiplier: float = 1.5   # Target has more shift (like main DGP)
    
    # PS parameters
    beta_scale: float = 0.2                # Scale of β coefficients
    delta_beta_scale: float = 0.3          # Scale of sparse difference Δβ
    
    # Outcome model: Y = τZ + α^T X + ε
    tau_target: float = -0.067             # ≈ -2/30 (from paper)
    tau_source: Optional[float] = None     # If None, same as target
    alpha_scale: float = 0.1               # Scale of outcome coefficients
    
    # Noise
    noise_std: float = 0.5
    
    # Treatment probability (RCT-like)
    treatment_prob: float = 0.5
    
    # Reproducibility
    random_state: int = 42


class L1TCLExtendedGenerator:
    """
    Extended L1-TCL generator matching their full experimental setup.
    
    Key features:
    1. Variable dimensionality d (configurable)
    2. Sparse PS difference: Δβ = β_target - β_source is s-sparse
    3. Multiple source sites with site-specific PS parameters
    4. Linear outcome: Y = τZ + α^T X + ε
    
    Source sites share a common β_source but have small site-specific perturbations.
    Target has a sparse deviation Δβ from the source parameters.
    
    This allows testing how well methods leverage source data when:
    - The PS model differs between source and target
    - The difference is sparse (L1-TCL assumption)
    - Multiple source sites provide more data
    """
    
    def __init__(self, config: L1TCLExtendedConfig = None):
        self.config = config or L1TCLExtendedConfig()
        self.rng = np.random.default_rng(self.config.random_state)
        
        d = self.config.n_features
        s = self.config.ps_sparsity
        
        # ═══════════════════════════════════════════════════════════════════════
        # Generate base PS parameters (shared across sources)
        # ═══════════════════════════════════════════════════════════════════════
        self.beta_source_base = self.rng.normal(0, self.config.beta_scale, size=d)
        
        # ═══════════════════════════════════════════════════════════════════════
        # Generate sparse difference Δβ (s nonzeros)
        # ═══════════════════════════════════════════════════════════════════════
        self.delta_beta_support = self.rng.choice(d, size=min(s, d), replace=False)
        self.delta_beta = np.zeros(d)
        self.delta_beta[self.delta_beta_support] = self.rng.normal(
            0, self.config.delta_beta_scale, size=len(self.delta_beta_support)
        )
        
        # Target PS parameters = source + sparse diff
        self.beta_target = self.beta_source_base + self.delta_beta
        
        # ═══════════════════════════════════════════════════════════════════════
        # Site-specific PS perturbations (small noise for each source site)
        # ═══════════════════════════════════════════════════════════════════════
        self.beta_sources = {}
        for c in range(1, self.config.n_source_sites + 1):
            # Small site-specific perturbation (much smaller than Δβ)
            site_noise = self.rng.normal(0, self.config.beta_scale * 0.1, size=d)
            self.beta_sources[c] = self.beta_source_base + site_noise
        
        # ═══════════════════════════════════════════════════════════════════════
        # Outcome coefficients α (shared across all domains)
        # ═══════════════════════════════════════════════════════════════════════
        self.alpha = self.rng.normal(0, self.config.alpha_scale, size=d)
        
        # ═══════════════════════════════════════════════════════════════════════
        # Covariate shifts per site
        # ═══════════════════════════════════════════════════════════════════════
        self.site_shifts = {}
        for c in range(0, self.config.n_source_sites + 1):
            shift_scale = (self.config.covariate_shift_scale * 
                          self.config.target_shift_multiplier if c == 0 
                          else self.config.covariate_shift_scale)
            self.site_shifts[c] = self.rng.normal(0, shift_scale, size=d)
        
        # Resolve tau_source
        self.tau_source = (self.config.tau_source 
                          if self.config.tau_source is not None 
                          else self.config.tau_target)
    
    @staticmethod
    def sigmoid(x: np.ndarray) -> np.ndarray:
        """Standard sigmoid: g(x) = 1 / (1 + exp(-x))."""
        # Use standard sigmoid (not L1-TCL's inverse)
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))
    
    def _propensity(self, X: np.ndarray, site_id: int) -> np.ndarray:
        """
        Compute propensity score P(Z=1|X) for a site.
        
        Parameters
        ----------
        X : array, shape (n, d)
        site_id : int (0=target, 1,2,...=sources)
        """
        if site_id == 0:
            beta = self.beta_target
        else:
            beta = self.beta_sources[site_id]
        
        linear_pred = X @ beta
        return self.sigmoid(linear_pred)
    
    def generate_site_data(self, site_id: int, n_samples: int) -> Dict:
        """
        Generate data for one site.
        
        Parameters
        ----------
        site_id : int
            0 = target, 1,2,... = sources
        n_samples : int
        
        Returns
        -------
        data : dict
        """
        d = self.config.n_features
        
        # Covariates with site-specific shift
        shift = self.site_shifts[site_id]
        X = self.rng.normal(0, 1.0, size=(n_samples, d)) + shift
        
        # Treatment (RCT-like, but PS varies by site)
        # Use constant treatment prob for simplicity (RCT design)
        A = self.rng.binomial(1, self.config.treatment_prob, size=n_samples)
        
        # True propensity (for diagnostics)
        e_true = self._propensity(X, site_id)
        
        # Outcome: Y = τZ + α^T X + ε
        tau = self.config.tau_target if site_id == 0 else self.tau_source
        mu0 = X @ self.alpha
        mu1 = tau + X @ self.alpha
        
        eps = self.rng.normal(0, self.config.noise_std, size=n_samples)
        Y = mu0 + A * tau + eps
        
        tau_true = np.full(n_samples, tau)  # Constant CATE
        
        return dict(
            X=X,
            A=A,
            Y=Y,
            e_true=e_true,
            tau_true=tau_true,
            mu0_true=mu0,
            mu1_true=mu1,
            c=np.full(n_samples, site_id, dtype=int)
        )
    
    def generate_full_dataset(self) -> Tuple[Dict, Dict]:
        """
        Generate complete multi-site dataset.
        
        Returns
        -------
        source_data : dict (pooled from all source sites)
        target_data : dict
        """
        # Generate source sites
        source_datasets = [
            self.generate_site_data(c, self.config.n_source_per_site)
            for c in range(1, self.config.n_source_sites + 1)
        ]
        
        # Pool sources
        source_data = {}
        for key in source_datasets[0].keys():
            if key == 'X':
                source_data[key] = np.vstack([d[key] for d in source_datasets])
            else:
                source_data[key] = np.concatenate([d[key] for d in source_datasets])
        
        # Generate target
        target_data = self.generate_site_data(0, self.config.n_target)
        
        return source_data, target_data
    
    def get_diagnostics(self) -> Dict:
        """Return diagnostic information about the extended L1-TCL DGP."""
        return {
            'dgp_type': 'L1-TCL-Extended',
            'n_features': self.config.n_features,
            'ps_sparsity': self.config.ps_sparsity,
            'n_source_sites': self.config.n_source_sites,
            'n_target': self.config.n_target,
            'n_source_per_site': self.config.n_source_per_site,
            'n_source_total': self.config.n_source_sites * self.config.n_source_per_site,
            
            # PS parameters
            'beta_target': self.beta_target.tolist(),
            'beta_source_base': self.beta_source_base.tolist(),
            'delta_beta': self.delta_beta.tolist(),
            'delta_beta_support': self.delta_beta_support.tolist(),
            'delta_beta_nnz': int(np.sum(np.abs(self.delta_beta) > 1e-10)),
            'delta_beta_norm': float(np.linalg.norm(self.delta_beta)),
            
            # Outcome parameters
            'tau_target': self.config.tau_target,
            'tau_source': self.tau_source,
            'alpha': self.alpha.tolist(),
            
            # Noise
            'noise_std': self.config.noise_std,
        }


def generate_l1tcl_extended(
    n_features: int = 20,
    ps_sparsity: int = 3,
    n_target: int = 100,
    n_source_per_site: int = 500,
    n_source_sites: int = 10,
    random_state: int = 42,
    **config_kwargs
) -> Tuple[Dict, Dict, L1TCLExtendedGenerator]:
    """
    Generate data using extended L1-TCL DGP.
    
    Parameters
    ----------
    n_features : int
        Dimensionality d (paper: {10, 20, 50, 75, 100})
    ps_sparsity : int
        Sparsity s of PS difference (paper: {1, 3, 5, 7, 10})
    n_target : int
        Target sample size (paper: {100, 200, 500})
    n_source_per_site : int
        Samples per source site
    n_source_sites : int
        Number of source sites (OUR ADDITION: 10 like main DGP)
    random_state : int
    
    Returns
    -------
    source_data, target_data, generator
    """
    config = L1TCLExtendedConfig(
        n_features=n_features,
        ps_sparsity=ps_sparsity,
        n_target=n_target,
        n_source_per_site=n_source_per_site,
        n_source_sites=n_source_sites,
        random_state=random_state,
        **config_kwargs
    )
    
    generator = L1TCLExtendedGenerator(config)
    source_data, target_data = generator.generate_full_dataset()
    
    return source_data, target_data, generator


def generate_l1tcl_data(
    n_target: int = 100,
    n_source: int = 1000,
    tau_target: float = -2/30,
    same_tau: bool = True,
    random_state: int = 42,
    **config_kwargs
) -> Tuple[Dict, Dict, L1TCLGenerator]:
    """
    Convenience wrapper for generating L1-TCL toy DGP data.
    
    This generates data following the L1-TCL paper (arXiv 2305.09126v3):
    - 2 covariates (X₁, X₂) with domain-specific distributions
    - Different propensity score parameters between domains
    - Constant treatment effect τ (not heterogeneous CATE)
    - Linear outcome: Y = τZ + αX₂ + ε
    
    Parameters
    ----------
    n_target : int
        Target domain sample size (default 100 = limited data)
    n_source : int
        Source domain sample size (default 1000 = abundant)
    tau_target : float
        True ATE in target domain (default -2/30 ≈ -0.067)
    same_tau : bool
        If True, source and target have same τ. If False, source τ=0.
    random_state : int
        Random seed
    **config_kwargs : additional config overrides
    
    Returns
    -------
    source_data : dict
    target_data : dict
    generator : L1TCLGenerator
    
    Example
    -------
    >>> source, target, gen = generate_l1tcl_data(n_target=100, n_source=1000)
    >>> print(f"True ATE: {gen.config.tau_target:.4f}")
    >>> print(f"Target n={len(target['Y'])}, Source n={len(source['Y'])}")
    """
    tau_source = tau_target if same_tau else 0.0
    
    config = L1TCLConfig(
        n_target=n_target,
        n_source=n_source,
        tau_target=tau_target,
        tau_source=tau_source,
        random_state=random_state,
        **config_kwargs
    )
    
    generator = L1TCLGenerator(config)
    source_data, target_data = generator.generate_full_dataset()
    
    return source_data, target_data, generator
