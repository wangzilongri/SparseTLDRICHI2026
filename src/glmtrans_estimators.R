#' Transfer Learning Estimators using glmtrans
#' 
#' This script provides wrapper functions around the glmtrans R package
#' for transfer learning in high-dimensional GLMs.
#' 
#' Reference:
#'   Tian, Y., & Feng, Y. (2023). Transfer learning under high-dimensional 
#'   generalized linear models. JASA, 118(544), 2684-2697.
#'
#' Usage from Python:
#'   Use rpy2 to source this file and call the functions, or
#'   call via subprocess with Rscript.

# =============================================================================
# Dependencies
# =============================================================================

# Set up local library path
local_lib <- file.path(dirname(getwd()), "R_libs")
if (dir.exists(local_lib)) {
  .libPaths(c(local_lib, .libPaths()))
}

# Check and install glmtrans if needed
if (!requireNamespace("glmtrans", quietly = TRUE)) {
  message("Installing glmtrans package...")
  if (!dir.exists(local_lib)) dir.create(local_lib, recursive = TRUE)
  install.packages("glmtrans", lib = local_lib, repos = "https://cloud.r-project.org")
  .libPaths(c(local_lib, .libPaths()))
}

suppressPackageStartupMessages({
  library(glmtrans)
  library(glmnet)
})

# =============================================================================
# Utility Functions
# =============================================================================

#' Format data for glmtrans
#' 
#' @param X Feature matrix (n x p)
#' @param Y Response vector (n)
#' @return List with x and y components
format_data <- function(X, Y) {
  list(x = as.matrix(X), y = as.vector(Y))
}

#' Format source data list for glmtrans
#' 
#' @param X_source Source feature matrix (n_source x p)
#' @param Y_source Source response vector (n_source)
#' @param c_source Source site indicators (n_source)
#' @return List of lists, one per source site
format_source_data <- function(X_source, Y_source, c_source) {
  X_source <- as.matrix(X_source)
  Y_source <- as.vector(Y_source)
  c_source <- as.vector(c_source)
  
  site_ids <- unique(c_source)
  source_list <- list()
  
  for (i in seq_along(site_ids)) {
    site <- site_ids[i]
    mask <- c_source == site
    source_list[[i]] <- list(
      x = X_source[mask, , drop = FALSE],
      y = Y_source[mask]
    )
  }
  
  return(source_list)
}

# =============================================================================
# Core glmtrans Wrapper
# =============================================================================

#' Fit glmtrans model for outcome regression
#' 
#' @param X_target Target features (n_target x p)
#' @param Y_target Target responses (n_target)
#' @param X_source Source features (n_source x p)
#' @param Y_source Source responses (n_source)
#' @param c_source Source site indicators (n_source)
#' @param family Response family: "gaussian", "binomial", "poisson"
#' @param transfer_source_id Which sources: "auto", "all", or integer vector
#' @param alpha Elastic-net mixing (1=lasso, 0=ridge)
#' @param nfolds CV folds for lambda selection
#' @param cores Number of cores for parallel computation
#' @param verbose Print progress
#' @return List with fitted model, coefficients, transferable sources
fit_glmtrans <- function(X_target, Y_target, 
                         X_source, Y_source, c_source,
                         family = "gaussian",
                         transfer_source_id = "auto",
                         alpha = 1,
                         nfolds = 10,
                         cores = 1,
                         verbose = FALSE) {
  
  # Format target data
  target <- format_data(X_target, Y_target)
  
  # Format source data by site
  source <- format_source_data(X_source, Y_source, c_source)
  
  if (verbose) {
    cat(sprintf("Target: n=%d, p=%d\n", nrow(target$x), ncol(target$x)))
    cat(sprintf("Sources: %d sites\n", length(source)))
    for (i in seq_along(source)) {
      cat(sprintf("  Site %d: n=%d\n", i, nrow(source[[i]]$x)))
    }
  }
  
  # Fit glmtrans
  fit <- glmtrans(
    target = target,
    source = source,
    family = family,
    transfer.source.id = transfer_source_id,
    alpha = alpha,
    nfolds = nfolds,
    cores = cores,
    detection.info = verbose
  )
  
  # Extract results
  result <- list(
    beta = fit$beta,
    intercept = fit$beta[1],
    coef = fit$beta[-1],
    transfer_source_ids = fit$transfer.source.id,
    family = family,
    model = fit
  )
  
  return(result)
}

#' Predict from fitted glmtrans model
#' 
#' @param fit Fitted glmtrans result from fit_glmtrans
#' @param X_new New feature matrix
#' @param type Prediction type: "link", "response", "class"
#' @return Predictions
predict_glmtrans <- function(fit, X_new, type = "response") {
  X_new <- as.matrix(X_new)
  pred <- predict(fit$model, newx = X_new, type = type)
  return(as.vector(pred))
}

# =============================================================================
# CATE Estimators
# =============================================================================

