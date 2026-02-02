"""
Comprehensive Evaluation Metrics for CATE Estimation.

Expanded metrics based on reviewer feedback:
1. Point estimation: PEHE, ATE Error, μ calibration
2. Ranking metrics: Spearman/Kendall correlation, Top-k uplift, Qini AUC
3. CATE calibration: Slope/intercept, ECE (Expected Calibration Error)
4. Decision-focused: Policy value, regret
5. Transport-specific: Working-model error, structural bias, M* recovery
6. Uncertainty: Coverage, CI length (if variance estimates available)

Reference: Response to reviewer comment on "metrics limited to RMSE"
"""

import numpy as np
from scipy import stats
from typing import Dict, Optional, Tuple, List
import warnings


# =============================================================================
# 1. BASIC POINT ESTIMATION METRICS
# =============================================================================

def pehe(tau_true: np.ndarray, tau_pred: np.ndarray) -> float:
    """
    Precision in Estimation of Heterogeneous Effects (PEHE).
    
    PEHE = sqrt(E[(τ(x) - τ̂(x))²])
    
    Parameters
    ----------
    tau_true : array-like
        True CATE values
    tau_pred : array-like
        Predicted CATE values
    
    Returns
    -------
    pehe : float
        Root mean squared error of CATE
    """
    return float(np.sqrt(np.mean((tau_true - tau_pred) ** 2)))


def ate_error(tau_true: np.ndarray, tau_pred: np.ndarray) -> float:
    """
    Absolute error in average treatment effect.
    
    ATE_error = |E[τ(x)] - E[τ̂(x)]|
    
    Parameters
    ----------
    tau_true : array-like
        True CATE values
    tau_pred : array-like
        Predicted CATE values
    
    Returns
    -------
    ate_error : float
        Absolute difference in population average
    """
    return float(np.abs(np.mean(tau_true) - np.mean(tau_pred)))


