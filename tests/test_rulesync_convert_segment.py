from minos import rulesync_convert
import pytest


def test_segment_text_article_sections():
    text = """
    Article 1 General provisions
    This is article one content.
    Section 1.1 Sub clause
    Sub content line.
    Article 2 Second title
    Second content.
    """
    segments = rulesync_convert.segment_text(text)
    clauses = [s["clause"] for s in segments]
    assert "1" in clauses
    assert "2" in clauses
    titles = {s["clause"]: s["title"] for s in segments}
    assert titles["1"].startswith("General")
    assert "Second title" in titles["2"]


def test_segment_text_title_fallback_to_body_first_line():
    text = """
    Article 3
    First line becomes title fallback.
    More body lines.
    """
    segments = rulesync_convert.segment_text(text)
    assert segments[0]["clause"] == "3"
    assert segments[0]["title"].startswith("First line becomes title")
    assert "More body lines." in segments[0]["body"]


def test_segment_text_raise_when_no_clause():
    text = "No clauses here"
    with pytest.raises(rulesync_convert.RulesyncConvertError):
        rulesync_convert.segment_text(text)
