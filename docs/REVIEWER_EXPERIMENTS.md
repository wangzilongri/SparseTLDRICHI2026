# Additional Experiments: Response to Reviewer SDFf

## Executive Summary

The reviewer raises important concerns about **statistical rigor**, **scope of evaluation**, and **missing comparisons**. This document specifies additional experiments beyond the current manuscript/design to address these gaps.

---

## Gap Analysis: Current vs Required

### ✅ Already Covered in DESIGN.md / ABLATION_TESTS.md

1. Core component ablations (5 methods)
2. Basic robustness checks (shift, sparsity, ρ)
3. Gold budget sweeps
4. General mention of comparative baselines

### ❌ Missing or Insufficient

1. **Monte Carlo rigor**: No explicit protocol for many runs + statistical testing
2. **Non-linear extensions**: Mentioned but not detailed (non-linear δ, non-linear DGP)
3. **Disconnected networks**: Not explicitly designed (multi-treatment scenario)
4. **Site imbalance**: Not addressed
5. **Covariate dimensionality**: Not systematically varied
6. **Comparative implementations**: IPW, AIPW, IPD-NMA not fully specified
7. **Cross-arm degradation**: Empirical sweeps exist, but no analytical validation

---

## Additional Experiments (Priority Order)

## PRIORITY 1: Statistical Rigor (Response to Q3)

### Experiment 1.1: Monte Carlo Protocol with Statistical Testing

**Problem**: Current experiments use single realizations or too few runs (n=20). Need statistical hypothesis testing.

**Design**:
```python
def monte_carlo_experiment_with_testing(
    n_runs=100,  # Increased from 20
    dgp_variants=['baseline', 'high_shift', 'dense_bias', 'low_rho'],
    methods=['No-Transfer', 'Proxy-Only', 'Proxy+DR', 'Anchor-Only', 'Proposed'],
    metrics=['PEHE', 'ATE_Error', 'Cal_RMSE_mu0', 'Cal_RMSE_mu1'],
    seed_start=1000
):
    """
    Rigorous Monte Carlo evaluation with statistical testing.
    
    For each DGP variant:
    1. Generate n_runs independent datasets
    2. Fit all methods on each dataset
    3. Compute all metrics
    4. Aggregate: mean, std, median, IQR, min, max
    5. Statistical tests:
       - Friedman test (methods as treatments, metrics as blocks)
       - Wilcoxon signed-rank pairwise tests with Bonferroni correction
       - Effect sizes (Cohen's d)
    
    Returns:
    --------
    results : DataFrame with columns
        ['DGP', 'Method', 'Metric', 'Mean', 'Std', 'Median', 'IQR', 'Min', 'Max']
    statistical_tests : dict with
        - friedman_statistic, friedman_pvalue
        - posthoc_pairwise: DataFrame of pairwise comparisons
        - effect_sizes: DataFrame of Cohen's d
    """
    results = []
    
    for dgp_name in dgp_variants:
        dgp_config = get_dgp_config(dgp_name)
        
        for run in range(n_runs):
            data = generate_data(**dgp_config, seed=seed_start + run)
            
            for method_name in methods:
                model = get_model(method_name)
                model.fit(data)
                
                for metric_name in metrics:
                    value = evaluate_metric(model, data, metric_name)
                    results.append({
                        'DGP': dgp_name,
                        'Run': run,
                        'Method': method_name,
                        'Metric': metric_name,
                        'Value': value
                    })
    
    df = pd.DataFrame(results)
    
    # Statistical testing
    statistical_tests = perform_hypothesis_tests(df)
    
    return df, statistical_tests


def perform_hypothesis_tests(df):
    """
    Friedman test: H0: all methods perform equally
    - Methods = treatments (5 levels)
    - Metrics = blocks (4 blocks per DGP)
    - Replicates = runs (100 per DGP-method-metric combo)
    
    Post-hoc: Wilcoxon signed-rank pairwise comparisons
    """
    from scipy.stats import friedmanchisquare, wilcoxon
    from itertools import combinations
    
    tests = {}
    
    for dgp in df['DGP'].unique():
        df_dgp = df[df['DGP'] == dgp]
        
        # Friedman test (omnibus)
        method_groups = [
            df_dgp[df_dgp['Method'] == m]['Value'].values 
            for m in df['Method'].unique()
        ]
        stat, pval = friedmanchisquare(*method_groups)
        
        tests[dgp] = {
            'friedman_stat': stat,
            'friedman_pval': pval,
            'pairwise': {}
        }
        
        # Post-hoc pairwise (if Friedman significant)
        if pval < 0.05:
            methods = df['Method'].unique()
            for m1, m2 in combinations(methods, 2):
                val1 = df_dgp[df_dgp['Method'] == m1]['Value'].values
                val2 = df_dgp[df_dgp['Method'] == m2]['Value'].values
                stat_pair, pval_pair = wilcoxon(val1, val2)
                
                # Cohen's d effect size
                cohens_d = (val1.mean() - val2.mean()) / np.sqrt(
                    (val1.std()**2 + val2.std()**2) / 2
                )
                
                tests[dgp]['pairwise'][f'{m1}_vs_{m2}'] = {
                    'statistic': stat_pair,
                    'pvalue': pval_pair,
                    'cohens_d': cohens_d
                }
    
    return tests
```

