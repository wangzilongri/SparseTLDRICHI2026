import fs from "node:fs/promises";
import path from "node:path";
import {
  createSlideContext,
  ensureArtifactToolWorkspace,
  importArtifactTool,
  padSlideNumber,
  saveBlobToFile,
} from "/Users/zilongwang/.codex/plugins/cache/openai-primary-runtime/presentations/26.521.10419/skills/presentations/scripts/artifact_tool_utils.mjs";

const workspace =
  "/Users/zilongwang/Transfer-Learning-for-Individual-Patient-Data-for-Clinical-Trials/outputs/manual-20260521-ichi-talk/presentations/ichi-2026-talk";
const starterPath = path.join(workspace, "template-starter.pptx");
const outputDir = path.join(workspace, "output");
const previewDir = path.join(workspace, "preview-appendix");
const finalPptx = path.join(outputDir, "appendix-lecture-bastani-tian-feng.pptx");

const MAROON = "#8A0020";
const GOLD = "#D5A834";
const BLUE = "#6F8EA4";
const GREEN = "#7B8F70";
const RED = "#B3414A";
const TEXT = "#2B2B2B";
const MUTED = "#65605C";
const SOFT = "#F7F5F2";
const LINE = "#DED8D1";

await ensureArtifactToolWorkspace(workspace);
const artifact = await importArtifactTool(workspace);
const { FileBlob, PresentationFile } = artifact;
const presentation = await PresentationFile.importPptx(await FileBlob.load(starterPath));
const ctx = createSlideContext(artifact, {
  slideSize: { width: 1280, height: 720 },
  workspaceDir: workspace,
  assetDir: path.join(workspace, "assets"),
  titleFont: "Aptos Display",
  bodyFont: "Aptos",
});

// Delete the 12 existing template slides (always delete index 0 since array shifts)
for (let i = 0; i < 12; i++) presentation.slides.getItem(0).delete();

// Add 17 blank slides
const S = [];
for (let i = 0; i < 17; i++) S.push(presentation.slides.add({}));

// ─── Helper functions ────────────────────────────────────────────────────────

// Title header for each slide (since blank slides have no placeholder shapes)
function H(slide, title, eyebrow = "") {
  ctx.addText(slide, {
    left: 72, top: 28, width: 1136, height: 78,
    text: title, fontSize: 30, color: MAROON, bold: true, typeface: "Aptos Display",
  });
  if (eyebrow) {
    ctx.addText(slide, {
      left: 72, top: 108, width: 800, height: 24,
      text: eyebrow, fontSize: 13, color: GOLD, bold: true,
    });
  }
  ctx.addShape(slide, {
    left: 72, top: 136, width: 1136, height: 2,
    fill: LINE, line: ctx.line("#00000000", 0),
  });
}

// Math/formula box (monospaced, blue border)
function mathBox(slide, x, y, w, h, label, formula) {
  ctx.addShape(slide, {
    left: x, top: y, width: w, height: h, geometry: "roundRect",
    fill: "#EEF2F7", line: ctx.line("#2C4770", 1.5),
  });
  if (label) {
    ctx.addText(slide, {
      left: x + 14, top: y + 8, width: w - 28, height: 20,
      text: label, fontSize: 11, color: "#2C4770", bold: true,
    });
  }
  ctx.addText(slide, {
    left: x + 14, top: y + (label ? 30 : 10), width: w - 28, height: h - (label ? 44 : 22),
    text: formula, fontSize: 13, color: TEXT, typeface: "Courier New",
  });
}

// Colored sidebar card
function sCard(slide, x, y, w, h, accent, title, body, titleSize = 16) {
  ctx.addShape(slide, {
    left: x, top: y, width: w, height: h, geometry: "roundRect",
    fill: "#FFFFFF", line: ctx.line(LINE, 1),
  });
  ctx.addShape(slide, {
    left: x, top: y, width: w, height: 5,
    fill: accent, line: ctx.line("#00000000", 0),
  });
  ctx.addText(slide, {
    left: x + 14, top: y + 14, width: w - 28, height: 26,
    text: title, fontSize: titleSize, color: TEXT, bold: true,
  });
  ctx.addText(slide, {
    left: x + 14, top: y + 46, width: w - 28, height: h - 62,
    text: body, fontSize: 13, color: MUTED, lineSpacing: 155,
  });
}

// Highlight box (bold insight box)
function insight(slide, x, y, w, h, text, color = GREEN) {
  ctx.addShape(slide, {
    left: x, top: y, width: w, height: h, geometry: "roundRect",
    fill: SOFT, line: ctx.line(color, 2),
  });
  ctx.addShape(slide, {
    left: x, top: y, width: 5, height: h,
    fill: color, line: ctx.line("#00000000", 0),
  });
  ctx.addText(slide, {
    left: x + 18, top: y + 10, width: w - 28, height: h - 20,
    text, fontSize: 15, color: TEXT, bold: false, lineSpacing: 160,
  });
}

// Step block for algorithms
function step(slide, x, y, w, h, num, title, body, color = BLUE) {
  ctx.addShape(slide, {
    left: x, top: y, width: w, height: h, geometry: "roundRect",
    fill: color + "22", line: ctx.line(color, 1.5),
  });
  ctx.addText(slide, {
    left: x + 12, top: y + 10, width: 36, height: 36,
    text: num, fontSize: 22, color: color, bold: true, align: "center",
  });
  ctx.addText(slide, {
    left: x + 54, top: y + 10, width: w - 66, height: 26,
    text: title, fontSize: 15, color: color, bold: true,
  });
  ctx.addText(slide, {
    left: x + 12, top: y + 44, width: w - 24, height: h - 56,
    text: body, fontSize: 12, color: TEXT, typeface: "Courier New", lineSpacing: 145,
  });
}

// ─── Slide 0 — Appendix divider ─────────────────────────────────────────────
{
  const slide = S[0];
  ctx.addShape(slide, {
    left: 0, top: 0, width: 1280, height: 720,
    fill: MAROON, line: ctx.line("#00000000", 0),
  });
  ctx.addText(slide, {
    left: 80, top: 240, width: 1120, height: 80,
    text: "Appendix: Method Foundations",
    fontSize: 44, color: "#FFFFFF", bold: true, align: "center", typeface: "Aptos Display",
  });
  ctx.addText(slide, {
    left: 80, top: 338, width: 1120, height: 36,
    text: "Bastani (2021) and Tian & Feng (2023) — sparse transfer learning theory",
    fontSize: 20, color: GOLD, bold: false, align: "center",
  });
  ctx.addText(slide, {
    left: 80, top: 390, width: 1120, height: 40,
    text: "These slides explain the sparse correction mechanism underlying our estimator pipeline.",
    fontSize: 15, color: "#FFFFFF", bold: false, align: "center",
  });
}

// ─── Slide 1 — Bastani (2021) overview ──────────────────────────────────────
{
  const slide = S[1];
  H(slide, "Bastani (2021): Predicting with Proxies", "BASTANI (2021) — Management Science 67(5), pp. 2964–2984");
  ctx.addText(slide, {
    left: 72, top: 152, width: 1136, height: 56,
    text: "A two-step LASSO estimator combining abundant proxy data with scarce gold labels. Achieves minimax rate scaling with bias sparsity s, not dimension d.",
    fontSize: 17, color: TEXT, bold: true,
  });
  sCard(slide, 72, 220, 338, 340, GOLD, "Proxy (source)",
    "Large n_proxy, small σ_proxy\nAbundant data → tight estimate\nBUT: centered at wrong β*_proxy\n\ny_proxy = xᵀ β*_proxy + ε");
  sCard(slide, 470, 220, 338, 340, GOLD, "Gold (target)",
    "Small n_gold, large σ_gold\nScarce data → wide uncertainty\nBUT: centered at truth β*_gold\n\ny_gold = xᵀ β*_gold + ε");
  sCard(slide, 868, 220, 338, 340, GREEN, "Key decomposition",
    "β*_gold = β*_proxy + δ*\n\n||δ*||_0 = s (sparse bias)\n\nOnly s of d features drive\nthe proxy-to-gold gap");
}

// ─── Slide 2 — Bastani formal model ─────────────────────────────────────────
{
  const slide = S[2];
  H(slide, "Formal model: shared features, sparse correction", "BASTANI (2021) — Model");
  mathBox(slide, 72, 155, 540, 110,
    "Data-generating processes",
    "y_gold  = xᵀ β*_gold  + ε_gold   (ε ~ σ_gold-subgaussian)\ny_proxy = xᵀ β*_proxy + ε_proxy  (ε ~ σ_proxy-subgaussian)\n\nSame features x ∈ R^d for both tasks");
  mathBox(slide, 72, 275, 540, 80,
    "Structural decomposition (key)",
    "β*_gold = β*_proxy + δ*\n||δ*||_0 = s  (only s coordinates differ)");
  insight(slide, 648, 155, 460, 90,
    "Proxy and gold tasks share the same feature space x ∈ R^d but have different regression coefficients",
    BLUE);
  insight(slide, 648, 255, 460, 90,
    "δ* is the sparse correction — only s of d features drive the gap between proxy and gold",
    GOLD);
  insight(slide, 648, 355, 460, 90,
    "Neither β*_gold nor β*_proxy needs to be sparse — only their DIFFERENCE δ* is assumed sparse",
    GREEN);
  sCard(slide, 72, 465, 1136, 150, MAROON, "What we need (3 assumptions)",
    "1. Sparse bias: ||δ*||_0 = s << d   2. Proxy invertibility: Σ_proxy ⪰ ψI (mild, n_proxy large)   3. Compatibility condition on gold design matrix restricted to supp(δ*) — weaker than requiring Σ_gold ⪱ 0",
    15);
}