#' Estimate CATE using glmtrans transfer learning
#' 
#' This estimator:
#' 1. Learns μ₀(X) via transfer from source control data
#' 2. Learns μ₁(X) via transfer from source treated data  
#' 3. Computes τ(X) = μ₁(X) - μ₀(X)
#' 
#' @param X_source Source features (n_source x p)
#' @param A_source Source treatment indicators (0/1)
#' @param Y_source Source outcomes
#' @param c_source Source site indicators
#' @param X_target Target features (n_target x p)
#' @param A_target Target treatment indicators
#' @param Y_target Target outcomes
#' @param transfer_source_id Which sources: "auto", "all"
#' @param alpha Elastic-net mixing parameter
#' @param nfolds CV folds
#' @param verbose Print progress
#' @return List with fitted models and prediction function
fit_glmtrans_cate <- function(X_source, A_source, Y_source, c_source,
                              X_target, A_target, Y_target,
                              transfer_source_id = "auto",
                              alpha = 1,
                              nfolds = 5,
                              verbose = FALSE) {
  
  X_source <- as.matrix(X_source)
  A_source <- as.vector(A_source)
  Y_source <- as.vector(Y_source)
  c_source <- as.vector(c_source)
  X_target <- as.matrix(X_target)
  A_target <- as.vector(A_target)
  Y_target <- as.vector(Y_target)
  
  # Split by treatment arm
  source_control <- A_source == 0
  source_treated <- A_source == 1
  target_control <- A_target == 0
  target_treated <- A_target == 1
  
  has_target_control <- sum(target_control) > 0
  has_target_treated <- sum(target_treated) > 0
  
  if (verbose) {
    cat(sprintf("Source: %d control, %d treated\n", 
                sum(source_control), sum(source_treated)))
    cat(sprintf("Target: %d control, %d treated\n",
                sum(target_control), sum(target_treated)))
  }
  
  # -------------------------------------------------------------------------
  # Fit μ₀ model (control outcome)
  # -------------------------------------------------------------------------
  mu0_fit <- NULL
  if (has_target_control && sum(source_control) > 0) {
    if (verbose) cat("\nFitting μ₀ model (control outcome)...\n")
    
    mu0_fit <- fit_glmtrans(
      X_target = X_target[target_control, , drop = FALSE],
      Y_target = Y_target[target_control],
      X_source = X_source[source_control, , drop = FALSE],
      Y_source = Y_source[source_control],
      c_source = c_source[source_control],
      family = "gaussian",
      transfer_source_id = transfer_source_id,
      alpha = alpha,
      nfolds = nfolds,
      verbose = verbose
    )
  } else if (has_target_control) {
    # No source, fit Lasso on target only
    if (verbose) cat("\nFitting μ₀ on target only (no source control)...\n")
    cv_fit <- cv.glmnet(X_target[target_control, , drop = FALSE], 
                        Y_target[target_control], 
                        alpha = alpha, nfolds = nfolds)
    mu0_fit <- list(
      beta = as.vector(coef(cv_fit, s = "lambda.min")),
      model = cv_fit,
      is_glmnet = TRUE
    )
  }
  
  # -------------------------------------------------------------------------
  # Fit μ₁ model (treated outcome)
  # -------------------------------------------------------------------------
  mu1_fit <- NULL
  if (has_target_treated && sum(source_treated) > 0) {
    if (verbose) cat("\nFitting μ₁ model (treated outcome)...\n")
    
    mu1_fit <- fit_glmtrans(
      X_target = X_target[target_treated, , drop = FALSE],
      Y_target = Y_target[target_treated],
      X_source = X_source[source_treated, , drop = FALSE],
      Y_source = Y_source[source_treated],
      c_source = c_source[source_treated],
      family = "gaussian",
      transfer_source_id = transfer_source_id,
      alpha = alpha,
      nfolds = nfolds,
      verbose = verbose
    )
  } else if (has_target_treated) {
    # No source treated, fit Lasso on target only
    if (verbose) cat("\nFitting μ₁ on target only (no source treated)...\n")
    cv_fit <- cv.glmnet(X_target[target_treated, , drop = FALSE], 
                        Y_target[target_treated], 
                        alpha = alpha, nfolds = nfolds)
    mu1_fit <- list(
      beta = as.vector(coef(cv_fit, s = "lambda.min")),
      model = cv_fit,
      is_glmnet = TRUE
    )
  }
  
  # -------------------------------------------------------------------------
  # Return result
  # -------------------------------------------------------------------------
  result <- list(
    mu0_fit = mu0_fit,
    mu1_fit = mu1_fit,
    has_target_control = has_target_control,
    has_target_treated = has_target_treated
  )
  
  class(result) <- "glmtrans_cate"
  return(result)
}

#' Predict CATE from fitted glmtrans_cate model
#' 
#' @param fit Fitted model from fit_glmtrans_cate
#' @param X_new New feature matrix
#' @return Predicted CATE τ(X) = μ₁(X) - μ₀(X)
predict_cate <- function(fit, X_new) {
  X_new <- as.matrix(X_new)
  n <- nrow(X_new)
  
  # Predict μ₀
  if (!is.null(fit$mu0_fit)) {
    if (isTRUE(fit$mu0_fit$is_glmnet)) {
      mu0 <- as.vector(predict(fit$mu0_fit$model, X_new, s = "lambda.min"))
    } else {
      mu0 <- predict_glmtrans(fit$mu0_fit, X_new)
    }
  } else {
    mu0 <- rep(0, n)
  }
  
  # Predict μ₁
  if (!is.null(fit$mu1_fit)) {
    if (isTRUE(fit$mu1_fit$is_glmnet)) {
      mu1 <- as.vector(predict(fit$mu1_fit$model, X_new, s = "lambda.min"))
    } else {
      mu1 <- predict_glmtrans(fit$mu1_fit, X_new)
    }
  } else {
    mu1 <- rep(0, n)
  }
  
  # CATE = μ₁ - μ₀
  return(mu1 - mu0)
}

# =============================================================================
# Doubly Robust CATE Estimator
# =============================================================================

#' Estimate CATE with Doubly Robust pseudo-outcomes
#' 
#' Uses glmtrans for outcome models, then computes DR pseudo-outcomes
#' and fits a final CATE model.
#' 
#' @param X_source Source features
#' @param A_source Source treatments
#' @param Y_source Source outcomes
#' @param c_source Source site indicators
#' @param X_target Target features
#' @param A_target Target treatments
#' @param Y_target Target outcomes
#' @param propensity Target propensity scores (optional)
#' @param transfer_source_id Which sources to transfer
#' @param alpha Elastic-net mixing
#' @param nfolds CV folds
#' @param verbose Print progress
#' @return List with CATE model
fit_glmtrans_dr <- function(X_source, A_source, Y_source, c_source,
                            X_target, A_target, Y_target,
                            propensity = NULL,
                            transfer_source_id = "auto",
                            alpha = 1,
                            nfolds = 5,
                            verbose = FALSE) {
  
  X_target <- as.matrix(X_target)
  A_target <- as.vector(A_target)
  Y_target <- as.vector(Y_target)
  n <- nrow(X_target)
  
  # First fit plug-in models
  plugin_fit <- fit_glmtrans_cate(
    X_source, A_source, Y_source, c_source,
    X_target, A_target, Y_target,
    transfer_source_id = transfer_source_id,
    alpha = alpha,
    nfolds = nfolds,
    verbose = verbose
  )
  
  # Get plug-in predictions on target
  mu0_hat <- rep(0, n)
  mu1_hat <- rep(0, n)
  
  if (!is.null(plugin_fit$mu0_fit)) {
    if (isTRUE(plugin_fit$mu0_fit$is_glmnet)) {
      mu0_hat <- as.vector(predict(plugin_fit$mu0_fit$model, X_target, s = "lambda.min"))
    } else {
      mu0_hat <- predict_glmtrans(plugin_fit$mu0_fit, X_target)
    }
  }
  
  if (!is.null(plugin_fit$mu1_fit)) {
    if (isTRUE(plugin_fit$mu1_fit$is_glmnet)) {
      mu1_hat <- as.vector(predict(plugin_fit$mu1_fit$model, X_target, s = "lambda.min"))
    } else {
      mu1_hat <- predict_glmtrans(plugin_fit$mu1_fit, X_target)
    }
  }
  
  # Propensity scores
  if (is.null(propensity)) {
    propensity <- mean(A_target)
  }
  e <- pmax(pmin(propensity, 0.99), 0.01)
  
  # Compute DR pseudo-outcomes
  # Γ = (A/e)(Y - μ₁) + μ₁ - ((1-A)/(1-e))(Y - μ₀) - μ₀
  pseudo_outcome <- (A_target / e) * (Y_target - mu1_hat) + mu1_hat -
                    ((1 - A_target) / (1 - e)) * (Y_target - mu0_hat) - mu0_hat
  
  # Fit CATE model on pseudo-outcomes
  if (verbose) cat("\nFitting CATE model on DR pseudo-outcomes...\n")
  
  cate_cv <- cv.glmnet(X_target, pseudo_outcome, alpha = alpha, nfolds = nfolds)
  
  result <- list(
    plugin_fit = plugin_fit,
    cate_model = cate_cv,
    mu0_hat = mu0_hat,
    mu1_hat = mu1_hat,
    pseudo_outcome = pseudo_outcome,
    ate_hat = mean(pseudo_outcome)
  )
  
  class(result) <- "glmtrans_dr"
  return(result)
}