**Expected Output**:
- Table of means ± std for each method × DGP × metric
- Friedman test results: "Proposed significantly better (p < 0.001)"
- Pairwise comparisons: "Proposed vs Proxy-Only: Cohen's d = 0.85 (large effect)"

**Acceptance Criterion**: Proposed achieves statistically significant improvement (p < 0.01) over all baselines on PEHE in at least 3/4 DGP variants.

---

### Experiment 1.2: Covariate Dimensionality Sweep

**Problem**: Reviewer asks to "vary the number of covariates used"

**Design**:
```python
def covariate_dimensionality_sweep(
    p_values=[5, 10, 20, 50, 100],  # Total covariates
    p_eff_values=[2, 3, 5],          # Effect modifiers
    s_bias_values=[2, 3, 5],         # Bias sparsity
    n_runs=50
):
    """
    Sweep covariate dimensionality to test:
    1. Does Proposed maintain advantage in high dimensions?
    2. Does LASSO selection remain stable as p increases?
    3. What is the phase transition in p where anchoring fails?
    
    For each (p, p_eff, s_bias) combo:
    - Generate data with p covariates
    - p_eff are true effect modifiers
    - s_bias controls sparsity of transport bias
    - Evaluate all methods
    
    Metrics:
    - PEHE (primary)
    - Feature selection accuracy (for LASSO): precision, recall, F1
    - Computational time
    """
    results = []
    
    for p in p_values:
        for p_eff in p_eff_values:
            for s_bias in s_bias_values:
                # Skip invalid combinations
                if p_eff > p or s_bias > p:
                    continue
                
                for run in range(n_runs):
                    data = generate_data(
                        n_features=p,
                        n_effect_modifiers=p_eff,
                        bias_sparsity=s_bias,
                        seed=run
                    )
                    
                    # Fit Proposed method
                    model = PlaceboAnchoredDRLearner()
                    start = time.time()
                    model.fit(data)
                    elapsed = time.time() - start
                    
                    # Evaluate
                    pehe = compute_pehe(model, data)
                    
                    # Feature selection metrics (for LASSO)
                    selected = np.where(np.abs(model.delta_placebo_) > 1e-6)[0]
                    true_nonzero = data['true_bias_support']
                    precision = len(set(selected) & set(true_nonzero)) / len(selected) if len(selected) > 0 else 0
                    recall = len(set(selected) & set(true_nonzero)) / len(true_nonzero) if len(true_nonzero) > 0 else 0
                    
                    results.append({
                        'p': p,
                        'p_eff': p_eff,
                        's_bias': s_bias,
                        'Run': run,
                        'PEHE': pehe,
                        'Precision': precision,
                        'Recall': recall,
                        'Time': elapsed
                    })
    
    return pd.DataFrame(results)
```

