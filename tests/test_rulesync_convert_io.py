from pathlib import Path

import pytest

from minos import rulesync_convert


def test_read_html(tmp_path: Path):
    html_path = tmp_path / "sample.html"
    html_path.write_text("<h1>Article 1</h1><p>content</p>", encoding="utf-8")
    text, mime = rulesync_convert.read_document(html_path)
    assert "Article 1" in text
    assert mime == "text/html"


def test_read_pdf_with_text_fallback(tmp_path: Path):
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_text("Section 1 Title\nSome content", encoding="utf-8")
    text, mime = rulesync_convert.read_document(pdf_path)
    assert "Section 1" in text
    assert mime == "application/pdf"


def test_read_document_unsupported_extension(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("content", encoding="utf-8")
    with pytest.raises(rulesync_convert.RulesyncConvertError):
        rulesync_convert.read_document(file_path)


def test_read_document_missing_file(tmp_path: Path):
    missing = tmp_path / "missing.html"
    with pytest.raises(rulesync_convert.RulesyncConvertError):
        rulesync_convert.read_document(missing)