def calibration_rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Root mean squared error for outcome calibration.
    
    Parameters
    ----------
    y_true : array-like
        True outcomes
    y_pred : array-like
        Predicted outcomes
    
    Returns
    -------
    rmse : float
        Root mean squared error
    """
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


# =============================================================================
# 2. RANKING METRICS (Heterogeneity Discovery)
# =============================================================================

def cate_rank_correlation(tau_true: np.ndarray, tau_pred: np.ndarray,
                          method: str = 'spearman') -> Tuple[float, float]:
    """
    Rank correlation between true and predicted CATE.
    
    Tests whether the model correctly ranks patients by treatment benefit,
    which is crucial for prioritization/targeting decisions.
    
    Parameters
    ----------
    tau_true : array-like
        True CATE values
    tau_pred : array-like
        Predicted CATE values
    method : str, default='spearman'
        'spearman' or 'kendall'
    
    Returns
    -------
    correlation : float
        Rank correlation coefficient
    pvalue : float
        Two-sided p-value
    """
    if method == 'spearman':
        corr, pval = stats.spearmanr(tau_true, tau_pred)
    elif method == 'kendall':
        corr, pval = stats.kendalltau(tau_true, tau_pred)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return float(corr), float(pval)


def topk_uplift_capture(tau_true: np.ndarray, tau_pred: np.ndarray,
                        k_fractions: List[float] = [0.1, 0.2, 0.3, 0.5]) -> Dict[str, float]:
    """
    Top-k uplift capture ratio.
    
    For patients with top-k% predicted CATE, compute what fraction of
    the maximum possible uplift is captured.
    
    Ratio = (mean τ in top-k% by τ̂) / (mean τ in top-k% by τ)
    
    When oracle uplift ≤ 0 (harmful treatment regime), the ratio is undefined.
    In this case, we report NaN for ratio but also provide alternative metrics:
    - fraction of positive-τ individuals in top-k
    - absolute captured and oracle values
    
    Use case: Measures targeting efficiency for treatment prioritization.
    
    Parameters
    ----------
    tau_true : array-like
        True CATE values
    tau_pred : array-like
        Predicted CATE values
    k_fractions : list of float
        Fractions to compute (e.g., [0.1, 0.2, 0.3] for top 10%, 20%, 30%)
    
    Returns
    -------
    ratios : dict
        Dictionary with keys like 'topk_10_ratio', 'topk_20_ratio', etc.
        Also includes '_captured', '_oracle', '_frac_positive' for each k.
    """
    n = len(tau_true)
    results = {}
    
    # Overall fraction with positive τ
    results['overall_frac_positive'] = float(np.mean(tau_true > 0))
    
    for k_frac in k_fractions:
        k = max(1, int(n * k_frac))
        key_prefix = f'topk_{int(k_frac * 100)}'
        
        # Top-k by predicted CATE
        pred_topk_idx = np.argsort(tau_pred)[-k:]
        captured = np.mean(tau_true[pred_topk_idx])
        
        # Oracle: top-k by true CATE
        true_topk_idx = np.argsort(tau_true)[-k:]
        oracle = np.mean(tau_true[true_topk_idx])
        
        # Ratio (1.0 = perfect, <1.0 = suboptimal targeting)
        # Handle oracle ≤ 0 cases
        if oracle > 1e-10:
            ratio = captured / oracle
        elif oracle < -1e-10:
            # Negative oracle: ratio is misleading, report NaN
            # (higher captured could be "worse" in harmful treatment scenario)
            ratio = np.nan
        else:
            # Oracle ≈ 0: check if captured is also ≈ 0
            ratio = 1.0 if np.abs(captured) < 1e-10 else np.nan
        
        results[f'{key_prefix}_ratio'] = float(ratio) if not np.isnan(ratio) else np.nan
        
        # Absolute values (always reported)
        results[f'{key_prefix}_captured'] = float(captured)
        results[f'{key_prefix}_oracle'] = float(oracle)
        
        # Alternative metric: fraction of positive-τ individuals captured in top-k
        # This is interpretable even when oracle uplift is negative
        frac_positive_in_topk = np.mean(tau_true[pred_topk_idx] > 0)
        results[f'{key_prefix}_frac_positive'] = float(frac_positive_in_topk)
        
        # Oracle fraction positive in top-k (for comparison)
        frac_positive_oracle = np.mean(tau_true[true_topk_idx] > 0)
        results[f'{key_prefix}_frac_positive_oracle'] = float(frac_positive_oracle)
    
    return results


def qini_auc(tau_true: np.ndarray, tau_pred: np.ndarray,
             n_points: int = 100) -> float:
    """
    Oracle Qini / Uplift curve AUC (simulation metric).
    
    NOTE: This is an "oracle Qini" that uses true τ(x) values, which are only
    available in simulation. It differs from the classical empirical Qini used
    in observational evaluation (based on treatment/control outcome differences
    within score bins). Use this for synthetic experiments only.
    
    The Qini curve plots cumulative treatment effect gained when treating
    the top fraction of patients sorted by predicted CATE.
    
    AUC normalized to [0, 1] where 1 = perfect ranking.
    
    Parameters
    ----------
    tau_true : array-like
        True CATE values (known in simulation)
    tau_pred : array-like
        Predicted CATE values
    n_points : int, default=100
        Number of points on the curve
    
    Returns
    -------
    auc : float
        Area under the oracle Qini curve (normalized)
    """
    n = len(tau_true)
    
    # Sort by predicted CATE (descending)
    sort_idx = np.argsort(tau_pred)[::-1]
    tau_sorted = tau_true[sort_idx]
    
    # Cumulative uplift
    cum_uplift_pred = np.cumsum(tau_sorted)
    
    # Oracle: sort by true CATE
    oracle_idx = np.argsort(tau_true)[::-1]
    tau_oracle = tau_true[oracle_idx]
    cum_uplift_oracle = np.cumsum(tau_oracle)
    
    # Random baseline
    cum_uplift_random = np.cumsum(np.ones(n)) * np.mean(tau_true)
    
    # Qini coefficient (area above random, normalized by oracle)
    # AUC for predicted (use trapezoid for numpy >= 2.0 compatibility)
    fractions = np.linspace(0, 1, n)
    try:
        # NumPy >= 2.0
        auc_pred = np.trapezoid(cum_uplift_pred, fractions) / n
        auc_oracle = np.trapezoid(cum_uplift_oracle, fractions) / n
        auc_random = np.trapezoid(cum_uplift_random, fractions) / n
    except AttributeError:
        # NumPy < 2.0
        auc_pred = np.trapz(cum_uplift_pred, fractions) / n
        auc_oracle = np.trapz(cum_uplift_oracle, fractions) / n
        auc_random = np.trapz(cum_uplift_random, fractions) / n
    
    # Normalized: (pred - random) / (oracle - random)
    if auc_oracle - auc_random > 0:
        qini = (auc_pred - auc_random) / (auc_oracle - auc_random)
    else:
        qini = 1.0 if np.allclose(tau_true, tau_pred) else 0.0
    
    return float(np.clip(qini, 0, 1))


# =============================================================================
# 3. CATE CALIBRATION METRICS
# =============================================================================

def cate_calibration_slope_intercept(tau_true: np.ndarray, 
                                      tau_pred: np.ndarray,
                                      degeneracy_threshold: float = 1e-10) -> Tuple[float, float, float, bool]:
    """
    CATE calibration slope and intercept via linear regression.
    
    Fits: τ_true = α + β·τ̂_pred + noise
    
    Ideal: α ≈ 0 (no systematic bias), β ≈ 1 (correct scaling)
    
    Degeneracy handling: If Var(τ̂) < threshold, the regression is ill-conditioned.
    In this case, we return slope=0, intercept=mean(τ), R²=0, and flag as degenerate.
    
    Parameters
    ----------
    tau_true : array-like
        True CATE values
    tau_pred : array-like
        Predicted CATE values
    degeneracy_threshold : float, default=1e-10
        Variance threshold below which predictions are considered constant
    
    Returns
    -------
    intercept : float
        Calibration intercept α (ideal = 0)
    slope : float
        Calibration slope β (ideal = 1)
    r_squared : float
        R² of calibration regression
    degenerate : bool
        True if predictions were (near) constant
    """
    pred_var = np.var(tau_pred)
    
    # Check for degenerate (near-constant) predictions
    if pred_var < degeneracy_threshold:
        # Degenerate: τ̂ is constant, regression is undefined
        # Return sensible defaults: slope=0 (no discrimination), 
        # intercept = mean(τ_true) (best constant predictor)
        return float(np.mean(tau_true)), 0.0, 0.0, True
    
    # Simple linear regression
    X = np.column_stack([np.ones(len(tau_pred)), tau_pred])
    try:
        coeffs, residuals, rank, s = np.linalg.lstsq(X, tau_true, rcond=None)
        intercept = coeffs[0]
        slope = coeffs[1]
    except np.linalg.LinAlgError:
        # Fallback for numerical issues
        return float(np.mean(tau_true)), 0.0, 0.0, True
    
    # R²
    ss_res = np.sum((tau_true - (intercept + slope * tau_pred)) ** 2)
    ss_tot = np.sum((tau_true - np.mean(tau_true)) ** 2)
    
    if ss_tot < degeneracy_threshold:
        # τ_true is also constant
        r_squared = 1.0 if ss_res < degeneracy_threshold else 0.0
    else:
        r_squared = 1 - ss_res / ss_tot
    
    return float(intercept), float(slope), float(r_squared), False


def cate_ece(tau_true: np.ndarray, tau_pred: np.ndarray,
             n_bins: int = 10) -> Tuple[float, float, Dict]:
    """
    Expected Calibration Error (ECE) for CATE.
    
    Bins predictions by τ̂ and computes average calibration error
    weighted by bin size.
    
    ECE = Σ_b (n_b / n) · |E[τ | τ̂ ∈ bin_b] - E[τ̂ | τ̂ ∈ bin_b]|
    
    Parameters
    ----------
    tau_true : array-like
        True CATE values
    tau_pred : array-like
        Predicted CATE values
    n_bins : int, default=10
        Number of bins
    
    Returns
    -------
    ece : float
        Expected calibration error
    mce : float
        Maximum calibration error (across bins)
    bin_info : dict
        Detailed bin information for reliability diagram
    """
    n = len(tau_true)
    
    # Check for degenerate predictions (constant τ̂)
    pred_var = np.var(tau_pred)
    if pred_var < 1e-10:
        # Degenerate: all predictions identical
        mean_error = np.abs(np.mean(tau_true) - np.mean(tau_pred))
        return float(mean_error), float(mean_error), {
            'bin_centers': [float(np.mean(tau_pred))],
            'mean_true': [float(np.mean(tau_true))],
            'mean_pred': [float(np.mean(tau_pred))],
            'bin_counts': [n],
            'bin_errors': [float(mean_error)],
            'degenerate': True
        }
    
    # Compute percentile-based bin edges
    bin_edges = np.percentile(tau_pred, np.linspace(0, 100, n_bins + 1))
    
    # Handle duplicate edges (many identical predictions)
    # De-duplicate by using unique edges, then pad back to n_bins+1 if needed
    unique_edges = np.unique(bin_edges)
    if len(unique_edges) < n_bins + 1:
        # Fall back to uniform bins between min and max
        min_pred, max_pred = np.min(tau_pred), np.max(tau_pred)
        if min_pred == max_pred:
            # All predictions identical (should be caught above, but safety)
            mean_error = np.abs(np.mean(tau_true) - np.mean(tau_pred))
            return float(mean_error), float(mean_error), {
                'bin_centers': [float(np.mean(tau_pred))],
                'mean_true': [float(np.mean(tau_true))],
                'mean_pred': [float(np.mean(tau_pred))],
                'bin_counts': [n],
                'bin_errors': [float(mean_error)],
                'degenerate': True
            }
        bin_edges = np.linspace(min_pred, max_pred, n_bins + 1)
    
    # Extend edges to capture all values
    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf
    
    # FIX: np.digitize with bin_edges gives indices in [0, n_bins]
    # We want indices in [0, n_bins-1]
    # np.digitize(x, bins) returns i such that bins[i-1] <= x < bins[i]
    # So we use all edges and subtract 1, then clip
    bin_indices = np.digitize(tau_pred, bin_edges[1:-1])  # Use interior edges
    # Now indices are in [0, n_bins-1]: 0 for x < edge[1], n_bins-1 for x >= edge[-2]
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)
    
    bin_info = {
        'bin_centers': [],
        'mean_true': [],
        'mean_pred': [],
        'bin_counts': [],
        'bin_errors': [],
        'degenerate': False
    }
    
    ece = 0.0
    mce = 0.0
    
    for b in range(n_bins):
        mask = (bin_indices == b)
        n_b = np.sum(mask)
        
        if n_b > 0:
            mean_true_b = np.mean(tau_true[mask])
            mean_pred_b = np.mean(tau_pred[mask])
            error_b = np.abs(mean_true_b - mean_pred_b)
            
            ece += (n_b / n) * error_b
            mce = max(mce, error_b)
            
            # Compute bin center (handle -inf edge)
            if np.isinf(bin_edges[b]):
                center = bin_edges[b + 1]
            elif np.isinf(bin_edges[b + 1]):
                center = bin_edges[b]
            else:
                center = (bin_edges[b] + bin_edges[b + 1]) / 2
            
            bin_info['bin_centers'].append(float(center))
            bin_info['mean_true'].append(float(mean_true_b))
            bin_info['mean_pred'].append(float(mean_pred_b))
            bin_info['bin_counts'].append(int(n_b))
            bin_info['bin_errors'].append(float(error_b))
    
    return float(ece), float(mce), bin_info


# =============================================================================
# 4. DECISION-FOCUSED METRICS (Policy Value / Regret)
# =============================================================================

def policy_value(tau_pred: np.ndarray, mu0_true: np.ndarray, mu1_true: np.ndarray,
                 threshold: float = 0.0, top_fraction: Optional[float] = None) -> float:
    """
    Value of treatment policy based on predicted CATE.
    
    Policy: π̂(x) = 1{τ̂(x) > threshold} or treat top fraction
    
    V(π̂) = E[μ₀(X) + π̂(X)·τ(X)]
    
    Parameters
    ----------
    tau_pred : array-like
        Predicted CATE values
    mu0_true : array-like
        True μ₀ values (baseline potential outcome)
    mu1_true : array-like
        True μ₁ values (treated potential outcome)
    threshold : float, default=0.0
        Treatment threshold (treat if τ̂ > threshold)
    top_fraction : float, optional
        If provided, treat top fraction instead of using threshold
    
    Returns
    -------
    value : float
        Expected outcome under the policy
    """
    tau_true = mu1_true - mu0_true
    n = len(tau_pred)
    
    if top_fraction is not None:
        k = max(1, int(n * top_fraction))
        treat_idx = np.argsort(tau_pred)[-k:]
        policy = np.zeros(n)
        policy[treat_idx] = 1
    else:
        policy = (tau_pred > threshold).astype(float)
    
    value = np.mean(mu0_true + policy * tau_true)
    return float(value)


def policy_regret(tau_pred: np.ndarray, mu0_true: np.ndarray, mu1_true: np.ndarray,
                  threshold: float = 0.0, top_fraction: Optional[float] = None) -> float:
    """
    Regret of treatment policy vs oracle optimal.
    
    Regret = V(π*) - V(π̂)
    
    IMPORTANT: Oracle must match the policy class!
    - For threshold policy: π* = 1{τ(x) > 0}
    - For top-k policy: π* = top-k by TRUE τ (budgeted oracle)
    
    Parameters
    ----------
    tau_pred : array-like
        Predicted CATE values
    mu0_true : array-like
        True μ₀ values
    mu1_true : array-like
        True μ₁ values
    threshold : float, default=0.0
        Treatment threshold
    top_fraction : float, optional
        If provided, treat top fraction (uses BUDGETED oracle)
    
    Returns
    -------
    regret : float
        Regret (can be negative if estimated > oracle due to noise)
    """
    tau_true = mu1_true - mu0_true
    n = len(tau_pred)
    
    # FIX: Oracle must match the same policy class
    if top_fraction is not None:
        # BUDGETED oracle: top-k by TRUE τ
        k = max(1, int(n * top_fraction))
        topk_true_idx = np.argsort(tau_true)[-k:]
        oracle_policy = np.zeros(n, dtype=float)
        oracle_policy[topk_true_idx] = 1.0
    else:
        # Unconstrained oracle: treat if τ > 0
        oracle_policy = (tau_true > 0).astype(float)
    
    v_oracle = float(np.mean(mu0_true + oracle_policy * tau_true))
    
    # Estimated policy value
    v_estimated = policy_value(tau_pred, mu0_true, mu1_true, threshold, top_fraction)
    
    regret = v_oracle - v_estimated
    # NOTE: Not clamping to 0 - negative regret indicates implementation issue
    return float(regret)


def policy_diagnostics(tau_pred: np.ndarray, mu0_true: np.ndarray, mu1_true: np.ndarray,
                       threshold: float = 0.0, top_fraction: Optional[float] = None) -> Dict[str, float]:
    """
    Diagnostic statistics for policy evaluation.
    
    Helps explain "worse PEHE but better regret" phenomenon:
    - If oracle treats few (treat_rate_oracle near 0), a pessimistic model
      that also treats few can have low regret despite bad PEHE.
    
    Parameters
    ----------
    tau_pred : array-like
        Predicted CATE values
    mu0_true : array-like
        True μ₀ values
    mu1_true : array-like  
        True μ₁ values
    threshold : float, default=0.0
        Treatment threshold
    top_fraction : float, optional
        If provided, treat top fraction
    
    Returns
    -------
    diagnostics : dict
        - treat_rate_hat: E[π̂(X)] - fraction treated by learned policy
        - treat_rate_oracle: E[π*(X)] - fraction treated by oracle
        - avg_tau_among_hat_treated: E[τ | π̂=1] - mean effect among treated
        - avg_tau_among_oracle_treated: E[τ | π*=1] - mean effect among oracle treated
    """
    tau_true = mu1_true - mu0_true
    n = len(tau_pred)
    
    # Learned policy
    if top_fraction is not None:
        k = max(1, int(n * top_fraction))
        treat_idx = np.argsort(tau_pred)[-k:]
        pi_hat = np.zeros(n, dtype=float)
        pi_hat[treat_idx] = 1.0
    else:
        pi_hat = (tau_pred > threshold).astype(float)
    
    # Oracle policy (matching policy class)
    if top_fraction is not None:
        k = max(1, int(n * top_fraction))
        topk_true_idx = np.argsort(tau_true)[-k:]
        pi_star = np.zeros(n, dtype=float)
        pi_star[topk_true_idx] = 1.0
    else:
        pi_star = (tau_true > 0).astype(float)
    
    treat_rate_hat = float(pi_hat.mean())
    treat_rate_star = float(pi_star.mean())
    
    # Average uplift among treated
    avg_tau_treated = float(tau_true[pi_hat == 1].mean()) if treat_rate_hat > 0 else np.nan
    avg_tau_oracle_treated = float(tau_true[pi_star == 1].mean()) if treat_rate_star > 0 else np.nan
    
    return {
        "treat_rate_hat": treat_rate_hat,
        "treat_rate_oracle": treat_rate_star,
        "avg_tau_among_hat_treated": avg_tau_treated,
        "avg_tau_among_oracle_treated": avg_tau_oracle_treated,
    }


def policy_metrics(tau_pred: np.ndarray, mu0_true: np.ndarray, mu1_true: np.ndarray,
                   top_fractions: List[float] = [0.1, 0.3, 0.5]) -> Dict[str, float]:
    """
    Comprehensive policy metrics with diagnostics.
    
    Returns
    -------
    metrics : dict
        Value/regret metrics:
        - value_treat_positive: Value of treating τ̂ > 0
        - regret_treat_positive: Regret vs oracle (can be negative)
        - value_topk_X: Value of treating top X%
        - regret_topk_X: Regret vs BUDGETED oracle at top X%
        
        Diagnostics (explain "worse PEHE but better regret"):
        - treat_rate_hat: Fraction treated by learned policy
        - treat_rate_oracle: Fraction treated by oracle
        - avg_tau_treated: Mean true effect among those treated
    """
    tau_true = mu1_true - mu0_true
    n = len(tau_pred)
    
    metrics = {}
    
    # Policy: treat if τ̂ > 0
    metrics['value_treat_positive'] = policy_value(tau_pred, mu0_true, mu1_true, threshold=0.0)
    metrics['regret_treat_positive'] = policy_regret(tau_pred, mu0_true, mu1_true, threshold=0.0)
    
    # Oracle value (unconstrained: treat if τ > 0)
    oracle_policy = (tau_true > 0).astype(float)
    metrics['value_oracle'] = float(np.mean(mu0_true + oracle_policy * tau_true))
    
    # Treat-all and treat-none baselines
    metrics['value_treat_all'] = float(np.mean(mu1_true))
    metrics['value_treat_none'] = float(np.mean(mu0_true))
    
    # Diagnostics for treat-positive policy (explains inversions)
    diag = policy_diagnostics(tau_pred, mu0_true, mu1_true, threshold=0.0)
    metrics['treat_rate_hat'] = diag['treat_rate_hat']
    metrics['treat_rate_oracle'] = diag['treat_rate_oracle']
    metrics['avg_tau_among_treated'] = diag['avg_tau_among_hat_treated']
    
    # Top-k policies with BUDGETED oracle
    for frac in top_fractions:
        key = int(frac * 100)
        metrics[f'value_top{key}'] = policy_value(tau_pred, mu0_true, mu1_true, top_fraction=frac)
        # NOTE: regret now uses budgeted oracle (top-k by true τ)
        metrics[f'regret_top{key}'] = policy_regret(tau_pred, mu0_true, mu1_true, top_fraction=frac)
    
    return metrics


# =============================================================================
# 5. TRANSPORT-SPECIFIC DIAGNOSTICS (Unique to this paper)
# =============================================================================

def working_model_vs_structural_bias(tau_pred: np.ndarray, 
                                      tau_target: np.ndarray,
                                      tau_working: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Decompose CATE error into working-model error vs structural bias.
    
    From paper appendix:
        |τ̂ - τ₀| ≤ |τ̂ - τ*| + |τ* - τ₀|
    
    where τ* is the working-model target (from A5/A6 structure).
    
    Parameters
    ----------
    tau_pred : array-like
        Predicted CATE (τ̂)
    tau_target : array-like
        True target CATE (τ₀)
    tau_working : array-like, optional
        Working-model CATE (τ*). If not provided, uses tau_target.
    
    Returns
    -------
    diagnostics : dict
        - total_error: |τ̂ - τ₀|
        - working_model_error: |τ̂ - τ*|
        - structural_bias: |τ* - τ₀|
    """
    if tau_working is None:
        tau_working = tau_target  # No structural bias in this case
    
    total_error = np.sqrt(np.mean((tau_pred - tau_target) ** 2))
    working_error = np.sqrt(np.mean((tau_pred - tau_working) ** 2))
    structural_bias = np.sqrt(np.mean((tau_working - tau_target) ** 2))
    
    return {
        'total_error': float(total_error),
        'working_model_error': float(working_error),
        'structural_bias': float(structural_bias)
    }


