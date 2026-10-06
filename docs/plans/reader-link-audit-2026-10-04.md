# RFC-0021 外部読者向け・軽量リンク監査

- 確認日: 2026-10-04（JST）。取得時刻は末尾の HTTP 記録に記載。
- 対象は公開 `claude-harness` の RFC-0021 だけ。RFC-0031 の正式実験、negative control 探索、著者一般の評価ではない。
- 公開 repo API は `private: false`、default branch の確認時 HEAD は `69a33e46890b66af5363836cfb3e8ab944206809`。main 版と、この SHA に固定した RFC 本文を取得した。[1][3][8]
- 根拠はすべて認証ヘッダーなしの live 公開 GET。ローカルの原稿、非公開 repo、保存された会話は根拠にしていない。ローカル確認は保存先・作業状態・指示ファイルの確認だけ。GitHub CLI の認証状態を確認したが、証拠の取得には使用しなかった。
- 判定語: **到達可能** = 公開資料で当該内容を直接確認、**記述のみ** = RFC 等に報告はあるが一次記録への接続なし、**未検証／到達不可** = 指定した公開 URL で確認できない。点数化はしない。HTTP 到達性と内容の裏づけは区別する。

## 結論

**問題→修正→理由の説明は追える。修正前後のコードも公開ミラーの別 SHA を経由すれば追える。ただし、著者の承認・当日の診断出力・検収ログまでを独立に確かめる鎖は閉じていない。** RFC の元 SHA が解決しないことと、修正自体が公開されていないことは別である。[8][22][24]

## 4 要素をたどった結果

| 要素 | 判定 | 公開で読めること／止まるところ |
|---|---|---|
| ① 出力・修正前 | **記述のみ＋修正前コードは到達可能** | RFC Summary / Motivation は 2026-09-13 の full gate 失敗と ty 診断を報告するが、stdout/stderr の保存物へのリンクはない。修正前テストは公開 sync commit `5f273eeb39cfc7a9a3fa35bcd5386984badefe87` に残り、入れ子の値へ直接添字アクセスする箇所を読める。元 commit `52b75cd` の body は公開ミラーで解決できなかった。[5][19]（前述の診断記述・変更前コードは [8][24]。） |
| ② 著者の修正・承認 | **コード修正は到達可能／著者判断は記述のみ** | RFC Status は著者 merge、旧 Status は起票・dispatch の判断を記す。ただし承認コメントや決定記録の URL はない。公開 sync commit `f95d231a3a7d92d5e96d59d74a750976242f66ff` の該当ファイル差分は +45/−31 で、境界関数を通す修正を確認できる。RFC の元 SHA `258ca6c` 自体は公開ミラーで解決しない。[6][20]（前述の記述とパッチは [8][22]。） |
| ③ 理由 | **主な理由は到達可能／ADR の指し先に注意** | RFC の Guide / Rationale は型を絞る理由と、検査対象の除外・ignore・pin 更新待ちを採らない理由を説明する。公開差分にも境界関数を使う説明があり、`llm-first-code` は型・境界強制の趣旨を記す。一方、RFC の「ANN 境界型強制（ADR-0056）」という参照先は予算系 lint の ADR であり、その文書だけではこの ANN 根拠を直接たどれない。[9]（主な理由の記述は [8][22][11]。） |
| ④ 結果 | **記述のみ（歴史的な実行結果は未検証）** | RFC Status は 2026-09-14 の ty / pytest / full gate 成功を報告する。しかし実行ログ・CI run・eval card の URL を示していない。現行テスト、collector、設定は公開で読めるが、full gate の `.claude/verify.sh` は固定 SHA の raw URL が 404 で公開 tree にもない。今回コードを実行しておらず、現在の成功も当日の成功も検証済みとはしない。[8][17][4]（公開コード・設定は [12][13][14]。） |

## SHA を取り違えずに追うための公開経路

- `52b75cd` と `258ca6c` は、それぞれ公開ミラーの commit API が **422 / No commit found for SHA**、GitHub commit ページが **404**。単一取得の失敗だけを根拠にしていない。API 結果は [5][6]。
  HTML 結果は [19][20]。
- 該当テストの公開 commit history は **200**。変更前と変更後の公開 sync SHA を取得し、変更後 commit API で該当パッチを確認した。+45/−31 と修正方法は RFC の説明に整合する。ただし、これで元 SHA の同一性や著者による当日の merge 操作を証明したとは扱わない。公開 sync commit は他の変更もまとめて含む。[18][22]
  変更前コードと RFC の記述は [24][8]。
- README は正本を `~/.claude/`、この repo を一方向 export と説明する。公開 sync script もローカル source directory からのコピーを示す。これは SHA が違う背景の説明にはなるが、「元 repo は private」の証明ではない。[7][16]
- 正しい公開 source repo の候補も確認した。RFC / README / sync script は元 SHA の解決先となる公開 repo URL を指定していない。所有者の公開 repo 一覧（pagination の next なし）で関連候補を確認し、名前からの候補 `shimo4228/growth-fable` は匿名 repo API **404**。別の公開 source repo で元 SHA を確認する経路はこの調査では特定できていない。404 から private・削除・不存在のいずれかを断定しない。[23][21]
  公開元の説明は [8][7][16]。

## 参照先の内容確認

- **ADR-0063: 200**。Review-when に full run の triage tick を使う較正条件があり、RFC Motivation の「赤いと較正が進まない」という関係は読める。この ADR 自身の pilot 計測・別 commit の検証には広げていない。[10][8]
- **ADR-0056: 200**。予算系 lint の global 規約の配置を決めた文書。HTTP リンクが生きていても、RFC が指す ANN 境界型強制の直接の根拠としては不一致が残る。[9][8]
- **llm-first-code: 200**。型を beacon とし、境界の明示型強制を重視する理由を読める。[11]
- **tests / collector / pyproject: 各 200**。現行テストの境界ヘルパー利用と collector 側の関数定義を確認。これはコードの存在の証拠であり、型検査・テスト実行の合格証拠ではない。[12][13][14]
- **plan / eval**: 対象 RFC 本文に、この修正の計画・承認記録・実行ログを指す plan/eval URL はない。公開 tree の一覧も確認したが、「全公開資料に記録が存在しない」とは結論しない。未指定の資料を総当たりする調査はしていない。[8][4]

## 具体的に足りない接続と利用上の意味

1. 元 SHA → 公開 sync SHA / 該当パッチの接続。公開差分は見つかるので、その対応ポインタだけでも外部読者の行き止まりは減る。[18][22]
   元 SHA の未解決は [5][6]。
2. 「著者判断（決定 1 = a）」・merge → 日付つきの承認記録。現状は RFC の報告を読むところで止まる。[8]
3. 診断と検収 → 対象 revision・コマンド・終了値が分かる公開ログ。full gate 本体の公開解決先もないため、外部で full run 全体を再検証する入口が閉じている。[8][17][4]
4. ANN 根拠 → 対応する規約節への正しい参照。ADR-0056 は到達性より参照内容の問題である。[8][9][11]

この 1 件では、修正案を理解したり再利用したりする読み方には役立つ。著者判断や歴史的検収を独立確認する用途では、本文中の報告と一次証拠を区別して読む必要がある。正式実験の必要性や著者一般への結論には広げない。

## 取得方法・再確認用ファイル

- HTTP 記録は、認証ヘッダーを付けない Python `urllib.request` による live HTTPS GET の結果。検索結果やローカル原稿による推定ではない。
- 保存済み公開レスポンスと HTTP 記録: `~/.hermes/cache/scratch/reader-link-audit-2026-10-04/`。
- URL・HTTP status・時刻・レスポンスファイルの機械可読記録: 同ディレクトリの `all-fetches.json`。
- 引用台帳: 同ディレクトリの `ledger.json`。本文の `[n]` はこの台帳から割り当てたもの。
- 公開文書の編集、commit / push、cron の変更はしていない。作成物はこのローカル報告と scratch 内の取得資料のみ。

## HTTP 記録（匿名 live GET）

確認範囲: 2026-10-04 16:10:24–16:12:23 JST。成功は本文取得を意味し、主張の正しさや実行成功を意味しない。