#' Predict CATE from DR model
predict_dr <- function(fit, X_new) {
  X_new <- as.matrix(X_new)
  pred <- predict(fit$cate_model, X_new, s = "lambda.min")
  return(as.vector(pred))
}


# =============================================================================
# CROSS-FITTED Glmtrans DR (Addressing Advisor's Critique)
# =============================================================================
#
# ADVISOR DIAGNOSIS (why original Glmtrans_DR underperforms):
#
# 1. NO CROSS-FITTING: μ̂ trained on same data as Γ computed → overfitting
# 2. PROPENSITY TAX: Bad ê amplifies noise through inverse weights  
# 3. DOUBLE SHRINKAGE: glmtrans shrinkage + Lasso on Γ → flattened τ̂
# 4. DR ON SMALL TARGET: Sources only used for μ̂, not for τ̂ learning
#
# FIX (implemented below):
# - Cross-fit nuisances when forming Γ (2-fold minimum)
# - Stable propensity estimation with clipping
# - Option to use ridge instead of Lasso for τ̂
# - Diagnostic output for variance comparison
# =============================================================================

#' Cross-fitted Glmtrans DR CATE estimator (CORRECTED)
#'
#' Addresses the issues with naive Glmtrans_DR:
#' - Uses K-fold cross-fitting for nuisance estimates
#' - Stable propensity with clipping
#' - Returns diagnostics for variance comparison
#'
#' @param X_source Source features
#' @param A_source Source treatments
#' @param Y_source Source outcomes
#' @param c_source Source site indicators
#' @param X_target Target features
#' @param A_target Target treatments
#' @param Y_target Target outcomes
#' @param transfer_source_id Which sources to transfer
#' @param n_folds Number of cross-fitting folds (default 2)
#' @param alpha Elastic-net mixing for final CATE (1=lasso, 0=ridge)
#' @param nfolds_cv CV folds for glmnet
#' @param prop_clip Propensity clipping bounds (default c(0.05, 0.95))
#' @param seed Random seed for fold assignment (NULL = don't set seed)
#' @param verbose Print progress
#' @return List with cross-fitted CATE model and diagnostics
fit_glmtrans_dr_crossfit <- function(X_source, A_source, Y_source, c_source,
                                      X_target, A_target, Y_target,
                                      transfer_source_id = "auto",
                                      n_folds = 2,
                                      alpha = 1,
                                      nfolds_cv = 5,
                                      prop_clip = c(0.05, 0.95),
                                      seed = NULL,
                                      verbose = FALSE) {
  
  X_target <- as.matrix(X_target)
  A_target <- as.vector(A_target)
  Y_target <- as.vector(Y_target)
  n <- nrow(X_target)
  
  if (verbose) cat("Cross-fitted Glmtrans DR with", n_folds, "folds\n")
  
  # Initialize storage for out-of-fold predictions
  mu0_oof <- rep(NA, n)
  mu1_oof <- rep(NA, n)
  e_oof <- rep(NA, n)
  
  # Create fold assignments
  # FIX (Problem B): Only set seed if explicitly provided
  if (!is.null(seed)) {
    set.seed(seed)
  }
  fold_ids <- sample(rep(1:n_folds, length.out = n))
  
  # =========================================================================
  # CROSS-FITTING: Train nuisances on fold k, predict on fold -k
  # =========================================================================
  # FIX (Problem A): Store per-fold training statistics to avoid leakage
  # These will be used for fallback imputation if model fitting fails
  fold_mu0_fallback <- rep(NA, n)  # Fold-specific fallbacks for each point
  fold_mu1_fallback <- rep(NA, n)
  fold_e_fallback <- rep(NA, n)
  
  for (k in 1:n_folds) {
    if (verbose) cat(sprintf("  Fold %d/%d...\n", k, n_folds))
    
    # Split target data
    train_idx <- fold_ids != k
    test_idx <- fold_ids == k
    
    X_train <- X_target[train_idx, , drop = FALSE]
    A_train <- A_target[train_idx]
    Y_train <- Y_target[train_idx]
    
    X_test <- X_target[test_idx, , drop = FALSE]
    
    # -----------------------------------------------------------------------
    # FIX (Problem A): Compute TRAINING-FOLD-ONLY statistics for fallback
    # These are computed BEFORE fitting, using ONLY the training fold
    # -----------------------------------------------------------------------
    mu0_mean_k <- mean(Y_train[A_train == 0], na.rm = TRUE)
    mu1_mean_k <- mean(Y_train[A_train == 1], na.rm = TRUE)
    e_mean_k <- mean(A_train)
    
    # Store fold-specific fallbacks for this fold's test indices
    fold_mu0_fallback[test_idx] <- mu0_mean_k
    fold_mu1_fallback[test_idx] <- mu1_mean_k
    fold_e_fallback[test_idx] <- e_mean_k
    
    # -----------------------------------------------------------------------
    # Fit glmtrans on training fold (uses sources + train target)
    # This is where transfer learning happens
    # -----------------------------------------------------------------------
    plugin_fit_k <- tryCatch({
      fit_glmtrans_cate(
        X_source, A_source, Y_source, c_source,
        X_train, A_train, Y_train,
        transfer_source_id = transfer_source_id,
        alpha = 1,  # Use Lasso for outcome models
        nfolds = nfolds_cv,
        verbose = FALSE
      )
    }, error = function(e) {
      if (verbose) cat(sprintf("    Warning: glmtrans failed in fold %d: %s\n", k, e$message))
      NULL
    })
    
    # Get out-of-fold predictions for μ₀, μ₁
    if (!is.null(plugin_fit_k)) {
      if (!is.null(plugin_fit_k$mu0_fit)) {
        if (isTRUE(plugin_fit_k$mu0_fit$is_glmnet)) {
          mu0_oof[test_idx] <- as.vector(predict(plugin_fit_k$mu0_fit$model, X_test, s = "lambda.min"))
        } else {
          mu0_oof[test_idx] <- predict_glmtrans(plugin_fit_k$mu0_fit, X_test)
        }
      }
      if (!is.null(plugin_fit_k$mu1_fit)) {
        if (isTRUE(plugin_fit_k$mu1_fit$is_glmnet)) {
          mu1_oof[test_idx] <- as.vector(predict(plugin_fit_k$mu1_fit$model, X_test, s = "lambda.min"))
        } else {
          mu1_oof[test_idx] <- predict_glmtrans(plugin_fit_k$mu1_fit, X_test)
        }
      }
    }
    
    # -----------------------------------------------------------------------
    # Fit propensity model on training fold (target only)
    # Use ridge logistic for stability (advisor recommendation)
    # -----------------------------------------------------------------------
    if (sum(A_train == 1) >= 5 && sum(A_train == 0) >= 5) {
      prop_cv <- tryCatch({
        cv.glmnet(X_train, A_train, family = "binomial", alpha = 0, nfolds = nfolds_cv)
      }, error = function(e) NULL)
      
      if (!is.null(prop_cv)) {
        e_oof[test_idx] <- as.vector(predict(prop_cv, X_test, s = "lambda.min", type = "response"))
      }
    }
    # If propensity fit fails or sample too small, e_oof[test_idx] stays NA
    # and will be filled with fold-specific e_mean_k below
  }
  
  # =========================================================================
  # FIX (Problem A): Handle missing predictions using FOLD-SPECIFIC fallbacks
  # This preserves cross-fitting validity by using only training-fold info
  # =========================================================================
  na_mu0 <- is.na(mu0_oof)
  na_mu1 <- is.na(mu1_oof)
  na_e <- is.na(e_oof)
  
  if (any(na_mu0)) {
    if (verbose) cat(sprintf("  Imputing %d missing μ₀ predictions with fold-specific means\n", sum(na_mu0)))
    mu0_oof[na_mu0] <- fold_mu0_fallback[na_mu0]
  }
  if (any(na_mu1)) {
    if (verbose) cat(sprintf("  Imputing %d missing μ₁ predictions with fold-specific means\n", sum(na_mu1)))
    mu1_oof[na_mu1] <- fold_mu1_fallback[na_mu1]
  }
  if (any(na_e)) {
    if (verbose) cat(sprintf("  Imputing %d missing propensities with fold-specific rates\n", sum(na_e)))
    e_oof[na_e] <- fold_e_fallback[na_e]
  }
  
  # =========================================================================
  # PROPENSITY CLIPPING (critical for stability)
  # =========================================================================
  e_clipped <- pmax(pmin(e_oof, prop_clip[2]), prop_clip[1])
  
  # Diagnostics: check for weight explosion
  inv_weights <- ifelse(A_target == 1, 1/e_clipped, 1/(1 - e_clipped))
  max_weight <- max(inv_weights)
  
  if (verbose) {
    cat(sprintf("  Propensity range: [%.3f, %.3f]\n", min(e_clipped), max(e_clipped)))
    cat(sprintf("  Max inverse weight: %.2f\n", max_weight))
    if (max_weight > 20) {
      cat("  WARNING: Large inverse weights detected - DR may be unstable\n")
    }
  }
  
  # =========================================================================
  # COMPUTE DR PSEUDO-OUTCOMES (using cross-fitted nuisances)
  # =========================================================================
  # Γᵢ = μ̂₁(Xᵢ) - μ̂₀(Xᵢ) + (Aᵢ - ê(Xᵢ))/(ê(Xᵢ)(1-ê(Xᵢ))) · (Yᵢ - μ̂_{Aᵢ}(Xᵢ))
  residual <- ifelse(A_target == 1, Y_target - mu1_oof, Y_target - mu0_oof)
  pseudo_outcome <- (mu1_oof - mu0_oof) + 
                    (A_target - e_clipped) / (e_clipped * (1 - e_clipped)) * residual
  
  # Also compute plug-in CATE for comparison
  plugin_cate <- mu1_oof - mu0_oof
  
  # Variance diagnostics (advisor's suggestion)
  var_pseudo <- var(pseudo_outcome)
  var_plugin <- var(plugin_cate)
  
  if (verbose) {
    cat(sprintf("  Var(Γ_DR): %.4f\n", var_pseudo))
    cat(sprintf("  Var(μ̂₁-μ̂₀): %.4f\n", var_plugin))
    cat(sprintf("  Ratio: %.2f\n", var_pseudo / var_plugin))
    if (var_pseudo > 2 * var_plugin) {
      cat("  WARNING: DR pseudo-outcomes much noisier than plug-in\n")
    }
  }
  
  # =========================================================================
  # FIT CATE MODEL ON PSEUDO-OUTCOMES
  # =========================================================================
  # Using specified alpha (can use ridge for less shrinkage)
  cate_cv <- cv.glmnet(X_target, pseudo_outcome, alpha = alpha, nfolds = nfolds_cv)
  
  # =========================================================================
  # PACKAGE RESULTS
  # =========================================================================
  result <- list(
    # Main output
    cate_model = cate_cv,
    ate_hat = mean(pseudo_outcome),
    
    # Cross-fitted predictions (for external use)
    mu0_oof = mu0_oof,
    mu1_oof = mu1_oof,
    e_oof = e_clipped,
    pseudo_outcome = pseudo_outcome,
    plugin_cate = plugin_cate,
    
    # Diagnostics
    diagnostics = list(
      var_pseudo = var_pseudo,
      var_plugin = var_plugin,
      var_ratio = var_pseudo / var_plugin,
      max_inv_weight = max_weight,
      prop_range = range(e_clipped),
      n_folds = n_folds
    )
  )
  
  class(result) <- "glmtrans_dr_crossfit"
  
  if (verbose) {
    cat(sprintf("  ATE estimate: %.4f\n", result$ate_hat))
    cat("✓ Cross-fitted DR complete.\n")
  }
  
  return(result)
}

