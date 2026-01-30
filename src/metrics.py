"""
Evaluation metrics for CATE estimation.

Metrics from paper:
- PEHE: Precision in Estimation of Heterogeneous Effects (RMSE of CATE)
- ATE Error: Mean absolute error of average treatment effect
- Calibration RMSE: RMSE for μ₀ and μ₁ predictions
"""

import numpy as np
from typing import Dict


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
    return np.sqrt(np.mean((tau_true - tau_pred) ** 2))


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
    return np.abs(np.mean(tau_true) - np.mean(tau_pred))


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
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


def evaluate_cate_model(model, X_test, tau_true, mu0_true=None, mu1_true=None,
                        compute_calibration=False) -> Dict[str, float]:
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
        True μ₀ values for calibration check
    mu1_true : array-like, optional
        True μ₁ values for calibration check
    compute_calibration : bool, default=False
        Whether to compute outcome calibration metrics
    
    Returns
    -------
    metrics : dict
        Dictionary with keys: pehe, ate_error, mu0_rmse (optional), mu1_rmse (optional)
    """
    # Predict CATE
    tau_pred = model.predict(X_test)
    
    metrics = {
        'pehe': pehe(tau_true, tau_pred),
        'ate_error': ate_error(tau_true, tau_pred)
    }
    
    # Calibration metrics (if model supports and data provided)
    if compute_calibration and hasattr(model, 'proxy_models_'):
        if mu0_true is not None:
            mu0_pred = model.proxy_models_[0].predict(X_test)
            if hasattr(model, 'delta_0_'):
                mu0_pred += model.delta_0_.predict(X_test)
            metrics['mu0_rmse'] = calibration_rmse(mu0_true, mu0_pred)
        
        if mu1_true is not None:
            mu1_pred = model.proxy_models_[1].predict(X_test)
            if hasattr(model, 'delta_1_'):
                mu1_pred += model.delta_1_.predict(X_test)
            metrics['mu1_rmse'] = calibration_rmse(mu1_true, mu1_pred)
    
    return metrics


def print_metrics(metrics: Dict[str, float], method_name: str = "Model"):
    """Pretty print evaluation metrics."""
    print(f"\n{method_name} Performance:")
    print(f"  PEHE:      {metrics['pehe']:.4f}")
    print(f"  ATE Error: {metrics['ate_error']:.4f}")
    
    if 'mu0_rmse' in metrics:
        print(f"  μ₀ RMSE:   {metrics['mu0_rmse']:.4f}")
    if 'mu1_rmse' in metrics:
        print(f"  μ₁ RMSE:   {metrics['mu1_rmse']:.4f}")


def compare_methods(results: Dict[str, Dict[str, float]]) -> None:
    """
    Compare multiple methods and print formatted table.
    
    Parameters
    ----------
    results : dict
        Dictionary mapping method names to metric dictionaries
    """
    methods = list(results.keys())
    metrics = list(results[methods[0]].keys())
    
    # Header
    print("\n" + "=" * 80)
    print("Method Comparison")
    print("=" * 80)
    print(f"{'Method':<20} " + " ".join([f"{m:>12}" for m in metrics]))
    print("-" * 80)
    
    # Rows
    for method in methods:
        values = [f"{results[method][m]:>12.4f}" for m in metrics]
        print(f"{method:<20} " + " ".join(values))
    
    print("=" * 80)
    
    # Find best for each metric (lower is better)
    print("\nBest Performance (lowest):")
    for metric in metrics:
        best_method = min(methods, key=lambda m: results[m][metric])
        best_value = results[best_method][metric]
        print(f"  {metric}: {best_method} ({best_value:.4f})")
