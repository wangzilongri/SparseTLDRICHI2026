"""
Benchmark Runner: Grid + Monte Carlo experiment driver.

This module provides the infrastructure for running systematic benchmark
experiments with parameter sweeps and Monte Carlo replications.
"""

import os
import sys
import time
import warnings
import traceback
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable, Tuple
from itertools import product
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from benchmark_schema import (
    Scenario, MethodSpec, RepResult, Feasibility,
    METHOD_REGISTRY, get_method_spec, generate_seed,
    validate_results_rep, create_empty_results_df,
    CORE_METRIC_COLS
)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class BenchmarkConfig:
    """
    Configuration for a benchmark experiment.
    
    Parameters
    ----------
    benchmark_id : str
        Unique identifier for this benchmark
    base_scenario : Dict[str, Any]
        Base scenario parameters (shared across all configs in grid)
    sweep_params : Dict[str, List[Any]]
        Parameters to sweep (cartesian product)
    n_rep : int
        Number of Monte Carlo replications per scenario
    seed0 : int
        Master seed for reproducibility
    methods : List[str]
        Methods to run (must be in METHOD_REGISTRY)
    has_target_treated : bool
        Whether target treated data is available (affects feasibility)
    output_dir : str
        Directory for results
    n_jobs : int
        Number of parallel jobs (-1 for all cores)
    verbose : bool
        Print progress
    """
    benchmark_id: str
    base_scenario: Dict[str, Any]
    sweep_params: Dict[str, List[Any]]
    n_rep: int = 100
    seed0: int = 42
    methods: List[str] = field(default_factory=lambda: ['ProxyOnly', 'AnchorOnly', 'ProposedB_LinearStepB'])
    has_target_treated: bool = False
    output_dir: str = 'results/benchmarks'
    n_jobs: int = 1
    verbose: bool = True
    
    def __post_init__(self):
        # Validate methods
        unknown = set(self.methods) - set(METHOD_REGISTRY.keys())
        if unknown:
            raise ValueError(f"Unknown methods: {unknown}")


# =============================================================================
# Scenario Grid Generation
# =============================================================================

def generate_scenario_grid(config: BenchmarkConfig) -> List[Scenario]:
    """
    Generate all scenarios from base config and sweep parameters.
    
    Returns list of Scenario objects (cartesian product of sweep params).
    """
    if not config.sweep_params:
        # No sweep, just base scenario
        return [Scenario(benchmark_id=config.benchmark_id, **config.base_scenario)]
    
    # Generate cartesian product
    param_names = list(config.sweep_params.keys())
    param_values = list(config.sweep_params.values())
    
    scenarios = []
    for combo in product(*param_values):
        scenario_params = config.base_scenario.copy()
        for name, value in zip(param_names, combo):
            scenario_params[name] = value
        
        scenario = Scenario(benchmark_id=config.benchmark_id, **scenario_params)
        scenarios.append(scenario)
    
    return scenarios


# =============================================================================
# Method Factory Protocol
# =============================================================================

# Type alias for method factory
# Factory takes (seed) and returns a fitted estimator-like object
MethodFactory = Callable[[int], Any]


def create_default_method_factories(seed: int) -> Dict[str, Callable]:
    """
    Create default method factories.
    
    Returns dict of method_name -> callable that returns fresh estimator instance.
    This is a placeholder - actual implementations should be provided.
    """
    from estimator_fixed import PlaceboAnchoredDRLearner
    from ablations import ProxyOnlyBaseline, AnchorOnlyBaseline, NoTransferBaseline
    
    factories = {
        'NoTransfer': lambda: NoTransferBaseline(),
        'ProxyOnly': lambda: ProxyOnlyBaseline(),
        'AnchorOnly': lambda: AnchorOnlyBaseline(),
        'ProposedA': lambda: PlaceboAnchoredDRLearner(option='A'),
        'ProposedB_LinearStepB': lambda: PlaceboAnchoredDRLearner(option='B'),
    }
    return factories