**Expected Findings**:
- PEHE degrades slowly as p increases (log(p) dependence due to LASSO)
- Feature selection precision remains high (> 0.8) when s_bias ≤ 5
- Computational time scales as O(p log p) due to LASSO path

**Visualization**: 3D surface plot of PEHE vs (p, s_bias) with p_eff fixed

---

## PRIORITY 2: Non-Linear Extensions (Response to Q5)

### Experiment 2.1: Non-Linear Transport Bias

**Problem**: "The model constrains bias term to be linear and sparse, which is restrictive"

**Design**:
```python
def nonlinear_bias_experiment(
    bias_forms=['linear', 'quadratic', 'interactions', 'piecewise', 'sigmoid'],
    correction_methods=['LASSO', 'Ridge', 'KernelRidge', 'RandomForest', 'Splines'],
    n_runs=50
):
    """
    Test performance when true transport bias is non-linear.
    
    DGPs:
    ------
    1. Linear: δ(x) = β'x (current assumption)
    2. Quadratic: δ(x) = β'x + γ'(x ⊙ x)
    3. Interactions: δ(x) = β'x + Σᵢⱼ θᵢⱼ xᵢxⱼ (2-way)
    4. Piecewise: δ(x) = β₁'x if x₁>0 else β₂'x
    5. Sigmoid: δ(x) = 1/(1 + exp(-β'x))
    
    Correction methods:
    -------------------
    1. LASSO: δ̂ = argmin ||y - X'β||² + λ||β||₁ (current)
    2. Ridge: δ̂ = argmin ||y - X'β||² + λ||β||²₂
    3. KernelRidge: δ̂ with RBF kernel (captures non-linearity)
    4. RandomForest: δ̂ = RF(X) (non-linear, non-parametric)
    5. Splines: δ̂ with natural cubic splines
    
    Research Questions:
    -------------------
    Q1: How much does LASSO degrade under non-linear bias?
    Q2: Do flexible corrections (RF, KernelRidge) help?
    Q3: Is there a bias-variance tradeoff (flexible = higher variance)?
    """
    results = []
    
    for bias_form in bias_forms:
        dgp = NonLinearBiasDGP(bias_form=bias_form)
        
        for correction in correction_methods:
            for run in range(n_runs):
                data = dgp.generate(seed=run)
                
                # Fit model with specified correction method
                model = PlaceboAnchoredDRLearner(
                    correction_method=correction
                )
                model.fit(data)
                
                # Evaluate
                pehe = compute_pehe(model, data)
                cal_mu0 = compute_calibration_rmse(model, data, arm=0)
                
                # Bias decomposition: how much is due to Stage 2?
                proxy_only_pehe = compute_pehe_proxy_only(model, data)
                stage2_improvement = proxy_only_pehe - pehe
                
                results.append({
                    'BiasForm': bias_form,
                    'Correction': correction,
                    'Run': run,
                    'PEHE': pehe,
                    'Cal_mu0': cal_mu0,
                    'Stage2_Improvement': stage2_improvement
                })
    
    return pd.DataFrame(results)
```

**Expected Findings**:
- **Linear bias**: LASSO optimal
- **Quadratic/Interactions**: Ridge/KernelRidge improve by 20-30%
- **Piecewise/Sigmoid**: RandomForest best, but higher variance
- **Key insight**: Graceful degradation - linear LASSO still helps even when wrong

**Visualization**: Heatmap of PEHE (bias_form × correction_method)

---

### Experiment 2.2: Non-Linear Outcome Models

**Problem**: Test "non-linear data-generating processes"

