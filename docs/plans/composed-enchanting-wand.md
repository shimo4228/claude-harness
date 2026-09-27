# plan を repo の `docs/plans/` に置き、ADR / RFC / commit からリンクする記録層にする

## Context

- **なぜ**: 2026-09-27 の議論（指摘と Eval を照合可能に公開する仕組みの方向づけ）で、公開物だけで連鎖を辿る予備測定を回した。公開済み 5 件・20 環のうち「確認」は 3 環（すべて「結果」の環）。欠けたのは「出力」と「指摘」の環で、その証拠は私的な場所にある。plan はまさにその 2 環 — 実装前のエージェントの意図、承認時の著者の編集（「(edited by user)」）、検証手順（外れうる予告）— を持つが、global の `~/.claude/plans/`（gitignore、255 本・3.3MB）にあって公開物から辿れない
- **前の判断**: 2026-08-25 に rfc-writer へ「plan は作業状態。紐付けはリンクでなく昇格。RFC・ADR から plans/ へリンクしない」と書き（cd93d38）、同日「何もしない既定は書かなくてよい」で削除した（4d77add）。理由は commit メッセージにだけ残った。ADR-0009:118 は既に存在しない plan を指す dead link になっている
- **今回の判断（著者）**: plan は凍結スナップショットとして残す。後の現実との食い違いはそれ自体が記録になる。ADR / RFC は日付付きの追記で上書きを記録するので、原本の plan を指しても害は無い。安い運用で、ADR / RFC も追いやすくなる
- **確かめた事実**:
  - `plansDirectory` 設定は CLI 2.1.9 で追加（公式 CHANGELOG）。project 単位で効かない不具合 #19537 は 2026-01-20 に修正済み。相対パスは作業ルート起点（二次資料 — Step 0 で実測する）
  - `ExitPlanMode` の payload は `plan` と `planFilePath` を持つ（`hooks/plan-executor-notice.sh` のヘッダ、271/271 実測）
  - **`~/.claude/.gitignore:16` の `plans/` は位置を固定しないので `docs/plans/` まで無視する**（`git check-ignore` で確認）。`/plans/` に直す必要がある
  - 公開同期 `claude-harness/scripts/sync-from-local.sh` は `SUBTREES=(skills agents rules docs/adr rfcs hooks scripts/hooks tests)`（:44）。`$HOME` の実値を含む行があると abort（:218-240、`pragma: allow-home-path` で個別許可）。直近 60 本の plan で `$HOME` 実値を含むのは 3 本、秘密のパターンは 0 本
  - verify.sh の markdown lint は staged `.md` への advisory（block しない）。`adr_lint.py` は節の有無だけを見る（行の追加は安全）。`claims.py` は frontmatter の `state:` と本文の最初の非見出し行（要約）を読む — RFC の plan リンクは要約行にしない位置（Status 節）に置く
- **狙う結果**: plan mode の plan が各 repo の `docs/plans/` に生まれ、承認されたものが commit され、ADR / RFC / 後続 commit から相対リンクで辿れる。~/.claude の plan は claude-harness にも出る

## 決めたこと（変えたいならここ）

1. **置き場所は `docs/plans/`**。ADR（`docs/adr/`）の隣で、root の legacy `plans/`（global 既定と同じ場所）と衝突しない
2. **既定は user-level** の `plansDirectory: "docs/plans"`（`~/.claude/settings.json`）。除外（私的な場所に置く）は各 `.claude/settings.local.json`（`**/.claude/settings.local.json` は global ignore 済み）で上書きする:
   - contemplative-agent → `.notes/plans`（第三者の投稿本文が混ざりうる。`.notes/` は既に非公開）
   - zenn-content → `planning/plans`（下書き・企画は非公開の方針、`.gitignore:25`）
   - Obsidian vault と `~/MyAI_Lab` 直下（repo でない）→ legacy の `~/.claude/plans`（絶対パス）
