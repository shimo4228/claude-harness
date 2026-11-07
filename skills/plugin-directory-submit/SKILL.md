---
name: plugin-directory-submit
description: "Anthropic の plugin directory に plugin を提出し、掲載後の listing を保つ手順。"
user-invocable: true
disable-model-invocation: true
origin: shimo4228
---

# Plugin Directory Submit

著者の GitHub repo にある Claude Code plugin を、Anthropic の plugin directory
（claude.ai/directory）に載せる。repo 側の準備と検査は Claude が仕上げ、developer portal
（claude.ai/directory/manage）での操作は著者が行い、結果を Claude が読み戻して直す。

仕様の正本は公式 doc（下の表）。portal の画面と審査の挙動は変わるので、提出のたびに
pre-submission checklist を読み直し、本文と違えば doc に従って本文を直す。

| doc | 読むこと |
|---|---|
| https://claude.com/docs/plugins/pre-submission-checklist | Validate と scan が見る項目と、各結果（Blocks / Policy hold / Warning / Note） |
| https://claude.com/docs/plugins/submit | portal の各 step、提出後の流れ、更新・追跡 branch・取り下げ |
| https://claude.com/docs/connectors/building/after-publishing | 掲載後に何が live の版に追従するか、Usage タブ |
| https://code.claude.com/docs/en/plugins/manifest-reference | `plugin.json` の各欄（directory listing fields 節） |

## 1. 提出時に一度だけ読まれる欄を先にそろえる

directory は次の欄を**最初の提出のときだけ**読む（as-of 2026-10-13、manifest reference の
Directory listing fields 節）。portal の Listing タブにも "Newer versions don't update them here"
とあり、掲載後に `plugin.json` を直しても届かない。portal の **編集** からも直せない（著者が
akc-cycle の画面で確認、2026-10-13）。直す経路は Anthropic に頼むことだけなので、提出の前に
そろえる。

- `icon`（§3）
- `documentationUrl` / `supportUrl`（`https://` の URL。repo の README と issues で足りる）
- `privacyPolicyUrl` / `termsOfServiceUrl`（データを集めない plugin では置かない）
- `author`（`name` と `url`）、`keywords` — akc-cycle はこれらを置かずに提出し、portal の
  Listing タブでアイコン・作成者・keywords が空のまま残った（2026-10-12 観察）

掲載後も live の版に追従するのは、`plugin.json` の `name`・`description`（短い説明）と
README（長い説明）だけ。review 中に reviewer がどちらかを書き換えたら、その文が残る。

## 2. manifest と README

**`plugin.json`**

- `name`: 小文字・数字・ハイフン、64 字以内。永続の識別子で、掲載後は変えない。表示名を
  変えたいときは `displayName` を使う。`claude-` で始まる名前や、一般語だけの名前
  （`test-plugin` の類）は Blocks か Policy hold になる
- `description`: directory の短い説明になる。1 行で「何をするか」と「入れた人が最初にすること」
  を書く。skill を持つ plugin は `/<plugin>:<skill>` を名指す（自然文の頼み方では skill が
  発火しなかった、akc-cycle で観察）。hook だけの plugin は「何も打たなくてよい。いつ何が
  入るか」を書く
- `version`: release のたびに上げる。入れた人の側はこの値で更新を知る
- `license`、`author`、`keywords`、§1 の欄

**README**（plugin フォルダの中。directory はこれを長い説明として出す）

- コードブロックの外で 40 語以上。中身の書き方は skill: `readme-writer` が持つ
- plugin が実行するもの・送るもの・取得するものを全部書く。security scan は README と
  コードの食い違いを「開示されていない挙動」として落とす
- hook を持つなら、各 hook が何を変えるかと、読むデータを書く（harness-scope の Validate が
  Note で求めた）
- Anthropic との提携・推奨を思わせる語（official、endorsed）は使わない。掲載後に限り
  "listed in the Claude plugin directory" と書いてよい（Software Directory Policy）

## 3. アイコン

1. plugin の `/codex:rescue` で Codex に画像生成を頼み、3〜4 案を出す。条件: 正方形、文字と数字を入れない、
   一つの太い形、余白を広く、32px に縮めても形が読める
2. 著者が 1 案を選ぶ。絵柄は著者が決める
3. 選んだ画像を正方形の PNG に整える: `sips -z 1024 1024 <in> --out <plugin>/.claude-plugin/icon.png`
   （元が正方形でなければ先に中央で切り抜く）。条件は一辺 512〜2048px・2 MB 未満
   （harness-scope 提出時の portal の表示、2026-10-03）。checklist が通す画像は PNG・JPEG・GIF・
   WebP・SVG で、1 ファイル 5 MiB 未満（as-of 2026-11-02）。両方を満たす PNG を作る。1024px の透過 PNG は通った
   （harness-stocktake、2026-11-02）
4. `sips -z 32 32` で縮めた写しを Read で開き、形が読めるか確かめる
5. `plugin.json` に `"icon": "./.claude-plugin/icon.png"` を書く。directory は既定の置き場を
   拾わず、この欄だけを読む。JPEG を SVG で包んだ形は「No icon」と判定された（akc-cycle）