// ─── Slide 3 — Two-step estimator ───────────────────────────────────────────
{
  const slide = S[3];
  H(slide, "The joint estimator: two-step LASSO", "BASTANI (2021) — Algorithm");
  ctx.addText(slide, {
    left: 72, top: 148, width: 1136, height: 34,
    text: "Two steps: estimate proxy with all proxy data, then debias using only gold data.",
    fontSize: 16, color: TEXT, bold: true,
  });
  step(slide, 72, 192, 530, 160, "1", "Proxy OLS (use all proxy data)",
    "β̂_proxy = argmin_β { (1/n_proxy) ||Y_proxy - X_proxy β||^2 }\n\nConverges to β*_proxy with rate O_p(d·σ_proxy / √n_proxy)\nRequires only n_proxy >> d",
    BLUE);
  step(slide, 72, 364, 530, 200, "2", "Debiasing LASSO (gold data only)",
    "δ̂ = argmin_δ { (1/n_gold) ||Y_gold - X_gold(δ + β̂_proxy)||^2 + λ||δ||_1 }\n\nβ̂_joint = δ̂ + β̂_proxy\n\nλ chosen by cross-validation on gold data\nRequires only n_gold >> s^2 (not d^2)",
    GOLD);
  insight(slide, 640, 192, 568, 130,
    "Reparameterization insight:\nStep 2 is LASSO on the residual\n(Y_gold - X_gold·β̂_proxy), recovering\nthe sparse correction δ*. Gold data\nis used only to identify which s\nfeatures need adjustment.",
    GREEN);
  insight(slide, 640, 334, 568, 130,
    "Only β̂_proxy (a d-dimensional\nvector) needs to be shared from\nStep 1 to Step 2. Raw proxy data\nneed not be shared — important\nfor privacy in federated clinical\ntrial settings.",
    BLUE);
  mathBox(slide, 640, 476, 568, 100,
    "First-stage noise flows through",
    "ν = β̂_proxy - β*_proxy  (small when n_proxy large)\nδ̄ = δ* - ν = β*_gold - β̂_proxy  (approx. sparse)\nLasso tail bounds hold for approx. sparse targets");
}

// ─── Slide 4 — Main theorem / rate comparison ────────────────────────────────
{
  const slide = S[4];
  H(slide, "Main result: bias sparsity s replaces dimension d", "BASTANI (2021) — Theorem (Corollary 1)");
  ctx.addText(slide, {
    left: 72, top: 148, width: 1136, height: 24,
    text: "Expected ℓ₁ estimation error, sup over problem parameters:",
    fontSize: 16, color: TEXT, bold: true,
  });
  mathBox(slide, 72, 178, 1136, 80,
    "Corollary 1 — Joint estimator rate",
    "R(β̂_joint, β*_gold) = O( max{ s·σ_gold·log(d·n_gold)/√n_gold,   s·d·σ_proxy·log(d·n_proxy)/√n_proxy } )");

  // Table headers
  ctx.addShape(slide, { left: 72, top: 272, width: 1136, height: 44, fill: MAROON + "22", line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: 80, top: 282, width: 420, height: 24, text: "Estimator", fontSize: 14, color: MAROON, bold: true });
  ctx.addText(slide, { left: 520, top: 282, width: 400, height: 24, text: "ℓ₁ Error Rate", fontSize: 14, color: MAROON, bold: true });
  ctx.addText(slide, { left: 960, top: 282, width: 240, height: 24, text: "Uses sparsity?", fontSize: 14, color: MAROON, bold: true });

  // Row 1: Gold OLS
  ctx.addShape(slide, { left: 72, top: 316, width: 1136, height: 44, fill: "#FFFFFF", line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: 80, top: 326, width: 420, height: 24, text: "Gold OLS (n_gold only)", fontSize: 13, color: TEXT });
  ctx.addText(slide, { left: 520, top: 326, width: 400, height: 24, text: "d·σ_gold / √n_gold", fontSize: 13, color: TEXT, typeface: "Courier New" });
  ctx.addText(slide, { left: 960, top: 326, width: 240, height: 24, text: "No", fontSize: 13, color: MUTED });

  // Row 2: Model averaging
  ctx.addShape(slide, { left: 72, top: 360, width: 1136, height: 44, fill: SOFT, line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: 80, top: 370, width: 420, height: 24, text: "Model averaging / weighted loss", fontSize: 13, color: TEXT });
  ctx.addText(slide, { left: 520, top: 370, width: 400, height: 24, text: "min(d·σ/√n_gold, ||δ*||_1 + d·σ/√n_proxy)", fontSize: 13, color: TEXT, typeface: "Courier New" });
  ctx.addText(slide, { left: 960, top: 370, width: 240, height: 24, text: "No", fontSize: 13, color: MUTED });

  // Row 3: Joint estimator
  ctx.addShape(slide, { left: 72, top: 404, width: 1136, height: 44, fill: GREEN + "22", line: ctx.line(GREEN, 1.5) });
  ctx.addText(slide, { left: 80, top: 414, width: 420, height: 24, text: "Joint estimator (Bastani)", fontSize: 13, color: TEXT, bold: true });
  ctx.addText(slide, { left: 520, top: 414, width: 400, height: 24, text: "s·σ·log(d) / √n_gold  [s << d]", fontSize: 13, color: GREEN, bold: true, typeface: "Courier New" });
  ctx.addText(slide, { left: 960, top: 414, width: 240, height: 24, text: "YES ✓", fontSize: 13, color: GREEN, bold: true });

  insight(slide, 72, 456, 1136, 100,
    "Interpretation: model averaging and weighted loss cannot exploit the sparse structure in δ* — they interpolate on the full d-dimensional parameter space and are provably stuck at the d/√n rate. The joint estimator targets δ* directly, needing gold data only for s dimensions.",
    GREEN);
}

