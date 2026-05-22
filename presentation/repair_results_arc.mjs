import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

process.env.HOME ||= "C:/Users/wrait";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..");
const presentationSkillDir =
  process.env.PRESENTATIONS_SKILL_DIR ||
  "C:/Users/wrait/.codex/plugins/cache/openai-primary-runtime/presentations/26.430.10722/skills/presentations";
const {
  createSlideContext,
  ensureArtifactToolWorkspace,
  importArtifactTool,
  padSlideNumber,
  saveBlobToFile,
} = await import(pathToFileURL(path.join(presentationSkillDir, "scripts", "artifact_tool_utils.mjs")).href);

const workspace = path.join(repoRoot, "presentation");
const sourcePptx = path.join(workspace, "output", "transfer-learning-meta-analysis-ichi-2026-talk.repaired.pptx");
const outputDir = path.join(workspace, "output");
const previewDir = path.join(workspace, "preview-results-arc");
const finalPptx = path.join(outputDir, "transfer-learning-meta-analysis-ichi-2026-talk.results-arc.pptx");
const equationDir = path.join(workspace, "assets", "equations");

const MAROON = "#8A0020";
const GOLD = "#D5A834";
const BLUE = "#6F8EA4";
const GREEN = "#7B8F70";
const RED = "#B3414A";
const TEXT = "#2B2B2B";
const MUTED = "#65605C";
const SOFT = "#F7F5F2";
const LINE = "#DED8D1";

