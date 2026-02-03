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
    """
    
    def __init__(self, config: FairSyntheticRCTConfig = None):
        self.config = config or FairSyntheticRCTConfig()
        self.rng = np.random.default_rng(self.config.random_state)
        
        p = self.config.n_features
        C = self.config.n_source_sites
        
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
            # Sparse placebo deviation β_{0,c}
            # ─────────────────────────────────────────────────────────────
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
    
    def _mu(self, X: np.ndarray, site_id: int, arm: int) -> np.ndarray:
        """
        Compute μ_{a,c}(x) = α_{a,c} + x^T b_a + nonlin(x) + x^T β_{a,c}.
        
        NEW: Includes arm-specific intercept α_{a,c}.
        """
        p = self.config.n_features
        
        # Arm-specific intercept (CHANGE 3)
        alpha = self.arm_intercepts[site_id][arm]
        
        if arm == 0:
            base = X @ self.b0_proxy
            dev = X @ self.beta0[site_id]
            
            if self.config.proxy_nonlinear_scale > 0:
                c0, c1 = self.proxy_nonlin_coef0
                base = base + self.config.proxy_nonlinear_scale * (
                    c0 * np.sin(X[:, 0]) + c1 * 0.5 * X[:, 1]**2
                )
        else:
            base = X @ self.b1_proxy
            dev = X @ self.beta1[site_id]
            
            if self.config.proxy_nonlinear_scale > 0:
                c0, c1 = self.proxy_nonlin_coef1
                base = base + self.config.proxy_nonlinear_scale * (
                    c0 * np.sin(X[:, 0]) + c1 * 0.5 * X[:, 1]**2
                )
        
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