**Design**:
```python
def nonlinear_outcome_dgp_experiment(
    outcome_forms=['linear', 'polynomial', 'interactions', 'tree_based', 'heteroskedastic'],
    proxy_models=['Linear', 'RandomForest', 'GradientBoosting', 'NeuralNet'],
    n_runs=50
):
    """
    Test robustness to non-linear outcome models in Stage 1.
    
    DGPs:
    -----
    1. Linear: Y = β₀'X + A·βτ'X + ε
    2. Polynomial: Y = Σⱼ βⱼ Xⱼ² + A·τ(X) + ε
    3. Interactions: Y = β'X + Σᵢⱼ γᵢⱼ XᵢXⱼ + A·τ(X) + ε
    4. Tree-based: Y = T(X) + A·τ(X) + ε, where T is decision tree
    5. Heteroskedastic: Y = μ(X) + A·τ(X) + ε(X), Var(ε|X) = σ²(X)
    
    Research Questions:
    -------------------
    Q1: Does flexible Stage 1 (RF, GBM) recover from misspecification?
    Q2: Does Stage 2 correction still help when Stage 1 is wrong?
    Q3: Is there a preferred proxy model for each DGP type?
    """
    results = []
    
    for outcome_form in outcome_forms:
        dgp = NonLinearOutcomeDGP(outcome_form=outcome_form)
        
        for proxy_model in proxy_models:
            for run in range(n_runs):
                data = dgp.generate(seed=run)
                
                # Fit with specified proxy model
                model = PlaceboAnchoredDRLearner(
                    proxy_learner=get_proxy_model(proxy_model)
                )
                model.fit(data)
                
                pehe = compute_pehe(model, data)
                
                results.append({
                    'OutcomeForm': outcome_form,
                    'ProxyModel': proxy_model,
                    'Run': run,
                    'PEHE': pehe
                })
    
    return pd.DataFrame(results)
```

**Expected Findings**:
- Linear proxy fails catastrophically on tree-based DGP
- RF/GBM robust across all DGPs (max 10% degradation)
- Neural Net best on heteroskedastic, but higher variance

---

## PRIORITY 3: Disconnected Networks (Response to Q7)

### Experiment 3.1: Multi-Treatment Disconnected Network

**Problem**: "Does not explicitly evaluate performance on disconnected networks"

**Design**:
```python
def disconnected_network_experiment(
    network_structures=['fully_connected', 'chain', 'star', 'disconnected_A', 'disconnected_B'],
    n_runs=50
):
    """
    Explicit evaluation on disconnected treatment networks.
    
    Network Structures:
    -------------------
    Treatments: {0 (placebo), A, B, C}
    
    1. Fully Connected (baseline):
       Sites: {0-A, 0-B, 0-C, A-B, A-C, B-C}
       
    2. Chain:
       Sites: {0-A, A-B, B-C}
       Target has 0 only → Need to transport A → B → C
       
    3. Star (0 at center):
       Sites: {0-A, 0-B, 0-C}
       No direct A-B, A-C, B-C comparisons
       
    4. Disconnected A:
       Sites: {0-B, 0-C}
       Target: 0 only, want to estimate A
       A only in source {A-0}, disconnected from target
       
    5. Disconnected B:
       Sites: {0-A, A-C}
       Target: 0 only, want to estimate B
       B only in source {B-0}, disconnected
    
    Baselines:
    ----------
    - IPD-NMA: Fails in disconnected cases (undefined)
    - Proposed: Should handle all cases via placebo anchoring
    
    Evaluation:
    -----------
    For each target treatment T ∈ {A, B, C}:
    - PEHE for τ_T(x) = μ_T(x) - μ_0(x)
    - Can we rank treatments correctly? Concordance index
    """
    results = []
    
    for network in network_structures:
        for run in range(n_runs):
            # Generate multi-treatment data with specified network
            data = generate_multitreatment_network(
                network_structure=network,
                seed=run
            )
            
            # Try IPD-NMA (will fail if disconnected)
            try:
                nma = IPDNetworkMetaAnalysis()
                nma.fit(data)
                nma_pehe = compute_pehe(nma, data)
            except ValueError:
                nma_pehe = np.nan  # Undefined
            
            # Proposed method (should always work)
            proposed = PlaceboAnchoredDRLearner()
            proposed.fit(data)
            proposed_pehe = compute_pehe(proposed, data)
            
            # Treatment ranking concordance
            true_ranking = data['true_treatment_ranking']
            pred_ranking = get_predicted_ranking(proposed, data)
            concordance = compute_concordance(true_ranking, pred_ranking)
            
            results.append({
                'Network': network,
                'Run': run,
                'NMA_PEHE': nma_pehe,
                'Proposed_PEHE': proposed_pehe,
                'Concordance': concordance
            })
    
    return pd.DataFrame(results)
```

