# Slide Design Preferences

Derived by comparing `SS19_165_Wang.pptx` (hand-edited reference) against the
programmatically generated deck (`19_165_Wang.pptx` / `results-arc` pipeline).

---

## Naming

**Preferred:** `SS19_165_Wang.pptx`  
**Generated:** `19_165_Wang.pptx`

Use `SS19` as the session-ID prefix, not bare `19`.  The `SS` prefix makes the
session type unambiguous to conference organizers.

---

## Formatting compliance check

| Requirement | Status | Notes |
|---|---|---|
| File format `.pptx` | ✅ | |
| 16:9 slide size (1280×720 px) | ✅ | |
| Aptos Display — titles | ✅ | All title shapes explicit |
| Aptos — body | ✅ | Body text explicit; inherited theme text also fine |
| Authors + affiliation on cover | ✅ | Single-line: names + ISyE/GT |
| Session label on cover | ✅ | "Scientific Session 19 (Analytics Track), Paper ID 165" |
| Presenter marked | ⚠️ | No underline on "Zilong Wang" in hand-edited version; generated version had underline |
| Date/location on cover body | ⚠️ | Cover body lacks explicit date line; footer shows "June 1–3, 2026" (not June 3 specifically) |

Both warnings are minor. The guidelines ask for presenter identification and date; both are present in some form. Nothing blocks submission.

---

## Structural preferences

### 1. More slides, lower density per slide
The hand-edited deck has **19 main slides** vs 12 generated. The user prefers
spreading the argument across more slides rather than packing multiple ideas onto
one slide. Avoid slide-stuffing even when it looks "efficient."

### 2. Progressive reveal sequences
Core Idea slides 05–08 form a four-step progressive build:
- 05: placebo as calibration signal (diagram only)
- 06: proxy-gold paradigm (one DGP image + labels)
- 07: same title with the second figure added
- 08: scenarios panel added (third figure)

**Preference:** reveal content incrementally across consecutive slides rather than
showing everything at once.  Each slide should be one step in the story.

### 3. Embed actual figures, don't draw them programmatically
The generated deck drew motivation cards, pipeline steps, and theorem panels
using python-pptx rectangles and text boxes. The hand-edited deck embeds
**screenshots / exported PNG/JPEG figures** from the paper or analysis outputs
(677 KB, 659 KB, 687 KB, 736 KB, 825 KB images on content slides).

**Preference:** use actual rendered figures. Do not substitute programmatic shapes
for content that the paper already has as a figure. Code-drawn layouts are
acceptable only for structural chrome (header bar, footer, timing pill, dividers).

### 4. Split the pipeline into Stage 1 / Stage 2 (not a single 4-row table)
The generated deck had one slide (`build_slide05b.py`) with a 4-row MAROON-panel
layout covering all pipeline steps. The hand-edited deck splits this into:
- Slide 09: overview of the full pipeline (text + small formula PNGs)
- Slide 10: "Stage 1 — Anchor + Sparse Transfer" (detail)
- Slide 11: "Stage 2 — Doubly Robust CATE Estimation" (detail)

**Preference:** the two-layer structure (sparse correction → DR learner) gets
separate slides to match the paper's §3.1–3.3 division.

### 5. Equation images: small inline PNGs, not MAROON panel backgrounds
The generated deck placed equation PNG assets on full-width MAROON rectangles
(white-text-on-dark) to make transparent PNGs visible. The hand-edited deck uses
small (2–5 KB) inline PNG images at natural size within the slide content area,
without a colored panel background.

**Preference:** if equation images are white-text-on-transparent, re-export them
with a light or opaque background (or use dark-background inline blocks that fit
naturally in the slide layout, not full-width MAROON panels).

### 6. Results section is 5–6 slides, not 2–3
The generated deck compressed results into 2 slides. The hand-edited deck has:
- Slide 13: Evaluation setup
- Slide 14: Ablation & benchmark overview (PEHE table)
- Slide 15: Connected targets story (same table + takeaway card)
- Slide 16: Why the method helps (ablation comparators: TargetOnly / ProxyOnly / AnchorOnly / Proposed)
- Slide 17: Robustness (source scaling + A5 sensitivity + limits)
- Slide 18: IHDP benchmark

**Preference:** each distinct results claim gets its own slide. Do not compress
the "why it works" explanation and robustness into the same slide as the headline
PEHE numbers.

### 7. Cover slide: compact single-line session/author block
The generated cover had a 2-line expanded author block (names line + separate
affiliation line) plus a separate date/location textbox, all programmatically
placed. The hand-edited cover uses:
- One compact text block: `"Scientific Session 19 (Analytics Track), Paper ID 165"`
- One text block: names + affiliation on a single line
- No separate date textbox

**Preference:** keep the cover clean. One line for session info, one line for
authors + affiliation. Do not expand into multiple separate text boxes.

### 8. Background imagery on closing slide
The takeaways / "Questions?" slide (slide 19) uses a large background JPEG
(585×540 pt, 2.6 MB). The generated deck had a plain-background closing slide.

**Preference:** use a meaningful image (figure, conceptual diagram, or photo) as
a visual anchor on the closing slide.

### 9. Timing pills: 0:00–15:00 range (not 12:00)
All timing pills in the hand-edited deck run through 15:00 (e.g., slide 19 shows
`13:46-15:00`). The generated deck had pills up to 15:00 as well; a 12-minute
rescale was considered but not applied.

**Decision:** keep 0:00–15:00 range. The 15-minute slot is the full allocated
time including Q&A; pills covering the full slot are correct for speaker pacing.

---

## What to preserve from the generated deck

- Chrome template: MAROON top bar, GOLD accent stripe, footer with venue +
  timing pill, slide-number badge — all carried over correctly.
- Font stack: Aptos Display (titles), Aptos (body), Courier New (inline code).
- Color palette: MAROON `#7A0019`, GOLD `#D8AE4B`, MUTED `#5E5A56`, WHITE.
- Appendix structure: 30 slides appended after slide 19, with divider slide at
  position 20.
