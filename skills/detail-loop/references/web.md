# Web products

The setup for a web page or app. The review phase (`references/review.md`) and the freeze phase
(`references/freeze.md`) apply unchanged; this file fills in how to render, run, pin and measure.

## Rendering for review

- Playwright at the widths of the review's step 1, light and dark, with `reducedMotion: 'reduce'`
  for layout measurements (animations move positions) and `no-preference` for motion findings.
- Each engine the users have: `chromium.launch({ channel: 'chrome' })` uses the installed Chrome and
  the machine's own fonts; `webkit.launch()` stands in for Safari and iPhone. A finding seen in one
  engine only is checked in the other before it is adopted.
- A copy of `dist/` outside the repo with a small static server, so the reviewer has no `eval/`.

## Runner for frozen checks

Playwright over the built pages (`dist/`) served by a small static server, one check per unit id.
`chromium.launch({ channel: 'chrome' })` measures in the installed Chrome with the machine's fonts;
an engine switch (`EVAL_ENGINE=webkit` → `webkit.launch()`) runs the same checks in Safari's engine.
A check that needs CDP (fonts per node) runs in Chromium only; report it as skipped in WebKit.

## Pinning

- Viewport, colour scheme and `reducedMotion: 'reduce'` for layout checks; `no-preference` for checks
  about motion (a separate context).
- Fonts: Japanese line breaks, hanging punctuation and `halt`/`palt` depend on the font. Run where the
  author's fonts are installed (Hiragino on the author's Mac); a sandbox with a fallback font measures
  a different page.
- Scroll-driven animations update after the scroll is processed: wait with a short timeout per step,
  not two animation frames. Let load-in animations finish before the first measurement.

## Measuring

- Per-character boxes with `Range.getClientRects()`, grouped into lines by their top. In WebKit a
  line's first character can also come back as a zero-width box at the previous line's end; use the
  box with ink.
- The fonts actually used for a node: CDP `CSS.getPlatformFontsForNode` (Chromium only). A finding
  that rests on a fallback font is about a page the users do not see.
- A reviewer's fix is checked by injecting it (`page.addStyleTag`, a DOM change) and measuring again.
- Focus a link with `page.focus()`: Safari's Tab skips links unless the reader turns that on.
- Under text zoom, set the root font size to 200% and read `scrollWidth`.

## The author's screen

When the review machine lacks the author's fonts or browser, take screenshots where the author reads
(the installed Chrome or WebKit on the author's Mac, at the widths of the review's step 1, light and
dark). Safari is a separate engine from Chrome: a page reviewed only in Chrome is not reviewed for
Safari.
