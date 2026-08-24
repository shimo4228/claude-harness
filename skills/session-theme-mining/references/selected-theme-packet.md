<!-- origin: shimo4228 -->
# Candidate Card and Selected Theme Packet

## Candidate Card

```markdown
### <candidate-id> — <question>

- Discovery route: repeated friction | cross-repo connection | change/tension
- Human anchor: "<verbatim quote>"
  - Harness / session / timestamp: <claude|codex> / <id> / <ISO-8601>
  - Raw path: <path>
- Independent support: <separate parent session | commit diff | live measurement>
  - Source: <path, commit, or command + as-of date>
  - Verification: <what was directly checked>
- Scope: <repos and date range>
- Publication overlap: <none | existing piece + concrete new delta>
- Missing evidence: <none or explicit gap>
- Proposed collection scope: <repos, dates, keywords>
```

候補は 0〜3 件。score、順位、推薦、記事タイトルは付けない。

## Candidate History JSON

著者の判断後、候補ごとにこの JSON を scratch file として作り、`history-record --input` に
渡す。`evidence_ids` は最低 2 件で、Human anchor と Independent support の安定 ID を入れる。

```json
{
  "candidate_id": "stable-kebab-case-id",
  "question": "候補カードと同じ問い",
  "evidence_ids": [
    "claude:<session-id>",
    "commit:<full-or-short-sha>"
  ],
  "status": "selected"
}
```

`status` は `selected` / `held` / `rejected` のいずれか。

## Coverage Receipt

```yaml
coverage:
  discovered_parent_sessions: <n>
  selected_sessions: <n>
  harnesses: [claude, codex]
  date_range:
    oldest: <ISO-8601>
    newest: <ISO-8601>
  repos_seen: <n>
  parse_warnings: <n>
  malformed_json: <n>
  line_too_large: <n>
  discovered_files: <n>
  source_bytes: <n>
  read_errors: <n>
  cache_write_errors: <n>
  skipped_byte_budget: <n>
  sampling:
    recent_days: 90
    recent_limit: 100
    legacy_limit: 30
    seed: 0
  missing_evidence: []
```

## Selected Theme Packet

著者が選んだ候補 1 件だけを次の形にする。同じ会話内の `collect-context` に渡し、tracked
file として保存する必要はない。

```yaml
selected_theme_packet:
  question: <selected question>
  selected_at: <ISO-8601>
  collection_scope:
    repos: []
    date_ranges: []
    keywords: []
  sources:
    - harness: <claude|codex|git|live>
      id: <session-id|commit|measurement-id>
      raw_path: <path or null>
      timestamp: <ISO-8601 or null>
      role: <human-anchor|independent-support>
      verification: <directly checked fact>
  publication_overlap:
    existing: <source or none>
    new_delta: <concrete delta>
  unresolved: []
  coverage: <copy of coverage receipt>
```

packet 自体を一次証拠として引用しない。`collect-context` は `sources` を開き直して検証し、
著者がこの問いを選んだ事実だけを本セッションの Judgment Record に残す。