#' Predict CATE from cross-fitted DR model
predict_dr_crossfit <- function(fit, X_new) {
  X_new <- as.matrix(X_new)
  pred <- predict(fit$cate_model, X_new, s = "lambda.min")
  return(as.vector(pred))
}


# =============================================================================
# Option B: Glmtrans for Source Detection + Source-DR CATE (THEORY-CLEAN)
# =============================================================================
#
# ADVISOR GUIDANCE (critical for paper defensibility):
# 
# "glmtrans theory justifies *source selection*, not arm-level transport of 
#  treatment effects."
#
# This implementation follows the EXACT construction the advisor provided:
#
#   Stage 0: Use glmtrans ONLY on control arm to detect transferable sources
#            -> Returns deterministic subset Ŝ₀ ⊂ {1,...,K}
#            -> Uses ONLY Y_target(0), NO target treated needed
#
#   Stage 1: Restrict to selected sources (NO weighting, just selection)
#            -> D_src^good = ∪_{k ∈ Ŝ₀} D_k
#
#   Stage 2: Fit DR CATE on selected sources
#            -> μ̂₀^src, μ̂₁^src fitted on selected source data
#            -> DR pseudo-outcomes computed on SOURCES
#            -> τ̂^src(x) fitted on source pseudo-outcomes
#
#   Stage 3: Transport to target
#            -> τ̂_target(x) := τ̂^src(x)  (direct transport, no correction)
#
# WHAT THIS DOES NOT DO (following advisor's "do not" list):
#   ✗ Does NOT use glmtrans coefficients as μ̂₁ in Option B
#   ✗ Does NOT run glmtrans jointly on A∈{0,1} when m₁=0
#   ✗ Does NOT infer treated-arm similarity from placebo similarity
#
# Paper description (advisor-approved):
#   "When the target site contains only control units, glmtrans cannot be 
#    applied directly to the treated arm. We therefore use glmtrans solely 
#    as a deterministic screening procedure on the control arm to identify 
#    transferable source sites. Conditional on this selected subset, we 
#    estimate CATEs using a doubly robust learner trained entirely on source 
#    data and transport the resulting CATE model to the target."
#
# Reference: Tian & Feng (2023) JASA - Transfer learning under high-dimensional GLMs
# =============================================================================

