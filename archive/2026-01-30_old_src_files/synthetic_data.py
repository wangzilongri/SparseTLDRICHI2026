"""
Synthetic data generation for multi-center RCT simulation.

Based on paper specifications:
- p=5 covariates (3 relevant effect modifiers, 2 nuisance)
- Site-specific covariate shifts
- Known propensity P(A=1) = 0.5
- Linear outcomes with structured heterogeneity
- Y = μ₀(X) + A·τ(X) + ε, ε ~ N(0, 0.5²)
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class SyntheticRCTConfig:
    """Configuration for synthetic RCT data generation."""
    n_features: int = 5
    n_effect_modifiers: int = 3
    n_source_sites: int = 3
    n_target: int = 200
    n_source_per_site: int = 500
    treatment_prob: float = 0.5
    noise_std: float = 0.5
    covariate_shift_scale: float = 1.0
    random_state: int = 42


class SyntheticRCTGenerator:
    """
    Generate synthetic multi-center RCT data with covariate shift.
    
    Ground truth model:
    - μ₀(x) = β₀ᵀx (baseline response, uses all features)
    - τ(x) = β_τᵀx[:n_eff] (treatment effect, uses only effect modifiers)
    - Y = μ₀(X) + A·τ(X) + ε
    
    Site-specific shifts:
    - Each site c has X ~ N(μ_c, I)
    - μ_c ~ N(0, σ_shift²) for sources
    - Target has different shift
    """
    
    def __init__(self, config: SyntheticRCTConfig = None):
        if config is None:
            config = SyntheticRCTConfig()
        self.config = config
        
        # Set random seed
        np.random.seed(config.random_state)
        
        # Generate true parameters
        self.beta_0 = np.random.randn(config.n_features) * 0.5  # Baseline
        self.beta_tau = np.zeros(config.n_features)
        self.beta_tau[:config.n_effect_modifiers] = np.random.randn(config.n_effect_modifiers) * 0.5
        
        # Generate site shifts
        self.site_shifts = {}
        for c in range(1, config.n_source_sites + 1):
            self.site_shifts[c] = np.random.randn(config.n_features) * config.covariate_shift_scale
        # Target has different shift
        self.site_shifts[0] = np.random.randn(config.n_features) * config.covariate_shift_scale * 1.5
    
    def generate_site_data(self, site_id: int, n_samples: int) -> Dict:
        """
        Generate data for a single site.
        
        Parameters
        ----------
        site_id : int
            Site identifier (0 for target, >0 for sources)
        n_samples : int
            Number of samples to generate
        
        Returns
        -------
        data : dict
            Dictionary with keys: X, A, Y, tau_true, mu0_true, mu1_true, c
        """
        # Covariates with site shift
        shift = self.site_shifts[site_id]
        X = np.random.randn(n_samples, self.config.n_features) + shift
        
        # Randomized treatment
        A = np.random.binomial(1, self.config.treatment_prob, n_samples)
        
        # True outcomes
        mu0 = X @ self.beta_0
        tau = X[:, :self.config.n_effect_modifiers] @ self.beta_tau[:self.config.n_effect_modifiers]
        mu1 = mu0 + tau
        
        # Observed outcomes
        noise = np.random.randn(n_samples) * self.config.noise_std
        Y = mu0 + A * tau + noise
        
        # Site indicator
        c = np.full(n_samples, site_id)
        
        return {
            'X': X,
            'A': A,
            'Y': Y,
            'tau_true': tau,
            'mu0_true': mu0,
            'mu1_true': mu1,
            'c': c
        }
    
    def generate_full_dataset(self) -> Tuple[Dict, Dict]:
        """
        Generate complete multi-site dataset.
        
        Returns
        -------
        source_data : dict
            Pooled source data with keys: X, A, Y, tau_true, mu0_true, mu1_true, c
        target_data : dict
            Target data with same keys
        """
        # Generate source sites
        source_datasets = []
        for c in range(1, self.config.n_source_sites + 1):
            site_data = self.generate_site_data(c, self.config.n_source_per_site)
            source_datasets.append(site_data)
        
        # Pool source data
        source_data = {
            'X': np.vstack([d['X'] for d in source_datasets]),
            'A': np.concatenate([d['A'] for d in source_datasets]),
            'Y': np.concatenate([d['Y'] for d in source_datasets]),
            'tau_true': np.concatenate([d['tau_true'] for d in source_datasets]),
            'mu0_true': np.concatenate([d['mu0_true'] for d in source_datasets]),
            'mu1_true': np.concatenate([d['mu1_true'] for d in source_datasets]),
            'c': np.concatenate([d['c'] for d in source_datasets])
        }
        
        # Generate target site
        target_data = self.generate_site_data(0, self.config.n_target)
        
        return source_data, target_data
    
    def true_cate(self, X: np.ndarray) -> np.ndarray:
        """Compute true CATE for given covariates."""
        return X[:, :self.config.n_effect_modifiers] @ self.beta_tau[:self.config.n_effect_modifiers]
    
    def true_ate(self, X: np.ndarray) -> float:
        """Compute true ATE for given covariate distribution."""
        return np.mean(self.true_cate(X))


def generate_synthetic_rct(n_source_sites=3, n_target=200, n_source_per_site=500,
                           n_features=5, n_effect_modifiers=3,
                           covariate_shift_scale=1.0, random_state=42):
    """
    Convenience function to generate synthetic RCT data.
    
    Returns
    -------
    source_data : dict
    target_data : dict
    generator : SyntheticRCTGenerator (for computing true quantities)
    """
    config = SyntheticRCTConfig(
        n_features=n_features,
        n_effect_modifiers=n_effect_modifiers,
        n_source_sites=n_source_sites,
        n_target=n_target,
        n_source_per_site=n_source_per_site,
        covariate_shift_scale=covariate_shift_scale,
        random_state=random_state
    )
    
    generator = SyntheticRCTGenerator(config)
    source_data, target_data = generator.generate_full_dataset()
    
    return source_data, target_data, generator


if __name__ == '__main__':
    # Test data generation
    source, target, gen = generate_synthetic_rct()
    
    print("Source data:")
    print(f"  Shape: X={source['X'].shape}, A={source['A'].shape}, Y={source['Y'].shape}")
    print(f"  Sites: {np.unique(source['c'])}")
    print(f"  Treatment distribution: {np.mean(source['A']):.3f}")
    
    print("\nTarget data:")
    print(f"  Shape: X={target['X'].shape}, A={target['A'].shape}, Y={target['Y'].shape}")
    print(f"  Treatment distribution: {np.mean(target['A']):.3f}")
    
    print("\nTrue parameters:")
    print(f"  β₀: {gen.beta_0}")
    print(f"  β_τ: {gen.beta_tau}")
    print(f"  True ATE (target): {gen.true_ate(target['X']):.3f}")
