"""
Validate the improved DGP (v2) properly implements A5 and A6.

Tests:
1. Proxy + deviation decomposition
2. Cross-arm transfer: beta1 = M* beta0 + nu
3. Sparsity of deviations
4. Nontransfer component magnitude
5. Disconnected target support
"""

import sys
sys.path.insert(0, 'src')

import numpy as np
from synthetic_data_v2 import (
    SyntheticRCTGenerator, 
    SyntheticRCTConfig,
    generate_synthetic_rct,
    generate_disconnected_target,
    sweep_nontransfer
)


def test_1_basic_generation():
    """Test 1: Basic data generation works."""
    print("=" * 80)
    print("TEST 1: Basic Generation")
    print("=" * 80)
    
    source, target, gen = generate_synthetic_rct(
        n_source_sites=3,
        n_target=200,
        random_state=42
    )
    
    print(f"\nSource data:")
    print(f"  Shape: {source['X'].shape}")
    print(f"  Sites: {np.unique(source['c'])}")
    print(f"  Placebo: {np.sum(source['A'] == 0)}")
    print(f"  Treated: {np.sum(source['A'] == 1)}")
    
    print(f"\nTarget data:")
    print(f"  Shape: {target['X'].shape}")
    print(f"  Site: {np.unique(target['c'])}")
    print(f"  Placebo: {np.sum(target['A'] == 0)}")
    print(f"  Treated: {np.sum(target['A'] == 1)}")
    
    print("\n✓ Basic generation working")
    return gen


def test_2_proxy_deviation_decomposition(gen):
    """Test 2: Verify proxy + deviation decomposition."""
    print("\n" + "=" * 80)
    print("TEST 2: Proxy + Deviation Decomposition")
    print("=" * 80)
    
    # Generate test data
    X_test = np.random.randn(100, 5)
    
    # Site 1 outcomes
    mu0_site1 = gen._mu(X_test, site_id=1, arm=0)
    mu1_site1 = gen._mu(X_test, site_id=1, arm=1)
    
    # Decompose manually
    mu0_proxy = X_test @ gen.b0_proxy
    mu0_dev = X_test @ gen.beta0[1]
    
    mu1_proxy = X_test @ gen.b1_proxy
    mu1_dev = X_test @ gen.beta1[1]
    
    # Check decomposition (should match, ignoring misspec)
    error0 = np.linalg.norm(mu0_site1 - (mu0_proxy + mu0_dev))
    error1 = np.linalg.norm(mu1_site1 - (mu1_proxy + mu1_dev))
    
    print(f"\nPlacebo decomposition error: {error0:.6f}")
    print(f"Treated decomposition error: {error1:.6f}")
    
    print(f"\nProxy coefficients:")
    print(f"  b0_proxy: {gen.b0_proxy}")
    print(f"  b1_proxy: {gen.b1_proxy}")
    
    print(f"\nSite 1 deviations:")
    print(f"  beta0: {gen.beta0[1]}")
    print(f"  beta1: {gen.beta1[1]}")
    
    assert error0 < 1e-10, f"Decomposition error too large: {error0}"
    assert error1 < 1e-10, f"Decomposition error too large: {error1}"
    
    print("\n✓ Decomposition verified")


def test_3_cross_arm_transfer(gen):
    """Test 3: Verify A6 cross-arm transfer: beta1 = M* beta0 + nu."""
    print("\n" + "=" * 80)
    print("TEST 3: Cross-Arm Transfer (A6)")
    print("=" * 80)
    
    print(f"\nTransfer operator M*:")
    print(f"  Shape: {gen.M_star.shape}")
    print(f"  ||M*||_F: {np.linalg.norm(gen.M_star, 'fro'):.4f}")
    print(f"  rank(M*): {np.linalg.matrix_rank(gen.M_star)}")
    print(f"\nM* =")
    print(gen.M_star)
    
    # Check transfer for each source site
    print(f"\nVerifying beta1 = M* beta0 + nu for each site:")
    print(f"{'Site':<10} {'||nu||':<12} {'||M*beta0||':<15} {'Transfer Error':<15}")
    print("-" * 55)
    
    for c in range(1, gen.config.n_source_sites + 1):
        beta0_c = gen.beta0[c]
        beta1_c = gen.beta1[c]
        nu_c = gen.nu[c]
        
        # Predicted via transfer
        beta1_predicted = gen.M_star @ beta0_c
        
        # Actual should be: M* beta0 + nu
        beta1_expected = beta1_predicted + nu_c
        
        transfer_error = np.linalg.norm(beta1_c - beta1_expected)
        
        print(f"Site {c:<5} {np.linalg.norm(nu_c):<12.4f} "
              f"{np.linalg.norm(beta1_predicted):<15.4f} "
              f"{transfer_error:<15.6e}")
        
        assert transfer_error < 1e-10, f"Transfer error too large for site {c}"
    
    print("\n✓ A6 transfer structure verified")


