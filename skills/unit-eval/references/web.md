# unit-eval — web products

How to write and pin a check when the product is a web page or app. The SKILL.md steps apply
unchanged.

## Runner

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

- Lines from per-character boxes, as `../../detail-review/references/web.md` (Measuring) describes.
- Focus a link with `page.focus()`: Safari's Tab skips links unless the reader turns that on.
- Under text zoom, set the root font size to 200% and read `scrollWidth`.
