"""
IHDP Semi-Synthetic Sweeps: Multi-site benchmark with real covariates.

These sweeps use the IHDP (Infant Health and Development Program) dataset
to construct multi-site RCT data via k-means clustering. This provides:
1. Real covariate distributions (25 features)
2. Known ground-truth CATE for exact evaluation
3. Natural covariate shift between clusters

Usage:
    python experiments/ihdp_sweeps.py --sweep connected --n_rep 50 --output results/ihdp
    python experiments/ihdp_sweeps.py --sweep disconnected --n_rep 50 --output results/ihdp
    python experiments/ihdp_sweeps.py --sweep all --n_rep 50 --output results/ihdp
"""

import os
import sys
import argparse
import warnings
import time
from datetime import datetime
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from benchmark_schema import (
    Scenario, Feasibility,
    generate_seed, 
    METHOD_REGISTRY, get_method_spec
)
from dataclasses import dataclass
from typing import Dict, Any
# Don't import aggregate_results - we'll use our own simpler version
from benchmark_adapters import (
    create_ihdp_data_generator, create_metric_computer, create_method_factories
)


# =============================================================================
# DEFAULT METHOD LISTS FOR IHDP
# =============================================================================

# Methods for disconnected target (m1=0, placebo-only)
IHDP_METHODS_OPTION_B = [
    # Baselines
    'ProxyOnly',           # Source proxy only (no correction)
    
    # Transport baselines (don't require target treated)
    'IPWTransport',           # Weighted outcome models
    'EntropyBalancing',       # Entropy balancing weights
    'OutcomeModelTransport',  # Unweighted outcome models
    
    # Anchor-based
    'AnchorPlugin',        # Proxy + placebo correction (no DR)
    
    # glmtrans transfer learning
    'Glmtrans_OptionB',    # RECOMMENDED for Option B (placebo-only)
]

# Methods for connected target (m1>0, has target treated)
IHDP_METHODS_OPTION_A = [
    # Baselines
    'TargetOnlyDR',        # Target-only DR (no transfer)
    'ProxyOnly',           # Source proxy only
    
    # Anchor-based
    'AnchorOnly',          # Proxy + placebo correction + DR
    'AnchorPlugin',        # Proxy + placebo correction (no DR)
    
    # Transport baselines
    'IPWTransport',           # Weighted outcome models
    'EntropyBalancing',       # Entropy balancing weights
    'OutcomeModelTransport',  # Unweighted outcome models
    
    # glmtrans transfer learning (Tian & Feng 2023)
    'Glmtrans_Auto',       # Auto source detection (plug-in)
    'Glmtrans_DR_CrossFit',# RECOMMENDED: Cross-fitted DR
]


# =============================================================================
# IHDP SWEEP CONFIGURATIONS
# =============================================================================