#' Stage 0: Detect transferable sources using glmtrans on CONTROL ARM ONLY
#'
#' This is the ONLY place glmtrans theory applies in Option B.
#' Returns a deterministic subset of source sites.
#' 
#' NOTE: This function is specifically for Option B (placebo-only target).
#' It's named _optionb to avoid conflict with the general detection function.
#'
#' @param X_t0 Target control features (n_t0 x p)
#' @param Y_t0 Target control outcomes (n_t0)
#' @param source_list List of source site data (each with x, y, w)
#' @param C0 Threshold multiplier (default 2, from glmtrans paper)
#' @param alpha Elastic-net mixing (1=lasso)
#' @param nfolds CV folds
#' @param verbose Print progress
#' @return Integer vector of transferable source IDs
detect_transferable_sources_optionb <- function(X_t0, Y_t0, source_list, 
                                                 C0 = 2, alpha = 1, nfolds = 5,
                                                 verbose = FALSE) {
  
  X_t0 <- as.matrix(X_t0)
  Y_t0 <- as.vector(Y_t0)
  
  if (length(Y_t0) < 10) {
    if (verbose) cat("  Insufficient target control data, using all sources.\n")
    return(seq_along(source_list))
  }
  
  # Target placebo data
  target <- list(x = X_t0, y = Y_t0)
  
  # Extract source CONTROLS only (this is where glmtrans theory applies)
  source_controls <- lapply(source_list, function(s) {
    ctrl_mask <- s$w == 0
    list(x = s$x[ctrl_mask, , drop = FALSE], 
         y = s$y[ctrl_mask])
  })
  
  # Filter out empty sources
  valid_sources <- sapply(source_controls, function(s) length(s$y) >= 10)
  if (sum(valid_sources) == 0) {
    if (verbose) cat("  No valid source controls, using all sources.\n")
    return(seq_along(source_list))
  }
  
  source_controls <- source_controls[valid_sources]
  valid_ids <- which(valid_sources)
  
  tryCatch({
    # Use glmtrans with auto detection on CONTROL ARM
    fit <- glmtrans::glmtrans(
      target = target,
      source = source_controls,
      family = "gaussian",
      transfer.source.id = "auto",  # Let glmtrans do its source selection
      alpha = alpha,
      nfolds = nfolds,
      cores = 1
    )
    
    # Extract selected sources (glmtrans returns indices into source_controls)
    selected_indices <- fit$transfer.source.id
    if (is.null(selected_indices) || length(selected_indices) == 0) {
      if (verbose) cat("  glmtrans selected no sources, using all.\n")
      return(seq_along(source_list))
    }
    
    # Map back to original source IDs
    selected_sources <- valid_ids[selected_indices]
    
    if (verbose) {
      cat(sprintf("  glmtrans selected %d/%d sources: %s\n", 
                  length(selected_sources), length(source_list),
                  paste(selected_sources, collapse = ", ")))
    }
    
    return(selected_sources)
    
  }, error = function(e) {
    if (verbose) cat(sprintf("  glmtrans detection failed: %s. Using all sources.\n", e$message))
    return(seq_along(source_list))
  })
}


