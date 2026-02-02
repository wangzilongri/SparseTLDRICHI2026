# Benchmark & Experiment Gaps Checklist

**Current State:** Single synthetic config (10 sources, target n=200, low-rank transfer rank=1, nontransfer_scale=0.3, proxy_nonlinearity=0.5) with No-Transfer / Proxy-Only / Anchor-Only / Proposed-A/B.

**Priority Legend:** 🔴 High (reviewer-critical) | 🟡 Medium | 🟢 Nice-to-have

**Schema Reference:** See [`docs/BENCHMARK_SCHEMA.md`](docs/BENCHMARK_SCHEMA.md) for complete data model specification.

---

## Implementation Reference (Completed Items)

### Files Created

| File | Lines | Description |
|------|-------|-------------|
| `src/benchmark_schema.py` | 580 | Dataclasses, enums, validation, method registry |
| `src/benchmark_runner.py` | 514 | Grid + MC experiment driver |
| `src/benchmark_aggregation.py` | 400 | Stats aggregation, Holm correction, LaTeX tables |
| `src/benchmark_plots.py` | 500 | PlotSpec system, consistent styling |
| `docs/BENCHMARK_SCHEMA.md` | 400 | Complete column definitions, plot specs |

### Quick Test Commands

```bash
# Test schema module
python src/benchmark_schema.py

# Test aggregation (with CSV input)
python src/benchmark_aggregation.py results_rep.csv --output results/ --reference ProxyOnly

# Test plot generation
python src/benchmark_plots.py --agg results_agg.csv --output results/figures --benchmark gold_sweep

# Run benchmark (requires DGP integration)
python src/benchmark_runner.py --benchmark gold_sweep --n_rep 10 --output results/benchmarks
```

### Key Imports

```python
# Schema
from src.benchmark_schema import (
    Scenario, MethodSpec, RepResult, PlotSpec, Feasibility,
    METHOD_REGISTRY, get_method_spec, get_feasible_methods,
    validate_results_rep, generate_seed, create_empty_results_df
)

# Runner
from src.benchmark_runner import (
    BenchmarkConfig, generate_scenario_grid, run_benchmark,
    run_gold_sweep, run_proxy_sweep
)

# Aggregation
from src.benchmark_aggregation import (
    aggregate_results, compute_summary_table, find_best_methods,
    compute_method_rankings, create_latex_table, save_aggregated_results
)

# Plots
from src.benchmark_plots import (
    plot_line, plot_bar, plot_heatmap, plot_violin, plot_scatter,
    execute_plot_spec, generate_benchmark_plots, METHOD_COLORS
)
```

### Method Color Reference

| Method | Color | Hex |
|--------|-------|-----|
| NoTransfer | Red | `#d62728` |
| ProxyOnly | Orange | `#ff7f0e` |
| AnchorOnly | Blue | `#1f77b4` |
| **ProposedA** | **Green (dark)** | `#2ca02c` |
| **ProposedB_LinearStepB** | **Green (light)** | `#98df8a` |
| **ProposedB_KernelStepB** | **Green (very light)** | `#c7e9c0` |
| IPD_RE | Pink | `#e377c2` |
| AIPWTransport | Gray | `#7f7f7f` |
| EntropyBalancing | Yellow-green | `#bcbd22` |
| TARNet | Purple | `#9467bd` |

---

## A. Core Infrastructure Additions (Do Once)

### A0) Data Model & Schema 🔴 ✅

**Implementation:** `src/benchmark_schema.py`

- [x] **Implement `results_rep` DataFrame schema** (see `docs/BENCHMARK_SCHEMA.md`)
  - Identifier cols: `benchmark_id`, `scenario_id`, `rep`, `method`, `feasibility`
  - Scenario cols: `m0`, `m1`, `n_proxy_total`, `C_sources`, `shift_strength`, etc.
  - Metric cols: `pehe`, `tau_corr`, `ate_abs_err`, `mu0_rmse`, `mu1_rmse`, etc.
  - Diagnostic cols: `stage2_lambda`, `stage2_n_selected`, `runtime_sec`
  - Uncertainty cols: `ate_se_if`, `ate_ci_low`, `ate_ci_high`, `ate_covered_95`

