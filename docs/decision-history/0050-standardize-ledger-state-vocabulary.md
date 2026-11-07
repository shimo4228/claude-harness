# ADR-0050: 台帳の状態語彙を標準語彙へ全域移行する

## Status

accepted

## Date

2026-08-25

## Context

[ADR-0049](./0049-unify-task-ledger-into-public-rfcs.md) Decision 3 は `rfcs/` 一元台帳の
状態語彙を、既存の台帳 8 語（`candidate` / `ready` / `in_progress` / `blocked` / `done` /
`decided` / `dropped` / `retired`）の流用と定めた — 第二語彙を作らないという原則の適用
だった。

同日のうちに、非標準語彙の恒常コストが実証された。judge セッション自身が、同じ 1 日の中で
`dropped` / `retired` / `withdrawn` の標準語対応を 2 通りに書いた。写像の定義が skill:
`task-stocktake` の 1 箇所に正本として置かれていても、実際の写像はセッションごとに頭の中で
再構成され、そこでずれる。定義の所在と適用時の再現性は別問題だった。

この drift への緩和として、各エントリの `## Status` 節に標準語 gloss を書く運用を導入し、
語彙自体の全域標準化は RFC-0003 として起票した。当初計画は gloss 運用を 3 ヶ月観測してから
標準化に進むかを判断する、というものだった（[ADR-0048](./0048-sdlc-playbook-translation-and-rfc-conformance.md)
の注記に記録済み）。

著者はこの観測期間を待たず、標準化の実施を指示した（2026-08-25「Rfc3 も opus 実装させといて」）。
本 ADR はその指示を受けて、観測待ちだった標準化を前倒しで確定する。

## Decision

台帳の状態語彙を全域（`rfcs/` store・単一表・skill / rule の規範記述・`claims.py` の既定値）
で次の 9 語へ移行する。

| 旧（8 語） | 新（9 語） | 語の出所 |
|---|---|---|
| `candidate` | `draft` | RFC 標準 |
| `ready` | `accepted` | RFC 標準 |
| `in_progress` | `in_progress` | issue-tracker 標準（不変） |
| `blocked` | `blocked` | issue-tracker 標準（不変。RFC 標準に state 語彙は無い） |
| `done` | `done` | issue-tracker 標準（不変） |
| `decided` | `resolved` | issue-tracker 標準（build なしで決着） |
| `dropped` | `rejected` / `withdrawn` に分裂 | RFC 標準。否決 = `rejected`、やらない選択・取り下げ = `withdrawn`（迷ったら `withdrawn`） |
| `retired` | `obsoleted` | IETF 標準（対象消滅。「何が対象を消したか」の引用必須規定は不変） |

1. 語の出所の分担線は、**RFC 世界に対応がある提案 lifecycle 語は RFC 標準語、RFC 世界に
   無い実行系状態は issue-tracker 標準語**とする。これは γ 一元化（提案と作業が 1 店舗）の
   語彙面での素直な帰結である。
2. Status 節の標準語 gloss 必須規定は廃止する。語彙自体が標準になったため、gloss は不要
   になる。Status は state 語 + 現在地 + 日付の構成のままとする。
3. `claims.py ready` の既定 `--state` を `accepted` に変更する。subcommand 名 `ready`
   自体は維持する — 「着手可能なものを問う」動詞句であり、hook 文言・docs に広く参照される
   interface のため、改名 churn を避ける。
4. 意味は 1:1 写像とする（`dropped` のみ 1:2）。過去の commit message・ADR 本文・
   `.notes/archive/` の旧語は書き換えない。本 ADR の対応表を archaeology の橋とする。
5. [ADR-0049](./0049-unify-task-ledger-into-public-rfcs.md) Decision 3 の「既存 8 語流用」は
   本 ADR が部分的に置き換える。第二語彙を作らない原則自体は維持する — 全域一括の移行なので
   語彙は常に 1 つのままである。0049 には日付つき注記を置く（main-loop 側で実施）。
6. RFC-0003 の当初計画（gloss 運用 3 ヶ月観測 → 判断）は著者指示により前倒しされ、本 ADR の
   標準化決定に置き換わる。

## Review-when

- 新語彙でも状態語の写像・使い分けの drift が再発した時（語彙でなく構造の問題と判断し直す）
- substrate が native の task ledger 機構を持った時
- ADR-0049 が supersede された時（本 ADR も道連れで再照合）

## Alternatives Considered

### gloss 運用の観測を待つ（RFC-0003 の当初 Next action）

各エントリの Status 節に標準語 gloss を書く運用を 3 ヶ月観測してから標準化を判断する当初
計画。却下: 著者判断で前倒しされた（2026-08-25）。gloss は per-entry の緩和にすぎず、
skill / rule の規範記述側の写像 drift は gloss だけでは残ったままだった。

### `rfcs/` のみ標準語に替える

単一表など台帳の他形式は旧 8 語のまま残し、`rfcs/` だけ新語彙にする案。却下: 第二語彙になる
（ADR-0049 Alternatives で既に却下済みの構図の再来）。

### `done` を `implemented` に替える（Rust RFC の完了語）

Rust RFC lifecycle の完了語 `implemented` に合わせる案。却下: 一元台帳は運用タスクも運ぶため
issue-tracker 標準の `done` の方が自然であり、`done` は drift の実績も無い。

## Consequences

### Positive

- 状態語が substrate の訓練済み語彙になり、セッション間の写像 drift が根治する見込みが立つ。
  gloss の運搬コストが消える。
- `rejected` / `withdrawn` の分裂により、「誰が閉じたか」（判断で否決 vs 取り下げ）が state
  だけで読めるようになる。

### Negative

- 過去の commit message・ADR・archive の旧語と断絶する。対応表で回収するが、grep は 2 語彙
  世代を跨ぐことになる。
- 語数が 8 → 9 に増える。2026-08-16 の 6 → 4+4 縮約から 9 日での再改編であり、語彙 churn
  自体が一時的な drift 源になりうる。
- 単一表 9 repo + rfcs 19 エントリ + skill / rule / `claims.py` / bats の横断 sweep を要する
  （実施は同日の build dispatch と judge 側編集）。

### Neutral / Follow-ups

- RFC-0003 は実装完了時に `done` で終端する（経緯は同エントリの Status に記録する）。
