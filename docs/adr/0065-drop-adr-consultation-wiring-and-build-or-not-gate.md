# ADR-0065: 新規アイデアへの制動を外す — ADR 照合配線の撤去、memory 却下記録の削除、Build-or-not 4 問の廃止、「することだけを書く」原則

## Status

accepted

## Date

2026-09-14

## Context

著者は 2026-09-14、普段のセッションで Claude Code が新しいアイデアに取り組むことを拒む、という
観測を報告した。拒む根拠の頻度は著者申告で ADR > memory > Build-or-not 4 問の儀式の順。
search-first は別セッションで再設計中のため本 ADR の対象外とする。

本セッションの Explore agent 2 本による調査結果: SessionStart hook は文脈を注入せず、block する
hook は commit 境界（secret-scan / verify / bandit / ruff / harness-lint）と危険コマンド
（validate-bash）だけである。常駐 rule は 13 ファイル / 297 行。ADR は 64 本（accepted 約 50、
`## Review-when` あり 22 — `ls docs/adr/[0-9]*.md | wc -l` / `grep -l '^## Review-when' docs/adr/*.md | wc -l`）。memory は 46 ファイル / 1,774 行で、「しない / 不要 / 禁止 / 却下 /
再提案しない」を含む行が約 80 ある。

「変更前に ADR を確認せよ」型の配線は 5 箇所ある: `AGENTS.md:9`（「変更前に関連 ADR を確認する」）、
`skills/grill-me/SKILL.md` rule 3（Date / Review-when を先に読み前提 Z を問う protocol）、
`agents/architect.md` の ADR / memory ガード 2 箇条、`rules/common/akc-cycle.md` の「ADR も足場で
ある」「却下記録の読み方」2 節（24 行）、`docs/adr/README.md` の template 前文。

[ADR-0044](./0044-adr-review-when-and-dated-annotation.md)（2026-08-19）は同じ観測に対し「読み方
protocol」（ADR は日付つき仮説、発散段階で却下記録を反証に使わない）を上記 5 箇所へ配線した。
26 日後の本日も観測が続いている。ADR-0044 の Alternatives には「ADR を廃止し
desire-frontier のように仮説台帳だけにする — 未決、再訪条件: Review-when 導入後も『ADR に縛られる』
観測が続いたら再訪する」があり、この再訪条件が発火した。ADR-0044 の Context は「この害の事例記録は
0 件」をベースラインとしており、本日時点でも記録された事例は著者の主観的観測のみである。

Build-or-not 4 問（①存在すべきか ②適正な大きさ ③誰が消費するか ④失効条件）は commit `1d4c4cf`
（2026-08-25）で `rules/common/planning.md`、`skills/implementation-chain/SKILL.md`（feat/chore ×
Build-or-not 行と fix × 機構ゲート行）、`agents/architect.md` ヘッダコメント、
`skills/rfc-writer/SKILL.md` 対応表に入った。所有 ADR は無く、実測根拠として外部 repo の CA
ADR-0095 を引いていた。著者（2026-09-14）:「プランファイルに儀式的に入っているが意味がないので
削除してくれ」。

著者（2026-09-14）:「ADR のしない型の書き方やめて。しないのなら記述しなくていい。するなと言われた
ら結局想起するから何も言わない方がマシだろ。これこそ rules にすべきことかもしれないな」。本
セッションで `claude --safe-mode` を probe した結果、CLAUDE.md / rules / skills / hooks / MCP /
auto-memory が全て落ち、auth と permission allowlist（auto mode）だけが残ることを確認した
（`--bare` は ANTHROPIC_API_KEY 必須で subscription では使えない）。これを使う「frontier セッション」
案を提示したところ著者:「なんで safe-mode の話が出てくるの？いちいち safe-mode に切り替えるって
こと？」— 要件は普段のセッションのままで新しいアイデアに乗れることである。

## Decision

1. ADR 照合配線を撤去する。`AGENTS.md:9` を「設計判断の記録は docs/adr/。既存機構を変更するとき
   経緯を読む」に置換する。`rules/common/akc-cycle.md` の「ADR も足場である」「却下記録の読み方」
   2 節を削除し、「ADR の扱い」1 節 3 行（ADR は日付つきの経緯記録 / 既存機構を変更するとき経緯を
   読む / 新しい判断が旧 ADR と衝突したら supersede し旧 ADR に
   `> **注記（YYYY-MM-DD, ADR-NNNN）**` を残す）に置換する（57 → 38 行）。`skills/grill-me/SKILL.md`
   rule 3 は「読んで分かる決定は文書から取る」までに縮める。`agents/architect.md` の ADR / memory
   ガード 2 箇条を削除し、ヘッダコメントを「判定は常に最強モデルで。fable が引けない場合のみ opus」
   に縮め、planning.md への幽霊参照 2 箇所を外す。`docs/adr/README.md` 前文、`rules/README.md` の
   akc-cycle 行、`skills/adr-writer/references/review-findings.md:10`、
   `scripts/hooks/harness_lint.py` のコメントを新節名に合わせる。ADR との関係は `agents/adr-reviewer.md` §7
   （ADR を書く時の先行 ADR との関係チェック）と implementation-chain Doc Sync の「所有 ADR の追補」
   行が引き受ける。ADR-0044 Decision 1・2・3・5・6（Review-when 節、注記規約、lint）は現行のまま。
