#!/usr/bin/env bash
# sync-from-local.sh — one-way export from the live Claude Code harness
# (~/.claude) into this publication repo.
#
# Collects components whose origin marker matches ORIGIN (frontmatter
# `origin: <value>` or HTML comment `<!-- origin: <value> -->`), stages
# them, runs a secret scan, then replaces the managed subtrees
# (skills/ agents/ rules/ docs/adr/ rfcs/ hooks/ scripts/hooks/ tests/) wholesale.
#
# Three subtree groups are NOT origin-filtered:
#   docs/adr/  — ADRs record this harness's own design decisions and are
#     self-authored by definition, so the whole directory is synced.
#   rfcs/  — the task-and-proposal ledger (ADR-0049): every entry is a
#     self-authored judgement record, published wholesale for the same reason
#     as ADRs. Entries are written publishable by default; sensitive detail
#     lives behind links, never in the body.
#   hooks/ scripts/hooks/ tests/  — membership comes from HOOK_ALLOWLIST below.
#     Publication here is a *curation* judgement (is this reusable outside this
#     machine?), not a *provenance* fact (who wrote it). Most hooks in the live
#     harness are self-authored AND ~/.claude-specific, so an origin filter would
#     conflate the two and publish code that cannot run anywhere else. ADR-0038.
#
# LICENSE and llms*.txt are never
# touched; README.md / README.ja.md are rewritten ONLY inside their
# `<!-- BEGIN/END GENERATED: ... -->` marker regions (the upstream-components
# manifest and the skill/agent/rule tables) — all prose outside markers is
# left intact, so those regions are mechanically owned and must not be
# hand-edited except for the Purpose text they carry. The script never
# commits — `git diff` in this repo is the review gate.
#
# Usage:
#   scripts/sync-from-local.sh --dry-run   # report differences only
#   scripts/sync-from-local.sh             # apply to working tree
#
# Config (env overrides):
#   HARNESS_SYNC_SOURCE  source harness dir   (default: ~/.claude)
#   HARNESS_SYNC_ORIGIN  origin value to match (default: shimo4228)

set -euo pipefail

SOURCE_DIR="${HARNESS_SYNC_SOURCE:-$HOME/.claude}"
ORIGIN="${HARNESS_SYNC_ORIGIN:-shimo4228}"
TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SUBTREES=(skills agents rules docs/adr rfcs hooks scripts/hooks tests)

# Hooks that are useful in any repo, plus the parts they need to run and be
# verified: the commit surface (git-commit gates), and — since 2026-08-25 —
# two session-surface hooks published alongside the rfcs/ ledger:
# task-claims-reminder.sh (ledger etiquette on read; needs scripts/claims.py,
# which lands OUTSIDE the wholesale-replaced subtrees — delisting it needs a
# manual delete in this repo) and review-model-notice.sh (judge-tier review
# routing). Paths are relative to SOURCE_DIR and land at the same relative
# path in the publication repo. Deliberately excluded: hooks that only
# ever fire inside ~/.claude (harness-lint-precommit.sh + harness_lint.py),
# harness-internal automations (episode-log guards, contemplative-name-reminder,
# herdr-agent-state), and the rest of the non-commit surface (validate-bash,
# docs-prewrite, bats-autorun, log-*-usage) which stays a separate judgement.
#
# Because these live in wholesale-replaced subtrees, dropping an entry here makes
# the file disappear from the publication repo on the next sync, showing up as a
# deletion in `git diff` — removal stays reviewable rather than silently lingering.
# Any hand-written companion doc therefore belongs OUTSIDE these subtrees
# (docs/hooks.md), or it would be wiped on every run.
HOOK_ALLOWLIST=(
  hooks/_git-target-common.sh
  hooks/_advisory-common.sh
  hooks/secret-scan-precommit.sh
  hooks/verify-precommit.sh
  hooks/bandit-precommit.sh
  hooks/ruff-format-precommit.sh
  hooks/review-chain-notice.sh
  hooks/task-claims-reminder.sh
  hooks/review-model-notice.sh
  scripts/hooks/verify_allow.py
  scripts/claims.py
  tests/git-target-extraction.bats
  tests/advisory-envelope.bats
  tests/secret-scan-precommit.bats
  tests/review-chain-notice.bats
  tests/verify-precommit.bats
  tests/bandit-precommit.bats
  tests/ruff-format-precommit.bats
  tests/task-claims.bats
  tests/review-model-notice.bats
)

