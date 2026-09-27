# Plan: とるリスク / 人間に渡す操作を 1 本の rule にまとめる

## Context

- 出発点は https://note.com/kazobara/n/ncc0a3d38921a（2026-09-09）の「アンチハーネス」節: 禁止リストだけで書くと現場が止まる。先に「とるリスク / とらないリスク」を仕訳し、許容事故を定義する。同記事の「共有してよいのは目的・禁止・完了条件だけ」— 禁止（境界）は全役割が読む層に置くべきもので、rules が全役割に放送される性質と一致する
- 著者の決定（2026-09-15）: 層別のコンテキスト管理は個人実装では過剰。スコープを「とってよいリスクと制約の整理」に絞り、各所に散っている禁止を 1 本の rule にする
- substrate（Claude Code の system prompt）は既に一般則を持つ — 「hard to reverse or outward-facing → confirm first」「Stop only for destructive actions or genuine scope changes」。ADR-0035 はこれを理由に `human-gate.md` を退役させた。新 rule はこの一般則を再宣言せず、**substrate が知りえないハーネス固有の事実**（ここでは何が不可逆・対外に当たるか）と**確認なしでやってよい側**だけを持つ
- 著者の原則（2026-09-14、ADR-0065）「することだけを書く。やめる項目は本文から消す」と両立させる: 「するな」の列挙でなく、**人間に渡す** / **とる** / **止まる** の 3 動詞で書く
- **著者の決定（2026-09-15）: main への取り込みと push は Claude の判断でよい。** これで ADR-0043 の「人間 = 最後のスイッチ（merge word）」が変わる。本 plan の読み: 判断役（judge）が検収したら自分で ff-only 取り込み・push まで行い、digest は事後報告。build は branch までで、実装者と検収者の分離は残す。無人時に rules / hooks / permissions / scheduled task / `.claude/verify.sh` を含む diff の取り込みだけは人間に残す（ExitPlanMode で確認）

## 散在の実態（本セッションで grep）

| 場所 | 内容 | 分類 |
|---|---|---|
| `skills/task-triage/references/packet-template.md:19,55` | main に触らない / merge / push / 台帳の状態変更 / `git add -A` | 境界（共通）+ task 固有 1 つ |
| `skills/task-triage/SKILL.md:19-23` role 表 Never does 列 | judge: 起票・drop を独断 / merge / rules・ADR・hooks・公開物を無人で触る。build: 受入条件変更 / merge / push / 台帳。human: 個別セッションを見る | 境界（共通）+ 役割固有 |
| `skills/task-triage/SKILL.md:207-209` Damping | files nothing / drops nothing alone / never merges, publishes, touches rules / ADR / hooks / security gates unattended / 計測中に起票規則を変えない | 境界（共通）の再掲 |
| `skills/task-triage/SKILL.md:192` | 自分が spawn していない pane を閉じない | 境界（共通） |
| `scripts/triage-tick.sh:86` tick prompt | Do not merge, publish, or touch rules / ADR / hooks / security gates; file nothing and drop nothing on your own | 境界（共通）の再掲 + 無人 judge 固有 |
| `skills/growth-astra/SKILL.md:15` / `skills/growth-fable/SKILL.md:15-16` | 公開・評判に関わる action（投稿・公開 push・第三者 repo への PR・設定変更）は草稿で止めて著者へ | 境界（共通）の再掲 |
| `rules/common/security.md:10-11` | verify.sh は承認 hash がある版だけ無人実行 | 境界（機構が持つ） |
| `rules/common/agents.md:8-12` | Herdr 委譲は HERDR_ENV=1 + 明示指示。spawn-session は既存 pane に触れない | 境界（共通） |
| `rules/common/debugging.md` | rate limit 連発は policy signal として止めて人間へ | 止まる条件（共通） |
| `hooks/validate-bash.sh` | `rm -rf /`、`git push --force` を block | 機構が持つ |
| `skills/x-draft:16` / `public-comment:62-64` / `herdr-delegate:51` / `codex-review` | 投稿は人間 / 外部書き込みは承認後 / 委譲先は commit しない / read-only | 各 skill の手順（境界の適用例） |

