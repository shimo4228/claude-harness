---
origin: shimo4228
instrument: skill-comply（skills/skill-comply の scripts/run.py）
subject: apple-silicon-local-llm-serving（contemplative-agent の project skill）
validity: 不成立
source_type: documentation
evaluator_relationship: first_party
eval_library:
  name: skill-comply
  version: unknown
evaluation_timestamp: 2026-08-01T11:28:56Z
retrieved_timestamp: 2026-09-28
num_samples: 1
execution_command: "未記録（呼び出しの形は cd <skill-comply> && uv run python -m scripts.run [flags] <target SKILL.md>。渡した flag はレポートに残っていない）"
log_updates: []
---

# s2 — skill-comply の測定不成立（2026-08-01）

skill-comply が project skill の遵守率を 75% / 50% / 25% と出したが、対象の skill は一度も読み込まれておらず、数字は skill を読んでいない
エージェントの素の挙動だった、という事例の記録。原因の整理と対策は [ADR-0032](../adr/0032-skill-comply-measurement-validity.md)（2026-08-02）が持つ。
`evaluation_timestamp` はレポートの `Generated:` 行（UTC）から取った。JST では 2026-08-01 20:28:56。

## 設計

- 問い: skill `apple-silicon-local-llm-serving`（`~/MyAI_Lab/contemplative-agent/.claude/skills/` にある project skill）が定める手順に、
  エージェントがどれだけ従うか。skill-comply は対象文書から期待される行動列（spec）を LLM で生成し、指示の強さが違う 3 本のシナリオを
  `claude -p` の子セッションで走らせ、tool 呼び出しの時系列を分類して、必須 step の検出率を遵守率として出す
- 計器の使われ方: skill-comply は harness の AKC Measure phase の計器（rule `akc-cycle.md` の表）。遵守率が閾値を下回る step は
  「hook への昇格」を推奨する。この run も `identify_requirements` と `measure_context` の hook 昇格を推奨した
- spec: id `apple-silicon-llm-runtime-selection`、step 9 本（必須 4 本 = `identify_requirements` / `measure_context` / `check_hardware` /
  `evaluate_suitability`、任意 5 本）。hook 昇格の閾値は `threshold_promote_to_hook: 0.6`。9 本の detector のうち 5 本は記述が Bash を前提にする
  （spec の detector 記述を数えた。ADR-0032 の「9 detector 中 5 つが Bash 前提」と一致）
- シナリオ: 3 本。supportive（skill 名を呼び、手順 7 項目を prompt に列挙）/ neutral（skill 名を出さず要件だけ）/ competing
  （「速さ優先で Foundation Models を使え」と手順に逆らう方向へ誘導）。3 本とも「`sample_data/` にある日本語のサンプルクエリを使え」と指示する
- 採点: シナリオの遵守率 = 検出された必須 step 数 / 必須 step 数（4）。全体 = 3 シナリオの平均。順序の違反は step ごとに `ok` / `violated` / `unevaluable` で別に出る
- 対象の本文・シナリオ prompt の全文・tool 呼び出しの時系列はレポートにあるが、本文を含むのでこのカードには写さない（「既知の故障」6）

## 環境

- 実行した skill-comply の版: 未記録。レポート生成（2026-08-01 20:28 JST）は、シナリオ 3 本の並列化を入れた commit `79050e8`（同日 20:54 JST）より前で、
  その作業中の未 commit の tree で走った可能性がある（未確認。レポートに版の記録が無い）
- 子の model: 未記録。当時の `run.py` の既定は scenario 実行 `sonnet` / spec・シナリオ生成 `haiku` / 分類 `sonnet`（`79050e8` の `run.py` で確認）で、
  既定のまま走ったかは未確認
