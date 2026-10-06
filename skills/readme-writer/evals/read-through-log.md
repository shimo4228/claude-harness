<!-- origin: shimo4228 -->
# 通読指摘数の記録（readme-writer の KPI）

最終判定の後に著者の通読が見つけた指摘の数。判定器の真のエラー率で、
`references/readme-judge-checklist.md` を直すときの主な入力。Workflow Step 7 で 1 行足す。

| 日付 | README | 最終判定 | 通読の指摘数 | 主な種類 |
|---|---|---|---|---|
| 2026-08-20 | contemplative-agent README.md / README.ja.md | EN / JA とも Publishable | 5（ほかに codex が事実誤り 5） | 事実の言いすぎ・不正確（repo の事実との照合が無かった） |
| 2026-09-25 | jev-skill-router README.md / README.ja.md（統合前の 3 agent 構成で判定） | fresh の最終判定 2 回とも Fix（毎回新しい文単位の指摘）。直してから通読へ | 未記入（著者の通読待ち） | — |
| 2026-09-25 | jev-research-pipeline README.md / README.ja.md（同上） | fresh の最終判定 2 回とも Fix（同上）。直してから通読へ | 未記入（著者の通読待ち） | — |
| 2026-10-01 | jev-skill-router README.md / README.ja.md（Jev で作る人向けに作り直し） | draft Fix → final Fix → recheck で EN / JA とも Publishable | 0（著者は通読して OK） | —（著者の指示で jev-research-pipeline への導線を途中で追加） |
| 2026-10-03 | harness-scope README.md / README.ja.md（新規、Rewrite） | draft Fix → recheck Publishable → final（JA だけ Fix）→ recheck で EN / JA とも Publishable | 0（著者は通読して GO） | —（通読後、別 session の計測で分かった「9 回中 1 回 Mod が読み込まれない」を Limitations に追記） |
| 2026-10-06 | shimo4228 hub README.md / README.ja.md（profile README、§V あり） | draft Fix（EN / JA。§V の V1・V2・V4 と主張の照合）→ recheck（§V すべて Yes）→ final EN Publishable・JA Fix（翻訳調 2 語）→ recheck。前後比較は両言語とも両順序で改稿後 | 0（著者は通読して GO。最後の recheck が拾った JA L9「正本」を著者が採って削った） | 見た目 0（push 後の live 実測で Start here は desktop の fold 内、mobile の表のはみ出しなし） |