- [x] **Implement `results_agg` DataFrame schema**
  - Aggregated: `X_mean`, `X_sd`, `X_n` for each metric X
  - Paired deltas: `pehe_delta_vs_proxy_mean`, `pehe_p_value`, `pehe_q_value` (Holm)

- [x] **Implement dataclasses** (`Scenario`, `MethodSpec`, `RepResult`, `PlotSpec`)

- [x] **Implement validation function** (`validate_results_rep()`)

- [x] **Define method whitelist with feasibility labels** (12 methods registered)
  - Core: `NoTransfer`, `ProxyOnly`, `AnchorOnly`, `ProposedA`, `ProposedB_LinearStepB`
  - Baselines: `IPD_RE`, `AIPWTransport`, `EntropyBalancing`, `DRLearner_*`, `TARNet`

**Usage:**
```python
from src.benchmark_schema import Scenario, RepResult, validate_results_rep

scenario = Scenario(benchmark_id='gold_sweep', m0=100, n_proxy_total=2000)
print(scenario.scenario_id)  # Auto-generated hash

result = RepResult(scenario_id=scenario.scenario_id, benchmark_id='gold_sweep',
                   rep=0, method='ProposedB_LinearStepB', feasibility='FeasibleRestricted',
                   pehe=1.5, ate_abs_err=0.3)
```

### A1) Experiment Runner: Grid + MC 🔴 ✅

**Implementation:** `src/benchmark_runner.py`

- [x] **Top-level driver with inputs:**
  - `base_config` (current "one point")
  - `grid`: list of configs (cartesian product of sweep params)
  - `n_rep`: number of MC repetitions
  - `seed0`: master seed

- [x] **Per (config, rep) loop:**
  - `seed = hash(config_id, rep, seed0)`
  - Generate data
  - Run all methods
  - Compute metrics
  - Write one row per (config, rep, method)

- [x] **Output schema:** Follow `results_rep` from `docs/BENCHMARK_SCHEMA.md`

**Usage:**
```python
from src.benchmark_runner import BenchmarkConfig, run_benchmark

config = BenchmarkConfig(
    benchmark_id='gold_sweep',
    base_scenario={'n_proxy_total': 2000, 'C_sources': 10},
    sweep_params={'m0': [25, 50, 100, 200, 500]},
    n_rep=100,
    seed0=42,
    methods=['ProxyOnly', 'ProposedB_LinearStepB'],
)
df_rep = run_benchmark(config, data_generator, metric_computer)
```

### A2) Aggregation + Stats Layer 🔴 ✅

**Implementation:** `src/benchmark_aggregation.py`

- [x] **Grouping:** by `(benchmark_id, scenario_id, method, feasibility, ...)`
- [x] **Summary stats:** `mean ± std` and `median ± IQR`
- [x] **Pairwise deltas vs reference baseline (ProxyOnly):**
  - Per-config paired t-test OR Wilcoxon signed-rank
  - Multiple-comparison correction (Holm)
  - Output: `X_delta_vs_proxy_mean`, `X_p_value`, `X_q_value`
- [x] **Outputs:**
  - "Sweep curves" (metric vs parameter) with error bars
  - "Heatmaps" (e.g., metric vs (m0, nontransfer))

**Usage:**
```python
from src.benchmark_aggregation import aggregate_results, find_best_methods

df_agg = aggregate_results(df_rep, reference_method='ProxyOnly')
# Columns: pehe_mean, pehe_sd, pehe_delta_vs_ProxyOnly_mean, pehe_p_value, pehe_q_value

best = find_best_methods(df_agg, metrics=['pehe', 'ate_abs_err'])
# {'pehe': {'method': 'ProposedB_LinearStepB', 'value': 1.39, ...}}
```

### A3) Plot Generation System 🟡 ✅

**Implementation:** `src/benchmark_plots.py`