# =============================================================================
# Single Rep Execution
# =============================================================================

def run_single_rep(
    scenario: Scenario,
    rep: int,
    seed: int,
    method_factories: Dict[str, Callable],
    data_generator: Callable,
    metric_computer: Callable,
    has_target_treated: bool
) -> List[RepResult]:
    """
    Run a single Monte Carlo replicate for all methods.
    
    Parameters
    ----------
    scenario : Scenario
        The scenario configuration
    rep : int
        Replicate index
    seed : int
        Random seed for this rep
    method_factories : dict
        Dict of method_name -> factory callable
    data_generator : callable
        Function(scenario, seed) -> data dict
    metric_computer : callable
        Function(tau_true, tau_pred, mu0_true, mu1_true, ...) -> metrics dict
    has_target_treated : bool
        Whether target treated is available
        
    Returns
    -------
    list of RepResult
        Results for each method
    """
    np.random.seed(seed)
    results = []
    
    # Generate data
    try:
        data = data_generator(scenario, seed)
    except Exception as e:
        warnings.warn(f"Data generation failed for scenario {scenario.scenario_id}, rep {rep}: {e}")
        return results
    
    # Extract ground truth for evaluation
    tau_true = data.get('tau_true')
    mu0_true = data.get('mu0_true')
    mu1_true = data.get('mu1_true')
    ate_true = data.get('ate_true', np.mean(tau_true) if tau_true is not None else None)
    
    # Run each method
    for method_name, factory in method_factories.items():
        method_spec = get_method_spec(method_name)
        feasibility = method_spec.get_feasibility(has_target_treated)
        
        # Skip infeasible methods
        if feasibility == Feasibility.INFEASIBLE_BY_DESIGN:
            continue
        
        # Skip if method needs target treated but it's not available
        if method_spec.uses_target_treated and not has_target_treated:
            continue
        
        t0 = time.time()
        try:
            # Create fresh estimator
            estimator = factory()
            
            # Fit and predict
            # Note: This assumes estimators have fit() and predict() methods
            # Actual interface depends on your estimator implementations
            estimator.fit(data)
            tau_pred = estimator.predict(data.get('X_target_eval', data.get('X_target')))
            
            runtime = time.time() - t0
            
            # Compute metrics
            metrics = metric_computer(
                tau_true=tau_true,
                tau_pred=tau_pred,
                mu0_true=mu0_true,
                mu1_true=mu1_true,
                ate_true=ate_true
            )
            
            # Get diagnostics from estimator if available
            diagnostics = {}
            if hasattr(estimator, 'stage2_lambda_'):
                diagnostics['stage2_lambda'] = estimator.stage2_lambda_
            if hasattr(estimator, 'stage2_n_selected_'):
                diagnostics['stage2_n_selected'] = estimator.stage2_n_selected_
            if hasattr(estimator, 'transfer_diagnostics_'):
                td = estimator.transfer_diagnostics_
                diagnostics['stepb_M_fro_norm'] = td.get('M_fro_norm')
                diagnostics['stepb_M_spectral_norm'] = td.get('M_spectral_norm')
                diagnostics['stepb_M_effective_rank'] = td.get('M_effective_rank')
                diagnostics['stepb_n_sites_used'] = td.get('n_sites_used')
            
            # Create result
            result = RepResult(
                scenario_id=scenario.scenario_id,
                benchmark_id=scenario.benchmark_id,
                rep=rep,
                method=method_name,
                feasibility=feasibility.value,
                seed=seed,
                uses_target_placebo=method_spec.uses_target_placebo,
                uses_target_treated=method_spec.uses_target_treated,
                uses_source_data=method_spec.uses_source_data,
                pehe=metrics.get('pehe'),
                tau_corr=metrics.get('tau_corr'),
                ate_hat=metrics.get('ate_hat'),
                ate_true=ate_true,
                ate_abs_err=metrics.get('ate_abs_err'),
                mu0_rmse=metrics.get('mu0_rmse'),
                mu1_rmse=metrics.get('mu1_rmse'),
                mu0_ece=metrics.get('mu0_ece'),
                tau_ece=metrics.get('tau_ece'),
                policy_regret=metrics.get('policy_regret'),
                qini_auc=metrics.get('qini_auc'),
                runtime_sec=runtime,
                **diagnostics
            )
            results.append(result)
            
        except Exception as e:
            warnings.warn(f"Method {method_name} failed for scenario {scenario.scenario_id}, rep {rep}: {e}")
            traceback.print_exc()
            # Record failure with NaN metrics
            result = RepResult(
                scenario_id=scenario.scenario_id,
                benchmark_id=scenario.benchmark_id,
                rep=rep,
                method=method_name,
                feasibility=feasibility.value,
                seed=seed,
                pehe=np.nan,
                runtime_sec=time.time() - t0
            )
            results.append(result)
    
    return results


