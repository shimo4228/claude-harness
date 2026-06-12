---
name: release-doi
description: DOI-registered research repo (Zenodo) のリリース手順。CODEMAPS / README 多言語 / CHANGELOG / CITATION.cff / pyproject.toml / llms.txt / glossary を整合させてから tag push、Zenodo 自動採番後に新 DOI を反映する 5 phase + post-release ワークフロー。AKC / AAP / contemplative-agent など shimo4228 系の研究 repo で再利用する。
user-invocable: true
origin: shimo4228
---

# release-doi — DOI Release Runbook

Zenodo に DOI 登録された research repo のリリース手順。`/release-doi` で起動。
適用対象: AKC (`agent-knowledge-cycle`) / AAP (`agent-attribution-practice`) / contemplative-agent など、`CITATION.cff` を持ち GitHub release webhook で Zenodo が自動採番する shimo4228 系 repo。

## When to use

- 直近の refactor / 新機能 / sunset ADR を Zenodo に新 version DOI として記録したい
- pyproject.toml / CITATION.cff / 多言語 README の version drift を解消したい
- CODEMAPS / glossary / llms.txt が code 実態とズレているのを release ゲートで揃えたい

**Skip when**:
- DOI 登録のない repo (Zenodo 連携していない) — `CITATION.cff` の有無で判定
- バージョン bump の必要なし (typo fix 等の小修正で release を切らない)
- bug fix だけなら patch version で `/release-doi` を起動、major refactor なら minor / breaking なら major

## Pre-flight: 前提確認

```bash
# CITATION.cff があるか (= Zenodo 連携している repo か)
test -f CITATION.cff && echo "DOI repo" || echo "skip /release-doi"

# 直近 tag 以降の commit が空でないか (新規 repo なら tag なしで OK)
git log "$(git describe --tags --abbrev=0 2>/dev/null)..HEAD" --oneline | head

# Zenodo webhook が GitHub repo に登録されているか
gh api repos/<owner>/<repo>/hooks --jq '[.[] | select(.config.url | contains("zenodo"))] | length'
# → 0 が返ったら Zenodo opt-in 未実施。先に user に依頼する (下の "Zenodo opt-in" 参照)
# → 1 以上なら OK。webhook の active 状態も確認:
gh api repos/<owner>/<repo>/hooks --jq '.[] | select(.config.url | contains("zenodo")) | {active, url: .config.url[:50]}'
```

空なら release 不要。webhook 未登録なら opt-in 依頼後に再開。

### Zenodo opt-in (新規 DOI repo の最初の release で必須)

Zenodo は GitHub repo ごとに **opt-in 連携** が必要。toggle ON 前に作成された GitHub Release は Zenodo に届かず、後から ON にしても遡及的には拾われない (公式仕様)。新規 repo で初回 release を切る場合、必ず Phase 0 で opt-in を確認する。

ユーザー対応手順 (user が browser でやる):

1. `! open https://zenodo.org/account/settings/github/` — Zenodo の GitHub settings を開く
2. (必要なら) "Sync now" で repo 一覧を refresh
3. 対象 repo を find → toggle を **ON**
4. 完了確認

確認後、`gh api repos/<owner>/<repo>/hooks` で Zenodo webhook が登録されていることを再チェックしてから Phase 1 へ進む。

## Phase 1: Verification baseline (read-only)

判断材料を ground truth として固定。**実コマンド出力**だけを信頼する (既存 doc の数値は drift しているので使わない)。

```bash
# 対象 commit 範囲
LAST_TAG=$(git describe --tags --abbrev=0)
git log ${LAST_TAG}..HEAD --oneline
git diff ${LAST_TAG}..HEAD --stat | tail -3

# Python repo なら
find src -name '*.py' | wc -l                          # init 含む
find src -name '*.py' -not -name '__init__.py' | wc -l # init 除く
find src -name '*.py' | xargs wc -l | tail -1
find tests -name 'test_*.py' | wc -l
uv run pytest --collect-only -q 2>&1 | tail -3

# version triple
grep -nE "^version" pyproject.toml
grep -nE "^version:" CITATION.cff
git tag --sort=-creatordate | head -5
```

