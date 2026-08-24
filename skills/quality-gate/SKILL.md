---
name: quality-gate
description: "人間向け公開物の受け入れゲート。完成稿と project の publication channel contract を読み、必須 reviewer verdict・機械検査・最新 title-reviewer findings が揃ったかを集約して PASS / FAIL / BLOCKED を返す。Use when — 公開直前、他人の原稿を公開してよいか確認するとき、/quality-gate <file>。NOT for — prose の再レビュー（→ editor / essay-reviewer / prose-clarity-reviewer）、タイトル候補の点検（→ title-reviewer）、公開操作（→ project-local publishing skill）、paper / README の専用ゲート。"
user-invocable: true
origin: shimo4228
---

# quality-gate — publication acceptance aggregator

公開可否を新しく評価せず、project が宣言した受け入れ条件の完了を照合する。媒体名、reviewer
名、frontmatter、CLI、公開手順は本 skill にハードコードしない。

## Input

- 完成稿の path
- `<project>/.claude/rules/*.md` の publication channel contract
- contract が要求する reviewer report / deterministic check result
- 本文の最後の構造変更より後に得た `title-reviewer` findings と、著者のタイトル選択

contract は対象 path ごとに少なくとも次を宣言する:

- channel / path matcher
- required reviewers と blocking verdict
- required deterministic checks
- title constraints
- publish handoff

## Procedure

1. 原稿 path を local contract の 1 channel に解決する。0 件または複数件なら推測せず
   `BLOCKED: channel contract missing or ambiguous`。
2. required reviewer ごとに、対象が現在の完成稿であることと blocking finding が解消済みで
   あることを確認する。report が無ければ FAIL。
3. contract の deterministic checks を実行または証跡照合する。秘密・個人 path・未サニタイズの
   生ログは全公開物の共通 blocker とする。媒体固有 validator は contract の command を使う。
4. 最新 `title-reviewer` が本文の最後の構造変更後に実行され、著者がタイトルを選択済みか確認する。
5. prose を再レビューせず、証拠付きで 1 つの verdict を返す。

## Verdict

- `PASS` — contract の全 blocker が満たされ、著者の公開 GO に渡せる
- `FAIL` — 必須 report / check / title decision に未解決項目がある
- `BLOCKED` — channel contract が無い、曖昧、または named artifact を確認できない

```markdown
# Quality Gate Result
Artifact: <path>
Channel: <channel>
Verdict: PASS | FAIL | BLOCKED

## Evidence
- [pass|fail|missing] <contract item>: <source or command result>

## Required next action
- <one concrete action, or "author publication GO">
```

## Boundaries

- 本 skill は reviewer を起動せず、reviewer の判断を上書きしない。
- ADR、memory、過去セッションを受け入れ条件として読まない。現在の contract と現在稿の証跡だけを使う。
- paper は `paper-ecosystem`、README は `readme-writer` の専用 gate を使う。
