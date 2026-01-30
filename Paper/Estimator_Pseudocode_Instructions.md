# Estimator implementation pseudocode + simulation/ablation playbook

## Purpose
Provide implementation-ready pseudocode for a future session to build:
1) the placebo-anchored proxy–gold estimator, 2) its ablations, and 3) simulation scenarios.

---

## Notation summary
- Sites/trials indexed by `c ∈ {0, 1, ..., C}`.
- Target site: `c = 0` with placebo-only outcomes used as **gold labels**.
- Source sites: `c = 1..C` with treated + placebo outcomes used as **proxy labels**.
- Covariates: `X ∈ R^p`.
- Treatment: `A ∈ {0,1}`.
- Outcome: `Y` (continuous primary; optional binary secondary).
- Known/true propensity: `π = P(A=1)` (randomized or modeled).

---

## A. Core estimator pseudocode

### A1) Data assembly
```
INPUT:
  - target dataset D0 = {(Xi, Ai=0, Yi)} for i=1..n0  # placebo-only
  - source datasets Dc for c=1..C with treated+placebo (Ai ∈ {0,1})
  - propensity π (known or estimated)
  - model classes: f0(x), f1(x), g(x)  # outcome models and correction

STEP 1: combine all source data into Dsrc = ⋃_{c=1..C} Dc
STEP 2: split Dsrc into placebo subset Dsrc0 and treated subset Dsrc1
```

### A2) Proxy outcome models (source only)
```
# Fit source outcome models
fit f0_src(x) on Dsrc0:   minimize loss(Y, f0(x))
fit f1_src(x) on Dsrc1:   minimize loss(Y, f1(x))

# Proxy CATE
tau_proxy(x) = f1_src(x) - f0_src(x)
```

### A3) Placebo anchoring (target-only correction)
```
# Use target placebo outcomes to correct baseline risk
# g(x) captures sparse/regularized correction from proxy baseline to target baseline
# g is fit using gold labels only (D0)

fit g(x) to D0:
  minimize loss(Y, f0_src(x) + g(x)) with sparsity/regularization

# anchored baseline
f0_anchor(x) = f0_src(x) + g(x)
```

### A4) Anchored CATE + DR-learner integration
```
# anchored potential outcomes
mu0(x) = f0_anchor(x)
mu1(x) = mu0(x) + tau_proxy(x)

# DR pseudo-outcome (known π)
phi_i = mu1(Xi) - mu0(Xi)
        + Ai * (Yi - mu1(Xi)) / π
        - (1-Ai) * (Yi - mu0(Xi)) / (1-π)

# Fit final CATE model
fit tau_hat(x) on (Xi, phi_i) for all i in Dsrc ∪ D0

OUTPUT:
  - tau_hat(x) CATE estimate
  - mu0(x), mu1(x) potential outcome estimates
  - ATE_hat = mean_x tau_hat(x)
```

---

## B. Ablation variants (define all model switches explicitly)

### B1) No-Transfer
```
# Use only target placebo outcomes
fit f0_target(x) on D0

# No treated data → no CATE extrapolation
# Option: set tau_hat(x)=0 or estimate via a parametric assumption (document clearly)
```

### B2) Proxy-Only (no anchoring)
```
f0 = f0_src
f1 = f1_src
mu0(x) = f0(x)
mu1(x) = f1(x)

# DR learning with proxy models only
construct phi_i using mu0/mu1 on Dsrc (optionally include D0 placebo)
fit tau_hat(x)
```

### B3) Anchor-Only (no transfer of treated outcomes)
```
# Use g(x) correction but no f1_src
fit f0_anchor on D0 using f0_src + g(x)

# No treated proxy model; CATE is not estimated from sources
# Option: tau_hat(x)=0 or a weak prior (document)
```

### B4) Full method (Proposed)
```
# Combine proxy outcome models + placebo anchoring + DR learner
use steps A1–A4
```

### B5) Sensitivity variants
```
- Replace f0/f1 with nonlinear model while g(x) is linear (and vice versa)
- Use estimated π(x) instead of known π
- Drop DR learner; compare to simple plug-in tau_proxy + anchor
```

---

## C. Simulation scenarios (design templates)

### C1) Base multi-site RCT with covariate shift
```
for each site c in 0..C:
  draw site shift δc
  sample covariates X from shifted distribution (mean/scale changes)
  randomize treatment A ~ Bernoulli(0.5)
  generate outcomes:
    mu0(x) = baseline(x; nonlinear terms)
    tau(x) = heterogeneous effect(x; interactions)
    Y = mu0(x) + A * tau(x) + noise(site-specific variance)
```

### C2) Gold-label scarcity
```
fix source sample sizes
vary n0 in {50, 100, 300, 500}
```

### C3) Shift severity
```
low/medium/high shift:
  increase |δc| and variance scaling across sites
```

### C4) Overlap violations
```
truncate target covariates to limited support
measure impact on PEHE/ATE/calibration
```

### C5) Proxy bias
```
add site-level baseline offsets: mu0_c(x) = mu0(x) + b_c
# tests robustness to residual baseline differences
```

### C6) Dimensionality stress test
```
run p ∈ {10, 30, 50, 100}
vary number of effect modifiers and nuisance covariates
```

---

## D. Evaluation protocol pseudocode
```
for each scenario S:
  for r in 1..R Monte Carlo replicates:
    generate data under S
    fit each method variant (No-Transfer, Proxy-Only, Anchor-Only, Proposed)
    compute metrics:
      - PEHE (RMSE of CATE)
      - ATE MAE
      - calibration RMSE for μ0 and μ1
  aggregate metrics: mean, SD, 95% CI
  perform Friedman test across methods per metric
  post-hoc pairwise tests with correction
```

---

## E. Implementation checklist
- [ ] Implement data generator with parameterized shift, overlap, and bias controls.
- [ ] Implement model classes for f0, f1, g, and tau (linear + nonlinear baselines).
- [ ] Implement DR pseudo-outcome pipeline with known/estimated propensities.
- [ ] Implement ablation toggles and scenario runner.
- [ ] Add metric calculators and Monte Carlo aggregation.
- [ ] Produce summary tables + plots (PEHE vs gold labels, vs shift severity, etc.).
