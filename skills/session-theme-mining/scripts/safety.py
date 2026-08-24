"""Sanitization and private atomic writes for transcript-derived data."""

from __future__ import annotations

import json
import os
import re
import tempfile
import unicodedata
from pathlib import Path

_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}"), "ANTHROPIC_KEY"),
    (re.compile(r"\bsk-proj-[A-Za-z0-9_-]{16,}"), "OPENAI_KEY"),
    (re.compile(r"\bsk-or-v1-[A-Za-z0-9_-]{16,}"), "OPENROUTER_KEY"),
    (re.compile(r"\bsk-[A-Za-z0-9]{32,}"), "API_KEY"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{16,}"), "GITHUB_TOKEN"),
    (re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}"), "SLACK_TOKEN"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS_ACCESS_KEY_ID"),
    (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
        "PRIVATE_KEY",
    ),
)
_ASSIGNMENT = re.compile(
    r"\b([A-Za-z0-9_]*(?:SECRET|TOKEN|PASSWORD|PASSWD|API_?KEY|ACCESS_?KEY)"
    r"[A-Za-z0-9_]*)\s*[=:]\s*[\"']?([^\s\"']{8,})[\"']?",
    flags=re.IGNORECASE,
)
_BEARER = re.compile(r"(?i)\b(Authorization\s*:\s*Bearer\s+)[A-Za-z0-9._~+/=-]+")
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b")
_URL_CREDENTIALS = re.compile(r"(?i)\b(https?://)[^/@\s:]+:[^/@\s]+@")
_COOKIE = re.compile(r"(?i)\b(Set-Cookie|Cookie)\s*:[^\r\n]+")
_BOILERPLATE = (
    "<system-reminder>",
    "<user_info>",
    "<recommended_plugins>",
    "<permissions instructions>",
    "<environment_context>",
    "<local-command-caveat>",
    "# AGENTS.md instructions",
    "<skills_instructions>",
    "<user_action>",
)


def redact(text: str) -> str:
    """Best-effort redaction and control removal before text reaches a model."""

    output = "".join(
        character
        for character in str(text)
        if character in {"\n", "\t"} or unicodedata.category(character) not in {"Cc", "Cf"}
    )
    for pattern, label in _SECRET_PATTERNS:
        output = pattern.sub(f"[redacted:{label}]", output)
    output = _ASSIGNMENT.sub(lambda match: f"{match.group(1)}=[redacted]", output)
    output = _BEARER.sub(r"\1[redacted:BEARER]", output)
    output = _JWT.sub("[redacted:JWT]", output)
    output = _URL_CREDENTIALS.sub(r"\1[redacted:URL_CREDENTIALS]@", output)
    return _COOKIE.sub(r"\1: [redacted:COOKIE]", output)


def compact(text: str, limit: int = 6_000) -> str:
    clean = redact(text).strip()
    if not clean or clean.startswith(_BOILERPLATE):
        return ""
    if len(clean) <= limit:
        return clean
    if limit < 1_200:
        return clean[:limit]
    head = clean[: max(0, limit - 1_200)]
    tail = clean[-1_000:]
    return f"{head}\n\n[... {len(clean) - limit} chars elided ...]\n\n{tail}"


def one_line(text: str, limit: int = 200) -> str:
    flat = re.sub(r"\s+", " ", redact(text)).strip()
    return flat if len(flat) <= limit else f"{flat[:limit]}..."


def secure_json_write(path: Path, payload: object) -> None:
    """Atomically write mode-0600 JSON without chmoding caller-owned directories."""

    try:
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=False)
    except FileExistsError:
        pass
    descriptor, temporary_name = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        temporary.replace(path)
        path.chmod(0o600)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise
