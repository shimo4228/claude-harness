# ADR-0052: URL 到達性と skill usage 集計を evidence script へ降ろす（skill-health / skill-stocktake）

## Status

accepted

## Date

2026-08-26

## Context

2026-08-26 の sweep（RFC-0008 / RFC-0009）で、skill の機械項目が 2 つ散文のまま残っていた。

**(1) URL 到達性。** URL の live check を要求する検査が 2 箇所にある —
`skills/skill-stocktake/SKILL.md` L122-124（Currency: "fetch named URLs"）と
`skills/context-sync/SKILL.md` L267（`EcosystemRepo` URLs が 200 を返すか、`curl -sI`）。
既存の evidence script（`adr_lint` / `readme_evidence` / `citation_audit` / `graph_lint` /
`geo_check` / `scan_refs` / `harness_lint`）はどれも URL 到達性を持たない。RFC-0008 は
`paper-ecosystem` の DOI / arXiv validity（L291）も消費者に数えていたが、これは誤り
（Decision 6）。

散文のまま残していることの害は「書き味の drift」ではなく **burst** である。stocktake
Phase 2（SKILL.md L106）は 10-12 件ずつの **並列 batch agent** を起動し、各 agent に
Currency 検査を無条件実行させる。66 skill（この worktree の `skills/*/SKILL.md`）分の
URL fetch が並列 agent に散る形は、
`rules/common/debugging.md` が禁じた形そのもの — 2026-07-16 に burst を継続した結果、
アカウント無期限 block と全作成物削除が起きている。

**(2) usage 集計。** stocktake の Phase 1 は `metrics/skill-usage.jsonl` を読んで
「直近 14 日の deliberate use 件数と最終使用日」を出す。4 つの補正規則が SKILL.md
L76-102 に散文で書かれ、毎回 LLM が jq one-liner を組み直していた。補正の誤りは
**静かに verdict を汚す** — event type を合算すれば一度も選ばれていない skill が busy に
見え（誤った Keep 証拠）、log 欠損を 0 と描画すれば「未計測」が「未使用」に化ける。

分業原理は「存在 = code、内容 = LLM」（[ADR-0021](./0021-rules-metadata-and-premise-lint-gates.md)
が導入）と skill: `review-to-lint`。直前の同型の先例は
[ADR-0051](./0051-extract-mechanical-adr-checks-into-cross-repo-lint.md)。

## Decision

1. **`skills/skill-health/scripts/url_liveness.py` を新設**する。URL リストを受け取り
   `url` / `status` / `verdict` の JSON を返す evidence モード — 判定せず、常に exit 0。
   verdict 語彙は `live`（2xx/3xx）/ `dead`（404・410・その他 4xx・接続失敗）/
   `blocked`（401・403・405・406・429・451 と 5xx — 到達したが URL について何も語らない応答）/
   `skip`（未検査）。**`blocked` を `dead` に畳まない**ことがこの語彙の要点で、403 は
   bot policy であって不在の証拠ではない（`cited-source-mirror-verification` L61 が
   SSRN の 403 を記録している。実測: `https://www.ssrn.com/abstract=0000000` → 403 →
   `blocked`、2026-08-26）。
1a. **URL の抽出も `scan_refs.py` に持たせる**（`--external-urls`、一覧を出して exit 0）。
   初稿は消費側 SKILL.md に `grep -rhoE … | sed 's/[.,)]*$//'` を書いていたが、これは
   (a) fenced code block の中の例示 URL まで拾って実際に fetch する（避けたはずの burst を
   audit 自身の doc で起こす）、(b) 末尾句読点を後から削るので URL に含まれる `)` も削り、
   生きているリンクを `dead` と報告する — `blocked`/`dead` 語彙を分けた目的をパイプ 1 本
   左で壊していた。実測（2026-08-26、この worktree の `skills/*/SKILL.md` 66 件）:

   ```bash
   grep -rhoE 'https?://[^ )>"`]+' skills/*/SKILL.md | sed 's/[.,)]*$//' | sort -u   # 71 件
   uv run --project skills/skill-health python -m scripts.scan_refs --external-urls  # 46 件
   ```

   差分は **grep 側にのみ 25 件、scan_refs 側にのみ 0 件** — 25 件は全て脱落ではなく除去で、内訳は fence 内の例示・placeholder
   （`https://github.com/<owner>`、`owner/repo`、`zenodo.NNNN`）・`:` で切れた template
   （`…/works/doi:<DOI>` → `…/works/doi`）・URL 自身の閉じ括弧を削った形
   （`…/Foo_(bar)` → `…/Foo_(bar`）。後ろ 2 種は code-review が実測で見つけたもので、
   どちらも実在しない URL を fetch して `dead` と報告していた。Markdown link の href に含まれる括弧の復元（codex cross-model 指摘）も
   同時に入れたので、正しい URL 側の取りこぼしは 0 件である。
   抽出は `test_scan_refs.py` の回帰下に入った
2. **rate limit は policy signal として実装する**（`rules/common/debugging.md`）。1 URL
   1 リクエスト、直列 + リクエスト間 delay、429/503 が閾値回（既定 2）連続したら
   **run を停止**して残りを `skip` にし `halt_reason` を報告する。**retry と backoff は
   持たない** — retry 機構はこの rule への違反をコードに焼き込むことになる。
   同じ理由で **concurrency を持たない**（並列 fetch は本 script の存在理由の否定）。
   **cache も持たない** — liveness は検査時点の事実で、cache された `live` は日付の無い主張。
2b. **リダイレクトを追わない。** 名指しされた URL が返した 3xx をそのまま報告する
   （語彙上 `live` — 「その URL は答えた」）。追う実装は 3 つの不変条件を同時に壊していた:
   (a) urllib は 1 回の `open()` の中で chain 全体を歩くので、呼び出し側が 1 回と数えて 1 回
   sleep する間に複数リクエストが出る — 禁じたはずの burst 形を library が再導入する、
   (b) 既定 handler は `ftp:` も任意 host も許すので、外部 origin の
   `302 Location: http://127.0.0.1:<port>/` が loopback へ到達して `live` を返した
   （PoC 実証、security-reviewer 2026-08-26）、(c) redirect loop が元の 301 として現れて
   `live` になった（codex cross-model 指摘）。代償は 1 つで、それは正直なもの — 削除された
   ページへ 301 する URL が `live` と読める。chain を追うのは liveness でなく resolution である
2a. **corpus は repo 制御データとして扱う。** URL 一覧は任意の `SKILL.md`（package manager が
   無審査で書き換える symlink 先の外部 skill を含む）が 1 行足せば入る。したがって
   loopback / private / link-local / multicast / reserved に解決する host は **fetch せず
   `skip`**（note: `internal address, not checked`）とし、**リダイレクトは各 hop で同じ検査を
   再適用する**。security-reviewer が 2026-08-26 に本 diff の版へ PoC を当て、外部 origin の
   `302 Location: http://127.0.0.1:<port>/…` を既定 opener が追って
   `{"status": 200, "verdict": "live"}` を返すこと、`http://169.254.169.254/latest/meta-data/`
   が corpus から素通りすることを実証した（前者は Decision 2b で構造的に閉じた）。`dead` にも `blocked` にも畳まない — 何も
   分からなかったのだから `skip` が正しい。DNS rebinding（解決と接続で答えが変わる）は
   範囲外とする: これは sandbox ではなく evidence probe である
3. **置き場は `skill-health`**。第一の理由は所有である — URL の抽出（Decision 1a）は
   skill-library の本文を読む仕事で、それは `scan_refs.py` そのものの仕事だった。
   `url_liveness.py` 自体は skill を何も知らない probe であり、scanner との隣接は抽象の共有
   ではなく所有と配線の一致である（初稿の「filesystem 側と network 側の二半身」という
   書きぶりは誇張なので訂正する。simplify altitude 指摘、2026-08-26）。
   第二に機構 — `.claude/verify.sh` L316 の pytest 配線は
   `git ls-files 'skills/*/pyproject.toml'` で sub-project を発見するので、`~/.claude/scripts/`
   直下ではテストがゲートで走らない（同じ穴は 2026-08-22 の code-review が `codex-review` の
   shell test で実証済み。verify.sh L321-323 に記録がある）。**これは自分で書いた glob なので
   1 行で広げられる**: 広げなかったのは、広げると root 直下も sub-project 探索の対象になり
   所有権フィルタ（`origin:` 判定）の適用先が曖昧になるためで、決定的な理由ではなく
   第二の理由として数える
4. **`skills/skill-stocktake/scripts/usage_stats.py` を新設**する（uv sub-project、
   evidence モード、exit 0）。4 補正規則をコードに固定し、各規則を
   `tests/test_usage_stats.py` の回帰テストで pin する。
5. **この diff で薄化するのは `skill-stocktake` と `skill-health` の 2 つ。**
   `skill-stocktake` は usage の散文手順（L76-102）を Step 0 配線に置換し、URL 検査を
   **親所有**の 1 パスとして Phase 1 に移す。Phase 2 の Currency 項目からは
   「fetch named URLs」を削り「親が Phase 1 で 1 回検査した verdict を読む。fetch するな」に
   置き換える。script が渡せない 2 つの解釈（`measurable: false` → `—` であって 0 ではない /
   `span_shorter_than_window: true` → 実 span をラベルにする）は SKILL.md に残す。
   **`skill-health` は usage の第 2 の消費者だった** — Phase 3 Utility（7/30/90 日窓）が
   4 補正規則の散文コピーを持ち、しかも**この diff が削除した節を canon として名指していた**。
   同じ script 呼び出し（`--days 90`）に置換する。
   **`context-sync`（L267 の `curl -sI`）は本 diff では変換しない** — S2 セッションの領分で
   並行編集が衝突するため。RFC-0008 の消費者としては開いたままで、変換は S2 に委ねる。
   したがって本 ADR 時点で `url_liveness` の配線済み消費者は 1 箇所である
6. **`paper-ecosystem` を消費者から外す。** DOI / arXiv validity は generic liveness では
   満たせない — DOI は誤った landing page へ 302 しても 200 を返しうるし、arXiv ID は
   形式検証の話である。これは識別子解決の問題で、`review-to-lint` の適用候補リストに
   `citation-formatter` として別枠で残っている（RFC-0005 の行 2 / 行 8）。RFC-0008 の消費者
   列挙（3 箇所）は本 ADR で 2 箇所に訂正する — **台帳側への注記は判断役（triage セッション）
   に委ねる**。本 build セッションは branch 上の commit だけを返す契約なので rfcs/ を書かない。
7. **verify.sh / commit hook への常時配線はしない** — ADR-0051 Decision 2 の判断
   （対象を触らない commit にも毎回課税する）をそのまま踏襲する。実行座標は
   skill のステップのみ。ただし sub-project の **pytest は** verify.sh full mode が
   自動発見して走る（Decision 3 の置き場理由）。

### 免除境界の実測（2026-08-26、実ログ 3060 行）

4 補正規則は (1) event type の分割（`slash + invoke` のみが deliberate）、(2) `sandbox: true`
行の除去、(3) tag が無い時代の sandbox path prefix の除去、(4) ログが窓より若いときの実 span
表示 — 全文は `usage_stats.py` の docstring が正本で、以下はその (3) の境界の実測である。
`review-to-lint` §3 は「免除境界を先に実測する」を要求する。実測値:

| 観測 | 値 |
|---|---|
| 全行 | 3060（read=2055 / invoke=813 / slash=192） |
| `sandbox: true` タグ付き行 | **0** |
| sandbox path を持つがタグ無しの行 | **25**（2026-07-28 .. 2026-08-17） |
| うち直近 14 日窓の deliberate | 5 |
| 補正後の窓内 deliberate 合計 | 319（手動 jq の結果と一致） |

タグは 2026-08-17 に追加されたが**実際には 1 行も出ていない** — `select(.sandbox != true)`
だけの濾過は現時点で何も落とさず、規則 3（path prefix）が仕事の全部をしている。効果は
均等ではない: `verify-bootstrap` は無補正で 2 件、補正後 **0 件**。compliance test 下の
skill が「使われている」ように見えるのを防いでいるのはこの 1 規則だけである。

境界は `/` で切る（`/tmp/skill-comply-sandbox-notes` を巻き込まない）。過剰マッチは
本物の使用を消すため、取りこぼしより高くつく。

規則 3 には失効がある: 既定 14 日窓が 2026-08-31 以降 2026-08-17 に届かなくなる。それでも
無条件のまま残す — `--days` は呼び出し側が決めるので `--days 90` の監査では依然必要で、
prefix 判定は O(1)、`/` 境界により過剰マッチしない。ログ自体から 2026-08-17 以前の行が
消えた時点で削除する。

### 固定した検証（手動 jq との一致）

`usage_stats.py --log ~/.claude/metrics/skill-usage.jsonl --now 2026-08-26T13:51:25Z` の出力は
現行の手動 jq 結果と一致した: 窓内 deliberate 合計 319、上位 8 件
（codex-review 37 / git-workflow 35 / code-review 29 / spawn-session 28 / simplify 27 /
implementation-chain 22 / harness-sync 14 / artifact-design 12）と last-used が全一致。
`read_events` の除外数だけ jq の read 総数 2055 と 3 件ずれるが、これは sandbox 除外が
event 分類より前に効く優先順（sandbox 化された `read` は read ノイズではなく sandbox ノイズ）
によるもので、意図した差である。

### search-first の照合結果（as-of 2026-08-26）

| 候補 | 版 / 日付 | 却下理由 |
|---|---|---|
| `urlchecker`（urlstechie） | 0.0.35 / 2024-02-03、MIT、21★ | JSON 出力が無い（CSV のみ）。403 と到達不能の区別なし |
| `linkchecker` | 10.6.0 / 2025-07-28、GPL-2.0、1.1k★ | GPL-2.0。設計がサイトクロールで「渡された URL だけ検査」と用途がずれる |
| `lychee`（Rust） | v0.24.2 / 2026-05-01、Apache-2.0 OR MIT、3.9k★ | 最有力。`--format json` と `--files-from -` を持つが、ソース（`lychee-lib/src/types/status.rs`）で `--accept` 外の全ステータスが `Error(RejectedStatusCode)` に畳まれ、**blocked と dead の区別は呼び出し側で再導出するしかない**。Rust binary で `dependencies = []` / uv 完結の既存規約から外れる |
| `deadlinks` | Apache-2.0、93★、最終コミット未確認 | クロール型で用途ずれ。JSON 出力・blocked 区別を一次ソースで確認できず。**鮮度が確認できていれば却下は覆らないが根拠は弱い** — lychee と同じ「blocked/dead を再導出するしかない」構造かどうかは未確認 |
| `linkinator-mcp` | — | 対話型 MCP tool。非対話 CLI + exit 0 evidence という契約に合わない |

**Verdict: Build — custom（stdlib `urllib.request` + `argparse`）。** どの候補も要件の核
（403=blocked と到達不能=dead の区別、429 連発で停止して報告）を組み込みで持たない。
lychee の CLI 面（`--files-from -`、accept 集合、per-host interval）は自前実装の設計
リファレンスとして流用した。

## Review-when

- **`lychee` 等が blocked/dead 相当の分類と「停止して報告」を native に持った** — その時点で
  Decision 1-2 の自作部分は薄い写像層に縮む。supersede 候補として再訪する
- **`grep -l url_liveness ~/.claude/skills/*/SKILL.md` が 1 件のまま 60 日経過した**
  （= context-sync が S2 で配線されなかった、または stocktake の Currency から URL 項目が
  落ちた）— 共有部品をやめて呼び出し側 inline に戻す
- **`log-skill-usage.sh` の schema が変わった / 同 hook が退役した** — `usage_stats.py` は
  ログの形に寄生しているので追従か削除
- **直近 2 回の stocktake レポートに `usage_stats` の `excluded` ブロックが載っていない**
  — script 実行そのものは記録されない（`log-skill-usage.sh` が記録するのは skill の
  read / invoke だけ）ので、レポートに転記された証拠の有無を代理指標にする。配線が死んで
  いれば両 script を削除する（`review-to-lint` §5 の「形骸化が観測されたら」の適用）
- **substrate が skill 使用統計を native に持った** — Scaffold Dissolution の downward

## Alternatives Considered

- **`lychee` を採用して薄いラッパーで包む** — 却下。blocked/dead の再導出と 429 停止は
  どのみち自前で、残るのは Rust binary という依存だけになる。`dependencies = []` を
  例外なく守ってきた既存 evidence script の規約も破る。ただし「移行なしで検査できるなら
  書かない」（`review-to-lint` §2）に最も近づいた候補であり、Review-when に再訪条件を置いた
- **`~/.claude/scripts/` 直下に共有 utility として置く** — 却下。verify.sh の pytest 配線が
  `skills/*/pyproject.toml` でしか発火しないため、テストがゲートで走らない
- **`url_liveness.py` も `skill-stocktake` 配下に置く**（`usage_stats.py` と同居）— 却下したが
  接戦。同居なら cross-skill の `uv run --project <sibling>` 呼び出しも、それが強いた
  `scan_refs.py` の `--project` 対応（と上の false negative）も要らなかった。採らなかったのは
  URL 抽出が `scan_refs.py` の仕事で、抽出と検査を別 skill に割ると今度はそちらが
  cross-skill 呼び出しになるため。**配線済み消費者が 1 箇所のままなら、この選択は再訪に値する**
  （Review-when 1 行目）
- **最初の消費者（context-sync）配下に置いて後で昇格**（RFC-0008 L14 の案）— 却下。
  context-sync は S2 セッションの領分で並行編集が衝突する。参照実在検査の owner は
  すでに skill-health にある
- **usage 集計は LLM の jq のままにする** — 却下。4 規則の合成を毎回やり直す作業が
  転記事故点で、誤りが「busy に見える skill」という誤った Keep 証拠として静かに通る。
  `verify-bootstrap` の 2 → 0 がその実例
- **429 に exponential backoff を入れる** — 却下。`rules/common/debugging.md` は 429 を
  transient error ではなく policy signal と定義している。backoff は「踏み抜いて続ける」の
  実装であり、2026-07-16 の事故はまさにその形で起きた
- **25 行に `sandbox: true` を後付けして規則 3 を削除する** — 却下。`skill-usage.jsonl` は
  hook が追記する**測定ログ**であり、後から書き換えれば以後の集計はすべて「実際に何が
  記録されたか」でなく「後で誰が何を直したか」に依存する。規則 3 のコストは prefix 判定
  1 行と test 2 件で、測定の再現性を失う価値はない（simplify altitude 指摘への回答）
- **verify.sh / commit hook に URL 検査を常時配線する** — 却下。ADR-0051 Decision 2 と同じ
  理由（無関係な commit への課税）に加え、ネットワーク検査をコミット境界に置くと
  オフライン時にゲートが不安定になる

## Consequences

- stocktake の usage 列が再現可能になった。数値の正本が script に移り、SKILL.md は
  「script が渡せない解釈」（`—` vs 0、実 span ラベル）だけを持つ
- **並列 batch agent からの URL fetch が消えた。** 66 skill 分の fetch が親 1 パスの直列
  検査に集約され、`rules/common/debugging.md` が禁じた burst 形が構造的に発生しなくなる。
  代償として stocktake の壁時計時間は URL 件数 × delay ぶん伸びる（既定 0.5s／件）
- `skip` / `halted` / `offline_suspected` / 非 null の `source_error` は「検査していない」を、
  `blocked` は「到達したが答えが URL について何も語らない」を表す。**この 2 つは別物**で、
  どちらも live とも dead とも書けない。読み手側にひと手間増えるが、これは意図した非対称
  （誤って dead と書く方が高くつく）
- 新しい sub-project が 1 つ増え（`skills/skill-stocktake`）、既存 sub-project に 1 ファイル
  増えた（`skills/skill-health`）。どちらも verify.sh full mode の pytest が自動で拾う
- RFC-0008 の「消費者 3 箇所」は 2 箇所に訂正された。DOI / arXiv validity は
  `citation-formatter` の別セッションに残る
- 副次的に `scan_refs.py` を 1 箇所直した。`uv run --project <sibling> python -m scripts.X` の
  形（本 ADR が作った cross-skill 呼び出し）を、呼び出し側 skill の `scripts/` に解決して
  dangling と報告していた。`--project` の最終セグメントを走査中の skills root 配下の
  sibling skill 名として解決する（解決できなければ行ごと skip。既存の `--directory` 除外と
  同じ扱い）。回帰は `test_project_override_resolves_against_the_named_sibling` ほか 1 件
- `last_used` は窓で切らない。「30 日前に使った」と「一度も deliberate に選ばれていない」が
  同じ `{deliberate: 0, last_used: null}` に潰れると retire 判断がその区別に乗れず、
  「script の数値を転記する」という Step 0 の規律に反して jq へ戻ることになる。
  窓は件数だけを縛る（回帰: `test_last_used_survives_the_window_cut`）
- harness に**初めて外向き egress** が生えた。UA は `claude-harness-url-liveness/0.1` で、
  一意な URL を corpus に 1 本仕込めば「この操作者がこの時刻に棚卸しを走らせた」+ IP が
  相手に見える。これは corpus に書ける者にしか使えず、その者は既に SKILL.md（agent が
  実行する制御プログラム）を書き換えられる — 露出の増分は受け入れる。内部 host への到達
  だけを Decision 2a で閉じた
- 免除境界の実測値（3060 行 / 25 行 / 5 行 / `verify-bootstrap` 2→0）は **ADR と
  `usage_stats.py` の docstring の 2 箇所**にある。**正本は docstring**（規則を実装している
  側）で、ADR はその時点のスナップショットとして凍結する。ログが変われば docstring 側だけを
  更新し、ADR は日付つき記録として残す（ADR-0051 Decision 3 が同じ二重記録を計上した先例）
- `scan_refs.py` の `--project` 対応は、false positive を 1 つ消す代わりに **false negative を
  1 つ作る**: `--project` の値が shell 変数のとき、その行の module 参照は dangling 判定から
  丸ごと外れる。cross-skill 呼び出しを導入した placement 選択のコストであって、単なる修正では
  ない（`skills/skill-health/scripts/scan_refs.py` の該当分岐にコメントで明記）
- **抽出は fence の外だけを見る。** これは例示 URL を fetch しないための境界だが、
  fence 内にしか現れない**運用 URL は検査対象から落ちる** — 実例:
  `skills/ai-native-preprint-submission/SKILL.md:112` の
  `https://aixiv.science/api/agent/submit`（codex cross-model 指摘）。「library が名指しした
  全 URL」という言い方は正確には「散文で名指した全 URL」であり、fence 内の endpoint の
  死活は依然として誰も見ていない。fence を含める形にすると audit が自分の例示 URL を叩く
  ので、閉じるなら「fence 内でも `curl`/`http` の引数位置にあるものだけ拾う」等の別設計が要る
- `url_liveness.py` は**実行経路上でネットワークに触れる**初の evidence script になった
  （ネットワークを触る script 自体は初ではない — `citation-sync/scripts/citation_audit.py`
  と `paper-deposit/scripts/zenodo_deposit.py` が既にある）。オフライン CI では
  `offline_suspected` 経路（全 URL が接続失敗なら `skip` へ倒す）が働くが、この経路は
  実ネットワークでの回帰テストを持たない — 単体テストは injected fetch で固定している
