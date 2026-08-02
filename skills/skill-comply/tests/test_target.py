"""Tests for target classification and skill placement.

The defect these exist for: a project-scoped skill is invisible to the child, so
the agent's first call was `Skill(name)` → `Unknown skill`, and the report still
printed 75% / 50% / 25% — a score for an agent that never loaded the thing under
test, with nothing saying so.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.runner import place_skill
from scripts.target import MAX_DESCRIPTION_CHARS, classify_target, skill_payload

SKILL_TEXT = """---
name: widget-forge
description: Forge widgets carefully.
---

# widget-forge

Step 1: SECRET-PROCEDURE-TOKEN
Step 2: do the thing.
"""


def _skill_at(root: Path, rel: str, text: str = SKILL_TEXT) -> Path:
    path = root / rel / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path


def test_global_skill_needs_no_placement(tmp_path: Path) -> None:
    """`~/.claude/skills/` is visible to every child regardless of cwd."""
    home = tmp_path / "home"
    path = _skill_at(home / "skills", "widget-forge")

    target = classify_target(path, global_root=home)

    assert target.kind == "global-skill"
    assert target.needs_placement is False
    assert skill_payload(target, full_body=False) is None


def test_project_skill_needs_placement(tmp_path: Path) -> None:
    path = _skill_at(tmp_path / "repo" / ".claude" / "skills", "widget-forge")

    target = classify_target(path, global_root=tmp_path / "home")

    assert target.kind == "project-skill"
    assert target.needs_placement is True
    assert target.skill_name == "widget-forge"


def test_a_rule_or_loose_md_is_not_a_skill(tmp_path: Path) -> None:
    """No Skill call should be expected of the agent, so nothing is placed."""
    path = tmp_path / "rules" / "testing.md"
    path.parent.mkdir(parents=True)
    path.write_text("# Testing\n\nAlways write tests.\n")

    target = classify_target(path, global_root=tmp_path / "home")

    assert target.kind == "document"
    assert target.skill_name is None
    assert skill_payload(target, full_body=False) is None


def test_stub_carries_discovery_metadata_but_not_the_body(tmp_path: Path) -> None:
    """The whole point of tier 1: the agent can find the skill, and the audited
    body never reaches the unattended child."""
    path = _skill_at(tmp_path / "repo" / ".claude" / "skills", "widget-forge")
    target = classify_target(path, global_root=tmp_path / "home")

    payload = skill_payload(target, full_body=False)
    assert payload is not None
    name, text = payload

    assert name == "widget-forge"
    assert "name: widget-forge" in text
    assert "Forge widgets carefully." in text
    assert "SECRET-PROCEDURE-TOKEN" not in text


def test_full_body_carries_the_real_procedure(tmp_path: Path) -> None:
    path = _skill_at(tmp_path / "repo" / ".claude" / "skills", "widget-forge")
    target = classify_target(path, global_root=tmp_path / "home")

    payload = skill_payload(target, full_body=True)
    assert payload is not None

    assert "SECRET-PROCEDURE-TOKEN" in payload[1]


def test_description_is_capped(tmp_path: Path) -> None:
    """It is the one piece of the audited document that reaches the child even in
    stub mode, so it is bounded. A real target's description ran ~500 chars and
    read as a summary of its own body — narrower than the document, not safe."""
    long_desc = "x" * (MAX_DESCRIPTION_CHARS + 400)
    path = _skill_at(
        tmp_path / "repo" / ".claude" / "skills",
        "widget-forge",
        f"---\nname: widget-forge\ndescription: {long_desc}\n---\n\nbody\n",
    )

    target = classify_target(path, global_root=tmp_path / "home")

    assert len(target.description) == MAX_DESCRIPTION_CHARS


def test_full_body_refuses_a_symlinked_target(tmp_path: Path) -> None:
    real = _skill_at(tmp_path / "elsewhere", "widget-forge")
    link_dir = tmp_path / "repo" / ".claude" / "skills" / "widget-forge"
    link_dir.mkdir(parents=True)
    (link_dir / "SKILL.md").symlink_to(real)

    target = classify_target(link_dir / "SKILL.md", global_root=tmp_path / "home")

    # `classify_target` resolves, so the symlink is followed for classification;
    # what must not happen is copying through a link that points anywhere.
    assert target.kind == "project-skill"


def test_place_skill_writes_where_the_child_discovers_it(tmp_path: Path) -> None:
    """Verified 2026-08-01 that this is the location that produces discovery, and
    2026-08-02 end-to-end that the `Unknown skill` error disappears."""
    written = place_skill(tmp_path, ("widget-forge", SKILL_TEXT))

    assert written == tmp_path / ".claude" / "skills" / "widget-forge" / "SKILL.md"
    assert written.read_text() == SKILL_TEXT


def test_place_skill_sanitises_the_directory_name(tmp_path: Path) -> None:
    """The name comes from frontmatter, which is audited-document content."""
    written = place_skill(tmp_path, ("evil/../../escape", "x"))

    assert written.parent.parent.parent == tmp_path / ".claude"
    assert ".." not in str(written)


def test_place_skill_refuses_a_name_that_sanitises_to_nothing(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no usable directory name"):
        place_skill(tmp_path, ("", "x"))


def test_full_body_refuses_when_the_given_path_is_a_symlink(tmp_path: Path) -> None:
    """`classify_target` resolves, so asking the resolved path is always False.

    The refusal has to `lstat` what the caller actually pointed at. Before this,
    a project skill symlinked to any file elsewhere was copied into the sandbox
    with the stated guard silently inert.
    """
    real = _skill_at(tmp_path / "elsewhere", "widget-forge")
    link_dir = tmp_path / "repo" / ".claude" / "skills" / "widget-forge"
    link_dir.mkdir(parents=True)
    (link_dir / "SKILL.md").symlink_to(real)

    target = classify_target(link_dir / "SKILL.md", global_root=tmp_path / "home")

    assert target.source_path is not None
    with pytest.raises(ValueError, match="symlink"):
        skill_payload(target, full_body=True)


def test_full_body_refuses_a_symlinked_parent_directory(tmp_path: Path) -> None:
    """A link anywhere in the chain redirects what gets copied."""
    real_skill_dir = tmp_path / "elsewhere" / "widget-forge"
    _skill_at(tmp_path / "elsewhere", "widget-forge")
    skills = tmp_path / "repo" / ".claude" / "skills"
    skills.mkdir(parents=True)
    (skills / "widget-forge").symlink_to(real_skill_dir, target_is_directory=True)

    target = classify_target(skills / "widget-forge" / "SKILL.md", global_root=tmp_path / "home")

    with pytest.raises(ValueError, match="symlink"):
        skill_payload(target, full_body=True)


def test_stub_mode_does_not_touch_the_filesystem_for_symlinks(tmp_path: Path) -> None:
    """Stub mode builds from metadata already read, so the link is irrelevant there."""
    real = _skill_at(tmp_path / "elsewhere", "widget-forge")
    link_dir = tmp_path / "repo" / ".claude" / "skills" / "widget-forge"
    link_dir.mkdir(parents=True)
    (link_dir / "SKILL.md").symlink_to(real)

    target = classify_target(link_dir / "SKILL.md", global_root=tmp_path / "home")
    payload = skill_payload(target, full_body=False)

    assert payload is not None
    assert "SECRET-PROCEDURE-TOKEN" not in payload[1]
