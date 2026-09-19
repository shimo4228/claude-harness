<!-- origin: shimo4228 -->
<!-- rationale: ADR-0001 + ADR-0035 — 外部更新との diff に必要な origin schema と探索パス、
     および skill-creator への命令形配線（ADR-0018 の命令形 fallback、2026-08-22）を常駐 -->
<!-- review-when: origin 管理または skill discovery path を変えた時 /
     skill-comply Tier 1 の配線あり / なし 2 arm で、なし arm が同等かつ十分高い時（命令形配線を外す — ADR-0046 Review-when 注記） -->
# Skill Origin Tracking

skill / agent / rule には `origin` を付ける。YAML frontmatter が無い文書は先頭の
`<!-- origin: ... -->` を使う。

| origin | 意味 |
|---|---|
| `shimo4228` | 自作 |
| `ECC` | ECC 未改変 |
| `{org/repo}` | 外部 repo |
| `community` | 出所を特定しない外部導入 |
| `auto-extracted` | learn-eval 出力 |
| `{origin}-customized` | 外部由来を内容編集 |
| （symlink、repo 外） | 外部ツール同梱 skill。origin は link 先が担い frontmatter には書かない（例: `hunk-review`） |

任意 field `replaces:` — 置き換えた前身（origin / sha / 日付）。外部由来を自作で書き直したとき
origin を反転してここに系譜を残す（例: `skill-creator`、2026-08-22）。lint は検査しない。

skill の正本は `skills/<name>/SKILL.md`。`commands/` は使わない。

**skill / agent を新規作成・大幅改修するときは、書く前に skill: `skill-creator` を読む**
（入口の intent 確認と fresh-context の草稿ゲートを持つ。自発発火は文言改良で伸びないので命令形で
配線する — ADR-0018。新規作成は `hooks/skill-create-notice.sh` も思い出させる）。
**既定は肯定形で書き、やめる項目は本文から消す。禁止を書けるのは、対象が grep 可能な具体的動作で、
既定挙動が逆だと観測されていて、機械ゲートが無いときだけ** — 理由を 1 句添える。文体・内部過程への禁止は
肯定形に言い換える（ADR-0070）。**小さな追記でも現行規則として書く** — 編集日・版差語・退役物は git と
ADR が持つ（as-of 日付は claim にだけ）。正本は skill-creator §3、機械検査は
`scripts/hooks/harness_lint.py`（ADR-0061）。
公開は skill: `harness-sync`。
