---
state: done 2026-08-29
review-when: substrate が skill listing の注入方式を変えた時（RFC-0017 と同一）。または善意 description の干渉効果量を直接測った研究・計器が得られた時
---
## Summary

skill description を「常駐コスト（字数）」でなく「挙動汚染（第 2 の rules 層）」として検査・撤去する軸を立てる。

RFC-0017 は description 撤去を字数削減として正当化したが、著者の実際の危惧は別にある: description は system prompt に常駐してモデルの挙動を変える**未監査の指示層**であり、rules は rules-stocktake が監査するのに description 内の指示文（NOT for ルーティング、「Use PROACTIVELY」型の発火指示）は誰も監査していない。本 RFC はこの軸の検査と撤去基準を扱う。

## Motivation

外部知見の検索時点照合（2026-08-29）で、「description は listing に載っているだけで挙動を変える」ことを支持する 4 本の線が揃った:

1. **経路は仕様**: Agent Skills の progressive disclosure では name + description が起動時に system prompt へ常時ロードされる — rules と同じチャネル（[Anthropic docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)）
2. **invoke されなくても挙動を変えることは敵対的設定で実証済み**: MCP-ITP（[arXiv:2601.07395](https://arxiv.org/abs/2601.07395)、2026-01）は毒性ツールが一度も呼ばれないまま description の文脈操作だけで agent を別ツール呼び出しへ誘導、12 モデル・548 ケースで最大 84.2% ASR。OWASP も [MCP Tool Poisoning](https://owasp.org/www-community/attacks/MCP_Tool_Poisoning) を攻撃分類として登録済み
3. **指示文でなくても常駐テキストは性能を劣化させる**: 無関係文脈の distraction（GSM-IC, ICML 2023 / GSM-DC, [EMNLP 2025](https://aclanthology.org/2025.emnlp-main.674/)）、Contextual Entrainment（[arXiv:2606.24077](https://arxiv.org/pdf/2606.24077) — prompt に現れた token は関連性と無関係に生成確率が上がる）
4. **ベンダー自身が description を挙動レバーとして扱う**: Claude Code docs は自動委譲を促すために description へ「Use PROACTIVELY」「MUST BE USED」と書くことを推奨 — description は documentation ではなく trigger（[subagent docs](https://code.claude.com/docs/en/sub-agents)）

harness 側の観測と合わせると: 「invoke 0 / read あり」の skill 群は、望んだ挙動（自発選択）を 79 日間産まず、上記 2・3 の経路で未測定の干渉だけを常駐させている — 期待値の非対称。

## Guide-level explanation

採用された場合の変化:

- **撤去判断の根拠が変わる**: 「字数が浮くか」でなく「この常駐文はどの挙動を狙い、実測でその挙動を産んでいるか」を問う。産んでいない description は干渉のみの純負債として撤去候補になる
- **1 行 description（RFC-0017 の手段 B）の位置づけが下がる**: 挙動汚染の観点では 1 行でも常駐は常駐（Contextual Entrainment は token 単位で効く）。到達経路を明示配線で作った上での `disable-model-invocation`（手段 A）が既定になる
- **残す側の description も検査対象になる**: 撤去しない skill の description 内の指示文（NOT for ルーティング、発火指示、他 skill への言及）を「常駐指示」として棚卸しする — rules-stocktake が rules に対して行う監査の description 版

## Reference-level explanation

検討する検査項目（機構化の要否は Build-or-not で判定）:

1. **指示文の抽出**: description から命令形・ルーティング指示（NOT for → X、「必ず」「Use PROACTIVELY」相当）を列挙し、「この指示は listing に常駐する価値があるか、body / rule に降ろせるか」を問う。semantic なので stocktake 系の問いに載せる形が素直
2. **狙いと実測の照合**: description の狙い（自発発火）と usage_stats の実測（invoke 数)を突き合わせる — RFC-0017 の residency-fold 列挙と同じ計器で足り、読み方だけが変わる
3. ~~**B 案の再検討**: RFC-0017 で B を割り当てた skill（`ai-native-preprint-submission`）を A + 明示参照の追加へ振り替えるか~~ — **前提消滅（2026-08-29）**: RFC-0017 の実施で B 適用は 0 本、`ai-native-preprint-submission` は手段 D で paper-lab へ移設済み（global に存在しない）。B 案の格下げ自体は skill-health の判断軸更新として実施

## Drawbacks

- **効果量が未測定**: 敵対的最適化された文章での 84.2% は善意 description の干渉量の上界ではあっても推定値ではない。「劇的に良くなる」根拠はまだ無い
- 撤去しすぎると自発発火に実際に効いている description（invoke > 0 の側）の trigger surface を巻き込みうる — 検査対象は狙いと実測が乖離したものに限る
- RFC-0017 と対象が重なるため、二重の台帳になるリスク。RFC-0017 は「今回の 15 本の 1 回の編集」、本 RFC は「軸の恒常化と残る description の監査」と切り分ける

## Rationale and alternatives

- **RFC-0017 に統合する**: 却下 — 0017 は accepted 済みの字数軸で、今回の実施はその根拠で完結する（著者判断 2026-08-29: 挙動軸は別 RFC へ）
- **何もしない**: distraction / entrainment の知見上、常駐指示は増えるほど干渉するが、善意 description での効果量が未測定な以上「まず測る」が対抗案として残る
- **rules-stocktake を description へ拡張する**: 検査の型（意図 / 根拠 / 鮮度 / 失効条件）は流用できるが、rules と description は正本の場所も編集経路も違う。拡張か新設かは採用時に判定

## Prior art

- RFC-0017（字数軸の先行。手段 A/B/C と到達経路の判断軸はそのまま流用できる）
- rules-stocktake（常駐指示の監査の型）
- `.notes/s1-skill-count-audit-2026-08-29.md`（invoke 0 / read あり群の実測）
- 外部: Motivation の 4 本（as-of 2026-08-29）

## Unresolved questions

- 善意 description の干渉を harness 内で測る計器を持てるか。2026-08-29 の調査: skill-comply の Tier 1（description だけ本物・body は stub）+ sandbox への skill 注入（`runner.place_skill`）で「listing に足す方向の A/B」の足場は既にある。ただし (a) global listing から 1 本だけ抜く制御口が無い、(b) 干渉測定は「無関係な課題での挙動変化」なので spec/grader の意味づけを作り直す必要、(c) scenario の非決定性ゆえ反復回数の設計が要る — 実質新計器 build なので建てない（著者判断 2026-08-29、下の Status）
- 「description 内の指示文」の抽出は regex（構造）か LLM（意味）か — feedback_regex_vs_semantic の区別で言えば意味的分類寄り
- name だけの listing 残置（description 撤去後）にも entrainment はある — 名前ごと消す A と name 残しの線引きをどこに置くか

## Status

draft 2026-08-29 — RFC-0017 のセッション中に著者の危惧（description = 第 2 の rules 層）から分離起票。外部知見の照合済み、採否判断は未。

accepted → 実施 2026-08-29 — 著者判断: **配線のみ・A/B 計器は建てない**（RFC-0017 と同じ「新規機構は建てない」。Build-or-not 自答はプラン `plans/rfc18-sleepy-cosmos.md` に記録）。実施内容:

1. `skills/skill-stocktake/SKILL.md` — Stage 1 に 6 問目 **Description audit**（常駐指示文の semantic 抽出、usage との join は parent の Phase 4）+ Phase 4 に join 規約（狙いを実測が裏づけない指示文のみ撤去候補、効いている trigger surface は巻き込まない）
2. `skills/skill-health/SKILL.md` — Phase 3 residency-fold の判断軸を反転: A + 明示参照が既定、1 行 description は参照先が無い場合の次善（1 行でも常駐は常駐 — entrainment は token 単位）
3. `skills/skill-creator/SKILL.md` — §3 に挙動汚染の根拠 1 行（予防側）
4. 検査項目 2 は既存 `usage_stats.py` の読み方変更で充足（新規計測なし）、検査項目 3 は前提消滅（上記注記）
5. 初回監査パス（listing 掲載 42 本、窓不足 3 本除外）を同日実施 — confirm-each で著者承認:
   - A 適用 4 本（いずれも明示参照あり・slash 温存）: `session-judgment-mining`（deliberate 0/79d）、`agent-stocktake`（invoke 0）、`generation-audit`（invoke 1、rule akc-cycle.md の命令形が入口）、`harness-boundary`（invoke 1、implementation-chain 本文が入口）
   - 指示降格 1 本: `tdd` — description の NOT for 4 件を body の正本表へ降ろし trigger 文のみ残す
   - 見送り: `herdr` の抑制文削除（rules/common/agents.md:10 と重複するが著者判断で温存）、`review-to-lint`（RFC-0017 の意図的除外を維持、次回再判定）。invoke 1〜3 の低頻度作業系（public-comment 等）は「稀な作業の自然言語入口」で乖離なし

## Next action

なし（恒常運用へ。次回 skill-stocktake / skill-health 実行時に 6 問目と新判断軸が回る）。測定計器は Unresolved に足場の調査結果を残した — 干渉効果量を測る必要が生じたら再起票。
