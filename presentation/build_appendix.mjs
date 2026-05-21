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
const finalPptx = path.join(outputDir, "appendix-lecture-method-foundations.pptx");

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
for (let i = 0; i < 30; i++) S.push(presentation.slides.add({}));

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
    text: "Bastani (2021)  ·  Tian & Feng (2023)  ·  Kennedy (2023)",
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

// ─── Slide 17 — Kennedy section divider ─────────────────────────────────────
{
  const slide = S[17];
  ctx.addShape(slide, {
    left: 0, top: 0, width: 1280, height: 720,
    fill: MAROON, line: ctx.line("#00000000", 0),
  });
  ctx.addText(slide, {
    left: 80, top: 220, width: 1120, height: 80,
    text: "Kennedy (2023): Doubly Robust CATE Estimation",
    fontSize: 40, color: "#FFFFFF", bold: true, align: "center", typeface: "Aptos Display",
  });
  ctx.addText(slide, {
    left: 80, top: 316, width: 1120, height: 36,
    text: "The final layer: from corrected baseline risk to heterogeneous treatment effects",
    fontSize: 20, color: GOLD, bold: false, align: "center",
  });
  ctx.addText(slide, {
    left: 80, top: 368, width: 1120, height: 40,
    text: "Kennedy (2023), Electronic Journal of Statistics 17(2): 3008–3049  ·  DOI: 10.1214/23-EJS2157",
    fontSize: 15, color: "#FFFFFF", bold: false, align: "center",
  });
}

// ─── Slide 18 — Setup: CATE and causal assumptions ───────────────────────────
{
  const slide = S[18];
  H(slide, "Setup: estimating heterogeneous treatment effects", "KENNEDY (2023) — Setup");
  ctx.addText(slide, {
    left: 72, top: 152, width: 1136, height: 36,
    text: "Goal: estimate CATE τ(x) = E[Y(1)−Y(0)|X=x] from experimental data using flexible ML for nuisance functions.",
    fontSize: 16, color: TEXT, bold: true,
  });
  mathBox(slide, 72, 196, 556, 90, "Observed data",
    "Z_i = (Y_i, A_i, X_i)  i.i.d.  i = 1,...,n\nY_i = outcome,  A_i ∈ {0,1} = treatment assigned\nX_i ∈ R^d = pre-treatment covariates");
  mathBox(slide, 72, 298, 556, 70, "Target estimand",
    "τ(x) = E[Y(1) − Y(0) | X = x]     (CATE)\nATE = E[τ(X)],    GATE = E[τ(X) | X ∈ G]");
  insight(slide, 648, 196, 560, 172,
    "In our clinical trial setting:\n• A_i = treatment indicator (active vs. placebo)\n• e(x) = P(treated|x) is KNOWN by randomization\n• Overlap guaranteed by design\n• Unconfoundedness holds by construction\n\nKnown propensity removes one estimation step — a structural advantage Kennedy's framework exploits via exact IPW weighting.",
    MAROON);
  sCard(slide, 72, 380, 340, 210, BLUE, "A1: Unconfoundedness",
    "Y(0), Y(1) ⊥ A | X\n\nNo unmeasured confounders.\nConditioning on X removes\nall treatment assignment bias.\nAutomatic in RCTs.");
  sCard(slide, 432, 380, 340, 210, GOLD, "A2: Overlap",
    "0 < e(x) < 1  ∀x\ne(x) = P(A=1|X=x)\n\nBoth arms observed at\nevery covariate value.\nCritical for IPW weighting.");
  sCard(slide, 792, 380, 416, 210, GREEN, "A3: SUTVA",
    "Y_i(a) = Y_i  when A_i = a\n\nNo interference between\nunits. Single version of\ntreatment. Standard in\nindividual-level trials.");
}

