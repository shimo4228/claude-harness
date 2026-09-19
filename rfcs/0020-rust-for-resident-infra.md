---
state: done 2026-09-06
review-when: Rust pilot が 1 件完走して運用感の実測が出たら本 RFC の発火条件を再評価。または python3 同梱前提が macOS 側で崩れたら緊急度を引き直す
---
## Summary

harness 常駐 infra（hook・daemon・parser 類）の言語既定を、既存の Rust 移行でなく「次に新しく作る常駐道具から Rust で書く」greenfield pilot 方針とし、既存移行は発火条件つきで待機させる。

## Motivation

LLM-first code 前提（rule: `llm-first-code.md`）での言語評価は 4 軸 — 訓練コーパス / 機械検証の密度 / フィードバックループ速度 / 正準形と toolchain 一体性。Rust は検証密度で圧勝し、その嬉しさは「無人・常駐・長寿命」の性質から来る: (1) silent failure（None・型不一致・エラー処理漏れ）がコンパイル時にバグクラスごと消える (2) 単一バイナリで実行環境 drift が消える (3) hook レイテンシが 50–100ms → 数 ms (4) 次の LLM 編集者へのコンパイラフィードバックで build セッションの bounce が減る（未実測の仮説）(5) 仕様が型に載る分、保存すべきテスト・golden が縮む。

一方で既存移行を今やらない理由: テキストだけの repo + 同梱 python3 で完結している harness に cargo/rustup という build 依存が新規に入り（依存の逆転）、silent failure の実事故は fail-closed 設計 + bats 425 本 + golden 凍結層（2026-08-31 導入）で塞いだ直後で痛みのシグナルが無く、実害ゼロの動くものの書き直しは Build-or-not が弾く形。greenfield なら既存挙動との等価性検証という最大コストを背負わずに toolchain コストと bounce 仮説を実測できる。

## Guide-level explanation

- 既定: 一回きりの script・探索コード・プロンプト主体の pipeline は従来どおり Python
- 新規の常駐道具（hook 実装・daemon・parser・整形層）を作る機会が来たら、Rust で書くことを第一候補として検討する（強制ではない — search-first と Build-or-not は通常どおり通す）
- 既存 infra（claims.py 等）の移行は下の発火条件が立つまでやらない

## Reference-level explanation

発火条件（いずれかで該当部分を再評価）:

1. Python infra で silent failure の実事故が再発 → その道具から個別移行を検討
2. 新規常駐道具の機会 → Rust で書き、それを pilot とする（toolchain コスト・bounce 率・運用感を実測）
3. pilot の実測が良好 → claims.py 級の既存移行を再検討。その際も一括でなく module 単位、golden 凍結層を等価性検証に使う（移行自体が「仕様＋検証だけから再生成できるか」の spec 完備性テストになる）

## Drawbacks

- cargo/rustup が Mac 環境の新規依存になる。バイナリは commit できず build step が verify / bats の前提に入る
- Rust の訓練コーパスは Python 比で一桁小さく、生成品質の差は残る（世代ごとに縮小中 — 相場観、as-of 2026-08-31）

## Rationale and alternatives

- 即時全面移行: 等価性検証コスト最大・痛みシグナル無しで棄却（本セッションの議論）
- 現状維持（Rust を検討しない): 常駐 infra の silent failure クラスと hook レイテンシを恒久的に受容することになる。発火条件つき待機の方が安い
- TS: 検証密度・toolchain 一体性のどちらでも首位を取れず、platform が web を強制するときのみ

## Prior art

- 2026-08-31 の lint LLM-first 棚卸しと golden 凍結層導入（`.claude/verify.md` 同日付節）が本方針の前提
- Contemplative Agent の全面 Rust 移行案は同議論で「複雑性がプロンプト側にあり効く面積が 2〜3 割」として優先度を下げた

## Unresolved questions

- bounce 減（嬉しさ 4）は未実測の仮説。pilot で測る
- pilot の計測項目の最小セット（toolchain セットアップ時間 / build セッション bounce / hook レイテンシ実測）

## Status

done 2026-09-06 — pilot 完走。hooklint（commit ab88358）+ ADR-0063（n=1 計測値、size 上限 600 の引き直し）。claims: RFC-0020 は 2026-09-06 01:33 UTC に outcome done で release 済み。方針（greenfield Rust + 発火条件つき待機）は本文がそのまま公開記録として残る。review-when「pilot 1 件完走で発火条件を再評価」は発火したが、発火条件 3（既存移行）の再評価は ADR-0063 Review-when の「2 件目の pilot 読み値があるか」を先に問う規定に従い、著者判断（triage cycle 2026-09-13 で state のみ更新、ADR-0063 L94 の管轄指定に従う）。

（旧 Status: accepted 2026-09-06 — **著者が発火条件 2（新規常駐道具の機会）を能動的に立てる判断をした**。Fable セッションを立てて Rust 実装のプランを起こす（plan mode、`.claude` cwd）。

（旧 Status: draft 2026-08-31 — 方針は著者合意済みだが着手可能な作業項目は無く、ready に載せないため draft のまま置いていた。採否は済んでいるのに `draft` を表示挙動のために使っており、語彙の定義と食い違っていた点は 2026-09-06 の triage が指摘。着手判断で解消した）

## Next action

プラン用の Fable セッションが本 RFC を claim し、pilot 対象（どの常駐道具を最初に Rust で書くか）とUnresolved questions の計測最小セット（toolchain セットアップ時間 / build セッション bounce / hook レイテンシ）を決める。プランが固まったら実装は build-tier へ dispatch。
