"""Tests for the reader-cut pilot tooling (plan: docs/plans/reader-cut-pilot.html)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import reader_cut, reader_cut_run, reader_cut_score
from scripts.reader_cut_units import extract_units, units_record

ARTICLE = """---
title: "t"
published: true
---

導入の一文です。二文目は
行をまたぎます。

## 節A

:::message
注意の箱です。
:::

- 箇条の項目です。
- 二つ目

| 表 | です |
|---|---|
| a | b |

```text
コードの中。です。
```

![図](x.png)

<p>HTML の行。</p>

> 引用の文です。

終わりのない残り

### 節B

最後の文です！
"""


@pytest.mark.unit
class TestUnits:
    def test_units_in_reading_order(self) -> None:
        texts = [(u.kind, u.text, u.section) for u in extract_units(ARTICLE)]
        assert texts == [
            ("sentence", "導入の一文です。", 0),
            ("sentence", "二文目は行をまたぎます。", 0),
            ("sentence", "注意の箱です。", 1),
            ("item", "箇条の項目です。", 1),
            ("item", "二つ目", 1),
            ("sentence", "引用の文です。", 1),
            ("sentence", "終わりのない残り", 1),
            ("sentence", "最後の文です！", 2),
        ]

    def test_wrapped_sentence_reports_its_first_line(self) -> None:
        u = extract_units(ARTICLE)[1]
        assert u.line == 6

    def test_indices_are_dense(self) -> None:
        assert [u.i for u in extract_units(ARTICLE)] == list(range(8))

    def test_code_table_html_image_never_become_units(self) -> None:
        joined = " ".join(u.text for u in extract_units(ARTICLE))
        for absent in ("コードの中", "表", "HTML の行", "図", ":::"):
            assert absent not in joined

    def test_source_under_home_is_written_home_relative(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # the units JSON is published with the harness; an absolute home path aborts the sync
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        src = tmp_path / "MyAI_Lab" / "a.md"
        src.parent.mkdir()
        src.write_text(ARTICLE)
        assert units_record(src, "a")["source"] == "~/MyAI_Lab/a.md"

    def test_source_outside_home_stays_as_given(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(Path, "home", lambda: tmp_path / "home")
        src = tmp_path / "a.md"
        src.write_text(ARTICLE)
        assert units_record(src, "a")["source"] == str(src)


def _units(spec: list[tuple[int, int, str]]) -> list[dict]:
    return [{"i": i, "section": s, "text": t} for i, s, t in spec]


UNITS = _units([(0, 0, "一。"), (1, 0, "二。"), (2, 1, "三。"), (3, 2, "四。")])
TEMPLATE = "R:{reader}\n{context}U:\n{units}\n"


@pytest.mark.unit
class TestPrompts:
    def test_full_view_asks_every_unit_once(self) -> None:
        arm = reader_cut_run.Arm("A2", "e.md", "full", "claude", "sonnet")
        prompts = reader_cut_run.build_prompts(UNITS, arm, TEMPLATE, "読者")
        assert len(prompts) == 1
        asked, text = prompts[0]
        assert asked == [0, 1, 2, 3]
        assert "R:読者" in text and "ここまでに読んだ" not in text
        assert "2\t三。" in text

    def test_forward_view_shows_only_earlier_sections_as_context(self) -> None:
        arm = reader_cut_run.Arm("A3", "e.md", "forward", "claude", "sonnet")
        prompts = reader_cut_run.build_prompts(UNITS, arm, TEMPLATE, "読者")
        assert [asked for asked, _ in prompts] == [[0, 1], [2], [3]]
        _, second = prompts[1]
        assert "ここまでに読んだ部分" in second
        assert "一。" in second and "四。" not in second
        assert "U:\n2\t三。" in second

    def test_unknown_view_raises(self) -> None:
        arm = reader_cut_run.Arm("X", "", "sideways", "claude", "")
        with pytest.raises(ValueError):
            reader_cut_run.build_prompts(UNITS, arm, TEMPLATE, "r")

    def test_placeholder_reader_stops_the_run(self, tmp_path: Path) -> None:
        (tmp_path / "p.md").write_text("{{TODO: 判断役が書く}}\n")
        arm = reader_cut_run.Arm("A1", "p.md", "full", "claude", "")
        with pytest.raises(reader_cut_run.ReaderNotReady):
            reader_cut_run.reader_text(arm, tmp_path)

    def test_empty_reader_means_no_reader(self, tmp_path: Path) -> None:
        arm = reader_cut_run.Arm("A0", "", "full", "claude", "")
        assert "指定なし" in reader_cut_run.reader_text(arm, tmp_path)

    def test_repo_arms_form_the_planned_ladder(self) -> None:
        arms = reader_cut_run.load_arms(reader_cut.PROMPT / "arms.toml")
        assert sorted(arms) == ["A0", "A1", "A2", "A3", "A4"]
        a1, a2, a3, a4 = arms["A1"], arms["A2"], arms["A3"], arms["A4"]
        assert (a1.view, a1.runner) == (a2.view, a2.runner) and a1.reader != a2.reader
        assert (a2.reader, a2.runner) == (a3.reader, a3.runner) and a3.view == "forward"
        assert (a2.reader, a2.view) == (a4.reader, a4.view) and a4.runner == "codex"
        assert arms["A0"].reader == ""


@pytest.mark.unit
class TestParseRows:
    def test_rows_with_preamble_and_spaces(self) -> None:
        text = "以下が判定です。\n0\tCUT\t読者は知っている\n1 PRESERVE 要る\n"
        rows = reader_cut_run.parse_rows(text, [0, 1])
        assert rows == {0: ("CUT", "読者は知っている"), 1: ("PRESERVE", "要る")}

    @pytest.mark.parametrize(
        "text",
        ["0\tCUT\ta\n", "0\tCUT\ta\n1\tCUT\tb\n2\tCUT\tc\n", "0\tCUT\ta\n0\tCUT\ta\n1\tCUT\tb\n"],
        ids=["missing", "unexpected", "duplicate"],
    )
    def test_incomplete_answers_fail_loud(self, text: str) -> None:
        with pytest.raises(reader_cut_run.ParseError):
            reader_cut_run.parse_rows(text, [0, 1])

    def test_empty_output_fails_loud(self) -> None:
        with pytest.raises(reader_cut_run.ParseError):
            reader_cut_run.parse_rows("", [0])


MARKS = {"t#0": "skip", "t#1": "skip", "t#2": None, "t#3": "stop", "t#4": None}
TEXTS = {
    "t#0": "要らない文。",
    "t#1": "これも。",
    "t#2": "3 回だけ動く。",
    "t#3": "要る。",
    "t#4": "普通。",
}


@pytest.mark.unit
class TestScore:
    def test_metrics_on_a_known_case(self) -> None:
        verdicts = {"t#0": "CUT", "t#1": "PRESERVE", "t#2": "CUT", "t#3": "CUT", "t#4": "CONDENSE"}
        s = reader_cut_score.score_run("A2", "run1", MARKS, TEXTS, verdicts)
        assert s.cut == 3
        assert s.precision == pytest.approx(1 / 3)
        assert s.recall == pytest.approx(1 / 2)
        assert s.lift == pytest.approx((1 / 3) / (2 / 5))
        assert s.stop_cut == 1
        assert s.protected_violations == 1  # "3 回だけ" cut, author did not mark it
        assert s.chars_cut == len("要らない文。") + len("3 回だけ動く。") + len("要る。")

    def test_no_cut_gives_no_precision(self) -> None:
        verdicts = dict.fromkeys(MARKS, "PRESERVE")
        s = reader_cut_score.score_run("A0", "run1", MARKS, TEXTS, verdicts)
        assert (s.cut, s.precision, s.lift) == (0, None, None)

    def test_verdicts_must_cover_the_labels(self) -> None:
        with pytest.raises(ValueError):
            reader_cut_score.score_run("A0", "run1", MARKS, TEXTS, {"t#0": "CUT"})

    def test_run_agreement_is_jaccard_of_cuts(self) -> None:
        a = {"x": "CUT", "y": "CUT", "z": "PRESERVE"}
        b = {"x": "CUT", "y": "PRESERVE", "z": "CUT"}
        assert reader_cut_score.run_agreement(a, b) == pytest.approx(1 / 3)
        none = dict.fromkeys(a, "PRESERVE")
        assert reader_cut_score.run_agreement(none, none) is None

    def test_summary_averages_runs(self) -> None:
        r1 = reader_cut_score.RunScore("A1", "run1", 2, 0.5, 0.5, 1.25, 0, 0, 10)
        r2 = reader_cut_score.RunScore("A1", "run2", 4, None, 1.0, None, 2, 1, 30)
        (row,) = reader_cut_score.summarize([r1, r2], {"A1": 0.5})
        assert row["cut"] == 3 and row["precision"] == 0.5 and row["recall"] == 0.75
        assert row["run_agreement"] == 0.5
        table = reader_cut_score.render_table(1, MARKS, 30, [row])
        assert "基準率 b = 0.400" in table and table.splitlines()[-1].startswith("A1")


@pytest.mark.integration
def test_pipeline_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data, prompt = tmp_path / "data", tmp_path / "prompt"
    (data / "page").mkdir(parents=True)
    prompt.mkdir()
    real = reader_cut.ROOT
    (data / "page" / "template.html").write_text(
        (real / "evals/reader-cut/page/template.html").read_text()
    )
    (prompt / "cutter.md").write_text((real / "prompt/cutter.md").read_text())
    (prompt / "arms.toml").write_text((real / "prompt/arms.toml").read_text())
    (prompt / "evidence.md").write_text("著者の発話の抜粋。\n")
    monkeypatch.setattr(reader_cut, "DATA", data)
    monkeypatch.setattr(reader_cut, "PROMPT", prompt)
    src = tmp_path / "a.md"
    src.write_text(ARTICLE)

    assert reader_cut.main(["split", str(src), "--text-id", "a"]) == 0
    assert reader_cut.main(["page"]) == 0
    page = (data / "page" / "marking.html").read_text()
    assert '"text_id": "a"' in page and "__DATA__" not in page

    sha = json.loads((data / "units" / "a.json").read_text())["sha256"]
    export = tmp_path / "export.json"
    export.write_text(
        json.dumps([{"id": "a", "data": {"sha256": sha, "marks": {"0": "skip", "5": "stop"}}}])
    )
    assert reader_cut.main(["ingest", str(export)]) == 0

    def fake(arm: reader_cut_run.Arm, text: str) -> str:
        asked = [
            int(line.split("\t")[0])
            for line in text.split("番号付き）\n")[1].splitlines()
            if line[:1].isdigit()
        ]
        return "\n".join(f"{i}\t{'CUT' if i == 0 else 'PRESERVE'}\tr" for i in asked)

    for run in ("1", "2"):
        args = reader_cut.argparse.Namespace(arm="A2", run=run, text=None, dry_run=False)
        assert reader_cut.cmd_run(args, runner=fake) == 0
    assert reader_cut.main(["score"]) == 0
    score = json.loads((data / "results" / "score.json").read_text())
    (row,) = score["arms"]
    assert row["arm"] == "A2" and row["precision"] == 1.0 and row["run_agreement"] == 1.0


@pytest.mark.integration
def test_ingest_refuses_a_changed_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = tmp_path / "data"
    monkeypatch.setattr(reader_cut, "DATA", data)
    src = tmp_path / "a.md"
    src.write_text(ARTICLE)
    reader_cut.main(["split", str(src), "--text-id", "a"])
    export = tmp_path / "e.json"
    export.write_text(json.dumps({"a": {"sha256": "0" * 64, "marks": {}}}))
    with pytest.raises(SystemExit):
        reader_cut.main(["ingest", str(export)])


@pytest.mark.unit
class TestIsolation:
    def test_claude_child_gets_no_user_context_and_no_tools(self) -> None:
        arm = reader_cut_run.Arm("A2", "e.md", "full", "claude", "sonnet")
        cmd = reader_cut_run.claude_command(arm, "P")
        assert cmd[:3] == ["claude", "-p", "P"]
        assert "--safe-mode" in cmd and "--strict-mcp-config" in cmd
        assert cmd[cmd.index("--tools") + 1] == ""
        assert cmd[cmd.index("--model") + 1] == "sonnet"

    def test_codex_child_is_read_only_and_ephemeral(self, tmp_path: Path) -> None:
        arm = reader_cut_run.Arm("A4", "e.md", "full", "codex", "")
        cmd = reader_cut_run.codex_command(arm, tmp_path / "o.txt")
        assert cmd[:2] == ["codex", "exec"] and "--model" not in cmd
        assert cmd[cmd.index("--sandbox") + 1] == "read-only" and "--ephemeral" in cmd
        assert cmd[-3:] == ["-o", str(tmp_path / "o.txt"), "-"]


@pytest.mark.unit
def test_wrapped_latin_words_keep_their_space() -> None:
    (u,) = extract_units("Claude\nCode を使う。\n")
    assert u.text == "Claude Code を使う。"


@pytest.mark.unit
def test_export_ids_may_carry_the_collection_prefix() -> None:
    docs = reader_cut._export_docs([{"id": "marks/a", "data": {"x": 1}}])
    assert docs == {"a": {"x": 1}}


@pytest.mark.integration
def test_page_escapes_every_angle_bracket(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    data = tmp_path / "data"
    (data / "page").mkdir(parents=True)
    (data / "page" / "template.html").write_text(
        '<script type="application/json" id="data">__DATA__</script><script>main()</script>'
    )
    monkeypatch.setattr(reader_cut, "DATA", data)
    src = tmp_path / "a.md"
    src.write_text("本文に <!-- と </script> と <script> がある。\n")
    reader_cut.main(["split", str(src), "--text-id", "a"])
    reader_cut.main(["page"])
    page = (data / "page" / "marking.html").read_text()
    assert page.count("<script") == 2 and page.count("</script>") == 2
    assert "<!--" not in page


@pytest.mark.integration
def test_score_refuses_results_from_another_version(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = tmp_path / "data"
    monkeypatch.setattr(reader_cut, "DATA", data)
    rec = {"text_id": "a", "sha256": "1" * 64, "units": [{"i": 0, "text": "一。", "mark": "skip"}]}
    (data / "labels").mkdir(parents=True)
    (data / "labels" / "a.json").write_text(json.dumps(rec))
    run_dir = data / "results" / "A0" / "run1"
    run_dir.mkdir(parents=True)
    (run_dir / "a.tsv").write_text("0\tCUT\tr\n")
    (run_dir / "a.meta.json").write_text(json.dumps({"sha256": "2" * 64}))
    with pytest.raises(SystemExit):
        reader_cut.main(["score"])


@pytest.mark.unit
def test_badge_lines_and_emphasis_are_not_text() -> None:
    md = (
        "[![DOI](https://x/b.svg)](https://doi.org/1) [![License: MIT](https://x/l.svg)](LICENSE)\n\n"
        "**太字の主張です。** `snake_case` は残す。\n"
    )
    assert [u.text for u in extract_units(md)] == ["太字の主張です。", "`snake_case` は残す。"]