判定: 既存 doc に統計値の二重記述がある場合 (header と stats table で異なる数値等) は **両方とも実コマンド出力に揃える**。single-source-of-truth 原則。

## Phase 2: CODEMAPS regeneration (該当 repo のみ)

`docs/CODEMAPS/` がある repo (contemplative-agent 等) は `/update-codemaps` skill を起動して再生成。

**Drift 解消ルール**:
- header 部 / stats table / 各 module 行の数値を Phase 1 ground truth に揃える
- 削除済み module への言及を削除 (履歴注釈として残す場合は「retired by ADR-XXXX」形式)
- 新規 module を追加 (purpose 1 行 + ADR 出典)
- 30% 超の構造変化があれば user 承認待ち

CODEMAPS のない repo (AKC / AAP は ADR 中心) はこの phase をスキップ。

## Phase 3: Cross-doc consistency

`/context-sync` を入口で起動して役割重複・migrated content・freshness を一括検出してから、以下を順次更新:

| File | 更新内容 |
|---|---|
| `CHANGELOG.md` | `## vX.Y.Z — <title> (YYYY-MM-DD)` を Unreleased セクションから繰り出す。**3 カテゴリ最低限**: Sunset (削除/withdraw)、Added (新規 ADR / module / feature)、Changed (動作/設定の変化)。Notes に migration 影響を記述 |
| `pyproject.toml` | `version = "X.Y.Z"` |
| `CITATION.cff` | `version: "X.Y.Z"`、`date-released: "YYYY-MM-DD"`。**DOI 欄は前 release の値を据え置き** (Post-release で新 version DOI に差し替え) |
| `.zenodo.json` | **citation surface 同期**: 前回 release 以降に repo docs (policy-mapping / glossary / papers 等) が新たに引用した外部文献 (arXiv / DOI 付き論文) を `related_identifiers` に追加 — `{"identifier": "10.48550/arXiv.<id>", "relation": "references", "resource_type": "publication-article", "scheme": "doi"}` (arXiv は DataCite DOI 形式 `10.48550/arXiv.NNNN.NNNNN`)。既存 entry との重複を排除。description 内の framework 列挙等も実態に揃える |
| `README.md` + 多言語版 | BibTeX `version = {X.Y.Z}`、badge tests 数、prompts/module count、sunset 文 sentence-level の削除。glossary 規約準拠。**BibTeX `doi` / `url` および "How to cite" 引用文の DOI は Post-release で新 version DOI に差し替え。DOI badge は concept DOI で固定済みなので触らない** |
| `llms.txt` | header version、ADR 一覧の追加、prompts count |
| `llms-full.txt` | Project Facts (Version / Tests / ADRs)、Q&A の数値、新 ADR の Q&A 追加 |
| `docs/glossary.md` | 新出語 (ADR slogan / 唯名 / 新 module 名) を多言語で追加。sunset 用語 (BM25 のような) を削除 |
| `CLAUDE.md` | sunset 機能の言及を削除。新規 doc 場所/conventions を追加 |
| `docs/adr/` cross-ref | supersede / sunset / withdraw 関係の双方向リンク確認 (新→旧、旧→新) |

**多言語 README 同期範囲は default で「中間」**: version + 統計 + sunset sentence の削除。全文再翻訳は別 PR (cost が大きい)。最小 (badge のみ) は drift を残すので避ける。

**single-source-of-truth 原則**:
- 同じ統計値を 2 箇所以上に書かない。書くなら一箇所を canonical にして他は参照に
- 例: test 数は llms-full.txt に書き、README badge と llms.txt は llms-full.txt 経由で揃える

## Phase 4: Verify (read-only)

