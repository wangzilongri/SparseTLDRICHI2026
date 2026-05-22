# Slide QA Rules

Future presentation edits should check these rules before delivery.

## Slide-face content

- Remove meta-commentary from visible slides: no "do this", "what to say", "talk move", "we should present", "speaker should", or process instructions on the slide face.
- Speaker guidance belongs in `SLIDE_RATIONALE.md`, presenter notes, or handoff docs, not in visible slide text.
- Titles should be claims or clean section labels, not editing instructions.
- Do not rely on white rectangles or overlays to hide stale text. Covered text can remain in the PPTX XML, notes, selection pane, accessibility text, or later exports. Delete stale text shapes before drawing replacements.
- After repair passes, scan the PPTX internals for forbidden phrases and old titles, not just the rendered PNG previews.

## Layout

- Check for text spilling outside cards, charts, tables, timing pills, or image bounds.
- Check for image/text overlap, especially after replacing template placeholders.
- Re-render previews after every build-script change; do not trust stale PNGs.
- Inspect both thumbnail/contact-sheet scale and full-size slides.

## Equations

- Prefer short, render-safe equations on main slides.
- Avoid dense theorem statements on main slides; move them to appendix.
- Final deck math must use proper equation rendering for variables and Greek letters. Do not leave ASCII fallbacks such as `sqrt(n0)`, `epsilon_tau`, `mu0_anchor`, `delta_hat`, `psi`, or `tau_hat` on visible slides.
- Use Office-native equation rendering when available. If the build environment cannot create native Office equations reliably, generate transparent PNG/SVG equation assets from LaTeX-style or SVG math source and place those assets on the slide.
- Verify equation boxes visually after rendering; formulas must be readable and not clipped.

## Results-arc caution

- Results slides should state audience-facing claims only. Avoid wording that describes presentation strategy, such as "first show", "use this as", "what the results need to prove", "opening evidence", "honest limitation", or "main discipline".
- When replacing a results slide, clear the old text layer first, then redraw the final slide content. The `repair_results_arc.mjs` pass uses this pattern on slides 05 and 07-11.
- QA the final deck in two ways: rendered PNG review for visual collisions, and PPTX XML text scan for hidden meta-commentary and ASCII math fallbacks.