// ─── Slide 19 — The DR pseudo-outcome ────────────────────────────────────────
{
  const slide = S[19];
  H(slide, "The DR pseudo-outcome: efficient influence function for CATE", "KENNEDY (2023) — Eq. (2.3)");
  mathBox(slide, 72, 152, 1136, 104, "DR pseudo-outcome (Kennedy 2023, Eq. 2.3)",
    "φ̂(Z_i) =  (μ̂₁(X_i) − μ̂₀(X_i))   +   A_i(Y_i − μ̂₁(X_i)) / ê(X_i)   −   (1−A_i)(Y_i − μ̂₀(X_i)) / (1−ê(X_i))\n           [direct plug-in term]             [treated residual / propensity]         [control residual / (1−propensity)]");
  sCard(slide, 72, 268, 340, 180, GREEN, "Direct term",
    "μ̂₁(x) − μ̂₀(x)\n\nPlug-in outcome model\ndifference. Fast when μ̂\nis close to μ. Biased when\nML models overfit training data.");
  sCard(slide, 432, 268, 340, 180, BLUE, "Treated IPW residual",
    "A_i(Y_i − μ̂₁(X_i)) / ê(X_i)\n\nResidual of treated\nobservations re-weighted\nby propensity.\nCorrects bias in direct term.");
  sCard(slide, 792, 268, 416, 180, GOLD, "Control IPW residual",
    "−(1−A_i)(Y_i − μ̂₀(X_i)) / (1−ê(X_i))\n\nResidual of control obs.\nweighted by 1−propensity.\nCompletes double correction.");
  insight(slide, 72, 460, 556, 90,
    "Key property: E[φ̂(Z_i) | X_i] = τ(X_i)\n\nThe pseudo-outcome is an unbiased pointwise proxy for the true CATE at each x — under A1–A3, regardless of how μ̂ and ê are estimated.",
    GREEN);
  insight(slide, 648, 460, 560, 90,
    "Double robustness:\nConsistent if μ̂ correct (direct term dominates)\nOR if ê correct (IPW residuals unbiased)\nBoth wrong → product error: O(||μ̂−μ||·||ê−e||)",
    BLUE);
  mathBox(slide, 72, 562, 1136, 66, "Final CATE estimate",
    "τ̂(x) = argmin_f  Σᵢ (φ̂(Z_i) − f(X_i))²    →   regress pseudo-outcomes on covariates; f can be any ML estimator");
}

// ─── Slide 20 — Cross-fitting algorithm ──────────────────────────────────────
{
  const slide = S[20];
  H(slide, "Cross-fitting: separating nuisance training from CATE regression", "KENNEDY (2023) — Algorithm");
  insight(slide, 72, 152, 1136, 48,
    "Problem: estimating μ̂ and ê on the same data used to compute φ̂ introduces first-order bias — nuisances 'memorize' training data, inflating pseudo-outcomes. Cross-fitting removes this bias via sample splitting.",
    RED);
  step(slide, 72, 208, 326, 200, "1", "Partition data",
    "Split {Z_i}ⁿ into K folds:\nI₁, I₂, ..., I_K\n(K = 3 is standard)\n\nFor fold k: use Iₖᶜ\n(complement) to train\nnuisances, apply on Iₖ",
    BLUE);
  step(slide, 416, 208, 392, 200, "2", "Estimate nuisances (out-of-fold)",
    "For each fold k ∈ {1,...,K}:\n\nFit μ̂₁^{−k}(·) on Iₖᶜ\nFit μ̂₀^{−k}(·) on Iₖᶜ\nFit ê^{−k}(·)  on Iₖᶜ\n\n← use any ML method",
    GOLD);
  step(slide, 826, 208, 382, 200, "3", "Compute pseudo-outcomes",
    "For i ∈ I_k (held-out fold):\nφ̂_i = (μ̂₁^{-k}(X_i) − μ̂₀^{-k}(X_i))\n  + A_i(Y_i−μ̂₁^{-k}(X_i))/ê^{-k}(X_i)\n  − (1−A_i)(Y_i−μ̂₀^{-k}(X_i))/(1−ê^{-k}(X_i))",
    GREEN);
  step(slide, 72, 420, 530, 170, "4", "Final CATE regression (all n obs)",
    "τ̂(x) = argmin_f Σᵢ (φ̂_i − f(X_i))²\n\nChoice of f:\n• Linear — interpretable coefficients\n• Random forest/boosting — flexible\n• Lasso — sparse effect modifiers\n• In our paper: random forest",
    MAROON);
  step(slide, 620, 420, 588, 170, "5", "Optional: Best Linear Projection",
    "γ̂ = argmin_γ Σᵢ (φ̂_i − γ₀ − γᵀX_i)²\n\nInterpretable summary of CATE heterogeneity.\nWald test on γ_j: does covariate j drive\neffect modification?\nOur paper: ranking and regret evaluation",
    MUTED);
  mathBox(slide, 72, 602, 1136, 68, "Why cross-fitting removes bias",
    "φ̂_i is computed from nuisances trained on Iₖᶜ and evaluated on held-out Iₖ → (nuisance, pseudo-outcome) pairs are independent → first-order remainder E[Δμ̂·Δê] ≈ 0");
}