```bash
# CITATION.cff syntax
uv run python -c "import yaml; data = yaml.safe_load(open('CITATION.cff')); print('OK:', data.get('version'), data.get('date-released'), data.get('doi'))"

# version triple 整合
echo "=== pyproject.toml ==="; grep "^version" pyproject.toml
echo "=== CITATION.cff ==="; grep "^version:" CITATION.cff
echo "=== BibTeX in READMEs ==="; grep -h "version.*=.*{" README*.md | sort -u

# CHANGELOG 形式
grep -E "^## v[0-9]" CHANGELOG.md | head -5

# 多言語 README の version 一致
grep -h "X\.Y\.Z" README*.md | sort -u  # X.Y.Z は今回の version

# pytest (Python repo)
uv run pytest -q --no-header --tb=line 2>&1 | tail -5

# lint
uv run ruff check src/ tests/ 2>&1 | tail -5

# secret scan
grep -rE "(api[_-]?key|password|secret|token)\s*=\s*[\"'][A-Za-z0-9]{20,}" src/ --include='*.py' | head -5

# 削除済み module への参照残存 (sunset がある場合)
grep -rnE "<deleted_module_name>" src/ tests/ --include='*.py' | head -5

# git status — 意図しないファイルが含まれていないか
git status --short
```

全 PASS で次へ。FAIL があれば停止して user に報告 (memory: `verify-before-work`)。

## Phase 5: Release execution

`git push` および `gh release create` は **user 明示依頼があれば実行**。memory `push-workflow` の default は「user に提案して止まる」だが、user が「push して」「release を切って」と言ったら実行する。**Release object 作成 = Zenodo webhook trigger** なので irreversible (DOI 採番が動き始める)。

```bash
# specific files で stage (git add -A 禁止 — 意図しないファイル混入防止)
git add CHANGELOG.md CITATION.cff pyproject.toml \
  README.md README.<langs>.md \
  docs/CODEMAPS/*.md docs/glossary.md \
  llms.txt llms-full.txt

# HEREDOC で commit (attribution は global settings.json で disable 済み — 追記しない)
git commit -m "$(cat <<'EOF'
release: vX.Y.Z — <one-line title>

- ADR-XXXX <主要変更 1>
- ADR-YYYY <主要変更 2>
- ...
- CODEMAPS / README N lang / llms.txt(/full) / glossary / CHANGELOG synced

<diff stats>: N files changed, +M / -K since vA.B.C. P tests across Q files.
EOF
)"

git tag -a vX.Y.Z -m "vX.Y.Z — <one-line title>"

# user 明示依頼で push
git push origin main
git push origin vX.Y.Z

# GitHub Release object を明示作成 — tag push だけでは Zenodo は trigger されない。
# Release object が webhook の発火源で、これを作って初めて Zenodo が archive + DOI 採番。
# notes は CHANGELOG の該当 section を awk で抽出するのが確実 (該当 ## vX.Y.Z 行直下から
# 次の ## v 行の直前まで)。
gh release create vX.Y.Z \
  --title "vX.Y.Z — <one-line title>" \
  --notes-file <(awk '/^## vX\.Y\.Z/{flag=1; next} /^## v[0-9]/{flag=0} flag' CHANGELOG.md) \
  --repo <owner>/<repo> \
  --latest
```

**Branch 切らない・PR 作らない** (memory `push-workflow`: 個人研究 repo は main 直 push、`gh pr create` 自動実行禁止)。`gh release create` は別物 — Zenodo DOI 連鎖の起点なので、user 明示依頼下では実行する。

**HF dataset sync** (`graph.jsonld` を持つ repo のみ): `gh release create` の後、project root で `/hf-sync <Owner/dataset>` を起動して HF mirror を反映する。Local の `hf login` token を使うので CI / token secret 管理は不要。詳細は `hf-sync` skill 参照。

## Post-release: DOI 反映

Zenodo は **GitHub Release object** に対して webhook が発火する。tag push 単体では trigger されない — Phase 5 末尾の `gh release create` がないと Zenodo は何も知らない。Release object 作成 → GitHub webhook → Zenodo が repo snapshot を archive → 数分以内に新 version DOI を採番、の連鎖。