6. アイコンは README の Markdown 画像構文からだけ参照する。hook・script・コードブロックの
   中でパスを書くと Policy hold になる

## 4. plugin フォルダの自己検査

plugin フォルダ（`.claude-plugin/plugin.json` を持つフォルダ）は、入れた人に配られる中身
そのもの。配らないもの（テスト、開発用ツール、probe、docs）は外に置く。repo の root を
plugin にするか、配るものだけを `plugin/` などの subfolder に置く（harness-scope は
`plugin/` に移した）。

`claude plugin validate --strict ./<plugin>` を通したうえで、portal で落ちた実例を先に潰す:

| 見る | 落ちた例・理由 |
|---|---|
| `.DS_Store` などの OS ファイルが無い | Blocks |
| 画像とフォント以外は 1 ファイル 256 KiB 未満、全体 512 ファイル以下 | Policy hold |
| plugin の root に `package.json` と lockfile が並んでいない | 入れた人の側で install が走るので Policy hold（harness-scope で devDependencies 87 MB が配られていた） |
| `uv run` に `--frozen` か `--locked`、`npx`/`uvx` は版を固定 | Blocks（akc-cycle） |
| plugin フォルダのコードが環境変数（`HOME`、token 類）を読まない | 「読む側」と「送る側」がフォルダ内にそろうと credential の Policy hold になる。harness-scope では、`HOME` を読む hook と、実行時にコマンドを組むテスト、`plugin.json` の GitHub URL の組み合わせが送る側に数えられた。環境を読まない作りにすれば、§1 の URL 欄は安全に置ける |
| hook と MCP の command は `${CLAUDE_PLUGIN_ROOT}` からの完全なパスで書く | subfolder の plugin では Blocks |
| symlink・submodule・LFS を使わない | 読み込まれる場所では Blocks |
| 読めるソースを commit する（minify・バイナリを置かない） | scan が読めないものは Policy hold |
| plugin フォルダ内の開発用 script が `plugin.json` を名指さない | `bench/` の script が `plugin.json` を探しただけで、そこから参照される icon が「code could run」の Policy hold になった（`UNREAD_ASSET_REFERENCED`）。root を plugin にした repo では避けられないので、reviewer に任せる |
| README の開示と URL の組み合わせ | README が「`~/.claude.json` を読む」と開示し、同じ README に外部 URL があり、skill の本文に `curl` の語があるだけで credential の Policy hold になった（`MCP_FORWARDS_CREDENTIAL_ENV`）。開示は消さずに残し、reviewer の確認に任せる |
| plugin フォルダの manifest（`plugin.json`、`gemini-extension.json` など他ツールのものも）に URL を置かない | akc-cycle は承認済みの 778526b に URL 入りの `gemini-extension.json` を足しただけの f66a18f から credential の Policy hold（"Update adds credential forward"）が続いた。検出は「読む側」の skill と「送る側」の manifest の URL の組で成立する。harness-scope は `plugin.json` の URL 欄を外した 0.1.7 で検出が消えた。listing の URL は提出フォームで渡す |
| skill の本文と CHANGELOG のコマンド例は、作業 dir をフルパスか相対パスで渡す | `--project "$PWD"` を書いた skill だけが credential の Policy hold の対象に挙がり、`$PWD` を外した版で対象から消えた（akc-cycle 1.6.2 → 1.6.3、2026-11-02）。直した経緯を CHANGELOG に書くときも、その変数名や「password」「key」の語を書くと CHANGELOG が対象に加わる。CHANGELOG には変えた挙動だけを書く |
| plugin が mod（`hooks/hooks.json` が hooks module を指す）を含むと、全版が Policy hold | 理由は "This plugin includes a mod"。コードの修正では外れず、reviewer が版ごとに公開する（harness-scope、2026-10 末から live の版にも「no longer meets directory policy」の通知）。README の hook ごとの説明は Note への答えとして保つ |

## 5. 載る面を決める

skill と command はどの面でも動く。hook と agent は Cowork と Claude Code だけで動き、chat は
黙って無視する。トップレベルの `bin/` があると、claude.ai と Cowork は plugin を入れない。
hook だけの plugin は chat の面（portal の表示では "Claude apps"）に載せず、Claude Code と
Cowork だけにする（著者の判断）。portal の設定タブの **Listed on** で "Claude apps (web,
desktop, mobile)" のチェックを外してもらう。既定では、plugin が動く面すべてに載り、後の版で
動く面が増えればそこにも載る。外した面は外れたままになる。

## 6. portal の操作を著者に渡す

提出・同意・公開は著者の操作。Claude は各 step で入れる値を先にそろえて渡す。

portal は https://claude.ai/directory/manage。日本語 UI では step 名が「ソース / 掲載情報 /
データの取り扱い / コンプライアンス / 確認して送信」になる。

