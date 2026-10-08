# Kickoff packet — S1: reader-cut-pilot（削り手の一致試験の道具を作る）

あなたは task-triage loop の **build 役**です。
cwd は `~/.claude` の git worktree（branch は Agent tool が作ったもの）。成果は branch 上の commit で返し、
判断役が検収して main へ ff-only 取り込みます。境界（人間に渡す操作 / とってよいリスク / 止まる条件）は
rule `boundary.md` — build は task branch まで。packet に無いことは harness の規約が既定。

最初に読む: `docs/plans/reader-cut-pilot.html`（承認済みの plan。claim 1〜4 と aux）、
`docs/plans/research/2026-10-07-reader-grounded-cut-pilot.md`（調査 report）、
`skills/readme-writer/scripts/readme_md.py:67`（`_content_lines`）と
`skills/readme-writer/scripts/readme_prose.py:163`（`register_ja` の文分割）、
skill `measurement-discipline` の原則 7・8・9。

Effort: medium — 通常の feat。文分割は既存 code の流用で、新しい parser は書かない。

実行者の決定: 既定の cloud session ではなくローカルの worktree。理由 — main に別作業の未 commit の追跡ファイルが
あり `scripts/cloud-dispatch.sh` の preflight が通らない（判断役は触れない）、かつ Artifact の db と
`claude -p` / `codex` の実行がローカルにしか無い。

## 進め方
- 入力が要らない step は止まらずに続ける。止まるのは Phase 0 の反証、Review の CRITICAL、time cap、
  この packet の外の操作が要るときだけ
- 確かめられなかったことには「未確認」と印を付け、どこを見たかを書く
- 方針を選んだ箇所は、その理由を 3 文で Report の Fix に書く
- チェックリストは commit しないファイル（`/tmp/reader-cut-tasks.md`）に置く

## 本番との差（measurement-discipline §8）
この試験に「本番」は無い。arm の梯子は plan claim 2.1 のとおりで、隣り合う arm の差は 1 つだけ:

| arm | 読者の欄 | 見せる範囲 | モデル |
|---|---|---|---|
| A0 | 空 | 全文 | sonnet（`claude -p --model sonnet`） |
| A1 | `prompt/persona.md`（著者を説明する 1 段落） | 全文 | sonnet |
| A2 | `prompt/evidence.md`（著者の発話の抜粋 + 既読記事の一覧） | 全文 | sonnet |
| A3 | `prompt/evidence.md` | その節までの前方だけ。判定させるのは現在の節の文だけ | sonnet |
| A4 | `prompt/evidence.md` | 全文 | codex（`codex exec`。Phase 0 で呼び方を確かめる） |

審判の定義（著者が確認した前提）: 正解ラベルは著者の印。`skip`（要らない）= 削ってよい文、`stop`（止まった）=
削ってはいけない側の証拠、`null` = 要る。削り手の `CUT` を「削った」と数える。`CONDENSE` は記録するが P/R に
入れない。`persona.md` と `evidence.md` の中身は判断役が書く — build はプレースホルダ（`{{TODO}}` を含む）を置き、
`run` は `{{TODO}}` が残っていたら例外で止まる。

## Goal（決定可能な受入条件）
1. `uv run --project skills/readme-writer --directory skills/readme-writer pytest -q` が exit 0。
   新しい `tests/test_reader_cut.py` を含み、split・score・prompt 組み立て・row parse を検査する
2. `./.claude/verify.sh`（引数なし）が exit 0
3. `python -m scripts.reader_cut split <path> --text-id <id>`（cwd = `skills/readme-writer`）が、plan claim 1.1 の
   JSON（`text_id` / `source` / `sha256` / `last_modified` / `reader: "author"` / `units[i, line, text, mark: null]`）を
   `evals/reader-cut/units/<id>.json` に書く。単位は本文の散文の文（。！？で閉じる、段落をまたいでよい）と
   箇条書きの項目。code fence・front matter・表・画像・HTML ブロック・見出しは単位にしない。次の 4 本で実行し、
   単位数を Report に書く:
   - `~/MyAI_Lab/pdf2anki/README.ja.md` → `pdf2anki.README.ja`
   - `~/MyAI_Lab/contemplative-agent-rules/README.ja.md` → `contemplative-agent-rules.README.ja`
   - `~/MyAI_Lab/zenn-content/articles/claude-code-context-audit.md` → `claude-code-context-audit`
   - `~/MyAI_Lab/zenn-content/articles/claude-code-zenn-writing-env.md` → `claude-code-zenn-writing-env`
4. `python -m scripts.reader_cut page` が、4 本の単位を載せた印付けページ 1 枚
   `evals/reader-cut/page/marking.html` を書く。plan claim 1 の mock のとおり、文を押すたびに
   null → skip → stop → null と巡回し、本文の切り替え・件数表示・保存がある。保存先は Artifact の db
   capability（collection `marks`、doc id = `text_id`、field `sha256` と `marks: {"<i>": "skip"|"stop"}`）。
   **書く前に skill `artifact-capabilities` を読み、その API どおりに書く**。phone 幅（375px）で横スクロールしない。
   公開はしない（判断役が行う）
5. `python -m scripts.reader_cut ingest <db-export.json>` が db の内容を `evals/reader-cut/labels/<id>.json`
   （units JSON に mark を埋めたもの）へ書く。sha256 が units と違えば例外で止まる