// ─── Slide 21 — Main theorem: convergence rates ───────────────────────────────
{
  const slide = S[21];
  H(slide, "Main theorem: product error structure and optimal rates", "KENNEDY (2023) — Theorem 2");
  mathBox(slide, 72, 152, 1136, 96, "Theorem 2 (Kennedy 2023) — mean-squared error of DR-Learner",
    "E||τ̂ − τ||² ≤ C · { ||μ̂₁−μ₁||₂·||ê−e||₂  +  ||μ̂₀−μ₀||₂·||ê−e||₂  +  r_n² }\n\nr_n = excess risk of the final regression (depends on smoothness of τ and choice of f)");
  sCard(slide, 72, 260, 560, 100, GREEN, "Optimal rate — β-smooth CATE, dim d",
    "Optimal CATE rate: n^{−2β/(2β+d)}\nNuisance requirement: ||μ̂−μ||₂, ||ê−e||₂ = o(n^{−β/(2β+d)})\nDR-Learner achieves oracle CATE rate when nuisances are fast enough");
  sCard(slide, 652, 260, 556, 100, BLUE, "Double robustness in practice",
    "Product structure: total error = O(||μ̂−μ||·||ê−e||)\nIf one nuisance converges at O(n^{−α}), the other at O(n^{−γ}):\nbias = O(n^{−α−γ}) — diminishing even for slow estimators");

  ctx.addShape(slide, { left: 72, top: 372, width: 1136, height: 40, fill: MAROON + "22", line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: 80, top: 382, width: 360, height: 24, text: "Method", fontSize: 13, color: MAROON, bold: true });
  ctx.addText(slide, { left: 460, top: 382, width: 380, height: 24, text: "Bias structure", fontSize: 13, color: MAROON, bold: true });
  ctx.addText(slide, { left: 860, top: 382, width: 340, height: 24, text: "Requirement for consistency", fontSize: 13, color: MAROON, bold: true });

  const cmpRows = [
    ["Plug-in (μ̂₁−μ̂₀ only)", "O(||μ̂₁−μ₁|| + ||μ̂₀−μ₀||)", "Both outcome models correct"],
    ["IPW-only (no outcome model)", "O(||ê−e|| / e(1−e)²)", "Propensity correct + strong overlap"],
    ["DR-Learner — Kennedy (2023)", "O(||μ̂−μ||·||ê−e||)", "Only ONE nuisance needs to be correct"],
  ];
  cmpRows.forEach(([method, bias, req], idx) => {
    const y = 412 + idx * 50;
    const bg = idx === 2 ? GREEN + "22" : (idx % 2 === 0 ? "#FFFFFF" : SOFT);
    const border = idx === 2 ? ctx.line(GREEN, 1.5) : ctx.line(LINE, 0.5);
    ctx.addShape(slide, { left: 72, top: y, width: 1136, height: 50, fill: bg, line: border });
    ctx.addText(slide, { left: 80, top: y + 10, width: 360, height: 30, text: method, fontSize: 12, color: TEXT, bold: idx === 2 });
    ctx.addText(slide, { left: 460, top: y + 10, width: 380, height: 30, text: bias, fontSize: 12, color: TEXT, typeface: "Courier New" });
    ctx.addText(slide, { left: 860, top: y + 10, width: 340, height: 30, text: req, fontSize: 12, color: idx === 2 ? GREEN : TEXT, bold: idx === 2 });
  });

  insight(slide, 72, 564, 1136, 80,
    "RCT bonus: e(x) is KNOWN → ||ê−e||₂ = 0 → bias = 0 regardless of outcome model quality. In our paper, propensity is known by randomization, so the DR-Learner achieves the oracle CATE rate with only the outcome model estimated from data.",
    GREEN);
}

// ─── Slide 22 — Neyman orthogonality ─────────────────────────────────────────
{
  const slide = S[22];
  H(slide, "Why it works: Neyman orthogonality and the influence function", "KENNEDY (2023) — Theory");
  ctx.addText(slide, {
    left: 72, top: 152, width: 1136, height: 36,
    text: "The DR pseudo-outcome is the efficient influence function (EIF) of the CATE functional — this is what makes cross-fitting and ML nuisances compatible with √n inference on τ.",
    fontSize: 16, color: TEXT, bold: true,
  });
  mathBox(slide, 72, 196, 556, 100, "Efficient influence function (EIF)",
    "ψ(Z; τ, e, μ₀, μ₁) = [A/e(X) − (1−A)/(1−e(X))](Y−μ_A(X))  +  [μ₁(X) − μ₀(X) − τ(X)]\n\nφ̂_i = empirical analog with plug-in (μ̂₀, μ̂₁, ê) for (μ₀, μ₁, e)");
  mathBox(slide, 72, 308, 556, 68, "Neyman orthogonality condition",
    "∂/∂η  E[ψ(Z; τ, η)] |_{η=η₀} = 0     (η = (e, μ₀, μ₁))\n\nFirst-order sensitivity to nuisance errors vanishes at truth η₀");
  insight(slide, 648, 196, 560, 180,
    "What orthogonality buys:\n\n1. Nuisance errors enter only at SECOND ORDER — O(||Δμ||·||Δê||), not O(||Δμ||)\n\n2. Allows ML nuisances at slow nonparametric rates while τ̂ achieves √n consistency on smooth CATE subproblems\n\n3. Enables valid inference on τ without Donsker conditions on nuisance function classes",
    BLUE);
  sCard(slide, 72, 388, 540, 196, GOLD, "Without orthogonality (naive plug-in)",
    "τ̂_plugin(x) = μ̂₁(x) − μ̂₀(x)  directly:\n• Bias = E[μ̂₁−μ₁] − E[μ̂₀−μ₀]\n• This is O(||μ̂−μ||) — FIRST-ORDER\n• If ||μ̂−μ|| = n^{-1/4}, bias = n^{-1/4}\n  >> n^{-1/2} threshold for √n-consistency\n• No √n rate without exact model spec.");
  sCard(slide, 632, 388, 576, 196, GREEN, "With orthogonality (DR pseudo-outcome)",
    "Using φ̂_i with cross-fitting:\n• Bias = O(||μ̂−μ||·||ê−e||) — SECOND-ORDER\n• If ||μ̂−μ|| = ||ê−e|| = n^{-1/4}:\n  bias = n^{-1/2} ✓ (√n-consistent)\n• RCT: ê = e known → bias = 0 exactly\n• Flexible ML for nuisances → valid inference");
  insight(slide, 72, 594, 1136, 72,
    "Practical summary: the EIF construction converts nuisance estimation errors from additive (first-order, unavoidable) into multiplicative (second-order, negligible when either nuisance is accurate). Cross-fitting ensures independence so sample splitting does not lose efficiency.",
    MAROON);
}