**よくある失敗 (2026-05-05 contemplative-agent v2.3.0 で実際に発生)**: tag を push して `git push origin vX.Y.Z` で完了したつもりになるが、Releases sidebar の "Latest" が前 version のまま、Zenodo にも何も届かない。`gh release create` を Phase 5 で実行し忘れたのが原因。tag は webhook を発火させない。

```bash
# 採番確認 (Zenodo の repo ページ or DOI badge URL を fetch)
# 新 DOI: 10.5281/zenodo.<new>

# 触る: version DOI を埋める citation 系のみ
#   - CITATION.cff (doi: / url:)
#   - README BibTeX (doi = {...} / url = {...}) — 全言語版
#   - README "How to cite" plain-text 引用
#   - llms-full.txt Citation 欄 (該当 fields があれば)
#
# 触らない: concept DOI で固定済みの display 系
#   - GitHub repo `homepage` field
#   - README DOI badge (badge SVG URL + click target、全言語版)
#
# (詳細は本 skill 末尾の "Concept DOI vs Version DOI 役割分離 policy" 表を参照)

git add CITATION.cff README.md README.<langs>.md
git commit -m "chore: update DOI to vX.Y.Z"
git push origin main
```

**Wikidata 連邦** (optional、新規 repo の初回 release 時): `wikidata-federation` skill で Wikidata item（P356=concept DOI, P50=著者 QID）を作成し、graph.jsonld に QID を sameAs 編入する。2回目以降の release では既存 item が concept DOI で解決し続けるため作業不要。

**HF dataset 反映** (`graph.jsonld` を持つ repo のみ): project root で `hf-sync` skill を起動して mirror を更新する。

```bash
# Project root の cwd で実行 (graph.jsonld が存在することが前提)
/hf-sync <Owner/dataset>
# または同等:
bash ~/.claude/skills/hf-sync/sync.sh <Owner/dataset>

# 反映確認
# https://huggingface.co/datasets/<Owner/dataset>/commits/main を開いて
# 最新 commit が直前 release より新しいことを目視
```

失敗時 (`hf upload` の 401 / 403、HF dataset 404 等) は `hf-sync` skill の "Failure modes" section に従う。

**Concept DOI vs Version DOI — 役割分離 policy**:

display 用 link は **concept DOI**、citation は **version DOI**、と用途で分ける。混同すると「badge / homepage が古い版を指したまま」または「citation がどの版か不明」のいずれかが発生する。shimo4228 系 (AAP / AKC / contemplative-agent) は 2026-05 にこの policy に統一済み。

| 用途 | 場所 | DOI 種別 | 更新頻度 |
|---|---|---|---|
| **Display** (常に latest を見せる) | GitHub repo `homepage` field | concept | 一度設定したら不要 |
| **Display** | README DOI badge (badge SVG URL + click target、全言語版) | concept | 一度設定したら不要 |
| **Citation** (どの版か特定) | `CITATION.cff` の `doi:` / `url:` | version | release ごと |
| **Citation** | README BibTeX `doi = {...}` / `url = {...}` | version | release ごと |
| **Citation** | README "How to cite" plain-text 引用 | version | release ごと |
| **Citation** (該当 fields があれば) | `llms-full.txt` Citation 欄 | version | release ごと |

理由: badge / homepage は「この repo は Zenodo 登録物です、最新版へどうぞ」という *表示* のリンク → 常に latest 解決される concept DOI が適切。CITATION.cff / BibTeX は *citation* なので「どの版を読んだか」を保存する必要があり version DOI 固定。

**Concept DOI lookup** (version DOI から導出):

```bash
# 任意の version DOI ID から concept DOI を取得
curl -s https://zenodo.org/api/records/<any_version_id> \
  | python3 -c 'import sys, json; d=json.load(sys.stdin); print("concept:", d.get("conceptdoi"), "  version:", d.get("doi"))'
```

