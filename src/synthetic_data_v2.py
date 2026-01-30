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
    """Configuration for synthetic RCT generation."""
    
    # Basic dimensions
    n_features: int = 5
    n_effect_modifiers: int = 3  # For reference (tau defined via mu1-mu0)
    n_source_sites: int = 10     # INCREASED for Step B identifiability
    n_target: int = 200
    n_source_per_site: int = 500
    treatment_prob: float = 0.5
    noise_std: float = 0.5
    
    # Covariate shift
    covariate_shift_scale: float = 1.0
    target_shift_multiplier: float = 1.5  # Target has more shift
    cov_shift_strength: float = 0.0       # Optional covariance shift
    
    # Proxy nonlinearity (makes Stage 1 nontrivial)
    proxy_nonlinear_scale: float = 0.5    # Mild nonlinearity in proxy
    
    # A5: Site deviation structure (sparse linear)
    dev_sparsity: int = 2                 # Nonzeros in beta_{0,c}
    dev_scale: float = 0.4                # Magnitude of corrections
    
    # Support structure (critical for Step B!)
    shared_support_size: int = 2          # Shared across sites
    idiosyncratic_support_size: int = 0   # Site-specific extras
    restrict_deviation_to_first_k: Optional[int] = None  # e.g., 3 for effect modifiers
    
    # A6: Transfer operator + nontransfer
    transfer_rank: int = 1                # rank(M*)
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
    
    Outcomes:
        Y = mu_{0,c}(X) + A * tau_c(X) + eps
        where tau_c(X) = mu_{1,c}(X) - mu_{0,c}(X)
    """
    
    def __init__(self, config: SyntheticRCTConfig = None):
        self.config = config or SyntheticRCTConfig()
        self.rng = np.random.default_rng(self.config.random_state)
        
        p = self.config.n_features
        r = min(self.config.transfer_rank, p)
        
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
        
        # ═════════════════════════════════════════════════════════════════
        # Shared support structure (critical for Step B!)
        # ═════════════════════════════════════════════════════════════════
        available_support = (list(range(self.config.restrict_deviation_to_first_k))
                            if self.config.restrict_deviation_to_first_k is not None
                            else list(range(p)))
        
        # Global shared support
        self.shared_support = self.rng.choice(
            available_support,
            size=min(self.config.shared_support_size, len(available_support)),
            replace=False
        )
        
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
            # Sparse placebo deviation beta_{0,c} with shared support
            # ─────────────────────────────────────────────────────────────
            beta0_c = np.zeros(p)
            
            # Shared support (always included)
            beta0_c[self.shared_support] = self.rng.normal(
                0, self.config.dev_scale, size=len(self.shared_support)
            )
            
            # Idiosyncratic support (site-specific)
            if self.config.idiosyncratic_support_size > 0:
                # Choose from available_support \ shared_support
                remaining = list(set(available_support) - set(self.shared_support))
                if len(remaining) > 0:
                    idio_size = min(self.config.idiosyncratic_support_size, len(remaining))
                    idio_support = self.rng.choice(remaining, size=idio_size, replace=False)
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
            # Standard RCT
            A = self.rng.binomial(1, self.config.treatment_prob, size=n_samples)
        
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
        
        Useful for validating that Step B can recover M*.
        Includes transfer quality metrics (SNR, cosine similarity).
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
        }
        
        # Per-site deviations and transfer quality
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
    
    NEW: Default increased to 10 sites for Step B identifiability.
    
    Parameters
    ----------
    n_source_sites : int (default 10, increased from 3)
    n_target : int
    n_source_per_site : int
    random_state : int
    **config_kwargs : additional config overrides
        - proxy_nonlinear_scale: float (default 0.5, makes Stage 1 nontrivial)
        - shared_support_size: int (controls Step B difficulty)
        - transfer_structure: str ("low_rank", "rhoI", "diag", "diag_plus_low_rank")
        - nontransfer_scale_target: float (degradation knob)
    
    Returns
    -------
    source_data : dict
    target_data : dict
    generator : SyntheticRCTGenerator (for diagnostics)
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