DRY_RUN=0
[[ "${1:-}" == "--dry-run" || "${1:-}" == "-n" ]] && DRY_RUN=1

# --- guard: managed subtrees must be clean so the sync delta is reviewable ---
if (( ! DRY_RUN )); then
  if ! git -C "$TARGET_DIR" diff --quiet -- "${SUBTREES[@]}" ||
     ! git -C "$TARGET_DIR" diff --cached --quiet -- "${SUBTREES[@]}"; then
    echo "ABORT: uncommitted changes in ${SUBTREES[*]} — commit or stash first," >&2
    echo "       so that 'git diff' after sync shows exactly the sync delta." >&2
    exit 1
  fi
fi

# --- staging ---
STAGING="$(mktemp -d)"
trap 'rm -rf "$STAGING"' EXIT
mkdir -p "$STAGING/skills" "$STAGING/agents" "$STAGING/rules" "$STAGING/docs/adr" \
  "$STAGING/rfcs" "$STAGING/hooks" "$STAGING/scripts/hooks" "$STAGING/tests"

has_origin() { head -15 "$1" | grep -q "origin: $ORIGIN"; }

# skills: directories whose SKILL.md declares the origin
for skill_md in "$SOURCE_DIR"/skills/*/SKILL.md; do
  [[ -f "$skill_md" ]] || continue
  has_origin "$skill_md" || continue
  cp -R "$(dirname "$skill_md")" "$STAGING/skills/"
done

# agents: flat *.md with the origin
for agent in "$SOURCE_DIR"/agents/*.md; do
  [[ -f "$agent" ]] || continue
  has_origin "$agent" || continue
  cp "$agent" "$STAGING/agents/"
done

# rules: *.md with the origin marker, preserving subdirectory layout
while IFS= read -r rule; do
  rel="${rule#"$SOURCE_DIR"/rules/}"
  mkdir -p "$STAGING/rules/$(dirname "$rel")"
  cp "$rule" "$STAGING/rules/$rel"
done < <(grep -rl "origin: $ORIGIN" "$SOURCE_DIR/rules/" 2>/dev/null || true)

# ADRs: the whole directory, no origin filter (self-authored by definition —
# they document this harness's own decisions; nothing external lands here)
for adr in "$SOURCE_DIR"/docs/adr/*.md; do
  [[ -f "$adr" ]] || continue
  cp "$adr" "$STAGING/docs/adr/"
done

# rfcs/: the public task-and-proposal ledger (ADR-0049) — same rationale as
# ADRs: self-authored judgement records, synced wholesale (index included)
for rfc in "$SOURCE_DIR"/rfcs/*.md; do
  [[ -f "$rfc" ]] || continue
  cp "$rfc" "$STAGING/rfcs/"
done

# hooks + their shared parts + their bats: explicit allowlist, no origin filter.
# A missing entry aborts rather than skipping: a renamed or deleted hook must be
# reconciled here, not silently published as a subset (the wholesale replace
# would then delete the file from the repo with no diff explaining why).
for rel in "${HOOK_ALLOWLIST[@]}"; do
  if [[ ! -f "$SOURCE_DIR/$rel" ]]; then
    echo "ABORT: HOOK_ALLOWLIST entry not found in source harness: $rel" >&2
    echo "       Reconcile scripts/sync-from-local.sh with $SOURCE_DIR." >&2
    exit 1
  fi
  cp -p "$SOURCE_DIR/$rel" "$STAGING/$rel"
done

# --- prune runtime artifacts from the staged payload ---
find "$STAGING" \( -name results.json -o -name '*.log' -o -name '*.pyc' \
  -o -name .DS_Store -o -name .coverage -o -name '.coverage.*' \) -delete
find "$STAGING" \( -name __pycache__ -o -name .pytest_cache -o -name .venv \
  -o -name node_modules -o -name .mypy_cache -o -name .ruff_cache \
  -o -name htmlcov -o -name results \) -type d -prune -exec rm -rf {} + 2>/dev/null || true
# `results` is skill-comply's run-output directory (generated specs + reports).
# It was being published because this script copies from the filesystem while the
# source harness gitignores it — so files the canonical repo declines to track
# were landing here, carrying absolute `/Users/<name>/…` paths from the machine
# that produced them. Pruning the directory is the fix; the path guard below is
# the backstop for the next artifact nobody thought about.

# --- frontmatter YAML validation (GitHub / SkillsMP parse strictly; abort on invalid) ---
if command -v python3 >/dev/null 2>&1 && python3 -c 'import yaml' >/dev/null 2>&1; then
  python3 - "$STAGING" <<'PYEOF' || exit 1
import glob, re, sys
import yaml
bad = []
for path in sorted(glob.glob(f"{sys.argv[1]}/**/*.md", recursive=True)):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    m = re.match(r"^---\n(.*?)\n---(\n|$)", text, re.S)
    if not m:
        continue
    try:
        yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        bad.append(f"  {path}: {str(exc).splitlines()[0]}")