**Expected Findings**:
- IPD-NMA undefined for disconnected_A, disconnected_B (PEHE = NaN)
- Proposed works in all cases
- PEHE degrades by ~30% in disconnected vs fully_connected
- Treatment ranking concordance > 0.8 even in disconnected cases

**Visualization**: Network diagrams + bar plots of PEHE by structure

---

## PRIORITY 4: Site Imbalance (Response to Q12)

### Experiment 4.1: Site Sample Size Imbalance

**Problem**: "How does the model perform when there is large imbalance between sites?"

**Design**:
```python
def site_imbalance_experiment(
    total_N=2000,
    imbalance_ratios=[1, 2, 5, 10, 20, 50],  # n_max / n_min
    n_sites=5,
    gold_fractions=[0.05, 0.10, 0.20],  # Fraction of N in target
    n_runs=50
):
    """
    Test robustness to severe site sample size imbalance.
    
    Scenarios:
    ----------
    Fix total N = 2000, vary allocation:
    
    1. Balanced (ratio=1):
       n = [400, 400, 400, 400, 400]
       
    2. Mild (ratio=2):
       n = [286, 286, 286, 286, 571]  (1 large site)
       
    3. Moderate (ratio=5):
       n = [182, 182, 182, 182, 909]
       
    4. Severe (ratio=10):
       n = [133, 133, 133, 133, 1333]
       
    5. Extreme (ratio=50):
       n = [38, 38, 38, 38, 1905]
    
    For each gold_fraction g:
       - Target has n_0 = g * N
       - Remaining (1-g) * N split across source sites
       - Within target: 50% placebo (gold), 50% treated
    
    Research Questions:
    -------------------
    Q1: Does large source site dominate and hurt anchoring?
    Q2: Does small gold budget (m_0 = g*N*0.5) limit performance?
    Q3: Is there a sweet spot for gold_fraction?
    """
    results = []
    
    for ratio in imbalance_ratios:
        for gold_frac in gold_fractions:
            n_target = int(total_N * gold_frac)
            n_source_total = total_N - n_target
            
            # Create imbalanced source allocation
            n_sources = allocate_imbalanced(
                n_total=n_source_total,
                n_sites=n_sites - 1,
                imbalance_ratio=ratio
            )
            
            for run in range(n_runs):
                data = generate_imbalanced_sites(
                    n_target=n_target,
                    n_sources=n_sources,
                    seed=run
                )
                
                # Fit model
                model = PlaceboAnchoredDRLearner()
                model.fit(data)
                
                pehe = compute_pehe(model, data)
                
                # Decompose error: proxy vs gold contribution
                m_0 = n_target // 2  # Gold budget
                
                results.append({
                    'ImbalanceRatio': ratio,
                    'GoldFraction': gold_frac,
                    'GoldBudget_m0': m_0,
                    'Run': run,
                    'PEHE': pehe
                })
    
    return pd.DataFrame(results)
```

**Expected Findings**:
- Performance stable for ratio ≤ 10
- Severe degradation when ratio > 20 AND gold_fraction < 0.10
- Sweet spot: gold_fraction ≈ 0.15 (balances proxy and gold contributions)

**Visualization**: 
- Line plot: PEHE vs imbalance_ratio (faceted by gold_fraction)
- Contour plot: PEHE vs (imbalance_ratio, gold_fraction)

---

## PRIORITY 5: Comparative Baselines (Response to Q10)

### Experiment 5.1: Comprehensive Baseline Comparison

**Problem**: "Missing comparisons with existing methods"

**Implementation Details**:

```python
# 1. IPW Transport (Reweighting)
class IPWTransport:
    def fit(self, X_source, A_source, Y_source, X_target, A_target, Y_target):
        # Estimate site assignment model: P(S=0|X)
        X_combined = np.vstack([X_source, X_target])
        S = np.hstack([np.zeros(len(X_source)), np.ones(len(X_target))])
        
        site_model = LogisticRegression()
        site_model.fit(X_combined, S)
        
        # Compute weights: w(x) = P(S=0|X) / P(S=1|X)
        prob_target = site_model.predict_proba(X_source)[:, 1]
        weights = prob_target / (1 - prob_target + 1e-6)
        
        # Stabilize weights
        weights = np.clip(weights, 0.1, 10)
        
        # Weighted outcome regression
        self.mu_0 = WeightedRegression().fit(
            X_source[A_source==0], 
            Y_source[A_source==0],
            weights[A_source==0]
        )
        self.mu_1 = WeightedRegression().fit(
            X_source[A_source==1],
            Y_source[A_source==1],
            weights[A_source==1]
        )
    
    def predict(self, X):
        return self.mu_1.predict(X) - self.mu_0.predict(X)


# 2. AIPW Transport (Doubly Robust)
class AIPWTransport:
    def fit(self, X_source, A_source, Y_source, X_target, A_target, Y_target):
        # Outcome regression (unweighted)
        self.mu_0 = RandomForestRegressor().fit(X_source[A_source==0], Y_source[A_source==0])
        self.mu_1 = RandomForestRegressor().fit(X_source[A_source==1], Y_source[A_source==1])
        
        # Site propensity
        X_combined = np.vstack([X_source, X_target])
        S = np.hstack([np.zeros(len(X_source)), np.ones(len(X_target))])
        self.site_model = LogisticRegression().fit(X_combined, S)
        
        # AIPW estimator
        # [Implementation follows Dahabreh et al. 2019]
    
    def predict(self, X):
        return self.mu_1.predict(X) - self.mu_0.predict(X)


# 3. IPD-MA with Random Effects
class IPDMetaAnalysis:
    def fit(self, X_source, A_source, Y_source, site_ids):
        # Hierarchical model: Y ~ β'X + A·τ'X + site_random_effect
        import statsmodels.api as sm
        from statsmodels.regression.mixed_linear_model import MixedLM
        
        df = pd.DataFrame(X_source, columns=[f'X{i}' for i in range(X_source.shape[1])])
        df['A'] = A_source
        df['Y'] = Y_source
        df['site'] = site_ids
        
        # Random intercept + fixed treatment effect
        formula = 'Y ~ A * (' + ' + '.join([f'X{i}' for i in range(X_source.shape[1])]) + ')'
        self.model = MixedLM.from_formula(formula, groups='site', data=df)
        self.result = self.model.fit()
    
    def predict(self, X):
        # Predict using fixed effects only (no site random effect)
        # [Implementation details]
        pass


# 4. Outcome Regression with Site Indicators
class OutcomeRegressionTransport:
    def fit(self, X_source, A_source, Y_source, site_ids, X_target):
        # Include site dummies + site-treatment interactions
        X_aug = np.hstack([
            X_source,
            pd.get_dummies(site_ids).values,
            A_source.reshape(-1, 1)
        ])
        
        self.model = GradientBoostingRegressor().fit(X_aug, Y_source)
        
        # For prediction, set site indicators to 0 (or average)
        self.target_site_encoding = np.zeros(len(np.unique(site_ids)))
    
    def predict(self, X):
        # [Implementation]
        pass


# Full comparison experiment
def comprehensive_baseline_comparison(n_runs=100):
    baselines = {
        'No-Transfer': NoTransferBaseline(),
        'Proxy-Only': ProxyOnlyBaseline(),
        'IPW-Transport': IPWTransport(),
        'AIPW-Transport': AIPWTransport(),
        'IPD-MA-FE': IPDMetaAnalysis(effects='fixed'),
        'IPD-MA-RE': IPDMetaAnalysis(effects='random'),
        'OutcomeReg-SiteIndicators': OutcomeRegressionTransport(),
        'Proposed': PlaceboAnchoredDRLearner()
    }
    
    # Test on multiple scenarios
    scenarios = [
        'mild_shift',
        'severe_shift',
        'overlap_violation',
        'disconnected'
    ]
    
    results = []
    for scenario in scenarios:
        for run in range(n_runs):
            data = generate_data(scenario=scenario, seed=run)
            
            for name, model in baselines.items():
                try:
                    model.fit(data)
                    pehe = compute_pehe(model, data)
                    ate_error = compute_ate_error(model, data)
                except Exception as e:
                    # Some methods may fail (e.g., IPD-MA in disconnected)
                    pehe = np.nan
                    ate_error = np.nan
                
                results.append({
                    'Scenario': scenario,
                    'Method': name,
                    'Run': run,
                    'PEHE': pehe,
                    'ATE_Error': ate_error
                })
    
    return pd.DataFrame(results)
```

