"""One Jev request per (report, condition) pair, and the canary pair that checks the pipe.

The unit is one source against one question (skill jev-judgment-design §5), and the thing the
source is compared against — the condition — is in ``state`` (§2). Two answers come back per
pair and they are kept apart (§4):

- ``met`` (Noul) is the gate: does the report say the awaited event happened?
- ``overlap`` (Choice) only orders the hits. Its lowest option is "shares vocabulary only"
  (§3), so a report that merely mentions the same product has somewhere to land.

Every question string and the threshold are measured inputs: editing one changes what the
log records, and ``QUESTION_HASH`` marks the version so old and new rows are not averaged.

Only the wire formats already confirmed live by skills/jev-skill-router are used (Noul with
``instructions``; Choice with ``instructions`` + ``criteria``, answered with
``probabilities``).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol

from scripts.conditions import Condition

#: Pinned, never read from the environment (same reason as jev-skill-router's MODEL).
MODEL = "jev-1.13.0"
WATCH_VERSION = "0.1.0"
#: Provisional. Nothing here was calibrated: the first rows of the log are the first data.
#: Change it only with the log in hand, and note the change in ADR-0080.
MET_THRESHOLD = 0.5
#: Jev takes 32k tokens for ``state`` plus the longest question. Japanese runs near one token
#: per character, so the report is cut well below that and the cut is logged.
MAX_REPORT_CHARS = 20000
REQUEST_TIMEOUT_S = 20.0

MET_INSTRUCTIONS = (
    "The `condition` names an event that, once it happens, means a design record must be "
    "re-examined. Does the `report` say that this event has actually happened — released, "
    "announced as done, changed, retired, or measured — and not merely discuss the same "
    "topic, propose it, predict it, or report a rumor?"
)
OVERLAP_INSTRUCTIONS = "How does the `report` relate to the event named in `condition`?"
OVERLAP_CRITERIA = {
    "words_only": (
        "The report is about a different matter that only shares vocabulary with the condition."
    ),
    "same_area": (
        "The report is about the same product or field, but not the specific change the "
        "condition waits for."
    ),
    "precursor": (
        "The report describes a step toward the event (plans, a preview, a partial change) "
        "but not the event itself."
    ),
    "event": "The report says the specific event the condition waits for has happened.",
}


def build_questions() -> dict[str, dict]:
    return {
        "met": {"type": "noul", "instructions": MET_INSTRUCTIONS},
        "overlap": {
            "type": "choice",
            "instructions": OVERLAP_INSTRUCTIONS,
            "criteria": dict(OVERLAP_CRITERIA),
        },
    }


QUESTION_HASH = hashlib.sha256(
    json.dumps(build_questions(), ensure_ascii=False, sort_keys=True).encode("utf-8")
).hexdigest()[:12]


class Client(Protocol):
    def ask(
        self,
        state: Mapping[str, str],
        questions: Mapping[str, dict],
        *,
        model: str,
        timeout: float,
    ) -> dict: ...


class JudgeError(RuntimeError):
    """The response came back but cannot be read as an answer to what was asked."""


@dataclass(frozen=True)
class Reading:
    met: float
    overlap: dict[str, float]
    truncated: bool
    model: str
    usage: dict[str, int] = field(default_factory=dict)

    @property
    def top_overlap(self) -> str:
        if not self.overlap:
            return ""
        return max(self.overlap.items(), key=lambda kv: (kv[1], kv[0]))[0]

    @property
    def hit(self) -> bool:
        return self.met >= MET_THRESHOLD


def build_state(
    condition_id: str, title: str, condition_text: str, report_name: str, report_text: str
) -> tuple[dict[str, str], bool]:
    truncated = len(report_text) > MAX_REPORT_CHARS
    body = report_text[:MAX_REPORT_CHARS] if truncated else report_text
    state = {
        "condition": f"{condition_id}: {title}\n{condition_text}",
        "report": f"{report_name}\n\n{body}",
    }
    return state, truncated


def _read(response: Mapping[str, Any], truncated: bool) -> Reading:
    returned = str(response.get("model") or "")
    if returned != MODEL:
        raise JudgeError(f"model mismatch: asked {MODEL}, got {returned or 'nothing'}")
    answers = response.get("answers") or {}
    met = (answers.get("met") or {}).get("noul")
    probabilities = (answers.get("overlap") or {}).get("probabilities") or {}
    if not isinstance(met, int | float):
        raise JudgeError("no noul in the answer to `met`")
    overlap = {
        str(k): float(v)
        for k, v in probabilities.items()
        if k in OVERLAP_CRITERIA and isinstance(v, int | float)
    }
    usage = {
        k: int(v) for k, v in (response.get("usage") or {}).items() if isinstance(v, int | float)
    }
    return Reading(
        met=float(met), overlap=overlap, truncated=truncated, model=returned, usage=usage
    )


def judge(
    client: Client,
    condition_id: str,
    title: str,
    condition_text: str,
    report_name: str,
    report_text: str,
) -> Reading:
    state, truncated = build_state(condition_id, title, condition_text, report_name, report_text)
    response = client.ask(state, build_questions(), model=MODEL, timeout=REQUEST_TIMEOUT_S)
    return _read(response, truncated)


def judge_pair(client: Client, condition: Condition, report_name: str, text: str) -> Reading:
    return judge(client, condition.id, condition.title, condition.text, report_name, text)


# The canary pair (skill jev-judgment-design §6): one report that must pass and one that
# shares the words but must not. Self-contained on purpose — it does not depend on any RFC
# keeping its wording, so a failing canary means the pipe or the threshold moved, not the
# ledger.
CANARY_CONDITION = (
    "CANARY",
    "canary",
    "Zenodo が legacy deposition API（/api/deposit/depositions）を廃止・変更した時",
)
CANARY_POSITIVE = (
    "canary-positive.md",
    "Zenodo は旧来の deposition API（/api/deposit/depositions）の提供を 2026-09-20 に終了したと"
    "発表した。以後の登録は InvenioRDM の /api/records に一本化され、旧エンドポイントへの"
    "リクエストは 410 Gone を返す。",
)
CANARY_NEGATIVE = (
    "canary-negative.md",
    "Zenodo はコミュニティページのデザインを刷新し、検索結果に「引用数順」の並び替えを加えた。"
    "発表は API のエンドポイントに変更はないと明記している。",
)


@dataclass(frozen=True)
class CanaryResult:
    positive: float | None
    negative: float | None
    error: str | None = None

    @property
    def ok(self) -> bool:
        if self.error or self.positive is None or self.negative is None:
            return False
        return self.positive >= MET_THRESHOLD > self.negative


def run_canary(client: Client) -> CanaryResult:
    try:
        positive = judge(client, *CANARY_CONDITION, *CANARY_POSITIVE)
        negative = judge(client, *CANARY_CONDITION, *CANARY_NEGATIVE)
    except Exception as exc:  # the canary reports; it never stops the run
        return CanaryResult(None, None, f"{type(exc).__name__}: {exc}")
    return CanaryResult(positive.met, negative.met)


def load_jev_client(root: Path) -> ModuleType:
    """Load skills/jev-skill-router/scripts/jev_client.py by path.

    Reused rather than copied: it carries the host pin, the redirect refusal and the key
    resolution that were security-reviewed for the router (ADR-0074 Decision 8), and a second
    copy would drift. It imports only the standard library, so it loads on its own.
    """
    path = root / "skills" / "jev-skill-router" / "scripts" / "jev_client.py"
    spec = importlib.util.spec_from_file_location("review_when_watch_jev_client", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
