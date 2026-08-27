"""Hermetic tests for overlap_candidates.py — fixture libraries in tmp_path.

The two grounding-checklist items this script replaces were self-reports
("Grepped ~/.claude/skills/ for keywords", "Checked for overlap with
MEMORY.md"). The tests therefore pin the two properties a self-report could
never give: the candidate list is derived from the draft's own terms, and every
hit carries a line number so the judgment can be checked.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.overlap_candidates import (
    MIN_SHARED_MEMORY_TERMS,
    collect_evidence,
    count_concepts,
    derive_memory_path,
    discover_memory_files,
    main,
    memory_matches,
    normalize_terms,
    read_skill_descriptions,
    score_candidates,
)

DRAFT = """# Rate limit as a policy signal

## Problem
A burst of 429s from an external platform is not a transient error.

## Solution
Stop the burst and report to the human instead of backing off.
"""


def write_skill(root: Path, name: str, description: str) -> Path:
    d = root / name
    d.mkdir(parents=True)
    md = d / "SKILL.md"
    md.write_text(
        f'---\nname: {name}\ndescription: "{description}"\norigin: shimo4228\n---\n\n# {name}\n',
        encoding="utf-8",
    )
    return md


@pytest.fixture
def skills_root(tmp_path: Path) -> Path:
    root = tmp_path / "skills"
    root.mkdir()
    return root


# ------------------------------------------------------------- skill overlap


def test_overlapping_skill_is_ranked_above_unrelated_ones(skills_root: Path) -> None:
    write_skill(skills_root, "debugging-notes", "Rate limit burst policy signal for platforms")
    write_skill(skills_root, "cake", "Bake a cake with flour and sugar")
    ranked = score_candidates(DRAFT, read_skill_descriptions(skills_root)[0])[0]
    assert ranked[0]["skill"] == "debugging-notes"
    assert ranked[0]["score"] > 0
    assert ranked[0]["shared_terms"]


def test_zero_overlap_candidates_are_dropped(skills_root: Path) -> None:
    write_skill(skills_root, "cake", "Bake a cake with flour and sugar")
    assert score_candidates(DRAFT, read_skill_descriptions(skills_root)[0])[0] == []


def test_top_n_bounds_the_candidate_list(skills_root: Path) -> None:
    for i in range(6):
        write_skill(skills_root, f"s{i}", f"Rate limit handling variant {i}")
    ranked = score_candidates(DRAFT, read_skill_descriptions(skills_root)[0], top_n=3)[0]
    assert len(ranked) == 3


def test_skill_body_is_not_read_only_the_description(skills_root: Path) -> None:
    # The listing surface a future session selects on is the description; a body
    # match would rank a skill the model will never be routed to.
    md = write_skill(skills_root, "cake", "Bake a cake")
    md.write_text(md.read_text(encoding="utf-8") + "\nrate limit burst policy signal\n")
    assert score_candidates(DRAFT, read_skill_descriptions(skills_root)[0])[0] == []


def test_unreadable_description_is_named_not_scored_zero(skills_root: Path) -> None:
    d = skills_root / "bare"
    d.mkdir()
    (d / "SKILL.md").write_text("---\nname: bare\n---\n\nbody\n", encoding="utf-8")
    assert "bare" not in read_skill_descriptions(skills_root)[0]
    assert read_skill_descriptions(skills_root)[1] == [
        {"skill": "bare", "reason": "no-description"}
    ]


def test_folded_block_description_is_read(skills_root: Path) -> None:
    # skills/paper-deposit/SKILL.md uses `description: >-` (2026-08-26, the only
    # one in the 67-skill library). Read naively the value is ">-", which
    # normalizes to nothing and silently removes that skill from every overlap
    # comparison — a miss the checklist item it replaced would never have made.
    d = skills_root / "folded"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: folded\ndescription: >-\n  Rate limit burst policy signal\n"
        "  for external platforms\norigin: shimo4228\n---\n\nbody\n",
        encoding="utf-8",
    )
    descriptions = read_skill_descriptions(skills_root)[0]
    assert "Rate limit burst policy signal for external platforms" == descriptions["folded"]
    assert score_candidates(DRAFT, descriptions)[0][0]["skill"] == "folded"


def test_literal_block_description_is_read(skills_root: Path) -> None:
    d = skills_root / "literal"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: literal\ndescription: |\n  Rate limit burst\n  policy signal\n---\n",
        encoding="utf-8",
    )
    assert read_skill_descriptions(skills_root)[0]["literal"] == "Rate limit burst policy signal"


def test_block_description_stops_at_the_next_key(skills_root: Path) -> None:
    d = skills_root / "stops"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: stops\ndescription: >-\n  Rate limit burst\norigin: shimo4228\n"
        "user-invocable: true\n---\n",
        encoding="utf-8",
    )
    assert read_skill_descriptions(skills_root)[0]["stops"] == "Rate limit burst"


def test_symlinked_skill_directories_are_included(skills_root: Path, tmp_path: Path) -> None:
    # `hunk-review` is a symlink out of the skills root; it still occupies the
    # listing, so it still competes for the draft's trigger.
    external = tmp_path / "external" / "outside"
    external.mkdir(parents=True)
    (external / "SKILL.md").write_text(
        '---\nname: outside\ndescription: "Rate limit burst policy signal"\n---\n', encoding="utf-8"
    )
    (skills_root / "outside").symlink_to(external, target_is_directory=True)
    assert "outside" in read_skill_descriptions(skills_root)[0]


# ------------------------------------------------------------ MEMORY overlap


def test_memory_index_line_is_matched_with_its_line_number(tmp_path: Path) -> None:
    memory = tmp_path / "MEMORY.md"
    memory.write_text(
        "# Memory\n\n## Feedback\n\n"
        "- [debugging](./debugging.md) — rate limit burst is a policy signal\n"
        "- [cake](./cake.md) — how to bake\n"
        "- [one](./one.md) — an unrelated note that happens to mention platform\n",
        encoding="utf-8",
    )
    hits, _read, _failed, _total = memory_matches(DRAFT, [memory])
    # The 'platform' line shares exactly one term and is below the floor.
    assert len(hits) == 1
    assert hits[0]["line"] == 5
    assert hits[0]["file"].endswith("MEMORY.md")
    assert hits[0]["shared_terms"]


def test_single_shared_term_is_below_the_memory_floor() -> None:
    # Measured 2026-08-26: on the live global MEMORY.md every false candidate
    # shared exactly one term and the true one shared four. Containment divides
    # by the candidate's term count, so a 3-term index line scores high on one
    # incidental word — the floor, not the score, is what separates them.
    assert MIN_SHARED_MEMORY_TERMS == 2
    line = "- [x](./x.md) — an entry about platform economics\n"
    assert memory_matches(DRAFT, [])[0] == []
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "MEMORY.md"
        f.write_text(line, encoding="utf-8")
        assert memory_matches(DRAFT, [f])[0] == []


def test_global_memory_is_discovered_from_any_project(tmp_path: Path) -> None:
    # The replaced checklist item said "(project + global)". Deriving only the
    # current project's slug hid the harness-level MEMORY.md from every other
    # repo, and "no candidate" then reads as verified.
    home = tmp_path / "home"
    expected = derive_memory_path(home / ".claude", home)
    expected.parent.mkdir(parents=True)
    expected.write_text("- [g](./g.md) — global\n", encoding="utf-8")
    elsewhere = tmp_path / "other-repo"
    elsewhere.mkdir()
    found, missing = discover_memory_files(elsewhere, home=home)
    assert found == [expected]
    assert elsewhere / "MEMORY.md" in missing


def test_missing_derived_memory_paths_are_reported_not_swallowed(tmp_path: Path) -> None:
    # A slug-convention change makes every derived path vanish; an empty
    # `memory_files_read` beside a non-empty `memory_files_missing` is the
    # observable form of that, and the only way the failure is not silent.
    found, missing = discover_memory_files(tmp_path / "nowhere", home=tmp_path / "nohome")
    assert found == []
    assert len(missing) == 3


def test_memory_file_absent_is_reported_not_fatal(tmp_path: Path) -> None:
    hits, read, failed, _ = memory_matches(DRAFT, [tmp_path / "nope.md"])
    assert hits == [] and read == []
    assert failed == [{"file": str(tmp_path / "nope.md"), "reason": "unreadable"}]


def test_derive_memory_path_encodes_the_project_path(tmp_path: Path) -> None:
    # Claude Code encodes the project path into ~/.claude/projects/<slug>/memory,
    # replacing "/", "." and "_" with "-" (verified against the live tree on
    # 2026-08-26: /Users/x/MyAI_Lab/agent-knowledge-cycle ->
    # -Users-x-MyAI-Lab-agent-knowledge-cycle).
    path = derive_memory_path(Path("/Users/x/MyAI_Lab/.claude"), home=tmp_path)
    assert path.name == "MEMORY.md"
    assert path.parent.name == "memory"
    assert path.parent.parent.name == "-Users-x-MyAI-Lab--claude"
    assert path.is_relative_to(tmp_path / ".claude" / "projects")


# ---------------------------------------------------------------- normalize


def test_japanese_text_produces_terms(skills_root: Path) -> None:
    # A Japanese-only draft scored zero against everything before CJK bigrams
    # were added, and "no candidates" then read as verified — the exact silent
    # false negative this script exists to remove (2026-08-26 cross-model review).
    ja_draft = "レート制限は transient error ではなく policy signal として扱う"
    write_skill(skills_root, "ja-skill", "レート制限の burst は policy signal として扱う")
    write_skill(skills_root, "unrelated", "ケーキを焼く手順")
    ranked = score_candidates(ja_draft, read_skill_descriptions(skills_root)[0])[0]
    assert ranked[0]["skill"] == "ja-skill"
    assert any(len(term) == 2 and not term.isascii() for term in ranked[0]["shared_terms"])


def test_one_japanese_word_is_one_concept() -> None:
    # A 7-character katakana word yields 6 bigrams. Counted as 6 terms it clears
    # a floor meant to require two independent ideas and outranks real matches
    # (measured 2026-08-26: it pushed a draft's true home out of the results).
    word = "パーミッション"
    assert count_concepts(normalize_terms(word), word) == 1
    two = "パーミッション セッション"
    assert count_concepts(normalize_terms(two), two) == 2


def test_a_single_japanese_word_is_below_the_memory_floor(tmp_path: Path) -> None:
    memory = tmp_path / "MEMORY.md"
    memory.write_text(
        "- [a](./a.md) — パーミッションの話\n- [b](./b.md) — パーミッションと git の話\n",
        encoding="utf-8",
    )
    draft = "パーミッション と git を扱う"
    hits, _, _, _ = memory_matches(draft, [memory])
    # One shared word is one concept and does not survive; the line that also
    # shares `git` does.
    assert [h["line"] for h in hits] == [2]
    assert hits[0]["shared_concepts"] == 2


def test_c_plus_plus_and_c_sharp_are_distinct_terms() -> None:
    # rstrip(".-+#") collapsed all three into "c", inventing a shared term and
    # hiding a genuine C++/C# overlap.
    terms = normalize_terms("C++ and C# and C")
    assert {"c", "c++", "c#"} <= terms


def test_japanese_only_text_is_not_empty() -> None:
    assert normalize_terms("レート制限") != frozenset()


def test_normalize_terms_is_case_and_punctuation_insensitive() -> None:
    assert normalize_terms("Rate-limit BURST, policy signal.") == normalize_terms(
        "rate-limit burst policy signal"
    )


def test_stopwords_do_not_create_overlap(skills_root: Path) -> None:
    write_skill(skills_root, "filler", "The and of to a an is it for with when use")
    assert score_candidates(DRAFT, read_skill_descriptions(skills_root)[0])[0] == []


# ------------------------------------------------------------- wiring / CLI


def test_collect_evidence_reports_provenance(skills_root: Path, tmp_path: Path) -> None:
    write_skill(skills_root, "debugging-notes", "Rate limit burst policy signal")
    memory = tmp_path / "MEMORY.md"
    memory.write_text("- [d](./d.md) — rate limit burst policy\n", encoding="utf-8")
    ev = collect_evidence(DRAFT, skills_root, [memory])
    assert ev["skills_root"] == str(skills_root)
    assert ev["skills_scanned"] == 1
    assert ev["memory_files_read"] == [str(memory)]
    assert ev["skill_candidates"][0]["skill"] == "debugging-notes"
    assert ev["memory_candidates"]


def test_evidence_never_judges(skills_root: Path) -> None:
    write_skill(skills_root, "twin", "Rate limit burst policy signal for external platforms")
    ev = collect_evidence(DRAFT, skills_root, [])
    # No verdict, no boolean "is a duplicate" — Save/Improve/Absorb/Drop stays
    # with learn-eval Step 5b.
    assert "verdict" not in ev
    assert "duplicate" not in json.dumps(ev)


def test_main_reads_the_draft_from_a_file_and_exits_zero(
    skills_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write_skill(skills_root, "twin", "Rate limit burst policy signal")
    draft = tmp_path / "draft.md"
    draft.write_text(DRAFT, encoding="utf-8")
    rc = main(["--draft", str(draft), "--skills-root", str(skills_root), "--no-auto-memory"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["skill_candidates"][0]["skill"] == "twin"


def test_main_reads_the_draft_from_stdin(
    skills_root: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    import io

    write_skill(skills_root, "twin", "Rate limit burst policy signal")
    monkeypatch.setattr("sys.stdin", io.StringIO(DRAFT))
    assert main(["--skills-root", str(skills_root), "--no-auto-memory"]) == 0
    assert json.loads(capsys.readouterr().out)["skills_scanned"] == 1


def test_main_exits_two_when_the_skills_root_is_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    draft = tmp_path / "d.md"
    draft.write_text(DRAFT, encoding="utf-8")
    rc = main(["--draft", str(draft), "--skills-root", str(tmp_path / "nope"), "--no-auto-memory"])
    assert rc == 2
    capsys.readouterr()


def test_empty_draft_is_an_input_error_not_a_clean_bill(
    skills_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A truncated or mis-pathed Write lands here. Reporting "no candidates" for
    # a draft with nothing in it is the false clean bill this script prevents.
    write_skill(skills_root, "twin", "Rate limit burst policy signal")
    draft = tmp_path / "empty.md"
    draft.write_text("", encoding="utf-8")
    assert main(["--draft", str(draft), "--skills-root", str(skills_root), "--no-auto-memory"]) == 2
    capsys.readouterr()


def test_unreadable_memory_file_is_not_reported_as_read(tmp_path: Path) -> None:
    # It exists, so `is_file()` said "read"; the decode failed, so zero lines
    # were compared. Reporting it as read let the SKILL.md guard miss it.
    memory = tmp_path / "MEMORY.md"
    memory.write_bytes(b"- [x](./x.md) \xff\xfe not utf-8 rate limit burst\n")
    hits, read, failed, _ = memory_matches(DRAFT, [memory])
    assert hits == []
    assert read == []
    assert failed == [{"file": str(memory), "reason": "bad-encoding"}]


def test_dangling_skill_symlink_is_named(skills_root: Path, tmp_path: Path) -> None:
    (skills_root / "gone").symlink_to(tmp_path / "not-there", target_is_directory=True)
    assert read_skill_descriptions(skills_root)[1] == [
        {"skill": "gone", "reason": "dangling-symlink"}
    ]


def test_candidate_totals_travel_with_the_truncated_slice(skills_root: Path) -> None:
    for i in range(7):
        write_skill(skills_root, f"s{i}", f"Rate limit handling variant {i}")
    hits, total = score_candidates(DRAFT, read_skill_descriptions(skills_root)[0], top_n=3)
    assert len(hits) == 3
    assert total == 7


def test_main_exits_two_when_an_explicit_memory_path_is_missing(
    skills_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # A derived path that is absent is evidence; an explicitly named one that is
    # absent is a typo, and reporting "no overlap" for it would be a false clean.
    draft = tmp_path / "d.md"
    draft.write_text(DRAFT, encoding="utf-8")
    rc = main(
        [
            "--draft",
            str(draft),
            "--skills-root",
            str(skills_root),
            "--memory",
            str(tmp_path / "nope.md"),
            "--no-auto-memory",
        ]
    )
    assert rc == 2
    capsys.readouterr()


def test_main_exits_two_when_the_draft_is_unreadable(
    skills_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "--draft",
            str(tmp_path / "missing.md"),
            "--skills-root",
            str(skills_root),
            "--no-auto-memory",
        ]
    )
    assert rc == 2
    capsys.readouterr()
