"""Structural evidence sections for readme_evidence: structure, identity lead,
first screen, insider references, term candidates, <details> blocks, figures and
DOI / citation. Each function returns one top-level JSON value of the contract
documented in readme_evidence; none decides whether the README is good.
"""

from __future__ import annotations

import re
from collections import Counter, OrderedDict
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import unquote

if __package__:
    from . import readme_md as _md
else:  # Support the documented direct script invocation.
    import readme_md as _md

_DETAILS_CLOSE_RE = _md._DETAILS_CLOSE_RE
_DETAILS_OPEN_RE = _md._DETAILS_OPEN_RE
_FENCE_RE = _md._FENCE_RE
_HTML_IMG_RE = _md._HTML_IMG_RE
_MD_IMAGE_RE = _md._MD_IMAGE_RE
_MD_LINK_RE = _md._MD_LINK_RE
Heading = _md.Heading
Image = _md.Image
Link = _md.Link
_content_lines = _md._content_lines
_fence_lines = _md._fence_lines
_is_external = _md._is_external
_is_prose_line = _md._is_prose_line
broken_anchors = _md.broken_anchors

_DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>)\]]+")
_BIBTEX_RE = re.compile(r"@\w+\s*\{", re.IGNORECASE)
_CITATION_AFFORDANCE_RE = re.compile(r"\b(citation|bibtex)\b", re.IGNORECASE)
_CITE_HEADING_RE = re.compile(r"(?im)^\s{0,3}#{1,6}\s+.*(\bcit(e|ing|ation)|引用)")
_SUMMARY_RE = re.compile(r"<summary\b[^>]*>(.*?)</summary\s*>", re.IGNORECASE | re.DOTALL)
_ADR_ID_RE = re.compile(r"\bADR-(\d{4})\b")
_GITHUB_REPO_RE = re.compile(r"https?://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")
_DOC_PATH_RE = re.compile(r"\(\s*(?:\./)?(docs/[^)\s#]+)")
# A line made of HTML tags only (<p align="center">, </p>, <picture>, <source …>):
# it wraps the figure next to it rather than separating it from its caption.
_TAG_ONLY_RE = re.compile(r"^(?:</?[A-Za-z][^>]*>\s*)+$")
_BACKTICK_RE = re.compile(r"`([^`\n]{2,60})`")
_BOLD_RE = re.compile(r"\*\*([^*\n]{2,60})\*\*")
_CAMEL_RE = re.compile(r"^[A-Z][a-z]+(?:[A-Z][a-z]+)+$")


def structure(
    headings: list[Heading],
    images: list[Image],
    links: list[Link],
    base_dir: Path,
    anchors: set[str],
) -> dict:
    jumps = []
    prev: int | None = None
    for h in headings:
        if prev is not None and h.level > prev + 1:
            jumps.append({"line": h.line, "from": prev, "to": h.level, "text": h.text})
        prev = h.level
    broken = []
    for href, line in [(ln.href, ln.line) for ln in links] + [(i.src, i.line) for i in images]:
        if _is_external(href):
            continue
        target = unquote(href.split("#", 1)[0].split("?", 1)[0].strip())
        if not target or target.startswith("/"):
            continue
        if not (base_dir / target).exists():
            broken.append({"href": href, "line": line})
    return {
        "h1_count": sum(1 for h in headings if h.level == 1),
        "headings": [{"level": h.level, "text": h.text, "line": h.line} for h in headings],
        "heading_level_jumps": jumps,
        "broken_local_refs": broken,
        "broken_anchors": broken_anchors(links, anchors),
        "images_without_alt": [{"src": i.src, "line": i.line} for i in images if not i.alt.strip()],
    }


def identity_lead(
    content: list[tuple[int, str]], headings: list[Heading], inside: dict[int, bool]
) -> dict:
    h1 = next((h for h in headings if h.level == 1), None)
    if h1 is None:
        return {"present": False, "line": None, "note": "no H1"}
    after = [h for h in headings if h.line > h1.line]
    end_line = after[0].line if after else None
    for line_no, line in content:
        if line_no <= h1.line or (end_line is not None and line_no >= end_line):
            continue
        if inside.get(line_no):
            continue
        if _is_prose_line(line.strip()):
            return {"present": True, "line": line_no}
    return {"present": False, "line": None}


