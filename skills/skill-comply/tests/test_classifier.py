"""Regression tests for classification output parsing.

2026-07-28: all three scenarios of a full run graded 0% while the traces
showed full compliance behavior. Root cause: the classifier's child
`claude -p` session inherited the user-level Explanatory output style and
wrapped the answer JSON in narrative prose + an insight block, and
`_parse_classification` failed open to `{}` on the parse error. These tests
pin the extraction against style-contaminated output and the fail-loud
contract.
"""

import pytest

from scripts.classifier import ClassificationParseError, _parse_classification
from scripts.parser import extract_yaml_payload

CLEAN = '{"classify_task_type": [0], "run_verify_gate": [1]}'

FENCED = """```json
{"classify_task_type": [0], "run_verify_gate": [1]}
```"""

# 実障害の再現形: narrative + insight ブロック + fenced JSON(最後)
STYLE_CONTAMINATED = """失礼しました、直前のツール呼び出しは誤りです。分類タスクは JSON を直接返します。

`★ Insight ─────────────────────────────────────`
この 62 件のツールコール列は、同一の 8 ステップサイクルが 7 回繰り返される構造でした。
`run_verify_gate` の定義に「レビュー agent の後 {順序条件} 」が明記されている点が鍵です。
`─────────────────────────────────────────────────`

```json
{"classify_task_type": [0, 8], "run_review_agents": [5, 13], "run_verify_gate": [6]}
```"""


def test_clean_json_parses():
    assert _parse_classification(CLEAN) == {
        "classify_task_type": [0],
        "run_verify_gate": [1],
    }


def test_fenced_json_parses():
    assert _parse_classification(FENCED) == {
        "classify_task_type": [0],
        "run_verify_gate": [1],
    }


def test_style_contaminated_output_parses():
    """narrative + insight ブロック付き出力から末尾の JSON を抽出できる。"""
    assert _parse_classification(STYLE_CONTAMINATED) == {
        "classify_task_type": [0, 8],
        "run_review_agents": [5, 13],
        "run_verify_gate": [6],
    }


def test_trailing_narrative_after_json():
    text = CLEAN + "\n\n以上が分類結果です。"
    assert _parse_classification(text) == {
        "classify_task_type": [0],
        "run_verify_gate": [1],
    }


def test_legitimate_empty_object_is_not_an_error():
    """モデルの「一致なし」= {} は正当な結果で、例外にしない。"""
    assert _parse_classification("{}") == {}


def test_no_json_raises_instead_of_failing_open():
    """抽出不能は {} でなく例外 — 定数 0% 報告への fail-open を禁止する。"""
    with pytest.raises(ClassificationParseError):
        _parse_classification("申し訳ありませんが、分類できませんでした。")


def test_non_list_values_are_filtered():
    text = '{"classify_task_type": [1, 2], "note": "not a list"}'
    assert _parse_classification(text) == {"classify_task_type": [1, 2]}


def test_nested_object_does_not_shadow_outer_mapping():
    """答えの JSON 内の nested object が本来の mapping を握り潰さない。

    2026-07-28 /code-review 指摘: 末尾走査は nested object の `{` を先に拾い、
    内側が {str: [int]} 形なら本来の答えを黙って置き換える (silent 0% の残党)。
    """
    text = '{"write_test": [0, 1], "extra": {"x": [1]}}'
    assert _parse_classification(text) == {"write_test": [0, 1]}


def test_multiple_top_level_objects_last_wins():
    """複数の top-level object があれば最後の有効なものが答え (既存規約の固定)。"""
    text = '{"old_attempt": [9]}\nやり直します。\n{"classify_task_type": [0]}'
    assert _parse_classification(text) == {"classify_task_type": [0]}


# ---- extract_yaml_payload (spec / scenario generators share this) ----

SPEC_YAML = """id: implementation-chain
name: Implementation Chain
steps:
  - id: classify_task_type
    description: "State the task type"
    required: true
"""


def test_yaml_clean_passthrough():
    assert extract_yaml_payload(SPEC_YAML).strip() == SPEC_YAML.strip()


def test_yaml_edge_fenced():
    fenced = f"```yaml\n{SPEC_YAML}```"
    assert "id: implementation-chain" in extract_yaml_payload(fenced)
    assert "```" not in extract_yaml_payload(fenced)


def test_yaml_style_contaminated_output():
    """実障害の再現形: narrative + insight ブロックに挟まれた fenced YAML を抽出できる。"""
    contaminated = (
        "内容も仕様に沿っています。\n\n"
        "`★ Insight ─────────────────────────────────────`\n"
        "この skill は 7 step で観測可能です。\n"
        "`─────────────────────────────────────────────────`\n\n"
        f"```yaml\n{SPEC_YAML}```\n\n以上が spec です。"
    )
    extracted = extract_yaml_payload(contaminated)
    assert "id: implementation-chain" in extracted
    assert "Insight" not in extracted


def test_yaml_bare_with_narrative_preamble():
    text = f"以下が仕様です。\n\n{SPEC_YAML}"
    extracted = extract_yaml_payload(text)
    assert extracted.startswith("id: implementation-chain")


def test_yaml_unparsable_returns_edge_stripped_for_retry_loop():
    """抽出不能時は元テキストを返し、呼び出し側の retry-with-feedback に委ねる。"""
    text = "YAML を生成できませんでした。"
    assert extract_yaml_payload(text) == text
