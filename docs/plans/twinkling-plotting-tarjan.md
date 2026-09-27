# llm-as-judge を TypeSafe Jev 対応にし、公開 repo を更新し、awesome list に載せる

状態: 案 B で組んである。著者は案を明示選択していない — 対話での指摘は「①の Yes/No 層は明らかに Jev 向き、
Jev には Yes/No を返す機能がある」で、これは案 B の中身そのもの。A か C にするなら承認時に差し戻してほしい。

**Jev の Yes/No 機能の実体**（一次ソース `https://docs.typesafe.ai/api.md`、as-of 2026-09-21）: 質問型 `noul` が
それで、応答は `{"type":"noul","noul": <0〜1 の数>}`（"The yes/no answer on a scale from 0 (no) to 1 (yes)"）。
boolean 欄と閾値パラメータは無い。任意で `criteria: {"true": …, "false": …}` を付けられる。
→ skill の①の 1 問 = `noul` 1 問。runner が `noul >= 0.5` を `Yes` と表示し、数値を横に残す。

## Context

著者指示（2026-09-21）。`skills/llm-as-judge/SKILL.md` は散文のみ（197 行、script なし）で Jev を呼ばない。
awesome list 3 本の掲載条件（実際に Jev を使う / 壊れたら落ちる実行可能チェックがある）を満たさないので、
「Jev 対応」の下限は **Jev を実際に呼ぶ道具 + stub で回るテスト** になる。
RFC-0024 Guide-level が「binary 証拠層がそのまま Noul 群になる」と書いた対応を、汎用の設計パターン skill の側で形にする。

設計上の正直な緊張が 2 つあり、どの案でも SKILL.md に書く:
- **原則①は「各答えに 1 行証拠」を要求するが、Noul は確率だけ返し証拠文を返さない。** Jev 証拠層は
  screening で、低い読み値の質問は verdict を出す LLM が原文に当たって証拠行を付ける
- **Noul は確率を返す。** runner は質問ごとに `answer`（Yes/No、0.5 境界）と生の確率 `p` を並べて返す —
  既存の出力 schema の `evidence[].answer` にそのまま入る。原則③が禁じるのは質問をまたぐ集計で、1 問の
  確率をその 1 問の Yes/No に直すのは集計ではない。質問ごとの癖（無関係な入力にも高値を返す質問 —
  RFC-0024 実測 `new_evidence` 0.96〜0.97）はベースライン測定で露出させる

## (1) 「Jev 対応」の選択肢

| 案 | 中身 | yibie | AbdelStark | cobanov | 保守 |
|---|---|:-:|:-:|:-:|---|
| A 散文のみ | SKILL.md に節「Running the evidence layer on a System One model」を足す | ✗ | ✗ | ✗ | ほぼ 0 |
| **B 散文 + 最小 runner（推奨）** | A + `scripts/noul_evidence.py`（質問セット JSON + artifact → 1 POST → 質問ごとの生確率 + `question_hash` + model pin の evidence JSON）+ `--baseline <無関係テキスト>` で同じ質問セットの素通り値を並べる + stub サーバで回る pytest と期待出力つき例。**verdict は出さない・閾値を持たない・集計しない・ログを貯めない** | ✓（skill として記述） | ✓ | ✓ | script 2 本 + test。Jev の wire format 変更時に 1 箇所 |
| C B + verdict まで | B + Noul 群 → named verdict を Choice で出す段 + 判定 registry（RFC-0025 形）+ 人手ラベルとの較正 | ✓ | ✓ | ✓ | 大。Choice は confidence 0.4〜0.7 で頭打ち（RFC-0024 実測）で②を Jev に降ろす根拠が弱い。較正は `sutro-sh/jev-align` と重なる見込み |

推奨 B の理由: 掲載条件を満たす最小形で、skill の主張（①証拠層は割れる / ②verdict は holistic のまま LLM か人 / ③集計しない）を
コードの形でそのまま示せる。C は②を確率的判定器に降ろすので skill 自身の主張と衝突する。

