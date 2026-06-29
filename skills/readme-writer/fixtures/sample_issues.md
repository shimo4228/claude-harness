# Sample Project

[![b1](https://img.shields.io/badge/build-passing.svg)](https://ci.example.com)
[![b2](https://img.shields.io/badge/version-1.0.svg)](https://example.com)
[![b3](https://img.shields.io/badge/license-MIT.svg)](https://example.com)
[![b4](https://img.shields.io/badge/coverage-90.svg)](https://example.com)
[![b5](https://img.shields.io/badge/PRs-welcome.svg)](https://example.com)
[![b6](https://img.shields.io/badge/made-with-love.svg)](https://example.com)
[![b7](https://img.shields.io/badge/stars-lots.svg)](https://example.com)

## Overview

This file deliberately contains issues for `readme_lint` to catch. There is no
plain identity sentence between the H1 and this first section (identity_lead),
a badge wall above (badge_budget), a duplicate H1 below (single_h1), a skipped
heading level (heading_levels), an image with no alt text (alt_text), a broken
local link (local_link), a raster diagram that should be Mermaid
(raster_diagram_hint), and a DOI buried in a collapsible with no how-to-reference
affordance (details_floor_leak + doi_citation_pairing).

#### Buried subsection

This heading is H4 directly under an H2 — a skipped level (no H3 in between).

![](logo.png)

![system architecture](docs/architecture.png)

See the [missing design doc](docs/does-not-exist.md) for details.

<details>
<summary>Reference</summary>

DOI 10.5281/zenodo.1234567

</details>

# Duplicate Title
