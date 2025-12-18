from minos import rulesync_convert


def test_eurlex_adapter_extracts_articles_and_skips_annex():
    html = """
    <div class="toc">Table of contents</div>
    <h1>ARTICLE 1 Subject-matter and objectives</h1>
    <p>1. This Regulation lays down rules.</p>
    <p>2. This Regulation protects fundamental rights.</p>
    <h2>Article 2 Material scope</h2>
    <p>This Regulation applies to the processing of personal data.</p>
    <h2>ANNEX I</h2>
    <p>Annex content should be ignored.</p>
    """
    adapter = rulesync_convert.EurlexAdapter()
    segments = adapter.extract_segments(html, source_url="https://eur-lex.europa.eu/eli/reg/2016/679/oj")
    assert len(segments) == 2
    clauses = {s["clause"] for s in segments}
    assert "1" in clauses
    assert "2" in clauses
    titles = {s["clause"]: s["title"] for s in segments}
    assert "Subject-matter" in titles["1"]
    # Annex 内容未被包含在正文
    assert all("Annex" not in s["body"] for s in segments)
