"""
Generate Tables/P3_Disconnected_PEHE.tex from the gold_fair_dim sweep results.

The disconnected regime (m1=0, m0=50) is the m1=0 slice of the gold_fair_dim
sweep run with (m0, m1) tuples. This script reads the aggregated CSV, formats
PEHE / ATE Error / ECE at 2 decimal places, bolds the true per-column minimum
(with ties broken at the raw value level), and writes the LaTeX table.

Usage:
    python scripts/generate_disconnected_pehe_table.py

    # Custom paths:
    python scripts/generate_disconnected_pehe_table.py \\
        --input  results/gold_fair_dim_glmtrans_remote_tuples/results_agg_gold_fair_dim_sweep.csv \\
        --output Paper/Transfer-Learning-for-Individual-Patient-Data-for-Clinical-Trials/Tables/P3_Disconnected_PEHE.tex
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)

DEFAULT_INPUT = os.path.join(
    REPO_ROOT,
    "results", "gold_fair_dim_glmtrans_remote_tuples",
    "results_agg_gold_fair_dim_sweep.csv",
)
DEFAULT_OUTPUT = os.path.join(
    REPO_ROOT,
    "Paper",
    "Transfer-Learning-for-Individual-Patient-Data-for-Clinical-Trials",
    "Tables",
    "P3_Disconnected_PEHE.tex",
)

# Disconnected regime filter
M0 = 50
M1 = 0

# Method display names and row order
METHOD_ORDER = [
    "ProxyOnly",
    "IPWTransport",
    "OutcomeModelTransport",
    "EntropyBalancing",
    "Glmtrans_OptionB",
]
METHOD_LABELS = {
    "ProxyOnly":            "ProxyOnly",
    "IPWTransport":         "IPW-Transport",
    "OutcomeModelTransport":"OM-Transport",
    "EntropyBalancing":     "EntropyBal",
    "Glmtrans_OptionB":     "Proposed-B",
}

P_DIMS = [10, 20, 50, 100]

# Metrics: (mean_col, sd_col, panel_label, arrow)
PANELS = [
    ("pehe_mean",        "pehe_sd",        r"\textbf{(a) PEHE $\downarrow$}",       "lower"),
    ("ate_abs_err_mean", "ate_abs_err_sd",  r"\textbf{(b) ATE Error $\downarrow$}",  "lower"),
    ("tau_ece_mean",     "tau_ece_sd",      r"\textbf{(c) ECE $\downarrow$}",        "lower"),
]

DECIMALS = 2


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt(val: float, sd: float, bold: bool, decimals: int = DECIMALS) -> str:
    """Format 'val±sd' with optional bolding."""
    fmt_str = f"{{:.{decimals}f}}"
    mean_s = fmt_str.format(val)
    sd_s   = fmt_str.format(sd)
    cell = rf"{mean_s}{{\tiny$\pm${sd_s}}}"
    if bold:
        cell = rf"\textbf{{{cell}}}"
    return cell


def build_panel(pivot_mean: pd.DataFrame, pivot_sd: pd.DataFrame,
                direction: str) -> list[str]:
    """Return list of LaTeX table rows for one panel."""
    rows = []
    for method in METHOD_ORDER:
        means = pivot_mean.loc[method]
        sds   = pivot_sd.loc[method]
        # Determine per-column winner(s) using raw values
        cells = []
        for p in P_DIMS:
            col_means = pivot_mean[p]
            best_val  = col_means.min() if direction == "lower" else col_means.max()
            is_best   = np.isclose(means[p], best_val, atol=1e-8)
            cells.append(fmt(means[p], sds[p], bold=is_best))
        label = METHOD_LABELS[method]
        rows.append(f"{label} & " + " & ".join(cells) + r" \\")
    return rows


def build_tabular(panel_rows: list[str]) -> list[str]:
    lines = [
        r"\begin{tabular}{@{}lcccc@{}}",
        r"\hline",
        r"\textbf{Method} & $p$=10 & $p$=20 & $p$=50 & $p$=100 \\",
        r"\hline",
    ] + panel_rows + [
        r"\hline",
        r"\end{tabular}",
    ]
    return lines


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def generate(input_path: str, output_path: str) -> None:
    df = pd.read_csv(input_path)

    # Filter to disconnected regime
    df = df[(df["m1"] == M1) & (df["m0"] == M0)]
    df = df[df["method"].isin(METHOD_ORDER)]

    if df.empty:
        sys.exit(
            f"ERROR: No rows found for m1={M1}, m0={M0} in {input_path}.\n"
            "Check that the correct results CSV is being used."
        )

    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3pt}",
        r"\renewcommand{\arraystretch}{1.1}",
        r"\caption{",
        r"\textbf{Disconnected regime ($m_1=0$):} Only target placebo available ($m_0=50$).",
        r"Methods requiring target treated data are undefined.",
        r"Mean{\tiny$\pm$SD} over 100 reps. Best in \textbf{bold}.",
        r"}",
        r"\label{tab:disconnected_pehe}",
        r"\vspace{2pt}",
        "",
    ]

    for i, (mean_col, sd_col, panel_label, direction) in enumerate(PANELS):
        pivot_mean = (
            df.pivot_table(index="method", columns="p_dim",
                           values=mean_col, aggfunc="first")
            .reindex(index=METHOD_ORDER, columns=P_DIMS)
        )
        pivot_sd = (
            df.pivot_table(index="method", columns="p_dim",
                           values=sd_col, aggfunc="first")
            .reindex(index=METHOD_ORDER, columns=P_DIMS)
        )

        panel_rows = build_panel(pivot_mean, pivot_sd, direction)

        lines.append(panel_label + r" \\[2pt]")
        lines.extend(build_tabular(panel_rows))

        if i < len(PANELS) - 1:
            lines += ["", r"\vspace{6pt}"]

    lines.append(r"\end{table}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Written: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate P3_Disconnected_PEHE.tex from gold_fair_dim sweep CSV."
    )
    parser.add_argument(
        "--input", default=DEFAULT_INPUT,
        help=f"Path to results_agg CSV (default: {DEFAULT_INPUT})"
    )
    parser.add_argument(
        "--output", default=DEFAULT_OUTPUT,
        help=f"Output .tex path (default: {DEFAULT_OUTPUT})"
    )
    args = parser.parse_args()
    generate(args.input, args.output)
