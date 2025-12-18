from minos import rulesync_convert


def test_leginfo_adapter_extracts_sections():
    html = """
    <div>Table of contents</div>
    <h1>SECTION 1798.100 Title</h1>
    <p>This is section content.</p>
    <h2>Section 1798.101 Another</h2>
    <p>Another section content.</p>
    """
    adapter = rulesync_convert.LeginfoAdapter()
    segments = adapter.extract_segments(html, source_url="https://leginfo.legislature.ca.gov/...")
    assert len(segments) == 2
    clauses = {s["clause"] for s in segments}
    assert "1798.100" in clauses
    assert "1798.101" in clauses
    titles = {s["clause"]: s["title"] for s in segments}
    assert "Title" in titles["1798.100"]
