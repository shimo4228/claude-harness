# Inspiration / Origin

This file records the canonical implementation that originated the `jsonld-knowledge-graph` pattern. Kept separate from `SKILL.md` so the skill stays portable to other projects that don't share this origin context.

## Origin

Pattern emerged in May 2026 while building per-line `graph.jsonld` files for the `shimo4228` research ecosystem (`agent-knowledge-cycle` / `agent-attribution-practice` / `contemplative-agent`). The hub repo `shimo4228/shimo4228` already had a `graph.jsonld` encoding inter-line sibling relationships; the per-line implementation work surfaced 9 reusable design moves that became this skill.

## Canonical implementation

| Repo | URL | What its graph.jsonld encodes |
|---|---|---|
| Hub | https://github.com/shimo4228/shimo4228 | 3 ResearchLine + 11 EcosystemRepo + 7 Concept + 4 ExternalReference; sibling-not-dependency structure |
| AKC | https://github.com/shimo4228/agent-knowledge-cycle | 6 Phase + 3 MemoryLayer + 9 ADR + 6 EcosystemRepo + 14 Concept; bijective phase ↔ skill binding via `implements` |
| AAP | https://github.com/shimo4228/agent-attribution-practice | 4 Quadrant + 3 ProhibitionLevel + 2 Phase + 10 ADR + 6 Concept; Quadrant × ADR matrix via `appliesTo`, ProhibitionLevel hierarchy via `realizedBy` |
| Contemplative Agent | https://github.com/shimo4228/contemplative-agent | 4 Axiom + 3 MemoryLayer + 8 ADR + 6 Concept + 3 EcosystemRepo; approval-gate chain via `gatedBy`, cross-line bridge to AAP via `appliesTo` (ADR-0033) |

Concept DOIs (always parent records, used as ResearchLine `@id`):
- AKC: `10.5281/zenodo.19200726`
- Contemplative Agent: `10.5281/zenodo.19212118`
- AAP: `10.5281/zenodo.19652013`

Shared vocab namespace:
- `https://shimo4228.github.io/shimo4228/vocab#`

All four graphs share `@id` URIs for `MemoryLayer` (3 layers), `EcosystemRepo` (per-repo URLs), and umbrella `Concept` nodes (`six-phase-loop`, `three-layer-structure`, `four-business-ai-quadrants`, `four-contemplative-axioms`, `prohibition-strength-hierarchy`, `security-by-absence`, `scaffold-dissolution`). LLMs crawling all four see triples merge automatically.

## Commit references

Pattern shipped in:
- Hub: `eb09838` (initial graph), `0fe2be9` (root Dataset + Graph-first reading order)
- AAP: `6bc03de`
- Contemplative Agent: `7f0d589`
- AKC: `4135093`

Skill formalization shipped after these (this file).

## Why moved out of SKILL.md

Per shimo4228 skill portability rule (`~/.claude/rules/common/skills.md`):

> 個人プロジェクト URL を本文に埋め込まない: 自分の canonical implementation、個人 repo、特定プロジェクト内のパスへの link は、skill を一人のユーザの filesystem / 一つのプロジェクトのライフサイクルに縛るため、本文に入れない
>
> 具体例・origin story の置き場所:
> - 個人プロジェクト参照・origin story・canonical implementation → `inspiration.md`、ADR Notes、memory、または同一 repo 内の "Related Projects" ファイルへ

This file is the inspiration.md that the rule prescribes.
