# Priority Checklist: Response to Reviewer SDFf

## TL;DR

**Current Status**: Design is sound but experiments need more rigor  
**Critical Gaps**: 3 experiments (Q3, Q7, Q10) must be done  
**Timeline**: Minimum 3 weeks, ideal 6-8 weeks  
**Risk**: High rejection risk without Q3, Q7, Q10

---

## 🔴 CRITICAL (Must Do - Rejection Risk)

### 1. Monte Carlo Rigor (Q3) - Week 1-2
**Why Critical**: Reviewer explicitly requests this, questions validity of current results

**Current**: 20 runs, no statistical tests  
**Required**: 100 runs, Friedman test, effect sizes

- [ ] Update all experiments to 100+ MC runs
- [ ] Implement Friedman test (methods as treatments, metrics as blocks)
- [ ] Add Wilcoxon pairwise tests with Bonferroni correction
- [ ] Compute Cohen's d effect sizes
- [ ] Generate tables: Mean ± Std, p-values, effect sizes
- [ ] Sweep covariate dimensionality: p ∈ {5, 10, 20, 50, 100}

**Files to Create**:
- `experiments/statistical_testing.py`
- `src/evaluation.py` (update with test functions)

**Expected Output**:
```
Friedman test: χ² = 87.3, p < 0.001 (methods differ significantly)
Post-hoc Wilcoxon: Proposed vs Proxy-Only: p < 0.001, d = 0.85 (large effect)
```

**Acceptance**: p < 0.01 for Proposed vs all baselines on PEHE

---

### 2. Disconnected Networks (Q7) - Week 3
**Why Critical**: Core motivating scenario, but not explicitly evaluated

**Current**: Mentions "disconnected" but no multi-treatment evaluation  
**Required**: Explicit multi-treatment network with topology variations

- [ ] Implement multi-treatment DGP: treatments {0, A, B, C}
- [ ] Create 5 network structures:
  - Fully connected (baseline)
  - Chain: 0-A-B-C
  - Star: 0 connects to A, B, C separately
  - Disconnected A: No path from A to target
  - Disconnected B: No path from B to target
- [ ] Show IPD-NMA returns `NaN` or fails
- [ ] Show Proposed works in all cases
- [ ] Measure treatment ranking concordance

**Files to Create**:
- `src/data_generator_multitreatment.py`
- `experiments/disconnected_networks.py`

**Expected Output**:
```
Network: Fully Connected
- IPD-NMA PEHE: 0.92
- Proposed PEHE: 0.85

Network: Disconnected A
- IPD-NMA PEHE: NaN (undefined)
- Proposed PEHE: 1.15 (30% degradation, still works)
```

**Acceptance**: Proposed functional in all topologies, IPD-NMA fails in ≥2

---

### 3. Baseline Comparisons (Q10) - Week 4-5
**Why Critical**: Reviewer says "strengthen the paper" - implies weakness without

**Current**: Listed but not implemented  
**Required**: Full implementations with fair comparison

- [ ] Implement 7 baselines:
  1. No-Transfer (target placebo only)
  2. Proxy-Only (pooled sources)
  3. IPW-Transport (reweighting)
  4. AIPW-Transport (doubly robust reweighting)
  5. IPD-MA-FE (fixed effects meta-analysis)
  6. IPD-MA-RE (random effects)
  7. OutcomeReg-Transport (with site indicators)
  8. Proposed (full method)
- [ ] Run on 4 scenarios × 100 runs:
  - Mild shift
  - Severe shift
  - Overlap violation
  - Disconnected
- [ ] Generate comparative tables and plots

**Files to Create**:
- `src/baselines/ipw_transport.py`
- `src/baselines/aipw_transport.py`
- `src/baselines/ipd_meta_analysis.py`
- `src/baselines/outcome_regression.py`
- `experiments/comparison_baselines.py`