# =============================================================================
# Parallel Execution
# =============================================================================

def _run_rep_wrapper(args):
    """Wrapper for parallel execution."""
    scenario, rep, seed, method_factories, data_generator, metric_computer, has_target_treated = args
    return run_single_rep(
        scenario, rep, seed, method_factories,
        data_generator, metric_computer, has_target_treated
    )


def run_benchmark(
    config: BenchmarkConfig,
    data_generator: Callable,
    metric_computer: Callable,
    method_factories: Optional[Dict[str, Callable]] = None
) -> pd.DataFrame:
    """
    Run a complete benchmark experiment.
    
    Parameters
    ----------
    config : BenchmarkConfig
        Benchmark configuration
    data_generator : callable
        Function(scenario, seed) -> data dict
    metric_computer : callable
        Function(tau_true, tau_pred, ...) -> metrics dict
    method_factories : dict, optional
        Method name -> factory callable. If None, uses defaults.
        
    Returns
    -------
    pd.DataFrame
        Long-format results DataFrame (results_rep schema)
    """
    # Generate scenarios
    scenarios = generate_scenario_grid(config)
    n_scenarios = len(scenarios)
    
    if config.verbose:
        print(f"="*70)
        print(f"Benchmark: {config.benchmark_id}")
        print(f"Scenarios: {n_scenarios}")
        print(f"Reps per scenario: {config.n_rep}")
        print(f"Methods: {config.methods}")
        print(f"Total runs: {n_scenarios * config.n_rep * len(config.methods)}")
        print(f"="*70)
    
    # Setup method factories
    if method_factories is None:
        method_factories = create_default_method_factories(config.seed0)
    
    # Filter to requested methods
    method_factories = {k: v for k, v in method_factories.items() if k in config.methods}
    
    # Collect all results
    all_results = []
    
    # Generate all tasks
    tasks = []
    for scenario in scenarios:
        for rep in range(config.n_rep):
            seed = generate_seed(scenario.scenario_id, rep, config.seed0)
            tasks.append((
                scenario, rep, seed, method_factories,
                data_generator, metric_computer, config.has_target_treated
            ))
    
    # Execute
    if config.n_jobs == 1:
        # Sequential
        iterator = tqdm(tasks, desc="Running", disable=not config.verbose)
        for task in iterator:
            results = _run_rep_wrapper(task)
            all_results.extend(results)
    else:
        # Parallel
        n_workers = config.n_jobs if config.n_jobs > 0 else os.cpu_count()
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = [executor.submit(_run_rep_wrapper, task) for task in tasks]
            for future in tqdm(as_completed(futures), total=len(futures), 
                             desc="Running", disable=not config.verbose):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    warnings.warn(f"Task failed: {e}")
    
    # Convert to DataFrame
    if not all_results:
        warnings.warn("No results collected!")
        return create_empty_results_df()
    
    rows = [r.to_dict() for r in all_results]
    df = pd.DataFrame(rows)
    
    # Add scenario parameters
    scenario_lookup = {s.scenario_id: s.to_dict() for s in scenarios}
    for col in scenario_lookup[scenarios[0].scenario_id].keys():
        if col not in df.columns:
            df[col] = df['scenario_id'].map(lambda sid: scenario_lookup[sid].get(col))
    
    # Validate
    try:
        validate_results_rep(df, config.benchmark_id)
    except ValueError as e:
        warnings.warn(f"Validation warning: {e}")
    
    # Save
    os.makedirs(config.output_dir, exist_ok=True)
    output_path = os.path.join(config.output_dir, f"results_rep_{config.benchmark_id}.csv")
    df.to_csv(output_path, index=False)
    
    if config.verbose:
        print(f"\n✓ Results saved: {output_path}")
        print(f"  Shape: {df.shape}")
        print(f"  Methods: {df['method'].unique().tolist()}")
        print(f"  Scenarios: {df['scenario_id'].nunique()}")
    
    return df


