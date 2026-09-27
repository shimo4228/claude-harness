# commit の門を hook に一本化し、rules を事実だけに絞る

## Context

`implementation-chain` 周りの hook 実行が冗長だった。経緯は ADR-0018（2026-07-25）の rightsize で
Review 実行確認文が rules から消え、遵守率が落ち（codex-review 54% → 20%）、その穴を hook で
塞いだこと。以後、名簿が rules と hook と skill の 3 箇所に散り、commit のたびに 827 bytes の
リマインダが注入される状態になっていた。

**方針は「hook を消して rules に戻す」ではなく、層の役割を分け直すことにした。**

| 層 | 持つもの | 理由 |
|---|---|---|
| **hook** | 発火時刻と名簿 | commit の瞬間に決定論的に鳴る。カバレッジ 93%（ADR-0028 実測） |
| **rules** | この環境の事実と配線 | 毎セッション常駐。思考や行動のプロセスは置かない |
| **skill** | 手順 | 呼んだ瞬間に読まれる |

この分け方が可能になったのは条件が変わったからである。ADR-0027 が「時刻に紐づく動詞は rules」と
判断したとき、hook は **13%** の commit でしか鳴っていなかった（ADR-0028:33 の実測）。閾値撤廃で
**93%** に上がった今、動詞も hook が運べる。**「hook だけで名簿を運ぶ」条件は一度も試されて
おらず、20% という数字はそれを否定する証拠にならない。**

## 決定事項（インタビューで確定）

1. `review-chain-notice.sh` の **commit 面は残す**。ただしメッセージを圧縮して冗長さに直接答える
2. Review 名簿の正本を **hook 1 箇所に一本化**し、`planning.md` から落とす
3. `human-gate.md` は**全面廃止、代替を置かない**（substrate 既定に全面委譲）
4. `output-register.md` も廃止
5. 廃止する hook は **4 本** — `evidence-file-notice.sh` と空転している Stop 3 本
6. `contemplative-axioms.md` は **verbatim 維持**（ADR-0018 (c) の著者判断を上書きしない）
7. rules は「**事実と配線だけ残す**」基準を適用。ただし `akc-cycle.md` の Scaffold Dissolution は
   残す（3 つの skill が定義として import している = 配線）
8. 公開 repo `shimo4228/human-gate` は**残して退役を明記**
9. 記録は**新規 ADR 1 本**（ADR-0035）にまとめる
10. 公開同期は**ローカル完了後に同じ作業で**実施

## Phase 1 — hook 層の整理

### 廃止する 4 本

| hook | 配線 | 廃止理由 |
|---|---|---|
| `hooks/evidence-file-notice.sh` | PreToolUse(Bash) | human-gate.md の検出面。rule 廃止で根拠が消滅する |
| `hooks/driftcheck.sh` | Stop | `exit 0` + stderr は debug log にしか行かず、モデルにもユーザーにも届かない（T-STOP-HOOK-CHANNEL で実証済み） |
| `hooks/search-first-verdict-check.sh` | Stop | 同上。実体の `scripts/hooks/search-first-verdict-check.py` と `tests/search-first-verdict-check.bats` も削除 |
| `hooks/dotclaude-dirty-check.sh` | Stop | 同上 |

`settings.json` の `hooks.Stop` はブロックごと削除（3 本すべてが対象で配列が空になる）。
`PreToolUse` の `Bash` matcher から `evidence-file-notice.sh` の 1 エントリを外す。

### 残す 1 本 — `review-chain-notice.sh` の commit 面

**Stop 分岐をスクリプトから削除する。** 2026-08-02 に配線を外した時点で、復帰には指紋抑制の
実装が必要になっていた（T-REVIEW-NOTICE-NOISE）。今回 commit 面を正式な正本にする以上、
使わない分岐と `tests/review-chain-notice.bats` の Stop ケースは維持コストでしかない。
**これは指紋抑制で Stop へ戻す選択肢を放棄することを意味する**ので、ADR-0035 に明記する。

**メッセージを 827 bytes → 400 bytes 以下に圧縮する:**