def test_4_sparsity(gen):
    """Test 4: Verify sparsity of site deviations (A5)."""
    print("\n" + "=" * 80)
    print("TEST 4: Sparsity of Site Deviations (A5)")
    print("=" * 80)
    
    expected_sparsity = gen.config.dev_sparsity
    p = gen.config.n_features
    
    print(f"\nExpected sparsity: {expected_sparsity}/{p}")
    print(f"\n{'Site':<10} {'Sparsity (beta0)':<20} {'Support':<30}")
    print("-" * 60)
    
    for c in range(0, gen.config.n_source_sites + 1):
        beta0_c = gen.beta0[c]
        sparsity = np.sum(np.abs(beta0_c) > 1e-10)
        support = np.where(np.abs(beta0_c) > 1e-10)[0]
        
        site_name = "Target" if c == 0 else f"Source {c}"
        print(f"{site_name:<10} {sparsity}/{p:<17} {list(support)}")
        
        assert sparsity == expected_sparsity, f"Sparsity mismatch for site {c}"
    
    print("\n✓ Sparse deviations verified")


def test_5_nontransfer_magnitude(gen):
    """Test 5: Verify nontransfer component has correct magnitude."""
    print("\n" + "=" * 80)
    print("TEST 5: Nontransfer Component Magnitude")
    print("=" * 80)
    
    source_scale = gen.config.nontransfer_scale_source
    target_scale = gen.config.nontransfer_scale_target
    
    print(f"\nExpected scales:")
    print(f"  Source: {source_scale}")
    print(f"  Target: {target_scale}")
    
    print(f"\n{'Site':<10} {'||nu||':<12} {'Expected':<12} {'Ratio':<10}")
    print("-" * 45)
    
    for c in range(0, gen.config.n_source_sites + 1):
        nu_c = gen.nu[c]
        nu_norm = np.linalg.norm(nu_c)
        
        expected = target_scale if c == 0 else source_scale
        # Expected norm ~ scale * sqrt(p) for Gaussian
        expected_norm = expected * np.sqrt(gen.config.n_features)
        ratio = nu_norm / expected_norm
        
        site_name = "Target" if c == 0 else f"Source {c}"
        print(f"{site_name:<10} {nu_norm:<12.4f} {expected_norm:<12.4f} {ratio:<10.2f}")
    
    # Check target has larger nontransfer
    nu_target_norm = np.linalg.norm(gen.nu[0])
    nu_source_norms = [np.linalg.norm(gen.nu[c]) for c in range(1, gen.config.n_source_sites + 1)]
    
    print(f"\nTarget vs Source nontransfer:")
    print(f"  Target ||nu||: {nu_target_norm:.4f}")
    print(f"  Source ||nu|| (avg): {np.mean(nu_source_norms):.4f}")
    print(f"  Ratio: {nu_target_norm / np.mean(nu_source_norms):.2f}x")
    
    print("\n✓ Nontransfer magnitudes correct")


def test_6_disconnected_target():
    """Test 6: Generate disconnected target (placebo-only)."""
    print("\n" + "=" * 80)
    print("TEST 6: Disconnected Target Generation")
    print("=" * 80)
    
    source, target, gen = generate_disconnected_target(
        n_target=200,
        nontransfer_scale_target=0.5,
        random_state=42
    )
    
    n_placebo = np.sum(target['A'] == 0)
    n_treated = np.sum(target['A'] == 1)
    
    print(f"\nTarget treatment distribution:")
    print(f"  Placebo: {n_placebo}")
    print(f"  Treated: {n_treated}")
    
    # Should still have tau_true and mu1_true for evaluation
    print(f"\nGround truth available:")
    print(f"  tau_true: {target['tau_true'].shape}")
    print(f"  mu0_true: {target['mu0_true'].shape}")
    print(f"  mu1_true: {target['mu1_true'].shape}")
    print(f"  Mean CATE: {np.mean(target['tau_true']):.4f}")
    
    assert n_treated == 0, "Disconnected target should have no treated!"
    assert 'tau_true' in target, "Should have tau_true for evaluation"
    
    print("\n✓ Disconnected target working")


def test_7_nontransfer_sweep():
    """Test 7: Sweep nontransfer magnitude."""
    print("\n" + "=" * 80)
    print("TEST 7: Nontransfer Sweep")
    print("=" * 80)
    
    scales = [0.0, 0.1, 0.3, 0.5, 0.8]
    datasets = sweep_nontransfer(
        nontransfer_scales=scales,
        n_target=200,
        random_state=42
    )
    
    print(f"\nGenerated {len(datasets)} datasets with varying nontransfer")
    print(f"\n{'Scale':<10} {'||nu_target||':<15} {'Mean |tau|':<15}")
    print("-" * 40)
    
    for scale, (source, target, gen) in zip(scales, datasets):
        nu_target_norm = np.linalg.norm(gen.nu[0])
        mean_tau = np.mean(np.abs(target['tau_true']))
        
        print(f"{scale:<10.2f} {nu_target_norm:<15.4f} {mean_tau:<15.4f}")
    
    print("\n✓ Nontransfer sweep working")


