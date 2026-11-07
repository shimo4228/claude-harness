# ADR-0014: multi-agent-orchestration.md ルール退役 — native 部分は公式ハーネスに委譲

## Status

accepted（[ADR-0013](./0013-cross-model-review-seam-via-codex.md) の決定 #3 を部分的に上書き）

## Date

2026-06-30

## Context

[ADR-0013](./0013-cross-model-review-seam-via-codex.md) の決定 #3 で `rules/common/multi-agent-orchestration.md`（2 軸 + 9 普遍則 + 反パターン + ハーネス方針）を「多エージェント/クロスモデル判断の正本」として新設した。

運用してみると、ultracode・通常セッションの双方で **実装の委任が消極化**する症状が出た。原因を点検した結果、ルールの大半が公式ハーネスと**冗長**で、かつ drift して有害化していたことが判明した:

- **native throughput 部分**（fan-out / pipeline vs parallel / single-writer-per-scope / worktree 隔離 / cost cap / 構造化ハンドオフ / code-vs-LLM 制御）は、**Workflow tool の description が遥かに詳細にカバー**している。Workflow description は tool として**常に system prompt に在る**ため、ルール化しても決定論ロードの優位すら足していなかった。さらに公式ハーネスは進化し続けるのに対し、自作コピーは更新されず staler になる。
- 冗長なだけでなく**有害**だった。ルール内の「同一モデルを増やしても判断の質は上がらない」「fan-out は <5-6」「ファイルを変更するのは常に 1 エージェント」が **負の prior** を形成し、公式ハーネスの pro-delegation な default を決定論層が上書きして劣化させた。これが委任消極化の震源。
- 唯一の非冗長部分は **cross-model 脱相関 routing**（throughput→native / 脱相関→別モデル）。ただしこれは既に三重に存在する: planning.md Chain Matrix（`codex-review` を能動トリガー）＋ ADR-0013（理由）＋ `codex-review` skill（運用）。ルールはその 4 つ目のコピーにすぎない。

これは `feedback_redundant_channel.md`（既存チャネルが運ぶ情報を二次チャネルで複製しない）と akc-cycle.md の Curate（redundancy / staleness チェック）にそのまま該当する。

## Decision

1. **`rules/common/multi-agent-orchestration.md` を削除する**（git 管理下のため hard-delete、履歴で復元可能）。native orchestration の判断は公式 Workflow / Agent ハーネスに委ねる。

2. **cross-model 脱相関の核は移譲先に残す**。脱相関 routing の能動トリガーは planning.md Chain Matrix（`codex-review` = Y）、理由は本 ADR 系列（0013 + 0014）、運用は `codex-review` skill が保持する。

3. **依存参照を repoint する**。`codex-review` skill の 2 箇所（"Grounded in" / principle 8）を ADR-0013 へ向け直す。rules/README.md のツリーから 1 行削除。

4. ADR-0013 の決定 #3（「判断軸を rule に昇格」）は本 ADR で上書きされる。ADR-0013 の決定 #1（codex-review seam）・#2（throughput は Workflow に集約）は**有効のまま**。

## Alternatives Considered

### (a) 負の prior だけ修正して維持

ルールを残し、委任を抑制する 5 箇所（2 軸 framing / 普遍則 #1 / #9 / 反パターン）だけ直す。一度実施したが、**「native throughput を語る標準ルール」を残すこと自体が drift の震源**であり、公式ハーネスとの冗長は解消しない。対症療法。**却下**。

### (b) 脱相関だけ残す 5 行に痩せる

native 部分を削り cross-model routing の 5 行だけ残す。だが能動トリガーは planning.md に既にあり、痩せたルールは planning.md + ADR-0013 + codex-review の再々掲。標準ルールに「native throughput」概念を残す限り drift リスクも残る。**却下**。

### (c) _archived/ へ soft-delete

可逆性ゲートの慣例（hard-delete 前に soft-delete）。だが git 管理下で履歴から完全復元できるため、`_archived/` は二重の安全網で冗長。ユーザー判断で hard-delete を選択。

## Consequences

### Positive

- 委任消極化の震源（負の prior）を除去。native orchestration は最新の公式ハーネスの default に従う。
- 冗長チャネルが 1 つ減り、Workflow description と自作ルールが食い違う drift リスクが消える。
- cross-model 脱相関の知識は ADR-0013 + planning.md + codex-review skill に集約され、単一の発見経路になる。

### Negative

- 「多エージェントの 2 軸」「team-OS に行かない」というハーネス哲学を毎セッション決定論ロードする層が無くなる。→ ただし設計判断は ADR（0013 + 0014）に記録され、将来の同種の問いには ADR を参照して答えられる。standing rule である必要性は低いと判断。
- ルール本文が参照していた worked framing（普遍則の番号付きリスト等）への外部参照は今後できない。→ codex-review skill から番号参照（principle 8）を ADR へ repoint 済み。他に依存は無いことを grep で確認済み。
