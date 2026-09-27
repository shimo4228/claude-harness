# skill-comply: 測定の正しさ（A・B）と、実行時間・可観測性

## Context

2026-08-01 の実運用で 4 件の問題が出た。優先度はユーザー指示のとおり
**測定の正しさ（A・B）が先、速度・可観測性が後**。速度を先に直すと
「速く間違った数字が出る」ようになるだけ。

| # | 問題 | 種別 | 状態 |
|---|---|---|---|
| **A** | project-scoped skill を測れないのに数字が出る | 測定の正しさ | 未着手 |
| **B** | setup_commands の生成器と実行器が契約を共有していない | 測定の正しさ | 未着手 |
| **C** | detector が要求するツールを子が持っていない場合がある（本調査で発見） | 測定の正しさ | 未着手 |
| **D** | 直列実行が遅い / 進捗が見えない | 速度・可観測性 | **実装済み・未コミット** |

D は先行して実装を終えている（テスト 85 件 green）。A・B と独立なので着地は分離できるが、
**単独でコミットするかは判断を仰ぐ**。

### 統一診断

A・B・C は別々のバグに見えて、根は 1 つ。

**レポートは「エージェントに何を訊いたか」については自己完結しているが、
「エージェントが実際に何をできる状態だったか」を一切記録していない。**

SKILL.md は「Reports are self-contained」と書き、spec・シナリオプロンプト・
タイムラインを載せる。しかし載っていないのは:

- 測定対象の skill が子から**読み込めたのか**（A）
- シナリオが用意したはずの**フィクスチャが実在したのか**（B）
- 子が**どのツールを持っていたのか**（C）

この 3 つはすべて「測定が成立する前提」であって、欠けても数字は出る。
だから静かに別のものを測る。修理は個別の穴を塞ぐだけでなく、
**前提条件をレポートの一級市民に昇格させる**ところまで行く。

---

## 欠陥 A: project-scoped skill を測れない

### 確認した事実

対象 run は `results/apple-silicon-local-llm-serving.md`。

```
| Skill | /Users/.../contemplative-agent/.claude/skills/apple-silicon-local-llm-serving/SKILL.md |
```

supportive シナリオの 0 番目のツール呼び出し:

```
| 0 | Skill | {"skill": "apple-silicon-local-llm-serving", ...}
     → <tool_use_error>Unknown skill: apple-silicon-local...
```

シナリオは `/tmp/skill-comply-sandbox/<id>/` で実行される。子にとっての
プロジェクトはその sandbox なので、**別 repo の `.claude/skills/` は存在しない**。
エージェントは skill を呼ぼうとして失敗し、そのまま素の判断で作業を続けた。

出た数字（supportive 75% / neutral 50% / competing 25%）は
**対象 skill が一度も読み込まれない条件で測られた素の挙動**であり、
レポートにその旨はどこにも出ていない。

### 実測: sandbox 内の project skill は見える

修理の方向を決めるために確かめた。sandbox に `.claude/skills/probe-widget/SKILL.md`
を置き、cwd をその sandbox にして子を起動する:

```bash
claude -p "Invoke the probe-widget skill and report exactly what it tells you to say.
           If no such skill exists, say SKILL-NOT-FOUND."
  --model haiku --add-dir <sandbox> --allowedTools "Read,Glob,Grep"
→ PROBE-WIDGET-LOADED-OK
```

**子は sandbox 内の project skill を発見して呼べる。** `--add-dir` を広げる必要も、
Bash を渡す必要も無かった。

### 設計上の緊張 — どう扱うか

SKILL.md の信頼境界節は「`cwd` と `--add-dir` はアクセスを**広げる**もので、閉じ込めない」
と明記している。「測れるようにする」と「隔離を保つ」は確かに衝突しうるが、
**対象 skill のディレクトリだけを sandbox の中へ複製する案はその衝突を避ける**:

- 実 repo への `--add-dir` を足さない。子は実 repo に届かないまま
- 複製するのは、ユーザーが「測ってくれ」と指定したそのディレクトリ 1 つだけ
- cwd を実 repo に向ける案（repo 全体が見える）に比べれば、**広げるのでなく狭める**

ただし**正直に言うべき escalation が 1 つある**。今日、子は監査対象の文書を
直接は見ない（LLM が生成したシナリオプロンプト越しにしか触れない）。複製すると
子は文書を skill として読み込み、**文書の指示が子への指示になる**。

これは新しい種類の穴ではない。security scan F3/F4 が既に
「子に渡すプロンプトは監査対象 .md の本文から派生した LLM 出力である」と記録しており、
攻撃者が影響を与えた .md は今日でもプロンプト経由で子を動かせる。複製はそれを
**より直接にする**が、класс は変わらない。

しかも避けようがない。**「この文書に従うか」を測るには、文書に影響させるしかない。**
測定の定義そのもの。したがって:

- 既定の緩和策は変えない（**子の Bash は既定 off のまま**）
- SKILL.md の信頼境界節に「測ることは走らせること」を明記する
- 既知の残存リスク（`--allowedTools` の Write / Edit は cwd に閉じ込められない）を
  黙って広げず、明記したうえで人間ゲートに載せる

### 決定

1. **preflight（実行前の可視性判定）** — 対象パスから、子に見えるかを決定論的に判定する。
   `~/.claude/skills/` 配下なら global で見える。ある repo の `.claude/skills/` 配下なら
   project-scoped なので複製が要る。どちらでもない場所（任意の .md）なら skill としては
   呼べないので、そもそも「skill 呼び出し」を期待しないことを明示する
2. **複製** — project-scoped と判定したら、その skill ディレクトリ**丸ごと**を
   `<sandbox>/.claude/skills/<name>/` へコピーする。参照ファイル
   （`references/`、スクリプト等）を skill が持つ場合があるためディレクトリ単位。
   コピー先は既存の `_contained` と同じ封じ込め判定を通す
3. **postflight（実行後の検出）** — トレース中の `Unknown skill: <name>` を
   決定論的に検出する。preflight の判定が外れても、ここで捕まる
4. **レポートに条件を出す** — Summary に「対象の種別（global / project / plain document）」
   「子から可視だったか」「skill 呼び出しが失敗した回数」を出す。
   **可視でないまま測ってしまった run は、スコアの隣に無効の印を付ける**
5. **可視化できないまま走らせない** — preflight が「呼べない」と判定し、かつ
   複製もできない場合は、15 分かけて無意味な数字を出す前に停止する

---

## 欠陥 B: setup_commands の契約が生成器と実行器で共有されていない

### 確認した事実

run の出力に `[setup refused]` が 6 回（3 シナリオ × 2 ファイル）:

```
[setup refused] "cat > .../requirements.md << 'EOF' ..."
                — only `mkdir`/`touch` inside the sandbox run
```

生成器プロンプトは「setup_commands should create a minimal sandbox
(dirs, **pyproject.toml**, etc.)」と、中身のあるファイルを作れと**書いている**。
実行器は `mkdir` / `touch` の 2 語彙しか解釈しない。**生成器は実行器の制約を知らない。**

結果、sandbox は空のまま（トレース中に `total 0` が 4 回）。エージェントは
測る対象が無い状態から始め、neutral シナリオでは**自分でフィクスチャを書き始めた**
（15,557 バイトの Write）。シナリオが意図した条件で実行されていない。

### 修理の方向

実行器を緩めて `cat >` を通すのは、2026-07-25 の security scan が閉じた
任意コマンド実行を開け直す行為。**信頼境界の設計は正しい。壊れているのは生成器側。**

守るべき不変条件を正確に言うと「**シェルを起動しない・プロセスを実行しない・
パスは sandbox 内に閉じる**」であって、「ファイルに中身を書かない」ではない。
`_apply_setup_commands` の docstring 自身が
「What the commands are actually for is creating directories and empty files,
and that needs no shell」と書いている。中身のあるフィクスチャが要るなら、
**コマンドとしてではなくデータとして渡せばよい**。

### 決定

1. **生成器に語彙を明示する** — 「dirs, pyproject.toml, etc.」という
   実行器が守れない案内を消し、許される形を正確に書く:
   `mkdir -p <相対パス>` と `touch <相対パス>` のみ。リダイレクト・ヒアドキュメント・
   パイプ・その他のコマンドは書かない
2. **フィクスチャの中身に安全な経路を新設する** — シナリオ schema に `files:` を足す。
   相対パス → 内容 の対応表で、pathlib で書き出す。プロセスは起動しない。
   既存の `_contained` を通し、絶対パスは拒否、サイズ上限と件数上限を置く。
   **「Nothing here executes a process」という性質はそのまま保たれる**
3. **拒否を一級の信号に昇格する** — 現状 `[setup refused]` は誰も読まない stderr 行。
   拒否件数を数え、レポートに出す。**フィクスチャが実体化しなかった run は
   測定品質の警告付きにする**

`files:` を足すことは信頼境界の緩和ではなく、**生成器が `cat >` に手を伸ばす理由そのものを
無くす**設計。緩めずに需要を満たす方向。

---

## 欠陥 C: detector が要求するツールを子が持っていない（本調査で発見）

対象 run の spec は 9 detector 中 **5 つが Bash を要求**する
（「Bash call to check available RAM」など）。一方 `DEFAULT_ALLOWED_TOOLS` は
`Read,Write,Edit,Glob,Grep` で **Bash は既定 off**。

この run はたまたま `--allow-bash` 付きで走っていた（トレースに Bash が 45 回）ので
実害は出ていない。しかし**付け忘れれば 5 つの step は構造的に検出不能**になり、
「実行しなかった」ではなく「実行できなかった」が 0% として出る。A・B と同じ型。

レポートには `--allow-bash` の有無がどこにも記録されていない。

### 決定

1. spec 生成後、各 detector が言及するツールと、子に渡す `--allowedTools` を突き合わせる。
   要求されているのに渡していないツールがあれば**実行前に警告する**
   （Bash が要るなら `--allow-bash` を促す。自動で付けない — 既定 off は意図的な設計）
2. レポートの Summary に**子に渡したツール一覧**を記録する

---

## D: 並列化と進捗（実装済み・未コミット）

先行して実装を終えている。内容は前版の plan どおりで、**A・B・C とは独立**。

- シナリオ 3 本を `ThreadPoolExecutor` で並列実行（`--concurrency`、既定 3、最小 1）。
  採点はもともとシナリオごとのループ内にあったので一緒に並ぶ
- 完了順はレポートに漏らさず、`scenario.level` 順に並べ直す（決定性の保全）
- 進捗を stdout → **stderr** へ。あわせて明示 flush
- sandbox の id 一意性を実行前に保証（並列では `shutil.rmtree` が兄弟を消すため）
- 子の異常終了 + トレース 0 件を `ScenarioExecutionError` に。0% と区別する
- ADR-0029、テスト 8 + 3 件追加（計 85 件 green）、ruff PASS

### 問題 2 の根本原因 — 切り分け結果（実測済み）

**仮説は半分当たり。観測された症状の原因は別だった。**

| 実測 | 結果 |
|---|---|
| `print("A"); sleep(3); print("B")` をパイプへ | 2 行が同時到着 = ブロックバッファされる |
| 同じものに `flush=True` | 3 秒差で到着 = flush で直る層は確かにある |
| flush 済み stdout を `tail -40` へ、同内容を stderr へ | stderr は t=0 / t=4 に即着、**stdout はプロセス終了後にまとめて到着** |

`tail -n 40` は `-f` なしだと「最後の N 行」を出す道具で、**定義上、入力が終わるまで
1 行も出せない**。`python -u` でも flush でも報告された症状は直らない。
直すのは stderr 化。flush はログ取り・バックグラウンド実行のために併せて入れた。