// ─── Slide 23 — Connection to our estimator ──────────────────────────────────
{
  const slide = S[23];
  H(slide, "Kennedy (2023) in our estimator: the anchored DR learner", "KENNEDY (2023) — Connection to our paper");
  ctx.addText(slide, {
    left: 72, top: 152, width: 1136, height: 36,
    text: "We apply Kennedy's DR learner on top of the Bastani/Tian&Feng corrected baseline risk — replacing μ̂₀ with μ̂₀^anchor, the sparse-corrected estimate.",
    fontSize: 16, color: TEXT, bold: true,
  });
  mathBox(slide, 72, 196, 1136, 88, "Full pipeline pseudo-outcome (our Eq. 5)",
    "ψ_i = (μ̂₁(X_i) − μ̂₀^anchor(X_i))  +  A_i(Y_i − μ̂₁(X_i)) / e(X_i)  −  (1−A_i)(Y_i − μ̂₀^anchor(X_i)) / (1−e(X_i))\n          [anchored direct term]               [treated residual IPW]                    [control residual — uses sparse-corrected μ̂₀^anchor]");

  ctx.addShape(slide, { left: 72, top: 294, width: 1136, height: 40, fill: MAROON + "22", line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: 80, top: 304, width: 510, height: 24, text: "Kennedy (2023) — generic DR learner", fontSize: 13, color: MAROON, bold: true });
  ctx.addText(slide, { left: 630, top: 304, width: 560, height: 24, text: "Our estimator (Proposed / Proposed-CF)", fontSize: 13, color: MAROON, bold: true });

  const mapK = [
    ["μ̂₀(x)  — any ML outcome model for control", "μ̂₀^anchor(x)  — Tian&Feng corrected (K sources + target placebo)"],
    ["μ̂₁(x)  — any ML outcome model for treatment", "μ̂₁(x)  — estimated from target treated arm only"],
    ["ê(x)  — estimated propensity score", "e(x)  — KNOWN exactly (randomized, by design)"],
    ["Final: τ̂(x) = E[φ̂|X=x], any ML method", "Final: τ̂(x) = random forest on ψ_i"],
    ["Proposed-CF: cross-fit φ̂_i across 3 folds", "Cross-fitting improves calibration → ECE rank 1.3"],
  ];
  mapK.forEach(([left, right], idx) => {
    const y = 334 + idx * 46;
    const bg = idx % 2 === 0 ? "#FFFFFF" : SOFT;
    ctx.addShape(slide, { left: 72, top: y, width: 1136, height: 46, fill: bg, line: ctx.line(LINE, 0.5) });
    ctx.addText(slide, { left: 80, top: y + 8, width: 510, height: 30, text: left, fontSize: 12, color: TEXT, typeface: "Courier New" });
    ctx.addText(slide, { left: 630, top: y + 8, width: 560, height: 30, text: right, fontSize: 12, color: TEXT });
  });

  insight(slide, 72, 566, 540, 114,
    "Why anchoring μ̂₀^anchor matters:\nStandard TargetOnly uses μ̂₀ from target data only — scarce, high variance. Our μ̂₀^anchor pools K source RCTs via sparse correction → lower variance → lower variance pseudo-outcomes ψ_i → more precise CATE τ̂(x). This is the key empirical improvement over Kennedy's generic DR learner.",
    GREEN);
  insight(slide, 632, 566, 576, 114,
    "Theorem 1 (connected target):\nμ̂₀^anchor is identified. ψ_i is Neyman-orthogonal → τ̂ achieves the identified CATE rate. Theorem 2 (disconnected — target placebo only):\nμ̂₀^anchor is working-model transport (A6). ψ_i remains well-calibrated for ranking and regret under the transport condition.",
    MAROON);
}

