<!-- origin: shimo4228 -->
<!-- rationale: ADR-0035 — model が内面化した debug 手順を退役し、2026-07-16 に実証した platform 固有 signal だけ保持 -->
<!-- review-when: platform が rate-limit と policy enforcement を明確に分離した時 -->
# Rate Limit Signal

外部 platform への大量書き込み中に rate limit が連発したら、transient error ではなく
policy signal と扱って burst を止める。2026-07-16、継続後にアカウント無期限 block と
全作成物削除が発生した。backoff で踏み抜かず人間へ報告する。
