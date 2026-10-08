"""CLI of the reader-cut pilot: does a cut-only LLM pass agree with the author's own
"skip" marks? Plan: docs/plans/reader-cut-pilot.html (packet:
docs/plans/reader-cut-pilot-s1-build.md).

  python -m scripts.reader_cut split <path> --text-id <id>   # units/<id>.json
  python -m scripts.reader_cut page                          # page/marking.html
  python -m scripts.reader_cut ingest <db-export.json>       # labels/<id>.json
  python -m scripts.reader_cut run --arm A2 --run 1 [--text <id>] [--dry-run]
  python -m scripts.reader_cut score                         # table + results/score.json

Run from skills/readme-writer. Data lives in evals/reader-cut/ (units, labels frozen
with the source sha256; results per arm and run).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__:
    from . import reader_cut_run as _run
    from . import reader_cut_score as _score
    from . import reader_cut_units as _units
else:  # direct script invocation
    import reader_cut_run as _run
    import reader_cut_score as _score
    import reader_cut_units as _units

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "evals" / "reader-cut"
PROMPT = ROOT / "prompt"


def _load_dir(d: Path) -> dict[str, dict]:
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))}


def cmd_split(args: argparse.Namespace) -> int:
    rec = _units.units_record(Path(args.path).expanduser(), args.text_id)
    out = DATA / "units" / f"{args.text_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    chars = sum(len(u["text"]) for u in rec["units"])
    print(f"{args.text_id}: {len(rec['units'])} units, {chars} chars -> {out}")
    return 0


def cmd_page(_args: argparse.Namespace) -> int:
    texts = list(_load_dir(DATA / "units").values())
    if not texts:
        raise SystemExit("no units/*.json yet; run split first")
    payload = [{k: t[k] for k in ("text_id", "sha256", "units")} for t in texts]
    # Every "<" escaped: "</script" or "<!--" in a sentence must not end or retype the
    # data block (a later "<script" after "<!--" would swallow the page script).
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    template = (DATA / "page" / "template.html").read_text(encoding="utf-8")
    out = DATA / "page" / "marking.html"
    out.write_text(template.replace("__DATA__", data), encoding="utf-8")
    print(f"{len(texts)} texts -> {out}")
    return 0


def _doc_id(raw_id: str) -> str:
    """The page writes marks/<text_id>; an export may carry the full path."""
    return raw_id.removeprefix("marks/")


def _export_docs(raw: object) -> dict[str, dict]:
    """Accept {id: body}, [{id, data}] or {"docs": [...]} from a db export."""
    if isinstance(raw, dict) and "docs" in raw:
        raw = raw["docs"]
    if isinstance(raw, list):
        return {_doc_id(d["id"]): d.get("data", d) for d in raw}
    if isinstance(raw, dict):
        return {_doc_id(k): v for k, v in raw.items()}
    raise ValueError("unrecognised db export shape")


def cmd_ingest(args: argparse.Namespace) -> int:
    docs = _export_docs(json.loads(Path(args.export).read_text(encoding="utf-8")))
    units = _load_dir(DATA / "units")
    for text_id, body in docs.items():
        rec = units.get(text_id)
        if rec is None:
            raise SystemExit(f"{text_id}: no units file")
        if body.get("sha256") != rec["sha256"]:
            raise SystemExit(f"{text_id}: sha256 differs from the marked version; labels void")
        marks = body.get("marks", {})
        for u in rec["units"]:
            u["mark"] = marks.get(str(u["i"]))
        out = DATA / "labels" / f"{text_id}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        n_skip = sum(u["mark"] == "skip" for u in rec["units"])
        print(f"{text_id}: {len(rec['units'])} units, skip {n_skip} -> {out}")
    return 0


def cmd_run(args: argparse.Namespace, runner: _run.Runner = _run.call_model) -> int:
    arm = _run.load_arms(PROMPT / "arms.toml")[args.arm]
    units = _load_dir(DATA / "units")
    ids = [args.text] if args.text else sorted(units)
    for text_id in ids:
        us = units[text_id]["units"]
        if args.dry_run:
            template = (PROMPT / "cutter.md").read_text(encoding="utf-8")
            reader = _run.reader_text(arm, PROMPT)
            for _asked, prompt in _run.build_prompts(us, arm, template, reader):
                print(prompt, end="\n---\n")
            continue
        verdicts = _run.run_text(us, arm, PROMPT, runner)
        out = DATA / "results" / arm.name / f"run{args.run}" / f"{text_id}.tsv"
        _run.write_tsv(out, verdicts)
        meta = {
            "sha256": units[text_id]["sha256"],
            "arm": arm.name,
            "runner": arm.runner,
            "model": arm.model or "(default)",
        }
        out.with_suffix(".meta.json").write_text(json.dumps(meta) + "\n", encoding="utf-8")
        n_cut = sum(v == "CUT" for v, _ in verdicts.values())
        print(f"{arm.name} run{args.run} {text_id}: CUT {n_cut}/{len(us)} -> {out}")
    return 0


def _keyed(labels: dict[str, dict]) -> tuple[dict[str, str | None], dict[str, str]]:
    marks, texts = {}, {}
    for text_id, rec in labels.items():
        for u in rec["units"]:
            k = f"{text_id}#{u['i']}"
            marks[k], texts[k] = u["mark"], u["text"]
    return marks, texts


def cmd_score(_args: argparse.Namespace) -> int:
    labels = _load_dir(DATA / "labels")
    if not labels:
        raise SystemExit("no labels/*.json yet; run ingest first")
    marks, texts = _keyed(labels)
    runs: list[_score.RunScore] = []
    per_run: dict[tuple[str, str], dict[str, str]] = {}
    for run_dir in sorted((DATA / "results").glob("*/run*")):
        arm, run = run_dir.parent.name, run_dir.name
        for text_id, rec in labels.items():
            meta = json.loads((run_dir / f"{text_id}.meta.json").read_text(encoding="utf-8"))
            if meta["sha256"] != rec["sha256"]:
                raise SystemExit(f"{arm}/{run}/{text_id}: judged a different version of the text")
        verdicts = {
            f"{text_id}#{i}": v
            for text_id in labels
            for i, v in _run.read_tsv(run_dir / f"{text_id}.tsv").items()
        }
        per_run[(arm, run)] = verdicts
        runs.append(_score.score_run(arm, run, marks, texts, verdicts))
    agreements = {}
    for arm in {a for a, _ in per_run}:
        pair = [v for (a, _), v in sorted(per_run.items()) if a == arm][:2]
        agreements[arm] = _score.run_agreement(*pair) if len(pair) == 2 else None
    rows = _score.summarize(runs, agreements)
    print(_score.render_table(len(labels), marks, sum(len(t) for t in texts.values()), rows))
    out = DATA / "results" / "score.json"
    out.write_text(
        json.dumps(
            {"runs": [_score.as_dict(r) for r in runs], "arms": rows}, ensure_ascii=False, indent=1
        )
        + "\n",
        encoding="utf-8",
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="reader_cut")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("split")
    p.add_argument("path")
    p.add_argument("--text-id", required=True)
    sub.add_parser("page")
    p = sub.add_parser("ingest")
    p.add_argument("export")
    p = sub.add_parser("run")
    p.add_argument("--arm", required=True)
    p.add_argument("--run", required=True, choices=["1", "2"])
    p.add_argument("--text")
    p.add_argument("--dry-run", action="store_true")
    sub.add_parser("score")
    args = ap.parse_args(argv)
    handlers = {
        "split": cmd_split,
        "page": cmd_page,
        "ingest": cmd_ingest,
        "run": cmd_run,
        "score": cmd_score,
    }
    return handlers[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
