# advisory 封筒の共通化・bats 握り潰しの掃除・verify advisory channel

## Context

直前のセッション（`0c0b248`）が hooks/ と tests/ を触ったことで、`.notes/TASKS.md` Pending の
3 件が同時に着手条件を満たした。3 件とも `hooks/` の同じ面を触るので 1 つの作業窓で回し、
commit は性質ごとに 3 つに分ける。

調査で task 記載の前提が 2 つ精緻化された（どちらも作業量を**減らす**方向）:

1. **bats 握り潰しの機構が特定できた。** bats 1.13 は test body を `set -eET` + ERR trap で
   走らせる（upstream README: "each line is an assertion of truth"）。それでも握り潰しが
   起きるのは、この Mac の `env bash` が **bash 3.2.57** で、3.2 の errexit が `[[ ]]`
   （条件コマンド）に適用されないから。実測（`bash -c 'set -eET; trap … ERR; f(){ X; echo REACHED; }; f'`）:

   | 失敗コマンド | ERR trap | 後続行 |
   |---|---|---|
   | `false` | 発火 | 到達せず |
   | `[ 1 -eq 2 ]` | 発火 | 到達せず |
   | `[[ 1 == 2 ]]` | **発火せず** | **到達する** |

   → 危険なのは裸 `[[ ]]` **だけ**で、`[ ]` は安全。tests/ の裸 `[[ ]]` 32 箇所のうち
   「後続コマンドがある」= **4 箇所**（全部 `tests/harness-lint-precommit.bats`）。
   残り 28 は各 @test の末尾で実害なし。`set -e` 下の `hooks/*.sh` に裸 `[[ ]]` は **0 件**
   （production 側は無傷。この確認自体が本件の主目的の半分だった）。

2. **T-VERIFY-ADVISORY-CHANNEL の被害が local に実在する。** この repo 自身の
   `.claude/verify.sh` は staged mode の PASS 経路で `warn()` を 3 箇所出す
   （L136 shellcheck 不在 / L149 markdownlint 未導入 / L150 `[markdown advisory]`）。
   L140 のコメントが「advisory (ratchet 中): 検出しても commit は止めない。drain 後に
   check へ昇格する」と書いているとおり、これは**見えることを前提にした ratchet** で、
   今は hook が `$out` を捨てるので永久に drain しない。

ユーザー判断（本セッションで確認済み）: **advisory channel を設ける** /
**bats-autorun の PASS は要約 1 行**。

## 作業前

```
python3 ~/.claude/scripts/claims.py claim T-ADVISORY-ENVELOPE-HELPER --label "advisory 封筒 helper"
python3 ~/.claude/scripts/claims.py claim T-BATS-MULTI-ASSERT       --label "bats 裸 [[ ]] 掃除"
python3 ~/.claude/scripts/claims.py claim T-VERIFY-ADVISORY-CHANNEL --label "verify PASS advisory"
```

chain（skill: `implementation-chain`、種別 = fix + refactor + chore(hooks)）:
Simplify → Code Review / Security Review → Doc Sync → Verify。
**Simplify は Review 群より前**（working tree に fix を当てるため）。
`hooks/simplify-order-notice.sh` が reviewer 起動直前に発火するはずなので、発火の有無を
計器の生死として記録する（届かなければそれ自体を報告する）。

---

## Commit 1 — `refactor(hooks): advisory 封筒を 1 箇所に集約し、bats-autorun の壊れた封筒を直す`

### 新規 `hooks/_advisory-common.sh`

先例は `hooks/_session-common.sh` / `_git-target-common.sh`（単体では発火しない共有部品、
`${BASH_SOURCE[0]}` 相対で source、絶対パス起動の不変条件をヘッダに書く）。

封筒リテラルが**ファイル内に 1 つだけ**存在する形にする:

```bash
# emit_advisory_stream <event> [extra_top_level_json]   — 本文は stdin
emit_advisory_stream() {
  jq -Rs --arg e "$1" --argjson x "${2:-\{\}}" \
    '$x + {hookSpecificOutput: {hookEventName: $e, additionalContext: .}}'
}
# emit_advisory <event> <text> [extra_top_level_json]
emit_advisory() { printf '%s' "$2" | emit_advisory_stream "$1" "${3:-}"; }
```

`extra_top_level_json` は `systemMessage` / `decision` / `reason` を同居させる bats-autorun
のためだけの口。README L29-30 のとおりこれらは別チャネルでトップレベルに置く。

### 移行する 4 本

| hook | event | 置換対象 |
|---|---|---|
| `review-chain-notice.sh` | PreToolUse | L15-16 |
| `simplify-order-notice.sh` | PreToolUse | L130-131 |
| `contemplative-name-reminder.sh` | UserPromptSubmit | L37-42 |
| `task-claims-reminder.sh` | PostToolUse | L95-100（`jq -Rs` ストリーム版） |

`review-chain-notice.sh` は `set -euo pipefail`、`verify-precommit.sh` / `simplify-order-notice.sh`
は `set -uo pipefail`。helper は両方で安全に source できること（source 失敗時は `|| exit 0`）。

### `bats-autorun.sh` の実バグ（本 commit の fix 部分）

L71 / L76 はどちらもトップレベル `additionalContext` で、**PASS も FAIL も model に届いていない**。
FAIL が届いて見えるのは `decision`/`reason` という別チャネルのおかげで、そこには
「tests failed after editing X」しか入っておらず**出力本体は落ちている**。

- PASS: `systemMessage` は現状維持。additionalContext は**要約 1 行**
  （`bats: N tests passed (<file> 編集後)`。`N` は TAP の `^ok ` 行数）。
  全出力を載せると、封筒を直した瞬間に .sh を保存するたび 302 テスト分の TAP が
  毎回 context に入る — 封筒修正が文脈コスト回帰を連れてくるのを避ける。
