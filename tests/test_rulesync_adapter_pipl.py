from minos import rulesync_convert


def test_pipl_adapter_extracts_chapter_articles():
    html = """
    <div>目录</div>
    <h1>第一章 总则</h1>
    <p>（总则内容）</p>
    <h2>第一条 为了保护个人信息权益</h2>
    <p>制定本法。</p>
    <h2>第二条 处理个人信息应当遵循</h2>
    <p>合法、正当、必要原则。</p>
    <h2>附则</h2>
    <p>附则内容不应解析</p>
    """
    adapter = rulesync_convert.PiplAdapter()
    segments = adapter.extract_segments(html, source_url="https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm")
    assert len(segments) == 2
    clauses = {s["clause"] for s in segments}
    assert "第一条" in clauses or "1" in clauses
    assert "第二条" in clauses or "2" in clauses
    assert all("附则" not in s["body"] for s in segments)