// ─── Slide 5 — When transfer helps / conditions ──────────────────────────────
{
  const slide = S[5];
  H(slide, "When the proxy-gold correction works", "BASTANI (2021) — Conditions and failure modes");
  sCard(slide, 72, 152, 540, 250, GREEN, "✓ Transfer helps when",
    "1. Sparse bias: s << d\n   Few features drive the proxy-gold gap\n\n2. Abundant proxy: n_proxy >> s²d² σ²_proxy\n   Step 1 accurately estimates β*_proxy\n\n3. Compatibility on gold design:\n   Σ_gold satisfies compatibility on supp(δ*)\n   [weaker than requiring Σ_gold ⪱ 0]");
  sCard(slide, 72, 414, 540, 210, RED, "✗ Transfer does not help when",
    "1. Dense bias (s ~ d):\n   Joint estimator ≈ gold-only OLS; no gain\n\n2. Proxy too noisy (σ_proxy large, n_proxy small):\n   First-stage error ν dominates; δ̄ not sparse\n\n3. Gold design degenerate on supp(δ*):\n   Compatibility fails; δ* not identifiable");
  insight(slide, 650, 152, 458, 120,
    "Sample complexity gap:\n\nGold-only methods: n_gold = O(d² σ²/ξ²)\nJoint estimator: n_gold = O(s² σ² log²(d)/ξ²)\n\nExponentially smaller in d when s << d",
    BLUE);
  mathBox(slide, 650, 284, 458, 90,
    "Optimal lambda (Corollary 1)",
    "λ* = Õ(σ_gold/√n_gold + d·σ_proxy/√n_proxy)\n\nIn practice: cross-validate on gold data");
  insight(slide, 650, 386, 458, 120,
    "Privacy-friendly:\nOnly β̂_proxy (Step 1 output) is shared\nbetween sites. Raw proxy data stays\nlocal. Works in federated healthcare\nsettings with data-sharing restrictions.",
    GOLD);
  insight(slide, 650, 518, 458, 100,
    "Extensions (§4.5):\nGeneralizes to any M-estimator with\nconvex loss (logistic, Poisson, etc.) with\nidentical rate using strong convexity of A",
    MUTED);
}

// ─── Slide 6 — Bastani ↔ clinical trial mapping ──────────────────────────────
{
  const slide = S[6];
  H(slide, "How Bastani maps to our estimator", "BASTANI (2021) — Connection to our paper");
  ctx.addText(slide, {
    left: 72, top: 148, width: 1136, height: 40,
    text: "Our sparse correction step IS Bastani's Eq. (2): debiasing LASSO on target placebo residuals, centered at the source-site proxy estimate.",
    fontSize: 16, color: TEXT, bold: true,
  });

  // Column headers
  ctx.addText(slide, { left: 80, top: 200, width: 620, height: 28, text: "Bastani (2021) formulation", fontSize: 16, color: BLUE, bold: true });
  ctx.addText(slide, { left: 760, top: 200, width: 448, height: 28, text: "Our paper", fontSize: 16, color: MAROON, bold: true });
  // Divider
  ctx.addShape(slide, { left: 740, top: 196, width: 2, height: 320, fill: LINE, line: ctx.line("#00000000", 0) });

  const rows = [
    ["Proxy: β*_proxy (source regression coeff.)", "μ̂₀^proxy(x)  — source-trial outcome model"],
    ["Gold: β*_gold (target regression coeff.)", "μ₀(x) — true target baseline risk"],
    ["Sparse correction: δ* = β*_gold − β*_proxy", "Sparse covariate-shift correction under A5"],
    ["Compatibility condition (gold design)", "Assumption A5: sparse local shift identifiable"],
    ["δ̂ = argmin ||Y_gold − X_gold(δ + β̂_proxy)||^2 + λ||δ||_1", "Our Eq. (4): sparse correction of baseline risk"],
    ["β̂_joint = δ̂ + β̂_proxy", "μ̂₀^anchor(x) = δ̂ + μ̂₀^proxy(x)"],
  ];
  rows.forEach(([left, right], idx) => {
    const y = 236 + idx * 46;
    const bg = idx % 2 === 0 ? "#FFFFFF" : SOFT;
    ctx.addShape(slide, { left: 72, top: y, width: 660, height: 44, fill: bg, line: ctx.line(LINE, 0.5) });
    ctx.addShape(slide, { left: 742, top: y, width: 466, height: 44, fill: bg, line: ctx.line(LINE, 0.5) });
    ctx.addText(slide, { left: 80, top: y + 8, width: 648, height: 28, text: left, fontSize: 12, color: TEXT, typeface: "Courier New" });
    ctx.addText(slide, { left: 750, top: y + 8, width: 450, height: 28, text: right, fontSize: 12, color: TEXT });
  });

  insight(slide, 72, 540, 1136, 110,
    "Key difference: our setting adds a DR learner on top of the corrected baseline risk estimate. Bastani's β̂_joint gives μ̂₀^anchor(x). We then form pseudo-outcomes ψ_i = μ̂₁(x_i) − μ̂₀^anchor(x_i) + IPW residual and fit CATE τ̂(x) = E[ψ|x]. Bastani provides the first-stage foundation.",
    MAROON);
}

