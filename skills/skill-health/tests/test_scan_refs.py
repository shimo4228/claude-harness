"""Tests for scan_refs — structural reference-existence scanner for SKILL.md files.

These cover the *structural* "missing artifacts" debt pattern (SkillOps,
arXiv:2605.13716): a SKILL.md names a script / bash file / agent / sibling
skill that does not exist on disk. This is decidable from the literal shape of
the Markdown plus a filesystem `exists()` check — 100% code-owned accuracy, no
LLM judgment (Agent Knowledge Cycle ADR-0008 Code-LLM Layering). Semantic
debt (over-specialized, trigger↔body drift) is NOT tested here; it is delegated
to a holistic pass in the skill body, never scored.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.scan_refs import (
    Reference,
    dangling,
    extract_agent_refs,
    extract_bash_scripts,
    extract_md_links,
    extract_references,
    extract_run_modules,
    main,
    render_json,
    render_report,
    scan_root,
    scan_skill,
)


def _write_skill(skill_dir: Path, body: str) -> Path:
    skill_dir.mkdir(parents=True, exist_ok=True)
    md = skill_dir / "SKILL.md"
    md.write_text(body, encoding="utf-8")
    return md


@pytest.mark.unit
class TestExtractRunModules:
    def test_plain_python_m_module(self) -> None:
        refs = extract_run_modules("run `python -m scripts.run` to start\n", "foo", Path("/s/foo"))
        assert len(refs) == 1
        assert refs[0].ref_type == "run_module"
        assert refs[0].target == str(Path("/s/foo/scripts/run.py"))
        assert refs[0].line == 1

    def test_uv_run_prefix(self) -> None:
        md = "```bash\nuv run python -m scripts.spec_generator --dry-run\n```\n"
        refs = extract_run_modules(md, "foo", Path("/s/foo"))
        assert [r.target for r in refs] == [str(Path("/s/foo/scripts/spec_generator.py"))]
        assert refs[0].line == 2

    def test_dotted_submodule_maps_to_nested_path(self) -> None:
        refs = extract_run_modules("python -m scripts.sub.mod\n", "foo", Path("/s/foo"))
        assert refs[0].target == str(Path("/s/foo/scripts/sub/mod.py"))

    def test_directory_override_is_skipped(self) -> None:
        # `--directory D` changes the cwd, so scripts.X no longer resolves to the
        # skill dir; skip rather than emit a false positive.
        md = "uv run --directory ../other python -m scripts.run\n"
        assert extract_run_modules(md, "foo", Path("/s/foo")) == []

    def test_records_raw_text(self) -> None:
        refs = extract_run_modules("python -m scripts.run\n", "foo", Path("/s/foo"))
        assert "scripts.run" in refs[0].raw

    def test_metavariable_module_skipped(self) -> None:
        # Regression (dogfood): a SKILL.md documenting the pattern
        # `python -m scripts.X` uses X as a metavariable, not a real module.
        assert extract_run_modules("`python -m scripts.X`\n", "foo", Path("/s/foo")) == []


@pytest.mark.unit
class TestExtractBashScripts:
    def test_home_expanded_path(self) -> None:
        md = "bash ~/.claude/skills/hf-sync/sync.sh\n"
        refs = extract_bash_scripts(md, "foo", Path("/s/foo"))
        assert len(refs) == 1
        assert refs[0].ref_type == "bash_script"
        assert refs[0].target == str(Path.home() / ".claude/skills/hf-sync/sync.sh")

    def test_relative_path_resolves_against_skill_dir(self) -> None:
        refs = extract_bash_scripts("bash ./scripts/build.sh\n", "foo", Path("/s/foo"))
        assert refs[0].target == str(Path("/s/foo/scripts/build.sh"))

    def test_absolute_path_used_as_is(self) -> None:
        refs = extract_bash_scripts("bash /opt/tools/run.sh\n", "foo", Path("/s/foo"))
        assert refs[0].target == "/opt/tools/run.sh"

    def test_non_sh_command_ignored(self) -> None:
        assert extract_bash_scripts("bash -c 'echo hi'\n", "foo", Path("/s/foo")) == []

    def test_angle_bracket_placeholder_skipped(self) -> None:
        # Regression: `bash <公開repo>/scripts/x.sh` is a doc template slot, not
        # a real path — must not be reported as a missing artifact.
        md = "bash <公開repo>/scripts/sync-from-local.sh --dry-run\n"
        assert extract_bash_scripts(md, "foo", Path("/s/foo")) == []

    def test_ellipsis_path_skipped(self) -> None:
        # Regression (dogfood): `bash …/x.sh` in prose documents the pattern;
        # the ellipsis marks a placeholder path.
        assert extract_bash_scripts("`bash …/x.sh`\n", "foo", Path("/s/foo")) == []


@pytest.mark.unit
class TestExtractAgentRefs:
    def test_explicit_agent_path(self) -> None:
        refs = extract_agent_refs("see `~/.claude/agents/code-reviewer.md`\n", "foo")
        assert len(refs) == 1
        assert refs[0].ref_type == "agent"
        assert refs[0].target == str(Path.home() / ".claude/agents/code-reviewer.md")

    def test_prose_agent_name_is_not_matched(self) -> None:
        # Conservative: bare prose names ("the code-reviewer agent") are too
        # ambiguous to resolve and must not be flagged.
        assert extract_agent_refs("invoke the code-reviewer agent\n", "foo") == []

    def test_metavariable_agent_skipped(self) -> None:
        # Regression (dogfood): `~/.claude/agents/X.md` documents the pattern
        # with X as a metavariable.
        assert extract_agent_refs("`~/.claude/agents/X.md`\n", "foo") == []


@pytest.mark.unit
class TestExtractMdLinks:
    def test_relative_doc_link(self) -> None:
        refs = extract_md_links("see [refs](./reference/x.md)\n", "foo", Path("/s/foo"))
        assert refs[0].ref_type == "md_link"
        assert refs[0].target == str(Path("/s/foo/reference/x.md"))

    def test_sibling_skill_link(self) -> None:
        refs = extract_md_links("[wcwl](../when-code-when-llm/SKILL.md)\n", "foo", Path("/s/foo"))
        assert refs[0].target == str(Path("/s/foo/../when-code-when-llm/SKILL.md"))

    def test_external_url_skipped(self) -> None:
        assert extract_md_links("[site](https://example.com/x)\n", "foo", Path("/s/foo")) == []

    def test_link_inside_code_fence_skipped(self) -> None:
        md = "```\n[x](./missing.md)\n```\n"
        assert extract_md_links(md, "foo", Path("/s/foo")) == []

    def test_fragment_is_stripped(self) -> None:
        refs = extract_md_links("[a](./doc.md#section)\n", "foo", Path("/s/foo"))
        assert refs[0].target == str(Path("/s/foo/doc.md"))

    def test_site_absolute_path_skipped(self) -> None:
        assert extract_md_links("[a](/docs/x.md)\n", "foo", Path("/s/foo")) == []

    def test_placeholder_href_url_skipped(self) -> None:
        # Regression: `[](url)` inside an inline-code example — "url" has no path
        # separator and no extension, so it is a placeholder, not a file ref.
        assert extract_md_links("`[](url)` stays literal\n", "foo", Path("/s/foo")) == []

    def test_ellipsis_href_skipped(self) -> None:
        # Regression: `[日本語](...)` — ellipsis placeholder, not a real link.
        assert extract_md_links("`[日本語](...)` example\n", "foo", Path("/s/foo")) == []

    def test_angle_bracket_href_skipped(self) -> None:
        assert extract_md_links("[x](<your-path>/y.md)\n", "foo", Path("/s/foo")) == []

    def test_extensionless_link_is_existence_checked(self) -> None:
        # Regression (reviewer MEDIUM): a bare extensionless target with a real
        # label (`[log](CHANGELOG)`) is NOT a placeholder — it must produce a
        # reference so existence is checked, not silently suppressed.
        refs = extract_md_links("[log](CHANGELOG)\n", "foo", Path("/s/foo"))
        assert len(refs) == 1
        assert refs[0].target == str(Path("/s/foo/CHANGELOG"))


@pytest.mark.unit
class TestExtractReferences:
    def test_collects_all_ref_types(self) -> None:
        md = (
            "# foo\n"
            "run `python -m scripts.run`\n"
            "bash ~/.claude/scripts/x.sh\n"
            "see [doc](./reference/y.md)\n"
        )
        kinds = {r.ref_type for r in extract_references(md, "foo", Path("/s/foo"))}
        assert kinds == {"run_module", "bash_script", "md_link"}


@pytest.mark.unit
class TestDangling:
    def test_existing_target_is_not_dangling(self, tmp_path: Path) -> None:
        (tmp_path / "scripts").mkdir()
        (tmp_path / "scripts" / "run.py").write_text("x", encoding="utf-8")
        ref = Reference("foo", "run_module", "scripts.run", str(tmp_path / "scripts/run.py"), 1)
        assert dangling([ref]) == []

    def test_missing_target_is_dangling(self, tmp_path: Path) -> None:
        ref = Reference("foo", "run_module", "scripts.gone", str(tmp_path / "scripts/gone.py"), 1)
        assert dangling([ref]) == [ref]

    def test_run_module_package_form_counts_as_existing(self, tmp_path: Path) -> None:
        # `python -m scripts.pkg` resolves to scripts/pkg/__init__.py too.
        pkg = tmp_path / "scripts" / "pkg"
        pkg.mkdir(parents=True)
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        ref = Reference("foo", "run_module", "scripts.pkg", str(tmp_path / "scripts/pkg.py"), 1)
        assert dangling([ref]) == []


@pytest.mark.integration
class TestScanSkill:
    def test_reports_only_missing_refs(self, tmp_path: Path) -> None:
        skill = tmp_path / "skills" / "demo"
        (skill / "scripts").mkdir(parents=True)
        (skill / "scripts" / "present.py").write_text("x", encoding="utf-8")
        md = _write_skill(
            skill,
            "# demo\n"
            "uv run python -m scripts.present\n"  # exists
            "uv run python -m scripts.gone\n",  # missing
        )
        result = scan_skill(md)
        assert [r.target for r in result] == [str(skill / "scripts" / "gone.py")]

    def test_healthy_skill_returns_empty(self, tmp_path: Path) -> None:
        skill = tmp_path / "skills" / "demo"
        (skill / "reference").mkdir(parents=True)
        (skill / "reference" / "guide.md").write_text("x", encoding="utf-8")
        md = _write_skill(skill, "# demo\nsee [guide](./reference/guide.md)\n")
        assert scan_skill(md) == []


@pytest.mark.integration
class TestScanRoot:
    def test_scans_every_skill_under_root(self, tmp_path: Path) -> None:
        good = tmp_path / "good"
        (good / "scripts").mkdir(parents=True)
        (good / "scripts" / "ok.py").write_text("x", encoding="utf-8")
        _write_skill(good, "# good\npython -m scripts.ok\n")
        bad = tmp_path / "bad"
        _write_skill(bad, "# bad\npython -m scripts.missing\n")
        result = scan_root(tmp_path)
        skills_with_debt = {r.skill for r in result}
        assert skills_with_debt == {"bad"}

    def test_empty_root_is_clean(self, tmp_path: Path) -> None:
        assert scan_root(tmp_path) == []


@pytest.mark.unit
class TestRender:
    def test_report_lists_dangling(self) -> None:
        refs = [Reference("bad", "run_module", "scripts.x", "/s/bad/scripts/x.py", 4)]
        text = render_report(refs, scanned=3)
        assert "bad" in text
        assert "scripts/x.py" in text or "scripts.x" in text

    def test_clean_report_says_so(self) -> None:
        assert "no" in render_report([], scanned=5).lower()

    def test_report_has_no_quality_score(self) -> None:
        """Structural scan must never emit a quality score (ADR-0008)."""
        refs = [Reference("bad", "agent", "~/.claude/agents/x.md", "/h/x.md", 2)]
        text = render_report(refs, scanned=1).lower()
        for forbidden in ("score", "/10", "/100", "rating", "grade"):
            assert forbidden not in text

    def test_json_is_valid_and_has_counts(self) -> None:
        refs = [Reference("bad", "run_module", "scripts.x", "/s/bad/scripts/x.py", 4)]
        data = json.loads(render_json(refs, scanned=3))
        assert data["scanned"] == 3
        assert data["dangling_count"] == 1
        assert data["dangling"][0]["skill"] == "bad"
        assert data["dangling"][0]["ref_type"] == "run_module"


@pytest.mark.integration
class TestCli:
    def test_clean_root_returns_zero(self, tmp_path: Path) -> None:
        skill = tmp_path / "demo"
        (skill / "scripts").mkdir(parents=True)
        (skill / "scripts" / "ok.py").write_text("x", encoding="utf-8")
        _write_skill(skill, "# demo\npython -m scripts.ok\n")
        assert main([str(tmp_path)]) == 0

    def test_dangling_returns_one(self, tmp_path: Path) -> None:
        _write_skill(tmp_path / "demo", "# demo\npython -m scripts.gone\n")
        assert main([str(tmp_path)]) == 1

    def test_missing_root_returns_two(self, tmp_path: Path) -> None:
        assert main([str(tmp_path / "nope")]) == 2

    def test_json_flag_emits_json(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _write_skill(tmp_path / "demo", "# demo\npython -m scripts.gone\n")
        main([str(tmp_path), "--json"])
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["dangling_count"] == 1
        assert parsed["scanned"] == 1