**Expected Rankings** (by PEHE, mean across scenarios):

1. **Proposed**: 0.85 (best)
2. **AIPW-Transport**: 0.92 (close second, but fails in disconnected)
3. **IPD-MA-RE**: 1.05 (assumes exchangeability)
4. **OutcomeReg**: 1.15 (no anchoring)
5. **IPW-Transport**: 1.28 (sensitive to overlap)
6. **Proxy-Only**: 1.35
7. **No-Transfer**: 2.10 (worst)

---

## PRIORITY 6: Cross-Arm Degradation Validation (Response to Q11)

### Experiment 6.1: Analytical vs Empirical Degradation

**Problem**: "Quantify how CATE error degrades as cross-arm correlation decreases, analytically rather than only empirically"

**Design**:
```python
def validate_analytical_degradation_bound(
    rho_values=np.linspace(0.0, 1.0, 21),
    delta_0_magnitudes=[0.5, 1.0, 1.5, 2.0],
    n_runs=100
):
    """
    Validate the analytical bound:
    
    ||τ̂ - τ₀||²_L2 ≤ O_p(N^{-1/2}) + δ_proxy·δ_gold + (1-ρ)||δ₀||²_L2 + ||ζ||²_L2 + ||r||²_L2
    
    Procedure:
    ----------
    1. For each (ρ, ||δ₀||):
       a. Generate data with known δ₀, ρ, ζ
       b. Fit Proposed method
       c. Compute empirical error: ||τ̂ - τ₀||_L2
       d. Compute analytical bound terms:
          - Sampling: 1/√N (from influence function variance)
          - Nuisance product: δ_proxy · δ_gold
          - Cross-arm: (1-ρ)||δ₀||_L2
          - Residuals: ||ζ||_L2 + ||r||_L2
    
    2. Plot:
       - Empirical error vs ρ
       - Analytical bound vs ρ
       - Check: empirical ≤ analytical (with high probability)
    
    3. Regression:
       - Fit: error ~ α + β(1-ρ)||δ₀|| + γ||ζ|| + ε
       - Check: β > 0, significant (validates linear degradation in 1-ρ)
    """
    results = []
    
    for delta_0_mag in delta_0_magnitudes:
        for rho in rho_values:
            for run in range(n_runs):
                # Generate with explicit cross-arm coupling
                data = generate_with_cross_arm_coupling(
                    delta_0_magnitude=delta_0_mag,
                    rho=rho,
                    seed=run
                )
                
                # Fit model
                model = PlaceboAnchoredDRLearner()
                model.fit(data)
                
                # Empirical error
                tau_pred = model.predict(data['X_target'])
                tau_true = data['tau_true']
                empirical_error = np.sqrt(np.mean((tau_pred - tau_true)**2))
                
                # Analytical bound terms
                N = len(data['X_target'])
                sampling_term = 1 / np.sqrt(N)
                
                delta_proxy = estimate_proxy_error(model, data)
                delta_gold = estimate_gold_error(model, data)
                nuisance_product = delta_proxy * delta_gold
                
                delta_0_norm = np.linalg.norm(data['delta_0'])
                cross_arm_term = (1 - rho) * delta_0_norm
                
                zeta_norm = np.linalg.norm(data['zeta'])
                residual_term = zeta_norm
                
                analytical_bound = (
                    sampling_term + 
                    nuisance_product + 
                    cross_arm_term + 
                    residual_term
                )
                
                results.append({
                    'delta_0_mag': delta_0_mag,
                    'rho': rho,
                    'Run': run,
                    'EmpiricalError': empirical_error,
                    'AnalyticalBound': analytical_bound,
                    'SamplingTerm': sampling_term,
                    'NuisanceProduct': nuisance_product,
                    'CrossArmTerm': cross_arm_term,
                    'ResidualTerm': residual_term,
                    'BoundViolation': empirical_error > analytical_bound
                })
    
    df = pd.DataFrame(results)
    
    # Statistical validation
    print("Bound violation rate:", df['BoundViolation'].mean())  # Should be ~0
    
    # Regression to validate linear degradation
    import statsmodels.formula.api as smf
    df['one_minus_rho_times_delta'] = (1 - df['rho']) * df['delta_0_mag']
    
    reg = smf.ols('EmpiricalError ~ one_minus_rho_times_delta + ResidualTerm', data=df).fit()
    print(reg.summary())
    
    # Expected: β > 0, p < 0.001
    assert reg.params['one_minus_rho_times_delta'] > 0
    assert reg.pvalues['one_minus_rho_times_delta'] < 0.001
    
    return df, reg
```