同じ境界が 6 箇所に文面違いで存在する。正本は無い。

## 決定

### 1. `rules/common/boundary.md` を新設し、境界の正本にする

草案（harness_lint の origin / rationale / review-when を持つ。約 20 行）:

```
<!-- origin: shimo4228 -->
<!-- rationale: ADR-0067 — 境界が 6 箇所に文面違いで散っていた。substrate の一般則（hard to reverse or outward-facing → confirm first）は再宣言せず、このハーネスで何がそれに当たるかと、確認なしでやってよい側だけを置く -->
<!-- review-when: 人間に渡す操作の列挙に 1 つ足す / 減らす時。substrate が ledger・gate script・scheduled task を outward-facing として自ら扱うようになった時 -->
# 境界 — 人間に渡す操作と、とってよいリスク

**人間に渡す**（このハーネスで不可逆・対外に当たるもの。substrate の「confirm first」の対象）:
公開（投稿・第三者 repo への PR・release / DOI）/ 課金 / Slack digest 以外の外部送信 /
台帳の起票・drop（無人時）/ permissions・hooks・scheduled task・`.claude/verify.sh`（承認 hash）・
rules・ADR・skills の無人変更（その diff を含む取り込みも）/ 自分が spawn していない pane・
session / Herdr 委譲（HERDR_ENV=1 と明示指示の両方）。

**とる**（確認を待たない）: 検収を通した task branch の main への ff-only 取り込みと push
（force は hook が止める）・worktree と task branch の中の破壊・方針転換・粗い代替案 1 本・
赤テストのまま次の仮説へ（記録して。commit 前の verify は変わらない）・scratchpad・下書き・
`.notes/` `.growth/` への記録・task branch への commit。「もっと安全な設計を先に」は止まる理由にしない。

**止まって報告する**: 同じ方針で 2 回失敗 / time cap / 前提の反証 / 外部 platform の rate limit 連発
（policy signal。2026-07-16 に無期限 block を経験）。そこまでを残して報告する。

機械が止めるもの（ここには書かない）: `hooks/validate-bash.sh`（`rm -rf /`、force push）、
commit gate（verify / secret scan / harness lint）、episode log の読み込み。
```

`debugging.md` は「止まって報告する」に吸収して削除（rate limit の 1 行はそのまま移す）。`agents.md` の Herdr 委譲ゲートと spawn-session の pane 条件は boundary に移し、`agents.md` は catalog の所在と review 分離の 2 行に縮む。`security.md` の verify_allow 行はそのまま（機構の記述）。

### 2. 散っている側を pointer にする（二重定義を消す）

| 場所 | 変更 |
|---|---|
| `packet-template.md:19` | 「main に触らない…」を「境界は rule `boundary.md`（build は task branch まで。取り込みは判断役）」の 1 文に。`:55` は task 固有の `git add -A` と対象外ファイルだけ残す。Report に `Risk: <とったリスク / 戻し方>` 1 行を足す |
| `task-triage/SKILL.md:19-23` role 表 | Never does 列から共通境界を外し、役割固有（judge: 起票・drop を独断しない / build: 受入条件を変えない・取り込まない / human: 個別セッションを見ない）だけ残す。Human 行の「the merge word」を外し、Judge 行の Does に「検収後の ff-only 取り込みと push」を足す。表の下に「共通の境界は rule `boundary.md`」 |
| `task-triage/SKILL.md:186-200` §4 | 「the human says which; the judge types the merge」「Before asking for the merge word」を、検収 PASS → judge が取り込み → digest に事後報告（merged / unmerged とその理由）へ書き換える。Unmerged queue は「judge が見送った理由つき」に。verify_allow の approve は人間のまま（承認 hash は 人間に渡す 側） |
| `task-triage/SKILL.md:207-209` | 「files nothing / drops nothing alone / 計測中に起票規則を変えない」（loop 固有）だけ残し、merge / publish / rules-hooks の句を削除 |
| `task-triage/SKILL.md:192` | 削除（boundary が持つ） |
| `scripts/triage-tick.sh:86` | 「Do not merge, publish, or touch rules / ADR / hooks / security gates;」を削除し「file nothing and drop nothing on your own」（無人 judge 固有）と Slack one-way を残す。digest の「a merge word」を「what was merged / left」に。rules は無人 session にも自動ロードされる |
| `docs/adr/0043` | `> **注記（2026-09-15, ADR-0067）**`: 最後のスイッチは人間から判断役へ。人間は方向決めと digest 回答。ADR-0045（Slack digest）の merge word 記述にも同じ注記 |
| `growth-astra:15` / `growth-fable:15-16` | 「公開・評判に関わる action は草稿で止めて著者へ（境界は rule `boundary.md`）」の 1 文に統一 |
| `x-draft` / `public-comment` / `herdr-delegate` / `codex-review` | 触らない（skill 固有の手順。境界の適用例であって定義ではない） |
| `implementation-chain` | 触らない（dirty。dispatch 条件「rule 変更なし」は境界でなく実行者の判断条件） |