if bad:
    print("ABORT: invalid YAML frontmatter in staged payload"
          " (strict parsers like GitHub's will fail to render):", file=sys.stderr)
    print("\n".join(bad), file=sys.stderr)
    sys.exit(1)
PYEOF
else
  echo "WARN: python3 + PyYAML not available — skipping frontmatter YAML validation" >&2
fi

# --- secret scan (high-confidence patterns; abort on any hit) ---
SECRET_RE='sk-ant-api[0-9A-Za-z_-]+|ghp_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{20,}|AKIA[0-9A-Z]{16}|xox[bporas]-[0-9A-Za-z-]{10,}|AIza[0-9A-Za-z_-]{35}|hf_[A-Za-z]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY'  # pragma: allowlist secret
if hits="$(grep -rEl "$SECRET_RE" "$STAGING" 2>/dev/null)"; then
  echo "ABORT: potential secrets detected in staged payload:" >&2
  echo "$hits" >&2
  exit 1
fi

# --- home-directory path scan (abort on any hit) ---
# The secret scan above only knows credential shapes. It says nothing about
# `$HOME/MyAI_Lab/...` expanded to a literal, which leaks this machine's
# filesystem layout and the private project names sitting in it. Eleven such
# files reached the public repo before this check existed (2026-08-08), all of
# them generated artifacts nobody read line by line. Aborting rather than
# warning: a warning printed in the middle of a sync is exactly what got missed.
#
# Matched as the **literal value of $HOME**, not a `/Users/<name>/` shape. The
# generic pattern fires on placeholders that are entirely fine to publish
# (`/Users/username/` in a reviewer checklist, `/Users/me/` in a test fixture,
# `/home/linuxbrew/` as a Homebrew constant), and a guard that cries wolf is a
# guard that gets bypassed. What is actually at stake is this machine's paths.
#
# To publish such a path deliberately, mark the line with the pragma below.
if hits="$(grep -rFn "$HOME/" "$STAGING" 2>/dev/null | grep -v 'pragma: allow-home-path')"; then
  echo "ABORT: absolute home-directory paths in staged payload" >&2
  echo "       (rewrite as \$HOME-relative, or mark the line 'pragma: allow-home-path'):" >&2
  printf '%s\n' "$hits" | sed "s|^$STAGING/|  |" >&2
  exit 1
fi

