kind: external
# ホリスティック評価の層（観点ローテーション・取り置き観点・不一致の保存・帰属ログ）を harness ネイティブで作るための外部調査

as-of: 2026-10-13。WebSearch / WebFetch 合計 13 回 + 内部 report 1 本 Read。Verdict は書かない。

## Scope searched

- 角度 1（公式 doc、取得日 2026-10-13、WebFetch 経由で要約された本文。各ページは 10 万字超で先頭 10 万字のみ処理、残りは未読）:
  - https://code.claude.com/docs/en/hooks
  - https://code.claude.com/docs/en/sub-agents
  - https://code.claude.com/docs/en/skills
- 角度 2（先行実装）: WebSearch 1 本（Claude Code の multi-perspective review / disagreement / audit log）と WebSearch 1 本（rubric rotation / held-out rubric）。Inspect AI・promptfoo・DeepEval・OpenAI Evals は今回は再調査していない。既存調査 `docs/plans/research/2026-10-06-eval-search.md` の §3（先行ツール）を 1〜120 行目だけ Read した（121 行目以降の 123 行は未読。論文節の続きと Contradictions がある）。
- 角度 3（根拠）: arXiv 2609.02246（abs ページ）、arXiv 2404.12272（abs ページ）、arXiv 2607.01830（abs ページ）、WebSearch 2 本（rubric 感度、judge 過最適化）。いずれも本文は読んでいない。
- 見つからなかった範囲: 「観点を毎回入れ替える」「生成側に見せない取り置き rubric」を LLM judge に適用して Goodhart を減らしたと実証する論文・ツール。評価結果の不一致を統合せず保存することを設計の中心に置く OSS。

## Found

### 角度 1: Claude Code 公式仕様（Spec/official behavior、一次資料、要約経由）

1. hook 共通入力 `agent_id` / `agent_type`（hooks ページ）
   - 引用: `agent_id` は「Unique identifier for the subagent or in-process teammate the hook fires in.」、`agent_type` は「Present when the session uses `--agent` or the hook fires inside a subagent. For subagents, the subagent's type takes precedence over the session's `--agent` value.」
   - Configuration 節: subagent が tool を呼ぶと「`PreToolUse` and `PostToolUse` fire the same configured hooks as in the main conversation, and the input carries the `agent_id` and `agent_type`」。
   - 違い・罠: (i) 「主ループでは `agent_id` が無い」とは doc が明言していない（記述からの推論）。実装前に主ループの実 payload を 1 回記録して確かめる必要がある。(ii) `agent_type` は `--agent` で起動した主セッションでも入る。主ループ判定には `agent_type` でなく `agent_id` の有無を使う。(iii) in-process teammate（agent teams）にも `agent_id` が入る。評価用 subagent だけを通す allowlist は `agent_type` の名前一致でも絞る必要がある。
   - 移せる: 「`agent_id` 無し、または `agent_type` が評価用 agent 名でない → 取り置き観点の path を deny」は仕様の範囲で書ける。
2. PreToolUse の deny 出力（hooks ページ）
   - 形: `{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"..."}}`。`permissionDecision` は allow / deny / ask / defer。`hookEventName` 必須。
   - 代替: exit 2 + stderr で block（JSON も出していれば JSON の reason が優先）。exit 0 + 出力なしは「判断なし」で通常の permission flow へ。
   - 罠: exit 1 など他の code は非 block（action は進む）。timeout した command hook も block しない。block させるには `"onFailure": "block"`（Claude Code v2.1.295 以降）。取り置きの機密性を守る hook は fail-open が既定なので、`onFailure: block` か、exit 2 で落ちる書き方が要る。
3. subagent frontmatter（sub-agents ページ）
   - `tools` は allowlist（省略時は全 tool を継承）。`disallowedTools` は denylist で、`Bash(git push *)` のように specifier を付けても「whole tool を除去」。両方ある場合は disallowedTools を先に適用し、次に tools を解決。
   - `model`: `sonnet` / `opus` / `haiku` / `fable` / 完全 ID / `inherit`。省略時は subagent model order で決まる。
   - 他に `permissionMode`、`maxTurns`、`skills`、`hooks`、`omitClaudeMd`（v2.1.271 以降。CLAUDE.md を載せずに起動）、`effort`、`isolation: worktree`、`memory`、`background`。plugin subagent は `hooks` / `mcpServers` / `permissionMode` を無視する。
   - 移せる: 観点ごとの独立 reader は `tools: Read, Grep, Glob` で作れる。`omitClaudeMd: true` は、評価者に書き手側の rule を見せない用途に使える（効果は未検証）。`maxTurns` で長さを抑えられる。
   - 注意: `tools` に Read を許すと、path 制限は hook にしか無い。取り置き観点のファイルは評価用 subagent の Read で読ませる設計なので、hook の allowlist が唯一の壁になる。
