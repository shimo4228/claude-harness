#!/usr/bin/env bash
# hf-sync: stage cwd's graph.jsonld into the local HF clone dir, regenerate
# graph.jsonl there, and upload both to the HF dataset.
#
# Usage: sync.sh <Owner/dataset>
#
# Convention: HF clone lives at ${HF_CLONE_BASE:-~/MyAI_Lab/hf-datasets}/<dataset>/
# (the basename of the dataset id). The clone is a plain working directory,
# not a git repo — it holds the snapshot of files that get uploaded to HF.
#
# Source repo stays clean: graph.jsonl never lands in the source tree.
#
# See ~/.claude/skills/hf-sync/SKILL.md for full context.

set -euo pipefail

if [[ $# -lt 1 || -z "${1:-}" ]]; then
  echo "usage: $(basename "$0") <Owner/dataset>" >&2
  echo "  e.g.  $(basename "$0") Shimo4228/agent-knowledge-cycle" >&2
  exit 2
fi

HF_REPO="$1"
DATASET=$(basename "$HF_REPO")
HF_CLONE="${HF_CLONE_BASE:-$HOME/MyAI_Lab/hf-datasets}/${DATASET}"
SOURCE_DIR="$(pwd)"

if [[ ! -f "$SOURCE_DIR/graph.jsonld" ]]; then
  echo "error: no graph.jsonld in $SOURCE_DIR" >&2
  echo "  run this from a project root containing graph.jsonld" >&2
  exit 1
fi

if [[ ! -d "$HF_CLONE" ]]; then
  echo "error: HF clone dir not found: $HF_CLONE" >&2
  echo "  expected layout: \$HF_CLONE_BASE/<dataset>/ (default base: ~/MyAI_Lab/hf-datasets)" >&2
  echo "  create it first with: mkdir -p \"$HF_CLONE\"" >&2
  exit 1
fi

if ! jq -e '.["@graph"] | type == "array" and length > 0' "$SOURCE_DIR/graph.jsonld" > /dev/null; then
  echo "error: graph.jsonld @graph must be a non-empty array" >&2
  exit 1
fi

cp "$SOURCE_DIR/graph.jsonld" "$HF_CLONE/graph.jsonld"
jq -c '.["@graph"][]' "$HF_CLONE/graph.jsonld" > "$HF_CLONE/graph.jsonl"
NODES=$(wc -l < "$HF_CLONE/graph.jsonl" | tr -d ' ')
echo "✓ Staged in $HF_CLONE (${NODES} nodes)"

hf upload "$HF_REPO" "$HF_CLONE/graph.jsonld" graph.jsonld --repo-type dataset
hf upload "$HF_REPO" "$HF_CLONE/graph.jsonl" graph.jsonl --repo-type dataset

echo "✓ Synced to https://huggingface.co/datasets/${HF_REPO}"
