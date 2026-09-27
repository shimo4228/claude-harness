# claude-harness の数字ハードコード撤去 + drift 構造根絶

## Context

GitHub プロフィールに `claude-harness` を pin したところ、repo の About(description)が
`10 skills, 5 agents, 5 rules` と **激しく stale**(実際は 35 / 12 / 7)。ユーザーの本質的な
指摘は「skill 数などをハードコードするのはスジが悪い」= この hub の `CLAUDE.md` にある
**No volatile state** 原則そのもの。集約カウントは churning set なので焼き込むと drift する。

調査で判明した構造:

- **症状**: repo About(`gh repo edit --description` が編集する欄)が stale。
- **真因**: `~/.claude/skills/harness-sync/SKILL.md` の **Step 4** が
  「README に skill/agent/rule の**一覧と数**を更新しろ」と明示指示 → 数字を人手維持に含めている。
- **README 本体の一覧テーブルは現在 fresh**(35/12/7 一致)だが、手/skill 維持なので drift 予備軍。
  各行に**手書きの「Purpose」列(人力キュレーション)**があるのが重要 — 単純再生成では失われる。
- **既存資産**: `scripts/sync-from-local.sh` に既に
  `<!-- BEGIN/END GENERATED: upstream-components -->` の**マーカー自動生成機構**がある(L123-217)。
  同じパターンで Contents テーブルも生成できる。

狙い: (1) 露出している stale な About を volatile-free に直す、(2) 数字を生み続ける真因を断つ、
(3) テーブルの membership を script 管理にして drift を構造的に根絶する — ただし Purpose 列の
人力キュレーションは保持する。

## ① repo description(About)を volatile-free + 誘引的に

数字を落とし(No-volatile-state)、機械抽出の味気なさを解消して「ここから使える部品を
pick できる」と伝える。かつ Claude Code 専用感を薄める — skills は Agent Skills 標準で
cross-tool、rules も移植可能、subagents のみ Claude Code 固有、という実態に忠実に。
可逆だが公開メタデータの書き込み。

```bash
gh repo edit shimo4228/claude-harness --description \
"A curated, MIT-licensed set of Agent Skills, subagents & behavioral rules from shimo4228's daily harness — the skills follow the open Agent Skills standard (Codex / Gemini CLI / Cursor, not just Claude Code). Lift the ones you want."
```

- **Why**: About は pin カード・repo トップに常時露出する最も見られる surface。集約カウントは
  No-volatile-state 対象なので排除。リード語を "Agent Skills"(オープン標準名)にし Claude Code を
  互換ツールの一つとして後置することで、cross-tool な再利用可能性を正確に示しつつ専用感を後退。
  "Lift the ones you want" で pick 可能さを前面化。subagents が Claude Code 固有な点は
  overclaim しない(「skills が標準準拠」とだけ言う)。

## ② 真因: harness-sync SKILL.md Step 4 を修正

`~/.claude/skills/harness-sync/SKILL.md`(global 版のみ。repo コピーは触らない)。

現状:
```
- `README.md` / `README.ja.md` — skill / agent / rule の一覧と数
```
→ 修正:
```
- `README.md` / `README.ja.md` — skill/agent/rule テーブルは GENERATED マーカー間で script が
  自動再生成する(membership は origin filter が正、Purpose 列は既存キュレーションを保持し新規のみ seed)。
  **集約カウント("N skills" 等)はどこにも書かない**(No-volatile-state)。手で直すのは Purpose 文面と
  周辺 prose のみ。**repo の About(description)も同様に volatile-free に保つ**(数字を入れない)
```

- **Why**: 数字ハードコードの発生源はこの指示。ここを断たないと①を直しても次の sync で再発する
  (debugging.md: 根本原因優先)。③でテーブルが自動生成になる事実も同時に反映。

## ③ Contents テーブルを Purpose 保持で script 自動生成

`claude-harness/scripts/sync-from-local.sh` の apply パス(L118 以降)に、既存 upstream-components
生成(L126-217)と同じ heredoc パターンで **Purpose 保持型テーブル生成**を追加。

**設計(既存 `origin_of()` を再利用):**

- `SELF = {shimo4228, auto-extracted, skill-create}` の自作 origin を持つ component を列挙:
  - skills: `SOURCE_DIR/skills/*/SKILL.md` → name = 親ディレクトリ名 → link `skills/<name>/SKILL.md`
  - agents: `SOURCE_DIR/agents/*.md` → name = stem → link `agents/<name>.md`
  - rules: `SOURCE_DIR/rules/*/*.md` → name = `common/<stem>` → link `rules/common/<stem>.md`
  (upstream-components は SELF を除外する。本ブロックは SELF **のみ**採る — 対称)