// ─── Slide 24 — Our paper section divider ────────────────────────────────────
{
  const slide = S[24];
  ctx.addShape(slide, {
    left: 0, top: 0, width: 1280, height: 720,
    fill: MAROON, line: ctx.line("#00000000", 0),
  });
  ctx.addText(slide, {
    left: 80, top: 210, width: 1120, height: 80,
    text: "Our Estimator: Rate Statements and Proof Sketches",
    fontSize: 40, color: "#FFFFFF", bold: true, align: "center", typeface: "Aptos Display",
  });
  ctx.addText(slide, {
    left: 80, top: 308, width: 1120, height: 36,
    text: "Theorems 1–2 from the companion appendix, with full intuition",
    fontSize: 20, color: GOLD, bold: false, align: "center",
  });
  // Two theorem summary boxes
  ctx.addShape(slide, {
    left: 152, top: 368, width: 430, height: 90, geometry: "roundRect",
    fill: "#FFFFFF22", line: ctx.line(GOLD, 1.5),
  });
  ctx.addText(slide, {
    left: 166, top: 378, width: 402, height: 70,
    text: "Theorem 1 (connected target)\n√n₀(τ̂_DR(x) − τ₀(x)) ⇒ N(0, V(x))\nIdentified CATE with √n₀ rate",
    fontSize: 14, color: "#FFFFFF", align: "center",
  });
  ctx.addShape(slide, {
    left: 700, top: 368, width: 430, height: 90, geometry: "roundRect",
    fill: "#FFFFFF22", line: ctx.line(BLUE, 1.5),
  });
  ctx.addText(slide, {
    left: 714, top: 378, width: 402, height: 70,
    text: "Theorem 2 (disconnected target)\n‖τ̂_B − τ₀‖ ≤ est. error + ε_τ + O_p(η^{1/2})\nTransport error decomposition",
    fontSize: 14, color: "#FFFFFF", align: "center",
  });
  ctx.addText(slide, {
    left: 80, top: 476, width: 1120, height: 30,
    text: "Full proofs in Appendix A of the companion repository",
    fontSize: 15, color: "#FFFFFF99", align: "center",
  });
}

// ─── Slide 25 — Lemma 1: nuisance rate via glmtrans ──────────────────────────
{
  const slide = S[25];
  H(slide, "Stage 1 nuisance rates via glmtrans (Lemma 1)", "OUR PAPER — Appendix A, Lemma 1");
  ctx.addText(slide, {
    left: 72, top: 152, width: 1136, height: 32,
    text: "Before the DR theorem we need an L₂(P₀) prediction rate for the glmtrans outcome regressions — the bridge from Tian & Feng to Stage 2.",
    fontSize: 15, color: TEXT, bold: true,
  });
  mathBox(slide, 72, 192, 760, 50, "L₂(P₀) norm (target-site covariate distribution)",
    "‖f‖_{L₂(P₀)} := (E[f(X)² | S=0])^{1/2}     [root-mean-squared error over target covariates]");
  mathBox(slide, 72, 252, 760, 120, "Lemma 1 — glmtrans prediction error rate (per arm a ∈ {0,1})",
    "‖μ̂_{a,0} − μ_{a,0}‖_{L₂(P₀)}  ≲\n\n    (s log p / (n_{a,0} + n_{a,Aₐ}))^{1/2}      +      (log p / n_{a,0})^{1/4} · h^{1/2}\n         [transfer: variance reduction]                    [target debiasing term]");
  mathBox(slide, 72, 382, 760, 68, "DML sufficient condition (used in Theorem 1)",
    "‖μ̂_{a,0} − μ_{a,0}‖_{L₂(P₀)} = o_p(n₀^{−1/4})     →    need both Lemma 1 terms = o(n₀^{−1/4})");
  insight(slide, 854, 192, 354, 90,
    "Term 1 (transfer):\nReplaces n_{a,0} by n_{a,0} + n_{a,Aₐ}.\nMore informative sources → smaller rate.\nRatio improvement ≈ √(n_{a,Aₐ}/n_{a,0}).",
    BLUE);
  insight(slide, 854, 294, 354, 90,
    "Term 2 (debiasing):\nTarget-only data estimates contrast.\nShrinks as h → 0 (sources closer to target).\nControls bias introduced by pooling sources.",
    GOLD);
  insight(slide, 854, 396, 354, 56,
    "Source detection:\nÂ_a = A_{a,h} with prob ≥ 1−δ\n(Tian & Feng Theorem 4).",
    GREEN);
  sCard(slide, 72, 460, 1136, 162, MAROON, "Sufficient condition for Theorem 1 (explicit in source and target sizes)",
    "Transfer term = o(n₀^{−1/4}):   s log p / (n_{a,0} + n_{a,Aₐ}) = o(n₀^{−1/2})\nDebiasing term = o(n₀^{−1/4}):   (log p / n_{a,0})^{1/4} · h^{1/2} = o(n₀^{−1/4})\n\nWeaker condition for consistency only: both Lemma 1 terms = o(1). This is the condition stated in Theorem 1 — substantially weaker than the standard DML n^{−1/4} requirement.", 14);
}