2. memory の却下記録を削除する（`projects/-Users-shimomoto-tatsuya--claude/memory/`、git 管理外。
   セッション scratchpad に一時退避した上で実施する）。削除 14 ファイル — 外部ツールの却下記録 3
   （`reference_delta_deltadb_observation` / `reference_skillevaluator_pilot` /
   `project_writing_agent_pi`）、skill / ADR へ昇格済み 7（`feedback_abstraction_trap` /
   `feedback_skill_design_intent` / `feedback_autonomous_trigger_ceiling` /
   `feedback_redundant_channel` → skill-creator §2、`feedback_git_dash_c_over_cd` →
   git-workflow、`feedback_python_review` → [ADR-0039](./0039-retire-python-reviewer-simplify-in-chain.md)、
   `reference_skill_creator_loop_gotchas` → [ADR-0046](./0046-skill-creator-shrink-in-place-and-creation-gate.md)）、
   判断が [ADR-0002](./0002-disable-claude-mem.md)〜[ADR-0007](./0007-open-concept-network-effect.md)
   に移った session log 4（`session-2026-02-23` / `03-13-scout` / `03-20-skill-comply` /
   `03-24-context-sync`）。編集 4 ファイル — `reference_herdr_setup`（herdr-ctx の「再提案しない」、
   `switch_ascii_input_source_in_prefix` の「再有効化しないこと」、link_handlers の「不要と判断」の
   3 文を削除し、音の扱いを「通知は視覚のみ（家庭内制約）」の記述に統一する。他の見送り記録は理由
   つきの事実として残る）、`user_depth_over_breadth`、
   `feedback_deterministic_semantic_layering`、`feedback_permission_mode_preference` は否定形の文を
   することの記述に置換する。
   `MEMORY.md` は削除行と「履歴」節を消し、残る hook から却下語を外す（66 → 46 行）。memory 全体は
   46 → 33 ファイル（−14、Decision 4 で +1）、1,774 → 1,166 行になる。
3. Build-or-not 4 問を削除する。`rules/common/planning.md` の該当箇条（3 行）を削除する
   （17 → 14 行）。`skills/implementation-chain/SKILL.md` の feat/chore × Build-or-not 発動条件行を
   削除し、fix × 機構ゲート行を「足すなら plan にその旨と大きさを 1 行書く」に置換する（CA
   ADR-0095/0098 の根拠句は残す）。`skills/rfc-writer/SKILL.md` 対応表の Build-or-not 行を削除する。
   agent `architect` は user / skill が明示的に呼ぶ opt-in agent として残し、task-triage /
   loop-design-check / harness-boundary / mondo からの「contested な build-or-not は architect
   へ」のポインタはそのまま置く。
4. 「することだけを書く」原則を配線する。`rules/common/skills.md` に 1 文「することだけを書く。
   やめる項目は本文から消す」を置く。正本は `skills/skill-creator/SKILL.md` §3 — 先頭 bullet を
   「することだけを書く」に書き換え（grep 可能な検出語・自己執行力のある規則・数値閾値は原文の
   まま残す — ADR-0058）、tombstone の bullet を「退役したものは本文から消す」に書き換える。
   §4 草稿ゲートの Hygiene 問と `agents/adr-reviewer.md` §8（Decision / Review-when / Consequences が
   対象）に「本文が『すること』で書かれているか」の検査項目を 1 つずつ足す。memory `feedback_write_only_what_to_do.md` を書き MEMORY.md に 1 行
   置く。検査は意味的ゲート（adr-reviewer §8 / skill-creator §4 草稿ゲート）が担う。

   > **注記（2026-09-16, ADR-0070）**: 本項の絶対形「することだけを書く」は「既定は肯定形。
   > 禁止は grep 可能な具体的動作・観測済み・機械ゲート無しの 3 条件を満たすときだけ、理由 1 句付き」に
   > 緩めた。文体・内部過程への禁止は肯定形のまま。外部由来の未改変 prompt は対象外。

## Review-when

