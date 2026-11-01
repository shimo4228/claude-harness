kind: internal
# Stage 0 前提テスト — 著者の 4 repo と公開 harness 20 本

as-of: 2026-11-01。plan [enumerated-petting-beaver](../enumerated-petting-beaver.md) Stage 0 手順 3–5。native 比較は
[2026-11-01-doctor-comparison.md](2026-11-01-doctor-comparison.md)、残り 10 本を回す前に固定した見立ては
[2026-11-01-premise-test-prediction.md](2026-11-01-premise-test-prediction.md)。

## 結論

- **驚きは公開 20 本中 19 本で成立**（plan の閾値は半数以上）。著者の 4 repo は 4/4。相手を大きい harness に絞る条件は発火しない
- **見立ては残り 10 本で 9/10 的中**（事前に置いた閾値は 8 本以上）。外れは P18（× と予測、判断可能な非 Keep 10 件で ○）
- **native に拾われない項目は非 Keep の 65%**（48/74、比較表）。位置取りを下げる条件（半分未満）は発火しない
- 最初の非 Keep 項目までの秒数は公開 20 本で中央値 134.5 秒、20 本すべて 200 秒以内（3 分以内は 18 本）。report 全体が 10 分以内に
  揃ったのは 12/20。遅いのは source でなく、全 source が終わった後の Phase 2–3（cross-check と report.md の組み立て）: 最後の
  section から report.md までが P01 377 秒、P02 405 秒、P06 771 秒、P11 1065 秒。P16 は report を組まずに終わり、P19 は組む途中で
  1800 秒の timeout。全 source の section は 20 本すべて 707 秒以内に揃っている
- 測定器の弱さ: 閾値 5 件は 20 本中 19 本が越える。この閾値は「驚きがあるか」をほぼ区別しない。Stage 3 の 50 本では件数でなく
  source 別の非 Keep 率と report 到達時間を主に見る

## 方法

**選定。** GitHub code search `filename:SKILL.md path:.claude/skills` を 9 ページ（696 ファイル、662 repo）取得。seed 20261101 で
shuffle し、fork でない・archive でない・2026-08-03 以降に push・300 MB 以下・`.claude/skills` 直下に skill dir 5 本以上で絞り、
著者の repo と ECC の mirror を外して 26 本を選んだ（P01–P20、P21–P26 は予備で未使用）。repo 名と Pnn の対応は手元だけに置く。
所有者への連絡はしていない。

**clone。** `GIT_LFS_SKIP_SMUDGE=1 git -c core.symlinks=false -c core.hooksPath=/dev/null clone --depth 1 --no-recurse-submodules`。
著者の repo は `git clone --local` の写し。全 run の後で全 clone の `git status` が clean（run は repo に書いていない）。

**隔離。** `skills/harness-stocktake/scripts/isolated-dry-run.sh`。cwd は空の out-dir（repo の settings・hooks・`.mcp.json` は
cwd からしか読まれない）、`--restricted`（Bash・WebFetch なし、settings ファイル無視、file tool は cwd と `--add-dir` に閉じる）、
`--strict-mcp-config`、`--disable-slash-commands`、tools は `Read,Grep,Glob,Write,Edit,Agent`、repo の下への Write / Edit は
`--disallowedTools`、`--settings` で `claudeMdExcludes: ~/.claude/**` と `autoMemoryEnabled: false`。`/context` で memory・skill・MCP が
載らないこと（8.4k token）を確認した。repo の外へ解決する symlink がある repo は起動前に止める。Claude Code 2.1.316、`--model opus`、
timeout 1800 秒、並列 3。

**驚きの操作化。** run 開始から 600 秒以内に `run/items-<source>.json` が現れた非 Keep 項目（Keep / Out of scope / Already Covered /
Too Specific 以外）のうち、fresh judge が decidable=true と答えたものが 5 件以上。fresh judge は report だけを渡した
`claude -p --model opus --tools ""`（hooks・style・`~/.claude` の CLAUDE.md を切り、JSON schema で全非 Keep 項目に
decidable を返させる）。report.md が無い run（P16・P19）は items JSON から組み立てた表を同じ judge に渡した。時刻は out-dir の外の
poller が 2 秒ごとに記録した `timeline.tsv`（model の自己申告ではない）。

