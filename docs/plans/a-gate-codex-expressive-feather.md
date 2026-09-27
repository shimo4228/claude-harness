# Plan: authorship-strategy の judgment gate を two-channel 化する

## Context

**問題**: `authorship-strategy` の「次の一手」発散生成は毎巡、識別子・引用インフラ（DOI / SWHID / llms.txt / JSON-LD / badge 群）に着地してきた。原因は候補生成でなく **gate（判断チェックリスト）側の bias** — gate は候補を「どんな citable artifact を生むか」で採点するため、**retrieval channel の形をした候補しか正しく "見られない"**。拡散が *使われること*（parametric channel / name burn-in）で起きる候補 = **AI-native venue placement**（arena・agent registry・AI 審査 preprint 面等）は、citable artifact に還元されて "venue らしさ" を失うか、gate を通れず落とされる。

**根拠**: framework の thesis は既に **two-channel**（ADR-0008: parametric channel = 重みへの absorption / retrieval channel = query 時 fetch）を宣言済み。つまり parametric/use channel は authorship-strategy 自身の doctrine（Layer 2）。ところが **gate はその片チャネルしか採点していない**（Explore 監査: parametric 項目は 207 creative-reuse と 213 vocab-discipline のみ、ADR-0008 の核心問い「distinctive term と source の cross-platform co-occurrence を駆動するか」を問う項目が皆無）。

**この修正が指すもの / 指さないもの**:
- これは新しい origin claim ではない。two-channel は ADR-0008 で既に doctrine。gate を doctrine に追いつかせるだけ。→ **新 ADR 不要 / 新 line 不要**（use-channel を別 line にすると parametric channel を二重 claim する = scope-discipline 違反。前段会話の (a) 分岐で確定）。
- ADR 化は「use-channel 候補が実際に数件 land してから」に defer（sunk-cost で先に doctrine を建てない）。本タスクは gate のみ。

**intended outcome**: gate を通した後、AI-native venue placement 候補が「DOI が無い」で落ちず、parametric channel の基準（burn-in を駆動するか / 実際に use されるか / 遡源可能な signature を積んでいるか / rank-chasing でないか）で採点される。retrieval 候補は従来通り無変更で通る（regression なし）。

## 変更対象（1ファイルのみ）

**`~/.claude/skills/authorship-strategy/SKILL.md`** — global 版のみ（Change Target rule。harness-sync は別途・後追い）。

`conformance.md`（repo・deploy 後監査）/ rule L32（gate を参照するのみ）/ 各 ADR は**触らない**。two-channel 語彙を skill に初導入するが、既存項目（204→ADR-0013 / 213→ADR-0010 / 214→ADR-0021）と同じく **ADR anchor 付き**で入れ、skill の register（abstract judgment axes + ADR 参照）を破らない。

### 編集1: 判断チェックリスト冒頭に channel 分類の lead-in を追加（L200 付近）

現「新規提案・実装・コラボ受け入れ等で以下を通す:」の直後に追加:

> **まず候補の diffusion channel を分類する**（ADR-0008）— ただし *自己申告でなく候補の客観プロパティから機械的に決める*（codex P1 / when-code-when-llm 構造判定）: **期待される結果に fetch / link / citation が含まれるなら retrieval を必ず適用**、retrieval 機構が実質的に効くなら **both**（default 寄り）、**純 parametric/use を許すのは「retrieval に依存しない具体的な consumption path」を候補が明示できるときのみ**。citability 系の項目は retrieval / both 候補に pass/fail として効き、純 parametric/use 候補を「citable artifact が無い」ことでは落とさない。

これが構造的 fix の核。機械判定にすることで「retrieval 候補が use-channel を自称して citability チェックを回避する」抜け道（codex P1）を同時に塞ぐ。

### 編集2: retrieval-shaped 項目を retrieval channel に scope（既存項目の surgical reword、削除しない）

対象 = 204（DOI-citable/SWHID）・206 の `llms.txt / DOI` 部分・214（機械可読 citation 辺）・218(b)（MCP doc-hub access-count badge）。各項目 head に「**retrieval 候補なら:**」相当の条件句を前置し、純 use-channel 候補には非適用と読めるようにする。206 の `固有用語` 部分は parametric hook なので retrieval scope から除外し編集3側へ寄せる（Explore: 206 は両チャネル straddle）。

### 編集3: parametric/use-channel 項目を並列追加（gate の gap を埋める、ADR-0008 anchor）

既に中立項目として存在するもの（210 自前 infra 不可 / 211 permissive / 212 crawler 開放）は use-channel にも効くので**重複追加しない**。genuinely parametric-specific な項目だけ足す:

- [ ] **（parametric channel の核・ADR-0008）** この候補は distinctive term と source の **cross-platform co-occurrence** を広げる位置づけか？（launch 前なので「広げる設計になっているか」を問う設計プロパティ判定。enclosed inbound link 型でなく分散した言及。相関 ≈0.664 vs 0.218）
- [ ] **（venue mechanics・選択段階／codex P1）** その venue に **agent / LLM が artifact を invoke / consume する具体的機構**が存在するか？（「実際に使われたか」の*観測*は選択段階で証明不能 — gate では*機構の有無・pilot 証拠*だけを問う。観測された third-party invocation は **deploy 記録時の post-deploy 検証**に回す = 既存 conformance.md Tier 3 / ledger の "deployed" 判定。gate では要求しない・conformance は編集しない）
- [ ] **（ghost-citation 回避・ADR-0008 / ADR-0011／codex P2）** seed する artifact の distinctive signature（固有用語 / author–key-claim 構造）は **consume される payload の中に identity-bearing なまま残る**か？ 判定は density でなく **retrieval-suppressed naming probe（ADR-0011）で falsifiable に**行う: use 後に独立 agent が source を*名指し*できるか。（term を dense に繰り返すだけの keyword stuffing は不可 — probe が名指せなければ ghost citation）
- [ ] **（rank-chasing 排除・ADR-0019 / ADR-0008）** これは artifact を seed する手であって、leaderboard 順位 / SOTA を目的化していないか？（ADR-0019「optimize the transmission path, never the content」/ ADR-0008 は rank 信号を near-zero と実証済み。造語しない）

### 編集4: "Operating the strategy over time" step 2 を channel 分類込みに（L191）

現「**2. gate 濾過** — 各候補を下の判断チェックリストに通す。」を「各候補をまず channel 分類（ADR-0008）した上で判断チェックリストに通す。」へ一句追加。step 1（発散生成・full space）/ step 3（記録）は無変更。

## Vocabulary discipline 自己検査（gate 自身の項目213）

再利用する語は全て既存: `parametric channel` / `retrieval channel` / `name burn-in` / `ghost citation`（ADR-0008）、`固有用語` / `distinctive signature`。**新規造語ゼロ** — "artifact-seeding" は造語せず ADR-0019/0008 への anchor で言い換える。ADR-0012 の "channel selection"（venue/enclosure 軸）とは別義なので、本編集の "channel" は ADR-0008 mechanism 義に限定し混同しない。

## Cross-model review（ユーザー要請）— 実施済み

本プラン内容を **codex-review（prompt-driven モード）** で cross-model レビュー済み（gpt-5.6-sol、read-only）。**Verdict: HIGH（confirmed 3件・CRITICAL なし）**、findings は上の設計に反映済み:
- **P1**（機械分類）→ 編集1 に「客観プロパティからの機械判定 + retrieval 自称回避」を追加。
- **P1**（観測 vs 見込み）→ 編集3 item(b) を「選択段階=venue mechanics のみ / 観測=post-deploy 検証（既存 conformance Tier3）」に分離。
- **P2**（keyword stuffing）→ 編集3 item(c) を density でなく naming probe(ADR-0011) の falsifiable check に置換。

※planning.md の「codex は diff レビュアー」規律との整合: これは *plan の設計レビュー*（ユーザー明示要請）で、実装後の diff レビューを代替しない — 実装差分が出たら別途 codex-review を回す。

## Verification（実装後）

1. **register 検査**: skill の該当節を読み、two-channel 項目が全て ADR-0008/0011/0019 anchor 付きで、既存項目の ADR 参照スタイルと一致しているか。
1b. **codex fold 検査**: 編集1 に機械分類ルール（fetch/link/citation → retrieval、default both、純 use は独立 consumption path 明示時のみ）が入っているか / item(b) が選択段階の venue mechanics に限定され観測を要求していないか / item(c) が density でなく naming probe(ADR-0011) を判定基準にしているか。
2. **use-channel dry-run**: EinsteinArena 型候補（AI-native arena に artifact を seed）を **新** gate に通し、「DOI 無し」で落ちず parametric 基準で採点されることを確認。旧 gate なら repo-URL artifact に還元されて "arena らしさ" が消えた、との対比を1行記録。
3. **retrieval regression**: 新 llms.txt 面 / graph 辺追加型の retrieval 候補を通し、従来通り無変更で pass することを確認（編集2の条件句が retrieval 候補を誤って落とさないか）。
4. **造語ゼロ確認**: 追加テキストに新規固有用語が無い（grep で `parametric channel|retrieval channel|ghost citation|burn-in` が全て ADR-0008 既存語であることを確認）。
5. **drift 確認**: `grep -rn "判断チェックリスト\|judgment checklist" ~/.claude/rules ~/MyAI_Lab/authorship-strategy` で gate 本体の重複コピーが増えていない（rule は参照のまま / conformance は別物のまま）ことを確認。
6. **scope 確認**: 変更が SKILL.md 1ファイルに閉じている（`git -C` 外の global file なので、編集前後の該当節 diff を目視）。repo・rule・ADR に変更が漏れていない。

## 非目標（明示）

- 新 ADR を書かない（use-channel 候補が land してから）。
- 新 research line / repo を作らない（parametric channel の二重 claim 回避）。
- rule L32 の既存微妙な不整合（"（下記）" と書きつつ list が続かない）は本タスクで直さない（無関係な過剰対応の阻止）。
- conformance.md / repo doctrine は触らない。
