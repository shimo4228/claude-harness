# RFC 導入の適否評価 — ~/.claude harness

調査日: 2026-08-24。現物（TASKS.md / docs/adr/ 47 件 / task-stocktake / task-triage / adr-writer / memory）を直接読んで判断。ファイル変更なし。

## 1. Current State

**Task Ledger**（`.notes/TASKS.md`、単一表形式）:

- 総量 52.7KB。**Pending 節 7.7KB（4 行）/ Done 節 44.9KB（38 行、ファイルの 85%）**
- Pending の内訳: `ready` 1（T-002）、`blocked` 3（T-EVAL-AXIS-BOOTSTRAP / T-REVIEW-GENERATION-RATE / T-SKILL-CREATOR-EVAL-NATIVE）。`candidate` は現在 0
- 状態語彙はすでに再設計済み（正本 `skills/task-stocktake/SKILL.md:52-57`）: 開 = `candidate`（採否判断がまだ要る）/ `ready` / `in_progress` / `blocked`（**採用済みで、条件成立だけで ready になる**）、終端 = `done` / `decided` / `dropped` / `retired`
- **`defer` / `observing` という状態は存在しない**。`skills/task-triage/SKILL.md:34` が明示: "There is no defer"。ユーザーの挙げた混在状態は、この repo ではすでに次へ吸収済み:
  - 観察待ち・モデル進化待ち → `blocked` + 必須 3 行（再開条件 / 照合先 / 成立時）。照合先が書けないものは `blocked` 入場拒否（task-stocktake:70-77）
  - 将来検討 → `candidate`、または「発生すれば自然に再発見されるものは保持しない → `dropped`」（task-stocktake:73-75）
  - 観察の決着 → `done`（読みが出た）vs `retired`（観察対象が消えた）の使い分け規律あり（task-stocktake:122-126）
- **blocked 3 行は事実上のミニ RFC**: 仮説・証拠・tripwire・再開条件・照合先を 1 行に持ち、launchd の無人 triage cycle（ADR-0045）が照合先を機械照合して日付つき照合ログを追記している（TASKS.md:14-16 に「照合 2026-08-19 / 2026-08-22 … 未発火」が現に 2 世代分）

**ADR**（`docs/adr/`、47 件）:

- Status 分布: accepted 43 / superseded 4（supersede 事象は ADR-0035 の 1 回のみ）
- **ADR-0044（2026-08-19 — 5 日前）が RFC の中核機能を ADR 内に実装済み**:
  - `## Review-when`（失効条件）節を 0044 以降必須化、`harness_lint.py` が存在を機械検査
  - `## Alternatives Considered` に**「未決 — 再訪条件: …」を明示的に許可**（0044:64「生きている対抗案は閉じない」）。実例 2 件（0044:124、0045:136）
  - 読み方 protocol「ADR は日付つき仮説。失効条件が発火した ADR に拘束力は無い」を akc-cycle.md に正本化
- proposal 的 ADR の混在: **構造的に起きない**。adr-writer は「frozen, already-approved decision packet」しか受けず、不完全 packet は書くこと自体を拒否する（skills/adr-writer/SKILL.md:16、ADR-0016 render-not-decide）
- 未決論点の ADR 内での置き場は Alternatives の「未決 — 再訪条件」であり、decision と deliberation は**同一文書内の節分離**で既に責務分離されている

**未決の設計論点の現在の分布**: ① 台帳の `blocked`（機械照合可能なもの）② ADR Alternatives「未決 — 再訪条件」（判断に付随するもの）③ memory の `concept_*` / `project_*`（〜5 件、repo 非依存の構想）④ ADR Consequences「解決しないこと」→ 台帳 blocked 行への送り（ADR-0041 → T-REVIEW-GENERATION-RATE の双方向参照が実例）。散在ではなく**役割分担が既に配線されている**。

**定期再評価の機構**: launchd triage loop（ADR-0043/0045、週次）が blocked の照合先を機械照合し、dead-band で未変化行の再読を省く。「観察待ち項目の定期再評価」は実装・稼働済み。

## 2. Core Problem

「実行タスクと未決論点の混在」は**この repo では既に解決済みの問題**である。Pending は 4 行で、blocked 3 行は照合先つきで無人 loop が回している。混在は設計であって欠陥ではない。