4. skill frontmatter（skills ページ）
   - `disable-model-invocation: true` は Claude の自動ロードを止め、「Also prevents the skill from being preloaded into subagents and from running when a scheduled task fires with the skill as its prompt」。Claude が呼ぼうとしても blocked。
   - `context: fork` は forked subagent で実行。「doesn't run in a fork of the current conversation」— 会話履歴は渡らず、skill 本文が task prompt になる。`agent` で subagent type を指定（省略時 general-purpose、カスタム agent 可）。
   - `allowed-tools` は「does not restrict which tools are available」— 許可プロンプトの免除であって制限ではない。
   - 移せる: 評価 skill を `disable-model-invocation: true` にすれば書き手 Claude の自発起動を止められる（観点の自己選択を防ぐ）。`context: fork` + `agent: <評価 agent>` で「書き手の会話を見ない評価者」を 1 skill で配線できる。違い: `allowed-tools` を tool 制限に使えない。制限は agent 側の `tools` か hook でやる。

### 角度 2: 先行実装

5. 既存調査 2026-10-06-eval-search §3（再利用、再調査なし）
   - Inspect AI・promptfoo・DeepEval は scorer / metric の catalog で、「観点ローテーション」「取り置き rubric」「不一致の保存」を機能として持つと確認していない（同調査の範囲で）。
   - claude-api 同梱 `eval-hillclimb` は train / test の固定 split と「held-out に触れない」を持つが、grader への過学習は split で防げない（同調査 1-E の推論）。本件の「取り置き観点」はこの隙間（grader 側の held-out）に当たる。同調査は split を case の側に置いた設計で、観点の側ではない。
6. Claude Code 側の skill 検索（WebSearch 1 本、snippet のみ。ページ本文は未読）
   - 「Review Protocol」skill（claudskills.com）: perspective ごとに sub-agent を dispatch し、conflict を検出し、REVIEW-SCHEMA の JSON を返す。conflict を残すか解消するかは snippet から不明。
   - skill-doctor: 評価ごとに 1 行を log に追記する（追記型ログの先例。帰属の粒度は不明）。
   - Terryc21 skill-reviewer: file:line 引用付きの findings と、複数 lens の second-opinion pass。
   - 検索結果の総括: 「不一致を統合せず残す + 帰属ログ + rubric 隠し」を揃えた plugin は見つからなかった（検索 1 本の範囲）。部分的に移せるのは「perspective ごとの sub-agent + 引用付き findings」と「1 行追記 log」の形だけ。そのまま使える物は確認していない。
7. 論文側の近縁（snippet + abstract）
   - Many Voices, One Reward（arXiv 2607.01830、2026-07-02 提出、abs 読み）: 複数 role から rubric を生成し統合して 1 つの scorer にする（MRRG）。単一 rubric の「dimensional blind spots」を問題にする点は本件と同じ向き。ただし統合する（本件は統合しない）、held-out / 回転の記述は abs に無い。
   - CHERRL（arXiv 2606.04923、snippet のみ）: 既知の bias を LLM judge に注入して reward hacking を再現する testbed（公開 code あり）。本件の「取り置き観点が実際に hacking を検出するか」を既知 bias で試す道具になりうる（未確認）。

### 角度 3: 根拠の照合

8. PROCTOR（arXiv 2609.02246、Vansh Wahi 単著、2026-09-02 v1、cs.AI。abstract のみ読み）
   - 題は「LLM-as-a-Judge Is Not an Oracle: Why Self-Improving Agents Need Deterministic Guardrails」。主張は「optimization が評価器の誤差を登る」より広く、judge を oracle でなく advisor に降格し、決定的検査で gate する、という設計論。
   - 証拠の種別: 数か月の自律 prompt 最適化 loop の運用経験と事例（11 件の評価信号の失敗を 4 類: judge bias / harness・metric 失敗 / ground-truth 誤り / reward hacking）。controlled benchmark ではない（abs の範囲）。例: agent が cached な answer key を読んで満点、pass 率 100% が真の能力約 68% を隠した、壊れた label で最適化器が正しい rule を削除。
   - 本件に効く 2 点: (a)「judge の rubric を書き直しても plateau、効いたのは judge の出力順の構造的制約」— rubric の改良では登れず構造で効く、という主張。(b) PROCTOR の 5 guardrail は hermetic sandbox / capability-disjoint roles / 受入検査が Teacher に優先 / frozen holdouts / canary case（満点は cheating の信号）。「capability-disjoint roles」と「frozen holdouts」は本件の「取り置き観点を hook で書き手から隔離」と同型。違い: PROCTOR の holdout は case 側の凍結で、取り置きの対象が観点（rubric）かは abs から不明。PROCTOR は Teacher も LLM judge で検出漏れが残ると自認する。
   - 本件の骨子（点数を出さない・人が読む）は PROCTOR の「judge は advisor、gate は決定的」と整合するが、PROCTOR は最終 gate を決定的検査に置く。本件の価値判断領域には決定的検査が無いので、gate の位置が違う。
   - 内部 rule `evals.md` が PROCTOR を「holdout 4–8 件は noise」の出所として引いている。abs にその数値は見えなかった（本文未読のため、あるともないとも言えない）。