**Expected Findings**:
- Bound holds with 95% probability (allowing for finite-sample slack)
- Regression coefficient β ≈ 0.85 (significant, p < 0.001)
- Validates: error ∝ (1-ρ) linearly

**Visualization**:
- Scatter: Empirical error vs (1-ρ)||δ₀|| (should be linear)
- Band plot: Analytical bound (shaded) vs empirical error (line) vs ρ

---

## Summary Table: All Additional Experiments

| Priority | Experiment | Reviewer Q | Effort | Impact |
|----------|-----------|-----------|--------|--------|
| **1** | Monte Carlo + Statistical Testing | Q3 | High | Critical |
| **1** | Covariate Dimensionality Sweep | Q3 | Medium | High |
| **2** | Non-Linear Transport Bias | Q5 | High | High |
| **2** | Non-Linear Outcome Models | Q5 | Medium | Medium |
| **3** | Multi-Treatment Disconnected | Q7 | High | Critical |
| **4** | Site Imbalance | Q12 | Medium | Medium |
| **5** | Comprehensive Baselines | Q10 | Very High | Critical |
| **6** | Analytical Degradation Validation | Q11 | Medium | Medium |

---

## Implementation Timeline

### Week 1: Core Statistical Rigor
- [ ] Implement Monte Carlo protocol (100 runs)
- [ ] Add Friedman + Wilcoxon tests
- [ ] Covariate dimensionality sweep (p ∈ [5, 100])
- [ ] Generate tables with means ± std, p-values

### Week 2: Non-Linear & Disconnected
- [ ] Implement 5 non-linear bias DGPs
- [ ] Test 5 correction methods
- [ ] Implement multi-treatment network generator
- [ ] Run disconnected network experiments

### Week 3: Baselines & Validation
- [ ] Implement all 7 baselines (IPW, AIPW, etc.)
- [ ] Run comprehensive comparison
- [ ] Site imbalance experiments
- [ ] Analytical degradation validation

### Week 4: Visualization & Reporting
- [ ] Generate all plots (20+ figures)
- [ ] Write up results for response letter
- [ ] Add to manuscript appendix

---

## Acceptance Criteria (For Response Letter)

To satisfy the reviewer, we must demonstrate:

1. ✅ **Statistical Significance**: Friedman test p < 0.001, pairwise Wilcoxon p < 0.01
2. ✅ **Robustness to Non-Linearity**: LASSO degrades gracefully (< 30% worse than oracle non-linear)
3. ✅ **Disconnected Networks Work**: Proposed functional where IPD-NMA undefined
4. ✅ **Site Imbalance Tolerable**: Performance stable for imbalance ratio ≤ 10
5. ✅ **Beats All Baselines**: Statistically significant improvement over IPW, AIPW, IPD-MA
6. ✅ **Analytical Bound Validated**: Empirical error matches analytical prediction (R² > 0.7)

If all 6 criteria met → Strong response to reviewer