- [x] **Implement `PlotSpec` dataclass**
- [x] **Auto-generate plots from spec:**
  - Line plots with error bars
  - Grouped bar charts
  - Heatmaps (for rank mismatch grid)
  - Violin/box plots (for stability)
  - Scatter plots (for coverage)
- [x] **Consistent styling:** Method colors, feasibility markers

**Usage:**
```python
from src.benchmark_plots import plot_line, execute_plot_spec, PlotSpec

# Direct plotting
fig = plot_line(df_agg, x='m0', y='pehe_mean', hue='method', yerr='pehe_sd')

# Via PlotSpec
spec = PlotSpec(name='pehe_vs_m0', df_source='results_agg', plot_type='line',
                x='m0', y='pehe_mean', hue='method', yerr='pehe_sd')
fig = execute_plot_spec(spec, df_agg=df_agg, output_dir='results/figures')
```

---

## B. Monte Carlo + Sweeps

### B1) Gold Budget Sweep 🔴

- [ ] **Parameterize target placebo:** `m0 ∈ {25, 50, 100, 200, 500}`
- [ ] **DGP subsample mechanism:**
  - Generate target with `N0_total` large (e.g., 2000 placebo + 2000 treated for oracle eval)
  - Estimation uses only `m0` placebo
  - Evaluation uses full held-out test set (including treated) to compute PEHE

- [ ] **Option A extension:**
  - Add `m1 ∈ {0, 25, 50, 100, 200}` (include 0 so Option A reduces to B)
  - **Crucial:** Keep evaluation treated data disjoint from estimation treated data

- [ ] **Plot:** 
  - x-axis = `m0`
  - y-axis = PEHE / μ₀ RMSE / policy regret
  - Separate panels: Option B (no treated target) vs Option A (some treated target)

### B2) Proxy Budget Sweep 🔴

- [ ] **Parameterize:** `n_proxy_total ∈ {500, 1000, 2000, 5000, 10000}`
- [ ] **Variant 1 - Fixed C:** 10 sources, allocate evenly `n_c = n_proxy_total / C`
- [ ] **Variant 2 - Fixed per-site n:** Vary number of sources C ∈ {2, 5, 10, 20}, holding total constant
- [ ] **Deliverable:** Show whether gains persist when proxy weak vs strong; whether anchoring dominates when proxy huge

### B3) Site Imbalance Sweep 🟡

- [ ] **Fix total proxy size, vary (n₁,...,n_C) concentration**
- [ ] **Configurations:**
  - One huge source (90% of samples) + many small
  - Even split
  - Power-law distribution
- [ ] **Addresses reviewer's "site imbalance" concern directly**

### B4) Covariate Shift Sweep 🟡

- [ ] **Vary |μ_c - μ₀| magnitude**
- [ ] **Vary Σ_c mismatch (eigenvalue ratio)**
- [ ] **Report Wasserstein-2 / MMD as proxy measure of shift**
- [ ] **Not just one setting**

### B5) Overlap/Positivity Stress-Test 🟡

- [ ] **Increasingly poor overlap between target and sources**
- [ ] **Increasingly poor overlap across arms within sites**
- [ ] **Report when reweighting fails:**
  - Calibration blow-up
  - Variance blow-up
  - ESS (effective sample size) collapse

---

## C. Misspecification Stress Tests (A5/A6)

### C1) A5 Violation: Non-Sparse Correction 🔴

- [ ] **"Controlled dense" generator:**
  - Dense vector b ∈ ℝᵖ with entries b_j ~ N(0,1)
  
- [ ] **Control "effective sparsity" via:**
  - **Top-k:** Keep top-k magnitudes (already sparse)
  - **Power-law decay:** Sort |b| descending, set b_(j) = s · j^(-α). Smaller α = denser

- [ ] **Sweep:**
  - `alpha ∈ {0.5, 1, 2, 4}` OR
  - `k/p ∈ {0.05, 0.1, 0.25, 0.5, 1.0}`

- [ ] **Report (beyond PEHE):**
  - Stage-2 selection stability: `n_selected`, Jaccard similarity across folds/reps
  - "Graceful degradation" curve: performance vs effective sparsity

### C2) A5 Violation: Nonlinear Correction 🔴

