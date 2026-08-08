# ADR-0004: documentation.md ルール退役

## Status
accepted

## Date
2026-03-13

## Context

`rules/common/documentation.md` は以下の2つの役割を担っていた:
1. CLAUDE.md メンテナンスのガイドライン（更新タイミング、提案の仕方）
2. 外向けドキュメント（README, 記事, プロフィール）の品質基準

このルールの内容は context-sync スキルの導入により、ドキュメント鮮度チェックが自動化された。また、外向けドキュメントの品質基準は article-writing スキルと重複していた。

## Decision

`rules/common/_archived/documentation.md` に移動して退役とした。

- CLAUDE.md メンテナンス → context-sync スキルが自動検出
- 外向けドキュメント基準 → article-writing スキルがカバー

## Alternatives Considered

- **そのまま残す** — context-sync と重複し、どちらが正かわからなくなる
- **削除する** — 退役理由が追跡できなくなる

## Consequences

- rules/ のコンテキストウィンドウ消費が減少
- context-sync が CLAUDE.md 鮮度の正式な担当になった
- _archived/ に残すことで、過去の方針を参照可能
