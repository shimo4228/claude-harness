"""Tests for drift_count.py — what a persona-read revision added that the author did not say.

A revision round may change how the thinking is shown, never what is claimed. These tests pin the
kinds of change the loop must surface to the author: numbers absent from the evidence dossier,
added superlatives, added or removed hedges, and Latin names absent from the dossier. New katakana
words are listed for reading but do not fail the round (ordinary loanwords would fire every round).
"""

from __future__ import annotations

import json
from pathlib import Path

import drift_count as dc


def test_new_number_absent_from_dossier_is_flagged() -> None:
    result = dc.drift("合計は減った。", "合計は 63% 減った。", dossier="")
    assert result["new_numbers"] == ["63%"]


def test_new_number_present_in_dossier_is_not_flagged() -> None:
    result = dc.drift("合計は減った。", "合計は 28,131 字から減った。", dossier="| 28131 |")
    assert result["new_numbers"] == []


def test_number_already_in_previous_round_is_not_flagged() -> None:
    result = dc.drift("29 本が名前だけ。", "名前だけは 29 本。", dossier="")
    assert result["new_numbers"] == []


def test_full_width_digits_match_half_width_in_dossier() -> None:
    result = dc.drift("減った。", "２９ 本に減った。", dossier="29 本")
    assert result["new_numbers"] == []


def test_leading_and_trailing_zeros_match() -> None:
    result = dc.drift("差が出た。", "1.80 倍と 09 本。", dossier="1.8 倍、9 本")
    assert result["new_numbers"] == []


def test_percent_is_not_covered_by_the_same_bare_number() -> None:
    result = dc.drift("減った。", "63% 減った。", dossier="63 件")
    assert result["new_numbers"] == ["63%"]


def test_date_parts_in_dossier_do_not_cover_a_new_number() -> None:
    result = dc.drift("減った。", "10 本減った。", dossier="2026-10-09 に測った")
    assert result["new_numbers"] == ["10"]


def test_date_parts_in_draft_are_not_counted_as_numbers() -> None:
    result = dc.drift("測った。", "2026-10-09 に測った。", dossier="")
    assert result["new_numbers"] == []


def test_superlative_count_increase_is_flagged() -> None:
    result = dc.drift("考えた。", "誰よりも考えた。最も深い。", dossier="")
    assert result["new_superlatives"] == ["最も", "誰よりも"]


def test_superlative_kept_at_same_count_is_not_flagged() -> None:
    result = dc.drift("最も効いた。", "効いたのは最も短い版。", dossier="")
    assert result["new_superlatives"] == []


def test_hedge_count_increase_is_flagged() -> None:
    result = dc.drift("発火は変わる。", "発火は変わるかもしれない。おそらく。", dossier="")
    assert result["new_hedges"] == ["おそらく", "かもしれ"]


def test_hedge_removal_is_flagged() -> None:
    result = dc.drift("おそらく減るかもしれない。", "減る。", dossier="")
    assert result["removed_hedges"] == ["おそらく", "かもしれ"]
    assert dc.has_drift(result)


def test_new_name_absent_from_dossier_is_flagged() -> None:
    result = dc.drift("lint で数える。", "lint で数える。LangChain も同じ。", dossier="")
    assert result["new_names"] == ["LangChain"]


def test_new_name_present_in_dossier_is_not_flagged() -> None:
    result = dc.drift(
        "数える。", "Pocock と同じく数える。", dossier="Matt Pocock の mattpocock/skills"
    )
    assert result["new_names"] == []


def test_short_name_inside_a_longer_dossier_word_is_flagged() -> None:
    result = dc.drift("数える。", "AI で数える。", dossier="email で送った MAIN branch")
    assert result["new_names"] == ["AI"]


def test_new_katakana_is_listed_but_does_not_fail_the_round() -> None:
    result = dc.drift("読んだ。", "このケースではオーケストレーターを読んだ。", dossier="")
    assert result["new_katakana"] == ["オーケストレーター", "ケース"]
    assert result["new_names"] == []
    assert not dc.has_drift(result)