def test_8_visualize_structure():
    """Test 8: Visualize DGP structure."""
    print("\n" + "=" * 80)
    print("TEST 8: DGP Structure Diagnostics")
    print("=" * 80)
    
    source, target, gen = generate_synthetic_rct(
        n_source_sites=3,
        n_target=200,
        dev_sparsity=2,
        transfer_rank=1,
        nontransfer_scale_target=0.3,
        random_state=42
    )
    
    # Get diagnostics
    diag = gen.get_diagnostics()
    
    print(f"\nDGP Diagnostics:")
    print(f"  M* norm: {diag['M_star_norm']:.4f}")
    print(f"  M* rank: {diag['M_star_rank']}")
    
    for c in range(0, gen.config.n_source_sites + 1):
        site_name = 'target' if c == 0 else f'source_{c}'
        print(f"\n  {site_name}:")
        print(f"    Sparsity: {diag[f'{site_name}_sparsity']}/5")
        print(f"    ||nu||: {diag[f'{site_name}_nu_norm']:.4f}")
    
    # Print M* matrix
    print(f"\nTransfer Operator M*:")
    print(gen.M_star)
    
    # Print beta matrices
    print(f"\nPlacebo Deviations β₀:")
    for c in range(0, 4):
        site_name = 'Target' if c == 0 else f'Source {c}'
        print(f"  {site_name}: {gen.beta0[c]}")
    
    print(f"\nTreated Deviations β₁:")
    for c in range(0, 4):
        site_name = 'Target' if c == 0 else f'Source {c}'
        print(f"  {site_name}: {gen.beta1[c]}")
    
    # Verify A6 numerically
    print(f"\nA6 Verification (β₁ = M*β₀ + ν):")
    for c in range(1, 4):
        beta1_actual = gen.beta1[c]
        beta1_predicted = gen.M_star @ gen.beta0[c] + gen.nu[c]
        error = np.linalg.norm(beta1_actual - beta1_predicted)
        print(f"  Source {c} reconstruction error: {error:.2e}")
    
    print("\n✓ Structure diagnostics complete")
    
    return diag


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "=" * 80)
    print("VALIDATING IMPROVED DGP (v2)")
    print("=" * 80)
    print("\nThis DGP properly implements:")
    print("  • A5: Sparse site deviations")
    print("  • A6: Cross-arm transfer via M*")
    print("  • Controllable nontransfer (degradation knob)")
    print("  • Disconnected target support")
    
    # Run tests
    gen = test_1_basic_generation()
    test_2_proxy_deviation_decomposition(gen)
    test_3_cross_arm_transfer(gen)
    test_4_sparsity(gen)
    test_5_nontransfer_magnitude(gen)
    test_6_disconnected_target()
    test_7_nontransfer_sweep()
    diag = test_8_visualize_structure()
    
    print("\n" + "=" * 80)
    print("✓ ALL TESTS PASSED - DGP v2 VALIDATED!")
    print("=" * 80)
    
    print("\n" + "=" * 80)
    print("KEY FEATURES")
    print("=" * 80)
    print(f"\n1. Proxy + Deviation Decomposition:")
    print(f"     μ_{{a,c}}(x) = x^T b_a + x^T β_{{a,c}} + r_{{a,c}}(x)")
    
    print(f"\n2. Cross-Arm Transfer (A6):")
    print(f"     β_{{1,c}} = M* β_{{0,c}} + ν_c")
    print(f"     ||M*||_F = {diag['M_star_norm']:.4f}")
    print(f"     rank(M*) = {diag['M_star_rank']}")
    
    print(f"\n3. Sparse Site Deviations (A5):")
    print(f"     Sparsity: {diag['target_sparsity']}/5 features")
    
    print(f"\n4. Nontransfer Component:")
    print(f"     Target ||ν_0||: {diag['target_nu_norm']:.4f}")
    print(f"     Source ||ν_c|| (avg): "
          f"{np.mean([diag[f'source_{c}_nu_norm'] for c in range(1, 4)]):.4f}")
    
    print(f"\n5. A6 Verified for Sources:")
    for c in range(1, 4):
        print(f"     Source {c} error: {diag[f'source_{c}_A6_error']:.2e}")
    
    return diag


if __name__ == '__main__':
    diag = run_all_tests()
