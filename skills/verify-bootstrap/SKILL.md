---
name: verify-bootstrap
description: "repo に機械ゲート（format / lint / type check / security / dependency audit / test）を立てる、または既存のゲートが古びていないか棚卸しする。Use when starting a new project, when a repo has no automated quality gate, when the user says 「lint を入れて」「この repo にゲートを立てて」「型チェックを入れたい」「静的解析を整備して」「ツールが古い」「verify を棚卸しして」, \"set up linting\", \"add a quality gate\", \"bootstrap the toolchain\", or invokes /verify-bootstrap. 使うツールは skill が知っているのではなく、その時点で search-first に調べさせる — repo のスタックが何であれ同じ手順で回る。NOT for — 既に立っているゲートを 1 回実行するだけ（それは repo の verify entrypoint を直接実行）、ハーネス自身の設定監査（→ config-gc）、コードの意味的レビュー（→ implementation-chain の Review 群）。"
compatibility: Developed and tested on Claude Code; portable to other Agent Skills-compatible agents.
license: MIT
metadata:
  author: shimo4228
  version: "1.0"
user-invocable: true
origin: shimo4228
---

# verify-bootstrap — repo に機械ゲートを立てる

人間がコードを読む速度は、AI が書く速度に追いつかない。だから構造的な正しさの判定は
**機械に移す**。この skill は repo ごとに、
その時点で最良の検査ツールを立てる。

## この skill が持たないもの（設計上の中核）

**ツール名の一覧を持たない。言語の検出テーブルも持たない。** ツールは陳腐化する
（flake8 + black + isort → ruff は 2 年で起きた）。固定表を持てば表が腐り、
腐った表が repo に配られる。

持つのは **調べ方と契約**だけ:

- repo の実態を列挙する手順（静的な言語リストを参照しない）
- category ごとに何を search-first に問うか
- 生成物 `.claude/verify.sh` の契約（global hook がこれだけを知る）
- strictness と陳腐化検知の規律

結果として、この skill が書かれた時点で存在しなかった言語・ツールでも同じ手順で回る。

## モード

| モード | 起動条件 | やること |
|---|---|---|
| **bootstrap** | `.claude/verify.sh` が無い | Step 1–6 を通す |
| **audit** | 既にある（`--audit` / 「棚卸し」） | Step 1 を再実行し、`.claude/verify.md` の選定を search-first で引き直して差分を提案 |

## Step 1 — repo の実態を列挙する（検出、静的表なし）

推測しない。**実測する**。

```bash
# 追跡ファイルの拡張子分布（上位）— 生成物・依存ディレクトリは除く
git ls-files | sed -n 's/.*\.\([A-Za-z0-9_]*\)$/\1/p' | sort | uniq -c | sort -rn | head -20
# ビルド/依存マニフェストの実在
git ls-files | grep -iE '(^|/)(pyproject\.toml|package\.json|Cargo\.toml|go\.mod|Gemfile|pom\.xml|build\.gradle.*|\*\.xcodeproj|Package\.swift|mix\.exs|composer\.json|Makefile|justfile)$' 
# 既存のゲート痕跡（重複導入の防止）
git ls-files | grep -iE '(pre-commit-config|lefthook|\.github/workflows/|trunk\.yaml|\.golangci|\.eslintrc|ruff\.toml)'
```

上のマニフェスト grep は**発見の補助であって権威ではない**。1 本目の拡張子分布が正本で、
grep に載っていない生態系が出てきたらそれを Step 2 にそのまま渡す（表を編集して
この skill に足さない — 表を持たないことがこの skill の設計）。

散文・設定・スキーマも対象に含める。コードだけがゲートの対象ではない
（Markdown の日本語 prose、YAML、CI 定義、シェルスクリプトはいずれも機械検査できる）。

## Step 2 — category ごとに現時点の最適ツールを調べる

検出した生態系ごとに、**6 category** を埋める。埋まらない category は「無い」と明記する
（空欄と「その言語には該当がない」は別物）。