| 削る箇所 | 理由 |
|---|---|
| 末尾の「review はテストが通っても残る欠陥（認可・並行性・設計盲点・injection 面）を見る別の層です」 | 毎回同一文字列で、2 回目以降の情報量がゼロ。1 文に畳む |
| ADR 区分の括弧内（「記録の検査: Context が検証可能な根拠を持つか / …」） | `adr-reviewer` agent の description が同じ内容を運ぶ |
| shaping 区分の `human-gate.md により本文提示が必要` | 参照先の rule が消える。「本文を人間に提示」だけ残す |
| `repo 由来の未検証データ: {ファイル名 3 件}` の echo | ADR-0034 自身が「`?` に潰れて特定できない」と自認している。**削ると prompt injection 面が丸ごと消える**（同 ADR が実証した注入経路）。件数だけで検出の目的は満たす |

**名簿に不足がないか確認する** — `planning.md` から名簿を落とすので、hook が唯一の正本になる。
現行の hook は code / shaping / ADR の 3 区分で code-reviewer・python-reviewer・
security-reviewer・codex-review・adr-reviewer を名指しするが、`swift-reviewer` と
`refactor-cleaner` が入っているか実施時に確認して補う。

### 共有部品と残る決定論ゲート

`hooks/_git-target-common.sh` は残る 6 本（secret-scan / verify / bandit / ruff-format /
harness-lint / review-chain-notice）が source しており**無変更**。
`tests/git-target-extraction.bats` も継続。

## Phase 2 — rules の再 rightsize（3,170 → 約 900 words、-72%）

**基準: 常駐に残すのは「この環境の事実・配線・固有の罠」だけ。思考や行動のプロセスを
規定するものは、それがどれだけ良い意見でも降格する。**

ADR-0018 の基準（substrate と重複するか）より鋭い。前者は重複を見つけ、後者は
over-constraint を見つける。判定は「調べれば分かる事実か、考え方の指示か」。

**例外は 2 件だけ**（ADR-0035 に列挙して、次に監査する人が理由を引けるようにする）:

1. **他資産が定義として import している概念** — Scaffold Dissolution。3 本の skill が
   Dissolve 判定の基準として引いており、意見ではなく配線として機能している
2. **価値層の宣言** — `contemplative-axioms.md`。命令形を含むが行動手続きではなく、
   ADR-0018 (c) の著者判断で常駐が確定している

（当初あった第 3 の例外「遅延発火する手続き = commit の門」は、名簿を hook に移したので消えた）

### 残す 10 ファイル

| ファイル | 現状 | 後 | 残す中身（＝この環境の事実） |
|---|---:|---:|---|
| `contemplative-axioms.md` | 317 | 317 | **無変更** |
| `akc-cycle.md` | 248 | ~100 | Scaffold Dissolution（2 ベクトル + 世代交代トリガー）と、ローカル版である旨の 1 行。Phase → skill 対応表と Measure / Maintain の注意は削る |
| `CLAUDE.md` | 215 | ~110 | Origin Policy / Change Target / 新プロジェクト規約 |
| `planning.md` | 494 | **~70** | Phase 0 は `/search-first` を呼ぶ（skill 名の配線）/ Verify は `.claude/verify.sh` と doc sync と `git status`（機械が持たない 2 項目のみ）/ 2 介入点 1 行。**Review 名簿は hook へ移す** |
| `skills.md` | 217 | ~60 | `origin:` 規約の表 / `commands/` は使わない / Global vs Project 1 行 |
| `security.md` | 202 | ~60 | hook 配線と BYPASS の変数名 / `verify_allow.py` の承認台帳 / LLM 信頼境界 1 行 |
| `coding-style.md` | 229 | ~55 | git 追跡下は `git rm` で足りる / batch 承認は償却されない / Change Target |
| `debugging.md` | 180 | ~35 | **Rate limit は警報であって障害ではない のみ**（2026-07-16 のアカウント block で実証） |
| `agents.md` | 181 | ~30 | Author-Reviewer は別プロセス / cross-agent は ADR-0015 ポインタ / herdr ゲート 1 行 |
| `task-tracking.md` | 159 | ~30 | 台帳は `.notes/TASKS.md` 1 ファイル |
| `testing.md` | 149 | ~25 | カバレッジ 80% / 本番では走らせない |

### 廃止する 4 ファイル

| ファイル | 現状 | 廃止理由 | 受け皿 |
|---|---:|---|---|
| `human-gate.md` | 238 | 決定済み（substrate 既定へ全面委譲） | なし |
| `patterns.md` | 172 | Code vs LLM も documented-invariant → ゲート化も、良い意見だが思考の規定。参照している skill は 1 本のみで、専用 skill が受け皿として既にある | `skills/when-code-when-llm` + learned note `documented-invariant-lint-gates.md` |
| `hooks.md` | 108 | hooks vs skills の判定は思考の規定。外部スクリプト分離は `hooks/README.md` が持つ | `hooks/README.md` |
| `output-register.md` | 61 | 決定済み | なし |

ファイル数 14 → 10（+ CLAUDE.md）。各ファイル先頭の `rationale:` / `review-when:` コメントは
harness_lint の検査対象なので**更新する**（ADR-0035 を指す）。

**`akc-cycle.md` と `patterns.md` を分けた理由**（ADR-0035 に記録）: 前者は
`generation-audit` / `agent-stocktake` / `rules-stocktake` の 3 本が Dissolve 判定の
**定義として import** しており、かつ AKC 配布版は設計意図の異なる別物なのでローカルに正本が要る。
後者は参照が `verify-bootstrap` 1 本だけで、`when-code-when-llm` という専用 skill
（公開 repo でもある）が正本を持てる。

### そのまま消す「思考の規定」（ADR-0035 に列挙）

降格でも吸収でもなく消すもの。後から「なぜ消えたか」を引けるようにする:

- `debugging.md`: 仮説 → 証拠 → 確認待ち → 修正のフロー全体、禁止 3 項目、リーセンシーバイアス注意
  — **確認待ちは substrate と衝突していた**（既定は「どう仮定しても危険か無意味な場合だけ止まる」）。
  消すと挙動が変わる: 原因を報告したうえで修正まで進むようになる
- `planning.md`: What / Why / Alternatives、証拠ベース意思決定、複雑性チャレンジ、
  Prototype Before Scale、「Stop hook が Verdict の存在を検査する」（**事実として偽** — 届いていない）
- `coding-style.md`: 既定はイミュータブル、Iteration Bounds、Reversibility Gate の判定 3 問
- `akc-cycle.md`: Phase → skill 対応表、Measure / Maintain の注意
- `security.md`: secret をハードコードしない等の一般論

## Phase 3 — 降格先と参照の de-link

### 降格先（既存の受け皿を使う。新規 skill は作らない）

| 内容 | 降格先 | 状態 |
|---|---|---|
| Code vs LLM seam | `skills/when-code-when-llm` | 既存 skill。確認して不足分のみ追記 |
| documented-invariant → ゲート化 | `skills/learned/documented-invariant-lint-gates.md` | 既存 note |
| hooks vs skills の判定 / 外部スクリプト分離 | `hooks/README.md` + `skills/learned/claude-code-tool-patterns.md` | 既存。後者は `rules/common/hooks.md` を「正本」と指しているので**正本を note 側に戻す** |
| Phase 0 の Verdict 表（Adopt / Extend / Compose / Build） | `skills/search-first` | 確認して不足分のみ |
| 証拠ベース意思決定 / Prototype Before Scale | `skills/implementation-chain` | 確認して不足分のみ |
| 複雑性チャレンジ（トリガーワード・ROI 表） | `agents/architect.md` | 既に essence evaluator。確認のみ |
| Reversibility Gate の判定 3 問・soft-delete の詳細 | `skills/config-gc` | 確認して不足分のみ |
| MagicMock の罠 | `skills/python-patterns` | 確認して不足分のみ |
| 台帳の解決順序・形式・卒業パス | `skills/task-stocktake` | 確認して不足分のみ |
| Knowledge Placement / Global vs Project | `skills/skill-creator` | 確認して不足分のみ |

### 先に確認する依存

`akc-cycle.md` の Scaffold Dissolution は 3 本の skill が正本として import している
（`generation-audit:14,111` / `agent-stocktake:253` / `rules-stocktake:94`）。**残す判断に
したのでポインタは無傷**。圧縮するとき、この 3 本が引く「2 ベクトル」と「第 3 トリガー =
世代交代」の記述を削らないこと。

### de-link が必要な参照

harness_lint の check 5 は **`docs/` 配下も走査する**。inline code の bare path は
`strip_code` で除外されるが、`[text](path)` 形式は落ちる。