## 公開 20 本

列: skills / agents / hooks / CLAUDE.md 行、全項目、非 Keep、source 別非 Keep、judge が判断可能とした非 Keep（全体 / 600 秒以内）、
最初の section・最初の非 Keep・report.md の秒数、`total_cost_usd`、驚き。

| id | 規模 | 項目 | 非 Keep | source 別 | 判断可能 | ≤600 s | section | 非 Keep | report | $ | 驚き |
|---|---|---|---|---|---|---|---|---|---|---|---|
| P01 | 35 / 1 / 2 / 222 | 163 | 43 | hooks2 docs5 agents1 distill9 skills13 assets7 rules6 | 35 | 24 | 111 | 107 | 1044 | 20.73 | ○ |
| P02 | 11 / 0 / 1 / 85 | 73 | 31 | hooks1 docs6 distill4 skills9 assets11 | 29 | 29 | 58 | 89 | 752 | 14.01 | ○ |
| P03 | 10 / 0 / 0 / 97 | 42 | 12 | docs1 distill4 skills3 assets4 | 10 | 10 | 36 | 141 | 316 | 3.97 | ○ |
| P04 | 19 / 6 / 4 / 7 | 72 | 19 | hooks3 docs1 agents3 distill2 skills6 assets4 | 18 | 18 | 58 | 113 | 500 | 6.88 | ○ |
| P05 | 23 / 33 / 9 / 333 | 112 | 49 | hooks3 docs9 agents15 distill3 skills7 assets12 | 46 | 46 | 55 | 149 | 563 | 10.41 | ○ |
| P06 | 13 / 10 / 2 / 193 | 88 | 26 | hooks3 docs4 agents5 distill1 skills4 assets9 | 26 | 26 | 56 | 123 | 1061 | 8.36 | ○ |
| P07 | 5 / 0 / 12 / 1 | 32 | 10 | hooks3 docs1 distill1 skills2 assets3 | 7 | 7 | 63 | 127 | 398 | 5.05 | ○ |
| P08 | 12 / 4 / 0 / 95 | 64 | 32 | docs7 agents4 distill3 skills7 assets11 | 31 | 31 | 48 | 153 | 434 | 7.96 | ○ |
| P09 | 21 / 0 / 0 / 0 | 70 | 32 | docs4 distill8 skills10 assets10 | 26 | 26 | 40 | 135 | 590 | 16.90 | ○ |
| P10 | 8 / 0 / 0 / 3 | 41 | 4 | docs1 distill1 skills2 | 4 | 4 | 43 | 134 | 261 | 5.53 | × |
| P11 | 139 / 0 / 0 / 156 | 202 | 34 | docs5 distill2 skills13 assets14 | 34 | 21 | 45 | 199 | 1700 | 14.31 | ○ |
| P12 | 23 / 15 / 4 / 134 | 104 | 36 | hooks4 docs6 agents7 distill3 skills12 assets4 | 28 | 28 | 47 | 160 | 468 | 8.81 | ○ |
| P13 | 76 / 1 / 1 / 85 | 113 | 11 | hooks1 docs4 agents1 distill1 assets4 | 8 | 8 | 59 | 75 | 585 | 6.47 | ○ |
| P14 | 11 / 0 / 0 / 0 | 53 | 14 | docs3 skills2 assets9 | 11 | 11 | 42 | 179 | 490 | 6.60 | ○ |
| P15 | 6 / 24 / 5 / 76 | 100 | 62 | hooks7 docs6 agents20 distill2 skills6 assets17 rules4 | 55 | 55 | 149 | 145 | 763 | 11.22 | ○ |
| P16 | 383 / 0 / 0 / 101 | 326 | 246 | docs5 distill3 skills209 assets29 | 230 | 23 | 46 | 163 | — | 12.67 | ○ |
| P17 | 22 / 5 / 1 / 3 | 76 | 23 | hooks2 docs4 agents2 skills12 assets3 | 20 | 20 | 52 | 109 | 638 | 10.10 | ○ |
| P18 | 5 / 0 / 0 / 38 | 37 | 10 | docs2 distill2 skills2 assets4 | 10 | 10 | 37 | 101 | 360 | 3.68 | ○ |
| P19 | 52 / 19 / 7 / 738 | 158 | 85 | hooks5 docs11 agents15 distill20 skills24 assets10 | 76 | 53 | 57 | 192 | — | — | ○ |
| P20 | 8 / 0 / 1 / 510 | 53 | 10 | hooks1 distill3 skills3 assets3 | 8 | 8 | 63 | 103 | 552 | 8.50 | ○ |

