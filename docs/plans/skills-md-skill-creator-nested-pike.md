# Plan: prompt-audit のアンチパターンを skill 作成・改修規律へ昇格

## Context

2026-09-02 の `/claude-api prompt-audit`（Fable 5.1 向け）で `~/.claude` の prompt surface から
88 件（High 3 / Medium 85）を検出し、44 ファイル +141/−421 を適用済み（未 commit）。分布は
**1d migration-relative（版差 marker と退役 tombstone）が 55 件**で、1a/1b は 0 件。
つまり ADR-0018/0035 で潰した「旧世代向け over-constraint」は再発しておらず、再発しているのは
**改修時に前版との差分を本文へ書く**癖 — 「（2026-08-25 追加）」「Y から降格」「旧 X は廃止」
「2026-08-29 移設」。これは新規作成時の skill-creator を通らない**小さな追記**で入るので、
skill-creator §3 の文章規律だけでは届かない。常駐 rule（skills.md）の 1 行と、機械ゲート
（harness_lint）の両方に配線する。llm-first-code「執行者は機械ゲート」に沿う。

著者確認済み: lint gate を足す / ADR を書く。

## 変更 1 — `skills/skill-creator/SKILL.md` §3「書き方 — Fable 向け」に 1 bullet 群を追加

既存 bullet「判断基準と罠を書く…」の直後に追加（正本はここ。skills.md は 1 行ポインタ）:

- **現行規則として書く — 前版との差分を書かない。** 「（日付 追加 / 追記 / 移設 / 移管 / 再編 /
  明文化）」「Y から降格」「旧 X は廃止、no longer」「2026-xx-xx に復活」は edit 履歴で、git と
  ADR が持つ。本文は現在の規則 + 理由 1 句 + ADR/RFC 番号。**as-of 日付は claim にだけ付ける**
  （knowledge-staleness）— 外部事実の検索時点、実測の観測日。edit の日付は付けない
  （実測: 2026-09-02 prompt-audit で 88 件中 55 件がこの型。ADR-0061）
- **存在しないものを「やらない」と書かない（tombstone）。** 退役した step / store / 機構は
  消し、禁止の実体があれば正の形で書く（「Wikidata 連邦 — RETIRED、この step は実行しない」→
  「sameAs は self-sovereign な解決先のみ」）。モデルは見たことのない選択肢を幻の代替として読む
- **経緯は ADR、本文は規則。** 「初見では X と推定しかけたが…」「第一波 / 第二波で移行」型の
  物語は残さない。理由が 1 句で言えるなら 1 句（「正本の改名時にコピーが取り残された前例あり」）
- **改修は置換、追記ではない。** 規則を変えたら旧記述を grep して消す — 同一ファイル内に 2 版
  が残ると Fable は両方を文字通り読んで毎回どちらかを選ぶ（config-gc L25 vs L61、
  authorship-strategy L184 vs L186 の実例）
- **条件を列挙したら tie-breaker を置かない。** 「判断に迷ったら Y」は条件付き gate を Y 側に
  戻す（implementation-chain feat×TDD の実例）
- **例は出力の register を固定する。** 例の文体・長さ・言語がそのまま出力に写る。GitHub
  コメント調の小文字例 9 本（thermo-nuclear）のような register 例は置かない。format を pin
  する例だけ、illustrative と明記して置く

§4 草稿ゲートの Hygiene 行に「版差 marker / tombstone / 同一ファイル内の 2 版」を追記（1 句）。

## 変更 2 — `rules/common/skills.md` に 1 行（常駐ポインタ）

「skill / agent を新規作成・大幅改修するときは skill-creator を読む」段落の直後:

> **小さな追記でも現行規則として書く** — 編集日・「追加 / 移設 / 廃止」の版差語・退役物の
> tombstone は本文に書かない（git と ADR が持つ。as-of 日付は claim にだけ）。正本は
> skill-creator §3、機械検査は `harness_lint.py`。

既存の `<!-- rationale -->` / `<!-- review-when -->` コメントは維持。residency +2 行。

## 変更 3 — `scripts/hooks/harness_lint.py` に `lint_version_diff_markers`

