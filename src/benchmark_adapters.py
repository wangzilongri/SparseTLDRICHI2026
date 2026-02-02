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
        # Map scenario params to SyntheticRCTConfig
        config_kwargs = {
            'random_state': seed,
        }
        
        # Target sizes
        if scenario.m0 is not None:
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
        
        # Create config
        config = SyntheticRCTConfig(**config_kwargs)
        
        # Generate data
        generator = SyntheticRCTGenerator(config)
        source_data, target_data = generator.generate_full_dataset()
        
        # Generate larger evaluation set for target (held out)
        # Keep estimation data small (m0), but have plenty for evaluation
        np.random.seed(seed + 10000)  # Different seed for eval
        eval_target = generator.generate_site_data(0, 1000)
        
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
            
            # Propensity (uniform in RCT)
            'propensity_target': np.full(len(target_data['X']), 0.5),
            
            # Generator for diagnostics
            'generator': generator,
        }
        
        return data
    
    return data_generator


# =============================================================================
# Metric Computer Adapter
# =============================================================================

def create_metric_computer() -> Callable:
    """
    Create a metric computer function compatible with benchmark_runner.
    
    Returns
    -------
    metric_computer : callable
        Function(tau_true, tau_pred, mu0_true, mu1_true, ate_true) -> metrics dict
    """
    from metrics import (
        pehe, ate_error, cate_rank_correlation, qini_auc,
        cate_calibration_slope_intercept, cate_ece, policy_metrics
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
        
        # PEHE
        try:
            metrics['pehe'] = float(pehe(tau_true, tau_pred))
        except Exception:
            metrics['pehe'] = np.nan
        
        # ATE error
        try:
            metrics['ate_hat'] = float(np.mean(tau_pred))
            if ate_true is not None:
                metrics['ate_abs_err'] = float(abs(np.mean(tau_pred) - ate_true))
            else:
                metrics['ate_abs_err'] = float(ate_error(tau_true, tau_pred))
        except Exception:
            metrics['ate_hat'] = np.nan
            metrics['ate_abs_err'] = np.nan
        
        # Rank correlation
        try:
            corr, pval = cate_rank_correlation(tau_true, tau_pred, method='spearman')
            metrics['tau_corr'] = float(corr) if not np.isnan(corr) else np.nan
        except Exception:
            metrics['tau_corr'] = np.nan
        
        # Qini AUC
        try:
            metrics['qini_auc'] = float(qini_auc(tau_true, tau_pred))
        except Exception:
            metrics['qini_auc'] = np.nan
        
        # Calibration
        try:
            intercept, slope, r2, degenerate = cate_calibration_slope_intercept(tau_true, tau_pred)
            metrics['calib_slope'] = float(slope)
            metrics['calib_intercept'] = float(intercept)
            metrics['calib_r2'] = float(r2)
        except Exception:
            metrics['calib_slope'] = np.nan
            metrics['calib_intercept'] = np.nan
            metrics['calib_r2'] = np.nan
        
        # ECE
        try:
            ece_val, mce_val, _ = cate_ece(tau_true, tau_pred)
            metrics['tau_ece'] = float(ece_val)
        except Exception:
            metrics['tau_ece'] = np.nan
        
        # Policy metrics (if potential outcomes available)
        if mu0_true is not None and mu1_true is not None:
            try:
                mu0_true = np.asarray(mu0_true).ravel()[:min_len]
                mu1_true = np.asarray(mu1_true).ravel()[:min_len]
                pm = policy_metrics(tau_true, tau_pred, mu0_true, mu1_true)
                metrics['policy_regret'] = float(pm.get('regret_treat_positive', np.nan))
            except Exception:
                metrics['policy_regret'] = np.nan
        
        # μ₀ RMSE (if we had predictions, but for now skip)
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
    All ablations now use the same PlaceboAnchoredDRLearner class with
    different `variant` settings for consistency and reproducibility.
    
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
        # No transfer: target-only, no source data used
        'NoTransfer': lambda: PlaceboAnchoredDRLearner(
            variant='no_transfer', 
            random_state=seed
        ),
        
        # Proxy only: source proxy models only, no anchoring (delta=0)
        'ProxyOnly': lambda: PlaceboAnchoredDRLearner(
            variant='proxy_only', 
            random_state=seed
        ),
        
        # Anchor only: proxy + placebo correction, no Step B transfer
        'AnchorOnly': lambda: PlaceboAnchoredDRLearner(
            variant='anchor_only', 
            random_state=seed
        ),
        
        # Anchor only A: proxy + both corrections from target, no Step B
        # Fair comparison when target has both arms
        'AnchorOnlyA': lambda: PlaceboAnchoredDRLearner(
            variant='anchor_only_A', 
            random_state=seed
        ),
        
        # Proposed Option A: needs target treated data
        'ProposedA': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_A', 
            random_state=seed
        ),
        
        # Proposed Option B with linear Step B: the main method
        'ProposedB_LinearStepB': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_B', 
            random_state=seed
        ),
        
        # Proposed Option B with ridge Stage-2 (for A5 dense correction)
        'ProposedB_RidgeStage2': lambda: PlaceboAnchoredDRLearner(
            variant='proposed_B', 
            stage2_mode='ridge',
            random_state=seed
        ),
    }
    
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
        'ProposedB_LinearStepB': 'proposed_B',
        'ProposedB_RidgeStage2': 'proposed_B',  # Same variant, different stage2_mode
    }
    
    method_to_stage2_mode = {
        'ProposedB_RidgeStage2': 'ridge',
    }
    
    # Get variants for the methods we're running
    variants = [method_to_variant.get(m, 'proposed_B') for m in methods if m in method_to_variant]
    
    # Determine what needs to be fit (FIX #2: only fit what's needed)
    need_proxy = any(v in ['proxy_only', 'anchor_only', 'anchor_only_A', 'proposed_A', 'proposed_B'] for v in variants)
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