def _repo_key(repo: str) -> str:
    """Comparison key for owner/repo: GitHub names are case-insensitive, and a URL
    capture may carry `.git` or a sentence-final dot."""
    return repo.lower().rstrip("./").removesuffix(".git")


def _is_own(repo: str, own_repo: str | None) -> bool:
    return own_repo is not None and _repo_key(repo) == _repo_key(own_repo)


def first_screen(
    content: list[tuple[int, str]],
    headings: list[Heading],
    inside: dict[int, bool],
    own_repo: str | None,
) -> dict:
    """Everything before the first H2 (or the whole file if none)."""
    h2 = next((h for h in headings if h.level == 2), None)
    end = h2.line if h2 else (content[-1][0] + 1 if content else 1)
    lines = [(n, t) for n, t in content if n < end]
    prose = [t for n, t in lines if _is_prose_line(t.strip()) and not inside.get(n)]
    terms: OrderedDict[str, int] = OrderedDict()
    for n, t in lines:
        for _kind, term in formatted_term_spans(t):
            terms.setdefault(term, n)
    repos = {m.group(1) for _, t in lines for m in _GITHUB_REPO_RE.finditer(t)}
    return {
        "end_line": h2.line if h2 else None,
        "lines": end - 1,  # raw lines before the first H2 (fenced blocks included)
        "prose_lines": len(prose),
        "links": sum(len(_MD_LINK_RE.findall(t)) for _, t in lines),
        "new_terms": [{"term": k, "line": v} for k, v in terms.items()],
        "adr_refs": sum(len(_ADR_ID_RE.findall(t)) for _, t in lines),
        "github_repos": sorted(r for r in repos if not _is_own(r, own_repo)),
    }


def insider_refs(content: list[tuple[int, str]], own_repo: str | None) -> dict:
    adr: dict[str, list[int]] = {}
    repos: dict[str, list[int]] = {}
    doc_paths: Counter = Counter()
    dois: dict[str, list[int]] = {}
    for n, t in content:
        for m in _ADR_ID_RE.finditer(t):
            adr.setdefault(f"ADR-{m.group(1)}", []).append(n)
        for m in _GITHUB_REPO_RE.finditer(t):
            if not _is_own(m.group(1), own_repo):
                repos.setdefault(m.group(1), []).append(n)
        for m in _DOC_PATH_RE.finditer(t):
            top = "/".join(m.group(1).split("/")[:2])
            doc_paths[top] += 1
        for m in _DOI_RE.finditer(t):
            dois.setdefault(m.group(0), []).append(n)
    return {
        "adr_total": sum(len(v) for v in adr.values()),
        "adr_unique": len(adr),
        "adr_ids": adr,
        "github_repo_count": len(repos),
        "github_repos": repos,
        "doc_paths": dict(doc_paths),
        "dois": dois,
    }


def formatted_term_spans(text: str) -> Iterator[tuple[str, str]]:
    """Yield (kind, term) for backtick / bold spans that look like names rather than
    paths, flags, labels, links or JA clauses. Shared by first_screen and term_candidates.
    Only formatted spans are candidates: a coined term in plain prose never reaches here
    (NOTES says so to the judge, who finds those)."""
    for kind, rx in (("code", _BACKTICK_RE), ("bold", _BOLD_RE)):
        for m in rx.finditer(text):
            term = m.group(1).strip()
            if "](" in term or term.endswith((":", "：")) or re.search(r"[、。（）]", term):
                continue  # a link, a label, or a JA clause — not a name
            if kind == "code" and (
                "/" in term or term.endswith((".py", ".md", ".json", ".sh", ".txt"))
            ):
                continue  # a path or file name, not a term
            if kind == "code" and (
                term.startswith("-")
                or (" " not in term and not _CAMEL_RE.match(term) and "-" not in term)
            ):
                continue  # a CLI flag, or a single lowercase token
            if kind == "code" and any(tok.startswith("-") or tok == "." for tok in term.split()):
                continue  # a command invocation with flags, not a name
            yield kind, term


def term_candidates(content: list[tuple[int, str]]) -> list[dict]:
    """Backtick / bold spans that look like names rather than code paths.
    Whether a span is a coined term is the judge's call; this only lists them."""
    seen: dict[str, dict] = {}
    for n, t in content:
        for kind, term in formatted_term_spans(t):
            entry = seen.setdefault(term, {"term": term, "kind": kind, "count": 0, "first_line": n})
            entry["count"] += 1
    return sorted(seen.values(), key=lambda e: (-e["count"], e["first_line"]))


