<!-- origin: shimo4228 -->
<!-- rationale: 2026-08-31 の mondo →実装で確立した前提。コードの読者・編集者・レビュアーは次セッションの LLM で、この読者への最適化が品質基準になる。全 lint 選定・テスト設計・可読性投資の上流にあるため常駐層に置く。当初の否定形（人間は読まない）は手抜きの誤読余地があり、同日中に要求形へ書き直した。指示文の肯定形規約（ADR-0070）は読者が LLM であることの帰結なのでここに置き、範囲を harness 外の repo の CLAUDE.md・行動指針 doc・ADR まで広げた（2026-10-11 著者指示） -->
<!-- review-when: 人間がコードを直接読む運用が復活したら。またはモデルが persistent memory / 実質無限 context を持ち「context 制限つきの次の編集者」前提が崩れたら（generation-audit で再監査） -->

# LLM-First Code (LLM 可読性を最優先する)

コードの読者・編集者・レビュアーは**次セッションの LLM**。この読者に最適化することが
品質基準そのもの。人間可読性が目標から外れるのは基準の引き下げでなく**読者の交代**で、
LLM 読者はしばしば人間より容赦ない — 曖昧・巧妙・肥大したコードは次の編集で bounce に
なって返ってくる。人間が読むのは **README と出力の文面**だけ（2026-08-31 著者確認）。

- **LLM 可読性の中身**: locality（context に収まる自己完結）> 深い抽象、明示 > 巧妙、
  型と invariant コメントは beacon。測る物差しは認知負荷でなく **context 経済**
- **可読性は保存しない、検証可能性を保存する。** 説明は必要時に LLM が生成できる
  （derived）。都度生成できない型・テスト・golden が保存層
- **基準の執行者は人間の目でなく機械ゲート。** lint / type check の選定は LLM-first
  4 軸（バグクラス / 正準形 = diff 安定 / 予算 = 編集信頼性 / 境界の明示型強制。
  人間美学系は select しない）— 正本は skill: `verify-bootstrap` Step 2。ゲートを通らない
  ものは誰も読まなくても不合格
- **出力こそ守る対象。** 機械が parse する出力の silent drift が最大の未検知リスク —
  golden 凍結層と更新規律の正本は harness の `tests/golden/README.md` と
  skill: `implementation-chain` の Doc Sync 行
- **人間可読性の予算は README と出力の文面にだけ払う**（readme-writer の投資はこの
  前提の帰結）。ADR・テスト・commit message は LLM 読者向けに最適化する — 密で
  自己完結、文脈を全部持つことが美文より優先
- **指示文は肯定形で書く。** 対象は LLM が従う文書すべて — harness の skills / agents /
  rules / output-styles、各 repo の CLAUDE.md・AGENTS.md・行動指針の doc、ADR の
  Decision / Review-when / Consequences。判断基準と罠を書き、やめる項目は本文から消す —
  名指しした「するな」は選択肢として想起される。禁止を書けるのは、対象が grep 可能な
  具体的動作で、既定挙動が逆だと観測されていて、機械ゲートが無いときだけで、理由を
  1 句添える。文体・内部過程への禁止は肯定形に言い換える。外部由来の未改変 prompt と、
  ADR の Context / Alternatives（事実と却下の記録）は写しのまま置く。既存の文書は触れた
  ときと棚卸し（skill: `context-sync` / `rules-stocktake`）で直す。正本は
  skill: `skill-creator` §3（ADR-0070）