# =============================================================================
# Quick Benchmark Helpers
# =============================================================================

def run_gold_sweep(
    m0_values: List[int] = [25, 50, 100, 200, 500],
    n_proxy_total: int = 2000,
    n_rep: int = 100,
    seed0: int = 42,
    **kwargs
) -> pd.DataFrame:
    """
    Run gold-budget (m0) sweep benchmark.
    
    This is a convenience wrapper for the most common benchmark.
    """
    config = BenchmarkConfig(
        benchmark_id='gold_sweep',
        base_scenario={
            'n_proxy_total': n_proxy_total,
            'C_sources': 10,
            'nontransfer_scale': 0.3,
        },
        sweep_params={'m0': m0_values},
        n_rep=n_rep,
        seed0=seed0,
        **kwargs
    )
    
    # Import here to avoid circular imports
    from benchmark_adapters import create_data_generator, create_metric_computer
    
    return run_benchmark(
        config,
        data_generator=create_data_generator(),
        metric_computer=create_metric_computer()
    )


def run_proxy_sweep(
    n_proxy_values: List[int] = [500, 1000, 2000, 5000, 10000],
    m0: int = 100,
    n_rep: int = 100,
    seed0: int = 42,
    **kwargs
) -> pd.DataFrame:
    """Run proxy-budget sweep benchmark."""
    config = BenchmarkConfig(
        benchmark_id='proxy_sweep',
        base_scenario={
            'm0': m0,
            'C_sources': 10,
            'nontransfer_scale': 0.3,
        },
        sweep_params={'n_proxy_total': n_proxy_values},
        n_rep=n_rep,
        seed0=seed0,
        **kwargs
    )
    
    from benchmark_adapters import create_data_generator, create_metric_computer
    
    return run_benchmark(
        config,
        data_generator=create_data_generator(),
        metric_computer=create_metric_computer()
    )


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run benchmark experiments")
    parser.add_argument('--benchmark', type=str, default='gold_sweep',
                       choices=['gold_sweep', 'proxy_sweep', 'site_imbalance'],
                       help='Benchmark to run')
    parser.add_argument('--n_rep', type=int, default=10, help='MC replicates')
    parser.add_argument('--seed', type=int, default=42, help='Master seed')
    parser.add_argument('--output', type=str, default='results/benchmarks', help='Output dir')
    parser.add_argument('--n_jobs', type=int, default=1, help='Parallel jobs')
    
    args = parser.parse_args()
    
    print(f"Running {args.benchmark} benchmark...")
    
    if args.benchmark == 'gold_sweep':
        df = run_gold_sweep(n_rep=args.n_rep, seed0=args.seed, 
                           output_dir=args.output, n_jobs=args.n_jobs)
    elif args.benchmark == 'proxy_sweep':
        df = run_proxy_sweep(n_rep=args.n_rep, seed0=args.seed,
                            output_dir=args.output, n_jobs=args.n_jobs)
    
    print(f"\nResults shape: {df.shape}")
    print(df.groupby('method')['pehe'].agg(['mean', 'std', 'count']))