# --- report / apply ---
if (( DRY_RUN )); then
  echo "# DRY-RUN (origin: $ORIGIN) — differences staging vs $TARGET_DIR"
  for t in "${SUBTREES[@]}"; do
    if [[ -d "$TARGET_DIR/$t" ]]; then
      diff -rq "$STAGING/$t" "$TARGET_DIR/$t" 2>/dev/null || true
    else
      # brand-new subtree: diff against a missing dir reports nothing, so
      # list the staged files explicitly instead of staying silent
      find "$STAGING/$t" -type f | sed "s|^$STAGING/|NEW: |" | sort
    fi
  done
  exit 0
fi

for t in "${SUBTREES[@]}"; do
  rm -rf "${TARGET_DIR:?}/$t"
done
cp -R "$STAGING"/. "$TARGET_DIR"/

# --- regenerate the upstream-components manifest in README.md ---
# Names only, no content: external-origin components are credited, never
# redistributed. Generated so the list cannot drift by hand-editing.
python3 - "$SOURCE_DIR" "$TARGET_DIR/README.md" <<'PYEOF' || true
import re
import sys
from pathlib import Path

src, readme = Path(sys.argv[1]), Path(sys.argv[2])
ECC_URL = "https://github.com/affaan-m/everything-claude-code"
BEGIN = "<!-- BEGIN GENERATED: upstream-components -->"
END = "<!-- END GENERATED: upstream-components -->"
SELF = {"shimo4228", "auto-extracted", "skill-create"}


GITHUB_RE = re.compile(r"https?://github\.com/([^/]+/[^/]+?)(?:\.git|/|$)")
KEG_RE = re.compile(
    r"^(?:/opt/homebrew|/usr/local|/home/linuxbrew/\.linuxbrew)/(?:opt|Cellar)/([^/]+)/"
)


def brew_origin(target):
    """Derive org/repo for a skill symlinked into a Homebrew keg
    (/opt/homebrew/{opt,Cellar}/<formula>/...). The bundled SKILL.md carries no
    origin line (hunk 0.19.0 dropped it), so provenance comes from the formula's
    stable URL / homepage. None when the path is not a keg or brew is absent."""
    import json
    import subprocess

    # /opt/homebrew (Apple Silicon) / /usr/local (Intel) / linuxbrew, then
    # opt/<formula> or Cellar/<formula>/<version>. Anchored so the leading
    # "/opt" of the prefix itself cannot be mistaken for the keg marker.
    m = KEG_RE.match(str(target))
    if not m:
        return None
    formula = m.group(1)
    try:
        out = subprocess.run(
            ["brew", "info", "--json=v2", formula],
            capture_output=True, text=True, timeout=60, check=True,
        ).stdout
        f = json.loads(out)["formulae"][0]
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, IndexError):
        return None
    for url in (f.get("urls", {}).get("stable", {}).get("url", ""), f.get("homepage", "")):
        m = GITHUB_RE.search(url or "")
        if m:
            return m.group(1)
    return None


def origin_of(path):
    try:
        head = "".join(path.read_text(encoding="utf-8").splitlines(keepends=True)[:15])
    except OSError:
        return None
    m = re.search(r"^origin:\s*(\S+)", head, re.M) or re.search(
        r"<!--\s*origin:\s*(\S+)\s*-->", head
    )
    if m:
        return m.group(1)
    # skills/<name> symlinked out of the repo: origin is the link target
    # (~/.claude rules/common/skills.md, symlink row).
    d = path.parent
    if d.is_symlink():
        return brew_origin(d.resolve())
    return None


items = []
for p in sorted(src.glob("skills/*/SKILL.md")):
    items.append(("skills", p.parent.name, origin_of(p)))
for p in sorted(src.glob("skills/*.md")):
    items.append(("skills", p.stem, origin_of(p)))
for p in sorted(src.glob("agents/*.md")):
    items.append(("agents", p.stem, origin_of(p)))
for p in sorted(src.glob("rules/*/*.md")):
    items.append(("rules", f"{p.parent.name}/{p.stem}", origin_of(p)))

