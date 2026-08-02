"""Parse observation traces (JSONL) and compliance specs (YAML)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml


def extract_yaml_payload(text: str) -> str:
    """Extract the YAML document from LLM stdout that may be wrapped in prose.

    The generator `claude -p` children inherit user-level config (output
    styles, CLAUDE.md), so the answer sometimes arrives with narrative
    paragraphs and insight blocks around a fenced YAML document instead of as
    bare stdout. Candidates are tried in order — last fenced block first
    (the final block is the answer by convention), then the edge-stripped
    whole text, then the tail starting at the first top-level YAML key — and
    the first candidate that loads as a YAML mapping wins. When none loads,
    the edge-stripped text is returned so the caller's own parse error (and
    retry-with-feedback loop) fires with the original content.
    """
    stripped_lines = text.strip().splitlines()
    if stripped_lines and stripped_lines[0].startswith("```"):
        stripped_lines = stripped_lines[1:]
    if stripped_lines and stripped_lines[-1].startswith("```"):
        stripped_lines = stripped_lines[:-1]
    edge_stripped = "\n".join(stripped_lines)

    candidates: list[str] = []
    fenced = re.findall(r"```[a-zA-Z]*\s*\n(.*?)```", text, re.DOTALL)
    candidates.extend(reversed(fenced))
    candidates.append(edge_stripped)
    key_match = re.search(r"^(?:id|scenarios):", text, re.MULTILINE)
    if key_match:
        candidates.append(text[key_match.start() :])

    for candidate in candidates:
        try:
            if isinstance(yaml.safe_load(candidate), dict):
                return candidate
        except yaml.YAMLError:
            continue
    return edge_stripped


@dataclass(frozen=True)
class ObservationEvent:
    timestamp: str
    event: str
    tool: str
    session: str
    input: str
    output: str


@dataclass(frozen=True)
class Detector:
    description: str
    after_step: str | None = None
    before_step: str | None = None


@dataclass(frozen=True)
class Step:
    id: str
    description: str
    required: bool
    detector: Detector


@dataclass(frozen=True)
class ComplianceSpec:
    id: str
    name: str
    source_rule: str
    version: str
    steps: tuple[Step, ...]
    threshold_promote_to_hook: float


def parse_trace(path: Path) -> list[ObservationEvent]:
    """Parse a JSONL observation trace file into sorted events."""
    if not path.exists():
        raise FileNotFoundError(f"Trace file not found: {path}")

    text = path.read_text().strip()
    if not text:
        return []

    events: list[ObservationEvent] = []
    for line in text.splitlines():
        raw = json.loads(line)
        events.append(
            ObservationEvent(
                timestamp=raw["timestamp"],
                event=raw["event"],
                tool=raw["tool"],
                session=raw["session"],
                input=raw.get("input", ""),
                output=raw.get("output", ""),
            )
        )

    return sorted(events, key=lambda e: e.timestamp)


def parse_spec(path: Path) -> ComplianceSpec:
    """Parse a YAML compliance spec file."""
    raw = yaml.safe_load(path.read_text())

    steps: list[Step] = []
    for s in raw["steps"]:
        d = s["detector"]
        steps.append(
            Step(
                id=s["id"],
                description=s["description"],
                required=s["required"],
                detector=Detector(
                    description=d["description"],
                    after_step=d.get("after_step"),
                    before_step=d.get("before_step"),
                ),
            )
        )

    # Temporal references must point at declared steps. An unknown id (LLM
    # hallucination or typo) would otherwise grade as "unevaluable" and pass,
    # silently softening the constraint it was meant to impose.
    step_ids = {s.id for s in steps}
    for s in steps:
        for ref in (s.detector.after_step, s.detector.before_step):
            if ref is not None and ref not in step_ids:
                raise ValueError(
                    f"step '{s.id}' references unknown step '{ref}' in after_step/before_step"
                )

    return ComplianceSpec(
        id=raw["id"],
        name=raw["name"],
        source_rule=raw["source_rule"],
        version=raw["version"],
        steps=tuple(steps),
        threshold_promote_to_hook=raw["scoring"]["threshold_promote_to_hook"],
    )
