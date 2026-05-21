"""
Generate proxy-gold-paradigm.png for the ICHI 2026 talk.

Three-panel figure illustrating the proxy/gold/anchored estimator paradigm:
  Left:   Proxy  – abundant, low variance, biased (source sites)
  Center: Gold   – scarce, high variance, unbiased (target placebo)
  Right:  Anchored – proposed; sparse correction: low variance + unbiased

Fix history
-----------
2026-05-21  Initial write (no prior script found).
            - Moved "True μ₀(x)" label BELOW the x-axis so it never
              overlaps the info text box in the upper-left.
            - Info text box lowered to y=0.45 axes fraction.
            - savefig uses bbox_inches='tight' to prevent suptitle clipping.
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from scipy.stats import norm

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
GOLD      = "#D5A834"   # dashed vertical line + info box border + gold panel
BLUE      = "#4A7BA4"   # proxy panel curve
OLIVE     = "#6B8F71"   # anchored panel curve
BG        = "#FAFAF8"   # figure background

PROXY_FILL  = "#4A7BA4"
GOLD_FILL   = "#D5A834"
ANCHOR_FILL = "#6B8F71"

# ---------------------------------------------------------------------------
# Distribution parameters
# ---------------------------------------------------------------------------
TRUE_MU = 0.0          # true μ₀(x) – always at x = 0

proxy_mu    =  1.8     # proxy estimator: biased to the right
proxy_sigma =  0.45    # low variance

gold_mu     =  0.0     # gold: unbiased
gold_sigma  =  1.1     # high variance

anchor_mu   =  0.0     # anchored: unbiased
anchor_sigma =  0.42   # low variance (sparse correction)

x = np.linspace(-3.5, 4.5, 1000)

# ---------------------------------------------------------------------------
# Figure layout
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(14, 4.6), facecolor=BG)
fig.patch.set_facecolor(BG)

fig.suptitle(
    "Proxy-gold paradigm: combining abundant-but-biased source data "
    "with scarce-but-calibrated target placebo labels",
    fontsize=10.5, color="#333333", y=1.00,
    fontfamily="DejaVu Sans"
)

# ---------------------------------------------------------------------------
# Shared axis limits
# ---------------------------------------------------------------------------
XLIM = (-3.2, 4.2)
YLIM_TOP = 1.05   # normalised so peak ≈ 1

# ---------------------------------------------------------------------------
# Helper: draw one panel
# ---------------------------------------------------------------------------
def draw_panel(ax, mu, sigma, fill_color, title, title_color,
               info_lines, subtitle,
               show_bias_arrow=False, bias_from=None, bias_to=None):

    ax.set_facecolor(BG)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.spines["bottom"].set_color("#AAAAAA")
    ax.tick_params(axis="y", left=False, labelleft=False)
    ax.tick_params(axis="x", colors="#555555", labelsize=9)

    # --- distribution curve (height normalised to 1) ---
    y_pdf = norm.pdf(x, mu, sigma)
    y_pdf_norm = y_pdf / y_pdf.max()

    ax.fill_between(x, y_pdf_norm, alpha=0.18, color=fill_color)
    ax.plot(x, y_pdf_norm, color=fill_color, lw=2.2)

    # --- true μ₀(x) dashed vertical line ---
    ax.axvline(TRUE_MU, color=GOLD, lw=1.6, linestyle="--", zorder=3)

    # --- "True μ₀(x)" label BELOW the x-axis ---
    # transform=ax.get_xaxis_transform() → x in data coords, y in axes fraction
    # y = -0.12 puts it just below the x-axis tick labels
    ax.text(
        TRUE_MU, -0.12,
        r"True $\hat{\mu}_0(x)$",
        transform=ax.get_xaxis_transform(),
        ha="center", va="top",
        fontsize=9.5, color=GOLD, style="italic",
        zorder=4,
    )

    # --- panel title ---
    ax.set_title(title, fontsize=15, fontweight="bold",
                 color=title_color, pad=8, loc="center")

    # --- x-axis label ---
    ax.set_xlabel(
        r"Estimated baseline risk  $\hat{\mu}_0(x)$",
        fontsize=9.5, color="#444444", labelpad=18
    )

    ax.set_xlim(XLIM)
    ax.set_ylim(-0.04, YLIM_TOP)

    # --- info text box (upper-left), lowered to y=0.45 ---
    info_text = "\n".join(info_lines)
    ax.text(
        0.03, 0.45, info_text,
        transform=ax.transAxes,
        ha="left", va="top",
        fontsize=8.5, color="#333333",
        linespacing=1.55,
        bbox=dict(
            boxstyle="round,pad=0.35",
            facecolor="white", edgecolor=GOLD,
            alpha=0.82, linewidth=0.8
        ),
        zorder=5,
    )

    # --- sub-caption below the panel ---
    ax.text(
        0.5, -0.22, subtitle,
        transform=ax.transAxes,
        ha="center", va="top",
        fontsize=9, color="#555555", style="italic",
    )

    # --- bias arrow (proxy panel only) ---
    if show_bias_arrow and bias_from is not None and bias_to is not None:
        ax.annotate(
            "", xy=(bias_to, 0.55), xytext=(bias_from, 0.55),
            arrowprops=dict(
                arrowstyle="<->",
                color="#333333", lw=1.3,
            ),
        )
        ax.text(
            (bias_from + bias_to) / 2, 0.61, "bias",
            ha="center", va="bottom",
            fontsize=9, color="#333333",
        )

# ---------------------------------------------------------------------------
# Panel 1 – Proxy
# ---------------------------------------------------------------------------
draw_panel(
    axes[0],
    mu=proxy_mu, sigma=proxy_sigma,
    fill_color=PROXY_FILL,
    title="Proxy  (source sites)",
    title_color=BLUE,
    info_lines=[
        "Abundant data (nS large)",
        "Narrow distribution → low variance",
        "Centered away from target → biased",
    ],
    subtitle="nS large → low variance, biased",
    show_bias_arrow=True,
    bias_from=TRUE_MU,
    bias_to=proxy_mu,
)

# ---------------------------------------------------------------------------
# Panel 2 – Gold
# ---------------------------------------------------------------------------
draw_panel(
    axes[1],
    mu=gold_mu, sigma=gold_sigma,
    fill_color=GOLD_FILL,
    title="Gold  (target placebo)",
    title_color=GOLD,
    info_lines=[
        "Scarce data (nT small)",
        "Wide distribution → high variance",
        "Centered on truth → unbiased ✓",
    ],
    subtitle="nT small → high variance, unbiased ✓",
)

# ---------------------------------------------------------------------------
# Panel 3 – Anchored (proposed)
# ---------------------------------------------------------------------------
draw_panel(
    axes[2],
    mu=anchor_mu, sigma=anchor_sigma,
    fill_color=ANCHOR_FILL,
    title="Anchored  (proposed)",
    title_color=OLIVE,
    info_lines=[
        "Proxy corrected by gold anchor",
        "Narrow distribution → low variance",
        "Centered on truth → unbiased ✓",
    ],
    subtitle="Sparse correction: best of both ✓",
)

# ---------------------------------------------------------------------------
# Final layout and save
# ---------------------------------------------------------------------------
fig.subplots_adjust(
    left=0.03, right=0.97,
    top=0.82, bottom=0.22,
    wspace=0.30,
)

output_path = (
    "/Users/zilongwang/Sparse_TL_DR_ICHI2026/presentation/figures/"
    "proxy-gold-paradigm.png"
)

fig.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
print(f"Saved: {output_path}")

# Report pixel dimensions
from PIL import Image
img = Image.open(output_path)
print(f"Pixel dimensions: {img.size[0]} x {img.size[1]} px  (W x H)")