| 削除対象 | 参照元 |
|---|---|
| `human-gate.md` | rules: `planning.md:83,108` / `coding-style.md:31` / `debugging.md:15` / `rules/README.md`<br>skills: `harness-sync:48,160` / `implementation-chain:146-149` / `readme-writer:344` / `public-comment:67` / `verify-bootstrap:16,157,209`<br>hooks: `hooks/README.md:33` / `review-chain-notice.sh:25,173,187,229` |
| `patterns.md` | rules: `rules/README.md:34`<br>skills: `verify-bootstrap:210`<br>**docs/adr: `0019:20,138,232`（markdown リンク = lint FAIL 確定）/ `0016:94` / `0033:84,101,129` / `0034:262`** |
| `hooks.md` | rules: `rules/README.md`<br>skills: `claude-code-tool-patterns.md:17`<br>hooks: `hooks/README.md:129`<br>**docs/adr: `0011:17` / `0034:220`** |
| `output-register.md` | rules: `rules/README.md:13,33`<br>**docs/adr: `0030:36,91`** |

**ADR 本文の参照は「退役先を注記して de-link」する**（harness_lint のエラーメッセージが指す作法）。
過去の判断記録なので参照を消すのではなく、`patterns.md` → `skills/when-code-when-llm` のように
現在の所在を併記する。実施時は
`grep -rn "rules/common/\(patterns\|hooks\|human-gate\|output-register\)"` で全 checked パス
（`rules/` `skills/learned/` `agents/` `docs/`）を洗い直す。

`rules/README.md` は構成図・履歴・判定基準を全面的に書き直す（14 → 10 ファイル、新基準を明記）。
`harness-sync/SKILL.md` は human-gate 行を sync 対象から外す。akc-cycle 行は無変更。

## Phase 4 — 記録

### 新規 ADR-0035

`commit の門を hook に一本化し、rules を事実だけに絞る`。ADR テスト 3 条件を満たす。

Context に「hook 13% → 93% で条件が変わった」を置き、Alternatives に
「hook を全廃して rules に名簿を戻す」「二重化を維持する」「rules も削らず hook だけ消す」を書く。
Consequences に**受け入れたコスト**を明記する — 名簿の正本が 1 箇所になったので
**hook が壊れると検出がゼロになる**（二重化を捨てた帰結）、Stop 復帰の選択肢を放棄した、
`debugging.md` の確認待ち削除で挙動が変わる、の 3 点。

### 既存 ADR の Status 追記

| ADR | 追記内容 |
|---|---|
| 0019（human-gate 層） | superseded — rule 全面廃止、substrate 既定へ委譲 |
| 0027（Review 実行確認を rules へ復元） | superseded — 名簿を hook へ再移設。**前提（hook カバレッジ 13%）が失効**したため |
| 0028（review-notice full scope） | **accepted のまま維持** — 本 ADR はこの hook に依存する |
| 0030（output-register 分離） | superseded — rule 廃止 |
| 0034（Stop 配線） | superseded — Stop 分岐をスクリプトごと削除 |
| 0018（rightsize） | 追記 — 本 ADR が第 2 波。**基準が変わった**ことを明記 |

**`docs/adr/README.md` のインデックスも同じ diff で更新する。** 現在 0019 / 0027 / 0030 / 0034 の
4 行が `accepted` のままで、要約文も削除済みの rule / hook を現存として記述している。

### 台帳 `.notes/TASKS.md`

- **廃棄**: `T-REVIEW-NOTICE-NOISE`（Stop 分岐ごと削除するので復帰対象が消える）/
  `T-STOP-HOOK-CHANNEL`（Stop 3 本すべて消滅）
- **更新**: `T-GIT-HOSTILE-CONFIG` の対象を残る 5 本に絞る。参照実装（`review-chain-notice.sh`
  の `GIT` 配列）は**残るので手順は引ける**
- **維持**: `T-SIGPIPE-HEAD-PIPE`（`ruff-format-precommit.sh:113`）。参照テストも残る
- **新設**: `T-HOOK-ONLY-ROSTER` — 下記の計測

## Phase 5 — 公開反映

1. `harness-sync` で `~/MyAI_Lab/claude-harness` を更新。公開中の rules 9 ファイルのうち
   **2 本が消え**（human-gate / output-register。patterns と hooks は元々未公開）、残り 7 本が縮む。
   README の自動生成 rules 表も再生成