cobanov 向けの 1 文（B の場合）: 「Jev answers each binary check as an independent Yes-probability; deterministic code
hashes the question set, pins the model, and prints the raw readings — it never thresholds, averages, or issues the verdict.」

## (2) 候補 4 との境界（1 行）

**skill の Jev 対応 = 利用者が持ち込む質問セットを回す汎用 runner と散文まで。harness 内の judge（readme-judge /
skill-stocktake / learn-eval / skill-creator §4）や hook がこの runner を呼ぶ配線を 1 本でも足したら、それが候補 4 の再開**
（RFC-0024 の再訪条件を満たしてから）。

## (3) 消費者への波及

無し（節の追加だけで、`## The three principles` の表と `### ①②③` の見出し・番号・文言を動かさない場合）。
- 番号を直接引くのは `rfcs/0024:73` と `rfcs/0025:31`（`llm-as-judge ③`）。④を足す・意味を変えると壊れる → **原則は 3 つのまま、Jev は「実行基盤の 1 つ」として別節**
- 構造依存（binary / named verdict / no aggregation の言い換え）: loop-design-check:22,87,150 / codex-review:84 /
  skill-stocktake:397 / learn-eval:253 / skill-creator:99 / agents/readme-judge.md:18 — 契約は変えないので無傷
- ADR-0046:79 が `Related` 見出しを名指し — 見出し名を残す
- `disable-model-invocation: true` と description の核は維持（description に Jev の 1 句を足すかは草稿ゲートで判定）

## (4) 既製との重なりと空き

as-of 2026-09-21。awesome list 4 本を索引に 16 repo の README / SKILL.md を読んだ（**コードは未読** — 「空き」は README 水準の判断で断定ではない。`skillranker` は存在・1 行説明・ライセンスの確認のみ）。

**既にある**
- 設計ガイド（runner なし）: 公式 `typesafe-ai/skills`、`dbreunig/building-with-jev-skill`（composite scoring など**集計するパターンも推奨**）、`samtay32/jev-system-architect`、`karanb192/jev-architect`、`24601/Augustus`（方法論 + Brier / reliability の評価 script）
- 用途固定の runner: `HyunjunJeon/jev-judgment`（coding-agent の 3 プロトコル、質問文固定、質問ごとの個別閾値）、`yuyang2230/jev-agent-skill`（classify / screen / score / verify の 4 種）
- 較正: `abhixhek/jevcal`（質問ごとの閾値をラベルデータに fit、held-out、CI でドリフト検知）、`sutro-sh/jev-align`（1 定義の分類器を GEPA で最適化）、`jev-ood-calibration`、`jev-orderby-bench`
- named outcome + JSONL ジャーナル + 較正の複合: `edgardcham/huncho`（決定木の branch 選択方式）

**空いている（見込み）**
1. 「複数の binary 証拠 → **集計せず** named verdict 1 つ、支配的 No が単独で決める」を明示した設計 — 近いのは huncho だが方式が違う。dbreunig は逆向き（集計を推奨）なので、**この skill の位置は「集計しない側の設計パターン」として立つ**
2. 利用者が持ち込む質問セットを Noul 群として回す**汎用** runner — 既製は用途固定かガイドのみ
3. 「無関係な入力にも高値を返す質問」を露出させるベースライン測定 — 較正系はラベルデータ前提で、ラベル無しの素通り値チェックは未確認
4. `question_hash` つきの出力 — README 水準では未確認

**帰結**: 閾値の fit・ドリフト検知は `jevcal` が既に持つので**自作せず SKILL.md から名指しで参照**する（案 C の較正部分を作らない根拠）。掲載節の候補: yibie `Evaluation & Benchmarking`（prompt 文書主体なので skill と明記）/ AbdelStark `Evaluations and independent research` / cobanov `Evaluation and calibration` / AnotiaWang `Agent Tools`（README.md と README_zh.md の同時更新が要る。今回の対象に入れるかは案の確定後に決める）。

## (5) 公開と PR の段取り（誰が何を承認するか）