// ─── Slide 7 — Bridge to Tian & Feng ────────────────────────────────────────
{
  const slide = S[7];
  H(slide, "Beyond one proxy: K sources with unknown similarity", "BASTANI (2021) → TIAN & FENG (2023)");
  sCard(slide, 72, 152, 540, 160, BLUE, "What Bastani covers",
    "• One proxy source dataset\n• Linear model (extended to GLMs in §4.5)\n• Oracle knowledge of which source to use\n• Sparse bias in ℓ₀ sense: ||δ*||_0 = s");
  sCard(slide, 72, 324, 540, 240, RED, "What Bastani does NOT cover",
    "• Multiple source datasets (K > 1)\n• Which sources are informative when h varies\n• Negative transfer when bad sources are pooled\n• Minimax lower bounds (optimality certificate)\n• Valid confidence intervals for inference\n• ℓ₁-sparse contrast (more general than ℓ₀)");
  insight(slide, 650, 152, 460, 410,
    "Clinical trials have K source studies, each with possibly different patient populations. Some sources are close to the target (small h = ||β_target − w^(k)||_1), others are far (negative transfer). We need:\n\n1. A method that pools ONLY informative sources\n2. Data-driven selection of which k ∈ A_h\n3. Minimax optimality over the class\n\n→ Tian & Feng (2023) addresses all three.",
    BLUE);
  ctx.addText(slide, {
    left: 340, top: 610, width: 600, height: 60,
    text: "→ See next section: Tian & Feng (2023)",
    fontSize: 20, color: GOLD, bold: true, align: "center",
  });
}

// ─── Slide 8 — Tian & Feng section intro ────────────────────────────────────
{
  const slide = S[8];
  H(slide, "Tian & Feng (2023): Transfer Learning under High-dimensional GLMs", "TIAN & FENG (2023) — JASA 118(544), pp. 2684–2697");
  ctx.addText(slide, {
    left: 72, top: 152, width: 1136, height: 48,
    text: "Extends Bastani to K source datasets, any GLM, with data-driven source selection and minimax-optimal rates.",
    fontSize: 17, color: TEXT, bold: true,
  });
  sCard(slide, 72, 220, 252, 320, BLUE, "K sources",
    "Any number of source datasets {(X^(k),y^(k))}^K_{k=1}\nEach with possibly different w^(k)");
  sCard(slide, 354, 220, 252, 320, GOLD, "Any GLM",
    "Linear, logistic, Poisson\ny^(k)|x ~ exp{y·xᵀw^(k) − ψ(xᵀw^(k))}");
  sCard(slide, 636, 220, 252, 320, GREEN, "Auto-selection",
    "Cross-validation detects A_h\n(informative sources)\nNo oracle knowledge required");
  sCard(slide, 918, 220, 252, 320, MAROON, "Minimax optimal",
    "Rate is tight: lower bound\nmatches upper bound\n+ confidence intervals");
}

// ─── Slide 9 — Setup and similarity ─────────────────────────────────────────
{
  const slide = S[9];
  H(slide, "Setup: K source GLMs + 1 target in high dimension", "TIAN & FENG (2023) — Model");
  mathBox(slide, 72, 152, 580, 120,
    "GLM model (k = 0, 1, ..., K)",
    "y^(k)|x ~ ρ(y) exp{ y·xᵀ w^(k) − ψ(xᵀ w^(k)) }\n\nTarget: β = w^(0) ∈ R^p,  ||β||_0 = s\nHigh-dimensional: n_0 << p,  n_k << p");
  mathBox(slide, 72, 284, 580, 100,
    "Contrast and transferring level",
    "δ^(k) = β − w^(k)     (contrast of source k from target)\n||δ^(k)||_1 = h_k      (transferring level of source k)\nA_h = { k : ||δ^(k)||_1 ≤ h }   (informative set)");
  mathBox(slide, 72, 396, 580, 100,
    "Effective sample size",
    "n_{A_h} = Σ_{k ∈ A_h} n_k     (total informative samples)\nK_{A_h} = |A_h|               (number of informative sources)");
  insight(slide, 688, 152, 520, 90,
    "High-dimensional regime:\nn_0 << p — classical MLE fails.\nBaseline is Lasso with rate O(s√(log p/n_0)).\nTransfer replaces n_0 by n_{A_h} + n_0.",
    BLUE);
  insight(slide, 688, 254, 520, 100,
    "ℓ₁ vs ℓ₀ contrast sparsity:\nTian & Feng use ||δ^(k)||_1 ≤ h (ℓ₁).\nBastani uses ||δ*||_0 = s (ℓ₀).\nℓ₁ allows the contrast to be diffusely small\nacross many coords, not exactly zero on s.",
    GOLD);
  insight(slide, 688, 366, 520, 130,
    "Two sparsity conditions:\n1. Target sparsity: ||β||_0 = s (needed to identify β with Lasso)\n2. Contrast sparsity: ||δ^(k)||_1 ≤ h (needed for debiasing step to work)\n\nThese are independent: β can have sparse support while δ^(k) is diffusely small.",
    GREEN);
}

