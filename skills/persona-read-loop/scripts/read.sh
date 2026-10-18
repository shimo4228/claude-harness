#!/usr/bin/env bash
# read.sh — run one isolated reader, or check that the isolation holds.
#
# usage:
#   read.sh <persona.txt> <prompt.md> <draft.reader.md> > out.json
#       One reader. persona.txt becomes the system prompt; prompt.md and the draft are
#       concatenated into the user prompt. Prints the reader's raw answer.
#   read.sh --probe
#       Starts a reader with the same flags and checks, from the init event and one question,
#       that it sees no tools, no MCP servers, no user or plugin skills, and no memory or
#       CLAUDE.md. Exit 0 when isolated, 1 when anything leaks, 2 when the check cannot run.
#
# env:
#   PERSONA_READ_CMD    the CLI to start (default: claude). Only Claude Code is tested.
#   PERSONA_READ_MODEL  reader model (default: sonnet)
#
# Isolation is `--setting-sources "" --strict-mcp-config --tools ""`, a replaced system prompt,
# auto memory off, and an empty working directory. Measured on Claude Code 2.1.302 (2026-10-18):
# --safe-mode still showed environment sections such as "# userEmail", and the empty
# --setting-sources alone still loaded the auto memory of the working directory's project.
# The empty --setting-sources is observed behavior, not documented, so the probe runs before
# every target.
set -euo pipefail

CMD="${PERSONA_READ_CMD:-claude}"
MODEL="${PERSONA_READ_MODEL:-sonnet}"
ISOLATION=(-p --setting-sources "" --strict-mcp-config --tools "" --model "$MODEL")

# Run the CLI from a fresh empty directory with auto memory off.
isolated() {
  local dir status=0
  dir=$(mktemp -d)
  (cd "$dir" && CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 "$CMD" "${ISOLATION[@]}" "$@" </dev/null) || status=$?
  rmdir "$dir" 2>/dev/null || true
  return "$status"
}

probe() {
  local question out
  question='Does your context contain a list of skills, any memory, or any CLAUDE.md headings? If it contains none of these, reply with the single word NONE and nothing else. Otherwise quote each one verbatim.'
  command -v "$CMD" >/dev/null 2>&1 || { echo "probe: $CMD not found" >&2; return 2; }
  command -v python3 >/dev/null 2>&1 || { echo "probe: python3 not found" >&2; return 2; }
  out=$(isolated --output-format stream-json --verbose \
    --system-prompt "You are a careful reader." "$question") || {
    echo "probe: $CMD exited non-zero" >&2
    return 2
  }
  printf '%s\n' "$out" | python3 -c '
import json, os, sys
from pathlib import Path

def user_skill_names() -> set[str]:
    """Skill directories the user installed: the config dir and every .claude/skills above cwd."""
    roots = [Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude")) / "skills"]
    here = Path.cwd()
    roots += [d / ".claude" / "skills" for d in (here, *here.parents)]
    return {p.parent.name for r in roots if r.is_dir() for p in r.glob("*/SKILL.md")}

init, answer = None, None
for line in sys.stdin:
    try:
        event = json.loads(line)
    except ValueError:
        continue
    if event.get("type") == "system" and event.get("subtype") == "init":
        init = event
    elif event.get("type") == "result":
        answer = (event.get("result") or "").strip()
if init is None or answer is None:
    print("probe: no init or result event in the output (CLI format changed?)", file=sys.stderr)
    sys.exit(2)

skills = init.get("skills") or []
installed = user_skill_names()
user = [s for s in skills if ":" in s or s in installed]
checks = [
    ("tools", len(init.get("tools") or []), ""),
    ("mcp_servers", len(init.get("mcp_servers") or []), ""),
    ("user skills", len(user), f"(built-in {len(skills) - len(user)})"),
]
for name, n, note in checks:
    print(f"{name:<12} {n}   {note}".rstrip())
shown = answer if len(answer) <= 60 else answer[:57] + "..."
print("context".ljust(12), shown)
leaked = [n for n, c, _ in checks if c] + ([] if answer == "NONE" else ["context"])
version = init.get("claude_code_version", "?")
if leaked:
    print("x not isolated (" + ", ".join(leaked) + ") - claude " + version)
    if user:
        print("  user skills: " + ", ".join(user))
    sys.exit(1)
print(f"ok isolated - claude {version}")
'
}

if [[ "${1:-}" == "--probe" ]]; then
  probe
  exit $?
fi

if [[ $# -ne 3 ]]; then
  echo "usage: read.sh <persona.txt> <prompt.md> <draft.reader.md> | read.sh --probe" >&2
  exit 2
fi
for f in "$1" "$2" "$3"; do
  [[ -f "$f" ]] || { echo "read.sh: no such file: $f" >&2; exit 2; }
done

system_prompt=$(cat -- "$1")
user_prompt=$(cat -- "$2" "$3")
isolated --system-prompt "$system_prompt" "$user_prompt"
