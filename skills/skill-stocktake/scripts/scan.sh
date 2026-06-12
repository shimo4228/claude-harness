#!/usr/bin/env bash
# scan.sh — enumerate skill files, extract frontmatter and UTC mtime
# Usage: scan.sh [CWD_SKILLS_DIR]
# Output: JSON to stdout
#
# When CWD_SKILLS_DIR is omitted, defaults to $PWD/.claude/skills so the
# script always picks up project-level skills without relying on the caller.
#
# Environment:
#   SKILL_STOCKTAKE_GLOBAL_DIR   Override ~/.claude/skills (for testing only;
#                                do not set in production — intended for bats tests)
#   SKILL_STOCKTAKE_PROJECT_DIR  Override project dir detection (for testing only)

set -euo pipefail

GLOBAL_DIR="${SKILL_STOCKTAKE_GLOBAL_DIR:-$HOME/.claude/skills}"
CWD_SKILLS_DIR="${SKILL_STOCKTAKE_PROJECT_DIR:-${1:-$PWD/.claude/skills}}"
# Usage log written by ~/.claude/hooks/log-skill-usage.sh (consumer-independent
# measurement layer). When absent, scan_summary.usage_log.available is false and
# consumers must render usage as "—" (unmeasured), never as 0.
# SKILL_USAGE_LOG is shared with log-skill-usage.sh; set it in tests only.
OBSERVATIONS="${SKILL_USAGE_LOG:-$HOME/.claude/metrics/skill-usage.jsonl}"

# Validate CWD_SKILLS_DIR looks like a .claude/skills path (defense-in-depth).
# Only warn when the path exists — a nonexistent path poses no traversal risk.
if [[ -n "$CWD_SKILLS_DIR" && -d "$CWD_SKILLS_DIR" && "$CWD_SKILLS_DIR" != */.claude/skills* ]]; then
  echo "Warning: CWD_SKILLS_DIR does not look like a .claude/skills path: $CWD_SKILLS_DIR" >&2
fi