// ─── Slide 10 — Algorithm: A-Trans-GLM ──────────────────────────────────────
{
  const slide = S[10];
  H(slide, "A-Trans-GLM: two-step algorithm with known A_h", "TIAN & FENG (2023) — Algorithm 1");
  step(slide, 72, 152, 580, 180, "1", "Pooled Lasso (Step 1 — use all informative data)",
    "ŵ^A = argmin_w { (1/(n_A+n_0)) Σ_{k ∈ {0}∪A} L_k(w) + λ_w||w||_1 }\n\nL_k(w) = -(y^(k))ᵀ X^(k)w + Σ_i ψ(wᵀ x_i^(k))\n\nλ_w = C_w √(log p / (n_{A_h} + n_0))",
    BLUE);
  step(slide, 72, 344, 580, 180, "2", "Debiasing Lasso (Step 2 — target data only)",
    "δ̂^A = argmin_δ { -(1/n_0)(y^(0))ᵀ X^(0)(ŵ^A + δ) + (1/n_0) Σ_i ψ((ŵ^A+δ)ᵀ x_i^(0)) + λ_δ||δ||_1 }\n\nλ_δ = C_δ √(log p / n_0)",
    GOLD);
  mathBox(slide, 72, 536, 580, 68, "Output", "β̂ = ŵ^A + δ̂^A");
  insight(slide, 688, 152, 520, 120,
    "Step 1 intuition:\nPool all n_{A_h} + n_0 observations.\nThis gives a biased but low-variance estimate\nŵ^A ≈ weighted mixture of {w^(k)}_{k∈A}.\nThe larger n_{A_h}, the lower the variance.",
    BLUE);
  insight(slide, 688, 284, 520, 120,
    "Step 2 intuition:\nCorrect the bias introduced by pooling.\nTarget data alone estimates δ = β − ŵ^A.\nSince ||δ||_1 ≤ h (small), this needs only\nn_0 observations. Requires h << √(log p/n_0).",
    GOLD);
  insight(slide, 688, 416, 520, 110,
    "Same structure as Bastani:\nStep 1 = proxy estimation\nStep 2 = debiasing LASSO on target\n\nDifference: Step 1 pools K sources\ninstead of 1, and uses GLM loss.",
    GREEN);
  insight(slide, 688, 538, 520, 66,
    "Penalty scales: λ_w uses combined n_{A_h}+n_0 (more data → smaller regularization). λ_δ uses only n_0 (target-only estimation of contrast).",
    MUTED);
}

// ─── Slide 11 — Trans-GLM: auto source detection ─────────────────────────────
{
  const slide = S[11];
  H(slide, "Trans-GLM: data-driven detection of informative sources", "TIAN & FENG (2023) — Algorithm 2");
  insight(slide, 72, 152, 1136, 56,
    "Problem: A_h is unknown in practice. We cannot observe ||β − w^(k)||_1 without knowing β. Algorithm 2 detects informative sources using cross-validation on the TARGET data only.",
    MAROON);
  step(slide, 72, 220, 340, 200, "1", "CV for each source",
    "For each source k and fold r:\n• Fit pooled model using\n  {source k} + {2 target folds}\n• Evaluate CV loss on\n  held-out target fold\n• Compute mean CV loss L̂₀^(k)",
    BLUE);
  step(slide, 444, 220, 340, 200, "2", "Compare to target-only",
    "Fit target-only Lasso: L̂₀^(0)\nEstimate noise σ̂ from\ncross-validated residuals\n\nInclude source k if:\nL̂₀^(k) − L̂₀^(0) ≤ C₀·σ̂\n(CV loss not worse than target)",
    GOLD);
  step(slide, 816, 220, 392, 200, "3", "Run A-Trans-GLM",
    "Â = { k : L̂₀^(k) − L̂₀^(0) ≤ threshold }\n\nRun Algorithm 1 with Â\ninstead of oracle A_h\n\nTheorem 4: Â = A_h\nwith high probability",
    GREEN);
  sCard(slide, 72, 436, 540, 210, GREEN, "Theorem 4 — Detection consistency",
    "Under identifiability (Assumption 5) and sufficient sample sizes:\n\nP(Â = A_h) ≥ 1 − δ\n\nAuto-detection is asymptotically exact.");
  sCard(slide, 650, 436, 558, 210, GOLD, "R package: glmtrans (CRAN)",
    "Implements all three algorithms:\n• A-Trans-GLM (oracle, known A_h)\n• Trans-GLM (auto-detection via CV)\n• Confidence intervals (Theorem 5)\n\nInstall: install.packages('glmtrans')");
}

// ─── Slide 12 — Main theorem ─────────────────────────────────────────────────
{
  const slide = S[12];
  H(slide, "Main theorem: transfer replaces n₀ by n_{A_h} + n₀", "TIAN & FENG (2023) — Theorem 1 + 2");
  mathBox(slide, 72, 152, 1136, 100,
    "Theorem 1 (upper bound) — ℓ₁ estimation error",
    "||β̂ − β||_1 ≲ s · √(log p / (n_{A_h} + n_0)) + h        [with prob. ≥ 1 − n_0^{-1}]\n\nTwo terms: (1) variance term — improves with more data; (2) bias term h — controlled when h << √(log p / n_0)");
  mathBox(slide, 72, 264, 1136, 60,
    "Naive Lasso baseline (no transfer)",
    "||β̂_Lasso − β||_1 = O_p( s · √(log p / n_0) )    [slower — only n_0 in denominator]");
  mathBox(slide, 72, 336, 1136, 60,
    "Theorem 2 (lower bound — minimax optimal)",
    "inf_{β̂} sup P(||β̂−β||_1 ≥ c·s·√(log p/(n_{A_h}+n_0))) ≥ 1/2  →  A-Trans-GLM is rate-optimal");
  insight(slide, 72, 410, 1136, 80,
    "Transfer benefit condition: h << √(log p / n_0)  AND  n_{A_h} >> n_0\nWhen both hold: denominator (n_{A_h} + n_0) >> n_0 → first term shrinks → huge improvement over Lasso.\nThe bias term h vanishes when sources are very close to target.",
    GREEN);
  sCard(slide, 72, 502, 540, 118, BLUE, "Rate comparison",
    "h → 0, n_{A_h} → ∞:\nTian & Feng: O(s√(log p / n_{A_h}))\nNaive Lasso:  O(s√(log p / n_0))\nRatio improvement: √(n_{A_h}/n_0)");
  sCard(slide, 650, 502, 558, 118, GOLD, "Confidence intervals (Theorem 5)",
    "Desparsified estimator b:\n√n_0 (b_j − β_j)/σ̂_j → N(0,1)\n\nValid CIs even in high dimension.\nImplemented in glmtrans.");
}