def test_has_drift_is_false_when_nothing_was_added() -> None:
    result = dc.drift("同じ文。", "同じ文。", dossier="")
    assert not dc.has_drift(result)


def test_cli_exits_1_and_prints_json_on_drift(tmp_path: Path, capsys) -> None:
    prev = tmp_path / "r0.md"
    curr = tmp_path / "r1.md"
    dossier = tmp_path / "dossier.md"
    prev.write_text("減った。", encoding="utf-8")
    curr.write_text("唯一 40% 減った。", encoding="utf-8")
    dossier.write_text("", encoding="utf-8")

    code = dc.main([str(prev), str(curr), "--dossier", str(dossier)])

    out = json.loads(capsys.readouterr().out)
    assert code == 1
    assert out["new_numbers"] == ["40%"]
    assert out["new_superlatives"] == ["唯一"]


def test_cli_exits_0_without_drift(tmp_path: Path, capsys) -> None:
    prev = tmp_path / "r0.md"
    curr = tmp_path / "r1.md"
    prev.write_text("減った。", encoding="utf-8")
    curr.write_text("減りました。", encoding="utf-8")

    code = dc.main([str(prev), str(curr)])

    assert code == 0
    assert json.loads(capsys.readouterr().out)["new_numbers"] == []


# English vocabulary and names (drafts written in English)


def test_english_superlative_increase_is_flagged() -> None:
    result = dc.drift(
        "We built a loop.", "We built the first loop. It is the best one.", dossier=""
    )
    assert result["new_superlatives"] == ["best", "the first"]


def test_english_superlative_matches_whole_words_only() -> None:
    result = dc.drift("It runs.", "It runs on the firstly loaded bestseller.", dossier="")
    assert result["new_superlatives"] == []


def test_english_superlative_ignores_case() -> None:
    result = dc.drift("A loop.", "The only loop. Unmatched.", dossier="")
    assert result["new_superlatives"] == ["the only", "unmatched"]


def test_english_hedge_increase_is_flagged() -> None:
    result = dc.drift(
        "The count drops.", "The count may drop. Perhaps it arguably drops.", dossier=""
    )
    assert result["new_hedges"] == ["arguably", "may", "perhaps"]


def test_english_hedge_removal_is_flagged() -> None:
    result = dc.drift("It might drop, likely by half.", "It drops by half.", dossier="")
    assert result["removed_hedges"] == ["likely", "might"]
    assert dc.has_drift(result)


def test_english_hedge_inside_a_longer_word_is_not_counted() -> None:
    result = dc.drift("It runs.", "It runs mayhem through mighty couldron.", dossier="")
    assert result["new_hedges"] == []


def test_english_draft_new_common_word_is_not_a_name() -> None:
    result = dc.drift(
        "Readers stop here.", "Readers stop here. Then they leave quickly.", dossier=""
    )
    assert result["new_names"] == []


def test_english_draft_new_product_name_is_flagged() -> None:
    result = dc.drift("We count words.", "We count words, as LangChain and GPT-5 do.", dossier="")
    assert result["new_names"] == ["GPT-5", "LangChain"]


def test_english_draft_capitalized_word_mid_sentence_is_a_name() -> None:
    result = dc.drift("We count words.", "We count words the way Pocock does.", dossier="")
    assert result["new_names"] == ["Pocock"]


def test_english_draft_name_from_dossier_is_not_flagged() -> None:
    result = dc.drift("We count.", "We count like Pocock.", dossier="Matt Pocock wrote it")
    assert result["new_names"] == []


def test_english_draft_list_item_start_is_not_a_name() -> None:
    result = dc.drift(
        "Steps:\n", "Steps:\n- Freeze the draft.\n1. Read it.\n## Revise\n", dossier=""
    )
    assert result["new_names"] == []


def test_word_moved_to_mid_sentence_is_not_new() -> None:
    result = dc.drift("Readers stop.", "Most of the time, Readers stop.", dossier="")
    assert result["new_names"] == []


def test_is_latin_text_follows_the_majority_script() -> None:
    assert dc.is_latin_text("The loop reads the draft.")
    assert not dc.is_latin_text("ループは稿を読む。lint で数える。")
