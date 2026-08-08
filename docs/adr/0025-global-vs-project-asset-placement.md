# ADR-0025: Global vs Project の資産配置基準を rules/common/skills.md に正本化

## Status
accepted

## Date
2026-07-27

## Context

skill / agent / rule を global（`~/.claude/`）と project（`<repo>/.claude/`）のどちらに置くかの基準が、3 箇所に分散して暗黙化していた:

- **ADR-0008** — 「グローバルには言語非依存 + Python スキルのみ保持」（ECC 取り込みの文脈に限定）
- **learn-eval skill** — 「2+ プロジェクトで有用なら Global、迷ったら Global」（learned パターンに限定）
- **writing-ecosystem skill** — Ecosystem Map の Overlay 行「プラットフォーム固有ルールは `<project>/.claude/rules/`」（執筆系に限定）

いずれも自ドメイン内の記述であり、資産クラス横断の配置基準を正面から定めた文書がなかった。zenn-content で `zenn-clarity-reviewer` agent（Zenn/Dev.to 専用の初見読者明瞭性レビュアー、global `clarity-reviewer` の channel 版）を新設した際、project 配置の妥当性を判断する正本が無いことが顕在化した（ユーザー自身も「グローバルとプロジェクトに関連スキルやエージェントが散在していてルールが曖昧」と認識）。

## Decision

配置判定を `rules/common/skills.md` の Knowledge Placement 節に「Global vs Project」として正本化する:

- **2+ の repo / channel で使う** → global
- **単一 platform・channel・repo に固有** → project overlay
- **迷ったら global**（project へ後から降ろす方が逆より容易）

skill / agent / rule の全資産クラスに共通で適用する。分散していた 3 記述は削除せず、この基準の**実例**として位置づける（ADR-0008 は ECC 文脈、learn-eval は learned パターン、writing-ecosystem は執筆系 overlay）。learn-eval には正本ポインタを追記した。

適用実例（本 ADR 時点）:
- `editor` / `essay-reviewer` / `fact-checker` — Zenn・Substack・README 等の複数 channel で共有 → global（2026-04-18 昇格済み、基準と整合）
- `clarity-reviewer` — 学術論文用で複数研究 repo から使う → global
- `zenn-clarity-reviewer` / `devto-translator` — Zenn/Dev.to channel 専用 → project（zenn-content ADR-0004）

## Alternatives Considered

- **新しい常駐 rule ファイルを新設** — 常駐は希少資源（rules/README.md）。既存の Knowledge Placement 節が同じ関心事（知識の置き場所判定）を既に扱っており、追記で足りる。不採用。
- **project ADR のみに記録（zenn-content 側）** — 基準は harness 全体（全 repo・全資産クラス）に効くべきもので、単一 repo の ADR に置くと他 repo から発見されない。不採用。
- **文書化せず都度判断** — 今回まさに「曖昧」が顕在化した。documented-invariant を持たない構造的規約は確率的にしか守られない（patterns.md）。不採用。

## Consequences

- 配置判断に迷ったとき参照する正本が 1 箇所になる（常駐 rules 内なので毎セッション適用される）
- 既存資産の配置を再監査する根拠ができる（agent-stocktake / skill-stocktake が基準として参照可能）
- 「2+ repo / channel」の判定は将来変わりうる — project 資産が 2 つ目の repo で必要になった時点で global 昇格を検討する（zenn-content の editor 群昇格が前例）
- 分散 3 記述と正本の間で将来 drift しうるが、実例ポインタ化により基準本文の複製は避けた