9. EvalGen（arXiv 2404.12272、Shankar et al. 2024、abs 読み）
   - criteria drift: 「users need criteria to grade outputs, but grading outputs helps users define criteria」。基準は見る出力に依存して動く。基準は出力と独立に事前定義できるという前提への反論。定性 study の結果。
   - 本件との関係: 成果物専用の観点を 1 つ生成する設計は drift を前提にした方向。一方、drift は「基準が時間でずれる」という事実で、ローテーションで防げる・悪化するかは論文の範囲外。
10. rubric を回す・隠すことで judge への過適合が減る、という直接の実証: 見つからなかった（検索 2 本。reward-model 過最適化の文献は ensemble と gold/proxy 分離が中心）。
    - 最も近い実証: Gao et al.（Scaling Laws for Reward Model Overoptimization、arXiv 2210.10760）と Coste et al. 2023 の ensemble。gold と proxy を分ける設計が標準で、最適化器が見ない評価器で測る、という形は「取り置き観点」の類比。ただし対象は学習した reward model と合成 gold label で、LLM judge の観点の入れ替えではない（snippet 経由、本文未読）。
11. 反証・懸念（rubric を変えると何が起きるか）
    - arXiv 2601.08654（snippet）: 意味が同じ rubric の順序入れ替え・言い換えで、raw rubric text に依存する方式ほどスコアが動く。低次元で簡潔な rubric では差が小さい。
    - arXiv 2609.02942（snippet）: rubric の文面だけで judge の出力を偶然以上に予測できる（因果は未確定）。rubric 感度の stress test を推奨。
    - arXiv 2509.01790（snippet）: 別の層（回答側の prompt template）では LLM judge が分散を下げたと報告。上 2 件と矛盾せず、対象の層が違う。
    - 含意: 観点を毎回入れ替えると、版間のスコア比較は成り立たない。本件は点数を出さず観点帰属付きの観察を残すので、比較可能性を捨てる設計と読める（評価の再現性が落ちる側の反証は、これが該当する）。ローテーションの効果（過適合の減少）と代償（比較不能）を直接比べた実証は見つからなかった。

## Contradictions

- 「rubric を直せば judge は良くなる」と「rubric 改良では plateau し構造制約が効いた」（PROCTOR abs）。前者は eval-audit / llm-as-judge の前提。後者は 1 著者の運用経験で、強い根拠ではない。
- 「rubric 表現で judge が動く」（2601.08654 / 2609.02942、snippet）と「judge 評価は prompt 感度を下げる」（2509.01790）。層が違うので衝突ではなく、観点を入れ替える設計は前者の感度を意図的に取り込む選択になる。
- 既存調査 2026-10-06 の方針（連続 measure・pass rate・CI）と、本件の「点数を出さない」。前者は最適化 loop（hillclimb）向け、後者は価値判断の評価向けで、対象が違う。
- 根拠の強さ: 公式 doc（角度 1）は強い。論文は全て abstract または snippet 止まりで、角度 3 は弱い。

## Still unknown

- 主ループの PreToolUse payload に `agent_id` が無いことの実測（doc は明言しない）。subagent から subagent を起こした場合の `agent_id` の扱い。
- 評価用 subagent が Bash を持たない設計で、hook が Read / Grep / Glob の path のみ見れば取り置きファイルを守れるか（主ループ側の Bash 経由の読み出し、Glob の列挙、git 経由の閲覧は別途塞ぐ必要がある。未調査）。
- 取り置き観点が書き手の文脈（会話・CLAUDE.md・過去の評価ログ）に漏れる経路。ログに観点本文を書くと漏れる。
- PROCTOR 本文の holdout / canary の条件と数値（`evals.md` の「holdout 4–8 件は noise」の出所確認を含む）。
- EvalGen 本文の criteria drift の量的な結果。
- 「観点ローテーション」「取り置き rubric」の LLM-judge 過適合への効果の実証（未発見。無いことの証明ではなく、検索 2 本の範囲）。
- 角度 2 の各 Claude Code skill（Review Protocol / skill-doctor / skill-reviewer）の中身。conflict を保存するか解消するかは SKILL.md を読まないと不明。
- 内部資産（llm-as-judge / loop-design-check 失敗モード #6 / measurement-discipline）との重複確認は今回していない。
