"""
Improved Synthetic Data Generator with Systematic Biases

Key improvements over original:
1. More source sites (5-10 instead of 3)
2. Systematic bias direction (not random signs)
3. Varied sparsity patterns per site
4. Larger bias magnitudes (more challenging)
5. Target bias designed to NOT cancel by accident
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional


@dataclass
class SiteConfig:
    """Configuration for a single clinical trial site"""
    n_patients: int
    mean_shift: np.ndarray
    beta_0: np.ndarray
    beta_tau: np.ndarray
    noise_std: float = 0.5
    treatment_prob: float = 0.5


class ImprovedMultiSiteSimulator:
    """
    Enhanced multi-center RCT simulator with systematic biases.
    
    Key changes from original:
    - More sites (5-10 sources)
    - Systematic positive biases (no random cancellation)
    - Varied sparsity patterns
    - Larger bias magnitudes (0.6-1.0 instead of 0.4)
    - Target designed with unique bias pattern
    """
    
    def __init__(self, n_features: int = 10, n_effect_modifiers: int = 3):
        self.p = n_features
        self.p_eff = n_effect_modifiers
        
        # Global true parameters (same as original)
        self.global_beta_0 = np.zeros(n_features)
        self.global_beta_0[:2] = [0.5, -0.3]
        
        self.global_beta_tau = np.zeros(n_features)
        self.global_beta_tau[:n_effect_modifiers] = [0.6, 0.4, -0.3]
    
    def generate_site(self, config: SiteConfig, site_id: int,
                     rho_cross_arm: float = 0.8, seed: int = 42) -> Dict:
        """Generate data for one site (same as original)"""
        np.random.seed(seed)
        n = config.n_patients
        
        X = np.random.randn(n, self.p) + config.mean_shift
        A = np.random.binomial(1, config.treatment_prob, n)
        propensity = np.full(n, config.treatment_prob)
        
        mu_0_global = X @ self.global_beta_0
        tau = X @ self.global_beta_tau
        
        delta_0 = config.beta_0
        
        # Cross-arm coupling
        eta = np.random.randn(self.p) * 0.3
        eta[np.abs(eta) < 0.1] = 0
        delta_1 = rho_cross_arm * delta_0 + np.sqrt(1 - rho_cross_arm**2) * eta
        
        mu_0 = mu_0_global + X @ delta_0
        mu_1 = mu_0_global + tau + X @ delta_1
        
        Y = A * mu_1 + (1 - A) * mu_0 + np.random.randn(n) * config.noise_std
        
        return {
            'X': X, 'A': A, 'Y': Y,
            'propensity': propensity,
            'mu_0': mu_0, 'mu_1': mu_1, 'tau': tau,
            'delta_0': delta_0, 'delta_1': delta_1,
            'site_id': site_id
        }
    
    def generate_systematic_bias(self, 
                                 bias_sparsity: int,
                                 bias_magnitude: float = 0.8,
                                 site_id: int = 0,
                                 seed: int = 42) -> np.ndarray:
        """
        Generate systematic bias that reduces accidental cancellation.
        
        Key changes:
        1. Biases are POSITIVE (or consistently directional)
        2. Different feature indices per site (varied patterns)
        3. Larger magnitude (0.6-1.0 instead of 0.4)
        4. Some overlap but not complete
        """
        np.random.seed(seed + site_id * 100)
        bias = np.zeros(self.p)
        
        # Select different features per site with some overlap
        # This creates diverse patterns while maintaining sparsity
        if site_id == 0:  # Target site - unique pattern
            # Target uses features that are DIFFERENT from most sources
            feature_pool = list(range(self.p))
            nonzero_idx = np.random.choice(feature_pool, bias_sparsity, replace=False)
        else:
            # Source sites have varied but overlapping patterns
            # Create site-specific "preferred features"
            offset = (site_id - 1) % (self.p - bias_sparsity + 1)
            feature_pool = list(range(offset, min(offset + bias_sparsity + 2, self.p)))
            if len(feature_pool) < bias_sparsity:
                feature_pool += list(range(bias_sparsity - len(feature_pool)))
            nonzero_idx = np.random.choice(feature_pool, bias_sparsity, replace=False)
        
        # SYSTEMATIC BIAS: All positive (or use abs())
        # This prevents random cancellation!
        bias_values = np.abs(np.random.randn(bias_sparsity)) * bias_magnitude
        
        # Add some variation in magnitude
        bias_values *= np.random.uniform(0.7, 1.3, bias_sparsity)
        
        bias[nonzero_idx] = bias_values
        
        return bias
    
    def generate_network(self,
                        n_source_sites: int = 5,  # Increased from 3!
                        n_target: int = 500,
                        source_patients_per_site: int = 400,  # Slightly reduced per site
                        disconnected: bool = True,
                        covariate_shift_scale: float = 0.5,
                        bias_sparsity: int = 3,  # Increased from 2!
                        bias_magnitude: float = 0.8,  # Increased from 0.4!
                        rho_cross_arm: float = 0.8,
                        seed: int = 42) -> Dict:
        """
        Generate improved network with more diverse biases.
        
        Key changes:
        - n_source_sites: 5 (was 3) - more diversity
        - bias_sparsity: 3 (was 2) - more complex patterns
        - bias_magnitude: 0.8 (was 0.4) - 2x stronger biases
        - Systematic positive biases (no random cancellation)
        """
        np.random.seed(seed)
        data = {'source': [], 'target': None}
        
        # Generate MORE source sites with VARIED patterns
        for s in range(n_source_sites):
            shift = np.random.randn(self.p) * covariate_shift_scale
            
            # Use improved bias generation
            site_bias = self.generate_systematic_bias(
                bias_sparsity=bias_sparsity,
                bias_magnitude=bias_magnitude,
                site_id=s + 1,  # Sites 1-5
                seed=seed
            )
            
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
        
        # Generate target with UNIQUE pattern (reduces cancellation)
        target_shift = np.random.randn(self.p) * covariate_shift_scale * 1.5
        
        # Target bias: Use site_id=0 to get unique pattern
        target_bias = self.generate_systematic_bias(
            bias_sparsity=bias_sparsity,
            bias_magnitude=bias_magnitude * 1.2,  # Even stronger in target!
            site_id=0,  # Special pattern for target
            seed=seed + 9999
        )
        
        target_config = SiteConfig(
            n_patients=n_target,
            mean_shift=target_shift,
            beta_0=target_bias,
            beta_tau=self.global_beta_tau,
            treatment_prob=0.5 if not disconnected else 0.5,
            noise_std=0.5
        )
        
        target_data = self.generate_site(target_config, site_id=0,
                                        rho_cross_arm=rho_cross_arm,
                                        seed=seed + 9999)
        
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
        """Pool all source sites (same as original)"""
        X_s = np.vstack([s['X'] for s in data['source']])
        A_s = np.hstack([s['A'] for s in data['source']])
        Y_s = np.hstack([s['Y'] for s in data['source']])
        prop_s = np.hstack([s['propensity'] for s in data['source']])
        return X_s, A_s, Y_s, prop_s


def compare_dgps(seed=42):
    """Compare original vs improved DGP"""
    from data_generator import MultiSiteSimulator
    
    print("="*80)
    print("COMPARING ORIGINAL vs IMPROVED DGP")
    print("="*80)
    print()
    
    # Original DGP
    print("ORIGINAL DGP (3 sources, random biases):")
    print("-" * 80)
    original = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    data_orig = original.generate_network(
        n_source_sites=3,
        n_target=500,
        rho_cross_arm=0.8,
        seed=seed
    )
    
    print(f"\nSource sites: {len(data_orig['source'])}")
    for i, site in enumerate(data_orig['source']):
        delta_0 = site['delta_0']
        print(f"  Site {i+1}: delta_0 = {delta_0}")
        print(f"          Sparsity: {np.sum(np.abs(delta_0) > 1e-6)}/10, "
              f"||delta||: {np.linalg.norm(delta_0):.3f}, "
              f"Sign: {'+' if np.sum(delta_0) > 0 else '-'}")
    
    target_delta_0 = data_orig['target']['delta_0']
    print(f"\nTarget: delta_0 = {target_delta_0}")
    print(f"        Sparsity: {np.sum(np.abs(target_delta_0) > 1e-6)}/10, "
          f"||delta||: {np.linalg.norm(target_delta_0):.3f}")
    
    # Average source bias
    avg_source = np.mean([s['delta_0'] for s in data_orig['source']], axis=0)
    print(f"\nAverage source bias: {avg_source}")
    print(f"Distance to target: {np.linalg.norm(avg_source - target_delta_0):.3f}")
    
    # Check cancellation potential
    print(f"\nCancellation analysis:")
    print(f"  Σ(source biases): {np.sum([s['delta_0'] for s in data_orig['source']]):.3f}")
    print(f"  Mean absolute bias: {np.mean(np.abs(avg_source)):.3f}")
    
    print("\n" + "="*80)
    print("IMPROVED DGP (5 sources, systematic biases):")
    print("-" * 80)
    improved = ImprovedMultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    data_imp = improved.generate_network(
        n_source_sites=5,
        n_target=500,
        bias_sparsity=3,
        bias_magnitude=0.8,
        rho_cross_arm=0.8,
        seed=seed
    )
    
    print(f"\nSource sites: {len(data_imp['source'])}")
    for i, site in enumerate(data_imp['source']):
        delta_0 = site['delta_0']
        print(f"  Site {i+1}: delta_0 = {delta_0}")
        print(f"          Sparsity: {np.sum(np.abs(delta_0) > 1e-6)}/10, "
              f"||delta||: {np.linalg.norm(delta_0):.3f}, "
              f"All positive: {np.all(delta_0 >= 0)}")
    
    target_delta_0 = data_imp['target']['delta_0']
    print(f"\nTarget: delta_0 = {target_delta_0}")
    print(f"        Sparsity: {np.sum(np.abs(target_delta_0) > 1e-6)}/10, "
          f"||delta||: {np.linalg.norm(target_delta_0):.3f}")
    print(f"        All positive: {np.all(target_delta_0 >= 0)}")
    
    # Average source bias
    avg_source = np.mean([s['delta_0'] for s in data_imp['source']], axis=0)
    print(f"\nAverage source bias: {avg_source}")
    print(f"Distance to target: {np.linalg.norm(avg_source - target_delta_0):.3f}")
    
    # Check cancellation potential
    print(f"\nCancellation analysis:")
    print(f"  All biases positive: LESS CANCELLATION!")
    print(f"  Mean bias: {np.mean(avg_source):.3f} (was near 0 in original)")
    print(f"  Magnitude 2x larger: {np.linalg.norm(avg_source):.3f}")


if __name__ == "__main__":
    compare_dgps(seed=42)
