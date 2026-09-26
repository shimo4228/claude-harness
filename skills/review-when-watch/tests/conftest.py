"""Shared fixtures: a fake Jev, a miniature harness tree and a reports directory.

No test touches the network. The fake answers from what it was sent, so a test states the
rule ("reports containing HIT satisfy RFC-0001") instead of queueing one response per call.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from scripts.judge import MODEL

REPO_ROOT = Path(__file__).resolve().parents[3]
NOW = dt.datetime(2026, 9, 25, 9, 0, tzinfo=dt.timezone(dt.timedelta(hours=9)))


class FakeJev:
    def __init__(self, hit_rule=None, fail_rule=None, model=MODEL, canary=(0.9, 0.1)):
        self.hit_rule = hit_rule or (lambda condition, report: False)
        self.fail_rule = fail_rule or (lambda condition, report: False)
        self.model = model
        self.canary = canary
        self.calls: list[dict] = []

    def ask(self, state, questions, *, model, timeout):
        self.calls.append({"state": state, "questions": questions, "model": model})
        condition, report = state["condition"], state["report"]
        if self.fail_rule(condition, report):
            raise RuntimeError("HTTP 500")
        if report.startswith("canary-positive.md"):
            met = self.canary[0]
        elif report.startswith("canary-negative.md"):
            met = self.canary[1]
        else:
            met = 0.93 if self.hit_rule(condition, report) else 0.12
        overlap = {"words_only": 0.1, "same_area": 0.2, "precursor": 0.1, "event": 0.6}
        if met < 0.5:
            overlap = {"words_only": 0.7, "same_area": 0.2, "precursor": 0.05, "event": 0.05}
        return {
            "model": self.model,
            "answers": {
                "met": {"type": "noul", "noul": met},
                "overlap": {
                    "type": "choice",
                    "choice": max(overlap.items(), key=lambda kv: kv[1])[0],
                    "probabilities": overlap,
                },
            },
            "usage": {"input_tokens": 100, "output_tokens": 0},
        }


RFC_README = """# RFCs

| # | Title |
|---|---|
| [0001](0001-first.md) | 最初の提案 |
| [0002](0002-second.md) | 二つ目 |
| [0003](0003-third.md) | 三つ目 |
"""

RFC_0001 = """---
state: done 2026-08-25
review-when: substrate が skill listing の注入方式を変えた時
---

## Summary
"""

RFC_0002 = """---
state: draft 2026-09-14
---

## Summary
"""

RFC_0003 = """---
state: blocked 2026-09-20
review-when: "影の比率が 30% を \\"超えた\\" とき"
---
"""

ADR_0044 = """# ADR-0044: 日付つき仮説として持つ

## Status

accepted

## Context

x

## Review-when

- substrate が決定記録の鮮度管理を native に持ったら

## Consequences

y
"""

ADR_0045 = """# ADR-0045: 退役した判断

## Status

superseded by ADR-0050

## Review-when

- 何か
"""

ADR_0046 = """# ADR-0046: 条件なし

## Status

accepted

## Review-when

無し
"""


@pytest.fixture
def harness(tmp_path: Path) -> Path:
    root = tmp_path / "harness"
    (root / "rfcs").mkdir(parents=True)
    (root / "docs" / "adr").mkdir(parents=True)
    (root / "rfcs" / "README.md").write_text(RFC_README, encoding="utf-8")
    (root / "rfcs" / "0001-first.md").write_text(RFC_0001, encoding="utf-8")
    (root / "rfcs" / "0002-second.md").write_text(RFC_0002, encoding="utf-8")
    (root / "rfcs" / "0003-third.md").write_text(RFC_0003, encoding="utf-8")
    (root / "docs" / "adr" / "README.md").write_text("# ADR\n", encoding="utf-8")
    (root / "docs" / "adr" / "0044-dated.md").write_text(ADR_0044, encoding="utf-8")
    (root / "docs" / "adr" / "0045-retired.md").write_text(ADR_0045, encoding="utf-8")
    (root / "docs" / "adr" / "0046-none.md").write_text(ADR_0046, encoding="utf-8")
    return root


@pytest.fixture
def reports_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "vault" / "daily-research"
    directory.mkdir(parents=True)
    (directory / "2026-09-25_jrp_skill-listing.md").write_text(
        "# Claude Code が skill listing を遅延読み込みに変えた HIT\n", encoding="utf-8"
    )
    (directory / "2026-09-24_jrp_other.md").write_text("# 別の話題\n", encoding="utf-8")
    (directory / "2026-09-10_jrp_old.md").write_text("# 古いレポート HIT\n", encoding="utf-8")
    (directory / "notes.md").write_text("レポートでない\n", encoding="utf-8")
    (directory / "2026-09-25_ai_track.md").write_text("# jrp 以前の形式 HIT\n", encoding="utf-8")
    return directory