| step | 著者がすること | Claude が渡すもの |
|---|---|---|
| 入口 | **Submit new** → **Plugin bundle** | — |
| ソース（Source） | Repository・Plugin path・Branch or tag を入れ、**Validate** | 3 つの値。repo と path は提出後に変えられない。private repo は Claude GitHub App の install とソースのアップロードへの同意が要り、公開の前に public にする。検証結果の各行は ▶ で開くと原因のファイルと code（`UNKNOWN_KEY` など）が出るので、著者に開いて見せてもらい §7 で扱う |
| 掲載情報（Listing details） | 表示を確かめる | 直したい欄があれば `plugin.json` / README を直して push し、Re-validate する |
| データの取り扱い | 4 問を選択式で答える | 選ぶ選択肢と理由。選択肢: 個人データ（いいえ / Reads only / Reads and stores）、宣言した connector 以外への送信（いいえ / Yes — listed in README）、Claude から受けたデータの保持（Not retained / Under 30 days / Longer）、18 歳未満向け（いいえ / はい）。送信がある plugin は README の開示を確かめてから Yes を選ぶ |
| コンプライアンス | 連絡先 email を確かめ、4 つの同意を選ぶ | 各同意の意味: Terms と Policy への同意 / privacy policy が扱うデータを正しく説明する（`privacyPolicyUrl` が無い plugin では README のデータの節がその説明になる） / 認証情報を持ち出さず宣言した MCP server の外でコードを実行しない / Anthropic からの連絡。Policy hold があると、この画面に「held for policy review」と出るが、提出はできる |
| 確認して送信（Review and submit） | 更新の届け方（既定は GitHub push webhook）と **Auto-publish passing versions** を選び、**Submit for review** | Auto-publish は off を勧める（main への push が審査後そのまま live になるため）。webhook の設定は repo の admin が要る |

GitHub アカウントは、提出する Claude organization で claude.ai に接続しておく。1 organization
につき 24 時間で 10 件まで（下書きと取り下げも数える）。

## 7. 結果を読み戻して直す

著者が貼った report（または portal の画面）を読み、finding ごとに扱う:

- **Blocks**: 直して push し、Source step の **Re-validate** を押してもらう。report は 1 commit
  ごとのもので、push しただけでは変わらない
- **Policy hold**: 原因をコードから特定できれば直す。特定できなければ、そのまま提出して
  reviewer の確認に任せる
- **Warning / Note**: 直せるものは直す

直した commit の本文に、portal の finding の文言・原因・直し方を Context / Decision で残す。
次の提出のための一次記録になる。

## 8. 提出後と掲載後

- 状態は portal の Submissions → plugin のページで追う。**Versions** タブに、scan した各
  commit と結果が出る
- 審査を通った版は、**Publish** を押すまで live にならない（既定では Anthropic の reviewer が
  公開する）。押すのは著者
- 設定タブの **Publish new versions automatically** を on にすると、検査を通った 2 版目以降は
  Publish を押さずに live になる。最初の版には効かず、reviewer が公開する設定のあいだも効かない
- 更新は、追跡している branch へ merge するだけで届く。`version` を上げ、CHANGELOG を書く。
  GitHub push webhook が無ければ、新しい commit は約 6 時間ごとの定期確認で拾われる。webhook は
  設定タブの **アップデート** の **セットアップ** で著者が入れる（repo の admin が要る）。
  すぐ見せたいときは **Check for new commits**。新しい版が保留や不合格のあいだも、listing は
  最後に公開した版を出し続ける
- reviewer 待ちの版があるあいだに新しい commit を出すと、その依頼がどう扱われるかは doc から
  読めない。待ってから出す
- **Usage** タブ（最大 90 日、CSV 出力可）で、インストール数・使っているアカウント数・
  コンポーネントごとの使用回数・directory の funnel が見られる。月次の読み取り対象に足すかは
  著者に 1 行で渡す（scheduled task の変更は著者の操作）

## 9. 記録する

- `~/MyAI_Lab/personal-branding/docs/research/listing-queue.md` に 1 行足す（掲載先「Anthropic の
  plugin directory（claude.ai/directory）」、経路「developer portal から提出（著者）」）。状態は
  提出までは `manual`、公開されたら `done`。personal-branding の作業ツリーには `listing-pr-daily`
  などの未 commit の変更が残っていることがあるので、HEAD の版に自分の 1 行だけを足した blob を
  `git hash-object -w` → `git update-index --cacheinfo` で index に置き、その 1 行だけを commit する
- 行為ログに 1 行為 1 行書く。書き先・worktree の更新（`fetch` → `rebase origin/main`、衝突したら
  書かずに報告）・採番（Acts 節の最大の `A-NNNN` に 1 を足す）・commit の形（push しない）は
  `~/.claude/scheduled-tasks/listing-pr-daily/SKILL.md` の行為ログの手順に従う。行の形:
  `| A-NNNN | YYYY-MM-DD | PB | Plugin directory submission for <plugin> (private route) | — | repo |`
- portal での提出は非公開の経路なので、提出の時点では「提出した」ことだけを書く。公開後は
  listing が公開の場になるので、場所を名指してよい（rule `public-records.md`）。queue の
  `ログ ID` に A-NNNN を入れる
