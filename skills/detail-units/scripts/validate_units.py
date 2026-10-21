"""Check a product's eval/units.yaml against the detail-units schema.

The schema is defined in the detail-units SKILL.md; this script enforces it so everything that
reads or writes the file can rely on its shape. It reports every
problem it finds, not only the first.

Usage:
    python3 validate_units.py <units.yaml> [--runner <file>]

--runner names the file that runs the frozen checks (for example eval/units.mjs). Each frozen
unit's eval.check must then appear in it as a quoted string, so a unit cannot be marked frozen
while no check exists for it.

Exit 0 when the file is valid, 1 when it has problems (listed as JSON on stdout), 2 on bad usage
or an unreadable file.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

JUDGES = {"machine", "hybrid", "author"}
STATUSES = {"open", "frozen", "author-eye", "retired"}
RELATION_KINDS = ("co-arising", "support")
UNIT_KEYS = {"id", "field", "what", "why", "eval", "cause", "relations", "origin", "decided_by", "status"}
REQUIRED_UNIT_KEYS = ("id", "field", "what", "why", "eval", "cause", "origin", "status")
EVAL_KEYS = {"judge", "check", "env", "expect", "instances"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _text(value: object) -> bool:
    return isinstance(value, str) and value.strip() != ""


def _check_eval(uid: str, ev: object, status: object, has_decision: bool) -> list[str]:
    if not isinstance(ev, dict):
        return [f"{uid}: eval must be a mapping"]
    errors = [f"{uid}: unknown eval key '{k}'" for k in ev if k not in EVAL_KEYS]
    judge = ev.get("judge")
    if judge not in JUDGES:
        errors.append(f"{uid}: eval.judge must be one of {sorted(JUDGES)}, got {judge!r}")
    if not _text(ev.get("expect")):
        errors.append(f"{uid}: eval.expect is required")
    if judge == "author":
        if "check" in ev:
            errors.append(f"{uid}: an author unit has no eval.check (it is judged by the author's eye)")
        if status not in ("author-eye", "retired"):
            errors.append(f"{uid}: an author unit has status author-eye or retired, got {status!r}")
    elif status == "author-eye":
        errors.append(f"{uid}: author-eye is the status of author units only")
    if "check" in ev and ev["check"] != uid:
        errors.append(f"{uid}: eval.check equals the id, got {ev['check']!r}")
    if status == "frozen":
        if not _text(ev.get("check")):
            errors.append(f"{uid}: a frozen unit needs eval.check")
        if judge == "hybrid" and not has_decision:
            errors.append(f"{uid}: a frozen hybrid unit needs decided_by (the author set its range)")
    return errors


def _check_relations(uid: str, relations: object, ids: set[str]) -> list[str]:
    if not isinstance(relations, list):
        return [f"{uid}: relations must be a list"]
    errors = []
    for rel in relations:
        if not isinstance(rel, dict) or set(rel) != {"unit", "how"}:
            errors.append(f"{uid}: each relation has exactly the keys unit and how")
            continue
        if rel["unit"] not in ids:
            errors.append(f"{uid}: relation to unknown unit {rel['unit']!r}")
        elif rel["unit"] == uid:
            errors.append(f"{uid}: a unit cannot relate to itself")
        if not (isinstance(rel["how"], str) and rel["how"].startswith(RELATION_KINDS)):
            errors.append(f"{uid}: relation how starts with one of {list(RELATION_KINDS)}")
    return errors


def _check_unit(unit: dict[str, Any], ids: set[str]) -> list[str]:
    uid = str(unit.get("id", "<no id>"))
    errors = [f"{uid}: unknown key '{k}'" for k in unit if k not in UNIT_KEYS]
    errors += [f"{uid}: {k} is required" for k in REQUIRED_UNIT_KEYS if k not in unit]
    errors += [
        f"{uid}: {k} must be non-empty text"
        for k in ("field", "what", "why", "cause", "origin")
        if k in unit and not _text(unit[k])
    ]
    status = unit.get("status")
    if status not in STATUSES:
        errors.append(f"{uid}: status must be one of {sorted(STATUSES)}, got {status!r}")
    if "decided_by" in unit and not _text(unit["decided_by"]):
        errors.append(f"{uid}: decided_by must be non-empty text")
    if "eval" in unit:
        errors += _check_eval(uid, unit["eval"], status, "decided_by" in unit)
    if "relations" in unit:
        errors += _check_relations(uid, unit["relations"], ids)
    return errors


def validate(units: object, runner_text: str | None = None) -> list[str]:
    """Return every schema problem in a parsed units.yaml; an empty list means valid."""
    if not isinstance(units, list) or not units:
        return ["the file must be a non-empty list of units"]
    errors: list[str] = []
    ids: set[str] = set()
    for i, unit in enumerate(units):
        if not isinstance(unit, dict):
            errors.append(f"entry {i}: each unit must be a mapping")
            continue
        uid = unit.get("id")
        if not (isinstance(uid, str) and ID_PATTERN.match(uid)):
            errors.append(f"entry {i}: id must be kebab-case, got {uid!r}")
        elif uid in ids:
            errors.append(f"{uid}: duplicate id")
        else:
            ids.add(uid)
    for unit in units:
        if isinstance(unit, dict):
            errors += _check_unit(unit, ids)
    if runner_text is not None:
        for unit in units:
            if not isinstance(unit, dict) or unit.get("status") != "frozen":
                continue
            check = (unit.get("eval") or {}).get("check")
            if isinstance(check, str) and check.strip() and not re.search(rf"""['"`]{re.escape(check)}['"`]""", runner_text):
                errors.append(f"{unit['id']}: check {check!r} does not appear in the runner")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check eval/units.yaml against the detail-units schema.")
    parser.add_argument("units", type=Path)
    parser.add_argument("--runner", type=Path, help="file that runs the frozen checks")
    args = parser.parse_args(argv)
    try:
        units = yaml.safe_load(args.units.read_text(encoding="utf-8"))
        runner_text = args.runner.read_text(encoding="utf-8") if args.runner else None
    except (OSError, yaml.YAMLError) as e:
        print(f"cannot read input: {e}", file=sys.stderr)
        return 2
    errors = validate(units, runner_text)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, ensure_ascii=False, indent=2))
        return 1
    counts: dict[str, int] = {}
    for unit in units:
        key = f"{unit['eval']['judge']}/{unit['status']}"
        counts[key] = counts.get(key, 0) + 1
    print(json.dumps({"valid": True, "units": len(units), "by_judge_status": counts}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
