from minos import rulesync_convert


def test_planalto_adapter_extracts_articles():
    html = """
    <div>Índice</div>
    <h1>Art. 1º Disposições gerais</h1>
    <p>Esta Lei dispõe sobre o tratamento de dados pessoais.</p>
    <h2>Art. 2º Fundamentos</h2>
    <p>A disciplina da proteção de dados pessoais tem como fundamentos o respeito à privacidade.</p>
    <h2>ANEXO I</h2>
    <p>Conteúdo de anexo não应被解析</p>
    """
    adapter = rulesync_convert.PlanaltoAdapter()
    segments = adapter.extract_segments(html, source_url="https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/L13709.htm")
    assert len(segments) == 2
    clauses = {s["clause"] for s in segments}
    assert "1º" in clauses or "1" in clauses
    assert "2º" in clauses or "2" in clauses
    assert all("ANEXO" not in s["body"].upper() for s in segments)