合計: 非 Keep 789 件、うち judge が判断可能 712 件（90%）。費用は API 換算で 19 本 $182.16（1 本 $3.68–20.73）、P19 は timeout で
未記録。subscription の枠で回した。

- **P16**: skills 383 本の大半が「この repo の仕事と関係しない汎用 skill の一括同梱」で Retire（skills の非 Keep 209 件はほぼ一つの
  パターン）。main loop は skills source の完了を待つと書いて turn を終え、report.md を組まずに終わった（rc=0、1183 秒）
- **P19**: 1800 秒の timeout。7 source の section は 673 秒で全部揃い、残り 1130 秒の Phase 2–3 で report.md を組む途中で切れた
- **P11**: section は 635 秒で揃い、report.md は 1700 秒。skills の 12 本ずつの分割は P11・P16・P19 のどれでも起きていない
  （items-skills.json が 1 本）
- 次に効く手は Phase 2–3 の短縮（cross-check を非 Keep 項目だけに絞る、report.md を sections の連結 + 衝突の追記にする）。
  Stage 0 の範囲外なので follow-up に回す

## 著者の 4 repo

A は修正前の skill（project mode の初版）、A2 は code review の修正を入れた現行 skill での再実行。jev-research-pipeline は
現行 skill で 1 回。

| repo | 項目 | 非 Keep | source 別 | 判断可能 | ≤600 s | section | 非 Keep | report | $ | 驚き |
|---|---|---|---|---|---|---|---|---|---|---|
| contemplative-agent (A2) | 75 | 22 | docs5 distill3 skills7 assets7 | 17 | 17 | 41 | 218 | 538 | 12.06 | ○ |
| zenn-content (A2) | 84 | 20 | docs5 agents4 distill2 skills3 assets5 rules1 | 16 | 16 | 41 | 150 | 516 | 8.99 | ○ |
| paper-lab (A2) | 32 | 16 | docs1 agents5 distill2 skills5 assets3 | 12 | 12 | 38 | 100 | 367 | 7.67 | ○ |
| jev-research-pipeline | 41 | 8 | docs1 agents1 assets6 | 7 | 7 | 44 | 135 | 623 | 7.23 | ○ |
| contemplative-agent (A) | 67 | 17 | docs4 distill3 skills6 assets4 | 13 | 13 | 42 | 239 | 530 | 9.16 | ○ |
| zenn-content (A) | 71 | 20 | docs5 agents5 distill1 skills4 assets4 rules1 | 16 | 16 | 40 | 132 | 516 | 8.98 | ○ |
| paper-lab (A) | 34 | 16 | docs1 agents5 distill2 skills4 assets4 | 14 | 14 | 42 | 102 | 415 | 4.58 | ○ |

同じ repo の A と A2 で非 Keep 件数は ±5 以内、驚きの判定は変わらない。

## 見立てと的中

見立て（P01–P10 から、P11 以降を回す前に commit d327ef6 で固定）: **skills < 10 かつ agents < 5 かつ hooks < 5 かつ CLAUDE.md < 50 行**
のときだけ驚きが出ない。