function equationSvg({ width, height, color = "#FFFFFF", lines, fontSize = 24 }) {
  const family = "Cambria Math, STIX Two Math, Times New Roman, serif";
  const lineGap = Math.round(fontSize * 1.25);
  const startY = Math.round((height - lineGap * (lines.length - 1)) / 2 + fontSize * 0.34);
  const text = lines
    .map((line, index) => `<text x="0" y="${startY + index * lineGap}" fill="${color}" font-family="${family}" font-size="${fontSize}" font-weight="600">${line}</text>`)
    .join("");
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${text}</svg>`;
}

async function writeEquationPng(name, options) {
  const out = path.join(equationDir, `${name}.png`);
  return out;
}

await fs.mkdir(equationDir, { recursive: true });
const equationAssets = {
  sourceProxy: await writeEquationPng("source-proxy", {
    width: 420,
    height: 76,
    fontSize: 34,
    lines: [
      'μ̂<tspan baseline-shift="sub" font-size="17">0</tspan><tspan baseline-shift="super" font-size="15">proxy</tspan>(x),',
      'μ̂<tspan baseline-shift="sub" font-size="17">1</tspan><tspan baseline-shift="super" font-size="15">proxy</tspan>(x)',
    ],
  }),
  targetAnchor: await writeEquationPng("target-anchor", {
    width: 420,
    height: 58,
    fontSize: 34,
    lines: ['Y<tspan baseline-shift="sub" font-size="17">0</tspan> − μ̂<tspan baseline-shift="sub" font-size="17">0</tspan><tspan baseline-shift="super" font-size="15">proxy</tspan>(X)'],
  }),
  sparseCorrection: await writeEquationPng("sparse-correction", {
    width: 420,
    height: 76,
    fontSize: 34,
    lines: [
      'μ̂<tspan baseline-shift="sub" font-size="17">0</tspan><tspan baseline-shift="super" font-size="15">anchor</tspan>(x)',
      '= μ̂<tspan baseline-shift="sub" font-size="17">0</tspan><tspan baseline-shift="super" font-size="15">proxy</tspan>(x) + δ̂(x)',
    ],
  }),
  drLearner: await writeEquationPng("dr-learner", {
    width: 420,
    height: 76,
    fontSize: 32,
    lines: [
      'ψ<tspan baseline-shift="sub" font-size="17">i</tspan> = μ̂<tspan baseline-shift="sub" font-size="17">1</tspan>(X<tspan baseline-shift="sub" font-size="17">i</tspan>) − μ̂<tspan baseline-shift="sub" font-size="17">0</tspan><tspan baseline-shift="super" font-size="15">anchor</tspan>(X<tspan baseline-shift="sub" font-size="17">i</tspan>)',
      '+ IPW residual',
    ],
  }),
  connectedTheorem: await writeEquationPng("connected-theorem", {
    width: 310,
    height: 42,
    color: "#2B2B2B",
    fontSize: 18,
    lines: ['√n<tspan baseline-shift="sub" font-size="13">0</tspan>(τ̂<tspan baseline-shift="sub" font-size="13">DR</tspan>(x) − τ<tspan baseline-shift="sub" font-size="13">0</tspan>(x)) ⇒ N(0,V(x))'],
  }),
  disconnectedTheorem: await writeEquationPng("disconnected-theorem", {
    width: 312,
    height: 58,
    color: "#2B2B2B",
    fontSize: 17,
    lines: [
      '||τ̂<tspan baseline-shift="sub" font-size="12">B</tspan> − τ<tspan baseline-shift="sub" font-size="12">0</tspan>|| ≤ estimation + ε<tspan baseline-shift="sub" font-size="12">τ</tspan>',
      '+ O<tspan baseline-shift="sub" font-size="12">p</tspan>(η<tspan baseline-shift="super" font-size="12">1/2</tspan>)',
    ],
  }),
};

await ensureArtifactToolWorkspace(workspace);
const artifact = await importArtifactTool(workspace);
const { FileBlob, PresentationFile } = artifact;
const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePptx));
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

function deleteTextContaining(slide, terms) {
  for (const shape of textShapes(slide)) {
    const text = textOf(shape);
    if (terms.some((term) => text.includes(term))) {
      shape.delete();
    }
  }
}

function clearVisibleText(slide) {
  for (const shape of textShapes(slide)) {
    shape.delete();
  }
}

function coverContent(slide, top = 140, height = 470) {
  ctx.addShape(slide, {
    left: 54,
    top,
    width: 1172,
    height,
    fill: "#FFFFFF",
    line: ctx.line("#00000000", 0),
    name: "repair-cover",
  });
}

function replaceTitle(slide, text) {
  ctx.addShape(slide, {
    left: 58,
    top: 38,
    width: 930,
    height: 100,
    fill: "#FFFFFF",
    line: ctx.line("#00000000", 0),
    name: "repair-title-cover",
  });
  ctx.addText(slide, {
    left: 72,
    top: 54,
    width: 900,
    height: 84,
    text,
    fontSize: 31,
    color: MAROON,
    bold: true,
    typeface: "Aptos Display",
    name: "repair-title",
  });
}

function claim(slide, text, y = 150) {
  ctx.addText(slide, {
    left: 72,
    top: y,
    width: 1040,
    height: 44,
    text,
    fontSize: 18,
    color: TEXT,
    bold: true,
    name: "repair-claim",
  });
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
    name: "repair-timing-pill",
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
    name: "repair-timing-label",
  });
}

function card(slide, { x, y, w, h, eyebrow, title, body, accent = GOLD, fill = "#FFFFFF", titleSize = 20, bodySize = 16 }) {
  ctx.addShape(slide, { left: x, top: y, width: w, height: h, geometry: "roundRect", fill, line: ctx.line(LINE, 1) });
  ctx.addShape(slide, { left: x, top: y, width: w, height: 6, fill: accent, line: ctx.line("#00000000", 0) });
  if (eyebrow) {
    ctx.addText(slide, { left: x + 20, top: y + 24, width: w - 40, height: 20, text: eyebrow, fontSize: 17, color: MAROON, bold: true });
  }
  ctx.addText(slide, { left: x + 20, top: y + (eyebrow ? 56 : 24), width: w - 40, height: 28, text: title, fontSize: titleSize, color: TEXT, bold: true });
  ctx.addText(slide, { left: x + 20, top: y + (eyebrow ? 96 : 64), width: w - 40, height: h - (eyebrow ? 112 : 80), text: body, fontSize: bodySize, color: MUTED });
}

function statCard(slide, x, y, w, label, value, sub, color = MAROON) {
  ctx.addShape(slide, { left: x, top: y, width: w, height: 132, geometry: "roundRect", fill: "#FFFFFF", line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: x + 20, top: y + 18, width: w - 40, height: 26, text: label, fontSize: 16, color: MUTED, bold: true });
  ctx.addText(slide, { left: x + 20, top: y + 48, width: w - 40, height: 46, text: value, fontSize: 35, color, bold: true, typeface: "Aptos Display" });
  ctx.addText(slide, { left: x + 20, top: y + 94, width: w - 40, height: 26, text: sub, fontSize: 14, color: MUTED });
}

function compactBadge(slide, x, y, w, label, value, sub, color = MAROON) {
  ctx.addShape(slide, { left: x, top: y, width: w, height: 104, geometry: "roundRect", fill: "#FFFFFF", line: ctx.line(LINE, 1) });
  ctx.addShape(slide, { left: x, top: y, width: 6, height: 104, fill: color, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { left: x + 18, top: y + 16, width: w - 34, height: 22, text: label, fontSize: 15, color: MUTED, bold: true });
  ctx.addText(slide, { left: x + 18, top: y + 42, width: w - 34, height: 24, text: value, fontSize: 19, color, bold: true });
  ctx.addText(slide, { left: x + 18, top: y + 70, width: w - 34, height: 22, text: sub, fontSize: 13, color: MUTED });
}

function evidenceCard(slide, x, y, w, h, label, title, body, accent = BLUE) {
  ctx.addShape(slide, { left: x, top: y, width: w, height: h, geometry: "roundRect", fill: "#FFFFFF", line: ctx.line(LINE, 1) });
  ctx.addShape(slide, { left: x, top: y, width: w, height: 6, fill: accent, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { left: x + 18, top: y + 18, width: w - 36, height: 18, text: label, fontSize: 12, color: accent, bold: true });
  ctx.addText(slide, { left: x + 18, top: y + 42, width: w - 36, height: 28, text: title, fontSize: 18, color: TEXT, bold: true });
  ctx.addText(slide, { left: x + 18, top: y + 80, width: w - 36, height: h - 96, text: body, fontSize: 15, color: MUTED });
}

function simpleBar(slide, x, y, label, value, max, color, width = 330) {
  ctx.addText(slide, { left: x, top: y - 2, width: 150, height: 22, text: label, fontSize: 14, color: TEXT, bold: label.startsWith("Proposed") });
  ctx.addShape(slide, { left: x + 160, top: y, width, height: 18, geometry: "roundRect", fill: "#EEEAE5", line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { left: x + 160, top: y, width: Math.max(8, (value / max) * width), height: 18, geometry: "roundRect", fill: color, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { left: x + 160 + width + 12, top: y - 2, width: 54, height: 22, text: value.toFixed(2), fontSize: 14, color: TEXT, bold: label.startsWith("Proposed") });
}

function metricRow(slide, y, label, value, max, color) {
  const barX = 356;
  const barW = 520;
  ctx.addText(slide, { left: 122, top: y - 2, width: 200, height: 24, text: label, fontSize: 17, color: TEXT, bold: label.startsWith("Proposed") });
  ctx.addShape(slide, { left: barX, top: y, width: barW, height: 20, geometry: "roundRect", fill: "#EEEAE5", line: ctx.line("#00000000", 0) });
  ctx.addShape(slide, { left: barX, top: y, width: Math.max(8, (value / max) * barW), height: 20, geometry: "roundRect", fill: color, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, { left: barX + barW + 20, top: y - 3, width: 68, height: 24, text: value.toFixed(1), fontSize: 17, color: TEXT, bold: label.startsWith("Proposed") });
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

// Slide 05
{
  const slide = slides[4];
  clearVisibleText(slide);
  replaceTitle(slide, "Estimator pipeline: anchor first, orthogonalize second");
  coverContent(slide, 142, 472);
  claim(slide, "Two layers do the work: sparse baseline anchoring first, then doubly robust CATE learning.", 150);
  [
    ["1", "Source proxy", equationAssets.sourceProxy, "Fit source outcome models from abundant source IPD.", BLUE, 72, 52],
    ["2", "Target anchor", equationAssets.targetAnchor, "Target placebo outcomes provide gold residual labels.", GOLD, 360, 42],
    ["3", "Sparse correction", equationAssets.sparseCorrection, "Debias target baseline risk with a low-complexity correction.", MAROON, 648, 52],
    ["4", "DR learner", equationAssets.drLearner, "Fit τ̂(x) = E[ψ | x] for targeting and regret.", GREEN, 936, 52],
  ].forEach(([step, title, equationPath, body, color, x, eqHeight], i) => {
    ctx.addShape(slide, { left: x, top: 232, width: 238, height: 246, geometry: "roundRect", fill: color, line: ctx.line("#00000000", 0) });
    ctx.addText(slide, { left: x + 22, top: 260, width: 194, height: 22, text: `${step} ${title}`, fontSize: 16, color: "#FFFFFF", bold: true });
    ctx.addImage(slide, { path: equationPath, left: x + 18, top: 310, width: 202, height: eqHeight, fit: "contain", alt: `${title} equation` });
    ctx.addText(slide, { left: x + 22, top: 402, width: 194, height: 54, text: body, fontSize: 14, color: "#FFFFFF" });
    if (i < 3) ctx.addText(slide, { left: x + 246, top: 338, width: 30, height: 24, text: "->", fontSize: 24, color: MUTED, bold: true, align: "center" });
  });
  ctx.addShape(slide, { left: 174, top: 510, width: 930, height: 62, geometry: "roundRect", fill: SOFT, line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: 198, top: 526, width: 882, height: 30, text: "Bastani/Tian-Feng supply the sparse anchor; Kennedy supplies the orthogonal DR learner.", fontSize: 18, color: TEXT, bold: true, align: "center" });
}

// Slide 06
{
  const slide = slides[5];
  coverContent(slide, 146, 462);
  card(slide, {
    x: 72,
    y: 176,
    w: 356,
    h: 290,
    title: "Connected target",
    body: "Target has treated and placebo outcomes.\n\nClaim: identified target-site CATE.\n\nGuarantee: Theorem 1 gives a Neyman-orthogonal expansion:",
    accent: GOLD,
  });
  ctx.addImage(slide, { path: equationAssets.connectedTheorem, left: 92, top: 394, width: 298, height: 40, fit: "contain", alt: "Theorem 1 asymptotic normality equation" });
  card(slide, {
    x: 462,
    y: 176,
    w: 356,
    h: 290,
    title: "Disconnected target",
    body: "Target has placebo outcomes only.\n\nClaim: screen-then-transport working-model estimate.\n\nGuarantee: Theorem 2 separates error sources:",
    accent: BLUE,
  });
  ctx.addImage(slide, { path: equationAssets.disconnectedTheorem, left: 482, top: 386, width: 306, height: 57, fit: "contain", alt: "Theorem 2 transport error decomposition equation" });
  card(slide, {
    x: 852,
    y: 176,
    w: 356,
    h: 290,
    title: "Key distinction",
    body: "These are different claims.\n\nConnected = identified CATE.\n\nDisconnected = useful ranking and scenario analysis under explicit A6 transport assumptions.",
    accent: MAROON,
  });
  ctx.addShape(slide, { left: 1050, top: 620, width: 170, height: 42, fill: "#FFFFFF", line: ctx.line("#00000000", 0) });
  timePill(slide, "6:01-7:15");
}

// Slide 08
{
  const slide = slides[7];
  coverContent(slide, 140, 472);
  claim(slide, "Across synthetic sweeps, Proposed ranks first on PEHE, ATE, Spearman, and regret; Proposed-CF leads calibration.");
  ctx.addText(slide, { left: 110, top: 192, width: 500, height: 24, text: "Average rank across performance metrics (lower is better)", fontSize: 19, color: TEXT, bold: true });
  [
    ["Proposed", 1.3, GREEN],
    ["Proposed-CF", 1.8, BLUE],
    ["Proposed-B*", 3.3, GOLD],
    ["OM-Transport", 4.2, "#9A9A9A"],
    ["IPW-Transport", 5.0, "#B9B9B9"],
    ["TargetOnly", 6.0, "#D0D0D0"],
    ["ProxyOnly", 8.5, RED],
  ].forEach(([label, value, color], i) => metricRow(slide, 246 + i * 44, label, value, 9, color));
  statCard(slide, 980, 238, 190, "Proposed avg rank", "1.3", "PEHE/ATE/rank/regret", GREEN);
  compactBadge(slide, 980, 404, 190, "Calibration leader", "Proposed-CF", "best ECE rank", BLUE);
  ctx.addText(slide, { left: 110, top: 548, width: 860, height: 18, text: "* AnchorOnly (avg rank about 6.5, ablation) and EntropyBal (about 5.5) omitted for space; full 9-method comparison in Table I", fontSize: 12, color: MUTED });
}

// Slide 10
{
  const slide = slides[9];
  coverContent(slide, 140, 472);
  claim(slide, "With m1=0, screen compatible sources and transport under A6; useful for ranking, not identification.");
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
    body: "Use target placebo to detect compatible sources, then transport source CATEs.\n\nThis supports scenario analysis, not nonparametric identification.",
    accent: MAROON,
    fill: SOFT,
  });
}

// Slide 07: orient the audience before results
{
  const slide = slides[6];
  clearVisibleText(slide);
  replaceTitle(slide, "Evaluation setup");
  coverContent(slide, 140, 472);
  claim(slide, "Evaluation spans scarce target evidence, covariate shift, and two target-data regimes.");
  evidenceCard(slide, 72, 210, 340, 220, "REGIMES", "Two target settings", "Connected: target has treated and placebo outcomes.\n\nDisconnected: target has placebo only, so treated effects are transported under A6.", GOLD);
  evidenceCard(slide, 470, 210, 340, 220, "COMPARATORS", "What transfer is compared against", "TargetOnly tests no transfer.\nProxyOnly tests source transfer without anchoring.\nAnchorOnly isolates target-placebo correction.\nTransport baselines test weighting/outcome-model transfer.", BLUE);
  evidenceCard(slide, 868, 210, 340, 220, "METRICS", "What counts as success", "Accuracy: PEHE and ATE error.\nTargeting: Spearman and policy regret.\nTrust: CATE calibration slope, R2, and ECE.", GREEN);
  ctx.addShape(slide, { left: 178, top: 486, width: 924, height: 62, geometry: "roundRect", fill: SOFT, line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: 210, top: 503, width: 860, height: 28, text: "Anchoring, source scaling, and disconnected transport are evaluated separately.", fontSize: 17, color: TEXT, bold: true, align: "center" });
  timePill(slide, "7:15-8:30");
}

// Slide 08: first result should be finite-sample connected target, not average rank
{
  const slide = slides[7];
  clearVisibleText(slide);
  replaceTitle(slide, "Connected targets: transfer helps when labels are scarce");
  coverContent(slide, 140, 472);
  claim(slide, "In connected targets, target-placebo anchoring helps most when target labels are scarce and p is large.");
  ctx.addText(slide, { left: 92, top: 204, width: 720, height: 24, text: "PEHE at target budget m0=150, m1=100 (lower is better)", fontSize: 19, color: TEXT, bold: true });
  [
    { y: 258, p: "p=20", target: 2.60, proposed: 0.50, method: "Proposed-CF", color: BLUE },
    { y: 356, p: "p=50", target: 4.75, proposed: 0.73, method: "Proposed", color: GREEN },
    { y: 454, p: "p=100", target: 7.57, proposed: 1.71, method: "Proposed", color: MAROON },
  ].forEach((d) => {
    ctx.addText(slide, { left: 92, top: d.y - 8, width: 72, height: 26, text: d.p, fontSize: 18, color: MAROON, bold: true });
    simpleBar(slide, 178, d.y - 4, "TargetOnly", d.target, 8.5, "#CFCFCF", 390);
    simpleBar(slide, 178, d.y + 32, d.method, d.proposed, 8.5, d.color, 390);
  });
  evidenceCard(slide, 900, 250, 270, 210, "TAKEAWAY", "This is the deployment case", "The method is not just better on average. Its biggest gains appear where target IPD is expensive: small target trial, high dimension, shifted sources.", GOLD, "#FFFFFF");
  timePill(slide, "8:30-10:00");
}

// Slide 09: show the source of benefit before summary ranks
{
  const slide = slides[8];
  clearVisibleText(slide);
  replaceTitle(slide, "Why the method helps: anchor, then learn CATEs");
  coverContent(slide, 140, 472);
  claim(slide, "The gain is not generic pooling; it comes from anchoring source models to target placebo and then learning CATEs.");
  [
    ["TargetOnly", "no transfer", "High variance when target treated labels are scarce.", "#CFCFCF"],
    ["ProxyOnly", "transfer without anchor", "Low variance but biased under covariate shift.", RED],
    ["AnchorOnly", "target placebo correction", "Shows the baseline calibration contribution.", GOLD],
    ["Proposed / Proposed-CF", "anchor + DR learner", "Adds orthogonal CATE learning and calibration.", GREEN],
  ].forEach(([title, label, body, color], i) => {
    const x = 72 + i * 286;
    ctx.addShape(slide, { left: x, top: 230, width: 244, height: 210, geometry: "roundRect", fill: "#FFFFFF", line: ctx.line(LINE, 1) });
    ctx.addShape(slide, { left: x, top: 230, width: 244, height: 6, fill: color, line: ctx.line("#00000000", 0) });
    ctx.addText(slide, { left: x + 18, top: 258, width: 208, height: 26, text: title, fontSize: 17, color: TEXT, bold: true });
    ctx.addText(slide, { left: x + 18, top: 292, width: 208, height: 22, text: label, fontSize: 13, color, bold: true });
    ctx.addText(slide, { left: x + 18, top: 332, width: 208, height: 70, text: body, fontSize: 14, color: MUTED });
  });
  ctx.addShape(slide, { left: 184, top: 486, width: 912, height: 62, geometry: "roundRect", fill: SOFT, line: ctx.line(LINE, 1) });
  ctx.addText(slide, { left: 210, top: 503, width: 860, height: 28, text: "Average ranks summarize the pattern after the finite-sample gain is visible.", fontSize: 17, color: TEXT, bold: true, align: "center" });
  timePill(slide, "10:00-11:15");
}

// Slide 10: robustness and boundaries
{
  const slide = slides[9];
  clearVisibleText(slide);
  replaceTitle(slide, "Robustness: source diversity helps; violations degrade smoothly");
  coverContent(slide, 140, 472);
  claim(slide, "The method scales with source diversity and degrades smoothly when the sparse-shift approximation weakens.");
  evidenceCard(slide, 82, 212, 350, 250, "SOURCE SCALING", "More source sites help when target data are scarce", "Across C=2 to 50 source sites, Proposed stays around PEHE 0.84 -> 0.66 at m0=150, m1=100, while TargetOnly remains near 5.\n\nThe useful signal is source diversity plus target anchoring.", BLUE);
  evidenceCard(slide, 466, 212, 350, 250, "A5 SENSITIVITY", "Violations hurt, but not catastrophically", "When sparse linear shift holds, Proposed-CF is about 0.38 PEHE.\n\nAs sparsity and nonlinearity increase, PEHE rises gradually rather than collapsing.", GOLD);
  evidenceCard(slide, 850, 212, 350, 250, "LIMIT", "Sparse proxy-gold shifts matter", "The strongest gains occur in the intended sparse proxy-gold regime.\n\nDense or highly nonlinear corrections reduce performance.", MAROON);
  timePill(slide, "11:15-12:30");
}

// Slide 11: disconnected + IHDP as final evidence
{
  const slide = slides[10];
  clearVisibleText(slide);
  replaceTitle(slide, "IHDP benchmark: real covariate shift tells the same story");
  coverContent(slide, 140, 472);
  claim(slide, "Real covariate shift tells the same story, while disconnected targets must stay labeled as transport.");
  evidenceCard(slide, 82, 210, 500, 270, "CONNECTED IHDP", "Proposed is strongest under real covariate shift", "IHDP uses real baseline covariates and semi-synthetic outcomes.\n\nExample at m0=25, m1=100:\nProposed PEHE 1.57 vs OM-Transport 2.05 vs TargetOnly 3.09.", GREEN, "#FFFFFF");
  evidenceCard(slide, 636, 210, 500, 270, "DISCONNECTED IHDP", "Useful ranking, not target identification", "With m1=0, Proposed-B is competitive on PEHE and strong on ranking.\n\nExample at m0=25:\nProposed-B PEHE 2.11 vs transport/proxy baselines 2.28-2.82.\n\nAssumption: A6 transport.", BLUE, "#FFFFFF");
  ctx.addText(slide, { left: 92, top: 516, width: 1030, height: 28, text: "Connected estimates identified CATEs; disconnected analyses are transport-based.", fontSize: 18, color: TEXT, bold: true, align: "center" });
  timePill(slide, "12:30-13:45");
}

// Slide 12
{
  const slide = slides[11];
  for (const shape of textShapes(slide)) {
    const text = textOf(shape);
    if (
      text.includes("Anchor to the target placebo arm") ||
      text.includes("Separate identified from transported claims") ||
      text.includes("Evaluate decisions, not only error")
    ) {
      shape.delete();
    }
  }
  ctx.addShape(slide, { left: 50, top: 396, width: 450, height: 160, fill: MAROON, line: ctx.line("#00000000", 0) });
  ctx.addText(slide, {
    left: 72,
    top: 408,
    width: 360,
    height: 136,
    text: "Anchor to target placebo.\nSeparate identified from\ntransported claims.\nEvaluate decisions, not only error.",
    fontSize: 21,
    color: "#FFFFFF",
    bold: true,
  });
  ctx.addShape(slide, { left: 314, top: 620, width: 170, height: 42, fill: "#FFFFFF", line: ctx.line("#00000000", 0) });
  timePill(slide, "13:46-15:00", 322, 626);
}

await fs.mkdir(outputDir, { recursive: true });
await fs.mkdir(previewDir, { recursive: true });

const previewPaths = [];
for (let index = 0; index < slides.length; index += 1) {
  const padded = padSlideNumber(index + 1);
  const slide = slides[index];
  const previewPath = path.join(previewDir, `slide-${padded}.png`);
  const preview = await presentation.export({ slide, format: "png", scale: 1 });
  await saveBlobToFile(preview, previewPath);
  previewPaths.push(previewPath);
}

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save(finalPptx);

await fs.writeFile(
  path.join(outputDir, "repair-manifest.json"),
  `${JSON.stringify({ sourcePptx, finalPptx, previewDir, slideCount: slides.length, previewPaths }, null, 2)}\n`,
  "utf8",
);

console.log(JSON.stringify({ finalPptx, previewDir, slideCount: slides.length }, null, 2));