2. `~/MyAI_Lab/human-gate` の README / README.ja / CHANGELOG に退役を追記 —
   「2026-08-02 に著者のハーネスから退役。理由は substrate による吸収（scaffold dissolution）」。
   **repo は archive せず削除もしない**。
   あわせて `human-gate/scripts/sync-from-local.sh` を**退役 abort に置き換える** — 同スクリプトは
   `~/.claude/rules/common/human-gate.md` と `hooks/evidence-file-notice.sh` の存在を前提に
   guard を掛けており、両方消えると「同期できるはずのものが壊れている」という誤ったエラーを出す
3. `~/MyAI_Lab/akc-cycle` の rule 部分は**同期しない**（ADR-0018 の注記どおり、配布版は
   skill 未導入環境向けの自己完結版で設計意図が異なる）

## 計測と撤退基準（T-HOOK-ONLY-ROSTER）

検証する仮説は「**93% 鳴る hook だけで名簿を運べる**」。

**先に制約を書く**: `metrics/*.jsonl` は `{ts, event, agent|skill, project}` のみで、
セッション ID も commit ID も持たない。**reviewer 起動を個々の commit に紐づけることはできない。**
測れるのは「日 × repo」の粒度まで。

- **母数**: `~/.claude` repo の `feat` / `fix` コミット数
- **分子**: 同じ日・`project` が `~/.claude` の `codex-review` invoke 数（`skill-usage.jsonl`）。
  skill-comply の合成シナリオは除外（ADR-0027 と同じ扱い）
- **窓**: 変更の翌日から feat/fix が **20 件**溜まるまで
- **比較先は回復後ではなく劣化後にする** — 08-01 / 08-02 は交絡した処理を含み n も小さい

| 期間 | 状態 | codex / feat-fix |
|---|---|---:|
| 07-05〜07-24 | rightsize 前（rules に名簿・hook 13%） | 0.54 |
| 07-25〜07-31 | rules から名簿消失・hook 13% | **0.20** |
| 08-01〜08-02 | rules に名簿・hook 93%（交絡） | 0.76 |

- **判定閾値**: 窓の期間で **0.35 を下回ったら仮説を棄却**（劣化水準 0.20 と rightsize 前 0.54 の
  中点）。0.90 と 0.60 を区別する必要はない — 検出したいのは 0.20 への逆戻りだけ
- **棄却時の対処**: `planning.md` に名簿を戻す（二重化へ回帰）。hook の Stop 面は復活させない
- **判定できなかった場合**: 20 件溜まらなければ**判定を延期して台帳に残す**。少数で判定しない

## Verification

```bash
# 1. 常駐語数の実測（目標 ~900 words / rules 10 ファイル + CLAUDE.md）
wc -w ~/.claude/rules/common/*.md ~/.claude/CLAUDE.md

# 2. harness_lint（リンク解決・origin・rationale/review-when・See skill ポインタ・hook 参照整合）
python3 ~/.claude/scripts/hooks/harness_lint.py

# 3. 削除した 4 hook がどこからも参照されていないこと
grep -rn "evidence-file-notice\|driftcheck\|search-first-verdict-check\|dotclaude-dirty-check" \
  ~/.claude --include="*.md" --include="*.json" --include="*.sh" --include="*.py"

# 4. 残る hook の回帰テスト（review-chain-notice.bats は Stop ケースを削除して継続）
bats ~/.claude/tests/*.bats

# 5. 圧縮後のメッセージ長を実測（目標 400 bytes 以下）
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m x"}}' \
  | bash ~/.claude/hooks/review-chain-notice.sh | wc -c

# 6. commit 境界の決定論ゲートが生きていること
git -C ~/.claude status
```

さらに**次セッションで実挙動を確認する** — 新しいセッションを開き、rules が 10 ファイルで
注入されること、削除した hook の `system-reminder` が出ないこと、commit 時に圧縮後の
リマインダが 1 回だけ出ることを目視する。

## Review chain

`chore`（設定・rules・hook の変更）+ 公開反映。実施時は code-reviewer（shell / json 変更）、
security-reviewer（hook のメッセージから untrusted データの echo を削るため）、
codex-review（rules 削減の妥当性を別モデルで）、ADR-0035 に adr-reviewer を回す。
