<!-- origin: shimo4228 -->
<!-- rationale: ADR-0018 + ADR-0035 — skill 群が import する Scaffold Dissolution のローカル正本だけを常駐 -->
<!-- review-when: import 元 skill が消えた時 / substrate が knowledge cycle を native 化した時 / モデル世代交代時 -->
# AKC Rules (local edition)

6 phase の手順は各 skill が持つ。skill 未導入環境向けの自己完結版は AKC repo が正本。

## Scaffold Dissolution

rule は足場であり、実践が自然に回るようになれば簡素化・削除する。

- **Inward** — 原則が会話パターンに吸収された
- **Downward** — substrate が capability を native に持ち、手書き rule が古い既定を上書きする

モデル世代交代も downward のトリガー。旧世代向けの禁止・網羅的手順・反復強調は
skill: `generation-audit` で再監査する。

## ADR も足場である（2026-08-14 著者指示）

ADR はその時点の一時的判断の記録であって、恒久的な拘束ではない。新しいアイデアや
観測が既存 ADR と衝突するとき、ADR を理由にアイデアを狭めない — supersede が正常系。
これは公理 Emptiness（全 directive は文脈依存の guideline であり固定した本質を持たない）
の適用でもある。記録は残し、判断は上書きする。初期コンセプト・初期構造にも同じことが
言える: プロジェクトの発展を初期の足場が阻害し始めたら、足場の方を溶かす。