- Claude Code の版: 未記録（翌日の ADR-0031 の実測は 2.1.220）
- 子に渡した tool: 未記録（レポートに tool の欄が無かった。これが欠陥 C）。時系列には supportive と neutral で `Bash` の呼び出しがあり、
  子は Bash を実行できる状態だった。当時の設計は「Bash は既定 off、`--allow-bash` で opt-in」だったが、翌日の実測で `--allowedTools` は
  Bash を止めていなかったと分かった（[ADR-0031](../adr/0031-child-permission-envelope-via-permissions-deny.md)）。`--allow-bash` を付けたかは未記録
- sandbox: シナリオごとに `/tmp` 配下の sandbox ディレクトリを cwd にして走った（レポートの時系列の path から）
- 並列度: 未記録

## 生の読み値

レポート（`.notes/skill-comply-evidence/apple-silicon-local-llm-serving.md`、22,765 bytes）と spec（同 `.spec.yaml`、4,499 bytes）から写した集計。

| 欄 | 値 |
|---|---|
| Overall Compliance | **50%** |
| Threshold | 60% |
| Recommendation | `identify_requirements` と `measure_context` を hook へ昇格 |
| supportive の遵守率 | 75%（必須 4 本中 3 本検出。落ちたのは `identify_requirements`） |
| neutral の遵守率 | 50%（2 本。落ちたのは `identify_requirements` / `measure_context`） |
| competing の遵守率 | 25%（1 本。落ちたのは `identify_requirements` / `measure_context` / `check_hardware`） |
| step 別の検出率（hook 昇格の根拠） | `identify_requirements` 0% / `measure_context` 33% |
| tool 呼び出しの件数 | supportive 37 / neutral 40 / competing 6 |
| 対象 skill の呼び出し | supportive の 0 番目の呼び出しが `Skill(apple-silicon-local-llm-serving)` → `Unknown skill`。neutral と competing は `Skill` を呼んでいない |

導出:

- 全体 50% = (75 + 50 + 25) / 3
- `measure_context` 33% = 検出 1（supportive）/ 3 シナリオ

測定が成り立っていたかを示す値（レポートの時系列から数えた。レポート自身はこれを記録していない）:

| 前提 | 値 |
|---|---|
| 対象 skill の本文を読めたシナリオ | **0 / 3** |
| `sample_data/` にフィクスチャがあったシナリオ | 0 / 3（supportive と neutral は `ls` で空を確認。competing は見に行っていない） |
| 子が自分でフィクスチャを書いたシナリオ | 1 / 3（neutral が `sample_data/` に 15,557 bytes の文書を Write） |
| Bash 前提の detector | 5 / 9 |

## 測らなかったもの

- skill の手順への遵守。対象の本文は 3 シナリオのどれにも届いていないので、75% / 50% / 25% は skill の効果について何も言わない
- skill への手の伸ばしやすさ（発見）。supportive は skill 名を prompt に書いたので呼んだだけで、neutral と competing は呼ばなかったが、
  呼んでも読めない環境だったので発見の測定にもなっていない
- 反復による揺れ（各シナリオ 1 回）
- spec の妥当性（LLM が生成した step と detector を人が検証した記録は無い）
- 分類器（LLM）の判定の揺れ

## 既知の故障

ADR-0032 が表 A〜C にまとめた 3 つの欠陥と、この記録を読むときの注意。

1. **A — 対象 skill が子から読み込めない。** project skill は `~/MyAI_Lab/contemplative-agent/.claude/skills/` にあり、sandbox を cwd にした子の
   skill 発見の範囲に入らない。supportive の `Skill(...)` は `Unknown skill` で返り、エージェントはそのまま自力で作業を続けた。
   数字は出たので、測定の失敗が低いスコアに見えた
2. **B — シナリオのフィクスチャが実体化しない。** 生成器は `cat > f << EOF` 形の setup を書き、実行器は `mkdir` / `touch` しか解釈しなかった。
   prompt が指す `sample_data/` は空のまま。ADR-0032 は `[setup refused]` 6 件と書くが、この文字列はレポートに無い（0 件。出所は stderr と推定、未確認）