- FAIL: `decision`/`reason` は**現状のまま**（実績のあるチャネルを触らない）＋
  封筒に出力本体を載せる（これまで落ちていた分が初めて届く）。長さ上限を掛ける
  （先行例: 前セッションの `claims.py open --oneline` 無制限長 HIGH）。
- 付随して `python3 -c 'json.dumps(...)[1:-1]'` の手組み JSON を廃し jq へ寄せる
  （helper が jq なので自然に消える。L60-64 の `[1:-1]` footgun コメントごと不要になる）。

### テスト

- 新規 `tests/advisory-envelope.bats` — helper を直接 source して封筒**そのもの**を検査
  （先例: `tests/git-target-extraction.bats`）。入れ子形 / `hookEventName` 同伴 /
  **トップレベル `additionalContext` が存在しないこと** / event 名の pass-through /
  extra JSON の merge / 引用符・改行・制御文字のエスケープ / 空本文。
- 各 hook の bats に散っている封筒 near-copy は **event 名 1 行**へ縮める
  （`tests/task-claims.bats:298-313`、`tests/simplify-order-notice.bats:140-151`、
  `tests/review-chain-notice.bats:56-61`）。
- `tests/bats-autorun.bats` には封筒テストが**現状 1 本も無い** — PASS 要約 / FAIL の
  decision+封筒共存 / トップレベル additionalContext 不在 を新規に置く。

### Doc

`hooks/README.md`: Shared 節に `_advisory-common.sh` の行を足し、L18-31 の封筒ブロックを
「唯一の実装は `_advisory-common.sh`、新しい hook はこれを source する」へ更新
（散文が正本だったから drift した、というのが本タスクの起点）。

---

## Commit 2 — `fix(tests): bash 3.2 の errexit が [[ ]] を飛ばす経路で握り潰されていた assertion を復旧`

1. **先に実測**（scratchpad に 1 ファイル）: 裸 `[[ ]]` と裸 `[ ]` を並べた .bats を
   実際の `bats` で走らせ、上の表を bats 経由でも再現する。Context の結論はプレーン bash
   での再現なので、bats 本体での確認を取ってから直す。
2. `tests/harness-lint-precommit.bats` の 4 箇所に `|| return 1` を付ける
   （L100, L131, L133, L286。repo の既存 idiom は `review-chain-notice.bats` にある）。
   4 つとも**現在は一度も検証されていない** assertion なので、付けた後に落ちないかを見る
   ＝ 落ちたら握り潰されていた本物の不具合。
3. **ratchet を置く**: 新規 `tests/bats-assertion-style.bats` が `tests/*.bats` を awk で
   走査し、「@test 内で後続コマンドがある裸 `[[ ]]`」を 0 件に固定する。一回の掃除で
   終わらせず、末尾にあった `[[ ]]` の後ろに 1 行足した瞬間に落ちるようにする。
   機構の説明（bash 3.2 / `[[ ]]` のみ / `[ ]` は安全）はこのファイルのヘッダを正本にし、
   他所へ複製しない。

残り 28 箇所の末尾 `[[ ]]` は**触らない**（実害が無く、ratchet が将来の劣化を捕まえる）。

---

## Commit 3 — `feat(hooks): verify ゲートの PASS 時 advisory を model へ届ける`

`hooks/verify-precommit.sh` L79 `[[ $rc -eq 0 ]] && exit 0` を置き換える:

```bash
if [[ $rc -eq 0 ]]; then
  [[ -n "$out" ]] || exit 0            # 無言 PASS は今までどおり無言
  emit_advisory PreToolUse "[verify] ゲートは PASS。以下は advisory:<capped $out>"
  exit 0
fi
```

- 長さ上限を掛ける（gate の stdout には repo 側ツールの出力が入り、ファイル名等の
  攻撃者選択テキストを含みうる。model が最も信用する経路に無制限長を流さない）。
- FAIL / rc=2 / rc=70-73 / timeout の各経路は**一切変えない**。
- 契約の更新: `verify-precommit.sh` ヘッダ L13「stdout = FAIL 時の検出行」と
  `skills/verify-bootstrap/SKILL.md:116`「PASS 時は無音に近く」を、
  「PASS 時の stdout は advisory として model に届く（無出力なら無言）」へ揃える。
- テスト（`tests/verify-precommit.bats`）: PASS + 出力あり → 封筒 / PASS + 無出力 → 完全に無言 /
  FAIL → 既存の block JSON のまま / 上限超過が切り詰められる。

---

## Verify

まとめて 1 コマンドにせず分けて回す（bats 全体は 2 分を超えることがある）:

```
python3 scripts/hooks/harness_lint.py
shellcheck -x hooks/*.sh
bats tests/            # 現状 302 通過・0 失敗が floor
```

さらに **本セッション自身が計器になる**:

- commit 1 で `hooks/*.sh` を編集した時点で `bats-autorun.sh` が発火するので、
  PASS の additionalContext が実際に届くかを実セッションで観測できる（前セッションが
  `task-claims-reminder` の到達を実測したのと同じ手）。届かなければ封筒の理解が
  まだ間違っているということなので、その時点で報告する。
- reviewer 起動時に `simplify-order-notice.sh` が発火するかを記録する。

## レビュー指摘の扱い

この diff が既に触っているファイル内で完結する指摘は**そのターンで直す**。
台帳（`.notes/TASKS.md`）へ送れるのは「別 commit になる」指摘だけ。
完了した 3 件は Done 節へ移し、`claims.py release --outcome done` を積む。
