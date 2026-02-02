"""
Benchmark Schema: Dataclasses and validation for experiment results.

This module defines the canonical data model for all benchmark experiments,
ensuring consistent schema across all sweeps and analyses.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Set
from enum import Enum
import hashlib
import json
import pandas as pd
import numpy as np


# =============================================================================
# Enums
# =============================================================================

class Feasibility(str, Enum):
    """Method feasibility classification."""
    FEASIBLE_RESTRICTED = "FeasibleRestricted"      # Uses only target placebo
    ORACLE_TARGET_TREATED = "OracleTargetTreated"   # Uses target treated (oracle)
    INFEASIBLE_BY_DESIGN = "InfeasibleByDesign"     # Cannot be computed in setting


class NonlinType(str, Enum):
    """Types of nonlinear corrections for A5 violation."""
    NONE = "none"
    INTERACTIONS = "interactions"
    PIECEWISE = "piecewise"
    TREE = "tree"
    MLP = "mlp"


class GraphType(str, Enum):
    """Treatment network graph types."""
    CHAIN = "chain"
    STAR = "star"
    TWO_COMPONENTS = "two_components"
    FULLY_CONNECTED = "fully_connected"


# =============================================================================
# Dataclasses
# =============================================================================

@dataclass(frozen=True)
class Scenario:
    """
    Immutable scenario configuration.
    
    All benchmark-specific parameters are optional; fill only what's relevant.
    The scenario_id is auto-generated from the configuration hash.
    """
    benchmark_id: str
    
    # Common knobs
    m0: Optional[int] = None                    # Target placebo for estimation
    m1: Optional[int] = None                    # Target treated for estimation
    n_proxy_total: Optional[int] = None         # Total proxy samples
    C_sources: Optional[int] = None             # Number of source sites
    p_dim: Optional[int] = None                 # Feature dimensionality
    
    # Site allocation
    imbalance_ratio: Optional[float] = None     # Max/min site size ratio
    dirichlet_alpha: Optional[float] = None     # Dirichlet concentration
    
    # Shift / overlap
    shift_strength: Optional[float] = None      # Covariate shift knob
    overlap_strength: Optional[float] = None    # Overlap/positivity knob
    
    # A5 knobs (correction misspecification)
    a5_effective_sparsity: Optional[float] = None  # k/p or power-law alpha
    a5_nonlin_type: Optional[str] = None           # NonlinType value
    a5_nonlin_strength: Optional[float] = None     # Scale of nonlinear term
    
    # A6 knobs (transfer misspecification)
    a6_rank_true: Optional[int] = None          # True rank of M*
    a6_rank_fit: Optional[int] = None           # Assumed rank in Step B
    a6_nonlin_rho: Optional[float] = None       # Mixing param for nonlinear transfer
    nontransfer_scale: Optional[float] = None   # Scale of non-transferable component
    
    # Network knobs
    K_treatments: Optional[int] = None          # Number of treatments
    graph_type: Optional[str] = None            # GraphType value
    
    # Noise settings
    noise_scale: Optional[float] = None
    noise_df: Optional[float] = None            # t-distribution df (None = Gaussian)
    contamination_prob: Optional[float] = None  # Contamination mixture prob
    
    @property
    def scenario_id(self) -> str:
        """Generate stable hash from non-None parameters."""
        params = {k: v for k, v in asdict(self).items() if v is not None}
        param_str = json.dumps(params, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, including scenario_id."""
        d = asdict(self)
        d['scenario_id'] = self.scenario_id
        return d


@dataclass(frozen=True)
class MethodSpec:
    """
    Method specification with feasibility labeling.
    
    This defines what data each method uses and its feasibility status
    in restricted vs oracle settings.
    """
    method: str
    feasibility_restricted: Feasibility  # When target treated unavailable
    feasibility_oracle: Feasibility      # When target treated available
    uses_target_placebo: bool = True
    uses_target_treated: bool = False
    uses_source_data: bool = True
    description: Optional[str] = None
    
    def get_feasibility(self, has_target_treated: bool) -> Feasibility:
        """Get feasibility based on data availability."""
        return self.feasibility_oracle if has_target_treated else self.feasibility_restricted


