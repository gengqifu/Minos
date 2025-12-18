import pytest
from pathlib import Path

from minos import rulesync_convert


@pytest.mark.xfail(reason="转换功能未实现，待 Story-10 开发", raises=rulesync_convert.RulesyncConvertError)
def test_gdpr_html_extract_segments(tmp_path: Path):
    html = """
    <html>
      <body>
        <h1>Article 1 本章标题</h1>
        <p>第一条内容。</p>
        <h2>Article 2 数据处理原则</h2>
        <p>第二条内容。</p>
      </body>
    </html>
    """
    path = tmp_path / "gdpr.html"
    path.write_text(html, encoding="utf-8")

    rules = rulesync_convert.extract_rules_from_file(
        path=path,
        source_url="https://eur-lex.europa.eu/eli/reg/2016/679/oj",
        regulation="gdpr",
    )
    assert len(rules) == 2
    assert rules[0]["clause"] == "1"
    assert "标题" in rules[0]["title"]
    assert rules[0]["source_url"] == "https://eur-lex.europa.eu/eli/reg/2016/679/oj"


@pytest.mark.xfail(reason="转换功能未实现，待 Story-10 开发", raises=rulesync_convert.RulesyncConvertError)
def test_ccpa_pdf_extract_sections(tmp_path: Path):
    pdf_text = """Section 1798.100 Title
This is section content.
Section 1798.101 Another section"""
    pdf_path = tmp_path / "ccpa.pdf"
    pdf_path.write_text(pdf_text, encoding="utf-8")

    rules = rulesync_convert.extract_rules_from_file(
        path=pdf_path,
        source_url="https://leginfo.legislature.ca.gov/faces/codes_displayText.xhtml?division=3.&part=4.&lawCode=CIV&title=1.81.5",
        regulation="ccpa",
    )
    assert len(rules) >= 2
    clauses = {r["clause"] for r in rules}
    assert "1798.100" in clauses
    assert "1798.101" in clauses


@pytest.mark.xfail(reason="转换功能未实现，待 Story-10 开发", raises=rulesync_convert.RulesyncConvertError)
def test_unknown_regulation_fails(tmp_path: Path):
    html = "<h1>Article 1</h1><p>content</p>"
    path = tmp_path / "unknown.html"
    path.write_text(html, encoding="utf-8")

    rulesync_convert.extract_rules_from_file(
        path=path,
        source_url="https://example.com/unknown",
        regulation="unknown-law",
    )