# Extract a frontmatter field (handles both quoted and unquoted single-line values).
# Does NOT support multi-line YAML blocks (| or >) or nested YAML keys.
extract_field() {
  local file="$1" field="$2"
  awk -v f="$field" '
    BEGIN { fm=0 }
    /^---$/ { fm++; next }
    fm==1 {
      n = length(f) + 2
      if (substr($0, 1, n) == f ": ") {
        val = substr($0, n+1)
        gsub(/^"/, "", val)
        gsub(/"$/, "", val)
        print val
        exit
      }
    }
    fm>=2 { exit }
  ' "$file"
}

# Get UTC timestamp N days ago (supports both macOS and GNU date)
date_ago() {
  local n="$1"
  date -u -v-"${n}d" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null ||
  date -u -d "${n} days ago" +%Y-%m-%dT%H:%M:%SZ
}

# Scan a directory and produce a JSON array of skill objects
scan_dir_to_json() {
  local dir="$1"
  local c7 c30 c90
  c7=$(date_ago 7)
  c30=$(date_ago 30)
  c90=$(date_ago 90)

  local tmpdir
  tmpdir=$(mktemp -d)
  # Use a function to avoid embedding $tmpdir in a quoted string (prevents injection
  # if TMPDIR were crafted to contain shell metacharacters).
  local _scan_tmpdir="$tmpdir"
  _scan_cleanup() { rm -rf "$_scan_tmpdir"; }
  trap _scan_cleanup RETURN

  # Pre-aggregate observation counts in one pass per window instead of
  # calling jq per-file — reduces from O(n*m) to O(n+m) jq invocations.
  # Counts both "invoke" and "read" events (any event with a matching path).
  local obs_7d_counts obs_30d_counts obs_90d_counts
  obs_7d_counts=""
  obs_30d_counts=""
  obs_90d_counts=""
  if [[ -f "$OBSERVATIONS" ]]; then
    obs_7d_counts=$(jq -r --arg c "$c7" \
      'select(.ts>=$c) | .path | select(. != "")' \
      "$OBSERVATIONS" 2>/dev/null | sort | uniq -c)
    obs_30d_counts=$(jq -r --arg c "$c30" \
      'select(.ts>=$c) | .path | select(. != "")' \
      "$OBSERVATIONS" 2>/dev/null | sort | uniq -c)
    obs_90d_counts=$(jq -r --arg c "$c90" \
      'select(.ts>=$c) | .path | select(. != "")' \
      "$OBSERVATIONS" 2>/dev/null | sort | uniq -c)
  fi

  local i=0
  while IFS= read -r file; do
    local name desc mtime u7 u30 u90 dp
    name=$(extract_field "$file" "name")
    desc=$(extract_field "$file" "description")
    mtime=$(date -u -r "$file" +%Y-%m-%dT%H:%M:%SZ)
    # uniq -c output format: "   N /path/to/file". Strip the count field and
    # compare the full remainder so paths containing spaces still match exactly.
    u7=$(echo "$obs_7d_counts" | awk -v f="$file" '{c=$1; $1=""; sub(/^ /,""); if ($0==f) print c}' | head -1)
    u7="${u7:-0}"
    u30=$(echo "$obs_30d_counts" | awk -v f="$file" '{c=$1; $1=""; sub(/^ /,""); if ($0==f) print c}' | head -1)
    u30="${u30:-0}"
    u90=$(echo "$obs_90d_counts" | awk -v f="$file" '{c=$1; $1=""; sub(/^ /,""); if ($0==f) print c}' | head -1)
    u90="${u90:-0}"
    dp="${file/#$HOME/~}"

    jq -n \
      --arg path "$dp" \
      --arg name "$name" \
      --arg description "$desc" \
      --arg mtime "$mtime" \
      --argjson use_7d "$u7" \
      --argjson use_30d "$u30" \
      --argjson use_90d "$u90" \
      '{path:$path,name:$name,description:$description,use_7d:$use_7d,use_30d:$use_30d,use_90d:$use_90d,mtime:$mtime}' \
      > "$tmpdir/$i.json"
    i=$((i+1))
  done < <(find "$dir" -name "*.md" -type f 2>/dev/null | sort)

  if [[ $i -eq 0 ]]; then
    echo "[]"
  else
    jq -s '.' "$tmpdir"/*.json
  fi
}

# --- Main ---

global_found="false"
global_count=0
global_skills="[]"

if [[ -d "$GLOBAL_DIR" ]]; then
  global_found="true"
  global_skills=$(scan_dir_to_json "$GLOBAL_DIR")
  global_count=$(echo "$global_skills" | jq 'length')
fi

project_found="false"
project_path=""
project_count=0
project_skills="[]"

if [[ -n "$CWD_SKILLS_DIR" && -d "$CWD_SKILLS_DIR" ]]; then
  project_found="true"
  project_path="$CWD_SKILLS_DIR"
  project_skills=$(scan_dir_to_json "$CWD_SKILLS_DIR")
  project_count=$(echo "$project_skills" | jq 'length')
fi

# Merge global + project skills into one array
all_skills=$(jq -s 'add' <(echo "$global_skills") <(echo "$project_skills"))

# Usage log availability: consumers must distinguish "unmeasured" from 0.
usage_available="false"
usage_since=""
if [[ -f "$OBSERVATIONS" ]]; then
  usage_available="true"
  usage_since=$(head -1 "$OBSERVATIONS" | jq -r '.ts // empty' 2>/dev/null) || usage_since=""
fi

jq -n \
  --arg global_found "$global_found" \
  --argjson global_count "$global_count" \
  --arg project_found "$project_found" \
  --arg project_path "$project_path" \
  --argjson project_count "$project_count" \
  --arg usage_available "$usage_available" \
  --arg usage_since "$usage_since" \
  --arg usage_path "${OBSERVATIONS/#$HOME/~}" \
  --argjson skills "$all_skills" \
  '{
    scan_summary: {
      global: { found: ($global_found == "true"), count: $global_count },
      project: { found: ($project_found == "true"), path: $project_path, count: $project_count },
      usage_log: {
        available: ($usage_available == "true"),
        since: (if $usage_since == "" then null else $usage_since end),
        path: $usage_path
      }
    },
    skills: $skills
  }'