| 段 | 実行 | 承認 |
|---|---|---|
| 正本 `~/.claude/skills/llm-as-judge/` の改修・task branch への commit | build-tier / 本セッション | 不要（boundary「とる」）。main への ff-only は検収後 |
| SKILL.md の著者通読（skill-creator §7） | 著者 | **著者 GO** |
| live smoke（runner を実 API に 1 回。key は script 経由でだけ解決） | 本セッション | プラン承認に含める |
| `scripts/sync-from-local.sh` で公開 repo へ同期 + repo 側所有物（README / CHANGELOG / llms.txt）の更新 — README は skill `readme-writer` | 本セッション | commit まで不要 |
| 公開 repo の **push** | 本セッション | **著者の明示承認**（diff を見せてから） |
| awesome list への **PR** — 順に yibie（週 3 枠の 2 本目）→ AbdelStark → cobanov。1 PR 1 プロジェクト、AI 生成とメンテナの開示、機外に出るデータ（artifact 本文と質問文が TypeSafe API へ）を明示 | 本セッションが PR 文面を下書き | **PR ごとに著者の明示承認**。文面を見せてから `gh pr create` |

## (6) implementation-chain

種別 **feat**（案 B/C。案 A なら散文編集のみで chain は skill-creator §4 草稿ゲート + 著者通読）。

- harness-boundary: eval 層の手続き（skill）+ stdlib script。runtime 非依存で可搬 → **Keep**。hook・settings には配線しない
- Phase 0: 本プランの (4)
- TDD: **Y** — 出力 JSON 契約とエラー時の振る舞いが争点（CLI なので **fail-loud**: API 失敗は非 0 exit、欠測を No と読ませない）。期待出力つき例を golden として固定
- Code Review: Y（`medium`、opus subagent 内で built-in `/code-review`）
- Security Review: **Y**（資格情報の読み取り / 外部 IO / 公開経路）。先に潰す型: https 限定 + リダイレクト拒否（`jev_client.py` の型をコピー）/ API 応答から取り出すのは float だけで文字列を出力に流さない / エラー reason は固定語彙 / key を出力・例外に載せない
- 共有方針: `skills/jev-skill-router/scripts/jev_client.py` を**コピーして改名**（依存させない — 公開 skill は自己完結。router 固有名 `USER_AGENT` / `JEV_ROUTER_KEY_FILE` を外す）。jev-skill-router 側は読むだけ
- Doc Sync: RFC-0024 Status に境界の 1 行（(2) の文）。harness-sync の表は既存行のまま（sync script は skill dir を丸ごとコピーするので `scripts/` `tests/` `pyproject.toml` は自動で載る — 先例 readme-writer）。ADR は起票しない（他 artifact が引く機構ではない → commit 本文に Context / Decision / Review-when）
- Verify: `./.claude/verify.sh`（`verify.sh:409-432` が `skills/*/pyproject.toml` + `tests/` を自動検出。verify.sh 自体は変更しない）
- **実行者**: script + tests は build-tier へ dispatch（`Agent(model: "opus", isolation: "worktree")`、packet に「HEAD を確認し main と違えば `git rebase main`」「`skills/jev-skill-router/**` と branch `task/jev-router-plugin` に触らない」「key file を読まない・cat しない」）。SKILL.md の散文は本セッションが書く（例外 (a)）

## Verification

1. `uv run --project ~/.claude/skills/llm-as-judge pytest -q`（stub サーバ、ネットワーク不要）— 期待出力つき例が golden と一致
2. `./.claude/verify.sh` exit 0、`python3 scripts/hooks/harness_lint.py`、skill-health `scan_refs` dangling 0
3. live smoke 1 回: 同梱の例（質問セット + artifact + 無関係な baseline テキスト）を実 API に通し、確率が返ること・`--baseline` で素通り値が並ぶことを目視
4. skill-creator §4 草稿ゲート（fresh subagent、Read/Grep/Glob のみ）→ named verdict
5. 公開 repo で sync 後に同じ pytest が通ること、`AbdelStark/awesome-typesafe` の `python3 scripts/check.py` が PR branch で通ること
