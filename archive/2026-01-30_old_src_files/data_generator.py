"""
Synthetic Data Generator for Multi-Site RCT Experiments

Generates controlled synthetic data with:
- Multiple source sites with covariate shift
- Single target site with sparse transport bias
- Known ground truth for evaluation
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional


@dataclass
class SiteConfig:
    """Configuration for a single clinical trial site"""
    n_patients: int
    mean_shift: np.ndarray  # Covariate distribution shift
    beta_0: np.ndarray      # True baseline coefficients (sparse transport bias)
    beta_tau: np.ndarray    # True CATE coefficients
    noise_std: float = 0.5
    treatment_prob: float = 0.5


class MultiSiteSimulator:
    """
    Generates synthetic multi-center RCT data with controlled properties.
    
    Ground Truth Models:
    --------------------
    μ_0(x) = β_0' x  (global baseline)
    τ(x) = β_τ' x[:p_eff]  (treatment effect, only on effect modifiers)
    μ_{0,c}(x) = μ_0(x) + δ_{0,c}' x  (site-specific baseline)
    μ_{1,c}(x) = μ_0(x) + τ(x) + δ_{1,c}' x  (site-specific treated)
    
    where:
    - δ_{a,c} has sparsity ||δ||_0 = s_bias
    - δ_{1,c} = ρ * δ_{0,c} + √(1-ρ²) * η_c  (cross-arm coupling)
    """
    
    def __init__(self, n_features: int = 10, n_effect_modifiers: int = 3):
        self.p = n_features
        self.p_eff = n_effect_modifiers
        
        # Global true parameters (sparse)
        self.global_beta_0 = np.zeros(n_features)
        self.global_beta_0[:2] = [0.5, -0.3]  # First 2 drive baseline
        
        self.global_beta_tau = np.zeros(n_features)
        self.global_beta_tau[:n_effect_modifiers] = [0.6, 0.4, -0.3]
    
    def generate_site(self, config: SiteConfig, site_id: int, 
                     rho_cross_arm: float = 0.8, seed: int = 42) -> Dict:
        """Generate data for one site with explicit cross-arm coupling"""
        np.random.seed(seed)
        n = config.n_patients
        
        # Covariates with site-specific shift (induces covariate shift)
        X = np.random.randn(n, self.p) + config.mean_shift
        
        # Treatment randomization
        A = np.random.binomial(1, config.treatment_prob, n)
        propensity = np.full(n, config.treatment_prob)
        
        # Outcome generation with site-specific baseline shift
        mu_0_global = X @ self.global_beta_0
        tau = X @ self.global_beta_tau
        
        # Site-specific biases with cross-arm coupling
        delta_0 = config.beta_0  # Placebo bias
        
        # Cross-arm coupling: δ_1 = ρ * δ_0 + √(1-ρ²) * η
        eta = np.random.randn(self.p) * 0.3
        eta[np.abs(eta) < 0.1] = 0  # Enforce sparsity
        delta_1 = rho_cross_arm * delta_0 + np.sqrt(1 - rho_cross_arm**2) * eta
        
        # Potential outcomes
        mu_0 = mu_0_global + X @ delta_0
        mu_1 = mu_0_global + tau + X @ delta_1
        
        # Observed outcome
        Y = A * mu_1 + (1 - A) * mu_0 + np.random.randn(n) * config.noise_std
        
        return {
            'X': X,
            'A': A,
            'Y': Y,
            'propensity': propensity,
            'mu_0': mu_0,
            'mu_1': mu_1,
            'tau': tau,
            'delta_0': delta_0,
            'delta_1': delta_1,
            'site_id': site_id
        }
    
    def generate_network(self,
                        n_source_sites: int = 3,
                        n_target: int = 200,
                        source_patients_per_site: int = 500,
                        disconnected: bool = True,
                        covariate_shift_scale: float = 0.5,
                        bias_sparsity: int = 2,
                        rho_cross_arm: float = 0.8,
                        seed: int = 42) -> Dict:
        """
        Generate full network: multiple sources + one target
        
        Parameters:
        -----------
        disconnected : bool
            If True, target has only placebo arm (A=0 for all)
        bias_sparsity : int
            Number of covariates that differ between sites (Assumption A5)
        rho_cross_arm : float
            Cross-arm coupling strength (Assumption A6)
        """
        np.random.seed(seed)
        data = {'source': [], 'target': None}
        
        # Generate source sites with random shifts
        for s in range(n_source_sites):
            shift = np.random.randn(self.p) * covariate_shift_scale
            
            # Site-specific bias is sparse (SYSTEMATIC POSITIVE BIASES!)
            site_bias = np.zeros(self.p)
            nonzero_idx = np.random.choice(self.p, bias_sparsity, replace=False)
            site_bias[nonzero_idx] = np.abs(np.random.randn(bias_sparsity)) * 0.8  # 2x stronger + all positive!
            
            config = SiteConfig(
                n_patients=source_patients_per_site,
                mean_shift=shift,
                beta_0=site_bias,
                beta_tau=self.global_beta_tau,
                treatment_prob=0.5
            )
            site_data = self.generate_site(config, site_id=s+1, 
                                          rho_cross_arm=rho_cross_arm,
                                          seed=seed + 1000 + s)
            data['source'].append(site_data)
        
        # Generate target with different shift
        target_shift = np.random.randn(self.p) * covariate_shift_scale * 1.5
        
        # Target bias (what we want to estimate via anchoring) - SYSTEMATIC!
        target_bias = np.zeros(self.p)
        nonzero_idx = np.random.choice(self.p, bias_sparsity, replace=False)
        target_bias[nonzero_idx] = np.abs(np.random.randn(bias_sparsity)) * 0.8  # 2x stronger + all positive!
        
        target_config = SiteConfig(
            n_patients=n_target,
            mean_shift=target_shift,
            beta_0=target_bias,
            beta_tau=self.global_beta_tau,
            treatment_prob=0.5 if not disconnected else 0.5,  # Generate then filter
            noise_std=0.5
        )
        
        target_data = self.generate_site(target_config, site_id=0,
                                        rho_cross_arm=rho_cross_arm,
                                        seed=seed + 9999)
        
        # Force disconnected if requested
        if disconnected:
            placebo_idx = np.where(target_data['A'] == 0)[0]
            for key in ['X', 'A', 'Y', 'propensity', 'mu_0', 'mu_1', 'tau']:
                if key in target_data and isinstance(target_data[key], np.ndarray):
                    target_data[key] = target_data[key][placebo_idx]
            target_data['config'] = target_config
            target_data['config'].n_patients = len(placebo_idx)
        
        data['target'] = target_data
        data['true_params'] = {
            'beta_0': self.global_beta_0,
            'beta_tau': self.global_beta_tau,
            'rho': rho_cross_arm
        }
        
        return data
    
    @staticmethod
    def pool_sources(data: Dict) -> Tuple:
        """Pool all source sites into single arrays for fitting"""
        X_s = np.vstack([s['X'] for s in data['source']])
        A_s = np.hstack([s['A'] for s in data['source']])
        Y_s = np.hstack([s['Y'] for s in data['source']])
        prop_s = np.hstack([s['propensity'] for s in data['source']])
        return X_s, A_s, Y_s, prop_s


def generate_simple_experiment(n_runs: int = 20, seed: int = 42) -> list:
    """Generate multiple datasets for Monte Carlo experiments"""
    simulator = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    datasets = []
    
    for run in range(n_runs):
        data = simulator.generate_network(
            n_source_sites=3,
            n_target=200,
            source_patients_per_site=500,
            disconnected=True,
            covariate_shift_scale=0.5,
            bias_sparsity=2,
            seed=seed + run
        )
        datasets.append(data)
    
    return datasets