def step_b_operator_quality(M_hat: np.ndarray, M_star: np.ndarray) -> Dict[str, float]:
    """
    Evaluate quality of Step B operator estimation.
    
    Parameters
    ----------
    M_hat : array-like, shape (p, p)
        Estimated transfer operator
    M_star : array-like, shape (p, p)
        True transfer operator (from DGP)
    
    Returns
    -------
    metrics : dict
        - frobenius_error: ||M̂ - M*||_F
        - operator_error: ||M̂ - M*||_op (spectral norm)
        - relative_error: ||M̂ - M*||_F / ||M*||_F
        - cosine_similarity: correlation between flattened M̂ and M*
    """
    diff = M_hat - M_star
    
    frob_error = np.linalg.norm(diff, 'fro')
    op_error = np.linalg.norm(diff, 2)  # Spectral norm
    
    M_star_norm = np.linalg.norm(M_star, 'fro')
    relative_error = frob_error / M_star_norm if M_star_norm > 1e-10 else np.inf
    
    # Cosine similarity
    flat_hat = M_hat.flatten()
    flat_star = M_star.flatten()
    if np.linalg.norm(flat_hat) > 1e-10 and np.linalg.norm(flat_star) > 1e-10:
        cosine = np.dot(flat_hat, flat_star) / (np.linalg.norm(flat_hat) * np.linalg.norm(flat_star))
    else:
        cosine = 0.0
    
    return {
        'frobenius_error': float(frob_error),
        'operator_error': float(op_error),
        'relative_error': float(relative_error),
        'cosine_similarity': float(cosine)
    }


def correction_quality(beta_hat: np.ndarray, beta_true: np.ndarray,
                       name: str = 'beta') -> Dict[str, float]:
    """
    Evaluate quality of sparse correction estimation.
    
    Parameters
    ----------
    beta_hat : array-like, shape (p,)
        Estimated correction coefficients
    beta_true : array-like, shape (p,)
        True correction coefficients (from DGP)
    name : str
        Name prefix for metrics
    
    Returns
    -------
    metrics : dict
        - {name}_l2_error: ||β̂ - β||₂
        - {name}_support_recall: fraction of true support recovered
        - {name}_support_precision: fraction of estimated support that's true
    """
    l2_error = np.linalg.norm(beta_hat - beta_true)
    
    # Support recovery
    true_support = set(np.where(np.abs(beta_true) > 1e-6)[0])
    est_support = set(np.where(np.abs(beta_hat) > 1e-6)[0])
    
    if len(true_support) > 0:
        recall = len(true_support & est_support) / len(true_support)
    else:
        recall = 1.0 if len(est_support) == 0 else 0.0
    
    if len(est_support) > 0:
        precision = len(true_support & est_support) / len(est_support)
    else:
        precision = 1.0 if len(true_support) == 0 else 0.0
    
    return {
        f'{name}_l2_error': float(l2_error),
        f'{name}_support_recall': float(recall),
        f'{name}_support_precision': float(precision)
    }


def transfer_prediction_error(model, source_betas: Dict[int, Tuple[np.ndarray, np.ndarray]]) -> Dict[str, float]:
    """
    Step B transfer prediction error across source sites.
    
    Computes: (1/C) Σ_c ||M̂·β̂_{0,c} - β̂_{1,c}||₂
    
    Parameters
    ----------
    model : fitted estimator with M_hat_
        Needs M_hat_ attribute
    source_betas : dict
        Mapping site_id -> (beta0_c, beta1_c) tuples
    
    Returns
    -------
    metrics : dict
        - mean_transfer_error: Average prediction error
        - max_transfer_error: Maximum prediction error
    """
    if not hasattr(model, 'M_hat_') or model.M_hat_ is None:
        return {'mean_transfer_error': np.nan, 'max_transfer_error': np.nan}
    
    M_hat = model.M_hat_
    errors = []
    
    for site_id, (beta0, beta1) in source_betas.items():
        predicted = M_hat @ beta0
        error = np.linalg.norm(predicted - beta1)
        errors.append(error)
    
    return {
        'mean_transfer_error': float(np.mean(errors)) if errors else np.nan,
        'max_transfer_error': float(np.max(errors)) if errors else np.nan
    }


# =============================================================================
# 6. UNCERTAINTY / INFERENCE METRICS
# =============================================================================

def coverage_and_length(tau_pred: np.ndarray, tau_true: np.ndarray,
                        se_pred: np.ndarray, alpha: float = 0.05) -> Dict[str, float]:
    """
    Coverage and length of confidence intervals.
    
    Parameters
    ----------
    tau_pred : array-like
        Predicted CATE values
    tau_true : array-like
        True CATE values
    se_pred : array-like
        Standard errors of predictions
    alpha : float, default=0.05
        Significance level (0.05 for 95% CI)
    
    Returns
    -------
    metrics : dict
        - coverage: Empirical coverage (should be ≈ 1-alpha)
        - avg_length: Average CI length
        - median_length: Median CI length
    """
    z = stats.norm.ppf(1 - alpha / 2)
    
    lower = tau_pred - z * se_pred
    upper = tau_pred + z * se_pred
    
    covered = (tau_true >= lower) & (tau_true <= upper)
    coverage = np.mean(covered)
    
    lengths = upper - lower
    
    return {
        'coverage': float(coverage),
        'avg_length': float(np.mean(lengths)),
        'median_length': float(np.median(lengths))
    }


def standardized_residuals(tau_pred: np.ndarray, tau_true: np.ndarray,
                           se_pred: np.ndarray) -> Dict[str, float]:
    """
    Standardized residual diagnostics.
    
    Z = (τ̂ - τ) / SE
    
    Should have mean ≈ 0, variance ≈ 1 if properly calibrated.
    
    Parameters
    ----------
    tau_pred : array-like
        Predicted CATE values
    tau_true : array-like
        True CATE values (or working-model target τ*)
    se_pred : array-like
        Standard errors of predictions
    
    Returns
    -------
    metrics : dict
        - z_mean: Mean of Z (should be ≈ 0)
        - z_var: Variance of Z (should be ≈ 1)
        - z_skew: Skewness of Z (should be ≈ 0)
    """
    z = (tau_pred - tau_true) / np.maximum(se_pred, 1e-10)
    
    return {
        'z_mean': float(np.mean(z)),
        'z_var': float(np.var(z)),
        'z_skew': float(stats.skew(z))
    }


# =============================================================================
# COMPREHENSIVE EVALUATION FUNCTIONS
# =============================================================================

