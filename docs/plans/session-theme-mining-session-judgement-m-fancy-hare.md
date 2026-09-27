# レビュー履歴の 1 回調査 — 手動棚卸しは反復指摘を見落としているか

## Context

`review-to-lint` は「reviewer を 1 つ選び、そのチェックリストを 3 分類して機械項目を script
へ降ろす」skill である。入口が**チェックリスト**に固定されているため、lint 化できるのは
reviewer が既に明文で持っている項目だけで、**実際に何度も出ている指摘**には入口が無い。

候補台帳 RFC-0005 の 12 件も `agents/` 25 本 + `skills/` 67 本のチェックリストを読んで出した
供給側の棚卸しで、RFC 本文自身が「機械化率最大の citation-formatter は直近需要が無い」と認め、
「優先順は機械化余地でなく需要の発火条件」へ原則を切り替えている。

問いは 1 つ: **チェックリスト起点の棚卸しは、履歴に残る反復指摘を見落としているか。**

これに答えるのに機構は要らない。1 回の手調査で足りる。

## この plan がやらないこと（architect 判定 2026-08-29 を受けて）

初版は `scripts/review_history.py`（抽出 + 親↔subagent 紐づけ + followup 窓切り出し +
`--cross-repo` + tests + uv sub-project）を新設する設計だった。却下:

- **ADR-0055 Decision 5**（2026-08-27）は「commit body に 1 行残して捨てる。**回収機構
  (tick sweep 等) は作らない**」と決め、Alternatives で「起票の遅延回収」と「監視計器の
  新設」を明示却下している。捨てた指摘を transcript と commit message から収穫する script は
  この却下対象そのもの。ADR-0055 の Review-when はどれも発火しておらず（見逃しの実害観測
  なし）、supersede に足る新観測は無い。「指摘が流れて消えている」は欠陥ではなく
  ADR-0055 が設計した状態である。
- **ADR-0056 Decision 5** が却下の射程を狭めた条件は「新 hook・新 script・新セッション・
  自作計器のいずれも増えず、増えるのは既存 config の行だけ」。新 script はこの狭めた側にも
  入らない。
- **順序が逆だった。** followup 窓を全 58 件に前倒しで切り出す必要は無い。分類を先に行い、
  生き残った候補クラスだけ後から手で確認すれば、紐づけ機構（最脆弱部）ごと消える。
- **CA ADR-0095 と同型。** 台帳を扱うコードは `claims.py` だけという現行規律に対し、
  紐づけ・欠測率・cross-repo・突合検算を持つ script は同じ成長曲線の種。初版 plan の
  Verification 節が既に「抽出漏れ検算」「null 率の可視化」を要求していた時点で、
  計器のための計器が始まっていた。

**2 回目の手調査を要求される事態が起きたら、それが script の需要トリガー。** その時点で
ADR-0055 の supersede 込みで再提案する。

## インタビューで確定した設計（維持）

| 項目 | 決定 |
|---|---|
| 一次 corpus | `~/.claude/projects/<project>/<session-id>/subagents/agent-*.jsonl`（reviewer の最終報告） |
| 反復の単位 | **指摘クラス（意味単位）** — 「ADR に Review-when が無い」等 |
| 範囲 | harness 1 repo・全期間。cross-repo は今回やらない |
| 行き先 | 採用反復 → **lint 候補**、却下反復 → **退役候補**（形骸規約・reviewer remit のズレ） |
| 成功基準 | 下の事前登録を満たす反復クラスが RFC-0005 の 12 候補の**外**に出れば合格 |
| 非目標 | reviewer の射程外にある欠陥クラスの発見（生存者バイアス） |

## 事前登録（クラス粒度の gaming を封じる — 調査開始前に固定する）

クラスの粒度は自由変数なので、細かく切れば「12 候補に無いクラス」はほぼ必ず作れる。
先に閾値を決める:

- **反復** = 同一クラスが **3 回以上**、かつ **2 セッション以上**にまたがる
- **採用実績** = そのクラスの少なくとも 1 件が採用されている（候補に絞って手で確認）
- **regime タグ** = 各クラスに出所 regime を付ける。ADR-0055 前（6 系統・high effort）/ 後、
  および退役 reviewer 由来（python-reviewer = ADR-0039、旧 code-reviewer = ADR-0042）。
  **退役 reviewer 由来のみで構成されるクラスは合格判定に数えない** — その reviewer はもう
  走らないので lint 化しても需要が無い
- 合格 = 上記を満たすクラスが RFC-0005 の 12 候補（および「やらない」5 件）のどれにも
  対応しないものとして 1 件以上ある

## 計測済みの事実（この plan の前提）