実際に台帳を肥大させているのは別の 2 点:

1. **Done 節の無期限残存** — 「完了・廃止したものは削除せず Done 節へ移す」（TASKS.md:5）の規約に archive 出口がなく、44.9KB（85%）が読み経路に残る。store 形式には `.notes/archive/tasks/` への mv が定義済み（task-stocktake:133-135）だが、**単一表形式の Done 節には archive 規約が無い**。台帳を開く agent は毎回 ~13k tokens を払う
2. **行内履歴の単調増加** — blocked 行に無人 cycle が照合ログを毎回追記し（T-EVAL-AXIS-BOOTSTRAP は既に照合 2 世代 + 更新 2 件を内包）、decided 行（T-012 ~3,000 字）は判断過程全文を保持する。1 行 = 1 セルの単一表で deliberation 履歴を持つ構造が上限なし

つまり本質は「未決論点の置き場が無い」ではなく「**終端行と履歴の刈り取り規約が単一表形式に無い**」。

## 3. RFC Fit

RFC という object type が提供するもの vs 既存機構:

| RFC の機能 | 既存の担い手 | 状態 |
|---|---|---|
| 未決の設計仮説の保持 | `blocked`（照合可能）/ `candidate`（採否待ち）/ ADR Alternatives 未決 / memory concept_* | 稼働中 |
| Revisit-When | blocked の再開条件・照合先・成立時（必須 3 行）、ADR の Review-when（lint 検査済み） | 稼働中 |
| 定期再評価 | launchd triage loop + dead-band | 稼働中・無人 |
| deliberation と decision の分離 | ADR-0044 の節分離（Alternatives 未決 vs Decision） | 導入 5 日、観測期間ゼロ |
| Status lifecycle（Proposed/Observing/…） | 台帳 state machine（candidate→blocked→ready→終端 4 値） | 稼働中 |

**隙間はほぼ無い**。唯一 RFC が固有に足すのは「複数案を長文で比較する独立文書」だが、その需要の現物は blocked 3 行と ADR 未決 2 件の計 5 件で、独立 document class を正当化する量ではない。

さらに決定的なのは、**ユーザーの RFC 案は ADR-0044 Alternatives の未決項目「ADR を廃止し desire-frontier のように仮説台帳だけにする」の変奏**だという点。その再訪条件は「Review-when 導入後も『ADR に縛られる』観測が続いたら」であり、導入 5 日で未発火。今 RFC を導入すると 0044 の効果測定を汚染し、同じ問題に 2 つの新機構を重ねることになる。

Hypothesis 別判定:

- **A（台帳から未決を分離すれば ready に限定できる）**: 反証。Pending は既に 4 行。分離対象の blocked 3 行を RFC へ移すと、triage loop の照合対象が 2 ファイルに割れ、claims.py / dead-band / digest の配線を全部二重化する
- **B（観察・比較・doctrine 変更は RFC の方が自然）**: 反証。それらは blocked + 照合先の規律（「照合できないなら blocked に入れない」）が既に受け止めており、RFC 化はこの入場規律を失う退行になる
- **C（RFC=how considered / ADR=what decided の責務分離）**: ADR-0044 が同一文書内で達成済み。文書を割ると「どの deliberation がどの decision に至ったか」の参照が 1 hop 増える
- **D（RFC は肥大を移すだけ）**: 妥当。CA ADR-0095 の実測（台帳機構は 2 日で 5,000 行に肥大）と task-stocktake の「肥大は機構でなく archive で解く」がこの repo 固有の反証を既に持つ

## 4. Alternatives

RFC を導入しない解決策 3 案（実問題 = Done 節残存 + 行内履歴増加に対して）:

**案 1: 単一表 Done 節の archive 規約**（推奨・最小）
- task-stocktake の archive 節に 1 文追加: 単一表の Done 節は N 件超で `.notes/archive/TASKS-done-YYYY.md` へ mv（store 形式の `.notes/archive/tasks/` と同じ思想）
- 効果: 読み経路 −44.9KB（−85%）。stale risk ゼロ（終端行は不変）。新機構ゼロ（規約 1 文のみ）
- コスト: task-stocktake の 1 節編集

