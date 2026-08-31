"""Golden: readme_evidence.py の stdout JSON 全形を凍結する。

個別フィールドの意味は test_readme_evidence.py が主張する。こちらが検知するのは
「意味テストは通るが、readme-judge が読む正確な形（キー順・インデント・数値の丸め）
が変わった」silent drift。judge は fresh context でこの JSON だけを証拠に裁くので、
形の変化は判定の変化に直結する。

更新規約: ~/.claude/tests/golden/README.md（タスクが出力変更を宣言しているときだけ更新）。
再生成: uv run --project . python scripts/readme_evidence.py fixtures/<name>.md \
        > tests/golden/<name>.json
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.readme_evidence import main

SKILL_ROOT = Path(__file__).parent.parent
GOLDEN = Path(__file__).parent / "golden"


@pytest.mark.unit
@pytest.mark.parametrize("name", ["sample_clean", "sample_issues"])
def test_stdout_json_matches_golden(
    name: str, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # path は引数がそのまま echo される — 相対パスで呼んで出力を環境非依存にする
    monkeypatch.chdir(SKILL_ROOT)
    rc = main([f"fixtures/{name}.md"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out == (GOLDEN / f"{name}.json").read_text(encoding="utf-8")
