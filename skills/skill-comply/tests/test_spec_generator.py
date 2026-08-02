"""Tests for spec_generator — save_to persistence for --spec reuse."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.parser import parse_spec
from scripts.spec_generator import generate_spec

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _claude_stdout() -> MagicMock:
    result = MagicMock()
    result.returncode = 0
    result.stdout = (FIXTURES / "tdd_spec.yaml").read_text()
    result.stderr = ""
    return result


@patch("scripts.spec_generator.subprocess.run", return_value=_claude_stdout())
def test_save_to_persists_spec_yaml(mock_run, tmp_path) -> None:
    """save_to keeps the raw generated YAML, reloadable via parse_spec."""
    save_path = tmp_path / "results" / "x.spec.yaml"

    spec = generate_spec(FIXTURES / "tdd_spec.yaml", save_to=save_path)

    assert save_path.exists()
    reloaded = parse_spec(save_path)
    assert reloaded == spec


@patch("scripts.spec_generator.subprocess.run", return_value=_claude_stdout())
def test_no_save_to_leaves_no_tempfile(mock_run, tmp_path, monkeypatch) -> None:
    """Without save_to, the intermediate tempfile is removed (legacy behavior)."""
    monkeypatch.setenv("TMPDIR", str(tmp_path))

    spec = generate_spec(FIXTURES / "tdd_spec.yaml")

    assert spec.id == "tdd-workflow"
    assert list(tmp_path.glob("*.yaml")) == []
