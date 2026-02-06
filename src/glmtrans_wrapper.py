"""
Python Wrapper for R glmtrans Package

This module provides Python wrappers that call the R glmtrans package
via subprocess or rpy2 for transfer learning in high-dimensional GLMs.

Reference:
    Tian, Y., & Feng, Y. (2023). Transfer learning under high-dimensional 
    generalized linear models. JASA, 118(544), 2684-2697.

Setup:
    To install R dependencies:
        python -m glmtrans_wrapper --setup
    
    Or from Python:
        from glmtrans_wrapper import setup_glmtrans
        setup_glmtrans()
"""

import numpy as np
import subprocess
import tempfile
import os
import json
from typing import Dict, List, Optional, Tuple, Any, Union
from pathlib import Path
import warnings
import sys

# Try to import pandas, but make it optional
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None


# Path to the R script
R_SCRIPT_PATH = Path(__file__).parent / "glmtrans_estimators.R"
R_LIBS_PATH = Path(__file__).parent.parent / "R_libs"


# =============================================================================
# Setup and Installation Functions
# =============================================================================

def _check_r_installed() -> bool:
    """Check if R/Rscript is installed on the system."""
    try:
        result = subprocess.run(
            ["Rscript", "--version"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _check_glmtrans_installed() -> bool:
    """Check if glmtrans R package is installed."""
    try:
        result = subprocess.run(
            ["Rscript", "-e", "library(glmtrans); cat('OK')"],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "R_LIBS_USER": str(R_LIBS_PATH)}
        )
        return "OK" in result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _check_r_available() -> bool:
    """Check if R and glmtrans are available."""
    return _check_r_installed() and _check_glmtrans_installed()


def setup_glmtrans(verbose: bool = True) -> bool:
    """
    Setup and install glmtrans R package if needed.
    
    This function:
    1. Checks if R is installed
    2. Creates a local R library directory
    3. Installs glmtrans and dependencies if not present
    
    Parameters
    ----------
    verbose : bool
        Print progress messages
        
    Returns
    -------
    success : bool
        True if glmtrans is available after setup
        
    Example
    -------
    >>> from glmtrans_wrapper import setup_glmtrans
    >>> if setup_glmtrans():
    ...     print("glmtrans ready!")
    """
    if verbose:
        print("=" * 60)
        print("Setting up glmtrans R package")
        print("=" * 60)
    
    # Step 1: Check if R is installed
    if verbose:
        print("\n1. Checking R installation...")
    
    if not _check_r_installed():
        print("   ERROR: R/Rscript not found in PATH")
        print("   Please install R from https://cran.r-project.org/")
        return False
    
    if verbose:
        print("   ✓ R is installed")
    
    # Step 2: Create local library directory
    if verbose:
        print(f"\n2. Setting up R library at {R_LIBS_PATH}...")
    
    R_LIBS_PATH.mkdir(parents=True, exist_ok=True)
    
    if verbose:
        print(f"   ✓ Library directory ready")
    
    # Step 3: Check if glmtrans is already installed
    if verbose:
        print("\n3. Checking glmtrans package...")
    
    if _check_glmtrans_installed():
        if verbose:
            print("   ✓ glmtrans is already installed and working")
        return True
    
    # Step 4: Install glmtrans
    if verbose:
        print("   Installing glmtrans (this may take a few minutes)...")
    
    install_script = f'''
# Set library path
.libPaths(c("{R_LIBS_PATH}", .libPaths()))

# Install glmtrans if not available
if (!requireNamespace("glmtrans", quietly = TRUE)) {{
    cat("Installing glmtrans from CRAN...\\n")
    install.packages("glmtrans", lib = "{R_LIBS_PATH}", 
                     repos = "https://cloud.r-project.org",
                     dependencies = TRUE)
}}

# Install glmnet if not available (dependency)
if (!requireNamespace("glmnet", quietly = TRUE)) {{
    cat("Installing glmnet from CRAN...\\n")
    install.packages("glmnet", lib = "{R_LIBS_PATH}",
                     repos = "https://cloud.r-project.org",
                     dependencies = TRUE)
}}

# Verify installation
library(glmtrans)
library(glmnet)
cat("\\nInstallation successful!\\n")
cat("glmtrans version:", as.character(packageVersion("glmtrans")), "\\n")
'''
    
    try:
        result = subprocess.run(
            ["Rscript", "-e", install_script],
            capture_output=True, text=True, timeout=600,  # 10 min timeout
            env={**os.environ, "R_LIBS_USER": str(R_LIBS_PATH)}
        )
        
        if verbose:
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    print(f"   {line}")
            if result.stderr and result.returncode != 0:
                for line in result.stderr.strip().split('\n')[:10]:
                    print(f"   [stderr] {line}")
        
        if result.returncode != 0:
            print(f"   ERROR: Installation failed with code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ERROR: Installation timed out")
        return False
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
    # Step 5: Verify installation
    if verbose:
        print("\n4. Verifying installation...")
    
    if _check_glmtrans_installed():
        if verbose:
            print("   ✓ glmtrans is now available!")
            print("\n" + "=" * 60)
            print("Setup complete! You can now use glmtrans methods.")
            print("=" * 60)
        return True
    else:
        print("   ERROR: Installation verification failed")
        return False


def get_glmtrans_status() -> Dict[str, Any]:
    """
    Get detailed status of glmtrans availability.
    
    Returns
    -------
    status : dict
        Dictionary with:
        - r_installed: bool
        - glmtrans_installed: bool
        - r_libs_path: str
        - available: bool
        - message: str
    """
    r_installed = _check_r_installed()
    glmtrans_installed = _check_glmtrans_installed() if r_installed else False
    
    if not r_installed:
        message = "R is not installed. Install from https://cran.r-project.org/"
    elif not glmtrans_installed:
        message = f"glmtrans not installed. Run: python -m glmtrans_wrapper --setup"
    else:
        message = "glmtrans is available and ready"
    
    return {
        'r_installed': r_installed,
        'glmtrans_installed': glmtrans_installed,
        'r_libs_path': str(R_LIBS_PATH),
        'available': r_installed and glmtrans_installed,
        'message': message
    }


def _array_to_r_matrix(arr: np.ndarray, name: str) -> str:
    """Convert numpy array to R matrix definition."""
    arr = np.asarray(arr)
    if arr.ndim == 1:
        values = ",".join(map(str, arr))
        return f"{name} <- c({values})"
    else:
        values = ",".join(map(str, arr.flatten(order='F')))
        return f"{name} <- matrix(c({values}), nrow={arr.shape[0]}, ncol={arr.shape[1]})"


class GlmtransR:
    """
    R-based glmtrans wrapper using subprocess.
    
    This calls the actual R glmtrans package for accurate transfer learning.
    
    Parameters
    ----------
    transfer_source_id : str
        Which sources: "auto", "all"
    alpha : float
        Elastic-net mixing (1=lasso, 0=ridge)
    nfolds : int
        CV folds for lambda selection
    verbose : bool
        Print R output
        
    Example
    -------
    >>> model = GlmtransR()
    >>> model.fit(X_target, Y_target, X_source, Y_source, c_source)
    >>> y_pred = model.predict(X_new)
    """
    
    def __init__(
        self,
        transfer_source_id: str = "auto",
        alpha: float = 1.0,
        nfolds: int = 5,
        verbose: bool = False
    ):
        self.transfer_source_id = transfer_source_id
        self.alpha = alpha
        self.nfolds = nfolds
        self.verbose = verbose
        
        # Check R availability
        if not _check_r_available():
            raise RuntimeError(
                "R or glmtrans package not available. "
                "Install R and run: install.packages('glmtrans')"
            )
        
        # Fitted state
        self.beta_ = None
        self.intercept_ = None
        self.transfer_source_ids_ = None
    
    def fit(
        self,
        X_target: np.ndarray,
        Y_target: np.ndarray,
        X_source: np.ndarray,
        Y_source: np.ndarray,
        c_source: np.ndarray,
        family: str = "gaussian"
    ) -> 'GlmtransR':
        """
        Fit glmtrans model.
        
        Parameters
        ----------
        X_target : ndarray (n_target, p)
            Target features
        Y_target : ndarray (n_target,)
            Target response
        X_source : ndarray (n_source, p)
            Source features
        Y_source : ndarray (n_source,)
            Source response
        c_source : ndarray (n_source,)
            Source site indicators
        family : str
            Response family: "gaussian", "binomial", "poisson"
            
        Returns
        -------
        self
        """
        X_target = np.asarray(X_target)
        Y_target = np.asarray(Y_target).flatten()
        X_source = np.asarray(X_source)
        Y_source = np.asarray(Y_source).flatten()
        c_source = np.asarray(c_source).flatten()
        
        # Create temporary files for data exchange
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save data to CSV files
            np.savetxt(f"{tmpdir}/X_target.csv", X_target, delimiter=",")
            np.savetxt(f"{tmpdir}/Y_target.csv", Y_target, delimiter=",")
            np.savetxt(f"{tmpdir}/X_source.csv", X_source, delimiter=",")
            np.savetxt(f"{tmpdir}/Y_source.csv", Y_source, delimiter=",")
            np.savetxt(f"{tmpdir}/c_source.csv", c_source, delimiter=",")
            
            # R script to fit model
            r_script = f'''
# Set up library paths
local_lib <- "{R_LIBS_PATH}"
if (dir.exists(local_lib)) .libPaths(c(local_lib, .libPaths()))

suppressPackageStartupMessages({{
  library(glmtrans)
  library(glmnet)
}})

# Load data
X_target <- as.matrix(read.csv("{tmpdir}/X_target.csv", header=FALSE))
Y_target <- as.vector(read.csv("{tmpdir}/Y_target.csv", header=FALSE)$V1)
X_source <- as.matrix(read.csv("{tmpdir}/X_source.csv", header=FALSE))
Y_source <- as.vector(read.csv("{tmpdir}/Y_source.csv", header=FALSE)$V1)
c_source <- as.vector(read.csv("{tmpdir}/c_source.csv", header=FALSE)$V1)

# Format target data
target <- list(x = X_target, y = Y_target)

# Format source data by site
site_ids <- unique(c_source)
source <- list()
for (i in seq_along(site_ids)) {{
  site <- site_ids[i]
  mask <- c_source == site
  source[[i]] <- list(x = X_source[mask, , drop=FALSE], y = Y_source[mask])
}}

# Fit glmtrans
fit <- glmtrans(
  target = target,
  source = source,
  family = "{family}",
  transfer.source.id = "{self.transfer_source_id}",
  alpha = {self.alpha},
  nfolds = {self.nfolds},
  detection.info = {'TRUE' if self.verbose else 'FALSE'}
)

# Save results
write.csv(fit$beta, "{tmpdir}/beta.csv", row.names=FALSE)
write.csv(fit$transfer.source.id, "{tmpdir}/transfer_ids.csv", row.names=FALSE)
'''
            
            # Run R script
            result = subprocess.run(
                ["Rscript", "-e", r_script],
                capture_output=True, text=True,
                env={**os.environ, "R_LIBS_USER": str(R_LIBS_PATH)}
            )
            
            if self.verbose:
                print(result.stdout)
            
            if result.returncode != 0:
                raise RuntimeError(f"R script failed:\n{result.stderr}")
            
            # Load results
            self.beta_ = np.loadtxt(f"{tmpdir}/beta.csv", delimiter=",", skiprows=1)
            self.intercept_ = self.beta_[0]
            self.coef_ = self.beta_[1:]
            
            try:
                transfer_ids = np.loadtxt(f"{tmpdir}/transfer_ids.csv", delimiter=",", skiprows=1)
                self.transfer_source_ids_ = list(transfer_ids.astype(int))
            except:
                self.transfer_source_ids_ = []
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict response."""
        X = np.asarray(X)
        return X @ self.coef_ + self.intercept_


class GlmtransCATEEstimator:
    """
    CATE Estimator using R glmtrans for transfer learning.
    
    This estimator:
    1. Learns μ₀(X) via transfer from source control data
    2. Learns μ₁(X) via transfer from source treated data  
    3. Computes τ(X) = μ₁(X) - μ₀(X)
    
    Compatible with the benchmark runner interface.
    
    Parameters
    ----------
    transfer_source_id : str
        "auto" for automatic detection, "all" for all sources
    alpha : float
        Elastic-net mixing (1=lasso)
    nfolds : int
        CV folds for lambda selection
    use_dr : bool
        Use doubly robust pseudo-outcomes
    verbose : bool
        Print R output
        
    Example
    -------
    >>> estimator = GlmtransCATEEstimator()
    >>> estimator.fit(X_source, A_source, Y_source, c_source, 
    ...               X_target, A_target, Y_target)
    >>> tau_hat = estimator.predict(X_eval)
    """
    
    def __init__(
        self,
        transfer_source_id: str = "auto",
        alpha: float = 1.0,
        nfolds: int = 5,
        use_dr: bool = False,
        verbose: bool = False
    ):
        self.transfer_source_id = transfer_source_id
        self.alpha = alpha
        self.nfolds = nfolds
        self.use_dr = use_dr
        self.verbose = verbose
        
        # Check R availability
        if not _check_r_available():
            raise RuntimeError(
                "R or glmtrans package not available. "
                "Install R and run: install.packages('glmtrans')"
            )
        
        # Fitted state
        self.mu0_beta_ = None
        self.mu1_beta_ = None
        self.cate_beta_ = None
        self.ate_hat_ = None
    
    def fit(
        self,
        X_source: np.ndarray,
        A_source: np.ndarray,
        Y_source: np.ndarray,
        c_source: np.ndarray,
        X_target: np.ndarray,
        A_target: np.ndarray,
        Y_target: np.ndarray,
        propensity_target: Optional[np.ndarray] = None
    ) -> 'GlmtransCATEEstimator':
        """
        Fit CATE estimator with transfer learning.
        
        Parameters
        ----------
        X_source : ndarray (n_source, p)
            Source features
        A_source : ndarray (n_source,)
            Source treatments (0/1)
        Y_source : ndarray (n_source,)
            Source outcomes
        c_source : ndarray (n_source,)
            Source site indicators
        X_target : ndarray (n_target, p)
            Target features
        A_target : ndarray (n_target,)
            Target treatments
        Y_target : ndarray (n_target,)
            Target outcomes
        propensity_target : ndarray, optional
            Target propensity scores
            
        Returns
        -------
        self
        """
        X_source = np.asarray(X_source)
        A_source = np.asarray(A_source).flatten()
        Y_source = np.asarray(Y_source).flatten()
        c_source = np.asarray(c_source).flatten()
        X_target = np.asarray(X_target)
        A_target = np.asarray(A_target).flatten()
        Y_target = np.asarray(Y_target).flatten()
        
        if propensity_target is None:
            propensity_target = np.full(len(A_target), np.mean(A_target))
        propensity_target = np.asarray(propensity_target)
        
        # Create temporary files for data exchange
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save data to CSV files
            np.savetxt(f"{tmpdir}/X_source.csv", X_source, delimiter=",")
            np.savetxt(f"{tmpdir}/A_source.csv", A_source, delimiter=",")
            np.savetxt(f"{tmpdir}/Y_source.csv", Y_source, delimiter=",")
            np.savetxt(f"{tmpdir}/c_source.csv", c_source, delimiter=",")
            np.savetxt(f"{tmpdir}/X_target.csv", X_target, delimiter=",")
            np.savetxt(f"{tmpdir}/A_target.csv", A_target, delimiter=",")
            np.savetxt(f"{tmpdir}/Y_target.csv", Y_target, delimiter=",")
            np.savetxt(f"{tmpdir}/propensity.csv", propensity_target, delimiter=",")
            
            # R script to fit CATE model
            if self.use_dr:
                fit_func = "fit_glmtrans_dr"
                predict_func = "predict_dr"
            else:
                fit_func = "fit_glmtrans_cate"
                predict_func = "predict_cate"
            
            r_script = f'''
# Set up library paths
local_lib <- "{R_LIBS_PATH}"
if (dir.exists(local_lib)) .libPaths(c(local_lib, .libPaths()))

# Source the estimator functions
source("{R_SCRIPT_PATH}")

# Load data
X_source <- as.matrix(read.csv("{tmpdir}/X_source.csv", header=FALSE))
A_source <- as.vector(read.csv("{tmpdir}/A_source.csv", header=FALSE)$V1)
Y_source <- as.vector(read.csv("{tmpdir}/Y_source.csv", header=FALSE)$V1)
c_source <- as.vector(read.csv("{tmpdir}/c_source.csv", header=FALSE)$V1)
X_target <- as.matrix(read.csv("{tmpdir}/X_target.csv", header=FALSE))
A_target <- as.vector(read.csv("{tmpdir}/A_target.csv", header=FALSE)$V1)
Y_target <- as.vector(read.csv("{tmpdir}/Y_target.csv", header=FALSE)$V1)
propensity <- as.vector(read.csv("{tmpdir}/propensity.csv", header=FALSE)$V1)

# Fit model
fit <- {fit_func}(
  X_source, A_source, Y_source, c_source,
  X_target, A_target, Y_target,
  {'propensity = propensity,' if self.use_dr else ''}
  transfer_source_id = "{self.transfer_source_id}",
  alpha = {self.alpha},
  nfolds = {self.nfolds},
  verbose = {'TRUE' if self.verbose else 'FALSE'}
)

# Predict CATE on target
tau_pred <- {predict_func}(fit, X_target)

# Save predictions (we'll use these for inference)
write.csv(tau_pred, "{tmpdir}/tau_pred.csv", row.names=FALSE)
write.csv(mean(tau_pred), "{tmpdir}/ate_hat.csv", row.names=FALSE)

# Save model coefficients if available
if (!is.null(fit$mu0_fit) && !isTRUE(fit$mu0_fit$is_glmnet)) {{
  write.csv(fit$mu0_fit$beta, "{tmpdir}/mu0_beta.csv", row.names=FALSE)
}}
if (!is.null(fit$mu1_fit) && !isTRUE(fit$mu1_fit$is_glmnet)) {{
  write.csv(fit$mu1_fit$beta, "{tmpdir}/mu1_beta.csv", row.names=FALSE)
}}

# For DR, also save CATE model
if (class(fit)[1] == "glmtrans_dr") {{
  beta_cate <- as.vector(coef(fit$cate_model, s = "lambda.min"))
  write.csv(beta_cate, "{tmpdir}/cate_beta.csv", row.names=FALSE)
}}
'''
            
            # Run R script
            result = subprocess.run(
                ["Rscript", "-e", r_script],
                capture_output=True, text=True, timeout=600,
                env={**os.environ, "R_LIBS_USER": str(R_LIBS_PATH)}
            )
            
            if self.verbose:
                print(result.stdout)
            
            if result.returncode != 0:
                raise RuntimeError(f"R script failed:\n{result.stderr}\n{result.stdout}")
            
            # Load ATE estimate
            self.ate_hat_ = float(np.loadtxt(f"{tmpdir}/ate_hat.csv", delimiter=",", skiprows=1))
            
            # Try to load coefficients
            try:
                self.mu0_beta_ = np.loadtxt(f"{tmpdir}/mu0_beta.csv", delimiter=",", skiprows=1)
            except:
                self.mu0_beta_ = None
            
            try:
                self.mu1_beta_ = np.loadtxt(f"{tmpdir}/mu1_beta.csv", delimiter=",", skiprows=1)
            except:
                self.mu1_beta_ = None
            
            try:
                self.cate_beta_ = np.loadtxt(f"{tmpdir}/cate_beta.csv", delimiter=",", skiprows=1)
            except:
                self.cate_beta_ = None
            
            # Store fitted tau for target (for diagnostics)
            self._tau_pred_target = np.loadtxt(f"{tmpdir}/tau_pred.csv", delimiter=",", skiprows=1)
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict CATE τ(X).
        
        Parameters
        ----------
        X : ndarray (n_samples, p)
            Features
            
        Returns
        -------
        tau_hat : ndarray (n_samples,)
            Predicted CATE
        """
        X = np.asarray(X)
        
        # If we have CATE coefficients (from DR), use those
        if self.cate_beta_ is not None:
            intercept = self.cate_beta_[0]
            coef = self.cate_beta_[1:]
            return X @ coef + intercept
        
        # Otherwise use plug-in: τ = μ₁ - μ₀
        mu0 = np.zeros(len(X))
        mu1 = np.zeros(len(X))
        
        if self.mu0_beta_ is not None:
            mu0 = X @ self.mu0_beta_[1:] + self.mu0_beta_[0]
        
        if self.mu1_beta_ is not None:
            mu1 = X @ self.mu1_beta_[1:] + self.mu1_beta_[0]
        
        return mu1 - mu0
    
    def get_ate(self) -> float:
        """Return estimated ATE."""
        return self.ate_hat_ if self.ate_hat_ is not None else 0.0


class GlmtransOptionBEstimator:
    """
    Option B CATE Estimator: Glmtrans source detection + Source-DR CATE.
    
    This implements the theoretically correct Option B for placebo-only targets:
    1. Use glmtrans ONLY on control arm for transferable source detection
    2. Restrict to selected sources (deterministic selection, not weighting)
    3. Fit DR CATE learner on selected sources only
    4. Transport the learned CATE to target
    
    This preserves:
    - The theory of glmtrans (deterministic transferable subset selection)
    - Feasibility for placebo-only target (no treated units required in target)
    
    Reference: Based on advisor's theoretical construction combining glmtrans
    source detection with source-DR CATE transport.
    
    Parameters
    ----------
    alpha : float
        Elastic-net mixing (1=lasso, 0=ridge)
    nfolds : int
        CV folds for lambda selection
    verbose : bool
        Print R output
    """
    
    def __init__(
        self,
        alpha: float = 1.0,
        nfolds: int = 5,
        verbose: bool = False
    ):
        self.alpha = alpha
        self.nfolds = nfolds
        self.verbose = verbose
        
        # Fitted attributes
        self.coef_cate_ = None
        self.coef_mu0_ = None
        self.coef_mu1_ = None
        self.tau_hat_ = None
        self.ate_hat_ = None
        self.selected_sources_ = None
        
        # Check R availability
        if not _check_r_available():
            raise RuntimeError("R with glmtrans package is required for GlmtransOptionBEstimator")
    
    def fit(
        self,
        X_source: np.ndarray,
        A_source: np.ndarray,
        Y_source: np.ndarray,
        c_source: np.ndarray,
        X_target: np.ndarray,
        A_target: Optional[np.ndarray] = None,
        Y_target: Optional[np.ndarray] = None,
        propensity_target: Optional[np.ndarray] = None
    ) -> 'GlmtransOptionBEstimator':
        """
        Fit Option B estimator.
        
        Parameters
        ----------
        X_source : array (n_source, p)
            Source covariates
        A_source : array (n_source,)
            Source treatments
        Y_source : array (n_source,)
            Source outcomes
        c_source : array (n_source,)
            Source site indicators
        X_target : array (n_target, p)
            Target covariates
        A_target : array (n_target,), optional
            Target treatments (used only to extract control outcomes if available)
        Y_target : array (n_target,), optional
            Target outcomes (used only to extract control outcomes for source detection)
        propensity_target : array, optional
            Not used (kept for interface compatibility)
        """
        X_source = np.asarray(X_source, dtype=np.float64)
        A_source = np.asarray(A_source, dtype=np.float64).flatten()
        Y_source = np.asarray(Y_source, dtype=np.float64).flatten()
        c_source = np.asarray(c_source, dtype=np.float64).flatten()
        X_target = np.asarray(X_target, dtype=np.float64)
        
        n_target, p = X_target.shape
        
        # Extract target control outcomes for source detection (if available)
        Y_target_control = None
        if A_target is not None and Y_target is not None:
            A_target = np.asarray(A_target, dtype=np.float64).flatten()
            Y_target = np.asarray(Y_target, dtype=np.float64).flatten()
            ctrl_mask = A_target == 0
            if ctrl_mask.sum() > 0:
                Y_target_control = np.full(n_target, np.nan)
                Y_target_control[ctrl_mask] = Y_target[ctrl_mask]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save data to CSV
            np.savetxt(os.path.join(tmpdir, "X_source.csv"), X_source, delimiter=",")
            np.savetxt(os.path.join(tmpdir, "A_source.csv"), A_source, delimiter=",")
            np.savetxt(os.path.join(tmpdir, "Y_source.csv"), Y_source, delimiter=",")
            np.savetxt(os.path.join(tmpdir, "c_source.csv"), c_source, delimiter=",")
            np.savetxt(os.path.join(tmpdir, "X_target.csv"), X_target, delimiter=",")
            
            if Y_target_control is not None:
                np.savetxt(os.path.join(tmpdir, "Y_target_control.csv"), Y_target_control, delimiter=",")
            
            # Build R script
            r_script = f'''
# Set library paths
local_lib <- "{R_LIBS_PATH}"
if (dir.exists(local_lib)) .libPaths(c(local_lib, .libPaths()))

# Source the glmtrans functions
source("{R_SCRIPT_PATH}")

# Load data
X_source <- as.matrix(read.csv("{os.path.join(tmpdir, 'X_source.csv')}", header=FALSE))
A_source <- as.vector(read.csv("{os.path.join(tmpdir, 'A_source.csv')}", header=FALSE)$V1)
Y_source <- as.vector(read.csv("{os.path.join(tmpdir, 'Y_source.csv')}", header=FALSE)$V1)
c_source <- as.vector(read.csv("{os.path.join(tmpdir, 'c_source.csv')}", header=FALSE)$V1)
X_target <- as.matrix(read.csv("{os.path.join(tmpdir, 'X_target.csv')}", header=FALSE))

# Load target control outcomes if available
Y_target_control <- NULL
if (file.exists("{os.path.join(tmpdir, 'Y_target_control.csv')}")) {{
  Y_target_control <- as.vector(read.csv("{os.path.join(tmpdir, 'Y_target_control.csv')}", header=FALSE)$V1)
}}

# Fit Option B model
fit <- fit_glmtrans_option_b(
  X_source = X_source,
  A_source = A_source,
  Y_source = Y_source,
  c_source = c_source,
  X_target = X_target,
  Y_target_control = Y_target_control,
  alpha = {self.alpha},
  nfolds = {self.nfolds},
  verbose = {"TRUE" if self.verbose else "FALSE"}
)

# Save results
write.csv(fit$tau_target, "{os.path.join(tmpdir, 'tau_target.csv')}", row.names=FALSE)
write.csv(fit$ate_hat, "{os.path.join(tmpdir, 'ate_hat.csv')}", row.names=FALSE)
write.csv(fit$selected_sources, "{os.path.join(tmpdir, 'selected_sources.csv')}", row.names=FALSE)

# Save coefficients
coef_cate <- as.vector(coef(fit$cate_model, s="lambda.min"))
coef_mu0 <- as.vector(coef(fit$mu0_model, s="lambda.min"))
coef_mu1 <- as.vector(coef(fit$mu1_model, s="lambda.min"))
write.csv(coef_cate, "{os.path.join(tmpdir, 'coef_cate.csv')}", row.names=FALSE)
write.csv(coef_mu0, "{os.path.join(tmpdir, 'coef_mu0.csv')}", row.names=FALSE)
write.csv(coef_mu1, "{os.path.join(tmpdir, 'coef_mu1.csv')}", row.names=FALSE)

cat("Option B fit complete.\\n")
'''
            
            # Execute R script
            r_script_path = os.path.join(tmpdir, "fit_option_b.R")
            with open(r_script_path, 'w') as f:
                f.write(r_script)
            
            result = subprocess.run(
                ["Rscript", r_script_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if self.verbose or result.returncode != 0:
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(result.stderr)
            
            if result.returncode != 0:
                raise RuntimeError(f"R script failed:\n{result.stderr}")
            
            # Load results
            self.tau_hat_ = pd.read_csv(os.path.join(tmpdir, "tau_target.csv")).values.flatten()
            self.ate_hat_ = pd.read_csv(os.path.join(tmpdir, "ate_hat.csv")).values.flatten()[0]
            self.selected_sources_ = pd.read_csv(os.path.join(tmpdir, "selected_sources.csv")).values.flatten()
            
            # Load coefficients (glmnet format: intercept + p coefficients)
            self.coef_cate_ = pd.read_csv(os.path.join(tmpdir, "coef_cate.csv")).values.flatten()
            self.coef_mu0_ = pd.read_csv(os.path.join(tmpdir, "coef_mu0.csv")).values.flatten()
            self.coef_mu1_ = pd.read_csv(os.path.join(tmpdir, "coef_mu1.csv")).values.flatten()
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict CATE for new observations."""
        if self.coef_cate_ is None:
            raise RuntimeError("Model not fitted. Call fit() first.")
        
        X = np.asarray(X, dtype=np.float64)
        
        # glmnet coefficients: [intercept, coef1, coef2, ...]
        intercept = self.coef_cate_[0]
        coef = self.coef_cate_[1:]
        
        # Handle dimension mismatch
        if len(coef) != X.shape[1]:
            if len(coef) > X.shape[1]:
                coef = coef[:X.shape[1]]
            else:
                coef = np.pad(coef, (0, X.shape[1] - len(coef)))
        
        return X @ coef + intercept
    
    def get_ate(self) -> float:
        """Return estimated ATE."""
        return self.ate_hat_ if self.ate_hat_ is not None else 0.0
    
    def get_selected_sources(self) -> np.ndarray:
        """Return the source sites selected by glmtrans."""
        return self.selected_sources_


def create_glmtrans_factories(seed: int = 42) -> Dict[str, Any]:
    """
    Create factory functions for glmtrans-based estimators.
    
    For integration with benchmark_adapters.py.
    
    Returns
    -------
    factories : dict
        Method name -> factory function
    """
    
    # Check if R is available
    r_available = _check_r_available()
    
    if not r_available:
        warnings.warn("R/glmtrans not available, glmtrans methods will not be registered")
        return {}
    
    factories = {
        # Standard glmtrans with auto source detection (plug-in)
        'Glmtrans_Auto': lambda: GlmtransCATEEstimator(
            transfer_source_id='auto',
            alpha=1.0,
            use_dr=False,
            nfolds=5
        ),
        
        # Glmtrans using all sources (plug-in)
        'Glmtrans_All': lambda: GlmtransCATEEstimator(
            transfer_source_id='all',
            alpha=1.0,
            use_dr=False,
            nfolds=5
        ),
        
        # Glmtrans with DR pseudo-outcomes
        'Glmtrans_DR': lambda: GlmtransCATEEstimator(
            transfer_source_id='auto',
            alpha=1.0,
            use_dr=True,
            nfolds=5
        ),
        
        # Elastic-net (alpha=0.5)
        'Glmtrans_ElasticNet': lambda: GlmtransCATEEstimator(
            transfer_source_id='auto',
            alpha=0.5,
            use_dr=False,
            nfolds=5
        ),
        
        # Option B: Source detection + Source-DR (for placebo-only target)
        # Uses glmtrans only for control-arm source detection, then fits
        # DR CATE on selected sources and transports to target.
        # Theoretically correct for disconnected target (m1=0).
        'Glmtrans_OptionB': lambda: GlmtransOptionBEstimator(
            alpha=1.0,
            nfolds=5
        ),
    }
    
    return factories


# =============================================================================
# Tests
# =============================================================================

def test_glmtrans_r():
    """Test the R-based glmtrans wrapper."""
    print("="*60)
    print("Testing GlmtransCATEEstimator (R-based)")
    print("="*60)
    
    np.random.seed(42)
    
    # Generate synthetic data
    p = 30
    n_source = 500
    n_target = 100
    n_sites = 3
    
    # True coefficients
    alpha0 = np.zeros(p)
    alpha0[:5] = [0.5, -0.3, 0.8, -0.2, 0.4]
    
    alpha1 = np.zeros(p)
    alpha1[:5] = [0.3, -0.5, 0.6, -0.1, 0.3]
    
    # Source data
    X_source = np.random.randn(n_source * n_sites, p)
    c_source = np.repeat(np.arange(n_sites), n_source)
    A_source = np.random.binomial(1, 0.5, n_source * n_sites)
    
    mu0_source = X_source @ alpha0
    mu1_source = X_source @ alpha1
    Y_source = (1 - A_source) * mu0_source + A_source * mu1_source + np.random.randn(n_source * n_sites) * 0.3
    
    # Target data
    X_target = np.random.randn(n_target, p)
    A_target = np.random.binomial(1, 0.5, n_target)
    
    mu0_target = X_target @ alpha0
    mu1_target = X_target @ alpha1
    tau_true = mu1_target - mu0_target
    Y_target = (1 - A_target) * mu0_target + A_target * mu1_target + np.random.randn(n_target) * 0.3
    
    print(f"Source: {len(X_source)} samples across {n_sites} sites")
    print(f"Target: {n_target} samples ({np.sum(A_target==0)} control, {np.sum(A_target==1)} treated)")
    print(f"True ATE: {np.mean(tau_true):.4f}")
    
    # Test plug-in estimator
    print("\n--- Glmtrans Plug-in ---")
    try:
        est_plugin = GlmtransCATEEstimator(
            transfer_source_id='auto',
            use_dr=False,
            verbose=True
        )
        est_plugin.fit(X_source, A_source, Y_source, c_source, X_target, A_target, Y_target)
        tau_plugin = est_plugin.predict(X_target)
        
        pehe_plugin = np.sqrt(np.mean((tau_plugin - tau_true)**2))
        ate_err_plugin = abs(np.mean(tau_plugin) - np.mean(tau_true))
        print(f"PEHE: {pehe_plugin:.4f}")
        print(f"|ATE Error|: {ate_err_plugin:.4f}")
    except Exception as e:
        print(f"Failed: {e}")
        pehe_plugin = float('inf')
    
    # Test DR estimator
    print("\n--- Glmtrans DR ---")
    try:
        est_dr = GlmtransCATEEstimator(
            transfer_source_id='auto',
            use_dr=True,
            verbose=True
        )
        est_dr.fit(X_source, A_source, Y_source, c_source, X_target, A_target, Y_target)
        tau_dr = est_dr.predict(X_target)
        
        pehe_dr = np.sqrt(np.mean((tau_dr - tau_true)**2))
        ate_err_dr = abs(np.mean(tau_dr) - np.mean(tau_true))
        print(f"PEHE: {pehe_dr:.4f}")
        print(f"|ATE Error|: {ate_err_dr:.4f}")
    except Exception as e:
        print(f"Failed: {e}")
        pehe_dr = float('inf')
    
    # Target-only baseline
    print("\n--- Target-Only Baseline (Lasso) ---")
    from sklearn.linear_model import LassoCV
    
    target_control = A_target == 0
    target_treated = A_target == 1
    
    lasso_0 = LassoCV(cv=5).fit(X_target[target_control], Y_target[target_control])
    lasso_1 = LassoCV(cv=5).fit(X_target[target_treated], Y_target[target_treated])
    
    tau_baseline = lasso_1.predict(X_target) - lasso_0.predict(X_target)
    pehe_baseline = np.sqrt(np.mean((tau_baseline - tau_true)**2))
    ate_err_baseline = abs(np.mean(tau_baseline) - np.mean(tau_true))
    print(f"PEHE: {pehe_baseline:.4f}")
    print(f"|ATE Error|: {ate_err_baseline:.4f}")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"{'Method':<25} | PEHE   | Improvement")
    print("-" * 50)
    print(f"{'Target-Only':<25} | {pehe_baseline:.4f} | baseline")
    if pehe_plugin != float('inf'):
        print(f"{'Glmtrans Plugin':<25} | {pehe_plugin:.4f} | {(pehe_baseline - pehe_plugin)/pehe_baseline*100:.1f}%")
    if pehe_dr != float('inf'):
        print(f"{'Glmtrans DR':<25} | {pehe_dr:.4f} | {(pehe_baseline - pehe_dr)/pehe_baseline*100:.1f}%")
    
    print("\n✓ Test completed!")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='glmtrans R package Python wrapper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Check glmtrans status
  python -m glmtrans_wrapper --status
  
  # Install/setup glmtrans
  python -m glmtrans_wrapper --setup
  
  # Run tests
  python -m glmtrans_wrapper --test
'''
    )
    parser.add_argument('--setup', action='store_true',
                        help='Install glmtrans R package if not present')
    parser.add_argument('--status', action='store_true',
                        help='Check glmtrans availability status')
    parser.add_argument('--test', action='store_true',
                        help='Run glmtrans tests')
    
    args = parser.parse_args()
    
    if args.status:
        status = get_glmtrans_status()
        print("=" * 60)
        print("glmtrans Status")
        print("=" * 60)
        print(f"R installed:        {'✓' if status['r_installed'] else '✗'}")
        print(f"glmtrans installed: {'✓' if status['glmtrans_installed'] else '✗'}")
        print(f"R libs path:        {status['r_libs_path']}")
        print(f"Available:          {'✓' if status['available'] else '✗'}")
        print(f"\nMessage: {status['message']}")
        sys.exit(0 if status['available'] else 1)
    
    elif args.setup:
        success = setup_glmtrans(verbose=True)
        sys.exit(0 if success else 1)
    
    elif args.test:
        if not _check_r_available():
            print("ERROR: glmtrans not available. Run --setup first.")
            sys.exit(1)
        test_glmtrans_r()
    
    else:
        # Default: show status
        status = get_glmtrans_status()
        print(f"glmtrans available: {'✓' if status['available'] else '✗'}")
        print(f"Message: {status['message']}")
        if not status['available']:
            print("\nTo setup: python -m glmtrans_wrapper --setup")
        parser.print_help()
