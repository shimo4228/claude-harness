---
state: accepted 2026-09-14
review-when: "影の比率（直近 60 日の transcript で、WebSearch か外部調査 subagent を使ったセッションのうち search-first を通らなかった割合。基準値 2026-09-14: 133 / 142 = 93.7%、手順は `.notes/search-first-shadow-baseline-2026-09-14.md`）を 2026-11 に取り直し、下がっていなければ「発火しない原因は trigger surface」の仮説が崩れたとして本エントリを再読する"
---
## Summary

search-first の verdict が package 一軸（Adopt / Extend / Compose / Build）で harness ではほぼ Build に落ち、見つけたものから学んだことを運ばない — 出力を報告に替え、受ける問いの種類を description に置き、scout を退役する。

## Motivation

著者の観察（2026-09-14）: ① なかなか発火しない ② 発火しても「プロジェクトにそのまま適用できない」と却下されることが多い ③ 探索範囲が制限列挙型（repo → レジストリ → MCP → skill → OSS）なのが良くない。ごく初期からの skill だが有効に機能した実感がない。

実測（harness の skill usage 計測 jsonl、2026-09-14 集計）: invoke は 6 月 6 / 7 月 14 / 8 月 8 / 9 月 0（14 日時点）。read は 8 月に 2 へ急減。agent `scout` の起動は累計 18。

構造的原因: `skills/search-first/SKILL.md` の verdict 表は「install できる package があるか」の一軸で、この harness は skill / rule / ADR でできているので問いはほぼ常に Build に落ちる。Build 判定は「見つけたものから何を学んだか」を運ぶ出力欄を持たない。②「適用できず却下」の実体はこれ。①は description の trigger surface が「add X functionality / what library」型の発話例しか持たず、harness で実際に出る問い（先行実装はあるか、この論文の主張は当てはまるか、公式は何と言っているか）に一致しないことの帰結。発火率は独立の knob ではない。

外部レビュー（Codex gpt-6-astra、2026-09-14、R&D 再設計の面接に対する意見）: 「search-first 強化は、面接で捨てた案の中で最も明確な需要証拠を持つ。ただし問い発見の代替ではない」。R&D 再設計そのもの（問い発見のループ）は別に扱う。

## Guide-level explanation

利用者は build セッション（Phase 0）と著者。search-first は外部に何があり、こちらの条件とどう違うかを**報告**し、判断（採る / 部分的に採る / 採らない）は呼び出し側が行う。そのまま使えるのは稀で、部分採用が成果。受ける問いは 6 種（library 選定 / 先行実装 / 論文・post の主張 / 仕様・公式挙動 / 状況の俯瞰 / 原典照合）+ 「外部に答えがありうる問い全般」の総称句。

## Reference-level explanation

- **報告契約**（verdict 行の後継）: `Scope searched`（検索語・source・as-of、見つからなかった範囲）/ `Found`（1 件ごとに 何か・対象と前提・根拠の種別・こちらとの相違・移せる部分）/ `Still unknown`。書き方の規則（全 claim に as-of と出所、不在は範囲付き、snippet と本文の区別、主張に対象・前提・相違）は skill 本文が持つ。rule には置かない — 常駐すると全文脈に当たり不自然（著者判断 2026-09-14）
- **種類別の表**: 探索先 / 証拠として数えるもの / 止め方。種類はゲートでなく手掛かり
- **委譲**: Full Mode は general-purpose subagent に tools を Read / Grep / Glob / WebSearch / WebFetch に絞って渡す（web 由来コンテンツを shell 持ちの agent に読ませない）。`agents/scout.md` は退役 — 直近 8 呼び出し全部で呼び出し側が scout の report 雛形を無視して完全な prompt を書いており、固有価値は general-purpose と同じだった
- **配線は維持**: `rules/common/planning.md`、`skills/implementation-chain/SKILL.md` Phase 0 行（早期停止条件は「報告に実装方針を変える既存解が含まれる → 再 plan」）、`skills/rfc-writer/SKILL.md` §2（結果 → Prior art）、`skills/verify-bootstrap/SKILL.md`（報告を受けたら採用条件を確認）、`rules/common/knowledge-staleness.md` の名指し
- 決定の記録: ADR-0066。ECC 版 search-first（PR #262）とは分岐（ADR-0006 で貢献終了済み）

