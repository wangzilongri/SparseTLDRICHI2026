import fs from "node:fs/promises";
import path from "node:path";

import {
  createSlideContext,
  ensureArtifactToolWorkspace,
  importArtifactTool,
  padSlideNumber,
  saveBlobToFile,
} from "/Users/zilongwang/.codex/plugins/cache/openai-primary-runtime/presentations/26.521.10419/skills/presentations/scripts/artifact_tool_utils.mjs";

const workspace = "/Users/zilongwang/Transfer-Learning-for-Individual-Patient-Data-for-Clinical-Trials/outputs/manual-20260521-ichi-talk/presentations/ichi-2026-talk";
const starterPath = path.join(workspace, "template-starter.pptx");
const outputDir = path.join(workspace, "output");
const previewDir = path.join(workspace, "preview");
const layoutDir = path.join(workspace, "layout");
const finalPptx = path.join(outputDir, "transfer-learning-meta-analysis-ichi-2026-talk.pptx");

const MAROON = "#8A0020";
const MAROON_DARK = "#650018";
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

function slidesFromPresentation(p) {
  if (Array.isArray(p.slides?.items)) return p.slides.items;
  return Array.from({ length: p.slides.count }, (_, index) => p.slides.getItem(index));
}

const slides = slidesFromPresentation(presentation);

function textShapes(slide) {
  return slide.shapes.items.filter((shape) => shape.text && typeof shape.text.toString === "function");
}

function textOf(shape) {
  return shape.text?.toString?.() || "";
}

function findByText(slide, needle) {
  return textShapes(slide).find((shape) => textOf(shape).trim() === needle);
}

function findContains(slide, needle) {
  return textShapes(slide).find((shape) => textOf(shape).includes(needle));
}

function setText(shape, value, options = {}) {
  if (!shape) return;
  shape.text.set(value);
  if (options.fontSize) shape.text.fontSize = options.fontSize;
  if (options.color) shape.text.color = options.color;
  if (options.bold !== undefined) shape.text.bold = options.bold;
  if (options.typeface) shape.text.typeface = options.typeface;
  if (options.align) shape.text.alignment = options.align;
  if (options.valign) shape.text.verticalAlignment = options.valign;
}

function setTemplateTitle(slide, title, size = 38) {
  const titleShape = findByText(slide, "Title") || findContains(slide, "Workflow, study design") || findContains(slide, "Acknowledgments");
  setText(titleShape, title, { fontSize: size, color: MAROON, bold: true, typeface: "Aptos Display" });
}

function clearContentPlaceholder(slide) {
  const body = findContains(slide, "point 1");
  if (body) body.delete();
}

function timePill(slide, text, x = 1058, y = 626) {
  ctx.addShape(slide, {
    left: x,
    top: y,
    width: 150,
    height: 26,
    geometry: "roundRect",
    fill: "#FFFFFF",
    line: ctx.line(LINE, 1),
    name: "timing-pill",
  });
  ctx.addText(slide, {
    left: x + 12,
    top: y + 5,
    width: 126,
    height: 16,
    text,
    fontSize: 13,
    color: MUTED,
    align: "center",
    name: "timing-label",
  });
}

function claim(slide, text, y = 148) {
  ctx.addText(slide, {
    left: 72,
    top: y,
    width: 1040,
    height: 44,
    text,
    fontSize: 18,
    color: TEXT,
    bold: true,
    name: "claim",
  });
}

function card(slide, { x, y, w, h, eyebrow, title, body, accent = GOLD, fill = "#FFFFFF", titleSize = 22 }) {
  ctx.addShape(slide, {
    left: x,
    top: y,
    width: w,
    height: h,
    geometry: "roundRect",
    fill,
    line: ctx.line(LINE, 1),
    name: "card",
  });
  ctx.addShape(slide, {
    left: x,
    top: y,
    width: w,
    height: 6,
    geometry: "rect",
    fill: accent,
    line: ctx.line("#00000000", 0),
    name: "card-accent",
  });
  if (eyebrow) {
    ctx.addText(slide, {
      left: x + 20,
      top: y + 24,
      width: w - 40,
      height: 20,
      text: eyebrow,
      fontSize: 18,
      color: MAROON,
      bold: true,
      name: "card-eyebrow",
    });
  }
  ctx.addText(slide, {
    left: x + 20,
    top: y + (eyebrow ? 56 : 24),
    width: w - 40,
    height: 28,
    text: title,
    fontSize: titleSize,
    color: TEXT,
    bold: true,
    name: "card-title",
  });
  ctx.addText(slide, {
    left: x + 20,
    top: y + (eyebrow ? 94 : 62),
    width: w - 40,
    height: h - (eyebrow ? 110 : 78),
    text: body,
    fontSize: 17,
    color: MUTED,
    name: "card-body",
  });
}