3. **承認した plan は、実装の最初の commit に単独で入れる**（`docs(plan): <slug>`）。後続 commit は本文に `Plan: docs/plans/<file>` を 1 行。ADR は Context の先頭に、RFC は `## Status` に日付付き 1 行でリンクする（相対リンク: ADR から `../plans/<file>`、RFC から `../docs/plans/<file>`）
4. 承認されなかった・放棄した plan は commit しなくてよい（消してよい）
5. **plan は公開可能な書き方を既定にする**（rfcs と同じ、ADR-0049）。秘密・第三者の本文・私的な戦略はリンク先へ逃がす。パスは `~/` で書く（`$HOME` 実値は同期で abort する）
6. **commit を促す hook は作らない**。2 週間の commit 率を見てから決める（ADR の Review-when に置く）
7. 既存の 255 本は移さない（中身の点検なしに repo へ入れない）
8. ~/.claude の `docs/plans/` は claude-harness へ同期する（`SUBTREES` に追加）

## 手順

**Step 0 — 実測（repo は触らない。scratchpad のみ）**
`claude -p --settings '{"plansDirectory":"docs/plans"}' --permission-mode plan "<小さな依頼>"` を次の 4 か所で走らせ、plan ファイルの落ちる場所を見る: (a) scratch の git repo の root、(b) その repo のサブディレクトリ、(c) repo でないディレクトリ、(d) `git worktree` の中。あわせて (e) 絶対パス指定が効くか。結果で決定 2 の除外リストを確定する（(b) が cwd 起点ならサブディレクトリ起動の注意を rule に 1 句足す）

**Step 1 — ignore の修正**
`~/.claude/.gitignore:16` の `plans/` を `/plans/` に。`git check-ignore -v docs/plans/x.md` が無反応、`plans/x.md` は従来どおり ignore されることを確認。`_gc_trash/2026-07-06/plans/*` はいま `plans/` のおかげで ignore されている可能性がある — `git check-ignore -v` で確かめ、他の規則で ignore されていなければ `/_gc_trash/` を足す

**Step 2 — 設定**
user-level `~/.claude/settings.json` に `"plansDirectory": "docs/plans"`。除外 4 か所の `.claude/settings.local.json` に上書きを置く（Step 0 の結果に合わせる）

**Step 3 — この plan を最初の記録にする**
この plan を `~/.claude/docs/plans/composed-enchanting-wand.md` へ移す（名前は Claude Code が付けたまま）

**Step 4 — 書き方の規約**（すべて短い追記）
- `rules/common/planning.md`: 1 項目 — 「plan は repo の `docs/plans/` に残る記録（ADR-0085）。公開可能な書き方を既定にし、機微はリンク先へ。承認した plan は実装の最初の commit に入れ、後続 commit（`Plan:` 行）と ADR / RFC からリンクする」。冒頭の rationale / review-when コメントを合わせて更新
- `skills/adr-writer/SKILL.md` Step 4: plan があれば Context の先頭に `Plan: [docs/plans/<file>](../plans/<file>)（承認 YYYY-MM-DD）` を 1 行
- `skills/rfc-writer/SKILL.md` §1 様式: plan があれば `## Status` に `**YYYY-MM-DD plan** — [docs/plans/<file>](../docs/plans/<file>)` を 1 行（本文の最初の行にしない — `claims.py ready` の要約になるため）
- `skills/harness-sync/SKILL.md`: subtree の列挙と規則の箇条に `docs/plans/` を追加（丸ごと同期、公開可能な書き方が既定、`$HOME` 実値は abort）

**Step 5 — ADR**
skill `adr-writer` で ADR-0085（番号は Step 2 の採番で確定）を起票: 上の決定 1〜8、Context に 2026-08-25 の経緯（cd93d38 / 4d77add）と予備測定、Review-when（下）、Alternatives（global のまま・hash だけ・per-repo の committed setting・hook・既存 255 本の移行・原案と編集の差分保存）。Context 先頭に Step 3 の plan へのリンク。ADR-0009:118 と ADR-0012:60 に日付付き注記（plan は legacy の global 置き場で公開されない／消失）