- subagent transcript は保存されている: `projects/<project>/<session-id>/subagents/agent-*.jsonl`。
  harness で 63 セッション / 247 ファイル / 146MB。設定変更は不要。
- 組込 `/code-review` の findings も subagents に入る。先頭 user message が
  `` `medium effort → 3+5 angles × 6 candidates → 1-vote verify → ≤8 findings` `` という固定署名。
- reviewer 種別は subagent 冒頭の user message で判別できる。**`agentType` フィールドは無い。**
- 親 transcript と subagent は id で繋がらない（親に `agentId` が無い）。
- 1 ファイル 100〜450KB。最終 assistant message のみを切り出す。
- `ReportFindings` の構造化 tool_use は全 project で 0 件（16 件のヒットは skill 本文の
  テキスト）。抽出は自然言語パースになる。
- reviewer 起動実績（親の Agent tool_use）: code-reviewer 18 / adr-reviewer 16 /
  security-reviewer 14 / python-reviewer 5 + writing 系 ≈ 5。**うち python-reviewer と
  code-reviewer は退役済み** = 23/58 が退役 reviewer 由来。

## 手順（1 セッション・コード資産ゼロ）

すべて scratchpad で行い、コミットしない。

**Step 1 — 抽出（jq 2 本）**

```bash
cd ~/.claude/projects/-Users-<user>--claude
for f in */subagents/*.jsonl; do
  echo "=== $f"
  # 種別同定: 冒頭 user message
  jq -r 'select(.type=="user")|.message.content?
        |if type=="string" then . else (map(select(.type=="text").text)|join(" ")) end' "$f" \
    2>/dev/null | head -1 | cut -c1-200
  # 報告本体: 最終 assistant text
  jq -r 'select(.type=="assistant")|.message.content?|select(type=="array")
        |.[]?|select(.type=="text")|.text' "$f" 2>/dev/null | tail -1
done > /tmp/.../reports.txt
```

`session-judgment-mining` Step 2 の検証済み人間発話パターンは Step 3 でだけ使う（再実装しない）。

**Step 2 — 通読とクラス化**

`reports.txt` を通読し、指摘クラスへ束ねる。各クラスに 発生回数 / セッション数 / 出した
reviewer / regime タグ / producer 実例を付ける。引用のまま残す（要約すると証拠力が消える）。

**Step 3 — 候補に絞って採否を確認**

事前登録の閾値（3 回以上・2 セッション以上・非退役 regime を含む）を満たしたクラス**だけ**に
ついて、`git log` と該当セッションの後続（Edit / 著者発話 / commit）を手で見て、採用 / 却下 /
不明を付ける。全件には行わない。

**Step 4 — 突合と判定**

生き残ったクラスを `rfcs/0005-review-to-lint-rollout-ledger.md` の 12 候補 + 「やらない」5 件と
突合する。

## 着地

- **合格**（12 候補の外に条件を満たすクラスが 1 件以上） → RFC-0005 の候補台帳に日付つきで
  行を足す。**既存台帳の行が増えるだけ**で、ADR-0056 と同じ着地形。skill 化・script 化は
  その候補に実需要が発火してから、既存の `review-to-lint` 入口で行う
- **不合格** → RFC-0005 に日付つき注記 1 行（「2026-08-29 に履歴 58 本を手調査。台帳外の
  反復クラスは出ず、チェックリスト起点の棚卸しで足りることを実測」）。**残渣ゼロ**
- どちらでも ADR は書かない（可逆、既存台帳への追記のみ）

## 開いている判断（今回は決めない）

- lint の置き場規約（reviewer / writer skill の Step か、repo `verify.sh` か、commit hook か）。
  判定軸の候補は **課税率**（その検査が意味を持つ commit の割合）と **既製性**（既製ツールの
  config 行で足りるか、自作 script か）。正本は `review-to-lint` §5 の書き換え
  （ADR-0056 が「免除境界の原則は review-to-lint が正本」の先例）。**実例が出てから書く**
- 掘削を skill 化するか、`review-to-lint` に吸収するか、`review-to-lint` を退役させるか。
  手調査が 2 回要求されてから

## Verification

- Step 1 の抽出件数 ≒ 親 transcript の reviewer 系 Agent tool_use 数（実測 58 ± 数本）。
  大きくずれたら抽出漏れ
- `/code-review` 署名を持つ agent が少なくとも 1 件は取れている
  （既知: セッション `948c2e02-…` の subagents 9 本に 1 件ある）
- 判定は事前登録の閾値だけで下す。閾値を後から動かさない
- リポジトリに新規ファイルが 1 つも増えていない（`git status` がクリーン）
