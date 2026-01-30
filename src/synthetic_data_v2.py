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
    n_source_sites: int = 3
    n_target: int = 200
    n_source_per_site: int = 500
    treatment_prob: float = 0.5
    noise_std: float = 0.5
    
    # Covariate shift
    covariate_shift_scale: float = 1.0
    target_shift_multiplier: float = 1.5  # Target has more shift
    
    # A5: Site deviation structure (sparse linear)
    dev_sparsity: int = 2                 # Nonzeros in beta_{0,c}
    dev_scale: float = 0.4                # Magnitude of corrections
    
    # A6: Transfer operator + nontransfer
    transfer_rank: int = 1                # rank(M*)
    transfer_strength: float = 1.0        # Scales M*
    nontransfer_scale_source: float = 0.05  # Small for sources
    nontransfer_scale_target: float = 0.3   # Larger for target (degradation knob)
    
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
        
        # ═════════════════════════════════════════════════════════════════
        # Transfer operator M* (low-rank structure, A6)
        # ═════════════════════════════════════════════════════════════════
        # M* = U V^T with rank r
        U = self.rng.normal(0, 1.0, size=(p, r))
        V = self.rng.normal(0, 1.0, size=(p, r))
        self.M_star = self.config.transfer_strength * (U @ V.T) / max(1, r)
        
        # ═════════════════════════════════════════════════════════════════
        # Site-specific parameters
        # ═════════════════════════════════════════════════════════════════
        self.site_shifts = {}     # Covariate shift mu_c
        self.beta0 = {}           # Placebo deviations
        self.beta1 = {}           # Treated deviations
        self.nu = {}              # Nontransfer component
        
        # Generate for sources (c=1,2,3) and target (c=0)
        for c in range(0, self.config.n_source_sites + 1):
            # ─────────────────────────────────────────────────────────────
            # Covariate shift
            # ─────────────────────────────────────────────────────────────
            shift_scale = (self.config.covariate_shift_scale * 
                          self.config.target_shift_multiplier if c == 0 
                          else self.config.covariate_shift_scale)
            self.site_shifts[c] = self.rng.normal(0, shift_scale, size=p)
            
            # ─────────────────────────────────────────────────────────────
            # Sparse placebo deviation beta_{0,c}
            # ─────────────────────────────────────────────────────────────
            beta0_c = np.zeros(p)
            s = min(self.config.dev_sparsity, p)
            support = self.rng.choice(p, size=s, replace=False)
            beta0_c[support] = self.rng.normal(0, self.config.dev_scale, size=s)
            
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
        
        Returns residual that's not captured by the linear model.
        """
        if self.config.misspec_scale <= 0:
            return np.zeros(X.shape[0])
        
        if not self.config.misspec_nonlinear:
            # Mild linear-ish structured residual
            w = self.rng.normal(0, 1.0, size=X.shape[1])
            return self.config.misspec_scale * (X @ w) / np.sqrt(X.shape[1])
        else:
            # Nonlinear: sin interaction on first two features
            return self.config.misspec_scale * np.sin(X[:, 0] * X[:, 1])
    
    def _mu(self, X: np.ndarray, site_id: int, arm: int) -> np.ndarray:
        """
        Compute mu_{a,c}(x) = x^T b_a + x^T beta_{a,c} + r_{a,c}(x).
        
        Parameters
        ----------
        X : array-like, shape (n, p)
        site_id : int (0=target, 1,2,3=sources)
        arm : int (0=placebo, 1=treated)
        
        Returns
        -------
        mu : array, shape (n,)
        """
        if arm == 0:
            base = X @ self.b0_proxy         # Proxy (shared)
            dev = X @ self.beta0[site_id]    # Site deviation (sparse)
        else:
            base = X @ self.b1_proxy
            dev = X @ self.beta1[site_id]
        
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
        # Covariates X | site (with shift)
        # ═════════════════════════════════════════════════════════════════
        shift = self.site_shifts[site_id]
        X = self.rng.normal(0, 1.0, size=(n_samples, p)) + shift
        
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
        # Observed outcome Y
        # ═════════════════════════════════════════════════════════════════
        eps = self.rng.normal(0, self.config.noise_std, size=n_samples)
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
        """
        diag = {
            'n_features': self.config.n_features,
            'n_source_sites': self.config.n_source_sites,
            'b0_proxy': self.b0_proxy,
            'b1_proxy': self.b1_proxy,
            'M_star': self.M_star,
            'M_star_norm': float(np.linalg.norm(self.M_star, 'fro')),
            'M_star_rank': int(np.linalg.matrix_rank(self.M_star)),
        }
        
        # Per-site deviations
        for c in range(0, self.config.n_source_sites + 1):
            site_name = 'target' if c == 0 else f'source_{c}'
            diag[f'{site_name}_beta0'] = self.beta0[c]
            diag[f'{site_name}_beta1'] = self.beta1[c]
            diag[f'{site_name}_nu'] = self.nu[c]
            diag[f'{site_name}_sparsity'] = int(np.sum(np.abs(self.beta0[c]) > 1e-6))
            diag[f'{site_name}_nu_norm'] = float(np.linalg.norm(self.nu[c]))
        
        # Verify A6: beta1 ≈ M* beta0 + nu
        for c in range(1, self.config.n_source_sites + 1):
            predicted = self.M_star @ self.beta0[c]
            actual = self.beta1[c] - self.nu[c]
            diag[f'source_{c}_A6_error'] = float(np.linalg.norm(predicted - actual))
        
        return diag


# ═════════════════════════════════════════════════════════════════════════
# Convenience functions
# ═════════════════════════════════════════════════════════════════════════

def generate_synthetic_rct(
    n_source_sites: int = 3,
    n_target: int = 200,
    n_source_per_site: int = 500,
    random_state: int = 42,
    **config_kwargs
) -> Tuple[Dict, Dict, SyntheticRCTGenerator]:
    """
    Convenience wrapper for generating synthetic RCT data.
    
    Parameters
    ----------
    n_source_sites : int
    n_target : int
    n_source_per_site : int
    random_state : int
    **config_kwargs : additional config overrides
    
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
    n_source_sites: int = 3,
    n_target: int = 200,
    n_source_per_site: int = 500,
    nontransfer_scale_target: float = 0.3,
    random_state: int = 42,
    **config_kwargs
) -> Tuple[Dict, Dict, SyntheticRCTGenerator]:
    """
    Generate data with disconnected target (placebo-only).
    
    Useful for testing Option B / Step B.
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
    n_source_sites: int = 3,
    n_target: int = 200,
    random_state: int = 42
) -> list:
    """
    Generate multiple datasets with varying cross-arm validity.
    
    Returns list of (source, target, generator) tuples.
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