| id | 予測 | 結果 | 一致 |
|---|---|---|---|
| P11 | ○ | ○ | ✓ |
| P12 | ○ | ○ | ✓ |
| P13 | ○ | ○ | ✓ |
| P14 | ○ | ○ | ✓ |
| P15 | ○ | ○ | ✓ |
| P16 | ○ | ○ | ✓ |
| P17 | ○ | ○ | ✓ |
| P18 | × | ○（10） | ✗ |
| P19 | ○ | ○ | ✓ |
| P20 | ○ | ○ | ✓ |

9/10 一致で、事前の閾値（8 本以上）を越えた。ただし予測は 9 本が ○ で、ほぼ全部が驚くという母集団では「全部 ○」と言うだけで
9/10 に届く。見立ての中身（小さい harness だけ驚かない）は P18 で反例が出た: skills 5・CLAUDE.md 38 行でも、docs と assets
（使われていない設定・切れた参照）から非 Keep が出る。驚かなかったのは 20 本で P10 だけ。

## 3 分の設計（手順 5）

**2026-10-31 の初回実行の再生。** skill の commit 23:10 → source への dispatch（BRIEF.md）23:27 → 7 source が並列に 23:27–23:41（agents
が最初に 23:31、hooks が最後に 23:41）→ items-all 23:42 → report 23:43。約 33 分のうち 17 分は main loop が source skill を読んでから
dispatch するまでの時間だった。

**直したこと（commit 22c83e9）。** run の最初の行動で 7 source を並列に dispatch する（main loop は source skill を読まない）。各 source は
終わった瞬間に `items-<source>.json` と `sections/<source>.md` を書き、report はこれで埋まっていく。結果、公開 20 本で最初の
section は中央値 53.5 秒、最初の非 Keep は中央値 134.5 秒。

**source の順序。** plan は「非 Keep が出やすい順（初回: assets 先頭）」と書いたが、24 run の実測（公開 20 + 著者 4、並列時の
各 source の完了秒）では:

| source | 完了秒の中央値 | 最大 | 非 Keep が出た run |
|---|---|---|---|
| rules | 56 | 332 | 3/24 |
| hooks | 60 | 198 | 12/24 |
| agents | 124 | 426 | 13/24 |
| docs | 182 | 303 | 23/24 |
| distill | 202 | 393 | 21/24 |
| skills | 261 | 707 | 22/24 |
| assets | 318 | 535 | 23/24 |

assets は最も遅い source で、逐次実行で先頭に置くと最初の項目は 5 分を越える。並列実行では順序は効かないので、表の順は
Agent tool が無いときの逐次実行のためにある。「非 Keep が出る確率 ÷ 完了秒」の大きい順 — hooks → docs → agents → distill → skills →
assets → rules — に SKILL.md の表を並べ替えた。

## 失効条件の確認

- `/doctor` 系が横断の判定か branch 適用を native に持った — 比較時点（2.1.316）で持っていない（比較表）
- `--bare` が `-p` の既定になった — なっていない。ただし `--bare` は API key だけを受け OAuth を受けないので、subscription では
  plan の「`--bare` か `--settings` で切って」の `--bare` 側は使えない。隔離は `--restricted` と cwd 分離で行った
- 公開 20 本の半数で驚きが出ない — 19/20 で出た
- GitHub の 403 / 429・spam 判定 — 書き込みは無い。code search と clone だけで、rate limit 信号は 0 件

## 限界

- judge は 1 回ずつ、1 model。decidable の判定の再現性は測っていない
- 閾値 5 件は母集団に対して低すぎる（上の「見立てと的中」）
- 選定は `.claude/skills` に SKILL.md がある repo に限る。plugin 形式で配る harness は入っていない
- P16 と P19 は report.md が無く、judge には items から組み立てた表を渡した（他の 18 本とは judge の入力の形が違う）