- 著者が「ADR / memory を根拠に新規アイデアを拒まれた」と観測したら、その場で `MEMORY.md` の
  Pending 節に日付つき 1 行（何を提案し、どの ADR / memory が根拠に挙がったか）を残す。
  2026-10-12（4 週間後）以降にその行が 1 件でもあれば、ADR-0044 の未決 Alternative「ADR を廃止し
  仮説台帳だけにする」を実行する。0 件なら本 ADR の第 1 項は満了とし、この行を Neutral へ移す。
- 無人 build chain が大きさの宣言なしに機構を足して肥大する事象（CA ADR-0095 型）が再発したら、
  機構ゲートを build-tier の dispatch packet 限定で戻す（agent `architect` を packet 側で呼ぶ）。
- substrate が決定記録の鮮度管理（日付・失効条件の照合）を native に持ったら、akc-cycle の
  「ADR の扱い」節は downward dissolution の対象にする。

## Alternatives Considered

### `--safe-mode` で起動する frontier セッション（launcher script + 短い stance）

本セッションで probe し、rules / memory / hooks が落ち auth と allowlist が残ることを確認した。
著者の要件は「普段のセッションのままで新しいアイデアに乗れること」で、セッション形式の切替はその
要件の外。採らない。

### 読み方 protocol を命令形に強める / planning.md へ移す

ADR-0044 の Review-when が自ら挙げた第 1 案。宣言文を足す方向で、ADR-0044 から 26 日の観測が
示すのはその方向が効かなかったこと。加えて「veto ではない」型の文は Decision 4 の原則と逆向き。
採らない。

### ADR を廃止し仮説台帳だけにする

ADR-0044 の未決案。未決 — 再訪条件: 本 ADR Review-when の第 1 項。

### memory を全削除する

user profile / 進行中 project / 作業作法の feedback は肯定形の事実で制動にならないため、種別ごとの
削除にとどめた。

### 「することだけを書く」原則を skill-creator §3 だけに置き、常駐 rule へ配線しない

skill-creator §3 が読まれるのは skill / agent の新規作成・大幅改修時だけで、原則が効くべき
ADR / memory / rule の編集は main loop が skill-creator を開かずに行う。常駐 rule `skills.md` の
1 文は、その編集面に届く唯一の surface。著者も「これこそ rules にすべきこと」と指定した。
1 文 + 意味ゲート 2 項目 + memory 1 ファイルが本 ADR で足す機構の全部で、machinery の増分は
この範囲に固定する。

### 否定形の語（しない / 禁止）を harness_lint で機械検査する

「複製しない」等、作業手順の動詞としての否定形が多数あり誤検知する。意味的ゲート
（adr-reviewer §8、skill-creator §4）で見る。

## Consequences

### Positive

- 常駐 rule 層が縮む（akc-cycle 57 → 38 行、planning.md 17 → 14 行、skills.md は 32 → 33 行で原則 1 文を
  得る）。MEMORY.md は 66 → 46 行、memory 総量は 1,774 → 1,166 行になる。
- ADR は既存機構を変えるときに経緯として読む対象になる（AGENTS.md:9 の新文言と揃う）。
- plan ファイルから Build-or-not 4 問の定型が消える。
- 「することだけを書く」1 原則が、skill-creator §3 の旧 2 bullet（トリビアル項目の列挙・
  tombstone の扱い）を置き換える。

### Negative

- memory の却下記録が消えたので、過去に見送った外部ツール（herdr-ctx、Delta/DeltaDB、
  SkillEvaluator）が再提案されうる。著者がその時点の情報で再判断する。
- 削除した 14 ファイル（608 行）は git 管理外で、退避先はセッション固有の scratchpad
  （`/private/tmp/claude-501/…/scratchpad/memory-backup-2026-09-14/`）。セッション終了後は
  Context のベースライン（46 ファイル / 1,774 行 / 却下語 約 80 行）を再現する手段が無くなる。
- grill-me の ADR 衝突チェックは plan 時から ADR を書く時（adr-reviewer §7）へ移る。
- ADR-0044 が「事例記録 0 件」とした計測の空白は残る（本 ADR も著者の主観的観測を起点にしている）。
- 公開 copy（claude-harness）は次の harness-sync まで drift する。ADR-0062:103 /
  [ADR-0048](./0048-sdlc-playbook-translation-and-rfc-conformance.md) の Build-or-not 言及は
  履歴として残る。

### Neutral / Follow-ups

- ADR-0044 の Alternatives「ADR を廃止し…」節と Review-when 節に
  `> **注記（2026-09-14, ADR-0065）**` を追記する（main loop の明示ステップ）。
- akc-cycle repo の自己完結版 `rules/common/akc-cycle.md` は別内容のため対象外。search-first は
  別セッションの再設計に委ねる。
- harness-sync は別セッション。
