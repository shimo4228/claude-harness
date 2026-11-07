# ADR-0003: 正規表現から LLM 分類への転換

## Status
accepted

## Date
2026-03-20

## Context

skill-comply（行動遵守率計測ツール）の開発中、ツールコール列の「意味」を分類するために正規表現を使い、繰り返し失敗した。

根本原因を分析した結果、ハーネス内の複数の情報源が「deterministic（正規表現）優先」を過剰に強化していた:
- testing.md の Verification Priority セクション
- eval-harness スキル
- regex-vs-llm-structured-text スキル

これらが「まず regex、LLM は最後の手段」というバイアスを形成し、意味的判断が必要な場面でも regex に固執する行動パターンを生んでいた。

## Decision

1. **skill-comply の分類エンジンを LLM ベースに全面移行**
2. **バイアス源の除去**: testing.md の Verification Priority セクション削除、regex-vs-llm スキルを DISABLED 化
3. **判断基準の明文化**: 構造的マッチング（形式・パターン）→ regex、意味的分類（行動・意図）→ LLM

## Alternatives Considered

- **regex パターンを洗練する** — 何度も試行して失敗。意味の判定は構造的マッチングでは本質的に不可能
- **ハイブリッド（regex + LLM fallback）** — 複雑さが増すだけで、regex が誤分類する「自信を持った間違い」が残る
- **バイアス源を残して skill-comply だけ修正** — 同じ問題が他のツールで再発する

## Consequences

- skill-comply の分類精度が大幅に向上
- LLM API コスト（分類に Haiku を使用）が発生するが、精度と引き換えに許容範囲
- 「regex vs LLM」の判断基準が feedback memory に記録され、将来の類似判断に活用可能
- ハーネス内の「deterministic 優先」バイアスが緩和された