def evaluate_cate_model(model, X_test: np.ndarray, tau_true: np.ndarray,
                        mu0_true: Optional[np.ndarray] = None,
                        mu1_true: Optional[np.ndarray] = None,
                        compute_calibration: bool = False,
                        compute_ranking: bool = True,
                        compute_policy: bool = True) -> Dict[str, float]:
    """
    Comprehensive evaluation of CATE model.
    
    Parameters
    ----------
    model : estimator
        Fitted model with predict() method
    X_test : array-like
        Test covariates
    tau_true : array-like
        True CATE values
    mu0_true : array-like, optional
        True μ₀ values for calibration and policy metrics
    mu1_true : array-like, optional
        True μ₁ values for calibration and policy metrics
    compute_calibration : bool, default=False
        Whether to compute outcome calibration (μ₀, μ₁ RMSE)
    compute_ranking : bool, default=True
        Whether to compute ranking metrics
    compute_policy : bool, default=True
        Whether to compute policy metrics (requires μ₀, μ₁)
    
    Returns
    -------
    metrics : dict
        Comprehensive evaluation metrics
    """
    # Predict CATE
    tau_pred = model.predict(X_test)
    
    # Basic metrics (always computed)
    metrics = {
        'pehe': pehe(tau_true, tau_pred),
        'ate_error': ate_error(tau_true, tau_pred)
    }
    
    # Ranking metrics
    if compute_ranking:
        corr, pval = cate_rank_correlation(tau_true, tau_pred, method='spearman')
        metrics['spearman_corr'] = corr
        metrics['spearman_pval'] = pval
        
        topk = topk_uplift_capture(tau_true, tau_pred, [0.1, 0.3])
        metrics['topk_10_ratio'] = topk['topk_10_ratio']
        metrics['topk_30_ratio'] = topk['topk_30_ratio']
        
        metrics['qini_auc'] = qini_auc(tau_true, tau_pred)
    
    # CATE calibration
    intercept, slope, r2, calib_degenerate = cate_calibration_slope_intercept(tau_true, tau_pred)
    metrics['calib_intercept'] = intercept
    metrics['calib_slope'] = slope
    metrics['calib_r2'] = r2
    metrics['calib_degenerate'] = calib_degenerate
    
    ece, mce, _ = cate_ece(tau_true, tau_pred)
    metrics['cate_ece'] = ece
    metrics['cate_mce'] = mce
    
    # Outcome calibration (μ₀, μ₁ RMSE)
    if compute_calibration and hasattr(model, 'proxy_models_'):
        if mu0_true is not None:
            mu0_pred = model.proxy_models_[0].predict(X_test)
            if hasattr(model, 'delta_0_global_'):
                mu0_pred = mu0_pred + model.delta_0_global_.predict(X_test)
            elif hasattr(model, 'delta_0_'):
                mu0_pred = mu0_pred + model.delta_0_.predict(X_test)
            metrics['mu0_rmse'] = calibration_rmse(mu0_true, mu0_pred)
        
        if mu1_true is not None:
            mu1_pred = model.proxy_models_[1].predict(X_test)
            if hasattr(model, 'delta_1_global_'):
                mu1_pred = mu1_pred + model.delta_1_global_.predict(X_test)
            elif hasattr(model, 'delta_1_'):
                mu1_pred = mu1_pred + model.delta_1_.predict(X_test)
            metrics['mu1_rmse'] = calibration_rmse(mu1_true, mu1_pred)
    
    # Policy metrics
    if compute_policy and mu0_true is not None and mu1_true is not None:
        policy = policy_metrics(tau_pred, mu0_true, mu1_true, top_fractions=[0.3])
        metrics['policy_regret'] = policy['regret_treat_positive']
        metrics['policy_value'] = policy['value_treat_positive']
        metrics['policy_value_top30'] = policy['value_top30']
        metrics['policy_regret_top30'] = policy['regret_top30']
    
    return metrics


def evaluate_with_dgp(model, target_data: Dict, generator,
                      compute_transport: bool = True) -> Dict[str, float]:
    """
    Full evaluation using DGP ground truth including transport-specific metrics.
    
    Parameters
    ----------
    model : estimator
        Fitted model
    target_data : dict
        Target data with 'X', 'tau_true', 'mu0_true', 'mu1_true'
    generator : SyntheticRCTGenerator
        DGP generator for accessing M*, β, etc.
    compute_transport : bool, default=True
        Whether to compute transport-specific diagnostics
    
    Returns
    -------
    metrics : dict
        All evaluation metrics including transport diagnostics
    """
    X = target_data['X']
    tau_true = target_data['tau_true']
    mu0_true = target_data['mu0_true']
    mu1_true = target_data['mu1_true']
    
    # Basic + ranking + policy metrics
    metrics = evaluate_cate_model(
        model, X, tau_true, mu0_true, mu1_true,
        compute_calibration=True,
        compute_ranking=True,
        compute_policy=True
    )
    
    # Transport-specific diagnostics
    if compute_transport and hasattr(model, 'M_hat_') and model.M_hat_ is not None:
        # M* quality
        M_star = generator.M_star
        m_metrics = step_b_operator_quality(model.M_hat_, M_star)
        metrics.update({f'M_{k}': v for k, v in m_metrics.items()})
        
        # Target correction quality
        if hasattr(model, 'delta_0_global_'):
            beta0_true = generator.beta0[0]  # Target
            if hasattr(model.delta_0_global_, 'coef_'):
                beta0_hat = model.delta_0_global_.coef_
            elif hasattr(model.delta_0_global_, 'named_steps'):
                beta0_hat = model.delta_0_global_.named_steps['lasso'].coef_
            else:
                beta0_hat = np.zeros_like(beta0_true)
            
            corr_metrics = correction_quality(beta0_hat, beta0_true, 'delta0')
            metrics.update(corr_metrics)
    
    return metrics


# =============================================================================
# PRINTING / REPORTING UTILITIES
# =============================================================================

def print_metrics(metrics: Dict[str, float], method_name: str = "Model"):
    """Pretty print evaluation metrics."""
    print(f"\n{method_name} Performance:")
    print("-" * 50)
    
    # Core metrics
    print(f"  PEHE:            {metrics['pehe']:.4f}")
    print(f"  ATE Error:       {metrics['ate_error']:.4f}")
    
    # Ranking
    if 'spearman_corr' in metrics:
        print(f"  Spearman ρ:      {metrics['spearman_corr']:.4f}")
    if 'qini_auc' in metrics:
        print(f"  Qini AUC:        {metrics['qini_auc']:.4f}")
    
    # Calibration
    if 'calib_slope' in metrics:
        print(f"  Calib Slope:     {metrics['calib_slope']:.4f} (ideal=1)")
        print(f"  Calib Intercept: {metrics['calib_intercept']:.4f} (ideal=0)")
    if 'cate_ece' in metrics:
        print(f"  CATE ECE:        {metrics['cate_ece']:.4f}")
    
    # Policy
    if 'policy_regret' in metrics:
        print(f"  Policy Regret:   {metrics['policy_regret']:.4f}")
    
    # Outcome calibration
    if 'mu0_rmse' in metrics:
        print(f"  μ₀ RMSE:         {metrics['mu0_rmse']:.4f}")
    if 'mu1_rmse' in metrics:
        print(f"  μ₁ RMSE:         {metrics['mu1_rmse']:.4f}")
    
    # Transport
    if 'M_frobenius_error' in metrics:
        print(f"  ||M̂-M*||_F:      {metrics['M_frobenius_error']:.4f}")
    if 'delta0_l2_error' in metrics:
        print(f"  ||δ̂₀-δ₀||₂:      {metrics['delta0_l2_error']:.4f}")


def compare_methods(results: Dict[str, Dict[str, float]], 
                    metrics_to_show: Optional[List[str]] = None) -> None:
    """
    Compare multiple methods and print formatted table.
    
    Parameters
    ----------
    results : dict
        Dictionary mapping method names to metric dictionaries
    metrics_to_show : list, optional
        Which metrics to display (default: core set)
    """
    if metrics_to_show is None:
        metrics_to_show = ['pehe', 'ate_error', 'spearman_corr', 'cate_ece', 'policy_regret']
    
    methods = list(results.keys())
    
    # Filter to available metrics
    available_metrics = set()
    for m in methods:
        available_metrics.update(results[m].keys())
    metrics_to_show = [m for m in metrics_to_show if m in available_metrics]
    
    # Header
    print("\n" + "=" * 100)
    print("Method Comparison")
    print("=" * 100)
    header = f"{'Method':<25} " + " ".join([f"{m:>12}" for m in metrics_to_show])
    print(header)
    print("-" * 100)
    
    # Rows
    for method in methods:
        values = []
        for m in metrics_to_show:
            if m in results[method]:
                values.append(f"{results[method][m]:>12.4f}")
            else:
                values.append(f"{'N/A':>12}")
        print(f"{method:<25} " + " ".join(values))
    
    print("=" * 100)
    
    # Find best for each metric
    print("\nBest Performance:")
    for metric in metrics_to_show:
        valid_methods = [m for m in methods if metric in results[m] and not np.isnan(results[m][metric])]
        if valid_methods:
            # Lower is better for error metrics, higher for correlation/ratio
            higher_is_better = metric in ['spearman_corr', 'kendall_corr', 'qini_auc', 
                                          'topk_10_ratio', 'topk_30_ratio', 'calib_slope',
                                          'policy_value', 'coverage']
            if higher_is_better:
                best_method = max(valid_methods, key=lambda m: results[m][metric])
            else:
                best_method = min(valid_methods, key=lambda m: results[m][metric])
            best_value = results[best_method][metric]
            direction = "↑" if higher_is_better else "↓"
            print(f"  {metric} {direction}: {best_method} ({best_value:.4f})")


def create_metrics_summary_table(results: Dict[str, Dict[str, float]],
                                  include_ranking: bool = True,
                                  include_calibration: bool = True,
                                  include_policy: bool = True) -> str:
    """
    Create a formatted table suitable for LaTeX/paper.
    
    Returns markdown table string.
    """
    methods = list(results.keys())
    
    # Define metric groups
    core = ['pehe', 'ate_error']
    ranking = ['spearman_corr', 'qini_auc'] if include_ranking else []
    calibration = ['calib_slope', 'cate_ece'] if include_calibration else []
    policy = ['policy_regret'] if include_policy else []
    
    all_metrics = core + ranking + calibration + policy
    
    # Filter available
    available = set()
    for m in methods:
        available.update(results[m].keys())
    all_metrics = [m for m in all_metrics if m in available]
    
    # Create markdown table
    lines = []
    lines.append("| Method | " + " | ".join(all_metrics) + " |")
    lines.append("|" + "---|" * (len(all_metrics) + 1))
    
    for method in methods:
        row = f"| {method} |"
        for metric in all_metrics:
            if metric in results[method]:
                row += f" {results[method][metric]:.4f} |"
            else:
                row += " N/A |"
        lines.append(row)
    
    return "\n".join(lines)


# =============================================================================
# CSV I/O Functions
# =============================================================================

