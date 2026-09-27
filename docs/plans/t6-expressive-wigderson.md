# T-006: セキュリティ層再編 — security-scan 退役 + claude-security 実スキャン + ADR-0019

## Context

台帳 T-006（T-005 Phase B）。公式 `claude-security` プラグイン (v0.10.0、2026-07-25 導入済み) の登場を機に、
`security-scan` skill（origin: ECC / `npx ecc-agentshield` の薄いラッパー / **5 ヶ月間 invoke 0 件**
— metrics/skill-usage.jsonl は棚卸し read 8 件のみ）を退役させる。

**調査で確定した分岐**: プラグインソースの直接読解により、claude-security は
**リポジトリコードの脆弱性スキャナ専用**で、`.claude/` 設定は「trust model の前提」として
明示的に検査対象外（plugin README.md:9 / SECURITY.md / SKILL.md:57、finding カテゴリに
misconfiguration 系スラッグ皆無）。agentshield が見ていたエージェント設定監査面
（settings.json permissions / mcp.json / hooks injection / agents tool access）とは**ほぼ直交**。
→ 台帳が予告した「見ないなら空席化 + hook 化を別途起票」ルートに確定。

退役は ADR-0011 の明示 Keep 判定（:54）の override になるため ADR-0019 が必要。
ユーザー確認済み: (1) 着手条件どおり実スキャンを先に実行、(2) 後続タスクは hook 化 +
security-guidance プラグイン評価を併記。

## Phase 1: /claude-security 実スキャン（着手条件の充足）

- `claude-security:claude-security` orchestrator agent を起動し、**scan のみ**（patch 生成なし）を依頼:
  scanRoot `~/.claude`、effort **medium**。
- 観察ポイント（ADR-0019 の実証データになる）:
  1. Inventory の coverage accounting が `settings.json` / `mcp.json`（存在すれば）/ `agents/*.md` /
     `hooks/` を「scanned component」として扱うか、background/untrusted-data 扱いか
  2. `hooks/*.sh` / `scripts/hooks/*.sh` / Python scripts への実コード finding（これ自体が
     プラグイン初回実用の副産物）
- 成果物 `CLAUDE-SECURITY-<ts>/` は repo 外扱い（自前 .gitignore 持ち）。RESULTS.md を読み、
  CRITICAL があれば rules/common/security.md の Security Response Protocol に従い**先に対処**（早期停止条件）。
- 観察結果が「設定も監査する」だった場合（ソース読解と矛盾）: 停止してユーザーに報告し、
  空席化ルートを再検討する。

## Phase 2: ADR-0019 起票（/adr-writer skill 経由）

`docs/adr/0019-*.md`（次番号 0019 確認済み・欠番なし）+ README.md index に 1 行追加。

決定パケットの要点:
- **Decision**: `security-scan` を完全削除（ADR-0011 の Keep を override）。
  根拠: invoke 0 件×5 ヶ月 / flag ドキュメントが ecc-agentshield 1.4.0 の stale subset /
  第三者 npm への supply chain 依存 / origin ECC（ADR-0008 でローカル一本化済み）
- **claude-security との直交性**を明記: コードスキャン面は plugin が上位互換で代替、
  設定監査面は**代替されず空席化** → T-008 起票で対処
- **skill-health risk 次元は空席化**（repoint 先なし。"latest grade if present" は実装上
  常に不在だった — grade 格納パスの定義自体がなかった事実も記録）
- Phase 1 のスキャン観察結果を実証データとして記載
- **Alternatives**: Keep 継続（ADR-0011）/ risk 次元を claude-security に repoint（不採用:
  設定を見ない）/ `_archived/` 移動（不採用: ADR-0011:67-69 の既決）
- **Revert 節**: `git checkout <直前 commit> -- skills/security-scan/` を記載

## Phase 3: 退役 + 参照 repoint（1 コミット、65081f1 パターン踏襲）

### 削除
- `git rm -r skills/security-scan/`（単一 SKILL.md のみ、外部スクリプトなし）

### 生きた参照の編集 — 5 ファイル 10 箇所 + skill-health パッケージ文字列 3 箇所

| ファイル | 箇所 | 処置 |
|---|---|---|
| `rules/common/security.md` | 「See skill: security-scan / See learned note: …」の行（※本日 bandit hook 追記で行番号シフト済み — 内容で特定） | `See skill: security-scan /` を削除し learned note ポインタのみ残す |
| `skills/agent-architecture-audit/SKILL.md` | :31 スコープ外委譲 | 「Security scanning — repo コードは `/claude-security` plugin」へ repoint |
| 同 | :252 Related | claude-security plugin の説明に差し替え |
| `skills/config-gc/SKILL.md` | :118 Related | エントリ削除（設定監査面は空席 — 必要なら T-008 参照を 1 行） |
| `skills/skill-health/SKILL.md` | :3 description 末尾 | `NOT for security scanning (that is the claude-security plugin)` へ |
| 同 | :79 Boundary 表 Risk 行 | owner を `(vacant — see ledger T-008)` に、動作を `report unmeasured` に |
| 同 | :84 箇条書き | security-scan = risk の行を削除、空席の 1 行に置換 |
| 同 | :137-138 Phase 3 Risk | 「owner 不在。常に `unmeasured` を報告し T-008 を指す」へ書き換え |
| 同 | :164 Related | 削除（または T-008 ポインタ） |
| `skills/skill-health/scripts/scan_refs.py` | :14 docstring / :119 文字列 | `security-scan` を委譲先列挙から除去 |
| `skills/skill-health/pyproject.toml` | :4 description | 同上 |

### 触らないもの
- `skills/skill-stocktake/results.json` / `rules-distill/results.json` — 次回実行で再生成
  （ADR-0011 Negative 節の既決。手動 prune しない）
- `settings.json` — security-scan / agentshield 関連エントリはもともとゼロ（`Bash(security:*)` は
  macOS キーチェーンコマンドで無関係）
- 公開 repo — origin ECC は harness-sync 対象外のため公開側に実体なし

## Phase 4: 台帳更新（同一コミット）

- `.notes/TASKS.md`: T-006 → Done 節へ（実施内容 + ADR-0019 リンク + スキャン結果要約）
- **T-008 新規起票**（Pending）: エージェント設定監査面の決定論ゲート化。
  スコープ: settings.json permission 監査 / mcp.json MCP リスク / hooks command injection /
  agents tool access。方式候補として **(a) hook 化（hooks.md「セキュリティチェック → hooks」準拠）
  (b) 公式 `security-guidance` プラグイン（marketplace に未有効化で存在）の評価** を併記。
  方式決定は着手時。

## Phase 5: Verify + commit

1. `grep -rn "security-scan" --include="*.md" --include="*.py" --include="*.toml"` —
   残存ヒットが ADR / TASKS.md Done 行 / results.json（再生成待ち容認）のみであること
2. skill-health の scan_refs.py が壊れていないこと（`python scripts/scan_refs.py` 実行 or 構文確認）
3. skill-health SKILL.md の YAML frontmatter 検証（description 編集後）
4. secret scan — PreToolUse hook が自動実行
5. `git status` — 意図外ファイルなし（CLAUDE-SECURITY-* が untracked に出ないこと確認）
6. コミット: `refactor(skills): security-scan を退役 — claude-security plugin 導入に伴う再編 (ADR-0019)`
   本文に復元コマンド `git checkout <hash> -- skills/security-scan/` を記載。
   ユーザーの Verify 結果確認 gate（2 介入点モデルの第 2 点）を経てからコミット。
