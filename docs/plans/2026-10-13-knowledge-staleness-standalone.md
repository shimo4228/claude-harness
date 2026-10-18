kind: external
# Should the knowledge-staleness rule ship as a standalone English repo (rules file + Claude Code plugin with SessionStart hook, bundled `claude plugin eval` results, awesome-list submissions), and how?

As-of 2026-10-13. Five angle notes (prior-art, awesome-lists, hook-delivery, rule-eval, adversarial) in `~/.cache/claude-research-notes/2026-10-13-knowledge-staleness-standalone/`, plus lead-verified local facts (L1-L5 below). Author constraint: rule text stays short; caveats go to eval cases, README, hook implementation.

## Scope searched
- Web search and fetch (about 45 calls across the notes): prior art for staleness rules, context7, date-injection hooks, memory/decision expiry tools, Claude Code hooks/memory/plugin/plugin-evals docs, superpowers hook source, awesome-list CONTRIBUTING files, Claude system prompt, over-searching and instruction-count papers, FreshQA.
- Lead-verified (local / gh, 2026-10-13):
  - L1. Claude Code 2.1.296: plugins cannot ship CLAUDE.md or rules (plugins-reference: "A CLAUDE.md at the plugin root isn't loaded as context"). Eval runs load only the plugin's skills, hooks, agents; user/project CLAUDE.md and `.claude/` are never read (plugin-evals, "How runs are isolated").
  - L2. Canary: a plugin SessionStart hook that `cat`s a file fired inside `claude plugin eval` (with 1.00 / without 0.00, 1 run each, $0.08).
  - L3. WebSearch is withheld in eval unless granted via `--allow-tools WebSearch` (score 0 to 1.00 after grant). WebFetch works with `--allow-tools "WebFetch(domain:pypi.org)"`.
  - L4. gh code search: the "search side" exists only as one-line fragments inside larger rule sets (details in Found 1).
  - L5. awesome-claude-code via gh api: CONTRIBUTING read directly (details in Found 4).
- Gaps: no search for published repos that bundle eval results; no measured cadence of agent-tooling change; Claude Code's own system prompt is unpublished; most paper figures are snippet-level.

## Found

### 1. Prior art: the "search side" is crowded, the "expiry side" is thin
- Context7 (Upstash), ~59k stars (dev.co listing, 2026-07-07; snippet). A retrieval tool, library docs only. Its server instruction, which is read here in full, says "Use even when you think you know the answer - your training data may not reflect recent changes." It is the deployed, narrower version of "check at time of use". It is a foil and an adoption comparator, not a rule.
- L4 fragments: claude-prime `_apply-all.md` ("ZERO ASSUMPTIONS ... trained knowledge is stale or wrong"; 119 stars, pushed 2026-05-16); houserules `standing-rules.md` (2 stars); ai-coding-config `trust-and-decision-making.mdc` ("When to Search vs. Rely on What You Know"; 24 stars, pushed 2026-09-21). None attaches expiry to recommendations or stored judgments. A search for `"valid-until" recommendation rule` returned 0 hits.
- Expiry side exists as tools and schemas for project decisions, not as a short rule on external LLM knowledge:
  - Selvedge `stale_decisions` MCP (full fetch; no adoption numbers).
  - DEG and FreshCtx (snippet).
  - ADR metamodels with review dates (Ardoq; snippet).
  - Memory-TTL posts: urandom.io 2026-03-25 (fetched), tianpan.co 2026-07-02 (snippet).
  - STALE benchmark, arXiv 2605.06527 (abstract only): the best model scores 55.2%, and agents retrieve updated evidence but do not act on it. This supports explicit expiry metadata.