// ─── Slide 26 — Theorem 1: statement + intuition ─────────────────────────────
{
  const slide = S[26];
  H(slide, "Theorem 1: asymptotic linearity for connected target (Proposed-CF)", "OUR PAPER — Theorem 1");
  mathBox(slide, 72, 152, 1136, 160, "Theorem 1 — Asymptotic linearity (full statement)",
    "Assume: (i) A1–A3; (ii) finite fourth moments of Y, bounded propensities ε ≤ e₀(x) ≤ 1−ε; (iii) cross-fitting of nuisances;\n(iv) ‖μ̂_{a,0} − μ_{a,0}‖_{L₂(P₀)} = o_p(1) for a ∈ {0,1}; (v) stable Gram matrix G₀ = E[Z_i Z_iᵀ | S=0].\n\nThen:    τ̂_DR(x) − τ₀(x)  =  (1/n₀) Σᵢ φ(Oᵢ; x)  +  o_p(n₀^{−1/2})\n\nwhere φ(Oᵢ; x) = b(x)ᵀ G₀⁻¹ Zᵢ · (Aᵢ − e₀(Xᵢ)) / (e₀(Xᵢ){1−e₀(Xᵢ)}) · (Yᵢ − μ_{Aᵢ,0}(Xᵢ))\n\nConsequently:     √n₀ (τ̂_DR(x) − τ₀(x))  ⇒  N(0, V(x)),     V(x) = Var(φ(O; x) | S=0)");

  sCard(slide, 72, 322, 540, 190, GREEN, "What the theorem says",
    "1. τ̂_DR(x) is √n₀-consistent and asymptotically normal at every fixed x\n\n2. The influence function φ(O; x) involves only KNOWN propensity e₀(x) — no propensity estimation error\n\n3. Nuisance errors (μ̂) enter only at second order → o_p(n₀^{−1/2}) remainder");
  sCard(slide, 652, 322, 556, 190, BLUE, "Key conditions explained",
    "Condition (iv): only o_p(1) consistency needed — weaker than standard DML o_p(n₀^{−1/4})\n\nWhy? Propensity known by design → no cross-term ‖Δμ‖·‖Δê‖ error from propensity; only ‖Δμ‖/√n₀ → 0\n\nCondition (v): identifies linear projection at x in finite samples");
  insight(slide, 72, 522, 540, 88,
    "Source data contribution:\nLemma 1 shows nuisance condition (iv) holds when n_{a,Aₐ} is large — more transferable source data makes Term 1 = (s log p / n_{a,Aₐ})^{1/2} smaller, pulling nuisances to zero faster and shrinking the second-order remainder.",
    GOLD);
  insight(slide, 652, 522, 556, 88,
    "RCT bonus (propensity known):\nThe influence function φ uses the EXACT e₀(x). In observational studies, ê(x) would add a cross-term error O(‖Δμ‖·‖Δê‖). Here that term is 0, giving exactly the semiparametric efficiency bound.",
    MAROON);
}