// ─── Slide 13 — Negative transfer ───────────────────────────────────────────
{
  const slide = S[13];
  H(slide, "Negative transfer: uninformative sources hurt", "TIAN & FENG (2023) — Cautionary analysis");
  insight(slide, 72, 152, 1136, 60,
    "Naively pooling ALL K sources (including those with large ||δ^(k)||_1 >> h) WORSENS estimation — 'negative transfer'. Use Trans-GLM (Algorithm 2) to avoid this.",
    RED);
  sCard(slide, 72, 224, 540, 260, RED, "What goes wrong with naive pooling",
    "If source k has ||δ^(k)||_1 = h_large >> h:\n• Step 1 pooling bias is O(h_large)\n• Step 2 debiasing cannot correct large h\n  (requires n_0 >> h²/log p, which fails)\n• Net: bias term dominates → worse than Lasso\n\nPooled-Trans-GLM (all K sources) can be\nMUCH worse than naive Lasso when most\nsources are far from the target.");
  sCard(slide, 650, 224, 558, 260, GREEN, "Trans-GLM solves this",
    "Algorithm 2 detects and excludes\nuninformative sources before pooling.\n\nKey guarantee (Theorem 4):\nP(Â = A_h) → 1 as n_0 → ∞\n\nResult: Trans-GLM is NEVER worse than\ntarget-only Lasso in the limit (safe transfer).\n\nSafe to deploy without knowing h in advance.");
  mathBox(slide, 72, 498, 1136, 100,
    "Formal negative transfer condition",
    "If k ∉ A_h (i.e., ||δ^(k)||_1 > h) is included in pooling:\n  ||β̂ − β||_1 ≥ c · h_large  (bias-dominated)\n  This is O(h_large) >> O(s·√(log p/n_0)) for large h_large\n  → Naive pooling can be arbitrarily bad; source selection is mandatory");
}

// ─── Slide 14 — Comparison Bastani vs Tian & Feng ───────────────────────────
{
  const slide = S[14];
  H(slide, "Bastani (2021) vs Tian & Feng (2023): key differences", "COMPARISON");

  // Table header
  ctx.addShape(slide, { left: 72, top: 152, width: 1136, height: 44, fill: MAROON + "22", line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: 80, top: 162, width: 300, height: 24, text: "Aspect", fontSize: 14, color: MAROON, bold: true });
  ctx.addText(slide, { left: 400, top: 162, width: 380, height: 24, text: "Bastani (2021)", fontSize: 14, color: MAROON, bold: true });
  ctx.addText(slide, { left: 800, top: 162, width: 390, height: 24, text: "Tian & Feng (2023)", fontSize: 14, color: MAROON, bold: true });

  const tableRows = [
    ["Model", "Linear (+ GLM extension §4.5)", "Any GLM as primary focus"],
    ["Sources", "1 proxy dataset", "K source datasets"],
    ["Sparsity of contrast", "ℓ₀: ||δ*||_0 = s", "ℓ₁: ||δ^(k)||_1 ≤ h"],
    ["Source selection", "Oracle (proxy known)", "Data-driven via CV (Alg. 2)"],
    ["Optimality", "Rate result (Corollary 1)", "Minimax lower bound (Theorem 2)"],
    ["Inference", "Point estimation only", "+ Confidence intervals (Theorem 5)"],
  ];
  tableRows.forEach(([aspect, bastani, tian], idx) => {
    const y = 196 + idx * 52;
    const bg = idx % 2 === 0 ? "#FFFFFF" : SOFT;
    ctx.addShape(slide, { left: 72, top: y, width: 1136, height: 52, fill: bg, line: ctx.line(LINE, 0.5) });
    ctx.addText(slide, { left: 80, top: y + 10, width: 300, height: 32, text: aspect, fontSize: 13, color: TEXT, bold: true });
    ctx.addText(slide, { left: 400, top: y + 10, width: 380, height: 32, text: bastani, fontSize: 13, color: TEXT });
    ctx.addText(slide, { left: 800, top: y + 10, width: 390, height: 32, text: tian, fontSize: 13, color: TEXT });
  });

  insight(slide, 72, 510, 1136, 90,
    "Both papers use the same two-step structure: (1) estimate with proxy/source data, (2) debias on target. Tian & Feng extends the scope from 1 source to K, provides minimax optimality, and handles unknown source quality.",
    GREEN);
}

