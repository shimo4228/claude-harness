#!/usr/bin/env python3
"""Add Wikidata QID URLs to `sameAs` of matching nodes in graph.jsonld files.

Format-preserving: edits are applied as text surgery anchored on each node's
unique @id, then validated by semantic tree comparison against an
independently computed expected tree. Never re-serializes the whole file
(json.dump would destroy the original formatting and produce huge diffs).

Usage:
    python3 add_qid_sameas.py --map qid_map.json graph1.jsonld ...           # dry-run
    python3 add_qid_sameas.py --map qid_map.json --apply graph1.jsonld ...   # apply

qid_map.json format:
{
  "person": {
    "qid": "https://www.wikidata.org/wiki/Q140090100",
    "orcid": "https://orcid.org/0000-0000-0000-0000"
  },
  "entities": [
    {
      "qid": "https://www.wikidata.org/wiki/Q140090186",
      "keys": [
        "https://doi.org/10.5281/zenodo.19200726",
        "https://github.com/example/my-repo"
      ]
    }
  ]
}

Matching rules:
- A node matches an entity iff one of its identity fields
  (@id / sameAs / identifier / url) EXACTLY equals one of the entity's keys
  (case-insensitive, trailing slash ignored). Substring matching is never
  used — it would confuse e.g. `owner/foo` with `owner/skill-foo`.
- Person nodes get the person QID only when their identity includes the
  ORCID URL AND their @type includes "Person".
- Nodes whose sameAs already contains the QID are skipped (idempotent).
"""

from __future__ import annotations

import argparse
import json
import re
import sys


def norm(s: str) -> str:
    return s.lower().rstrip("/")


def identity_strings(node: dict) -> list:
    out = []
    for field in ("@id", "sameAs", "identifier", "url"):
        v = node.get(field)
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, str):
                    out.append(x)
                elif isinstance(x, dict) and isinstance(x.get("value"), str):
                    out.append(x["value"])
        elif isinstance(v, dict) and isinstance(v.get("value"), str):
            out.append(v["value"])
    return out


def node_types(node: dict) -> list:
    t = node.get("@type", [])
    return t if isinstance(t, list) else [t]


def compute_targets(d: dict, mapping: dict) -> dict:
    """@id -> qid for nodes that should gain a sameAs entry."""
    key_to_qid = {}
    for ent in mapping.get("entities", []):
        for k in ent["keys"]:
            key_to_qid[norm(k)] = ent["qid"]
    person = mapping.get("person") or {}
    person_qid = person.get("qid")
    person_orcid = norm(person["orcid"]) if person.get("orcid") else None

    targets = {}
    for n in d.get("@graph", [d]):
        if not isinstance(n, dict) or "@id" not in n:
            continue
        ids = {norm(s) for s in identity_strings(n)}
        qid = None
        if person_qid and person_orcid in ids and "Person" in node_types(n):
            qid = person_qid
        else:
            hits = {key_to_qid[i] for i in ids if i in key_to_qid}
            if len(hits) == 1:
                qid = hits.pop()
            elif len(hits) > 1:
                sys.exit(f"ABORT: node {n['@id']} matches multiple QIDs: {hits}")
        if qid:
            existing = n.get("sameAs")
            if existing == qid or (isinstance(existing, list) and qid in existing):
                continue
            targets[n["@id"]] = qid
    return targets


def expected_tree(d: dict, targets: dict) -> dict:
    d = json.loads(json.dumps(d))  # deep copy
    for n in d.get("@graph", [d]):
        if isinstance(n, dict) and n.get("@id") in targets:
            qid = targets[n["@id"]]
            ex = n.get("sameAs")
            if ex is None:
                n["sameAs"] = qid
            elif isinstance(ex, str):
                n["sameAs"] = [ex, qid]
            else:
                n["sameAs"] = ex + [qid]
    return d