def save_results_csv(results: Dict[str, Dict[str, float]], 
                     filepath: str,
                     include_timestamp: bool = True) -> str:
    """
    Save evaluation results to a CSV file.
    
    Parameters
    ----------
    results : dict
        Dictionary mapping method names to metric dictionaries.
    filepath : str
        Output file path (will add .csv if not present).
    include_timestamp : bool
        Whether to include a timestamp column.
        
    Returns
    -------
    str
        The actual filepath written to.
    """
    import csv
    from datetime import datetime
    
    if not filepath.endswith('.csv'):
        filepath = filepath + '.csv'
    
    # Collect all metrics across all methods
    all_metrics = set()
    for method_results in results.values():
        all_metrics.update(method_results.keys())
    all_metrics = sorted(all_metrics)
    
    # Write CSV
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        header = ['method']
        if include_timestamp:
            header.append('timestamp')
        header.extend(all_metrics)
        writer.writerow(header)
        
        # Rows
        timestamp = datetime.now().isoformat() if include_timestamp else None
        for method, metrics in results.items():
            row = [method]
            if include_timestamp:
                row.append(timestamp)
            for metric in all_metrics:
                val = metrics.get(metric, np.nan)
                # Handle nan and format floats
                if isinstance(val, (int, float)):
                    if np.isnan(val):
                        row.append('')
                    else:
                        row.append(f'{val:.6f}')
                else:
                    row.append(str(val))
            writer.writerow(row)
    
    return filepath


def load_results_csv(filepath: str) -> Dict[str, Dict[str, float]]:
    """
    Load evaluation results from a CSV file.
    
    Parameters
    ----------
    filepath : str
        Path to the CSV file.
        
    Returns
    -------
    dict
        Dictionary mapping method names to metric dictionaries.
    """
    import csv
    
    results = {}
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            method = row.pop('method')
            row.pop('timestamp', None)  # Remove timestamp if present
            
            # Convert values to floats where possible
            metrics = {}
            for key, val in row.items():
                if val == '' or val is None:
                    metrics[key] = np.nan
                else:
                    try:
                        metrics[key] = float(val)
                    except ValueError:
                        metrics[key] = val
            
            results[method] = metrics
    
    return results


def append_results_csv(results: Dict[str, Dict[str, float]], 
                       filepath: str,
                       experiment_name: str = None) -> str:
    """
    Append results to an existing CSV file (creates if doesn't exist).
    
    Useful for accumulating results across multiple runs/experiments.
    
    Parameters
    ----------
    results : dict
        Dictionary mapping method names to metric dictionaries.
    filepath : str
        Output file path.
    experiment_name : str, optional
        Name/identifier for this experiment run.
        
    Returns
    -------
    str
        The filepath written to.
    """
    import csv
    import os
    from datetime import datetime
    
    if not filepath.endswith('.csv'):
        filepath = filepath + '.csv'
    
    # Collect all metrics
    all_metrics = set()
    for method_results in results.values():
        all_metrics.update(method_results.keys())
    all_metrics = sorted(all_metrics)
    
    # Check if file exists to determine if we need header
    file_exists = os.path.exists(filepath)
    
    with open(filepath, 'a', newline='') as f:
        writer = csv.writer(f)
        
        # Header if new file
        if not file_exists:
            header = ['experiment', 'method', 'timestamp'] + list(all_metrics)
            writer.writerow(header)
        
        # Rows
        timestamp = datetime.now().isoformat()
        for method, metrics in results.items():
            row = [experiment_name or '', method, timestamp]
            for metric in all_metrics:
                val = metrics.get(metric, np.nan)
                if isinstance(val, (int, float)):
                    if np.isnan(val):
                        row.append('')
                    else:
                        row.append(f'{val:.6f}')
                else:
                    row.append(str(val))
            writer.writerow(row)
    
    return filepath


# =============================================================================
# Plotting Functions
# =============================================================================

# Standardized color palette for methods
# Uses colorblind-friendly colors from matplotlib's tab10
METHOD_COLORS = {
    # No-Transfer baseline (red - worst)
    'No-Transfer': '#d62728',      # Red
    'NoTransfer': '#d62728',
    'No Transfer': '#d62728',
    
    # Proxy-Only baseline (orange)
    'Proxy-Only': '#ff7f0e',       # Orange  
    'ProxyOnly': '#ff7f0e',
    'Proxy Only': '#ff7f0e',
    
    # Anchor-Only baseline (blue)
    'Anchor-Only': '#1f77b4',      # Blue
    'AnchorOnly': '#1f77b4',
    'Anchor Only': '#1f77b4',
    
    # Proposed methods (greens - shades differentiate A vs B)
    'Proposed': '#2ca02c',         # Green (dark) - generic
    'Proposed-A': '#2ca02c',       # Green (dark) - Option A
    'Proposed (A)': '#2ca02c',
    'ProposedA': '#2ca02c',
    'Proposed-B': '#98df8a',       # Green (light) - Option B
    'Proposed (B)': '#98df8a',
    'ProposedB': '#98df8a',
    'ProposedB_LinearStepB': '#98df8a',  # Green (light)
    'Proposed-B (StepB)': '#98df8a',
    'ProposedB_KernelStepB': '#c7e9c0',  # Green (very light)
    
    # Transport/IPD baselines
    'IPD_RE': '#e377c2',           # Pink
    'AIPWTransport': '#7f7f7f',    # Gray
    'AIPW Transport': '#7f7f7f',
    'EntropyBalancing': '#bcbd22', # Yellow-green
    
    # CATE learners
    'DRLearner_PooledWithSite': '#17becf',  # Cyan
    'DRLearner_PooledNoSite': '#aec7e8',    # Light blue
    'TARNet': '#9467bd',           # Purple
    'T-Learner': '#d62728',        # Red
    'S-Learner': '#9467bd',        # Purple
    'X-Learner': '#8c564b',        # Brown
    'DR-Learner': '#e377c2',       # Pink
    'CATE-RF': '#bcbd22',          # Yellow-green
    'Oracle': '#17becf',           # Cyan
}

# Fallback colors for unknown methods
_FALLBACK_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
]


def get_method_colors(methods: List[str]) -> List[str]:
    """
    Get standardized colors for a list of methods.
    
    Parameters
    ----------
    methods : list
        List of method names.
        
    Returns
    -------
    list
        List of color hex codes in same order as methods.
    """
    colors = []
    fallback_idx = 0
    used_fallbacks = set()
    
    for method in methods:
        if method in METHOD_COLORS:
            colors.append(METHOD_COLORS[method])
        else:
            # Try partial matching
            matched = False
            for key, color in METHOD_COLORS.items():
                if key.lower() in method.lower() or method.lower() in key.lower():
                    colors.append(color)
                    matched = True
                    break
            
            if not matched:
                # Use fallback color
                while fallback_idx < len(_FALLBACK_COLORS):
                    if _FALLBACK_COLORS[fallback_idx] not in used_fallbacks:
                        colors.append(_FALLBACK_COLORS[fallback_idx])
                        used_fallbacks.add(_FALLBACK_COLORS[fallback_idx])
                        fallback_idx += 1
                        break
                    fallback_idx += 1
                else:
                    # Ran out of fallbacks, cycle
                    colors.append(_FALLBACK_COLORS[len(colors) % len(_FALLBACK_COLORS)])
    
    return colors


def plot_comparison_bars(results: Dict[str, Dict[str, float]],
                         metrics: List[str] = None,
                         figsize: Tuple[int, int] = (12, 5),
                         title: str = "Method Comparison",
                         save_path: str = None,
                         show: bool = True) -> 'matplotlib.figure.Figure':
    """
    Create bar chart comparing methods across metrics.
    
    Parameters
    ----------
    results : dict
        Dictionary mapping method names to metric dictionaries.
    metrics : list, optional
        List of metrics to plot. If None, uses ['pehe', 'ate_error', 'spearman_corr'].
    figsize : tuple
        Figure size (width, height).
    title : str
        Plot title.
    save_path : str, optional
        Path to save the figure.
    show : bool
        Whether to display the plot.
        
    Returns
    -------
    matplotlib.figure.Figure
        The figure object.
    """
    import matplotlib.pyplot as plt
    
    if metrics is None:
        metrics = ['pehe', 'ate_error', 'spearman_corr', 'policy_regret']
    
    # Filter to available metrics
    available = set()
    for r in results.values():
        available.update(r.keys())
    metrics = [m for m in metrics if m in available]
    
    methods = list(results.keys())
    n_metrics = len(metrics)
    n_methods = len(methods)
    
    fig, axes = plt.subplots(1, n_metrics, figsize=figsize)
    if n_metrics == 1:
        axes = [axes]
    
    # Use standardized color palette
    colors = get_method_colors(methods)
    
    # Metrics where higher is better
    higher_better = {'spearman_corr', 'kendall_corr', 'qini_auc', 
                     'topk_uplift_ratio', 'calib_r2', 'policy_value',
                     'policy_value_top30', 'cosine_similarity',
                     'support_recall', 'support_precision', 'coverage'}
    
    for ax, metric in zip(axes, metrics):
        values = [results[m].get(metric, np.nan) for m in methods]
        bars = ax.bar(range(n_methods), values, color=colors)
        
        ax.set_xticks(range(n_methods))
        ax.set_xticklabels(methods, rotation=45, ha='right', fontsize=9)
        
        direction = "↑" if metric in higher_better else "↓"
        ax.set_title(f"{metric} {direction}", fontsize=11)
        ax.set_ylabel(metric)
        
        # Highlight best
        valid_values = [v for v in values if not np.isnan(v)]
        if valid_values:
            if metric in higher_better:
                best_idx = values.index(max(valid_values))
            else:
                best_idx = values.index(min(valid_values))
            bars[best_idx].set_edgecolor('red')
            bars[best_idx].set_linewidth(2)
        
        ax.grid(axis='y', alpha=0.3)
    
    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        
    if show:
        plt.show()
    else:
        plt.close(fig)
    
    return fig


