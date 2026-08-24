"""Normalized transcript record types shared by catalog and cache code."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

if __package__:
    from .safety import compact, one_line
else:  # Direct execution through session_catalog.py.
    from safety import compact, one_line


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class Event:
    kind: Literal["message", "tool"]
    role: str | None
    text: str
    result: str | None = None
    timestamp: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> Event:
        raw_kind = payload.get("kind")
        if raw_kind == "message":
            kind: Literal["message", "tool"] = "message"
        elif raw_kind == "tool":
            kind = "tool"
        else:
            raise ValueError(f"unknown event kind: {raw_kind}")
        raw_role = payload.get("role")
        raw_result = payload.get("result")
        raw_timestamp = payload.get("timestamp")
        return cls(
            kind=kind,
            role=raw_role if isinstance(raw_role, str) else None,
            text=str(payload.get("text", "")),
            result=raw_result if isinstance(raw_result, str) else None,
            timestamp=raw_timestamp if isinstance(raw_timestamp, str) else None,
        )


@dataclass(frozen=True, slots=True)
class SessionRecord:
    session_id: str
    harness: Literal["claude", "codex"]
    cwd: str
    raw_path: str
    started_at: str | None
    title: str
    events: tuple[Event, ...]
    is_parent: bool = True
    warnings: tuple[str, ...] = ()

    @classmethod
    def from_parts(
        cls,
        *,
        session_id: str,
        harness: Literal["claude", "codex"],
        cwd: str,
        raw_path: Path,
        started_at: str | None,
        title: str,
        events: Iterable[tuple[str, str | None, str, str | None, str | None]],
        is_parent: bool = True,
        warnings: Iterable[str] = (),
    ) -> SessionRecord:
        normalized: list[Event] = []
        for raw_kind, role, text, result, timestamp in events:
            if raw_kind == "message":
                kind: Literal["message", "tool"] = "message"
            elif raw_kind == "tool":
                kind = "tool"
            else:
                raise ValueError(f"unknown event kind: {raw_kind}")
            normalized.append(
                Event(
                    kind=kind,
                    role=role,
                    text=compact(text) if kind == "message" else one_line(text),
                    result=one_line(result, 240) if result else None,
                    timestamp=timestamp,
                )
            )
        return cls(
            session_id=session_id,
            harness=harness,
            cwd=cwd,
            raw_path=str(raw_path),
            started_at=started_at,
            title=one_line(title, 300),
            events=tuple(event for event in normalized if event.text),
            is_parent=is_parent,
            warnings=tuple(warnings),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SessionRecord:
        raw_events = payload.get("events")
        events = raw_events if isinstance(raw_events, list) else []
        raw_warnings = payload.get("warnings")
        warnings = raw_warnings if isinstance(raw_warnings, list) else []
        raw_harness = payload.get("harness")
        if raw_harness == "claude":
            harness: Literal["claude", "codex"] = "claude"
        elif raw_harness == "codex":
            harness = "codex"
        else:
            raise ValueError(f"unknown harness: {raw_harness}")
        raw_started_at = payload.get("started_at")
        return cls(
            session_id=str(payload["session_id"]),
            harness=harness,
            cwd=str(payload.get("cwd", "")),
            raw_path=str(payload["raw_path"]),
            started_at=raw_started_at if isinstance(raw_started_at, str) else None,
            title=str(payload.get("title", "")),
            events=tuple(Event.from_dict(item) for item in events if isinstance(item, dict)),
            is_parent=bool(payload.get("is_parent", True)),
            warnings=tuple(str(item) for item in warnings),
        )

    @property
    def repo_key(self) -> str:
        return self.cwd or "(unknown)"

    @property
    def started_datetime(self) -> datetime:
        parsed = parse_datetime(self.started_at)
        if parsed is not None:
            return parsed
        try:
            return datetime.fromtimestamp(Path(self.raw_path).stat().st_mtime, tz=UTC)
        except OSError:
            return datetime.fromtimestamp(0, tz=UTC)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class CatalogDiagnostics:
    discovered_files: int = 0
    source_bytes: int = 0
    skipped_byte_budget: int = 0
    read_errors: int = 0
    cache_write_errors: int = 0
    parse_warnings: int = 0
    malformed_json: int = 0
    line_too_large: int = 0
