# ADR-0058: 執筆ハーネスの規約を短い原則へ戻す（足場溶解）

## Status

accepted

## Date

2026-08-28

## Context

Orwell "Politics and the English Language" (1946) の 6 rules を執筆規約へ取り込めないか、
という問いから始まった。監査の結果、**取り込むべき新規ルールはほぼ無かった** — 6 つのうち
4 つ（短い語 / 削る / 能動態 / 専門用語）は `writing-ecosystem` に既にあり、
`It's not X, it's Y` も `references/style-diagnostics.md` にあった。

差は内容ではなく書き方だった。Orwell のルールは短い原則で終わり、読み手が自分の原稿へ問いを
向ける余地を残す。既存規約は同じ内容を、例示・例外・判定手順・整合弁明・出自の日付で包んで
いた。最も鮮明な証拠が規約自身の中にあった — 改稿前の `writing-ecosystem/SKILL.md:216`:

> 「皆さん」の禁止だけでは、誰にも語りかけない中立解説文が通ってしまう（2026-08-20 著者指摘
> — 禁止形と機械検出だけが残り、読者へ語りかける側の指示が落ちていた）

短い原則を禁止形へ狭めた結果、意図が落ちた。その対処が**さらに 11 行足すこと**だった。原則を
復帰させれば禁止形と積極形の両方が導ける。

執筆系 15 ファイル（2,504 行）を監査したところ、問題は 3 種類あった。(1) 足場 — 原則に添えた
例示・例外・判定手順・整合弁明・出自の日付。(2) 複製 — 「ここに複製しない」と宣言しながら
複製している箇所（4 skill 中、宣言を守れていたのは `prose-translation` のみ）。(3) 実害 —
複製が drift して規約が食い違う、存在しない保証を主張する、canon 自身の規約に違反する。

`skills.md` が配線する `skill-creator` は「目安 100 行」を規定している。改稿前の
`writing-ecosystem` は 438 行、`editor` 270 行、`collect-context` 275 行だった。

## Decision

1. **Craft 規約を短い原則の列へ戻す。** 各行は原則 1 文 + 自分の原稿へ向ける問い 1 句で終える。
   Orwell ルール 1（見慣れた比喩）を**禁止形のみ**で追加する（「新しい比喩を作れ」は原文に
   なく、拡大解釈）。ルール 6 に相当する例外条項を末尾に置く — 守った結果、文が不誠実になる・
   回りくどくなる・言いたいことが消えるなら、規約の方を破る。

2. **層を分離する。** 原則は skill 本文、検査項目と数値閾値は判定を出す agent、直し方の実例は
   `references/`。段落密度と初出説明の閾値は `prose-clarity-reviewer` へ、専門用語の緩和策と
   発見調の register は `style-diagnostics.md` へ移した。

3. **B（足場）と D（検査項目）を分けて畳む。** Orwell のルールは書く人向けで検査者向けでは
   ない。reviewer agent の具体性は findings の解像度を作るので抽象化しない。畳むのは例示・
   例外・判定手順・整合弁明・出自の日付だけ。

4. **実測由来の拡張も畳む。** 短い原則が実際に失敗して足された文言（語りかけの積極形 11 行）
   も原則へ戻す。失敗の原因が「原則を禁止形へ狭めたこと」なので、拡張ではなく原則の復帰で
   直る（2026-08-28 著者裁定）。

5. **複製は正本 1 つへ統合する**（ADR-0010 と同じ — 揃えない、削除する）。`editor` と
   `essay-reviewer` の Output Format 約 55 行 × 2 は `skills/writing-ecosystem/references/review-output-format.md`
   へ、README の造語予算・参照規律は `readme-judge-checklist.md` へ、初出説明は
   `prose-clarity-reviewer` へ寄せた。

6. **「三段階の問い構造」を削除する**（2026-08-28 著者裁定）。主根拠は冗長 —「結論の問い化」
   節が同じ内容を確度の話として既に持つ。第 3 段「議論途中の修辞的疑問」は
   `style-diagnostics` の「同じ結論を疑問形で繰り返さない」および zenn-content の Zenn
   register とも衝突していたが、channel を主根拠にすると channel が canon を変形させる形に
   なるため副次的な根拠として扱う。

7. **溶解の過程で露出した境界矛盾を同時に直す。** fresh-context の草稿ゲートが verdict `Fix` と
   ともに 4 件を指摘した — (a) 冒頭行が Voice を自分の正本と宣言しながら本文は channel contract
   に委譲していた、(b)「規範の正本」を名乗る Title Conventions が `headline-craft` の生成技法を
   3 行複製していた、(c) `Final structural pass` 5 項目のうち 3 項目が同じ phase で走る
   `prose-clarity-reviewer` の検査項目の再掲だった、(d) AI 開示が channel policy なのに global で
   無条件に宣言され、zenn-content が contract 側で carve-out を書く羽目になっていた。
   加えて退役済みの節名 `Banned Patterns` を指す inbound pointer 2 件と、内部アンカー 1 件の
   slug 不一致を修正した。

## Review-when

- 溶解後の reviewer が findings の解像度を落としたと著者が感じたとき。その項目は B ではなく
  D だったということで、判定側へ復帰させる
- 短い原則が再び「禁止形だけ」と読まれて穴埋めの subsection が生えたとき。Decision 4 の前提
  （原則の復帰で直る）が誤りだったことになる
- モデル世代交代で、原則からの敷衍が今より効くようになったとき（`akc-cycle.md` の downward）

## Alternatives Considered

- **Orwell の 6 rules を新規ルールとして追加する。** 却下 — 監査で 4 つが既存と重複し、残り 2 つ
  も既存原則の系だった。追加は規約の肥大にしかならない。
- **長い記述を一律に短くする。** 却下 — reviewer agent の実例列挙（`prose-clarity-reviewer` の
  「冒頭の摩擦」「前述の問題」）は grep 可能な検出語で、抽象化すると検出不能になる。
  `fact-checker` の transcript 禁止の機序も、`security.md` が agent 定義を「実行される制御
  プログラム」と定義する以上、禁止の自己執行力そのものなので残す。
- **実測由来の拡張だけ残す。** 却下（著者裁定） — 最も肥大した節が手つかずで残る。

## Consequences

- 執筆時に読む層が短くなり、原則が問いとして働く。`writing-ecosystem` 438 → 378 行
- 検査項目が判定を出す側へ集約され、canon を変えても agent 側の目次を追随させる必要が減る
- 一方、閾値が skill 本文から見えなくなった。著者が「1 段落何文まで」を知りたいときは
  `prose-clarity-reviewer` を開く必要がある
- `editor` / `essay-reviewer` が共有 reference に依存する。片方だけの出力変更ができなくなる
- 縮約が定義を狭める事故が 1 件起きた。`editor` の severity 行を縮めた際、「contract が名指しする
  規約は CRITICAL のまま扱う」を「contract が名指しする規約**だけ**が CRITICAL」に変えてしまい、
  canon の CRITICAL 定義（読者への約束・事実・中心命題を壊すもの）と別定義になった。草稿ゲートが
  検出し、両 agent を canon へのポインタに戻した。**畳むときは、原文が何を許していたかを確かめる**