慣例的に concept DOI = (最初の version DOI - 1) になることが多いが、必ず API で確認する (新規 record 形式では別の番号体系になりうる)。

**One-time setup (新規 repo の最初の release 後)**:

1. GitHub Release 作成 → Zenodo webhook で最初の version DOI 採番
2. 上記 API で concept DOI を取得
3. `gh repo edit <owner>/<repo> --homepage "https://doi.org/<concept_doi>"`
4. README DOI badge を concept DOI に設定 — badge SVG URL と click target の両方
5. 全言語 README の DOI badge も同じ concept DOI に揃える

以降、release のたびに badge / homepage は **触らない**。Citation 系のみ Post-release で version DOI に差し替える。

**移行 (既存 repo で badge が version DOI のまま残っている場合)**: 新規 release 時に concept DOI へ差し替える。過去 commit log や tag history に version DOI 形式の badge が残っていても問題ない (HTML/SVG snapshot として保存されるため citation は破壊されない)。

## Early stop conditions

- **Pre-flight で Zenodo webhook 未登録** → user に opt-in 依頼で停止 (上の "Zenodo opt-in" 参照)。新規 DOI repo の最初の release で頻発する漏れ
- Phase 1 で `LAST_TAG..HEAD` の commit が空 → release 不要、user に報告
- Phase 2 で CODEMAPS の構造変化が >50% → user 承認待ち (大規模架構変更の可能性)
- Phase 4 で test FAIL / secret detection HIT / lint error → 停止して報告
- Phase 5 で `git status` に意図しない modified file → user 承認待ち
- Phase 5 で `gh release create` を忘れて tag だけ push してしまった → 後追いで `gh release create vX.Y.Z --notes-file ... --latest` を実行 (tag が既にあれば release object のみ追加される)
- **Post-release で webhook delivery が 4xx** (`gh api repos/<owner>/<repo>/hooks/<hook_id>/deliveries` で `status_code: 403` 等) → opt-in 漏れの可能性が高い。webhook event 自体は届いているが Zenodo が受理していない。下の "復旧手順" 参照
- Post-release で `gh release create` 実行後 30 分以内に Zenodo が DOI 採番しない → Zenodo dashboard の webhook delivery ログを user に確認依頼 (GitHub-Zenodo 連携が外れている / 認証切れの可能性)

### 復旧手順: opt-in 漏れで初回 release が Zenodo に届かなかった場合

GitHub commit はそのまま残し、tag + Release object のみ作り直す:

```bash
# 1. Release object 削除
gh release delete vX.Y.Z --yes --repo <owner>/<repo>

# 2. remote tag 削除
git push origin --delete vX.Y.Z

# 3. local tag 削除
git tag --delete vX.Y.Z

# 4. user に Zenodo opt-in を依頼 (上の "Zenodo opt-in" 参照)
#    完了後、webhook 登録を再確認:
gh api repos/<owner>/<repo>/hooks --jq '.[] | select(.config.url | contains("zenodo")) | {active}'
# → {"active": true} が返ることを確認

# 5. tag + Release object を再作成
git tag -a vX.Y.Z -m "..."
git push origin vX.Y.Z
gh release create vX.Y.Z --title "..." --notes-file <(awk ... CHANGELOG.md) --latest --repo <owner>/<repo>

# 6. webhook delivery の status_code を確認 (今度は 202 OK が出るはず)
HOOK_ID=$(gh api repos/<owner>/<repo>/hooks --jq '.[0].id')
gh api "repos/<owner>/<repo>/hooks/$HOOK_ID/deliveries" --jq '.[0:3] | .[] | {event, action, status_code}'
```

GitHub commit は不変 (release commit + DOI 反映 commit は残る)。tag/release のみ作り直すので blast radius は小さい。

## Notes — 設計判断の根拠

