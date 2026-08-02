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