## Drawbacks

library 選定の決定性（1 行で Adopt / Build が読める）は失う。呼び出し側が報告を読んで判断する分、Quick Mode の軽さは 1 段落分重くなる。

## Rationale and alternatives

- (a) verdict 表を維持し Build 行の下に「学び」欄を足す — 二値が学びを捨てる構造は残る
- (b) search-first を退役し、書き方の規則 3 行を knowledge-staleness rule へ移す — 3 行は verdict の二値への対策であって verdict が無ければ対象が無い。常駐 rule に置くと全文脈に当たり不自然。rule が skill を名指ししており指す先を残す方が筋（著者判断 2026-09-14）
- (c) scout を opus に上げて残す — 呼び出し側が雛形を無視している実測に反する
- (d) 何もしない — 減衰を受け入れる

## Prior art

一次資料（raw 本文を読んだ、2026-09-14）から本設計に持ち込んだもの:

- [HumanLayer research_codebase](https://github.com/humanlayer/humanlayer/blob/main/.claude/commands/research_codebase.md)「DOCUMENT WHAT IS, NOT WHAT SHOULD BE」— 調査者は記述し、判断は呼び出し側（報告契約の根拠）
- [K-Dense hypothesis-generation](https://github.com/K-Dense-AI/scientific-agent-skills/blob/main/skills/hypothesis-generation/SKILL.md) の dated evidence boundary — 不在は「探索範囲内で見つからなかった」と範囲付きで書く
- [Open Deep Research](https://github.com/langchain-ai/open_deep_research)（archived、最終 push 2026-08-10）の `prompts.py` — 停止条件（独立 3 源 / 直近 2 検索が同内容 / call 上限）。Full Mode の予算（約 15）の出所
- 外部 deep-research（Codex、2026-09-14、著者依頼）が挙げた執筆規則のうち一次資料に遡れるもの — 主張と原典の対応（ALCE, EMNLP 2023）、snippet と本文確認の区別（Verification Handbook ch.2）、source の主張 / 分析推論 / repo 含意の区別（ICD 203）、「次の検索が何を解決するか言えなくなったら止める」（Pirolli 2007 の information foraging）

実測（transcript 走査、2026-09-14）:

- search-first / scout を通った直近 8 件の問い: library 選定 2 / 先行実装 4 / 仕様 1 / 状況の俯瞰 2（重複あり）。8 件全部で呼び出し側が自前 prompt に「as-of 日付・一次ソース・報告せよ」を書いていた — 報告契約は現場の使い方を skill に書いたもの
- 直近 60 日の transcript 979 本のうち外部調査をした 142 のうち skill を通らなかった 133（影の集団、93.7%。述語固定の手順は `.notes/search-first-shadow-baseline-2026-09-14.md`）: 5 種に収まらない塊が **原典照合**（主張・引用・数値を一次資料が本当にそう言っているか）。受けるべきでない塊はトラブルシューティング / how-to と repo 内調査（description で別入口へ routing）

## Unresolved questions

（解消済み）① 発火は配線でなく description の trigger surface で扱う ② 探索範囲は 6 種 + 総称句 ③ R&D 側の 5 部とは同型にしない — 報告は比較の材料で、判断は呼び出し側

## Status

accepted 2026-09-14 — skill 改修・scout 退役・消費者 6 ファイルの書き換えを実施。fresh-context 草稿ゲートと行動 gate の結果は ADR-0066 Decision 9 が持つ。

## Next action

影の比率の再測定（2026-11）。手順・述語・基準集合（分母 / 影のセッション一覧）は `.notes/search-first-shadow-baseline-2026-09-14.md` に固定してある — 同じ snippet を実行し、基準値と比べる。
