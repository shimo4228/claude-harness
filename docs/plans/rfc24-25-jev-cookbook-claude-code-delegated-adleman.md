# jev-skill-router — cookbook skill_suggestion の Claude Code 実装を自作 skill として作り、公開する

## Context

RFC-0024 候補 2（skill ルーター）を最初の Jev 配線として実装する。動機は ADR-0018:85 の
「skill 自発トリガー上限 ≒ 40%」への構造的回答と、間違った skill 本文を読む往復の削減。
RFC-0024 は `blocked`（Fable 枠回復待ち）だが、著者が 2026-09-21 に着手を指示した。

既製実装の調査（as-of 2026-09-21、GitHub code/repo 検索 + README 一次確認）:

- 公式 cookbook [skill_suggestion](https://docs.typesafe.ai/cookbooks/skill_suggestion.md) は
  Python SDK のノートで Claude Code への言及なし
- **Claude Code hook としての忠実実装は 0 件**。Claude Code 向け 2 件（jev-skill-gate /
  skill-router、各 ★2）は別機構（skillOverrides 書き換え / skills.sh からの install 提案）
- 忠実実装は Hermes 向けに 1 件: `DECRUX9812/typesafe-skill-router`（MIT、★8、`f150284`）。
  cookbook に無い実測知見を 2 つ持つ — **255 choices 上限（→ chunk + `none_of_these`）** と
  **Choice と fits が割れたときの margin 規則**

著者決定（2026-09-21）:

1. 共通の源は cookbook。DECRUX は**参照**に留め、コードはコピーしない。cookbook から
   Claude Code 向けに自分で実装し、**公開する**（同じことをする人の役に立つ）
2. roster は user skills だけでなく **plugin skills と project skills も対象**にする

### origin の付け方（rule: skills.md の語彙に合わせる）

`origin: shimo4228` とし、系譜は `replaces:` に残す（skills.md の既存規約 —
「外部由来を自作で書き直したとき origin を反転して系譜を残す」、先例 `skill-creator`）。
`…-customized` にしない理由は機械的: `.claude/verify.sh:120` の owned 判定と harness-sync の
公開フィルタはどちらも `shimo4228` を見るので、customized を名乗ると **ゲートにも公開にも
乗らない**。系譜に書くもの:

- cookbook URL + 取得日（質問文・state 形・2 call 構成・`<skill_relevance>` 文面の出所）
- DECRUX `f150284`（255 cap と margin 規則の出所。コードは非コピー、知見の credit）

OSS 慣習としての整理: 公開レシピの独立実装は通常の行為。コードをコピーしないので MIT の
notice 義務は生じないが、README の Prior art に DECRUX と cookbook を明記する。cookbook 本文の
ライセンス表記は docs 上で未確認（typesafe-ai の SDK / skills repo は MIT）— 質問文は機能的な
短文だが、引用元 URL をコード内コメントと README に必ず置く。

## 方針

1. **shadow から入る**。注入せずログだけ書き、「薦めた skill」と「そのターンで実際に使われた
   skill」の一致を先に測る。shadow は自己 detach で走り、プロンプトをブロックしない
2. **ログ行は最初から RFC-0025 の registry schema**（RFC-0025 の最小実装を兼ねる。貯めるだけ —
   読み戻し・描画・集計は作らない、CA ADR-0095）
3. RFC-0024 設計原則 1〜8 を継承: version pin `jev-1.13.0` / fail-open / timeout 明示 /
   確率を block に直結しない / 閾値はデータが溜まるまで cookbook 値（gate 0.30 / fits 0.30）
4. **公開物として自己完結**させる。harness 内部部品（`_advisory-common.sh` 等）に依存しない。
   stdlib のみ、Python 3.10+

## 成果物 — `skills/jev-skill-router/`（sub-project、`origin: shimo4228`）

書く前に skill: `skill-creator` を読む（rule: skills.md）。`pyproject.toml` を持たせるので
verify.sh の pytest / ty / ruff / LOC 予算が自動で掛かる。

```
skills/jev-skill-router/
  SKILL.md            install（settings.json snippet）/ key の置き方 / mode / ログの読み方 /
                      送信される範囲 / 系譜。disable-model-invocation: true
  README.md (+ja)     公開 repo の入口 — skill: readme-writer で書く
  LICENSE             MIT
  pyproject.toml      依存ゼロ、dev に pytest
  scripts/
    route.py          hook entrypoint: stdin JSON → skip 判定 → mode 分岐 → ログ / 注入
    roster.py         multi-root の skill 収集
    router.py         2 call（wide → rerank）+ gate + fits + chunk + margin
    jev_client.py     urllib の最小 client（timeout・1 endpoint・version pin）
    decision_log.py   registry 行の組み立てと追記
  tests/              pytest（network なし、client は scripted response を注入）
```

### roster.py — 3 系統を 1 つの名簿に

| 系統 | 発見方法 | 名簿上の名前 |
|---|---|---|
| user | `~/.claude/skills/*/SKILL.md`（symlink は辿る: `hunk-review`）| `name` |
| plugin | `~/.claude/plugins/installed_plugins.json` の `installPath` のうち、`settings.json` の `enabledPlugins` が true のものだけ → `<installPath>/skills/*/SKILL.md` | `<plugin>:<name>`（Skill tool の呼び名と同じ） |
| project | hook 入力の `cwd` から git root まで遡り、各階層の `.claude/skills/*/SKILL.md` | `name`（同名は project が勝つ — Claude Code の解決順に合わせる） |

- `plugins/cache/` を総なめしない — 無効・旧版の plugin を拾うため（win4r README が同じ罠を記録）
- 除外: 自分自身、frontmatter `disable-model-invocation: true`
- `--add-dir` の追加ディレクトリは hook 入力に無いので対象外（SKILL.md の Limits に書く）
- 名簿が 240 を超えたら chunk（Jev API は 1 問 255 choices まで — DECRUX の実測）
- built-in skill（anthropic-skills:* 等、ディスクに SKILL.md が無いもの）は見えない。Limits に書く

### router.py — cookbook の移植

- Call 1: `Choice`（短縮 description 60 字）+ gate `Noul` 3 問（cookbook の質問文をそのまま）。
  gate = 3 問の平均（`prose_suffices` は反転）< 0.30 → 提案なし、Call 2 を使わない
- Call 2: top 3 を full description + SKILL.md 冒頭 700 字で `Choice` + 候補ごとの fits `Noul`。
  `max(fits) < 0.30` → 提案なし
- chunk 時は各 chunk に `none_of_these` を足し、P(none) ≥ 0.50 の chunk は候補を出さない
- margin 規則（Choice winner ≠ fits 最大のとき）は **実装するが既定 off**（`fits_margin=None`）。
  cookbook に無い規則なので、shadow ログで不一致の頻度を見てから点ける
- 質問文は定数として 1 箇所に置き、`QUESTION_HASH` をそこから導出する

### route.py — mode と skip

- `JEV_ROUTER=off|shadow|inject`（既定 shadow）
- skip（Jev を呼ばない）: off / prompt が `/` 始まり / 4000 字超 / key 不在 /
  cwd が skill-comply sandbox
- key: 環境変数 `TYPESAFE_API_KEY` → 無ければ `~/.config/typesafe/env`（0600）。
  model / base_url は引数と定数で固定し、他所の `.env` は読まない
- shadow: 自プロセスを `start_new_session` で再起動して即 exit 0、stdout 空
- inject: 同期（wall-clock 上限 3 秒、超えたら無言で exit 0）。提案があれば
  `{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":…}}` を自前で出す。
  文面は cookbook の `<skill_relevance>` ブロック。「提案なし」のときは**何も注入しない**
- あらゆる例外を握って exit 0。失敗も `reason` 付きで 1 行残す

### decision_log.py — RFC-0025 schema

```json
{"ts":"…Z","project":"…","session":"…","mode":"shadow",
 "model":"jev-1.13.0","router_version":"0.1.0","question_hash":"<12>",
 "roster_hash":"<12>","n_skills":78,"n_by_source":{"user":55,"plugin":15,"project":8},
 "prompt_sha":"<12>","prompt_chars":123,
 "gate":0.51,"gate_values":{…},"shortlist":[…],"fits":{…},"winner":"…",
 "suggestion":"tdd"|null,"reason":"…","chunks":1,"usage":{…},"elapsed_ms":640}
```

- 既定の書き先は `~/.claude/metrics/jev-decisions.jsonl`（env で上書き可）。0600、symlink 先には書かない
- **プロンプト本文は書かない**（`skill-usage.jsonl` と同じ設計判断）
- `question_hash` が RFC-0025 の要点「質問文の版」。変われば別分布として読む
- outcome への join は読む側がやる: `session` + `ts` で `metrics/skill-usage.jsonl` の
  `invoke` / `read` / `slash` と時系列突合

## harness 側の配線

- `settings.json`: `UserPromptSubmit` に
  `python3 ~/.claude/skills/jev-skill-router/scripts/route.py` を 1 行、`env` に `JEV_ROUTER=shadow`
- `.gitignore`: `metrics/jev-decisions.jsonl`
- `hooks/README` 等の hook 一覧に 1 行（Doc Sync）
- harness_lint の envelope check が skills/ 配下の python にも掛かるかは実装時に確認。掛かるなら
  lint 側の許可でなく、check の対象規則（hooks/*.sh の手書き封筒）に当たらないことを bats/pytest で示す

## テスト（TDD、pytest。coverage ≥ 80%）

- roster: 3 系統の発見 / 無効 plugin を拾わない / project が同名で勝つ / plugin 名が `p:s` /
  `disable-model-invocation` と自分自身の除外 / symlink skill / 壊れた frontmatter で落ちない
- router: gate で打ち切ると Call 2 を呼ばない / fits で reject-all / chunk と `none_of_these` /
  同確率の tie-break が決定的 / margin off が既定
- route: 各 skip 条件で client 未呼び出し・stdout 空 / shadow は stdout 空 + ログ 1 行 /
  inject の封筒形と event 名 / API 失敗・timeout で exit 0 + `reason` 行 /
  ログに prompt 本文が無い / symlink のログ path に書かない / 他所の `.env` が model を変えない
- golden: inject の出力 1 本を `tests/golden/` に凍結（機械が parse する出力 — rule: llm-first-code）

## 実行 chain（skill: `implementation-chain`、種別 feat）

このセッションは judge-tier なので実装は build-tier の新セッションへ dispatch が既定。
着手時 `claims.py claim RFC-0024 --label "jev-skill-router shadow"`。
skill-creator（intent packet → 草稿ゲート）→ TDD → 実装 → Review: code reviewer +
**security-reviewer**（外部 IO・資格情報・無人実行の 3 面。送信範囲と key の扱いを重点）→
Doc Sync → `.claude/verify.sh`。

## 台帳と記録

- `rfcs/0024`: `state: in_progress 2026-09-21`。Status に「候補 2 のみ着手。Rationale の既製
  plugin 却下は維持 — 既製を入れず cookbook から自作した」
- `rfcs/0025`: `state: in_progress`。Status に「registry の最小形を `jev-decisions.jsonl` として
  router に同梱。Unresolved『質問文を変えたとき』は question_hash で別分布扱い、と暫定回答」
- ADR 1 本（skill: `adr-writer`）: 無人 hook が外部 API へプロンプトを送る新機構。RFC-0024
  Prior art が要求する **ADR-0002 との差分**（注入は skills/ 正本へのポインタ 1 行 / 選択は
  prompt 投入時に決まる）を書く。Review-when は下の inject ゲート

## 公開（人間ゲート。ローカル検証の後）

1. ローカルで Verification 1〜4 が通る
2. README を skill: `readme-writer` で書く（何をするか / 送信される範囲 / install 3 手順 /
   shadow → inject の進め方 / Limits / Prior art: cookbook・DECRUX）。数値は cookbook の
   vendor 実験を「彼らの roster での方向」として引くに留め、自分の一致率は shadow データが
   溜まってから足す
3. skill: `harness-sync` で claude-harness 集約 repo へ + 単独 skill repo `jev-skill-router` を作成
   （単独 repo の新設・公開実行は著者の承認で行う — rule: boundary.md）
4. 公開後に hub repo / X での告知は別判断

## inject へ切り替える条件（今回は作るが点けない）

暦でなく観測量（measurement-discipline 原則 2）:

- routed 行 ≥ 200、うち同ターンで skill 使用があった行 ≥ 40
- 読む生値 3 つ: 一致（suggestion = 実使用）/ needless（提案あり・使用なし）/ missed（使用あり・
  提案なし）。一致が低ければ注入しても効かず、高すぎれば注入が要らない
- 切替前に実機で 1 回: `contemplative-name-reminder.sh` と同時に `additionalContext` を返した
  ときの合成挙動（RFC-0024 Unresolved）
- 日本語 prompt では fits が下に寄る可能性（DECRUX README: 西語で −0.14）— shadow の分布で確認

## 既知の限界（受容）

- 無人セッション（launchd の triage / daily-research）のプロンプトも送られる。止めるなら
  起動 script に `JEV_ROUTER=off`（別判断、今回は触らない）
- プロンプトに貼られた secret はそのまま外に出る。公開物は自己完結が要るので harness の
  secret-scan は再利用しない。SKILL.md / README の「送信される範囲」に明記し、ADR の Drawbacks に書く

## 人間に渡す操作

- TypeSafe API key を `~/.config/typesafe/env` に置き `chmod 600`（Claude は key を扱わない）
- settings.json / 新 skill / ADR / RFC state の diff 承認、公開の実行承認

## Verification

1. `uv run --project skills/jev-skill-router pytest -q` 緑・coverage ≥ 80% → `.claude/verify.sh` 緑
2. key 設置後、`~/.claude` と zenn-content の両方で通常プロンプトを数本・`/` コマンドを 1 本 →
   `tail metrics/jev-decisions.jsonl`: `/` は行なし、`n_by_source` に plugin と project が出る、
   zenn-content では project skill（`writing-ecosystem` 等）が shortlist に現れる、体感遅延なし
3. `jq 'select(.suggestion!=null)'` で提案の妥当性を目視、`elapsed_ms` と `usage` を確認
4. `JEV_ROUTER=off` で行が増えない / key file を外しても prompt が通る（fail-open）
5. `python3 scripts/hooks/harness_lint.py` 緑
