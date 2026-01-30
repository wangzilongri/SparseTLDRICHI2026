"""
Test script for improved linear estimators with hyperparameter optimization

Demonstrates the new features:
1. Linear regression for Stages 1 & 2
2. Automatic hyperparameter selection
3. Comparison with original RF-based estimators
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

# Import data generator
from data_generator import MultiSiteSimulator

# Import improved estimators
from improved_estimator import ImprovedPlaceboAnchoredDRLearner
from improved_baselines import ImprovedProxyOnlyBaseline, ImprovedAnchorOnlyBaseline, NoTransferBaseline

# Import original estimators for comparison
from scratch_estimator import PlaceboAnchoredDRLearner
from baselines import ProxyOnlyBaseline, AnchorOnlyBaseline


def test_single_run():
    """Test improved estimators on a single data instance"""
    
    print("="*80)
    print("TESTING IMPROVED LINEAR ESTIMATORS")
    print("="*80)
    print()
    
    # Generate data
    print("Generating synthetic data...")
    simulator = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    data = simulator.generate_network(
        n_source_sites=3,
        n_target=2000,
        rho_cross_arm=0.8,
        disconnected=False,
        seed=42
    )
    
    X_s, A_s, Y_s, prop_s = simulator.pool_sources(data)
    X_t = data['target']['X']
    A_t = data['target']['A']
    Y_t = data['target']['Y']
    tau_true = data['target']['tau']
    mu0_true = data['target']['mu_0']
    mu1_true = data['target']['mu_1']
    
    print(f"Source: {len(X_s)} samples")
    print(f"Target: {len(X_t)} samples (ρ=0.8)")
    print()
    
    # Test improved estimators
    print("-"*80)
    print("IMPROVED ESTIMATORS (Linear Stages + HP Optimization)")
    print("-"*80)
    print()
    
    # Proxy-Only (Linear)
    print("1. Improved Proxy-Only (Ridge with CV)...")
    proxy_improved = ImprovedProxyOnlyBaseline(alpha='cv')
    proxy_improved.fit(X_s, A_s, Y_s, X_t, A_t, Y_t)
    tau_pred_proxy_improved = proxy_improved.predict(X_t)
    pehe_proxy_improved = np.sqrt(mean_squared_error(tau_true, tau_pred_proxy_improved))
    print(f"   PEHE: {pehe_proxy_improved:.4f}")
    print()
    
    # Anchor-Only (Linear)
    print("2. Improved Anchor-Only (Ridge + Elastic Net CV)...")
    anchor_improved = ImprovedAnchorOnlyBaseline(
        stage1_alpha='cv',
        stage2_model='elasticnet'
    )
    anchor_improved.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
    tau_pred_anchor_improved = anchor_improved.predict(X_t)
    pehe_anchor_improved = np.sqrt(mean_squared_error(tau_true, tau_pred_anchor_improved))
    print(f"   PEHE: {pehe_anchor_improved:.4f}")
    print()
    
    # Proposed (Linear with HP tuning)
    print("3. Improved Proposed (Linear + HP Optimization, verbose=True)...")
    proposed_improved = ImprovedPlaceboAnchoredDRLearner(
        stage1_model='ridge',
        stage1_alpha='cv',
        stage2_model='elasticnet',
        stage3_model='rf',
        stage3_tune=True,
        stage3_cv_folds=3,
        option='A',
        n_folds_dr=3,
        verbose=True
    )
    proposed_improved.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
    tau_pred_proposed_improved = proposed_improved.predict(X_t)
    pehe_proposed_improved = np.sqrt(mean_squared_error(tau_true, tau_pred_proposed_improved))
    print(f"   PEHE: {pehe_proposed_improved:.4f}")
    print()
    
    # Compare with original RF-based estimators
    print("-"*80)
    print("ORIGINAL ESTIMATORS (Random Forest, No HP Optimization)")
    print("-"*80)
    print()
    
    from sklearn.ensemble import RandomForestRegressor
    
    # Proxy-Only (RF)
    print("4. Original Proxy-Only (Random Forest)...")
    proxy_original = ProxyOnlyBaseline(proxy_model=RandomForestRegressor(
        n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=42, n_jobs=1
    ))
    proxy_original.fit(X_s, A_s, Y_s, X_t, A_t, Y_t)
    tau_pred_proxy_original = proxy_original.predict(X_t)
    pehe_proxy_original = np.sqrt(mean_squared_error(tau_true, tau_pred_proxy_original))
    print(f"   PEHE: {pehe_proxy_original:.4f}")
    print()
    
    # Anchor-Only (RF)
    print("5. Original Anchor-Only (Random Forest + LASSO)...")
    anchor_original = AnchorOnlyBaseline(proxy_model=RandomForestRegressor(
        n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=42, n_jobs=1
    ))
    anchor_original.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
    tau_pred_anchor_original = anchor_original.predict(X_t)
    pehe_anchor_original = np.sqrt(mean_squared_error(tau_true, tau_pred_anchor_original))
    print(f"   PEHE: {pehe_anchor_original:.4f}")
    print()
    
    # Proposed (RF)
    print("6. Original Proposed (Random Forest, No Tuning)...")
    proposed_original = PlaceboAnchoredDRLearner(
        proxy_model=RandomForestRegressor(
            n_estimators=200, max_depth=8, min_samples_leaf=20, random_state=42, n_jobs=1
        ),
        cate_model=RandomForestRegressor(
            n_estimators=200, max_depth=5, min_samples_leaf=10, random_state=43, n_jobs=1
        ),
        option='A',
        n_folds_dr=3,
        random_state=42,
        verbose=False
    )
    proposed_original.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
    tau_pred_proposed_original = proposed_original.predict(X_t)
    pehe_proposed_original = np.sqrt(mean_squared_error(tau_true, tau_pred_proposed_original))
    print(f"   PEHE: {pehe_proposed_original:.4f}")
    print()
    
    # Summary comparison
    print("="*80)
    print("SUMMARY COMPARISON")
    print("="*80)
    print()
    
    results = pd.DataFrame({
        'Method': [
            'Proxy-Only (Improved-Linear)',
            'Proxy-Only (Original-RF)',
            'Anchor-Only (Improved-Linear)',
            'Anchor-Only (Original-RF)',
            'Proposed (Improved-Linear+HP)',
            'Proposed (Original-RF)'
        ],
        'PEHE': [
            pehe_proxy_improved,
            pehe_proxy_original,
            pehe_anchor_improved,
            pehe_anchor_original,
            pehe_proposed_improved,
            pehe_proposed_original
        ],
        'Type': [
            'Improved',
            'Original',
            'Improved',
            'Original',
            'Improved',
            'Original'
        ]
    })
    
    results['Relative_Performance'] = (results['PEHE'].min() / results['PEHE']) * 100
    
    print(results.to_string(index=False))
    print()
    
    # Identify winner
    winner_idx = results['PEHE'].idxmin()
    winner = results.loc[winner_idx, 'Method']
    winner_pehe = results.loc[winner_idx, 'PEHE']
    
    print(f"WINNER: {winner} (PEHE = {winner_pehe:.4f})")
    print()
    
    # Save results
    results.to_csv('results/improved_estimators_test.csv', index=False)
    print("Results saved to: results/improved_estimators_test.csv")


def test_hyperparameter_sensitivity():
    """Test different Stage 3 models and hyperparameter configurations"""
    
    print("\n" + "="*80)
    print("HYPERPARAMETER SENSITIVITY ANALYSIS")
    print("="*80)
    print()
    
    simulator = MultiSiteSimulator(n_features=10, n_effect_modifiers=3)
    data = simulator.generate_network(
        n_source_sites=3,
        n_target=2000,
        rho_cross_arm=1.0,  # Shared bias regime where Proposed should excel
        disconnected=False,
        seed=42
    )
    
    X_s, A_s, Y_s, prop_s = simulator.pool_sources(data)
    X_t, A_t, Y_t = data['target']['X'], data['target']['A'], data['target']['Y']
    tau_true = data['target']['tau']
    
    configs = [
        {'name': 'RF (default)', 'stage3_model': 'rf', 'stage3_tune': False},
        {'name': 'RF (tuned)', 'stage3_model': 'rf', 'stage3_tune': True},
        {'name': 'GBM (default)', 'stage3_model': 'gbm', 'stage3_tune': False},
        {'name': 'GBM (tuned)', 'stage3_model': 'gbm', 'stage3_tune': True},
        {'name': 'Ridge (tuned)', 'stage3_model': 'ridge', 'stage3_tune': True},
    ]
    
    results = []
    
    for config in configs:
        print(f"Testing: {config['name']}...", end=' ', flush=True)
        
        model = ImprovedPlaceboAnchoredDRLearner(
            stage1_model='ridge',
            stage1_alpha='cv',
            stage2_model='elasticnet',
            stage3_model=config['stage3_model'],
            stage3_tune=config['stage3_tune'],
            stage3_cv_folds=3,
            option='A',
            n_folds_dr=3,
            verbose=False
        )
        
        model.fit(X_s, A_s, Y_s, X_t, A_t, Y_t, prop_s, data['target']['propensity'])
        tau_pred = model.predict(X_t)
        pehe = np.sqrt(mean_squared_error(tau_true, tau_pred))
        
        results.append({
            'Configuration': config['name'],
            'PEHE': pehe
        })
        
        print(f"PEHE = {pehe:.4f}")
    
    df = pd.DataFrame(results)
    print("\nSummary:")
    print(df.to_string(index=False))
    
    return df


if __name__ == "__main__":
    # Test 1: Single run comparison
    test_single_run()
    
    # Test 2: Hyperparameter sensitivity
    # test_hyperparameter_sensitivity()  # Uncomment to run