- 対象: `skills/*/SKILL.md`（外部 symlink は除外、既存 `is_external_symlink` を再利用）、
  `agents/*.md`、`rules/common/*.md`、`CLAUDE.md`。frontmatter と code fence は除外
  （既存 `strip_code` を再利用）
- regex: 同一括弧内に `20\d\d-\d\d-\d\d` と edit 動詞 `(追加|追記|移設|移管|再編|明文化|更新済み|移行済み)`
  → `[（(][^（）()]*20\d{2}-\d{2}-\d{2}[^（）()]*(追加|追記|移設|移管|再編|明文化|更新済み|移行済み)[^（）()]*[）)]`
  - `退役 / 廃止 / 降格 / 反転 / 復活` は**含めない** — 現状態の as-of 記述にも使われる
    （現 tree の残り 2 hit: authorship-strategy:201「2026-08-04 退役、再導入しない」、
    harness-sync:207「2026-07-31 に退役、ADR-0026」は正当）。lint は「edit 履歴」だけ機械判定し、
    tombstone / 経緯物語は skill-creator の判断層に残す
- finding 文: `{path}:{line}: 版差 marker「…」— 現行規則として書き、edit 日付は git に任せる (skill-creator §3 / ADR-0061)`
- `main()` の呼び出し列に追加（`lint_rules_metadata` の後）
- 現 tree（diff 適用後）で該当 0 件を確認済み → baseline clean

## 変更 4 — テスト

- `tests/harness-lint-precommit.bats` に 2 ケース: marker を含む skill fixture → exit 3 + 該当行、
  「（2026-08-04 退役）」を含む fixture → exit 0（偽陽性ガード）
- `tests/golden/harness-lint/` の clean fixture が silent のまま通ることを確認（golden 更新は
  出力が変わった場合のみ、`tests/golden/README.md` の手順）

## 変更 5 — ADR-0061（adr-writer agent で render）

決定 packet:
- Context: prompt-audit 2026-09-02 の分布（88 件、1d 55 / 1c 18 / G2 9 / 1a 7）、ADR-0018/0035 後も
  再発した型は「改修時の版差記述」で新規作成ゲートを通らない、High 3 件（release-doi の `$(`
  が harness 自身の hook と衝突 / config-gc・authorship-strategy の同一ファイル内 2 版）
- Decision: (1) skill-creator §3 に 6 規律 (2) skills.md に常駐 1 行 (3) harness_lint に
  version-diff marker 検査（edit 動詞限定）(4) 88 件の適用
- Review-when: 次の Claude model release で `/claude-api prompt-audit` を再実行し 1d が再び
  最多なら lint の動詞集合を広げる / lint が正当な as-of 記述を 2 回以上偽陽性で止めたら
  動詞集合を狭める
- Alternatives: lint 無し（文章規律のみ — 今回の 55 件は文章規律が既にある下で入った）/
  退役語も lint 対象（as-of 記述を巻き込む偽陽性、現 tree に 2 例）/ generation-audit に
  統合（あれは runtime 層照合で、内部 cruft の静的検査は別物）
- Consequences: residency +2 行、precommit に regex 1 本、`generation-audit` Related に
  `/claude-api prompt-audit` を 1 行ポインタ追加（任意）

## 実行順

1. harness_lint.py + bats（TDD: RED → GREEN）
2. skill-creator §3 / §4、skills.md
3. ADR-0061（adr-writer skill 経由、index 更新）
4. `python3 scripts/hooks/harness_lint.py` / `bash .claude/verify.sh` / `scan_refs` dangling 0
5. commit は著者指示後（今日の 44 ファイル適用分と同じ commit か分けるかは著者判断。
   verify-precommit は tests 内 2 ファイルの既存 ruff format 差分で止まる可能性 → 先に `ruff format tests/`）

## Verification

- `uv run --directory ~/.claude/tests bats tests/harness-lint-precommit.bats`（新 2 ケース含む）
- `python3 scripts/hooks/harness_lint.py` exit 0
- 手動: `echo "（2026-09-02 追加）" >> skills/tdd/SKILL.md` → lint exit 3 → revert
- `.claude/verify.sh` 全通過
