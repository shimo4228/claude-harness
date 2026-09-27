# human-gate.md 監査ファースト最適化

## 統治原則（ユーザーの第一動機）

human-gate.md は「人間がボトルネックにならず、真に大事な部分（intent 判断）だけに認知資源を
集中させる」ために作られたルールである。今回の最適化の第一動機は、このルールが**逆にモデルの
動きを阻害する側に転じていないか**を検査し、転じている部分を取り除くこと。語数削減は従属目標。

したがって監査の主判定は各条項に対する次の 2 問:

1. **人間の注意を節約しているか** — この条項がないと人間が余計なものを読まされる/判断させられるか
2. **モデルの自律動作を阻害していないか** — この条項がモデルに余計な停止・確認・提示・躊躇を
   強いていないか（system prompt の autonomy 既定「proceed without asking / Stop only for
   destructive actions or genuine scope changes」との衝突を含む）

両方 No の条項は目的を失っており、削除候補。1 が Yes でも 2 も Yes なら、
節約効果と阻害コストのトレードオフとして明示提起する。

## Context

`rules/common/human-gate.md` は記事化の過程 (2026-07-28、ADR-0019 追記の 5 修正) で
HEAD 263 words + 未コミット「1 作業 1 ゲート」節 49 words = **312 words** に膨張した。
`rules/common` 全体も rightsize 水準 2,314 (ADR-0018) → 2,916 words と +26% 戻っている。

ただし ADR-0019 追記 (2026-07-28) は 5 修正の rule 常駐コストを**明示的に受容済み**
（「固定スキーマは毎回発火するゲートの手順であり、skill の確率的トリガーに委ねると守られない」）。
そのため grill-me の結果、以下を確定した:

- **監査ファースト**: 判定を証拠の後ろに置く。削減範囲は監査結果を見て決める
- **スコープ**: human-gate.md 行単位 + cross-reference 先 (planning.md / coding-style.md /
  debugging.md) との重複のみ。generation-audit は不使用（世代交代監査は ADR-0018 実施済み、
  human-gate.md は Claude 5 世代生まれ — 膨張原因は根拠 prose の逆流であり世代ミスマッチではない）
- **未コミット節も監査対象**。working tree 312 words をベースラインとし、最終 1 コミットに束ねる
- **成功基準は基準駆動・数値目標なし**: 「規範（何をせよ）は保持、根拠 prose（なぜ）・
  両立論証・anchor 段落は ADR-0019 へのポインタに畳む」。語数は結果として before/after 報告

## Phase A: 監査（読み取りのみ）

`human-gate.md` の全文を節・文単位で分解し、rules-stocktake の判定フレームで監査表を作る。

各行の分類:

| 分類 | 判定基準 | 既定 verdict |
|---|---|---|
| **規範** (何をせよ / 提示スキーマ / 分岐規則) | 削ると行動が変わる | 統治原則の 2 問で評価。阻害なしなら Keep、**阻害ありなら ADR-0019 再審議として提起**（勝手に削らない） |
| **根拠 prose** (なぜ / 〜だから) | ADR-0019 本文に同内容があるか照合 | あれば Compress（ポインタ化）、なければ landing 先を記録 |
| **両立論証** (他 rule と矛盾しない説明) | 例: 「1 作業 1 ゲート」節の coding-style.md 両立 2 行 | Compress 候補 |
| **重複** | planning.md / coding-style.md / debugging.md / agents.md と同内容 | 正本 1 箇所化の候補 |

規範条項の阻害コスト評価では特に以下を疑う（統治原則の 2 問目の具体化）:

- 固定 5 フィールドスキーマの**適用範囲**が意図（intent 判断の照合）より広く発火していないか
- 本文提示カテゴリ（behavior-shaping / control plane / 証拠生成物）の拡張が、
  人間の読む量をかえって増やしていないか（本文提示 = 人間が全文を読む前提の設計）
- 「1 作業 1 ゲート」の例外条件が、モデルに中間停止の判断迷いを生む書き方になっていないか

### Runtime 層・公式推奨との照合（generation-audit の中核メソッドを単一ファイルに適用）

human-gate.md の各条項を以下 2 つの substrate 面と突き合わせ、
**conflict / redundancy / drift** に分類する（generation-audit の分類フレーム）:

1. **現セッションの system prompt + tool descriptions**（ライブ収集）。照合対象の候補は
   既に見えている — system prompt は「For actions that are hard to reverse or outward-facing,
   confirm first unless durably authorized」（↔ 昇格規則 / Reversibility Gate）、
   「For reversible actions …, proceed without asking. Stop only for destructive actions or
   genuine scope changes」（↔ 1 作業 1 ゲート）、「Report outcomes faithfully: if tests fail,
   say so with the output」（↔ FAIL 例外）を既にネイティブに運ぶ。rule 側が substrate と同内容なら
   redundancy（downward dissolution 候補）、より厳しい/緩いなら「意図的な上書きか」を判定する
2. **Anthropic 公式の Claude 5 プロンプト推奨**（WebFetch で取得: docs.claude.com の
   prompt/context engineering ガイダンス + ADR-0018 が引く Thariq 記事
   「The new rules of context engineering for Claude 5 models」）。各保持条項を
   「ルール付与 → 判断委譲」「反復強調 → 一度だけ」等の Then → Now 基準に照らし、
   旧世代型の書き方（防衛的論証・反復・説得調）が残っていないか検査する

分類の帰結: redundancy = substrate が既に運ぶ → 削除候補（ただし human-gate.md の存在理由は
「Claude が既定で持たない、この環境固有の意見」なので、**substrate より厳しい/特殊な部分だけ残す**
形に圧縮）。conflict = substrate の新しい既定を劣化させる → 優先削除候補。
drift = 静的コピーが古い → 更新か削除。

### 追加の検査項目

1. **注入実測**: HTML コメント (`rationale:` / `review-when:`) は注入時 strip されるため、
   `wc -w` の disk 値でなく strip 後の値も併記する（rules/README.md の規定）
2. **ADR-0019 照合**: 削減候補の根拠が ADR-0019 に既載か 1 件ずつ確認。
   未載（例: 未コミット節の両立論証 — ADR-0019 より新しい）は ADR-0019 追記への移設を提案
3. **被参照リンク**: `human-gate.md` を参照する側 (planning.md / coding-style.md /
  debugging.md / security.md ほか、`grep -rl "human-gate" rules/ skills/ docs/` で実測) の
  アンカーが壊れないか

## Phase B: 提示（human gate 自身の規定に従う）

`human-gate.md` は behavior-shaping artifact なので、**監査表 + 圧縮後の全文（本文）**を提示する。
意図の要約への畳み込みはしない。提示内容:

- 監査表（行 × 分類 × verdict × 根拠の所在 × substrate 照合結果 [conflict/redundancy/drift/なし]）
- 圧縮案の全文 diff
- ADR-0019 追記案（移設する根拠 prose がある場合のみ）
- before/after の語数（disk / strip 後の両方）

ユーザー承認までは一切書き込まない。承認が「削減幅を狭める / 広げる」なら Phase A の表に戻る。

## Phase C: 適用 + コミット（承認後）

1. `rules/common/human-gate.md` を承認版に書き換え（global 版のみ、Change Target 規約）。
   ファイル先頭の `rationale:` / `review-when:` メタデータコメントは保持・必要なら更新 (ADR-0021)
2. 移設する根拠 prose があれば `docs/adr/0019-human-gate-layer.md` に追記
   （ADR-0018 の「削減分は消さず吸収」パターン）
3. 被参照リンクの整合を確認
4. コミット: 未コミットの「1 作業 1 ゲート」節 + 今回の最適化を **1 コミット**に束ねる。
   `skills/harness-sync/SKILL.md` の dirty は**無関係なので含めない**（`git add` はパス指定）。
   git 作法: 1 Bash call = 1 git コマンド (`git-workflow` skill)

## Verification

- `wc -w rules/common/human-gate.md` と strip 後語数の before/after
- `grep -rn "human-gate" rules/ docs/adr/` でリンク切れなし
- `git -C ~/.claude status` で human-gate.md（+ ADR-0019 追記時は同ファイル）のみが
  コミット対象になっていること
- harness_lint 相当のメタデータ検査（`rationale:` / `review-when:` コメントの存在）

## 触らないもの

- **規範内容の無断変更** — 固定 5 フィールドスキーマ・提示物の対象分岐・昇格規則・FAIL 例外は
  監査（阻害コスト軸含む）の対象にはするが、変更は ADR-0019 の再審議事項として Phase B で
  明示提起し、承認なしには書き換えない
- `planning.md` / `coding-style.md` 等の他 rules ファイル（重複検出しても今回は human-gate.md 側で
  ポインタ化する。他ファイル側の編集が必要な結論になったら Phase B で明示提案）
- ADR-0019 末尾の「position paper 引用の瑕疵（未対応）」— 別タスク、スコープ外
