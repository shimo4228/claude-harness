"""Classify tool calls against compliance steps using LLM."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.parser import ComplianceSpec, ObservationEvent
from scripts.spec_generator import UTILITY_SETTINGS

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Sonnet handles long traces (50+ events × multi-step specs) within budget;
# haiku times out on contemplative-style abstract specs whose prompts balloon.
CLASSIFIER_TIMEOUT_SECONDS = 300


def classify_events(
    spec: ComplianceSpec,
    trace: list[ObservationEvent],
    model: str = "sonnet",
) -> dict[str, list[int]]:
    """Classify which tool calls match which compliance steps.

    Returns {step_id: [event_indices]} via a single LLM call.
    """
    if not trace:
        return {}

    steps_desc = "\n".join(f"- {step.id}: {step.detector.description}" for step in spec.steps)

    tool_calls = "\n".join(
        f"[{i}] {event.tool}: input={event.input[:500]} output={event.output[:200]}"
        for i, event in enumerate(trace)
    )

    prompt_template = (PROMPTS_DIR / "classifier.md").read_text()
    prompt = prompt_template.replace("{steps_description}", steps_desc).replace(
        "{tool_calls}", tool_calls
    )

    result = subprocess.run(
        [
            "claude",
            "-p",
            prompt,
            "--model",
            model,
            "--output-format",
            "text",
            "--settings",
            UTILITY_SETTINGS,
        ],
        capture_output=True,
        text=True,
        timeout=CLASSIFIER_TIMEOUT_SECONDS,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"classifier subprocess failed (rc={result.returncode}): {result.stderr[:500]!r}"
        )

    return _parse_classification(result.stdout)


class ClassificationParseError(RuntimeError):
    """Raised when no classification JSON can be extracted from model output.

    A silent `{}` here is indistinguishable from "the model matched nothing",
    which turns a broken measurement into a plausible-looking 0% report.
    """


def _parse_classification(text: str) -> dict[str, list[int]]:
    """Parse LLM classification output into {step_id: [event_indices]}.

    The child `claude -p` session inherits user-level config (output styles,
    CLAUDE.md), so on long traces the answer JSON may arrive wrapped in
    narrative prose and markdown fences rather than as bare stdout. The text
    is scanned FORWARD, decoding at each candidate `{` and skipping the whole
    decoded span, so only TOP-LEVEL objects are candidates — a nested object
    inside the answer can never shadow it (scanning from the end did exactly
    that: the innermost `{` decoded first and silently replaced the real
    mapping). Among top-level objects the last valid one wins (the final
    object is the answer by convention). An empty `{}` from the model is a
    legitimate "nothing matched" verdict; extracting no JSON at all is a
    measurement failure and raises.
    """
    decoder = json.JSONDecoder()
    result: dict[str, list[int]] | None = None
    pos = 0
    while True:
        brace = text.find("{", pos)
        if brace == -1:
            break
        try:
            parsed, end = decoder.raw_decode(text, brace)
        except json.JSONDecodeError:
            pos = brace + 1
            continue
        pos = end
        if not isinstance(parsed, dict):
            continue
        try:
            result = {k: [int(i) for i in v] for k, v in parsed.items() if isinstance(v, list)}
        except (TypeError, ValueError):
            continue
    if result is not None:
        return result
    raise ClassificationParseError(
        "no parsable classification JSON in model output; "
        f"first 500 chars of stdout: {text[:500]!r}"
    )