SUFFIX = "-customized"
rows = {}  # (base, modified) -> {kind: [names]}
for kind, name, o in items:
    if o is None:
        # Unknown provenance is not "self": say so instead of silently dropping
        # the credit (2026-08-22 hunk-review regression).
        print(f"[credits] origin unknown, not credited: {kind}/{name}", file=sys.stderr)
        continue
    if o in SELF:
        continue
    base, modified = (o[: -len(SUFFIX)], True) if o.endswith(SUFFIX) else (o, False)
    rows.setdefault((base, modified), {}).setdefault(kind, []).append(name)


def label(base, modified):
    shown = f"[{base}](https://github.com/{base})" if "/" in base else base
    if modified:
        return f"{shown} + local modifications"
    if (base, True) in rows:
        return f"{shown} (unmodified)"
    return shown


def cell(group, kind):
    return ", ".join(group.get(kind, [])) or "—"


ordered = sorted(rows, key=lambda k: (k[0] != "ECC", k[0], k[1]))
table = ["| Upstream | Skills | Agents | Rules |", "|---|---|---|---|"]
for key in ordered:
    group = rows[key]
    table.append(
        f"| {label(*key)} | {cell(group, 'skills')}"
        f" | {cell(group, 'agents')} | {cell(group, 'rules')} |"
    )

block = "\n".join(
    [
        BEGIN,
        "### Upstream components (names only)",
        "",
        "The live harness also runs components from external upstreams."
        " Their content — including any local modifications to it — is"
        " **not redistributed** here; the names alone are listed so the full"
        f" composition stays visible. ECC = [Everything Claude Code]({ECC_URL}).",
        "",
        *table,
        END,
    ]
)
text = readme.read_text(encoding="utf-8")
if BEGIN not in text or END not in text:
    print(
        "WARN: upstream-components markers missing in README.md — manifest NOT written",
        file=sys.stderr,
    )
    sys.exit(0)
new = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), block, text, flags=re.S)
if new != text:
    readme.write_text(new, encoding="utf-8")
    print("# manifest: README.md upstream-components regenerated")
else:
    print("# manifest: unchanged")
PYEOF

# --- regenerate the skill / agent / rule tables in README.md / README.ja.md ---
# Membership is derived from the just-synced payload; the Purpose column is
# preserved from the existing tables so hand-written curation survives, and only
# genuinely new components get a seeded Purpose (first clause of the SKILL.md
# `description`). Generated between markers so the roster cannot drift by
# hand-editing. Aggregate counts ("N skills") are deliberately written nowhere:
# a churning count baked into prose only drifts (No-volatile-state).
# No `|| true`: compute-then-write means a failure leaves every README untouched
# and aborts the run (set -e) rather than silently shipping a half-written table.
if command -v python3 >/dev/null 2>&1; then
python3 - "$TARGET_DIR" <<'PYEOF'
import re
import sys
from pathlib import Path

try:
    import yaml  # frontmatter is YAML; safe_load handles block scalars (>-, |-)
except ImportError:
    yaml = None