#' Stage 1: Restrict to selected sources (NO weighting)
#'
#' Simply subsets the source data. No reweighting, no soft selection.
#' This is essential for maintaining glmtrans theory.
#'
#' @param source_list List of source site data
#' @param selected_ids Integer vector of selected source IDs
#' @return Restricted source list
restrict_to_selected_sources <- function(source_list, selected_ids) {
  source_list[selected_ids]
}


#' Fit Option B: Glmtrans source detection + Source-DR CATE (THEORY-CLEAN)
#'
#' @param X_source Source features (n_source x p)
#' @param A_source Source treatment indicators (n_source)
#' @param Y_source Source outcomes (n_source)
#' @param c_source Source site indicators (n_source)
#' @param X_target Target features (n_target x p)
#' @param Y_target_control Target control outcomes (placebo only, can have NAs)
#' @param C0 Threshold for source detection (default 2)
#' @param alpha Elastic-net mixing (1=lasso, 0=ridge)
#' @param nfolds CV folds
#' @param verbose Print progress
#' @return List with CATE model trained on selected sources
fit_glmtrans_option_b <- function(X_source, A_source, Y_source, c_source,
                                   X_target, Y_target_control = NULL,
                                   C0 = 2, alpha = 1, nfolds = 5,
                                   verbose = FALSE) {
  
  X_source <- as.matrix(X_source)
  A_source <- as.vector(A_source)
  Y_source <- as.vector(Y_source)
  c_source <- as.vector(c_source)
  X_target <- as.matrix(X_target)
  
  n_source <- nrow(X_source)
  n_target <- nrow(X_target)
  p <- ncol(X_source)
  site_ids <- sort(unique(c_source))
  
  # =========================================================================
  # STAGE 0: Transferable source detection on CONTROL ARM ONLY
  # =========================================================================
  # This is the ONLY place glmtrans theory applies.
  # Uses only Y_target(0), exactly as glmtrans was designed.
  # =========================================================================
  if (verbose) cat("Stage 0: Detecting transferable sources (control arm only)...\n")
  
  # Build source list (each site with x, y, w)
  source_list <- lapply(site_ids, function(sid) {
    mask <- c_source == sid
    list(
      x = X_source[mask, , drop = FALSE],
      y = Y_source[mask],
      w = A_source[mask]
    )
  })
  
  # Extract target control data (if available)
  if (!is.null(Y_target_control) && length(Y_target_control) > 0) {
    valid_idx <- !is.na(Y_target_control)
    if (sum(valid_idx) >= 10) {
      X_t0 <- X_target[valid_idx, , drop = FALSE]
      Y_t0 <- Y_target_control[valid_idx]
      
      # Run source detection (uses Option B specific function)
      selected_ids <- detect_transferable_sources_optionb(
        X_t0, Y_t0, source_list, 
        C0 = C0, alpha = alpha, nfolds = nfolds, verbose = verbose
      )
    } else {
      if (verbose) cat("  Insufficient target control data, using all sources.\n")
      selected_ids <- seq_along(source_list)
    }
  } else {
    if (verbose) cat("  No target control data, using all sources.\n")
    selected_ids <- seq_along(source_list)
  }
  
  # Map selected_ids back to site_ids
  selected_sources <- site_ids[selected_ids]
  
  # =========================================================================
  # STAGE 1: Restrict to selected sources (NO WEIGHTING)
  # =========================================================================
  # Simply subset. No soft selection, no importance weighting.
  # This maintains the deterministic nature of glmtrans selection.
  # =========================================================================
  if (verbose) cat("Stage 1: Restricting to selected sources...\n")
  
  selected_mask <- c_source %in% selected_sources
  X_src_good <- X_source[selected_mask, , drop = FALSE]
  A_src_good <- A_source[selected_mask]
  Y_src_good <- Y_source[selected_mask]
  
  if (verbose) {
    cat(sprintf("  Using %d/%d source observations from %d/%d sites.\n",
                nrow(X_src_good), n_source, 
                length(selected_sources), length(site_ids)))
  }
  
  # =========================================================================
  # STAGE 2: Fit DR CATE on selected sources
  # =========================================================================
  # DR learning happens WHERE IDENTIFICATION HOLDS: on the sources.
  # No target treated data is used or needed.
  # =========================================================================
  if (verbose) cat("Stage 2: Fitting DR CATE on selected sources...\n")
  
  # Separate by treatment arm
  ctrl_mask <- A_src_good == 0
  trt_mask <- A_src_good == 1
  
  X_src_ctrl <- X_src_good[ctrl_mask, , drop = FALSE]
  Y_src_ctrl <- Y_src_good[ctrl_mask]
  X_src_trt <- X_src_good[trt_mask, , drop = FALSE]
  Y_src_trt <- Y_src_good[trt_mask]
  
  # Fit outcome models μ̂₀, μ̂₁ on SOURCES
  mu0_cv <- cv.glmnet(X_src_ctrl, Y_src_ctrl, alpha = alpha, nfolds = nfolds)
  mu1_cv <- cv.glmnet(X_src_trt, Y_src_trt, alpha = alpha, nfolds = nfolds)
  
  # Estimate propensity on sources (assumed constant within sources)
  e_hat <- mean(A_src_good)
  e_hat <- pmax(pmin(e_hat, 0.99), 0.01)
  
  # Get outcome predictions on all selected source data
  mu0_src <- as.vector(predict(mu0_cv, X_src_good, s = "lambda.min"))
  mu1_src <- as.vector(predict(mu1_cv, X_src_good, s = "lambda.min"))
  
  # Compute DR pseudo-outcomes on SOURCES
  # Γᵢ = μ̂₁(Xᵢ) - μ̂₀(Xᵢ) + (Aᵢ - ê)/(ê(1-ê)) · (Yᵢ - μ̂_{Aᵢ}(Xᵢ))
  residual <- ifelse(A_src_good == 1, 
                     Y_src_good - mu1_src, 
                     Y_src_good - mu0_src)
  pseudo_src <- (mu1_src - mu0_src) + 
                (A_src_good - e_hat) / (e_hat * (1 - e_hat)) * residual
  
  # Fit CATE model τ̂^src(x) on source pseudo-outcomes
  cate_cv <- cv.glmnet(X_src_good, pseudo_src, alpha = alpha, nfolds = nfolds)
  
  # =========================================================================
  # STAGE 3: Transport to target
  # =========================================================================
  # Direct transport: τ̂_target(x) := τ̂^src(x)
  # No further correction (we have no target treated data to correct with)
  # =========================================================================
  if (verbose) cat("Stage 3: Transporting CATE to target...\n")
  
  # Get predictions on target
  tau_target <- as.vector(predict(cate_cv, X_target, s = "lambda.min"))
  mu0_target <- as.vector(predict(mu0_cv, X_target, s = "lambda.min"))
  mu1_target <- as.vector(predict(mu1_cv, X_target, s = "lambda.min"))
  
  result <- list(
    # Models (for prediction on new data)
    mu0_model = mu0_cv,
    mu1_model = mu1_cv,
    cate_model = cate_cv,
    
    # Source detection info (for paper reporting)
    selected_sources = selected_sources,
    n_sources_total = length(site_ids),
    n_sources_used = length(selected_sources),
    n_obs_total = n_source,
    n_obs_used = nrow(X_src_good),
    
    # Target predictions (main output)
    tau_target = tau_target,
    mu0_target = mu0_target,
    mu1_target = mu1_target,
    ate_hat = mean(tau_target),
    
    # Diagnostics
    source_propensity = e_hat
  )
  
  class(result) <- "glmtrans_option_b"
  
  if (verbose) {
    cat(sprintf("  ATE estimate: %.4f\n", result$ate_hat))
    cat("✓ Option B fit complete.\n")
  }
  
  return(result)
}

