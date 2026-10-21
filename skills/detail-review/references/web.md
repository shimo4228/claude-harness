# detail-review — web products

The measuring setup for a web page or app. The SKILL.md steps apply unchanged; this file fills in
how a reviewer renders and measures.

## Rendering

- Playwright at the widths of step 1, light and dark, with `reducedMotion: 'reduce'` for layout
  measurements (animations move positions) and `no-preference` for motion findings.
- Each engine the users have: `chromium.launch({ channel: 'chrome' })` uses the installed Chrome and
  the machine's own fonts; `webkit.launch()` stands in for Safari and iPhone. A finding seen in one
  engine only is checked in the other before it is adopted.
- A copy of `dist/` outside the repo with a small static server, so the reviewer has no `eval/`.

## Measuring

- Per-character boxes with `Range.getClientRects()`, grouped into lines by their top. In WebKit a
  line's first character can also come back as a zero-width box at the previous line's end; use the
  box with ink.
- The fonts actually used for a node: CDP `CSS.getPlatformFontsForNode` (Chromium only). A finding
  that rests on a fallback font is about a page the users do not see.
- A fix is checked by injecting it (`page.addStyleTag`, a DOM change) and measuring again.

## The author's screen

When the review machine lacks the author's fonts or browser, take screenshots where the author reads
(the installed Chrome or WebKit on the author's Mac, at the widths of step 1, light and dark). Safari
is a separate engine from Chrome: a page reviewed only in Chrome is not reviewed for Safari.