// ─── Slide 27 — Proof sketch: Theorem 1 ──────────────────────────────────────
{
  const slide = S[27];
  H(slide, "Proof sketch: three-step asymptotic linearity argument", "OUR PAPER — Proof of Theorem 1");
  step(slide, 72, 152, 1136, 148, "1", "Oracle pseudo-outcome: E[ψ⁰_i | X_i, S_i=0] = τ₀(X_i)",
    "Define ψ⁰_i = μ_{1,0}(Xᵢ) − μ_{0,0}(Xᵢ)  +  (Aᵢ − e₀(Xᵢ))/(e₀(Xᵢ){1−e₀(Xᵢ)}) · (Yᵢ − μ_{Aᵢ,0}(Xᵢ))\n\nBy randomization (A1–A2): E[Yᵢ − μ_{Aᵢ,0}(Xᵢ) | Xᵢ, Aᵢ, S=0] = 0 → centered residual → E[ψ⁰_i | Xᵢ] = τ₀(Xᵢ)\n\nTherefore E[Zᵢ(ψ⁰_i − Zᵢᵀθ₀) | S=0] = 0 → oracle score is unbiased at true CATE parameter θ₀",
    BLUE);
  step(slide, 72, 308, 1136, 148, "2", "Decompose θ̂ − θ₀ = T₁ₙ (oracle) + T₂ₙ (nuisance remainder) → show T₂ₙ = o_p(n₀^{−1/2})",
    "θ̂ − θ₀ = Ĝ⁻¹[(1/n₀)Σ Zᵢ(ψ̂ᵢ − ψ⁰ᵢ)] + Ĝ⁻¹[(1/n₀)Σ Zᵢ(ψ⁰ᵢ − Zᵢᵀθ₀)]  =: T₂ₙ + T₁ₙ\n\nFor T₂ₙ: by CROSS-FITTING, Δ_a^{(−k)}(Xᵢ) ⊥ fold-k evaluation obs. → E[ψ̂ᵢ−ψ⁰ᵢ | Xᵢ, training] = 0\n\nE‖(1/n₀)Σ Zᵢ(ψ̂ᵢ−ψ⁰ᵢ)‖² ≲ (‖Δμ₀‖² + ‖Δμ₁‖²)/n₀  →  ‖T₂ₙ‖ = O_p((Aₙ/√n₀)) = o_p(n₀^{−1/2})  since Aₙ = o_p(1)",
    GOLD);
  step(slide, 72, 464, 1136, 148, "3", "CLT on oracle term T₁ₙ → asymptotic normality",
    "T₁ₙ = Ĝ⁻¹(1/n₀)Σ Zᵢ · (Aᵢ−e₀(Xᵢ))/(e₀(Xᵢ){1−e₀(Xᵢ)}) · (Yᵢ−μ_{Aᵢ,0}(Xᵢ))\n\nĜ⁻¹ = G₀⁻¹ + o_p(1)  →  evaluating at fixed x:  b(x)ᵀ T₁ₙ = (1/n₀) Σ φ(Oᵢ;x) + o_p(n₀^{−1/2})\n\nφ(O;x) has mean 0 and finite variance V(x) by A3 + bounded propensities → CLT gives √n₀ · (1/n₀)Σ φ(Oᵢ;x) ⇒ N(0,V(x))",
    GREEN);
  insight(slide, 72, 620, 1136, 60,
    "Key move in Step 2: cross-fitting ensures the nuisance error Δ_a^{(−k)} is INDEPENDENT of the held-out pseudo-outcome (Oᵢ, i ∈ I_k). Without independence, E[Zᵢ(ψ̂ᵢ−ψ⁰ᵢ)] could be O(‖Δμ‖) — first-order, not o_p(n₀^{−1/2}).",
    MAROON);
}

// ─── Slide 28 — Theorem 2: statement + intuition ─────────────────────────────
{
  const slide = S[28];
  H(slide, "Theorem 2: transport error decomposition for disconnected target (Proposed-B)", "OUR PAPER — Theorem 2");
  mathBox(slide, 72, 152, 1136, 120, "Theorem 2 — Transport error decomposition (full statement)",
    "Assume A1–A3 and A6. In the disconnected regime, τ₀ is not identified from target data alone. Compare τ̂_B to the oracle transported target τ*(x) := E[τ_S(x) | S ∈ C₀*].\n\n‖τ̂_B − τ₀‖_{L₂(P₀)}  ≤  ‖τ̂_B − τ*‖_{L₂(P₀)}  +  ‖τ* − τ₀‖_{L₂(P₀)}  +  Δ_sel\n                                  [estimation error]          [structural transport bias ≤ ε_τ]       [screening error = O_p(η^{1/2})]\n\nIf P(Ĉ₀ ⊆ C₀*) ≥ 1−η and E‖τ̂_B − τ*‖² < ∞, then Δ_sel = O_p(η^{1/2}).");
  sCard(slide, 72, 282, 338, 290, BLUE, "Term 1: estimation error",
    "‖τ̂_B − τ*‖_{L₂(P₀)}\n\nHow well the source-DR learner (trained on Ĉ₀) predicts the oracle-transported target CATE τ* on target covariates.\n\nControlled by:\n• Source sample sizes n_{a,c} for c ∈ Ĉ₀\n• Complexity of CATE learner\n• Transfer variance reduction from pooling");
  sCard(slide, 430, 282, 370, 290, RED, "Term 2: structural transport bias",
    "‖τ* − τ₀‖_{L₂(P₀)} ≤ ε_τ\n\nIrreducible mismatch between oracle selected sources and true target CATE on target support.\n\nThis term is ZERO only if:\n• Selected sources have τ_c(x) = τ₀(x) a.s.\nOtherwise bounded by ε_τ from A6.\n\nNot reducible by more data from sources — fundamental structural gap.");
  sCard(slide, 820, 282, 388, 290, GOLD, "Term 3: screening error",
    "Δ_sel = ‖(τ̂_B−τ*)·1_{E^c}‖_{L₂(P₀)}\n\nActive only when Ĉ₀ ⊄ C₀* (screening admits a bad source). Controlled by η = P(Ĉ₀ ⊄ C₀*).\n\nΔ_sel = O_p(η^{1/2})  [via Cauchy-Schwarz]\n\nη → 0 as placebo sample n_{0,0} → ∞ by Tian & Feng detection consistency.");
  insight(slide, 72, 582, 1136, 70,
    "What A6 provides: (a) the oracle good-source set C₀* exists with ‖τ_S − τ₀‖_{L₂(P₀)} ≤ ε_τ for S ∈ C₀*; (b) placebo screening achieves Ĉ₀ ⊆ C₀* with prob ≥ 1−η. The theorem says: if A6 holds and screening works, total error ≈ source estimation error + ε_τ.",
    GREEN);
  insight(slide, 72, 660, 1136, 44,
    "Remark: when ε_τ is large (sources far from target), Term 2 dominates — adding source data cannot help. This is the fundamental limit of non-identified transport.",
    MUTED);
}

// ─── Slide 29 — Proof sketch: Theorem 2 + cross-arm degradation ──────────────
{
  const slide = S[29];
  H(slide, "Proof sketch: auxiliary predictor trick + cross-arm degradation", "OUR PAPER — Proofs of Theorem 2 and Proposition 1");
  step(slide, 72, 152, 640, 156, "1", "Auxiliary predictor + triangle inequality",
    "Define: τ̃_B = τ̂_B · 1_E + τ* · 1_{E^c}   (replace by oracle on screening failure event E^c)\n\nTriangle inequality:  ‖τ̂_B − τ₀‖ ≤ ‖τ̂_B − τ̃_B‖ + ‖τ̃_B − τ*‖ + ‖τ* − τ₀‖\n                                           =: Δ_sel              = ‖(τ̂_B−τ*)·1_E‖     ≤ ε_τ\n\n1_E multiplication only reduces norm → identification of screening-only cost",
    BLUE);
  step(slide, 72, 318, 640, 148, "2", "Structural bias ≤ ε_τ via Jensen's inequality",
    "τ*(x) − τ₀(x) = E[τ_S(x) − τ₀(x) | S ∈ C₀*] = E[g_S(x) | S ∈ C₀*]\n\n‖τ* − τ₀‖_{L₂(P₀)} = ‖E[g_S | S ∈ C₀*]‖ ≤ E[‖g_S‖_{L₂(P₀)} | S ∈ C₀*]   [Minkowski]\n\nA6(b): ‖τ_S − τ₀‖_{L₂(P₀)} ≤ ε_τ for S ∈ C₀*  →  ‖τ* − τ₀‖_{L₂(P₀)} ≤ ε_τ  ✓",
    GOLD);
  step(slide, 72, 476, 640, 134, "3", "Screening error = O_p(η^{1/2}) via Cauchy-Schwarz",
    "E[Δ_sel] = E[‖τ̂_B − τ*‖_{L₂(P₀)} · 1_{E^c}]  ≤  (E‖τ̂_B−τ*‖²)^{1/2} · P(E^c)^{1/2}  ≤  M₂^{1/2} · η^{1/2}\n\nMarkov → P(Δ_sel > t·η^{1/2}) ≤ M₂^{1/2}/t   for any t > 0\n\n→  Δ_sel = O_p(η^{1/2}).  η → 0 as n_{0,0} → ∞ by Tian & Feng Theorem 4.",
    GREEN);
  mathBox(slide, 728, 152, 480, 238, "Proposition 1 — Cross-arm degradation",
    "Model: δ₁*(x) = ρ·δ₀*(x) + ζ*(x)\n       (coupling placebo-to-treated correction)\n\nStructural bias (ρ_alg = 1 heuristic):\n‖τ* − τ₀‖_{L₂(P₀)} ≤\n\n  |1−ρ|·‖δ₀*‖_{L₂(P₀)} + ‖ζ*‖_{L₂(P₀)} + ‖r₁‖_{L₂(P₀)}\n    [coupling gap]       [unexplained]      [approx error]");
  insight(slide, 728, 402, 480, 110,
    "Intuition: imperfect cross-arm transfer (ρ < 1) enters the BIAS term — it shifts the centering of τ̂ around τ₀, not the √n₀ CLT fluctuation. More placebo data cannot reduce |1−ρ|·‖δ₀*‖; only stronger A6 (smaller ε_τ, closer sources) can.",
    BLUE);
  insight(slide, 728, 524, 480, 86,
    "Combined:\n‖τ̂ − τ₀‖ ≤ ‖τ̂ − τ*‖ + ε_τ\nFirst term: √N CLT + second-order nuisance.\nSecond term: controlled by A6 + Prop. 1.",
    MAROON);
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