#' Predict CATE from Option B model
predict_option_b <- function(fit, X_new) {
  X_new <- as.matrix(X_new)
  pred <- predict(fit$cate_model, X_new, s = "lambda.min")
  return(as.vector(pred))
}

# =============================================================================
# Propensity Score Transfer Learning
# =============================================================================

#' Transfer learning for propensity score estimation
#' 
#' @param X_target Target features
#' @param A_target Target treatments
#' @param X_source Source features
#' @param A_source Source treatments  
#' @param c_source Source site indicators
#' @param transfer_source_id Which sources
#' @param alpha Elastic-net mixing
#' @param nfolds CV folds
#' @param verbose Print progress
#' @return List with fitted propensity model
fit_glmtrans_propensity <- function(X_target, A_target,
                                    X_source, A_source, c_source,
                                    transfer_source_id = "auto",
                                    alpha = 1,
                                    nfolds = 5,
                                    verbose = FALSE) {
  
  X_target <- as.matrix(X_target)
  A_target <- as.vector(A_target)
  
  fit <- fit_glmtrans(
    X_target = X_target,
    Y_target = A_target,
    X_source = X_source,
    Y_source = A_source,
    c_source = c_source,
    family = "binomial",
    transfer_source_id = transfer_source_id,
    alpha = alpha,
    nfolds = nfolds,
    verbose = verbose
  )
  
  return(fit)
}

#' Predict propensity scores
predict_propensity <- function(fit, X_new) {
  pred <- predict_glmtrans(fit, X_new, type = "response")
  return(pmax(pmin(pred, 0.99), 0.01))  # Clip for stability
}

# =============================================================================
# Source Detection (Transferability Analysis)
# =============================================================================

#' Detect which sources are transferable
#' 
#' @param X_target Target features
#' @param Y_target Target responses
#' @param X_source Source features
#' @param Y_source Source responses
#' @param c_source Source site indicators
#' @param family Response family
#' @param C0 Threshold constant (default 2)
#' @param verbose Print progress
#' @return List with transfer_source_ids, source_losses, threshold
detect_transferable_sources <- function(X_target, Y_target,
                                        X_source, Y_source, c_source,
                                        family = "gaussian",
                                        C0 = 2,
                                        verbose = FALSE) {
  
  target <- format_data(X_target, Y_target)
  source <- format_source_data(X_source, Y_source, c_source)
  
  detection <- source_detection(
    target = target,
    source = source,
    family = family,
    C0 = C0,
    detection.info = verbose
  )
  
  return(list(
    transfer_source_ids = detection$transfer.source.id,
    source_losses = detection$source.loss,
    target_valid_loss = detection$target.valid.loss,
    threshold = detection$threshold
  ))
}

# =============================================================================
# Baseline: Target-Only Lasso (No Transfer)
# =============================================================================

#' Fit CATE using target data only (no transfer learning)
#' 
#' This serves as a baseline for comparison.
fit_target_only_cate <- function(X_target, A_target, Y_target,
                                 alpha = 1, nfolds = 5, verbose = FALSE) {
  
  X_target <- as.matrix(X_target)
  A_target <- as.vector(A_target)
  Y_target <- as.vector(Y_target)
  
  target_control <- A_target == 0
  target_treated <- A_target == 1
  
  # Fit μ₀ on target control
  mu0_fit <- NULL
  if (sum(target_control) > 5) {
    mu0_fit <- cv.glmnet(X_target[target_control, , drop = FALSE],
                         Y_target[target_control],
                         alpha = alpha, nfolds = nfolds)
  }
  
  # Fit μ₁ on target treated  
  mu1_fit <- NULL
  if (sum(target_treated) > 5) {
    mu1_fit <- cv.glmnet(X_target[target_treated, , drop = FALSE],
                         Y_target[target_treated],
                         alpha = alpha, nfolds = nfolds)
  }
  
  result <- list(mu0_fit = mu0_fit, mu1_fit = mu1_fit)
  class(result) <- "target_only_cate"
  return(result)
}

#' Predict CATE from target-only model
predict_target_only <- function(fit, X_new) {
  X_new <- as.matrix(X_new)
  n <- nrow(X_new)
  
  mu0 <- if (!is.null(fit$mu0_fit)) {
    as.vector(predict(fit$mu0_fit, X_new, s = "lambda.min"))
  } else {
    rep(0, n)
  }
  
  mu1 <- if (!is.null(fit$mu1_fit)) {
    as.vector(predict(fit$mu1_fit, X_new, s = "lambda.min"))
  } else {
    rep(0, n)
  }
  
  return(mu1 - mu0)
}

# =============================================================================
# Baseline: Pooled Source (Naive Transfer)
# =============================================================================