### 3. ADR-0067 を起票、ADR-0035 に注記

- ADR-0067（skill: `adr-writer`。0066 は search-first で使用済み）: Context = 散在 6 箇所 + 記事のアンチハーネス + 著者決定 2 つ（境界を 1 rule に / main 取り込みと push は Claude の判断）、Decision = 境界の正本を 1 rule に / substrate 一般則は再宣言しない / 3 動詞で書く / 最後のスイッチを判断役へ（ADR-0043 を部分 supersede）、Review-when = 上記 + 「判断役の取り込みで main が壊れ、人間が revert した回数が 3 か月で 2 回を超えたら merge を人間へ戻す」、Alternatives = (a) packet だけに書く（著者却下: 常駐 md を役割が参照すべき）(b) 層別コンテキスト管理（著者却下: 個人実装では過剰）(c) human-gate.md の復活（ADR-0035 が退役させた停止手順の再導入になる。本 rule は手順でなく事実の列挙）(d) build 自身が取り込む（実装者と検収者の分離が消える。却下）
- ADR-0035 の human-gate 退役節に `> **注記（2026-09-15, ADR-0067）**`: 停止手順は退役のまま。境界の**事実**だけを `boundary.md` が持つ

### 4. 付随

- `rules/README.md` の表に `boundary.md` 行を足し、`debugging.md` 行を消す
- `docs/adr/README.md` index に 0067
- harness-sync は別セッション（ADR-0065 と同じ）

## 実行者

prose のみ（rule / skill 参照 / tick prompt の文字列 / ADR）。implementation-chain の例外 (a) で本セッション。前提: 作業ツリーの ADR-0065 / RFC-0022 は本 plan のファイル（boundary.md 新規、packet-template、task-triage SKILL、triage-tick.sh、growth-*、debugging.md、agents.md、README 2 本、ADR-0035）と重ならないので、先に commit しなくてよい。commit は本 plan のファイルだけを add→commit 一気に（並行セッション対策、`git -C`、`$(` なし）

## Verification

1. `python3 scripts/hooks/harness_lint.py` green（新 rule の origin / rationale / review-when、README リンク、退役語の不在）
2. `grep -rn "merge, publish\|merges, publishes\|merge word\|草稿で止めて" skills/ scripts/ rules/ docs/adr/README.md` — 残るのは boundary.md、各 skill の pointer 1 文、ADR 本文の履歴だけ
3. `bats tests/` green（tick prompt を凍結する golden は無いことを確認済み）
4. adr-writer の `adr_lint.py` + agent `adr-reviewer`（ADR-0067）
5. 次の build packet 1 本で、Report に Risk 行が出ることを検収で見る

## 記事のうち今回採らないもの

層別コンテキスト管理（PURPOSE / TASK / TOOLS の役割別配布）、subagent 既定 model、compaction 閾値、資産の退役、コスト計測。実測は本セッションの transcript に残っている（14 日 332 セッション / 5.49 B 入力 / subagent probe 41,676 tokens）。必要になったら別 plan
