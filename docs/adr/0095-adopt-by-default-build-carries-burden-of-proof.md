# ADR-0095: 自作の側に証明責任を置く — 部品ごとの既製品の問いと 4 つの停止条件

## Status

accepted — commit「feat(skills): search-first が採用を既定にし、依存追加に dependency intake を置く」（b5636f3、
2026-09-26）が置いた Build の基準「どの候補も埋めない gap を名指す」を、候補ごとの停止条件と抱える保守の記述に
置き換え、intake を MCP server・plugin・外部 skill に広げる。[ADR-0066](./0066-search-first-report-contract-and-scout-retirement.md)
Decision 1 と Consequences Negative に注記する

## Date

2026-10-24

## Context

著者（2026-10-24）: 「Search-first があるものの、なかなか既存の MCP や OSS などのツールを導入しない気がする」。続けて
「車輪の再発明を防いで、どんどん本来の目的を果たしたい。自分で作るとその部分の保守も必要だし、品質向上にも労力を
注ぐことになる。多少無理をしてでも既存ツールを使うという形の方が良くないか。導入前にはセキュリティチェックをかける」。
plan 全体を丸ごと置き換える既製品を問う案は「重すぎる」として退けた。

前の状態: 2026-09-26 に同じ趣旨の問い（「search-first を毎回回すのにいつもスクラッチで作る」）から commit b5636f3 が
入っていた。search-first は Adopt を既定とし、report に `## Verdict`（Adopt / Adopt-part / Build — gap）を持ち、
implementation-chain は lockfile に入る package に dependency intake を掛けていた。plan での Verdict の書き手は
[ADR-0086](./0086-research-gate-before-plan.md) で lead に決まっていた。それから 1 か月、既定は効いていなかった。

同日の診断（この repo のファイルを読んだ結果、2026-10-24）:

- `docs/plans/*.html`（packed / artifact を除く 7 本）で `Verdict` の語を含むものは 0 本（`grep -c Verdict`）。書き手は
  決まっていたが、plan に Verdict が書かれていない
- `docs/plans/research/` の外部調査 report 8 本（`kind: external`、2026-10-04〜10-18）のうち 7 本は、自作物の設計根拠を
  問うていた（例:「persona-read を単独 skill に切り出す設計の根拠」）。例外は 2026-10-04-research-plan-mode
  （「既存の仕様・先行実装…で使えるものはあるか」）。research gate は plan の段で開くので、作るかどうかは問う前に
  決まっていることが多く、結果は「移せる部分」（アイデアの輸入）で終わる
- Build の基準が「gap を名指す」だけで軽い。候補ごとに何が外れたかも、自作で抱える保守も書かずに Build が通る。
  一方の Adopt は intake（audit・保守と採用・license・Security Review Y）を通る。intake は MCP server・plugin・外部
  skill を対象にしていなかった
- 反例として、導入は search-first の外では起きている: plugin の設定には 2026-10-24 時点で 15 件（うち有効 13）が
  並ぶ（設定ファイルは gitignore 下）。[ADR-0084](./0084-retire-codex-review-skill-for-official-codex-plugin.md) は
  自作の codex-review skill を公式 Codex plugin に置き換えた。入口は著者自身の発見で、search-first ではない

## Decision

1. **Build に証明責任を置く。** 正本は `skills/search-first/SKILL.md` §3 Verdict。Adopt は理由を要さず、薄い adapter で
   吸収できる摩擦（流儀の違い・使わない機能・版の固定）は受け入れる。Build は候補ごとに「外した停止条件」と
   「抱えるもの（コードの大きさと保守）」を書き、どちらかが欠けた Build 行は Adopt と読む。「既存ツール」は
   library・CLI・MCP server・plugin・公開 skill・agent runtime の native 機能を含む
2. **停止条件は 4 つ**（正本は同 §3）: (1) 内部を fork / patch しないと使えない (2) つなぎのコードが自作と同じくらい
   大きい (3) dependency intake で落ちる (4) plan の目的そのものを担わせることになる