**Step 6 — Review**
`/code-review medium`（~/.claude の diff と claude-harness の script diff）と `security-reviewer`（公開範囲が動くため）を並列。reviewer への指示は implementation-chain の定型文

**Step 7 — Verify と commit（~/.claude）**
`./.claude/verify.sh`（full）exit 0、`adr_lint.py --gate`、`git status` clean。commit は分ける: (a) `.gitignore` と plan の記録（`docs(plan): …`）、(b) rules / skills、(c) ADR-0085 と index・注記。各本文に `Plan: docs/plans/composed-enchanting-wand.md`

**Step 8 — 公開（著者の GO を得てから）**
claude-harness: `scripts/sync-from-local.sh` の `SUBTREES` に `docs/plans` を追加、README.md / README.ja.md の `docs/adr/`・`rfcs/` の段落の後に `docs/plans/` を 1 段落（skill `readme-writer` の Incremental モード）。skill `harness-sync` の dry-run → 著者 GO → apply → claude-harness を push

## Chain（implementation-chain）

- 種別: **feat** — 新しい記録層と、公開範囲（外に出るデータの範囲）の追加
- Phase 0: 済み（CHANGELOG・issue・二次資料）+ Step 0 の実測
- TDD: `-` — 振る舞いの変わるコードは同期 script の配列 1 要素だけで、dry-run が確かめる
- Code Review: Y（`medium`）/ Security Review: Y（公開経路）/ Doc Sync: Y（ADR-0085、skills、公開 README）/ Verify: Y
- harness-boundary: `plansDirectory` = Runtime（薄い配線。plan mode が変われば見直す）/ `docs/plans/` の中身 = Data（runtime を替えても残る markdown の記録）/ 公開既定と書き方 = Values（rule）/ リンクの手順 = Skills（adr-writer・rfc-writer）/ commit を促す hook = Defer（実測してから）
- 実行者の決定: このセッション（Opus 5.5、build-tier）で実装する — 複数 repo と untracked の設定を触るので cloud dispatch に乗らない（(b)）、かつ著者の明示指示（(c)）

## Verification

- Step 0 の 5 ケースの落ち先を記録し、決定 2 と一致する
- 設定後、~/.claude で plan mode に入ると plan が `~/.claude/docs/plans/` に生まれる。CA・zenn-content では `.notes/plans` / `planning/plans` に生まれ、`git status` は clean のまま
- `git check-ignore`: `docs/plans/x.md` は無視されない、`plans/x.md` は無視される
- `adr_lint.py --gate` と `adr_review_evidence.py` のリンク検査で ADR-0085 → plan のリンクが生きている
- `./.claude/verify.sh` full exit 0
- 公開後: GitHub 上の ADR-0085 から plan へのリンクが開ける。任意で、今日の読者役の予備測定を ADR-0085 に当て、「出力」と「Expect」の環が「確認」になるかを見る（外れうる予測）

## ADR-0085 の Review-when（案）

- 2 週間後に `~/.claude/docs/plans/` の tracked / untracked の比を数える。承認済みの plan の commit が半分未満なら、`ExitPlanMode` の PostToolUse で「承認した plan を最初の commit に」と促す advisory を足す
- plan mode が mod 化・廃止される、または `plansDirectory` の意味が変わる（CHANGELOG）→ 設定と規約を見直す（ADR-0057 の注記と同じ前提）
- 公開した plan で機微情報の事故が 1 件でも出たら、公開の既定を見直す（ADR-0049 と同じ tripwire）
- 同期が `$HOME` 実値で abort することが続いたら、同期側で `~/` への置換を足す
- 4 週間、plan へリンクする ADR / RFC が 0 本なら、リンク規約は使われていない — 規約を消す

## 範囲外

- 指摘と Eval の公開の本体（commit の `指摘:` / `Trigger:` / `Expect:`、Eval カード、読者役による定期照合）— 詳細設計セッションで決める
- エージェントの原案と著者の編集の差分を残すこと（`ExitPlanMode` の payload を使う案）
- 既存 255 本の移行、cloud session での plan（user-level 設定が届かない）
