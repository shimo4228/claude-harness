kind: internal
# Stage 1 — plugin `harness-stocktake` と「入れてから 3 分」の実測

as-of: 2026-11-01。plan [enumerated-petting-beaver](../enumerated-petting-beaver.md) Stage 1。Claude Code 2.1.316、audit は opus。

## 結論

- **判定は通った**: persona 3 体全員が README だけで install → `--dry-run` → report.md に到達。最初の非 Keep の section まで
  88–90 秒（中央値 89 秒、目標 3 分以内）、report まで 276–294 秒。sample harness の bench で `total_cost_usd` が記録された
- bench（sample harness、install から）: install 1 秒、最初の section = 最初の非 Keep 87 秒、report.md 242 秒、$4.08、29 項目・非 Keep 22
- 費用（API 換算）: bench $4.08 + persona の audit $3.90 / $3.62 / $4.33 + persona 本体 $0.14 × 3 + 確認用の小呼び出し ≒ **$13**（予算 $40）
- readme-judge: draft で Fix（13 点）→ span 修正 → recheck で Fix（span 3 点: 使用履歴の範囲、ledger の置き場所、Runs に uv）→ 直して終了（2 往復の上限）。recheck の 6 問は 0 No

## 計測の形と plan からのずれ

- plan は「一時 `CLAUDE_CONFIG_DIR` + `claude -p`」。一時 config / 一時 HOME では subscription のログインが引き継がれない
  （`Not logged in`）。認証ファイルを写すのは token の rotation で本体のログインを壊しうるので採らなかった
- 代わりに: **install は一時 `CLAUDE_CONFIG_DIR` で README の 1 行どおり**（認証不要）、**audit は本物の認証のまま**
  install された cache の実体を `--plugin-dir` で読み、`--setting-sources local`・`disableAllHooks`・`claudeMdExcludes`（`~/.claude`）・
  `--strict-mcp-config` で切る。対象は `--project <sample harness>`。著者の user skill の一覧は外せない（flag が無い）
- GitHub repo は未作成（下記）。install の source は `shimo4228/harness-stocktake` の代わりにローカル checkout の path。
  GitHub からの install（private repo の clone）は未検証
- persona は `claude -p --model sonnet`（persona の system prompt、README は `<details>` の中身を伏せた版）。`claude` は shim で、
  `plugin ...` は一時 config へ、`-p "/harness-stocktake:..."` は上の隔離 audit へ渡し、persona の「`~/.claude`」を sample harness の
  `--project` に読み替える。shim と driver は scratchpad（session 限り）

## persona 3 体

| persona | 到達 | 最初の非 Keep | report | 詰まった所（sandbox 由来を除く） | 続けるか |
|---|---|---|---|---|---|
| ECC を入れたままの人 | ○ | 89 秒 | 294 秒 | `-p` では許可を先に渡す必要がある / project mode では使用履歴の検査が n/a | maybe（行を読んでいない・費用と時間） |
| CLAUDE.md 200 行の tech lead | ○ | 88 秒 | 276 秒 | `-p` で各 command を見ずに許可した | maybe（行を repo と突き合わせてから） |
| `/doctor` で足りると思う人 | ○ | 90 秒 | 278 秒 | 進捗が見えない / 英語 report に 未確認 が混じる / context-sync の script が `python3 -I` で落ちた | maybe（/doctor が出さない cross-file の指摘は本物） |

sandbox 由来で README では直らない詰まり: audit 先が `../harness` に読み替えられて見えたこと、report.md が persona の許可 dir の外で
開けなかったこと。3 体とも summary だけで判断しており、「行を読んで確かめたい」が共通の留保。

README で直した: 前提（Claude Code 2.1.275+・git・Python 3.11+・uv）、`claude -p` の許可つきの形、`sections/` を開けば進捗が見える、
dry-run の report は読む用で承認は dry-run なしの run、使用履歴の検査は log があるときだけ（無ければ `/doctor`）。skill 側で直した:
未確認 を report 言語に合わせる。

## 未解決（follow-up）

- ~~context-sync の `context_evidence.py` が `python3 -I` で落ちる~~ → d3035af（直接起動 branch で script の dir を sys.path に入れる、-I の回帰テスト）
- ~~ledger が plugin の install folder の中にあり apply branch に載らない~~ → 3063da7 で監査対象の `<harness>/stocktake/<skill>.json` へ。
  sample harness の `--dry-run`（skills のみ、$1.28）で、置いた台帳を新しい path から読み、apply 時の書き込み先も同じ path と確認
- ~~skill-stocktake の URL 検査が plugin では常に n/a~~ → 2d35b81 で skill-health を同梱（readme-judge recheck の外側の指摘も同じ根）。
  plugin の配置で `${CLAUDE_SKILL_DIR}/../skill-health` の scan_refs → url_liveness が動くことを直接確認。sample harness の
  `--dry-run`（$1.24）は sample の skill が URL を持たず、report に URL 検査の記録が残らないので、この確認には使えなかった
