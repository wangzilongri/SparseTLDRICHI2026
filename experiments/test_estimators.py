"""
Quick test of all estimators without visualization.
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
from synthetic_data import generate_synthetic_rct
from estimator import PlaceboAnchoredDRLearner
from ablations import NoTransferBaseline, ProxyOnlyBaseline, AnchorOnlyBaseline
from metrics import evaluate_cate_model, compare_methods


def test_all_estimators():
    """Test all four estimators on single dataset."""
    print("=" * 80)
    print("TESTING ALL ESTIMATORS")
    print("=" * 80)
    
    # Generate data
    print("\nGenerating synthetic data...")
    source, target, gen = generate_synthetic_rct(
        n_source_sites=3,
        n_target=200,
        n_source_per_site=500,
        random_state=42
    )
    
    X_source = source['X']
    A_source = source['A']
    Y_source = source['Y']
    c_source = source['c']
    
    X_target = target['X']
    A_target = target['A']
    Y_target = target['Y']
    tau_target = target['tau_true']
    mu0_target = target['mu0_true']
    mu1_target = target['mu1_true']
    
    print(f"Source: {len(X_source)} samples from 3 sites")
    print(f"Target: {len(X_target)} samples")
    
    results = {}
    
    # =========================================================================
    # 1. No-Transfer
    # =========================================================================
    print("\n" + "-" * 80)
    print("1. Testing No-Transfer Baseline...")
    print("-" * 80)
    
    try:
        no_transfer = NoTransferBaseline(random_state=42)
        no_transfer.fit(X_source, A_source, Y_source, c_source,
                        X_target, A_target, Y_target)
        
        results['No-Transfer'] = evaluate_cate_model(
            no_transfer, X_target, tau_target
        )
        print(f"✓ No-Transfer: PEHE={results['No-Transfer']['pehe']:.4f}, ATE Error={results['No-Transfer']['ate_error']:.4f}")
    except Exception as e:
        print(f"✗ No-Transfer failed: {e}")
    
    # =========================================================================
    # 2. Proxy-Only
    # =========================================================================
    print("\n" + "-" * 80)
    print("2. Testing Proxy-Only Baseline...")
    print("-" * 80)
    
    try:
        proxy_only = ProxyOnlyBaseline(random_state=42)
        proxy_only.fit(X_source, A_source, Y_source, c_source,
                       X_target, A_target, Y_target)
        
        results['Proxy-Only'] = evaluate_cate_model(
            proxy_only, X_target, tau_target,
            mu0_target, mu1_target, compute_calibration=True
        )
        print(f"✓ Proxy-Only: PEHE={results['Proxy-Only']['pehe']:.4f}, ATE Error={results['Proxy-Only']['ate_error']:.4f}")
        if 'mu0_rmse' in results['Proxy-Only']:
            print(f"             μ₀ RMSE={results['Proxy-Only']['mu0_rmse']:.4f}, μ₁ RMSE={results['Proxy-Only']['mu1_rmse']:.4f}")
    except Exception as e:
        print(f"✗ Proxy-Only failed: {e}")
    
    # =========================================================================
    # 3. Anchor-Only
    # =========================================================================
    print("\n" + "-" * 80)
    print("3. Testing Anchor-Only Baseline...")
    print("-" * 80)
    
    try:
        anchor_only = AnchorOnlyBaseline(option='A', random_state=42)
        anchor_only.fit(X_source, A_source, Y_source, c_source,
                        X_target, A_target, Y_target)
        
        results['Anchor-Only'] = evaluate_cate_model(
            anchor_only, X_target, tau_target,
            mu0_target, mu1_target, compute_calibration=True
        )
        print(f"✓ Anchor-Only: PEHE={results['Anchor-Only']['pehe']:.4f}, ATE Error={results['Anchor-Only']['ate_error']:.4f}")
        if 'mu0_rmse' in results['Anchor-Only']:
            print(f"               μ₀ RMSE={results['Anchor-Only']['mu0_rmse']:.4f}, μ₁ RMSE={results['Anchor-Only']['mu1_rmse']:.4f}")
    except Exception as e:
        print(f"✗ Anchor-Only failed: {e}")
    
    # =========================================================================
    # 4. Proposed (Full)
    # =========================================================================
    print("\n" + "-" * 80)
    print("4. Testing Proposed Method (Full)...")
    print("-" * 80)
    
    try:
        proposed = PlaceboAnchoredDRLearner(option='A', random_state=42, verbose=True)
        proposed.fit(X_source, A_source, Y_source, c_source,
                     X_target, A_target, Y_target)
        
        results['Proposed'] = evaluate_cate_model(
            proposed, X_target, tau_target,
            mu0_target, mu1_target, compute_calibration=True
        )
        print(f"✓ Proposed: PEHE={results['Proposed']['pehe']:.4f}, ATE Error={results['Proposed']['ate_error']:.4f}")
        if 'mu0_rmse' in results['Proposed']:
            print(f"           μ₀ RMSE={results['Proposed']['mu0_rmse']:.4f}, μ₁ RMSE={results['Proposed']['mu1_rmse']:.4f}")
    except Exception as e:
        print(f"✗ Proposed failed: {e}")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    
    if results:
        compare_methods(results)
    else:
        print("No results to compare.")
    
    return results


if __name__ == '__main__':
    results = test_all_estimators()
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS COMPLETE")
    print("=" * 80)