// ─── Slide 15 — Clinical trial mapping for Tian & Feng ───────────────────────
{
  const slide = S[15];
  H(slide, "How Tian & Feng maps to our multi-source clinical trial setting", "TIAN & FENG (2023) — Connection to our paper");
  ctx.addText(slide, {
    left: 72, top: 148, width: 1136, height: 30,
    text: "In our paper: K source RCTs, target has placebo only, some sources are close (small h), others far (large h). Tian & Feng provides the foundation for multi-source pooling.",
    fontSize: 16, color: TEXT, bold: true,
  });

  // Table header
  ctx.addShape(slide, { left: 72, top: 185, width: 1136, height: 40, fill: MAROON + "22", line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: 80, top: 195, width: 560, height: 24, text: "Tian & Feng (2023)", fontSize: 14, color: MAROON, bold: true });
  ctx.addText(slide, { left: 660, top: 195, width: 540, height: 24, text: "Our paper (this work)", fontSize: 14, color: MAROON, bold: true });

  const mapRows = [
    ["K source GLMs {(X^(k), y^(k))}_{k=1}^K", "K source trial IPDs"],
    ["Source coefficient w^(k) ∈ R^p", "Source-site outcome model μ̂₀^(k)(x)"],
    ["Target coefficient β = w^(0)", "Target baseline risk μ₀(x)"],
    ["Contrast δ^(k) = β − w^(k)", "Covariate shift under A5: sparse local shift"],
    ["Transferring set A_h (informative sources)", "Compatible sources satisfying Assumption A6"],
    ["Trans-GLM Step 1: pooled Lasso", "Source pooling with anchor (sparse correction)"],
    ["Trans-GLM Step 2: debiasing on target", "δ̂ correction: argmin with λ||δ||_1"],
  ];
  mapRows.forEach(([left, right], idx) => {
    const y = 225 + idx * 48;
    const bg = idx % 2 === 0 ? "#FFFFFF" : SOFT;
    ctx.addShape(slide, { left: 72, top: y, width: 1136, height: 48, fill: bg, line: ctx.line(LINE, 0.5) });
    ctx.addText(slide, { left: 80, top: y + 8, width: 560, height: 32, text: left, fontSize: 12, color: TEXT, typeface: "Courier New" });
    ctx.addText(slide, { left: 660, top: y + 8, width: 540, height: 32, text: right, fontSize: 12, color: TEXT });
  });

  insight(slide, 72, 566, 1136, 110,
    "Key difference from Tian & Feng: we target individual CATE τ(x) = E[Y(1)−Y(0)|x], not the baseline risk coefficient β. Our DR learner layer (pseudo-outcomes ψ_i = μ̂₁(x_i)−μ̂₀^anchor(x_i)+IPW residual) sits on top of the Tian & Feng foundation. GLM family = logistic regression for binary endpoints, linear regression for continuous.",
    MAROON);
}

// ─── Slide 16 — Summary ──────────────────────────────────────────────────────
{
  const slide = S[16];
  H(slide, "Summary: two papers, one estimator pipeline", "SUMMARY");
  sCard(slide, 72, 160, 338, 440, BLUE, "Bastani (2021)",
    "• Single proxy-gold setup\n• β*_gold = β*_proxy + δ*, ||δ*||_0 = s\n• Two-step Lasso: proxy OLS → debiasing\n• Rate: s·σ/√n_gold (s replaces d)\n• Powers our sparse correction step\n• Privacy: share only β̂_proxy");
  sCard(slide, 470, 160, 338, 440, GOLD, "Tian & Feng (2023)",
    "• K sources, GLMs, unknown quality\n• Contrast: ||δ^(k)||_1 ≤ h\n• Auto-detects A_h via cross-validation\n• Minimax optimal rates (Theorem 2)\n• Confidence intervals (Theorem 5)\n• R: glmtrans on CRAN");
  sCard(slide, 868, 160, 338, 440, GREEN, "Our estimator",
    "• Bastani's correction: μ̂₀^proxy → μ̂₀^anchor\n• Tian & Feng: K-source GLM extension\n• DR learner: pseudo-outcomes ψ_i\n• CATE: τ̂(x) = E[ψ|x]\n• Connected: Theorem 1 (identified)\n• Disconnected: Theorem 2 (working model)");
  insight(slide, 72, 618, 1136, 74,
    "The full estimator = Tian & Feng baseline risk correction (multi-source GLM pooling with debiasing) + Kennedy (2023) doubly robust CATE learner with cross-fitting. Each layer has its own theoretical guarantee; our paper proves the joint guarantee under Assumptions A1–A6.",
    GREEN);
}

// ─── Export ──────────────────────────────────────────────────────────────────
await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

for (let i = 0; i < S.length; i++) {
  const padded = padSlideNumber(i + 1);
  const preview = await presentation.export({ slide: S[i], format: "png", scale: 1 });
  await saveBlobToFile(preview, path.join(previewDir, `slide-${padded}.png`));
}

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(finalPptx);
const stat = await fs.stat(finalPptx);
console.log(JSON.stringify({ finalPptx, bytes: stat.size, slideCount: S.length, previewDir }));
