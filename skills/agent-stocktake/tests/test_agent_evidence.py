"""Hermetic tests for agent_evidence.py — fixture corpora built in tmp_path.

The fixtures reproduce the shapes measured in the real `~/.claude/agents/`
corpus on 2026-08-26 (25 files): both `tools:` notations in use (JSON list —
22 files; bare comma-separated — prompt-forager, swift-reviewer), a Japanese
confidence-discard suppression instruction (security-reviewer L91), and
ALWAYS/NEVER tokens that appear as *quoted vocabulary* rather than directives
(prompt-writer L19, swift-reviewer L3) — the false-positive case the enumerate/
decide split exists for.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.agent_evidence import (
    DEFAULT_DUP_THRESHOLD,
    collect_evidence,
    description_near_duplicates,
    main,
    normalize_terms,
    parse_tools,
    scan_suppression,
)


def write_agent(
    d: Path,
    stem: str,
    *,
    name: str | None = None,
    description: str = "Does a thing. Use when the user asks for a thing.",
    tools: str | None = '["Read", "Grep"]',
    body: str = "# Body\n\nDo the work.\n",
) -> Path:
    front = [f"name: {name if name is not None else stem}", f"description: {description}"]
    if tools is not None:
        front.append(f"tools: {tools}")
    path = d / f"{stem}.md"
    path.write_text("---\n" + "\n".join(front) + "\n---\n\n" + body, encoding="utf-8")
    return path


@pytest.fixture
def agents_dir(tmp_path: Path) -> Path:
    d = tmp_path / "agents"
    d.mkdir()
    return d


# --------------------------------------------------------------- name vs stem
# The stem verdict moved to the `harness_lint.py` gate (RFC-0014 / ADR-0054); these
# pin the boundary so it cannot come back here as a second opinion.


def test_name_is_reported_but_the_stem_verdict_is_left_to_the_gate(agents_dir: Path) -> None:
    write_agent(agents_dir, "scout", name="scout-agent")
    entry = collect_evidence(agents_dir.parent, "agents")["agents"][0]
    assert entry["name"] == "scout-agent"
    assert "name_matches_stem" not in entry


def test_missing_name_is_null_not_a_crash(agents_dir: Path) -> None:
    (agents_dir / "broken.md").write_text("---\ndescription: x\n---\n\nbody\n", encoding="utf-8")
    entry = collect_evidence(agents_dir.parent, "agents")["agents"][0]
    assert entry["name"] is None


# ------------------------------------------------------------------- tools:


def test_parse_tools_json_list_form() -> None:
    parsed = parse_tools('["Read", "Grep", "Glob", "Bash"]')
    assert parsed["form"] == "json-list"
    assert [t for t in parsed["names"]] == ["Read", "Grep", "Glob", "Bash"]


def test_parse_tools_bare_comma_form() -> None:
    # agents/prompt-forager.md L4 and agents/swift-reviewer.md L4 (2026-08-26)
    parsed = parse_tools("WebSearch, WebFetch")
    assert parsed["form"] == "bare-csv"
    assert parsed["names"] == ["WebSearch", "WebFetch"]


def test_parse_tools_absent() -> None:
    parsed = parse_tools(None)
    assert parsed["form"] is None
    assert parsed["names"] == []


def test_unknown_tool_is_classified_unknown(agents_dir: Path) -> None:
    write_agent(agents_dir, "a", tools='["Read", "Telepathy"]')
    ev = collect_evidence(agents_dir.parent, "agents")
    statuses = {t["name"]: t["status"] for t in ev["agents"][0]["tools"]["items"]}
    assert statuses["Read"] == "builtin"
    # "unverified" not "unknown": the script only knows its own dated list.
    assert statuses["Telepathy"] == "unverified"


def test_mcp_tool_resolves_against_configured_servers(agents_dir: Path) -> None:
    write_agent(agents_dir, "scout", tools='["mcp__context7__query-docs"]')
    ev = collect_evidence(
        agents_dir.parent, "agents", mcp_servers={"context7"}, mcp_sources=[{"status": "ok"}]
    )
    item = ev["agents"][0]["tools"]["items"][0]
    assert item["status"] == "mcp"
    assert item["server"] == "context7"
    assert item["server_in_config"] is True


def test_mcp_tool_of_unconfigured_server_is_flagged(agents_dir: Path) -> None:
    write_agent(agents_dir, "scout", tools='["mcp__retired__do-thing"]')
    ev = collect_evidence(
        agents_dir.parent, "agents", mcp_servers={"context7"}, mcp_sources=[{"status": "ok"}]
    )
    item = ev["agents"][0]["tools"]["items"][0]
    assert item["status"] == "mcp"
    assert item["server_in_config"] is False


def test_mcp_verdict_is_withheld_when_no_config_source_parsed(agents_dir: Path) -> None:
    # A mid-write or malformed ~/.claude.json used to flip every MCP tool to
    # "not configured" at once — fabricated Update evidence against correct
    # agents. With no usable source the script must decline to answer.
    write_agent(agents_dir, "scout", tools='["mcp__context7__query-docs"]')
    ev = collect_evidence(
        agents_dir.parent, "agents", mcp_servers=set(), mcp_sources=[{"status": "unparsable"}]
    )
    assert ev["agents"][0]["tools"]["items"][0]["server_in_config"] is None
    assert ev["registry"]["mcp_config_readable"] is False


def test_known_tools_file_is_loaded_without_crashing(
    agents_dir: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The documented escape hatch for the dated BUILTIN_TOOLS list. It was left
    # behind by the _read_text -> (text, reason) refactor and raised
    # AttributeError — exit 1 and a traceback, breaking the evidence contract
    # twice over, while 39 tests passed because they called collect_evidence
    # directly.
    write_agent(agents_dir, "a", tools='["Telepathy"]')
    listing = tmp_path / "tools.txt"
    listing.write_text("Telepathy\n", encoding="utf-8")
    rc = main(["--root", str(agents_dir.parent), "--known-tools", str(listing)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["agents"][0]["tools"]["items"][0]["status"] == "builtin"
    assert payload["registry"]["known_tools"]["source"] == "override"


def test_known_tools_override_is_honoured(agents_dir: Path) -> None:
    write_agent(agents_dir, "a", tools='["Telepathy"]')
    ev = collect_evidence(agents_dir.parent, "agents", known_tools={"Telepathy"})
    assert ev["agents"][0]["tools"]["items"][0]["status"] == "builtin"


# ------------------------------------------------- description near-duplicates


def test_near_identical_descriptions_are_paired() -> None:
    pairs = description_near_duplicates(
        {
            "a.md": "Strict README reviewer for repo top pages. Use after drafting a README.",
            "b.md": "Strict README reviewer for repo top pages. Use after drafting a README file.",
        },
        threshold=0.6,
    )
    assert len(pairs) == 1
    assert {pairs[0]["a"], pairs[0]["b"]} == {"a.md", "b.md"}
    assert pairs[0]["similarity"] >= 0.6


def test_default_threshold_sits_in_the_measured_gap() -> None:
    # 2026-08-26 corpus: highest real pair 0.525, next 0.319. The default must
    # separate them — a regression that moves it silently changes what the
    # stocktake sees.
    assert 0.32 < DEFAULT_DUP_THRESHOLD <= 0.525


def test_distinct_descriptions_are_not_paired() -> None:
    pairs = description_near_duplicates(
        {
            "a.md": "Swift concurrency reviewer for iOS projects.",
            "b.md": "Citation and reference list specialist for academic papers.",
        },
        threshold=0.6,
    )
    assert pairs == []


def test_similarity_is_word_order_insensitive() -> None:
    # difflib's character ratio drops on reordering; the token-set measure must not.
    pairs = description_near_duplicates(
        {
            "a.md": "reviewer strict README for pages top repo",
            "b.md": "strict README reviewer for repo top pages",
        },
        threshold=0.9,
    )
    assert len(pairs) == 1


def test_normalize_terms_drops_case_and_punctuation() -> None:
    assert normalize_terms("Strict README reviewer — for repo top pages.") == normalize_terms(
        "strict readme reviewer for repo top pages"
    )


# ----------------------------------------------------- suppression candidates


def test_japanese_confidence_discard_is_enumerated() -> None:
    # Verbatim from agents/security-reviewer.md L91 (2026-08-26) — the single
    # true positive in the corpus and the reason the catalog is bilingual.
    body = "前置き\n残った指摘に確信度を付け、低いものは捨てる。\n後書き\n"
    hits = scan_suppression(body.splitlines())
    assert [h["line"] for h in hits] == [2]
    assert hits[0]["patterns"] == ["confidence-discard-ja"]


def test_english_confidence_threshold_is_enumerated() -> None:
    hits = scan_suppression(["report only findings you are ≥80% confident in"])
    assert len(hits) == 1
    assert hits[0]["patterns"] == ["confidence-threshold"]


def test_be_conservative_is_enumerated() -> None:
    # agents/refactor-cleaner.md L75 (2026-08-26)
    hits = scan_suppression(["3. **Be conservative** -- when in doubt, don't remove"])
    assert len(hits) == 1


def test_severity_floor_is_enumerated() -> None:
    hits = scan_suppression(["Only report high-severity issues."])
    assert len(hits) == 1
    assert hits[0]["patterns"] == ["severity-floor"]


def test_an_output_contract_is_not_a_suppression_candidate() -> None:
    # agents/fact-checker.md L164 and readme-reviewer.md L13 shapes: "only
    # report findings" describes what the agent returns, not a class of finding
    # it withholds. The `only-report` pattern that matched them was cut on
    # 2026-08-26 after producing two false positives and no true ones.
    assert scan_suppression(["**Do NOT edit the article.** Only report findings."]) == []


def test_scoping_an_agents_own_evaluation_is_not_suppression() -> None:
    # agents/readme-judge.md L79 shape.
    assert scan_suppression(["評価は欠陥検出に限定し、文体の方向づけには使わない。"]) == []


def test_documented_scope_exclusion_is_still_enumerated() -> None:
    # agents/security-reviewer.md L82-84: surfaced on purpose. Whether a scope
    # exclusion is legitimate is a reading, not a regex.
    hits = scan_suppression(["- shell script の command injection は報告しない"])
    assert hits[0]["patterns"] == ["report-exclusion-ja"]


def test_prose_without_suppression_is_not_enumerated() -> None:
    hits = scan_suppression(["Read every file and report what you find."])
    assert hits == []


def test_always_never_candidates_are_line_numbered(agents_dir: Path) -> None:
    write_agent(agents_dir, "a", body="# B\n\nALWAYS run the gate.\nNEVER skip a file.\n")
    ev = collect_evidence(agents_dir.parent, "agents")
    lines = [h["line"] for h in ev["agents"][0]["always_never_candidates"]]
    # Frontmatter is 4 lines + blank; the body starts at line 6.
    assert len(lines) == 2
    assert lines == sorted(lines)


def test_always_never_hits_carry_their_text_for_the_llm_to_judge(agents_dir: Path) -> None:
    # agents/prompt-writer.md L19 shape: the tokens are quoted vocabulary, not a
    # directive. The script must still enumerate it — judging is the LLM's job —
    # so the text has to travel with the hit.
    write_agent(agents_dir, "a", body='# B\n\nNo "MUST", "NEVER", "ALWAYS" unless critical\n')
    ev = collect_evidence(agents_dir.parent, "agents")
    hits = ev["agents"][0]["always_never_candidates"]
    assert len(hits) == 1
    assert "unless critical" in hits[0]["text"]


# ------------------------------------------------------- measurement + wiring


def test_desc_words_and_body_lines_are_measured(agents_dir: Path) -> None:
    write_agent(agents_dir, "a", description="one two three", body="l1\nl2\nl3\n")
    evidence = collect_evidence(agents_dir.parent, "agents")
    entry = evidence["agents"][0]
    assert entry["desc_words"] == 3
    # body_lines excludes the frontmatter and the blank separator after it.
    assert entry["body_lines"] == 3
    assert evidence["total_desc_words"] == 3


def test_folded_block_description_is_read(agents_dir: Path) -> None:
    # No agent uses the folded form as of 2026-08-26, but one skill does
    # (skills/paper-deposit/SKILL.md), and the residency column is only
    # meaningful if a folded description counts its real words rather than ">-".
    (agents_dir / "folded.md").write_text(
        "---\nname: folded\ndescription: >-\n  one two\n  three four\n"
        'tools: ["Read"]\n---\n\nbody\n',
        encoding="utf-8",
    )
    entry = collect_evidence(agents_dir.parent, "agents")["agents"][0]
    assert entry["description"] == "one two three four"
    assert entry["desc_words"] == 4


def test_japanese_descriptions_produce_terms(agents_dir: Path) -> None:
    write_agent(agents_dir, "a", description="レート制限の burst を policy signal と扱う")
    write_agent(agents_dir, "b", description="レート制限の burst を policy signal として扱う")
    pairs = collect_evidence(agents_dir.parent, "agents")["description_near_duplicates"]
    assert len(pairs) == 1


def test_unparsable_tools_list_is_named_at_the_top_level(agents_dir: Path) -> None:
    # YAML flow style is valid frontmatter but not JSON. Left unnamed, the
    # agent's `items: []` reads identically to "no tools: key" — unrestricted.
    write_agent(agents_dir, "a", tools="[Read, Grep]")
    ev = collect_evidence(agents_dir.parent, "agents")
    assert ev["agents"][0]["tools"]["form"] == "unparsable"
    assert ev["tools_unparsable"] == ["a.md"]


def test_unreadable_agent_files_are_named_not_dropped(agents_dir: Path) -> None:
    # Silently dropping one leaves agents_total counting a file that appears
    # nowhere in `agents` — a JSON that looks complete and is not.
    write_agent(agents_dir, "ok")
    (agents_dir / "huge.md").write_text("x" * 1_000_001, encoding="utf-8")
    ev = collect_evidence(agents_dir.parent, "agents")
    assert ev["agents_total"] == 2
    assert [a["file"] for a in ev["agents"]] == ["ok.md"]
    assert ev["unreadable"] == [{"file": "huge.md", "reason": "too-big"}]


def test_agents_are_sorted_by_filename(agents_dir: Path) -> None:
    for stem in ("zeta", "alpha", "mid"):
        write_agent(agents_dir, stem)
    ev = collect_evidence(agents_dir.parent, "agents")
    assert [a["file"] for a in ev["agents"]] == ["alpha.md", "mid.md", "zeta.md"]


def test_missing_agents_dir_returns_none(tmp_path: Path) -> None:
    assert collect_evidence(tmp_path, "agents") is None


def test_main_emits_json_and_exits_zero_with_findings(
    agents_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # evidence, not a verdict: a corpus full of findings still exits 0.
    write_agent(agents_dir, "a", name="mismatch", tools='["Telepathy"]', body="ALWAYS do it.\n")
    rc = main(["--root", str(agents_dir.parent)])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    # The CLI surface, not just collect_evidence, must be free of the moved field.
    assert "name_matches_stem" not in payload["agents"][0]


def test_main_exits_two_when_corpus_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--root", str(tmp_path)]) == 2
    capsys.readouterr()


def test_registry_provenance_is_reported(agents_dir: Path) -> None:
    write_agent(agents_dir, "a")
    ev = collect_evidence(agents_dir.parent, "agents", mcp_servers={"context7"})
    assert ev["registry"]["mcp_servers"] == ["context7"]
    # The as-of stamp is what lets a reader weigh an "unverified" against the
    # list's age; without it the classification claims more than it knows.
    assert ev["registry"]["known_tools"]["as_of"]
    assert ev["registry"]["known_tools"]["source"] == "embedded"


def test_overridden_tool_list_carries_no_as_of_stamp(agents_dir: Path) -> None:
    # An empty or truncated --known-tools file flips every builtin to
    # "unverified"; stamping the embedded date beside it would hide why.
    write_agent(agents_dir, "a")
    reg = collect_evidence(agents_dir.parent, "agents", known_tools=set())["registry"]
    assert reg["known_tools"] == {"source": "override", "as_of": None, "count": 0}


def test_mcp_config_provenance_is_deduplicated(tmp_path: Path) -> None:
    # With --root ~/.claude two of the three candidate paths are the same file;
    # listing it twice reads as two independent confirmations of a server.
    from scripts.agent_evidence import discover_mcp_servers

    _, sources = discover_mcp_servers(Path.home() / ".claude")
    paths = [s["path"] for s in sources]
    assert len(paths) == len(set(paths))
    assert all("status" in s for s in sources)


def test_always_never_ignores_the_description(agents_dir: Path) -> None:
    # agents/swift-reviewer.md:3 says "MUST BE USED for Swift projects" in its
    # description. That is a delegation trigger, not an instruction to the
    # agent, so the body-only scan must not surface it.
    write_agent(agents_dir, "a", description="Reviewer. MUST BE USED for X.", body="# B\n\nok\n")
    assert (
        collect_evidence(agents_dir.parent, "agents")["agents"][0]["always_never_candidates"] == []
    )
