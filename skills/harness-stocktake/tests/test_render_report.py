"""render_report.py: the deterministic Phase 3 of harness-stocktake.

Claims:
    - SOURCE_ORDER is the source table of SKILL.md, in its order (the two cannot drift apart)
    - order = verdict group, then source table order, then id; Keep items come last
    - two non-Keep items on one file collide even when crosscheck.json is absent
    - Phase 2 collisions and amends land in both items' conflicts and in the change cell
    - a grouped Retire item (`targets`) absorbs same-group items on those files; they get no row
    - an unreadable item file is named in the header instead of failing the run
    - report.md ends with the native-check paragraph; --assembled marks the header
    - a section's item lines are left out of report.md (each finding appears once, in the tables)
    - --lang ja and --lang en write the same report structure in their own words (the tests below
      assert the Japanese text; test_lang_en_* the English)
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from scripts import render_report

SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"


def _item(item_id: str, verdict: str, target: str, **extra: object) -> dict:
    return {
        "id": item_id,
        "source": item_id.split("-")[0],
        "verdict": verdict,
        "target": target,
        "reason": f"reason of {item_id}. More.",
        "change": f"change {item_id}",
        **extra,
    }


def _run(tmp_path: Path, files: dict[str, object], crosscheck: object = None) -> Path:
    run = tmp_path / "run"
    (run / "sections").mkdir(parents=True)
    for name, items in files.items():
        (run / f"items-{name}.json").write_text(json.dumps(items), encoding="utf-8")
        (run / "sections" / f"{name}.md").write_text(
            f"## Source: {name}\n\n- line\n", encoding="utf-8"
        )
    if crosscheck is not None:
        (run / "crosscheck.json").write_text(json.dumps(crosscheck), encoding="utf-8")
    return run


def _render(run: Path, *extra: str) -> tuple[str, list[dict]]:
    lang = [] if "--lang" in extra else ["--lang", "ja"]
    assert render_report.main([str(run), "--target", "demo", *lang, *extra]) == 0
    out = run / ("report.assembled.md" if "--out" in extra else "report.md")
    return out.read_text(encoding="utf-8"), json.loads((run / "items-all.json").read_text())


def test_source_order_matches_skill_table() -> None:
    text = SKILL.read_text(encoding="utf-8")
    table = text.split("| Source id | Skill | What it audits |", 1)[1]
    ids = re.findall(r"^\| `([a-z]+)` \|", table.split("\n\n", 1)[0], flags=re.M)
    assert ids == render_report.SOURCE_ORDER[: len(ids)]
    assert render_report.SOURCE_ORDER[len(ids) :] == ["generation"]


def test_order_groups_then_source_then_id(tmp_path: Path) -> None:
    run = _run(
        tmp_path,
        {
            "skills": [
                _item("skills-10", "Retire", "a"),
                _item("skills-2", "Keep", "b"),
                _item("skills-3", "Improve", "c"),
            ],
            "hooks": [_item("hooks-01", "Update", "d"), _item("hooks-02", "Retire", "e")],
        },
    )
    _, items = _render(run)
    assert [i["id"] for i in items] == ["hooks-02", "skills-10", "hooks-01", "skills-3", "skills-2"]
    assert [i["order"] for i in items] == [1, 2, 3, 4, 5]


def test_same_target_collides_without_crosscheck(tmp_path: Path) -> None:
    run = _run(
        tmp_path,
        {
            "docs": [_item("docs-01", "Update", "CLAUDE.md")],
            "distill": [
                _item("distill-01", "Append", "CLAUDE.md"),
                _item("distill-02", "Keep", "CLAUDE.md"),
            ],
        },
    )
    report, items = _render(run)
    by_id = {i["id"]: i for i in items}
    assert by_id["docs-01"]["conflicts"] == ["distill-01"]
    assert by_id["distill-02"]["conflicts"] == []
    assert "crosscheck.json が無い" in report
    assert "docs-01 × distill-01 (same-target)" in report


def test_crosscheck_collisions_and_amend(tmp_path: Path) -> None:
    run = _run(
        tmp_path,
        {
            "skills": [_item("skills-01", "Retire", "s/a"), _item("skills-02", "Keep", "s/b")],
            "rules": [_item("rules-01", "Update", "r.md")],
        },
        crosscheck={
            "collisions": [
                {
                    "items": ["skills-01", "rules-01", "ghost-9"],
                    "kind": "pointer",
                    "note": "r.md names a",
                    "winner": "skills-01",
                }
            ],
            "amend": {"skills-01": "also fix r.md:3"},
        },
    )
    report, items = _render(run)
    by_id = {i["id"]: i for i in items}
    assert by_id["rules-01"]["conflicts"] == ["skills-01"]
    assert "勝つのは skills-01" in report
    assert "change skills-01 **Phase 2:** also fix r.md:3" in report


def test_grouped_retire_absorbs_rows(tmp_path: Path) -> None:
    group = _item("skills-90", "Retire", ".claude/skills/{a,b,c}", targets=["s/a", "s/b", "s/c"])
    run = _run(
        tmp_path,
        {
            "skills": [
                group,
                _item("skills-01", "Retire", "s/a"),
                _item("skills-02", "Retire", "s/b"),
                _item("skills-03", "Improve", "s/c"),
            ]
        },
    )
    report, items = _render(run)
    by_id = {i["id"]: i for i in items}
    assert by_id["skills-01"]["folded_into"] == "skills-90"
    assert "skills-03" in by_id["skills-90"]["conflicts"]
    rows = [ln for ln in report.splitlines() if re.match(r"^\| \d+ \| skills-", ln)]
    assert [r.split(" | ")[1] for r in rows] == ["skills-90", "skills-03"]
    assert "3 file・2 項目を束ねた: skills-01, skills-02" in report


def test_bad_item_file_is_named_not_fatal(tmp_path: Path) -> None:
    run = _run(tmp_path, {"hooks": [_item("hooks-01", "Retire", "h.sh")]})
    (run / "items-docs.json").write_text("{not json", encoding="utf-8")
    report, _ = _render(run)
    assert "items-docs.json: 読めない" in report
    assert "hooks-01" in report


def test_assembled_header_sections_and_native_note(tmp_path: Path) -> None:
    run = _run(
        tmp_path,
        {
            "skills-2": [_item("skills-20", "Retire", "x")],
            "skills-1": [_item("skills-10", "Keep", "y")],
            "hooks": [],
        },
    )
    report, _ = _render(run, "--assembled", "--out", str(run / "report.assembled.md"))
    assert "呼び出し側が items から組み立てた" in report
    heads = [ln for ln in report.splitlines() if ln.startswith("### Source")]
    assert heads == ["### Source: hooks", "### Source: skills-1", "### Source: skills-2"]
    assert report.rstrip().endswith("（この run はどちらも実行していない）。")
    assert "`/doctor prompt-audit`" in report


def test_no_items_is_exit_2(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    assert render_report.main([str(tmp_path / "empty")]) == 2


def test_empty_item_lists_still_render(tmp_path: Path) -> None:
    run = _run(tmp_path, {"hooks": [], "rules": {"items": []}})
    report, items = _render(run)
    assert items == []
    assert "| **Total** | **0** |" in report


def test_native_note_matches_artifact_template() -> None:
    body = render_report.MESSAGES["ja"]["native"].split("\n\n", 1)[1].strip()
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", body)
    template = (SKILL.parent / "templates" / "report.html").read_text(encoding="utf-8")
    assert f"<p>{html}</p>" in template


def test_collision_on_folded_item_moves_to_its_group(tmp_path: Path) -> None:
    group = _item("skills-probe-01", "Retire", "pack", targets=["s/a", "s/b"])
    run = _run(
        tmp_path,
        {
            "skills-probe": [group],
            "skills-1": [_item("skills-1-01", "Retire", "s/a")],
            "rules": [_item("rules-01", "Update", "r.md")],
        },
        crosscheck={
            "collisions": [
                {"items": ["skills-1-01", "rules-01"], "kind": "pointer"},
                {"items": "skills-1-01,rules-01"},
            ]
        },
    )
    report, items = _render(run)
    by_id = {i["id"]: i for i in items}
    assert by_id["skills-probe-01"]["conflicts"] == ["rules-01"]
    assert "items が配列でない衝突を 1 件外した" in report


def test_first_sentence_keeps_abbreviations() -> None:
    assert (
        render_report._first_sentence("Covers it, e.g. the PR flow. More.")
        == "Covers it, e.g. the PR flow."
    )


def test_target_starting_with_dash(tmp_path: Path) -> None:
    run = _run(tmp_path, {"hooks": []})
    assert render_report.main([str(run), "--target=-tools", "--base=-"]) == 0
    assert "— -tools" in (run / "report.md").read_text(encoding="utf-8")


def test_symlinked_inputs_are_skipped_and_outputs_refused(tmp_path: Path) -> None:
    secret = tmp_path / "secret.md"
    secret.write_text("SECRET-LINE\n", encoding="utf-8")
    run = _run(tmp_path, {"hooks": [_item("hooks-01", "Retire", "h.sh")]})
    (run / "sections" / "leak.md").symlink_to(secret)
    (run / "sections" / "dir.md").mkdir()
    report, _ = _render(run)
    assert "SECRET-LINE" not in report
    assert "sections/leak.md: 通常の file でないので読まない" in report
    victim = tmp_path / "victim.txt"
    (run / "report.md").unlink()
    (run / "report.md").symlink_to(victim)
    assert render_report.main([str(run)]) == 2
    assert not victim.exists()


def test_untrusted_frame_precedes_copied_text(tmp_path: Path) -> None:
    run = _run(tmp_path, {"hooks": []})
    report, _ = _render(run, "--untrusted")
    assert report.index(render_report.MESSAGES["ja"]["untrusted"]) < report.index("## Sources")


def test_skills_batch_keep_collides_with_probe_merge(tmp_path: Path) -> None:
    run = _run(
        tmp_path,
        {
            "skills-1": [_item("skills-1-01", "Keep", "s/a")],
            "skills-probe": [_item("skills-probe-01", "Merge into b", "s/a")],
        },
    )
    _, items = _render(run)
    assert {i["id"]: i["conflicts"] for i in items} == {
        "skills-probe-01": ["skills-1-01"],
        "skills-1-01": ["skills-probe-01"],
    }


def test_fold_joins_grouped_items_across_batches(tmp_path: Path) -> None:
    run = _run(
        tmp_path,
        {
            "skills-1": [_item("skills-1-01", "Retire", "pack", targets=["s/a", "s/b"])],
            "skills-2": [
                _item("skills-2-01", "Retire", "pack", targets=["s/c", "s/d"]),
                _item("skills-2-02", "Retire", "s/d"),
                _item("skills-2-03", "Improve", "s/e"),
            ],
        },
        crosscheck={"fold": [{"into": "skills-1-01", "items": ["skills-2-01", "skills-2-03"]}]},
    )
    report, items = _render(run)
    by_id = {i["id"]: i for i in items}
    assert by_id["skills-1-01"]["targets"] == ["s/a", "s/b", "s/c", "s/d"]
    assert by_id["skills-2-01"]["folded_into"] == "skills-1-01"
    assert by_id["skills-2-02"]["folded_into"] == "skills-1-01"
    assert "folded_into" not in by_id["skills-2-03"]
    assert "判定の group が違うので外した" in report
    rows = [ln for ln in report.splitlines() if re.match(r"^\| \d+ \| skills-", ln)]
    assert [r.split(" | ")[1] for r in rows] == ["skills-1-01", "skills-2-03"]


def test_section_item_lines_appear_once(tmp_path: Path) -> None:
    run = _run(tmp_path, {"hooks": [_item("hooks-01", "Retire", "h.sh")]})
    (run / "sections" / "hooks.md").write_text(
        "## Source: hooks — Retire 1 · Keep 0\n\nScope: 1 hook.\n\n"
        "- Retire · h.sh · reason of hooks-01.\n\nKeep: 0\n",
        encoding="utf-8",
    )
    report, _ = _render(run)
    assert "### Source: hooks — Retire 1 · Keep 0" in report
    assert "Scope: 1 hook." in report and "Keep: 0" in report
    assert report.count("reason of hooks-01.") == 1


def test_lang_en_writes_english_labels(tmp_path: Path) -> None:
    run = _run(
        tmp_path,
        {"hooks": [_item("hooks-01", "Retire", "h.sh"), _item("hooks-02", "Keep", "k.sh")]},
    )
    report, _ = _render(run, "--lang", "en")
    assert report.startswith("# Harness stocktake ")
    assert "| Retire | 1 |" in report
    assert "## Keep (1)" in report
    assert "no crosscheck.json" in report
    assert "## What the native checks cover" in report
    assert not re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", report)


def test_lang_default_is_english(tmp_path: Path) -> None:
    run = _run(tmp_path, {"hooks": [_item("hooks-01", "Retire", "h.sh")]})
    assert render_report.main([str(run), "--target", "demo"]) == 0
    assert (run / "report.md").read_text(encoding="utf-8").startswith("# Harness stocktake ")