def find_enclosing_spans(text: str, anchor_positions: list) -> dict:
    """anchor_pos -> (open, close+1) span of the innermost enclosing object.

    Single forward string-aware scan; backward scanning breaks on strings.
    """
    pending = sorted(anchor_positions)
    open_to_anchors = {}
    spans = {}
    stack = []
    in_str = False
    i = 0
    pi = 0
    n = len(text)
    while i < n:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            stack.append(i)
        elif c == "}":
            o = stack.pop()
            for a in open_to_anchors.pop(o, []):
                spans[a] = (o, i + 1)
        while pi < len(pending) and pending[pi] <= i:
            if pending[pi] == i:
                top = stack[-1]
                open_to_anchors.setdefault(top, []).append(i)
            pi += 1
        i += 1
    return spans


def value_span(text: str, key_pos: int) -> tuple:
    """Span of the JSON value (string or array) following the key at key_pos."""
    colon = text.index(":", key_pos)
    i = colon + 1
    while text[i] in " \t\n":
        i += 1
    if text[i] == '"':
        j = i + 1
        while True:
            if text[j] == "\\":
                j += 2
                continue
            if text[j] == '"':
                return i, j + 1
            j += 1
    if text[i] == "[":
        depth = 0
        in_str = False
        j = i
        while True:
            c = text[j]
            if in_str:
                if c == "\\":
                    j += 2
                    continue
                if c == '"':
                    in_str = False
            elif c == '"':
                in_str = True
            elif c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    return i, j + 1
            j += 1
    raise ValueError("unsupported sameAs value")


def process_file(path: str, mapping: dict, apply: bool) -> None:
    original = json.load(open(path))
    targets = compute_targets(original, mapping)
    if not targets:
        print(f"[SKIP] {path} (no changes)")
        return
    label = "APPLY" if apply else "DRY"
    print(f"[{label}] {path}")
    for node_id, qid in targets.items():
        print(f"    {node_id[:60]:62} += {qid.rsplit('/', 1)[-1]}")
    if not apply:
        return

    expected = expected_tree(original, targets)
    text = open(path).read()

    for node_id, qid in targets.items():
        anchor = f'"@id": "{node_id}"'
        occurrences = [m.start() for m in re.finditer(re.escape(anchor), text)]
        if not occurrences:
            sys.exit(f"ABORT: anchor not found for {node_id} in {path}")
        spans_map = find_enclosing_spans(text, occurrences)
        candidates = []
        for occ in occurrences:
            s, e = spans_map[occ]
            try:
                obj = json.loads(text[s:e])
            except json.JSONDecodeError:
                continue
            if obj.get("@id") == node_id and ("@type" in obj or "sameAs" in obj):
                candidates.append((s, e, occ))
        if len(candidates) != 1:
            sys.exit(f"ABORT: node span not unique for {node_id} in {path}: {len(candidates)}")
        s, e, id_pos = candidates[0]
        block = text[s:e]
        if '"sameAs"' in block:
            key_pos = s + block.index('"sameAs"')
            vs, ve = value_span(text, key_pos)
            val = json.loads(text[vs:ve])
            new_val = [val, qid] if isinstance(val, str) else val + [qid]
            text = text[:vs] + json.dumps(new_val, ensure_ascii=False) + text[ve:]
        else:
            after = id_pos + len(anchor)
            line_start = text.rfind("\n", 0, id_pos) + 1
            indent = text[line_start:id_pos]
            insertion = f',\n{indent}"sameAs": "{qid}"'
            text = text[:after] + insertion + text[after:]

    new_tree = json.loads(text)
    if new_tree != expected:
        sys.exit(f"ABORT: semantic validation failed for {path} (file NOT written)")
    with open(path, "w") as f:
        f.write(text)
    print(f"    -> {len(targets)} nodes updated, semantic validation passed")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", required=True, help="qid_map.json")
    parser.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    parser.add_argument("files", nargs="+", help="graph.jsonld files")
    args = parser.parse_args()
    mapping = json.loads(open(args.map).read())
    for p in args.files:
        process_file(p, mapping, args.apply)


if __name__ == "__main__":
    main()