- [ ] **Replace δ_{a,0}(x) = x'β with nonlinear family (implement 2-3):**
  1. **Sparse interactions:** Σ_{(j,k)∈I} γ_jk x_j x_k with small |I|
  2. **Piecewise:** Σ_{j∈S} γ_j max(0, x_j - t_j)
  3. **Tree-like:** Σ_ℓ w_ℓ 𝟙(x_{j_ℓ} > t_ℓ) (random depth-2 stump ensemble)
  4. **NN correction:** Small MLP on subset of features

- [ ] **Estimation variant (optional but strong):**
  - "Anchor-Stage2-GBM" (Stage 2 uses gradient boosting instead of LASSO)
  - Shows framework can swap in flexible calibrators

- [ ] **Key plot:** PEHE vs "nonlinearity strength" parameter η (scale of nonlinear term)

### C3) A6 Violation: Cross-Arm Mapping Not Low-Rank 🔴

- [ ] **Implement rank sweep:**
  - Generate M* with rank `r_true ∈ {1, 2, 5, 10, p}`
  - Sample U ∈ ℝ^(p×r), V ∈ ℝ^(p×r), set M* = UV'

- [ ] **Fit Step B with assumed rank `r_fit ∈ {1, 2, 5}`**
- [ ] **Report mismatch grid (r_true, r_fit)**

- [ ] **Deliverable:**
  - Shows Option B breaks *predictably* as rank complexity increases
  - Justifies "we use low-rank as regularization; misfit appears as structural term"

### C4) A6 Violation: Cross-Arm Mapping Nonlinear 🔴

- [ ] **Replace β₁ = Mβ₀ + ν with:**
  - β₁ = σ(Mβ₀) + ν (elementwise nonlinearity)
  - OR β₁ = M₂ · ReLU(M₁β₀) + ν

- [ ] **Sweep "degree of nonlinearity":**
  - Mixing parameter ρ ∈ [0,1]: β₁ = (1-ρ)Mβ₀ + ρf(β₀) + ν

- [ ] **Baseline add-on (recommended):**
  - Step B with kernel ridge / MLP mapping from β₀→β₁ (trained on source sites)
  - Shows "Option B is not inherently linear; linear is conservative default"

### C5) Site-Specific Transfer Operators M_c 🟡

- [ ] **Different transfer operators per site**
- [ ] **Tests pooling assumption**
- [ ] **Sweep heterogeneity in M_c**

### C6) Effect-Modifier Confounding with Site Indicator 🟡