**案 2: 照合ログの畳み込み規約**
- blocked 行の「照合 YYYY-MM-DD … 未発火」を「最新 1 件 + 通算未発火回数（初回日付）」に畳む規約を task-triage の dead-band 節に 1 文追加
- 効果: blocked 行の単調増加を停止。照合履歴の完全な生データが要る場面は git log が持つ
- コスト: task-triage の 1 文 + 無人 cycle prompt の 1 文

**案 3: RFC minimal 導入**（比較のため）
- `rfcs/` + Status/Created/Revisit-When。コスト: 新 document class の語彙定義（task-stocktake 相当の正本が要る）、lint 追加、triage loop の照合対象追加、harness-sync 対象追加、stocktake 兄弟（rfc-stocktake）がいずれ必要、ADR-0044 との境界定義（「未決 Alternatives と RFC はどちらに書くか」という新しい ambiguity）
- 得るもの: 現在 5 件の未決項目の置き場 — 既に住処がある
- **却下**: agent が読む context は純増、ambiguity も純増、scaffold dissolution 方針と逆行

**案 4: RFC で台帳の中間層（candidate/blocked）を置き換える**（議論で追加検討 → 却下）
- RFC lifecycle は既存 state machine と 1:1 対応（Proposed=candidate / Observing=blocked / Accepted=decided / Rejected=dropped / Withdrawn=retired）で、意味の追加ゼロの改名。語彙正本・triage・claims 配線の全書き換えは純粋な churn
- 固有コスト: blocked→ready がセル 1 編集で済む現状に対し、Accepted RFC → Task 起票という cross-file の継ぎ目が生まれ、orphan（RFC は Accepted なのに Task 無し等）を誰も lint しない
- メリット 3 つのうち「1 論点 1 ファイル」は store 形式が、「問いの保持」は retention policy 変更が新語彙ゼロで提供。差し引き明確にマイナス

**案 5: RFC で台帳全体を置き換える**（議論で追加検討 → 却下）
- 継ぎ目問題は消えるが、台帳は既に「deliberation と実行を 1 class に持つ」構造なので、全置き換えは**現状の改名に収束**する
- 改名の得失: 得 = genre 信号（LLM が RFC 形式の読み方を事前に知っている）— ただし効くのは deliberation 行のみ。失 = ①実行行への genre ミスマッチ（chore を RFC と題すと「提案段階か？」という誤読を注入）②dispatch 語彙（ready/claim/lease）は RFC status が覆えず語彙は縮小でなく拡大 ③実測で鍛えた規律（blocked 入場規律、done/retired 区別）の新語彙下での再導出コスト
- RFC の実利（節構成）は、store 形式の本文が自由記述である現行規約の内側で、deliberation の重い行だけが RFC 的節構成（Question/Evidence/Alternatives/Revisit-When）を採ることで機構変更ゼロで取れる — 文体の選択であって機構ではない

## 5. Recommendation

**DO NOT ADOPT**

根拠（この repo 固有の証拠のみ）:

1. RFC が担う 5 機能すべてに稼働中の担い手がある（§3 の表）
2. RFC 案の中核は ADR-0044 Alternatives の既存未決項目の変奏で、その再訪条件（導入後も縛られる観測が続く）は 5 日経過・未発火。先行判断の観測期間中に同じ問題へ新機構を重ねない
3. 実際の肥大は Done 節 85% と行内履歴で、document class 不足ではない。task-stocktake 自身が「肥大した台帳は機構でなく archive で解く」と正本化済み
4. blocked の入場規律（照合先を書けないなら入れない）は「まだ意思決定すべきでない論点」への**現役のフィルタ**であり、RFC はこれを迂回する安い起票経路を新設してしまう — 台帳肥大の最大の入口が「起票が最安の経路」であること（CA ADR-0095、rules/common/task-tracking.md）と正面衝突する

代わりに案 1 + 案 2（archive 規約 + 照合ログ畳み込み、合計 2〜3 文の規約追加）を提案する。

### Authorship-strategy 観点の評価（議論で追加）

「deliberation を一級の成果物として保持する」価値は本物だが、authorship-strategy 自身が既に制度化している（SKILL.md:199-230 inquiry-first 節 — 「gate を通れる形をしていない思考が存在できない」を失敗モードと名指し、**問いの正本 = manifesto の open-question set** と定義済み。desire-frontier の仮説台帳と ADR-0044 未決 Alternatives はその実装）。

