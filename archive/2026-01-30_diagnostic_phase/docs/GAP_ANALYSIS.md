# Gap Analysis: Current Design vs Reviewer Requirements

## Executive Summary

**Status**: Current design (DESIGN.md + ABLATION_TESTS.md) covers ~60% of reviewer requests. **Critical gaps** exist in statistical rigor, non-linear extensions, and explicit disconnected network evaluation.

**Recommendation**: Implement experiments from REVIEWER_EXPERIMENTS.md (Priority 1-3 are essential).

---

## Detailed Gap Analysis by Reviewer Question

### Q1: Conditional Exchangeability (Conceptual)
**Reviewer Concern**: Method doesn't assume conditional exchangeability, so how does it handle unmeasured effect modifiers?

**Current Status**: ✅ ADEQUATE
- DESIGN.md clearly states this is a **working-model estimator**, not causal identification
- Assumptions A4-A6 are regularity conditions, not identification assumptions

**Action Needed**: None (conceptual clarification in response letter)

---

### Q2: Total Variation & Outcome Stability (Theoretical)
**Reviewer Concern**: Original A4 was imprecise (TV distance always ≤ 1, doesn't imply outcome stability)

**Current Status**: ✅ ADDRESSED
- Response letter revises A4 to **Lipschitz continuity** of outcome regressions
- No additional experiments needed

**Action Needed**: Update DESIGN.md Section 3 to reflect revised A4

---

### Q3: Monte Carlo Evaluation & Statistical Testing ⚠️
**Reviewer Concern**: 
- Need many MC runs (not just 20)
- Need statistical hypothesis testing (Friedman test)
- Vary number of covariates

**Current Status**: ❌ INSUFFICIENT

Current ABLATION_TESTS.md says:
```markdown
### 5.1 Core Component Ablations (Priority 1)
- 5 methods × 20 runs
```

**Gaps**:
1. **Too few runs**: 20 → need 100+
2. **No statistical tests**: No Friedman, no Wilcoxon, no p-values
3. **No effect sizes**: No Cohen's d
4. **No covariate dimensionality sweep**: p not varied systematically

**Required**:
- ✅ Experiment 1.1: Monte Carlo with Friedman/Wilcoxon tests (REVIEWER_EXPERIMENTS.md)
- ✅ Experiment 1.2: Covariate dimensionality sweep p ∈ {5, 10, 20, 50, 100}

**Effort**: High (1-2 weeks)
**Priority**: **CRITICAL** - Reviewer explicitly requests this

---

### Q4: Disconnected Target (Conceptual)
**Reviewer Concern**: Claims to estimate without treated arm, but how is β_{1,0} estimated?

**Current Status**: ✅ CLARIFIED
- Response letter explains Option B uses **shared bias assumption** (A6)
- Working-model estimand, not identification

**Action Needed**: Update DESIGN.md to emphasize working-model language

---

### Q5: Restrictive Linear Sparse Bias ⚠️
**Reviewer Concern**: 
- What if transport bias is non-linear or non-sparse?
- Need sensitivity analyses

**Current Status**: ❌ INSUFFICIENT

Current ABLATION_TESTS.md mentions robustness checks:
```markdown
### 4.2 Transport Bias Sparsity (Assumption A5)
true_sparsities = [1, 2, 3, 5, 8, 10, 20]
```

**Gaps**:
1. **Only varies sparsity**, not functional form
2. **No non-linear bias DGPs** (quadratic, interactions, piecewise)
3. **No alternative correction methods** (Ridge, KernelRidge, RF)

**Required**:
- ✅ Experiment 2.1: Non-linear transport bias (REVIEWER_EXPERIMENTS.md)
  - 5 bias forms × 5 correction methods × 50 runs
- ✅ Experiment 2.2: Non-linear outcome models
  - 5 DGPs × 4 proxy models × 50 runs

**Effort**: High (1-2 weeks)
**Priority**: **HIGH** - Directly addresses core assumption

---

### Q6: Shared Support Across Arms (Conceptual)
**Reviewer Concern**: Why do treatment arms share covariate support?

**Current Status**: ✅ CLARIFIED
- Response letter explains this is a **design property of RCTs** (positivity)
- Not a biological assumption

**Action Needed**: None (conceptual clarification)

---

### Q7: Disconnected Networks ⚠️
**Reviewer Concern**: 
- Paper motivates disconnected networks but doesn't evaluate them
- How are they constructed?

**Current Status**: ❌ MISSING

Current ABLATION_TESTS.md:
- No explicit multi-treatment network experiments
- "Disconnected" only means target has no treated arm, not network topology

**Gaps**:
1. **No multi-treatment DGP** (treatments {0, A, B, C})
2. **No network topology variation** (star, chain, disconnected)
3. **No comparison where IPD-NMA fails by design**

**Required**:
- ✅ Experiment 3.1: Multi-treatment disconnected networks (REVIEWER_EXPERIMENTS.md)
  - 5 network structures × 50 runs
  - Show IPD-NMA returns `NaN`, Proposed works

**Effort**: Medium-High (1 week)
**Priority**: **CRITICAL** - Core motivating scenario

---

### Q8: Efficiency & Finite-Sample Bounds (Theoretical)
**Reviewer Concern**: 
- What does √n refer to? (proxy, gold, or total?)
- Need explicit finite-sample error decomposition

**Current Status**: ✅ ADDRESSED (in response letter)
- √N refers to total Stage 3 sample size
- Explicit bound: error ≤ O_p(N^{-1/2}) + δ_proxy·δ_gold + Approx(A5, A6)

**Action Needed**: 
- Update DESIGN.md Section 3.3 to show finite-sample bound
- No new experiments needed

---

### Q9: LASSO Scaling & CV (Implementation)
**Reviewer Concern**: 
- How are covariates standardized?
- How is λ selected with small gold samples?

**Current Status**: ✅ ADDRESSED (in response letter)
- Standardize to mean 0, std 1 within gold sample
- Use repeated K-fold CV with 1-SE rule

**Action Needed**: 
- Update DESIGN.md Section 3.2 to specify standardization
- Add to implementation checklist

---

### Q10: Missing Comparisons ⚠️
**Reviewer Concern**: 
- No comparison against IPW, AIPW, IPD-NMA, outcome regression transport
- Need methods with different assumptions

**Current Status**: ❌ INSUFFICIENT

Current ABLATION_TESTS.md Section 5:
```markdown
### 5. Comparative Baselines (Priority 2)
- IPD-NMA, TMLE Transport, Causal Forest, AIPW, Bastani et al. 2021
```

**Gaps**:
1. **Not implemented** - only listed, no code
2. **No implementation details** for each baseline
3. **No specification of when each method should fail**

**Required**:
- ✅ Experiment 5.1: Comprehensive baseline comparison (REVIEWER_EXPERIMENTS.md)
  - 8 methods × 4 scenarios × 100 runs
  - Full implementations provided

**Effort**: Very High (2-3 weeks)
**Priority**: **CRITICAL** - Reviewer explicitly requests

---

### Q11: Analytical Cross-Arm Degradation ⚠️
**Reviewer Concern**: 
- Can you analytically quantify how error degrades as ρ decreases?
- Not just empirical ρ-sweep

**Current Status**: ⚠️ PARTIAL

Current ABLATION_TESTS.md Section 4.3:
```markdown
### 4.3 Cross-Arm Coupling Strength (Assumption A6)
rho_values = [0.0, 0.3, 0.5, 0.7, 0.9, 0.95, 1.0]
```

**Gaps**:
1. **Only empirical sweep**, no analytical bound validation
2. **No regression** to test linear degradation in (1-ρ)
3. **No comparison** of empirical error to analytical prediction

**Required**:
- ✅ Experiment 6.1: Analytical vs empirical degradation (REVIEWER_EXPERIMENTS.md)
  - Validate bound: error ≤ (1-ρ)||δ₀|| + ||ζ|| + ...
  - Regression to show β > 0, p < 0.001

**Effort**: Medium (3-4 days)
**Priority**: **MEDIUM** - Nice to have, strengthens theory

---

### Q12: Site Imbalance & Error Propagation ⚠️
**Reviewer Concern**: 
- Performance under severe site sample-size imbalance?
- How does error propagate across stages?

**Current Status**: ❌ MISSING

Current ABLATION_TESTS.md:
- No mention of site imbalance
- No explicit error propagation analysis

**Gaps**:
1. **No imbalance experiments** (n_max/n_min ratios)
2. **No decomposition** showing which stage dominates error

**Required**:
- ✅ Experiment 4.1: Site imbalance (REVIEWER_EXPERIMENTS.md)
  - Imbalance ratios ∈ {1, 2, 5, 10, 20, 50}
  - Gold fractions ∈ {0.05, 0.10, 0.20}

**Effort**: Medium (3-4 days)
**Priority**: **MEDIUM** - Good to address

---

## Summary: Critical Gaps

### Must Implement (Rejection Risk if Missing)

1. **Q3: Statistical Testing** ⚠️ CRITICAL
   - 100+ MC runs with Friedman test
   - Covariate dimensionality sweep
   - **Effort**: 1-2 weeks

2. **Q7: Disconnected Networks** ⚠️ CRITICAL
   - Multi-treatment explicit evaluation
   - Show IPD-NMA fails, Proposed works
   - **Effort**: 1 week

3. **Q10: Baseline Comparisons** ⚠️ CRITICAL
   - Implement IPW, AIPW, IPD-NMA, etc.
   - Fair comparison on multiple scenarios
   - **Effort**: 2-3 weeks

### Should Implement (Strengthens Paper)

4. **Q5: Non-Linear Extensions** ⚠️ HIGH
   - Non-linear bias forms
   - Non-linear outcome models
   - **Effort**: 1-2 weeks

5. **Q11: Analytical Degradation** ⚠️ MEDIUM
   - Validate analytical bound
   - Regression analysis
   - **Effort**: 3-4 days

6. **Q12: Site Imbalance** ⚠️ MEDIUM
   - Imbalance ratio sweep
   - Error decomposition
   - **Effort**: 3-4 days

---

## Comparison Table: Current vs Required

| Component | Current Coverage | Reviewer Requirement | Gap Severity | Effort |
|-----------|-----------------|---------------------|-------------|--------|
| **Core Ablations** | ✅ 5 methods, 20 runs | ✅ Same, but 100 runs | ⚠️ Moderate | Low |
| **Statistical Tests** | ❌ None | ✅ Friedman, Wilcoxon, Cohen's d | 🔴 Critical | High |
| **Covariate Dim** | ❌ Fixed p=5 | ✅ Sweep p ∈ [5, 100] | 🔴 Critical | Medium |
| **Non-Linear Bias** | ⚠️ Sparsity only | ✅ 5 forms × 5 corrections | 🟡 High | High |
| **Non-Linear DGP** | ❌ Linear only | ✅ 5 DGPs × 4 models | 🟡 High | Medium |
| **Disconnected Networks** | ❌ Not explicit | ✅ Multi-treatment topology | 🔴 Critical | High |
| **Site Imbalance** | ❌ Not covered | ✅ Imbalance ratios | 🟡 Medium | Medium |
| **Baseline Comparisons** | ⚠️ Listed only | ✅ Implemented + results | 🔴 Critical | Very High |
| **Analytical Degradation** | ⚠️ Empirical only | ✅ + Analytical validation | 🟡 Medium | Medium |

**Legend**: 
- ✅ Adequate | ⚠️ Partial | ❌ Missing
- 🔴 Critical | 🟡 Important | ⚪ Nice-to-have

---

## Recommended Action Plan

### Phase 1: Critical Gaps (4-5 weeks)
**Goal**: Address rejection risks

**Week 1-2**: Statistical Rigor (Q3)
- [ ] Implement 100-run Monte Carlo protocol
- [ ] Add Friedman + Wilcoxon tests to all experiments
- [ ] Covariate dimensionality sweep (p ∈ [5, 100])
- [ ] Generate tables with p-values and effect sizes

**Week 3**: Disconnected Networks (Q7)
- [ ] Implement multi-treatment DGP
- [ ] Create 5 network topologies
- [ ] Run experiments showing IPD-NMA fails
- [ ] Generate network diagrams

**Week 4-5**: Baseline Comparisons (Q10)
- [ ] Implement all 7 baselines (IPW, AIPW, IPD-MA, etc.)
- [ ] Run comprehensive comparison (8 methods × 4 scenarios × 100 runs)
- [ ] Create comparative tables and plots

### Phase 2: Strengthening (2-3 weeks)
**Goal**: Address high-priority extensions

**Week 6-7**: Non-Linear Extensions (Q5)
- [ ] Implement 5 non-linear bias DGPs
- [ ] Test 5 correction methods
- [ ] Implement 5 non-linear outcome DGPs
- [ ] Test 4 proxy model types

**Week 8**: Remaining Items (Q11, Q12)
- [ ] Analytical degradation validation
- [ ] Site imbalance experiments
- [ ] Final visualization suite

---

## Minimum Viable Response

If time is extremely limited, prioritize:

1. **Q3: Statistical Testing** (MUST)
   - 100 runs + Friedman test for core ablations
   - Takes existing experiments, adds rigor
   - **Time**: 3-4 days

2. **Q7: Disconnected Networks** (MUST)
   - One clear multi-treatment example
   - Show IPD-NMA = NaN, Proposed works
   - **Time**: 3-4 days

3. **Q10: Minimal Baselines** (MUST)
   - Implement just IPW, AIPW, IPD-MA (3 baselines)
   - Run on 2 scenarios × 50 runs
   - **Time**: 1 week

**Total Minimum**: 2-3 weeks for bare minimum response

---

## Updated File Structure (After Implementation)

```
Sparse_TL_DR_ICHI2026/
├── README.md
├── DESIGN.md                      # Updated with revised A4, finite-sample bounds
├── ABLATION_TESTS.md              # Original ablation plan
├── REVIEWER_EXPERIMENTS.md        # Additional experiments for reviewer
├── GAP_ANALYSIS.md                # This document
├── requirements.txt
├── src/
│   ├── estimator.py               # Clean implementation
│   ├── data_generator.py          # Updated with multi-treatment, non-linear DGPs
│   ├── baselines.py               # NEW: IPW, AIPW, IPD-MA implementations
│   └── evaluation.py              # Updated with statistical tests
└── experiments/
    ├── ablation_core.py           # Updated: 100 runs, Friedman test
    ├── ablation_nonlinear.py      # NEW: Non-linear bias & DGP
    ├── ablation_disconnected.py   # NEW: Multi-treatment networks
    ├── ablation_imbalance.py      # NEW: Site imbalance
    ├── comparison_baselines.py    # NEW: Comprehensive baselines
    └── validation_analytical.py   # NEW: Analytical bound validation
```

---

## Conclusion

**Current Status**: Design is conceptually sound but **experimentally incomplete** for reviewer standards.

**Recommendation**: 
- **Minimum**: Implement Experiments 1.1, 3.1, 5.1 (Q3, Q7, Q10) - 3 weeks
- **Ideal**: All Priority 1-3 experiments from REVIEWER_EXPERIMENTS.md - 6-8 weeks

**Risk Assessment**:
- Without Q3, Q7, Q10: **High rejection risk**
- Without Q5, Q11, Q12: **Acceptable, but weaker**

The reviewer is asking for **rigorous empirical validation** of a methodologically sound approach. Current design has the right structure but needs more experimental depth.