| Source ID | HTTP | 取得時刻（JST） | レスポンス保存先（scratch 内） |
|---|---:|---|---|
| [1] | 200 | 2026-10-04T16:10:24.623159+09:00 | `initial-0.txt` |
| [2] | 200 | 2026-10-04T16:10:24.952345+09:00 | `initial-1.txt` |
| [3] | 200 | 2026-10-04T16:10:25.568432+09:00 | `initial-2.txt` |
| [4] | 200 | 2026-10-04T16:10:57.344382+09:00 | `round2-0.txt` |
| [5] | 422 | 2026-10-04T16:10:57.066792+09:00 | `round2-1.txt` |
| [6] | 422 | 2026-10-04T16:10:57.011890+09:00 | `round2-2.txt` |
| [7] | 200 | 2026-10-04T16:10:57.019960+09:00 | `round2-3.txt` |
| [8] | 200 | 2026-10-04T16:11:39.945659+09:00 | `round3-0.txt` |
| [9] | 200 | 2026-10-04T16:11:39.953974+09:00 | `round3-1.txt` |
| [10] | 200 | 2026-10-04T16:11:39.957752+09:00 | `round3-2.txt` |
| [11] | 200 | 2026-10-04T16:11:39.926136+09:00 | `round3-3.txt` |
| [12] | 200 | 2026-10-04T16:11:39.945811+09:00 | `round3-4.txt` |
| [13] | 200 | 2026-10-04T16:11:39.961978+09:00 | `round3-5.txt` |
| [14] | 200 | 2026-10-04T16:11:40.321707+09:00 | `round3-6.txt` |
| [15] | 200 | 2026-10-04T16:11:40.321828+09:00 | `round3-7.txt` |
| [16] | 200 | 2026-10-04T16:11:40.310551+09:00 | `round3-8.txt` |
| [17] | 404 | 2026-10-04T16:11:40.279417+09:00 | `round3-9.txt` |
| [18] | 200 | 2026-10-04T16:11:40.470126+09:00 | `round3-10.txt` |
| [19] | 404 | 2026-10-04T16:11:40.543256+09:00 | `round3-11.txt` |
| [20] | 404 | 2026-10-04T16:11:40.842215+09:00 | `round3-12.txt` |
| [21] | 404 | 2026-10-04T16:11:41.614720+09:00 | `round3-13.txt` |
| [22] | 200 | 2026-10-04T16:12:22.113607+09:00 | `round4-0.txt` |
| [23] | 200 | 2026-10-04T16:12:22.984922+09:00 | `round4-1.txt` |
| [24] | 200 | 2026-10-04T16:12:23.358216+09:00 | `round4-2.txt` |

## Sources

[1] https://api.github.com/repos/shimo4228/claude-harness
[2] https://raw.githubusercontent.com/shimo4228/claude-harness/main/rfcs/0021-verify-full-red-growth-fable-ty.md
[3] https://api.github.com/repos/shimo4228/claude-harness/commits/main
[4] https://api.github.com/repos/shimo4228/claude-harness/git/trees/69a33e46890b66af5363836cfb3e8ab944206809?recursive=1
[5] https://api.github.com/repos/shimo4228/claude-harness/commits/52b75cd
[6] https://api.github.com/repos/shimo4228/claude-harness/commits/258ca6c
[7] https://raw.githubusercontent.com/shimo4228/claude-harness/main/README.md
[8] https://raw.githubusercontent.com/shimo4228/claude-harness/69a33e46890b66af5363836cfb3e8ab944206809/rfcs/0021-verify-full-red-growth-fable-ty.md
[9] https://raw.githubusercontent.com/shimo4228/claude-harness/69a33e46890b66af5363836cfb3e8ab944206809/docs/adr/0056-budget-lints-as-verify-bootstrap-annotation.md
[10] https://raw.githubusercontent.com/shimo4228/claude-harness/69a33e46890b66af5363836cfb3e8ab944206809/docs/adr/0063-rfc-0020-rust-pilot-hooklint.md
[11] https://raw.githubusercontent.com/shimo4228/claude-harness/69a33e46890b66af5363836cfb3e8ab944206809/rules/common/llm-first-code.md
[12] https://raw.githubusercontent.com/shimo4228/claude-harness/69a33e46890b66af5363836cfb3e8ab944206809/skills/growth-fable/tests/test_collect_snapshot.py
[13] https://raw.githubusercontent.com/shimo4228/claude-harness/69a33e46890b66af5363836cfb3e8ab944206809/skills/growth-fable/scripts/collect_snapshot.py
[14] https://raw.githubusercontent.com/shimo4228/claude-harness/69a33e46890b66af5363836cfb3e8ab944206809/skills/growth-fable/pyproject.toml
[15] https://raw.githubusercontent.com/shimo4228/claude-harness/69a33e46890b66af5363836cfb3e8ab944206809/skills/growth-fable/SKILL.md
[16] https://raw.githubusercontent.com/shimo4228/claude-harness/69a33e46890b66af5363836cfb3e8ab944206809/scripts/sync-from-local.sh
[17] https://raw.githubusercontent.com/shimo4228/claude-harness/69a33e46890b66af5363836cfb3e8ab944206809/.claude/verify.sh
[18] https://api.github.com/repos/shimo4228/claude-harness/commits?path=skills%2Fgrowth-fable%2Ftests%2Ftest_collect_snapshot.py&per_page=100
[19] https://github.com/shimo4228/claude-harness/commit/52b75cd
[20] https://github.com/shimo4228/claude-harness/commit/258ca6c
[21] https://api.github.com/repos/shimo4228/growth-fable
[22] https://api.github.com/repos/shimo4228/claude-harness/commits/f95d231a3a7d92d5e96d59d74a750976242f66ff
[23] https://api.github.com/users/shimo4228/repos?per_page=100&type=owner&page=1
[24] https://raw.githubusercontent.com/shimo4228/claude-harness/5f273eeb39cfc7a9a3fa35bcd5386984badefe87/skills/growth-fable/tests/test_collect_snapshot.py
