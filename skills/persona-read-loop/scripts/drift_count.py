"""List what a persona-read revision added or dropped that the author did not decide.

A revision round may change how the thinking is shown, never what is claimed (the author's words
cap the certainty). This compares two full rounds of a draft and returns: numbers absent from the
evidence dossier, added superlatives, added and removed hedges, and Latin-script names absent from
the dossier. Any of these goes to the author before the next round. New katakana words are listed
for reading only, because ordinary loanwords would fire every round.

Superlatives and hedges are counted in Japanese and English. Japanese terms match as substrings;
English terms match as whole words, ignoring case.

Which Latin tokens count as names depends on the draft's script. In a draft that is mostly
Japanese (or other non-Latin script), every Latin token is a name (tool and product names are what
appears in Latin there). In a draft that is mostly Latin script, a token is a name when it has a
digit, an underscore, or a capital after its first letter (LangChain, GPT-5, AI), or when it is
capitalized somewhere other than the start of a sentence (Pocock). Lower-case product names in an
English draft are therefore not counted.

Usage:
    python3 drift_count.py <prev.md> <curr.md> [--dossier <path>]

Prints JSON. Exit 1 when anything other than new_katakana is non-empty, 0 otherwise.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

SUPERLATIVES = (
    "最も",
    "唯一",
    "初めて",
    "誰よりも",
    "第一人者",
    "圧倒的",
    "並ぶ者",
    "随一",
    "最高",
    "最大",
    "the first",
    "the only",
    "first-ever",
    "the most",
    "best",
    "unmatched",
    "unrivaled",
    "unparalleled",
    "unprecedented",
    "world-class",
    "state-of-the-art",
)
HEDGES = (
    "かもしれ",
    "と思われ",
    "可能性があ",
    "おそらく",
    "とは限らな",
    "と考えられ",
    "ように見え",
    "may",
    "might",
    "could",
    "arguably",
    "likely",
    "perhaps",
    "possibly",
    "probably",
    "presumably",
    "potentially",
    "seems",
    "appears to",
)

# A digit run that is not part of a date, time, version or identifier (2026-10-09, 09:00, v2.1, C17).
_NUMBER = re.compile(r"(?<![A-Za-z0-9\-/:.])\d[\d,]*(?:\.\d+)?(?![\d\-/:]|\.\d)%?")
_LATIN = re.compile(r"[A-Za-z][A-Za-z0-9_\-]*")
_LATIN_LETTER = re.compile(r"[A-Za-z]")
_KATAKANA = re.compile(r"[ァ-ヴー]{2,}")
# Text before a token that puts it at the start of a sentence, a line, or a list or heading item.
_SENTENCE_START = re.compile(r"(?:[.!?:]\s+|\n[ \t]*(?:[#>*+\-]+|\d+[.)])?[ \t]*)[\"'(\[]*$")
_LOOKBACK = 16
INFORMATIONAL = ("new_katakana",)


def _is_ascii(term: str) -> bool:
    return term.isascii()


def count(text: str, term: str) -> int:
    """Occurrences of a term: whole words ignoring case for English, substrings otherwise."""
    if _is_ascii(term):
        return len(re.findall(rf"(?<![A-Za-z]){re.escape(term)}(?![A-Za-z])", text, re.IGNORECASE))
    return text.count(term)


def _canonical_number(raw: str) -> str:
    percent = raw.endswith("%")
    value = raw.rstrip("%").replace(",", "")
    if "." in value:
        value = value.rstrip("0").rstrip(".")
    value = value.lstrip("0") or "0"
    return value + ("%" if percent else "")


def numbers(text: str) -> set[str]:
    """Canonical numbers: full-width folded, separators and redundant zeros dropped, % kept."""
    return {
        _canonical_number(m.group()) for m in _NUMBER.finditer(unicodedata.normalize("NFKC", text))
    }


def is_latin_text(text: str) -> bool:
    """True when Latin letters outnumber the other letters (a mostly English draft)."""
    latin = len(_LATIN_LETTER.findall(text))
    other = sum(1 for ch in text if ch.isalpha() and not ch.isascii())
    return latin > other


def _starts_sentence(text: str, start: int) -> bool:
    before = text[max(0, start - _LOOKBACK) : start]
    if start <= _LOOKBACK:
        before = "\n" + before  # the start of the text is the start of a line
    return bool(_SENTENCE_START.search(before))


def _marked_as_name(token: str) -> bool:
    return any(ch.isdigit() or ch == "_" for ch in token) or any(ch.isupper() for ch in token[1:])


def latin_names(text: str, latin_text: bool | None = None) -> set[str]:
    """Latin-script names; the rule depends on the draft's script (see the module docstring)."""
    text = unicodedata.normalize("NFKC", text)
    if latin_text is None:
        latin_text = is_latin_text(text)
    if not latin_text:
        return set(_LATIN.findall(text))
    names = set()
    for m in _LATIN.finditer(text):
        token = m.group()
        if _marked_as_name(token):
            names.add(token)
        elif token[0].isupper() and not _starts_sentence(text, m.start()):
            names.add(token)
    return names


def katakana(text: str) -> set[str]:
    return set(_KATAKANA.findall(text))


def added(prev: str, curr: str, terms: tuple[str, ...]) -> list[str]:
    return sorted(t for t in terms if count(curr, t) > count(prev, t))


def removed(prev: str, curr: str, terms: tuple[str, ...]) -> list[str]:
    return sorted(t for t in terms if count(curr, t) < count(prev, t))


def drift(prev: str, curr: str, dossier: str) -> dict[str, list[str]]:
    latin_text = is_latin_text(curr)
    said_numbers = numbers(prev) | numbers(dossier)
    # Names already said are every Latin token of the earlier texts, so a word that only changes
    # its position in a sentence is not new.
    said_names = latin_names(prev, latin_text=False) | latin_names(dossier, latin_text=False)
    return {
        "new_numbers": sorted(numbers(curr) - said_numbers),
        "new_superlatives": added(prev, curr, SUPERLATIVES),
        "new_hedges": added(prev, curr, HEDGES),
        "removed_hedges": removed(prev, curr, HEDGES),
        "new_names": sorted(latin_names(curr, latin_text) - said_names),
        "new_katakana": sorted(katakana(curr) - katakana(prev) - katakana(dossier)),
    }


def has_drift(result: dict[str, list[str]]) -> bool:
    return any(v for k, v in result.items() if k not in INFORMATIONAL)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="List what a persona-read revision added or dropped."
    )
    parser.add_argument("prev", type=Path)
    parser.add_argument("curr", type=Path)
    parser.add_argument(
        "--dossier", type=Path, help="evidence dossier; its numbers and names count as said"
    )
    args = parser.parse_args(argv)

    dossier = args.dossier.read_text(encoding="utf-8") if args.dossier else ""
    result = drift(
        args.prev.read_text(encoding="utf-8"), args.curr.read_text(encoding="utf-8"), dossier
    )
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 1 if has_drift(result) else 0


if __name__ == "__main__":
    raise SystemExit(main())
