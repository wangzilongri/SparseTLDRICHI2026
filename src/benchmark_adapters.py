"""
Benchmark Adapters: Bridge existing code to new benchmark infrastructure.

This module provides adapter functions that connect:
- synthetic_data_v2.py -> data_generator for benchmark_runner
- metrics.py -> metric_computer for benchmark_runner  
- estimator_fixed.py + ablations.py -> method_factories
"""

import os
import sys
import warnings
import numpy as np
from typing import Dict, Callable, Any, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmark_schema import Scenario, MethodSpec, get_method_spec, METHOD_REGISTRY


# =============================================================================
# Data Generator Adapter
# =============================================================================

def create_data_generator() -> Callable:
    """
    Create a data generator function compatible with benchmark_runner.
    
    Returns
    -------
    data_generator : callable
        Function(scenario, seed) -> data dict
    """
    from synthetic_data_v2 import SyntheticRCTConfig, SyntheticRCTGenerator
    
    # Import fair DGP (optional, may not exist)
    try:
        from synthetic_data_v2_fair import FairSyntheticRCTConfig, FairSyntheticRCTGenerator
        FAIR_DGP_AVAILABLE = True
    except ImportError:
        FAIR_DGP_AVAILABLE = False
    
    # Import L1-TCL DGP (toy and extended versions)
    from synthetic_data_v2 import (
        L1TCLConfig, L1TCLGenerator,
        L1TCLExtendedConfig, L1TCLExtendedGenerator
    )
    
    def data_generator(scenario: Scenario, seed: int) -> Dict[str, Any]:
        """
        Generate synthetic data based on scenario configuration.
        
        Parameters
        ----------
        scenario : Scenario
            Benchmark scenario with parameters
        seed : int
            Random seed
            
        Returns
        -------
        data : dict
            Dictionary with all data needed for estimation and evaluation
        """
        # ═══════════════════════════════════════════════════════════════════════
        # Check for L1-TCL DGP (special case: different structure)
        # ═══════════════════════════════════════════════════════════════════════
        use_l1tcl = getattr(scenario, 'use_l1tcl_dgp', None) or (
            scenario.benchmark_id is not None and 'l1tcl' in scenario.benchmark_id.lower()
        )
        
        if use_l1tcl:
            return _generate_l1tcl_data(scenario, seed)
        
        # ═══════════════════════════════════════════════════════════════════════
        # Standard DGP (multi-site, heterogeneous CATE)
        # ═══════════════════════════════════════════════════════════════════════
        
        # Map scenario params to SyntheticRCTConfig
        config_kwargs = {
            'random_state': seed,
        }
        
        # Target sizes - compute total and treatment fraction
        m0 = scenario.m0 if scenario.m0 is not None else 100
        m1 = scenario.m1 if scenario.m1 is not None else 0
        n_target_total = m0 + m1
        
        if n_target_total > 0:
            config_kwargs['n_target'] = n_target_total
            # Set treatment probability to achieve desired m0/m1 split
            if m1 == 0:
                # Disconnected target: placebo-only
                config_kwargs['target_treated_frac'] = 0.0
            else:
                # Mixed target: set treatment_prob_target to get ~m1/(m0+m1) treated
                config_kwargs['treatment_prob_target'] = m1 / n_target_total
        elif scenario.m0 is not None:
            config_kwargs['n_target'] = scenario.m0
        
        # Source/proxy settings
        if scenario.n_proxy_total is not None and scenario.C_sources is not None:
            config_kwargs['n_source_sites'] = scenario.C_sources
            config_kwargs['n_source_per_site'] = scenario.n_proxy_total // scenario.C_sources
        elif scenario.n_proxy_total is not None:
            # Default 10 sources
            config_kwargs['n_source_sites'] = 10
            config_kwargs['n_source_per_site'] = scenario.n_proxy_total // 10
        elif scenario.C_sources is not None:
            config_kwargs['n_source_sites'] = scenario.C_sources
        
        # Covariate shift
        if scenario.shift_strength is not None:
            config_kwargs['covariate_shift_scale'] = scenario.shift_strength
        
        # Nontransfer
        if scenario.nontransfer_scale is not None:
            config_kwargs['nontransfer_scale_target'] = scenario.nontransfer_scale
        
        # Transfer rank (A6)
        if scenario.a6_rank_true is not None:
            config_kwargs['transfer_rank'] = scenario.a6_rank_true
        
        # Sparsity (A5)
        if scenario.a5_effective_sparsity is not None:
            # Convert fraction to number of nonzeros
            p = config_kwargs.get('n_features', 5)
            config_kwargs['dev_sparsity'] = max(1, int(scenario.a5_effective_sparsity * p))
        
        # Feature dimension
        if scenario.p_dim is not None:
            config_kwargs['n_features'] = scenario.p_dim
        
        # Fair DGP knobs (for OptionB evaluation)
        if scenario.overlap_lambda is not None:
            config_kwargs['overlap_lambda'] = scenario.overlap_lambda
        if scenario.intercept_drift_scale is not None:
            config_kwargs['intercept_drift_scale'] = scenario.intercept_drift_scale
        if scenario.nu_support_overlap is not None:
            config_kwargs['nu_support_overlap'] = scenario.nu_support_overlap
        if scenario.nu_coefficient_corr is not None:
            config_kwargs['nu_coefficient_corr'] = scenario.nu_coefficient_corr
        
        # Choose DGP: fair or standard
        use_fair = scenario.use_fair_dgp or any([
            scenario.overlap_lambda is not None,
            scenario.intercept_drift_scale is not None,
            scenario.nu_support_overlap is not None,
            scenario.nu_coefficient_corr is not None,
        ])
        
        if use_fair and FAIR_DGP_AVAILABLE:
            config = FairSyntheticRCTConfig(**config_kwargs)
            generator = FairSyntheticRCTGenerator(config)
        else:
            config = SyntheticRCTConfig(**config_kwargs)
            generator = SyntheticRCTGenerator(config)
        source_data, target_data = generator.generate_full_dataset()
        
        # Generate larger evaluation set for target (held out)
        # Keep estimation data small (m0), but have plenty for evaluation
        np.random.seed(seed + 10000)  # Different seed for eval
        eval_target = generator.generate_site_data(0, 1000)
        
        # Compute actual m0/m1 from generated data
        actual_m0 = int(np.sum(target_data['A'] == 0))
        actual_m1 = int(np.sum(target_data['A'] == 1))
        has_target_treated = actual_m1 > 0
        
        # Compute propensity based on actual treatment assignment
        if actual_m1 > 0:
            propensity = actual_m1 / (actual_m0 + actual_m1)
        else:
            propensity = 0.5  # Default for placebo-only (doesn't affect estimation)
        
        # Package for benchmark runner
        data = {
            # Source data
            'X_source': source_data['X'],
            'A_source': source_data['A'],
            'Y_source': source_data['Y'],
            'c_source': source_data['c'],
            
            # Target estimation data
            'X_target': target_data['X'],
            'A_target': target_data['A'],
            'Y_target': target_data['Y'],
            
            # Target evaluation data (separate, larger)
            'X_target_eval': eval_target['X'],
            'tau_true': eval_target['tau_true'],
            'mu0_true': eval_target['mu0_true'],
            'mu1_true': eval_target['mu1_true'],
            'ate_true': float(np.mean(eval_target['tau_true'])),
            
            # Propensity (based on actual treatment fraction)
            'propensity_target': np.full(len(target_data['X']), propensity),
            
            # Feasibility flags
            'has_target_treated': has_target_treated,
            'actual_m0': actual_m0,
            'actual_m1': actual_m1,
            
            # Generator for diagnostics
            'generator': generator,
        }
        
        return data
    
    def _generate_l1tcl_data(scenario: Scenario, seed: int) -> Dict[str, Any]:
        """
        Generate data using L1-TCL DGP (arXiv 2305.09126v3).
        
        Supports two modes:
        1. Toy DGP (2 covariates, single source) - when p_dim=2 or C_sources=1
        2. Extended DGP (variable d, s, multi-site) - otherwise
        
        Parameters
        ----------
        scenario : Scenario
        seed : int
        
        Returns
        -------
        data : dict
        """
        # Determine if we should use extended or toy DGP
        p_dim = scenario.p_dim if scenario.p_dim is not None else 20
        n_sources = scenario.C_sources if scenario.C_sources is not None else 10
        
        # Use toy DGP only if explicitly 2 features AND 1 source
        use_toy = (p_dim == 2 and n_sources == 1)
        
        # Target sample size
        m0 = scenario.m0 if scenario.m0 is not None else 100
        m1 = scenario.m1 if scenario.m1 is not None else 0
        n_target = m0 + m1
        
        if use_toy:
            # ═══════════════════════════════════════════════════════════════════
            # TOY DGP (original 2-covariate version)
            # ═══════════════════════════════════════════════════════════════════
            l1tcl_kwargs = {'random_state': seed, 'n_target': n_target}
            if scenario.n_proxy_total is not None:
                l1tcl_kwargs['n_source'] = scenario.n_proxy_total
            
            config = L1TCLConfig(**l1tcl_kwargs)
            generator = L1TCLGenerator(config)
            source_data, target_data = generator.generate_full_dataset()
            
            # Eval data
            eval_generator = L1TCLGenerator(L1TCLConfig(
                n_target=1000,
                random_state=seed + 10000,
                **{k: getattr(config, k) for k in [
                    'mu1_target', 'mu2_target', 'beta1_target', 'beta2_target',
                    'tau_target', 'alpha_target', 'noise_std'
                ]}
            ))
            _, eval_target = eval_generator.generate_full_dataset()
            dgp_type = 'l1tcl_toy'
        else:
            # ═══════════════════════════════════════════════════════════════════
            # EXTENDED DGP (variable d, s, multi-site)
            # ═══════════════════════════════════════════════════════════════════
            ext_kwargs = {
                'random_state': seed,
                'n_features': p_dim,
                'n_target': n_target,
                'n_source_sites': n_sources,
            }
            
            # PS sparsity (from scenario if available)
            ps_sparsity = getattr(scenario, 'a5_effective_sparsity', None)
            if ps_sparsity is not None:
                # Convert fraction to integer sparsity
                ext_kwargs['ps_sparsity'] = max(1, int(ps_sparsity * p_dim))
            else:
                # Default: ~15% sparsity
                ext_kwargs['ps_sparsity'] = max(1, p_dim // 7)
            
            # Source samples per site
            if scenario.n_proxy_total is not None:
                ext_kwargs['n_source_per_site'] = scenario.n_proxy_total // n_sources
            
            config = L1TCLExtendedConfig(**ext_kwargs)
            generator = L1TCLExtendedGenerator(config)
            source_data, target_data = generator.generate_full_dataset()
            
            # Eval data - generate fresh target-domain data
            eval_config = L1TCLExtendedConfig(
                n_features=config.n_features,
                ps_sparsity=config.ps_sparsity,
                n_target=1000,
                n_source_sites=1,  # Don't need sources for eval
                random_state=seed + 10000,
                tau_target=config.tau_target,
                alpha_scale=config.alpha_scale,
                noise_std=config.noise_std,
            )
            eval_gen = L1TCLExtendedGenerator(eval_config)
            # Copy target-specific parameters
            eval_gen.beta_target = generator.beta_target
            eval_gen.alpha = generator.alpha
            eval_gen.site_shifts[0] = generator.site_shifts[0]
            _, eval_target = eval_gen.generate_full_dataset()
            dgp_type = 'l1tcl_extended'
        
        # Compute actual m0/m1
        actual_m0 = int(np.sum(target_data['A'] == 0))
        actual_m1 = int(np.sum(target_data['A'] == 1))
        has_target_treated = actual_m1 > 0
        
        # Propensity
        propensity = actual_m1 / (actual_m0 + actual_m1) if actual_m1 > 0 else 0.5
        
        # Package for benchmark runner
        data = {
            # Source data
            'X_source': source_data['X'],
            'A_source': source_data['A'],
            'Y_source': source_data['Y'],
            'c_source': source_data['c'],
            
            # Target estimation data
            'X_target': target_data['X'],
            'A_target': target_data['A'],
            'Y_target': target_data['Y'],
            
            # Target evaluation data
            'X_target_eval': eval_target['X'],
            'tau_true': eval_target['tau_true'],  # Constant!
            'mu0_true': eval_target['mu0_true'],
            'mu1_true': eval_target['mu1_true'],
            'ate_true': float(np.mean(eval_target['tau_true'])),
            
            # Propensity
            'propensity_target': np.full(len(target_data['X']), propensity),
            
            # Feasibility flags
            'has_target_treated': has_target_treated,
            'actual_m0': actual_m0,
            'actual_m1': actual_m1,
            
            # Generator for diagnostics
            'generator': generator,
            
            # L1-TCL specific flag
            'dgp_type': dgp_type,
        }
        
        return data
    
    return data_generator


# =============================================================================
# Metric Computer Adapter
# =============================================================================

def create_metric_computer() -> Callable:
    """
    Create a metric computer function compatible with benchmark_runner.
    
    Computes comprehensive metrics for CATE estimation:
    1. Point estimation: PEHE, ATE Error, Bias
    2. Ranking: Spearman, Kendall, Top-k uplift capture, Qini AUC
    3. Calibration: Slope, Intercept, R², ECE
    4. Decision-focused: Policy value, Policy regret
    
    Returns
    -------
    metric_computer : callable
        Function(tau_true, tau_pred, mu0_true, mu1_true, ate_true) -> metrics dict
    """
    from metrics import (
        pehe, ate_error, cate_rank_correlation, qini_auc,
        cate_calibration_slope_intercept, cate_ece, 
        policy_value, policy_regret, topk_uplift_capture
    )
    
    def metric_computer(
        tau_true: np.ndarray,
        tau_pred: np.ndarray,
        mu0_true: Optional[np.ndarray] = None,
        mu1_true: Optional[np.ndarray] = None,
        ate_true: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Compute all relevant metrics.
        
        Parameters
        ----------
        tau_true : array
            True CATE
        tau_pred : array
            Predicted CATE
        mu0_true, mu1_true : array, optional
            True potential outcomes (for policy metrics)
        ate_true : float, optional
            True ATE
            
        Returns
        -------
        metrics : dict
            Dictionary of metric name -> value
        """
        metrics = {}
        
        # Handle edge cases
        if tau_pred is None or len(tau_pred) == 0:
            return {'pehe': np.nan, 'ate_abs_err': np.nan}
        
        tau_true = np.asarray(tau_true).ravel()
        tau_pred = np.asarray(tau_pred).ravel()
        
        # Ensure same length
        min_len = min(len(tau_true), len(tau_pred))
        tau_true = tau_true[:min_len]
        tau_pred = tau_pred[:min_len]
        
        # =====================================================================
        # 1. POINT ESTIMATION METRICS
        # =====================================================================
        
        # PEHE
        try:
            metrics['pehe'] = float(pehe(tau_true, tau_pred))
        except Exception:
            metrics['pehe'] = np.nan
        
        # ATE and error
        try:
            metrics['ate_hat'] = float(np.mean(tau_pred))
            ate_true_computed = float(np.mean(tau_true))
            if ate_true is not None:
                metrics['ate_abs_err'] = float(abs(np.mean(tau_pred) - ate_true))
            else:
                metrics['ate_abs_err'] = float(ate_error(tau_true, tau_pred))
            # Bias (signed)
            metrics['ate_bias'] = float(np.mean(tau_pred) - ate_true_computed)
        except Exception:
            metrics['ate_hat'] = np.nan
            metrics['ate_abs_err'] = np.nan
            metrics['ate_bias'] = np.nan
        
        # =====================================================================
        # 2. RANKING METRICS (Heterogeneity Discovery)
        # =====================================================================
        
        # Spearman correlation
        try:
            corr, pval = cate_rank_correlation(tau_true, tau_pred, method='spearman')
            metrics['tau_corr'] = float(corr) if not np.isnan(corr) else np.nan
        except Exception:
            metrics['tau_corr'] = np.nan
        
        # Kendall correlation
        try:
            corr_kendall, _ = cate_rank_correlation(tau_true, tau_pred, method='kendall')
            metrics['tau_kendall'] = float(corr_kendall) if not np.isnan(corr_kendall) else np.nan
        except Exception:
            metrics['tau_kendall'] = np.nan
        
        # Top-k uplift capture
        try:
            topk = topk_uplift_capture(tau_true, tau_pred, k_fractions=[0.1, 0.2, 0.3])
            metrics['topk_10_ratio'] = float(topk.get('topk_10_ratio', np.nan))
            metrics['topk_20_ratio'] = float(topk.get('topk_20_ratio', np.nan))
            metrics['topk_30_ratio'] = float(topk.get('topk_30_ratio', np.nan))
            metrics['topk_10_captured'] = float(topk.get('topk_10_captured', np.nan))
            metrics['topk_20_captured'] = float(topk.get('topk_20_captured', np.nan))
        except Exception:
            metrics['topk_10_ratio'] = np.nan
            metrics['topk_20_ratio'] = np.nan
            metrics['topk_30_ratio'] = np.nan
            metrics['topk_10_captured'] = np.nan
            metrics['topk_20_captured'] = np.nan
        
        # Qini AUC
        try:
            metrics['qini_auc'] = float(qini_auc(tau_true, tau_pred))
        except Exception:
            metrics['qini_auc'] = np.nan
        
        # =====================================================================
        # 3. CALIBRATION METRICS
        # =====================================================================
        
        try:
            intercept, slope, r2, degenerate = cate_calibration_slope_intercept(tau_true, tau_pred)
            metrics['calib_slope'] = float(slope)
            metrics['calib_intercept'] = float(intercept)
            metrics['calib_r2'] = float(r2)
        except Exception:
            metrics['calib_slope'] = np.nan
            metrics['calib_intercept'] = np.nan
            metrics['calib_r2'] = np.nan
        
        # ECE and MCE
        try:
            ece_val, mce_val, _ = cate_ece(tau_true, tau_pred)
            metrics['tau_ece'] = float(ece_val)
            metrics['tau_mce'] = float(mce_val)
        except Exception:
            metrics['tau_ece'] = np.nan
            metrics['tau_mce'] = np.nan
        
        # =====================================================================
        # 4. DECISION-FOCUSED METRICS (Policy Value / Regret)
        # =====================================================================
        
        if mu0_true is not None and mu1_true is not None:
            try:
                mu0_true = np.asarray(mu0_true).ravel()[:min_len]
                mu1_true = np.asarray(mu1_true).ravel()[:min_len]
                
                # Policy value (treat if τ̂ > 0)
                metrics['policy_value'] = float(policy_value(tau_pred, mu0_true, mu1_true, threshold=0.0))
                
                # Policy regret vs oracle
                metrics['policy_regret'] = float(policy_regret(tau_pred, mu0_true, mu1_true, threshold=0.0))
                
                # Top-k policy value/regret (treat top 20%)
                metrics['policy_value_top20'] = float(policy_value(tau_pred, mu0_true, mu1_true, top_fraction=0.2))
                metrics['policy_regret_top20'] = float(policy_regret(tau_pred, mu0_true, mu1_true, top_fraction=0.2))
                
            except Exception:
                metrics['policy_value'] = np.nan
                metrics['policy_regret'] = np.nan
                metrics['policy_value_top20'] = np.nan
                metrics['policy_regret_top20'] = np.nan
        else:
            metrics['policy_value'] = np.nan
            metrics['policy_regret'] = np.nan
            metrics['policy_value_top20'] = np.nan
            metrics['policy_regret_top20'] = np.nan
        
        # μ₀ RMSE (placeholder - would need model predictions)
        metrics['mu0_rmse'] = np.nan
        metrics['mu1_rmse'] = np.nan
        
        return metrics
    
    return metric_computer


# =============================================================================
# Method Factories
# =============================================================================

def create_method_factories(seed: int = 42) -> Dict[str, Callable]:
    """
    Create method factory functions for benchmark runner.
    
    Each factory returns a fresh estimator instance when called.
    Ablations mostly use the same PlaceboAnchoredDRLearner class with
    different `variant` settings for consistency, except for the
    placebo-only NoTransfer baseline.
    
    Parameters
    ----------
    seed : int
        Random seed
        
    Returns
    -------
    factories : dict
        method_name -> factory callable
    """
    from estimator_fixed import PlaceboAnchoredDRLearner
    
    # All methods use the same class with different variants
    # This ensures consistent behavior and artifact persistence
    factories = {
        # ═══════════════════════════════════════════════════════════════════
        # BASELINES
        # ═══════════════════════════════════════════════════════════════════
        
        # Target-only DR: Learn only on target (no source data)
        # NOTE: This is NOT "no transfer" - it's "target-only baseline"
        # Renamed from 'NoTransfer' for clarity per reviewer feedback
        'TargetOnlyDR': lambda: PlaceboAnchoredDRLearner(
            variant='target_only_dr', 
            random_state=seed
        ),
        
        # Backward-compat alias (use TargetOnlyDR in new code)
        'NoTransfer': lambda: PlaceboAnchoredDRLearner(
            variant='target_only_dr', 
            random_state=seed
        ),
        
        # Proxy only: source proxy models only, no anchoring (delta=0)
        'ProxyOnly': lambda: PlaceboAnchoredDRLearner(
            variant='proxy_only', 
            random_state=seed
        ),
        
        # ═══════════════════════════════════════════════════════════════════
        # ANCHOR ABLATIONS (with/without DR)
        # ═══════════════════════════════════════════════════════════════════
        
        # Anchor only: proxy + placebo correction + DR Stage 3
        'AnchorOnly': lambda: PlaceboAnchoredDRLearner(
            variant='anchor_only', 
            random_state=seed
        ),
        
        # NEW: Anchor plug-in: proxy + placebo correction, NO DR (plug-in CATE)
        # Shows what Stage 3 (DR pseudo-outcomes) adds
        'AnchorPlugin': lambda: PlaceboAnchoredDRLearner(
            variant='anchor_plugin', 
            random_state=seed
        ),
        
        # ═══════════════════════════════════════════════════════════════════
        # PROPOSED METHODS
        # ═══════════════════════════════════════════════════════════════════
        
        # Proposed Option A: needs target treated data
        'ProposedA': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A', 
            random_state=seed
        ),
        
        # Proposed Option A Together: joint correction model with A as feature
        'ProposedA_Together': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A_together', 
            random_state=seed
        ),
        
        # Proposed Option A with joint proxy: single Stage 1 model μ(X, A)
        'ProposedA_JointProxy': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A',
            proxy_mode='together',
            random_state=seed
        ),
        
        # Proposed Option A fully joint: joint proxy AND joint correction
        'ProposedA_FullyJoint': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A_together',
            proxy_mode='together',
            random_state=seed
        ),
        
        # ═══════════════════════════════════════════════════════════════════
        # DIRECT MODE VARIANTS: Fit on Y directly (not residuals)
        # ═══════════════════════════════════════════════════════════════════
        
        # Direct mode: fit μ directly on target Y (no residual structure)
        'ProposedA_Direct': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A',
            correction_mode='direct',
            random_state=seed
        ),
        
        # Direct + joint correction
        'ProposedA_Together_Direct': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A_together',
            correction_mode='direct',
            random_state=seed
        ),
        
        # Direct + joint proxy
        'ProposedA_JointProxy_Direct': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A',
            proxy_mode='together',
            correction_mode='direct',
            random_state=seed
        ),
        
        # Fully direct: joint proxy + joint correction + direct fitting
        'ProposedA_FullyDirect': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A_together',
            proxy_mode='together',
            correction_mode='direct',
            random_state=seed
        ),
        
        # ═══════════════════════════════════════════════════════════════════
        # NO CROSS-FITTING VARIANTS: Fit on all data (no held-out)
        # ═══════════════════════════════════════════════════════════════════
        
        # No cross-fitting with separate models
        'ProposedA_NoCrossfit': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A',
            cross_fitting=False,
            random_state=seed
        ),
        
        # No cross-fitting + direct mode
        'ProposedA_Direct_NoCrossfit': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A',
            correction_mode='direct',
            cross_fitting=False,
            random_state=seed
        ),
        
        # No cross-fitting + joint correction
        'ProposedA_Together_NoCrossfit': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A_together',
            cross_fitting=False,
            random_state=seed
        ),
        
        # No cross-fitting + joint + direct
        'ProposedA_Together_Direct_NoCrossfit': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A_together',
            correction_mode='direct',
            cross_fitting=False,
            random_state=seed
        ),
        
        # Proposed Option B (target DR): needs target treated for Stage 3
        # NOTE: Despite Step B, this still requires target treated for DR!
        'ProposedB_LinearStepB': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_B', 
            random_state=seed
        ),
        
        # NEW: Proposed Option B (source DR): works with placebo-only target!
        # This is the TRUE disconnected-target method from the paper
        'ProposedB_SourceDR': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_B_source_dr', 
            random_state=seed
        ),
        
        # Proposed Option B with ridge Stage-2 (for A5 dense correction)
        'ProposedB_RidgeStage2': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_B', 
            stage2_mode='ridge',
            random_state=seed
        ),
    }
    
    # Add transport baselines (reviewer-requested comparisons)
    try:
        from transport_baselines import create_transport_baseline_factories
        transport_factories = create_transport_baseline_factories(seed)
        factories.update(transport_factories)
    except ImportError:
        # Transport baselines not available
        pass
    
    # Add glmtrans-based estimators (Tian & Feng 2023 transfer learning)
    try:
        from glmtrans_wrapper import create_glmtrans_factories
        glmtrans_factories = create_glmtrans_factories(seed)
        factories.update(glmtrans_factories)
    except ImportError:
        # Glmtrans not available
        pass
    
    return factories


def create_method_factory_single(method_name: str, seed: int = 42) -> Callable:
    """
    Create a factory for a single method by name.
    
    Parameters
    ----------
    method_name : str
        Method name from METHOD_REGISTRY
    seed : int
        Random seed
        
    Returns
    -------
    factory : callable
        Factory that returns an estimator instance
    """
    factories = create_method_factories(seed)
    if method_name not in factories:
        raise ValueError(f"Unknown method: {method_name}. Available: {list(factories.keys())}")
    return factories[method_name]


# =============================================================================
# Efficient Multi-Method Runner (uses SharedComponents)
# =============================================================================

def run_methods_efficiently(
    data: Dict[str, Any],
    methods: list,
    seed: int = 42,
    verbose: bool = False
) -> Dict[str, Dict[str, Any]]:
    """
    Run multiple methods efficiently by sharing Stage 1 and Step B.
    
    This avoids refitting proxy models and transfer operator for each method,
    providing significant speedup when running multiple ablations.
    
    FIX #9: Only fit shared components that are actually needed by the methods.
    
    Parameters
    ----------
    data : dict
        Data dictionary from data_generator with keys:
        X_source, A_source, Y_source, c_source, X_target, A_target, Y_target, etc.
    methods : list of str
        Method names to run
    seed : int
        Random seed
    verbose : bool
        Print progress
        
    Returns
    -------
    results : dict
        method_name -> {
            'tau_pred': array,
            'estimator': fitted estimator,
            'diagnostics': dict
        }
    """
    from estimator_fixed import SharedComponents, PlaceboAnchoredDRLearner
    
    # Map method names to variants
    method_to_variant = {
        'NoTransfer': 'no_transfer',
        'ProxyOnly': 'proxy_only',
        'AnchorOnly': 'anchor_only',
        'AnchorOnlyA': 'anchor_only_A',  # Added new variant
        'ProposedA': 'proposed_A',
        'ProposedA_Together': 'proposed_A_together',  # Joint outcome model
        'ProposedB_LinearStepB': 'proposed_B',
        'ProposedB_RidgeStage2': 'proposed_B',  # Same variant, different stage2_mode
    }
    
    method_to_stage2_mode = {
        'ProposedB_RidgeStage2': 'ridge',
    }
    
    # Get variants for the methods we're running
    variants = [method_to_variant.get(m, 'proposed_B') for m in methods if m in method_to_variant]
    
    # Determine what needs to be fit (FIX #2: only fit what's needed)
    need_proxy = any(v in ['proxy_only', 'anchor_only', 'anchor_only_A', 'proposed_A', 'proposed_A_together', 'proposed_B'] for v in variants)
    need_stepB = any(v == 'proposed_B' for v in variants)
    
    results = {}
    X_eval = data.get('X_target_eval', data['X_target'])
    
    if need_proxy:
        # Fit shared components once (only fit what's needed)
        if verbose:
            print(f"Fitting shared components (fit_proxy={need_proxy}, fit_stepB={need_stepB})...")
        
        shared = SharedComponents(random_state=seed, verbose=verbose)
        shared.fit(
            data['X_source'], data['A_source'], 
            data['Y_source'], data['c_source'],
            fit_proxy=need_proxy,
            fit_stepB=need_stepB
        )
        
        # Run each method using shared components
        for method in methods:
            variant = method_to_variant.get(method)
            if variant is None:
                warnings.warn(f"Unknown method {method}, skipping")
                continue
            
            stage2_mode = method_to_stage2_mode.get(method, 'lasso')
            
            if verbose:
                print(f"  Running {method} (variant={variant})...")
            
            est = PlaceboAnchoredDRLearner(
                variant=variant,
                stage2_mode=stage2_mode,
                random_state=seed,
                verbose=False
            )
            
            # Use shared components
            est.fit_with_shared(
                shared,
                data['X_target'], data['A_target'], data['Y_target'],
                data.get('propensity_target')
            )
            
            tau_pred = est.predict(X_eval)
            
            results[method] = {
                'tau_pred': tau_pred,
                'estimator': est,
                'diagnostics': est.get_diagnostics()
            }
    else:
        # No shared components needed (all no_transfer)
        for method in methods:
            variant = method_to_variant.get(method, 'no_transfer')
            
            est = PlaceboAnchoredDRLearner(
                variant=variant,
                random_state=seed,
                verbose=False
            )
            
            est.fit(
                data['X_source'], data['A_source'], 
                data['Y_source'], data['c_source'],
                data['X_target'], data['A_target'], data['Y_target'],
                data.get('propensity_target')
            )
            
            tau_pred = est.predict(X_eval)
            
            results[method] = {
                'tau_pred': tau_pred,
                'estimator': est,
                'diagnostics': est.get_diagnostics()
            }
    
    return results


# =============================================================================
# Estimator Wrapper (standardizes fit/predict interface)
# =============================================================================

class EstimatorWrapper:
    """
    Wrapper that standardizes the fit/predict interface for benchmark runner.
    
    Different estimators may have different signatures; this unifies them.
    """
    
    def __init__(self, estimator):
        self.estimator = estimator
        self.fitted = False
    
    def fit(self, data: Dict[str, Any]) -> 'EstimatorWrapper':
        """Fit estimator on data dict."""
        self.estimator.fit(
            X_source=data['X_source'],
            A_source=data['A_source'],
            Y_source=data['Y_source'],
            c_source=data['c_source'],
            X_target=data['X_target'],
            A_target=data['A_target'],
            Y_target=data['Y_target'],
            propensity_target=data.get('propensity_target')
        )
        self.fitted = True
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict CATE."""
        return self.estimator.predict(X)
    
    def __getattr__(self, name):
        """Forward attribute access to wrapped estimator."""
        return getattr(self.estimator, name)


def create_wrapped_method_factories(seed: int = 42) -> Dict[str, Callable]:
    """
    Create method factories that return wrapped estimators.
    
    The wrappers provide a standardized interface for benchmark_runner.
    """
    base_factories = create_method_factories(seed)
    
    wrapped = {}
    for name, factory in base_factories.items():
        wrapped[name] = lambda f=factory: EstimatorWrapper(f())
    
    return wrapped


# =============================================================================
# Convenience Functions
# =============================================================================

def run_single_method(
    method_name: str,
    data: Dict[str, Any],
    seed: int = 42
) -> np.ndarray:
    """
    Run a single method on data and return predictions.
    
    Convenience function for testing.
    """
    factories = create_method_factories(seed)
    if method_name not in factories:
        raise ValueError(f"Unknown method: {method_name}")
    
    estimator = factories[method_name]()
    
    # Fit
    estimator.fit(
        X_source=data['X_source'],
        A_source=data['A_source'],
        Y_source=data['Y_source'],
        c_source=data['c_source'],
        X_target=data['X_target'],
        A_target=data['A_target'],
        Y_target=data['Y_target'],
        propensity_target=data.get('propensity_target')
    )
    
    # Predict
    X_eval = data.get('X_target_eval', data['X_target'])
    return estimator.predict(X_eval)


def quick_benchmark(
    n_rep: int = 5,
    m0: int = 100,
    methods: list = ['ProxyOnly', 'ProposedB_LinearStepB'],
    seed: int = 42
) -> Dict[str, Dict[str, float]]:
    """
    Quick benchmark for testing.
    
    Returns dict of method -> {metric: value}.
    """
    data_gen = create_data_generator()
    metric_comp = create_metric_computer()
    
    from benchmark_schema import Scenario
    scenario = Scenario(benchmark_id='quick', m0=m0, n_proxy_total=2000, C_sources=10)
    
    results = {m: [] for m in methods}
    
    for rep in range(n_rep):
        data = data_gen(scenario, seed + rep)
        
        for method in methods:
            tau_pred = run_single_method(method, data, seed + rep)
            metrics = metric_comp(
                tau_true=data['tau_true'],
                tau_pred=tau_pred,
                mu0_true=data['mu0_true'],
                mu1_true=data['mu1_true'],
                ate_true=data['ate_true']
            )
            results[method].append(metrics)
    
    # Aggregate
    aggregated = {}
    for method in methods:
        aggregated[method] = {}
        for metric in results[method][0].keys():
            vals = [r[metric] for r in results[method] if not np.isnan(r[metric])]
            if vals:
                aggregated[method][metric] = np.mean(vals)
            else:
                aggregated[method][metric] = np.nan
    
    return aggregated


# =============================================================================
# CLI Test
# =============================================================================

if __name__ == "__main__":
    print("Testing benchmark adapters...")
    
    # Quick test
    results = quick_benchmark(n_rep=3, m0=100)
    
    print("\nQuick Benchmark Results (3 reps, m0=100):")
    print("-" * 50)
    for method, metrics in results.items():
        print(f"\n{method}:")
        for metric, value in metrics.items():
            if not np.isnan(value):
                print(f"  {metric}: {value:.4f}")
    
    print("\n✓ Adapters work!")