def details_blocks(markdown: str) -> list[dict]:
    blocks: list[dict] = []
    stack: list[int] = []  # open lines only; the body is sliced on close (no O(N^2) copies)
    raw = markdown.splitlines()
    for n, t in enumerate(raw, start=1):  # raw lines: a fenced BibTeX inside counts
        for _ in _DETAILS_OPEN_RE.findall(t):
            stack.append(n)
        for _ in _DETAILS_CLOSE_RE.findall(t):
            if stack:
                open_line = stack.pop()
                blk = {"open_line": open_line}
                body = "\n".join(raw[open_line - 1 : n])
                summary_m = _SUMMARY_RE.search(body)
                body_wo_summary = _SUMMARY_RE.sub("", body)
                blocks.append(
                    {
                        "open_line": blk["open_line"],
                        "close_line": n,
                        "lines": n - blk["open_line"] + 1,
                        "summary": re.sub(r"<[^>]+>", "", summary_m.group(1)).strip()
                        if summary_m
                        else "",
                        "contains": {
                            "doi": bool(_DOI_RE.search(body_wo_summary)),
                            "bibtex": bool(_BIBTEX_RE.search(body_wo_summary)),
                            "citation": "CITATION" in body_wo_summary.upper(),
                            "image": bool(
                                _MD_IMAGE_RE.search(body_wo_summary)
                                or _HTML_IMG_RE.search(body_wo_summary)
                            ),
                            "code_fence": "```" in body_wo_summary,
                        },
                    }
                )
    for open_line in stack:  # never closed: report, do not guess a body
        blocks.append(
            {
                "open_line": open_line,
                "close_line": None,
                "lines": None,
                "summary": "",
                "unclosed": True,
            }
        )
    return sorted(blocks, key=lambda b: b["open_line"])


def figures(
    markdown: str, images: list[Image], badges: list[Image], headings: list[Heading]
) -> list[dict]:
    all_lines = markdown.splitlines()
    content_map = dict(_content_lines(markdown))  # fenced lines are absent: never prose
    badge_lines = {b.line for b in badges}
    figure_images = [i for i in images if i not in badges]
    # lines that never count as the text equivalent, even when _is_prose_line says yes
    # (a setext heading's text line, a badge row with words, a captioned sibling figure)
    never_prose = {h.line for h in headings} | badge_lines | {i.line for i in figure_images}

    def is_wrapper(n: int) -> bool:
        t = content_map.get(n, "").strip()
        return bool(t) and bool(_TAG_ONLY_RE.match(t)) and not _HTML_IMG_RE.search(t)

    def prose_adjacent(first: int, last: int) -> bool:
        while is_wrapper(first - 1):
            first -= 1
        while is_wrapper(last + 1):
            last += 1
        window = (*range(first - 2, first), *range(last + 1, last + 3))
        return any(
            n not in never_prose and _is_prose_line(content_map.get(n, "").strip()) for n in window
        )

    out: list[dict] = []
    for line, info in _fence_lines(markdown):
        if info.lower().startswith("mermaid"):
            close = line  # the figure spans the opening through the closing fence
            for i in range(line + 1, len(all_lines) + 1):
                if _FENCE_RE.match(all_lines[i - 1]):
                    close = i
                    break
            out.append(
                {"kind": "mermaid", "line": line, "prose_adjacent": prose_adjacent(line, close)}
            )
    for img in figure_images:
        out.append(
            {
                "kind": "image",
                "line": img.line,
                "src": img.src,
                "alt": img.alt,
                "prose_adjacent": prose_adjacent(img.line, img.line),
                "badge_row": img.line in badge_lines,
            }
        )
    return sorted(out, key=lambda f: f["line"])


def doi_citation(markdown: str, content: list[tuple[int, str]]) -> dict:
    doi_line = next((n for n, t in content if _DOI_RE.search(t)), None)
    how_to_cite = bool(
        _BIBTEX_RE.search(markdown)
        or _CITATION_AFFORDANCE_RE.search(markdown)
        or _CITE_HEADING_RE.search(markdown)
        or "citation.cff" in markdown.lower()
    )
    return {
        "doi_present": doi_line is not None,
        "doi_first_line": doi_line,
        "how_to_cite_present": how_to_cite,
    }