6. `python -m scripts.reader_cut run --arm A0..A4 --run 1|2 [--text <id>] [--dry-run]` が
   `prompt/cutter.md` と `prompt/arms.toml` から prompt を組み、A0〜A3 は
   `claude -p <prompt> --model sonnet --settings '{"outputStyle": "default"}'`、A4 は codex で呼び、
   `<i>\t<CUT|CONDENSE|PRESERVE>\t<根拠>` の行を parse して `evals/reader-cut/results/<arm>/run<k>/<id>.tsv` に書く。
   行数・番号が単位と合わなければ例外（`{}` で続けない）。外部呼び出しは関数 1 つに閉じ、テストは偽の runner で
   行う。`--dry-run` は prompt を表示するだけ。**本物の arm は走らせない**（印がまだ無い。判断役が後で回す）
7. `python -m scripts.reader_cut score` が plan claim 3 の表（text 数・文数・skip 数・基準率 b、arm ごとに
   CUT 数 / P / R / P/b / 止∩CUT / 保護違反 / run 一致 = 1 − Jaccard 距離の補、削った字数）を出し、同じ内容を
   `evals/reader-cut/results/score.json` に書く。保護文の正規表現は plan claim 2.2 の sketch を出発点にする。
   合成 fixture での golden test を付ける

## Phase 0 — 前提の再照合（反証されたら実装せず止めて報告。記録して正しく直せる範囲はその判断も報告に書く）
- worktree の branch が local `main`（`c74113d docs(plan): reader-cut-pilot` と、この packet の commit を含む）を
  含むこと。含まなければ `git merge --ff-only main` してから始める
- `readme_md._content_lines` と `readme_prose.register_ja` の文分割が、日本語の記事（Zenn の front matter・
  `:::message` ブロック付き）でも流用できるか。できなければ最小の分岐を足し、その理由を Fix に書く
- `codex exec --help` で非対話の呼び方と、model・出力の受け取り方を確かめる。使えなければ A4 は `run` で
  明示的な例外にし、Needs from judge に書く
- skill `artifact-capabilities` の db capability が「collection / doc id / field」の形で使えるか

## Build（順序）
1. TDD: `tests/test_reader_cut.py` の失敗するテストを先に書く（split の単位境界、score の P/R/b と保護違反、
   row parse の fail-loud、`{{TODO}}` で止まる run）
2. 実装は `scripts/reader_cut.py` 1 本（subcommand: split / page / ingest / run / score）。既存の
   `readme_md` / `readme_prose` を import して流用し、複製しない。依存は追加しない（`tomllib` は標準）
3. `prompt/cutter.md` は plan claim 2 の sketch、`prompt/arms.toml` は claim 2.1 の sketch を正本にする
4. verify: Goal 1・2

## Review
- 種別: feat。**chain は skill `implementation-chain` の Chain Matrix に従う**（この packet は reviewer を列挙しない —
  列挙漏れは省略の許可ではない）。Phase 0 External Research は plan の調査 report で済んでいるので省いてよい
- packet に書いていないことは harness の規約が既定。省略・読み替えは可だが、報告に「逸脱: 何を・なぜ」と
  **必ず名指し**する。無言の逸脱は結果が正しくても bounce される
- diff 外の気づきは `rfcs/` にも台帳にも書かない。再現手順を書けるものは Report の `Proposed tasks`
  （最大 2 件）に、書けないものは `Out-of-diff findings` に 1 行ずつ置く

## Must-not（境界 = Goodhart 対策）
- 変えてよいのは `skills/readme-writer/scripts/reader_cut.py`・`skills/readme-writer/prompt/`・
  `skills/readme-writer/tests/test_reader_cut.py`（と必要な fixture）・`skills/readme-writer/evals/reader-cut/` だけ
- `skills/readme-writer/evals/read-through-log.md` と `SKILL.md` を変えない（前者は著者の未 commit の変更が
  main の作業ツリーにある。列の追加は判断役が後で行う）
- `pyproject.toml` に依存を足さない。テストを弱めない・消さない・設定で黙らせない
- `.claude/verify.sh`・`.claude/verify.md`・`.github/`・`.claude/settings.json` を変えない
- 本物の `claude -p` / `codex` の arm を走らせない。Artifact を公開しない。corpus の本文を書き換えない
- `git add -A` を使わない。この packet のファイルを編集しない
- time cap 90 分。超えたら打ち切って、そこまでの diff とテスト状況で報告
- shell ループで複数 path を回すときは、path をファイルに書いて `while read` で 1 行ずつ回す

## Report（最終 commit の message 本文 = session が閉じても残る唯一の証拠）
feat(readme-writer): 削り手の一致試験の道具（split / page / ingest / run / score）

Packet: S1
Plan: docs/plans/reader-cut-pilot-s1-build.md
Needs from judge: <判断役かオーナーの決定・承認が要るもの / none>
Model: <この session のモデル名>
Effort: <実際に走った effort。分からなければ「未確認」>
Premise: <Phase 0 の 4 項目の結果>
Fix: <what and why>
Regression: <test names、RED→GREEN の確認方法>
Verify: <pytest の件数 / verify.sh の exit / 日時>
Review: <chain どおりに回した reviewer と結果> / Deviations: <逸脱の名指しと理由、無ければ none>
Units: <4 本それぞれの単位数と字数>
Risk: <とったリスク / 戻し方>
Proposed tasks (for the judge, 最大 2 件): <none でよい>
Out-of-diff findings (for the judge): <none でよい>

最後のメッセージは「判断役に要るもの」から始め、commit SHA・branch 名・verify の結果・所要時間を報告して
終了してください。前提が崩れて実装しなかったときも同じ形で報告してください。
