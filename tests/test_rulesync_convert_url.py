from pathlib import Path

from minos import rulesync_convert


def test_convert_url_to_yaml_with_cache(tmp_path: Path):
    html = """
    <h1>Article 1 Title</h1>
    <p>Clause one.</p>
    <h2>Article 2 Second</h2>
    <p>Clause two.</p>
    """
    serve_dir = tmp_path / "serve"
    serve_dir.mkdir()
    html_file = serve_dir / "index.html"
    html_file.write_text(html, encoding="utf-8")
    url = html_file.as_uri()
    cache_dir = tmp_path / "cache"
    out = tmp_path / "rules.yaml"

    # 首次下载 + 转换
    result = rulesync_convert.convert_url_to_yaml(
        url=url,
        cache_dir=cache_dir,
        out_path=out,
        regulation="gdpr",
        version="1.0.0",
        timeout=5,
    )
    assert result.exists()
    content = out.read_text(encoding="utf-8")
    assert "GDPR-001" in content

    # 模拟离线：删除源文件后再次调用，应直接命中缓存
    html_file.unlink()
    cached = cache_dir / rulesync_convert._cache_filename(url)
    assert cached.exists()
    result2 = rulesync_convert.convert_url_to_yaml(
        url=url,
        cache_dir=cache_dir,
        out_path=out,
        regulation="gdpr",
        version="1.0.0",
        timeout=1,
    )
    assert result2.exists()
