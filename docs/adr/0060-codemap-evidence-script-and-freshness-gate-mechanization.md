# ADR-0060: codemap の freshness gate と header 検収を evidence script へ降ろし、codemap-writer chain を意味的チェック専任に薄化

## Status

accepted

## Date

2026-09-01

## Context

codemap chain（`update-codemaps` skill + `codemap-writer` agent）の機械検査は、skill 本文に
インライン shell として埋まっていた — step 2 の freshness gate（header から `Source` sha を
sed で抜き、`git rev-list --count` で behind を数える）と step 5 の produced 検収
（`case` 文で header を目視パターン照合）。この形には実害の記録が既に 2 件ある:
zsh の word splitting で pathspec が潰れ behind=0 に化ける罠（2026-08-17 実測、skill 本文が
長文で警告していた）と、mtime 判定が stale codemap を fresh と報告した事故
（contemplative-agent `728f6d6`）。LLM が毎回 shell 断片を転記して実行する構造は、
この種の罠を「本文の警告文」でしか防げない。

/review-to-lint（[ADR-0051](./0051-extract-mechanical-adr-checks-into-cross-repo-lint.md) の
水平展開、台帳は RFC-0005）を codemap-writer に適用した。RFC-0005 の 12+3 候補に codemap 系は
無く、著者の明示指示（2026-09-01）が発火条件。

免除境界の実測（2026-09-01、docs/CODEMAPS/ を持つ全 10 repo / 24 ファイル）:
**現行 spec（`Source:` sha + `Tokens:`）準拠の header は 0 件**。実態は `Token estimate:`
表記・`Updated:` 継ぎ足し鎖（contemplative-agent architecture.md は 8 本、token 主張は実測比
57% drift）・prose 値の `Files scanned:`・header 無し（doctrine-corpus、gai-passport-ios）。
spec は agent 定義に後から入り、corpus は一度も再生成されていない。既存全 corpus に厳格 gate を
当てれば初日に全滅する。

search-first 照合: context-sync の `context_checks.py` は CODEMAPS の prose 照合
（graph.jsonld / llms.txt との突合）のみで freshness header は検査しない — 重複なし。
header 形式は harness 固有仕様なので既製 lint ツールの照合は不要と判断（自明却下）。

## Decision

1. `skills/update-codemaps/scripts/codemap_evidence.py` を新設する（uv sub-project、
   pytest 11 本）。既定は evidence モード — JSON 出力・判定しない・exit 0
   （`adr_lint.py` / `readme_evidence.py` と同じ契約）。検査内容: header 分類
   （spec / legacy / none）と field 解析、`Generated` 日付妥当性、`Source` sha の履歴実在・
   HEAD 一致・behind 数（subprocess list-args — zsh word-splitting 罠はコードの性質として
   消滅）、`Tokens` 主張 vs 実測（bytes/4）drift、`Updated:` 継ぎ足し鎖の長さ、
   INDEX 集計整合、mtime fallback 素材、count 様トークンの列挙（Numeric Claims Discipline の
   hybrid 候補 — 免除判定は読み手の LLM）。
2. `--gate` は `--produced` 必須とし、**agent が今書いたと主張するファイルにだけ**現行 spec を
   厳格適用する（exit 3）。既存 corpus の legacy header は evidence の注記どまり — gate 対象に
   しない。この境界は上の実測（24/24 legacy）が根拠で、orphan を今日の sha で裁かない従来の
   「glob するな」規律も `--produced` 必須化でコードの性質になる。
3. code/LLM の境界線: deterministic（header 実在・書式・sha 解決・behind・token drift・
   orphan・INDEX 集計）= script、hybrid（count 様トークン・継ぎ足し鎖長）= script が数えて
   LLM が解釈、semantic（どの codemap を書くか・altitude 圧縮・architecture 捏造禁止・
   dependencies.md の実質判定）= codemap-writer agent に残す。
4. 実行座標は skill / agent のステップ（ADR-0051 Decision 2 と同じ判断 — 課税率が低く
   自作 script なので verify.sh 常時配線はしない）: update-codemaps step 2（evidence）と
   step 5（gate）、codemap-writer agent の返却前自己検収（gate）。skill 本文の shell 断片と
   zsh 罠の長文警告は script 参照へ置換した。
5. verify.sh の owned 判定（5 箇所の origin case）に `*ECC-customized*` を追加する。
   update-codemaps は `origin: ECC-customized` で、従来の判定では新設テストが黙って
   スキップされた。ECC-customized = 内容編集済み = repo copy は著者所有、が根拠。現時点で
   Python / shell 資産を持つ ECC-customized skill は update-codemaps のみで副作用なし。

## Review-when

- codemap-writer の header spec（§ Freshness header）が変わったら — script の spec regex は
  agent 定義と 1:1 で、片方だけの変更は gate を偽陽性/偽陰性にする
- 既存 corpus を現行 spec で再生成し終えたら — legacy 免除を evidence から警告へ格上げする
  余地が生まれる
- `--gate` が常時配線（verify.sh / commit hook）を要求され始めたら — Decision 4 の座標判断を
  ADR-0051 Decision 2 と併せて再訪
- ECC-customized skill が外部 upstream の Python 資産を持ち込んだら — Decision 5 の owned
  判定が外部コードを lint し始めるので、skill 単位の除外に切り替える

## Alternatives Considered

- **既存 corpus 全体への厳格 gate**: 24/24 が legacy で初日に全滅。免除境界の設計ミスを
  そのまま踏む形なので却下。
- **context-sync の evidence script 群へ同居**: 対象 corpus は同じ docs/CODEMAPS/ だが、
  検査の正本（header spec）は codemap-writer agent が持つ。writer skill 配下に置く
  review-to-lint の置き場規約（§3）に従い、drift 面でも spec の隣が正しい。
- **legacy header の自動移行（script が書き換える）**: 移行は再生成（agent の仕事）で行うのが
  正しい。script が本文を書き換え始めると evidence 契約（判定しない・変更しない）が壊れる。
- **verify.sh 常時配線**: codemap を触らない commit にも毎回課税する。ADR-0051 Decision 2 の
  判断を踏襲して skill ステップ側へ。

## Consequences

- 良: zsh word-splitting 罠と「orphan を今日の sha で裁く」誤りが、警告文でなくコードの
  性質として消える。skill 本文の防御的長文が削れた。
- 良: 継ぎ足し鎖長と token drift が初めて数値化された（contemplative-agent architecture.md
  の Updated 8 本 / 57% drift は再生成需要の evidence）。
- 負: header spec が agent 定義と script の 2 箇所に存在する（regex は spec の写し）。
  Review-when 1 項で監視する。
- 負: skill を経由しない codemap 編集には効かない（ADR-0051 と同じ制約）。
- 中立: 既存 corpus の legacy header は本 ADR では直さない — 次回それぞれの repo で
  regenerate されたときに spec へ揃う。