- Date-injection hooks (tommcfarlin gist; snippet) tell the model today's date, not "verify". This is the nearest delivery-mechanism precedent.
- The mainstream form of expiry is a revisit trigger plus an owner, not a calendar date. An HN opinion says 6-12 month ADR expiry never worked in practice (snippet). The author's "valid-until or invalidating event" matches the trigger form.
- Differentiation (note's reading, web search only): the unfilled niche is one short tool-free rule combining (i) as-of dates on claims, (ii) valid-until or invalidating event on recommendations, with "no expiry = freshness unknown, weight down", and (iii) a one-time "was this superseded?" check before reusing months-old "latest methods".

### 2. Delivery: hook mechanics (hooks doc 2026-10-13, partial read via summarizer)
- SessionStart plain stdout on exit 0 is added as context. The JSON form (`hookSpecificOutput.additionalContext`) is also documented. Neither is marked recommended.
- Cap: 10,000 chars for each of additionalContext, systemMessage, initialUserMessage and plain stdout. Over the cap, the text goes to a file and Claude sees a path plus a 2,000-char preview, and is not told to read it. The rule file must stay under 10,000 chars.
- Matchers: startup, resume, clear, compact, fork. superpowers uses `startup|clear|compact` and omits resume because resume replays the transcript, which would duplicate the text. Its hook emits one JSON field only, because Claude Code reads both flat and nested fields without dedup.
- The docs advise factual statements over imperative system-style commands, since imperatives can trigger prompt-injection defences. Delivery (L2) does not prove compliance.
- Known issues (mirrors of anthropics/claude-code; one fetched, the rest snippet):
  - #28305: compact-matcher context not injected (v2.1.51, closed not-planned). Status on 2.1.296 is untested.
  - #53682 and #31658: mixing raw-text and bare-JSON hooks, or flat and nested JSON, on one matcher dropped one of them. Plain stdout alone has no reported bug.
  - #21659: identical command strings in two plugins are deduped before `${CLAUDE_PLUGIN_ROOT}` expansion, so one is skipped.
  - #14281: additionalContext injected multiple times (closed).
- Memory doc: `~/.claude/rules/*.md` and `.claude/rules/*.md` are official. Install for a user = copy the file. By L1 plugins cannot ship them, hence the hook. The hook is Claude Code-specific. Cursor rejects plain-text SessionStart stdout and its sessionStart is reported buggy. Codex and Gemini have experimental hooks (third-party snippets). The portable core is the plain file used as AGENTS.md, GEMINI.md or `.cursor/rules`.

### 3. Eval design (plugin-evals doc, read in full for the relevant sections; FreshQA via summary)
- Defaults: 3 runs per case per arm. `--ablation with-without` adds a no-plugin arm; delta = with minus without. Each run is an isolated session with an empty working directory.
- Graders: regex, tool_used, tool_order, file_exists, llm, baseline. A grader that cannot pass without the plugin is a `scored:false` indicator unless `arm: both` is set. The hook-fired probe is therefore with-only.
- The default judge is haiku; the doc warns it is format-biased on long text. Use regex for long files, `--judge-model sonnet` for llm graders, and short PASS/FAIL rubrics.
- Output is `results/<timestamp>/aggregate-result.json` (schemaVersion 1) plus a single self-contained `report.html`, so bundling is feasible (inference; the doc does not mention publishing). Rate-limited runs score 0 and look like regressions, so check NOTES/error fields. Check the bundle for absolute paths and account info before committing (not verified).
- With L3: tool_used WebSearch/WebFetch graders work only if both arms are granted the tools. Pin `--allow-tools` in the repo's eval command.
- Grader sketch (inference from the doc, not a sourced method):
  - Search-before-assert: tool_used plus tool_order, with a regex on the final reply for a date pattern.
  - Expiry attached: file_exists plus a regex for `valid[- ]until|expires|review[- ]when|invalidat`.
  - Controls: never-changing facts (for example "explain a mutex") with a negative `arm: both` tool_used grader, to catch ritual searching. FreshQA lesson: reward confident-correct answers, do not reward refusal or hedging, and include false-premise items. Here, a prompt that embeds an outdated premise is the stale-claim trap.
  - Ceiling risk: base Claude may already search on "current way to X" prompts, so delta is about 0. Claude Code already injects the current date.
  - Pair a regex for "as of" with tool_used, because boilerplate satisfies the regex alone.
- n: 6 cases x 3 runs = 18 per arm. The author's evals rule says 4-8 test cases are noise for hill-climbing, so use these results as a presence-of-effect check, report per-case raw pass counts, and claim no magnitude. The AGENTS.md ablation (arXiv 2602.11988; secondary summaries only) found agents follow context files but task success is not improved and cost rises about 20%. Report behaviour delta plus tool-call and token cost.

### 4. Awesome lists (read 2026-10-13)
- hesreallyhim/awesome-claude-code (55.6k stars; last commit 2026-10-13 by gh api). CONTRIBUTING read via API (L5):
  - Issue form only; "Do not open a PR".
  - Eligible if at least 14 days since first commit with later commits, or at least 100 stars.
  - One recommendation at a time; recommendations must be created by humans (so the author files the form manually).
  - One-line, non-salesy description. "If getting on the list is any part of a promotional strategy... have a backup plan."
  - README sections include Configuration, Memory & Context Persistence, Skills and Multi-Purpose; no dedicated rules section.
- Anthropic: a self-hosted marketplace needs no submission, just `.claude-plugin/marketplace.json` in the repo. Install is `claude plugin marketplace add <owner>/<repo>`; the one-shot `--marketplace` form needs v2.1.292+. Validate with `claude plugin validate --strict`; the docs also list `claude plugin eval` as a pre-release step. The claude.ai directory takes submissions through the developer portal (paid plan, GitHub repo). `claude-plugins-official` accepts no portal submissions. SessionStart-hook platform support on claude.ai/Cowork is unverified.
- travisvn/awesome-claude-skills: PRs under 10 stars are auto-closed, and it requires "not AI-generated" work. VoltAgent/awesome-agent-skills: "Brand new skills ... are not accepted", skills only. PatrickJS/awesome-cursorrules (40.9k stars; 82 open PRs; last-commit date not retrieved): PR with a `.mdc` file. Offering the rule as `alwaysApply: true` is possible but Cursor-specific. jqueryscript/awesome-claude-code: criteria not retrieved (404). No AGENTS.md-specific list was found.
- General lists (awesome-python, awesome-nodejs and similar) have age and star gates that a brand-new single-file repo fails (snippet).

### 5. Is it redundant or harmful?
- Substrate: the Opus 5.5 chat system prompt (2026-09-22, read in full) has a knowledge-cutoff block telling Claude to say its knowledge may be superseded and to direct people to web search. The docs say these prompts do not apply to the API. Claude Code's own prompt is unpublished, so equivalence there is unverified. The block covers news-style recency, not library/tool facts before design decisions, nor expiry on stored judgments.
- Problem is real but not "weekly": arXiv 2604.09515 (snippet) says models do not reliably override stale parametric knowledge even when newer docs are in the prompt; arXiv 2605.06279 (snippet) found version-pinning varies 26.83%-95.18%. The Upstash benchmark is a vendor source, and its figures plus the secondhand ICSE numbers are unverified. No primary data on a ~1-week cadence was found. The closest anecdote is the month-scale release volatility listed in the Opus 5.5 prompt.
- Harms:
  - Over-searching (Apple over-searching paper, When2Tool 2605.09252, Web Tool Trap; all snippet): prompt-only discouragement suppresses needed calls along with unneeded ones, and "primary source" can be a stale or SEO page.
  - Hedging boilerplate stacking on top of Claude's own cutoff hedging (untested).
  - Instruction dilution: IFScale 2507.11538 (read in full) shows accuracy falling with instruction count, but on a synthetic 2025 task. Conflict between instructions matters more than count (snippet). Token cost of a short rule is negligible.
- Alternatives named: a SessionStart hook injecting today's date plus the gap to the cutoff (checkable, untested); an on-demand skill (the author's own ADR-0018 says self-firing skills are unreliable).