target = Path(sys.argv[1])
KINDS = [
    ("skills-table", "Skill", "skills"),
    ("agents-table", "Agent", "agents"),
    ("rules-table", "Rule", "rules"),
]
# Table rows look like: | [name](link/path) | purpose text |
ROW_RE = re.compile(r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*(.*?)\s*\|\s*$", re.M)
_BLOCK_INDICATORS = {">", ">-", ">+", "|", "|-", "|+"}


def clean(text):
    return text.replace("|", r"\|").replace("\n", " ").strip()


def seed_purpose(path):
    # First clause of the frontmatter `description`, as a placeholder a human
    # refines in the same `git diff`. Rules have no frontmatter -> "".
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return ""
    front = m.group(1)
    desc = ""
    if yaml is not None:
        try:
            data = yaml.safe_load(front)
            if isinstance(data, dict) and data.get("description"):
                desc = str(data["description"])
        except yaml.YAMLError:
            desc = ""
    if not desc:  # regex fallback (no PyYAML); may leak a bare block indicator
        d = re.search(r"^description:\s*(.+)$", front, re.M)
        cand = d.group(1).strip().strip("\"'") if d else ""
        desc = "" if cand in _BLOCK_INDICATORS else cand
    first = re.split(r"[。.](?:\s|$)", desc.strip(), maxsplit=1)[0]
    # rstrip trailing space / backslash so the truncated seed survives a
    # parse round-trip unchanged (ROW_RE strips trailing whitespace) — keeps
    # regeneration idempotent even when [:140] cuts mid-token.
    return clean(first)[:140].rstrip(" \\")


def enumerate_kind(kind):
    out = []
    if kind == "skills":
        for p in sorted(target.glob("skills/*/SKILL.md")):
            out.append((p.parent.name, f"skills/{p.parent.name}/SKILL.md", p))
        for p in sorted(target.glob("skills/*.md")):
            out.append((p.stem, f"skills/{p.stem}.md", p))
    elif kind == "agents":
        for p in sorted(target.glob("agents/*.md")):
            out.append((p.stem, f"agents/{p.stem}.md", p))
    elif kind == "rules":
        for p in sorted(target.glob("rules/*/*.md")):
            out.append((p.stem, f"rules/{p.parent.name}/{p.stem}.md", p))
    return out


def regenerate(text, rname):
    new_text = text
    for marker_id, header, kind in KINDS:
        begin = f"<!-- BEGIN GENERATED: {marker_id} -->"
        end = f"<!-- END GENERATED: {marker_id} -->"
        mo = re.search(re.escape(begin) + r"(.*?)" + re.escape(end), new_text, re.S)
        if not mo:
            print(
                f"WARN: {marker_id} markers missing in {rname} — table NOT regenerated",
                file=sys.stderr,
            )
            continue
        # existing Purpose + order scoped to THIS marker block only, so the
        # 4-column upstream-components table can never bleed into the parse.
        existing, order = {}, []
        for _name, path, purpose in ROW_RE.findall(mo.group(1)):
            existing[path] = purpose
            order.append(path)
        order_set = set(order)
        by_path = {path: (name, p) for name, path, p in enumerate_kind(kind)}
        current = set(by_path)
        # keep curated order, drop removed, append new (sorted) at the end
        ordered = [pth for pth in order if pth in current]
        ordered += sorted(pth for pth in current if pth not in order_set)
        rows = [f"| {header} | Purpose |", "| --- | --- |"]
        for pth in ordered:
            name, p = by_path[pth]
            # key-presence, not truthiness: an intentionally blank Purpose cell
            # is preserved, never silently re-seeded on the next run.
            purpose = existing[pth] if pth in existing else (seed_purpose(p) or "—")
            rows.append(f"| [{name}]({pth}) | {purpose} |")
        block = begin + "\n" + "\n".join(rows) + "\n" + end
        new_text = new_text[: mo.start()] + block + new_text[mo.end():]
    return new_text


# Compute every README first; only then write. A crash mid-compute writes
# nothing, so the two files can never end up asymmetrically updated.
updates = []
for rname in ("README.md", "README.ja.md"):
    rp = target / rname
    if not rp.exists():
        continue
    text = rp.read_text(encoding="utf-8")
    new_text = regenerate(text, rname)
    if new_text != text:
        updates.append((rp, new_text, rname))

for rp, new_text, rname in updates:
    tmp = rp.with_suffix(rp.suffix + ".tmp")  # atomic: write temp then replace
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(rp)
    print(f"# tables: {rname} skill/agent/rule tables regenerated")
if not updates:
    print("# tables: READMEs unchanged")
PYEOF
else
  echo "WARN: python3 not available — README tables not regenerated" >&2
fi

echo "# APPLIED (origin: $ORIGIN). Review before committing:"
git -C "$TARGET_DIR" status --short