function comparisonRow(slide, y, leftHead, leftText, rightHead, rightText) {
  ctx.addText(slide, { left: 106, top: y, width: 310, height: 24, text: leftHead, fontSize: 19, color: MAROON, bold: true });
  ctx.addText(slide, { left: 106, top: y + 34, width: 400, height: 58, text: leftText, fontSize: 17, color: MUTED });
  ctx.addText(slide, { left: 602, top: y, width: 310, height: 24, text: rightHead, fontSize: 19, color: MAROON, bold: true });
  ctx.addText(slide, { left: 602, top: y + 34, width: 470, height: 58, text: rightText, fontSize: 17, color: MUTED });
  ctx.addShape(slide, { left: 548, top: y + 2, width: 2, height: 82, fill: LINE, line: ctx.line("#00000000", 0) });
}

function metricRow(slide, y, label, value, max, color) {
  const barX = 356;
  const barW = 520;
  ctx.addText(slide, { left: 122, top: y - 2, width: 200, height: 24, text: label, fontSize: 17, color: TEXT, bold: label.startsWith("Proposed") });
  ctx.addShape(slide, { left: barX, top: y, width: barW, height: 20, geometry: "roundRect", fill: "#EEEAE5", line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { left: barX, top: y, width: Math.max(8, (value / max) * barW), height: 20, geometry: "roundRect", fill: color, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { left: barX + barW + 20, top: y - 3, width: 68, height: 24, text: value.toFixed(1), fontSize: 17, color: TEXT, bold: label.startsWith("Proposed") });
}

function statCard(slide, x, y, w, label, value, sub, color = MAROON) {
  ctx.addShape(slide, { left: x, top: y, width: w, height: 132, geometry: "roundRect", fill: "#FFFFFF", line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: x + 20, top: y + 18, width: w - 40, height: 26, text: label, fontSize: 16, color: MUTED, bold: true });
  ctx.addText(slide, { left: x + 20, top: y + 48, width: w - 40, height: 46, text: value, fontSize: 35, color, bold: true, typeface: "Aptos Display" });
  ctx.addText(slide, { left: x + 20, top: y + 94, width: w - 40, height: 26, text: sub, fontSize: 14, color: MUTED });
}

function groupedBars(slide, data, x, y, w, h) {
  const max = Math.max(...data.flatMap((d) => [d.proxy, d.proposed]));
  const groupW = w / data.length;
  ctx.addShape(slide, { left: x, top: y, width: w, height: h, fill: "#FFFFFF", line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: x + 18, top: y + 16, width: w - 36, height: 24, text: "Disconnected PEHE, target placebo only (m0=50)", fontSize: 18, color: TEXT, bold: true });
  data.forEach((d, i) => {
    const gx = x + i * groupW + 34;
    const base = y + h - 54;
    const scale = (h - 112) / max;
    const proxyH = d.proxy * scale;
    const proposedH = d.proposed * scale;
    ctx.addShape(slide, { left: gx, top: base - proxyH, width: 32, height: proxyH, fill: RED, line: ctx.line("#00000000", 0) });
    ctx.addShape(slide, { left: gx + 42, top: base - proposedH, width: 32, height: proposedH, fill: GREEN, line: ctx.line("#00000000", 0) });
    ctx.addText(slide, { left: gx - 10, top: base + 10, width: 94, height: 18, text: `p=${d.p}`, fontSize: 13, color: MUTED, align: "center" });
  });
  ctx.addShape(slide, { left: x + w - 210, top: y + 52, width: 12, height: 12, fill: RED, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { left: x + w - 190, top: y + 47, width: 160, height: 20, text: "ProxyOnly", fontSize: 14, color: MUTED });
  ctx.addShape(slide, { left: x + w - 210, top: y + 78, width: 12, height: 12, fill: GREEN, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { left: x + w - 190, top: y + 73, width: 160, height: 20, text: "Proposed-B", fontSize: 14, color: MUTED });
}

function addTalkHeader(slide, title, time, size = 38) {
  setTemplateTitle(slide, title, size);
  timePill(slide, time);
}

// Slide transition helper — gracefully degrades if the artifact tool does not
// expose a transition API (PPTX will still build; set manually in PowerPoint
// using the design described in SLIDE_RATIONALE.md).
function setTransition(slide, type, durationMs = 700) {
  try {
    if (slide.transition !== undefined) {
      slide.transition.type = type;
      slide.transition.duration = durationMs;
    }
  } catch (_) { /* API does not expose transitions on this version — set manually */ }
}

// Slide 1 — no incoming transition (first slide)
{
  const slide = slides[0];
  setText(findByText(slide, "Session / Track"), "Research Paper", { fontSize: 18, color: MAROON, bold: true, align: "center" });
  setText(findByText(slide, "Insert Presentation Title"), "Transfer Learning for Meta-analysis\nUnder Covariate Shift", {
    fontSize: 37,
    color: "#FFFFFF",
    bold: true,
    typeface: "Aptos Display",
  });
  setText(
    findByText(slide, "Subtitle, study framing, or one-sentence contribution statement"),
    "Placebo-anchored proxy-gold learning for target-specific treatment effects",
    { fontSize: 19, color: "#FFFFFF" },
  );
  setText(
    findContains(slide, "Authors"),
    "Zilong Wang, Ali Abdeen, Turgay Ayer | Georgia Institute of Technology",
    { fontSize: 18, color: "#FFFFFF" },
  );
  timePill(slide, "0:00-0:30");
  setTransition(slide, "none", 0);
}

// Slide 2 — fade (700ms) from title; act break. Pill adjusted +1s: 0:31
{
  const slide = slides[1];
  addTalkHeader(slide, "Clinical trial evidence rarely lands in the target population", "0:31-1:45", 37);
  setTransition(slide, "fade", 700);
  clearContentPlaceholder(slide);
  claim(slide, "The decision target is patient-level and local; the available evidence is multi-site and shifted.");
  card(slide, {
    x: 72,
    y: 206,
    w: 342,
    h: 200,
    eyebrow: "01",
    title: "Different enrolled patients",
    body: "RCT sites can differ by eligibility, geography, baseline risk, and case mix. Pooling can estimate the wrong population.",
    accent: GOLD,
  });
  card(slide, {
    x: 469,
    y: 206,
    w: 342,
    h: 200,
    eyebrow: "02",
    title: "Different baseline risk",
    body: "A shared comparator is not automatically exchangeable once covariates and residual risk drift across studies.",
    accent: BLUE,
  });
  card(slide, {
    x: 866,
    y: 206,
    w: 342,
    h: 200,
    eyebrow: "03",
    title: "Patient-level decisions",
    body: "Decision makers need CATEs, targeting, regret, and calibration - not only a network-wide average effect.",
    accent: GREEN,
  });
  await ctx.addImage(slide, {
    path: "/Users/zilongwang/Sparse_TL_DR_ICHI2026/presentation/figures/covariate-shift.png",
    left: 82, top: 418, width: 1006, height: 192,
    fit: "contain",
    alt: "Source and target covariate distributions illustrating shift",
  });
}

// Slide 3 — cut (0ms) from slide 2; within same problem-setup act
{
  const slide = slides[2];
  addTalkHeader(slide, "The gap: standard transport needs conditions the target lacks", "1:45-3:00", 37);
  setTransition(slide, "none", 0);
  clearContentPlaceholder(slide);
  claim(slide, "The hard case is weakly connected or disconnected target evidence under covariate shift.");
  ctx.addShape(slide, { left: 72, top: 190, width: 1136, height: 406, geometry: "roundRect", fill: "#FFFFFF", line: ctx.line(LINE, 1) });
  ctx.addShape(slide, { left: 72, top: 190, width: 1136, height: 6, fill: GOLD, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { left: 106, top: 218, width: 360, height: 24, text: "Common assumption", fontSize: 20, color: MAROON, bold: true });
  ctx.addText(slide, { left: 602, top: 218, width: 420, height: 24, text: "Failure mode in this talk", fontSize: 20, color: MAROON, bold: true });
  comparisonRow(slide, 270, "Network connectivity", "Target trial connects through a shared comparator arm.", "Disconnected target", "Target may have placebo only for the treatment of interest.");
  comparisonRow(slide, 374, "Comparator exchangeability", "Placebo arms are comparable after measured adjustment.", "Residual baseline drift", "Measured shift plus site-specific risk makes direct transfer biased.");
  comparisonRow(slide, 478, "Average effect is enough", "NMA or transport reports a marginal target estimand.", "Individualized decisions", "The task is calibrated patient-level CATE and targeting.");
}

// Slide 4 — cover-right (500ms); major argument pivot: problem → answer
{
  const slide = slides[3];
  addTalkHeader(slide, "Core idea: target placebo is the gold calibration signal", "3:00-4:15", 37);
  setTransition(slide, "cover", 500);
  clearContentPlaceholder(slide);
  claim(slide, "Source data is abundant but miscalibrated for the target; target placebo is scarce but perfectly calibrated — sparse correction bridges the two.");
  await ctx.addImage(slide, {
    path: "/Users/zilongwang/Sparse_TL_DR_ICHI2026/presentation/figures/proxy-gold-paradigm.png",
    left: 72, top: 200, width: 1136, height: 460,
    fit: "contain",
    alt: "Proxy-gold paradigm: source sites have low-variance biased estimates; target placebo has high-variance unbiased labels; anchoring yields low-variance unbiased CATE",
  });
}

// Slide 5 — cut (0ms); zoom-in: same four-step frame, higher resolution
{
  const slide = slides[4];
  addTalkHeader(slide, "Estimator pipeline: anchor first, orthogonalize second", "4:15-6:00", 37);
  setTransition(slide, "none", 0);
  const replacements = [
    ["Data", "Fit source models"],
    ["Describe the cohort, records, devices, or multimodal sources.", "Learn mu0 and mu1 from source IPD; randomized propensities are known."],
    ["Method", "Anchor baseline"],
    ["Summarize modeling, evaluation, or intervention design.", "Use target placebo gold labels to correct target baseline risk."],
    ["Validation", "Build pseudo-outcomes"],
    ["Explain benchmarks, comparison groups, or review procedures.", "Form DR pseudo-outcomes with cross-fitting when target treated data exist."],
    ["Impact", "Estimate CATE"],
    ["Connect the workflow to outcomes, deployment, or next steps.", "Predict tau(x), evaluate ranking, calibration, and treatment policy regret."],
  ];
  for (const [oldText, newText] of replacements) {
    const shape = findByText(slide, oldText);
    if (shape) {
      setText(shape, newText, {
        bold: ["Fit source models", "Anchor baseline", "Build pseudo-outcomes", "Estimate CATE"].includes(newText),
        fontSize: newText === "Build pseudo-outcomes" ? 19 : undefined,
      });
    }
  }
  await ctx.addImage(slide, {
    path: "/Users/zilongwang/Sparse_TL_DR_ICHI2026/presentation/figures/method-pipeline.png",
    left: 72, top: 155, width: 1136, height: 470,
    fit: "contain",
    alt: "Method pipeline: proxy estimate → gold anchor → sparse correction → DR learner",
  });
}

// Slide 6 — fade (700ms); section break: pipeline → regime distinction. Pill adjusted +1s: 6:01
{
  const slide = slides[5];
  addTalkHeader(slide, "Two target regimes, two interpretations", "6:01-7:15");
  setTransition(slide, "fade", 700);
  const title = findContains(slide, "Acknowledgments");
  setText(title, "Two target regimes, two interpretations", { fontSize: 41, color: MAROON, bold: true, typeface: "Aptos Display" });
  const pairs = [
    ["Collaborators", "Connected target"],
    ["List co-authors, labs, institutions, health systems, or deployment partners here.", "Target has treated and placebo outcomes. The estimator targets an identified target-site CATE and admits a Neyman-orthogonal expansion."],
    ["Funding", "Disconnected target"],
    ["Grant support, sponsorship, contracts, or infrastructure acknowledgments.", "Target has placebo only. The output is a screen-then-transport working-model estimate under explicit A6 transport assumptions."],
    ["Disclosure", "What to say"],
    ["State relevant conflicts of interest, industry affiliations, or product relationships.", "The talk should separate what is identified from what is transported; that distinction is the methodological honesty."],
  ];
  for (const [oldText, newText] of pairs) {
    const shape = findByText(slide, oldText);
    if (shape) setText(shape, newText, { bold: ["Connected target", "Disconnected target", "What to say"].includes(newText), color: ["Connected target", "Disconnected target", "What to say"].includes(newText) ? MAROON : MUTED });
  }
}

// Slide 7 — push-left (500ms); major pivot: method act → evidence act
{
  const slide = slides[6];
  addTalkHeader(slide, "Evaluation: accuracy, targeting, regret, and calibration", "7:15-8:30", 37);
  setTransition(slide, "push", 500);
  const replacements = [
    ["Data", "Synthetic RCTs"],
    ["Describe the cohort, records, devices, or multimodal sources.", "Controlled covariate shift, known potential outcomes, 100 Monte Carlo replicates."],
    ["Method", "Ablations"],
    ["Summarize modeling, evaluation, or intervention design.", "Compare TargetOnly, ProxyOnly, AnchorOnly, transport baselines, Proposed variants."],
    ["Validation", "Stress tests"],
    ["Explain benchmarks, comparison groups, or review procedures.", "Sweep target budget, dimension, number of sources, sparsity, and nonlinearity."],
    ["Impact", "IHDP benchmark"],
    ["Connect the workflow to outcomes, deployment, or next steps.", "Real covariate distributions with semi-synthetic outcomes over 50 realizations."],
  ];
  for (const [oldText, newText] of replacements) {
    const shape = findByText(slide, oldText);
    if (shape) setText(shape, newText, { bold: ["Synthetic RCTs", "Ablations", "Stress tests", "IHDP benchmark"].includes(newText) });
  }
}

// Slide 8 — cut (0ms); within evidence act, aggregate results
{
  const slide = slides[7];
  addTalkHeader(slide, "Synthetic summary: proposed methods dominate the ranking table", "8:30-10:00", 36);
  setTransition(slide, "none", 0);
  clearContentPlaceholder(slide);
  claim(slide, "Across synthetic sweeps, Proposed is rank 1 on PEHE, ATE, Spearman, and regret; Proposed-CF leads calibration.");
  ctx.addText(slide, { left: 110, top: 192, width: 500, height: 24, text: "Average rank across performance metrics (lower is better)", fontSize: 19, color: TEXT, bold: true });
  [
    ["Proposed", 1.3, GREEN],
    ["Proposed-CF", 1.8, BLUE],
    ["Proposed-B†", 3.3, GOLD],
    ["OM-Transport", 4.2, "#9A9A9A"],
    ["IPW-Transport", 5.0, "#B9B9B9"],
    ["TargetOnly", 6.0, "#D0D0D0"],
    ["ProxyOnly", 8.5, RED],
  ].forEach(([label, value, color], i) => metricRow(slide, 246 + i * 44, label, value, 9, color));
  statCard(slide, 980, 238, 190, "Proposed avg rank", "1.3", "PEHE/ATE/rank/regret", GREEN);
  statCard(slide, 980, 394, 190, "Proposed-CF", "1.3", "ECE rank (calibration)", BLUE);
  ctx.addText(slide, {
    left: 110, top: 548, width: 860, height: 18,
    text: "† AnchorOnly (avg rank ≈6.5, ablation) and EntropyBal (≈5.5) omitted for space — full 9-method comparison in Table I",
    fontSize: 12, color: MUTED,
  });
}

// Slide 9 — cut (0ms); within evidence act, zooming into finite-sample regime
{
  const slide = slides[8];
  addTalkHeader(slide, "Small target samples are where transfer pays off", "10:00-11:15", 37);
  setTransition(slide, "none", 0);
  clearContentPlaceholder(slide);
  claim(slide, "When p is large and target labels are scarce, target-only learning deteriorates while anchored transfer stays usable.");
  statCard(slide, 82, 218, 310, "p=100, target 150/100", "7.57 -> 1.71", "TargetOnly PEHE to Proposed", GREEN);
  statCard(slide, 430, 218, 310, "p=50, target 150/100", "4.75 -> 0.73", "TargetOnly PEHE to Proposed", GREEN);
  statCard(slide, 778, 218, 310, "p=20, target 150/100", "2.60 -> 0.50", "TargetOnly PEHE to Proposed-CF", BLUE);
  ctx.addShape(slide, { left: 82, top: 398, width: 1006, height: 112, geometry: "roundRect", fill: SOFT, line: ctx.line(LINE, 1) });
  ctx.addText(slide, {
    left: 112,
    top: 424,
    width: 946,
    height: 58,
    text: "Talk move: show this slide as the finite-sample reason for the method. The estimator is not just theoretically neat; it is strongest where target IPD is most expensive.",
    fontSize: 21,
    color: TEXT,
    bold: true,
  });
}

// Slide 10 — fade (500ms); argument pivot: connected → disconnected regime
{
  const slide = slides[9];
  addTalkHeader(slide, "Disconnected targets: useful, but label the assumption", "11:15-12:30", 37);
  setTransition(slide, "fade", 500);
  clearContentPlaceholder(slide);
  claim(slide, "With m1=0, Proposed-B is best or near-best on PEHE, but the estimand is transported rather than identified.");
  groupedBars(
    slide,
    [
      { p: 10, proxy: 2.34, proposed: 1.63 },
      { p: 20, proxy: 3.37, proposed: 1.95 },
      { p: 50, proxy: 5.78, proposed: 3.25 },
      { p: 100, proxy: 8.21, proposed: 4.05 },
    ],
    72,
    198,
    704,
    346,
  );
  card(slide, {
    x: 824,
    y: 222,
    w: 340,
    h: 272,
    eyebrow: "A6",
    title: "Screen-then-transport",
    body: "Use target placebo to detect compatible sources, then transport source CATEs. This supports scenario analysis, not nonparametric identification.",
    accent: MAROON,
    fill: SOFT,
  });
}

// Slide 11 — fade (500ms); validation pivot: synthetic → real-data evidence
{
  const slide = slides[10];
  addTalkHeader(slide, "IHDP benchmark: real covariate shift tells the same story", "12:30-13:45", 36);
  setTransition(slide, "fade", 500);
  clearContentPlaceholder(slide);
  claim(slide, "On real IHDP covariates with known counterfactuals, the method remains best or competitive across connected and disconnected regimes.");
  card(slide, {
    x: 82,
    y: 210,
    w: 500,
    h: 268,
    eyebrow: "Connected",
    title: "Proposed is best in 9/9 PEHE cells",
    body: "Example: at m0=25, m1=100, PEHE is 1.57 for Proposed vs 2.05 for OM-Transport and 3.09 for TargetOnly.",
    accent: GREEN,
  });
  card(slide, {
    x: 636,
    y: 210,
    w: 500,
    h: 268,
    eyebrow: "Disconnected",
    title: "Lowest PEHE at all placebo budgets",
    body: "At m0=25, PEHE is 2.11 for Proposed-B vs 2.28-2.82 for transport/proxy baselines. Interpret under the working transport condition.",
    accent: BLUE,
    titleSize: 20,
  });
}

// Slide 12 — fade (700ms); act break: evidence → takeaways. Pill adjusted +1s: 13:46
{
  const slide = slides[11];
  setText(findByText(slide, "Thank you"), "Takeaways", { fontSize: 42, color: "#FFFFFF", bold: true, typeface: "Aptos Display" });
  setText(findByText(slide, "Questions?"), "Questions?", { fontSize: 34, color: GOLD, bold: true, typeface: "Aptos Display" });
  setText(findContains(slide, "Presenter name"), "Zilong Wang\nGeorgia Institute of Technology\nzwang937@gatech.edu", { fontSize: 23, color: "#FFFFFF" });
  ctx.addText(slide, {
    left: 72,
    top: 410,
    width: 480,
    height: 175,
    text: "Anchor to the target placebo arm.\nSeparate identified from transported claims.\nEvaluate decisions, not only error.",
    fontSize: 24,
    color: "#FFFFFF",
    bold: true,
  });
  timePill(slide, "13:46-15:00", 322, 626);
  setTransition(slide, "fade", 700);
}

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(layoutDir, { recursive: true });

const previewPaths = [];
for (let index = 0; index < slides.length; index += 1) {
  const padded = padSlideNumber(index + 1);
  const slide = slides[index];
  const previewPath = path.join(previewDir, `slide-${padded}.png`);
  const preview = await presentation.export({ slide, format: "png", scale: 1 });
  await saveBlobToFile(preview, previewPath);
  previewPaths.push(previewPath);
  const layout = await presentation.export({ slide, format: "layout" });
  await saveBlobToFile(layout, path.join(layoutDir, `slide-${padded}.layout.json`));
}

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(finalPptx);

const stat = await fs.stat(finalPptx);
await fs.writeFile(
  path.join(outputDir, "build-manifest.json"),
  `${JSON.stringify({ finalPptx, bytes: stat.size, previewPaths }, null, 2)}\n`,
  "utf8",
);

console.log(JSON.stringify({ finalPptx, bytes: stat.size, slideCount: slides.length, previewDir }, null, 2));