3. **問いは plan 全体でなく部品ごと。** search-first §0 に、plan の目的でなく手段にあたる部品（parser・CLI の
   wrapper・eval runner・hook 内の検査など）を並べ、部品ごとに Library / tool の問いを 1 行ずつ立てる手順を置く。
   implementation-chain の条件付き発火の列挙に「`feat` / `refactor` × 部品の既製品」を置き、plan に部品ごとの
   Verdict 行を書かせる
4. **Verdict の書き手**: Quick は report が持ち、plan では lead が plan に書く（ADR-0086 の分担のまま）。Full の
   adversarial 角度は、先頭候補を停止条件に当てる役にする
5. **dependency intake を MCP server・plugin・外部 skill に広げる。** audit の対象が無いので、入る本体（hook・script・
   MCP の tool 一覧・外部への送信先）を untrusted data として読む。取得した版（commit sha か版番号）は、導入する
   commit の本文に `Intake: <tool> <版>` の 1 行で残す（設定ファイルは gitignore 下で後から読めないため）。package の
   導入も同じ行を書く
6. 経緯は `skills/search-first/MAINTENANCE.md` に置く（公開 copy からは harness-sync が除く）

## Review-when

- 2026-12-31 の triage で数える: 期間内の `feat` / `refactor` commit が新規ファイルとして部品（script・parser・
  client）を足したのに、本文の `Plan:` 行のリンク先 plan に部品の Verdict 行が無いもの（`git log --diff-filter=A` と
  `docs/plans/*.html`）。2 件を超えたら証明責任が書き手に効いていない — 下の「hook で強制」を再訪する
- `git log --grep "Intake:"` で拾った導入のうち、3 か月以内に外した commit が 2 件を超える — 「多少の無理」の上限
  （停止条件 2 と 3）を厳しくする
- RFC-0022 の影の比率の再測定（2026-11）で、外部調査の大半が search-first を通らないままなら、既定を変えても
  入口に届いていない。配線（rule の命令形か hook）で扱う

## Alternatives Considered

- **plan が作るものを丸ごと置き換える既製品を問う（Full の adversarial 角度に足す）** — 不採用（著者判断 2026-10-24
  「重すぎる」）。plan の目的は自作の側にあり、丸ごとの置き換えはほぼ常に「無い」で終わる。車輪は手段の部品の側にある
- **b5636f3 のまま（Build は gap の名指しで足りる）** — 不採用。1 か月で plan の Verdict が 0 本、Build の基準が軽く、
  既定が効かなかった
- **停止条件を置かずに Adopt を既定にする** — 不採用。つなぎが自作より大きくなる採用や、内部 patch を抱える採用は、
  自作と同じ保守を別の形で抱える。著者の「多少無理をしてでも」の「多少」を測る線が要る
- **部品ごとに Full（並列の researcher）を回す** — 不採用。部品の数だけ調査が増え、plan の前段が重くなる。部品の問いは
  1 行で、決めかねる部品だけを Full に回す
- **plan の Verdict 行を hook で強制する** — Open — revisit when: Review-when 1 が成立したとき。今は書き手への規約で
  足りるかを先に見る

## Consequences

### Positive

- 自作の部品が増えるたびに理由が plan に残り、後から「なぜ作ったか」を読める
- 手段の部品を既製品に寄せた分、保守と品質向上の手間が外に出る
- MCP server・plugin・外部 skill の導入にも intake の手順が付き、導入の版が commit 本文に残る

### Negative

- plan が 1 段重くなる（部品の列挙と Verdict 行）
- 外部ツールへの依存が増え、上流の破壊的変更・保守停止・供給網の危険を抱える。版の固定と intake で受けるが、
  更新の追従は自作に無かった仕事として残る
- intake は遡らない。既に有効な plugin 13 件は今回の手順を通っていない
- 公開 repo `shimo4228/search-first` の README は、harness-sync を回すまで旧い記述のまま
- 戻すコスト: search-first と implementation-chain の文面、ADR-0066 の注記 2 つを戻すだけ（コードは無い）

### Neutral / Follow-ups

- [ADR-0001](./0001-ecc-skill-management-policies.md) / [ADR-0008](./0008-ecc-local-only-management.md) の ECC skill の
  ローカル取り込みは、本 ADR では Adopt-part の一形態にあたり、変えない
- 外部の plugin を自作で置き換える向きの判断（ADR-0084 の逆向き）にも、同じ停止条件が掛かる