- **Ground truth は実コマンド出力だけ**: 既存 doc の数値は drift しているので、INDEX.md の「43 modules」を読まずに `find src -name '*.py' | wc -l` を信頼する
- **`.zenodo.json` references = 被引用研究者への passive シグナル**: repo markdown 内の引用は Google Scholar / arXiv "cited by" の citation graph に一切入らない (被引用側から不可視)。`.zenodo.json` の `references` 辺は release 時に DataCite metadata として propagate し、OpenAIRE / Scholix の citation graph に機械可読な辺を張る。引用した文献の著者周辺に届く数少ない受動経路なので、新規引用が増えた release では必ず同期する (authorship-strategy の citation-graph federation tactic)。収集コマンド例: `grep -rhoE "arXiv:?[0-9]{4}\.[0-9]{4,5}" docs/ *.txt | sort -u` を既存 `related_identifiers` と突き合わせる
- **多言語 README は default 中間**: 全文再翻訳は cost 過大、最小 (badge のみ) は drift を残す。version + 統計 + sunset sentence までが妥当
- **DOI 欄は Phase 5 で据え置き**: tag push 前に新 DOI を埋めると Zenodo 採番前なので必ず壊れる。Post-release で 1 commit 増やす方が安全
- **Branch 切らない**: memory `push-workflow` — 個人研究 repo の default は main 直 push。`gh pr create` を自動実行しない
- **Numeric cap を quality filter にしない**: memory `no-numeric-caps` — `max_rules=N` 型の機械的 cap を CHANGELOG / release notes に持ち込まない
- **Single responsibility per artifact**: 1 ファイル = 1 責務。新 concern を既存ファイルに sub-structure で押し込む前に、他層に家があるか問う (memory `single-responsibility-per-artifact`)
- **Substrate migration sweep**: schema/storage/primary index を変えた release では、全 command pipeline を grep で棚卸し (memory `substrate-migration-sweep`)
- **新規 DOI repo は Zenodo opt-in が事前必須**: Zenodo の GitHub 連携は repo ごとの opt-in 設計。toggle ON 前に作成された release は遡及的に拾われない (公式仕様)。Pre-flight で `gh api repos/<owner>/<repo>/hooks` を確認しないと、Phase 5 まで進めて Zenodo に何も届いていないことを Post-release で初めて発見してリカバリーすることになる。**新規 repo のたびに必要だが忘れがち** — sibling repo (AKC / AAP / contemplative-agent / authorship-strategy) では既に opt-in 済みのため、慣れていると新規 repo で初回 release を切る時の盲点になる。doctrine-corpus v0.1.0 (2026-05-22) でこの漏れが発生し、tag/release 再作成でリカバリーした事例あり

## Worked example (abstracted)

contemplative-agent v2.3.0 (2026-05-05) で実行した内容の構造:

- **Phase 1 baseline**: 16 commits since v2.2.1, 110 files changed, +2170/-5772, 49 modules / 11390 LOC / 29 test files / 1032 tests
- **Phase 2 CODEMAPS**: 6 ファイル更新 — INDEX.md の statistics drift (51→49 modules, 13400→11400 LOC, 35→29 test files) 解消、新規 helper module 3 件追加、削除済み module への言及削除
- **Phase 3 cross-doc**: 18 ファイル更新 — CHANGELOG v2.3.0 セクション追加、6 言語 README BibTeX bump、llms.txt の ADR list 拡充、glossary から retired 用語削除
- **Phase 4 verify**: pytest 1032/1032 PASS, ruff PASS, secret scan clean, version triple 一致
- **Phase 5 release**: 1 commit + 1 tag + main/tag 両 push + `gh release create v2.3.0 --notes-file <(awk ... CHANGELOG.md) --latest` で Release object 作成 (Zenodo webhook の trigger)
- **Post-release**: Release object 作成で Zenodo webhook が発火 → 数分後 DOI 採番 → CITATION.cff の DOI 差し替え 1 commit

具体 commit / file path は repo ごとに変わる。本 skill 本文は構造のみを保持し、実数値・パスは実行時に Phase 1 baseline で取得する。