def plot_metrics_heatmap(results: Dict[str, Dict[str, float]],
                         metrics: List[str] = None,
                         normalize: bool = True,
                         figsize: Tuple[int, int] = (10, 6),
                         title: str = "Metrics Heatmap",
                         save_path: str = None,
                         show: bool = True) -> 'matplotlib.figure.Figure':
    """
    Create a heatmap of methods vs metrics.
    
    Parameters
    ----------
    results : dict
        Dictionary mapping method names to metric dictionaries.
    metrics : list, optional
        List of metrics to include.
    normalize : bool
        Whether to normalize metrics to [0,1] for comparison.
    figsize : tuple
        Figure size.
    title : str
        Plot title.
    save_path : str, optional
        Path to save the figure.
    show : bool
        Whether to display the plot.
        
    Returns
    -------
    matplotlib.figure.Figure
        The figure object.
    """
    import matplotlib.pyplot as plt
    
    if metrics is None:
        metrics = ['pehe', 'ate_error', 'spearman_corr', 'qini_auc', 
                   'cate_ece', 'policy_regret']
    
    # Filter to available
    available = set()
    for r in results.values():
        available.update(r.keys())
    metrics = [m for m in metrics if m in available]
    
    methods = list(results.keys())
    
    # Build matrix
    matrix = np.zeros((len(methods), len(metrics)))
    for i, method in enumerate(methods):
        for j, metric in enumerate(metrics):
            matrix[i, j] = results[method].get(metric, np.nan)
    
    # Metrics where higher is better (flip sign for normalization)
    higher_better = {'spearman_corr', 'kendall_corr', 'qini_auc', 
                     'topk_uplift_ratio', 'calib_r2', 'policy_value'}
    
    if normalize:
        # Normalize each column, flipping higher-is-better metrics
        norm_matrix = np.zeros_like(matrix)
        for j, metric in enumerate(metrics):
            col = matrix[:, j]
            valid_mask = ~np.isnan(col)
            if valid_mask.sum() > 0:
                col_min = col[valid_mask].min()
                col_max = col[valid_mask].max()
                if col_max > col_min:
                    normalized = (col - col_min) / (col_max - col_min)
                    # For higher-is-better, flip so lower (green) is better
                    if metric not in higher_better:
                        normalized = 1 - normalized
                    else:
                        pass  # Keep as is, higher stays higher
                    norm_matrix[:, j] = normalized
                else:
                    norm_matrix[:, j] = 0.5
        matrix = norm_matrix
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Use reversed colormap so green = good (low = good after transform)
    cmap = 'RdYlGn' if normalize else 'viridis'
    im = ax.imshow(matrix, cmap=cmap, aspect='auto')
    
    ax.set_xticks(range(len(metrics)))
    ax.set_xticklabels(metrics, rotation=45, ha='right')
    ax.set_yticks(range(len(methods)))
    ax.set_yticklabels(methods)
    
    # Color the y-tick labels with standardized method colors
    method_colors = get_method_colors(methods)
    for i, (label, color) in enumerate(zip(ax.get_yticklabels(), method_colors)):
        label.set_color(color)
        label.set_fontweight('bold')
    
    # Add values
    for i in range(len(methods)):
        for j in range(len(metrics)):
            val = results[methods[i]].get(metrics[j], np.nan)
            if not np.isnan(val):
                color = 'white' if matrix[i, j] < 0.5 else 'black'
                ax.text(j, i, f'{val:.3f}', ha='center', va='center', 
                       color=color, fontsize=9)
    
    plt.colorbar(im, ax=ax, label='Normalized Score (green=better)' if normalize else 'Value')
    ax.set_title(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        
    if show:
        plt.show()
    else:
        plt.close(fig)
    
    return fig


def plot_radar_chart(results: Dict[str, Dict[str, float]],
                     metrics: List[str] = None,
                     figsize: Tuple[int, int] = (8, 8),
                     title: str = "Method Comparison Radar",
                     save_path: str = None,
                     show: bool = True) -> 'matplotlib.figure.Figure':
    """
    Create a radar/spider chart comparing methods.
    
    All metrics are normalized to [0,1] where 1 = best.
    
    Parameters
    ----------
    results : dict
        Dictionary mapping method names to metric dictionaries.
    metrics : list, optional
        List of metrics to include on radar.
    figsize : tuple
        Figure size.
    title : str
        Plot title.
    save_path : str, optional
        Path to save the figure.
    show : bool
        Whether to display the plot.
        
    Returns
    -------
    matplotlib.figure.Figure
        The figure object.
    """
    import matplotlib.pyplot as plt
    
    if metrics is None:
        metrics = ['pehe', 'spearman_corr', 'qini_auc', 'cate_ece', 'policy_regret']
    
    # Filter to available
    available = set()
    for r in results.values():
        available.update(r.keys())
    metrics = [m for m in metrics if m in available]
    
    if len(metrics) < 3:
        raise ValueError("Need at least 3 metrics for radar chart")
    
    methods = list(results.keys())
    n_metrics = len(metrics)
    
    # Metrics where higher is better
    higher_better = {'spearman_corr', 'kendall_corr', 'qini_auc', 
                     'topk_uplift_ratio', 'calib_r2', 'policy_value'}
    
    # Normalize metrics to [0, 1] where 1 = best
    normalized = {method: [] for method in methods}
    
    for metric in metrics:
        values = [results[m].get(metric, np.nan) for m in methods]
        valid = [v for v in values if not np.isnan(v)]
        
        if valid:
            min_val, max_val = min(valid), max(valid)
            for i, method in enumerate(methods):
                val = values[i]
                if np.isnan(val):
                    norm_val = 0
                elif max_val == min_val:
                    norm_val = 1
                else:
                    norm_val = (val - min_val) / (max_val - min_val)
                    # Flip if lower is better
                    if metric not in higher_better:
                        norm_val = 1 - norm_val
                normalized[method].append(norm_val)
        else:
            for method in methods:
                normalized[method].append(0)
    
    # Radar chart
    angles = np.linspace(0, 2 * np.pi, n_metrics, endpoint=False).tolist()
    angles += angles[:1]  # Complete the loop
    
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))
    
    # Use standardized color palette
    colors = get_method_colors(methods)
    
    for i, method in enumerate(methods):
        values = normalized[method] + normalized[method][:1]  # Complete loop
        ax.plot(angles, values, 'o-', linewidth=2, label=method, color=colors[i])
        ax.fill(angles, values, alpha=0.15, color=colors[i])
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, size=10)
    ax.set_ylim(0, 1)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(['0.25', '0.50', '0.75', '1.00'], size=8)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    ax.set_title(title, fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        
    if show:
        plt.show()
    else:
        plt.close(fig)
    
    return fig


def plot_metric_by_parameter(sweep_results: List[Dict],
                             param_name: str,
                             metric: str = 'pehe',
                             methods: List[str] = None,
                             figsize: Tuple[int, int] = (10, 6),
                             title: str = None,
                             save_path: str = None,
                             show: bool = True) -> 'matplotlib.figure.Figure':
    """
    Plot a metric vs a swept parameter for multiple methods.
    
    Parameters
    ----------
    sweep_results : list
        List of dicts, each with 'param_value' and 'results' keys.
        'results' maps method names to metric dicts.
    param_name : str
        Name of the swept parameter (for axis label).
    metric : str
        Which metric to plot.
    methods : list, optional
        Which methods to include. If None, uses all.
    figsize : tuple
        Figure size.
    title : str, optional
        Plot title.
    save_path : str, optional
        Path to save the figure.
    show : bool
        Whether to display the plot.
        
    Returns
    -------
    matplotlib.figure.Figure
        The figure object.
    """
    import matplotlib.pyplot as plt
    
    if methods is None:
        methods = list(sweep_results[0]['results'].keys())
    
    param_values = [r['param_value'] for r in sweep_results]
    
    fig, ax = plt.subplots(figsize=figsize)
    
    # Use standardized color palette
    colors = get_method_colors(methods)
    
    for i, method in enumerate(methods):
        metric_values = []
        for r in sweep_results:
            if method in r['results']:
                metric_values.append(r['results'][method].get(metric, np.nan))
            else:
                metric_values.append(np.nan)
        
        ax.plot(param_values, metric_values, 'o-', label=method, 
                color=colors[i], linewidth=2, markersize=8)
    
    ax.set_xlabel(param_name, fontsize=12)
    ax.set_ylabel(metric, fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    if title:
        ax.set_title(title, fontsize=14, fontweight='bold')
    else:
        ax.set_title(f'{metric} vs {param_name}', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        
    if show:
        plt.show()
    else:
        plt.close(fig)
    
    return fig


def save_all_plots(results: Dict[str, Dict[str, float]],
                   output_dir: str,
                   prefix: str = "results",
                   formats: List[str] = ['png', 'pdf'],
                   show: bool = False) -> List[str]:
    """
    Save all standard plots to a directory.
    
    Parameters
    ----------
    results : dict
        Dictionary mapping method names to metric dictionaries.
    output_dir : str
        Directory to save plots.
    prefix : str
        Filename prefix.
    formats : list
        List of formats to save (e.g., ['png', 'pdf']).
    show : bool
        Whether to display plots.
        
    Returns
    -------
    list
        List of saved file paths.
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    saved_files = []
    
    # Bar chart
    for fmt in formats:
        path = os.path.join(output_dir, f"{prefix}_bars.{fmt}")
        plot_comparison_bars(results, save_path=path, show=show)
        saved_files.append(path)
    
    # Heatmap
    for fmt in formats:
        path = os.path.join(output_dir, f"{prefix}_heatmap.{fmt}")
        plot_metrics_heatmap(results, save_path=path, show=show)
        saved_files.append(path)
    
    # Radar chart
    try:
        for fmt in formats:
            path = os.path.join(output_dir, f"{prefix}_radar.{fmt}")
            plot_radar_chart(results, save_path=path, show=show)
            saved_files.append(path)
    except ValueError:
        pass  # Not enough metrics for radar
    
    return saved_files


def generate_results_report(results: Dict[str, Dict[str, float]],
                            output_dir: str,
                            experiment_name: str = "experiment",
                            dgp_config: Dict = None,
                            save_plots: bool = True,
                            embed_images: bool = True,
                            embed_csv: bool = True,
                            include_methodology: bool = True) -> str:
    """
    Generate a complete results report with CSV, plots, and markdown summary.
    
    Parameters
    ----------
    results : dict
        Dictionary mapping method names to metric dictionaries.
    output_dir : str
        Directory to save all outputs.
    experiment_name : str
        Name of the experiment.
    dgp_config : dict, optional
        DGP configuration to include in report.
    save_plots : bool
        Whether to generate and save plots.
    embed_images : bool
        Whether to embed images in markdown (vs just linking).
    embed_csv : bool
        Whether to embed full CSV content in markdown.
    include_methodology : bool
        Whether to include DGP, estimator, and metric descriptions.
        
    Returns
    -------
    str
        Path to the markdown summary file.
    """
    import os
    from datetime import datetime
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Save CSV
    csv_path = os.path.join(output_dir, f"{experiment_name}.csv")
    save_results_csv(results, csv_path, include_timestamp=False)
    
    # Save plots (prefer png for embedding)
    plot_files = []
    plot_files_png = {}
    if save_plots:
        # Save both PNG and PDF
        for fmt in ['png', 'pdf']:
            from metrics import plot_comparison_bars, plot_metrics_heatmap, plot_radar_chart
            
            bars_path = os.path.join(output_dir, f"{experiment_name}_bars.{fmt}")
            plot_comparison_bars(results, save_path=bars_path, show=False)
            plot_files.append(bars_path)
            if fmt == 'png':
                plot_files_png['bars'] = os.path.basename(bars_path)
            
            heatmap_path = os.path.join(output_dir, f"{experiment_name}_heatmap.{fmt}")
            plot_metrics_heatmap(results, save_path=heatmap_path, show=False)
            plot_files.append(heatmap_path)
            if fmt == 'png':
                plot_files_png['heatmap'] = os.path.basename(heatmap_path)
            
            try:
                radar_path = os.path.join(output_dir, f"{experiment_name}_radar.{fmt}")
                plot_radar_chart(results, save_path=radar_path, show=False)
                plot_files.append(radar_path)
                if fmt == 'png':
                    plot_files_png['radar'] = os.path.basename(radar_path)
            except ValueError:
                pass  # Not enough metrics for radar
    
    # Generate markdown report
    md_path = os.path.join(output_dir, f"{experiment_name}_report.md")
    
    # Find best method for key metrics
    higher_better = {'spearman_corr', 'qini_auc', 'policy_value'}
    
    def find_best(metric):
        valid = {m: r.get(metric, np.nan) for m, r in results.items()}
        valid = {m: v for m, v in valid.items() if not np.isnan(v)}
        if not valid:
            return "N/A", np.nan
        if metric in higher_better:
            best = max(valid.items(), key=lambda x: x[1])
        else:
            best = min(valid.items(), key=lambda x: x[1])
        return best
    
    with open(md_path, 'w') as f:
        f.write(f"# Results Report: {experiment_name}\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Table of Contents
        f.write("## Table of Contents\n\n")
        toc_num = 1
        f.write(f"{toc_num}. [Summary](#summary)\n"); toc_num += 1
        if include_methodology:
            f.write(f"{toc_num}. [Data Generating Process (DGP)](#data-generating-process-dgp)\n"); toc_num += 1
            f.write(f"{toc_num}. [Estimators](#estimators)\n"); toc_num += 1
            f.write(f"{toc_num}. [Metric Definitions](#metric-definitions)\n"); toc_num += 1
        if dgp_config:
            f.write(f"{toc_num}. [Experiment Configuration](#experiment-configuration)\n"); toc_num += 1
        f.write(f"{toc_num}. [Results Table](#results-table)\n"); toc_num += 1
        f.write(f"{toc_num}. [Visualizations](#visualizations)\n"); toc_num += 1
        f.write(f"{toc_num}. [Raw Data](#raw-data)\n")
        f.write("\n---\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        f.write("### Best Methods by Metric\n\n")
        f.write("| Metric | Direction | Best Method | Value |\n")
        f.write("|--------|-----------|-------------|-------|\n")
        for metric in ['pehe', 'ate_error', 'spearman_corr', 'qini_auc', 'cate_ece', 'policy_regret']:
            best_method, best_val = find_best(metric)
            if isinstance(best_val, float) and not np.isnan(best_val):
                direction = "↑ higher" if metric in higher_better else "↓ lower"
                f.write(f"| {metric} | {direction} | **{best_method}** | {best_val:.4f} |\n")
        f.write("\n")
        
        # Methodology sections
        if include_methodology:
            # DGP Description
            f.write("---\n\n")
            f.write("## Data Generating Process (DGP)\n\n")
            f.write("The synthetic data follows a multi-site RCT structure with transfer learning assumptions.\n\n")
            f.write("### Mathematical Formulation\n\n")
            f.write("For each site $c \\in \\{0, 1, ..., C\\}$ (where $c=0$ is the target site):\n\n")
            f.write("**Covariates:**\n")
            f.write("$$X_c \\sim \\mathcal{N}(\\mu_c, \\Sigma_c)$$\n\n")
            f.write("**Potential Outcome Model (Assumption A5):**\n")
            f.write("$$\\mu_{a,c}(x) = \\mu_a^{\\text{proxy}}(x) + \\delta_{a,c}(x) + r_{a,c}(x)$$\n\n")
            f.write("Where:\n")
            f.write("- $\\mu_a^{\\text{proxy}}(x) = x^\\top b_a$ — shared proxy regression (learned from sources)\n")
            f.write("- $\\delta_{a,c}(x) = x^\\top \\beta_{a,c}$ — sparse site-specific correction in class $\\mathcal{D}$\n")
            f.write("- $r_{a,c}(x)$ — residual misspecification (small)\n\n")
            f.write("**Cross-Arm Transfer (Assumption A6):**\n")
            f.write("$$\\beta_{1,c} = M^* \\beta_{0,c} + \\nu_c$$\n\n")
            f.write("Where:\n")
            f.write("- $M^*$ — low-rank transfer operator (shared across sites)\n")
            f.write("- $\\nu_c$ — site-specific non-transfer component\n\n")
            f.write("**Observed Outcome:**\n")
            f.write("$$Y = \\mu_{0,c}(X) + A \\cdot \\tau_c(X) + \\varepsilon, \\quad \\varepsilon \\sim \\mathcal{N}(0, \\sigma^2)$$\n\n")
            f.write("**True CATE:**\n")
            f.write("$$\\tau_c(x) = \\mu_{1,c}(x) - \\mu_{0,c}(x)$$\n\n")
            
            # Estimator Descriptions
            f.write("---\n\n")
            f.write("## Estimators\n\n")
            
            f.write("### No-Transfer Baseline\n\n")
            f.write("Predicts the global average treatment effect (ATE) from source data for all individuals:\n")
            f.write("$$\\hat{\\tau}(x) = \\bar{Y}_1^{\\text{source}} - \\bar{Y}_0^{\\text{source}}$$\n\n")
            f.write("This baseline ignores heterogeneity and individual covariates.\n\n")
            
            f.write("### Proxy-Only Baseline\n\n")
            f.write("Trains outcome models on pooled source data and applies directly to target:\n")
            f.write("$$\\hat{\\tau}^{\\text{proxy}}(x) = \\hat{\\mu}_1^{\\text{proxy}}(x) - \\hat{\\mu}_0^{\\text{proxy}}(x)$$\n\n")
            f.write("Where $\\hat{\\mu}_a^{\\text{proxy}}$ is trained on all source sites. ")
            f.write("This ignores site-specific deviations $\\delta_{a,c}$.\n\n")
            
            f.write("### Anchor-Only Baseline\n\n")
            f.write("Uses target data only to estimate CATE via T-Learner:\n")
            f.write("$$\\hat{\\tau}^{\\text{anchor}}(x) = \\hat{\\mu}_1^{\\text{target}}(x) - \\hat{\\mu}_0^{\\text{target}}(x)$$\n\n")
            f.write("Where $\\hat{\\mu}_a^{\\text{target}}$ is trained exclusively on target site data.\n\n")
            
            f.write("### Proposed: Placebo-Anchored DR-Learner\n\n")
            f.write("A three-stage doubly-robust estimator that combines proxy models with target corrections:\n\n")
            f.write("**Stage 1 (Proxy):** Train $\\hat{\\mu}_a^{\\text{proxy}}(x)$ on pooled source data.\n\n")
            f.write("**Stage 2 (Correction):** Learn sparse corrections on target site:\n")
            f.write("$$\\hat{\\delta}_{a,0}(x) = x^\\top \\hat{\\beta}_{a,0}$$\n")
            f.write("by regressing residuals $(Y - \\hat{\\mu}_a^{\\text{proxy}}(X))$ on $X$ using LASSO.\n\n")
            f.write("- **Option A:** Estimate $\\hat{\\beta}_{0,0}$ from target placebo and $\\hat{\\beta}_{1,0}$ from target treated.\n")
            f.write("- **Option B:** Estimate $\\hat{\\beta}_{0,0}$ from target placebo and use transfer: $\\hat{\\beta}_{1,0} = \\hat{M} \\hat{\\beta}_{0,0}$\n\n")
            f.write("**Stage 3 (DR-Learner):** Compute doubly-robust pseudo-outcomes with cross-fitting:\n")
            f.write("$$\\psi_i = \\hat{\\tau}(X_i) + \\frac{A_i - \\hat{e}(X_i)}{\\hat{e}(X_i)(1-\\hat{e}(X_i))} \\cdot (Y_i - \\hat{\\mu}_{A_i}(X_i))$$\n\n")
            f.write("Where:\n")
            f.write("- $\\hat{\\tau}(x) = [\\hat{\\mu}_1^{\\text{proxy}}(x) + \\hat{\\delta}_{1,0}(x)] - [\\hat{\\mu}_0^{\\text{proxy}}(x) + \\hat{\\delta}_{0,0}(x)]$\n")
            f.write("- $\\hat{e}(x)$ is the propensity score (clipped to $[\\epsilon, 1-\\epsilon]$)\n\n")
            f.write("Final CATE estimate from regressing $\\psi_i$ on $X_i$.\n\n")
            
            # Metric Definitions
            f.write("---\n\n")
            f.write("## Metric Definitions\n\n")
            
            f.write("### Accuracy Metrics\n\n")
            f.write("**PEHE (Precision in Estimation of Heterogeneous Effects):**\n")
            f.write("$$\\text{PEHE} = \\sqrt{\\frac{1}{n} \\sum_{i=1}^n (\\hat{\\tau}(x_i) - \\tau(x_i))^2}$$\n\n")
            f.write("Root mean squared error of CATE predictions. *Lower is better.*\n\n")
            
            f.write("**ATE Error:**\n")
            f.write("$$\\text{ATE Error} = |\\bar{\\hat{\\tau}} - \\bar{\\tau}|$$\n\n")
            f.write("Absolute error in average treatment effect. *Lower is better.*\n\n")
            
            f.write("### Ranking Metrics\n\n")
            f.write("**Spearman Correlation ($\\rho$):**\n")
            f.write("$$\\rho = 1 - \\frac{6 \\sum d_i^2}{n(n^2-1)}$$\n\n")
            f.write("Where $d_i$ is the difference in ranks between $\\hat{\\tau}(x_i)$ and $\\tau(x_i)$. ")
            f.write("Measures monotonic relationship. *Higher is better* (range: $[-1, 1]$).\n\n")
            
            f.write("**Qini AUC:**\n")
            f.write("$$\\text{Qini AUC} = \\int_0^1 \\frac{\\text{Uplift}(t)}{\\text{Uplift}_{\\text{oracle}}(t)} dt$$\n\n")
            f.write("Area under the Qini curve, normalized by oracle performance. ")
            f.write("Measures quality of treatment prioritization. *Higher is better* (range: $[0, 1]$).\n\n")
            
            f.write("**Top-k Uplift Ratio:**\n")
            f.write("$$\\text{Top-}k\\text{ Ratio} = \\frac{\\sum_{i \\in \\text{top-}k(\\hat{\\tau})} \\tau(x_i)}{\\sum_{i \\in \\text{top-}k(\\tau)} \\tau(x_i)}$$\n\n")
            f.write("Fraction of oracle uplift captured by treating top $k\\%$ by predicted CATE. *Higher is better.*\n\n")
            
            f.write("### Calibration Metrics\n\n")
            f.write("**Calibration Slope & Intercept:**\n")
            f.write("From regressing true CATE on predicted: $\\tau = \\alpha + \\beta \\cdot \\hat{\\tau} + \\epsilon$\n\n")
            f.write("- *Ideal:* $\\alpha = 0$ (intercept), $\\beta = 1$ (slope)\n\n")
            
            f.write("**ECE (Expected Calibration Error):**\n")
            f.write("$$\\text{ECE} = \\sum_{b=1}^B \\frac{|B_b|}{n} |\\bar{\\tau}_{B_b} - \\bar{\\hat{\\tau}}_{B_b}|$$\n\n")
            f.write("Average absolute difference between true and predicted CATE within bins. *Lower is better.*\n\n")
            
            f.write("### Policy Metrics\n\n")
            f.write("**Policy Value:**\n")
            f.write("$$V(\\hat{\\pi}) = \\frac{1}{n} \\sum_{i=1}^n [\\mu_0(x_i) + \\hat{\\pi}(x_i) \\cdot \\tau(x_i)]$$\n\n")
            f.write("Expected outcome under policy $\\hat{\\pi}(x) = \\mathbb{1}[\\hat{\\tau}(x) > 0]$. *Higher is better.*\n\n")
            
            f.write("**Policy Regret:**\n")
            f.write("$$\\text{Regret} = V(\\pi^*) - V(\\hat{\\pi})$$\n\n")
            f.write("Where $\\pi^*(x) = \\mathbb{1}[\\tau(x) > 0]$ is the oracle policy. *Lower is better.*\n\n")
        
        # DGP config if provided
        if dgp_config:
            f.write("---\n\n")
            f.write("## Experiment Configuration\n\n")
            f.write("```yaml\n")
            for k, v in dgp_config.items():
                f.write(f"{k}: {v}\n")
            f.write("```\n\n")
        
        # Full results table
        f.write("---\n\n")
        f.write("## Results Table\n\n")
        f.write(create_metrics_summary_table(results))
        f.write("\n\n")
        
        # Visualizations
        f.write("---\n\n")
        f.write("## Visualizations\n\n")
        
        if embed_images and plot_files_png:
            if 'bars' in plot_files_png:
                f.write("### Method Comparison (Bar Chart)\n\n")
                f.write(f"![Bar Chart]({plot_files_png['bars']})\n\n")
            
            if 'radar' in plot_files_png:
                f.write("### Method Comparison (Radar Chart)\n\n")
                f.write(f"![Radar Chart]({plot_files_png['radar']})\n\n")
            
            if 'heatmap' in plot_files_png:
                f.write("### Metrics Heatmap\n\n")
                f.write(f"![Heatmap]({plot_files_png['heatmap']})\n\n")
        else:
            f.write("Plot files:\n\n")
            for pf in plot_files:
                f.write(f"- `{os.path.basename(pf)}`\n")
            f.write("\n")
        
        # Raw Data (CSV)
        f.write("---\n\n")
        f.write("## Raw Data\n\n")
        
        if embed_csv:
            f.write("### Full Results CSV\n\n")
            f.write("```csv\n")
            with open(csv_path, 'r') as csv_file:
                f.write(csv_file.read())
            f.write("```\n\n")
        else:
            f.write(f"CSV file: `{os.path.basename(csv_path)}`\n\n")
        
        # Detailed metrics per method
        f.write("### Detailed Metrics by Method\n\n")
        for method, metrics in results.items():
            f.write(f"#### {method}\n\n")
            f.write("| Metric | Value |\n")
            f.write("|--------|-------|\n")
            for metric, value in sorted(metrics.items()):
                if isinstance(value, float):
                    if np.isnan(value):
                        f.write(f"| {metric} | N/A |\n")
                    else:
                        f.write(f"| {metric} | {value:.6f} |\n")
                else:
                    f.write(f"| {metric} | {value} |\n")
            f.write("\n")
        
        # Footer
        f.write("---\n\n")
        f.write("*Report generated automatically by `metrics.generate_results_report()`*\n")
    
    return md_path


def compile_report_to_pdf_pandoc(md_path: str, output_path: str = None,
                                  pandoc_path: str = 'pandoc') -> str:
    """
    Compile a markdown report to PDF using pandoc (recommended).
    
    This produces the best quality output with proper LaTeX math rendering.
    
    Parameters
    ----------
    md_path : str
        Path to the markdown file.
    output_path : str, optional
        Output PDF path. If None, uses same name as md file with .pdf extension.
    pandoc_path : str
        Path to pandoc executable.
        
    Returns
    -------
    str
        Path to the generated PDF file.
        
    Note
    ----
    Requires pandoc and a LaTeX distribution (e.g., TexLive, MacTeX).
    Install pandoc: brew install pandoc
    Install LaTeX: brew install --cask mactex
    """
    import subprocess
    import shutil
    import os
    
    if output_path is None:
        output_path = md_path.replace('.md', '.pdf')
    
    # Check if pandoc exists
    pandoc_cmd = shutil.which(pandoc_path) or pandoc_path
    
    try:
        result = subprocess.run(
            [pandoc_cmd, md_path,
             '-o', output_path,
             '--pdf-engine=xelatex',
             '-V', 'geometry:margin=1in',
             '-V', 'fontsize=11pt',
             '--toc',
             '--highlight-style=tango'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Pandoc failed: {result.stderr}")
            
        return output_path
        
    except FileNotFoundError:
        raise RuntimeError(
            "Pandoc not found. Install with: brew install pandoc\n"
            "For LaTeX support, also install: brew install --cask mactex"
        )


def compile_report_to_pdf(md_path: str, output_path: str = None) -> str:
    """
    Compile a markdown report to PDF.
    
    Parameters
    ----------
    md_path : str
        Path to the markdown file.
    output_path : str, optional
        Output PDF path. If None, uses same name as md file with .pdf extension.
        
    Returns
    -------
    str
        Path to the generated PDF file.
        
    Note
    ----
    Requires fpdf2 package: pip install fpdf2
    LaTeX math will be shown as plain text. For proper math rendering,
    use pandoc with LaTeX: pandoc input.md -o output.pdf
    """
    import os
    import re
    
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError:
        raise ImportError("fpdf2 is required for PDF compilation. Install with: pip install fpdf2")
    
    if output_path is None:
        output_path = md_path.replace('.md', '.pdf')
    
    # Get directory of the markdown file for resolving relative image paths
    md_dir = os.path.dirname(md_path)
    
    def sanitize(text):
        """Replace Unicode characters with ASCII equivalents"""
        replacements = {
            '→': '->', '↑': '(up)', '↓': '(dn)', '✓': '[x]', '✗': '[ ]',
            '≤': '<=', '≥': '>=', '≠': '!=', '∈': 'in', '∼': '~',
            '×': 'x', '−': '-', '·': '.', 'ρ': 'rho', 'τ': 'tau',
            'μ': 'mu', 'σ': 'sigma', 'β': 'beta', 'α': 'alpha',
            'ε': 'eps', 'δ': 'delta', 'ν': 'nu', 'π': 'pi',
            '∞': 'inf', '∑': 'sum', '∫': 'int', '√': 'sqrt',
            '\\top': '^T', '\\mathcal': '', '\\text': '', '\\hat': '^',
            '\\bar': '_', '\\frac': '/', '\\cdot': '*',
        }
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text.encode('ascii', 'replace').decode('ascii')
    
    # Read markdown
    with open(md_path, 'r') as f:
        md_content = f.read()
    
    class ReportPDF(FPDF):
        def header(self):
            self.set_font('Helvetica', 'B', 10)
            self.cell(0, 10, 'Experiment Report', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
            self.ln(3)
            
        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', align='C')

        def chapter_title(self, title):
            self.set_font('Helvetica', 'B', 14)
            self.set_fill_color(230, 230, 230)
            self.cell(0, 10, sanitize(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
            self.ln(3)
            
        def section_title(self, title):
            self.set_font('Helvetica', 'B', 11)
            self.cell(0, 7, sanitize(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.ln(1)
            
        def body_text(self, text):
            self.set_font('Helvetica', '', 10)
            self.multi_cell(0, 5, sanitize(text))
            self.ln(1)
            
        def code_block(self, text):
            self.set_font('Courier', '', 8)
            self.set_fill_color(245, 245, 245)
            for line in text.split('\n')[:30]:
                self.cell(0, 4, sanitize(line[:90]), new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
            self.ln(2)
            
        def add_table(self, headers, rows):
            self.set_font('Helvetica', 'B', 8)
            n_cols = len(headers)
            col_width = min(25, (self.w - 20) / n_cols)
            
            self.set_fill_color(200, 200, 200)
            for h in headers:
                self.cell(col_width, 5, sanitize(h[:12]), border=1, fill=True, align='C')
            self.ln()
            
            self.set_font('Helvetica', '', 7)
            for row in rows[:20]:
                for cell in row:
                    self.cell(col_width, 4, sanitize(str(cell)[:12]), border=1, align='C')
                self.ln()
            self.ln(2)
    
    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    lines = md_content.split('\n')
    in_code_block = False
    code_content = []
    table_rows = []
    table_headers = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if not line.strip():
            i += 1
            continue
        
        # Code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                pdf.code_block('\n'.join(code_content))
                code_content = []
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue
            
        if in_code_block:
            code_content.append(line)
            i += 1
            continue
        
        # Tables
        if '|' in line and not line.startswith('!'):
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if cells:
                if all(set(c).issubset({'-', ':', ' '}) for c in cells):
                    i += 1
                    continue
                if not table_headers:
                    table_headers = cells
                else:
                    table_rows.append(cells)
            i += 1
            if i >= len(lines) or '|' not in lines[i]:
                if table_headers and table_rows:
                    pdf.add_table(table_headers, table_rows)
                table_headers = []
                table_rows = []
            continue
        
        # Headers
        if line.startswith('# '):
            pdf.add_page()
            pdf.chapter_title(line[2:].strip())
        elif line.startswith('## '):
            pdf.ln(5)
            pdf.chapter_title(line[3:].strip())
        elif line.startswith('### '):
            pdf.section_title(line[4:].strip())
        elif line.startswith('#### '):
            pdf.section_title(line[5:].strip())
        elif line.startswith('**') and line.endswith('**'):
            pdf.section_title(line.replace('**', ''))
        elif line.startswith('---'):
            pass
        elif line.startswith('!['):
            # Image
            match = re.search(r'\!\[([^\]]*)\]\(([^\)]+)\)', line)
            if match:
                img_path = os.path.join(md_dir, match.group(2))
                if os.path.exists(img_path):
                    try:
                        pdf.image(img_path, w=160)
                        pdf.ln(3)
                    except:
                        pdf.body_text(f'[Image: {match.group(1)}]')
        elif line.startswith('- '):
            pdf.body_text('  * ' + line[2:])
        elif line.strip().startswith('$$'):
            math = line.replace('$$', '').strip()
            if math:
                pdf.set_font('Courier', '', 9)
                pdf.body_text('    ' + math)
                pdf.set_font('Helvetica', '', 10)
        else:
            text = re.sub(r'\$([^\$]+)\$', r'(\1)', line)
            text = text.replace('**', '').replace('*', '')
            if text.strip():
                pdf.body_text(text)
        
        i += 1
    
    pdf.output(output_path)
    return output_path