@dataclass
class RepResult:
    """
    Single replicate result.
    
    Contains all metrics and diagnostics for one (scenario, rep, method) tuple.
    """
    # Identifiers
    scenario_id: str
    benchmark_id: str
    rep: int
    method: str
    feasibility: str
    seed: Optional[int] = None
    
    # Data usage flags
    uses_target_placebo: bool = True
    uses_target_treated: bool = False
    uses_source_data: bool = True
    
    # Core metrics
    pehe: Optional[float] = None
    tau_corr: Optional[float] = None           # Spearman correlation
    ate_hat: Optional[float] = None
    ate_true: Optional[float] = None
    ate_abs_err: Optional[float] = None
    mu0_rmse: Optional[float] = None
    mu1_rmse: Optional[float] = None
    mu0_ece: Optional[float] = None
    tau_ece: Optional[float] = None
    policy_regret: Optional[float] = None
    qini_auc: Optional[float] = None
    
    # Stage-2 diagnostics
    stage2_lambda: Optional[float] = None
    stage2_n_selected: Optional[int] = None
    stage2_l2_norm_beta: Optional[float] = None
    
    # Transfer diagnostics (Step B)
    stepb_M_fro_norm: Optional[float] = None
    stepb_M_spectral_norm: Optional[float] = None
    stepb_M_effective_rank: Optional[float] = None
    stepb_n_sites_used: Optional[int] = None
    
    # Weighting diagnostics
    ess_weights: Optional[float] = None
    max_weight_p99: Optional[float] = None
    
    # Measured shift (not the knob, the actual measured value)
    shift_metric_w1: Optional[float] = None
    shift_metric_mmd: Optional[float] = None
    
    # Runtime
    runtime_sec: Optional[float] = None
    
    # Uncertainty (for coverage)
    ate_se_if: Optional[float] = None
    ate_se_boot: Optional[float] = None
    ate_ci_low: Optional[float] = None
    ate_ci_high: Optional[float] = None
    ate_covered_95: Optional[int] = None       # 0/1 indicator
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for DataFrame row."""
        return asdict(self)


@dataclass(frozen=True)
class PlotSpec:
    """
    Plot specification for automated figure generation.
    
    Defines how to generate a specific plot from results DataFrames.
    """
    name: str
    df_source: str                              # "results_rep" or "results_agg"
    plot_type: str                              # "line" | "bar" | "heatmap" | "violin" | "scatter"
    x: str
    y: str
    hue: Optional[str] = None
    facet_col: Optional[str] = None
    facet_row: Optional[str] = None
    yerr: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None   # column -> allowed values
    title: Optional[str] = None
    xlabel: Optional[str] = None
    ylabel: Optional[str] = None
    xscale: Optional[str] = None               # "log", "linear"
    yscale: Optional[str] = None
    hline: Optional[float] = None              # Horizontal reference line
    vline: Optional[float] = None              # Vertical reference line


# =============================================================================
# Method Registry
# =============================================================================

# Core methods
METHOD_REGISTRY: Dict[str, MethodSpec] = {
    # No transfer baseline
    "NoTransfer": MethodSpec(
        method="NoTransfer",
        feasibility_restricted=Feasibility.FEASIBLE_RESTRICTED,
        feasibility_oracle=Feasibility.ORACLE_TARGET_TREATED,
        uses_target_placebo=True,
        uses_target_treated=True,  # Needs treated for CATE
        uses_source_data=False,
        description="Target-only DR-Learner, no source data"
    ),
    
    # Proxy-only baseline
    "ProxyOnly": MethodSpec(
        method="ProxyOnly",
        feasibility_restricted=Feasibility.FEASIBLE_RESTRICTED,
        feasibility_oracle=Feasibility.FEASIBLE_RESTRICTED,
        uses_target_placebo=False,
        uses_target_treated=False,
        uses_source_data=True,
        description="Source-only proxy model, no target anchoring"
    ),
    
    # Anchor-only baseline
    "AnchorOnly": MethodSpec(
        method="AnchorOnly",
        feasibility_restricted=Feasibility.FEASIBLE_RESTRICTED,
        feasibility_oracle=Feasibility.ORACLE_TARGET_TREATED,
        uses_target_placebo=True,
        uses_target_treated=True,  # Needs treated for direct correction
        uses_source_data=True,
        description="Proxy + target anchoring (needs both arms)"
    ),
    
    # Proposed Option A (needs target treated)
    "ProposedA": MethodSpec(
        method="ProposedA",
        feasibility_restricted=Feasibility.INFEASIBLE_BY_DESIGN,
        feasibility_oracle=Feasibility.ORACLE_TARGET_TREATED,
        uses_target_placebo=True,
        uses_target_treated=True,
        uses_source_data=True,
        description="Proposed with direct target corrections (Option A)"
    ),
    
    # Proposed Option B with linear Step B
    "ProposedB_LinearStepB": MethodSpec(
        method="ProposedB_LinearStepB",
        feasibility_restricted=Feasibility.FEASIBLE_RESTRICTED,
        feasibility_oracle=Feasibility.FEASIBLE_RESTRICTED,
        uses_target_placebo=True,
        uses_target_treated=False,
        uses_source_data=True,
        description="Proposed with linear transfer operator (Option B)"
    ),
    
    # Proposed Option B with kernel Step B
    "ProposedB_KernelStepB": MethodSpec(
        method="ProposedB_KernelStepB",
        feasibility_restricted=Feasibility.FEASIBLE_RESTRICTED,
        feasibility_oracle=Feasibility.FEASIBLE_RESTRICTED,
        uses_target_placebo=True,
        uses_target_treated=False,
        uses_source_data=True,
        description="Proposed with kernel transfer operator (Option B)"
    ),
    
    # IPD hierarchical model
    "IPD_RE": MethodSpec(
        method="IPD_RE",
        feasibility_restricted=Feasibility.ORACLE_TARGET_TREATED,
        feasibility_oracle=Feasibility.ORACLE_TARGET_TREATED,
        uses_target_placebo=True,
        uses_target_treated=True,
        uses_source_data=True,
        description="IPD random-effects hierarchical model"
    ),
    
    # AIPW Transport
    "AIPWTransport": MethodSpec(
        method="AIPWTransport",
        feasibility_restricted=Feasibility.FEASIBLE_RESTRICTED,
        feasibility_oracle=Feasibility.FEASIBLE_RESTRICTED,
        uses_target_placebo=True,
        uses_target_treated=False,
        uses_source_data=True,
        description="AIPW with site reweighting for transport"
    ),
    
    # Entropy balancing
    "EntropyBalancing": MethodSpec(
        method="EntropyBalancing",
        feasibility_restricted=Feasibility.FEASIBLE_RESTRICTED,
        feasibility_oracle=Feasibility.FEASIBLE_RESTRICTED,
        uses_target_placebo=True,
        uses_target_treated=False,
        uses_source_data=True,
        description="Entropy balancing weights for transport"
    ),
    
    # DR-Learner with site ID
    "DRLearner_PooledWithSite": MethodSpec(
        method="DRLearner_PooledWithSite",
        feasibility_restricted=Feasibility.ORACLE_TARGET_TREATED,
        feasibility_oracle=Feasibility.ORACLE_TARGET_TREATED,
        uses_target_placebo=True,
        uses_target_treated=True,
        uses_source_data=True,
        description="Pooled DR-Learner with site ID feature"
    ),
    
    # DR-Learner without site ID
    "DRLearner_PooledNoSite": MethodSpec(
        method="DRLearner_PooledNoSite",
        feasibility_restricted=Feasibility.ORACLE_TARGET_TREATED,
        feasibility_oracle=Feasibility.ORACLE_TARGET_TREATED,
        uses_target_placebo=True,
        uses_target_treated=True,
        uses_source_data=True,
        description="Pooled DR-Learner without site ID feature"
    ),
    
    # TARNet
    "TARNet": MethodSpec(
        method="TARNet",
        feasibility_restricted=Feasibility.ORACLE_TARGET_TREATED,
        feasibility_oracle=Feasibility.ORACLE_TARGET_TREATED,
        uses_target_placebo=True,
        uses_target_treated=True,
        uses_source_data=True,
        description="TARNet representation learning"
    ),
}


def get_method_spec(method_name: str) -> MethodSpec:
    """Get method specification by name."""
    if method_name not in METHOD_REGISTRY:
        raise ValueError(f"Unknown method: {method_name}. Available: {list(METHOD_REGISTRY.keys())}")
    return METHOD_REGISTRY[method_name]


def get_feasible_methods(has_target_treated: bool) -> List[str]:
    """Get list of methods feasible given data availability."""
    feasible = []
    for name, spec in METHOD_REGISTRY.items():
        feas = spec.get_feasibility(has_target_treated)
        if feas != Feasibility.INFEASIBLE_BY_DESIGN:
            feasible.append(name)
    return feasible


# =============================================================================
# Column Schemas
# =============================================================================

REQUIRED_ID_COLS = [
    'benchmark_id', 'scenario_id', 'rep', 'method', 'feasibility'
]

SCENARIO_PARAM_COLS = [
    'm0', 'm1', 'n_proxy_total', 'C_sources', 'p_dim',
    'imbalance_ratio', 'dirichlet_alpha',
    'shift_strength', 'overlap_strength',
    'a5_effective_sparsity', 'a5_nonlin_type', 'a5_nonlin_strength',
    'a6_rank_true', 'a6_rank_fit', 'a6_nonlin_rho', 'nontransfer_scale',
    'K_treatments', 'graph_type',
    'noise_scale', 'noise_df', 'contamination_prob'
]

CORE_METRIC_COLS = [
    'pehe', 'tau_corr', 'ate_hat', 'ate_true', 'ate_abs_err',
    'mu0_rmse', 'mu1_rmse', 'mu0_ece', 'tau_ece',
    'policy_regret', 'qini_auc'
]

DIAGNOSTIC_COLS = [
    'stage2_lambda', 'stage2_n_selected', 'stage2_l2_norm_beta',
    'stepb_M_fro_norm', 'stepb_M_spectral_norm', 'stepb_M_effective_rank', 'stepb_n_sites_used',
    'ess_weights', 'max_weight_p99',
    'shift_metric_w1', 'shift_metric_mmd',
    'runtime_sec'
]

UNCERTAINTY_COLS = [
    'ate_se_if', 'ate_se_boot', 'ate_ci_low', 'ate_ci_high', 'ate_covered_95'
]

# Benchmark-specific required columns
BENCHMARK_REQUIRED_COLS: Dict[str, List[str]] = {
    'gold_sweep': ['m0', 'n_proxy_total'],
    'proxy_sweep': ['n_proxy_total', 'm0'],
    'site_imbalance': ['n_proxy_total', 'm0'],  # + imbalance_ratio OR dirichlet_alpha
    'covariate_shift': ['shift_strength', 'm0', 'n_proxy_total'],
    'overlap_stress': ['overlap_strength', 'm0', 'n_proxy_total'],
    'a5_dense': ['a5_effective_sparsity', 'm0', 'n_proxy_total'],
    'a5_nonlinear': ['a5_nonlin_type', 'a5_nonlin_strength', 'm0', 'n_proxy_total'],
    'a6_rank': ['a6_rank_true', 'a6_rank_fit', 'm0', 'n_proxy_total'],
    'a6_nonlinear': ['a6_nonlin_rho', 'm0', 'n_proxy_total'],
    'disconnected_graph': ['K_treatments', 'graph_type', 'm0'],
    'coverage': ['ate_ci_low', 'ate_ci_high', 'ate_covered_95'],
    'lambda_stability': ['m0', 'stage2_lambda', 'stage2_n_selected'],
}


# =============================================================================
# Validation
# =============================================================================

def validate_results_rep(df: pd.DataFrame, benchmark_id: Optional[str] = None) -> None:
    """
    Validate rep-level results DataFrame.
    
    Parameters
    ----------
    df : pd.DataFrame
        The results DataFrame to validate
    benchmark_id : str, optional
        If provided, also check benchmark-specific required columns
        
    Raises
    ------
    ValueError
        If validation fails
    """
    errors = []
    
    # Check required ID columns
    missing_id = set(REQUIRED_ID_COLS) - set(df.columns)
    if missing_id:
        errors.append(f"Missing ID columns: {missing_id}")
    
    # Check feasibility values
    if 'feasibility' in df.columns:
        valid_feas = {f.value for f in Feasibility}
        invalid_feas = set(df['feasibility'].dropna().unique()) - valid_feas
        if invalid_feas:
            errors.append(f"Invalid feasibility values: {invalid_feas}. Valid: {valid_feas}")
    
    # Check at least one metric present
    metrics_present = set(CORE_METRIC_COLS) & set(df.columns)
    if not metrics_present:
        errors.append(f"No core metrics found. Need at least one of: {CORE_METRIC_COLS}")
    
    # Check benchmark-specific columns
    if benchmark_id and benchmark_id in BENCHMARK_REQUIRED_COLS:
        required = BENCHMARK_REQUIRED_COLS[benchmark_id]
        missing = set(required) - set(df.columns)
        if missing:
            errors.append(f"Benchmark '{benchmark_id}' missing required columns: {missing}")
    
    # Check for duplicate (scenario_id, rep, method) tuples
    if all(c in df.columns for c in ['scenario_id', 'rep', 'method']):
        dups = df.duplicated(subset=['scenario_id', 'rep', 'method'], keep=False)
        if dups.any():
            n_dups = dups.sum()
            errors.append(f"Found {n_dups} duplicate (scenario_id, rep, method) rows")
    
    if errors:
        raise ValueError("Validation failed:\n  - " + "\n  - ".join(errors))
    
    print(f"✓ Validation passed" + (f" for benchmark '{benchmark_id}'" if benchmark_id else ""))


def validate_method_names(methods: List[str]) -> None:
    """Validate that all method names are in the registry."""
    unknown = set(methods) - set(METHOD_REGISTRY.keys())
    if unknown:
        raise ValueError(f"Unknown methods: {unknown}. Available: {list(METHOD_REGISTRY.keys())}")


# =============================================================================
# DataFrame Construction Helpers
# =============================================================================

def scenario_to_row(scenario: Scenario) -> Dict[str, Any]:
    """Convert Scenario to DataFrame row dict."""
    return scenario.to_dict()


def results_to_dataframe(results: List[RepResult], scenario: Scenario) -> pd.DataFrame:
    """
    Convert list of RepResults to DataFrame with scenario columns.
    
    Parameters
    ----------
    results : list of RepResult
        Results from multiple reps/methods
    scenario : Scenario
        The scenario configuration
        
    Returns
    -------
    pd.DataFrame
        Long-format results DataFrame
    """
    rows = []
    scenario_dict = scenario.to_dict()
    
    for r in results:
        row = r.to_dict()
        # Add scenario params (don't overwrite existing)
        for k, v in scenario_dict.items():
            if k not in row or row[k] is None:
                row[k] = v
        rows.append(row)
    
    return pd.DataFrame(rows)


def create_empty_results_df() -> pd.DataFrame:
    """Create empty DataFrame with correct schema."""
    cols = (
        REQUIRED_ID_COLS + 
        ['seed', 'uses_target_placebo', 'uses_target_treated', 'uses_source_data'] +
        SCENARIO_PARAM_COLS + 
        CORE_METRIC_COLS + 
        DIAGNOSTIC_COLS + 
        UNCERTAINTY_COLS
    )
    return pd.DataFrame(columns=cols)


# =============================================================================
# Seed Generation
# =============================================================================

def generate_seed(scenario_id: str, rep: int, seed0: int) -> int:
    """
    Generate deterministic seed from scenario, rep, and master seed.
    
    Uses hash to ensure reproducibility across runs.
    """
    seed_str = f"{scenario_id}_{rep}_{seed0}"
    return int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16) % (2**31)


if __name__ == "__main__":
    # Quick test
    scenario = Scenario(
        benchmark_id="gold_sweep",
        m0=100,
        m1=0,
        n_proxy_total=2000,
        C_sources=10,
        nontransfer_scale=0.3
    )
    print(f"Scenario ID: {scenario.scenario_id}")
    print(f"Scenario dict: {scenario.to_dict()}")
    
    # Test method registry
    print(f"\nFeasible methods (restricted): {get_feasible_methods(has_target_treated=False)}")
    print(f"Feasible methods (oracle): {get_feasible_methods(has_target_treated=True)}")
