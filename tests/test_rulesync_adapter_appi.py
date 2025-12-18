from minos import rulesync_convert


def test_appi_adapter_extracts_articles_and_stops_at_fusoku():
    html = """
    <div>目次</div>
    <h1>第1条（目的）</h1>
    <p>この法律は、個人情報の保護を目的とする。</p>
    <h2>第2条（定義）</h2>
    <p>この法律において「個人情報」とは...</p>
    <h2>付則</h2>
    <p>付則はパースしない。</p>
    """
    adapter = rulesync_convert.AppiAdapter()
    segments = adapter.extract_segments(html, source_url="https://www.ppc.go.jp/personalinfo/legal/guidelines_tsusoku/")
    assert len(segments) == 2
    clauses = {s["clause"] for s in segments}
    assert "1" in clauses or "第1条" in clauses
    assert "2" in clauses or "第2条" in clauses
    assert all("付則" not in s["body"] for s in segments)
