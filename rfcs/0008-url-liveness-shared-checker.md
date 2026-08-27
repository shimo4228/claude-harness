---
state: done 2026-08-27
---
## Summary

URL 到達性（liveness）検査の共通部品を新設する — skill-stocktake / context-sync / paper-ecosystem の 3 箇所が要求しているが、既存 evidence script のどれも持たない。

## Motivation

2026-08-26 sweep で、URL の live check を要求する検査が 3 skill に散在すると判明した: skill-stocktake L126（参照 URL の stale 判定）、context-sync L267（`curl -sI` による 200 確認）、paper-ecosystem L291（DOI / arXiv / URL の実在）。既存 script（adr_lint / readme_evidence / citation_audit / graph_lint / geo_check / scan_refs / harness_lint）はいずれも URL 到達性を持たない。各所で個別実装すると rate limit 対応・リダイレクト解釈・偽陰性（bot 拒否 403）の扱いが drift する。

## Reference-level explanation

- 置き場: 消費者が複数 skill に跨るため `~/.claude/scripts/` 直下の共有 utility とするか、最初の消費者（RFC-0006 context-sync）配下に置いて後で昇格するかは実装セッションが search-first（既存 link checker: lychee / linkchecker 等の外部ツール照合を含む）後に決め、判断を ADR に残す
- 契約: URL リストを受け取り JSON（url / status / verdict: live・dead・blocked・skip）を返す evidence モード。判定しない・exit 0
- **rate limit は policy signal として扱う**（rules/common/debugging.md）— burst せず、連発時は停止して報告する設計を必須とする
- 403 / bot 拒否は dead と区別する（cited-source-mirror-verification L61 の既知パターン）
- offline 環境では全件 skip を返し、呼び出し側の evidence に「未検証」として載る

## Status

done — S1 build セッションで `skills/skill-health/scripts/url_liveness.py` として実装（リダイレクト非追跡・rate limit 停止報告型・内部 host skip）、main へ merge（239f066、ADR-0052）。2026-08-27