| category | 問い |
|---|---|
| **format** | 整形の正規化。差分ノイズを消し、レビュー対象を意味の変化だけにする |
| **lint** | 構造的な誤り・複雑度・デッドコード |
| **type check** | 型で表現できる契約。型なし言語なら「型注釈を段階導入する手段があるか」 |
| **security** | 危険な構文・秘密の混入（秘密スキャンは harness 側にもあるので重複を確認） |
| **dependency** | 既知脆弱性・未使用依存・ライセンス |
| **test** | テストランナーとカバレッジ測定 |

各 category について **`search-first` skill を呼ぶ**（WebSearch を直接叩かない —
依存追加・自作 utility の前は search-first、が `rules/common/planning.md` の配線）。問いには必ず
「**2026 年時点で**」に相当する時点指定と「既存の代替から乗り換えが起きていないか」を含める。
記憶している定番を答えにしない — この skill が防ごうとしているのはまさにそれ。

Verdict が出たら、次を確認してから採用する:

- **最終リリースが 12 ヶ月以内か**（放置プロジェクトを新規 repo に入れない）
- **単一バイナリ / on-demand 実行が可能か**（`uvx` / `npx` / `brew` 等。repo の
  実行環境を汚さずに走るか）
- **設定を持ち込めるか**（strictness を宣言でき、例外を許可リスト化できるか）
- **CI とローカルで同じものが走るか**（乖離するとローカルが形骸化する）

## Step 3 — 最大 strict で導入する

**既定は最大 strict**。AI は厳しさに文句を言わないので、従来「人間の忍耐」を理由に
緩められていた分の天秤は正しさ側に倒す。

- 警告を warning のまま放置しない — **error にする**
- 型の抜け穴（`any` 相当・型チェック抑制コメント）を **禁止側に倒す**
- 版を **pin する**（`ruff==0.16.0` のように。supply chain の固定。bump は手動）
- 例外は**インラインの抑制コメントでなく、設定ファイルの許可リストで理由付き**に
  （インライン抑制は理由が消えて無限増殖する）

**新規 repo は初日から最大 strict**（drain すべき負債がゼロなので ratchet 不要）。
**既存 repo への後付けだけ ratchet を使う** — 全 rule を warn で入れ、既存違反を
drain し切ってから error に上げる。初日から block にすると「回避の作法」が育つ。

## Step 4 — `.claude/verify.sh` を生成する（global hook との契約）

repo が持つ **唯一の入口**。ハーネス側の hook はこのファイルの存在と exit code しか
見ない — だから repo が何語で書かれていても hook を変更せずに済む。

**契約（厳守）**:

| 項目 | 仕様 |
|---|---|
| パス | `<repo root>/.claude/verify.sh`（実行可能） |
| 引数 | `--staged` = commit 境界の高速検査（staged ファイルのみ）。引数なし = repo 全体の完全検査 |
| 環境 | `$VERIFY_REPO_ROOT` があれば repo root として使う（承認機構が渡す） |
| exit code | `0` = PASS / `1` = FAIL（commit を止める）/ `2` = 検査不能（ツール不在等、fail-soft） |
| 出力 | FAIL 時は**人間と LLM が読んで直せる検出行**。PASS 時の出力は **advisory**（commit は止めないが伝えたいこと — 昇格待ちの ratchet、眠っているゲートの通知）として `verify-precommit.sh` が model へ渡す。言うことが無ければ**無出力**（無言 PASS にノイズを足さない）。**stdout と stderr は区別されない** — hook は `2>&1` でまとめて受けるので、成功時に stderr へ出る進捗・非推奨警告も advisory になる。黙っていたいものは黙らせる |
| 実行時間 | `--staged` は**数秒以内**。超えるものは無引数側にだけ置く |

**速い / 遅いの分離**（これを守らないと bypass の作法が育つ）:

- `--staged`: format check・lint・security scan（ファイル単位で完結するもの）
- 無引数: build・type check・test・dependency audit（repo 全体・分単位）

ツール解決は `PATH にあれば使う → 無ければ on-demand 実行（uvx / npx 等）→ それも
無ければ exit 2 で fail-soft`。**fail-soft でも無音にしない** — どのゲートが眠って
いるかを stdout に出す（眠っているゲートは、無いゲートより危険）。

**実装上の罠（どちらも実測で踏んだもの）**:

- **repo root は `$VERIFY_REPO_ROOT` → 自分自身の位置、の順で決める** — cwd 起点にすると
  hook 経由で**別 repo を検査して無言で PASS する fail-open** になる。承認機構は照合済み
  バイト列を一時ファイルに置いて実行する（TOCTOU 回避）ので `BASH_SOURCE` が repo を
  指さない場合がある。両対応が必須:

  ```bash
  if [[ -n "${VERIFY_REPO_ROOT:-}" ]]; then
    ROOT="$VERIFY_REPO_ROOT"
  else
    ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P) || exit 2
  fi
  ```
- **追跡されているか確認する** — `.gitignore` が `.claude/*` を除外している repo は多い。
  除外されたままだと CI と他クローンからゲートが消える。`git check-ignore` で確認し、
  必要なら `!.claude/verify.sh` / `!.claude/verify.md` を足す

**生成しただけでは commit 境界で走らない** — hook は permission プロンプトを経ずに実行するため、
「ファイルがある」を「実行してよい」と読み替えない設計になっている（clone しただけの外部 repo で
コードが自動実行される経路を塞ぐ）。**人間が内容を読んで承認**して初めて実行される:

```
python3 ~/.claude/scripts/hooks/verify_allow.py approve <repo>
```

承認は内容ハッシュに紐づくので、`verify.sh` を編集したら `verify_allow.py` の台帳を更新する前に
新しい本文を確認する。これは permission prompt を経ない repo-local code 実行の信頼境界である。

生成した `verify.sh` は**その場で 1 回実行して動作を確認する**。さらに
**違反を一時注入して category ごとに発火を実証する**（format 崩し・未使用 import・
`eval` 等）。PASS するだけの確認は、ゲートが眠っていても PASS するので証拠にならない。
実証が済んだら注入した probe を必ず削除する。

## Step 5 — 選定を記録する（陳腐化を可視化する）

`<repo root>/.claude/verify.md` に、category ごとに次を残す:

```
## type check
tool: pyright ==1.1.x
選定日: 2026-07-31
理由: mypy より速く既定が strict。ty / pyrefly は 2026-07 時点で pre-1.0
再調査トリガー: 12 ヶ月経過 / 代替が 1.0 到達 / 現行ツールの最終リリースが 12 ヶ月以上前
```

この記録が無いと audit モードが「何を引き直すべきか」を判断できない。
**選定日と再調査トリガーは必須**、理由は 1 行でよい。

## Step 6 — CI に同じものを配線する（任意だが推奨）

ローカルゲートだけでは、bypass された commit が素通りする。CI が `.claude/verify.sh`
を無引数で実行する job を持てば、ローカルと CI の乖離が構造的に起きない
（**同じ入口を両方から呼ぶ**。CI 用に別のコマンド列を書くと必ず drift する）。

## audit モード

1. Step 1 を再実行（stack が変わっていないか — 言語が増えていれば category が空く）
2. `.claude/verify.md` の各 category について、**再調査トリガーに該当するものだけ**
   search-first で引き直す（全件引き直すと毎回コストが出る）
3. 差分を提示: 現行 → 候補、乗り換えコスト、据え置きの理由
4. 判断はユーザー。**自動で乗り換えない** — ツール変更は repo 全体の diff を生み、
   元に戻すコストが導入コストを上回る

## アンチパターン

- **固定のツール表をこの skill に足す** — 表が腐り、腐った表が全 repo に配られる。
  Step 1–2 を回すコストを惜しんで表を作った時点でこの skill は死ぬ
- **インラインの抑制コメントを許す** — 理由が消え、例外が無限に増える
- **警告を warning のまま運用する** — 誰も見ない。error にするか、消すか
- **repo 固有の特殊ルールを積む** — 「この repo だけ独自」は設計不足のサイン。
  まずスタックを標準に寄せ、それでも要る例外だけ理由付きで許可リストへ
- **遅い検査を `--staged` に入れる** — commit のたびに数十秒待たされ、bypass が常態化
- **生成して実行せずに終える** — 動作未確認のゲートは、無いゲートより悪い（あると誤認する）

## 関連

- Phase 0 のエントリポイント: skill `search-first`（ツール選定は必ずここを通す）
- ゲートを含む実装フロー全体: skill `implementation-chain`
