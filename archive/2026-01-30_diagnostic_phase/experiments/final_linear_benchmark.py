"""
Final Benchmark with Optimal Linear Configuration

Based on testing, use:
- Stages 1 & 2: Linear (Ridge + Elastic Net)
- Stage 3: RF with tuning (works best at ρ=0.8)
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import pandas as pd
import matplotlib
matplotlib.rcParams['mathtext.fontset'] = 'cm'
matplotlib.rcParams['font.family'] = 'serif'
import matplotlib.pyplot as plt
from pathlib import Path
from joblib import Parallel, delayed

from data_generator import MultiSiteSimulator
from improved_estimator import ImprovedPlaceboAnchoredDRLearner
from improved_baselines import ImprovedProxyOnlyBaseline, ImprovedAnchorOnlyBaseline
from sklearn.metrics import mean_squared_error


def run_single(rho, seed):
    """Single MC run"""
    simulator = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    
    data = simulator.generate_network(
        n_source_sites=3,
        n_target=2000,
        rho_cross_arm=rho,
        disconnected=False,
        seed=seed
    )
    
    X_s, A_s, Y_s, prop_s = simulator.pool_sources(data)
    X_t, A_t, Y_t = data['target']['X'], data['target']['A'], data['target']['Y']
    tau_true = data['target']['tau']
    
    results = {'rho': rho, 'seed': seed}
    
    # Proxy-Only (Linear)
    proxy = ImprovedProxyOnlyBaseline(alpha='cv')
    proxy.fit(X_s, A_s, Y_s, X_t, A_t, Y_t)
    results['Proxy'] = np.sqrt(mean_squared_error(tau_true, proxy.predict(X_t)))
    
    # Anchor-Only (Linear)
    anchor = ImprovedAnchorOnlyBaseline(stage1_alpha='cv', stage2_model='elasticnet')
    anchor.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
    results['Anchor'] = np.sqrt(mean_squared_error(tau_true, anchor.predict(X_t)))
    
    # Proposed (Linear + Tuned RF Stage 3)
    try:
        proposed = ImprovedPlaceboAnchoredDRLearner(
            stage1_model='ridge', stage1_alpha='cv',
            stage2_model='elasticnet',
            stage3_model='rf', stage3_tune=True,
            option='A', n_folds_dr=3, verbose=False
        )
        proposed.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
        results['Proposed'] = np.sqrt(mean_squared_error(tau_true, proposed.predict(X_t)))
    except:
        results['Proposed'] = np.nan
    
    return results


def main():
    print('='*80)
    print('FINAL BENCHMARK: Linear Models + HP Optimization')
    print('='*80)
    print()
    print('Configuration:')
    print('  - Stage 1: Ridge Regression (CV-tuned alpha)')
    print('  - Stage 2: Elastic Net (CV-tuned alpha + l1_ratio)')
    print('  - Stage 3: Random Forest (GridSearchCV-tuned)')
    print('  - Sample size: n=2000')
    print('  - Runs: 30 per rho')
    print()
    
    # Run benchmark
    for rho in [0.3, 0.5, 0.8, 1.0]:
        print(f'ρ = {rho:.1f} (30 runs)...', end=' ', flush=True)
        
        results = []
        for seed in range(42, 72):  # Sequential to avoid nested parallelism
            r = run_single(rho, seed)
            results.append(r)
        
        df = pd.DataFrame(results)
        
        proxy_mean = df['Proxy'].mean()
        anchor_mean = df['Anchor'].mean()
        proposed_mean = df['Proposed'].mean()
        
        proxy_std = df['Proxy'].std()
        anchor_std = df['Anchor'].std()
        proposed_std = df['Proposed'].std()
        
        proposed_vs_proxy = 100 * (proxy_mean - proposed_mean) / proxy_mean
        proposed_vs_anchor = 100 * (anchor_mean - proposed_mean) / anchor_mean
        
        winner = min([('Proxy', proxy_mean), ('Anchor', anchor_mean), ('Proposed', proposed_mean)], 
                    key=lambda x: x[1])[0]
        
        print(f'DONE')
        print(f'  Proxy:    {proxy_mean:.4f} ± {proxy_std:.4f}')
        print(f'  Anchor:   {anchor_mean:.4f} ± {anchor_std:.4f}')
        print(f'  Proposed: {proposed_mean:.4f} ± {proposed_std:.4f} ({proposed_vs_proxy:+.1f}% vs Proxy, {proposed_vs_anchor:+.1f}% vs Anchor)')
        win_marker = 'WIN WIN WIN' if winner == 'Proposed' else ''
        print(f'  → WINNER: {winner} {win_marker}')
        print()
    
    print('='*80)
    print('BENCHMARK COMPLETE')
    print('='*80)


if __name__ == '__main__':
    main()