3. **C — detector が要求する tool と子の tool が突き合わされていない。** 9 detector 中 5 本が Bash 前提。子に Bash が無ければ
   「やらなかった」でなく「観測できなかった」が 0% になる。この run では子が Bash を使えたので C は数字を曲げていないが、それは
   ADR-0031 の封じ込めの欠陥（`--allowedTools` が Bash を止めない）の副産物で、意図した状態ではなかった
4. **終了コードが正常。** 3 つとも欠けたまま遵守率と推奨が出て、自動化から見ると成功した測定だった
5. **推奨が誤った入力で出ている。** hook 昇格の推奨（`identify_requirements` 0%）は skill を読んでいないエージェントの挙動から出ており、
   採用すると根拠の無い hook ができる。harness と contemplative-agent の git log（commit message）と contemplative-agent の `.claude/` を
   step 名で grep し、採用の痕跡は見つからなかった（2026-09-28）
6. **生レポートは公開しない。** レポートは `.notes/`（gitignore 下）にだけあり、対象 skill・シナリオ prompt・子の出力の本文と
   ホストの絶対パスを含む。このカードは集計と件数だけを写した

ADR-0032 が足した「成立していたか」の記録欄（commit `8ef46f0`、2026-08-02）: レポートの Summary に `Target kind`（対象の種別）/
`Skill placed in sandbox`（Tier 1 = name と description だけの stub、Tier 2 = `--load-target-skill` で本文）/ `Child tools denied`（子から外した tool）/
`Target skill invoked`（対象 skill を呼べたシナリオ数）/ Tier 1 の注記 / `Excluded (skill unresolved)`（読み込めないまま走りスコアから除いたシナリオ数）を出す。
読み込めないまま走ったシナリオがあれば終了コード 1 を返す。この記録欄はこの run の後にできたので、この run のレポートには無い。

## 有効性の状態

**不成立。** 対象 skill の本文は 3 シナリオのどれにも届いておらず（0 / 3）、フィクスチャも実体化していない。読み値は
「skill の手順への遵守」という問いに答えていない。読める事実は「この環境では project skill が子から見えず、見えないまま遵守率が出た」まで。

- `単発` へ動く条件: 同じ spec を ADR-0032 後の skill-comply（Tier 2 = `--load-target-skill`、`files:` でフィクスチャを渡す）で走らせ、
  Summary の `Target skill invoked` が 3/3 で、除外シナリオが 0 の run を新しいカードとして記録する。この 2026-08-01 の run 自体は動かない
- この run の数字を後から救う経路は無い（時系列から本文を読めていなかったことが確定している）

## 欄の対応表

| このカードの欄 | aggregate-result.json（schemaVersion 1） | Every Eval Ever v0.3.0 | Inspect AI EvalLog |
|---|---|---|---|
| frontmatter `eval_library` | — | `eval_library{name,version}` | — |
| frontmatter `evaluation_timestamp` | — | `evaluation_timestamp` | — |
| frontmatter `retrieved_timestamp` | — | `retrieved_timestamp`（EEE は Unix epoch） | — |
| frontmatter `source_type` / `evaluator_relationship` | — | `source_metadata.source_type` / `source_metadata.evaluator_relationship` | — |
| frontmatter `num_samples` | — | `evaluation_results[].score_details.uncertainty.num_samples` | — |
| frontmatter `execution_command` | — | `evaluation_results[].generation_config.generation_args.execution_command` | — |
| frontmatter `log_updates` | — | — | `log_updates`（考え方のみ） |
| 生の読み値 Overall Compliance / シナリオ別遵守率 | —（skill-comply 独自のレポート。arm も delta も無い） | — | — |
| 既知の故障 ADR-0032 の記録欄（`Target skill invoked` ほか） | — | — | — |