**Expected Output**:
```
Method Rankings (by PEHE, averaged across scenarios):
1. Proposed: 0.85 ± 0.12
2. AIPW-Transport: 0.92 ± 0.15
3. IPD-MA-RE: 1.05 ± 0.18
4. OutcomeReg: 1.15 ± 0.22
5. IPW-Transport: 1.28 ± 0.31
6. Proxy-Only: 1.35 ± 0.25
7. No-Transfer: 2.10 ± 0.45
```

**Acceptance**: Proposed ranks #1 with statistical significance (p < 0.01)

---

## 🟡 HIGH PRIORITY (Should Do - Strengthens Paper)

### 4. Non-Linear Extensions (Q5) - Week 6-7
**Why Important**: Addresses core assumption (linear sparse bias)

**Sub-experiments**:

#### 4a. Non-Linear Transport Bias
- [ ] Implement 5 bias forms:
  - Linear (current)
  - Quadratic: δ(x) = β'x + γ'(x²)
  - Interactions: δ(x) = β'x + Σᵢⱼ θᵢⱼ xᵢxⱼ
  - Piecewise: δ(x) = β₁'x if x₁>0 else β₂'x
  - Sigmoid: δ(x) = 1/(1+exp(-β'x))
- [ ] Test 5 correction methods:
  - LASSO (current)
  - Ridge
  - KernelRidge (RBF)
  - RandomForest
  - Natural splines
- [ ] 5 bias × 5 corrections × 50 runs = 1,250 experiments

**Files to Create**:
- `src/data_generator_nonlinear.py`
- `experiments/nonlinear_bias.py`

**Expected**: LASSO degrades gracefully (< 30% worse than oracle)

#### 4b. Non-Linear Outcome Models
- [ ] Implement 5 DGPs:
  - Linear Y = β'X + A·τ(X) + ε
  - Polynomial
  - Interactions (2-way)
  - Tree-based
  - Heteroskedastic: Var(ε|X) = σ²(X)
- [ ] Test 4 proxy models:
  - Linear
  - RandomForest
  - GradientBoosting
  - NeuralNet
- [ ] 5 DGPs × 4 models × 50 runs = 1,000 experiments

**Expected**: RF/GBM robust across all DGPs

---

### 5. Site Imbalance (Q12) - Week 8 (Day 1-4)
**Why Important**: Practical concern in real multi-site trials

- [ ] Fix total N = 2000
- [ ] Sweep imbalance ratios: {1, 2, 5, 10, 20, 50}
- [ ] Sweep gold fractions: {0.05, 0.10, 0.20}
- [ ] 6 ratios × 3 fractions × 50 runs = 900 experiments
- [ ] Measure when performance collapses

**Files to Create**:
- `experiments/site_imbalance.py`

**Expected**: Stable for ratio ≤ 10, degrades for ratio > 20 when gold < 0.10

---

### 6. Analytical Degradation Validation (Q11) - Week 8 (Day 5-7)
**Why Important**: Strengthens theoretical contribution

- [ ] For each ρ ∈ [0, 1]:
  - Generate data with known δ₀, ρ, ζ
  - Compute empirical error: ||τ̂ - τ₀||
  - Compute analytical bound: O_p(N^{-1/2}) + (1-ρ)||δ₀|| + ||ζ|| + ...
  - Verify: empirical ≤ analytical (with high probability)
- [ ] Regression: error ~ α + β(1-ρ)||δ₀|| + ε
- [ ] Test: β > 0, p < 0.001

**Files to Create**:
- `experiments/analytical_validation.py`

**Expected**: Bound holds 95% of time, regression β ≈ 0.85 (p < 0.001)

---

## Timeline Summary

### Minimum Viable (3 weeks) - Avoid Rejection
```
Week 1-2: Q3 (Monte Carlo + tests)
Week 3:   Q7 (Disconnected networks)
Week 4-5: Q10 (Baselines - minimal: IPW, AIPW, IPD-MA only)
```
**Risk**: Low rejection risk, but weak on robustness

### Recommended (6 weeks) - Strong Response
```
Week 1-2: Q3 (Monte Carlo + tests)
Week 3:   Q7 (Disconnected networks)
Week 4-5: Q10 (All baselines)
Week 6-7: Q5 (Non-linear extensions)
```
**Risk**: Very low rejection risk, addresses all critical concerns

### Ideal (8 weeks) - Comprehensive
```
Week 1-2: Q3 (Monte Carlo + tests)
Week 3:   Q7 (Disconnected networks)
Week 4-5: Q10 (All baselines)
Week 6-7: Q5 (Non-linear extensions)
Week 8:   Q12 (Site imbalance) + Q11 (Analytical validation)
```
**Risk**: Negligible rejection risk, publishable in top venue

---

## Quick Start: What to Do Today

### Step 1: Read Documents (1 hour)
- [ ] Read GAP_ANALYSIS.md to understand gaps
- [ ] Read REVIEWER_EXPERIMENTS.md sections 1.1, 3.1, 5.1 (the critical 3)

### Step 2: Set Up Testing Infrastructure (2-3 hours)
- [ ] Update `src/evaluation.py` with statistical test functions:
  ```python
  def friedman_test(results_df)
  def wilcoxon_pairwise(results_df)
  def compute_cohens_d(group1, group2)
  ```

### Step 3: Start with Monte Carlo (Priority 1)
- [ ] Pick one existing experiment (e.g., core ablation)
- [ ] Change `n_runs=20` → `n_runs=100`
- [ ] Add statistical tests at the end
- [ ] Verify it works (2-3 hours)

### Step 4: Plan Implementation (1 hour)
- [ ] Create GitHub issues or task list for each experiment
- [ ] Assign time estimates
- [ ] Schedule work over next 3-8 weeks

---

## Success Metrics

After implementing all Critical (🔴) experiments, you should be able to show:

✅ **Statistical Significance**:
```
Friedman test: p < 0.001 (methods significantly differ)
Proposed vs Proxy-Only: Wilcoxon p < 0.001, Cohen's d = 0.85
Proposed vs AIPW: Wilcoxon p = 0.003, Cohen's d = 0.42
```

✅ **Disconnected Networks**:
```
4/5 network structures: IPD-NMA undefined
4/5 network structures: Proposed functional
Treatment ranking concordance > 0.8 in disconnected cases
```

✅ **Baseline Superiority**:
```
PEHE Rankings (mean ± std):
1. Proposed: 0.85 ± 0.12 ⭐
2. AIPW: 0.92 ± 0.15
3-7. Others: > 1.0
Friedman p < 0.001, all pairwise p < 0.01
```

If you can show these 3 things → **Strong response to reviewer**

---

## Files to Create (Summary)

### Critical
```
experiments/
  statistical_testing.py          # Q3: Monte Carlo + tests
  disconnected_networks.py        # Q7: Multi-treatment
  comparison_baselines.py         # Q10: All baselines

src/baselines/
  ipw_transport.py               # Q10
  aipw_transport.py              # Q10
  ipd_meta_analysis.py           # Q10
  outcome_regression.py          # Q10

src/
  data_generator_multitreatment.py  # Q7
  evaluation.py (update)             # Q3: Add test functions
```

### High Priority
```
experiments/
  nonlinear_bias.py              # Q5a
  nonlinear_outcome.py           # Q5b
  site_imbalance.py              # Q12
  analytical_validation.py       # Q11

src/
  data_generator_nonlinear.py   # Q5
```

---

## When to Stop

**Bare Minimum** (can submit response):
- ✅ Q3 (100 runs + Friedman test)
- ✅ Q7 (One disconnected example)
- ✅ Q10 (3 baselines: IPW, AIPW, IPD-MA)
- **Time**: 3 weeks

**Safe** (low rejection risk):
- ✅ All Critical (Q3, Q7, Q10 full)
- ✅ Q5a (Non-linear bias)
- **Time**: 5 weeks

**Ideal** (competitive for top venue):
- ✅ All Critical + High Priority
- **Time**: 8 weeks

Choose based on deadline and resources.