- **README.md と README.ja.md 両方**を処理。各ファイルで:
  - 既存テーブル行 `^\| \[(name)\]\(path\) \| (purpose) \|` を parse → name→Purpose の map を復元
    (**言語ごとに独立**して保持)。
  - 出力順は **既存 README の並び順を優先**(curated グルーピングを崩さない)、新規のみ末尾に追記、
    削除された component は自動で落とす。
  - 各行の Purpose: 既存 map にあればそのまま流用。**新規のみ** SKILL.md `description` frontmatter の
    先頭句を truncate して seed(人間が同 sync の `git diff` レビューで refine)。
  - 3 テーブルをそれぞれ専用マーカー間に出力:
    `<!-- BEGIN/END GENERATED: skills-table -->` / `agents-table` / `rules-table`。
  - マーカー不在なら WARN して skip(upstream-components と同じ防御)。
- **マーカーの一回だけ手動挿入**(en/ja 両方): 既存の各テーブル(ヘッダ行+区切り+データ行)を
  BEGIN/END で囲む。`### Skills` 見出しと直後の AKC 注記(L57 の blockquote)は**マーカー外**に残す。

- **Why generator(③a)を採る**: membership 検出は構造的(code)、Purpose 記述は意味的(human)という
  enumerate/decide split(when-code-when-llm)を尊重しつつ、既存キュレーションを壊さない。名前だけの
  upstream-components と違い Purpose 列があるため「既存流用 + 新規のみ seed」が必須。

## 任意クリーンアップ(同 diff で拾えるなら)

- **version DOI → concept DOI**: 両 README の L57 が AKC を version DOI `zenodo.org/records/19200727`
  でリンク。他行は concept `10.5281/zenodo.19200726` を使用しており不整合。hub CLAUDE.md「Concept DOIs
  only」に従い concept へ統一。**Why**: 既知の DOI drift(off-by-one)パターン。README を触るついでに是正。
- 「the first six / 最初の 6 つ」は AKC の 6-phase 構造に対応する stable な数なので**そのまま**
  (churning count ではない)。

## 影響ファイル

| ファイル | 変更 |
|---|---|
| (GitHub) `shimo4228/claude-harness` About | `gh repo edit --description`(①) |
| `~/.claude/skills/harness-sync/SKILL.md` | Step 4 の doc-sync 指示を修正(②、global 版のみ) |
| `claude-harness/scripts/sync-from-local.sh` | Purpose 保持テーブル生成ブロック追加(③) |
| `claude-harness/README.md` / `README.ja.md` | 3 テーブルに GENERATED マーカーを一回挿入(③) + 任意で L57 DOI 修正 |

## 実装チェーン(planning.md)

- 種別: `fix`(script の drift バグ修正) + `chore`(description) + skill/doc 編集。
- 実装後 Review(並列): **python-reviewer**(sync script の追加 Python ブロック) + **code-reviewer**
  (shell 文脈・マーカー regex の安全性)。secrets/認証は触らないので security-reviewer は `-`。
- 早期停止: いずれかが CRITICAL を返したら停止して報告。

## 検証(end-to-end)

1. **①**: `gh repo view shimo4228/claude-harness --json description` で新文言・数字ゼロを確認。
2. **③ 生成の正しさ**: en/ja にマーカー挿入後、`bash scripts/sync-from-local.sh`(apply)を実行。
   subtree が clean である前提(guard L31-38)なので、先に現状を commit するか stash。
3. `git -C claude-harness diff` を確認: 期待は「マーカー挿入 + テーブル再生成」のみで、
   **membership は 35/12/7 のまま・Purpose 文面が保持されている**こと(新規 component が無ければ
   Purpose の変化ゼロが理想)。想定外の行削除・Purpose 消失があれば生成ロジックの不具合。
4. `--dry-run` でも subtree 差分ゼロ(payload 不変)を確認。
5. **②**: `~/.claude/skills/harness-sync/SKILL.md` に数字維持の記述が残っていないか grep。
6. `git status` で意図しないファイル混入がないこと。
7. 全 PASS で claude-harness 側を commit(push はユーザー判断)。~/.claude 側の SKILL.md 変更は
   別コミット(別 repo)。