#' Fit CATE by pooling all source data (naive transfer)
#' 
#' This pools all source data without accounting for heterogeneity.
fit_pooled_source_cate <- function(X_source, A_source, Y_source,
                                   alpha = 1, nfolds = 5, verbose = FALSE) {
  
  X_source <- as.matrix(X_source)
  A_source <- as.vector(A_source)
  Y_source <- as.vector(Y_source)
  
  source_control <- A_source == 0
  source_treated <- A_source == 1
  
  # Fit μ₀ on pooled source control
  mu0_fit <- NULL
  if (sum(source_control) > 5) {
    mu0_fit <- cv.glmnet(X_source[source_control, , drop = FALSE],
                         Y_source[source_control],
                         alpha = alpha, nfolds = nfolds)
  }
  
  # Fit μ₁ on pooled source treated
  mu1_fit <- NULL
  if (sum(source_treated) > 5) {
    mu1_fit <- cv.glmnet(X_source[source_treated, , drop = FALSE],
                         Y_source[source_treated],
                         alpha = alpha, nfolds = nfolds)
  }
  
  result <- list(mu0_fit = mu0_fit, mu1_fit = mu1_fit)
  class(result) <- "pooled_source_cate"
  return(result)
}

#' Predict CATE from pooled source model
predict_pooled_source <- function(fit, X_new) {
  # Same as target_only
  predict_target_only(fit, X_new)
}

# =============================================================================
# Test Function
# =============================================================================

test_glmtrans_estimators <- function() {
  cat("============================================================\n")
  cat("Testing glmtrans R implementation\n")
  cat("============================================================\n\n")
  
  set.seed(42)
  
  # Generate synthetic data
  p <- 30
  n_source <- 500
  n_target <- 100
  n_sites <- 3
  
  # True coefficients
  alpha0 <- rep(0, p)
  alpha0[1:5] <- c(0.5, -0.3, 0.8, -0.2, 0.4)
  
  alpha1 <- rep(0, p)
  alpha1[1:5] <- c(0.3, -0.5, 0.6, -0.1, 0.3)
  
  # Source data
  X_source <- matrix(rnorm(n_source * n_sites * p), ncol = p)
  c_source <- rep(1:n_sites, each = n_source)
  A_source <- rbinom(n_source * n_sites, 1, 0.5)
  
  mu0_source <- X_source %*% alpha0
  mu1_source <- X_source %*% alpha1
  Y_source <- (1 - A_source) * mu0_source + A_source * mu1_source + rnorm(n_source * n_sites) * 0.3
  
  # Target data
  X_target <- matrix(rnorm(n_target * p), ncol = p)
  A_target <- rbinom(n_target, 1, 0.5)
  
  mu0_target <- X_target %*% alpha0
  mu1_target <- X_target %*% alpha1
  tau_true <- mu1_target - mu0_target
  Y_target <- (1 - A_target) * mu0_target + A_target * mu1_target + rnorm(n_target) * 0.3
  
  cat(sprintf("Source: %d samples across %d sites\n", nrow(X_source), n_sites))
  cat(sprintf("Target: %d samples (%d control, %d treated)\n", 
              n_target, sum(A_target == 0), sum(A_target == 1)))
  cat(sprintf("True ATE: %.4f\n", mean(tau_true)))
  
  # Test 1: Source detection
  cat("\n--- Test 1: Source Detection ---\n")
  detection <- detect_transferable_sources(
    X_target[A_target == 0, ], Y_target[A_target == 0],
    X_source[A_source == 0, ], Y_source[A_source == 0], c_source[A_source == 0],
    verbose = TRUE
  )
  cat(sprintf("Transferable sources: %s\n", paste(detection$transfer_source_ids, collapse = ", ")))
  
  # Test 2: Plug-in CATE
  cat("\n--- Test 2: Glmtrans Plug-in CATE ---\n")
  plugin_fit <- fit_glmtrans_cate(
    X_source, A_source, Y_source, c_source,
    X_target, A_target, Y_target,
    transfer_source_id = "auto",
    verbose = TRUE
  )
  tau_plugin <- predict_cate(plugin_fit, X_target)
  pehe_plugin <- sqrt(mean((tau_plugin - tau_true)^2))
  ate_err_plugin <- abs(mean(tau_plugin) - mean(tau_true))
  cat(sprintf("PEHE: %.4f\n", pehe_plugin))
  cat(sprintf("|ATE Error|: %.4f\n", ate_err_plugin))
  
  # Test 3: DR CATE
  cat("\n--- Test 3: Glmtrans DR CATE ---\n")
  dr_fit <- fit_glmtrans_dr(
    X_source, A_source, Y_source, c_source,
    X_target, A_target, Y_target,
    transfer_source_id = "auto",
    verbose = TRUE
  )
  tau_dr <- predict_dr(dr_fit, X_target)
  pehe_dr <- sqrt(mean((tau_dr - tau_true)^2))
  ate_err_dr <- abs(mean(tau_dr) - mean(tau_true))
  cat(sprintf("PEHE: %.4f\n", pehe_dr))
  cat(sprintf("|ATE Error|: %.4f\n", ate_err_dr))
  
  # Test 4: Target-only baseline
  cat("\n--- Test 4: Target-Only Baseline ---\n")
  target_fit <- fit_target_only_cate(X_target, A_target, Y_target)
  tau_target <- predict_target_only(target_fit, X_target)
  pehe_target <- sqrt(mean((tau_target - tau_true)^2))
  ate_err_target <- abs(mean(tau_target) - mean(tau_true))
  cat(sprintf("PEHE: %.4f\n", pehe_target))
  cat(sprintf("|ATE Error|: %.4f\n", ate_err_target))
  
  # Summary
  cat("\n============================================================\n")
  cat("SUMMARY\n")
  cat("============================================================\n")
  cat(sprintf("%-25s | PEHE   | ATE Err | Improvement\n", "Method"))
  cat(paste(rep("-", 60), collapse = ""), "\n")
  cat(sprintf("%-25s | %.4f | %.4f  | baseline\n", "Target-Only", pehe_target, ate_err_target))
  cat(sprintf("%-25s | %.4f | %.4f  | %.1f%%\n", "Glmtrans Plugin", pehe_plugin, ate_err_plugin,
              (pehe_target - pehe_plugin) / pehe_target * 100))
  cat(sprintf("%-25s | %.4f | %.4f  | %.1f%%\n", "Glmtrans DR", pehe_dr, ate_err_dr,
              (pehe_target - pehe_dr) / pehe_target * 100))
  
  cat("\n✓ All tests completed!\n")
}

# Run tests if executed directly
if (sys.nframe() == 0) {
  test_glmtrans_estimators()
}
