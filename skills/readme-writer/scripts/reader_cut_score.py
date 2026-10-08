"""Score the reader-cut pilot: how far each arm's CUTs agree with the author's marks.
Plan: docs/plans/reader-cut-pilot.html claim 3.

Ground truth (author-confirmed): mark "skip" = may be cut, "stop" = must not be cut
(evidence the reader needed more), unmarked = needed. Only CUT counts as cut; CONDENSE
is kept in the raw results but enters no metric. Length removed is recorded, never a
target — a length goal rewards over-cutting.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

# Numbers, negations, scope limits: a CUT of such a unit that the author did not mark
# "skip" is a violation (LLM rewrites drop exactly these — research report §3).
PROTECTED_RE = re.compile(
    r"\d|％|%"
    r"|ない|ません|ず[、。]|なし|無い"
    r"|だけ|のみ|限り|場合|とき|未|ただし|以外"
)


@dataclass(frozen=True)
class RunScore:
    arm: str
    run: str
    cut: int
    precision: float | None
    recall: float | None
    lift: float | None
    stop_cut: int
    protected_violations: int
    chars_cut: int


def _ratio(num: int, den: int) -> float | None:
    return num / den if den else None


def base_rate(marks: dict[str, str | None]) -> float:
    return _ratio(sum(m == "skip" for m in marks.values()), len(marks)) or 0.0


def score_run(
    arm: str,
    run: str,
    marks: dict[str, str | None],
    texts: dict[str, str],
    verdicts: dict[str, str],
) -> RunScore:
    """`marks`, `texts`, `verdicts` are keyed by "<text_id>#<i>" over the same units."""
    if verdicts.keys() != marks.keys():
        raise ValueError(f"{arm}/{run}: verdicts do not cover the labelled units")
    cut = {k for k, v in verdicts.items() if v == "CUT"}
    skip = {k for k, m in marks.items() if m == "skip"}
    stop = {k for k, m in marks.items() if m == "stop"}
    hit = len(cut & skip)
    p = _ratio(hit, len(cut))
    b = base_rate(marks)
    return RunScore(
        arm=arm,
        run=run,
        cut=len(cut),
        precision=p,
        recall=_ratio(hit, len(skip)),
        lift=p / b if p is not None and b else None,
        stop_cut=len(cut & stop),
        protected_violations=sum(
            1 for k in cut if PROTECTED_RE.search(texts[k]) and marks[k] != "skip"
        ),
        chars_cut=sum(len(texts[k]) for k in cut),
    )


def run_agreement(a: dict[str, str], b: dict[str, str]) -> float | None:
    """Jaccard similarity of two runs' CUT sets (1.0 = identical). None when neither cut."""
    ca = {k for k, v in a.items() if v == "CUT"}
    cb = {k for k, v in b.items() if v == "CUT"}
    return _ratio(len(ca & cb), len(ca | cb))


def _mean(xs: list[float | None]) -> float | None:
    vals = [x for x in xs if x is not None]
    return sum(vals) / len(vals) if vals else None


def summarize(runs: list[RunScore], agreements: dict[str, float | None]) -> list[dict]:
    """One row per arm: the mean over its runs, plus run-to-run agreement."""
    rows = []
    for arm in sorted({r.arm for r in runs}):
        rs = [r for r in runs if r.arm == arm]
        rows.append(
            {
                "arm": arm,
                "runs": len(rs),
                "cut": _mean([r.cut for r in rs]),
                "precision": _mean([r.precision for r in rs]),
                "recall": _mean([r.recall for r in rs]),
                "lift": _mean([r.lift for r in rs]),
                "stop_cut": _mean([r.stop_cut for r in rs]),
                "protected_violations": _mean([r.protected_violations for r in rs]),
                "chars_cut": _mean([r.chars_cut for r in rs]),
                "run_agreement": agreements.get(arm),
            }
        )
    return rows


def _fmt(x: float | None, nd: int = 2) -> str:
    return "—" if x is None else f"{x:.{nd}f}"


def render_table(
    n_texts: int, marks: dict[str, str | None], total_chars: int, rows: list[dict]
) -> str:
    n_skip = sum(m == "skip" for m in marks.values())
    lines = [
        f"text {n_texts} 本 · 文 {len(marks)} · 要らない {n_skip} · 基準率 b = "
        f"{_fmt(base_rate(marks), 3)}",
        "",
        "arm  CUT    P     R     P/b   止∩CUT 保護違反 run一致 削った字数",
    ]
    for r in rows:
        lines.append(
            f"{r['arm']:<4} {_fmt(r['cut'], 1):>5}  {_fmt(r['precision'])}  {_fmt(r['recall'])}"
            f"  {_fmt(r['lift'], 1):>4}  {_fmt(r['stop_cut'], 1):>5}  "
            f"{_fmt(r['protected_violations'], 1):>6}  {_fmt(r['run_agreement'])}"
            f"  {_fmt(r['chars_cut'], 0)} / {total_chars}"
        )
    return "\n".join(lines)


def as_dict(s: RunScore) -> dict:
    return asdict(s)