## Contradictions
- awesome-claude-code intake. The adversarial note's mirror (mintlify, snippet) said "only account allowed to submit PRs is Claude" and listed criteria like license and actively maintained. The awesome-lists note and L5 (CONTRIBUTING via API) give the issue form, a 14-day / 100-star gate and human-authored recommendations. The primary read (API) is stronger; use it. The mirror's license criterion is unconfirmed.
- Substrate absorbs the search side vs it does not. The Opus 5.5 chat prompt does carry superseded-knowledge wording, but its docs scope it to claude.ai and exclude the API; Claude Code's prompt is unknown. The wording is not evidence for Claude Code or other agents. L4/Context7 show the search side is also present in the wild as ad-hoc lines. The non-redundant part is the expiry side (stronger evidence: no expiry text in the L4 hits, 0 for `valid-until`).
- Hook output form. hook-delivery found plain stdout and JSON both documented and plain stdout has no reported own bug; superpowers emits JSON with a single field and platform detection. Issues #53682/#31658 concern mixing shapes, not plain stdout. The two are consistent: plain stdout alone is the simplest; do not mix with other hooks' shapes. Compact and resume behaviour on 2.1.296 is untested.
- Prompt-only discouragement of search vs needed calls. When2Tool says prompt-only discouragement suppresses necessary calls, while FreshQA and the hook-delivery note suggest control cases reward restraint. The evidence is preprint/snippet; handle with eval controls, not rule text.
- "Weekly" staleness. The author's worldview says about one week; the evidence found supports staleness, not that cadence. Treat the figure as a heuristic.

## Still unknown
- Behaviour of SessionStart under `claude -p` outside plugin eval; whether compact injects on 2.1.296; whether resume duplicates text; whether plain stdout and JSON differ in wrapping. All are cheap local tests.
- Whether any public repo bundles `claude plugin eval` results; whether results contain absolute paths or account info.
- Whether Claude Code's own system prompt carries a recency instruction (unpublished); OpenAI/Cursor/Codex defaults.
- Whether the SessionStart plugin loads on claude.ai/Cowork and passes Anthropic's portal validation.
- Last-commit and merge latency of awesome-cursorrules and other lists; which README section of awesome-claude-code fits best.
- Full text of the snippet-level papers (2604.09515, 2605.06279, 2605.09252, 2602.11988, STALE) and the ICSE deprecated-API figures.
- Any measured cadence of change in agent tooling; any eval of "rule says verify" versus none on staleness errors with tool-call cost.
