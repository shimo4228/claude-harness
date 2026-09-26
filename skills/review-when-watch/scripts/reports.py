"""Find the daily-research reports to read.

The reports are the notes jev-research-pipeline (`jrp run`, daily 05:00) writes to
``<JRP_VAULT_DIR>/daily-research/{date}_jrp_{slug}.md``. ``JRP_VAULT_DIR`` comes from the
environment or from jrp's own env file (``~/.config/jrp/env``, or ``JRP_ENV_FILE``).

``REVIEW_WHEN_REPORTS_DIR`` overrides all of it, and under launchd it is the only way the
directory is given: the vault is in iCloud Drive, and macOS privacy (TCC) lets launchd's
``/bin/bash`` open it but not the uv-managed python — its ``open()`` waits on an invisible
consent prompt (jrp's first scheduled run hung 80 minutes on exactly this). So
``scripts/launchd-watch.sh`` copies the notes to a local stage and points this variable
there; python never touches the vault when launchd runs it.

Reports are read, never written. A symlinked file is skipped: the job runs unattended, and a
link planted in the vault would make it send an arbitrary local file to an outside API.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_JRP_ENV = ".config/jrp/env"
REPORT_SUBDIR = "daily-research"
#: Only jrp's notes, the same set scripts/launchd-watch.sh stages. Older
#: ``{date}_{track}_{slug}.md`` notes share the directory and are not this job's input.
REPORT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})_jrp_.+\.md$")


class ReportsError(RuntimeError):
    """The reports directory could not be resolved. The job reports this; it never guesses."""


@dataclass(frozen=True)
class Report:
    path: Path
    date: dt.date
    text: str

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def sha(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()[:16]


def _env_file_value(path: Path, key: str, home: Path) -> str | None:
    """``key``'s value in a ``KEY=value`` env file (``export`` and quotes allowed).

    The file is read, never sourced: only this one value is wanted from a file that also
    holds the pipeline's other secrets.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        name, sep, value = line.partition("=")
        if not sep or name.strip() != key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        return value.replace("${HOME}", str(home)).replace("$HOME", str(home)) or None
    return None


def resolve_reports_dir(env: Mapping[str, str], home: Path) -> Path:
    override = (env.get("REVIEW_WHEN_REPORTS_DIR") or "").strip()
    if override:
        directory = Path(override).expanduser()
    else:
        vault = (env.get("JRP_VAULT_DIR") or "").strip()
        env_file = Path(env.get("JRP_ENV_FILE") or home / DEFAULT_JRP_ENV).expanduser()
        if not vault:
            vault = _env_file_value(env_file, "JRP_VAULT_DIR", home) or ""
        if not vault:
            raise ReportsError(f"JRP_VAULT_DIR が分からない（環境変数にも {env_file} にも無い）")
        directory = Path(vault).expanduser() / REPORT_SUBDIR
    if not directory.is_dir():
        raise ReportsError(f"レポートの置き場所が無い: {directory}")
    return directory


def list_reports(directory: Path, today: dt.date, lookback_days: int) -> list[Report]:
    """Reports dated within the last ``lookback_days`` days (today included), oldest first."""
    oldest = today - dt.timedelta(days=lookback_days - 1)
    reports: list[Report] = []
    for path in sorted(directory.glob("*.md")):
        match = REPORT_RE.match(path.name)
        if not match or path.is_symlink() or not path.is_file():
            continue
        try:
            date = dt.date.fromisoformat(match.group(1))
        except ValueError:
            continue
        if not oldest <= date <= today:
            continue
        reports.append(Report(path=path, date=date, text=path.read_text(encoding="utf-8")))
    return reports