IHDP_SWEEP_CONFIGS = {
    # =========================================================================
    # CONNECTED TARGET (Option A): Target has both placebo and treated
    # =========================================================================
    'ihdp_connected': {
        'benchmark_id': 'ihdp_connected_sweep',
        'description': 'IHDP connected target: m₀ × m₁ budget sweep',
        'base_scenario': {
            'use_ihdp': True,
            'n_sites': 6,
        },
        'sweep_type': 'grid_2d',
        'sweep_param': 'm0',
        'sweep_param_2': 'm1',
        'sweep_values': [25, 50, 100],  # m0 values
        'm1_values': [25, 50, 100],     # m1 values (all > 0)
        'methods': IHDP_METHODS_OPTION_A,
        
        'motivation': """
**Research Question:** How do estimators perform on real IHDP covariates with varying target budgets?

**Why This Matters:**
- IHDP provides real covariate distributions (not simulated)
- Ground-truth CATE enables exact PEHE evaluation
- Multi-site structure via k-means provides natural covariate shift
- Tests Option A methods that require target treated data

**Expected Behavior:**
- All methods improve as (m₀, m₁) increase
- Proposed methods (Glmtrans_Auto, Glmtrans_DR_CrossFit) should dominate
- TargetOnlyDR competitive only at large budgets
""",
    },
    
    # =========================================================================
    # DISCONNECTED TARGET (Option B): Target has placebo only
    # =========================================================================
    'ihdp_disconnected': {
        'benchmark_id': 'ihdp_disconnected_sweep',
        'description': 'IHDP disconnected target: m₀ sweep with m₁=0',
        'base_scenario': {
            'use_ihdp': True,
            'n_sites': 6,
            'm1': 0,  # Disconnected: no target treated
        },
        'sweep_type': '1d',
        'sweep_param': 'm0',
        'sweep_values': [25, 50, 100, 200],  # Target placebo budget
        'methods': IHDP_METHODS_OPTION_B,
        
        'motivation': """
**Research Question:** Can we estimate CATE in IHDP when target has placebo only?

**Why This Matters:**
- Tests the "disconnected trial network" scenario from reviewer comments
- Target site observes placebo outcomes only (m₁ = 0)
- Must transport CATE from sources to target
- Validates Assumption A6 (screening-valid transportability)

**Expected Behavior:**
- Glmtrans_OptionB should match or beat transport baselines
- Performance improves with m₀ (better source selection)
- AnchorPlugin competitive but may overfit at low m₀
""",
    },
    
    # =========================================================================
    # SITE SCALING: Vary number of source sites
    # =========================================================================
    'ihdp_site_scaling': {
        'benchmark_id': 'ihdp_site_scaling_sweep',
        'description': 'IHDP site scaling: vary number of clusters',
        'base_scenario': {
            'use_ihdp': True,
            'm0': 50,
            'm1': 50,  # Connected target
        },
        'sweep_type': '1d',
        'sweep_param': 'n_sites',
        'sweep_values': [3, 4, 5, 6],  # Number of k-means clusters
        'methods': IHDP_METHODS_OPTION_A,
        
        'motivation': """
**Research Question:** How does the number of source sites affect transfer learning on IHDP?

**Why This Matters:**
- More sites = smaller clusters = potentially stronger covariate shift
- Tests robustness of source detection mechanism
- Fewer sites = more data per site but less diversity

**Expected Behavior:**
- Sweet spot around 4-5 sites (balance of data and diversity)
- Glmtrans methods should handle varying site counts gracefully
""",
    },
    
    # =========================================================================
    # DISCONNECTED SITE SCALING
    # =========================================================================
    'ihdp_disconnected_site_scaling': {
        'benchmark_id': 'ihdp_disconnected_site_scaling_sweep',
        'description': 'IHDP disconnected: vary sites with m₁=0',
        'base_scenario': {
            'use_ihdp': True,
            'm0': 100,
            'm1': 0,  # Disconnected
        },
        'sweep_type': '1d',
        'sweep_param': 'n_sites',
        'sweep_values': [3, 4, 5, 6],
        'methods': IHDP_METHODS_OPTION_B,
        
        'motivation': """
**Research Question:** How does site diversity affect Option B on IHDP?

**Why This Matters:**
- In disconnected regime, CATE is learned entirely from sources
- More sites may improve source selection via glmtrans
- Tests robustness of Assumption A6 screening
""",
    },
}


# =============================================================================
# AGGREGATION
# =============================================================================

def _aggregate_ihdp_results(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate IHDP results across replications.
    
    Groups by (benchmark_id, method, m0, m1, n_sites) and computes
    mean/std for each metric.
    """
    # Group columns (scenario identifiers)
    group_cols = ['benchmark_id', 'method', 'm0', 'm1']
    if 'n_sites' in df.columns:
        group_cols.append('n_sites')
    
    # Metric columns (numeric columns to aggregate)
    metric_cols = [c for c in df.columns if c not in group_cols + 
                   ['rep_id', 'seed', 'feasible', 'runtime_seconds', 
                    'diag_realization_id', 'diag_n_sites', 'diag_sources_selected']]
    
    # Filter to numeric columns only
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    metric_cols = [c for c in metric_cols if c in numeric_cols]
    
    # Aggregate
    agg_dict = {}
    for col in metric_cols:
        agg_dict[f'{col}_mean'] = (col, 'mean')
        agg_dict[f'{col}_sd'] = (col, 'std')
    
    # Count replications
    agg_dict['n_reps'] = ('rep_id', 'count')
    
    # Group and aggregate
    agg_df = df.groupby(group_cols, as_index=False).agg(**agg_dict)
    
    return agg_df


# =============================================================================
# IHDP SCENARIO GENERATOR
# =============================================================================

def generate_ihdp_scenarios(config: dict) -> List[Scenario]:
    """
    Generate scenarios from IHDP sweep configuration.
    
    Similar to generate_scenarios in core_sweeps.py but handles IHDP-specific parameters.
    """
    base = config.get('base_scenario', {})
    sweep_type = config.get('sweep_type', '1d')
    
    scenarios = []
    
    if sweep_type == '1d':
        param = config['sweep_param']
        values = config['sweep_values']
        
        for v in values:
            scenario_dict = {**base, param: v}
            scenario_dict['benchmark_id'] = config['benchmark_id']
            scenarios.append(Scenario(**scenario_dict))
    
    elif sweep_type == 'grid_2d':
        param1 = config['sweep_param']
        values1 = config['sweep_values']
        param2 = config.get('sweep_param_2', 'm1')
        values2 = config.get('m1_values', config.get('secondary_values', []))
        
        for v1 in values1:
            for v2 in values2:
                scenario_dict = {**base, param1: v1, param2: v2}
                scenario_dict['benchmark_id'] = config['benchmark_id']
                scenarios.append(Scenario(**scenario_dict))
    
    elif sweep_type == '2d':
        param1 = config['sweep_param']
        values1 = config['sweep_values']
        param2 = config.get('secondary_param')
        values2 = config.get('secondary_values', [])
        
        for v1 in values1:
            for v2 in values2:
                scenario_dict = {**base, param1: v1}
                if param2:
                    scenario_dict[param2] = v2
                scenario_dict['benchmark_id'] = config['benchmark_id']
                scenarios.append(Scenario(**scenario_dict))
    
    return scenarios


# =============================================================================
# SINGLE REPLICATION RUNNER
# =============================================================================

@dataclass
class IHDPRepResult:
    """Simple result container for IHDP benchmarks."""
    scenario: Scenario
    method: str
    rep_id: int
    seed: int
    feasible: str
    metrics: Dict[str, Any]
    diagnostics: Dict[str, Any]
    runtime_seconds: float


def run_single_ihdp_replication(args: Tuple) -> List[IHDPRepResult]:
    """
    Run one replication of IHDP benchmark.
    
    Parameters
    ----------
    args : tuple
        (scenario, methods, rep_id, base_seed, verbose)
        
    Returns
    -------
    results : list of IHDPRepResult
    """
    scenario, methods, rep_id, base_seed, verbose = args
    
    # Seed for this replication
    seed = generate_seed(scenario.scenario_id, rep_id, base_seed)
    
    # Create data generator and metric computer
    data_gen = create_ihdp_data_generator()
    metric_comp = create_metric_computer()
    method_factories = create_method_factories(seed)
    
    # Generate IHDP data
    try:
        data = data_gen(scenario, seed)
    except Exception as e:
        if verbose:
            print(f"  [Rep {rep_id}] Data generation failed: {e}")
        return []
    
    results = []
    has_target_treated = data.get('has_target_treated', data.get('actual_m1', 0) > 0)
    
    for method_name in methods:
        # Check method availability
        if method_name not in method_factories:
            if verbose:
                print(f"  [Rep {rep_id}] Method {method_name} not available, skipping")
            continue
        
        # Check feasibility
        spec = get_method_spec(method_name)
        requires_treated = spec.uses_target_treated if spec else False
        if requires_treated and not has_target_treated:
            # Method requires target treated but we don't have it
            result = IHDPRepResult(
                scenario=scenario,
                method=method_name,
                rep_id=rep_id,
                seed=seed,
                feasible='INFEASIBLE_NO_TARGET_TREATED',
                metrics={},
                diagnostics={},
                runtime_seconds=0.0
            )
            results.append(result)
            continue
        
        # Run method
        start_time = time.time()
        try:
            estimator = method_factories[method_name]()
            
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
            
            # Predict on evaluation set
            X_eval = data.get('X_target_eval', data['X_target'])
            tau_pred = estimator.predict(X_eval)
            
            # Compute metrics
            metrics = metric_comp(
                tau_true=data['tau_true'],
                tau_pred=tau_pred,
                mu0_true=data.get('mu0_true'),
                mu1_true=data.get('mu1_true'),
                ate_true=data.get('ate_true')
            )
            
            runtime = time.time() - start_time
            
            # Get diagnostics if available
            diagnostics = {}
            if hasattr(estimator, 'get_diagnostics'):
                try:
                    diagnostics = estimator.get_diagnostics()
                except Exception:
                    pass
            
            # Add IHDP-specific info
            diagnostics['realization_id'] = data.get('realization_id')
            diagnostics['n_sites'] = data.get('n_sites')
            
            result = IHDPRepResult(
                scenario=scenario,
                method=method_name,
                rep_id=rep_id,
                seed=seed,
                feasible='FEASIBLE',
                metrics=metrics,
                diagnostics=diagnostics,
                runtime_seconds=runtime
            )
            
        except Exception as e:
            if verbose:
                print(f"  [Rep {rep_id}] {method_name} failed: {e}")
            runtime = time.time() - start_time
            result = IHDPRepResult(
                scenario=scenario,
                method=method_name,
                rep_id=rep_id,
                seed=seed,
                feasible='ERROR',
                metrics={'pehe': np.nan, 'ate_abs_err': np.nan},
                diagnostics={'error': str(e)},
                runtime_seconds=runtime
            )
        
        results.append(result)
    
    return results


# =============================================================================
# MAIN SWEEP RUNNER
# =============================================================================

def run_ihdp_sweep(
    sweep_name: str,
    n_rep: int = 50,
    n_jobs: int = 1,
    output_dir: str = 'results/ihdp',
    base_seed: int = 42,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Run IHDP sweep and save results.
    
    Parameters
    ----------
    sweep_name : str
        Name of sweep from IHDP_SWEEP_CONFIGS
    n_rep : int
        Number of replications (cycles through IHDP realizations 1-50)
    n_jobs : int
        Number of parallel jobs (-1 for all cores)
    output_dir : str
        Output directory
    base_seed : int
        Base random seed
    verbose : bool
        Print progress
        
    Returns
    -------
    df : pd.DataFrame
        Results dataframe
    """
    if sweep_name not in IHDP_SWEEP_CONFIGS:
        raise ValueError(f"Unknown sweep: {sweep_name}. Available: {list(IHDP_SWEEP_CONFIGS.keys())}")
    
    config = IHDP_SWEEP_CONFIGS[sweep_name]
    scenarios = generate_ihdp_scenarios(config)
    methods = config['methods']
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"IHDP Sweep: {sweep_name}")
        print(f"{'='*60}")
        print(f"Scenarios: {len(scenarios)}")
        print(f"Methods: {len(methods)}")
        print(f"Replications: {n_rep}")
        print(f"Total runs: {len(scenarios) * len(methods) * n_rep}")
        print(f"Output: {output_dir}")
        print(f"{'='*60}\n")
    
    # Prepare tasks
    tasks = []
    for scenario in scenarios:
        for rep_id in range(n_rep):
            tasks.append((scenario, methods, rep_id, base_seed, False))
    
    # Run tasks
    all_results = []
    
    if n_jobs == 1:
        # Sequential execution
        for task in tqdm(tasks, desc=f"Running {sweep_name}", disable=not verbose):
            results = run_single_ihdp_replication(task)
            all_results.extend(results)
    else:
        # Parallel execution
        if n_jobs == -1:
            n_jobs = multiprocessing.cpu_count()
        
        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            futures = [executor.submit(run_single_ihdp_replication, task) for task in tasks]
            
            for future in tqdm(as_completed(futures), total=len(futures), 
                             desc=f"Running {sweep_name}", disable=not verbose):
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    if verbose:
                        print(f"Task failed: {e}")
    
    # Convert to DataFrame
    records = []
    for r in all_results:
        record = {
            'benchmark_id': r.scenario.benchmark_id,
            'method': r.method,
            'rep_id': r.rep_id,
            'seed': r.seed,
            'feasible': r.feasible.value if hasattr(r.feasible, 'value') else r.feasible,
            'runtime_seconds': r.runtime_seconds,
            'm0': r.scenario.m0,
            'm1': r.scenario.m1,
        }
        
        # Add IHDP-specific scenario params
        if hasattr(r.scenario, 'n_sites') and r.scenario.n_sites is not None:
            record['n_sites'] = r.scenario.n_sites
        
        # Add metrics
        for k, v in r.metrics.items():
            record[k] = v
        
        # Add select diagnostics
        if r.diagnostics:
            for k in ['realization_id', 'n_sites', 'sources_selected']:
                if k in r.diagnostics:
                    record[f'diag_{k}'] = r.diagnostics[k]
        
        records.append(record)
    
    df = pd.DataFrame(records)
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    benchmark_id = config['benchmark_id']
    
    # Save raw results
    csv_path = os.path.join(output_dir, f'results_rep_{benchmark_id}.csv')
    df.to_csv(csv_path, index=False)
    if verbose:
        print(f"\nSaved raw results to: {csv_path}")
    
    # Aggregate and save
    try:
        agg_df = _aggregate_ihdp_results(df)
        agg_path = os.path.join(output_dir, f'results_agg_{benchmark_id}.csv')
        agg_df.to_csv(agg_path, index=False)
        if verbose:
            print(f"Saved aggregated results to: {agg_path}")
    except Exception as e:
        if verbose:
            print(f"Aggregation failed: {e}")
            import traceback
            traceback.print_exc()
    
    return df


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='Run IHDP semi-synthetic sweeps')
    parser.add_argument('--sweep', type=str, default='all',
                       help=f'Sweep to run: {list(IHDP_SWEEP_CONFIGS.keys())} or "all"')
    parser.add_argument('--n_rep', type=int, default=50,
                       help='Number of replications (default: 50, cycles through IHDP realizations)')
    parser.add_argument('--n_jobs', type=int, default=1,
                       help='Number of parallel jobs (-1 for all cores)')
    parser.add_argument('--output', type=str, default='results/ihdp',
                       help='Output directory')
    parser.add_argument('--seed', type=int, default=42,
                       help='Base random seed')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress progress output')
    
    args = parser.parse_args()
    
    if args.sweep == 'all':
        sweeps = list(IHDP_SWEEP_CONFIGS.keys())
    else:
        sweeps = [args.sweep]
    
    for sweep in sweeps:
        run_ihdp_sweep(
            sweep_name=sweep,
            n_rep=args.n_rep,
            n_jobs=args.n_jobs,
            output_dir=args.output,
            base_seed=args.seed,
            verbose=not args.quiet
        )
    
    print("\nDone!")


if __name__ == '__main__':
    main()