- 問いの先行帰属: 価値は本物だが担い手は DOI/ORCID 層（authorship ADR-0013）。~/.claude は worked-implementation 側の repo で priority-claim 装置ではない
- RFC genre の diffusion 利点: 本物だが genre の選択の話で、置き場が harness である理由にならない。doctrine repo 側（AKC / desire-frontier）の判断
- harness rfcs/ 新設は問いの正本を 2 箇所にする（redundant channel — 確立済み feedback に抵触）

**authorship 観点が照らした本物の隙間**: harness 台帳で `dropped` / `decided` として消える deliberation のうち doctrine 価値のある問い（例: T-REVIEW-GENERATION-RATE の「台帳の肥大 < コードの肥大の非対称性は一般に成り立つか」）を manifesto OQ set へ昇格させる配線が存在しない。**回収案（昇格配線）**: task-triage の終端判定に 1 問追加 —「この行に doctrine 価値のある問いが残るなら、閉じる前に manifesto OQ set へ登録する」。新 document class ゼロ、規約 1 文。

## 6. Proposed Model

RFC は導入しないため、既存 flow を明文化して示す（新設ではなく現状の記述）:

```
設計上の疑問・仮説
  ├─ 照合先を書ける（機械照合可能）────→ 台帳 blocked（再開条件/照合先/成立時）
  │                                        └─ launchd triage が週次照合 → 発火で ready
  ├─ 採否の判断が人間に要る ──────────→ 台帳 candidate → digest で 1 問ずつ
  ├─ 判断に付随する生きた対抗案 ──────→ ADR Alternatives「未決 — 再訪条件」
  ├─ repo 非依存の構想 ────────────────→ memory concept_* / project_*
  └─ 照合先も採否も書けない ──────────→ dropped（再発見されるものは保持しない）

判断が出た → ADR（Review-when 付き）→ 残実行作業は台帳 ready → 実装
```

分類規則（導出したもの）: **「照合先を書けるか」→「採否が残っているか」→「判断に付随するか」の 3 問**で全項目が既存の置き場に落ちる。RFC が必要になるのは 3 問すべてに No で、かつ保持する価値がある場合のみ — その場合の現行の答えは `dropped`（保持しない）であり、これは意図的な設計（将来の自分への予告を溜めない）。

## 7. Migration Sketch

RFC 移行は不要。実問題への最小 migration:

1. Done 節 38 行を `.notes/archive/TASKS-done-2026.md` へ mv（1 回、git mv 相当。履歴は git が保持）
2. blocked 3 行の照合ログを「最新 1 件 + 未発火 N 回（初回 YYYY-MM-DD）」へ畳む（1 回、~10 分）
3. task-stocktake に archive 規約 1 文、task-triage に畳み込み規約 1 文を追記
4. （authorship 昇格配線）task-triage の終端判定に「doctrine 価値のある問いが残るなら manifesto OQ set へ登録してから閉じる」の 1 問を追記

全件分類・全件移行は不要 — Pending 4 行は現在の置き場が正しい。

## 8. Deletion Criteria

（RFC 不採用のため「制度の廃止条件」は該当なし。代わりに**本判断の再訪条件**を定義する）

次のいずれかが観測されたら DO NOT ADOPT を再訪する:

1. **ADR-0044 の Review-when が発火**（「ADR に縛られる」観測が Review-when 導入後も続く）— その時の第一候補は 0044 Alternatives の既存未決案「仮説台帳」であり、RFC はその実装形の一つとして比較する
2. **blocked が ~10 行を超え、Pending の主役が実行でなく観察になる** — 単一表 1 セルでの deliberation 保持が構造限界に達した証拠。その時は RFC 新設より先に store 形式（1 論点 1 ファイル）への移行を検討する（既存語彙・claims.py がそのまま使える）
3. **ADR Alternatives の「未決 — 再訪条件」が誰にも照合されない実例が出る** — 現在 ADR の未決項目は triage loop の照合対象外。件数が増えて手動照合が漏れ始めたら、置き場でなく照合の配線を直す

いずれの場合も、まず既存機構の拡張（store 化 / 照合対象の追加）を RFC 新設より先に評価する。