- [ ] **Implement latent U:**
  - Draw U ~ N(κ'X, 1) but site-dependent κ_c
  - Treatment effect depends on U: τ_c(x) = τ_base(x) + γU
  - Keep U unobserved in estimation

- [ ] **Sweep γ and site-correlation strength**

- [ ] **Report failure-mode figure:**
  - Calibration of μ₀ improves (anchoring still helps baseline)
  - But τ ranking/policy regret degrades as γ grows
  - Visually supports "we do not claim unmeasured effect modification is resolved"

---

## D. Baselines

### D1) IPD Hierarchical / Random Effects 🔴

- [ ] **Mixed-effects model for outcomes:**
  - Fixed effects: treatment, covariates, treatment×covariate interactions
  - Random intercepts and random treatment effects by site

- [ ] **Implementation:**
  - Python: `statsmodels.MixedLM`
  - R: `lme4::lmer`

- [ ] **Fairness handling:**
  - In "restricted" (no treated target): label as **oracle/infeasible**
  - In "oracle" setting: report it

- [ ] **Outputs:** τ̂(x) from fitted model as difference in predicted means

### D2) AIPW Transport Baseline 🔴

- [ ] **Standard transport AIPW for ATE:**
  - Fit site model w(x) = Pr(S=0|X=x) using pooled source+target placebo
  - Compute weights for source to mimic target
  - Fit outcome regressions μ̂_a(x) on sources
  - AIPW target ATE formula

- [ ] **Stress-test benefit:** Under overlap violations, this baseline should blow up—good contrast

### D3) "Just Add Site ID" Baselines 🟡

- [ ] **Baseline 1:** Pooled DR-learner WITH `site_id` as feature
- [ ] **Baseline 2:** Same but WITHOUT `site_id`
- [ ] **Diagnostic value:** If method's gains collapse to "site_id does it", preempt reviewer criticism

### D4) Covariate-Balancing Weights 🟡

- [ ] **Entropy balancing / CBPS-style**
- [ ] **Stronger alternative to plain logistic IPW**

### D5) R-/DR-Learner on Pooled Data 🟢

- [ ] **With site features vs without site features**
- [ ] **Tests if gains are "just add site id"**

### D6) TARNet/CFR-Style Representation Learning 🟢

- [ ] **Common in IHDP-style CATE benchmarks**
- [ ] **"Out of domain" but reviewers like seeing it**

### D7) Feasible vs Oracle Labeling System 🔴

- [ ] **Add column `feasibility` per method per scenario:**
  - `feasible_restricted`: uses only target placebo for estimation
  - `oracle_target_treated`: uses target treated for estimation
  - `infeasible_disconnected`: requires info not present by design

- [ ] **In plots/tables:**
  - Show feasible methods in main table
  - Move oracle methods to appendix or gray them out

---

## E. Disconnected Network Benchmark Family

### E1) Treatment Graph Generator 🟡

- [ ] **Inputs:**
  - `K` treatments + placebo
  - `graph_type ∈ {chain, star, two_components}`
  - `target_component`: which component contains target's available arms (placebo only)

- [ ] **For each source site:** Sample an edge (comparator pair) from the graph component

### E2) Multi-Treatment Graphs 🟡

- [ ] **Vary number of treatments**
- [ ] **Graph connectivity: chain, star, two components**

### E3) Partial Connectivity 🟡

- [ ] **Target connected via placebo for some treatments but not others**

### E4) Evaluation Protocol 🟡

- [ ] **Estimand:** Effect of "held-out" treatment A* in target
- [ ] **Ensure by construction:** No path connects A* to target under NMA assumptions
- [ ] **Report:** NMA/IPD-NMA is undefined (don't compute)

---

## F. Uncertainty + Interval Coverage

### F1) Influence-Function SE for ATE + Coverage 🟡

- [ ] **For each rep:**
  - Compute ATE_hat and SE_hat from IF
  - 95% CI

- [ ] **Across reps:** Empirical coverage rate

- [ ] **Compare:**
  - IF-based SE
  - Nonparametric bootstrap over individuals (optional; small MC grid only)

### F2) Conditional CATE Coverage 🟢

- [ ] **Pick fixed covariate points (e.g., 20 quantile grid points)**
- [ ] **Compute pointwise intervals using:**
  - Asymptotic normal approximation from local regression residuals
  - OR bootstrap

- [ ] **Show coverage vs τ̂ decile**

---

## G. Practical Robustness Checks

### G1) LASSO Lambda Stability Under Small m₀ 🟡

- [ ] **Log for each rep:** Selected λ, `n_selected`, CV curve variance
- [ ] **Plot:** Histogram of λ across reps for each m₀
- [ ] **Compare:** "1-SE rule" vs "min-CV" (two variants)

### G2) No-Leak Scaling 🟡

- [ ] **Enforce:** All standardization/PCA/representation learning fits on training folds only
- [ ] **Apply to validation/test folds**
- [ ] **Add unit test:** Assert fold means not used globally

### G3) Heavy Tails / Outliers 🟡

- [ ] **Noise options:**
  - t_ν with ν ∈ {3, 5, 10}
  - Contamination: (1-ε)N(0,σ²) + εN(0,10σ²), ε ∈ {0.01, 0.05}

- [ ] **Report:** ECE + policy regret (reveal tail sensitivity)

### G4) High-Dimensional p ≫ m₀ 🟡

- [ ] **Sweep:** `p ∈ {50, 200, 500, 1000}`
- [ ] **Keep `m0` small (50/100)**
- [ ] **Shows exactly where Stage 2 fails—and whether Option B compounds it**

---

## H. Real-Data Benchmarks

### H1) IHDP / ACIC-Style Semi-Synthetic 🟢

- [ ] **Classic CATE benchmark**
- [ ] **Sanity check for Stage 3 machinery**
- [ ] **(Even if transport story is synthetic)**

### H2) Multi-Site / Multi-Trial IPD-Like Dataset 🟢

- [ ] **Construct "sites" by splitting large observational/RCT dataset into cohorts with covariate shift**
- [ ] **Key:** Target has placebo only for estimation (hide treated except for eval)

---

## Implementation Priority (Minimum Viable for Reviewers)

### Phase 1: Infrastructure 🔴
1. - [ ] A0: Data model & schema (dataclasses, validation)
2. - [ ] A1: Experiment runner (grid + MC)
3. - [ ] A2: Aggregation + stats layer (mean±sd, paired tests, Holm correction)
4. - [ ] A3: Plot generation system

### Phase 2: Core Sweeps 🔴
5. - [ ] B1: Gold-budget sweep (m₀ ∈ {25,50,100,200,500})
6. - [ ] B2: Proxy-budget sweep (Σn_c varying)
7. - [ ] B3: Site imbalance sweep (reviewer explicitly asked)

### Phase 3: Assumption Violations 🔴
8. - [ ] C1: A5 dense correction (power-law decay α sweep)
9. - [ ] C2: A5 nonlinear correction (sparse interactions or piecewise)
10. - [ ] C3: A6 rank mismatch (r_true vs r_fit grid)
11. - [ ] C4: A6 nonlinear transfer (mixing parameter ρ sweep)

### Phase 4: Strong Baselines 🔴
12. - [ ] D1: IPD hierarchical model
13. - [ ] D2: AIPW transport baseline
14. - [ ] D7: Feasible vs Oracle labeling system

### Phase 5: Extended Benchmarks 🟡
15. - [ ] B4: Covariate shift sweep
16. - [ ] B5: Overlap stress-test
17. - [ ] C6: Effect-modifier confounding
18. - [ ] D3: "Just add site ID" baselines
19. - [ ] F1: ATE interval coverage

### Phase 6: Polish 🟢
20. - [ ] E1-E4: Disconnected network family
21. - [ ] G1-G4: Robustness checks
22. - [ ] H1-H2: Real-data benchmarks

---

## Minimum Viable Rebuttal Commitment

**If you need to commit in the rebuttal without overpromising:**

1. ✅ **MC (≥100 reps)** + **Gold-budget sweep** + **Proxy-budget sweep**, all with mean±sd and paired tests
2. ✅ Two misspec tests: **dense correction** + **rank-mismatch cross-arm mapping** (most bang-for-buck)
3. ✅ Add **AIPW transport** + **hierarchical IPD** as baselines, with explicit **feasible/oracle labeling**
4. ✅ Add **site-imbalance sweep** (since reviewer explicitly asked)

**This answers 80% of reviewer's "missing experiments" critique with minimal new method engineering.**

---

## Progress Tracking

| Category | Total | Done | Remaining |
|----------|-------|------|-----------|
| A. Infrastructure (A0-A3) | 4 | **4** | 0 |
| B. MC + Sweeps | 5 | 0 | 5 |
| C. Misspec Tests | 6 | 0 | 6 |
| D. Baselines | 7 | 0 | 7 |
| E. Disconnected Family | 4 | 0 | 4 |
| F. Uncertainty | 2 | 0 | 2 |
| G. Robustness | 4 | 0 | 4 |
| H. Real Data | 2 | 0 | 2 |
| **TOTAL** | **34** | **4** | **30** |

---

## Artifact Checklist (Per Benchmark)

Each benchmark runner should produce:

- [ ] `results_rep_{benchmark}.csv` - Rep-level results (strict schema)
- [ ] `results_agg_{benchmark}.csv` - Aggregated results with paired tests
- [ ] `figures/{benchmark}_*.png` - Auto-generated plots from PlotSpec
- [ ] `tables/{benchmark}_*.tex` - LaTeX tables for paper

---

*Last updated: 2026-01-30*