### D の扱い（判断を仰ぐ）

A・B・C とファイルが重なるのは `run.py` / SKILL.md のみで、競合はしない。
**先にコミットして着地させる**か、**A・B と同じ diff にまとめる**かを選んでほしい。

---

## 実装順序

1. **A**（測れない対象を黙って測らない）— preflight → 複製 → postflight → レポート記録
2. **B**（フィクスチャが実体化する）— 生成器の語彙明示 → `files:` 経路 → 拒否の可視化
3. **C**（ツール可用性の突き合わせ）— A・B のレポート拡張に相乗り
4. **D** — 着地済み。順序はユーザー判断

A と B は独立。片方ずつ着地してよい。

---

## 変更ファイル

| ファイル | 内容 | ゲート提示区分 |
|---|---|---|
| `scripts/runner.py` | skill の複製、`files:` の書き出し、拒否件数の返却 | 意図の要約 |
| `scripts/run.py` | preflight 可視性判定、postflight の `Unknown skill` 検出、ツール突き合わせ | 意図の要約 |
| `scripts/scenario_generator.py` | `files:` フィールドの取り込み | 意図の要約 |
| `scripts/report.py` | Summary に測定条件（対象種別 / 可視性 / ツール / 拒否件数）を追加 | 意図の要約 |
| `prompts/scenario_generator.md` | 語彙の明示、`files:` の書き方 | **本文を提示** |
| `SKILL.md` | 対象種別ごとの測定可否、「測ることは走らせること」、`files:` の契約 | **本文を提示** |
| `tests/*` | 下の検証節 | 意図の要約 |
| `docs/adr/0031-*.md` | 測定の前提条件をレポートの一級市民にする判断 | **本文を提示** |

`prompts/` と SKILL.md は振る舞いを形づくる資産、ADR は判断の正本なので、
`human-gate.md` に従いコミット前ゲートで**差分の本文を提示**する。
信頼境界に触れる変更（複製・`files:`）は**不可逆・高影響の昇格規則**にも該当するため、
区分によらず本文を出す。

---

## 検証

**A — 測定が成立していることを示す**

1. project skill を対象に実行し、トレースの 0 番目で Skill 呼び出しが**成功**すること
   （`Unknown skill` が消えること）。対象は今回の
   `contemplative-agent/.claude/skills/apple-silicon-local-llm-serving/`
2. 修理前後で同じ spec（`--spec` 固定）を使い、スコアが**変わる**ことを確認する。
   変わらなければ複製が効いていない疑い
3. わざと存在しないパスや skill 化されていない .md を渡し、preflight が
   実行前に停止すること
4. 複製後も子が実 repo に到達できないこと（sandbox 外の repo ファイルを
   Read しようとして失敗すること）

**B — フィクスチャが実体化すること**

1. `[setup refused]` が 0 件になること
2. sandbox に `files:` の内容が期待どおり書かれていること（`total 0` が消えること）
3. 絶対パス・`../` を含む `files:` エントリが拒否されること（封じ込めの回帰テスト）
4. `files:` の内容にシェルの記法が入っていても**実行されない**こと
   （プロセス起動が無いことの回帰テスト）

**C**

1. Bash を要求する detector を含む spec で `--allow-bash` 無しに実行し、
   実行前に警告が出ること

**D（実施済み）**

- テスト 85 件 green、`ruff format --check` / `ruff check` PASS、`.claude/verify.sh` exit 0

**Review** — `implementation-chain` の Chain Matrix に従い `feat` 相当。
python-reviewer + security-reviewer + codex-review を起動してから Verify に進む。
security-reviewer には**信頼境界に触れる 2 点**（sandbox への複製 = 監査対象文書が子への
指示になること、`files:` = 新しい書き込み経路）を明示的に見せ、
F2/F3/F4/F18 の対処が生きているかを確認させる。
